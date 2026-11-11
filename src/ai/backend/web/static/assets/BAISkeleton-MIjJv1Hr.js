import{t as e}from"./jsx-runtime-BapUIyWk.js";import{t}from"./VStack-DaUzGF31.js";import{t as n,u as r}from"./Skeleton-D35z7Ria.js";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

antd-parity skeleton composed from Astryx's single-box `Skeleton`: antd's
multi-part shimmer (title + paragraph rows, avatar, input/button shapes)
collapses onto `variant` + `rows`/`hasTitle`/`hasAvatar`. `active` is dropped
as a prop (Astryx skeletons are always animated); `block` is dropped (Astryx
already defaults `width: '100%'`). Mapping evidence: MAPPING.md §"Also
COMPOSITION" (FR-3482); moved here from react/src/components/astryx-bui in
FR-3513 so BUI components (e.g. `BAIModal`'s loading body) can share it.

Standard pairing (`use-bai-card.md`): the Suspense fallback INSIDE a card
body, so the header stays visible while the body loads.
*/
var i=e(),a={small:`var(--size-element-sm)`,default:`var(--size-element-md)`,large:`var(--size-element-lg)`},o=16,s=4,c=`61%`,l=`38%`,u=32,d={small:48,default:64,large:80},f=({variant:e=`paragraph`,rows:f=3,hasTitle:p=!0,hasAvatar:m=!1,size:h=`default`,radius:g=1,width:_,height:v,startIndex:y=0,...b})=>{"use memo";if(e===`block`)return(0,i.jsx)(n,{width:_,height:v,radius:g,index:y,...b});if(e===`input`||e===`button`)return(0,i.jsx)(n,{width:_??(e===`button`?d[h]:`100%`),height:v??a[h],radius:g,index:y,...b});let x=y,S=(0,i.jsxs)(t,{gap:s,align:`stretch`,width:`100%`,children:[p?(0,i.jsx)(n,{width:m?l:_??`100%`,height:o,radius:g,index:x++,...b}):null,Array.from({length:Math.max(0,f)},(e,t)=>(0,i.jsx)(n,{width:t===f-1&&(p||f>1)?c:`100%`,height:o,radius:g,index:x++,...b},t))]});return m?(0,i.jsxs)(r,{gap:s,align:`start`,width:`100%`,children:[(0,i.jsx)(n,{width:u,height:u,radius:`rounded`,index:y,...b}),S]}):S};export{f as t};
