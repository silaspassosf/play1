# 10 — Setup do Ambiente Playwright

**Objetivo:** Preparar o ambiente em `d:\Play` para iniciar a migração Selenium → Playwright.
Este documento é o passo a passo executável.

---

## Passo 1: Garantir que o repo está versionado

```powershell
cd d:\Play

# Se ainda não for um repo git
git init
git add .
git commit -m "chore: estado atual pré-migração Playwright"

# Ou criar branch de migração
git checkout -b feat/playwright-migration
```

---

## Passo 2: Instalar Playwright

```powershell
# No ambiente d:\Play
pip install playwright

# Baixar o Firefox do Playwright (não usa geckodriver)
playwright install firefox

# Verificar instalação
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
```

**Nota:** O Firefox do Playwright é baixado em `%LOCALAPPDATA%\ms-playwright\`.
O `geckodriver.exe` em `Fix/geckodriver.exe` **não é mais necessário** para o Playwright,
mas deve ser mantido até que toda a migração esteja completa (código Selenium ainda roda).

---

## Passo 3: Criar `requirements_play.txt`

```powershell
# Na raiz d:\Play
@"
# Playwright migration
playwright>=1.40.0

# Mantidos do projeto original
requests>=2.31.0
pdfplumber>=0.9.0
openpyxl>=3.1.0
python-dotenv>=1.0.0
"@ | Set-Content requirements_play.txt

pip install -r requirements_play.txt
```

---

## Passo 4: Criar `Fix/playwright_core.py` (arquivo inicial)

```powershell
# Criar o arquivo com o header correto
@"
"""
Fix/playwright_core.py — Núcleo Playwright (substitui Fix/core.py)

Migração incremental de Selenium para Playwright.
Este arquivo cresce a cada fase conforme as funções são portadas.

Referência: Fix/core.py (Selenium original — permanece funcional)
"""
from playwright.sync_api import Page, Locator, sync_playwright, TimeoutError as PlaywrightTimeoutError
from Fix.log import logger
import os, re, time, datetime, json

# Reexportar funções que não dependem de Selenium (mantidas idênticas)
from Fix.core import (
    medir_tempo,
    ErroCollector,
    coletor_erros,
    js_base,
    com_retry,
)
"@ | Set-Content Fix/playwright_core.py
```

**IMPORTANTE:** A linha `from Fix.core import (...)` no `playwright_core.py` reexporta
as funções que não precisam mudar. Isso garante que código que importa `from Fix.playwright_core import com_retry`
funcione desde o início, mesmo antes de `playwright_core.py` estar completo.

---

## Passo 5: Smoke test de verificação

Criar `smoke_test_play.py` na raiz para validar o estado atual da migração:

```python
# smoke_test_play.py — executar com: py smoke_test_play.py
"""Smoke test do estado atual da migração Playwright."""

resultados = {}

def testar(nome, fn):
    try:
        fn()
        resultados[nome] = '✓'
    except Exception as e:
        resultados[nome] = f'✗ {str(e)[:60]}'

# Playwright instalado
testar('playwright instalado', lambda: __import__('playwright.sync_api', fromlist=['sync_playwright']))

# Fase 1
testar('playwright_core import', lambda: __import__('Fix.playwright_core', fromlist=['criar_driver_PC']))

# Fase 2
testar('browser_suporte migrado', lambda: exec("from Fix.browser_suporte import validar_conexao_page"))
testar('utils login_cpf', lambda: exec("from Fix.utils import login_cpf"))

# Fase 3
testar('session_from_page', lambda: exec("from Fix.variaveis import session_from_page"))

# Fase 4
testar('atos.judicial', lambda: exec("from atos.judicial import ato_judicial"))

# Fase 5
testar('PEC migrado', lambda: exec("from PEC.regras import determinar_acoes_por_observacao"))

# Fase 6
testar('Prazo migrado', lambda: exec("from Prazo.loop_orquestrador import loop_prazo"))
testar('Mandado migrado', lambda: exec("from Mandado.core import main"))

# Resultado
print("\n=== Status da Migração ===")
fases_ok = sum(1 for s in resultados.values() if s == '✓')
for nome, status in resultados.items():
    print(f"  {status} {nome}")

print(f"\n{fases_ok}/{len(resultados)} verificações passando")
if fases_ok == len(resultados):
    print("MIGRAÇÃO COMPLETA!")
```

```powershell
# Executar a qualquer momento para ver o progresso
py smoke_test_play.py
```

---

## Passo 6: `.gitignore` e exclusões

```powershell
# Adicionar ao .gitignore do novo repo
@"
# Playwright
playwright-report/
test-results/
__pycache__/
*.pyc

# Sessões e cookies
cookies_sessoes/
*.json.bak
"@ | Add-Content .gitignore
```

---

## Estrutura final do d:\Play após setup

```
d:\Play\
├── Fix/
│   ├── playwright_core.py    ← CRIADO no passo 4
│   ├── core.py               ← ORIGINAL Selenium (referência, não editar)
│   ├── selenium_base/        ← operações base Selenium
│   ├── browser_suporte.py    ← será sobrescrito na Fase 2
│   ├── utils.py              ← será sobrescrito na Fase 2
│   ├── variaveis.py          ← receberá session_from_page na Fase 3
│   └── ...
├── atos/                     ← será migrado na Fase 4
├── PEC/                      ← será migrado na Fase 5 (PoC)
├── Prazo/                    ← será migrado na Fase 6
├── Mandado/                  ← será migrado na Fase 6
├── SISB/                     ← fora do escopo inicial
├── Peticao/                  ← fora do escopo inicial
├── Triagem/                  ← fora do escopo inicial
├── bianca/                   ← standalone (migrar separadamente)
├── smoke_test_play.py        ← CRIADO no passo 5
├── requirements_play.txt     ← CRIADO no passo 3
├── README.md
└── 00-estrategia.md ... 11-riscos.md
```

---

## Comandos de verificação frequentes

```powershell
# Verificar quantos imports Selenium ainda restam por módulo
Select-String -Path "Fix\*.py" -Pattern "from selenium" | Select-Object Filename, LineNumber
Select-String -Path "atos\*.py" -Pattern "from selenium" | Select-Object Filename, LineNumber
Select-String -Path "PEC\*.py" -Pattern "from selenium" | Select-Object Filename, LineNumber
Select-String -Path "Prazo\*.py" -Pattern "from selenium" | Select-Object Filename, LineNumber
Select-String -Path "Mandado\*.py" -Pattern "from selenium" | Select-Object Filename, LineNumber

# Total de imports Selenium restantes
(Select-String -Recurse -Path "*.py" -Pattern "from selenium").Count

# Smoke test atual
py smoke_test_play.py
```
