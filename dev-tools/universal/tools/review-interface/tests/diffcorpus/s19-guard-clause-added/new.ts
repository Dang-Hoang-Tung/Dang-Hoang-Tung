export function total(order?: Order) {
  if (!order) return 0;
  return order.lines.length;
}
