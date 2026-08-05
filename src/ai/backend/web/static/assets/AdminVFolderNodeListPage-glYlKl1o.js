import{u as z,t as U,a as W,aa as Y,r as I,o as D,aY as H,a4 as X,a5 as E,bE as Z,d8 as J,k as ee,j as n,B as p,bJ as ne,Z as ae,ac as N,c2 as le,a7 as te,b2 as re,bu as B,aq as O,j8 as oe,K as w,j9 as se,bX as ie,b4 as de,ja as ue,ab as ge,b7 as q,dF as me,aN as $,jb as ce,jc as Fe,jd as pe,ad as fe,ar as ye}from"./index-DB7yUW94.js";const G=(function(){var V={defaultValue:null,kind:"LocalArgument",name:"filter"},a={defaultValue:null,kind:"LocalArgument",name:"filterForActiveCount"},d={defaultValue:null,kind:"LocalArgument",name:"filterForDeletedCount"},u={defaultValue:null,kind:"LocalArgument",name:"first"},C={defaultValue:null,kind:"LocalArgument",name:"offset"},h={defaultValue:null,kind:"LocalArgument",name:"order"},o={defaultValue:null,kind:"LocalArgument",name:"permission"},t={kind:"Variable",name:"permission",variableName:"permission"},b=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"order",variableName:"order"},t],g={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},K={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},F={alias:null,args:null,kind:"ScalarField",name:"permissions",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},y={kind:"Literal",name:"first",value:0},k={kind:"Literal",name:"offset",value:0},m=[f],c={alias:"active",args:[{kind:"Variable",name:"filter",variableName:"filterForActiveCount"},y,k,t],concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:m,storageKey:null},l={alias:"deleted",args:[{kind:"Variable",name:"filter",variableName:"filterForDeletedCount"},y,k,t],concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:m,storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},_={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null};return{fragment:{argumentDefinitions:[V,a,d,u,C,h,o],kind:"Fragment",metadata:null,name:"AdminVFolderNodeListPageQuery",selections:[{alias:null,args:b,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:g,action:"THROW"},K,F,{args:null,kind:"FragmentSpread",name:"VFolderNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeleteVFolderModalFragment"},{args:null,kind:"FragmentSpread",name:"EditableVFolderNameFragment"},{args:null,kind:"FragmentSpread",name:"RestoreVFolderModalFragment"},{args:null,kind:"FragmentSpread",name:"VFolderNodeIdenticonFragment"},{args:null,kind:"FragmentSpread",name:"SharedFolderPermissionInfoModalFragment"},{args:null,kind:"FragmentSpread",name:"BAIVFolderDeleteButtonFragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},f],storageKey:null},c,l],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[C,u,V,h,o,a,d],kind:"Operation",name:"AdminVFolderNodeListPageQuery",selections:[{alias:null,args:b,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[g,K,F,s,{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quota_scope_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownership_type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"group_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"usage_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"max_files",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"max_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"last_used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"num_files",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cur_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null},F,_,{alias:null,args:null,kind:"ScalarField",name:"creator",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{kind:"InlineFragment",selections:[{kind:"InlineFragment",selections:[S,{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},g,_,{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[s,g],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null}],type:"ComputeSessionNode",abstractKey:null},{kind:"InlineFragment",selections:[S,{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[s],storageKey:null}],type:"VFolder",abstractKey:null},{kind:"InlineFragment",selections:[S],type:"VirtualFolderNode",abstractKey:null}],type:"Node",abstractKey:"__isNode"}],storageKey:null}],storageKey:null},f],storageKey:null},c,l]},params:{cacheID:"d8850204541e90e662e6da1b08462675",id:null,metadata:{},name:"AdminVFolderNodeListPageQuery",operationKind:"query",text:`query AdminVFolderNodeListPageQuery(
  $offset: Int
  $first: Int
  $filter: String
  $order: String
  $permission: VFolderPermissionValueField
  $filterForActiveCount: String
  $filterForDeletedCount: String
) {
  vfolder_nodes(offset: $offset, first: $first, filter: $filter, order: $order, permission: $permission) {
    edges {
      node {
        id
        status
        permissions
        ...VFolderNodesFragment
        ...DeleteVFolderModalFragment
        ...EditableVFolderNameFragment
        ...RestoreVFolderModalFragment
        ...VFolderNodeIdenticonFragment
        ...SharedFolderPermissionInfoModalFragment
        ...BAIVFolderDeleteButtonFragment
      }
    }
    count
  }
  active: vfolder_nodes(first: 0, offset: 0, filter: $filterForActiveCount, permission: $permission) {
    count
  }
  deleted: vfolder_nodes(first: 0, offset: 0, filter: $filterForDeletedCount, permission: $permission) {
    count
  }
}

fragment AppLaunchConfirmationModalFragment on ComputeSessionNode {
  id
  row_id
  name
  ...useBackendAIAppLauncherFragment
}

fragment AppLauncherModalFragment on ComputeSessionNode {
  id
  row_id
  name
  service_ports
  access_key
  ...useBackendAIAppLauncherFragment
  ...SFTPConnectionInfoModalFragment
  ...TensorboardPathModalFragment
  ...AppLaunchConfirmationModalFragment
}

fragment BAIComputeSessionNodeNotificationItemFragment on ComputeSessionNode {
  id
  name
  status
  status_info
  status_data
  ...SessionActionButtonsFragment
  ...SessionStatusTagFragment
}

fragment BAINodeNotificationItemFragment on Node {
  __isNode: __typename
  ... on ComputeSessionNode {
    __typename
    status
    name
    row_id
    ...BAIComputeSessionNodeNotificationItemFragment
  }
  ... on VFolder {
    __typename
    ...BAIVirtualFolderNodeNotificationItemV2Fragment
  }
  ... on VirtualFolderNode {
    __typename
    status
    ...BAIVirtualFolderNodeNotificationItemFragment
  }
  id
}

fragment BAIVFolderDeleteButtonFragment on VirtualFolderNode {
  permissions
}

fragment BAIVirtualFolderNodeNotificationItemFragment on VirtualFolderNode {
  row_id
  id
  name
  status
}

fragment BAIVirtualFolderNodeNotificationItemV2Fragment on VFolder {
  id
  metadata {
    name
  }
}

fragment ContainerCommitModalFragment on ComputeSessionNode {
  id
  name
  row_id
}

fragment ContainerLogModalFragment on ComputeSessionNode {
  id
  row_id
  name
  status
  access_key
  kernel_nodes {
    edges {
      node {
        id
        row_id
        container_id
        cluster_idx
        cluster_role
        cluster_hostname
      }
    }
  }
}

fragment DeleteVFolderModalFragment on VirtualFolderNode {
  id
  name
  permissions
}

fragment EditableVFolderNameFragment on VirtualFolderNode {
  id
  name
  user
  group
  status
}

fragment RestoreVFolderModalFragment on VirtualFolderNode {
  id
  name
}

fragment SFTPConnectionInfoModalFragment on ComputeSessionNode {
  row_id
  vfolder_nodes @since(version: "25.4.0") {
    edges {
      node {
        name
        id
      }
    }
  }
}

fragment SessionActionButtonsFragment on ComputeSessionNode {
  id
  name
  row_id
  type
  status
  access_key
  service_ports
  commit_status
  user_id
  ...TerminateSessionModalFragment
  ...ContainerLogModalFragment
  ...ContainerCommitModalFragment
  ...AppLauncherModalFragment
  ...SFTPConnectionInfoModalFragment
  ...useBackendAIAppLauncherFragment
}

fragment SessionStatusTagFragment on ComputeSessionNode {
  id
  status
  status_info
  status_data
  queue_position @since(version: "25.13.0")
}

fragment SharedFolderPermissionInfoModalFragment on VirtualFolderNode {
  id
  name
  row_id
  creator
  ownership_type
  user_email
  permission
  ...VFolderPermissionCellFragment
}

fragment TensorboardPathModalFragment on ComputeSessionNode {
  id
  row_id
  name
  ...useBackendAIAppLauncherFragment
}

fragment TerminateSessionModalFragment on ComputeSessionNode {
  id
  row_id
  name
  scaling_group
  access_key
  project_id
  kernel_nodes {
    edges {
      node {
        container_id
        agent_id
        id
      }
    }
  }
}

fragment VFolderNodeIdenticonFragment on VirtualFolderNode {
  id
}

fragment VFolderNodesFragment on VirtualFolderNode {
  id
  status
  name
  host
  quota_scope_id
  ownership_type
  user
  user_email
  group
  group_name
  usage_mode
  max_files
  max_size
  created_at
  last_used
  num_files
  cur_size
  cloneable
  permissions @since(version: "24.09.0")
  ...VFolderPermissionCellFragment
  ...VFolderNodeIdenticonFragment
  ...SharedFolderPermissionInfoModalFragment
  ...BAINodeNotificationItemFragment
}

fragment VFolderPermissionCellFragment on VirtualFolderNode {
  permissions
}

fragment useBackendAIAppLauncherFragment on ComputeSessionNode {
  name
  row_id
  vfolder_mounts
  scaling_group
  project_id
  service_ports
}
`}}})();G.hash="61335271ca378f8ff80cff73517798c7";const ke=["READY","PERFORMING","CLONING","MOUNTED","ERROR","DELETE_PENDING","DELETE_ONGOING","DELETE_COMPLETE","DELETE_ERROR"],T={active:'status != "DELETE_PENDING" & status != "DELETE_ONGOING" & status != "DELETE_ERROR" & status != "DELETE_COMPLETE"',deleted:'status in ["DELETE_PENDING", "DELETE_ONGOING", "DELETE_ERROR"]'},Se=V=>{"use memo";var j;const{t:a}=z(),{token:d}=U.useToken(),u=W(),[C,h]=Y("table_column_overrides.AdminVFolderNodeListPage"),[o,t]=I.useState([]),[b,{toggle:g}]=D(!1),[K,{toggle:F}]=D(!1),[f,{toggle:y}]=D(!1),{baiPaginationOption:k,tablePaginationOption:m,setTablePaginationOption:c}=H({current:1,pageSize:10}),[l,s]=X({order:E.withDefault("-created_at"),filter:E,statusCategory:E.withDefault("active"),mode:E.withDefault("all")},{history:"replace"}),_=I.useRef({[l.statusCategory]:{queryParams:l,tablePaginationOption:m}});_.current[l.statusCategory]={queryParams:l,tablePaginationOption:m};function S(e){switch(e){case"all":case void 0:return;case"general":return`(! name ilike ".%")&(usage_mode == "${e}")`;case"pipeline":return'usage_mode == "data"';case"automount":return'name ilike ".%"';default:return`usage_mode == "${e}"`}}const Q=S(l.mode),[R,v]=Z("initial-fetch"),M={offset:k.offset,first:k.first,filter:J([l.statusCategory==="active"||l.statusCategory===void 0?T.active:T.deleted,l.filter,Q]),order:l.order,permission:"read_attribute",filterForActiveCount:T.active,filterForDeletedCount:T.deleted},x=I.useDeferredValue(M),L=I.useDeferredValue(R),{vfolder_nodes:i,...P}=ee.useLazyLoadQuery(G,x,{fetchPolicy:L==="initial-fetch"?"store-and-network":"network-only",fetchKey:L==="initial-fetch"?void 0:L});return n.jsxs(p,{direction:"column",align:"stretch",gap:"md",...V,children:[n.jsxs(ne,{variant:"borderless",title:a("data.Folders"),styles:{header:{borderBottom:"none"},body:{paddingTop:0}},children:[n.jsx(ae,{activeKey:l.statusCategory,onChange:e=>{const r=_.current[e]||{};s(null),s({...r.queryParams,statusCategory:e}),c(r.tablePaginationOption||{current:1}),t([])},items:N({active:a("data.Active"),deleted:a("data.folders.TrashBin")},(e,r)=>{var A;return{key:r,label:n.jsxs(p,{justify:"center",gap:10,children:[e,(((A=P[r])==null?void 0:A.count)||0)>0&&n.jsx(ye,{count:P[r].count,color:l.statusCategory===r?d.colorPrimary:d.colorTextDisabled,size:"small",showZero:!0,style:{paddingRight:d.paddingXS,paddingLeft:d.paddingXS,fontSize:10}})]})}})}),n.jsxs(p,{direction:"column",align:"stretch",gap:"sm",children:[n.jsxs(p,{justify:"between",wrap:"wrap",gap:"sm",children:[n.jsxs(p,{gap:"sm",align:"start",style:{flexShrink:1},wrap:"wrap",children:[n.jsx(le,{optionType:"button",value:l.mode,onChange:e=>{s({mode:e.target.value}),c({current:1}),t([])},options:te([{label:a("data.All"),value:"all"},{label:a("data.General"),value:"general"},((j=u==null?void 0:u._config)==null?void 0:j.fasttrackEndpoint)&&{label:a("data.Pipeline"),value:"data"},{label:a("data.AutoMount"),value:"automount"},u._config.enableModelFolders&&{label:a("data.Models"),value:"model"}])}),n.jsx(re,{"data-testid":"vfolder-filter",filterProperties:[{key:"name",propertyLabel:a("data.folders.Name"),type:"string"},{key:"status",propertyLabel:a("data.folders.Status"),type:"string",strictSelection:!0,defaultOperator:"==",options:N(ke,e=>({label:e,value:e}))},{key:"host",propertyLabel:a("data.folders.Location"),type:"string"},{key:"ownership_type",propertyLabel:a("data.Type"),type:"string",strictSelection:!0,defaultOperator:"==",options:[{label:a("data.User"),value:"user"},{label:a("data.Project"),value:"group"}]},{key:"permission",propertyLabel:a("data.Permission"),type:"string",strictSelection:!0,defaultOperator:"==",options:[{label:a("data.ReadOnly"),value:"ro"},{label:a("data.ReadWrite"),value:"rw"}]}],value:l.filter??void 0,onChange:e=>{s({filter:e??null}),c({current:1}),t([])}})]}),n.jsxs(p,{gap:"xs",children:[o.length>0&&l.statusCategory==="active"&&n.jsxs(n.Fragment,{children:[n.jsx(B,{count:o.length,onClearSelection:()=>t([])}),n.jsx(O,{title:a("data.folders.MoveToTrash"),children:n.jsx(oe,{vfolderFrgmt:o,onClick:()=>{g()}})})]}),o.length>0&&l.statusCategory==="deleted"&&n.jsxs(n.Fragment,{children:[n.jsx(B,{count:o.length,onClearSelection:()=>t([])}),n.jsx(O,{title:a("data.folders.Restore"),children:n.jsx(w,{icon:n.jsx(se,{style:{color:d.colorInfo}}),onClick:()=>{F()}})})]}),n.jsx(ie,{settingId:"admin-vfolder-list",loading:x!==M||L!==R,value:R,onChange:e=>{v(e)}}),n.jsx(w,{type:"primary",icon:n.jsx(de,{}),onClick:()=>{y()},children:a("data.CreateFolder")})]})]}),n.jsx(ue,{order:l.order,loading:x!==M,vfoldersFrgmt:$(N(i==null?void 0:i.edges,"node")),rowSelection:{type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(e){return{disabled:ce(e.status)&&e.status!=="delete-pending"}},onChange:e=>{me(e,$(N(i==null?void 0:i.edges,"node")),t)},selectedRowKeys:N(o,e=>e.id)},pagination:{pageSize:m.pageSize,current:m.current,total:(i==null?void 0:i.count)??0,onChange(e,r){q(e)&&q(r)&&c({current:e,pageSize:r})}},onChangeOrder:e=>{s({order:e??null})},onRemoveRow:e=>{t(r=>ge(r,A=>A.id!==e)),v()},tableSettings:{columnOverrides:C,onColumnOverridesChange:h}})]})]}),n.jsx(Fe,{vfolderFrgmts:o,open:b,onRequestClose:e=>{e&&(v(),t([])),g()}}),n.jsx(pe,{vfolderFrgmts:o,open:K,onRequestClose:e=>{e&&(v(),t([])),F()}}),n.jsx(fe,{open:f,folderType:"project",alertMessage:a("data.folders.AdminDataPageAlert"),onRequestClose:e=>{y(),e&&v()}})]})};export{Se as default};
//# sourceMappingURL=AdminVFolderNodeListPage-glYlKl1o.js.map
