import{t as e}from"./compiler-runtime-CZQb2eIb.js";import{Wt as t,kt as n,vt as r}from"./lodash-ClfL87UH.js";/* empty css            */import{t as i}from"./jsx-runtime-BapUIyWk.js";import{O as a}from"./DefaultProviders-BFjPhnQa.js";import{l as o,r as s,s as c}from"./DataGrid2-S8Qkyg5h.js";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

ui-common `DataGridSettingsModal` under its BUI name (FR-4096): `open` →
`isOpen`, `required` → `isAlwaysVisible`, `disableReorder` → `isReorderable`,
and one `onRequestClose(result?)` for both Apply and cancel. The strings come
from ui-common's catalog.
*/
var l=e(),u=i(),d=e=>{"use memo";let t=(0,l.c)(21),n,r,i,a,o,c;t[0]===e?(n=t[1],r=t[2],i=t[3],a=t[4],o=t[5],c=t[6]):({open:o,columns:n,visibleColumnKeys:c,disableReorder:r,onRequestClose:a,...i}=e,t[0]=e,t[1]=n,t[2]=r,t[3]=i,t[4]=a,t[5]=o,t[6]=c);let d;t[7]===a?d=t[8]:(d=e=>{e||a(void 0)},t[7]=a,t[8]=d);let p;t[9]===n?p=t[10]:(p=n.map(f),t[9]=n,t[10]=p);let m=!r,h;t[11]===a?h=t[12]:(h=e=>a(e),t[11]=a,t[12]=h);let g;return t[13]!==i||t[14]!==o||t[15]!==d||t[16]!==p||t[17]!==m||t[18]!==h||t[19]!==c?(g=(0,u.jsx)(s,{...i,isOpen:o,onOpenChange:d,columns:p,visibleColumnKeys:c,isReorderable:m,onApply:h}),t[13]=i,t[14]=o,t[15]=d,t[16]=p,t[17]=m,t[18]=h,t[19]=c,t[20]=g):g=t[20],g};function f(e){return{key:e.key,label:e.label,isAlwaysVisible:e.required}}
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

QA-FINDINGS Q-13 — "My Environments, RBAC Management 의 table settings modal
에서만 다른 스타일을 갖고 있습니다. 다른 컴포넌트와 동일한 스타일을 유지하도록
수정이 필요합니다."

There are two column-settings surfaces in the app. Most tables use the one
`BAITable` renders for its `tableSettings` prop
(`BAITableSettingModal`): a `Dialog` with a title+subtitle header, an
unlabelled search field, drag-to-reorder handles, locked required columns and
Cancel/Apply. The five tables that predate that prop — `RoleNodes` (RBAC
Management), `CustomizedImageList` (My Environments), `ImageList`,
`ContainerRegistryList`, `AgentSummaryList` — reach this component instead,
which drew its own `BAIModal` + `Form` with a LABELLED search field, a 220px
box, no reordering and OK/Cancel. Same job, visibly different modal.

So this component keeps its own prop contract and its own persistence, and
DELEGATES the rendering. Those five tables store visibility as
`hiddenColumnKeys` through `useHiddenColumnKeysSetting`, while
`tableSettings` stores a richer `columnOverrides` record (hidden + order +
width); migrating them is a storage change that would drop users' saved
columns on first load, and it is not what the report asks for. Delegating gets
one look out of one implementation with no storage change and no call-site
edit.

Two behaviours are deliberately NOT forwarded, because this contract cannot
carry them:

- **Drag-to-reorder** is disabled (`disableReorder`). `hiddenColumnKeys` has
nowhere to put an order, so an order the user set would be silently lost on
close. The shared modal already hides its grip handles in that mode.
- **Required columns** are not marked. `BAIColumnsType` carries `required`,
but these five call sites never set it, so nothing would render differently.

The label flattening also comes from the shared helper now. The local
`onChangeTitleToString` walked only the DIRECT string children of an element,
so a header nesting its text one level deeper (a tooltip'd header, an icon +
label pair) produced `undefined` and the row showed its raw column key —
the same class of defect as Q-12, one narrower.
*/
var p=e=>{"use memo";let t=(0,l.c)(17),{open:i,onRequestClose:a,columns:o,hiddenColumnKeys:s}=e,c,f,p,h;if(t[0]!==o||t[1]!==s||t[2]!==i){let e=r(o,m);c=d,f=i,p=e;let a;t[7]===s?a=t[8]:(a=s??[],t[7]=s,t[8]=a),h=n(r(e,`key`),a),t[0]=o,t[1]=s,t[2]=i,t[3]=c,t[4]=f,t[5]=p,t[6]=h}else c=t[3],f=t[4],p=t[5],h=t[6];let g;t[9]===a?g=t[10]:(g=e=>a(e?{selectedColumnKeys:e.selectedColumnKeys}:void 0),t[9]=a,t[10]=g);let _;return t[11]!==c||t[12]!==f||t[13]!==p||t[14]!==h||t[15]!==g?(_=(0,u.jsx)(c,{open:f,columns:p,visibleColumnKeys:h,disableReorder:!0,onRequestClose:g}),t[11]=c,t[12]=f,t[13]=p,t[14]=h,t[15]=g,t[16]=_):_=t[16],_};function m(e){let n=t(e.key);return{key:n,label:c(o(e)).trim()||n,required:!!e.required}}
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var h=e=>{let[t,n]=a(`hiddenColumnKeys.${e}`);return[t,n]};export{p as n,h as t};
