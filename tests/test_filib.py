import asyncio

from iodine.filib import FileInput


async def _check_preserves_whitespace(tmp_path):
    path = tmp_path / "input.txt"
    fi = FileInput(
        path,
        solid_header="H\n",
        solid_footer="\nF",
        submit_condition="body.endswith(';')",
        interval=0.01,
        silent=True,
        clear_file_on_submit=False,
    )

    async def writer():
        await asyncio.sleep(0.05)
        path.write_text("H\n  hi  ;\nF")

    writer_task = asyncio.create_task(writer())
    result = await fi.waitForInput()
    await writer_task

    assert result == "  hi  ;", result


def test_wait_for_input_keeps_body_whitespace(tmp_path):
    asyncio.run(_check_preserves_whitespace(tmp_path))


async def _check_corrupted_header_resets_body(tmp_path):
    path = tmp_path / "input.txt"
    fi = FileInput(
        path,
        solid_header="H\n",
        solid_footer="\nF",
        submit_condition="body == ' x '",
        interval=0.01,
        silent=True,
        clear_file_on_submit=False,
    )

    path.write_text("wH\n x \nF")
    with open(path, "r") as file:
        content = file.read()
    assert fi._extract_body(content) == ""

    path.write_text("H\nTwH\n x \nF")
    with open(path, "r") as file:
        content = file.read()
    assert fi._extract_body(content) == ""


def test_wait_for_input_discards_corrupted_boundaries(tmp_path):
    asyncio.run(_check_corrupted_header_resets_body(tmp_path))


def test_wait_for_input_rejects_same_loop_rewrites(tmp_path):
    fi = FileInput(tmp_path / "input.txt", silent=True)
    loop_id = id(asyncio.get_running_loop())
    fi._last_seen_loop_id = loop_id
    fi._last_seen_mtime_ns = 100

    assert fi._has_same_loop_rewrite(200, loop_id) is True
    assert fi._has_same_loop_rewrite(100, loop_id) is False
    assert fi._has_same_loop_rewrite(200, loop_id + 1) is False
