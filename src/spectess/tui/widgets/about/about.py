# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------


#--------------------
# System wide imports
# -------------------
import sys

PKG = 'spectess.tui.widgets.about'
if sys.version_info[1] < 11:
    from pkg_resources import resource_string as resource_bytes
    ack = resource_bytes(PKG, 'ack.md').decode('utf-8')
else:
    from importlib_resources import files
    ack = files(PKG).joinpath('ack.md').read_text()

# ---------------
# Textual imports
# ---------------

from textual import on
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import  Label, Button, Rule, Markdown

#--------------
# local imports
# -------------

from spectess import __version__


class About(ModalScreen):

    DEFAULT_CSS = """
    About {
        align: center middle; 
    }

    About > Container {
        width: 50;
        height: auto;
        background: $panel;
        border: double yellow;
    }

    About > Container > Label {
        margin: 1;
    }

    About > Container > Button {
        margin: 1;
        width: 100%;
    }
    """

    def __init__(self, title=""):
        self._title = title
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(f"Version: {__version__}")
            yield Markdown(ack)
            yield Button('Dismiss',variant="success")

    def on_mount(self) -> None:
        self.query_one(Container).border_title = self._title

    @on(Button.Pressed)
    def ok_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()