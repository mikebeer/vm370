# Build the Pascal compiler and its runtime library.
#
#   make                 builds build/pascal.rxbin and build/pasrt.rxbin
#   make test            compiles and runs every program in tests/ and compares the output
#
# CREXX_BIN is the directory holding the cREXX tools (rxc, rxas, rxvm).
CREXX_BIN ?= $(dir $(shell which rxc))
RXC  = $(CREXX_BIN)/rxc
RXAS = $(CREXX_BIN)/rxas

all: build/pascal.rxbin build/pasrt.rxbin

build/%.rxbin: %.crexx
	mkdir -p build
	cp $< build/$*.crexx
	cd build && $(RXC) -n $* > $*.log 2>&1 || (cat $*.log; exit 1)
	cd build && $(RXAS) $*

test: all
	./tests/run.sh

ide-test:
	python3 tests/ide_test.py

clean:
	rm -rf build

.PHONY: all test ide-test clean
