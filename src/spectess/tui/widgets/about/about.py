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

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import  Label, Button, Rule, Markdown


from textual import on, work
from textual.worker import Worker, WorkerState
from textual.widgets import Header, Footer, Log, DataTable, Label, Button, Static, Switch, ProgressBar, Rule, Checkbox
from textual.widgets import  TabbedContent, TabPane, Tabs, Input, RadioSet, RadioButton, Placeholder, Digits, DirectoryTree, OptionList

from textual.containers import Horizontal, Vertical

#--------------
# local imports
# -------------

from spectess import __version__


class About(ModalScreen):

    DEFAULT_CSS = """
    About {
        align: center middle;
        width: auto;
        height: auto;
    }
    About > Container {
        width: auto;
        height: auto;
        margin: 1;
        background: $panel;
        border:  double yellow;
    }
    About > Container > Label {
        margin: 1;
    }
    About > Container > Button {
         align: center middle;
         width: auto;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(f"Version: {__version__}")
            yield Markdown(ack)
            yield Button('Dismiss')

    @on(Button.Pressed)
    def start_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()