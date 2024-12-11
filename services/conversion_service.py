# services/conversion_service.py
import subprocess
from config.settings import Settings
from core.molecule import Molecule
from config.constants import XYZ_DIR
import logging

class ConversionService:
    """
    Classe para lidar com a conversão de formatos de arquivo usando o OpenBabel.
    """
    def __init__(self, settings: Settings):
        self.settings = settings
        self.openbabel_path = settings.openbabel_path

    def sdf_to_xyz(self, molecule: Molecule):
        """
        Converte um arquivo SDF para XYZ usando o OpenBabel.
        """
        if not molecule.sdf_path:
            raise ValueError("Caminho do arquivo SDF não definido.")
        if not molecule.name:
            raise ValueError("Nome da molécula não definido.")

        sdf_path = molecule.sdf_path
        xyz_path = str(XYZ_DIR / f"{molecule.name}.xyz")
        molecule.xyz_path = xyz_path

        command = [
            self.settings.openbabel_path,  # Caminho do OpenBabel
            "-isdf", sdf_path,
            "-oxyz",
            "-O" + xyz_path,  # Usar -O para especificar o arquivo de saída
            "-h"  # Adicionar hidrogênios
        ]

        try:
            process = subprocess.run(command, capture_output=True, text=True, check=True)
            logging.info(f"Arquivo {sdf_path} convertido para {xyz_path} com sucesso.")
            if process.stderr:
                logging.warning(f"Mensagens do OpenBabel para {molecule.name}: {process.stderr}")

        except subprocess.CalledProcessError as e:
            logging.error(f"Erro ao converter {sdf_path} para {xyz_path}: {e}")
            logging.error(f"Saída de erro do OpenBabel: {e.stderr}")
            raise RuntimeError(f"Falha na conversão de SDF para XYZ para a molécula {molecule.name}.") from e
        except FileNotFoundError:
            logging.error(f"OpenBabel não encontrado. Verifique a instalação e a configuração do caminho: {self.openbabel_path}")
            raise