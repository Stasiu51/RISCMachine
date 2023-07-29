"""
This file contains a basic assembler for the instruction set to make writing programs easier.
It has a system of labels and references so the programmer does not need to calculate jump amounts manually.
This script pushes the limits of what is comfortable with match statements, splits etc. For more advanced functionality
an OOP approach using regex or a parsing library would be more suitable.
This script has not undergone rigorous testing.
"""

from constants import *
import numpy as np

COPY_FLAGS = {"HLF": 0b10000, "FRM_SIG": 0b01000, "TO_SIG": 0b00100, "OW": 0b00010, "IM": 0b00001}
JUMP_FLAGS = {"ON_HIGH": 0b10000, "ON_LOW": 0, "DEC": 0b01000, "INC": 0}
address_max = 1 << 16


def make_ins_data(opcode, arg1, arg2, data):
    """
    Creates an instruction that takes two 5 bit arguments and a 16-bit address/data argument.
    """
    return (Int(opcode) << 26) | (Int(arg1) << 21) | (Int(arg2) << 16) | Int(data)


def make_ins_reg(opcode, arg1, arg2, arg3):
    """
    Creates an instruction that takes three 5 bit arguments.
    """
    return (Int(opcode) << 26) | (Int(arg1) << 21) | (Int(arg2) << 16) | (Int(arg3) << 11)


def parse_arg(s, range_max, range_min=0):
    """
    Parses an argument that could be in decimal or binary syntax
    """
    try:
        if len(s) >= 2 and s[0] == "B":
            val = int(s[1:], 2)
        else:
            val = int(s, 10)
    except Exception as e:
        raise Exception(f"Failed to parse argument '{s}'.") from e
    if not range_min <= val < range_max:
        raise ValueError(f"Argument {val} is out of range (min {range_min}, max {range_max}).")
    return val


def parse_arg_multiple(max_range, *args):
    """
    Convenience function for multiple parse_arg calls
    """
    return (parse_arg(s, max_range) for s in args)


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
                case ["NOP"]:
                    program_data.append(make_ins_data(OPCODE_NOP, 0, 0, 0))
                case ["HALT"]:
                    program_data.append(make_ins_data(OPCODE_HALT, 0, 0, 0))
                case ["ADD", arg_1, arg_2, arg_3]:
                    program_data.append(make_ins_reg(OPCODE_ADD, *parse_arg_multiple(32, arg_1, arg_2, arg_3)))
                case ["SUB", arg_1, arg_2, arg_3]:
                    program_data.append(make_ins_reg(OPCODE_SUB, *parse_arg_multiple(32, arg_1, arg_2, arg_3)))
                case ["COMP", arg_1, arg_2, arg_3]:
                    program_data.append(make_ins_reg(OPCODE_CMP, *parse_arg_multiple(32, arg_1, arg_2, arg_3)))
                case ["LOAD", address, register, *flags]:
                    flags = sum(bit for token, bit in COPY_FLAGS.items() if token in flags)
                    program_data.append(
                        make_ins_data(OPCODE_LOAD, parse_arg(register, 32), flags, parse_arg(address, address_max)))
                case ["STORE", register, address, *flags]:
                    flags = sum(bit for token, bit in COPY_FLAGS.items() if token in flags)
                    program_data.append(
                        make_ins_data(OPCODE_STORE, parse_arg(register, 32), flags, parse_arg(address, address_max)))
                case ["JUMP", register, amount, *flags]:
                    flags = sum(bit for token, bit in JUMP_FLAGS.items() if token in flags)
                    if amount[0] == '[' and amount[-1] == ']':
                        # find label distance. up to programmer to specify direction. no error checking for simplicity.
                        parsed_amount = Int(abs(labels[amount[1:-1]] - line_i))
                    else:
                        parsed_amount = parse_arg(amount, address_max)
                    program_data.append(
                        make_ins_data(OPCODE_JMP, parse_arg(register, 32), flags, parsed_amount))
                case ["PRINT", reg_1, reg_2, address]:
                    program_data.append(
                        make_ins_data(OPCODE_PRINT, *parse_arg_multiple(32, reg_1, reg_2),
                                      parse_arg(address, address_max)))
                case _:
                    # Anything not recognised here is a syntax error
                    raise ValueError(f"Unknown syntax: '{line}'")
        except Exception as e:
            raise ValueError(f"Syntax error on line {line_i}: '{line}'.") from e
    return np.array(program_data, dtype=Int)
