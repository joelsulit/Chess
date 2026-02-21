from chess_engine.game import Game
from chess_engine.notation import convert_position

from tests.helpers import clear_board, play_move, reset_tracking


def test_fools_mate_checkmate():
    game = Game()
    play_move(game, "f2", "f3")
    play_move(game, "e7", "e5")
    play_move(game, "g2", "g4")
    play_move(game, "d8", "h4")
    assert game.is_checkmate("w")


def test_stalemate_detection():
    game = Game()
    clear_board(game, turn="b")
    game.board[0][0] = "bK"  # a8
    game.board[2][2] = "wK"  # c6
    game.board[1][2] = "wQ"  # c7
    reset_tracking(game)
    assert game.is_stalemate("b")


def test_castling_kingside():
    game = Game()
    clear_board(game, turn="w")
    game.board[7][4] = "wK"
    game.board[7][7] = "wR"
    game.board[0][4] = "bK"
    game.castling_rights = {"wK": True, "wQ": False, "bK": False, "bQ": False}
    reset_tracking(game)

    play_move(game, "e1", "g1")
    assert game.board[7][6] == "wK"
    assert game.board[7][5] == "wR"


def test_en_passant_capture():
    game = Game()
    play_move(game, "e2", "e4")
    play_move(game, "a7", "a6")
    play_move(game, "e4", "e5")
    play_move(game, "d7", "d5")

    move = game.build_move(*convert_position("e5"), *convert_position("d6"), color="w")
    assert move is not None
    assert move.special == "en_passant"
    game.commit_move(move)
    assert game.board[2][3] == "wP"
    assert game.board[3][3] == "."


def test_promotion_to_knight():
    game = Game()
    clear_board(game, turn="w")
    game.board[7][4] = "wK"
    game.board[0][7] = "bK"
    game.board[1][0] = "wP"
    reset_tracking(game)

    play_move(game, "a7", "a8", promotion="N")
    assert game.board[0][0] == "wN"


def test_repetition_and_draw_clocks():
    game = Game()
    for _ in range(2):
        play_move(game, "g1", "f3")
        play_move(game, "g8", "f6")
        play_move(game, "f3", "g1")
        play_move(game, "f6", "g8")
    assert game.is_threefold_repetition()

    game.halfmove_clock = 100
    assert game.is_fifty_move_draw()
    game.halfmove_clock = 150
    assert game.is_seventy_five_move_draw()


def test_insufficient_material_detection():
    game = Game()
    clear_board(game, turn="w")
    game.board[7][4] = "wK"
    game.board[0][4] = "bK"
    reset_tracking(game)
    assert game.is_insufficient_material()

    game.board[6][3] = "wB"
    game.board[1][6] = "wN"
    reset_tracking(game)
    assert not game.is_insufficient_material()
