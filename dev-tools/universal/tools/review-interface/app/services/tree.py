import copy

from app.domain import worst

NODE_H, GAP_X, GAP_Y, CHAR_W, PAD, INDENT, STACK_GAP = 42, 16, 56, 7.4, 24, 22, 10


def build_tree(paths, root_name):
    root = {"name": root_name, "children": {}, "file": None}
    for p in paths:
        node = root
        for part in p.split("/"):
            node = node["children"].setdefault(part, {"name": part, "children": {}, "file": None})
        node["file"] = p

    def compress(n, is_root=False):
        kids = [compress(c) for c in n["children"].values()]
        while len(kids) == 1 and not kids[0]["file"] and not is_root and not n["file"]:
            n = {"name": n["name"] + "/" + kids[0]["name"], "file": None, "kids": kids[0]["kids"]}
            kids = n["kids"]
        return {"name": n["name"], "file": n["file"], "kids": sorted(kids, key=lambda k: (k["file"] is not None, k["name"]))}

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


def items_of(n):
    folders = [k for k in n["kids"] if k["kids"]]
    leaves = [k for k in n["kids"] if not k["kids"]]
    return folders + ([{"stack": leaves}] if leaves else [])


def items_width(its):
    return sum(i["span"] for i in its) + GAP_X * (len(its) - 1) if its else 0


def measure(n, file_stats):
    n["stat"] = stat_info(n, file_stats)
    n["w"] = max(len(label_of(n)) * CHAR_W, len(n["stat"]["text"]) * 6.2) + PAD
    its = items_of(n)
    for it in its:
        if "stack" in it:
            for leaf in it["stack"]:
                measure(leaf, file_stats)
            it["span"] = INDENT + max(leaf["w"] for leaf in it["stack"])
        else:
            measure(it, file_stats)
    n["items"] = its
    n["span"] = max(n["w"], items_width(its))


def place(n, left, y):
    n["y"] = y
    its = n["items"]
    kids_w = items_width(its)
    only_stack = len(its) == 1 and "stack" in its[0]
    x = left if only_stack else left + (n["span"] - kids_w) / 2
    cy = y + NODE_H + (STACK_GAP * 2 if only_stack else GAP_Y)
    for it in its:
        if "stack" in it:
            for j, leaf in enumerate(it["stack"]):
                leaf["y"] = cy + j * (NODE_H + STACK_GAP)
                leaf["items"] = []
                leaf["cx"] = x + INDENT + leaf["w"] / 2
            it["cx"] = x + INDENT / 2
        else:
            place(it, x, cy)
        x += it["span"] + GAP_X
    n["cx"] = left + n["w"] / 2 if only_stack else left + n["span"] / 2 if not its else (its[0]["cx"] + its[-1]["cx"]) / 2


def node_geometry(n, file_stats):
    st = n["stat"]
    role = "leaf" if n["file"] else ("root" if n["y"] == 0 else "dir")
    return {
        "x": n["cx"] - n["w"] / 2, "y": n["y"], "w": n["w"], "h": NODE_H, "cx": n["cx"],
        "label": label_of(n), "title": n["file"] or n["name"],
        "file": file_stats[n["file"]]["idx"] if n["file"] else None, "role": role,
        "kind": worst(n["kind"] for n in st["notes"]), "gen": st["gen"], "a": st["a"], "d": st["d"], "notes": len(st["notes"]),
    }


def stack_edges(it, top):
    edges = [f'M{it["cx"]},{top} V{it["stack"][-1]["y"] + NODE_H / 2}']
    for leaf in it["stack"]:
        edges.append(f'M{it["cx"]},{leaf["y"] + NODE_H / 2} H{leaf["cx"] - leaf["w"] / 2}')
    return edges


def walk(n, file_stats, nodes, edges):
    nodes.append(node_geometry(n, file_stats))
    its = n["items"]
    if not its:
        return
    if len(its) == 1 and "stack" in its[0]:
        edges += stack_edges(its[0], n["y"] + NODE_H)
        nodes += [node_geometry(leaf, file_stats) for leaf in its[0]["stack"]]
        return
    bus = n["y"] + NODE_H + GAP_Y / 2
    edges.append(f'M{n["cx"]},{n["y"] + NODE_H} V{bus}')
    if len(its) > 1:
        edges.append(f'M{its[0]["cx"]},{bus} H{its[-1]["cx"]}')
    for it in its:
        if "stack" in it:
            edges += stack_edges(it, bus)
            nodes += [node_geometry(leaf, file_stats) for leaf in it["stack"]]
        else:
            edges.append(f'M{it["cx"]},{bus} V{it["y"]}')
            walk(it, file_stats, nodes, edges)


def layout(tree, file_stats):
    root = copy.deepcopy(tree)
    measure(root, file_stats)
    place(root, 0, 0)
    nodes, edges = [], []
    walk(root, file_stats, nodes, edges)
    return {"width": root["span"], "height": max(n["y"] + n["h"] for n in nodes), "nodes": nodes, "edges": edges}
