import{l as t,bc as v,r as O,ff as g,fP as S}from"./index-DPebpL40.js";/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */function z(d,i,s,p,{getItem:y,getId:N,getTotal:E}){const o=t.useRef([]),[c,L]=t.useTransition(),[u]=t.useState(i.limit),[a,f]=t.useState(0),l=t.useRef(s),e=!v(l.current,s),n=O.useLazyLoadQuery(d,{limit:e?i.limit:u,offset:e?0:a,...s},p),m=t.useMemo(()=>{const r=y(n);return e&&(o.current=[]),r?g([...o.current,...r],N):void 0},[n]),x=a+u<E(n),R=S(()=>{c||!x||(o.current=m||[],L(()=>{const r=a+u;f(r)}))});return t.useEffect(()=>{e&&(l.current=s,f(0))},[e]),{paginationData:m,result:n,loadNext:R,hasNext:x,isLoadingNext:c}}export{z as u};
//# sourceMappingURL=usePaginatedQuery-BsS6BXgl.js.map
