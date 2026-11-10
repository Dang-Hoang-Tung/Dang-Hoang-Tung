export function pick(items: Item[]) {
  const limit = 10;
  return items.slice(0, limit);
}

export function other() {
  return 1;
}

export function last() {
  return 2;
}
