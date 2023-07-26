# RISC Machine Design Spec

## Figure of Merit

Obviously, a RISC machine is not a useful tool for calculation when it is a simulation running on a CISC computer. Even if it were to be coded at the lowest level possible such that there was a one-to-one correspondence between simluated RISC instructions and the executed CISC instructions, there would be no advantage to using the RISC set as the CPU is not designed to take advantage by consistently pipelining exectution as in a real RISC machine. There is therefore some ambiguity as to the metric(s) to be optimised for when designing its architecture. Possible such metrics are

- Actual execution time on the host device
- Actual memory usage on the host device (this is quite easy to get close to optimal I think)
- Available memory/program size of simulated device

Optimising for these three metrics is an exercise in standard program optimisation and I suspect somewhat misses the purpose of this challenge. I think a more interesting approach is to imagine that the design of the computer specified here represents the design of a physical RISC CPU, and that the programmatic implementation to some extent is a simulation of the calculations performed on the device. The challenge is then to consider a design speicification that would be suitable for a RISC device and implement its function, even where this gives rise to complexities that will provide no actual advantage in terms of the three metrics listed above. Where I have a choice, I will make arbitrary desicions based on my own sense of 'mechanical aesthetic'. I will also try to program the simulation in an efficient manner.

## Design Constraints - RISC advantages

The key aim when designing a RISC computer is to keep the per-instruction times as low as possible (this *reduced* complexity of each instruction is the namesake of the concept, rather than the smaller number of available instructions). The idea is that along with intelligent compiling, this will outweigh the advantage of having a more versatile intstruction set, where individual instructions may take a large number of cycles to execute. As far as possible, one should aim for a one-CPU-cycle-per-intruction exectution. I am not familar with CPU design but it seems that having a fixed instruction length, within which there is a fixed opcode length, and generally consistent structuring of the instructions, helps when designing the circuitry to be pipelined.

My specification is therefore as follows:

- I will use a 32-bit instruction length. This is an arbitrary choice as, as explained above, in this challenge I will imagine I am desigining a physical device . It might well be the case that 32 bit instruction length is a constraint imposed by the circuitry available. It also adds some additional design constraints that make the challenge more fun, and is an homage to actual RISC devices of the 70s and 80s.

- The opcode length will be 6. I am tasked with implementing an instruction set of 8 instructions, which would require 3 bits minimum. However, this will be extended. Additionally, I imagine that when designing the decoding circuitry, certain physical instruction layouts might make things easier. I designate the first two bits as a binary encoding of which part of the CPU is required for an instruction (memory access, ALU, branching/control) and the third, fourth, fifth and sixth as a binary further specification of the instruction to be performed.

- There will be 32 data registers. Of these, data register 0 will always read zero and data register 1 will always read one. Attempting to load into these regsisters is equivalent to a NOP. This is loosely inspired by the RISC-1 computer of 1981.

- There is a 16-bit program counter register.

- There are an additional 32 one-bit status registers, which I imagine in hardware would consist of a single 32-bit register with dedicated indexing or bit-shift logic.

- From my research it seems both Von-Neumann and Harvard-model (seperate program and data memory) memory models have been used on RISC devices. Within the goals I have set myself, I can't see a big reason to use one over the other, but I'd much prefer the device to have a single memory as I think It will be fun to write programs that can change their own code. I will therefore adopt a Von-Neumann model, with the PC initialised to memory adress 0. It will be the programmer's reponsibility to avoid overwriting the program.

## Language: Python

I will write the program in python. Were I more concerned about optimal performance, Rust or C++ would be preferable. Another approach might be to write a python module wrapper around a C extension to actually run the code. The fastest execution would be a cross-compiler that just translated the provided script into x86. However, I am most confident in my ability to write good-quality Python, and performance is unlikely to be particularly important, so I will use Python.
