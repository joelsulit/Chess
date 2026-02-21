from .bishop import is_valid_move as bishop_move
from .rook import is_valid_move as rook_move


def is_valid_move(piece, sr, sc, dr, dc, board):
    return rook_move(piece, sr, sc, dr, dc, board) or bishop_move(
        piece, sr, sc, dr, dc, board
    )
