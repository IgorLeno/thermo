from services.calculation_service import CalculationService
from services.file_service import FileService
from services.pubchem_service import PubChemService
from services.conversion_service import ConversionService
from config.settings import Settings
from core.molecule import Molecule
import os
import logging

class Menu:
    """
    Classe que implementa o menu interativo do programa.
    """
    def __init__(self, settings: Settings, file_service: FileService, pubchem_service: PubChemService, conversion_service: ConversionService, calculation_service: CalculationService):
        self.settings = settings
        self.file_service = file_service
        self.pubchem_service = pubchem_service
        self.conversion_service = conversion_service
        self.calculation_service = calculation_service
        self.molecules = []  # Lista para armazenar as moléculas processadas

    def run(self):
        """Exibe o menu principal e aguarda a escolha do usuário."""
        while True:
            print("\nMenu Principal:")
            print("1. Calcular a entalpia de uma molécula")
            print("2. Calcular a entalpia para várias moléculas")
            print("3. Editar configurações")
            print("4. Resultados")
            print("5. Sair")

            choice = input("Escolha uma opção: ")

            if choice == "1":
                self.calculate_single_molecule()
            elif choice == "2":
                self.calculate_multiple_molecules()
            elif choice == "3":
                self.edit_settings()
            elif choice == "4":
                self.show_results()
            elif choice == "5":
                print("Saindo do programa...")
                break
            else:
                print("Opção inválida. Tente novamente.")

    def calculate_single_molecule(self):
        """
        Solicita o nome da molécula ao usuário e realiza os cálculos.
        """
        molecule_name = input("Digite o nome da molécula: ")
        molecule = Molecule(name=molecule_name)
        self.process_molecule(molecule)

    def calculate_multiple_molecules(self):
        """
        Solicita uma lista de nomes de moléculas ou um arquivo e realiza os cálculos.
        """
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

        for name in molecule_names:
            molecule = Molecule(name=name)
            self.process_molecule(molecule)

    def process_molecule(self, molecule: Molecule):
        """
        Processa uma molécula, realizando os cálculos e armazenando os resultados.
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

            # Executa os cálculos
            self.calculation_service.run_calculation(molecule)
            self.molecules.append(molecule)

            print(f"Cálculos concluídos para {molecule.name}. Entalpia de formação: {molecule.formation_enthalpy:.2f} kcal/mol")

        except Exception as e:
            logging.error(f"Erro ao processar a molécula {molecule.name}: {e}")
            print(f"Erro ao processar a molécula {molecule.name}. Veja o log para mais detalhes.")

    def edit_settings(self):
        """Permite ao usuário visualizar e modificar as configurações."""
        while True:
            print("\nConfigurações Atuais:")
            print(f"1. Número de threads: {self.settings.calculation_params.n_threads}")
            print(f"2. Método do CREST: {self.settings.calculation_params.crest_method}")
            print(f"3. Caminho do OpenBabel: {self.settings.openbabel_path}")
            print(f"4. Caminho do CREST: {self.settings.crest_path}")
            print(f"5. Caminho do xTB: {self.settings.xtb_path}")
            print(f"6. Temperatura eletrônica (Kelvin): {self.settings.calculation_params.electronic_temperature}")
            print(f"7. Solvente: {self.settings.calculation_params.solvent}")
            print("8. Salvar configurações")
            print("9. Voltar ao menu principal")

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
                self.settings.xtb_path = input("Digite o novo caminho do xTB: ")
            elif choice == "6":
                self.settings.calculation_params.electronic_temperature = float(input("Digite a nova temperatura eletrônica (em Kelvin): "))
            elif choice == "7":
                self.settings.calculation_params.solvent = input("Digite o nome do solvente (ou deixe em branco para nenhum): ")
            elif choice == "8":
                filepath = input("Digite o caminho para salvar o arquivo de configuração: ")
                self.settings.save_settings(filepath)
                print("Configurações salvas com sucesso.")
            elif choice == "9":
                break
            else:
                print("Opção inválida.")

    def show_results(self):
        """Exibe os resultados dos cálculos realizados."""
        if not self.molecules:
            print("Nenhum cálculo foi realizado ainda.")
            return

        print("\nResultados:")
        print(f"{'Molécula':<20} {'CID':<10} {'Entalpia de Formação (kcal/mol)':<35} {'Erros':<20}")
        print("-" * 95)
        for molecule in self.molecules:
            enthalpy_str = f"{molecule.formation_enthalpy:.2f}" if molecule.formation_enthalpy is not None else "N/A"
            print(f"{molecule.name:<20} {str(molecule.pubchem_cid):<10} {enthalpy_str:<35}")

        # Opção para gerar um arquivo de resumo
        if input("Deseja gerar um arquivo de resumo (s/n)? ").lower() == "s":
            output_file = input("Digite o nome do arquivo de resumo: ")
            if not output_file.endswith(".txt"):
                output_file += ".txt"
            self.file_service.generate_summary(self.molecules, output_file)
            print(f"Arquivo de resumo gerado: {output_file}")