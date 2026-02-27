from __future__ import annotations

import httpx

from .config import settings


class HHClient:
    async def get_vacancy(self, vacancy_id: str) -> dict | None:
        if not vacancy_id:
            return None

        url = f"{settings.hh_api_base_url}/vacancies/{vacancy_id}"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers={"User-Agent": "hh-whatsapp-bot/1.0"})

        if response.status_code == 200:
            return response.json()

        return None
