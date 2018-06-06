all:

test:
	bash-testthat/testthat.sh tests

clean:
	$(RM) -r tests/*.output

.PHONY: all test clean
