# Data Model: Parlay Tracker

## Stored: `src/belt/data/parlays.json`

Hand-edited (by Claude, for the LM). Parlays in any order; the tab sorts them.

```json
{
  "parlays": [
    {
      "season": 2026,
      "week": 10,
      "lsp": "Tate hathaway",
      "category": "NFL RB anytime TD only",
      "payout": null,
      "legs": [
        {"member": "Taylor Basso", "pick": "Bijan Robinson anytime TD", "odds": -150, "result": "W"},
        {"member": "Tate hathaway", "pick": "Derrick Henry anytime TD", "odds": -200, "result": null}
      ]
    }
  ]
}
```

### Parlay

| Field | Type | Notes |
|-------|------|-------|
| `season` | int | Season year, e.g. 2026. |
| `week` | int | NFL week of the games bet on: the week after the LSP's loss. |
| `lsp` | string | The LSP's name, as the other tabs show it. |
| `category` | string | Free text, as the LSP said it. |
| `payout` | number or null | Dollars paid if it hit. Null otherwise, or if unknown. |
| `legs` | list of Leg | One per member, eight in all. |

### Leg

| Field | Type | Notes |
|-------|------|-------|
| `member` | string | Who picked it, as the other tabs show their name. |
| `pick` | string | Free text, as written on the slip. |
| `odds` | int or null | American odds, e.g. -150 or 240. Null if unknown (backfills). |
| `result` | `"W"`, `"L"` or null | Null until graded. |

No validation: the file is written by hand and the league polices itself.

## Worked out per request (in `parlays.py`)

- **Parlay result**: `"busted"` if any leg is L, `"hit"` if every leg is W, else `"pending"`.
- **Sole loser** of a parlay: the member whose leg is the only L, when every leg is graded.
  None otherwise.
- **MemberStats** (one per member seen in any leg): `name`, `wins`, `losses`, `hit_rate`
  (wins ÷ graded, None with nothing graded), `expected_rate` (average implied chance of graded
  legs with odds, None if there are none), `kills` (parlays where they were the sole loser).
- **Summary**: settled parlays (hit or busted), hits, and total payout of hits.
