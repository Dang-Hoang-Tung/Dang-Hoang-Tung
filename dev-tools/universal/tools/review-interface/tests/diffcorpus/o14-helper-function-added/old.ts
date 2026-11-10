export function attach(issues: Issue[], start: number): void {
  mark(issues, start);
}

export function finalize(issue: Issue): Issue {
  return issue;
}
