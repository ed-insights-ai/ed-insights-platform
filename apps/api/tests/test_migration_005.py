import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext


VERSIONS = Path(__file__).resolve().parents[1] / "alembic" / "versions"
DATA_TABLES = (
    "schools",
    "games",
    "team_game_stats",
    "player_game_stats",
    "game_events",
)


def _load_005():
    spec = importlib.util.spec_from_file_location(
        "m005", VERSIONS / "005_reset_gac_schools.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_migration(function, connection):
    context = MigrationContext.configure(connection)
    with Operations.context(Operations(context)):
        function()


@pytest.mark.anyio
async def test_005_is_data_preserving():
    engine = sa.create_engine("sqlite://")
    with engine.connect() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE schools ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT, "
            "abbreviation TEXT UNIQUE, "
            "conference TEXT, "
            "mascot TEXT, "
            "gender TEXT, "
            "enabled BOOLEAN)"
        )
        for table in DATA_TABLES[1:]:
            connection.exec_driver_sql(
                f"CREATE TABLE {table} ("
                "id INTEGER PRIMARY KEY, "
                "game_id INTEGER, "
                "school_id INTEGER)"
            )

        connection.exec_driver_sql(
            "INSERT INTO schools (name, abbreviation) VALUES ('Harding', 'HU')"
        )
        connection.exec_driver_sql(
            "INSERT INTO games (id, game_id, school_id) VALUES (1, 1001, 1)"
        )
        for table in DATA_TABLES[2:]:
            connection.exec_driver_sql(
                f"INSERT INTO {table} (id, game_id, school_id) VALUES (1, 1001, 1)"
            )

        def counts():
            return {
                table: connection.exec_driver_sql(
                    f"SELECT COUNT(*) FROM {table}"
                ).scalar()
                for table in DATA_TABLES
            }

        migration = _load_005()
        _run_migration(migration.upgrade, connection)
        after_upgrade = counts()

        assert after_upgrade == {
            "schools": 14,
            "games": 1,
            "team_game_stats": 1,
            "player_game_stats": 1,
            "game_events": 1,
        }

        _run_migration(migration.downgrade, connection)
        assert counts() == after_upgrade
