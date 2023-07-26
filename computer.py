import numpy as np
from typing import Dict, Callable
Int, Array = np.uint32, np.ndarray #Type Alias
ZERO, ONE, ONES, HALF_ONES, SIG_HALF_ONES = Int(0), Int(1), ~Int(0), Int((2<<15)-1), Int(((2<<15)-1)<<16)
print(bin(HALF_ONES),bin(SIG_HALF_ONES))


class Mask:
    def __init__(self, mask, shift):
        self.mask = Int(mask)
        self.shift = Int(shift)

    def get(self, var):
        return (var & self.mask) >> self.shift
    
    def set(self, var, value):
        return (var & ~self.mask) | (value << self.shift)

N_DATA_REGISTERS = 32
MEMORY_SIZE_DEFAULT = 2 << 16
OPCODE_MASK = Mask(0b111111_00000_00000_0000000000000000,26)
ARG1_MASK = Mask(0b000000_11111_00000_0000000000000000,21)
ARG2_MASK = Mask(0b000000_00000_11111_0000000000000000, 16)
DATA_MASK = Mask(0b000000_00000_00000_1111111111111111, 0)

OPCODE_NOP = Int(0b000000)
OPCODE_HALT = Int(0b000001)
OPCODE_CMP = Int(0b000010)
OPCODE_JMP = Int(0b000011)
OPCODE_LOAD = Int(0b000100)
OPCODE_STORE = Int(0b000101)
OPCODE_ADD = Int(0b001001)
OPCODE_SUB = Int(0b001010)
OPCODE_DEBUG = Int(0b111111)

RUNNING_FLAG_MASK = Mask(1,0)
CARRY_FLAG_MASK = Mask(1,1)

IMMEDIATE_LOAD_FLAG_MASK = Mask(0b10000,0)
SIGNIFICANT_LOAD_FLAG_MASK = Mask(0b01000,0)
OVERWRITE_LOAD_FLAG_MASK = Mask(0b00100,0)

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
            OPCODE_DEBUG: self.debug,
            OPCODE_LOAD: self.load,
            OPCODE_STORE: self.store
        }
        self.debug_callbacks = {ZERO: lambda arg1,arg2,data: print(
            f"Debug: {arg1=:05b},{arg2=:05b},{data=:016b}")} # Default debug print behaviour
    
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

    def execute(self):
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
        print("nop")
        pass
     
    def halt(self, arg1, arg2, data):
        print("halt")
        # halt the computer
        self.status_reg = RUNNING_FLAG_MASK.set(self.status_reg, ZERO)
    
    def debug(self,arg1, arg2, data):
        print(f"debug, {bin(arg1)}")
        if arg1 not in self.debug_callbacks:
            raise DecodingError(f"No matching debug callback for argument {arg1}.")
        self.debug_callbacks[arg1](arg1,arg2,data)

    def load(self, register, control_flags, adrs_or_data):
        print(f"load {register}, {control_flags:05b}, {adrs_or_data}")
        if register <= 1:
            print(f"Warning: attempted to write to read-only register {register}.")
            return
        if not IMMEDIATE_LOAD_FLAG_MASK.get(control_flags):
        # Load from memory
            if not 0 <= adrs_or_data < self.memory_size:
                raise SegmentationFaultError(f"Attempted to read from address {adrs_or_data}, which is out of range.")
            self.data_regs[register] = self.memory[adrs_or_data]
            return

        # Immediate Load from Instruction
        if SIGNIFICANT_LOAD_FLAG_MASK.get(control_flags):
            if OVERWRITE_LOAD_FLAG_MASK.get(control_flags):
                self.data_regs[register] = adrs_or_data << 16
            else:
                self.data_regs[register] = (self.data_regs[control_flags] & HALF_ONES) | (adrs_or_data << 16)
        else:
            if OVERWRITE_LOAD_FLAG_MASK.get(control_flags):
                self.data_regs[register] = adrs_or_data
            else:
                print('wo')
                self.data_regs[register] = (self.data_regs[register] & SIG_HALF_ONES) | adrs_or_data


    def store(self, register, _, address):
        print(f"store {register}, {address}")
        if not 0 <= address < self.memory_size:
            raise SegmentationFaultError(f"Attempted to write to address {address}, which is out of range.")
        self.memory[address] = self.data_regs[register]












        
c = Computer()
program = np.array([
    0b000000_00000_00000_0000000000000000,
    0b000100_00010_11000_0101010101010101,
    0b000101_00010_00000_0000000000001000,
    0b000001_00000_00000_0000000000000000,
],dtype = Int)
c.set_memory_chunk(0,program)
# c.set_debug_callbacks(df)
c.execute()
print(1)