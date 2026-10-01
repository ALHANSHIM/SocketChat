import secrets as sc
import socket as sk
import struct as st
from threading import Thread, Event
from queue import Queue, Empty
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes


VERSION = b"SCHATv1"

def _recv_exact(x, n):
    buf = b""
    while len(buf) < n:
        chunk = x.recv(n - len(buf))
        if not chunk:
            raise OSError("closed")
        buf += chunk
    return buf


def send_msg(x, data):
    # send size first (4 bytes), then send the data
    # so the other side knows where one message ends
    size = len(data)
    x.sendall(st.pack("!I", size))
    x.sendall(data)


def recv_msg(x):
    
    size_bytes = _recv_exact(x, 4)
    size = st.unpack("!I", size_bytes)[0]
    data = _recv_exact(x, size)
    return data


class crypto:
    
    @staticmethod
    def aes_en(message):
        key = sc.token_bytes(16)
        nonce = sc.token_bytes(12)
        message = message.encode()
        lock = AESGCM(key)
        hash_message = nonce + lock.encrypt(nonce, message, None)
        return key, hash_message

    @staticmethod
    def aes_de(key, hash_message):
        lock = AESGCM(key)
        message = lock.decrypt(hash_message[:12], hash_message[12:], None)
        return message.decode("utf-8")

    @staticmethod
    def rsa_en(public_key, message):
        en_message = public_key.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return en_message

    @staticmethod
    def rsa_de(private_key, message):
        de_message = private_key.decrypt(
            message,
            padding.OAEP(

                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return de_message

    @staticmethod
    def hypierd(public_key, message):
        key, hashed_message = crypto.aes_en(message)
        hashed_public_key = crypto.rsa_en(public_key, key)
        return hashed_public_key, hashed_message



class recv_data:

    @staticmethod
    def recv_text_message(x, private_key, on_disconnect=None, on_message=None):
        while True:
            try:
                data = recv_msg(x)
            except OSError:
                if on_disconnect:
                    on_disconnect()
                break
            try:
                enc_key = data[:256]
                enc_message = data[256:]
                decrypted_aes_key = crypto.rsa_de(private_key, enc_key)
                de_msg = crypto.aes_de(decrypted_aes_key, enc_message)
                if on_message:
                    on_message(de_msg)
            except Exception:
                continue


            
class route:
    
    @staticmethod
    def server(queue_client_found, stop_server, client_addr=None, send_queue=None, on_message=None, on_disconnect=None, on_socket=None):
        while not stop_server.is_set():
            server_socket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
            server_socket.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
            port = 5000
            server_socket.bind(("", port))
            server_socket.listen(1)
            server_socket.settimeout(0.5)
            while not stop_server.is_set():
                try:
                    new_socket, addr = server_socket.accept()
                except sk.timeout:
                    continue
                except OSError:
                    break
                queue_client_found.put(addr)
                if client_addr == addr[0]:
                    try:
                        new_socket.sendall(VERSION)
                        if _recv_exact(new_socket, len(VERSION)) != VERSION:
                            raise OSError("version mismatch")
                    except OSError:
                        try:
                            new_socket.close()
                        except OSError:
                            pass
                        if on_disconnect is not None:
                            on_disconnect()
                        continue
                    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
                    public_key = private_key.public_key()
                    public_bytes = public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    )
                    try:
                        send_msg(new_socket, public_bytes)
                        recv_public_bytes = recv_msg(new_socket)
                        received_public_key = serialization.load_pem_public_key(recv_public_bytes)
                    except Exception:
                        try:
                            new_socket.close()
                        except OSError:
                            pass
                        if on_disconnect is not None:
                            on_disconnect()
                        continue
                    if on_socket is not None:
                        try:
                            on_socket(new_socket)
                        except Exception:
                            pass
                    if send_queue is None:
                        send_queue = Queue()
                    t1 = Thread(target=recv_data.recv_text_message, args=(new_socket, private_key, on_disconnect, on_message))
                    t1.daemon = True
                    t1.start()
                    while not stop_server.is_set():
                        try:
                            server_message = send_queue.get(timeout=0.5)
                        except Empty:
                            continue
                        try:
                            hashed_public_key, hashed_message = crypto.hypierd(received_public_key, server_message)
                            send_msg(new_socket, hashed_public_key + hashed_message)
                        except OSError:
                            break
                    try:
                        new_socket.close()
                    except OSError:
                        pass
                    try:
                        server_socket.close()
                    except OSError:
                        pass
                    return addr, True
                else:
                    try:
                        new_socket.close()
                    except OSError:
                        pass
                    continue
            try:
                server_socket.close()
            except OSError:
                pass








        
    @staticmethod
    def client(server_addr, port_num, send_queue=None, on_message=None, on_disconnect=None, on_connected=None, stop_client=None, on_socket=None):
        try:
            client_socket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
            client_socket.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
            client_socket.connect((server_addr, port_num))
        except OSError:
            if on_disconnect is not None:
                on_disconnect()
            return False
        try:
            if _recv_exact(client_socket, len(VERSION)) != VERSION:
                raise OSError("version mismatch")
            client_socket.sendall(VERSION)
        except OSError:
            try:
                client_socket.close()
            except OSError:
                pass
            if on_disconnect is not None:
                on_disconnect()
            return False
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        try:
            recv_public_bytes = recv_msg(client_socket)
            received_public_key = serialization.load_pem_public_key(recv_public_bytes)
            send_msg(client_socket, public_bytes)
        except Exception:
            try:
                client_socket.close()
            except OSError:
                pass
            if on_disconnect is not None:
                on_disconnect()
            return False
        if on_socket is not None:
            try:
                on_socket(client_socket)
            except Exception:
                pass
        if send_queue is None:
            send_queue = Queue()
        t1 = Thread(target=recv_data.recv_text_message, args=(client_socket, private_key, on_disconnect, on_message))
        t1.daemon = True
        t1.start()
        if on_connected is not None:
            on_connected()
        while stop_client is None or not stop_client.is_set():
            try:
                message = send_queue.get(timeout=0.5)
            except Empty:
                continue
            try:
                hashed_public_key, hashed_message = crypto.hypierd(received_public_key, message)
                send_msg(client_socket, hashed_public_key + hashed_message)
            except OSError:
                break
        try:
            client_socket.close()
        except OSError:
            pass
        if on_disconnect is not None:
            on_disconnect()
        return True

                
