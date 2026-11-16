import{Jt as e,V as t,ft as n,vt as r}from"./lodash-ClfL87UH.js";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var i=/^[=@\t\r]/,a=e=>i.test(e)?!0:/^[+-]/.test(e)&&e!==`-`&&!Number.isFinite(Number(e)),o=Symbol(`csvLiteral`),s=e=>({[o]:!0,value:e==null?``:String(e)}),c=e=>typeof e==`object`&&!!e&&o in e,l=e=>`"${e.replace(/"/g,`""`)}"`;function u(e){return e==null?``:c(e)?l(e.value):typeof e==`number`||typeof e==`boolean`?String(e):(e=n(e)?e:JSON.stringify(e),a(e)&&(e=`'${e}`),l(e))}var d=(n,i)=>{let a=r(n,e=>t(e,`__fragments`,`__fragmentOwner`,`__id`)),o=e(a[0]),s=r(a,e=>r(e,(e,t)=>{if(i!=null&&i[t]){var n;return((n=i[t])==null?void 0:n.call(i,e))||e}return e})).map(e=>e.map(u).join(`,`)).join(`
`);return[o.map(u).join(`,`),s].join(`
`)},f=(e,t)=>{let n=URL.createObjectURL(e),r=document.createElement(`a`);r.href=n,r.download=t,document.body.appendChild(r),r.click(),document.body.removeChild(r),setTimeout(()=>URL.revokeObjectURL(n),100)},p=(e,t)=>{let n=e.startsWith(`﻿`)?e:`﻿`+e;f(new Blob([n],{type:`text/csv;charset=utf-8;`}),t.toLowerCase().endsWith(`.csv`)?t:`${t}.csv`)},m=(e,t,n)=>{p(d(e,n),t)},h=e=>{e.charCodeAt(0)===65279&&(e=e.slice(1));let t=[],n=``,r=[],i=!1;for(let a=0;a<e.length;a++){let o=e[a];i?o===`"`?e[a+1]===`"`?(n+=`"`,a++):i=!1:n+=o:o===`"`?i=!0:o===`,`?(r.push(n),n=``):o===`
`||o===`\r`?(o===`\r`&&e[a+1]===`
`&&a++,r.push(n),n=``,t.push(r),r=[]):n+=o}if(i)throw Error(`Unterminated quoted field in CSV`);(n.length>0||r.length>0)&&(r.push(n),t.push(r));let a=t.filter(e=>e.some(e=>e.trim()!==``));if(a.length===0)return[];let o=a[0].map(e=>e.trim());return a.slice(1).map(e=>{let t={};return o.forEach((n,r)=>{t[n]=(e[r]??``).trim()}),t})};export{m as a,u as i,f as n,h as o,p as r,s as t};
