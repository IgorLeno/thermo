import pytest
from services.calculation_service import CalculationService
from core.molecule import Molecule
from config.constants import *
from unittest.mock import patch, Mock
import re

# Mock para subprocess.Popen
@pytest.fixture
def mock_popen():
    """Mocka o subprocess.Popen para simular a execução do CREST."""
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

def test_run_calculation_integration(calculation_service, sample_molecule, tmp_path, mock_popen):
    """Testa a integração das etapas da busca conformacional."""
    xyz_file = tmp_path / "test.xyz"
    xyz_file.write_text("Test XYZ content")
    sample_molecule.xyz_path = str(xyz_file)
    sample_molecule.name = "test"

    calculation_service.run_calculation(sample_molecule)

    assert (OUTPUT_DIR / "test" / CREST_BEST_FILE).exists()
    assert (OUTPUT_DIR / "test" / CREST_CONFORMERS_FILE).exists()

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

def test_run_crest_file_not_found(calculation_service, sample_molecule):
    """Testa o tratamento de erro quando o arquivo XYZ não é encontrado (CREST)."""
    sample_molecule.xyz_path = "nonexistent_file.xyz"
    sample_molecule.name = "test"

    with pytest.raises(FileNotFoundError):
        calculation_service.run_crest(sample_molecule)