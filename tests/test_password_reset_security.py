import hashlib


def test_reset_token_hash_nao_e_o_token_bruto():
    token = "token-de-exemplo-que-nao-deve-ir-para-o-banco"
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()

    assert digest != token
    assert len(digest) == 64


def test_reset_token_hash_e_deterministico():
    token = "token-seguro"
    primeiro = hashlib.sha256(token.encode("utf-8")).hexdigest()
    segundo = hashlib.sha256(token.encode("utf-8")).hexdigest()

    assert primeiro == segundo
