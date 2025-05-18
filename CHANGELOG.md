# CHANGELOG - Grimme Thermo

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
