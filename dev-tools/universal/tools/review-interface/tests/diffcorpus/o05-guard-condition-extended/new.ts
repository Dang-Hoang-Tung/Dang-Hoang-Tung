const shouldRevalidate = (() => {
  if (isInitialMount && !isUndefined(revalidateOnMount)) return revalidateOnMount
  const data = !isUndefined(fallback) ? fallback : snapshot.data
  if (suspense && hasCacheData && isUndefined(data)) return false
  return isUndefined(data) || revalidateIfStale
})()
