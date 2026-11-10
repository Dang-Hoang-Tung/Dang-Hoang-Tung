describe('Tabs', () => {
  it('renders', () => {
    render(<Tabs.Root />);
  });

  it('reports value changes', () => {
    const onChange = vi.fn((value: TabValue) => value);
    render(
      <Tabs.Root defaultValue="one" onValueChange={onChange}>
        <Tabs.Trigger value="two">Two</Tabs.Trigger>
      </Tabs.Root>,
    );
    expect(onChange).toHaveBeenCalledWith('two');
  });
});
