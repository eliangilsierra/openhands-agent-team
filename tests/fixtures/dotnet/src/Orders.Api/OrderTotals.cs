namespace Orders.Api;

public static class OrderTotals
{
    public static decimal Sum(decimal[] amounts) => amounts.Sum();
}
