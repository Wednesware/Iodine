import asyncio

from ww.mg26_11.filepath import FilePath
from ww.mg26_11.logging import log


class FileInput:
    def __init__(
        self,
        path: str | FilePath,
        submit_condition: str = "body.endswith('\\n')",
        interval: float | int = 0.1,
        silent: bool = False,
        solid_header: str = "",
        solid_footer: str = "",
    ) -> None:
        self.path: FilePath = FilePath(path)
        self.submit_condition: str = submit_condition
        self.interval: float | int = interval
        self.silent: bool = silent
        self.solid_header: str = solid_header
        self.solid_footer: str = solid_footer

        self.file = None
        self.body: str = ""

    def _extract_body(self, content: str) -> str:
        if self.solid_header and not content.startswith(self.solid_header):
            return ""
        if self.solid_footer and not content.endswith(self.solid_footer):
            return ""
        if self.solid_header:
            content = content[len(self.solid_header):]
        if self.solid_footer:
            footer_index = content.rfind(self.solid_footer)
            if footer_index == -1:
                return ""
            content = content[:footer_index]
        if self.solid_header and self.solid_header in content:
            return ""
        return content

    def write(self):
        self.file.seek(0)
        self.file.truncate(0)
        self.file.write(self.solid_header + self.body + self.solid_footer)
        self.file.flush()

    async def waitForInput(self) -> str:
        starter_log: log = (
            log(f"Awaiting input in file: {self.path}...")
            if not self.silent
            else ...
        )
        starter_log.print() if not self.silent else ...
        with open(str(self.path), "w+") as self.file:
            self.body = ""
            self.write()
            while True:
                self.file.seek(0)
                content: str = self.file.read()
                expected_length = len(self.solid_header) + len(self.body) + len(self.solid_footer)
                current_header = content[:len(self.solid_header)] if self.solid_header else ""
                footer_start = max(len(content) - len(self.solid_footer), 0) if self.solid_footer else len(content)
                current_footer = content[footer_start:] if self.solid_footer else ""
                if len(content) != expected_length or current_header != self.solid_header or current_footer != self.solid_footer:
                    self.body = self._extract_body(content)
                    log("Fixed file boundaries.").print() if not self.silent else ...
                    self.write()
                if eval(
                    self.submit_condition,
                    {
                        "content": self.solid_header + self.body + self.solid_footer,
                        "body": self.body,
                        "fileinput": self,
                    },
                ):
                    starter_log.sublog(
                        "Submit condition met, returning content."
                    ).print() if not self.silent else ...
                    return self.body
                await asyncio.sleep(self.interval)