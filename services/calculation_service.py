import re
import shlex
import subprocess
import os
from pathlib import Path
import logging
from core.molecule import Molecule
from config.settings import Settings
from services.file_service import FileService
from services.conversion_service import ConversionService
from config.constants import *

class CalculationService:
    def __init__(self, settings: Settings, file_service: FileService, conversion_service: ConversionService):
        self.settings = settings
        self.file_service = file_service
        self.conversion_service = conversion_service

    def run_crest(self, molecule: Molecule):
        """
        Executa o CREST para busca conformacional diretamente no ambiente conda no WSL.
        O arquivo XYZ é copiado para o diretório do CREST no ambiente conda, o cálculo é executado lá,
        e depois todos os arquivos são movidos para o diretório de saída.
        """
        logging.info(f"Iniciando a execução do CREST para a molécula: {molecule.name}")
        try:
            # Verifica se o arquivo XYZ existe após a conversão
            xyz_path = molecule.xyz_path
            if not os.path.exists(xyz_path):
                raise FileNotFoundError(f"Arquivo XYZ não encontrado após conversão: {xyz_path}")
            logging.info(f"Arquivo XYZ encontrado após conversão: {xyz_path}")

            # Cria o diretório de saída do CREST
            output_dir = CREST_DIR / molecule.name
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"Diretório de saída do CREST criado: {output_dir}")

            # Define o diretório do CREST no WSL e caminhos do conda
            crest_wsl_dir = "/home/igor_fern/miniconda3/envs/crest_env/bin"
            xyz_filename = os.path.basename(xyz_path)

            # Converte o caminho Windows para o formato WSL
            xyz_path_abs = os.path.abspath(xyz_path)
            drive_letter = xyz_path_abs[0].lower()
            wsl_xyz_path = f"/mnt/{drive_letter}/{xyz_path_abs[3:].replace('\\', '/')}"
            
            # Copia o arquivo XYZ para o diretório WSL
            copy_command = f"cp '{wsl_xyz_path}' '{crest_wsl_dir}/{xyz_filename}'"
            subprocess.run(
                ["wsl", "bash", "-c", copy_command],
                capture_output=True,
                text=True,
                check=True
            )

            # Cria um script shell temporário no WSL
            script_content = f'''#!/bin/bash
    cd {crest_wsl_dir}
    source /home/igor_fern/miniconda3/etc/profile.d/conda.sh
    conda activate crest_env
    ./crest ./{xyz_filename} --gfn2 -T {self.settings.calculation_params.n_threads} {'--solv ' + self.settings.calculation_params.solvent if self.settings.calculation_params.solvent else ''}
    '''
            
            # Salva o script no WSL
            script_path = f"{crest_wsl_dir}/run_crest.sh"
            subprocess.run(
                ["wsl", "bash", "-c", f"echo '{script_content}' > {script_path}"],
                check=True
            )

            # Torna o script executável
            subprocess.run(
                ["wsl", "chmod", "+x", script_path],
                check=True
            )

            # Executa o script
            crest_log_file = output_dir / "crest.log"
            logging.info("Executando CREST via script...")
            
            with open(crest_log_file, "w") as log_file:
                process = subprocess.run(
                    ["wsl", script_path],
                    stdout=log_file,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )

            # Remove o script temporário
            subprocess.run(
                ["wsl", "rm", "-f", script_path],
                check=True
            )

            # Converte o caminho do diretório de saída para formato WSL
            output_dir_wsl = f"/mnt/{str(output_dir)[0].lower()}/{str(output_dir)[3:].replace('\\', '/')}"
            
            # Move os arquivos gerados para o diretório de saída
            move_command = f'''
            for file in {crest_wsl_dir}/crest* {crest_wsl_dir}/TMPCONF*; do
                if [ -f "$file" ]; then
                    mv "$file" '{output_dir_wsl}/'
                fi
            done
            '''
            
            subprocess.run(
                ["wsl", "bash", "-c", move_command],
                check=True
            )

            # Remove o arquivo XYZ de entrada
            subprocess.run(
                ["wsl", "rm", "-f", f"{crest_wsl_dir}/{xyz_filename}"],
                check=True
            )

            # Define os caminhos dos arquivos de saída importantes
            molecule.crest_conformers_path = str(output_dir / CREST_CONFORMERS_FILE)
            molecule.crest_best_path = str(output_dir / CREST_BEST_FILE)
            
            logging.info(f"Busca conformacional com CREST concluída para {molecule.name}")
            logging.info(f"Arquivos de saída: {molecule.crest_conformers_path}, {molecule.crest_best_path}")

        except subprocess.CalledProcessError as e:
            error_msg = f"Erro ao executar o CREST para a molécula {molecule.name}."
            if e.stderr:
                error_msg += f"\nErro: {e.stderr}"
            logging.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            logging.error(f"Erro ao executar o CREST para a molécula {molecule.name}: {e}")
            raise




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

        try:
            with open(xtb_log_file, "w") as log_file:
                process = subprocess.run(
                    command,
                    cwd=output_dir,
                    stdout=log_file,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )

            # Define o caminho do arquivo de saída da otimização
            molecule.xtb_opt_path = str(output_dir / XTBOPT_FILE)
            logging.info(f"Otimização de geometria com xTB concluída para {molecule.name}.")

        except subprocess.CalledProcessError as e:
            error_msg = f"Erro ao executar a otimização com xTB para a molécula {molecule.name}."
            if e.stderr:
                error_msg += f"\nErro: {e.stderr}"
            logging.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
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

        try:
            with open(xtb_log_file, "w") as log_file:
                process = subprocess.run(
                    command,
                    cwd=output_dir,
                    stdout=log_file,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )

            # Define os caminhos dos arquivos de saída do cálculo da Hessiana
            molecule.hessian_path = str(output_dir / HESSIAN_FILE)
            molecule.vibspectrum_path = str(output_dir / VIB_SPECTRUM_FILE)
            molecule.thermochemistry_path = str(output_dir / THERMOCHEMISTRY_FILE)

            logging.info(f"Cálculo da Hessiana e frequências vibracionais com xTB concluído para {molecule.name}.")

        except subprocess.CalledProcessError as e:
            error_msg = f"Erro ao executar o cálculo da Hessiana com xTB para a molécula {molecule.name}."
            if e.stderr:
                error_msg += f"\nErro: {e.stderr}"
            logging.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            logging.error(f"Erro ao executar o cálculo da Hessiana com xTB para a molécula {molecule.name}: {e}")
            raise

    def extract_formation_enthalpy(self, molecule: Molecule):
        """
        Extrai a entalpia de formação do arquivo de saída do xTB (xtbhess.log ou thermochemistry).
        """
        if not molecule.thermochemistry_path:
            logging.warning(f"O caminho do arquivo de termoquímica não está definido para a molécula {molecule.name}.")
            return
        
        thermochemistry_path = Path(molecule.thermochemistry_path)
        if not thermochemistry_path.exists():
            logging.warning(f"Arquivo de termoquímica do xTB não encontrado: {molecule.thermochemistry_path}.")
            return

        try:
            with open(thermochemistry_path, "r") as f:
                content = f.read()

            # Expressão regular para encontrar a entalpia de formação
            match = re.search(r"formation enthalpy\s+([\w-]+[\w]+)\s+([\d.-]+)\s+([\d.-]+)", content)

            if match:
                unit, value, _ = match.groups()
                formation_enthalpy_au = float(value)
                logging.info(f"Entalpia de formação extraída para {molecule.name}: {formation_enthalpy_au} {unit}")

                # Converte de Hartree para kcal/mol (1 Hartree = 627.509 kcal/mol)
                if unit == "Eh":
                    formation_enthalpy_kcal_mol = formation_enthalpy_au * 627.509
                else:
                    formation_enthalpy_kcal_mol = formation_enthalpy_au
                molecule.formation_enthalpy = formation_enthalpy_kcal_mol

            else:
                logging.warning(f"Não foi possível encontrar a entalpia de formação no arquivo {thermochemistry_path}.")
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