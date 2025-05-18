# main.py
from interfaces.cli import CommandLineInterface
from config.settings import Settings
from services.file_service import FileService
from services.pubchem_service import PubChemService
from services.conversion_service import ConversionService
from services.calculation_service import CalculationService
from utils.logging_config import setup_application_logging, get_logging_manager
import logging
import os
from pathlib import Path
from datetime import datetime
from config.constants import PDB_DIR, MOPAC_DIR

def setup_directories():
    """
    Configura os diretórios necessários para o programa.
    """
    # Diretórios para a etapa MOPAC
    os.makedirs(PDB_DIR, exist_ok=True)
    os.makedirs(MOPAC_DIR, exist_ok=True)

def main():
    """
    Função principal do programa conformer_search.
    """
    # Configura o sistema de logging centralizado
    setup_application_logging()
    
    # Obtém o gerenciador de logging para acessar informações
    logging_manager = get_logging_manager()
    log_filename = logging_manager.get_log_filename()
    
    logging.info("=== Iniciando o programa de busca conformacional e cálculo de entalpia ===")
    logging.info(f"Log detalhado sendo salvo em: {log_filename}")
    
    # Exibe uma mensagem mais limpa no console
    print("=== Grimme Thermo - Sistema de Busca Conformacional ===")
    print(f"Log detalhado: {log_filename}")
    print("=" * 55)

    # Configura os diretórios necessários
    setup_directories()

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
    
    # Inicializa a interface de linha de comando
    cli = CommandLineInterface(settings, file_service, pubchem_service, conversion_service, calculation_service)

    # Inicia a interface de linha de comando
    try:
        cli.run()
        logging.info("Programa finalizado com sucesso.")
    except Exception as e:
        logging.error(f"Erro inesperado: {e}", exc_info=True)  # Adiciona rastreamento de pilha
        print(f"Erro inesperado: {e}")
        print(f"Consulte o log para mais detalhes: {log_filename}")

if __name__ == "__main__":
    main()