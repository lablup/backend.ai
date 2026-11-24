import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";import{t as n}from"./compiler-runtime-CZQb2eIb.js";import{t as r}from"./jsx-runtime-BapUIyWk.js";import{S as i}from"./Modal2-DnaQJkP1.js";import{t as a}from"./TextInput-C_tSDoXF.js";import{t as o}from"./NumberInput-6qDMlvvj.js";var s=e(t(),1),c=r();function l({defaultValue:e,onCommit:t,type:n,placeholder:r,isDisabled:l,status:u,label:d,isLabelHidden:f,width:p,className:m,style:h,controlClassName:g,controlStyle:_,...v}){let y=i(),[b,x]=(0,s.useState)(e??``),S=(0,s.useRef)(null),[C,w]=(0,s.useState)(e);C!==e&&(w(e),x(e??``));let T={...v,label:d??y(`uic.UncontrolledInput.label`),isLabelHidden:f??d===void 0,placeholder:r,isDisabled:l,status:u,width:p,containerClassName:m,containerStyle:h,controlClassName:g,controlStyle:_},E=()=>{if(l)return;let e=S.current??b;S.current=null,t==null||t(e)};if(n===`number`){let e=b===``?null:Number(b);return(0,c.jsx)(o,{...T,value:e===null||Number.isNaN(e)?null:e,onChange:e=>{let t=e===null?``:String(e);S.current=t,x(t)},onEnter:E,onBlur:E})}return(0,c.jsx)(a,{...T,type:n===`password`||n===`email`?n:`text`,value:b,onChange:x,onEnter:E,onBlur:E})}l.displayName=`UncontrolledInput`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

Adapter over ui-common `UncontrolledInput` (FR-4054): keeps antd's
`disabled` and string `status`. The fallback accessible name comes from
ui-common's catalog.
*/
var u=n(),d=e=>{"use memo";let t=(0,u.c)(10),n,r,i;t[0]===e?(n=t[1],r=t[2],i=t[3]):({disabled:n,status:r,...i}=e,t[0]=e,t[1]=n,t[2]=r,t[3]=i);let a;t[4]===r?a=t[5]:(a=r===`error`||r===`warning`?{type:r}:void 0,t[4]=r,t[5]=a);let o;return t[6]!==n||t[7]!==a||t[8]!==i?(o=(0,c.jsx)(l,{...i,isDisabled:n,status:a}),t[6]=n,t[7]=a,t[8]=i,t[9]=o):o=t[9],o};export{d as t};
