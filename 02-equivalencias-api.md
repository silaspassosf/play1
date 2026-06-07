# 02 — Equivalências de API: Selenium → Playwright

Este é o dicionário de tradução. Consultar em primeiro lugar ao reescrever qualquer função.

---

## 1. Tipos centrais

| Selenium | Playwright (sync_api) | Nota |
|---|---|---|
| `from selenium.webdriver.remote.webdriver import WebDriver` | `from playwright.sync_api import Page` | substituição 1:1 |
| `from selenium.webdriver.remote.webelement import WebElement` | `from playwright.sync_api import Locator` | substituição 1:1 |
| `from selenium.webdriver.common.by import By` | *(não existe)* | seletores são strings diretamente |
| `from selenium.webdriver.support.ui import WebDriverWait` | *(não existe)* | auto-wait nativo |
| `from selenium.webdriver.support import expected_conditions as EC` | *(não existe)* | estados via `locator.wait_for(state=...)` |
| `from selenium.webdriver.common.keys import Keys` | *(não existe)* | `locator.press('Enter')`, `locator.press('Tab')` |
| `from selenium.common.exceptions import TimeoutException` | `from playwright.sync_api import TimeoutError` | nome diferente |
| `from selenium.common.exceptions import NoSuchElementException` | *(não existe)* | use `locator.count() == 0` |
| `from selenium.common.exceptions import StaleElementReferenceException` | *(não existe)* | Playwright relocaliza automaticamente |

---

## 2. Criação do browser e navegação

| Selenium | Playwright |
|---|---|
| `driver = webdriver.Firefox(options=options, service=service)` | `browser = pw.firefox.launch(headless=False)` |
| `options.add_argument('-headless')` | `pw.firefox.launch(headless=True)` |
| `options.binary_location = r"C:\Prog...\firefox.exe"` | `pw.firefox.launch(executable_path=r"C:\...\firefox.exe")` |
| `driver.maximize_window()` | `context = browser.new_context(viewport={'width': 1920, 'height': 1080})` |
| `driver.set_window_size(1920, 1080)` | mesmo acima |
| `driver.implicitly_wait(10)` | *(não usar)* — Playwright tem auto-wait por locator |
| `driver.get(url)` | `page.goto(url)` |
| `driver.current_url` | `page.url` |
| `driver.back()` | `page.go_back()` |
| `driver.forward()` | `page.go_forward()` |
| `driver.refresh()` | `page.reload()` |
| `driver.quit()` | `browser.close(); pw.stop()` |
| `driver.close()` | `page.close()` |

---

## 3. Localização de elementos

| Selenium | Playwright |
|---|---|
| `driver.find_element(By.CSS_SELECTOR, sel)` | `page.locator(sel)` |
| `driver.find_elements(By.CSS_SELECTOR, sel)` | `page.locator(sel).all()` |
| `driver.find_element(By.XPATH, xpath)` | `page.locator(f'xpath={xpath}')` |
| `driver.find_element(By.ID, id)` | `page.locator(f'#{id}')` |
| `driver.find_element(By.NAME, name)` | `page.locator(f'[name="{name}"]')` |
| `element.find_element(By.CSS_SELECTOR, sel)` | `locator.locator(sel)` (sub-locator) |
| `element.find_elements(By.CSS_SELECTOR, sel)` | `locator.locator(sel).all()` |
| `element.find_element(By.XPATH, './...')` | `locator.locator('xpath=./...')` |
| aria-label | `page.get_by_label('texto')` |
| role | `page.get_by_role('button', name='Salvar')` |
| placeholder | `page.get_by_placeholder('texto')` |
| text visible | `page.get_by_text('texto')` |

### Filtros (muito úteis para Angular Material)
```python
# Selecionar mat-option que contenha texto específico
page.locator('mat-option').filter(has_text='Análise').click()

# Combinar role + filtro
page.get_by_role('option').filter(has_text='Execução').click()
```

---

## 4. Esperas (o maior ganho do Playwright)

| Selenium | Playwright |
|---|---|
| `WebDriverWait(driver, t).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))` | `page.locator(sel).wait_for(state='attached', timeout=t*1000)` |
| `WebDriverWait(driver, t).until(EC.visibility_of_element_located(...))` | `page.locator(sel).wait_for(state='visible', timeout=t*1000)` |
| `WebDriverWait(driver, t).until(EC.element_to_be_clickable(...))` | automático no `.click()` |
| `EC.invisibility_of_element_located(...)` | `page.locator(sel).wait_for(state='hidden')` |
| `aguardar_renderizacao_nativa(driver)` | `page.wait_for_load_state('domcontentloaded')` |
| `aguardar_renderizacao_nativa(driver, sel, 'aparecer')` | `page.locator(sel).wait_for(state='visible')` |
| `aguardar_renderizacao_nativa(driver, sel, 'sumir')` | `page.locator(sel).wait_for(state='hidden')` |
| `aguardar_renderizacao_nativa(driver, sel, 'habilitado')` | `page.locator(sel).wait_for(state='visible')` + checar enabled |
| `wait_for_page_load(driver)` | `page.wait_for_load_state('load')` |
| `time.sleep(1)` | **não usar** — use `page.wait_for_timeout(1000)` apenas se necessário |

### Angular zone stability (substitui `aguardar_renderizacao_nativa` para Angular)
```python
# Aguardar Angular estabilizar completamente (equivale ao aguardar_renderizacao_nativa sem seletor)
page.wait_for_function(
    "() => window.getAllAngularTestabilities?.()?.every(t => t.isStable()) ?? true"
)
```

---

## 5. Interação com elementos

| Selenium | Playwright |
|---|---|
| `element.click()` | `locator.click()` |
| `driver.execute_script("arguments[0].click();", el)` | `locator.click(force=True)` |
| `element.send_keys('texto')` | `locator.fill('texto')` (limpa e preenche) |
| `element.send_keys('texto')` (append) | `locator.press_sequentially('texto')` |
| `element.clear()` | `locator.clear()` |
| `element.send_keys(Keys.ENTER)` | `locator.press('Enter')` |
| `element.send_keys(Keys.TAB)` | `locator.press('Tab')` |
| `element.send_keys(Keys.ARROW_DOWN)` | `locator.press('ArrowDown')` |
| `element.is_displayed()` | `locator.is_visible()` |
| `element.is_enabled()` | `locator.is_enabled()` |
| `element.text` | `locator.text_content()` ou `locator.inner_text()` |
| `element.get_attribute('href')` | `locator.get_attribute('href')` |
| `driver.execute_script("arguments[0].scrollIntoView();", el)` | `locator.scroll_into_view_if_needed()` |
| `ActionChains(driver).move_to_element(el).click().perform()` | `locator.click()` (auto-scroll incluso) |

---

## 6. JavaScript

| Selenium | Playwright |
|---|---|
| `driver.execute_script("return document.title")` | `page.evaluate("() => document.title")` |
| `driver.execute_script("arguments[0].click();", el)` | `page.evaluate("el => el.click()", element_handle)` |
| `driver.execute_async_script(script)` | `page.evaluate(async_script)` ou `page.evaluate_handle(...)` |
| `driver.execute_script("CKEDITOR.instances['x'].setData('html')")` | `page.evaluate("CKEDITOR.instances['x'].setData('html')")` |
| `driver.execute_script("return document.readyState")` | não necessário — use `wait_for_load_state` |
| `js_base() + esperarElemento(sel)` | `page.locator(sel).wait_for()` (não precisa de JS) |

---

## 7. Cookies e sessão

| Selenium | Playwright |
|---|---|
| `driver.get_cookies()` | `page.context.cookies()` |
| `driver.add_cookie({'name': n, 'value': v})` | `page.context.add_cookies([{'name': n, 'value': v, 'url': url}])` |
| `session_from_driver(driver)` | `session_from_page(page)` — ver `05-fase3-session-bridge.md` |

### Implementação de `session_from_page`:
```python
def session_from_page(page, grau: int = 1):
    sess = requests.Session()
    for c in page.context.cookies():
        sess.cookies.set(c['name'], c['value'], domain=c.get('domain', ''))
    parsed = urlparse(page.url)
    trt_host = parsed.netloc
    sess.headers.update({
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'X-Grau-Instancia': str(grau)
    })
    return sess, trt_host
```

---

## 8. Abas (janelas)

| Selenium | Playwright |
|---|---|
| `driver.window_handles` | `page.context.pages` |
| `driver.switch_to.window(handle)` | `nova_page = page.context.pages[-1]` |
| `driver.window_handles[-1]` (nova aba) | `page.context.wait_for_event('page')` → retorna nova `Page` |
| `driver.close()` (fechar aba atual) | `page.close()` |

### Aguardar nova aba abrir:
```python
with page.context.expect_page() as new_page_info:
    page.locator('button#abrirAba').click()
nova_aba = new_page_info.value
nova_aba.wait_for_load_state()
```

---

## 9. Validação de driver (browser_suporte)

| Selenium | Playwright |
|---|---|
| `driver.session_id is None` | `page.is_closed()` |
| `driver.current_url` (teste de conexão) | `page.url` (não lança exceção se fechada) |
| `is_browsing_context_discarded_error(msg)` | `page.is_closed()` |
| `validar_conexao_driver(driver)` | `not page.is_closed()` |
| overlays headless (`limpar_overlays_headless`) | **não necessário** — Playwright não tem esse problema |
| zoom hack (`document.body.style.zoom = '60%'`) | **não necessário** |
| `click_headless_safe(driver, sel)` | `page.locator(sel).click()` — funciona igual visible/headless |

---

## 10. Angular Material — receitas específicas PJe

Ver `09-padroes-angular-pje.md` para receitas completas. Sumário:

```python
# mat-select dropdown
page.locator('mat-select[formcontrolname="destinos"]').click()
page.get_by_role('option', name='Análise').click()

# mat-input (Angular Material text field)
page.locator('input[formcontrolname="campo"]').fill('valor')
# Playwright já dispara os eventos necessários para Angular

# mat-checkbox
page.locator('mat-checkbox').click()

# mat-datepicker
page.locator('input[matdatepicker]').fill('15/01/2025')
page.keyboard.press('Escape')  # fechar o picker

# Aguardar mat-spinner desaparecer (loading Angular)
page.locator('mat-spinner').wait_for(state='hidden')
```

---

## 11. Erros e exceções

| Selenium Exception | Playwright Equivalente |
|---|---|
| `TimeoutException` | `playwright.sync_api.TimeoutError` |
| `NoSuchElementException` | `locator.count() == 0` ou `expect(locator).to_have_count(0)` |
| `StaleElementReferenceException` | **não existe** — Playwright re-resolve automaticamente |
| `ElementClickInterceptedException` | `locator.click(force=True)` ou remover overlay |
| `ElementNotInteractableException` | `locator.click(force=True)` |
| `WebDriverException` | `playwright.sync_api.Error` |

---

## 12. Patterns depreciados que DESAPARECEM

Estes padrões do `Fix/core.py` não têm equivalente porque **não são necessários** em Playwright:

- `js_base()` — os MutationObservers eram workaround para Selenium. Playwright tem auto-wait.
- `aguardar_e_clicar(driver, sel)` usando `execute_async_script` — vira `page.locator(sel).click()`
- `preencher_campo` com `execute_async_script` + `triggerEvent` — vira `locator.fill(valor)` (Playwright já dispara eventos Angular)
- Zoom hack (`document.body.style.zoom = '60%'`) — não necessário
- `click_headless_safe` — `locator.click()` funciona igual em visible e headless
- `limpar_overlays_headless` — não necessário
- `safe_click` com todas as estratégias de fallback — `locator.click()` com `force=True` cobre todos os casos
- `com_retry` para Selenium — Playwright tem retry automático em locators; para lógica de negócio, manter `com_retry`
