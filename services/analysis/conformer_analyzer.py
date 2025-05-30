# services/analysis/conformer_analyzer.py
import os
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from core.molecule import Molecule
from config.constants import OUTPUT_DIR, CREST_DIR, CREST_ENERGIES_FILE, CREST_CONFORMERS_FILE

class ConformerAnalyzer:
    """
    Classe para analisar os resultados da busca conformacional com CREST.
    Fornece funcionalidades para extrair e analisar dados de energia e estrutura dos confôrmeros.
    """
    
    def __init__(self):
        """Inicializa o analisador de confôrmeros."""
        logging.info("Inicializando serviço de análise de confôrmeros")
    
    def get_conformer_energies(self, molecule_name: str) -> Optional[Dict]:
        """
        Lê o arquivo crest.energies e extrai as energias dos confôrmeros.
        
        Args:
            molecule_name: Nome da molécula a ser analisada.
            
        Returns:
            Um dicionário contendo dados de energia dos confôrmeros ou None se o arquivo não for encontrado.
            O dicionário inclui: 'energies', 'relative_energies', 'boltzmann_weights' e 'populations'.
        """
        try:
            # CORREÇÃO: Busca primeiro no diretório CREST (repository/crest)
            energy_file = CREST_DIR / molecule_name / CREST_ENERGIES_FILE
            
            # Se não encontrar no repository/crest, tenta em final_molecules
            if not energy_file.exists():
                energy_file = OUTPUT_DIR / molecule_name / CREST_ENERGIES_FILE
                
            if not energy_file.exists():
                # Suprime warning para não poluir a saída
                return None
            
            # Lê as energias do arquivo
            energies = []
            with open(energy_file, 'r') as f:
                for line in f:
                    # O arquivo crest.energies tem o formato: número_confôrmero energia
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        try:
                            energy = float(parts[1])
                            energies.append(energy)
                        except ValueError:
                            continue
            
            if not energies:
                return None
            
            # Converte para array numpy para facilitar os cálculos
            energies = np.array(energies)
            
            # Calcula energias relativas em kcal/mol (1 hartree = 627.5 kcal/mol)
            hartree_to_kcal = 627.5
            relative_energies = (energies - energies[0]) * hartree_to_kcal
            
            # Calcula pesos de Boltzmann a 298.15 K
            RT = 0.593  # kcal/mol a 298.15 K
            boltzmann_weights = np.exp(-relative_energies / RT)
            boltzmann_weights /= np.sum(boltzmann_weights)  # Normaliza
            
            # Calcula populações em porcentagem
            populations = boltzmann_weights * 100
            
            return {
                'energies': energies.tolist(),
                'relative_energies': relative_energies.tolist(),
                'boltzmann_weights': boltzmann_weights.tolist(),
                'populations': populations.tolist(),
                'num_conformers': len(energies)
            }
        
        except Exception as e:
            logging.debug(f"Erro ao analisar energias dos confôrmeros para {molecule_name}: {e}")
            return None
    
    def get_best_conformer_energy(self, molecule_name: str) -> Optional[float]:
        """
        Extrai a energia do melhor confôrmero do arquivo crest_best.xyz.
        
        Args:
            molecule_name: Nome da molécula a ser analisada.
            
        Returns:
            A energia do melhor confôrmero ou None se não for encontrada.
        """
        try:
            # CORREÇÃO: Busca primeiro no diretório CREST (repository/crest)
            best_file = CREST_DIR / molecule_name / "crest_best.xyz"
            
            # Se não encontrar no repository/crest, tenta em final_molecules
            if not best_file.exists():
                best_file = OUTPUT_DIR / molecule_name / "crest_best.xyz"
                
            if not best_file.exists():
                # Suprime warning para não poluir a saída
                return None
            
            with open(best_file, 'r') as f:
                lines = f.readlines()
                
            # O arquivo crest_best.xyz tem o formato XYZ
            # A segunda linha pode conter a energia
            if len(lines) >= 2:
                comment_line = lines[1].strip()
                # A linha de comentário pode conter a energia no formato: "energy: -17.72299717"
                # ou apenas o valor da energia
                try:
                    # Tenta extrair energia da linha de comentário
                    if "energy:" in comment_line.lower():
                        energy_str = comment_line.split("energy:")[-1].strip()
                        energy = float(energy_str)
                    else:
                        # Se não tem "energy:", tenta converter a linha diretamente
                        energy = float(comment_line)
                    
                    return energy
                
                except (ValueError, IndexError):
                    # Se não conseguir extrair da linha de comentário, tenta outros métodos
                    pass
            
            # Se não conseguiu extrair da linha de comentário, busca no arquivo de energias
            energy_data = self.get_conformer_energies(molecule_name)
            if energy_data and 'energies' in energy_data:
                # O primeiro confôrmero é o de menor energia
                return energy_data['energies'][0]
            
            return None
        
        except Exception as e:
            logging.debug(f"Erro ao extrair energia do melhor confôrmero para {molecule_name}: {e}")
            return None
    
    def get_heat_of_formation(self, molecule_name: str) -> Optional[float]:
        """
        Extrai a entalpia de formação (heat of formation) do arquivo MOPAC .out em kJ/mol.
        
        Args:
            molecule_name: Nome da molécula a ser analisada.
            
        Returns:
            A entalpia de formação em kJ/mol ou None se não for encontrada.
        """
        try:
            # Busca primeiro no diretório MOPAC (repository/mopac)
            from config.constants import MOPAC_DIR
            mopac_file = MOPAC_DIR / molecule_name / f"{molecule_name}.out"
            
            # Se não encontrar no repository/mopac, tenta em final_molecules
            if not mopac_file.exists():
                mopac_file = OUTPUT_DIR / molecule_name / f"{molecule_name}.out"
                
            if not mopac_file.exists():
                # Suprime warning para não poluir a saída
                return None
            
            # Lê o arquivo MOPAC e procura por heat of formation
            with open(mopac_file, 'r') as f:
                content = f.read()
            
            # Procura por diferentes padrões de heat of formation
            import re
            
            # Padrão típico: "HEAT OF FORMATION = -234.567 KCAL/MOL"
            pattern1 = r"HEAT OF FORMATION\s+=\s+(-?\d+\.?\d*)\s+KCAL/MOL"
            match = re.search(pattern1, content, re.IGNORECASE)
            
            if match:
                heat_of_formation_kcal = float(match.group(1))
                # Converte de kcal/mol para kJ/mol (1 kcal = 4.184 kJ)
                heat_of_formation_kj = heat_of_formation_kcal * 4.184
                return heat_of_formation_kj
            
            # Padrão alternativo: "FINAL HEAT OF FORMATION = -234.567 KCAL/MOL"
            pattern2 = r"FINAL HEAT OF FORMATION\s+=\s+(-?\d+\.?\d*)\s+KCAL/MOL"
            match = re.search(pattern2, content, re.IGNORECASE)
            
            if match:
                heat_of_formation_kcal = float(match.group(1))
                heat_of_formation_kj = heat_of_formation_kcal * 4.184
                return heat_of_formation_kj
                
            # Padrão mais geral para capturar qualquer linha com heat of formation
            pattern3 = r".*HEAT.*FORMATION.*=\s+(-?\d+\.?\d*)\s+KCAL"
            match = re.search(pattern3, content, re.IGNORECASE)
            
            if match:
                heat_of_formation_kcal = float(match.group(1))
                heat_of_formation_kj = heat_of_formation_kcal * 4.184
                return heat_of_formation_kj
            
            return None
        
        except Exception as e:
            logging.debug(f"Erro ao extrair heat of formation para {molecule_name}: {e}")
            return None
    
    def count_atoms(self, molecule_name: str) -> Optional[Dict]:
        """
        Conta o número de átomos no melhor confôrmero.
        
        Args:
            molecule_name: Nome da molécula a ser analisada.
            
        Returns:
            Um dicionário com a contagem de cada tipo de átomo ou None se o arquivo não for encontrado.
        """
        try:
            # CORREÇÃO: Busca primeiro no diretório CREST (repository/crest)
            conformer_file = CREST_DIR / molecule_name / CREST_CONFORMERS_FILE
            
            # Se não encontrar no repository/crest, tenta em final_molecules
            if not conformer_file.exists():
                conformer_file = OUTPUT_DIR / molecule_name / CREST_CONFORMERS_FILE
                
            if not conformer_file.exists():
                # Não gera log warning para evitar poluir a saída
                return None
            
            atom_counts = {}
            current_conformer = False
            
            with open(conformer_file, 'r') as f:
                lines = f.readlines()
                
                # Formato XYZ: primeira linha é o número de átomos, 
                # segunda linha é o comentário (nome da molécula),
                # as linhas seguintes são as coordenadas dos átomos
                i = 0
                while i < len(lines):
                    try:
                        num_atoms = int(lines[i].strip())
                        molecule_line = lines[i+1].strip()
                        
                        # Verifica se estamos no primeiro confôrmero da molécula correta
                        if molecule_line == molecule_name and not current_conformer:
                            current_conformer = True
                            
                            # Processa os átomos deste confôrmero
                            for j in range(i+2, i+2+num_atoms):
                                if j < len(lines):
                                    atom_info = lines[j].strip().split()
                                    if atom_info:
                                        atom_type = atom_info[0]
                                        atom_counts[atom_type] = atom_counts.get(atom_type, 0) + 1
                            
                            # Após processar o primeiro confôrmero, podemos sair
                            break
                        
                        # Pula para o próximo confôrmero
                        i += num_atoms + 2
                    except (ValueError, IndexError):
                        i += 1
            
            if not atom_counts:
                # Não gera log warning para evitar poluir a saída
                return None
            
            return {
                'atom_counts': atom_counts,
                'total_atoms': sum(atom_counts.values())
            }
        
        except Exception as e:
            # Apenas loga o erro em modo debug, sem warning
            logging.debug(f"Erro ao analisar átomos dos confôrmeros para {molecule_name}: {e}")
            return None
    
    def get_conformer_statistics(self, molecule_name: str) -> Dict:
        """
        Obtém estatísticas completas sobre os confôrmeros de uma molécula.
        
        Args:
            molecule_name: Nome da molécula a ser analisada.
            
        Returns:
            Um dicionário com estatísticas sobre os confôrmeros.
        """
        result = {'molecule_name': molecule_name, 'success': False}
        
        # Obtém dados de energia
        energy_data = self.get_conformer_energies(molecule_name)
        if energy_data:
            result.update(energy_data)
            result['success'] = True
            
            # Calcula estatísticas adicionais
            if energy_data['relative_energies']:
                rel_energies = energy_data['relative_energies']
                result['energy_range'] = max(rel_energies) - min(rel_energies)
                result['energy_mean'] = np.mean(rel_energies)
                result['energy_median'] = np.median(rel_energies)
                result['energy_std'] = np.std(rel_energies)
        
        # Obtém dados de átomos
        atom_data = self.count_atoms(molecule_name)
        if atom_data:
            result.update(atom_data)
            
        return result
    
    def generate_energy_distribution(self, molecule_name: str) -> Optional[str]:
        """
        Gera uma representação em texto da distribuição de energia dos confôrmeros.
        
        Args:
            molecule_name: Nome da molécula a ser analisada.
            
        Returns:
            Uma string representando a distribuição de energia ou None se os dados não estiverem disponíveis.
        """
        energy_data = self.get_conformer_energies(molecule_name)
        if not energy_data or 'relative_energies' not in energy_data:
            return None
        
        rel_energies = energy_data['relative_energies']
        populations = energy_data['populations']
        
        # Cria um histograma simples de texto
        result = f"Distribuição de Energia para {molecule_name}\n"
        result += "=" * 50 + "\n"
        result += f"Total de confôrmeros: {len(rel_energies)}\n"
        result += f"Faixa de energia: 0.00 - {max(rel_energies):.2f} kcal/mol\n\n"
        
        result += "Confôrmero  Energia Rel.  População  Histograma\n"
        result += "-" * 50 + "\n"
        
        for i, (energy, pop) in enumerate(zip(rel_energies, populations)):
            # Limita a exibição aos 20 confôrmeros mais estáveis
            if i >= 20:
                break
                
            # Cria um histograma simples usando asteriscos
            hist_bar = "*" * int(pop / 2)  # Divide por 2 para não ficar muito grande
            result += f"{i+1:<11} {energy:8.2f}     {pop:6.2f}%   {hist_bar}\n"
        
        return result
    
    def analyze_all_molecules(self) -> List[Dict]:
        """
        Analisa todas as moléculas que possuem resultados de busca conformacional.
        
        Returns:
            Uma lista de dicionários com estatísticas para cada molécula.
        """
        results = []
        
        try:
            # CORREÇÃO: Verifica primeiro em CREST_DIR
            if CREST_DIR.exists():
                molecule_dirs = [d for d in CREST_DIR.iterdir() if d.is_dir()]
                
                for molecule_dir in molecule_dirs:
                    molecule_name = molecule_dir.name
                    stats = self.get_conformer_statistics(molecule_name)
                    results.append(stats)
            
            # Também verifica em OUTPUT_DIR para resultados antigos
            if OUTPUT_DIR.exists():
                molecule_dirs = [d for d in OUTPUT_DIR.iterdir() if d.is_dir()]
                
                for molecule_dir in molecule_dirs:
                    molecule_name = molecule_dir.name
                    # Só adiciona se ainda não foi analisado
                    if not any(r['molecule_name'] == molecule_name for r in results):
                        stats = self.get_conformer_statistics(molecule_name)
                        results.append(stats)
            
            return results
        
        except Exception as e:
            logging.error(f"Erro ao analisar todas as moléculas: {e}")
            return results
