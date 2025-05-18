# Grimme Thermo - Sistema Automatizado de Busca Conformacional e Cálculos Termodinâmicos

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

## 📋 Visão Geral

O **Grimme Thermo** é um sistema científico automatizado desenvolvido para realizar busca conformacional de moléculas orgânicas utilizando o programa CREST (Conformer-Rotamer Ensemble Sampling Tool) seguido por cálculos de entalpia de formação com MOPAC (Molecular Orbital Package). O sistema oferece uma solução completa para análise conformacional e termodinâmica molecular, incluindo integração com dashboard web para visualização de resultados.

### 🎯 Funcionalidades Principais

- **Download Automático**: Obtenção de estruturas moleculares do PubChem por nome
- **Conversão de Formatos**: Suporte completo para SDF, XYZ, PDB via OpenBabel
- **Busca Conformacional**: Integração com CREST usando métodos GFN-xTB
- **Cálculos Termodinâmicos**: Análise de entalpia de formação com MOPAC
- **Interface Intuitiva**: Menu interativo de linha de comando
- **Análise de Resultados**: Ferramentas avançadas para análise estatística e visualização
- **Dashboard Web**: Integração com Supabase para visualização online dos resultados

## 🔧 Requisitos do Sistema

### Software Base
- **Sistema Operacional**: Windows 10/11
- **Python**: 3.8 ou superior
- **WSL2**: Ubuntu 22.04 (para execução do CREST)

### Programas Externos
- **CREST**: Instalado no ambiente conda WSL
- **OpenBabel**: Versão 3.1.1+ (Windows)
- **MOPAC**: 2016 ou 2023 (Windows)

### Dependências Python
```txt
requests>=2.31.0
PyYAML>=6.0.1
numpy>=1.24.0
matplotlib>=3.7.2
supabase>=2.0.0
tqdm>=4.66.1
pandas>=2.0.3
plotly>=5.16.0
colorama>=0.4.6
rich>=13.5.0
typer>=0.9.0
```

## 🚀 Instalação

### 1. Clone do Repositório
```bash
git clone https://github.com/seu-usuario/grimme_thermo.git
cd grimme_thermo
```

### 2. Configuração do Ambiente Python
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows
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
  openbabel_path: "C:\\Program Files\\OpenBabel-3.1.1\\obabel.exe"
  crest_path: "\\\\wsl.localhost\\Ubuntu-22.04\\home\\user\\miniconda3\\envs\\crest_env\\bin\\crest"
  mopac_path: "C:\\Program Files\\MOPAC\\MOPAC2016.exe"

mopac_params:
  keywords: "PM7 EF PRECISE GNORM=0.01 NOINTER GRAPHF VECTORS MMOK CYCLES=20000"

supabase:
  enabled: true
  url: "https://seu-projeto.supabase.co"
  key: "sua-chave-api"
  storage:
    enabled: true
    molecules_bucket: "molecule-files"
```

### Configuração do Dashboard (Opcional)

Para ativar o dashboard web baseado em Supabase:

1. Crie uma conta em [Supabase](https://supabase.com)
2. Configure o banco de dados usando `setup_supabase.sql`
3. Obtenha as credenciais da API
4. Atualize o arquivo `config.yaml` ou use o menu do programa

Consulte [`docs/supabase_setup.md`](docs/supabase_setup.md) para instruções detalhadas.

## 📱 Uso

### Execução Principal
```bash
python main.py
```

### Script Simplificado
```bash
python run.py --molecule "etanol" --method "gfn2" --solvent "water"
```

### Menu Interativo

O programa oferece um menu com as seguintes opções:

1. **Cálculo para uma molécula** - Processamento individual
2. **Cálculo para múltiplas moléculas** - Processamento em lote
3. **Editar configurações** - Modificação de parâmetros
4. **Exibir resultados** - Visualização de dados calculados
5. **Analisar resultados** - Análise estatística detalhada
6. **Configurar dashboard** - Gerenciamento do Supabase
7. **Sair** - Encerramento do programa

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

### CREST
- **Métodos disponíveis**: GFN1-xTB, GFN2-xTB, GFNff
- **Solventes**: Água, metanol, DMSO, acetonitrila, etc.
- **Temperatura**: Configurável (padrão: 300K)
- **Paralelização**: Suporte multi-thread

### MOPAC
- **Métodos semi-empíricos**: PM6, PM7, AM1, RM1
- **Cálculos**: Entalpia de formação, otimização de geometria
- **Critérios de convergência**: Configuráveis
- **Propriedades**: Orbitais moleculares, cargas atômicas

## 📁 Estrutura do Projeto

```
grimme_thermo/
├── 📁 config/                  # Configurações e constantes
│   ├── settings.py
│   └── constants.py
├── 📁 core/                   # Classes principais
│   ├── molecule.py
│   └── calculation.py
├── 📁 interfaces/             # Interface de linha de comando
│   ├── cli.py
│   ├── menu.py
│   └── analysis_cli.py
├── 📁 services/               # Serviços de processamento
│   ├── calculation_service.py
│   ├── conversion_service.py
│   ├── pubchem_service.py
│   ├── supabase_service.py
│   └── 📁 analysis/          # Análise de resultados
│       └── conformer_analyzer.py
├── 📁 utils/                  # Utilitários gerais
│   ├── validators.py
│   └── exceptions.py
├── 📁 repository/             # Arquivos intermediários
│   ├── 📁 sdf/               # Estruturas PubChem
│   ├── 📁 xyz/               # Coordenadas cartesianas
│   ├── 📁 crest/             # Resultados CREST
│   ├── 📁 pdb/               # Estruturas para MOPAC
│   └── 📁 mopac/            # Resultados MOPAC
├── 📁 final_molecules/        # Resultados finais
│   └── 📁 output/
├── 📁 tests/                  # Testes unitários
├── 📁 docs/                   # Documentação
├── 📁 examples/               # Exemplos de uso
├── 📁 logs/                   # Arquivos de log
├── main.py                    # Programa principal
├── run.py                     # Script simplificado
├── config.yaml                # Configuração principal
├── requirements.txt           # Dependências Python
└── README.md                  # Este arquivo
```

## 📊 Análise de Resultados

### Análise de Confôrmeros
- **Distribuição energética**: Gráficos de energia relativa
- **Populações de Boltzmann**: Cálculo de abundâncias
- **Propriedades geométricas**: Distâncias e ângulos de ligação
- **Visualização 3D**: Exportação para visualizadores moleculares

### Análise Termodinâmica
- **Entalpia de formação**: Valores calculados e corrigidos
- **Parâmetros termodinâmicos**: Entropia, energia livre de Gibbs
- **Validação**: Comparação com dados experimentais
- **Análise de erro**: Estimativa de precisão

### Exemplo de Saída
```
=== Resumo do Cálculo - Etanol ===
Confôrmeros encontrados: 15
Conformer de menor energia: -154.987 Hartree
População de Boltzmann (maior conformer): 67.3%
Entalpia de formação: -234.567 kJ/mol
Erro estimado: ±2.1 kJ/mol
```

## 🧪 Testes

### Execução dos Testes
```bash
# Todos os testes
python -m pytest tests/

# Com relatório de cobertura
python -m pytest tests/ --cov=. --cov-report=html

# Testes específicos
python -m pytest tests/test_molecule.py
```

### Categorias de Teste
- **Unidade**: Testes de classes individuais
- **Integração**: Testes de fluxo completo
- **Validação**: Comparação com resultados conhecidos

## 🔍 Sistema de Logging

### Configuração Otimizada
O sistema possui logging bifurcado para maior clareza:
- **Console**: Apenas logs essenciais (INFO+)
- **Arquivo**: Logs detalhados (DEBUG+)

### Localização e Formato
- **Diretório**: `logs/`
- **Arquivo**: `conformer_search_YYYYMMDD_HHMMSS.log`
- **Console**: Logs limpos sem informações técnicas
- **Arquivo**: Logs completos com timestamps e detalhes

### Filtros Automáticos
O sistema filtra automaticamente logs verbosos de:
- Bibliotecas HTTP (httpx, httpcore, hpack)
- Operações de rede detalhadas
- Trace logs de debugging interno
- Mantém apenas logs da aplicação e erros importantes

### Debugging
```python
# Para debugging específico
from utils.logging_config import get_logging_manager
manager = get_logging_manager()

# Adicionar padrão para filtrar
manager.add_blocked_pattern("meu_padrao")

# Ajustar nível de módulo específico
manager.set_module_log_level("meu_modulo", logging.DEBUG)
```

Consulte [`docs/logging_system.md`](docs/logging_system.md) para detalhes completos do sistema de logging.

## ⚠️ Limitações Conhecidas

- **Dependência do WSL**: CREST requer ambiente Linux
- **Tamanho molecular**: Moléculas muito grandes podem falhar
- **Solventes**: Nem todos os solventes são suportados por todos os métodos
- **Memória**: Cálculos extensos requerem RAM adequada

## 🐛 Solução de Problemas

### Problemas Comuns

#### CREST não encontrado
```bash
# Verificar instalação no WSL
wsl -e which crest

# Reinstalar se necessário
wsl -e conda install -c conda-forge crest
```

#### OpenBabel falha
```bash
# Verificar instalação
obabel -V

# Testar conversão simples
obabel -isdf input.sdf -oxyz output.xyz
```

#### MOPAC não executa
```powershell
# Verificar licença
MOPAC2016.exe

# Testar execução simples
MOPAC2016.exe test.dat
```

#### Erro de conexão Supabase
- Verificar URL e chave API
- Confirmar conectividade com a internet
- Testar credenciais no painel Supabase

## 🤝 Contribuição

### Como Contribuir

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas alterações (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Crie um Pull Request

### Padrões de Código
- **Style Guide**: PEP 8
- **Documentação**: Docstrings Google style
- **Testes**: Pytest com >90% cobertura
- **Type Hints**: Obrigatório para APIs públicas

## 📚 Documentação Adicional

- **[Configuração Supabase](docs/supabase_setup.md)**: Setup completo do dashboard
- **[Exemplos de Uso](examples/)**: Scripts de exemplo
- **[API Reference](docs/api/)**: Documentação das classes e métodos

## 📄 Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE) - veja o arquivo LICENSE para detalhes.

## 🙏 Agradecimentos

- **Prof. Stefan Grimme** e equipe pelo desenvolvimento do CREST
- **Dr. James J. P. Stewart** pelo desenvolvimento do MOPAC
- **Equipe OpenBabel** pelas ferramentas de conversão molecular
- **Supabase** pela plataforma de backend

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/grimme_thermo/issues)
- **Discussões**: [GitHub Discussions](https://github.com/seu-usuario/grimme_thermo/discussions)
- **Email**: seu-email@dominio.com

## 📈 Roadmap

### Próximas Versões
- [ ] Suporte para cálculos DFT (Gaussian, ORCA)
- [ ] Interface gráfica (GUI)
- [ ] Análise de trajetória molecular
- [ ] Machine Learning para predição de propriedades
- [ ] Suporte para clusters de alta performance
- [ ] API REST para integração externa

---

### 📊 Estatísticas do Projeto

![Linguagem Principal](https://img.shields.io/github/languages/top/seu-usuario/grimme_thermo)
![Tamanho do Repositório](https://img.shields.io/github/repo-size/seu-usuario/grimme_thermo)
![Última Atualização](https://img.shields.io/github/last-commit/seu-usuario/grimme_thermo)

---

*Desenvolvido como parte de Trabalho de Conclusão de Curso (TCC) - 2025*

**Grimme Thermo** v1.0.0 - Sistema Automatizado de Análise Conformacional e Termodinâmica Molecular
