from chess_engine.game import Game
from web_app import app

from tests.helpers import play_move


def test_game_undo_last_move():
    game = Game()
    start_board = [row[:] for row in game.board]

    play_move(game, "e2", "e4")
    assert game.turn == "b"

    undone = game.undo_last_move()
    assert undone == 1
    assert game.turn == "w"
    assert game.board == start_board


def test_game_undo_multiple_moves():
    game = Game()
    play_move(game, "e2", "e4")
    play_move(game, "e7", "e5")
    play_move(game, "g1", "f3")
    assert game.turn == "b"

    undone = game.undo_last_move(2)
    assert undone == 2
    assert game.turn == "b"
    assert game.board[4][4] == "wP"  # e4
    assert game.board[3][4] == "."   # e5 undone


def test_undo_api():
    with app.test_client() as client:
        created = client.post("/api/games")
        game_id = created.get_json()["game_id"]

        m1 = client.post(f"/api/games/{game_id}/moves", json={"move": "e2e4"})
        assert m1.status_code == 200

        undo = client.post(f"/api/games/{game_id}/undo", json={"steps": 1})
        assert undo.status_code == 200
        payload = undo.get_json()
        assert payload["undone_steps"] == 1
        assert payload["turn"] == "w"
        assert payload["board"][6][4] == "wP"  # e2
        assert payload["board"][4][4] == "."   # e4 cleared


def test_undo_api_no_moves():
    with app.test_client() as client:
        created = client.post("/api/games")
        game_id = created.get_json()["game_id"]

        undo = client.post(f"/api/games/{game_id}/undo", json={"steps": 1})
        assert undo.status_code == 400
