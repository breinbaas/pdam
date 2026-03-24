from typing import List, Tuple
from shapely.geometry import (
    LineString,
    MultiPoint,
    Point,
    GeometryCollection,
    MultiLineString,
    Polygon,
    MultiPolygon,
)
from shapely import get_coordinates

from objects.dam import SoilPolygon


def z_at(points: List[Tuple[float, float]], x: float) -> float:
    """Get the z coordinate at a given x coordinate"""
    for i in range(len(points) - 1):
        if points[i][0] <= x <= points[i + 1][0]:
            return points[i][1] + (points[i + 1][1] - points[i][1]) * (
                x - points[i][0]
            ) / (points[i + 1][0] - points[i][0])

    return None


def extract_polygon_from_soilpolygons(
    dam_soil_polygons: List[SoilPolygon], pg_subtract: Polygon
) -> List[SoilPolygon]:
    result_polygons = []

    for sp in dam_soil_polygons:
        sp_shapely = sp.to_shapely()
        diff = sp_shapely.difference(pg_subtract)

        if diff.is_empty:
            continue

        # Extract polygons from the result (could be Polygon, MultiPolygon or GeometryCollection)
        parts = []
        if isinstance(diff, Polygon):
            parts.append(diff)
        elif isinstance(diff, MultiPolygon):
            parts.extend(list(diff.geoms))
        elif isinstance(diff, GeometryCollection):
            for geom in diff.geoms:
                if isinstance(geom, Polygon):
                    parts.append(geom)

        for part in parts:
            if part.area > 0.001:
                # Convert back to SoilPolygon
                # Remove the last point because it's the same as the first in shapely
                points = list(part.exterior.coords)[:-1]
                result_polygons.append(
                    SoilPolygon(soil_name=sp.soil_name, points=points)
                )

    return result_polygons


def clean_points(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    i = 1
    while i < len(points) - 1:
        if points[i - 1][1] == points[i][1] == points[i + 1][1]:
            points.pop(i)
        i += 1
    return points


def polyline_polyline_intersections(
    points_line1: List[Tuple[float, float]],
    points_line2: List[Tuple[float, float]],
) -> List[Tuple[float, float]]:
    result = []

    ls1 = LineString(points_line1)
    ls2 = LineString(points_line2)
    intersections = ls1.intersection(ls2)

    if intersections.is_empty:
        return []
    elif type(intersections) == MultiPoint:
        result = [(g.x, g.y) for g in intersections.geoms]
    elif type(intersections) == Point:
        x, y = intersections.coords.xy
        result = [(x[0], y[0])]
    elif type(intersections) == LineString:
        result += [(p[0], p[1]) for p in get_coordinates(intersections).tolist()]
    elif type(intersections) == GeometryCollection:
        geoms = [g for g in intersections.geoms if type(g) != Point]
        result += [(p[0], p[1]) for p in get_coordinates(geoms).tolist()]
        for p in [g for g in intersections.geoms if type(g) == Point]:
            x, y = p.coords.xy
            result.append((x[0], y[0]))
    elif type(intersections) == MultiLineString:
        geoms = [g for g in intersections.geoms if type(g) != Point]
        if len(geoms) >= 2:
            x1, z1 = geoms[0].coords.xy
            x2, z2 = geoms[1].coords.xy

            if x1 == x2:  # vertical
                x = x1.tolist()[0]
                zs = z1.tolist() + z2.tolist()
                result.append((x, min(zs)))
                result.append((x, max(zs)))
            elif z1 == z2:  # horizontal
                z = z1.tolist()[0]
                xs = x1.tolist() + x2.tolist()
                result.append((min(xs), z))
                result.append((max(xs), z))
            else:
                raise ValueError(
                    f"Unimplemented intersection type '{type(intersections)}' that is not a horizontal or vertical line or consists of more than 2 lines"
                )
        else:
            raise ValueError(
                f"Unimplemented intersection type '{type(intersections)}' with varying x or z coordinates"
            )
    else:
        raise ValueError(
            f"Unimplemented intersection type '{type(intersections)}' {points_line1}"
        )
    return sorted(result, key=lambda x: x[0])
