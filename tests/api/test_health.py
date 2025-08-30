
from httpx import AsyncClient


async def test_health(client: AsyncClient, override_get_db):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
