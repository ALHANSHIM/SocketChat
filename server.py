import socket as sk
from threading import Thread 

host = sk.gethostname()
port = 5000

s = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
s.bind((host, port))
s.listen(5)
print("the server is ready for clients......")

# دالة الاستقبال لكل عميل في خيط منفصل
def rescev_message(new):
    while True:
        try:  
            data = new.recv(1024)
            if not data:
                print("\nthe client is disconnected")
                break
            client_message = data.decode('utf-8')
            print(f'\nclient: {client_message}')
            print(":>", end="", flush=True) 
        except Exception:
             break

while True:
    new_socket, addr = s.accept()
    print(f" the server has accepted a client with IP='{addr[0]}' and port='{addr[1]}'. ")
    code = int(input("Enter 1 to start chatting or Enter 2 to exit. "))
    if code == 1:
        t1 = Thread(target=rescev_message, args=[new_socket])
        t1.start()
        while True:
            print("Enter your message after :> then press Enter. If you want to exit just type 'exit--'")
            server_message = input(":>")
            if server_message == "exit--":
                new_socket.close()
                break
            else:
                new_socket.send(server_message.encode("utf-8"))
