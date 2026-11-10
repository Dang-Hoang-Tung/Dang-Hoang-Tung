import type { Cache, SWRConfigValue } from 'swr'
import useSWR, { useSWRConfig, SWRConfig } from 'swr'
import { expectType } from './utils'

export function useTestCache() {
  expectType<Cache<any>>(useSWRConfig().cache)
}
