import streamlit as st
from chatbot import ChatBot
from collections import Counter
import json

st.set_page_config(
    page_title="Chatbot Financeiro Inteligente",
    layout="centered",
    page_icon="💰"
)

# Fundo principal (usando container)
page_bg = """
<style>
[data-testid="stAppViewContainer"] {
background-color: #e6f2e6;
}
[data-testid="stSidebar"] {
background-color: #cce6cc;
}
.stButton>button {
background-color: #2e7d32;
color:white;
}
.stTextInput>div>input, .stTextArea>div>textarea {
border: 2px solid #2e7d32;
background-color:#f0fff0;
color:#0b3d0b;
}
h1,h2,h3,h4,h5,h6 {
color:#1b5e20;
}
hr {
border-top: 2px solid #2e7d32;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# utilitarios
def load_counters(path='data/counters.json'):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"formal":0, "engracado":0, "rude":0}

def save_report(chatbot: ChatBot, session_state):
    total = session_state.get('interactions', 0)
    questions = session_state.get('questions', [])
    most_common = Counter(questions).most_common(1)[0][0] if questions else ''
    report = [
        f"Total de interações nesta sessão: {total}",
        f"Pergunta mais frequente da sessão: {most_common}",
        "Contador acumulado de personalidades:",
        json.dumps(chatbot.counters, ensure_ascii=False, indent=2),
        "Últimas interações (persistidas):"
    ]
    last = chatbot.get_last_history(10)
    for u,b in last:
        report.append(f"Q: {u}\nA: {b}\n")
    report_text = '\n\n'.join(report)
    with open('data/summary.txt', 'w', encoding='utf-8') as f:
        f.write(report_text)
    return 'data/summary.txt'

# Título
st.title(' Chatbot Financeiro Inteligente')
st.markdown('Disponível 24/7 — registre gastos, tire dúvidas e aprenda sobre finanças.')

# iniciar o bot
chat = ChatBot()

# sidebar customizada
with st.sidebar:
    st.header('Configuração')
    personality = st.selectbox('Escolha a personalidade', ['formal','engracado','rude'])
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

    st.markdown('**Últimas 5 interações (persistidas):**')
    last5 = chat.get_last_history(5)
    if last5:
        for q,a in last5:
            st.write(f'- **Q:** {q} → **A:** {a}')
    else:
        st.write('Nenhuma interação anterior encontrada.')

    st.markdown('**Uso de personalidades (acumulado):**')
    st.write(chat.counters)

# conversa com o bot
st.markdown('### Converse com o chatbot')
col1, col2 = st.columns([3,1])
with col1:
    user_input = st.text_input("Digite sua pergunta:")
    if st.button("Enviar"):
        if st.session_state['learning_q']:
            st.warning("Finalize o aprendizado antes de nova pergunta.")
        else:
            st.session_state['questions'].append(user_input)
            ans = chat.answer(user_input, st.session_state['personality'])
            if ans is None:
                st.session_state['learning_q'] = user_input
                st.info("Não sei responder. Ensine-me abaixo ")
            else:
                chat.register_interaction(user_input, ans)
                st.write(ans)

    if st.session_state['learning_q']:
        resp = st.text_area("Escreva a resposta para ensinar:", key="teach_area")
        if st.button("Salvar resposta"):
            chat.learn(st.session_state['learning_q'], resp)
            ans = chat.answer(st.session_state['learning_q'], st.session_state['personality'])
            chat.register_interaction(st.session_state['learning_q'], ans)
            st.success("Resposta aprendida!")
            st.write(ans)
            st.session_state['learning_q'] = None

# estatísticas da sessão
st.markdown('---')
st.markdown('### Estatísticas da sessão')
st.write(f'Total de interações nesta sessão: {st.session_state["interactions"]}')
if st.session_state['session_questions']:
    most = Counter(st.session_state['session_questions']).most_common(3)
    st.write('Perguntas mais frequentes nesta sessão:')
    for q,c in most:
        st.write(f'- {q} (x{c})')

# ações
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
