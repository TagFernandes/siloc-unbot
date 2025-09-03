from flask import Flask, request, jsonify, g ,Response
import time
import os
import json
from functools import wraps


# 1. --- Imports do OpenTelemetry ---
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor # A biblioteca chave
## Log
import logging
from loki_logger_handler.loki_logger_handler import LokiLoggerHandler

# Metricas
from prometheus_client import (
    Counter, Gauge, Histogram, 
    generate_latest, CONTENT_TYPE_LATEST
)


import RSA
import VerifyPassword


#Log
handler = LokiLoggerHandler(
    url="http://localhost:3100/loki/api/v1/push",
    labels={"application": "SILOC", "environment": "development"},
)
logger = logging.getLogger("my-app-logger")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

#Trace
resource = Resource(attributes={
    "service.name": "siloc-unbot",
    "service.version": "0.1.0"
})
tracer_provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)


#Metricas
REQUESTS_TOTAL = Counter(
    'flask_requests_total',
    'Total de requisições HTTP processadas.',
    ['method', 'endpoint', 'status_code']
)

ERRORS_TOTAL = Counter(
    'flask_errors_total',
    'Total de erros encontrados na aplicação.',
    ['error_type', 'endpoint']
)
REQUESTS_IN_PROGRESS = Gauge(
    'flask_requests_in_progress',
    'Número de requisições em progresso.',
    ['endpoint']
)

REQUEST_LATENCY = Histogram(
    'flask_request_latency_seconds',
    'Latência das requisições HTTP.',
    ['endpoint'],
    buckets=[0.1, 0.2, 0.5, 1, 2, 5]
)

NAVEGADORES_DISPONIVEIS = Gauge(
    'navegadores_disponiveis',
    'Número de navegadores disponiveis para as requisicoes'
)


app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
NAVEGADORES_ATIVOS=0





@app.before_request
def before_request():
    """Executado antes de cada requisição."""
    # Armazena o tempo de início no objeto 'g' do Flask, que é específico para cada requisição
    g.start_time = time.time()
    # Incrementa o gauge de requisições em progresso para o endpoint atual
    REQUESTS_IN_PROGRESS.labels(endpoint=request.path).inc()

@app.after_request
def after_request(response):
    """Executado após cada requisição."""
    # Calcula a latência
    latency = time.time() - g.start_time
    # Observa a latência no histograma, com a label do endpoint
    REQUEST_LATENCY.labels(endpoint=request.path).observe(latency)
    
    # Decrementa o gauge de requisições em progresso
    REQUESTS_IN_PROGRESS.labels(endpoint=request.path).dec()
    
    # Incrementa o contador de requisições totais
    REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=request.path,
        status_code=response.status_code
    ).inc()
    
    return response

@app.route('/metrics')
def metrics():
    """Expõe as métricas no formato do Prometheus."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)



###########################################################################################################################


def readConfig():
    with open("config.json", 'r', encoding='utf-8') as arquivo:
        configuracoes = json.load(arquivo)
    return configuracoes

def readSecrets():
    with open("secrets_acess.json", 'r', encoding='utf-8') as arquivo:
        secrets = json.load(arquivo)
    return secrets

##############################################################################################################################


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Verifica se o cabeçalho de autorização foi enviado
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # Extrai o token do formato "Bearer <token>"
                token = auth_header.split(" ")[1]
            except IndexError:
                logger.warning("Formato de token malformado")
                return jsonify({"mensagem": "Formato de token malformado"}), 401
        
        if not token:
            logger.warning("Token ausente")
            return jsonify({"mensagem": "Token ausente"}), 401
        
        authorized_acess = readSecrets()
        if (token not in authorized_acess):
            print("token_invalido")
            logger.warning("Token inválido")
            return jsonify({"mensagem": "Token inválido"}), 401
        logger.info(f"Token válido: {authorized_acess[token]}")
        print(f"Token válido: {authorized_acess[token]}")

        return f(*args, **kwargs)
    return decorated

        
def controle_navegadores(modifyNumber=0):
    global NAVEGADORES_ATIVOS
    
    config = readConfig()
    maxNavegadores = int(config.get("navegadoresMAX"))

    if maxNavegadores <= 0: 
        NAVEGADORES_DISPONIVEIS.set(-1)
        return True

    if (NAVEGADORES_ATIVOS >= maxNavegadores) and (modifyNumber > 0):
        logger.warning(f"Maximo de navegaroes atingidos - {NAVEGADORES_ATIVOS} de {maxNavegadores}")
        return False

    NAVEGADORES_ATIVOS += modifyNumber
    NAVEGADORES_DISPONIVEIS.set(maxNavegadores - NAVEGADORES_ATIVOS )
    return True


@app.route('/check-login', methods=['POST'])
@token_required
def check_login():
    if not request.is_json:
        logger.warning("Requisicao mal formatada")
        return jsonify({"erro": "O corpo da requisição deve ser JSON"}), 400

    data = request.get_json()
    matricula = data.get('matricula')
    senha = data.get('senha')

    if not matricula or not senha:
        logger.warning("Requisicao nao contem campos senha ou matricula")
        return jsonify({"erro": "Os campos 'matricula' e 'senha' são obrigatórios"}), 400
    
    try:
        senha_decriptografada = RSA.descriptografar(senha)
    except:
        logger.error("Falha ao descriptografar a senha")
    
    if (controle_navegadores(1) == False):
        logger.error("Servidor sobrecarregado: sem navegadores disponiveis para processar a requisicao") 
        return jsonify({"status": "servidor ocupado, tente novamente mais tarde"}), 503
    resultado = int(VerifyPassword.VerifyPasswordSigaa(str(matricula), senha_decriptografada))
    controle_navegadores(-1)

    if (resultado == 0):
        logger.info("Senha validada: senha ou usuario incorretos")
        return jsonify({"status": "senha ou usuario incorretos"}), 401
    elif (resultado == 1):
        logger.info("Senha validada: senha correta")
        return jsonify({"status": "senha correta"}), 200
    elif (resultado == 3):
        logger.error("Nao foi possivel determinar se a senha esta correta")
        return jsonify({"status": "não foi possível determinar a senha"}), 503
    else:
        logger.error("Nao foi possivel determinar se a senha esta correta - Falha desconhecida")
        return jsonify({"status": "erro desconhecido"}), 500



@app.route("/chave-publica", methods=['GET'])
@token_required
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

    print(RSA.criptografar("teste123"))
    print("Serivdor iniciado")
    

    config = readConfig()
    maxNavegadores = int(config.get("navegadoresMAX"))
    NAVEGADORES_DISPONIVEIS.set(maxNavegadores)

    logger.info("Servidor iniciado")
    app.run(host='0.0.0.0', port=5000, debug=False)