/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var e=`settings`,t=`/usersettings`,n=[`general`,`logs`,`login-sessions`,`login-history`],r=e=>e==null||e===``?null:n.includes(e)?e:`general`,i=(t,n,r)=>{let i=new URLSearchParams(t);return r==null||r.forEach((e,t)=>{t!==`tab`&&t!==`settings`&&i.set(t,e)}),i.set(e,n),`?${i.toString()}`},a=e=>e.replace(/\/+$/,``).toLowerCase()===t,o=null,s=e=>{a(e.pathname)||(o={pathname:e.pathname,search:e.search,hash:e.hash,state:e.state})},c=()=>o;export{r as a,s as c,i,e as n,a as o,t as r,c as s,n as t};
