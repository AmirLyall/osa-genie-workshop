---
name: pcard-split-purchase-test
description: Run a P-card split-purchase test on the OSA workshop data. Use when asked to test for split purchases, purchases broken up to stay under a card's single-purchase limit.
---

# P-card split-purchase test

Use the `osa_pcard_review` tables (`transactions` and `cardholders`).

## Steps

1. Group transactions by card, merchant and transaction date.
2. Keep groups with two or more purchases where every purchase is at or under the card's `single_purchase_limit`, but the combined total is over it.
3. Join to `cardholders` for the cardholder name, agency and limit.
4. Unless the user gives a different period, cover fiscal year 2026 (July 1, 2025 to June 30, 2026).

## Output

- A summary line: the number of possible split purchases and their combined dollars.
- A table sorted by combined total, largest first: date, cardholder, agency, merchant, number of purchases, combined total, single-purchase limit.
- A count by agency.
- A closing note that these are possible splits to review with receipts and the cardholder, not confirmed violations.
