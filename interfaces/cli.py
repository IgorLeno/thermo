
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
import subprocess
import shutil as shell_utils

class CommandLineInterface:
    """
    Classe que implementa a interface de linha de comando do programa.
    """
    def __init__(self, settings: Settings = None, file_service: FileService = None,
                 pubchem_service: PubChemService = None, conversion_service: ConversionService = None,
                 calculation_service: CalculationService = None):
        # Carrega configurações do arquivo se settings não foi fornecido
        if settings is None:
            self.settings = Settings()
            self.settings.load_settings("config.yaml")
        else:
            self.settings = settings
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

    def _detect_browsers(self):
        """Detecta navegadores instalados no sistema."""
        browsers = {}
        
        # Caminhos comuns do Chrome no Windows
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                browsers['chrome'] = path
                break
        
        # Caminhos comuns do Firefox
        firefox_paths = [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
        ]
        
        for path in firefox_paths:
            if os.path.exists(path):
                browsers['firefox'] = path
                break
        
        # Edge (geralmente está instalado por padrão no Windows)
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
        
        for path in edge_paths:
            if os.path.exists(path):
                browsers['edge'] = path
                break
        
        return browsers

    def _open_url_with_browser(self, url, browser_choice=None):
        """
        Abre uma URL com um navegador específico ou permite ao usuário escolher.
        
        Args:
            url: URL a ser aberta
            browser_choice: 'chrome', 'firefox', 'edge', 'default' ou None para mostrar menu
        """
        browsers = self._detect_browsers()
        
        if browser_choice is None:
            # Mostra opções de navegador ao usuário
            print("\nEscolha o navegador para abrir:")
            options = []
            
            if 'chrome' in browsers:
                options.append(('chrome', 'Google Chrome'))
            if 'firefox' in browsers:
                options.append(('firefox', 'Mozilla Firefox'))
            if 'edge' in browsers:
                options.append(('edge', 'Microsoft Edge'))
            
            options.append(('default', 'Navegador padrão do sistema'))
            options.append(('clipboard', 'Copiar URL para área de transferência'))
            options.append(('cancel', 'Cancelar'))
            
            for i, (key, name) in enumerate(options, 1):
                print(f"{i}. {name}")
            
            try:
                choice = int(input("\nEscolha uma opção: ")) - 1
                if 0 <= choice < len(options):
                    browser_choice = options[choice][0]
                else:
                    print("Opção inválida.")
                    return False
            except ValueError:
                print("Por favor, digite um número válido.")
                return False
        
        try:
            if browser_choice == 'cancel':
                print("Operação cancelada.")
                return False
            elif browser_choice == 'clipboard':
                # Copia para área de transferência
                try:
                    import pyperclip
                    pyperclip.copy(url)
                    print(f"URL copiada para área de transferência: {url}")
                    print("Cole no navegador de sua escolha (Ctrl+V)")
                    return True
                except ImportError:
                    # Fallback: mostra a URL na tela
                    print(f"URL para copiar manualmente: {url}")
                    print("(Copie esta URL e cole no navegador logado na conta correta)")
                    return True
            elif browser_choice == 'default':
                # Usa navegador padrão
                webbrowser.open(url)
                return True
            elif browser_choice in browsers:
                # Usa navegador específico
                browser_path = browsers[browser_choice]
                print(f"Abrindo com {browser_choice.title()}...")
                
                # Abre o navegador específico com a URL
                subprocess.Popen([browser_path, url])
                return True
            else:
                print(f"Navegador {browser_choice} não encontrado no sistema.")
                return False
        except Exception as e:
            print(f"Erro ao abrir URL: {e}")
            print(f"URL para abrir manualmente: {url}")
            return False

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

    def _save_settings_auto(self):
        """Salva as configurações automaticamente."""
        try:
            self.settings.save_settings("config.yaml")
        except Exception as e:
            logging.warning(f"Não foi possível salvar configurações automaticamente: {e}")
    
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
                        self._save_settings_auto()
                except ValueError:
                    print("Por favor, digite um número inteiro válido.")
            elif choice == "2":
                method = input("Digite o novo método do CREST (gfn1, gfn2, gfnff): ").lower()
                if method in ["gfn1", "gfn2", "gfnff"]:
                    self.settings.calculation_params.crest_method = method
                    print(f"Método CREST atualizado para: {method}")
                    self._save_settings_auto()
                else:
                    print("Método inválido. Use gfn1, gfn2 ou gfnff.")
            elif choice == "3":
                path = input("Digite o novo caminho do OpenBabel: ")
                if os.path.exists(path):
                    self.settings.openbabel_path = path
                    print(f"Caminho do OpenBabel atualizado.")
                    self._save_settings_auto()
                else:
                    print(f"Aviso: O caminho {path} não existe. Deseja continuar? (s/n)")
                    if input().lower() == 's':
                        self.settings.openbabel_path = path
                        print(f"Caminho do OpenBabel atualizado.")
                        self._save_settings_auto()
            elif choice == "4":
                path = input("Digite o novo caminho do CREST: ")
                self.settings.crest_path = path
                print(f"Caminho do CREST atualizado.")
                self._save_settings_auto()
            elif choice == "5":
                try:
                    temp = float(input("Digite a nova temperatura eletrônica (em Kelvin): "))
                    if temp <= 0:
                        print("A temperatura deve ser maior que 0 Kelvin.")
                    else:
                        self.settings.calculation_params.electronic_temperature = temp
                        print(f"Temperatura eletrônica atualizada para: {temp} K")
                        self._save_settings_auto()
                except ValueError:
                    print("Por favor, digite um número válido.")
            elif choice == "6":
                solvent = input("Digite o nome do solvente (ou deixe em branco para nenhum): ")
                self.settings.calculation_params.solvent = solvent if solvent.strip() else None
                if solvent.strip():
                    print(f"Solvente atualizado para: {solvent}")
                else:
                    print("Solvente removido (cálculo em fase gasosa).")
                self._save_settings_auto()
            elif choice == "7":
                keywords = input(f"Digite as novas palavras-chave do MOPAC (atual: {self.settings.mopac_keywords}): ")
                if keywords.strip():
                    self.settings.mopac_keywords = keywords
                    print(f"Palavras-chave do MOPAC atualizadas para: {keywords}")
                    self._save_settings_auto()
                else:
                    print("Palavras-chave do MOPAC não foram alteradas.")
            elif choice == "8":
                path = input("Digite o novo caminho do executável do MOPAC: ")
                self.settings.mopac_executable_path = Path(path)
                print(f"Caminho do MOPAC atualizado.")
                self._save_settings_auto()
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
                self._save_settings_auto()
            elif choice == "11":
                url = input("Digite a URL da API do Supabase: ")
                if url:
                    self.settings.supabase.url = url
                    print("URL da API atualizada.")
                    self._save_settings_auto()
                else:
                    print("URL não alterada.")
            elif choice == "12":
                key = input("Digite a chave da API do Supabase: ")
                if key:
                    self.settings.supabase.key = key
                    print("Chave da API atualizada.")
                    self._save_settings_auto()
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
                self._save_settings_auto()
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
                # CORREÇÃO: Verifica ambos os diretórios (repository e final_molecules)
                repository_crest_dir = CREST_DIR
                repository_mopac_dir = MOPAC_DIR
                output_dir = OUTPUT_DIR
                
                # Combina moléculas de ambos os diretórios
                molecule_names = set()
                
                # Verifica repository/crest
                if repository_crest_dir.exists():
                    for d in repository_crest_dir.iterdir():
                        if d.is_dir():
                            molecule_names.add(d.name)
                
                # Verifica final_molecules/output
                if output_dir.exists():
                    for d in output_dir.iterdir():
                        if d.is_dir():
                            molecule_names.add(d.name)
                
                if molecule_names:
                    print(f"\nResultados de execuções anteriores encontrados: {len(molecule_names)} molécula(s)")
                    print("\nMoléculas com resultados salvos:")
                    
                    for mol_name in sorted(molecule_names):
                        # Verifica status nos diretórios repository
                        crest_dir = repository_crest_dir / mol_name
                        mopac_dir = repository_mopac_dir / mol_name
                        
                        has_crest_best = (crest_dir / CREST_BEST_FILE).exists()
                        has_conformers = (crest_dir / CREST_CONFORMERS_FILE).exists()
                        has_mopac_out = (mopac_dir / f"{mol_name}.out").exists()
                        
                        # Se não encontrar na repository, verifica em final_molecules
                        if not has_crest_best or not has_conformers or not has_mopac_out:
                            final_dir = output_dir / mol_name
                            if final_dir.exists():
                                if not has_crest_best:
                                    has_crest_best = (final_dir / CREST_BEST_FILE).exists()
                                if not has_conformers:
                                    has_conformers = (final_dir / CREST_CONFORMERS_FILE).exists()
                                if not has_mopac_out:
                                    has_mopac_out = (final_dir / f"{mol_name}.out").exists()
                        
                        # Determina o status
                        if has_crest_best and has_conformers and has_mopac_out:
                            status = "Completo"
                        elif has_crest_best and has_conformers:
                            status = "CREST OK"
                        else:
                            status = "Incompleto"
                        
                        print(f"  - {mol_name}: {status}")
                    
                    # Oferece opção para gerar resumo
                    if input("\nDeseja gerar um arquivo de resumo para estes resultados? (s/n): ").lower() == "s":
                        # Cria uma lista de Path objects para compatibilidade
                        result_dirs = []
                        for mol_name in molecule_names:
                            # Prioriza repository, mas se não existir, usa final_molecules
                            if (repository_crest_dir / mol_name).exists():
                                result_dirs.append(repository_crest_dir / mol_name)
                            elif (output_dir / mol_name).exists():
                                result_dirs.append(output_dir / mol_name)
                        
                        self._generate_summary_for_existing_results(result_dirs)
                        return
            except Exception as e:
                logging.error(f"Erro ao verificar resultados anteriores: {e}")
            
            return

        print("\nResultados dos cálculos realizados nesta sessão:")
        print(f"{'Molécula':<20} {'Status':<12} {'Entalpia (MOPAC)':<20}")
        print("-" * 52)
        
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
            
            print(f"{molecule.name:<20} {status:<12} {entalpia:<20}")

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
            
            # Mostra navegadores detectados
            browsers = self._detect_browsers()
            browsers_list = list(browsers.keys())
            if browsers_list:
                print(f"Navegadores detectados: {', '.join([b.title() for b in browsers_list])}")
            
            print("\nOpções:")
            print("1. Configurar credenciais do Supabase")
            print("2. Testar conexão com o Supabase")
            print("3. Sincronizar resultados existentes")
            print("4. Abrir o dashboard no navegador")
            print("5. Testar detecção de navegadores")
            print("6. Voltar ao menu principal")
            
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
                self._test_browser_detection()
            elif choice == "6":
                break
            else:
                print("Opção inválida. Tente novamente.")
    
    def _test_browser_detection(self):
        """Testa a detecção de navegadores e permite abrir uma URL de teste."""
        print("\n----- Teste de Detecção de Navegadores -----")
        
        browsers = self._detect_browsers()
        
        if browsers:
            print("Navegadores encontrados:")
            for browser, path in browsers.items():
                status = "✓ Funcional" if os.path.exists(path) else "✗ Não encontrado"
                print(f"  - {browser.title()}: {status}")
                print(f"    Caminho: {path}")
        else:
            print("Nenhum navegador encontrado nos caminhos padrão.")
        
        # Oferece teste com URL
        test_url = "https://www.google.com"
        if input(f"\nDeseja testar abrindo {test_url}? (s/n): ").lower() == 's':
            success = self._open_url_with_browser(test_url)
            if success:
                print("Teste realizado com sucesso!")
            else:
                print("Teste não pôde ser concluído.")
    
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
        
        # Salvar configurações automaticamente se mudanças foram feitas
        if any([
            hasattr(self, '_config_changed') and self._config_changed,
            enable,  # Se o usuário digitou algo
            url,     # Se o usuário digitou algo
            key,     # Se o usuário digitou algo
            storage  # Se o usuário digitou algo
        ]):
            self.settings.save_settings("config.yaml")
            print("Configurações do Supabase salvas automaticamente.")
            
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
                
                # Testa o Storage se estiver habilitado e verifica/cria o bucket
                if self.settings.supabase.storage_enabled:
                    bucket_name = self.settings.supabase.molecules_bucket
                    if self.supabase_service.ensure_bucket_exists(bucket_name):
                        print(f"Conexão com o Storage bem-sucedida! Bucket '{bucket_name}' está acessível.")
                    else:
                        print(f"Aviso: Não foi possível verificar ou criar o bucket '{bucket_name}'.")
                        print(f"Verifique suas permissões e se a chave API tem acesso para criar buckets.")
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
            # CORREÇÃO: Verificamos tanto o diretório final_molecules quanto repository
            output_dir = OUTPUT_DIR
            repository_crest_dir = CREST_DIR
            repository_mopac_dir = MOPAC_DIR
            
            if not output_dir.exists() and not repository_crest_dir.exists():
                print("Nenhum resultado encontrado. Execute a busca conformacional primeiro.")
                return
            
            # Verificamos os diretórios em final_molecules/output
            molecule_dirs_final = [d for d in output_dir.iterdir() if d.is_dir()] if output_dir.exists() else []
            
            # Verificamos os diretórios em repository/crest
            molecule_dirs_crest = [Path(repository_crest_dir) / d.name for d in repository_crest_dir.iterdir() 
                                 if d.is_dir()] if repository_crest_dir.exists() else []
            
            # Combinamos todas as moléculas encontradas (por nome)
            molecule_names = set([d.name for d in molecule_dirs_final])
            molecule_names.update([d.name for d in molecule_dirs_crest])
            
            if not molecule_names:
                print("Nenhum resultado encontrado. Execute a busca conformacional primeiro.")
                return
                
            molecule_names = sorted(list(molecule_names))
            print(f"Encontrados {len(molecule_names)} molécula(s) com resultados.")
            print("\nMoléculas disponíveis para sincronização:")
            
            for i, mol_name in enumerate(molecule_names, 1):
                print(f"{i}. {mol_name}")
            
            choice = input("\nSincronizar todas as moléculas (t) ou escolher quais sincronizar (e)? ")
            
            molecules_to_sync = []
            if choice.lower() == "t":
                molecules_to_sync = molecule_names
            elif choice.lower() == "e":
                indices = input("Digite os números das moléculas a sincronizar, separados por vírgula: ")
                try:
                    selected = [int(idx.strip()) - 1 for idx in indices.split(",")]
                    molecules_to_sync = [molecule_names[idx] for idx in selected if 0 <= idx < len(molecule_names)]
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
                    
                    # Configuramos os caminhos para os arquivos, verificando primeiro em repository
                    crest_dir = Path(repository_crest_dir) / mol_name
                    mopac_dir = Path(repository_mopac_dir) / mol_name
                    
                    # Verificar se os arquivos existem
                    crest_best_path = crest_dir / CREST_BEST_FILE
                    crest_conformers_path = crest_dir / CREST_CONFORMERS_FILE
                    crest_energies_path = crest_dir / CREST_ENERGIES_FILE
                    
                    if not crest_best_path.exists():
                        # Tenta encontrar no diretório final_molecules
                        alt_path = output_dir / mol_name / CREST_BEST_FILE
                        if alt_path.exists():
                            crest_best_path = alt_path
                        else:
                            logging.warning(f"Arquivo de conformer não encontrado para {mol_name}: {crest_best_path}")
                    
                    if not crest_conformers_path.exists():
                        # Tenta encontrar no diretório final_molecules
                        alt_path = output_dir / mol_name / CREST_CONFORMERS_FILE
                        if alt_path.exists():
                            crest_conformers_path = alt_path
                        else:
                            logging.warning(f"Arquivo de confôrmeros não encontrado para {mol_name}: {crest_conformers_path}")
                    
                    if not crest_energies_path.exists():
                        # Tenta encontrar no diretório final_molecules
                        alt_path = output_dir / mol_name / CREST_ENERGIES_FILE
                        if alt_path.exists():
                            crest_energies_path = alt_path
                        else:
                            logging.warning(f"Arquivo de energias não encontrado para {mol_name}: {crest_energies_path}")
                    
                    molecule.crest_best_path = str(crest_best_path)
                    molecule.crest_conformers_path = str(crest_conformers_path)
                    
                    # Verificamos e extraímos a entalpia se disponível
                    mopac_out_file = mopac_dir / f"{mol_name}.out"
                    if not mopac_out_file.exists():
                        # Tenta encontrar no diretório final_molecules
                        alt_path = output_dir / mol_name / f"{mol_name}.out"
                        if alt_path.exists():
                            mopac_out_file = alt_path
                            print(f"Arquivo MOPAC alternativo encontrado em {alt_path}")
                    
                    if mopac_out_file.exists():
                        # Use o método do CalculationService para extrair a entalpia
                        enthalpy, enthalpy_kj = self.calculation_service._extract_mopac_enthalpy(mopac_out_file)
                        if enthalpy is not None:
                            molecule.enthalpy_formation_mopac = enthalpy
                            molecule.enthalpy_formation_mopac_kj = enthalpy_kj
                            print(f"Entalpia extraída: {enthalpy} kcal/mol, {enthalpy_kj} kJ/mol")
                        else:
                            print(f"Não foi possível extrair a entalpia do arquivo {mopac_out_file}")
                    else:
                        print(f"Arquivo MOPAC não encontrado para {mol_name}")
                    
                    # Obtemos estatísticas dos confôrmeros
                    try:
                        conformer_stats = analyzer.get_conformer_statistics(mol_name)
                        if not conformer_stats or not conformer_stats.get("success", False):
                            print(f"Não foi possível obter estatísticas de confôrmeros para {mol_name}")
                    except Exception as e:
                        print(f"Erro ao analisar confôrmeros: {e}")
                        conformer_stats = {"success": False}
                    
                    # Upload para o Supabase
                    try:
                        molecule_id = self.supabase_service.upload_molecule(molecule)
                        
                        if not molecule_id:
                            print(f"Erro ao enviar molécula {mol_name} para o Supabase.")
                            failed += 1
                            continue
                    except Exception as e:
                        print(f"Erro ao fazer upload da molécula: {e}")
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
                        "best_conformer_path": str(crest_best_path) if crest_best_path.exists() else None,
                        "all_conformers_path": str(crest_conformers_path) if crest_conformers_path.exists() else None
                    }
                    
                    # Adiciona estatísticas do conformador se disponíveis
                    if conformer_stats and conformer_stats.get("success", False):
                        crest_results["energy_distribution"] = conformer_stats.get("relative_energies", [])
                        crest_results["relative_energies"] = conformer_stats.get("relative_energies", [])
                        crest_results["populations"] = conformer_stats.get("populations", [])
                    
                    try:
                        crest_success = self.supabase_service.upload_calculation_results(
                            molecule_id=molecule_id,
                            calculation_type="crest",
                            status="completed",
                            parameters=crest_params,
                            results=crest_results
                        )
                    except Exception as e:
                        print(f"Erro ao fazer upload dos resultados CREST: {e}")
                        crest_success = False
                    
                    # Upload de resultados MOPAC se disponíveis
                    mopac_success = True
                    if hasattr(molecule, "enthalpy_formation_mopac") and molecule.enthalpy_formation_mopac is not None:
                        mopac_params = {
                            "keywords": self.settings.mopac_keywords
                        }
                        
                        mopac_results = {
                            "enthalpy_formation": molecule.enthalpy_formation_mopac,
                            "enthalpy_formation_kj": getattr(molecule, 'enthalpy_formation_mopac_kj', None),
                            "method": self.settings.mopac_keywords.split()[0] if self.settings.mopac_keywords else None,
                            "output_path": str(mopac_out_file) if mopac_out_file.exists() else None
                        }
                        
                        try:
                            mopac_success = self.supabase_service.upload_calculation_results(
                                molecule_id=molecule_id,
                                calculation_type="mopac",
                                status="completed",
                                parameters=mopac_params,
                                results=mopac_results
                            )
                        except Exception as e:
                            print(f"Erro ao fazer upload dos resultados MOPAC: {e}")
                            mopac_success = False
                    
                    if crest_success and mopac_success:
                        print(f"✓ {mol_name} sincronizado com sucesso!")
                        successful += 1
                    else:
                        print(f"✗ Erro parcial ao sincronizar {mol_name}.")
                        failed += 1
                        
                except Exception as e:
                    print(f"✗ Erro ao sincronizar {mol_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    failed += 1
            
            print(f"\nSincronização concluída: {successful} sucesso(s), {failed} falha(s).")
            
        except Exception as e:
            print(f"Erro durante a sincronização: {e}")
            import traceback
            traceback.print_exc()    
    def _open_dashboard(self):
        """
        Abre o dashboard/interface do Supabase no navegador.
        
        O "dashboard" do projeto é o Table Editor nativo do Supabase onde os dados
        das moléculas são armazenados e podem ser visualizados. Também oferece acesso
        ao Storage para ver arquivos de moléculas.
        """
        if not self.settings.supabase.enabled:
            print("Supabase está desabilitado. Habilite-o primeiro.")
            return
        
        # Extrai o projeto ID da URL da API
        if not self.settings.supabase.url:
            print("URL da API do Supabase não configurada.")
            return
        
        try:
            # A URL da API é algo como: https://iyvvuguktlktwjwhoppf.supabase.co/rest/v1/
            # Precisamos extrair o projeto ID: iyvvuguktlktwjwhoppf
            parts = self.settings.supabase.url.split("/")
            if len(parts) >= 3:
                project_domain = parts[2]  # ex: iyvvuguktlktwjwhoppf.supabase.co
                project_id = project_domain.split('.')[0]  # ex: iyvvuguktlktwjwhoppf
                
                # Mostra opções para o usuário escolher qual página acessar
                print("\nOpções do Dashboard:")
                print("1. Dashboard principal (visão geral do projeto)")
                print("2. Table Editor (visualizar dados das moléculas)")
                print("3. Storage (visualizar arquivos de moléculas)")
                print("4. Cancelar")
                
                choice = input("\nEscolha uma opção: ")
                
                dashboard_url = None
                if choice == "1":
                    # Dashboard principal do projeto
                    dashboard_url = f"https://supabase.com/dashboard/project/{project_id}"
                    print(f"Preparando para abrir dashboard principal do Supabase...")
                    print(f"NOTA: Esta página requer login na sua conta Supabase")
                elif choice == "2":
                    # Table Editor diretamente
                    dashboard_url = f"https://supabase.com/dashboard/project/{project_id}/editor"
                    print(f"Preparando para abrir Table Editor do Supabase...")
                    print(f"Você verá as tabelas 'molecules', 'calculations', 'crest_results' e 'mopac_results'")
                    print(f"NOTA: Requer login na sua conta Supabase")
                elif choice == "3":
                    # Storage
                    dashboard_url = f"https://supabase.com/dashboard/project/{project_id}/storage/buckets"
                    print(f"Preparando para abrir Storage do Supabase...")
                    print(f"Procure pelo bucket '{self.settings.supabase.molecules_bucket}' para arquivos de moléculas")
                    print(f"NOTA: Requer login na sua conta Supabase")
                elif choice == "4":
                    print("Operação cancelada.")
                    return
                else:
                    print("Opção inválida.")
                    return
                
                if dashboard_url:
                    print(f"URL: {dashboard_url}")
                    print(f"Projeto ID: {project_id}")
                    
                    # Detecta navegadores e pergunta qual usar
                    browsers = self._detect_browsers()
                    
                    # Se Chrome está disponível, sugere usá-lo primeiro
                    if 'chrome' in browsers:
                        print(f"\n💡 DICA: Chrome detectado no sistema.")
                        print(f"Se sua conta Supabase está logada no Chrome, recomendamos usá-lo.")
                    
                    # Permite escolher o navegador
                    success = self._open_url_with_browser(dashboard_url)
                    
                    if success:
                        print("Dashboard aberto com sucesso!")
                    else:
                        print("Não foi possível abrir o dashboard automaticamente.")
                
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
