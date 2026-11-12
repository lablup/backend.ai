import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";import{t as n}from"./compiler-runtime-CZQb2eIb.js";/* empty css            */import{t as r}from"./jsx-runtime-BapUIyWk.js";import{s as i}from"./DefaultProviders-BFjPhnQa.js";import{r as a}from"./Skeleton-D35z7Ria.js";import{U as o}from"./TotalResourceWithinResourceGroup--9B9dPSp.js";import{G as s,rt as c}from"./helper-BWFKT_2Y.js";import{n as l,r as u,t as d}from"./panelCatalog-Dyd4k_HJ.js";import{t as f}from"./BAIUnmountAfterClose-Cxr4Dp_U.js";import{i as p}from"./useCurrentUserProjectRoles-CLTXJ3AL.js";import{M as m}from"./index-49VU5B_r.js";import{t as h}from"./useVFolderInvitations-D_zm5Puj.js";import g from"./SessionDetailAndContainerLogOpenerLegacy-klqe1NvT.js";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var _=n(),v=e(t(),1),y=()=>{"use memo";let e=(0,_.c)(5),{t}=a(),{upsertNotification:n}=i(),[r]=h(),o,s;return e[0]!==r.length||e[1]!==t||e[2]!==n?(o=()=>{r.length<=0||n({key:`invitedFolders`,message:t(`data.InvitedFoldersTooltip`,{count:r.length}),to:{search:new URLSearchParams({invitation:`true`}).toString()},open:!0,duration:0})},s=[r.length,t,n],e[0]=r.length,e[1]=t,e[2]=n,e[3]=o,e[4]=s):(o=e[3],s=e[4]),(0,v.useEffect)(o,s),null},b=e=>{
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
let t=e.startsWith(`?`)?e.slice(1):e;if(!t)return null;if(!t.includes(`=`))return{kind:`legacyGithub`,data:{url:`https://github.com/${t}`}};let n=new URLSearchParams(t);if(n.get(`type`)!==`url`)return null;try{let e=JSON.parse(n.get(`data`)??``);if(!e||typeof e!=`object`)return null;let{url:t,branch:r}=e;return{kind:`url`,data:{...typeof t==`string`?{url:t}:{},...typeof r==`string`?{branch:r}:{}}}}catch{return null}},x=e=>{let t=e.startsWith(`?`)?e.slice(1):e;if(!t.includes(`=`))return``;let n=new URLSearchParams(t);return n.delete(`type`),n.delete(`data`),n.toString()},S=r(),C=()=>{"use memo";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
let e=(0,_.c)(14),t=c(),n=s(),r;e[0]===t.search?r=e[1]:(r=()=>b(t.search),e[0]=t.search,e[1]=r);let[i,a]=(0,v.useState)(r),o;e[2]!==t.hash||e[3]!==t.pathname||e[4]!==t.search||e[5]!==n?(o=()=>{b(t.search)&&n({pathname:t.pathname,search:x(t.search),hash:t.hash},{replace:!0})},e[2]=t.hash,e[3]=t.pathname,e[4]=t.search,e[5]=n,e[6]=o):o=e[6];let u=(0,v.useEffectEvent)(o),d;e[7]===u?d=e[8]:(d=()=>{u()},e[7]=u,e[8]=d);let p;e[9]===Symbol.for(`react.memo_cache_sentinel`)?(p=[],e[9]=p):p=e[9],(0,v.useEffect)(d,p);let m=!!i,h=i==null?void 0:i.data,g;e[10]===Symbol.for(`react.memo_cache_sentinel`)?(g=()=>a(null),e[10]=g):g=e[10];let y;return e[11]!==m||e[12]!==h?(y=(0,S.jsx)(f,{children:(0,S.jsx)(l,{open:m,initialTab:`notebook`,initialData:h,onCancel:g})}),e[11]=m,e[12]=h,e[13]=y):y=e[13],y},w=()=>{"use memo";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
let e=(0,_.c)(12),{urlProjectName:t,resolvedId:n}=p(),r;e[0]!==n||e[1]!==t?(r=t&&n?{id:n,name:t}:null,e[0]=n,e[1]=t,e[2]=r):r=e[2];let i=r,a;e[3]===Symbol.for(`react.memo_cache_sentinel`)?(a={},e[3]=a):a=e[3];let s,c;e[4]===i?(s=e[5],c=e[6]):(s=(0,S.jsx)(u,{page:`project`,project:i,catalog:d,isRefetching:!1,queryRefs:a}),c=(0,S.jsx)(g,{project:i}),e[4]=i,e[5]=s,e[6]=c);let l;e[7]===Symbol.for(`react.memo_cache_sentinel`)?(l=(0,S.jsx)(C,{}),e[7]=l):l=e[7];let f;e[8]===Symbol.for(`react.memo_cache_sentinel`)?(f=(0,S.jsx)(m,{children:(0,S.jsx)(v.Suspense,{fallback:null,children:(0,S.jsx)(y,{})})}),e[8]=f):f=e[8];let h;return e[9]!==s||e[10]!==c?(h=(0,S.jsxs)(o,{children:[s,c,l,f]}),e[9]=s,e[10]=c,e[11]=h):h=e[11],h};export{w as default};
