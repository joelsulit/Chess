import pytest

from chess_engine.game import Game


@pytest.fixture
def game():
    return Game()
