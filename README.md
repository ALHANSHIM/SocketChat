# SocketChat

![Latest Version](https://img.shields.io/badge/version-v1.0.0--alpha-brightgreen)
![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)
![Topic](https://img.shields.io/badge/topic-networking-orange)

Hey there! This is SocketChat, a simple terminal-based chat application built with Python. 

### Why I built this
I'm currently diving into Python and wanted to understand how networking works under the hood. So, I built this project to get hands-on experience with the `socket` library and learn how to handle data transfers and multiple threads. 

### Current Status & Future Plans
Right now, this is just a super early prototype. It’s basic, and I haven't done any deep error handling yet, so things might crash if inputs are unexpected. I'm treating this as a starting point, and I'll definitely be upgrading it, squashing bugs, and adding better features in the future as I learn more.

---

## How it works

The project is split into two files:
1. `server.py`: Listens for connections and handles sending/receiving messages on the server side.
2. `client.py`: Connects to the server's IP address and allows the user to chat.

Both scripts use threads (`threading` module) so you can receive incoming messages in the background while typing your own.

## How to run it

1. **Start the Server**
   Run the server script first on the host machine:
   ```bash
   python server.py
