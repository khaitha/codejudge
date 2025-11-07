"""Make the ``src/`` layout importable during tests without an install step.

CI also runs ``pip install -e .`` to validate packaging and the console script,
but this lets ``pytest`` work straight from a fresh checkout.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
