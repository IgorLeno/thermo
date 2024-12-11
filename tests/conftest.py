# tests/conftest.py
import pytest
from pathlib import Path
import tempfile
import shutil
from typing import Dict, Any

from src.core.molecule import Molecule, MoleculeConfiguration, CalculationMethod
from src.services.calculation_service import CalculationService
from src.services.file_service import FileService
from src.services.pubchem_service import PubchemService
from src.services.conversion_service import ConversionService
from src.config.settings import ConfigurationManager
from src.utils.validators import ValidationError

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def base_dir(temp_dir):
    """Set up base directory structure."""
    base = temp_dir / "thermo"
    dirs = [
        "repository/rep_sdf",
        "repository/rep_tgroups",
        "repository/rep_tjump",
        "repository/rep_mopac",
        "final_molecules/out",
        "vega",
        "ammp",
        "mopac",
        "working"
    ]
    for dir_path in dirs:
        (base / dir_path).mkdir(parents=True)
    return base

@pytest.fixture
def config_manager(base_dir):
    """Initialize configuration manager."""
    config_dir = base_dir / "configs"
    return ConfigurationManager(config_dir)

@pytest.fixture
def file_service(base_dir):
    """Initialize file service."""
    return FileService(base_dir)

@pytest.fixture
def pubchem_service(base_dir):
    """Initialize PubChem service."""
    return PubchemService(base_dir / "repository/rep_sdf")

@pytest.fixture
def conversion_service(base_dir):
    """Initialize conversion service."""
    return ConversionService(base_dir / "vega")

@pytest.fixture
def calculation_service(base_dir):
    """Initialize calculation service."""
    return CalculationService(base_dir, n_workers=1, debug=True)

@pytest.fixture
def sample_molecule_config():
    """Create sample molecule configuration."""
    return MoleculeConfiguration(
        name="test_config",
        steps=1000,
        temperature=298.0,
        methods=[CalculationMethod.PM7],
        entropy_methods=[CalculationMethod.PM7]
    )

@pytest.fixture
def sample_molecule(sample_molecule_config):
    """Create sample molecule object."""
    molecule = Molecule("test_molecule", sample_molecule_config)
    molecule.set_pubchem_info("Test Compound", "C2H6O")
    return molecule

# tests/test_molecule.py
def test_molecule_initialization(sample_molecule_config):
    """Test molecule object initialization."""
    molecule = Molecule("ethanol", sample_molecule_config)
    assert molecule.name == "ethanol"
    assert molecule.config == sample_molecule_config
    assert not molecule.errors
    assert not molecule.conformers
    assert not molecule.calculation_results

def test_molecule_add_conformer(sample_molecule):
    """Test adding conformer results."""
    sample_molecule.add_conformer(
        energy=-100.5,
        step=42,
        structure_data=b"ATOM data",
        method="AMMP"
    )
    assert len(sample_molecule.conformers) == 1
    assert sample_molecule.best_conformer.energy == -100.5
    assert sample_molecule.best_conformer.step == 42
    
def pytest_configure(config):
    """Add custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )

def test_molecule_calculation_results(sample_molecule):
    """Test adding calculation results."""
    sample_molecule.add_calculation_result(
        method=CalculationMethod.PM7,
        enthalpy=-50.3,
        entropy=0.15
    )
    assert CalculationMethod.PM7.value in sample_molecule.calculation_results
    result = sample_molecule.calculation_results[CalculationMethod.PM7.value]
    assert result.enthalpy == -50.3
    assert result.entropy == 0.15

# tests/test_calculation.py
from src.core.calculation import CalculationParameters, ConformerSearch

def test_calculation_parameters():
    """Test calculation parameters initialization."""
    params = CalculationParameters(
        working_dir=Path("/tmp/work"),
        output_dir=Path("/tmp/output"),
        method=CalculationMethod.PM7
    )
    assert params.temperature == 298.0
    assert params.cycles == 20000
    assert params.precision == 0.001

@pytest.mark.integration
def test_conformer_search(base_dir, sample_molecule):
    """Test conformer search workflow."""
    params = CalculationParameters(
        working_dir=base_dir / "working",
        output_dir=base_dir / "repository/rep_tjump",
        method=CalculationMethod.PM7
    )
    search = ConformerSearch(params, steps=100)
    result = search.run(sample_molecule)
    assert result
    assert sample_molecule.best_conformer is not None

# tests/test_services.py
def test_file_service_operations(file_service, temp_dir):
    """Test file service basic operations."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")
    
    # Test file copy
    dest_path = file_service.copy_file(test_file, "working")
    assert dest_path.exists()
    assert dest_path.read_text() == "test content"
    
    # Test file move
    moved_path = file_service.move_file(dest_path, "mopac")
    assert moved_path.exists()
    assert not dest_path.exists()

@pytest.mark.integration
def test_pubchem_service(pubchem_service):
    """Test PubChem service functionality."""
    result = pubchem_service.download_structure("ethanol")
    assert result is not None
    assert result.exists()
    assert result.suffix == ".sdf"

def test_conversion_service(conversion_service, temp_dir):
    """Test structure format conversion."""
    # Create test SDF file
    sdf_file = temp_dir / "test.sdf"
    sdf_file.write_text("MOCK SDF CONTENT")
    
    result = conversion_service.convert_structure(
        sdf_file,
        "pdb"
    )
    assert result.exists()
    assert result.suffix == ".pdb"

@pytest.mark.integration
def test_calculation_service(calculation_service, sample_molecule_config):
    """Test full calculation workflow."""
    results = calculation_service.process_molecules(
        ["ethanol"],
        sample_molecule_config
    )
    assert len(results) == 1
    assert not results[0].errors
    assert CalculationMethod.PM7.value in results[0].calculation_results

# tests/test_validation.py
from src.utils.validators import (
    validate_temperature,
    validate_steps,
    validate_molecule_name
)

def test_temperature_validation():
    """Test temperature validation."""
    assert validate_temperature(298.0) == 298.0
    with pytest.raises(ValidationError):
        validate_temperature(-1.0)
    with pytest.raises(ValidationError):
        validate_temperature(1000.0)

def test_steps_validation():
    """Test conformer steps validation."""
    assert validate_steps(1000) == 1000
    with pytest.raises(ValidationError):
        validate_steps(0)
    with pytest.raises(ValidationError):
        validate_steps(1000000)

def test_molecule_name_validation():
    """Test molecule name validation."""
    assert validate_molecule_name("ethanol") == "ethanol"
    assert validate_molecule_name("ethyl acetate") == "ethyl acetate"
    with pytest.raises(ValidationError):
        validate_molecule_name("")
    with pytest.raises(ValidationError):
        validate_molecule_name("invalid/name")