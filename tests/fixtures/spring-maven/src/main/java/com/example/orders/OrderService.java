package com.example.orders;

import org.springframework.stereotype.Service;

@Service
public class OrderService {
    public long total(long[] amounts) {
        long sum = 0;
        for (long amount : amounts) {
            sum += amount;
        }
        return sum;
    }
}
