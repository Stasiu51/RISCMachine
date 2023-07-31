from numpy import uint32 as Int
from numpy import ndarray as Array
ZERO, ONE, ONES, HALF_ONES, SIG_HALF_ONES = Int(0), Int(1), ~Int(0), Int((1<<16)-1), Int(((1<<16)-1)<<16)

class Mask:
    def __init__(self, mask, shift):
        self.mask = Int(mask)
        self.shift = Int(shift)

    def get(self, var):
        return (var & self.mask) >> self.shift

    def set(self, var, value):
        return (var & ~self.mask) | (value << self.shift)


N_DATA_REGISTERS = 32
MEMORY_SIZE_MAX = 1 << 16
CACHE_SECTION_RESPONSIBILITY = MEMORY_SIZE_MAX // 32
CACHE_SECTION_SIZE = 8

CACHE_SECTION_INDEX_MASK = Mask(0b11111_00000000000, 11)

OPCODE_MASK = Mask(0b111111_00000_00000_0000000000000000, 26)
ARG1_MASK = Mask(0b000000_11111_00000_0000000000000000, 21)
ARG2_MASK = Mask(0b000000_00000_11111_0000000000000000, 16)
DATA_MASK = Mask(0b000000_00000_00000_1111111111111111, 0)

# Core instructions
OPCODE_NOP = Int(0b000_000)
OPCODE_HALT = Int(0b000_001)

OPCODE_ADD = Int(0b001_001)
OPCODE_SUB = Int(0b001_010)

OPCODE_COMP = Int(0b010_000)

OPCODE_LOAD = Int(0b011_001)
OPCODE_STORE = Int(0b011_010)

OPCODE_JMP = Int(0b100_001)

OPCODE_PRINT = Int(0b111_111)

# Extension Instructions

OPCODE_LSHIFT = Int(0b001_011)
OPCODE_RSHIFT = Int(0b001_100)

OPCODE_COMPGRT = Int(0b010_010)
OPCODE_COMPLST = Int(0b010_011)

RUNNING_FLAG_INDEX = 0
OVERFLOW_FLAG_INDEX = 1

HALF_COPY_FLAG_INDEX = 4
SIGNIFICANT_SRC_FLAG_INDEX = 3
SIGNIFICANT_DST_FLAG_INDEX = 2
OVERWRITE_FLAG_INDEX = 1
IMMEDIATE_FLAG_INDEX = 0

JUMP_CONDITION_INDEX = 4
JUMP_SUBTRACT_INDEX = 3

INSTRUCTION_TIME_NS = 1
CACHE_HIT_TIME_NS = 1
CACHE_MISS_TIME_NS = 70

class SegmentationFaultError(Exception):
    pass


class DecodingError(Exception):
    pass
