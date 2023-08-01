"""
This file contains a basic assembler for the instruction set to make writing programs easier.
It has a system of labels and references so the programmer does not need to calculate jump amounts manually.
This script pushes the limits of what is comfortable with match statements, splits etc. For more advanced functionality
an OOP approach using regex or a parsing library would be more suitable.
This script has not undergone rigorous testing.
"""
import numpy as np

from computer_core.instructions import instructions
from computer_core.constants import *


def assemble(program: str):
    """
    Main function that produces a machine code program from assembly code
    """

    # Pre-processing step to remove empty lines and comments and find jump labels
    lines = program.splitlines()
    pre_processed_lines = []
    labels = {}
    line_i = 0
    for full_line in lines:
        line = full_line.split('#')[0]  # Remove comments
        match line.split():
            case []:  # Empty line
                continue
            case [other, *_]:
                # Found jump label
                if other[0] == '[' and other[-1] == ']':
                    labels[other[1:-1]] = line_i
                else:
                    pre_processed_lines.append(line)
                    line_i += 1  # We only count the lines with instructions.

    # Main parsing step
    program_data = []
    for line_i, line in enumerate(pre_processed_lines):
        try:
            match line.split():
                case [token, *args]:
                    for instruction in instructions:
                        if token == instruction.assembly_token():
                            program_data.append(instruction.make_instruction(args, line_i, labels))
                            break
                    else:
                        raise SyntaxError(f"Unknown token {token}.")
                case _:
                    raise SyntaxError("Could not decompose line.")
        except Exception as e:
            raise SyntaxError(f"Could not parse line {line_i}: '{line}'.") from e
    return np.array(program_data, dtype=Int)
