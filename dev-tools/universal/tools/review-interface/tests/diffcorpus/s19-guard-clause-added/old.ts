export function total(order?: Order) {
  return order.lines.length;
}
