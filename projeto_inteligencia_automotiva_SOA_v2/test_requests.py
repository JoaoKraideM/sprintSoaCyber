import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def executar_testes_poc():
    print("=== INICIANDO VERIFICAÇÃO DE APRESENTAÇÃO, SERVIÇO E CYBERSECURITY ===")
    
    # 1. Teste de Autenticação Segura (JWT Generation)
    print("\n[1] Testando login com credenciais do .env...")
    login_data = {"username": "analista_mercado", "password": "Analise789"}
    res_login = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if res_login.status_code != 200:
        print("Erro ao autenticar. Certifique-se de que o servidor está online via 'python run.py'.")
        return
        
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✔ Token JWT obtido com sucesso.")

    # 2. Execução do Cenário Mandatório do Desafio (Ford Ranger Raptor)
    print("\n[2] Enviando request estruturado de consulta competitivo para validação...")
    payload_busca = {
        "marca": "Ford",
        "modelo": "Ranger Raptor",
        "versao": "3.0 V6 Bi-Turbo",
        "atributos_desejados": ["Amortecedores", "Som", "Ar Condicionado Digital", "Teto Solar"]
    }
    res_busca = requests.post(f"{BASE_URL}/veiculos/comparar", json=payload_busca, headers=headers)
    print("Status da Resposta:", res_busca.status_code)
    print("JSON de Saída Padronizado:")
    print(json.dumps(res_busca.json(), indent=2, ensure_ascii=False))

    # 3. Teste de Resiliência de Cybersecurity (Payload Flooding Prevention)
    print("\n[3] Injetando ataque de payload massivo fictício (>50KB) para testar o Middleware...")
    payload_gigante = {
        "marca": "Ford", "modelo": "Ranger Raptor", "versao": "A" * 60000 # Força estouro do buffer configurado
    }
    res_cyber = requests.post(f"{BASE_URL}/veiculos/comparar", json=payload_gigante, headers=headers)
    print(f"Status esperado (413): {res_cyber.status_code}")
    print("Resposta do barramento de proteção:", res_cyber.text)

if __name__ == "__main__":
    try:
        executar_testes_poc()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERRO: O servidor da API não está a rodar. Execute 'python run.py' antes de testar.")