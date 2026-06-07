"""
run_playwright.py — Entry point Playwright para todos os módulos PJe.

Uso:
    py run_playwright.py              ← menu interativo
    py run_playwright.py mandado      ← executar Mandado direto
    py run_playwright.py prazo        ← executar Prazo direto
    py run_playwright.py pec          ← executar PEC direto
    py run_playwright.py smoke        ← teste de fumaça (abre e fecha browser)
"""

import sys
from Fix.playwright_core import (
    criar_driver_PC, criar_driver_VT, finalizar_driver,
)
from Fix.browser_suporte_play import validar_conexao_page
from Fix.variaveis import session_from_page, PjeApiClient

# ── Configuração ──
URL_PJE = "https://pje.trt2.jus.br/pjekz/"


def login_playwright(page, cpf=None, senha=None):
    """Login no PJe usando a versão Playwright de login_cpf."""
    from Fix.utils import login_cpf_playwright

    if cpf and senha:
        return login_cpf_playwright(page, cpf=cpf, senha=senha)
    else:
        # Tenta pegar do ambiente
        import os
        cpf = os.environ.get('PJE_USER')
        senha = os.environ.get('PJE_SENHA')
        if cpf and senha:
            return login_cpf_playwright(page, cpf=cpf, senha=senha)

        print("\n🔐 Login manual necessário.")
        print("   Configure as variáveis de ambiente PJE_USER e PJE_SENHA")
        print("   ou use: py run_playwright.py --cpf SEU_CPF --senha SUA_SENHA")
        page.goto(URL_PJE)
        input("   Faça login no navegador e pressione Enter...")
        return True


def smoke_test():
    """Teste rápido: abre o browser, navega, fecha."""
    print("🧪 Smoke test Playwright...")
    page = criar_driver_PC(headless=False)
    if not page:
        print("❌ Falha ao criar page")
        return

    print("   ✅ Page criada")
    page.goto(URL_PJE)
    print(f"   ✅ Navegou para: {page.url}")
    print("   ✅ Conexão:", "OK" if validar_conexao_page(page) else "FALHA")

    # Testar session_from_page (vai falhar sem login, mas testa que não quebra)
    try:
        sess, trt = session_from_page(page)
        print(f"   ✅ session_from_page: host={trt}")
    except Exception as e:
        print(f"   ⚠️ session_from_page: {e} (esperado sem login)")

    finalizar_driver(page)
    print("✅ Smoke test concluído!")


def run_mandado(cpf=None, senha=None):
    """Executa fluxo Mandado com Playwright."""
    print("\n📋 MANDADO — Fluxo de Mandados (Playwright)")

    page = criar_driver_PC(headless=False)
    if not page:
        print("❌ Falha ao criar page")
        return

    try:
        if not login_playwright(page, cpf, senha):
            print("❌ Falha no login")
            return

        # Usa a versão Playwright do Mandado
        from Mandado.core_play import main as mandado_main
        mandado_main()

    except ImportError as e:
        print(f"⚠️ Mandado core_play.py: {e}")
        print("   O módulo Mandado ainda referencia imports originais.")
        print("   Edite Mandado/core_play.py para ajustar os imports internos.")
    finally:
        finalizar_driver(page)


def run_prazo(cpf=None, senha=None):
    """Executa fluxo Prazo com Playwright."""
    print("\n📅 PRAZO — Loop de Prazos (Playwright)")

    page = criar_driver_PC(headless=False)
    if not page:
        print("❌ Falha ao criar page")
        return

    try:
        if not login_playwright(page, cpf, senha):
            print("❌ Falha no login")
            return

        from Prazo.loop_orquestrador_play import loop_prazo
        resultado = loop_prazo(page)
        print(f"Resultado: {resultado}")

    except ImportError as e:
        print(f"⚠️ Prazo loop_orquestrador_play.py: {e}")
        print("   Verifique os imports internos do arquivo _play.py")
    finally:
        finalizar_driver(page)


def run_pec(cpf=None, senha=None):
    """Executa fluxo PEC com Playwright."""
    print("\n📨 PEC — Processamento de Petições (Playwright)")

    page = criar_driver_PC(headless=False)
    if not page:
        print("❌ Falha ao criar page")
        return

    try:
        if not login_playwright(page, cpf, senha):
            print("❌ Falha no login")
            return

        from PEC.regras_play import determinar_acoes_por_observacao
        print("✅ PEC importado com sucesso")
        # O fluxo completo requer configuração adicional (atividades, buckets)
        print("   Execute o fluxo PEC completo via orquestrador")

    except ImportError as e:
        print(f"⚠️ PEC regras_play.py: {e}")
    finally:
        finalizar_driver(page)


def menu():
    """Menu interativo."""
    print("=" * 55)
    print("🎭 PJe Plus — PLAYWRIGHT")
    print("=" * 55)
    print("  1 — Smoke test (abre/fecha browser)")
    print("  2 — Mandado (fluxo Argos + Outros)")
    print("  3 — Prazo (loop de prazos)")
    print("  4 — PEC (petições eletrônicas)")
    print("  0 — Sair")
    print("=" * 55)

    choice = input("   Opção: ").strip()

    if choice == "1":
        smoke_test()
    elif choice == "2":
        run_mandado()
    elif choice == "3":
        run_prazo()
    elif choice == "4":
        run_pec()
    elif choice == "0":
        print("👋 Saindo...")
    else:
        print("Opção inválida")


# ── Entry point ──
if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""

    # Parse --cpf e --senha dos argumentos
    cpf = None
    senha = None
    for i, a in enumerate(sys.argv):
        if a == '--cpf' and i + 1 < len(sys.argv):
            cpf = sys.argv[i + 1]
        if a == '--senha' and i + 1 < len(sys.argv):
            senha = sys.argv[i + 1]

    if arg == "smoke":
        smoke_test()
    elif arg == "mandado":
        run_mandado(cpf=cpf, senha=senha)
    elif arg == "prazo":
        run_prazo(cpf=cpf, senha=senha)
    elif arg == "pec":
        run_pec(cpf=cpf, senha=senha)
    else:
        menu()
