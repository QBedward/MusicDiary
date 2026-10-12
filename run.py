import tkinter as tk
from frontend.auth import AuthWindow
from frontend.search import MusicDiaryApp
from utils.center_window import center_window

def launch_main_app(username):
    # Clear login widgets
    for widget in root.winfo_children():
        widget.destroy()
    # Resize and center dashboard for the logged-in user
    center_window(root, 1000, 700)
    MusicDiaryApp(root, username)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Personal Music Diary System")
    
    # Center login window on startup
    center_window(root, 400, 450)
    
    # Start with Authentication Window first
    AuthWindow(root, launch_main_app)
    root.mainloop()