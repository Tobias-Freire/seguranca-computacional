"""
RSA "de verdade" — usando a biblioteca `cryptography` (pip install cryptography).

Diferenças em relação ao RSA didático:
  * OAEP  (cifração): adiciona aleatoriedade -> o mesmo texto gera cifras diferentes
  * PSS   (assinatura): padding probabilístico recomendado para assinaturas
  * Implementação resistente a ataques de temporização (slide 30)
"""

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

OAEP = padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
PSS = padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH)


def gerar_chaves(bits=2048):
    privada = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    return privada.public_key(), privada


def chave_publica_pem(publica):
    return publica.public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()


def cifrar(mensagem, publica):
    return publica.encrypt(mensagem.encode("utf-8"), OAEP)


def decifrar(cifra, privada):
    return privada.decrypt(cifra, OAEP).decode("utf-8")


def assinar(mensagem, privada):
    return privada.sign(mensagem.encode("utf-8"), PSS, hashes.SHA256())


def verificar(mensagem, assinatura, publica):
    try:
        publica.verify(assinatura, mensagem.encode("utf-8"), PSS, hashes.SHA256())
        return True
    except InvalidSignature:
        return False


if __name__ == "__main__":
    pub, priv = gerar_chaves()
    msg = "Seminário de Criptografia 2026"
    c1, c2 = cifrar(msg, pub), cifrar(msg, pub)
    assert c1 != c2 and decifrar(c1, priv) == decifrar(c2, priv) == msg
    s = assinar(msg, priv)
    assert verificar(msg, s, pub) and not verificar(msg + "!", s, pub)
    print("Todos os testes passaram.")
