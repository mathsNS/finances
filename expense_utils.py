"""expense_utils.py

Pequeno módulo que demonstra uso de listas e dicionários para registrar gastos temporários.
"""
from typing import List, Dict

class ExpenseManager:
    """Gerencia despesas em memória e permite exportar para texto."""
    def __init__(self):
        self.expenses: List[Dict] = []

    def add_expense(self, amount: float, category: str, note: str = ''):
        entry = {'amount': amount, 'category': category, 'note': note}
        self.expenses.append(entry)

    def summary(self):
        totals = {}
        for e in self.expenses:
            totals[e['category']] = totals.get(e['category'], 0) + e['amount']
        return totals

    def export_txt(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            for e in self.expenses:
                f.write(f"{e['amount']}|{e['category']}|{e['note']}\n")
