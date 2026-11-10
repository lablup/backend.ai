import{r as v,az as O}from"./index-CwWAznqi.js";import{r as t}from"./icons-BgdBQS0N.js";import{b as g,x as z}from"./lodash-RhKGq0BF.js";/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */function T(d,i,s,l,{getItem:y,getId:N,getTotal:E}){const n=t.useRef([]),[c,L]=t.useTransition(),[u]=t.useState(i.limit),[a,f]=t.useState(0),m=t.useRef(s),e=!g(m.current,s),r=v.useLazyLoadQuery(d,{limit:e?i.limit:u,offset:e?0:a,...s},l),p=t.useMemo(()=>{const o=y(r);return e&&(n.current=[]),o?z([...n.current,...o],N):void 0},[r]),x=a+u<E(r),R=O(()=>{c||!x||(n.current=p||[],L(()=>{const o=a+u;f(o)}))});return t.useEffect(()=>{e&&(m.current=s,f(0))},[e]),{paginationData:p,result:r,loadNext:R,hasNext:x,isLoadingNext:c}}export{T as u};
//# sourceMappingURL=usePaginatedQuery-R0VAu0cL.js.map
