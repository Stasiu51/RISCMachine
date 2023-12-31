from math import ceil

import numpy as np
from bitarray import bitarray

from computer_core.constants import *

class Memory:
    """
    Memory class: basically a wrapper around a numpy array which allows for some custom behaviour.
    Methods are self-explanatory with just some bounds and type checking.
    """

    def __init__(self, memory_size):
        if not 2 <= memory_size <= (1 << 16):
            raise ValueError(f"Invalid memory size {memory_size}. Must be between 2 and 65536")
        self.size = memory_size
        self.cache_section_size = CACHE_SECTION_SIZE
        self.cache_section_number = ceil(memory_size / CACHE_SECTION_RESPONSIBILITY)

        self._array = np.zeros(memory_size, dtype=Int)
        self._cache = np.zeros((self.cache_section_number,CACHE_SECTION_SIZE), dtype = Int) # value indicates no reference
        self._cache_addresses = np.ones((self.cache_section_number, CACHE_SECTION_SIZE), dtype = Int) * ONES
        self._cache_tree_bits = [bitarray('0' * (CACHE_SECTION_SIZE - 1), endian ='little')
                                 for _ in range(self.cache_section_number)]

    def __getitem__(self, address):
        if type(address) is slice:
            # Slice logic: to work with caches: make these a series of single accesses
            start, stop = address.start or 0, address.stop or self.size
            return_array = np.zeros((stop - start), dtype = Int)
            for i, adr in enumerate(range(start, stop)):
                return_array[i] = self.__getitem__(adr)
            return return_array

        # Normal lookup
        if not 0 <= address < self.size:
            raise SegmentationFaultError(
                f"Attempted to read address {address}, which is out of bounds (max {self.size}).")

        cache_section, cache_index, cache_hit = self.cache_lookup(address)
        if cache_hit:
            return self._cache[cache_section, cache_index]

        # Otherwise need to store in the cache
        self._cache[cache_section, cache_index] = self._array[address]
        return self._cache[cache_section, cache_index]

    def __setitem__(self, address, value):
        if type(address) is slice:
            # Slice logic: to work with caches: make these a series of single accesses
            start, stop = address.start or 0, address.stop or self.size # to convert slice into range
            if type(value) is Array:
                if value.size != (stop - start):
                    raise ValueError("Value must be an array of same length as the slice.")
                for adr, val in zip(range(start, stop), value):
                    self.__setitem__(adr,val)
            else: # single value set
                for adr in range(start,stop):
                    self.__setitem__(adr, value)
            return


        # Single access: error checking
        if not 0 <= address < self.size:
            raise SegmentationFaultError(
                f"Attempted to set address {address}, which is out of bounds (max {self.size}).")
        if type(value) is not Int:
            raise TypeError("Type of value when setting memory should be uint32.")

        cache_section, cache_index, cache_hit = self.cache_lookup(address)

        self._cache[cache_section, cache_index] = value

    """
    Note _cache_tree_bits follows a heap convention: that is, the bits in a single section are indexed as follows:

          ┌------0------┐       ╮
       ┌--1---┐      ┌--2---┐   ├ _cache_tree_bits index
     ┌-3┐   ┌-4┐   ┌-5┐   ┌-6┐  ╯
    [ ][ ] [ ][ ] [ ][ ] [ ][ ] - cache locations
     0  1   2  3   4  5   6  7  - cache_index

    This convention allows for convenient arithmetic traversal of the tree.
    """

    def cache_lookup(self, address):
        cache_section = CACHE_SECTION_INDEX_MASK.get(address)
        if address in self._cache_addresses[cache_section]:

            #    Cache hit: move up the tree, flipping bits.
            cache_pos = np.where(self._cache_addresses[cache_section] == address)[0][0]
            path = cache_pos + self.cache_section_size - 1
            while path != 0:
                d, m = divmod(path - 1,2)
                path = d
                # Flip bit to point away from direction of travel
                self._cache_tree_bits[cache_section][path] = 1 - m
            return cache_section, cache_pos, True
        else:
            # Cache miss: move down the tree along the path, flipping bits along the way
            path = 0
            while path < self.cache_section_size - 1:
                self._cache_tree_bits[cache_section][path] ^= 1
                path = path*2 + 2 - self._cache_tree_bits[cache_section][path]
            path -= self.cache_section_size - 1

            # put whatever is there back into main memory, unless it is the sentinel value 0b111..11
            if (replaced_address := self._cache_addresses[cache_section, path]) != ONES:
                self._array[replaced_address] = self._cache[cache_section, path]

            # update address
            self._cache_addresses[cache_section, path] = address
            return cache_section, path, False

class NoSuchRegisterError(Exception):
    pass

class DataRegisterArray:
    """
    Class which stores the data registers, and enforces the read-only 0 and 1 registers.
    No error checking required for this one beyond default numpy errors.
    """
    def __init__(self, size = 32):
        self._array = np.zeros(size, dtype = Int)
        self.size = size
        self._array[1] = 1

    def __setitem__(self, register, value):
        if type(register) is slice:
            # Slice logic: to work with caches: make these a series of single accesses
            start, stop = register.start or 0, register.stop or self.size  # to convert slice into range
            if type(value) is Array:
                if value.size != (stop - start):
                    raise ValueError("Value must be an array of same length as the slice.")
                for reg, val in zip(range(start, stop), value):
                    self.__setitem__(reg, val)
            else:  # single value set
                for reg in range(start, stop):
                    self.__setitem__(reg, value)
            return
        if register <= 1:
            print(f"Warning: attempted to write to data register {register}, but it is read-only.")
            return
        self._array[register] = value

    def __getitem__(self, register):
        return self._array[register]

