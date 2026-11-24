import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";import{t as n}from"./jsx-runtime-BapUIyWk.js";import{t as r}from"./Tooltip-QQJy2agO.js";import{R as i}from"./usePressFeedback-BIoIGSxE.js";var a=e(t(),1),o=6;function s(e,t,n){if(e!=null&&typeof e!=`boolean`){if(typeof e==`string`){e.trim()!==``&&n.push(e);return}if(typeof e==`number`){n.push(String(e));return}if(!(t>=o)){if(Array.isArray(e)){for(let r of e)s(r,t+1,n);return}if((0,a.isValidElement)(e)){let r=e.props;s(r==null?void 0:r.children,t+1,n)}}}}function c(e){let t=[];return s(e,0,t),t.join(` `).replace(/\s+/g,` `).trim()}var l=n();function u({icon:e,focusable:t=!0,style:n,className:a,...o}){let s=c(o.content)||void 0,u=(0,l.jsx)(i,{color:`placeholder`,className:`uic-icon-with-tooltip__icon`,children:e}),d=e=>[`uic-icon-with-tooltip`,e,a].filter(Boolean).join(` `);return(0,l.jsx)(r,{...o,children:t?(0,l.jsx)(`button`,{type:`button`,"aria-label":s,className:d(`uic-icon-with-tooltip--button`),style:n,children:u}):(0,l.jsx)(`span`,{"aria-label":s,className:d(``),style:n,children:u})})}u.displayName=`IconWithTooltip`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

ui-common `IconWithTooltip` under its BUI name; the props are identical
(every Tooltip prop, with the text of `content` naming the trigger).
`BAIQuestionIconWithTooltip` specializes it with the CircleHelp glyph.
*/
var d=u;export{u as n,d as t};
