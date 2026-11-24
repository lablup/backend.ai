import{t as e}from"./compiler-runtime-CZQb2eIb.js";import{t}from"./jsx-runtime-BapUIyWk.js";import{t as n}from"./CodeBlock-CAhj4Gfj.js";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var r=e(),i=t(),a=new Set([`bash`,`javascript`,`json`,`plaintext`,`python`,`shell`,`typescript`,`yaml`]),o=e=>{"use memo";let t=(0,r.c)(12),{children:o,language:s,style:c}=e,l,u,d;if(t[0]!==o||t[1]!==s){let e=s.toLowerCase();l=n,u=o??``,d=a.has(e)?e:`plaintext`,t[0]=o,t[1]=s,t[2]=l,t[3]=u,t[4]=d}else l=t[2],u=t[3],d=t[4];let f;t[5]===c?f=t[6]:(f={flex:1,minWidth:0,...c},t[5]=c,t[6]=f);let p;return t[7]!==l||t[8]!==u||t[9]!==d||t[10]!==f?(p=(0,i.jsx)(l,{code:u,language:d,width:`100%`,style:f}),t[7]=l,t[8]=u,t[9]=d,t[10]=f,t[11]=p):p=t[11],p};export{o as t};
