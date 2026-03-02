from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


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
    positive_keywords: tuple[str, ...] = ()
    negative_keywords: tuple[str, ...] = ()
    min_answer_len: int = 20


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
    InterviewQuestion("Почему вы хотите работать у нас?", ("компания", "продукт", "миссия", "команда"), ("деньги",)),
    InterviewQuestion("Почему вы выбрали именно эту профессию/отрасль?", ("интерес", "развит", "технолог", "опыт"), ()),
    InterviewQuestion("Почему мы должны выбрать именно вас?", ("результат", "опыт", "ответствен", "проект"), ()),
    InterviewQuestion("Что вас мотивирует на работе?", ("рост", "команда", "результат", "задач"), ("только деньги",)),
    InterviewQuestion("Где вы видите себя через 3–5 лет?", ("развит", "эксперт", "лид", "рост"), ("не знаю",)),
    InterviewQuestion("Почему вы ушли с предыдущего места работы?", ("рост", "новый", "задач", "проект"), ("конфликт", "ненавижу", "плохой начальник")),
    InterviewQuestion("Какие ваши сильные стороны?", ("ответствен", "коммуникац", "аналит", "инициатив"), ()),
    InterviewQuestion("Какие ваши слабые стороны?", ("работаю над", "улучшаю", "исправляю"), ("нет слабых",)),
    InterviewQuestion("Есть ли у вас опыт работы с Python/Java/JavaScript?", ("python", "java", "javascript", "js"), ()),
    InterviewQuestion("Расскажите о вашем опыте работы с командой.", ("команда", "коммуникац", "совмест", "планирован"), ("не люблю команду",)),
    InterviewQuestion("Умеете ли вы работать в условиях многозадачности?", ("приоритет", "план", "дедлайн"), ("не умею",)),
    InterviewQuestion("Опишите проект, которым вы гордитесь.", ("проект", "результат", "метрик", "влияние"), ()),
    InterviewQuestion("Как вы справляетесь со стрессом?", ("план", "приоритет", "спокойно", "перерыв"), ("не справляюсь",)),
    InterviewQuestion("Как вы решаете конфликтные ситуации?", ("диалог", "обсуж", "факт", "компромисс"), ("кричу", "игнорирую")),
    InterviewQuestion("Как вы организуете своё время?", ("план", "календар", "приоритет", "задач"), ("хаотично",)),
    InterviewQuestion("Какие качества помогают вам достигать результатов?", ("дисциплин", "ответствен", "систем", "инициатив"), ()),
    InterviewQuestion("Расскажите о случае, когда вы ошиблись и как исправили ситуацию.", ("ошиб", "исправ", "вывод", "урок"), ("никогда не ошибаюсь",)),
    InterviewQuestion("Что вы знаете о нашей компании?", ("компания", "продукт", "рынок", "клиент"), ("ничего",)),
    InterviewQuestion("Какие тренды в отрасли вы считаете важными?", ("автоматизац", "ai", "безопас", "облако"), ()),
    InterviewQuestion("Почему вам интересен именно наш продукт/услуга?", ("продукт", "польза", "клиент", "ценност"), ("без разницы",)),
    InterviewQuestion("Какие курсы или тренинги вы проходили за последний год?", ("курс", "обуч", "сертификат", "прошел"), ("ничего",)),
    InterviewQuestion("Какие навыки вы планируете развивать?", ("развит", "план", "навык", "изуч"), ("не планирую",)),
    InterviewQuestion("Как вы обучаетесь новым технологиям или инструментам?", ("документац", "практик", "курс", "проект"), ()),
    InterviewQuestion("Каковы ваши ожидания по зарплате?", ("рыноч", "вилка", "обсуждаем", "kzt", "usd", "руб"), ("любая",)),
    InterviewQuestion("Готовы ли вы к командировкам или смене графика?", ("готов", "возможно", "обсуждаем"), ("не готов",)),
    InterviewQuestion("Предпочитаете удалённую работу или офис?", ("удален", "офис", "гибрид"), ("без разницы",)),
)


class VacancyResponder:
    def __init__(self, vacancy_info: VacancyInfo | None = None):
        self.vacancy_info = vacancy_info
        self.sessions: dict[str, CandidateSession] = {}

    def update(self, vacancy_info: VacancyInfo | None) -> None:
        self.vacancy_info = vacancy_info

    def answer(self, sender: str, text: str) -> str:
        if not text.strip():
            return "Напишите ваш вопрос по вакансии разработчика, и я отвечу."

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
            "Запускаю интервью. Ответьте на вопросы по очереди.\n"
            f"Вопрос 1/{len(INTERVIEW_QUESTIONS)}: {first_question}"
        )

    def _handle_interview_answer(self, sender: str, text: str, session: CandidateSession) -> str:
        question = INTERVIEW_QUESTIONS[session.question_index]
        session.answers.append(text.strip())
        session.score += self._score_answer(text, question)
        session.question_index += 1

        if session.question_index >= len(INTERVIEW_QUESTIONS):
            return self._finish_interview(sender, session)

        next_question = INTERVIEW_QUESTIONS[session.question_index].text
        return f"Вопрос {session.question_index + 1}/{len(INTERVIEW_QUESTIONS)}: {next_question}"

    def _score_answer(self, text: str, question: InterviewQuestion) -> int:
        normalized = text.lower().strip()
        score = 0
        if len(normalized) >= question.min_answer_len:
            score += 1
        score += self._keyword_hits(normalized, question.positive_keywords)
        score -= self._keyword_hits(normalized, question.negative_keywords)
        return score

    def _keyword_hits(self, text: str, keywords: Iterable[str]) -> int:
        return sum(1 for keyword in keywords if keyword in text)

    def _finish_interview(self, sender: str, session: CandidateSession) -> str:
        max_score = len(INTERVIEW_QUESTIONS) * 3
        threshold = max(20, int(max_score * 0.35))
        is_fit = session.score >= threshold

        verdict = "Подходит" if is_fit else "Пока не подходит"
        explanation = (
            "Ответы содержат релевантный опыт, мотивацию и готовность к развитию."
            if is_fit
            else "В ответах мало конкретики по опыту, мотивации или рабочим условиям."
        )
        summary = f"Итог интервью: {verdict}. Балл: {session.score}/{max_score}. {explanation}"

        del self.sessions[sender]
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
