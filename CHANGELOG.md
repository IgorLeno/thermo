# CHANGELOG - Grimme Thermo

## [1.2.0] - 2025-05-19

### Adicionado
- **Integração com Chemperium**: Implementação completa da Opção 2 (Δ-Learning Integration)
  - Serviço Chemperium (`services/chemperium/`) para predições de entalpia
  - Método `predict_enthalpy_with_llot()` usando MOPAC como Lower Level of Theory
  - Método `predict_enthalpy_standalone()` para predições diretas
  - Suporte para métodos CBS-QB3 e G3MP2B3
  - Cálculos 3D utilizando geometrias do CREST

### Modificado
- **Menu Principal**: Adicionadas 4 novas opções de cálculo
  1. Cálculo tradicional (CREST + MOPAC)
  2. Cálculo com Chemperium (CREST + MOPAC + Chemperium) 
  3. Só Chemperium (rápido, sem CREST)
  4. Múltiplas moléculas com Chemperium
  
- **Classe Molecule**: Novos campos para integração Chemperium
  - `smiles`: SMILES da molécula
  - `enthalpy_chemperium_kj_mol`: Entalpia corrigida
  - `enthalpy_chemperium_uncertainty_kj_mol`: Incerteza da predição
  - `chemperium_reliability_score`: Score de confiabilidade
  - Método `set_chemperium_results()` para armazenar resultados

- **PubChem Service**: Método `get_smiles_by_name()` para obter SMILES
- **Supabase Service**: Suporte para campos Chemperium na tabela molecules
- **Menu de Configurações**: Opções para configurar método e dimensão Chemperium

### Configuração
- **Seção [chemperium] no config.yaml**:
  - `enabled`: Habilitar/desabilitar Chemperium
  - `method`: Método de cálculo (cbs-qb3/g3mp2b3)
  - `dimension`: Dimensão molecular (sempre 3d)
  - `data_location`: Localização dos modelos (null = padrão)

### Banco de Dados
- **Novas colunas na tabela molecules**:
  - `smiles`: SMILES canônico
  - `hf_chemp`: Entalpia Chemperium (kJ/mol)
  - `hf_chemp_uncertainty`: Incerteza (kJ/mol)
  - `chemperium_reliability`: Score de confiabilidade
- **Script**: `add_chemperium_columns.sql` para migração

### Dependências
- **chemperium>=1.0.0**: Pacote principal
- **rdkit>=2023.3.3**: Manipulação molecular
- **tensorflow>=2.12.0,<=2.15.0**: Backend ML

### Documentação
- **Guia técnico**: `docs/chemperium_integration.md`
- **Script de teste**: `test_chemperium_integration.py`
- **README atualizado**: Seções sobre Chemperium

### Interface
- **Show Results**: Exibe MOPAC e Chemperium lado a lado
- **Tratamento de erros**: Mensagens específicas para problemas Chemperium
- **Fallback gracioso**: Funciona mesmo se Chemperium não estiver instalado

---

## [1.1.1] - 2025-05-19

### Modificado
- **README.md**: Atualização completa com todas as novas funcionalidades implementadas
  - Seção expandida sobre sistema de logging otimizado
  - Detalhes sobre configurações persistentes automáticas
  - Documentação de novas funcionalidades do dashboard
  - Seção detalhada de solução de problemas atualizada
  - Roadmap atualizado com implementações recentes

### Destacado
- Documentação agora reflete todas as melhorias da v1.1.0
- Guias detalhados para resolução de problemas comuns
- Instruções específicas para configuração automática do Supabase

---

## [1.1.0] - 2025-05-18

### Adicionado
- **Sistema de Logging Otimizado**: Implementado sistema bifurcado de logging
  - Console: Apenas logs essenciais (INFO+) 
  - Arquivo: Logs detalhados completos (DEBUG+)
  - Filtro automático para bibliotecas verbosas (httpx, httpcore, hpack)
  - Classe `ConsoleFilter` para controle granular de logs no console
  - Classe `LoggingManager` para gerenciamento centralizado
  - Documentação completa em [`docs/logging_system.md`](docs/logging_system.md)

### Modificado
- `main.py`: Substituída configuração de logging básica pelo sistema otimizado
- `README.md`: Atualizada seção de logging com novas características

### Benefícios
- Redução drástica de logs verbosos no console durante sincronização Supabase
- Experiência de usuário mais limpa
- Logs completos mantidos em arquivo para debugging
- Sistema flexível e configurável

### Migração
- Usuários existentes: Nenhuma ação necessária, mudança automática
- Sistema backward-compatible com configurações existentes

---

## [1.0.0] - 2025-05-07

### Initial Release
- Sistema completo de busca conformacional com CREST
- Cálculos de entalpia com MOPAC
- Interface CLI interativa
- Integração com Supabase
- Dashboard web
- Análise de resultados
- Documentação completa

---

## Formato

Este changelog segue o formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

### Tipos de Mudança
- **Adicionado**: Para novas funcionalidades
- **Modificado**: Para mudanças em funcionalidades existentes
- **Deprecated**: Para funcionalidades que serão removidas em próximas versões
- **Removido**: Para funcionalidades removidas
- **Corrigido**: Para correções de bugs
- **Segurança**: Para correções de vulnerabilidades
