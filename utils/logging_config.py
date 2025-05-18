"""
Configuração centralizada do sistema de logging para o Grimme Thermo.
Este módulo configura diferentes níveis de log para diferentes componentes,
silenciando logs verbosos das bibliotecas externas.
"""
import logging
import os
from pathlib import Path
from datetime import datetime

class ConsoleFilter(logging.Filter):
    """
    Filtro personalizado para bloquear logs específicos no console.
    Permite controle granular sobre quais logs aparecem no console.
    """
    
    def __init__(self):
        super().__init__()
        # Padrões de logs para filtrar (bloquear no console)
        self.blocked_patterns = [
            # Padrões específicos do hpack (como visto nos logs originais)
            'Decoded',
            'Encoding', 
            'Adding',
            'encoded header block',
            'consumed',
            'bytes',
            
            # Padrões de trace do httpx/httpcore
            '*trace*',
            'trace.',
            'trace -',
            'receive_response_headers',
            'send_request_headers',
            'send_request_body', 
            'receive_response_body',
            'response_closed',
            'connection_pool',
            
            # Padrões de HTTP requests
            'HTTP Request:',
            'HTTP/1.1',
            'HTTP/2',
            
            # Padrões específicos que apareceram nos logs
            '*trace - send*request_headers.started',
            '*trace - send*request_body.started',
            '*trace - receive*response_headers.started',
            '*trace - receive*response_body.started',
            'return_value=',
            'stream_id='
        ]
        
        # Loggers específicos para bloquear completamente no console
        self.blocked_loggers = [
            'httpx._client',
            'httpcore._sync',
            'httpcore._async', 
            'httpcore.http11',
            'httpcore.http2',
            'hpack',
            'h2',
            'h11'
        ]
        
        # Padrões de nomes de logger para bloquear
        self.blocked_logger_patterns = [
            '*trace',
            '_client',
            '_sync.',
            '_async.'
        ]
    
    def filter(self, record):
        """
        Filtra logs baseado no logger name e mensagem.
        Retorna False para bloquear o log, True para permitir.
        """
        # Bloqueia loggers específicos por nome exato
        if record.name in self.blocked_loggers:
            return False
            
        # Bloqueia loggers que contêm padrões específicos
        for pattern in self.blocked_logger_patterns:
            if pattern in record.name:
                return False
        
        # Bloqueia logs de nível DEBUG de qualquer logger httpx/httpcore
        if record.levelno == logging.DEBUG:
            if any(prefix in record.name for prefix in ['httpx', 'httpcore', 'hpack', 'h2', 'h11']):
                return False
        
        # Bloqueia mensagens contendo padrões específicos
        if hasattr(record, 'getMessage'):
            try:
                message = record.getMessage()
                if any(pattern.lower() in message.lower() for pattern in self.blocked_patterns):
                    return False
            except:
                # Se houver erro ao obter a mensagem, permite o log
                pass
                
        # Permite outros logs
        return True

class LoggingManager:
    """Gerencia a configuração de logging para toda a aplicação."""
    
    def __init__(self):
        self.file_handler = None
        self.console_handler = None
        self.root_logger = logging.getLogger()
        self.console_filter = ConsoleFilter()
        
    def setup_logging(self, log_dir='logs', console_level=logging.INFO, file_level=logging.DEBUG):
        """
        Configura o sistema de logging com handlers separados para arquivo e console.
        
        Args:
            log_dir: Diretório para salvar os arquivos de log
            console_level: Nível de log para o console (padrão: INFO)
            file_level: Nível de log para arquivo (padrão: DEBUG)
        """
        # Cria diretório de logs se não existir
        os.makedirs(log_dir, exist_ok=True)
        
        # Nome do arquivo de log com timestamp
        log_filename = f'{log_dir}/conformer_search_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        
        # Remove handlers existentes para evitar duplicação
        self.root_logger.handlers.clear()
        
        # Configurar handler para arquivo (logs detalhados)
        self.file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        self.file_handler.setLevel(file_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        self.file_handler.setFormatter(file_formatter)
        
        # Configurar handler para console (logs essenciais com filtro)
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(console_level)
        self.console_handler.addFilter(self.console_filter)  # Adiciona o filtro personalizado
        console_formatter = logging.Formatter(
            '%(levelname)s - %(name)s - %(message)s'
        )
        self.console_handler.setFormatter(console_formatter)
        
        # Configurar o logger root
        self.root_logger.setLevel(logging.DEBUG)
        self.root_logger.addHandler(self.file_handler)
        self.root_logger.addHandler(self.console_handler)
        
        # Configurar loggers específicos para suprimir logs verbosos
        self._configure_external_loggers()
        
        logging.info(f"Sistema de logging configurado. Arquivo: {log_filename}")
        
    def _configure_external_loggers(self):
        """Configura os loggers de bibliotecas externas para reduzir verbosidade."""
        
        # Bibliotecas HTTP/HTTPX - extremamente verbosas
        external_loggers = [
            'httpx',
            'httpcore', 
            'httpcore._sync',
            'httpcore._async',
            'httpcore.http11',
            'httpcore.http2',
            'hpack',
            'h2',
            'h11',
            'urllib3',
            'urllib3.connectionpool',
            'requests',
            'requests.packages.urllib3',
            'supabase._client',
            'supabase.storage',
            'gotrue',
            'postgrest'
        ]
        
        # Configura nível WARNING para estes loggers
        for logger_name in external_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.WARNING)
            logger.propagate = True
        
        # Loggers específicos do trace do httpx - extremamente verbosos
        trace_loggers = [
            'httpx._client',
            'httpcore._sync.http11',
            'httpcore._sync.http2', 
            'httpcore._sync.connection_pool',
            'httpcore._async.http11',
            'httpcore._async.http2',
            'httpcore._async.connection_pool',
            # Adicionais específicos do httpx que foram observados
            'httpcore._sync.http_proxy',
            'httpcore._async.http_proxy',
            'httpcore.backends._sync',
            'httpcore.backends._async'
        ]
        
        for logger_name in trace_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.ERROR)  # Apenas erros críticos
            logger.propagate = True
        
        # Silenciar completamente qualquer logger com '*trace' no nome
        # Isso é feito de forma dinâmica para capturar loggers criados em runtime
        def filter_trace_loggers():
            for logger_dict_name in list(logging.Logger.manager.loggerDict.keys()):
                if any(pattern in logger_dict_name.lower() for pattern in ['trace', '*trace', '_trace']):
                    logger = logging.getLogger(logger_dict_name)
                    logger.setLevel(logging.CRITICAL)
                    logger.propagate = False
        
        # Aplica o filtro imediatamente e programa para aplicar novamente
        filter_trace_loggers()
        
        # Impede que httpx configure seu próprio logging de trace
        try:
            import httpx
            # Desabilita os logs de trace do httpx
            if hasattr(httpx, '_client'):
                httpx_client_logger = logging.getLogger('httpx._client')
                httpx_client_logger.disabled = False  # Permite WARNING e ERROR
                httpx_client_logger.setLevel(logging.WARNING)
        except ImportError:
            pass
            
        # Configura todos os loggers que começam com determinados prefixos
        prefixes_to_limit = ['httpx', 'httpcore', 'hpack', 'h2', 'h11']
        for logger_name in list(logging.Logger.manager.loggerDict.keys()):
            for prefix in prefixes_to_limit:
                if logger_name.startswith(prefix):
                    logger = logging.getLogger(logger_name)
                    if logger.level < logging.WARNING:
                        logger.setLevel(logging.WARNING)
                
    def set_module_log_level(self, module_name, level):
        """
        Define o nível de log para um módulo específico.
        
        Args:
            module_name: Nome do módulo (ex: 'services.supabase_service')
            level: Nível de log (ex: logging.WARNING)
        """
        logger = logging.getLogger(module_name)
        logger.setLevel(level)
        
    def suppress_console_logs_from(self, logger_names):
        """
        Suprime logs no console para os loggers especificados,
        mantendo apenas os logs em arquivo.
        
        Args:
            logger_names: Lista de nomes de loggers para suprimir no console
        """
        for logger_name in logger_names:
            logger = logging.getLogger(logger_name)
            
            # Remove o handler do console apenas deste logger
            if self.console_handler in logger.handlers:
                logger.removeHandler(self.console_handler)
            
            # Adiciona apenas o handler de arquivo
            if self.file_handler not in logger.handlers:
                logger.addHandler(self.file_handler)
            
            # Evita que o log seja propagado para o root logger
            logger.propagate = False
            
    def get_log_filename(self):
        """Retorna o nome do arquivo de log atual."""
        if self.file_handler:
            return self.file_handler.baseFilename
        return None
        
    def add_blocked_pattern(self, pattern):
        """Adiciona um padrão para ser bloqueado no console."""
        self.console_filter.blocked_patterns.append(pattern)
        
    def add_blocked_logger(self, logger_name):
        """Adiciona um logger para ser bloqueado no console."""
        self.console_filter.blocked_loggers.append(logger_name)

# Instância global para facilitar o uso
_logging_manager = LoggingManager()

def setup_application_logging():
    """Função de conveniência para configurar o logging da aplicação."""
    _logging_manager.setup_logging()
    
def get_logging_manager():
    """Retorna a instância do gerenciador de logging."""
    return _logging_manager

def silence_external_libraries():
    """Silencia bibliotecas externas especialmente verbosas no console."""
    external_loggers = [
        'httpx',
        'httpcore', 
        'hpack',
        'h2',
        'h11',
        'urllib3',
        'supabase'
    ]
    _logging_manager.suppress_console_logs_from(external_loggers)
