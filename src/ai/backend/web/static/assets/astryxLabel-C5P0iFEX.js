import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";var n=e(t(),1),r=6,i=(e,t,a)=>{
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

Accessible-name helper for the antd -> Astryx migration (to-astryx phase 3,
wave 2 / ticket W2-D).

Astryx's universal contract #1: `label` is a **required `string`** that the
control renders (or announces) itself. antd took a `ReactNode` in the same
slot — `children`, `title`, `text`, `label` — so every frontier wrapper that
keeps an antd-shaped surface has to flatten a node into a name.

Casting `node as string` compiles, renders, and poisons `aria-label` with
`[object Object]` (P2). This module does the flattening properly: it walks
string/number leaves through fragments, arrays and elements and joins them.
A node built only from non-textual leaves (an icon, an `<img>`) yields `''`,
which callers must treat as "no name available" — either `isLabelHidden` plus
an `endContent` render (Token/Badge), or an explicit translated fallback.

The walk also cannot see PROP-carried text (`Badge label=`, `BAIDoubleToken
values=`) — such call sites name the text explicitly instead (`title` on
`BAISelect`'s options path, `label` on its children carrier — FR-3544).
*/
if(e!=null&&typeof e!=`boolean`){if(typeof e==`string`)e.trim()!==``&&a.push(e);else if(typeof e==`number`)a.push(String(e));else if(!(t>=r)){if(Array.isArray(e))e.forEach(e=>i(e,t+1,a));else if(n.isValidElement(e)){let n=e.props;i(n==null?void 0:n.children,t+1,a)}}}},a=e=>{let t=[];return i(e,0,t),t.join(` `).replace(/\s+/g,` `).trim()},o=(...e)=>{for(let t of e){let e=a(t??null);if(e!==``)return e}return``};export{o as n,a as t};
