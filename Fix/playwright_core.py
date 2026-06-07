"""
Fix/playwright_core.py — Núcleo Playwright (substitui Fix/core.py)

Migração incremental de Selenium para Playwright.
Expõe a MESMA API pública de Fix/core.py com implementação Playwright.

Referência: Fix/core.py (Selenium original — permanece funcional durante a migração)
"""

from playwright.sync_api import Page, Locator, sync_playwright, TimeoutError as PlaywrightTimeoutError
from Fix.log import logger
import os, re, time, datetime, json, unicodedata

# ============================================================
# Re-exports de Fix/core.py (funções SEM dependência Selenium)
# ============================================================

from Fix.core import (
    medir_tempo,
    ErroCollector,
    coletor_erros,
    js_base,
    com_retry,
    _extrair_jwt_exp,
    _montar_options_pc,
    _montar_options_vt,
    _aplicar_preferencias,
    smart_sleep,
    sleep,
    GECKODRIVER_PATH,
)

# Variáveis de compatibilidade
DEBUG = os.getenv('PJEPLUS_DEBUG', '0').lower() in ('1', 'true', 'on')
TIME_ENABLED = True


# ============================================================
# CRIAÇÃO DE BROWSER / PAGE
# ============================================================

def criar_driver_PC(headless: bool = False) -> Page:
    """Cria Page Playwright equivalente ao criar_driver_PC Selenium.

    Firefox com user-agent override e viewport 1920x1080.
    Retorna Page. Para fechar: finalizar_driver(page).
    """
    try:
        pw = sync_playwright().start()
        browser = pw.firefox.launch(
            headless=headless,
            firefox_user_prefs={
                "dom.webdriver.enabled": False,
                "useAutomationExtension": False,
                "general.useragent.override": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) "
                    "Gecko/20100101 Firefox/91.0"
                ),
                "dom.webnotifications.enabled": False,
                "dom.min_background_timeout_value": 0,
                "dom.timeout.throttling_delay": 0,
                "dom.timeout.budget_throttling_max_delay": 0,
                "media.volume_scale": "0.0",
            }
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) "
                "Gecko/20100101 Firefox/91.0"
            ),
        )
        page = context.new_page()
        page._pje_playwright = pw
        logger.info("page criada: PC (Playwright)")
        return page
    except Exception as e:
        logger.error("ERRO em criar_driver_PC: %s: %s", type(e).__name__, e)
        return None


def criar_driver_VT(headless: bool = False) -> Page:
    """Cria Page Playwright equivalente ao criar_driver_VT Selenium.

    Versão simplificada — sem perfis Firefox (Playwright gerencia isolamento).
    """
    try:
        pw = sync_playwright().start()
        browser = pw.firefox.launch(
            headless=headless,
            firefox_user_prefs={
                "dom.webdriver.enabled": False,
                "useAutomationExtension": False,
                "extensions.update.enabled": False,
                "dom.min_background_timeout_value": 0,
                "dom.timeout.throttling_delay": 0,
                "dom.timeout.budget_throttling_max_delay": 0,
            }
        )
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        page._pje_playwright = pw
        logger.info("page criada: VT (Playwright)")
        return page
    except Exception as e:
        logger.error("ERRO em criar_driver_VT: %s: %s", type(e).__name__, e)
        return None


def criar_driver_notebook(headless: bool = False) -> Page:
    """Cria Page Playwright equivalente ao criar_driver_notebook Selenium."""
    try:
        pw = sync_playwright().start()
        browser = pw.firefox.launch(
            headless=headless,
            firefox_user_prefs={
                "dom.min_background_timeout_value": 0,
                "dom.timeout.throttling_delay": 0,
                "dom.timeout.budget_throttling_max_delay": 0,
            }
        )
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        page._pje_playwright = pw
        logger.info("page criada: NOTEBOOK (Playwright)")
        return page
    except Exception as e:
        logger.error("ERRO em criar_driver_notebook: %s: %s", type(e).__name__, e)
        return None


def criar_driver_sisb_pc(headless: bool = False) -> Page:
    """Cria Page Playwright para SISBAJUD PC."""
    return criar_driver_PC(headless=headless)


def criar_driver_sisb_notebook(headless: bool = False) -> Page:
    """Cria Page Playwright para SISBAJUD Notebook."""
    return criar_driver_notebook(headless=headless)


# Aliases lowercase para compatibilidade
criar_driver_pc = criar_driver_PC
criar_driver_vt = criar_driver_VT


def finalizar_driver(page: Page, log: bool = True) -> None:
    """Encerra browser e playwright instance. Equivale a finalizar_driver do core.py."""
    try:
        browser = page.context.browser if not page.is_closed() else None
        if browser:
            browser.close()
        pw = getattr(page, '_pje_playwright', None)
        if pw:
            pw.stop()
        if log:
            logger.info("page finalizada")
    except Exception as e:
        if log:
            logger.warning("finalizar_driver: %s", e)


# ============================================================
# FUNÇÕES DE ESPERA (wait)
# ============================================================

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
            page.wait_for_function(
                f"() => {{ const el = document.querySelector('{seletor}'); "
                f"return el && !el.disabled; }}",
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
    by=None,  # ignorado — Playwright usa CSS por padrão
    log: bool = False,
):
    """Substitui esperar_elemento do core.py. Retorna Locator ou None.

    Playwright auto-wait: espera o elemento ser attached.
    Se texto fornecido, filtra pelo texto e aguarda visível.
    """
    timeout_ms = int(timeout * 1000)
    try:
        loc = page.locator(seletor)
        loc.wait_for(state='attached', timeout=timeout_ms)
        if texto:
            filtered = loc.filter(has_text=texto)
            filtered.wait_for(state='visible', timeout=timeout_ms)
            return filtered.first
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
def wait(page: Page, selector: str, timeout: float = 10, by=None) -> object:
    """Compatibilidade com código legado que usa wait()."""
    return esperar_elemento(page, selector, timeout=timeout)


def wait_for_visible(page: Page, selector: str, timeout: float = 10, by=None) -> object:
    """Compatibilidade com código legado."""
    return esperar_elemento(page, selector, timeout=timeout)


def wait_for_clickable(page: Page, selector: str, timeout: float = 10, by=None) -> object:
    """Compatibilidade com código legado."""
    return esperar_elemento(page, selector, timeout=timeout)


def wait_for_page_load(page: Page, timeout: float = 10) -> bool:
    """Aguarda page load completo."""
    try:
        page.wait_for_load_state('load', timeout=int(timeout * 1000))
        return True
    except PlaywrightTimeoutError:
        return False


def esperar_url_conter(page: Page, substring: str, timeout: float = 10) -> bool:
    """Aguarda URL conter substring."""
    try:
        page.wait_for_url(f'**{substring}**', timeout=int(timeout * 1000))
        return True
    except PlaywrightTimeoutError:
        return False


# ============================================================
# FUNÇÕES DE CLIQUE
# ============================================================

def aguardar_e_clicar(
    page: Page,
    seletor: str,
    log: bool = False,
    timeout: float = 10,
    by=None,  # ignorado — Playwright usa CSS
    usar_js: bool = True,  # ignorado — Playwright lida nativamente
    retornar_elemento: bool = False,
    debug=None,  # ignorado
    **kwargs  # absorve parâmetros legados
):
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


def safe_click(
    page: Page,
    selector_or_element,
    timeout: float = 10,
    by=None,
    log: bool = False,
) -> bool:
    """Compatibilidade com safe_click do core.py."""
    if isinstance(selector_or_element, str):
        return aguardar_e_clicar(page, selector_or_element, timeout=timeout, log=log)
    # É um Locator
    try:
        selector_or_element.click(timeout=int(timeout * 1000))
        return True
    except Exception as e:
        if log:
            logger.error("safe_click: %s", e)
        return False


def safe_click_no_scroll(page: Page, element, log: bool = False) -> bool:
    """Compatibilidade com safe_click_no_scroll do core.py."""
    try:
        element.click(force=True)
        return True
    except Exception as e:
        if log:
            logger.error("safe_click_no_scroll: %s", e)
        return False


# ============================================================
# FUNÇÕES DE PREENCHIMENTO
# ============================================================

def preencher_campo(
    page: Page,
    seletor: str,
    valor: str,
    trigger_events: bool = True,  # mantido na interface, não necessário em Playwright
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
            loc.fill(str(valor))
        else:
            loc.press_sequentially(str(valor))
        if log:
            logger.debug("preencher_campo: '%s' = '%s'", seletor, str(valor)[:50])
        return True
    except Exception as e:
        if log:
            logger.warning("preencher_campo: %s: %s", seletor, e)
        return False


def preencher_campos_prazo(
    page: Page,
    valor: int = 0,
    timeout: float = 10,
    log: bool = True,
) -> bool:
    """Preenche campos de prazo no PJe."""
    try:
        page.locator('input[formcontrolname="prazoDias"]').fill(str(valor))
        return True
    except Exception as e:
        if log:
            logger.warning("preencher_campos_prazo: %s", e)
        return False


def preencher_multiplos_campos(
    page: Page,
    campos_dict: dict,
    log: bool = False,
) -> bool:
    """Preenche múltiplos campos de uma vez."""
    sucesso = True
    for seletor, valor in campos_dict.items():
        if not preencher_campo(page, seletor, valor, log=log):
            sucesso = False
    return sucesso


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


# ============================================================
# BUSCA INTELIGENTE
# ============================================================

def buscar_seletor_robusto(
    page: Page,
    textos: list,
    contexto=None,
    timeout: float = 5,
    log: bool = False,
):
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
                input_id = label.get_attribute('for')
                if input_id:
                    return page.locator(f'#{input_id}').first
        except Exception:
            pass

    return None


def escolher_opcao_inteligente(
    page: Page,
    valor: str,
    estrategias_custom=None,
    debug: bool = False,
) -> bool:
    """DEPRECATED — use selecionar_opcao() ou aguardar_e_clicar().

    Versão Playwright simplificada para compatibilidade.
    """
    try:
        # Tentar por role
        btn = page.get_by_role('button', name=valor)
        if btn.count() > 0:
            btn.first.click()
            return True
        # Tentar por texto
        link = page.get_by_text(valor)
        if link.count() > 0:
            link.first.click()
            return True
        # Tentar por CSS direto
        page.locator(valor).first.click(timeout=3000)
        return True
    except Exception:
        return False


def encontrar_elemento_inteligente(
    page: Page,
    valor: str,
    estrategias_custom=None,
    debug: bool = False,
):
    """Versão Playwright de encontrar_elemento_inteligente. Retorna Locator ou None."""
    for loc in [
        page.get_by_label(valor),
        page.get_by_placeholder(valor),
        page.get_by_role('textbox', name=valor),
        page.locator(f'#{valor}'),
        page.locator(f'[name="{valor}"]'),
    ]:
        try:
            if loc.count() > 0:
                return loc.first
        except Exception:
            continue
    return None


# ============================================================
# FILTROS E TABELAS
# ============================================================

def aplicar_filtro_100(page: Page) -> bool:
    """Equivale a aplicar_filtro_100 do Fix/core.py — 100 itens por página."""
    try:
        page.locator(
            'mat-select[aria-label*="itens"], mat-select[aria-label*="Items"]'
        ).first.click()
        page.get_by_role('option', name='100').click()
        page.locator('mat-spinner').wait_for(state='hidden', timeout=15000)
        return True
    except Exception:
        return False


def filtro_fase(page: Page) -> bool:
    """Aplica filtro de fase no painel PJe."""
    try:
        page.locator('mat-select[formcontrolname="fpglobal_faseProcessual"]').first.click()
        page.wait_for_timeout(500)
        return True
    except Exception:
        return False


def filtrofases(
    page: Page,
    fases_alvo: list = None,
    tarefas_alvo=None,
    seletor_tarefa: str = 'Tarefa do processo',
) -> bool:
    """Aplica filtro de fases processuais — versão Playwright."""
    if fases_alvo is None:
        fases_alvo = ['liquidacao', 'execucao']
    try:
        for fase in fases_alvo:
            chip = page.locator('mat-chip').filter(has_text=fase)
            if chip.count() > 0:
                chip.first.click()
                page.wait_for_timeout(500)
        return True
    except Exception as e:
        logger.warning("filtrofases: %s", e)
        return False


def _aguardar_loader_painel(page: Page, timeout: float = 10) -> bool:
    """Aguarda loader do painel desaparecer."""
    try:
        page.locator('mat-spinner').wait_for(state='hidden', timeout=int(timeout * 1000))
        return True
    except PlaywrightTimeoutError:
        return False


# ============================================================
# COOKIES E SESSÃO
# ============================================================

def salvar_cookies_sessao(
    page: Page,
    caminho_arquivo: str = None,
    info_extra: dict = None,
) -> str:
    """Salva cookies da page Playwright para arquivo JSON."""
    try:
        cookies = page.context.cookies()
        if caminho_arquivo is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            caminho_arquivo = f'cookies_sessao_{timestamp}.json'
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump({
                'cookies': cookies,
                'info': info_extra or {},
                'timestamp': str(datetime.datetime.now()),
                'url': page.url,
            }, f, indent=2)
        return caminho_arquivo
    except Exception as e:
        logger.warning("salvar_cookies_sessao: %s", e)
        return None


def carregar_cookies_sessao(
    page: Page,
    max_idade_horas: float = 24,
) -> bool:
    """Carrega cookies de arquivo JSON para a page Playwright."""
    try:
        import glob
        arquivos = sorted(glob.glob('cookies_sessao_*.json'), reverse=True)
        for arq in arquivos:
            with open(arq, 'r', encoding='utf-8') as f:
                data = json.load(f)
            ts = datetime.datetime.fromisoformat(data.get('timestamp', '2000-01-01T00:00:00'))
            idade = (datetime.datetime.now() - ts).total_seconds() / 3600
            if idade < max_idade_horas:
                page.context.add_cookies(data['cookies'])
                logger.info("carregar_cookies_sessao: cookies carregados de %s", arq)
                return True
        return False
    except Exception as e:
        logger.warning("carregar_cookies_sessao: %s", e)
        return False


def verificar_e_aplicar_cookies(page: Page) -> bool:
    """Verifica e aplica cookies salvos se disponíveis."""
    return carregar_cookies_sessao(page)


# ============================================================
# CREDENCIAL / LOGIN DELEGATION
# ============================================================

def credencial(
    tipo_driver: str = 'PC',
    tipo_login: str = 'CPF',
    headless: bool = False,
    cpf: str = None,
    senha: str = None,
    url_login: str = None,
    max_idade_cookies: float = 24,
):
    """Obtém page Playwright autenticada.

    Delega para Fix/utils.py para o login real.
    """
    if tipo_driver == 'VT':
        page = criar_driver_VT(headless=headless)
    else:
        page = criar_driver_PC(headless=headless)

    if page is None:
        return None

    # Tentar cookies primeiro
    if carregar_cookies_sessao(page, max_idade_horas=max_idade_cookies):
        return page

    # Login via utils
    if tipo_login == 'CPF' and cpf and senha:
        from Fix.utils import login_cpf
        login_cpf(page, url_login=url_login, cpf=cpf, senha=senha)

    return page


# ============================================================
# VERIFICAÇÃO DE DOCUMENTOS
# ============================================================

def verificar_documento_decisao_sentenca(page: Page) -> bool:
    """Verifica se há documento de decisão/sentença visível — versão Playwright."""
    try:
        return (
            page.locator('text=Sentença').is_visible() or
            page.locator('text=Decisão').is_visible() or
            page.locator('text=Despacho').is_visible()
        )
    except Exception:
        return False


def visibilidade_sigilosos(page: Page, polo: str = 'ativo', log: bool = True) -> dict:
    """Verifica visibilidade de documentos sigilosos — versão Playwright."""
    resultado = {'sigilosos': [], 'total': 0}
    try:
        docs = page.locator('li.tl-item-container').all()
        resultado['total'] = len(docs)
        for doc in docs:
            try:
                if doc.locator('.tl-sigiloso, [class*="sigilo"]').count() > 0:
                    texto = doc.text_content() or ''
                    resultado['sigilosos'].append(texto[:100])
            except Exception:
                continue
        if log and resultado['sigilosos']:
            logger.info("visibilidade_sigilosos: %d/%d sigilosos", len(resultado['sigilosos']), resultado['total'])
    except Exception as e:
        if log:
            logger.warning("visibilidade_sigilosos: %s", e)
    return resultado


# ============================================================
# BUSCA DE DOCUMENTOS NA TIMELINE
# ============================================================

def buscar_documento_argos(
    page: Page,
    log: bool = True,
    ignorar_indices: list = None,
):
    """Busca documento relevante na timeline para fluxo Argos — versão Playwright."""
    try:
        docs = page.locator('a.tl-documento:not([target="_blank"])').all()
        if log:
            logger.debug("buscar_documento_argos: %d documentos encontrados", len(docs))

        for i, doc in enumerate(docs):
            if ignorar_indices and i in ignorar_indices:
                continue
            try:
                texto = doc.text_content() or ''
                if len(texto) > 10:  # documento com conteúdo mínimo
                    return (texto, doc, i)
            except Exception:
                continue

        return None
    except Exception as e:
        if log:
            logger.warning("buscar_documento_argos: %s", e)
        return None


def buscar_documentos_polo_ativo(
    page: Page,
    data_decisao_str: str = None,
    debug: bool = False,
) -> list:
    """Busca documentos do polo ativo na timeline — versão Playwright."""
    resultados = []
    try:
        docs = page.locator('li.tl-item-container').all()
        for doc in docs:
            try:
                texto = doc.text_content() or ''
                resultados.append({'texto': texto, 'elemento': doc})
            except Exception:
                continue
    except Exception as e:
        if debug:
            logger.warning("buscar_documentos_polo_ativo: %s", e)
    return resultados


def buscar_documentos_sequenciais(
    page: Page,
    log: bool = True,
) -> list:
    """Busca documentos sequenciais na timeline — versão Playwright."""
    try:
        docs = page.locator('li.tl-item-container a.tl-documento').all()
        if log:
            logger.debug("buscar_documentos_sequenciais: %d docs", len(docs))
        return [(doc.text_content() or '', doc) for doc in docs]
    except Exception as e:
        if log:
            logger.warning("buscar_documentos_sequenciais: %s", e)
        return []


def buscar_ultimo_mandado(page: Page, log: bool = True):
    """Busca último mandado na timeline — versão Playwright."""
    try:
        mandados = page.locator('a.tl-documento').filter(has_text='Mandado').all()
        if mandados:
            ultimo = mandados[-1]
            if log:
                logger.debug("buscar_ultimo_mandado: encontrado")
            return ultimo.text_content() or '', ultimo
        return None
    except Exception as e:
        if log:
            logger.warning("buscar_ultimo_mandado: %s", e)
        return None


def buscar_mandado_autor(page: Page, log: bool = True):
    """Busca mandado do autor na timeline — versão Playwright."""
    try:
        docs = page.locator('a.tl-documento').all()
        for doc in docs:
            texto = doc.text_content() or ''
            if 'mandado' in texto.lower():
                if log:
                    logger.debug("buscar_mandado_autor: encontrado")
                return texto, doc
        return None
    except Exception as e:
        if log:
            logger.warning("buscar_mandado_autor: %s", e)
        return None


# ============================================================
# BOTÕES AUXILIARES
# ============================================================

def _clicar_botao_movimentar(page: Page, timeout: float = 10, log: bool = False) -> bool:
    """Clica no botão Movimentar Processos."""
    try:
        page.get_by_role('button', name='Movimentar processos').click(
            timeout=int(timeout * 1000)
        )
        return True
    except Exception:
        try:
            page.locator('button').filter(has_text='Movimentar').first.click(
                timeout=int(timeout * 1000)
            )
            return True
        except Exception as e:
            if log:
                logger.warning("_clicar_botao_movimentar: %s", e)
            return False


def _clicar_botao_tarefa_processo(page: Page, timeout: float = 10, log: bool = False) -> bool:
    """Clica no botão de tarefa do processo."""
    try:
        page.locator('button[tarefa-processo], button[abrir-tarefa]').first.click(
            timeout=int(timeout * 1000)
        )
        return True
    except Exception as e:
        if log:
            logger.warning("_clicar_botao_tarefa_processo: %s", e)
        return False


def criar_botoes_detalhes(page: Page) -> bool:
    """Cria/verifica botões de detalhes na timeline — versão Playwright."""
    try:
        botoes = page.locator('button.detalhes, button[abrir-detalhes]').all()
        return len(botoes) > 0
    except Exception:
        return False


# ============================================================
# UTILITÁRIOS
# ============================================================

def exibir_configuracao_ativa() -> None:
    """Exibe configuração ativa do ambiente Playwright."""
    try:
        import playwright
        logger.info("Playwright versão: %s", playwright.__version__ if hasattr(playwright, '__version__') else 'instalado')
    except ImportError:
        logger.warning("Playwright não instalado")


def _log_info(msg: str) -> None:
    """Compatibilidade com logs antigos."""
    logger.info(msg)


def _log_error(msg: str) -> None:
    """Compatibilidade com logs antigos."""
    logger.error(msg)


def _audit(action: str, target: str, status: str, extra: str = None) -> None:
    """Compatibilidade com auditoria antiga."""
    if extra:
        logger.debug("[AUDIT] %s:%s:%s %s", action, target, status, extra)
    else:
        logger.debug("[AUDIT] %s:%s:%s", action, target, status)
