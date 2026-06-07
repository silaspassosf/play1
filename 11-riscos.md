# 11 — Riscos da Migração

**Registro de riscos identificados antes de iniciar.**
Cada risco tem: probabilidade (Alta/Média/Baixa) × impacto (Alto/Médio/Baixo) = prioridade.

---

## Tabela de riscos

| # | Risco | Prob | Impacto | Prioridade | Mitigação |
|---|---|---|---|---|---|
| R1 | Firefox binary path diferente no Playwright vs geckodriver | Alta | Alto | 🔴 | Ver seção R1 abaixo |
| R2 | mat-select CDK overlay timing (opção some antes de clicar) | Média | Alto | 🔴 | Ver seção R2 |
| R3 | CKEditor versão incompatível com `setData()` async | Média | Alto | 🔴 | Ver seção R3 |
| R4 | Angular zone wait não disponível na versão PJe em produção | Média | Médio | 🟡 | Ver seção R4 |
| R5 | Estrutura de cookies `page.context.cookies()` diferente de `driver.get_cookies()` | Baixa | Alto | 🟡 | Ver seção R5 |
| R6 | ThreadPoolExecutor com Playwright (SISB) — contextos não thread-safe | Alta | Alto | 🔴 | Ver seção R6 |
| R7 | Headless: print dialogs SISB não são suportados em Playwright | Média | Médio | 🟡 | Ver seção R7 |
| R8 | Selenium como dependência transitiva de outro pacote | Baixa | Baixo | 🟢 | `pip show selenium` após migração |
| R9 | Playwright Firefox não suporta extensões | Alta | Médio | 🟡 | Ver seção R9 |
| R10 | Sessão PJe expira durante loop longo (cookie TTL) | Média | Alto | 🔴 | Detecção + re-login já implementada |

---

## R1 — Firefox binary path

### Problema
Playwright baixa seu próprio Firefox (isolado, versão pinned).
Não usa o `Firefox Developer Edition` configurado no Selenium.

### Sintoma
```
Error: Failed to launch firefox (executable doesn't exist at /path/to/ms-playwright/firefox...)
```

### Mitigação
```python
# playwright_core.py — criar_driver_PC()
from playwright.sync_api import sync_playwright
import os

def criar_driver_PC(headless=False):
    pw = sync_playwright().start()
    # Playwright usa seu próprio Firefox — não precisa configurar path
    browser = pw.firefox.launch(headless=headless)
    page = browser.new_page()
    return page, browser, pw  # retornar os 3 para poder fechar corretamente
```

### Resolução antecipada
```powershell
playwright install firefox
# Verificar onde foi instalado
playwright install --dry-run firefox
```

---

## R2 — mat-select CDK overlay timing

### Problema
Após clicar no mat-select, o overlay CDK (`div.cdk-overlay-pane`) aparece mas
as `mat-option` podem não estar renderizadas imediatamente. Se tentar clicar muito rápido:
- opção não encontrada
- overlay fecha sozinho

### Sintoma
```
TimeoutError: waiting for locator('mat-option') to be visible
```

### Mitigação
```python
def selecionar_mat_select(page, seletor_select: str, texto_opcao: str):
    page.locator(seletor_select).click()
    # Aguardar CDK overlay ABRIR e renderizar opções
    page.locator('div.cdk-overlay-pane').wait_for(state='visible', timeout=5000)
    # Aguardar pelo menos 1 opção
    page.locator('mat-option').first.wait_for(state='visible', timeout=5000)
    # Clicar na opção correta
    page.locator('mat-option').filter(has_text=texto_opcao).click()
    # Aguardar CDK overlay FECHAR
    page.locator('div.cdk-overlay-pane').wait_for(state='hidden', timeout=5000)
```

---

## R3 — CKEditor versão

### Problema
PJe pode usar CKEditor 4 (API síncrona: `setData()`) ou CKEditor 5 (API diferente).
A receita de `09-padroes-angular-pje.md` assume CKEditor 4.

### Como verificar
```python
# No console do browser / page.evaluate:
versao = page.evaluate("() => typeof CKEDITOR !== 'undefined' ? CKEDITOR.version : (typeof ClassicEditor !== 'undefined' ? 'CKEditor5' : 'não encontrado')")
print(versao)
```

### Mitigação CKEditor 5
```python
# CKEditor 5 usa API diferente
page.evaluate("""
    () => {
        // CKEditor 5 — acessado via instância no DOM
        const el = document.querySelector('.ck-editor__editable');
        if (el && el.ckeditorInstance) {
            el.ckeditorInstance.setData(html);
        }
    }
""", html)
```

---

## R4 — Angular zone stability

### Problema
`window.getAllAngularTestabilities()` pode não existir em versões antigas do Angular
ou quando a aplicação não expõe testabilities (produção com otimizações).

### Sintoma
`wait_for_function` resolve `undefined` imediatamente sem aguardar nada.

### Mitigação
```python
def aguardar_angular_safe(page, timeout_ms=10000):
    """Aguarda Angular com fallback gracioso."""
    try:
        resultado = page.wait_for_function(
            """() => {
                const testabilities = window.getAllAngularTestabilities?.();
                if (!testabilities || testabilities.length === 0) return true;  // fallback
                return testabilities.every(t => t.isStable());
            }""",
            timeout=timeout_ms
        )
        return True
    except Exception:
        # Fallback: aguardar ausência de spinners
        try:
            page.locator('mat-spinner').wait_for(state='hidden', timeout=timeout_ms)
            return True
        except Exception:
            return False
```

---

## R5 — Estrutura de cookies

### Problema
`driver.get_cookies()` retorna lista de dicts com chaves do Selenium.
`page.context.cookies()` retorna lista de dicts com chaves do Playwright.
As chaves são ligeiramente diferentes (`httpOnly` vs `http_only`, etc.).

### Verificação
```python
# Selenium: {'name': 'JSESSIONID', 'value': 'xxx', 'domain': '...', 'path': '/', 'secure': False, 'httpOnly': True}
# Playwright: {'name': 'JSESSIONID', 'value': 'xxx', 'domain': '...', 'path': '/', 'secure': False, 'httpOnly': True, 'sameSite': 'None'}
```

### Mitigação
`session_from_page` em `Fix/variaveis.py` deve mapear os campos explicitamente:

```python
def session_from_page(page, grau=1):
    pw_cookies = page.context.cookies()
    sess = requests.Session()
    for c in pw_cookies:
        sess.cookies.set(c['name'], c['value'], domain=c.get('domain', ''))
    trt_host = page.url.split('/')[2]  # extrai o host
    return sess, trt_host
```

---

## R6 — ThreadPoolExecutor + Playwright

### Problema
`playwright.sync_api` **NÃO é thread-safe**. Não é possível compartilhar `Page` ou `BrowserContext`
entre threads. `SISB/helpers.py` usa `ThreadPoolExecutor` com `max_workers=20`.

### Impacto
Se SISB chamar funções Playwright dentro de threads → crash imediato.

### Mitigação
A parte do ThreadPoolExecutor em SISB é para chamadas **API REST** (`PjeApiClient`), 
não para automação de browser. O browser roda em 1 thread; só as chamadas `requests` são paralelas.

**Verificar** ao chegar na migração SISB: confirmar que o `ThreadPoolExecutor` só chama `client.timeline()` 
e similares — nunca `page.locator()` dentro das threads.

Se necessário paralelismo real com browser: usar `browser.new_context()` por thread.

---

## R7 — Print dialogs no SISB

### Problema
SISB provavelmente usa `window.print()` ou emite relatórios em PDF.
Playwright intercepta print dialogs mas não os executa automaticamente.

### Mitigação
```python
# Interceptar e ignorar print dialogs
page.on('dialog', lambda dialog: dialog.dismiss())

# Para gerar PDF no Playwright (headless only):
pdf_bytes = page.pdf(format='A4')
with open('relatorio.pdf', 'wb') as f:
    f.write(pdf_bytes)
```

---

## R9 — Playwright Firefox não suporta extensões

### Problema
Playwright Firefox não carrega extensões (`.xpi`) ao contrário do geckodriver.
Se o projeto depende de alguma extensão Firefox → não funcionará.

### Verificação
Checar `Fix/variaveis.py` e `Fix/browser_suporte.py` por referências a `.xpi` ou extensões.

### Alternativa
Se extensão for crítica, usar `Chromium` no lugar de Firefox (Playwright suporta extensões no Chromium).
Mas verificar se o PJe é compatível com Chromium antes de trocar.

---

## Timeline de riscos por fase

| Fase | Riscos Ativos |
|---|---|
| 1 — Fix/playwright_core | R1 (setup Firefox) |
| 2 — Fix/utils + browser | R2 (mat-select timing) |
| 3 — session bridge | R5 (estrutura cookies) |
| 4 — atos/ | R2, R4 (Angular zone) |
| 5 — PEC PoC | R2, R3 (CKEditor), R4, R5, R10 (sessão expira) |
| 6 — Prazo + Mandado | R2, R6 (threads) |
| SISB (futuro) | R6 (ThreadPoolExecutor), R7 (print), R10 |
