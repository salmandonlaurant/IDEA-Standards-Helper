"""IDEA Standards Helper - a simple desktop app for non-technical users.

Double-click the .exe (or run this file with Python), choose a folder of
drawings, click one big button, and the app prepares everything needed to
apply the office standard inside IDEA Architecture 24.

Also includes an optional bilingual OpenCode assistant. OpenCode runs as a
small local service started by this app; the chat stays inside this window.

Supports English and Greek.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import platform
import queue
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
import tkinter as tk

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
OPENCODE_DIR = (
    Path(os.environ.get("LOCALAPPDATA", Path.home())) / "IDEA Standards Helper" / "opencode"
)
OPENCODE_EXE = OPENCODE_DIR / "opencode.exe"

OPENCODE_WINDOWS_URLS = {
    "AMD64": "https://opencode.ai/update/api/latest/cli/opencode/opencode-windows-x64.zip",
    "ARM64": "https://opencode.ai/update/api/latest/cli/opencode/opencode-windows-arm64.zip",
}
DEFAULT_MODEL = "openrouter/anthropic/claude-sonnet-5.5"

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
        # --- assistant ---
        "assistant_closed": "4  AI Assistant (OpenCode)   ▸",
        "assistant_open": "4  AI Assistant (OpenCode)   ▾",
        "assistant_intro": (
            "Type what you want in English or Greek. The assistant works inside "
            "the drawings folder and can apply standards, create scripts and edit files."
        ),
        "assistant_status": "Status: {status}",
        "status_not_installed": "OpenCode is not installed yet",
        "status_installed": "OpenCode is installed (not running)",
        "status_running": "OpenCode is running",
        "setup_btn": "Set up OpenCode (one time)",
        "setup_wait": "Downloading OpenCode… this can take a minute.",
        "setup_done": "OpenCode is ready. Add an API key below, then press Start assistant.",
        "setup_failed": "Could not set up OpenCode automatically: {exc}",
        "api_key_label": "AI provider key (OpenRouter)",
        "api_key_hint": (
            "Paste an OpenRouter API key. It is saved only on this computer. "
            "You can get one at openrouter.ai/keys."
        ),
        "model_label": "AI model",
        "start_assistant": "Start assistant",
        "stop_assistant": "Stop assistant",
        "assistant_ready": "Assistant ready. Ask it to do something below.",
        "assistant_starting": "Starting OpenCode…",
        "assistant_stopped": "Assistant stopped.",
        "send": "Send",
        "assistant_thinking": "Thinking…",
        "assistant_help": "Ask: 'Apply the office standards to all drawings' or 'Τι πρέπει να αλλάξω;'",
        "need_api_key_title": "API key needed",
        "need_api_key_body": "Please paste an OpenRouter API key before starting the assistant.",
        "need_folder_title": "Choose a folder first",
        "need_folder_body": "Choose the drawings folder above before starting the assistant.",
        "assistant_error": "Assistant error: {exc}",
        "assistant_welcome": "OpenCode assistant connected. How can I help with these drawings?",
        "assistant_note": (
            "Full project access is enabled. Backups are still made automatically before "
            "drawing files are changed."
        ),
        "setup_title": "OpenCode setup",
        "create_idea_config": "Prepared OpenCode instructions in the drawings folder.",
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
        # --- assistant ---
        "assistant_closed": "4  Βοηθός AI (OpenCode)   ▸",
        "assistant_open": "4  Βοηθός AI (OpenCode)   ▾",
        "assistant_intro": (
            "Γράψτε αυτό που θέλετε στα Ελληνικά ή τα Αγγλικά. Ο βοηθός εργάζεται μέσα "
            "στον φάκελο των σχεδίων και μπορεί να εφαρμόσει πρότυπα, να δημιουργήσει σενάρια "
            "και να επεξεργαστεί αρχεία."
        ),
        "assistant_status": "Κατάσταση: {status}",
        "status_not_installed": "Το OpenCode δεν είναι εγκατεστημένο ακόμη",
        "status_installed": "Το OpenCode είναι εγκατεστημένο (δεν τρέχει)",
        "status_running": "Το OpenCode τρέχει",
        "setup_btn": "Εγκατάσταση OpenCode (μία φορά)",
        "setup_wait": "Λήψη OpenCode… μπορεί να πάρει ένα λεπτό.",
        "setup_done": "Το OpenCode είναι έτοιμο. Προσθέστε κλειδί API παρακάτω και πατήστε «Εκκίνηση βοηθού».",
        "setup_failed": "Δεν ήταν δυνατή η αυτόματη εγκατάσταση: {exc}",
        "api_key_label": "Κλειδί παρόχου AI (OpenRouter)",
        "api_key_hint": (
            "Επικολλήστε ένα κλειδί OpenRouter. Αποθηκεύεται μόνο σε αυτόν τον υπολογιστή. "
            "Μπορείτε να το πάρετε από το openrouter.ai/keys."
        ),
        "model_label": "Μοντέλο AI",
        "start_assistant": "Εκκίνηση βοηθού",
        "stop_assistant": "Διακοπή βοηθού",
        "assistant_ready": "Ο βοηθός είναι έτοιμος. Ρωτήστε τον τι θέλετε.",
        "assistant_starting": "Εκκίνηση OpenCode…",
        "assistant_stopped": "Ο βοηθός διακόπηκε.",
        "send": "Αποστολή",
        "assistant_thinking": "Σκέφτεται…",
        "assistant_help": "Ρωτήστε: «Εφάρμοσε τα πρότυπα σε όλα τα σχέδια» ή «Τι πρέπει να αλλάξω;»",
        "need_api_key_title": "Χρειάζεται κλειδί API",
        "need_api_key_body": "Επικολλήστε ένα κλειδί OpenRouter πριν ξεκινήσετε τον βοηθό.",
        "need_folder_title": "Επιλέξτε πρώτα φάκελο",
        "need_folder_body": "Επιλέξτε τον φάκελο με τα σχέδια πριν ξεκινήσετε τον βοηθό.",
        "assistant_error": "Σφάλμα βοηθού: {exc}",
        "assistant_welcome": "Ο βοηθός OpenCode συνδέθηκε. Πώς μπορώ να βοηθήσω με αυτά τα σχέδια;",
        "assistant_note": (
            "Η πλήρης πρόσβαση στον φάκελο είναι ενεργή. Παρ' όλα αυτά, γίνεται αυτόματα "
            "αντίγραφο ασφαλείας πριν αλλαχθούν σχέδια."
        ),
        "setup_title": "Εγκατάσταση OpenCode",
        "create_idea_config": "Δημιουργήθηκαν οδηγίες OpenCode στον φάκελο των σχεδίων.",
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
        "opencode_key": "",
        "opencode_model": DEFAULT_MODEL,
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
        f'    (cons "DIMTXT"     {dim_h})',
        f'    (cons "DIMASZ"     {arrow_size})',
        '    (cons "DIMBLK"     STD-ARROW)',
        '    (cons "DIMBLK1"    STD-ARROW)',
        '    (cons "DIMBLK2"    STD-ARROW)',
        '    (cons "DIMLDRBLK"  STD-ARROW)',
        '    (cons "DIMEXE"     1.25)',
        '    (cons "DIMEXO"     0.625)',
        '    (cons "DIMGAP"     0.625)',
        '    (cons "DIMTAD"     1)',
        '    (cons "DIMDEC"     0)',
        '    (cons "DIMTIX"     1)',
        '    (cons "DIMSOXD"    0)',
        '    (cons "DIMZIN"     8)',
        f'    (cons "DIMSCALE"   {dim_scale})',
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
    return head + CONFIG_START + "\n" + generate_config(values, lang) + CONFIG_END + tail


def find_drawings(folder: Path, recursive: bool) -> list[Path]:
    candidates = folder.rglob("*") if recursive else folder.glob("*")
    return sorted(p for p in candidates if p.is_file() and p.suffix.lower() == ".dwg")


def prepare_standards(values: dict, lang: str = "en", log=None) -> dict:
    """Create backup, LISP and SCR. Shared by the button and the CLI mode."""
    folder = Path(values["folder"])
    if not folder.is_dir():
        raise ValueError(tr(lang, "choose_folder_body"))

    # Validate numbers before touching anything.
    build_lisp(values, lang)

    files = find_drawings(folder, bool(values.get("recursive")))
    if not files:
        raise ValueError(tr(lang, "no_drawings_body"))

    if log:
        log(tr(lang, "found_msg", n=len(files), folder=folder))

    backup_path = None
    if values.get("backup", True):
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = folder / f"Standards Backup {stamp}"
        for dwg in files:
            target = backup_path / dwg.relative_to(folder)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dwg, target)
        if log:
            log(tr(lang, "backup_msg", backup=backup_path))

    lisp_file = folder / "IDEA_Standards.lsp"
    lisp_file.write_text(build_lisp(values, lang), encoding="utf-8")
    if log:
        log(tr(lang, "lisp_msg"))

    script_file = folder / "apply_standards.scr"
    build_script(files, lisp_file, script_file)
    if log:
        log(tr(lang, "script_msg", script=script_file))

    return {
        "status": "ok",
        "folder": str(folder),
        "drawings": len(files),
        "backup": str(backup_path) if backup_path else None,
        "lisp": str(lisp_file),
        "script": str(script_file),
    }


# ---------------------------------------------------------------------------
# OpenCode support
# ---------------------------------------------------------------------------

def find_opencode() -> Path | None:
    if OPENCODE_EXE.is_file():
        return OPENCODE_EXE
    found = shutil.which("opencode")
    return Path(found) if found else None


def install_opencode() -> Path:
    """Download the official Windows CLI zip and extract opencode.exe."""
    machine = (platform.machine() or "AMD64").upper()
    url = OPENCODE_WINDOWS_URLS.get(machine, OPENCODE_WINDOWS_URLS["AMD64"])
    OPENCODE_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = OPENCODE_DIR / "opencode-cli.zip"
    urllib.request.urlretrieve(url, zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        candidates = [n for n in zf.namelist() if n.lower().endswith("opencode.exe")]
        if not candidates:
            raise RuntimeError("The downloaded zip did not contain opencode.exe.")
        zf.extract(candidates[0], OPENCODE_DIR)
        extracted = OPENCODE_DIR / candidates[0]
        if extracted.resolve() != OPENCODE_EXE.resolve():
            if OPENCODE_EXE.exists():
                OPENCODE_EXE.unlink()
            extracted.replace(OPENCODE_EXE)
    zip_path.unlink(missing_ok=True)
    if not OPENCODE_EXE.is_file():
        raise RuntimeError("OpenCode installation did not produce opencode.exe.")
    return OPENCODE_EXE


def write_idea_config(folder: Path, model: str) -> None:
    """Project config for OpenCode: model + broad permissions."""
    folder.mkdir(parents=True, exist_ok=True)
    config = {
        "$schema": "https://opencode.ai/config.json",
        "model": model or DEFAULT_MODEL,
        "permissions": [{"action": "*", "resource": "*", "effect": "allow"}],
    }
    (folder / "opencode.jsonc").write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def write_idea_instructions(folder: Path, exe: Path, lang: str) -> None:
    """Give OpenCode a skill + AGENTS.md so it knows the IDEA workflow."""
    skill_dir = folder / ".opencode" / "skills" / "idea-helper"
    skill_dir.mkdir(parents=True, exist_ok=True)
    exe_s = str(exe)
    folder_s = str(folder)
    body = f"""---
name: IDEA Helper
description: Apply office standards, create IDEA scripts, inspect drawings, and help with architecture drafting tasks in this folder. Use for any IDEA Architecture 24 request.
---

## Language

Always answer in the same language as the user. If the user writes Greek, answer fully in Greek. If the user writes English, answer in English.

## Where you are

The working directory is {folder_s}. It contains IDEA Architecture 24 DWG drawings. You have full read/write access inside this folder. Do not modify files outside it.

## IMPORTANT: use the helper program for standard work

The packaged app also has a hidden command-line mode. Call it instead of guessing LISP code:

- List what it can do: `"{exe_s}" --cli help --out "{folder_s}\\idea_helper_last_result.json"`
- Inspect drawings: `"{exe_s}" --cli report --folder "{folder_s}" --out "{folder_s}\\idea_helper_last_result.json"`
- Apply office standards: `"{exe_s}" --cli apply --folder "{folder_s}" --backup true --out "{folder_s}\\idea_helper_last_result.json"`

After every call, read `idea_helper_last_result.json` in this folder and use the JSON result in your answer. The app window has no console output, so the JSON file is the result.

The apply action automatically creates a `Standards Backup <timestamp>` folder before changing anything. Never delete backups.

## The IDEA execution step

Applying standards creates `apply_standards.scr` and `IDEA_Standards.lsp`. The user must still open IDEA Architecture 24, type `SCRIPT`, and choose `apply_standards.scr`. Always tell them this in their language.

## Other drafting requests

For dimensions, fonts/colours, arrow types, interior/exterior walls, insulation, ventilation, interior spaces or furniture placement:

1. Inspect the folder first (`--cli report` or normal file tools).
2. If it is an office-standard change, use `--cli apply`.
3. If it needs new automation, write a clearly named `.lsp` file in this folder and tell the user to run it with `SCRIPT` in IDEA. Keep it reversible and explain what it does.
4. Never claim you edited a DWG directly unless you actually wrote or ran a script that does so.

## Safety

Be concrete and brief. Show which files you created. Keep Greek users fully informed in Greek.
"""
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    agents = f"""# IDEA Architecture 24 workspace

This folder contains DWG drawings for IDEA Architecture 24.

- Respond in the user's language (Greek if they write Greek).
- Use the `idea-helper` skill for all IDEA tasks.
- Prefer the helper CLI at `{exe_s}` with `--cli` for standards work; read `idea_helper_last_result.json` afterwards.
- Always preserve `Standards Backup *` folders.
- To execute a script in IDEA: open IDEA, type SCRIPT, choose the `.scr` file.
"""
    (folder / "AGENTS.md").write_text(agents, encoding="utf-8")


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


# ---------------------------------------------------------------------------
# CLI mode (used by OpenCode)
# ---------------------------------------------------------------------------

def _bool_arg(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def cli_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="IDEA Standards Helper")
    sub = parser.add_subparsers(dest="action", required=True)

    help_p = sub.add_parser("help")
    help_p.add_argument("--out", default=None)
    report = sub.add_parser("report")
    report.add_argument("--folder", required=True)
    report.add_argument("--recursive", default=None)

    apply_p = sub.add_parser("apply")
    apply_p.add_argument("--folder", required=True)
    apply_p.add_argument("--backup", default=None)
    apply_p.add_argument("--recursive", default=None)
    apply_p.add_argument("--font", default=None)
    apply_p.add_argument("--note-height", default=None)
    apply_p.add_argument("--title-height", default=None)
    apply_p.add_argument("--dim-height", default=None)
    apply_p.add_argument("--arrow-size", default=None)
    apply_p.add_argument("--dim-scale", default=None)

    for p in (report, apply_p):
        p.add_argument("--out", default=None)

    args = parser.parse_args(argv)
    settings = load_settings()
    lang = settings.get("language", "en")
    out_path: Path | None = None
    result: dict

    try:
        if args.action == "help":
            out_path = Path(args.out) if args.out else None
            result = {
                "status": "ok",
                "program": "IDEA Standards Helper",
                "actions": [
                    {"name": "help", "description": "List these actions."},
                    {"name": "report", "description": "List DWG files in a folder."},
                    {"name": "apply", "description": "Backup and write IDEA standards + SCR."},
                ],
            }
        else:
            folder = Path(args.folder)
            out_path = Path(args.out) if args.out else folder / "idea_helper_last_result.json"
            if args.action == "report":
                files = find_drawings(folder, _bool_arg(args.recursive, bool(settings.get("recursive"))))
                result = {
                    "status": "ok",
                    "folder": str(folder),
                    "drawings": [str(p) for p in files],
                    "count": len(files),
                }
            else:  # apply
                values = dict(settings)
                values["folder"] = str(folder)
                values["backup"] = _bool_arg(args.backup, bool(settings.get("backup", True)))
                values["recursive"] = _bool_arg(args.recursive, bool(settings.get("recursive")))
                for key, attr in (
                    ("font", "font"),
                    ("note_height", "note_height"),
                    ("title_height", "title_height"),
                    ("dim_height", "dim_height"),
                    ("arrow_size", "arrow_size"),
                    ("dim_scale", "dim_scale"),
                ):
                    val = getattr(args, attr)
                    if val is not None:
                        values[key] = val
                result = prepare_standards(values, lang)
    except Exception as exc:
        result = {"status": "error", "error": str(exc)}
        if out_path is None:
            out_path = Path.cwd() / "idea_helper_last_result.json"

    if out_path is not None:
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("status") == "ok" else 1


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.settings = load_settings()
        self.lang = self.settings.get("language", "en")
        self.title("IDEA Standards Helper")
        self.geometry("760x1040")
        self.minsize(680, 760)
        self.configure(bg="#f4f6f8")
        try:
            self.iconbitmap(str(resource_path("app_icon.ico")))
        except Exception:
            pass

        # Runtime state for the assistant.
        self.ai_proc: subprocess.Popen | None = None
        self.ai_base_url = ""
        self.ai_password = ""
        self.ai_session_id: str | None = None
        self.ai_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.ai_busy = False
        self.chat_history: list[tuple[str, str]] = []
        self.log_history: list[str] = []
        self.last_script: Path | None = None
        self.last_folder: Path | None = None
        self.assistant_open = False

        self._build_ui()
        self.after(150, self._drain_ai_queue)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

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
        self.lang_var = tk.StringVar(value="Ελληνικά" if self.lang == "el" else "English")
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
            ("font", 26), ("note_height", 10), ("title_height", 10),
            ("dim_height", 10), ("arrow_size", 10), ("dim_scale", 10),
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
            for label, code in arrow_map.items():
                if code == stored_arrow:
                    stored_arrow = label
                    break
        else:
            stored_arrow = next(iter(arrow_map))
        self.arrow_var = tk.StringVar(value=stored_arrow)
        ttk.Combobox(
            grid, textvariable=self.arrow_var, values=list(arrow_map),
            state="readonly", width=24,
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
        ttk.Checkbutton(opt_box, text=self.t("backup"), variable=self.backup_var).pack(anchor="w")
        ttk.Checkbutton(opt_box, text=self.t("recursive"), variable=self.recursive_var).pack(anchor="w")
        ttk.Checkbutton(opt_box, text=self.t("auto"), variable=self.auto_var).pack(anchor="w")

        # --- Optional advanced section, hidden until asked for ---
        self.advanced_open = False
        self.advanced_btn = ttk.Button(
            content, text=self.t("advanced_closed"), command=self.toggle_advanced
        )
        self.advanced_btn.pack(anchor="w", pady=(8, 0))
        self.advanced_holder = ttk.Frame(content)
        exe_box = ttk.Labelframe(
            self.advanced_holder, text=self.t("exe_label"), padding=12,
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
        ttk.Label(exe_box, text=self.t("exe_hint"), foreground="#5b6573").pack(
            anchor="w", pady=(8, 0)
        )
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

        # --- Step 4: OpenCode assistant ---
        self.assistant_btn = ttk.Button(
            content,
            text=self.t("assistant_open" if self.assistant_open else "assistant_closed"),
            command=self.toggle_assistant,
        )
        self.assistant_btn.pack(anchor="w", pady=(18, 0))
        self.assistant_holder = ttk.Frame(content)
        if self.assistant_open:
            self._build_assistant(self.assistant_holder)

        # --- Log ---
        ttk.Label(
            content, text=self.t("log_label"), font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(16, 4))
        self.log = scrolledtext.ScrolledText(
            content, height=9, wrap="word", font=("Segoe UI", 10),
            bg="#ffffff", fg="#263238", relief="solid", borderwidth=1,
        )
        self.log.pack(fill="both", expand=True)
        self.log.configure(state="disabled")
        for line in self.log_history:
            self._append_log(line)

        tk.Label(
            content, text=self.t("footer"), font=("Segoe UI", 9),
            bg="#f4f6f8", fg="#5b6573",
        ).pack(anchor="w", pady=(10, 0))

        if not self.log_history:
            self.message(self.t("welcome"))
        if getattr(self, "last_script", None):
            self.copy_btn.configure(state="normal")
            self.open_btn.configure(state="normal")
            self.launch_btn.configure(
                state="normal" if Path(self.settings.get("idea_exe", "")).is_file() else "disabled"
            )
        self.refresh_count()

    def _build_assistant(self, parent: ttk.Frame) -> None:
        for child in list(parent.winfo_children()):
            child.destroy()

        box = ttk.Labelframe(
            parent, text="OpenCode", padding=12, style="Section.TLabelframe"
        )
        box.pack(fill="x", pady=(6, 0))

        status = tr(
            self.lang,
            "assistant_status",
            status=tr(self.lang, "status_running" if self.ai_proc else "status_installed" if find_opencode() else "status_not_installed"),
        )
        tk.Label(box, text=status, font=("Segoe UI", 9), fg="#5b6573").pack(anchor="w")
        tk.Label(
            box, text=self.t("assistant_intro"), font=("Segoe UI", 9),
            fg="#5b6573", wraplength=660, justify="left",
        ).pack(anchor="w", pady=(4, 8))

        setup_row = ttk.Frame(box)
        setup_row.pack(fill="x")
        ttk.Button(setup_row, text=self.t("setup_btn"), command=self.setup_opencode).pack(side="left")
        ttk.Button(setup_row, text=self.t("start_assistant"), command=self.start_assistant).pack(side="left", padx=(8, 0))
        self.stop_btn = ttk.Button(
            setup_row, text=self.t("stop_assistant"), command=self.stop_assistant,
            state="normal" if self.ai_proc else "disabled",
        )
        self.stop_btn.pack(side="left", padx=(8, 0))

        creds = ttk.Frame(box)
        creds.pack(fill="x", pady=(10, 0))
        ttk.Label(creds, text=self.t("api_key_label")).pack(anchor="w")
        self.key_var = tk.StringVar(value=self.settings.get("opencode_key", ""))
        ttk.Entry(creds, textvariable=self.key_var, show="*", width=60).pack(fill="x")
        ttk.Label(creds, text=self.t("api_key_hint"), foreground="#5b6573").pack(anchor="w", pady=(3, 0))
        ttk.Label(creds, text=self.t("model_label")).pack(anchor="w", pady=(8, 0))
        self.model_var = tk.StringVar(value=self.settings.get("opencode_model", DEFAULT_MODEL))
        ttk.Entry(creds, textvariable=self.model_var, width=60).pack(fill="x")

        ttk.Label(box, text=self.t("assistant_note"), foreground="#5b6573", wraplength=660).pack(
            anchor="w", pady=(8, 4)
        )

        self.chat = scrolledtext.ScrolledText(
            box, height=8, wrap="word", font=("Segoe UI", 10),
            bg="#fbfcfd", fg="#263238", relief="solid", borderwidth=1,
        )
        self.chat.pack(fill="both", expand=True)
        self.chat.configure(state="disabled")
        for role, text in self.chat_history:
            self._append_chat(role, text)

        send_row = ttk.Frame(box)
        send_row.pack(fill="x", pady=(6, 0))
        self.prompt_var = tk.StringVar()
        self.prompt_entry = ttk.Entry(send_row, textvariable=self.prompt_var)
        self.prompt_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.send_btn = ttk.Button(send_row, text=self.t("send"), command=self.send_prompt)
        self.send_btn.pack(side="left")
        self.prompt_entry.bind("<Return>", lambda _e: self.send_prompt())

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

    def toggle_assistant(self) -> None:
        if self.assistant_open:
            self.assistant_holder.pack_forget()
            self.assistant_btn.configure(text=self.t("assistant_closed"))
            self.assistant_open = False
        else:
            self.assistant_holder.pack(fill="x", pady=(6, 0))
            self._build_assistant(self.assistant_holder)
            self.assistant_btn.configure(text=self.t("assistant_open"))
            self.assistant_open = True

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

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def message(self, text: str) -> None:
        self.log_history.append(text)
        self._append_log(text)
        self.update_idletasks()

    def _append_chat(self, role: str, text: str) -> None:
        prefix = "You: " if role == "user" else "OpenCode: "
        self.chat.configure(state="normal")
        self.chat.insert("end", prefix + text + "\n\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def current_values(self) -> dict:
        arrow_map = ARROW_CHOICES_EL if self.lang == "el" else ARROW_CHOICES
        values = {
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
        if hasattr(self, "key_var"):
            values["opencode_key"] = self.key_var.get().strip()
        if hasattr(self, "model_var"):
            values["opencode_model"] = self.model_var.get().strip() or DEFAULT_MODEL
        return values

    def store_settings(self) -> None:
        self.settings.update(self.current_values())
        save_settings(self.settings)

    def pick_folder(self) -> None:
        chosen = filedialog.askdirectory(title=self.t("step1"))
        if chosen:
            self.folder_var.set(chosen)
            self.refresh_count()
            self.store_settings()

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
        self.count_var.set(self.t("found", n=len(files)) if files else self.t("no_dwg"))

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
            self.progress.start(10)
            result = prepare_standards(values, self.lang, log=self.message)
            self.progress.stop()

            self.last_script = Path(result["script"])
            self.last_folder = Path(result["folder"])
            self.copy_btn.configure(state="normal")
            self.open_btn.configure(state="normal")
            self.launch_btn.configure(
                state="normal" if Path(values["idea_exe"]).is_file() else "disabled"
            )

            self.message("")
            self.message(self.t("almost_done"))
            self.message(self.t("step_a"))
            self.message(self.t("step_b"))
            self.message(self.t("step_c", script=result["script"]))
            self.message(self.t("after_done"))
            self.message(self.t("copy_tip"))

            if values["auto_run"] and values["idea_exe"]:
                exe = Path(values["idea_exe"])
                if exe.is_file():
                    try:
                        subprocess.Popen([str(exe), "/b", result["script"]])
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

    # ---------------- assistant ----------------
    def setup_opencode(self) -> None:
        self.message(self.t("setup_wait"))
        try:
            exe = install_opencode()
            self.message(self.t("setup_done"))
            if self.assistant_open:
                self._build_assistant(self.assistant_holder)
            self.message(str(exe))
        except Exception as exc:
            messagebox.showerror(self.t("setup_title"), self.t("setup_failed", exc=exc))

    def _api(self, method: str, path: str, body: dict | None = None, timeout: int = 30) -> dict:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {
            "Accept": "application/json",
            "Authorization": "Basic "
            + base64.b64encode(f"opencode:{self.ai_password}".encode()).decode(),
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self.ai_base_url + path, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
        return json.loads(raw.decode("utf-8")) if raw else {}

    def start_assistant(self) -> None:
        values = self.current_values()
        self.store_settings()
        key = values.get("opencode_key", "")
        folder = Path(values["folder"])
        if not key:
            messagebox.showwarning(self.t("need_api_key_title"), self.t("need_api_key_body"))
            return
        if not folder.is_dir():
            messagebox.showwarning(self.t("need_folder_title"), self.t("need_folder_body"))
            return

        exe = find_opencode()
        if not exe:
            messagebox.showwarning(self.t("setup_title"), self.t("status_not_installed"))
            return

        self.message(self.t("assistant_starting"))
        self.stop_assistant(silent=True)

        model = values.get("opencode_model") or DEFAULT_MODEL
        write_idea_config(folder, model)
        write_idea_instructions(folder, Path(sys.executable), self.lang)
        self.message(self.t("create_idea_config"))

        self.ai_password = uuid.uuid4().hex
        port = free_port()
        self.ai_base_url = f"http://127.0.0.1:{port}"
        env = os.environ.copy()
        env["OPENROUTER_API_KEY"] = key
        env["OPENCODE_PASSWORD"] = self.ai_password
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            self.ai_proc = subprocess.Popen(
                [str(exe), "serve", "--hostname", "127.0.0.1", "--port", str(port)],
                cwd=str(folder),
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )
        except Exception as exc:
            self.ai_proc = None
            messagebox.showerror(self.t("error_title"), str(exc))
            return

        deadline = time.time() + 45
        ready = False
        while time.time() < deadline:
            if self.ai_proc.poll() is not None:
                break
            try:
                self._api("GET", "/api/info", timeout=3)
                ready = True
                break
            except Exception:
                time.sleep(0.5)
        if not ready:
            self.stop_assistant(silent=True)
            messagebox.showerror(self.t("error_title"), self.t("assistant_error", exc="server did not start"))
            return

        try:
            created = self._api(
                "POST",
                "/api/session",
                {"location": {"directory": str(folder.resolve())}},
            )
            self.ai_session_id = (created.get("data") or {}).get("id")
        except Exception as exc:
            self.stop_assistant(silent=True)
            messagebox.showerror(self.t("error_title"), self.t("assistant_error", exc=exc))
            return

        self.chat_history.append(("assistant", self.t("assistant_welcome")))
        if self.assistant_open:
            self._build_assistant(self.assistant_holder)
        self.message(self.t("assistant_ready"))

    def stop_assistant(self, silent: bool = False) -> None:
        if self.ai_proc and self.ai_proc.poll() is None:
            self.ai_proc.terminate()
            try:
                self.ai_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ai_proc.kill()
        self.ai_proc = None
        self.ai_session_id = None
        self.ai_base_url = ""
        self.ai_password = ""
        if not silent:
            self.message(self.t("assistant_stopped"))
        if self.assistant_open:
            self._build_assistant(self.assistant_holder)

    def send_prompt(self) -> None:
        text = self.prompt_var.get().strip()
        if not text or not self.ai_session_id or self.ai_busy:
            return
        self.prompt_var.set("")
        self.chat_history.append(("user", text))
        self._append_chat("user", text)
        self.ai_busy = True
        self.send_btn.configure(state="disabled")
        threading.Thread(target=self._chat_worker, args=(text,), daemon=True).start()

    def _chat_worker(self, text: str) -> None:
        try:
            self._api(
                "POST",
                f"/api/session/{self.ai_session_id}/prompt",
                {"text": text},
                timeout=30,
            )
            self.ai_queue.put(("status", self.t("assistant_thinking")))

            seen_text = ""
            last_id = None
            deadline = time.time() + 300
            while time.time() < deadline:
                try:
                    pending = self._api("GET", "/api/permission/request", timeout=5)
                    for req in (pending.get("data") or []):
                        req_id = req.get("id")
                        sid = req.get("sessionID")
                        if req_id and sid:
                            try:
                                self._api(
                                    "POST",
                                    f"/api/session/{sid}/permission/{req_id}/reply",
                                    {"decision": "once"},
                                    timeout=5,
                                )
                            except Exception:
                                pass
                except Exception:
                    pass

                messages = self._api(
                    "GET", f"/api/session/{self.ai_session_id}/message", timeout=10
                )
                data = messages.get("data") or []
                assistant = [m for m in data if m.get("type") == "assistant"]
                if assistant:
                    msg = assistant[-1]
                    parts = []
                    for part in msg.get("content") or []:
                        if part.get("type") == "text" and part.get("text"):
                            parts.append(str(part["text"]))
                    current = "\n".join(parts).strip()
                    if current and current != seen_text:
                        seen_text = current
                        last_id = msg.get("id")
                        self.ai_queue.put(("replace", current))
                    if msg.get("finish") and last_id == msg.get("id"):
                        break
                time.sleep(1.2)

            if not seen_text:
                self.ai_queue.put(("assistant", "(…)"))
        except Exception as exc:
            self.ai_queue.put(("error", self.t("assistant_error", exc=exc)))
        finally:
            self.ai_queue.put(("done", ""))

    def _drain_ai_queue(self) -> None:
        try:
            while True:
                kind, text = self.ai_queue.get_nowait()
                if kind == "replace":
                    if self.chat_history and self.chat_history[-1][0] == "assistant":
                        self.chat_history[-1] = ("assistant", text)
                    else:
                        self.chat_history.append(("assistant", text))
                    if self.assistant_open:
                        self._build_assistant(self.assistant_holder)
                elif kind == "assistant":
                    self.chat_history.append(("assistant", text))
                    if self.assistant_open:
                        self._build_assistant(self.assistant_holder)
                elif kind == "status":
                    self.message(text)
                elif kind == "error":
                    self.message(text)
                    messagebox.showerror(self.t("error_title"), text)
                elif kind == "done":
                    self.ai_busy = False
                    if hasattr(self, "send_btn"):
                        self.send_btn.configure(state="normal")
        except queue.Empty:
            pass
        self.after(150, self._drain_ai_queue)

    def on_close(self) -> None:
        self.store_settings()
        self.stop_assistant(silent=True)
        self.destroy()


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        raise SystemExit(cli_main(sys.argv[2:]))
    App().mainloop()


if __name__ == "__main__":
    main()
