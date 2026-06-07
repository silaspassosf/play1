# 08 — Fase 6: `Prazo/` + `Mandado/`

**Objetivo:** Migrar os dois módulos de negócio restantes após o PoC PEC ser validado.
Se a Fase 5 funcionou, esta fase é majoritariamente trabalho mecânico de substituição de imports.

**Dependência:** Fase 5 concluída e validada.

---

## Prazo/

### Inventário

| Arquivo | Selenium direto | Complexidade |
|---|---|---|
| `Prazo/loop_orquestrador.py` | `By`, `WebDriver`, `WebElement`, `WebDriverWait`, `EC`, `TimeoutException` | **Alta** |
| `Prazo/loop_lote.py` | Via Fix | Média |
| `Prazo/loop_execucao_final.py` | Via Fix | Média |
| `Prazo/p2b_gateway.py` | Via Fix | Baixa |
| `Prazo/p2b_core.py` | Via Fix | Baixa |
| `Prazo/p2b_regras_execucao.py` | Via Fix | Baixa |
| `Prazo/p2b_documentos.py` | Via Fix | Baixa |

### Atenção especial: `loop_orquestrador.py`

Este arquivo usa Selenium **diretamente** (não só via Fix). Tem imports explícitos de:
```python
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
```

Além de usar `GIGS_API_MAX_WORKERS = 20` com `ThreadPoolExecutor` para chamadas paralelas de API.
A lógica paralela **não muda** — ela é sobre `requests.Session`, não sobre o browser.

---

## Task 6.1 — `Prazo/loop_orquestrador.py` (arquivo crítico)

**Description:** Migrar o arquivo de maior complexidade em `Prazo/`.
Contém a lógica central do loop de processamento de prazos.

**Mudanças específicas além do padrão:**

```python
# Substituições diretas (além dos imports):

# 1. TimeoutException
# ANTES:
except TimeoutException:
# DEPOIS:
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
except PlaywrightTimeoutError:

# 2. WebElement como tipo de retorno
# ANTES:
def _alguma_funcao(driver) -> WebElement:
# DEPOIS:
def _alguma_funcao(page) -> Locator:

# 3. WebDriverWait inline (se existir além das funções Fix)
# ANTES:
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
# DEPOIS:
page.locator(sel).wait_for(state='attached', timeout=10000)
```

**Acceptance criteria:**
- [ ] `from Prazo.loop_orquestrador import loop_prazo` sem erro
- [ ] Nenhum `import selenium` em `loop_orquestrador.py`
- [ ] `ThreadPoolExecutor` para API calls mantido intacto
- [ ] `GIGS_API_MAX_WORKERS` mantido

**Files:** `Prazo/loop_orquestrador.py`

**Scope:** M

---

## Task 6.2 — Demais arquivos Prazo/

**Description:** Migração mecânica dos arquivos Prazo restantes.
Seguem o padrão padrão de substituição de imports.

**Acceptance criteria:**
- [ ] `from Prazo.p2b_gateway import processar_gigs_sem_prazo_p2b` sem erro
- [ ] Nenhum `import selenium` em `Prazo/*.py`

**Files:**
- `Prazo/loop_lote.py`
- `Prazo/loop_execucao_final.py`
- `Prazo/p2b_gateway.py`
- `Prazo/p2b_regras_execucao.py`
- `Prazo/p2b_documentos.py`
- `Prazo/prov.py`

**Scope:** M

---

## Mandado/

### Inventário

| Arquivo | Selenium direto | Complexidade |
|---|---|---|
| `Mandado/core.py` | Via Fix | Média |
| `Mandado/processamento.py` | Via Fix | Média |
| `Mandado/fluxo_argos.py` | Via Fix | Média |
| `Mandado/entrada_api.py` | Via Fix | Baixa |
| `Mandado/apoio_fluxos.py` | Via Fix | Média |
| `Mandado/regras.py` | Via Fix | Baixa |
| `Mandado/anexos_argos.py` | Via Fix | Baixa |

---

## Task 6.3 — `Mandado/` completo

**Description:** Migrar todos os arquivos do módulo Mandado.
O módulo Mandado é menos denso em Selenium direto que o Prazo — migração mais simples.

**Mudanças padrão:**
1. `from selenium... import WebDriver` → `from playwright.sync_api import Page`
2. `from Fix.core import ...` → `from Fix.playwright_core import ...`
3. `driver: WebDriver` → `page: Page`

**Acceptance criteria:**
- [ ] `from Mandado.core import main` sem erro
- [ ] `from Mandado.regras import aplicar_regras_argos` sem erro
- [ ] Nenhum `import selenium` em `Mandado/*.py`

**Files:**
- `Mandado/core.py`
- `Mandado/processamento.py`
- `Mandado/fluxo_argos.py`
- `Mandado/entrada_api.py`
- `Mandado/apoio_fluxos.py`
- `Mandado/regras.py`
- `Mandado/anexos_argos.py`

**Scope:** M

---

## Task 6.4 — Orquestrador Playwright (a definir)

**Description:** Definir o orquestrador que usará as versões Playwright de todos os módulos.
O orquestrador Selenium atual permanece intocado.

**Mudanças em relação ao orquestrador Selenium:**
```python
# ANTES (Selenium)
from Fix.core import finalizar_driver, criar_driver_pc
from Fix.utils import login_cpf

# DEPOIS (Playwright)
from Fix.playwright_core import finalizar_driver, criar_driver_PC
from Fix.utils import login_cpf  # já migrado na Fase 2
```

**Acceptance criteria:**
- [ ] Orquestrador Playwright funcional
- [ ] Orquestrador Selenium original continua funcionando

**Scope:** S

---

## Checkpoint Fase 6 — Migração completa

```bash
# Zero Selenium nos módulos migrados
grep -r 'from selenium' Prazo/ Mandado/ PEC/ atos/ Fix/playwright_core.py Fix/browser_suporte.py Fix/utils.py
# deve retornar vazio

# Smoke test full
py -c "
from Fix.playwright_core import criar_driver_PC, finalizar_driver
from Fix.utils import login_cpf
from PEC.regras import determinar_acoes_por_observacao
from Prazo.loop_orquestrador import loop_prazo
from Mandado.core import main
print('Migração completa: todos os módulos de negócio sem Selenium')
"
```

- [ ] grep retorna vazio em todos os módulos migrados
- [ ] Todos os imports OK
- [ ] Teste end-to-end dos 3 fluxos (PEC, Prazo, Mandado) passa

---

## O que fica para depois (fora do escopo inicial)

- `SISB/` — SISBAJUD tem complexidade própria (ThreadPoolExecutor, print dialogs); migrar em fase separada
- `Peticao/` — módulo de petições com muitas dependências de atos; migrar após estabilização
- `Triagem/` — triagem de petição inicial (B1–B15); verificar acoplamento Selenium
- `bianca/` — standalone Selenium; migrar separadamente para manter independência
- `Fix/selenium_base/` — operações base extraídas; substituir pelo equivalente Playwright ao final
