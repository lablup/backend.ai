import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";import{Yt as n}from"./lodash-ClfL87UH.js";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var r=e(t(),1);function i(e={},t={}){let{defaultValue:i,defaultValuePropName:s=`defaultValue`,valuePropName:c=`value`,trigger:l=`onChange`}=t,u=e[c],d=(0,r.useRef)(u!==void 0),f=u!==void 0;(0,r.useEffect)(()=>{d.current=f},[f]);let p=(0,r.useMemo)(()=>f?u:Object.prototype.hasOwnProperty.call(e,s)?e[s]:i,[]),m=(0,r.useRef)(p);f&&(m.current=u);let h=o();function g(t,...r){let i=n(t)?t(m.current):t;f||(m.current=i,h()),e[l]&&e[l](i,...r)}return[m.current,a(g)]}function a(e){let t=(0,r.useRef)(e);t.current=(0,r.useMemo)(()=>e,[e]);let n=(0,r.useRef)(null);return n.current||(n.current=function(...e){return t.current.apply(this,e)}),n.current}function o(){let[,e]=(0,r.useState)({});return(0,r.useCallback)(()=>e({}),[])}export{i as t};
