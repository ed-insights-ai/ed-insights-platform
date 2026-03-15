# ── Team stats ──────────────────────────────────────────────


def test_team_stats_empty(client):
    resp = client.get("/api/stats/team")
    assert resp.status_code == 200
    assert resp.json() == []


def test_team_stats_with_data(client, seed_team_stats):
    resp = client.get("/api/stats/team")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    row = data[0]
    assert "school_name" in row
    assert "total_goals" in row


def test_team_stats_filter_school(client, seed_team_stats):
    resp = client.get("/api/stats/team", params={"school": "HU"})
    assert resp.status_code == 200


def test_team_stats_invalid_school(client, seed_schools):
    resp = client.get("/api/stats/team", params={"school": "NOPE"})
    assert resp.status_code == 404


# ── Player leaderboard ──────────────────────────────────────


def test_player_leaderboard_empty(client):
    resp = client.get("/api/stats/players")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_player_leaderboard_default_sort(client, seed_player_stats):
    resp = client.get("/api/stats/players")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    # Default sort is by goals descending
    goals = [p["total_goals"] for p in body["items"]]
    assert goals == sorted(goals, reverse=True)


def test_player_leaderboard_sort_assists(client, seed_player_stats):
    resp = client.get("/api/stats/players", params={"sort": "assists"})
    assert resp.status_code == 200
    body = resp.json()
    assists = [p["total_assists"] for p in body["items"]]
    assert assists == sorted(assists, reverse=True)


def test_player_leaderboard_sort_minutes(client, seed_player_stats):
    resp = client.get("/api/stats/players", params={"sort": "minutes"})
    assert resp.status_code == 200


def test_player_leaderboard_sort_shots(client, seed_player_stats):
    resp = client.get("/api/stats/players", params={"sort": "shots"})
    assert resp.status_code == 200


def test_player_leaderboard_invalid_sort(client, seed_schools):
    resp = client.get("/api/stats/players", params={"sort": "invalid"})
    assert resp.status_code == 400
    assert "Invalid sort" in resp.json()["detail"]


def test_player_leaderboard_pagination(client, seed_player_stats):
    resp = client.get("/api/stats/players", params={"limit": 1, "offset": 0})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["total"] == 2


def test_player_leaderboard_filter_school(client, seed_player_stats):
    resp = client.get("/api/stats/players", params={"school": "HU"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2


def test_player_leaderboard_invalid_school(client, seed_schools):
    resp = client.get("/api/stats/players", params={"school": "NOPE"})
    assert resp.status_code == 404
