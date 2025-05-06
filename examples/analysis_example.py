# examples/analysis_example.py
"""
Este exemplo demonstra como usar o módulo de análise de confôrmeros
diretamente a partir de um script Python, sem usar a interface CLI.
"""

import sys
import os
import logging
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PATH
sys.path.append(str(Path(__file__).parent.parent))

from services.analysis.conformer_analyzer import ConformerAnalyzer

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    """Função principal para demonstrar o uso do analisador de confôrmeros."""
    
    # Cria uma instância do analisador
    analyzer = ConformerAnalyzer()
    
    # EXEMPLO 1: Analisar uma molécula específica
    print("EXEMPLO 1: Análise de uma molécula específica")
    print("=" * 50)
    
    # Substitua "benzeno" pelo nome de uma molécula que você já processou
    molecule_name = "benzeno"
    
    # Obtém estatísticas dos confôrmeros
    stats = analyzer.get_conformer_statistics(molecule_name)
    
    if not stats or not stats.get('success', False):
        print(f"Não foi possível analisar a molécula {molecule_name}.")
        print("Verifique se a busca conformacional foi concluída e se o nome está correto.")
    else:
        # Exibe informações básicas
        print(f"Molécula: {molecule_name}")
        print(f"Número de confôrmeros: {stats.get('num_conformers', 'N/A')}")
        
        # Exibe informações sobre átomos, se disponíveis
        if 'atom_counts' in stats:
            print("\nComposição Atômica:")
            print(f"Total de átomos: {stats.get('total_atoms', 'N/A')}")
            for atom, count in sorted(stats['atom_counts'].items()):
                print(f"  {atom}: {count}")
        
        # Exibe informações sobre energias
        if 'relative_energies' in stats and stats['relative_energies']:
            print("\nEstatísticas de Energia:")
            print(f"Faixa de energia: 0.00 - {max(stats['relative_energies']):.2f} kcal/mol")
            print(f"Energia média: {stats.get('energy_mean', 'N/A'):.2f} kcal/mol")
            print(f"Desvio padrão: {stats.get('energy_std', 'N/A'):.2f} kcal/mol")
            
            # Mostra os 3 confôrmeros mais estáveis
            print("\nConfôrmeros Mais Estáveis:")
            print(f"{'#':<3} {'E. Rel. (kcal/mol)':<20} {'População (%)':<15}")
            for i in range(min(3, len(stats['relative_energies']))):
                print(f"{i+1:<3} {stats['relative_energies'][i]:<20.2f} {stats['populations'][i]:<15.2f}")
        
        # Exibe distribuição de energia
        energy_dist = analyzer.generate_energy_distribution(molecule_name)
        if energy_dist:
            print("\nDistribuição de Energia:")
            print(energy_dist)
    
    # EXEMPLO 2: Analisar todas as moléculas calculadas
    print("\n\nEXEMPLO 2: Análise de todas as moléculas")
    print("=" * 50)
    
    all_molecules = analyzer.analyze_all_molecules()
    
    if not all_molecules:
        print("Nenhuma molécula encontrada com resultados de busca conformacional.")
    else:
        print(f"Total de moléculas analisadas: {len(all_molecules)}")
        print(f"\n{'Molécula':<20} {'Confôrmeros':<12} {'E. Máx. (kcal/mol)':<20} {'Átomos':<8}")
        print("-" * 65)
        
        for stats in all_molecules:
            molecule_name = stats['molecule_name']
            num_conformers = stats.get('num_conformers', 'N/A') if stats.get('success', False) else 'N/A'
            max_energy = f"{max(stats['relative_energies']):.2f}" if stats.get('success', False) and 'relative_energies' in stats and stats['relative_energies'] else 'N/A'
            total_atoms = stats.get('total_atoms', 'N/A')
            
            print(f"{molecule_name:<20} {num_conformers:<12} {max_energy:<20} {total_atoms:<8}")
    
    print("\nExemplo concluído.")

if __name__ == "__main__":
    main()
