# Bewitching Sinners - Thai translation mod installer.
#
# Runs with the game's own bundled Python (no separate Python install needed).
#   install:    thaimod_install.py install   [GAME_DIR]
#   uninstall:  thaimod_install.py uninstall [GAME_DIR]
#
# What it does:
#   * copies the Thai translation (data/tl_thai) to GAME_DIR/game/tl/thai
#   * builds GAME_DIR/game/tl/thai/tr_strings.rpy from the PLAYER'S OWN game files:
#     the mod ships only Thai text keyed by a hash of each English string, and the English
#     side is read from the local game, so the mod does not redistribute the game's text.
#   * never modifies any original game file. Uninstall = remove game/tl/thai.
# Console messages are English on purpose (the Windows console draws Thai badly).

import sys, os, re, json, hashlib, shutil, zlib, pickle, io

BS = chr(92)
NL = chr(10)
HERE = os.path.dirname(os.path.abspath(__file__))
MARKER = "thaimod.txt"
# Must live in game/ itself: the game only loads tl/thai after Thai is selected.
BUTTON = "thaimod_language_button.rpy"
BUTTON_TAG = "# Bewitching Sinners Thai mod - language button."


def die(msg):
    print("ERROR: " + msg)
    sys.exit(1)


def find_game_dir(argv):
    if len(argv) > 2:
        return os.path.abspath(argv[2])
    # data/ -> mod folder -> game folder
    return os.path.dirname(os.path.dirname(HERE))


def check_game_dir(gd):
    if not (os.path.isdir(os.path.join(gd, "game")) and os.path.isdir(os.path.join(gd, "renpy"))):
        die("This does not look like the Bewitching Sinners folder: %s" % gd + NL +
            "Put the ThaiMod folder inside the game folder (next to BewitchingSinners.exe) and run it again.")


# ------------------------------------------------------------------ string literals

def unescape(lit):
    out = []
    i = 0
    while i < len(lit):
        c = lit[i]
        if c == BS and i + 1 < len(lit):
            n = lit[i + 1]
            out.append(NL if n == "n" else n)
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def quote(value):
    return value.replace(BS, BS + BS).replace('"', BS + '"').replace(NL, BS + "n")


def key(value):
    return hashlib.md5(value.encode("utf-8")).hexdigest()


LIT = re.compile('"((?:[^"' + BS + BS + NL + ']|' + BS + BS + '.)*)"' + "|" +
                 "'((?:[^'" + BS + BS + NL + "]|" + BS + BS + ".)*)'")


def literals(text):
    for m in LIT.finditer(text):
        s = m.group(1) if m.group(1) is not None else m.group(2)
        if s:
            yield unescape(s)


def read_text(data):
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return ""


def rpa_scripts(path):
    """Yield (name, text) for .rpy/.rpym files inside a Ren'Py RPA-3.0 archive."""
    with open(path, "rb") as f:
        header = f.readline().split()
        if not header or header[0] != b"RPA-3.0":
            return
        offset = int(header[1], 16)
        k = int(header[2], 16)
        f.seek(offset)
        index = pickle.loads(zlib.decompress(f.read()), encoding="bytes")
        for name, parts in index.items():
            if isinstance(name, bytes):
                name = name.decode("utf-8", "replace")
            if not (name.endswith(".rpy") or name.endswith(".rpym")):
                continue
            p = parts[0]
            o, l = p[0] ^ k, p[1] ^ k
            prefix = p[2] if len(p) > 2 else b""
            if isinstance(prefix, str):
                prefix = prefix.encode("latin-1")
            f.seek(o)
            yield name, read_text(prefix + f.read(l - len(prefix)))


def local_sources(gd):
    game = os.path.join(gd, "game")
    thai = os.path.normcase(os.path.join(game, "tl", "thai"))
    for root, dirs, files in os.walk(game):
        if os.path.normcase(root).startswith(thai):
            continue
        for fn in files:
            p = os.path.join(root, fn)
            if fn.endswith(".rpy") or fn.endswith(".rpym"):
                with open(p, "rb") as f:
                    yield p, read_text(f.read())
            elif fn.endswith(".rpa"):
                try:
                    for name, text in rpa_scripts(p):
                        yield p + ":" + name, text
                except Exception as e:
                    print("  warning: could not read archive %s (%s)" % (fn, e))
    common = os.path.join(gd, "renpy", "common")
    for fn in sorted(os.listdir(common)):
        if fn.endswith(".rpy") or fn.endswith(".rpym"):
            with open(os.path.join(common, fn), "rb") as f:
                yield fn, read_text(f.read())


# ------------------------------------------------------------------ install / uninstall

def remove_button(gd):
    p = os.path.join(gd, "game", BUTTON)
    if os.path.exists(p):
        with io.open(p, encoding="utf-8") as f:
            if not f.readline().startswith(BUTTON_TAG):
                die("%s exists but was not created by this mod. Not touching it." % p)
        os.remove(p)
    for extra in (p + "c",):
        if os.path.exists(extra):
            os.remove(extra)


def remove_ours(target):
    if not os.path.exists(target):
        return
    if not os.path.exists(os.path.join(target, MARKER)):
        die("%s exists but was not created by this mod. Not touching it." % target)
    shutil.rmtree(target)


def install(gd):
    check_game_dir(gd)
    src = os.path.join(HERE, "tl_thai")
    table = json.load(io.open(os.path.join(HERE, "strings_th.json"), encoding="utf-8"))
    target = os.path.join(gd, "game", "tl", "thai")
    tmp = target + ".installing"

    print("Game folder: " + gd)
    print("Reading the game's own text to match UI strings...")
    found = {}
    files = 0
    for name, text in local_sources(gd):
        files += 1
        for value in literals(text):
            if value in found:
                continue
            k = key(value)
            if k in table:
                found[value] = table[k]
    matched_keys = set(key(v) for v in found)
    print("  scanned %d script files, matched %d of %d UI strings" % (files, len(matched_keys), len(table)))

    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    shutil.copytree(src, tmp)
    lines = ["# Thai UI strings - generated on this computer by the Thai mod installer.",
             "# The English (old) side was read from this copy of the game.", "",
             "translate thai strings:", ""]
    for value in sorted(found):
        lines.append('    old "%s"' % quote(value))
        lines.append('    new "%s"' % found[value])
        lines.append("")
    with io.open(os.path.join(tmp, "tr_strings.rpy"), "w", encoding="utf-8") as f:
        f.write(NL.join(lines))
    with io.open(os.path.join(tmp, MARKER), "w", encoding="utf-8") as f:
        f.write("Installed by the Bewitching Sinners Thai mod. Delete this folder to uninstall." + NL)

    remove_ours(target)
    os.rename(tmp, target)
    remove_button(gd)
    shutil.copy(os.path.join(HERE, BUTTON), os.path.join(gd, "game", BUTTON))
    print("")
    print("Installed to: " + target)
    print("Start the game, then Setting > Language > (the Thai button under Chinese).")
    missing = len(table) - len(matched_keys)
    if missing:
        print("Note: %d UI strings were not found in this game version and stay in English." % missing)


def uninstall(gd):
    check_game_dir(gd)
    target = os.path.join(gd, "game", "tl", "thai")
    button = os.path.join(gd, "game", BUTTON)
    if not os.path.exists(target) and not os.path.exists(button):
        print("The Thai mod is not installed. Nothing to do.")
        return
    remove_ours(target)
    remove_button(gd)
    print("Removed: " + target)
    print("Removed: " + button)
    print("No original game file was changed, so the game is back to normal.")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("install", "uninstall"):
        die("usage: thaimod_install.py install|uninstall [GAME_DIR]")
    gd = find_game_dir(sys.argv)
    try:
        if sys.argv[1] == "install":
            install(gd)
        else:
            uninstall(gd)
    except SystemExit:
        raise
    except Exception as e:
        die("%s: %s" % (type(e).__name__, e))
