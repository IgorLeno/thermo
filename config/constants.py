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
PDB_DIR = REPOSITORY_DIR / "pdb"
DAT_DIR = REPOSITORY_DIR / "dat"
MOPAC_DIR = REPOSITORY_DIR / "mopac"

# Subdiretórios de PROGRAMS_DIR
OPENBABEL_DIR = PROGRAMS_DIR / "OpenBabel"
CREST_PROGRAM_DIR = PROGRAMS_DIR / "crest"
MOPAC_PROGRAM_DIR = PROGRAMS_DIR / "MOPAC"

# Subdiretórios de FINAL_MOLECULES_DIR
OUTPUT_DIR = FINAL_MOLECULES_DIR / "output"

# Arquivos CREST
CREST_CONFORMERS_FILE = "crest_conformers.xyz"
CREST_BEST_FILE = "crest_best.xyz"
CREST_LOG_FILE = "crest.out"
CREST_ENSEMBLE_FILE = ".crest_ensemble"
CREST_ENERGIES_FILE = "crest.energies"
CREST_ROTAMERS_FILE = "crest_rotamers.xyz"

# Arquivos MOPAC
MOPAC_INPUT_FILE = "{molecule_name}.dat"
MOPAC_OUTPUT_FILE = "{molecule_name}.out"
MOPAC_ARC_FILE = "{molecule_name}.arc"