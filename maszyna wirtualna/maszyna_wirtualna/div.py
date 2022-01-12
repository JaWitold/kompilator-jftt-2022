def divide(x, y):
  if x == 0:
    return (0, 0)
  q, r = divide(x >> 1, y)
  q = q << 1
  r = r << 1
  if x % 2 == 1:
    r += 1
  if r >= y:
    r -= y
    q += 1
  return (q, r)

def div_v2(x, y):
  if y == 0:
    return 0
  
  if x < 0:
    x = -x
    y = -y
  x_ = x
  n = 0;
  while x_ != 0:
    x_ //= 2
    n += 1

  q = 0
  r = 0
  while n >= 0:
    x_ = x
    j = n
    while j > 0:
      x_ = x_ // 2
      j -= 1
    # print(x_)

    q *= 2
    r *= 2
    if x_ % 2 == 1:
      r += 1
    if r - y >= 0:
      q += 1
      r -= y
    n -= 1
  return q
  

# print(divide(40, 5)[0])
# print(divide(41, 5)[0])
# print(divide(42, 5)[0])

# print(div_v2(40, 5))
# print(div_v2(-40, 5))
# print(div_v2(40, -5))
# print(div_v2(-40, -5))

from collections.abc import Sequence

def simulate_aging(Rs: Sequence, k: int) -> None:
    """Simulate aging."""
    print(' t  |  R-bits (0-{length})        |  Counters for pages 0-{length}'.format(length=len(Rs)))
    Vs = [0] * len(Rs[0])
    for t, R in enumerate(Rs):
        Vs[:] = [R[i] << k - 1 | V >> 1
                 for i, V in enumerate(Vs)]
        print('{:02d}  |  {}  |  [{}]'.format(t, R,
                                              ', '.join(['{:0{}b}'.format(V, k)
                                                         for V in Vs])))
Rs = [[1,0,1,0,1,1], [1,1,0,0,1,0], [1,1,0,1,0,1], [1,0,0,0,1,0], [0,1,1,0,0,0]]
k = 8
simulate_aging(Rs, k)