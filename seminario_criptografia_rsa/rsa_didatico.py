"""
RSA didático — implementação do zero (apenas biblioteca padrão do Python).

Baseado em Stallings & Brown, "Computer Security: Principles and Practice",
Caps. 2, 20 e 21 (Algoritmo RSA, funções de hash, assinatura digital).

ATENÇÃO: este é o "RSA de livro-texto" (sem padding). Serve para ENTENDER o
algoritmo. Em produção usa-se RSA com OAEP (cifração) e PSS (assinatura),
como mostrado em rsa_biblioteca.py.
"""

import hashlib
import math
import secrets

# ---------------------------------------------------------------------------
# 1. Ferramentas matemáticas
# ---------------------------------------------------------------------------

def mdc_estendido(a, b):
    """Algoritmo de Euclides estendido: retorna (g, x, y) com a*x + b*y = g."""
    x0, x1, y0, y1 = 1, 0, 0, 1
    while b:
        q, a, b = a // b, b, a % b
        x0, x1 = x1, x0 - q * x1
        y0, y1 = y1, y0 - q * y1
    return a, x0, y0


def inverso_modular(e, phi):
    """d tal que e*d ≡ 1 (mod phi)."""
    g, x, _ = mdc_estendido(e, phi)
    if g != 1:
        raise ValueError("e não é inversível módulo phi(n)")
    return x % phi


def eh_provavel_primo(n, rodadas=40):
    """Teste de primalidade probabilístico de Miller-Rabin."""
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    # escreve n-1 = 2^s * d, com d ímpar
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(rodadas):
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False  # a é "testemunha" de que n é composto
    return True


def gerar_primo(bits):
    """Sorteia números ímpares de `bits` bits até achar um primo."""
    while True:
        # força o bit mais alto (tamanho exato) e o mais baixo (ímpar)
        candidato = secrets.randbits(bits) | (1 << (bits - 1)) | 1
        if eh_provavel_primo(candidato):
            return candidato


# ---------------------------------------------------------------------------
# 2. Geração de chaves
# ---------------------------------------------------------------------------

def gerar_chaves(bits=2048, e=65537, p=None, q=None):
    """
    Passos do RSA (slide 27):
      1. escolher primos p e q
      2. n = p*q
      3. phi(n) = (p-1)(q-1)
      4. escolher e com mdc(e, phi(n)) = 1
      5. d = e^-1 mod phi(n)
    Chave pública PU = {e, n}; chave privada PR = {d, n}.
    """
    while True:
        if p is None or q is None:
            p_, q_ = gerar_primo(bits // 2), gerar_primo(bits - bits // 2)
        else:
            p_, q_ = p, q
        phi = (p_ - 1) * (q_ - 1)
        if p_ != q_ and math.gcd(e, phi) == 1:
            break
        if p is not None:
            raise ValueError("e não é coprimo com phi(n) para esses p, q")
    n = p_ * q_
    d = inverso_modular(e, phi)
    return {"n": n, "e": e}, {"n": n, "d": d, "p": p_, "q": q_, "phi": phi}


# ---------------------------------------------------------------------------
# 3. Cifração / decifração (C = M^e mod n ; M = C^d mod n)
# ---------------------------------------------------------------------------

def cifrar_int(m, pub):
    if not 0 <= m < pub["n"]:
        raise ValueError("M precisa estar entre 0 e n-1")
    return pow(m, pub["e"], pub["n"])


def decifrar_int(c, priv):
    return pow(c, priv["d"], priv["n"])


def texto_para_int(texto):
    return int.from_bytes(texto.encode("utf-8"), "big")


def int_para_texto(numero):
    tamanho = (numero.bit_length() + 7) // 8
    return numero.to_bytes(tamanho, "big").decode("utf-8")


def cifrar_texto(texto, pub):
    return cifrar_int(texto_para_int(texto), pub)


def decifrar_texto(c, priv):
    return int_para_texto(decifrar_int(c, priv))


# ---------------------------------------------------------------------------
# 4. Assinatura digital (hash SHA-256 + chave privada)
# ---------------------------------------------------------------------------

def hash_int(mensagem, n):
    h = hashlib.sha256(mensagem.encode("utf-8")).digest()
    return int.from_bytes(h, "big") % n


def assinar(mensagem, priv):
    """S = H(M)^d mod n — só o dono da chave privada consegue produzir."""
    return pow(hash_int(mensagem, priv["n"]), priv["d"], priv["n"])


def verificar(mensagem, assinatura, pub):
    """Qualquer um com a chave pública confere: S^e mod n == H(M)?"""
    return pow(assinatura, pub["e"], pub["n"]) == hash_int(mensagem, pub["n"])


# ---------------------------------------------------------------------------
# 5. Ataque matemático: fatoração de n (Pollard rho, variante de Brent)
# ---------------------------------------------------------------------------

def pollard_rho(n):
    """Encontra um fator não trivial de n. Custo ~ sqrt(menor primo)."""
    if n % 2 == 0:
        return 2
    while True:
        y, c, m = secrets.randbelow(n - 1) + 1, secrets.randbelow(n - 1) + 1, 128
        g, r, q = 1, 1, 1
        while g == 1:
            x = y
            for _ in range(r):
                y = (y * y + c) % n
            k = 0
            while k < r and g == 1:
                ys = y
                for _ in range(min(m, r - k)):
                    y = (y * y + c) % n
                    q = q * abs(x - y) % n
                g = math.gcd(q, n)
                k += m
            r *= 2
        if g == n:
            g = 1
            while g == 1:
                ys = (ys * ys + c) % n
                g = math.gcd(abs(x - ys), n)
        if g != n:
            return g


def quebrar_chave(pub):
    """A partir SOMENTE da chave pública {e, n}, reconstrói a chave privada."""
    p = pollard_rho(pub["n"])
    q = pub["n"] // p
    phi = (p - 1) * (q - 1)
    d = inverso_modular(pub["e"], phi)
    return {"n": pub["n"], "d": d, "p": p, "q": q, "phi": phi}


# ---------------------------------------------------------------------------
# Autoteste rápido: python3 rsa_didatico.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Exemplo do livro: p=17, q=11, e=7 -> d=23; M=88 -> C=11
    pub, priv = gerar_chaves(p=17, q=11, e=7)
    assert priv["d"] == 23 and cifrar_int(88, pub) == 11 and decifrar_int(11, priv) == 88

    pub, priv = gerar_chaves(1024)
    msg = "Seminário de Criptografia 2026"
    assert decifrar_texto(cifrar_texto(msg, pub), priv) == msg
    s = assinar(msg, priv)
    assert verificar(msg, s, pub) and not verificar(msg + "!", s, pub)

    pub, _ = gerar_chaves(64)
    assert decifrar_texto(cifrar_texto("oi", pub), quebrar_chave(pub)) == "oi"
    print("Todos os testes passaram.")
