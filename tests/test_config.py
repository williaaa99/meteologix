import os
import sys
import importlib
import pytest


def test_config_raises_on_missing_required_var(monkeypatch):
    # Remove config from sys.modules if it exists so we can reload it fresh
    if "config" in sys.modules:
        del sys.modules["config"]
    
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("EVOLUTION_API_KEY", raising=False)
    monkeypatch.delenv("WHATSAPP_GROUP_ID", raising=False)
    # Import config without the required vars — should raise KeyError
    with pytest.raises(KeyError):
        import config


def test_config_storage_dir_has_default(monkeypatch):
    # Remove config from sys.modules if it exists so we can reload it fresh
    if "config" in sys.modules:
        del sys.modules["config"]
    
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("EVOLUTION_API_KEY", "evo-key")
    monkeypatch.setenv("WHATSAPP_GROUP_ID", "123@g.us")
    monkeypatch.delenv("STORAGE_DIR", raising=False)
    import config
    importlib.reload(config)
    assert config.STORAGE_DIR == "storage"
