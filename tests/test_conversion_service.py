import pytest
from services.conversion_service import ConversionService
from core.molecule import Molecule
from config.constants import *
import os
from unittest.mock import patch, Mock

@pytest.fixture
def mock_openbabel():
    """Mocka o subprocess.run para simular a execução do OpenBabel."""
    with patch("subprocess.run") as mock_run:
        yield mock_run

def test_sdf_to_xyz_success(conversion_service, sample_molecule, tmp_path, mock_openbabel):
    """Testa a conversão de SDF para XYZ com um arquivo SDF de teste."""
    # Cria um arquivo SDF de teste
    sdf_file = tmp_path / "test.sdf"
    sdf_file.write_text("Test SDF content")
    sample_molecule.sdf_path = str(sdf_file)
    sample_molecule.name = "test"

    # Configura o mock para simular uma execução bem-sucedida do OpenBabel
    mock_openbabel.return_value.returncode = 0
    mock_openbabel.return_value.stderr = ""

    # Chama a função de conversão
    conversion_service.sdf_to_xyz(sample_molecule)

    # Verifica se o arquivo XYZ foi criado
    xyz_file = XYZ_DIR / "test.xyz"
    assert xyz_file.exists()

def test_sdf_to_xyz_openbabel_not_found(conversion_service, sample_molecule, tmp_path):
    """Testa a conversão de SDF para XYZ quando o OpenBabel não é encontrado."""
    # Configura o mock para simular um erro de arquivo não encontrado
    with patch("subprocess.run", side_effect=FileNotFoundError):
        # Cria um arquivo SDF de teste
        sdf_file = tmp_path / "test.sdf"
        sdf_file.write_text("Test SDF content")
        sample_molecule.sdf_path = str(sdf_file)
        sample_molecule.name = "test"

        # Verifica se a exceção correta é lançada
        with pytest.raises(RuntimeError):
            conversion_service.sdf_to_xyz(sample_molecule)