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


@dataclass
class InterviewQuestion:
    text: str
    expected_yes: bool = True


@dataclass
class CandidateSession:
    question_index: int = 0
    answers: list[str] | None = None
    score: int = 0
    started: bool = False

    def __post_init__(self) -> None:
        if self.answers is None:
            self.answers = []


INTERVIEW_START_KEYWORDS = (
    "собеседование",
    "интервью",
    "анкета",
    "хочу пройти",
    "хочу откликнуться",
    "готов пройти",
    "начать",
)

INTERVIEW_QUESTIONS: tuple[InterviewQuestion, ...] = (
    InterviewQuestion("У вас есть коммерческий опыт в Python, Java или JavaScript?"),
    InterviewQuestion("Вы уверенно работаете в команде и умеете договариваться с коллегами?"),
    InterviewQuestion("Вы умеете работать в условиях многозадачности и соблюдать дедлайны?"),
    InterviewQuestion("Вы спокойно справляетесь со стрессовыми ситуациями на работе?"),
    InterviewQuestion("Вы конструктивно решаете конфликты без эскалации?"),
    InterviewQuestion("Вы регулярно учитесь и развиваете профессиональные навыки?"),
    InterviewQuestion("За последний год вы проходили курсы или обучение по профессии?"),
    InterviewQuestion("Вам интересен именно наш продукт и вы хотите развиваться в компании?"),
    InterviewQuestion("Вы готовы к командировкам или изменениям графика при необходимости?"),
    InterviewQuestion("Ваши зарплатные ожидания соответствуют рыночной вилке вакансии?"),
)


class VacancyResponder:
    def __init__(self, vacancy_info: VacancyInfo | None = None):
        self.vacancy_info = vacancy_info
        self.sessions: dict[str, CandidateSession] = {}
        self.completed_candidates: set[str] = set()

    def update(self, vacancy_info: VacancyInfo | None) -> None:
        self.vacancy_info = vacancy_info

    def answer(self, sender: str, text: str) -> str:
        if sender not in self.sessions and sender not in self.completed_candidates:
            return self._start_interview(sender)

        if self._should_start_interview(text):
            return self._start_interview(sender)

        session = self.sessions.get(sender)
        if session and session.started:
            return self._handle_interview_answer(sender, text, session)

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

    def _should_start_interview(self, text: str) -> bool:
        normalized = text.lower()
        return any(token in normalized for token in INTERVIEW_START_KEYWORDS)

    def _start_interview(self, sender: str) -> str:
        self.sessions[sender] = CandidateSession(started=True)
        first_question = INTERVIEW_QUESTIONS[0].text
        return (
            "Запускаю интервью из 10 вопросов. Отвечайте только: да или нет.\n"
            f"Вопрос 1/{len(INTERVIEW_QUESTIONS)}: {first_question}"
        )

    def _handle_interview_answer(self, sender: str, text: str, session: CandidateSession) -> str:
        parsed_answer = self._parse_yes_no(text)
        if parsed_answer is None:
            current_question = INTERVIEW_QUESTIONS[session.question_index].text
            return (
                "Пожалуйста, ответьте только 'да' или 'нет'.\n"
                f"Вопрос {session.question_index + 1}/{len(INTERVIEW_QUESTIONS)}: {current_question}"
            )

        question = INTERVIEW_QUESTIONS[session.question_index]
        session.answers.append("да" if parsed_answer else "нет")
        session.score += self._score_answer(parsed_answer, question)
        session.question_index += 1

        if session.question_index >= len(INTERVIEW_QUESTIONS):
            return self._finish_interview(sender, session)

        next_question = INTERVIEW_QUESTIONS[session.question_index].text
        return f"Вопрос {session.question_index + 1}/{len(INTERVIEW_QUESTIONS)}: {next_question}"

    def _score_answer(self, answer_yes: bool, question: InterviewQuestion) -> int:
        return 1 if answer_yes == question.expected_yes else 0

    def _parse_yes_no(self, text: str) -> bool | None:
        normalized = text.lower().strip()
        if normalized in {"да", "yes", "y", "+"}:
            return True
        if normalized in {"нет", "no", "n", "-"}:
            return False
        return None

    def _finish_interview(self, sender: str, session: CandidateSession) -> str:
        max_score = len(INTERVIEW_QUESTIONS)
        threshold = 7
        is_fit = session.score >= threshold

        verdict = "Подходит" if is_fit else "Пока не подходит"
        explanation = (
            "Кандидат дал достаточно положительных ответов по ключевым критериям."
            if is_fit
            else "Недостаточно положительных ответов по ключевым критериям."
        )
        summary = f"Итог интервью: {verdict}. Балл: {session.score}/{max_score}. {explanation}"

        del self.sessions[sender]
        self.completed_candidates.add(sender)
        return summary

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
                "Для интервью напишите: собеседование."
            )

        return (
            f"Вакансия: {self.vacancy_info.title}. Могу подсказать по зарплате, опыту, графику и отклику. "
            "Для интервью напишите: собеседование."
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
