def is_en_passant_capture(piece, sr, sc, dr, dc, board, en_passant_target, opponent_color):
    if en_passant_target != (dr, dc):
        return False

    direction = -1 if piece[0] == "w" else 1
    if dr != sr + direction or abs(dc - sc) != 1:
        return False

    if board[dr][dc] != ".":
        return False

    return board[sr][dc] == opponent_color + "P"


def next_en_passant_target(move):
    if move.piece[1] == "P" and abs(move.dr - move.sr) == 2:
        return ((move.dr + move.sr) // 2, move.sc)
    return None


def get_effective_en_passant_target(board, en_passant_target, turn):
    if en_passant_target is None:
        return None

    row, col = en_passant_target
    source_row = row + (1 if turn == "w" else -1)
    if not (0 <= source_row < 8):
        return None

    for side_col in (col - 1, col + 1):
        if 0 <= side_col < 8 and board[source_row][side_col] == turn + "P":
            return en_passant_target

    return None
