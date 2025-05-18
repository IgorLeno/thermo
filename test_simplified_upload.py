"""
Upload simplificado sem as colunas de entalpia na tabela molecules.
Use este script se não conseguir adicionar as colunas.
"""

import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from services.supabase_service import SupabaseService

class SupabaseServiceSimplified(SupabaseService):
    """Versão simplificada do serviço Supabase que não usa colunas de entalpia na tabela molecules."""
    
    def upload_molecule(self, molecule):
        """
        Versão simplificada que não tenta inserir entalpia na tabela molecules.
        """
        if not self.enabled:
            return None
        
        try:
            # Verifica se a molécula já existe
            response = self.supabase.table("molecules") \
                .select("id") \
                .eq("name", molecule.name) \
                .execute()
                
            if response.data:
                molecule_id = response.data[0]["id"]
                print(f"✅ Molécula '{molecule.name}' já existe com ID: {molecule_id}")
                return molecule_id
            
            # Dados básicos apenas (sem entalpia)
            molecule_data = {
                "name": molecule.name,
            }
            
            # Insere a molécula
            response = self.supabase.table("molecules").insert(molecule_data).execute()
            
            if response.data:
                molecule_id = response.data[0]["id"]
                print(f"✅ Molécula '{molecule.name}' inserida com ID: {molecule_id}")
                return molecule_id
            else:
                print(f"❌ Erro: Sem dados de retorno para {molecule.name}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao fazer upload de {molecule.name}: {e}")
            return None


def test_simplified_upload():
    """Testa o upload simplificado."""
    from config.settings import Settings
    from core.molecule import Molecule
    
    # Carrega configurações
    settings = Settings()
    if not settings.supabase.enabled:
        print("❌ Supabase não está habilitado.")
        return
    
    # Inicializa serviço simplificado
    service = SupabaseServiceSimplified(
        url=settings.supabase.url,
        key=settings.supabase.key
    )
    
    if not service.enabled:
        print("❌ Não foi possível conectar ao Supabase.")
        return
    
    # Testa upload de uma molécula simples
    test_molecule = Molecule(name="ethanol_test")
    
    molecule_id = service.upload_molecule(test_molecule)
    
    if molecule_id:
        print(f"🎉 Teste bem-sucedido! Molecule ID: {molecule_id}")
        
        # Remove a molécula de teste
        try:
            service.supabase.table("molecules").delete().eq("id", molecule_id).execute()
            print("✅ Molécula de teste removida.")
        except Exception as e:
            print(f"⚠️  Não foi possível remover molécula de teste: {e}")
    else:
        print("❌ Teste falhou.")

if __name__ == "__main__":
    test_simplified_upload()
