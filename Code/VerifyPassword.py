

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


def fill_text(xpath, keys, wait): 
    elemento_xpath = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    elemento_xpath.click()
    elemento_xpath.send_keys(keys)

def click(xpath, wait):
    elemento_xpath = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    elemento_xpath.click()

    
def VerifyPasswordSigaa(matricula:str, senha:str):
    # 3 - Nao foi possivel determinar a senha
    # 0 - Senha incorreta
    # 1 - Senha correta
    try:
        print("Verificando matrícula: ", matricula)
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Ativa o modo headless
        chrome_options.add_argument("--disable-gpu")  # Necessário para algumas máquinas
        chrome_options.add_argument("--no-sandbox")  # Para ambientes de servidor
        chrome_options.add_argument("--disable-dev-shm-usage")  # Evita problemas de memória compartilhada


        service = Service(log_path='NUL')

        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 5)
        driver.get('https://sigaa.unb.br/')

        seletor_user = '//*[@id="username"]'
        seletor_password = '//*[@id="password"]'
        seletor_btnLogin = '//*[@id="login-form"]/button'

        fill_text(seletor_user, matricula, wait)
        fill_text(seletor_password, senha, wait)
        
        click(seletor_btnLogin, wait)

        inicio = time.time()
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        tempo_decorrido = time.time() - inicio
        tempoMAX = 5
        print(tempo_decorrido)

        if tempo_decorrido > tempoMAX:
            print("TEMPO MAX: ", matricula)
            driver.quit()

            return 3 
        
        time.sleep(0.5)
        if ('AUTENTICAÇÃO INTEGRADA' in driver.page_source or 'cadastre-se aqui' in driver.page_source or 'Credenciais inválidas' in driver.page_source):
            driver.quit()
            print("Senha inválida: ", matricula)

            return 0 #Usuário ou senha infromados estão incorretos
        
        driver.get('https://sigaa.unb.br/')
        time.sleep(2)

        if('Atualizar Foto e Perfil' in driver.page_source and 'Meus Dados Pessoais' in driver.page_source): 
            driver.quit()   
            print("Senha válida: ", matricula)

            return 1 #Senha validada
        
        else: 
            driver.quit()
            print("Nao foi possivel confirmar a senha: ", matricula)
            return 3
    except Exception as e:
        print("Erro na validação de senha no sigaa, ", matricula)
        print (e)

        try: driver.quit()
        except: pass

        return 3