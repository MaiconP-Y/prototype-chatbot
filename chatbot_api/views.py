import json 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import logging
from chatbot_api.services.waha_api import Waha
from chatbot_api.services.redis_client import (
    get_session_state, 
    update_session_state,
    add_message_to_history,
    enqueue_user,
    is_user_in_queue,
    publish_new_user,  # NOVA IMPORT
) 

waha = Waha()
logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def webhook(request):
    """
    Webhook otimizado - focado em resposta rápida e notificação assíncrona
    """
    try:
        main_data = json.loads(request.body)
        message_data = main_data.get("payload", {})

        chat_id = message_data.get("from")
        message = message_data.get("body", "").strip().lower() 
        
        # 1. Salva mensagem no histórico (rápido)
        add_message_to_history(chat_id, "User", message)
        logger.info(f"📝 Mensagem {message} de {chat_id} salva")

        # 2. Recupera estado da sessão
        session_state = get_session_state(chat_id)
        current_step = session_state.get('step', 'INICIO') if session_state else 'INICIO'

        logger.info(f"🔍 Estado de {chat_id}: {current_step}")

        if current_step == "EM_ATENDIMENTO":
            
            publish_new_user(chat_id) # Worker pega a mensagem e continua a conversa
            return JsonResponse({"status": "success", "step": current_step})
        
        elif current_step == "IN_QUEUE":
            # 3.2. Usuário na Fila (Mas o worker ainda não o pegou)
            # Resposta mínima e notificação para que o worker saiba que o usuário
            # enviou mais uma mensagem e processe o estado de IN_QUEUE -> EM_ATENDIMENTO.
            resposta = "Você já está na fila. Sua nova mensagem será processada em breve."
            waha.send_whatsapp_message(chat_id, resposta)
            add_message_to_history(chat_id, "Bot", resposta)
            return JsonResponse({"status": "success", "step": current_step})

        elif not is_user_in_queue(chat_id): 
            # 3.3. NOVO USUÁRIO (Estado: INICIO, e não está na lista da fila)
            new_step = "IN_QUEUE"
            queue_position = enqueue_user(chat_id)
            
            resposta = f" Você está na fila. Posição: {queue_position}. Aguarde o atendimento."
            waha.send_whatsapp_message(chat_id, resposta)
            add_message_to_history(chat_id, "Bot", resposta)
            
            update_session_state(chat_id, step=new_step) # Atualiza o estado
            if queue_position == 1:
                publish_new_user(chat_id) # Notifica o worker para iniciar o processamento
                logger.info("Worker notificado. Novo usuário é o primeiro.")
            return JsonResponse({"status": "success", "step": current_step})
        return JsonResponse({"status": "success", "step": current_step})
                
    
    except Exception as e:
        logger.error(f"❌ Erro no webhook: {e}", exc_info=True)
        return JsonResponse({"error": "Internal server error"}, status=500)