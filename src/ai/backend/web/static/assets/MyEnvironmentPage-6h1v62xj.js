import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{A as t,D as n,P as r,Zn as i,f as a}from"./icons-Btg1s2wy.js";import{t as o}from"./compiler-runtime-CZQb2eIb.js";import{St as s,T as c,Wt as l,et as u,kt as d,ot as f,ut as ee,vt as p,w as m,wt as h}from"./lodash-ClfL87UH.js";/* empty css            */import{t as g}from"./jsx-runtime-BapUIyWk.js";import{R as _}from"./usePressFeedback-BIoIGSxE.js";import{t as v}from"./IconButton-DGkWhkpU.js";import{r as y}from"./Skeleton-D35z7Ria.js";import{t as b}from"./BAIFlex-BElkJeHW.js";import{t as te}from"./app-shim-DTEBzR8d.js";import{s as x}from"./useThemeMode-Dg5yAWy7.js";import{I as ne,v as S,w as C}from"./helper-BWFKT_2Y.js";import{t as w}from"./react-relay-BfoHYpUf.js";import{t as re}from"./useToggle-CAWNf18k.js";import{l as ie,u as T}from"./helper-DF1Eunoe.js";import{t as E}from"./BAIText-CtDfjLnS.js";import{t as D}from"./BAISkeleton-MIjJv1Hr.js";import{t as O}from"./BAIDeleteConfirmModal-CwJ76ZY7.js";import{t as k}from"./BAITextHighlighter-D8LVcDhu.js";import{t as A}from"./TextInput-B89-yA_Q.js";import{t as j}from"./BAITable-BRd_Ua6I.js";import{n as ae,t as oe}from"./useHiddenColumnKeysSetting-CnfCJ_-z.js";import{a as M,i as N}from"./dist-C3M-rFln.js";import{ht as P}from"./index-49VU5B_r.js";import{t as F}from"./AliasedImageTagTokens-Db9ohylm.js";var I=o(),L=(function(){var e={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},t={alias:null,args:null,kind:`ScalarField`,name:`humanized_name`,storageKey:null},n={alias:null,args:null,kind:`ScalarField`,name:`tag`,storageKey:null},r={alias:null,args:null,kind:`ScalarField`,name:`registry`,storageKey:null},i={alias:null,args:null,kind:`ScalarField`,name:`architecture`,storageKey:null},a={alias:null,args:null,kind:`ScalarField`,name:`digest`,storageKey:null},o=[{alias:null,args:null,kind:`ScalarField`,name:`key`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`value`,storageKey:null}],s={alias:null,args:null,concreteType:`KVPair`,kind:`LinkedField`,name:`labels`,plural:!0,selections:o,storageKey:null},c={alias:null,args:null,kind:`ScalarField`,name:`supported_accelerators`,storageKey:null},l={alias:null,args:null,kind:`ScalarField`,name:`namespace`,storageKey:null},u={alias:null,args:null,kind:`ScalarField`,name:`base_image_name`,storageKey:null},d={alias:null,args:null,concreteType:`KVPair`,kind:`LinkedField`,name:`tags`,plural:!0,selections:o,storageKey:null},f={alias:null,args:null,kind:`ScalarField`,name:`version`,storageKey:null};return{fragment:{argumentDefinitions:[],kind:`Fragment`,metadata:null,name:`CustomizedImageListQuery`,selections:[{alias:null,args:null,concreteType:`ImageNode`,kind:`LinkedField`,name:`customized_images`,plural:!0,selections:[e,t,n,r,i,a,s,c,l,u,d,f,{args:null,kind:`FragmentSpread`,name:`AliasedImageTagTokensFragment`}],storageKey:null}],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[],kind:`Operation`,name:`CustomizedImageListQuery`,selections:[{alias:null,args:null,concreteType:`ImageNode`,kind:`LinkedField`,name:`customized_images`,plural:!0,selections:[e,t,n,r,i,a,s,c,l,u,d,f],storageKey:null}]},params:{cacheID:`689536ba855719005bf8d2310798350b`,id:null,metadata:{},name:`CustomizedImageListQuery`,operationKind:`query`,text:`query CustomizedImageListQuery {
  customized_images {
    id
    humanized_name
    tag
    registry
    architecture
    digest
    labels {
      key
      value
    }
    supported_accelerators
    namespace
    base_image_name
    tags {
      key
      value
    }
    version
    ...AliasedImageTagTokensFragment
  }
}

fragment AliasedImageTagTokensFragment on ImageNode {
  labels {
    key
    value
  }
  tags {
    key
    value
  }
}
`}}})();L.hash=`7043e7324fbc70951d3d233aa611311f`;var R=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`id`}],t=[{alias:null,args:[{kind:`Variable`,name:`image_id`,variableName:`id`}],concreteType:`ForgetImageById`,kind:`LinkedField`,name:`forget_image_by_id`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`ok`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`msg`,storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`CustomizedImageListForgetMutation`,selections:t,type:`Mutation`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`CustomizedImageListForgetMutation`,selections:t},params:{cacheID:`6b517a276517434fdeb129e0535f9519`,id:null,metadata:{},name:`CustomizedImageListForgetMutation`,operationKind:`mutation`,text:`mutation CustomizedImageListForgetMutation(
  $id: String!
) {
  forget_image_by_id(image_id: $id) {
    ok
    msg
  }
}
`}}})();R.hash=`ab2f38ba9700f7c548544a3bc471eb01`;var z=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`id`}],t=[{alias:null,args:[{kind:`Variable`,name:`image_id`,variableName:`id`}],concreteType:`UntagImageFromRegistry`,kind:`LinkedField`,name:`untag_image_from_registry`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`ok`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`msg`,storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`CustomizedImageListUntagMutation`,selections:t,type:`Mutation`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`CustomizedImageListUntagMutation`,selections:t},params:{cacheID:`c71657d2d82d32a7b5b91377f22a41fb`,id:null,metadata:{},name:`CustomizedImageListUntagMutation`,operationKind:`mutation`,text:`mutation CustomizedImageListUntagMutation(
  $id: String!
) {
  untag_image_from_registry(image_id: $id) {
    ok
    msg
  }
}
`}}})();z.hash=`403ccc93953ffe2c119ecfb71a1b8b32`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var B=e(i(),1),V=w(),H=g(),U=()=>{let{t:e}=y(),{message:i}=te.useApp(),[o,{toggle:g}]=re(),[w,D]=(0,B.useTransition)(),[M,N]=x(`initial-fetch`),[P,I]=(0,B.useState)(``),[U,W]=(0,B.useState)(``),[G,K]=(0,B.useTransition)(),[q,J]=(0,B.useState)(null),[,{tagAlias:se}]=ne(),{customized_images:Y}=(0,V.useLazyLoadQuery)(L,{},{fetchPolicy:M===`initial-fetch`?`store-and-network`:`network-only`,fetchKey:M}),[ce,le]=(0,V.useMutation)(R),[ue,de]=(0,V.useMutation)(z),X=(0,B.useMemo)(()=>m(Y,e=>e==null?void 0:e.humanized_name),[Y]),Z=(0,B.useMemo)(()=>X==null?void 0:X.map(e=>({namespace:e==null?void 0:e.namespace,fullName:S(e)||``,digest:(e==null?void 0:e.digest)||``,baseImageName:e==null?void 0:e.base_image_name,tags:e==null?void 0:e.tags,version:e==null?void 0:e.version})),[X]),fe=(0,B.useMemo)(()=>{if(f(P))return X;let e=RegExp(`${h(P)}`,`i`);return s(X,(t,n)=>c(t,(t,r)=>{if(r===`id`)return!1;if([`digest`,`architecture`,`registry`].includes(r))return e.test(l(t));let i=Z[n]||{},a=e.test(i.namespace||``),o=e.test(i.fullName),s=c(i.tags,t=>e.test(t.key)||e.test(t.value)),u=e.test(i.version||``),d=e.test(i.digest);return a||o||s||u||d}))},[P,Z,X]),Q=ie([{title:e(`environment.FullImagePath`),key:`fullImagePath`,render:(e,t)=>(0,H.jsx)(E,{monospace:!0,ellipsis:{tooltip:!0},copyable:{text:S(t)||``},children:(0,H.jsx)(k,{keyword:P,children:S(t)||``})}),sorter:(e,t)=>C(S(e),S(t)),width:480},{title:e(`general.Control`),key:`control`,render:(t,n)=>(0,H.jsx)(b,{direction:`row`,align:`stretch`,justify:`center`,gap:`xxs`,children:(0,H.jsx)(v,{variant:`ghost`,className:`bai-name-action-cell-danger`,icon:(0,H.jsx)(a,{size:`1em`}),label:e(`button.Delete`),tooltip:e(`button.Delete`),onClick:()=>{J(n||null)}})})},{title:e(`environment.Registry`),dataIndex:`registry`,key:`registry`,sorter:(e,t)=>C(e==null?void 0:e.registry,t==null?void 0:t.registry),render:e=>(0,H.jsx)(k,{keyword:P,children:e})},{title:e(`environment.Architecture`),dataIndex:`architecture`,key:`architecture`,sorter:(e,t)=>C(e==null?void 0:e.architecture,t==null?void 0:t.architecture),render:e=>(0,H.jsx)(k,{keyword:P,children:e})},{title:e(`environment.Namespace`),key:`namespace`,dataIndex:`namespace`,sorter:(e,t)=>C(e==null?void 0:e.namespace,t==null?void 0:t.namespace),render:e=>(0,H.jsx)(k,{keyword:P,children:e})},{title:e(`environment.BaseImageName`),key:`base_image_name`,dataIndex:`base_image_name`,sorter:(e,t)=>C(e==null?void 0:e.base_image_name,t==null?void 0:t.base_image_name),render:e=>(0,H.jsx)(k,{keyword:P,children:se(e)})},{title:e(`environment.Version`),key:`version`,dataIndex:`version`,sorter:(e,t)=>C(e==null?void 0:e.version,t==null?void 0:t.version),render:e=>(0,H.jsx)(k,{keyword:P,children:e})},{title:e(`environment.Tags`),key:`tags`,dataIndex:`tags`,render:(e,t)=>(0,H.jsx)(F,{imageFrgmt:t,highlightKeyword:P})},{title:e(`environment.Digest`),dataIndex:`digest`,key:`digest`,sorter:(e,t)=>C(e==null?void 0:e.digest,t==null?void 0:t.digest),render:e=>(0,H.jsx)(b,{style:{maxWidth:200},align:`stretch`,children:(0,H.jsx)(_,{maxLines:1,children:(0,H.jsx)(k,{keyword:P,children:e})})})}]),[$,pe]=oe(`CustomizedImageList`);return(0,H.jsxs)(b,{direction:`column`,align:`stretch`,children:[(0,H.jsxs)(b,{direction:`column`,align:`stretch`,gap:`sm`,children:[(0,H.jsxs)(b,{justify:`between`,gap:`xs`,wrap:`wrap`,children:[(0,H.jsx)(A,{"aria-label":e(`environment.SearchImages`),value:U,hasClear:!0,startIcon:t,placeholder:e(`environment.SearchImages`),onChange:e=>{W(e),K(()=>I(e))},width:200}),(0,H.jsx)(v,{label:e(`button.Refresh`),tooltip:e(`button.Refresh`),icon:(0,H.jsx)(r,{size:`1em`}),isLoading:w,onClick:()=>{D(()=>N())}})]}),(0,H.jsx)(j,{scroll:{x:`max-content`},resizable:!0,loading:G,columns:s(Q,e=>!ee($,l(e==null?void 0:e.key))),dataSource:T(fe),rowKey:`id`,pagination:{extraContent:(0,H.jsx)(v,{variant:`ghost`,icon:(0,H.jsx)(n,{size:`1em`}),label:e(`table.SettingTable`),onClick:()=>{g()}})}})]}),(0,H.jsx)(ae,{open:o,onRequestClose:e=>{e!=null&&e.selectedColumnKeys&&pe(d(Q.map(e=>l(e.key)),e==null?void 0:e.selectedColumnKeys)),g()},columns:Q,hiddenColumnKeys:$}),(0,H.jsx)(O,{open:q!==null,title:e(`dialog.title.DeleteSomething`,{name:S(q)??``}),target:e(`general.Image`),items:q?[{key:q.id,label:S(q)??q.id}]:[],confirmText:e(`credential.PermanentlyDelete`),requireConfirmInput:!0,inputProps:{placeholder:e(`credential.PermanentlyDelete`)},confirmLoading:le||de,onOk:()=>{q&&ue({variables:{id:q.id},onCompleted:(t,n)=>{if(!u(t.untag_image_from_registry)&&!t.untag_image_from_registry.ok)i.error(t.untag_image_from_registry.msg);else if(n&&(n==null?void 0:n.length)>0){let e=p(n,e=>e.message);for(let t of e)i.error(t)}else ce({variables:{id:q.id},onCompleted:(t,n)=>{if(!u(t.forget_image_by_id)&&!t.forget_image_by_id.ok)i.error(t.forget_image_by_id.msg);else if(n&&(n==null?void 0:n.length)>0){let e=p(n,e=>e.message);for(let t of e)i.error(t)}else D(()=>{N()}),i.success(e(`environment.CustomizedImageSuccessfullyDeleted`)),J(null)},onError:()=>{i.error(e(`environment.FailedToDeleteCustomizedImage`))}})},onError:()=>{i.error(e(`environment.FailedToDeleteCustomizedImage`))}})},onCancel:()=>{J(null)}})]})},W=()=>{"use memo";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
let e=(0,I.c)(17),{t}=y(),n;e[0]===Symbol.for(`react.memo_cache_sentinel`)?(n=N([`image`]).withDefault(`image`),e[0]=n):n=e[0];let[r,i]=M(`tab`,n),a;e[1]===i?a=e[2]:(a=e=>{e===`image`&&i(e)},e[1]=i,e[2]=a);let o;e[3]===t?o=e[4]:(o=t(`environment.Images`),e[3]=t,e[4]=o);let s;e[5]===o?s=e[6]:(s=[{key:`image`,label:o}],e[5]=o,e[6]=s);let c;e[7]===Symbol.for(`react.memo_cache_sentinel`)?(c=(0,H.jsx)(D,{rows:4}),e[7]=c):c=e[7];let l;e[8]===r?l=e[9]:(l=r===`image`&&(0,H.jsx)(U,{}),e[8]=r,e[9]=l);let u;e[10]===l?u=e[11]:(u=(0,H.jsx)(B.Suspense,{fallback:c,children:l}),e[10]=l,e[11]=u);let d;return e[12]!==r||e[13]!==a||e[14]!==s||e[15]!==u?(d=(0,H.jsx)(P,{activeTabKey:r,onTabChange:a,tabList:s,children:u}),e[12]=r,e[13]=a,e[14]=s,e[15]=u,e[16]=d):d=e[16],d};export{W as default};
