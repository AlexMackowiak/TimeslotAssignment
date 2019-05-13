#!/bin/bash
output_suppression_var=$(python3 -m unittest discover -b -s ./tests -p 'test_*.py')
