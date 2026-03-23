import os
import shapefile


from geolib.models.dstability.internal import PersistableShadingTypeEnum

from objects.dam import (
    DAMPointType,
    DAMSoil,
    DAMSoilLayer,
    DAMSoilProfile,
    DAMPoint,
    DAMTrafficLoadLocation,
    DAMRevetment,
    DAMSurfaceLine,
    DAMSubSoil,
    DAMLocation,
    DAMInput,
    DAMScenario,
    DAMAnalysis,
)

BOTTOM_LEVEL = -9999.0


def get_point_type(location_id, x, char_points):
    if x == char_points[location_id]["x_surface_level_water_side"]:
        return DAMPointType.SURFACE_LEVEL_WATER_SIDE
    elif x == char_points[location_id]["x_toe_canal"]:
        return DAMPointType.TOE_CANAL
    elif x == char_points[location_id]["x_start_canal"]:
        return DAMPointType.START_CANAL
    elif x == char_points[location_id]["x_dike_toe_water_side"]:
        return DAMPointType.DIKE_TOE_WATER_SIDE
    elif x == char_points[location_id]["x_berm_crest_water_side"]:
        return DAMPointType.BERM_CREST_WATER_SIDE
    elif x == char_points[location_id]["x_berm_start_water_side"]:
        return DAMPointType.BERM_START_WATER_SIDE
    elif x == char_points[location_id]["x_dike_crest_water_side"]:
        return DAMPointType.DIKE_CREST_WATER_SIDE
    elif x == char_points[location_id]["x_traffic_load_water_side"]:
        return DAMPointType.TRAFFIC_LOAD_WATER_SIDE
    elif x == char_points[location_id]["x_traffic_load_land_side"]:
        return DAMPointType.TRAFFIC_LOAD_LAND_SIDE
    elif x == char_points[location_id]["x_dike_crest_land_side"]:
        return DAMPointType.DIKE_CREST_LAND_SIDE
    elif x == char_points[location_id]["x_berm_start_land_side"]:
        return DAMPointType.BERM_START_LAND_SIDE
    elif x == char_points[location_id]["x_berm_crest_land_side"]:
        return DAMPointType.BERM_CREST_LAND_SIDE
    elif x == char_points[location_id]["x_dike_toe_land_side"]:
        return DAMPointType.DIKE_TOE_LAND_SIDE
    elif x == char_points[location_id]["x_ditch_start_water_side"]:
        return DAMPointType.DITCH_START_WATER_SIDE
    elif x == char_points[location_id]["x_ditch_bottom_water_side"]:
        return DAMPointType.DITCH_BOTTOM_WATER_SIDE
    elif x == char_points[location_id]["x_ditch_bottom_land_side"]:
        return DAMPointType.DITCH_BOTTOM_LAND_SIDE
    elif x == char_points[location_id]["x_ditch_start_land_side"]:
        return DAMPointType.DITCH_START_LAND_SIDE
    elif x == char_points[location_id]["x_surface_level_land_side"]:
        return DAMPointType.SURFACE_LEVEL_LAND_SIDE
    else:
        return DAMPointType.NONE


def get_characteristic_points(path):
    lines = open(path, "r").readlines()
    header = lines[0]
    column_names = [a.strip() for a in header.split(";")[1:]]

    result = {}
    for line in lines[1:]:
        args = [a.strip() for a in line.split(";")]
        d = {cn: a for cn, a in zip(column_names, args[1:])}
        location_id = args[0]
        x_surface_level_water_side = float(d["X_Maaiveld buitenwaarts"])
        x_toe_canal = float(d["X_Teen geul"])
        x_start_canal = float(d["X_Insteek geul"])
        x_dike_toe_water_side = float(d["X_Teen dijk buitenwaarts"])
        x_berm_crest_water_side = float(d["X_Kruin buitenberm"])
        x_berm_start_water_side = float(d["X_Insteek buitenberm"])
        x_dike_crest_water_side = float(d["X_Kruin buitentalud"])
        x_traffic_load_water_side = float(d["X_Verkeersbelasting kant buitenwaarts"])
        x_traffic_load_land_side = float(d["X_Verkeersbelasting kant binnenwaarts"])
        x_dike_crest_land_side = float(d["X_Kruin binnentalud"])
        x_berm_start_land_side = float(d["X_Insteek binnenberm"])
        x_berm_crest_land_side = float(d["X_Kruin binnenberm"])
        x_dike_toe_land_side = float(d["X_Teen dijk binnenwaarts"])
        x_ditch_start_water_side = float(d["X_Insteek sloot dijkzijde"])
        x_ditch_bottom_water_side = float(d["X_Slootbodem dijkzijde"])
        x_ditch_bottom_land_side = float(d["X_Slootbodem polderzijde"])
        x_ditch_start_land_side = float(d["X_Insteek sloot polderzijde"])
        x_surface_level_land_side = float(d["X_Maaiveld binnenwaarts"])

        result[location_id] = {
            "x_surface_level_water_side": x_surface_level_water_side,
            "x_toe_canal": x_toe_canal,
            "x_start_canal": x_start_canal,
            "x_dike_toe_water_side": x_dike_toe_water_side,
            "x_berm_crest_water_side": x_berm_crest_water_side,
            "x_berm_start_water_side": x_berm_start_water_side,
            "x_dike_crest_water_side": x_dike_crest_water_side,
            "x_traffic_load_water_side": x_traffic_load_water_side,
            "x_traffic_load_land_side": x_traffic_load_land_side,
            "x_dike_crest_land_side": x_dike_crest_land_side,
            "x_berm_start_land_side": x_berm_start_land_side,
            "x_berm_crest_land_side": x_berm_crest_land_side,
            "x_dike_toe_land_side": x_dike_toe_land_side,
            "x_ditch_start_water_side": x_ditch_start_water_side,
            "x_ditch_bottom_water_side": x_ditch_bottom_water_side,
            "x_ditch_bottom_land_side": x_ditch_bottom_land_side,
            "x_ditch_start_land_side": x_ditch_start_land_side,
            "x_surface_level_land_side": x_surface_level_land_side,
        }

    return result


def get_subsoils(path):
    result = {}
    for line in open(path, "r").readlines()[1:]:
        args = [a.strip() for a in line.split(";")]
        result[args[2]] = {
            "soilprofile_id_crest": args[0],
            "soilprofile_id_toe": args[1],
            "soilgeometry2D_name": args[4],
        }
    return result


def get_locations(path):
    result = {}
    for line in open(path, "r").readlines()[1:]:
        args = [a.strip() for a in line.split(";")]
        result[args[0]] = {
            "surfaceline_id": args[1],
            "segment_id": args[2],
            "x_soilgeometry2D_origin": float(args[3]),
        }
    return result


def get_segments(path):
    result = {}
    for line in open(path, "r").readlines()[1:]:
        args = [a.strip() for a in line.split(";")]
        result[args[0]] = {
            "soilgeometry2D_name": args[1],
            "probability": float(args[2]),
        }
    return result


def get_slopelayers(path):
    result = {}
    for line in open(path, "r").readlines()[1:]:
        args = [a.strip() for a in line.split(";")]
        result[args[1]] = {
            "x_offset": float(args[3]),
            "soilgeometry2D_name": args[4],
            "slope_layer_material": args[8],
            "slope_layer_thickness": float(args[9]),
        }
    return result


def get_soils(path):
    result = {}
    for line in open(path, "r").readlines()[1:]:
        args = [a.strip() for a in line.split(";")]
        result[args[0]] = {
            "yd": float(args[1]),
            "ys": float(args[2]),
            "phi": float(args[3]),
            "cohesie": float(args[4]),
            "color": args[5],
        }
    return result


def get_soilprofiles(path):
    lines = open(path).readlines()
    result = {}
    for line in lines[1:]:
        args = [a.strip() for a in line.split(";")]
        if len(args) > 0:
            profile_id = args[3]
            soil_name = args[2]
            top_level = float(args[0])

            if profile_id not in result:
                result[profile_id] = []

            # Only add if it's the first item or the soil_name is different from the last one
            if (
                not result[profile_id]
                or result[profile_id][-1]["soil_name"] != soil_name
            ):
                result[profile_id].append(
                    {"soil_name": soil_name, "top_level": top_level}
                )
    return result


def get_surfacelines(path):
    lines = open(path, "r").readlines()
    result = {}
    for line in lines[1:]:
        args = [a.strip() for a in line.split(";")]
        id = args[0]
        xs = [float(a) for a in args[1::3]]
        ys = [float(a) for a in args[2::3]]
        zs = [float(a) for a in args[3::3]]

        result[id] = (xs, ys, zs)

    return result


def get_waterlevels(path):
    sf = shapefile.Reader(path)
    polderpeilen = {}
    for rec in sf.records():
        polderpeilen[rec["locationid"]] = {
            "max": rec["MAX_PEIL"],
            "min": rec["MIN_PEIL"],
        }

    return polderpeilen


def get_hydraulic_head(path):
    sf = shapefile.Reader(path)
    stijghoogtes = {}
    for rec in sf.records():
        stijghoogtes[rec["locationid"]] = rec["HOOGTE"]

    return stijghoogtes


def get_design_waterlevel(path):
    sf = shapefile.Reader(path)
    design_waterlevels = {}
    for rec in sf.records():
        design_waterlevels[rec["CODE"]] = {
            "streefpeil": rec["STREEFPEIL"],
            "toetspeil": rec["TOETSPEIL"],
        }

    return design_waterlevels


def get_traffic_load(path):
    sf_trafficloads = shapefile.Reader(path)
    traffic_loads = {}
    for rec in sf_trafficloads.records():
        traffic_loads[rec["NAAM"]] = {
            "magnitude": rec["MAGNITUDE"],
        }

    return traffic_loads


def import_rijnland(path):
    filenames = []
    if os.path.exists(path) and os.path.isdir(path):
        filenames = [
            f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))
        ]
    else:
        raise ValueError(f"Error: Path {path} is not a directory.")

    surfaceline_id_location_id_dict = {}

    for filename in filenames:
        if filename.find("characteristicpoints.csv") > -1:
            characteristic_points = get_characteristic_points(
                os.path.join(path, filename)
            )
        elif filename.find("combinationfile.csv") > -1:
            subsoils = get_subsoils(os.path.join(path, filename))
        elif filename.find("locations.csv") > -1:
            locations = get_locations(os.path.join(path, filename))
            for k, v in locations.items():
                surfaceline_id_location_id_dict[v["surfaceline_id"]] = k
        elif filename.find("segments.csv") > -1:
            segments = get_segments(os.path.join(path, filename))
        elif filename.find("slopelayers.csv") > -1:
            revetments = get_slopelayers(os.path.join(path, filename))
        elif filename.find("soilparameters.csv") > -1:
            soils = get_soils(os.path.join(path, filename))
        elif filename.find("soilprofiles.csv") > -1:
            soilprofiles = get_soilprofiles(os.path.join(path, filename))
        elif filename.find("surfacelines.csv") > -1:
            surfacelines = get_surfacelines(os.path.join(path, filename))
        elif filename.find("locations_peilen.shp") > -1:
            waterlevels = get_waterlevels(os.path.join(path, filename))
        elif filename.find("stijghoogteAtLocations.shp") > -1:
            hydraulic_head = get_hydraulic_head(os.path.join(path, filename))
        elif filename.find("toetspeil_V1.shp") > -1:
            design_waterlevel = get_design_waterlevel(os.path.join(path, filename))
        elif filename.find("verkeersbelasting_stbi1.shp") > -1:
            traffic_loads = get_traffic_load(os.path.join(path, filename))

    # grondsoorten
    dam_soils = []
    for k, v in soils.items():
        dam_soils.append(
            DAMSoil(
                name=k,
                unsaturated_weight=float(v["yd"]),
                saturated_weight=float(v["ys"]),
                strength_model_above="Mohr-Coulomb",
                strength_model_below="Mohr-Coulomb",
                is_probabilistic=False,
                c_mean=float(v["cohesie"]),
                c_std=0.0,
                phi_mean=float(v["phi"]),
                phi_std=0.0,
                psi_mean=0.0,
                psi_std=0.0,
                shear_stress_ratio_s_mean=0.0,
                shear_stress_ratio_s_std=0.0,
                strength_exponent_m_mean=0.0,
                strength_exponent_m_std=0.0,
                is_probabilistic_pop=False,
                pop_mean=0.0,
                pop_std=0.0,
                c_phi_correlated=False,
                s_m_correlated=False,
                consolidation_traffic_load=50,
                color=f"#80{v['color'][1:]}",
                pattern=PersistableShadingTypeEnum.DIAGONAL_A,
            )
        )
    # profielen
    dam_soilprofiles = {}
    for k, v in soilprofiles.items():
        soillayers = []

        for i, l in enumerate(v):
            if i == len(v) - 1:
                bottom_level = BOTTOM_LEVEL
            else:
                bottom_level = float(v[i + 1]["top_level"])
            soillayers.append(
                DAMSoilLayer(
                    top=float(l["top_level"]),
                    bottom=bottom_level,
                    soil_name=l["soil_name"],
                )
            )
            bottom_level = float(l["top_level"])

        dam_soilprofiles[k] = DAMSoilProfile(
            name=k,
            layers=soillayers,
        )

    # dwarsprofielen
    dam_surfacelines = {}
    for k, v in surfacelines.items():
        xs, ys, zs = v[0], v[1], v[2]

        is_2d = all(y == 0.0 for y in ys)

        if is_2d:
            points = [
                [l, x, 0.0, z, get_point_type(k, x, characteristic_points)]
                for l, x, z in zip(xs, xs, zs)
            ]
        else:
            points, dl = [], 0
            for i in range(1, len(xs)):
                if i == 1:
                    points.append(
                        [
                            dl,
                            xs[0],
                            ys[0],
                            zs[0],
                            get_point_type(k, xs[0], characteristic_points),
                        ]
                    )
                x1, y1 = xs[i - 1], ys[i - 1]
                x2, y2 = xs[i], ys[i]
                dl += math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                points.append(
                    [
                        dl,
                        x2,
                        y2,
                        zs[i],
                        get_point_type(k, xs[i], characteristic_points),
                    ]
                )

        # convert to dike_crest_land_side as 0.0
        adjust_l, dl = False, 0.0
        for p in points:
            if p[4] == DAMPointType.DIKE_CREST_LAND_SIDE:
                if p[0] != 0.0:
                    adjust_l = True
                    dl = p[0] - points[0][0]

        if adjust_l:
            for i in range(len(points)):
                points[i][0] += dl

        revetment = None
        if k in revetments.keys():
            d_revetment = revetments[k]

            # find dike_toe_land_side
            x_dike_toe_land_side = None
            for p in points:
                if p[4] == DAMPointType.DIKE_TOE_LAND_SIDE:
                    x_dike_toe_land_side = p[1]
                    break

            if (
                x_dike_toe_land_side is not None
                and d_revetment["slope_layer_thickness"] > 0
            ):
                revetment = DAMRevetment(
                    left=x_dike_toe_land_side,
                    right=x_dike_toe_land_side + d_revetment["x_offset"],
                    thickness=d_revetment["slope_layer_thickness"],
                    soil_name=d_revetment["slope_layer_material"],
                )

        trafficload = None
        if k in traffic_loads.keys():
            d_trafficload = traffic_loads[k]
            tl_start = None
            tl_end = None
            for p in points:
                if p[4] == DAMPointType.TRAFFIC_LOAD_WATER_SIDE:
                    tl_start = p[0]
                elif p[4] == DAMPointType.TRAFFIC_LOAD_LAND_SIDE:
                    tl_end = p[0]
                    break

            if tl_start is not None and tl_end is not None:
                trafficload = DAMTrafficLoadLocation(
                    left=tl_start,
                    right=tl_end,
                    magnitude=d_trafficload["magnitude"],
                )

        dam_surfacelines[k] = DAMSurfaceLine(
            id=k,
            points=[
                DAMPoint(l=p[0], x=p[1], y=p[2], z=p[3], type=p[4]) for p in points
            ],
            revetment=revetment,
            trafficload=trafficload,
        )

    dam_locations = []
    for location_id, v in locations.items():
        subsoil_dict = subsoils[v["surfaceline_id"]]
        subsoil = DAMSubSoil(
            crest_profile=dam_soilprofiles[subsoil_dict["soilprofile_id_crest"]],
            toe_profile=dam_soilprofiles[subsoil_dict["soilprofile_id_toe"]],
            probability=segments[location_id]["probability"],
        )

        dam_location = DAMLocation(
            id=location_id,
            subsoils=[subsoil],
            surfaceline=dam_surfacelines[v["surfaceline_id"]],
        )
        dam_locations.append(dam_location)

    # TODO >> Create scenarios

    dam_input = DAMInput(
        soils=dam_soils,
        locations=dam_locations,
    )

    dam_scenarios = []
    for location in dam_locations:
        for subsoil in location.subsoils:
            daily_level = design_waterlevel[location.id]["streefpeil"]
            extreme_level = design_waterlevel[location.id]["toetspeil"]
            polder_level = waterlevels[location.id]["max"]
            traffic_load = traffic_loads[location.surfaceline.id]["magnitude"]

            dam_scenarios.append(
                DAMScenario(
                    name="dagelijks",
                    stage=0,
                    location=location,
                    traffic_load_magnitude=traffic_load,
                    waterlevel_river=daily_level,
                    waterlevel_polder=polder_level,
                )
            )

            dam_scenarios.append(
                DAMScenario(
                    name="maatgevend",
                    stage=1,
                    location=location,
                    traffic_load_magnitude=traffic_load,
                    waterlevel_river=extreme_level,
                    waterlevel_polder=polder_level,
                )
            )

    dam_analysis = DAMAnalysis(
        input=dam_input,
        scenarios=dam_scenarios,
    )

    return dam_analysis
