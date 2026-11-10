export const Save = () => (
  <Button variant="primary" disabled={!dirty} onClick={save}>
    Save
  </Button>
);
