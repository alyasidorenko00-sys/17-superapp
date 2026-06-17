"""Утилита: Расписание занятий."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from pathlib import Path
from datetime import datetime, timedelta


class ScheduleManager(tk.Frame):
    DATA_FILE = "schedule.json"
    DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    TYPES = ["Лекция", "Практика", "Семинар", "Лабораторная"]

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg="white")
        self.lessons = []
        self.next_id = 1

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._setup_ui()
        self._load_data()
        self._start_timer()

    def _setup_ui(self):
        # Заголовок
        title_frame = tk.Frame(self, bg="#3498db", height=60)
        title_frame.grid(row=0, column=0, sticky="ew")
        title_frame.grid_propagate(False)

        tk.Label(title_frame, text="📅 Расписание занятий",
                 font=("Arial", 20, "bold"), bg="#3498db", fg="white").pack(pady=15)

        # Таймер до следующей пары
        self.timer_frame = tk.Frame(self, bg="#f39c12", relief="ridge", bd=2)
        self.timer_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        self.timer_label = tk.Label(self.timer_frame, text="⏰ Следующая пара: ...",
                                    font=("Arial", 14, "bold"), bg="#f39c12", fg="white")
        self.timer_label.pack(pady=10)

        self.countdown_label = tk.Label(self.timer_frame, text="00:00:00",
                                        font=("Arial", 24, "bold"), bg="#f39c12", fg="white")
        self.countdown_label.pack()

        # Кнопки
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)

        tk.Button(btn_frame, text="➕ Добавить", command=self._add_lesson,
                  bg="#27ae60", fg="white", relief="flat", padx=20, pady=8).pack(side="left", padx=5)

        tk.Button(btn_frame, text="📊 Статистика", command=self._show_stats,
                  bg="#9b59b6", fg="white", relief="flat", padx=20, pady=8).pack(side="left", padx=5)

        # Сетка расписания
        grid_frame = tk.LabelFrame(self, text="📋 Расписание на неделю",
                                   font=("Arial", 12, "bold"), bg="white", relief="ridge", bd=2)
        grid_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        grid_frame.grid_columnconfigure(0, weight=1)

        # Заголовки дней
        header = tk.Frame(grid_frame, bg="#ecf0f1")
        header.pack(fill="x")

        tk.Label(header, text="Время", bg="#ecf0f1", font=("Arial", 9, "bold"),
                 width=8).pack(side="left", padx=2)

        for day in self.DAYS:
            tk.Label(header, text=day[:3], bg="#ecf0f1", font=("Arial", 9, "bold"),
                     width=14).pack(side="left", padx=2)

        # Скролл для сетки
        canvas_frame = tk.Frame(grid_frame)
        canvas_frame.pack(fill="both", expand=True)

        self.canvas_frame = tk.Frame(canvas_frame, bg="white")
        self.canvas_frame.pack(fill="both", expand=True)

        self._draw_grid()

    def _draw_grid(self):
        """Нарисовать сетку времени."""
        for w in self.canvas_frame.winfo_children():
            w.destroy()

        time_slots = [f"{h:02d}:00" for h in range(8, 20)]

        for i, time in enumerate(time_slots):
            row = tk.Frame(self.canvas_frame, bg="white")
            row.pack(fill="x", pady=1)

            tk.Label(row, text=time, bg="white", font=("Arial", 8),
                     width=8).pack(side="left", padx=2)

            for day in range(6):
                cell = tk.Frame(row, bg="#ecf0f1", relief="ridge", bd=1,
                                width=100, height=35)
                cell.pack(side="left", padx=2)
                cell.pack_propagate(False)

                # Найти занятие
                for lesson in self.lessons:
                    if lesson["day_idx"] == day and lesson["start"] <= time < lesson["end"]:
                        self._fill_cell(cell, lesson)
                        break
                else:
                    cell.bind("<Button-1>", lambda e, d=day, t=time: self._add_lesson(day=d, start=t))

    def _fill_cell(self, cell, lesson):
        colors = {
            "Лекция": "#3498db",
            "Практика": "#27ae60",
            "Семинар": "#f39c12",
            "Лабораторная": "#e74c3c"
        }
        color = colors.get(lesson["type"], "#95a5a6")

        cell.configure(bg=color)

        tk.Label(cell, text=lesson["name"], bg=color, fg="white",
                 font=("Arial", 7, "bold")).pack(expand=True)
        tk.Label(cell, text=f"{lesson['room']}", bg=color, fg="white",
                 font=("Arial", 6)).pack()

        cell.bind("<Button-1>", lambda e, l=lesson: self._edit_lesson(l))
        cell.bind("<Button-3>", lambda e, l=lesson: self._delete_lesson(l))

    def _start_timer(self):
        """Запустить таймер."""
        self._update_timer()
        self.after(1000, self._start_timer)

    def _update_timer(self):
        """Обновить таймер."""
        now = datetime.now()
        current_day = now.weekday()
        current_time = now.strftime("%H:%M")

        # Найти следующую пару
        next_lesson = None

        # Сегодня
        today_lessons = [l for l in self.lessons
                         if l["day_idx"] == current_day and l["start"] > current_time]
        if today_lessons:
            today_lessons.sort(key=lambda x: x["start"])
            next_lesson = today_lessons[0]
            day_offset = 0
        else:
            # Завтра и дальше
            for offset in range(1, 7):
                next_day = (current_day + offset) % 6
                day_lessons = [l for l in self.lessons if l["day_idx"] == next_day]
                if day_lessons:
                    day_lessons.sort(key=lambda x: x["start"])
                    next_lesson = day_lessons[0]
                    day_offset = offset
                    break

        if next_lesson:
            day_name = self.DAYS[next_lesson["day_idx"]]
            day_text = "сегодня" if day_offset == 0 else f"через {day_offset} дн. ({day_name})"

            self.timer_label.configure(
                text=f"⏰ {next_lesson['name']} ({next_lesson['room']}) - {day_text} в {next_lesson['start']}"
            )

            # Обратный отсчет
            target = datetime.strptime(f"{next_lesson['start']}", "%H:%M")
            target = target.replace(year=now.year, month=now.month, day=now.day)

            if day_offset > 0:
                target += timedelta(days=day_offset)

            delta = target - now

            if delta.total_seconds() > 0:
                hours = int(delta.total_seconds() // 3600)
                minutes = int((delta.total_seconds() % 3600) // 60)
                seconds = int(delta.total_seconds() % 60)
                self.countdown_label.configure(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            else:
                self.countdown_label.configure(text="00:00:00")
        else:
            self.timer_label.configure(text="⏰ Нет запланированных занятий")
            self.countdown_label.configure(text="--:--:--")

    def _add_lesson(self, day=0, start="09:00"):
        """Добавить занятие."""
        dialog = LessonDialog(self, self.DAYS, self.TYPES)
        if dialog.result:
            lesson = {
                "id": self.next_id,
                "name": dialog.result["name"],
                "day_idx": dialog.result["day_idx"],
                "day": self.DAYS[dialog.result["day_idx"]],
                "start": dialog.result["start"],
                "end": dialog.result["end"],
                "type": dialog.result["type"],
                "room": dialog.result["room"]
            }

            # Проверка пересечений
            for l in self.lessons:
                if l["day_idx"] == lesson["day_idx"]:
                    if not (lesson["end"] <= l["start"] or lesson["start"] >= l["end"]):
                        messagebox.showerror("Ошибка",
                                             f"Пересечение с '{l['name']}' ({l['start']}-{l['end']})")
                        return

            self.lessons.append(lesson)
            self.next_id += 1
            self._save_data()
            self._draw_grid()
            messagebox.showinfo("Успех", "Занятие добавлено!")

    def _edit_lesson(self, lesson):
        """Редактировать занятие."""
        dialog = LessonDialog(self, self.DAYS, self.TYPES, lesson)
        if dialog.result:
            lesson["name"] = dialog.result["name"]
            lesson["day_idx"] = dialog.result["day_idx"]
            lesson["day"] = self.DAYS[dialog.result["day_idx"]]
            lesson["start"] = dialog.result["start"]
            lesson["end"] = dialog.result["end"]
            lesson["type"] = dialog.result["type"]
            lesson["room"] = dialog.result["room"]

            self._save_data()
            self._draw_grid()
            messagebox.showinfo("Успех", "Занятие обновлено!")

    def _delete_lesson(self, lesson):
        """Удалить занятие."""
        if messagebox.askyesno("Подтверждение", f"Удалить '{lesson['name']}'?"):
            self.lessons.remove(lesson)
            self._save_data()
            self._draw_grid()
            messagebox.showinfo("Успех", "Занятие удалено!")

    def _show_stats(self):
        """Показать статистику."""
        if not self.lessons:
            messagebox.showinfo("Статистика", "Нет занятий")
            return

        by_day = {}
        by_type = {}

        for lesson in self.lessons:
            day = lesson["day"]
            by_day[day] = by_day.get(day, 0) + 1

            ltype = lesson["type"]
            by_type[ltype] = by_type.get(ltype, 0) + 1

        msg = f"📊 Статистика расписания\n\n"
        msg += f"Всего занятий: {len(self.lessons)}\n\n"

        msg += "📅 По дням:\n"
        for day in self.DAYS:
            count = by_day.get(day, 0)
            if count > 0:
                msg += f"   {day}: {count}\n"

        msg += f"\n📚 По типам:\n"
        for ltype, count in by_type.items():
            msg += f"   {ltype}: {count}\n"

        messagebox.showinfo("Статистика", msg)

    def _save_data(self):
        data = {
            "lessons": self.lessons,
            "next_id": self.next_id
        }
        with open(self.DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_data(self):
        if Path(self.DATA_FILE).exists():
            try:
                with open(self.DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.lessons = data.get("lessons", [])
                self.next_id = data.get("next_id", 1)
                self._draw_grid()
            except Exception as e:
                print(f"Ошибка загрузки: {e}")


class LessonDialog(simpledialog.Dialog):
    def __init__(self, parent, days, types, lesson=None):
        self.days = days
        self.types = types
        self.edit_lesson = lesson
        self.result = None
        super().__init__(parent, title="Редактировать" if lesson else "Новое занятие")

    def body(self, master):
        tk.Label(master, text="Название:").grid(row=0, sticky="w", pady=5)
        self.name_entry = tk.Entry(master, width=40)
        self.name_entry.grid(row=1, sticky="ew", pady=5)

        tk.Label(master, text="День:").grid(row=2, sticky="w", pady=5)
        self.day_var = tk.StringVar(value=self.days[0])
        day_combo = ttk.Combobox(master, textvariable=self.day_var,
                                 values=self.days, state="readonly", width=37)
        day_combo.grid(row=3, sticky="ew", pady=5)

        tk.Label(master, text="Начало (ЧЧ:ММ):").grid(row=4, sticky="w", pady=5)
        self.start_entry = tk.Entry(master, width=20)
        self.start_entry.grid(row=5, sticky="w", pady=5)
        self.start_entry.insert(0, "09:00")

        tk.Label(master, text="Конец (ЧЧ:ММ):").grid(row=4, column=1, sticky="w", pady=5, padx=(20, 0))
        self.end_entry = tk.Entry(master, width=20)
        self.end_entry.grid(row=5, column=1, sticky="w", pady=5, padx=(20, 0))
        self.end_entry.insert(0, "10:30")

        tk.Label(master, text="Тип:").grid(row=6, sticky="w", pady=5)
        self.type_var = tk.StringVar(value=self.types[0])
        type_combo = ttk.Combobox(master, textvariable=self.type_var,
                                  values=self.types, state="readonly", width=37)
        type_combo.grid(row=7, sticky="ew", pady=5)

        tk.Label(master, text="Аудитория:").grid(row=8, sticky="w", pady=5)
        self.room_entry = tk.Entry(master, width=40)
        self.room_entry.grid(row=9, sticky="ew", pady=5)

        if self.edit_lesson:
            self.name_entry.insert(0, self.edit_lesson["name"])
            self.day_var.set(self.edit_lesson["day"])
            self.start_entry.delete(0, "end")
            self.start_entry.insert(0, self.edit_lesson["start"])
            self.end_entry.delete(0, "end")
            self.end_entry.insert(0, self.edit_lesson["end"])
            self.type_var.set(self.edit_lesson["type"])
            self.room_entry.insert(0, self.edit_lesson["room"])

        return self.name_entry

    def apply(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Введите название")
            return

        start = self.start_entry.get().strip()
        end = self.end_entry.get().strip()

        if end <= start:
            messagebox.showerror("Ошибка", "Время конца должно быть позже начала")
            return

        self.result = {
            "name": name,
            "day_idx": self.days.index(self.day_var.get()),
            "start": start,
            "end": end,
            "type": self.type_var.get(),
            "room": self.room_entry.get().strip()
        }