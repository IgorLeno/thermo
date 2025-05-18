#!/usr/bin/env python3
"""
Script de verificação rápida para testar se o programa inicia sem erros.
"""

import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Testa se todos os módulos podem ser importados sem erros."""
    try:
        print("Testando importações...")
        
        # Testa importação das classes principais
        from config.settings import Settings
        print("✅ config.settings")
        
        from core.molecule import Molecule
        print("✅ core.molecule")
        
        from interfaces.cli import CommandLineInterface
        print("✅ interfaces.cli")
        
        from services.supabase_service import SupabaseService
        print("✅ services.supabase_service")
        
        print("\n🎉 Todas as importações foram bem-sucedidas!")
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False

def test_settings_load():
    """Testa se as configurações são carregadas corretamente."""
    try:
        print("\nTestando carregamento de configurações...")
        
        from config.settings import Settings
        settings = Settings()
        settings.load_settings("config.yaml")
        
        print(f"✅ Supabase: {'Habilitado' if settings.supabase.enabled else 'Desabilitado'}")
        if settings.supabase.enabled:
            print(f"✅ URL: {settings.supabase.url}")
            print(f"✅ Key: {'Configurada' if settings.supabase.key else 'Não configurada'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao carregar configurações: {e}")
        return False

def main():
    """Executa todos os testes."""
    print("=== Verificação Rápida do Grimme Thermo ===\n")
    
    success = True
    
    # Teste 1: Importações
    if not test_imports():
        success = False
    
    # Teste 2: Configurações
    if not test_settings_load():
        success = False
    
    # Resultado final
    print("\n" + "="*50)
    if success:
        print("🎉 VERIFICAÇÃO CONCLUÍDA COM SUCESSO!")
        print("✅ O programa deve inicializar normalmente.")
        print("\nPara executar o programa completo:")
        print("python main.py")
    else:
        print("❌ PROBLEMAS ENCONTRADOS!")
        print("Verifique os erros acima antes de ejecutar o programa.")
    
    return success

if __name__ == "__main__":
    main()
