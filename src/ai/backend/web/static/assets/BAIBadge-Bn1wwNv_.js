import{t as e}from"./compiler-runtime-CZQb2eIb.js";import{t}from"./jsx-runtime-BapUIyWk.js";import{R as n}from"./usePressFeedback-BIoIGSxE.js";import{t as r}from"./StatusDot-B2UXcn95.js";var i=e(),a=t(),o={success:`success`,info:`accent`,warning:`warning`,error:`error`,default:`neutral`},s=e=>{"use memo";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

`BAIBadge` on Astryx (to-astryx phase 3, ticket A).

antd `Badge status={…} text={…}` — a coloured dot with a label beside it —
maps to Astryx **`StatusDot`** (MAPPING §3.8, "`status` + `text` ->
`StatusDot`"). `StatusDot` renders the dot ONLY (its `label` is the
`aria-label`, deliberately not visible), so the visible label is a sibling
`Text`, which is also what antd's markup was.

FRONTIER COMPONENT — the public surface is unchanged (`color` as a BUI
`SemanticColor`, `processing`, plus antd `Badge`'s `text` / `style` /
`className`), so `BAIAuditLogStatusBadge`, `BAISchedulingResultBadge`,
`StorageUsageBadge` and `SessionSlotCell` stay at zero diff.
*/
let t=(0,i.c)(20),s,c,l,u,d,f;t[0]===e?(s=t[1],c=t[2],l=t[3],u=t[4],d=t[5],f=t[6]):({color:c,processing:l,text:f,className:s,style:d,...u}=e,t[0]=e,t[1]=s,t[2]=c,t[3]=l,t[4]=u,t[5]=d,t[6]=f);let p=s?`bai-badge ${s}`:`bai-badge`,m=c?void 0:`bai-badge-dot--unknown`,h=c?o[c]:`neutral`,g=typeof f==`string`?f:`status`,_;t[7]!==l||t[8]!==m||t[9]!==h||t[10]!==g?(_=(0,a.jsx)(r,{className:m,variant:h,label:g,isPulsing:l}),t[7]=l,t[8]=m,t[9]=h,t[10]=g,t[11]=_):_=t[11];let v;t[12]===f?v=t[13]:(v=f==null?null:(0,a.jsx)(n,{children:f}),t[12]=f,t[13]=v);let y;return t[14]!==u||t[15]!==d||t[16]!==p||t[17]!==_||t[18]!==v?(y=(0,a.jsxs)(`span`,{...u,className:p,style:d,children:[_,v]}),t[14]=u,t[15]=d,t[16]=p,t[17]=_,t[18]=v,t[19]=y):y=t[19],y};export{s as t};
