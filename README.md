# Iodine

Iodine is a small Python toolkit for interactive terminal applications. It
provides editable prompts, multi-line editors, autocomplete, searchable
selection menus, ANSI styling, key bindings, and a file-backed asynchronous
input primitive.

The interactive widgets use a POSIX terminal in raw mode and redraw only the
part of the screen owned by the widget.

## Installation

Iodine is installed through the Wednesware package tool:

```sh
n2 get iodine
```

The library currently requires:

- Python 3.12 or newer
- Nitrogen 26.56 or newer
- Magnesium, for colors, file paths, and logging
- A POSIX terminal for `run()` and the terminal helpers

## Quick start

```python
from iodine import run
from iodine.widgets import TextInput

name = run(TextInput(prompt="Name: ", placeholder="Ada Lovelace"))
if name is not None:
	print(f"Hello, {name}!")
```

`run()` returns the submitted value, or `None` when the user cancels with
Escape or Ctrl+C.

For a tour of all widgets, run:

```sh
python examples/demo.py
```

## Dependencies

- Python 3.12+
- Nitrogen 26.57+ (`pip install wwn`)

## Widgets

All widgets inherit from `iodine.widgets.Widget`. They expose `done`,
`cancelled`, and `result`, and can be driven with `iodine.run`.

### `TextInput`

```python
from iodine import run
from iodine.widgets import TextInput

def required(value):
	return "This field is required" if not value.strip() else None

value = run(TextInput(
	prompt="Username: ",
	value="initial",
	placeholder="Enter a username",
	validator=required,
	history=["alice", "bob"],
))
```

`TextInput` is a single-line editor with:

- Cursor movement with Left, Right, Home, End, Ctrl+A, and Ctrl+E
- Backspace, Delete, Ctrl+W (delete the previous word), and Ctrl+U (delete
  to the beginning)
- Up and Down history navigation
- Placeholders and inline validation errors
- Password masking with `password=True` and a configurable `mask_char`
- A custom `Theme` through the `theme` argument

Press Enter to submit. A validator receives the current string and should
return an error message, or `None` to allow submission. Successful submission
also appends the value to the widget's in-memory history.

### `MultilineInput`

```python
from iodine import run
from iodine.widgets import MultilineInput

notes = run(MultilineInput(
	prompt="Notes:",
	line_numbers=True,
	max_visible_lines=12,
))
```

`MultilineInput` behaves like a minimal terminal text area. Enter inserts a
newline, Tab inserts four spaces, and the cursor can move across lines. Use
Ctrl+D to submit the complete text and Escape or Ctrl+C to cancel. The result
is a single string containing newline characters.

Useful options are `value`, `placeholder`, `line_numbers`, `theme`, and
`max_visible_lines`. When the content is taller than the visible limit, the
editor scrolls to keep the cursor in view.

### `SuggestInput`

```python
from iodine import run
from iodine.widgets import SuggestInput

language = run(SuggestInput(
	suggestions=["python", "rust", "ruby", "typescript"],
	fuzzy=True,
	prompt="Language: ",
))
```

`SuggestInput` extends `TextInput` with a completion list. Suggestions can be
a list of strings or a callable receiving the current text and returning a
list. Matching is case-insensitive prefix matching by default; `fuzzy=True`
matches characters in order anywhere in a candidate. Use Up and Down to move
through matches and Tab to accept the highlighted suggestion. `max_visible`
limits the number of displayed suggestions, and `accept_key` changes the key
used to accept one.

All normal `TextInput` options, including validation and password masking, are
also available as keyword arguments.

### `SyntaxInput`

```python
from iodine import PYTHON, run
from iodine.widgets import SyntaxInput

source = run(SyntaxInput(
	PYTHON,
	prompt="Code:",
	line_numbers=True,
	value="def greet(name):\n    return f'hello {name}'",
))
```

`SyntaxInput` is a `MultilineInput` that applies a supplied `Highlighter` to
each line while it is edited. Iodine includes the ready-made `PYTHON` and
`JSON` highlighters. Highlighting is regex-based and affects display only;
the submitted result remains plain text.

### `SelectMenu` and `Option`

```python
from iodine import run
from iodine.widgets import SelectMenu
from iodine.widgets.select import Option

choice = run(SelectMenu(
	[Option("Small", "s"), Option("Large", "l")],
	title="Size",
))
```

Options may be strings or `Option(label, value)` objects. A single-select menu
returns the selected value. Set `multi=True` to show checkboxes; Space toggles
the current item and Enter returns a list of selected values.

Selection menus support:

- Live, case-insensitive substring filtering while `searchable=True`
- Up, Down, Page Up, Page Down, Home, and End navigation
- Scrolling with `max_visible`
- Custom titles, pointers, themes, and item rendering

`render_item` can be a callable with the signature
`(option, is_cursor, is_checked) -> str`. It replaces the default row
renderer.

## Running widgets

```python
from iodine import Keymap, run
from iodine.widgets import TextInput

hotkeys = Keymap()

@hotkeys.on("CTRL_S")
def save(_key):
	print("saved")

value = run(
	TextInput(prompt="Command: "),
	global_keymap=hotkeys,
	alt_screen=True,
)
```

`run(widget, global_keymap=None, alt_screen=False, term=None)` manages raw
terminal input, hides the cursor, renders the widget, dispatches keys, and
restores the terminal even when the widget exits. A global keymap is checked
before the widget's own handler. `alt_screen=True` runs the interaction in the
terminal's alternate screen buffer. Pass a custom `Terminal` when embedding
Iodine in another terminal loop or when capturing output.

## Styling

### `Style`

`Style` wraps text in ANSI formatting:

```python
from iodine import Style

warning = Style(fg="yellow", bold=True).wrap("Warning")
```

Supported flags are `bold`, `dim`, `italic`, `underline`, `reverse`, and
`strike`. Foreground and background colors may be named colors such as
`"cyan"`, 256-color palette integers, RGB tuples such as `(255, 120, 0)`, or
color names understood by Magnesium.

`Style.ansi()` returns the ANSI start sequence. `Style.merge(other)` returns a
new style with the explicit attributes of `other` layered over the original.

### `Theme`

`Theme` is a named collection of styles used by widgets. The default theme
contains `text`, `prompt`, `placeholder`, `cursor`, `error`, `hint`,
`selected`, `unselected`, `pointer`, `checked`, `title`, `suggestion`,
`suggestion_selected`, and `line_number` styles.

Override only the parts you need:

```python
from iodine import Style, Theme
from iodine.widgets import TextInput

theme = Theme(
	prompt=Style(fg="green", bold=True),
	error=Style(fg="bright_red", bold=True),
)
field = TextInput(prompt="> ", theme=theme)
```

`DEFAULT_THEME` is the shared default theme. Create a separate `Theme` when
an application needs independent widget styling.

## Key handling

`Key` represents one decoded terminal key. Printable input has
`name="CHAR"` and its character in `char`; special keys use names such as
`ENTER`, `ESC`, `UP`, `DOWN`, `TAB`, `BACKSPACE`, `DELETE`, `PAGE_UP`, and
`CTRL_C`. `Key.token()` returns the printable character or canonical key name.

`read_key(fd, timeout=None)` reads and decodes one key from a file descriptor.
With a timeout, it returns `None` if no input is available before the timeout.

`Keymap` supports single keys and multi-key chords:

```python
from iodine import Keymap

keys = Keymap()
keys.bind("F1", show_help)
keys.bind("q", quit_app)
keys.bind_chord("g", "g", callback=go_to_top)
```

`bind()` and `bind_chord()` return the callback, `on()` provides decorator
syntax, `unbind()` removes a single-key binding, and `dispatch(key)` returns
`True` when a callback handled the key.

## Syntax highlighting

Create custom highlighters from ordered regular-expression rules:

```python
from iodine import Highlighter, Style

INI = Highlighter([
	(r"^\\[.*\\]$", Style(fg="cyan", bold=True)),
	(r"^[A-Za-z_]+(?=\\s*=)", Style(fg="yellow")),
])
```

Rules are compiled when the `Highlighter` is created. Earlier rules win when
matches overlap. `styles_for(text)` returns one style per character, while
`highlight(text)` returns the text wrapped in ANSI sequences.

## Terminal primitives

`Terminal` provides the low-level POSIX terminal operations used by `run()`:

- `raw_mode()` temporarily enables character-at-a-time input
- `hidden_cursor()` hides and restores the cursor
- `alt_screen()` enters and leaves the alternate screen buffer
- `redraw(previous_line_count, lines)` replaces a rendered block
- `clear_block(previous_line_count)` clears a rendered block
- `size` returns `(columns, rows)`
- `write()`, `flush()`, and `newline()` provide output helpers

Most applications should use `run()` instead of managing these contexts
directly.

## File-backed input

`iodine.filib.FileInput` lets an external editor or process submit text by
editing a file. It is useful for simple file-based consoles and integrations
where the producer and consumer do not share a direct input stream.

```python
import asyncio
from iodine.filib import FileInput

async def main():
	prompt = FileInput(
		"input.txt",
		solid_header="BEGIN\n",
		solid_footer="\nEND",
		submit_condition="body.endswith(';')",
		interval=0.1,
	)
	body = await prompt.waitForInput()
	print(body)

asyncio.run(main())
```

When `waitForInput()` starts, it writes the configured header, current body,
and footer to the path, then polls at `interval` seconds. The submit
condition is evaluated with these names available:

- `body`: text between the solid boundaries
- `content`: complete file content, including boundaries
- `fileinput`: the active `FileInput` instance

The method returns the body without the header or footer and preserves its
whitespace. If the boundaries are changed or corrupted, FileInput extracts a
valid body when possible and rewrites the protected boundaries. Set `silent=True`
to suppress status logging.

## Extending widgets

Subclass `Widget` when you need a custom interaction. Implement
`render_lines()` to return the lines to display and `handle_key(key)` to
mutate state. Call `submit(value)` when the interaction is complete or
`cancel()` when it should stop without a result.

For an editor based on an existing widget, override its rendering hooks such
as `TextInput._char_style()` or `MultilineInput._char_style()` instead of
duplicating cursor and editing behavior.

## Project layout

```text
iodine/
├── iodine/
│   ├── __init__.py          # terminal, styling, keys, highlighting, run()
│   ├── filib.py             # asynchronous file-backed input
│   └── widgets/              # interactive widgets
├── examples/demo.py          # interactive widget showcase
└── tests/                    # automated tests
```

## License

Iodine is released under the MIT License. See [LICENSE.md](LICENSE.md).