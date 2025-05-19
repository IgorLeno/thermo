# 🚀 Guia de Instalação Rápida - Integração Chemperium

## 📋 Pré-requisitos

- Python 3.8+ instalado
- Git instalado
- Ambiente virtual recomendado

## ⚡ Instalação Rápida

### 1. Clone e Setup
```bash
git clone https://github.com/alexportugal18/grimme_thermo.git
cd grimme_thermo
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Verificar Integração Chemperium
```bash
python test_chemperium_integration.py
```

## 🧪 Teste Rápido

### 1. Executar Programa
```bash
python main.py
```

### 2. Testar Chemperium (Opção 3)
- Escolha: **3. Só Chemperium (rápido, sem CREST)**
- Digite: **ethanol**
- Aguarde resultado (~30 segundos)

### 3. Resultado Esperado
```
=== Resultados para ethanol ===
Chemperium: -234.567 ± 2.123 kJ/mol
```

## 🔧 Configuração Opcional

### 1. Método Chemperium
- Menu → **5. Editar configurações**
- Opção **8. Método Chemperium**
- Escolher: `cbs-qb3` (preciso) ou `g3mp2b3` (rápido)

### 2. Banco de Dados (Opcional)
Se usar Supabase:
```sql
-- No Editor SQL do Supabase
\i add_chemperium_columns.sql
```

## ⚠️ Solução de Problemas

### Chemperium não instalado
```bash
pip install chemperium
```

### TensorFlow não compatível
```bash
pip install "tensorflow>=2.12.0,<=2.15.0"
```

### RDKit não instalado
```bash
pip install rdkit
```

## 📚 Próximos Passos

1. **Leia**: `docs/chemperium_integration.md`
2. **Configure**: Supabase para dashboard
3. **Teste**: Com suas moléculas
4. **Compare**: Resultados MOPAC vs Chemperium

## 🆘 Suporte

- Issues: [GitHub Issues](https://github.com/alexportugal18/grimme_thermo/issues)
- Documentação: `docs/`
- Teste: `python test_chemperium_integration.py`

---
*Tempo estimado de setup: 5-10 minutos*
