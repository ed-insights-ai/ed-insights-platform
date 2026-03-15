import pytest


@pytest.mark.anyio
async def test_list_schools_empty(client):
    resp = await client.get("/api/schools")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_list_schools(client, seed_schools):
    resp = await client.get("/api/schools")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    names = [s["name"] for s in data]
    assert names == sorted(names)  # ordered alphabetically
    assert data[0]["abbreviation"] in ("HU", "MSU")
