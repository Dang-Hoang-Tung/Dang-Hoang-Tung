async function load(id: string) {
  const r = await fetchOrder(id);
  return r;
}
