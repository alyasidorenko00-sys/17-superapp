"""Утилита: Трекер привычек."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from pathlib import Path
from datetime import datetime, timedelta


class HabitTracker(tk.Frame):
    DATA_FILE = "habits.json"

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg="white")
        self.habits = []
        self.next_id = 1

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # Заголовок
        title_frame = tk.Frame(self, bg="#27ae60", height=60)
        title_frame.grid(row=0, column=0, sticky="ew")
        title_frame.grid_propagate(False)

        tk.Label(title_frame, text="📊 Трекер привычек",
                 font=("Arial", 20, "bold"), bg="#27ae60", fg="white").pack(pady=15)

        # Панель управления
        control_frame = tk.Frame(self, bg="white")
        control_frame.grid(row=1, column=0, pady=10, padx=20)

        tk.Button(control_frame, text="➕ Добавить привычку", command=self._add_habit,
                  bg="#27ae60", fg="white", relief="flat", padx=20, pady=10).pack(side="left", padx=5)

        tk.Button(control_frame, text="📊 Статистика", command=self._show_stats,
                  bg="#3498db", fg="white", relief="flat", padx=20, pady=10).pack(side="left", padx=5)

        # Список привычек
        self.habits_frame = tk.Frame(self, bg="white")
        self.habits_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.habits_frame.grid_columnconfigure(0, weight=1)

    def _add_habit(self):
        name = simpledialog.askstring("Новая привычка", "Название привычки:")
        if name and name.strip():
            habit = {
                "id": self.next_id,
                "name": name.strip(),
                "created": datetime.now().strftime("%Y-%m-%d"),
                "completions": {},
                "current_streak": 0,
                "best_streak": 0
            }
            self.habits.append(habit)
            self.next_id += 1
            self._save_data()
            self._refresh()
            messagebox.showinfo("Успех", f"Привычка '{name}' добавлена!")

    def _mark_habit(self, habit):
        today = datetime.now().strftime("%Y-%m-%d")

        if today in habit["completions"]:
            # Убрать отметку
            del habit["completions"][today]
            messagebox.showinfo("Отменено", "Отметка снята")
        else:
            # Добавить отметку
            habit["completions"][today] = "completed"
            messagebox.showinfo("Успех", "Отлично! Так держать! 🔥")

        self._calculate_streaks(habit)
        self._save_data()
        self._refresh()

    def _calculate_streaks(self, habit):
        """Рассчитать текущую и лучшую серию."""
        completions = sorted(habit["completions"].keys())

        if not completions:
            habit["current_streak"] = 0
            return

        # Текущая серия
        current = 0
        today = datetime.now().date()

        for i in range(365):
            check_date = today - timedelta(days=i)
            date_str = check_date.strftime("%Y-%m-%d")

            if date_str in completions:
                current += 1
            elif i == 0:
                continue
            else:
                break

        habit["current_streak"] = current

        # Лучшая серия
        best = 0
        temp = 0
        prev_date = None

        for date_str in completions:
            curr_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            if prev_date is None or (curr_date - prev_date).days <= 1:
                temp += 1
                best = max(best, temp)
            else:
                temp = 1

            prev_date = curr_date

        habit["best_streak"] = best

    def _show_stats(self):
        if not self.habits:
            messagebox.showinfo("Статистика", "Нет привычек для анализа")
            return

        total = len(self.habits)
        today = datetime.now().strftime("%Y-%m-%d")
        completed_today = sum(1 for h in self.habits if today in h["completions"])

        best_habit = max(self.habits, key=lambda h: h["best_streak"])

        msg = (f"📊 Статистика привычек\n\n"
               f"Всего привычек: {total}\n"
               f"Выполнено сегодня: {completed_today}/{total}\n\n"
               f"🏆 Лучшая серия: {best_habit['best_streak']} дней\n"
               f"   ({best_habit['name']})")

        messagebox.showinfo("Статистика", msg)

    def _refresh(self):
        for w in self.habits_frame.winfo_children():
            w.destroy()

        if not self.habits:
            tk.Label(self.habits_frame, text="📝 Добавьте свою первую привычку!",
                     font=("Arial", 14), bg="white", fg="gray").pack(pady=50)
            return

        for habit in self.habits:
            frame = tk.Frame(self.habits_frame, bg="#ecf0f1", relief="ridge", bd=2)
            frame.pack(fill="x", pady=10)
            frame.grid_columnconfigure(0, weight=1)

            # Название
            tk.Label(frame, text=f"📌 {habit['name']}",
                     font=("Arial", 14, "bold"), bg="#ecf0f1").grid(row=0, column=0,
                                                                    padx=15, pady=10, sticky="w")

            # Серии
            streak_frame = tk.Frame(frame, bg="#ecf0f1")
            streak_frame.grid(row=0, column=1, padx=15)

            tk.Label(streak_frame, text=f"🔥 {habit['current_streak']} дн.",
                     bg="#ecf0f1", fg="#e67e22", font=("Arial", 12, "bold")).pack(side="left", padx=5)

            tk.Label(streak_frame, text=f"🏆 {habit['best_streak']} дн.",
                     bg="#ecf0f1", fg="#95a5a6", font=("Arial", 10)).pack(side="left", padx=5)

            # Кнопки
            btn_frame = tk.Frame(frame, bg="#ecf0f1")
            btn_frame.grid(row=0, column=2, padx=15)

            today = datetime.now().strftime("%Y-%m-%d")
            is_done = today in habit["completions"]

            if is_done:
                tk.Button(btn_frame, text="✅ Выполнено",
                          command=lambda h=habit: self._mark_habit(h),
                          bg="#27ae60", fg="white", relief="flat", padx=15, pady=8).pack(side="left", padx=2)
            else:
                tk.Button(btn_frame, text="✔️ Отметить",
                          command=lambda h=habit: self._mark_habit(h),
                          bg="#3498db", fg="white", relief="flat", padx=15, pady=8).pack(side="left", padx=2)

            tk.Button(btn_frame, text="🗑️",
                      command=lambda h=habit: self._delete_habit(h),
                      bg="#e74c3c", fg="white", relief="flat", padx=10, pady=8).pack(side="left", padx=2)

    def _delete_habit(self, habit):
        if messagebox.askyesno("Подтверждение", f"Удалить привычку '{habit['name']}'?"):
            self.habits.remove(habit)
            self._save_data()
            self._refresh()
            messagebox.showinfo("Удалено", "Привычка удалена")

    def _save_data(self):
        data = {
            "habits": self.habits,
            "next_id": self.next_id
        }
        with open(self.DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_data(self):
        if Path(self.DATA_FILE).exists():
            try:
                with open(self.DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.habits = data.get("habits", [])
                self.next_id = data.get("next_id", 1)
                self._refresh()
            except Exception as e:
                print(f"Ошибка загрузки: {e}")