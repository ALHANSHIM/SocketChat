
import time
from textual.app import App
from textual.binding import Binding
from tui.auto_loading import ConfirmDialog
from tui.chat import ChatScreen
from tui.ip_loading import IpLoadingScreen
from tui.welcome_page import WelcomeScreen
from threading import Thread, Event
from queue import Queue
from functions import route
from core import runs_hearing
from startup import P2_sender
class SocketChatApp(App):
    TITLE = "SocketChat"
    MIN_SIZE = (60, 24)
    START_HEARING = True

    BINDINGS = [
        Binding("ctrl+w", "go_welcome", "Welcome", priority=True),
    ]

    def on_mount(self): 
        self.push_screen(WelcomeScreen())
        if self.START_HEARING:
            self.start_hearing()

    async def action_quit(self): 
        self._stop_all_services()
        await super().action_quit()

    def _stop_all_services(self):
        self.stop_hearing()
        self.stop_server()
        self.stop_client()
        self.close_chat()

    def action_go_welcome(self): 
        if isinstance(self.screen, WelcomeScreen):
            return
        if isinstance(self.screen, ConfirmDialog):
            self.screen.dismiss(False)
            return
        self.show_welcome()

    def run_pi_loading(self, ip): 
       self.push_screen(IpLoadingScreen(ip=ip))

    def show_welcome(self): 
        self.stop_server()
        self.stop_client()
        self.close_chat()
        self.switch_screen(WelcomeScreen())
        if self.START_HEARING:
            try:
                self.start_hearing()
            except Exception:
                pass

    def _save_socket(self, x):
        self._chat_socket = x

    def stop_server(self):
        try:
            self._server_stop.set()
        except Exception:
            pass

    def stop_client(self):
        try:
            self._client_stop.set()
        except Exception:
            pass

    def close_chat(self):
        try:
            self._chat_socket.close()
        except Exception:
            pass

    def start_server(self, ip, send_queue=None, on_message=None, on_disconnect=None):
        if send_queue is None:
            send_queue = Queue()
        try:
            self._server_stop.set()
        except Exception:
            pass
        self.close_chat()
        self._server_stop = Event()
        self._server_queue = Queue()
        self._chat_socket = None
        Thread(target=route.server, args=(self._server_queue, self._server_stop, ip, send_queue, on_message, on_disconnect, self._save_socket), daemon=True).start()
        return send_queue

    def start_hearing(self): 
        try:
            if self._hearing_thread.is_alive():
                return
        except AttributeError:
            pass
        self._hearing_ignored = set() 
        self._hearing_popup_open = False 
        self._hearing_stop = Event()
        self._hearing_thread = Thread(target=runs_hearing, kwargs={
            "on_device_found": self.on_device_found,
            "stop_event": self._hearing_stop,
        }, daemon=True)
        self._hearing_thread.start()

    def stop_hearing(self):
        try:
            self._hearing_stop.set()
        except AttributeError:
            pass

    def on_device_found(self, ip, port, result_queue):
        self.call_from_thread(self.ask_popup, ip, port, result_queue)

    def ask_popup(self, ip, port, result_queue):
        try:
            if self._hearing_stop.is_set():
                result_queue.put(False)
                return
        except Exception:
            pass
        if ip in getattr(self, "_hearing_ignored", set()) or getattr(self, "_hearing_popup_open", False):
            result_queue.put(False)
            return
        self._hearing_popup_open = True
        self.push_screen(
            ConfirmDialog(f"Do you accept connecting with {ip}?"),
            lambda result: self._finish_decision(ip, port, result_queue, result),
        )

    def _finish_decision(self, ip, port, result_queue, result):
        self._hearing_popup_open = False
        result_queue.put(result)
        if not result:
            try:
                self._hearing_ignored.add(ip)
            except AttributeError:
                self._hearing_ignored = {ip}
            self.notify("Connection denied — still listening for devices", severity="warning")
            return
        if port is None:
            Thread(target=self._serve_device, args=(ip,), daemon=True).start()
            return
        self._dial_device(ip, port)

    def _serve_device(self, ip):
        self.notify(f"Connecting to {ip}...")
        send_queue = self.start_server(ip, None, self._post_chat_message, self._on_chat_closed)
        sender_event = Event()
        sender_event.set()
        Thread(target=P2_sender, kwargs={"p2_sender_event": sender_event, "ip": ip}, daemon=True).start()
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                addr = self._server_queue.get(timeout=0.5)
            except Exception:
                continue
            if addr[0] == ip:
                sender_event.clear()
                self._open_chat(ip, 5000, send_queue, True)
                return
        sender_event.clear()
        try:
            self._server_stop.set()
        except Exception:
            pass
        try:
            self.call_from_thread(self.notify, "Nobody connected in 60s")
            self.call_from_thread(self.show_welcome)
        except Exception:
            pass

    def _dial_device(self, ip, port):
        self.notify(f"Connecting to {ip}...")
        send_queue = Queue()
        try:
            self._client_stop.set()
        except Exception:
            pass
        self.close_chat()
        self._client_stop = Event()
        self._chat_socket = None
        Thread(target=route.client, args=(ip, port, send_queue, self._post_chat_message, self._on_chat_closed, lambda: self._open_chat(ip, port, send_queue, False), self._client_stop, self._save_socket), daemon=True).start()

    def _open_chat(self, ip, port, send_queue, is_server):
        self.stop_hearing()
        info = [("server" if is_server else "client", "true"), ("IP", ip), ("port", str(port)), ("time", time.strftime("%H:%M:%S"))]
        chat = ChatScreen(connection_info=info, send_queue=send_queue)
        self._chat_screen = chat
        self.call_from_thread(self.switch_screen, chat)

    def _post_chat_message(self, text):
        try:
            chat = self._chat_screen
        except AttributeError:
            return
        try:
            self.call_from_thread(chat.show_message, text)
        except Exception:
            pass

    def _on_chat_closed(self):
        try:
            self.call_from_thread(self.notify, "Device disconnected")
            self.call_from_thread(self.show_welcome)
        except Exception:
            pass


def run_app():
    SocketChatApp().run()


if __name__ == "__main__":
    run_app()