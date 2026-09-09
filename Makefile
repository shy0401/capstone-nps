PYTHON ?= python
.PHONY: bootstrap up down test e2e golden security-test offline-test bundle
bootstrap up down test e2e golden security-test offline-test bundle:
	$(PYTHON) infra/scripts/manage.py $@
