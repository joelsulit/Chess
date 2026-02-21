def clear_path(sr, sc, dr, dc, board):
    step_r = 0 if sr == dr else (1 if dr > sr else -1)
    step_c = 0 if sc == dc else (1 if dc > sc else -1)

    r, c = sr + step_r, sc + step_c

    while (r, c) != (dr, dc):
        if board[r][c] != ".":
            return False
        r += step_r
        c += step_c

    return True
