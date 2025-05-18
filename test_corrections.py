#!/usr/bin/env python3
# Teste para verificar se as correções funcionaram

import logging
from services.analysis.conformer_analyzer import ConformerAnalyzer

# Configura logging para debugging
logging.basicConfig(level=logging.INFO)

# Testa o analisador de confôrmeros
analyzer = ConformerAnalyzer()

# Testa as moléculas disponíveis
molecules = ["butanol", "ethanol", "propanol"]

print("=== Teste das Correções ===\n")

print("1. Testando get_best_conformer_energy:")
for mol in molecules:
    energy = analyzer.get_best_conformer_energy(mol)
    print(f"  {mol}: {energy}")

print("\n2. Testando get_heat_of_formation:")
for mol in molecules:
    hf = analyzer.get_heat_of_formation(mol)
    print(f"  {mol}: {hf} kJ/mol")

print("\n3. Testando get_conformer_energies:")
for mol in molecules:
    energies = analyzer.get_conformer_energies(mol)
    num_conf = energies.get('num_conformers', 'N/A') if energies else 'N/A'
    print(f"  {mol}: {num_conf} confôrmeros")

print("\n4. Testando análise completa:")
from interfaces.analysis_cli import AnalysisInterface

# Simula a listagem de moléculas
analyzer_interface = AnalysisInterface()
analyzer_interface._list_all_molecules()

print("\n=== Teste Concluído ===")
