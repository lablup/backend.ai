import{t as R,u as b,am as E,ar as D,as as M,a as w,at as V,r as v,a4 as B,au as x,i as j,av as G,aw as $,ax as P,a1 as K,j as e,ay as L,aB as W,a5 as q,a6 as T,ab as N,ac as Q}from"./index-CuMUOZIG.js";import{S as U,A as z,a as J,R as O}from"./SessionCountDashboardItem-BxDymSLM.js";import{B as H}from"./BAIBoard-BfP1JFuH.js";import"./AgentList-BIKkFDtk.js";import"./BAIAdminResourceGroupSelect-lPsmBdjd.js";import"./SessionDetailDrawer-DsXE9SCK.js";import"./corner-down-left-Vh5jrx0E.js";import"./FolderLink-B_vcYigG.js";import"./zip-DjhbM1yJ.js";import"./unzip-CH5XQxXO.js";import"./BAIGraphQLPropertyFilter-BJSph4O9.js";const I=function(){var u={defaultValue:null,kind:"LocalArgument",name:"agentNodeFilter"},S={defaultValue:null,kind:"LocalArgument",name:"isSuperAdmin"},k={defaultValue:null,kind:"LocalArgument",name:"resourceGroup"},g={defaultValue:null,kind:"LocalArgument",name:"scopeId"},F={defaultValue:null,kind:"LocalArgument",name:"skipAgentStats"},y={defaultValue:null,kind:"LocalArgument",name:"skipTotalResourceWithinResourceGroup"},m=[{kind:"Variable",name:"scopeId",variableName:"scopeId"}],i={kind:"Literal",name:"first",value:0},a={kind:"Variable",name:"scope_id",variableName:"scopeId"},c={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o=[c],s={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},n={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},_={alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},A=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],f={alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},l=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[s,r,d,n],storageKey:null}],storageKey:null},c],t=[s,n,{alias:null,args:null,kind:"ScalarField",name:"available_slots",storageKey:null},_,f];return{fragment:{argumentDefinitions:[u,S,k,g,F,y],kind:"Fragment",metadata:null,name:"AdminDashboardPageQuery",selections:[{args:m,kind:"FragmentSpread",name:"SessionCountDashboardItemFragment"},{args:m,kind:"FragmentSpread",name:"RecentlyCreatedSessionFragment"},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{fragment:{kind:"InlineFragment",selections:[{args:[{kind:"Variable",name:"agentNodeFilter",variableName:"agentNodeFilter"},{kind:"Variable",name:"isSuperAdmin",variableName:"isSuperAdmin"},{kind:"Variable",name:"resourceGroup",variableName:"resourceGroup"}],kind:"FragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}]},{condition:"skipAgentStats",kind:"Condition",passingValue:!1,selections:[{fragment:{kind:"InlineFragment",selections:[{args:null,kind:"FragmentSpread",name:"AgentStatsFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"AgentStatsFragment"}]}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[g,k,y,F,S,u],kind:"Operation",name:"AdminDashboardPageQuery",selections:[{alias:"myInteractive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},i,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:o,storageKey:null},{alias:"myBatch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},i,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:o,storageKey:null},{alias:"myInference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},i,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:o,storageKey:null},{alias:"myUpload",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},i,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:o,storageKey:null},{alias:null,args:[{kind:"Literal",name:"filter",value:'status == "running"'},{kind:"Literal",name:"first",value:5},{kind:"Literal",name:"order",value:"-created_at"},a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[s,r,d,n,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},p,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},_,{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},s,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},d,{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:A,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:A,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},s],storageKey:null},r,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},n,p,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},s],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[r,d,s],storageKey:null}],storageKey:null},c],storageKey:null},f,{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:l,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:l,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{condition:"isSuperAdmin",kind:"Condition",passingValue:!1,selections:[{alias:null,args:[{kind:"Literal",name:"filter",value:"schedulable == true"},{kind:"Literal",name:"limit",value:1e3},{kind:"Literal",name:"offset",value:0},{kind:"Variable",name:"scaling_group",variableName:"resourceGroup"},{kind:"Literal",name:"status",value:"ALIVE"}],concreteType:"AgentSummaryList",kind:"LinkedField",name:"agent_summary_list",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentSummary",kind:"LinkedField",name:"items",plural:!0,selections:t,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"total_count",storageKey:null}],storageKey:null}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"agentNodeFilter"},{kind:"Literal",name:"first",value:100}],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AgentNode",kind:"LinkedField",name:"node",plural:!1,selections:t,storageKey:null}],storageKey:null},c],storageKey:null}]}]},{condition:"skipAgentStats",kind:"Condition",passingValue:!1,selections:[{alias:null,args:null,concreteType:"AgentStats",kind:"LinkedField",name:"agentStats",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentResource",kind:"LinkedField",name:"totalResource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"free",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capacity",storageKey:null}],storageKey:null}],storageKey:null}]}]},params:{cacheID:"c12424bbea7ded53cef9fcca26553c3b",id:null,metadata:{},name:"AdminDashboardPageQuery",operationKind:"query",text:`query AdminDashboardPageQuery(
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
`}}}();I.hash="96b17d3da84f2e5251488a099091bcf8";const re=()=>{const{token:u}=R.useToken(),{t:S}=b(),k=E(),g=D(),F=M(),y=w(),[m,i]=V(),[a,c]=v.useTransition(),[o,s]=B("admin_dashboard_board_items"),r=x(),d=y.supports("agent-stats"),n=j.useLazyLoadQuery(I,{scopeId:`project:${k.id}`,resourceGroup:g||"default",skipTotalResourceWithinResourceGroup:!r,skipAgentStats:!d,isSuperAdmin:G(F,"superadmin"),agentNodeFilter:`schedulable == true & status == "ALIVE" & scaling_group == "${g}"`},{fetchPolicy:m===$?"store-and-network":"network-only",fetchKey:m});P(()=>{c(()=>{i()})},3e4);const p=K([{id:"activeSessions",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:e.jsx(v.Suspense,{fallback:e.jsx(L,{active:!0,style:{padding:`0px ${u.marginMD}px`}}),children:e.jsx(U,{queryRef:n,isRefetching:a,title:S("session.ActiveSessions")})})}},r&&{id:"totalResourceWithinResourceGroup",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.TotalResourceWithinResourceGroupFragment&&e.jsx(W,{queryRef:n.TotalResourceWithinResourceGroupFragment,refetching:a})}},d&&n.AgentStatsFragment&&{id:"agentStats",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:e.jsx(v.Suspense,{fallback:e.jsx(L,{active:!0,style:{padding:`0px ${u.marginMD}px`}}),children:e.jsx(z,{queryRef:n.AgentStatsFragment,isRefetching:a})})}},{id:"activeAgents",rowSpan:4,columnSpan:4,definition:{minRowSpan:3,minColumnSpan:4},data:{content:e.jsx(v.Suspense,{fallback:e.jsx(L,{active:!0,style:{padding:`0px ${u.marginMD}px`}}),children:e.jsx(J,{fetchKey:m,onChangeFetchKey:()=>i()})})}},{id:"recentlyCreatedSession",rowSpan:3,columnSpan:4,definition:{minRowSpan:2,minColumnSpan:2},data:{content:e.jsx(O,{queryRef:n,isRefetching:a})}}]),_=q(p,l=>!N(o,t=>t.id===l.id)),f=[...K(T(o,l=>{var C;const t=(C=N(p,h=>h.id===l.id))==null?void 0:C.data;return t?{...l,data:t}:void 0})),..._];return e.jsx(H,{movable:!0,resizable:!0,bordered:!0,items:f,onItemsChange:l=>{const t=[...l.detail.items];s(T(t,C=>Q(C,"data")))}})};export{re as default};
//# sourceMappingURL=AdminDashboardPage-BFIK5F4R.js.map
