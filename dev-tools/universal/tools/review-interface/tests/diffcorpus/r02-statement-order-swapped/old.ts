export async function close(order: Order) {
  await save(order);
  notify(order);
}
