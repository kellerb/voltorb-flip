import collections
import itertools

import attr
import z3

#https://docs.python.org/3/library/itertools.html#itertools-recipes
def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)

@attr.s
class Constraint:
    sum_ = attr.ib()
    zeros = attr.ib()

def solve_vortorb_flip(col_constraints, row_constraints, cell_constraints):
    '''
    col_constraints: [Constraint], left-to-right
    row_constraints: [Constraint], top-to-bottom
    cell_constraints: {(row, col): val}

    returns num_solutions, 2d-array[row][col]{val: probability}
    '''
    cel_val_upper_bound = max(c.sum_ for c in col_constraints)
    cel_val_upper_bound = max(cel_val_upper_bound, max(c.sum_ for c in row_constraints))
    cel_val_upper_bound = min(cel_val_upper_bound, 3)

    s = z3.Solver()
    n = len(col_constraints)
    xss = [[z3.Int('x{}{}'.format(i, j)) for j in range(n)] for i in range(n)]
    # cell constraints
    for i in range(n):
        for j in range(n):
            val = cell_constraints.get((i, j))
            if val is not None:
                s.add(xss[i][j] == val)
            else:
                s.add(0 <= xss[i][j], xss[i][j] <= cel_val_upper_bound)

    # row constraints
    for i in range(n):
        s.add(z3.Sum(xss[i]) == row_constraints[i].sum_)
        s.add(z3.PbEq([(xss[i][j]==0, 1) for j in range(n)], row_constraints[i].zeros))

    # col constraints
    for j in range(n):
        s.add(z3.Sum([xss[i][j] for i in range(n)]) == col_constraints[j].sum_)
        s.add(z3.PbEq([(xss[i][j]==0, 1) for i in range(n)], col_constraints[j].zeros))

    num_soln = 0
    soln = [[collections.defaultdict(int) for j in range(n)] for i in range(n)]
    while s.check() == z3.sat:
        num_soln += 1
        m = s.model()
        for i in range(n):
            for j in range(n):
                soln[i][j][m[xss[i][j]].as_long()] += 1
        s.add(z3.Or([xss[i][j] != m[xss[i][j]] for i in range(n) for j in range(n)]))

    for i in range(n):
        for j in range(n):
            for k, v in list(soln[i][j].items()):
                soln[i][j][k] = v/num_soln
    return num_soln, soln

def get_col_row_constraints():
    s = input('Enter col constraints left-to-right, then row constraints top-to-bottom as repeated "{sum} {voltorb count}"\n')
    l = list(map(int, s.split()))
    grouped_input = [Constraint(sum_=a, zeros=b) for a, b in grouper(l, 2)]
    assert len(grouped_input) % 2 == 0, 'Sum of row count and col count should be even'
    n = len(grouped_input) // 2
    col_constraints = grouped_input[:n]
    row_constraints = grouped_input[n:]
    return col_constraints, row_constraints

def get_cell_constraints():
    s = input('Enter cell constraints as repeated "{row} {col} {val}"\n')
    l = list(map(int, s.split()))
    assert len(l) % 3 == 0, 'Count of cell constraint input items should be multiple of three'
    return {(row, col): val for row, col, val in grouper(l, 3)}

def print_soln(num_soln, soln):
    print('num_soln', num_soln)
    n = len(soln[0])
    soln_print = []
    longest_cell = 0
    for i in range(n):
        row = []
        for j in range(n):
            cell = []
            for k, v in sorted(soln[i][j].items()):
                cell.append('{}: {:.2}'.format(k, v))
            row.append('{{{}}}'.format(', '.join(cell)))
            longest_cell = max(longest_cell, len(row[-1]))
        soln_print.append(row)
    for i in range(n):
        for j in range(n):
            template = '{{:{}}}'.format(longest_cell)
            print(template.format(soln_print[i][j]), end=' ')
        print()

if __name__ == '__main__':
    col_constraints, row_constraints = get_col_row_constraints()
    cell_constraints = get_cell_constraints()
    num_soln, soln = solve_vortorb_flip(col_constraints, row_constraints, cell_constraints)
    print_soln(num_soln, soln)
