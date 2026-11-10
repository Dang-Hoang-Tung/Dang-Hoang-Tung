export function other() {
  return 1;
}

export function last() {
  return 2;
}

export function pick(items: Item[]) {
  const limit = 20;
  return items.slice(0, limit);
}
