export type MutationConfig<SWRData> = {
  populateCache?: boolean
  optimisticData?: SWRData | ((currentData?: SWRData) => SWRData)
  rollbackOnError?: boolean
}
