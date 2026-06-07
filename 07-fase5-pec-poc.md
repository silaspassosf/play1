# 07 — Fase 5: `PEC/` — Primeiro Módulo de Negócio (PoC)

**Objetivo:** Migrar o módulo PEC — o PoC real da migração.
Se PEC rodar em Playwright de ponta a ponta, a abordagem está validada.

**Dependência:** Fases 1–4 concluídas.

---

## Por que PEC é o melhor PoC?

1. **Modular**: entrypoint claro em `PEC/runtime_pec.py` → `executar_fluxo_novo_simplificado()`
2. **Heavy Angular Material**: formulários complexos (mat-select, mat-input, mat-datepicker)
   — exatamente onde Playwright mais brilha
3. **API-heavy**: 40% do fluxo é chamadas REST via `PjeApiClient` — não muda nada
4. **Relatório mensurável**: ao final, dá para comparar o número de erros PEC Selenium vs Playwright

---

## Inventário de arquivos PEC/

| Arquivo | Selenium? | Prioridade |
|---|---|---|
| `PEC/regras.py` | Via Fix | P0 |
| `PEC/prescricao.py` | Via Fix | P0 |
| `PEC/api_client.py` | Via Fix (session_from_driver) | P0 |
| `PEC/core_progresso.py` | Sem Selenium (JSON/IO) | P1 |
| `PEC/core_pos_carta.py` | Via Fix | P1 |
| `PEC/carta_utils.py` | Via Fix | P1 |
| `PEC/anexos/anexos_extracao.py` | Via Fix | P1 |
| `PEC/anexos/anexos_formatacao.py` | Via Fix | P1 |

---

## Task 5.1 — `PEC/regras.py` (arquivo central)

**Description:** O arquivo central de regras do PEC. Contém as funções de matching
e determinação de ações por observação (`determinar_acoes_por_observacao`,
`get_action_rules`, etc.).

**Mudanças:**
1. `from selenium.webdriver.common.by import By` → remover
2. `from selenium.webdriver.remote.webdriver import WebDriver` → `from playwright.sync_api import Page`
3. `from Fix.core import ...` → `from Fix.playwright_core import ...`
4. `from Fix.variaveis import session_from_driver` → `from Fix.variaveis import session_from_page`
5. `sess, trt = session_from_driver(driver)` → `sess, trt = session_from_page(page)`
6. Type hints: `driver: WebDriver` → `page: Page`

**Acceptance criteria:**
- [ ] `from PEC.regras import determinar_acoes_por_observacao` sem erro
- [ ] Nenhum `import selenium` em `PEC/regras.py`

**Files:** `PEC/regras.py`

**Scope:** M

---

## Task 5.2 — `PEC/prescricao.py`, `PEC/api_client.py`, `PEC/core_pos_carta.py`

**Description:** Migrar arquivos de suporte do PEC.

**Acceptance criteria:**
- [ ] `from PEC.prescricao import def_presc` sem erro
- [ ] `from PEC.api_client import *` sem erro
- [ ] Nenhum `import selenium` nos arquivos

**Files:** `PEC/prescricao.py`, `PEC/api_client.py`, `PEC/core_pos_carta.py`, `PEC/carta_utils.py`

**Scope:** S

---

## Task 5.3 — `PEC/anexos/` — módulo de anexos

**Description:** Migrar extração e formatação de anexos.
Usam `Fix/core.py` para interação com browser.

**Acceptance criteria:**
- [ ] Nenhum `import selenium` em `PEC/anexos/*.py`

**Files:** `PEC/anexos/anexos_extracao.py`, `PEC/anexos/anexos_formatacao.py`

**Scope:** M

---

## Task 5.4 — Teste de integração PEC end-to-end

**Description:** Executar o fluxo PEC completo num processo real de teste
para validar que a migração não quebrou nenhuma lógica de negócio.

**Roteiro de teste:**
1. `criar_driver_PC(headless=False)` → Page
2. `login_cpf(page, url, cpf, senha)`
3. `executar_fluxo_novo_simplificado(page)` em modo dry-run (ou num processo de teste)
4. Verificar logs: zero `WebDriverException`, zero `StaleElementReferenceException`

**Métricas a comparar (Selenium vs Playwright):**
- Tempo total de execução do lote
- Número de retries necessários
- Erros de element not found
- Flakiness em mat-select e mat-datepicker

**Acceptance criteria:**
- [ ] Fluxo PEC executa sem erro fatal em pelo menos 3 processos consecutivos
- [ ] Logs não mostram nenhuma exception Selenium
- [ ] Tempo de execução igual ou menor ao Selenium

**Dependencies:** Tasks 5.1–5.3

**Scope:** L (teste real no ambiente PJe)

---

## Checkpoint Fase 5 — PoC validado

```bash
# Zero Selenium em PEC/
grep -r 'from selenium' PEC/
# deve retornar vazio

# Imports OK
py -c "
from PEC.regras import determinar_acoes_por_observacao
from PEC.prescricao import def_presc
print('PEC/ migrado OK')
"
```

**Este checkpoint é o mais importante da migração.**
Se passar, os princípios estão validados e Prazo + Mandado são trabalho mecânico.

---

## Problemas esperados na Fase 5 e como resolver

### Problema 1: seletor CSS frágil no PJe
**Sintoma:** `TimeoutError` em seletores como `'button.mat-raised-button'`
**Solução Playwright:** Trocar para `page.get_by_role('button', name='Movimentar processos')`
ou `page.locator('button').filter(has_text='Movimentar processos')`

### Problema 2: mat-datepicker não aceita `fill()`
**Sintoma:** Data não é reconhecida pelo Angular Material
**Solução:**
```python
page.locator('input[matdatepicker]').fill('15/01/2025')
page.keyboard.press('Enter')
# ou usar o picker:
page.locator('input[matdatepicker]').click()
page.get_by_role('gridcell', name='15').click()
```

### Problema 3: mat-select fecha antes de clicar na opção
**Sintoma:** Option nunca é clicada, dropdown fecha sozinho
**Solução:**
```python
# Aguardar overlay do CDK aparecer antes de clicar
page.locator('div.cdk-overlay-container mat-option').wait_for(state='visible')
page.locator('mat-option').filter(has_text='Análise').click()
```

### Problema 4: Modal/overlay intercepta clique
**Sintoma:** `ElementClickInterceptedException` equivalente
**Solução Playwright:**
```python
# Verificar se há overlay aberto
overlay = page.locator('.cdk-overlay-backdrop')
if overlay.is_visible():
    overlay.click()  # fechar o overlay
    page.wait_for_timeout(300)
# Tentar novamente
page.locator('button.alvo').click()
```

### Problema 5: CKEditor não inicializou ainda
**Sintoma:** `CKEDITOR.instances is undefined` em `page.evaluate()`
**Solução:**
```python
# Aguardar CKEditor inicializar
page.wait_for_function("() => Object.keys(CKEDITOR.instances || {}).length > 0", timeout=10000)
page.evaluate("CKEDITOR.instances[Object.keys(CKEDITOR.instances)[0]].setData(html)")
```
