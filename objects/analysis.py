import logging
from pathlib import Path
from typing import List
from pydantic import BaseModel
from shapely.geometry import Polygon

from geolib.models.dstability import DStabilityModel
from geolib.geometry.one import Point

from objects.dam import DAMInput, DAMScenario, DAMPointType
from helpers.geometry import extract_polygon_from_soilpolygons


class DAMAnalysis(BaseModel):
    input: DAMInput = None
    scenarios: List[DAMScenario] = []

    def create_stix(
        self,
        output_path: str,
        soils_algorithm: callable,
        phreatic_line_algorithm: callable,
        max_soilprofile_depth: float,
        params: dict = {},
    ):
        for scenario in self.scenarios[:2]:
            for (
                subsoil
            ) in scenario.location.subsoils:  # a scenario can contain multiple subsoils
                # a scenario can contain multiple stages so create one stix file with 1 scenario and n stages
                name = f"{scenario.location.id}_{subsoil.crest_profile.id}_{subsoil.toe_profile.id}_{subsoil.probability:03d}"
                logging.info(f"Handling '{name}'")
                log_filename = Path(output_path) / f"{name}.log"
                flog = open(log_filename, "w")
                flog.write(f"LOCATIE: {scenario.location.id}\n")
                flog.write(f"PROBABILITY ONDERGROND: {subsoil.probability}%\n")

                flog.write(f"GRONDOPBOUW KRUIN ({subsoil.crest_profile.id})\n")
                flog.write("-" * 80 + "\n")
                for layer in subsoil.crest_profile.layers:
                    flog.write(
                        f"{layer.top:10.2f},{layer.bottom:10.2f}, {layer.soil_name}\n"
                    )
                flog.write("-" * 80 + "\n")
                flog.write(f"GRONDOPBOUW TEEN ({subsoil.toe_profile.id})\n")
                for layer in subsoil.toe_profile.layers:
                    flog.write(
                        f"{layer.top:10.2f},{layer.bottom:10.2f}, {layer.soil_name}\n"
                    )
                flog.write("-" * 80 + "\n")

                flog.write(f"SCENARIO: {scenario.name}\n")
                for stage in scenario.stages:
                    flog.write(f"STAGE: {stage.name}\n")
                    flog.write(f"WATERSTAND RIVIER: {stage.waterlevel_river}\n")
                    flog.write(f"WATERSTAND POLDER: {stage.waterlevel_polder}\n")
                    flog.write(f"TRAFFIC LOAD: {stage.traffic_load_magnitude}\n")
                    flog.write(f"HYDRAULIC HEAD: {stage.hydraulic_head}\n")

                flog.write("-" * 80 + "\n")

                dm = DStabilityModel()

                # Grondsoorten
                try:
                    soils = soils_algorithm(self.input.soils)
                    for soil in soils:
                        dm.add_soil(soil)
                except Exception as e:
                    flog.write(f"[FATAL] Error during soils_algorithm: {e}\n")
                    continue

                # Freatische lijn
                try:
                    pl1 = phreatic_line_algorithm(
                        surfaceline=scenario.location.surfaceline,
                        waterlevel_river=scenario.stages[0].waterlevel_river,
                        waterlevel_polder=scenario.stages[0].waterlevel_polder,
                        params={
                            "offset_surface_line": 0.1,
                            "offset_dike_crest_water_side": 0.0,
                            "offset_dike_crest_land_side": scenario.stages[
                                1
                            ].waterlevel_river
                            - scenario.stages[0].waterlevel_river,
                        },
                    )
                    pl1_points = [Point(x=p[0], z=p[1]) for p in pl1]
                    pl1_id = dm.add_head_line(
                        points=pl1_points,
                        label="Phreatic Line",
                        is_phreatic_line=True,
                    )
                except Exception as e:
                    flog.write(f"[FATAL] Error during phreatic_line_algorithm: {e}\n")
                    continue

                # Grondlagen totaal
                x0 = scenario.location.surfaceline.left
                x1 = scenario.location.surfaceline.get_point_by_type(
                    DAMPointType.DIKE_TOE_LAND_SIDE
                ).l
                x2 = scenario.location.surfaceline.right

                soil_polygons_crest = subsoil.crest_profile.to_soil_polygons(
                    left=x0, right=x1, max_depth=max_soilprofile_depth
                )
                soil_polygons_toe = subsoil.toe_profile.to_soil_polygons(
                    left=x1, right=x2, max_depth=max_soilprofile_depth
                )

                # Alles boven het maaiveld weghalen
                surfaceline_left = scenario.location.surfaceline.left
                surfaceline_right = scenario.location.surfaceline.right

                pg_points_surfaceline = [
                    p.as_lz() for p in scenario.location.surfaceline.points
                ]
                pg_points_surfaceline.append((surfaceline_right, 9999.0))
                pg_points_surfaceline.append((surfaceline_left, 9999.0))
                pg_points_surfaceline.append(pg_points_surfaceline[0])
                pg_surfaceline = Polygon(pg_points_surfaceline)

                soil_polygons_crest = extract_polygon_from_soilpolygons(
                    soil_polygons_crest, pg_surfaceline
                )
                soil_polygons_toe = extract_polygon_from_soilpolygons(
                    soil_polygons_toe, pg_surfaceline
                )

                for spg in soil_polygons_crest:
                    points = [Point(x=p[0], z=p[1]) for p in spg.points]
                    dm.add_layer(points, spg.soil_name)

                for spg in soil_polygons_toe:
                    points = [Point(x=p[0], z=p[1]) for p in spg.points]
                    dm.add_layer(points, spg.soil_name)

                stix_path = Path(output_path) / f"{name}.stix"
                dm.serialize(stix_path)
                flog.close()
