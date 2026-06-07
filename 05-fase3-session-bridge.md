# 05 — Fase 3: Session Bridge (`Fix/variaveis.py`)

**Objetivo:** Adicionar `session_from_page()` ao `Fix/variaveis.py`.
`PjeApiClient` e todas as outras funções ficam **idênticas** — elas usam `requests.Session` puro.

**Dependência:** Fase 2 concluída.

---

## Por que esta fase é simples?

`Fix/variaveis.py` **não importa Selenium** em nenhuma linha.
A única função com acoplamento ao browser é `session_from_driver(driver)`,
que extrai cookies do Selenium para criar um `requests.Session`.

No Playwright, cookies ficam em `page.context.cookies()` com a mesma estrutura.
A mudança é literalmente 8 linhas.

---

## Task 3.1 — Adicionar `session_from_page` em `Fix/variaveis.py`

**Description:** Adicionar nova função `session_from_page` ao lado de `session_from_driver`.
Ambas coexistem. Código Selenium usa `session_from_driver`. Código migrado usa `session_from_page`.

**Onde inserir:** Logo após a definição de `session_from_driver` (linha ~385 do original).

**Implementação:**
```python
def session_from_page(page, grau: int = 1) -> Tuple[requests.Session, str]:
    """Cria um requests.Session a partir de uma Playwright Page.
    
    Equivalente a session_from_driver mas para Playwright.
    Retorna (session, trt_host) — mesma interface.
    
    Uso:
        from Fix.variaveis import session_from_page, PjeApiClient
        sess, trt = session_from_page(page)
        client = PjeApiClient(sess, trt)
    """
    sess = requests.Session()
    try:
        cookies = page.context.cookies()
        for c in cookies:
            sess.cookies.set(c['name'], c['value'])
        parsed = urlparse(page.url)
        trt_host = parsed.netloc
    except Exception:
        raise
    sess.headers.update({
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'X-Grau-Instancia': str(grau)
    })
    return sess, trt_host
```

**Acceptance criteria:**
- [ ] `session_from_page` exportada de `Fix.variaveis`
- [ ] `session_from_driver` intocada (Selenium continua funcionando)
- [ ] `PjeApiClient` intocada
- [ ] `session_from_page(page)` retorna `(requests.Session, str)` com cookies da sessão PJe

**Verification:**
```python
# Após login Playwright:
py -c "
from Fix.variaveis import session_from_page, session_from_driver
print('session_from_page importada OK')
print('session_from_driver ainda presente OK')
"
```

**Files:** `Fix/variaveis.py` (adição mínima de ~15 linhas)

**Scope:** XS

---

## Task 3.2 — Atualizar todos os módulos migrados para usar `session_from_page`

**Description:** Em cada arquivo migrado (PEC, Prazo, Mandado) onde existe:
```python
from Fix.variaveis import session_from_driver
sess, trt = session_from_driver(driver)
```
Trocar para:
```python
from Fix.variaveis import session_from_page
sess, trt = session_from_page(page)
```

**Esta task ocorre em paralelo com as Fases 4, 5 e 6 conforme os módulos são migrados.**

**Lista de arquivos afetados:**
- `PEC/runtime_pec.py` — `session_from_driver` chamado em `PECAPIClient.fetch_atividades_vencidas`
- `PEC/orquestrador.py` — verificar
- `Prazo/loop_orquestrador.py` — `session_from_driver` em `PjeApiClient` setup
- `Mandado/entrada_api.py` — verificar
- `SISB/core.py` — verificar

**Acceptance criteria para cada arquivo:**
- [ ] `from Fix.variaveis import session_from_page` no topo
- [ ] `session_from_driver` removido das chamadas (não do import de `variaveis.py`)
- [ ] `sess, trt = session_from_page(page)` no lugar de `session_from_driver(driver)`

**Dependencies:** Task 3.1

**Scope:** XS por arquivo

---

## Impacto na arquitetura de `PjeApiClient`

`PjeApiClient.__init__(session, trt_host)` — **não muda**.
A classe recebe um `requests.Session` pronto, indiferente se veio de Selenium ou Playwright.

```python
# Selenium (antes)
sess, trt = session_from_driver(driver)
client = PjeApiClient(sess, trt)

# Playwright (depois)
sess, trt = session_from_page(page)
client = PjeApiClient(sess, trt)  # idêntico daqui para frente
```

Todo o código que usa `client.timeline()`, `client.atividades_gigs()`, etc. **permanece idêntico**.

---

## Checkpoint Fase 3

```bash
py -c "
from Fix.variaveis import session_from_page, session_from_driver, PjeApiClient
print('session_from_page:', session_from_page)
print('session_from_driver:', session_from_driver)
print('PjeApiClient:', PjeApiClient)
print('Fase 3 OK')
"
```

- [ ] Ambas as funções de sessão exportadas
- [ ] `PjeApiClient` intocada
- [ ] Zero mudanças na lógica de negócio dos módulos ainda não migrados
