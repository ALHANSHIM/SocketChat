import socket as sk
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal
from textual.screen import Screen
from textual.widgets import Static, Label, Input
from socketchat.tui.auto_loading import AutoLoadingScreen
from socketchat.tui.ip_loading import IpLoadingScreen
from socketchat.core import parse_command


BRAND_BG     = "#0B0C0A"
BRAND_GREEN  = "#02462E"
BRAND_GOLD   = "#FEC700"

TEXT_PRIMARY   = "#F1EDE2"
TEXT_SECONDARY = "#9BA397"
TEXT_META      = "#B9B17A"


LOGO = """\
 █▀▀ █▀█ █▀▀ █ █ █▀▀ ▀█▀ █▀▀ █ █ █▀█ ▀█▀
 ▀▀█ █ █ █   █▀▄ █▀▀  █  █   █▀█ █▀█  █
 ▀▀▀ ▀▀▀ ▀▀▀ ▀ ▀ ▀▀▀  ▀  ▀▀▀ ▀ ▀ ▀ ▀  ▀"""

HEADLINE = "Welcome to SocketChat"
SUBTEXT = (
    "Make sure your network allows UDP broadcast for auto-discovery.\n"
    "Type a command below to get started."
)

LINK = "https://github.com/alhanshim/socketchat"

COMMANDS_HINT = (
    f"[{BRAND_GOLD}]/ip 192.168.1.5[/]  connect directly to a device\n"
    f"[{BRAND_GOLD}]/auto[/]             find devices on your network"
)




class WelcomeScreen(Screen):
    CSS = f"""
    WelcomeScreen {{
        background: {BRAND_BG};
        align: center middle;
    }}

    #center {{
        width: 100%;
        max-width: 72;
        height: auto;
        layout: vertical;
    }}

   
    #logo {{
        width: 100%;
        height: auto;
        color: {BRAND_GOLD};
        text-style: bold;
        content-align: center middle;
        text-align: center;
        margin-bottom: 2;
    }}

    #headline {{
        width: 100%;
        height: auto;
        color: {TEXT_PRIMARY};
        text-style: bold;
        content-align: center middle;
        text-align: center;
        margin-top: 2;
        margin-bottom: 1;
    }}

    #subtext {{
        width: 100%;
        height: auto;
        color: {TEXT_SECONDARY};
        content-align: center middle;
        text-align: center;
        margin-bottom: 1;
    }}

    #link {{
        width: 100%;
        height: auto;
        color: {TEXT_META};
        content-align: center middle;
        text-align: center;
        margin-bottom: 4;
    }}

    #commands {{
        width: 100%;
        height: auto;
        color: {TEXT_SECONDARY};
        content-align: center middle;
        text-align: center;
        margin-top: 2;
    }}

    #input-row {{
        width: 100%;
        height: auto;
        align: center middle;
    }}

    #cmd-input {{
        width: 60%;
        height: 3;
        border: round {BRAND_GREEN};
        background: #101310;
        color: {TEXT_PRIMARY};
    }}

    #cmd-input:focus {{
        border: round {BRAND_GOLD};
    }}

    #cmd-input > .input--placeholder {{
        color: {TEXT_META};
    }}

    #footer {{
        dock: bottom;
        width: 100%;
        height: 1;
        align: center middle;
        color: {TEXT_META};
    }}
    """



    BINDINGS = [
        ("escape", "quit", "Exit"),
        Binding("ctrl+a", "toggle_auto", "Toggle auto", priority=True),
        ("q", "quit", "Quit"),
    ]

    AUTO = False

    def action_toggle_auto(self):
        self.AUTO = not self.AUTO
        self.log(f"Auto mode {'ON' if self.AUTO else 'OFF'}")
        if self.AUTO:
            self.app.switch_screen(AutoLoadingScreen())





    def compose(self):
        with Center(id="center"):
            yield Static(LOGO, id="logo")
            yield Label(HEADLINE, id="headline")
            yield Label(SUBTEXT, id="subtext")
            yield Static(LINK, id="link")
            with Horizontal(id="input-row"):
                yield Input(value="/", id="cmd-input")
            yield Static(COMMANDS_HINT, id="commands")
        yield Static(
            f"[{BRAND_GOLD}]Ctrl+Q[/] exit"
            "  ·  "
            f"[{BRAND_GOLD}]Ctrl+A[/] auto",
            id="footer",
        )



    def on_mount(self):
        input = self.query_one("#cmd-input", Input)
        input.cursor_position = 1
        input.focus()

    def show_notfcion(self, type=None):
        self.notify("wrong command, try again.")







    def on_input_submitted(self, event: Input.Submitted):
        user_input = event.input.value
        parsed = parse_command(user_input)
        if parsed is None:
            self.show_notfcion()
        else:
            verb = parsed["verb"]
            if verb == "auto":
                self.app.switch_screen(AutoLoadingScreen())
            elif verb == "ip":
                ip = parsed["args"][0]
                try:
                    sk.inet_aton(ip)
                except OSError:
                    self.show_notfcion()
                else:
                    self.app.switch_screen(IpLoadingScreen(ip=ip))
            elif verb == "settings":
                pass
        event.input.cursor_position = 1
        event.input.focus()




class _PreviewApp(App):

    def on_mount(self):
        self.push_screen(WelcomeScreen())



if __name__ == "__main__":
    _PreviewApp().run()