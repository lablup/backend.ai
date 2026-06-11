import{as as G,u as Q,t as $,A as z,v as H,p as W,Z as X,r as f,a4 as Z,dF as Y,br as J,bt as ee,bs as R,cS as ne,at as ae,cT as se,i as te,aw as le,j as s,B as S,U as ie,a6 as w,cb as oe,b1 as re,a1 as de,bu as ue,ap as ce,b2 as ge,iu as me,aC as pe,aL as ye,m as fe,aj as x,aM as P,dv as Se,c5 as Fe,i_ as ke,i$ as _e,aq as Ce}from"./index-CuMUOZIG.js";const j=function(){var F={defaultValue:null,kind:"LocalArgument",name:"filter"},t={defaultValue:20,kind:"LocalArgument",name:"first"},c={defaultValue:0,kind:"LocalArgument",name:"offset"},L={defaultValue:null,kind:"LocalArgument",name:"order"},N=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"order",variableName:"order"}],r={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},l={kind:"Literal",name:"first",value:0},y={kind:"Literal",name:"offset",value:0},g=[i],T={alias:"all",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED"'},l,y],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:g,storageKey:'compute_session_nodes(filter:"status != "TERMINATED" & status != "CANCELLED"",first:0,offset:0)'},E={alias:"interactive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},l,y],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:g,storageKey:'compute_session_nodes(filter:"status != "TERMINATED" & status != "CANCELLED" & type == "interactive"",first:0,offset:0)'},k={alias:"inference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},l,y],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:g,storageKey:'compute_session_nodes(filter:"status != "TERMINATED" & status != "CANCELLED" & type == "inference"",first:0,offset:0)'},v={alias:"batch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},l,y],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:g,storageKey:'compute_session_nodes(filter:"status != "TERMINATED" & status != "CANCELLED" & type == "batch"",first:0,offset:0)'},_={alias:"system",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},l,y],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:g,storageKey:'compute_session_nodes(filter:"status != "TERMINATED" & status != "CANCELLED" & type == "system"",first:0,offset:0)'},o={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},n={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},p=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],C=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[r,o,d,m],storageKey:null}],storageKey:null},i];return{fragment:{argumentDefinitions:[F,t,c,L],kind:"Fragment",metadata:null,name:"AdminComputeSessionListPageQuery",selections:[{kind:"CatchField",field:{alias:"computeSessionNodeResult",args:N,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:r,action:"THROW"},{kind:"RequiredField",field:d,action:"THROW"},{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"},{args:null,kind:"FragmentSpread",name:"TerminateSessionModalFragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},i],storageKey:null},to:"RESULT"},T,E,k,v,_],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[t,c,F,L],kind:"Operation",name:"AdminComputeSessionListPageQuery",selections:[{alias:"computeSessionNodeResult",args:N,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[r,d,o,m,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},n,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},r,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},d,{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:p,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:p,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},r],storageKey:null},o,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},m,n,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},r],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[o,d,r],storageKey:null}],storageKey:null},i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:C,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:C,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],storageKey:null}],storageKey:null},i],storageKey:null},T,E,k,v,_]},params:{cacheID:"d1b03d6da6dd0a559b507a7bfb5b80cb",id:null,metadata:{},name:"AdminComputeSessionListPageQuery",operationKind:"query",text:`query AdminComputeSessionListPageQuery(
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
  vfolder_mounts
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
  idle_checks @since(version: "24.12.0")
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
`}}}();j.hash="20511d2ccabe11df1c413275a52a3443";const Le=["all","interactive","batch","inference","system"],Te=()=>{"use memo";const F=G(),{t}=Q(),{token:c}=$.useToken(),{message:L}=z.useApp(),{logger:N}=H(),r=W(),d=X(),[i,l]=f.useState([]),[y,g]=f.useState(!1),[T,E]=Z("table_column_overrides.AdminComputeSessionListPage"),{supportedFields:k,exportCSV:v}=Y("sessions"),{baiPaginationOption:_,tablePaginationOption:o,setTablePaginationOption:m}=J({current:1,pageSize:10}),[n,p]=ee({order:R(_e),filter:ne.withDefault(""),type:R(Le).withDefault("all"),statusCategory:R(["running","finished"]).withDefault("running")},{history:"replace"}),C=f.useRef({[n.type]:{queryParams:n,tablePaginationOption:o}});f.useEffect(()=>{C.current[n.type]={queryParams:n,tablePaginationOption:o}},[n,o]);const B=n.type==="all"||n.type===void 0?void 0:`type == "${n.type}"`,V=n.statusCategory==="running"||n.statusCategory===void 0?'status != "TERMINATED" & status != "CANCELLED"':'status == "TERMINATED" | status == "CANCELLED"',O=e=>e==="TERMINATED"||e==="CANCELLED",[h,q]=ae(),K={offset:_.offset,first:_.first,filter:se([V,n.filter,B]),order:n.order||"-created_at"},I=f.useDeferredValue(K),b=f.useDeferredValue(h),U=te.useLazyLoadQuery(j,I,{fetchPolicy:b===le?"store-and-network":"network-only",fetchKey:b}),{computeSessionNodeResult:D,...M}=U,u=D.ok?D.value:null;return s.jsxs(S,{direction:"column",align:"stretch",gap:"sm",children:[s.jsx(ie,{activeKey:n.type,onChange:e=>{const a=C.current[e]||{queryParams:{statusCategory:"running"}};p(null),p({...a.queryParams,type:e}),m(a.tablePaginationOption||{current:1}),l([])},items:w({all:t("general.All"),interactive:t("session.Interactive"),batch:t("session.Batch"),inference:t("session.Inference"),system:t("session.System")},(e,a)=>{var A;return{key:a,label:s.jsxs(S,{justify:"center",gap:10,children:[e,(((A=M[a])==null?void 0:A.count)||0)>0&&s.jsx(Ce,{count:M[a].count,color:n.type===a?c.colorPrimary:c.colorTextDisabled,size:"small",showZero:!0,style:{paddingRight:c.paddingXS,paddingLeft:c.paddingXS,fontSize:10}})]})}})}),s.jsxs(S,{direction:"column",align:"stretch",gap:"sm",children:[s.jsxs(S,{justify:"between",wrap:"wrap",gap:"sm",children:[s.jsxs(S,{gap:"sm",align:"start",style:{flexShrink:1},wrap:"wrap",children:[s.jsx(oe,{optionType:"button",value:n.statusCategory,onChange:e=>{p({statusCategory:e.target.value}),m({current:1}),l([])},options:[{label:t("session.Running"),value:"running"},{label:t("session.Finished"),value:"finished"}]}),s.jsx(re,{filterProperties:de([{key:"name",propertyLabel:t("session.SessionName"),type:"string"},{key:"scaling_group",propertyLabel:t("session.ResourceGroup"),type:"string"},{key:"agent_ids",propertyLabel:t("session.Agent"),type:"string"},{key:"user_email",propertyLabel:t("session.launcher.OwnerEmail"),type:"string"}]),value:n.filter||void 0,onChange:e=>{p({filter:e||""}),m({current:1}),l([])}})]}),s.jsxs(S,{gap:"sm",children:[i.length>0&&s.jsxs(s.Fragment,{children:[s.jsx(ue,{count:i.length,onClearSelection:()=>l([])}),s.jsx(ce,{title:t("session.TerminateSession"),placement:"topLeft",children:s.jsx(ge,{icon:s.jsx(me,{color:c.colorError}),onClick:()=>{g(!0)}})})]}),s.jsx(pe,{loading:I!==K||b!==h,autoUpdateDelay:15e3,value:h,onChange:e=>{q(e)}})]})]}),D.ok?s.jsx(ye,{order:n.order,onClickSessionName:e=>{const a=new URLSearchParams(d.search);a.set("sessionDetail",e.row_id),r({pathname:d.pathname,hash:d.hash,search:a.toString()},{state:{sessionDetailDrawerFrgmt:e,createdAt:new Date().toISOString()}})},loading:I!==K,rowSelection:{type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(e){return{disabled:O(e.status)}},onChange:e=>{Se(e,P(u==null?void 0:u.edges.map(a=>a==null?void 0:a.node)),l)},selectedRowKeys:w(i,e=>e.id)},sessionsFrgmt:P(u==null?void 0:u.edges.map(e=>e==null?void 0:e.node)),pagination:{pageSize:o.pageSize,current:o.current,total:(u==null?void 0:u.count)??0,onChange:(e,a)=>{x(e)&&x(a)&&m({current:e,pageSize:a})}},onChangeOrder:e=>{p({order:e})},tableSettings:{columnOverrides:T,defaultColumnOverrides:{environment:{hidden:!1},resourceGroup:{hidden:!1},type:{hidden:!1},cluster_mode:{hidden:!1},created_at:{hidden:!1},project_id:{hidden:!1}},onColumnOverridesChange:E},exportSettings:!fe(k)&&(F==="superadmin"||F==="admin")?{supportedFields:k,onExport:async e=>{const a={};n.statusCategory==="finished"?a.status=["TERMINATED","CANCELLED"]:a.status=["PENDING","SCHEDULED","PREPARING","PREPARED","CREATING","PULLING","RESTARTING","RUNNING","TERMINATING","ERROR"],n.type&&n.type!=="all"&&(a.session_type=[n.type]),await v(e,a).catch(A=>{L.error(t("general.ErrorOccurred")),N.error(A)})}}:void 0}):s.jsx(Fe,{type:"error",showIcon:!0,message:t("error.FailedToLoadTableData")})]}),s.jsx(ke,{open:y,sessionFrgmts:i,onRequestClose:e=>{g(!1),e&&l([])}})]})};export{Te as default};
//# sourceMappingURL=AdminComputeSessionListPage-DmeebH5_.js.map
