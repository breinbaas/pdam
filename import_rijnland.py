from pathlib import Path

from importers.rijnland import import_rijnland
from database.database import DatabaseHandler

DAM_INPUT_PATH = r"C:\Users\brein\Documents\Rijnland"
DATABASE_PATH = r"C:\Users\brein\Documents\Rijnland\Output\rijnland.db"

if __name__ == "__main__":
    if Path(DATABASE_PATH).exists():
        Path(DATABASE_PATH).unlink()
    dam_analysis = import_rijnland(DAM_INPUT_PATH)
    db = DatabaseHandler(DATABASE_PATH)
    db.save_analysis(dam_analysis, "Rijnland")
    loaded_analysis = db.load_analysis(1)
    print(loaded_analysis)
