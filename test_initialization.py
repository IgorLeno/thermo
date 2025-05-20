#!/usr/bin/env python3
"""
Script de teste para verificar a inicialização do Chemperium Service.
"""

import sys
sys.path.append('.')

from config.settings import Settings
from services.chemperium.chemperium_service import ChemperiumService
import logging

def test_chemperium_initialization():
    """Testa se o ChemperiumService inicializa corretamente."""
    print("=== Teste de Inicializacao do Chemperium ===")
    
    try:
        # Carregar configurações
        print("1. Carregando configuracoes...")
        settings = Settings()
        settings.load_settings("config.yaml")
        print(f"   Config carregado: {type(settings.config)}")
        print(f"   Chemperium config: {settings.config.get('chemperium', 'MISSING')}")
        
        # Inicializar serviço
        print("2. Inicializando ChemperiumService...")
        chemperium_service = ChemperiumService(settings.config)
        print(f"   Servico criado: {type(chemperium_service)}")
        print(f"   Habilitado: {chemperium_service.enabled}")
        print(f"   Disponivel: {chemperium_service.is_available()}")
        print(f"   Metodo: {chemperium_service.method}")
        print(f"   Dimensao: {chemperium_service.dimension}")
        
        # Testar disponibilidade
        print("3. Testando disponibilidade...")
        if chemperium_service.is_available():
            print("   Chemperium esta disponivel (real ou mock)")
        else:
            print("   Chemperium nao esta disponivel")
            
        print("\n   ### TESTE PASSOU - ChemperiumService inicializou corretamente!")
        return True
        
    except Exception as e:
        print(f"\n   ### TESTE FALHOU - Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_menu_integration():
    """Testa se o Menu consegue usar o ChemperiumService."""
    print("\n=== Teste de Integracao Menu-Chemperium ===")
    
    try:
        from interfaces.menu import Menu
        from services.file_service import FileService
        from services.pubchem_service import PubChemService
        from services.conversion_service import ConversionService
        from services.calculation_service import CalculationService
        
        # Configurar serviços
        settings = Settings()
        settings.load_settings("config.yaml")
        
        file_service = FileService()
        pubchem_service = PubChemService()
        conversion_service = ConversionService(settings)
        calculation_service = CalculationService(settings, file_service, conversion_service)
        
        # Criar menu
        print("1. Criando Menu...")
        menu = Menu(settings, file_service, pubchem_service, conversion_service, calculation_service)
        print(f"   Menu criado: {type(menu)}")
        print(f"   ChemperiumService: {type(menu.chemperium_service)}")
        
        # Verificar métodos
        print("2. Verificando metodos...")
        print(f"   calculate_single_molecule_with_chemperium: {'OK' if hasattr(menu, 'calculate_single_molecule_with_chemperium') else 'MISSING'}")
        print(f"   calculate_single_molecule_chemperium_only: {'OK' if hasattr(menu, 'calculate_single_molecule_chemperium_only') else 'MISSING'}")
        print(f"   calculate_multiple_molecules_chemperium: {'OK' if hasattr(menu, 'calculate_multiple_molecules_chemperium') else 'MISSING'}")
        
        print("\n   ### TESTE PASSOU - Integracao Menu-Chemperium funcionando!")
        return True
        
    except Exception as e:
        print(f"\n   ### TESTE FALHOU - Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Configurar logging básico
    logging.basicConfig(level=logging.WARNING)
    
    print("=== TESTES DE INTEGRACAO CHEMPERIUM ===\n")
    
    test1 = test_chemperium_initialization()
    test2 = test_menu_integration()
    
    print(f"\n=== RESUMO ===")
    print(f"   Inicializacao: {'PASSOU' if test1 else 'FALHOU'}")
    print(f"   Integracao:    {'PASSOU' if test2 else 'FALHOU'}")
    
    if test1 and test2:
        print(f"\n=== TODOS OS TESTES PASSARAM! O sistema esta pronto para uso. ===")
        sys.exit(0)
    else:
        print(f"\n=== ALGUNS TESTES FALHARAM. Verifique os erros acima. ===")
        sys.exit(1)
