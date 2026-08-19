"""
Run the full pipeline end to end, in order:
  1. load_georgia.py   - clean and load the two Georgia source files
  2. standardize.py     - stack Georgia files, standardize both ports into
                          one common schema, compute delay where possible
  3. clean_carriers.py  - normalize inconsistent carrier name variants
  4. build_chart.py     - generate the carrier volume comparison chart

Run from inside the scripts/ folder:
    python run_pipeline.py
"""

import subprocess
import sys

STEPS = [
    "load_georgia.py",
    "standardize.py",
    "clean_carriers.py",
    "build_chart.py",
]

for step in STEPS:
    print(f"\n{'=' * 60}\nRunning {step}\n{'=' * 60}")
    result = subprocess.run([sys.executable, step])
    if result.returncode != 0:
        print(f"\n{step} failed -- stopping pipeline.")
        sys.exit(1)

print("\nPipeline complete. See ../data/processed/ and ../output/ for results.")
