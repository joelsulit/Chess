from chess_engine.constants import PROMOTION_OPTIONS


def needs_promotion(piece, destination_row):
    return piece[1] == "P" and destination_row in {0, 7}


def normalize_promotion_choice(choice):
    if choice is None:
        return None

    normalized = choice.strip().upper()
    if normalized in PROMOTION_OPTIONS:
        return normalized
    return None
