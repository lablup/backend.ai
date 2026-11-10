import{a4 as Y,l as Z,r as ee,n as ne,af as h}from"./index-CwWAznqi.js";import{u as ae,a as le}from"./usePaginatedQuery-D34XeqI8.js";import{B as te}from"./BAIComplexSelect-D8NzXrV7.js";import{m as g}from"./BAIPropertyFilter-CgtWad1r.js";import{r as u}from"./icons-BgdBQS0N.js";import{u as x}from"./useControllableValue-BmgV_ECW.js";import{e as I,J as N,m as V,c as re}from"./lodash-RhKGq0BF.js";const O=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},o={defaultValue:null,kind:"LocalArgument",name:"limit"},s={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"permission"},d={defaultValue:null,kind:"LocalArgument",name:"scopeId"},f=[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Literal",name:"order",value:"-created_at"},{kind:"Variable",name:"permission",variableName:"permission"},{kind:"Variable",name:"scope_id",variableName:"scopeId"}],concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[l,o,s,t,d],kind:"Fragment",metadata:null,name:"BAIVFolderSelectPaginatedQuery",selections:f,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[s,o,d,l,t],kind:"Operation",name:"BAIVFolderSelectPaginatedQuery",selections:f},params:{cacheID:"eddda0f4ea4f7ad2fb75f7f417cfe31d",id:null,metadata:{},name:"BAIVFolderSelectPaginatedQuery",operationKind:"query",text:`query BAIVFolderSelectPaginatedQuery(
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
`}}})();O.hash="7a6826cee67c39bf1f4841f69c578621";const C=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"first"},o={defaultValue:null,kind:"LocalArgument",name:"scopeId"},s={defaultValue:null,kind:"LocalArgument",name:"selectedFilter"},t={defaultValue:null,kind:"LocalArgument",name:"skipSelectedVFolder"},d=[{condition:"skipSelectedVFolder",kind:"Condition",passingValue:!1,selections:[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"selectedFilter"},{kind:"Variable",name:"first",variableName:"first"},{kind:"Literal",name:"permission",value:"read_attribute"},{kind:"Variable",name:"scope_id",variableName:"scopeId"}],concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]}];return{fragment:{argumentDefinitions:[l,o,s,t],kind:"Fragment",metadata:null,name:"BAIVFolderSelectValueQuery",selections:d,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[s,l,t,o],kind:"Operation",name:"BAIVFolderSelectValueQuery",selections:d},params:{cacheID:"10b4d03752ab72bdea0c8473bffc577d",id:null,metadata:{},name:"BAIVFolderSelectValueQuery",operationKind:"query",text:`query BAIVFolderSelectValueQuery(
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
`}}})();C.hash="f2f9fac35a9f022e6de82b4592e8acf2";const ie='status != "DELETE_PENDING" & status != "DELETE_ONGOING" & status != "DELETE_ERROR" & status != "DELETE_COMPLETE"',pe=({currentProjectId:l,filter:o,excludeDeleted:s,valuePropName:t="id",requiredPermission:d="read_attribute",onResolvedNamesChange:f,fallbackLabels:y,multiple:p=!1,isLoading:Q,ref:R,...k})=>{"use memo";var T;const{t:w}=Y(),[_,q]=x(k,{valuePropName:"value",trigger:"onChange"}),[L,P]=x(k,{valuePropName:"open",trigger:"onOpenChange",defaultValuePropName:"defaultOpen"}),K=u.useDeferredValue(L),[F,G]=u.useState(""),v=ae(F),[M,E]=u.useTransition(),$=g([s?ie:null,o]),[z,A]=Z(),D=u.useDeferredValue(z),B=u.useDeferredValue(_),c=I(N(B??[])),S=n=>{if(n)return t==="id"?n.id:n.row_id??void 0},{vfolder_nodes:i}=ee.useLazyLoadQuery(C,{selectedFilter:g([c.length?g(V(c,n=>`id == "${t==="id"?h(n):n}"`),"|"):null,$],"&"),first:Math.max(c.length,1),skipSelectedVFolder:c.length===0,scopeId:l?`project:${l}`:void 0},{fetchPolicy:c.length?"store-or-network":"store-only",fetchKey:D}),{paginationData:j,result:H,loadNext:J,isLoadingNext:U}=le(O,{limit:10},{filter:g([$,v?`name ilike "%${v}%"`:null]),scopeId:l?`project:${l}`:void 0,permission:d},{fetchPolicy:K?"network-only":"store-only",fetchKey:D},{getTotal:n=>{var e;return((e=n.vfolder_nodes)==null?void 0:e.count)??void 0},getItem:n=>{var e,a;return(a=(e=n.vfolder_nodes)==null?void 0:e.edges)==null?void 0:a.map(r=>r==null?void 0:r.node)},getId:n=>n==null?void 0:n.id});u.useImperativeHandle(R,()=>({refetch:()=>{E(()=>{A()})}}),[A,E]),u.useEffect(()=>{if(f&&(i!=null&&i.edges)){const n={};i.edges.forEach(e=>{var m;const a=S(e==null?void 0:e.node),r=(m=e==null?void 0:e.node)==null?void 0:m.name;a&&r&&(n[a]=r)}),f(n)}},[i]);const W=I(V(j,n=>{const e=S(n);if(!e)return null;const a=t==="id"?h(e):e;return{value:e,label:(n==null?void 0:n.name)??e,description:a}})),X=(()=>{const n=V(c,e=>{var m;const a=re(i==null?void 0:i.edges,b=>S(b==null?void 0:b.node)===e),r=(y==null?void 0:y[e])??(t==="id"?h(e)??e:e);return{label:((m=a==null?void 0:a.node)==null?void 0:m.name)??r,value:e}});return p?n:n[0]??null})();return ne.jsx(te,{placeholder:w("comp:BAIVFolderSelect.SelectFolder"),...k,multiple:p,isLoading:Q||!!L&&!K||_!==B||F!==v||M,isLoadingNext:U,total:((T=H.vfolder_nodes)==null?void 0:T.count)??void 0,options:W,value:X,onChange:n=>{const e=I(N(n??[])),a=V(e,r=>r.value);q(p?a:a[0],p?e:e[0])},searchValue:F,onSearch:G,onOpenChange:P,endReached:J})};export{pe as B};
//# sourceMappingURL=BAIVFolderSelect-BcW2gerz.js.map
