import os
import sys
import tkinter as tk
from tkinter import messagebox
import threading
import webbrowser

# Configure standard Windows/macOS VLC path support
if sys.platform.startswith("win"):
    vlc_path = r"C:\Program Files\VideoLAN\VLC"
    if os.path.exists(vlc_path):
        os.environ["PYTHON_VLC_MODULE_PATH"] = vlc_path
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(vlc_path)
elif sys.platform == "darwin":
    vlc_path = "/Applications/VLC.app/Contents/MacOS/lib"
    if os.path.exists(vlc_path):
        os.environ["PYTHON_VLC_MODULE_PATH"] = vlc_path

import vlc
from backend.DiaryEntry import (
    fetch_song_title,
    save_entry,
    load_entries,
    delete_entry,
    get_audio_stream_url,
)


# ==========================================
# COLOR PALETTE & DESIGN CONSTANTS
# ==========================================
BG = "#E7E7E7"
WHITE = "#FFFFFF"
HEADER = "#777777"
HEADER_DARK = "#5F5F5F"
SEARCH_BG = "#E9E6E6"
CARD_TOP = "#EFEBEB"
CARD_BOTTOM = "#D9D7D7"
TEXT = "#111111"
MUTED = "#888888"
SHADOW = "#BDBBBB"


def rounded_rectangle(canvas, x1, y1, x2, y2, radius=16, **kwargs):
    """Draw a smooth rounded rectangle on a Tkinter Canvas."""
    radius = max(1, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points = [
        x1 + radius, y1, x2 - radius, y1,
        x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2,
        x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius,
        x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(
        points, smooth=True, splinesteps=24, **kwargs
    )


class MusicDiaryApp:
    def __init__(self, root, username="GUEST"):
        self.root = root
        self.current_user = username
        self.root.configure(bg=BG)

        # VLC Player Initialization
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()
        self.current_playing_title = None

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.refresh_feed)

        self.create_layout()
        self.refresh_feed()

    # ==========================================
    # 1. MAIN LAYOUT CONSTRUCTION
    # ==========================================
    def create_layout(self):
        self._create_profile_bar()
        self._create_content_wrapper()

    def _create_profile_bar(self):
        profile_bar = tk.Frame(self.root, bg=HEADER, height=58)
        profile_bar.pack(side=tk.TOP, fill=tk.X)
        profile_bar.pack_propagate(False)

        avatar = tk.Canvas(
            profile_bar, width=34, height=34, bg=HEADER, highlightthickness=0
        )
        avatar.pack(side=tk.LEFT, padx=(18, 12), pady=12)
        avatar.create_oval(2, 2, 32, 32, fill=WHITE, outline=WHITE)

        tk.Label(
            profile_bar,
            text=self.current_user,
            bg=HEADER,
            fg=WHITE,
            font=("Segoe UI", 11),
        ).pack(side=tk.LEFT)

        tk.Button(
            profile_bar,
            text="Log Out",
            command=self.logout_user,
            bg=HEADER_DARK,
            fg=WHITE,
            activebackground="#4A4A4A",
            activeforeground=WHITE,
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=5,
            cursor="hand2",
            font=("Segoe UI", 9),
        ).pack(side=tk.RIGHT, padx=18)

    def _create_content_wrapper(self):
        content_wrapper = tk.Frame(self.root, bg=WHITE)
        content_wrapper.pack(fill=tk.BOTH, expand=True)

        self._create_bottom_navigation(content_wrapper)
        self._create_main_workspace(content_wrapper)

    def _create_bottom_navigation(self, parent):
        bottom_nav = tk.Frame(parent, bg=WHITE, height=66)
        bottom_nav.pack(side=tk.BOTTOM, fill=tk.X)
        bottom_nav.pack_propagate(False)

        nav_inner = tk.Frame(bottom_nav, bg=WHITE)
        nav_inner.pack(expand=True)

        # Album Tab
        album_col = tk.Frame(nav_inner, bg=WHITE)
        album_col.pack(side=tk.LEFT, padx=34)
        album_circle = tk.Canvas(
            album_col, width=28, height=28, bg=WHITE, highlightthickness=0
        )
        album_circle.pack()
        album_circle.create_oval(2, 2, 26, 26, fill="#C7C7C7", outline="")
        tk.Label(
            album_col, text="Album", bg=WHITE, fg=TEXT, font=("Segoe UI", 8)
        ).pack(pady=(1, 0))

        # Add Tab (+)
        add_col = tk.Frame(nav_inner, bg=WHITE)
        add_col.pack(side=tk.LEFT, padx=34)

        add_circle = tk.Canvas(
            add_col, width=28, height=28, bg=WHITE, highlightthickness=0, cursor="hand2"
        )
        add_circle.pack()
        add_circle.create_oval(2, 2, 26, 26, fill="#929090", outline="")
        add_circle.create_text(
            14, 14, text="+", fill=WHITE, font=("Segoe UI", 12, "bold")
        )
        add_circle.bind("<Button-1>", lambda event: self.open_add_dialog())
        
        lbl_add = tk.Label(
            add_col, text="Add", bg=WHITE, fg=TEXT, font=("Segoe UI", 8, "bold"), cursor="hand2"
        )
        lbl_add.pack(pady=(1, 0))
        lbl_add.bind("<Button-1>", lambda event: self.open_add_dialog())
        add_col.bind("<Button-1>", lambda event: self.open_add_dialog())

    def _create_main_workspace(self, parent):
        main_area = tk.Frame(parent, bg=WHITE)
        main_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=18, pady=(8, 5))

        tk.Label(
            main_area, text="Music Diary", bg=WHITE, fg=TEXT, font=("Segoe UI", 15, "bold")
        ).pack(anchor="w", pady=(0, 10))

        # Rounded Search Field
        search_shell = tk.Frame(main_area, bg=WHITE, height=40)
        search_shell.pack(fill=tk.X, pady=(0, 12))
        search_shell.pack_propagate(False)
        
        self.search_canvas = tk.Canvas(
            search_shell, bg=WHITE, height=40, highlightthickness=0, bd=0
        )
        self.search_canvas.pack(fill=tk.BOTH, expand=True)

        def draw_search(event=None):
            self.search_canvas.delete("search-shape")
            width = max(self.search_canvas.winfo_width(), 100)
            rounded_rectangle(
                self.search_canvas, 1, 1, width - 2, 38, radius=7,
                fill=SEARCH_BG, outline=SEARCH_BG, tags="search-shape"
            )
            self.search_canvas.coords(self.search_window, 13, 20)
            self.search_canvas.itemconfigure(
                self.search_window, width=max(50, width - 28)
            )

        self.search_entry = tk.Entry(
            self.search_canvas,
            textvariable=self.search_var,
            bg=SEARCH_BG,
            fg=MUTED,
            insertbackground=TEXT,
            font=("Segoe UI", 9),
            bd=0,
            relief=tk.FLAT,
        )
        self.search_entry.insert(0, "Search")
        self.search_window = self.search_canvas.create_window(
            13, 20, window=self.search_entry, anchor="w", height=24
        )
        self.search_canvas.bind("<Configure>", draw_search)
        self.search_entry.bind("<FocusIn>", self.clear_placeholder)
        self.search_entry.bind("<FocusOut>", self.restore_placeholder)

        tk.Label(
            main_area, text="Your Diary", bg=WHITE, fg=TEXT, font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 8))

        # Scrollable Card Area Container
        container = tk.Frame(main_area, bg=WHITE)
        container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(container, bg=WHITE, highlightthickness=0, bd=0)
        self.scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        
        self.grid_frame = tk.Frame(self.canvas, bg=WHITE)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.grid_frame.bind(
            "<Configure>",
            lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfigure(self.canvas_window, width=event.width),
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    # ==========================================
    # 2. EVENT HANDLERS & DIALOGS
    # ==========================================
    def _on_mousewheel(self, event):
        if self.canvas.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def clear_placeholder(self, event=None):
        if self.search_entry.get() == "Search":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg=TEXT)

    def restore_placeholder(self, event=None):
        if not self.search_entry.get().strip():
            self.search_entry.insert(0, "Search")
            self.search_entry.config(fg=MUTED)

    def logout_user(self):
        self.player.stop()
        for widget in self.root.winfo_children():
            widget.destroy()

        from utils.center_window import center_window
        from frontend.auth import AuthWindow

        center_window(self.root, 400, 450)

        def open_app(username):
            for widget in self.root.winfo_children():
                widget.destroy()
            center_window(self.root, 1000, 700)
            MusicDiaryApp(self.root, username)

        AuthWindow(self.root, open_app)

    def open_add_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Diary Entry")
        dialog.geometry("420x340")
        dialog.configure(bg=WHITE)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(
            dialog, text="Add to Your Diary", bg=WHITE, fg=TEXT, font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", padx=22, pady=(18, 12))

        tk.Label(
            dialog, text="Paste YouTube Link:", bg=WHITE, fg=TEXT, font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=22, pady=(0, 5))

        url_entry = tk.Entry(
            dialog, bg="#F3F1F1", fg=TEXT, insertbackground=TEXT, font=("Segoe UI", 10), bd=0, relief=tk.FLAT
        )
        url_entry.pack(fill=tk.X, padx=22, ipady=8)

        tk.Label(
            dialog, text="Journal Description:", bg=WHITE, fg=TEXT, font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=22, pady=(14, 5))

        desc_entry = tk.Text(
            dialog, bg="#F3F1F1", fg=TEXT, insertbackground=TEXT, font=("Segoe UI", 10), height=4, bd=0, relief=tk.FLAT, wrap=tk.WORD
        )
        desc_entry.pack(fill=tk.X, padx=22)

        status_lbl = tk.Label(
            dialog, text="", bg=WHITE, fg=MUTED, font=("Segoe UI", 9)
        )
        status_lbl.pack(pady=(6, 0))

        def submit():
            url = url_entry.get().strip()
            desc = desc_entry.get("1.0", tk.END).strip()
            if not url:
                messagebox.showerror("Error", "Please enter a YouTube link!", parent=dialog)
                return

            status_lbl.config(text="Converting link to title...")

            def background_task():
                try:
                    title = fetch_song_title(url)
                    save_entry(self.current_user, title, url, desc)
                    self.root.after(0, lambda: self._finish_save(dialog))
                except Exception as error:
                    self.root.after(
                        0, lambda: messagebox.showerror("Save Error", str(error), parent=dialog)
                    )
                    self.root.after(0, lambda: status_lbl.config(text="Could not save entry."))

            threading.Thread(target=background_task, daemon=True).start()

        tk.Button(
            dialog,
            text="Convert & Save",
            command=submit,
            bg=HEADER,
            fg=WHITE,
            activebackground=HEADER_DARK,
            activeforeground=WHITE,
            relief=tk.FLAT,
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
        ).pack(pady=10)

    def _finish_save(self, dialog):
        if dialog.winfo_exists():
            dialog.destroy()
        self.refresh_feed()

    # ==========================================
    # 3. FEED & CARD RENDERING
    # ==========================================
    def refresh_feed(self, *args):
        if not hasattr(self, "grid_frame") or not self.grid_frame.winfo_exists():
            return

        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        entries = load_entries(self.current_user)
        search_query = self.search_var.get().strip().lower()
        if search_query == "search":
            search_query = ""

        filtered_entries = [
            entry for entry in entries
            if search_query in entry.get("title", "").lower()
            or search_query in entry.get("description", "").lower()
        ]

        # Render cards in a 4-column layout with tight spacing
        for index, entry in enumerate(filtered_entries):
            row, col = divmod(index, 4)
            self.create_card(
                self.grid_frame,
                entry.get("title", "Untitled"),
                entry.get("url", ""),
                entry.get("description", ""),
                entry.get("date", ""),
                row,
                col,
            )

        for col in range(4):
            self.grid_frame.grid_columnconfigure(col, weight=0, uniform="diary")

    def create_card(self, parent, title, url, description, date, row, col):
        # Original compact card width (170)
        card = tk.Canvas(
            parent, width=170, height=140, bg=WHITE, highlightthickness=0, bd=0
        )
        # Tightened horizontal padding (padx=3) so cards sit close together while keeping original size
        card.grid(row=row, column=col, padx=3, pady=4, sticky="nw")
        card.grid_propagate(False)

        # Draw card shadows and rounded geometry sections
        rounded_rectangle(card, 2, 4, 168, 137, radius=17, fill=SHADOW, outline=SHADOW)
        rounded_rectangle(card, 1, 1, 167, 133, radius=17, fill=CARD_TOP, outline=CARD_TOP)
        rounded_rectangle(card, 1, 66, 167, 133, radius=15, fill=CARD_BOTTOM, outline=CARD_BOTTOM)
        card.create_rectangle(1, 66, 167, 80, fill=CARD_BOTTOM, outline=CARD_BOTTOM)

        shown_title = title[:22] + ("..." if len(title) > 22 else "")
        lbl_title = tk.Label(
            card, text=shown_title, bg=CARD_BOTTOM, fg=TEXT, font=("Segoe UI", 8, "bold"), cursor="hand2", anchor="w"
        )
        card.create_window(10, 82, window=lbl_title, anchor="nw", width=146)
        lbl_title.bind("<Button-1>", lambda event, link=url: webbrowser.open(link))

        detail = description.strip() if description.strip() else date
        detail = detail[:24] + ("..." if len(detail) > 24 else "")
        lbl_detail = tk.Label(
            card, text=detail, bg=CARD_BOTTOM, fg="#666666", font=("Segoe UI", 7), anchor="w"
        )
        card.create_window(10, 100, window=lbl_detail, anchor="nw", width=146)

        play_btn = tk.Button(
            card,
            text="▶ Play",
            command=lambda link=url, song=title: self.start_audio_thread(link, song),
            bg="#FFFFFF",
            fg="#555555",
            activebackground="#F5F5F5",
            activeforeground=TEXT,
            bd=0,
            relief=tk.FLAT,
            padx=5,
            pady=1,
            font=("Segoe UI", 7, "bold"),
            cursor="hand2",
        )
        card.create_window(10, 118, window=play_btn, anchor="nw")

        del_btn = tk.Button(
            card,
            text="✕",
            command=lambda link=url: self.delete_diary_entry(link),
            bg=CARD_BOTTOM,
            fg="#666666",
            activebackground="#C8C6C6",
            activeforeground=TEXT,
            bd=0,
            relief=tk.FLAT,
            padx=4,
            pady=1,
            font=("Segoe UI", 8),
            cursor="hand2",
        )
        card.create_window(153, 117, window=del_btn, anchor="ne")

    def delete_diary_entry(self, url):
        if messagebox.askyesno(
            "Delete Entry",
            "Are you sure you want to delete this diary entry?",
            parent=self.root,
        ):
            delete_entry(self.current_user, url)
            self.refresh_feed()

    # ==========================================
    # 4. AUDIO PLAYBACK
    # ==========================================
    def start_audio_thread(self, url, title):
        threading.Thread(target=self.play_audio, args=(url, title), daemon=True).start()

    def play_audio(self, url, title):
        stream_url = get_audio_stream_url(url)
        if not stream_url:
            self.root.after(
                0, lambda: messagebox.showerror("Playback Error", "Could not load audio stream.")
            )
            return

        self.player.stop()
        media = self.vlc_instance.media_new(stream_url)
        self.player.set_media(media)
        self.player.play()
        self.current_playing_title = title