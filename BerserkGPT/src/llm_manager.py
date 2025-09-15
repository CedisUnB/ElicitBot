import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class LLMManager:
    def __init__(self):
        self.chat_history = []
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("API key do OpenAI não encontrada no arquivo .env")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4-turbo-preview"  # Modelo mais recente do GPT-4
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
8. Conduza a conversa para conseguir identificar mais requisitos

Ao final de cada conversa sobre um requisito, você deve:
1. Resumir o requisito identificado
2. Listar as regras de negócio associadas
3. Definir os critérios de aceitação"""

    def _extract_requirements(self, conversation):
        """Extrai requisitos da conversa usando o modelo."""
        messages = [
            {
                "role": "system",
                "content": """Você é um analista de requisitos especializado em extrair requisitos de software.
Sua tarefa é analisar a conversa e extrair informações estruturadas sobre os requisitos discutidos.
Seja preciso e objetivo na extração das informações."""
            },
            {
                "role": "user",
                "content": """Analise a conversa a seguir e extraia as informações no formato especificado:

CONVERSA:
{conversation}

EXTRAIA E FORMATE AS INFORMAÇÕES ASSIM:
[Requisito Principal]
Descreva em uma frase clara e objetiva o requisito principal identificado.

[História de Usuário]
Como: [especifique o papel/tipo de usuário]
Quero: [descreva a funcionalidade específica]
Para: [explique o benefício/valor obtido]

[Regras de Negócio]
- Liste cada regra de negócio identificada
- Seja específico e objetivo
- Use linguagem clara

[Critérios de Aceitação]
- Liste cada critério que deve ser atendido
- Seja específico e verificável
- Use formato 'Dado/Quando/Então' quando apropriado"""
            }
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,  # Reduzindo a temperatura para respostas mais consistentes
                presence_penalty=0.0,
                frequency_penalty=0.0,
                max_tokens=1000
            )
            
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
            
            return None
        except Exception as e:
            print(f"Erro ao extrair requisitos: {str(e)}")
            return None

    def process_message(self, user_input):
        """Processa a mensagem do usuário, extrai requisitos e retorna uma resposta."""
        messages = [
            {
                "role": "system",
                "content": self._get_system_prompt()
            }
        ]
        
        # Adiciona o histórico da conversa
        messages.extend([
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.chat_history
        ])
        
        # Adiciona a mensagem atual do usuário
        messages.append({"role": "user", "content": user_input})

        try:
            # Faz a requisição para a API do OpenAI com parâmetros otimizados
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,  # Reduzindo para respostas mais consistentes
                presence_penalty=0.0,
                frequency_penalty=0.3,  # Encoraja alguma variação no vocabulário
                max_tokens=1000
            )
            
            if not response.choices:
                return "❌ Resposta inválida do GPT"
            
            content = response.choices[0].message.content
            self.chat_history.extend([
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": content}
            ])

            # Tenta extrair requisitos da conversa após cada interação
            if len(self.chat_history) >= 2:  # Reduzindo para começar mais cedo
                conversation = "\n".join([
                    f"{msg['role'].upper()}: {msg['content']}"
                    for msg in self.chat_history[-4:]
                ])
                requirements = self._extract_requirements(conversation)
                if requirements:
                    self.requirements.append({
                        'conversation': conversation,
                        'analysis': requirements,
                        'timestamp': datetime.now().isoformat()
                    })
            
            return content
                
        except Exception as e:
            return f"❌ Erro ao conectar com GPT: {str(e)}"

    def get_requirements(self):
        """Retorna os requisitos extraídos até o momento."""
        return self.requirements
