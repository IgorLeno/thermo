# Grimme Thermo - Busca Conformacional com CREST e Cálculo de Entalpia com MOPAC

## Visão Geral

O **Grimme Thermo** é um software científico para automatizar o fluxo de trabalho de busca conformacional de moléculas orgânicas usando o programa CREST (Conformer-Rotamer Ensemble Sampling Tool) desenvolvido pelo grupo do Prof. Stefan Grimme, seguido por cálculos de entalpia de formação usando MOPAC (Molecular Orbital Package). 

O programa permite:

- Baixar estruturas moleculares diretamente do PubChem por nome de molécula
- Converter formatos de arquivo usando OpenBabel
- Executar busca conformacional usando CREST via Windows Subsystem for Linux (WSL)
- Calcular entalpia de formação usando MOPAC
- Analisar e visualizar os resultados dos cálculos
- Armazenar e visualizar resultados em um dashboard baseado em Supabase

## Principais Funcionalidades

- **Acesso ao PubChem**: Obtenção automática de estruturas moleculares a partir do nome da molécula
- **Integração com OpenBabel**: Conversão eficiente entre formatos de arquivos moleculares (SDF, XYZ, PDB)
- **Integração com CREST**: Busca conformacional completa utilizando métodos GFN-xTB
- **Integração com MOPAC**: Cálculos de entalpia de formação utilizando métodos semi-empíricos
- **Interface de Linha de Comando**: Menu interativo para facilitar o uso
- **Análise de Resultados**: Ferramentas para análise estatística dos conformeros encontrados
- **Dashboard Web**: Visualização de resultados e estatísticas via Supabase
- **Logs detalhados**: Rastreamento de todas as etapas do processo com mensagens informativas
- **Visualização Gráfica**: Gráficos interativos usando Plotly para análise de resultados

## Requisitos

- Python 3.8 ou superior
- Windows 10/11 com WSL2 (Windows Subsystem for Linux) e Ubuntu 22.04 instalado
- CREST instalado no ambiente conda no WSL
- OpenBabel 3.1.1 ou superior instalado no Windows
- MOPAC2016 ou superior instalado no Windows
- Bibliotecas Python listadas em `requirements.txt`

## Instalação

### 1. Preparação do Ambiente

Clone o repositório:
```
git clone https://github.com/seu-usuario/grimme_thermo.git
cd grimme_thermo
```

Instale as dependências Python:
```
pip install -r requirements.txt
```

### 2. Configuração do WSL2

Instale o WSL2 (necessário para o CREST):
```
wsl --install -d Ubuntu-22.04
```

### 3. Instalação do CREST no WSL

Instale o conda no ambiente WSL:
```bash
# No terminal WSL Ubuntu
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

Crie um ambiente conda para o CREST e instale-o:
```bash
# No terminal WSL Ubuntu
conda create -n crest_env
conda activate crest_env
conda install -c conda-forge xtb crest
```

### 4. Instalação de Programas Externos

- Instale o OpenBabel no Windows (versão 3.1.1 ou superior)
  - Download: https://github.com/openbabel/openbabel/releases

- Instale o MOPAC2016 ou MOPAC2023 no Windows
  - MOPAC2016: http://openmopac.net/MOPAC2016.html
  - MOPAC2023: http://openmopac.net/MOPAC2023.html

### 5. Configuração do Projeto

Execute o script de configuração do ambiente:
```
python setup_environment.py
```

Configure o arquivo `config.yaml` com os caminhos corretos para os programas:
```yaml
calculation_parameters:
  n_threads: 4
  crest_method: gfn2
  electronic_temperature: 300.0
  solvent:
programs:
  openbabel_path: C:\Program Files\OpenBabel-3.1.1\obabel.exe
  crest_path: \\wsl.localhost\Ubuntu-22.04\home\seu_usuario\miniconda3\envs\crest_env\bin\crest
  mopac_path: C:\Program Files\MOPAC\MOPAC2016.exe
mopac_params:
  keywords: "PM7 EF PRECISE GNORM=0.01 NOINTER GRAPHF VECTORS MMOK CYCLES=20000"
```

### 6. Configuração do Supabase

Para ativar a integração com o dashboard web:

1. Crie uma conta no Supabase (https://supabase.com)
2. Configure um novo projeto
3. Crie um banco de dados com as tabelas necessárias (script disponível em `setup_supabase.sql`)
4. Configure o storage do Supabase para armazenar arquivos moleculares
5. Atualize as credenciais no arquivo `config.yaml`:
```yaml
supabase:
  enabled: true
  url: https://seu-projeto.supabase.co
  key: sua-chave-api
  storage:
    enabled: true
    molecules_bucket: molecule-files
```

## Uso

### Interface de Linha de Comando

Execute o programa principal:
```
python main.py
```

Ou use o script simplificado para processamento rápido:
```
python run.py --molecule "etanol" --method "gfn2" --solvent "water"
```

### Fluxo de Trabalho

Para cada molécula, o programa segue o seguinte fluxo:

1. **Download da estrutura do PubChem** - Obtém a estrutura molecular em formato SDF
2. **Conversão para XYZ** - Utiliza OpenBabel para converter SDF para XYZ
3. **Busca conformacional com CREST** - Executa CREST via WSL para encontrar confôrmeros
4. **Conversão do melhor confôrmero para PDB** - Prepara o arquivo para o MOPAC
5. **Cálculo de entalpia com MOPAC** - Executa MOPAC para calcular a entalpia de formação
6. **Análise e armazenamento de resultados** - Processa e salva os resultados obtidos
7. **Upload para Supabase** - Envia os resultados para o dashboard web

### Menu Interativo

O programa oferece um menu interativo com as seguintes opções:

1. **Realizar cálculo completo para uma molécula** - Processa uma única molécula
2. **Realizar cálculo completo para várias moléculas** - Processa múltiplas moléculas
3. **Editar configurações** - Modifica parâmetros de cálculo e caminhos
4. **Exibir resultados** - Mostra resumos dos cálculos realizados
5. **Analisar resultados** - Fornece análise detalhada dos confôrmeros
6. **Configurar dashboard (Supabase)** - Gerencia a integração com Supabase
7. **Sair** - Encerra o programa

## Parâmetros de Cálculo

### CREST

Os parâmetros do CREST podem ser configurados no arquivo `config.yaml`:

- **crest_method**: Método de cálculo (gfn1, gfn2, gfnff)
- **electronic_temperature**: Temperatura eletrônica em Kelvin
- **n_threads**: Número de threads para paralelização
- **solvent**: Modelo de solvente (água, metanol, etc.)

### MOPAC

Os parâmetros do MOPAC podem ser configurados no arquivo `config.yaml`:

- **keywords**: Palavras-chave para o cálculo do MOPAC
  - PM7: Método semiempírico
  - EF: Cálculo de entalpia de formação
  - PRECISE: Maior precisão nos critérios de convergência
  - GNORM: Critério de convergência para o gradiente
  - VECTORS: Salva os orbitais moleculares
  - MMOK: Correções de mecânica molecular
  - CYCLES: Número máximo de ciclos SCF

## Estrutura de Diretórios

```
grimme_thermo/
├── config/               # Configurações e constantes
├── core/                 # Classes principais (Molecule, Calculation)
├── interfaces/           # Interface de linha de comando
├── services/             # Serviços para cálculos e processamento
│   ├── analysis/         # Ferramentas de análise de resultados
├── repository/           # Armazenamento de arquivos intermediários
│   ├── crest/            # Resultados da busca conformacional
│   ├── pdb/              # Arquivos PDB para MOPAC
│   ├── mopac/            # Resultados dos cálculos MOPAC
├── final_molecules/      # Resultados finais processados
├── logs/                 # Registros de execução
├── main.py               # Ponto de entrada principal do programa
├── run.py                # Script simplificado para execução
├── setup_environment.py  # Script para configuração do ambiente
├── setup_programs.py     # Script para instalação de programas
├── config.yaml           # Arquivo de configuração principal
├── requirements.txt      # Dependências Python
└── README.md             # Documentação do projeto
```

## Dashboard Web (Supabase)

O dashboard web baseado em Supabase oferece:

- **Visualização de moléculas**: Lista de todas as moléculas processadas
- **Detalhes de cálculos**: Informações detalhadas sobre cada cálculo
- **Estatísticas**: Gráficos e métricas sobre os resultados
- **Comparação de moléculas**: Análise comparativa entre diferentes estruturas
- **Histórico de cálculos**: Rastreamento de todas as execuções
- **Exportação de dados**: Download de resultados em vários formatos

### Acessando o Dashboard

1. Acesse o URL do seu projeto Supabase
2. Faça login com suas credenciais
3. Navegue até a seção "Dashboard" do projeto
4. Selecione a molécula ou o grupo de moléculas para visualização

## Análise de Resultados

O programa inclui ferramentas avançadas para análise de resultados:

### Análise de Confôrmeros

- **Distribuição de energia**: Gráficos de energia relativa dos confôrmeros
- **Populações de Boltzmann**: Cálculo das populações de cada confôrmero
- **Propriedades geométricas**: Análise das distâncias e ângulos entre átomos
- **Visualização 3D**: Exportação para visualizadores moleculares

### Cálculos de Entalpia

- **Entalpia de formação**: Valores calculados pelo MOPAC
- **Parâmetros termodinâmicos**: Entropia, energia livre de Gibbs
- **Comparação com valores experimentais**: Validação dos resultados
- **Análise de erro**: Estimativa da precisão dos cálculos

## Integração com Programas Externos

### CREST

- Suporte para métodos GFN1-xTB, GFN2-xTB e GFNff
- Busca conformacional com diferentes níveis de precisão
- Suporte para cálculos em solvente implícito
- Paralelização eficiente dos cálculos

### MOPAC

- Suporte para métodos semiempíricos (PM6, PM7, AM1, RM1)
- Cálculos de entalpia de formação com correções
- Otimização de geometria com diferentes critérios
- Análise de propriedades eletrônicas

### OpenBabel

- Conversão entre mais de 110 formatos de arquivo
- Limpeza e normalização de estruturas moleculares
- Geração de coordenadas 3D
- Atribuição de tipos de átomo e cargas

## Desenvolvimento e Testes

O projeto inclui suporte completo para testes:

```
# Executar todos os testes
python -m pytest tests/

# Executar testes com cobertura
python -m pytest tests/ --cov=. --cov-report=html
```

### Contribuindo

1. Faça um fork do repositório
2. Crie uma branch para sua funcionalidade (`git checkout -b feature/nova-funcionalidade`)
3. Faça commit das suas alterações (`git commit -am 'Adiciona nova funcionalidade'`)
4. Faça push para a branch (`git push origin feature/nova-funcionalidade`)
5. Crie um novo Pull Request

## Suporte e Documentação

- **Documentação detalhada**: Disponível no diretório `docs/`
- **Exemplos de uso**: Disponíveis no diretório `examples/`
- **Tutoriais**: Disponíveis no wiki do projeto
- **FAQ**: Perguntas frequentes no arquivo `docs/FAQ.md`

## Otimizações e Características Avançadas

- **Execução em lote**: Processamento de múltiplas moléculas em paralelo
- **Checkpoint e retomada**: Capacidade de continuar cálculos interrompidos
- **Exportação de dados**: Formatos CSV, JSON e Excel para análise externa
- **Visualização interativa**: Gráficos dinâmicos com Plotly
- **CLI avançada**: Interface de linha de comando colorida e interativa com Rich e Typer
- **Cálculos em cluster**: Suporte para execução em ambientes de HPC

## Limitações Conhecidas

- CREST requer o WSL configurado com ambiente conda
- MOPAC é executado apenas no Windows
- Algumas moléculas muito grandes podem não ser processadas adequadamente
- Cálculos com solventes específicos podem requerer parâmetros adicionais

## Licença

Este software é distribuído sob a licença MIT.

## Citação

Se utilizar este software em trabalhos acadêmicos, por favor cite:

```
Sobrenome, Nome. (2025). Grimme Thermo: Software para Busca Conformacional 
e Cálculo de Entalpia. [Software]. https://github.com/seu-usuario/grimme_thermo
```

## Agradecimentos

- Grupo do Prof. Stefan Grimme pelo desenvolvimento do CREST
- James J. P. Stewart pelo desenvolvimento do MOPAC
- Equipe do OpenBabel pelo conversor de formatos moleculares
- Contribuidores do projeto Supabase pela plataforma de backend

---

© 2025 | Desenvolvido como parte de trabalho de conclusão de curso
