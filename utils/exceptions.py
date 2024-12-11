class DownloadError(Exception):
    """Exceção para erros de download."""
    pass

class ConversionError(Exception):
    """Exceção para erros de conversão de arquivos."""
    pass

class CalculationError(Exception):
    """Exceção para erros durante os cálculos."""
    pass

class SettingsError(Exception):
    """Exceção para erros relacionados às configurações."""
    pass