SHELL := /bin/bash

.PHONY: package lint-python

package:
	./scripts/package_source.sh

lint-python:
	python3 -m py_compile scripts/convert_findings.py scripts/enforce_thresholds.py

