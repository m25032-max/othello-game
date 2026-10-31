import tkinter as tk
import threading
import queue
import math
import random
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageChops, ImageDraw

import othello_ai_easy as ai_easy
import othello_ai_normal as ai_normal
import othello_ai_hard as ai_hard
import othello_ai_death as ai_death


# ==========================================
# Theme
# ==========================================

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class OthelloGUI:

    # Colors
    BG = "#F5F7FA"
    SURFACE = "#FFFFFF"
    SURFACE_ALT = "#F8FAFC"

    PRIMARY = "#F97316"
    PRIMARY_HOVER = "#EA580C"
    PRIMARY_LIGHT = "#FFF1E8"

    TEXT = "#1E293B"
    SUBTEXT = "#64748B"
    BORDER = "#E2E8F0"

    OVERLAY_BG = "#D0D0D0"
    OVERLAY_ACCENT = "#d1501b"
    OVERLAY_ACCENT_HOVER = "#9A3412"
    OVERLAY_SHADOW = "#A8A8A8"
    OVERLAY_TEXT = "#1E293B"
    OVERLAY_SUBTEXT = "#4B5563"

    BOARD = "#27845E"
    BOARD_LINE = "#1B6949"

    BLACK = "#17202A"
    WHITE = "#FFFFFF"
    LEGAL = "#8FE3B5"

    ROULETTE_FRAME_MS = 33
    ROULETTE_FRAMES = 30
    ROULETTE_REVOLUTIONS = 6

    DIFFICULTIES = [
        ("かんたん", ai_easy, "もっとも標準的"),
        ("ふつう", ai_normal, "意外と難しい"),
        ("むずかしい", ai_hard, "自信がある人でも\n負けてしまうことも"),
        ("デス", ai_death, "常に最善の手を打たないと\n負けてしまう"),
    ]

    def __init__(self, root):

        self.root = root
        self.root.title("Reversi - Othello")
        self.root.geometry("1100x780")
        self.root.minsize(800, 650)
        self.root.configure(fg_color=self.BG)

        self.ai = ai_normal
        self.difficulty_name = "ふつう"
        self.human_color = self.ai.BLACK
        self.ai_color = self.ai.WHITE

        self.board = None
        self.current_player = None

        self.game_over = False
        self.is_waiting = False
        self.ai_turn_active = False
        self.is_game_started = False

        self.cell_size = 60
        self.offset_x = 0
        self.offset_y = 0

        self.ai_queue = queue.Queue()
        self.game_token = 0

        self.home_frame = None
        self.game_frame = None
        self.canvas = None
        self.result_overlay = None
        self.result_overlay_data = None
        self.home_logo_image = None
        self.confetti_particles = []
        self.confetti_after_id = None
        self.roulette_data = None
        self.roulette_after_id = None
        self.roulette_ticks = 0
        self.roulette_start_angle = 0.0
        self.roulette_target_angle = 0.0

        self.difficulty_buttons = {}

        self.message_after_id = None
        self.ai_after_id = None
        self.pass_after_id = None

        self.pass_overlay_data = None

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

        self.show_home_screen()

    # ======================================
    # Utility
    # ======================================

    def create_card(self, parent, **kwargs):

        return ctk.CTkFrame(
            parent,
            fg_color=self.SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER,
            **kwargs
        )

    def create_label(
        self,
        parent,
        text,
        size=14,
        weight="normal",
        color=None,
        **kwargs
    ):

        return ctk.CTkLabel(
            parent,
            text=text,
            font=("Arial", size, weight),
            text_color=color or self.TEXT,
            **kwargs
        )

    def clear_frames(self):

        if self.home_frame:
            self.home_frame.destroy()
            self.home_frame = None

        if self.game_frame:
            self.game_frame.destroy()
            self.game_frame = None

        self.canvas = None
        self.result_overlay = None
        self.result_overlay_data = None

    def cancel_scheduled_tasks(self):

        for attr in (
            "message_after_id",
            "ai_after_id",
            "pass_after_id",
            "confetti_after_id",
            "roulette_after_id"
        ):

            task_id = getattr(self, attr)

            if task_id is not None:

                try:
                    self.root.after_cancel(task_id)
                except tk.TclError:
                    pass

                setattr(self, attr, None)

        self.pass_overlay_data = None
        self.roulette_data = None
        self.roulette_ticks = 0
        self.confetti_particles = []
        if self.canvas is not None:
            self.canvas.delete("confetti")
            self.canvas.delete("roulette_overlay")

    def clear_ai_queue(self):

        while True:

            try:
                self.ai_queue.get_nowait()

            except queue.Empty:
                break

    def on_close(self):

        self.game_token += 1
        self.cancel_scheduled_tasks()
        self.root.destroy()

    # ======================================
    # Home Screen
    # ======================================

    def show_home_screen(self):

        self.game_token += 1
        self.cancel_scheduled_tasks()
        self.clear_ai_queue()
        self.clear_frames()

        self.is_game_started = False
        self.is_waiting = False
        self.game_over = False
        self.ai_turn_active = False

        self.root.title("Reversi - Othello")

        self.home_frame = ctk.CTkFrame(
            self.root,
            fg_color=self.BG,
            corner_radius=0
        )

        self.home_frame.pack(
            fill="both",
            expand=True
        )

        container = ctk.CTkFrame(
            self.home_frame,
            fg_color="transparent"
        )

        container.pack(
            expand=True,
            fill="both",
            padx=30,
            pady=30
        )

        # Logo

    #     self.create_label(
    #       container,
    #       "OTHELLO",
    #       size=15,
    #       weight="bold",
    #       color=self.PRIMARY
    #   ).pack(pady=(20, 8))

        logo_path = Path(__file__).resolve().with_name("vs_othello_ai_logo.png")
        with Image.open(logo_path) as source_image:
            logo = source_image.convert("RGBA")

        corner_radius = round(min(logo.size) * 0.11)
        corner_mask = Image.new("L", logo.size, 0)
        ImageDraw.Draw(corner_mask).rounded_rectangle(
            (0, 0, logo.width - 1, logo.height - 1),
            radius=corner_radius,
            fill=255
        )
        logo.putalpha(
            ImageChops.multiply(logo.getchannel("A"), corner_mask)
        )

        display_width = 500
        display_height = round(display_width * logo.height / logo.width)
        self.home_logo_image = ctk.CTkImage(
            light_image=logo,
            size=(display_width, display_height)
        )
        ctk.CTkLabel(
            container,
            text="",
            image=self.home_logo_image,
            fg_color="transparent",
            corner_radius=0
        ).pack(pady=5)

        self.create_label(
            container,
            "部員が作成したオセロAIと対戦!",
            size=14,
            color=self.SUBTEXT
        ).pack(pady=(0, 30))

        # Difficulty card

        card = self.create_card(container)

        card.pack(
            fill="x",
            padx=40,
            pady=10
        )

        inner = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        inner.pack(
            fill="x",
            padx=30,
            pady=25
        )

        self.create_label(
            inner,
            "難易度を選択",
            size=19,
            weight="bold"
        ).pack(anchor="w")

        self.create_label(
            inner,
            "対戦するAIの強さを選んでください。",
            size=12,
            color=self.SUBTEXT
        ).pack(
            anchor="w",
            pady=(5, 20)
        )

        difficulty_frame = ctk.CTkFrame(
            inner,
            fg_color="transparent"
        )

        difficulty_frame.pack(fill="x")

        self.difficulty_buttons = {}

        for name, module, description in self.DIFFICULTIES:

            option = ctk.CTkFrame(
                difficulty_frame,
                fg_color="transparent"
            )
            option.pack(
                side="left",
                expand=True,
                fill="x",
                padx=5
            )

            button = ctk.CTkButton(
                option,
                text=name,
                height=58,
                corner_radius=12,
                border_width=1,
                border_color=self.BORDER,
                fg_color=self.SURFACE_ALT,
                hover_color=self.PRIMARY_LIGHT,
                text_color=self.TEXT,
                font=("Arial", 14, "bold"),
                command=lambda m=module, n=name:
                    self.select_difficulty_on_home(m, n)
            )

            button.pack(fill="x")

            self.create_label(
                option,
                description,
                size=11,
                color=self.SUBTEXT
            ).pack(pady=(6, 0))

            self.difficulty_buttons[name] = button

        self.update_home_difficulty_buttons()

        self.selected_label = self.create_label(
            inner,
            f"選択中：{self.difficulty_name}",
            size=13,
            weight="bold",
            color=self.PRIMARY
        )

        self.selected_label.pack(
            anchor="w",
            pady=(18, 0)
        )

        # Start button

        ctk.CTkButton(
            container,
            text="ゲームを開始する  →",
            height=55,
            width=260,
            corner_radius=12,
            fg_color=self.PRIMARY,
            hover_color=self.PRIMARY_HOVER,
            font=("Arial", 16, "bold"),
            command=self.start_game_from_home
        ).pack(pady=25)

        self.create_label(
            container,
            "ルーレットで先手・後手を決定します",
            size=11,
            weight="bold",
            color=self.SUBTEXT
        ).pack(pady=5)

    def select_difficulty_on_home(self, ai_module, name):

        self.ai = ai_module
        self.difficulty_name = name

        self.update_home_difficulty_buttons()

    def update_home_difficulty_buttons(self):

        for name, button in self.difficulty_buttons.items():

            selected = name == self.difficulty_name

            button.configure(
                fg_color=(
                    self.PRIMARY_LIGHT
                    if selected else self.SURFACE_ALT
                ),
                border_color=(
                    self.PRIMARY
                    if selected else self.BORDER
                ),
                border_width=2 if selected else 1,
                text_color=(
                    self.PRIMARY_HOVER
                    if selected else self.TEXT
                )
            )

        selected_label = getattr(self, "selected_label", None)
        if selected_label is not None and selected_label.winfo_exists():

            selected_label.configure(
                text=f"選択中：{self.difficulty_name}"
            )

    def start_game_from_home(self):

        self.clear_frames()
        self.setup_game_screen()

        self.is_game_started = True

        self.restart_game()

    # ======================================
    # Game Screen
    # ======================================

    def setup_game_screen(self):

        self.game_frame = ctk.CTkFrame(
            self.root,
            fg_color=self.BG,
            corner_radius=0
        )

        self.game_frame.pack(
            fill="both",
            expand=True
        )

        # Top bar

        header = ctk.CTkFrame(
            self.game_frame,
            fg_color=self.SURFACE,
            height=70,
            corner_radius=0
        )

        header.pack(fill="x")
        header.pack_propagate(False)

        self.create_label(
            header,
            "OTHELLO",
            size=18,
            weight="bold",
            color=self.PRIMARY
        ).pack(
            side="left",
            padx=(25, 18)
        )

        self.create_label(
            header,
            f"難易度：{self.difficulty_name}",
            size=13,
            color=self.SUBTEXT
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="もう一度遊ぶ",
            width=135,
            height=38,
            corner_radius=10,
            fg_color=self.PRIMARY,
            hover_color=self.PRIMARY_HOVER,
            font=("Arial", 12, "bold"),
            command=self.restart_game
        ).pack(side="right", padx=(5, 15))

        ctk.CTkButton(
            header,
            text="ホームに戻る",
            width=135,
            height=38,
            corner_radius=10,
            fg_color=self.SURFACE,
            hover_color=self.PRIMARY_LIGHT,
            text_color=self.TEXT,
            border_width=1,
            border_color=self.BORDER,
            font=("Arial", 12, "bold"),
            command=self.show_home_screen
        ).pack(side="right", padx=5)

        # Main board area
        # Canvas occupies the entire central area.
        # The board itself is centered inside the Canvas.

        self.canvas = tk.Canvas(
            self.game_frame,
            bg=self.BG,
            highlightthickness=0,
            bd=0
        )

        self.canvas.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

        self.canvas.bind(
            "<Button-1>",
            self.click
        )

        self.canvas.bind(
            "<Configure>",
            self.on_resize
        )

        # Bottom information panel

        footer = ctk.CTkFrame(
            self.game_frame,
            fg_color=self.SURFACE,
            height=115,
            corner_radius=0
        )

        footer.pack(fill="x")
        footer.pack_propagate(False)

        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=2)
        footer.grid_columnconfigure(2, weight=1)

        # Black score

        black_box = ctk.CTkFrame(
            footer,
            fg_color="transparent"
        )

        black_box.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=20,
            pady=10
        )

        self.black_role_label = self.create_label(
            black_box,
            "●  BLACK",
            size=12,
            weight="bold",
            color=self.SUBTEXT
        )
        self.black_role_label.pack()

        self.black_score = self.create_label(
            black_box,
            "2",
            size=28,
            weight="bold"
        )

        self.black_score.pack()

        # Turn information

        turn_box = ctk.CTkFrame(
            footer,
            fg_color="transparent"
        )

        turn_box.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=10,
            pady=10
        )

        self.turn_label = self.create_label(
            turn_box,
            "● あなたの番",
            size=17,
            weight="bold",
            color=self.PRIMARY
        )

        self.turn_label.pack(pady=(8, 2))

        self.status_label = self.create_label(
            turn_box,
            "置ける場所を選択してください。",
            size=12,
            color=self.SUBTEXT
        )

        self.status_label.pack()

        # White score

        white_box = ctk.CTkFrame(
            footer,
            fg_color="transparent"
        )

        white_box.grid(
            row=0,
            column=2,
            sticky="nsew",
            padx=20,
            pady=10
        )

        self.white_role_label = self.create_label(
            white_box,
            "○  WHITE",
            size=12,
            weight="bold",
            color=self.SUBTEXT
        )
        self.white_role_label.pack()

        self.white_score = self.create_label(
            white_box,
            "2",
            size=28,
            weight="bold"
        )

        self.white_score.pack()

    # ======================================
    # Board Drawing
    # ======================================

    def on_resize(self, event):

        if not self.canvas:
            return

        size = self.ai.BOARD_SIZE

        available = min(
            event.width,
            event.height
        )

        self.cell_size = max(
            available // size,
            10
        )

        board_size = self.cell_size * size

        # Center the board horizontally and vertically.

        self.offset_x = (
            event.width - board_size
        ) // 2

        self.offset_y = (
            event.height - board_size
        ) // 2

        self.draw_board()

    def draw_board(self):

        if self.canvas is None or self.board is None:
            return

        self.canvas.delete("all")

        size = self.ai.BOARD_SIZE
        total = self.cell_size * size

        x0 = self.offset_x
        y0 = self.offset_y

        # Board background

        self.canvas.create_rectangle(
            x0,
            y0,
            x0 + total,
            y0 + total,
            fill=self.BOARD,
            outline="#206F50",
            width=2
        )

        # Legal moves

        legal_moves = []

        if not self.game_over and not self.is_waiting:

            legal_moves = self.ai.get_legal_moves(
                self.board,
                self.current_player
            )

        # Draw cells and pieces

        for row in range(size):

            for col in range(size):

                x1 = x0 + col * self.cell_size
                y1 = y0 + row * self.cell_size

                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    outline=self.BOARD_LINE,
                    width=1
                )

                padding = max(
                    self.cell_size // 12,
                    3
                )

                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2

                piece = self.board[row, col]

                if piece == self.ai.BLACK:

                    self.draw_piece(
                        cx,
                        cy,
                        padding,
                        self.BLACK
                    )

                elif piece == self.ai.WHITE:

                    self.draw_piece(
                        cx,
                        cy,
                        padding,
                        self.WHITE
                    )

                elif (
                    (row, col) in legal_moves
                    and self.current_player == self.human_color
                ):

                    radius = max(
                        self.cell_size // 10,
                        4
                    )

                    self.canvas.create_oval(
                        cx - radius,
                        cy - radius,
                        cx + radius,
                        cy + radius,
                        fill=self.LEGAL,
                        outline=""
                    )

        # Update score

        black, white = self.ai.count_pieces(
            self.board
        )

        self.black_score.configure(text=str(black))
        self.white_score.configure(text=str(white))

        # Update turn

        if self.game_over:

            turn = "■ ゲーム終了"
            color = self.SUBTEXT

        elif self.is_waiting:

            if self.current_player == self.ai_color:
                turn = "◉ AI 思考中..."
            else:
                turn = "◉ 処理中..."

            color = self.PRIMARY

        elif self.current_player == self.human_color:

            turn = "● あなたの番"
            color = self.PRIMARY

        else:

            turn = "○ AI の番"
            color = self.SUBTEXT

        self.turn_label.configure(
            text=turn,
            text_color=color
        )

        self.root.title(
            f"Reversi | {black} : {white}"
        )

        # Re-render overlays after redraw or resize.

        if self.game_over:
            self.render_result_overlay()
        elif self.roulette_data:
            self.render_roulette_overlay()
        elif self.pass_overlay_data:
            self.render_pass_overlay()

    def draw_piece(self, cx, cy, padding, color):

        x1 = cx - self.cell_size / 2 + padding
        y1 = cy - self.cell_size / 2 + padding

        x2 = cx + self.cell_size / 2 - padding
        y2 = cy + self.cell_size / 2 - padding

        # Shadow

        self.canvas.create_oval(
            x1 + 2,
            y1 + 3,
            x2 + 2,
            y2 + 3,
            fill="#15523B",
            outline=""
        )

        outline = (
            "#D1D5DB"
            if color == self.WHITE
            else "#101820"
        )

        self.canvas.create_oval(
            x1,
            y1,
            x2,
            y2,
            fill=color,
            outline=outline,
            width=1
        )

    # ======================================
    # PASS Overlay
    # ======================================

    def show_pass_overlay(self, player):

        if not self.canvas:
            return

        self.hide_pass_overlay()

        if player == self.human_color:

            subtitle = "あなたの番はスキップされました"
            color = self.OVERLAY_ACCENT

        else:

            subtitle = "AIの番はスキップされました"
            color = self.OVERLAY_SUBTEXT

        self.pass_overlay_data = {
            "title": "PASS",
            "subtitle": subtitle,
            "color": color
        }

        self.render_pass_overlay()

        self.pass_after_id = self.root.after(
            1500,
            self.hide_pass_overlay
        )

    def render_pass_overlay(self):

        if not self.canvas or not self.pass_overlay_data:
            return

        self.canvas.delete("pass_overlay")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        cx = width // 2
        cy = height // 2

        data = self.pass_overlay_data
        color = data["color"]

        # Overlay background

        box_width = 340
        box_height = 180

        x1 = cx - box_width // 2
        y1 = cy - box_height // 2
        x2 = cx + box_width // 2
        y2 = cy + box_height // 2

        # Shadow

        self.canvas.create_rectangle(
            x1 + 5,
            y1 + 6,
            x2 + 5,
            y2 + 6,
            fill=self.OVERLAY_SHADOW,
            outline="",
            tags="pass_overlay"
        )

        # Main card

        self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=self.OVERLAY_BG,
            stipple="gray75",
            outline=color,
            width=3,
            tags="pass_overlay"
        )

        # PASS icon

        self.canvas.create_text(
            cx,
            cy - 48,
            text="⏭",
            font=("Arial", 30),
            fill=color,
            tags="pass_overlay"
        )

        # PASS title

        self.canvas.create_text(
            cx,
            cy - 5,
            text=data["title"],
            font=("Arial", 32, "bold"),
            fill=color,
            tags="pass_overlay"
        )

        # Description

        self.canvas.create_text(
            cx,
            cy + 48,
            text=data["subtitle"],
            font=("Arial", 13, "bold"),
            fill=self.OVERLAY_SUBTEXT,
            tags="pass_overlay"
        )

        self.canvas.tag_raise("pass_overlay")

    def hide_pass_overlay(self):

        if self.pass_after_id is not None:

            try:
                self.root.after_cancel(
                    self.pass_after_id
                )
            except tk.TclError:
                pass

            self.pass_after_id = None

        if self.canvas:
            self.canvas.delete("pass_overlay")

        self.pass_overlay_data = None

    # ======================================
    # Messages
    # ======================================

    def show_message(self, text):

        if not self.status_label.winfo_exists():
            return

        if self.message_after_id is not None:

            self.root.after_cancel(
                self.message_after_id
            )

        self.status_label.configure(
            text=text,
            text_color=self.PRIMARY
        )

        self.message_after_id = self.root.after(
            1800,
            self.clear_message
        )

    def clear_message(self):

        self.message_after_id = None

        if self.status_label.winfo_exists():

            self.status_label.configure(
                text="置ける場所を選択してください。",
                text_color=self.SUBTEXT
            )

    # ======================================
    # Game Management
    # ======================================

    def update_color_role_labels(self):

        if not hasattr(self, "black_role_label"):
            return

        black_role = "あなた" if self.human_color == self.ai.BLACK else "AI"
        white_role = "あなた" if self.human_color == self.ai.WHITE else "AI"
        self.black_role_label.configure(
            text=f"●  BLACK（{black_role}）"
        )
        self.white_role_label.configure(
            text=f"○  WHITE（{white_role}）"
        )

    def restart_game(self):

        self.game_token += 1

        self.cancel_scheduled_tasks()
        self.clear_ai_queue()

        self.board = self.ai.init_board()
        self.current_player = self.ai.BLACK

        self.game_over = False
        self.is_waiting = True
        self.ai_turn_active = False

        self.hide_result_overlay()
        self.roulette_ticks = 0
        self.roulette_start_angle = random.uniform(0, 360)
        self.roulette_target_angle = (
            self.roulette_start_angle
            + 360 * self.ROULETTE_REVOLUTIONS
            + random.uniform(0, 360)
        )
        self.roulette_data = {
            "angle": self.roulette_start_angle,
            "text": "回転中…"
        }

        self.status_label.configure(
            text="先手・後手をルーレットで決定します。",
            text_color=self.SUBTEXT
        )

        self.draw_board()
        self.roulette_after_id = self.root.after(
            self.ROULETTE_FRAME_MS,
            self.advance_turn_roulette
        )

    def advance_turn_roulette(self):

        self.roulette_after_id = None
        if self.roulette_data is None or self.game_frame is None:
            return

        self.roulette_ticks += 1
        progress = min(
            self.roulette_ticks / self.ROULETTE_FRAMES,
            1.0
        )
        eased_progress = 1 - (1 - progress) ** 3
        angle = self.roulette_start_angle + (
            self.roulette_target_angle - self.roulette_start_angle
        ) * eased_progress

        if progress < 1.0:
            self.roulette_data = {"angle": angle, "text": "回転中…"}
            self.render_roulette_overlay()
            self.roulette_after_id = self.root.after(
                self.ROULETTE_FRAME_MS,
                self.advance_turn_roulette
            )
            return

        final_angle = self.roulette_target_angle % 360
        pointer_angle = 90
        human_has_black = (pointer_angle - final_angle) % 360 < 180
        self.human_color = (
            self.ai.BLACK if human_has_black else self.ai.WHITE
        )
        self.ai_color = (
            self.ai.WHITE
            if self.human_color == self.ai.BLACK
            else self.ai.BLACK
        )
        self.update_color_role_labels()

        result = "黒（先手）" if human_has_black else "白（後手）"
        self.roulette_data = {
            "angle": self.roulette_target_angle,
            "text": result
        }
        self.render_roulette_overlay()
        self.roulette_after_id = self.root.after(
            700,
            self.finish_turn_roulette
        )

    def render_roulette_overlay(self):

        if self.canvas is None or self.roulette_data is None:
            return

        self.canvas.delete("roulette_overlay")
        cx = self.canvas.winfo_width() // 2
        cy = self.canvas.winfo_height() // 2
        radius = 130
        angle = self.roulette_data["angle"] % 360
        x1 = cx - radius
        y1 = cy - radius
        x2 = cx + radius
        y2 = cy + radius

        self.canvas.create_text(
            cx,
            cy - radius - 44,
            text="先手・後手ルーレット",
            font=("Arial", 18, "bold"),
            fill=self.OVERLAY_TEXT,
            tags="roulette_overlay"
        )

        # A raised rim and two colored half-circle sectors form the wheel.
        self.canvas.create_oval(
            x1 - 8, y1 - 8, x2 + 8, y2 + 8,
            fill=self.OVERLAY_SHADOW,
            outline="#6B7280",
            width=2,
            tags="roulette_overlay"
        )
        self.canvas.create_arc(
            x1, y1, x2, y2,
            start=angle,
            extent=180,
            style=tk.PIESLICE,
            fill=self.OVERLAY_ACCENT,
            outline=self.OVERLAY_TEXT,
            width=3,
            tags="roulette_overlay"
        )
        self.canvas.create_arc(
            x1, y1, x2, y2,
            start=angle + 180,
            extent=180,
            style=tk.PIESLICE,
            fill=self.OVERLAY_BG,
            outline=self.OVERLAY_TEXT,
            width=3,
            tags="roulette_overlay"
        )

        for label, label_angle, color in (
            ("黒（先手）", angle + 90, "#000000"),
            ("白（後手）", angle + 270, "#000000"),
        ):
            radians = math.radians(label_angle)
            label_x = cx + radius * 0.55 * math.cos(radians)
            label_y = cy - radius * 0.55 * math.sin(radians)
            self.canvas.create_text(
                label_x,
                label_y,
                text=label,
                font=("Arial", 12, "bold"),
                fill=color,
                angle=angle,
                tags="roulette_overlay"
            )

        # The pointer stays fixed while the wheel spins beneath it.
        self.canvas.create_polygon(
            cx, cy - radius + 8,
            cx - 14, cy - radius - 20,
            cx + 14, cy - radius - 20,
            fill=self.OVERLAY_ACCENT,
            outline=self.OVERLAY_TEXT,
            width=2,
            tags="roulette_overlay"
        )
        self.canvas.create_oval(
            cx - 18, cy - 18, cx + 18, cy + 18,
            fill=self.OVERLAY_SHADOW,
            outline=self.OVERLAY_TEXT,
            width=3,
            tags="roulette_overlay"
        )
        self.canvas.create_text(
            cx,
            cy + radius + 40,
            text=self.roulette_data["text"],
            font=("Arial", 18, "bold"),
            fill="#000000",
            tags="roulette_overlay"
        )
        self.canvas.tag_raise("roulette_overlay")

    def finish_turn_roulette(self):

        self.roulette_after_id = None
        if self.roulette_data is None or self.game_frame is None:
            return

        self.roulette_data = None
        self.is_waiting = False
        self.status_label.configure(
            text="置ける場所を選択してください。",
            text_color=self.SUBTEXT
        )
        self.draw_board()
        self.check_turn_and_run()

    # ======================================
    # Player Input
    # ======================================

    def click(self, event):

        if (
            self.current_player != self.human_color
            or self.game_over
            or self.is_waiting
            or self.board is None
        ):
            return

        click_x = event.x - self.offset_x
        click_y = event.y - self.offset_y

        row = click_y // self.cell_size
        col = click_x // self.cell_size

        if not (
            0 <= row < self.ai.BOARD_SIZE
            and 0 <= col < self.ai.BOARD_SIZE
        ):
            return

        legal_moves = self.ai.get_legal_moves(
            self.board,
            self.human_color
        )

        if (row, col) not in legal_moves:
            return

        result = self.ai.make_move(
            self.board,
            row,
            col,
            self.human_color
        )

        if result is not None and not isinstance(result, bool):
            self.board = result

        self.current_player = self.ai_color
        self.is_waiting = True

        self.draw_board()

        self.ai_after_id = self.root.after(
            200,
            self.check_turn_and_run
        )

    # ======================================
    # AI
    # ======================================

    def ai_move(self):

        if (
            self.game_over
            or self.board is None
            or self.current_player != self.ai_color
            or not self.ai_turn_active
        ):
            return

        self.is_waiting = True

        token = self.game_token

        board_snapshot = self.board.copy()

        def worker():

            try:

                move = self.ai.select_ai_move(
                    board_snapshot,
                    self.ai_color
                )

                self.ai_queue.put(
                    (token, "success", move)
                )

            except Exception as error:

                self.ai_queue.put(
                    (token, "error", str(error))
                )

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

        self.root.after(
            50,
            self.poll_ai_result,
            token
        )

    def poll_ai_result(self, token):

        if token != self.game_token or self.game_over:
            return

        try:

            result_token, result_type, result = (
                self.ai_queue.get_nowait()
            )

        except queue.Empty:

            self.root.after(
                50,
                self.poll_ai_result,
                token
            )
            return

        if result_token != token:
            self.root.after(
                50,
                self.poll_ai_result,
                token
            )
            return

        if result_type == "error":

            self.ai_turn_active = False
            self.is_waiting = False

            self.show_message(
                f"AIエラー: {result}"
            )

            self.draw_board()
            return

        self.apply_ai_move(result)

    def apply_ai_move(self, move):

        if (
            self.game_over
            or self.current_player != self.ai_color
            or not self.ai_turn_active
        ):
            return

        self.ai_turn_active = False

        if move is not None:

            row, col = move

            result = self.ai.make_move(
                self.board,
                row,
                col,
                self.ai_color
            )

            if result is not None and not isinstance(result, bool):
                self.board = result

        self.current_player = self.human_color
        self.is_waiting = False

        self.draw_board()

        self.ai_after_id = self.root.after(
            200,
            self.check_turn_and_run
        )

    # ======================================
    # Pass / Turn Management
    # ======================================

    def resume_after_pass(self, next_player):

        if self.game_over:
            return

        self.is_waiting = False
        self.current_player = next_player

        self.draw_board()

        self.check_turn_and_run()

    def check_turn_and_run(self):

        if self.board is None or self.game_over:
            return

        human_moves = self.ai.get_legal_moves(
            self.board,
            self.human_color
        )

        ai_moves = self.ai.get_legal_moves(
            self.board,
            self.ai_color
        )

        # Game over

        if not human_moves and not ai_moves:

            self.game_over = True
            self.is_waiting = False
            self.ai_turn_active = False

            self.draw_board()
            self.show_end_message()

            return

        # AI turn

        if self.current_player == self.ai_color:

            if ai_moves:

                if self.ai_turn_active:
                    return

                self.ai_turn_active = True
                self.is_waiting = True
                self.draw_board()

                self.ai_after_id = self.root.after(
                    400,
                    self.ai_move
                )

            else:

                self.is_waiting = True
                self.draw_board()

                self.show_pass_overlay(
                    self.ai_color
                )

                self.ai_after_id = self.root.after(
                    1500,
                    lambda: self.resume_after_pass(
                        self.human_color
                    )
                )

        # Human turn

        elif self.current_player == self.human_color:

            if not human_moves:

                self.is_waiting = True
                self.draw_board()

                self.show_pass_overlay(
                    self.human_color
                )

                self.ai_after_id = self.root.after(
                    1500,
                    lambda: self.resume_after_pass(
                        self.ai_color
                    )
                )

            else:

                self.is_waiting = False
                self.draw_board()

    # ======================================
    # Game Result
    # ======================================

    def show_end_message(self):

        if self.board is None or not self.canvas:
            return

        black, white = self.ai.count_pieces(self.board)

        human_count = black if self.human_color == self.ai.BLACK else white
        ai_count = white if self.ai_color == self.ai.WHITE else black
        human_stone = "黒" if self.human_color == self.ai.BLACK else "白"
        ai_stone = "白" if self.ai_color == self.ai.WHITE else "黒"

        player_won = human_count > ai_count
        if player_won:
            result = "YOU WIN!"
            detail = f"プレイヤー（{human_stone}）の勝利です。"
        elif ai_count > human_count:
            result = "AI WINS!"
            detail = f"AI（{ai_stone}）の勝利です。"
        else:
            result = "DRAW!"
            detail = "引き分けです。"

        self.turn_label.configure(
            text="■ ゲーム終了",
            text_color=self.PRIMARY
        )
        self.status_label.configure(
            text="対戦結果が確定しました。",
            text_color=self.SUBTEXT
        )

        self.hide_result_overlay()
        self.result_overlay_data = {
            "result": result,
            "detail": detail,
            "score": f"{black} : {white}"
        }

        # Draw the panel and accent border in one Canvas shape so both
        # follow the same rounded outline.
        home_button = ctk.CTkButton(
            self.game_frame,
            text="ホームに戻る",
            width=140,
            height=40,
            corner_radius=10,
            bg_color=self.OVERLAY_BG,
            fg_color=self.OVERLAY_BG,
            hover_color="#BDBDBD",
            text_color=self.OVERLAY_TEXT,
            border_width=1,
            border_color="#9E9E9E",
            command=self.show_home_screen
        )

        replay_button = ctk.CTkButton(
            self.game_frame,
            text="もう一度遊ぶ",
            width=140,
            height=40,
            corner_radius=10,
            bg_color=self.OVERLAY_BG,
            fg_color=self.OVERLAY_ACCENT,
            hover_color=self.OVERLAY_ACCENT_HOVER,
            command=self.restart_game
        )

        self.result_overlay = [home_button, replay_button]
        self.render_result_overlay()

        if player_won:
            self.start_confetti()

    def start_confetti(self):

        if (
            self.canvas is None
            or not self.game_over
            or self.confetti_particles
        ):
            return

        width = max(self.canvas.winfo_width(), 1)
        colors = [
            "#C2410C", "#FFD166", "#06D6A0",
            "#118AB2", "#EF476F", "#F8F9FA"
        ]

        for _ in range(70):
            self.confetti_particles.append({
                "x": random.randint(0, width),
                "y": random.randint(-50, 0),
                "vx": random.uniform(-2, 2),
                "vy": random.uniform(1, 4),
                "color": random.choice(colors),
                "size": random.randint(4, 8)
            })

        self.animate_confetti()

    def animate_confetti(self):

        self.confetti_after_id = None
        if self.canvas is None or not self.game_over:
            self.confetti_particles = []
            return

        self.canvas.delete("confetti")
        height = self.canvas.winfo_height()
        remaining_particles = []

        for particle in self.confetti_particles:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["vy"] += 0.05

            if particle["y"] < height:
                size = particle["size"]
                self.canvas.create_rectangle(
                    particle["x"],
                    particle["y"],
                    particle["x"] + size,
                    particle["y"] + size,
                    fill=particle["color"],
                    outline="",
                    tags="confetti"
                )
                remaining_particles.append(particle)

        self.confetti_particles = remaining_particles

        if self.confetti_particles:
            self.canvas.tag_lower("confetti", "result_overlay")
            self.confetti_after_id = self.root.after(
                30,
                self.animate_confetti
            )

    def render_result_overlay(self):

        if (
            not self.result_overlay
            or self.canvas is None
            or self.result_overlay_data is None
        ):
            return

        if not all(button.winfo_exists() for button in self.result_overlay):
            return

        self.canvas.delete("result_overlay")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        cx = width / 2
        cy = height / 2
        box_width = 440
        box_height = 210
        radius = 22
        left = cx - box_width / 2
        right = cx + box_width / 2
        top = cy - box_height / 2
        bottom = cy + box_height / 2

        points = []
        corners = (
            (right - radius, top + radius, -90, 0),
            (right - radius, bottom - radius, 0, 90),
            (left + radius, bottom - radius, 90, 180),
            (left + radius, top + radius, 180, 270),
        )
        for corner_x, corner_y, start_angle, end_angle in corners:
            for step in range(13):
                angle = start_angle + (end_angle - start_angle) * step / 12
                radians = math.radians(angle)
                points.extend((
                    corner_x + radius * math.cos(radians),
                    corner_y + radius * math.sin(radians)
                ))

        self.canvas.create_polygon(
            *points,
            fill=self.OVERLAY_BG,
            stipple="gray75",
            outline=self.OVERLAY_ACCENT,
            width=3,
            tags="result_overlay"
        )
        self.canvas.create_text(
            cx,
            cy - 45,
            text=self.result_overlay_data["result"],
            font=("Arial", 30, "bold"),
            fill=self.OVERLAY_ACCENT,
            tags="result_overlay"
        )
        self.canvas.create_text(
            cx,
            cy - 4,
            text=(
                f"{self.result_overlay_data['detail']}  "
                f"{self.result_overlay_data['score']}"
            ),
            font=("Arial", 14, "bold"),
            fill=self.OVERLAY_TEXT,
            tags="result_overlay"
        )

        center_x = self.canvas.winfo_x() + cx
        button_y = self.canvas.winfo_y() + cy + 58
        self.result_overlay[0].place(
            x=center_x - 76,
            y=button_y,
            anchor="center"
        )
        self.result_overlay[1].place(
            x=center_x + 76,
            y=button_y,
            anchor="center"
        )
        for button in self.result_overlay:
            button.lift()

    def hide_result_overlay(self):

        if self.canvas is not None:
            self.canvas.delete("result_overlay")

        if self.result_overlay is not None:
            for widget in self.result_overlay:
                try:
                    if widget.winfo_exists():
                        widget.destroy()
                except tk.TclError:
                    pass
            self.result_overlay = None

        self.result_overlay_data = None


# ==========================================
# Main
# ==========================================

if __name__ == "__main__":

    root = ctk.CTk()

    app = OthelloGUI(root)

    root.mainloop()
