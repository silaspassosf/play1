"""
Fix/browser_suporte_play.py — Suporte de browser Playwright.

Equivalente Playwright de Fix/browser_suporte.py.
Fornece funções para gerenciamento de abas, validação de page,
cliques e otimizações com Playwright nativo.
"""

import time
from typing import Optional

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from Fix.log import logger
from Fix.playwright_core import aguardar_e_clicar, safe_click_no_scroll


# ============================================================
# Funções de abas
# ============================================================

def is_browsing_context_discarded_error(error_message: str) -> bool:
    """Compatibilidade. No Playwright basta checar page.is_closed()."""
    if not error_message:
        return False
    msg = str(error_message).lower()
    return (
        'target closed' in msg or
        'page closed' in msg or
        'connection closed' in msg or
        'browsing context has been discarded' in msg
    )


def validar_conexao_page(page: Page, contexto: str = "GERAL", proc_id: Optional[str] = None) -> bool:
    """Versão Playwright de validar_conexao_driver."""
    if page.is_closed():
        logger.error("validar_conexao_page: page está fechada [%s]", contexto)
        return False
    try:
        _ = page.url  # teste de conexão
        return True
    except Exception as e:
        logger.error("validar_conexao_page: erro: %s [%s]", e, contexto)
        return False


# Alias para compatibilidade com código que chama validar_conexao_driver
def validar_conexao_driver(page: Page, contexto: str = "GERAL", proc_id: Optional[str] = None) -> bool:
    """Alias de compatibilidade — redireciona para validar_conexao_page."""
    return validar_conexao_page(page, contexto, proc_id)


def trocar_para_nova_aba(page: Page, aba_lista_original: str = None, timeout: float = 10) -> Optional[Page]:
    """Retorna a última aba aberta no contexto. Equivale a trocar_para_nova_aba do Selenium."""
    pages = page.context.pages
    if len(pages) > 1:
        return pages[-1]
    try:
        with page.context.expect_page(timeout=int(timeout * 1000)) as new_page_info:
            pass
        nova = new_page_info.value
        nova.wait_for_load_state()
        return nova
    except PlaywrightTimeoutError:
        logger.warning("trocar_para_nova_aba: nenhuma nova aba abriu em %ss", timeout)
        return page


def aguardar_nova_aba(page: Page, aba_lista_original: str = None, timeout: float = 10) -> Page:
    """Aguarda e retorna nova aba."""
    pages_antes = len(page.context.pages)
    try:
        page.wait_for_timeout(500)
        for _ in range(int(timeout * 2)):
            pages = page.context.pages
            if len(pages) > pages_antes:
                nova = pages[-1]
                nova.wait_for_load_state()
                return nova
            time.sleep(0.5)
    except Exception as e:
        logger.warning("aguardar_nova_aba: %s", e)
    return page


def forcar_fechamento_abas_extras(page: Page, aba_lista_original: str = None) -> None:
    """Fecha todas as abas exceto a primeira do contexto."""
    pages = page.context.pages
    for p in pages[1:]:
        try:
            p.close()
        except Exception as e:
            logger.debug("forcar_fechamento_abas_extras: %s", e)


# ============================================================
# Overlays e headless
# ============================================================

def limpar_overlays_headless(page: Page) -> bool:
    """Playwright não precisa de limpeza de overlays — no-op."""
    return True


def click_headless_safe(page: Page, selector: str, by=None, timeout: int = 10) -> bool:
    """Compatibilidade. No Playwright .click() já funciona em headless."""
    try:
        page.locator(selector).first.click(timeout=timeout * 1000)
        return True
    except Exception as e:
        logger.warning("click_headless_safe: %s: %s", selector, e)
        return False


def is_headless_mode(page: Page) -> bool:
    """Sempre False no contexto Playwright — sem tratamento especial para headless."""
    return False


# ============================================================
# Scroll
# ============================================================

def scroll_to_element_safe(page: Page, element, log: bool = False) -> bool:
    """Scroll seguro — usa scroll_into_view_if_needed do Playwright."""
    try:
        element.scroll_into_view_if_needed()
        return True
    except Exception as e:
        if log:
            logger.warning("scroll_to_element_safe: %s", e)
        return False


# ============================================================
# Otimizações (no-op no Playwright)
# ============================================================

def inicializar_otimizacoes(page: Page = None) -> None:
    """No-op — Playwright gerencia otimizações nativamente."""
    pass


def finalizar_otimizacoes(page: Page = None) -> None:
    """No-op — Playwright gerencia otimizações nativamente."""
    pass
