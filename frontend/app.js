const boardEl = document.getElementById("board");
const turnValueEl = document.getElementById("turnValue");
const stateValueEl = document.getElementById("stateValue");
const fullmoveValueEl = document.getElementById("fullmoveValue");
const halfmoveValueEl = document.getElementById("halfmoveValue");
const statusBadgeEl = document.getElementById("statusBadge");
const messageEl = document.getElementById("message");
const selectionEl = document.getElementById("selection");
const moveHistoryEl = document.getElementById("moveHistory");
const moveFormEl = document.getElementById("moveForm");
const moveInputEl = document.getElementById("moveInput");
const promotionInputEl = document.getElementById("promotionInput");
const newGameBtn = document.getElementById("newGameBtn");
const resetBtn = document.getElementById("resetBtn");
const undoBtn = document.getElementById("undoBtn");
const flipBtn = document.getElementById("flipBtn");
const engineMoveBtn = document.getElementById("engineMoveBtn");
const engineLevelSelect = document.getElementById("engineLevelSelect");
const vsEngineToggle = document.getElementById("vsEngineToggle");

const files = "abcdefgh";
const pieceMap = {
  wK: "\u265A",
  wQ: "\u265B",
  wR: "\u265C",
  wB: "\u265D",
  wN: "\u265E",
  wP: "\u265F",
  bK: "\u265A",
  bQ: "\u265B",
  bR: "\u265C",
  bB: "\u265D",
  bN: "\u265E",
  bP: "\u265F",
};

let gameId = null;
let gameState = null;
let selectedSquare = null;
let legalTargets = new Set();
let lastMove = null;
let orientation = "white";
let moveHistory = [];
let selectionRequestId = 0;
let engineBusy = false;

function squareName(row, col) {
  return `${files[col]}${8 - row}`;
}

function parseSquare(name) {
  if (!name || name.length !== 2) {
    return null;
  }

  const file = files.indexOf(name[0].toLowerCase());
  const rank = Number(name[1]);
  if (file < 0 || rank < 1 || rank > 8) {
    return null;
  }

  return { row: 8 - rank, col: file };
}

function pieceColor(piece) {
  return piece.startsWith("w") ? "white" : "black";
}

function isOwnPiece(piece) {
  return piece !== "." && gameState && piece[0] === gameState.turn;
}

function clearSelection() {
  selectedSquare = null;
  legalTargets = new Set();
  selectionEl.textContent = "Selected: none";
}

function setMessage(text, isError = false) {
  messageEl.textContent = text;
  messageEl.classList.toggle("error", isError);
}

function stateLabel(state) {
  if (!state) {
    return "-";
  }
  if (state.ended) {
    return state.result || "finished";
  }
  if (state.check) {
    return "check";
  }
  return "active";
}

function badgeLabel(state) {
  if (!state) {
    return "Active";
  }
  if (state.ended) {
    return "Game Over";
  }
  if (state.check) {
    return "Check";
  }
  return "Active";
}

function applyBadgeStyle(state) {
  statusBadgeEl.classList.remove("check", "ended");
  if (!state) {
    return;
  }

  if (state.ended) {
    statusBadgeEl.classList.add("ended");
    return;
  }
  if (state.check) {
    statusBadgeEl.classList.add("check");
  }
}

function renderMeta() {
  if (!gameState) {
    return;
  }

  turnValueEl.textContent = gameState.turn ? gameState.turn.toUpperCase() : "-";
  stateValueEl.textContent = stateLabel(gameState);
  fullmoveValueEl.textContent = gameState.fullmove_number;
  halfmoveValueEl.textContent = gameState.halfmove_clock;
  statusBadgeEl.textContent = badgeLabel(gameState);
  applyBadgeStyle(gameState);
}

function renderMoveHistory() {
  moveHistoryEl.innerHTML = "";

  if (!moveHistory.length) {
    const empty = document.createElement("li");
    empty.className = "empty-history";
    empty.textContent = "No moves yet.";
    moveHistoryEl.appendChild(empty);
    return;
  }

  for (let index = 0; index < moveHistory.length; index += 2) {
    const row = document.createElement("li");

    const ply = document.createElement("span");
    ply.className = "ply-index";
    ply.textContent = `${Math.floor(index / 2) + 1}.`;

    const whiteMove = document.createElement("span");
    whiteMove.textContent = moveHistory[index] || "";

    const blackMove = document.createElement("span");
    blackMove.textContent = moveHistory[index + 1] || "";

    row.appendChild(ply);
    row.appendChild(whiteMove);
    row.appendChild(blackMove);
    moveHistoryEl.appendChild(row);
  }
}

function isLastMoveSquare(name) {
  if (!lastMove) {
    return false;
  }
  return lastMove.start === name || lastMove.end === name;
}

function isCheckSquare(piece) {
  if (!gameState || !gameState.check || gameState.ended || piece === ".") {
    return false;
  }
  return piece === `${gameState.turn}K`;
}

function visualToActual(visualRow, visualCol) {
  if (orientation === "white") {
    return { row: visualRow, col: visualCol };
  }
  return { row: 7 - visualRow, col: 7 - visualCol };
}

async function fetchLegalTargets(startSquare) {
  if (!gameId || !gameState) {
    return [];
  }

  try {
    const response = await api(
      `/api/games/${gameId}/legal-moves?from=${encodeURIComponent(startSquare)}`
    );
    return response.targets || [];
  } catch {
    return [];
  }
}

function renderBoard() {
  if (!gameState) {
    return;
  }

  boardEl.innerHTML = "";

  for (let visualRow = 0; visualRow < 8; visualRow += 1) {
    for (let visualCol = 0; visualCol < 8; visualCol += 1) {
      const square = document.createElement("button");
      square.type = "button";
      square.className = "square";

      const actual = visualToActual(visualRow, visualCol);
      const name = squareName(actual.row, actual.col);
      const piece = gameState.board[actual.row][actual.col];
      const light = (actual.row + actual.col) % 2 === 0;

      square.classList.add(light ? "light" : "dark");
      if (selectedSquare === name) {
        square.classList.add("selected");
      }
      if (legalTargets.has(name)) {
        square.classList.add("legal-target");
        if (piece !== ".") {
          square.classList.add("has-piece");
        }
      }
      if (isLastMoveSquare(name)) {
        square.classList.add("last-move");
      }
      if (isCheckSquare(piece)) {
        square.classList.add("in-check");
      }

      if (visualRow === 7) {
        square.classList.add("show-file");
        square.dataset.file = files[actual.col];
      }
      if (visualCol === 0) {
        square.classList.add("show-rank");
        square.dataset.rank = String(8 - actual.row);
      }

      square.dataset.square = name;
      square.addEventListener("click", () => handleSquareClick(name, piece));

      if (piece !== ".") {
        const span = document.createElement("span");
        span.className = `piece ${pieceColor(piece)}`;
        span.textContent = pieceMap[piece] || piece;
        square.appendChild(span);
      }

      boardEl.appendChild(square);
    }
  }
}

async function setSelection(squareNameValue) {
  if (!squareNameValue) {
    clearSelection();
    renderBoard();
    return;
  }

  const parsed = parseSquare(squareNameValue);
  if (!parsed) {
    clearSelection();
    renderBoard();
    return;
  }

  const piece = gameState.board[parsed.row][parsed.col];
  if (!isOwnPiece(piece)) {
    clearSelection();
    renderBoard();
    return;
  }

  selectedSquare = squareNameValue;
  legalTargets = new Set();
  selectionEl.textContent = `Selected: ${squareNameValue} (loading...)`;
  renderBoard();

  const requestId = ++selectionRequestId;
  const targets = await fetchLegalTargets(squareNameValue);
  if (requestId !== selectionRequestId || selectedSquare !== squareNameValue) {
    return;
  }

  legalTargets = new Set(targets);
  selectionEl.textContent = `Selected: ${squareNameValue} (${legalTargets.size} legal)`;
  renderBoard();
}

function updateControls() {
  const endedOrMissing = !gameState || gameState.ended;
  moveInputEl.disabled = endedOrMissing || engineBusy;
  promotionInputEl.disabled = endedOrMissing || engineBusy;
  moveFormEl.querySelector("button[type='submit']").disabled = endedOrMissing || engineBusy;
  engineMoveBtn.disabled = endedOrMissing || engineBusy;
  engineLevelSelect.disabled = engineBusy;
  undoBtn.disabled = engineBusy || !gameState || moveHistory.length === 0;
  newGameBtn.disabled = engineBusy;
  resetBtn.disabled = engineBusy;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const data = await response.json();
  if (!response.ok) {
    const err = new Error(data.error || "Request failed.");
    err.payload = data;
    throw err;
  }
  return data;
}

function applyLastMoveFromToken(token) {
  if (!token || token.length < 4) {
    return;
  }

  const from = token.slice(0, 2).toLowerCase();
  const to = token.slice(2, 4).toLowerCase();
  if (parseSquare(from) && parseSquare(to)) {
    lastMove = { start: from, end: to };
  }
}

function pushMoveHistory(token) {
  if (!token) {
    return;
  }
  moveHistory.push(token.toLowerCase());
  renderMoveHistory();
}

function removeLastMoves(count) {
  const total = Math.max(0, Number(count) || 0);
  for (let i = 0; i < total && moveHistory.length; i += 1) {
    moveHistory.pop();
  }
  renderMoveHistory();
}

function refreshLastMoveFromHistory() {
  if (!moveHistory.length) {
    lastMove = null;
    return;
  }
  applyLastMoveFromToken(moveHistory[moveHistory.length - 1]);
}

async function createGame() {
  const state = await api("/api/games", { method: "POST" });
  gameId = state.game_id;
  gameState = state;
  moveHistory = [];
  renderMoveHistory();
  lastMove = null;
  clearSelection();
  renderMeta();
  renderBoard();
  updateControls();
  setMessage(state.message);
}

async function resetGame() {
  if (!gameId) {
    await createGame();
    return;
  }

  const state = await api(`/api/games/${gameId}/reset`, { method: "POST" });
  gameState = state;
  moveHistory = [];
  renderMoveHistory();
  lastMove = null;
  clearSelection();
  renderMeta();
  renderBoard();
  updateControls();
  setMessage(state.message);
}

function formatMoveToken(start, end, promotion) {
  const promo = promotion ? `=${promotion}` : "";
  return `${start}${end}${promo}`;
}

async function playMove(payload, moveToken) {
  if (!gameId) {
    await createGame();
  }

  try {
    engineBusy = true;
    updateControls();
    const state = await api(`/api/games/${gameId}/moves`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    gameState = state;
    const played = state.played_move || moveToken;
    applyLastMoveFromToken(played);
    pushMoveHistory(played);
    clearSelection();
    renderMeta();
    renderBoard();
    updateControls();
    setMessage(state.message);
    return true;
  } catch (error) {
    setMessage(error.message, true);
    if (error.payload && error.payload.promotion_required) {
      promotionInputEl.focus();
    }
    return false;
  } finally {
    engineBusy = false;
    updateControls();
  }
}

async function requestEngineMove() {
  if (!gameState || gameState.ended || !gameId) {
    return false;
  }

  try {
    engineBusy = true;
    updateControls();
    setMessage("Engine thinking...");

    const state = await api(`/api/games/${gameId}/engine-move`, {
      method: "POST",
      body: JSON.stringify({
        level: engineLevelSelect.value || "hard",
        use_stockfish: true,
      }),
    });

    gameState = state;
    const played = state.played_move || "";
    applyLastMoveFromToken(played);
    pushMoveHistory(played);
    clearSelection();
    renderMeta();
    renderBoard();
    setMessage(state.message);
    return true;
  } catch (error) {
    setMessage(error.message || "Engine move failed.", true);
    return false;
  } finally {
    engineBusy = false;
    updateControls();
  }
}

async function requestUndo(steps = 1) {
  if (!gameState || !gameId || engineBusy) {
    return false;
  }

  try {
    engineBusy = true;
    updateControls();

    const state = await api(`/api/games/${gameId}/undo`, {
      method: "POST",
      body: JSON.stringify({ steps }),
    });

    gameState = state;
    removeLastMoves(state.undone_steps || steps);
    refreshLastMoveFromHistory();
    clearSelection();
    renderMeta();
    renderBoard();
    setMessage(state.message);
    return true;
  } catch (error) {
    setMessage(error.message || "Undo failed.", true);
    return false;
  } finally {
    engineBusy = false;
    updateControls();
  }
}

async function maybeAutoEngineMove() {
  if (!vsEngineToggle.checked) {
    return;
  }
  if (!gameState || gameState.ended) {
    return;
  }
  if (gameState.turn !== "b") {
    return;
  }
  await requestEngineMove();
}

async function handleSquareClick(square, piece) {
  if (!gameState || gameState.ended) {
    return;
  }

  if (!selectedSquare) {
    if (isOwnPiece(piece)) {
      await setSelection(square);
    }
    return;
  }

  if (selectedSquare === square) {
    await setSelection(null);
    return;
  }

  if (isOwnPiece(piece)) {
    await setSelection(square);
    return;
  }

  if (!legalTargets.has(square)) {
    return;
  }

  const start = selectedSquare;
  const end = square;
  const promotion = promotionInputEl.value || undefined;
  const moveToken = formatMoveToken(start, end, promotion);

  const success = await playMove({ start, end, promotion }, moveToken);
  if (success) {
    await maybeAutoEngineMove();
  }
}

moveFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!gameState || gameState.ended) {
    return;
  }

  const move = moveInputEl.value.trim();
  if (!move) {
    setMessage("Enter a move first.", true);
    return;
  }

  const promotion = promotionInputEl.value || undefined;
  const compact = move.replace(/\s+/g, "").toLowerCase();

  const success = await playMove({ move, promotion }, compact);
  if (success) {
    await maybeAutoEngineMove();
    moveInputEl.focus();
    moveInputEl.select();
  }
});

newGameBtn.addEventListener("click", async () => {
  await createGame();
});

resetBtn.addEventListener("click", async () => {
  await resetGame();
});

undoBtn.addEventListener("click", async () => {
  await requestUndo(1);
});

engineMoveBtn.addEventListener("click", async () => {
  await requestEngineMove();
});

vsEngineToggle.addEventListener("change", async () => {
  if (vsEngineToggle.checked) {
    await maybeAutoEngineMove();
  }
});

flipBtn.addEventListener("click", () => {
  orientation = orientation === "white" ? "black" : "white";
  renderBoard();
});

renderMoveHistory();
createGame().catch((error) => {
  setMessage(error.message || "Unable to start game.", true);
});
