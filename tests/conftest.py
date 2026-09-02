import os

# The dataset is a snapshot; freezing the clock keeps the deadline assertions
# meaningful instead of "everything expired months ago".
os.environ.setdefault("EMPORIO_TODAY", "2026-03-25")
