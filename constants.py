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

OPCODE_NOP = Int(0b000000)
OPCODE_HALT = Int(0b000001)
OPCODE_CMP = Int(0b000010)
OPCODE_JMP = Int(0b000011)
OPCODE_LOAD = Int(0b000100)
OPCODE_STORE = Int(0b000101)
OPCODE_ADD = Int(0b001001)
OPCODE_SUB = Int(0b001010)
OPCODE_PRINT = Int(0b111111)

RUNNING_FLAG_INDEX = 0
OVERFLOW_FLAG_INDEX = 1

HALF_COPY_FLAG_INDEX = 4
SIGNIFICANT_SRC_FLAG_INDEX = 3
SIGNIFICANT_DST_FLAG_INDEX = 2
OVERWRITE_FLAG_INDEX = 1
IMMEDIATE_FLAG_INDEX = 0

JUMP_CONDITION_INDEX = 4
JUMP_SUBTRACT_INDEX = 3

class SegmentationFaultError(Exception):
    pass


class DecodingError(Exception):
    pass
