import { cartTotal } from './cart-total';
import { expect, test } from 'vitest';

test('sums prices', () => {
  expect(cartTotal([1, 2])).toBe(3);
});
