const shouldRevalidate = (() => {
  if (isInitialMount && !isUndefined(revalidateOnMount)) return revalidateOnMount
  if (suspense && hasCacheData) return false
  const data = !isUndefined(fallback) ? fallback : snapshot.data
  return isUndefined(data) || revalidateIfStale
})()
