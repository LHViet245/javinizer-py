# Design Specifications: Javinizer Liquid Glass UI

**Style:** Liquid Glass / Apple macOS Future
**Theme:** Dark Mode + Neon Accents (Purple/Cyan/Pink)

## 🎨 Color Palette

| Name | Hex | Usage |
|------|-----|-------|
| **Background** | `#0f0c29` -> `#302b63` | Main gradient background (Deep Purple/Blue) |
| **Glass Surface** | `rgba(255, 255, 255, 0.05)` | Panels, Cards (needs backdrop-filter: blur) |
| **Glass Border** | `rgba(255, 255, 255, 0.1)` | 1px border for definition |
| **Primary** | `#00d2ff` | Primary Actions (Sort, Apply), Active States (Cyan) |
| **Secondary** | `#9d50bb` | Accents, Tags, Highlights (Neon Purple) |
| **Text Primary** | `#ffffff` | Headings, Main text |
| **Text Muted** | `#aeb2b8` | Descriptions, Secondary info |
| **Danger** | `#ff416c` | Delete, Errors |
| **Success** | `#00f260` | Progress completion, Success states |

## 🪄 Glassmorphism CSS Snippet

```css
.glass-panel {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
}
```

## 📐 Layout & Spacing

- **Sidebar (Left):** 280px fixed. Glass panel.
- **Main Content (Center):** Flexible. Glass cards grid.
- **Inspector (Right):** 350px fixed. Glass panel.
- **Radius:** `xl` (16px) for panels, `lg` (12px) for cards, `full` (9999px) for buttons/pills.

## 🧩 Components Mapping (vs Original GUI)

### 1. File Explorer & Selection (Left Panel)

* **Original:** `/Input/Path` text input.
- **New Design:** Recursive Folder Tree.
  - *Features:* Expand/Collapse folders, Multi-select files.
  - *Controls:* "Scan Recursive" toggle (top of tree).

### 2. Operations Toolbar (Top Area)

* **Original:** Checkboxes (Update, Strict, Force, Interactive).
- **New Design:** "Control Deck" - A horizontal glass strip.
  - *Toggle Switches:* iOS-style toggles for options.
  - *Action Buttons:* "Dry Run" (Ghost button), "Start Processing" (Gradient Primary button).

### 3. Main Data Grid (Center Area)

* **Original:** Table with Name, Size, Modified.
- **New Design:** Hybrid View (Switchable).
  - *List Mode:* Clean table with sticky headers.
  - *Grid Mode:* Card view showing auto-scraped Cover Art + ID.
  - *Status Indicators:* Glowing dot (Green=Ready, Yellow=Processing, Red=Error).

### 4. Metadata Inspector (Right Panel)

* **Original:** "Aggregated Data" form.
- **New Design:** "Movie Card" Details.
  - *Cover Art:* Top, large, with reflection.
  - *Fields:* Editable inputs with floating labels (Title, ID, Year).
  - *Tags:* Clickable pills (Genre, Maker).
  - *Actresses:* Circular avatars row.
  - *Action Footer:* "Apply Changes", "Reset", "JSON View" buttons at bottom of panel.

### 5. Log & Progress (Bottom Area)

* **Original:** N/A (Console window only).
- **New Design:** "Terminal HUD".
  - Collapsible bottom drawer.
  - Real-time streaming text (green monospace).
  - Global Progress Bar (neon gradient).

## 🖼️ Iconography

* Use **Lucide Icons** (clean, consistent stroke).
- *Mapping:*
  - Settings -> `Settings`
  - Sort -> `Wand2`
  - Folder -> `FolderOpen`
  - File -> `FileVideo`
  - Search -> `Search`
