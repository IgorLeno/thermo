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
from typing import List
from pathlib import Path
import logging
import os
import sys
import time

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

    def run(self):
        """Exibe o menu principal e aguarda a escolha do usuário."""
        print("\n==================================================")
        print("  Busca Conformacional e Cálculo de Entalpia      ")
        print("  (CREST + MOPAC)                                 ")
        print("==================================================")
        
        while True:
            print("\nMenu Principal:")
            print("1. Realizar cálculo completo para uma molécula")
            print("2. Realizar cálculo completo para várias moléculas")
            print("3. Editar configurações")
            print("4. Exibir resultados")
            print("5. Analisar resultados")
            print("6. Sair")

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

            # Verifica os resultados no diretório final
            final_dir = OUTPUT_DIR / molecule.name
            
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
            crest_dir = CREST_DIR / molecule.name
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
            
            # Arquivos do MOPAC
            mopac_dir = MOPAC_DIR / molecule.name
            pdb_file = PDB_DIR / f"{molecule.name}.pdb"
            
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