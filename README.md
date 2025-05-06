# Grimme Thermo - Busca Conformacional com CREST

## Visão Geral

O projeto **grimme_thermo** é um software científico para busca conformacional de moléculas orgânicas usando o programa CREST (Conformer-Rotamer Ensemble Sampling Tool) desenvolvido pelo grupo do Prof. Stefan Grimme. O programa permite:

- Baixar estruturas moleculares diretamente do PubChem
- Converter formatos de arquivo usando OpenBabel
- Executar busca conformacional usando CREST via WSL/Ubuntu
- Analisar e visualizar os resultados da busca conformacional

## Requisitos

- Python 3.8 ou superior
- Windows com WSL (Windows Subsystem for Linux) e Ubuntu instalado
- CREST instalado no ambiente conda no WSL
- OpenBabel 3.1.1 ou superior instalado no Windows
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
openbabel_path: C:\Program Files\OpenBabel-3.1.1\obabel.exe
crest_path: \\wsl.localhost\Ubuntu\home\seu_usuario\miniconda3\envs\crest_env\bin\crest
```

## Uso

Execute o programa principal:
```
python main.py
```

O programa oferece uma interface de linha de comando com as seguintes opções:

1. **Busca conformacional para uma única molécula** - Processa apenas uma molécula especificada pelo nome
2. **Busca conformacional para múltiplas moléculas** - Processa várias moléculas a partir de uma lista
3. **Editar configurações** - Permite modificar parâmetros de cálculo e caminhos dos programas
4. **Exibir resultados** - Mostra resumos dos cálculos realizados
5. **Analisar resultados** - Fornece análise detalhada dos confôrmeros encontrados
6. **Sair** - Encerra o programa

## Análise de Resultados

O programa inclui uma funcionalidade de análise de resultados que permite:

- **Análise detalhada de moléculas individuais** - Estatísticas de energia, população de confôrmeros, etc.
- **Listagem de todas as moléculas processadas** - Resumo geral dos cálculos
- **Geração de relatórios completos** - Relatórios detalhados em formato de texto
- **Comparação de múltiplas moléculas** - Análise comparativa de diferentes estruturas

A análise fornece informações como:
- Número total de confôrmeros encontrados
- Distribuição de energias relativas
- Análise populacional baseada na distribuição de Boltzmann
- Estatísticas atômicas dos confôrmeros
- Visualização de distribuições de energia

## Arquivos de Saída

Os resultados são organizados no diretório `final_molecules/output/{nome_da_molécula}/` e incluem:

- `crest_best.xyz` - O confôrmero de menor energia
- `crest_conformers.xyz` - Todos os confôrmeros encontrados
- `crest.energies` - Energias de cada confôrmero
- `crest.out` - Log de saída do programa CREST
- `.crest_ensemble` - Informações do ensemble de confôrmeros

## Licença

Este software é distribuído sob a licença [inserir licença].

## Contato

Para dúvidas ou sugestões, entre em contato com [inserir contato].
