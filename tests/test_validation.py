import pytest
from src.utils.validators import (
    validate_temperature,
    validate_steps,
    validate_molecule_name,
    validate_calculation_method
)
from src.utils.exceptions import ValidationError
from src.core.molecule import CalculationMethod

def test_validate_temperature():
    """Test temperature validation."""
    # Valid temperatures
    assert validate_temperature(298.0) == 298.0
    assert validate_temperature(100.0) == 100.0
    assert validate_temperature(600.0) == 600.0
    
    # Invalid temperatures
    with pytest.raises(ValidationError):
        validate_temperature(-1.0)
    with pytest.raises(ValidationError):
        validate_temperature(1000.0)
    with pytest.raises(ValidationError):
        validate_temperature(0.0)

def test_validate_steps():
    """Test conformer steps validation."""
    # Valid step counts
    assert validate_steps(1000) == 1000
    assert validate_steps(100) == 100
    assert validate_steps(10000) == 10000
    
    # Invalid step counts
    with pytest.raises(ValidationError):
        validate_steps(0)
    with pytest.raises(ValidationError):
        validate_steps(-100)
    with pytest.raises(ValidationError):
        validate_steps(1000001)

def test_validate_molecule_name():
    """Test molecule name validation."""
    # Valid names
    assert validate_molecule_name("ethanol") == "ethanol"
    assert validate_molecule_name("ethyl acetate") == "ethyl acetate"
    assert validate_molecule_name("2-propanol") == "2-propanol"
    
    # Invalid names
    with pytest.raises(ValidationError):
        validate_molecule_name("")
    with pytest.raises(ValidationError):
        validate_molecule_name("invalid/name")
    with pytest.raises(ValidationError):
        validate_molecule_name("name with * symbol")

def test_validate_calculation_method():
    """Test calculation method validation."""
    # Valid methods
    assert validate_calculation_method(CalculationMethod.PM7) == CalculationMethod.PM7
    assert validate_calculation_method(CalculationMethod.AM1) == CalculationMethod.AM1
    
    # Invalid methods
    with pytest.raises(ValidationError):
        validate_calculation_method("invalid_method")
    with pytest.raises(ValidationError):
        validate_calculation_method(None)