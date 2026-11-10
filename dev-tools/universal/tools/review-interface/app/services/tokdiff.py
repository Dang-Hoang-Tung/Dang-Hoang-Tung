"""Strong (token-level) highlights for a diff's changed rows.

The diff has two layers. The light layer is git's own: every removed and added row keeps its red or green tint, and
rows `--color-moved` marks keep their purple one, so no changed line is ever hidden. This module is the strong layer on
top. Inside each git change block it diffs the rows' tokens, ignoring layout, to pick which tokens get the strong
highlight. Token runs moved between blocks or files lose it only when nothing about them changed: same enclosing
scope, and order-free units such as function or type declarations. Changed rows left with no strong token are quiet:
only whitespace, formatting or a pure move changed. When unsure, it highlights more, never less.
"""
import bisect
import os
import re
import time
from difflib import SequenceMatcher

MIN_EQUAL = 4  # unchanged runs this short between two edits on the same line are highlighted with them
MIN_MOVE = 5  # fewest tokens in a run that counts as moved rather than coincidentally equal
MAX_MOVE_CANDIDATES = 50
MAX_BLOCK_TOKENS = 6000  # bigger blocks skip alignment and highlight every token
FILE_SECONDS = 2.0  # past this a file falls back to highlighting each changed row whole
MOVE_SECONDS = 3.0  # past this, unmatched runs simply stay highlighted

JS_EXTS = {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"}
JSX_EXTS = {".tsx", ".jsx", ".js"}
PLAIN_LANGS = {  # extension: (string quotes, line comment)
    ".py": ("\"'", "#"), ".sh": ("\"'", "#"), ".bash": ("\"'", "#"), ".zsh": ("\"'", "#"), ".rb": ("\"'", "#"),
    ".yml": ("\"'", "#"), ".yaml": ("\"'", "#"), ".toml": ("\"'", "#"), ".mk": ("\"'", "#"), ".sql": ("\"'", "--"),
}
PLAIN_DEFAULT = ('"', None)
INDENTED = {".py", ".yml", ".yaml", ".md", ".mk"}
MAKEFILES = {"makefile", "gnumakefile"}

JS_PUNCT = (r">>>=|\.\.\.|===|!==|\*\*=|<<=|>>=|>>>|&&=|\|\|=|\?\?=|=>|==|!=|<=|>=|&&|\|\||\?\?|\?\.|\+\+|--|\+=|-=|\*=|"
            r"/=|%=|&=|\|=|\^=|\*\*|<<|>>|[{}()\[\];,<>+\-*/%&|^!~?:=.@#\\]")
JS_TOKEN = re.compile(r"(?P<ws>\s+)|(?P<lc>//[^\n]*)|(?P<bc>/\*.*?\*/)|"
                      r"(?P<str>\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*')|(?P<num>\d[\w.]*|\.\d\w*)|"
                      r"(?P<id>[A-Za-z_$\u00c0-\uffff][\w$\u00c0-\uffff]*)|(?P<p>" + JS_PUNCT + r")|(?P<other>.)", re.S)
JS_REGEX = re.compile(r"/(?:\\.|\[(?:\\.|[^\]\\\n])*\]|[^/\\\n\[])+/[a-z]*")
WORD = re.compile(r"\S+")
INDENT = re.compile(r"(?m)^([ \t]*)(\S+)")
QUOTED = {'"': r'"(?:\\.|[^"\\\n])*"', "'": r"'(?:\\.|[^'\\\n])*'"}
REGEX_AFTER = {"return", "typeof", "case", "do", "else", "in", "of", "new", "delete", "void", "throw", "yield", "await"}
NEWLINE_ENDS_AFTER = {"return", "throw", "break", "continue", "yield", "async", "++", "--"}
NEWLINE_JOINS_BEFORE = tuple("([`+-/")
CLOSERS = {"}", "]", ")", ">"}
OPENERS = {"(": ")", "[": "]", "{": "}"}
LEADING_PIPE_AFTER = {"=", ":", "(", "<", ","}
JSX_PAREN_AFTER = {"return", "=>", "=", "?", ":", ",", "(", "[", "&&", "||", "??"}
DECLARATIONS = {"function", "type", "interface", "class", "enum", "namespace", "module"}
MODIFIERS = {"export", "default", "declare", "async", "abstract", "public", "private", "protected", "static",
             "readonly", "override", "get", "set", "*"}
ORDER_FREE_BODIES = {"class", "interface", "type"}
BLOCK_AFTER = {")", "=>", "else", "try", "do", "finally"}


class _Lang:
    def __init__(self, path):
        name = os.path.basename(path).lower()
        self.ext = ".mk" if name in MAKEFILES else os.path.splitext(name)[1]
        self.js = self.ext in JS_EXTS
        self.jsx = self.ext in JSX_EXTS


# Tokenize: [(text, start, end)]. Layout is dropped, comments split into words, strings kept whole; the text is only
# compared, so it may differ from the source where two spellings mean the same (quote style).

def _template_end(src, i):
    depth, j = 0, i + 1
    while j < len(src):
        c = src[j]
        if c == "\\":
            j += 2
            continue
        if depth == 0 and c == "`":
            return j + 1
        if c == "$" and src[j + 1:j + 2] == "{":
            depth, j = depth + 1, j + 2
            continue
        if depth and c == "}":
            depth -= 1
        elif depth and c == "`":
            j = _template_end(src, j)
            continue
        j += 1
    return len(src)


def _regex_allowed(prev):
    return prev is None or prev in REGEX_AFTER or not re.match(r"[\w$)\]}\"'`]", prev[-1])


def _ends_expression(prev):
    return bool(re.match(r"[\w$)\]}\"'`]", prev[-1]))


def _newline_matters(prev, nxt):
    """A line break between two tokens that automatic semicolon insertion reads differently from a space."""
    return prev in NEWLINE_ENDS_AFTER or (nxt.startswith(NEWLINE_JOINS_BEFORE) and _ends_expression(prev))


def _string_value(text):
    return "'" + text[1:-1].replace("\\'", "'").replace('\\"', '"')


def _js_raw(src):
    out, i, prev, prev_at, broke = [], 0, None, None, False
    while i < len(src):
        m = None
        if src[i] == "`":
            tok = (src[i:_template_end(src, i)], i, _template_end(src, i))
        elif src[i] == "/" and src[i + 1:i + 2] not in ("/", "*") and _regex_allowed(prev) and JS_REGEX.match(src, i):
            r = JS_REGEX.match(src, i)
            tok = (r.group(0), i, r.end())
        else:
            m = JS_TOKEN.match(src, i)
            if m.lastgroup == "ws":
                broke = broke or "\n" in m.group(0)
                i = m.end()
                continue
            if m.lastgroup in ("lc", "bc"):
                out += [(w.group(0), i + w.start(), i + w.end()) for w in WORD.finditer(m.group(0))]
                broke = broke or "\n" in m.group(0)
                i = m.end()
                continue
            tok = (_string_value(m.group(0)) if m.lastgroup == "str" else m.group(0), i, m.end())
        if broke and prev is not None and _newline_matters(prev, src[tok[1]:tok[2]]):
            at = prev_at if prev in NEWLINE_ENDS_AFTER else tok[1:]
            out.append(("<nl>",) + at)
        out.append(tok)
        prev, prev_at, broke, i = src[tok[1]:tok[2]], tok[1:], False, tok[2]
    return out


def _without_trailing_commas(toks):
    return [t for k, t in enumerate(toks) if not (t[0] == "," and k + 1 < len(toks) and toks[k + 1][0] in CLOSERS)]


def _without_leading_pipes(toks):
    """`type A =\n  | B` and `type A = B` are the same type."""
    return [t for k, t in enumerate(toks) if not (t[0] in ("|", "&") and k and toks[k - 1][0] in LEADING_PIPE_AFTER)]


def _bracket_pairs(toks):
    pairs, stack = {}, []
    for k, t in enumerate(toks):
        if t[0] in OPENERS:
            stack.append(k)
        elif stack and t[0] == OPENERS[toks[stack[-1]][0]]:
            pairs[stack.pop()] = k
    return pairs


def _starts_element(toks, k):
    nxt = toks[k + 1][0] if k + 1 < len(toks) else ""
    if toks[k][0] != "<" or not (nxt == ">" or re.match(r"[A-Za-z]", nxt)):
        return False
    prev = toks[k - 1][0] if k else None
    return prev is None or prev == "return" or not re.match(r"[\w$)\]]", prev[-1])


def _without_jsx_parens(toks):
    """`return (\n  <A />\n)` and `return <A />` are the same."""
    drop = set()
    for k, end in _bracket_pairs(toks).items():
        if (toks[k][0] == "(" and k and toks[k - 1][0] in JSX_PAREN_AFTER and _starts_element(toks, k + 1)
                and toks[end - 1][0] == ">"):
            drop.update((k, end))
    return [t for k, t in enumerate(toks) if k not in drop]


def _jsx_children(toks):
    """Indexes of the tokens that sit in JSX children: text, and the `<` or `{` that starts a child."""
    out = set()

    def expression(j):
        depth = 0
        while j < len(toks):
            t = toks[j][0]
            if t == "}" and depth == 0:
                return j + 1
            if _starts_element(toks, j):
                j = element(j)
                continue
            depth += 1 if t in OPENERS else -1 if t in CLOSERS and t != ">" else 0
            j += 1
        return j

    def element(k):
        j = k + 1
        while j < len(toks) and toks[j][0] not in (">", "/"):
            j = expression(j + 1) if toks[j][0] == "{" else j + 1
        if j >= len(toks) or toks[j][0] == "/":
            return j + 2
        j += 1
        while j < len(toks):
            out.add(j)
            if toks[j][0] == "<" and j + 1 < len(toks) and toks[j + 1][0] == "/":
                while j < len(toks) and toks[j][0] != ">":
                    j += 1
                return j + 1
            if _starts_element(toks, j):
                j = element(j)
            else:
                j = expression(j + 1) if toks[j][0] == "{" else j + 1
        return j

    k = 0
    while k < len(toks):
        k = element(k) if _starts_element(toks, k) else k + 1
    return out


def _with_jsx_spacing(src, toks):
    """JSX keeps a space between text and `{expr}` or tags when it stays on one line, so it is part of the token."""
    children = _jsx_children(toks)
    out = []
    for k, (text, s, e) in enumerate(toks):
        gap = src[toks[k - 1][2]:s] if k else ""
        out.append((" " + text if k in children and gap and "\n" not in gap else text, s, e))
    return out


def _js_tokens(src, lang):
    toks = _without_leading_pipes(_without_trailing_commas(_js_raw(src)))
    return _with_jsx_spacing(src, _without_jsx_parens(toks)) if lang.jsx else toks


def _plain_pattern(quotes, comment):
    lc = r"(?P<lc>" + re.escape(comment) + r"[^\n]*)|" if comment else ""
    return re.compile(r"(?P<ws>\s+)|" + lc + r"(?P<str>" + "|".join(QUOTED[q] for q in quotes) + r")|(?P<id>\w+)|(?P<p>[^\s\w])")


def _plain_tokens(src, lang):
    quotes, comment = PLAIN_LANGS.get(lang.ext, PLAIN_DEFAULT)
    out = []
    for m in _plain_pattern(quotes, comment).finditer(src):
        if m.lastgroup == "lc":
            out += [(w.group(0), m.start() + w.start(), m.start() + w.end()) for w in WORD.finditer(m.group(0))]
        elif m.lastgroup != "ws":
            out.append((m.group(0), m.start(), m.end()))
    if lang.ext in INDENTED:
        # Indentation is meaning here; its token sits on the line's first word so a re-indent stays visible.
        out += [("<indent %s>" % m.group(1), m.start(2), m.end(2)) for m in INDENT.finditer(src)]
        out.sort(key=lambda t: (t[1], not t[0].startswith("<indent")))
    return out


def tokenize(src, path):
    lang = _Lang(path)
    return _js_tokens(src, lang) if lang.js else _plain_tokens(src, lang)


# One side (old or new) of a hunk, as text with its lines mapped back to row indexes.

class _Side:
    def __init__(self, rows, seg, kind, path):
        self.rows = [i for i in seg if rows[i][0] in ("ctx", kind)]
        self.text = "\n".join(rows[i][3] for i in self.rows)
        self.starts = [0]
        for r in self.rows[:-1]:
            self.starts.append(self.starts[-1] + len(rows[r][3]) + 1)
        self.js = _Lang(path).js
        self.tokens = tokenize(self.text, path)
        self.first = [self.line(t[1]) for t in self.tokens]
        self.last = [self.line(max(t[2] - 1, t[1])) for t in self.tokens]
        self.openers = _openers(self.tokens)
        self.pairs = _bracket_pairs(self.tokens)
        texts = {}
        for k, t in enumerate(self.tokens):
            texts.setdefault(self.first[k], []).append(t[0])
        self.line_text = {ln: " ".join(words) for ln, words in texts.items()}

    def line(self, offset):
        return bisect.bisect_right(self.starts, offset) - 1

    def head(self, k):
        """The tokens of the line holding k's innermost open bracket or JSX element, "" at the top level."""
        o = self.openers[k]
        return "" if o is None else self.line_text[self.first[o]]

    def in_lines(self, lo, hi):
        """Indexes of the tokens touching lines lo..hi."""
        return range(bisect.bisect_left(self.last, lo), bisect.bisect_right(self.first, hi))

    def ends_line(self, k):
        return k + 1 == len(self.tokens) or self.first[k + 1] > self.last[k]

    def pieces(self, k):
        """(row, start, end) for each line token k covers, columns relative to the row."""
        _, s, e = self.tokens[k]
        for ln in range(self.first[k], self.last[k] + 1):
            base = self.starts[ln]
            end = self.starts[ln + 1] - 1 if ln + 1 < len(self.starts) else len(self.text)
            yield self.rows[ln], max(s, base) - base, min(e, end) - base


def _openers(toks):
    """Per token, the index of its innermost open bracket or JSX element, or None."""
    stack, out = [], []
    for k, (text, _, _) in enumerate(toks):
        out.append(stack[-1] if stack else None)
        bare = text.lstrip()
        if bare in OPENERS:
            stack.append(k)
        elif bare in (")", "]", "}") and stack:
            stack.pop()
        elif bare == "<" and k + 1 < len(toks) and toks[k + 1][0] == "/" and stack:
            stack.pop()
        elif _starts_element(toks, k) and _opens_element(toks, k):
            stack.append(k)
    return out


def _opens_element(toks, k):
    j, depth = k + 1, 0
    while j < len(toks) and not (depth == 0 and toks[j][0] in (">", "/")):
        depth += 1 if toks[j][0] in ("{", "(") else -1 if toks[j][0] in ("}", ")") else 0
        j += 1
    return j < len(toks) and toks[j][0] == ">"


# Align: inside one git change block, which tokens changed.

def _segments(rows):
    seg, out = [], []
    for i, r in enumerate(rows):
        if r[0] == "hunk":
            if seg:
                out.append(seg)
            seg = []
        else:
            seg.append(i)
    return out + [seg] if seg else out


def _blocks(rows, seg):
    """Per run of del/add rows, its (first, last) line on the old and on the new side, None for an empty side."""
    out, old, new, cur = [], 0, 0, None
    for i in seg:
        kind = rows[i][0]
        if kind == "ctx":
            cur, old, new = None, old + 1, new + 1
            continue
        if cur is None:
            cur = [None, None]
            out.append(cur)
        n, line = (0, old) if kind == "del" else (1, new)
        cur[n] = (cur[n][0] if cur[n] else line, line)
        old, new = (old + 1, new) if kind == "del" else (old, new + 1)
    return out


def _one_line(ops, k, lines_a, lines_b):
    """Whether equal run k shares a line with the edits on both sides of it."""
    for n, lines in ((0, lines_a), (1, lines_b)):
        lo, hi = ops[k][1 + 2 * n], ops[k][2 + 2 * n]
        before, after = ops[k - 1][1 + 2 * n:3 + 2 * n], ops[k + 1][1 + 2 * n:3 + 2 * n]
        if before[1] > before[0] and lines[before[1] - 1][1] != lines[lo][0]:
            return False
        if after[1] > after[0] and lines[after[0]][0] != lines[hi - 1][1]:
            return False
    return True


def _align(a, b, lines_a, lines_b):
    """(changed positions in a, in b, equal pairs) for two lists of token texts with their (first, last) lines."""
    if not a or not b or len(a) + len(b) > MAX_BLOCK_TOKENS:
        return set(range(len(a))), set(range(len(b))), []
    ops = SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
    changed_a, changed_b = set(), set()
    for k, (tag, i1, i2, j1, j2) in enumerate(ops):
        short = tag == "equal" and i2 - i1 < MIN_EQUAL and 0 < k < len(ops) - 1
        if tag != "equal" or (short and _one_line(ops, k, lines_a, lines_b)):
            changed_a.update(range(i1, i2))
            changed_b.update(range(j1, j2))
    pairs = [(i, j) for tag, i1, i2, j1, j2 in ops if tag == "equal" for i, j in zip(range(i1, i2), range(j1, j2))]
    return changed_a, changed_b, pairs


def _mixed_brackets(side, ks, changed):
    """Positions of the changed brackets, other than statement blocks, whose contents in this block are partly changed
    and partly kept. A statement block's braces are strong themselves and leave the statements inside as they were."""
    at = {k: p for p, k in enumerate(ks)}
    out = set()
    for p in changed:
        close = side.pairs.get(ks[p])
        if close is None or (side.tokens[ks[p]][0] == "{" and ks[p] and side.tokens[ks[p] - 1][0] in BLOCK_AFTER):
            continue
        inside = [at[k] in changed for k in range(ks[p] + 1, close) if k in at]
        if any(inside) and not all(inside):
            out.add(p)
    return out


def _restructured(sides, picked, aligned):
    """Equal tokens whose bracket was added or removed around changed neighbours were moved into a new structure, as
    `x,` turning into `y: { id: x }`; only a bracket wrapping kept tokens alone leaves them unchanged."""
    changed_a, changed_b, pairs = aligned
    mixed = [_mixed_brackets(side, ks, hits) for side, ks, hits in zip(sides, picked, (changed_a, changed_b))]
    at = [{k: p for p, k in enumerate(ks)} for ks in picked]
    for i, j in pairs:
        openers = (at[0].get(sides[0].openers[picked[0][i]]), at[1].get(sides[1].openers[picked[1][j]]))
        if openers[0] in mixed[0] or openers[1] in mixed[1]:
            changed_a.add(i)
            changed_b.add(j)
    return changed_a, changed_b


def _imports(side, ks):
    """{position in ks: key} for the tokens of each import with bindings; the key ignores the order of named imports."""
    out, p = {}, 0
    while p < len(ks):
        k = ks[p]
        if side.tokens[k][0] != "import" or (side.openers[k] is not None):
            p += 1
            continue
        q = p + 1
        while q < len(ks) and not side.tokens[ks[q]][0].startswith("'"):
            q += 1
        if q >= len(ks) or q == p + 1:
            p += 1
            continue
        end = q + 1 + (q + 1 < len(ks) and side.tokens[ks[q + 1]][0] == ";")
        words = [side.tokens[x][0] for x in ks[p + 1:q]]
        named = " ".join(words[words.index("{") + 1:words.index("}")]).split(" , ") if "{" in words and "}" in words else []
        key = (tuple(words[:words.index("{")] if "{" in words else words), tuple(sorted(named)), side.tokens[ks[q]][0])
        out.update((x, key) for x in range(p, end))
        p = end
    return out


def _same_imports(sides, picked, changed):
    """Drop the changes of imports that only moved or reordered their names; side-effect imports are not touched."""
    keys = [_imports(side, ks) for side, ks in zip(sides, picked)]
    shared = set(keys[0].values()) & set(keys[1].values())
    return [{p for p in hits if keys[n].get(p) not in shared} for n, hits in enumerate(changed)]


def _line_end_commas(side, ks, hits):
    """A comma closing a line is layout in JS: it moves when a list is reflowed or grows by one item."""
    return {p for p in hits if not (side.js and side.tokens[ks[p]][0] == "," and side.ends_line(ks[p]))}


class _Slow(Exception):
    pass


def _changes(fi, path, rows, deadline):
    """The changed tokens of one file, per side, as (text, run, side, token index), runs never crossing a block; then
    the rows of blocks that only remove or only add lines."""
    out = ([], [], set())
    for si, seg in enumerate(_segments(rows)):
        sides = (_Side(rows, seg, "del", path), _Side(rows, seg, "add", path))
        for bi, lines in enumerate(_blocks(rows, seg)):
            if time.monotonic() > deadline:
                raise _Slow
            picked = [list(side.in_lines(*span)) if span else [] for side, span in zip(sides, lines)]
            for side, span in zip(sides, lines):
                if span and None in lines:
                    out[2].update(side.rows[ln] for ln in range(span[0], span[1] + 1))
            texts = [[side.tokens[k][0] for k in ks] for side, ks in zip(sides, picked)]
            lines = [[(side.first[k], side.last[k]) for k in ks] for side, ks in zip(sides, picked)]
            changed = _same_imports(sides, picked, _restructured(sides, picked, _align(*texts, *lines)))
            for n, (side, ks, hits) in enumerate(zip(sides, picked, changed)):
                for order, p in enumerate(sorted(_line_end_commas(side, ks, hits))):
                    out[n].append((side.tokens[ks[p]][0], (fi, si, bi, p - order), side, ks[p]))
    return out


# Moves: equal runs of changed tokens on both sides. A run loses its highlight only when it is a pure move.

def _move_index(adds):
    index = {}
    for j in range(len(adds) - MIN_MOVE + 1):
        if adds[j][1] == adds[j + MIN_MOVE - 1][1]:
            index.setdefault(tuple(a[0] for a in adds[j:j + MIN_MOVE]), []).append(j)
    return index


def _run_length(dels, adds, i, j):
    n = 0
    while (i + n < len(dels) and j + n < len(adds) and dels[i + n][0] == adds[j + n][0]
           and dels[i + n][1] == dels[i][1] and adds[j + n][1] == adds[j][1]):
        n += 1
    return n


def _move_candidates(dels, adds, deadline):
    index, found = _move_index(adds), []
    for i in range(len(dels) - MIN_MOVE + 1):
        if time.monotonic() > deadline:
            break
        if dels[i][1] != dels[i + MIN_MOVE - 1][1]:
            continue
        for j in index.get(tuple(d[0] for d in dels[i:i + MIN_MOVE]), [])[:MAX_MOVE_CANDIDATES]:
            continued = i and j and dels[i - 1][1] == dels[i][1] and adds[j - 1][1] == adds[j][1] and dels[i - 1][0] == adds[j - 1][0]
            if not continued:
                found.append((_run_length(dels, adds, i, j), i, j))
    return sorted(found, key=lambda c: -c[0])


def _stretches(ks):
    out = []
    for k in ks:
        if out and out[-1][1] == k:
            out[-1][1] = k + 1
        else:
            out.append([k, k + 1])
    return out


def _matched_runs(dels, adds, deadline):
    """[(i, j, n)]: dels[i:i+n] equals adds[j:j+n], longest first, no token in two runs."""
    used_d, used_a, runs = set(), set(), []
    for n, i, j in _move_candidates(dels, adds, deadline):
        free = [k for k in range(n) if i + k not in used_d and j + k not in used_a]
        for start, stop in _stretches(free):
            if stop - start >= MIN_MOVE:
                runs.append((i + start, j + start, stop - start))
                used_d.update(range(i + start, i + stop))
                used_a.update(range(j + start, j + stop))
    return runs


def _order_free(units, head):
    """Whether every unit (tokens of one statement or member) is a declaration whose position doesn't matter."""
    body = head.split(" ")[:3]
    for unit in units:
        words = [w for w in unit if w not in MODIFIERS]
        if not words:
            continue
        if words[0] == "import" and len(words) > 1 and not words[1].startswith("'"):
            continue
        if words[0] not in DECLARATIONS and not ORDER_FREE_BODIES & set(body):
            return False
    return True


def _units(texts):
    units, cur = [], []
    for t in texts:
        cur.append(t)
        if t in (";", "}"):
            units.append(cur)
            cur = []
    return units + [cur] if cur else units


def _pure(run, dels, adds, pairs):
    """Whether a matched run is a pure move: same enclosing scope, and order-free unless its parent moved with it."""
    i, j, n = run
    inside = {(id(dels[i + k][2]), dels[i + k][3]) for k in range(n)}
    top = []
    for k in range(n):
        old_side, old_k = dels[i + k][2], dels[i + k][3]
        new_side, new_k = adds[j + k][2], adds[j + k][3]
        o_old, o_new = old_side.openers[old_k], new_side.openers[new_k]
        if o_old is not None and (id(old_side), o_old) in inside:
            continue
        if o_old is not None and pairs.get((id(old_side), o_old)) == (id(new_side), o_new):
            continue
        if old_side.head(old_k) != new_side.head(new_k):
            return False
        top.append(dels[i + k][0])
    return _order_free(_units(top), dels[i][2].head(dels[i][3])) if top else True


def _moves(dels, adds, deadline):
    """Positions in dels and adds of the tokens that only moved."""
    runs = _matched_runs(dels, adds, deadline)
    pairs = {(id(dels[i + k][2]), dels[i + k][3]): (id(adds[j + k][2]), adds[j + k][3]) for i, j, n in runs for k in range(n)}
    moved_d, moved_a = set(), set()
    for run in runs:
        if _pure(run, dels, adds, pairs):
            i, j, n = run
            moved_d.update(range(i, i + n))
            moved_a.update(range(j, j + n))
    return moved_d, moved_a


# Grade rows: strong spans per row; rows left without any are quiet.

def _merged(ranges):
    out = []
    for start, end in sorted(ranges):
        if end <= start:
            continue
        if out and start <= out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return out


def _bridged(ranges, text):
    out = []
    for start, end in ranges:
        if out and not text[out[-1][1]:start].strip():
            out[-1][1] = end
        else:
            out.append([start, end])
    return out


def _trimmed(ranges, text):
    out = []
    for start, end in ranges:
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if end > start:
            out.append([start, end])
    return out


def _changed_rows(rows):
    return [i for i, r in enumerate(rows) if r[0] in ("del", "add")]


def _whole_rows(rows):
    return {i: r for i in _changed_rows(rows) for r in [_trimmed([[0, len(rows[i][3])]], rows[i][3])] if r}


def _grade(rows, changes, offsets, moved):
    ranges, touched = {}, set()
    for side_changes, offset, side_moved in zip(changes, offsets, moved):
        for pos, (_, _, side, k) in enumerate(side_changes):
            for row, s, e in side.pieces(k):
                touched.add(row)
                if pos + offset not in side_moved:
                    ranges.setdefault(row, []).append([s, e])
    # A line only removed or only added is new code as a whole, even where its tokens were dropped as layout.
    whole = _whole_rows(rows)
    ranges.update((i, whole[i]) for i in changes[2] if i in whole and (i in ranges or i not in touched))
    spans = {i: r for i, rs in ranges.items() for r in [_trimmed(_bridged(_merged(rs), rows[i][3]), rows[i][3])] if r}
    return spans, set(_changed_rows(rows)) - set(spans)


def strong_spans(files):
    """Per file, (spans, quiet): spans maps a row index to its strong [[start, end], ...] columns, quiet holds the
    del/add rows with none, whose changes are only whitespace, formatting or a pure move. files are {"path", "rows"}
    dicts with git's rows; a file too slow to compare gets every changed row highlighted whole and no quiet rows."""
    changes = []
    for fi, f in enumerate(files):
        try:
            changes.append(_changes(fi, f["path"], f["rows"], time.monotonic() + FILE_SECONDS))
        except (_Slow, RecursionError):
            changes.append(None)
    dels = [c for ch in changes if ch for c in ch[0]]
    adds = [c for ch in changes if ch for c in ch[1]]
    moved = _moves(dels, adds, time.monotonic() + MOVE_SECONDS)
    out, offsets = [], [0, 0]
    for f, ch in zip(files, changes):
        if ch is None:
            out.append((_whole_rows(f["rows"]), set()))
            continue
        out.append(_grade(f["rows"], ch, offsets, moved))
        offsets = [offsets[0] + len(ch[0]), offsets[1] + len(ch[1])]
    return out
