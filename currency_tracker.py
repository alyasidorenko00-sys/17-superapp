"""Утилита: Курсы валют с API ЦБ РФ."""
import tkinter as tk
from tkinter import ttk
import threading
import requests
from datetime import datetime, timedelta


class CurrencyTracker(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg="white")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._setup_ui()
        threading.Thread(target=self._load_data, daemon=True).start()

    def _setup_ui(self):
        # Заголовок
        title_frame = tk.Frame(self, bg="#3498db", height=60)
        title_frame.grid(row=0, column=0, sticky="ew")
        title_frame.grid_propagate(False)

        tk.Label(title_frame, text="📈 Курсы валют ЦБ РФ",
                font=("Arial", 20, "bold"), bg="#3498db", fg="white").pack(pady=15)

        # Кнопка обновления
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.grid(row=1, column=0, pady=10)

        tk.Button(btn_frame, text="🔄 Обновить данные", command=self._refresh_data,
                 bg="#27ae60", fg="white", relief="flat", padx=20, pady=10).pack()

        # Статус
        self.status_label = tk.Label(self, text="⏳ Загрузка данных с ЦБ РФ...",
                                    font=("Arial", 12), bg="white", fg="orange")
        self.status_label.grid(row=2, column=0, pady=20)

        # Таблица
        self.table_frame = tk.Frame(self, bg="white")
        self.table_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)

    def _refresh_data(self):
        self.status_label.configure(text="⏳ Обновление...", fg="orange")
        threading.Thread(target=self._load_data, daemon=True).start()

    def _load_data(self):
        """Загрузка реальных данных с API ЦБ РФ."""
        try:
            base_url = "https://www.cbr-xml-daily.ru/archive/{y}/{m:02d}/{d:02d}/daily_json.js"
            today = datetime.now()

            dates, usd, eur, cny = [], [], [], []

            # Получаем данные за последние 7 дней
            for i in range(7, -1, -1):
                d = today - timedelta(days=i)
                url = base_url.format(y=d.year, m=d.month, d=d.day)

                try:
                    resp = requests.get(url, timeout=5)
                    if resp.status_code == 200:
                        data = resp.json()
                        dates.append(d.strftime("%d.%m.%Y"))
                        usd.append(data["Valute"]["USD"]["Value"])
                        eur.append(data["Valute"]["EUR"]["Value"])
                        cny.append(data["Valute"]["CNY"]["Value"])
                except Exception as e:
                    print(f"Ошибка загрузки {d.strftime('%d.%m')}: {e}")
                    continue

            if dates:
                # Формируем данные для таблицы
                table_data = []
                for i in range(len(dates)):
                    table_data.append((
                        dates[i],
                        f"{usd[i]:.2f} ₽",
                        f"{eur[i]:.2f} ₽",
                        f"{cny[i]:.2f} ₽"
                    ))

                # Статистика
                usd_avg = sum(usd) / len(usd)
                eur_avg = sum(eur) / len(eur)
                cny_avg = sum(cny) / len(cny)

                usd_change = usd[-1] - usd[0]
                eur_change = eur[-1] - eur[0]
                cny_change = cny[-1] - cny[0]

                stats_text = (f"📊 Средний курс за 7 дней: USD {usd_avg:.2f} ₽ | "
                             f"EUR {eur_avg:.2f} ₽ | CNY {cny_avg:.2f} ₽\n"
                             f"📈 Изменение: USD {usd_change:+.2f} | "
                             f"EUR {eur_change:+.2f} | CNY {cny_change:+.2f}")

                self.after(0, self._show_data, table_data, stats_text)
            else:
                self.after(0, lambda: self.status_label.configure(
                    text="❌ Не удалось загрузить данные", fg="red"))

        except Exception as e:
            self.after(0, lambda: self.status_label.configure(
                text=f"❌ Ошибка: {e}", fg="red"))

    def _show_data(self, data, stats_text):
        """Отображение данных в таблице."""
        # Очистка
        for w in self.table_frame.winfo_children():
            w.destroy()

        # Таблица
        columns = ("Дата", "USD", "EUR", "CNY")
        tree = ttk.Treeview(self.table_frame, columns=columns,
                           show="headings", height=8)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")

        for row in data:
            tree.insert("", "end", values=row)

        tree.pack(fill="both", expand=True)

        # Статистика
        stats_label = tk.Label(self.table_frame, text=stats_text,
                              font=("Arial", 11), bg="#ecf0f1", pady=10)
        stats_label.pack(fill="x", pady=(10, 0))

        self.status_label.configure(text="✅ Данные загружены с ЦБ РФ", fg="green")