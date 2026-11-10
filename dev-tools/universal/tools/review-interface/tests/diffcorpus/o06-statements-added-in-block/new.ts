if (!count) {
  const dispose = disposers.get(key)
  dispose?.()

  subscriptions.delete(key)
  disposers.delete(key)
}
