test('a throwing internal throws on every read', () => {
  for (let i = 0; i < 3; i++) {
    expect(() => schema.read()).toThrow();
  }
});

test('a throwing getter repeats the same error until it resolves', () => {
  let ready = false;
  const boom = new Error('boom');
  const schema = make(() => {
    if (!ready) throw boom;
    return value();
  });
  expect(() => schema.parse('a')).toThrow(boom);
  ready = true;
  expect(schema.parse('a')).toEqual('a');
});
