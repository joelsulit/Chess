def convert_position(position):
    cols = "abcdefgh"
    position = position.strip().lower()

    if len(position) != 2 or position[0] not in cols or position[1] not in "12345678":
        raise ValueError("Invalid board coordinate.")

    row = 8 - int(position[1])
    col = cols.index(position[0])
    return row, col


def parse_move_input(command, turn):
    cleaned = command.strip()
    if not cleaned:
        raise ValueError("Empty command.")

    castling = cleaned.lower().replace("0", "o")
    if castling in {"o-o", "oo"}:
        return ("e1", "g1", None) if turn == "w" else ("e8", "g8", None)
    if castling in {"o-o-o", "ooo"}:
        return ("e1", "c1", None) if turn == "w" else ("e8", "c8", None)

    parts = cleaned.split()
    if len(parts) == 1:
        token = parts[0].lower()
        if len(token) in {4, 5}:
            start = token[:2]
            end = token[2:4]
            promo = token[4].upper() if len(token) == 5 else None
            return start, end, promo
        raise ValueError("Invalid move format.")

    if len(parts) in {2, 3}:
        start = parts[0]
        end = parts[1]
        promo = parts[2].upper() if len(parts) == 3 else None
        return start, end, promo

    raise ValueError("Invalid move format.")
