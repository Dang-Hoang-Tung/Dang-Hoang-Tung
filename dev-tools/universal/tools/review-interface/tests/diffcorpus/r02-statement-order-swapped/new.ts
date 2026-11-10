export async function close(order: Order) {
  notify(order);
  await save(order);
}
