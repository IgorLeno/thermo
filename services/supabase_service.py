"""
Serviço para comunicação com o Supabase.
Gerencia o upload de dados de moléculas, cálculos e resultados.
"""
import os
import json
from pathlib import Path
import logging
from supabase import create_client, Client
from typing import Dict, Any, Optional, List, Union
from core.molecule import Molecule

class SupabaseService:
    """Serviço para gerenciar a comunicação com o Supabase."""
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Inicializa o serviço do Supabase.
        
        Args:
            url: URL da API do Supabase (opcional, pode ser definida via variável de ambiente)
            key: Chave da API do Supabase (opcional, pode ser definida via variável de ambiente)
        """
        # Tenta obter as credenciais das variáveis de ambiente ou do argumento
        self.url = url or os.environ.get("SUPABASE_URL")
        self.key = key or os.environ.get("SUPABASE_KEY")
        
        if not self.url or not self.key:
            logging.warning("Credenciais do Supabase não configuradas. A integração com o dashboard estará desativada.")
            self.enabled = False
            return
            
        try:
            self.supabase: Client = create_client(self.url, self.key)
            self.enabled = True
            logging.info("Conexão com o Supabase estabelecida com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao conectar com o Supabase: {e}")
            self.enabled = False
    
    def ensure_bucket_exists(self, bucket_name: str) -> bool:
        """
        Verifica se o bucket existe e cria-o se não existir.
        
        Args:
            bucket_name: Nome do bucket a ser verificado/criado
            
        Returns:
            True se o bucket existe ou foi criado com sucesso, False caso contrário
        """
        if not self.enabled:
            logging.warning("Serviço Supabase desativado. Não é possível verificar ou criar bucket.")
            return False
            
        try:
            # Verifica se o bucket existe
            try:
                self.supabase.storage.get_bucket(bucket_name)
                logging.info(f"Bucket '{bucket_name}' já existe.")
                return True
            except Exception as e:
                if "Bucket not found" in str(e):
                    logging.info(f"Bucket '{bucket_name}' não existe. Tentando criar...")
                    # Cria o bucket
                    try:
                        self.supabase.storage.create_bucket(bucket_name, options={
                            'public': True  # Define o bucket como público para facilitar o acesso
                        })
                        logging.info(f"Bucket '{bucket_name}' criado com sucesso.")
                        return True
                    except Exception as create_error:
                        logging.error(f"Erro ao criar bucket '{bucket_name}': {create_error}")
                        return False
                else:
                    logging.error(f"Erro ao verificar bucket '{bucket_name}': {e}")
                    return False
        except Exception as e:
            logging.error(f"Erro ao gerenciar bucket '{bucket_name}': {e}")
            return False
    
    def upload_molecule(self, molecule: Molecule) -> Optional[str]:
        """
        Envia dados da molécula para o Supabase.
        
        Args:
            molecule: Objeto Molecule com os dados da molécula
            
        Returns:
            ID da molécula no Supabase ou None em caso de erro
        """
        if not self.enabled:
            logging.warning("Serviço Supabase desativado. Não é possível fazer upload da molécula.")
            return None
        
        try:
            # Verifica se a molécula já existe
            response = self.supabase.table("molecules") \
                .select("id") \
                .eq("name", molecule.name) \
                .execute()
                
            if response.data:
                # Molécula já existe, retorna o ID existente
                molecule_id = response.data[0]["id"]
                logging.info(f"Molécula '{molecule.name}' já existe no Supabase com ID: {molecule_id}")
                return molecule_id
            
            # Prepara os dados da molécula
            molecule_data = {
                "name": molecule.name,
                "pubchem_cid": molecule.pubchem_cid,
                # Adicione outros campos disponíveis
            }
            
            # Insere a molécula no Supabase
            response = self.supabase.table("molecules").insert(molecule_data).execute()
            
            if not response.data:
                logging.error(f"Erro ao inserir molécula '{molecule.name}' no Supabase: Sem dados de retorno")
                return None
                
            molecule_id = response.data[0]["id"]
            logging.info(f"Molécula '{molecule.name}' inserida no Supabase com ID: {molecule_id}")
            return molecule_id
            
        except Exception as e:
            logging.error(f"Erro ao fazer upload da molécula '{molecule.name}' para o Supabase: {e}")
            return None
    
    def upload_calculation_results(self, 
                                  molecule_id: str, 
                                  calculation_type: str, 
                                  status: str, 
                                  parameters: Dict[str, Any], 
                                  results: Dict[str, Any]) -> bool:
        """
        Envia resultados de cálculo para o Supabase.
        
        Args:
            molecule_id: ID da molécula no Supabase
            calculation_type: Tipo de cálculo ('crest' ou 'mopac')
            status: Status do cálculo ('completed', 'failed', etc.)
            parameters: Parâmetros utilizados no cálculo
            results: Resultados do cálculo
            
        Returns:
            True se o upload foi bem-sucedido, False caso contrário
        """
        if not self.enabled:
            logging.warning("Serviço Supabase desativado. Não é possível fazer upload dos resultados.")
            return False
            
        if not molecule_id:
            logging.error("ID da molécula é obrigatório para o upload de resultados.")
            return False
            
        try:
            # Criar registro de cálculo
            calc_data = {
                "molecule_id": molecule_id,
                "calculation_type": calculation_type,
                "status": status,
                "parameters": parameters
            }
            
            # Insere o cálculo no Supabase
            calc_response = self.supabase.table("calculations").insert(calc_data).execute()
            
            if not calc_response.data:
                logging.error(f"Erro ao inserir cálculo para molécula {molecule_id}: Sem dados de retorno")
                return False
            
            calculation_id = calc_response.data[0]["id"]
            logging.info(f"Cálculo {calculation_type} inserido com ID: {calculation_id}")
            
            # Inserir resultados específicos com base no tipo de cálculo
            if calculation_type == "crest":
                # Converte listas para JSON se necessário
                for key in ["energy_distribution", "relative_energies", "populations"]:
                    if key in results and not isinstance(results[key], str):
                        results[key] = json.dumps(results[key])
                
                crest_data = {
                    "calculation_id": calculation_id,
                    "num_conformers": results.get("num_conformers"),
                    "best_conformer_path": results.get("best_conformer_path"),
                    "all_conformers_path": results.get("all_conformers_path"),
                    "energy_distribution": results.get("energy_distribution"),
                    "relative_energies": results.get("relative_energies"),
                    "populations": results.get("populations")
                }
                
                self.supabase.table("crest_results").insert(crest_data).execute()
                logging.info(f"Resultados CREST inseridos para cálculo {calculation_id}")
            
            elif calculation_type == "mopac":
                mopac_data = {
                    "calculation_id": calculation_id,
                    "enthalpy_formation": results.get("enthalpy_formation"),
                    "method": results.get("method"),
                    "output_path": results.get("output_path")
                }
                
                self.supabase.table("mopac_results").insert(mopac_data).execute()
                logging.info(f"Resultados MOPAC inseridos para cálculo {calculation_id}")
            
            return True
            
        except Exception as e:
            logging.error(f"Erro ao fazer upload dos resultados para o Supabase: {e}")
            return False
    
    def upload_file(self, file_path: Union[str, Path], bucket_name: str, file_name: Optional[str] = None) -> Optional[str]:
        """
        Faz upload de um arquivo para o storage do Supabase.
        
        Args:
            file_path: Caminho do arquivo a ser enviado
            bucket_name: Nome do bucket no Supabase Storage
            file_name: Nome do arquivo no bucket (opcional, usa o nome original se não especificado)
            
        Returns:
            URL pública do arquivo ou None em caso de erro
        """
        if not self.enabled:
            logging.warning("Serviço Supabase desativado. Não é possível fazer upload do arquivo.")
            return None
        
        # Verifica e cria o bucket se necessário
        if not self.ensure_bucket_exists(bucket_name):
            logging.error(f"Não foi possível garantir a existência do bucket '{bucket_name}'. Upload cancelado.")
            return None
            
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logging.error(f"Arquivo não encontrado: {file_path}")
                return None
                
            file_name = file_name or file_path.name
            
            # Lê o conteúdo do arquivo
            with open(file_path, 'rb') as f:
                file_contents = f.read()
            
            # Faz upload do arquivo
            result = self.supabase.storage.from_(bucket_name).upload(
                path=file_name,
                file=file_contents,
                file_options={"content-type": "application/octet-stream"},
                file_options_override=True  # Sobrescreve se o arquivo já existir
            )
            
            # Obtém a URL pública
            if result.get('Key'):
                public_url = self.supabase.storage.from_(bucket_name).get_public_url(file_name)
                logging.info(f"Arquivo {file_path} enviado para o Supabase Storage: {public_url}")
                return public_url
                
            logging.error(f"Erro ao fazer upload do arquivo {file_path}: {result}")
            return None
            
        except Exception as e:
            logging.error(f"Erro ao fazer upload do arquivo {file_path} para o Supabase: {e}")
            return None
    
    def get_molecule_results(self, molecule_name: str) -> Dict[str, Any]:
        """
        Obtém todos os resultados para uma molécula específica.
        
        Args:
            molecule_name: Nome da molécula
            
        Returns:
            Dicionário com os dados da molécula e seus resultados
        """
        if not self.enabled:
            logging.warning("Serviço Supabase desativado. Não é possível obter resultados.")
            return {}
            
        try:
            # Busca a molécula
            molecule_response = self.supabase.table("molecules") \
                .select("*") \
                .eq("name", molecule_name) \
                .execute()
                
            if not molecule_response.data:
                logging.warning(f"Molécula '{molecule_name}' não encontrada no Supabase.")
                return {}
                
            molecule_data = molecule_response.data[0]
            molecule_id = molecule_data["id"]
            
            # Busca os cálculos
            calculations_response = self.supabase.table("calculations") \
                .select("*") \
                .eq("molecule_id", molecule_id) \
                .execute()
                
            calculations = calculations_response.data
            
            # Para cada cálculo, busca os resultados específicos
            results = []
            for calc in calculations:
                calc_id = calc["id"]
                calc_type = calc["calculation_type"]
                
                if calc_type == "crest":
                    crest_response = self.supabase.table("crest_results") \
                        .select("*") \
                        .eq("calculation_id", calc_id) \
                        .execute()
                        
                    if crest_response.data:
                        calc["crest_results"] = crest_response.data[0]
                        
                elif calc_type == "mopac":
                    mopac_response = self.supabase.table("mopac_results") \
                        .select("*") \
                        .eq("calculation_id", calc_id) \
                        .execute()
                        
                    if mopac_response.data:
                        calc["mopac_results"] = mopac_response.data[0]
                
                results.append(calc)
            
            return {
                "molecule": molecule_data,
                "calculations": results
            }
            
        except Exception as e:
            logging.error(f"Erro ao obter resultados da molécula '{molecule_name}' do Supabase: {e}")
            return {}
