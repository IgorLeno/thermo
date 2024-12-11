# services/pubchem_service.py
import requests
import os
from services.file_service import FileService
from config.constants import SDF_DIR
from core.molecule import Molecule
from typing import Optional
import logging

class PubChemService:
    """
    Classe para interagir com o PubChem.
    """
    def __init__(self):
        self.base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        self.file_service = FileService()

    def get_sdf_by_name(self, molecule_name: str) -> tuple[Optional[str], Optional[int]]:
        """
        Busca o arquivo SDF de uma molécula no PubChem pelo nome.

        Retorna:
            Uma tupla contendo o caminho do arquivo SDF baixado e o CID da molécula,
            ou (None, None) se a molécula não for encontrada ou se ocorrer um erro.
        """
        # Normaliza o nome do arquivo para evitar problemas com caracteres especiais
        safe_filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in molecule_name) + ".sdf"
        sdf_path = SDF_DIR / safe_filename

        try:
            # Primeiro, busca o CID pelo nome
            cid_url = f"{self.base_url}/compound/name/{molecule_name}/cids/TXT"
            cid_response = requests.get(cid_url)
            cid_response.raise_for_status()  # Lança um erro para códigos de status HTTP 4xx ou 5xx

            cid = int(cid_response.text.strip())

            # Em seguida, busca o SDF pelo CID
            sdf_url = f"{self.base_url}/compound/cid/{cid}/record/SDF/?record_type=3d&response_type=save"
            sdf_response = requests.get(sdf_url)
            sdf_response.raise_for_status()

            # Salva o arquivo SDF
            self.file_service.create_directory(SDF_DIR)  # Certifica-se de que o diretório existe
            with open(sdf_path, "w") as f:
                f.write(sdf_response.text)

            logging.info(f"Arquivo SDF baixado para {molecule_name} (CID: {cid}) em {sdf_path}")
            return str(sdf_path), cid

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logging.warning(f"Molécula '{molecule_name}' não encontrada no PubChem.")
                print(f"Molécula '{molecule_name}' não encontrada no PubChem.")
            else:
                logging.error(f"Erro ao acessar o PubChem: {e}")
                print(f"Erro ao acessar o PubChem. Veja o log para mais detalhes.")
            return None, None
        except Exception as e:
            logging.error(f"Erro ao obter SDF para {molecule_name}: {e}")
            print(f"Erro ao obter SDF para {molecule_name}. Veja o log para mais detalhes.")
            return None, None