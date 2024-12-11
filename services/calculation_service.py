# services/calculation_service.py

import subprocess
import os
import re
from core.molecule import Molecule
from core.calculation import CalculationParameters
from config.settings import Settings
from services.file_service import FileService
from services.conversion_service import ConversionService
from config.constants import *
import logging

class CalculationService:
    """
    Classe que gerencia a execução dos cálculos com CREST e xTB.
    """
    def __init__(self, settings: Settings, file_service: FileService, conversion_service: ConversionService):
        self.settings = settings
        self.file_service = file_service
        self.conversion_service = conversion_service

    def run_crest(self, molecule: Molecule):
        """
        Executa o CREST para busca conformacional usando WSL.
        """
        
        xyz_path = molecule.xyz_path
        if not os.path.exists(xyz_path):
            raise FileNotFoundError(f"Arquivo XYZ não encontrado: {xyz_path}")

        # Cria o diretório de saída do CREST
        output_dir = CREST_DIR / molecule.name
        os.makedirs(output_dir, exist_ok=True)

        # Define o caminho do arquivo de log do CREST
        crest_log_file = output_dir / "crest.log"

        # Monta o comando do CREST para execução via WSL
        crest_path = self.settings.crest_path
        command = ["wsl", crest_path] + self.settings.calculation_params.crest_command(xyz_path)

        # Executa o CREST via WSL e captura a saída e erros
        try:
            with open(crest_log_file, "w") as log_file:
                process = subprocess.Popen(command, cwd=output_dir, stdout=log_file, stderr=subprocess.PIPE, text=True)
                _, stderr = process.communicate()

            # Verifica se houve erros na execução do CREST
            if process.returncode != 0:
                logging.error(f"Erro ao executar o CREST para a molécula {molecule.name}.")
                if stderr:
                    logging.error(stderr)
                raise RuntimeError(f"Erro ao executar o CREST para a molécula {molecule.name}. Veja o log para mais detalhes: {crest_log_file}")

            # Define os caminhos dos arquivos de saída do CREST
            molecule.crest_conformers_path = str(output_dir / CREST_CONFORMERS_FILE)
            molecule.crest_best_path = str(output_dir / CREST_BEST_FILE)

            logging.info(f"Busca conformacional com CREST concluída para {molecule.name}.")

        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            logging.error(f"Erro ao executar o CREST para a molécula {molecule.name}: {e}")
            raise

        # Extrai as energias dos confôrmeros do arquivo crest.energies, se existir
        crest_energies_file = output_dir / "crest.energies"
        if os.path.exists(crest_energies_file):
            try:
                with open(crest_energies_file, "r") as f:
                    for line in f:
                        match = re.search(r"TOTAL ENERGY\s+=\s+(-?\d+\.\d+)", line)
                        if match:
                            energy = float(match.group(1))
                            molecule.conformer_energies.append(energy)
                logging.info(f"Energias dos confôrmeros extraídas com sucesso para {molecule.name}.")
            except Exception as e:
                logging.warning(f"Não foi possível extrair as energias dos confôrmeros para {molecule.name}: {e}")

    def run_xtb_opt(self, molecule: Molecule):
        """
        Executa o xTB para otimização de geometria.
        """
        if not molecule.crest_best_path:
            raise ValueError("Caminho do arquivo crest_best.xyz não definido.")

        crest_best_path = Path(molecule.crest_best_path)
        if not crest_best_path.exists():
            raise FileNotFoundError(f"Arquivo de melhor confôrmero do CREST não encontrado: {molecule.crest_best_path}")

        # Cria o diretório de saída do xTB
        output_dir = XTB_DIR / molecule.name
        os.makedirs(output_dir, exist_ok=True)
        
        # Define o caminho do arquivo de log do xTB
        xtb_log_file = output_dir / "xtb_opt.log"

        # Monta o comando do xTB para otimização
        command = self.settings.calculation_params.xtb_command(str(crest_best_path), "opt")
        command.insert(0, self.settings.xtb_path)

        # Executa o xTB e captura a saída e erros
        try:
            with open(xtb_log_file, "w") as log_file:
                process = subprocess.Popen(command, cwd=output_dir, stdout=log_file, stderr=subprocess.PIPE, text=True)
                _, stderr = process.communicate()

            # Verifica se houve erros na execução do xTB
            if process.returncode != 0:
                logging.error(f"Erro ao executar a otimização com xTB para a molécula {molecule.name}.")
                if stderr:
                    logging.error(stderr)
                raise RuntimeError(f"Erro ao executar a otimização com xTB para a molécula {molecule.name}. Veja o log para mais detalhes: {xtb_log_file}")

            # Define o caminho do arquivo de saída da otimização
            molecule.xtb_opt_path = str(output_dir / XTBOPT_FILE)

            logging.info(f"Otimização de geometria com xTB concluída para {molecule.name}.")

        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            logging.error(f"Erro ao executar a otimização com xTB para a molécula {molecule.name}: {e}")
            raise

    def run_xtb_hess(self, molecule: Molecule):
        """
        Executa o xTB para cálculo da Hessiana e frequências vibracionais.
        """
        if not molecule.xtb_opt_path:
            raise ValueError("Caminho do arquivo xtbopt.xyz não definido.")

        xtb_opt_path = Path(molecule.xtb_opt_path)
        if not xtb_opt_path.exists():
            raise FileNotFoundError(f"Arquivo de geometria otimizada do xTB não encontrado: {molecule.xtb_opt_path}")

        # Cria o diretório de saída do xTB
        output_dir = XTB_DIR / molecule.name
        os.makedirs(output_dir, exist_ok=True)

        # Define o caminho do arquivo de log do xTB
        xtb_log_file = output_dir / "xtb_hess.log"

        # Monta o comando do xTB para cálculo da Hessiana
        command = self.settings.calculation_params.xtb_command(str(xtb_opt_path), "hess")
        command.insert(0, self.settings.xtb_path)

        # Executa o xTB e captura a saída e erros
        try:
            with open(xtb_log_file, "w") as log_file:
                process = subprocess.Popen(command, cwd=output_dir, stdout=log_file, stderr=subprocess.PIPE, text=True)
                _, stderr = process.communicate()

            # Verifica se houve erros na execução do xTB
            if process.returncode != 0:
                logging.error(f"Erro ao executar o cálculo da Hessiana com xTB para a molécula {molecule.name}.")
                if stderr:
                    logging.error(stderr)
                raise RuntimeError(f"Erro ao executar o cálculo da Hessiana com xTB para a molécula {molecule.name}. Veja o log para mais detalhes: {xtb_log_file}")

            # Define os caminhos dos arquivos de saída do cálculo da Hessiana
            molecule.hessian_path = str(output_dir / HESSIAN_FILE)
            molecule.vibspectrum_path = str(output_dir / VIB_SPECTRUM_FILE)
            molecule.thermochemistry_path = str(output_dir / THERMOCHEMISTRY_FILE)

            logging.info(f"Cálculo da Hessiana e frequências vibracionais com xTB concluído para {molecule.name}.")

        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            logging.error(f"Erro ao executar o cálculo da Hessiana com xTB para a molécula {molecule.name}: {e}")
            raise

    def extract_formation_enthalpy(self, molecule: Molecule):
        """
        Extrai a entalpia de formação do arquivo de saída do xTB (xtbhess.log ou thermochemistry).
        """
        if not molecule.thermochemistry_path:
            logging.warning(f"O caminho do arquivo de termoquímica não está definido para a molécula {molecule.name}. Não foi possível extrair a entalpia de formação.")
            return
        
        thermochemistry_path = Path(molecule.thermochemistry_path)
        if not thermochemistry_path.exists():
            logging.warning(f"Arquivo de termoquímica do xTB não encontrado: {molecule.thermochemistry_path}. Não foi possível extrair a entalpia de formação.")
            return

        try:
            with open(thermochemistry_path, "r") as f:
                content = f.read()

            # Expressão regular para encontrar a entalpia de formação
            match = re.search(r"formation enthalpy\s+([\w-]+[\w]+)\s+([\d.-]+)\s+([\d.-]+)", content)

            if match:
                unit, value, _ = match.groups()  # Captura a unidade, o valor e a linha (não utilizada)
                formation_enthalpy_au = float(value)  # Converte o valor para float
                logging.info(f"Entalpia de formação extraída para {molecule.name}: {formation_enthalpy_au} {unit}")

                # Converte de Hartree para kcal/mol (1 Hartree = 627.509 kcal/mol)
                if unit == "Eh":
                    formation_enthalpy_kcal_mol = formation_enthalpy_au * 627.509
                else:
                    formation_enthalpy_kcal_mol = formation_enthalpy_au
                molecule.formation_enthalpy = formation_enthalpy_kcal_mol

            else:
                logging.warning(f"Não foi possível encontrar a entalpia de formação no arquivo {thermochemistry_path} para a molécula {molecule.name}.")
                molecule.formation_enthalpy = None

        except Exception as e:
            logging.error(f"Erro ao extrair a entalpia de formação para {molecule.name}: {e}")
            molecule.formation_enthalpy = None

    def run_calculation(self, molecule: Molecule):
        """
        Executa o fluxo completo de cálculo para uma molécula: CREST, otimização xTB e Hessiana xTB.
        """
        try:
            self.run_crest(molecule)
            self.run_xtb_opt(molecule)
            self.run_xtb_hess(molecule)
            self.extract_formation_enthalpy(molecule)

            # Move os arquivos de saída para o diretório final
            self.file_service.move_output_files(molecule)

        except Exception as e:
            logging.error(f"Erro durante o cálculo para a molécula {molecule.name}: {e}")
            print(f"Erro durante o cálculo para a molécula {molecule.name}. Veja o arquivo de log para mais detalhes.")