"""
Script de teste para verificar a integração Chemperium.
Testa as funcionalidades principais da integração sem executar cálculos completos.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from pathlib import Path
from services.chemperium import ChemperiumService
from services.pubchem_service import PubChemService
from core.molecule import Molecule
from config.settings import Settings

def test_chemperium_availability():
    """Testa se o Chemperium está disponível."""
    print("=== Teste 1: Disponibilidade do Chemperium ===")
    
    try:
        import chemperium
        print("OK Chemperium esta instalado")
        
        # Configuração mínima
        config = {"chemperium": {"enabled": True, "method": "cbs-qb3", "dimension": "3d"}}
        chemperium_service = ChemperiumService(config)
        
        if chemperium_service.is_available():
            print("OK Chemperium esta disponivel")
            return True
        else:
            print("ERRO Chemperium nao esta disponivel")
            return False
    except ImportError:
        print("ERRO Chemperium nao esta instalado")
        print("  Para instalar: pip install chemperium")
        return False

def test_pubchem_smiles():
    """Testa a obtenção de SMILES do PubChem."""
    print("\n=== Teste 2: Obtencao de SMILES do PubChem ===")
    
    pubchem_service = PubChemService()
    test_molecules = ["ethanol", "methanol", "water"]
    
    success_count = 0
    for molecule_name in test_molecules:
        try:
            smiles = pubchem_service.get_smiles_by_name(molecule_name)
            if smiles:
                print(f"OK {molecule_name}: {smiles}")
                success_count += 1
            else:
                print(f"ERRO {molecule_name}: SMILES nao encontrado")
        except Exception as e:
            print(f"ERRO {molecule_name}: Erro - {e}")
    
    print(f"Resultado: {success_count}/{len(test_molecules)} moleculas com SMILES obtidos")
    return success_count == len(test_molecules)

def test_molecule_structure():
    """Testa a estrutura atualizada da classe Molecule."""
    print("\n=== Teste 3: Estrutura da Classe Molecule ===")
    
    molecule = Molecule(name="test_molecule")
    
    # Testa novos atributos
    required_attributes = [
        "smiles",
        "enthalpy_chemperium_kj_mol",
        "enthalpy_chemperium_uncertainty_kj_mol",
        "chemperium_reliability_score"
    ]
    
    success_count = 0
    for attr in required_attributes:
        if hasattr(molecule, attr):
            print(f"OK Atributo '{attr}' presente")
            success_count += 1
        else:
            print(f"ERRO Atributo '{attr}' ausente")
    
    # Testa método set_chemperium_results
    try:
        molecule.set_chemperium_results(
            enthalpy_kj=-200.0,
            uncertainty_kj=5.0,
            reliability=0.95
        )
        print("OK Metodo 'set_chemperium_results' funcional")
        success_count += 1
    except Exception as e:
        print(f"ERRO Metodo 'set_chemperium_results' falhou: {e}")
    
    print(f"Resultado: {success_count}/{len(required_attributes) + 1} verificacoes bem-sucedidas")
    return success_count == len(required_attributes) + 1

def test_configuration_loading():
    """Testa o carregamento das configurações do Chemperium."""
    print("\n=== Teste 4: Carregamento das Configuracoes ===")
    
    try:
        settings = Settings()
        # Simula carregamento de configuração
        settings.config = {
            "chemperium": {
                "enabled": True,
                "method": "cbs-qb3",
                "dimension": "3d",
                "data_location": None
            }
        }
        
        chemperium_service = ChemperiumService(settings.config)
        
        expected_values = {
            "enabled": True,
            "method": "cbs-qb3",
            "dimension": "3d"
        }
        
        success_count = 0
        for key, expected_value in expected_values.items():
            actual_value = getattr(chemperium_service, key, None)
            if actual_value == expected_value:
                print(f"OK {key}: {actual_value}")
                success_count += 1
            else:
                print(f"ERRO {key}: esperado {expected_value}, obtido {actual_value}")
        
        print(f"Resultado: {success_count}/{len(expected_values)} configuracoes corretas")
        return success_count == len(expected_values)
        
    except Exception as e:
        print(f"ERRO ao carregar configuracoes: {e}")
        return False

def test_unit_conversion():
    """Testa as funções de conversão de unidades."""
    print("\n=== Teste 5: Conversao de Unidades ===")
    
    from services.chemperium.chemperium_service import kcal_to_kj, kj_to_kcal
    
    test_cases = [
        (100, 418.4),  # 100 kcal/mol = 418.4 kJ/mol
        (50, 209.2),   # 50 kcal/mol = 209.2 kJ/mol
        (-25, -104.6)  # -25 kcal/mol = -104.6 kJ/mol
    ]
    
    success_count = 0
    for kcal_value, expected_kj in test_cases:
        converted_kj = kcal_to_kj(kcal_value)
        back_to_kcal = kj_to_kcal(converted_kj)
        
        if abs(converted_kj - expected_kj) < 0.1 and abs(back_to_kcal - kcal_value) < 0.1:
            print(f"OK {kcal_value} kcal/mol <-> {converted_kj} kJ/mol")
            success_count += 1
        else:
            print(f"ERRO {kcal_value} kcal/mol: esperado {expected_kj}, obtido {converted_kj}")
    
    print(f"Resultado: {success_count}/{len(test_cases)} conversoes corretas")
    return success_count == len(test_cases)

def test_chemperium_mock_prediction():
    """Testa uma predição mock do Chemperium (se disponível)."""
    print("\n=== Teste 6: Predicao Mock do Chemperium ===")
    
    config = {"chemperium": {"enabled": True, "method": "cbs-qb3", "dimension": "3d"}}
    chemperium_service = ChemperiumService(config)
    
    if not chemperium_service.is_available():
        print("AVISO Chemperium nao disponivel. Pulando teste de predicao.")
        return True
    
    # Dados de teste para etanol
    test_smiles = "CCO"
    test_xyz = """3

C          1.31970       -0.64380        0.00000
C          0.02030        0.05840        0.00000
O         -1.08430       -0.70260        0.00000
H          1.17970       -1.32130        0.87370
H          1.17970       -1.32130       -0.87370
H          2.24040       -0.05350        0.00000
H         -0.06240        0.69730        0.87370
H         -0.06240        0.69730       -0.87370
H         -1.91840       -0.15480        0.00000"""
    
    try:
        # Teste predição standalone
        enthalpy, uncertainty = chemperium_service.predict_enthalpy_standalone(
            smiles=test_smiles,
            xyz_content=test_xyz
        )
        print(f"OK Predicao standalone: {enthalpy:.3f} +/- {uncertainty:.3f} kcal/mol")
        
        # Teste predição com LLOT (usando valor mock)
        llot_test = -60.0  # kcal/mol mock para etanol
        enthalpy_llot, uncertainty_llot = chemperium_service.predict_enthalpy_with_llot(
            smiles=test_smiles,
            xyz_content=test_xyz,
            llot_enthalpy=llot_test
        )
        print(f"OK Predicao com LLOT: {enthalpy_llot:.3f} +/- {uncertainty_llot:.3f} kcal/mol")
        
        print("OK Predicoes Chemperium funcionais")
        return True
        
    except Exception as e:
        print(f"ERRO na predicao Chemperium: {e}")
        return False

def run_all_tests():
    """Executa todos os testes e retorna relatório."""
    print("INICIANDO TESTES DA INTEGRACAO CHEMPERIUM")
    print("=" * 60)
    
    tests = [
        ("Disponibilidade Chemperium", test_chemperium_availability),
        ("SMILES do PubChem", test_pubchem_smiles),
        ("Estrutura Molecule", test_molecule_structure),
        ("Configuracoes", test_configuration_loading),
        ("Conversao de Unidades", test_unit_conversion),
        ("Predicao Chemperium", test_chemperium_mock_prediction)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"ERRO inesperado em {test_name}: {e}")
            results[test_name] = False
    
    # Relatório Final
    print("\n" + "=" * 60)
    print("RELATORIO FINAL DOS TESTES")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, success in results.items():
        status = "PASSOU" if success else "FALHOU"
        print(f"{test_name:<25} {status}")
    
    print("-" * 60)
    print(f"RESULTADO GERAL: {passed}/{total} testes passaram ({100*passed/total:.1f}%)")
    
    if passed == total:
        print("\nTODOS OS TESTES PASSARAM!")
        print("A integracao Chemperium esta funcionando corretamente.")
    elif passed >= total * 0.8:
        print("\nMAIORIA DOS TESTES PASSOU")
        print("A integracao esta funcional, mas pode haver problemas menores.")
    else:
        print("\nVARIOS TESTES FALHARAM")
        print("Verifique a instalacao e configuracao do Chemperium.")
    
    return passed == total

if __name__ == "__main__":
    # Configura logging para os testes
    logging.basicConfig(level=logging.WARNING)  # Reduz verbosidade
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
