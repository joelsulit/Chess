def create_initial_board():
    board = [["." for _ in range(8)] for _ in range(8)]

    for i in range(8):
        board[1][i] = "bP"
        board[6][i] = "wP"

    board[0][0] = board[0][7] = "bR"
    board[7][0] = board[7][7] = "wR"

    board[0][1] = board[0][6] = "bN"
    board[7][1] = board[7][6] = "wN"

    board[0][2] = board[0][5] = "bB"
    board[7][2] = board[7][5] = "wB"

    board[0][3] = "bQ"
    board[0][4] = "bK"
    board[7][3] = "wQ"
    board[7][4] = "wK"

    return board


def find_king(board, color):
    target = color + "K"
    for row in range(8):
        for col in range(8):
            if board[row][col] == target:
                return row, col
    return None
