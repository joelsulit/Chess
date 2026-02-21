def get_castling_move_type(
    piece,
    sr,
    sc,
    dr,
    dc,
    board,
    castling_rights,
    is_in_check,
    is_square_attacked,
    opponent_color,
):
    color = piece[0]
    home_row = 7 if color == "w" else 0

    if (sr, sc) != (home_row, 4):
        return None

    if is_in_check(color, board):
        return None

    if dc == 6:
        if not castling_rights[color + "K"]:
            return None
        if board[home_row][7] != color + "R":
            return None
        if board[home_row][5] != "." or board[home_row][6] != ".":
            return None
        if is_square_attacked(board, home_row, 5, opponent_color):
            return None
        if is_square_attacked(board, home_row, 6, opponent_color):
            return None
        return "castle_kingside"

    if dc == 2:
        if not castling_rights[color + "Q"]:
            return None
        if board[home_row][0] != color + "R":
            return None
        if board[home_row][1] != "." or board[home_row][2] != ".":
            return None
        if board[home_row][3] != ".":
            return None
        if is_square_attacked(board, home_row, 3, opponent_color):
            return None
        if is_square_attacked(board, home_row, 2, opponent_color):
            return None
        return "castle_queenside"

    return None
