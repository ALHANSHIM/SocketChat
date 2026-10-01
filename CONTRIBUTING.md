# Contributing to SocketChat

Thanks for visiting. I created SocketChat as a simple terminal chat for a single LAN, and I try to keep the codebase short so that you can read it in an evening. You can test out most things with two machines on WiFi.

## How to run it

```bash
git clone https://github.com/ALHANSHIM/SocketChat.git
cd SocketChat
```

```bash
pip install -e .
```
```bash
schat
```

> [!NOTE]
> On Linux, if pip complains about `externally-managed-environment`, make a venv first, then install again.

Try `/auto` to find peers, or `/ip 192.168.x.x` to connect directly.

## Sending a change

Nothing strict here. If you want to help, this is all it takes:

**1. Fork the repo and fix or add something**
```bash
git checkout -b fix-something
```
Need some ideas? checkout the  help wanted section below and choose one.

**2. Test it on your LAN**
Run `schat` on two devices and make sure `/auto` and `/ip` still work.

**3. Open a pull request**
One fix per request. Tell me what you tried and paste any error you saw. Your OS and Python version help too.

## Help wanted

If you want a place to start, these would help the most:

- **Custom connection port.** Currently, the chat always operates over TCP port 5000. This particular post deals only with the TCP socket. I think it should be really easy to configure by command line `schat --port 5001`, or even TUI page setting.
- **Send files and images.** Right now, Socketchat is capable of sending text messages only. The addition of file and picture transmission capabilities would be really nice.
- **Fix the bugs** It is my first project , so I'm sure that I have overlooked some bugs. Feel free to run it and test it out and tell me anything I should know – anything that can help me will be of immense value. Simple fixes are just as important as new features.

***It is my very first project, and I would honestly appreciate any suggestions or criticism that will help me improve my performance in any way.***
