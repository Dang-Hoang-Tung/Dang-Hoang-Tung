function load(customerId: string) {
  const row = db.get(customerId);
  return audit(customerId, row);
}
