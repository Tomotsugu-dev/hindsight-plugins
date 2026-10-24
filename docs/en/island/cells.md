# cells: Cells

![cells](../../images/island/cells.svg)

Cells are available only when the island is open. The illustration has 14 cells, 10 per row, with the eighth cell marked as current. A focus plugin could use one cell for each focus session today, colored by its category.

```json
{
  "type": "cells",
  "colors": ["#a78bfa", "#a78bfa", "#a78bfa", "#a78bfa", "#a78bfa", "#f87171", "#a78bfa", "#a78bfa", null, null, null, null, null, null],
  "columns": 10,
  "current": 7
}
```

| Field | Required? | Description |
|---|---|---|
| `colors` | Yes | One `#rrggbb` color per cell; use `null` for an empty cell |
| `columns` | Yes | Number of cells per row |
| `current` | No | Zero-based index of the current cell, outlined in white |

- Cells are at most 10 pixels wide. They shrink if they do not fit on the island.

## Allowed positions

- `open.left`, `open.right`.

## Count limits

Calls that violate these limits fail:

- `columns` must be from 1 to 20.
- At most three rows, so `colors` has at most 60 entries. `colors` cannot be empty.
- `current` must refer to a cell in `colors`.
