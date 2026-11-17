#!/usr/bin/env pythonw
"""
launcher.pyw - Independent Windowless Entrypoint for CS2 Sub-Tick Replay Studio

Runs directly on Windows without opening any command prompt or terminal window.
Double-click this file to launch the control center natively without .bat files.
"""

import os
import sys

app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
os.chdir(app_dir)

from launcher import ReplayStudioLauncherApp

if __name__ == "__main__":
    app = ReplayStudioLauncherApp()
    app.run()
