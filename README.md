# SocketChat

A lightweight terminal-based chat application built with Python sockets and threading.

![version](https://img.shields.io/badge/version-1.0.0--alpha-blue)
![python](https://img.shields.io/badge/python-%3E%3D3.10-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![topic](https://img.shields.io/badge/topic-networking-orange)

## Overview

SocketChat is a simple client-server chat application written in pure Python, with no external dependencies. It was built as a hands-on project to explore how networking works under the hood — handling socket connections, sending and receiving data, and managing multiple simultaneous connections using threads.

## Why I Built This

I'm currently learning the fundamentals of computer networking and wanted to understand how data actually moves between machines. Rather than just reading about sockets, I built this project to get practical experience with the Python `socket` library and to learn how to handle concurrent connections using the `threading` module.

## Features

- Real-time, terminal-based messaging between a server and multiple clients
- Built using only Python's standard library (`socket`, `threading`)
- Simple, readable codebase — great for anyone learning network programming
- Two-file architecture for clarity: a server and a client

## How It Works

The project is split into two scripts:

| File | Description |
|------|--------------|
| `server.py` | Listens for incoming connections and handles sending/receiving messages |
| `client.py` | Connects to the server's IP address and lets the user send/receive messages |

Both scripts use the `threading` module so messages can be received in the background while the user is still able to type and send their own.

## Getting Started

### Requirements

- Python 3.10 or higher
- No external dependencies — uses only the standard library

### Installation

```bash
git clone https://github.com/ALHANSHIM/SocketChat.git
cd SocketChat
```

### Usage

**1. Start the server** (on the host machine):

```bash
python server.py
```

**2. Start the client** (on the same or a different machine on the network):

```bash
python client.py
```

> Make sure the client is configured with the correct server IP address before connecting.

## Project Status

This project is an early-stage prototype. The core functionality works, but it hasn't been hardened yet — unexpected input or unusual network conditions may cause issues. It's a learning project first, and a polished tool second. Feedback and suggestions are very welcome.

## Roadmap

- [ ] Improve error handling for dropped or unstable connections
- [ ] Add support for usernames and message history
- [ ] Add encryption for message privacy
- [ ] Write basic tests
- [ ] Package as an installable CLI tool

## Contributing

Contributions, issues, and suggestions are welcome. If you'd like to help improve SocketChat:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Open a pull request

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Author

**ALHANSHIM**
