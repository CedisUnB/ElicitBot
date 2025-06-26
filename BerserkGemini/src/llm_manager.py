import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class LLMManager:
    def __init__(self):
        self.chat_history = []
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("API key do Gemini não encontrada no arquivo .env")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.requirements = []
        self.current_context = {
            'funcionalidade': '',
            'objetivo': '',
            'regras_negocio': [],
            'criterios_aceitacao': []
        }

    def _get_system_prompt(self):
        return """Você é um analista de requisitos experiente conduzindo uma sessão de elicitação de requisitos.

Seu objetivo é:
1. Extrair requisitos funcionais da conversa
2. Identificar regras de negócio
3. Definir critérios de aceitação
4. Manter o foco em um requisito por vez

Siga estas diretrizes:
1. Faça perguntas objetivas e focadas
2. Evite jargão técnico
3. Quando identificar ambiguidades, peça esclarecimentos
4. Explore o POR QUE de cada requisito
5. Valide seu entendimento repetindo o que foi dito
6. Mantenha um tom profissional mas amigável
7. Explore não só O QUE o stakeholder quer, mas POR QUE ele quer
8. Conduza a conversa para conseguir identificar mais requisitos

Ao final de cada conversa sobre um requisito, você deve:
1. Resumir o requisito identificado
2. Listar as regras de negócio associadas
3. Definir os critérios de aceitação"""

    def _extract_requirements(self, conversation):
        """Extrai requisitos da conversa usando o modelo."""
        prompt = f"""Com base na conversa a seguir, extraia:
        1. O requisito principal
        2. As regras de negócio
        3. Os critérios de aceitação
        4. Uma história de usuário no formato "Como [papel], quero [funcionalidade] para [benefício]"

Conversa:
{conversation}

Responda no formato:
Requisito: [requisito identificado]

História de Usuário:
Como [papel do usuário]
Quero [funcionalidade desejada]
Para [benefício esperado]

Regras de Negócio:
- [regra 1]
- [regra 2]

Critérios de Aceitação:
- [critério 1]
- [critério 2]"""

        try:
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers={'Content-Type': 'application/json'},
                json={
                    'contents': [{
                        'parts': [{
                            'text': prompt
                        }]
                    }]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('candidates') and data['candidates'][0].get('content'):
                    return data['candidates'][0]['content']['parts'][0]['text']
            
            return None
        except:
            return None

    def process_message(self, user_input):
        """Processa a mensagem do usuário, extrai requisitos e retorna uma resposta."""
        # Prepara o contexto completo com o histórico
        context = self._get_system_prompt() + "\n\nHistórico da conversa:\n"
        for msg in self.chat_history:
            context += f"{msg['role']}: {msg['content']}\n"
        context += f"\nUsuário: {user_input}"

        try:
            # Faz a requisição para a API do Gemini
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers={'Content-Type': 'application/json'},
                json={
                    'contents': [{
                        'parts': [{
                            'text': context
                        }]
                    }]
                }
            )
            
            if response.status_code != 200:
                return f"❌ Erro na API do Gemini: {response.text}"
            
            try:
                data = response.json()
                if not data.get('candidates') or not data['candidates'][0].get('content'):
                    return "❌ Resposta inválida do Gemini"
                
                content = data['candidates'][0]['content']['parts'][0]['text']
                self.chat_history.extend([
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "content": content}
                ])

                # Tenta extrair requisitos da conversa
                if len(self.chat_history) >= 4:  # Após algumas mensagens
                    conversation = "\n".join([msg["content"] for msg in self.chat_history[-4:]])
                    requirements = self._extract_requirements(conversation)
                    if requirements:
                        self.requirements.append({
                            'conversation': conversation,
                            'analysis': requirements,
                            'timestamp': datetime.now().isoformat()
                        })
                
                return content
                
            except ValueError as e:
                return f"❌ Erro ao processar JSON: {str(e)}"
            
        except Exception as e:
            return f"❌ Erro ao conectar com Gemini: {str(e)}"

    def get_requirements(self):
        """Retorna os requisitos extraídos até o momento."""
        return self.requirements
