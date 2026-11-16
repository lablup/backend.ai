import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";import{t as n}from"./jsx-runtime-BapUIyWk.js";var r=e(t(),1),i=n(),a=e=>e.replace(/[\\^$.*+?()[\]{}|]/g,`\\$&`);function o({children:e,keyword:t,className:n,highlightStyle:r}){if(!e)return null;let o=[`uic-text-highlighter`,n].filter(Boolean).join(` `);if(!t)return(0,i.jsx)(`span`,{className:o,children:e});let s=t.toLowerCase(),c=e.split(RegExp(`(${a(t)})`,`gi`));return(0,i.jsx)(`span`,{className:o,children:c.map((e,t)=>e.toLowerCase()===s?(0,i.jsx)(`span`,{className:`uic-text-highlighter__match`,style:r,children:e},t):e)})}var s=(0,r.memo)(o);s.displayName=`TextHighlighter`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

ui-common `TextHighlighter` under its BUI name (FR-4096); `style` styles each
mark. The mark colour is the theme's `--color-warning-border-hover`, which
ui-common reads itself.
*/
var c=({children:e,keyword:t,style:n})=>(0,i.jsx)(s,{keyword:t,highlightStyle:n,children:e});export{s as n,c as t};
