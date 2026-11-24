import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";import{Lt as n,Mt as r,bt as i,vt as a}from"./lodash-ClfL87UH.js";import{t as o}from"./jsx-runtime-BapUIyWk.js";import{n as s}from"./Skeleton-D35z7Ria.js";import{r as c}from"./hooks-UUY7pxyu.js";import{t as l}from"./react-relay-BfoHYpUf.js";import{t as u}from"./useControllableValue-BOAfgoBq.js";import{n as d,t as f}from"./usePaginatedQuery-KRy44KD-.js";import{C as p}from"./helper-DF1Eunoe.js";import{n as m}from"./BAIPropertyFilter-Bp3-ZYGr.js";import{t as h}from"./BAIComplexSelect-37b7gvnf.js";var g=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`first`},t={defaultValue:null,kind:`LocalArgument`,name:`scopeId`},n={defaultValue:null,kind:`LocalArgument`,name:`selectedFilter`},r={defaultValue:null,kind:`LocalArgument`,name:`skipSelectedVFolder`},i=[{condition:`skipSelectedVFolder`,kind:`Condition`,passingValue:!1,selections:[{alias:null,args:[{kind:`Variable`,name:`filter`,variableName:`selectedFilter`},{kind:`Variable`,name:`first`,variableName:`first`},{kind:`Literal`,name:`permission`,value:`read_attribute`},{kind:`Variable`,name:`scope_id`,variableName:`scopeId`}],concreteType:`VirtualFolderConnection`,kind:`LinkedField`,name:`vfolder_nodes`,plural:!1,selections:[{alias:null,args:null,concreteType:`VirtualFolderEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`VirtualFolderNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`row_id`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]}];return{fragment:{argumentDefinitions:[e,t,n,r],kind:`Fragment`,metadata:null,name:`BAIVFolderSelectValueQuery`,selections:i,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[n,e,r,t],kind:`Operation`,name:`BAIVFolderSelectValueQuery`,selections:i},params:{cacheID:`10b4d03752ab72bdea0c8473bffc577d`,id:null,metadata:{},name:`BAIVFolderSelectValueQuery`,operationKind:`query`,text:`query BAIVFolderSelectValueQuery(
  $selectedFilter: String
  $first: Int!
  $skipSelectedVFolder: Boolean!
  $scopeId: ScopeField
) {
  vfolder_nodes(scope_id: $scopeId, filter: $selectedFilter, first: $first, permission: "read_attribute") @skip(if: $skipSelectedVFolder) {
    edges {
      node {
        name
        id
        row_id
      }
    }
  }
}
`}}})();g.hash=`f2f9fac35a9f022e6de82b4592e8acf2`;var _=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`filter`},t={defaultValue:null,kind:`LocalArgument`,name:`limit`},n={defaultValue:null,kind:`LocalArgument`,name:`offset`},r={defaultValue:null,kind:`LocalArgument`,name:`permission`},i={defaultValue:null,kind:`LocalArgument`,name:`scopeId`},a=[{alias:null,args:[{kind:`Variable`,name:`filter`,variableName:`filter`},{kind:`Variable`,name:`first`,variableName:`limit`},{kind:`Variable`,name:`offset`,variableName:`offset`},{kind:`Literal`,name:`order`,value:`-created_at`},{kind:`Variable`,name:`permission`,variableName:`permission`},{kind:`Variable`,name:`scope_id`,variableName:`scopeId`}],concreteType:`VirtualFolderConnection`,kind:`LinkedField`,name:`vfolder_nodes`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`count`,storageKey:null},{alias:null,args:null,concreteType:`VirtualFolderEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`VirtualFolderNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`row_id`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[e,t,n,r,i],kind:`Fragment`,metadata:null,name:`BAIVFolderSelectPaginatedQuery`,selections:a,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[n,t,i,e,r],kind:`Operation`,name:`BAIVFolderSelectPaginatedQuery`,selections:a},params:{cacheID:`eddda0f4ea4f7ad2fb75f7f417cfe31d`,id:null,metadata:{},name:`BAIVFolderSelectPaginatedQuery`,operationKind:`query`,text:`query BAIVFolderSelectPaginatedQuery(
  $offset: Int!
  $limit: Int!
  $scopeId: ScopeField
  $filter: String
  $permission: VFolderPermissionValueField
) {
  vfolder_nodes(scope_id: $scopeId, offset: $offset, first: $limit, filter: $filter, permission: $permission, order: "-created_at") {
    count
    edges {
      node {
        id
        name
        row_id
      }
    }
  }
}
`}}})();_.hash=`7a6826cee67c39bf1f4841f69c578621`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

BAIVFolderSelect — ticket-27 Astryx sibling of `BAIVFolderSelect`,
built on `BAIComplexSelect` (ticket 26).

FRONTIER RULE (MIGRATION-SPEC §0 "번역 프런티어" / 래퍼 정책): the antd
`BAIVFolderSelect` is NOT touched. It keeps serving every unmigrated call
site until this wrapper's last consumer is converted. This file's OUTER
value contract is deliberately the same plain key(s) (`string | string[] |
undefined`) the antd wrapper exposes today — `labelInValue` lives strictly
between this wrapper and `BAIComplexSelect`.

KEY SEMANTICS ARE UNCHANGED from the antd original: when `valuePropName`
is `'id'` the outer key is the raw Relay **global** id (`node.id`, NOT
`toLocalId`-converted). `toLocalId` is used only for
display (the secondary id text) and to build the local-UUID filter value for
the value-resolution query, exactly as the antd `labelRender`/`optionRender`
did. When `valuePropName` is `'row_id'` the outer key is the raw UUID
(`node.row_id`), also unchanged.

`mode="multiple"` support is kept: the antd original's `onChange` already
branches on `selectProps.mode === 'multiple' || 'tags'` and its value prop is
typed `string | string[] | undefined`, so `multiple` is passed straight
through to `BAIComplexSelect` (inherited, not `Omit`-ed, from
`BAIComplexSelectProps`).

PILOT-DECISIONs:
- antd `onClickVFolder` made the TRIGGER's rendered label a clickable
`BAILink` when nothing was being searched. `BAIComplexSelect`'s trigger
only prints `value.label` as plain text (P26-3/P26-4), so
`onClickVFolder` is dropped entirely from the props interface.
- The secondary monospace "(id)" text that every option row showed via
`optionRender` moves into each option's `description` slot.
- antd's `notFoundContent={<Skeleton.Input/>}` first-load placeholder is
dropped (P26-7); the empty state is the shared "No results" text.
*/
var v=e(t(),1),y=l(),b=o(),x=`status != "DELETE_PENDING" & status != "DELETE_ONGOING" & status != "DELETE_ERROR" & status != "DELETE_COMPLETE"`,S=({currentProjectId:e,filter:t,excludeDeleted:o,valuePropName:l=`id`,requiredPermission:S=`read_attribute`,onResolvedNamesChange:C,fallbackLabels:w,multiple:T=!1,isLoading:E,ref:D,...O})=>{"use memo";var k;let{t:A}=s(),[j,M]=u(O,{valuePropName:`value`,trigger:`onChange`}),[N,P]=u(O,{valuePropName:`open`,trigger:`onOpenChange`,defaultValuePropName:`defaultOpen`}),F=(0,v.useDeferredValue)(N),[I,L]=(0,v.useState)(``),R=d(I),[z,B]=(0,v.useTransition)(),V=m([o?x:null,t]),[H,U]=c(),W=(0,v.useDeferredValue)(H),G=(0,v.useDeferredValue)(j),K=r(n(G??[])),q=e=>{if(e)return l===`id`?e.id:e.row_id??void 0},{vfolder_nodes:J}=(0,y.useLazyLoadQuery)(g,{selectedFilter:m([K.length?m(a(K,e=>`id == "${l===`id`?p(e):e}"`),`|`):null,V],`&`),first:Math.max(K.length,1),skipSelectedVFolder:K.length===0,scopeId:e?`project:${e}`:void 0},{fetchPolicy:K.length?`store-or-network`:`store-only`,fetchKey:W}),{paginationData:Y,result:X,loadNext:Z,isLoadingNext:Q}=f(_,{limit:10},{filter:m([V,R?`name ilike "%${R}%"`:null]),scopeId:e?`project:${e}`:void 0,permission:S},{fetchPolicy:F?`network-only`:`store-only`,fetchKey:W},{getTotal:e=>{var t;return((t=e.vfolder_nodes)==null?void 0:t.count)??void 0},getItem:e=>{var t;return(t=e.vfolder_nodes)==null||(t=t.edges)==null?void 0:t.map(e=>e==null?void 0:e.node)},getId:e=>e==null?void 0:e.id});(0,v.useImperativeHandle)(D,()=>({refetch:()=>{B(()=>{U()})}}),[U,B]),(0,v.useEffect)(()=>{if(C&&J!=null&&J.edges){let e={};J.edges.forEach(t=>{var n;let r=q(t==null?void 0:t.node),i=t==null||(n=t.node)==null?void 0:n.name;r&&i&&(e[r]=i)}),C(e)}},[J]);let $=r(a(Y,e=>{let t=q(e);if(!t)return null;let n=l===`id`?p(t):t;return{value:t,label:(e==null?void 0:e.name)??t,description:n}})),ee=(()=>{let e=a(K,e=>{var t;let n=i(J==null?void 0:J.edges,t=>q(t==null?void 0:t.node)===e),r=(w==null?void 0:w[e])??(l===`id`?p(e)??e:e);return{label:(n==null||(t=n.node)==null?void 0:t.name)??r,value:e}});return T?e:e[0]??null})();return(0,b.jsx)(h,{placeholder:A(`comp:BAIVFolderSelect.SelectFolder`),...O,multiple:T,isLoading:E||!!N&&!F||j!==G||I!==R||z,isLoadingNext:Q,total:((k=X.vfolder_nodes)==null?void 0:k.count)??void 0,options:$,value:ee,onChange:e=>{let t=r(n(e??[])),i=a(t,e=>e.value);M(T?i:i[0],T?t:t[0])},searchValue:I,onSearch:L,onOpenChange:P,endReached:Z})};export{S as t};
