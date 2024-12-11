import os
import shutil
import glob
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

    def clear_directory(self, directory: str):
        """Remove todos os arquivos e subdiretórios de um diretório."""
        for root, dirs, files in os.walk(directory, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))

    def copy_file(self, source: str, destination: str):
        """Copia um arquivo de source para destination."""
        shutil.copy(source, destination)

    def move_file(self, source: str, destination: str):
        """Move um arquivo de source para destination."""
        shutil.move(source, destination)

    def file_exists(self, filepath: str) -> bool:
        """Verifica se um arquivo existe."""
        return os.path.exists(filepath)
    
    def move_output_files(self, molecule: Molecule):
        """
        Move os arquivos de saída relevantes para o diretório final de resultados.
        """
        molecule_output_dir = OUTPUT_DIR / molecule.name
        self.create_directory(molecule_output_dir)

        # Move o arquivo xtbopt.xyz
        if molecule.xtb_opt_path:
            self.move_file(molecule.xtb_opt_path, molecule_output_dir / XTBOPT_FILE)

        # Move o arquivo crest_best.xyz
        if molecule.crest_best_path:
            self.move_file(molecule.crest_best_path, molecule_output_dir / CREST_BEST_FILE)

        # Move o arquivo crest_conformers.xyz
        if molecule.crest_conformers_path:
            self.move_file(molecule.crest_conformers_path, molecule_output_dir / CREST_CONFORMERS_FILE)

        # Move o arquivo xtbhess.log (ou thermochemistry)
        if molecule.thermochemistry_path:
            self.move_file(molecule.thermochemistry_path, molecule_output_dir / THERMOCHEMISTRY_FILE)

        # Move o arquivo g98.out
        xtb_output_dir = XTB_DIR / molecule.name
        g98_file_path = xtb_output_dir / G98_FILE
        if g98_file_path.exists():
            self.move_file(g98_file_path, molecule_output_dir / G98_FILE)

        # Move os arquivos hessian e vibspectrum
        if molecule.hessian_path:
            self.move_file(molecule.hessian_path, molecule_output_dir / HESSIAN_FILE)
        if molecule.vibspectrum_path:
            self.move_file(molecule.vibspectrum_path, molecule_output_dir / VIB_SPECTRUM_FILE)

    def generate_summary(self, molecules: list[Molecule], output_file: str = "summary.txt"):
        """
        Gera um arquivo de resumo com os resultados de todas as moléculas processadas.
        """
        with open(output_file, "w") as f:
            f.write("Resumo dos cálculos de entalpia de formação:\n\n")
            f.write(f"{'Molécula':<20} {'Entalpia de Formação (kcal/mol)':<35}\n")
            f.write("-" * 55 + "\n")
            for molecule in molecules:
                f.write(f"{molecule.name:<20} {molecule.formation_enthalpy:<35.2f}\n")