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
*/const s={top:"above",bottom:"below",left:"start",right:"end"},r=e=>{if(!e)return{};const o=/^(top|bottom|left|right)(Left|Right|Top|Bottom)?$/.exec(e);if(!o)return{};const n=s[o[1]],t=o[2];return{placement:n,alignment:t==="Left"||t==="Top"?"start":t==="Right"||t==="Bottom"?"end":void 0}};export{r as s};
//# sourceMappingURL=astryxPlacement-BxR6_qos.js.map
