from unittest.mock import MagicMock

import pytest

from src.dependencies.db import build_db_uri


def make_config(db_uri: str) -> MagicMock:
    config = MagicMock()
    config.db_uri = db_uri
    return config


class TestBuildDbUri:
    def test_postgresql_scheme_replaced_with_psycopg_driver(self):
        config = make_config("postgresql://localhost/mydb")
        result = build_db_uri(config)
        assert result == "postgresql+psycopg://localhost/mydb"

    def test_already_has_psycopg_driver_is_unchanged(self):
        config = make_config("postgresql+psycopg://localhost/mydb")
        result = build_db_uri(config)
        assert result == "postgresql+psycopg://localhost/mydb"

    def test_non_postgresql_uri_raises_value_error(self):
        config = make_config("sqlite:///local.db")
        with pytest.raises(ValueError):
            build_db_uri(config)

    def test_credentials_and_port_preserved(self):
        config = make_config("postgresql://user:pass@localhost:5432/db")
        result = build_db_uri(config)
        assert result == "postgresql+psycopg://user:pass@localhost:5432/db"
