"""
This file contains the implementation of the computer as per the specification in the README.
"""

import numpy as np
from typing import Dict, Callable
from constants import *
from assembler import assemble
from memories import Memory, DataRegisterArray
from bitarray import bitarray
from bitarray.util import int2ba


class Computer:
    def __init__(self, memory_size=MEMORY_SIZE_DEFAULT):
        # 32, 32-bit data registers
        # self.data_regs = np.zeros(N_DATA_REGISTERS, dtype=Int)
        # the second register is always one
        # self.data_regs[1] = ONE
        self.data_regs = DataRegisterArray()
        # COMP register, for the result of logical operations such as CMP
        self.comp_reg = bitarray('0'*32, endian='little')
        # Status register, for other status bits, such as `running' and overflow flags
        self.status_reg = bitarray('0'*32, endian='little')
        # Program counter
        self.PC = np.uint16(0)
        # (Unified) Memory
        self.memory = Memory(memory_size)
        self.memory_size = memory_size
        # Functions to be called by the instructions
        self.opcode_functions: Dict[Int, Callable] = {
            OPCODE_NOP: self.nop,
            OPCODE_HALT: self.halt,
            OPCODE_PRINT: self.print,
            OPCODE_LOAD: self.load,
            OPCODE_STORE: self.store,
            OPCODE_JMP: self.jump,
            OPCODE_ADD: self.add,
            OPCODE_SUB: self.sub,
            OPCODE_CMP: self.comp
        }
        self.debug_mode = False

    @staticmethod
    def assemble_and_run(code, debug_mode=False):
        """
        Helper function to quickly run a program from assembly code
        """
        computer = Computer()
        program_data = assemble(code)
        computer.set_memory_chunk(0, program_data)
        computer.execute(debug_mode=debug_mode)

    def set_memory_chunk(self, address, data):
        """
        Set a chunk of memory, useful for loading programs
        """
        if not 0 <= address < self.memory_size:
            raise SegmentationFaultError("Address not within memory")
        if type(data) is not Array or data.dtype != Int:
            raise TypeError("Program data should be a numpy array of type uint32")
        if not 0 <= address + data.size <= self.memory_size:
            raise SegmentationFaultError("Data is too large for memory.")

        self.memory[address: address + data.size] = data

    def set_memory_address(self, address, value):
        """
        Set a single address in memory, useful for loading program arguments
        """
        self.memory[address] = value

    def get_memory_address(self, address) -> Int:
        """
        Get a single address in memory, useful for reading program outputs
        """
        return self.memory[address]

    @staticmethod
    def decode(instruction):
        """
        Split an instruction into opcode and arguments
        """
        return OPCODE_MASK.get(instruction), ARG1_MASK.get(instruction), \
            ARG2_MASK.get(instruction), DATA_MASK.get(instruction)

    def execute(self, debug_mode=False):
        """
        Main execution loop for running a program. Follows fetch-decode-execute cycle.
        """
        self.debug_mode = debug_mode
        # Set 'running' flag
        self.status_reg[RUNNING_FLAG_INDEX] = True

        while self.status_reg[RUNNING_FLAG_INDEX]:
            # Fetch
            if not 0 <= self.PC < self.memory_size:
                raise SegmentationFaultError(
                    f"Attempted to load instruction from address {self.PC}, which is out of bounds.")
            instruction = self.memory[self.PC]

            # Decode
            opcode, arg1, arg2, data = Computer.decode(instruction)
            if not opcode in self.opcode_functions:
                raise DecodingError(f"Invalid opcode: {bin(opcode)}.")

            # Execute
            self.opcode_functions[opcode](arg1, arg2, data)

            # Increase PC
            self.PC += 1  # Note that this will happen regardless of jump

    #
    # Functions for instructions. Take the decoded arguments and return whether the computer should halt execution.
    #

    def nop(self, arg1, arg2, data):
        """ Do nothing. """
        if self.debug_mode: print("nop")
        pass

    def halt(self, arg1, arg2, data):
        """ Stop execution by resetting the 'running' flag. """
        if self.debug_mode: print("halt")
        self.status_reg[RUNNING_FLAG_INDEX] = False

    def print(self, register_1, register_2, address):
        """
        Print the contents of data registers with indices register_1, register_2 and the memory at the given address.
        """
        print(f"print: register {register_1}: {self.data_regs[register_1]:032b} = {self.data_regs[register_1]}, "
              f"register {register_2}: {self.data_regs[register_2]:032b} = {self.data_regs[register_2]}, "
              f"address {address}: {self.memory[address]:032b} = {self.memory[address]}")

    def load(self, register, control_flags_int, adrs_or_data):
        """
        Load data from memory or the instruction itself into a data register.
        For a complete description of the flags, see the README.
        """
        if self.debug_mode: print(f"load {register}, {control_flags_int:05b}, {adrs_or_data}")
        control_flags = int2ba(int(control_flags_int), endian = 'little',length=5)
        if register <= 1:
            print(f"Warning: attempted to load to register {register} which is read-only.")
            return

        if control_flags[IMMEDIATE_FLAG_INDEX]:  # Immediate mode, instruction itself is source
            source_bits = self.memory[self.PC]
        else:  # Load from memory
            if not 0 <= adrs_or_data < self.memory_size:
                raise SegmentationFaultError(f"Attempted to read from address {adrs_or_data}, which is out of range.")
            source_bits = self.memory[adrs_or_data]

        if not control_flags[HALF_COPY_FLAG_INDEX]:  # moving all 32 bits
            self.data_regs[register] = source_bits
            return

        # moving only 16 bits
        if control_flags[SIGNIFICANT_SRC_FLAG_INDEX]:
            half_source_bits = (SIG_HALF_ONES & source_bits) >> 16
        else:
            half_source_bits = HALF_ONES & source_bits

        if control_flags[SIGNIFICANT_DST_FLAG_INDEX]:
            if control_flags[OVERWRITE_FLAG_INDEX]:
                self.data_regs[register] = Int(half_source_bits << 16)  # Overwrite all the bits
            else:
                # Overwrite only the 16 affected bits
                self.data_regs[register] = Int((half_source_bits << 16) | (self.data_regs[register] & HALF_ONES))
        else:
            if control_flags[OVERWRITE_FLAG_INDEX]:
                self.data_regs[register] = Int(half_source_bits)
            else:
                self.data_regs[register] = Int(half_source_bits | (self.data_regs[register] & SIG_HALF_ONES))

    def store(self, register, control_flags_int, adrs_or_data):
        """
        Store data from a data register or the instruction itself into an address in memory.
        For a complete description of the flags, see the README.
        """
        if self.debug_mode: print(f"store {register}, {control_flags_int:05b}, {adrs_or_data}")
        control_flags = int2ba(int(control_flags_int), endian='little', length=5)

        if not 0 <= adrs_or_data < self.memory_size:
            raise SegmentationFaultError(f"Attempted to write to address {adrs_or_data}, which is out of range.")

        if control_flags[IMMEDIATE_FLAG_INDEX]:  # Immediate mode, instruction itself is source
            source_bits = self.memory[self.PC]
        else:  # Load from memory
            source_bits = self.data_regs[register]

        if not control_flags[HALF_COPY_FLAG_INDEX]:  # moving all 32 bits
            self.memory[adrs_or_data] = source_bits
            return

        # moving only 16 bits
        if control_flags[SIGNIFICANT_SRC_FLAG_INDEX]:
            half_source_bits = (SIG_HALF_ONES & source_bits) >> 16
        else:
            half_source_bits = HALF_ONES & source_bits

        if control_flags[SIGNIFICANT_DST_FLAG_INDEX]:
            if control_flags[OVERWRITE_FLAG_INDEX]:  # Overwrite all the bits
                self.memory[adrs_or_data] = Int(half_source_bits << 16)
            else:  # Overwrite only the 16 affected bits
                self.memory[adrs_or_data] = Int((half_source_bits << 16) | (self.memory[adrs_or_data] & HALF_ONES))
        else:
            if control_flags[OVERWRITE_FLAG_INDEX]:
                self.memory[adrs_or_data] = Int(half_source_bits)
            else:
                self.memory[adrs_or_data] = Int(half_source_bits | (self.memory[adrs_or_data] & SIG_HALF_ONES))

    def jump(self, control_register, control_flags_int, jump_amount):
        """
        A conditional relative jump, performed by modifying the program counter.
        """
        if self.debug_mode: print(f"jump {control_register=}, {control_flags_int=:05b}, {jump_amount=}")
        control_flags = int2ba(int(control_flags_int), endian='little', length=5)
        if self.comp_reg[control_register] == control_flags[JUMP_CONDITION_INDEX]:
            # subtract 1 for convenience as the computer will add one at the end of the cycle
            new_PC = self.PC - jump_amount - 1 if control_flags[JUMP_SUBTRACT_INDEX] else self.PC + jump_amount - 1
            if not 0 <= new_PC < self.memory_size:
                raise SegmentationFaultError(f"Attempted to move program counter to {new_PC}, which is out of bounds.")
            self.PC = new_PC

    def add(self, reg_1, reg_2, reg_3_data):
        """
        Add the contents of reg_1 and the contents of reg_2 and store the result in reg_3.
        In case of overflow, set the relevant status bit.
        """
        reg_3 = reg_3_data >> 11
        if self.debug_mode: print(f"add {reg_1=}, {reg_2=}, {reg_3=}")
        if reg_3 <= 1:
            print(f"Warning: attempted to add into register {reg_3} which is read-only.")
            return
        if int(self.data_regs[reg_1]) + int(self.data_regs[reg_2]) >= 1 << 32:  # Overflow occurred.
            print("Warning: integer overflow. Flag set.")
            self.status_reg[OVERFLOW_FLAG_INDEX] = True
        else:
            self.status_reg[OVERFLOW_FLAG_INDEX] = False
        self.data_regs[reg_3] = self.data_regs[reg_1] + self.data_regs[reg_2]

    def sub(self, reg_1, reg_2, reg_3_data):
        """
        Subtract the contents of reg_2 from the contents of reg_1 and store the result in reg_3.
        In case of underflow, set the relevant status bit.
        """
        reg_3 = reg_3_data >> 11
        if self.debug_mode: print(f"sub {reg_1=}, {reg_2=}, {reg_3=}")
        if reg_3 <= 1:
            print(f"Warning: attempted to subtract into register {reg_3} which is read-only.")
            return
        if int(self.data_regs[reg_1]) - int(self.data_regs[reg_2]) < 0:  # Underflow occurred.
            print("Warning: integer underflow. Flag set.")
            self.status_reg[OVERFLOW_FLAG_INDEX] = True
        else:
            self.status_reg[OVERFLOW_FLAG_INDEX] = False
        self.data_regs[reg_3] = self.data_regs[reg_1] - self.data_regs[reg_2]

    def comp(self, reg_1, reg_2, comp_reg_data):
        """
        Compare the contents of reg_2 and the contents of reg_1 and set the specified bit in the COMP_REG.
        """
        comp_reg = comp_reg_data >> 11
        if self.debug_mode: print(f"compare {reg_1=}, {reg_2=}, {comp_reg=}")
        self.comp_reg[comp_reg] = self.data_regs[reg_1] == self.data_regs[reg_2]









