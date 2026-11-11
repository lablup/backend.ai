import{t as e}from"./jsx-runtime-BapUIyWk.js";import{u as t}from"./Skeleton-D35z7Ria.js";import{t as n}from"./Badge-8q4sdq1t.js";var r=e();function i({values:e=[]}){if(e.length===0)return null;let i=e.map(e=>typeof e==`string`?{label:e,variant:`neutral`}:e);return(0,r.jsx)(t,{gap:0,align:`center`,className:`uic-double-badge`,children:i.map((e,t)=>e.label?(0,r.jsx)(n,{className:`uic-double-badge__item`,variant:e.variant??`neutral`,label:e.label},t):null)})}i.displayName=`DoubleBadge`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

ui-common `DoubleBadge` under its BUI name; the props are identical. The
settled counterpart is `BAIDoubleToken`.
*/
var a=i;export{a as t};
