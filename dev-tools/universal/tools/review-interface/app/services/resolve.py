"""Find the repo file an import points at, at a given commit, and read files the PR doesn't touch."""
import json
import posixpath
import subprocess

from app.services import git
from app.services.shell import run

CODE_EXTS = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs", ".json", ".d.ts")
MAX_BYTES = 2_000_000
_trees = {}


class NotFound(Exception):
    pass


def clone_for(cfg, repo):
    clone = git.clone_for(cfg, repo)
    if not clone:
        raise NotFound("This needs a local clone of " + repo)
    return clone


def _stem(p):
    for e in sorted(CODE_EXTS, key=len, reverse=True):
        if p.endswith(e):
            return p[:-len(e)]
    return None


def _packages(clone, sha, paths):
    files = [p for p in paths if p.endswith("package.json") and "node_modules/" not in p]
    if not files:
        return {}
    out = subprocess.run(["git", "-C", clone, "cat-file", "--batch"], input="".join(f"{sha}:{p}\n" for p in files),
                         capture_output=True, text=True, check=True, timeout=60).stdout
    names, pos = {}, 0
    for p in files:
        header_end = out.index("\n", pos)
        header = out[pos:header_end].split()
        if len(header) < 3 or header[1] != "blob":
            pos = header_end + 1
            continue
        size = int(header[2])
        body = out[header_end + 1:header_end + 1 + size]
        pos = header_end + 1 + size + 1
        try:
            name = json.loads(body).get("name")
        except (ValueError, AttributeError):
            continue
        if isinstance(name, str) and name:
            names[name] = posixpath.dirname(p)
    return names


def tree(clone, sha):
    key = (clone, sha)
    if key not in _trees:
        paths = [p for p in run("git", "-C", clone, "ls-tree", "-r", "-z", "--name-only", sha, timeout=60).split("\0") if p]
        index = {}
        for p in paths:
            stem = _stem(p)
            if stem is None or "node_modules/" in p:
                continue
            for s in {stem, stem[:-6] if stem.endswith("/index") else stem}:
                segs = s.split("/")
                for k in range(len(segs)):
                    index.setdefault("/".join(segs[k:]), []).append(p)
        if len(_trees) >= 4:
            _trees.pop(next(iter(_trees)))
        _trees[key] = (set(paths), index, _packages(clone, sha, paths))
    return _trees[key]


def _candidates(base):
    out = [base] + [base + e for e in CODE_EXTS] + [base + "/index" + e for e in CODE_EXTS]
    stem = _stem(base)
    if stem is not None:
        out += [stem + e for e in (".ts", ".tsx", ".mts")]
    return out


def _first(paths, base):
    return next((c for c in _candidates(base) if c in paths), None)


def _closest(hits, from_path):
    def shared(p):
        a, b = p.split("/"), from_path.split("/")
        n = 0
        while n < min(len(a), len(b)) and a[n] == b[n]:
            n += 1
        return n
    return sorted(set(hits), key=lambda p: (-shared(p), len(p), p))[0]


def resolve(clone, sha, from_path, spec):
    paths, index, packages = tree(clone, sha)
    if spec.startswith("."):
        return _first(paths, posixpath.normpath(posixpath.join(posixpath.dirname(from_path), spec)))
    for name in sorted(packages, key=len, reverse=True):
        if spec == name or spec.startswith(name + "/"):
            rest, root = spec[len(name):].lstrip("/"), packages[name]
            for base in ([posixpath.join(root, rest), posixpath.join(root, "src", rest)] if rest else [posixpath.join(root, "src/index"), posixpath.join(root, "index")]):
                hit = _first(paths, base)
                if hit:
                    return hit
    segs = spec.split("/")
    for k in range(len(segs)):
        if len(segs) - k < 2 and len(segs) > 1:
            break
        hits = index.get("/".join(segs[k:]))
        if hits:
            return _closest(hits, from_path)
    return None


def read(clone, sha, path):
    paths = tree(clone, sha)[0]
    if path not in paths:
        raise NotFound(path + " isn't in the repo at this commit")
    size = int(run("git", "-C", clone, "cat-file", "-s", f"{sha}:{path}"))
    if size > MAX_BYTES:
        raise NotFound(path + " is too big to show")
    try:
        return run("git", "-C", clone, "show", f"{sha}:{path}", timeout=30, errors="strict")
    except UnicodeDecodeError:
        raise NotFound(path + " isn't a text file")
