if (!count) {
  const dispose = disposers.get(key)
  dispose?.()
}
