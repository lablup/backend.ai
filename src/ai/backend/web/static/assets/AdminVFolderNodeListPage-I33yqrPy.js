import{u as U,t as W,a as H,a4 as Y,r as A,aV as B,aW as X,$ as Z,a0 as E,bF as J,cZ as ee,i as ne,j as n,B as p,bI as ae,U as le,a6 as N,c0 as te,a1 as re,b1 as oe,bv as j,am as w,io as se,z as $,ip as ie,aA as de,b4 as ue,iq as me,a5 as ge,b6 as q,dy as ce,aK as G,ir as Fe,is as pe,it as fe,a8 as ye,aa as T,an as ke}from"./index-r5M52Un8.js";const z=function(){var C={defaultValue:null,kind:"LocalArgument",name:"filter"},a={defaultValue:null,kind:"LocalArgument",name:"filterForActiveCount"},s={defaultValue:null,kind:"LocalArgument",name:"filterForDeletedCount"},u={defaultValue:null,kind:"LocalArgument",name:"first"},V={defaultValue:null,kind:"LocalArgument",name:"offset"},h={defaultValue:null,kind:"LocalArgument",name:"order"},o={defaultValue:null,kind:"LocalArgument",name:"permission"},t={kind:"Variable",name:"permission",variableName:"permission"},b=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"order",variableName:"order"},t],m={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},K={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},F={alias:null,args:null,kind:"ScalarField",name:"permissions",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},y={kind:"Literal",name:"first",value:0},k={kind:"Literal",name:"offset",value:0},g=[f],c={alias:"active",args:[{kind:"Variable",name:"filter",variableName:"filterForActiveCount"},y,k,t],concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:g,storageKey:null},l={alias:"deleted",args:[{kind:"Variable",name:"filter",variableName:"filterForDeletedCount"},y,k,t],concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:g,storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},_={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null};return{fragment:{argumentDefinitions:[C,a,s,u,V,h,o],kind:"Fragment",metadata:null,name:"AdminVFolderNodeListPageQuery",selections:[{alias:null,args:b,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:m,action:"THROW"},K,F,{args:null,kind:"FragmentSpread",name:"VFolderNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeleteVFolderModalFragment"},{args:null,kind:"FragmentSpread",name:"EditableVFolderNameFragment"},{args:null,kind:"FragmentSpread",name:"RestoreVFolderModalFragment"},{args:null,kind:"FragmentSpread",name:"VFolderNodeIdenticonFragment"},{args:null,kind:"FragmentSpread",name:"SharedFolderPermissionInfoModalFragment"},{args:null,kind:"FragmentSpread",name:"BAIVFolderDeleteButtonFragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},f],storageKey:null},c,l],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[V,u,C,h,o,a,s],kind:"Operation",name:"AdminVFolderNodeListPageQuery",selections:[{alias:null,args:b,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[m,K,F,d,{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quota_scope_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownership_type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"group_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"usage_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"max_files",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"max_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"last_used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"num_files",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cur_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null},F,_,{alias:null,args:null,kind:"ScalarField",name:"creator",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{kind:"InlineFragment",selections:[{kind:"InlineFragment",selections:[S,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},m,_,{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[d,m],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null}],type:"ComputeSessionNode",abstractKey:null},{kind:"InlineFragment",selections:[S,{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[d],storageKey:null}],type:"VFolder",abstractKey:null},{kind:"InlineFragment",selections:[S],type:"VirtualFolderNode",abstractKey:null}],type:"Node",abstractKey:"__isNode"}],storageKey:null}],storageKey:null},f],storageKey:null},c,l]},params:{cacheID:"9fdc875b939fc853ba35ce210ad4b97f",id:null,metadata:{},name:"AdminVFolderNodeListPageQuery",operationKind:"query",text:`query AdminVFolderNodeListPageQuery(
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
  row_id
  id
  name
  status
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
`}}}();z.hash="61335271ca378f8ff80cff73517798c7";const _e=["READY","PERFORMING","CLONING","MOUNTED","ERROR","DELETE_PENDING","DELETE_ONGOING","DELETE_COMPLETE","DELETE_ERROR"],R={active:'status != "DELETE_PENDING" & status != "DELETE_ONGOING" & status != "DELETE_ERROR" & status != "DELETE_COMPLETE"',deleted:'status in ["DELETE_PENDING", "DELETE_ONGOING", "DELETE_ERROR"]'},ve=C=>{"use memo";var O;const{t:a}=U(),{token:s}=W.useToken(),u=H(),[V,h]=Y("table_column_overrides.AdminVFolderNodeListPage"),[o,t]=A.useState([]),[b,{toggle:m}]=B(!1),[K,{toggle:F}]=B(!1),[f,{toggle:y}]=B(!1),{baiPaginationOption:k,tablePaginationOption:g,setTablePaginationOption:c}=X({current:1,pageSize:10}),[l,d]=Z({order:E(T,"-created_at"),filter:E(T,void 0),statusCategory:E(T,"active"),mode:E(T,"all")}),_=A.useRef({[l.statusCategory]:{queryParams:l,tablePaginationOption:g}});_.current[l.statusCategory]={queryParams:l,tablePaginationOption:g};function S(e){switch(e){case"all":case void 0:return;case"general":return`(! name ilike ".%")&(usage_mode == "${e}")`;case"pipeline":return'usage_mode == "data"';case"automount":return'name ilike ".%"';default:return`usage_mode == "${e}"`}}const Q=S(l.mode),[M,v]=J("initial-fetch"),x={offset:k.offset,first:k.first,filter:ee([l.statusCategory==="active"||l.statusCategory===void 0?R.active:R.deleted,l.filter,Q]),order:l.order,permission:"read_attribute",filterForActiveCount:R.active,filterForDeletedCount:R.deleted},P=A.useDeferredValue(x),I=A.useDeferredValue(M),{vfolder_nodes:i,...D}=ne.useLazyLoadQuery(z,P,{fetchPolicy:I==="initial-fetch"?"store-and-network":"network-only",fetchKey:I==="initial-fetch"?void 0:I});return n.jsxs(p,{direction:"column",align:"stretch",gap:"md",...C,children:[n.jsxs(ae,{variant:"borderless",title:a("data.Folders"),styles:{header:{borderBottom:"none"},body:{paddingTop:0}},children:[n.jsx(le,{activeKey:l.statusCategory,onChange:e=>{const r=_.current[e]||{};d({...r.queryParams,statusCategory:e},"replace"),c(r.tablePaginationOption||{current:1}),t([])},items:N({active:a("data.Active"),deleted:a("data.folders.TrashBin")},(e,r)=>{var L;return{key:r,label:n.jsxs(p,{justify:"center",gap:10,children:[e,(((L=D[r])==null?void 0:L.count)||0)>0&&n.jsx(ke,{count:D[r].count,color:l.statusCategory===r?s.colorPrimary:s.colorTextDisabled,size:"small",showZero:!0,style:{paddingRight:s.paddingXS,paddingLeft:s.paddingXS,fontSize:10}})]})}})}),n.jsxs(p,{direction:"column",align:"stretch",gap:"sm",children:[n.jsxs(p,{justify:"between",wrap:"wrap",gap:"sm",children:[n.jsxs(p,{gap:"sm",align:"start",style:{flexShrink:1},wrap:"wrap",children:[n.jsx(te,{optionType:"button",value:l.mode,onChange:e=>{d({mode:e.target.value},"replaceIn"),c({current:1}),t([])},options:re([{label:a("data.All"),value:"all"},{label:a("data.General"),value:"general"},((O=u==null?void 0:u._config)==null?void 0:O.fasttrackEndpoint)&&{label:a("data.Pipeline"),value:"data"},{label:a("data.AutoMount"),value:"automount"},u._config.enableModelFolders&&{label:a("data.Models"),value:"model"}])}),n.jsx(oe,{"data-testid":"vfolder-filter",filterProperties:[{key:"name",propertyLabel:a("data.folders.Name"),type:"string"},{key:"status",propertyLabel:a("data.folders.Status"),type:"string",strictSelection:!0,defaultOperator:"==",options:N(_e,e=>({label:e,value:e}))},{key:"host",propertyLabel:a("data.folders.Location"),type:"string"},{key:"ownership_type",propertyLabel:a("data.Type"),type:"string",strictSelection:!0,defaultOperator:"==",options:[{label:a("data.User"),value:"user"},{label:a("data.Project"),value:"group"}]},{key:"permission",propertyLabel:a("data.Permission"),type:"string",strictSelection:!0,defaultOperator:"==",options:[{label:a("data.ReadOnly"),value:"ro"},{label:a("data.ReadWrite"),value:"rw"}]}],value:l.filter||void 0,onChange:e=>{d({filter:e},"replaceIn"),c({current:1}),t([])}})]}),n.jsxs(p,{gap:"sm",children:[o.length>0&&l.statusCategory==="active"&&n.jsxs(n.Fragment,{children:[n.jsx(j,{count:o.length,onClearSelection:()=>t([])}),n.jsx(w,{title:a("data.folders.MoveToTrash"),children:n.jsx(se,{vfolderFrgmt:o,style:{borderColor:s.colorBorder},type:"text",variant:"outlined",onClick:()=>{m()}})})]}),o.length>0&&l.statusCategory==="deleted"&&n.jsxs(n.Fragment,{children:[n.jsx(j,{count:o.length,onClearSelection:()=>t([])}),n.jsx(w,{title:a("data.folders.Restore"),children:n.jsx($,{style:{color:s.colorInfo,borderColor:s.colorBorder},type:"text",variant:"outlined",icon:n.jsx(ie,{}),onClick:()=>{F()}})})]}),n.jsx(de,{loading:P!==x||I!==M,autoUpdateDelay:15e3,value:M,onChange:e=>{v(e)}}),n.jsx($,{type:"primary",icon:n.jsx(ue,{}),onClick:()=>{y()},children:a("data.CreateFolder")})]})]}),n.jsx(me,{order:l.order,loading:P!==x,vfoldersFrgmt:G(N(i==null?void 0:i.edges,"node")),rowSelection:{type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(e){return{disabled:Fe(e.status)&&e.status!=="delete-pending"}},onChange:e=>{ce(e,G(N(i==null?void 0:i.edges,"node")),t)},selectedRowKeys:N(o,e=>e.id)},pagination:{pageSize:g.pageSize,current:g.current,total:(i==null?void 0:i.count)??0,onChange(e,r){q(e)&&q(r)&&c({current:e,pageSize:r})}},onChangeOrder:e=>{d({order:e},"replaceIn")},onRemoveRow:e=>{t(r=>ge(r,L=>L.id!==e)),v()},tableSettings:{columnOverrides:V,onColumnOverridesChange:h}})]})]}),n.jsx(pe,{vfolderFrgmts:o,open:b,onRequestClose:e=>{e&&(v(),t([])),m()}}),n.jsx(fe,{vfolderFrgmts:o,open:K,onRequestClose:e=>{e&&(v(),t([])),F()}}),n.jsx(ye,{open:f,folderType:"project",alertMessage:a("data.folders.AdminDataPageAlert"),onRequestClose:e=>{y(),e&&v()}})]})};export{ve as default};
//# sourceMappingURL=AdminVFolderNodeListPage-I33yqrPy.js.map
