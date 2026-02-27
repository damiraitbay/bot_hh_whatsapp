# HH WhatsApp Bot (FastAPI + Twilio)

Бот принимает входящие WhatsApp-сообщения через Twilio Webhook и отвечает на типовые вопросы по вакансии разработчика.
Данные по вакансии подтягиваются из HH API по `HH_VACANCY_ID`.

## 1) Локально (опционально)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## 2) Временный деплой на Render (рекомендуется)

В репозитории уже есть `render.yaml`, поэтому деплой делается как Blueprint.

1. Запушьте проект в GitHub.
2. В Render откройте: `New` -> `Blueprint`.
3. Выберите репозиторий и создайте сервис.
4. В Render задайте env-переменные:
   - `APP_BASE_URL` = ваш URL Render (например `https://hh-whatsapp-bot.onrender.com`)
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_WHATSAPP_NUMBER` (обычно `whatsapp:+14155238886` для Sandbox)
   - `HH_VACANCY_ID` (число из ссылки `https://hh.ru/vacancy/<id>`)
5. Дождитесь статуса `Live` и проверьте `GET /health`.

## 3) Webhook в Twilio

В Twilio Sandbox для WhatsApp укажите webhook:

`POST {APP_BASE_URL}/webhooks/twilio/whatsapp`

Пример: `https://hh-whatsapp-bot.onrender.com/webhooks/twilio/whatsapp`

## 4) Проверка

- `GET /health` -> `{"status":"ok"}`
- отправьте сообщение в WhatsApp Sandbox, например: `Какая зарплата?`

## Что умеет бот

- Отвечает по ключевым темам: зарплата, опыт, график, стек, отклик.
- Если данных из HH нет, дает fallback-ответ и просит уточнение.

## Важно

- Free план на Render подходит для тестов, не для продакшена.
- Для более умных ответов можно добавить LLM (OpenAI) поверх текущей логики.
