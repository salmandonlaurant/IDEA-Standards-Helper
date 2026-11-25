# IDEA Architecture 24 — one-click office standards

## Easiest way: the desktop app

Double-click **`Start IDEA Standards Helper.bat`** (or the built `.exe` in `dist\`).

In the app:

0. **Language** → choose **English** or **Ελληνικά** in the top-right. The whole interface changes instantly and remembers the choice.
1. **Where are your drawings?** → Browse to the project folder.
2. **How should the drawings look?** → leave the recommended values, or change them.
3. Press the green **Apply to my drawings** button.
4. Open IDEA, type `SCRIPT`, and choose the file shown in the app (there's a **Copy script path** button).

The app makes a backup first and creates everything IDEA needs. No command prompt or code editing.

Optional: expand **"let the app open IDEA for you"** and browse to `IDEA.exe` if you want the app to launch IDEA automatically.

## AI assistant inside the app (OpenCode)

Expand **"4 AI Assistant (OpenCode)"** (or **"4 Βοηθός AI (OpenCode)"** in Greek).

One-time setup:

1. Click **Set up OpenCode (one time)**. The app downloads the official Windows CLI (~130 MB) into `%LOCALAPPDATA%\IDEA Standards Helper\opencode\` — no terminal needed.
2. Paste an **OpenRouter API key** (from <https://openrouter.ai/keys>). It is saved only on that computer.
3. Click **Start assistant**. The app starts a private local OpenCode server, creates `opencode.jsonc` and an `idea-helper` skill in the drawings folder, and opens a chat.

She can then type in **Greek or English**, e.g.:

- "Apply the office standards to all drawings"
- "Τι πρέπει να αλλάξω σε αυτό το σχέδιο;"
- "Create a ventilation layer and explain how to run the script"

The assistant has full access to the selected drawings folder. It uses a hidden CLI mode in the same `.exe` (`--cli help`, `--cli report`, `--cli apply`) and reads `idea_helper_last_result.json`. Backups are still created before standard changes. She still runs the generated `.scr` with `SCRIPT` in IDEA.

Click **Stop assistant** when finished; the local server is closed.

## Files under the hood

- `app.py` — the desktop app.
- `standards.lsp` — applies the office standard inside IDEA Architecture 24 / 4MCAD.
- `make_batch.py` — generates a `.scr` file to run it on a whole folder of DWGs.
- `app_icon.ico` — the app icon (made from the supplied image).
- `build_exe.bat` — rebuilds the single-file `.exe` with the icon.

## 1. Set up the standard once (manual route)

Open `standards.lsp` in Notepad and edit the **CONFIG** section at the top:

| Section | What to change |
|---|---|
| `STD-LAYERS` | Layer names, ACI colour numbers, linetypes |
| `STD-TEXTSTYLES` | Font file (e.g. `arial.ttf`), text height, width factor |
| `STD-ARROW` | `_CLOSED`, `_OPEN`, or `_ARCHTICK` |
| `STD-DIMVARS` | Text height, arrow size, extension offsets, decimal places, lineweight |
| `STD-DIMSTYLE` | Name of the dimension style the script creates |
| `STD-CURLAYER` / `STD-CURTEXT` | What becomes current after setup |

Values are in **millimetres at 1:1** (model space). If she dimensions inside scaled viewports, change `DIMSCALE`.

## 2. Apply to the current drawing

1. In IDEA Architecture 24, type `APPLOAD` and load `standards.lsp`.
   - Tip: add it to **Startup Suite** so it loads automatically every time.
2. Type `STDSETUP` and press Enter.
3. Type `STDLIST` any time to review the configured settings.

It will:
- create or update every layer (colour + linetype),
- create or update the text styles,
- set dimension variables and save them as the named dimension style,
- make the standard layer and text style current.

> **Test on a copy of a drawing first.** Layers that already exist are updated in place; objects on them keep their layer assignment but inherit the new colour/linetype.

## 3. Apply to a whole project folder

```powershell
python make_batch.py "C:\Projects\Job123" --backup "C:\Backups\Job123"
```

Options:
- `--recursive` — include subfolders.
- `--lisp "path\to\standards.lsp"` — use a different LISP file.
- `--out "path\to\my.scr"` — choose the script filename.

Then in IDEA:
1. Type `SCRIPT`.
2. Select the generated `batch_standards.scr`.
3. Let it run — it opens each DWG, applies the standards, saves and closes it.

## Troubleshooting

| Problem | Fix |
|---|---|
| `STDSETUP` unknown command | The LISP did not load. Run `APPLOAD` again, or check the file path. |
| Linetype looks wrong | The linetype is not in the drawing — the script falls back to `CONTINUOUS`. Load the linetype file first, or use `CONTINUOUS` in the config. |
| Arrows look wrong | The arrow block was missing, so the default was used. Check the `STD-ARROW` block exists in the drawing. |
| Prompt appears during batch run | Make sure no drawing has unsaved changes before running the script. |
| IDEA-specific BIM objects do not respond | These scripts handle standard DWG entities (layers, text styles, dimensions). Native IDEA BIM objects may need IDEA's .NET API — we can add that next. |

## Next automations to build

1. Auto-dimension a selected room with the standard style.
2. Space detection + room labels + Excel room schedule.
3. Furniture layout rules engine (room use → block placement).
4. Wall-type assistant and ventilation schedule.
5. Drawing QA/QC auditor.
