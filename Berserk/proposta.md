Solução

	- Chatbot que realiza elicitação de requisitos, ou seja, que conversa com o stakeholder para entender o problema e extrair os requisitos do sistema


Restrições necessárias do chatbot

A ideia inicial é definir um domínio específico em qual o chat  vai atuar, estou pensando em treinar para o contexto de e-commerce( mas poderíamos criar um contexto específico pare a saúde ,  para educação, ou qualquer outro), mas o importante é que nesses primeiros passos do chat ele seja voltado para um domínio específico para podermos explorar as outras funcionalidades mais importantes que falarei a seguir  

O segundo objetivo é fazer com que ele lide com apenas requisitos funcionais( e no futuro adaptarmos para os não funcionais também), tendo como output os requisitos no formato de User stories

Outra limitação que iremos colocar é que estaremos sempre tratando de soluções em sistemas WEB 



Estrutura do chat 

Modelos LLMs( aqui poderá variar , ainda faremos a decisão de qual modelo melhor poderá se desempenhar aqui)  
Tamanho (quantidade de parâmetros) e capacidade de rodar localmente


Baixa taxa de alucinação.


Capacidade de manter contexto em interações multi-turn.


Open Source preferencialmente.


langGraph/LangChain( ajudar a definir o fluxo da conversa e criar um sistema de feedback para o usuário ajudar a avaliar a resposta do modelo e assim ele conseguir treinar suas respostas a partir do uso)
Sistema de Feedbacks, para  o desenvolvimento o sistema de feedbacks será baseado no estrutura de Util ou não util, ou seja, após gerar a user Storie tera dois emoticons um joinha positivo e um negativo e ao selecionar um deles enviaram um feedback para a máquina  👎 👍 





Fluxo Sugerido


Chatbot    Exemplo




Saudação + explicação da tarefa "Olá! Estou aqui para te ajudar a definir as funcionalidades do seu sistema de e-commerce. Vamos começar?


Pergunta por uma funcionalidade esperada Qual funcionalidade você gostaria que o seu site tivesse?"

Pergunta por objetivo Legal. E para que serve essa funcionalidade?


Pergunta pelo usuário beneficiado   Quem vai usar essa funcionalidade? Um cliente, administrador...?

Geração de User Story

Feedback

Avaliação de Feedback


Interface do chat eu quero utilizar o Streamlit  



 salvar as user stories em um excel ou docs

id": "US01",
  "titulo": "Adicionar produto ao carrinho",
  "role": "usuário",
  "Eu quero": "adicionar um produto ao carrinho de compras",
  "Para": "possa finalizar minha compra posteriormente"


Cada coluna no excel / xlsx com um id, titulo etc…

Em relação a escalabilidade ele vai salvar uma planilha  para o MVP e em um futuro a gente realiza a integração com um banco mais complexo , seja um PostgreSQL ou algo assim

Extra: eu quero adicionar a tecnologia speach-to-speach, após a realização do MVP e para isso pretendo utilizar alguma tecnologia S2S open source , porém este tipo de modelo não está tão preciso, caso necessário utilizaremos o da google cloud é pago , mas é mais robusto 




Possiveis Problemas

Falas ambíguas e utilizações de palavras genéricas( utilizaremos um fluxo para identificar algumas dessas situações e moldar o chat para contar isso, ex: o que você gostaria de falar com “produto bom”,)
1
Se o usuário disser “quero um sistema bom”, o chatbot pergunta:
2
O que você quis dizer com ‘bom’? Você está falando de facilidade de uso, segurança ou outra coisa?”
3
Banco de termos: Palavras como bom, rápido, intuitivo, melhor serão reconhecidas e o bot pedirá especificação.
4
O chat gera uma sugestão ao se deparar com isso 
5
Quando você diz ‘um bom processo de pagamento’, você gostaria de algo como pagamento em um clique ou integração com várias bandeiras de cartão?”

 

Fluxo conversacional quebrado A IA pode pular etapas, repetir perguntas ou sair do contexto Isso pode confundir ou cansar o usuário( feedbacks do usuário ajudarão a resolver esse problema)

Alucinações, é muito comum este tipo de solução alucinar bastante, por isso as restrições indicadas no começo do documento são muito importantes para esse início de desenvolvimento , para limitarmos o escopo e irmos adaptando com o passar do tempo reduzindo assim as alucinações 
Limitações do Speach-to-Speach, reconhecimento semântico e de voz, e gastos com modelos que exigem a licença de uso , tendo isso em vista pretendo trabalhar nesse quesito após o MVP estiver concluído


Diferenciais de outros modelos



diferente de outros LLMs , o chat seguirá um fluxo de conversa o que guiará o usuário, sem deixá-lo perdido 

 as conversas serão personalizadas e adaptadas para este tipo de tarefa,(elicitação de requisitos, gerando user stories)

Domínio especializado, fará perguntas guiadas baseado no domínio tratado( a priori e-commerce) 

Sua forma de aprender com os erros é mais eficaz, pois ele utiliza as interações multi-turn

Geração automática de artefatos(documentos com as user stories )

Integração com voz (Implementação após o MVP estiver pronto)

Adaptável por domínio e empresa







MVP: Criar um chatbot simples que:

Faça perguntas sobre requisitos funcionais  de um sistema de e-commerce.

Armazene as respostas do usuário.

Gera um resumo básico ou um documento com os requisitos coletados.
 
Receba feedback de cada resposta (útil ou não útil).  👎 👍




Critérios de Sucesso

A avaliação do desempenho do chatbot na elicitação de requisitos será feita com base em métricas claras e objetivas, considerando tanto a forma quanto a qualidade das user stories geradas.
1. Aderência ao Padrão de Formato
Métrica: Percentual de user stories geradas no formato padrão:
 "Como [usuário], eu quero [objetivo] para [benefício]"
EXEMPLO: Meta de sucesso: Alcançar ao menos 85% de user stories com estrutura válida, demonstrando entendimento correto do modelo esperado.
2. Avaliação com INVEST
As user stories geradas serão analisadas conforme os critérios do framework INVEST:
Independente
Negociável
Valiosa
Estimável
Simples (Small)
Testável


Métrica: Cada critério será avaliado de forma qualitativa por avaliadores humanos, ou semi automaticamente via checklist.
EXEMPLO: Meta de sucesso: Pelo menos 80% das user stories devem atender a 5 ou mais critérios INVEST.
3. Avaliação com QUS Framework (Lucassen et al.)
As user stories também serão analisadas com base nos 13 critérios de qualidade linguística definidos pelo QUS Framework, agrupados em três categorias:
SINTÁTICOS
Bem-formada: Inclui papel e meio.
Atômica: Refere-se a uma única funcionalidade.
Minimalista: Contém apenas papel, meio e fim.
SEMÂNTICOS
Conceitualmente coerente: Meio expressa funcionalidade e fim expressa justificativa.
Orientada ao problema: Não apresenta soluções.
Não ambígua: Livre de termos genéricos ou vagos.
Livre de conflitos: Sem contradições com outras user stories.
PRAGMÁTICOS
Frase completa: Estrutura gramatical correta.
Estimável: Clara o suficiente para estimativas.


Única: Sem repetições.
Uniforme: Segue o mesmo modelo/template das demais.
Independente: Sem dependências explícitas.
Completa: Conjunto de histórias gera sistema funcional.
Métrica: Percentual de user stories que atendem a ao menos 10 dos 13 critérios.
EXEMPLO: Meta de sucesso: Atingir no mínimo 75% de conformidade com os critérios do QUS Framework.
4. Feedback do Usuário
O chatbot deve coletar feedback após cada resposta, classificando-a como útil ou não útil.
Métrica: Percentual de respostas avaliadas como úteis.
EXEMPLO: Meta de sucesso: Obter mínimo de 80% de respostas úteis, indicando que o fluxo está adequado à compreensão do usuário.
