import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";import{t as n}from"./jsx-runtime-BapUIyWk.js";var r=e(t(),1),i=n(),a={xxs:`var(--spacing-1)`,xs:`var(--spacing-2)`,sm:`var(--spacing-3)`,ms:`var(--spacing-4)`,md:`var(--spacing-5)`,lg:`var(--spacing-6)`,xl:`var(--spacing-8)`,xxl:`var(--spacing-12)`},o=r.forwardRef(({direction:e=`row`,wrap:t=`nowrap`,justify:n=`flex-start`,align:r=`center`,gap:o=0,style:s,children:c,...l},u)=>{
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

Stays in BUI rather than ui-common (FR-4087): it is the frozen antd `Flex`
vocabulary (`direction`, `justify`, `gap="sm"`) of ~290 call sites, and
Astryx `Stack`/`HStack`/`VStack` already own the role for new code.
*/
let d=e=>e===void 0?`0px`:typeof e==`string`?a[e]:`${e}px`,f=Array.isArray(o)?`${d(o[0])} ${d(o[1])}`:typeof o==`number`?o:d(o),p=[n,r].map(e=>{let t;switch(e){case`start`:t=`flex-start`;break;case`end`:t=`flex-end`;break;case`between`:t=`space-between`;break;case`around`:t=`space-around`;break;default:t=e}return t}),m={display:`flex`,flexDirection:e,flexWrap:t,justifyContent:p[0],alignItems:p[1],...s};return(0,i.jsx)(`div`,{ref:u,style:{alignItems:`stretch`,border:`0 solid black`,boxSizing:`border-box`,display:`flex`,flexBasis:`auto`,flexDirection:`column`,flexShrink:0,listStyle:`none`,margin:0,minHeight:0,minWidth:0,padding:0,position:`relative`,textDecoration:`inherit`,gap:f,...m},...l,children:c})});o.displayName=`BAIFlex`;export{o as t};
