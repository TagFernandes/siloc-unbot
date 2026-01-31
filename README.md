# SILOC - System for Login Check

O **SILOC** é uma ferramenta automatizada desenvolvida para validação de credenciais. Utilizando **Selenium** para simular interações reais, o sistema verifica a validade de logins e gerencia o acesso através de chaves de API.

---

## 🚀 Como Executar

Para rodar o sistema, siga os passos abaixo:

1. **Instale as dependências:**
   Certifique-se de ter o Python instalado e execute o comando:
   ```bash
   pip install -r requirements.txt

2. **Execute:**
   ```bash
   python3 app.py


## ⚙️ Configuração

O sistema é alimentado por dois arquivos JSON principais:

### 1. config.json

Gerencia os parâmetros operacionais da aplicação.

* `navegadoresMAX`: Define a quantidade de navegadores simultâneos que o Selenium pode abrir. Este controle é essencial para não sobrecarregar a memória RAM do sistema.

### 2. secrets_acess.json

Este arquivo funciona como uma lista de controle de acesso (ACL), definindo quais chaves (tokens) e usuários/sistemas externos têm permissão para consumir o serviço.

* **Estrutura:** `{"chave": "usuario"}`
* **Exemplo:** `{"chave1": "usuario1", "chave2": "sistema_externo"}`
<br><br>
<br><br>

# 🏗️ Arquitetura do Sistema SILOC
---

## 🧩 Visão Geral da Solução

O SILOC opera como um microserviço de validação de identidade que utiliza automação de interface (RPA) para verificar credenciais em sistemas que não possuem APIs formais.

### Componentes Principais:
1.  **API Gateway (Flask):** Gerencia as rotas, autenticação de tokens e o fluxo de requisições.
2.  **Motor de Automação (Selenium):** Responsável pela interação direta com o portal de destino (SIGAA).
3.  **Módulo de Segurança (RSA):** Garante a integridade e o sigilo das senhas trafegadas.
4.  **Stack de Observabilidade:** Monitoramento em tempo real via Prometheus, Loki e OpenTelemetry.

---

## 🔒 Fluxo de Segurança (Criptografia Assimétrica)

O sistema utiliza o algoritmo **RSA de 2048 bits** com preenchimento **OAEP (SHA-256)** para proteger as credenciais.

1.  **Inicialização:** O servidor gera um par de chaves (`chave_privada.pem` e `chave_publica.pem`) ao iniciar.
2.  **Distribuição:** O cliente consome o endpoint `/chave-publica` para obter a chave de criptografia.
3.  **Envio:** A senha é criptografada no lado do cliente e enviada em Base64.
4.  **Descriptografia:** O `app.py` utiliza a chave privada local para obter a senha original apenas no momento da execução do Selenium.

---

## 🚦 Controle de Concorrência (Semáforo de Navegadores)

Para evitar o esgotamento de memória RAM (comum ao abrir múltiplas instâncias do Chrome), o sistema implementa um controle de estado:

* **Configuração:** O limite é lido do campo `navegadoresMAX` no `config.json`.
* **Lógica:** Antes de iniciar um `driver.get()`, o sistema verifica se `NAVEGADORES_ATIVOS < navegadoresMAX`.
* **Resposta de Sobrecarga:** Caso o limite seja atingido, o servidor retorna **HTTP 503 (Service Unavailable)**, preservando a estabilidade da máquina.

---

## 📊 Observabilidade e Telemetria

O SILOC foi desenhado para ser monitorado via **Grafana**, utilizando os seguintes coletores:

| Ferramenta | Função | Principais Métricas/Logs |
| :--- | :--- | :--- |
| **Prometheus** | Métricas de Performance | `flask_request_latency_seconds`, `navegadores_disponiveis` |
| **Loki** | Centralização de Logs | Logs de erro de login, falhas de descriptografia e tokens inválidos |
| **OpenTelemetry** | Rastreamento (Tracing) | Identificação de gargalos no tempo de resposta do Selenium |

---

## 🛠️ Tecnologias Utilizadas

* **Backend:** Flask (Python)
* **Automação:** Selenium WebDriver (Chrome Headless)
* **Segurança:** Cryptography (RSA/OAEP)
* **Monitoramento:** Prometheus Client, Loki Logger, OpenTelemetry SDK

---

> **Nota Técnica:** O sistema utiliza `threading` implícito pelo Flask para lidar com múltiplas requisições, mas o gargalo real é controlado pelo pool de navegadores definido no arquivo de configuração.
