# Integração com Chemperium - Guia Técnico

## 📋 Visão Geral

Este documento descreve a integração do **Chemperium** no **Grimme Thermo**, implementando a **Opção 2: Δ-Learning Integration** para correção sistemática de entalpias calculadas pelo MOPAC.

## 🎯 Objetivo da Integração

- **Δ-Learning**: Usar MOPAC como Lower Level of Theory (LLOT) e Chemperium para correção
- **Melhor Precisão**: Combinar rapidez do MOPAC com alta precisão do Chemperium
- **Flexibilidade**: Permitir uso tradicional (CREST+MOPAC) ou com Chemperium
- **Compatibilidade**: Manter funcionalidades existentes intactas

## 🏗️ Arquitetura da Integração

### **1. Fluxos de Cálculo Disponíveis**

```
1. Tradicional:         Nome → PubChem → SDF → XYZ → CREST → MOPAC → Resultados

2. Com Chemperium:      Nome → PubChem → SMILES + SDF → XYZ → CREST → MOPAC → 
                                                                    ↓
                                                    Chemperium (SMILES + XYZ + LLOT) → Resultados

3. Só Chemperium:       Nome → PubChem → SMILES + SDF → XYZ → Chemperium → Resultados

4. Múltiplas moléculas: Qualquer dos fluxos acima para listas de moléculas
```

### **2. Componentes Implementados**

#### **A. ChemperiumService** (`services/chemperium/chemperium_service.py`)
- `predict_enthalpy_with_llot()`: Predição com Δ-learning
- `predict_enthalpy_standalone()`: Predição sem LLOT
- `predict_thermochemistry_full()`: H, S, G completos
- `get_nasa_polynomials()`: Polinômios em formato Chemkin
- `is_available()`: Verifica se Chemperium está instalado

#### **B. Atualização da Classe Molecule** (`core/molecule.py`)
```python
# Novos campos adicionados:
smiles: Optional[str] = None                              # SMILES da molécula
enthalpy_chemperium_kj_mol: Optional[float] = None        # Entalpia corrigida
enthalpy_chemperium_uncertainty_kj_mol: Optional[float] = None  # Incerteza
chemperium_reliability_score: Optional[float] = None      # Score de confiabilidade
```

#### **C. Extensão do PubChem Service** (`services/pubchem_service.py`)
```python
def get_smiles_by_name(self, molecule_name: str) -> Optional[str]:
    """Obtém SMILES canônico do PubChem via API."""
```

#### **D. Menu Atualizado** (`interfaces/menu.py`)
- **Opção 1**: Cálculo tradicional (CREST + MOPAC)
- **Opção 2**: Cálculo com Chemperium (CREST + MOPAC + Chemperium)
- **Opção 3**: Só Chemperium (rápido, sem CREST)
- **Opção 4**: Múltiplas moléculas com Chemperium

### **3. Configuração**

#### **config.yaml**
```yaml
chemperium:
  enabled: true                    # Habilitar/desabilitar Chemperium
  method: cbs-qb3                  # Método (cbs-qb3 ou g3mp2b3)
  dimension: 3d                    # Dimensão (sempre 3d para usar geometrias)
  data_location: null              # null = usar modelos padrão do pacote
```

#### **Banco de Dados (Supabase)**
```sql
-- Novas colunas na tabela molecules
ALTER TABLE molecules ADD COLUMN smiles TEXT;
ALTER TABLE molecules ADD COLUMN hf_chemp DECIMAL;           -- Entalpia Chemperium
ALTER TABLE molecules ADD COLUMN hf_chemp_uncertainty DECIMAL;  -- Incerteza
ALTER TABLE molecules ADD COLUMN chemperium_reliability DECIMAL; -- Score confiabilidade
```

## 🔧 Implementação Técnica

### **1. Δ-Learning Workflow**

```python
# 1. Executar fluxo tradicional (CREST + MOPAC)
molecule = Molecule(name="etanol")
pubchem_service.get_sdf_by_name(molecule.name)
conversion_service.sdf_to_xyz(molecule)
calculation_service.run_calculation(molecule)  # CREST + MOPAC

# 2. Obter SMILES
smiles = pubchem_service.get_smiles_by_name(molecule.name)

# 3. Usar MOPAC como LLOT para Chemperium
llot_kcal = molecule.enthalpy_kj_mol / 4.184  # Converter para kcal/mol
enthalpy_chemp, uncertainty = chemperium_service.predict_enthalpy_with_llot(
    smiles=smiles,
    xyz_content=xyz_content,
    llot_enthalpy=llot_kcal
)

# 4. Converter e armazenar resultados
molecule.enthalpy_chemperium_kj_mol = enthalpy_chemp * 4.184
molecule.enthalpy_chemperium_uncertainty_kj_mol = uncertainty * 4.184
```

### **2. Tratamento de Errors**

```python
from utils.exceptions import ChemperiumError

try:
    enthalpy, uncertainty = chemperium_service.predict_enthalpy_with_llot(...)
except ChemperiumError as e:
    if "not installed" in str(e):
        print("Chemperium não está instalado. Execute: pip install chemperium")
    else:
        print(f"Erro no cálculo Chemperium: {e}")
```

### **3. Configuração de Geometrias**

```python
# Usa confôrmero de menor energia (best conformer) do CREST
if molecule.crest_best_path and os.path.exists(molecule.crest_best_path):
    with open(molecule.crest_best_path, 'r') as f:
        xyz_content = f.read()
else:
    # Fallback para geometria inicial do PubChem
    with open(molecule.xyz_path, 'r') as f:
        xyz_content = f.read()
```

## 📊 Saída dos Resultados

### **1. Console**
```
=== Resultados para etanol ===
MOPAC:      -234.567 kJ/mol
Chemperium: -235.123 ± 1.234 kJ/mol
Diferença:  -0.556 kJ/mol
```

### **2. Show Results**
```
Molécula    CID    MOPAC (kJ/mol)  Chemperium (kJ/mol)       Arquivo Confôrmeros
etanol      702    -234.567        -235.123 ± 1.234         crest_conformers.xyz
```

### **3. Supabase Dashboard**
- **hf_mopac**: -234.567 (kJ/mol)
- **hf_chemp**: -235.123 (kJ/mol)
- **hf_chemp_uncertainty**: 1.234 (kJ/mol)
- **chemperium_reliability**: 0.95

## 🎛️ Controle de Qualidade

### **1. Verificação de Instalação**
```python
chemperium_service = ChemperiumService(config)
if not chemperium_service.is_available():
    print("Chemperium não disponível. Funcionalidade desabilitada.")
```

### **2. Validação de Entrada**
- SMILES válido obtido do PubChem
- Arquivos XYZ com coordenadas válidas  
- LLOT numérico válido do MOPAC

### **3. Score de Confiabilidade**
- Chemperium retorna score 0-1 indicando confiança na predição
- Valores baixos (<0.5) indicam predições com maior incerteza

## 🧪 Testing

### **1. Testes Unitários**
```bash
python -m pytest tests/test_chemperium_service.py -v
```

### **2. Testes de Integração**
```bash
# Teste com molécula conhecida
python main.py
# Escolha: 2. Cálculo com Chemperium
# Digite: ethanol
```

### **3. Validação de Resultados**
- Compare com dados experimentais disponíveis
- Verifique consistência entre MOPAC e Chemperium
- Monitore scores de confiabilidade

## 🚀 Instalação e Configuração

### **1. Dependências**
```bash
pip install chemperium
pip install rdkit tensorflow>=2.12.0,<=2.15.0
```

### **2. Configuração Inicial**
```bash
# Execute o programa 
python main.py

# Configure Chemperium via menu
# Opção 5: Editar configurações
# Configure método (cbs-qb3 padrão, g3mp2b3 mais rápido)
```

### **3. Banco de Dados**
```sql
-- Execute no Editor SQL do Supabase
\i add_chemperium_columns.sql
```

## 🔍 Debugging

### **1. Logs Detalhados**
```bash
# Verificar logs em logs/conformer_search_YYYYMMDD_HHMMSS.log
tail -f logs/conformer_search_*.log
```

### **2. Verificação Manual**
```python
import chemperium as cp

# Teste básico
thermo = cp.Thermo("cbs-qb3", "3d")
result = thermo.predict_enthalpy(
    smiles="CCO",  # Etanol
    xyz=xyz_coords,
    llot=-234.567/4.184  # MOPAC em kcal/mol
)
print(result)
```

## 🔧 Configurações Avançadas

### **1. Métodos Disponíveis**
- **cbs-qb3**: Mais preciso, mais lento
- **g3mp2b3**: Mais rápido, boa precisão

### **2. Customização de Modelos**
```yaml
chemperium:
  data_location: "/path/to/custom/models"  # Modelos customizados
```

### **3. Controle de Temperatura**
```python
# Cálculos em temperaturas específicas
result = thermo.predict_enthalpy(smiles, xyz, llot, t=373.15)  # 100°C
```

## 📚 Referências

- **Chemperium**: [GitHub Repository](https://github.com/mrodobbe/chemperium)
- **Paper**: Dobbelaere et al., "Geometric Deep Learning for Molecular Property Predictions"
- **CREST**: Grimme Group conformer sampling tool
- **MOPAC**: Stewart semi-empirical quantum chemistry package

## 🤝 Contribuição

Para reportar bugs ou sugerir melhorias na integração Chemperium:

1. Abra um issue descrevendo o problema
2. Inclua logs relevantes e configurações
3. Especifique versões do Chemperium e dependências
4. Forneça exemplos reproduzíveis quando possível

---

*Documentação atualizada para Grimme Thermo v1.2.0 - Integração Chemperium*
