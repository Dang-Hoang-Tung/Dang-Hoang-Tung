export type MutationConfig<SWRData> = {
  populateCache?: boolean
  optimisticData?:
    | SWRData
    | ((currentData?: SWRData, displayedData?: SWRData) => SWRData)
  rollbackOnError?: boolean
}
