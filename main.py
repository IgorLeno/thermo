from core.molecule import Molecule
from services.calculation_service import CalculationService
from services.pubchem_service import PubChemService
from services.file_service import FileService
from services.conversion_service import ConversionService
from config.settings import Settings
from interfaces.menu import Menu
from interfaces.cli import CommandLineInterface
import logging

def main():
    """
    Função principal do programa thermo_grimme.
    """
    # Configuração do logging
    logging.basicConfig(filename='thermo_grimme.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # Carrega as configurações
    settings = Settings()
    try:
        settings.load_settings("config.yaml")
        logging.info("Configurações carregadas com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao carregar configurações: {e}")
        print(f"Erro ao carregar configurações: {e}")
        return
    
    # Inicializa os serviços
    file_service = FileService()
    pubchem_service = PubChemService()
    conversion_service = ConversionService(settings)
    calculation_service = CalculationService(settings, file_service, conversion_service)
    
    # Inicializa a interface
    # menu = Menu(settings, file_service, pubchem_service, conversion_service, calculation_service)
    cli = CommandLineInterface(settings, file_service, pubchem_service, conversion_service, calculation_service)

    # Inicia o menu
    try:
        # menu.run()
        cli.run()
        logging.info("Programa finalizado com sucesso.")
    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        print(f"Erro inesperado: {e}")

if __name__ == "__main__":
    main()