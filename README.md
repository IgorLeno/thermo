# Grimme Thermo - Busca Conformacional com CREST e Cálculo de Entalpia com MOPAC

## Visão Geral

O **Grimme Thermo** é um software científico para automatizar o fluxo de trabalho de busca conformacional de moléculas orgânicas usando o programa CREST (Conformer-Rotamer Ensemble Sampling Tool) desenvolvido pelo grupo do Prof. Stefan Grimme, seguido por cálculos de entalpia de formação usando MOPAC (Molecular Orbital Package). 

O programa permite:

- Baixar estruturas moleculares diretamente do PubChem por nome de molécula
- Converter formatos de arquivo usando OpenBabel
- Executar busca conformacional usando CREST via Windows Subsystem for Linux (WSL)
- Calcular entalpia de formação usando MOPAC
- Analisar e visualizar os resultados dos cálculos
- Armazenar e visualizar resultados em um dashboard baseado em Supabase (opcional)

## Principais Funcionalidades

- **Acesso ao PubChem**: Obtenção automática de estruturas moleculares a partir do nome da molécula
- **Integração com OpenBabel**: Conversão eficiente entre formatos de arquivos moleculares (SDF, XYZ, PDB)
- **Integração com CREST**: Busca conformacional completa utilizando métodos GFN-xTB
- **Integração com MOPAC**: Cálculos de entalpia de formação utilizando métodos semi-empíricos
- **Interface de Linha de Comando**: Menu interativo para facilitar o uso
- **Análise de Resultados**: Ferramentas para análise estatística dos conformeros encontrados
- **Dashboard Web (opcional)**: Visualização de resultados e estatísticas via Supabase
- **Logs detalhados**: Rastreamento de todas as etapas do processo com mensagens informativas

## Requisitos

- Python 3.8 ou superior
- Windows 10/11 com WSL (Windows Subsystem for Linux) e Ubuntu instalado
- CREST instalado no ambiente conda no WSL
- OpenBabel 3.1.1 ou superior instalado no Windows
- MOPAC2016 ou superior instalado no Windows
- Bibliotecas Python listadas em `requirements.txt`:
  - requests
  - pathlib
  - logging
  - dataclasses
  - pyyaml
  - pytest
  - numpy

## Instalação

1. Clone o repositório:
```
git clone https://github.com/seu-usuario/grimme_thermo.git
cd grimme_thermo
```

2. Instale as dependências Python:
```
pip install -r requirements.txt
```

3. Configure o ambiente WSL (necessário para o CREST):
```
wsl --install
```

4. Instale o conda no ambiente WSL:
```bash
# No terminal WSL Ubuntu
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

5. Crie um ambiente conda para o CREST e instale-o:
```bash
# No terminal WSL Ubuntu
conda create -n crest_env
conda activate crest_env
conda install -c conda-forge xtb crest
```

6. Instale o OpenBabel no Windows (versão 3.1.1 ou superior)

7. Instale o MOPAC2016 no Windows

8. Configure o arquivo `config.yaml` com os caminhos corretos para os programas:
```yaml
calculation_parameters:
  n_threads: 4
  crest_method: gfn2
  electronic_temperature: 300.0
  solvent:
programs:
  openbabel_path: C:\Program Files\OpenBabel-3.1.1\obabel.exe
  crest_path: \\wsl.localhost\Ubuntu\home\seu_usuario\miniconda3\envs\crest_env\bin\crest
  mopac_path: C:\Caminho\Para\MOPAC\MOPAC2016.exe
mopac_params:
  keywords: "PM7 EF PRECISE GNORM=0.01 NOINTER GRAPHF VECTORS MMOK CYCLES=20000"
```

9. (Opcional) Configure o Supabase para armazenamento e visualização de resultados:
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

O programa oferece um menu interativo com as seguintes opções:

1. **Realizar cálculo completo para uma molécula** - Processa uma única molécula
2. **Realizar cálculo completo para várias moléculas** - Processa múltiplas moléculas
3. **Editar configurações** - Modifica parâmetros de cálculo e caminhos
4. **Exibir resultados** - Mostra resumos dos cálculos realizados
5. **Analisar resultados** - Fornece análise detalhada dos confôrmeros
6. **Configurar dashboard (Supabase)** - Gerencia a integração com Supabase
7. **Sair** - Encerra o programa

### Fluxo de Trabalho

Para cada molécula, o programa segue o seguinte fluxo:

1. **Download da estrutura do PubChem** - Obtém a estrutura molecular em formato SDF
2. **Conversão para XYZ** - Utiliza OpenBabel para converter SDF para XYZ
3. **Busca conformacional com CREST** - Executa CREST via WSL para encontrar confôrmeros
4. **Conversão do melhor confôrmero para PDB** - Prepara o arquivo para o MOPAC
5. **Cálculo de entalpia com MOPAC** - Executa MOPAC para calcular a entalpia de formação
6. **Análise e armazenamento de resultados** - Processa e salva os resultados obtidos
7. **Upload para Supabase (opcional)** - Envia os resultados para o dashboard web

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
├── programs/             # Programas externos (MOPAC, etc.)
├── .vscode/              # Configurações VS Code
├── .idea/                # Configurações PyCharm
├── main.py               # Ponto de entrada principal do programa
├── run.py                # Script simplificado para execução
├── setup_environment.py  # Script para configuração do ambiente
├── setup_programs.py     # Script para instalação de programas
├── config.yaml           # Arquivo de configuração principal
├── requirements.txt      # Dependências Python
└── README.md             # Documentação do projeto
```

## Arquivos de Saída

Os resultados são organizados em diferentes diretórios:

- **repository/crest/{nome_molécula}/** - Arquivos da busca conformacional com CREST:
  - `crest_best.xyz` - Confôrmero de menor energia
  - `crest_conformers.xyz` - Todos os confôrmeros encontrados
  - `crest.energies` - Energias de cada confôrmero
  - `crest.out` - Log de saída do CREST
  - `.crest_ensemble` - Informações do ensemble de confôrmeros

- **repository/pdb/** - Arquivos PDB convertidos do melhor confôrmero
  - `{nome_molécula}.pdb` - Arquivo PDB do melhor confôrmero

- **repository/mopac/{nome_molécula}/** - Arquivos do cálculo de entalpia:
  - `{nome_molécula}.dat` - Arquivo de entrada do MOPAC
  - `{nome_molécula}.out` - Arquivo de saída do MOPAC com resultados
  - `{nome_molécula}.arc` - Arquivo com geometria otimizada

- **final_molecules/output/{nome_molécula}/** - Resumos e arquivos finais:
  - `results_summary.txt` - Resumo dos cálculos realizados

## Análise de Resultados

O programa inclui funcionalidades avançadas para análise de resultados:

- **Análise detalhada de confôrmeros** - Estatísticas sobre energias e populações
- **Listagem de moléculas processadas** - Resumo geral com status dos cálculos
- **Geração de relatórios** - Exportação de resultados detalhados
- **Comparação de múltiplas moléculas** - Análise comparativa de diferentes estruturas

As análises incluem informações como:
- Número total de confôrmeros encontrados
- Distribuição de energias relativas
- Populações baseadas na distribuição de Boltzmann
- Estatísticas atômicas dos confôrmeros
- Valores de entalpia de formação calculados com MOPAC

## Integração com Supabase (opcional)

O programa oferece integração com Supabase para armazenamento e visualização de dados:

- **Armazenamento de metadados** - Informações sobre moléculas e cálculos
- **Upload de arquivos** - Armazenamento de arquivos XYZ, PDB e resultados
- **Dashboard web** - Visualização interativa de resultados e estatísticas
- **Sincronização de resultados** - Envio de cálculos concluídos para o banco de dados

Para habilitar esta funcionalidade, é necessário:
1. Criar uma conta no Supabase (https://supabase.com)
2. Configurar um projeto com as tabelas necessárias
3. Adicionar as credenciais no arquivo `config.yaml`
4. Habilitar a integração no menu do programa

## Depuração e Logs

O programa mantém logs detalhados de todas as operações:

- Logs são armazenados no diretório `logs/`
- Cada execução gera um arquivo de log com timestamp
- Mensagens de erro são registradas com detalhes para facilitar a depuração
- Níveis de log incluem INFO, WARNING, ERROR e DEBUG

## Desenvolvimento e Testes

O projeto inclui suporte para testes com pytest:

```
python -m pytest tests/
```

## Limitações Conhecidas

- CREST requer o WSL configurado com ambiente conda
- MOPAC é executado apenas no Windows
- Algumas moléculas muito grandes podem não ser processadas adequadamente
- A integração com Supabase requer conexão internet estável

## Suporte e Contribuições

Para reportar problemas, sugestões ou contribuições, utilize as issues do GitHub.

## Licença

Este software é distribuído sob a licença MIT.

## Citação

Se utilizar este software em trabalhos acadêmicos, por favor cite:

```
[Inserir referência bibliográfica]
```

## Agradecimentos

- Grupo do Prof. Stefan Grimme pelo desenvolvimento do CREST
- James J. P. Stewart pelo desenvolvimento do MOPAC
- Equipe do OpenBabel pelo conversor de formatos moleculares