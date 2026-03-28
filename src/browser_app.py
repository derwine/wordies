from __future__ import annotations

import json
import threading
import webbrowser
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from secrets import token_urlsafe
from typing import Any
from urllib.parse import urlparse

from src.game_engine import GameSession

HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Wordies</title>
    <style>
      :root {
        --bg: linear-gradient(160deg, #0f172a 0%, #111827 45%, #1e293b 100%);
        --panel: rgba(15, 23, 42, 0.82);
        --panel-border: rgba(125, 211, 252, 0.3);
        --text: #e5eef8;
        --muted: #9fb3c8;
        --accent: #67e8f9;
        --correct: #22c55e;
        --present: #f59e0b;
        --absent: #64748b;
        --empty: #1f2937;
        --button: #0ea5e9;
        --button-hover: #0284c7;
        --round-end: #f97316;
        --round-end-hover: #ea580c;
        --shadow: 0 24px 80px rgba(15, 23, 42, 0.45);
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        min-height: 100vh;
        font-family: "Avenir Next", "Segoe UI", sans-serif;
        background: var(--bg);
        color: var(--text);
      }
      .shell {
        max-width: 1120px;
        margin: 0 auto;
        padding: 32px 20px 48px;
      }
      .hero {
        display: grid;
        gap: 18px;
        margin-bottom: 24px;
      }
      .eyebrow {
        color: var(--accent);
        letter-spacing: 0.14em;
        font-size: 0.75rem;
        text-transform: uppercase;
      }
      h1 {
        margin: 0;
        font-size: clamp(2.8rem, 6vw, 5.2rem);
        line-height: 0.92;
      }
      .lead {
        margin: 0;
        max-width: 760px;
        color: var(--muted);
        font-size: 1.05rem;
      }
      .layout {
        display: grid;
        grid-template-columns: 1.55fr 1fr;
        gap: 22px;
        align-items: start;
      }
      .panel {
        background: var(--panel);
        border: 1px solid var(--panel-border);
        border-radius: 24px;
        box-shadow: var(--shadow);
        backdrop-filter: blur(18px);
      }
      .board-panel {
        padding: 24px;
      }
      .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        margin-bottom: 18px;
      }
      .panel-title {
        margin: 0;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--muted);
      }
      .pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(103, 232, 249, 0.08);
        color: var(--accent);
        font-size: 0.85rem;
      }
      .board {
        display: grid;
        gap: 12px;
      }
      .board-row {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 12px;
      }
      .tile {
        aspect-ratio: 1 / 1;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: clamp(1.4rem, 3vw, 2rem);
        font-weight: 800;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        background: var(--empty);
        transition: transform 160ms ease, background 160ms ease, border-color 160ms ease;
      }
      .tile[data-state="correct"] { background: var(--correct); }
      .tile[data-state="present"] { background: var(--present); }
      .tile[data-state="absent"] { background: var(--absent); }
      .tile:hover { transform: translateY(-2px); }
      .side-stack {
        display: grid;
        gap: 18px;
      }
      .side-panel {
        padding: 22px;
      }
      .status {
        margin: 0 0 10px;
        font-size: 1.15rem;
      }
      .muted {
        color: var(--muted);
      }
      .controls {
        display: grid;
        gap: 14px;
        margin-top: 18px;
      }
      .controls[data-win="true"] .guess-form {
        display: none;
      }
      .guess-form {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 10px;
      }
      input[type="text"] {
        width: 100%;
        background: rgba(15, 23, 42, 0.84);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        color: var(--text);
        font-size: 1rem;
        padding: 16px 18px;
        outline: none;
        text-transform: lowercase;
      }
      input[type="text"]:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 4px rgba(103, 232, 249, 0.12);
      }
      button {
        border: 0;
        border-radius: 16px;
        padding: 14px 18px;
        font-size: 0.98rem;
        font-weight: 700;
        color: white;
        background: var(--button);
        cursor: pointer;
        transition: transform 140ms ease, background 140ms ease;
      }
      button:hover { background: var(--button-hover); transform: translateY(-1px); }
      button.secondary {
        background: rgba(148, 163, 184, 0.18);
        color: var(--text);
      }
      button.round-end {
        background: var(--round-end);
        color: white;
        box-shadow: 0 0 0 4px rgba(249, 115, 22, 0.18);
      }
      button.round-end:hover {
        background: var(--round-end-hover);
      }
      .keyboard {
        display: grid;
        gap: 10px;
        margin-top: 8px;
      }
      .keyboard-row {
        display: flex;
        justify-content: center;
        gap: 8px;
        flex-wrap: nowrap;
      }
      .key {
        min-width: 40px;
        padding: 12px 0;
        border-radius: 12px;
        text-align: center;
        font-weight: 700;
        background: var(--empty);
      }
      .key[data-state="correct"] { background: var(--correct); }
      .key[data-state="present"] { background: var(--present); }
      .key[data-state="absent"] { background: var(--absent); }
      .toolbar {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 10px;
      }
      .note {
        margin-top: 12px;
        color: var(--muted);
        font-size: 0.93rem;
      }
      .modal {
        position: fixed;
        inset: 0;
        display: none;
        align-items: center;
        justify-content: center;
        padding: 20px;
        background: rgba(15, 23, 42, 0.72);
        backdrop-filter: blur(14px);
        z-index: 20;
      }
      .modal[data-open="true"] {
        display: flex;
      }
      .modal-card {
        width: min(720px, 100%);
        border-radius: 28px;
        border: 1px solid rgba(125, 211, 252, 0.2);
        background: rgba(15, 23, 42, 0.96);
        box-shadow: var(--shadow);
        padding: 24px;
      }
      .modal-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 20px;
      }
      .stats-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin: 18px 0;
      }
      .stats-card {
        border-radius: 18px;
        background: rgba(30, 41, 59, 0.72);
        padding: 16px;
      }
      .stats-label {
        color: var(--muted);
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
      }
      .stats-value {
        margin-top: 8px;
        font-size: 1.8rem;
        font-weight: 800;
      }
      .history-chart {
        display: grid;
        gap: 12px;
        margin-top: 18px;
      }
      .history-row {
        display: grid;
        grid-template-columns: 88px 1fr 72px;
        gap: 12px;
        align-items: center;
      }
      .history-label {
        color: var(--muted);
        font-size: 0.9rem;
      }
      .history-bar-wrap {
        height: 14px;
        border-radius: 999px;
        overflow: hidden;
        background: rgba(148, 163, 184, 0.16);
      }
      .history-bar {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #22c55e, #67e8f9);
      }
      .history-bar.loss {
        background: linear-gradient(90deg, #f97316, #f59e0b);
      }
      .history-value {
        text-align: right;
        font-size: 0.92rem;
      }
      .confetti-layer {
        pointer-events: none;
        position: fixed;
        inset: 0;
        overflow: hidden;
        z-index: 15;
      }
      .confetti {
        position: absolute;
        top: -12vh;
        width: 12px;
        height: 22px;
        border-radius: 999px;
        opacity: 0.92;
        animation: confetti-fall 1600ms ease-in forwards;
      }
      .win-banner {
        display: none;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
        padding: 14px 16px;
        border-radius: 18px;
        background: rgba(34, 197, 94, 0.14);
        border: 1px solid rgba(34, 197, 94, 0.28);
      }
      .win-banner[data-show="true"] {
        display: flex;
      }
      .win-title {
        font-size: 1rem;
        font-weight: 800;
      }
      .win-copy {
        color: var(--muted);
        font-size: 0.92rem;
      }
      @keyframes confetti-fall {
        0% { transform: translateY(0) rotate(0deg); opacity: 0; }
        10% { opacity: 1; }
        100% { transform: translateY(115vh) rotate(560deg); opacity: 0; }
      }
      @media (max-width: 900px) {
        .layout { grid-template-columns: 1fr; }
        .shell { padding: 22px 14px 40px; }
        .guess-form { grid-template-columns: 1fr; }
        .stats-grid { grid-template-columns: 1fr; }
        .history-row { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <div class="confetti-layer" id="confetti-layer"></div>
    <main class="shell">
      <section class="hero">
        <div class="eyebrow">Wordies Browser Mode</div>
        <h1>Guess fast. Keep it clean.</h1>
        <p class="lead">
          A local browser version of Wordies with the same rules as the terminal game,
          tuned for a sharper, more app-like feel.
        </p>
      </section>
      <section class="layout">
        <div class="panel board-panel">
          <div class="panel-header">
            <h2 class="panel-title">Board</h2>
            <div class="pill" id="guesses-left">6 guesses left</div>
          </div>
          <div class="board" id="board"></div>
        </div>
        <div class="side-stack">
          <div class="panel side-panel">
            <div class="panel-header">
              <h2 class="panel-title">Play</h2>
            </div>
            <p class="status" id="status">Guess a five-letter word.</p>
            <p class="muted" id="answer-state">Local mode is running on your machine.</p>
            <div class="controls" id="controls">
              <div class="win-banner" id="win-banner" data-show="false">
                <div>
                  <div class="win-title">Round solved</div>
                  <div class="win-copy">Take the win lap, then jump into the next round.</div>
                </div>
                <button class="secondary" id="banner-stats-button" type="button">View Stats</button>
              </div>
              <form class="guess-form" id="guess-form">
                <input id="guess-input" type="text" minlength="5" maxlength="5" autocomplete="off" placeholder="type a guess" />
                <button type="submit">Submit</button>
              </form>
              <div class="toolbar">
                <button class="secondary" id="clue-button" type="button">Show Clue</button>
                <button class="secondary" id="stats-button" type="button">Recent Stats</button>
                <button class="secondary" id="new-round-button" type="button">New Round</button>
              </div>
              <p class="note" id="clue-text"></p>
            </div>
          </div>
          <div class="panel side-panel">
            <div class="panel-header">
              <h2 class="panel-title">Keyboard</h2>
            </div>
            <div class="keyboard" id="keyboard"></div>
          </div>
        </div>
      </section>
    </main>
    <div class="modal" id="stats-modal" data-open="false" aria-hidden="true">
      <div class="modal-card">
        <div class="panel-header">
          <h2 class="panel-title">Recent Performance</h2>
          <button class="secondary" id="close-stats-button" type="button">Close</button>
        </div>
        <p class="muted">Stored locally in your browser so your recent runs stay with you.</p>
        <div class="stats-grid">
          <div class="stats-card">
            <div class="stats-label">Rounds</div>
            <div class="stats-value" id="stats-rounds">0</div>
          </div>
          <div class="stats-card">
            <div class="stats-label">Wins</div>
            <div class="stats-value" id="stats-wins">0</div>
          </div>
          <div class="stats-card">
            <div class="stats-label">Win Rate</div>
            <div class="stats-value" id="stats-win-rate">0%</div>
          </div>
        </div>
        <div class="history-chart" id="history-chart"></div>
        <div class="modal-actions">
          <button id="modal-new-round-button" type="button">New Round</button>
          <button class="secondary" id="modal-close-button" type="button">Hide</button>
        </div>
      </div>
    </div>
    <script>
      const STORAGE_KEYS = {
        session: "wordies_session",
        history: "wordies_results",
      };
      const state = {
        clueVisible: false,
        sessionId: window.localStorage.getItem(STORAGE_KEYS.session),
        latestPayload: null,
        lastResolvedSignature: null,
        statsModalOpen: false,
      };

      async function api(path, options = {}) {
        const headers = {
          "Content-Type": "application/json",
          ...(options.headers || {}),
        };
        if (state.sessionId) {
          headers["X-Wordies-Session"] = state.sessionId;
        }
        const response = await fetch(path, {
          ...options,
          headers,
        });
        if (!response.ok) {
          throw new Error("Request failed");
        }
        const payload = await response.json();
        if (payload.session_id) {
          state.sessionId = payload.session_id;
          window.localStorage.setItem(STORAGE_KEYS.session, payload.session_id);
        }
        return payload;
      }

      function loadHistory() {
        try {
          return JSON.parse(window.localStorage.getItem(STORAGE_KEYS.history) || "[]");
        } catch (error) {
          return [];
        }
      }

      function saveHistory(entries) {
        window.localStorage.setItem(STORAGE_KEYS.history, JSON.stringify(entries.slice(-12)));
      }

      function resultSignature(payload) {
        const finalRow = payload.board.find((row) => row.some((tile) => tile.letter));
        const letters = finalRow ? finalRow.map((tile) => tile.letter).join("") : "";
        return `${payload.session_id}:${payload.finished}:${payload.won}:${payload.guesses_left}:${letters}`;
      }

      function recordCompletedRound(payload) {
        if (!payload.finished) {
          return;
        }
        const signature = resultSignature(payload);
        if (signature === state.lastResolvedSignature) {
          return;
        }
        state.lastResolvedSignature = signature;
        const entries = loadHistory();
        entries.push({
          won: payload.won,
          guesses: payload.won ? 6 - payload.guesses_left : 6,
          label: payload.won ? `Win in ${6 - payload.guesses_left}` : "Loss",
          timestamp: Date.now(),
        });
        saveHistory(entries);
      }

      function historyRowMarkup(entry, index, maxGuesses = 6) {
        const width = `${Math.max(18, Math.round((entry.guesses / maxGuesses) * 100))}%`;
        const barClass = entry.won ? "history-bar" : "history-bar loss";
        const label = entry.won ? `Round ${index + 1}` : `Round ${index + 1}`;
        const value = entry.won ? `${entry.guesses} guesses` : "Loss";
        return `
          <div class="history-row">
            <div class="history-label">${label}</div>
            <div class="history-bar-wrap">
              <div class="${barClass}" style="width: ${width};"></div>
            </div>
            <div class="history-value">${value}</div>
          </div>
        `;
      }

      function renderStatsModal() {
        const entries = loadHistory();
        const wins = entries.filter((entry) => entry.won).length;
        const rounds = entries.length;
        const winRate = rounds ? `${Math.round((wins / rounds) * 100)}%` : "0%";
        document.getElementById("stats-rounds").textContent = rounds;
        document.getElementById("stats-wins").textContent = wins;
        document.getElementById("stats-win-rate").textContent = winRate;
        document.getElementById("history-chart").innerHTML = rounds
          ? entries.map((entry, index) => historyRowMarkup(entry, index)).reverse().join("")
          : `<p class="muted">No completed rounds yet. Finish one and the chart will light up.</p>`;
      }

      function setStatsModalOpen(open) {
        state.statsModalOpen = open;
        const modal = document.getElementById("stats-modal");
        modal.dataset.open = open ? "true" : "false";
        modal.setAttribute("aria-hidden", open ? "false" : "true");
        if (open) {
          renderStatsModal();
        }
      }

      function triggerCelebration() {
        const layer = document.getElementById("confetti-layer");
        layer.innerHTML = "";
        const colors = ["#67e8f9", "#22c55e", "#f59e0b", "#f97316", "#f8fafc"];
        for (let index = 0; index < 22; index += 1) {
          const piece = document.createElement("div");
          piece.className = "confetti";
          piece.style.left = `${4 + index * 4.2}%`;
          piece.style.background = colors[index % colors.length];
          piece.style.animationDelay = `${(index % 6) * 45}ms`;
          piece.style.transform = `translateY(0) rotate(${index * 16}deg)`;
          layer.appendChild(piece);
        }
        window.setTimeout(() => {
          layer.innerHTML = "";
        }, 1900);
      }

      function tileMarkup(tile) {
        const letter = tile.letter ? tile.letter.toUpperCase() : "";
        return `<div class="tile" data-state="${tile.state}">${letter}</div>`;
      }

      function renderBoard(board) {
        const root = document.getElementById("board");
        root.innerHTML = board
          .map((row) => `<div class="board-row">${row.map(tileMarkup).join("")}</div>`)
          .join("");
      }

      function renderKeyboard(rows) {
        const root = document.getElementById("keyboard");
        root.innerHTML = rows
          .map(
            (row) =>
              `<div class="keyboard-row">${row
                .map(
                  (key) =>
                    `<div class="key" data-state="${key.state}">${key.letter}</div>`
                )
                .join("")}</div>`
          )
          .join("");
      }

      function renderClue() {
        if (!state.latestPayload) {
          return;
        }
        document.getElementById("clue-text").textContent = state.clueVisible
          ? `Clue: ${state.latestPayload.clue}`
          : "";
        document.getElementById("clue-button").textContent = state.clueVisible
          ? "Hide Clue"
          : "Show Clue";
      }

      function showBrowserError(message) {
        document.getElementById("status").textContent = message;
        document.getElementById("answer-state").textContent =
          "Refresh the page or start a new round if the issue persists.";
      }

      function renderState(payload) {
        const previouslyWon = state.latestPayload ? state.latestPayload.won : false;
        state.latestPayload = payload;
        recordCompletedRound(payload);
        renderBoard(payload.board);
        renderKeyboard(payload.keyboard);
        document.getElementById("status").textContent = payload.status;
        document.getElementById("guesses-left").textContent = `${payload.guesses_left} guesses left`;
        document.getElementById("answer-state").textContent = payload.finished
          ? "Round complete. Start a fresh one when you're ready."
          : "Local mode is running on your machine.";
        document.getElementById("controls").dataset.win = payload.won ? "true" : "false";
        document.getElementById("guess-input").disabled = payload.finished;
        document.querySelector('#guess-form button[type="submit"]').disabled = payload.finished;
        document.getElementById("new-round-button").classList.toggle("round-end", payload.won);
        document.getElementById("win-banner").dataset.show = payload.won ? "true" : "false";
        if (payload.won && !previouslyWon) {
          triggerCelebration();
        }
        renderClue();
        renderStatsModal();
      }

      async function refresh() {
        try {
          const payload = await api("/api/state");
          renderState(payload);
        } catch (error) {
          showBrowserError("Could not refresh the game state.");
        }
      }

      document.getElementById("guess-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const input = document.getElementById("guess-input");
        const guess = input.value.trim().toLowerCase();
        try {
          const payload = await api("/api/guess", {
            method: "POST",
            body: JSON.stringify({ guess }),
          });
          renderState(payload);
          input.value = "";
          input.focus();
        } catch (error) {
          showBrowserError("Could not submit your guess.");
        }
      });

      document.getElementById("new-round-button").addEventListener("click", async () => {
        state.clueVisible = false;
        state.lastResolvedSignature = null;
        try {
          const payload = await api("/api/reset", {
            method: "POST",
            body: JSON.stringify({}),
          });
          renderState(payload);
          document.getElementById("guess-input").focus();
        } catch (error) {
          showBrowserError("Could not start a new round.");
        }
      });

      document.getElementById("clue-button").addEventListener("click", () => {
        state.clueVisible = !state.clueVisible;
        renderClue();
      });

      document.getElementById("stats-button").addEventListener("click", () => {
        setStatsModalOpen(true);
      });

      document.getElementById("banner-stats-button").addEventListener("click", () => {
        setStatsModalOpen(true);
      });

      document.getElementById("close-stats-button").addEventListener("click", () => {
        setStatsModalOpen(false);
      });

      document.getElementById("modal-close-button").addEventListener("click", () => {
        setStatsModalOpen(false);
      });

      document.getElementById("modal-new-round-button").addEventListener("click", async () => {
        setStatsModalOpen(false);
        document.getElementById("new-round-button").click();
      });

      document.getElementById("stats-modal").addEventListener("click", (event) => {
        if (event.target.id === "stats-modal") {
          setStatsModalOpen(false);
        }
      });

      window.addEventListener("error", () => {
        showBrowserError("Something went wrong in the browser UI.");
      });

      window.addEventListener("unhandledrejection", () => {
        showBrowserError("Something went wrong in the browser UI.");
      });

      window.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && state.statsModalOpen) {
          setStatsModalOpen(false);
        }
      });

      refresh().then(() => document.getElementById("guess-input").focus());
    </script>
  </body>
</html>
"""


class BrowserApp:
    def __init__(self, answers: list[str] | tuple[str, ...], host: str = "127.0.0.1", port: int = 8765) -> None:
        self.answers = tuple(answers)
        self.host = host
        self.port = port
        self.sessions: dict[str, GameSession] = {}

    def get_session(self, session_id: str | None) -> tuple[str, GameSession]:
        if session_id and session_id in self.sessions:
            return session_id, self.sessions[session_id]

        new_session_id = token_urlsafe(16)
        session = GameSession(self.answers)
        self.sessions[new_session_id] = session
        return new_session_id, session

    def serialize(
        self,
        session: GameSession,
        session_id: str,
        message: str | None = None,
    ) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "status": message or session.status(),
            "board": session.board_rows(),
            "keyboard": session.keyboard_rows(),
            "guesses_left": session.max_guesses - session.guesses_used,
            "finished": session.finished,
            "won": session.guess_correct,
            "clue": session.clue(),
        }

    def serve(self, open_browser: bool = True) -> None:
        server = self.create_server()
        url = f"http://{self.host}:{self.port}"
        if open_browser:
            threading.Timer(0.35, lambda: webbrowser.open(url)).start()
        print(f"Wordies browser mode running at {url}")
        print("Press Ctrl+C to stop the local server.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down browser mode.")
        finally:
            server.server_close()

    def create_server(
        self,
        handler_class: type[BaseHTTPRequestHandler] | None = None,
    ) -> ThreadingHTTPServer:
        if handler_class is None:
            app = self

            class Handler(BaseHTTPRequestHandler):
                def get_session_id(self) -> str | None:
                    header_session_id = self.headers.get("X-Wordies-Session")
                    if header_session_id:
                        return header_session_id
                    raw_cookie = self.headers.get("Cookie")
                    if not raw_cookie:
                        return None
                    cookie = SimpleCookie()
                    cookie.load(raw_cookie)
                    if "wordies_session" not in cookie:
                        return None
                    return cookie["wordies_session"].value

                def send_json(self, payload: dict[str, Any], session_id: str | None = None) -> None:
                    body = json.dumps(payload).encode("utf-8")
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    if session_id:
                        self.send_header("Set-Cookie", f"wordies_session={session_id}; Path=/; SameSite=Lax")
                    self.end_headers()
                    self.wfile.write(body)

                def send_html(self) -> None:
                    body = HTML.encode("utf-8")
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

                def read_json(self) -> dict[str, Any]:
                    content_length = int(self.headers.get("Content-Length", "0"))
                    if content_length == 0:
                        return {}
                    return json.loads(self.rfile.read(content_length).decode("utf-8"))

                def do_GET(self) -> None:  # noqa: N802
                    parsed = urlparse(self.path)
                    if parsed.path == "/":
                        self.send_html()
                        return
                    if parsed.path == "/api/state":
                        session_id, session = app.get_session(self.get_session_id())
                        self.send_json(app.serialize(session, session_id), session_id=session_id)
                        return
                    self.send_error(HTTPStatus.NOT_FOUND, "Not found")

                def do_POST(self) -> None:  # noqa: N802
                    parsed = urlparse(self.path)
                    session_id, session = app.get_session(self.get_session_id())
                    payload = self.read_json()

                    if parsed.path == "/api/guess":
                        guess = str(payload.get("guess", "")).strip().lower()
                        if not guess:
                            self.send_json(
                                app.serialize(session, session_id, "Enter a five-letter word."),
                                session_id=session_id,
                            )
                            return
                        error, accepted = session.submit_guess(guess)
                        if error or not accepted:
                            self.send_json(
                                app.serialize(session, session_id, error),
                                session_id=session_id,
                            )
                            return
                        self.send_json(app.serialize(session, session_id), session_id=session_id)
                        return

                    if parsed.path == "/api/reset":
                        session.reset_round()
                        self.send_json(app.serialize(session, session_id), session_id=session_id)
                        return

                    self.send_error(HTTPStatus.NOT_FOUND, "Not found")

                def log_message(self, format: str, *args: Any) -> None:
                    return

            handler_class = Handler

        server = ThreadingHTTPServer((self.host, self.port), handler_class)
        self.host, self.port = server.server_address[:2]
        return server
