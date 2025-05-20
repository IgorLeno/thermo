"""
Mock do Chemperium para permitir desenvolvimento sem instalação.
Este módulo simula a API do Chemperium para fins de teste e desenvolvimento.
"""

import logging
import numpy as np
import pandas as pd
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class MockThermo:
    """Mock da classe Thermo do Chemperium."""
    
    def __init__(self, method: str, dimension: str, data_location: Optional[str] = None):
        """Simula inicialização do Thermo."""
        self.method = method
        self.dimension = dimension
        self.data_location = data_location
        logger.info(f"Mock Chemperium inicializado: {method} ({dimension})")
    
    def predict_enthalpy(self, smiles: str, xyz: Optional[str] = None, 
                        llot: Optional[float] = None, t: float = 298.15, 
                        quality_check: bool = False) -> pd.DataFrame:
        """Simula predição de entalpia."""
        
        # Simula diferentes entalpias baseadas no SMILES
        mock_enthalpies = {
            "CCO": -59.7,     # etanol
            "CO": -56.2,      # metanol
            "O": -68.3,       # água
            "CCCCCCCC": -49.8, # octano
            "c1ccccc1": 19.8,  # benzeno
        }
        
        base_enthalpy = mock_enthalpies.get(smiles, -50.0)  # Valor padrão
        
        # Se LLOT fornecido, adiciona variação
        if llot is not None and self.dimension == "3d":
            # Simula correção Δ-learning
            correction = np.random.normal(0, 2)  # Correção aleatória
            enthalpy = llot + correction
        else:
            enthalpy = base_enthalpy
        
        # Simula incerteza
        uncertainty = abs(np.random.normal(0, 2))
        
        # Cria DataFrame de resultado
        temp_str = f"H{int(t)}"
        result = pd.DataFrame({
            "smiles": [smiles],
            f"{temp_str}_prediction": [enthalpy],
            f"{temp_str}_uncertainty": [uncertainty]
        })
        
        if quality_check:
            result["reliability"] = [np.random.uniform(0.7, 0.95)]
        
        logger.info(f"Mock predição: {smiles} -> {enthalpy:.3f} ± {uncertainty:.3f} kcal/mol")
        return result

# Função principal para simular importação
def Thermo(method: str, dimension: str, data_location: Optional[str] = None):
    """Função factory que simula chemperium.Thermo."""
    return MockThermo(method, dimension, data_location)

# Para compatibilidade com importações do tipo "import chemperium as cp"
class MockChemperium:
    """Mock do módulo chemperium."""
    
    @staticmethod
    def Thermo(method: str, dimension: str, data_location: Optional[str] = None):
        return MockThermo(method, dimension, data_location)
