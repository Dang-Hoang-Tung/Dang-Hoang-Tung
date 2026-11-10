test('a throwing internal throws on every read', () => {
  for (let i = 0; i < 3; i++) {
    expect(() => schema.read()).toThrow();
  }
});
