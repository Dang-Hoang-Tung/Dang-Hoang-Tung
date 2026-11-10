afterAll(() => {
  // TS < 4.5 causes type error without `as any`
  ;(window as any).localStorage = saved
})
