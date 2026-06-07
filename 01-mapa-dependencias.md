# 01 — Mapa de Dependências Selenium

## Grafo de dependências

```
Fix/core.py  (raiz — 2915 linhas, 100% Selenium)
    │
    ├── Fix/browser_suporte.py  (importa aguardar_e_clicar de core.py)
    │       │
    │       └── Fix/utils.py  (importa funções de browser_suporte)
    │
    ├── Fix/extracao.py  (usa WebDriver diretamente)
    │
    ├── Fix/diagnostico_runtime.py  (usa WebDriver como type hint)
    │
    ├── atos/comunicacao.py  ──────────────────────────┐
    ├── atos/comunicacao_preenchimento.py              │
    ├── atos/comunicacao_destinatarios.py              │
    ├── atos/comunicacao_navigation.py                 │── todos importam
    ├── atos/judicial.py                               │   Fix/core.py
    ├── atos/judicial_fluxo.py                         │
    ├── atos/movimentos_fluxo.py                       │
    └── atos/anexos_sigilo.py ──────────────────────────┘
            │
            ├── PEC/runtime_pec.py
            ├── PEC/regras_execucao.py
            ├── PEC/orquestrador.py
            │
            ├── Prazo/loop_orquestrador.py
            ├── Prazo/loop_lote.py
            ├── Prazo/loop_execucao_final.py
            ├── Prazo/p2b_gateway.py
            │
            ├── Mandado/entrada_api.py
            ├── Mandado/fluxo_argos.py
            └── Mandado/apoio_fluxos.py

Fix/variaveis.py  (PjeApiClient — sem Selenium, só requests)
    │
    └── session_from_driver(driver)  ← única função com acoplamento Selenium
                                         (adicionaremos session_from_page ao lado)
```

---

## Inventário completo de imports Selenium por arquivo

### Camada Fix/ (base — migrar primeiro)

| Arquivo | Imports Selenium ativos | Prioridade |
|---|---|---|
| `Fix/core.py` | `webdriver`, `WebDriver`, `By`, `WebDriverWait`, `EC`, `Keys`, todas as exceptions | **P0 — primeiro** |
| `Fix/browser_suporte.py` | `WebDriver`, `WebElement`, `By`, `WebDriverWait`, `EC`, 4 exceptions | P1 |
| `Fix/utils.py` | `WebDriver`, `By`, `Keys`, `WebDriverWait`, `EC` | P1 |
| `Fix/extracao.py` | `WebDriver`, `WebElement`, `By`, `Keys`, `WebDriverWait`, `EC`, `TimeoutException` | P1 |
| `Fix/selenium_base/click_operations.py` | `WebDriver`, `WebElement`, `By` | P1 |
| `Fix/selenium_base/element_interaction.py` | `WebDriver`, `WebElement`, `By`, `Keys` | P1 |
| `Fix/selenium_base/wait_operations.py` | `WebDriverWait`, `EC`, `By` | P1 |
| `Fix/diagnostico_runtime.py` | `WebDriver` (type hint only) | P2 |
| `Fix/variaveis.py` | **nenhum** (apenas `session_from_driver` usa driver como arg) | P3 (adição) |

### Camada atos/ (migrar após Fix/)

| Arquivo | Imports Selenium ativos | Prioridade |
|---|---|---|
| `atos/judicial.py` | via Fix/core | P2 |
| `atos/movimentos.py` | via Fix/core | P2 |
| `atos/movimentos_chips.py` | via Fix/core | P2 |
| `atos/regras.py` | via Fix/core | P2 |
| `atos/wrappers_mov.py` | via Fix/core | P2 |
| `atos/anexos/anexos_extracao.py` | via Fix/core | P2 |
| `atos/anexos/anexos_formatacao.py` | via Fix/core | P2 |

### Camada de negócio (migrar após atos/)

| Arquivo | Imports Selenium ativos | Prioridade |
|---|---|---|
| `PEC/regras.py` | via Fix | P3 |
| `PEC/prescricao.py` | via Fix | P3 |
| `PEC/api_client.py` | via Fix | P3 |
| `Prazo/loop_orquestrador.py` | `By`, `WebDriver`, `WebElement`, `WebDriverWait`, `EC`, `TimeoutException` | P3 |
| `Prazo/loop_lote.py` | via Fix | P3 |
| `Prazo/loop_execucao_final.py` | via Fix | P3 |
| `Prazo/p2b_gateway.py` | via Fix | P3 |
| `Mandado/core.py` | via Fix | P3 |
| `Mandado/processamento.py` | via Fix | P3 |
| `Mandado/fluxo_argos.py` | via Fix | P3 |
| `Mandado/entrada_api.py` | via Fix | P3 |
| `Mandado/apoio_fluxos.py` | via Fix | P3 |
| `Mandado/regras.py` | via Fix | P3 |
| `SISB/Core/driver.py` | `WebDriver` | P4 (fora do escopo inicial) |
| `SISB/processamento/` | via Fix | P4 (fora do escopo inicial) |

---

## Regra de ordem de migração

```
P0: Fix/core.py  (criar playwright_core.py ao lado)
        ↓
P1: Fix/browser_suporte.py
    Fix/utils.py  (login_cpf e helpers)
    Fix/extracao.py
        ↓
P2: atos/ (todos os arquivos)
        ↓
P3: PEC/  → Prazo/  → Mandado/
        ↓
P4: SISB/ (deixar por último — mais complexo, menos urgente para a PoC)
```

**Nunca pular níveis.** Se um arquivo P3 for editado antes de todos os P1 estarem prontos,
os imports irão falhar em cascata.

---

## Arquivos que NÃO precisam ser tocados

Estes arquivos não têm import Selenium e funcionam sem mudança:

- `Fix/variaveis.py` → apenas adicionaremos `session_from_page()`
- `Fix/log.py` → sem Selenium
- `Fix/tipos.py` → sem Selenium
- `Fix/monitoramento_progresso_unificado.py` → sem Selenium (usa apenas JSON/IO)
- `Fix/variaveis_client.py` → `PjeApiClient` com `requests.Session` puro
- `Fix/variaveis_helpers.py` → helpers de API REST
- `Fix/variaveis_resolvers.py` → resolvers de API
- `Peticao/api/` → usa `requests.Session`, sem Selenium
- `Peticao/core/` → utilitários puros e extração

---

## Contagem de ocorrências por módulo (estimativa)

```
Fix/core.py              ~180 usos diretos de Selenium
Fix/browser_suporte.py    ~60 usos diretos de Selenium
Fix/extracao.py           ~40 usos diretos de Selenium
Fix/utils.py              ~30 usos diretos de Selenium
atos/ (total)             ~50 usos diretos de Selenium
PEC/ (total)              ~30 usos (maioria via Fix/)
Prazo/ (total)            ~40 usos (maioria via Fix/)
Mandado/ (total)          ~20 usos (maioria via Fix/)
```

**Insight crítico:** Se `Fix/playwright_core.py` expuser a mesma API pública de `Fix/core.py`,
aproximadamente 80% dos outros arquivos precisam apenas trocar:
```python
# de:
from Fix.core import aguardar_e_clicar, esperar_elemento, preencher_campo

# para:
from Fix.playwright_core import aguardar_e_clicar, esperar_elemento, preencher_campo
```
e trocar `driver: WebDriver` por `page: Page` nos type hints.
A lógica de negócio em si permanece idêntica.
