import json
import os
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog

APP_TITLE = "Aqua Launcher"
CONFIG_FILE = Path("apps.json")

DEFAULT_APPS = [
    {"name": "Notepad", "path": r"C:\\Windows\\System32\\notepad.exe", "emoji": "📝"},
    {"name": "Calculator", "path": r"C:\\Windows\\System32\\calc.exe", "emoji": "🧮"},
    {"name": "Paint", "path": r"C:\\Windows\\System32\\mspaint.exe", "emoji": "🎨"},
]


class DockButton(tk.Canvas):
    def __init__(self, parent, app, launch_callback, remove_callback):
        super().__init__(
            parent,
            width=98,
            height=116,
            bg=parent.cget("bg"),
            highlightthickness=0,
            bd=0,
        )
        self.app = app
        self.launch_callback = launch_callback
        self.remove_callback = remove_callback
        self.hovered = False

        self.shadow = self.create_oval(28, 76, 70, 86, fill="#0a0a0a", outline="")
        self.tile = self.create_oval(16, 16, 82, 82, fill="#334155", outline="#94a3b8", width=2)
        self.gloss = self.create_arc(20, 20, 78, 62, start=0, extent=180, style="arc", outline="#dbeafe", width=2)
        self.icon = self.create_text(49, 51, text=app.get("emoji", "🚀"), fill="#ffffff", font=("Segoe UI Emoji", 27))
        self.indicator = self.create_oval(44, 92, 54, 102, fill="#38bdf8", outline="", state="hidden")
        self.label = self.create_text(49, 110, text=app.get("name", "App"), fill="#cbd5e1", font=("Segoe UI", 9, "bold"))

        self.bind_all_children("<Enter>", self.on_enter)
        self.bind_all_children("<Leave>", self.on_leave)
        self.bind_all_children("<Button-1>", self.on_click)
        self.bind_all_children("<Button-3>", self.on_right_click)

    def bind_all_children(self, event_name, callback):
        self.bind(event_name, callback)
        for item_id in self.find_all():
            self.tag_bind(item_id, event_name, callback)

    def on_enter(self, _event):
        if self.hovered:
            return
        self.hovered = True
        self.itemconfigure(self.tile, fill="#2563eb", outline="#bfdbfe")
        self.itemconfigure(self.indicator, state="normal")
        self.itemconfigure(self.label, fill="#f8fafc")
        self.scale("all", 49, 58, 1.1, 1.1)

    def on_leave(self, _event):
        if not self.hovered:
            return
        self.hovered = False
        self.itemconfigure(self.tile, fill="#334155", outline="#94a3b8")
        self.itemconfigure(self.indicator, state="hidden")
        self.itemconfigure(self.label, fill="#cbd5e1")
        self.scale("all", 49, 58, 1 / 1.1, 1 / 1.1)

    def on_click(self, _event):
        self.launch_callback(self.app)

    def on_right_click(self, _event):
        self.remove_callback(self.app)


class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("980x420")
        self.minsize(760, 320)
        self.configure(bg="#020617")

        self.apps = self.load_apps()

        self.background = tk.Canvas(self, highlightthickness=0, bd=0, bg="#020617")
        self.background.pack(fill="both", expand=True)
        self.background.bind("<Configure>", self.redraw_background)

        self.root_layer = tk.Frame(self.background, bg="#020617")
        self.background_window = self.background.create_window(0, 0, anchor="nw", window=self.root_layer)

        self.create_ui()

    def redraw_background(self, event):
        self.background.coords(self.background_window, 0, 0)
        self.background.itemconfigure(self.background_window, width=event.width, height=event.height)

        self.background.delete("bg")
        width = event.width
        height = event.height

        bands = [
            ("#020617", 0),
            ("#0b1122", int(height * 0.28)),
            ("#111827", int(height * 0.58)),
            ("#1e293b", height),
        ]
        for index in range(len(bands) - 1):
            color, start_y = bands[index]
            _, end_y = bands[index + 1]
            self.background.create_rectangle(0, start_y, width, end_y, fill=color, outline="", tags="bg")

    def create_ui(self):
        menu = tk.Frame(self.root_layer, bg="#030712", height=32)
        menu.pack(fill="x")

        tk.Label(menu, text="●  ●  ●", fg="#fda4af", bg="#030712", font=("Segoe UI", 10)).pack(side="left", padx=14)
        tk.Label(menu, text=APP_TITLE, fg="#e2e8f0", bg="#030712", font=("Segoe UI", 10, "bold")).pack(side="left")

        actions = tk.Frame(menu, bg="#030712")
        actions.pack(side="right", padx=12)

        tk.Button(
            actions,
            text="+ Add App",
            command=self.add_app,
            relief="flat",
            bd=0,
            padx=12,
            pady=4,
            bg="#1d4ed8",
            fg="#ffffff",
            activebackground="#2563eb",
            activeforeground="#ffffff",
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="right")

        headline = tk.Frame(self.root_layer, bg="#020617")
        headline.pack(fill="x", pady=(18, 0))

        tk.Label(
            headline,
            text="Launch your apps like a Mac dock",
            bg="#020617",
            fg="#f8fafc",
            font=("Segoe UI", 24, "bold"),
        ).pack()
        tk.Label(
            headline,
            text="Click to open • Right-click to remove",
            bg="#020617",
            fg="#94a3b8",
            font=("Segoe UI", 11),
        ).pack(pady=(6, 0))

        dock_shell = tk.Frame(self.root_layer, bg="#020617")
        dock_shell.pack(fill="both", expand=True, pady=24)

        self.dock_shadow = tk.Frame(dock_shell, bg="#020202", height=126)
        self.dock_shadow.place(relx=0.5, rely=0.52, anchor="center", relwidth=0.88)

        self.dock = tk.Frame(
            dock_shell,
            bg="#0f172acc",
            padx=20,
            pady=16,
            highlightbackground="#475569",
            highlightthickness=1,
        )
        self.dock.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.86)

        footer = tk.Label(
            self.root_layer,
            text="Tip: Right-click any icon to remove it from the dock.",
            bg="#020617",
            fg="#64748b",
            font=("Segoe UI", 9),
        )
        footer.pack(pady=(0, 16))

        self.render_apps()

    def render_apps(self):
        for widget in self.dock.winfo_children():
            widget.destroy()

        for app in self.apps:
            button = DockButton(self.dock, app, self.launch_app, self.remove_app)
            button.pack(side="left", padx=6)

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

        default_name = os.path.splitext(os.path.basename(selected))[0]
        name = simpledialog.askstring("App name", "Display name for this app:", initialvalue=default_name)
        if not name:
            name = default_name

        emoji = simpledialog.askstring("Icon", "Enter an emoji for the dock icon:", initialvalue="⚡")
        if not emoji:
            emoji = "⚡"

        new_app = {"name": name.strip() or default_name, "path": selected, "emoji": emoji.strip()[:2]}
        self.apps.append(new_app)
        self.save_apps()
        self.render_apps()

    def remove_app(self, app):
        if app not in self.apps:
            return
        confirmed = messagebox.askyesno("Remove app", f"Remove '{app.get('name', 'App')}' from the dock?")
        if not confirmed:
            return

        self.apps.remove(app)
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
