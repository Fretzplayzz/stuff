import json
import os
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

APP_TITLE = "Aqua Launcher"
CONFIG_FILE = Path("apps.json")

DEFAULT_APPS = [
    {"name": "Notepad", "path": r"C:\\Windows\\System32\\notepad.exe", "emoji": "📝"},
    {"name": "Calculator", "path": r"C:\\Windows\\System32\\calc.exe", "emoji": "🧮"},
    {"name": "Paint", "path": r"C:\\Windows\\System32\\mspaint.exe", "emoji": "🎨"},
]


class DockButton(tk.Canvas):
    def __init__(self, parent, app, launch_callback):
        super().__init__(
            parent,
            width=84,
            height=96,
            bg="#000000",
            highlightthickness=0,
            bd=0,
        )
        self.app = app
        self.launch_callback = launch_callback
        self.circle = self.create_oval(8, 8, 76, 76, fill="#1f2937", outline="#374151", width=2)
        self.icon = self.create_text(42, 42, text=app.get("emoji", "🚀"), fill="#ffffff", font=("Segoe UI Emoji", 24))
        self.label = self.create_text(42, 88, text=app.get("name", "App"), fill="#d1d5db", font=("Segoe UI", 9))

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

    def on_enter(self, _event):
        self.itemconfigure(self.circle, fill="#2563eb", outline="#60a5fa")
        self.scale("all", 42, 48, 1.08, 1.08)

    def on_leave(self, _event):
        self.itemconfigure(self.circle, fill="#1f2937", outline="#374151")
        self.scale("all", 42, 48, 1 / 1.08, 1 / 1.08)

    def on_click(self, _event):
        self.launch_callback(self.app)


class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("760x220")
        self.minsize(600, 200)
        self.configure(bg="#000000")

        self.apps = self.load_apps()
        self.create_ui()

    def create_ui(self):
        top = tk.Frame(self, bg="#000000")
        top.pack(fill="x", padx=16, pady=(12, 4))

        title = tk.Label(top, text=APP_TITLE, fg="#f9fafb", bg="#000000", font=("Segoe UI", 13, "bold"))
        title.pack(side="left")

        add_button = tk.Button(
            top,
            text="+ Add App",
            bg="#1f2937",
            fg="#f9fafb",
            activebackground="#374151",
            activeforeground="#f9fafb",
            relief="flat",
            padx=12,
            command=self.add_app,
        )
        add_button.pack(side="right")

        dock_shell = tk.Frame(self, bg="#000000")
        dock_shell.pack(fill="both", expand=True, padx=16, pady=8)

        self.dock = tk.Frame(dock_shell, bg="#111827", padx=16, pady=12)
        self.dock.place(relx=0.5, rely=0.5, anchor="center")

        self.render_apps()

    def render_apps(self):
        for w in self.dock.winfo_children():
            w.destroy()

        for app in self.apps:
            button = DockButton(self.dock, app, self.launch_app)
            button.pack(side="left", padx=8)

    def launch_app(self, app):
        path = app.get("path", "")
        if not path:
            return
        try:
            subprocess.Popen(path, shell=True)
        except OSError as exc:
            messagebox.showerror("Launch failed", f"Could not launch {app.get('name', 'app')}:\n{exc}")

    def add_app(self):
        selected = filedialog.askopenfilename(
            title="Choose an application",
            filetypes=[("Applications", "*.exe"), ("All files", "*.*")],
        )
        if not selected:
            return

        name = os.path.splitext(os.path.basename(selected))[0]
        new_app = {"name": name, "path": selected, "emoji": "⚡"}
        self.apps.append(new_app)
        self.save_apps()
        self.render_apps()

    def load_apps(self):
        if CONFIG_FILE.exists():
            try:
                with CONFIG_FILE.open("r", encoding="utf-8") as fh:
                    apps = json.load(fh)
                    if isinstance(apps, list):
                        return apps
            except (OSError, json.JSONDecodeError):
                pass

        self.save_apps(DEFAULT_APPS)
        return DEFAULT_APPS.copy()

    def save_apps(self, data=None):
        payload = data if data is not None else self.apps
        try:
            with CONFIG_FILE.open("w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
        except OSError as exc:
            messagebox.showwarning("Save warning", f"Could not save app list:\n{exc}")


if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
