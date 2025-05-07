# services/conversion_service.py
import subprocess
import os
from pathlib import Path
from config.settings import Settings
from core.molecule import Molecule
from config.constants import XYZ_DIR, PDB_DIR
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
            
    def convert_file(self, input_file_path: Path, output_file_path: Path, input_format: str, output_format: str) -> bool:
        """
        Converte um arquivo de um formato para outro usando o OpenBabel.
        
        Args:
            input_file_path: Caminho para o arquivo de entrada.
            output_file_path: Caminho para o arquivo de saída.
            input_format: Formato do arquivo de entrada (ex: 'xyz', 'sdf').
            output_format: Formato do arquivo de saída (ex: 'pdb', 'mol2').
            
        Returns:
            bool: True se a conversão foi bem-sucedida, False caso contrário.
        """
        try:
            # Cria o diretório de saída se não existir
            os.makedirs(output_file_path.parent, exist_ok=True)
            
            command = [
                self.settings.openbabel_path,
                f"-i{input_format}", str(input_file_path),
                f"-o{output_format}",
                f"-O{str(output_file_path)}",
                "-h"  # Adicionar hidrogênios
            ]
            
            process = subprocess.run(command, capture_output=True, text=True, check=True)
            logging.info(f"Arquivo {input_file_path} convertido para {output_file_path} com sucesso.")
            
            if process.stderr and not os.path.exists(output_file_path):
                logging.warning(f"Mensagens do OpenBabel: {process.stderr}")
                return False
                
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Erro ao converter {input_file_path} para {output_file_path}: {e}")
            logging.error(f"Saída de erro do OpenBabel: {e.stderr}")
            return False
        except FileNotFoundError:
            logging.error(f"OpenBabel não encontrado. Verifique a instalação e a configuração do caminho: {self.openbabel_path}")
            return False
        except Exception as e:
            logging.error(f"Erro inesperado durante a conversão: {e}")
            return False