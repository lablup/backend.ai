import{t as e}from"./compiler-runtime-CZQb2eIb.js";import{t}from"./jsx-runtime-BapUIyWk.js";import{t as n}from"./Badge-8q4sdq1t.js";var r=e(),i=t(),a=e=>{"use memo";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

The count pill next to a tab label. Settles the "accent-vs-fixed-blue" open
question left at the top of `BAIBadgeCount` (to-astryx ticket 08): the active
tab's count carries the ACTIVE MENU GROUP's primary, via `--color-accent`
(see `BAITabCountBadge.css` for why no `Badge.variant` can express that).
*/
let t=(0,r.c)(13),a,o,s,c,l;t[0]===e?(a=t[1],o=t[2],s=t[3],c=t[4],l=t[5]):({count:s,selected:c,showZero:l,className:o,...a}=e,t[0]=e,t[1]=a,t[2]=o,t[3]=s,t[4]=c,t[5]=l);let u=c!==void 0&&c;if(s==null||s===0&&!(l!==void 0&&l))return null;let d=u?`bai-tab-count-badge--selected`:``,f=o??``,p;t[6]!==d||t[7]!==f?(p=[`bai-tab-count-badge`,d,f].filter(Boolean),t[6]=d,t[7]=f,t[8]=p):p=t[8];let m=p.join(` `),h;return t[9]!==a||t[10]!==s||t[11]!==m?(h=(0,i.jsx)(n,{className:m,label:s,...a}),t[9]=a,t[10]=s,t[11]=m,t[12]=h):h=t[12],h};a.displayName=`BAITabCountBadge`;export{a as t};
