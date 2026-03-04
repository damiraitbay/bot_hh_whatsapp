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
    options: tuple[tuple[str, int], ...]


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
    InterviewQuestion(
        text="Работаете ли вы в настоящее время?",
        options=(
            ("ДА, я работаю и ищу подработку", 0),
            ("НЕТ, я мама", 10),
            ("НЕТ, я в поиске работы", 5),
            ("НЕТ, я студент / школьник", 5),
        ),
    ),
    InterviewQuestion(
        text="Работаете ли вы более 8 часов в день и более 5 дней в неделю?",
        options=(("ДА", 0), ("НЕТ", 5)),
    ),
    InterviewQuestion(
        text="Вы работаете менее 40 часов или более 40 часов в неделю?",
        options=(("Менее 40 часов", 5), ("Более 40 часов", 0)),
    ),
    InterviewQuestion(
        text="Сколько часов в неделю вы реально можете работать (с учётом вечернего и ночного времени)?",
        options=(
            ("2 часа", 5),
            ("4 часа", 10),
            ("8 часов", 5),
            ("10 часов", 5),
        ),
    ),
    InterviewQuestion(
        text="Как вы оцениваете свои навыки работы с компьютером? Оценка от 1 до 10 (где 10 — очень высокий уровень).",
        options=(
            ("10", 3),
            ("9", 3),
            ("8", 3),
            ("7", 3),
            ("6", 3),
            ("5", -50),
            ("4", -50),
            ("3", -50),
            ("2", -50),
            ("1", -50),
        ),
    ),
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
        first_question = self._format_question(0)
        return (
            "Здравствуйте,\n\n"
            "Благодарим вас за отклик на вакансию с возможностью работы из дома (Homeoffice).\n\n"
            "Просим вас с пониманием отнестись к тому, что в рамках короткого этапа отбора "
            "мы хотели бы задать несколько вопросов. Цель — заранее определить, сможете ли вы "
            "работать необходимое количество часов в формате Homeoffice.\n\n"
            "Пожалуйста, отвечайте номером варианта (например: 1, 2, 3...) "
            "или текстом выбранного варианта.\n\n"
            f"{first_question}"
        )

    def _handle_interview_answer(self, sender: str, text: str, session: CandidateSession) -> str:
        parsed_score = self._parse_answer(session.question_index, text)
        if parsed_score is None:
            current_question = self._format_question(session.question_index)
            return (
                "Не удалось распознать ответ. Пожалуйста, укажите номер варианта или точный текст варианта.\n\n"
                f"{current_question}"
            )

        session.answers.append(text.strip())
        session.score += parsed_score
        session.question_index += 1

        if session.question_index >= len(INTERVIEW_QUESTIONS):
            return self._finish_interview(sender, session)

        return self._format_question(session.question_index)

    def _format_question(self, index: int) -> str:
        question = INTERVIEW_QUESTIONS[index]
        lines = [f"Вопрос {index + 1}/{len(INTERVIEW_QUESTIONS)}:", question.text, ""]
        lines.extend(f"{option_index}. {label}" for option_index, (label, _) in enumerate(question.options, start=1))
        return "\n".join(lines)

    def _parse_answer(self, question_index: int, text: str) -> int | None:
        question = INTERVIEW_QUESTIONS[question_index]
        normalized = re.sub(r"\s+", " ", text.lower().strip())

        if normalized.isdigit():
            option_number = int(normalized)
            if 1 <= option_number <= len(question.options):
                return question.options[option_number - 1][1]

        for label, score in question.options:
            normalized_label = re.sub(r"\s+", " ", label.lower().strip())
            if normalized == normalized_label:
                return score

        return None

    def _finish_interview(self, sender: str, session: CandidateSession) -> str:
        if session.score < 10:
            summary = (
                "Результат: менее 10 баллов.\n"
                "К сожалению, вы не подходите под требования, так как, вероятно, "
                "не сможете обеспечить минимум 60 рабочих часов в месяц."
            )
        else:
            summary = (
                "Результат: более 10 баллов.\n"
                "Мы будем рады пригласить вас на собеседование.\n"
                "Пожалуйста, свяжитесь напрямую с Александром Хаасом через WhatsApp для назначения встречи.\n\n"
                "Телефон: +7 707 358 55 74"
            )

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
