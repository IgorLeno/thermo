# Configuração do Dashboard Supabase

Este documento fornece instruções detalhadas para configurar o dashboard web baseado em Supabase para o Grimme Thermo.

## O que é o Supabase?

O Supabase é uma plataforma de backend como serviço (BaaS) de código aberto que oferece:

- Banco de dados PostgreSQL gerenciado
- API RESTful automática
- Autenticação de usuários
- Armazenamento de arquivos
- Funções em tempo real

Para o Grimme Thermo, usamos o Supabase para armazenar os resultados dos cálculos e fornecer um dashboard web para visualização.

## Criando uma conta no Supabase

1. Acesse [https://supabase.com](https://supabase.com) e clique em "Sign Up"
2. Crie uma conta usando e-mail ou GitHub
3. Após fazer login, clique em "New Project"
4. Escolha uma organização ou crie uma nova
5. Dê um nome ao seu projeto (ex: "grimme-thermo")
6. Defina uma senha para o banco de dados (anote-a em um local seguro)
7. Escolha a região mais próxima de você para o servidor
8. Clique em "Create new project"

## Configurando o banco de dados

Após a criação do projeto, você precisará configurar as tabelas necessárias para armazenar os dados:

1. No painel lateral, clique em "SQL Editor"
2. Clique em "New Query"
3. Copie o conteúdo do arquivo `setup_supabase.sql` para o editor
4. Clique em "Run" para executar o script SQL

Este script criará as seguintes tabelas:
- `molecules`: Armazena informações sobre as moléculas
- `calculations`: Registra os cálculos realizados
- `crest_results`: Armazena resultados específicos do CREST
- `mopac_results`: Armazena resultados específicos do MOPAC

## Configurando o Storage

O Storage é usado para armazenar arquivos, como arquivos XYZ de estruturas moleculares e arquivos de saída de cálculos:

1. No painel lateral, clique em "Storage"
2. Clique em "Create new bucket"
3. Digite "molecule-files" como nome do bucket
4. Marque a opção "Public bucket" (para facilitar o acesso aos arquivos)
5. Clique em "Create bucket"

## Obtendo as credenciais da API

Para conectar o Grimme Thermo ao Supabase, você precisará das credenciais da API:

1. No painel lateral, clique em "Settings" e depois em "API"
2. Copie a URL na seção "Project URL" (ex: https://abcdefghijk.supabase.co)
3. Copie a chave na seção "anon public" em "Project API keys"

Estas credenciais serão usadas no arquivo `config.yaml` do Grimme Thermo.

## Configurando o Grimme Thermo

Abra o arquivo `config.yaml` do Grimme Thermo e adicione as seguintes configurações:

```yaml
supabase:
  enabled: true
  url: https://seu-projeto.supabase.co  # Substitua pela URL do seu projeto
  key: sua-chave-api  # Substitua pela chave anon public
  storage:
    enabled: true
    molecules_bucket: molecule-files
```

Alternativamente, você pode usar a interface do programa para configurar essas opções:

1. Execute o programa: `python main.py`
2. Escolha a opção "6. Configurar dashboard (Supabase)"
3. Siga as instruções para inserir as credenciais

## Testando a conexão

Após configurar as credenciais:

1. Execute o programa: `python main.py`
2. Escolha a opção "6. Configurar dashboard (Supabase)"
3. Escolha a opção "2. Testar conexão com o Supabase"

Se a conexão for bem-sucedida, você verá uma mensagem confirmando.

## Usando o dashboard

Após configurar o Supabase e realizar cálculos, você pode acessar o dashboard web:

1. Execute o programa: `python main.py`
2. Escolha a opção "6. Configurar dashboard (Supabase)"
3. Escolha a opção "4. Abrir o dashboard no navegador"
4. Selecione qual interface deseja acessar:
   - **Dashboard principal**: Visão geral do projeto
   - **Table Editor**: Para visualizar os dados das moléculas
   - **Storage**: Para visualizar arquivos de moléculas

**IMPORTANTE**: Todas as interfaces do Supabase requerem que você faça login na sua conta. Mantenha suas credenciais de login em mãos.

## Solução de problemas

### Erro "Bucket not found"

Se você encontrar o erro "Bucket not found", o bucket "molecule-files" não existe no Supabase.

Solução:
1. Acesse o painel do Supabase
2. Vá para a seção "Storage"
3. Crie um bucket chamado "molecule-files"

### Erro de credenciais inválidas

Se você encontrar erros relacionados a credenciais:

1. Verifique se a URL do projeto está correta
2. Verifique se a chave API está correta
3. Confirme se está usando a chave "anon public" (não a chave de serviço)

### Erro de permissão ao fazer upload de arquivos

Se não conseguir fazer upload de arquivos:

1. Verifique se o bucket está definido como público
2. Confirme se as políticas de segurança foram configuradas corretamente
3. Verifique se sua chave API tem permissões de gravação

### Tabelas inexistentes

Se receber erros sobre tabelas não existentes:

1. Execute novamente o script SQL `setup_supabase.sql`
2. Verifique no "Table Editor" se as tabelas foram criadas

## Recursos adicionais

- [Documentação oficial do Supabase](https://supabase.com/docs)
- [API do Supabase para Python](https://supabase.com/docs/reference/python/introduction)
- [Documentação do PostgreSQL](https://www.postgresql.org/docs/)
