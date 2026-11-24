import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";import{at as n,o as r}from"./lodash-ClfL87UH.js";/* empty css            */import{c as i}from"./useThemeMode-Dg5yAWy7.js";import{t as a}from"./react-relay-BfoHYpUf.js";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var o=e(t(),1),s=a();function c(e,t,a,c,{getItem:l,getId:u,getTotal:d}){let f=(0,o.useRef)([]),[p,m]=(0,o.useTransition)(),[h]=(0,o.useState)(t.limit),[g,_]=(0,o.useState)(0),v=(0,o.useRef)(a),y=!n(v.current,a),b=(0,s.useLazyLoadQuery)(e,{limit:y?t.limit:h,offset:y?0:g,...a},c),x=(0,o.useMemo)(()=>{let e=l(b);return y&&(f.current=[]),e?r([...f.current,...e],u):void 0},[b]),S=g+h<d(b),C=i(()=>{!p&&S&&(f.current=x||[],m(()=>{let e=g+h;_(e)}))});return(0,o.useEffect)(()=>{y&&(v.current=a,_(0))},[y]),{paginationData:x,result:b,loadNext:C,hasNext:S,isLoadingNext:p}}export{c as t};
