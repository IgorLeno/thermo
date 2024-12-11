import yaml
from core.calculation import CalculationParameters
from dataclasses import asdict

class Settings:
    """
    Gerencia as configurações do programa.
    """
    def __init__(self):
        self.calculation_params = CalculationParameters()
        self.openbabel_path = "obabel"  # Caminho padrão, pode ser alterado
        self.crest_path = "crest"
        self.xtb_path = "xtb"

    def load_settings(self, filepath: str):
        """Carrega as configurações a partir de um arquivo YAML."""
        try:
            with open(filepath, "r") as f:
                config = yaml.safe_load(f)

            self.calculation_params = CalculationParameters(**config.get("calculation_parameters", {}))
            self.openbabel_path = config.get("openbabel_path", "obabel")
            self.crest_path = config.get("crest_path", "crest")
            self.xtb_path = config.get("xtb_path", "xtb")
        except FileNotFoundError:
            print(f"Arquivo de configuração não encontrado: {filepath}")
            print("Usando configurações padrão.")
        except Exception as e:
            print(f"Erro ao ler o arquivo de configuração: {e}")
            print("Usando configurações padrão.")

    def save_settings(self, filepath: str):
        """Salva as configurações em um arquivo YAML."""
        config = {
            "calculation_parameters": asdict(self.calculation_params),
            "openbabel_path": self.openbabel_path,
            "crest_path": self.crest_path,
            "xtb_path": self.xtb_path
        }
        try:
            with open(filepath, "w") as f:
                yaml.dump(config, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar o arquivo de configuração: {e}")