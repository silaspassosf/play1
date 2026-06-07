# 06 — Fase 4: Módulo `atos/`

**Objetivo:** Migrar todos os arquivos de `atos/` de Selenium para Playwright.
Este módulo é a ponte entre a camada Fix e os módulos de negócio (PEC, Prazo, Mandado).

**Dependência:** Fases 1, 2 e 3 concluídas.

---

## Inventário de arquivos em `atos/`

| Arquivo | Dependência Selenium | Complexidade |
|---|---|---|
| `atos/judicial.py` | via Fix/core | Alta |
| `atos/movimentos.py` | via Fix/core | Média |
| `atos/movimentos_chips.py` | via Fix/core | Média |
| `atos/regras.py` | via Fix/core | Média |
| `atos/wrappers_mov.py` | via Fix/core | Média |
| `atos/anexos/anexos_extracao.py` | via Fix/core | Média |
| `atos/anexos/anexos_formatacao.py` | via Fix/core | Baixa |

---

## Padrão de migração para atos/

**A maioria dos arquivos em `atos/` segue este padrão simples:**

```python
# ANTES (Selenium)
from selenium.webdriver.remote.webdriver import WebDriver
from Fix.core import aguardar_e_clicar, esperar_elemento, preencher_campo

def minha_funcao(driver: WebDriver, ...) -> bool:
    aguardar_e_clicar(driver, 'button.salvar')
    preencher_campo(driver, 'input#campo', 'valor')
    return True

# DEPOIS (Playwright) — mudanças mínimas
from playwright.sync_api import Page
from Fix.playwright_core import aguardar_e_clicar, esperar_elemento, preencher_campo

def minha_funcao(page: Page, ...) -> bool:
    aguardar_e_clicar(page, 'button.salvar')   # mesmo código
    preencher_campo(page, 'input#campo', 'valor')  # mesmo código
    return True
```

**As 3 mudanças em cada arquivo:**
1. `from selenium... import WebDriver` → `from playwright.sync_api import Page`
2. `from Fix.core import ...` → `from Fix.playwright_core import ...`
3. `driver: WebDriver` → `page: Page` nos type hints de cada função

**A lógica interna não muda.**

---

## Task 4.1 — `atos/judicial.py` e `atos/regras.py`

**Description:** Migrar `judicial.py` (atos judiciais) e `regras.py` (regras de atos).
`ato_judicial()` é a função mais usada do módulo. A interface deve ser preservada.

**Mudanças:**
- Trocar imports Selenium por Playwright
- `driver: WebDriver` → `page: Page` nos type hints
- Trocar `from Fix.core import` por `from Fix.playwright_core import`
- Verificar se há `WebDriverWait` ou `By` inline e converter

**Acceptance criteria:**
- [ ] `from atos.judicial import ato_judicial` sem erro
- [ ] Nenhum `import selenium` nos arquivos
- [ ] Type hints atualizados para `Page`

**Arquivos:**
- `atos/judicial.py`
- `atos/regras.py`

**Scope:** M

---

## Task 4.2 — `atos/movimentos.py`, `atos/movimentos_chips.py`, `atos/wrappers_mov.py`

**Description:** Migrar módulo de movimentos processuais e chips.

**Mudanças:**
- Mesmas 3 mudanças do padrão acima

**Acceptance criteria:**
- [ ] `from atos.movimentos import mov` sem erro
- [ ] Nenhum `import selenium` nos arquivos

**Arquivos:**
- `atos/movimentos.py`
- `atos/movimentos_chips.py`
- `atos/wrappers_mov.py`

**Scope:** M

---

## Task 4.3 — `atos/anexos/` — extração e formatação

**Description:** Migrar os arquivos de anexos. Usam `Fix/core.py` para interação com browser.

**Mudanças:**
- Mesmas 3 mudanças do padrão acima
- Verificar se há `WebDriverWait` ou `By` inline

**Acceptance criteria:**
- [ ] Nenhum `import selenium` em `atos/anexos/*.py`
- [ ] Smoke test de import sem erro

**Arquivos:**
- `atos/anexos/anexos_extracao.py`
- `atos/anexos/anexos_formatacao.py`

**Scope:** S

---

## Checkpoint Fase 4

```bash
# Smoke test todos os módulos atos/
py -c "
from atos.judicial import ato_judicial
from atos.movimentos import mov
from atos.regras import *
print('atos/ OK — zero Selenium')
"

# Verificar que não sobrou nenhum import Selenium
grep -r 'from selenium' atos/
# deve retornar vazio
```

- [ ] Todos os imports OK
- [ ] `grep -r 'from selenium' atos/` retorna vazio
- [ ] `Fix/playwright_core.py` continua sendo a única dependência de browser em `atos/`
