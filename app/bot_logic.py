from __future__ import annotations

import re
from dataclasses import dataclass


TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class VacancyInfo:
    title: str
    salary: str
    experience: str
    employment: str
    schedule: str
    address: str
    snippet: str
    apply_url: str


class VacancyResponder:
    def __init__(self, vacancy_info: VacancyInfo | None = None):
        self.vacancy_info = vacancy_info

    def update(self, vacancy_info: VacancyInfo | None) -> None:
        self.vacancy_info = vacancy_info

    def answer(self, text: str) -> str:
        if not text.strip():
            return "Напишите ваш вопрос по вакансии разработчика, и я отвечу."

        normalized = text.lower()

        if any(k in normalized for k in ["зп", "зарп", "salary", "оклад", "сколько плат"]):
            return self._salary_answer()

        if any(k in normalized for k in ["опыт", "experience", "junior", "middle", "senior"]):
            return self._experience_answer()

        if any(k in normalized for k in ["график", "удален", "офис", "формат", "schedule"]):
            return self._schedule_answer()

        if any(k in normalized for k in ["стек", "технолог", "обязанност", "что делать"]):
            return self._stack_answer()

        if any(k in normalized for k in ["отклик", "как откликнуться", "apply", "ссылка"]):
            return self._apply_answer()

        return self._default_answer()

    def _salary_answer(self) -> str:
        if not self.vacancy_info:
            return "По зарплате пока нет данных в HH. Напишите рекрутеру, чтобы уточнить вилку."
        return f"По вакансии '{self.vacancy_info.title}' зарплата: {self.vacancy_info.salary}."

    def _experience_answer(self) -> str:
        if not self.vacancy_info:
            return "Требования по опыту лучше уточнить у рекрутера — данные из HH пока не загружены."
        return f"Требуемый опыт: {self.vacancy_info.experience}."

    def _schedule_answer(self) -> str:
        if not self.vacancy_info:
            return "Формат работы и график лучше уточнить у рекрутера."
        return (
            f"Формат: {self.vacancy_info.employment}, график: {self.vacancy_info.schedule}. "
            f"Локация: {self.vacancy_info.address}."
        )

    def _stack_answer(self) -> str:
        if not self.vacancy_info:
            return "По стеку пока нет данных. Можете прислать ваш опыт, и рекрутер свяжется с вами."
        return f"Коротко по задачам/стеку: {self.vacancy_info.snippet}"

    def _apply_answer(self) -> str:
        if not self.vacancy_info:
            return "Чтобы откликнуться, отправьте резюме рекрутеру или ссылку на ваш HH профиль."
        return f"Откликнуться можно здесь: {self.vacancy_info.apply_url}"

    def _default_answer(self) -> str:
        if not self.vacancy_info:
            return (
                "Я отвечаю на вопросы по вакансии разработчика: зарплата, опыт, график, стек, отклик. "
                "Напишите, что именно интересует."
            )

        return (
            f"Вакансия: {self.vacancy_info.title}. Могу подсказать по зарплате, опыту, графику и отклику. "
            "Сформулируйте вопрос подробнее."
        )


def map_vacancy(raw: dict) -> VacancyInfo:
    salary_data = raw.get("salary") or {}
    salary_from = salary_data.get("from")
    salary_to = salary_data.get("to")
    currency = salary_data.get("currency") or ""

    if salary_from and salary_to:
        salary = f"{salary_from}-{salary_to} {currency}".strip()
    elif salary_from:
        salary = f"от {salary_from} {currency}".strip()
    elif salary_to:
        salary = f"до {salary_to} {currency}".strip()
    else:
        salary = "не указана"

    description = raw.get("description") or ""
    clean_description = TAG_RE.sub(" ", description)
    clean_description = re.sub(r"\s+", " ", clean_description).strip()

    return VacancyInfo(
        title=raw.get("name") or "Вакансия разработчика",
        salary=salary,
        experience=(raw.get("experience") or {}).get("name") or "не указан",
        employment=(raw.get("employment") or {}).get("name") or "не указан",
        schedule=(raw.get("schedule") or {}).get("name") or "не указан",
        address=((raw.get("address") or {}).get("city") or "не указан"),
        snippet=clean_description[:350] + ("..." if len(clean_description) > 350 else ""),
        apply_url=raw.get("alternate_url") or "",
    )
