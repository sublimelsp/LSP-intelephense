.PHONY: all
all:

.PHONY: install
install:
	pip install -U -r requirements.txt

.PHONY: ci-check
ci-check:
	mypy -p plugin
	flake8 .
	black --check --diff --preview .
	isort --check --diff .

.PHONY: ci-fix
ci-fix:
	autoflake --in-place .
	black --preview .
	isort .
