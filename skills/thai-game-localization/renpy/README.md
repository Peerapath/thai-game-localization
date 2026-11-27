# Ren'Py reference implementation

Code from a shipped Thai mod for a Ren'Py 8.3 visual novel (Bewitching Sinners, ~22,000 lines).
It is a starting point to adapt, not a drop-in tool: game names, labels, characters and
`EXTRA_STRINGS` are specific to that game. PLAYBOOK section 7.6 explains why each piece exists.

| File | What it is |
|---|---|
| `pipe.py` | Pipeline: `extract` (Ren'Py template + source scan + .rpa), `exportall N`, `check`, `apply`, `build` (ZWSP at build time), `package` (release zip) |
| `thai_setup.rpy` | Goes in `game/tl/thai/`: FontGroup per font, `config.font_name_map` for hard-coded fonts, speaker-name switch, `Message` class patch |
| `thaimod_language_button.rpy` | Goes in `game/` (not `tl/`): the language button, so it exists before `tl/thai` is loaded |
| `thaimod_install.py` | Installer run with the game's bundled Python; rebuilds `tr_strings.rpy` from the player's own files |
| `test_harness.rpy` | Temporary `game/zz_thai_spike.rpy`: env-var gated screenshots, label overrides, save/restart checks |
| `win_capture.ps1` | Windows: capture the game window and send clicks (Ren'Py needs two clicks: focus, then click) |

Generate the Ren'Py template with the game's own Python, then move it out of `game/tl`:

```
lib/py3-windows-x86_64/python.exe <Game>.py . translate thai
```
