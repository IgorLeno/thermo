# main.py
from interfaces.cli import CommandLineInterface
from config.settings import Settings
from services.file_service import FileService
from services.pubchem_service import PubChemService
from services.conversion_service import ConversionService
from services.calculation_service import CalculationService
import logging
import os
from datetime import datetime

def main():
    """
    Função principal do programa conformer_search.
    """
    # Cria diretório de logs se não existir
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Nome do arquivo de log com timestamp
    log_filename = f'logs/conformer_search_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    # Configuração do logging com nível mais detalhado e exibindo no console também
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()  # Adiciona saída para o console
        ]
    )

    logging.info("=== Iniciando o programa de busca conformacional ===")
    logging.info(f"Log sendo salvo em: {log_filename}")

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