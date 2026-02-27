from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from .bot_logic import VacancyResponder, map_vacancy
from .config import settings
from .hh_client import HHClient

logger = logging.getLogger(__name__)

hh_client = HHClient()
responder = VacancyResponder()


def _validate_twilio_request(request: Request, form_data: dict[str, str]) -> bool:
    if not settings.twilio_auth_token:
        return True

    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        return False

    validator = RequestValidator(settings.twilio_auth_token)
    url = str(request.url)
    return validator.validate(url, form_data, signature)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.hh_vacancy_id:
        try:
            raw_vacancy = await hh_client.get_vacancy(settings.hh_vacancy_id)
            if raw_vacancy:
                responder.update(map_vacancy(raw_vacancy))
                logger.info("HH vacancy loaded: %s", settings.hh_vacancy_id)
            else:
                logger.warning("HH vacancy was not loaded: %s", settings.hh_vacancy_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to load HH vacancy: %s", exc)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.post("/webhooks/twilio/whatsapp")
async def twilio_whatsapp_webhook(
    request: Request,
    Body: str = Form(default=""),
    From: str = Form(default=""),
) -> PlainTextResponse:
    form_data = {k: v for k, v in {"Body": Body, "From": From}.items() if isinstance(v, str)}
    if not _validate_twilio_request(request, form_data):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    answer = responder.answer(Body)

    response = MessagingResponse()
    response.message(answer)

    logger.info("Incoming WhatsApp message from %s: %s", From, Body)
    logger.info("Outgoing reply: %s", answer)

    return PlainTextResponse(str(response), media_type="application/xml")
