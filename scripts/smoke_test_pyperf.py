#!/usr/bin/env python3
"""Human-written smoke benchmark proving that SymPy and pyperf work locally."""

import os

# Set this before importing SymPy. Reusing the same symbolic expression can
# otherwise benchmark a cached result instead of the expansion work itself.
os.environ.setdefault("SYMPY_USE_CACHE", "no")

import pyperf
from sympy import expand, symbols


x, y, z = symbols("x y z")
EXPRESSION = (x + y + z) ** 10


def main() -> None:
    runner = pyperf.Runner()
    runner.bench_func("sympy_expand_degree_10", expand, EXPRESSION)


if __name__ == "__main__":
    main()
