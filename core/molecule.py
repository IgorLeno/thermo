from dataclasses import dataclass, field
from typing import List, Optional

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
    xtb_opt_path: Optional[str] = None
    hessian_path: Optional[str] = None
    vibspectrum_path: Optional[str] = None
    thermochemistry_path: Optional[str] = None
    formation_enthalpy: Optional[float] = None
    conformer_energies: List[float] = field(default_factory=list)

    def __str__(self):
        return f"Molecule(name={self.name}, cid={self.pubchem_cid})"