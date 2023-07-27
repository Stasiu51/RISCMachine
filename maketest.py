match "hello":
    case ["h", *inner, "o"]:
        print(inner)
    case other:
        print(other)