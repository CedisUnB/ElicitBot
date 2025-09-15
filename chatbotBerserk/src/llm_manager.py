import requests
from datetime import datetime
#------------------------
#------------------------
#------------------------

class LLMManager:
    def __init__(self):
        self.chat_history = []
        self.model = "deepseek-r1:32b"
        self.requirements = []
        self.current_context = {
            'funcionalidade': '',
            'objetivo': '',
            'regras_negocio': [],
            'criterios_aceitacao': []
        }

    def _get_system_prompt(self):
        return """Você é um analista de requisitos experiente conduzindo uma sessão de elicitação de requisitos.

Definições importantes:
- Requisito Funcional: uma funcionalidade que o sistema deve oferecer para atender aos objetivos do usuário.
- História de Usuário: uma descrição curta de uma funcionalidade sob a perspectiva do usuário, no formato "Como [tipo de usuário], quero [funcionalidade] para [benefício]".
- Regra de Negócio: diretrizes ou condições que determinam ou restringem o funcionamento do sistema.
- Critério de Aceitação: condições claras que devem ser atendidas para que o requisito seja considerado completo e aceito.


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
8. Conduza a conversa para conseguir identificar mais requisitos"""

# Ao final de cada conversa sobre um requisito, você deve:
# 1. Resumir o requisito identificado
# 2. Listar as regras de negócio associadas
# 3. Definir os critérios de aceitação

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
                'http://ollama.labssc.com/api/chat',
                headers={'Content-Type': 'application/json',
                         "X-API-Key": "Ollama_IA_2025#"},
                json={
                    'model': self.model,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'stream': True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'content' in data['message']:
                    return data['message']['content']
            
            return None
        except:
            return None

    def process_message(self, user_input):
        """Processa a mensagem do usuário, extrai requisitos e retorna uma resposta."""
        messages = [
            {"role": "system", "content": self._get_system_prompt()}
        ] + self.chat_history + [
            {"role": "user", "content": user_input}
        ]

        try:
            response = requests.post(
                'http://ollama.labssc.com/api/chat',
                headers={'Content-Type': 'application/json',
                         "X-API-Key": "Ollama_IA_2025#"},
                json={
                    'model': self.model,
                    'messages': messages,
                    'stream': False
                }
            )
            
            if response.status_code != 200:
                return f"❌ Erro na API do Ollama: {response.text}"
            
            try:
                data = response.json()
                if 'message' not in data or 'content' not in data['message']:
                    return "❌ Resposta inválida do Ollama"
                
                content = data['message']['content']
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
            return f"❌ Erro ao conectar com Ollama: {str(e)}"

    def get_requirements(self):
        """Retorna os requisitos extraídos até o momento."""
        return self.requirements
