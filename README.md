# Grimme Thermo - Sistema Automatizado de Busca Conformacional e Cálculos Termodinâmicos

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![Version](https://img.shields.io/badge/Version-1.1.0-green.svg)](CHANGELOG.md)

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

O sistema de logging foi otimizado para reduzir drasticamente a verbosidade no console:

- **Console**: Apenas logs essenciais (INFO e acima)
- **Arquivo**: Logs detalhados completos (DEBUG e acima)
- **Filtro Automático**: Remove logs verbosos de bibliotecas HTTP (httpx, httpcore, hpack)

Consulte [`docs/logging_system.md`](docs/logging_system.md) para detalhes completos.

### Configuração do Dashboard (Opcional)

Para ativar a visualização web dos dados através do Supabase:

1. Crie uma conta em [Supabase](https://supabase.com)
2. Configure o banco de dados usando `setup_supabase.sql`
3. Execute o script `remove_unused_columns.sql` para otimizar o banco
4. Obtenha as credenciais da API
5. Configure através do menu do programa (opção 6)

**Nota sobre Navegadores**: O programa detecta automaticamente Chrome, Firefox e Edge instalados no sistema. Ao abrir o dashboard, você pode escolher qual navegador usar - útil quando diferentes contas Supabase estão logadas em navegadores diferentes.

**Dashboard disponível**:
- **Table Editor**: Para visualizar dados das moléculas e cálculos
- **Storage**: Para visualizar arquivos de moléculas

Consulte [`docs/supabase_setup.md`](docs/supabase_setup.md) para instruções detalhadas.

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
├── 📁 interfaces/             # Interface CLI
│   ├── cli.py
│   ├── menu.py
│   └── analysis_cli.py
├── 📁 services/               # Serviços de processamento
│   ├── calculation_service.py
│   ├── conversion_service.py
│   ├── file_service.py
│   ├── pubchem_service.py
│   ├── supabase_service.py
│   └── 📁 analysis/          # Análise avançada
│       └── conformer_analyzer.py
├── 📁 utils/                  # Utilitários
│   ├── validators.py
│   ├── exceptions.py
│   └── logging_config.py     # Sistema de logging otimizado
├── 📁 repository/             # Arquivos intermediários
│   ├── 📁 sdf/               # Estruturas PubChem
│   ├── 📁 xyz/               # Coordenadas cartesianas
│   ├── 📁 crest/             # Resultados CREST
│   ├── 📁 pdb/               # Estruturas para MOPAC
│   └── 📁 mopac/            # Resultados MOPAC
├── 📁 final_molecules/        # Resultados finais processados
├── 📁 logs/                   # Logs detalhados do sistema
├── 📁 docs/                   # Documentação técnica
│   ├── logging_system.md
│   └── supabase_setup.md
├── 📁 tests/                  # Testes unitários e integração
├── 📁 examples/               # Exemplos de uso
├── main.py                    # Programa principal
├── run.py                     # Script simplificado
├── config.yaml                # Configuração principal
├── setup_environment.py       # Script de configuração inicial
├── setup_programs.py          # Configuração de programas externos
└── requirements.txt           # Dependências Python
```

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

## 🐛 Solução de Problemas

### Problemas Comuns

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

#### Problemas do Supabase
1. Verificar URL e chave API no config.yaml
2. Confirmar conectividade com `curl -I https://seu-projeto.supabase.co`
3. Executar `remove_unused_columns.sql` se necessário
4. Consultar logs detalhados em `logs/`

#### Configurações não persistem
- As configurações agora são salvas automaticamente
- Verifique permissões de escrita no arquivo `config.yaml`
- Consulte `ALTERACOES_IMPLEMENTADAS.md` para detalhes

## 🚀 Novidades da Versão 1.1.0

### Sistema de Logging Otimizado
- Console drasticamente mais limpo durante operações
- Logs completos mantidos em arquivo para debugging
- Filtro automático de logs verbosos de bibliotecas HTTP

### Configurações Persistentes
- Configurações do Supabase agora são salvas automaticamente
- Não é mais necessário reconfigurar a cada execução

### Melhorias no Banco de Dados
- Remoção de colunas desnecessárias (`pubchem_cid`, `completed_at`)
- Esquema otimizado e mais limpo
- Scripts SQL incluídos para atualização

Consulte [`CHANGELOG.md`](CHANGELOG.md) para detalhes completos.

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

### Próximas Versões (v1.2.x)
- [ ] Interface gráfica (GUI) baseada em PyQt/Tkinter
- [ ] Suporte para cálculos DFT (integração com Gaussian/ORCA)
- [ ] Análise de trajetória conformacional
- [ ] Exportação de relatórios em PDF

### Versões Futuras (v2.x)
- [ ] Machine Learning para predição de propriedades
- [ ] Suporte para clusters de alta performance (HPC)
- [ ] API REST para integração externa
- [ ] Módulo de análise farmacológica (ADMET)

### Integração com Métodos Híbridos
- [ ] Implementação de potenciais ML/QM híbridos
- [ ] Integração com TensorMol/SchNet para aceleração
- [ ] Suporte para métodos de difusão molecular
- [ ] Interface com bancos de dados QM (QM9, QM7X)

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
