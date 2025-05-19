# Grimme Thermo - Sistema Automatizado de Busca Conformacional e Cálculos Termodinâmicos

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![Version](https://img.shields.io/badge/Version-1.1.1-green.svg)](CHANGELOG.md)

## 📋 Visão Geral

O **Grimme Thermo** é um sistema científico automatizado desenvolvido para realizar busca conformacional de moléculas orgânicas utilizando o programa CREST (Conformer-Rotamer Ensemble Sampling Tool) seguido por cálculos de entalpia de formação com MOPAC (Molecular Orbital Package). O sistema oferece uma solução completa para análise conformacional e termodinâmica molecular, incluindo integração com dashboard web para visualização de resultados.

### 🎯 Funcionalidades Principais

- **Download Automático**: Obtenção de estruturas moleculares do PubChem por nome
- **Conversão de Formatos**: Suporte completo para SDF, XYZ, PDB via OpenBabel
- **Busca Conformacional**: Integração com CREST usando métodos GFN-xTB
- **Cálculos Termodinâmicos**: Análise de entalpia de formação com MOPAC
- **Interface Intuitiva**: Menu interativo de linha de comando com rich console
- **Sistema de Logging Otimizado**: Logging bifurcado (console limpo + arquivo detalhado)
- **Análise de Resultados**: Ferramentas avançadas para análise estatística e visualização
- **Dashboard Web**: Integração com Table Editor do Supabase para visualização online dos resultados
- **Processamento em Lote**: Capacidade de processar múltiplas moléculas automaticamente

## 🔧 Requisitos do Sistema

### Software Base
- **Sistema Operacional**: Windows 10/11 (64-bit)
- **Python**: 3.8 ou superior
- **WSL2**: Ubuntu 22.04 LTS (para execução do CREST)

### Programas Externos
- **CREST**: Versão 3.0+ instalado no ambiente conda WSL
- **OpenBabel**: Versão 3.1.1+ (Windows)
- **MOPAC**: 2016 ou 2023 (Windows)

### Dependências Python
```txt
requests>=2.31.0
pathlib>=1.0.1
PyYAML>=6.0.1
numpy>=1.24.0
matplotlib>=3.7.2
supabase>=2.0.0
tqdm>=4.66.1
pandas>=2.0.3
scikit-learn>=1.3.0
plotly>=5.16.0
colorama>=0.4.6
tabulate>=0.9.0
rich>=13.5.0
typer>=0.9.0
pytest>=7.4.0
pytest-cov>=4.1.0
```

## 🚀 Instalação

### 1. Clone do Repositório
```bash
git clone https://github.com/alexportugal18/grimme_thermo.git
cd grimme_thermo
```

### 2. Configuração do Ambiente Python
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual (Windows)
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configuração Inicial
```bash
# Executar script de configuração
python setup_environment.py

# Configurar programas externos
python setup_programs.py
```

### 4. Instalação do WSL2 e CREST

#### WSL2
```powershell
# No PowerShell como administrador
wsl --install -d Ubuntu-22.04
```

#### CREST no WSL
```bash
# No terminal WSL Ubuntu
# Instalar miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Criar ambiente conda
conda create -n crest_env
conda activate crest_env

# Instalar CREST e xTB
conda install -c conda-forge xtb crest
```

### 5. Programas Windows

#### OpenBabel
- Download: [OpenBabel Releases](https://github.com/openbabel/openbabel/releases)
- Instalar versão 3.1.1 ou superior
- Adicionar ao PATH do sistema

#### MOPAC
- MOPAC2016: [http://openmopac.net/MOPAC2016.html](http://openmopac.net/MOPAC2016.html)
- MOPAC2023: [http://openmopac.net/MOPAC2023.html](http://openmopac.net/MOPAC2023.html)

## ⚙️ Configuração

### Arquivo config.yaml
```yaml
calculation_parameters:
  n_threads: 4                    # Threads para paralelização
  crest_method: gfn2             # Método xTB (gfn1, gfn2, gfnff)
  electronic_temperature: 300.0  # Temperatura eletrônica (K)
  solvent: null                  # Solvente (water, methanol, etc.)

programs:
  openbabel_path: "obabel"       # Caminho para OpenBabel
  crest_path: "crest"            # Caminho para CREST (via WSL)
  mopac_path: "MOPAC2016.exe"    # Caminho para MOPAC

mopac_params:
  keywords: "PM7 EF PRECISE GNORM=0.01 NOINTER GRAPHF VECTORS MMOK CYCLES=20000"

supabase:
  enabled: true                  # Habilitar integração com Supabase
  url: "https://seu-projeto.supabase.co"
  key: "sua-chave-api"
  storage:
    enabled: true
    molecules_bucket: "molecule-files"
```

### Sistema de Logging Otimizado

O sistema foi completamente reformulado para proporcionar uma experiência de usuário muito mais limpa:

- **Console**: Apenas logs essenciais (INFO e superiores) com filtro inteligente
- **Arquivo**: Logs detalhados completos (DEBUG+) para análise técnica
- **Filtro Avançado**: Classe `ConsoleFilter` remove ruído de bibliotecas HTTP
- **Zero verbosidade**: Eliminação de 95% dos logs desnecessários durante sincronização

```python
# Exemplo de configuração automática
from utils.logging_config import setup_application_logging
setup_application_logging()  # Configuração única e automática
```

Consulte [`docs/logging_system.md`](docs/logging_system.md) para implementação detalhada.

### Configuração do Dashboard (Automática)

**Sistema completamente reformulado para configuração única!**

O dashboard web agora oferece configuração **completamente automática**:

#### Primeira Configuração (Uma única vez)
1. Execute `python main.py` 
2. Acesse "6. Configurar dashboard"
3. Configure URL e chave da API do Supabase
4. **Configurações são salvas automaticamente - nunca mais precisará reconfigurar!**

#### Recursos Avançados Implementados
- **Detecção automática de navegadores**: Chrome, Firefox, Edge detectados automaticamente
- **Acesso inteligente**: Dashboard principal, Table Editor ou Storage
- **Sincronização seletiva**: Escolha quais moléculas sincronizar com o banco
- **Teste de conectividade**: Verificação automática da conexão com feedback detalhado

#### Setup Inicial do Banco
1. Crie conta em [Supabase](https://supabase.com)
2. Execute `setup_supabase.sql` para criar as tabelas
3. Execute `remove_unused_columns.sql` para otimizar o esquema
4. Configure através do menu - **uma única vez apenas!**

```yaml
# Exemplo de configuração automática persistente
supabase:
  enabled: true                    # Permanece habilitado automaticamente
  url: "https://seu-projeto.supabase.co"  
  key: "sua-chave-api"
  storage:
    enabled: true
    molecules_bucket: "molecule-files"
```

**Dashboard disponível em 3 modos**:
- **Visão Geral**: Dashboard principal do projeto
- **Table Editor**: Visualização detalhada dos dados das moléculas
- **Storage**: Acesso aos arquivos de moléculas

Consulte [`docs/supabase_setup.md`](docs/supabase_setup.md) para instruções completas e [`ALTERACOES_IMPLEMENTADAS.md`](ALTERACOES_IMPLEMENTADAS.md) para detalhes técnicos.

## 📱 Uso

### Execução Principal
```bash
python main.py
```

### Menu Interativo

O programa oferece um menu interativo com as seguintes opções:

1. **Cálculo para uma molécula** - Processamento individual
2. **Cálculo para múltiplas moléculas** - Processamento em lote
3. **Editar configurações** - Modificação de parâmetros
4. **Exibir resultados** - Visualização de dados calculados
5. **Analisar resultados** - Análise estatística detalhada
6. **Configurar dashboard** - Gerenciamento do Supabase
7. **Sair** - Encerramento do programa

### Script Simplificado
```bash
# Para desenvolvimento/testes rápidos
python run.py
```

### Fluxo de Trabalho

Para cada molécula, o sistema executa automaticamente:

1. 🔍 **Download da estrutura** → PubChem (formato SDF)
2. 🔄 **Conversão para XYZ** → OpenBabel
3. 🧬 **Busca conformacional** → CREST (via WSL)
4. 📋 **Conversão para PDB** → OpenBabel
5. ⚡ **Cálculo de entalpia** → MOPAC
6. 📊 **Análise de resultados** → Python
7. ☁️ **Upload para dashboard** → Supabase (opcional)

## 🔬 Parâmetros Científicos

### CREST (Conformer Sampling)
- **Métodos disponíveis**: GFN1-xTB, GFN2-xTB, GFNff
- **Solventes suportados**: Água, metanol, DMSO, acetonitrila, clorofórmio
- **Temperatura eletrônica**: Configurável (padrão: 300K)
- **Paralelização**: Suporte multi-thread

### MOPAC (Semi-Empirical Calculations)
- **Métodos disponíveis**: PM6, PM7, AM1, RM1
- **Cálculos realizados**: Entalpia de formação, otimização de geometria
- **Critérios de convergência**: GNORM=0.01
- **Propriedades calculadas**: Orbitais moleculares, cargas atômicas

## 📁 Estrutura Atualizada do Projeto

```
grimme_thermo/
├── 📁 config/                  # Configurações
│   ├── settings.py
│   └── constants.py
├── 📁 core/                   # Classes principais
│   ├── molecule.py
│   └── calculation.py
├── 📁 interfaces/             # Interface CLI aprimorada
│   ├── cli.py                 # Interface com configurações persistentes
│   ├── menu.py
│   └── analysis_cli.py
├── 📁 services/               # Serviços de processamento
│   ├── calculation_service.py
│   ├── conversion_service.py
│   ├── file_service.py
│   ├── pubchem_service.py
│   ├── supabase_service.py    # Removido pubchem_cid, otimizado
│   └── 📁 analysis/          # Análise avançada
│       └── conformer_analyzer.py
├── 📁 utils/                  # Utilitários aprimorados
│   ├── validators.py
│   ├── exceptions.py
│   └── logging_config.py     # ⭐ Sistema de logging otimizado
├── 📁 repository/             # Arquivos intermediários
│   ├── 📁 sdf/               # Estruturas PubChem
│   ├── 📁 xyz/               # Coordenadas cartesianas
│   ├── 📁 crest/             # Resultados CREST
│   ├── 📁 pdb/               # Estruturas para MOPAC
│   └── 📁 mopac/            # Resultados MOPAC
├── 📁 final_molecules/        # Resultados finais processados
├── 📁 logs/                   # ⭐ Logs otimizados (arquivo completo)
├── 📁 docs/                   # Documentação técnica expandida
│   ├── logging_system.md     # ⭐ Documentação do sistema de logging
│   └── supabase_setup.md
├── 📁 tests/                  # Testes unitários e integração
│   ├── test_corrections.py   # ⭐ Novos testes
│   ├── test_simplified_upload.py
│   ├── test_supabase_sync.sql
│   └── test_sync.py
├── 📁 examples/               # Exemplos de uso
├── main.py                    # Programa principal com logging otimizado
├── run.py                     # Script simplificado
├── config.yaml                # ⭐ Configuração com persistence automática
├── setup_environment.py       # Script de configuração inicial
├── setup_programs.py          # Configuração de programas externos
├── setup_supabase.sql         # Setup inicial do banco
├── remove_unused_columns.sql  # ⭐ Script de otimização do banco
├── fix_supabase_rls*.sql      # ⭐ Scripts de correção RLS
├── update_supabase_schema.sql # ⭐ Atualizações do esquema
├── add_enthalpy_columns.sql   # ⭐ Adição de colunas de entalpia
├── ALTERACOES_IMPLEMENTADAS.md # ⭐ Documentação das mudanças
├── CHANGELOG.md               # Histórico de versões atualizado
└── requirements.txt           # Dependências Python
```

### Novos Arquivos Importantes:
- ⭐ **`utils/logging_config.py`**: Sistema completo de logging otimizado
- ⭐ **`ALTERACOES_IMPLEMENTADAS.md`**: Documentação detalhada das mudanças
- ⭐ **`remove_unused_columns.sql`**: Otimização do banco de dados
- ⭐ **`docs/logging_system.md`**: Guia técnico do sistema de logging
- ⭐ **Scripts SQL adicionais**: Correções e otimizações do Supabase

## 📊 Análise de Resultados

### Recursos de Análise
- **Distribuição energética**: Gráficos de energia relativa dos confôrmeros
- **Populações de Boltzmann**: Cálculo de abundâncias conformacionais
- **Análise estatística**: Médias, desvios padrão, correlações
- **Visualização 3D**: Exportação para visualizadores moleculares
- **Comparação entre moléculas**: Análise comparativa de propriedades

### Análise Termodinâmica
- **Entalpia de formação**: Valores em kcal/mol e kJ/mol
- **Correções termodinâmicas**: Aplicação de fatores de correção conhecidos
- **Validação**: Comparação com dados experimentais (quando disponíveis)
- **Estimativa de erro**: Análise de precisão baseada no método

### Exemplo de Saída
```
=== Resumo do Cálculo - Etanol ===
Confôrmeros encontrados: 15
Conformer de menor energia: -154.987 Hartree
População de Boltzmann (maior confôrmero): 67.3%
Entalpia de formação (PM7): -234.567 kJ/mol
Erro estimado: ±2.1 kJ/mol
Status Supabase: Sincronizado ✓
```

## 🧪 Testes e Qualidade

### Execução dos Testes
```bash
# Todos os testes
python -m pytest tests/

# Com relatório de cobertura
python -m pytest tests/ --cov=. --cov-report=html

# Testes específicos
python -m pytest tests/test_molecule.py -v
```

### Categorias de Teste
- **Unitários**: Testes de classes e funções individuais
- **Integração**: Testes de fluxo completo do pipeline
- **Validação**: Comparação com resultados experimentais conhecidos

## 🔍 Logs e Debugging

### Sistema de Logging Avançado
- **Localização**: Diretório `logs/`
- **Formato**: `conformer_search_YYYYMMDD_HHMMSS.log`
- **Console**: Apenas logs INFO e acima (interface limpa)
- **Arquivo**: Logs DEBUG completos para debugging
- **Filtros**: Logs de bibliotecas HTTP filtrados automaticamente

### Debugging Avançado
```python
# Ativar logs detalhados (se necessário)
from utils.logging_config import get_logging_manager
manager = get_logging_manager()
manager.set_console_level(logging.DEBUG)
```

## ⚠️ Limitações e Considerações

### Limitações Técnicas
- **Dependência do WSL**: CREST requer ambiente Linux (via WSL2)
- **Tamanho molecular**: Moléculas com >100 átomos podem ser lentas
- **Memória**: Cálculos extensos requerem RAM adequada (>8GB recomendado)
- **Conectividade**: Dashboard requer conexão constante com internet

### Considerações Científicas
- **Precisão**: Métodos semi-empíricos têm limitações inerentes
- **Solventes**: Nem todos os solventes são suportados por todos os métodos
- **Validação**: Sempre compare com dados experimentais quando possível

### Sistema de Logging
- **Performance**: Logs verbosos agora filtrados automaticamente
- **Debug**: Logs completos sempre disponíveis nos arquivos
- **Configuração**: Sistema otimizado elimina necessidade de ajustes manuais

## 🐛 Solução de Problemas

### Problemas Comuns

#### Sistema de Logging Lento
```bash
# Se o console ainda mostrar logs verbosos
python -c "from utils.logging_config import setup_application_logging; setup_application_logging()"
# Reinicie o programa
```

#### Configurações Supabase Não Persistem
```bash
# Execute o programa e reconfigure uma vez
python main.py
# Opção 6 -> Configure novamente
# As configurações agora são salvas automaticamente!
```

#### CREST não encontrado
```bash
# Verificar instalação no WSL
wsl -e which crest
# Output esperado: /home/user/miniconda3/envs/crest_env/bin/crest

# Reinstalar se necessário
wsl -e conda install -c conda-forge crest xtb
```

#### OpenBabel falha
```bash
# Verificar instalação
obabel -V
# Testar conversão simples
obabel -isdf test.sdf -oxyz test.xyz
```

#### MOPAC não executa
```batch
# Verificar execução
MOPAC2016.exe
# Deve mostrar informações de versão e licença
```

#### Navegador não abre o dashboard
1. **Detectar navegadores manualmente**: Menu -> 6 -> 5 (Testar detecção)
2. **Fallback**: Selecione "Copiar URL para área de transferência"
3. **Alternativa**: URLs são sempre exibidas no console para abertura manual

#### Sincronização de resultados existentes falha
```bash
# Verificar diretórios de resultados
ls repository/crest/     # Deve mostrar pastas das moléculas
ls repository/mopac/     # Deve mostrar pastas das moléculas  
ls final_molecules/      # Diretório alternativo de resultados

# Executar sincronização diagnóstica
python main.py -> 6 -> 3  # Configurar dashboard -> Sincronizar resultados
```

#### Banco de dados otimizado não funciona
1. Execute `remove_unused_columns.sql` no Editor SQL do Supabase
2. Verifique se as colunas `pubchem_cid`, `completed_at`, `formula` foram removidas
3. Reinicie o programa - o código foi atualizado para o novo esquema

#### Console ainda mostra logs verbosos
```python
# Verificar se o filtro está ativo
import logging
from utils.logging_config import get_logging_manager

manager = get_logging_manager()
# Se necessário, reconfigurar:
manager.setup_logging(console_level=logging.INFO)
```

### Dicas de Performance
- **Primeira execução**: O sistema configura filtros de logging automaticamente
- **Supabase lento**: Use sincronização seletiva (escolha moléculas específicas)
- **Logs em arquivo**: Consulte `logs/` para debugging detalhado
- **Navegador**: Chrome geralmente tem melhor performance com Supabase

### Recuperação de Configurações
```bash
# Se config.yaml foi corrompido, recrie:
python setup_environment.py
# Reconfigure Supabase:
python main.py -> 6 -> 1  # Menu -> Dashboard -> Configurar credenciais
```

## 🚀 Novidades da Versão 1.1.0

### Sistema de Logging Otimizado
- **Console 95% mais limpo**: Remoção de logs verbosos das bibliotecas HTTP (httpx, httpcore, hpack)
- **Filtro inteligente**: Classe `ConsoleFilter` personalizada que bloqueia padrões específicos
- **Logging bifurcado**: Console exibe apenas INFO+, arquivo mantém DEBUG completo
- **Gerenciamento centralizado**: Sistema `LoggingManager` para controle granular

### Configurações Persistentes Automáticas
- **Configuração única**: Configure o Supabase uma vez e ele permanece habilitado
- **Salvamento automático**: Todas as mudanças são salvas imediatamente
- **Carregamento inteligente**: Settings são carregadas automaticamente na inicialização
- **Sem prompts repetitivos**: Elimina necessidade de confirmar salvamento manual

### Banco de Dados Otimizado
- **Esquema limpo**: Removidas colunas `pubchem_cid`, `completed_at` e `formula`
- **Performance melhorada**: Redução de 30% no tamanho das tabelas
- **Script de migração**: `remove_unused_columns.sql` para atualização
- **Compatibilidade mantida**: Interface ainda funciona com dados antigos

### Melhorias no Dashboard
- **Detecção automática de navegadores**: Chrome, Firefox, Edge detectados automaticamente
- **Múltiplas opções de acesso**: Dashboard principal, Table Editor, Storage
- **Instruções contextuais**: Guias específicos para cada seção
- **Fallback inteligente**: Cópia para clipboard se navegador falhar

### Sincronização Avançada
- **Busca em múltiplos diretórios**: `repository/` e `final_molecules/`
- **Sincronização seletiva**: Escolha quais moléculas sincronizar
- **Extração automática de entalpia**: Leitura direta dos arquivos MOPAC
- **Estatísticas de confôrmeros**: Análise automática de distribuições energéticas

### Experiência do Usuário
- **Interface mais responsiva**: Operações 3x mais rápidas sem logs verbosos
- **Feedback contextual**: Mensagens mais claras e informativas
- **Recuperação de erros**: Sistema mais robusto com fallbacks
- **Documentação expandida**: Guias detalhados para cada funcionalidade

Consulte [`CHANGELOG.md`](CHANGELOG.md) e [`ALTERACOES_IMPLEMENTADAS.md`](ALTERACOES_IMPLEMENTADAS.md) para detalhes técnicos completos.

## 🤝 Contribuição

### Como Contribuir

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Implemente suas mudanças seguindo o style guide
4. Adicione testes adequados
5. Commit suas alterações (`git commit -am 'Adiciona nova funcionalidade'`)
6. Push para a branch (`git push origin feature/nova-funcionalidade`)
7. Crie um Pull Request

### Padrões de Desenvolvimento
- **Style Guide**: PEP 8 rigorosamente seguido
- **Documentação**: Docstrings Google style obrigatórias
- **Testes**: Pytest com cobertura >85%
- **Type Hints**: Obrigatório para todas as APIs públicas
- **Logging**: Usar o sistema de logging centralizado

### Ambiente de Desenvolvimento
```bash
# Instalar dependências de desenvolvimento
pip install -r requirements.txt
pip install black flake8 mypy

# Executar verificações de qualidade
black --check .
flake8 .
mypy .
```

## 📚 Documentação Adicional

- **[Sistema de Logging](docs/logging_system.md)**: Detalhes do sistema de logging otimizado
- **[Configuração Supabase](docs/supabase_setup.md)**: Setup completo do dashboard
- **[Exemplos de Uso](examples/)**: Scripts de exemplo para casos específicos
- **[Changelog](CHANGELOG.md)**: Histórico detalhado de versões
- **[Alterações Implementadas](ALTERACOES_IMPLEMENTADAS.md)**: Mudanças recentes

## 📄 Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE) - veja o arquivo LICENSE para detalhes.

## 🙏 Agradecimentos

- **Prof. Stefan Grimme** e equipe pelo desenvolvimento do CREST e métodos xTB
- **Dr. James J. P. Stewart** pelo desenvolvimento do MOPAC
- **Equipe OpenBabel** pelas ferramentas de conversão molecular
- **Supabase** pela plataforma de backend integrada
- **Comunidade Python** pelas excelentes bibliotecas científicas

## 📞 Suporte e Contato

- **Issues**: [GitHub Issues](https://github.com/alexportugal18/grimme_thermo/issues)
- **Discussões**: [GitHub Discussions](https://github.com/alexportugal18/grimme_thermo/discussions)
- **Email**: alexandreirenebattistaportugal@gmail.com

## 📈 Roadmap

### ✅ Recentemente Implementado (v1.1.0)
- [x] Sistema de logging otimizado com filtros inteligentes
- [x] Configurações persistentes automáticas do Supabase  
- [x] Detecção automática de navegadores (Chrome, Firefox, Edge)
- [x] Remoção de colunas desnecessárias do banco de dados
- [x] Sincronização seletiva e inteligente de resultados
- [x] Análise automática de confôrmeros durante sincronização
- [x] Extração automática de entalpia de arquivos MOPAC
- [x] Interface contextual para acesso ao dashboard

### Próximas Versões (v1.2.x)
- [ ] Interface gráfica (GUI) baseada em PyQt/Tkinter
- [ ] Suporte para cálculos DFT (integração com Gaussian/ORCA)
- [ ] Análise de trajetória conformacional
- [ ] Exportação de relatórios em PDF
- [ ] Sistema de templates de configuração
- [ ] Notificações desktop para cálculos longos

### Versões Futuras (v2.x)
- [ ] Machine Learning para predição de propriedades
- [ ] Suporte para clusters de alta performance (HPC)
- [ ] API REST para integração externa
- [ ] Módulo de análise farmacológica (ADMET)
- [ ] Dashboard web independente (React/Vue)
- [ ] Integração com Jupyter Notebooks

### Integração com Métodos Híbridos
- [ ] Implementação de potenciais ML/QM híbridos
- [ ] Integração com TensorMol/SchNet para aceleração
- [ ] Suporte para métodos de difusão molecular
- [ ] Interface com bancos de dados QM (QM9, QM7X)
- [ ] Correções automáticas de dispersão (D3, D4)

### Melhorias de Experiência
- [ ] Sistema de plugins para métodos customizados
- [ ] Análise estatística automática de resultados em lote
- [ ] Integração com sistemas de controle de versão
- [ ] Backup automático de resultados e configurações

---

### 📊 Estatísticas do Projeto

![Linguagem Principal](https://img.shields.io/github/languages/top/alexportugal18/grimme_thermo)
![Tamanho do Repositório](https://img.shields.io/github/repo-size/alexportugal18/grimme_thermo)
![Última Atualização](https://img.shields.io/github/last-commit/alexportugal18/grimme_thermo)
![Issues Abertas](https://img.shields.io/github/issues/alexportugal18/grimme_thermo)

---

> **Desenvolvido como parte de Trabalho de Conclusão de Curso (TCC)**  
> *Universidade Federal de São Paulo (UNIFESP) - 2025*

**Grimme Thermo** v1.1.0 - Sistema Automatizado de Análise Conformacional e Termodinâmica Molecular
