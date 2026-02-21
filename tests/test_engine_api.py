from web_app import app


def test_engine_move_endpoint_from_start():
    with app.test_client() as client:
        created = client.post("/api/games")
        assert created.status_code == 200
        game_id = created.get_json()["game_id"]

        moved = client.post(f"/api/games/{game_id}/engine-move", json={})
        assert moved.status_code == 200

        payload = moved.get_json()
        assert payload["move_source"] in {"stockfish", "fallback"}
        assert payload["move_side"] == "w"
        assert isinstance(payload["played_move"], str)
        assert len(payload["played_move"]) in {4, 5}
        assert payload["turn"] == "b"


def test_engine_move_after_player_move():
    with app.test_client() as client:
        created = client.post("/api/games")
        game_id = created.get_json()["game_id"]

        user_move = client.post(f"/api/games/{game_id}/moves", json={"move": "e2e4"})
        assert user_move.status_code == 200
        assert user_move.get_json()["turn"] == "b"

        moved = client.post(
            f"/api/games/{game_id}/engine-move",
            json={"use_stockfish": False},
        )
        assert moved.status_code == 200
        payload = moved.get_json()
        assert payload["move_source"] == "fallback"
        assert payload["move_side"] == "b"
        assert payload["turn"] == "w"


def test_engine_levels_supported():
    with app.test_client() as client:
        for level in ("easy", "hard", "very_hard"):
            created = client.post("/api/games")
            game_id = created.get_json()["game_id"]

            moved = client.post(
                f"/api/games/{game_id}/engine-move",
                json={"level": level, "use_stockfish": False},
            )
            assert moved.status_code == 200
            payload = moved.get_json()
            assert payload["move_source"] == "fallback"
            assert payload["played_move"]
