def clamp(val, lo=0, hi=255):
    if val < lo:
        return lo
    if val > hi:
        return hi
    return val


def create_matrix(rows, cols, fill=0.0):
    return [[fill] * cols for _ in range(rows)]


def copy_matrix(mat):
    return [row[:] for row in mat]


def flatten_2d(mat):
    result = []
    for row in mat:
        result.extend(row)
    return result


def reshape_1d(arr, rows, cols):
    return [arr[r * cols:(r + 1) * cols] for r in range(rows)]


def extract_block(matrix, row, col, size=8):
    return [matrix[row + r][col:col + size] for r in range(size)]


def insert_block(matrix, block, row, col):
    for r, brow in enumerate(block):
        for c, val in enumerate(brow):
            matrix[row + r][col + c] = val


def pad_to_multiple(matrix, multiple=8, pad_value=0):
    rows = len(matrix)
    cols = len(matrix[0]) if rows > 0 else 0
    new_rows = rows if rows % multiple == 0 else rows + (multiple - rows % multiple)
    new_cols = cols if cols % multiple == 0 else cols + (multiple - cols % multiple)
    result = create_matrix(new_rows, new_cols, pad_value)
    for r in range(rows):
        for c in range(cols):
            result[r][c] = matrix[r][c]
    return result
