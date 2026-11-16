import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";import{t as n}from"./compiler-runtime-CZQb2eIb.js";import{Lt as r,Mt as i,Y as a,vt as o}from"./lodash-ClfL87UH.js";import{t as s}from"./jsx-runtime-BapUIyWk.js";import{n as c}from"./Skeleton-D35z7Ria.js";import{r as l}from"./hooks-UUY7pxyu.js";import{t as u}from"./react-relay-BfoHYpUf.js";import{t as ee}from"./useControllableValue-BOAfgoBq.js";import{n as te,t as ne}from"./usePaginatedQuery-KRy44KD-.js";import{t as re}from"./BAIComplexSelect-37b7gvnf.js";import{t as ie}from"./BAIImageNodeSimpleTagV2-2UAD4hKM.js";var ae=n(),oe=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`ids`},{defaultValue:null,kind:`LocalArgument`,name:`scope`},{defaultValue:null,kind:`LocalArgument`,name:`skipSelected`}],t=[{condition:`skipSelected`,kind:`Condition`,passingValue:!1,selections:[{alias:null,args:[{fields:[{fields:[{kind:`Variable`,name:`in`,variableName:`ids`}],kind:`ObjectValue`,name:`id`}],kind:`ObjectValue`,name:`filter`},{kind:`Literal`,name:`limit`,value:100},{kind:`Variable`,name:`scope`,variableName:`scope`}],concreteType:`ImageV2Connection`,kind:`LinkedField`,name:`scopedImagesV2`,plural:!1,selections:[{alias:null,args:null,concreteType:`ImageV2Edge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ImageV2`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},{alias:null,args:null,concreteType:`ImageV2IdentityInfo`,kind:`LinkedField`,name:`identity`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`canonicalName`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`architecture`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`BAIScopedImageSelectValueQuery`,selections:t,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`BAIScopedImageSelectValueQuery`,selections:t},params:{cacheID:`e5d920d894b54dab01c081ce017530ae`,id:null,metadata:{},name:`BAIScopedImageSelectValueQuery`,operationKind:`query`,text:`query BAIScopedImageSelectValueQuery(
  $ids: [UUID!]
  $scope: ImageSearchScope!
  $skipSelected: Boolean!
) {
  scopedImagesV2(scope: $scope, filter: {id: {in: $ids}}, limit: 100) @skip(if: $skipSelected) {
    edges {
      node {
        id
        entityId
        identity {
          canonicalName
          architecture
        }
      }
    }
  }
}
`}}})();oe.hash=`b561b4e248e4232d7cbe02fa1199f2f5`;var se=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`filter`},t={defaultValue:null,kind:`LocalArgument`,name:`limit`},n={defaultValue:null,kind:`LocalArgument`,name:`offset`},r={defaultValue:null,kind:`LocalArgument`,name:`scope`},i=[{kind:`Variable`,name:`filter`,variableName:`filter`},{kind:`Variable`,name:`limit`,variableName:`limit`},{kind:`Variable`,name:`offset`,variableName:`offset`},{kind:`Literal`,name:`orderBy`,value:[{direction:`ASC`,field:`NAME`}]},{kind:`Variable`,name:`scope`,variableName:`scope`}],a={alias:null,args:null,kind:`ScalarField`,name:`count`,storageKey:null},o={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},s={alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},c={alias:null,args:null,concreteType:`ImageV2IdentityInfo`,kind:`LinkedField`,name:`identity`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`canonicalName`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`architecture`,storageKey:null}],storageKey:null},l=[{alias:null,args:null,kind:`ScalarField`,name:`key`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`value`,storageKey:null}];return{fragment:{argumentDefinitions:[e,t,n,r],kind:`Fragment`,metadata:null,name:`BAIScopedImageSelectPaginatedQuery`,selections:[{alias:null,args:i,concreteType:`ImageV2Connection`,kind:`LinkedField`,name:`scopedImagesV2`,plural:!1,selections:[a,{alias:null,args:null,concreteType:`ImageV2Edge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ImageV2`,kind:`LinkedField`,name:`node`,plural:!1,selections:[o,s,c,{args:null,kind:`FragmentSpread`,name:`BAIImageNodeSimpleTagV2Fragment`}],storageKey:null}],storageKey:null}],storageKey:null}],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[n,t,e,r],kind:`Operation`,name:`BAIScopedImageSelectPaginatedQuery`,selections:[{alias:null,args:i,concreteType:`ImageV2Connection`,kind:`LinkedField`,name:`scopedImagesV2`,plural:!1,selections:[a,{alias:null,args:null,concreteType:`ImageV2Edge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ImageV2`,kind:`LinkedField`,name:`node`,plural:!1,selections:[o,s,c,{alias:null,args:null,concreteType:`ImageV2MetadataInfo`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:[{alias:null,args:null,concreteType:`ImageV2TagEntry`,kind:`LinkedField`,name:`tags`,plural:!0,selections:l,storageKey:null},{alias:null,args:null,concreteType:`ImageV2LabelEntry`,kind:`LinkedField`,name:`labels`,plural:!0,selections:l,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:`f8ee299e7abdec064da93cb5d849f2cd`,id:null,metadata:{},name:`BAIScopedImageSelectPaginatedQuery`,operationKind:`query`,text:`query BAIScopedImageSelectPaginatedQuery(
  $offset: Int!
  $limit: Int!
  $filter: ImageV2Filter
  $scope: ImageSearchScope!
) {
  scopedImagesV2(scope: $scope, offset: $offset, limit: $limit, filter: $filter, orderBy: [{field: NAME, direction: ASC}]) {
    count
    edges {
      node {
        id
        entityId
        identity {
          canonicalName
          architecture
        }
        ...BAIImageNodeSimpleTagV2Fragment
      }
    }
  }
}

fragment BAIImageNodeSimpleTagV2Fragment on ImageV2 {
  identity {
    canonicalName
    architecture
  }
  metadata {
    tags {
      key
      value
    }
    labels {
      key
      value
    }
  }
}
`}}})();se.hash=`e5ee326b12a20aacacaf3cba0ddc10a4`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

BAIScopedImageSelect — Relay-paginated, id-valued image select over
`scopedImagesV2` (ADR 0012). The value is the image UUID; options are
labelled `"<canonicalName>@<architecture>"`, and a selected id missing from
the loaded pages falls back to the UUID as its label.
*/
var d=e(t(),1),ce=u(),le=s(),ue=e=>e.trim().replace(/@[^@/:]*$/,``).trimEnd(),f=e=>{"use memo";var t,n;let s=(0,ae.c)(55),u,f,p,m,h,g;s[0]===e?(u=s[1],f=s[2],p=s[3],m=s[4],h=s[5],g=s[6]):({filter:u,scope:m,multiple:g,isLoading:f,ref:p,...h}=e,s[0]=e,s[1]=u,s[2]=f,s[3]=p,s[4]=m,s[5]=h,s[6]=g);let _=g!==void 0&&g,{t:v}=c(),y;s[7]===Symbol.for(`react.memo_cache_sentinel`)?(y={valuePropName:`value`,trigger:`onChange`},s[7]=y):y=s[7];let[ve,b]=ee(h,y),x;s[8]===Symbol.for(`react.memo_cache_sentinel`)?(x={valuePropName:`open`,trigger:`onOpenChange`,defaultValuePropName:`defaultOpen`},s[8]=x):x=s[8];let[ye,S]=ee(h,x),be=(0,d.useDeferredValue)(ye),[C,xe]=(0,d.useState)(``),w=te(C),T;s[9]===w?T=s[10]:(T=ue(w),s[9]=w,s[10]=T);let E=T,[Se,Ce]=(0,d.useTransition)(),[we,D]=l(),O=(0,d.useDeferredValue)(we),k=(0,d.useDeferredValue)(ve),A;s[11]===k?A=s[12]:(A=k??[],s[11]=k,s[12]=A);let j=i(r(A)),M=j.length?`store-or-network`:`store-only`,N;s[13]!==O||s[14]!==M?(N={fetchPolicy:M,fetchKey:O},s[13]=O,s[14]=M,s[15]=N):N=s[15];let Te=(0,ce.useLazyLoadQuery)(oe,{ids:j,scope:m,skipSelected:j.length===0},N),Ee=a(i(o((t=Te.scopedImagesV2)==null?void 0:t.edges,de)),fe),P;s[16]===Symbol.for(`react.memo_cache_sentinel`)?(P={limit:20},s[16]=P):P=s[16];let F;s[17]===u?F=s[18]:(F=u??{},s[17]=u,s[18]=F);let I;s[19]===E?I=s[20]:(I=E?{name:{contains:E}}:{},s[19]=E,s[20]=I);let L;s[21]!==I||s[22]!==F?(L={...F,...I},s[21]=I,s[22]=F,s[23]=L):L=s[23];let R;s[24]!==m||s[25]!==L?(R={scope:m,filter:L},s[24]=m,s[25]=L,s[26]=R):R=s[26];let De=be?`network-only`:`store-only`,z;s[27]!==O||s[28]!==De?(z={fetchPolicy:De,fetchKey:O},s[27]=O,s[28]=De,s[29]=z):z=s[29];let B;s[30]===Symbol.for(`react.memo_cache_sentinel`)?(B={getTotal:pe,getItem:me,getId:he},s[30]=B):B=s[30];let{paginationData:V,result:Oe,loadNext:H,isLoadingNext:U}=ne(se,P,R,z,B),W,G;s[31]===D?(W=s[32],G=s[33]):(W=()=>({refetch:()=>{Ce(()=>{D()})}}),G=[D,Ce],s[31]=D,s[32]=W,s[33]=G),(0,d.useImperativeHandle)(p,W,G);let ke=ge,K;if(s[34]!==V){let e;s[36]===Symbol.for(`react.memo_cache_sentinel`)?(e=e=>{let t=e==null?void 0:e.entityId;return t?{value:t,label:ke(e==null?void 0:e.identity),labelContent:e?(0,le.jsx)(ie,{imageFrgmt:e,copyable:!1}):void 0}:null},s[36]=e):e=s[36],K=i(o(V,e)),s[34]=V,s[35]=K}else K=s[35];let q=K,J;bb0:{let e=o(j,e=>{let t=Ee[e];return{label:t?ke(t.identity):e,value:e}});if(_){J=e;break bb0}J=e[0]??null}let Y=J,X;s[37]===v?X=s[38]:(X=v(`comp:BAIImageSelect.SelectImage`),s[37]=v,s[38]=X);let Z=f||ve!==k||C!==w||Se,Ae=((n=Oe.scopedImagesV2)==null?void 0:n.count)??void 0,Q;s[39]!==_||s[40]!==b?(Q=e=>{let t=i(r(e??[])),n=o(t,_e);b(_?n:n[0],_?t:t[0])},s[39]=_,s[40]=b,s[41]=Q):Q=s[41];let $;return s[42]!==U||s[43]!==Y||s[44]!==H||s[45]!==_||s[46]!==q||s[47]!==C||s[48]!==h||s[49]!==S||s[50]!==X||s[51]!==Z||s[52]!==Ae||s[53]!==Q?($=(0,le.jsx)(re,{placeholder:X,...h,multiple:_,isLoading:Z,isLoadingNext:U,total:Ae,options:q,value:Y,onChange:Q,searchValue:C,onSearch:xe,onOpenChange:S,endReached:H}),s[42]=U,s[43]=Y,s[44]=H,s[45]=_,s[46]=q,s[47]=C,s[48]=h,s[49]=S,s[50]=X,s[51]=Z,s[52]=Ae,s[53]=Q,s[54]=$):$=s[54],$};function de(e){return e==null?void 0:e.node}function fe(e){return e.entityId}function pe(e){var t;return((t=e.scopedImagesV2)==null?void 0:t.count)??void 0}function p(e){return e==null?void 0:e.node}function me(e){var t;return(t=e.scopedImagesV2)==null||(t=t.edges)==null?void 0:t.map(p)}function he(e){return e==null?void 0:e.entityId}function ge(e){return e?`${e.canonicalName}@${e.architecture}`:``}function _e(e){return e.value}export{f as t};
