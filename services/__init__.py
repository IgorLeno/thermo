# src/services/__init__.py

from pathlib import Path
from typing import NamedTuple

from .program_manager import ProgramManager, ProgramType
from .file_service import FileService
from .pubchem_service import PubchemService
from .conversion_service import ConversionService
from .calculation_service import CalculationService
from .cleanup_service import CleanupService
from ..config.settings import ConfigurationManager

class Services(NamedTuple):
    """Container for all service instances"""
    program_manager: ProgramManager
    file_service: FileService
    pubchem_service: PubchemService
    conversion_service: ConversionService
    calculation_service: CalculationService
    cleanup_service: CleanupService
    config_manager: ConfigurationManager

def initialize_services(base_dir: Path) -> Services:
    """
    Initialize all required services in the correct order.
    
    Args:
        base_dir: Base project directory
        
    Returns:
        Services: Named tuple containing all initialized services
    """
    # Initialize program manager first as other services depend on it
    program_manager = ProgramManager(base_dir)
    
    # Initialize cleanup service early as it's needed by other services
    cleanup_service = CleanupService(base_dir)
    
    # Initialize file service
    file_service = FileService(base_dir)
    
    # Initialize PubChem service with repository directory
    pubchem_service = PubchemService(base_dir / 'repository/rep_sdf')
    
    # Initialize conversion service with required dependencies
    conversion_service = ConversionService(program_manager, cleanup_service)
    
    # Initialize configuration manager
    config_dir = base_dir / 'configs'
    config_manager = ConfigurationManager(config_dir)
    
    # Initialize calculation service last as it depends on other services
    calculation_service = CalculationService(
        base_dir=base_dir,
        program_manager=program_manager,
        cleanup_service=cleanup_service,
        n_workers=1
    )
    
    # Return all services in a named tuple
    return Services(
        program_manager=program_manager,
        file_service=file_service,
        pubchem_service=pubchem_service,
        conversion_service=conversion_service,
        calculation_service=calculation_service,
        cleanup_service=cleanup_service,
        config_manager=config_manager
    )