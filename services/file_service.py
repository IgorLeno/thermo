import os
import shutil
import glob
import logging
from pathlib import Path
from datetime import datetime
from config.constants import *
from core.molecule import Molecule

class FileService:
    """
    Classe para lidar com operações de arquivos e diretórios.
    """

    def create_directory(self, directory: str, clear: bool = False):
        """Cria um diretório. Se clear=True, remove o conteúdo existente."""
        if clear and os.path.exists(directory):
            self.clear_directory(directory)
        os.makedirs(directory, exist_ok=True)
        logging.info(f"Diretório criado: {directory}")

    def clear_directory(self, directory: str):
        """Remove todos os arquivos e subdiretórios de um diretório."""
        try:
            for root, dirs, files in os.walk(directory, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))
            logging.info(f"Diretório limpo: {directory}")
        except Exception as e:
            logging.error(f"Erro ao limpar diretório {directory}: {e}")

    def copy_file(self, source: str, destination: str):
        """Copia um arquivo de source para destination."""
        try:
            if not os.path.exists(source):
                logging.warning(f"Arquivo de origem não existe: {source}")
                return None
                
            # Garante que o diretório de destino existe
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            shutil.copy(source, destination)
            logging.info(f"Arquivo copiado: {source} -> {destination}")
            return destination
        except Exception as e:
            logging.error(f"Erro ao copiar arquivo {source} para {destination}: {e}")
            return None

    def move_file(self, source: str, destination: str):
        """Move um arquivo de source para destination."""
        try:
            if not os.path.exists(source):
                logging.warning(f"Arquivo de origem não existe: {source}")
                return None
                
            # Garante que o diretório de destino existe
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            shutil.move(source, destination)
            logging.info(f"Arquivo movido: {source} -> {destination}")
            return destination
        except Exception as e:
            logging.error(f"Erro ao mover arquivo {source} para {destination}: {e}")
            # Tenta uma abordagem alternativa - copiar e depois excluir
            try:
                if os.path.exists(source):
                    shutil.copy(source, destination)
                    os.remove(source)
                    logging.info(f"Arquivo copiado e removido manualmente: {source} -> {destination}")
                    return destination
            except Exception as copy_error:
                logging.error(f"Falha na abordagem alternativa: {copy_error}")
            return None

    def file_exists(self, filepath: str) -> bool:
        """Verifica se um arquivo existe."""
        exists = os.path.exists(filepath)
        if not exists:
            logging.debug(f"Arquivo não existe: {filepath}")
        return exists
    
    def move_output_files(self, molecule: Molecule):
        """
        Move os arquivos de saída relevantes para o diretório final de resultados.
        """
        try:
            molecule_output_dir = OUTPUT_DIR / molecule.name
            self.create_directory(molecule_output_dir)
            logging.info(f"Preparando diretório de saída final: {molecule_output_dir}")

            # Lista para rastrear arquivos movidos com sucesso
            moved_files = []

            # Move o arquivo crest_best.xyz se existir
            if molecule.crest_best_path:
                if os.path.exists(molecule.crest_best_path):
                    dest_path = molecule_output_dir / CREST_BEST_FILE
                    if self.move_file(molecule.crest_best_path, dest_path):
                        moved_files.append(f"crest_best.xyz -> {dest_path}")
                else:
                    logging.warning(f"Arquivo crest_best.xyz não encontrado em {molecule.crest_best_path}")

            # Move o arquivo crest_conformers.xyz se existir
            if molecule.crest_conformers_path:
                if os.path.exists(molecule.crest_conformers_path):
                    dest_path = molecule_output_dir / CREST_CONFORMERS_FILE
                    if self.move_file(molecule.crest_conformers_path, dest_path):
                        moved_files.append(f"crest_conformers.xyz -> {dest_path}")
                else:
                    logging.warning(f"Arquivo crest_conformers.xyz não encontrado em {molecule.crest_conformers_path}")

            # Move o arquivo crest.out e .crest_ensemble se existirem
            if molecule.crest_output_dir:
                crest_log_path = Path(molecule.crest_output_dir) / CREST_LOG_FILE
                crest_ensemble_path = Path(molecule.crest_output_dir) / CREST_ENSEMBLE_FILE
                crest_energies_path = Path(molecule.crest_output_dir) / "crest.energies"
                
                if crest_log_path.exists():
                    dest_path = molecule_output_dir / CREST_LOG_FILE
                    if self.move_file(str(crest_log_path), dest_path):
                        moved_files.append(f"crest.out -> {dest_path}")
                
                if crest_ensemble_path.exists():
                    dest_path = molecule_output_dir / CREST_ENSEMBLE_FILE
                    if self.move_file(str(crest_ensemble_path), dest_path):
                        moved_files.append(f".crest_ensemble -> {dest_path}")
                        
                if crest_energies_path.exists():
                    dest_path = molecule_output_dir / "crest.energies"
                    if self.move_file(str(crest_energies_path), dest_path):
                        moved_files.append(f"crest.energies -> {dest_path}")
            
            # Move os arquivos MOPAC se existirem
            if hasattr(molecule, 'path_to_mopac_out') and molecule.path_to_mopac_out and molecule.path_to_mopac_out.exists():
                dest_path = molecule_output_dir / f"{molecule.name}.out"
                if self.copy_file(str(molecule.path_to_mopac_out), dest_path):
                    moved_files.append(f"{molecule.name}.out -> {dest_path}")
                    
            if hasattr(molecule, 'path_to_mopac_arc') and molecule.path_to_mopac_arc and molecule.path_to_mopac_arc.exists():
                dest_path = molecule_output_dir / f"{molecule.name}.arc"
                if self.copy_file(str(molecule.path_to_mopac_arc), dest_path):
                    moved_files.append(f"{molecule.name}.arc -> {dest_path}")
            else:
                # Tenta encontrar o arquivo .arc no diretório do MOPAC
                alt_arc_path = MOPAC_PROGRAM_DIR / f"{molecule.name}.arc"
                if alt_arc_path.exists():
                    dest_path = molecule_output_dir / f"{molecule.name}.arc"
                    if self.copy_file(str(alt_arc_path), dest_path):
                        moved_files.append(f"{molecule.name}.arc -> {dest_path} (do diretório MOPAC)")
                    
            if hasattr(molecule, 'converted_pdb_path') and molecule.converted_pdb_path and molecule.converted_pdb_path.exists():
                dest_path = molecule_output_dir / f"{molecule.name}.pdb"
                if self.copy_file(str(molecule.converted_pdb_path), dest_path):
                    moved_files.append(f"{molecule.name}.pdb -> {dest_path}")
            
            # Cria um arquivo summary com os resultados
            if hasattr(molecule, 'enthalpy_formation_mopac') and molecule.enthalpy_formation_mopac is not None:
                summary_path = molecule_output_dir / "enthalpy_summary.txt"
                try:
                    with open(summary_path, 'w') as f:
                        f.write(f"Molécula: {molecule.name}\n")
                        f.write(f"Entalpia de formação (MOPAC): {molecule.enthalpy_formation_mopac}\n")
                    moved_files.append(f"Arquivo de resumo criado: {summary_path}")
                except Exception as sum_err:
                    logging.error(f"Erro ao criar arquivo de resumo: {sum_err}")
            
            # Verificar se algum arquivo foi movido
            if moved_files:
                logging.info(f"Arquivos movidos para {molecule_output_dir}:")
                for file in moved_files:
                    logging.info(f"  - {file}")
            else:
                logging.warning(f"Nenhum arquivo foi movido para {molecule_output_dir}")
                
                # Tenta procurar arquivos CREST diretamente no diretório de saída
                try:
                    crest_dir = CREST_DIR / molecule.name
                    if crest_dir.exists():
                        # Procura por arquivos com padrão crest_*.xyz
                        crest_files = list(crest_dir.glob("crest_*.xyz"))
                        logging.info(f"Arquivos encontrados no diretório CREST: {crest_files}")
                        
                        # Tenta copiar qualquer arquivo encontrado
                        for file in crest_files:
                            dest_path = molecule_output_dir / file.name
                            self.copy_file(str(file), dest_path)
                            logging.info(f"Arquivo copiado como alternativa: {file} -> {dest_path}")
                except Exception as search_error:
                    logging.error(f"Erro ao procurar arquivos alternativos: {search_error}")
                
            # Lista os arquivos no diretório final para verificação
            try:
                final_files = list(molecule_output_dir.glob("*"))
                logging.info(f"Arquivos finais no diretório {molecule_output_dir}: {[f.name for f in final_files]}")
            except Exception as e:
                logging.error(f"Erro ao listar arquivos finais: {e}")
                
        except Exception as e:
            logging.error(f"Erro ao mover arquivos de saída: {e}")
            print(f"Erro ao mover arquivos de saída para {molecule.name}. Veja o log para mais detalhes.")

    def generate_summary(self, molecules: list[Molecule], output_file: str = "summary.txt"):
        """
        Gera um arquivo de resumo com informações sobre as moléculas processadas.
        """
        try:
            with open(output_file, "w") as f:
                f.write("Resumo dos cálculos de busca conformacional e entalpia:\n\n")
                f.write(f"{'Molécula':<15} {'CID':<8} {'CREST':<10} {'MOPAC':<10} {'Entalpia':<20}\n")
                f.write("-" * 63 + "\n")
                
                for molecule in molecules:
                    # Verifica status dos arquivos nos diretórios corretos
                    crest_dir = CREST_DIR / molecule.name
                    mopac_dir = MOPAC_DIR / molecule.name
                    
                    # Status do CREST
                    crest_status = "Concluído"
                    if not (crest_dir / CREST_CONFORMERS_FILE).exists() or not (crest_dir / CREST_BEST_FILE).exists():
                        crest_status = "Incompleto"
                    
                    # Status do MOPAC
                    mopac_status = "Concluído"
                    if not (mopac_dir / f"{molecule.name}.out").exists() or not (mopac_dir / f"{molecule.name}.arc").exists():
                        mopac_status = "Incompleto"
                    
                    # Informação de entalpia
                    entalpia = "N/A"
                    if hasattr(molecule, 'enthalpy_formation_mopac') and molecule.enthalpy_formation_mopac is not None:
                        entalpia = f"{molecule.enthalpy_formation_mopac}"
                    
                    f.write(f"{molecule.name:<15} {molecule.pubchem_cid or 'N/A':<8} {crest_status:<10} {mopac_status:<10} {entalpia:<20}\n")
                
                # Adiciona informações sobre os métodos utilizados
                f.write("\n\nDetalhes do cálculo:\n")
                f.write(f"- Método CREST: {molecules[0].settings.calculation_params.crest_method if hasattr(molecules[0], 'settings') else 'gfn2'}\n")
                f.write(f"- Método MOPAC: {molecules[0].settings.mopac_keywords.split()[0] if hasattr(molecules[0], 'settings') and hasattr(molecules[0].settings, 'mopac_keywords') else 'PM7'}\n")
                f.write(f"- Data do cálculo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            logging.info(f"Arquivo de resumo gerado: {output_file}")
            print(f"Arquivo de resumo gerado: {output_file}")
        except Exception as e:
            logging.error(f"Erro ao gerar arquivo de resumo: {e}")
            print(f"Erro ao gerar arquivo de resumo. Veja o log para mais detalhes.")