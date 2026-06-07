# /play — Automação PJe (Selenium → Playwright)

Projeto de automação do sistema PJe (Poder Judiciário Eletrônico) para o TRT2.
Atualmente em **Selenium + Firefox**, com plano de migração para **Playwright**.

## Estrutura atual do projeto

```
d:\Play\
├── Fix/                  ← Core de automação Selenium (core.py, utils.py, browser_suporte.py, etc.)
│   ├── selenium_base/    ← Operações base: clique, espera, retry
│   ├── drivers/          ← Gerenciamento de lifecycle do WebDriver
│   └── progress/         ← Monitoramento de progresso
├── atos/                 ← Ações judiciais (judicial, movimentos, comunicação, anexos)
├── PEC/                  ← Fluxo PEC — processamento de petições eletrônicas
│   └── anexos/           ← Extração e formatação de anexos
├── Prazo/                ← Processamento de prazos (loop + P2B gateway)
├── Mandado/              ← Fluxo de mandados (Argos + Outros)
├── SISB/                 ← SISBAJUD — ordens de bloqueio/transferência
│   ├── Core/             ← Driver, sessão, utils JS/dados
│   └── processamento/    ← Minutas, ordens, séries, relatórios, validação
├── Peticao/              ← Processamento de petições (classificação + ações)
│   ├── api/              ← Cliente API PJe para petições
│   ├── atos/             ← Wrappers de atos específicos de petição
│   ├── core/             ← Extração, utils, log
│   └── helpers/          ← Helpers de despacho e assistente
├── Triagem/              ← Triagem de petição inicial (B1–B15)
├── bianca/               ← Módulo standalone: Triagem + DOM (Selenium isolado)
└── docs/ (raiz)          ← Plano de migração Playwright (arquivos 00 a 11)
```

## Documentação

### Estratégia de migração Playwright (docs raiz)

| Arquivo | Conteúdo |
|---|---|
| `00-estrategia.md` | Filosofia, regras de ouro, estratégia da migração |
| `01-mapa-dependencias.md` | Grafo de dependências Selenium por módulo |
| `02-equivalencias-api.md` | Tabela completa Selenium → Playwright |
| `03-fase1-fix-core.md` | **Fase 1** — Criar `Fix/playwright_core.py` |
| `04-fase2-fix-utils-browser.md` | **Fase 2** — `Fix/browser_suporte.py` + login |
| `05-fase3-session-bridge.md` | **Fase 3** — `session_from_driver` → `session_from_page` |
| `06-fase4-atos.md` | **Fase 4** — módulo `atos/` |
| `07-fase5-pec-poc.md` | **Fase 5** — `PEC/` como PoC |
| `08-fase6-prazo-mandado.md` | **Fase 6** — `Prazo/` + `Mandado/` |
| `09-padroes-angular-pje.md` | Receitas: Angular Material, CKEditor, abas, cookies |
| `10-setup-novo-repo.md` | Setup do ambiente Playwright |
| `11-riscos.md` | Riscos e estratégias de mitigação |

### Documentação por módulo

| Módulo | Documentos |
|---|---|
| **Mandado** | `README.md`, `CORRECOES_IMPLEMENTADAS.md`, `RESUMO_CORRECOES.md`, `TROUBLESHOOTING.md`, `RELATORIO_MUDANCAS.md`, `INVESTIGACAO_PATCHES_MANDADO.md` |
| **Prazo** | `README.md`, `CORRECAO_SINCRONIZACAO_CICLOS.md` |
| **bianca** | `README.md`, `ARQUITETURA.md`, `plano.md`, `REFATORACAO.md` |
| **PEC** | `ANALISE_REFATORACAO_MODULAR.md`, `LOOP_PERICIAS_ANALISE.md` |
| **SISB** | `RELATORIO_REFATORACAO_FASE2.md`, `RELATORIO_REFATORACAO_HELPERS.md` |
| **Fix** | `PADRAO_LIQ_API.md` |
| **Peticao** | `petall.md` (mapeamento de funções) |
| **Triagem** | `trindex.md` (índice da triagem), `PLANO_INDEPENDENCIA.md`, `tr.md` (prompt IA), `triagem.md` (prompt IA) |

## Regra fundamental da migração

O código Selenium em `Fix/core.py` e demais módulos **permanece funcional** durante toda a migração.
A migração para Playwright é feita criando `Fix/playwright_core.py` com a mesma API pública,
permitindo que os módulos troquem o import sem mudar a lógica de negócio.

## Estado atual da migração

- [x] Módulos existentes modularizados (Mandado, Prazo, SISB, Triagem, Peticao, bianca)
- [x] `Fix/core.py` — core Selenium funcional (~2900 linhas)
- [x] `Fix/selenium_base/` — operações base extraídas (clique, espera, retry)
- [ ] Fase 1 — `Fix/playwright_core.py` (a criar)
- [ ] Fase 2 — `Fix/browser_suporte.py` + login migrados
- [ ] Fase 3 — `session_from_page` adicionado em `Fix/variaveis.py`
- [ ] Fase 4 — `atos/` migrado para Playwright
- [ ] Fase 5 — PEC rodando em Playwright (PoC)
- [ ] Fase 6 — Prazo + Mandado migrados
