.PHONY: all verify sim golden stress ablation lockstep clean sync-docs

PYTHON ?= python

all: verify

verify:
	$(PYTHON) run_verification.py

golden:
	$(PYTHON) sim/snn_golden_stdp.py

stress:
	$(PYTHON) sim/stress_test_collapse.py

ablation:
	$(PYTHON) sim/ablation_study_stdp_vs_threshold.py

sim:
	$(PYTHON) sim/end_to_end_mission_sim.py

lockstep:
	$(PYTHON) sim/verify_python_rtl_lockstep.py

sync-docs:
	$(PYTHON) scripts/sync_docs_with_rtl.py

clean:
	rm -f sim/*.vvp sim/*.vcd sim/*.csv *.vvp *.vcd *.log rtl_trace.csv
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
