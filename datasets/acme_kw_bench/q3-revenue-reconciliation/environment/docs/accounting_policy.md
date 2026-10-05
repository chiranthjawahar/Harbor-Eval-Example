# Acme Corp Revenue Recognition Policy (FY2026 Q3)

1. **Succeeded vs. Refunded Charges**:
   - Only charges with `status = succeeded` may be recognized as revenue.
   - Charges with `status = refunded` must be recognized at `$0.00` USD.

2. **Annual Contract Proration (ASC 606)**:
   - Invoices with `billing_term = monthly` are recognized 100% in the quarter billed.
   - Invoices with `billing_term = annual` cover 4 quarters (12 months); only **25% (1 quarter)** of the total contract value may be recognized in Q3.

3. **Foreign Exchange (FX) Conversion**:
   - All EUR charges must be converted to USD using the fixed Q3 treasury peg: **`1.00 EUR = 1.10 USD`**.
