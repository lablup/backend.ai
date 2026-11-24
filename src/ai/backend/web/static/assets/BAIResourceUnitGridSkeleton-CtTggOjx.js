import{t as e}from"./jsx-runtime-BapUIyWk.js";import{t}from"./VStack-DaUzGF31.js";import{t as n,u as r}from"./Skeleton-D35z7Ria.js";var i=e(),a=3,o=[140,180,100],s=`var(--size-element-sm)`,c=5,l=10,u=40,d=12,f=[[`45%`,`25%`],[`30%`,`40%`],[`55%`,`20%`]],p=`var(--size-element-sm)`;function m({rows:e=a,className:m,...h}){let g=0;return(0,i.jsxs)(t,{gap:3,align:`stretch`,className:[`uic-unit-grid-skeleton`,m].filter(Boolean).join(` `),...h,children:[(0,i.jsx)(r,{gap:3,align:`center`,children:o.map((e,t)=>(0,i.jsx)(n,{width:e,height:s,radius:2,index:g++},t))}),(0,i.jsx)(r,{gap:3,wrap:`wrap`,align:`center`,children:Array.from({length:c},(e,t)=>(0,i.jsxs)(r,{gap:1,align:`center`,children:[(0,i.jsx)(n,{width:l,height:l,radius:1,index:g++}),(0,i.jsx)(n,{width:u,height:d,radius:1,index:g++})]},t))}),Array.from({length:Math.max(0,e)},(e,t)=>{let a=f[t%f.length];return(0,i.jsx)(r,{gap:3,align:`center`,className:`uic-unit-grid-skeleton__row`,children:a.map((e,t)=>(0,i.jsx)(n,{width:e,height:p,radius:1,index:g++},t))},t)})]})}m.displayName=`UnitGridSkeleton`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

ui-common `UnitGridSkeleton` under its BUI name (FR-3569): the Suspense
fallback for `BAIResourceUnitGrid`.
*/
var h=m;export{h as t};
