# button: Button

![button](../../images/en/island/button.svg)

Buttons are available only when the island is open. The left button in the illustration has an icon only; the right one has an icon and text.

```json
{ "type": "button", "id": "pause", "icon": "Pause" }
```

```json
{ "type": "button", "id": "skip", "icon": "SkipForward", "text": "Skip" }
```

| Field | Required? | Description |
|---|---|---|
| `id` | Yes | Name chosen by the plugin, returned unchanged when the button is clicked |
| `icon` | Yes | Icon name, the same as an [`icon`](icon.md) component's `name` |
| `text` | No | Text on the button |

When the button is clicked, the background script receives an `island.clicked` event containing `{ "button": "<id>" }`. Clicking a button does not open the plugin's page.

```js
hindsight.on("island.clicked", ({ button }) => {
  if (button === "pause") {
    // Pause
  }
});
```

Only a plugin running in the background can place a button. Without a background script, it cannot receive clicks, so `island.show` fails.

## Allowed positions

- `open.left`, `open.right`.

## Length limits

- `id` must be nonempty and at most 64 bytes.
- `text` must be nonempty and at most 20 display units wide, as calculated in [text](text.md). It cannot contain control characters such as a newline.
