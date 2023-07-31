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
            0b000_000_00001_00010_0000000000000011,  # NOP 1 2 3
            0b001_001_00100_00101_0011000000000000,  # ADD 4 5 6 0
            0b001_010_00111_01000_0100100000000000,  # SUB 7 9 8 0
            0b011_001_01010_01011_0000000000001100,  # LOAD 10 11 12
            0b011_010_01101_01110_0000000000001111,  # STORE 13 14 15
            0b100_001_10000_10001_0000000000010010,  # JUMP 16 17 18
            0b010_000_10011_10100_1010100000000000,  # COMP 19 20 21 0
            0b000_001_10110_10111_0000000000011000,  # HALT 19 20 21 0
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

