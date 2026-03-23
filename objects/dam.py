from enum import IntEnum
from typing import List, Optional
from pydantic import BaseModel
from geolib.models.dstability.internal import PersistableShadingTypeEnum
import logging
from pathlib import Path


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


class DAMSoilProfile(BaseModel):
    id: str = ""
    layers: List[DAMSoilLayer] = []


class DAMPoint(BaseModel):
    l: float = 0.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    point_type: str = ""


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
    index: int
    traffic_load_magnitude: float = 0.0
    waterlevel_river: float = 0.0
    waterlevel_polder: float = 0.0
    hydraulic_head: float = 0.0


class DAMScenario(BaseModel):
    name: str = ""
    location: DAMLocation = None
    stages: List[DAMStage] = []


class DAMAnalysis(BaseModel):
    input: DAMInput = None
    scenarios: List[DAMScenario] = []

    def create_stix(self, output_path: str):
        for scenario in self.scenarios:
            for (
                subsoil
            ) in scenario.location.subsoils:  # a scenario can contain multiple subsoils
                # a scenario can contain multiple stages so create one stix file with 1 scenario and n stages
                name = f"{scenario.location.id}_{scenario.name}_{subsoil.crest_profile.id}_{subsoil.toe_profile.id}_{subsoil.probability:03d}"
                logging.info(f"Handling '{name}'")
                log_filename = Path(output_path) / f"{name}.log"
                flog = open(log_filename, "w")
                flog.write(f"LOCATIE: {scenario.location.id}\n")
                flog.write(f"SCENARIO: {scenario.name}\n")
                flog.write(f"PROBABILITY ONDERGROND: {subsoil.probability}%\n")
                flog.write("-" * 80 + "\n")
                flog.write(f"GRONDOPBOUW KRUIN ({subsoil.crest_profile.id})\n")
                flog.write("-" * 80 + "\n")
                for layer in subsoil.crest_profile.layers:
                    flog.write(
                        f"{layer.top:10.2f},{layer.bottom:10.2f}, {layer.soil_name}\n"
                    )
                flog.write("-" * 80 + "\n")
                flog.write(f"GRONDOPBOUW TEEN ({subsoil.toe_profile.id})\n")
                flog.write("-" * 80 + "\n")
                for layer in subsoil.toe_profile.layers:
                    flog.write(
                        f"{layer.top:10.2f},{layer.bottom:10.2f}, {layer.soil_name}\n"
                    )
                flog.write("-" * 80 + "\n")
                stix_path = Path(output_path) / f"{name}.stix"
                flog.close()
                break
            break
