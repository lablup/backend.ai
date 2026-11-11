import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";import{t as n}from"./compiler-runtime-CZQb2eIb.js";import{Lt as r,Mt as i,bt as ee,vt as a}from"./lodash-ClfL87UH.js";import{t as o}from"./jsx-runtime-BapUIyWk.js";import{n as te}from"./Skeleton-D35z7Ria.js";import{r as ne}from"./hooks-UUY7pxyu.js";import{t as s}from"./react-relay-BfoHYpUf.js";import{t as c}from"./useControllableValue-BOAfgoBq.js";import{n as re,t as ie}from"./usePaginatedQuery-KRy44KD-.js";import{t as ae}from"./BAIComplexSelect-37b7gvnf.js";var oe=n(),l=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`projectIds`},{defaultValue:null,kind:`LocalArgument`,name:`skipSelected`}],t=[{condition:`skipSelected`,kind:`Condition`,passingValue:!1,selections:[{alias:null,args:[{fields:[{fields:[{kind:`Variable`,name:`in`,variableName:`projectIds`}],kind:`ObjectValue`,name:`id`}],kind:`ObjectValue`,name:`filter`},{kind:`Literal`,name:`limit`,value:100}],concreteType:`ProjectV2Connection`,kind:`LinkedField`,name:`adminProjectsV2`,plural:!1,selections:[{alias:null,args:null,concreteType:`ProjectV2Edge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ProjectV2`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},{alias:null,args:null,concreteType:`ProjectBasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`BAIAdminProjectSelectValueQuery`,selections:t,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`BAIAdminProjectSelectValueQuery`,selections:t},params:{cacheID:`70891ecbabe030e69ff125083dbeb5fb`,id:null,metadata:{},name:`BAIAdminProjectSelectValueQuery`,operationKind:`query`,text:`query BAIAdminProjectSelectValueQuery(
  $projectIds: [UUID!]!
  $skipSelected: Boolean!
) {
  adminProjectsV2(filter: {id: {in: $projectIds}}, limit: 100) @skip(if: $skipSelected) {
    edges {
      node {
        id
        entityId
        basicInfo {
          name
        }
      }
    }
  }
}
`}}})();l.hash=`a8a20e02a8297224ff6315d1721dba57`;var u=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`filter`},t={defaultValue:null,kind:`LocalArgument`,name:`limit`},n={defaultValue:null,kind:`LocalArgument`,name:`offset`},r=[{alias:null,args:[{kind:`Variable`,name:`filter`,variableName:`filter`},{kind:`Variable`,name:`limit`,variableName:`limit`},{kind:`Variable`,name:`offset`,variableName:`offset`},{kind:`Literal`,name:`orderBy`,value:[{direction:`ASC`,field:`NAME`}]}],concreteType:`ProjectV2Connection`,kind:`LinkedField`,name:`adminProjectsV2`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`count`,storageKey:null},{alias:null,args:null,concreteType:`ProjectV2Edge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ProjectV2`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},{alias:null,args:null,concreteType:`ProjectBasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[e,t,n],kind:`Fragment`,metadata:null,name:`BAIAdminProjectSelectPaginatedQuery`,selections:r,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[n,t,e],kind:`Operation`,name:`BAIAdminProjectSelectPaginatedQuery`,selections:r},params:{cacheID:`bd5f606eca9f7bda49cfb3391b17c896`,id:null,metadata:{},name:`BAIAdminProjectSelectPaginatedQuery`,operationKind:`query`,text:`query BAIAdminProjectSelectPaginatedQuery(
  $offset: Int!
  $limit: Int!
  $filter: ProjectV2Filter
) {
  adminProjectsV2(offset: $offset, limit: $limit, filter: $filter, orderBy: [{field: NAME, direction: ASC}]) {
    count
    edges {
      node {
        id
        entityId
        basicInfo {
          name
        }
      }
    }
  }
}
`}}})();u.hash=`4d29b458f841bf78afbcccaae9a3fa62`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

BAIAdminProjectSelect — ticket-27 Astryx sibling of the antd
`BAIAdminProjectSelect` (Relay-paginated, id-valued select pattern B,
following the recipe used across the Astryx migration).

FRONTIER RULE (MIGRATION-SPEC §0 "번역 프런티어" / 래퍼 정책): the antd
`BAIAdminProjectSelect` is NOT touched by this file. It keeps serving every
unmigrated call site until a later ticket moves them over. This file is the
Astryx-native sibling, and its OUTER value contract is deliberately the same
plain key (`string` / `string[]`) the antd wrapper exposes — labelInValue
lives strictly between the wrapper and `BAIComplexSelect`, exactly as it
does between `BAIUserSelect`/`BAIUserSelect` and `BAISelect`.

PILOT-DECISIONs:
- P26-6 The `open ? 'network-only' : 'store-only'` fetchPolicy switch is
kept — `BAIComplexSelect.onOpenChange` re-exposes the open state that
`ComplexSelector` otherwise keeps private.
- P26-7 antd's `notFoundContent={<Skeleton.Input/>}` first-load placeholder
is dropped: the empty state is the shared "No results" text.
- This wrapper's antd original had no `optionRender`/`labelRender`, so
there is no rich-content-to-`description` migration to record here.
*/
var d=e(t(),1),se=s(),ce=o(),f=e=>{"use memo";var t;let n=(0,oe.c)(51),o,s,f,p,m;n[0]===e?(o=n[1],s=n[2],f=n[3],p=n[4],m=n[5]):({filter:o,multiple:m,isLoading:s,ref:f,...p}=e,n[0]=e,n[1]=o,n[2]=s,n[3]=f,n[4]=p,n[5]=m);let h=m!==void 0&&m,{t:g}=te(),_;n[6]===Symbol.for(`react.memo_cache_sentinel`)?(_={valuePropName:`value`,trigger:`onChange`},n[6]=_):_=n[6];let[v,y]=c(p,_),b;n[7]===Symbol.for(`react.memo_cache_sentinel`)?(b={valuePropName:`open`,trigger:`onOpenChange`,defaultValuePropName:`defaultOpen`},n[7]=b):b=n[7];let[me,x]=c(p,b),he=(0,d.useDeferredValue)(me),[S,ge]=(0,d.useState)(``),C=re(S),[_e,w]=(0,d.useTransition)(),[ve,T]=ne(),E=(0,d.useDeferredValue)(ve),D=(0,d.useDeferredValue)(v),O;n[8]===D?O=n[9]:(O=D??[],n[8]=D,n[9]=O);let k=i(r(O)),A=k.length>0?`store-or-network`:`store-only`,j;n[10]!==E||n[11]!==A?(j={fetchPolicy:A,fetchKey:E},n[10]=E,n[11]=A,n[12]=j):j=n[12];let{adminProjectsV2:M}=(0,se.useLazyLoadQuery)(l,{projectIds:k,skipSelected:k.length===0},j),N;n[13]===Symbol.for(`react.memo_cache_sentinel`)?(N={limit:10},n[13]=N):N=n[13];let P;n[14]===o?P=n[15]:(P=o??{},n[14]=o,n[15]=P);let F;n[16]===C?F=n[17]:(F=C?{name:{contains:C}}:{},n[16]=C,n[17]=F);let I;n[18]!==P||n[19]!==F?(I={filter:{...P,...F}},n[18]=P,n[19]=F,n[20]=I):I=n[20];let L=he?`network-only`:`store-only`,R;n[21]!==E||n[22]!==L?(R={fetchPolicy:L,fetchKey:E},n[21]=E,n[22]=L,n[23]=R):R=n[23];let z;n[24]===Symbol.for(`react.memo_cache_sentinel`)?(z={getTotal:le,getItem:ue,getId:de},n[24]=z):z=n[24];let{paginationData:B,result:ye,loadNext:V,isLoadingNext:H}=ie(u,N,I,R,z),U,W;n[25]===T?(U=n[26],W=n[27]):(U=()=>({refetch:()=>{w(()=>{T()})}}),W=[T,w],n[25]=T,n[26]=U,n[27]=W),(0,d.useImperativeHandle)(f,U,W);let be=fe,G;if(n[28]!==B){let e;n[30]===Symbol.for(`react.memo_cache_sentinel`)?(e=e=>{var t;let n=be(e);return n?{value:n,label:(e==null||(t=e.basicInfo)==null?void 0:t.name)??n}:null},n[30]=e):e=n[30],G=i(a(B,e)),n[28]=B,n[29]=G}else G=n[29];let K=G,q;bb0:{let e;n[31]===(M==null?void 0:M.edges)?e=n[32]:(e=e=>{var t;let n=ee(M==null?void 0:M.edges,t=>be(t==null?void 0:t.node)===e);return{label:(n==null||(t=n.node)==null||(t=t.basicInfo)==null?void 0:t.name)??e,value:e}},n[31]=M==null?void 0:M.edges,n[32]=e);let t=a(k,e);if(h){q=t;break bb0}q=t[0]??null}let J=q,Y;n[33]===g?Y=n[34]:(Y=g(`comp:BAIProjectSelect.SelectProject`),n[33]=g,n[34]=Y);let X=s||!!me&&!he||v!==D||S!==C||_e,Z=((t=ye.adminProjectsV2)==null?void 0:t.count)??void 0,Q;n[35]!==h||n[36]!==y?(Q=e=>{let t=i(r(e??[])),n=a(t,pe);y(h?n:n[0],h?t:t[0])},n[35]=h,n[36]=y,n[37]=Q):Q=n[37];let $;return n[38]!==H||n[39]!==J||n[40]!==V||n[41]!==h||n[42]!==K||n[43]!==S||n[44]!==p||n[45]!==x||n[46]!==Y||n[47]!==X||n[48]!==Z||n[49]!==Q?($=(0,ce.jsx)(ae,{placeholder:Y,...p,multiple:h,isLoading:X,isLoadingNext:H,total:Z,options:K,value:J,onChange:Q,searchValue:S,onSearch:ge,onOpenChange:x,endReached:V}),n[38]=H,n[39]=J,n[40]=V,n[41]=h,n[42]=K,n[43]=S,n[44]=p,n[45]=x,n[46]=Y,n[47]=X,n[48]=Z,n[49]=Q,n[50]=$):$=n[50],$};function le(e){var t;return((t=e.adminProjectsV2)==null?void 0:t.count)??void 0}function p(e){return e==null?void 0:e.node}function ue(e){var t;return(t=e.adminProjectsV2)==null||(t=t.edges)==null?void 0:t.map(p)}function de(e){return e==null?void 0:e.entityId}function fe(e){return e==null?void 0:e.entityId}function pe(e){return e.value}export{f as t};
