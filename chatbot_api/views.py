from django.shortcuts import render
import json 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def webhook(request):
    """
    Webhook endpoint for WhatsApp Business API integration.
    
    Processes incoming messages and returns immediate acknowledgment
    to prevent timeouts in the WhatsApp ecosystem.
    """
    try:
        main_data = json.loads(request.body)
            
        message_data = main_data.get("payload", {})
        
        print(message_data)

        return JsonResponse({"status": "success", "message": "Payload accepted for processing."})
    except json.JSONDecodeError:
        logger.error(f"ERRO DE JSON: Dados recebidos não são um JSON válido. Corpo: {request.body[:200]}...", exc_info=True)
        return JsonResponse({"error": "Invalid JSON format in request body"}, status=400)

    except Exception as e:
        logger.error(f"Erro inesperado no webhook: {e}", exc_info=True)
        return JsonResponse({"error": "Internal server error"}, status=500)
