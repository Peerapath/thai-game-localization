---
name: thai-game-localization
description: Use when translating or localizing a game, mod, visual novel or app UI into Thai, or making a Thai patch/translation mod (Ren'Py, Unity/TextMeshPro, GameMaker or any engine); when Thai text renders wrong (tone marks missing, overlapping or clipped, tofu boxes, no line wrapping, text overflowing boxes); when choosing Thai fonts, Thai word segmentation, PyThaiNLP or ZWSP; when shipping or releasing a translation mod (installer, Nexus Mods quarantine, not redistributing the game's text); or before starting any Thai translation work so the rendering check happens first.
---

# Thai game localization

Knowledge from three shipped Thai translation mods: GameMaker (2,348 strings), Unity 6 / TMP
(1,575 strings) and Ren'Py 8 (22,042 strings, all released or prepared for Nexus Mods).
Full detail is in [PLAYBOOK.md](PLAYBOOK.md), written in Thai. Ren'Py reference code is in
[renpy/](renpy/README.md).

## Read this first

**Prove the rendering works before translating a single string.**

Thai stacks up to three marks on one consonant. Many engines draw glyph by glyph without
OpenType shaping, so they render only ONE zero-width mark per base letter: the tone mark after
an upper vowel disappears or lands on the vowel. Put this string in the real UI on day one:

```
ที่  ปี่  ฝี  ฟี  เป็น  กั๊ก  ญี่ปุ่น  เพื่อ  สิ้น  ที่นี่  ผู้  ปู่  ฟู่
```

If any of it renders wrong, the engine is not shaping and the font strategy changes. Finding out
after the translation is done means redoing work.

| Engine | Shaping | Font strategy |
|---|---|---|
| GameMaker | none | Bake marks into PUA glyphs, merge Thai into the game font (PLAYBOOK 1.3, 3) |
| Unity 6 TMP | none | Bake PUA into the game's own font, patch every font copy (PLAYBOOK 7.5) |
| Ren'Py 8 (Python 3) | HarfBuzz by default | No baking. `FontGroup` routes U+0E00–0E7F to a Thai font (PLAYBOOK 7.6) |

## The things that actually bite

1. **No shaping** → bake HarfBuzz-shaped marks into Private Use Area glyphs. (PLAYBOOK 1.3)
2. **Clipped tone marks** → widen OS/2 `usWinAscent`/`usWinDescent`; marks reach ~1.03 em. (1.4)
3. **No line wrapping** → insert U+200B between words with PyThaiNLP **at build time only**.
   Never before `? ! . ,` or `ๆ` (use NBSP before ๆ), and add every glossary name to the
   tokenizer dictionary or names get split across lines. (PLAYBOOK 2)
4. **Font licences** → merging OFL glyphs makes the result OFL, forces a rename, Apache bases
   must say they were modified. Read the `name` table before shipping. (3.2)
5. **Broken variables and markup** → validate every batch before writing, fail the whole
   batch on one bad row. (4.3)
6. **PUA collisions** → scan the cmap of every font in the game before picking a range. (7.5)
7. **Fonts hard-coded in screens** (chat, shop, the engine's own error/settings screens) show
   tofu even after the main UI works. Search every `font` reference, not only the GUI config.
8. **Testing only the state you developed in.** A language that loads lazily works on your
   machine (already set to Thai) and fails for a fresh player who starts in English. Test a
   fresh English start, switching language, return to main menu, save/load. (7.6)

## Ren'Py games

- Generate the exact template with the game's own Python, no SDK needed:
  `lib/py3-windows-x86_64/python.exe <Game>.py . translate thai` — then move it out of `game/tl`.
- The generated `strings` only cover `_()`. Also scan `Character("Name")`, dynamic speaker
  variables, custom chat functions, menu text, and scripts inside `.rpa` archives.
- If the game sets `config.defer_tl_scripts = True`, `tl/thai` loads only when Thai is active:
  the language button must live in `game/`, and names defined in `tl/thai` init code vanish on
  return to the main menu. Keep state in `config`, class attributes or `translate python`.
- Fonts hard-coded in screens: `config.font_name_map["X.ttf"] = FontGroup(...)`, building the
  group **before** mapping the name (FontGroup refuses mapped names). Include `DejaVuSans.ttf`.
- Text assembled at runtime (`"%s. %s"`, typewriter slices) never matches the string table:
  translate where the object is built (patch the class), never by rebinding a store function.
- Code like `if _preferences.language == None: <English> else: <Chinese>` sends other languages
  the Chinese text: add string entries keyed by those Chinese literals; use `[var!t]` for
  variables that hold pronouns or words.
- One English string with two meanings (a name and an item): switch the speaker's `name` in
  `config.change_language_callbacks`.

## Process rules that paid off

- **Only the strongest model writes Thai.** A cheap model once produced a Lao letter and a
  doubled tone mark that no validator caught. Cheap models do mechanical work only.
- **The glossary decides terminology.** With many parallel translators, give every one the
  same STYLE.md (voices, pronouns, glossary), have them report new terms, then count spelling
  variants across all output and normalize before building.
- **Work survives on disk, not in the orchestrator.** Write each batch to its own file and
  validate it; after a crash or usage limit, re-run only the batches whose file is missing or
  fails the check.
- **Never ship the game's own text.** Ship Thai keyed by a hash of the English and let the
  installer read the English from the player's files. Scan the release for leaked source text.
- **Installers:** if the game bundles an interpreter (Ren'Py ships Python), run the installer
  with it: no user setup, no PowerShell. Nexus still quarantines `.bat`; answer with a file list
  plus SHA-256 and every path written. Check the game has a Nexus page before you plan the release.

## Order of work

```
1. rendering spike      <-- before any translation
2. confirm the text channel (language slot, file format)
3. glossary + style guide (voices, pronouns)
4. pipeline + validator
5. translate in batches
6. build + test in the real game (fresh English start too)
7. package, leak-scan, release
```

## Reference code

- `renpy/` — full Ren'Py pipeline, setup file, language button, installer, test harness.
- The GameMaker and Unity tools named in PLAYBOOK (`thaishape.py`, `fontmerge.py`,
  `segment.py`, `batch.py`, `gamefiles.py`) are described there but not included.
