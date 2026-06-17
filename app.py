"""Ядро SuperApp - исправленная версия."""
import tkinter as tk
from tkinter import messagebox


class SuperApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SuperApp v2.0")
        self.root.geometry("1000x700")

        self.utils = {}
        self.active_frame = None
        self.nav_buttons = {}

        # ВАЖНО: Сначала загружаем утилиты, потом создаем интерфейс!
        self._register_utilities()
        self._build_sidebar()
        self._build_content()

        # Запускаем первую доступную утилиту
        if self.utils:
            first_key = list(self.utils.keys())[0]
            self._navigate(first_key)

        self.root.mainloop()

    def _register_utilities(self):
        """Загружаем утилиты ПЕРЕД созданием интерфейса."""

        try:
            from mood_tracker import MoodTracker
            self.utils["mood"] = MoodTracker
            print("✅ MoodTracker загружен")
        except Exception as e:
            print(f"❌ MoodTracker: {e}")

        try:
            from currency_tracker import CurrencyTracker
            self.utils["currency"] = CurrencyTracker
            print("✅ CurrencyTracker загружен")
        except Exception as e:
            print(f"❌ CurrencyTracker: {e}")

        try:
            from habit_tracker import HabitTracker
            self.utils["habits"] = HabitTracker
            print("✅ HabitTracker загружен")
        except Exception as e:
            print(f"❌ HabitTracker: {e}")

        try:
            from budget_manager import BudgetManager
            self.utils["budget"] = BudgetManager
            print("✅ BudgetManager загружен")
        except Exception as e:
            print(f"❌ BudgetManager: {e}")

        try:
            from schedule_manager import ScheduleManager
            self.utils["schedule"] = ScheduleManager
            print("✅ ScheduleManager загружен")
        except Exception as e:
            print(f"❌ ScheduleManager: {e}")

        print(f"\n📊 Загружено утилит: {len(self.utils)}/5")

    def _build_sidebar(self):
        """Создаем боковую панель ПОСЛЕ загрузки утилит."""
        sidebar = tk.Frame(self.root, bg="#2c3e50", width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="🧩 SuperApp", font=("Arial", 22, "bold"),
                bg="#2c3e50", fg="white").pack(pady=20)

        # Все кнопки (создаем для всех утилит)
        buttons = [
            ("mood", "😊 Дневник настроения"),
            ("currency", "📈 Курсы валют"),
            ("habits", "📊 Трекер привычек"),
            ("budget", "💰 Менеджер бюджета"),
            ("schedule", "📅 Расписание")
        ]

        for key, text in buttons:
            if key in self.utils:  # Только загруженные утилиты
                btn = tk.Button(sidebar, text=text, bg="#2c3e50", fg="white",
                               activebackground="#34495e", activeforeground="white",
                               relief="flat", padx=20, pady=10,
                               command=lambda k=key: self._navigate(k))
                btn.pack(fill="x", padx=5, pady=2)
                self.nav_buttons[key] = btn

    def _build_content(self):
        self.content = tk.Frame(self.root, bg="white")
        self.content.pack(side="right", fill="both", expand=True, padx=20, pady=20)

    def _navigate(self, key):
        if self.active_frame:
            self.active_frame.destroy()

        # Подсветка кнопок
        for btn in self.nav_buttons.values():
            btn.configure(bg="#2c3e50")
        if key in self.nav_buttons:
            self.nav_buttons[key].configure(bg="#34495e")

        # Загрузка утилиты
        util_class = self.utils.get(key)
        if util_class:
            try:
                self.active_frame = util_class(self.content)
                self.active_frame.pack(fill="both", expand=True)
                print(f"✅ Открыта: {key}")
            except Exception as e:
                print(f"❌ Ошибка открытия {key}: {e}")
                tk.Label(self.content, text=f"Ошибка: {e}",
                        font=("Arial", 14), fg="red", bg="white").pack(expand=True)
        else:
            tk.Label(self.content, text="Утилита не найдена",
                    font=("Arial", 14), bg="white").pack(expand=True)


if __name__ == "__main__":
    SuperApp()