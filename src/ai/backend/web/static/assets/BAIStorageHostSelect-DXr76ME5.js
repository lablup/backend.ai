import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";import{t as n}from"./compiler-runtime-CZQb2eIb.js";import{Lt as r,Mt as i,bt as ee,vt as a}from"./lodash-ClfL87UH.js";import{t as o}from"./jsx-runtime-BapUIyWk.js";import{n as te}from"./Skeleton-D35z7Ria.js";import{r as ne}from"./hooks-UUY7pxyu.js";import{t as s}from"./react-relay-BfoHYpUf.js";import{t as c}from"./useControllableValue-BOAfgoBq.js";import{n as re,t as ie}from"./usePaginatedQuery-KRy44KD-.js";import{n as l}from"./BAIPropertyFilter-Bp3-ZYGr.js";import{t as ae}from"./BAIComplexSelect-37b7gvnf.js";var oe=n(),se=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`filter`},{defaultValue:null,kind:`LocalArgument`,name:`limit`},{defaultValue:null,kind:`LocalArgument`,name:`offset`},{defaultValue:null,kind:`LocalArgument`,name:`skipSelected`}],t=[{condition:`skipSelected`,kind:`Condition`,passingValue:!1,selections:[{alias:null,args:[{kind:`Variable`,name:`filter`,variableName:`filter`},{kind:`Variable`,name:`limit`,variableName:`limit`},{kind:`Variable`,name:`offset`,variableName:`offset`}],concreteType:`StorageVolumeList`,kind:`LinkedField`,name:`storage_volume_list`,plural:!1,selections:[{alias:null,args:null,concreteType:`StorageVolume`,kind:`LinkedField`,name:`items`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`backend`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`path`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`proxy`,storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`total_count`,storageKey:null}],storageKey:null}]}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`BAIStorageHostSelectValueQuery`,selections:t,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`BAIStorageHostSelectValueQuery`,selections:t},params:{cacheID:`52cde009974f0c6207a7ab76c95a3889`,id:null,metadata:{},name:`BAIStorageHostSelectValueQuery`,operationKind:`query`,text:`query BAIStorageHostSelectValueQuery(
  $filter: String
  $limit: Int!
  $offset: Int!
  $skipSelected: Boolean!
) {
  storage_volume_list(filter: $filter, limit: $limit, offset: $offset) @skip(if: $skipSelected) {
    items {
      id
      backend
      path
      proxy
    }
    total_count
  }
}
`}}})();se.hash=`462985640fa9c52cef6bf852f37a6a92`;var ce=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`filter`},t={defaultValue:null,kind:`LocalArgument`,name:`limit`},n={defaultValue:null,kind:`LocalArgument`,name:`offset`},r={defaultValue:null,kind:`LocalArgument`,name:`order`},i=[{alias:null,args:[{kind:`Variable`,name:`filter`,variableName:`filter`},{kind:`Variable`,name:`limit`,variableName:`limit`},{kind:`Variable`,name:`offset`,variableName:`offset`},{kind:`Variable`,name:`order`,variableName:`order`}],concreteType:`StorageVolumeList`,kind:`LinkedField`,name:`storage_volume_list`,plural:!1,selections:[{alias:null,args:null,concreteType:`StorageVolume`,kind:`LinkedField`,name:`items`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`backend`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`path`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`proxy`,storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`total_count`,storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[e,t,n,r],kind:`Fragment`,metadata:null,name:`BAIStorageHostSelectPaginatedQuery`,selections:i,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[n,t,e,r],kind:`Operation`,name:`BAIStorageHostSelectPaginatedQuery`,selections:i},params:{cacheID:`189fc8e613d64ad429013fdd5877b86b`,id:null,metadata:{},name:`BAIStorageHostSelectPaginatedQuery`,operationKind:`query`,text:`query BAIStorageHostSelectPaginatedQuery(
  $offset: Int!
  $limit: Int!
  $filter: String
  $order: String
) {
  storage_volume_list(offset: $offset, limit: $limit, filter: $filter, order: $order) {
    items {
      id
      backend
      path
      proxy
    }
    total_count
  }
}
`}}})();ce.hash=`c02d0aaac23f1d089c7cc3d04fb15d3b`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

BAIStorageHostSelect — ticket-27 Astryx sibling of
`BAIStorageHostSelect`, built on `BAIComplexSelect` (ticket 26).

FRONTIER RULE (MIGRATION-SPEC §0 "번역 프런티어" / 래퍼 정책): the antd
`BAIStorageHostSelect` is NOT touched. It keeps serving every unmigrated call
site until this wrapper's last consumer is converted. This file's OUTER
value contract is deliberately the same plain key(s) (`string | string[] |
undefined`) the antd wrapper exposes today — `labelInValue` lives strictly
between this wrapper and `BAIComplexSelect`.

`mode="multiple"` support is kept: the antd original's `onChange` already
branches on `selectProps.mode === 'multiple' || 'tags'` and its value prop is
typed `string | string[] | undefined`, so `multiple` is passed straight
through to `BAIComplexSelect` (inherited, not `Omit`-ed, from
`BAIComplexSelectProps`).

PILOT-DECISIONs:
- The antd original rendered both the trigger label and each option's label
in `BAIText monospace` via `labelRender`/`optionRender`. `label` must be a
plain string for `BAIComplexSelect` (P26-3 — it is the trigger text, the
accessible name, and the live-region text), so the monospace styling is
dropped; the storage host id string itself (already a plain, readable
identifier) is used verbatim as the label.
- antd's `notFoundContent={<Skeleton.Input/>}` first-load placeholder is
dropped (P26-7); the empty state is the shared "No results" text.
*/
var u=e(t(),1),le=s(),ue=o(),d=e=>{"use memo";var t;let n=(0,oe.c)(48),o,s,d,f,p;n[0]===e?(o=n[1],s=n[2],d=n[3],f=n[4],p=n[5]):({filter:o,multiple:p,isLoading:s,ref:d,...f}=e,n[0]=e,n[1]=o,n[2]=s,n[3]=d,n[4]=f,n[5]=p);let m=p!==void 0&&p,{t:h}=te(),g;n[6]===Symbol.for(`react.memo_cache_sentinel`)?(g={valuePropName:`value`,trigger:`onChange`},n[6]=g):g=n[6];let[_e,_]=c(f,g),v;n[7]===Symbol.for(`react.memo_cache_sentinel`)?(v={valuePropName:`open`,trigger:`onOpenChange`,defaultValuePropName:`defaultOpen`},n[7]=v):v=n[7];let[y,b]=c(f,v),x=(0,u.useDeferredValue)(y),[S,ve]=(0,u.useState)(``),C=re(S),[ye,w]=(0,u.useTransition)(),[be,T]=ne(),E=(0,u.useDeferredValue)(be),D=(0,u.useDeferredValue)(_e),O;n[8]===D?O=n[9]:(O=D??[],n[8]=D,n[9]=O);let k=i(r(O)),A=k.length?`store-or-network`:`store-only`,j;n[10]!==E||n[11]!==A?(j={fetchPolicy:A,fetchKey:E},n[10]=E,n[11]=A,n[12]=j):j=n[12];let{storage_volume_list:M}=(0,le.useLazyLoadQuery)(se,{filter:k.length?l(a(k,de),`|`):void 0,limit:Math.max(k.length,1),offset:0,skipSelected:k.length===0},j),N;n[13]===Symbol.for(`react.memo_cache_sentinel`)?(N={limit:10},n[13]=N):N=n[13];let P=C?`id ilike "%${C}%"`:null,F;n[14]!==o||n[15]!==P?(F=l([o,P]),n[14]=o,n[15]=P,n[16]=F):F=n[16];let I;n[17]===F?I=n[18]:(I={filter:F},n[17]=F,n[18]=I);let L=x?`network-only`:`store-only`,R;n[19]!==E||n[20]!==L?(R={fetchPolicy:L,fetchKey:E},n[19]=E,n[20]=L,n[21]=R):R=n[21];let z;n[22]===Symbol.for(`react.memo_cache_sentinel`)?(z={getTotal:fe,getItem:pe,getId:me},n[22]=z):z=n[22];let{paginationData:B,result:xe,loadNext:V,isLoadingNext:H}=ie(ce,N,I,R,z),U,W;n[23]===T?(U=n[24],W=n[25]):(U=()=>({refetch:()=>{w(()=>{T()})}}),W=[T,w],n[23]=T,n[24]=U,n[25]=W),(0,u.useImperativeHandle)(d,U,W);let G;n[26]===B?G=n[27]:(G=i(a(B,he)),n[26]=B,n[27]=G);let K=G,q;bb0:{let e;n[28]===(M==null?void 0:M.items)?e=n[29]:(e=e=>{let t=ee(M==null?void 0:M.items,t=>(t==null?void 0:t.id)===e);return{label:(t==null?void 0:t.id)??e,value:e}},n[28]=M==null?void 0:M.items,n[29]=e);let t=a(k,e);if(m){q=t;break bb0}q=t[0]??null}let J=q,Y;n[30]===h?Y=n[31]:(Y=h(`comp:BAIStorageHostSelect.SelectStorageHost`),n[30]=h,n[31]=Y);let X=s||!!y&&!x||_e!==D||S!==C||ye,Z=((t=xe.storage_volume_list)==null?void 0:t.total_count)??void 0,Q;n[32]!==m||n[33]!==_?(Q=e=>{let t=a(i(r(e??[])),ge);_(m?t:t[0],void 0)},n[32]=m,n[33]=_,n[34]=Q):Q=n[34];let $;return n[35]!==H||n[36]!==J||n[37]!==V||n[38]!==m||n[39]!==K||n[40]!==S||n[41]!==f||n[42]!==b||n[43]!==Y||n[44]!==X||n[45]!==Z||n[46]!==Q?($=(0,ue.jsx)(ae,{placeholder:Y,...f,multiple:m,isLoading:X,isLoadingNext:H,total:Z,options:K,value:J,onChange:Q,searchValue:S,onSearch:ve,onOpenChange:b,endReached:V}),n[35]=H,n[36]=J,n[37]=V,n[38]=m,n[39]=K,n[40]=S,n[41]=f,n[42]=b,n[43]=Y,n[44]=X,n[45]=Z,n[46]=Q,n[47]=$):$=n[47],$};function de(e){return`id == "${e}"`}function fe(e){var t;return((t=e.storage_volume_list)==null?void 0:t.total_count)??void 0}function pe(e){var t;return(t=e.storage_volume_list)==null?void 0:t.items}function me(e){return e==null?void 0:e.id}function he(e){return e!=null&&e.id?{value:e.id,label:e.id}:null}function ge(e){return e.value}export{d as t};
