import unittest

from computer_core.computer import Computer, Int
from assembler.assembler import assemble
from computer_core.cost_metric_tracker import CostMetricTracker

"""
This file contains a program, written in assembly code, that takes in two integers A and B and returns 
the divisor and remainder after calculating A/B (equivalent to divmod(A,B) in python).

It uses bit shifts to achieve a complexity linear in the number of bits of A, that is, is has time complexity O(log(A)).
"""
ARG1, ARG2, OUT1, OUT2 = 100, 101, 102, 103
code = f"""
# Load program arguments
LOAD {ARG1} 2
LOAD {ARG2} 3
# Load the number 1 into reg 4

# Find highest m = 2^n*B s.t. m <= A
ADD 1 0 4
ADD 3 0 5
[LOOP1]
LSHIFT 4 1 4
LSHIFT 5 1 5
COMPLST 2 5 0
JUMP 0 [LOOP1] ON_LOW DEC
RSHIFT 4 1 4
RSHIFT 5 1 5

[LOOP2]
# Add to the div register 6
ADD 4 6 6
# Sub from the rem register 2, A -> A - m
SUB 2 5 2

[LOOP3]
# Find the next smallest number m = 2^n * B  s.t  m <= A
RSHIFT 4 1 4
# Does n == 0? In which case we are done.
COMP 4 0 0
JUMP 0 [END] INC ON_HIGH
RSHIFT 5 1 5
COMPLST 2 5 1
JUMP 1 [LOOP3] DEC ON_HIGH
JUMP 3 [LOOP2] DEC

[END]
# Store outputs from program.
STORE 6 {OUT1}
STORE 2 {OUT2}
PRINT 6 2 0
HALT
"""
program = assemble(code)

def tenth_fibonacci_no(A, B):
    print(f"Running division with {A=}, {B=}...")
    computer = Computer()

    # Load program
    computer.set_memory_chunk(0,program)

    # Set arguments
    computer.set_memory_address(ARG1,Int(A))
    computer.set_memory_address(ARG2,Int(B))

    # Run
    with CostMetricTracker(computer, debug_mode=False) as cost_tracker:
        computer.execute(debug_mode = True)

    # Get result
    div = computer.get_memory_address(OUT1)
    rem = computer.get_memory_address(OUT2)
    print(f"Returned {div=}, {rem=}.")
    print(cost_tracker.summary())
    return div, rem

class TestIntegerDivision(unittest.TestCase):
    def test_integer_division(self):
        inputs_and_expected = [
            (1,1,1,0),
            (10,1,10,0),
            (71,9,7,8),
            (1236738, 457, 2706, 96)
        ]
        for arg_1, arg_2, exp_div, exp_rem in inputs_and_expected:
            self.assertEqual((exp_div, exp_rem),tenth_fibonacci_no(arg_1,arg_2))

if __name__ == "__main__":
    unittest.main()
