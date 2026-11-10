export function attach(issues: Issue[], start: number): void {
  mark(issues, start);
}

/** Gives each issue from `start` on its own path. */
export function ownPaths(issues: Issue[], start: number): void {
  for (let i = start; i < issues.length; i++) {
    const iss = issues[i] as any;
    if (iss.path) iss.path = iss.path.slice();
  }
}

export function finalize(issue: Issue): Issue {
  return issue;
}
