"""
This file gives a proof-of-concept implementation of reading from a linked list that already exists in memory.
Adding new elements to a linked list would require a compiler with knowledge of how the memory is allocated, but
is in principle feasible using similar techniques.

The list that is in memory takes the following form:

Address 50 (given as an argument): (Value) 2
Address 51: (Pointer to next element) 60

Address 60: (Value) 3
Address 61: (Pointer to next element) 56

Address 56: (Value) 5
Address 57: (Pointer to next element) 81

Address 81: (Value) 7
Address 82: (Pointer to next element) 62

Address 62: (Value) 7
Address 63: (Sentinel) 0b1111....11111

The goal of the program is to find and return the value of the final element in the linked list, which is 11.
"""

import unittest
from computer_core.computer import Computer, Int
from assembler.assembler import assemble

code = """
# First load the argument, which is the memory address of the first element of the list, into register 2.
LOAD 100 2 #0

# Load the sentinel value into register 10 for later comparison.
LOAD B1111111111111111 10 IMMEDIATE HALF #1
LOAD B1111111111111111 10 IMMEDIATE HALF TO_SIG #2

[MAINLOOP]
# Calculate address of pointer to next element into register 3
ADD 2 1 3
# Edit the following LOAD instruction so it contains the calculated address
STORE 3 5 HALF
# Load the address into register 4
LOAD 0 4
# Compare this pointer with the sentinel and store result in COMP register 0.
COMP 4 10 0
# If it is the same, jump out of the loop
JUMP 0 [END] INC ON_HIGH
# Not the same: need to find next element. The address of the next element is in register 4.
ADD 4 0 2
# Repeat main loop unconditionally
JUMP 1 [MAINLOOP] DEC

[END]
# If it is the same, we have found the element and it is stored in the address held in register 2
STORE 2 11 HALF
LOAD 0 5

# Store the output into memory slot 101 for returning.
STORE 5 101

HALT
"""


class TestLinkedList(unittest.TestCase):
    def test_linked_list(self):
        # Assemble the code
        program = assemble(code)

        # Set up the computer and store the linked list in the memory
        c = Computer()
        address = 50
        elements = [(2, 60), (3, 56), (5, 62), (7, 81), (11, (1 << 32) - 1)]
        for value, next_address in elements:
            c.set_memory_address(address, Int(value))
            c.set_memory_address(address + 1, Int(next_address))
            address = next_address

        # Load the program
        c.set_memory_chunk(0, program)

        # Provide the first address to the program as an argument
        c.set_memory_address(100, Int(50))

        c.execute(debug_mode = False)

        # Get the result
        result = c.get_memory_address(101)

        self.assertEqual(11, result)
