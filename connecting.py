import socket as sk
import time
from threading import Thread, Event
from queue import Queue, Empty
from startup import P2_sender



def sending_unicast_packet(ip, p2_sender_event):
    p2_sender_event.set()
    Thread(target=P2_sender, kwargs={
        "ip": ip,
        "p2_sender_event": p2_sender_event
    }, daemon=True).start()



def start_ip_connecting(app, ip, connecting_evnt=None, timeout=30, on_message=None, on_disconnect=None, on_connected=None, on_timeout=None):
    """this function will eun when the user enter an ip to connect with 
     what is dose
       1. starting the server 
       2. sending uincast packets to the ip so it now what divce wants to connect with 
       3. if the divce connect with the server in (timeout) sec the on_connected runs,
          if not the on_timeout runs and the user comes back to the welcome page 

     app is the already-running SocketChatApp instance. It must be passed in
     rather than constructed here, so the server state started below lives on
     the same object the UI reads from.""" 
    if connecting_evnt is None:
        connecting_evnt = Event()
        connecting_evnt.set()
    send_queue = Queue()
    app.start_server(ip, send_queue, on_message, on_disconnect)
    p2_sender_event = Event()
    sending_unicast_packet(ip, p2_sender_event)
    addr = None
    deadline = time.monotonic() + timeout
    while connecting_evnt.is_set() and time.monotonic() < deadline:
        try:
            addr = app._server_queue.get(timeout=0.5)
        except Empty:
            continue
        if addr[0] == ip:
            break
        addr = None
    p2_sender_event.clear()
    if addr is not None:
        if on_connected is not None:
            on_connected(send_queue, addr)
        return True
    try:
        app._server_stop.set()
    except Exception:
        pass
    if on_timeout is not None and connecting_evnt.is_set():
        on_timeout()
    return False
