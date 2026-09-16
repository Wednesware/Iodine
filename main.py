import subprocess

from iodine.filib import FileInput

DEFAULT_COMMAND: str = "python -m main >/dev/null"
DEFAULT_FOOTER: str = "# Enter a command after > and press enter. Type 'quit' to exit."

async def main():
    footer: str = DEFAULT_FOOTER
    fi: FileInput = FileInput("console.sh", solid_header=f"{DEFAULT_COMMAND}\n\n> ", solid_footer=f"\n\n{DEFAULT_FOOTER}")
    while True:
        fi.solid_footer = f"\n\n{footer}"
        try:
            content: str = await fi.waitForInput()
        except KeyboardInterrupt:
            content: str = "quit"
        if content.strip() == "quit":
            fi.path.write(f"{DEFAULT_COMMAND}\n\n#> " + f"\n\n# CONSOLE IS OFF. Run this file in the terminal to turn it on.")
            break
        result: subprocess.CompletedProcess = subprocess.run(content, capture_output=True, shell=True)
        footer = f"{result.stderr.decode().strip()}{result.stdout.decode().strip()}"
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())