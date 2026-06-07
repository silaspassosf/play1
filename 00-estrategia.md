# 00 — Estratégia da Migração

## Premissa central

O código Selenium atual em `d:\Play` **permanece funcional** durante toda a migração.
A migração para Playwright é feita **no mesmo repo**, criando arquivos Playwright lado a lado
com os equivalentes Selenium (`Fix/playwright_core.py` ao lado de `Fix/core.py`),
substituindo imports incrementalmente sem quebrar o que já funciona.

## Por que não refatorar a estrutura?

A lógica de negócio (10+ módulos) é o bem real. A camada Selenium é apenas o motor.
Trocar o motor sem mexer na carroceria é a menor superfície de risco possível.
Refatorar a estrutura junto com a migração multiplica o risco sem agregar valor.

**Nota:** A estrutura já foi modularizada (Mandado, Prazo, SISB, Triagem, Peticao, bianca).
A migração Playwright preserva essa modularização, trocando apenas a camada de browser.

---

## Regras de ouro (invioláveis)

### RG-1: Substituição por sobrescrita
Em cada arquivo migrado, remove-se os imports Selenium e insere-se os imports Playwright.
A assinatura das funções públicas é preservada ao máximo.
`WebDriver driver` → `Page page` em type hints. Nada mais muda na interface.

### RG-2: Ordem de dependência
Nunca migrar um módulo antes de suas dependências.
Ordem obrigatória: `Fix/core.py` → `Fix/browser_suporte.py` → `Fix/variaveis.py` → `Fix/utils.py` → `atos/` → módulos de negócio.

### RG-3: Um arquivo de cada vez
Nenhuma fase migra mais de um arquivo por sessão de trabalho.
Após cada arquivo: rodar o smoke test do arquivo (`py -c "from Fix.playwright_core import criar_driver_PC"`).

### RG-4: Sem dependência cruzada
Durante a migração, não existem arquivos parcialmente Selenium + parcialmente Playwright.
Um arquivo é 100% Selenium ou 100% Playwright. Nada no meio.

### RG-5: `Fix/variaveis.py` não muda (quase)
`PjeApiClient` usa `requests.Session` puro — sem Selenium, sem Playwright.
A única mudança: adicionar `session_from_page(page)` ao lado de `session_from_driver(driver)`.
Ambos coexistem.

---

## Substituição de tipos central

| Conceito | Selenium | Playwright |
|---|---|---|
| Motor do browser | `WebDriver` | `Page` |
| Elemento | `WebElement` | `Locator` |
| Gerenciar instâncias | `webdriver.Firefox(options)` | `playwright.firefox.launch()` + `context.new_page()` |
| Tipo de retorno dos drivers | `WebDriver` | `Page` |
| Argumento de todas as funções | `driver: WebDriver` | `page: Page` |

Essa substituição de tipo é a espinha dorsal. Toda outra mudança é consequência dela.

---

## Estrutura do repo (atual + planejado)

```
d:\Play\                        ← repo de trabalho
├── Fix/
│   ├── core.py                 ← Selenium original (~2900 linhas) — FUNCIONAL
│   ├── playwright_core.py      ← NOVO (Fase 1): mesma API, implementação Playwright
│   ├── browser_suporte.py      ← será sobrescrito na Fase 2
│   ├── utils.py                ← será sobrescrito na Fase 2 (login_cpf, CKEditor)
│   ├── variaveis.py            ← session_from_page adicionada na Fase 3
│   ├── selenium_base/          ← operações base Selenium (clique, espera, retry)
│   ├── drivers/                ← lifecycle do WebDriver
│   ├── progress/               ← monitoramento de progresso
│   └── ...
├── atos/                       ← será migrado na Fase 4
├── PEC/                        ← PoC na Fase 5
├── Prazo/                      ← migrado na Fase 6
├── Mandado/                    ← migrado na Fase 6
├── SISB/                       ← fora do escopo inicial (migrar depois)
├── Peticao/                    ← fora do escopo inicial
├── Triagem/                    ← fora do escopo inicial
├── bianca/                     ← standalone Selenium (migrar separadamente)
├── 00-estrategia.md .. 11-riscos.md  ← documentação do plano
└── README.md
```

---

## Instalação do Playwright

```bash
# No ambiente atual (d:\Play)
pip install playwright

# Baixar binário Firefox do Playwright (não usa geckodriver.exe)
playwright install firefox

# Verificar
python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

**Atenção:** `playwright install firefox` baixa o Firefox próprio do Playwright
em `%LOCALAPPDATA%\ms-playwright\`. O `Firefox Developer Edition` e o
`Fix/geckodriver.exe` continuam funcionando para o código Selenium
durante a transição.

---

## Decisões de arquitetura

### A: Python sync_api, não async
O projeto atual é 100% síncrono. A API `playwright.sync_api` preserva isso.
Migrar para async junto com Playwright triplicaria a dificuldade — não fazer.

### B: Firefox como browser alvo
O PJe foi homologado e testado no Firefox. Playwright suporta Firefox nativamente.
`playwright.firefox.launch()` é o ponto de entrada.

### C: Sem `playwright.Page` como tipo de retorno explícito nos wrappers
As funções de negócio recebem `page` como argumento (duck typing).
Evita import circular e facilita testes com mocks.

### D: Manter `geckodriver.exe` no repo por compatibilidade
O `Fix/geckodriver.exe` permanece no lugar até que 100% dos fluxos estejam migrados.
Após a migração completa, remover.

### E: `playwright_core.py` como drop-in replacement
Criar `Fix/playwright_core.py` com a mesma API pública de `Fix/core.py`.
Os módulos migrados trocam `from Fix.core import` por `from Fix.playwright_core import`.
`Fix/core.py` original continua funcionando para módulos ainda não migrados.

---

## Cronograma estimado de esforço

| Fase | Arquivo alvo | Complexidade | Estimativa |
|---|---|---|---|
| 1 | `Fix/playwright_core.py` | Alta (2915 linhas de referência) | 3–5 sessões |
| 2 | `Fix/browser_suporte.py` | Média | 1–2 sessões |
| 3 | `Fix/variaveis.py` (adição) | Baixa | 0.5 sessão |
| 4 | `atos/` (6 arquivos) | Média-Alta | 3–4 sessões |
| 5 | `PEC/` (PoC) | Alta | 3–4 sessões |
| 6 | `Prazo/` + `Mandado/` | Alta | 4–6 sessões |

Total estimado: 15–22 sessões de trabalho focado.

---

## Critério de "fase concluída"

Uma fase está concluída quando:
1. O(s) arquivo(s) alvo não contém nenhum `import selenium`
2. O smoke test passa: `py -c "from <modulo> import <funcao_principal>"`
3. O fluxo de negócio end-to-end roda sem erro no ambiente real
