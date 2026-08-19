import httpx

from app.config.settings import settings


class SmartThetaClient:
    """
    Client for communicating with the SmartTheta/Market API.
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = (
            base_url or settings.smarttheta_base_url
        ).rstrip("/")

    async def get(
        self,
        endpoint: str,
        headers: dict[str, str] | None = None,
        params: dict | None = None,
    ):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.get(
                url,
                headers=headers,
                params=params,
            )

        response.raise_for_status()

        return response.json()

    async def get_market_data(
        self,
        symbol: str,
    ):
        return await self.get(
            f"/api/market/{symbol.upper()}"
        )

    async def get_market_history(
        self,
        symbol: str,
        limit: int = 20,
    ):
        return await self.get(
            f"/api/market/{symbol.upper()}/history",
            params={
                "limit": limit,
            },
        )

    async def get_live_market_data(self):
        return await self.get(
            "/api/market/live"
        )
