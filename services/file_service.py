import os
import shutil
import glob
import logging
from pathlib import Path
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
                f.write("Resumo da busca conformacional:\n\n")
                f.write(f"{'Molécula':<20} {'CID':<10} {'Arquivo de Confôrmeros':<40} {'Status':<15}\n")
                f.write("-" * 85 + "\n")
                for molecule in molecules:
                    conf_path = os.path.basename(molecule.crest_conformers_path) if molecule.crest_conformers_path else "N/A"
                    
                    # Verifica se os arquivos existem no diretório final
                    final_dir = OUTPUT_DIR / molecule.name
                    status = "Concluído"
                    if not (final_dir / CREST_CONFORMERS_FILE).exists() or not (final_dir / CREST_BEST_FILE).exists():
                        status = "Incompleto"
                    
                    f.write(f"{molecule.name:<20} {molecule.pubchem_cid or 'N/A':<10} {conf_path:<40} {status:<15}\n")
            
            logging.info(f"Arquivo de resumo gerado: {output_file}")
            print(f"Arquivo de resumo gerado: {output_file}")
        except Exception as e:
            logging.error(f"Erro ao gerar arquivo de resumo: {e}")
            print(f"Erro ao gerar arquivo de resumo. Veja o log para mais detalhes.")