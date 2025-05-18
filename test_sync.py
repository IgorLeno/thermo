#!/usr/bin/env python3
"""
Script de teste rápido para verificar a sincronização com o Supabase.
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from core.molecule import Molecule
from services.supabase_service import SupabaseService
from config.settings import Settings

def main():
    print("=== Teste de Sincronização Supabase ===\n")
    
    # Carrega as configurações
    try:
        settings = Settings()
        if not settings.supabase.enabled:
            print("❌ Supabase não está habilitado nas configurações.")
            print("Configure-o primeiro usando o menu principal (opção 6).")
            return
    except Exception as e:
        print(f"❌ Erro ao carregar configurações: {e}")
        return
    
    # Inicializa o serviço Supabase
    try:
        supabase_service = SupabaseService(
            url=settings.supabase.url,
            key=settings.supabase.key
        )
        
        if not supabase_service.enabled:
            print("❌ Não foi possível conectar ao Supabase.")
            print("Verifique suas credenciais nas configurações.")
            return
            
        print("✅ Conexão com Supabase estabelecida.")
    except Exception as e:
        print(f"❌ Erro ao conectar com Supabase: {e}")
        return
    
    # Teste de upload de uma molécula simples
    try:
        print("\n📝 Testando upload de molécula...")
        
        # Cria uma molécula de teste
        test_molecule = Molecule(name="test_molecule_sync")
        test_molecule.enthalpy_formation_mopac = -100.5
        test_molecule.enthalpy_formation_mopac_kj = -420.8
        
        # Tenta fazer upload
        molecule_id = supabase_service.upload_molecule(test_molecule)
        
        if molecule_id:
            print(f"✅ Molécula de teste enviada com sucesso. ID: {molecule_id}")
            
            # Remove a molécula de teste
            try:
                supabase_service.supabase.table("molecules").delete().eq("id", molecule_id).execute()
                print("✅ Molécula de teste removida com sucesso.")
            except Exception as cleanup_e:
                print(f"⚠️  Aviso: Não foi possível remover a molécula de teste: {cleanup_e}")
        else:
            print("❌ Falha no upload da molécula de teste.")
            return
            
    except Exception as e:
        print(f"❌ Erro no teste de upload: {e}")
        return
    
    # Teste de verificação de bucket (se habilitado)
    if settings.supabase.storage_enabled:
        try:
            print("\n🗂️  Testando acesso ao Storage...")
            bucket_name = settings.supabase.molecules_bucket
            bucket_ok = supabase_service.ensure_bucket_exists(bucket_name)
            
            if bucket_ok:
                print(f"✅ Bucket '{bucket_name}' está acessível.")
            else:
                print(f"⚠️  Problemas com o bucket '{bucket_name}'.")
        except Exception as e:
            print(f"❌ Erro no teste de Storage: {e}")
    
    print("\n✅ Todos os testes concluídos!")
    print("🚀 Você pode agora usar a sincronização pelo menu principal (opção 6 -> 3).")

if __name__ == "__main__":
    main()
