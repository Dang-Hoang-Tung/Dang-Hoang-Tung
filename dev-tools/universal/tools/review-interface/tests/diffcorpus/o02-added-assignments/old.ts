if (cacheContext) {
  ;(extended as any).cache = cacheContext[0]
  ;(extended as any).mutate = cacheContext[1]
  ;(extended as any).unload = cacheContext[4]
}
