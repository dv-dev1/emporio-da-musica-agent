"""The dataset is a snapshot, so the clock is frozen.

Without this every deadline assertion would degenerate into "expired months
ago" the day someone runs the suite.
"""

import os

os.environ.setdefault("EMPORIO_TODAY", "2026-03-25")
