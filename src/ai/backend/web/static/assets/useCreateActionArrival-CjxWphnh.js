import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";import{t as n}from"./compiler-runtime-CZQb2eIb.js";import{G as r,W as i}from"./helper-BWFKT_2Y.js";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var a=n(),o=e(t(),1),s=`action`,c=e=>{"use memo";let t=(0,a.c)(13),n=i(),c=r(),l;t[0]===n.search?l=t[1]:(l=new URLSearchParams(n.search).get(s),t[0]=n.search,t[1]=l);let u=l,d;t[2]!==n.hash||t[3]!==n.search||t[4]!==n.state||t[5]!==c||t[6]!==e?(d=()=>{e();let t=new URLSearchParams(n.search);t.delete(s),c({search:t.toString(),hash:n.hash},{replace:!0,state:n.state})},t[2]=n.hash,t[3]=n.search,t[4]=n.state,t[5]=c,t[6]=e,t[7]=d):d=t[7];let f=(0,o.useEffectEvent)(d),p;t[8]!==u||t[9]!==f?(p=()=>{u===`add`&&f()},t[8]=u,t[9]=f,t[10]=p):p=t[10];let m;t[11]===u?m=t[12]:(m=[u],t[11]=u,t[12]=m),(0,o.useEffect)(p,m)};export{c as n,s as t};
