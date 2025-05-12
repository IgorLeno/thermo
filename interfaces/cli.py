
# interfaces/cli.py
import argparse
import shutil
from core.molecule import Molecule
from services.calculation_service import CalculationService
from services.file_service import FileService
from services.pubchem_service import PubChemService
from services.conversion_service import ConversionService
from interfaces.analysis_cli import AnalysisInterface
from config.settings import Settings
from config.constants import *
from typing import List, Optional
from pathlib import Path
import logging
import os
import sys
import time
import webbrowser

class CommandLineInterface:
    """
    Classe que implementa a interface de linha de comando do programa.
    """
    def __init__(self, settings: Settings = None, file_service: FileService = None,
                 pubchem_service: PubChemService = None, conversion_service: ConversionService = None,
                 calculation_service: CalculationService = None):
        self.settings = settings or Settings()
        self.file_service = file_service or FileService()
        self.pubchem_service = pubchem_service or PubChemService()
        self.conversion_service = conversion_service or ConversionService(self.settings)
        self.calculation_service = calculation_service or CalculationService(self.settings, self.file_service, self.conversion_service)
        self.molecules = []
        
        # Inicializa o serviço Supabase se habilitado
        self.supabase_service = None
        if self.settings.supabase.enabled:
            try:
                from services.supabase_service import SupabaseService
                self.supabase_service = SupabaseService(
                    url=self.settings.supabase.url,
                    key=self.settings.supabase.key
                )
            except ImportError:
                logging.error("Biblioteca Supabase não encontrada. Execute 'pip install supabase'.")
            except Exception as e:
                logging.error(f"Erro ao inicializar serviço Supabase na interface: {e}")

    def run(self):
        """Exibe o menu principal e aguarda a escolha do usuário."""
        print("\n==================================================")
        print("  Busca Conformacional e Cálculo de Entalpia      ")
        print("  (CREST + MOPAC)                                 ")
        print("==================================================")
        
        # Verifica se o Supabase está configurado
        supabase_status = "Habilitado" if self.settings.supabase.enabled else "Desabilitado"
        
        while True:
            print("\nMenu Principal:")
            print("1. Realizar cálculo completo para uma molécula")
            print("2. Realizar cálculo completo para várias moléculas")
            print("3. Editar configurações")
            print("4. Exibir resultados")
            print("5. Analisar resultados")
            print(f"6. Configurar dashboard (Supabase: {supabase_status})")
            print("7. Sair")

            choice = input("\nEscolha uma opção: ")

            if choice == "1":
                molecule_name = input("Digite o nome da molécula: ")
                self.calculate_single_molecule(molecule_name)
            elif choice == "2":
                input_method = input("Deseja digitar os nomes das moléculas (1) ou fornecer um arquivo com a lista (2)? ")
                if input_method == "1":
                    molecule_names = input("Digite os nomes das moléculas separados por vírgula: ").split(",")
                    molecule_names = [name.strip() for name in molecule_names]
                    self.calculate_multiple_molecules(molecule_names)
                elif input_method == "2":
                    filepath = input("Digite o caminho do arquivo (cada linha deve conter um nome de molécula): ")
                    try:
                        with open(filepath, "r") as f:
                            molecule_names = [line.strip() for line in f]
                        self.calculate_multiple_molecules(molecule_names)
                    except FileNotFoundError:
                        print(f"Arquivo não encontrado: {filepath}")
                else:
                    print("Opção inválida.")
            elif choice == "3":
                self.edit_settings()
            elif choice == "4":
                self.show_results()
            elif choice == "5":
                self.analyze_results()
            elif choice == "6":
                self.configure_dashboard()
            elif choice == "7":
                print("\nSaindo do programa...")
                break
            else:
                print("Opção inválida. Tente novamente.")

    def calculate_single_molecule(self, molecule_name: str):
        """
        Realiza busca conformacional para uma única molécula.
        """
        try:
            print(f"\n=== Iniciando busca conformacional para {molecule_name} ===")
            logging.info(f"Iniciando busca conformacional para {molecule_name}")
            
            molecule = Molecule(name=molecule_name)
            self.process_molecule(molecule)
            
        except Exception as e:
            logging.error(f"Erro ao processar molécula {molecule_name}: {e}", exc_info=True)
            print(f"\nErro ao processar molécula {molecule_name}. Veja o arquivo de log para mais detalhes.")

    def calculate_multiple_molecules(self, molecule_names: List[str]):
        """
        Realiza busca conformacional para várias moléculas.
        """
        if not molecule_names:
            print("Nenhuma molécula para processar.")
            return
            
        print(f"\n=== Iniciando busca conformacional para {len(molecule_names)} moléculas ===")
        logging.info(f"Iniciando busca conformacional para {len(molecule_names)} moléculas: {molecule_names}")
        
        successful = 0
        failed = 0
        
        for idx, name in enumerate(molecule_names, 1):
            print(f"\n[{idx}/{len(molecule_names)}] Processando: {name}")
            try:
                molecule = Molecule(name=name)
                result = self.process_molecule(molecule)
                if result:
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                logging.error(f"Erro ao processar molécula {name}: {e}", exc_info=True)
                print(f"Erro ao processar molécula {name}. Veja o arquivo de log para mais detalhes.")
                failed += 1
        
        print(f"\n=== Busca conformacional concluída ===")
        print(f"Total: {len(molecule_names)} molécula(s)")
        print(f"Sucesso: {successful} molécula(s)")
        print(f"Falha: {failed} molécula(s)")
        
        logging.info(f"Busca conformacional concluída. Total: {len(molecule_names)}, Sucesso: {successful}, Falha: {failed}")

    def process_molecule(self, molecule: Molecule):
        """
        Processa uma molécula, realizando a busca conformacional com CREST,
        seguida do cálculo de entalpia com MOPAC e armazenando os resultados.
        """
        try:
            start_time = time.time()
            logging.info(f"Iniciando processamento da molécula: {molecule.name}")
            
            print(f"[1/5] Baixando estrutura do PubChem para {molecule.name}...")
            # Baixa o SDF do PubChem
            sdf_path, cid = self.pubchem_service.get_sdf_by_name(molecule.name)
            if sdf_path is None:
                print(f"Molécula '{molecule.name}' não encontrada no PubChem.")
                return False
                
            molecule.sdf_path = sdf_path
            molecule.pubchem_cid = cid
            print(f"      Estrutura baixada com sucesso. CID: {cid}")

            print(f"[2/5] Convertendo SDF para XYZ utilizando OpenBabel...")
            # Converte o SDF para XYZ
            self.conversion_service.sdf_to_xyz(molecule)
            print(f"      Conversão concluída: {molecule.xyz_path}")

            print(f"[3/5] Executando busca conformacional com CREST...")
            print(f"      Este processo pode demorar vários minutos. Por favor, aguarde...")
            # Executa o cálculo completo (CREST + MOPAC)
            success = self.calculation_service.run_calculation(molecule)
            if not success:
                print(f"\nErro durante o cálculo para {molecule.name}. Veja o log para mais detalhes.")
                return False
                
            print(f"[4/5] Calculando entalpia de formação com MOPAC...")
            
            # Verifica se a entalpia foi calculada
            if hasattr(molecule, 'enthalpy_formation_mopac') and molecule.enthalpy_formation_mopac is not None:
                print(f"      Entalpia de formação: {molecule.enthalpy_formation_mopac} (unidade do MOPAC)")
            else:
                print(f"      Não foi possível calcular a entalpia de formação.")
            
            print(f"[5/5] Organizando resultados...")
            self.molecules.append(molecule)

            # Verifica os resultados
            final_dir = OUTPUT_DIR / molecule.name
            
            # Definir diretórios aqui, antes de serem usados
            crest_dir = CREST_DIR / molecule.name
            mopac_dir = MOPAC_DIR / molecule.name
            pdb_file = PDB_DIR / f"{molecule.name}.pdb"
            
            # Verificando contagem de confôrmeros
            conformers_count = 0
            crest_conformers_path = crest_dir / CREST_CONFORMERS_FILE
            if os.path.exists(crest_conformers_path):
                try:
                    with open(crest_conformers_path, 'r') as f:
                        conformers_count = sum(1 for line in f if line.strip() == molecule.name)
                except:
                    pass  # Ignora erros na contagem
            
            elapsed_time = time.time() - start_time
            print(f"\n=== Cálculo completo de {molecule.name} concluído em {elapsed_time:.1f} segundos ===")
            
            # Verificar os arquivos nos locais corretos (não no diretório final)
            status = "CONCLUÍDO"
            files_status = []
            
            # Verificar arquivos CREST no diretório repository/crest
            for file, desc in [
                (CREST_BEST_FILE, "Melhor confôrmero (CREST)"),
                (CREST_CONFORMERS_FILE, "Confôrmeros encontrados (CREST)"),
                (CREST_LOG_FILE, "Log do CREST"),
                (CREST_ENERGIES_FILE, "Energias dos confôrmeros (CREST)")
            ]:
                if os.path.exists(crest_dir / file):
                    files_status.append(f"✓ {desc}")
                else:
                    files_status.append(f"✗ {desc}")
                    if file in [CREST_BEST_FILE, CREST_CONFORMERS_FILE]:
                        status = "INCOMPLETO"
            
            # Verificar arquivos MOPAC no diretório repository/mopac
            if os.path.exists(mopac_dir / f"{molecule.name}.out"):
                files_status.append(f"✓ Arquivo de saída do MOPAC (.out)")
            else:
                files_status.append(f"✗ Arquivo de saída do MOPAC (.out)")
                status = "INCOMPLETO"
                
            if os.path.exists(mopac_dir / f"{molecule.name}.arc"):
                files_status.append(f"✓ Arquivo de geometria do MOPAC (.arc)")
            else:
                files_status.append(f"✗ Arquivo de geometria do MOPAC (.arc)")
                
            if os.path.exists(pdb_file):
                files_status.append(f"✓ Arquivo de estrutura PDB")
            else:
                files_status.append(f"✗ Arquivo de estrutura PDB")
            
            print(f"Status: {status}")
            for status in files_status:
                print(f"  {status}")
                
            if conformers_count > 0:
                print(f"Número de confôrmeros encontrados: {conformers_count}")
            
            # Exibe a entalpia de formação se disponível
            if hasattr(molecule, 'enthalpy_formation_mopac') and molecule.enthalpy_formation_mopac is not None:
                print(f"Entalpia de formação (MOPAC): {molecule.enthalpy_formation_mopac}")
                
            # Mostre os caminhos para os diretórios de resultados
            print(f"Diretório CREST: {crest_dir}")
            print(f"Diretório MOPAC: {mopac_dir}")
            print(f"Diretório PDB: {PDB_DIR}")
            
            # Informa se os resultados foram enviados para o Supabase
            if self.settings.supabase.enabled and self.supabase_service and self.supabase_service.enabled:
                print(f"Resultados enviados para o dashboard Supabase.")
            
            logging.info(f"Processamento concluído para {molecule.name}. Status: {status}")
            return True

        except Exception as e:
            logging.error(f"Erro ao processar a molécula {molecule.name}: {e}", exc_info=True)
            print(f"\nErro ao processar a molécula {molecule.name}. Veja o log para mais detalhes.")
            return False

    def edit_settings(self):
        """
        Edita as configurações com base nos argumentos fornecidos.
        """
        while True:
            print("\nConfigurações Atuais:")
            print("\n== Parâmetros do CREST ==")
            print(f"1. Número de threads: {self.settings.calculation_params.n_threads}")
            print(f"2. Método do CREST: {self.settings.calculation_params.crest_method}")
            print(f"5. Temperatura eletrônica (Kelvin): {self.settings.calculation_params.electronic_temperature}")
            print(f"6. Solvente: {self.settings.calculation_params.solvent or 'Nenhum'}")
            
            print("\n== Parâmetros do MOPAC ==")
            print(f"7. Palavras-chave do MOPAC: {self.settings.mopac_keywords}")
            
            print("\n== Caminhos dos Programas ==")
            print(f"3. Caminho do OpenBabel: {self.settings.openbabel_path}")
            print(f"4. Caminho do CREST: {self.settings.crest_path}")
            print(f"8. Caminho do MOPAC: {self.settings.mopac_executable_path}")
            
            print("\n== Configurações do Supabase ==")
            print(f"10. Status do Supabase: {'Habilitado' if self.settings.supabase.enabled else 'Desabilitado'}")
            print(f"11. URL da API do Supabase: {self.settings.supabase.url}")
            print(f"12. Chave da API do Supabase: {'*' * 8 if self.settings.supabase.key else 'Não configurada'}")
            print(f"13. Upload de arquivos para Storage: {'Habilitado' if self.settings.supabase.storage_enabled else 'Desabilitado'}")
            
            print("\n== Opções ==")
            print("9. Salvar configurações")
            print("0. Voltar ao menu principal")

            choice = input("\nEscolha uma opção para editar: ")

            if choice == "1":
                try:
                    threads = int(input("Digite o novo número de threads: "))
                    if threads < 1:
                        print("Número de threads deve ser pelo menos 1.")
                    else:
                        self.settings.calculation_params.n_threads = threads
                        print(f"Número de threads atualizado para: {threads}")
                except ValueError:
                    print("Por favor, digite um número inteiro válido.")
            elif choice == "2":
                method = input("Digite o novo método do CREST (gfn1, gfn2, gfnff): ").lower()
                if method in ["gfn1", "gfn2", "gfnff"]:
                    self.settings.calculation_params.crest_method = method
                    print(f"Método CREST atualizado para: {method}")
                else:
                    print("Método inválido. Use gfn1, gfn2 ou gfnff.")
            elif choice == "3":
                path = input("Digite o novo caminho do OpenBabel: ")
                if os.path.exists(path):
                    self.settings.openbabel_path = path
                    print(f"Caminho do OpenBabel atualizado.")
                else:
                    print(f"Aviso: O caminho {path} não existe. Deseja continuar? (s/n)")
                    if input().lower() == 's':
                        self.settings.openbabel_path = path
                        print(f"Caminho do OpenBabel atualizado.")
            elif choice == "4":
                path = input("Digite o novo caminho do CREST: ")
                self.settings.crest_path = path
                print(f"Caminho do CREST atualizado.")
            elif choice == "5":
                try:
                    temp = float(input("Digite a nova temperatura eletrônica (em Kelvin): "))
                    if temp <= 0:
                        print("A temperatura deve ser maior que 0 Kelvin.")
                    else:
                        self.settings.calculation_params.electronic_temperature = temp
                        print(f"Temperatura eletrônica atualizada para: {temp} K")
                except ValueError:
                    print("Por favor, digite um número válido.")
            elif choice == "6":
                solvent = input("Digite o nome do solvente (ou deixe em branco para nenhum): ")
                self.settings.calculation_params.solvent = solvent if solvent.strip() else None
                if solvent.strip():
                    print(f"Solvente atualizado para: {solvent}")
                else:
                    print("Solvente removido (cálculo em fase gasosa).")
            elif choice == "7":
                keywords = input(f"Digite as novas palavras-chave do MOPAC (atual: {self.settings.mopac_keywords}): ")
                if keywords.strip():
                    self.settings.mopac_keywords = keywords
                    print(f"Palavras-chave do MOPAC atualizadas para: {keywords}")
                else:
                    print("Palavras-chave do MOPAC não foram alteradas.")
            elif choice == "8":
                path = input("Digite o novo caminho do executável do MOPAC: ")
                self.settings.mopac_executable_path = Path(path)
                print(f"Caminho do MOPAC atualizado.")
            elif choice == "9":
                filepath = input("Digite o caminho para salvar o arquivo de configuração (padrão: config.yaml): ")
                if not filepath:
                    filepath = "config.yaml"
                self.settings.save_settings(filepath)
                print(f"Configurações salvas com sucesso em: {filepath}")
            elif choice == "10":
                enable = input("Habilitar o Supabase? (s/n): ").lower()
                self.settings.supabase.enabled = enable == "s"
                print(f"Supabase {'habilitado' if self.settings.supabase.enabled else 'desabilitado'}.")
            elif choice == "11":
                url = input("Digite a URL da API do Supabase: ")
                if url:
                    self.settings.supabase.url = url
                    print("URL da API atualizada.")
                else:
                    print("URL não alterada.")
            elif choice == "12":
                key = input("Digite a chave da API do Supabase: ")
                if key:
                    self.settings.supabase.key = key
                    print("Chave da API atualizada.")
                else:
                    print("Chave não alterada.")
            elif choice == "13":
                enable = input("Habilitar upload de arquivos para o Storage? (s/n): ").lower()
                self.settings.supabase.storage_enabled = enable == "s"
                if self.settings.supabase.storage_enabled:
                    bucket = input(f"Nome do bucket para armazenamento de arquivos (padrão: {self.settings.supabase.molecules_bucket}): ")
                    if bucket:
                        self.settings.supabase.molecules_bucket = bucket
                print(f"Upload de arquivos {'habilitado' if self.settings.supabase.storage_enabled else 'desabilitado'}.")
            elif choice == "0":
                return
            else:
                print("Opção inválida.")

    def show_results(self):
        """Exibe os resultados das buscas conformacionais realizadas."""
        if not self.molecules:
            print("\nNenhuma busca conformacional foi realizada ainda nesta sessão.")
            
            # Verifica se há resultados de execuções anteriores
            try:
                output_dir = OUTPUT_DIR
                if output_dir.exists():
                    previous_results = [d for d in output_dir.iterdir() if d.is_dir()]
                    if previous_results:
                        print(f"\nResultados de execuções anteriores encontrados: {len(previous_results)} molécula(s)")
                        print("\nMoléculas com resultados salvos:")
                        for result_dir in previous_results:
                            has_conformers = (result_dir / CREST_CONFORMERS_FILE).exists()
                            has_best = (result_dir / CREST_BEST_FILE).exists()
                            status = "Completo" if has_conformers and has_best else "Incompleto"
                            print(f"  - {result_dir.name}: {status}")
                        
                        # Oferece opção para gerar resumo
                        if input("\nDeseja gerar um arquivo de resumo para estes resultados? (s/n): ").lower() == "s":
                            self._generate_summary_for_existing_results(previous_results)
                            return
            except Exception as e:
                logging.error(f"Erro ao verificar resultados anteriores: {e}")
            
            return

        print("\nResultados dos cálculos realizados nesta sessão:")
        print(f"{'Molécula':<15} {'CID':<8} {'Status':<12} {'Entalpia (MOPAC)':<20}")
        print("-" * 55)
        
        for molecule in self.molecules:
            # Verifica se os arquivos existem nos diretórios corretos
            crest_dir = CREST_DIR / molecule.name
            mopac_dir = MOPAC_DIR / molecule.name
            
            # Verificar status dos arquivos CREST
            has_conformers = os.path.exists(crest_dir / CREST_CONFORMERS_FILE)
            has_best = os.path.exists(crest_dir / CREST_BEST_FILE)
            
            # Verificar status dos arquivos MOPAC
            has_mopac_out = os.path.exists(mopac_dir / f"{molecule.name}.out")
            has_mopac_arc = os.path.exists(mopac_dir / f"{molecule.name}.arc")
            
            if has_conformers and has_best and has_mopac_out:
                status = "Completo"
            elif has_conformers and has_best:
                status = "CREST OK"
            else:
                status = "Incompleto"
            
            # Verifica se há informação de entalpia
            entalpia = f"{molecule.enthalpy_formation_mopac}" if hasattr(molecule, 'enthalpy_formation_mopac') and molecule.enthalpy_formation_mopac is not None else "N/A"
            
            print(f"{molecule.name:<15} {str(molecule.pubchem_cid):<8} {status:<12} {entalpia:<20}")

        # Opção para gerar um arquivo de resumo
        if input("\nDeseja gerar um arquivo de resumo (s/n)? ").lower() == "s":
            output_file = input("Digite o nome do arquivo de resumo (padrão: conformer_summary.txt): ")
            if not output_file:
                output_file = "conformer_summary.txt"
            if not output_file.endswith(".txt"):
                output_file += ".txt"
            self.file_service.generate_summary(self.molecules, output_file)
            print(f"Arquivo de resumo gerado: {output_file}")
            
    def analyze_results(self):
        """Inicia a interface de análise de resultados."""
        analysis_interface = AnalysisInterface()
        analysis_interface.run()
    
    def configure_dashboard(self):
        """Configura e gerencia o dashboard Supabase."""
        while True:
            supabase_status = "Habilitado" if self.settings.supabase.enabled else "Desabilitado"
            
            print("\n===== Configuração do Dashboard =====")
            print(f"Status do Supabase: {supabase_status}")
            
            if self.settings.supabase.enabled:
                print(f"URL da API: {self.settings.supabase.url}")
                print(f"Chave da API: {'*' * 8 if self.settings.supabase.key else 'Não configurada'}")
                print(f"Upload de arquivos: {'Habilitado' if self.settings.supabase.storage_enabled else 'Desabilitado'}")
            
            print("\nOpções:")
            print("1. Configurar credenciais do Supabase")
            print("2. Testar conexão com o Supabase")
            print("3. Sincronizar resultados existentes")
            print("4. Abrir o dashboard no navegador")
            print("5. Voltar ao menu principal")
            
            choice = input("\nEscolha uma opção: ")
            
            if choice == "1":
                self._configure_supabase_credentials()
            elif choice == "2":
                self._test_supabase_connection()
            elif choice == "3":
                self._sync_existing_results()
            elif choice == "4":
                self._open_dashboard()
            elif choice == "5":
                break
            else:
                print("Opção inválida. Tente novamente.")
    
    def _configure_supabase_credentials(self):
        """Configura as credenciais do Supabase."""
        print("\n----- Configuração do Supabase -----")
        
        # Habilitar/desabilitar Supabase
        enable = input(f"Habilitar o Supabase? ({'s' if self.settings.supabase.enabled else 'n'}): ").lower()
        if enable:
            self.settings.supabase.enabled = enable == "s"
        
        if not self.settings.supabase.enabled:
            print("Supabase desabilitado.")
            return
        
        # URL da API
        url = input(f"URL da API do Supabase (atual: {self.settings.supabase.url}): ")
        if url:
            self.settings.supabase.url = url
        
        # Chave da API
        key = input(f"Chave da API do Supabase (atual: {'*' * 8 if self.settings.supabase.key else 'Não configurada'}): ")
        if key:
            self.settings.supabase.key = key
        
        # Configurações de Storage
        storage = input(f"Habilitar upload de arquivos para Storage? ({'s' if self.settings.supabase.storage_enabled else 'n'}): ").lower()
        if storage:
            self.settings.supabase.storage_enabled = storage == "s"
        
        if self.settings.supabase.storage_enabled:
            bucket = input(f"Nome do bucket para armazenamento (atual: {self.settings.supabase.molecules_bucket}): ")
            if bucket:
                self.settings.supabase.molecules_bucket = bucket
        
        # Salvar configurações
        save = input("Salvar configurações? (s/n): ").lower()
        if save == "s":
            self.settings.save_settings("config.yaml")
            print("Configurações do Supabase salvas com sucesso.")
            
            # Reinicializa o serviço Supabase com as novas configurações
            try:
                from services.supabase_service import SupabaseService
                self.supabase_service = SupabaseService(
                    url=self.settings.supabase.url,
                    key=self.settings.supabase.key
                )
                # Atualiza o serviço de cálculo também
                if self.calculation_service:
                    self.calculation_service.supabase_service = self.supabase_service
            except ImportError:
                print("Biblioteca Supabase não encontrada. Execute 'pip install supabase'.")
            except Exception as e:
                print(f"Erro ao inicializar serviço Supabase: {e}")
    
    def _test_supabase_connection(self):
        """Testa a conexão com o Supabase."""
        if not self.settings.supabase.enabled:
            print("Supabase está desabilitado. Habilite-o primeiro.")
            return
        
        print("\nTestando conexão com o Supabase...")
        
        try:
            # Verifica se o serviço Supabase existe e está habilitado
            if not self.supabase_service:
                from services.supabase_service import SupabaseService
                self.supabase_service = SupabaseService(
                    url=self.settings.supabase.url,
                    key=self.settings.supabase.key
                )
            
            if not self.supabase_service.enabled:
                print("Erro: Serviço Supabase não está habilitado. Verifique as credenciais.")
                return
            
            # Tenta fazer uma consulta simples
            try:
                response = self.supabase_service.supabase.table("molecules").select("count", count="exact").execute()
                count = response.count
                print(f"Conexão bem-sucedida! {count} molécula(s) encontrada(s) no banco de dados.")
                
                # Testa o Storage se estiver habilitado
                if self.settings.supabase.storage_enabled:
                    storage_test = self.supabase_service.supabase.storage.get_bucket(self.settings.supabase.molecules_bucket)
                    print(f"Conexão com o Storage bem-sucedida! Bucket '{self.settings.supabase.molecules_bucket}' está acessível.")
            except Exception as e:
                print(f"Erro ao acessar o banco de dados: {e}")
                
        except ImportError:
            print("Erro: Biblioteca Supabase não encontrada. Execute 'pip install supabase'.")
        except Exception as e:
            print(f"Erro ao testar conexão: {e}")
    
    def _sync_existing_results(self):
        """Sincroniza resultados existentes com o Supabase."""
        if not self.settings.supabase.enabled:
            print("Supabase está desabilitado. Habilite-o primeiro.")
            return
            
        if not self.supabase_service or not self.supabase_service.enabled:
            print("Serviço Supabase não está habilitado. Verifique a conexão.")
            return
        
        print("\nBuscando resultados existentes...")
        
        try:
            output_dir = OUTPUT_DIR
            if not output_dir.exists():
                print("Nenhum resultado encontrado. Execute a busca conformacional primeiro.")
                return
                
            molecule_dirs = [d for d in output_dir.iterdir() if d.is_dir()]
            
            if not molecule_dirs:
                print("Nenhum resultado encontrado. Execute a busca conformacional primeiro.")
                return
                
            print(f"Encontrados {len(molecule_dirs)} molécula(s) com resultados.")
            print("\nMoléculas disponíveis para sincronização:")
            
            for i, mol_dir in enumerate(molecule_dirs, 1):
                print(f"{i}. {mol_dir.name}")
            
            choice = input("\nSincronizar todas as moléculas (t) ou escolher quais sincronizar (e)? ")
            
            molecules_to_sync = []
            if choice.lower() == "t":
                molecules_to_sync = [d.name for d in molecule_dirs]
            elif choice.lower() == "e":
                indices = input("Digite os números das moléculas a sincronizar, separados por vírgula: ")
                try:
                    selected = [int(idx.strip()) - 1 for idx in indices.split(",")]
                    molecules_to_sync = [molecule_dirs[idx].name for idx in selected if 0 <= idx < len(molecule_dirs)]
                except (ValueError, IndexError):
                    print("Seleção inválida.")
                    return
            else:
                print("Opção inválida.")
                return
            
            if not molecules_to_sync:
                print("Nenhuma molécula selecionada para sincronização.")
                return
            
            print(f"\nSincronizando {len(molecules_to_sync)} molécula(s) com o Supabase...")
            
            from services.analysis.conformer_analyzer import ConformerAnalyzer
            analyzer = ConformerAnalyzer()
            
            successful = 0
            failed = 0
            
            for mol_name in molecules_to_sync:
                print(f"Sincronizando {mol_name}...")
                
                try:
                    # Criamos uma molécula temporária com os dados necessários
                    molecule = Molecule(name=mol_name)
                    
                    # Configuramos os caminhos para os arquivos
                    crest_dir = CREST_DIR / mol_name
                    mopac_dir = MOPAC_DIR / mol_name
                    
                    molecule.crest_best_path = str(crest_dir / CREST_BEST_FILE)
                    molecule.crest_conformers_path = str(crest_dir / CREST_CONFORMERS_FILE)
                    
                    # Verificamos e extraímos a entalpia se disponível
                    mopac_out_file = mopac_dir / f"{mol_name}.out"
                    if mopac_out_file.exists():
                        # Use o método do CalculationService para extrair a entalpia
                        enthalpy = self.calculation_service._extract_mopac_enthalpy(mopac_out_file)
                        if enthalpy is not None:
                            molecule.enthalpy_formation_mopac = enthalpy
                    
                    # Obtemos estatísticas dos confôrmeros
                    conformer_stats = analyzer.get_conformer_statistics(mol_name)
                    
                    # Upload para o Supabase
                    molecule_id = self.supabase_service.upload_molecule(molecule)
                    
                    if not molecule_id:
                        print(f"Erro ao enviar molécula {mol_name} para o Supabase.")
                        failed += 1
                        continue
                    
                    # Upload de resultados CREST
                    crest_params = {
                        "n_threads": self.settings.calculation_params.n_threads,
                        "method": self.settings.calculation_params.crest_method,
                        "electronic_temperature": self.settings.calculation_params.electronic_temperature,
                        "solvent": self.settings.calculation_params.solvent
                    }
                    
                    crest_results = {
                        "num_conformers": conformer_stats.get("num_conformers") if conformer_stats and conformer_stats.get("success", False) else None,
                        "best_conformer_path": molecule.crest_best_path,
                        "all_conformers_path": molecule.crest_conformers_path
                    }
                    
                    # Adiciona estatísticas do conformador se disponíveis
                    if conformer_stats and conformer_stats.get("success", False):
                        crest_results["energy_distribution"] = conformer_stats.get("relative_energies", [])
                        crest_results["relative_energies"] = conformer_stats.get("relative_energies", [])
                        crest_results["populations"] = conformer_stats.get("populations", [])
                    
                    crest_success = self.supabase_service.upload_calculation_results(
                        molecule_id=molecule_id,
                        calculation_type="crest",
                        status="completed",
                        parameters=crest_params,
                        results=crest_results
                    )
                    
                    # Upload de resultados MOPAC se disponíveis
                    mopac_success = True
                    if hasattr(molecule, "enthalpy_formation_mopac") and molecule.enthalpy_formation_mopac is not None:
                        mopac_params = {
                            "keywords": self.settings.mopac_keywords
                        }
                        
                        mopac_results = {
                            "enthalpy_formation": molecule.enthalpy_formation_mopac,
                            "method": self.settings.mopac_keywords.split()[0] if self.settings.mopac_keywords else None,
                            "output_path": str(mopac_out_file) if mopac_out_file.exists() else None
                        }
                        
                        mopac_success = self.supabase_service.upload_calculation_results(
                            molecule_id=molecule_id,
                            calculation_type="mopac",
                            status="completed",
                            parameters=mopac_params,
                            results=mopac_results
                        )
                    
                    if crest_success and mopac_success:
                        print(f"✓ {mol_name} sincronizado com sucesso!")
                        successful += 1
                    else:
                        print(f"✗ Erro parcial ao sincronizar {mol_name}.")
                        failed += 1
                        
                except Exception as e:
                    print(f"✗ Erro ao sincronizar {mol_name}: {e}")
                    failed += 1
            
            print(f"\nSincronização concluída: {successful} sucesso(s), {failed} falha(s).")
            
        except Exception as e:
            print(f"Erro durante a sincronização: {e}")
    
    def _open_dashboard(self):
        """Abre o dashboard Supabase no navegador."""
        if not self.settings.supabase.enabled:
            print("Supabase está desabilitado. Habilite-o primeiro.")
            return
        
        # Extrai o domínio do projeto a partir da URL da API
        if not self.settings.supabase.url:
            print("URL da API do Supabase não configurada.")
            return
        
        try:
            # A URL da API é geralmente algo como: https://xyzabc.supabase.co/rest/v1/
            # Precisamos extrair a parte https://xyzabc.supabase.co
            parts = self.settings.supabase.url.split("/")
            if len(parts) >= 3:
                base_url = f"{parts[0]}//{parts[2]}"
                dashboard_url = f"{base_url}/dashboard/"
                
                print(f"Abrindo dashboard Supabase em: {dashboard_url}")
                webbrowser.open(dashboard_url)
            else:
                print("Formato de URL inválido.")
        except Exception as e:
            print(f"Erro ao abrir o dashboard: {e}")
            
    def _generate_summary_for_existing_results(self, result_dirs):
        """Gera um resumo para resultados existentes de execuções anteriores."""
        try:
            output_file = input("Digite o nome do arquivo de resumo (padrão: calculation_summary.txt): ")
            if not output_file:
                output_file = "calculation_summary.txt"
            if not output_file.endswith(".txt"):
                output_file += ".txt"
                
            with open(output_file, "w") as f:
                f.write("Resumo dos cálculos (execuções anteriores):\n\n")
                f.write(f"{'Molécula':<15} {'Status CREST':<12} {'Status MOPAC':<12} {'Entalpia':<20} {'Diretório':<40}\n")
                f.write("-" * 99 + "\n")
                
                for result_dir in result_dirs:
                    molecule_name = result_dir.name
                    
                    # Verifica status do CREST
                    has_conformers = (result_dir / CREST_CONFORMERS_FILE).exists()
                    has_best = (result_dir / CREST_BEST_FILE).exists()
                    crest_status = "Completo" if has_conformers and has_best else "Incompleto"
                    
                    # Verifica status do MOPAC
                    has_mopac_out = (result_dir / f"{molecule_name}.out").exists()
                    has_mopac_arc = (result_dir / f"{molecule_name}.arc").exists()
                    mopac_status = "Completo" if has_mopac_out and has_mopac_arc else "Incompleto"
                    
                    # Tenta obter a entalpia do arquivo de resumo
                    enthalpy_str = "N/A"
                    enthalpy_summary_path = result_dir / "enthalpy_summary.txt"
                    if enthalpy_summary_path.exists():
                        try:
                            with open(enthalpy_summary_path, 'r') as ef:
                                for line in ef:
                                    if "Entalpia de formação" in line:
                                        enthalpy_str = line.split(":", 1)[1].strip()
                                        break
                        except:
                            pass
                    
                    # Alternativa: verificar arquivo results_summary.txt
                    if enthalpy_str == "N/A":
                        results_summary_path = result_dir / "results_summary.txt"
                        if results_summary_path.exists():
                            try:
                                with open(results_summary_path, 'r') as rf:
                                    for line in rf:
                                        if "Entalpia de Formação" in line and "não calculada" not in line.lower():
                                            enthalpy_str = line.split(":", 1)[1].strip()
                                            break
                            except:
                                pass
                    
                    f.write(f"{molecule_name:<15} {crest_status:<12} {mopac_status:<12} {enthalpy_str:<20} {str(result_dir):<40}\n")
                    
            print(f"Arquivo de resumo gerado: {output_file}")
            
        except Exception as e:
            logging.error(f"Erro ao gerar resumo para resultados existentes: {e}")
            print(f"Erro ao gerar arquivo de resumo. Veja o log para mais detalhes.")
