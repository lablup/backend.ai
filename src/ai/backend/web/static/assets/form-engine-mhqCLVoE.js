import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";/* empty css            */import{t as n}from"./jsx-runtime-BapUIyWk.js";import{I as r}from"./usePressFeedback-BIoIGSxE.js";import{S as i,_ as a}from"./Modal2-DnaQJkP1.js";import{n as o}from"./catalog-BNHCAujK.js";var s=Object.fromEntries([`label`,`type`,`len`,`min`,`max`,`pattern`].map(e=>[e,`\${${e}}`]));function c(e){let t=t=>e(t,s),n=e=>({len:t(`uic.Form.${e}Len`),min:t(`uic.Form.${e}Min`),max:t(`uic.Form.${e}Max`),range:t(`uic.Form.${e}Range`)});return{default:t(`uic.Form.default`),required:t(`uic.Form.required`),whitespace:t(`uic.Form.whitespace`),types:{string:t(`uic.Form.typeString`),number:t(`uic.Form.typeNumber`),object:t(`uic.Form.typeObject`),email:t(`uic.Form.typeEmail`),url:t(`uic.Form.typeUrl`)},string:n(`string`),number:n(`number`),array:n(`array`),pattern:{mismatch:t(`uic.Form.patternMismatch`)}}}var l=c((e,t)=>String(new r(o[e].defaultMessage,`en`).format(t)));function u(...e){let t={...l};return e.forEach(e=>{e&&Object.keys(e).forEach(n=>{let r=e[n],i=t[n];r&&typeof r==`object`&&i&&typeof i==`object`?t[n]={...i,...r}:t[n]=r})}),t}var d=e(t(),1),f=n();function p(){let e=i();return d.useMemo(()=>c(e),[e])}var m=({children:e,validateMessages:t,requiredMark:n,optionalLabel:r})=>{let i=d.useContext(a),o=d.useMemo(()=>({...i,...t===void 0?null:{validateMessages:t},...n===void 0?null:{requiredMark:n},...r===void 0?null:{optionalLabel:r}}),[i,t,n,r]);return(0,f.jsx)(a.Provider,{value:o,children:e})};
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

Form engine, react-app entry: re-exports the engine (`@lablup/ui-common/Form`)
through `backend.ai-ui`'s `form-engine` alias, so `react/src` files keep
importing `../form-engine`. RE-EXPORTS ONLY, for the reason in
`packages/backend.ai-ui/src/form-engine/index.ts`.
*/
export{m as n,u as r,p as t};
