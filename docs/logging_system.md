# Sistema de Logging Otimizado - Grimme Thermo

## Visão Geral

O sistema de logging foi otimizado para reduzir drasticamente a verbosidade no console, mantendo logs detalhados nos arquivos para debugging. Este sistema resolve o problema de logs excessivos das bibliotecas HTTP (httpx, httpcore, hpack) durante operações com o Supabase.

## Características Principais

### 1. Logging Bifurcado
- **Console**: Apenas logs essenciais (nível INFO e acima)
- **Arquivo**: Todos os logs detalhados (nível DEBUG e acima)

### 2. Filtro Inteligente
- Bloqueia automaticamente logs verbosos de bibliotecas externas no console
- Mantém todos os logs no arquivo para análise posterior
- Filtra padrões específicos como "Decoded", "Encoding", "HTTP Request:", etc.

### 3. Configuração Automática
- Silencia automaticamente loggers conhecidos por serem verbosos
- Configura níveis apropriados para diferentes bibliotecas
- Aplica filtros dinâmicos para loggers criados em runtime

## Como Usar

### Configuração Básica (Já Implementada)
```python
from utils.logging_config import setup_application_logging

# No início do main.py (já configurado)
setup_application_logging()

# Usar logging normalmente
import logging
logging.info("Este log aparece no console e arquivo")
logging.debug("Este log aparece apenas no arquivo")
```

### Configuração Avançada
```python
from utils.logging_config import get_logging_manager

# Obter o gerenciador de logging
manager = get_logging_manager()

# Adicionar padrões personalizados para filtrar
manager.add_blocked_pattern("meu_padrao_especifico")

# Bloquear logger específico no console
manager.add_blocked_logger("minha_biblioteca.verbose")

# Ajustar nível de log para módulo específico
manager.set_module_log_level("services.supabase_service", logging.WARNING)
```

## Logs que São Filtrados no Console

### Bibliotecas HTTP
- `httpx` (DEBUG/INFO)
- `httpcore` (DEBUG/INFO)
- `hpack` (todos os logs)
- `h2` (DEBUG/INFO)
- `h11` (DEBUG/INFO)

### Padrões de Mensagem
- `Decoded XX, consumed Y bytes`
- `Adding (header) to the header table`
- `HTTP Request: POST/GET ...`
- `*trace - send*request_headers.started`
- `receive_response_headers.complete`
- E muitos outros padrões específicos

## Logs que PERMANECEM no Console

### Logs da Aplicação
- Todos os logs dos módulos do Grimme Thermo (INFO+)
- Logs de erro e warning de qualquer biblioteca

### Logs Importantes
- Erros críticos de qualquer fonte
- Warnings de bibliotecas externas
- Logs de progresso do usuário

## Estrutura dos Arquivos de Log

### Formato do Console
```
INFO - module_name - mensagem
WARNING - module_name - mensagem
ERROR - module_name - mensagem
```

### Formato do Arquivo
```
2025-05-18 10:15:55,984 - INFO - module_name - function_name:line_number - mensagem detalhada
```

## Configurações por Módulo

### Níveis de Log Configurados
- **Aplicação (grimme_thermo.*)**: DEBUG
- **httpx/httpcore**: WARNING (apenas warnings e erros no console)
- **hpack**: ERROR (apenas erros críticos)
- **supabase**: WARNING
- **requests/urllib3**: WARNING

## Benefícios

1. **Console Limpo**: Apenas informações relevantes para o usuário
2. **Debugging Completo**: Todos os logs detalhados mantidos em arquivo
3. **Performance**: Redução significativa na saída do console
4. **Flexibilidade**: Fácil ajuste de filtros e níveis
5. **Manutenibilidade**: Sistema centralizado e configurável

## Arquivo de Log

Os logs detalhados são salvos em:
```
logs/conformer_search_YYYYMMDD_HHMMSS.log
```

Cada execução gera um novo arquivo com timestamp único.

## Troubleshooting

### Se logs importantes não aparecem no console:
1. Verifique se o nível do logger está adequado
2. Confirme se o padrão da mensagem não está sendo filtrado
3. Use `manager.set_module_log_level()` para ajustar

### Se logs ainda aparecem no console:
1. Adicione novos padrões com `manager.add_blocked_pattern()`
2. Ajuste o nível do logger específico
3. Verifique se o filtro está sendo aplicado corretamente

## Exemplo de Uso Durante Sincronização

**Antes (verboso):**
```
2025-05-18 10:06:48,176 - DEBUG - hpack - Decoded 84, consumed 1 bytes
2025-05-18 10:06:48,177 - DEBUG - hpack - Decoded (b'sb-project-ref', b'iyvvuguktlktwjwhoppf'), consumed 1
...centenas de linhas similares...
```

**Depois (limpo):**
```
INFO - supabase_service - Cálculo crest inserido com ID: ae786c15-ea11-45b5-ab32-948a4dd10130
✓ ethanol sincronizado com sucesso!
Sincronizando propanol...
```

## Implementação Técnica

O sistema usa:
- `ConsoleFilter`: Filtro personalizado para o handler do console
- `LoggingManager`: Gerenciador centralizado de configuração
- Configuração automática de loggers externos
- Handlers separados para console e arquivo

## Compatibilidade

- Python 3.8+
- Todas as bibliotecas do requirements.txt
- Funciona com ou sem Supabase habilitado

---

*Sistema implementado para resolver o problema de logs excessivos durante operações de sincronização com Supabase.*
