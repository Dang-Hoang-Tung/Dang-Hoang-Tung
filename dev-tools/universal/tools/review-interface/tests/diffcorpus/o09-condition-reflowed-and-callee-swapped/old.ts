if (typeof cloned.enabled === 'function') {
  cloned.enabled = original.enabled()
}
const defaulted = client.defaultQueryOptions(cloned)
