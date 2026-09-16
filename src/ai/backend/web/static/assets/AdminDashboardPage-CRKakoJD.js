import{ab as b,u as E,z as M,b8 as D,a_ as w,a as V,aN as B,l as A,a7 as j,bb as x,r as G,bc as P,bg as $,bd as W,ah as T,j as e,aU as K,be as q,W as U,ak as Q,al as I,ap as h,aq as z}from"./index-DPebpL40.js";import{S as J,A as O,a as H,R as Y}from"./SessionCountDashboardItem-DzFjEfMS.js";import{B as X}from"./BAIBoard-D9sz-jhW.js";import"./AgentList-LffeYOO5.js";import"./sessionStatusBuckets-CRW9PX0M.js";import"./BAIId-oHD2WVBQ.js";import"./BAITag-dedPDMOM.js";import"./BAIAdminResourceGroupSelect-heA2aAjp.js";import"./refresh-cw-rioqa8A9.js";import"./SessionDetailDrawer-CHJu8GbK.js";import"./FolderLink-rZTSRFdj.js";import"./zip-dqg4xnl6.js";import"./unzip-CzK734fj.js";import"./ScopedAuditLog-Dwul8NSy.js";import"./BAIGraphQLPropertyFilter-CPqP1l9W.js";import"./rotate-ccw-clock-CpAeUoLy.js";const R=(function(){var m={defaultValue:null,kind:"LocalArgument",name:"agentNodeFilter"},k={defaultValue:null,kind:"LocalArgument",name:"isSuperAdmin"},p={defaultValue:null,kind:"LocalArgument",name:"resourceGroup"},S={defaultValue:null,kind:"LocalArgument",name:"scopeId"},y={defaultValue:null,kind:"LocalArgument",name:"skipAgentStats"},_={defaultValue:null,kind:"LocalArgument",name:"skipTotalResourceWithinResourceGroup"},c=[{kind:"Variable",name:"scopeId",variableName:"scopeId"}],i={kind:"Literal",name:"first",value:0},a={kind:"Variable",name:"scope_id",variableName:"scopeId"},g={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o=[g],s={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},n={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},F={alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},L={alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},l=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],t={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},v=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[s,r,d,n],storageKey:null}],storageKey:null},g],N=[s,n,{alias:null,args:null,kind:"ScalarField",name:"available_slots",storageKey:null},L,u];return{fragment:{argumentDefinitions:[m,k,p,S,y,_],kind:"Fragment",metadata:null,name:"AdminDashboardPageQuery",selections:[{args:c,kind:"FragmentSpread",name:"SessionCountDashboardItemFragment"},{args:c,kind:"FragmentSpread",name:"RecentlyCreatedSessionFragment"},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{fragment:{kind:"InlineFragment",selections:[{args:[{kind:"Variable",name:"agentNodeFilter",variableName:"agentNodeFilter"},{kind:"Variable",name:"isSuperAdmin",variableName:"isSuperAdmin"},{kind:"Variable",name:"resourceGroup",variableName:"resourceGroup"}],kind:"FragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}]},{condition:"skipAgentStats",kind:"Condition",passingValue:!1,selections:[{fragment:{kind:"InlineFragment",selections:[{args:null,kind:"FragmentSpread",name:"AgentStatsFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"AgentStatsFragment"}]}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[S,p,_,y,k,m],kind:"Operation",name:"AdminDashboardPageQuery",selections:[{alias:"myInteractive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},i,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:o,storageKey:null},{alias:"myBatch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},i,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:o,storageKey:null},{alias:"myInference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},i,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:o,storageKey:null},{alias:"myUpload",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},i,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:o,storageKey:null},{alias:null,args:[{kind:"Literal",name:"filter",value:'status == "running"'},{kind:"Literal",name:"first",value:5},{kind:"Literal",name:"order",value:"-created_at"},a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[s,r,d,n,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},F,f,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},L,{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},C,{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},s,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},d,{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:l,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:l,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},C,s],storageKey:null},r,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},n,f,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},t,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},s],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[r,d,s],storageKey:null}],storageKey:null},g],storageKey:null},u,t,{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:v,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:v,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},F,{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{condition:"isSuperAdmin",kind:"Condition",passingValue:!1,selections:[{alias:null,args:[{kind:"Literal",name:"filter",value:"schedulable == true"},{kind:"Literal",name:"limit",value:1e3},{kind:"Literal",name:"offset",value:0},{kind:"Variable",name:"scaling_group",variableName:"resourceGroup"},{kind:"Literal",name:"status",value:"ALIVE"}],concreteType:"AgentSummaryList",kind:"LinkedField",name:"agent_summary_list",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentSummary",kind:"LinkedField",name:"items",plural:!0,selections:N,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"total_count",storageKey:null}],storageKey:null}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"agentNodeFilter"},{kind:"Literal",name:"first",value:100}],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AgentNode",kind:"LinkedField",name:"node",plural:!1,selections:N,storageKey:null}],storageKey:null},g],storageKey:null}]}]},{condition:"skipAgentStats",kind:"Condition",passingValue:!1,selections:[{alias:null,args:null,concreteType:"AgentStats",kind:"LinkedField",name:"agentStats",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentResource",kind:"LinkedField",name:"totalResource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"free",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capacity",storageKey:null}],storageKey:null}],storageKey:null}]}]},params:{cacheID:"7e3c922b3012f6b116f39b8f20b1680c",id:null,metadata:{},name:"AdminDashboardPageQuery",operationKind:"query",text:`query AdminDashboardPageQuery(
  $scopeId: ScopeField
  $resourceGroup: String
  $skipTotalResourceWithinResourceGroup: Boolean!
  $skipAgentStats: Boolean!
  $isSuperAdmin: Boolean!
  $agentNodeFilter: String!
) {
  ...SessionCountDashboardItemFragment_3vJUag
  ...RecentlyCreatedSessionFragment_3vJUag
  ...TotalResourceWithinResourceGroupFragment_2otDCj @skip(if: $skipTotalResourceWithinResourceGroup)
  ...AgentStatsFragment @skip(if: $skipAgentStats)
}

fragment AgentStatsFragment on Query {
  agentStats @since(version: "25.15.0") {
    totalResource {
      free
      used
      capacity
    }
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

fragment EditSessionPriorityModalFragment on ComputeSessionNode {
  id
  name
  priority @since(version: "24.09.0")
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

fragment RecentlyCreatedSessionFragment_3vJUag on Query {
  compute_session_nodes(first: 5, order: "-created_at", filter: "status == \\"running\\"", scope_id: $scopeId) {
    edges {
      node {
        id
        ...SessionNodesFragment
      }
    }
  }
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

fragment SessionAccessKeyFragment on ComputeSessionNode {
  access_key
  user_id
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

fragment SessionCountDashboardItemFragment_3vJUag on Query {
  myInteractive: compute_session_nodes(first: 0, filter: "status != \\"TERMINATED\\" & status != \\"CANCELLED\\" & type == \\"interactive\\"", scope_id: $scopeId) {
    count
  }
  myBatch: compute_session_nodes(first: 0, filter: "status != \\"TERMINATED\\" & status != \\"CANCELLED\\" & type == \\"batch\\"", scope_id: $scopeId) {
    count
  }
  myInference: compute_session_nodes(first: 0, filter: "status != \\"TERMINATED\\" & status != \\"CANCELLED\\" & type == \\"inference\\"", scope_id: $scopeId) {
    count
  }
  myUpload: compute_session_nodes(first: 0, filter: "status != \\"TERMINATED\\" & status != \\"CANCELLED\\" & type == \\"system\\"", scope_id: $scopeId) {
    count
  }
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
  ...SessionAccessKeyFragment
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
  priority @since(version: "24.09.0")
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
  ...EditSessionPriorityModalFragment
  ...SessionAccessKeyFragment
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

fragment TotalResourceWithinResourceGroupFragment_2otDCj on Query {
  agent_summary_list(limit: 1000, offset: 0, status: "ALIVE", scaling_group: $resourceGroup, filter: "schedulable == true") @skip(if: $isSuperAdmin) {
    items {
      id
      status
      available_slots
      occupied_slots
      scaling_group
    }
    total_count
  }
  agent_nodes(filter: $agentNodeFilter, first: 100) @include(if: $isSuperAdmin) @since(version: "24.12.0") {
    edges {
      node {
        id
        status
        available_slots
        occupied_slots
        scaling_group
      }
    }
    count
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
`}}})();R.hash="96b17d3da84f2e5251488a099091bcf8";const Se=()=>{const{token:m}=b.useToken(),{t:k}=E(),p=M(),S=D(),y=w(),_=V(),[c,i]=B(),[a,g]=A.useTransition(),[o,s]=j("admin_dashboard_board_items"),r=x(),d=_.supports("agent-stats"),n=G.useLazyLoadQuery(R,{scopeId:`project:${p.id}`,resourceGroup:S||"default",skipTotalResourceWithinResourceGroup:!r,skipAgentStats:!d,isSuperAdmin:P(y,"superadmin"),agentNodeFilter:`schedulable == true & status == "ALIVE" & scaling_group == "${S}"`},{fetchPolicy:c===$?"store-and-network":"network-only",fetchKey:c});W(()=>{g(()=>{i()})},3e4);const F=T([{id:"activeSessions",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:e.jsx(A.Suspense,{fallback:e.jsx(K,{style:{padding:`0px ${m.marginMD}px`}}),children:e.jsx(J,{queryRef:n,isRefetching:a,title:k("session.ActiveSessions")})})}},r&&{id:"totalResourceWithinResourceGroup",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.TotalResourceWithinResourceGroupFragment&&e.jsx(q,{queryRef:n.TotalResourceWithinResourceGroupFragment,refetching:a})}},d&&n.AgentStatsFragment&&{id:"agentStats",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:e.jsx(A.Suspense,{fallback:e.jsx(K,{style:{padding:`0px ${m.marginMD}px`}}),children:e.jsx(O,{queryRef:n.AgentStatsFragment,isRefetching:a})})}},{id:"activeAgents",rowSpan:4,columnSpan:4,definition:{minRowSpan:3,minColumnSpan:4},data:{content:e.jsx(A.Suspense,{fallback:e.jsx(K,{style:{padding:`0px ${m.marginMD}px`}}),children:e.jsx(H,{fetchKey:c,onChangeFetchKey:()=>i()})})}},{id:"recentlyCreatedSession",rowSpan:3,columnSpan:4,definition:{minRowSpan:2,minColumnSpan:2},data:{content:e.jsx(Y,{queryRef:n,isRefetching:a,project:U(p)})}}]),f=Q(F,l=>!h(o,t=>t.id===l.id)),C=[...T(I(o,l=>{var u;const t=(u=h(F,v=>v.id===l.id))==null?void 0:u.data;return t?{...l,data:t}:void 0})),...f];return e.jsx(X,{movable:!0,resizable:!0,bordered:!0,items:C,onItemsChange:l=>{const t=[...l.detail.items];s(I(t,u=>z(u,"data")))}})};export{Se as default};
//# sourceMappingURL=AdminDashboardPage-CRKakoJD.js.map
