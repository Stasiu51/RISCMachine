from computer_core.constants import Int

def make_ins_data(opcode, arg1, arg2, data):
    """
    Creates an instruction that takes two 5 bit arguments and a 16-bit address/data argument.
    """
    return (Int(opcode) << 26) | (Int(arg1) << 21) | (Int(arg2) << 16) | Int(data)


def make_ins_reg(opcode, arg1, arg2, arg3):
    """
    Creates an instruction that takes three 5 bit arguments.
    """
    return (Int(opcode) << 26) | (Int(arg1) << 21) | (Int(arg2) << 16) | (Int(arg3) << 11)


def parse_arg(s, range_max, range_min=0):
    """
    Parses an argument that could be in decimal or binary syntax
    """
    try:
        if len(s) >= 2 and s[0] == "B":
            val = int(s[1:], 2)
        else:
            val = int(s, 10)
    except Exception as e:
        raise Exception(f"Failed to parse argument '{s}'.") from e
    if not range_min <= val < range_max:
        raise ValueError(f"Argument {val} is out of range (min {range_min}, max {range_max}).")
    return val


def parse_arg_multiple(max_range, *args):
    """
    Convenience function for multiple parse_arg calls
    """
    return (parse_arg(s, max_range) for s in args)

def require_args(args, min_n_args, max_n_args):
    n = len(args)
    if min_n_args is not None and n < min_n_args:
        raise SyntaxError(f"Instruction requires at least {min_n_args} arguments, but only given {n}.")
    if max_n_args is not None and n > max_n_args:
        raise SyntaxError(f"Instruction requires at most {max_n_args} arguments, but only given {n}.")
    return args