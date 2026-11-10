if (selectError) {
  error = selectError
  errorUpdatedAt =
    prev?.error === error ? prev.errorUpdatedAt : Date.now()
  status = 'error'
}
