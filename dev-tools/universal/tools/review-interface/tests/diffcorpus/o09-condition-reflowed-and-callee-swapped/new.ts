if (
  typeof cloned.enabled === 'function' &&
  cloned.enabled.length === 0
) {
  cloned.enabled = cloned.enabled()
}
const defaulted = client.defaultQueryOptions(cloned)
