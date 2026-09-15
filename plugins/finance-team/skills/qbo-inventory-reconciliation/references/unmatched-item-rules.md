# Flag Unmatched Items — Classification Detail (Step 6)

List the two special cases below in that same section too:

- Counted, and not found in QBO's inventory items. That means a naming
  mismatch, or a discontinued item. It can also mean something counted
  that nobody set up in QBO as an inventory item.
- In QBO's inventory pull, and not in the physical count. **What you do
  here depends on the omission convention that Step 2 confirmed.** The
  bookkeeper may have said the count is exhaustive, so a missing item
  means a real counted zero. Zero-fill this item's counted quantity in
  that case. Run it through Step 5 as a normal item. A nonzero QBO
  quantity then correctly shows as a shortage. The bookkeeper may instead
  have said the count lists only what they found. A missing item then
  means that nobody checked it. List it here as genuinely uncounted in
  that case, rather than zero-filling it. Treating "not checked" as
  "checked and found zero" would report false shrinkage.
- **Value without quantity**, from Step 5. QBO shows zero on-hand quantity
  for an item. The physical count also shows zero, or nobody counted the
  item at all because they believe there is none. QBO's asset value for
  that item is nonzero. Flag this as a stranded-value discrepancy. Cite
  QBO's raw asset value as the amount. Do this even though there is no
  quantity variance and no computed dollar variance to report.
- **Intraday timing, no supporting log**, from Step 1 and Step 5. The
  count was not taken end-of-day and no timestamped movement log was
  available. Flag every item in the report this way. Do not flag only the
  ones with observable "same-day activity". QBO's day-granular data cannot
  tell you per item whether it moved that day. Flag each one as "variance
  may include post-count movement", even though you still report a number.
