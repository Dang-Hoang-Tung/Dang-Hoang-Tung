const start = payload.issues.length;
const output = def.transform(payload.value, payload);
if (output instanceof Promise) {
  return output.then((output) => {
    payload.value = output;
    if (payload.issues.length !== start) ownPaths(payload.issues, start);
    return payload;
  });
}
payload.value = output;
if (payload.issues.length !== start) ownPaths(payload.issues, start);
return payload;
