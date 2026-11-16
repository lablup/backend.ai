import{dn as e}from"./icons-Btg1s2wy.js";import{t}from"./jsx-runtime-BapUIyWk.js";import{R as n,d as r}from"./usePressFeedback-BIoIGSxE.js";import{S as i}from"./Modal2-DnaQJkP1.js";import{t as a}from"./IconButton-DGkWhkpU.js";import{u as o}from"./Skeleton-D35z7Ria.js";var s=t();function c({count:e,onClear:t,label:c,clearLabel:l,clearIcon:u}){let d=i();if(e<=0)return null;let f=l??d(`uic.SelectionLabel.clear`);return(0,s.jsxs)(o,{gap:1,align:`center`,children:[(0,s.jsx)(n,{children:c??d(`uic.SelectionLabel.selectedCount`,{count:e})}),t?(0,s.jsx)(a,{variant:`ghost`,size:`sm`,icon:u??(0,s.jsx)(r,{icon:`close`}),label:f,tooltip:f,onClick:t}):null]})}c.displayName=`SelectionLabel`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

Adapter over ui-common `SelectionLabel` (FR-4054): keeps `onClearSelection`
and the CircleX clear glyph. The strings come from ui-common's catalog.
*/
var l=({onClearSelection:t,clearIcon:n=(0,s.jsx)(e,{}),...r})=>{"use memo";return(0,s.jsx)(c,{...r,clearIcon:n,onClear:t})};export{l as t};
