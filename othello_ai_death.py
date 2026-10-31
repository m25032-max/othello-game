import numpy as np

EMPTY, BLACK, WHITE = 0, 1, -1
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              ( 0, -1),          ( 0, 1),
              ( 1, -1), ( 1, 0), ( 1, 1)]

BOARD_SIZE = 8

# スコアテーブルの作成
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
TRANSPOSITION_TABLE = {}

# ボードの初期化
def board_to_hash(board):
    return board.tobytes() if board is not None and not isinstance(board, bool) else b""

# ボードの配置
def init_board():
    board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
    mid = BOARD_SIZE // 2
    board[mid - 1, mid - 1] = WHITE
    board[mid - 1, mid] = BLACK
    board[mid, mid - 1] = BLACK
    board[mid, mid] = WHITE
    global TRANSPOSITION_TABLE
    TRANSPOSITION_TABLE.clear()
    return board

# 画面外チェック
def in_bounds(row, col):
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

# 🛠️ 縦横（row, col）がねじれないよう厳密に修正した挟み込み判定
def get_flips(board, row, col, player):
    if board is None or isinstance(board, bool):
        return []
    if board[row, col] != EMPTY:
        return []
    flips = []
    for drow, dcol in DIRECTIONS:
        nrow, ncol = row + drow, col + dcol
        line = []
        while in_bounds(nrow, ncol) and board[nrow, ncol] == -player:
            line.append((nrow, ncol))
            nrow += drow; ncol += dcol
        if in_bounds(nrow, ncol) and board[nrow, ncol] == player and line:
            flips.extend(line)
    return flips

# 合法手の取得：GUI（main.py）へ正しい (row, col) 形式で返す
def get_legal_moves(board, player):
    if board is None or isinstance(board, bool):
        return []
    return [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if get_flips(board, r, c, player)]

# 🛠️ GUIの仕様に合わせ、元の盤面を直接壊さずに「ひっくり返した後の配列」を返す形に修正
def make_move(board, row, col, player):
    if board is None or isinstance(board, bool):
        return board
    flips = get_flips(board, row, col, player)
    if not flips:
        return board

    temp_board = board.copy()
    temp_board[row, col] = player
    for fr, fc in flips:
        temp_board[fr, fc] = player
    return temp_board

# 石の数を数える
def count_pieces(board):
    if board is None or isinstance(board, bool):
        return 0, 0
    return int(np.sum(board == BLACK)), int(np.sum(board == WHITE))
# AIの手の評価（安定度・着手可能数・スコアテーブルを統合評価）
def evaluate_board(board, my_color, my_moves_count, opp_moves_count):
    dynamic_table = SCORE_TABLE.copy()
    corners = [
        ((0, 0), [(0, 1), (1, 0), (1, 1)]),
        ((0, -1), [(0, -2), (1, -1), (1, -2)]),
        ((-1, 0), [(-1, 1), (-2, 0), (-2, 1)]),
        ((-1, -1), [(-1, -2), (-2, -1), (-2, -2)])
    ]
    for (cr, cc), neighbors in corners:
        owner = board[cr, cc]
        if owner != EMPTY:
            for nr, nc in neighbors:
                dynamic_table[nr, nc] = 30 if owner == my_color else -100

    score = np.sum(board * dynamic_table) * my_color
    score += (my_moves_count - opp_moves_count) * 15

    stable_score = 0
    for cr, cc in [(0, 0), (0, -1), (-1, 0), (-1, -1)]:
        if board[cr, cc] != EMPTY:
            stable_score += 50 if board[cr, cc] == my_color else -50
    score += stable_score
    return score

# AIの手の選択（中盤用：置換表付きAlpha-Beta法）
def alphabeta(board, depth, alpha, beta, player, my_color, best_move_at_parent=None):
    board_hash = (board_to_hash(board), depth, player)
    if board_hash in TRANSPOSITION_TABLE:
        cached_alpha, cached_beta, cached_score, cached_move = TRANSPOSITION_TABLE[board_hash]
        if cached_alpha >= beta: return cached_score, cached_move
        if cached_beta <= alpha: return cached_score, cached_move

    legal_moves = get_legal_moves(board, player)
    opponent_moves = get_legal_moves(board, -player)

    if depth == 0 or (not legal_moves and not opponent_moves):
        my_moves_count = len(legal_moves) if player == my_color else len(opponent_moves)
        opp_moves_count = len(opponent_moves) if player == my_color else len(legal_moves)
        return evaluate_board(board, my_color, my_moves_count, opp_moves_count), None

    if not legal_moves:
        score, _ = alphabeta(board, depth - 1, alpha, beta, -player, my_color)
        return score, None

    # 反復深化による親ノードの最善手があれば最優先で探索（枝刈り効率化）
    if best_move_at_parent and best_move_at_parent in legal_moves:
        legal_moves.remove(best_move_at_parent)
        legal_moves.insert(0, best_move_at_parent)
    else:
        legal_moves.sort(key=lambda m: SCORE_TABLE[m[0], m[1]], reverse=True)

    best_move = None
    original_alpha, original_beta = alpha, beta

    if player == my_color:
        best_score = -float('inf')
        for move in legal_moves:
            temp_board = make_move(board, move[0], move[1], player)
            score, _ = alphabeta(temp_board, depth - 1, alpha, beta, -player, my_color, best_move_at_parent)
            if score > best_score:
                best_score, best_move = score, move
            alpha = max(alpha, best_score)
            if beta <= alpha: break
        TRANSPOSITION_TABLE[board_hash] = (alpha, original_beta, best_score, best_move)
        return best_score, best_move
    else:
        best_score = float('inf')
        for move in legal_moves:
            temp_board = make_move(board, move[0], move[1], player)
            score, _ = alphabeta(temp_board, depth - 1, alpha, beta, -player, my_color, best_move_at_parent)
            if score < best_score:
                best_score, best_move = score, move
            beta = min(beta, best_score)
            if beta <= alpha: break
        TRANSPOSITION_TABLE[board_hash] = (original_alpha, beta, best_score, best_move)
        return best_score, best_move

# 終盤用のAIの手の選択（完全読み切りマスカウント評価）
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

    legal_moves.sort(key=lambda m: SCORE_TABLE[m[0], m[1]], reverse=True)

    best_move = None
    if player == my_color:
        best_score = -float('inf')
        for move in legal_moves:
            temp_board = make_move(board, move[0], move[1], player)
            score, _ = endgame_alphabeta(temp_board, alpha, beta, -player, my_color)
            if score > best_score:
                best_score, best_move = score, move
            alpha = max(alpha, best_score)
            if beta <= alpha: break
        return best_score, best_move
    else:
        best_score = float('inf')
        for move in legal_moves:
            temp_board = make_move(board, move[0], move[1], player)
            score, _ = endgame_alphabeta(temp_board, alpha, beta, -player, my_color)
            if score < best_score:
                best_score, best_move = score, move
            beta = min(beta, best_score)
            if beta <= alpha: break
        return best_score, best_move

# GUI（main.py）から呼び出されるAIの最善手決定関数（反復深化）
def select_ai_move(board, player):
    if board is None or isinstance(board, bool):
        return None

    empty_count = np.sum(board == EMPTY)
    if empty_count <= 10:
        _, best_move = endgame_alphabeta(board, -float('inf'), float('inf'), player, my_color=player)
        return best_move

    # 空きマスに応じて深さを可変（Iterative Deepening）
    target_depth = 5 if empty_count <= 20 else 4
    best_move = None

    for d in range(1, target_depth + 1):
        _, current_best = alphabeta(board, d, -float('inf'), float('inf'), player, my_color=player, best_move_at_parent=best_move)
        if current_best:
            best_move = current_best

    return best_move
