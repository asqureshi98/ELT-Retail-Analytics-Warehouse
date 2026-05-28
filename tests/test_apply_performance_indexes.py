from scripts.apply_performance_indexes import build_connection_kwargs


def test_build_connection_kwargs_uses_local_defaults(monkeypatch):
    for key in ["POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]:
        monkeypatch.delenv(key, raising=False)

    assert build_connection_kwargs() == {
        "host": "localhost",
        "port": 5432,
        "dbname": "retail_warehouse",
        "user": "retail_user",
        "password": "retail_password",
    }


def test_build_connection_kwargs_accepts_environment_overrides(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "postgres")
    monkeypatch.setenv("POSTGRES_PORT", "15432")
    monkeypatch.setenv("POSTGRES_DB", "analytics")
    monkeypatch.setenv("POSTGRES_USER", "analytics_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")

    assert build_connection_kwargs() == {
        "host": "postgres",
        "port": 15432,
        "dbname": "analytics",
        "user": "analytics_user",
        "password": "secret",
    }
