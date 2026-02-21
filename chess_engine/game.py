import copy

from chess_engine.board_state import create_initial_board, find_king
from chess_engine.constants import PROMOTION_OPTIONS
from chess_engine.models import Move
from chess_engine.notation import convert_position, parse_move_input
from chess_engine.pieces import MOVE_VALIDATORS
from chess_engine.pieces.pawn import is_attack_move as pawn_attack_move
from chess_engine.rules.attacks import is_square_attacked as square_attacked_rule
from chess_engine.rules.castling import get_castling_move_type
from chess_engine.rules.draws import build_position_key, is_insufficient_material
from chess_engine.rules.en_passant import is_en_passant_capture, next_en_passant_target
from chess_engine.rules.move_application import apply_move_to_board, update_castling_rights
from chess_engine.rules.promotion import needs_promotion, normalize_promotion_choice
from chess_engine.ui import print_board


class Game:
    def __init__(self):
        self.board = create_initial_board()
        self.turn = "w"
        self.castling_rights = {
            "wK": True,
            "wQ": True,
            "bK": True,
            "bQ": True,
        }
        self.en_passant_target = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.position_counts = {}
        self._undo_stack = []
        self.record_position()

    @staticmethod
    def opponent(color):
        return "b" if color == "w" else "w"

    @staticmethod
    def in_bounds(row, col):
        return 0 <= row < 8 and 0 <= col < 8

    @staticmethod
    def coords_to_square(row, col):
        files = "abcdefgh"
        return f"{files[col]}{8 - row}"

    @staticmethod
    def square_to_coords(square):
        return convert_position(square)

    def get_position_key(self):
        return build_position_key(
            self.board,
            self.turn,
            self.castling_rights,
            self.en_passant_target,
        )

    def record_position(self):
        key = self.get_position_key()
        self.position_counts[key] = self.position_counts.get(key, 0) + 1

    def _snapshot(self):
        return {
            "board": copy.deepcopy(self.board),
            "turn": self.turn,
            "castling_rights": dict(self.castling_rights),
            "en_passant_target": self.en_passant_target,
            "halfmove_clock": self.halfmove_clock,
            "fullmove_number": self.fullmove_number,
            "position_counts": dict(self.position_counts),
        }

    def _restore_snapshot(self, snapshot):
        self.board = copy.deepcopy(snapshot["board"])
        self.turn = snapshot["turn"]
        self.castling_rights = dict(snapshot["castling_rights"])
        self.en_passant_target = snapshot["en_passant_target"]
        self.halfmove_clock = snapshot["halfmove_clock"]
        self.fullmove_number = snapshot["fullmove_number"]
        self.position_counts = dict(snapshot["position_counts"])

    def is_threefold_repetition(self):
        return self.position_counts.get(self.get_position_key(), 0) >= 3

    def is_fivefold_repetition(self):
        return self.position_counts.get(self.get_position_key(), 0) >= 5

    def is_fifty_move_draw(self):
        return self.halfmove_clock >= 100

    def is_seventy_five_move_draw(self):
        return self.halfmove_clock >= 150

    def is_square_attacked(self, board, row, col, attacker_color):
        return square_attacked_rule(
            board,
            row,
            col,
            attacker_color,
            MOVE_VALIDATORS,
            pawn_attack_move,
        )

    def is_in_check(self, color, board=None):
        board = board if board is not None else self.board
        king_pos = find_king(board, color)
        if king_pos is None:
            return True

        return self.is_square_attacked(board, king_pos[0], king_pos[1], self.opponent(color))

    def build_move(self, sr, sc, dr, dc, color=None, board=None):
        board = board if board is not None else self.board

        if not self.in_bounds(sr, sc) or not self.in_bounds(dr, dc):
            return None
        if (sr, sc) == (dr, dc):
            return None

        piece = board[sr][sc]
        if piece == ".":
            return None
        if color is not None and piece[0] != color:
            return None

        target = board[dr][dc]
        if target != "." and target[0] == piece[0]:
            return None
        if target != "." and target[1] == "K":
            return None

        move = Move(
            sr=sr,
            sc=sc,
            dr=dr,
            dc=dc,
            piece=piece,
            target=target if target != "." else None,
            special=None,
            promotion=False,
            is_capture=target != ".",
            capture_square=(dr, dc) if target != "." else None,
        )

        piece_type = piece[1]

        if piece_type == "P":
            if MOVE_VALIDATORS["P"](piece, sr, sc, dr, dc, board):
                pass
            elif is_en_passant_capture(
                piece,
                sr,
                sc,
                dr,
                dc,
                board,
                self.en_passant_target,
                self.opponent(piece[0]),
            ):
                move.special = "en_passant"
                move.is_capture = True
                move.capture_square = (sr, dc)
                move.target = self.opponent(piece[0]) + "P"
            else:
                return None

            move.promotion = needs_promotion(piece, dr)
            return move

        if piece_type == "K" and sr == dr and abs(dc - sc) == 2:
            castle_type = get_castling_move_type(
                piece,
                sr,
                sc,
                dr,
                dc,
                board,
                self.castling_rights,
                self.is_in_check,
                self.is_square_attacked,
                self.opponent(piece[0]),
            )
            if castle_type is None:
                return None
            move.special = castle_type
            return move

        validator = MOVE_VALIDATORS.get(piece_type)
        if validator is None:
            return None
        if not validator(piece, sr, sc, dr, dc, board):
            return None

        return move

    def would_leave_king_in_check(self, move, promotion_piece="Q"):
        temp_board = copy.deepcopy(self.board)
        apply_move_to_board(temp_board, move, promotion_piece)
        return self.is_in_check(move.piece[0], temp_board)

    def is_valid_move(self, piece, sr, sc, dr, dc, promotion_piece="Q"):
        move = self.build_move(sr, sc, dr, dc, color=piece[0])
        if move is None:
            return False
        return not self.would_leave_king_in_check(move, promotion_piece)

    def get_legal_moves(self, color=None):
        color = color or self.turn
        legal = []

        for sr in range(8):
            for sc in range(8):
                piece = self.board[sr][sc]
                if piece == "." or piece[0] != color:
                    continue

                for dr in range(8):
                    for dc in range(8):
                        move = self.build_move(sr, sc, dr, dc, color=color)
                        if move is None:
                            continue

                        if move.promotion:
                            for option in sorted(PROMOTION_OPTIONS):
                                if not self.would_leave_king_in_check(move, option):
                                    legal.append((move, option))
                        else:
                            if not self.would_leave_king_in_check(move):
                                legal.append((move, None))

        return legal

    def move_to_uci(self, move, promotion=None):
        token = self.coords_to_square(move.sr, move.sc) + self.coords_to_square(move.dr, move.dc)
        if move.promotion:
            token += (promotion or "Q").lower()
        return token

    def parse_uci_move(self, uci_move):
        token = (uci_move or "").strip().lower()
        if len(token) not in {4, 5}:
            return None, None

        start = token[:2]
        end = token[2:4]
        promotion = token[4].upper() if len(token) == 5 else None

        try:
            sr, sc = self.square_to_coords(start)
            dr, dc = self.square_to_coords(end)
        except ValueError:
            return None, None

        piece = self.board[sr][sc]
        if piece == "." or piece[0] != self.turn:
            return None, None

        move = self.build_move(sr, sc, dr, dc, color=self.turn)
        if move is None:
            return None, None

        if move.promotion and promotion not in PROMOTION_OPTIONS:
            return None, None
        if not move.promotion:
            promotion = None

        if self.would_leave_king_in_check(move, promotion):
            return None, None

        return move, promotion

    def apply_uci_move(self, uci_move):
        move, promotion = self.parse_uci_move(uci_move)
        if move is None:
            return False
        self.commit_move(move, promotion)
        return True

    def to_fen(self):
        fen_rows = []
        for row in self.board:
            empty_count = 0
            fen_row = []
            for piece in row:
                if piece == ".":
                    empty_count += 1
                    continue

                if empty_count:
                    fen_row.append(str(empty_count))
                    empty_count = 0

                symbol = piece[1]
                fen_row.append(symbol.upper() if piece[0] == "w" else symbol.lower())

            if empty_count:
                fen_row.append(str(empty_count))

            fen_rows.append("".join(fen_row))

        castling = ""
        if self.castling_rights["wK"]:
            castling += "K"
        if self.castling_rights["wQ"]:
            castling += "Q"
        if self.castling_rights["bK"]:
            castling += "k"
        if self.castling_rights["bQ"]:
            castling += "q"
        if not castling:
            castling = "-"

        en_passant = "-"
        if self.en_passant_target is not None:
            en_passant = self.coords_to_square(
                self.en_passant_target[0],
                self.en_passant_target[1],
            )

        return (
            f"{'/'.join(fen_rows)} "
            f"{self.turn} "
            f"{castling} "
            f"{en_passant} "
            f"{self.halfmove_clock} "
            f"{self.fullmove_number}"
        )

    def has_any_legal_moves(self, color):
        for sr in range(8):
            for sc in range(8):
                piece = self.board[sr][sc]
                if piece == "." or piece[0] != color:
                    continue

                for dr in range(8):
                    for dc in range(8):
                        move = self.build_move(sr, sc, dr, dc, color=color)
                        if move is None:
                            continue

                        if move.promotion:
                            for option in PROMOTION_OPTIONS:
                                if not self.would_leave_king_in_check(move, option):
                                    return True
                        elif not self.would_leave_king_in_check(move):
                            return True

        return False

    def is_checkmate(self, color):
        return self.is_in_check(color) and not self.has_any_legal_moves(color)

    def is_stalemate(self, color):
        return not self.is_in_check(color) and not self.has_any_legal_moves(color)

    def is_insufficient_material(self):
        return is_insufficient_material(self.board)

    def commit_move(self, move, promotion_piece=None):
        self._undo_stack.append(self._snapshot())
        update_castling_rights(self.castling_rights, move)
        apply_move_to_board(self.board, move, promotion_piece)
        self.en_passant_target = next_en_passant_target(move)

        if move.piece[1] == "P" or move.is_capture:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        moving_color = move.piece[0]
        self.turn = self.opponent(moving_color)
        if moving_color == "b":
            self.fullmove_number += 1

        self.record_position()

    def undo_last_move(self, steps=1):
        try:
            steps = int(steps)
        except (TypeError, ValueError):
            steps = 1

        if steps < 1:
            return 0

        undone = 0
        for _ in range(steps):
            if not self._undo_stack:
                break
            snapshot = self._undo_stack.pop()
            self._restore_snapshot(snapshot)
            undone += 1

        return undone

    def play(self):
        while True:
            print_board(self.board)
            print(f"{self.turn.upper()}'s Turn")

            if self.is_in_check(self.turn):
                print(f"{self.turn.upper()} is in check!")

            command = input("Enter move (e2e4, e2 e4, O-O) or q to quit: ").strip()
            if command.lower() == "q":
                break

            try:
                start, end, promotion_piece = parse_move_input(command, self.turn)
                sr, sc = convert_position(start)
                dr, dc = convert_position(end)
                promotion_piece = normalize_promotion_choice(promotion_piece)
            except ValueError:
                print("Invalid input format! Example: e2e4, e2 e4, e7e8q, O-O")
                continue

            piece = self.board[sr][sc]
            if piece == "." or piece[0] != self.turn:
                print("Invalid piece!")
                continue

            move = self.build_move(sr, sc, dr, dc, color=self.turn)
            if move is None:
                print("Invalid move!")
                continue

            if move.promotion:
                while promotion_piece not in PROMOTION_OPTIONS:
                    promotion_piece = normalize_promotion_choice(
                        input("Promote to (Q/R/B/N): ").strip()
                    )
            elif promotion_piece is not None:
                print("Promotion piece only applies when a pawn reaches last rank.")
                continue

            if self.would_leave_king_in_check(move, promotion_piece):
                print("Illegal move: your king would be in check!")
                continue

            moving_side = self.turn
            self.commit_move(move, promotion_piece)

            if self.is_checkmate(self.turn):
                print_board(self.board)
                print(f"Checkmate! {moving_side.upper()} wins.")
                break

            if self.is_stalemate(self.turn):
                print_board(self.board)
                print("Draw by stalemate.")
                break

            if self.is_insufficient_material():
                print_board(self.board)
                print("Draw by insufficient material.")
                break

            if self.is_fivefold_repetition():
                print_board(self.board)
                print("Draw by fivefold repetition.")
                break

            if self.is_seventy_five_move_draw():
                print_board(self.board)
                print("Draw by seventy-five-move rule.")
                break

            if self.is_threefold_repetition():
                print_board(self.board)
                print("Draw by threefold repetition.")
                break

            if self.is_fifty_move_draw():
                print_board(self.board)
                print("Draw by fifty-move rule.")
                break
