#!/usr/bin/env python3
"""
Worker independente para processar fila do WhatsApp - VERSÃO CORRIGIDA
"""
import os
import sys
import logging
import redis
import django

# Configura Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot.settings')
django.setup() 

from chatbot_api.services.redis_client import (
    update_session_state,
    add_message_to_history, get_recent_history,
    publish_new_user, enqueue_user, get_redis_client
)
from chatbot_api.services.waha_api import Waha

# Configurações
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0)),
    'decode_responses': True
}

waha_api = Waha()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("whatsapp-worker")

class WhatsAppWorker:
    def __init__(self):
        self.redis_client = None
        self.setup_connections()
        self.redis_client = get_redis_client()
        
    def setup_connections(self):
        """Estabelece conexões com Redis e WAHA API"""
        try:
            # 🔥 CORREÇÃO: Usa a função do service padronizada
            self.redis_client = get_redis_client()
            self.redis_client.ping()
            
        except Exception as e:
            logger.error(f"❌ Erro na configuração do Worker: {e}")
            raise

    def process_user_message(self, chat_id: str):
        """Processa a mensagem do usuário COM ATUALIZAÇÃO DE ESTADO E RESPOSTA"""
        try:
            
            update_session_state(chat_id, step="EM_ATENDIMENTO")
            logger.info(f" Estado atualizado para EM_ATENDIMENTO: {chat_id}")
            
            # Busca histórico completo
            history = get_recent_history(chat_id, limit=10)
            
            # Futuro invoke
            response = self.generate_response(chat_id, history)
            logger.info(f"Resposta gerada: {response}")
            
            # ENVIA RESPOSTA via WAHA
            waha_api.send_whatsapp_message(chat_id, response)
            logger.info(f"Resposta enviada via WAHA: {chat_id}")
            
            # SALVA RESPOSTA NO HISTÓRICO
            add_message_to_history(chat_id, "Bot", response)
            
            logger.info(f"Processamento concluído para: {chat_id}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar {chat_id}: {e}", exc_info=True)
            # Re-adiciona na fila em caso de erro
            try:
                enqueue_user(chat_id)
                publish_new_user(chat_id)
                logger.info(f"🔄 Usuário re-adicionado na fila: {chat_id}")
            except Exception as retry_error:
                logger.error(f"💥 Erro ao re-adicionar na fila: {retry_error}")

    def generate_response(self, chat_id: str, history: list) -> str:
        """Gera resposta baseada no histórico"""
        # Lógica simples - FUTURO: substituir por LLM
        user_messages = [msg for msg in history if "[User]:" in msg]
        
        # Simulação de logica (Futura implementação agente de ia com Groq)
        if not user_messages:
            return "Olá! Em que posso ajudar?"
            
        last_user_message = user_messages[0].lower()
        if "pedido" in last_user_message:
            return "Olá! Verifiquei seu pedido e ele está em processamento. Previsão de entrega: 2 dias úteis."
        elif "preço" in last_user_message or "valor" in last_user_message:
            return "Posso ajudar com informações de preços! Nosso atendente especializado entrará em contato."
        elif "obrigado" in last_user_message or "obrigada" in last_user_message:
            return "Por nada! Estamos aqui para ajudar. Precisa de mais alguma coisa?"
        else:
            return "Obrigado por entrar em contato! Estou transferindo você para nosso atendente especializado que responderá em instantes."

    def listen_queue(self):
        """Fica escutando notificações da fila via Redis Pub/Sub"""
        logger.info("🔊 Iniciando worker - Escutando fila Pub/Sub...")
        
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe("new_user_queue")
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                chat_id = message['data']
                logger.info(f"📨 Nova notificação recebida: {chat_id}")
                self.process_user_message(chat_id)

    def run(self):
        """Método principal do worker"""
        logger.info("🚀 WhatsApp Worker INICIADO - Versão Corrigida")
        try:
            self.listen_queue()
        except KeyboardInterrupt:
            logger.info("⏹️ Worker interrompido pelo usuário")
        except Exception as e:
            logger.error(f"💥 Erro fatal no worker: {e}")
            raise

if __name__ == "__main__":
    worker = WhatsAppWorker()
    worker.run()