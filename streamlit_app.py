"""streamlit_app.py

Aplicação Streamlit que serve como GUI para o Chatbot Financeiro Inteligente.
"""
import streamlit as st
from chatbot import ChatBot
from collections import Counter
import json
import os

st.set_page_config(page_title="Chatbot Financeiro Inteligente", layout='centered')

# --- Helper utilities
def load_counters(path='data/counters.json'):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"formal":0, "engracado":0, "rude":0}

def save_report(chatbot: ChatBot, session_state):
    # generate a summary report file
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

# --- Main UI
st.title('🤖 Chatbot Financeiro Inteligente')
st.markdown('Disponível 24/7 — registre gastos, tire dúvidas e aprenda sobre finanças.')

# instantiate chatbot
chat = ChatBot()

# show last 5 interactions
st.sidebar.header('Configuração')
personality = st.sidebar.selectbox('Escolha a personalidade', ['formal','engracado','rude'])
if 'session_questions' not in st.session_state:
    st.session_state['session_questions'] = []
if 'interactions' not in st.session_state:
    st.session_state['interactions'] = 0

st.sidebar.markdown('**Últimas 5 interações (persistidas):**')
last5 = chat.get_last_history(5)
if last5:
    for q,a in last5:
        st.sidebar.write(f'- **Q:** {q} → **A:** {a}')
else:
    st.sidebar.write('Nenhuma interação anterior encontrada.')

# personality usage counters
st.sidebar.markdown('**Uso de personalidades (acumulado):**')
counters = chat.counters
st.sidebar.write(counters)

st.markdown('### Converse com o chatbot')
col1, col2 = st.columns([3,1])
with col1:
    user_input = st.text_input('Digite sua pergunta ou registre um gasto (ex: "gastei 20 em almoço")')
with col2:
    send = st.button('Enviar')

if send and user_input.strip():
    st.session_state['interactions'] += 1
    st.session_state['session_questions'].append(user_input.strip())
    # check simple commands: show history, gerar relatorio, trocar personalidade
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
        # normal QA flow
        ans = chat.answer(user_input, personality)
        if ans is None:
            st.warning('Não sei responder essa pergunta — entrando em modo de aprendizagem.')
            provided = st.text_area('Por favor, escreva uma resposta apropriada para ensinar ao chatbot (apenas uma resposta):')
            teach = st.button('Ensinar resposta')
            if teach and provided.strip():
                chat.learn(user_input.strip(), provided.strip())
                st.success('Obrigado! Aprendi essa resposta.')
                # after learning, produce reply using selected personality
                ans2 = chat._apply_personality(provided.strip(), personality)
                chat.register_interaction(user_input.strip(), ans2)
                st.write(ans2)
        else:
            chat.register_interaction(user_input.strip(), ans)
            st.write(ans)

# show session stats and controls
st.markdown('---')
st.markdown('### Estatísticas da sessão')
st.write(f'Total de interações nesta sessão: {st.session_state["interactions"]}')
if st.session_state['session_questions']:
    from collections import Counter
    most = Counter(st.session_state['session_questions']).most_common(3)
    st.write('Perguntas mais frequentes nesta sessão:')
    for q,c in most:
        st.write(f'- {q} (x{c})')

st.markdown('---')
st.markdown('### Ações')
if st.button('Gerar relatório final e salvar contadores'):
    path = save_report(chat, st.session_state)
    chat.save_counters()
    st.success('Relatório gerado e contadores salvos.')
    with open(path, 'r', encoding='utf-8') as f:
        st.text(f.read())
    st.download_button('Baixar relatório', path, file_name='summary.txt')

st.markdown('Você pode consultar ou editar os arquivos em `data/` (qa_dict.txt, learned.txt, history.txt, counters.json).')
