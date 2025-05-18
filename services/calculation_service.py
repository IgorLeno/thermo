import subprocess
import os
import re
import shutil
import time
import json
from pathlib import Path
import logging
from typing import Optional, Dict, Any
from core.molecule import Molecule
from config.settings import Settings
from services.file_service import FileService
from services.conversion_service import ConversionService
from config.constants import *
from services.analysis.conformer_analyzer import ConformerAnalyzer

class CalculationService:
    def __init__(self, settings: Settings, file_service: FileService, conversion_service: ConversionService):
        self.settings = settings
        self.file_service = file_service
        self.conversion_service = conversion_service
        self.mopac_executable = str(settings.mopac_executable_path)
        self.mopac_keywords = settings.mopac_keywords
        
        # Inicializa o serviço Supabase se estiver habilitado nas configurações
        self.supabase_service = None
        if settings.supabase.enabled:
            try:
                from services.supabase_service import SupabaseService
                self.supabase_service = SupabaseService(
                    url=settings.supabase.url,
                    key=settings.supabase.key
                )
                if self.supabase_service.enabled:
                    logging.info("Serviço Supabase inicializado com sucesso.")
                else:
                    logging.warning("Supabase habilitado nas configurações, mas a conexão falhou.")
            except ImportError:
                logging.error("Biblioteca Supabase não encontrada. Execute 'pip install supabase'.")
            except Exception as e:
                logging.error(f"Erro ao inicializar serviço Supabase: {e}")

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
                # Simplifica a mensagem de erro/aviso do CREST
                stderr_lines = process.stderr.splitlines()
                simplified_stderr = ""
                
                # Filtra as linhas relevantes (evita mostrar todo o PATH e outros detalhes verbosos)
                for line in stderr_lines:
                    if ("error" in line.lower() or 
                        "warning" in line.lower() or 
                        "executing crest" in line.lower() or
                        "crest concluído" in line.lower()):
                        simplified_stderr += line + "\n"
                        
                # Se ainda for muito longo, usa apenas o início e o fim
                if len(simplified_stderr.splitlines()) > 5:
                    top_lines = simplified_stderr.splitlines()[:2]
                    bottom_lines = simplified_stderr.splitlines()[-2:]
                    simplified_stderr = "\n".join(top_lines + ["..."] + bottom_lines)
                
                logging.warning(f"Avisos ou erros do CREST: {simplified_stderr}")
            else:
                logging.info("CREST executado sem erros ou avisos.")

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

    def _convert_xyz_to_pdb(self, input_xyz_path: Path) -> Optional[Path]:
        """Converte o XYZ do CREST para PDB e salva em repository/pdb/."""
        if not input_xyz_path or not input_xyz_path.exists():
            logging.error(f"Arquivo XYZ de entrada '{input_xyz_path}' não encontrado para conversão para PDB.")
            return None

        pdb_dir = PDB_DIR
        pdb_dir.mkdir(parents=True, exist_ok=True)
        output_pdb_path = pdb_dir / f"{self.molecule_data.name}.pdb"

        try:
            success = self.conversion_service.convert_file(
                input_file_path=input_xyz_path,
                output_file_path=output_pdb_path,
                input_format="xyz",
                output_format="pdb"
            )
            if success:
                logging.info(f"Convertido {input_xyz_path} para {output_pdb_path}")
                return output_pdb_path
            else:
                logging.error(f"Falha ao converter {input_xyz_path} para PDB.")
                return None
        except Exception as e:
            logging.error(f"Erro durante a conversão XYZ para PDB: {e}")
            return None

    def _prepare_mopac_input_file(self, pdb_file_path: Path, mopac_work_dir: Path) -> Optional[Path]:
        """Prepara o arquivo .dat para o MOPAC."""
        if not pdb_file_path or not pdb_file_path.exists():
            logging.error(f"Arquivo PDB '{pdb_file_path}' não encontrado para preparar input do MOPAC.")
            return None
        
        # Primeiro, gera o arquivo .dat no diretório dat
        dat_dir = DAT_DIR
        dat_dir.mkdir(parents=True, exist_ok=True)
        dat_file_path = dat_dir / f"{self.molecule_data.name}.dat"
        
        try:
            with open(pdb_file_path, 'r') as f_pdb:
                pdb_content = f_pdb.read()

            # MOPAC espera palavras-chave, uma linha em branco (opcional, mas boa prática), depois as coordenadas.
            # O arquivo PDB do OpenBabel já terá as coordenadas ATOM/HETATM e END.
            mopac_input_content = f"{self.mopac_keywords}\n\n{pdb_content}" 

            # Escreve o arquivo no diretório dat
            with open(dat_file_path, 'w') as f_dat:
                f_dat.write(mopac_input_content)
            logging.info(f"Arquivo de entrada do MOPAC preparado: {dat_file_path}")
            
            # Garante que o diretório de trabalho do MOPAC existe
            mopac_work_dir.mkdir(parents=True, exist_ok=True)
            
            # Copia o arquivo para o diretório de trabalho do MOPAC
            mopac_input_dat_path = mopac_work_dir / f"{self.molecule_data.name}.dat"
            shutil.copy(dat_file_path, mopac_input_dat_path)
            logging.info(f"Arquivo de entrada do MOPAC copiado para: {mopac_input_dat_path}")
            
            return dat_file_path
        except Exception as e:
            logging.error(f"Erro ao preparar arquivo de entrada do MOPAC: {e}")
            return None

    def _run_mopac(self, input_dat_path: Path, working_directory: Path) -> bool:
        """Executa o MOPAC."""
        try:
            # Verifica se o arquivo de entrada existe
            if not input_dat_path.exists():
                logging.error(f"Arquivo de entrada do MOPAC não encontrado: {input_dat_path}")
                return False
                
            # Verifica se o diretório de saída existe (para os resultados)
            working_directory.mkdir(parents=True, exist_ok=True)
            
            # Diretório onde o MOPAC está instalado
            mopac_install_dir = MOPAC_PROGRAM_DIR
            if not Path(mopac_install_dir).exists():
                logging.error(f"Diretório do MOPAC não encontrado: {mopac_install_dir}")
                return False
                
            # Verifica se o executável do MOPAC existe
            mopac_exec = Path(mopac_install_dir) / "MOPAC2016.exe"
            if not mopac_exec.exists():
                logging.error(f"Executável do MOPAC não encontrado: {mopac_exec}")
                return False
                
            # Nome base do arquivo (sem extensão)
            molecule_name = self.molecule_data.name
            
            # Copia o arquivo .dat para o diretório do MOPAC
            mopac_input_file = Path(mopac_install_dir) / f"{molecule_name}.dat" 
            try:
                shutil.copy(input_dat_path, mopac_input_file)
                logging.info(f"Arquivo de entrada copiado para diretório do MOPAC: {mopac_input_file}")
            except Exception as e:
                logging.error(f"Erro ao copiar arquivo de entrada para diretório do MOPAC: {e}")
                return False
                
            # Executa o MOPAC no diretório correto
            command = [str(mopac_exec), f"{molecule_name}"]
            logging.info(f"Executando MOPAC no diretório {mopac_install_dir}: {' '.join(command)}")
            
            # Salva o diretório atual para restaurar depois
            original_dir = os.getcwd()
            
            # Muda para o diretório do MOPAC para execução
            os.chdir(mopac_install_dir)
            
            try:
                # Executa o MOPAC
                process = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                # Verifica resultado
                logging.info(f"MOPAC retornou código: {process.returncode}")
                if process.stdout:
                    logging.info(f"MOPAC stdout: {process.stdout}")
                if process.stderr:
                    logging.warning(f"MOPAC stderr: {process.stderr}")
                
                # Verifica se os arquivos de saída foram gerados
                mopac_out_file = Path(mopac_install_dir) / f"{molecule_name}.out"
                mopac_arc_file = Path(mopac_install_dir) / f"{molecule_name}.arc"
                
                if not mopac_out_file.exists() or not mopac_arc_file.exists():
                    logging.error(f"Arquivos de saída do MOPAC não foram gerados: {mopac_out_file}, {mopac_arc_file}")
                    # Método alternativo - usando shell=True com o caminho completo
                    alt_command = f"{mopac_exec} {molecule_name}"
                    logging.info(f"Tentando método alternativo: {alt_command}")
                    
                    alt_process = subprocess.run(
                        alt_command,
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    logging.info(f"MOPAC alternativo retornou código: {alt_process.returncode}")
                    if alt_process.stdout:
                        logging.info(f"MOPAC stdout alternativo: {alt_process.stdout}")
                    if alt_process.stderr:
                        logging.warning(f"MOPAC stderr alternativo: {alt_process.stderr}")
                
                # Verifica novamente se os arquivos foram gerados
                if mopac_out_file.exists() and mopac_arc_file.exists():
                    # Move os arquivos de saída para o diretório de trabalho
                    shutil.copy(mopac_out_file, working_directory / f"{molecule_name}.out")
                    shutil.copy(mopac_arc_file, working_directory / f"{molecule_name}.arc")
                    
                    logging.info(f"Arquivos de saída do MOPAC movidos para: {working_directory}")
                    
                    # Limpa os arquivos temporários
                    try:
                        temp_files = [
                            mopac_out_file,
                            mopac_arc_file,
                            mopac_input_file,
                            Path(mopac_install_dir) / f"{molecule_name}.mgf"
                        ]
                        
                        for temp_file in temp_files:
                            if temp_file.exists():
                                os.remove(temp_file)
                                logging.info(f"Arquivo temporário removido: {temp_file}")
                    except Exception as clean_e:
                        logging.warning(f"Erro ao limpar arquivos temporários: {clean_e}")
                    
                    return True
                else:
                    logging.error(f"MOPAC falhou ao gerar os arquivos de saída mesmo após tentativas alternativas")
                    return False
                    
            finally:
                # Restaura o diretório original
                os.chdir(original_dir)
                
        except Exception as e:
            logging.error(f"Erro durante a execução do MOPAC: {e}")
            try:
                # Restaura o diretório original em caso de erro
                os.chdir(original_dir)
            except:
                pass
            return False

        # Prepara o comando com o caminho absoluto do executável
        command = [mopac_path, str(input_dat_path.name)] # MOPAC usa o nome do arquivo no cwd
        logging.info(f"Executando MOPAC: {' '.join(command)} em {working_directory}")

        try:
            # Tenta executar o MOPAC com o comando completo
            logging.info(f"Tentando executar MOPAC com comando: {command}")
            
            process = subprocess.run(
                command,
                cwd=str(working_directory), # MOPAC gera arquivos no diretório de trabalho
                capture_output=True,
                text=True,
                check=False # Não levanta exceção para non-zero exit codes automaticamente
            )
            
            # Arquivos esperados
            mopac_out_file = working_directory / f"{self.molecule_data.name}.out"
            mopac_arc_file = working_directory / f"{self.molecule_data.name}.arc"
            
            # Verifica resultado
            logging.info(f"MOPAC retornou código: {process.returncode}")
            if process.stdout:
                logging.info(f"MOPAC stdout: {process.stdout}")
            if process.stderr:
                logging.warning(f"MOPAC stderr: {process.stderr}")
            
            # Se os arquivos existem, deu certo
            if mopac_out_file.exists() and mopac_arc_file.exists():
                logging.info(f"MOPAC concluído com sucesso. Arquivos gerados: {mopac_out_file}, {mopac_arc_file}")
                return True
                
            # Se não funcionou, tenta abordagem alternativa
            if process.returncode != 0 or not (mopac_out_file.exists() and mopac_arc_file.exists()):
                logging.warning("Tentando método alternativo para executar o MOPAC...")
                
                # Usando cmd.exe explicitamente (melhor compatibilidade no Windows)
                cmd_command = f'cd /d "{working_directory}" && "{command[0]}" {command[1]}'
                logging.info(f"Comando alternativo: {cmd_command}")
                
                alt_process = subprocess.run(
                    cmd_command,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                logging.info(f"MOPAC alternativo retornou código: {alt_process.returncode}")
                if alt_process.stdout:
                    logging.info(f"MOPAC stdout alternativo: {alt_process.stdout}")
                if alt_process.stderr:
                    logging.warning(f"MOPAC stderr alternativo: {alt_process.stderr}")
                
                # Verifica novamente se os arquivos foram criados
                if mopac_out_file.exists() and mopac_arc_file.exists():
                    logging.info(f"MOPAC alternativo concluído com sucesso.")
                    return True
                else:
                    logging.error(f"MOPAC falhou com ambos os métodos. Arquivos não encontrados em {working_directory}")
                    # Lista os arquivos no diretório para diagnóstico
                    try:
                        files_in_dir = list(working_directory.glob("*"))
                        logging.info(f"Arquivos no diretório após tentativas: {[f.name for f in files_in_dir]}")
                    except Exception as dir_e:
                        logging.error(f"Erro ao listar diretório: {dir_e}")
                    return False
            
            # Se chegou aqui é porque funcionou na primeira tentativa
            return True

        except FileNotFoundError:
            logging.error(f"Erro: Executável do MOPAC '{self.mopac_executable}' não encontrado. Verifique o caminho e as configurações.")
            return False
        except Exception as e:
            logging.error(f"Erro durante a execução do MOPAC: {e}")
            return False
    
    def _extract_mopac_enthalpy(self, mopac_output_file: Path) -> tuple:
        """
        Extrai a entalpia de formação do arquivo .out do MOPAC em ambas as unidades.
        
        Args:
            mopac_output_file: Caminho para o arquivo de saída .out do MOPAC
            
        Returns:
            Uma tupla com (entalpia_kcal_mol, entalpia_kj_mol) ou (None, None) em caso de erro
        """
        if not mopac_output_file or not mopac_output_file.exists():
            logging.error(f"Arquivo de saída do MOPAC '{mopac_output_file}' não encontrado para extração.")
            return None, None
        try:
            with open(mopac_output_file, 'r') as f:
                content = f.read()
            
            # Expressão regular para capturar ambos os valores (kcal/mol e kJ/mol)
            # FINAL HEAT OF FORMATION = -67.53047 KCAL/MOL = -282.54749 KJ/MOL
            match = re.search(r"FINAL HEAT OF FORMATION\s*=\s*(-?\d+\.\d+)\s*KCAL/MOL\s*=\s*(-?\d+\.\d+)\s*KJ/MOL", 
                            content, re.IGNORECASE)
            
            if match:
                enthalpy_kcal = float(match.group(1))
                enthalpy_kj = float(match.group(2))
                logging.info(f"Entalpia de formação extraída do MOPAC: {enthalpy_kcal} kcal/mol, {enthalpy_kj} kJ/mol")
                return enthalpy_kcal, enthalpy_kj
            else:
                # Tentativa alternativa - procurar os valores separadamente
                match_kcal = re.search(r"FINAL HEAT OF FORMATION\s*=\s*(-?\d+\.\d+)\s*KCAL/MOL", content, re.IGNORECASE)
                match_kj = re.search(r"FINAL HEAT OF FORMATION\s*=\s*(-?\d+\.\d+)\s*KJ/MOL", content, re.IGNORECASE)
                
                if match_kcal:
                    enthalpy_kcal = float(match_kcal.group(1))
                    # Se apenas kcal/mol foi encontrado, calcule kJ/mol (1 kcal/mol = 4.184 kJ/mol)
                    enthalpy_kj = enthalpy_kcal * 4.184
                    logging.info(f"Entalpia de formação extraída do MOPAC (apenas kcal): {enthalpy_kcal} kcal/mol, calculado: {enthalpy_kj} kJ/mol")
                    return enthalpy_kcal, enthalpy_kj
                    
                elif match_kj:
                    enthalpy_kj = float(match_kj.group(1))
                    # Se apenas kJ/mol foi encontrado, calcule kcal/mol (1 kJ/mol = 0.239 kcal/mol)
                    enthalpy_kcal = enthalpy_kj * 0.239
                    logging.info(f"Entalpia de formação extraída do MOPAC (apenas kJ): calculado: {enthalpy_kcal} kcal/mol, {enthalpy_kj} kJ/mol")
                    return enthalpy_kcal, enthalpy_kj
                
                logging.warning(f"Não foi possível encontrar 'FINAL HEAT OF FORMATION' no arquivo {mopac_output_file}")
                return None, None
        except Exception as e:
            logging.error(f"Erro ao extrair entalpia do MOPAC: {e}")
            return None, None

    def _store_final_results(self):
        """Armazena os resultados finais (ex: entalpia) em final_molecules."""
        final_dir = FINAL_MOLECULES_DIR / "output" / self.molecule_data.name
        final_dir.mkdir(parents=True, exist_ok=True)

        summary_file = final_dir / "results_summary.txt"
        with open(summary_file, 'w') as f:
            f.write(f"Molécula: {self.molecule_data.name}\n")
            f.write(f"Método de Entalpia: MOPAC ({self.mopac_keywords.split()[0] if self.mopac_keywords else 'N/A'})\n") # Ex: PM7
            
            # Inclui ambas as unidades de entalpia
            if self.molecule_data.enthalpy_formation_mopac is not None:
                f.write(f"Entalpia de Formação: {self.molecule_data.enthalpy_formation_mopac} kcal/mol\n")
                if hasattr(self.molecule_data, 'enthalpy_formation_mopac_kj') and self.molecule_data.enthalpy_formation_mopac_kj is not None:
                    f.write(f"Entalpia de Formação: {self.molecule_data.enthalpy_formation_mopac_kj} kJ/mol\n")
            else:
                f.write("Entalpia de Formação: Não calculada ou erro.\n")
            
            f.write("\nCaminhos dos arquivos intermediários:\n")
            f.write(f"  CREST best XYZ: {self.molecule_data.path_to_crest_best_xyz}\n")
            f.write(f"  PDB para MOPAC: {self.molecule_data.converted_pdb_path}\n")
            f.write(f"  MOPAC .dat: {self.molecule_data.mopac_input_dat_path}\n")
            f.write(f"  MOPAC .out: {self.molecule_data.path_to_mopac_out}\n")
        
        logging.info(f"Resultados finais para {self.molecule_data.name} salvos em {summary_file}")

        # Opcional: Copiar o MOPAC .out para final_dir também
        if self.molecule_data.path_to_mopac_out and self.molecule_data.path_to_mopac_out.exists():
            shutil.copy(self.molecule_data.path_to_mopac_out, final_dir)
            
    def run_calculation(self, molecule: Molecule):
        """
        Executa o fluxo completo de cálculo para uma molécula: CREST seguido de MOPAC.
        """
        try:
            # Armazena a molécula como atributo da classe para acesso em outros métodos
            self.molecule_data = molecule
            
            # Etapa CREST
            self.run_crest(molecule)
            
            # Verifica se os arquivos de saída do CREST existem antes de prosseguir
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
            
            # Verifica novamente antes de prosseguir para MOPAC
            if not molecule.path_to_crest_best_xyz or not molecule.path_to_crest_best_xyz.exists():
                logging.error(f"Arquivo crest_best.xyz não encontrado após todas as tentativas. Não é possível prosseguir para MOPAC.")
                return False
                
            logging.info("Etapa CREST concluída. Iniciando etapa MOPAC...")
            
            # --- Etapa de Conversão XYZ (do CREST) para PDB ---
            converted_pdb_path = self._convert_xyz_to_pdb(molecule.path_to_crest_best_xyz)
            if not converted_pdb_path:
                logging.error(f"Falha na conversão para PDB. Workflow interrompido para {molecule.name}.")
                return False
            molecule.converted_pdb_path = converted_pdb_path

            # --- Etapa de Preparação do Input MOPAC ---
            mopac_work_dir = MOPAC_DIR / molecule.name
            mopac_input_dat = self._prepare_mopac_input_file(converted_pdb_path, mopac_work_dir)
            if not mopac_input_dat:
                logging.error(f"Falha na preparação do arquivo de entrada do MOPAC. Workflow interrompido para {molecule.name}.")
                return False
            molecule.mopac_input_dat_path = mopac_input_dat
            molecule.mopac_output_directory = mopac_work_dir

            # --- Etapa de Execução do MOPAC ---
            # Usamos o arquivo .dat copiado no diretório mopac/molecule_name
            mopac_exec_dat_path = mopac_work_dir / f"{self.molecule_data.name}.dat"
            mopac_success = self._run_mopac(mopac_exec_dat_path, mopac_work_dir)
            if not mopac_success:
                logging.error(f"Falha na execução do MOPAC. Workflow interrompido para {molecule.name}.")
                return False
            
            # --- Etapa de Extração da Entalpia do MOPAC ---
            mopac_out_file = mopac_work_dir / f"{molecule.name}.out"
            enthalpy = self._extract_mopac_enthalpy(mopac_out_file)
            
            # Atualizar o objeto Molecule com os resultados do MOPAC
            molecule.set_mopac_results(
                pdb_path=converted_pdb_path,
                dat_path=mopac_input_dat,
                output_dir=mopac_work_dir,
                enthalpy=enthalpy
            )

            if enthalpy is not None:
                logging.info(f"Entalpia de formação (MOPAC) para {molecule.name}: {enthalpy} (unidade conforme MOPAC output)")
                self._store_final_results()
            else:
                logging.warning(f"Não foi possível obter a entalpia de formação do MOPAC para {molecule.name}.")
            
            # Nota: Não movemos arquivos para o diretório final_molecules
            # Os arquivos CREST ficam em repository/crest, os MOPAC em repository/mopac
            
            # Enviar resultados para o Supabase se habilitado
            if self.supabase_service and self.supabase_service.enabled:
                self._upload_results_to_supabase(molecule)
            
            logging.info(f"Workflow completo concluído para {molecule.name}.")
            return True
            
        except Exception as e:
            logging.error(f"Erro durante o cálculo para a molécula {molecule.name}: {e}")
            print(f"Erro durante o cálculo para a molécula {molecule.name}. Veja o arquivo de log para mais detalhes.")
            return False
            
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
            
    def _upload_results_to_supabase(self, molecule: Molecule) -> bool:
        """
        Envia os resultados do cálculo para o Supabase.
        
        Args:
            molecule: Objeto Molecule com os dados da molécula
            
        Returns:
            True se o upload foi bem-sucedido, False caso contrário
        """
        if not self.supabase_service or not self.supabase_service.enabled:
            logging.warning("Serviço Supabase não está habilitado. Não será feito upload dos resultados.")
            return False
            
        try:
            logging.info(f"Enviando resultados de {molecule.name} para o Supabase...")
            
            # Obter o ID da molécula (ou criar se não existir)
            molecule_id = self.supabase_service.upload_molecule(molecule)
            if not molecule_id:
                logging.error(f"Erro ao enviar a molécula {molecule.name} para o Supabase.")
                return False
                
            # Prepara os parâmetros e resultados do CREST
            crest_params = {
                "n_threads": self.settings.calculation_params.n_threads,
                "method": self.settings.calculation_params.crest_method,
                "electronic_temperature": self.settings.calculation_params.electronic_temperature,
                "solvent": self.settings.calculation_params.solvent
            }
            
            # Obter estatísticas dos confôrmeros
            analyzer = ConformerAnalyzer()
            conformer_stats = analyzer.get_conformer_statistics(molecule.name)
            
            # Upload de arquivos para o Storage, se habilitado
            best_conformer_url = None
            all_conformers_url = None
            
            if self.settings.supabase.storage_enabled:
                bucket_name = self.settings.supabase.molecules_bucket
                
                # Verificar e criar o bucket se necessário
                if not self.supabase_service.ensure_bucket_exists(bucket_name):
                    logging.error(f"Não foi possível garantir a existência do bucket '{bucket_name}'. Upload de arquivos cancelado.")
                else:
                    # Agora que o bucket existe, tenta fazer o upload dos arquivos
                    if molecule.crest_best_path and Path(molecule.crest_best_path).exists():
                        best_conformer_url = self.supabase_service.upload_file(
                            file_path=molecule.crest_best_path,
                            bucket_name=bucket_name,
                            file_name=f"{molecule.name}/crest_best.xyz"
                        )
                        
                    if molecule.crest_conformers_path and Path(molecule.crest_conformers_path).exists():
                        all_conformers_url = self.supabase_service.upload_file(
                            file_path=molecule.crest_conformers_path,
                            bucket_name=bucket_name,
                            file_name=f"{molecule.name}/crest_conformers.xyz"
                        )
            
            # Preparar resultados do CREST com caminhos locais ou URLs
            crest_results = {
                "num_conformers": len(molecule.conformer_energies) if hasattr(molecule, 'conformer_energies') and molecule.conformer_energies else None,
                "best_conformer_path": best_conformer_url or molecule.crest_best_path,
                "all_conformers_path": all_conformers_url or molecule.crest_conformers_path
            }
            
            # Adicionar estatísticas do conformador se disponíveis
            if conformer_stats and conformer_stats.get('success', False):
                crest_results["energy_distribution"] = conformer_stats.get("relative_energies", [])
                crest_results["relative_energies"] = conformer_stats.get("relative_energies", [])
                crest_results["populations"] = conformer_stats.get("populations", [])
            
            # Enviar resultados CREST
            crest_success = self.supabase_service.upload_calculation_results(
                molecule_id=molecule_id,
                calculation_type="crest",
                status="completed",
                parameters=crest_params,
                results=crest_results
            )
            
            # Upload do arquivo MOPAC para o Storage, se habilitado
            mopac_output_url = None
            
            if self.settings.supabase.storage_enabled and molecule.path_to_mopac_out and molecule.path_to_mopac_out.exists():
                bucket_name = self.settings.supabase.molecules_bucket
                # O bucket já deve existir neste ponto, mas verificamos novamente por segurança
                if self.supabase_service.ensure_bucket_exists(bucket_name):
                    mopac_output_url = self.supabase_service.upload_file(
                        file_path=molecule.path_to_mopac_out,
                        bucket_name=bucket_name,
                        file_name=f"{molecule.name}/mopac.out"
                    )
            
            # Enviar resultados MOPAC
            mopac_params = {
                "keywords": self.mopac_keywords
            }
            
            mopac_results = {
                "enthalpy_formation": molecule.enthalpy_formation_mopac,
                "method": self.mopac_keywords.split()[0] if self.mopac_keywords else None,
                "output_path": mopac_output_url or str(molecule.path_to_mopac_out) if molecule.path_to_mopac_out else None
            }
            
            mopac_success = self.supabase_service.upload_calculation_results(
                molecule_id=molecule_id,
                calculation_type="mopac",
                status="completed" if molecule.enthalpy_formation_mopac is not None else "failed",
                parameters=mopac_params,
                results=mopac_results
            )
            
            if crest_success and mopac_success:
                logging.info(f"Resultados de {molecule.name} enviados com sucesso para o Supabase.")
                return True
            else:
                logging.warning(f"Pelo menos um dos uploads de {molecule.name} falhou: CREST={crest_success}, MOPAC={mopac_success}")
                return False
                
        except Exception as e:
            logging.error(f"Erro ao enviar resultados de {molecule.name} para o Supabase: {e}")
            return False