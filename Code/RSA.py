import os
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric.padding import MGF1

def gerar_chaves_rsa():
    """
    Gera um par de chaves RSA (pública e privada) e as salva em arquivos
    na pasta 'chaves'.
    """
    # Cria a pasta 'chaves' se ela não existir
    if not os.path.exists('chaves'):
        os.makedirs('chaves')

    # Gera a chave privada
    chave_privada = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Serializa a chave privada para o formato PEM
    pem_chave_privada = chave_privada.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Salva a chave privada em um arquivo
    with open('chaves/chave_privada.pem', 'wb') as f:
        f.write(pem_chave_privada)

    # Gera a chave pública correspondente
    chave_publica = chave_privada.public_key()

    # Serializa a chave pública para o formato PEM
    pem_chave_publica = chave_publica.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Salva a chave pública em um arquivo
    with open('chaves/chave_publica.pem', 'wb') as f:
        f.write(pem_chave_publica)

    print("Par de chaves RSA gerado e salvo na pasta 'chaves'.")

def criptografar(mensagem: str) -> str:
    """
    Criptografa uma mensagem de texto usando a chave pública RSA e a codifica em Base64.

    Args:
        mensagem: A string de texto a ser criptografada.

    Returns:
        Uma string contendo a mensagem criptografada e codificada em Base64.
    """
    # Carrega a chave pública do arquivo
    with open('chaves/chave_publica.pem', 'rb') as f:
        chave_publica = serialization.load_pem_public_key(f.read())

    # Converte a mensagem de string para bytes
    mensagem_bytes = mensagem.encode('utf-8')

    # Criptografa a mensagem usando o preenchimento OAEP
    cifra = chave_publica.encrypt(
        mensagem_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Codifica a cifra em Base64 e a retorna como uma string
    return base64.b64encode(cifra).decode('utf-8')

def descriptografar(mensagem_criptografada_b64: str) -> str:
    """
    Descriptografa uma mensagem codificada em Base64 usando a chave privada RSA.

    Args:
        mensagem_criptografada_b64: A string criptografada e codificada em Base64.

    Returns:
        A string da mensagem original.
    """
    # Carrega a chave privada do arquivo
    with open('chaves/chave_privada.pem', 'rb') as f:
        chave_privada = serialization.load_pem_private_key(
            f.read(),
            password=None
        )

    # Decodifica a mensagem de Base64 para bytes
    cifra = base64.b64decode(mensagem_criptografada_b64)

    # Descriptografa a mensagem usando a chave privada e o mesmo preenchimento
    mensagem_original_bytes = chave_privada.decrypt(
        cifra,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Converte os bytes descriptografados de volta para uma string
    return mensagem_original_bytes.decode('utf-8')
