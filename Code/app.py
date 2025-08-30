from flask import Flask, request, jsonify
import time
import os
import json

import RSA
import VerifyPassword

app = Flask(__name__)

NAVEGADORES_ATIVOS=0

def controle_navegadores(modifyNumber=0):
    global NAVEGADORES_ATIVOS
    
    with open("config.json", 'r', encoding='utf-8') as arquivo:
        configuracoes = json.load(arquivo)
        maxNavegadores = int(configuracoes.get("navegadoresMAX"))
    if maxNavegadores <= 0: return True

    if (NAVEGADORES_ATIVOS >= maxNavegadores) and (modifyNumber > 0):
        return False

    NAVEGADORES_ATIVOS += modifyNumber
    return True


@app.route('/check-login', methods=['POST'])
def check_login():
    if not request.is_json:
        return jsonify({"erro": "O corpo da requisição deve ser JSON"}), 400

    data = request.get_json()
    matricula = data.get('matricula')
    senha = data.get('senha')

    if not matricula or not senha:
        return jsonify({"erro": "Os campos 'matricula' e 'senha' são obrigatórios"}), 400
    
    senha_decriptografada = RSA.descriptografar(senha)
    
    if (controle_navegadores(1) == False): return jsonify({"status": "servidor ocupado, tente novamente mais tarde"}), 503
    resultado = int(VerifyPassword.VerifyPasswordSigaa(str(matricula), senha_decriptografada))
    controle_navegadores(-1)

    if (resultado == 0):
        return jsonify({"status": "senha incorreta"}), 401
    elif (resultado == 1):
        return jsonify({"status": "senha correta"}), 200
    elif (resultado == 3):
        return jsonify({"status": "não foi possível determinar a senha"}), 503
    else:
        return jsonify({"status": "erro desconhecido"}), 500



@app.route("/chave-publica", methods=['GET'])
def obter_chave_publica():
    """
    Endpoint que lê o arquivo da chave pública e o retorna em um formato JSON.
    """

    # Lê o conteúdo do arquivo da chave pública
    with open(CAMINHO_CHAVE_PUBLICA, 'r') as f:
        chave_publica_pem = f.read()
    
    # Retorna a chave dentro de um objeto JSON
    return jsonify({
        'algoritmo': 'RSA',
        'formato': 'PEM',
        'chave_publica': chave_publica_pem
    })


if __name__ == '__main__':
    PASTA_CHAVES = 'chaves'
    CAMINHO_CHAVE_PUBLICA = os.path.join(PASTA_CHAVES, 'chave_publica.pem')

    RSA.gerar_chaves_rsa()
    time.sleep(2)

    print(RSA.criptografar("teste1234"))

    print("Serivdor iniciado")
    app.run(host='0.0.0.0', port=5000, debug=False)