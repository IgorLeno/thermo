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
            molecule.crest_output_dir = str(output_dir)
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
            copy_result = subprocess.run(
                ["wsl", "bash", "-c", copy_command],
                capture_output=True,
                text=True,
                check=True
            )
            logging.info(f"Arquivo XYZ copiado para WSL: {copy_result.stdout}")
            if copy_result.stderr:
                logging.warning(f"Avisos ao copiar XYZ: {copy_result.stderr}")

            # Verifica se o arquivo foi copiado corretamente
            check_file_command = f"ls -la '{crest_wsl_dir}/{xyz_filename}'"
            check_file_result = subprocess.run(
                ["wsl", "bash", "-c", check_file_command],
                capture_output=True,
                text=True
            )
            logging.info(f"Verificação do arquivo XYZ no WSL: {check_file_result.stdout}")
            if check_file_result.returncode != 0:
                raise FileNotFoundError(f"Arquivo XYZ não foi copiado corretamente para o WSL: {check_file_result.stderr}")

            # Cria um script shell temporário no WSL
            script_content = f'''#!/bin/bash
set -e  # Sair imediatamente se um comando falhar
set -x  # Imprimir comandos e seus argumentos

cd {crest_wsl_dir}
source /home/igor_fern/miniconda3/etc/profile.d/conda.sh
conda activate crest_env
echo "Executando CREST para {xyz_filename}..."
pwd
ls -la ./{xyz_filename}
./crest ./{xyz_filename} --gfn2 -T {self.settings.calculation_params.n_threads} {'--solv ' + self.settings.calculation_params.solvent if self.settings.calculation_params.solvent else ''}
echo "CREST concluído, listando arquivos gerados:"
ls -la ./crest_*.xyz ./.crest* ./crest.* 2>/dev/null || echo "Nenhum arquivo de resultado encontrado"
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
            crest_log_file = output_dir / CREST_LOG_FILE
            logging.info("Executando CREST via script...")
            
            with open(crest_log_file, "w") as log_file:
                process = subprocess.run(
                    ["wsl", script_path],
                    stdout=log_file,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )
            
            if process.stderr:
                logging.warning(f"Avisos ou erros do CREST: {process.stderr}")

            # Remove o script temporário
            subprocess.run(
                ["wsl", "rm", "-f", script_path],
                check=True
            )

            # Converte o caminho do diretório de saída para formato WSL
            output_dir_wsl = f"/mnt/{str(output_dir)[0].lower()}/{str(output_dir)[3:].replace('\\', '/')}"
            
            # Garante que o diretório de destino exista no WSL
            mkdir_command = f"mkdir -p '{output_dir_wsl}'"
            subprocess.run(
                ["wsl", "bash", "-c", mkdir_command],
                check=True
            )
            
            # Copia (em vez de mover) os arquivos gerados para o diretório de saída
            copy_files_command = f'''
# Lista e imprime os arquivos que serão copiados para depuração
echo "Arquivos disponíveis no diretório CREST:"
ls -la {crest_wsl_dir}/crest_*.xyz {crest_wsl_dir}/.crest* {crest_wsl_dir}/crest.* 2>/dev/null || echo "Nenhum arquivo CREST encontrado"

# Copia arquivos específicos que sabemos que são gerados
cp {crest_wsl_dir}/crest_best.xyz '{output_dir_wsl}/' 2>/dev/null || echo "Arquivo crest_best.xyz não encontrado"
cp {crest_wsl_dir}/crest_conformers.xyz '{output_dir_wsl}/' 2>/dev/null || echo "Arquivo crest_conformers.xyz não encontrado"
cp {crest_wsl_dir}/crest.energies '{output_dir_wsl}/' 2>/dev/null || echo "Arquivo crest.energies não encontrado"
cp {crest_wsl_dir}/.crest_ensemble '{output_dir_wsl}/' 2>/dev/null || echo "Arquivo .crest_ensemble não encontrado"

# Verifica os arquivos copiados
echo "Arquivos copiados para o diretório de saída:"
ls -la '{output_dir_wsl}/' 2>/dev/null || echo "Diretório de saída vazio ou inacessível"
'''
            
            # Execute o comando com saída de erro visível para depuração
            copy_result = subprocess.run(
                ["wsl", "bash", "-c", copy_files_command],
                capture_output=True,
                text=True
            )
            logging.info(f"Resultado da cópia de arquivos: {copy_result.stdout}")
            if copy_result.stderr:
                logging.warning(f"Erros na cópia de arquivos: {copy_result.stderr}")

            # Verifica se os arquivos existem no WSL antes de definir os caminhos
            check_command = f"ls -la '{output_dir_wsl}/crest_best.xyz' '{output_dir_wsl}/crest_conformers.xyz' 2>/dev/null || echo 'Arquivos não encontrados'"
            check_result = subprocess.run(
                ["wsl", "bash", "-c", check_command],
                capture_output=True,
                text=True
            )

            if "Arquivos não encontrados" not in check_result.stdout:
                # Define os caminhos dos arquivos de saída importantes
                molecule.crest_conformers_path = str(output_dir / CREST_CONFORMERS_FILE)
                molecule.crest_best_path = str(output_dir / CREST_BEST_FILE)
                logging.info(f"Arquivos de saída: {molecule.crest_conformers_path}, {molecule.crest_best_path}")
            else:
                logging.error("Arquivos de saída do CREST não foram encontrados após a execução.")
                logging.info(f"Conteúdo do diretório de saída WSL: {check_result.stdout}")
                
                # Verificar se os arquivos foram gerados no diretório de trabalho do CREST
                check_crest_dir = f"ls -la {crest_wsl_dir}/crest_*.xyz {crest_wsl_dir}/.crest* 2>/dev/null || echo 'Nenhum arquivo CREST encontrado'"
                crest_dir_result = subprocess.run(
                    ["wsl", "bash", "-c", check_crest_dir],
                    capture_output=True,
                    text=True
                )
                logging.info(f"Arquivos no diretório do CREST: {crest_dir_result.stdout}")
                
                # Tenta uma abordagem alternativa - copiar diretamente do WSL para o Windows usando cp.exe
                alt_copy_command = f'''
                for file in crest_best.xyz crest_conformers.xyz; do
                    if [ -f "{crest_wsl_dir}/$file" ]; then
                        echo "Tentando cópia alternativa de $file..."
                        cp -v "{crest_wsl_dir}/$file" "{output_dir_wsl}/"
                    fi
                done
                '''
                alt_copy_result = subprocess.run(
                    ["wsl", "bash", "-c", alt_copy_command],
                    capture_output=True,
                    text=True
                )
                logging.info(f"Resultado da cópia alternativa: {alt_copy_result.stdout}")
                
                # Verifica novamente se os arquivos foram copiados
                recheck_command = f"ls -la '{output_dir_wsl}/'"
                recheck_result = subprocess.run(
                    ["wsl", "bash", "-c", recheck_command],
                    capture_output=True,
                    text=True
                )
                logging.info(f"Conteúdo final do diretório de saída: {recheck_result.stdout}")
                
                # Define os caminhos dos arquivos mesmo que não existam no Windows
                # para que o FileService possa lidar com eles adequadamente
                molecule.crest_conformers_path = str(output_dir / CREST_CONFORMERS_FILE)
                molecule.crest_best_path = str(output_dir / CREST_BEST_FILE)

            # Remove o arquivo XYZ de entrada do WSL
            subprocess.run(
                ["wsl", "rm", "-f", f"{crest_wsl_dir}/{xyz_filename}"],
                check=True
            )
            
            logging.info(f"Busca conformacional com CREST concluída para {molecule.name}")

        except subprocess.CalledProcessError as e:
            error_msg = f"Erro ao executar o CREST para a molécula {molecule.name}."
            if e.stderr:
                error_msg += f"\nErro: {e.stderr}"
            logging.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            logging.error(f"Erro ao executar o CREST para a molécula {molecule.name}: {e}")
            raise

    def run_calculation(self, molecule: Molecule):
        """
        Executa o fluxo simplificado de cálculo para uma molécula: apenas CREST.
        """
        try:
            self.run_crest(molecule)
            
            # Verifica se os arquivos de saída existem antes de prosseguir
            files_exist = True
            if molecule.crest_best_path and not os.path.exists(molecule.crest_best_path):
                logging.warning(f"Arquivo crest_best.xyz não encontrado: {molecule.crest_best_path}")
                files_exist = False
                
            if molecule.crest_conformers_path and not os.path.exists(molecule.crest_conformers_path):
                logging.warning(f"Arquivo crest_conformers.xyz não encontrado: {molecule.crest_conformers_path}")
                files_exist = False
            
            if not files_exist:
                logging.error(f"Arquivos de saída do CREST não foram encontrados após a execução para {molecule.name}.")
                # Tenta uma abordagem alternativa - copiar diretamente do WSL para Windows
                self._copy_crest_files_directly(molecule)
            
            # Move os arquivos de saída para o diretório final
            self.file_service.move_output_files(molecule)
            
            # Verifica novamente se os arquivos foram movidos corretamente
            output_dir = OUTPUT_DIR / molecule.name
            if not (output_dir / CREST_BEST_FILE).exists() or not (output_dir / CREST_CONFORMERS_FILE).exists():
                logging.warning(f"Arquivos CREST finais não foram encontrados em {output_dir}")
            else:
                logging.info(f"Arquivos CREST movidos com sucesso para {output_dir}")

        except Exception as e:
            logging.error(f"Erro durante o cálculo para a molécula {molecule.name}: {e}")
            print(f"Erro durante o cálculo para a molécula {molecule.name}. Veja o arquivo de log para mais detalhes.")
            
    def _copy_crest_files_directly(self, molecule):
        """
        Método auxiliar para tentar copiar os arquivos CREST diretamente do WSL para o Windows
        quando os métodos normais falham.
        """
        try:
            crest_wsl_dir = "/home/igor_fern/miniconda3/envs/crest_env/bin"
            output_dir = CREST_DIR / molecule.name
            
            # Verifica se os arquivos existem no WSL
            check_command = f"ls -la {crest_wsl_dir}/crest_best.xyz {crest_wsl_dir}/crest_conformers.xyz 2>/dev/null || echo 'Arquivos não encontrados'"
            check_result = subprocess.run(
                ["wsl", "bash", "-c", check_command],
                capture_output=True,
                text=True
            )
            
            if "Arquivos não encontrados" in check_result.stdout:
                logging.error(f"Arquivos CREST não encontrados no WSL: {check_result.stdout}")
                return False
                
            logging.info(f"Tentando copiar arquivos diretamente do WSL: {check_result.stdout}")
            
            # Lê o conteúdo dos arquivos no WSL e os escreve diretamente no Windows
            for file_name in ["crest_best.xyz", "crest_conformers.xyz"]:
                cat_command = f"cat {crest_wsl_dir}/{file_name} 2>/dev/null || echo 'Arquivo não encontrado'"
                cat_result = subprocess.run(
                    ["wsl", "bash", "-c", cat_command],
                    capture_output=True,
                    text=True
                )
                
                if "Arquivo não encontrado" not in cat_result.stdout:
                    # Escreve o conteúdo para o arquivo no Windows
                    with open(output_dir / file_name, 'w') as f:
                        f.write(cat_result.stdout)
                    logging.info(f"Arquivo {file_name} copiado manualmente para {output_dir / file_name}")
            
            # Atualiza os caminhos da molécula
            molecule.crest_best_path = str(output_dir / CREST_BEST_FILE)
            molecule.crest_conformers_path = str(output_dir / CREST_CONFORMERS_FILE)
            
            return True
            
        except Exception as e:
            logging.error(f"Erro ao tentar copiar arquivos diretamente: {e}")
            return False