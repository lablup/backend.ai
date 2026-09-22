import{l as t,bd as R,r as v,fU as g,fO as S}from"./index-Dd8bt51s.js";/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */function z(x,i,s,p,{getItem:y,getId:N,getTotal:E}){const o=t.useRef([]),[c,L]=t.useTransition(),[u]=t.useState(i.limit),[a,f]=t.useState(0),d=t.useRef(s),e=!R(d.current,s),n=v.useLazyLoadQuery(x,{limit:e?i.limit:u,offset:e?0:a,...s},p),l=t.useMemo(()=>{const r=y(n);return e&&(o.current=[]),r?g([...o.current,...r],N):void 0},[n]),m=a+u<E(n),O=S(()=>{c||!m||(o.current=l||[],L(()=>{const r=a+u;f(r)}))});return t.useEffect(()=>{e&&(d.current=s,f(0))},[e]),{paginationData:l,result:n,loadNext:O,hasNext:m,isLoadingNext:c}}export{z as u};
//# sourceMappingURL=usePaginatedQuery-CmwInngL.js.map
