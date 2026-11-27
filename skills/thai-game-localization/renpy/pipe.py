"""Thai localization pipeline for a Ren'Py game (reference implementation from the
Bewitching Sinners Thai mod - adapt paths, EXTRA_STRINGS and the source scan to your game).

Layout: <game>/thai-mod/{tools/pipe.py, template/, src/, data/, batches/, done/, STYLE.md}
  template/ = output of `<game python> <Game>.py . translate thai` (moved out of game/tl)
  src/      = the game's .rpy files, including those extracted from .rpa archives

  python pipe.py extract            # build data/units.json from template + source scan
  python pipe.py export N [size]    # write batches/NNN.txt of untranslated units
  python pipe.py apply FILE...      # validate done files fully, then merge into data/th.json
  python pipe.py build              # write game/tl/thai/*.rpy (ZWSP inserted here only)
  python pipe.py stats

Backslashes are produced with chr(92) on purpose: shell/tool layers eat them.
"""
import sys, os, re, json, glob, hashlib, collections

B = chr(92)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.dirname(ROOT) + '/game'
TEMPLATE = ROOT + '/template'
SRC = ROOT + '/src'          # extracted game scripts (local only, never shipped)
DATA = ROOT + '/data'
UNITS = DATA + '/units.json'
TH = DATA + '/th.json'
OUT = GAME + '/tl/thai'
ZW = chr(0x200b)

LIT = '"((?:[^"' + B + B + chr(10) + ']|' + B + B + '.)*)"'

# escape tokens used in batch files (so no backslash ever passes through an editor)
TOK = [(B + 'n', '<br>'), (B + '"', '<q>'), (B + B, '<bs>')]


def to_tok(s):
    out = []
    i = 0
    while i < len(s):
        if s[i] == B and i + 1 < len(s):
            pair = s[i:i + 2]
            for a, t in TOK:
                if pair == a:
                    out.append(t)
                    break
            else:
                out.append(pair)
            i += 2
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)


def from_tok(s):
    for a, t in TOK:
        s = s.replace(t, a)
    return s


def rd(p):
    return open(p, encoding='utf-8-sig').read()


def skey(old):
    return 's_' + hashlib.md5(old.encode('utf-8')).hexdigest()[:10]


# ---------------------------------------------------------------- extract

def parse_template():
    """Return (say_units, string_olds) from Ren'Py-generated template files."""
    say, strs = [], []
    for f in sorted(glob.glob(TEMPLATE + '/*.rpy')):
        name = os.path.basename(f)
        text = rd(f)
        blocks = re.split(r'(?m)^(?=translate thai )', text)
        for b in blocks:
            if not b.startswith('translate thai '):
                continue
            head = b.split(chr(10), 1)[0]
            ident = head[len('translate thai '):].rstrip(':').strip()
            if ident == 'strings':
                for m in re.finditer(r'(?m)^    # (\S+):(\d+)' + chr(10) + '    old ' + LIT, b):
                    strs.append((name, m.group(3), int(m.group(2))))
                continue
            lines = [l for l in b.split(chr(10))[1:] if l.strip() and not l.strip().startswith('#')]
            assert len(lines) == 1, (name, ident, lines)
            stmt = lines[0].strip()
            m = re.search(LIT, stmt)
            pre = stmt[:m.start()].strip()
            who = pre.split()[0] if pre else '-'
            say.append({'k': ident, 'kind': 'say', 'f': name, 'who': who, 'pre': pre, 'en': m.group(1)})
    return say, strs


def scan_source_strings():
    """Strings shown via screens / messenger that the generator does not list."""
    found = collections.OrderedDict()
    pats = [r'\bmsg\s*\(\s*' + LIT, r"'name'\s*:\s*" + LIT, r'_\(\s*' + LIT,
            r'\bNPC\s*=\s*' + LIT, r"Character\(\s*'([^'\[]+)'", r'Character\(\s*"([^"\[]+)"']
    for f in sorted(glob.glob(SRC + '/**/*.rpy', recursive=True)):
        rel = os.path.relpath(f, SRC).replace(B, '/')
        s = rd(f)
        for p in pats:
            for m in re.finditer(p, s):
                v = m.group(1)
                if not re.search('[A-Za-z]', v) or re.search('[' + chr(0x4e00) + '-' + chr(0x9fff) + ']', v):
                    continue
                found.setdefault(v, rel)
    # strings the Chinese translators found and that still exist in the source
    allsrc = ''.join(rd(f) for f in glob.glob(SRC + '/**/*.rpy', recursive=True))
    for f in glob.glob(GAME + '/tl/chinese/**/*.rpy', recursive=True):
        for m in re.finditer(r'(?m)^    old ' + LIT + '$', rd(f)):
            v = m.group(1)
            if '"' + v + '"' in allsrc:
                found.setdefault(v, 'chinese:' + os.path.basename(f))
    return found


def scan_language_branches():
    """Pair English and Chinese messenger choice names in `if _preferences.language == None` blocks."""
    alias = {}
    for f in glob.glob(SRC + '/*.rpy'):
        lines = rd(f).split(chr(10))
        for i, l in enumerate(lines):
            if '_preferences.language == None' not in l:
                continue
            en = re.findall(r"'name'\s*:\s*" + LIT, lines[i + 1])
            if not en or not lines[i + 2].strip().startswith('else'):
                continue
            zh = re.findall(r"'name'\s*:\s*" + LIT, lines[i + 3])
            if len(en) == len(zh):
                for a, b in zip(en, zh):
                    alias.setdefault(a, set()).add(b)
    return alias


def extract():
    say, strs = parse_template()
    seen = collections.OrderedDict()
    for name, old, line in strs:
        seen.setdefault(old, name)
    for v, where in scan_source_strings().items():
        seen.setdefault(v, where)
    alias = scan_language_branches()
    units = [u for u in say if u['f'] != '00auto-highlight.rpy']
    for old, where in seen.items():
        u = {'k': skey(old), 'kind': 'str', 'f': where, 'who': '', 'en': old}
        if old in alias:
            u['alias'] = sorted(alias[old])
        units.append(u)
    keys = [u['k'] for u in units]
    assert len(keys) == len(set(keys)), 'duplicate keys'
    os.makedirs(DATA, exist_ok=True)
    json.dump(units, open(UNITS, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('say', len(say), 'strings', len(units) - len(say), 'alias', len(alias))


# ---------------------------------------------------------------- validation

TAG = re.compile(r'\{[^{}]*\}')
VAR = re.compile(r'\[[^\[\]]*\]')
PRON = {'kamu', 'dia', 'dia2', 'kk'}
THAI_MARK = '[' + chr(0x0e31) + chr(0x0e34) + '-' + chr(0x0e3a) + chr(0x0e47) + '-' + chr(0x0e4e) + ']'
TONE = '[' + chr(0x0e48) + '-' + chr(0x0e4b) + ']'


def var_name(v):
    return v[1:-1].split('!')[0].split('.')[0].split('[')[0]


def check(en, th):
    errs = []
    if not th.strip():
        errs.append('empty')
    if ZW in th or chr(0xfeff) in th:
        errs.append('zero-width char')
    if re.search('[' + chr(0x0e80) + '-' + chr(0x0eff) + ']', th):
        errs.append('Lao character')
    if re.search(TONE + THAI_MARK + '*' + TONE, th) or re.search(THAI_MARK + '{3,}', th):
        errs.append('stacked/doubled marks')
    if re.search('[' + chr(0x0e50) + '-' + chr(0x0e59) + ']', th):
        errs.append('Thai digits')
    if re.search('[' + chr(0x4e00) + '-' + chr(0x9fff) + ']', th):
        errs.append('CJK in Thai')
    if chr(0xfffd) in th:
        errs.append('replacement char U+FFFD (write a real dash/ellipsis instead)')
    if re.search('[' + chr(0x0e01) + '-' + chr(0x0e45) + chr(0x0e47) + '-' + chr(0x0e4e) + ']' + chr(0x0e46), th):
        errs.append('mai yamok needs a space before it')
    if '"' in th.replace(B + '"', ''):
        errs.append('unescaped double quote')
    if th.count(B) != th.count(B + 'n') + th.count(B + '"') + 2 * th.count(B + B):
        errs.append('stray backslash')
    # tags: exact multiset
    te = collections.Counter(TAG.findall(en))
    tt = collections.Counter(TAG.findall(th))
    if te != tt:
        errs.append('tags %s != %s' % (dict(te), dict(tt)))
    # brace balance outside tags
    if th.count('{') != th.count('}') or th.count('[') != th.count(']'):
        errs.append('unbalanced brackets')
    # vars: non-pronoun exact; pronoun subset
    ve = [v for v in VAR.findall(en)]
    vt = [v for v in VAR.findall(th)]
    ne = collections.Counter(v for v in ve if var_name(v) not in PRON)
    nt = collections.Counter(v for v in vt if var_name(v) not in PRON)
    if ne != nt:
        errs.append('vars %s != %s' % (dict(ne), dict(nt)))
    pe = {var_name(v) for v in ve if var_name(v) in PRON}
    for v in vt:
        n = var_name(v)
        if n in PRON:
            if n == 'kk' and 'kk' not in pe:
                errs.append('kk not in source')
            if n != 'kk' and not (pe - {'kk'}):
                errs.append('pronoun var not in source')
            if v not in ('[kamu!t]', '[kk!t]'):
                errs.append('use [kamu!t]/[kk!t], got ' + v)
    if en.count(B + 'n') != th.count(B + 'n'):
        errs.append('newline count')
    return errs


# ---------------------------------------------------------------- batches

def load_units():
    return json.load(open(UNITS, encoding='utf-8'))


def load_th():
    return json.load(open(TH, encoding='utf-8')) if os.path.exists(TH) else {}


def export(n, size=150, start=None):
    units = load_units()
    th = load_th()
    todo = [u for u in units if u['k'] not in th]
    if start:
        idx = next(i for i, u in enumerate(todo) if u['k'] == start)
        todo = todo[idx:]
    batch = todo[:size]
    os.makedirs(ROOT + '/batches', exist_ok=True)
    p = ROOT + '/batches/%03d.txt' % n
    with open(p, 'w', encoding='utf-8') as f:
        for u in batch:
            who = (u['pre'] or 'narr') if u['kind'] == 'say' else '#str'
            f.write('%s|%s|%s%s' % (u['k'], who, to_tok(u['en']), chr(10)))
    print(p, len(batch), 'remaining', len(todo) - len(batch), 'first file', batch[0]['f'] if batch else '-')


def parse_done(p):
    out = collections.OrderedDict()
    for i, line in enumerate(rd(p).split(chr(10)), 1):
        if not line.strip():
            continue
        if '|' not in line:
            raise SystemExit('%s:%d no separator' % (p, i))
        k, t = line.split('|', 1)
        k = k.strip()
        if k in out:
            raise SystemExit('%s:%d duplicate key %s' % (p, i, k))
        out[k] = from_tok(t.strip())
    return out


def check_cmd(paths):
    """Validate done files against their batch files. Writes nothing."""
    units = {u['k']: u for u in load_units()}
    bad = []
    for p in paths:
        bp = ROOT + '/batches/' + os.path.basename(p)
        want = [l.split('|', 1)[0] for l in rd(bp).split(chr(10)) if l.strip()] if os.path.exists(bp) else []
        got = parse_done(p)
        missing = [k for k in want if k not in got]
        if missing:
            bad.append('%s: missing %d keys: %s' % (os.path.basename(p), len(missing), ' '.join(missing[:20])))
        for k, t in got.items():
            if k not in units:
                bad.append('%s: unknown key %s' % (os.path.basename(p), k))
                continue
            e = check(units[k]['en'], t)
            if e:
                bad.append('%s: %s: %s | %s' % (os.path.basename(p), k, '; '.join(e), to_tok(t)))
    print(chr(10).join(bad) if bad else 'OK')
    raise SystemExit(1 if bad else 0)


def apply(paths):
    units = {u['k']: u for u in load_units()}
    th = load_th()
    new = collections.OrderedDict()
    bad = []
    for p in paths:
        for k, t in parse_done(p).items():
            if k not in units:
                bad.append('%s: unknown key %s' % (p, k))
                continue
            e = check(units[k]['en'], t)
            if e:
                bad.append('%s: %s: %s | %s' % (os.path.basename(p), k, '; '.join(e), t))
            new[k] = t
    if bad:
        print(chr(10).join(bad))
        raise SystemExit('REJECTED: %d problems, nothing written' % len(bad))
    th.update(new)
    tmp = TH + '.tmp'
    json.dump(th, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)
    os.replace(tmp, TH)
    print('applied', len(new), 'total', len(th), '/', len(units))


# ---------------------------------------------------------------- build

_tok = None


def segment(s):
    """Insert ZWSP between Thai words; never inside tags, vars or escapes."""
    global _tok
    if _tok is None:
        from pythainlp.tokenize import word_tokenize
        from pythainlp.corpus import thai_words
        from pythainlp.util import Trie
        trie = Trie(set(thai_words()) | glossary_words())
        _tok = lambda t: word_tokenize(t, custom_dict=trie, engine='newmm', keep_whitespace=True)
    parts = re.split('(' + r'\{[^{}]*\}|\[[^\[\]]*\]|' + re.escape(B) + '.' + ')', s)
    out = []
    thai = re.compile('[' + chr(0x0e00) + '-' + chr(0x0e7f) + ']')
    no_before = set('?!.,;:)]}…”’"' + "'" + chr(0x0e46) + chr(0x0e2f))   # never break before these
    no_after = set('([{“‘"' + "'")                                     # never break after these
    for i, p in enumerate(parts):
        if i % 2 == 1 or not thai.search(p):
            out.append(p)
            continue
        words = _tok(p)
        buf = ''
        for j, w in enumerate(words):
            if j:
                prev = words[j - 1]
                if not (w.isspace() or prev.isspace() or w[0] in no_before or prev[-1] in no_after):
                    if thai.match(w[0]) or thai.match(prev[-1]):
                        buf += ZW
            buf += w
        out.append(buf)
    # keep ๆ on the same line as the word it repeats
    return ''.join(out).replace(' ' + chr(0x0e46), chr(0xa0) + chr(0x0e46))


def glossary_words():
    words = set()
    thai = re.compile('[' + chr(0x0e00) + '-' + chr(0x0e7f) + ']')
    for line in rd(ROOT + '/STYLE.md').split(chr(10)):
        if not line.startswith('|'):
            continue
        cells = line.strip('|').split('|')
        if len(cells) < 2:
            continue
        for part in re.split('[/,()“”"]', cells[-1]):
            for w in part.split():
                if thai.search(w) and re.fullmatch('[' + chr(0x0e00) + '-' + chr(0x0e7f) + ']+', w):
                    words.add(w)
    return words


EXTRA_STRINGS = [
    # pronoun variables (game stores Chinese values when language != None)
    ('她', 'เธอ'), ('她的', 'เธอ'), ('他', 'เขา'), ('他的', 'เขา'), ('伊', 'เขา'), ('伊的', 'เขา'),
    ('she', 'เธอ'), ('her', 'เธอ'), ('hers', 'เธอ'), ('he', 'เขา'), ('his', 'เขา'), ('him', 'เขา'),
    ('they', 'เขา'), ('their', 'เขา'), ('them', 'เขา'),
    ('姐姐', 'พี่สาว'), ('哥哥', 'พี่ชาย'), ('双胞胎', 'พี่'), ('sister', 'พี่สาว'), ('brother', 'พี่ชาย'),
]


def q(s):
    return '"' + s + '"'


def build():
    units = load_units()
    th = load_th()
    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(OUT + '/*.rpy') + glob.glob(OUT + '/*.rpyc'):
        if os.path.basename(f).startswith('tr_'):
            os.remove(f)
    byfile = collections.OrderedDict()
    strings = []
    for u in units:
        if u['k'] not in th:
            continue
        if u['kind'] == 'say':
            byfile.setdefault(u['f'], []).append(u)
        else:
            strings.append(u)
    NL = chr(10)
    n = 0
    for name, us in byfile.items():
        lines = ['# Thai translation - generated by thai-mod/tools/pipe.py', '']
        for u in us:
            t = segment(th[u['k']])
            stmt = (u['pre'] + ' ' if u['pre'] else '') + q(t)
            lines += ['translate thai %s:' % u['k'], '    ' + stmt, '']
            n += 1
        open(OUT + '/tr_' + name, 'w', encoding='utf-8').write(NL.join(lines))
    olds = set()
    lines = ['# Thai translation - generated by thai-mod/tools/pipe.py', '', 'translate thai strings:', '']
    for u in strings:
        t = segment(th[u['k']])
        for old in [u['en']] + u.get('alias', []):
            if old in olds:
                continue
            olds.add(old)
            lines += ['    old ' + q(old), '    new ' + q(t), '']
    for old, t in EXTRA_STRINGS:
        if old not in olds:
            olds.add(old)
            lines += ['    old ' + q(old), '    new ' + q(t), '']
    open(OUT + '/tr_strings.rpy', 'w', encoding='utf-8').write(NL.join(lines))
    print('built say', n, 'strings', len(olds))


def unescape(lit):
    out, i = [], 0
    while i < len(lit):
        if lit[i] == B and i + 1 < len(lit):
            out.append(chr(10) if lit[i + 1] == 'n' else lit[i + 1])
            i += 2
        else:
            out.append(lit[i])
            i += 1
    return ''.join(out)


def vkey(value):
    return hashlib.md5(value.encode('utf-8')).hexdigest()


def package(version):
    """Release folder + zip for Nexus. Ships no English game text: the installer rebuilds
    tr_strings.rpy from the player's own files (keys = md5 of each English string)."""
    import shutil, zipfile
    build()
    units = load_units()
    th = load_th()
    name = 'BewitchingSinners-ThaiMod'
    rel = ROOT + '/release'
    out = rel + '/' + name
    if os.path.exists(out):
        shutil.rmtree(out)
    data = out + '/data'
    tl = data + '/tl_thai'
    os.makedirs(tl + '/fonts')
    for f in glob.glob(OUT + '/*.rpy'):
        if os.path.basename(f) != 'tr_strings.rpy':
            shutil.copy(f, tl)
    for f in glob.glob(OUT + '/fonts/*'):
        shutil.copy(f, tl + '/fonts')
    table = {}
    for u in units:
        if u['kind'] != 'str' or u['k'] not in th:
            continue
        t = segment(th[u['k']])
        for old in [u['en']] + u.get('alias', []):
            table.setdefault(vkey(unescape(old)), t)
    for old, t in EXTRA_STRINGS:
        table.setdefault(vkey(old), t)
    json.dump(table, open(data + '/strings_th.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)
    shutil.copy(ROOT + '/release_src/data/thaimod_install.py', data)
    shutil.copy(ROOT + '/release_src/data/thaimod_language_button.rpy', data)
    for f in glob.glob(ROOT + '/release_src/*.txt'):
        shutil.copy(f, out)
    # launchers (written here so no tool layer can eat the backslashes)
    CRLF = chr(13) + chr(10)
    py_win = '%~dp0..' + B + 'lib' + B + 'py3-windows-x86_64' + B + 'python.exe'
    for action, title in (('install', 'Installing'), ('uninstall', 'Removing')):
        bat = ['@echo off', 'setlocal', 'set "PY=' + py_win + '"',
               'if not exist "%PY%" (',
               '  echo ERROR: Put the ThaiMod folder inside the Bewitching Sinners game folder, next to BewitchingSinners.exe.',
               '  pause', '  exit /b 1', ')',
               'echo ' + title + ' the Bewitching Sinners Thai mod...',
               '"%PY%" "%~dp0data' + B + 'thaimod_install.py" ' + action,
               'pause', '']
        open(out + '/' + action + '.bat', 'w', encoding='ascii', newline='').write(CRLF.join(bat))
        sh = ['#!/bin/sh', 'DIR="$(cd "$(dirname "$0")" && pwd)"', 'GAME="$(dirname "$DIR")"',
              'for PY in "$GAME/lib/py3-linux-x86_64/python" "$GAME/BewitchingSinners.app/Contents/MacOS/python"; do',
              '  if [ -x "$PY" ]; then exec "$PY" "$DIR/data/thaimod_install.py" ' + action + ' "$GAME"; fi',
              'done',
              'echo "ERROR: Put the ThaiMod folder inside the Bewitching Sinners game folder."',
              'exit 1', '']
        open(out + '/' + action + '.sh', 'w', encoding='ascii', newline='').write(chr(10).join(sh))
    zpath = rel + '/%s-v%s.zip' % (name, version)
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(out):
            for fn in files:
                p = os.path.join(root, fn)
                arc = 'ThaiMod/' + os.path.relpath(p, out).replace(B, '/')
                zi = zipfile.ZipInfo.from_file(p, arc)
                if fn.endswith('.sh'):
                    zi.external_attr = 0o100755 << 16
                with open(p, 'rb') as fh:
                    z.writestr(zi, fh.read(), zipfile.ZIP_DEFLATED)
    print('release', out, 'strings', len(table), 'zip', zpath, os.path.getsize(zpath))


def stats():
    units = load_units()
    th = load_th()
    files = collections.Counter()
    for u in units:
        files[u['f'] if u['kind'] == 'say' else 'strings'] += 1
    done = collections.Counter()
    for u in units:
        if u['k'] in th:
            done[u['f'] if u['kind'] == 'say' else 'strings'] += 1
    for f, total in files.items():
        print('%-22s %5d / %5d' % (f, done[f], total))
    print('TOTAL %d / %d' % (len(th), len(units)))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cmd = sys.argv[1]
    if cmd == 'extract':
        extract()
    elif cmd == 'export':
        export(int(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 150, sys.argv[4] if len(sys.argv) > 4 else None)
    elif cmd == 'check':
        check_cmd(sys.argv[2:])
    elif cmd == 'exportall':
        size = int(sys.argv[2])
        units = load_units()
        os.makedirs(ROOT + '/batches', exist_ok=True)
        n = 0
        for i in range(0, len(units), size):
            n += 1
            with open(ROOT + '/batches/%03d.txt' % n, 'w', encoding='utf-8') as f:
                for u in units[i:i + size]:
                    who = (u['pre'] or 'narr') if u['kind'] == 'say' else '#str'
                    f.write('%s|%s|%s%s' % (u['k'], who, to_tok(u['en']), chr(10)))
        print('batches', n)
    elif cmd == 'apply':
        apply(sys.argv[2:])
    elif cmd == 'build':
        build()
    elif cmd == 'package':
        package(sys.argv[2] if len(sys.argv) > 2 else '1.0')
    elif cmd == 'stats':
        stats()
