#include <iostream>
using std::cout;
using std::endl;
#include <vector>
using std::vector;
#include <array>
using std::array;
#include <unordered_map>
using std::unordered_map;
#include <numeric>
using std::accumulate;

#include <boost/multiprecision/cpp_int.hpp>

using uint = unsigned;

struct pair {
    uint left;
    uint right;
    bool operator==(const pair& o) const {
        return o.left == left && o.right == right;
    }
    pair(uint l, uint r) : left(l), right(r) {}
};

vector<pair> black_preimages = {{2,0},
                                {0,2},
                                {1,0},
                                {0,1}};
vector<pair> white_preimages = {{0,0},
                                {1,1},
                                {2,2},
                                {3,3},
                                {0,3},
                                {3,0},
                                {1,3},
                                {3,1},
                                {2,3},
                                {3,2},
                                {1,2},
                                {2,1}};

using bigint = boost::multiprecision::uint512_t;

// if ROWS or COLS increases, then may need to increase number of bits in bigint
const int ROWS = 9; // memory used is at least 2^(ROWS + 2)
const int COLS = 50;

// useful for fast array lookup later
array<uint, COLS> encode_columns(array<array<bool,ROWS>,COLS>& g) {
    array<uint, COLS> gi;
    for (int j = 0; j < COLS; ++j) {
        uint n = 0;
        for (int i = 0; i < ROWS; ++i) {
            n |= g[ROWS-1-i][j] << i;
        }
        gi[j] = n;
    }
    return gi;
}

uint vertical_reflect(uint col, int rows) {
    uint ret = 0;
    for (int i = 0; i < rows; ++i) {
        ret |= ((col>>(rows-1-i))&1) << i;
    }
    return ret;
}

unordered_map<uint,vector<pair>> get_column_preimages(array<uint, COLS>& gi) {
    unordered_map<uint,vector<pair>> cpi;
    for (const auto& col : gi) {
        if (cpi.count(col))
            continue;
        
        uint vert_refl = vertical_reflect(col, ROWS);
        if (cpi.count(vert_refl)) {
            for (const auto& pi : cpi[vert_refl]) {
                cpi[col].emplace_back(vertical_reflect(pi.left, ROWS + 1),
                                      vertical_reflect(pi.right, ROWS + 1));
            }
            continue;
        }

        vector<pair> scpi = (col & 1) ? black_preimages : white_preimages;
        for (uint i = 1; i < ROWS; ++i) {
            vector<pair> temp;

            vector<pair> blocks = (col & (uint(1) << i)) ? black_preimages : white_preimages;

            for (const auto& pi : scpi) {
                pair top_row { (pi.left >> i) & 1, (pi.right >> i) & 1 };
                for (const auto& block : blocks) {
                    pair bottom_row { block.left & 1, block.right & 1 };
                    if (top_row == bottom_row) {
                        temp.emplace_back(pi.left | ((block.left & 2) << i),
                                          pi.right | ((block.right & 2) << i));
                    }
                }
            }
            scpi = temp;
        }
        cpi[col] = scpi;
    }
    return cpi;
}

int main() {
    // make grid ROWS*COLS grid of false for stress test (maximize number of possible preimages)
    array<bool,ROWS> x; x.fill(false);
    array<array<bool,ROWS>,COLS> g; g.fill(x);

    // encode columns into integers and for each column get its preimages
    auto gi = encode_columns(g);
    auto cpi = get_column_preimages(gi);

    // count of valid paths from preimages of leftmost column (gi[0])
    // to preimages of the ith column (gi[i])
    vector<bigint> lcounts(pow(2, ROWS+1), 0);

    // there is exactly one valid path from preimage j of column i to preimage j of column i
    for (const pair& lp : cpi[gi[0]]) {
        lcounts[lp.right] += 1;
    }

    // dynamic programming
    vector<bigint> rcounts(pow(2,ROWS+1), 0);
    for (int i = 1; i < COLS; ++i) {
        std::fill(rcounts.begin(), rcounts.end(), 0);
        for (const pair& rp : cpi[gi[i]]) {
            rcounts[rp.right] += lcounts[rp.left];
        }
        auto temp = std::move(lcounts);
        lcounts = std::move(rcounts);
        rcounts = std::move(temp);
    }
    bigint sum = accumulate(lcounts.begin(), lcounts.end(), bigint(0));
    cout << sum << endl;
}
