all:

test:
	bash-testthat/testthat.sh tests

clean:

.PHONY: all test clean
