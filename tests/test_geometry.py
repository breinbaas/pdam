import sys
import os
sys.path.append(os.getcwd())

from helpers.geometry import extract_polygon_from_soilpolygons
from objects.dam import SoilPolygon

def test_extract_polygon():
    # 1. Completely covered
    sp1 = SoilPolygon(soil_name="Soil1", points=[(0, 0), (2, 0), (2, 2), (0, 2)])
    pg_sub = SoilPolygon(soil_name="Sub", points=[(-1, -1), (3, -1), (3, 3), (-1, 3)])
    
    result = extract_polygon_from_soilpolygons([sp1], pg_sub)
    print(f"Test 1 (Completely covered): Expected 0, Got {len(result)}")
    assert len(result) == 0

    # 2. Partially covered (half)
    sp2 = SoilPolygon(soil_name="Soil2", points=[(0, 0), (2, 0), (2, 2), (0, 2)])
    pg_sub2 = SoilPolygon(soil_name="Sub2", points=[(1, -1), (3, -1), (3, 3), (1, 3)])
    
    result = extract_polygon_from_soilpolygons([sp2], pg_sub2)
    print(f"Test 2 (Partially covered): Expected 1, Got {len(result)}")
    assert len(result) == 1
    assert result[0].soil_name == "Soil2"
    # Result should be [(0, 0), (1, 0), (1, 2), (0, 2)]
    print(f"Result points: {result[0].points}")

    # 3. Small remnant (area <= 0.01)
    sp3 = SoilPolygon(soil_name="Soil3", points=[(0, 0), (2, 0), (2, 2), (0, 2)])
    # Subtracting everything except a very thin slice: 2 * 0.005 = 0.01
    pg_sub3 = SoilPolygon(soil_name="Sub3", points=[(0.005, -1), (3, -1), (3, 3), (0.005, 3)])
    
    result = extract_polygon_from_soilpolygons([sp3], pg_sub3)
    print(f"Test 3 (Small remnant 0.01): Expected 0, Got {len(result)}")
    assert len(result) == 0

    # 4. Larger remnant (area > 0.01)
    sp4 = SoilPolygon(soil_name="Soil4", points=[(0, 0), (2, 0), (2, 2), (0, 2)])
    # 2 * 0.011 = 0.022
    pg_sub4 = SoilPolygon(soil_name="Sub4", points=[(0.011, -1), (3, -1), (3, 3), (0.011, 3)])
    
    result = extract_polygon_from_soilpolygons([sp4], pg_sub4)
    print(f"Test 4 (Larger remnant 0.022): Expected 1, Got {len(result)}")
    assert len(result) == 1

    print("All tests passed!")

if __name__ == "__main__":
    test_extract_polygon()
