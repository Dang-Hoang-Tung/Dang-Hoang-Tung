# Implementation
- Is the main logic correct?
- Is the code organized in a way that promotes testability and maintainability?
- Are there any signs of tight coupling, entanglement, or leaky abstractions?
- Are there any opportunities to simplify the design or reduce complexity?
- Are there any opportunities to leverage existing libraries, tools, or frameworks to simplify the implementation?
- Are there any areas where the code could be more modular, reusable, or composable?
- Are there any opportunities to improve the clarity, readability, or expressiveness of the code?
- Are there any potential edge cases or failure modes that are not adequately handled?
- Do functions return values honestly, or do they spill inner logic that has to be caught/handled by the caller? For example, if the function throws errors that need to be collapsed into a value by the caller, that's bad design.
- Is dependency injection appropriately used? Where possible we should inject dependencies to avoid coupling. However, DI should be one-layer and not multiple layers (i.e. instead of passing in dependencies of dependencies, just initialise the full dependency object outside and pass it in).

# Types, contracts, schemas
- Are types and interfaces well-defined and used consistently? Or duplicated or inconsistent?
- Are there any missing types or interfaces that would improve clarity and safety?
- Are there any types or interfaces that are too broad or too narrow?
- Are there any inconsistencies in naming or structure of types and interfaces?
- Are there any potential issues with type safety or type inference in the current implementation?
- Are the types exhaustive and do they cover all relevant cases?
- Are there any use of loose typing (e.g. `any`, `object`, `dict`, `unknown`, `never`) that could be improved with more specific types?
- Does datetime field (if exists) naming follow a consistent convention?
- Are types explicitly defined or dynamically generated? Wherever possible they should be derived explicitly, especially when there are multiple variants of the same base/generic type.
- Are we missing type guards? Objects should always be coerced to the correct types using type guards. An explicit type guard (`x is T`) should exist for each explicit type, unless the type is differentiated trivially (i.e. just one field "type") then we can make a generic type guard.
- Are schemas clear as to whether they belong to the API or DB? The file path or variable name should reflect that.
- Are schema values tightly constrained (enums, `.uuid()`, `.min`/`.max`, bounded lists) rather than bare `z.string()`/`z.number()` — especially request inputs (query/path/body), the trust boundary?

# Tests
- Are there tests for the new code? If not, is there a good reason why not?
- Do the tests follow our testing principles and best practices?
- Do the tests provide good coverage of the new code, including edge cases and failure modes?
- Are the tests well-structured, clear, and maintainable?
- Are the tests exhaustive or are there any important scenarios that are not covered?
- Are any of the tests redundant or insignificant?

# Nits
- Are there variable names that could be improved?
- Are there logic pieces that could be more readable?
- Are there coding styles that are ugly or not idiomatic?
- File sizes should be moderate: files should not be over 500 lines, but also should not contain just a simple small function. Group functions/helpers and separate by domain layers when the file gets big.
