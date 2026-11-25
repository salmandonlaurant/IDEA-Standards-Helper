"""IDEA Standards Helper - a simple desktop app for non-technical users.

Double-click the .exe (or run this file with Python), choose a folder of
drawings, click one big button, and the app prepares everything needed to
apply the office standard inside IDEA Architecture 24.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from make_batch import build_script

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_LAYERS = [
    ("0", 7, "CONTINUOUS"),
    ("A-WALL-EXT", 1, "CONTINUOUS"),
    ("A-WALL-INT", 8, "CONTINUOUS"),
    ("A-DOOR", 2, "CONTINUOUS"),
    ("A-WINDOW", 4, "CONTINUOUS"),
    ("A-SPACE", 5, "CONTINUOUS"),
    ("A-FURNITURE", 3, "CONTINUOUS"),
    ("A-DIM", 6, "CONTINUOUS"),
    ("A-TEXT", 7, "CONTINUOUS"),
    ("A-VENT", 140, "DASHED"),
    ("A-FIRE", 1, "CONTINUOUS"),
]

ARROW_CHOICES = {
    "Filled arrow": "_CLOSED",
    "Open arrow": "_OPEN",
    "Architectural tick": "_ARCHTICK",
}

SETTINGS_FILE = (
    Path(os.environ.get("APPDATA", Path.home())) / "IDEA Standards Helper" / "settings.json"
)

CONFIG_START = ";;; ------------------ CONFIG - EDIT THIS -----------------------"
CONFIG_END = ";;; ---------------- END CONFIG ---------------------------------"


def resource_path(name: str) -> Path:
    """Find a bundled file both when running from source and from the .exe."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / name
    return Path(__file__).resolve().parent / name


def load_settings() -> dict:
    defaults = {
        "folder": "",
        "idea_exe": "",
        "font": "arial.ttf",
        "note_height": "2.5",
        "title_height": "3.5",
        "dim_height": "2.5",
        "arrow_size": "2.5",
        "arrow_style": "Filled arrow",
        "dim_scale": "1.0",
        "backup": True,
        "recursive": False,
        "auto_run": False,
    }
    try:
        if SETTINGS_FILE.is_file():
            defaults.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
    except Exception:
        pass
    return defaults


def save_settings(data: dict) -> None:
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def as_float(value: str, field: str) -> float:
    try:
        return float(str(value).strip().replace(",", "."))
    except ValueError:
        raise ValueError(f"'{field}' must be a number (for example 2.5).")


def generate_config(values: dict) -> str:
    """Build the CONFIG block of standards.lsp from the app fields."""
    note_h = as_float(values["note_height"], "Note text height")
    title_h = as_float(values["title_height"], "Title text height")
    dim_h = as_float(values["dim_height"], "Dimension text height")
    arrow_size = as_float(values["arrow_size"], "Arrow size")
    dim_scale = as_float(values["dim_scale"], "Dimension scale")
    font = values["font"].strip() or "arial.ttf"
    arrow = ARROW_CHOICES.get(values["arrow_style"], "_CLOSED")

    lines = [
        "(setq STD-LAYERS",
        "  (list",
    ]
    for name, colour, ltype in DEFAULT_LAYERS:
        lines.append(f'    (list "{name}" {colour} "{ltype}")')
    lines += [
        "  )",
        ")",
        "",
        "(setq STD-TEXTSTYLES",
        "  (list",
        f'    (list "STD-NOTE"    "{font}" {note_h} 1.0 0.0)',
        f'    (list "STD-TITLE"   "{font}" {title_h} 1.0 0.0)',
        f'    (list "STD-DIMTXT"  "{font}" {dim_h} 1.0 0.0)',
        "  )",
        ")",
        "",
        f'(setq STD-ARROW "{arrow}")',
        "",
        "(setq STD-DIMVARS",
        "  (list",
        '    (cons "DIMTXSTY"   "STD-DIMTXT")',
        f"    (cons \"DIMTXT\"     {dim_h})",
        f"    (cons \"DIMASZ\"     {arrow_size})",
        '    (cons "DIMBLK"     STD-ARROW)',
        '    (cons "DIMBLK1"    STD-ARROW)',
        '    (cons "DIMBLK2"    STD-ARROW)',
        '    (cons "DIMLDRBLK"  STD-ARROW)',
        "    (cons \"DIMEXE\"     1.25)",
        "    (cons \"DIMEXO\"     0.625)",
        "    (cons \"DIMGAP\"     0.625)",
        "    (cons \"DIMTAD\"     1)",
        "    (cons \"DIMDEC\"     0)",
        "    (cons \"DIMTIX\"     1)",
        "    (cons \"DIMSOXD\"    0)",
        "    (cons \"DIMZIN\"     8)",
        f"    (cons \"DIMSCALE\"   {dim_scale})",
        '    (cons "DIMCLRD"    256)',
        '    (cons "DIMCLRE"    256)',
        '    (cons "DIMCLRT"    256)',
        "  )",
        ")",
        "",
        '(setq STD-DIMSTYLE   "STD-DIM")',
        '(setq STD-CURLAYER   "A-WALL-EXT")',
        '(setq STD-CURTEXT    "STD-NOTE")',
    ]
    return "\n".join(lines) + "\n"


def build_lisp(values: dict) -> str:
    template = resource_path("standards.lsp").read_text(encoding="utf-8")
    if CONFIG_START not in template or CONFIG_END not in template:
        raise ValueError("standards.lsp is missing its CONFIG markers.")
    head, rest = template.split(CONFIG_START, 1)
    _, tail = rest.split(CONFIG_END, 1)
    return head + CONFIG_START + "\n" + generate_config(values) + CONFIG_END + tail


def find_drawings(folder: Path, recursive: bool) -> list[Path]:
    candidates = folder.rglob("*") if recursive else folder.glob("*")
    return sorted(p for p in candidates if p.is_file() and p.suffix.lower() == ".dwg")


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.settings = load_settings()
        self.title("IDEA Standards Helper")
        self.geometry("700x880")
        self.minsize(620, 700)
        self.configure(bg="#f4f6f8")
        try:
            self.iconbitmap(str(resource_path("app_icon.ico")))
        except Exception:
            pass
        self._build_ui()

    # ---------------- UI ----------------
    def _build_ui(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))

        canvas = tk.Canvas(self, bg="#f4f6f8", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        content = ttk.Frame(canvas, padding=18)
        canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind(
            "<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )

        tk.Label(
            content,
            text="IDEA Standards Helper",
            font=("Segoe UI", 18, "bold"),
            bg="#f4f6f8",
            fg="#1f2937",
        ).pack(anchor="w")
        header_row = ttk.Frame(content)
        header_row.pack(fill="x", pady=(2, 14))
        tk.Label(
            header_row,
            text="Make your IDEA drawings match your office standard — no typing needed.",
            font=("Segoe UI", 10),
            bg="#f4f6f8",
            fg="#5b6573",
        ).pack(side="left")
        ttk.Button(header_row, text="What does this do?", command=self.show_help).pack(
            side="right"
        )

        # --- Step 1: folder ---
        folder_box = ttk.Labelframe(
            content, text="1  Where are your drawings?", padding=12,
            style="Section.TLabelframe",
        )
        folder_box.pack(fill="x", pady=6)
        row = ttk.Frame(folder_box)
        row.pack(fill="x")
        self.folder_var = tk.StringVar(value=self.settings["folder"])
        ttk.Entry(row, textvariable=self.folder_var, width=62).pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        self.folder_var.trace_add("write", lambda *_: self.refresh_count())
        ttk.Button(row, text="Browse…", command=self.pick_folder).pack(side="left")
        self.count_var = tk.StringVar(value="Choose a folder to see your drawings.")
        ttk.Label(folder_box, textvariable=self.count_var, foreground="#5b6573").pack(
            anchor="w", pady=(8, 0)
        )

        # --- Step 2: standard ---
        std_box = ttk.Labelframe(
            content, text="2  How should the drawings look? (leave as-is if unsure)", padding=12,
            style="Section.TLabelframe",
        )
        std_box.pack(fill="x", pady=6)
        self.vars = {
            key: tk.StringVar(value=str(self.settings[key]))
            for key in (
                "font", "note_height", "title_height", "dim_height",
                "arrow_size", "dim_scale",
            )
        }
        fields = [
            ("Text font", "font", 26),
            ("Note text height (mm)", "note_height", 10),
            ("Title text height (mm)", "title_height", 10),
            ("Dimension text height (mm)", "dim_height", 10),
            ("Arrow size (mm)", "arrow_size", 10),
            ("Dimension scale", "dim_scale", 10),
        ]
        grid = ttk.Frame(std_box)
        grid.pack(fill="x")
        for index, (label, key, width) in enumerate(fields):
            r, c = divmod(index, 2)
            ttk.Label(grid, text=label).grid(row=r * 2, column=c, sticky="w", padx=(0, 16), pady=(6, 2))
            ttk.Entry(grid, textvariable=self.vars[key], width=width).grid(
                row=r * 2 + 1, column=c, sticky="w", padx=(0, 16), pady=(0, 6)
            )
        ttk.Label(grid, text="Arrow style").grid(row=6, column=0, sticky="w", padx=(0, 16), pady=(6, 2))
        self.arrow_var = tk.StringVar(value=self.settings["arrow_style"])
        ttk.Combobox(
            grid,
            textvariable=self.arrow_var,
            values=list(ARROW_CHOICES),
            state="readonly",
            width=24,
        ).grid(row=7, column=0, sticky="w", padx=(0, 16), pady=(0, 6))
        ttk.Button(
            grid, text="Use recommended settings", command=self.reset_standard
        ).grid(row=7, column=1, sticky="w")

        # --- Step 3: options ---
        opt_box = ttk.Labelframe(
            content, text="3  Options", padding=12, style="Section.TLabelframe"
        )
        opt_box.pack(fill="x", pady=6)
        self.backup_var = tk.BooleanVar(value=self.settings["backup"])
        self.recursive_var = tk.BooleanVar(value=self.settings["recursive"])
        self.auto_var = tk.BooleanVar(value=self.settings["auto_run"])
        ttk.Checkbutton(
            opt_box, text="Make a backup of the drawings first (recommended)",
            variable=self.backup_var,
        ).pack(anchor="w")
        ttk.Checkbutton(
            opt_box, text="Include drawings in subfolders",
            variable=self.recursive_var,
        ).pack(anchor="w")
        ttk.Checkbutton(
            opt_box, text="Open IDEA automatically (only if set up below)",
            variable=self.auto_var,
        ).pack(anchor="w")

        # --- Optional advanced section, hidden until asked for ---
        self.advanced_open = False
        self.advanced_btn = ttk.Button(
            content,
            text="Optional: let the app open IDEA for you   ▸",
            command=self.toggle_advanced,
        )
        self.advanced_btn.pack(anchor="w", pady=(8, 0))
        self.advanced_holder = ttk.Frame(content)

        exe_box = ttk.Labelframe(
            self.advanced_holder,
            text="IDEA program (optional)",
            padding=12,
            style="Section.TLabelframe",
        )
        exe_box.pack(fill="x")
        row = ttk.Frame(exe_box)
        row.pack(fill="x")
        self.exe_var = tk.StringVar(value=self.settings["idea_exe"])
        ttk.Entry(row, textvariable=self.exe_var, width=54).pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        ttk.Button(row, text="Browse…", command=self.pick_exe).pack(side="left")
        ttk.Label(
            exe_box,
            text="Find IDEA.exe on the computer (usually in C:\\Program Files\\4M\\...). "
                 "Leave this blank if you prefer to open IDEA yourself.",
            foreground="#5b6573",
        ).pack(anchor="w", pady=(8, 0))

        self.recursive_var.trace_add("write", lambda *_: self.refresh_count())

        # --- Action ---
        self.apply_button = tk.Button(
            content,
            text="  APPLY TO MY DRAWINGS  ",
            command=self.apply,
            bg="#2e7d32",
            fg="white",
            activebackground="#256b28",
            activeforeground="white",
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=10,
        )
        self.apply_button.pack(pady=(18, 8), fill="x")
        self.progress = ttk.Progressbar(content, mode="indeterminate", length=100)
        self.progress.pack(fill="x", pady=(0, 8))

        actions = ttk.Frame(content)
        actions.pack(fill="x")
        self.copy_btn = ttk.Button(
            actions, text="Copy script path", command=self.copy_path, state="disabled"
        )
        self.copy_btn.pack(side="left", padx=(0, 8))
        self.open_btn = ttk.Button(
            actions, text="Open drawings folder", command=self.open_folder, state="disabled"
        )
        self.open_btn.pack(side="left", padx=(0, 8))
        self.launch_btn = ttk.Button(
            actions, text="Open IDEA now", command=self.launch_idea, state="disabled"
        )
        self.launch_btn.pack(side="left")

        ttk.Label(content, text="What happened", font=("Segoe UI", 10, "bold")).pack(
            anchor="w", pady=(16, 4)
        )
        self.log = scrolledtext.ScrolledText(
            content, height=10, wrap="word", font=("Segoe UI", 10),
            bg="#ffffff", fg="#263238", relief="solid", borderwidth=1,
        )
        self.log.pack(fill="both", expand=True)
        self.log.configure(state="disabled")

        tk.Label(
            content,
            text="Tip: try it on one test drawing first. Keep the backups until you are happy.",
            font=("Segoe UI", 9),
            bg="#f4f6f8",
            fg="#5b6573",
        ).pack(anchor="w", pady=(10, 0))

        self.message(
            "Welcome! Choose the folder with your drawings, check the settings, "
            "then press the green button."
        )

    # ---------------- helpers ----------------
    def show_help(self) -> None:
        messagebox.showinfo(
            "What this app does",
            "This app gets your drawings ready for IDEA Architecture 24.\n\n"
            "1. Pick the folder with your drawings.\n"
            "2. Check the look settings (or leave the recommended ones).\n"
            "3. Press the green button.\n\n"
            "The app makes a backup, then creates a small file that IDEA can run.\n"
            "You then open IDEA, type SCRIPT, and choose that file.\n\n"
            "Every drawing gets the right layers, fonts, arrow style and dimensions "
            "automatically — no clicking through each drawing.",
        )

    def reset_standard(self) -> None:
        defaults = load_settings()
        for key in (
            "font", "note_height", "title_height", "dim_height",
            "arrow_size", "dim_scale",
        ):
            self.vars[key].set(defaults[key])
        self.arrow_var.set(defaults["arrow_style"])
        self.message("Settings reset to the recommended values.")

    def toggle_advanced(self) -> None:
        if self.advanced_open:
            self.advanced_holder.pack_forget()
            self.advanced_btn.configure(text="Optional: let the app open IDEA for you   ▸")
            self.advanced_open = False
        else:
            self.advanced_holder.pack(fill="x", pady=(6, 0))
            self.advanced_btn.configure(text="Optional: let the app open IDEA for you   ▾")
            self.advanced_open = True

    def launch_idea(self) -> None:
        exe = self.exe_var.get().strip()
        if not exe or not Path(exe).is_file():
            messagebox.showwarning(
                "IDEA not set",
                "Open the 'Optional: let the app open IDEA for you' section and "
                "browse to IDEA.exe first.",
            )
            return
        try:
            subprocess.Popen([exe])
            self.message(f"Opened {Path(exe).name}.")
        except Exception as exc:  # pragma: no cover - platform specific
            self.message(f"Could not open IDEA: {exc}")

    def message(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
        self.update_idletasks()

    def current_values(self) -> dict:
        return {
            "folder": self.folder_var.get().strip(),
            "idea_exe": self.exe_var.get().strip(),
            "font": self.vars["font"].get(),
            "note_height": self.vars["note_height"].get(),
            "title_height": self.vars["title_height"].get(),
            "dim_height": self.vars["dim_height"].get(),
            "arrow_size": self.vars["arrow_size"].get(),
            "dim_scale": self.vars["dim_scale"].get(),
            "arrow_style": self.arrow_var.get(),
            "backup": self.backup_var.get(),
            "recursive": self.recursive_var.get(),
            "auto_run": self.auto_var.get(),
        }

    def store_settings(self) -> None:
        save_settings(self.current_values())

    def pick_folder(self) -> None:
        chosen = filedialog.askdirectory(title="Choose the folder with your drawings")
        if chosen:
            self.folder_var.set(chosen)
            self.refresh_count()

    def pick_exe(self) -> None:
        chosen = filedialog.askopenfilename(
            title="Find IDEA.exe", filetypes=[("Program", "*.exe"), ("All files", "*.*")]
        )
        if chosen:
            self.exe_var.set(chosen)
            self.store_settings()

    def refresh_count(self) -> None:
        folder = Path(self.folder_var.get().strip())
        if not folder.is_dir():
            self.count_var.set("Choose a folder to see your drawings.")
            return
        files = find_drawings(folder, self.recursive_var.get())
        self.count_var.set(
            f"Found {len(files)} drawing(s)." if files else "No DWG drawings found in this folder."
        )

    def copy_path(self) -> None:
        path = getattr(self, "last_script", None)
        if path:
            self.clipboard_clear()
            self.clipboard_append(str(path))
            self.message("Script path copied. You can paste it into the file dialog in IDEA.")

    def open_folder(self) -> None:
        folder = getattr(self, "last_folder", None)
        if folder and folder.is_dir():
            os.startfile(folder)  # type: ignore[attr-defined]

    # ---------------- main action ----------------
    def apply(self) -> None:
        values = self.current_values()
        self.store_settings()
        folder = Path(values["folder"])

        if not values["folder"] or not folder.is_dir():
            messagebox.showwarning("Choose a folder", "Please choose the folder with your drawings.")
            return

        try:
            # Validate numbers before writing anything.
            build_lisp(values)
            files = find_drawings(folder, values["recursive"])
            if not files:
                messagebox.showwarning(
                    "No drawings found", "No DWG files were found in that folder."
                )
                return

            self.log.configure(state="normal")
            self.log.delete("1.0", "end")
            self.log.configure(state="disabled")
            self.progress.start(10)
            self.message(f"Found {len(files)} drawing(s) in {folder}")

            if values["backup"]:
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                backup = folder / f"Standards Backup {stamp}"
                for dwg in files:
                    target = backup / dwg.relative_to(folder)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(dwg, target)
                self.message(f"Backup saved in: {backup}")

            lisp_file = folder / "IDEA_Standards.lsp"
            lisp_file.write_text(build_lisp(values), encoding="utf-8")
            self.message("Your standard was written into IDEA_Standards.lsp")

            script_file = folder / "apply_standards.scr"
            build_script(files, lisp_file, script_file)
            self.message(f"Ready-to-run script created: {script_file}")

            self.last_script = script_file
            self.last_folder = folder
            self.progress.stop()
            self.copy_btn.configure(state="normal")
            self.open_btn.configure(state="normal")
            self.launch_btn.configure(
                state="normal" if Path(values["idea_exe"]).is_file() else "disabled"
            )

            self.message("")
            self.message("ALMOST DONE — in IDEA Architecture 24:")
            self.message("  1. Open the program.")
            self.message("  2. Type SCRIPT and press Enter.")
            self.message(f"  3. Choose this file: {script_file}")
            self.message("It will open each drawing, apply the standard, save and close it.")
            self.message("(Button above copies the path so you can paste it.)")

            if values["auto_run"] and values["idea_exe"]:
                exe = Path(values["idea_exe"])
                if exe.is_file():
                    try:
                        subprocess.Popen([str(exe), "/b", str(script_file)])
                        self.message(f"Launched IDEA: {exe.name}")
                    except Exception as exc:  # pragma: no cover - platform specific
                        self.message(f"Could not launch IDEA automatically: {exc}")
                else:
                    self.message("IDEA program not found at that path — use the SCRIPT steps above.")

        except ValueError as exc:
            self.progress.stop()
            messagebox.showerror("Check your numbers", str(exc))
        except Exception as exc:
            self.progress.stop()
            messagebox.showerror("Something went wrong", str(exc))
            self.message(f"Error: {exc}")


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
