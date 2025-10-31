# WhatsApp Session Manager 🚀

**Protótipo Ativo - Mantido e Atualizado Regularmente**

## Escopo do Protótipo

Este é um protótipo funcional de um sistema de gerenciamento de sessões e filas para WhatsApp API (com WAHA, mas customizável), focado em **estabilidade** e **escalabilidade**.

---

### ⚡ **NOVA ARQUITETURA E FUNCIONALIDADES PRINCIPAIS (Out/2025)**

A arquitetura foi atualizada para um sistema de mensagens assíncrono robusto, garantindo que o processamento das mensagens não trave e acione os Workers instantaneamente.

| Funcionalidade | Detalhes |
| :--- | :--- |
| **Comunicação Estável** | Substituição do modelo anterior por **Redis Pub/Sub** para gerenciamento de mensagens assíncronas e acionamento instantâneo do Worker. |
| **Gestão de Estado** | Persistência do estado da conversa por usuário (onde o usuário parou). |
| **Atendimento Organizado** | **Controle de Estado, Histórico e Gerenciamento de Fila** que ordena as conversas e envia **notificações de posição na fila** para o usuário. |
| **Histórico de Conversas** | Armazenamento completo do histórico de mensagens. |
| **Webhook Escalável** | Processamento assíncrono de mensagens do WhatsApp. |

---

## Arquitetura Atual

O sistema opera com um fluxo assíncrono de comunicação e um Worker dedicado:

* **Fluxo de Mensagens:** WhatsApp Webhook → Django → Redis **(Pub/Sub)** → **Worker (Processamento)** → WAHA API.
* **Nota Técnica:** Atualmente, o Worker é configurado para atender 1 usuário por vez, mas a arquitetura já está pronta e provada para **escalar com múltiplos Workers** (processos) consumindo a fila simultaneamente.

### Stack Tecnológica
* **Backend:** Django 4.2+
* **Banco de Sessão:** Redis
* **Mensageria:** Redis Pub/Sub e Sistema de Filas integrado
* **API WhatsApp:** WAHA (WhatsApp HTTP API)
* **Containerização:** Docker & Docker Compose

### Próximo Passo

Implementação da **lógica do Agente de IA** que utilizará as informações de Histórico e Estado da Sessão para agendar consultas e processar respostas inteligentes.

### Objetivo Final
Criar uma base sólida e atualizada para sistemas de chatbots empresariais escaláveis, servindo como referência para implementações em produção.