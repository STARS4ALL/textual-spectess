# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import os
import sys
import argparse
import logging

import statistics

# ---------------
# Textual imports
# ---------------

from textual import on, work
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Log, DataTable, Label, Button, Static, Switch, ProgressBar, Sparkline, Rule
from textual.widgets import  TabbedContent, TabPane, Input, RadioButton, Button

from textual.containers import Horizontal, Vertical

#--------------
# local imports
# -------------

from spectess.photometer import REF, TEST, label

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger()

# -------------------
# Auxiliary functions
# -------------------

class SpecTessApp(App[str]):

    TITLE = "SpecTESS-W"
    SUB_TITLE = "TESS-W Zero Joser Calibration tool"

    # Seems the bindings are for the Footer widget
    BINDINGS = [
        ("q", "quit", "Quit Application")
    ]

    CSS_PATH = [
        os.path.join("css", "spectess.tcss"),
    ]

    def __init__(self, controller, description):
       
        self.controller = controller
        # Widget references in REF/TEST pairs
        self.log_w = [None, None]
        self.switch_w = [None, None]
        self.metadata_w = [None, None]
        self.progress_w = [None, None]
        self.graph_w = [None, None]
        self.nsamples_w = [None, None]
        self.SUB_TITLE = description
        super().__init__()
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="complex"):
                yield Switch(id="tst_phot")
                yield Label("Photometer On/Off", classes="mylabels")
                yield Label("Number of Samples", classes="mylabels")
                yield Label("Wavelength [nm]", classes="mylabels")
                yield Input(placeholder="Number of samples", id="nsamples", type="integer")
                yield Input(placeholder="Wavelength [nm]")
                yield RadioButton("Save samples")
                yield Label("Statistics", classes="mylabels")
                yield Button("Capture", id="start_button")
                yield ProgressBar(id="tst_ring", total=100, show_eta=False)
            yield DataTable(id="tst_metadata")
        yield Log(id="tst_log", classes="box")
        yield Footer()
        

    def on_mount(self) -> None:      
        for ident in ("#tst_metadata",):
            table = self.query_one(ident)
            table.add_columns(*("Property", "Value"))
            table.fixed_columns = 2
            table.show_cursor = False
        self.log_w[TEST] = self.query_one("#tst_log")
        self.log_w[TEST].border_title = f"{label(TEST)} LOG"
        self.switch_w[TEST] = self.query_one("#tst_phot")
        self.switch_w[TEST].border_title = 'OFF / ON'
        self.metadata_w[TEST] = self.query_one("#tst_metadata")
        self.nsamples_w[TEST] = self.query_one("#nsamples")
        self.nsamples_w[TEST].value = self.controller.samples

    # -----------------------------
    # API exposed to the Controller
    # -----------------------------
    
    def append_log(self, role, line):
        self.log_w[role].write_line(line)

    def reset_switch(self, role):
        self.switch_w[role].value = False
   
    def clear_metadata_table(self, role):
        self.metadata_w[role].clear()

    def update_metadata_table(self, role, metadata):
        self.metadata_w[role].add_rows(metadata.items())

    def action_quit(self):
        self.controller.quit_event.set()
        self.exit(return_code=2)


    # ----------------------
    # Textual event handlers
    # ----------------------

    @on(Switch.Changed, "#tst_phot")
    def tst_switch_pressed(self, message):
        if message.control.value:
            w = self.run_worker(self.controller.get_info(TEST), exclusive=True)
        else:
            self.clear_metadata_table(TEST)

    @on(Button.Pressed, "#start_button")
    def button_pressed(self, event: Button.Pressed) -> None:
        self.exit(str(event.button))