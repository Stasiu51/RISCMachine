template = """
              ┌------0              ╮
           ┌--0          ┌--0       ├ tree bits (stored in a bit array by the heap convention)
         ┌-0    ┌-0    ┌-0    ┌-0   ╯
        [ ][ ] [ ][ ] [ ][ ] [ ][ ] - address of stored memory
         0  1   2  3   4  5   6  7  - (cache_index)
         
                     1------┐       ╮
              1---┐         1---┐   ├ tree bits (stored in a bit array by the heap convention)
           1┐     1┐     1┐     1┐  ╯
        [ ][ ] [ ][ ] [ ][ ] [ ][ ] - address of stored memory
         0  1   2  3   4  5   6  7  - (cache_index)
"""

def gen(a,b,c,d,e,f,g):
    t = template[:]
    if a:
        t = t[:10] + '       0------┐'*10 + t[30:]
    return t

print(gen(1,1,1,1,1,1,1))
