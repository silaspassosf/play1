# 09 — Padrões Angular/PJe no Playwright

**Este é o arquivo de referência mais consultado durante a implementação.**
Contém receitas prontas para os padrões mais frequentes do PJe.

---

## 1. Angular Material — mat-select (dropdown)

### Padrão básico
```python
# Abrir e selecionar opção
page.locator('mat-select[formcontrolname="destinos"]').click()
page.get_by_role('option', name='Análise').click()
```

### Com filtro parcial de texto (sem exato)
```python
page.locator('mat-select[formcontrolname="destinos"]').click()
page.locator('mat-option').filter(has_text='Exec').first.click()
```

### Aguardar opções carregar antes de clicar
```python
page.locator('mat-select[formcontrolname="destinos"]').click()
# Aguardar overlay do CDK aparecer
page.locator('div.cdk-overlay-pane mat-option').first.wait_for(state='visible', timeout=5000)
page.get_by_role('option', name='Execução').click()
```

### Dropdown com muitas opções (scrollar para encontrar)
```python
page.locator('mat-select').click()
# Playwright localiza a opção mesmo fora do viewport
page.locator('mat-option').filter(has_text='Texto longo da opção').click()
```

### Verificar valor selecionado
```python
valor = page.locator('mat-select[formcontrolname="destinos"] span.mat-select-value-text').text_content()
assert 'Análise' in valor
```

---

## 2. Angular Material — mat-input (campos de texto)

### Preencher campo (substitui preencher_campo do core.py)
```python
# fill() já limpa o campo, dispara input/change para Angular
page.locator('input[formcontrolname="campo"]').fill('valor')

# Com append (sem limpar)
page.locator('input[formcontrolname="campo"]').press_sequentially('valor')
```

### Campos com aria-label
```python
page.get_by_label('Número do processo').fill('1234567-89.2024.5.02.0001')
```

### Campos com placeholder
```python
page.get_by_placeholder('Digite o número do processo').fill('1234567-89.2024.5.02.0001')
```

### Disparar eventos manualmente (quando Angular não detecta automaticamente)
```python
# Raramente necessário — Playwright normalmente lida bem com isso
campo = page.locator('input[formcontrolname="campo"]')
campo.fill('valor')
campo.dispatch_event('input')
campo.dispatch_event('change')
campo.dispatch_event('blur')
```

---

## 3. Angular Material — mat-checkbox

```python
# Clicar no checkbox (marca/desmarca)
page.locator('mat-checkbox[formcontrolname="ativo"]').click()

# Verificar se está marcado
esta_marcado = page.locator('mat-checkbox').locator('input[type="checkbox"]').is_checked()

# Garantir que está marcado (sem toggle indesejado)
checkbox_input = page.locator('mat-checkbox').locator('input[type="checkbox"]')
if not checkbox_input.is_checked():
    page.locator('mat-checkbox').click()
```

---

## 4. Angular Material — mat-datepicker

```python
# Preencher diretamente no input
page.locator('input[matdatepicker="picker"]').fill('15/01/2025')
page.keyboard.press('Escape')  # fechar picker se abriu

# Alternativa: usar o picker visual
page.locator('button[matdatepickertoggle]').click()
page.get_by_role('gridcell', name='15').click()
```

---

## 5. Angular Material — mat-spinner / loading

```python
# Aguardar spinner desaparecer antes de continuar
page.locator('mat-spinner').wait_for(state='hidden', timeout=30000)

# Alternativa: aguardar elemento de resultado aparecer
page.locator('mat-table').wait_for(state='visible', timeout=30000)
```

---

## 6. Estabilização Angular (substitui aguardar_renderizacao_nativa)

```python
# Aguardar ngZone estabilizar (mais confiável que networkidle para Angular)
def aguardar_angular(page, timeout_ms=10000):
    """Aguarda Angular zone estabilizar completamente."""
    try:
        page.wait_for_function(
            "() => window.getAllAngularTestabilities?.()?.every(t => t.isStable()) ?? true",
            timeout=timeout_ms
        )
        return True
    except Exception:
        return False

# Uso
aguardar_angular(page)

# Alternativa mais simples (funciona na maioria dos casos)
page.wait_for_load_state('networkidle', timeout=10000)
```

---

## 7. Navegação no PJe

### Abrir processo pelo ID
```python
from Fix.variaveis import url_processo_detalhe
url = url_processo_detalhe(id_processo)
page.goto(url)
page.wait_for_load_state('networkidle')
```

### Aguardar router Angular completar
```python
# Após page.goto() ou clique que muda rota:
page.wait_for_url('**/processo/**', timeout=15000)
# ou aguardar elemento da nova tela
page.locator('pje-detalhe-processo').wait_for(state='visible', timeout=15000)
```

### Voltar para lista de tarefas
```python
page.go_back()
page.wait_for_load_state('networkidle')
```

---

## 8. Abas (janelas)

### Abrir link em nova aba e trabalhar nela
```python
with page.context.expect_page() as new_page_info:
    page.locator('button#abrir-tarefa').click()
nova_aba = new_page_info.value
nova_aba.wait_for_load_state()

# Trabalhar na nova aba
nova_aba.locator('button.salvar').click()

# Fechar e voltar
nova_aba.close()
# page ainda aponta para a aba original
```

### Fechar todas as abas extras
```python
for p in page.context.pages[1:]:
    p.close()
```

---

## 9. CKEditor

### Inserir HTML
```python
def inserir_html_ckeditor(page, html: str) -> bool:
    try:
        # Aguardar CKEditor inicializar
        page.wait_for_function(
            "() => typeof CKEDITOR !== 'undefined' && Object.keys(CKEDITOR.instances || {}).length > 0",
            timeout=10000
        )
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
        logger.error("inserir_html_ckeditor: %s", e)
        return False
```

### Coletar conteúdo do editor
```python
conteudo = page.evaluate("""
    () => {
        const ids = Object.keys(CKEDITOR.instances || {});
        return ids.length > 0 ? CKEDITOR.instances[ids[0]].getData() : null;
    }
""")
```

---

## 10. Tabelas (mat-table)

### Aguardar tabela carregar com dados
```python
page.locator('mat-table').wait_for(state='visible', timeout=15000)
# Aguardar pelo menos 1 linha
page.locator('mat-row').first.wait_for(state='visible', timeout=10000)
```

### Iterar sobre linhas
```python
linhas = page.locator('mat-row').all()
for linha in linhas:
    texto = linha.locator('mat-cell').first.text_content()
    print(texto)
```

### Clicar em botão dentro de uma linha específica
```python
# Linha que contém "12345"
page.locator('mat-row').filter(has_text='12345').locator('button').click()
```

---

## 11. Filtros e buscas

### Campo de busca com debounce Angular
```python
# Playwright respeita debounce automaticamente se usar fill()
page.locator('input.search-input').fill('texto a buscar')
# Aguardar resultados carregarem
page.locator('mat-row').first.wait_for(state='visible', timeout=10000)
```

### Aplicar filtro de 100 itens por página (aplicar_filtro_100 do core.py)
```python
def aplicar_filtro_100(page) -> bool:
    """Equivale a aplicar_filtro_100 do Fix/core.py."""
    try:
        # Procurar mat-select de itens por página
        page.locator('mat-select[aria-label*="Items per page"], mat-select[aria-label*="itens"]').click()
        page.get_by_role('option', name='100').click()
        page.locator('mat-spinner').wait_for(state='hidden', timeout=15000)
        return True
    except Exception:
        return False
```

---

## 12. Cookies e autenticação

### Extrair cookies após login para requests.Session
```python
from Fix.variaveis import session_from_page, PjeApiClient

sess, trt = session_from_page(page)
client = PjeApiClient(sess, trt)

# Agora client funciona igual ao modo Selenium
dados = client.timeline(id_processo)
```

### Salvar cookies para retomar sessão
```python
import json

# Salvar
cookies = page.context.cookies()
with open('cookies_sessao.json', 'w') as f:
    json.dump(cookies, f)

# Restaurar em nova sessão
with open('cookies_sessao.json') as f:
    cookies = json.load(f)
page.context.add_cookies(cookies)
```

---

## 13. Overlays e modais

### Aguardar modal abrir
```python
page.locator('mat-dialog-container').wait_for(state='visible', timeout=10000)
```

### Fechar modal com ESC
```python
page.keyboard.press('Escape')
page.locator('mat-dialog-container').wait_for(state='hidden', timeout=5000)
```

### Confirmar/cancelar dialog
```python
# Confirmar
page.get_by_role('button', name='Confirmar').click()
# Cancelar
page.get_by_role('button', name='Cancelar').click()
```

### Aguardar overlay CDK fechar
```python
page.locator('.cdk-overlay-backdrop').wait_for(state='hidden', timeout=5000)
```

---

## 14. Tratamento de erros comum no PJe

### Acesso negado
```python
def verificar_acesso_negado(page) -> bool:
    """Detecta se PJe exibiu tela de acesso negado."""
    return (
        'Acesso negado' in page.title() or
        page.locator('text=Acesso negado').is_visible() or
        page.locator('text=403').is_visible()
    )
```

### Sessão expirada
```python
def sessao_expirada(page) -> bool:
    """Detecta se sessão PJe expirou."""
    return (
        '/login' in page.url or
        page.locator('input[type="password"]').is_visible()
    )
```

### Re-login automático
```python
if sessao_expirada(page):
    from Fix.utils import login_cpf
    login_cpf(page, cpf=CPF, senha=SENHA)
```
