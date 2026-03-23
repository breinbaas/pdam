import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import List, Optional, Union

from objects.dam import (
    DAMSoil,
    DAMLocation,
    DAMScenario,
    DAMInput,
    DAMSurfaceLine,
    DAMSubSoil,
    DAMAnalysis,
    DAMStage,
)


class DatabaseHandler:
    """
    Handles reading and writing DAMAnalysis data to a SQLite or Postgres database.

    Defaults to SQLite. To use Postgres, set db_type='postgres' and provide
    a connection string as db_path.
    """

    def __init__(self, db_path: str = "pdam.db", db_type: str = "sqlite"):
        self.db_path = db_path
        self.db_type = db_type
        self.p = "?" if db_type == "sqlite" else "%s"
        self._init_db()

    def _get_connection(self):
        if self.db_type == "sqlite":
            return sqlite3.connect(self.db_path)
        elif self.db_type == "postgres":
            import psycopg2

            return psycopg2.connect(self.db_path)
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def _init_db(self):
        """Initializes the database schema if it doesn't exist."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            if self.db_type == "sqlite":
                pk_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
            else:
                pk_type = "SERIAL PRIMARY KEY"

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS analyses (
                    id {pk_type},
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS soils (
                    id {pk_type},
                    analysis_id INTEGER,
                    name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    FOREIGN KEY (analysis_id) REFERENCES analyses (id)
                )
                """
            )
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS locations (
                    id {pk_type},
                    analysis_id INTEGER,
                    external_id TEXT NOT NULL,
                    surfaceline_data TEXT NOT NULL,
                    subsoils_data TEXT NOT NULL,
                    FOREIGN KEY (analysis_id) REFERENCES analyses (id)
                )
                """
            )
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS scenarios (
                    id {pk_type},
                    analysis_id INTEGER,
                    name TEXT NOT NULL,
                    location_external_id TEXT NOT NULL,
                    stages_data TEXT NOT NULL,
                    FOREIGN KEY (analysis_id) REFERENCES analyses (id)
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def save_analysis(self, analysis: DAMAnalysis, name: str) -> int:
        """Saves a DAMAnalysis object to the database."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Insert analysis record
            cursor.execute(f"INSERT INTO analyses (name) VALUES ({self.p})", (name,))

            if self.db_type == "sqlite":
                analysis_id = cursor.lastrowid
            else:
                cursor.execute("SELECT LASTVAL()")
                analysis_id = cursor.fetchone()[0]

            # Save soils
            if analysis.input and analysis.input.soils:
                for soil in analysis.input.soils:
                    cursor.execute(
                        f"INSERT INTO soils (analysis_id, name, data) VALUES ({self.p}, {self.p}, {self.p})",
                        (analysis_id, soil.name, soil.model_dump_json()),
                    )

            # Save locations
            if analysis.input and analysis.input.locations:
                for location in analysis.input.locations:
                    cursor.execute(
                        f"INSERT INTO locations (analysis_id, external_id, surfaceline_data, subsoils_data) VALUES ({self.p}, {self.p}, {self.p}, {self.p})",
                        (
                            analysis_id,
                            location.id,
                            (
                                location.surfaceline.model_dump_json()
                                if location.surfaceline
                                else "{}"
                            ),
                            json.dumps([s.model_dump() for s in location.subsoils]),
                        ),
                    )

            # Save scenarios
            if analysis.scenarios:
                for scenario in analysis.scenarios:
                   
                    cursor.execute(
                        f"INSERT INTO scenarios (analysis_id, name, location_external_id, stages_data) VALUES ({self.p}, {self.p}, {self.p}, {self.p})",
                        (
                            analysis_id,
                            scenario.name,
                            scenario.location.id if scenario.location else None,
                            json.dumps([s.model_dump() for s in scenario.stages]),
                        ),
                    )
            conn.commit()
            return analysis_id
        finally:
            conn.close()

    def load_analysis(self, analysis_id: int) -> DAMAnalysis:
        """Loads a DAMAnalysis object from the database by its ID."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Load soils
            cursor.execute(
                f"SELECT data FROM soils WHERE analysis_id = {self.p}", (analysis_id,)
            )
            soils = [DAMSoil.model_validate_json(row[0]) for row in cursor.fetchall()]

            # Load locations
            cursor.execute(
                f"SELECT external_id, surfaceline_data, subsoils_data FROM locations WHERE analysis_id = {self.p}",
                (analysis_id,),
            )
            locations = []
            for row in cursor.fetchall():
                external_id, surfaceline_json, subsoils_json = row
                surfaceline = DAMSurfaceLine.model_validate_json(surfaceline_json)
                subsoils_raw = json.loads(subsoils_json)
                subsoils = [DAMSubSoil.model_validate(s) for s in subsoils_raw]
                locations.append(
                    DAMLocation(
                        id=external_id, surfaceline=surfaceline, subsoils=subsoils
                    )
                )

            # Load scenarios
            cursor.execute(
                f"SELECT name, location_external_id, stages_data FROM scenarios WHERE analysis_id = {self.p}",
                (analysis_id,),
            )
            scenarios = []
            for row in cursor.fetchall():
                name, loc_id, stages_data = row
                stages_raw = json.loads(stages_data)
                stages = [DAMStage.model_validate(s) for s in stages_raw]

                # Find the location object
                location = next((l for l in locations if l.id == loc_id), None)

                scenarios.append(
                    DAMScenario(name=name, location=location, stages=stages)
                )

            dam_input = DAMInput(soils=soils, locations=locations)
            return DAMAnalysis(input=dam_input, scenarios=scenarios)
        finally:
            conn.close()

    def list_analyses(self):
        """Returns a list of all saved analyses."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, created_at FROM analyses ORDER BY created_at DESC"
            )
            return cursor.fetchall()
        finally:
            conn.close()
