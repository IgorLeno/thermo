"""
Serviço de integração com Chemperium para predição de entalpia de formação.
Suporta Δ-learning com MOPAC como lower level of theory.
"""

import logging
import os
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from utils.exceptions import ChemperiumError, ConfigurationError

logger = logging.getLogger(__name__)


class ChemperiumService:
    """Serviço para cálculos de entalpia usando Chemperium."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o serviço Chemperium.
        
        Args:
            config: Configurações do sistema
        """
        self.config = config.get('chemperium', {})
        self.method = self.config.get('method', 'cbs-qb3')
        self.dimension = self.config.get('dimension', '3d')
        self.data_location = self.config.get('data_location', None)
        self.enabled = self.config.get('enabled', True)
        
        # Verificar se Chemperium está instalado
        self.chemperium_available = self._check_chemperium_availability()
        
        if self.enabled and not self.chemperium_available:
            logger.warning("Chemperium está habilitado mas não está instalado")
    
    def _check_chemperium_availability(self) -> bool:
        """Verifica se o Chemperium está instalado e disponível."""
        try:
            import chemperium
            logger.info("Chemperium encontrado e disponível")
            return True
        except ImportError:
            logger.warning("Chemperium não está instalado, usando mock para desenvolvimento")
            return False
    
    def predict_enthalpy_with_llot(self, 
                                  smiles: str,
                                  xyz_content: str,
                                  llot_enthalpy: float,
                                  temp: float = 298.15) -> Tuple[float, float]:
        """
        Prediz entalpia usando Chemperium com Δ-learning.
        
        Args:
            smiles: SMILES da molécula
            xyz_content: Conteúdo do arquivo XYZ
            llot_enthalpy: Entalpia do MOPAC (lower level of theory) em kcal/mol
            temp: Temperatura em K (padrão: 298.15)
            
        Returns:
            Tuple[float, float]: (entalpia_predita, incerteza) em kcal/mol
            
        Raises:
            ChemperiumError: Se ocorrer erro na predição
        """
        try:
            if self.chemperium_available:
                import chemperium as cp
                module_to_use = cp
            else:
                # Usa mock se Chemperium não disponível
                from .mock_chemperium import MockChemperium
                module_to_use = MockChemperium()
                logger.warning("Usando mock do Chemperium para desenvolvimento")
            
            # Inicializar modelo Chemperium
            logger.info(f"Inicializando modelo Chemperium {self.method} ({self.dimension})")
            thermo = module_to_use.Thermo(self.method, self.dimension, self.data_location)
            
            # Realizar predição
            logger.info("Calculando entalpia com Chemperium...")
            result = thermo.predict_enthalpy(
                smiles=smiles,
                xyz=xyz_content,
                llot=llot_enthalpy,
                t=temp,
                quality_check=True
            )
            
            # Extrair resultados
            enthalpy = result['H298_prediction'].iloc[0]
            uncertainty = result['H298_uncertainty'].iloc[0]
            reliability = result.get('reliability', [0.0]).iloc[0]
            
            logger.info(f"Entalpia Chemperium: {enthalpy:.3f} ± {uncertainty:.3f} kcal/mol")
            logger.info(f"Score de confiabilidade: {reliability:.3f}")
            
            return enthalpy, uncertainty
            
        except ImportError:
            raise ChemperiumError("Erro ao importar Chemperium")
        except Exception as e:
            raise ChemperiumError(f"Erro na predição Chemperium: {str(e)}")
    
    def predict_enthalpy_standalone(self, 
                                   smiles: str,
                                   xyz_content: str,
                                   temp: float = 298.15) -> Tuple[float, float]:
        """
        Prediz entalpia usando apenas Chemperium (sem LLOT).
        
        Args:
            smiles: SMILES da molécula
            xyz_content: Conteúdo do arquivo XYZ
            temp: Temperatura em K (padrão: 298.15)
            
        Returns:
            Tuple[float, float]: (entalpia_predita, incerteza) em kcal/mol
            
        Raises:
            ChemperiumError: Se ocorrer erro na predição
        """
        try:
            if self.chemperium_available:
                import chemperium as cp
                module_to_use = cp
            else:
                # Usa mock se Chemperium não disponível
                from .mock_chemperium import MockChemperium
                module_to_use = MockChemperium()
                logger.warning("Usando mock do Chemperium para desenvolvimento")
            
            # Para predição standalone, usar 2D se não tiver coordenadas
            dimension = self.dimension if xyz_content else "2d"
            
            logger.info(f"Inicializando modelo Chemperium {self.method} ({dimension})")
            thermo = module_to_use.Thermo(self.method, dimension, self.data_location)
            
            # Realizar predição
            logger.info("Calculando entalpia com Chemperium (standalone)...")
            
            if dimension == "3d":
                result = thermo.predict_enthalpy(
                    smiles=smiles,
                    xyz=xyz_content,
                    t=temp,
                    quality_check=True
                )
            else:
                result = thermo.predict_enthalpy(
                    smiles=smiles,
                    t=temp,
                    quality_check=True
                )
            
            # Extrair resultados
            enthalpy = result['H298_prediction'].iloc[0]
            uncertainty = result['H298_uncertainty'].iloc[0]
            reliability = result.get('reliability', [0.0]).iloc[0]
            
            logger.info(f"Entalpia Chemperium: {enthalpy:.3f} ± {uncertainty:.3f} kcal/mol")
            logger.info(f"Score de confiabilidade: {reliability:.3f}")
            
            return enthalpy, uncertainty
            
        except ImportError:
            raise ChemperiumError("Erro ao importar Chemperium")
        except Exception as e:
            raise ChemperiumError(f"Erro na predição Chemperium: {str(e)}")
    
    def predict_thermochemistry_full(self, 
                                   smiles: str,
                                   xyz_content: str,
                                   llot_enthalpy: Optional[float] = None,
                                   temp: float = 298.15) -> Dict[str, float]:
        """
        Prediz propriedades termodinâmicas completas (H, S, G).
        
        Args:
            smiles: SMILES da molécula
            xyz_content: Conteúdo do arquivo XYZ
            llot_enthalpy: Entalpia MOPAC (opcional)
            temp: Temperatura em K
            
        Returns:
            Dict com entalpia, entropia, energia livre e incertezas
        """
        if not self.chemperium_available:
            raise ChemperiumError("Chemperium não está instalado")
        
        try:
            import chemperium as cp
            
            logger.info(f"Inicializando modelo Chemperium {self.method} ({self.dimension})")
            thermo = cp.Thermo(self.method, self.dimension, self.data_location)
            
            # Realizar predição completa
            logger.info("Calculando termoquímica completa com Chemperium...")
            
            result = thermo.predict_gibbs(
                smiles=smiles,
                xyz=xyz_content,
                llot=llot_enthalpy,
                t=temp,
                quality_check=True
            )
            
            # Extrair todos os resultados
            temp_int = int(temp)
            output = {
                'enthalpy': result[f'H{temp_int}_prediction'].iloc[0],
                'enthalpy_uncertainty': result[f'H{temp_int}_uncertainty'].iloc[0],
                'entropy': result[f'S{temp_int}_prediction'].iloc[0],
                'entropy_uncertainty': result[f'S{temp_int}_uncertainty'].iloc[0],
                'gibbs': result[f'G{temp_int}_prediction'].iloc[0],
                'h_reliability': result.get(f'H{temp_int}_reliability', [0.0]).iloc[0],
                's_reliability': result.get(f'S{temp_int}_reliability', [0.0]).iloc[0]
            }
            
            logger.info(f"Termoquímica Chemperium:")
            logger.info(f"  H: {output['enthalpy']:.3f} ± {output['enthalpy_uncertainty']:.3f} kcal/mol")
            logger.info(f"  S: {output['entropy']:.3f} ± {output['entropy_uncertainty']:.3f} cal/mol·K")
            logger.info(f"  G: {output['gibbs']:.3f} kcal/mol")
            
            return output
            
        except ImportError:
            raise ChemperiumError("Erro ao importar Chemperium")
        except Exception as e:
            raise ChemperiumError(f"Erro na predição Chemperium: {str(e)}")
    
    def get_nasa_polynomials(self,
                           molecule_name: str,
                           smiles: str,
                           xyz_content: str,
                           llot_enthalpy: Optional[float] = None) -> str:
        """
        Gera polinômios NASA em formato Chemkin.
        
        Args:
            molecule_name: Nome da molécula
            smiles: SMILES da molécula
            xyz_content: Conteúdo do arquivo XYZ
            llot_enthalpy: Entalpia MOPAC (opcional)
            
        Returns:
            String com polinômios NASA em formato Chemkin
        """
        if not self.chemperium_available:
            raise ChemperiumError("Chemperium não está instalado")
        
        try:
            import chemperium as cp
            
            logger.info(f"Gerando polinômios NASA para {molecule_name}")
            thermo = cp.Thermo(self.method, self.dimension, self.data_location)
            
            chemkin_data = thermo.get_nasa_polynomials(
                names=molecule_name,
                smiles=smiles,
                xyz=xyz_content,
                llot=llot_enthalpy,
                chemkin=True
            )
            
            logger.info("Polinômios NASA gerados com sucesso")
            return chemkin_data
            
        except ImportError:
            raise ChemperiumError("Erro ao importar Chemperium")
        except Exception as e:
            raise ChemperiumError(f"Erro ao gerar polinômios NASA: {str(e)}")
    
    def is_available(self) -> bool:
        """Retorna se o Chemperium está disponível (real ou mock)."""
        return self.enabled  # Sempre disponível se habilitado (usa mock se necessário)


# Função de conveniência para converter units
def kcal_to_kj(kcal_value: float) -> float:
    """Converte kcal/mol para kJ/mol."""
    return kcal_value * 4.184

def kj_to_kcal(kj_value: float) -> float:
    """Converte kJ/mol para kcal/mol."""
    return kj_value / 4.184
