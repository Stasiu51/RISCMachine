import unittest

from computer import Computer, Int
from assembler import assemble

"""
This file contains a program that, given two starting numbers of a fibonacci-style sequence, 
calculates the 10th number in that sequence. It contains a set of test cases. 
The program is not intended to be resilient to invalid inputs such as those resulting in overflows.
"""

code = """
LOAD 100 2 # Argument 1 should be loaded into 100 before execution
LOAD 101 3 # ... and argument 2 into 101.
LOAD 8 5 IM HLF


[LOOP]
ADD 2 3 4
ADD 3 0 2
ADD 4 0 3
SUB 5 1 5
COMP 5 0 0
JUMP 0 [LOOP] DEC
STORE 4 102 # The result can be retrieved from 102.
PRINT 4 2 102

HALT
"""
program = assemble(code)

def tenth_fibonacci_no(starting_a, starting_b):
    computer = Computer()

    # Load program
    computer.set_memory_chunk(0,program)

    # Set arguments
    computer.set_memory_address(100,Int(starting_a))
    computer.set_memory_address(101,Int(starting_b))

    # Run
    computer.execute()

    # Get result
    return computer.get_memory_address(102)

class TestFibonacci(unittest.TestCase):
    def test_fibonacci(self):
        inputs_and_expected = [
            (1,1,55),
            (0,0,0),
            (1,0,21),
            (10,10,550)
        ]
        for arg_1, arg_2, expected in inputs_and_expected:
            self.assertEqual(expected,tenth_fibonacci_no(arg_1,arg_2))

if __name__ == "__main__":
    unittest.main()
