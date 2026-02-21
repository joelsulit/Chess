from chess_engine.notation import convert_position


def reset_tracking(game):
    game.position_counts = {}
    game.record_position()


def clear_board(game, turn="w"):
    game.board = [["." for _ in range(8)] for _ in range(8)]
    game.turn = turn
    game.castling_rights = {"wK": False, "wQ": False, "bK": False, "bQ": False}
    game.en_passant_target = None
    game.halfmove_clock = 0
    game.fullmove_number = 1
    reset_tracking(game)


def play_move(game, start, end, promotion=None):
    sr, sc = convert_position(start)
    dr, dc = convert_position(end)
    move = game.build_move(sr, sc, dr, dc, color=game.turn)
    assert move is not None, f"Invalid move: {start}->{end}"
    if move.promotion and promotion is None:
        promotion = "Q"
    assert not game.would_leave_king_in_check(move, promotion), (
        f"Move leaves king in check: {start}->{end}"
    )
    game.commit_move(move, promotion)
