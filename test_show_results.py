#!/usr/bin/env python3
# Teste específico para show_results

import logging
from interfaces.cli import CommandLineInterface

# Configura logging para debugging
logging.basicConfig(level=logging.ERROR)

print("=== Teste da opção 4 (Exibir Resultados) ===\n")

# Cria a interface
cli = CommandLineInterface()

# Testa a função show_results
cli.show_results()

print("\n=== Teste Concluído ===")
