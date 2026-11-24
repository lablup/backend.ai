/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

antd placement -> Astryx `placement` + `alignment` (to-astryx phase 3,
wave 2 / ticket W2-D).

MAPPING §4: antd's single compound `placement` (`top`, `topLeft`,
`bottomRight`, …) **splits into two props** everywhere in Astryx — `Tooltip`,
`Popover`, `HoverCard`, `DropdownMenu` all take `placement` (the axis) plus
`alignment` (the position along it). The axis vocabulary changes too:
`top|bottom|left|right` -> `above|below|start|end`.

Frontier wrappers that keep an antd-shaped `placement` prop route it through
here rather than each restating the 12-value table.
*/
var e={top:`above`,bottom:`below`,left:`start`,right:`end`},t=t=>{if(!t)return{};let n=/^(top|bottom|left|right)(Left|Right|Top|Bottom)?$/.exec(t);if(!n)return{};let r=e[n[1]],i=n[2];return{placement:r,alignment:i===`Left`||i===`Top`?`start`:i===`Right`||i===`Bottom`?`end`:void 0}};export{t};
