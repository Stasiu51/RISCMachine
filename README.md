# RISC CPU Task Readme

## Running the code

The computer simulation code, unit tests, and example programs (which are also tests) are all in this repository. There are a few dependencies, which are given in *requirements.txt*. These can be installed (I suggest into a virtual environment) with pip. The following instructions assume a working python (>= 3.10) installation that can be used in a shell with `py`. On some systems you should replace  `py` with  `python3` or  `python`, and/or replace  `pip` with  `pip3`.

1. Clone the repository into a local folder: `git clone https://github.com/Stasiu51/RISCMachine/`

2. Navigate into it: `cd RISCMachine`

3. (Optional) make a new python virtual environment: `py -m venv venv`

4. (Optional) activate the venv: `venv\Scripts\activate` on Windows, `source venv/bin/activate` on Mac/Linux.

5. Install requirements: `pip install -r requirements.txt`

All the tests and examples can be run at once through the single script *tests.py*:

`py tests.py`

# RISC Machine Design Spec

Disclaimer: I had little prior knowledge of CPU design or architecture. Everything I have done in this task has been based on research in the time allocated.
 
## Figure of Merit

Obviously, a RISC machine is not a useful tool for calculation when it is a simulation running on a CISC computer. Even if it were to be coded at the lowest level possible such that there was a one-to-one correspondence between simluated RISC instructions and the executed CISC instructions, there would be no advantage to using the RISC instruction set as the CPU is not designed to take advantage of it by consistently pipelining execution as in a real RISC machine. There is therefore some ambiguity as to the metric(s) to be optimised for when designing its architecture. Possible such metrics could be

- Actual execution time on the host device
- Actual memory usage on the host device (this is quite easy to get close to optimal I think)
- Available memory/program size of simulated device

Optimising for these three metrics is an exercise in standard program optimisation and I suspect somewhat misses the purpose of this challenge. I think a more interesting approach is to imagine that the design of the computer specified here represents the design of a physical RISC CPU, and that the programmatic implementation to some extent is a simulation of the calculations performed on the device. The challenge is then to consider a design specification that would be suitable for a RISC device and implement its function, even where this gives rise to complexities that will provide no actual advantage in terms of the three metrics listed above. I set out my chosen goals in the 'Design Goals' section of this document.

## Design Constraints - RISC architecture

The key aim when designing a RISC computer is to keep the per-instruction times as low as possible (this *reduced* complexity of each instruction is the namesake of the concept, rather than the smaller number of available instructions). The idea is that along with intelligent compiling, this will outweigh the advantage of having a more versatile instruction set as in a CISC device, where individual instructions may take many cycles to execute. As far as possible, one should aim for a one-CPU-cycle-per-intruction execution. I am not familiar with CPU design, but it seems that having a fixed instruction length, within which there is a fixed opcode length, and generally consistent structuring of the instructions, helps when designing the circuitry to be pipelined.

## Design Goals

The chip I will be designing is a small, inexpensive general purpose microprocessor, similar in capacity to an arduino UNO. I will not be optimising purely for efficient practical design, as if I were, I would simply copy the specification of an existing design, which are the result of decades of iteration by talented teams. I will instead aim to develop an architecture that is in principle capable of all the same calculations as more standard chips in interesting alternative ways using a unified memory and dynamically updated instructions. A further somewhat artificial goal is that the device must have a clock speed of at least 1GHz, as below this speed there would be unlikely to be any advantage in implementing a cache. Perhaps the device is aimed at very low-latency tasks, e.g. in physics experiments?

## Architecture Specification

My specification is therefore as follows:

- I will use a 32-bit word size, register size, and instruction length. This is an arbitrary choice as, as explained above, in this challenge I will imagine I am designing a physical device. It might well be the case that 32 bit instruction length is a constraint imposed by the circuitry available. It also adds some additional design constraints that make the challenge more fun, and is an homage to actual RISC devices of the 70s and 80s.

- Addresses will be 16-bit. This leads to a maximum of 262kB of memory, which is sufficient for basic microprocessor tasks. The advantage of 16-bit addresses is that they take up half of one instruction, which allows for interesting manipulation techniques (see later).

- There will be 32 data registers. Of these, data register 0 will always read zero and data register 1 will always read one. Attempting to load into these registers is equivalent to a NOP. This behaviour is convenient for programming, and is loosely inspired by the RISC-1 computer of 1981.

- There is a 16-bit program counter register.

- There are an additional 32 one-bit status registers, which I imagine in hardware would consist of a single 32-bit register with dedicated indexing or cyclic bit-shift logic.

- From my research it seems both Von-Neumann (unified memory) and Harvard (separate program and data memory) memory models have been used on RISC devices. For the esoteric style of execution I am going for, I need the CPU to be able to edit the memory where the program is stored. A natural way to achieve this is to adopt a Von-Neumann model, with the PC initialised to memory address 0. It will be the programmer's responsibility to avoid overwriting the program in a deleterious way during execution.

- The opcode length will be 6. A minimum of 3 is required for the 8 requested instructions, but this leaves room for extension.

### Instruction format

- Bits 0-5 - opcode 
- Bits 6-10 - ARG1: register argument 1
- Bits 11-15 - ARG2: either the second register argument (in the case of arithmetic or logic operations) or a set of flags that are immediately loaded into an internal register to further specify the behaviour of an instruction:
- Bits 16 - 31 - DATA: either the third register argument for arithmetic and logic operations (these are only 5-bit, so bits 21-31 are unused in this case); or for jump and load/store instructions, a 16-bit memory address or numeric literal.

### Instruction list
(Basic implementation)
| Instruction | Opcode (Bits 0-5) | Arguments Bits (4-31 as above) |
| -- | -- | --|
| NOP | 000 000 | Ignored.
| HALT | 000 001 | Ignored.
| ADD | 001 001 | Adds data registers ARG1 and ARG2, stores result in data register DATA. |
| SUB | 001 010 | Subtracts data register ARG2 from ARG1, stores result in data register DATA. |
| COMP | 010 000 | Compares contents of ARG1 data register to ARG2 data register. If equal, COMP register specified by DATA set to 1, else set to 0. | 
| LOAD | 011 001 | Load value into data register ARG1. Behaviour determined by flags in ARG2 as described below.
| STORE |011 010| Stores data register ARG1 into address in DATA. Behaviour determined by flags in ARG2 as described below.|
| JMP | 100 001 | Jump an amount set by DATA depending on the COMP register bit ARG1. ARG2 are execution flags (see below). |
| PRINT | 111111 | Prints the contents of the data registers ARG1 and ARG2 and the memory stored at address DATA. |

(Additional extension instructions)
| Instruction | Opcode (Bits 0-5) | Arguments Bits (4-31 as above) |
| -- | -- | --|
| LSHIFT | 001 011 | Shifts the contents of data register ARG1 left by a number of bits given by the contents of data register ARG2, store result in data register ARG3|
| RSHIFT | 001 100 | Shifts the contents of data register ARG1 right by a number of bits given by the contents of data register ARG2, store result in data register ARG3|
| COMPGRT | 010 010| As COMP, but set the COMP register bit only if the contents of the ARG1 data register are greater than the contents of the ARG2 data register.|
| COMPLST | 010 011 | As COMP, but set the COMP register bit only if the contents of the ARG1 data register are less than the contents of the ARG2 data register.|

#### Load/store behaviour
The bits in ARG2 are sent to a 'flag register' of size five bits, where they specify the behaviour of the jump instruction. There are keywords which allow the setting of these flags when producing a program using the assembler.

- Bit 11 (`HLF` in assembly) specifies whether the copy instruction should only copy 16 bits. If it is set:
    - Bit 12 (`FROM_SIG` in assembly) specifies whether the source bits should be the most or least significant 16 bits of the source memory address of register.
    - Bit 13 (`TO_SIG` in assembly) specifies whether the source bits should be copied to the most or least significant 16 bits of the destination memory address or register.
    - Bit 14 (`OW` in assembly) specifies if the other 16 bits in the destination memory address or register should be set to 0.
- Bit 15 (`IM` in assembly) specifies that the source of the bits to be copied is the instruction itself. Combined with the above options, this allows for the manipulation of memory addresses. Sometimes referred to as 'immediate mode'.

#### Jump behaviour

- Bit 11 (`ON_HIGH` or `ON_LOW` in assembly) specifies whether the jump should be conditional on a 0 or 1 state of the specified bit in the COMP register.
- Bit 12 (`INC` or `DEC` in assembly) specifies whether the jump should increment or decrement the program counter.

### Assembler

I wrote a simple assembler script (*assembler/assembler.py*) to help generate the machine code for the examples. The syntax for the assembly code it takes as input is easily gleaned from the example programs (e.g. in *linked_list_program.py*). The assembler supports comments and provides automatic calculation of jump amounts.

## Language: Python

I will write the program in python. Were I more concerned about optimal performance, Rust or C++ would be preferable. Another approach might be to write a python module wrapper around a C extension to actually run the code. The fastest execution would be a cross-compiler that just translated the provided script into x86. However, I am most confident in my ability to write good-quality Python, and performance is unlikely to be particularly important, so I will use Python.

# Extension tasks

## Linked list

Using a linked list as part of a program requires abstraction only possible with a higher level language. To use one of these I would need to write a compiler. I therefore interpret this task as showing how it is in principle possible to manipulate a linked list using a program written in my assembly language.

Linked lists fundamentally rely on pointers. Using pointers requires us to be able to read and write to an address that is itself a variable known only at runtime. The obvious way to achieve this is to allow the `LOAD` and `STORE` instructions, as well taking as arguments a source/destination register and an address, to take a second register, whose contents specify the address to be read from or written to. This is not the approach I have taken. The `LOAD` and `STORE` instructions in my specification have only a (normal) literal address mode, and a literal contents ('immediate') mode.

This leads to an alternative approach, which I would not necessarily advocate in professional design but is much more interesting to play with as a toy processor: the program can dynamically update its own code to adjust the arguments of upcoming `LOAD` and `STORE` instructions. The unified memory model makes this possible. A proof of concept program, which traverses the elements of a linked list until it arrives at a sentinel, is given in *linked_list_program.py*.

## Additional instructions

The instructions are implemented as static classes which derive from an abstract `Instruction` class (in *computer_core/instructions.py*). This makes it simple to extend the instruction set, by simply adding more derived classes to *computer_core/instructions.py*. Note that these classes are never instantiated; binary instructions are created and stored in the computer memory, which are decoded by the computer object. In addition to the required core instructions, I implemented (see the bottom of *computer_core/instructions.py*):
- `LSHIFT` and `RSHIFT` - Left and right bit shift operations, which shift the contents of a register by a number of places specified by the contents of another register.
- `COMP_GRT` and `COMP_LST` - similar to the `COMP` instruction but which set the bit in the COMP_REG if the contents of the specified register are strictly greater or less than one another respectively.

I make use of these instructions in the example program in *integer_division_program.py*.

## Cache

Decisions to be taken when designing a cache system are:

- What should the total cache size be?
- What should the associativity of the cache be - that is, for any given memory address, how many possibly locations are there in the cache where that memory could be stored. For simplicity, I will take individual addresses as data blocks and not some larger chunk.
- What replacement/placement policy should be implemented to avoid cache misses whilst keeping operation efficient?

Basic chips such as the Arduino UNO have no cache, as their clock speeds (16MHz for the UNO) are slow enough that they can perform an SRAM access within one clock cycle. Access times for SRAM (as in the UNO) are around 10ns, or it would be around 50ns for DRAM. For our cache to have any utility, I will suppose the clock speed is 1 GHz, which is probably overkill for a prototyping board such as the Arduino - but perhaps a goal of the board is extremely low latency, perhaps for scientific experiments on a nanosecond timescale.

The main advantage of a cache system in a unified memory system like this one will be fast loading of instructions when performing loops. We would therefore like to be able to keep a set of around 10-20 instructions towards the start of memory consistently in the cache, remaining in cache even when other memory accesses occur to other parts of the memory. However, this is a simple and inexpensive microcontroller with limited memory to begin with, so it does not make sense for the cache to be very big, nor should there be much ancillary data for the implementation of the cache placement/replacement policies.

My design for the cache system is as follows:

- There will be a total of 1kB of unified cache memory. 
- This is divided into 32 sections each containing space for the contents of 8 memory locations. The first 5 bits of the 16-bit address space determine which of the sections of memory are allowed to be cached in. 
- The associativity of the system is therefore 8. Each section of cache has responsibility for 2048 possibly memory addresses.
- It is intended that any loops of instructions in the program will be reliably held in the first of these caches.

- A least-recently-used (LRU) replacement policy is a common strategy. However, for systems with a high associativity such as this, an exact LRU system is expensive to implement, as it is necessary to store and compare data on the access times of all the cache locations. I will therefore use a pseudo-LRU algorithm, tree-PLRU. This algorithm was used in early RISC architectures such as the PowerPC G4 and is not too complicated to implement. This algorithm requires storing only 7 'tree bits' per 8 cache locations, and provides in most cases a good approximation to LRU performance. 
- The inclusion of a cache in this simulation *slows* performance of the simulation as it adds complexity to every memory access. It is intended that, *in silico*, the physical circuitry that performs the tree traversal would be highly efficient.

The cache is implemented as part of the `Memory` class in *computer_core/memories.py*. A detailed example of its operation is given in the unit test in *computer_core/cache_test.py*.

## Cost of execution metric

My model for the time to execute a program is as follows. The clock time is chosen to be fairly low (therefore inexpensive) whilst still benefiting from a cache. The other times are taken from memory access times and L1 cache access times of modern Intel CPUs:

- The CPU runs at 1GHz, and all instructions take one cycle (1ns) to execute. In addition:

- for a LOAD/STORE operation, a cache hit (reading from/writing to the SRAM cache) pauses execution for 1ns (equivalent to one extra cycle);

- for a LOAD/STORE operation, a cache miss (reading from/writing to the DRAM memory) pauses execution for 80ns.

- The memory cost of running a program will be the number of unique memory locations in both the data caches and the RAM. I track both seperately.

To track these costs without introducing additional complexity into the computer code, I wrote a class `CostMetricTracker` in *cost_metric_tracker.py* which works as a context manager that hooks onto the internal function calls of the computer object, so that the computer code does not have to explicitly call the logging object.

You can see this class working in the example programs in *fibonacci_program.py*, *linked_list_program.py* and *integer_division_program.py*, where it is used to print a summary of the program execution costs.



