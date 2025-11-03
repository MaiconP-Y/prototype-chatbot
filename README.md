# WhatsApp Session Manager 

**Protótipo Ativo - Mantido e Atualizado Regularmente**

## Escopo do Protótipo

Este é um protótipo funcional de um sistema de gerenciamento de sessões e filas para WhatsApp API (com WAHA, mas customizável), focado em estabilidade e escalabilidade.

## ⚡ NOVA ARQUITETURA E FUNCIONALIDADES PRINCIPAIS (Out/2025)

A arquitetura foi atualizada para um sistema de mensagens assíncrono robusto, garantindo que o processamento das mensagens não trave e acione os Workers instantaneamente.

| Funcionalidade | Detalhes |
|----------------|-----------|
| **Comunicação Estável** | Substituição do modelo anterior por Redis Pub/Sub para gerenciamento de mensagens assíncronas e acionamento instantâneo do Worker. |
| **Gestão de Estado** | Persistência do estado da conversa por usuário (onde o usuário parou). |
| **Atendimento Organizado** | Controle de Estado, Histórico e Gerenciamento de Fila que ordena as conversas e envia notificações de posição na fila para o usuário. |
| **Histórico de Conversas** | Armazenamento completo do histórico de mensagens. |
| **Webhook Escalável** | Processamento assíncrono de mensagens do WhatsApp. |
| **Segurança HMAC** | **CRÍTICO:** Todas as requisições de Webhook são validadas com HMAC-SHA512 para garantir que apenas o servidor WAHA autêntico possa se comunicar com o Django. |

## Segurança e Integridade do Webhook

A integridade do sistema é garantida pela validação de cada requisição HTTP POST recebida pelo Webhook:

1.  **Assinatura HMAC:** O servidor WAHA assina o corpo de cada requisição (payload) usando a chave secreta (`WEBHOOK_HMAC_SECRET`) com o algoritmo **SHA512**.
2.  **Validação de Integridade:** O Django lê o corpo da requisição e o cabeçalho `X-Webhook-Hmac`. Ele recalcula o HMAC usando a chave secreta de ambiente e compara as assinaturas.
3.  **Bloqueio de Ataques:** Qualquer requisição com assinatura inválida (simulação de ataque ou erro de configuração) é imediatamente bloqueada com o código **403 Forbidden** e um aviso de segurança é registrado no log.

## Arquitetura Atual

O sistema opera com um fluxo assíncrono de comunicação e um Worker dedicado:

**Fluxo de Mensagens:** `WhatsApp Webhook → (Validação HMAC) → Django → Redis (Pub/Sub) → Worker (Processamento) → WAHA API`

**Nota Técnica:** Atualmente, o Worker é configurado para atender 1 usuário por vez, mas a arquitetura já está pronta e provada para escalar com múltiplos Workers (processos) consumindo a fila simultaneamente.

## Stack Tecnológica

- **Backend:** Django 4.2+
- **Banco de Sessão:** Redis
- **Mensageria:** Redis Pub/Sub e Sistema de Filas integrado
- **API WhatsApp:** WAHA (WhatsApp HTTP API)
- **Containerização:** Docker & Docker Compose