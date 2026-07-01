import{ad as A,r as F,i as S,a6 as b,j as s,bA as R,b6 as K,cn as I,bi as h,aw as _}from"./index-r5M52Un8.js";const d=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"after"},{defaultValue:null,kind:"LocalArgument",name:"filter"},{defaultValue:10,kind:"LocalArgument",name:"first"}],a=[{kind:"Variable",name:"after",variableName:"after"},{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"first"}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"BAIAdminResourceGroupSelectPaginationQuery",selections:[{args:a,kind:"FragmentSpread",name:"BAIAdminResourceGroupSelect_resourceGroupsFragment"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"BAIAdminResourceGroupSelectPaginationQuery",selections:[{alias:null,args:a,concreteType:"ResourceGroupConnection",kind:"LinkedField",name:"resourceGroups",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},{alias:null,args:null,concreteType:"ResourceGroupEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ResourceGroup",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cursor",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PageInfo",kind:"LinkedField",name:"pageInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endCursor",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"hasNextPage",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:a,filters:["filter"],handle:"connection",key:"BAIAdminResourceGroupSelect_resourceGroups",kind:"LinkedHandle",name:"resourceGroups"}]},params:{cacheID:"1a90a27c601f1d11dcd17163dbcfabbe",id:null,metadata:{},name:"BAIAdminResourceGroupSelectPaginationQuery",operationKind:"query",text:`query BAIAdminResourceGroupSelectPaginationQuery(
  $after: String
  $filter: ResourceGroupFilter
  $first: Int = 10
) {
  ...BAIAdminResourceGroupSelect_resourceGroupsFragment_G9cLv
}

fragment BAIAdminResourceGroupSelect_resourceGroupsFragment_G9cLv on Query {
  resourceGroups(first: $first, after: $after, filter: $filter) @since(version: "26.1.0") {
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
`}}}();d.hash="97c2e022b1e40671b4d0311dbd4912ec";const m=function(){var e=["resourceGroups"];return{argumentDefinitions:[{defaultValue:null,kind:"LocalArgument",name:"after"},{defaultValue:null,kind:"LocalArgument",name:"filter"},{defaultValue:10,kind:"LocalArgument",name:"first"}],kind:"Fragment",metadata:{connection:[{count:"first",cursor:"after",direction:"forward",path:e}],refetch:{connection:{forward:{count:"first",cursor:"after"},backward:null,path:e},fragmentPathInResult:[],operation:d}},name:"BAIAdminResourceGroupSelect_resourceGroupsFragment",selections:[{alias:"resourceGroups",args:[{kind:"Variable",name:"filter",variableName:"filter"}],concreteType:"ResourceGroupConnection",kind:"LinkedField",name:"__BAIAdminResourceGroupSelect_resourceGroups_connection",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},{alias:null,args:null,concreteType:"ResourceGroupEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ResourceGroup",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cursor",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PageInfo",kind:"LinkedField",name:"pageInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endCursor",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"hasNextPage",storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null}}();m.hash="97c2e022b1e40671b4d0311dbd4912ec";const B=({queryRef:e,loading:a,...r})=>{var o,t;const{t:g}=A(),u=F.useRef(null),{data:l,loadNext:p,isLoadingNext:f,refetch:k,hasNext:y}=S.usePaginationFragment(m,e),G=b((o=l.resourceGroups)==null?void 0:o.edges,n=>({label:n.node.name,value:n.node.name}));return s.jsx(R,{ref:u,placeholder:g("comp:BAIAdminResourceGroupSelect.PlaceHolder"),showSearch:{autoClearSearchValue:!0,filterOption:!1},loading:a,options:G,...r,searchAction:async n=>{var i,c;(i=u.current)==null||i.scrollTo(0),k({filter:n?{name:{contains:n}}:null}),await((c=r.searchAction)==null?void 0:c.call(r,n))},endReached:()=>{y&&p(10)},notFoundContent:h(l)?s.jsx(_.Input,{active:!0,size:"small",block:!0}):void 0,footer:K((t=l.resourceGroups)==null?void 0:t.count)&&l.resourceGroups.count>0?s.jsx(I,{loading:f,total:l.resourceGroups.count}):void 0})};export{B};
//# sourceMappingURL=BAIAdminResourceGroupSelect-CpJJPia8.js.map
