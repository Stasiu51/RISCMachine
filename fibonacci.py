from computer import Computer

code = """
LOAD 1 2 IM HLF
LOAD 1 3 IM HLF
LOAD 10 5 IM HLF
PRINT 2 3 0

ADD 2 3 4
ADD 3 0 2
ADD 4 0 3
PRINT 4 5 0
SUB 5 1 5
COMP 5 0 0
JUMP 0 6 DEC

HALT
"""

Computer.assemble_and_run(code)
