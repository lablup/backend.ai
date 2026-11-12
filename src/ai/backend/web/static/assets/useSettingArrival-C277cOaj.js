import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";import{t as n}from"./compiler-runtime-CZQb2eIb.js";import{ft as r,ut as i}from"./lodash-ClfL87UH.js";import{r as a}from"./Skeleton-D35z7Ria.js";import{G as o,W as s}from"./helper-BWFKT_2Y.js";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var c=n(),l=e(t(),1),u=`setting`,d=1500,f=e=>{"use memo";let t=(0,c.c)(13),{t:n}=a(),f=s(),p=o(),m;if(t[0]!==f.search||t[1]!==n||t[2]!==e){let a=new URLSearchParams(f.search).get(u),o=a?n(a,{postProcess:[]}):void 0;m=r(o)&&i(e,o)?o:null,t[0]=f.search,t[1]=n,t[2]=e,t[3]=m}else m=t[3];let h=m,g;t[4]!==f.pathname||t[5]!==f.search||t[6]!==p?(g=()=>{let e=new URLSearchParams(f.search);e.delete(u),p({pathname:f.pathname,search:e.toString()},{replace:!0})},t[4]=f.pathname,t[5]=f.search,t[6]=p,t[7]=g):g=t[7];let _=(0,l.useEffectEvent)(g),v;t[8]!==h||t[9]!==_?(v=()=>{if(!h)return;let e=setTimeout(_,d);return()=>clearTimeout(e)},t[8]=h,t[9]=_,t[10]=v):v=t[10];let y;return t[11]===h?y=t[12]:(y=[h],t[11]=h,t[12]=y),(0,l.useEffect)(v,y),h};export{f as n,u as t};
