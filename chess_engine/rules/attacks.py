def is_square_attacked(board, row, col, attacker_color, move_validators, pawn_attack_move):
    for src_row in range(8):
        for src_col in range(8):
            piece = board[src_row][src_col]
            if piece == "." or piece[0] != attacker_color:
                continue

            if piece[1] == "P":
                if pawn_attack_move(piece, src_row, src_col, row, col):
                    return True
                continue

            validator = move_validators.get(piece[1])
            if validator and validator(piece, src_row, src_col, row, col, board):
                return True

    return False
