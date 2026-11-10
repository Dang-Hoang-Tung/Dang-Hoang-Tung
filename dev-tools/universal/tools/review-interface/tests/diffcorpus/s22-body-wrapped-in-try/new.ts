async function go() {
  const a = prepare();
  try {
    await save(a);
  } catch (e) {
    report(e);
  }
}
