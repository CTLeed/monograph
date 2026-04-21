# Monograph — weekly issue toolchain

Three free, local tools plus a human in the loop. No API keys, no
subscriptions, no cloud spend. Each Tuesday looks like:

```
  chat.py research  ──▶  notes/NNN-slug.md
         │
         ▼
  write_issue.py    ──▶  drafts/NNN-slug.json
         │
         ▼
  Claude Code       ──▶  issues/NNN-slug.html  +  patched index/archive
```

---

## What each tool does

### `chat.py` — the Level-1 chat helper

Bridges free web chats (Claude.ai, ChatGPT, Gemini). It interpolates a
prepared prompt, copies it to your Windows clipboard, and opens the
chosen provider in your default browser. You paste (Ctrl+V), submit,
wait, copy the response (Ctrl+A, Ctrl+C), and press Enter in the
terminal. It reads the clipboard back and saves the output to disk.

Two subcommands:

- `pick` — fills `backlog.txt` with 15 AI-suggested products to profile.
  Run this every few weeks when the backlog gets thin.
- `research` — gathers notes for a specific upcoming issue.
  Run this every Tuesday morning for the week's subject.

### `write_issue.py` — the local draft writer

Reads `notes/NNN-slug.md` and calls your local Ollama instance to write
the essay in the Monograph voice. Ollama returns structured JSON (title,
dek, body_html, metadata); the script validates it and saves
`drafts/NNN-slug.json`. No network beyond `localhost:11434`.

### Claude Code — the publisher

Once you're happy with the draft, start Claude Code in
`D:\ForFun\monograph` and say:

> publish draft 25 from drafts/025-superhuman.json

Claude reads the draft, renders `issues/025-superhuman.html` using
`issues/024-linear.html` as the template, prepends a card to
`archive.html`, swaps the featured section in `index.html`, and rebuilds
the recent-issues grid. Backup `.bak` files are written before any
mutation. You can review the diff and roll back in one move.

---

## One-time setup

1. **Python 3.11+.** `python --version`.
2. **Ollama** installed and serving:
   ```
   ollama serve
   ```
   Leave this running in a spare terminal. It starts automatically on
   Windows boot if you installed Ollama's service.
3. **A writing model pulled locally.** `gemma4:e4b` is the default;
   anything in your `ollama list` works with `--model <name>`.
4. **No pip installs needed.** `chat.py` and `write_issue.py` use only
   the Python standard library.
5. **Log into your chosen web chat(s) once.** The browser remembers the
   session, so subsequent `chat.py` runs drop you straight into the
   chat.

---

## Weekly workflow

### Monday evening: refill the backlog (only if needed)

```
python tools\chat.py pick --provider claude
```

- Script copies the picker prompt to your clipboard and opens
  `claude.ai/new`.
- Paste (Ctrl+V), Enter, wait ~30 seconds.
- Ctrl+A inside the response, Ctrl+C.
- Back in the terminal, press Enter.
- Script parses bolded product names from the reply and appends the
  new ones to `backlog.txt`. Duplicates (already covered, already
  queued) are skipped. The raw reply is saved to
  `notes/pick-YYYY-MM-DD.md` for reference.

You only need to run this when `backlog.txt` is running low — maybe
once a month.

### Tuesday 7 AM: research

Pick the next product (top line of `backlog.txt`, or your own choice):

```
python tools\chat.py research --product "Superhuman"
```

- Copies the research prompt (interpolated with the product name,
  target issue number, and next-Tuesday date) to the clipboard.
- Opens your chosen chat (`--provider claude|chatgpt|gemini`).
- Paste, Enter, wait for the full response, Ctrl+A Ctrl+C.
- Press Enter in the terminal.
- Saves `notes/025-superhuman.md`.

Claude is the suggested default because its research depth tends to be
strongest on free web tier. Try all three — use whichever works best
for you.

### Tuesday 8 AM: write the draft with Ollama

```
python tools\write_issue.py --product "Superhuman"
```

- Reads `notes/025-superhuman.md`.
- Hits `http://localhost:11434/api/chat` with the Monograph
  editorial-voice system prompt + your notes.
- Validates the returned JSON (body length, required sections,
  typographic punctuation).
- Saves `drafts/025-superhuman.json`.

Expect 2–10 minutes depending on model size and your hardware. Override
the model with `--model mistral:7b-instruct-q4_0` or
`--model deepseek-r1:14b` etc. If the first run produces a weak draft,
re-run with `--overwrite --temperature 0.9` to get a different angle.

Before publishing, open the JSON and skim the `body_html` field. A
local 7B–14B model will get the structure right but the prose often
needs a tightening pass — edit the JSON directly, or load it into
Claude Code for polish.

### Tuesday 9 AM: publish

Start Claude Code in the project root and say:

> publish draft 25 from drafts/025-superhuman.json

Claude will:

1. Read the draft JSON.
2. Read `issues/024-linear.html` as the template.
3. Scan `issues/` for the three most recent prior issues (for the
   related-grid cards) and check the current featured cover variant
   (to avoid repeating it).
4. Write `issues/025-superhuman.html`.
5. Back up and patch `archive.html` (prepend new card, update masthead
   date, update issue-range label).
6. Back up and patch `index.html` (rewrite featured section, rebuild
   recent-issues grid to 5 cards + archive tile, update footer "Latest
   Issue" link).

You can then spot-check the rendered page locally:

```
python -m http.server 8080
```

and open http://localhost:8080/. If anything looks off, tell Claude
what to fix or restore the `.bak` files.

---

## Files this toolchain produces

```
notes/
  ├── pick-2026-04-20.md         raw output of the last picker run
  └── 025-superhuman.md          research notes for issue 25

drafts/
  └── 025-superhuman.json        structured draft from Ollama

issues/
  └── 025-superhuman.html        published issue (written by Claude Code)

backlog.txt                      list of products to profile, one per line
```

Backups `archive.html.bak` and `index.html.bak` are written in-place
before the publish step touches those files. Delete them once you've
verified the publish went clean.

---

## Useful overrides

```
# Use a different writing model (see `ollama list`).
python tools\write_issue.py --product "Superhuman" --model deepseek-r1:14b

# Override the publish date.
python tools\write_issue.py --product "Superhuman" --date 2026-05-05

# Override the issue number (skipping one, or renumbering).
python tools\chat.py research --product "Superhuman" --issue-num 26
python tools\write_issue.py --product "Superhuman" --issue-num 26

# Get research from ChatGPT or Gemini instead of Claude.
python tools\chat.py research --product "Ghost" --provider chatgpt
python tools\chat.py research --product "Ghost" --provider gemini

# Regenerate a draft with higher temperature.
python tools\write_issue.py --product "Superhuman" --overwrite --temperature 0.9
```

---

## Troubleshooting

**`Could not reach Ollama at http://localhost:11434/api/chat`** — start
the Ollama server: `ollama serve`. Check that the model is pulled:
`ollama list`.

**`Clipboard is empty; aborting.`** — you pressed Enter before copying
the response. Re-run the command.

**The parsed backlog picks look wrong** — open the raw file in
`notes/pick-YYYY-MM-DD.md`, edit by hand, and either append manually to
`backlog.txt` or re-run `chat.py pick` with a different provider.

**Ollama's JSON output is malformed** — the script saves the raw
response to `drafts/NNN-slug.raw.txt` and attempts bracket recovery.
If it still fails, re-run with `--overwrite` (and possibly a different
model or higher `--num-predict`). Smaller 7B models sometimes truncate
the JSON mid-essay; try `--num-predict 12000` or switch to
`gemma4:e4b`/`deepseek-r1:14b`.

**Draft prose feels flat** — local open-weight models in this size range
won't match frontier models on voice. Two workable paths: (a) hand-edit
the `body_html` directly in the JSON before publishing; (b) paste the
draft into a free web chat with the instruction "rewrite this essay in
a more literary voice, keeping the structure" and paste the result back.
Neither costs anything.

**Publish went wrong** — restore `archive.html.bak` → `archive.html`
and `index.html.bak` → `index.html`, delete `issues/NNN-slug.html`, and
ask Claude Code to publish again.
