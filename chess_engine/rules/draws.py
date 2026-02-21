from chess_engine.rules.en_passant import get_effective_en_passant_target


def build_position_key(board, turn, castling_rights, en_passant_target):
    board_key = tuple(tuple(row) for row in board)
    castling_key = (
        castling_rights["wK"],
        castling_rights["wQ"],
        castling_rights["bK"],
        castling_rights["bQ"],
    )
    effective_ep = get_effective_en_passant_target(board, en_passant_target, turn)
    return board_key, turn, castling_key, effective_ep


def is_insufficient_material(board):
    minor_pieces = []

    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece == "." or piece[1] == "K":
                continue

            if piece[1] in {"P", "R", "Q"}:
                return False

            minor_pieces.append((piece, row, col))

    if not minor_pieces:
        return True

    if len(minor_pieces) == 1:
        return True

    if len(minor_pieces) == 2:
        first_piece = minor_pieces[0][0]
        second_piece = minor_pieces[1][0]
        first_color = first_piece[0]
        second_color = second_piece[0]
        first_type = first_piece[1]
        second_type = second_piece[1]

        if first_color != second_color:
            return True

        if first_type == "N" and second_type == "N":
            return True

        return False

    return False
