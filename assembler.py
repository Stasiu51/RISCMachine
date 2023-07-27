from constants import *
import numpy as np
"""
This file contains a basic assembler for the instruction set to make writing programs easier.
"""
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
        if len(s)>=2 and s[0] == "B":
            val = int(s[1:],2)
        else:
            val = int(s,10)
    except Exception as e:
        raise Exception(f"Failed to parse argument '{s}'.") from e
    if not range_min <= val < range_max:
        raise ValueError(f"Argument {val} is out of range (min {range_min}, max {range_max}).")
    return val

def parse_arg_multiple(max_range, *args):
    return (parse_arg(s, max_range) for s in args)


def assemble(program: str):
    program_data = []
    lines = program.splitlines()
    for i_line, line in enumerate(lines):
        try:
            match line.split():
                case []:
                    continue
                case ["NOP"]:
                    program_data.append(make_ins_data(OPCODE_NOP,0,0,0))
                case ["HALT"]:
                    program_data.append(make_ins_data(OPCODE_HALT, 0, 0, 0))
                case ["ADD",arg_1,arg_2,arg_3]:
                    program_data.append(make_ins_reg(OPCODE_ADD, *parse_arg_multiple(32,arg_1,arg_2,arg_3)))
                case ["SUB", arg_1, arg_2, arg_3]:
                    program_data.append(make_ins_reg(OPCODE_SUB, *parse_arg_multiple(32,arg_1,arg_2,arg_3)))
                case ["COMP", arg_1, arg_2, arg_3]:
                    program_data.append(make_ins_reg(OPCODE_CMP, *parse_arg_multiple(32,arg_1,arg_2,arg_3)))
                case ["LOAD", address, register, *flags]:
                    flags = sum(bit for token, bit in COPY_FLAGS.items() if token in flags)
                    program_data.append(
                        make_ins_data(OPCODE_LOAD, parse_arg(register,32),flags,parse_arg(address,address_max)))
                case ["STORE", register, address, *flags]:
                    flags = sum(bit for token, bit in COPY_FLAGS.items() if token in flags)
                    program_data.append(
                        make_ins_data(OPCODE_STORE, parse_arg(register,32),flags,parse_arg(address,address_max)))
                case ["JUMP", register, amount, *flags]:
                    flags = sum(bit for token, bit in JUMP_FLAGS.items() if token in flags)
                    program_data.append(
                        make_ins_data(OPCODE_JMP, parse_arg(register, 32), flags, parse_arg(amount, address_max)))
                case ["PRINT", reg_1, reg_2, address]:
                    program_data.append(
                        make_ins_data(OPCODE_PRINT, *parse_arg_multiple(32, reg_1, reg_2), parse_arg(address, address_max)))
                case _:
                    raise ValueError(f"Unknown syntax: '{line}'")
        except Exception as e:
            raise ValueError(f"Syntax error on line {i_line}.") from e
    return np.array(program_data, dtype = Int)
