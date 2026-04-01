# Adding Custom Fonts

This document explains how to add new fonts under `resources/fonts/`.

## How It Works

The application parses the `fontFamily` value from `theme.json` and **automatically loads** the corresponding CSS file for each font name.

```
theme.json fontFamily: "MyFont, 'Ubuntu', Roboto, sans-serif"
                          │         │        │
                          ▼         ▼        ▼
        resources/fonts/myfont/myfont.css
        resources/fonts/ubuntu/ubuntu.css
        resources/fonts/roboto/roboto.css
```

Auto-loading rules (from `injectFontCSS` in `customThemeConfig.ts`):

1. Split the `fontFamily` string by `,`
2. Normalize each name to **lowercase with spaces replaced by hyphens** (e.g. `My Custom Font` → `my-custom-font`)
3. Inject a `<link>` tag into `<head>` pointing to `resources/fonts/{normalized-name}/{normalized-name}.css`
4. Generic families like `sans-serif`, `monospace`, etc. are ignored

> **Key rule**: The font directory name and CSS file name must match the normalized form of the font name.

---

## Case 1: Font Distributed with CSS

This applies to fonts that already include a CSS file (e.g. Google Fonts downloads, open-source font packages).

### Steps

1. **Create a directory** using the normalized name.

   ```
   resources/fonts/{normalized-name}/
   ```

2. **Place the files** — copy the provided CSS and font files as-is.

   ```
   resources/fonts/my-custom-font/
   ├── my-custom-font.css      ← entry CSS (name must match)
   ├── woff2/
   │   ├── MyCustomFont-Regular.woff2
   │   ├── MyCustomFont-Bold.woff2
   │   └── ...
   └── woff/
       └── ...
   ```

3. **Verify CSS file name** — the entry CSS file must be named `{normalized-name}.css`.
   - If the provided CSS has a different name, either **rename it** or create a wrapper CSS that `@import`s the original.

4. **Verify internal paths** — ensure `url()` paths inside the CSS point to the correct file locations.

   ```css
   /* Use relative paths */
   src: url(./woff2/MyCustomFont-Regular.woff2) format('woff2');
   ```

### Example: Roboto (distributed with woff2/woff)

```
resources/fonts/roboto/
├── roboto.css                        ← entry CSS
├── roboto-v19-latin-regular.woff2
├── roboto-v19-latin-regular.woff
├── roboto-v19-latin-100.woff2
└── ...
```

```css
/* roboto.css */
@font-face {
  font-family: 'Roboto';
  font-style: normal;
  font-weight: 400;
  src: local('Roboto'), local('Roboto-Regular'),
    url('./roboto-v19-latin-regular.woff2') format('woff2'),
    url('./roboto-v19-latin-regular.woff') format('woff');
}
```

---

## Case 2: Font Files Only (No CSS Provided)

This applies when you only have raw font files (ttf, otf, woff2, etc.) without a CSS file.

### Steps

1. **Create a directory**

   ```
   resources/fonts/{normalized-name}/
   ```

2. **Place the font files**

   ```
   resources/fonts/my-custom-font/
   ├── MyCustomFont-Thin.ttf
   ├── MyCustomFont-Regular.ttf
   ├── MyCustomFont-Bold.ttf
   └── ...
   ```

3. **Write a CSS file** — create `{normalized-name}.css` with `@font-face` declarations for each weight.

### Writing `@font-face` Rules

```css
@font-face {
  font-family: 'FontName';       /* Must match the name used in theme.json */
  font-weight: 400;              /* Use numeric weight values */
  font-display: swap;            /* Swap after loading to avoid invisible text */
  src: local('FontName Regular'),  /* Use system-installed version if available */
    url(./FontName-Regular.ttf) format('truetype');
}
```

#### Font Weight Reference

| Weight | Name        | Typical Use      |
|--------|-------------|------------------|
| 100    | Thin        |                  |
| 200    | ExtraLight  |                  |
| 300    | Light       | Secondary text   |
| 400    | Regular     | Body text        |
| 500    | Medium      |                  |
| 600    | SemiBold    |                  |
| 700    | Bold        | Emphasis         |
| 800    | ExtraBold   |                  |
| 900    | Black       | Headings         |

#### Format Values

| Extension | Format Value               |
|-----------|----------------------------|
| .woff2    | `format('woff2')`          |
| .woff     | `format('woff')`           |
| .ttf      | `format('truetype')`       |
| .otf      | `format('opentype')`       |

#### Source Priority (when multiple formats are available)

```css
src: local('FontName Regular'),
  url(./font.woff2) format('woff2'),      /* smallest file, highest priority */
  url(./font.woff) format('woff'),        /* fallback */
  url(./font.ttf) format('truetype');     /* last resort */
```

### Example: ttf-only Font

```
resources/fonts/my-custom-font/
├── my-custom-font.css           ← manually written
├── MyCustomFont-Thin.ttf
├── MyCustomFont-Light.ttf
├── MyCustomFont-Regular.ttf
├── MyCustomFont-Medium.ttf
├── MyCustomFont-Bold.ttf
└── MyCustomFont-Black.ttf
```

```css
/* my-custom-font.css */
@font-face {
  font-family: 'My Custom Font';
  font-weight: 400;
  font-display: swap;
  src: local('My Custom Font Regular'),
    url(./MyCustomFont-Regular.ttf) format('truetype');
}

@font-face {
  font-family: 'My Custom Font';
  font-weight: 700;
  font-display: swap;
  src: local('My Custom Font Bold'),
    url(./MyCustomFont-Bold.ttf) format('truetype');
}

/* ... repeat for remaining weights */
```

---

## Applying in theme.json

After placing font files and CSS, add the font name to `fontFamily` in `resources/theme.json`.

```jsonc
{
  "light": {
    "token": {
      "fontFamily": "My Custom Font, 'Ubuntu', Roboto, sans-serif"
      //              ↑ earlier in the list = higher priority
    }
  },
  "dark": {
    "token": {
      "fontFamily": "'Ubuntu', Roboto, sans-serif"
      // light and dark can have different fontFamily values
    }
  }
}
```

> CSS files are auto-loaded based on the names listed in `fontFamily`. No manual `<link>` tags or code changes are required.

---

## Checklist

- [ ] Directory name matches the normalized font name (lowercase, spaces → hyphens)
- [ ] CSS file is named `{directory-name}.css`
- [ ] `font-family` in `@font-face` matches the name used in `theme.json`
- [ ] `url()` paths in CSS point to the correct font file locations
- [ ] For new fonts, `font-display: swap` is set on all `@font-face` rules (recommended; some legacy fonts in this repo may not yet include it)
- [ ] Font name is added to `fontFamily` in `theme.json`

## Currently Registered Fonts

| Directory       | CSS Entry            | Notes                          |
|-----------------|----------------------|--------------------------------|
| `roboto/`       | `roboto.css`         | woff2/woff, CSS included       |
| `ubuntu/`       | `ubuntu.css`         | woff2/woff, CSS included       |
