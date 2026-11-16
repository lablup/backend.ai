import{M as e}from"./DefaultProviders-BFjPhnQa.js";import{s as t}from"./Modal2-DnaQJkP1.js";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

The one z-index ladder (FR-3578 T10): every full-window layer takes a NAME here
instead of a number. `zIndexLadder.css` and `index.html` hand-mirror these
values; `scripts/migration-gates/z-index-ladder-gate.mjs` fails on drift.

| Layer | Value | Owner |
|---|---|---|
| `appHeader` | 100 | `MainLayout` header; `SiderToggleButton` sits one above it |
| (reserved) | 101–899 | unowned. A layer placed here sits BELOW the boot curtain, so anything that must stay visible during boot belongs above `splash` |
| `splash` | 900 | `index.html` `#splash`, which stays mounted as the logged-out backdrop. It sits BELOW `modalBase` deliberately: every dialog is a `document.body` portal now, so no login-screen wrapper can lift one over a splash that outranks the band |
| `loginHost` | 950 | `InteractiveLoginPage`'s full-viewport card host |
| (legacy 1000 band) | 1000–1002 | a SECOND vocabulary this ladder does not own: the antd-era popup base (1000), inlined by `FolderExplorerModal` (`+ 2`); the non-modal `Drawer` (ui-common's fork) bases at 1000 too, and `DragAndDrop` sits at 1001 |
| `modalBase` | 1100 | ui-common `Modal` (so `BAIModal` and the app-shim's `modal.*`) and `BAIDrawerPortal` (the scrimmed drawer), plus `BAI_Z_INDEX_MODAL_LEVEL_STEP` per level of ui-common's modal stack they share. `BAI_MODAL_Z_INDEX_BAND` hands this band to that stack |
| `loginSideHelp` | 1101 | `LoginFormPanel`'s side help panel — a fixed sibling anchored to the base modal's edge, so it clears that modal's mask but not a modal opened on top of it |
| `notification` | 11000 | `.bai-notification-stack` |
| (CSS top layer) | above all | Astryx `Toast`/`Popover`/`DropdownMenu`/`Tooltip`, `BAITour` — not stackable against this ladder. A NON-SCRIM `Drawer` is not here either: ui-common's fork opens it with `show()` (lab 0.6.5 would use the top layer), so it stacks at the legacy 1000 band above |
| context-local stacking | off the ladder at any magnitude | `BAIBoard.css` (BUI), `BAITable*`, `BAICompactGroup.css` — local to a subtree |
*/
var n={appHeader:100,splash:900,loginHost:950,modalBase:1100,loginSideHelp:1101,notification:11e3},r={base:n.modalBase,step:10,max:n.notification-1};t(r);
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var i=()=>``,a=(typeof document<`u`?document.title:``)||`Backend.AI`,o=(e,t=a)=>e?`${e} · ${t}`:t,s=({pageLabel:e,actAsName:t,attentionCount:n=0})=>`${n>0?`(${n}) `:``}${t?`[${t}] `:``}${i()}${o(e)}`,c={},l=(e={})=>{
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
c={...c,...e},document.title=s(c)},u=e=>{l({pageLabel:e})},d=`actAsHandoff`,f=`backendaiwebui.actAs`,p=`backendaiwebui.actAs.handoff.`,m=6e4,h=e=>{
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
let t=e;return typeof(t==null?void 0:t.userId)==`string`&&t.userId.length>0&&typeof t.email==`string`&&typeof t.name==`string`},g=e=>{if(!e)return null;try{return JSON.parse(e)}catch{return null}},_=e=>{try{for(let t=localStorage.length-1;t>=0;t--){let n=localStorage.key(t);if(!(n!=null&&n.startsWith(p)))continue;let r=g(localStorage.getItem(n));(!r||e-r.createdAt>m)&&localStorage.removeItem(n)}}catch{}},v=()=>{try{let e=g(sessionStorage.getItem(f));return h(e)?e:null}catch{return null}},y=t=>{let n=Date.now();_(n);let r=e(),i=p+r;try{localStorage.setItem(i,JSON.stringify({target:t,createdAt:n}))}catch{return!1}let a=new URL(`/`,window.location.href);a.searchParams.set(d,r);let o=window.open(a.href,`_blank`);if(!o){try{localStorage.removeItem(i)}catch{}return!1}return o.opener=null,!0},b=()=>{let e=new URL(window.location.href),t=e.searchParams.get(d);if(!t)return;e.searchParams.delete(d),window.history.replaceState(window.history.state,``,e.href);let n=p+t;try{let e=g(localStorage.getItem(n));localStorage.removeItem(n),e&&Date.now()-e.createdAt<=m&&h(e.target)&&sessionStorage.setItem(f,JSON.stringify(e.target))}catch{}},x=e=>{l({actAsName:e.name||e.email})},S=()=>{try{sessionStorage.removeItem(f)}catch{}window.close(),setTimeout(()=>{window.location.replace(new URL(`/`,window.location.href).href)},200)},C={login:{light:`loginLogoSrc`,dark:`loginLogoSrcDark`},about:{light:`aboutLogoSrc`,dark:`aboutLogoSrcDark`}},w={login:{light:`manifest/backend.ai-text.svg`,dark:`manifest/backend.ai-text-bgdark.svg`},about:{light:`manifest/backend.ai-webui-black.svg`,dark:`manifest/backend.ai-webui-white.svg`}},T={light:`srcDark`,dark:`src`},E=(e,t,n)=>{
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
let r=e==null?void 0:e[C[t][n]];if(r)return{src:r,source:`own`};let i=T[n],a=e==null?void 0:e[i];return a?{src:a,source:`inherited`,inheritedFrom:i}:{src:w[t][n],source:`default`}};export{v as a,l as c,S as i,n as l,b as n,y as o,x as r,u as s,E as t};
