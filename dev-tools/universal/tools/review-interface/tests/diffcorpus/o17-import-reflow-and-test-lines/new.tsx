import type { Cache, SWRConfigValue, TagRevalidator } from 'swr'
import useSWR, {
  revalidateTag as globalRevalidateTag,
  useSWRConfig,
  SWRConfig
} from 'swr'
import { expectType } from './utils'

export function useTestCache() {
  expectType<Cache<any>>(useSWRConfig().cache)
  expectType<TagRevalidator>(useSWRConfig().revalidateTag)
  expectType<TagRevalidator>(globalRevalidateTag)
}
