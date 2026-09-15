# Output Templates

## Status View (Step 3)

Build one status view. Cover the closing schedule and all six steps:

```
## Close Status for [period], target close date: [date or "not stated"]

| Step                        | Status                    | Notes |
|------------------------------|---------------------------|-------|
| Cash                         | …                         | …     |
| Revenue / AR                 | …                         | …     |
| Expenses / AP                | …                         | …     |
| Payroll / balance sheet      | …                         | …     |
| Inventory                    | …                         | …     |
| Closing (this step)          | …                         | …     |
```

## Close Not Ready (Step 4)

```
## Close Not Ready

Blocked: [step name(s)]
Reason: [bookkeeper's stated reason]

We didn't pull the final reports. Clear the blocked step(s), then run
this skill again once each is Done or Accepted with open items.
```

## Outstanding Items in This Package (Step 6)

```
## Outstanding Items in This Package

| Step | Status | Open Item |
|------|--------|-----------|
| …    | Accepted with open items | … |

(If none: "Nothing was accepted with open items, every step was fully
Done.")
```
