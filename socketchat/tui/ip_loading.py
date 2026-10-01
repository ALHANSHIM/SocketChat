from __future__ import annotations

import time
from threading import Event, Thread

from textual.app import App, ComposeResult
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Static

from socketchat.connecting import start_ip_connecting
from socketchat.tui.chat import ChatScreen
from socketchat.tui.loading import LoadingRing


BRAND_BG      = "#0B0C0A"
BRAND_GREEN   = "#02462E"
BRAND_GOLD    = "#FEC700"

TEXT_PRIMARY   = "#F1EDE2"
TEXT_SECONDARY = "#9BA397"
TEXT_META      = "#B9B17A"


class IpLoadingScreen(Screen):
    def __init__(self, ip: str = "", *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.ip = ip

    CSS = f"""
    IpLoadingScreen {{
        background: {BRAND_BG};
        align: center middle;
    }}

    #center {{
        width: 100%;
        max-width: 84;
        height: auto;
        layout: vertical;
    }}

    #loader-wrap {{
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 2;
        margin-bottom: 2;
    }}
    #loader-wrap LoadingRing {{
        color: {BRAND_GOLD};
    }}

    #status {{
        width: 100%;
        height: auto;
        color: {TEXT_SECONDARY};
        content-align: center middle;
        text-align: center;
        margin-bottom: 4;
    }}

    #footer {{
        dock: bottom;
        width: 100%;
        height: 1;
        align: center middle;
        color: {TEXT_META};
    }}
    """

    BINDINGS = [
        ("escape", "quit", "Exit"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Center(id="center"):
            with Vertical(id="loader-wrap"):
                with Center():
                    yield LoadingRing()
            yield Static(f"Connecting to {self.ip}...", id="status")
        yield Static(
            f"[{BRAND_GOLD}]ESC[/] exit"
            "  ·  "
            f"[{BRAND_GOLD}]Ctrl+W[/] welcome",
            id="footer",
        )

    def on_mount(self) -> None:
        # Capture the app while this screen is still mounted. After
        # _on_connected() calls switch_screen(), this screen is unmounted and
        # self.app raises NoActiveAppError in network threads — which the
        # callbacks below swallow, silently dropping every received message.
        self._app_ref = self.app
        self._connecting_stop = Event()
        self._connecting_stop.set()
        try:
            self._app_ref.stop_hearing()
        except Exception:
            pass
        Thread(target=start_ip_connecting, kwargs={
            "app": self._app_ref,
            "ip": self.ip,
            "connecting_evnt": self._connecting_stop,
            "timeout": 30,
            "on_message": self._on_net_message,
            "on_disconnect": self._on_net_closed,
            "on_connected": self._on_connected,
            "on_timeout": self._on_timeout,
        }, daemon=True).start()

    def on_unmount(self) -> None:
        try:
            self._connecting_stop.clear()
        except AttributeError:
            pass

    def _on_connected(self, send_queue, addr) -> None:
        app = self._app_ref
        info = [("server", "true"), ("IP", addr[0]), ("port", str(addr[1])), ("time", time.strftime("%H:%M:%S"))]
        chat = ChatScreen(connection_info=info, send_queue=send_queue)
        self._chat = chat
        app._chat_screen = chat
        app.call_from_thread(app.switch_screen, chat)

    def _on_timeout(self) -> None:
        try:
            self._app_ref.call_from_thread(self._app_ref.notify, "Nobody connected in 30s")
            self._app_ref.call_from_thread(self._app_ref.show_welcome)
        except Exception:
            pass

    def _on_net_message(self, text: str) -> None:
        try:
            chat = self._chat
        except AttributeError:
            return
        try:
            self._app_ref.call_from_thread(chat.show_message, text)
        except Exception:
            pass

    def _on_net_closed(self) -> None:
        try:
            self._app_ref.call_from_thread(self._app_ref.notify, "Device disconnected")
        except Exception:
            pass


class _PreviewApp(App):

    def on_mount(self) -> None:
        self.push_screen(IpLoadingScreen(ip="192.168.1.42"))


if __name__ == "__main__":
    _PreviewApp().run()