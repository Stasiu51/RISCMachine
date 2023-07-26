from numpy import uint32 as Int
from numpy import ndarray as Array
ZERO, ONE, ONES, HALF_ONES, SIG_HALF_ONES = Int(0), Int(1), ~Int(0), Int((2<<15)-1), Int(((2<<15)-1)<<16)

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
OPCODE_MASK = Mask(0b111111_00000_00000_0000000000000000, 26)
ARG1_MASK = Mask(0b000000_11111_00000_0000000000000000, 21)
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
OPCODE_PRINT = Int(0b111111)

RUNNING_FLAG_MASK = Mask(0b1, 0)
CARRY_FLAG_MASK = Mask(0b10, 1)
OVERFLOW_FLAG_MASK = Mask(0b100, 0)

HALF_COPY_FLAG_MASK = Mask(0b10000, 0)
SIGNIFICANT_SRC_FLAG_MASK = Mask(0b01000, 0)
SIGNIFICANT_DST_FLAG_MASK = Mask(0b00100, 0)
OVERWRITE_FLAG_MASK = Mask(0b00010, 0)
IMMEDIATE_FLAG_MASK = Mask(0b00001, 0)

JUMP_CONDITION_FLAG = Mask(0b10000, 0)
JUMP_SUBTRACT_FLAG = Mask(0b01000, 0)
