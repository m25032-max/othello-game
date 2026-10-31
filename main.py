import tkinter as tk
import threading
import othello_ai_easy as ai_easy
import othello_ai_normal as ai_normal
import othello_ai_hard as ai_hard
import othello_ai_death as ai_death

class OthelloGUI:
    # 色の定義
    COLOR_ORANGE = "#FF5F1F"
    COLOR_DARK_ORANGE = "#CC4B14"

    # GUIの初期化コード
    def __init__(self, root):
        self.root = root
        self.root.title("オセロ - 黒（人間） vs 白（AI）")
        self.cell_size = 60
        self.ai = ai_normal
        self.difficulty_name = "ふつう"
        self.board = None
        self.current_player = self.ai.BLACK
        self.game_over = False
        self.is_waiting = False
        self.is_game_started = False
        self.restart_btn = None
        self.end_home_btn = None
        self.offset_x = 0
        self.offset_y = 0
        self._current_msg = None

        self.main_frame = tk.Frame(root)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.home_frame = None
        self.game_frame = None
        self.canvas = None
        self.header_frame = None

        self.root.geometry(f"{self.cell_size * self.ai.BOARD_SIZE}x{self.cell_size * self.ai.BOARD_SIZE + 90}")
        self.show_home_screen()

    # ホーム画面のコード
    def show_home_screen(self):
        self.clear_frames()
        self.is_game_started = False
        self.is_waiting = False
        self.game_over = False
        self.home_frame = tk.Frame(self.main_frame, bg="white")
        self.home_frame.pack(expand=True, fill="both")

        title_label = tk.Label(self.home_frame, text="リバーシ / オセロ", font=("Arial", 26, "bold"), fg=self.COLOR_ORANGE, bg="white")
        title_label.pack(pady=(50, 10))
        subtitle_label = tk.Label(self.home_frame, text="黒（人間） vs 白（AI）", font=("Arial", 13, "bold"), fg=self.COLOR_ORANGE, bg="white")
        subtitle_label.pack(pady=(0, 40))
        diff_frame = tk.Frame(self.home_frame, bg="white")
        diff_frame.pack(pady=10)
        diff_label = tk.Label(diff_frame, text="難易度を選択してください：", font=("Arial", 12, "bold"), fg=self.COLOR_ORANGE, bg="white")
        diff_label.pack(pady=(0, 15))
        btn_diff_frame = tk.Frame(diff_frame, bg="white")
        btn_diff_frame.pack()

        self.btn_easy = tk.Button(btn_diff_frame, text="かんたん", font=("Arial", 11, "bold"), bg="white", fg=self.COLOR_ORANGE, activebackground="white", activeforeground=self.COLOR_ORANGE, bd=2, relief="raised", padx=10, pady=5, command=lambda: self.select_difficulty_on_home(ai_easy, "かんたん"))
        self.btn_normal = tk.Button(btn_diff_frame, text="ふつう", font=("Arial", 11, "bold"), bg="white", fg=self.COLOR_ORANGE, activebackground="white", activeforeground=self.COLOR_ORANGE, bd=2, relief="raised", padx=10, pady=5, command=lambda: self.select_difficulty_on_home(ai_normal, "ふつう"))
        self.btn_hard = tk.Button(btn_diff_frame, text="むずかしい", font=("Arial", 11, "bold"), bg="white", fg=self.COLOR_ORANGE, activebackground="white", activeforeground=self.COLOR_ORANGE, bd=2, relief="raised", padx=10, pady=5, command=lambda: self.select_difficulty_on_home(ai_hard, "むずかしい"))
        self.btn_death = tk.Button(btn_diff_frame, text="デス", font=("Arial", 11, "bold"), bg="white", fg=self.COLOR_ORANGE, activebackground="white", activeforeground=self.COLOR_ORANGE, bd=2, relief="raised", padx=10, pady=5, command=lambda: self.select_difficulty_on_home(ai_death, "デス"))

        self.btn_easy.pack(side="left", padx=5)
        self.btn_normal.pack(side="left", padx=5)
        self.btn_hard.pack(side="left", padx=5)
        self.btn_death.pack(side="left", padx=5)
        self.update_home_difficulty_buttons()

        start_btn = tk.Button(self.home_frame, text="ゲーム開始", command=self.start_game_from_home, font=("Arial", 14, "bold"), bg="white", fg=self.COLOR_ORANGE, activebackground="white", activeforeground=self.COLOR_ORANGE, bd=2, relief="raised", padx=30, pady=10)
        start_btn.pack(pady=(50, 10))

    # 難易度選択の処理コード
    def select_difficulty_on_home(self, ai_module, name):
        self.ai = ai_module
        self.difficulty_name = name
        self.update_home_difficulty_buttons()

    # 難易度ボタン用のコード
    def update_home_difficulty_buttons(self):
        for btn, name in [(self.btn_easy, "かんたん"), (self.btn_normal, "ふつう"), (self.btn_hard, "むずかしい"), (self.btn_death, "デス")]:
            if self.difficulty_name == name:
                btn.config(bg="#FFF0E5", fg=self.COLOR_DARK_ORANGE, relief="sunken")
            else:
                btn.config(bg="white", fg=self.COLOR_ORANGE, relief="raised")
    # ホームからゲームを開始するコード
    def start_game_from_home(self):
        self.clear_frames()
        self.setup_game_screen()
        self.is_game_started = True
        self.restart_game()

    # ゲーム画面のセットアップコード
    def setup_game_screen(self):
        self.game_frame = tk.Frame(self.main_frame, bg="white")
        self.game_frame.pack(expand=True, fill="both")
        self.header_frame = tk.Frame(self.game_frame, bg="white", pady=5)
        self.header_frame.grid(row=0, column=0, sticky="ew")

        # 確認を挟まず、押したらダイレクトにshow_home_screenを呼ぶように修正
        self.btn_home = tk.Button(self.header_frame, text="ホームへ戻る", font=("Arial", 10, "bold"), bg="white", fg=self.COLOR_ORANGE, activebackground="white", activeforeground=self.COLOR_ORANGE, command=self.show_home_screen)
        self.btn_home.pack(side="left", padx=10)

        info_label = tk.Label(self.header_frame, text=f"難易度: {self.difficulty_name}", font=("Arial", 11, "bold"), fg=self.COLOR_ORANGE, bg="white")
        info_label.pack(side="right", padx=15)
        self.canvas = tk.Canvas(self.game_frame, bg="#1e1e1e", highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Configure>", self.on_resize)

        self.game_frame.rowconfigure(1, weight=1)
        self.game_frame.columnconfigure(0, weight=1)

    # 盤面のフレームをクリアするコード
    def clear_frames(self):
        if self.home_frame: self.home_frame.destroy(); self.home_frame = None
        if self.game_frame: self.game_frame.destroy(); self.game_frame = None

    # 盤面のリサイズ処理コード
    def on_resize(self, event):
        if not self.canvas: return
        self.cell_size = max(min(event.width, event.height) // self.ai.BOARD_SIZE, 10)
        board_total_size = self.cell_size * self.ai.BOARD_SIZE
        self.offset_x = (event.width - board_total_size) // 2
        self.offset_y = (event.height - board_total_size) // 2
        self.draw_board()

    # 盤面の描画コード（表示漏れ対策の強制リフレッシュを導入）
    def draw_board(self):
        if not self.canvas: return
        if self.board is None or isinstance(self.board, bool): return

        self.canvas.delete("all")
        board_total_size = self.cell_size * self.ai.BOARD_SIZE
        self.canvas.create_rectangle(self.offset_x, self.offset_y, self.offset_x + board_total_size, self.offset_y + board_total_size, fill="darkgreen", outline="")

        # 常に最新の合法手（おける場所）を同期して取得
        legal_moves = self.ai.get_legal_moves(self.board, self.current_player)

        for i in range(self.ai.BOARD_SIZE):
            for j in range(self.ai.BOARD_SIZE):
                x1, y1 = self.offset_x + j * self.cell_size, self.offset_y + i * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="black")
                padding = max(self.cell_size // 12, 2)

                if self.board[i, j] == self.ai.BLACK:
                    self.canvas.create_oval(x1+padding, y1+padding, x2-padding, y2-padding, fill="black")
                elif self.board[i, j] == self.ai.WHITE:
                    self.canvas.create_oval(x1+padding, y1+padding, x2-padding, y2-padding, fill="white")
                # あなたの番（黒）、かつAI思考待ちでなく、ゲーム中の場合にガイドを描画
                elif (i, j) in legal_moves and self.current_player == self.ai.BLACK and not self.is_waiting and not self.game_over:
                    radius = max(self.cell_size // 8, 4)
                    cx, cy = x1 + self.cell_size // 2, y1 + self.cell_size // 2
                    self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill="#55aa55", outline="")

        b_cnt, w_cnt = self.ai.count_pieces(self.board)
        self.root.title(f"オセロ - {'黒（人間）●' if self.current_player == self.ai.BLACK else '白（AI）○'}の番 [{b_cnt}:{w_cnt}]")

        if hasattr(self, '_current_msg') and self._current_msg:
            self._render_message_text(self._current_msg)

        if self.game_over:
            self.show_end_message()

        # 画面描画の遅延タスクを今すぐ強制処理し、描画漏れを確実に防ぐ
        self.root.update_idletasks()
    # メッセージ表示の時間・状態の管理コード
    def show_message(self, text):
        if not self.canvas: return
        self._current_msg = text
        self._render_message_text(text)
        def clear_msg():
            self._current_msg = None
            if self.canvas: self.canvas.delete("msg")
        self.root.after(800, clear_msg)

    # メッセージ表示の見た目の描画コード
    def _render_message_text(self, text):
        center_x, center_y = self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2
        font_size = max(self.cell_size // 3, 10)
        msg_w = max(len(text) * font_size, 120)
        self.canvas.create_rectangle(center_x - msg_w, center_y - 30, center_x + msg_w, center_y + 30, fill="black", outline=self.COLOR_ORANGE, width=2, tags="msg")
        self.canvas.create_text(center_x, center_y, text=text, fill=self.COLOR_ORANGE, font=("Arial", font_size, "bold"), anchor="center", tags="msg")

    # ゲーム終了時のメッセージ表示コード
    def show_end_message(self):
        if not self.canvas: return
        black_count, white_count = self.ai.count_pieces(self.board)
        is_player_win = black_count > white_count

        if is_player_win:
            result_text = f"プレイヤー（黒）の勝ち！\n{black_count} vs {white_count}"
            box_width = 220
        elif white_count > black_count:
            result_text = f"AI（白）の勝ち！\n{black_count} vs {white_count}"
            box_width = 220
        else:
            result_text = f"引き分け！\n{black_count} vs {white_count}"
            box_width = 220

        # パーティクルアニメーションの初期化コード
        if is_player_win and (not hasattr(self, 'particles') or not self.particles):
            import random
            self.particles = []
            colors = ["#FF5F1F", "#FFD700", "#00FF7F", "#1E90FF", "#FF69B4", "#00FFFF"]
            w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
            for _ in range(70):
                self.particles.append({
                    "x": random.randint(10, w - 10),
                    "y": random.randint(-50, 0),
                    "vx": random.uniform(-2, 2),
                    "vy": random.uniform(1, 4),
                    "color": random.choice(colors),
                    "size": random.randint(4, 8)
                })
            self.animate_particles()

        # 結果表示のコード
        center_x, center_y = self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2
        font_size = max(self.cell_size // 5, 10)

        self.canvas.create_rectangle(center_x - box_width, center_y - 70, center_x + box_width, center_y + 70, fill="black", outline=self.COLOR_ORANGE, width=2, tags="ui_end")
        self.canvas.create_text(center_x, center_y - 20, text=result_text, fill=self.COLOR_ORANGE, font=("Arial", font_size, "bold"), anchor="center", justify="center", tags="ui_end")

        if self.restart_btn is None:
            self.restart_btn = tk.Button(self.canvas, text="もう一度遊ぶ", command=self.restart_game, font=("Arial", 11, "bold"), bg="white", fg=self.COLOR_ORANGE, activebackground="white", activeforeground=self.COLOR_ORANGE, bd=0, relief="flat")
            self.canvas.create_window(center_x - 65, center_y + 35, window=self.restart_btn, tags="restart_tag")

        if self.end_home_btn is None:
            self.end_home_btn = tk.Button(self.canvas, text="ホームへ戻る", command=self.show_home_screen, font=("Arial", 11, "bold"), bg="white", fg=self.COLOR_ORANGE, activebackground="white", activeforeground=self.COLOR_ORANGE, bd=0, relief="flat")
            self.canvas.create_window(center_x + 65, center_y + 35, window=self.end_home_btn, tags="end_home_tag")

    # パーティクルアニメーションのコード
    def animate_particles(self):
        if not self.game_over or not self.canvas: return
        self.canvas.delete("particle")
        h = self.canvas.winfo_height()
        still_running = False

        if hasattr(self, 'particles') and self.particles:
            for p in self.particles:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] += 0.05

                if p["y"] < h:
                    still_running = True
                    self.canvas.create_rectangle(p["x"], p["y"], p["x"]+p["size"], p["y"]+p["size"], fill=p["color"], outline="", tags="particle")

        self.canvas.tag_raise("ui_end")
        self.canvas.tag_raise("restart_tag")
        self.canvas.tag_raise("end_home_tag")

        if still_running:
            self.root.after(30, self.animate_particles)

    # ゲームを再起動するコード
    def restart_game(self):
        self._current_msg = None
        if hasattr(self, 'particles'): self.particles = []

        if self.restart_btn: self.restart_btn.destroy(); self.restart_btn = None
        if self.end_home_btn: self.end_home_btn.destroy(); self.end_home_btn = None

        if self.canvas:
            self.canvas.delete("restart_tag")
            self.canvas.delete("end_home_tag")
            self.canvas.delete("particle")
            self.canvas.delete("ui_end")

        if hasattr(self, 'btn_home') and self.btn_home:
            self.btn_home.config(state="normal")

        self.board = self.ai.init_board()
        self.current_player = self.ai.BLACK
        self.game_over = False
        self.is_waiting = False
        self.draw_board()

    # クリックイベントの処理コード
    def click(self, event):
        if self.current_player != self.ai.BLACK or self.game_over or self.is_waiting: return

        click_x, click_y = event.x - self.offset_x, event.y - self.offset_y
        row, col = click_y // self.cell_size, click_x // self.cell_size
        if not (0 <= row < self.ai.BOARD_SIZE and 0 <= col < self.ai.BOARD_SIZE): return

        if (row, col) in self.ai.get_legal_moves(self.board, self.current_player):
            res = self.ai.make_move(self.board, row, col, self.current_player)
            if res is not None and not isinstance(res, bool):
                self.board = res

            self.current_player = self.ai.WHITE
            self.is_waiting = True
            self.draw_board()
            self.root.after(200, self.check_turn_and_run)

    # AIの手を計算して適用するコード
    def ai_move(self):
        def th_target():
            move = self.ai.select_ai_move(self.board, self.ai.WHITE)
            self.root.after(0, self.apply_ai_move, move)
        threading.Thread(target=th_target, daemon=True).start()

    # AIの手を適用するコード
    def apply_ai_move(self, move):
        if move:
            row, col = move
            res = self.ai.make_move(self.board, row, col, self.ai.WHITE)
            if res is not None and not isinstance(res, bool):
                self.board = res

        self.current_player = self.ai.BLACK
        self.is_waiting = False
        self.draw_board()
        self.root.after(200, self.check_turn_and_run)

    # AIがパスする時用のコード
    def resume_after_pass(self, next_player):
        self.is_waiting = False
        self.current_player = next_player
        self.draw_board()
        self.check_turn_and_run()

    # ゲームのターンをチェックして進行するコード
    def check_turn_and_run(self):
        if self.board is None or isinstance(self.board, bool): return

        black_count, white_count = self.ai.count_pieces(self.board)
        if black_count == 0 or white_count == 0:
            self.game_over = True
            self.draw_board()
            return

        if self.game_over: return
        human_moves = self.ai.get_legal_moves(self.board, self.ai.BLACK)
        ai_moves = self.ai.get_legal_moves(self.board, self.ai.WHITE)
        if not human_moves and not ai_moves: self.game_over = True; self.draw_board(); return

        if self.current_player == self.ai.WHITE:
            if ai_moves:
                self.is_waiting = True
                self.root.after(500, self.ai_move)
            else:
                self.show_message("白（AI）パス")
                self.is_waiting = True
                self.root.after(800, lambda: self.resume_after_pass(self.ai.BLACK))
        elif self.current_player == self.ai.BLACK:
            if not human_moves:
                self.show_message("黒（人間）パス")
                self.is_waiting = True
                self.root.after(800, lambda: self.resume_after_pass(self.ai.WHITE))
            else:
                self.is_waiting = False
                self.draw_board()

# メインループ
if __name__ == "__main__":
    root = tk.Tk()
    app = OthelloGUI(root)
    root.mainloop()
