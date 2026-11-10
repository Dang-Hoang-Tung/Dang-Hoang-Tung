const saved = api.setState

api.setState = (...args) => {
  saved(...(args as Parameters<typeof saved>))
  return setItem()
}
