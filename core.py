from threading import Thread, Event
from queue import Queue, Empty
from startup import auto_listener



def runs_hearing(on_device_found=None, stop_event=None):
    if stop_event is None:
        stop_event = Event()
    request_queue = Queue()
    Thread(target=auto_listener, args=(request_queue, stop_event), daemon=True).start()
    ignored = set()
    while not stop_event.is_set():
        try:
            ip, port = request_queue.get(timeout=0.5)
        except Empty:
            continue
        if stop_event.is_set():
            break
        if ip in ignored:
            continue
        if on_device_found is None:
            continue
        result_queue = Queue()
        try:
            on_device_found(ip, port, result_queue)
        except Exception:
            continue
        confirmed = None
        while not stop_event.is_set():
            try:
                confirmed = result_queue.get(timeout=0.5)
                break
            except Empty:
                continue
        if stop_event.is_set():
            break
        if confirmed:
            stop_event.set()
            break
        ignored.add(ip)




def parse_command(raw_input):
    if not raw_input.startswith("/"):

        return None
    command = raw_input[1:].strip()
    parts = command.split()
    verb = parts[0].lower() if parts else ""
    if verb == "auto":
        return {"verb": "auto"}
    elif verb == "ip":
        ip = parts[1] if len(parts) > 1 else ""
        return {"verb": "ip", "args": [ip]}
    return None


if __name__ == "__main__":
    from window import SocketChatApp
    SocketChatApp().run()

