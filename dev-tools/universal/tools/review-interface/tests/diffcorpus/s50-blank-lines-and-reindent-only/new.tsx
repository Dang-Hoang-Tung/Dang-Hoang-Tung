export function go() {
  if (flag) {
    const a = prepare();
    save(a);
    notify(a);
  }
}
