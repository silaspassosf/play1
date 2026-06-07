# 04 — Fase 2: `Fix/browser_suporte.py` + `Fix/utils.py`

**Objetivo:** Sobrescrever `Fix/browser_suporte.py` e `Fix/utils.py` com implementações Playwright.
`Fix/extracao.py` fica para a fase seguinte (mais complexo).

**Dependência:** Fase 1 (`Fix/playwright_core.py`) concluída.

---

## Fix/browser_suporte.py

**Arquivo de referência:** `Fix/browser_suporte.py` (consolidação de `Fix/abas.py`,
`Fix/headless_helpers.py`, `Fix/otimizacao_wrapper.py`)

### Funções e seu destino na migração

| Função atual | Destino Playwright |
|---|---|
| `is_browsing_context_discarded_error(msg)` | `page.is_closed()` — simplificado |
| `validar_conexao_driver(driver)` | `validar_conexao_page(page)` |
| `trocar_para_nova_aba(driver)` | retornar `page.context.pages[-1]` |
| `forcar_fechamento_abas_extras(driver)` | fechar todas as `page.context.pages` exceto a primeira |
| `click_headless_safe(driver, sel)` | `page.locator(sel).click()` — sem lógica especial |
| `scroll_to_element_safe(driver, el)` | `locator.scroll_into_view_if_needed()` |
| `limpar_overlays_headless(driver)` | **NÃO NECESSÁRIO** — remover |
| `inicializar_otimizacoes(driver)` | vazio / não necessário |
| `finalizar_otimizacoes(driver)` | vazio / não necessário |

---

## Task 2.1 — `Fix/browser_suporte.py` sobrescrito

**Description:** Reescrever `browser_suporte.py` usando as equivalências Playwright.
Remover funções que não fazem sentido no Playwright (`limpar_overlays_headless`,
`click_headless_safe` com toda a lógica de fallback).

**Implementação das funções principais:**
```python
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from Fix.log import logger


def validar_conexao_page(page: Page, contexto: str = "GERAL", proc_id: str = None) -> bool:
    """Versão Playwright de validar_conexao_driver."""
    if page.is_closed():
        logger.error("validar_conexao_page: page está fechada [%s]", contexto)
        return False
    try:
        _ = page.url  # teste de conexão
        return True
    except Exception as e:
        logger.error("validar_conexao_page: erro: %s", e)
        return False


# Alias para compatibilidade com código que chama validar_conexao_driver
def validar_conexao_driver(page: Page, contexto: str = "GERAL", proc_id: str = None):
    return validar_conexao_page(page, contexto, proc_id)


def is_browsing_context_discarded_error(error_message: str) -> bool:
    """Compatibilidade. No Playwright basta checar page.is_closed()."""
    if not error_message:
        return False
    msg = str(error_message).lower()
    return 'target closed' in msg or 'page closed' in msg or 'connection closed' in msg


def trocar_para_nova_aba(page: Page, timeout: float = 10) -> Page:
    """Retorna a última aba aberta no contexto. Equivale a trocar_para_nova_aba."""
    pages = page.context.pages
    if len(pages) > 1:
        return pages[-1]
    # Aguardar nova aba
    try:
        with page.context.expect_page(timeout=int(timeout * 1000)) as new_page_info:
            pass
        return new_page_info.value
    except PlaywrightTimeoutError:
        logger.warning("trocar_para_nova_aba: nenhuma nova aba abriu em %ss", timeout)
        return page


def forcar_fechamento_abas_extras(page: Page) -> None:
    """Fecha todas as abas exceto a principal."""
    pages = page.context.pages
    for p in pages[1:]:
        try:
            p.close()
        except Exception as e:
            logger.debug("forcar_fechamento_abas_extras: %s", e)


def scroll_to_element_safe(page: Page, locator, log: bool = False) -> bool:
    """Scroll seguro — usa scroll_into_view_if_needed do Playwright."""
    try:
        locator.scroll_into_view_if_needed()
        return True
    except Exception as e:
        if log:
            logger.warning("scroll_to_element_safe: %s", e)
        return False


def click_headless_safe(page: Page, seletor: str, timeout: float = 10) -> bool:
    """Compatibilidade. No Playwright .click() já funciona em headless."""
    try:
        page.locator(seletor).first.click(timeout=int(timeout * 1000))
        return True
    except Exception as e:
        logger.warning("click_headless_safe: %s: %s", seletor, e)
        return False


# Funções de otimização — no Playwright são no-op (gerenciado pelo browser launch)
def inicializar_otimizacoes(page: Page) -> None:
    pass

def finalizar_otimizacoes(page: Page) -> None:
    pass

# Funções de modo headless — Playwright não precisa de detecção especial
def is_headless_mode(page: Page) -> bool:
    """Sempre False no contexto Playwright — sem tratamento especial para headless."""
    return False
```

**Acceptance criteria:**
- [ ] `from Fix.browser_suporte import validar_conexao_page, trocar_para_nova_aba` sem erro
- [ ] `validar_conexao_driver` exportado como alias (compatibilidade de chamada)
- [ ] Zero imports de `selenium.*` em `browser_suporte.py`

**Verification:**
```bash
py -c "from Fix.browser_suporte import validar_conexao_driver, trocar_para_nova_aba, click_headless_safe; print('OK')"
```

**Dependencies:** Fase 1 completa

**Files:** `Fix/browser_suporte.py`

**Scope:** M

---

## Task 2.2 — `Fix/utils.py` — função `login_cpf`

**Description:** A função crítica de `Fix/utils.py` na migração é `login_cpf`.
As funções de CKEditor (`inserir_html_editor`, `inserir_texto_editor`) também precisam ser migradas.
Funções utilitárias puras (validar_cpf, formatar_data, etc.) não precisam de mudança.

**Referência em `Fix/utils.py`:** linha ~369 (`login_cpf`)

**Implementação `login_cpf` Playwright:**
```python
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

def login_cpf(
    page: Page,
    url_login: str = None,
    cpf: str = None,
    senha: str = None,
    aguardar_url_final: bool = True,
) -> bool:
    """Realiza login no PJe por CPF. Substitui login_cpf do utils.py.
    
    O PJe usa Angular Material. Playwright preenche os campos diretamente
    sem precisar de execute_script ou wait manual.
    """
    try:
        if url_login:
            page.goto(url_login)
        
        # Aguardar formulário de login carregar
        page.locator('input[id*="cpf"], input[formcontrolname*="cpf"], input[placeholder*="CPF"]').first.wait_for(
            state='visible', timeout=15000
        )
        
        # Preencher CPF
        page.locator('input[id*="cpf"], input[formcontrolname*="cpf"]').first.fill(cpf)
        
        # Preencher senha
        page.locator('input[type="password"]').first.fill(senha)
        
        # Clicar em entrar
        page.get_by_role('button', name='Entrar').click()
        # Fallback
        if not page.get_by_role('button', name='Entrar').count():
            page.locator('button[type="submit"]').first.click()
        
        if aguardar_url_final:
            # Aguardar redirecionamento pós-login
            page.wait_for_url('**/pjekz/**', timeout=30000)
        
        logger.info("login_cpf: login realizado com sucesso")
        return True
    except PlaywrightTimeoutError:
        logger.error("login_cpf: timeout — formulário não carregou ou redirect falhou")
        return False
    except Exception as e:
        logger.error("login_cpf: erro: %s", e)
        return False
```

**ATENÇÃO:** O seletor exato do campo CPF no PJe precisa ser verificado na primeira execução real.
Inspecionar o HTML do formulário de login e ajustar o seletor se necessário.

---

## Task 2.3 — `Fix/utils.py` — funções CKEditor

**Description:** `inserir_html_editor` e `inserir_texto_editor` usam `driver.execute_script`.
No Playwright, muda para `page.evaluate()`.

**Implementação:**
```python
def inserir_html_editor(page: Page, html: str, editor_id: str = None) -> bool:
    """Insere HTML no CKEditor. Equivale a inserir_html_editor do utils.py."""
    try:
        if editor_id:
            page.evaluate(f"CKEDITOR.instances['{editor_id}'].setData(arguments[0])", html)
        else:
            # Pegar a primeira instância disponível
            page.evaluate("""
                (html) => {
                    const ids = Object.keys(CKEDITOR.instances);
                    if (ids.length > 0) {
                        CKEDITOR.instances[ids[0]].setData(html);
                        return true;
                    }
                    return false;
                }
            """, html)
        return True
    except Exception as e:
        logger.error("inserir_html_editor: %s", e)
        return False


def inserir_texto_editor(page: Page, texto: str, editor_id: str = None) -> bool:
    """Insere texto puro no CKEditor."""
    try:
        if editor_id:
            page.evaluate(f"CKEDITOR.instances['{editor_id}'].insertText(arguments[0])", texto)
        else:
            page.evaluate("""
                (texto) => {
                    const ids = Object.keys(CKEDITOR.instances);
                    if (ids.length > 0) {
                        CKEDITOR.instances[ids[0]].insertText(texto);
                        return true;
                    }
                    return false;
                }
            """, texto)
        return True
    except Exception as e:
        logger.error("inserir_texto_editor: %s", e)
        return False
```

**Acceptance criteria:**
- [ ] `login_cpf(page, url, cpf, senha)` navega para PJe e preenche os campos
- [ ] `inserir_html_editor(page, '<p>texto</p>')` injeta via `page.evaluate()`
- [ ] Funções utilitárias puras (sem Selenium) permanecem idênticas
- [ ] Zero imports de `selenium.*` em `utils.py`

**Verification:**
```bash
py -c "from Fix.utils import login_cpf, inserir_html_editor, validar_cpf; print('OK')"
```

**Dependencies:** Task 2.1, Fase 1

**Files:** `Fix/utils.py`

**Scope:** M

---

## Checkpoint Fase 2

```bash
# Fix/browser_suporte.py e Fix/utils.py sem imports Selenium
py -m py_compile Fix/browser_suporte.py
py -m py_compile Fix/utils.py

# Smoke test
py -c "
from Fix.browser_suporte import validar_conexao_driver, trocar_para_nova_aba
from Fix.utils import login_cpf, inserir_html_editor
print('Fix/browser_suporte.py OK')
print('Fix/utils.py OK')
"
```

- [ ] Ambos compilam sem erro
- [ ] Zero `import selenium` nos dois arquivos
- [ ] `Fix/core.py` (Selenium original) ainda intocado
