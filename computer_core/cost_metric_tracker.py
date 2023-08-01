"""
This file contains a class which functions as a context manager whose job is to hook onto the internal function calls of
the computer in order to cost program execution in terms of memory usage and execution time.

It is quite a 'hacky' approach, but it keeps the main computer execution code cleaner by not having to pass around this
object.
"""

from computer_core.computer import Computer
from computer_core.constants import *

class CostMetricTracker:

    def __init__(self, computer, debug_mode = False):
        self.computer = computer
        self.instructions_executed = 0
        self.accessed_memory_addresses = set()
        self.accessed_datacache_addresses = set()
        self.execution_time_ns = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.memory_accesses = 0
        self.debug_mode = debug_mode

    def __enter__(self):
        # Add a hook onto computer decoding (must happen once per instruction)
        Computer.old_decode = Computer.decode
        def new_decode(instruction):
            self.log_execute_instruction()
            return Computer.old_decode(instruction)
        Computer.decode = new_decode

        # Add a hook onto cache
        type(self.computer.memory)._old_cache_lookup = type(self.computer.memory).cache_lookup
        def new_cache_lookup(self_memory, address):
            cache_section, cache_index, cache_hit = self.computer.memory._old_cache_lookup(address)
            self.log_cache_lookup(address, cache_hit)
            return cache_section, cache_index, cache_hit
        type(self.computer.memory).cache_lookup = new_cache_lookup

        # Add hooks onto the data register methods
        type(self.computer.data_regs)._old_getitem = type(self.computer.data_regs).__getitem__
        def new_getitem(self_memory, address):
            self.log_datacache_access(address)
            return self.computer.data_regs._old_getitem(address)
        type(self.computer.data_regs).__getitem__ = new_getitem

        type(self.computer.data_regs)._old_setitem = type(self.computer.data_regs).__setitem__
        def new_setitem(self_memory, address, value):
            self.log_datacache_access(address)
            self.computer.data_regs._old_setitem(address, value)
        type(self.computer.data_regs).__setitem__ = new_setitem

        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        # Unhook the methods
        type(self.computer.memory).cache_lookup = type(self.computer.memory)._old_cache_lookup
        type(self.computer.data_regs).__setitem__ = type(self.computer.data_regs)._old_setitem
        type(self.computer.data_regs).__getitem__ = type(self.computer.data_regs)._old_getitem
        Computer.decode = Computer.old_decode

    def log_execute_instruction(self):
        self.instructions_executed += 1
        self.execution_time_ns += INSTRUCTION_TIME_NS

    def log_cache_lookup(self, address, cache_hit):
        if self.debug_mode: print(f"Cache access at {address}: cache hit={cache_hit}.")
        self.accessed_memory_addresses.add(address)
        self.memory_accesses += 1
        if cache_hit:
            self.cache_hits += 1
            self.execution_time_ns += CACHE_HIT_TIME_NS
        else:
            self.cache_misses += 1
            self.execution_time_ns += CACHE_MISS_TIME_NS

    def log_datacache_access(self, address):
        self.accessed_datacache_addresses.add(address)

    def summary(self):
        cache_mem = len(self.accessed_datacache_addresses) * 4
        ram_mem = len(self.accessed_memory_addresses) * 4
        return \
f"""Instructions executed: {self.instructions_executed}.
Cache hits: {self.cache_hits} ({100*self.cache_hits/self.memory_accesses:.1f}%)
Cache misses: {self.cache_misses} ({100*self.cache_misses/self.memory_accesses:.1f}%)
RAM memory used: {ram_mem} bytes.
Data register memory used: {cache_mem} bytes.
-----------------------------
Total execution time: {self.execution_time_ns}ns.
Total memory used: {ram_mem+cache_mem} bytes.
-----------------------------"""


