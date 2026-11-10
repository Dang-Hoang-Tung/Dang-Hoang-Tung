const handle = (canary) => {
  // abort if the canary is aborted
  if (aborted(canary)) return canary;
  return run(canary);
};
