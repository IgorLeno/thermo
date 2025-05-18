from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path

@dataclass
class Molecule:
    """
    Representa uma molécula e armazena seus dados.
    """
    name: str
    pubchem_cid: Optional[int] = None
    sdf_path: Optional[str] = None
    xyz_path: Optional[str] = None
    crest_conformers_path: Optional[str] = None
    crest_best_path: Optional[str] = None
    crest_output_dir: Optional[str] = None
    conformer_energies: List[float] = field(default_factory=list)
    
    # Campos para a etapa MOPAC
    converted_pdb_path: Optional[Path] = None  # Ex: repository/pdb/ethanol.pdb
    mopac_input_dat_path: Optional[Path] = None  # Ex: repository/mopac/ethanol/ethanol.dat
    mopac_output_directory: Optional[Path] = None  # Ex: repository/mopac/ethanol/
    mopac_output_log_path: Optional[Path] = None  # Ex: repository/mopac/ethanol/ethanol.out
    enthalpy_formation_mopac: Optional[float] = None  # Entalpia em kcal/mol
    enthalpy_formation_mopac_kj: Optional[float] = None  # Entalpia em kJ/mol

    def __str__(self):
        return f"Molecule(name={self.name})"
        
    @property
    def path_to_crest_best_xyz(self) -> Optional[Path]:
        """Retorna o caminho para o arquivo crest_best.xyz."""
        return Path(self.crest_best_path) if self.crest_best_path else None
        
    @property
    def path_to_mopac_out(self) -> Optional[Path]:
        """Retorna o caminho para o arquivo de saída do MOPAC."""
        return self.mopac_output_directory / f"{self.name}.out" if self.mopac_output_directory and self.name else None
    
    @property
    def path_to_mopac_arc(self) -> Optional[Path]:
        """Retorna o caminho para o arquivo .arc do MOPAC."""
        return self.mopac_output_directory / f"{self.name}.arc" if self.mopac_output_directory and self.name else None
        
    def set_mopac_results(self, pdb_path: Path, dat_path: Path, output_dir: Path, enthalpy: tuple):
        """
        Define os resultados do cálculo MOPAC.
        
        Args:
            pdb_path: Caminho para o arquivo PDB usado como entrada
            dat_path: Caminho para o arquivo .dat gerado
            output_dir: Diretório onde os arquivos de saída do MOPAC foram salvos
            enthalpy: Tupla contendo (entalpia_kcal_mol, entalpia_kj_mol)
        """
        self.converted_pdb_path = pdb_path
        self.mopac_input_dat_path = dat_path
        self.mopac_output_directory = output_dir
        
        # Verifica qual arquivo .out usar
        mopac_out_path = output_dir / f"{self.name}.out"
        if not mopac_out_path.exists():
            # Tenta o caminho no diretório MOPAC program
            from config.constants import MOPAC_PROGRAM_DIR
            alternate_out = Path(MOPAC_PROGRAM_DIR) / f"{self.name}.out"
            if alternate_out.exists():
                self.mopac_output_log_path = alternate_out
            else:
                self.mopac_output_log_path = mopac_out_path
        else:
            self.mopac_output_log_path = mopac_out_path
            
        # Armazena os dois valores de entalpia
        if enthalpy and isinstance(enthalpy, tuple) and len(enthalpy) == 2:
            self.enthalpy_formation_mopac = enthalpy[0]  # kcal/mol
            self.enthalpy_formation_mopac_kj = enthalpy[1]  # kJ/mol
        else:
            self.enthalpy_formation_mopac = None
            self.enthalpy_formation_mopac_kj = None