"""IDEA Standards Helper - a simple desktop app for non-technical users.

Double-click the .exe (or run this file with Python), choose a folder of
drawings, click one big button, and the app prepares everything needed to
apply the office standard inside IDEA Architecture 24.

Supports English and Greek.
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
ARROW_CHOICES_EL = {
    "Γεμάτο βέλος": "_CLOSED",
    "Ανοιχτό βέλος": "_OPEN",
    "Αρχιτεκτονική νυχιά": "_ARCHTICK",
}

SETTINGS_FILE = (
    Path(os.environ.get("APPDATA", Path.home())) / "IDEA Standards Helper" / "settings.json"
)

CONFIG_START = ";;; ------------------ CONFIG - EDIT THIS -----------------------"
CONFIG_END = ";;; ---------------- END CONFIG ---------------------------------"

# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------

TRANSLATIONS = {
    "en": {
        "app_title": "IDEA Standards Helper",
        "subtitle": "Make your IDEA drawings match your office standard — no typing needed.",
        "language": "Language",
        "help_btn": "What does this do?",
        "help_title": "What this app does",
        "help_body": (
            "This app gets your drawings ready for IDEA Architecture 24.\n\n"
            "1. Pick the folder with your drawings.\n"
            "2. Check the look settings (or leave the recommended ones).\n"
            "3. Press the green button.\n\n"
            "The app makes a backup, then creates a small file that IDEA can run.\n"
            "You then open IDEA, type SCRIPT, and choose that file.\n\n"
            "Every drawing gets the right layers, fonts, arrow style and dimensions "
            "automatically — no clicking through each drawing."
        ),
        "step1": "1  Where are your drawings?",
        "browse": "Browse…",
        "folder_hint": "Choose a folder to see your drawings.",
        "found": "Found {n} drawing(s).",
        "no_dwg": "No DWG drawings found in this folder.",
        "step2": "2  How should the drawings look? (leave as-is if unsure)",
        "font": "Text font",
        "note_height": "Note text height (mm)",
        "title_height": "Title text height (mm)",
        "dim_height": "Dimension text height (mm)",
        "arrow_size": "Arrow size (mm)",
        "dim_scale": "Dimension scale",
        "arrow_style": "Arrow style",
        "reset": "Use recommended settings",
        "reset_msg": "Settings reset to the recommended values.",
        "step3": "3  Options",
        "backup": "Make a backup of the drawings first (recommended)",
        "recursive": "Include drawings in subfolders",
        "auto": "Open IDEA automatically (only if set up below)",
        "advanced_closed": "Optional: let the app open IDEA for you   ▸",
        "advanced_open": "Optional: let the app open IDEA for you   ▾",
        "exe_label": "IDEA program (optional)",
        "exe_hint": (
            "Find IDEA.exe on the computer (usually in C:\\Program Files\\4M\\...). "
            "Leave this blank if you prefer to open IDEA yourself."
        ),
        "apply": "  APPLY TO MY DRAWINGS  ",
        "copy_path": "Copy script path",
        "open_folder": "Open drawings folder",
        "open_idea": "Open IDEA now",
        "log_label": "What happened",
        "welcome": (
            "Welcome! Choose the folder with your drawings, check the settings, "
            "then press the green button."
        ),
        "footer": (
            "Tip: try it on one test drawing first. Keep the backups until you are happy."
        ),
        "choose_folder_title": "Choose a folder",
        "choose_folder_body": "Please choose the folder with your drawings.",
        "no_drawings_title": "No drawings found",
        "no_drawings_body": "No DWG files were found in that folder.",
        "found_msg": "Found {n} drawing(s) in {folder}",
        "backup_msg": "Backup saved in: {backup}",
        "lisp_msg": "Your standard was written into IDEA_Standards.lsp",
        "script_msg": "Ready-to-run script created: {script}",
        "almost_done": "ALMOST DONE — in IDEA Architecture 24:",
        "step_a": "  1. Open the program.",
        "step_b": "  2. Type SCRIPT and press Enter.",
        "step_c": "  3. Choose this file: {script}",
        "after_done": "It will open each drawing, apply the standard, save and close it.",
        "copy_tip": "(Button above copies the path so you can paste it.)",
        "launched": "Launched IDEA: {name}",
        "idea_missing": "IDEA program not found at that path — use the SCRIPT steps above.",
        "copied": "Script path copied. You can paste it into the file dialog in IDEA.",
        "idea_not_set_title": "IDEA not set",
        "idea_not_set_body": (
            "Open the 'let the app open IDEA for you' section and browse to IDEA.exe first."
        ),
        "opened_idea": "Opened {name}.",
        "could_not_idea": "Could not open IDEA: {exc}",
        "num_error": "'{field}' must be a number (for example 2.5).",
        "check_numbers_title": "Check your numbers",
        "error_title": "Something went wrong",
        "error_msg": "Error: {exc}",
    },
    "el": {
        "app_title": "Βοηθός Προτύπων IDEA",
        "subtitle": "Κάντε τα σχέδια σας στο IDEA να ταιριάζουν με τα πρότυπα του γραφείου — χωρίς πληκτρολόγηση εντολών.",
        "language": "Γλώσσα",
        "help_btn": "Τι κάνει αυτό;",
        "help_title": "Τι κάνει αυτή η εφαρμογή;",
        "help_body": (
            "Η εφαρμογή ετοιμάζει τα σχέδιά σας για το IDEA Architecture 24.\n\n"
            "1. Επιλέξτε τον φάκελο με τα σχέδιά σας.\n"
            "2. Ελέγξτε τις ρυθμίσεις εμφάνισης (ή αφήστε τις προτεινόμενες).\n"
            "3. Πατήστε το πράσινο κουμπί.\n\n"
            "Η εφαρμογή κάνει αντίγραφο ασφαλείας και δημιουργεί ένα μικρό αρχείο "
            "που μπορεί να εκτελέσει το IDEA.\n"
            "Ανοίγετε το IDEA, πληκτρολογείτε SCRIPT και επιλέγετε αυτό το αρχείο.\n\n"
            "Κάθε σχέδιο αποκτά αυτόματα τα σωστά επίπεδα, γραμματοσειρές, βέλη "
            "και διαστάσεις — χωρίς να κάνετε κλικ σε κάθε σχέδιο ξεχωριστά."
        ),
        "step1": "1  Πού είναι τα σχέδιά σας;",
        "browse": "Αναζήτηση…",
        "folder_hint": "Επιλέξτε φάκελο για να δείτε τα σχέδιά σας.",
        "found": "Βρέθηκαν {n} σχέδια.",
        "no_dwg": "Δεν βρέθηκαν σχέδια DWG σε αυτόν τον φάκελο.",
        "step2": "2  Πώς πρέπει να μοιάζουν τα σχέδια; (αφήστε όπως είναι αν δεν ξέρετε)",
        "font": "Γραμματοσειρά κειμένου",
        "note_height": "Ύψος κειμένου σημειώσεων (mm)",
        "title_height": "Ύψος κειμένου τίτλου (mm)",
        "dim_height": "Ύψος κειμένου διαστάσεων (mm)",
        "arrow_size": "Μέγεθος βέλους (mm)",
        "dim_scale": "Κλίμακα διαστάσεων",
        "arrow_style": "Στυλ βέλους",
        "reset": "Χρήση προτεινόμενων ρυθμίσεων",
        "reset_msg": "Οι ρυθμίσεις επανήλθαν στις προτεινόμενες τιμές.",
        "step3": "3  Επιλογές",
        "backup": "Πρώτα αντίγραφο ασφαλείας των σχεδίων (συνιστάται)",
        "recursive": "Συμπερίληψη σχεδίων σε υποφακέλους",
        "auto": "Αυτόματο άνοιγμα του IDEA (μόνο αν ρυθμιστεί παρακάτω)",
        "advanced_closed": "Προαιρετικά: να ανοίγει η εφαρμογή το IDEA για εσάς   ▸",
        "advanced_open": "Προαιρετικά: να ανοίγει η εφαρμογή το IDEA για εσάς   ▾",
        "exe_label": "Πρόγραμμα IDEA (προαιρετικά)",
        "exe_hint": (
            "Βρείτε το IDEA.exe στον υπολογιστή (συνήθως στο C:\\Program Files\\4M\\...). "
            "Αφήστε το κενό αν προτιμάτε να ανοίγετε μόνοι σας το IDEA."
        ),
        "apply": "  ΕΦΑΡΜΟΓΗ ΣΤΑ ΣΧΕΔΙΑ ΜΟΥ  ",
        "copy_path": "Αντιγραφή διαδρομής",
        "open_folder": "Άνοιγμα φακέλου σχεδίων",
        "open_idea": "Άνοιγμα IDEA τώρα",
        "log_label": "Τι συνέβη",
        "welcome": "Καλώς ήρθατε! Επιλέξτε τον φάκελο με τα σχέδια σας, ελέγξτε τις ρυθμίσεις και πατήστε το πράσινο κουμπί.",
        "footer": "Συμβουλή: δοκιμάστε πρώτα σε ένα δοκιμαστικό σχέδιο. Κρατήστε τα αντίγραφα ασφαλείας μέχρι να μείνετε ικανοποιημένοι.",
        "choose_folder_title": "Επιλέξτε φάκελο",
        "choose_folder_body": "Παρακαλώ επιλέξτε τον φάκελο με τα σχέδια σας.",
        "no_drawings_title": "Δεν βρέθηκαν σχέδια",
        "no_drawings_body": "Δεν βρέθηκαν αρχεία DWG σε αυτόν τον φάκελο.",
        "found_msg": "Βρέθηκαν {n} σχέδια στον φάκελο {folder}",
        "backup_msg": "Το αντίγραφο ασφαλείας αποθηκεύτηκε στον φάκελο: {backup}",
        "lisp_msg": "Το πρότυπό σας γράφτηκε στο αρχείο IDEA_Standards.lsp",
        "script_msg": "Δημιουργήθηκε το έτοιμο σενάριο: {script}",
        "almost_done": "ΣΧΕΔΟΝ ΕΤΟΙΜΟ — στο IDEA Architecture 24:",
        "step_a": "  1. Ανοίξτε το πρόγραμμα.",
        "step_b": "  2. Πληκτρολογήστε SCRIPT και πατήστε Enter.",
        "step_c": "  3. Επιλέξτε αυτό το αρχείο: {script}",
        "after_done": "Θα ανοίξει κάθε σχέδιο, θα εφαρμόσει το πρότυπο, θα αποθηκεύσει και θα το κλείσει.",
        "copy_tip": "(Το παραπάνω κουμπί αντιγράφει τη διαδρομή για να την επικολλήσετε.)",
        "launched": "Άνοιξε το IDEA: {name}",
        "idea_missing": "Το IDEA δεν βρέθηκε σε αυτή τη διαδρομή — χρησιμοποιήστε τα παραπάνω βήματα SCRIPT.",
        "copied": "Η διαδρομή αντιγράφηκε. Μπορείτε να την επικολλήσετε στο παράθυρο αρχείων του IDEA.",
        "idea_not_set_title": "Το IDEA δεν έχει ρυθμιστεί",
        "idea_not_set_body": "Ανοίξτε την ενότητα «να ανοίγει η εφαρμογή το IDEA για εσάς» και επιλέξτε πρώτα το IDEA.exe.",
        "opened_idea": "Άνοιξε το {name}.",
        "could_not_idea": "Δεν ήταν δυνατό το άνοιγμα του IDEA: {exc}",
        "num_error": "Το «{field}» πρέπει να είναι αριθμός (π.χ. 2.5).",
        "check_numbers_title": "Ελέγξτε τους αριθμούς",
        "error_title": "Κάτι πήγε στραβά",
        "error_msg": "Σφάλμα: {exc}",
    },
}


def tr(lang: str, key: str, **fmt: object) -> str:
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(
        key, TRANSLATIONS["en"].get(key, key)
    )
    return text.format(**fmt) if fmt else text


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
        "language": "en",
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


def as_float(value: str, field_key: str, lang: str = "en") -> float:
    try:
        return float(str(value).strip().replace(",", "."))
    except ValueError:
        raise ValueError(tr(lang, "num_error", field=tr(lang, field_key)))


def generate_config(values: dict, lang: str = "en") -> str:
    """Build the CONFIG block of standards.lsp from the app fields."""
    note_h = as_float(values["note_height"], "note_height", lang)
    title_h = as_float(values["title_height"], "title_height", lang)
    dim_h = as_float(values["dim_height"], "dim_height", lang)
    arrow_size = as_float(values["arrow_size"], "arrow_size", lang)
    dim_scale = as_float(values["dim_scale"], "dim_scale", lang)
    font = values["font"].strip() or "arial.ttf"

    arrow_map = ARROW_CHOICES_EL if lang == "el" else ARROW_CHOICES
    arrow = arrow_map.get(values["arrow_style"], "_CLOSED")

    lines = ["(setq STD-LAYERS", "  (list"]
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


def build_lisp(values: dict, lang: str = "en") -> str:
    template = resource_path("standards.lsp").read_text(encoding="utf-8")
    if CONFIG_START not in template or CONFIG_END not in template:
        raise ValueError("standards.lsp is missing its CONFIG markers.")
    head, rest = template.split(CONFIG_START, 1)
    _, tail = rest.split(CONFIG_END, 1)
    return (
        head
        + CONFIG_START
        + "\n"
        + generate_config(values, lang)
        + CONFIG_END
        + tail
    )


def find_drawings(folder: Path, recursive: bool) -> list[Path]:
    candidates = folder.rglob("*") if recursive else folder.glob("*")
    return sorted(p for p in candidates if p.is_file() and p.suffix.lower() == ".dwg")


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.settings = load_settings()
        self.lang = self.settings.get("language", "en")
        self.title("IDEA Standards Helper")
        self.geometry("700x900")
        self.minsize(620, 720)
        self.configure(bg="#f4f6f8")
        try:
            self.iconbitmap(str(resource_path("app_icon.ico")))
        except Exception:
            pass
        self._build_ui()

    # ---------------- translation helper ----------------
    def t(self, key: str, **fmt: object) -> str:
        return tr(self.lang, key, **fmt)

    # ---------------- UI ----------------
    def _build_ui(self) -> None:
        for child in list(self.winfo_children()):
            child.destroy()

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
        self.canvas = canvas
        canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        content = ttk.Frame(canvas, padding=18)
        canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind(
            "<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        tk.Label(
            content,
            text=self.t("app_title"),
            font=("Segoe UI", 18, "bold"),
            bg="#f4f6f8",
            fg="#1f2937",
        ).pack(anchor="w")

        header_row = ttk.Frame(content)
        header_row.pack(fill="x", pady=(2, 14))
        tk.Label(
            header_row,
            text=self.t("subtitle"),
            font=("Segoe UI", 10),
            bg="#f4f6f8",
            fg="#5b6573",
        ).pack(side="left", fill="x", expand=True)
        self.lang_var = tk.StringVar(
            value="Ελληνικά" if self.lang == "el" else "English"
        )
        lang_box = ttk.Combobox(
            header_row,
            textvariable=self.lang_var,
            values=["English", "Ελληνικά"],
            state="readonly",
            width=12,
        )
        lang_box.pack(side="right")
        lang_box.bind("<<ComboboxSelected>>", self.change_language)
        ttk.Button(header_row, text=self.t("help_btn"), command=self.show_help).pack(
            side="right", padx=(0, 8)
        )

        # --- Step 1: folder ---
        folder_box = ttk.Labelframe(
            content, text=self.t("step1"), padding=12, style="Section.TLabelframe"
        )
        folder_box.pack(fill="x", pady=6)
        row = ttk.Frame(folder_box)
        row.pack(fill="x")
        self.folder_var = tk.StringVar(value=self.settings.get("folder", ""))
        ttk.Entry(row, textvariable=self.folder_var, width=62).pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        ttk.Button(row, text=self.t("browse"), command=self.pick_folder).pack(side="left")
        self.folder_var.trace_add("write", lambda *_: self.refresh_count())
        self.count_var = tk.StringVar(value=self.t("folder_hint"))
        ttk.Label(folder_box, textvariable=self.count_var, foreground="#5b6573").pack(
            anchor="w", pady=(8, 0)
        )

        # --- Step 2: standard ---
        std_box = ttk.Labelframe(
            content, text=self.t("step2"), padding=12, style="Section.TLabelframe"
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
            ("font", 26),
            ("note_height", 10),
            ("title_height", 10),
            ("dim_height", 10),
            ("arrow_size", 10),
            ("dim_scale", 10),
        ]
        grid = ttk.Frame(std_box)
        grid.pack(fill="x")
        for index, (key, width) in enumerate(fields):
            r, c = divmod(index, 2)
            ttk.Label(grid, text=self.t(key)).grid(
                row=r * 2, column=c, sticky="w", padx=(0, 16), pady=(6, 2)
            )
            ttk.Entry(grid, textvariable=self.vars[key], width=width).grid(
                row=r * 2 + 1, column=c, sticky="w", padx=(0, 16), pady=(0, 6)
            )
        ttk.Label(grid, text=self.t("arrow_style")).grid(
            row=6, column=0, sticky="w", padx=(0, 16), pady=(6, 2)
        )
        arrow_map = ARROW_CHOICES_EL if self.lang == "el" else ARROW_CHOICES
        stored_arrow = self.settings.get("arrow_style", "Filled arrow")
        if stored_arrow in arrow_map.values():
            # stored value may be a code from another language; map back to label
            for label, code in arrow_map.items():
                if code == stored_arrow:
                    stored_arrow = label
                    break
        else:
            stored_arrow = next(iter(arrow_map))
        self.arrow_var = tk.StringVar(value=stored_arrow)
        ttk.Combobox(
            grid,
            textvariable=self.arrow_var,
            values=list(arrow_map),
            state="readonly",
            width=24,
        ).grid(row=7, column=0, sticky="w", padx=(0, 16), pady=(0, 6))
        ttk.Button(grid, text=self.t("reset"), command=self.reset_standard).grid(
            row=7, column=1, sticky="w"
        )

        # --- Step 3: options ---
        opt_box = ttk.Labelframe(
            content, text=self.t("step3"), padding=12, style="Section.TLabelframe"
        )
        opt_box.pack(fill="x", pady=6)
        self.backup_var = tk.BooleanVar(value=self.settings["backup"])
        self.recursive_var = tk.BooleanVar(value=self.settings["recursive"])
        self.auto_var = tk.BooleanVar(value=self.settings["auto_run"])
        ttk.Checkbutton(
            opt_box, text=self.t("backup"), variable=self.backup_var
        ).pack(anchor="w")
        ttk.Checkbutton(
            opt_box, text=self.t("recursive"), variable=self.recursive_var
        ).pack(anchor="w")
        ttk.Checkbutton(
            opt_box, text=self.t("auto"), variable=self.auto_var
        ).pack(anchor="w")

        # --- Optional advanced section, hidden until asked for ---
        self.advanced_open = False
        self.advanced_btn = ttk.Button(
            content,
            text=self.t("advanced_closed"),
            command=self.toggle_advanced,
        )
        self.advanced_btn.pack(anchor="w", pady=(8, 0))
        self.advanced_holder = ttk.Frame(content)
        exe_box = ttk.Labelframe(
            self.advanced_holder,
            text=self.t("exe_label"),
            padding=12,
            style="Section.TLabelframe",
        )
        exe_box.pack(fill="x")
        row = ttk.Frame(exe_box)
        row.pack(fill="x")
        self.exe_var = tk.StringVar(value=self.settings.get("idea_exe", ""))
        ttk.Entry(row, textvariable=self.exe_var, width=54).pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        ttk.Button(row, text=self.t("browse"), command=self.pick_exe).pack(side="left")
        ttk.Label(
            exe_box, text=self.t("exe_hint"), foreground="#5b6573"
        ).pack(anchor="w", pady=(8, 0))
        self.recursive_var.trace_add("write", lambda *_: self.refresh_count())

        # --- Action ---
        self.apply_button = tk.Button(
            content,
            text=self.t("apply"),
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
            actions, text=self.t("copy_path"), command=self.copy_path, state="disabled"
        )
        self.copy_btn.pack(side="left", padx=(0, 8))
        self.open_btn = ttk.Button(
            actions, text=self.t("open_folder"), command=self.open_folder, state="disabled"
        )
        self.open_btn.pack(side="left", padx=(0, 8))
        self.launch_btn = ttk.Button(
            actions, text=self.t("open_idea"), command=self.launch_idea, state="disabled"
        )
        self.launch_btn.pack(side="left")

        ttk.Label(
            content, text=self.t("log_label"), font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(16, 4))
        self.log = scrolledtext.ScrolledText(
            content, height=10, wrap="word", font=("Segoe UI", 10),
            bg="#ffffff", fg="#263238", relief="solid", borderwidth=1,
        )
        self.log.pack(fill="both", expand=True)
        self.log.configure(state="disabled")

        tk.Label(
            content,
            text=self.t("footer"),
            font=("Segoe UI", 9),
            bg="#f4f6f8",
            fg="#5b6573",
        ).pack(anchor="w", pady=(10, 0))

        self.message(self.t("welcome"))
        if getattr(self, "last_script", None):
            self.copy_btn.configure(state="normal")
            self.open_btn.configure(state="normal")
            self.launch_btn.configure(
                state="normal" if Path(self.settings.get("idea_exe", "")).is_file() else "disabled"
            )

    def _on_mousewheel(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ---------------- helpers ----------------
    def change_language(self, _event: object = None) -> None:
        self.settings.update(self.current_values())
        self.settings["language"] = "el" if self.lang_var.get() == "Ελληνικά" else "en"
        self.lang = self.settings["language"]
        save_settings(self.settings)
        self._build_ui()
        self.refresh_count()

    def show_help(self) -> None:
        messagebox.showinfo(self.t("help_title"), self.t("help_body"))

    def reset_standard(self) -> None:
        defaults = load_settings()
        for key in (
            "font", "note_height", "title_height", "dim_height",
            "arrow_size", "dim_scale",
        ):
            self.vars[key].set(defaults[key])
        arrow_map = ARROW_CHOICES_EL if self.lang == "el" else ARROW_CHOICES
        self.arrow_var.set(next(iter(arrow_map)))
        self.message(self.t("reset_msg"))

    def toggle_advanced(self) -> None:
        if self.advanced_open:
            self.advanced_holder.pack_forget()
            self.advanced_btn.configure(text=self.t("advanced_closed"))
            self.advanced_open = False
        else:
            self.advanced_holder.pack(fill="x", pady=(6, 0))
            self.advanced_btn.configure(text=self.t("advanced_open"))
            self.advanced_open = True

    def launch_idea(self) -> None:
        exe = self.exe_var.get().strip()
        if not exe or not Path(exe).is_file():
            messagebox.showwarning(self.t("idea_not_set_title"), self.t("idea_not_set_body"))
            return
        try:
            subprocess.Popen([exe])
            self.message(self.t("opened_idea", name=Path(exe).name))
        except Exception as exc:  # pragma: no cover - platform specific
            self.message(self.t("could_not_idea", exc=exc))

    def message(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
        self.update_idletasks()

    def current_values(self) -> dict:
        arrow_map = ARROW_CHOICES_EL if self.lang == "el" else ARROW_CHOICES
        return {
            "folder": self.folder_var.get().strip(),
            "idea_exe": self.exe_var.get().strip(),
            "font": self.vars["font"].get(),
            "note_height": self.vars["note_height"].get(),
            "title_height": self.vars["title_height"].get(),
            "dim_height": self.vars["dim_height"].get(),
            "arrow_size": self.vars["arrow_size"].get(),
            "dim_scale": self.vars["dim_scale"].get(),
            "arrow_style": arrow_map.get(self.arrow_var.get(), "_CLOSED"),
            "backup": self.backup_var.get(),
            "recursive": self.recursive_var.get(),
            "auto_run": self.auto_var.get(),
            "language": self.lang,
        }

    def store_settings(self) -> None:
        save_settings(self.current_values())

    def pick_folder(self) -> None:
        chosen = filedialog.askdirectory(title=self.t("step1"))
        if chosen:
            self.folder_var.set(chosen)
            self.refresh_count()

    def pick_exe(self) -> None:
        chosen = filedialog.askopenfilename(
            title=self.t("exe_label"),
            filetypes=[("Program", "*.exe"), ("All files", "*.*")],
        )
        if chosen:
            self.exe_var.set(chosen)
            self.store_settings()

    def refresh_count(self) -> None:
        folder = Path(self.folder_var.get().strip())
        if not folder.is_dir():
            self.count_var.set(self.t("folder_hint"))
            return
        files = find_drawings(folder, self.recursive_var.get())
        self.count_var.set(
            self.t("found", n=len(files)) if files else self.t("no_dwg")
        )

    def copy_path(self) -> None:
        path = getattr(self, "last_script", None)
        if path:
            self.clipboard_clear()
            self.clipboard_append(str(path))
            self.message(self.t("copied"))

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
            messagebox.showwarning(self.t("choose_folder_title"), self.t("choose_folder_body"))
            return

        try:
            build_lisp(values, self.lang)
            files = find_drawings(folder, values["recursive"])
            if not files:
                messagebox.showwarning(
                    self.t("no_drawings_title"), self.t("no_drawings_body")
                )
                return

            self.log.configure(state="normal")
            self.log.delete("1.0", "end")
            self.log.configure(state="disabled")
            self.progress.start(10)
            self.message(self.t("found_msg", n=len(files), folder=folder))

            if values["backup"]:
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                backup = folder / f"Standards Backup {stamp}"
                for dwg in files:
                    target = backup / dwg.relative_to(folder)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(dwg, target)
                self.message(self.t("backup_msg", backup=backup))

            lisp_file = folder / "IDEA_Standards.lsp"
            lisp_file.write_text(build_lisp(values, self.lang), encoding="utf-8")
            self.message(self.t("lisp_msg"))

            script_file = folder / "apply_standards.scr"
            build_script(files, lisp_file, script_file)
            self.message(self.t("script_msg", script=script_file))

            self.last_script = script_file
            self.last_folder = folder
            self.progress.stop()
            self.copy_btn.configure(state="normal")
            self.open_btn.configure(state="normal")
            self.launch_btn.configure(
                state="normal" if Path(values["idea_exe"]).is_file() else "disabled"
            )

            self.message("")
            self.message(self.t("almost_done"))
            self.message(self.t("step_a"))
            self.message(self.t("step_b"))
            self.message(self.t("step_c", script=script_file))
            self.message(self.t("after_done"))
            self.message(self.t("copy_tip"))

            if values["auto_run"] and values["idea_exe"]:
                exe = Path(values["idea_exe"])
                if exe.is_file():
                    try:
                        subprocess.Popen([str(exe), "/b", str(script_file)])
                        self.message(self.t("launched", name=exe.name))
                    except Exception as exc:  # pragma: no cover - platform specific
                        self.message(self.t("could_not_idea", exc=exc))
                else:
                    self.message(self.t("idea_missing"))

        except ValueError as exc:
            self.progress.stop()
            messagebox.showerror(self.t("check_numbers_title"), str(exc))
        except Exception as exc:
            self.progress.stop()
            messagebox.showerror(self.t("error_title"), str(exc))
            self.message(self.t("error_msg", exc=exc))


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
