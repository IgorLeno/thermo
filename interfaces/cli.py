import argparse
from core.molecule import Molecule
from services.calculation_service import CalculationService
from services.file_service import FileService
from services.pubchem_service import PubChemService
from services.conversion_service import ConversionService
from config.settings import Settings
from typing import List
import logging

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
        self.parser = self._create_parser()
        self.molecules = []

    def _create_parser(self) -> argparse.ArgumentParser:
        """Cria o parser de argumentos de linha de comando."""
        parser = argparse.ArgumentParser(description="Programa para cálculo de entalpia de formação de moléculas orgânicas.")
        subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

        # Comando para calcular a entalpia de uma única molécula
        single_parser = subparsers.add_parser("1", help="Calcula a entalpia de uma molécula")
        single_parser.add_argument("molecule_name", type=str, help="Nome da molécula")

        # Comando para calcular a entalpia de várias moléculas
        multiple_parser = subparsers.add_parser("2", help="Calcula a entalpia de várias moléculas")
        multiple_parser.add_argument("molecule_names", type=str, nargs="*", help="Nomes das moléculas")
        multiple_parser.add_argument("-f", "--file", type=str, help="Arquivo com a lista de moléculas")

        # Comando para editar configurações
        config_parser = subparsers.add_parser("3", help="Editar configurações")
        config_parser.add_argument("-t", "--threads", type=int, help="Número de threads")
        config_parser.add_argument("-m", "--method", type=str, help="Método do CREST (gfn1, gfn2, gfnff)")
        config_parser.add_argument("-ob", "--openbabel", type=str, help="Caminho do OpenBabel")
        config_parser.add_argument("-c", "--crest", type=str, help="Caminho do CREST")
        config_parser.add_argument("-x", "--xtb", type=str, help="Caminho do xTB")
        config_parser.add_argument("-et", "--etemp", type=float, help="Temperatura eletrônica (em Kelvin)")
        config_parser.add_argument("-s", "--solvent", type=str, help="Solvente")
        config_parser.add_argument("--save", type=str, help="Salvar configurações em um arquivo")

        # Comando para exibir resultados
        result_parser = subparsers.add_parser("4", help="Exibe os resultados dos cálculos realizados.")
        result_parser.add_argument("-g", "--generate_summary", type=str, help="Gera um arquivo de resumo.")

        return parser

    def run(self):
        """Analisa os argumentos de linha de comando e executa a ação apropriada."""
        print("\nMenu Principal:")
        print("1. Calcular a entalpia de uma molécula")
        print("2. Calcular a entalpia para várias moléculas")
        print("3. Editar configurações")
        print("4. Exibir resultados")
        print("5. Sair")

        choice = input("Escolha uma opção: ")

        # Mapeia a escolha do usuário para o nome do comando correspondente
        command_map = {
            "1": "single",
            "2": "multiple",
            "3": "config",
            "4": "results",
            "5": "exit"
        }

        command = command_map.get(choice)

        if command == "exit":
            print("Saindo do programa...")
            return

        if command:
            # Passa argumentos fictícios para simular a estrutura original
            args = self.parser.parse_args([command, "dummy"] if command in ["single", "multiple", "config", "results"] else [command])
            
            if command == "single":
                molecule_name = input("Digite o nome da molécula: ")
                self.calculate_single_molecule(molecule_name)
            elif command == "multiple":
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
                self.calculate_multiple_molecules(molecule_names)

            elif command == "config":
                self.edit_settings(args)
            elif command == "results":
                self.show_results(args.generate_summary if hasattr(args, 'generate_summary') else None)
        else:
            print("Opção inválida.")

    def calculate_single_molecule(self, molecule_name: str):
        """
        Calcula a entalpia de uma única molécula.
        """
        molecule = Molecule(name=molecule_name)
        self.process_molecule(molecule)

    def calculate_multiple_molecules(self, molecule_names: List[str], filepath: str = None):
        """
        Calcula a entalpia de várias moléculas.
        """
        if filepath:
            try:
                with open(filepath, "r") as f:
                    molecule_names = [line.strip() for line in f]
            except FileNotFoundError:
                print(f"Arquivo não encontrado: {filepath}")
                return
        elif not molecule_names:
            print("Erro: É necessário fornecer os nomes das moléculas ou um arquivo com a lista.")
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

    def edit_settings(self, args):
        """
        Edita as configurações com base nos argumentos fornecidos.
        """
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

    def show_results(self, generate_summary:str = None):
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
        if generate_summary:
            if not generate_summary.endswith(".txt"):
                generate_summary += ".txt"
            self.file_service.generate_summary(self.molecules, generate_summary)
            print(f"Arquivo de resumo gerado: {generate_summary}")