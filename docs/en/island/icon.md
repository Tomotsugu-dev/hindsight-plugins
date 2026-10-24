# icon: Icon

![icon](../../images/island/icon.svg)

The illustration shows the closed island on the left and the open island on the right.

```json
{ "type": "icon", "name": "Code", "color": "#a78bfa" }
```

| Field | Required? | Description |
|---|---|---|
| `name` | Yes | Icon name; see below |
| `color` | No | `#rrggbb`; defaults to white |

## Allowed positions

| Position | Size |
|---|---|
| `closed.left`, `closed.right` | 14 pixels. A side containing only an icon is circular |
| `open.left`, `open.right` | 22 pixels |

## Icon names

- Category icons, matching `icon` returned by `categories.list`: `Code` `Terminal` `Database` `GitBranch` `Bug` `Server` `Cloud` `Bot` `Globe` `Search` `Compass` `Newspaper` `Rss` `MessageCircle` `MessagesSquare` `Mail` `CalendarDays` `Briefcase` `FileText` `Table2` `Presentation` `NotebookPen` `PenLine` `Calculator` `ChartLine` `Brush` `Palette` `PenTool` `Box` `Image` `Camera` `Clapperboard` `Gamepad2` `Music` `Headphones` `Mic` `Film` `Video` `Tv` `GraduationCap` `BookOpen` `Languages` `Heart` `Coffee` `Dumbbell` `ShoppingCart` `Wallet` `Download` `FolderOpen` `HardDrive` `Shield` `Lock` `Activity` `Clock` `Wrench` `Sparkles` `Monitor` `MoreHorizontal` `EyeOff` `Tag`
- Icons for buttons: `Play` `Pause` `Square` `SkipForward` `RotateCcw` `Check` `X` `Plus` `Minus`
- Both `icon` and [`button`](button.md) can use either group. Names match the [Lucide](https://lucide.dev/icons/) icon library.
- Unknown names display as `Tag` without an error.

## Length limits

- `name` must be nonempty and at most 64 bytes.
