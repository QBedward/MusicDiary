import tkinter as tk
from tkinter import messagebox
from backend.UserAccount import register_user, verify_user

class AuthWindow:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.root.configure(bg="#121212")

        self.frame = tk.Frame(self.root, bg="#1e1e1e", padx=30, pady=30)
        self.frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.title_lbl = tk.Label(self.frame, text="Music Diary Login", bg="#1e1e1e", fg="white", font=("Segoe UI", 16, "bold"))
        self.title_lbl.pack(pady=(0, 20))

        tk.Label(self.frame, text="Username", bg="#1e1e1e", fg="#9ca3af", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.username_entry = tk.Entry(self.frame, bg="#252525", fg="white", insertbackground="white", font=("Segoe UI", 11), bd=0)
        self.username_entry.pack(fill=tk.X, ipady=6, pady=(2, 15))

        tk.Label(self.frame, text="Password", bg="#1e1e1e", fg="#9ca3af", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.password_entry = tk.Entry(self.frame, bg="#252525", fg="white", insertbackground="white", font=("Segoe UI", 11), show="*", bd=0)
        self.password_entry.pack(fill=tk.X, ipady=6, pady=(2, 20))

        self.login_btn = tk.Button(
            self.frame, text="Log In", bg="#3b82f6", fg="white", bd=0,
            font=("Segoe UI", 10, "bold"), pady=8, cursor="hand2",
            command=self.handle_login
        )
        self.login_btn.pack(fill=tk.X, pady=(0, 10))

        self.register_btn = tk.Button(
            self.frame, text="Create New Account", bg="#252525", fg="#d1d5db", bd=0,
            font=("Segoe UI", 9), pady=6, cursor="hand2",
            command=self.handle_register
        )
        self.register_btn.pack(fill=tk.X)

    def handle_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        success, message = verify_user(username, password)
        if success:
            messagebox.showinfo("Success", message)
            self.on_login_success(username.strip())
        else:
            messagebox.showerror("Login Failed", message)

    def handle_register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        success, message = register_user(username, password)
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Registration Failed", message)