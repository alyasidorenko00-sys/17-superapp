"""Утилита: Менеджер бюджета."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from pathlib import Path
from datetime import datetime


class BudgetManager(tk.Frame):
    DATA_FILE = "budget.json"

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg="white")
        self.transactions = []
        self.categories = ["Еда", "Транспорт", "Развлечения", "Одежда", "Учеба", "Другое"]
        self.income_sources = ["Стипендия", "Подработка", "Помощь", "Другое"]

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # Заголовок
        title_frame = tk.Frame(self, bg="#27ae60", height=60)
        title_frame.grid(row=0, column=0, sticky="ew")
        title_frame.grid_propagate(False)

        tk.Label(title_frame, text="💰 Менеджер бюджета",
                 font=("Arial", 20, "bold"), bg="#27ae60", fg="white").pack(pady=15)

        # Баланс
        balance_frame = tk.Frame(self, bg="#ecf0f1", relief="ridge", bd=2)
        balance_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        self.balance_label = tk.Label(balance_frame, text="💵 Баланс: 0 ₽",
                                      font=("Arial", 18, "bold"), bg="#ecf0f1", fg="#2c3e50")
        self.balance_label.pack(pady=10)

        self.income_label = tk.Label(balance_frame, text="📥 Доходы: 0 ₽",
                                     font=("Arial", 12), bg="#ecf0f1", fg="#27ae60")
        self.income_label.pack()

        self.expense_label = tk.Label(balance_frame, text="📤 Расходы: 0 ₽",
                                      font=("Arial", 12), bg="#ecf0f1", fg="#e74c3c")
        self.expense_label.pack()

        # Кнопки
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)

        tk.Button(btn_frame, text="➕ Доход", command=self._add_income,
                  bg="#27ae60", fg="white", relief="flat", padx=20, pady=8).pack(side="left", padx=5)

        tk.Button(btn_frame, text="➖ Расход", command=self._add_expense,
                  bg="#e74c3c", fg="white", relief="flat", padx=20, pady=8).pack(side="left", padx=5)

        tk.Button(btn_frame, text="📊 Статистика", command=self._show_stats,
                  bg="#3498db", fg="white", relief="flat", padx=20, pady=8).pack(side="left", padx=5)

        # Таблица
        list_frame = tk.LabelFrame(self, text="📋 Транзакции",
                                   font=("Arial", 12, "bold"), bg="white", relief="ridge", bd=2)
        list_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        list_frame.grid_columnconfigure(0, weight=1)

        columns = ("Дата", "Тип", "Категория", "Сумма")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _add_income(self):
        dialog = IncomeDialog(self, self.income_sources)
        if dialog.result:
            self.transactions.append({
                "type": "income",
                "amount": dialog.result["amount"],
                "category": dialog.result["source"],
                "date": datetime.now().strftime("%d.%m.%Y %H:%M")
            })
            self._save_data()
            self._refresh()
            messagebox.showinfo("Успех", f"Доход {dialog.result['amount']} ₽ добавлен!")

    def _add_expense(self):
        dialog = ExpenseDialog(self, self.categories)
        if dialog.result:
            self.transactions.append({
                "type": "expense",
                "amount": dialog.result["amount"],
                "category": dialog.result["category"],
                "date": datetime.now().strftime("%d.%m.%Y %H:%M")
            })
            self._save_data()
            self._refresh()
            messagebox.showinfo("Успех", f"Расход {dialog.result['amount']} ₽ добавлен!")

    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        income = sum(t["amount"] for t in self.transactions if t["type"] == "income")
        expense = sum(t["amount"] for t in self.transactions if t["type"] == "expense")

        self.balance_label.configure(text=f"💵 Баланс: {income - expense:,.0f} ₽")
        self.income_label.configure(text=f"📥 Доходы: {income:,.0f} ₽")
        self.expense_label.configure(text=f"📤 Расходы: {expense:,.0f} ₽")

        for t in reversed(self.transactions[-20:]):
            amount_str = f"+{t['amount']:.0f} ₽" if t["type"] == "income" else f"-{t['amount']:.0f} ₽"
            color = "green" if t["type"] == "income" else "red"

            self.tree.insert("", "end", values=(
                t["date"],
                "📥 Доход" if t["type"] == "income" else "📤 Расход",
                t["category"],
                amount_str
            ), tags=(color,))

        self.tree.tag_configure("green", foreground="green")
        self.tree.tag_configure("red", foreground="red")

    def _show_stats(self):
        if not self.transactions:
            messagebox.showinfo("Статистика", "Нет транзакций для анализа")
            return

        income = sum(t["amount"] for t in self.transactions if t["type"] == "income")
        expense = sum(t["amount"] for t in self.transactions if t["type"] == "expense")

        expenses_by_cat = {}
        for t in self.transactions:
            if t["type"] == "expense":
                cat = t["category"]
                expenses_by_cat[cat] = expenses_by_cat.get(cat, 0) + t["amount"]

        msg = (f"💰 Общая статистика\n\n"
               f"📥 Всего доходов: {income:,.0f} ₽\n"
               f"📤 Всего расходов: {expense:,.0f} ₽\n"
               f"💵 Баланс: {income - expense:,.0f} ₽\n"
               f"📊 Транзакций: {len(self.transactions)}\n\n"
               f"📈 Расходы по категориям:\n")

        for cat, amount in sorted(expenses_by_cat.items(), key=lambda x: x[1], reverse=True):
            msg += f"   {cat}: {amount:,.0f} ₽\n"

        messagebox.showinfo("Статистика", msg)

    def _save_data(self):
        data = {
            "transactions": self.transactions,
            "categories": self.categories,
            "income_sources": self.income_sources
        }
        with open(self.DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_data(self):
        if Path(self.DATA_FILE).exists():
            try:
                with open(self.DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.transactions = data.get("transactions", [])
                self.categories = data.get("categories", self.categories)
                self.income_sources = data.get("income_sources", self.income_sources)
                self._refresh()
            except Exception as e:
                print(f"Ошибка загрузки: {e}")


class IncomeDialog(simpledialog.Dialog):
    def __init__(self, parent, sources):
        self.sources = sources
        self.result = None
        super().__init__(parent, title="Добавить доход")

    def body(self, master):
        tk.Label(master, text="Источник:").grid(row=0, sticky="w", pady=5)
        self.source_var = tk.StringVar(value=self.sources[0])
        combo = ttk.Combobox(master, textvariable=self.source_var,
                             values=self.sources, state="readonly", width=30)
        combo.grid(row=1, sticky="ew", pady=5)

        tk.Label(master, text="Сумма (₽):").grid(row=2, sticky="w", pady=5)
        self.amount_entry = tk.Entry(master, width=30)
        self.amount_entry.grid(row=3, sticky="ew", pady=5)

        return self.amount_entry

    def apply(self):
        try:
            amount = float(self.amount_entry.get())
            if amount > 0:
                self.result = {
                    "source": self.source_var.get(),
                    "amount": amount
                }
            else:
                messagebox.showerror("Ошибка", "Сумма должна быть больше 0")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную сумму")


class ExpenseDialog(simpledialog.Dialog):
    def __init__(self, parent, categories):
        self.categories = categories
        self.result = None
        super().__init__(parent, title="Добавить расход")

    def body(self, master):
        tk.Label(master, text="Категория:").grid(row=0, sticky="w", pady=5)
        self.category_var = tk.StringVar(value=self.categories[0])
        combo = ttk.Combobox(master, textvariable=self.category_var,
                             values=self.categories, state="readonly", width=30)
        combo.grid(row=1, sticky="ew", pady=5)

        tk.Label(master, text="Сумма (₽):").grid(row=2, sticky="w", pady=5)
        self.amount_entry = tk.Entry(master, width=30)
        self.amount_entry.grid(row=3, sticky="ew", pady=5)

        return self.amount_entry

    def apply(self):
        try:
            amount = float(self.amount_entry.get())
            if amount > 0:
                self.result = {
                    "category": self.category_var.get(),
                    "amount": amount
                }
            else:
                messagebox.showerror("Ошибка", "Сумма должна быть больше 0")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную сумму")