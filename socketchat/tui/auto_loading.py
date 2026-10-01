from __future__ import annotations
import time
from threading import Event, Thread

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Static
from queue import Queue, Empty
from socketchat.startup import discover, my_ip
from socketchat.tui.chat import ChatScreen
from socketchat.tui.loading import LoadingRing

BRAND_BG      = "#0B0C0A"   
BRAND_GREEN   = "#02462E"    
BRAND_GOLD    = "#FEC700"   

TEXT_PRIMARY   = "#F1EDE2"  
TEXT_SECONDARY = "#9BA397"  
TEXT_META      = "#B9B17A" 

GREEN_TINT = "#4E9E7C"

GOLD_DIM = "#8A751A"


class ConfirmDialog(ModalScreen[bool]):

    CSS = f"""
    ConfirmDialog {{
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }}
    #confirm-box {{
        width: 60%;
        max-width: 50;
        height: auto;
        padding: 1 3;
        background: {BRAND_BG};
        layout: vertical;
    }}
    #confirm-question {{
        width: 100%;
        height: auto;
        color: {TEXT_PRIMARY};
        text-align: center;
        margin-bottom: 2;
    }}
    #confirm-actions {{
        width: 100%;
        height: auto;
        align: center middle;
    }}
    #confirm-actions Button {{
        width: auto;
        min-width: 10;
        margin: 0 1;
    }}
    """
    def __init__(self, question: str) -> None:
        super().__init__()
        self.question = question
    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-box"):
            yield Static(self.question, id="confirm-question")
            with Horizontal(id="confirm-actions"):
                yield Button("Accept", id="accept", variant="success")
                yield Button("Deny", id="deny", variant="error")

    def on_show(self) -> None:
        self.query_one("Button#deny").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "accept")


class PacketLog(Static):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entries: list[tuple[str, str, str, str, int]] = []

    def append(self, direction: str, addr: str, ptype: str, size: int) -> None:
        stamp = time.strftime("%H:%M:%S")
        self._entries.append((direction, stamp, addr, ptype, size))
        self.update("\n".join(self._rows()))
        try:
            self.scroll_end(animate=False)
        except Exception:
            pass

    def _max_data_rows(self) -> int:
       
        box = self.parent
        if box is not None:
            available = box.content_size.height
            if available > 0:
                return max(1, available - 2)
        return 1

    def _rows(self) -> list[str]:
        rows = [
            f"[b][{BRAND_GOLD}] SENT  [/][/]   "
            f"[b][{GREEN_TINT}]RECEIVED[/][/]",
            f"[{TEXT_META}]DIR   TIME      ADDR              TYPE    SIZE[/]",
        ]
        for direction, stamp, addr, ptype, size in self._entries[-self._max_data_rows():]:
            color = BRAND_GOLD if direction == "SEND" else GREEN_TINT
            label = "SEND" if direction == "SEND" else "RECV"
            rows.append(
                f"[{color}]{label:^4}[/]  {stamp}  "
                f"[{TEXT_PRIMARY}]{addr:<16} {ptype:<6} {size:>5}[/]"
            )
        return rows


def _ip_num(ip):
    try:
        return tuple(int(part) for part in ip.split("."))
    except Exception:
        return (0,)


class AutoLoadingScreen(Screen):
    CSS = f"""
    AutoLoadingScreen {{
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
    #packet-row {{
        width: 100%;
        height: auto;
        align: center middle;
    }}
    #packet-box {{
        width: 53;
        height: 16;
        border: round {BRAND_GREEN};
        background: #0D0F0C;
        padding: 1 2;
        scrollbar-gutter: stable;
        scrollbar-color: {GOLD_DIM};
        scrollbar-color-hover: {GOLD_DIM};
        scrollbar-color-active: {BRAND_GOLD};
        scrollbar-background: #0B0C0A;
        scrollbar-background-hover: #0B0C0A;
        scrollbar-background-active: #0B0C0A;
    }}
    #packet-box:focus, #packet-box:focus-within {{
        border-top: heavy {GOLD_DIM};
    }}
    #packet-box PacketLog {{
        width: 100%;
        color: {TEXT_PRIMARY};
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
        ("ctrl+a", "toggle_auto", "Toggle auto"),
        ("q", "quit", "Quit"),
    ]
    AUTO = True
    START_DISCOVERY = True
    def _start_discovery(self) -> None:
       
        app = self.app
        log = self.query_one("#log", PacketLog)

        def on_packet(direction, addr, ptype, size) -> None:
            app.call_from_thread(log.append, direction, addr, ptype, size)

        def on_connected(connection_info) -> None:
            app.call_from_thread(self.on_discovered, connection_info)

        def on_broadcast(connection_info) -> None:
            app.call_from_thread(self.on_broadcast_found, connection_info)

        self._sender_event = Event()
        self._listener_event = Event()
        self._sender_event.set()
        self._listener_event.set()
        Thread(
            target=discover.sender,
            args=[self._sender_event],
            kwargs={"on_packet": on_packet},
            daemon=True,
        ).start()
        Thread(
            target=discover.listener,
            args=[self._listener_event, None],
            kwargs={"on_packet": on_packet, "on_connected": on_connected, "on_broadcast": on_broadcast},
            daemon=True,
        ).start()

    def on_mount(self) -> None:
        discover.current_packet_type = 1
        discover.IP_address = ""
        self._ignored = set()
        self._committed = False
        self._popup_open = False
        self._peer_ip = ""
        self._dialling = False
        self._my_ip = my_ip()
        try:
            self.app.stop_hearing()
        except Exception:
            pass
        if self.START_DISCOVERY:
            self._start_discovery()

    def on_unmount(self) -> None:
        try:
            self._sender_event.clear()
        except AttributeError:
            pass
        try:
            self._listener_event.clear()
        except AttributeError:
            pass

    def action_toggle_auto(self) -> None:
        self.AUTO = not self.AUTO
        self.log(f"Auto mode {'ON' if self.AUTO else 'OFF'}")

    def compose(self) -> ComposeResult:
        with Center(id="center"):
            with Vertical(id="loader-wrap"):
                with Center():
                    yield LoadingRing()
            yield Static("Discovering devices...", id="status")
            with Horizontal(id="packet-row"):
                with VerticalScroll(id="packet-box"):
                    yield PacketLog(id="log")
        yield Static(
            f"[{BRAND_GOLD}]ESC[/] exit"
            "  ·  "
            f"[{BRAND_GOLD}]Ctrl+A[/] auto"
            "  ·  "
            f"[{BRAND_GOLD}]Ctrl+W[/] welcome",
            id="footer",
        )

    def ask_popup(self, ip, get_result):
        self.app.push_screen(
            ConfirmDialog(f"Do you accept connecting with {ip}?"),
            get_result,
        )

    def on_broadcast_found(self, connection_info):
        ip = connection_info["IP"]
        if ip in self._ignored or self._committed or self._popup_open:
            return
        self._popup_open = True
        self.ask_popup(ip, lambda result: self._decide_broadcast(ip, result))

    def on_discovered(self, connection_info):
        ip, port = connection_info["IP"], connection_info["port"]
        if ip in self._ignored or self._popup_open:
            return
        if self._committed:
            # we already serve someone, this unicast means the other device
            # accepted too and both are servers, the smaller ip dials
            if ip == self._peer_ip and not self._dialling and _ip_num(self._my_ip) < _ip_num(ip):
                self._dialling = True
                self.app._dial_device(ip, port)
            return
        self._popup_open = True
        self.ask_popup(ip, lambda result: self._decide_unicast(ip, port, result))

    def _decide_broadcast(self, ip, result):
        self._popup_open = False
        if not result:
            self._ignored.add(ip)
            self.notify(f"Ignoring {ip} for this session", severity="warning")
            return
        self._committed = True
        self.query_one("#status", Static).update(f"Connecting to {ip}...")
        send_queue = self.app.start_server(ip, None, self.app._post_chat_message, self.app._on_chat_closed)
        self._peer_ip = ip
        discover.IP_address = ip
        discover.current_packet_type = 2
        Thread(target=self._wait_for_peer, args=(ip, send_queue), daemon=True).start()

    def _decide_unicast(self, ip, port, result):
        self._popup_open = False
        if not result:
            self._ignored.add(ip)
            self.notify(f"Ignoring {ip} for this session", severity="warning")
            return
        self._committed = True
        self.app._dial_device(ip, port)

    def _wait_for_peer(self, ip, send_queue):
        while self._listener_event.is_set():
            try:
                addr = self.app._server_queue.get(timeout=0.5)
            except Empty:
                continue
            if addr[0] == ip:
                self.app._open_chat(ip, 5000, send_queue, True)
                break

if __name__ == "__main__":
    from window import SocketChatApp

    SocketChatApp().run()
