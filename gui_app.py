import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from hh_parser import HHParser
from collections import Counter
import pandas as pd
import re

class HHparserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Парсер вакансий HH.ru")
        self.root.geometry("850x800")
        self.parser = HHParser()
        self.current_data = None
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.create_main_tab()
        self.create_analytics_tab()
        self.create_info_panel()
        self.create_save_section()
    
    def create_main_tab(self):
        """Создает основную вкладку с поиском вакансий"""
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Главная")
        
        style = ttk.Style()
        style.configure("TFrame", padding=10)
        style.configure("TButton", padding=5)
        
        main_frame = ttk.Frame(self.main_tab)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Ключевое слово:").pack(pady=5)
        self.keyword_entry = ttk.Entry(main_frame, width=50)
        self.keyword_entry.pack(pady=5)
        
        ttk.Label(main_frame, text="Стоп-слова (через запятую или пробел):").pack(pady=5)
        self.stop_words_entry = ttk.Entry(main_frame, width=50)
        self.stop_words_entry.pack(pady=5)
        
        selection_frame = ttk.Frame(main_frame)
        selection_frame.pack(pady=10, fill=tk.X)
        
        region_frame = ttk.LabelFrame(selection_frame, text="Регион поиска")
        region_frame.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
        
        self.area_var = tk.StringVar(value="1")
        areas = [("Москва", "1"), ("Санкт-Петербург", "2"), ("Россия", "113")]
        for text, value in areas:
            ttk.Radiobutton(region_frame, text=text, variable=self.area_var, value=value).pack(anchor=tk.W)
        
        schedule_frame = ttk.LabelFrame(selection_frame, text="Формат работы")
        schedule_frame.pack(side=tk.RIGHT, padx=10, fill=tk.BOTH, expand=True)
        
        self.schedule_vars = {
            "remote": tk.BooleanVar(),
            "hybrid": tk.BooleanVar(),
            "office": tk.BooleanVar()
        }
        
        ttk.Checkbutton(
            schedule_frame, 
            text="Удалённая работа", 
            variable=self.schedule_vars["remote"]
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            schedule_frame, 
            text="Гибридный формат", 
            variable=self.schedule_vars["hybrid"]
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            schedule_frame, 
            text="Офис", 
            variable=self.schedule_vars["office"]
        ).pack(anchor=tk.W, pady=2)
        
        self.search_btn = ttk.Button(main_frame, text="Найти вакансии", command=self.run_search)
        self.search_btn.pack(pady=15)
        
        self.progress = ttk.Progressbar(main_frame, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=5)
        self.progress.pack_forget()
        
        self.status_var = tk.StringVar(value="Готов к работе")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.pack()
        
        self.detailed_status_var = tk.StringVar(value="")
        self.detailed_status_label = ttk.Label(main_frame, textvariable=self.detailed_status_var)
        self.detailed_status_label.pack()
    
    def create_analytics_tab(self):
        """Создает вкладку для анализа навыков"""
        self.analytics_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.analytics_tab, text="Аналитика")
        
        skills_frame = ttk.LabelFrame(self.analytics_tab, text="Анализ навыков")
        skills_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(
            skills_frame, 
            text="Сохранить статистику по текущей выборке"
        ).pack(pady=(5, 0))
        
        self.save_btn = ttk.Button(
            skills_frame, 
            text="Сохранить статистику", 
            command=self.save_skills,
            state=tk.DISABLED
        )
        self.save_btn.pack(pady=5)
        
        ttk.Label(
            skills_frame, 
            text="Создать статистику из существующей выборки"
        ).pack(pady=(15, 0))
        
        self.create_stats_btn = ttk.Button(
            skills_frame, 
            text="Создать статистику", 
            command=self.create_stats_from_file
        )
        self.create_stats_btn.pack(pady=5)
        
        self.skills_status = ttk.Label(skills_frame, text="")
        self.skills_status.pack(pady=10)
    
    def create_info_panel(self):
        """Создает панель информации с вертикальным расположением статистики"""
        self.info_frame = ttk.LabelFrame(self.root, text="Информация о результатах")
        self.info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Основной контейнер для колонок
        columns_container = ttk.Frame(self.info_frame)
        columns_container.pack(fill=tk.X, pady=5)
        
        # Колонка 1: Основная информация
        col1 = ttk.Frame(columns_container)
        col1.pack(side=tk.LEFT, fill=tk.Y, padx=10, expand=True)
        
        self.total_var = tk.StringVar(value="Всего вакансий: -")
        self.with_salary_var = tk.StringVar(value="С зарплатой: -")
        self.last_date_var = tk.StringVar(value="Последняя дата: -")
        self.pages_var = tk.StringVar(value="Страниц: -/-")
        
        ttk.Label(col1, textvariable=self.total_var, anchor="w").pack(fill=tk.X)
        ttk.Label(col1, textvariable=self.with_salary_var, anchor="w").pack(fill=tk.X)
        ttk.Label(col1, textvariable=self.last_date_var, anchor="w").pack(fill=tk.X)
        ttk.Label(col1, textvariable=self.pages_var, anchor="w").pack(fill=tk.X)
        
        # Колонка 2: Опыт работы
        col2 = ttk.Frame(columns_container)
        col2.pack(side=tk.LEFT, fill=tk.Y, padx=10, expand=True)
        
        ttk.Label(col2, text="Опыт работы:", font=('TkDefaultFont', 9, 'bold')).pack(anchor="w")
        self.experience_vars = {}
        
        # Колонка 3: График работы
        col3 = ttk.Frame(columns_container)
        col3.pack(side=tk.LEFT, fill=tk.Y, padx=10, expand=True)
        
        ttk.Label(col3, text="График работы:", font=('TkDefaultFont', 9, 'bold')).pack(anchor="w")
        self.schedule_vars_stats = {}
        
        # Колонка 4: Контакты
        col4 = ttk.Frame(columns_container)
        col4.pack(side=tk.LEFT, fill=tk.Y, padx=10, expand=True)
        
        ttk.Label(col4, text="Контакты:", font=('TkDefaultFont', 9, 'bold')).pack(anchor="w")
        self.contacts_var = tk.StringVar(value="Указаны: - (-%)")
        ttk.Label(col4, textvariable=self.contacts_var, anchor="w").pack(fill=tk.X)
    
    def create_save_section(self):
        save_frame = ttk.LabelFrame(self.root, text="Сохранение результатов")
        save_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.save_results_btn = ttk.Button(
            save_frame, 
            text="Сохранить вакансии", 
            command=self.save_results,
            state=tk.DISABLED
        )
        self.save_results_btn.pack(pady=5)
        
        self.save_status = ttk.Label(save_frame, text="Данные не загружены")
        self.save_status.pack()
    
    def create_stats_from_file(self):
        """Создает статистику навыков из существующего файла"""
        try:
            filepath = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")]
            )
            
            if not filepath:
                return
            
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath)
            
            if "Ссылка" not in df.columns:
                messagebox.showerror("Ошибка", "В файле отсутствует колонка 'Ссылка'")
                return
            
            vacancy_ids = []
            for link in df["Ссылка"]:
                match = re.search(r'vacancy/(\d+)', str(link))
                if match:
                    vacancy_ids.append(match.group(1))
            
            if not vacancy_ids:
                messagebox.showerror("Ошибка", "Не удалось извлечь ID вакансий из ссылок")
                return
            
            self.status_var.set("Получение данных по вакансиям из файла...")
            self.root.update()
            
            vacancies_df = self.parser.get_vacancies_by_ids(vacancy_ids)
            
            if vacancies_df.empty:
                messagebox.showwarning("Предупреждение", "Не удалось получить данные по вакансиям")
                return
            
            all_skills = []
            for skills_str in vacancies_df["Ключевые навыки"]:
                if skills_str != "Не указаны":
                    skills = [s.strip() for s in skills_str.split(",")]
                    all_skills.extend(skills)
            
            if not all_skills:
                messagebox.showinfo("Информация", "В выбранных вакансиях не указаны ключевые навыки")
                return
            
            skills_counter = Counter(all_skills)
            skills_df = pd.DataFrame({
                "Навык": list(skills_counter.keys()),
                "Частота": list(skills_counter.values())
            }).sort_values("Частота", ascending=False)
            
            save_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile="ключевые_навыки_из_файла"
            )
            
            if save_path:
                skills_df.to_excel(save_path, index=False)
                self.skills_status.config(text=f"Файл с навыками сохранен: {save_path}")
                messagebox.showinfo("Успешно", "Статистика ключевых навыков создана и сохранена!")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании статистики:\n{str(e)}")
            self.skills_status.config(text="Ошибка создания статистики")
        finally:
            self.status_var.set("Готов к работе")
    
    def run_search(self):
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showerror("Ошибка", "Введите ключевое слово!")
            return
            
        try:
            area = self.area_var.get()
            stop_words = self.stop_words_entry.get().strip()
            
            schedules = {
                "remote": self.schedule_vars["remote"].get(),
                "hybrid": self.schedule_vars["hybrid"].get(),
                "office": self.schedule_vars["office"].get()
            }
            
            self.progress["value"] = 0
            self.progress.pack()
            self.status_var.set("Идет поиск вакансий...")
            self.root.update()
            
            self.search_btn.config(state=tk.DISABLED)
            self.save_results_btn.config(state=tk.DISABLED)
            self.save_btn.config(state=tk.DISABLED)
            
            self.current_data = self.parser.get_vacancies(
                keyword=keyword,
                area=area,
                stop_words=stop_words,
                schedules=schedules if any(schedules.values()) else None,
                progress_callback=self.update_progress
            )
            
            self.update_info_panel(self.current_data)
            self.save_results_btn.config(state=tk.NORMAL)
            self.save_btn.config(state=tk.NORMAL)
            self.status_var.set("Поиск завершен!")
            self.detailed_status_var.set(f"Найдено {len(self.current_data)} вакансий")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка:\n{str(e)}")
            self.status_var.set("Ошибка при выполнении")
            self.detailed_status_var.set("")
            self.reset_ui()
        finally:
            self.search_btn.config(state=tk.NORMAL)
            self.root.after(3000, lambda: self.progress.pack_forget())
    
    def save_skills(self):
        if self.current_data is None or self.current_data.empty:
            messagebox.showwarning("Ошибка", "Нет данных для анализа")
            return
            
        try:
            all_skills = []
            for skills_str in self.current_data["Ключевые навыки"]:
                if skills_str != "Не указаны":
                    skills = [s.strip() for s in skills_str.split(",")]
                    all_skills.extend(skills)
            
            if not all_skills:
                messagebox.showinfo("Информация", "В выбранных вакансиях не указаны ключевые навыки")
                return
            
            skills_counter = Counter(all_skills)
            
            skills_df = pd.DataFrame({
                "Навык": list(skills_counter.keys()),
                "Частота": list(skills_counter.values())
            })
            
            skills_df = skills_df.sort_values("Частота", ascending=False)
            
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile="ключевые_навыки_вакансий"
            )
            
            if filepath:
                skills_df.to_excel(filepath, index=False)
                self.skills_status.config(text=f"Файл с навыками сохранен: {filepath}")
                messagebox.showinfo("Успешно", "Статистика ключевых навыков сохранена!")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении навыков:\n{str(e)}")
            self.skills_status.config(text="Ошибка сохранения навыков")
    
    def update_progress(self, current, total):
        progress = int((current / total) * 100) if total > 0 else 0
        self.progress["value"] = progress
        self.detailed_status_var.set(f"Обработка страницы {current} из {total}")
        self.pages_var.set(f"Страниц: {current}/{total}")
        self.root.update_idletasks()
    
    def save_results(self):
        if self.current_data is None or self.current_data.empty:
            messagebox.showwarning("Ошибка", "Нет данных для сохранения")
            return
            
        try:
            keyword = self.keyword_entry.get().strip()
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[
                    ("Excel files", "*.xlsx"), 
                    ("CSV files", "*.csv"),
                    ("JSON files", "*.json")
                ],
                initialfile=f"вакансии_{keyword}"
            )
            
            if filepath:
                if filepath.endswith('.csv'):
                    self.current_data.to_csv(filepath, index=False)
                elif filepath.endswith('.json'):
                    self.current_data.to_json(filepath, orient='records', force_ascii=False)
                else:
                    self.current_data.to_excel(filepath, index=False)
                
                self.save_status.config(text=f"Файл сохранен: {filepath}")
                messagebox.showinfo("Успешно", "Данные сохранены!")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении:\n{str(e)}")
            self.save_status.config(text="Ошибка сохранения")
    
    def update_info_panel(self, df):
        total = len(df)
        if total == 0:
            self.reset_ui()
            return
        
        # Основная статистика
        with_salary = len(df[df['Зарплата'] != "Не указана"])
        last_date = df['Дата публикации'].max()
        
        self.total_var.set(f"Всего вакансий: {total}")
        self.with_salary_var.set(f"С зарплатой: {with_salary} ({with_salary/total*100:.1f}%)")
        self.last_date_var.set(f"Последняя дата: {last_date}")
        
        # Очищаем предыдущую статистику
        for col in [self.info_frame.winfo_children()[0].winfo_children()[1],  # Колонка опыта
                    self.info_frame.winfo_children()[0].winfo_children()[2]]: # Колонка графика
            for widget in col.winfo_children()[1:]:
                widget.destroy()
        
        # Статистика по опыту работы
        experience_stats = df['Опыт работы'].value_counts(normalize=True).mul(100).round(1)
        for exp, percent in experience_stats.items():
            count = len(df[df['Опыт работы'] == exp])
            label_text = f"{exp}: {count} ({percent}%)"
            ttk.Label(self.info_frame.winfo_children()[0].winfo_children()[1], 
                     text=label_text, anchor="w").pack(fill=tk.X)
        
        # Статистика по графику работы
        schedule_stats = df['График работы'].value_counts(normalize=True).mul(100).round(1)
        for schedule, percent in schedule_stats.items():
            count = len(df[df['График работы'] == schedule])
            label_text = f"{schedule}: {count} ({percent}%)"
            ttk.Label(self.info_frame.winfo_children()[0].winfo_children()[2], 
                     text=label_text, anchor="w").pack(fill=tk.X)
        
        # Статистика по контактам
        with_contacts = len(df[df['Контакты'] != "Не указаны"])
        percent = with_contacts / total * 100
        self.contacts_var.set(f"Указаны: {with_contacts} ({percent:.1f}%)")
    
    def reset_ui(self):
        self.total_var.set("Всего вакансий: -")
        self.with_salary_var.set("С зарплатой: -")
        self.last_date_var.set("Последняя дата: -")
        self.pages_var.set("Страниц: -/-")
        
        # Очищаем статистику
        for col in [self.info_frame.winfo_children()[0].winfo_children()[1],  # Колонка опыта
                    self.info_frame.winfo_children()[0].winfo_children()[2]]: # Колонка графика
            for widget in col.winfo_children()[1:]:
                widget.destroy()
        
        self.contacts_var.set("Указаны: - (-%)")
        self.save_status.config(text="Данные не загружены")
        self.skills_status.config(text="")
        self.save_results_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        self.status_var.set("Готов к работе")
        self.detailed_status_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = HHparserApp(root)
    root.mainloop()