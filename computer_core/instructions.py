from abc import ABC, abstractmethod
from typing import List
from bitarray.util import int2ba
from computer_core.constants import *
from assembler.assembler_utils import make_ins_data, make_ins_reg, \
    parse_arg, require_args, parse_arg_multiple


class Instruction(ABC):
    # Ideally these would be properties,
    # but there seems to be no elegant way of making static abstract properties in python
    @staticmethod
    @abstractmethod
    def opcode() -> Int:
        """
        Return the binary opcode which identifies the instruction in machine code.
        """
        pass

    @staticmethod
    @abstractmethod
    def assembly_token() -> str:
        """
        Return the string token which identifies the instruction in assembly.
        """
        pass

    @staticmethod
    @abstractmethod
    def make_instruction(args: List[str], line_index, labels) -> Int:
        """
        Construct the machine code instruction data from the line of assembly code.
        """
        pass

    @staticmethod
    @abstractmethod
    def execute_on(computer, arg1: Int, arg2: Int, data: Int):
        """
        Execute the instruction on the given computer.
        """
        pass


class Nop(Instruction):
    """ Do nothing. """

    @staticmethod
    def opcode() -> Int:
        return OPCODE_NOP

    @staticmethod
    def assembly_token() -> str:
        return 'NOP'

    @staticmethod
    def make_instruction(args: List[str], line_index, labels) -> Int:
        return make_ins_data(OPCODE_NOP, 0, 0, 0)

    @staticmethod
    def execute_on(computer, arg1: Int, arg2: Int, data: Int):
        if computer.debug_mode: print("NOP")


class Halt(Instruction):
    """ Stop execution by resetting the 'running' flag. """

    @staticmethod
    def opcode() -> Int:
        return OPCODE_HALT

    @staticmethod
    def assembly_token() -> str:
        return 'HALT'

    @staticmethod
    def make_instruction(args: List[str], line_index, labels) -> Int:
        return make_ins_data(OPCODE_HALT, 0, 0, 0)

    @staticmethod
    def execute_on(computer, arg1: Int, arg2: Int, data: Int):
        """ Stop execution by resetting the 'running' flag. """
        if computer.debug_mode: print("HALT")
        computer.status_reg[RUNNING_FLAG_INDEX] = False


class Print(Instruction):
    """
    Print the contents of data registers with indices register_1, register_2 and the memory at the given address.
    """

    @staticmethod
    def opcode() -> Int:
        return OPCODE_PRINT

    @staticmethod
    def assembly_token() -> str:
        return 'PRINT'

    @staticmethod
    def make_instruction(args: List[str], line_index, labels) -> Int:
        reg_1, reg_2, address = require_args(args, 3, 3)
        return make_ins_data(OPCODE_PRINT, *parse_arg_multiple(32, reg_1, reg_2),
                             parse_arg(address, MEMORY_SIZE_MAX))

    @staticmethod
    def execute_on(computer, arg1: Int, arg2: Int, data: Int):
        print(f"print: register {arg1}: {computer.data_regs[arg1]:032b} = {computer.data_regs[arg1]}, "
              f"register {arg2}: {computer.data_regs[arg2]:032b} = {computer.data_regs[arg2]}, "
              f"address {data}: {computer.memory[data]:032b} = {computer.memory[data]}")


COPY_FLAGS = {"HALF": 0b10000, "FULL": 0,
              "FRM_SIG": 0b01000, "FROM_LOW": 0,
              "TO_SIG": 0b00100, "TO_LOW": 0,
              "OVERWRITE": 0b00010, "NO_OVERWRITE": 0,
              "IMMEDIATE": 0b00001, "NORMAL": 0}


class Load(Instruction):
    """
    Load data from memory or from the instruction itself into a data register.
    For a complete description of the flags, see the README.
    """

    @staticmethod
    def opcode() -> Int:
        return OPCODE_LOAD

    @staticmethod
    def assembly_token() -> str:
        return "LOAD"

    @staticmethod
    def make_instruction(args: List[str], line_index, labels) -> Int:
        address, register, *flag_args = require_args(args, 2, None)
        flags = Int(0)
        for flag_arg in flag_args:
            if flag_arg not in COPY_FLAGS:
                raise SyntaxError(f"Unknown flag {flag_arg}.")
            flags ^= COPY_FLAGS[flag_arg]
        return make_ins_data(OPCODE_LOAD, parse_arg(register, 32), flags, parse_arg(address, MEMORY_SIZE_MAX))

    @staticmethod
    def execute_on(computer, arg1: Int, arg2: Int, data: Int):
        if computer.debug_mode: print(f"load {arg1}, {arg2:05b}, {data}")
        control_flags = int2ba(int(arg2), endian='little', length=5)

        if control_flags[IMMEDIATE_FLAG_INDEX]:  # Immediate mode, instruction itcomputer is source
            source_bits = computer.memory[computer.PC]
        else:  # Load from memory
            if not 0 <= data < computer.memory_size:
                raise SegmentationFaultError(f"Attempted to read from address {data}, which is out of range.")
            source_bits = computer.memory[data]

        if not control_flags[HALF_COPY_FLAG_INDEX]:  # moving all 32 bits
            computer.data_regs[arg1] = source_bits
            return

        # moving only 16 bits
        if control_flags[SIGNIFICANT_SRC_FLAG_INDEX]:
            half_source_bits = (SIG_HALF_ONES & source_bits) >> 16
        else:
            half_source_bits = HALF_ONES & source_bits

        if control_flags[SIGNIFICANT_DST_FLAG_INDEX]:
            if control_flags[OVERWRITE_FLAG_INDEX]:
                computer.data_regs[arg1] = Int(half_source_bits << 16)  # Overwrite all the bits
            else:
                # Overwrite only the 16 affected bits
                computer.data_regs[arg1] = Int((half_source_bits << 16) | (computer.data_regs[arg1] & HALF_ONES))
        else:
            if control_flags[OVERWRITE_FLAG_INDEX]:
                computer.data_regs[arg1] = Int(half_source_bits)
            else:
                computer.data_regs[arg1] = Int(half_source_bits | (computer.data_regs[arg1] & SIG_HALF_ONES))


class Store(Instruction):
    """
    Store data from a data register or from the instruction itself into an address in memory.
    For a complete description of the flags, see the README.
    """

    @staticmethod
    def opcode() -> Int:
        return OPCODE_STORE

    @staticmethod
    def assembly_token() -> str:
        return "STORE"

    @staticmethod
    def make_instruction(args: List[str], line_index, labels) -> Int:
        register, address, *flag_args = require_args(args, 2, None)
        flags = Int(0)
        for flag_arg in flag_args:
            if flag_arg not in COPY_FLAGS:
                raise SyntaxError(f"Unknown flag {flag_arg}.")
            flags ^= COPY_FLAGS[flag_arg]
        return make_ins_data(OPCODE_STORE, parse_arg(register, 32), flags, parse_arg(address, MEMORY_SIZE_MAX))

    @staticmethod
    def execute_on(computer, arg1: Int, arg2: Int, data: Int):
        if computer.debug_mode: print(f"store {arg1}, {arg2:05b}, {data}")
        control_flags = int2ba(int(arg2), endian='little', length=5)

        if not 0 <= data < computer.memory_size:
            raise SegmentationFaultError(f"Attempted to write to address {data}, which is out of range.")

        if control_flags[IMMEDIATE_FLAG_INDEX]:  # Immediate mode, instruction itcomputer is source
            source_bits = computer.memory[computer.PC]
        else:  # Load from memory
            source_bits = computer.data_regs[arg1]

        if not control_flags[HALF_COPY_FLAG_INDEX]:  # moving all 32 bits
            computer.memory[data] = source_bits
            return

        # moving only 16 bits
        if control_flags[SIGNIFICANT_SRC_FLAG_INDEX]:
            half_source_bits = (SIG_HALF_ONES & source_bits) >> 16
        else:
            half_source_bits = HALF_ONES & source_bits

        if control_flags[SIGNIFICANT_DST_FLAG_INDEX]:
            if control_flags[OVERWRITE_FLAG_INDEX]:  # Overwrite all the bits
                computer.memory[data] = Int(half_source_bits << 16)
            else:  # Overwrite only the 16 affected bits
                computer.memory[data] = Int((half_source_bits << 16) | (computer.memory[data] & HALF_ONES))
        else:
            if control_flags[OVERWRITE_FLAG_INDEX]:
                computer.memory[data] = Int(half_source_bits)
            else:
                computer.memory[data] = Int(half_source_bits | (computer.memory[data] & SIG_HALF_ONES))


JUMP_FLAGS = {"ON_HIGH": 0b10000, "ON_LOW": 0, "DEC": 0b01000, "INC": 0}


class Jump(Instruction):
    """
    A conditional relative jump, performed by modifying the program counter.
    """

    @staticmethod
    def opcode() -> Int:
        return OPCODE_JMP

    @staticmethod
    def assembly_token() -> str:
        return "JUMP"

    @staticmethod
    def make_instruction(args: List[str], line_index, labels) -> Int:
        comp_reg, amount, *flag_args = require_args(args, 3, None)
        flags = Int(0)
        for flag_arg in flag_args:
            if flag_arg not in JUMP_FLAGS:
                raise SyntaxError(f"Unknown flag {flag_arg}.")
            flags ^= JUMP_FLAGS[flag_arg]
        if amount[0] == '[' and amount[-1] == ']':
            # find label distance. up to programmer to specify direction. no error checking for simplicity.
            parsed_amount = Int(abs(labels[amount[1:-1]] - line_index))
        else:
            parsed_amount = parse_arg(amount, MEMORY_SIZE_MAX)
        return make_ins_data(OPCODE_JMP, parse_arg(comp_reg, 32), flags, parsed_amount)

    @staticmethod
    def execute_on(computer, arg1: Int, arg2: Int, data: Int):
        if computer.debug_mode: print(f"jump control register={arg1}, flags={arg2:05b}, amount={data=}")
        control_flags = int2ba(int(arg2), endian='little', length=5)
        if computer.comp_reg[arg1] == control_flags[JUMP_CONDITION_INDEX]:
            # subtract 1 for convenience as the computer will add one at the end of the cycle
            new_PC = computer.PC - data - 1 if control_flags[JUMP_SUBTRACT_INDEX] else computer.PC + data - 1
            if not 0 <= new_PC < computer.memory_size:
                raise SegmentationFaultError(f"Attempted to move program counter to {new_PC}, which is out of bounds.")
            computer.PC = new_PC


class Add(Instruction):
    """
    Add the contents of reg_1 and the contents of reg_2 and store the result in reg_3.
    In case of overflow, set the relevant status bit.
    """

    @staticmethod
    def opcode() -> Int:
        return OPCODE_ADD

    @staticmethod
    def assembly_token() -> str:
        return "ADD"

    @staticmethod
    def make_instruction(args: List[str], line_index, labels) -> Int:
        reg1, reg2, reg3 = require_args(args, 3, 3)
        return make_ins_reg(OPCODE_ADD, *parse_arg_multiple(32, reg1, reg2, reg3))

    @staticmethod
    def execute_on(computer, arg1: Int, arg2: Int, data: Int):
        reg3 = data >> 11
        if computer.debug_mode: print(f"add reg_1={arg1}, reg_2={arg2}, reg_3={reg3}")
        if int(computer.data_regs[arg1]) + int(computer.data_regs[arg2]) >= 1 << 32:  # Overflow occurred.
            print("Warning: integer overflow. Flag set.")
            computer.status_reg[OVERFLOW_FLAG_INDEX] = True
        else:
            computer.status_reg[OVERFLOW_FLAG_INDEX] = False
        computer.data_regs[reg3] = computer.data_regs[arg1] + computer.data_regs[arg2]


class Sub(Instruction):
    """
    Subtract the contents of reg_2 from the contents of reg_1 and store the result in reg_3.
    In case of underflow, set the relevant status bit.
    """

    @staticmethod
    def opcode() -> Int:
        return OPCODE_SUB

    @staticmethod
    def assembly_token() -> str:
        return "SUB"

    @staticmethod
    def make_instruction(args: List[str], line_index, labels) -> Int:
        reg1, reg2, reg3 = require_args(args, 3, 3)
        return make_ins_reg(OPCODE_SUB, *parse_arg_multiple(32, reg1, reg2, reg3))

    @staticmethod
    def execute_on(computer, arg1: Int, arg2: Int, data: Int):
        reg_3 = data >> 11
        if computer.debug_mode: print(f"sub {arg1=}, {arg2=}, {reg_3=}")
        if reg_3 <= 1:
            print(f"Warning: attempted to subtract into register {reg_3} which is read-only.")
            return
        if int(computer.data_regs[arg1]) - int(computer.data_regs[arg2]) < 0:  # Underflow occurred.
            print("Warning: integer underflow. Flag set.")
            computer.status_reg[OVERFLOW_FLAG_INDEX] = True
        else:
            computer.status_reg[OVERFLOW_FLAG_INDEX] = False
        computer.data_regs[reg_3] = computer.data_regs[arg1] - computer.data_regs[arg2]


class Comp(Instruction):
    """
    Compare the contents of reg_2 and the contents of reg_1 and set the specified bit in the COMP_REG.
    """

    @staticmethod
    def opcode() -> Int:
        return OPCODE_COMP

    @staticmethod
    def assembly_token() -> str:
        return 'COMP'

    @staticmethod
    def make_instruction(args: List[str], line_index, labels) -> Int:
        reg1, reg2, comp_reg = require_args(args, 3, 3)
        return make_ins_reg(OPCODE_COMP, *parse_arg_multiple(32, reg1, reg2, comp_reg))

    @staticmethod
    def execute_on(computer, arg1: Int, arg2: Int, data: Int):
        comp_reg = data >> 11
        if computer.debug_mode:
            print(f"comp reg_1={arg1}, reg_2={arg2}, comp_reg={comp_reg}")
        if computer.debug_mode: print(f"compare {arg1=}, {arg2=}, {comp_reg=}")
        computer.comp_reg[comp_reg] = computer.data_regs[arg1] == computer.data_regs[arg2]


instructions = [Nop, Halt, Add, Sub, Load, Store, Comp, Jump, Print]
