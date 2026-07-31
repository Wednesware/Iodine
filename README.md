# Wednesware Iodine

Linux/MacOS smart terminal input widgets for Python 3.7+ (Windows support is experimental).

Requires [Magnesium](https://github.com/Wednesware/Magnesium) 26.11+

## Features

- **Raw-mode terminal control** with alt-screen / hidden cursor helpers (`iodine.Terminal`)
- **Key decoding** for arrows, Home/End/Delete/PageUp/Down, function keys, Ctrl+letter chords, Tab/Shift+Tab (`iodine.read_key`)
- **`TextInput`** - single-line input with cursor movement, insert/delete, word-delete (Ctrl+W), history (Up/Down), placeholders, password masking, live validation
- **`MultilineInput`** - a minimal textarea: multi-line editing, optional line numbers, Ctrl+D to submit
- **`SuggestInput`** - `TextInput` + autocomplete dropdown (prefix or fuzzy matching, Tab/Right to accept, Up/Down to navigate suggestions)
- **`SyntaxInput`** - `MultilineInput` with live regex-based syntax highlighting (ships with `PYTHON` and `JSON` rule sets, or bring your own `Highlighter`)
- **`SelectMenu`** - customizable selection screens: single or multi-select (checkboxes), live search/filter, scrolling for long lists, fully custom item rendering
- **`Keymap`** - keybind trigger system for both widget-local bindings and global hotkeys (e.g. F1 for help, Ctrl+S to save) checked across the whole run loop, plus multi-key chord sequences
- **`Theme`/`Style`** - 16/256-color, truecolor, and (via `ww.mg26_11.color`) 140+ named CSS colors, fully customizable per-widget

## Design

- All rendering uses a "virtual cursor" (a reverse-video character drawn in
  the string itself) instead of moving the real terminal cursor - this
  avoids fragile ANSI cursor-position math entirely.
- Every widget redraw clears and rewrites only its own block of lines
  (`Terminal.redraw`), so widgets can be composed/run in sequence cleanly.
- Extend anything: subclass `Widget` and implement `render_lines()` +
  `handle_key()`.

## Quick start

```python
from ww.i import run
from ww.i.widgets.text_input import TextInput

name = run(TextInput(prompt="Name: ", placeholder="e.g. Ada"))
print(name)
```

## Selection screen

```python
from ww.i import run
from ww.i.widgets.select import SelectMenu

choice = run(SelectMenu(["apple", "banana", "cherry"], title="Pick a fruit:"))
```

Multi-select with checkboxes:

```python
picks = run(SelectMenu(["apple", "banana", "cherry"], multi=True))
```

## Suggestions

```python
from ww.i import run
from ww.i.widgets.suggest_input import SuggestInput

lang = run(SuggestInput(suggestions=["python", "rust", "go"], fuzzy=True))
```

## Syntax highlighting

```python
from ww.i import run
from ww.i.widgets.syntax_input import SyntaxInput
from ww.i.highlight import PYTHON

code = run(SyntaxInput(PYTHON, line_numbers=True))
```

## Global keybind triggers

```python
from ww.i import run
from ww.i.widgets.text_input import TextInput
from ww.i.keymap import Keymap

hotkeys = Keymap()

@hotkeys.on("F1")
def show_help(key):
    print("help!")

run(TextInput(prompt="> "), global_keymap=hotkeys)
```
