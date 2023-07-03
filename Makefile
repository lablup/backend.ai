
.PHONY: all doc test

all:

doc:
	@echo
	@echo "Building documentation"
	@echo "======================"
	@echo
	python setup.py build_sphinx
	@echo
	@echo Generated documentation: "file://"$$(readlink -f doc/build/html/index.html)
	@echo

test:
	@echo
	@echo "Running tests"
	@echo "============="
	@echo
	py.test tests/
