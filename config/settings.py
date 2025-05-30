import yaml
from core.calculation import CalculationParameters
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Dict, Any

@dataclass
class SupabaseConfig:
    """Configuração para o Supabase."""
    enabled: bool = False
    url: str = ""
    key: str = ""
    storage_enabled: bool = False
    molecules_bucket: str = "molecules"

class Paths:
    """
    Classe para armazenar os caminhos dos diretórios do projeto.
    """
    def __init__(self):
        self.repository_dir = Path("repository")
        self.repository_sdf_dir = self.repository_dir / "sdf"
        self.repository_xyz_dir = self.repository_dir / "xyz"
        self.repository_crest_dir = self.repository_dir / "crest"
        self.repository_pdb_dir = self.repository_dir / "pdb"
        self.repository_mopac_dir = self.repository_dir / "mopac"
        self.final_molecules_dir = Path("final_molecules")

class Settings:
    """
    Gerencia as configurações do programa.
    """
    def __init__(self):
        self.calculation_params = CalculationParameters()
        self.openbabel_path = "obabel"  # Caminho padrão, pode ser alterado
        self.crest_path = "crest"
        self.mopac_executable_path: Optional[Path] = None
        self.mopac_keywords: str = "PM7 EF PRECISE GNORM=0.01 NOINTER GRAPHF VECTORS MMOK CYCLES=20000"  # Default
        self.paths = Paths()
        self.supabase = SupabaseConfig()

    def load_settings(self, filepath: str):
        """Carrega as configurações a partir de um arquivo YAML."""
        try:
            with open(filepath, "r") as f:
                config = yaml.safe_load(f)

            self.calculation_params = CalculationParameters(**config.get("calculation_parameters", {}))
            
            # Programas
            programs_config = config.get("programs", {})
            self.openbabel_path = programs_config.get("openbabel_path", "obabel")
            self.crest_path = programs_config.get("crest_path", "crest")
            self.mopac_executable_path = Path(programs_config.get("mopac_path", "MOPAC2016.exe"))
            
            # Parâmetros do MOPAC
            mopac_config = config.get("mopac_params", {})
            self.mopac_keywords = mopac_config.get("keywords", self.mopac_keywords)
            
            # Configurações do Supabase
            supabase_config = config.get("supabase", {})
            self.supabase.enabled = supabase_config.get("enabled", False)
            self.supabase.url = supabase_config.get("url", "")
            self.supabase.key = supabase_config.get("key", "")
            
            # Configurações do Storage do Supabase
            storage_config = supabase_config.get("storage", {})
            if isinstance(storage_config, dict):
                self.supabase.storage_enabled = storage_config.get("enabled", False)
                self.supabase.molecules_bucket = storage_config.get("molecules_bucket", "molecules")
            
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
            "programs": {
                "openbabel_path": self.openbabel_path,
                "crest_path": self.crest_path,
                "mopac_path": str(self.mopac_executable_path) if self.mopac_executable_path else "MOPAC2016.exe"
            },
            "mopac_params": {
                "keywords": self.mopac_keywords
            },
            "supabase": {
                "enabled": self.supabase.enabled,
                "url": self.supabase.url,
                "key": self.supabase.key,
                "storage": {
                    "enabled": self.supabase.storage_enabled,
                    "molecules_bucket": self.supabase.molecules_bucket
                }
            }
        }
        try:
            with open(filepath, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
        except Exception as e:
            print(f"Erro ao salvar o arquivo de configuração: {e}")
