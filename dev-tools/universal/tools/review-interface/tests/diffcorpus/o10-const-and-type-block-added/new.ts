export const DEFAULT_WIDTH = 500
export const DEFAULT_SORT_ORDER = 1
export const FILTER_SCOPES = ['key', 'data', 'all'] as const
/** What the list filters match: the key, the data, or either. */
export type FilterScope = (typeof FILTER_SCOPES)[number]
export const DEFAULT_FILTER_SCOPE: FilterScope = 'key'
