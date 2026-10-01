from __future__ import annotations

import time

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Static, Input


BRAND_BG     = "#0B0C0A"
BRAND_GREEN  = "#02462E"
BRAND_GOLD   = "#FEC700"

TEXT_PRIMARY   = "#F1EDE2"
TEXT_SECONDARY = "#9BA397"
TEXT_META      = "#B9B17A"
GREEN_TINT     = "#4E9E7C"
GOLD_DIM       = "#8A751A"

PANEL_BG = "#0D0F0C"
INPUT_BG = "#101310"


def _escape(text: str) -> str:
    return text.replace("[", "［").replace("]", "］")


def _message_md(sent: bool, text: str, stamp: str) -> str:
    e = _escape(text)
    color = GREEN_TINT if sent else BRAND_GOLD
    return f"[{color}]{e}[/]\n[{TEXT_META} dim]{stamp}[/]"


def _info_md(info: list[tuple[str, str]]) -> str:
    rows = []
    for key, value in info:
        rows.append(f"[{TEXT_META}]{key:<9}[/] [{TEXT_SECONDARY}]{value}[/]")
    return "\n".join(rows)


def _header_md() -> str:
    line_len = 120
    return (
        f"[b {BRAND_GOLD}]socketchat[/b {BRAND_GOLD}] "
        f"[dim {BRAND_GREEN}]{'─' * line_len}[/dim {BRAND_GREEN}]"
    )


def _footer_md() -> str:
    return (
        f"[{BRAND_GOLD}]ESC[/] disconnect"
        "  ·  "
        f"[{BRAND_GOLD}]Ctrl+D[/] disconnect"
        "  ·  "
        f"[{BRAND_GOLD}]Ctrl+W[/] welcome"
    )


class ChatScreen(Screen):
    CONNECTION_INFO: list[tuple[str, str]] = [
        ("client",    "true"),
        ("server",    "false"),
        ("IP",        "192.168.1.42"),
        ("encrypted", "true"),
        ("port",      "5000"),
        ("time",      "14:22:03"),
    ]

    def __init__(
        self,
        connection_info: list[tuple[str, str]] | None = None,
        send_queue=None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.connection_info = (
            connection_info if connection_info is not None else self.CONNECTION_INFO
        )
        self.send_queue = send_queue

    CSS = f"""
    ChatScreen {{
        background: {BRAND_BG};
    }}

    #chat-header {{
        width: 100%;
        height: 2;
        color: {TEXT_SECONDARY};
        background: {BRAND_BG};
    }}

    #chat-body {{
        width: 100%;
        height: 1fr;
        margin: 0 2;
    }}

    #chat-body-inner {{
        width: 100%;
        height: 100%;
    }}

    #info-panel {{
        width: 26;
        min-width: 26;
        height: 100%;
        border: round {BRAND_GREEN};
        background: {PANEL_BG};
        padding: 1 2;
        color: {TEXT_PRIMARY};
        scrollbar-color: {GOLD_DIM};
        scrollbar-color-hover: {GOLD_DIM};
        scrollbar-color-active: {BRAND_GOLD};
        scrollbar-background: {BRAND_BG};
    }}

    #chat-side {{
        width: 1fr;
        height: 100%;
        layout: vertical;
        border: round {BRAND_GREEN};
        background: {PANEL_BG};
        padding: 0;
    }}

    #msg-scroll {{
        width: 100%;
        height: 1fr;
        padding: 1 2;
        scrollbar-size: 1 1;
        scrollbar-color: {GOLD_DIM};
        scrollbar-color-hover: {GOLD_DIM};
        scrollbar-color-active: {BRAND_GOLD};
        scrollbar-background: {PANEL_BG};
        scrollbar-background-hover: {PANEL_BG};
        scrollbar-background-active: {PANEL_BG};
    }}

    #msg-scroll Static {{
        width: 100%;
        color: {TEXT_PRIMARY};
        margin: 0 0 1 0;
    }}

    #msg-scroll .msg-sent {{
        text-align: right;
    }}

    #msg-scroll .msg-recv {{
        text-align: left;
    }}

    #msg-input {{
        width: 100%;
        height: 3;
        border: round {BRAND_GREEN};
        background: {INPUT_BG};
        color: {TEXT_PRIMARY};
    }}

    #msg-input:focus {{
        border: round {BRAND_GOLD};
    }}

    #msg-input > .input--placeholder {{
        color: {TEXT_META};
    }}

    #footer {{
        dock: bottom;
        width: 100%;
        height: 1;
        align: center middle;
        color: {TEXT_META};
    }}

    .timestamp {{
        color: {TEXT_META};
        text-style: dim;
    }}
    """

    BINDINGS = [
        ("escape", "disconnect", "Disconnect"),
        ("ctrl+d", "disconnect", "Disconnect"),
    ]

    def action_disconnect(self) -> None:
        self.app.show_welcome()

    def _append_message(self, sent: bool, text: str, stamp: str) -> None:
        md = _message_md(sent, text, stamp)
        scroll = self.query_one("#msg-scroll")
        scroll.mount(Static(md, classes="msg-sent" if sent else "msg-recv"))
        # Scroll after the new widget has been laid out, not before.
        self.call_after_refresh(scroll.scroll_end, animate=False)

    def show_message(self, text: str) -> None:
        self._append_message(False, text, time.strftime("%H:%M:%S"))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.input.value.strip()
        if not text:
            return
        stamp = time.strftime("%H:%M:%S")
        self._append_message(True, text, stamp)
        if self.send_queue is not None:
            try:
                self.send_queue.put(text)
            except Exception:
                pass
        event.input.value = ""
        event.input.cursor_position = 0
        event.input.focus()

    def compose(self) -> ComposeResult:
        yield Static(_header_md(), id="chat-header")
        with Vertical(id="chat-body"):
            with Horizontal(id="chat-body-inner"):
                yield Static(
                    _info_md(self.connection_info), id="info-panel"
                )
                with Vertical(id="chat-side"):
                    yield VerticalScroll(id="msg-scroll")
                    yield Input(
                        placeholder="Type a message...", id="msg-input"
                    )
        yield Static(_footer_md(), id="footer")


PREVIEW_MESSAGES: list[tuple[bool, str, str]] = [
    (True,  "Hey, are you on the same network?", "14:21:30"),
    (False, "Yes, just connected. Encrypted channel is live.", "14:21:33"),
    (True,  "Great. Sending the key exchange now.", "14:21:36"),
    (False, "Got it. Ready when you are.", "14:21:38"),
    (True,  "Transferring the file. Should be quick.", "14:22:01"),
    (False, "Receiving...", "14:22:03"),
    (True,  "Let me know once it's done.", "14:22:10"),
    (False, "Received. All looks good, thanks.", "14:22:14"),
]


class _PreviewApp(App):

    def on_mount(self) -> None:
        self.push_screen(ChatScreen())
        self.query_one("#msg-input", Input).focus()
        chat = self.screen
        for sent, text, stamp in PREVIEW_MESSAGES:
            chat._append_message(sent, text, stamp)


if __name__ == "__main__":
    _PreviewApp().run()