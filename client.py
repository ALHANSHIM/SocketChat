import socket as sk 
from threading import Thread
host = sk.gethostname()
port = 5000

s = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
s.connect((host, port))
def recv_message(x):
  while True:
    try:
      data = x.recv(1024)
      if not data:
        print("the server is disconnected")
        break
      else:
        
        msg = data.decode("utf-8")
        print(f"server: {msg}\n")
        print(":>", end="", flush=True)
    except Exception:
      break    
t1 = Thread(target=recv_message, args=[s])

while True:

  t1 = Thread(target=recv_message, args=[s])
  
  code = int(input("Enter 1 to start chating or Enter 2 to exit. "))
  if code == 1:
    print("to exit from the chat type --exit")
    t1.start()
    while True:
      print("Enter your massage after :> the press Enter. if you want to exit just type '--exit'")

      message = input("t:>")
      if message == "--exit":
        s.close()
        break
    
      else:
        s.send(message.encode('utf-8'))
    break
