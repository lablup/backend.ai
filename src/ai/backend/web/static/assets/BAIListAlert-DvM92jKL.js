import{t as e}from"./compiler-runtime-CZQb2eIb.js";import{t}from"./jsx-runtime-BapUIyWk.js";import{t as n}from"./Banner-ElTQ2msG.js";import{U as r}from"./index-49VU5B_r.js";var i=t(),a=165;function o({title:e,items:t,maxHeight:r=a,...o}){let s=t.length===0?void 0:(0,i.jsx)(`ul`,{tabIndex:0,className:`uic-list-banner__list`,style:{"--list-banner-max-height":typeof r==`number`?`${r}px`:r,listStyle:`circle inside`},children:t.map((e,t)=>(0,i.jsx)(`li`,{children:e.content},e.key??`__index-${t}`))}),c=e!=null;return(0,i.jsx)(n,{...o,title:c?e:s,description:c?s:void 0})}o.displayName=`ListBanner`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

ui-common `ListBanner` under its BUI name (FR-4096), with BAIAlert's
antd-shaped props mapped the way BAIAlert maps them (`toBannerProps`).
*/
var s=e(),c=e=>{"use memo";let t=(0,s.c)(10),n,a,c;if(t[0]!==e){let{items:i,maxHeight:o,...s}=e;n=i,a=o,c=r(s),t[0]=e,t[1]=n,t[2]=a,t[3]=c}else n=t[1],a=t[2],c=t[3];let l;if(t[4]!==c){let{description:e,...n}=c;l=n,t[4]=c,t[5]=l}else l=t[5];let u;return t[6]!==l||t[7]!==n||t[8]!==a?(u=(0,i.jsx)(o,{...l,items:n,maxHeight:a}),t[6]=l,t[7]=n,t[8]=a,t[9]=u):u=t[9],u};export{c as t};
