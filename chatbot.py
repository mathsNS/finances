"""chatbot.py

Módulo que contém classes de domínio e lógica principal do  
"""
import json
import random
from typing import List, Dict

class ConversationEntry:
    """Representa uma única interação (pergunta e resposta)."""
    def __init__(self, user: str, bot: str):
        self.user = user
        self.bot = bot

    def to_line(self) -> str:
        return f"USER: {self.user}\nBOT: {self.bot}\n---\n"

class ChatBot:
    """Classe principal do chatbot financeiro.

    Regras:
    - Carrega um dicionário de perguntas-respostas de um arquivo .txt.
    - Mantém histórico em memória (lista) e persiste em arquivo.
    - Se não souber responder, entra em modo de aprendizagem e pede uma resposta ao usuário.
    - Suporta três personalidades que afetam *como* a resposta é entregue.
    """
    def __init__(self, qa_path='data/qa_dict.txt', history_path='data/history.txt',
                 learned_path='data/learned.txt', counters_path='data/counters.json'):
        self.qa_path = qa_path
        self.history_path = history_path
        self.learned_path = learned_path
        self.counters_path = counters_path

        self.qa = self._load_qa()
        self.history: List[ConversationEntry] = []
        self._load_history()
        self.counters = self._load_counters()

    def _load_qa(self) -> Dict[str, List[str]]:
        qa = {}
        try:
            with open(self.qa_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '|' in line:
                        q, a = line.split('|', 1)
                        variants = [v.strip() for v in a.split(';;;') if v.strip()]
                        qa[q.lower()] = variants
        except FileNotFoundError:
            pass
        return qa

    def _load_history(self):
        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
                if not text:
                    return
                # to_line
                parts = text.split('---\n')
                for p in parts:
                    if not p.strip():
                        continue
                    lines = p.strip().splitlines()
                    user = lines[0].replace('USER:','').strip() if lines else ''
                    bot = lines[1].replace('BOT:','').strip() if len(lines)>1 else ''
                    self.history.append(ConversationEntry(user, bot))
        except FileNotFoundError:
            pass

    def _load_counters(self):
        try:
            with open(self.counters_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {"formal":0,"engracado":0,"rude":0}

    def _save_counters(self):
        with open(self.counters_path,'w',encoding='utf-8') as f:
            json.dump(self.counters,f,ensure_ascii=False,indent=2)

    def persist_history(self):
        with open(self.history_path, 'a', encoding='utf-8') as f:
            for entry in self.history_to_persist():
                f.write(entry)

    def history_to_persist(self):
        # retorna a linha e apaga o historico 
        lines = [e.to_line() for e in self.history]
        return lines

    def _save_learned(self, question: str, answer: str):
        with open(self.learned_path, 'a', encoding='utf-8') as f:
            f.write(f"{question}|{answer}\n")
        # atualiza o QA
        with open(self.qa_path, 'a', encoding='utf-8') as f:
            f.write(f"{question}|{answer};;;{answer}\n")

    def get_last_history(self, n=5):
        # ultimas interacoes que nao estao na memoria 
        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
                if not text:
                    return []
                parts = text.split('---\n')
                parsed = []
                for p in parts:
                    if not p.strip():
                        continue
                    lines = p.strip().splitlines()
                    user = lines[0].replace('USER:','').strip() if lines else ''
                    bot = lines[1].replace('BOT:','').strip() if len(lines)>1 else ''
                    parsed.append((user, bot))
                return parsed[-n:]
        except FileNotFoundError:
            return []

    def answer(self, question: str, personality: str) -> str:
        #procura no dicionario 
        q = question.lower()
        # verificando se alguma tecla do QA esta sendo pressionada 
        for key, variants in self.qa.items():
            if key in q:
                base = random.choice(variants)
                return self._apply_personality(base, personality)
        #(caso nao encontre)
        return None

    def _apply_personality(self,text,personality):
        if personality=='formal':
            self.counters['formal']+=1
            self._save_counters()
            return f"Prezada(o), {text}"
        elif personality=='engracado':
            self.counters['engracado']+=1
            self._save_counters()
            return f"Tá ligado? {text} 😄"
        elif personality=='rude':
            self.counters['rude']+=1
            self._save_counters()
            return f"Vamos lá: {text}."
        return text

    def register_interaction(self, user_q: str, bot_a: str):
        entry = ConversationEntry(user_q, bot_a)
        self.history.append(entry)
        #historico dos arquivos 
        with open(self.history_path, 'a', encoding='utf-8') as f:
            f.write(entry.to_line())

    def learn(self, question: str, answer: str):
        # salvar as questoes do modo aprendizado
        self._save_learned(question, answer)
