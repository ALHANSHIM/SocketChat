from textual.app import App, ComposeResult
from textual.containers import Center, Middle
from textual.reactive import reactive
from textual.widgets import Static

RING_R, RING_C = 8, 12


def build_ring(offset: int) -> list[str]:
    rows = []
    for y in range(RING_R):
        line = []
        for x in range(RING_C):
            dx = x - (RING_C - 1) / 2
            dy = y - (RING_R - 1) / 2
            r = (dx * dx + dy * dy) ** 0.5
            if 3.4 <= r <= 4.4:
                seg = int((dx + dy + 3) % 8)
                if (seg + offset) % 8 in (0, 7):
                    line.append("\u2588")
                elif (seg + offset) % 8 in (1,):
                    line.append("\u2593")
                else:
                    line.append("\u2591")
            else:
                line.append(" ")
        rows.append(" ".join(line))
    return rows


class LoadingRing(Static):

    offset: reactive[int] = reactive(0)
    DEFAULT_CSS = """
    LoadingRing {
        color: #00d4ff;
        text-style: bold;
        width: auto;
        height: auto;
        content-align: center middle;
    }
    """

    def on_mount(self) -> None:
        self.set_interval(0.09, self._tick)

    def _tick(self) -> None:
        self.offset = (self.offset + 1) % 8

    def watch_offset(self, old: int, new: int) -> None:
        self.update("\n".join(build_ring(new)))


class LoadingApp(App):

    CSS = """
    Screen {
        background: black;
        layout: vertical;
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                yield LoadingRing()


if __name__ == "__main__":
    LoadingApp().run()
