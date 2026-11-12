import{t as e}from"./compiler-runtime-CZQb2eIb.js";import{t}from"./jsx-runtime-BapUIyWk.js";import{u as n}from"./Skeleton-D35z7Ria.js";import{t as r}from"./Token-D5_yAVQ_.js";import{t as i}from"./BAIText-CtDfjLnS.js";import{n as a,t as o}from"./BAITextHighlighter-D8LVcDhu.js";var s=t();function c({values:e=[],highlightKeyword:t}){if(e.length===0)return null;let i=e.map(e=>typeof e==`string`?{label:e,color:`blue`}:e),o=t!==void 0;return(0,s.jsx)(n,{gap:0,align:`center`,className:`uic-double-token`,children:i.map((e,n)=>{if(!e.label)return null;let i=e.endContent===void 0?o?(0,s.jsx)(a,{keyword:t,children:e.label}):void 0:e.endContent;return(0,s.jsx)(r,{className:`uic-double-token__item`,color:e.color??`blue`,label:e.label,isLabelHidden:i!==void 0,endContent:i},n)})})}c.displayName=`DoubleToken`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

ui-common `DoubleToken` under its BUI name (FR-4096): a welded run of Tokens
for a settled pair; the live counterpart is `BAIDoubleBadge`.
*/
var l=e(),u=e=>{"use memo";let t=(0,l.c)(11),n,r,a;t[0]===e?(n=t[1],r=t[2],a=t[3]):({values:a,highlightKeyword:n,...r}=e,t[0]=e,t[1]=n,t[2]=r,t[3]=a);let u;t[4]!==n||t[5]!==a?(u=a==null?void 0:a.map(e=>{if(typeof e==`string`)return e;let{copyable:t,...r}=e;return!t||r.endContent!==void 0?r:{...r,endContent:(0,s.jsx)(i,{copyable:{text:r.label},inheritColor:!0,children:n===void 0?r.label:(0,s.jsx)(o,{keyword:n,children:r.label})})}}),t[4]=n,t[5]=a,t[6]=u):u=t[6];let d=u,f;return t[7]!==n||t[8]!==r||t[9]!==d?(f=(0,s.jsx)(c,{...r,highlightKeyword:n,values:d}),t[7]=n,t[8]=r,t[9]=d,t[10]=f):f=t[10],f};export{u as t};
