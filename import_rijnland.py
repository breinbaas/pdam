from pathlib import Path
import logging

from importers.rijnland import import_rijnland
from database.database import DatabaseHandler


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

if __name__ == "__main__":
    if Path(DATABASE_PATH).exists():
        Path(DATABASE_PATH).unlink()
    dam_analysis = import_rijnland(DAM_INPUT_PATH)
    db = DatabaseHandler(DATABASE_PATH)
    db.save_analysis(dam_analysis, "Rijnland")

    dam_analysis = db.load_analysis(1)
    dam_analysis.create_stix(OUTPUT_PATH)
