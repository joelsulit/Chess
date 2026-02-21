import os
import random
from copy import deepcopy


PIECE_VALUES = {
    "P": 1,
    "N": 3,
    "B": 3,
    "R": 5,
    "Q": 9,
    "K": 0,
}


def _opponent(color):
    return "b" if color == "w" else "w"


def _material_balance(board, perspective):
    own = 0
    opp = 0

    for row in board:
        for piece in row:
            if piece == ".":
                continue
            value = PIECE_VALUES.get(piece[1], 0)
            if piece[0] == perspective:
                own += value
            else:
                opp += value

    return own - opp


def _evaluate_position(game, perspective):
    side_to_move = game.turn
    opponent = _opponent(side_to_move)

    if game.is_checkmate(side_to_move):
        return -10000 if side_to_move == perspective else 10000

    if game.is_stalemate(side_to_move):
        return 0

    score = _material_balance(game.board, perspective) * 10

    if game.is_in_check(_opponent(perspective)):
        score += 3
    if game.is_in_check(perspective):
        score -= 3

    return score


def _fallback_easy(game):
    legal = game.get_legal_moves(game.turn)
    if not legal:
        return None, "none"
    move, promotion = random.choice(legal)
    return game.move_to_uci(move, promotion), "fallback"


def _fallback_hard(game):
    legal = game.get_legal_moves(game.turn)
    if not legal:
        return None, "none"

    legal = game.get_legal_moves(game.turn)

    best_score = None
    best_tokens = []

    for move, promotion in legal:
        score = 0.0

        if move.target:
            score += PIECE_VALUES.get(move.target[1], 0)

        if promotion:
            score += PIECE_VALUES.get(promotion, 0) * 0.2

        token = game.move_to_uci(move, promotion)

        if best_score is None or score > best_score:
            best_score = score
            best_tokens = [token]
        elif score == best_score:
            best_tokens.append(token)

    return random.choice(best_tokens), "fallback"


def _fallback_very_hard(game):
    legal = game.get_legal_moves(game.turn)
    if not legal:
        return None, "none"

    perspective = game.turn
    best_score = None
    best_tokens = []

    for move, promotion in legal:
        token = game.move_to_uci(move, promotion)
        sim = deepcopy(game)
        if not sim.apply_uci_move(token):
            continue

        opponent_legal = sim.get_legal_moves(sim.turn)
        if not opponent_legal:
            score = _evaluate_position(sim, perspective)
        else:
            # 1-ply response search (engine move + opponent best reply).
            reply_scores = []
            for reply_move, reply_promo in opponent_legal:
                reply_token = sim.move_to_uci(reply_move, reply_promo)
                sim_reply = deepcopy(sim)
                if not sim_reply.apply_uci_move(reply_token):
                    continue
                reply_scores.append(_evaluate_position(sim_reply, perspective))

            score = min(reply_scores) if reply_scores else _evaluate_position(sim, perspective)

        if best_score is None or score > best_score:
            best_score = score
            best_tokens = [token]
        elif score == best_score:
            best_tokens.append(token)

    if not best_tokens:
        return _fallback_hard(game)

    return random.choice(best_tokens), "fallback"


def _stockfish_choose_move(game, skill_level=10, think_time_ms=250):
    try:
        import chess
        import chess.engine
    except Exception:
        return None

    path = os.getenv("STOCKFISH_PATH", "stockfish")

    try:
        board = chess.Board(game.to_fen())
        with chess.engine.SimpleEngine.popen_uci(path) as engine:
            try:
                engine.configure({"Skill Level": max(0, min(20, int(skill_level)))})
            except Exception:
                pass

            think_seconds = max(0.05, float(think_time_ms) / 1000.0)
            result = engine.play(board, chess.engine.Limit(time=think_seconds))
            if result and result.move:
                return result.move.uci(), "stockfish"
    except Exception:
        return None

    return None


def _level_settings(level):
    normalized = (level or "hard").strip().lower().replace("-", "_")
    if normalized not in {"easy", "hard", "very_hard"}:
        normalized = "hard"

    if normalized == "easy":
        return normalized, 4, 80
    if normalized == "very_hard":
        return normalized, 20, 900
    return normalized, 12, 300


def _fallback_choose_move(game, level):
    if level == "easy":
        return _fallback_easy(game)
    if level == "very_hard":
        return _fallback_very_hard(game)
    return _fallback_hard(game)


def choose_engine_move(game, skill_level=10, think_time_ms=250, use_stockfish=True, level="hard"):
    level, level_skill, level_time = _level_settings(level)
    if skill_level is None:
        skill_level = level_skill
    if think_time_ms is None:
        think_time_ms = level_time

    if use_stockfish:
        stockfish_result = _stockfish_choose_move(
            game,
            skill_level=skill_level,
            think_time_ms=think_time_ms,
        )
        if stockfish_result is not None:
            move_token, source = stockfish_result
            move, _ = game.parse_uci_move(move_token)
            if move is not None:
                return move_token, source

    return _fallback_choose_move(game, level)
