import{aA as Y,bj as B,l as u,n as Z,e3 as p,aN as ee,bn as h,df as N,r as ne,al as g,dg as ae,j as le,dh as te,N as I,ap as re}from"./index-DPebpL40.js";const O=(function(){var t={defaultValue:null,kind:"LocalArgument",name:"filter"},o={defaultValue:null,kind:"LocalArgument",name:"limit"},s={defaultValue:null,kind:"LocalArgument",name:"offset"},l={defaultValue:null,kind:"LocalArgument",name:"permission"},d={defaultValue:null,kind:"LocalArgument",name:"scopeId"},f=[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Literal",name:"order",value:"-created_at"},{kind:"Variable",name:"permission",variableName:"permission"},{kind:"Variable",name:"scope_id",variableName:"scopeId"}],concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[t,o,s,l,d],kind:"Fragment",metadata:null,name:"BAIVFolderSelectPaginatedQuery",selections:f,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[s,o,d,t,l],kind:"Operation",name:"BAIVFolderSelectPaginatedQuery",selections:f},params:{cacheID:"eddda0f4ea4f7ad2fb75f7f417cfe31d",id:null,metadata:{},name:"BAIVFolderSelectPaginatedQuery",operationKind:"query",text:`query BAIVFolderSelectPaginatedQuery(
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
`}}})();O.hash="7a6826cee67c39bf1f4841f69c578621";const C=(function(){var t={defaultValue:null,kind:"LocalArgument",name:"first"},o={defaultValue:null,kind:"LocalArgument",name:"scopeId"},s={defaultValue:null,kind:"LocalArgument",name:"selectedFilter"},l={defaultValue:null,kind:"LocalArgument",name:"skipSelectedVFolder"},d=[{condition:"skipSelectedVFolder",kind:"Condition",passingValue:!1,selections:[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"selectedFilter"},{kind:"Variable",name:"first",variableName:"first"},{kind:"Literal",name:"permission",value:"read_attribute"},{kind:"Variable",name:"scope_id",variableName:"scopeId"}],concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]}];return{fragment:{argumentDefinitions:[t,o,s,l],kind:"Fragment",metadata:null,name:"BAIVFolderSelectValueQuery",selections:d,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[s,t,l,o],kind:"Operation",name:"BAIVFolderSelectValueQuery",selections:d},params:{cacheID:"10b4d03752ab72bdea0c8473bffc577d",id:null,metadata:{},name:"BAIVFolderSelectValueQuery",operationKind:"query",text:`query BAIVFolderSelectValueQuery(
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
`}}})();C.hash="f2f9fac35a9f022e6de82b4592e8acf2";const ie='status != "DELETE_PENDING" & status != "DELETE_ONGOING" & status != "DELETE_ERROR" & status != "DELETE_COMPLETE"',se=({currentProjectId:t,filter:o,excludeDeleted:s,valuePropName:l="id",requiredPermission:d="read_attribute",onResolvedNamesChange:f,fallbackLabels:V,multiple:y=!1,isLoading:Q,ref:R,...k})=>{"use memo";var x;const{t:w}=Y(),[_,q]=B(k,{valuePropName:"value",trigger:"onChange"}),[L,P]=B(k,{valuePropName:"open",trigger:"onOpenChange",defaultValuePropName:"defaultOpen"}),K=u.useDeferredValue(L),[F,j]=u.useState(""),v=Z(F),[G,$]=u.useTransition(),A=p([s?ie:null,o]),[M,E]=ee(),D=u.useDeferredValue(M),T=u.useDeferredValue(_),c=h(N(T??[])),S=n=>{if(n)return l==="id"?n.id:n.row_id??void 0},{vfolder_nodes:r}=ne.useLazyLoadQuery(C,{selectedFilter:p([c.length?p(g(c,n=>{const e=l==="id"?I(n):n;return`${l} == "${e}"`}),"|"):null,A],"&"),first:Math.max(c.length,1),skipSelectedVFolder:c.length===0,scopeId:t?`project:${t}`:void 0},{fetchPolicy:c.length?"store-or-network":"store-only",fetchKey:D}),{paginationData:z,result:H,loadNext:J,isLoadingNext:U}=ae(O,{limit:10},{filter:p([A,v?`name ilike "%${v}%"`:null]),scopeId:t?`project:${t}`:void 0,permission:d},{fetchPolicy:K?"network-only":"store-only",fetchKey:D},{getTotal:n=>{var e;return((e=n.vfolder_nodes)==null?void 0:e.count)??void 0},getItem:n=>{var e,a;return(a=(e=n.vfolder_nodes)==null?void 0:e.edges)==null?void 0:a.map(i=>i==null?void 0:i.node)},getId:n=>n==null?void 0:n.id});u.useImperativeHandle(R,()=>({refetch:()=>{$(()=>{E()})}}),[E,$]),u.useEffect(()=>{if(f&&(r!=null&&r.edges)){const n={};r.edges.forEach(e=>{var m;const a=S(e==null?void 0:e.node),i=(m=e==null?void 0:e.node)==null?void 0:m.name;a&&i&&(n[a]=i)}),f(n)}},[r]);const W=h(g(z,n=>{const e=S(n);if(!e)return null;const a=l==="id"?I(e):e;return{value:e,label:(n==null?void 0:n.name)??e,description:a}})),X=(()=>{const n=g(c,e=>{var m;const a=re(r==null?void 0:r.edges,b=>S(b==null?void 0:b.node)===e),i=(V==null?void 0:V[e])??(l==="id"?I(e)??e:e);return{label:((m=a==null?void 0:a.node)==null?void 0:m.name)??i,value:e}});return y?n:n[0]??null})();return le.jsx(te,{placeholder:w("comp:BAIVFolderSelect.SelectFolder"),...k,multiple:y,isLoading:Q||!!L&&!K||_!==T||F!==v||G,isLoadingNext:U,total:((x=H.vfolder_nodes)==null?void 0:x.count)??void 0,options:W,value:X,onChange:n=>{const e=g(h(N(n??[])),a=>a.value);q(y?e:e[0],void 0)},searchValue:F,onSearch:j,onOpenChange:P,endReached:J})};export{se as B};
//# sourceMappingURL=BAIVFolderSelect-BEmbOfAF.js.map
