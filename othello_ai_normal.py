import numpy as np

EMPTY, BLACK, WHITE = 0, 1, -1
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              ( 0, -1),          ( 0, 1),
              ( 1, -1), ( 1, 0), ( 1, 1)]

BOARD_SIZE = 8

# スコアテーブルの生成
def generate_score_table(size):
    table = np.full((size, size), 3)
    table[0, :] = 5; table[-1, :] = 5; table[:, 0] = 5; table[:, -1] = 5
    if size > 4:
        table[1, :] = -5; table[-2, :] = -5; table[:, 1] = -5; table[:, -2] = -5
    if size > 4:
        for i in [2, -3]:
            for j in [0, 1, 2, -3, -2, -1]:
                if 0 <= i < size and 0 <= j < size:
                    table[i, j] = 15 if j in [2, -3] else -5
                    table[j, i] = 15 if j in [2, -3] else -5
    if size > 2:
        table[1, 1] = -80; table[1, -2] = -80; table[-2, 1] = -80; table[-2, -2] = -80
        table[0, 1] = -40; table[1, 0] = -40; table[0, -2] = -40; table[1, -1] = -40
        table[-1, 1] = -40; table[-2, 0] = -40; table[-1, -2] = -40; table[-2, -1] = -40
    table[0, 0] = 120; table[0, -1] = 120; table[-1, 0] = 120; table[-1, -1] = 120
    return table

SCORE_TABLE = generate_score_table(BOARD_SIZE)

# ボードの初期化
def init_board():
    board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
    mid = BOARD_SIZE // 2
    board[mid - 1, mid - 1] = WHITE
    board[mid - 1, mid] = BLACK
    board[mid, mid - 1] = BLACK
    board[mid, mid] = WHITE
    return board

def in_bounds(x, y):
    return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE

# 挟み込み判定と石の取得
def get_flips(board, x, y, player):
    if board[x, y] != EMPTY:
        return []
    flips = []
    for dx, dy in DIRECTIONS:
        nx, ny = x + dx, y + dy
        line = []
        while in_bounds(nx, ny) and board[nx, ny] == -player:
            line.append((nx, ny))
            nx += dx; ny += dy
        if in_bounds(nx, ny) and board[nx, ny] == player and line:
            flips.extend(line)
    return flips

# 合法手（おける場所）の取得：GUI（main.py）と完全連動
def get_legal_moves(board, player):
    if board is None or isinstance(board, bool):
        return []
    return [(x, y) for x in range(BOARD_SIZE) for y in range(BOARD_SIZE) if get_flips(board, x, y, player)]

# GUI側がフリーズしないように、配置後の新しい配列を返す仕様に修正
def make_move(board, x, y, player):
    if board is None or isinstance(board, bool):
        return board
    flips = get_flips(board, x, y, player)
    if not flips:
        return board  # 置けない場合はそのまま返す

    temp_board = board.copy()
    temp_board[x, y] = player
    for fx, fy in flips:
        temp_board[fx, fy] = player
    return temp_board  # 変更後の新しいボード配列を返す

# 石の数を数える
def count_pieces(board):
    if board is None or isinstance(board, bool):
        return 0, 0
    return int(np.sum(board == BLACK)), int(np.sum(board == WHITE))
# ボードの評価関数
def evaluate_board(board, my_color):
    dynamic_table = SCORE_TABLE.copy()
    corners = [
        ((0, 0), [(0, 1), (1, 0), (1, 1)]),
        ((0, -1), [(0, -2), (1, -1), (1, -2)]),
        ((-1, 0), [(-1, 1), (-2, 0), (-2, 1)]),
        ((-1, -1), [(-1, -2), (-2, -1), (-2, -2)])
    ]
    for (cx, cy), neighbors in corners:
        owner = board[cx, cy]
        if owner != EMPTY:
            for nx, ny in neighbors:
                if owner == my_color:
                    dynamic_table[nx, ny] = 30
                else:
                    dynamic_table[nx, ny] = -100

    score = 0
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i, j] == my_color:
                score += dynamic_table[i, j]
            elif board[i, j] == -my_color:
                score -= dynamic_table[i, j]
    return score

# AIの手の選択（中盤用：Alpha-Beta法）
def alphabeta(board, depth, alpha, beta, player, my_color):
    legal_moves = get_legal_moves(board, player)
    opponent_moves = get_legal_moves(board, -player)

    if depth == 0 or (not legal_moves and not opponent_moves):
        return evaluate_board(board, my_color), None

    if not legal_moves:
        score, _ = alphabeta(board, depth - 1, alpha, beta, -player, my_color)
        return score, None

    legal_moves.sort(key=lambda m: SCORE_TABLE[m[0], m[1]], reverse=True)

    best_move = None
    if player == my_color:
        best_score = -float('inf')
        for move in legal_moves:
            temp_board = make_move(board, move[0], move[1], player)
            score, _ = alphabeta(temp_board, depth - 1, alpha, beta, -player, my_color)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        return best_score, best_move
    else:
        best_score = float('inf')
        for move in legal_moves:
            temp_board = make_move(board, move[0], move[1], player)
            score, _ = alphabeta(temp_board, depth - 1, alpha, beta, -player, my_color)
            if score < best_score:
                best_score = score
                best_move = move
            beta = min(beta, best_score)
            if beta <= alpha:
                break
        return best_score, best_move

# 終盤用のAIの手の選択（完全読み切り：Alpha-Beta法）
def endgame_alphabeta(board, alpha, beta, player, my_color):
    legal_moves = get_legal_moves(board, player)
    opponent_moves = get_legal_moves(board, -player)

    if not legal_moves and not opponent_moves:
        b_cnt, w_cnt = count_pieces(board)
        my_count = b_cnt if my_color == BLACK else w_cnt
        opp_count = w_cnt if my_color == BLACK else b_cnt
        return my_count - opp_count, None

    if not legal_moves:
        score, _ = endgame_alphabeta(board, alpha, beta, -player, my_color)
        return score, None

    def evaluate_move_for_ordering(move):
        temp = make_move(board, move[0], move[1], player)
        return -len(get_legal_moves(temp, -player))

    legal_moves.sort(key=evaluate_move_for_ordering, reverse=True)

    best_move = None
    if player == my_color:
        best_score = -float('inf')
        for move in legal_moves:
            temp_board = make_move(board, move[0], move[1], player)
            score, _ = endgame_alphabeta(temp_board, alpha, beta, -player, my_color)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        return best_score, best_move
    else:
        best_score = float('inf')
        for move in legal_moves:
            temp_board = make_move(board, move[0], move[1], player)
            score, _ = endgame_alphabeta(temp_board, alpha, beta, -player, my_color)
            if score < best_score:
                best_score = score
                best_move = move
            beta = min(beta, best_score)
            if beta <= alpha:
                break
        return best_score, best_move

# GUIから呼び出されるAIの最善手決定関数
def select_ai_move(board, player):
    if board is None or isinstance(board, bool):
        return None

    empty_count = np.sum(board == EMPTY)

    if empty_count <= 8:
        _, best_move = endgame_alphabeta(board, -float('inf'), float('inf'), player, my_color=player)
    else:
        SEARCH_DEPTH = 5 if empty_count <= 12 else 3
        _, best_move = alphabeta(board, SEARCH_DEPTH, -float('inf'), float('inf'), player, my_color=player)

    return best_move
