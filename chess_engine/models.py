from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Move:
    sr: int
    sc: int
    dr: int
    dc: int
    piece: str
    target: Optional[str] = None
    special: Optional[str] = None
    promotion: bool = False
    is_capture: bool = False
    capture_square: Optional[Tuple[int, int]] = None
