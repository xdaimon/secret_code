black_preimages = [(2,0),
                   (0,2),
                   (1,0),
                   (0,1)]
white_preimages = [(0,0),
                   (1,1),
                   (2,2),
                   (3,3),
                   (0,3),
                   (3,0),
                   (1,3),
                   (3,1),
                   (2,3),
                   (3,2),
                   (1,2),
                   (2,1)]

def encode_columns(g, w, h):
    # Represent each column in g as an integer, a bit sequence.
    gi = []
    for j in range(w):
        n = 0
        for i in range(h):
            n |= g[h-1-i][j] << i
        gi.append(n)
    return gi

def vertical_reflect(col, h):
    ret = 0
    for i in range(h):
        ret |= ((col>>(h-1-i))&1) << i
    return ret

def get_column_preimages(g, h):
    # Generate all valid preimages for each column of height h in g.  A
    # preimage for a column is built by successively overlapping 2x2 preimages.
    # The list of all valid preimages is build iteratively. First, all
    # preimages for the subcolumn of height h=1 are generated. Then 2x2 blocks
    # from white_preimages or black_preimages are overlapped with h=1 preimages
    # to form all h=2 preimages.

    # column to preimages map
    cpi = {}

    for col in g:
        # Don't generate preimages for the same column twice
        if col in cpi:
            continue

        # Vertical reflection of the column also reflects the preimages
        vert_refl = vertical_reflect(col, h)
        if vert_refl in cpi:
            temp = []
            for pi in cpi[vert_refl]:
                refl = (vertical_reflect(pi[0], h+1),
                        vertical_reflect(pi[1], h+1))
                temp.append(refl)
            cpi[col] = temp
            continue

        # subcolumn preimages
        scpi = white_preimages
        if col&1:
            scpi = black_preimages

        for i in range(1,h): # for each bit in col
            temp = []

            # 2x2 blocks
            blocks = white_preimages
            if col&(1<<i):
                blocks = black_preimages

            for pi in scpi:
                top_row = ((pi[0]>>i)&1, (pi[1]>>i)&1)

                for block in blocks:
                    bottom_row = (block[0]&1, block[1]&1)

                    # If overlap of block and subcolumn preimage is equal
                    if top_row == bottom_row:
                        # then place top row of block onto subcolumn preimage
                        new = list(pi[:])
                        new[0] |= (block[0]&2) << i
                        new[1] |= (block[1]&2) << i
                        temp.append(tuple(new))
            scpi = temp

        cpi[col] = scpi
    return cpi

def answer(g):
    # We can count the number of grids that lead to g after one timestep by
    # counting the number of unique paths through a graph of column preimages.
    # The algorithm is roughly like this,
    #    Generate all preimages for each column in g
    #    Find number of ways to combine a preimage from each column with a
    #    preimage from a neighboring column

    h = len(g)
    w = len(g[0])
    g = encode_columns(g, w, h)
    cpi = get_column_preimages(g, h)

    # Count of paths to preimages of the left column are in lcounts[preimage]
    lcounts = {}
    # Combine counts for preimages with equivalent right columns.
    for lp in cpi[g[0]]:
        lcounts[lp[1]] = 1 + lcounts.get(lp[1],0)

    # For each pair of columns (lcol, rcol) in g, count the number paths from
    # preimages of lcol to preimages of rcol. There is a path between a pair of
    # preimages (lp,rp) if the right column of lp (lp[1]) is equal to the left
    # column of rp (rp[0]).  Once we have the number of paths to a preimage, we
    # no longer need that preimages' left column. In the code below we store
    # rp's right column (rp[1]) for use in the next loop iteration but we do
    # not store not rp's left column.
    for rcol in g[1:]:
        rcounts = {}

        # This will loop a maximum of 2**(h+1) times because we've combined all
        # preimages with equivalent right cols and the number of possible
        # columns of height h+1 is 2**(h+1). This makes a huge difference when
        # the column in question is the all False column of height 9, which has
        # 121552 preimages.
        for rp in cpi[rcol]:
            # If overlap of lp and rp is equal, that is
            # if lp[1] == rp[0] for some lp[1] in lcounts
            if rp[0] in lcounts:

                # On the next iteration, only consider those preimages that
                # have a valid overlap with some preimage of the left column
                rcounts[rp[1]] = lcounts[rp[0]] + rcounts.get(rp[1],0)

        lcounts = rcounts
    return sum(lcounts.values())


#################### Description of another method ########################
# I thought about how to keep a count of unique paths to the preimages of
# bit i,j in the grid in terms of the previously visited bit's counts and
# state (True/False). I can easily use a list of counts to find the number
# of possible preimages for a single column. The same technique can be used
# to count the preimages of any path through the grid, so long as there is
# no index i s.t. a preimage of bit i overlaps with a preimage of bit j
# where |i - j| > 2. For example,
#
# If the path is 3 bits long and looks like this
#   _____________
#   |     |     |
#   |  2  |  3  |
#   |_____|_____|
#   |     |     |
#   |  1  |     |
#   |_____|_____|
#
# Then I can count the number of number of paths to preimages of bits
# 1, 2 and 3.
# If 1, 2 and 3 are all black bits in the image, then
#
# bit | path to preimage count list
#  1  | [1 1 1 1]  # paths to first bit's preimages are initialized to 1
#  2  | [2 2 1 1]
#  3  | [2 3 1 2]  # the sum is the number of preimages for the
#                  # grid = [[True],[True],[True]]
#
# However, if the 4th box in the above grid was included in the path, then
# a new counting algorithm would be needed. I think the issue is that the
# counts in the list for bit 3 represent combinations of preimages of bits
# 2 and 1 that a preimage in bit 4 may not have valid overlap with. In this
# case, the counts in bit 3 become useless for bit 4 even if the preimage
# in bit 4 has valid overlap with preimages in bit 3. I thought of a
# possible solution though, it requires recomputing the counts along a
# certain path. If the grid has the following cells
#   _____________
#   |     |     |
#   |  3  |  4  |
#   |_____|_____|
#   |     |     |
#   |  2  |  5  |
#   |_____|_____|
#   |     |     |
#   |  1  |  6  |
#   |_____|_____|
#
# Assume I've computed the counts of paths to preimages in 1, 2, 3 and 4
# (and in that order). If I want to compute the number of combinations of
# preimages for bits 1, 2, 3, 4 that lead to preimage i in bit 5, then I'll
# have to recompute the number of combinations for 2, 3 and 4 excluding any
# combinations that do not have valid overlap with preimage i in bit 5.
# Then the num of comb that lead to preimage i in bit 5 should be the sum
# of the num of comb that lead to preimage j in bit 4 for all preimage j
# that preimage i has valid overlap with.
# However, when computing the number of paths to a preimage of bit 6, we'd
# have to recompute paths to preimages in bit 5.
#
# It seems much easier to just list preimages for each column and then
# to count the number of valid combinations of those.


# # Not enough time in life of universe to compute for g=9x50 grid of False
# def comb(lp, i_lcol):
#     i_rcol = i_lcol + 1
#     if i_rcol == w:
#         return 1
#     msum = 0
#     for rp in cpi[g[i_rcol]]:
#         if lp == rp[0]:
#             msum += comb(rp[1], i_rcol)
#     return msum
# msum = 0
# for lp in cpi[g[0]]:
#     msum += comb(lp[1], 0)
# return msum










# grid = [
# [True, True, False, False]*10,
# [False, True, False, False, True, False, False, False]*5,
# [False, True, False, False]*10,
# [True, False, True, False]*10,
# [False, False, False, False, False, False, False, False]*5,
# [False, True, False, False]*10,
# [False, False, False, False, False, False, False, False]*5,
# [False, False, False, False]*10,
# [False, False, False, True]*10,
# ]
# expect = 'a lot'
grid = [[False]*50 for _ in range(9)]
expect = 'idk'
# grid = [
#     [True, False, True],
#     [False, True, False],
#     [True, False, True]
# ]
# expect = 4
# grid = [
#     [True, False],
#     [False, True],
# ]
# expect = 12
# grid = [[False]*50 for _ in range(9)]
# expect = 'a lot'
# grid = [
#     [False] for _ in range(3)
# ]
# expect = 'idk'

import time

start = time.time()
res = answer(grid)
span = time.time() - start

print(span*1000)
print("Got: ", res)
print("Exp: ", expect)
