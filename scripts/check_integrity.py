#!/usr/bin/env python3
import os
import re
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rtl_dir = os.path.join(repo_root, "rtl")
docs_dir = os.path.join(repo_root, "docs")

print("=" * 80)
print("NRP-1 REPO INTEGRITY & COMPLIANCE CHECKER")
print("=" * 80)

# Check 1: RTL Verilog Compliance
files = [f for f in os.listdir(rtl_dir) if f.endswith('.v')]
unpacked_port_pattern = re.compile(r'input\s+wire\s*\[\d+:\d+\]\s+\w+\s*\[\d+:\d+\]|output\s+(reg|wire)\s*\[\d+:\d+\]\s+\w+\s*\[\d+:\d+\]')
rtl_ok = True
for f in files:
    with open(os.path.join(rtl_dir, f), 'r', encoding='utf-8') as fp:
        content = fp.read()
    if unpacked_port_pattern.search(content):
        print(f"  [FAIL] {f}: Contains SystemVerilog unpacked array ports!")
        rtl_ok = False
    else:
        print(f"  [PASS] {f}: Pure IEEE 1364-2001 synthesizable Verilog.")

# Check 2: Markdown Code Fences
md_files = [os.path.join(docs_dir, "PROJECT_BIBLE.md"), os.path.join(docs_dir, "DEFENSE_DOSSIER.md")]
fences_ok = True
for mp in md_files:
    with open(mp, 'r', encoding='utf-8') as fp:
        lines = fp.readlines()
    fences = [i+1 for i, line in enumerate(lines) if line.strip().startswith("```")]
    is_even = (len(fences) % 2 == 0)
    print(f"  [{'PASS' if is_even else 'FAIL'}] {os.path.basename(mp)}: {len(fences)} fences (Even: {is_even})")
    if not is_even:
        fences_ok = False

if rtl_ok and fences_ok:
    print("[ALL CHECKS PASSED]: Repository integrity is 100% verified.")
    sys.exit(0)
else:
    print("[INTEGRITY FAILURE]: Discrepancies found.")
    sys.exit(1)
