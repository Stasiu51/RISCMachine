from computer import Computer
# not working yet
code = """
LOAD 6 2 IM HLF
ADD 2 0 3

ADD 2 4 4
SUB 3 1 3
COMP 3 0 1
JUMP 1 3 DEC

SUB 2 1 2
COMP 2 0 0
JUMP 0 7 DEC
PRINT 4 0 0
HALT
"""

Computer.assemble_and_run(code)
