import threading
import uuid

from flask import Flask, jsonify, request

from chess_engine.constants import PROMOTION_OPTIONS
from chess_engine.engine import choose_engine_move
from chess_engine.game import Game
from chess_engine.notation import convert_position, parse_move_input
from chess_engine.rules.promotion import normalize_promotion_choice

app = Flask(__name__, static_folder="frontend", static_url_path="/")

_games = {}
_games_lock = threading.Lock()


def _opponent(color):
    return "b" if color == "w" else "w"


def _square_name(row, col):
    files = "abcdefgh"
    return f"{files[col]}{8 - row}"


def _serialize_outcome(game):
    side_to_move = game.turn
    check = game.is_in_check(side_to_move)

    if game.is_checkmate(side_to_move):
        winner = _opponent(side_to_move)
        return {
            "ended": True,
            "result": "checkmate",
            "winner": winner,
            "message": f"Checkmate! {winner.upper()} wins.",
            "check": True,
        }

    if game.is_stalemate(side_to_move):
        return {
            "ended": True,
            "result": "stalemate",
            "winner": None,
            "message": "Draw by stalemate.",
            "check": False,
        }

    if game.is_insufficient_material():
        return {
            "ended": True,
            "result": "insufficient_material",
            "winner": None,
            "message": "Draw by insufficient material.",
            "check": check,
        }

    if game.is_fivefold_repetition():
        return {
            "ended": True,
            "result": "fivefold_repetition",
            "winner": None,
            "message": "Draw by fivefold repetition.",
            "check": check,
        }

    if game.is_seventy_five_move_draw():
        return {
            "ended": True,
            "result": "seventy_five_move_rule",
            "winner": None,
            "message": "Draw by seventy-five-move rule.",
            "check": check,
        }

    if game.is_threefold_repetition():
        return {
            "ended": True,
            "result": "threefold_repetition",
            "winner": None,
            "message": "Draw by threefold repetition.",
            "check": check,
        }

    if game.is_fifty_move_draw():
        return {
            "ended": True,
            "result": "fifty_move_rule",
            "winner": None,
            "message": "Draw by fifty-move rule.",
            "check": check,
        }

    return {
        "ended": False,
        "result": None,
        "winner": None,
        "message": f"{side_to_move.upper()} to move.",
        "check": check,
    }


def _serialize_state(game_id, game, extra_message=None):
    outcome = _serialize_outcome(game)
    message = outcome["message"]
    if outcome["check"] and not outcome["ended"]:
        message = f"{message} {game.turn.upper()} is in check."

    if extra_message:
        message = f"{extra_message} {message}"

    return {
        "game_id": game_id,
        "board": game.board,
        "turn": game.turn,
        "fullmove_number": game.fullmove_number,
        "halfmove_clock": game.halfmove_clock,
        "castling_rights": dict(game.castling_rights),
        "en_passant_target": game.en_passant_target,
        "check": outcome["check"],
        "ended": outcome["ended"],
        "result": outcome["result"],
        "winner": outcome["winner"],
        "message": message.strip(),
    }


def _with_move_metadata(state_payload, played_move=None, move_side=None, move_source=None):
    if played_move is not None:
        state_payload["played_move"] = played_move
    if move_side is not None:
        state_payload["move_side"] = move_side
    if move_source is not None:
        state_payload["move_source"] = move_source
    return state_payload


def _get_game_or_404(game_id):
    with _games_lock:
        game = _games.get(game_id)
    if game is None:
        return None, (jsonify({"error": "Game not found."}), 404)
    return game, None


def _parse_level(value):
    normalized = (value or "hard").strip().lower().replace("-", "_")
    if normalized not in {"easy", "hard", "very_hard"}:
        normalized = "hard"
    return normalized


def _normalize_engine_knobs(level, skill_level, think_time_ms):
    level = _parse_level(level)
    if level == "easy":
        default_skill = 4
        default_time = 80
    elif level == "very_hard":
        default_skill = 20
        default_time = 900
    else:
        default_skill = 12
        default_time = 300

    try:
        parsed_skill = int(skill_level) if skill_level is not None else default_skill
    except (TypeError, ValueError):
        parsed_skill = default_skill

    try:
        parsed_time = int(think_time_ms) if think_time_ms is not None else default_time
    except (TypeError, ValueError):
        parsed_time = default_time

    parsed_skill = max(0, min(20, parsed_skill))
    parsed_time = max(30, min(3000, parsed_time))
    return level, parsed_skill, parsed_time


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.post("/api/games")
def create_game():
    game_id = str(uuid.uuid4())
    game = Game()

    with _games_lock:
        _games[game_id] = game

    return jsonify(_serialize_state(game_id, game))


@app.get("/api/games/<game_id>")
def get_game(game_id):
    game, error = _get_game_or_404(game_id)
    if error:
        return error
    return jsonify(_serialize_state(game_id, game))


@app.post("/api/games/<game_id>/reset")
def reset_game(game_id):
    _, error = _get_game_or_404(game_id)
    if error:
        return error

    game = Game()
    with _games_lock:
        _games[game_id] = game

    return jsonify(_serialize_state(game_id, game, extra_message="Game reset."))


@app.post("/api/games/<game_id>/moves")
def make_move(game_id):
    game, error = _get_game_or_404(game_id)
    if error:
        return error

    if _serialize_outcome(game)["ended"]:
        return jsonify({"error": "Game is already finished."}), 400

    payload = request.get_json(silent=True) or {}

    start = payload.get("start")
    end = payload.get("end")
    promotion = payload.get("promotion")
    move_text = payload.get("move")

    try:
        if move_text:
            start, end, parsed_promotion = parse_move_input(move_text, game.turn)
            if promotion is None:
                promotion = parsed_promotion

        if not start or not end:
            raise ValueError("Missing start/end.")

        start_row, start_col = convert_position(start)
        end_row, end_col = convert_position(end)
    except ValueError:
        return jsonify({"error": "Invalid move input."}), 400

    piece = game.board[start_row][start_col]
    if piece == "." or piece[0] != game.turn:
        return jsonify({"error": "Invalid piece selection."}), 400

    move = game.build_move(start_row, start_col, end_row, end_col, color=game.turn)
    if move is None:
        return jsonify({"error": "Invalid move."}), 400

    promotion = normalize_promotion_choice(promotion)
    if move.promotion and promotion not in PROMOTION_OPTIONS:
        return jsonify(
            {
                "error": "Promotion required. Choose Q, R, B, or N.",
                "promotion_required": True,
            }
        ), 400

    if not move.promotion:
        promotion = None

    if game.would_leave_king_in_check(move, promotion):
        return jsonify({"error": "Illegal move: king would be in check."}), 400

    move_side = game.turn
    game.commit_move(move, promotion)

    played_token = f"{start.lower()}{end.lower()}"
    played = f"{start.lower()}->{end.lower()}"
    if promotion:
        played_token = f"{played_token}{promotion.lower()}"
        played = f"{played}={promotion}"

    state = _serialize_state(game_id, game, extra_message=f"Played {played}.")
    return jsonify(
        _with_move_metadata(
            state,
            played_move=played_token,
            move_side=move_side,
            move_source="player",
        )
    )


@app.get("/api/games/<game_id>/legal-moves")
def legal_moves(game_id):
    game, error = _get_game_or_404(game_id)
    if error:
        return error

    start = (request.args.get("from") or "").strip().lower()
    try:
        sr, sc = convert_position(start)
    except ValueError:
        return jsonify({"from": start, "targets": []})

    piece = game.board[sr][sc]
    if piece == "." or piece[0] != game.turn:
        return jsonify({"from": start, "targets": []})

    targets = []
    for dr in range(8):
        for dc in range(8):
            move = game.build_move(sr, sc, dr, dc, color=game.turn)
            if move is None:
                continue

            if move.promotion:
                can_play = False
                for promotion in PROMOTION_OPTIONS:
                    if not game.would_leave_king_in_check(move, promotion):
                        can_play = True
                        break
                if not can_play:
                    continue
            else:
                if game.would_leave_king_in_check(move):
                    continue

            targets.append(_square_name(dr, dc))

    return jsonify({"from": start, "targets": targets})


@app.post("/api/games/<game_id>/engine-move")
def engine_move(game_id):
    game, error = _get_game_or_404(game_id)
    if error:
        return error

    if _serialize_outcome(game)["ended"]:
        return jsonify({"error": "Game is already finished."}), 400

    payload = request.get_json(silent=True) or {}
    level = payload.get("level", "hard")
    skill_level = payload.get("skill_level")
    think_time_ms = payload.get("think_time_ms")
    level, skill_level, think_time_ms = _normalize_engine_knobs(level, skill_level, think_time_ms)
    use_stockfish = payload.get("use_stockfish", True)
    if isinstance(use_stockfish, str):
        use_stockfish = use_stockfish.strip().lower() not in {"0", "false", "no", "off"}
    else:
        use_stockfish = bool(use_stockfish)

    try:
        move_token, source = choose_engine_move(
            game,
            skill_level=skill_level,
            think_time_ms=think_time_ms,
            use_stockfish=use_stockfish,
            level=level,
        )
    except Exception:
        return jsonify({"error": "Engine failed to choose a move."}), 500

    if not move_token:
        return jsonify({"error": "No legal engine move available."}), 400

    move_side = game.turn
    if not game.apply_uci_move(move_token):
        return jsonify({"error": "Engine produced an invalid move."}), 500

    state = _serialize_state(
        game_id,
        game,
        extra_message=f"Engine ({source}) played {move_token}.",
    )
    return jsonify(
        _with_move_metadata(
            state,
            played_move=move_token,
            move_side=move_side,
            move_source=source,
        )
    )


@app.post("/api/games/<game_id>/undo")
def undo_move(game_id):
    game, error = _get_game_or_404(game_id)
    if error:
        return error

    payload = request.get_json(silent=True) or {}
    steps = payload.get("steps", 1)

    try:
        steps = int(steps)
    except (TypeError, ValueError):
        steps = 1

    steps = max(1, min(10, steps))
    undone = game.undo_last_move(steps)
    if undone == 0:
        return jsonify({"error": "No moves to undo."}), 400

    state = _serialize_state(game_id, game, extra_message=f"Undid {undone} move(s).")
    state["undone_steps"] = undone
    return jsonify(state)


if __name__ == "__main__":
    app.run(debug=True)
