# Grimme Thermo - Busca Conformacional com CREST e Cálculo de Entalpia com MOPAC

## Visão Geral

O projeto **grimme_thermo** é um software científico para busca conformacional de moléculas orgânicas usando o programa CREST (Conformer-Rotamer Ensemble Sampling Tool) desenvolvido pelo grupo do Prof. Stefan Grimme, com posterior cálculo de entalpias de formação usando MOPAC. O programa permite:

- Baixar estruturas moleculares diretamente do PubChem
- Converter formatos de arquivo usando OpenBabel
- Executar busca conformacional usando CREST via WSL/Ubuntu
- Realizar cálculos de entalpia de formação usando MOPAC
- Analisar e visualizar os resultados da busca conformacional e cálculos termodinâmicos

## Requisitos

- Python 3.8 ou superior
- Windows com WSL (Windows Subsystem for Linux) e Ubuntu instalado
- CREST instalado no ambiente conda no WSL
- OpenBabel 3.1.1 ou superior instalado no Windows
- MOPAC2016 instalado no Windows
- As bibliotecas Python listadas em `requirements.txt`

## Instalação

1. Clone o repositório:
```
git clone https://github.com/seu-usuario/grimme_thermo.git
cd grimme_thermo
```

2. Instale as dependências:
```
pip install -r requirements.txt
```

3. Configure o ambiente:
```
python setup_environment.py
```

4. Edite o arquivo `config.yaml` com os caminhos corretos para os programas:
```yaml
calculation_parameters:
  n_threads: 4
  crest_method: gfn2
  electronic_temperature: 300.0
  solvent:
programs:
  openbabel_path: C:\Program Files\OpenBabel-3.1.1\obabel.exe
  crest_path: \\wsl.localhost\Ubuntu\home\seu_usuario\miniconda3\envs\crest_env\bin\crest
  mopac_path: C:\Repositorio\TCC\grimme_thermo\programs\MOPAC\MOPAC2016.exe
mopac_params:
  keywords: "PM7 EF PRECISE GNORM=0.01 NOINTER GRAPHF VECTORS MMOK CYCLES=20000"
```

## Uso

Execute o programa principal:
```
python main.py
```

O programa oferece uma interface de linha de comando com as seguintes opções:

1. **Busca conformacional e cálculo de entalpia para uma única molécula** - Processa apenas uma molécula especificada pelo nome
2. **Busca conformacional e cálculo de entalpia para múltiplas moléculas** - Processa várias moléculas a partir de uma lista
3. **Editar configurações** - Permite modificar parâmetros de cálculo e caminhos dos programas
4. **Exibir resultados** - Mostra resumos dos cálculos realizados
5. **Analisar resultados** - Fornece análise detalhada dos confôrmeros encontrados
6. **Sair** - Encerra o programa

## Fluxo de Trabalho

O programa segue o seguinte fluxo de trabalho para cada molécula:

1. **Baixar estrutura do PubChem** - Obtém a estrutura molecular em formato SDF
2. **Converter para XYZ** - Utiliza OpenBabel para converter o formato SDF para XYZ
3. **Executar busca conformacional** - Utiliza CREST para encontrar confôrmeros de baixa energia
4. **Converter para PDB** - Converte o confôrmero de menor energia para formato PDB
5. **Preparar e executar cálculo MOPAC** - Calcula a entalpia de formação usando MOPAC
6. **Analisar resultados** - Fornece estatísticas e visualizações dos resultados

## Análise de Resultados

O programa inclui uma funcionalidade de análise de resultados que permite:

- **Análise detalhada de moléculas individuais** - Estatísticas de energia, população de confôrmeros, entalpia de formação, etc.
- **Listagem de todas as moléculas processadas** - Resumo geral dos cálculos
- **Geração de relatórios completos** - Relatórios detalhados em formato de texto
- **Comparação de múltiplas moléculas** - Análise comparativa de diferentes estruturas

A análise fornece informações como:
- Número total de confôrmeros encontrados
- Distribuição de energias relativas
- Análise populacional baseada na distribuição de Boltzmann
- Estatísticas atômicas dos confôrmeros
- Visualização de distribuições de energia
- Valores de entalpia de formação calculados com MOPAC

## Arquivos de Saída

Os resultados são organizados nos seguintes diretórios:

- **repository/crest/{nome_da_molécula}/** - Arquivos da busca conformacional com CREST:
  - `crest_best.xyz` - O confôrmero de menor energia
  - `crest_conformers.xyz` - Todos os confôrmeros encontrados
  - `crest.energies` - Energias de cada confôrmero
  - `crest.out` - Log de saída do programa CREST
  - `.crest_ensemble` - Informações do ensemble de confôrmeros

- **repository/pdb/** - Arquivos PDB convertidos do melhor confôrmero
  - `{nome_da_molécula}.pdb` - Arquivo PDB do melhor confôrmero

- **repository/mopac/{nome_da_molécula}/** - Arquivos do cálculo de entalpia:
  - `{nome_da_molécula}.dat` - Arquivo de entrada do MOPAC
  - `{nome_da_molécula}.out` - Arquivo de saída do MOPAC com resultados
  - `{nome_da_molécula}.arc` - Arquivo com geometria otimizada

- **final_molecules/output/{nome_da_molécula}/** - Resumos e arquivos finais:
  - `results_summary.txt` - Resumo dos cálculos realizados

## Características Adicionais

- **Tratamento robusto de erros** - Captura e tratamento adequado de erros durante todo o fluxo de trabalho
- **Sistema de logs detalhados** - Rastreamento de todas as etapas do processo
- **Configuração flexível** - Parâmetros ajustáveis via arquivo de configuração YAML
- **Compatibilidade com WSL** - Integração direta com o CREST no ambiente Linux
- **Análise estatística de resultados** - Ferramentas para análise detalhada dos confôrmeros e suas energias
- **Geração de relatórios** - Exportação de resultados em formatos de fácil leitura

## Licença

Este software é distribuído sob a licença [inserir licença].

## Contato

Para dúvidas ou sugestões, entre em contato com [inserir contato].
