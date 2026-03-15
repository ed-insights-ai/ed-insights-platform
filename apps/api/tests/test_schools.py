def test_list_schools_empty(client):
    resp = client.get("/api/schools")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_schools(client, seed_schools):
    resp = client.get("/api/schools")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    names = [s["name"] for s in data]
    assert names == sorted(names)  # ordered alphabetically
    assert data[0]["abbreviation"] in ("HU", "MSU")
