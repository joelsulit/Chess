import pytest

from chess_engine.notation import parse_move_input


def test_parse_compact_and_spaced_moves():
    assert parse_move_input("e2e4", "w") == ("e2", "e4", None)
    assert parse_move_input("e2 e4", "w") == ("e2", "e4", None)
    assert parse_move_input("e7e8q", "w") == ("e7", "e8", "Q")


def test_parse_castling_aliases():
    assert parse_move_input("o-o", "w") == ("e1", "g1", None)
    assert parse_move_input("0-0-0", "b") == ("e8", "c8", None)


def test_parse_invalid_move_raises():
    with pytest.raises(ValueError):
        parse_move_input("e2", "w")
