import pytest
from core.molecule import Molecule
from config.settings import Settings
from services.file_service import FileService
from services.pubchem_service import PubChemService
from services.conversion_service import ConversionService
from services.calculation_service import CalculationService
from config.constants import *
import os

@pytest.fixture
def sample_molecule():
    """Retorna uma molécula de teste."""
    return Molecule(name="test_molecule")

@pytest.fixture(scope="session")
def settings():
    """Retorna um objeto Settings para os testes."""
    return Settings()

@pytest.fixture(scope="session")
def file_service():
    """Retorna um objeto FileService para os testes."""
    return FileService()

@pytest.fixture(scope="session")
def pubchem_service():
    """Retorna um objeto PubChemService para os testes."""
    return PubChemService()

@pytest.fixture(scope="session")
def conversion_service(settings):
    """Retorna um objeto ConversionService para os testes."""
    return ConversionService(settings)

@pytest.fixture(scope="session")
def calculation_service(settings, file_service, conversion_service):
    """Retorna um objeto CalculationService para os testes."""
    return CalculationService(settings, file_service, conversion_service)