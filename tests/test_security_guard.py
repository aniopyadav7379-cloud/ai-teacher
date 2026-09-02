import os
import pytest


def test_refuses_to_start_with_default_secret_in_non_dev_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    from backend.core import config
    config.get_settings.cache_clear()

    from fastapi.testclient import TestClient
    import importlib
    import backend.main as main_module
    importlib.reload(main_module)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        with TestClient(main_module.app):
            pass

    # cleanup: restore dev settings for subsequent tests in the same process
    monkeypatch.setenv("APP_ENV", "development")
    config.get_settings.cache_clear()
    importlib.reload(main_module)


def test_starts_fine_with_default_secret_in_development(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    from backend.core import config
    config.get_settings.cache_clear()

    from fastapi.testclient import TestClient
    import importlib
    import backend.main as main_module
    importlib.reload(main_module)

    with TestClient(main_module.app) as client:
        r = client.get("/api/health")
        assert r.status_code == 200
