from assembler import assemble
import numpy as np

code = """
NOP
ADD 4 5 6
SUB 7 8 9
LOAD 10 11 FROM_SIG TO_SIG
STORE 13 14 HLF FROM_SIG TO_SIG OW IM
JUMP 16 17 DEC ON_HIGH
COMP 20 21 22
HALT

"""
print(np.vectorize(np.binary_repr)(assemble(code), width=32))