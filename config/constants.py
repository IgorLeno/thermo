from pathlib import Path

# Diretórios principais
ROOT_DIR = Path(__file__).parent.parent
REPOSITORY_DIR = ROOT_DIR / "repository"
FINAL_MOLECULES_DIR = ROOT_DIR / "final_molecules"
PROGRAMS_DIR = ROOT_DIR / "programs"

# Subdiretórios de REPOSITORY_DIR
SDF_DIR = REPOSITORY_DIR / "sdf"
XYZ_DIR = REPOSITORY_DIR / "xyz"
CREST_DIR = REPOSITORY_DIR / "crest"
XTB_DIR = REPOSITORY_DIR / "xtb"

# Subdiretórios de PROGRAMS_DIR
OPENBABEL_DIR = PROGRAMS_DIR / "OpenBabel"
CREST_PROGRAM_DIR = PROGRAMS_DIR / "crest"
XTB_PROGRAM_DIR = PROGRAMS_DIR / "xtb"

# Subdiretórios de FINAL_MOLECULES_DIR
OUTPUT_DIR = FINAL_MOLECULES_DIR / "output"

# Arquivos
CREST_CONFORMERS_FILE = "crest_conformers.xyz"
CREST_BEST_FILE = "crest_best.xyz"
XTBOPT_FILE = "xtbopt.xyz"
HESSIAN_FILE = "hessian"
VIB_SPECTRUM_FILE = "vibspectrum"
THERMOCHEMISTRY_FILE = "xtbhess.log" # Ou "thermochemistry" dependendo da versão do xTB
G98_FILE = "g98.out"