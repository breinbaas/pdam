import sys
import os
import json

# Add current directory to path so we can import modules
sys.path.append(os.getcwd())

from database.database import DatabaseHandler
from objects.dam import (
    DAMAnalysis, 
    DAMSoil, 
    DAMLocation, 
    DAMScenario, 
    DAMInput, 
    DAMSurfaceLine, 
    DAMSubSoil,
    DAMPoint,
    DAMSoilProfile,
    DAMSoilLayer,
    DAMStage
)

def test_database():
    db_file = "test_pdam.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        
    handler = DatabaseHandler(db_path=db_file)
    
    # 1. Create mock data
    soil = DAMSoil(name="Clay", unsaturated_weight=18.0, saturated_weight=20.0, color="#FF0000")
    
    point = DAMPoint(l=0.0, x=0.0, y=0.0, z=0.0, point_type="DIKE_CREST")
    surfaceline = DAMSurfaceLine(id="SL1", points=[point])
    
    profile = DAMSoilProfile(id="P1", layers=[])
    subsoil = DAMSubSoil(crest_profile=profile, toe_profile=profile, probability=50)
    location = DAMLocation(id="LOC1", surfaceline=surfaceline, subsoils=[subsoil])
    
    dam_input = DAMInput(soils=[soil], locations=[location])
    
    stage = DAMStage(
        index=0,
        traffic_load_magnitude=5.0,
        waterlevel_river=2.0,
        waterlevel_polder=-1.0,
        hydraulic_head=1.0
    )
    
    scenario = DAMScenario(
        name="daily", 
        location=location,
        stages=[stage]
    )
    
    analysis = DAMAnalysis(input=dam_input, scenarios=[scenario])
    
    # 2. Save analysis
    print("Saving analysis...")
    analysis_id = handler.save_analysis(analysis, "Test Project")
    print(f"Saved with ID: {analysis_id}")
    
    # 3. Load analysis
    print("Loading analysis...")
    loaded_analysis = handler.load_analysis(analysis_id)
    
    # 4. Verify
    print("Verifying...")
    try:
        assert len(loaded_analysis.input.soils) == 1
        assert loaded_analysis.input.soils[0].name == "Clay"
        assert len(loaded_analysis.input.locations) == 1
        assert loaded_analysis.input.locations[0].id == "LOC1"
        assert loaded_analysis.input.locations[0].subsoils[0].probability == 50
        assert len(loaded_analysis.scenarios) == 1
        assert loaded_analysis.scenarios[0].name == "daily"
        assert loaded_analysis.scenarios[0].location is not None
        assert loaded_analysis.scenarios[0].location.id == "LOC1"
        assert len(loaded_analysis.scenarios[0].stages) == 1
        assert loaded_analysis.scenarios[0].stages[0].index == 0
        assert loaded_analysis.scenarios[0].stages[0].traffic_load_magnitude == 5.0
        
        print("Verification SUCCESSFUL!")
    except AssertionError as e:
        print(f"Verification FAILED: {e}")
        sys.exit(1)
    
    if os.path.exists(db_file):
        os.remove(db_file)

if __name__ == "__main__":
    test_database()
