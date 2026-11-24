import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t,ut as n}from"./icons-Btg1s2wy.js";import{t as r}from"./compiler-runtime-CZQb2eIb.js";import{Lt as i,Mt as a,T as ee,bt as te,vt as o}from"./lodash-ClfL87UH.js";import{t as s}from"./jsx-runtime-BapUIyWk.js";import{n as ne}from"./Skeleton-D35z7Ria.js";import{t as c}from"./combineFilters-BLDXhHSK.js";import{r as re}from"./hooks-UUY7pxyu.js";import{t as l}from"./react-relay-BfoHYpUf.js";import{t as ie}from"./useControllableValue-BOAfgoBq.js";import{n as ae,t as oe}from"./usePaginatedQuery-KRy44KD-.js";import{t as se}from"./BAIComplexSelect-37b7gvnf.js";var ce=r(),le=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`limit`},t={defaultValue:null,kind:`LocalArgument`,name:`scope`},n={defaultValue:null,kind:`LocalArgument`,name:`selectedFilter`},r={defaultValue:null,kind:`LocalArgument`,name:`skipSelected`},i=[{condition:`skipSelected`,kind:`Condition`,passingValue:!1,selections:[{alias:null,args:[{kind:`Variable`,name:`filter`,variableName:`selectedFilter`},{kind:`Variable`,name:`limit`,variableName:`limit`},{kind:`Variable`,name:`scope`,variableName:`scope`}],concreteType:`UserV2Connection`,kind:`LinkedField`,name:`scopedUsersV2`,plural:!1,selections:[{alias:null,args:null,concreteType:`UserV2Edge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`UserV2`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},{alias:null,args:null,concreteType:`UserV2BasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`email`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`fullName`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]}];return{fragment:{argumentDefinitions:[e,t,n,r],kind:`Fragment`,metadata:null,name:`BAIScopedUserSelectValueQuery`,selections:i,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[t,n,e,r],kind:`Operation`,name:`BAIScopedUserSelectValueQuery`,selections:i},params:{cacheID:`73f803e1b9de2f6f3006e799975668d7`,id:null,metadata:{},name:`BAIScopedUserSelectValueQuery`,operationKind:`query`,text:`query BAIScopedUserSelectValueQuery(
  $scope: UserScope!
  $selectedFilter: UserV2Filter
  $limit: Int!
  $skipSelected: Boolean!
) {
  scopedUsersV2(scope: $scope, filter: $selectedFilter, limit: $limit) @skip(if: $skipSelected) {
    edges {
      node {
        id
        entityId
        basicInfo {
          email
          fullName
        }
      }
    }
  }
}
`}}})();le.hash=`411743b8638ae718f2aaa52604b93e2c`;var ue=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`filter`},t={defaultValue:null,kind:`LocalArgument`,name:`limit`},n={defaultValue:null,kind:`LocalArgument`,name:`offset`},r={defaultValue:null,kind:`LocalArgument`,name:`orderBy`},i={defaultValue:null,kind:`LocalArgument`,name:`scope`},a=[{alias:null,args:[{kind:`Variable`,name:`filter`,variableName:`filter`},{kind:`Variable`,name:`limit`,variableName:`limit`},{kind:`Variable`,name:`offset`,variableName:`offset`},{kind:`Variable`,name:`orderBy`,variableName:`orderBy`},{kind:`Variable`,name:`scope`,variableName:`scope`}],concreteType:`UserV2Connection`,kind:`LinkedField`,name:`scopedUsersV2`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`count`,storageKey:null},{alias:null,args:null,concreteType:`UserV2Edge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`UserV2`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},{alias:null,args:null,concreteType:`UserV2BasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`email`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`fullName`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[e,t,n,r,i],kind:`Fragment`,metadata:null,name:`BAIScopedUserSelectPaginatedQuery`,selections:a,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[i,n,t,e,r],kind:`Operation`,name:`BAIScopedUserSelectPaginatedQuery`,selections:a},params:{cacheID:`efde6092b86268c770cd00e780dc0fef`,id:null,metadata:{},name:`BAIScopedUserSelectPaginatedQuery`,operationKind:`query`,text:`query BAIScopedUserSelectPaginatedQuery(
  $scope: UserScope!
  $offset: Int!
  $limit: Int!
  $filter: UserV2Filter
  $orderBy: [UserV2OrderBy!]
) {
  scopedUsersV2(scope: $scope, offset: $offset, limit: $limit, filter: $filter, orderBy: $orderBy) {
    count
    edges {
      node {
        id
        entityId
        basicInfo {
          email
          fullName
        }
      }
    }
  }
}
`}}})();ue.hash=`9f76fb36f1f0267e95d5c7b6c2bf8a87`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

BAIScopedUserSelect — user picker over `scopedUsersV2` (ADR 0012), built on
`BAIComplexSelect`: offset pagination with scroll-driven `loadNext`,
server-side search, and a plain-key (`string` / `string[]`) value with
label-in-value kept inside the wrapper. The caller passes the `scope`.
*/
var u=e(t(),1),de=l(),fe=s(),pe=10,me=/^[^\s@]+@[^\s@]+\.[^\s@]+$/,d=e=>{"use memo";var t;let r=(0,ce.c)(53),s,l,d,f,p,m,h,g,_;r[0]===e?(s=r[1],l=r[2],d=r[3],f=r[4],p=r[5],m=r[6],h=r[7],g=r[8],_=r[9]):({scope:f,allowCustomSelect:m,filter:s,excludeInactive:h,valuePropName:g,multiple:_,isLoading:l,ref:d,...p}=e,r[0]=e,r[1]=s,r[2]=l,r[3]=d,r[4]=f,r[5]=p,r[6]=m,r[7]=h,r[8]=g,r[9]=_);let ye=m!==void 0&&m,be=h!==void 0&&h,v=g===void 0?`email`:g,y=_!==void 0&&_,{t:b}=ne(),x;r[10]===Symbol.for(`react.memo_cache_sentinel`)?(x={valuePropName:`value`,trigger:`onChange`},r[10]=x):x=r[10];let[xe,Se]=ie(p,x),S;r[11]===Symbol.for(`react.memo_cache_sentinel`)?(S={valuePropName:`open`,trigger:`onOpenChange`,defaultValuePropName:`defaultOpen`},r[11]=S):S=r[11];let[Ce,C]=ie(p,S),we=(0,u.useDeferredValue)(Ce),[w,Te]=(0,u.useState)(``),T=ae(w),[Ee,De]=(0,u.useTransition)(),[Oe,E]=re(),D=(0,u.useDeferredValue)(Oe),O,k;r[12]===E?(O=r[13],k=r[14]):(O=()=>({refetch:()=>{De(()=>{E()})}}),k=[E,De],r[12]=E,r[13]=O,r[14]=k),(0,u.useImperativeHandle)(d,O,k);let ke=c([be?{status:{equals:`ACTIVE`}}:null,s]),A=(0,u.useDeferredValue)(xe),j;r[15]===A?j=r[16]:(j=A??[],r[15]=A,r[16]=j);let M=a(i(j)),N=v===`id`&&M.length>0,P=N?`store-or-network`:`store-only`,F;r[17]!==D||r[18]!==P?(F={fetchPolicy:P,fetchKey:D},r[17]=D,r[18]=P,r[19]=F):F=r[19];let Ae=(0,de.useLazyLoadQuery)(le,{scope:f,selectedFilter:N?c([{uuid:{in:M}},ke]):null,limit:Math.max(M.length,1),skipSelected:!N},F),I;r[20]===Symbol.for(`react.memo_cache_sentinel`)?(I={limit:pe},r[20]=I):I=r[20];let L=we?`network-only`:`store-only`,R;r[21]!==D||r[22]!==L?(R={fetchPolicy:L,fetchKey:D},r[21]=D,r[22]=L,r[23]=R):R=r[23];let z;r[24]===Symbol.for(`react.memo_cache_sentinel`)?(z={getTotal:he,getItem:ge,getId:_e},r[24]=z):z=r[24];let{paginationData:B,result:je,loadNext:V,isLoadingNext:H}=oe(ue,I,{scope:f,filter:c([ke,T?{email:{iContains:T}}:null]),orderBy:[{field:`EMAIL`,direction:`ASC`}]},R,z),U;r[25]===v?U=r[26]:(U=e=>{var t;if(e)return v===`id`?e.entityId:((t=e.basicInfo)==null?void 0:t.email)??void 0},r[25]=v,r[26]=U);let W=U,G;r[27]===W?G=r[28]:(G=e=>{var t,n;let r=W(e);return r?{value:r,label:(e==null||(t=e.basicInfo)==null?void 0:t.email)??r,description:(e==null||(n=e.basicInfo)==null?void 0:n.fullName)??void 0}:null},r[27]=W,r[28]=G);let K=a(o(B,G)),q=T.trim(),J=ye&&v===`email`&&me.test(q)&&!ee(K,e=>e.value.toLowerCase()===q.toLowerCase())?{value:q,label:q,description:b(`comp:BAIScopedUserSelect.InviteByEmail`),icon:(0,fe.jsx)(n,{size:`1em`})}:null,Y;bb0:{var Me;let e;r[29]===W?e=r[30]:(e=e=>{var t;let n=W(e==null?void 0:e.node);return n?[n,e==null||(t=e.node)==null||(t=t.basicInfo)==null?void 0:t.email]:null},r[29]=W,r[30]=e);let t=new Map(a(o((Me=Ae.scopedUsersV2)==null?void 0:Me.edges,e))),n=o(M,e=>({label:t.get(e)??e,value:e}));if(y){Y=n;break bb0}Y=n[0]??null}let Ne=Y,X=se,Z;r[31]===b?Z=r[32]:(Z=b(`comp:BAIUserSelect.SelectUser`),r[31]=b,r[32]=Z);let Pe=l||!!Ce&&!we||xe!==A||w!==T||Ee,Fe=((t=je.scopedUsersV2)==null?void 0:t.count)??void 0,Ie=J?[...K,J]:K,Q;r[33]!==J||r[34]!==W||r[35]!==y||r[36]!==B||r[37]!==Se?(Q=e=>{let t=a(i(e??[])),n=o(t,ve),r=o(t,e=>{let t=te(B,t=>W(t)===e.value);return t?{...e,userId:t.entityId}:J&&e.value===J.value?{...e,isCustom:!0}:e});Se(y?n:n[0],y?r:r[0]),y||Te(``)},r[33]=J,r[34]=W,r[35]=y,r[36]=B,r[37]=Se,r[38]=Q):Q=r[38];let $;return r[39]!==X||r[40]!==H||r[41]!==Ne||r[42]!==V||r[43]!==y||r[44]!==w||r[45]!==p||r[46]!==C||r[47]!==Z||r[48]!==Pe||r[49]!==Fe||r[50]!==Ie||r[51]!==Q?($=(0,fe.jsx)(X,{placeholder:Z,...p,multiple:y,isLoading:Pe,isLoadingNext:H,total:Fe,options:Ie,value:Ne,onChange:Q,searchValue:w,onSearch:Te,onOpenChange:C,endReached:V}),r[39]=X,r[40]=H,r[41]=Ne,r[42]=V,r[43]=y,r[44]=w,r[45]=p,r[46]=C,r[47]=Z,r[48]=Pe,r[49]=Fe,r[50]=Ie,r[51]=Q,r[52]=$):$=r[52],$};function he(e){var t;return((t=e.scopedUsersV2)==null?void 0:t.count)??void 0}function ge(e){var t;return a(o((t=e.scopedUsersV2)==null?void 0:t.edges,`node`))}function _e(e){return e==null?void 0:e.id}function ve(e){return e.value}export{d as t};
