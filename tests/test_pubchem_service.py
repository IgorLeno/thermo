import pytest
from services.pubchem_service import PubChemService
from core.molecule import Molecule
from config.constants import *
import os

@pytest.mark.parametrize("molecule_name, expected_cid", [
    ("benzene", 5284602),
    ("aspirin", 2244),
])
def test_get_sdf_by_name_success(pubchem_service, molecule_name, expected_cid, file_service):
    """Testa o download de SDFs do PubChem com nomes válidos."""
    sdf_path, cid = pubchem_service.get_sdf_by_name(molecule_name)
    assert sdf_path is not None
    assert cid == expected_cid
    assert os.path.exists(sdf_path)

def test_get_sdf_by_name_not_found(pubchem_service):
    """Testa o download de SDFs do PubChem com nomes inválidos."""
    sdf_path, cid = pubchem_service.get_sdf_by_name("invalid_molecule_name")
    assert sdf_path is None
    assert cid is None