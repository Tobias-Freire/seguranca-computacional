"""
Uso:
    python3 demo.py            # interativo: ENTER avança cada etapa
    python3 demo.py --auto     # roda tudo direto (ensaio)
    python3 demo.py 4          # começa pela etapa 4
"""

import sys
import time

import rsa_didatico as rd

AUTO = "--auto" in sys.argv
INICIO = next((int(a) for a in sys.argv[1:] if a.isdigit()), 1)

AZUL, VERDE, VERM, AMAR, NEGR, FIM = "\033[94m", "\033[92m", "\033[91m", "\033[93m", "\033[1m", "\033[0m"


def titulo(numero, texto):
    print(f"\n{NEGR}{AZUL}{'=' * 70}\n  ETAPA {numero} — {texto}\n{'=' * 70}{FIM}")


def pausa():
    if not AUTO:
        input(f"{AMAR}  [ENTER para continuar]{FIM}")


def curto(numero, digitos=40):
    s = str(numero)
    return s if len(s) <= 2 * digitos else f"{s[:digitos]}...{s[-digitos:]}  ({len(s)} dígitos)"


# ---------------------------------------------------------------------------

def etapa1_exemplo_livro():
    titulo(1, "Exemplo do livro (Stallings): p = 17, q = 11")
    pub, priv = rd.gerar_chaves(p=17, q=11, e=7)
    print(f"  n = p·q            = 17·11      = {pub['n']}")
    print(f"  φ(n) = (p-1)(q-1)  = 16·10      = {priv['phi']}")
    print(f"  e = 7   (mdc(7, 160) = 1)")
    print(f"  d = e⁻¹ mod φ(n)   → 7·d ≡ 1 (mod 160) → d = {priv['d']}   (7·23 = 161)")
    print(f"\n  Chave pública  PU = {{e={pub['e']}, n={pub['n']}}}")
    print(f"  Chave privada  PR = {{d={priv['d']}, n={priv['n']}}}")
    pausa()
    m = 88
    c = rd.cifrar_int(m, pub)
    print(f"\n  Cifrar   M = {m}:   C = 88^7  mod 187 = {VERDE}{c}{FIM}")
    print(f"  Decifrar C = {c}:   M = 11^23 mod 187 = {VERDE}{rd.decifrar_int(c, priv)}{FIM}")
    pausa()


def etapa2_chaves_reais():
    titulo(2, "Gerando um par de chaves de 2048 bits (do zero)")
    t = time.perf_counter()
    pub, priv = rd.gerar_chaves(2048)
    dt = time.perf_counter() - t
    print(f"  Primos sorteados e testados com Miller-Rabin em {dt:.2f} s")
    print(f"  p = {curto(priv['p'])}")
    print(f"  q = {curto(priv['q'])}")
    print(f"  n = {curto(pub['n'])}")
    print(f"  e = {pub['e']}")
    print(f"  d = {curto(priv['d'])}")
    pausa()
    return pub, priv


def etapa3_cifrar(pub, priv):
    titulo(3, "Confidencialidade: Bob cifra com a chave PÚBLICA de Alice")
    msg = input(f"  Digite uma mensagem (ENTER = padrão): ").strip() if not AUTO else ""
    msg = msg or "Encontro às 10h na sala do seminário"
    m = rd.texto_para_int(msg)
    print(f"\n  Texto → número M = {curto(m)}")
    c = rd.cifrar_texto(msg, pub)
    print(f"  C = M^e mod n    = {VERM}{curto(c)}{FIM}")
    pausa()
    print(f"  Alice decifra com a chave PRIVADA: M = C^d mod n")
    print(f"  → {VERDE}{rd.decifrar_texto(c, priv)}{FIM}")
    print(f"\n  {AMAR}Obs.: RSA de livro-texto é determinístico:{FIM} cifrar de novo dá o mesmo C? "
          f"{rd.cifrar_texto(msg, pub) == c}")
    pausa()


def etapa4_assinatura(pub, priv):
    titulo(4, "Assinatura digital: hash SHA-256 + chave PRIVADA")
    msg = "Transferir R$ 100,00 para Bob"
    s = rd.assinar(msg, priv)
    print(f"  Mensagem:   '{msg}'")
    print(f"  Assinatura S = H(M)^d mod n = {curto(s, 30)}")
    print(f"  Verificação (S^e mod n == H(M)): {VERDE}{rd.verificar(msg, s, pub)}{FIM}")
    pausa()
    adulterada = "Transferir R$ 900,00 para Bob"
    print(f"\n  Atacante altera para: '{adulterada}'")
    print(f"  Verificação com a mesma assinatura: {VERM}{rd.verificar(adulterada, s, pub)}{FIM}")
    print(f"  → Integridade e autenticidade garantidas (mas SEM confidencialidade)")
    pausa()


def etapa5_ataque():
    titulo(5, "Ataque matemático: fatorar n para descobrir a chave privada")
    print("  O atacante só conhece a chave PÚBLICA {e, n} e um texto cifrado.\n")
    segredo = "PIX"  # 24 bits: cabe até na menor chave (M precisa ser < n)
    for bits in (32, 48, 64, 72, 80, 88):
        pub, _ = rd.gerar_chaves(bits)
        c = rd.cifrar_texto(segredo, pub)
        t = time.perf_counter()
        quebrada = rd.quebrar_chave(pub)
        dt = time.perf_counter() - t
        texto = rd.decifrar_texto(c, quebrada)
        print(f"  n de {bits:3d} bits: p={quebrada['p']:<14} q={quebrada['q']:<14} "
              f"{dt:8.3f} s  → '{VERM}{texto}{FIM}'")
    print(f"\n  Pollard rho custa ~2^(bits/4): cada +16 bits em n ≈ 16× mais trabalho.")
    print(f"  Recorde mundial (GNFS, 2020): RSA-250 = 829 bits, ~2700 anos de núcleo de CPU.")
    print(f"  {VERDE}Por isso a recomendação é ≥ 2048 bits (slide 25).{FIM}")
    pausa()


def etapa6_biblioteca():
    titulo(6, "Como se usa na prática: biblioteca `cryptography` (OAEP + PSS)")
    try:
        import rsa_biblioteca as rb
    except ImportError:
        print("  (instale com: pip install cryptography)")
        return
    pub, priv = rb.gerar_chaves(2048)
    print("  Chave pública em formato PEM (como em certificados/TLS):")
    print("  " + "\n  ".join(rb.chave_publica_pem(pub).splitlines()[:3]) + "\n  ...")
    msg = "Encontro às 10h na sala do seminário"
    c1, c2 = rb.cifrar(msg, pub), rb.cifrar(msg, pub)
    print(f"\n  Mesma mensagem cifrada 2×:")
    print(f"    C1 = {c1.hex()[:48]}...")
    print(f"    C2 = {c2.hex()[:48]}...")
    print(f"  Iguais? {VERDE}{c1 == c2}{FIM}  → OAEP adiciona aleatoriedade")
    print(f"  Decifrado: {VERDE}{rb.decifrar(c1, priv)}{FIM}")
    s = rb.assinar(msg, priv)
    print(f"  Assinatura PSS válida? {VERDE}{rb.verificar(msg, s, pub)}{FIM}   "
          f"adulterada? {VERM}{rb.verificar(msg + '!', s, pub)}{FIM}")
    print(f"\n{NEGR}  Fim da demonstração. Obrigado!{FIM}\n")


if __name__ == "__main__":
    pub = priv = None
    if INICIO <= 1:
        etapa1_exemplo_livro()
    if INICIO <= 4:
        pub, priv = etapa2_chaves_reais() if INICIO <= 2 else rd.gerar_chaves(2048)
    if INICIO <= 3:
        etapa3_cifrar(pub, priv)
    if INICIO <= 4:
        etapa4_assinatura(pub, priv)
    if INICIO <= 5:
        etapa5_ataque()
    etapa6_biblioteca()
