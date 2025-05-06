import requests
import pandas as pd
import time
import re
from typing import Optional, Callable, List, Union, Dict
from collections import Counter

class HHParser:
    def __init__(self):
        self.base_url = "https://api.hh.ru/vacancies"
        self.schedule_mapping = {
            "remote": "remote",
            "hybrid": "flexible",
            "office": "fullDay"
        }
    
    def get_vacancies(self, 
                    keyword: str, 
                    area: int = 1,
                    stop_words: Optional[Union[str, List[str]]] = None,
                    schedules: Optional[Dict[str, bool]] = None,
                    progress_callback: Optional[Callable[[int, int], None]] = None) -> pd.DataFrame:
        """Поиск вакансий с фильтрацией по формату работы"""
        vacancies = []
        keyword_lower = keyword.lower()
        total_pages = None
        
        stop_words_list = self._process_stop_words(stop_words)
        
        selected_schedules = []
        if schedules:
            selected_schedules = [self.schedule_mapping[key] for key, value in schedules.items() if value]
        
        page = 0
        while True:
            page += 1
            if progress_callback and total_pages:
                progress_callback(page, total_pages)
            
            params = {
                "text": keyword,
                "page": page - 1,
                "per_page": 100,
                "area": area,
                "enable_snippets": "true"
            }
            
            if selected_schedules:
                params["schedule"] = selected_schedules
            
            try:
                response = requests.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if total_pages is None:
                    total_pages = data.get("pages", 1)
                    if progress_callback:
                        progress_callback(0, total_pages)
                
                filtered_items = []
                for item in data.get("items", []):
                    # Получаем полную информацию о вакансии для доступа к ключевым навыкам
                    vacancy_id = item.get("id")
                    vacancy_details = self._get_vacancy_details(vacancy_id)
                    
                    title = (item.get("name") or "").lower()
                    snippet = item.get("snippet", {})
                    requirement = (snippet.get("requirement") or "").lower()
                    responsibility = (snippet.get("responsibility") or "").lower()
                    full_text = f"{title} {requirement} {responsibility}"
                    
                    keyword_match = full_text.strip() and re.search(rf'\b{re.escape(keyword_lower)}\b', full_text)
                    
                    stop_word_found = False
                    if stop_words_list:
                        for stop_word in stop_words_list:
                            if re.search(rf'\b{re.escape(stop_word)}\b', full_text):
                                stop_word_found = True
                                break
                    
                    if keyword_match and not stop_word_found:
                        # Добавляем навыки из деталей вакансии
                        item["key_skills"] = vacancy_details.get("key_skills", [])
                        filtered_items.append(item)
                
                vacancies.extend(filtered_items)
                
                if page >= total_pages:
                    break
                    
                time.sleep(0.6)
                
            except requests.exceptions.RequestException as e:
                raise Exception(f"Ошибка API: {str(e)}")
        
        return self._format_results(vacancies)
    
    def get_vacancies_by_ids(self, vacancy_ids: List[str]) -> pd.DataFrame:
        """Получает вакансии по списку ID"""
        vacancies = []
        for vacancy_id in vacancy_ids:
            try:
                vacancy_details = self._get_vacancy_details(vacancy_id)
                if vacancy_details:
                    vacancies.append(vacancy_details)
                time.sleep(0.2)
            except Exception as e:
                print(f"Ошибка при получении вакансии {vacancy_id}: {str(e)}")
        
        return self._format_results(vacancies)
    
    def _get_vacancy_details(self, vacancy_id: str) -> dict:
        """Получает полную информацию о вакансии, включая ключевые навыки"""
        try:
            response = requests.get(f"{self.base_url}/{vacancy_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return {}
    
    def _process_stop_words(self, stop_words: Optional[Union[str, List[str]]]) -> List[str]:
        if not stop_words:
            return []
        
        if isinstance(stop_words, str):
            stop_words = re.split(r'[, \t\n]+', stop_words.strip())
        
        return [word.lower().strip() for word in stop_words if word.strip()]
    
    def _format_results(self, vacancies: list) -> pd.DataFrame:
        results = []
        for vacancy in vacancies:
            salary = vacancy.get("salary")
            salary_str = self._format_salary(salary)
            
            schedule = vacancy.get("schedule", {})
            schedule_name = schedule.get("name") if schedule else "Не указан"
            
            # Получаем ключевые навыки
            skills = [skill.get("name") for skill in vacancy.get("key_skills", [])]
            
            results.append({
                "Компания": vacancy.get("employer", {}).get("name", "Не указано"),
                "Вакансия": vacancy.get("name", "Без названия"),
                "Зарплата": salary_str,
                "Формат работы": schedule_name,
                "Ключевые навыки": ", ".join(skills) if skills else "Не указаны",
                "Ссылка": f"https://hh.ru/vacancy/{vacancy.get('id', '')}",
                "Дата": vacancy.get("published_at", "")[:10],
                "Описание": self._get_description_snippet(vacancy.get("snippet", {}))
            })
        
        return pd.DataFrame(results)
    
    def _format_salary(self, salary: dict) -> str:
        if not salary:
            return "Не указана"
        from_sal = salary.get('from', '')
        to_sal = salary.get('to', '')
        currency = salary.get('currency', '')
        return f"{from_sal}-{to_sal} {currency}" if from_sal or to_sal else "Не указана"
    
    def _get_description_snippet(self, snippet: dict) -> str:
        req = snippet.get("requirement", "") or ""
        resp = snippet.get("responsibility", "") or ""
        return f"{req} {resp}".strip()