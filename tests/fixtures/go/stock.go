package inventory

// Available reports whether the stock covers the quantity.
func Available(stock, quantity int) bool {
	return stock >= quantity
}
