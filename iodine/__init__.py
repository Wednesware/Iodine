from __future__ import annotations

import os, select, re, contextlib, termios, sys, tty, shutil

from ww.mg26_11.logging import error as ww_error
from ww.mg26_11.color import Color


ESCAPE_SEQUENCES = {
    "\x1b[A": "UP", "\x1b[B": "DOWN", "\x1b[C": "RIGHT", "\x1b[D": "LEFT",
    "\x1bOA": "UP", "\x1bOB": "DOWN", "\x1bOC": "RIGHT", "\x1bOD": "LEFT",
    "\x1b[H": "HOME", "\x1b[F": "END",
    "\x1b[1~": "HOME", "\x1b[4~": "END", "\x1b[7~": "HOME", "\x1b[8~": "END",
    "\x1b[3~": "DELETE",
    "\x1b[5~": "PAGE_UP", "\x1b[6~": "PAGE_DOWN",
    "\x1bOP": "F1", "\x1bOQ": "F2", "\x1bOR": "F3", "\x1bOS": "F4",
    "\x1b[15~": "F5", "\x1b[17~": "F6", "\x1b[18~": "F7", "\x1b[19~": "F8",
    "\x1b[20~": "F9", "\x1b[21~": "F10", "\x1b[23~": "F11", "\x1b[24~": "F12",
    "\x1b[Z": "SHIFT_TAB",
    "\x1b[1;5C": "CTRL_RIGHT", "\x1b[1;5D": "CTRL_LEFT",
}

NAMED_COLORS = {
    "black": 0, "red": 1, "green": 2, "yellow": 3,
    "blue": 4, "magenta": 5, "cyan": 6, "white": 7,
    "bright_black": 8, "gray": 8, "grey": 8,
    "bright_red": 9, "bright_green": 10, "bright_yellow": 11,
    "bright_blue": 12, "bright_magenta": 13, "bright_cyan": 14, "bright_white": 15,
}

class Terminal:
    """Wraps a POSIX tty with raw-mode + ANSI helpers.

    Widgets never emit real cursor moves for editing (they render a "virtual"
    cursor as a highlighted character instead), which means redrawing a block
    of N lines only ever needs: move up (N-1), carriage return, clear to end
    of screen, write new block. See :meth:`redraw`.
    """

    def __init__(self, out=None, in_fd: int | None = None):
        self.out = out or sys.stdout
        self.fd = in_fd if in_fd is not None else sys.stdin.fileno()
        self._saved_attrs = None

    # -- raw mode -----------------------------------------------------
    @contextlib.contextmanager
    def raw_mode(self):
        self._saved_attrs = termios.tcgetattr(self.fd)
        tty.setraw(self.fd)
        try:
            yield self
        finally:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self._saved_attrs)

    @contextlib.contextmanager
    def hidden_cursor(self):
        self.write("\x1b[?25l")
        self.flush()
        try:
            yield self
        finally:
            self.write("\x1b[?25h")
            self.flush()

    @contextlib.contextmanager
    def alt_screen(self):
        self.write("\x1b[?1049h")
        self.flush()
        try:
            yield self
        finally:
            self.write("\x1b[?1049l")
            self.flush()

    # -- low level ------------------------------------------------------
    def write(self, s: str) -> None:
        self.out.write(s)

    def flush(self) -> None:
        self.out.flush()

    @property
    def size(self) -> tuple[int, int]:
        cols, rows = shutil.get_terminal_size()
        return cols, rows

    # -- block redraw ---------------------------------------------------
    def redraw(self, prev_line_count: int, lines: list[str]) -> int:
        """Erase the previously drawn block (``prev_line_count`` lines,
        cursor assumed at the end of the last line with no trailing
        newline) and write ``lines`` in its place. Returns new line count.
        """
        if prev_line_count:
            if prev_line_count > 1:
                self.write(f"\x1b[{prev_line_count - 1}A")
            self.write("\r\x1b[J")
        self.write("\r\n".join(lines))
        self.flush()
        return len(lines)

    def clear_block(self, prev_line_count: int) -> None:
        if prev_line_count:
            if prev_line_count > 1:
                self.write(f"\x1b[{prev_line_count - 1}A")
            self.write("\r\x1b[J")
        self.flush()

    def newline(self) -> None:
        self.write("\r\n")
        self.flush()

class Style:
    def __init__(self, fg=None, bg=None, bold=False, dim=False, italic=False,
                 underline=False, reverse=False, strike=False):
        self.fg = fg
        self.bg = bg
        self.bold = bold
        self.dim = dim
        self.italic = italic
        self.underline = underline
        self.reverse = reverse
        self.strike = strike

    def _color_code(self, color, ground: str) -> str | None:
        base = 38 if ground == "fg" else 48
        if isinstance(color, tuple) and len(color) == 3:
            r, g, b = color
            return f"{base};2;{r};{g};{b}"
        if isinstance(color, str):
            idx = NAMED_COLORS.get(color)
            if idx is not None:
                return f"{base};5;{idx}"
            rgb = Color.get(color)
            if rgb is not None:
                r, g, b = rgb
                return f"{base};2;{r};{g};{b}"
            return None
        if isinstance(color, int):
            return f"{base};5;{color}"
        return None

    def ansi(self) -> str:
        parts = []
        if self.bold:
            parts.append("1")
        if self.dim:
            parts.append("2")
        if self.italic:
            parts.append("3")
        if self.underline:
            parts.append("4")
        if self.reverse:
            parts.append("7")
        if self.strike:
            parts.append("9")
        if self.fg is not None:
            c = self._color_code(self.fg, "fg")
            if c:
                parts.append(c)
        if self.bg is not None:
            c = self._color_code(self.bg, "bg")
            if c:
                parts.append(c)
        if not parts:
            return ""
        return "\x1b[" + ";".join(parts) + "m"

    def wrap(self, text: str) -> str:
        code = self.ansi()
        return f"{code}{text}{Color.reset}" if code else text

    def merge(self, other: "Style | None") -> "Style":
        """Return a new style with ``other``'s explicit attributes layered
        on top of this one (used to combine e.g. a cursor style with a
        syntax-highlight style)."""
        if other is None:
            return self
        return Style(
            fg=other.fg if other.fg is not None else self.fg,
            bg=other.bg if other.bg is not None else self.bg,
            bold=other.bold or self.bold,
            dim=other.dim or self.dim,
            italic=other.italic or self.italic,
            underline=other.underline or self.underline,
            reverse=other.reverse or self.reverse,
            strike=other.strike or self.strike,
        )


class Theme:
    """A named bundle of styles widgets pull from, so an app can restyle
    everything in one place."""

    def __init__(self, **styles: Style):
        self.styles = {
            "text": Style(),
            "prompt": Style(fg="cyan", bold=True),
            "placeholder": Style(dim=True),
            "cursor": Style(reverse=True),
            "error": Style(fg="red"),
            "hint": Style(dim=True, italic=True),
            "selected": Style(fg="black", bg="cyan", bold=True),
            "unselected": Style(),
            "pointer": Style(fg="cyan", bold=True),
            "checked": Style(fg="green", bold=True),
            "title": Style(bold=True, underline=True),
            "suggestion": Style(dim=True),
            "suggestion_selected": Style(fg="black", bg="yellow"),
            "line_number": Style(dim=True),
        }
        self.styles.update(styles)

    def __getitem__(self, key: str) -> Style:
        return self.styles[key]

    def get(self, key: str, default: Style | None = None) -> Style:
        return self.styles.get(key, default or Style())

DEFAULT_THEME = Theme()

class Key:
    __slots__ = ("name", "char")

    def __init__(self, name: str, char: str | None = None):
        self.name = name
        self.char = char

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other or self.char == other
        if isinstance(other, Key):
            return self.name == other.name and self.char == other.char
        return NotImplemented

    def __hash__(self):
        return hash((self.name, self.char))

    def __repr__(self):
        return f"Key({self.name!r}, {self.char!r})"

    def token(self) -> str:
        """The value most useful for keymap lookups: the char if printable,
        otherwise the canonical name."""
        return self.char if self.name == "CHAR" and self.char else self.name


def read_key(fd: int, timeout: float | None = None) -> Key | None:
    """Read and decode a single key event from ``fd``.

    Blocks until a key is available unless ``timeout`` is given, in which
    case ``None`` is returned if nothing arrives in time.
    """
    if timeout is not None:
        ready, _, _ = select.select([fd], [], [], timeout)
        if not ready:
            return None

    first = os.read(fd, 1)
    if not first:
        return None
    ch = first.decode(errors="ignore")

    if ch == "\x1b":
        seq = ch
        while True:
            ready, _, _ = select.select([fd], [], [], 0.01)
            if not ready:
                break
            seq += os.read(fd, 1).decode(errors="ignore")
            if seq in ESCAPE_SEQUENCES:
                break
            if len(seq) > 8:
                break
        if seq == "\x1b":
            return Key("ESC")
        name = ESCAPE_SEQUENCES.get(seq)
        return Key(name) if name else Key("UNKNOWN", char=seq)

    if ch in ("\r", "\n"):
        return Key("ENTER")
    if ch == "\t":
        return Key("TAB")
    if ch in ("\x7f", "\x08"):
        return Key("BACKSPACE")
    if ch == "\x03":
        return Key("CTRL_C")
    if ch == "\x04":
        return Key("CTRL_D")

    code = ord(ch)
    if 1 <= code <= 26:
        # Ctrl+A..Ctrl+Z (Ctrl+I == Tab, Ctrl+M == Enter handled above)
        letter = chr(code + 96).upper()
        return Key(f"CTRL_{letter}")

    return Key("CHAR", char=ch)

class Keymap:
    """A flat map of key token -> callback, plus support for multi-key
    chord sequences (e.g. ``"g g"`` vim-style double-tap)."""

    def __init__(self):
        self._bindings: dict[str, callable] = {}
        self._chords: dict[tuple, callable] = {}
        self._chord_buffer: list[str] = []

    def bind(self, key: str, callback):
        """Bind a single key token, e.g. ``"F1"``, ``"CTRL_S"``, or a
        literal character like ``"q"``."""
        self._bindings[key] = callback
        return callback

    def bind_chord(self, *keys: str, callback):
        """Bind a sequence of key tokens pressed in order, e.g.
        ``bind_chord("g", "g", callback=go_to_top)``."""
        self._chords[tuple(keys)] = callback
        return callback

    def unbind(self, key: str):
        self._bindings.pop(key, None)

    def on(self, key: str):
        """Decorator form of :meth:`bind`."""
        def deco(fn):
            self.bind(key, fn)
            return fn
        return deco

    def dispatch(self, key: Key) -> bool:
        """Try to handle ``key``. Returns True if a callback fired."""
        token = key.token()

        if self._chords:
            self._chord_buffer.append(token)
            # trim buffer to longest chord length
            max_len = max((len(c) for c in self._chords), default=0)
            if len(self._chord_buffer) > max_len:
                self._chord_buffer = self._chord_buffer[-max_len:]
            for chord, cb in self._chords.items():
                n = len(chord)
                if tuple(self._chord_buffer[-n:]) == chord:
                    self._chord_buffer.clear()
                    cb(key)
                    return True

        cb = self._bindings.get(token)
        if cb is None and key.name != "CHAR":
            cb = self._bindings.get(key.name)
        if cb:
            cb(key)
            return True
        return False

class Highlighter:
    def __init__(self, rules: list[tuple[str, Style]]):
        self.rules = [(re.compile(pattern), style) for pattern, style in rules]

    def styles_for(self, text: str) -> list[Style | None]:
        """Return a per-character list of the winning Style (or None)."""
        styled: list[Style | None] = [None] * len(text)
        for regex, style in self.rules:
            for m in regex.finditer(text):
                start, end = m.span()
                for i in range(start, end):
                    if styled[i] is None:
                        styled[i] = style
        return styled

    def highlight(self, text: str) -> str:
        """Return ``text`` wrapped in ANSI codes per matching rule."""
        styles = self.styles_for(text)
        out = []
        i, n = 0, len(text)
        while i < n:
            style = styles[i]
            j = i
            while j < n and styles[j] is style:
                j += 1
            chunk = text[i:j]
            out.append(style.wrap(chunk) if style else chunk)
            i = j
        return "".join(out)


PYTHON = Highlighter([
    (r"#.*$", Style(fg="bright_black", italic=True)),
    (r"(\"\"\".*?\"\"\"|'''.*?''')", Style(fg="green")),
    (r'(\".*?\"|\'.*?\')', Style(fg="green")),
    (r"\b\d+(\.\d+)?\b", Style(fg="magenta")),
    (r"\b(def|class|if|elif|else|for|while|return|import|from|as|with|"
     r"try|except|finally|raise|yield|lambda|in|not|and|or|is|None|True|"
     r"False|pass|break|continue|async|await|self)\b", Style(fg="cyan", bold=True)),
    (r"\b([A-Za-z_][A-Za-z0-9_]*)(?=\()", Style(fg="yellow")),
])

JSON = Highlighter([
    (r'"(\\.|[^"\\])*"\s*(?=:)', Style(fg="cyan")),
    (r'"(\\.|[^"\\])*"', Style(fg="green")),
    (r"\b(true|false|null)\b", Style(fg="magenta", bold=True)),
    (r"-?\b\d+(\.\d+)?([eE][+-]?\d+)?\b", Style(fg="yellow")),
    (r"[{}\[\],:]", Style(fg="bright_black")),
])

def run(
    widget,
    global_keymap: Keymap | None = None,
    alt_screen: bool = False,
    term: Terminal | None = None,
):
    """Drive ``widget`` interactively until it submits or is cancelled.

    ``global_keymap`` lets an application register hotkeys (e.g. F1 for
    help, Ctrl+S to save) that are checked before the widget's own key
    handling, regardless of which widget is currently focused.

    Returns the widget's result, or ``None`` if cancelled.
    """
    term = term or Terminal()
    caught: Exception | None = None
    with term.raw_mode():
        with term.hidden_cursor():
            stack = []
            if alt_screen:
                cm = term.alt_screen()
                cm.__enter__()
                stack.append(cm)
            try:
                widget.render(term)
                while not widget.done:
                    key = read_key(term.fd)
                    if key is None:
                        continue
                    if key.name == "CTRL_C" and not (global_keymap and "CTRL_C" in global_keymap._bindings):
                        widget.cancel()
                        break
                    handled = False
                    if global_keymap is not None:
                        handled = global_keymap.dispatch(key)
                    if not handled:
                        widget.handle_key(key)
                    widget.render(term)
            except Exception as exc:
                caught = exc
            finally:
                for cm in reversed(stack):
                    cm.__exit__(None, None, None)
                term.newline()
    if caught is not None:
        ww_error.from_exception(caught).print()
        raise caught
    return None if widget.cancelled else widget.result
