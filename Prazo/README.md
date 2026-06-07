# Módulo Prazo - Sistema de Processamento de Prazos PJe

## 📋 Visão Geral

O **Módulo Prazo** é um sistema modularizado para processamento automatizado de prazos no sistema PJe (Poder Judiciário Eletrônico). Resultado de uma refatoração completa seguindo o guia unificado de otimização IA.

## 🏗️ Arquitetura

### Estrutura do Módulo
```
Prazo/
├── __init__.py              # Interface principal do módulo
├── loop_orquestrador.py     # Loop principal de processamento
├── loop_lote.py             # Processamento em lote
├── loop_execucao_final.py   # Execução final do loop
├── p2b_gateway.py           # Gateway P2B (API REST)
├── p2b_core.py              # Utilitários e constantes
├── p2b_documentos.py        # Processamento de documentos
├── p2b_regras_execucao.py   # Regras de execução P2B
├── p2b_fluxo_prescricao.py  # Fluxo de prescrição (legado)
└── p2b_fluxo_lazy.py        # Fluxo lazy (legado)
```

### Padrão de Design
- **Loop + Gateway**: Separação entre loop de browser e chamadas API
- **Modularização**: Cada arquivo com responsabilidade específica
- **Selenium**: Usa `Fix/core.py` e `Fix/browser_suporte.py` para automação
- **Playwright (planejado)**: Migrar para `Fix/playwright_core.py` na Fase 6

## 📊 Métricas

| Aspecto | Estado |
|---------|--------|
| **Loop principal** | `loop_orquestrador.py` — orquestração completa |
| **Gateway P2B** | `p2b_gateway.py` — chamadas API REST |
| **Dependência Selenium** | Alta — usa `WebDriver`, `By`, `WebDriverWait`, `EC` diretamente |
| **Status migração Playwright** | ⏳ Pendente — Fase 6 do plano |

## 🚀 Como Usar

### Execução via loop principal
```python
from Prazo.loop_orquestrador import loop_prazo

# Com driver Selenium já autenticado
loop_prazo(driver)
```

### Gateway P2B
```python
from Prazo.p2b_gateway import processar_gigs_sem_prazo_p2b

processar_gigs_sem_prazo_p2b()
```

### Utilitários Disponíveis
```python
from Prazo.p2b_core import (
    normalizar_texto, gerar_regex_geral, parse_gigs_param,
    carregar_progresso_p2b, marcar_processo_executado_p2b
)
```

## 🔧 Dependências

- **Fix/core.py**: Automação Selenium (aguardar_e_clicar, esperar_elemento, etc.)
- **Fix/browser_suporte.py**: Validação de driver, abas, scroll
- **Fix/variaveis.py**: `PjeApiClient`, `session_from_driver`
- **atos/**: Ações processuais (judicial, movimentos)

## 🔄 Plano de Migração para Playwright

Ver [08-fase6-prazo-mandado.md](../08-fase6-prazo-mandado.md) para o plano completo.

Resumo:
1. Trocar `from Fix.core import` → `from Fix.playwright_core import`
2. `driver: WebDriver` → `page: Page` nos type hints
3. `WebDriverWait` / `EC` / `By` → `page.locator()` com auto-wait
4. `session_from_driver` → `session_from_page`

## 📝 Funcionalidades Principais

### loop_orquestrador.py
- Loop principal de processamento de prazos
- Painel 14 (Análise) e Painel 8 (Cumprimento de providências)
- Usa Selenium diretamente (`By`, `WebDriver`, `WebDriverWait`, `EC`)

### p2b_gateway.py
- Gateway P2B para processamento de GIGS sem prazo
- Chamadas API REST via `PjeApiClient`
- Menos acoplado ao Selenium que o loop

---

**Versão**: 2.1.0
**Data**: Maio 2026
**Status**: Funcional em Selenium | Migração Playwright pendente (Fase 6)