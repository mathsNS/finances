"""streamlit_app.py

Aplicação Streamlit que serve como GUI para o Chatbot Financeiro Inteligente.
"""
import streamlit as st
from chatbot import ChatBot
from collections import Counter
import json
import os

st.set_page_config(page_title="Chatbot Financeiro Inteligente", layout='centered')

# utilitarios de ajuda
def load_counters(path='data/counters.json'):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"formal":0, "engracado":0, "rude":0}

def save_report(chatbot: ChatBot, session_state):
    # gerar o report file do sumario
    total = session_state.get('interactions', 0)
    questions = session_state.get('questions', [])
    if questions:
        most_common = Counter(questions).most_common(1)[0][0]
    else:
        most_common = ''
    report = []
    report.append(f"Total de interações nesta sessão: {total}")
    report.append(f"Pergunta mais frequente da sessão: {most_common}")
    report.append("Contador acumulado de personalidades:")
    report.append(json.dumps(chatbot.counters, ensure_ascii=False, indent=2))
    report.append("Últimas interações (persistidas):")
    last = chatbot.get_last_history(10)
    for u,b in last:
        report.append(f"Q: {u}\nA: {b}\n")
    report_text = '\n\n'.join(report)
    with open('data/summary.txt', 'w', encoding='utf-8') as f:
        f.write(report_text)
    return 'data/summary.txt'

# UI principal (frase do "cabeçalho")
st.title(' Chatbot Financeiro Inteligente')
st.markdown('Disponível 24/7 — registre gastos, tire dúvidas e aprenda sobre finanças.')

# iniciar o bot instantaneamente 
chat = ChatBot()

# mostrar as ultimas 5 interações
st.sidebar.header('Configuração')
personality = st.sidebar.selectbox('Escolha a personalidade', ['formal','engracado','rude'])
if 'session_questions' not in st.session_state:
    st.session_state['session_questions'] = []
if 'personality' not in st.session_state:
    st.session_state['personality']='formal'
if 'interactions' not in st.session_state:
    st.session_state['interactions'] = 0
if 'learning_q' not in st.session_state:
    st.session_state['learning_q']=None
if 'questions' not in st.session_state:
    st.session_state['questions']=[]    

st.sidebar.markdown('**Últimas 5 interações (persistidas):**')
last5 = chat.get_last_history(5)
if last5:
    for q,a in last5:
        st.sidebar.write(f'- **Q:** {q} → **A:** {a}')
else:
    st.sidebar.write('Nenhuma interação anterior encontrada.')

# contador das personalidades 
st.sidebar.markdown('**Uso de personalidades (acumulado):**')
counters = chat.counters
st.sidebar.write(counters)

st.markdown('### Converse com o chatbot')
col1, col2 = st.columns([3,1])
with col1:
    user_input=st.text_input("Digite sua pergunta:")
    if st.button("Enviar"):
        if st.session_state['learning_q']:
            st.warning("Finalize o aprendizado antes de nova pergunta.")
        else:
            st.session_state['questions'].append(user_input)
            ans=chat.answer(user_input,st.session_state['personality'])
            if ans is None:
                st.session_state['learning_q']=user_input
                st.info("Não sei responder. Ensine-me abaixo ")
            else:
                chat.register_interaction(user_input,ans)
                st.write(ans)

    if st.session_state['learning_q']:
        resp=st.text_area("Escreva a resposta para ensinar:",key="teach_area")
        if st.button("Salvar resposta"):
            chat.learn(st.session_state['learning_q'],resp)
            ans=chat.answer(st.session_state['learning_q'],st.session_state['personality'])
            chat.register_interaction(st.session_state['learning_q'],ans)
            st.success("Resposta aprendida!")
            st.write(ans)
            st.session_state['learning_q']=None

if user_input.strip():
    st.session_state['interactions'] += 1
    st.session_state['session_questions'].append(user_input.strip())
    #checar comms de historico, relatorio e trocar personalidade
    low = user_input.lower()
    if low.startswith('histórico') or low.startswith('historico'):
        st.write('Histórico (últimas interações persistidas):')
        for q,a in chat.get_last_history(50):
            st.write(f'Q: {q} → A: {a}')
    elif low.startswith('relatório') or low.startswith('relatorio') or low.startswith('gerar relatorio'):
        path = save_report(chat, st.session_state)
        st.success('Relatório gerado.')
        with open(path, 'r', encoding='utf-8') as f:
            st.text(f.read())
        st.download_button('Baixar relatório', path, file_name='summary.txt')
    else:
# with col2:
#     send = st.button('Enviar')

# if send and user_input.strip():
#     st.session_state['interactions'] += 1
#     st.session_state['session_questions'].append(user_input.strip())
#     #checar comms de historico, relatorio e trocar personalidade
#     low = user_input.lower()
#     if low.startswith('histórico') or low.startswith('historico'):
#         st.write('Histórico (últimas interações persistidas):')
#         for q,a in chat.get_last_history(50):
#             st.write(f'Q: {q} → A: {a}')
#     elif low.startswith('relatório') or low.startswith('relatorio') or low.startswith('gerar relatorio'):
#         path = save_report(chat, st.session_state)
#         st.success('Relatório gerado.')
#         with open(path, 'r', encoding='utf-8') as f:
#             st.text(f.read())
#         st.download_button('Baixar relatório', path, file_name='summary.txt')
#     else:
#         # normal QA 
#         ans = chat.answer(user_input, personality)
#         if ans is None:
#             st.warning('Não sei responder essa pergunta — entrando em modo de aprendizagem.')
#             provided = st.text_area('Por favor, escreva uma resposta apropriada para ensinar ao chatbot (apenas uma resposta):')
#             teach = st.button('Ensinar resposta')
#             if teach and provided.strip():
#                 chat.learn(user_input.strip(), provided.strip())
#                 st.success('Obrigado! Aprendi essa resposta.')
#                 # depois de aprender, reproduzir resposta usando a personalidade
#                 ans2 = chat._apply_personality(provided.strip(), personality)
#                 chat.register_interaction(user_input.strip(), ans2)
#                 st.write(ans2)
#         else:
#             chat.register_interaction(user_input.strip(), ans)
#             st.write(ans)

# status da sessao e controles
        st.markdown("---")
if st.button("Gerar relatório final"):
    total=len(st.session_state['questions'])
    common=Counter(st.session_state['questions']).most_common(1)
    report=[f"Total interações: {total}"]
    if common: report.append(f"Pergunta mais frequente: {common[0][0]}")
    with open("data/summary.txt","w",encoding="utf-8") as f: f.write("\n".join(report))
    st.download_button("Baixar relatório","data/summary.txt",file_name="summary.txt")

st.markdown('---')
st.markdown('### Ações')
if st.button('Gerar relatório final e salvar contadores'):
    path = save_report(chat, st.session_state)
    chat._save_counters()
    st.success('Relatório gerado e contadores salvos.')
    with open(path, 'r', encoding='utf-8') as f:
        st.text(f.read())
    st.download_button('Baixar relatório', path, file_name='summary.txt')

st.markdown('Você pode consultar ou editar os arquivos em `data/` (qa_dict.txt, learned.txt, history.txt, counters.json).')
