try:
    from colorama import Fore, init

    init(autoreset=True)
except ImportError:
    class _FallbackFore:
        CYAN = ""
        YELLOW = ""

    Fore = _FallbackFore()


def color_piece(piece):
    if piece == ".":
        return " . "

    if piece.startswith("w"):
        return Fore.CYAN + f"{piece:^3}"

    if piece.startswith("b"):
        return Fore.YELLOW + f"{piece:^3}"

    return f"{piece:^3}"


def print_board(board):
    print("\n    a   b   c   d   e   f   g   h")
    print("  +" + "---+" * 8)

    for row in range(8):
        print(8 - row, end=" |")
        for col in range(8):
            print(color_piece(board[row][col]) + "|", end="")
        print(f" {8-row}")
        print("  +" + "---+" * 8)

    print("    a   b   c   d   e   f   g   h\n")
