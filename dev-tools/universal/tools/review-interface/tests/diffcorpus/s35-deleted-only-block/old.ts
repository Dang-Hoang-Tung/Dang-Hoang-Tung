export function keep() {
  return 1;
}

export function legacyTotal(items: number[]) {
  return items.reduce((a, b) => a + b, 0);
}

export const tail = 2;
