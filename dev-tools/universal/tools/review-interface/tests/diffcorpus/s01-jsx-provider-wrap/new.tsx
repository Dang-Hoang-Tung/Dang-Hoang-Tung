export function Page() {
  return (
    <ThemeProvider theme={theme}>
      <Layout>
        <OrderList orders={orders} />
      </Layout>
    </ThemeProvider>
  );
}
