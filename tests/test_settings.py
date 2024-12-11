import pytest
from config.settings import Settings
from core.calculation import CalculationParameters
import os

def test_settings_default_values(settings):
    """Testa os valores padrão do objeto Settings."""
    assert isinstance(settings.calculation_params, CalculationParameters)
    assert settings.openbabel_path == "obabel"

def test_settings_load_save(settings, tmp_path):
    """Testa o carregamento e salvamento de configurações."""
    config_file = tmp_path / "test_config.yaml"
    settings.calculation_params.n_threads = 8
    settings.openbabel_path = "/test/path/to/openbabel"
    settings.save_settings(str(config_file))

    new_settings = Settings()
    new_settings.load_settings(str(config_file))

    assert new_settings.calculation_params.n_threads == 8
    assert new_settings.openbabel_path == "/test/path/to/openbabel"