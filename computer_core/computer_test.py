import io, sys, unittest, bitarray
from unittest.mock import patch
import numpy as np
Int = np.uint32
from computer_core import constants, computer
from computer_core import instructions

class TestComputer(unittest.TestCase):

    @patch.object(instructions.Halt, "execute_on")
    @patch.object(instructions.Jump, "execute_on")
    @patch.object(instructions.Comp, "execute_on")
    @patch.object(instructions.Store, "execute_on")
    @patch.object(instructions.Load, "execute_on")
    @patch.object(instructions.Sub, "execute_on")
    @patch.object(instructions.Add, "execute_on")
    @patch.object(instructions.Nop, "execute_on")
    def test_execute(self, Nop, Add, Sub, Load, Store, Comp, Jump, Halt):
        """
        Test that the computer executes the correct instructions with the correct arguments.
        Mocks the functions themselves to avoid side effects.
        """
        program = np.array([
            0b000000_00001_00010_0000000000000011,  # NOP 1 2 3
            0b001001_00100_00101_0011000000000000,  # ADD 4 5 6 0
            0b001010_00111_01000_0100100000000000,  # SUB 7 9 8 0
            0b000100_01010_01011_0000000000001100,  # LOAD 10 11 12
            0b000101_01101_01110_0000000000001111,  # STORE 13 14 15
            0b000011_10000_10001_0000000000010010,  # JUMP 16 17 18
            0b000010_10011_10100_1010100000000000,  # COMP 19 20 21 0
            0b000001_10110_10111_0000000000011000,  # HALT 19 20 21 0
        ], dtype=Int)

        c = computer.Computer(memory_size=8)
        c.set_memory_chunk(0, program)
        # No halt, so should run out of memory
        with self.assertRaises(computer.SegmentationFaultError):
            c.execute()
        Nop.assert_called_with(c, 1, 2, 3)
        Add.assert_called_with(c, 4, 5, 6 << 11)
        Sub.assert_called_with(c,7, 8, 9 << 11)
        Load.assert_called_with(c,10, 11, 12)
        Store.assert_called_with(c,13, 14, 15)
        Jump.assert_called_with(c,16, 17, 18)
        Comp.assert_called_with(c,19, 20, 21 << 11)
        Halt.assert_called_with(c,22, 23, 24)

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
            instructions.Load.execute_on(c, 2, 0, Int(-1))

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
            instructions.Store.execute_on(c, 2, 0, Int(-1))

        with self.assertRaises(computer.SegmentationFaultError):
            instructions.Store.execute_on(c, 2, 0, Int(10))

    def test_mem_set(self):
        """Test setting an address memory (e.g.) loading a constant"""
        data = Int(0b10011001100110011001100110011001)
        address = 5

        c = computer.Computer(memory_size=10)
        c.set_memory_address(address, data)

        np.testing.assert_array_equal(c.memory[address], data)

    def test_mem_set_errors(self):
        """Test failure cases of address setting function."""
        data = Int(0b10011001100110011001100110011001)

        with self.assertRaises(computer.SegmentationFaultError):
            c = computer.Computer(memory_size=10)
            c.set_memory_address(-1, data)

        with self.assertRaises(computer.SegmentationFaultError):
            c = computer.Computer(memory_size=10)
            c.set_memory_address(10, data)

        with self.assertRaises(TypeError):
            c = computer.Computer(memory_size=10)
            c.set_memory_address(0, int(data))

    def test_mem_get(self):
        """Test getting an address memory (e.g.) loading a constant"""
        data = Int(0b10011001100110011001100110011001)
        address = 5

        c = computer.Computer(memory_size=10)
        c.memory[address] = data
        retrieved_data = c.get_memory_address(address)

        np.testing.assert_array_equal(retrieved_data, data)

    def test_mem_get_errors(self):
        """Test failure cases of address getting function."""
        data = Int(0b10011001100110011001100110011001)

        with self.assertRaises(computer.SegmentationFaultError):
            c = computer.Computer(memory_size=10)
            c.get_memory_address(-1)

        with self.assertRaises(computer.SegmentationFaultError):
            c = computer.Computer(memory_size=10)
            c.get_memory_address(10)

    def test_mem_set_chunk(self):
        """Test setting of a chunk of memory (e.g.) loading a program"""
        data = np.array([1, 2, 3, 1 << 32 - 1, 1 << 32 - 2, 1 << 32 - 3], dtype=Int)

        c = computer.Computer(memory_size=10)
        c.set_memory_chunk(3, data)

        np.testing.assert_array_equal(c.memory[3:9], data)

    def test_mem_set_chunk_errors(self):
        """Test failure cases setting of a chunk of memory"""
        data = np.array([1, 2, 3, 1 << 32 - 1, 1 << 32 - 2, 1 << 32 - 3], dtype=Int)

        with self.assertRaises(computer.SegmentationFaultError):
            c = computer.Computer(memory_size=10)
            c.set_memory_chunk(-1, data)

        with self.assertRaises(computer.SegmentationFaultError):
            c = computer.Computer(memory_size=10)
            c.set_memory_chunk(7, data)

        with self.assertRaises(TypeError):
            c = computer.Computer(memory_size=10)
            c.set_memory_chunk(0, data.astype(np.uint64))

    def test_decode(self):
        """
        Test splitting instruction into components
        """
        opcode = Int(0b101010)
        arg1 = Int(0b11111)
        arg2 = Int(0b00000)
        data = Int(0b1111000011110000)

        instruction = (opcode << 26) | (arg1 << 21) | (arg2 << 16) | data
        decoded_opcode, decoded_arg1, decoded_arg2, decoded_data = computer.Computer.decode(instruction)

        self.assertEqual(opcode, decoded_opcode)
        self.assertEqual(arg1, decoded_arg1)
        self.assertEqual(arg2, decoded_arg2)
        self.assertEqual(data, decoded_data)

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
        expected = bitarray.bitarray('0'*32, endian = 'little')

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