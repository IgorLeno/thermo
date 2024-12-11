import pytest
from core.calculation import CalculationParameters

def test_calculation_parameters_creation():
    """Testa a criação de um objeto CalculationParameters."""
    params = CalculationParameters(n_threads=4, crest_method="gfn1")
    assert params.n_threads == 4
    assert params.crest_method == "gfn1"

def test_crest_command_generation():
    """Testa a geração do comando do CREST."""
    params = CalculationParameters(n_threads=2, crest_method="gfn2")
    command = params.crest_command("test.xyz")
    assert command == ["crest", "test.xyz", "--chrg", "0", "--uhf", "0", "-T", "2", "--gfn", "2"]

def test_xtb_command_generation():
    """Testa a geração do comando do xTB."""
    params = CalculationParameters(n_threads=8)
    command = params.xtb_command("test.xyz", "opt")
    assert command == ["xtb", "test.xyz", "--opt", "--chrg", "0", "--uhf", "0", "-T", "8"]