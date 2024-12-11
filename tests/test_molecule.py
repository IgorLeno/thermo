import pytest
from core.molecule import Molecule

def test_molecule_creation(sample_molecule):
    """Testa a criação de um objeto Molecule."""
    assert sample_molecule.name == "test_molecule"
    assert sample_molecule.sdf_path is None
    assert sample_molecule.xyz_path is None
    # ... (verifique outros atributos)

def test_molecule_string_representation(sample_molecule):
    """Testa a representação em string de um objeto Molecule."""
    assert str(sample_molecule) == "Molecule(name=test_molecule, cid=None)"