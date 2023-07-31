import unittest, bitarray, sys, io
import numpy as np
from computer_core import instructions, computer, constants
from computer_core.constants import Int


class TestInstructions(unittest.TestCase):
    def test_print(self):
        """
        Test that the print function correctly prints two registers and an address in memory
        """
        c = computer.Computer()
        c.memory[4] = Int(0b11110000111100001111000011110000)
        c.data_regs[2] = Int(0b11001100110011001100110011001100)
        c.data_regs[3] = Int(0b10101010101010101010101010101010)
        expected = "print: register 2: 11001100110011001100110011001100 = 3435973836," + \
                   " register 3: 10101010101010101010101010101010 = 2863311530," + \
                   " address 4: 11110000111100001111000011110000 = 4042322160\n"

        redirect = io.StringIO()  # Create StringIO object
        sys.stdout = redirect  # and redirect stdout.
        instructions.Print.execute_on(c, 2, 3, 4)
        sys.stdout = sys.__stdout__

        self.assertEqual(redirect.getvalue(), expected)

    def test_print_error(self):
        """
        Test for segfault when attempting to print out of bounds
        """
        c = computer.Computer(memory_size=10)
        with self.assertRaises(computer.SegmentationFaultError):
            instructions.Print.execute_on(c, 0, 0, -1)
        with self.assertRaises(computer.SegmentationFaultError):
            instructions.Print.execute_on(c, 0, 0, 10)

    def test_load(self):
        """
        Tests the various functionalities of the load instruction
        """

        def combine(x, y):
            return Int((x << 16) | y)

        A, B, C, D, E, F = np.linspace(1 << 15, (1 << 16) - 1, 6).astype(Int)

        starting_ins = combine(A, B)
        starting_reg = combine(C, D)
        starting_mem = combine(E, F)

        c = computer.Computer(memory_size=2)
        c.memory[INS := 0] = starting_ins
        c.memory[MEM := 1] = starting_mem
        c.data_regs[2:] = starting_reg

        # full load from memory
        REG = 3
        expected = combine(E, F)
        instructions.Load.execute_on(c, REG, 0b00000, MEM)
        self.assertEqual(c.data_regs[REG], expected)

        # low sig to low sig half load from memory
        REG = 4
        expected = combine(C, F)
        instructions.Load.execute_on(c, REG, 0b10000, MEM)
        self.assertEqual(c.data_regs[REG], expected)

        # low sig to high sig half load from memory
        REG = 5
        expected = combine(F, D)
        instructions.Load.execute_on(c, REG, 0b10100, MEM)
        self.assertEqual(c.data_regs[REG], expected)

        # high sig to low sig half load from memory
        REG = 6
        expected = combine(C, E)
        instructions.Load.execute_on(c, REG, 0b11000, MEM)
        self.assertEqual(c.data_regs[REG], expected)

        # low sig to low sig half load from memory with overwrite
        REG = 7
        expected = combine(0, F)
        instructions.Load.execute_on(c, REG, 0b10010, MEM)
        self.assertEqual(c.data_regs[REG], expected)

        # high sig to high sig half load from memory with overwrite
        REG = 8
        expected = combine(E, 0)
        instructions.Load.execute_on(c, REG, 0b11110, MEM)
        self.assertEqual(c.data_regs[REG], expected)

        # full load from instruction (immediate)
        REG = 9
        expected = combine(A, B)
        instructions.Load.execute_on(c, REG, 0b00001, MEM)
        self.assertEqual(c.data_regs[REG], expected)

        # low sig to low sig half load from instruction (immediate) with overwrite
        REG = 9
        expected = combine(0, B)
        instructions.Load.execute_on(c, REG, 0b10011, MEM)
        self.assertEqual(c.data_regs[REG], expected)

        # low sig to high sig half load from instruction (immediate) with overwrite
        REG = 10
        expected = combine(B, 0)
        instructions.Load.execute_on(c, REG, 0b10111, MEM)
        self.assertEqual(c.data_regs[REG], expected)

    def test_load_error(self):
        """
        Test for segfault when loading out-of-bounds memory
        """
        c = computer.Computer(memory_size=10)
        with self.assertRaises(computer.SegmentationFaultError):
            instructions.Load.execute_on(c, 2, 0, -1)

        with self.assertRaises(computer.SegmentationFaultError):
            instructions.Load.execute_on(c, 2, 0, Int(10))

        # Should not be a problem in immediate mode
        instructions.Load.execute_on(c, 2, 0b00001, Int(10))

    def test_store(self):
        """
        Tests the various functionalities of the store instruction
        """

        def combine(x, y):
            return Int((x << 16) | y)

        # Generate some 16-bit numbers
        A, B, C, D, E, F = np.linspace(1 << 15, (1 << 16) - 1, 6).astype(Int)
        starting_ins = combine(A, B)
        starting_reg = combine(C, D)
        starting_mem = combine(E, F)

        c = computer.Computer(memory_size=10)
        c.memory[INS := 0] = starting_ins
        c.memory[1:] = starting_mem
        c.data_regs[REG := 2] = starting_reg

        # full store from register
        MEM = 1
        expected = combine(C, D)
        instructions.Store.execute_on(c, REG, 0b00000, MEM)
        self.assertEqual(c.memory[MEM], expected)

        # low sig to low sig half store from register
        MEM = 2
        expected = combine(E, D)
        instructions.Store.execute_on(c, REG, 0b10000, MEM)
        self.assertEqual(c.memory[MEM], expected)

        # low sig to high sig half store from register
        MEM = 3
        expected = combine(D, F)
        instructions.Store.execute_on(c, REG, 0b10100, MEM)
        self.assertEqual(c.memory[MEM], expected)

        # high sig to low sig half store from register
        MEM = 4
        expected = combine(E, C)
        instructions.Store.execute_on(c, REG, 0b11000, MEM)
        self.assertEqual(c.memory[MEM], expected)

        # low sig to low sig half store from register with overwrite
        MEM = 5
        expected = combine(0, D)
        instructions.Store.execute_on(c, REG, 0b10010, MEM)
        self.assertEqual(c.memory[MEM], expected)

        # high sig to high sig half store from memory with overwrite
        MEM = 6
        expected = combine(C, 0)
        instructions.Store.execute_on(c, REG, 0b11110, MEM)
        self.assertEqual(c.memory[MEM], expected)

        # full store from instruction (immediate)
        MEM = 7
        expected = combine(A, B)
        instructions.Store.execute_on(c, REG, 0b00001, MEM)
        self.assertEqual(c.memory[MEM], expected)

        # low sig to low sig half store from instruction (immediate) with overwrite
        MEM = 8
        expected = combine(0, B)
        instructions.Store.execute_on(c, REG, 0b10011, MEM)
        self.assertEqual(c.memory[MEM], expected)

        # low sig to high sig half store from instruction (immediate) with overwrite
        MEM = 9
        expected = combine(B, 0)
        instructions.Store.execute_on(c, REG, 0b10111, MEM)
        self.assertEqual(c.memory[MEM], expected)

    def test_store_error(self):
        """
        Test for segfault when writing to out-of-bounds memory
        """
        c = computer.Computer(memory_size=10)
        with self.assertRaises(computer.SegmentationFaultError):
            instructions.Store.execute_on(c, 2, 0, -1)

        with self.assertRaises(computer.SegmentationFaultError):
            instructions.Store.execute_on(c, 2, 0, Int(10))

    def test_halt(self):
        """
        Test that halt resets the 'running' flag
        """
        c = computer.Computer()
        c.status_reg[constants.RUNNING_FLAG_INDEX] = True
        instructions.Halt.execute_on(c, Int(0), Int(0), Int(0))

        self.assertEqual(False, c.status_reg[constants.RUNNING_FLAG_INDEX])

    def test_add(self):
        """
        Tests the functionality of the add function, including setting over(under)flow bit
        """
        a = 15
        b = 25
        expected = a + b

        c = computer.Computer(memory_size=10)
        REG1, REG2, REG3 = 2, 3, 4
        c.data_regs[REG1] = a
        c.data_regs[REG2] = b

        instructions.Add.execute_on(c, REG1, REG2, REG3 << 11)
        self.assertEqual(expected, c.data_regs[REG3])
        self.assertEqual(0, c.status_reg[constants.OVERFLOW_FLAG_INDEX])

        # Also test that it can add in-place
        instructions.Add.execute_on(c, REG1, REG2, REG2 << 11)
        self.assertEqual(expected, c.data_regs[REG2])
        self.assertEqual(0, c.status_reg[constants.OVERFLOW_FLAG_INDEX])

        # Test overflow behaviour
        c.data_regs[REG1] = Int((1 << 32) - 1)
        c.data_regs[REG2] = Int(1)
        instructions.Add.execute_on(c, REG1, REG2, REG3 << 11)
        self.assertEqual(1, c.status_reg[constants.OVERFLOW_FLAG_INDEX])

    def test_sub(self):
        """
        Tests the functionality of the sub function, including setting over(under)flow bit
        """
        a = 25
        b = 15
        expected = a - b

        c = computer.Computer()
        REG1, REG2, REG3 = 2, 3, 4
        c.data_regs[REG1] = a
        c.data_regs[REG2] = b

        instructions.Sub.execute_on(c, REG1, REG2, REG3 << 11)
        self.assertEqual(expected, c.data_regs[REG3])
        self.assertEqual(0, c.status_reg[constants.OVERFLOW_FLAG_INDEX])

        # Also test that it subtract in-place
        instructions.Sub.execute_on(c, REG1, REG2, REG2 << 11)
        self.assertEqual(expected, c.data_regs[REG2])
        self.assertEqual(0, c.status_reg[constants.OVERFLOW_FLAG_INDEX])

        # Test underflow behaviour
        instructions.Sub.execute_on(c, REG2, REG1, REG3 << 11)
        self.assertEqual(1, c.status_reg[constants.OVERFLOW_FLAG_INDEX])

    def test_jump(self):
        """
        Test jump behaviour
        """
        c = computer.Computer(memory_size=10)

        # forward jump
        c.PC = 5
        instructions.Jump.execute_on(c, 5, 0b00000, 3)
        self.assertEqual(7, c.PC)  # note the included - 1 due to cycle increment

        # backward jump
        c.PC = 5
        instructions.Jump.execute_on(c, 5, 0b01000, 3)
        self.assertEqual(1, c.PC)

        # don't jump if comp bit is required and not set
        c.PC = 5
        instructions.Jump.execute_on(c, 5, 0b10000, 3)
        self.assertEqual(5, c.PC)

        # ...but do when it is set
        c.comp_reg[5] = True
        c.PC = 5
        instructions.Jump.execute_on(c, 5, 0b10000, 3)
        self.assertEqual(7, c.PC)

        # test subtract again
        c.PC = 5
        instructions.Jump.execute_on(c, 5, 0b11000, 3)
        self.assertEqual(1, c.PC)

    def test_jump_error(self):
        """
        Test that jump segfaults when jumping to out of bounds address
        """
        c = computer.Computer(memory_size=10)

        # forwards jump
        c.PC = 5
        with self.assertRaises(computer.SegmentationFaultError):
            instructions.Jump.execute_on(c, 5, 0b00000, 6)

        # backwards jump
        c.PC = 5
        with self.assertRaises(computer.SegmentationFaultError):
            instructions.Jump.execute_on(c, 5, 0b01000, 5)

    def test_comp(self):
        """
        Test function of compare instruction
        """
        c = computer.Computer(memory_size=10)

        a, b = 10, 15
        REG1, REG2, REG3 = 2, 3, 4
        c.data_regs[REG1] = a
        c.data_regs[REG2] = a
        c.data_regs[REG3] = b
        expected = bitarray.bitarray('0' * 32, endian='little')

        # These two are the same
        instructions.Comp.execute_on(c, REG1, REG2, 3 << 11)
        expected[3] = True
        self.assertEqual(expected, c.comp_reg)

        # These are different
        instructions.Comp.execute_on(c, REG1, REG3, 1 << 11)
        self.assertEqual(expected, c.comp_reg)

        # Comparing register to itself should also work
        instructions.Comp.execute_on(c, REG3, REG3, 1 << 11)
        expected[1] = True
        self.assertEqual(expected, c.comp_reg)

    #
    # Extension instructions test
    #

    def test_lshift(self):
        """
        Tests the functionality of the LShift function, including setting over(under)flow bit
        """
        a = 15
        b = 8
        d = 29
        expected = a << b

        c = computer.Computer()
        REG1, REG2, REG3, REG4 = 2, 3, 4, 5
        c.data_regs[REG1] = a
        c.data_regs[REG2] = b
        c.data_regs[REG4] = d

        instructions.LShift.execute_on(c, REG1, REG2, REG3 << 11)
        self.assertEqual(expected, c.data_regs[REG3])
        self.assertEqual(0, c.status_reg[constants.OVERFLOW_FLAG_INDEX])

        # Also test that it shifts in-place
        instructions.LShift.execute_on(c, REG1, REG2, REG2 << 11)
        self.assertEqual(expected, c.data_regs[REG2])
        self.assertEqual(0, c.status_reg[constants.OVERFLOW_FLAG_INDEX])

        # Test overflow behaviour
        instructions.LShift.execute_on(c, REG1, REG4, REG4 << 11)
        self.assertEqual(1, c.status_reg[constants.OVERFLOW_FLAG_INDEX])

    def test_rshift(self):
        """
        Tests the functionality of the RShift function. There is no underflow possibility.
        """
        a = 0b11110000
        b = 5
        expected = a >> b # = 0b111

        c = computer.Computer()
        REG1, REG2, REG3 = 2, 3, 4
        c.data_regs[REG1] = a
        c.data_regs[REG2] = b

        instructions.RShift.execute_on(c, REG1, REG2, REG3 << 11)
        self.assertEqual(expected, c.data_regs[REG3])
        self.assertEqual(0, c.status_reg[constants.OVERFLOW_FLAG_INDEX])

        # Also test that it shifts in-place
        instructions.RShift.execute_on(c, REG1, REG2, REG1 << 11)
        self.assertEqual(expected, c.data_regs[REG1])
        self.assertEqual(0, c.status_reg[constants.OVERFLOW_FLAG_INDEX])

        # Test that it goes to zero
        instructions.RShift.execute_on(c, REG1, REG2, REG1 << 11)
        self.assertEqual(0, c.data_regs[REG1])
        self.assertEqual(0, c.status_reg[constants.OVERFLOW_FLAG_INDEX])

    def test_comp_grt(self):
        """
        Test function of compare instruction
        """
        c = computer.Computer(memory_size=10)

        a, b = 10, 20
        REG1, REG2, REG3 = 2, 3, 4
        c.data_regs[REG1] = a
        c.data_regs[REG2] = b
        expected = bitarray.bitarray('0' * 32, endian='little')

        # 20 > 10, should set bit 3
        instructions.Comp_Greater_Than.execute_on(c, REG2, REG1, 3 << 11)
        expected[3] = True
        self.assertEqual(expected, c.comp_reg)

        # 10 < 20, should unset bit 3
        instructions.Comp_Greater_Than.execute_on(c, REG1, REG2, 3 << 11)
        expected[3] = False
        self.assertEqual(expected, c.comp_reg)

        # Comparing register to itself should also work
        instructions.Comp_Greater_Than.execute_on(c, REG1, REG1, 1 << 11)
        self.assertEqual(expected, c.comp_reg)

    def test_comp_lst(self):
        """
        Test function of compare instruction
        """
        c = computer.Computer(memory_size=10)

        a, b = 20, 10
        REG1, REG2, REG3 = 2, 3, 4
        c.data_regs[REG1] = a
        c.data_regs[REG2] = b
        expected = bitarray.bitarray('0' * 32, endian='little')

        # 10 < 20, should set bit 3
        instructions.Comp_Less_Than.execute_on(c, REG2, REG1, 3 << 11)
        expected[3] = True
        self.assertEqual(expected, c.comp_reg)

        # 20 > 10, should unset bit 3
        instructions.Comp_Less_Than.execute_on(c, REG1, REG2, 3 << 11)
        expected[3] = False
        self.assertEqual(expected, c.comp_reg)

        # Comparing register to itself should also work
        instructions.Comp_Less_Than.execute_on(c, REG1, REG1, 1 << 11)
        self.assertEqual(expected, c.comp_reg)
