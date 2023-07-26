import numpy as np
from typing import Dict, Callable
from constants import *
from assembler import assemble

class SegmentationFaultError(Exception):
    pass

class DecodingError(Exception):
    pass

class Computer:
    def __init__(self, memory_size = MEMORY_SIZE_DEFAULT):
        self.data_regs = np.zeros(N_DATA_REGISTERS,dtype = Int)
        self.data_regs[1] = ONE
        self.comp_reg = Int(0) # For the result of logical operations such as CMP
        self.status_reg = Int(0) # For other status bits, such as `running' and carry flags
        self.PC = np.uint16(0)
        self.memory = np.zeros(memory_size, dtype = Int)
        self.memory_size = memory_size
        self.opcode_functions: Dict[Int, Callable] = {
            OPCODE_NOP: self.nop,
            OPCODE_HALT: self.halt,
            OPCODE_PRINT: self.print,
            OPCODE_LOAD: self.load,
            OPCODE_STORE: self.store,
            OPCODE_JMP: self.jump,
            OPCODE_ADD: self.add,
            OPCODE_SUB: self.sub,
            OPCODE_CMP: self.cmp
        }
        self.debug_mode = False

    @staticmethod
    def assemble_and_run(code, debug_mode = False):
        computer = Computer()
        program_data = assemble(code)
        computer.set_memory_chunk(0, program_data)
        computer.execute(debug_mode = debug_mode)
    
    def set_memory_chunk(self, address, data):
        if not 0 <= address < self.memory_size:
            raise SegmentationFaultError("Address not within memory")
        if type(data) is not Array:#or data.dtype != Int:
            raise TypeError("Program data should be a numpy array of type uint32")
        if not 0 <= data.size < self.memory_size:
            raise SegmentationFaultError("Data is too large for memory.")
        
        self.memory[address: address + data.size] = data

    def set_debug_callbacks(self, debug_callbacks):
        if type(debug_callbacks) is not dict:
            raise TypeError("debug_callbacks should be a dictionary of functions indexed by uint32.")
        self.debug_callbacks = debug_callbacks
    
    def set_memory_address(self, address, value):
        if not 0 <= address < self.memory_size:
            raise SegmentationFaultError("Attempted to write to invalid address")
        if type(value) is not Int:
            raise TypeError("Value should have type uint32")
        self.memory[address] = value
    
    def read_memory_address(self, address) -> Int:
        if not 0 <= address < self.memory_size:
            raise SegmentationFaultError("Attempted to write to invalid address")
        return self.memory[address]


    def execute(self, debug_mode = False):
        self.debug_mode = debug_mode
        self.status_reg = RUNNING_FLAG_MASK.set(self.status_reg, ONE)

        while RUNNING_FLAG_MASK.get(self.status_reg):
            #Fetch
            instruction = self.memory[self.PC]

            #Decode
            opcode = OPCODE_MASK.get(instruction)
            arg1 = ARG1_MASK.get(instruction)
            arg2 = ARG2_MASK.get(instruction)
            data = DATA_MASK.get(instruction)
            if not opcode in self.opcode_functions:
                raise DecodingError(f"Invalid opcode: {bin(opcode)}.")

            #Execute
            if self.opcode_functions[opcode](arg1, arg2, data):
                return

            #Increase PC
            self.PC += 1 #Note that this will happen regardless of jump

    # Functions for instructions. Take the decoded arguments and return whether the computer should halt execution.

    def nop(self, arg1, arg2, data):
        if self.debug_mode: print("nop")
        pass
     
    def halt(self, arg1, arg2, data):
        if self.debug_mode: print("halt")
        # halt the computer
        self.status_reg = RUNNING_FLAG_MASK.set(self.status_reg, ZERO)

    def print(self, register_1, register_2, address):
        if not 0 <= address < self.memory_size:
            raise SegmentationFaultError(f"Attempted to print from address {address}, which is out of range.")
        print(f"print: register {register_1}: {self.data_regs[register_1]:032b} = {self.data_regs[register_1]}, "
              f"register {register_2}: {self.data_regs[register_2]:032b} = {self.data_regs[register_2]}, "
              f"address {address}: {self.memory[address]:032b} = {self.memory[address]}")

    def load(self, register, control_flags, adrs_or_data):
        if self.debug_mode: print(f"load {register}, {control_flags:05b}, {adrs_or_data}")
        if register <= 1:
            print(f"Warning: attempted to load to register {register} which is read-only.")
            return
        if IMMEDIATE_FLAG_MASK.get(control_flags): #Immediate mode, instruction itself is source
            source_bits = self.memory[self.PC]
        else: # Load from memory
            if not 0 <= adrs_or_data < self.memory_size:
                raise SegmentationFaultError(f"Attempted to read from address {adrs_or_data}, which is out of range.")
            source_bits = self.memory[adrs_or_data]

        if not HALF_COPY_FLAG_MASK.get(control_flags): # moving all 32 bits
            self.data_regs[register] = source_bits
            return

        # moving only 16 bits
        if SIGNIFICANT_SRC_FLAG_MASK.get(control_flags):
            half_source_bits = (SIG_HALF_ONES & source_bits) >> 16
        else:
            half_source_bits = HALF_ONES & source_bits

        if SIGNIFICANT_DST_FLAG_MASK.get(control_flags):
            if OVERWRITE_FLAG_MASK.get(control_flags):
                self.data_regs[register] = (half_source_bits << 16) # Overwrite all the bits
            else:
                self.data_regs[register] = (half_source_bits << 16) | (self.data_regs[register] & HALF_ONES) # Overwrite only the 16 affected bits
        else:
            if OVERWRITE_FLAG_MASK.get(control_flags):
                self.data_regs[register] = half_source_bits
            else:
                self.data_regs[register] = half_source_bits | (self.data_regs[register] & SIG_HALF_ONES)

    def store(self, register, control_flags, adrs_or_data):
        if self.debug_mode: print(f"store {register}, {control_flags:05b}, {adrs_or_data}")

        if not 0 <= adrs_or_data < self.memory_size:
            raise SegmentationFaultError(f"Attempted to write to address {adrs_or_data}, which is out of range.")

        if IMMEDIATE_FLAG_MASK.get(control_flags):  # Immediate mode, instruction itself is source
            source_bits = self.memory[self.PC]
        else:  # Load from memory
            source_bits = self.data_regs[register]

        if not HALF_COPY_FLAG_MASK.get(control_flags):  # moving all 32 bits
            self.memory[adrs_or_data] = source_bits
            return

        # moving only 16 bits
        if SIGNIFICANT_SRC_FLAG_MASK.get(control_flags):
            half_source_bits = (SIG_HALF_ONES & source_bits) >> 16
        else:
            half_source_bits = HALF_ONES & source_bits

        if SIGNIFICANT_DST_FLAG_MASK.get(control_flags):
            if OVERWRITE_FLAG_MASK.get(control_flags): # Overwrite all the bits
                self.memory[adrs_or_data] = (half_source_bits << 16)
            else: # Overwrite only the 16 affected bits
                self.memory[adrs_or_data] = (half_source_bits << 16) | (self.data_regs[register] & HALF_ONES)
        else:
            if OVERWRITE_FLAG_MASK.get(control_flags):
                self.memory[adrs_or_data] = half_source_bits
            else:
                self.memory[adrs_or_data] = half_source_bits | (self.data_regs[register] & SIG_HALF_ONES)

    def jump(self, control_register, control_flags, jump_amount):
        if self.debug_mode: print(f"jump {control_register=}, {control_flags=:05b}, {jump_amount=}")
        if (self.comp_reg >> control_register) & 1 == JUMP_CONDITION_FLAG.get(control_flags):
            # subtract 1 for convenience as the computer will add one at the end of the cycle
            new_PC = self.PC - jump_amount - 1 if JUMP_SUBTRACT_FLAG.get(control_flags) else self.PC + jump_amount - 1
            if not 0 <= self.PC < self.memory_size:
                raise SegmentationFaultError(f"Attempted to move program counter to {new_PC}, which is out of bounds.")
            self.PC = new_PC

    def add(self, reg_1, reg_2, reg_3_data):
        reg_3 = reg_3_data >> 11
        if self.debug_mode: print(f"add {reg_1=}, {reg_2=}, {reg_3=}")
        if reg_3 <= 1:
            print(f"Warning: attempted to add into register {reg_3} which is read-only.")
            return
        if int(self.data_regs[reg_1]) + int(self.data_regs[reg_2]) >= 2<<31: # Overflow occurred.
            print("Warning: integer overflow. Flag set.")
            self.status_reg = OVERFLOW_FLAG_MASK.set(self.status_reg, ONE)
        else:
            self.status_reg = OVERFLOW_FLAG_MASK.set(self.status_reg, ZERO)
        self.data_regs[reg_3] = self.data_regs[reg_1] + self.data_regs[reg_2]


    def sub(self, reg_1, reg_2, reg_3_data):
        reg_3 = reg_3_data >> 11
        if self.debug_mode: print(f"sub {reg_1=}, {reg_2=}, {reg_3=}")
        if reg_3 <= 1:
            print(f"Warning: attempted to subtract into register {reg_3} which is read-only.")
            return
        if int(self.data_regs[reg_1]) - int(self.data_regs[reg_2]) < 0: # Underflow occurred.
            print("Warning: integer underflow. Flag set.")
            self.status_reg = OVERFLOW_FLAG_MASK.set(self.status_reg, ONE)
        else:
            self.status_reg = OVERFLOW_FLAG_MASK.set(self.status_reg, ZERO)
        self.data_regs[reg_3] = self.data_regs[reg_1] - self.data_regs[reg_2]

    def cmp(self, reg_1, reg_2, comp_reg_data):
        comp_reg = comp_reg_data >> 11
        if self.debug_mode: print(f"compare {reg_1=}, {reg_2=}, {comp_reg=}")
        mask = ~Int(0b1 << comp_reg)
        value = Int(self.data_regs[reg_1] == self.data_regs[reg_2])
        self.comp_reg = (self.comp_reg & mask) | value << comp_reg















        

print(1)