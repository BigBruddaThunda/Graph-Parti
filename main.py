"""Launch the Archideck cockpit + GRAPH PARTI canvas (split-pane):  python main.py

GRAPH PARTI also runs standalone (canvas only) via:  python -m graphparti
"""
import sys

from archideck.host import run

if __name__ == "__main__":
    sys.exit(run())
