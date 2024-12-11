# run_tests.py
import subprocess
import sys
import os
from pathlib import Path
import argparse

def setup_python_path():
    """Adiciona o diretório do projeto ao PYTHONPATH."""
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    os.environ['PYTHONPATH'] = str(project_root)

def run_tests(verbose=False, coverage=False, html_report=False, test_file=None):
    """Executa os testes com as opções especificadas."""
    
    # Adicionar diretório ao PYTHONPATH
    setup_python_path()
    
    # Construir o comando base
    cmd = ["pytest"]
    
    # Adicionar opções
    if verbose:
        cmd.append("-v")
        
    if coverage:
        cmd.append("--cov=src")
        if html_report:
            cmd.append("--cov-report=html")
        else:
            cmd.append("--cov-report=term-missing")
            
    # Adicionar arquivo específico se fornecido
    if test_file:
        cmd.append(str(test_file))
    
    # Configurar ambiente para o subprocess
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path(__file__).parent.parent)
    
    # Executar os testes
    try:
        subprocess.run(cmd, check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar testes: {e}")
        sys.exit(1)
        
    if html_report:
        print("\nRelatório HTML gerado em 'htmlcov/index.html'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executa testes do projeto")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mostra saída detalhada")
    parser.add_argument("-c", "--coverage", action="store_true", help="Mostra cobertura de código")
    parser.add_argument("--html", action="store_true", help="Gera relatório de cobertura em HTML")
    parser.add_argument("-f", "--file", type=str, help="Arquivo de teste específico para executar")
    
    args = parser.parse_args()
    
    run_tests(
        verbose=args.verbose,
        coverage=args.coverage,
        html_report=args.html,
        test_file=args.file if args.file else None
    )