import io, sys, mock, unittest
from mock import patch, DEFAULT

import numpy as np
Int = np.uint32

import computer

class TestComputer(unittest.TestCase):
    """
    Test that the computer executes the correct instructions with the correct arguments.
    Mocks the functions themselves to avoid side effects.
    """

    @mock.patch.multiple('computer.Computer',
                         nop=DEFAULT,
                         add=DEFAULT,
                         sub=DEFAULT,
                         load=DEFAULT,
                         store=DEFAULT,
                         comp=DEFAULT,
                         jump=DEFAULT,
                         halt=DEFAULT, )
    def test_execute(self, nop, add, sub, load, store, comp, jump, halt):
        program = np.array([
            0b000000_00001_00010_0000000000000011,
            0b001001_00100_00101_0011000000000000,
            0b001010_00111_01000_0100100000000000,
            0b000100_01010_01011_0000000000001100,
            0b000101_01101_01110_0000000000001111,
            0b000011_10000_10001_0000000000010010,
            0b000010_10011_10100_1010100000000000,
            0b000001_10110_10111_0000000000011000], dtype=Int)

        c = computer.Computer(memory_size=8)
        c.set_memory_chunk(0, program)
        # No halt, so should run out of memory
        with self.assertRaises(computer.SegmentationFaultError):
            c.execute()
        print("hello")
        nop.assert_called_with(1, 2, 3)
        add.assert_called_with(4, 5, 6 << 11)
        sub.assert_called_with(7, 8, 9 << 11)
        load.assert_called_with(10, 11, 12)
        store.assert_called_with(13, 14, 15)
        jump.assert_called_with(16, 17, 18)
        comp.assert_called_with(19, 20, 21 << 11)
        halt.assert_called_with(22, 23, 24)


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
        data = np.array([1,2,3,1<<32 - 1, 1<<32 - 2, 1 << 32 - 3], dtype = Int)

        c = computer.Computer(memory_size=10)
        c.set_memory_chunk(3, data)

        np.testing.assert_array_equal(c.memory[3:9], data)

    def test_mem_set_chunk_errors(self):
        """Test failure cases setting of a chunk of memory"""
        data = np.array([1,2,3,1<<32 - 1, 1<<32 - 2, 1 << 32 - 3], dtype = Int)

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
        c.status_reg |= 1
        c.halt(Int(0),Int(0),Int(0))

        self.assertEqual(c.status_reg, Int(0))

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
        c.print(2,3,4)
        sys.stdout = sys.__stdout__

        self.assertEqual(redirect.getvalue(), expected)

    def test_print_error(self):
        """
        Test for segfault when attempting to print out of bounds
        """
        c = computer.Computer(memory_size=10)
        with self.assertRaises(computer.SegmentationFaultError):
            c.print(0, 0, -1)
        with self.assertRaises(computer.SegmentationFaultError):
            c.print(0, 0, 10)

    def test_load(self):
        pass





def test_mock(self):
        class A:
            def f(self, x, y):
                print(f"Called with {x}.")

            def g(self,y):
                print("g")

        a = A()
        with patch.object(a,'f',autospec=True) as mock_f:
            a.f(123,2)

        mock_f.assert_called_with(123,2)


if __name__ == "__main__":
    unittest.main()