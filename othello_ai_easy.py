import sys
import numpy as np

BLACK = 1
WHITE = -1
EMPTY = 0
BOARD_SIZE = 8

# 正しい8方向ベクトルに修正（重複を無くし、全方向を網羅）
DX = [-1, 1, 0, 0, -1, -1, 1, 1]
DY = [0, 0, -1, 1, -1, 1, -1, 1]

# 初期配置
def init_board():
    board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
    board[3, 3] = WHITE
    board[3, 4] = BLACK
    board[4, 3] = BLACK
    board[4, 4] = WHITE
    return board

# 合法手の取得
def get_legal_moves(board, player):
    str_board = _convert_to_str_board(board)
    str_stone = 'B' if player == BLACK else 'W'
    return legal(str_board, str_stone)

# 石を置く
def make_move(board, row, col, player):
    str_board = _convert_to_str_board(board)
    str_stone = 'B' if player == BLACK else 'W'
    new_str_board = mk_new_board(str_board, row, col, str_stone)

    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if new_str_board[i][j] == 'B':
                board[i, j] = BLACK
            elif new_str_board[i][j] == 'W':
                board[i, j] = WHITE
            else:
                board[i, j] = EMPTY
    return board

# 石の数を数える
def count_pieces(board):
    black_count = np.sum(board == BLACK)
    white_count = np.sum(board == WHITE)
    return black_count, white_count

# AIの手
def select_ai_move(board, player):
    str_board = _convert_to_str_board(board)
    str_stone = 'B' if player == BLACK else 'W'
    return select_move(str_board, str_stone)

# 勝ち負け判定
def _convert_to_str_board(board):
    str_board = []
    for i in range(BOARD_SIZE):
        row_str = ""
        for j in range(BOARD_SIZE):
            if board[i, j] == BLACK:
                row_str += 'B'
            elif board[i, j] == WHITE:
                row_str += 'W'
            else:
                row_str += '.'
        str_board.append(row_str)
    return str_board

def in_board(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def mob(board, x, y):
    ret = 0
    for d in range(8):
        nx, ny = x + DX[d], y + DY[d]
        if in_board(nx, ny) and board[nx][ny] == '.':
            ret += 1
    return ret

def mk_new_board(board, x, y, stone):
    if not in_board(x, y) or board[x][y] != '.':
        return board

    new_board = [list(row) for row in board]
    enm = 'W' if stone == 'B' else 'B'
    new_board[x][y] = stone

    for d in range(8):
        nx, ny = x + DX[d], y + DY[d]
        path = []

        while in_board(nx, ny) and new_board[nx][ny] == enm:
            path.append((nx, ny))
            nx += DX[d]
            ny += DY[d]

        if in_board(nx, ny) and new_board[nx][ny] == stone:
            for px, py in path:
                new_board[px][py] = stone

    return ["".join(row) for row in new_board]

def legal(board, stone):
    vec_ret = []
    enm = 'W' if stone == 'B' else 'B'

    for i in range(8):
        for j in range(8):
            if board[i][j] != '.':
                continue

            is_legal = False
            for d in range(8):
                nx, ny = i + DX[d], j + DY[d]
                count = 0

                while in_board(nx, ny) and board[nx][ny] == enm:
                    count += 1
                    nx += DX[d]
                    ny += DY[d]

                if count > 0 and in_board(nx, ny) and board[nx][ny] == stone:
                    is_legal = True
                    break

            if is_legal:
                vec_ret.append((i, j))
    return vec_ret

# 石をひっくり返す
def rev_stone(board, x, y, stone):
    total_rev = 0
    total_mob = 0
    enm = 'W' if stone == 'B' else 'B'

    if not in_board(x, y) or board[x][y] != '.':
        return 0, 0

    for d in range(8):
        nx, ny = x + DX[d], y + DY[d]
        path = []

        while in_board(nx, ny) and board[nx][ny] == enm:
            path.append((nx, ny))
            nx += DX[d]
            ny += DY[d]

        if in_board(nx, ny) and board[nx][ny] == stone:
            total_rev += len(path)
            for px, py in path:
                total_mob += mob(board, px, py)

    return total_rev, total_mob

# 全ての石を数える
def evaluate(board, stone):
    black = 0
    white = 0
    count = 0
    for i in range(8):
        for k in range(8):
            now_score = 1
            if (i == 0 or i == 7) and (k == 0 or k == 7):
                now_score += 1
            if board[i][k] == 'B':
                black += now_score
            elif board[i][k] == 'W':
                white += now_score
            if board[i][k] != '.':
                count += 1

    if stone == 'B':
        return black, count
    else:
        return white, count

# スコアリング関数
def nega_alpha(board, depth, alpha, beta, stone):
    if depth == 0:
        return evaluate(board, stone)[0]

    enm = 'W' if stone == 'B' else 'B'
    moves = legal(board, stone)

    if not moves:
        if not legal(board, enm):
            return evaluate(board, stone)[0]
        return -nega_alpha(board, depth - 1, -beta, -alpha, enm)

    max_score = -1000000
    for mov in moves:
        next_board = mk_new_board(board, mov[0], mov[1], stone)
        score = -nega_alpha(next_board, depth - 1, -beta, -alpha, enm)

        max_score = max(max_score, score)
        alpha = max(alpha, score)
        if alpha >= beta:
            break

    return max_score

# 動きの決定
def select_move(board, stone):
    import random
    can_move = legal(board, stone)
    if not can_move:
        return None

    my_stone = stone
    enm_stone = 'W' if my_stone == 'B' else 'B'

    total_stones = sum(8 - row.count('.') for row in board)

    weak = [[0] * 8 for _ in range(8)]
    strongest = (-float('inf'), -1, -1)

    for i, k in can_move:
        if (i <= 1 or i >= 6) or (k <= 1 or k >= 6): weak[i][k] -= 20
        if (i == 0 or i == 7) and (k == 0 or k == 7): weak[i][k] += 100
        if (2 <= i <= 5) and (2 <= k <= 5): weak[i][k] += 20
        if (i == 1 or i == 6) and (k == 1 or k == 6): weak[i][k] -= 80

        reversed_count, reversed_mob = rev_stone(board, i, k, my_stone)

        alpha = -1000000
        beta = 1000000
        depth = 3

        if total_stones <= 16:
            weak[i][k] -= (reversed_count - 1)
            next_board = mk_new_board(board, i, k, my_stone)
            weak[i][k] += nega_alpha(next_board, depth, alpha, beta, enm_stone) // 2
        elif total_stones <= 48:
            weak[i][k] -= reversed_mob * 5
            weak[i][k] -= (reversed_count - 1)
            next_board = mk_new_board(board, i, k, my_stone)
            weak[i][k] += nega_alpha(next_board, depth, alpha, beta, enm_stone) // 2
        else:
            weak[i][k] += reversed_count
            next_board = mk_new_board(board, i, k, my_stone)
            weak[i][k] += nega_alpha(next_board, depth, alpha, beta, enm_stone) // 2

        if strongest[0] <= weak[i][k]:
            strongest = (weak[i][k], i, k)

    if strongest[1] == -1 or strongest[2] == -1:
        return None
    return strongest[1], strongest[2]
