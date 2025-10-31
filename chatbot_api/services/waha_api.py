import os
import requests
import json

class Waha():

    def __init__(self):
        self.__api_url = os.environ.get("WAHA_API_URL", "http://waha:3000")
        self.waha_api_chave = os.environ.get("WAHA_API_KEY") 
        self.waha_instance = os.environ.get("WAHA_INSTANCE_KEY", "default")

    def send_whatsapp_message(self, chat_id, message):
        url = f"{self.__api_url}/api/sendText"
        api_key = self.waha_api_chave 
        session_name = self.waha_instance
        
        headers = {
        'Content-Type': 'application/json',
        'X-Api-Key': api_key
        }
        
        payload = {    
            "chatId": chat_id,         
            "text": message,
            "session": session_name
        }
        
        try:
            response = requests.post(
                url, 
                headers=headers, 
                data=json.dumps(payload)
            )
            response.raise_for_status() 
            
            print(f"Mensagem enviada com sucesso! Status: {response.status_code}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            # Captura erros de conexão ou erros de status (4xx/5xx)
            print(f"Erro ao enviar mensagem para WAHA: {e}")
            if response is not None and response.status_code == 401:
                print("ERRO 401: Verifique se o AUTH_TOKEN no WAHA e o WAHA_AUTH_TOKEN no Django são iguais e estão corretos.")
            return None

        