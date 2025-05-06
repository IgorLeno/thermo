import os

def create_directory_structure():
    """Cria a estrutura de diretórios para o projeto."""

    directories = [
        "core",
        "config",
        "services",
        "interfaces",
        "utils",
        "final_molecules/output",
        "programs/crest",
        "programs/OpenBabel",
        "repository/sdf",
        "repository/xyz",
        "repository/crest",
        "tests"
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
        if "__init__.py" not in files:
            with open(os.path.join(root, "__init__.py"), "w") as f:
                pass
            print(f"Arquivo __init__.py criado em: {root}")

if __name__ == "__main__":
    create_directory_structure()
    create_empty_files(".")