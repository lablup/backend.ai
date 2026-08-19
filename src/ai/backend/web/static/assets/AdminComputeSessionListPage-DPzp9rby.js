import{m as z,u as $,t as H,A as W,E as X,w as Z,a2 as Y,r as S,aa as J,dZ as ee,aY as ne,a4 as ae,bt as w,a5 as se,jR as te,au as le,d8 as ie,k as oe,ax as re,j as s,B as F,Z as de,ac as B,c2 as ue,b2 as ce,a7 as me,ct as ge,b0 as pe,bu as fe,aq as ye,s as Se,js as Fe,bX as ke,aM as _e,p as Ce,b7 as V,aN as O,dF as Le,bh as Ne,jS as Te,ar as Ee}from"./index-DB7yUW94.js";import{B as ve}from"./BAIAdminProjectSelect-Bwu7O4oY.js";const q=(function(){var k={defaultValue:null,kind:"LocalArgument",name:"filter"},t={defaultValue:20,kind:"LocalArgument",name:"first"},c={defaultValue:0,kind:"LocalArgument",name:"offset"},N={defaultValue:null,kind:"LocalArgument",name:"order"},T=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"order",variableName:"order"}],r={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},l={kind:"Literal",name:"first",value:0},f={kind:"Literal",name:"offset",value:0},m=[i],E={alias:"all",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED"'},l,f],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:m,storageKey:'compute_session_nodes(filter:"status != "TERMINATED" & status != "CANCELLED"",first:0,offset:0)'},v={alias:"interactive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},l,f],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:m,storageKey:'compute_session_nodes(filter:"status != "TERMINATED" & status != "CANCELLED" & type == "interactive"",first:0,offset:0)'},_={alias:"inference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},l,f],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:m,storageKey:'compute_session_nodes(filter:"status != "TERMINATED" & status != "CANCELLED" & type == "inference"",first:0,offset:0)'},A={alias:"batch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},l,f],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:m,storageKey:'compute_session_nodes(filter:"status != "TERMINATED" & status != "CANCELLED" & type == "batch"",first:0,offset:0)'},C={alias:"system",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},l,f],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:m,storageKey:'compute_session_nodes(filter:"status != "TERMINATED" & status != "CANCELLED" & type == "system"",first:0,offset:0)'},o={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},n={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},L=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],h={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},K=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[r,o,d,g],storageKey:null}],storageKey:null},i];return{fragment:{argumentDefinitions:[k,t,c,N],kind:"Fragment",metadata:null,name:"AdminComputeSessionListPageQuery",selections:[{kind:"CatchField",field:{alias:"computeSessionNodeResult",args:T,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:r,action:"THROW"},{kind:"RequiredField",field:d,action:"THROW"},{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"},{args:null,kind:"FragmentSpread",name:"TerminateSessionModalFragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},i],storageKey:null},to:"RESULT"},E,v,_,A,C],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[t,c,k,N],kind:"Operation",name:"AdminComputeSessionListPageQuery",selections:[{alias:"computeSessionNodeResult",args:T,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[r,d,o,g,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},n,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},p,{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},r,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},d,{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:L,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:L,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},p,r],storageKey:null},o,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},g,n,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},h,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},r],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[o,d,r],storageKey:null}],storageKey:null},i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},h,{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:K,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:K,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],storageKey:null}],storageKey:null},i],storageKey:null},E,v,_,A,C]},params:{cacheID:"b3b5faa20af0e10a6e9f82769480a697",id:null,metadata:{},name:"AdminComputeSessionListPageQuery",operationKind:"query",text:`query AdminComputeSessionListPageQuery(
  $first: Int = 20
  $offset: Int = 0
  $filter: String
  $order: String
) {
  computeSessionNodeResult: compute_session_nodes(first: $first, offset: $offset, filter: $filter, order: $order) {
    edges {
      node {
        id
        name
        ...SessionNodesFragment
        ...TerminateSessionModalFragment
      }
    }
    count
  }
  all: compute_session_nodes(first: 0, offset: 0, filter: "status != \\"TERMINATED\\" & status != \\"CANCELLED\\"") {
    count
  }
  interactive: compute_session_nodes(first: 0, offset: 0, filter: "status != \\"TERMINATED\\" & status != \\"CANCELLED\\" & type == \\"interactive\\"") {
    count
  }
  inference: compute_session_nodes(first: 0, offset: 0, filter: "status != \\"TERMINATED\\" & status != \\"CANCELLED\\" & type == \\"inference\\"") {
    count
  }
  batch: compute_session_nodes(first: 0, offset: 0, filter: "status != \\"TERMINATED\\" & status != \\"CANCELLED\\" & type == \\"batch\\"") {
    count
  }
  system: compute_session_nodes(first: 0, offset: 0, filter: "status != \\"TERMINATED\\" & status != \\"CANCELLED\\" & type == \\"system\\"") {
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

fragment BAISessionAgentIdsFragment on ComputeSessionNode {
  agent_ids
}

fragment BAISessionClusterModeFragment on ComputeSessionNode {
  cluster_mode
  cluster_size
}

fragment BAISessionTypeTagFragment on ComputeSessionNode {
  type
}

fragment ConnectedKernelListFragment on KernelNode {
  id
  row_id
  cluster_hostname
  cluster_idx
  cluster_role
  status
  status_info
  agent_id
  container_id
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

fragment EditableSessionNameFragment on ComputeSessionNode {
  id
  row_id
  name
  priority
  user_id
  status
  project_id
}

fragment FolderLink_vfolderNode on VirtualFolderNode {
  row_id
  name
  ...VFolderNodeIdenticonFragment
}

fragment ImageNodeSimpleTagFragment on ImageNode {
  base_image_name
  version
  architecture
  name
  tags {
    key
    value
  }
  labels {
    key
    value
  }
  registry
  namespace
  tag
}

fragment MountedVFolderLinksFragment on ComputeSessionNode {
  row_id
  vfolder_nodes @since(version: "25.4.0") {
    edges {
      node {
        ...FolderLink_vfolderNode
        id
      }
    }
  }
  ...MountedVFolderLinksLegacyLazyFolderLinkFragment
}

fragment MountedVFolderLinksLegacyLazyFolderLinkFragment on ComputeSessionNode {
  row_id
  vfolder_mounts
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

fragment SessionDetailContentFragment on ComputeSessionNode {
  id
  row_id
  name
  project_id
  user_id
  owner @since(version: "25.13.0") {
    email
    id
  }
  resource_opts
  status
  status_data
  vfolder_mounts
  vfolder_nodes @since(version: "25.4.0") {
    edges {
      node {
        ...FolderLink_vfolderNode
        id
      }
    }
    count
  }
  created_at
  terminated_at
  scaling_group
  agent_ids
  requested_slots
  occupied_slots
  tag
  idle_checks @since(version: "24.12.0")
  type
  startup_command
  kernel_nodes {
    edges {
      node {
        image {
          ...ImageNodeSimpleTagFragment
          id
        }
        ...ConnectedKernelListFragment
        id
      }
    }
  }
  dependees {
    edges {
      node {
        id
        row_id
        name
        status
      }
    }
    count
  }
  dependents {
    edges {
      node {
        id
        row_id
        name
        status
      }
    }
    count
  }
  ...SessionStatusTagFragment
  ...SessionActionButtonsFragment
  ...BAISessionTypeTagFragment
  ...EditableSessionNameFragment
  ...SessionReservationFragment
  ...ContainerLogModalFragment
  ...SessionUsageMonitorFragment
  ...ContainerCommitModalFragment
  ...SessionIdleChecksNodeFragment
  ...SessionStatusDetailModalFragment
  ...AppLauncherModalFragment
  ...MountedVFolderLinksFragment
  ...BAISessionAgentIdsFragment
  ...BAISessionClusterModeFragment
}

fragment SessionDetailDrawerFragment on ComputeSessionNode {
  id
  project_id
  ...SessionDetailContentFragment
}

fragment SessionIdleChecksNodeFragment on ComputeSessionNode {
  id
  idle_checks
  ...SessionReclamationStatusCellFragment
}

fragment SessionNodesFragment on ComputeSessionNode {
  id
  row_id
  name
  status
  type
  service_ports
  user_id
  agent_ids
  ...SessionStatusTagFragment
  ...SessionReservationFragment
  ...SessionSlotCellFragment
  ...SessionReclamationStatusCellFragment
  ...SessionUsageMonitorFragment
  ...SessionDetailDrawerFragment
  ...BAISessionAgentIdsFragment
  ...BAISessionTypeTagFragment
  ...BAISessionClusterModeFragment
  ...AppLauncherModalFragment
  ...TerminateSessionModalFragment
  kernel_nodes {
    edges {
      node {
        image {
          ...ImageNodeSimpleTagFragment
          id
        }
        id
      }
    }
  }
  created_at
  scaling_group
  project_id
  owner @since(version: "25.13.0") {
    email
    id
  }
  dependees {
    edges {
      node {
        row_id
        name
        id
      }
    }
    count
  }
  dependents {
    edges {
      node {
        row_id
        name
        id
      }
    }
    count
  }
}

fragment SessionReclamationStatusCellFragment on ComputeSessionNode {
  id
  idle_checks
  ...SessionReclamationStatusPopoverFragment
}

fragment SessionReclamationStatusPopoverFragment on ComputeSessionNode {
  id
  idle_checks
}

fragment SessionReservationFragment on ComputeSessionNode {
  id
  created_at
  starts_at
  terminated_at
}

fragment SessionSlotCellFragment on ComputeSessionNode {
  id
  status
  occupied_slots
  requested_slots
  tag
  ...useSessionNodeLiveStatSessionFragment
}

fragment SessionStatusDetailModalFragment on ComputeSessionNode {
  id
  name
  status
  status_info
  status_data
  starts_at
  ...SessionStatusTagFragment
}

fragment SessionStatusTagFragment on ComputeSessionNode {
  id
  status
  status_info
  status_data
  queue_position @since(version: "25.13.0")
}

fragment SessionUsageMonitorFragment on ComputeSessionNode {
  occupied_slots
  ...useSessionNodeLiveStatSessionFragment
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

fragment useBackendAIAppLauncherFragment on ComputeSessionNode {
  name
  row_id
  vfolder_mounts
  scaling_group
  project_id
  service_ports
}

fragment useSessionNodeLiveStatSessionFragment on ComputeSessionNode {
  id
  kernel_nodes {
    edges {
      node {
        live_stat
        cluster_role
        id
      }
    }
  }
}
`}}})();q.hash="20511d2ccabe11df1c413275a52a3443";const Ae=["all","interactive","batch","inference","system"],Ie=()=>{"use memo";const k=z(),{t}=$(),{token:c}=H.useToken(),{message:N}=W.useApp(),{logger:T}=X(),r=Z(),d=Y(),[i,l]=S.useState([]),[f,m]=S.useState(!1),[E,v]=J("table_column_overrides.AdminComputeSessionListPage"),{supportedFields:_,exportCSV:A}=ee("sessions"),{baiPaginationOption:C,tablePaginationOption:o,setTablePaginationOption:g}=ne({current:1,pageSize:10}),[n,p]=ae({order:w(te),filter:se.withDefault(""),type:w(Ae).withDefault("all"),statusCategory:w(["running","finished"]).withDefault("running")},{history:"replace"}),L=S.useRef({[n.type]:{queryParams:n,tablePaginationOption:o}});S.useEffect(()=>{L.current[n.type]={queryParams:n,tablePaginationOption:o}},[n,o]);const h=n.type==="all"||n.type===void 0?void 0:`type == "${n.type}"`,K=n.statusCategory==="running"||n.statusCategory===void 0?'status != "TERMINATED" & status != "CANCELLED"':'status == "TERMINATED" | status == "CANCELLED"',U=e=>e==="TERMINATED"||e==="CANCELLED",[I,G]=le(),R={offset:C.offset,first:C.first,filter:ie([K,n.filter,h]),order:n.order||"-created_at"},b=S.useDeferredValue(R),D=S.useDeferredValue(I),Q=oe.useLazyLoadQuery(q,b,{fetchPolicy:D===re?"store-and-network":"network-only",fetchKey:D}),{computeSessionNodeResult:M,...P}=Q,u=M.ok?M.value:null;return s.jsxs(F,{direction:"column",align:"stretch",gap:"sm",children:[s.jsx(de,{activeKey:n.type,onChange:e=>{const a=L.current[e]||{queryParams:{statusCategory:"running"}};p(null),p({...a.queryParams,type:e}),g(a.tablePaginationOption||{current:1}),l([])},items:B({all:t("general.All"),interactive:t("session.Interactive"),batch:t("session.Batch"),inference:t("session.Inference"),system:t("session.System")},(e,a)=>{var y;return{key:a,label:s.jsxs(F,{justify:"center",gap:10,children:[e,(((y=P[a])==null?void 0:y.count)||0)>0&&s.jsx(Ee,{count:P[a].count,color:n.type===a?c.colorPrimary:c.colorTextDisabled,size:"small",showZero:!0,style:{paddingRight:c.paddingXS,paddingLeft:c.paddingXS,fontSize:10}})]})}})}),s.jsxs(F,{direction:"column",align:"stretch",gap:"sm",children:[s.jsxs(F,{justify:"between",wrap:"wrap",gap:"sm",children:[s.jsxs(F,{gap:"sm",align:"start",style:{flexShrink:1},wrap:"wrap",children:[s.jsx(ue,{optionType:"button",value:n.statusCategory,onChange:e=>{p({statusCategory:e.target.value}),g({current:1}),l([])},options:[{label:t("session.Running"),value:"running"},{label:t("session.Finished"),value:"finished"}]}),s.jsx(ce,{filterProperties:me([{key:"project_id",propertyLabel:t("data.Project"),type:"string",defaultOperator:"==",renderInput:({onAddCondition:e})=>s.jsx(ve,{value:null,style:{minWidth:200},onChange:(a,y)=>{var j;const x=(j=ge(y)[0])==null?void 0:j.label;e(a,pe(x)?x:void 0)}})},{key:"name",propertyLabel:t("session.SessionName"),type:"string"},{key:"scaling_group",propertyLabel:t("session.ResourceGroup"),type:"string"},{key:"agent_ids",propertyLabel:t("session.Agent"),type:"string"},{key:"user_email",propertyLabel:t("session.launcher.OwnerEmail"),type:"string"}]),value:n.filter||void 0,onChange:e=>{p({filter:e||""}),g({current:1}),l([])}})]}),s.jsxs(F,{gap:"xs",children:[i.length>0&&s.jsxs(s.Fragment,{children:[s.jsx(fe,{count:i.length,onClearSelection:()=>l([])}),s.jsx(ye,{title:t("session.TerminateSession"),placement:"topLeft",children:s.jsx(Se,{icon:s.jsx(Fe,{color:c.colorError}),onClick:()=>{m(!0)}})})]}),s.jsx(ke,{settingId:"admin-session-list",defaultAutoUpdateDelay:15e3,loading:b!==R||D!==I,value:I,onChange:e=>{G(e)}})]})]}),M.ok?s.jsx(_e,{order:n.order,onClickSessionName:e=>{const a=new URLSearchParams(d.search);a.set("sessionDetail",e.row_id),r({pathname:d.pathname,hash:d.hash,search:a.toString()},{state:{sessionDetailDrawerFrgmt:e,createdAt:new Date().toISOString()}})},loading:b!==R,rowSelection:{type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(e){return{disabled:U(e.status)}},onChange:e=>{Le(e,O(u==null?void 0:u.edges.map(a=>a==null?void 0:a.node)),l)},selectedRowKeys:B(i,e=>e.id)},sessionsFrgmt:O(u==null?void 0:u.edges.map(e=>e==null?void 0:e.node)),pagination:{pageSize:o.pageSize,current:o.current,total:(u==null?void 0:u.count)??0,onChange:(e,a)=>{V(e)&&V(a)&&g({current:e,pageSize:a})}},onChangeOrder:e=>{p({order:e})},tableSettings:{columnOverrides:E,defaultColumnOverrides:{environment:{hidden:!1},resourceGroup:{hidden:!1},type:{hidden:!1},cluster_mode:{hidden:!1},created_at:{hidden:!1},project_id:{hidden:!1}},onColumnOverridesChange:v},exportSettings:!Ce(_)&&(k==="superadmin"||k==="admin")?{supportedFields:_,onExport:async e=>{const a={};n.statusCategory==="finished"?a.status=["TERMINATED","CANCELLED"]:a.status=["PENDING","SCHEDULED","PREPARING","PREPARED","CREATING","PULLING","RESTARTING","RUNNING","TERMINATING","ERROR"],n.type&&n.type!=="all"&&(a.session_type=[n.type]),await A(e,a).catch(y=>{N.error(t("general.ErrorOccurred")),T.error(y)})}}:void 0}):s.jsx(Ne,{type:"error",showIcon:!0,message:t("error.FailedToLoadTableData")})]}),s.jsx(Te,{open:f,sessionFrgmts:i,onRequestClose:e=>{m(!1),e&&l([])}})]})};export{Ie as default};
//# sourceMappingURL=AdminComputeSessionListPage-DPzp9rby.js.map
