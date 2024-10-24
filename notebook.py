#!/usr/bin/env python

from json import load
import fileinput

def loc(nb):
    cells = load(open(nb))['cells']
    return sum(len(c['source']) for c in cells if c['cell_type'] == 'code')

def run(ipynb_files):
    sum = 0
    for nb in ipynb_files:
        l = loc(nb.strip())
        print(f"{nb.strip()}: {l}")
        sum += l
    return sum

if __name__ == '__main__':
    # usage: find . -name '*.ipynb' | python3 notebook.py
    print(run(fileinput.input()))


