def is_valid_move(piece, sr, sc, dr, dc, board):
    direction = -1 if piece.startswith("w") else 1
    start_row = 6 if piece.startswith("w") else 1

    if sc == dc:
        if dr == sr + direction and board[dr][dc] == ".":
            return True

        if (
            sr == start_row
            and dr == sr + (2 * direction)
            and board[sr + direction][sc] == "."
            and board[dr][dc] == "."
        ):
            return True

    if is_attack_move(piece, sr, sc, dr, dc):
        if board[dr][dc] != "." and board[dr][dc][0] != piece[0]:
            return True

    return False


def is_attack_move(piece, sr, sc, dr, dc):
    direction = -1 if piece.startswith("w") else 1
    return dr == sr + direction and abs(dc - sc) == 1
