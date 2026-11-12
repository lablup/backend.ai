import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";import{t as n}from"./compiler-runtime-CZQb2eIb.js";import{Lt as r,Mt as i,vt as a}from"./lodash-ClfL87UH.js";import{t as o}from"./jsx-runtime-BapUIyWk.js";import{n as s}from"./Skeleton-D35z7Ria.js";import{t as c}from"./react-relay-BfoHYpUf.js";import{t as l}from"./useControllableValue-BOAfgoBq.js";import{t as u}from"./BAIComplexSelect-37b7gvnf.js";var d=n(),f=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`after`},{defaultValue:null,kind:`LocalArgument`,name:`filter`},{defaultValue:10,kind:`LocalArgument`,name:`first`}],t=[{kind:`Variable`,name:`after`,variableName:`after`},{kind:`Variable`,name:`filter`,variableName:`filter`},{kind:`Variable`,name:`first`,variableName:`first`}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`BAIAdminResourceGroupSelectPaginationQuery`,selections:[{args:t,kind:`FragmentSpread`,name:`BAIAdminResourceGroupSelect_resourceGroupsFragment`}],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`BAIAdminResourceGroupSelectPaginationQuery`,selections:[{alias:null,args:t,concreteType:`ResourceGroupConnection`,kind:`LinkedField`,name:`adminResourceGroups`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`count`,storageKey:null},{alias:null,args:null,concreteType:`ResourceGroupEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ResourceGroup`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`__typename`,storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cursor`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`PageInfo`,kind:`LinkedField`,name:`pageInfo`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`endCursor`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`hasNextPage`,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:t,filters:[`filter`],handle:`connection`,key:`BAIAdminResourceGroupSelect_adminResourceGroups`,kind:`LinkedHandle`,name:`adminResourceGroups`}]},params:{cacheID:`fd4e1d0ab7a5885ce9e9a50f11d5d809`,id:null,metadata:{},name:`BAIAdminResourceGroupSelectPaginationQuery`,operationKind:`query`,text:`query BAIAdminResourceGroupSelectPaginationQuery(
  $after: String
  $filter: ResourceGroupFilter
  $first: Int = 10
) {
  ...BAIAdminResourceGroupSelect_resourceGroupsFragment_G9cLv
}

fragment BAIAdminResourceGroupSelect_resourceGroupsFragment_G9cLv on Query {
  adminResourceGroups(first: $first, after: $after, filter: $filter) {
    count
    edges {
      node {
        id
        name
        __typename
      }
      cursor
    }
    pageInfo {
      endCursor
      hasNextPage
    }
  }
}
`}}})();f.hash=`08c79340b082e35831eb5b188649ce85`;var p=(function(){var e=[`adminResourceGroups`];return{argumentDefinitions:[{defaultValue:null,kind:`LocalArgument`,name:`after`},{defaultValue:null,kind:`LocalArgument`,name:`filter`},{defaultValue:10,kind:`LocalArgument`,name:`first`}],kind:`Fragment`,metadata:{connection:[{count:`first`,cursor:`after`,direction:`forward`,path:e}],refetch:{connection:{forward:{count:`first`,cursor:`after`},backward:null,path:e},fragmentPathInResult:[],operation:f}},name:`BAIAdminResourceGroupSelect_resourceGroupsFragment`,selections:[{alias:`adminResourceGroups`,args:[{kind:`Variable`,name:`filter`,variableName:`filter`}],concreteType:`ResourceGroupConnection`,kind:`LinkedField`,name:`__BAIAdminResourceGroupSelect_adminResourceGroups_connection`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`count`,storageKey:null},{alias:null,args:null,concreteType:`ResourceGroupEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ResourceGroup`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`__typename`,storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cursor`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`PageInfo`,kind:`LinkedField`,name:`pageInfo`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`endCursor`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`hasNextPage`,storageKey:null}],storageKey:null}],storageKey:null}],type:`Query`,abstractKey:null}})();p.hash=`08c79340b082e35831eb5b188649ce85`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

BAIAdminResourceGroupSelect — ticket-27 Astryx sibling of
`BAIAdminResourceGroupSelect`.

CLASS C (CONVERSION-BRIEF §2.C): the only wrapper in this repo built on
`usePaginationFragment` (cursor pagination via a `queryRef` fragment key)
rather than `useLazyPaginatedQuery` (offset pagination). Per the brief,
`endReached` maps to `loadNext(pageSize)` and `isLoadingNext` to the hook's
own flag; nothing else about the recipe changes. The `queryRef` prop is
unchanged — parents still supply the fragment data the same way.

FRONTIER RULE: the antd `BAIAdminResourceGroupSelect` is NOT touched; it
keeps serving every unmigrated call site until callers move to this sibling.

PILOT-DECISIONs:
- resourceGroups use `name` as BOTH their primary key and display label
(see the original's own comment: "since scaling group uses name as
primary key, use name as value"). Because label and value are always
identical for this domain object, there is no separate "selected value
-> label" resolution query to keep (unlike the Relay-offset wrappers,
where the display name is a different field than the key and can go
missing from `options` after paging). `label: key, value: key` is not a
fallback here, it is definitionally correct.
- P26-7 antd's `notFoundContent={<Skeleton.Input/>}` first-load
placeholder is dropped — shared "No results" text instead.
*/
var m=e(t(),1),h=c(),g=o(),_=e=>{"use memo";var t,n;let o=(0,d.c)(38),c,f,_,x;o[0]===e?(c=o[1],f=o[2],_=o[3],x=o[4]):({queryRef:f,multiple:x,isLoading:c,..._}=e,o[0]=e,o[1]=c,o[2]=f,o[3]=_,o[4]=x);let S=x!==void 0&&x,{t:C}=s(),w;o[5]===Symbol.for(`react.memo_cache_sentinel`)?(w={valuePropName:`value`,trigger:`onChange`},o[5]=w):w=o[5];let[T,E]=l(_,w),[D,O]=(0,m.useState)(``),{data:k,loadNext:A,isLoadingNext:j,refetch:M,hasNext:N}=(0,h.usePaginationFragment)(p,f),P,F;if(o[6]!==T||o[7]!==((t=k.adminResourceGroups)==null?void 0:t.edges)||o[8]!==S){var I,L;let e;o[11]===T?e=o[12]:(e=T??[],o[11]=T,o[12]=e);let t=i(r(e)),n;if(o[13]!==((I=k.adminResourceGroups)==null?void 0:I.edges)){var R,z;n=i(a((R=k.adminResourceGroups)==null?void 0:R.edges,v)),o[13]=(z=k.adminResourceGroups)==null?void 0:z.edges,o[14]=n}else n=o[14];P=n;bb0:{let e=a(t,y);if(S){F=e;break bb0}F=e[0]??null}o[6]=T,o[7]=(L=k.adminResourceGroups)==null?void 0:L.edges,o[8]=S,o[9]=P,o[10]=F}else P=o[9],F=o[10];let B=F,V;o[15]===C?V=o[16]:(V=C(`comp:BAIAdminResourceGroupSelect.PlaceHolder`),o[15]=C,o[16]=V);let H=((n=k.adminResourceGroups)==null?void 0:n.count)??void 0,U;o[17]!==S||o[18]!==E?(U=e=>{let t=a(i(r(e??[])),b);E(S?t:t[0],void 0)},o[17]=S,o[18]=E,o[19]=U):U=o[19];let W;o[20]===M?W=o[21]:(W=e=>{O(e),M({filter:e?{name:{contains:e}}:null})},o[20]=M,o[21]=W);let G;o[22]!==N||o[23]!==A?(G=()=>{N&&A(10)},o[22]=N,o[23]=A,o[24]=G):G=o[24];let K;return o[25]!==c||o[26]!==j||o[27]!==B||o[28]!==S||o[29]!==P||o[30]!==D||o[31]!==_||o[32]!==V||o[33]!==H||o[34]!==U||o[35]!==W||o[36]!==G?(K=(0,g.jsx)(u,{placeholder:V,..._,multiple:S,isLoading:c,isLoadingNext:j,total:H,options:P,value:B,onChange:U,searchValue:D,onSearch:W,endReached:G}),o[25]=c,o[26]=j,o[27]=B,o[28]=S,o[29]=P,o[30]=D,o[31]=_,o[32]=V,o[33]=H,o[34]=U,o[35]=W,o[36]=G,o[37]=K):K=o[37],K};function v(e){var t;return e!=null&&(t=e.node)!=null&&t.name?{value:e.node.name,label:e.node.name}:null}function y(e){return{label:e,value:e}}function b(e){return e.value}export{_ as t};
