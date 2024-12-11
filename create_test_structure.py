# create_test_structure.py
from pathlib import Path

def create_test_structure():
    # Criar diretório de testes
    test_dir = Path("tests")
    test_dir.mkdir(exist_ok=True)
    
    # Criar subdiretório de dados
    data_dir = test_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Criar arquivo __init__.py
    init_file = test_dir / "__init__.py"
    init_file.touch()
    
    print("Estrutura de testes criada com sucesso!")

if __name__ == "__main__":
    create_test_structure()