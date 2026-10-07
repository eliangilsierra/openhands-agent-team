export function cartTotal(prices: number[]): number {
  return prices.reduce((sum, price) => sum + price, 0);
}
