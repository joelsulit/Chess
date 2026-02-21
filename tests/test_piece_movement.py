from chess_engine.notation import convert_position

from tests.helpers import play_move


def test_bishop_blocked_then_unblocked(game):
    blocked = game.build_move(*convert_position("f1"), *convert_position("b5"), color="w")
    assert blocked is None

    play_move(game, "e2", "e3")
    play_move(game, "a7", "a6")

    unblocked = game.build_move(
        *convert_position("f1"),
        *convert_position("b5"),
        color="w",
    )
    assert unblocked is not None


def test_bishop_can_capture_diagonal(game):
    play_move(game, "e2", "e3")
    play_move(game, "c7", "c6")
    play_move(game, "f1", "b5")
    play_move(game, "a7", "a6")
    play_move(game, "b5", "c6")

    row, col = convert_position("c6")
    assert game.board[row][col] == "wB"
