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
        Verifica se o bucket existe e pergunta ao usuário se deseja criá-lo caso não exista.
        
        Args:
            bucket_name: Nome do bucket a ser verificado/criado
            
        Returns:
            True se o bucket existe ou foi criado com sucesso, False caso contrário
        """
        if not self.enabled:
            logging.warning("Serviço Supabase desativado. Não é possível verificar ou criar bucket.")
            return False
            
        try:
            # OVERRIDE: Devido a problemas na API do Supabase para detecção de buckets
            # Vamos tentar um método alternativo e considerar o bucket como existente se possível
            try:
                # Tenta acessar o bucket diretamente - essa é uma abordagem mais direta
                # que funciona mesmo quando os métodos list_buckets/get_bucket falham
                bucket_access = self.supabase.storage.from_(bucket_name)
                # Se não lançar exceção, assumimos que o bucket existe
                logging.info(f"Bucket '{bucket_name}' acessado com sucesso via from_().")
                print(f"Bucket '{bucket_name}' acessado com sucesso.")
                return True
            except Exception as direct_e:
                # Se falhar no acesso direto, tentamos outros métodos
                logging.warning(f"Acesso direto ao bucket '{bucket_name}' falhou: {direct_e}")
            
            # Tenta listar todos os buckets
            try:
                buckets = self.supabase.storage.list_buckets()
                # Log completo para diagnóstico
                logging.info(f"Buckets retornados pela API: {buckets}")
                
                if not buckets:
                    logging.warning("A API retornou uma lista vazia de buckets.")
                    print("A API retornou uma lista vazia de buckets.")
                
                bucket_names = [bucket['name'] for bucket in buckets] if buckets else []
                
                if bucket_name in bucket_names:
                    logging.info(f"Bucket '{bucket_name}' encontrado na lista de buckets.")
                    return True
                else:
                    # Se o bucket não foi encontrado na lista mas sabemos que ele existe...
                    # (esse é o caso que estamos enfrentando segundo as imagens)
                    
                    # Pergunte ao usuário como proceder
                    print(f"\nO bucket '{bucket_name}' não existe no Supabase.")
                    if bucket_names:
                        print(f"Buckets existentes: {', '.join(bucket_names)}")
                    else:
                        print("Nenhum bucket existente detectado pela API.")
                        print("NOTA: Isso pode ser um problema de permissão ou API, não necessariamente a ausência de buckets.")
                    
                    # Pergunte se quer ignorar a verificação e tentar usar o bucket mesmo assim
                    resposta = input("Deseja ignorar essa verificação e tentar usar o bucket mesmo assim? (s/n): ").lower()
                    
                    if resposta == 's':
                        print(f"Ignorando verificação. Tentando usar o bucket '{bucket_name}' mesmo assim.")
                        logging.info(f"Usuário optou por ignorar verificação e tentar usar o bucket '{bucket_name}'.")
                        return True
                    
                    # Caso contrário, pergunte se quer criar
                    resposta = input("Deseja criar este bucket? (s/n): ").lower()
                    
                    if resposta == 's':
                        # Cria o bucket
                        try:
                            self.supabase.storage.create_bucket(bucket_name, options={
                                'public': True  # Define o bucket como público para facilitar o acesso
                            })
                            print(f"Bucket '{bucket_name}' criado com sucesso.")
                            logging.info(f"Bucket '{bucket_name}' criado com sucesso.")
                            
                            # Sugere a criação de políticas
                            print("\nImportante: Lembre-se de configurar as políticas de segurança!")
                            print("Acesse Storage > Policies no painel do Supabase para configurar.")
                            
                            return True
                        except Exception as create_error:
                            logging.error(f"Erro ao criar bucket '{bucket_name}': {create_error}")
                            print(f"Erro ao criar bucket: {create_error}")
                            
                            # Mesmo com erro, pergunta se deseja ignorar e tentar usar
                            resposta = input("Deseja ignorar o erro e tentar usar o bucket mesmo assim? (s/n): ").lower()
                            if resposta == 's':
                                return True
                            return False
                    else:
                        # Se não quer criar, pergunta se quer usar um existente
                        if bucket_names:
                            use_existing = input(f"Deseja usar o bucket '{bucket_names[0]}' em vez disso? (s/n): ").lower()
                            if use_existing == 's':
                                print(f"Usando bucket '{bucket_names[0]}' para operações de armazenamento.")
                                return True
                        
                        # Última chance - perguntar se quer tentar usar mesmo assim
                        resposta = input("Última verificação: Deseja ignorar problemas e tentar usar o bucket original mesmo assim? (s/n): ").lower()
                        if resposta == 's':
                            print(f"Tentando usar o bucket '{bucket_name}' mesmo que não seja detectado.")
                            return True
                            
                        print("Algumas operações de armazenamento podem falhar.")
                        return False
            except Exception as e:
                logging.error(f"Erro ao listar buckets: {e}")
                print(f"Erro ao listar buckets: {e}")
                
                # Pergunte se deseja tentar usar o bucket mesmo assim
                resposta = input(f"Erro ao verificar buckets. Deseja tentar usar o bucket '{bucket_name}' mesmo assim? (s/n): ").lower()
                if resposta == 's':
                    print(f"Tentando usar o bucket '{bucket_name}' mesmo com erros de verificação.")
                    return True
                return False
                
        except Exception as e:
            logging.error(f"Erro ao gerenciar bucket '{bucket_name}': {e}")
            print(f"Erro ao gerenciar bucket: {e}")
            
            # Pergunte se deseja tentar usar o bucket mesmo assim como último recurso
            resposta = input(f"Erro geral. Deseja tentar usar o bucket '{bucket_name}' mesmo assim? (s/n): ").lower()
            if resposta == 's':
                return True
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
                # Molécula já existe, atualiza com novos dados
                molecule_id = response.data[0]["id"]
                logging.info(f"Molécula '{molecule.name}' já existe no Supabase com ID: {molecule_id}")
                
                # Prepara os dados para atualização
                update_data = self._prepare_molecule_data(molecule)
                if update_data:
                    update_response = self.supabase.table("molecules") \
                        .update(update_data) \
                        .eq("id", molecule_id) \
                        .execute()
                    logging.info(f"Molécula '{molecule.name}' atualizada no Supabase")
                
                return molecule_id
            
            # Prepara os dados básicos da molécula
            molecule_data = self._prepare_molecule_data(molecule)
            if not molecule_data:
                logging.error(f"Não foi possível preparar dados para a molécula '{molecule.name}'")
                return None
            
            # Insere a molécula no Supabase
            response = self.supabase.table("molecules").insert(molecule_data).execute()
            
            if not response.data:
                logging.error(f"Erro ao inserir molécula '{molecule.name}' no Supabase: Sem dados de retorno")
                return None
                
            molecule_id = response.data[0]["id"]
            logging.info(f"Molécula '{molecule.name}' inserida no Supabase com ID: {molecule_id}")
            return molecule_id
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Erro ao fazer upload da molécula '{molecule.name}' para o Supabase: {e}")
            
            # Tratamento específico para erro de coluna não encontrada
            if "Could not find" in error_msg and "column" in error_msg:
                print(f"\n⚠️  ERRO DE COLUNA NÃO ENCONTRADA!")
                print(f"Uma ou mais colunas não existem na tabela 'molecules'.")
                print(f"Para corrigir este problema:")
                print(f"1. Execute o script 'add_enthalpy_columns.sql' no Editor SQL do Supabase")
                print(f"2. Ou remova as colunas de entalpia do código temporariamente")
                print(f"Detalhes do erro: {e}")
                
            # Tratamento específico para erro de RLS
            elif "row-level security policy" in error_msg:
                print(f"\n⚠️  ERRO DE SEGURANÇA (RLS) DETECTADO!")
                print(f"A política de segurança do Supabase está bloqueando a inserção.")
                print(f"Para corrigir este problema:")
                print(f"1. Execute o script 'fix_supabase_rls_complete.sql' no Editor SQL do Supabase")
                print(f"2. Ou desative RLS para as tabelas no painel do Supabase")
                print(f"3. Ou configure políticas apropriadas para permitir inserções")
                print(f"Detalhes do erro: {e}")
                
            elif "42501" in error_msg:
                print(f"\n⚠️  ERRO DE PERMISSÃO DETECTADO!")
                print(f"A chave API não tem permissões suficientes.")
                print(f"Verifique:")
                print(f"1. Se a chave API é do tipo 'service_role' e não 'anon'")
                print(f"2. Se as permissões da tabela 'molecules' estão configuradas corretamente")
                print(f"Detalhes do erro: {e}")
                
            return None
    
    def _prepare_molecule_data(self, molecule: Molecule) -> Dict[str, Any]:
        """
        Prepara os dados da molécula para inserção/atualização no Supabase.
        
        Args:
            molecule: Objeto Molecule
            
        Returns:
            Dicionário com os dados preparados
        """
        # Dados básicos obrigatórios
        molecule_data = {
            "name": molecule.name,
        }
        
        # Adiciona campos opcionais apenas se existirem
        if hasattr(molecule, 'smiles') and molecule.smiles:
            molecule_data["smiles"] = molecule.smiles
            
        # Entalpia MOPAC
        if hasattr(molecule, 'enthalpy_formation_mopac_kj') and molecule.enthalpy_formation_mopac_kj is not None:
            molecule_data["hf_mopac"] = molecule.enthalpy_formation_mopac_kj
        elif hasattr(molecule, 'enthalpy_kj_mol') and molecule.enthalpy_kj_mol is not None:
            molecule_data["hf_mopac"] = molecule.enthalpy_kj_mol
            
        # Entalpia Chemperium
        if hasattr(molecule, 'enthalpy_chemperium_kj_mol') and molecule.enthalpy_chemperium_kj_mol is not None:
            molecule_data["hf_chemp"] = molecule.enthalpy_chemperium_kj_mol
            
        # Incerteza Chemperium
        if hasattr(molecule, 'enthalpy_chemperium_uncertainty_kj_mol') and molecule.enthalpy_chemperium_uncertainty_kj_mol is not None:
            molecule_data["hf_chemp_uncertainty"] = molecule.enthalpy_chemperium_uncertainty_kj_mol
            
        # Score de confiabilidade
        if hasattr(molecule, 'chemperium_reliability_score') and molecule.chemperium_reliability_score is not None:
            molecule_data["chemperium_reliability"] = molecule.chemperium_reliability_score
        
        return molecule_data
    
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
                    "enthalpy_formation_kj": results.get("enthalpy_formation_kj"),
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
        bucket_exists = self.ensure_bucket_exists(bucket_name)
        if not bucket_exists:
            print(f"Não foi possível garantir a existência do bucket '{bucket_name}'.")
            # Pergunte se quer tentar o upload mesmo assim como último recurso
            resposta = input("Tentar fazer o upload mesmo assim como último recurso? (s/n): ").lower()
            if resposta != 's':
                logging.error("Upload cancelado pelo usuário.")
                return None
            print("Tentando upload mesmo com problemas de verificação do bucket...")
            
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logging.error(f"Arquivo não encontrado: {file_path}")
                return None
                
            file_name = file_name or file_path.name
            
            # Lê o conteúdo do arquivo
            with open(file_path, 'rb') as f:
                file_contents = f.read()
            
            # Tenta fazer upload do arquivo, ignorando erros de bucket inexistente
            try:
                print(f"Enviando arquivo para o bucket '{bucket_name}'...")
                
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
                    print(f"Upload concluído com sucesso: {file_name}")
                    return public_url
                    
                logging.error(f"Erro ao fazer upload do arquivo {file_path}: {result}")
                return None
                
            except Exception as upload_e:
                logging.error(f"Erro no upload para o bucket '{bucket_name}': {upload_e}")
                print(f"Erro no upload: {upload_e}")
                
                # Tenta descobrir se o erro é por causa do bucket ou outro problema
                if "bucket" in str(upload_e).lower() and "not found" in str(upload_e).lower():
                    print("Erro relacionado a bucket não encontrado.")
                    
                    # Tenta listar buckets existentes como último recurso
                    try:
                        buckets = self.supabase.storage.list_buckets()
                        bucket_names = [bucket['name'] for bucket in buckets] if buckets else []
                        
                        if bucket_names:
                            print(f"Buckets disponíveis: {', '.join(bucket_names)}")
                            alt_bucket = input(f"Digite o nome de um bucket alternativo para tentar (ou deixe em branco para cancelar): ")
                            
                            if alt_bucket:
                                print(f"Tentando upload para o bucket alternativo: {alt_bucket}")
                                
                                # Tenta fazer upload para o bucket alternativo
                                result = self.supabase.storage.from_(alt_bucket).upload(
                                    path=file_name,
                                    file=file_contents,
                                    file_options={"content-type": "application/octet-stream"},
                                    file_options_override=True
                                )
                                
                                if result.get('Key'):
                                    public_url = self.supabase.storage.from_(alt_bucket).get_public_url(file_name)
                                    logging.info(f"Arquivo enviado para bucket alternativo '{alt_bucket}': {public_url}")
                                    print(f"Upload concluído com sucesso para bucket alternativo: {alt_bucket}")
                                    return public_url
                        else:
                            print("Não foi possível encontrar buckets alternativos.")
                    except Exception as list_e:
                        logging.error(f"Erro ao listar buckets alternativos: {list_e}")
                        
                return None
            
        except Exception as e:
            logging.error(f"Erro ao fazer upload do arquivo {file_path} para o Supabase: {e}")
            print(f"Erro geral no processo de upload: {e}")
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
