# Windows Setup Notes

This project was developed and tested on Linux (and runs there without any
of the issues below). These are the Windows-specific rough edges hit while
setting it up natively — collected here so they're documented once instead
of rediscovered.

## 1. `chroma-hnswlib` fails to build (`unresolved external symbol __imp__Py*`, `LNK1120`)

**Symptom:** `pip install -r backend\requirements.txt` fails while building
`chroma-hnswlib`, with dozens of `LNK2001: unresolved external symbol
__imp__Py...` errors ending in `fatal error LNK1120`.

**Cause:** No prebuilt wheel exists for your exact Python build, so pip
compiles it from source — and if you run `pip install` from a plain
terminal (not an x64-configured VS build prompt), MSVC Build Tools can
default to its 32-bit (`x86`) host/target toolset while your Python
interpreter is 64-bit. The compile step succeeds; the *link* step then
fails because a 32-bit object file can't link against 64-bit Python's
import library.

**Fix:**
1. Open **"x64 Native Tools Command Prompt for VS 2022"** from the Start
   Menu — not a plain terminal, not the generic "Developer Command Prompt".
2. `cd /d C:\path\to\ai_teacher`
3. `.venv\Scripts\activate`
4. `python -m pip install -r backend\requirements.txt`

Sanity-check your Python isn't itself 32-bit first:
```
python -c "import struct; print(struct.calcsize('P')*8)"
```
should print `64`. If it prints `32`, reinstall 64-bit Python 3.12 from
python.org and rebuild the venv.

If you'd rather not compile at all: install `chroma-hnswlib` via
conda-forge (`conda install -c conda-forge chroma-hnswlib`), which ships
prebuilt Windows binaries, then `pip install` the rest.

## 2. Tests fail with "async def functions are not natively supported"

**Symptom:** `python -m pytest -q` runs, but every `async def` test fails
with that message, and you see `PytestConfigWarning: Unknown config option:
asyncio_mode`.

**Cause:** `backend\requirements.txt` (production deps) deliberately does
**not** include `pytest`/`pytest-asyncio` — those are test-only and live in
`backend\requirements-dev.txt` instead, so the production Docker image
doesn't carry them. If you only ever ran the first file, `pytest-asyncio`
was never installed (or you have a stray `pytest` from something else,
sans the plugin), so `pytest.ini`'s `asyncio_mode = auto` is silently
ignored and `@pytest.mark.asyncio` tests fail outright.

**Fix:**
```
python -m pip install -r backend\requirements-dev.txt
```
(This includes `-r requirements.txt`, so it's safe to run even if you've
already installed the production file — nothing conflicts.) Then:
```
python -m pytest -q
```
Expected result: `28 passed` (or `26 passed, 2 skipped` if Tesseract/Poppler
aren't installed — see below; that's expected, not a failure).

**Common trap:** if you're pasting commands from a chat/doc into the
terminal, make sure you're copying just the *command*, not the terminal
*prompt* in front of it (e.g. `(.venv) C:\path>`) — `cmd.exe` will choke on
the stray `(` and the install silently won't run, and you'll see the exact
same test failures as if you'd done nothing.

## 3. OCR tests are skipped / OCR doesn't work locally

**Symptom:** `test_ocr_fallback.py`'s 2 tests show as `s` (skipped), and
uploading a scanned PDF doesn't extract any text.

**Cause:** OCR (`backend/services/rag/parser.py`) depends on the
`tesseract` and `pdftoppm` (Poppler) **system binaries**, not just Python
packages. `pytesseract`/`pdf2image` (the Python wrappers, already in
`requirements.txt`) call out to these — they're not bundled by pip on
Windows.

**Fix (optional — only needed if you want OCR working outside Docker):**
1. Install Tesseract: the
   [UB-Mannheim Windows installer](https://github.com/UB-Mannheim/tesseract/wiki).
   Add its install directory (contains `tesseract.exe`) to your `PATH`.
2. Install Poppler: download a build from
   [oschwartz10612/poppler-windows releases](https://github.com/oschwartz10612/poppler-windows/releases),
   extract it, and add its `Library\bin` folder (contains `pdftoppm.exe`)
   to your `PATH`.
3. Open a **new** terminal (so the updated `PATH` takes effect) and re-run
   `python -m pytest tests/test_ocr_fallback.py -v` — both tests should now
   pass instead of skip.

This isn't needed for the Docker deployment — `backend/Dockerfile` installs
`tesseract-ocr` and `poppler-utils` via `apt-get` automatically.

## 4. General note

All three issues above are specific to running the backend **natively on
Windows** outside Docker. If you hit friction setting up local dev, running
everything through `docker compose up` instead sidesteps all of them (the
Linux container has the compiler toolchain, OCR binaries, and dependency
split already handled) — see the main `README.md`'s Docker section.
