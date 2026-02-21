from .bishop import is_valid_move as bishop_move
from .king import is_valid_move as king_move
from .knight import is_valid_move as knight_move
from .pawn import is_valid_move as pawn_move
from .queen import is_valid_move as queen_move
from .rook import is_valid_move as rook_move

MOVE_VALIDATORS = {
    "P": pawn_move,
    "R": rook_move,
    "N": knight_move,
    "B": bishop_move,
    "Q": queen_move,
    "K": king_move,
}
