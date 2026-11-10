it('keeps a stable function', () => {
  const countAtom = atom(1)
  let firstFn:
    (((get: Getter) => number) & { mockClear: () => void }) | undefined
  expect(countAtom).toBeDefined()
})
