const handle = (canary) => {
  // abort if the canary is aborted
  if (aborted(canary)) {
    canary.aborted = true;
    return canary;
  }
  return run(canary);
};
