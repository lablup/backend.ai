import{vn as e}from"./icons-Btg1s2wy.js";import{t}from"./jsx-runtime-BapUIyWk.js";import{t as n}from"./BAIIconWithTooltip-uPQTnQkb.js";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

`BAIAlertIconWithTooltip` on Astryx (to-astryx phase 3, ticket A).

A hover-explained warning/error glyph. antd `Tooltip` -> Astryx `Tooltip`
(MAPPING §4, DIRECT): `title` -> `content`, `placement` splits into
`placement` + `alignment`. The public surface keeps antd's `title`, so the 9
call sites in 5 files do not change.

The icon colour is the one thing Astryx's closed enums cannot carry (the glyph
is a bare lucide SVG, not an Astryx component), so it reads the status token
directly — `--color-warning` / `--color-error` are the same seeds antd's
`colorWarning` / `colorError` resolved to, so the hue is legacy-identical in
both modes (P19: names checked against the built theme).
*/
var r=t(),i=({iconProps:t,type:i,title:a,placement:o})=>(0,r.jsx)(n,{content:a,placement:o,icon:(0,r.jsx)(e,{style:{color:i===`warning`?`var(--color-warning)`:i===`error`?`var(--color-error)`:void 0},...t})});export{i as t};
