# 03 — Fase 1: `Fix/playwright_core.py`

**Objetivo:** Criar `Fix/playwright_core.py` com a mesma API pública de `Fix/core.py`.
Todos os módulos que importam de `Fix/core.py` poderão trocar o import e funcionar.

**Arquivo de referência:** `Fix/core.py` (~2900 linhas, Selenium, funcional)
**Arquivo a criar:** `Fix/playwright_core.py` (no mesmo repo `d:\Play`)

---

## Por que criar um arquivo novo em vez de sobrescrever?

Porque durante a migração alguns módulos ainda usam `Fix/core.py` (Selenium).
Criar `Fix/playwright_core.py` permite importar do novo módulo nos arquivos já migrados,
enquanto os não migrados continuam usando `Fix/core.py`.
Quando todos os módulos estiverem migrados, `Fix/core.py` pode ser depreciado.

---

## Task 1.1 — Estrutura base e imports

**Description:** Criar o arquivo com imports Playwright, remover todos os imports Selenium,
manter imports utilitários (os, re, time, json, etc.) e configurar o logger.

**Acceptance criteria:**
- [ ] Arquivo criado em `Fix/playwright_core.py`
- [ ] `from playwright.sync_api import Page, Locator, sync_playwright, TimeoutError as PlaywrightTimeoutError` no topo
- [ ] Zero imports de `selenium.*`
- [ ] `logger` importado de `Fix.log` (igual ao core.py original)
- [ ] `DEBUG`, `TIME_ENABLED` e `medir_tempo` mantidos identicamente (não dependem de Selenium)

**Verification:**
- [ ] `py -c "from Fix.playwright_core import medir_tempo"` sem erro

**Dependencies:** Nenhuma

**Files:**
- `Fix/playwright_core.py` (novo)

**Scope:** XS

---

## Task 1.2 — Factory de drivers: `criar_driver_PC`, `criar_driver_VT`

**Description:** Implementar as funções de criação de browser/page Playwright,
com a mesma interface: `criar_driver_PC(headless=False) -> Page`.

**Referência em `Fix/core.py`:** linhas ~1790–1972 (`criar_driver_PC`, `criar_driver_VT`, etc.)

**Implementação Playwright:**
```python
from playwright.sync_api import sync_playwright, Page

def criar_driver_PC(headless: bool = False) -> Page:
    """Cria Page Playwright equivalente ao criar_driver_PC Selenium.
    
    Retorna Page. Para fechar: page.context.browser.close(); pw._impl_obj...
    Use finalizar_driver(page) para encerrar corretamente.
    """
    pw = sync_playwright().start()
    browser = pw.firefox.launch(
        headless=headless,
        executable_path=r"C:\Program Files\Firefox Developer Edition\firefox.exe",
        args=[],
        firefox_user_prefs={
            "dom.webdriver.enabled": False,
            "useAutomationExtension": False,
            "general.useragent.override": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "dom.webnotifications.enabled": False,
            "dom.min_background_timeout_value": 0,
        }
    )
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
    )
    page = context.new_page()
    # Guardar referência ao pw para poder parar depois
    page._pje_playwright = pw
    return page


def criar_driver_VT(headless: bool = False) -> Page:
    """Equivalente ao criar_driver_VT Selenium."""
    pw = sync_playwright().start()
    browser = pw.firefox.launch(
        headless=headless,
        firefox_user_prefs={
            "dom.webdriver.enabled": False,
            "useAutomationExtension": False,
            "extensions.update.enabled": False,
            "browser.cache.disk.enable": False,
        }
    )
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()
    page._pje_playwright = pw
    return page


def finalizar_driver(page: Page) -> None:
    """Encerra browser e playwright instance. Equivale a finalizar_driver do core.py."""
    try:
        browser = page.context.browser
        if browser:
            browser.close()
        pw = getattr(page, '_pje_playwright', None)
        if pw:
            pw.stop()
    except Exception as e:
        logger.warning("finalizar_driver: %s", e)
```

**Acceptance criteria:**
- [ ] `criar_driver_PC()` retorna `Page` navegável
- [ ] `criar_driver_PC(headless=True)` funciona sem janela visível
- [ ] `criar_driver_VT()` funciona analogamente
- [ ] `finalizar_driver(page)` encerra sem erros
- [ ] Sem `geckodriver.exe` necessário (Playwright gerencia o browser driver)

**Verification:**
```python
py -c "
from Fix.playwright_core import criar_driver_PC, finalizar_driver
page = criar_driver_PC(headless=True)
page.goto('about:blank')
print('URL:', page.url)
finalizar_driver(page)
print('OK')
"
```

**Dependencies:** Task 1.1

**Files:** `Fix/playwright_core.py`

**Scope:** S

---

## Task 1.3 — Esperas: `aguardar_renderizacao_nativa`, `esperar_elemento`, `wait`

**Description:** Reimplementar as funções de espera usando Playwright auto-wait.
Estas funções são as mais chamadas em todo o projeto.

**Referência em `Fix/core.py`:** linhas ~70–220

**Implementação:**
```python
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

def aguardar_renderizacao_nativa(
    page: Page,
    seletor: str = None,
    modo: str = "aparecer",
    timeout: float = 10,
) -> bool:
    """Substitui aguardar_renderizacao_nativa do core.py.
    
    Sem seletor: aguarda page load state.
    modo='aparecer': aguarda elemento visível.
    modo='sumir': aguarda elemento oculto/removido.
    modo='habilitado': aguarda elemento visível e habilitado.
    """
    timeout_ms = int(timeout * 1000)
    try:
        if not seletor:
            page.wait_for_load_state('domcontentloaded', timeout=timeout_ms)
            return True
        
        loc = page.locator(seletor)
        
        if modo == 'sumir':
            loc.wait_for(state='hidden', timeout=timeout_ms)
        elif modo == 'habilitado':
            loc.wait_for(state='visible', timeout=timeout_ms)
            # extra: aguardar não estar disabled
            page.wait_for_function(
                f"() => {{ const el = document.querySelector('{seletor}'); return el && !el.disabled; }}",
                timeout=timeout_ms
            )
        else:  # 'aparecer' (default)
            loc.wait_for(state='visible', timeout=timeout_ms)
        
        return True
    except PlaywrightTimeoutError:
        return False
    except Exception as e:
        logger.warning("aguardar_renderizacao_nativa: %s", e)
        return False


def esperar_elemento(
    page: Page,
    seletor: str,
    texto: str = None,
    timeout: float = 10,
    log: bool = False,
) -> object:  # retorna Locator ou None
    """Substitui esperar_elemento do core.py. Retorna Locator ou None."""
    timeout_ms = int(timeout * 1000)
    try:
        loc = page.locator(seletor)
        loc.wait_for(state='attached', timeout=timeout_ms)
        if texto:
            loc.filter(has_text=texto).wait_for(state='visible', timeout=timeout_ms)
            return loc.filter(has_text=texto).first
        return loc.first
    except PlaywrightTimeoutError:
        if log:
            logger.error("[ESPERAR][ERRO] Timeout para: '%s'", seletor)
        return None
    except Exception as e:
        if log:
            logger.error("[ESPERAR][ERRO] %s: %s", seletor, e)
        return None


# Aliases de compatibilidade
def wait(page: Page, selector: str, timeout: float = 10, **kwargs) -> object:
    """Compatibilidade com código legado que usa wait()."""
    return esperar_elemento(page, selector, timeout=timeout)

def wait_for_visible(page: Page, selector: str, timeout: float = 10, **kwargs) -> object:
    """Compatibilidade com código legado."""
    return esperar_elemento(page, selector, timeout=timeout)

def wait_for_clickable(page: Page, selector: str, timeout: float = 10, **kwargs) -> object:
    """Compatibilidade com código legado."""
    return esperar_elemento(page, selector, timeout=timeout)
```

**Acceptance criteria:**
- [ ] `esperar_elemento(page, 'mat-table')` retorna Locator quando elemento existe
- [ ] `esperar_elemento(page, '.inexistente', timeout=2)` retorna None sem lançar exceção
- [ ] `aguardar_renderizacao_nativa(page)` aguarda page load
- [ ] `aguardar_renderizacao_nativa(page, '.spinner', 'sumir')` aguarda elemento sumir

**Dependencies:** Tasks 1.1, 1.2

**Scope:** S

---

## Task 1.4 — Cliques: `aguardar_e_clicar`, `safe_click`, `safe_click_no_scroll`

**Description:** Reimplementar funções de clique. Esta é a maior simplificação da migração —
todos os fallbacks, zoom hacks e execute_async_script desaparecem.

**Referência em `Fix/core.py`:** linhas ~400–600 (aguardar_e_clicar, safe_click, etc.)

**Implementação:**
```python
def aguardar_e_clicar(
    page: Page,
    seletor: str,
    timeout: float = 10,
    log: bool = False,
    retornar_elemento: bool = False,
    **kwargs  # absorve parâmetros legados como usar_js, by
) -> object:
    """Substitui aguardar_e_clicar do core.py.
    
    Playwright auto-wait: espera o elemento ser visível e clicável automaticamente.
    Sem execute_async_script, sem zoom hacks, sem fallbacks manuais.
    """
    timeout_ms = int(timeout * 1000)
    try:
        loc = page.locator(seletor).first
        if retornar_elemento:
            loc.wait_for(state='visible', timeout=timeout_ms)
            return loc
        loc.click(timeout=timeout_ms)
        if log:
            logger.debug("aguardar_e_clicar: clicou em '%s'", seletor)
        return True
    except PlaywrightTimeoutError:
        if log:
            logger.error("aguardar_e_clicar: timeout para '%s'", seletor)
        return None if retornar_elemento else False
    except Exception as e:
        if log:
            logger.error("aguardar_e_clicar: %s: %s", seletor, e)
        return None if retornar_elemento else False


def safe_click(page: Page, selector_or_locator, timeout: float = 10, log: bool = False, **kwargs) -> bool:
    """Compatibilidade com safe_click do core.py."""
    if isinstance(selector_or_locator, str):
        return aguardar_e_clicar(page, selector_or_locator, timeout=timeout, log=log)
    # É um Locator
    try:
        selector_or_locator.click(timeout=int(timeout * 1000))
        return True
    except Exception as e:
        if log:
            logger.error("safe_click: %s", e)
        return False


def safe_click_no_scroll(page: Page, locator, log: bool = False) -> bool:
    """Compatibilidade com safe_click_no_scroll do core.py."""
    try:
        locator.click(force=True)
        return True
    except Exception as e:
        if log:
            logger.error("safe_click_no_scroll: %s", e)
        return False
```

**Acceptance criteria:**
- [ ] `aguardar_e_clicar(page, 'button')` clica e retorna True
- [ ] `aguardar_e_clicar(page, '.inexistente', timeout=2)` retorna False sem lançar
- [ ] `**kwargs` absorve `usar_js`, `by`, `debug` sem erro (compatibilidade)

**Dependencies:** Tasks 1.1, 1.3

**Scope:** S

---

## Task 1.5 — Preenchimento: `preencher_campo`, `selecionar_opcao`

**Description:** Reimplementar funções de formulário. O `preencher_campo` perde todo o
`execute_async_script` + `triggerEvent` porque Playwright já dispara eventos Angular.

**Referência em `Fix/core.py`:** linhas ~700–900

**Implementação:**
```python
def preencher_campo(
    page: Page,
    seletor: str,
    valor: str,
    trigger_events: bool = True,  # mantido na interface mas não necessário em Playwright
    limpar: bool = True,
    log: bool = False,
) -> bool:
    """Substitui preencher_campo do core.py.
    
    page.locator.fill() já:
    - limpa o campo
    - dispara input/change/blur para Angular
    - espera o elemento estar visível
    """
    try:
        loc = page.locator(seletor).first
        if limpar:
            loc.fill(str(valor))  # fill já limpa
        else:
            loc.press_sequentially(str(valor))
        if log:
            logger.debug("preencher_campo: '%s' = '%s'", seletor, str(valor)[:50])
        return True
    except Exception as e:
        if log:
            logger.warning("preencher_campo: %s: %s", seletor, e)
        return False


def selecionar_opcao(
    page: Page,
    seletor_dropdown: str,
    texto_opcao: str,
    timeout: float = 10,
    exato: bool = False,
    log: bool = False,
) -> bool:
    """Substitui selecionar_opcao do core.py para mat-select Angular Material.
    
    Strategy:
    1. Clicar no mat-select para abrir
    2. Usar get_by_role('option') com filtro de texto
    3. Clicar na opção
    """
    timeout_ms = int(timeout * 1000)
    try:
        # Resolver seletor se for nome conhecido
        seletores_conhecidos = {
            'destino': 'mat-select[aria-placeholder*="destino"], mat-select[formcontrolname="destinos"]',
            'fase': 'mat-select[formcontrolname="fpglobal_faseProcessual"]',
            'tipo': 'mat-select[formcontrolname="tipoCredito"]',
        }
        seletor_final = seletores_conhecidos.get(seletor_dropdown, seletor_dropdown)
        
        # Abrir dropdown
        page.locator(seletor_final).first.click(timeout=timeout_ms)
        
        # Aguardar opções
        page.locator('mat-option').first.wait_for(state='visible', timeout=timeout_ms)
        
        # Selecionar opção
        if exato:
            page.get_by_role('option', name=texto_opcao, exact=True).click(timeout=timeout_ms)
        else:
            page.locator('mat-option').filter(has_text=texto_opcao).first.click(timeout=timeout_ms)
        
        if log:
            logger.debug("selecionar_opcao: '%s' -> '%s'", seletor_dropdown, texto_opcao)
        return True
    except PlaywrightTimeoutError:
        if log:
            logger.error("selecionar_opcao: timeout para '%s' em '%s'", texto_opcao, seletor_dropdown)
        return False
    except Exception as e:
        if log:
            logger.error("selecionar_opcao: %s", e)
        return False
```

**Acceptance criteria:**
- [ ] `preencher_campo(page, 'input[formcontrolname="campo"]', 'valor')` preenche e retorna True
- [ ] `selecionar_opcao(page, 'mat-select', 'Análise')` abre dropdown e clica na opção
- [ ] Interface mantida: mesmos parâmetros que o original (compatibilidade de chamada)

**Dependencies:** Tasks 1.1, 1.3

**Scope:** M

---

## Task 1.6 — Busca inteligente: `buscar_seletor_robusto`

**Description:** Reimplementar usando locators Playwright nativos.
A versão Selenium usava 3 fases de busca; Playwright simplifica para get_by_label/placeholder/role.

**Referência em `Fix/core.py`:** linhas ~600–680

**Implementação:**
```python
def buscar_seletor_robusto(page: Page, textos: list, contexto=None, timeout: float = 5, log: bool = False):
    """Versão Playwright de buscar_seletor_robusto. Retorna Locator ou None."""
    for texto in textos:
        # Fase 1: por placeholder ou aria-label
        for loc in [
            page.get_by_placeholder(texto),
            page.get_by_label(texto),
            page.locator(f'input[aria-label*="{texto}"]'),
        ]:
            try:
                if loc.first.is_visible():
                    return loc.first
            except Exception:
                continue
        
        # Fase 2: por texto visível → input associado
        try:
            label = page.get_by_text(texto, exact=False).first
            if label.is_visible():
                # Tentar input associado via for= ou próximo input
                input_id = label.get_attribute('for')
                if input_id:
                    return page.locator(f'#{input_id}').first
        except Exception:
            pass
    
    return None
```

**Dependencies:** Task 1.1

**Scope:** XS

---

## Task 1.7 — `com_retry`, `ErroCollector`, `js_base`

**Description:**
- `com_retry` — mantido idêntico (não usa Selenium)
- `ErroCollector` — mantido idêntico (não usa Selenium)
- `js_base()` — mantido para compatibilidade com código que usa `page.evaluate()`,
  mas a maioria dos usos desaparece porque Playwright não precisa de MutationObserver

**Acceptance criteria:**
- [ ] `com_retry` aceita `page` em vez de `driver` nos args mas funciona igual (é genérico)
- [ ] `js_base()` retorna a mesma string JS (pode ser usada em `page.evaluate()` se necessário)

**Dependencies:** Task 1.1

**Scope:** XS

---

## Checkpoint Fase 1

Após todas as tasks 1.1–1.7:

```python
# Smoke test completo
py -c "
from Fix.playwright_core import (
    criar_driver_PC, finalizar_driver,
    aguardar_renderizacao_nativa, esperar_elemento,
    aguardar_e_clicar, preencher_campo, selecionar_opcao,
    com_retry, medir_tempo
)
print('Todos os imports OK')
page = criar_driver_PC(headless=True)
page.goto('https://pje.trt2.jus.br')
print('Navegação OK:', page.url)
finalizar_driver(page)
print('Finalização OK')
"
```

- [ ] Todos os imports OK
- [ ] `criar_driver_PC(headless=True)` abre e navega
- [ ] `Fix/playwright_core.py` sem nenhum `import selenium`
- [ ] `Fix/core.py` original intocado (referência Selenium ainda funcional)
