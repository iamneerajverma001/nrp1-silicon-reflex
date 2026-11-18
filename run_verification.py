#!/usr/bin/env python3
import sys
import os

# Redirect directly to sim/run_all_sims_and_tests.py
repo_root = os.path.dirname(os.path.abspath(__file__))
sim_script = os.path.join(repo_root, "sim", "run_all_sims_and_tests.py")

if __name__ == "__main__":
    os.chdir(repo_root)
    with open(sim_script, "r", encoding="utf-8") as f:
        code = compile(f.read(), sim_script, "exec")
        exec(code, {"__name__": "__main__", "__file__": sim_script})
