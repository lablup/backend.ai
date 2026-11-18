import{pn as e}from"./icons-Btg1s2wy.js";import{t}from"./jsx-runtime-BapUIyWk.js";import{t as n}from"./BAIIconWithTooltip-uPQTnQkb.js";import{t as r}from"./astryxPlacement-BES-gjz7.js";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

`BAIQuestionIconWithTooltip` on Astryx (to-astryx phase 3, wave 2 / W2-D).

FRONTIER COMPONENT — 63 call sites in 30 files, all of which pass antd's
`title`. The public surface stays antd-shaped (`title`, `placement`, `open`,
`style`) and the antd `TooltipProps` import is replaced by a locally-declared
interface, so this module drops out of the antd import graph (P15).

`title`     -> Astryx `content`  (MAPPING §4)
`placement` -> `placement` + `alignment`, split via `helper/astryxPlacement`

PILOT-DECISION — **the glyph tint moves from a token read to `Text`'s own
colour scale.** antd painted it `color: token('--color-text-tertiary')` from the
theme-shim; Astryx has no arbitrary colour slot (P5), and the nearest member
of its closed `TextColor` enum is `placeholder` (the tertiary/hint step). The
icon is wrapped in a `Text color="placeholder"` so it inherits that step from
the theme in both light and dark instead of a resolved hex — and the
theme-shim `useToken()` call disappears, which is the shim's idiomatic end
state.

PILOT-DECISION — **the rest of antd's `TooltipProps` is dropped, not
translated.** `color` has no Astryx counterpart (MAPPING §4), and
`overlayStyle` / `overlayInnerStyle` / `getPopupContainer` / `trigger` /
`mouseEnterDelay` describe antd's overlay DOM, which Astryx replaces with CSS
anchor positioning + the Popover API. No call site passes any of them
(measured: `title` ×63, `placement` ×3, `style` ×2, `iconProps` ×2).

The trigger mechanics (focusable reset button, FR-3589 anchor-name note) live
in the generic base, `BAIIconWithTooltip`, which this component renders with
the antd surface translated to Astryx's native prop names at the boundary.
*/
var i=t(),a=({title:t,placement:a,open:o,onOpenChange:s,mouseEnterDelay:c,style:l,className:u,iconProps:d,focusable:f})=>{let{placement:p,alignment:m}=r(a);return(0,i.jsx)(n,{icon:(0,i.jsx)(e,{...d,size:`1em`}),content:t,placement:p,alignment:m,isOpen:o,onOpenChange:s,delay:c===void 0?void 0:c*1e3,style:l,className:u,focusable:f})};export{a as t};
