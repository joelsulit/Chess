from chess_engine.constants import PROMOTION_OPTIONS


def apply_move_to_board(board, move, promotion_piece):
    board[move.sr][move.sc] = "."

    if move.special == "en_passant":
        cap_row, cap_col = move.capture_square
        board[cap_row][cap_col] = "."
    elif move.special == "castle_kingside":
        board[move.sr][5] = board[move.sr][7]
        board[move.sr][7] = "."
    elif move.special == "castle_queenside":
        board[move.sr][3] = board[move.sr][0]
        board[move.sr][0] = "."

    final_piece = move.piece
    if move.promotion:
        choice = (promotion_piece or "Q").upper()
        if choice not in PROMOTION_OPTIONS:
            choice = "Q"
        final_piece = move.piece[0] + choice

    board[move.dr][move.dc] = final_piece


def update_castling_rights(castling_rights, move):
    piece = move.piece
    captured = move.target

    if piece == "wK":
        castling_rights["wK"] = False
        castling_rights["wQ"] = False
    elif piece == "bK":
        castling_rights["bK"] = False
        castling_rights["bQ"] = False
    elif piece == "wR":
        if (move.sr, move.sc) == (7, 0):
            castling_rights["wQ"] = False
        elif (move.sr, move.sc) == (7, 7):
            castling_rights["wK"] = False
    elif piece == "bR":
        if (move.sr, move.sc) == (0, 0):
            castling_rights["bQ"] = False
        elif (move.sr, move.sc) == (0, 7):
            castling_rights["bK"] = False

    if captured == "wR":
        if (move.dr, move.dc) == (7, 0):
            castling_rights["wQ"] = False
        elif (move.dr, move.dc) == (7, 7):
            castling_rights["wK"] = False
    elif captured == "bR":
        if (move.dr, move.dc) == (0, 0):
            castling_rights["bQ"] = False
        elif (move.dr, move.dc) == (0, 7):
            castling_rights["bK"] = False
