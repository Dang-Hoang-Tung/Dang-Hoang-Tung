import copy

from app.domain import worst

NODE_H, GAP_X, CHAR_W, PAD, ROW_GAP = 42, 40, 7.4, 24, 10
ICON_W = 18


def build_tree(paths, root_name, collapse=True):
    root = {"name": root_name, "children": {}, "file": None}
    for p in paths:
        node = root
        for part in p.split("/"):
            node = node["children"].setdefault(part, {"name": part, "children": {}, "file": None})
        node["file"] = p

    def compress(n, is_root=False):
        kids = [compress(c) for c in n["children"].values()]
        while collapse and len(kids) == 1 and not kids[0]["file"] and not is_root and not n["file"]:
            n = {"name": n["name"] + "/" + kids[0]["name"], "file": None, "kids": kids[0]["kids"]}
            kids = n["kids"]
        return {"name": n["name"], "file": n["file"], "kids": sorted(kids, key=lambda k: (k["file"] is not None, k["name"].lower(), k["name"]))}

    return compress(root, True)


def label_of(n):
    return n["name"] if len(n["name"]) <= 44 else n["name"][:20] + "…" + n["name"][-23:]


def note_text(count):
    return f" · {count} note" + ("s" if count != 1 else "") if count else ""


def node_stats(n, file_stats):
    if n["file"]:
        fs = file_stats[n["file"]]
        a, d, notes = fs["a"], fs["d"], fs["notes"]
    else:
        a = d = 0
        notes = []
        for k in n["kids"]:
            ka, kd, kn = node_stats(k, file_stats)
            a, d, notes = a + ka, d + kd, notes + kn
    return a, d, notes


def stat_info(n, file_stats):
    a, d, notes = node_stats(n, file_stats)
    gen = bool(n["file"] and file_stats[n["file"]]["gen"])
    text = f"+{a} −{d}" + note_text(len(notes)) + (" · generated" if gen else "")
    return {"a": a, "d": d, "notes": notes, "gen": gen, "text": text}


def measure(n, file_stats):
    n["stat"] = stat_info(n, file_stats)
    n["w"] = max(len(label_of(n)) * CHAR_W + ICON_W, len(n["stat"]["text"]) * 6.2) + PAD
    for k in n["kids"]:
        measure(k, file_stats)


def place(n, x, y):
    """Lay the tree out left to right: each node shares a row with its first child, so rows read in directory order."""
    n["x"], n["y"] = x, y
    bottom = y
    for k in n["kids"]:
        bottom = place(k, x + n["w"] + GAP_X, bottom)
    return max(bottom, y + NODE_H + ROW_GAP)


def column_xs(root):
    """x of each depth's column: every node at a depth starts at the same x, so levels line up across branches."""
    widths = []

    def collect(n, depth):
        if depth == len(widths):
            widths.append(0)
        widths[depth] = max(widths[depth], n["w"])
        for k in n["kids"]:
            collect(k, depth + 1)
    collect(root, 0)
    xs, x = [], 0
    for w in widths:
        xs.append(x)
        x += w + GAP_X
    return xs


def place_aligned(n, xs, y, depth=0):
    n["x"], n["y"] = xs[depth], y
    bottom = y
    for k in n["kids"]:
        bottom = place_aligned(k, xs, bottom, depth + 1)
    return max(bottom, y + NODE_H + ROW_GAP)


def node_geometry(n, file_stats, role):
    st = n["stat"]
    return {
        "x": n["x"], "y": n["y"], "w": n["w"], "h": NODE_H, "cx": n["x"] + n["w"] / 2,
        "label": label_of(n), "title": n["file"] or n["name"],
        "file": file_stats[n["file"]]["idx"] if n["file"] else None, "role": role,
        "status": file_stats[n["file"]].get("status", "modified") if n["file"] else None,
        "kind": worst(n["kind"] for n in st["notes"]), "gen": st["gen"], "a": st["a"], "d": st["d"], "notes": len(st["notes"]),
    }


def _mid(n):
    return n["y"] + NODE_H / 2


def walk(n, file_stats, nodes, edges, role="root"):
    nodes.append(node_geometry(n, file_stats, role))
    kids = n["kids"]
    if not kids:
        return
    bus = kids[0]["x"] - GAP_X / 2
    edges.append(f'M{n["x"] + n["w"]},{_mid(n)} H{bus}')
    if len(kids) > 1:
        edges.append(f"M{bus},{_mid(kids[0])} V{_mid(kids[-1])}")
    for k in kids:
        edges.append(f'M{bus},{_mid(k)} H{k["x"]}')
        walk(k, file_stats, nodes, edges, "leaf" if k["file"] else "dir")


def layout(tree, file_stats, aligned=False):
    root = copy.deepcopy(tree)
    measure(root, file_stats)
    if aligned:
        place_aligned(root, column_xs(root), 0)
    else:
        place(root, 0, 0)
    nodes, edges = [], []
    walk(root, file_stats, nodes, edges)
    return {"width": max(n["x"] + n["w"] for n in nodes), "height": max(n["y"] + n["h"] for n in nodes), "nodes": nodes, "edges": edges}
