"""Утилита: Дневник настроения (Mood Tracker)."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from pathlib import Path
from datetime import datetime, timedelta


class MoodEntry:
    """Модель записи настроения."""
    MOODS = {
        1: "😢",  # Очень плохо
        2: "😕",  # Плохо
        3: "😐",  # Нормально
        4: "😊",  # Хорошо
        5: "😄"  # Отлично
    }

    MOOD_NAMES = {
        1: "Очень плохо",
        2: "Плохо",
        3: "Нормально",
        4: "Хорошо",
        5: "Отлично"
    }

    def __init__(self, id, date, mood, note=""):
        self.id = id
        self.date = date  # "YYYY-MM-DD"
        self.mood = mood  # 1-5
        self.note = note

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "mood": self.mood,
            "note": self.note
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data["id"], data["date"], data["mood"], data.get("note", ""))


class MoodTracker(tk.Frame):
    """Главный виджет дневника настроения."""
    DATA_FILE = "mood_data.json"

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg="white")
        self.entries = []
        self.next_id = 1

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Создать интерфейс."""
        # Заголовок
        title_frame = tk.Frame(self, bg="#9b59b6", height=60)
        title_frame.grid(row=0, column=0, sticky="ew")
        title_frame.grid_propagate(False)

        tk.Label(title_frame, text="😊 Дневник настроения",
                 font=("Arial", 20, "bold"), bg="#9b59b6", fg="white").pack(pady=15)

        # Быстрая оценка настроения
        mood_frame = tk.Frame(self, bg="#ecf0f1", relief="ridge", bd=2)
        mood_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        tk.Label(mood_frame, text="Как вы себя чувствуете сегодня?",
                 font=("Arial", 12), bg="#ecf0f1").pack(pady=10)

        emoji_frame = tk.Frame(mood_frame, bg="#ecf0f1")
        emoji_frame.pack(pady=5)

        for mood_value in range(1, 6):
            emoji = MoodEntry.MOODS[mood_value]
            btn = tk.Button(emoji_frame, text=emoji, font=("Arial", 24),
                            bg="#ecf0f1", relief="flat", cursor="hand2",
                            command=lambda m=mood_value: self._quick_add_mood(m))
            btn.pack(side="left", padx=10)

        self.today_label = tk.Label(mood_frame, text="",
                                    font=("Arial", 11), bg="#ecf0f1", fg="#27ae60")
        self.today_label.pack(pady=5)

        # Кнопки управления
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)

        tk.Button(btn_frame, text="📝 Добавить запись", command=self._add_entry,
                  bg="#9b59b6", fg="white", relief="flat", padx=20, pady=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="📊 Статистика", command=self._show_stats,
                  bg="#3498db", fg="white", relief="flat", padx=20, pady=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="📈 График", command=self._show_chart,
                  bg="#27ae60", fg="white", relief="flat", padx=20, pady=8).pack(side="left", padx=5)

        # История записей
        history_frame = tk.LabelFrame(self, text="📋 История настроений",
                                      font=("Arial", 12, "bold"), bg="white", relief="ridge", bd=2)
        history_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        history_frame.grid_columnconfigure(0, weight=1)
        history_frame.grid_rowconfigure(0, weight=1)

        columns = ("Дата", "Настроение", "Заметка")
        self.tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=10)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")

        self.tree.column("Заметка", width=300)

        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Кнопки редактирования
        edit_frame = tk.Frame(history_frame, bg="white")
        edit_frame.grid(row=1, column=0, pady=10)

        tk.Button(edit_frame, text="✏️ Редактировать", command=self._edit_entry,
                  bg="#f39c12", fg="white", relief="flat", padx=15).pack(side="left", padx=5)
        tk.Button(edit_frame, text="🗑️ Удалить", command=self._delete_entry,
                  bg="#e74c3c", fg="white", relief="flat", padx=15).pack(side="left", padx=5)

        self.tree.bind("<Double-1>", lambda e: self._edit_entry())

    def _quick_add_mood(self, mood_value):
        """Быстрое добавление настроения."""
        today = datetime.now().strftime("%Y-%m-%d")

        # Проверяем, есть ли уже запись за сегодня
        for entry in self.entries:
            if entry.date == today:
                if messagebox.askyesno("Подтверждение",
                                       f"Запись за сегодня уже есть ({MoodEntry.MOODS[entry.mood]}). Заменить?"):
                    entry.mood = mood_value
                    self._save_data()
                    self._refresh()
                    messagebox.showinfo("Успех", f"Настроение обновлено: {MoodEntry.MOODS[mood_value]}")
                return

        # Создаем новую запись
        entry = MoodEntry(self.next_id, today, mood_value)
        self.entries.append(entry)
        self.next_id += 1
        self._save_data()
        self._refresh()
        messagebox.showinfo("Успех", f"Настроение сохранено: {MoodEntry.MOODS[mood_value]}")

    def _add_entry(self):
        """Добавить запись с заметкой."""
        dialog = MoodDialog(self)
        if dialog.result:
            entry = MoodEntry(
                self.next_id,
                dialog.result["date"],
                dialog.result["mood"],
                dialog.result["note"]
            )
            self.entries.append(entry)
            self.next_id += 1
            self._save_data()
            self._refresh()
            messagebox.showinfo("Успех", "Запись добавлена!")

    def _edit_entry(self):
        """Редактировать запись."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите запись для редактирования")
            return

        index = self.tree.index(selection[0])
        if 0 <= index < len(self.entries):
            entry = self.entries[index]
            dialog = MoodDialog(self, entry)
            if dialog.result:
                entry.date = dialog.result["date"]
                entry.mood = dialog.result["mood"]
                entry.note = dialog.result["note"]
                self._save_data()
                self._refresh()
                messagebox.showinfo("Успех", "Запись обновлена!")

    def _delete_entry(self):
        """Удалить запись."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите запись для удаления")
            return

        if messagebox.askyesno("Подтверждение", "Удалить выбранную запись?"):
            index = self.tree.index(selection[0])
            if 0 <= index < len(self.entries):
                self.entries.pop(index)
                self._save_data()
                self._refresh()
                messagebox.showinfo("Успех", "Запись удалена!")

    def _refresh(self):
        """Обновить отображение."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Сортируем по дате (новые сверху)
        sorted_entries = sorted(self.entries, key=lambda e: e.date, reverse=True)

        for entry in sorted_entries:
            emoji = MoodEntry.MOODS[entry.mood]
            mood_name = MoodEntry.MOOD_NAMES[entry.mood]

            self.tree.insert("", "end", values=(
                entry.date,
                f"{emoji} {mood_name}",
                entry.note
            ))

        # Обновляем метку за сегодня
        today = datetime.now().strftime("%Y-%m-%d")
        today_entry = next((e for e in self.entries if e.date == today), None)

        if today_entry:
            self.today_label.configure(
                text=f"Сегодня: {MoodEntry.MOODS[today_entry.mood]} {MoodEntry.MOOD_NAMES[today_entry.mood]}"
            )
        else:
            self.today_label.configure(text="Сегодня запись еще не добавлена")

    def _show_stats(self):
        """Показать статистику."""
        if not self.entries:
            messagebox.showinfo("Статистика", "Нет записей для анализа")
            return

        # Считаем среднее настроение
        avg_mood = sum(e.mood for e in self.entries) / len(self.entries)

        # Находим лучший и худший день
        best_day = max(self.entries, key=lambda e: e.mood)
        worst_day = min(self.entries, key=lambda e: e.mood)

        # Считаем за последнюю неделю
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        week_entries = [e for e in self.entries if e.date >= week_ago]
        week_avg = sum(e.mood for e in week_entries) / len(week_entries) if week_entries else 0

        msg = (f"📊 Статистика настроения\n\n"
               f" Среднее настроение: {avg_mood:.1f}/5\n"
               f"📅 Всего записей: {len(self.entries)}\n\n"
               f"😊 Лучший день: {best_day.date} ({MoodEntry.MOODS[best_day.mood]})\n"
               f"😢 Худший день: {worst_day.date} ({MoodEntry.MOODS[worst_day.mood]})\n\n"
               f"📆 За последнюю неделю: {week_avg:.1f}/5 ({len(week_entries)} записей)")

        messagebox.showinfo("Статистика", msg)

    def _show_chart(self):
        """Показать график настроения."""
        if not self.entries:
            messagebox.showinfo("График", "Нет записей для отображения")
            return

        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            # Берем последние 30 дней
            sorted_entries = sorted(self.entries, key=lambda e: e.date)[-30:]

            dates = [e.date[5:] for e in sorted_entries]  # MM-DD
            moods = [e.mood for e in sorted_entries]

            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(dates, moods, marker='o', linewidth=2, markersize=8, color='#9b59b6')
            ax.set_ylim(0.5, 5.5)
            ax.set_yticks([1, 2, 3, 4, 5])
            ax.set_yticklabels(['😢', '😕', '😐', '😊', '😄'])
            ax.set_title("Динамика настроения", fontsize=12, fontweight='bold')
            ax.set_xlabel("Дата")
            ax.set_ylabel("Настроение")
            ax.grid(True, alpha=0.3)
            fig.autofmt_xdate()
            plt.tight_layout()

            chart_window = tk.Toplevel(self)
            chart_window.title("📈 График настроения")
            chart_window.geometry("700x400")

            canvas = FigureCanvasTkAgg(fig, master=chart_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

            tk.Button(chart_window, text="Закрыть", command=chart_window.destroy,
                      bg="#95a5a6", fg="white", relief="flat", padx=30, pady=10).pack(pady=10)

        except ImportError:
            messagebox.showinfo("График",
                                "Для отображения графика установите matplotlib:\n"
                                "pip install matplotlib==3.5.3")

    def _save_data(self):
        """Сохранить данные."""
        data = {
            "entries": [e.to_dict() for e in self.entries],
            "next_id": self.next_id
        }
        with open(self.DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_data(self):
        """Загрузить данные."""
        if not Path(self.DATA_FILE).exists():
            self._refresh()
            return

        try:
            with open(self.DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.entries = [MoodEntry.from_dict(e) for e in data.get("entries", [])]
            self.next_id = data.get("next_id", 1)
            self._refresh()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")


class MoodDialog(simpledialog.Dialog):
    """Диалог добавления/редактирования записи."""

    def __init__(self, parent, entry=None):
        self.edit_entry = entry
        self.result = None
        super().__init__(parent, title="Редактировать запись" if entry else "Новая запись")

    def body(self, master):
        tk.Label(master, text="Дата:", font=("Arial", 11)).grid(row=0, sticky="w", pady=5)
        self.date_entry = tk.Entry(master, width=20, font=("Arial", 11))
        self.date_entry.grid(row=1, sticky="w", pady=5)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Label(master, text="Настроение:", font=("Arial", 11)).grid(row=2, sticky="w", pady=5)
        self.mood_var = tk.IntVar(value=3)

        mood_frame = tk.Frame(master)
        mood_frame.grid(row=3, sticky="ew", pady=5)

        for mood_value in range(1, 6):
            emoji = MoodEntry.MOODS[mood_value]
            tk.Radiobutton(mood_frame, text=emoji, variable=self.mood_var,
                           value=mood_value, font=("Arial", 16)).pack(side="left", padx=10)

        tk.Label(master, text="Заметка:", font=("Arial", 11)).grid(row=4, sticky="w", pady=5)
        self.note_text = tk.Text(master, width=40, height=4, font=("Arial", 11))
        self.note_text.grid(row=5, sticky="ew", pady=5)

        # Заполнить если редактирование
        if self.edit_entry:
            self.date_entry.delete(0, "end")
            self.date_entry.insert(0, self.edit_entry.date)
            self.mood_var.set(self.edit_entry.mood)
            self.note_text.insert("1.0", self.edit_entry.note)

        return self.date_entry

    def apply(self):
        date = self.date_entry.get().strip()
        if not date:
            messagebox.showerror("Ошибка", "Введите дату")
            return

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты (должен быть ГГГГ-ММ-ДД)")
            return

        self.result = {
            "date": date,
            "mood": self.mood_var.get(),
            "note": self.note_text.get("1.0", "end").strip()
        }