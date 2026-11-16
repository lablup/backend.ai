import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{P as t,Zn as n,ht as r}from"./icons-Btg1s2wy.js";import{t as i}from"./compiler-runtime-CZQb2eIb.js";import{J as a,Mt as o,Wt as s,en as c,ot as l,vt as u}from"./lodash-ClfL87UH.js";/* empty css            */import{t as d}from"./jsx-runtime-BapUIyWk.js";import{n as f,r as p}from"./Skeleton-D35z7Ria.js";import{t as m}from"./BAIFlex-BElkJeHW.js";import{t as h}from"./BAIButton-FCOTP7us.js";import{r as ee}from"./hooks-UUY7pxyu.js";import{t as g}from"./react-relay-BfoHYpUf.js";import{t as _}from"./useControllableValue-BOAfgoBq.js";import{n as te,t as v}from"./usePaginatedQuery-KRy44KD-.js";import{o as y}from"./helper-DF1Eunoe.js";import{t as b}from"./BAIText-CtDfjLnS.js";import{t as x}from"./BAIComplexSelect-37b7gvnf.js";import{t as S}from"./react-error-boundary-DESmfvQ5.js";var ne=i(),C=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`id`},{defaultValue:null,kind:`LocalArgument`,name:`skip`}],t=[{condition:`skip`,kind:`Condition`,passingValue:!1,selections:[{alias:null,args:[{kind:`Variable`,name:`id`,variableName:`id`}],concreteType:`RuntimeVariant`,kind:`LinkedField`,name:`runtimeVariant`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`readsVfolderConfigFiles`,storageKey:null}],storageKey:null}]}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`BAIRuntimeVariantSelectValueQuery`,selections:t,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`BAIRuntimeVariantSelectValueQuery`,selections:t},params:{cacheID:`4214ff207cb6641360fac2aa5a5cf176`,id:null,metadata:{},name:`BAIRuntimeVariantSelectValueQuery`,operationKind:`query`,text:`query BAIRuntimeVariantSelectValueQuery(
  $id: UUID!
  $skip: Boolean!
) {
  runtimeVariant(id: $id) @skip(if: $skip) {
    id
    entityId
    name
    readsVfolderConfigFiles @since(version: "26.8.0")
  }
}
`}}})();C.hash=`8037dc81ff8034d5163dd318c6bd5325`;var w=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`filter`},t={defaultValue:null,kind:`LocalArgument`,name:`limit`},n={defaultValue:null,kind:`LocalArgument`,name:`offset`},r=[{alias:null,args:[{kind:`Variable`,name:`filter`,variableName:`filter`},{kind:`Variable`,name:`limit`,variableName:`limit`},{kind:`Variable`,name:`offset`,variableName:`offset`},{kind:`Literal`,name:`orderBy`,value:[{direction:`ASC`,field:`NAME`}]}],concreteType:`RuntimeVariantConnection`,kind:`LinkedField`,name:`runtimeVariants`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`count`,storageKey:null},{alias:null,args:null,concreteType:`RuntimeVariantEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`RuntimeVariant`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`readsVfolderConfigFiles`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[e,t,n],kind:`Fragment`,metadata:null,name:`BAIRuntimeVariantSelectPaginatedQuery`,selections:r,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[n,t,e],kind:`Operation`,name:`BAIRuntimeVariantSelectPaginatedQuery`,selections:r},params:{cacheID:`7e97f307f159a14a6cd7feac4967275e`,id:null,metadata:{},name:`BAIRuntimeVariantSelectPaginatedQuery`,operationKind:`query`,text:`query BAIRuntimeVariantSelectPaginatedQuery(
  $offset: Int!
  $limit: Int!
  $filter: RuntimeVariantFilter
) {
  runtimeVariants(offset: $offset, limit: $limit, filter: $filter, orderBy: [{field: NAME, direction: "ASC"}]) {
    count
    edges {
      node {
        id
        entityId
        name
        readsVfolderConfigFiles @since(version: "26.8.0")
      }
    }
  }
}
`}}})();w.hash=`2c40f4d14bfdfd9e4a20305a7c93b842`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

BAIRuntimeVariantSelect — ticket-27 Astryx sibling of
`BAIRuntimeVariantSelect`, built on `BAIComplexSelect` (ticket 26).

FRONTIER RULE (MIGRATION-SPEC §0 "번역 프런티어" / 래퍼 정책): the antd
`BAIRuntimeVariantSelect` is NOT touched. It keeps serving every unmigrated
call site until this wrapper's last consumer is converted. This file's OUTER
value contract is deliberately the same plain key (`string | undefined`) the
antd wrapper exposes today — `labelInValue` lives strictly between this
wrapper and `BAIComplexSelect`.

Single-value only: the antd original never handled `mode="multiple"` in its
`onChange`, so this sibling keeps that same single-value assumption.

PILOT-DECISIONs: none. The antd original used no `optionRender` /
`labelRender` / `onClickVFolder`-style rich rendering, so there is nothing
beyond the standard `notFoundContent={<Skeleton.Input/>}` drop (P26-7) to
record here.
*/
var T=e(n(),1),re=g(),E=d(),D=e=>{"use memo";var t;let n=(0,ne.c)(59),r,i,d,p,m;n[0]===e?(r=n[1],i=n[2],d=n[3],p=n[4],m=n[5]):({onResolvedVariantsChange:d,onResolvedNamesChange:i,isLoading:r,ref:p,...m}=e,n[0]=e,n[1]=r,n[2]=i,n[3]=d,n[4]=p,n[5]=m);let{t:h}=f(),g;n[6]===Symbol.for(`react.memo_cache_sentinel`)?(g={valuePropName:`value`,trigger:`onChange`},n[6]=g):g=n[6];let[b,S]=_(m,g),D;n[7]===Symbol.for(`react.memo_cache_sentinel`)?(D={valuePropName:`open`,trigger:`onOpenChange`,defaultValuePropName:`defaultOpen`},n[7]=D):D=n[7];let[ae,O]=_(m,D),ue=(0,T.useDeferredValue)(ae),[k,de]=(0,T.useState)(``),A=te(k),[fe,pe]=(0,T.useTransition)(),[me,j]=ee(),M=(0,T.useDeferredValue)(me),N=(0,T.useDeferredValue)(b),P;n[8]===N?P=n[9]:(P=N?y(s(N)):``,n[8]=N,n[9]=P);let F=P,he=!F,I;n[10]!==F||n[11]!==he?(I={id:F,skip:he},n[10]=F,n[11]=he,n[12]=I):I=n[12];let ge=F?`store-or-network`:`store-only`,L;n[13]!==M||n[14]!==ge?(L={fetchPolicy:ge,fetchKey:M},n[13]=M,n[14]=ge,n[15]=L):L=n[15];let{runtimeVariant:R}=(0,re.useLazyLoadQuery)(C,I,L),z;n[16]===A?z=n[17]:(z=A?{name:{iContains:A}}:null,n[16]=A,n[17]=z);let _e=z,ve;n[18]===Symbol.for(`react.memo_cache_sentinel`)?(ve={limit:20},n[18]=ve):ve=n[18];let B;n[19]===_e?B=n[20]:(B={filter:_e},n[19]=_e,n[20]=B);let ye=ue?`network-only`:`store-only`,V;n[21]!==M||n[22]!==ye?(V={fetchPolicy:ye,fetchKey:M},n[21]=M,n[22]=ye,n[23]=V):V=n[23];let H;n[24]===Symbol.for(`react.memo_cache_sentinel`)?(H={getTotal:ie,getItem:oe,getId:se},n[24]=H):H=n[24];let{paginationData:U,result:be,loadNext:xe,isLoadingNext:Se}=v(w,ve,B,V,H),W,G;n[25]===j?(W=n[26],G=n[27]):(W=()=>({refetch:()=>{pe(()=>{j()})}}),G=[j,pe],n[25]=j,n[26]=W,n[27]=G),(0,T.useImperativeHandle)(p,W,G);let K;n[28]!==i||n[29]!==d||n[30]!==U||n[31]!==R?(K=()=>{if(!d&&!i)return;let e={};R!=null&&R.entityId&&R.name&&(e[R.entityId]={name:R.name,readsVfolderConfigFiles:R.readsVfolderConfigFiles??R.name===`custom`});for(let t of U??[])t!=null&&t.entityId&&t.name&&(e[t.entityId]={name:t.name,readsVfolderConfigFiles:t.readsVfolderConfigFiles??t.name===`custom`});l(e)||(d==null||d(e),i==null||i(a(e,ce)))},n[28]=i,n[29]=d,n[30]=U,n[31]=R,n[32]=K):K=n[32];let Ce=(0,T.useEffectEvent)(K),q;n[33]===Ce?q=n[34]:(q=()=>{Ce()},n[33]=Ce,n[34]=q);let J;n[35]!==U||n[36]!==R?(J=[R,U],n[35]=U,n[36]=R,n[37]=J):J=n[37],(0,T.useEffect)(q,J);let Y;n[38]===U?Y=n[39]:(Y=o(u(U,le)),n[38]=U,n[39]=Y);let we=Y,X;n[40]!==N||n[41]!==(R==null?void 0:R.name)?(X=N?{label:(R==null?void 0:R.name)??s(N),value:s(N)}:null,n[40]=N,n[41]=R==null?void 0:R.name,n[42]=X):X=n[42];let Te=X,Z;n[43]===h?Z=n[44]:(Z=h(`comp:BAIRuntimeVariantSelect.SelectRuntimeVariant`),n[43]=h,n[44]=Z);let Ee=r||b!==N||k!==A||fe,De=((t=be.runtimeVariants)==null?void 0:t.count)??void 0,Q;n[45]===S?Q=n[46]:(Q=e=>{let t=c(e)?e[0]:e;S(t==null?void 0:t.value,t??void 0)},n[45]=S,n[46]=Q);let $;return n[47]!==Se||n[48]!==Te||n[49]!==xe||n[50]!==we||n[51]!==k||n[52]!==m||n[53]!==O||n[54]!==Z||n[55]!==Ee||n[56]!==De||n[57]!==Q?($=(0,E.jsx)(x,{placeholder:Z,...m,isLoading:Ee,isLoadingNext:Se,total:De,options:we,value:Te,onChange:Q,searchValue:k,onSearch:de,onOpenChange:O,endReached:xe}),n[47]=Se,n[48]=Te,n[49]=xe,n[50]=we,n[51]=k,n[52]=m,n[53]=O,n[54]=Z,n[55]=Ee,n[56]=De,n[57]=Q,n[58]=$):$=n[58],$};function ie(e){var t;return((t=e.runtimeVariants)==null?void 0:t.count)??void 0}function ae(e){return e==null?void 0:e.node}function oe(e){var t;return(t=e.runtimeVariants)==null||(t=t.edges)==null?void 0:t.map(ae)}function se(e){return e==null?void 0:e.id}function ce(e){return e.name}function le(e){let t=e==null?void 0:e.entityId;return t?{value:t,label:(e==null?void 0:e.name)??t}:null}var O=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`queryTemplate`}],t=[{alias:null,args:[{fields:[{kind:`Variable`,name:`queryTemplate`,variableName:`queryTemplate`}],kind:`ObjectValue`,name:`input`}],concreteType:`QueryDefinitionExecuteResult`,kind:`LinkedField`,name:`adminPreviewPrometheusQueryPreset`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null},{alias:null,args:null,concreteType:`QueryDefinitionMetricResult`,kind:`LinkedField`,name:`result`,plural:!0,selections:[{alias:null,args:null,concreteType:`QueryDefinitionMetricResultValue`,kind:`LinkedField`,name:`values`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`timestamp`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`value`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`PrometheusQueryTemplatePreviewQuery`,selections:t,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`PrometheusQueryTemplatePreviewQuery`,selections:t},params:{cacheID:`0f242107d6502f88118101fae35c21f5`,id:null,metadata:{},name:`PrometheusQueryTemplatePreviewQuery`,operationKind:`query`,text:`query PrometheusQueryTemplatePreviewQuery(
  $queryTemplate: String!
) {
  adminPreviewPrometheusQueryPreset(input: {queryTemplate: $queryTemplate}) {
    status
    result {
      values {
        timestamp
        value
      }
    }
  }
}
`}}})();O.hash=`fea104d590115a6372f88fc47d4a0607`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var ue=800,k=e=>{"use memo";let t=(0,ne.c)(11),{queryTemplate:n}=e,{t:i}=p(),a;t[0]===n?a=t[1]:(a=[n],t[0]=n,t[1]=a);let o;t[2]===i?o=t[3]:(o=e=>{let{error:t}=e;return(0,E.jsx)(m,{gap:`xxs`,children:(0,E.jsx)(b,{type:`danger`,children:pe(t,i(`autoScalingRule.QueryExecutionFailed`))})})},t[2]=i,t[3]=o);let s;t[4]===Symbol.for(`react.memo_cache_sentinel`)?(s=(0,E.jsx)(r,{className:`bai-icon-spin`,size:`1em`}),t[4]=s):s=t[4];let c;t[5]===n?c=t[6]:(c=(0,E.jsx)(T.Suspense,{fallback:s,children:(0,E.jsx)(de,{queryTemplate:n})}),t[5]=n,t[6]=c);let l;return t[7]!==a||t[8]!==o||t[9]!==c?(l=(0,E.jsx)(S,{resetKeys:a,fallbackRender:o,children:c}),t[7]=a,t[8]=o,t[9]=c,t[10]=l):l=t[10],l},de=e=>{"use memo";let n=(0,ne.c)(21),{queryTemplate:i}=e,{t:a}=p(),o;n[0]===i?o=n[1]:(o=i.trim(),n[0]=i,n[1]=o);let s=o,c;n[2]===Symbol.for(`react.memo_cache_sentinel`)?(c={wait:ue},n[2]=c):c=n[2];let l=te(s,c),[u,d]=ee(),f=(0,T.useDeferredValue)(u),g;n[3]===l?g=n[4]:(g={queryTemplate:l},n[3]=l,n[4]=g);let _=l?`network-only`:`store-only`,v;n[5]!==f||n[6]!==_?(v={fetchPolicy:_,fetchKey:f},n[5]=f,n[6]=_,n[7]=v):v=n[7];let{adminPreviewPrometheusQueryPreset:y}=(0,re.useLazyLoadQuery)(O,g,v),x=!!l&&(y==null?void 0:y.status)!==`success`,S;n[8]!==(y==null?void 0:y.result)||n[9]!==x||n[10]!==a?(S=x?null:fe(y==null?void 0:y.result,a),n[8]=y==null?void 0:y.result,n[9]=x,n[10]=a,n[11]=S):S=n[11];let C=S,w;return n[12]!==f||n[13]!==u||n[14]!==l||n[15]!==x||n[16]!==a||n[17]!==s||n[18]!==d||n[19]!==C?(w=l===s?l?x?(0,E.jsx)(m,{gap:`xxs`,children:(0,E.jsx)(b,{type:`danger`,children:a(`autoScalingRule.QueryExecutionFailed`)})}):(0,E.jsxs)(m,{gap:`xxs`,children:[(0,E.jsxs)(b,{type:`secondary`,children:[a(`autoScalingRule.CurrentValue`),`:`]}),(0,E.jsx)(b,{type:`secondary`,children:C??a(`autoScalingRule.NoDataAvailable`)}),(0,E.jsx)(h,{type:`link`,size:`small`,icon:(0,E.jsx)(t,{size:`1em`}),loading:u!==f,onClick:()=>d(),title:a(`autoScalingRule.RefreshPreview`),"aria-label":a(`autoScalingRule.RefreshPreview`)})]}):null:(0,E.jsx)(r,{className:`bai-icon-spin`,size:`1em`}),n[12]=f,n[13]=u,n[14]=l,n[15]=x,n[16]=a,n[17]=s,n[18]=d,n[19]=C,n[20]=w):w=n[20],w},A=e=>{let t=parseFloat(e);return isNaN(t)?e:(Math.round(t*100)/100).toString()},fe=(e=[],t)=>{if(e.length===1){let t=e[0].values,n=t.length>0?t[t.length-1].value:null;return n==null?null:A(n)}if(e.length>1){let n=e[0].values,r=n.length>0?n[n.length-1].value:null;return r==null?null:t(`autoScalingRule.MultipleSeriesResult`,{count:e.length,value:A(r)})}return null},pe=(e,t)=>{if(!(e instanceof Error))return t;let n=e.message.indexOf(`got error(s): `);if(n===-1)return e.message||t;let r=e.message.slice(n+14),i=r.indexOf(`See the error`);return(i===-1?r:r.slice(0,i)).trim()||t};export{D as n,k as t};
