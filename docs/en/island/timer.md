# timer: Countdown

![timer](../../images/island/timer.svg)

The illustration shows the closed island on the left and the open island on the right, both a quarter of the way through the countdown. The ring shrinks over time, and the remaining time appears beside it: `h:mm:ss` for one hour or more, or `m:ss` for less than an hour.

```json
{ "type": "timer", "start": "2026-10-21T10:00:00+09:00", "end": "2026-10-21T10:25:00+09:00", "color": "#fb923c" }
```

| Field | Required? | Description |
|---|---|---|
| `start` | Yes | Start time in RFC 3339, like `at` in a `focus.changed` event |
| `end` | Yes | End time in the same format |
| `pausedAt` | No | Pause time in the same format. If present, the display freezes at the time remaining then |
| `color` | No | Ring color as `#rrggbb`; defaults to white |

- Hindsight runs the countdown itself; the plugin need not call `island.show` every second.
- To pause, call `island.show` again with `pausedAt` on the timer.
- To resume, move both `start` and `end` forward by the duration of the pause, remove `pausedAt`, and call again. Moving only `end` changes the total duration and makes the ring inaccurate.
- At zero, the timer stays at zero until the plugin changes the content.

## Allowed positions

| Position | Appearance |
|---|---|
| `closed.left`, `closed.right` | 14-pixel ring and small text |
| `open.left`, `open.right` | 20-pixel ring and large text |

## Value limits

Calls that violate these limits fail:

- `start` must be before `end`.
- `pausedAt` must be between `start` and `end`.
