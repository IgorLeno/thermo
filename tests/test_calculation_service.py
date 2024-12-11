import pytest
from services.calculation_service import CalculationService
from core.molecule import Molecule
from config.constants import *
from unittest.mock import patch, Mock
import re

# Mock para subprocess.Popen
@pytest.fixture
def mock_popen():
    """Mocka o subprocess.Popen para simular a execução do CREST e xTB."""
    mock_process = Mock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = ("", "")  # Retorna tupla vazia para stdout e stderr
    with patch("subprocess.Popen", return_value=mock_process) as mock_popen:
        yield mock_popen

def test_run_crest_success(calculation_service, sample_molecule, tmp_path, mock_popen):
    """Testa a execução bem-sucedida do CREST."""
    xyz_file = tmp_path / "test.xyz"
    xyz_file.write_text("Test XYZ content")
    sample_molecule.xyz_path = str(xyz_file)
    sample_molecule.name = "test"

    calculation_service.run_crest(sample_molecule)

    assert (CREST_DIR / "test" / CREST_CONFORMERS_FILE).exists()
    assert (CREST_DIR / "test" / CREST_BEST_FILE).exists()

def test_run_xtb_opt_success(calculation_service, sample_molecule, tmp_path, mock_popen):
    """Testa a execução bem-sucedida da otimização com xTB."""
    crest_best_file = tmp_path / "crest_best.xyz"
    crest_best_file.write_text("Test XYZ content")
    sample_molecule.crest_best_path = str(crest_best_file)
    sample_molecule.name = "test"

    calculation_service.run_xtb_opt(sample_molecule)

    assert (XTB_DIR / "test" / XTBOPT_FILE).exists()

def test_run_xtb_hess_success(calculation_service, sample_molecule, tmp_path, mock_popen):
    """Testa a execução bem-sucedida do cálculo da Hessiana com xTB."""
    xtbopt_file = tmp_path / "xtbopt.xyz"
    xtbopt_file.write_text("Test XYZ content")
    sample_molecule.xtb_opt_path = str(xtbopt_file)
    sample_molecule.name = "test"

    calculation_service.run_xtb_hess(sample_molecule)

    assert (XTB_DIR / "test" / HESSIAN_FILE).exists()
    assert (XTB_DIR / "test" / VIB_SPECTRUM_FILE).exists()
    assert (XTB_DIR / "test" / THERMOCHEMISTRY_FILE).exists()

def test_extract_formation_enthalpy_success(calculation_service, sample_molecule, tmp_path):
    """Testa a extração bem-sucedida da entalpia de formação."""
    xtbhess_file = tmp_path / "xtbhess.log"
    xtbhess_file.write_text("""
    ... other text ...
    formation enthalpy              Eh      -12.345            1
    ... other text ...
    """)
    sample_molecule.thermochemistry_path = str(xtbhess_file)
    sample_molecule.name = "test"

    calculation_service.extract_formation_enthalpy(sample_molecule)

    assert sample_molecule.formation_enthalpy == pytest.approx(-12.345 * 627.509)

def test_run_calculation_integration(calculation_service, sample_molecule, tmp_path, mock_popen):
    """Testa a integração das etapas de cálculo (CREST, otimização, Hessiana)."""
    xyz_file = tmp_path / "test.xyz"
    xyz_file.write_text("Test XYZ content")
    sample_molecule.xyz_path = str(xyz_file)
    sample_molecule.name = "test"

    calculation_service.run_calculation(sample_molecule)

    assert (OUTPUT_DIR / "test" / XTBOPT_FILE).exists()
    assert (OUTPUT_DIR / "test" / CREST_BEST_FILE).exists()
    assert (OUTPUT_DIR / "test" / CREST_CONFORMERS_FILE).exists()
    assert (OUTPUT_DIR / "test" / THERMOCHEMISTRY_FILE).exists()

def test_extract_formation_enthalpy_not_found(calculation_service, sample_molecule, tmp_path):
    """Testa o caso em que a entalpia de formação não é encontrada."""
    xtbhess_file = tmp_path / "xtbhess.log"
    xtbhess_file.write_text("... other text ...")
    sample_molecule.thermochemistry_path = str(xtbhess_file)
    sample_molecule.name = "test"

    calculation_service.extract_formation_enthalpy(sample_molecule)

    assert sample_molecule.formation_enthalpy is None

def test_run_crest_error(calculation_service, sample_molecule, tmp_path, mock_popen):
    """Testa o tratamento de erros na execução do CREST."""
    xyz_file = tmp_path / "test.xyz"
    xyz_file.write_text("Test XYZ content")
    sample_molecule.xyz_path = str(xyz_file)
    sample_molecule.name = "test"

    # Configura o mock para simular um erro na execução do CREST
    mock_popen.return_value.returncode = 1
    mock_popen.return_value.communicate.return_value = ("", "CREST error")

    with pytest.raises(RuntimeError, match=re.escape(f"Erro ao executar o CREST para a molécula {sample_molecule.name}.")):
        calculation_service.run_crest(sample_molecule)

def test_run_xtb_opt_error(calculation_service, sample_molecule, tmp_path, mock_popen):
    """Testa o tratamento de erros na execução da otimização com xTB."""
    crest_best_file = tmp_path / "crest_best.xyz"
    crest_best_file.write_text("Test XYZ content")
    sample_molecule.crest_best_path = str(crest_best_file)
    sample_molecule.name = "test"

    # Configura o mock para simular um erro na execução do xTB
    mock_popen.return_value.returncode = 1
    mock_popen.return_value.communicate.return_value = ("", "xTB opt error")

    with pytest.raises(RuntimeError, match=re.escape(f"Erro ao executar a otimização com xTB para a molécula {sample_molecule.name}.")):
        calculation_service.run_xtb_opt(sample_molecule)

def test_run_xtb_hess_error(calculation_service, sample_molecule, tmp_path, mock_popen):
    """Testa o tratamento de erros na execução do cálculo da Hessiana com xTB."""
    xtbopt_file = tmp_path / "xtbopt.xyz"
    xtbopt_file.write_text("Test XYZ content")
    sample_molecule.xtb_opt_path = str(xtbopt_file)
    sample_molecule.name = "test"

    # Configura o mock para simular um erro na execução do xTB
    mock_popen.return_value.returncode = 1
    mock_popen.return_value.communicate.return_value = ("", "xTB hess error")

    with pytest.raises(RuntimeError, match=re.escape(f"Erro ao executar o cálculo da Hessiana com xTB para a molécula {sample_molecule.name}.")):
        calculation_service.run_xtb_hess(sample_molecule)

def test_run_crest_file_not_found(calculation_service, sample_molecule):
    """Testa o tratamento de erro quando o arquivo XYZ não é encontrado (CREST)."""
    sample_molecule.xyz_path = "nonexistent_file.xyz"
    sample_molecule.name = "test"

    with pytest.raises(FileNotFoundError):
        calculation_service.run_crest(sample_molecule)

def test_run_xtb_opt_file_not_found(calculation_service, sample_molecule):
    """Testa o tratamento de erro quando o arquivo crest_best.xyz não é encontrado (otimização xTB)."""
    sample_molecule.crest_best_path = "nonexistent_file.xyz"
    sample_molecule.name = "test"

    with pytest.raises(FileNotFoundError):
        calculation_service.run_xtb_opt(sample_molecule)

def test_run_xtb_hess_file_not_found(calculation_service, sample_molecule):
    """Testa o tratamento de erro quando o arquivo xtbopt.xyz não é encontrado (Hessiana xTB)."""
    sample_molecule.xtb_opt_path = "nonexistent_file.xyz"
    sample_molecule.name = "test"

    with pytest.raises(FileNotFoundError):
        calculation_service.run_xtb_hess(sample_molecule)