class Cart {
  public items: Item[] = [];

  count() {
    return this.items.length;
  }

  clear() {
    this.items = [];
  }
}
