import redis
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# O objeto cliente será armazenado globalmente AQUI, mas inicializado como None
_redis_client = None 

# --- A Conexão Lazy (O Padrão Ouro) ---

def get_redis_client():
    """
    Inicializa e retorna o cliente Redis de forma lazy (sob demanda) e segura.
    Implementa o padrão Singleton: cria a conexão apenas uma vez por processo.
    """
    global _redis_client
    
    # 1. Se já estiver conectado, retorna a conexão existente imediatamente
    if _redis_client is not None:
        return _redis_client

    # 2. Tenta conectar pela primeira vez (o settings já estará carregado aqui)
    try:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST, 
            port=settings.REDIS_PORT, 
            db=settings.REDIS_DB,
            decode_responses=True, 
            socket_connect_timeout=5, 
            socket_timeout=5,
        )
        _redis_client.ping()
        logger.info("Conexão com Redis estabelecida com sucesso via get_redis_client!")
        return _redis_client
        
    except Exception as e:
        _redis_client = None
        logger.error(f"Erro CRÍTICO ao conectar ao Redis: {e}", exc_info=True)
        # É importante levantar um erro se a conexão for vital
        raise ConnectionError(f"Falha na inicialização do cliente Redis: {e}") 


# --- Chaves de Redis (Permanecem iguais) ---
QUEUE_KEY = "queue:support"

# --- Funções de Fila (Todas devem usar get_redis_client()) ---

def enqueue_user(chat_id: str) -> int:
    """Adiciona o chat_id na fila e NOTIFICA O WORKER."""
    r = get_redis_client() # <<< OBTÉM A CONEXÃO AQUI
    new_size = r.rpush(QUEUE_KEY, chat_id)
    
    logger.info(f"Usuário {chat_id} adicionado à fila e notificação enviada.")
    return new_size

def is_user_in_queue(chat_id: str) -> bool:
    """Verifica se o usuário já está na fila."""
    r = get_redis_client() # <<< OBTÉM A CONEXÃO AQUI
    return chat_id in set(r.lrange(QUEUE_KEY, 0, -1))

def get_next_from_queue() -> str:
    """Remove e retorna o próximo usuário da fila (BLOCKING)"""
    r = get_redis_client()
    # Bloqueia até 30 segundos esperando um usuário
    result = r.blpop(QUEUE_KEY, timeout=30)
    if result:
        chat_id = result[1]
        logger.info(f"🎯 Próximo usuário da fila: {chat_id}")
        return chat_id
    return None

# --- Funções Pub/Sub para Comunicação com Worker ---

def publish_new_user(chat_id: str):
    """Publica notificação de novo usuário na fila via Redis Pub/Sub"""
    r = get_redis_client()
    r.publish("new_user_queue", chat_id)
    logger.info(f"📢 Notificação Pub/Sub enviada para usuário {chat_id}")

# --- Funções de Histórico (Todas devem usar get_redis_client()) ---

def get_history_key(chat_id: str) -> str:
    return f"history:{chat_id}"

def add_message_to_history(chat_id: str, sender: str, message: str) -> int:
    """Adiciona uma mensagem ao histórico do usuário (Bot ou User)."""
    r = get_redis_client() # <<< OBTÉM A CONEXÃO AQUI
    message_entry = f"[{sender}]: {message}"
    return r.lpush(get_history_key(chat_id), message_entry)

def get_recent_history(chat_id: str, limit: int = 10) -> list:
    """Retorna as N mensagens mais recentes do histórico."""
    r = get_redis_client() # <<< OBTÉM A CONEXÃO AQUI
    history = r.lrange(get_history_key(chat_id), 0, limit - 1)
    return history[::-1] 

def get_full_history(chat_id: str) -> list:
    """Retorna todo o histórico de mensagens (mais recente primeiro)"""
    r = get_redis_client()
    history = r.lrange(get_history_key(chat_id), 0, -1)
    return history[::-1]

# --- Funções de Estado de Sessão (Todas devem usar get_redis_client()) ---

def get_session_key(chat_id: str) -> str:
    return f"session:{chat_id}"

def get_session_state(chat_id: str) -> dict:
    """Recupera os dados de estado da sessão do usuário."""
    r = get_redis_client() # <<< OBTÉM A CONEXÃO AQUI
    state = r.hgetall(get_session_key(chat_id))
    return state

def update_session_state(chat_id: str, **kwargs):
    """Atualiza estado da sessão"""
    r = get_redis_client()
    session_key = f"session:{chat_id}"
    
    for field, value in kwargs.items():
        r.hset(session_key, field, str(value))
    
    logger.info(f"Estado atualizado: {chat_id} -> {kwargs}")

def set_session_ttl(chat_id: str, ttl_seconds: int = 3600):
    """Define TTL (Time To Live) para a sessão (padrão: 1 hora)"""
    r = get_redis_client()
    r.expire(get_session_key(chat_id), ttl_seconds)
    logger.info(f"⏰ TTL de {ttl_seconds}s definido para sessão de {chat_id}")