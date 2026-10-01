import struct as st
import socket as sk
from  threading import Thread, Event
import time
from queue import Queue


class packet:
    def broad_packet():
        packet_format = "!IB"
        magic_num = 35345
        command_id = 1
        packet = st.pack(packet_format, magic_num, command_id)
        return packet
  
    def unicast_packet(port=5000):
        packet_format = "!IBH"
        magic_num = 35345
        command_id = 2 
        tcp_port_num = port
        packet = st.pack(packet_format, magic_num, command_id, tcp_port_num)
        return packet



def own_ips():
    my_ips = set()
    my_ips.add("127.0.0.1")
    my_ips.add("0.0.0.0")

    try:
        my_name = sk.gethostname()
        __, __, found_ips = sk.gethostbyname_ex(my_name)
        for ip in found_ips:
            my_ips.add(ip)
    except Exception:
        pass

  
    try:
        temp_socket = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        temp_socket.connect(("8.8.8.8", 80))
        my_ips.add(temp_socket.getsockname()[0])
        temp_socket.close()
    except Exception:
        pass

    return list(my_ips)


def my_ip():
    try:
        s = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "0.0.0.0"


def broadcast_ips():
   
    my_ips = own_ips()
    broads = set()
    for ip in my_ips:
        if ip == "127.0.0.1" or ip == "0.0.0.0":
            continue
        try:
            parts = ip.split(".")
            if len(parts) == 4:
                broad = parts[0] + "." + parts[1] + "." + parts[2] + ".255"
                broads.add(broad)
        except Exception:
            pass
    if len(broads) == 0:
        broads.add("255.255.255.255")
    return list(broads)


class discover: 
    current_packet_type = 1
    IP_address = ""
    @staticmethod
    def listener(listene_event, packet_queue=None, on_packet=None, on_connected=None, on_broadcast=None):

        while True:
            listene_event.wait()
            broad_format = "!IB"
            un_format = "!IBH"
            magic_num = 35345

            lis_socket = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
            lis_socket.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
            lis_socket.settimeout(0.5)
            lis_socket.bind(("0.0.0.0", 50005))
            my_ips = own_ips()
            while listene_event.is_set():
                try:
                    data, addr = lis_socket.recvfrom(1024)
                except sk.timeout:
                    continue
                except OSError:
                    break
                ip, src_port = addr
                if ip in my_ips:
                    continue
                if len(data) == 5:
                    try:
                        magic_number, command_id = st.unpack(broad_format, data)
                    except st.error:
                        continue
                    if magic_number == magic_num:
                        if on_packet is not None:
                            on_packet("RECV", ip, "BROAD", len(data))
                        if on_broadcast is not None:
                            on_broadcast({"IP": ip})

                elif len(data) == 7:
                    try:
                        magic_number, command_id, port_num = st.unpack(un_format, data)
                    except st.error:
                        continue
                    if magic_number == magic_num:
                        if on_packet is not None:
                            on_packet("RECV", ip, "UNICAST", len(data))
                        if on_connected is not None:
                            on_connected({"IP": ip, "port": port_num})
                else:
                    print(" ")
            try:
                lis_socket.close()
            except OSError:
                pass


    
    @staticmethod
    def sender(sender_event, on_packet=None):
        while True:
            sender_event.wait()   
            if discover.current_packet_type == 1:
                send_socket = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
                send_socket.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
                send_socket.setsockopt(sk.SOL_SOCKET, sk.SO_BROADCAST, 1)
                packet1 = packet.broad_packet()
                times = 5
                broads = broadcast_ips()
                while sender_event.is_set() and discover.current_packet_type == 1:
                    for broad_ip in broads:
                        send_socket.sendto(packet1, (broad_ip, 50005))
                        if on_packet is not None:
                            on_packet("SEND", broad_ip, "BROAD", len(packet1))
                    if times > 0:
                        time.sleep(0.3)
                        times -= 1
                    else:
                        time.sleep(1)
                send_socket.close()

            else:
                send_socket = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
                send_socket.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
                packet2 = packet.unicast_packet()
                while sender_event.is_set() and discover.current_packet_type == 2:
                    send_socket.sendto(packet2, (discover.IP_address, 50005))
                    if on_packet is not None:
                        on_packet("SEND", discover.IP_address, "UNICAST", len(packet2))
                    time.sleep(1)
                send_socket.close()
    
   
def P2_sender(p2_sender_event, ip):
    send_socket = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
    send_socket.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
    packet2 = packet.unicast_packet()
    while True:
        p2_sender_event.wait()
        send_socket.sendto(packet2, (ip, 50005))
        time.sleep(1)








def auto_listener(request_queue, stop_event=None): 
    un_format = "!IBH"
    broad_format = "!IB"
    magic_num = 35345
    try:
        lis_socket = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        lis_socket.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
        lis_socket.settimeout(0.5)
        lis_socket.bind(("", 50005))
    except OSError:
        lis_socket = None
    my_ips = own_ips()
    while stop_event is None or not stop_event.is_set():
        if lis_socket is None:
            if stop_event is None:
                time.sleep(0.5)
            elif stop_event.wait(0.5):
                break
            continue
        try:
            data, addr = lis_socket.recvfrom(1024)
        except sk.timeout:
            continue
        except OSError:
            break
        ip, src_port = addr
        if ip in my_ips:
            continue
        if len(data) == 5:
           
            try:
                magic_number, command_id = st.unpack(broad_format, data)
            except st.error:
                continue
            if magic_number == magic_num:
                try:
                    request_queue.put((ip, None))
                except Exception:
                    pass
        elif len(data) == 7:
            try:
                magic_number, command_id, port_num = st.unpack(un_format, data)
            except st.error:
                continue
            if magic_number == magic_num:
                try:
                    request_queue.put((ip, port_num))
                except Exception:
                    pass
    try:
        if lis_socket is not None:
            lis_socket.close()
    except Exception:
        pass



