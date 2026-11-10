function load(userId: string) {
  const row = db.get(userId);
  return audit(userId, row);
}
