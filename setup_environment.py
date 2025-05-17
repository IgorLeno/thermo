import os
import sys
import logging
import shutil
from pathlib import Path
import yaml

def create_directory_structure():
    """Cria a estrutura de diretórios para o projeto."""

    directories = [
        "core",
        "config",
        "services",
        "services/analysis",
        "interfaces",
        "utils",
        "logs",
        "final_molecules/output",
        "programs/crest",
        "programs/OpenBabel",
        "programs/MOPAC",
        "repository/sdf",
        "repository/xyz",
        "repository/crest",
        "repository/pdb",
        "repository/mopac",
        "tests",
        "examples/molecules"
    ]

    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"Diretório criado: {directory}")
        except OSError as e:
            print(f"Erro ao criar diretório {directory}: {e}")

def create_empty_files(directory):
    """Cria arquivos __init__.py vazios nos diretórios especificados."""

    for root, dirs, files in os.walk(directory):
        # Ignorar diretórios específicos
        if any(excluded_dir in root for excluded_dir in ['.git', '.vscode', '.idea', 'venv', '__pycache__']):
            continue
            
        # Ignorar diretórios do programs, repository, final_molecules e logs
        if any(repo_dir in root for repo_dir in ['programs', 'repository', 'final_molecules', 'logs', 'examples']):
            if root.endswith(('programs', 'repository', 'final_molecules', 'logs', 'examples')):
                # Criar apenas no diretório raiz desses
                if "__init__.py" not in files:
                    with open(os.path.join(root, "__init__.py"), "w") as f:
                        pass
                    print(f"Arquivo __init__.py criado em: {root}")
            continue
            
        if "__init__.py" not in files:
            with open(os.path.join(root, "__init__.py"), "w") as f:
                pass
            print(f"Arquivo __init__.py criado em: {root}")

def create_default_config():
    """Cria ou atualiza o arquivo de configuração padrão se não existir."""
    config_file = "config.yaml"
    
    # Se o arquivo já existir, não sobrescrever
    if os.path.exists(config_file):
        print(f"Arquivo de configuração {config_file} já existe. Não será sobrescrito.")
        return
    
    default_config = {
        "calculation_parameters": {
            "n_threads": 4,
            "crest_method": "gfn2",
            "electronic_temperature": 300.0,
            "solvent": None
        },
        "programs": {
            "openbabel_path": "obabel",
            "crest_path": "crest",
            "mopac_path": "MOPAC2016.exe"
        },
        "mopac_params": {
            "keywords": "PM7 EF PRECISE GNORM=0.01 NOINTER GRAPHF VECTORS MMOK CYCLES=20000"
        },
        "supabase": {
            "enabled": False,
            "url": "",
            "key": "",
            "storage": {
                "enabled": False,
                "molecules_bucket": "molecule-files"
            }
        }
    }
    
    with open(config_file, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
    
    print(f"Arquivo de configuração padrão criado: {config_file}")

def setup_logging():
    """Configura o sistema de logging."""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    print(f"Sistema de logging configurado. Logs serão salvos em: {log_dir}")

def copy_example_files():
    """Copia arquivos de exemplo para o diretório de exemplos."""
    example_molecules = [
        {"name": "ethanol.xyz", "content": 
"""9
Ethanol
C          0.00000        0.00000        0.00000
H          0.00000        0.00000        1.09000
H          1.02800        0.00000       -0.36400
H         -0.51400       -0.89000       -0.36400
C         -0.66900        1.23000       -0.51300
H         -0.14100        2.13000       -0.17400
H         -0.67900        1.24000       -1.60300
O         -2.01100        1.25000       -0.05000
H         -2.42800        2.04000       -0.40800
"""},
        {"name": "acetone.xyz", "content": 
"""10
Acetone
C          0.00000        0.00000        0.00000
O          0.00000        0.00000        1.22000
C         -1.29000       -0.00000       -0.74000
H         -2.13000        0.00000       -0.05000
H         -1.33000       -0.88000       -1.38000
H         -1.33000        0.88000       -1.38000
C          1.29000        0.00000       -0.74000
H          1.33000       -0.88000       -1.38000
H          1.33000        0.88000       -1.38000
H          2.13000        0.00000       -0.05000
"""}
    ]
    
    examples_dir = Path("examples/molecules")
    os.makedirs(examples_dir, exist_ok=True)
    
    for molecule in example_molecules:
        file_path = examples_dir / molecule["name"]
        with open(file_path, 'w') as f:
            f.write(molecule["content"])
        print(f"Arquivo de exemplo criado: {file_path}")

def check_python_version():
    """Verifica se a versão do Python é compatível."""
    min_version = (3, 8)
    current_version = sys.version_info[:2]
    
    if current_version < min_version:
        print(f"AVISO: Este projeto requer Python {min_version[0]}.{min_version[1]} ou superior.")
        print(f"Você está usando Python {current_version[0]}.{current_version[1]}.")
        return False
    else:
        print(f"Versão do Python compatível: {current_version[0]}.{current_version[1]}")
        return True

def check_required_tools():
    """Verifica se as ferramentas externas estão disponíveis no sistema."""
    tools = {
        "OpenBabel": shutil.which("obabel"),
        "MOPAC": shutil.which("MOPAC2016.exe") or shutil.which("MOPAC2023.exe"),
        "WSL": shutil.which("wsl")
    }
    
    all_found = True
    print("\nVerificando ferramentas externas:")
    for tool, path in tools.items():
        if path:
            print(f"✓ {tool} encontrado: {path}")
        else:
            print(f"✗ {tool} não encontrado! Será necessário instalá-lo manualmente.")
            all_found = False
    
    if not all_found:
        print("\nALGUMAS FERRAMENTAS NECESSÁRIAS NÃO FORAM ENCONTRADAS!")
        print("Por favor, instale as ferramentas ausentes antes de usar o programa.")
        print("Consulte o README.md para instruções de instalação.")
    
    return all_found

def main():
    """Função principal para configurar o ambiente."""
    print("=== Configurando ambiente para Grimme Thermo ===\n")
    
    check_python_version()
    create_directory_structure()
    create_empty_files(".")
    create_default_config()
    copy_example_files()
    setup_logging()
    check_required_tools()
    
    print("\n=== Configuração do ambiente concluída! ===")
    print("Você pode agora instalar os programas externos usando:")
    print("  python setup_programs.py")
    print("\nE executar o programa principal com:")
    print("  python main.py")

if __name__ == "__main__":
    main()
