#!/usr/bin/env python3
"""Allocate memory until the container memory limit terminates this process."""

blocks: list[bytearray] = []
while True:
    blocks.append(bytearray(8 * 1024 * 1024))
