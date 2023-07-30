"""
This file contains the implementation of the computer as per the specification in the README.
"""

import numpy as np
from typing import Dict, Callable
from computer_core.constants import *
from computer_core.memories import Memory, DataRegisterArray
from bitarray import bitarray
from computer_core.instructions import instructions


class Computer:
    def __init__(self, memory_size=MEMORY_SIZE_MAX):
        # Data registers
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
        self.debug_mode = False

    def set_memory_chunk(self, address, data):
        """
        Set a chunk of memory, useful for loading programs
        """
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
            machine_code_instruction = self.memory[self.PC]

            # Decode and execute
            opcode, arg1, arg2, data = Computer.decode(machine_code_instruction)
            for instruction in instructions:
                if opcode == instruction.opcode():
                    instruction.execute_on(self, arg1, arg2, data)
                    break
            else:
                raise DecodingError(f"Invalid opcode: {bin(opcode)}.")

            # Increase PC
            self.PC += 1  # Note that this will happen regardless of jump