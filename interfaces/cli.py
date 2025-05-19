
from interfaces.menu import Menu
from interfaces.analysis_cli import AnalysisInterface
from core.molecule import Molecule
from services.calculation_service import CalculationService
from services.file_service import FileService
from services.pubchem_service import PubChemService
from services.conversion_service import ConversionService
from config.settings import Settings
import logging

class CommandLineInterface:
    """
    Classe que implementa a interface de linha de comando do programa.
    """
    def __init__(self, settings: Settings = None, file_service: FileService = None,
                 pubchem_service: PubChemService = None, conversion_service: ConversionService = None,
                 calculation_service: CalculationService = None):
        # Carrega configurações do arquivo se settings não foi fornecido
        if settings is None:
            self.settings = Settings()
            self.settings.load_settings("config.yaml")
        else:
            self.settings = settings
        self.file_service = file_service or FileService()
        self.pubchem_service = pubchem_service or PubChemService()
        self.conversion_service = conversion_service or ConversionService(self.settings)
        self.calculation_service = calculation_service or CalculationService(self.settings, self.file_service, self.conversion_service)
        
        # Inicializa o menu principal
        self.menu = Menu(
            settings=self.settings,
            file_service=self.file_service,
            pubchem_service=self.pubchem_service,
            conversion_service=self.conversion_service,
            calculation_service=self.calculation_service
        )

    def run(self):
        """Executa a interface, delegando para o menu principal."""
        print("\n==================================================")
        print("  Busca Conformacional e Cálculo de Entalpia      ")
        print("  (Tradicional: CREST + MOPAC)                   ")
        print("  (Com Chemperium: CREST + MOPAC + Chemperium)   ")
        print("==================================================")
        
        # Delega para o menu principal
        self.menu.run()
