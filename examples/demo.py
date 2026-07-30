"""Interactive demo of every iodine widget.

Run with:  python examples/demo.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from iodine import (
    TextInput, MultilineInput, SuggestInput, SyntaxInput, SelectMenu,
    Option, Keymap, Style, Theme, PYTHON, run,
)


def section(title):
    print(f"\n\033[1;36m== {title} ==\033[0m")


def demo_text_input():
    section("Text input (with validation + history)")

    def not_empty(v):
        return "can't be empty" if not v.strip() else None

    name = run(TextInput(prompt="Your name: ", placeholder="e.g. Ada", validator=not_empty))
    print(f"-> {name!r}")


def demo_password():
    section("Password input")
    pw = run(TextInput(prompt="Password: ", password=True))
    print(f"-> {'*' * len(pw or '')}")


def demo_suggestions():
    section("Text input with suggestions (fuzzy, Tab to accept)")
    langs = ["python", "javascript", "typescript", "rust", "go", "ruby", "java", "kotlin", "swift"]
    lang = run(SuggestInput(suggestions=langs, fuzzy=True, prompt="Language: "))
    print(f"-> {lang!r}")


def demo_multiline():
    section("Multi-line input (Ctrl+D submits, Esc cancels)")
    text = run(MultilineInput(prompt="Notes:", line_numbers=True))
    print(f"-> {text!r}")


def demo_syntax():
    section("Multi-line input with Python syntax highlighting")
    code = run(SyntaxInput(PYTHON, prompt="Code:", line_numbers=True,
                            value='def greet(name):\n    return f"hello {name}"'))
    print(f"-> \n{code}")


def demo_select():
    section("Selection screen (single choice, searchable)")
    options = [Option(f"Option {i}") for i in range(1, 30)]
    choice = run(SelectMenu(options, title="Pick one:", max_visible=8))
    print(f"-> {choice!r}")


def demo_multiselect():
    section("Selection screen (multi-select with checkboxes)")
    fruit = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape"]
    picks = run(SelectMenu(fruit, title="Pick your fruit:", multi=True))
    print(f"-> {picks!r}")


def demo_keybind_triggers():
    section("Global keybind triggers (F1 = help, Ctrl+S = 'saved!', during a text input)")
    hotkeys = Keymap()
    state = {"help": False, "message": ""}

    field = TextInput(prompt="Type something (F1 help, Ctrl+S save): ")

    @hotkeys.on("F1")
    def toggle_help(_key):
        state["help"] = not state["help"]

    @hotkeys.on("CTRL_S")
    def save(_key):
        state["message"] = "saved!"

    # Wrap render to show extra status lines driven by the keybinds above.
    orig_render_lines = field.render_lines

    def render_lines():
        lines = orig_render_lines()
        if state["help"]:
            lines.append(Style(dim=True).wrap("  (this is contextual help toggled by F1)"))
        if state["message"]:
            lines.append(Style(fg="green").wrap(f"  {state['message']}"))
        return lines

    field.render_lines = render_lines
    text = run(field, global_keymap=hotkeys)
    print(f"-> {text!r}")


if __name__ == "__main__":
    demo_text_input()
    demo_password()
    demo_suggestions()
    demo_multiline()
    demo_syntax()
    demo_select()
    demo_multiselect()
    demo_keybind_triggers()
