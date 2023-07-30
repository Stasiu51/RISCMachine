"""This file contains a unit test which serves as a demonstration of the function of the cache,
which implements a tree-LRU cache replacement policy.

This does not constitute a thorough testing of all the edge-cases of the cache system."""

import unittest

import computer
from constants import *


class TestCache(unittest.TestCase):
    def test_cache(self):
        c = computer.Computer()
        """
        Test behaviour of cache.
        Starting with empty cache:
              ┌------0              ╮
           ┌--0          ┌--0       ├ tree bits (stored in a bit array by the heap convention)
         ┌-0    ┌-0    ┌-0    ┌-0   ╯
        [ ][ ] [ ][ ] [ ][ ] [ ][ ] - address of stored memory
         0  1   2  3   4  5   6  7  - (cache_index)
        """
        c.memory[1] = Int(10)
        """
        Flips all bits on way down tree, following directions set by tree bits.
        
                     1------┐       ╮
              1---┐      ┌--0       ├ tree bits
           1┐   ┌-0    ┌-0    ┌-0   ╯  
        [1][ ] [ ][ ] [ ][ ] [ ][ ] - address of stored memory
         0  1   2  3   4  5   6  7  - cache_index
        """
        self.assertEqual('1101000', c.memory._cache_tree_bits[0].to01())
        self.assertEqual(1, c.memory._cache_addresses[0,0])
        self.assertEqual(10, c.memory._cache[0,0])

        c.memory[2] = Int(20)
        """
        Another memory set. Do same thing.
        
              ┌------0              ╮
              1---┐         1---┐   ├ tree bits
           1┐   ┌-0      1┐   ┌-0   ╯  
        [1][ ] [ ][ ] [2][ ] [ ][ ] - address of stored memory
         0  1   2  3   4  5   6  7  - cache_index
        """
        self.assertEqual('0111010', c.memory._cache_tree_bits[0].to01())
        self.assertEqual(2, c.memory._cache_addresses[0,4])
        self.assertEqual(20, c.memory._cache[0,4])

        c.memory[1] = Int(100)
        """
        Now access memory address 1 again. Set all bits to face away from it (only changes the root bit).

                     1------┐       ╮
              1---┐         1---┐   ├ tree bits
           1┐   ┌-0      1┐   ┌-0   ╯  
        [1][ ] [ ][ ] [2][ ] [ ][ ] - address of stored memory
         0  1   2  3   4  5   6  7  - cache_index
        """
        self.assertEqual('1111010', c.memory._cache_tree_bits[0].to01())
        self.assertEqual(1, c.memory._cache_addresses[0,0])
        self.assertEqual(100, c.memory._cache[0,0])

        c.memory[3] = Int(30)
        self.assertEqual('0101011', c.memory._cache_tree_bits[0].to01())
        c.memory[4] = Int(40)
        self.assertEqual('1001111', c.memory._cache_tree_bits[0].to01())
        c.memory[5] = Int(50)
        self.assertEqual('0011101', c.memory._cache_tree_bits[0].to01())
        c.memory[6] = Int(60)
        self.assertEqual('1110101', c.memory._cache_tree_bits[0].to01())
        c.memory[7] = Int(70)
        self.assertEqual('0100100', c.memory._cache_tree_bits[0].to01())
        c.memory[8] = Int(80)
        self.assertEqual('1000000', c.memory._cache_tree_bits[0].to01())
        """
        Some more additions:
              ┌------0              ╮
              1---┐      ┌--0       ├ tree bits
           1┐   ┌-0      1┐     1┐  ╯  
        [1][ ] [ ][ ] [2][ ] [3][ ] - address of stored memory
         0  1   2  3   4  5   6  7  - cache_index
         
                     1------┐       ╮
           ┌--0          ┌--0       ├ tree bits
           1┐     1┐     1┐     1┐  ╯  
        [1][ ] [4][ ] [2][ ] [3][ ] - address of stored memory
         0  1   2  3   4  5   6  7  - cache_index
         
              ┌------0              ╮
           ┌--0             1---┐   ├ tree bits
           1┐     1┐   ┌-0      1┐  ╯  
        [1][ ] [4][ ] [2][5] [3][ ] - address of stored memory
         0  1   2  3   4  5   6  7  - cache_index
         
                     1------┐       ╮
              1---┐         1---┐   ├ tree bits
         ┌-0      1┐   ┌-0      1┐  ╯  
        [1][6] [4][ ] [2][5] [3][ ] - address of stored memory
         0  1   2  3   4  5   6  7  - cache_index
         
              ┌------0              ╮
              1---┐      ┌--0       ├ tree bits
         ┌-0      1┐   ┌-0    ┌-0   ╯  
        [1][6] [4][ ] [2][5] [3][7] - address of stored memory
         0  1   2  3   4  5   6  7  - cache_index
         
                     1------┐       ╮
           ┌--0          ┌--0       ├ tree bits
         ┌-0    ┌-0    ┌-0    ┌-0   ╯  
        [1][6] [4][8] [2][5] [3][7] - address of stored memory
         0  1   2  3   4  5   6  7  - cache_index  
        """
        c.memory[9] = Int(90)
        """
        Now we set a further bit. It replaces [2], which is as desired as this was the least recently used:
              ┌------0              ╮
           ┌--0             1---┐   ├ tree bits
         ┌-0    ┌-0      1┐   ┌-0   ╯  
        [1][6] [4][8] [9][5] [3][7] - address of stored memory
         0  1   2  3   4  5   6  7  - cache_index 
         
         We must also check if the value of 20 at address 2 has been correctly transferred to the main memory,
         and that it can be retrieved and re-stored in the cache.
        """
        self.assertEqual('0010010', c.memory._cache_tree_bits[0].to01())
        self.assertEqual(9, c.memory._cache_addresses[0,4])
        self.assertEqual(90, c.memory._cache[0,4])

        # Stored in main memory?
        self.assertEqual(20, c.memory._array[2])

        # Retrieved and put back in cache?
        self.assertEqual(20, c.memory[2])
        self.assertEqual(2, c.memory._cache_addresses[0,0])
        self.assertEqual(20, c.memory._cache[0,0])
