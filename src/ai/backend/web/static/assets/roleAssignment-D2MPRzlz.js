import{t as e}from"./compiler-runtime-CZQb2eIb.js";import{t}from"./jsx-runtime-BapUIyWk.js";import{n}from"./Skeleton-D35z7Ria.js";import{t as r}from"./astryxLabel-C5P0iFEX.js";import{t as i}from"./CheckboxInput-DinsfW7h.js";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

`BAICheckbox` keeps antd's `Checkbox` surface (`checked`, `children` as the
inline label, `disabled`) over ui-common's `CheckboxInput`, which reads the
enclosing `Form.Item`'s status itself.

PILOT-DECISION — an unlabelled checkbox (a permission-matrix cell) falls back
to the translated `general.Select` as its `aria-label`, as `BAIButton`'s
icon-only fallback does.
*/
var a=e(),o=t(),s=e=>{"use memo";let t=(0,a.c)(25),s,c,l,u,d,f,p,m,h;t[0]===e?(s=t[1],c=t[2],l=t[3],u=t[4],d=t[5],f=t[6],p=t[7],m=t[8],h=t[9]):({checked:s,value:h,indeterminate:u,disabled:l,children:c,label:f,isLabelHidden:d,onChange:p,...m}=e,t[0]=e,t[1]=s,t[2]=c,t[3]=l,t[4]=u,t[5]=d,t[6]=f,t[7]=p,t[8]=m,t[9]=h);let{t:g}=n(),_;t[10]!==c||t[11]!==f?(_=f??r(c),t[10]=c,t[11]=f,t[12]=_):_=t[12];let v=_,y=v!==``,b=d??!y,x=u?`indeterminate`:h??s??!1,S;t[13]!==y||t[14]!==b||t[15]!==v||t[16]!==g?(S=b?y?v:g(`general.Select`):void 0,t[13]=y,t[14]=b,t[15]=v,t[16]=g,t[17]=S):S=t[17];let C=b?void 0:v,w;return t[18]!==l||t[19]!==p||t[20]!==m||t[21]!==x||t[22]!==S||t[23]!==C?(w=(0,o.jsx)(i,{...m,value:x,"aria-label":S,disabled:l,onChange:p,children:C}),t[18]=l,t[19]=p,t[20]=m,t[21]=x,t[22]=S,t[23]=C,t[24]=w):w=t[24],w},c=/is already assigned to user/,l=e=>c.test(e.message)
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
;export{s as n,l as t};
