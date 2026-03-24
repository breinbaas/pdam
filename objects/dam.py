from enum import IntEnum
from typing import List, Optional, Tuple
from pydantic import BaseModel
from geolib.models.dstability.internal import PersistableShadingTypeEnum

from shapely.geometry import Polygon


class SoilPolygon(BaseModel):
    soil_name: str = ""
    points: List[Tuple[float, float]] = []

    def to_shapely(self) -> Polygon:
        points = self.points + [self.points[0]]
        return Polygon(points)


class DAMPointType(IntEnum):
    NONE = 0
    SURFACE_LEVEL_WATER_SIDE = 1
    TOE_CANAL = 2
    START_CANAL = 3
    DIKE_TOE_WATER_SIDE = 4
    BERM_CREST_WATER_SIDE = 5
    BERM_START_WATER_SIDE = 6
    DIKE_CREST_WATER_SIDE = 7
    TRAFFIC_LOAD_WATER_SIDE = 8
    TRAFFIC_LOAD_LAND_SIDE = 9
    DIKE_CREST_LAND_SIDE = 10
    BERM_START_LAND_SIDE = 11
    BERM_CREST_LAND_SIDE = 12
    DIKE_TOE_LAND_SIDE = 13
    DITCH_START_WATER_SIDE = 14
    DITCH_BOTTOM_WATER_SIDE = 15
    DITCH_BOTTOM_LAND_SIDE = 16
    DITCH_START_LAND_SIDE = 17
    SURFACE_LEVEL_LAND_SIDE = 18


class DAMSoil(BaseModel):
    name: str = ""
    unsaturated_weight: float = 0.0
    saturated_weight: float = 0.0
    strength_model_above: str = ""
    strength_model_below: str = ""
    is_probabilistic: bool = False
    c_mean: float = 0.0
    c_std: float = 0.0
    phi_mean: float = 0.0
    phi_std: float = 0.0
    psi_mean: float = 0.0
    psi_std: float = 0.0
    shear_stress_ratio_s_mean: float = 0.0
    shear_stress_ratio_s_std: float = 0.0
    strength_exponent_m_mean: float = 0.0
    strength_exponent_m_std: float = 0.0
    is_probabilistic_pop: bool = False
    pop_mean: float = 0.0
    pop_std: float = 0.0
    c_phi_correlated: bool = False
    s_m_correlated: bool = False
    consolidation_traffic_load: float = 0.0
    color: str = ""
    pattern: PersistableShadingTypeEnum = PersistableShadingTypeEnum.NONE

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, d: dict) -> "DAMSoil":
        return DAMSoil(**d)  # todo covert PersistableShadingTypeEnum


class DAMSoilLayer(BaseModel):
    top: float = 0.0
    bottom: float = 0.0
    soil_name: str = ""

    @property
    def height(self) -> float:
        return self.top - self.bottom


class DAMSoilProfile(BaseModel):
    id: str = ""
    layers: List[DAMSoilLayer] = []

    def to_soil_polygons(
        self, left: float, right: float, max_depth: float
    ) -> List[SoilPolygon]:
        soil_polygons = []
        for layer in self.layers:
            if layer.bottom < -max_depth:
                layer.bottom = -max_depth

            if layer.height <= 0.0:
                continue

            soil_polygons.append(
                SoilPolygon(
                    soil_name=layer.soil_name,
                    points=[
                        (left, layer.top),
                        (right, layer.top),
                        (right, layer.bottom),
                        (left, layer.bottom),
                    ],
                )
            )
        return soil_polygons


class DAMPoint(BaseModel):
    l: float = 0.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    point_type: DAMPointType = DAMPointType.NONE

    def as_lz(self) -> Tuple[float, float]:
        return (self.l, self.z)


class DAMTrafficLoadLocation(BaseModel):
    left: Optional[float] = None
    right: Optional[float] = None


class DAMRevetment(BaseModel):
    left: Optional[float] = None
    right: Optional[float] = None
    thickness: Optional[float] = None
    soil_name: Optional[str] = None


class DAMSurfaceLine(BaseModel):
    id: str = ""
    points: List[DAMPoint] = []
    trafficload: Optional[DAMTrafficLoadLocation] = None
    revetment: Optional[DAMRevetment] = None

    @property
    def left(self) -> float:
        return self.points[0].l

    @property
    def right(self) -> float:
        return self.points[-1].l

    @property
    def top(self) -> float:
        return max([p.z for p in self.points])

    @property
    def has_ditch(self) -> bool:
        return (
            self.has_point_type(DAMPointType.DITCH_START_WATER_SIDE)
            & self.has_point_type(DAMPointType.DITCH_START_LAND_SIDE)
            & self.has_point_type(DAMPointType.DITCH_BOTTOM_WATER_SIDE)
            & self.has_point_type(DAMPointType.DITCH_BOTTOM_LAND_SIDE)
        )

    def intersections_at_z(self, z: float) -> List[float]:
        from helpers.geometry import polyline_polyline_intersections

        z_points = [(self.left, z), (self.right, z)]
        surface_points = [(p.l, p.z) for p in self.points]
        return polyline_polyline_intersections(z_points, surface_points)

    def get_point_by_type(self, point_type: DAMPointType) -> Optional[DAMPoint]:
        for point in self.points:
            if point.point_type == point_type:
                return point
        return None

    def has_point_type(self, point_type: DAMPointType) -> bool:
        for point in self.points:
            if point.point_type == point_type:
                return True
        return False

    def z_at(self, l: float) -> float:
        for i in range(len(self.points) - 1):
            if self.points[i].l <= l <= self.points[i + 1].l:
                return self.points[i].z + (self.points[i + 1].z - self.points[i].z) * (
                    l - self.points[i].l
                ) / (self.points[i + 1].l - self.points[i].l)

        return None


class DAMSubSoil(BaseModel):
    crest_profile: DAMSoilProfile = None
    toe_profile: DAMSoilProfile = None
    probability: int = 0


class DAMLocation(BaseModel):
    id: str = ""
    subsoils: List[DAMSubSoil] = []
    surfaceline: DAMSurfaceLine = None


class DAMInput(BaseModel):
    soils: List[DAMSoil] = []
    locations: List[DAMLocation] = []


class DAMStage(BaseModel):
    name: str = ""
    index: int = -1
    traffic_load_magnitude: float = 0.0
    waterlevel_river: float = 0.0
    waterlevel_polder: float = 0.0
    hydraulic_head: float = 0.0


class DAMScenario(BaseModel):
    name: str = ""
    location: DAMLocation = None
    stages: List[DAMStage] = []
