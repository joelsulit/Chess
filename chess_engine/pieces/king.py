def is_valid_move(_piece, sr, sc, dr, dc, _board):
    return max(abs(sr - dr), abs(sc - dc)) == 1
