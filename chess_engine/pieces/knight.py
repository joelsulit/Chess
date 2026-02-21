def is_valid_move(_piece, sr, sc, dr, dc, _board):
    return (abs(sr - dr), abs(sc - dc)) in {(2, 1), (1, 2)}
