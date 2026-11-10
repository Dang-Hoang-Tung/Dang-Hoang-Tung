const saved = api.setState

api.setState = (state, replace) => {
  saved(state, replace as any)
  return setItem()
}
