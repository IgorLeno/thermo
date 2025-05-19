from services.calculation_service import CalculationService
from services.file_service import FileService
from services.pubchem_service import PubChemService
from services.conversion_service import ConversionService
from services.chemperium import ChemperiumService
from config.settings import Settings
from core.molecule import Molecule
import os
import logging

class Menu:
    """
    Classe que implementa o menu interativo do programa.
    """
    def __init__(self, settings: Settings, file_service: FileService, pubchem_service: PubChemService, 
                 conversion_service: ConversionService, calculation_service: CalculationService):
        self.settings = settings
        self.file_service = file_service
        self.pubchem_service = pubchem_service
        self.conversion_service = conversion_service
        self.calculation_service = calculation_service
        self.chemperium_service = ChemperiumService(settings.config)
        self.molecules = []  # Lista para armazenar as moléculas processadas

    def run(self):
        """Exibe o menu principal e aguarda a escolha do usuário."""
        while True:
            print("\nMenu Principal:")
            print("1. Cálculo tradicional (CREST + MOPAC)")
            print("2. Cálculo com Chemperium (CREST + MOPAC + Chemperium)")
            print("3. Só Chemperium (rápido, sem CREST)")
            print("4. Múltiplas moléculas com Chemperium")
            print("5. Editar configurações")
            print("6. Resultados")
            print("7. Sair")

            choice = input("Escolha uma opção: ")

            if choice == "1":
                self.calculate_single_molecule_traditional()
            elif choice == "2":
                self.calculate_single_molecule_with_chemperium()
            elif choice == "3":
                self.calculate_single_molecule_chemperium_only()
            elif choice == "4":
                self.calculate_multiple_molecules_chemperium()
            elif choice == "5":
                self.edit_settings()
            elif choice == "6":
                self.show_results()
            elif choice == "7":
                print("Saindo do programa...")
                break
            else:
                print("Opção inválida. Tente novamente.")

    def calculate_single_molecule_traditional(self):
        """
        Solicita o nome da molécula ao usuário e realiza busca conformacional tradicional.
        """
        molecule_name = input("Digite o nome da molécula: ")
        molecule = Molecule(name=molecule_name)
        self.process_molecule_traditional(molecule)

    def calculate_single_molecule_with_chemperium(self):
        """
        Realiza busca conformacional tradicional seguida de cálculo Chemperium.
        """
        if not self.chemperium_service.is_available():
            print("Chemperium não está disponível. Verifique a instalação.")
            return
            
        molecule_name = input("Digite o nome da molécula: ")
        molecule = Molecule(name=molecule_name)
        self.process_molecule_with_chemperium(molecule)

    def calculate_single_molecule_chemperium_only(self):
        """
        Realiza cálculo apenas com Chemperium (sem CREST).
        """
        if not self.chemperium_service.is_available():
            print("Chemperium não está disponível. Verifique a instalação.")
            return
            
        molecule_name = input("Digite o nome da molécula: ")
        molecule = Molecule(name=molecule_name)
        self.process_molecule_chemperium_only(molecule)

    def calculate_multiple_molecules_chemperium(self):
        """
        Realiza cálculo em lote com Chemperium.
        """
        if not self.chemperium_service.is_available():
            print("Chemperium não está disponível. Verifique a instalação.")
            return
            
        print("Opções para múltiplas moléculas:")
        print("1. CREST + MOPAC + Chemperium")
        print("2. Apenas Chemperium (rápido)")
        
        method_choice = input("Escolha o método: ")
        
        # Obter lista de moléculas
        input_method = input("Deseja digitar os nomes das moléculas (1) ou fornecer um arquivo com a lista (2)? ")
        if input_method == "1":
            molecule_names = input("Digite os nomes das moléculas separados por vírgula: ").split(",")
            molecule_names = [name.strip() for name in molecule_names]
        elif input_method == "2":
            filepath = input("Digite o caminho do arquivo (cada linha deve conter um nome de molécula): ")
            try:
                with open(filepath, "r") as f:
                    molecule_names = [line.strip() for line in f]
            except FileNotFoundError:
                print(f"Arquivo não encontrado: {filepath}")
                return
        else:
            print("Opção inválida.")
            return

        # Processar cada molécula
        for name in molecule_names:
            molecule = Molecule(name=name)
            if method_choice == "1":
                self.process_molecule_with_chemperium(molecule)
            elif method_choice == "2":
                self.process_molecule_chemperium_only(molecule)
            else:
                print("Método inválido. Usando apenas Chemperium.")
                self.process_molecule_chemperium_only(molecule)

    def process_molecule_traditional(self, molecule: Molecule):
        """
        Processa uma molécula usando o método tradicional (CREST + MOPAC).
        """
        try:
            # Baixa o SDF do PubChem
            sdf_path, cid = self.pubchem_service.get_sdf_by_name(molecule.name)
            if sdf_path is None:
                return  # Pula para a próxima molécula se o SDF não for encontrado
            molecule.sdf_path = sdf_path
            molecule.pubchem_cid = cid

            # Converte o SDF para XYZ
            self.conversion_service.sdf_to_xyz(molecule)

            # Executa a busca conformacional
            self.calculation_service.run_calculation(molecule)
            self.molecules.append(molecule)

            print(f"Busca conformacional concluída para {molecule.name}.")
            if molecule.crest_best_path and os.path.exists(molecule.crest_best_path):
                print(f"Melhor confôrmero encontrado: {molecule.crest_best_path}")
            if molecule.crest_conformers_path and os.path.exists(molecule.crest_conformers_path):
                print(f"Arquivo de confôrmeros: {molecule.crest_conformers_path}")

        except Exception as e:
            logging.error(f"Erro ao processar a molécula {molecule.name}: {e}")
            print(f"Erro ao processar a molécula {molecule.name}. Veja o log para mais detalhes.")

    def process_molecule_with_chemperium(self, molecule: Molecule):
        """
        Processa uma molécula usando CREST + MOPAC + Chemperium.
        """
        try:
            from services.chemperium.chemperium_service import kcal_to_kj
            
            # Parte 1: Fluxo tradicional (CREST + MOPAC)
            print(f"[{molecule.name}] Iniciando fluxo tradicional...")
            
            # Obter SMILES do PubChem
            smiles = self.pubchem_service.get_smiles_by_name(molecule.name)
            if not smiles:
                print(f"Não foi possível obter SMILES para {molecule.name}")
                return
            molecule.smiles = smiles
            
            # Baixa o SDF do PubChem
            sdf_path, cid = self.pubchem_service.get_sdf_by_name(molecule.name)
            if sdf_path is None:
                return
            molecule.sdf_path = sdf_path
            molecule.pubchem_cid = cid

            # Converte o SDF para XYZ
            self.conversion_service.sdf_to_xyz(molecule)

            # Executa busca conformacional e MOPAC
            self.calculation_service.run_calculation(molecule)
            
            # Verifica se MOPAC foi executado
            if not hasattr(molecule, 'enthalpy_kj_mol') or molecule.enthalpy_kj_mol is None:
                print(f"MOPAC não retornou entalpia válida para {molecule.name}")
                return

            # Parte 2: Chemperium
            print(f"[{molecule.name}] Iniciando cálculo Chemperium...")
            
            # Ler coordenadas do melhor confôrmero
            best_xyz_content = None
            if molecule.crest_best_path and os.path.exists(molecule.crest_best_path):
                with open(molecule.crest_best_path, 'r') as f:
                    best_xyz_content = f.read()
            elif molecule.xyz_path and os.path.exists(molecule.xyz_path):
                with open(molecule.xyz_path, 'r') as f:
                    best_xyz_content = f.read()
            else:
                print(f"Não foi possível encontrar coordenadas XYZ para {molecule.name}")
                return
            
            # Converter entalpia MOPAC para kcal/mol (LLOT)
            llot_kcal = molecule.enthalpy_kj_mol / 4.184  # kJ/mol -> kcal/mol
            
            # Executar Chemperium
            enthalpy_chemp_kcal, uncertainty_kcal = self.chemperium_service.predict_enthalpy_with_llot(
                smiles=molecule.smiles,
                xyz_content=best_xyz_content,
                llot_enthalpy=llot_kcal
            )
            
            # Converter para kJ/mol e armazenar
            molecule.enthalpy_chemperium_kj_mol = enthalpy_chemp_kcal * 4.184
            molecule.enthalpy_chemperium_uncertainty_kj_mol = uncertainty_kcal * 4.184
            
            # Exibir resultados
            print(f"\n=== Resultados para {molecule.name} ===")
            print(f"MOPAC:      {molecule.enthalpy_kj_mol:.2f} kJ/mol")
            print(f"Chemperium: {molecule.enthalpy_chemperium_kj_mol:.2f} ± {molecule.enthalpy_chemperium_uncertainty_kj_mol:.2f} kJ/mol")
            print(f"Diferença:  {molecule.enthalpy_chemperium_kj_mol - molecule.enthalpy_kj_mol:.2f} kJ/mol")
            
            self.molecules.append(molecule)

        except Exception as e:
            logging.error(f"Erro ao processar a molécula {molecule.name} com Chemperium: {e}")
            print(f"Erro ao processar a molécula {molecule.name}. Veja o log para mais detalhes.")

    def process_molecule_chemperium_only(self, molecule: Molecule):
        """
        Processa uma molécula usando apenas Chemperium (sem CREST).
        """
        try:
            print(f"[{molecule.name}] Calculando apenas com Chemperium...")
            
            # Obter SMILES do PubChem
            smiles = self.pubchem_service.get_smiles_by_name(molecule.name)
            if not smiles:
                print(f"Não foi possível obter SMILES para {molecule.name}")
                return
            molecule.smiles = smiles
            
            # Baixa o SDF e converte para XYZ
            sdf_path, cid = self.pubchem_service.get_sdf_by_name(molecule.name)
            if sdf_path is None:
                return
            molecule.sdf_path = sdf_path
            molecule.pubchem_cid = cid

            # Converte o SDF para XYZ
            self.conversion_service.sdf_to_xyz(molecule)
            
            # Ler coordenadas XYZ
            xyz_content = None
            if molecule.xyz_path and os.path.exists(molecule.xyz_path):
                with open(molecule.xyz_path, 'r') as f:
                    xyz_content = f.read()
            else:
                print(f"Não foi possível encontrar coordenadas XYZ para {molecule.name}")
                return
            
            # Executar Chemperium standalone
            enthalpy_chemp_kcal, uncertainty_kcal = self.chemperium_service.predict_enthalpy_standalone(
                smiles=molecule.smiles,
                xyz_content=xyz_content
            )
            
            # Converter para kJ/mol e armazenar
            molecule.enthalpy_chemperium_kj_mol = enthalpy_chemp_kcal * 4.184
            molecule.enthalpy_chemperium_uncertainty_kj_mol = uncertainty_kcal * 4.184
            
            # Marcar que não foi usado MOPAC
            molecule.enthalpy_kj_mol = None
            
            # Exibir resultados
            print(f"\n=== Resultados para {molecule.name} ===")
            print(f"Chemperium: {molecule.enthalpy_chemperium_kj_mol:.2f} ± {molecule.enthalpy_chemperium_uncertainty_kj_mol:.2f} kJ/mol")
            
            self.molecules.append(molecule)

        except Exception as e:
            logging.error(f"Erro ao processar a molécula {molecule.name} com Chemperium: {e}")
            print(f"Erro ao processar a molécula {molecule.name}. Veja o log para mais detalhes.")

    def edit_settings(self):
        """Permite ao usuário visualizar e modificar as configurações."""
        while True:
            print("\nConfigurações Atuais:")
            print(f"1. Número de threads: {self.settings.calculation_params.n_threads}")
            print(f"2. Método do CREST: {self.settings.calculation_params.crest_method}")
            print(f"3. Caminho do OpenBabel: {self.settings.openbabel_path}")
            print(f"4. Caminho do CREST: {self.settings.crest_path}")
            print(f"5. Temperatura eletrônica (Kelvin): {self.settings.calculation_params.electronic_temperature}")
            print(f"6. Solvente: {self.settings.calculation_params.solvent}")
            
            # Configurações Chemperium
            chemperium_config = self.settings.config.get('chemperium', {})
            print(f"7. Chemperium habilitado: {chemperium_config.get('enabled', True)}")
            print(f"8. Método Chemperium: {chemperium_config.get('method', 'cbs-qb3')}")
            print(f"9. Dimensão Chemperium: {chemperium_config.get('dimension', '3d')}")
            
            print("10. Salvar configurações")
            print("11. Voltar ao menu principal")

            choice = input("Escolha uma opção para editar: ")

            if choice == "1":
                self.settings.calculation_params.n_threads = int(input("Digite o novo número de threads: "))
            elif choice == "2":
                self.settings.calculation_params.crest_method = input("Digite o novo método do CREST (gfn1, gfn2, gfnff): ")
            elif choice == "3":
                self.settings.openbabel_path = input("Digite o novo caminho do OpenBabel: ")
            elif choice == "4":
                self.settings.crest_path = input("Digite o novo caminho do CREST: ")
            elif choice == "5":
                self.settings.calculation_params.electronic_temperature = float(input("Digite a nova temperatura eletrônica (em Kelvin): "))
            elif choice == "6":
                self.settings.calculation_params.solvent = input("Digite o nome do solvente (ou deixe em branco para nenhum): ")
            elif choice == "7":
                enabled = input("Habilitar Chemperium? (s/n): ").lower() == 's'
                if 'chemperium' not in self.settings.config:
                    self.settings.config['chemperium'] = {}
                self.settings.config['chemperium']['enabled'] = enabled
                self.chemperium_service.enabled = enabled
            elif choice == "8":
                print("Métodos disponíveis: g3mp2b3 (rápido), cbs-qb3 (preciso)")
                method = input("Digite o método Chemperium: ")
                if method in ['g3mp2b3', 'cbs-qb3']:
                    if 'chemperium' not in self.settings.config:
                        self.settings.config['chemperium'] = {}
                    self.settings.config['chemperium']['method'] = method
                    self.chemperium_service.method = method
                else:
                    print("Método inválido. Use 'g3mp2b3' ou 'cbs-qb3'.")
            elif choice == "9":
                dimension = input("Digite a dimensão (2d/3d): ")
                if dimension in ['2d', '3d']:
                    if 'chemperium' not in self.settings.config:
                        self.settings.config['chemperium'] = {}
                    self.settings.config['chemperium']['dimension'] = dimension
                    self.chemperium_service.dimension = dimension
                else:
                    print("Dimensão inválida. Use '2d' ou '3d'.")
            elif choice == "10":
                filepath = input("Digite o caminho para salvar o arquivo de configuração: ")
                self.settings.save_settings(filepath)
                print("Configurações salvas com sucesso.")
            elif choice == "11":
                break
            else:
                print("Opção inválida.")

    def show_results(self):
        """Exibe os resultados das buscas conformacionais realizadas."""
        if not self.molecules:
            print("Nenhuma busca conformacional foi realizada ainda.")
            return

        print("\nResultados:")
        print(f"{'Molécula':<20} {'CID':<10} {'MOPAC (kJ/mol)':<15} {'Chemperium (kJ/mol)':<20} {'Arquivo Confôrmeros':<30}")
        print("-" * 120)
        
        for molecule in self.molecules:
            conf_path = os.path.basename(molecule.crest_conformers_path) if hasattr(molecule, 'crest_conformers_path') and molecule.crest_conformers_path else "N/A"
            
            # Formatação das entalpias
            mopac_str = f"{molecule.enthalpy_kj_mol:.2f}" if hasattr(molecule, 'enthalpy_kj_mol') and molecule.enthalpy_kj_mol is not None else "N/A"
            
            if hasattr(molecule, 'enthalpy_chemperium_kj_mol') and molecule.enthalpy_chemperium_kj_mol is not None:
                chemp_str = f"{molecule.enthalpy_chemperium_kj_mol:.2f} ± {molecule.enthalpy_chemperium_uncertainty_kj_mol:.2f}"
            else:
                chemp_str = "N/A"
            
            print(f"{molecule.name:<20} {str(molecule.pubchem_cid):<10} {mopac_str:<15} {chemp_str:<20} {conf_path:<30}")

        # Opção para gerar um arquivo de resumo
        if input("Deseja gerar um arquivo de resumo (s/n)? ").lower() == "s":
            output_file = input("Digite o nome do arquivo de resumo: ")
            if not output_file.endswith(".txt"):
                output_file += ".txt"
            self.file_service.generate_summary(self.molecules, output_file)
            print(f"Arquivo de resumo gerado: {output_file}")