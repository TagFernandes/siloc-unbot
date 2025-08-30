import requests
import json
import base64
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes

SERVER_URL = 'https://siloc.unbot.com.br'

matricula_usuario = '221030885'
senha_usuario = 'teste1234'

def criptografar(mensagem: str, chave_publica_pem: str) -> str:
    """
    Criptografa uma mensagem de texto usando a chave pública RSA (em formato PEM) 
    e a codifica em Base64.
    """
    # Carrega a chave pública a partir da string PEM
    chave_publica = serialization.load_pem_public_key(
        chave_publica_pem.encode('utf-8')
    )

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

def main():
    print("--- Cliente de Login Seguro (Versão 2) ---")

    # 1. Obter a chave pública do servidor
    try:
        print(f"1. Solicitando chave pública de {SERVER_URL}/chave-publica...")
        resposta_chave = requests.get(f"{SERVER_URL}/chave-publica")
        resposta_chave.raise_for_status()
        
        chave_publica_servidor = resposta_chave.json()['chave_publica']
        print("   Chave pública recebida com sucesso!\n")
    except requests.exceptions.RequestException as e:
        print(f"ERRO: Não foi possível conectar ao servidor. {e}")
        return

    # 2. Preparar os dados de login
    print("2. Criptografando a senha...")
    print(f"   Matrícula (texto puro): {matricula_usuario}")
    print(f"   Senha (original): {senha_usuario}")
    
    senha_criptografada = criptografar(senha_usuario, chave_publica_servidor)
    print(f"   Senha (criptografada): {senha_criptografada[:40]}...\n")
    
    # 3. Montar e enviar o payload final
    payload_final = {
        'matricula': matricula_usuario,
        'senha': senha_criptografada
    }
    
    print(f"3. Enviando JSON para {SERVER_URL}/check-login...")
    print(f"   Payload a ser enviado: {json.dumps(payload_final, indent=2)}")
    
    try:
        resposta_login = requests.post(f"{SERVER_URL}/check-login", json=payload_final)
        
        # 4. Exibir a resposta do servidor
        print("\n--- Resposta do Servidor ---")
        print(f"Status Code: {resposta_login.status_code}")
        print(f"Corpo da Resposta: {resposta_login.json()}")

    except requests.exceptions.RequestException as e:
        print(f"ERRO: Não foi possível enviar os dados de login. {e}")

if __name__ == '__main__':
    main()