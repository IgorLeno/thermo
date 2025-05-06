# interfaces/analysis_cli.py
import os
import logging
from pathlib import Path
from typing import List, Optional
from services.analysis.conformer_analyzer import ConformerAnalyzer
from config.constants import OUTPUT_DIR

class AnalysisInterface:
    """
    Interface para análise dos resultados da busca conformacional.
    """
    
    def __init__(self):
        """Inicializa a interface de análise."""
        self.conformer_analyzer = ConformerAnalyzer()
        
    def run(self):
        """Executa a interface de análise."""
        while True:
            print("\n===== Análise de Confôrmeros =====")
            print("1. Analisar uma molécula específica")
            print("2. Listar todas as moléculas calculadas")
            print("3. Gerar relatório completo de análise")
            print("4. Comparar múltiplas moléculas")
            print("5. Voltar ao menu principal")
            
            choice = input("\nEscolha uma opção: ")
            
            if choice == "1":
                self._analyze_specific_molecule()
            elif choice == "2":
                self._list_all_molecules()
            elif choice == "3":
                self._generate_full_report()
            elif choice == "4":
                self._compare_molecules()
            elif choice == "5":
                break
            else:
                print("Opção inválida. Tente novamente.")
    
    def _analyze_specific_molecule(self):
        """Analisa uma molécula específica."""
        molecule_name = input("Digite o nome da molécula: ")
        
        # Verifica se a molécula existe
        molecule_dir = OUTPUT_DIR / molecule_name
        if not molecule_dir.exists() or not molecule_dir.is_dir():
            print(f"Molécula '{molecule_name}' não encontrada. Verifique o nome e tente novamente.")
            return
        
        print(f"\nAnalisando molécula: {molecule_name}")
        
        # Obtém estatísticas dos confôrmeros
        stats = self.conformer_analyzer.get_conformer_statistics(molecule_name)
        
        if not stats or not stats.get('success', False):
            print(f"Não foi possível analisar a molécula {molecule_name}. Verifique se a busca conformacional foi concluída.")
            return
        
        # Exibe informações básicas
        print("\n----- Informações Básicas -----")
        print(f"Molécula: {molecule_name}")
        print(f"Número de confôrmeros: {stats.get('num_conformers', 'N/A')}")
        
        # Exibe informações sobre átomos, se disponíveis
        if 'atom_counts' in stats:
            print("\n----- Composição Atômica -----")
            print(f"Total de átomos: {stats.get('total_atoms', 'N/A')}")
            print("Distribuição de átomos:")
            for atom, count in sorted(stats['atom_counts'].items()):
                print(f"  {atom}: {count}")
        
        # Exibe informações sobre energias
        if 'relative_energies' in stats:
            print("\n----- Estatísticas de Energia -----")
            print(f"Faixa de energia: 0.00 - {max(stats['relative_energies']):.2f} kcal/mol")
            print(f"Energia média: {stats.get('energy_mean', 'N/A'):.2f} kcal/mol")
            print(f"Desvio padrão: {stats.get('energy_std', 'N/A'):.2f} kcal/mol")
            
            # Mostra os 5 confôrmeros mais estáveis
            print("\n----- Confôrmeros Mais Estáveis -----")
            print(f"{'#':<3} {'E. Rel. (kcal/mol)':<20} {'População (%)':<15}")
            for i in range(min(5, len(stats['relative_energies']))):
                print(f"{i+1:<3} {stats['relative_energies'][i]:<20.2f} {stats['populations'][i]:<15.2f}")
        
        # Exibe distribuição de energia
        energy_dist = self.conformer_analyzer.generate_energy_distribution(molecule_name)
        if energy_dist:
            print("\n----- Distribuição de Energia -----")
            print(energy_dist)
        
        # Opção para salvar o relatório
        if input("\nDeseja salvar este relatório em um arquivo? (s/n): ").lower() == 's':
            filename = input("Digite o nome do arquivo (padrão: análise_{molécula}.txt): ")
            if not filename:
                filename = f"análise_{molecule_name}.txt"
            
            with open(filename, 'w') as f:
                f.write(f"Análise de Confôrmeros para {molecule_name}\n")
                f.write("=" * 50 + "\n\n")
                
                f.write("----- Informações Básicas -----\n")
                f.write(f"Molécula: {molecule_name}\n")
                f.write(f"Número de confôrmeros: {stats.get('num_conformers', 'N/A')}\n\n")
                
                if 'atom_counts' in stats:
                    f.write("----- Composição Atômica -----\n")
                    f.write(f"Total de átomos: {stats.get('total_atoms', 'N/A')}\n")
                    f.write("Distribuição de átomos:\n")
                    for atom, count in sorted(stats['atom_counts'].items()):
                        f.write(f"  {atom}: {count}\n")
                    f.write("\n")
                
                if 'relative_energies' in stats:
                    f.write("----- Estatísticas de Energia -----\n")
                    f.write(f"Faixa de energia: 0.00 - {max(stats['relative_energies']):.2f} kcal/mol\n")
                    f.write(f"Energia média: {stats.get('energy_mean', 'N/A'):.2f} kcal/mol\n")
                    f.write(f"Desvio padrão: {stats.get('energy_std', 'N/A'):.2f} kcal/mol\n\n")
                    
                    f.write("----- Confôrmeros Mais Estáveis -----\n")
                    f.write(f"{'#':<3} {'E. Rel. (kcal/mol)':<20} {'População (%)':<15}\n")
                    for i in range(min(5, len(stats['relative_energies']))):
                        f.write(f"{i+1:<3} {stats['relative_energies'][i]:<20.2f} {stats['populations'][i]:<15.2f}\n")
                    f.write("\n")
                
                if energy_dist:
                    f.write("----- Distribuição de Energia -----\n")
                    f.write(energy_dist)
            
            print(f"Relatório salvo em {filename}")
    
    def _list_all_molecules(self):
        """Lista todas as moléculas com resultados de busca conformacional."""
        if not OUTPUT_DIR.exists():
            print("Nenhum resultado encontrado. Execute a busca conformacional primeiro.")
            return
        
        molecule_dirs = [d for d in OUTPUT_DIR.iterdir() if d.is_dir()]
        
        if not molecule_dirs:
            print("Nenhum resultado encontrado. Execute a busca conformacional primeiro.")
            return
        
        print(f"\nEncontradas {len(molecule_dirs)} moléculas com resultados:")
        print(f"{'Nome':<20} {'Confôrmeros':<15} {'Energia Máx.':<15} {'Átomos':<10}")
        print("-" * 60)
        
        for molecule_dir in molecule_dirs:
            molecule_name = molecule_dir.name
            stats = self.conformer_analyzer.get_conformer_statistics(molecule_name)
            
            num_conformers = stats.get('num_conformers', 'N/A') if stats and stats.get('success', False) else 'N/A'
            max_energy = f"{max(stats['relative_energies']):.2f}" if stats and 'relative_energies' in stats and stats['relative_energies'] else 'N/A'
            total_atoms = stats.get('total_atoms', 'N/A') if stats else 'N/A'
            
            print(f"{molecule_name:<20} {num_conformers:<15} {max_energy:<15} {total_atoms:<10}")
    
    def _generate_full_report(self):
        """Gera um relatório completo de análise para todas as moléculas."""
        molecules = self.conformer_analyzer.analyze_all_molecules()
        
        if not molecules:
            print("Nenhum resultado encontrado. Execute a busca conformacional primeiro.")
            return
        
        filename = input("Digite o nome do arquivo para o relatório (padrão: relatório_conformacional.txt): ")
        if not filename:
            filename = "relatório_conformacional.txt"
        
        with open(filename, 'w') as f:
            f.write("Relatório de Análise Conformacional\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Moléculas analisadas: {len(molecules)}\n\n")
            
            # Tabela resumo
            f.write("Resumo das Moléculas:\n")
            f.write(f"{'Molécula':<20} {'Confôrmeros':<15} {'Energia Máx.':<15} {'Átomos':<10}\n")
            f.write("-" * 60 + "\n")
            
            for stats in molecules:
                molecule_name = stats['molecule_name']
                num_conformers = stats.get('num_conformers', 'N/A') if stats.get('success', False) else 'N/A'
                max_energy = f"{max(stats['relative_energies']):.2f}" if 'relative_energies' in stats and stats['relative_energies'] else 'N/A'
                total_atoms = stats.get('total_atoms', 'N/A')
                
                f.write(f"{molecule_name:<20} {num_conformers:<15} {max_energy:<15} {total_atoms:<10}\n")
            
            f.write("\n\n")
            
            # Detalhes para cada molécula
            for stats in molecules:
                if not stats.get('success', False):
                    continue
                    
                molecule_name = stats['molecule_name']
                
                f.write(f"Análise Detalhada: {molecule_name}\n")
                f.write("-" * 50 + "\n")
                
                # Informações básicas
                f.write(f"Número de confôrmeros: {stats.get('num_conformers', 'N/A')}\n")
                
                # Composição atômica
                if 'atom_counts' in stats:
                    f.write("\nComposição Atômica:\n")
                    f.write(f"Total de átomos: {stats.get('total_atoms', 'N/A')}\n")
                    for atom, count in sorted(stats['atom_counts'].items()):
                        f.write(f"  {atom}: {count}\n")
                
                # Estatísticas de energia
                if 'relative_energies' in stats:
                    f.write("\nEstatísticas de Energia:\n")
                    f.write(f"Faixa de energia: 0.00 - {max(stats['relative_energies']):.2f} kcal/mol\n")
                    f.write(f"Energia média: {stats.get('energy_mean', 'N/A'):.2f} kcal/mol\n")
                    f.write(f"Desvio padrão: {stats.get('energy_std', 'N/A'):.2f} kcal/mol\n")
                
                # Confôrmeros mais estáveis
                if 'relative_energies' in stats:
                    f.write("\nConfôrmeros Mais Estáveis:\n")
                    f.write(f"{'#':<3} {'E. Rel. (kcal/mol)':<20} {'População (%)':<15}\n")
                    for i in range(min(10, len(stats['relative_energies']))):
                        f.write(f"{i+1:<3} {stats['relative_energies'][i]:<20.2f} {stats['populations'][i]:<15.2f}\n")
                
                f.write("\n" + "=" * 50 + "\n\n")
            
            # Estatísticas comparativas
            if len(molecules) > 1:
                f.write("Análise Comparativa\n")
                f.write("-" * 50 + "\n")
                
                # Molécula com mais confôrmeros
                molecules_with_conformers = [m for m in molecules if m.get('success', False) and 'num_conformers' in m]
                if molecules_with_conformers:
                    most_conformers = max(molecules_with_conformers, key=lambda x: x['num_conformers'])
                    f.write(f"Molécula com mais confôrmeros: {most_conformers['molecule_name']} ({most_conformers['num_conformers']})\n")
                
                # Molécula com maior faixa de energia
                molecules_with_energies = [m for m in molecules if m.get('success', False) and 'energy_range' in m]
                if molecules_with_energies:
                    highest_range = max(molecules_with_energies, key=lambda x: x['energy_range'])
                    f.write(f"Molécula com maior faixa de energia: {highest_range['molecule_name']} ({highest_range['energy_range']:.2f} kcal/mol)\n")
                
                # Molécula com mais átomos
                molecules_with_atoms = [m for m in molecules if 'total_atoms' in m]
                if molecules_with_atoms:
                    most_atoms = max(molecules_with_atoms, key=lambda x: x['total_atoms'])
                    f.write(f"Molécula com mais átomos: {most_atoms['molecule_name']} ({most_atoms['total_atoms']})\n")
        
        print(f"Relatório completo gerado em {filename}")
    
    def _compare_molecules(self):
        """Compara estatísticas entre múltiplas moléculas."""
        if not OUTPUT_DIR.exists():
            print("Nenhum resultado encontrado. Execute a busca conformacional primeiro.")
            return
        
        molecule_dirs = [d for d in OUTPUT_DIR.iterdir() if d.is_dir()]
        
        if not molecule_dirs:
            print("Nenhum resultado encontrado. Execute a busca conformacional primeiro.")
            return
        
        # Lista as moléculas disponíveis
        print("\nMoléculas disponíveis para comparação:")
        for i, molecule_dir in enumerate(molecule_dirs, 1):
            print(f"{i}. {molecule_dir.name}")
        
        # Solicita a seleção das moléculas
        selection = input("\nDigite os números das moléculas a comparar, separados por vírgula: ")
        try:
            indices = [int(idx.strip()) - 1 for idx in selection.split(",")]
            selected_molecules = [molecule_dirs[idx].name for idx in indices if 0 <= idx < len(molecule_dirs)]
        except (ValueError, IndexError):
            print("Seleção inválida.")
            return
        
        if not selected_molecules or len(selected_molecules) < 2:
            print("Selecione pelo menos duas moléculas para comparação.")
            return
        
        print(f"\nComparando {len(selected_molecules)} moléculas:")
        for molecule in selected_molecules:
            print(f"- {molecule}")
        
        # Coleta estatísticas das moléculas selecionadas
        molecule_stats = []
        for molecule_name in selected_molecules:
            stats = self.conformer_analyzer.get_conformer_statistics(molecule_name)
            if stats and stats.get('success', False):
                molecule_stats.append(stats)
            else:
                print(f"Não foi possível analisar {molecule_name}. Excluindo da comparação.")
        
        if len(molecule_stats) < 2:
            print("Número insuficiente de moléculas válidas para comparação.")
            return
        
        # Exibe tabela comparativa
        print("\n----- Comparação de Moléculas -----")
        print(f"{'Molécula':<20} {'Confôrmeros':<12} {'E. Máx.':<10} {'E. Média':<10} {'Átomos':<8}")
        print("-" * 65)
        
        for stats in molecule_stats:
            molecule_name = stats['molecule_name']
            num_conformers = stats.get('num_conformers', 'N/A')
            max_energy = f"{max(stats['relative_energies']):.2f}" if 'relative_energies' in stats and stats['relative_energies'] else 'N/A'
            mean_energy = f"{stats.get('energy_mean', 0):.2f}" if 'energy_mean' in stats else 'N/A'
            total_atoms = stats.get('total_atoms', 'N/A')
            
            print(f"{molecule_name:<20} {num_conformers:<12} {max_energy:<10} {mean_energy:<10} {total_atoms:<8}")
        
        # Análise comparativa
        print("\n----- Análise Comparativa -----")
        
        # Molécula com mais confôrmeros
        most_conformers = max(molecule_stats, key=lambda x: x.get('num_conformers', 0))
        print(f"Molécula com mais confôrmeros: {most_conformers['molecule_name']} ({most_conformers.get('num_conformers', 'N/A')})")
        
        # Molécula com maior faixa de energia
        molecules_with_range = [m for m in molecule_stats if 'energy_range' in m]
        if molecules_with_range:
            highest_range = max(molecules_with_range, key=lambda x: x['energy_range'])
            print(f"Molécula com maior faixa de energia: {highest_range['molecule_name']} ({highest_range['energy_range']:.2f} kcal/mol)")
        
        # Molécula com maior energia média relativa
        molecules_with_mean = [m for m in molecule_stats if 'energy_mean' in m]
        if molecules_with_mean:
            highest_mean = max(molecules_with_mean, key=lambda x: x['energy_mean'])
            print(f"Molécula com maior energia média: {highest_mean['molecule_name']} ({highest_mean['energy_mean']:.2f} kcal/mol)")
        
        # Molécula com mais átomos
        molecules_with_atoms = [m for m in molecule_stats if 'total_atoms' in m]
        if molecules_with_atoms:
            most_atoms = max(molecules_with_atoms, key=lambda x: x['total_atoms'])
            print(f"Molécula com mais átomos: {most_atoms['molecule_name']} ({most_atoms['total_atoms']})")
