const output = def.transform(payload.value, payload);
if (output instanceof Promise) {
  return output.then((output) => {
    payload.value = output;
    return payload;
  });
}
payload.value = output;
return payload;
