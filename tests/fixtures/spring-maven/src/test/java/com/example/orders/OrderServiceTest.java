package com.example.orders;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class OrderServiceTest {
    @Test
    void sumsAmounts() {
        assertEquals(3, new OrderService().total(new long[] {1, 2}));
    }
}
