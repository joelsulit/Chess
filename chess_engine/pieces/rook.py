from .helpers import clear_path


def is_valid_move(_piece, sr, sc, dr, dc, board):
    if sr != dr and sc != dc:
        return False

    return clear_path(sr, sc, dr, dc, board)
