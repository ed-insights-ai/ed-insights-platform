import pytest


@pytest.mark.anyio
async def test_list_games_empty(client):
    resp = await client.get("/api/games")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


@pytest.mark.anyio
async def test_list_games_all(client, seed_games):
    resp = await client.get("/api/games")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3


@pytest.mark.anyio
async def test_list_games_filter_by_school_abbrev(client, seed_games):
    resp = await client.get("/api/games", params={"school": "HU"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    for item in body["items"]:
        assert item["school_id"] == 1


@pytest.mark.anyio
async def test_list_games_filter_by_school_id(client, seed_games):
    resp = await client.get("/api/games", params={"school_id": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["game_id"] == 2001


@pytest.mark.anyio
async def test_list_games_filter_by_season(client, seed_games):
    resp = await client.get("/api/games", params={"season": 2024})
    assert resp.status_code == 200
    assert resp.json()["total"] == 3


@pytest.mark.anyio
async def test_list_games_invalid_school_404(client, seed_schools):
    resp = await client.get("/api/games", params={"school": "NOPE"})
    assert resp.status_code == 404
    assert "NOPE" in resp.json()["detail"]


@pytest.mark.anyio
async def test_list_games_pagination(client, seed_games):
    resp = await client.get("/api/games", params={"limit": 1, "offset": 0})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["total"] == 3
    assert body["limit"] == 1
    assert body["offset"] == 0


@pytest.mark.anyio
async def test_get_game_200(client, seed_games, seed_events):
    resp = await client.get("/api/games/1001")
    assert resp.status_code == 200
    body = resp.json()
    assert body["game_id"] == 1001
    assert body["venue"] == "Greene Stadium"
    assert isinstance(body["team_stats"], list)
    assert isinstance(body["player_stats"], list)
    assert isinstance(body["events"], list)
    assert len(body["events"]) == 1


@pytest.mark.anyio
async def test_get_game_404(client, seed_schools):
    resp = await client.get("/api/games/99999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()
