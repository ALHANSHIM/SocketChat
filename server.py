import socket as sk 
from threading import Thread

host = sk.gethostname()
port = 5000

s = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
s.bind((host, port))
s.listen(5)

print("the server is ready for cleints......")
# tell here the server is ready to run

def rescev_message(new):  # the recv function
    while True:
        try:
            data = new.recv(1024)
            if not data:
                print("the client is disconnected")
                break

            client_message = data.decode('utf-8')
            print(f'client: {client_message}\n')
            print(":>", end="", flush=True)

        except Exception:
            break

while True:
    new_socket, addr = s.accept()

    print(f" the server has accept a clinet with IP='{addr[0]}' and the clint using port='{addr[1]}'. ")

    code = int(input("Enter 1 to start chating or Enter 2 to exit. "))

    if code == 1:
        t1 = Thread(target=rescev_message, args=[new_socket])
        t1.start()

        while True:
            print("Enter your massage after :> the press Enter. if you want to exit just type 'exit--'")

            server_message = input(":>")

            if server_message == "exit--":
                new_socket.close()
                break
            else:
                new_socket.send(server_message.encode("utf-8"))
