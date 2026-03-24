from pathlib import Path
import logging
from typing import List
from geolib.soils.soil import Soil, ShearStrengthModelTypePhreaticLevel

from helpers.geometry import clean_points, z_at
from importers.rijnland import import_rijnland
from database.database import DatabaseHandler
from objects.dam import DAMSurfaceLine, DAMPointType, DAMSoil

DAM_INPUT_PATH = r"C:\Users\brein\Documents\Rijnland"
DATABASE_PATH = r"C:\Users\brein\Documents\Rijnland\Output\rijnland.db"
OUTPUT_PATH = r"C:\Users\brein\Documents\Rijnland\Output"


logging.basicConfig(
    filename="dam2stix.log",
    filemode="w",
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)


def rijnland_soil_algorithm(dam_soils: List[DAMSoil]) -> List[Soil]:
    soils = []
    for dam_soil in dam_soils:
        soil = Soil()
        soil.shear_strength_model_above_phreatic_level = (
            ShearStrengthModelTypePhreaticLevel.MOHR_COULOMB
        )
        soil.shear_strength_model_below_phreatic_level = (
            ShearStrengthModelTypePhreaticLevel.MOHR_COULOMB
        )
        soil.name = dam_soil.name
        soil.code = dam_soil.name
        soil.soil_weight_parameters.saturated_weight.mean = dam_soil.unsaturated_weight
        soil.soil_weight_parameters.unsaturated_weight.mean = dam_soil.saturated_weight
        soil.mohr_coulomb_parameters.cohesion.mean = dam_soil.c_mean
        soil.mohr_coulomb_parameters.friction_angle.mean = dam_soil.phi_mean
        soil.color = dam_soil.color
        soils.append(soil)
    return soils


def rijnland_phreatic_line_algorithm(
    surfaceline: DAMSurfaceLine,
    waterlevel_river: float,
    waterlevel_polder: float,
    params: dict,
):
    # P1 = Meest linker punt
    pl_points = []
    pl_points.append((surfaceline.left, waterlevel_river))

    intersections_at_waterlevel_river = surfaceline.intersections_at_z(waterlevel_river)

    if len(intersections_at_waterlevel_river) == 0:
        raise ValueError("No intersection with surfaceline found at waterlevel_river")

    # P2 = Snijpunt waterlijn en dijk
    p2 = intersections_at_waterlevel_river[0]
    pl_points.append(p2)

    # P3 = Buitenkruin
    if not surfaceline.has_point_type(DAMPointType.DIKE_CREST_WATER_SIDE):
        raise ValueError("No dike crest water side found")
    p = surfaceline.get_point_by_type(DAMPointType.DIKE_CREST_WATER_SIDE).as_lz()

    if p[0] > pl_points[-1][0]:
        p3 = (
            p[0],
            min(pl_points[-1][1], p[1] - params["offset_dike_crest_water_side"]),
        )
        pl_points.append(p3)

    # P4 = Binnenkruin
    p = surfaceline.get_point_by_type(DAMPointType.DIKE_CREST_LAND_SIDE).as_lz()
    p4 = (p[0], min(pl_points[-1][1], p[1] - params["offset_dike_crest_land_side"]))
    pl_points.append(p4)

    # P5 = OPTIONAL Insteek berm waterzijde
    if surfaceline.has_point_type(DAMPointType.BERM_START_LAND_SIDE):
        p = surfaceline.get_point_by_type(DAMPointType.BERM_START_LAND_SIDE).as_lz()
        p5 = (p[0], min(pl_points[-1][1], p[1] - params["offset_surface_line"]))
        pl_points.append(p5)

    # P6 = Teen dijk
    p = surfaceline.get_point_by_type(DAMPointType.DIKE_TOE_LAND_SIDE).as_lz()
    p6 = (p[0], min(pl_points[-1][1], p[1] - params["offset_surface_line"]))
    pl_points.append(p6)

    # P7 = OPTIONAL Insteek sloot waterzijde
    if surfaceline.has_point_type(DAMPointType.DITCH_START_WATER_SIDE):
        p = surfaceline.get_point_by_type(DAMPointType.DITCH_START_WATER_SIDE).as_lz()
        p7 = (p[0], waterlevel_polder)
        pl_points.append(p7)

    # P8 = Meest rechter punt
    p8 = [surfaceline.right, waterlevel_polder]
    pl_points.append(p8)

    # vanaf de binnenkruin moeten we controleren of de punten niet boven het maaiveld (minus offset) uitkomen
    # en of de punten niet oplopen
    xl = p4[0]

    # deze controle doen we tot de sloot insteek of als deze er niet is tot het einde van de geometrie
    xr = (
        surfaceline.right
        if not surfaceline.has_ditch
        else surfaceline.get_point_by_type(DAMPointType.DITCH_START_WATER_SIDE).l
    )

    # bepaal alle x coordinaten van het maaiveld tussen xl en xr
    xs = [p.l for p in surfaceline.points if p.l > xl and p.l <= xr]
    # en voeg de pl coordinaten toe
    xs += [p[0] for p in pl_points if p[0] > xl and p[0] <= xr]
    # verwijder dubbelingen
    xs = sorted(list(set(xs)))

    # bepaal de z coordinaten op basis van de initiele freatische lijn
    zpl = [z_at(pl_points, x) for x in xs]
    zmv = [surfaceline.z_at(x) for x in xs]

    # check of ze boven het maaiveld uitkomen en zo ja dan verplaatsen naar maaiveld - offset
    for i in range(len(zpl)):
        if zpl[i] > zmv[i] - params["offset_surface_line"]:
            zpl[i] = zmv[i] - params["offset_surface_line"]

    # maak de nieuwe pl lijn
    # voeg eerst de punten tot en met de binnenkruin toe
    final_pl_points = [[p[0], p[1]] for p in pl_points if p[0] <= xl]

    # voeg alle punten tussen xl en xr toe en check de hoogte tov mv
    for x, z in zip(xs, zpl):
        final_pl_points.append([x, z])

    # als xr != levee.right voeg ook dan nog de oude punten toe
    if xr != surfaceline.right:
        final_pl_points += [p for p in pl_points if p[0] > xr]

    for i in range(1, len(final_pl_points)):
        if final_pl_points[i - 1][1] < final_pl_points[i][1]:
            final_pl_points[i][1] = final_pl_points[i - 1][1]

    return clean_points(final_pl_points)


if __name__ == "__main__":
    if Path(DATABASE_PATH).exists():
        Path(DATABASE_PATH).unlink()
    dam_analysis = import_rijnland(DAM_INPUT_PATH)
    db = DatabaseHandler(DATABASE_PATH)
    db.save_analysis(dam_analysis, "Rijnland")

    dam_analysis = db.load_analysis(1)

    dam_analysis.create_stix(
        OUTPUT_PATH,
        soils_algorithm=rijnland_soil_algorithm,
        phreatic_line_algorithm=rijnland_phreatic_line_algorithm,
        max_soilprofile_depth=30,
    )
