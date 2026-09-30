import{ab as M,u as D,z as w,b9 as B,a$ as j,a as x,aN as $,l as C,a7 as G,bc as P,r as W,bd as q,bh as Q,be as U,ah as b,j as e,aV as K,bf as z,W as J,ak as O,al as R,ap as E,aq as H}from"./index-Bq7-uTgl.js";import{S as Y,A as X,a as Z,R as ee}from"./SessionCountDashboardItem-Bzs8Il1R.js";import{B as ne}from"./BAIBoard-CiVaeVwn.js";import"./AgentList-DfHTjVtG.js";import"./sessionStatusBuckets-DQKZxHEC.js";import"./BAIAdminResourceGroupSelect-Ne9LT16v.js";import"./refresh-cw-2Q7hvcGX.js";import"./SessionDetailDrawer-Ba4XTWgM.js";import"./scroll-text-D0DWMIA7.js";import"./orderBy-DTaVA3tg.js";import"./FolderLink-Dlxwcc-O.js";import"./zip-DAoeM2hf.js";import"./unzip-xudXSyre.js";import"./ScopedAuditLog-Dzol7HPP.js";import"./BAIGraphQLPropertyFilter-BBtdM8Jh.js";import"./rotate-ccw-clock-CuUFXStU.js";const V=(function(){var d={defaultValue:null,kind:"LocalArgument",name:"agentNodeFilter"},y={defaultValue:null,kind:"LocalArgument",name:"aliveAgentFilter"},S={defaultValue:null,kind:"LocalArgument",name:"isSuperAdmin"},F={defaultValue:null,kind:"LocalArgument",name:"resourceGroup"},_={defaultValue:null,kind:"LocalArgument",name:"schedulableAgentFilter"},f={defaultValue:null,kind:"LocalArgument",name:"scopeId"},u={defaultValue:null,kind:"LocalArgument",name:"skipAgentStats"},k={defaultValue:null,kind:"LocalArgument",name:"skipTotalResourceWithinResourceGroup"},o=[{kind:"Variable",name:"scopeId",variableName:"scopeId"}],m={kind:"Literal",name:"first",value:0},i={kind:"Variable",name:"scope_id",variableName:"scopeId"},c={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},s=[c],a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},n={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},L={alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},A={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},l={alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},r=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],v={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},N=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[a,n,g,p],storageKey:null}],storageKey:null},c],I=[a,p,{alias:null,args:null,kind:"ScalarField",name:"available_slots",storageKey:null},l,h],T={kind:"Literal",name:"first",value:1};return{fragment:{argumentDefinitions:[d,y,S,F,_,f,u,k],kind:"Fragment",metadata:null,name:"AdminDashboardPageQuery",selections:[{args:o,kind:"FragmentSpread",name:"SessionCountDashboardItemFragment"},{args:o,kind:"FragmentSpread",name:"RecentlyCreatedSessionFragment"},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{fragment:{kind:"InlineFragment",selections:[{args:[{kind:"Variable",name:"agentNodeFilter",variableName:"agentNodeFilter"},{kind:"Variable",name:"isSuperAdmin",variableName:"isSuperAdmin"},{kind:"Variable",name:"resourceGroup",variableName:"resourceGroup"}],kind:"FragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}]},{condition:"skipAgentStats",kind:"Condition",passingValue:!1,selections:[{fragment:{kind:"InlineFragment",selections:[{args:[{kind:"Variable",name:"aliveAgentFilter",variableName:"aliveAgentFilter"},{kind:"Variable",name:"schedulableAgentFilter",variableName:"schedulableAgentFilter"}],kind:"FragmentSpread",name:"AgentStatsFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"AgentStatsFragment"}]}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[f,F,k,u,S,d,y,_],kind:"Operation",name:"AdminDashboardPageQuery",selections:[{alias:"myInteractive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},m,i],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:s,storageKey:null},{alias:"myBatch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},m,i],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:s,storageKey:null},{alias:"myInference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},m,i],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:s,storageKey:null},{alias:"myUpload",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},m,i],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:s,storageKey:null},{alias:null,args:[{kind:"Literal",name:"filter",value:'status == "running"'},{kind:"Literal",name:"first",value:5},{kind:"Literal",name:"order",value:"-created_at"},i],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[a,n,g,p,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},L,A,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},l,{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},t,{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},a,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:r,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:r,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},t,a],storageKey:null},n,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},p,A,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},v,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},a],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[n,g,a],storageKey:null}],storageKey:null},c],storageKey:null},h,v,{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:N,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:N,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},L,{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domain_name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{condition:"isSuperAdmin",kind:"Condition",passingValue:!1,selections:[{alias:null,args:[{kind:"Literal",name:"filter",value:"schedulable == true"},{kind:"Literal",name:"limit",value:1e3},{kind:"Literal",name:"offset",value:0},{kind:"Variable",name:"scaling_group",variableName:"resourceGroup"},{kind:"Literal",name:"status",value:"ALIVE"}],concreteType:"AgentSummaryList",kind:"LinkedField",name:"agent_summary_list",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentSummary",kind:"LinkedField",name:"items",plural:!0,selections:I,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"total_count",storageKey:null}],storageKey:null}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"agentNodeFilter"},{kind:"Literal",name:"first",value:100}],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AgentNode",kind:"LinkedField",name:"node",plural:!1,selections:I,storageKey:null}],storageKey:null},c],storageKey:null}]}]},{condition:"skipAgentStats",kind:"Condition",passingValue:!1,selections:[{alias:null,args:null,concreteType:"AgentStats",kind:"LinkedField",name:"agentStats",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentResource",kind:"LinkedField",name:"totalResource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"free",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capacity",storageKey:null}],storageKey:null}],storageKey:null},{alias:"aliveAgents",args:[{kind:"Variable",name:"filter",variableName:"aliveAgentFilter"},T],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:s,storageKey:null},{alias:"schedulableAgents",args:[{kind:"Variable",name:"filter",variableName:"schedulableAgentFilter"},T],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:s,storageKey:null}]}]},params:{cacheID:"1d01fe7f2c8778f69aaa16456eeb7093",id:null,metadata:{},name:"AdminDashboardPageQuery",operationKind:"query",text:`query AdminDashboardPageQuery(
  $scopeId: ScopeField
  $resourceGroup: String
  $skipTotalResourceWithinResourceGroup: Boolean!
  $skipAgentStats: Boolean!
  $isSuperAdmin: Boolean!
  $agentNodeFilter: String!
  $aliveAgentFilter: String!
  $schedulableAgentFilter: String!
) {
  ...SessionCountDashboardItemFragment_3vJUag
  ...RecentlyCreatedSessionFragment_3vJUag
  ...TotalResourceWithinResourceGroupFragment_2otDCj @skip(if: $skipTotalResourceWithinResourceGroup)
  ...AgentStatsFragment_rQkRq @skip(if: $skipAgentStats)
}

fragment AgentStatsFragment_rQkRq on Query {
  agentStats @since(version: "25.15.0") {
    totalResource {
      free
      used
      capacity
    }
  }
  aliveAgents: agent_nodes(filter: $aliveAgentFilter, first: 1) @since(version: "24.12.0") {
    count
  }
  schedulableAgents: agent_nodes(filter: $schedulableAgentFilter, first: 1) @since(version: "24.12.0") {
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

fragment BAIImageNodeSimpleTagFragment on ImageNode {
  base_image_name
  version
  architecture
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

fragment BAISessionAgentIdsFragment on ComputeSessionNode {
  agent_ids
}

fragment BAISessionClusterModeFragment on ComputeSessionNode {
  cluster_mode
  cluster_size
}

fragment BAISessionTypeTokenFragment on ComputeSessionNode {
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
          ...BAIImageNodeSimpleTagFragment
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
  ...SessionStatusBadgeFragment
  ...SessionActionButtonsFragment
  ...BAISessionTypeTokenFragment
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
  ...SessionStatusBadgeFragment
  ...SessionReservationFragment
  ...SessionSlotCellFragment
  ...SessionReclamationStatusCellFragment
  ...SessionUsageMonitorFragment
  ...SessionDetailDrawerFragment
  ...BAISessionAgentIdsFragment
  ...BAISessionTypeTokenFragment
  ...BAISessionClusterModeFragment
  ...AppLauncherModalFragment
  ...TerminateSessionModalFragment
  ...EditSessionPriorityModalFragment
  ...SessionAccessKeyFragment
  kernel_nodes {
    edges {
      node {
        image {
          ...BAIImageNodeSimpleTagFragment
          id
        }
        id
      }
    }
  }
  created_at
  terminated_at
  status_info
  result
  domain_name
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

fragment SessionStatusBadgeFragment on ComputeSessionNode {
  id
  status
  status_info
  status_data
  queue_position @since(version: "25.13.0")
}

fragment SessionStatusDetailModalFragment on ComputeSessionNode {
  id
  name
  status
  status_info
  status_data
  starts_at
  ...SessionStatusBadgeFragment
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
`}}})();V.hash="d2c73ada0319a83e613187c43ff06035";const ye=()=>{const{token:d}=M.useToken(),{t:y}=D(),S=w(),F=B(),_=j(),f=x(),[u,k]=$(),[o,m]=C.useTransition(),[i,c]=G("admin_dashboard_board_items"),s=P(),a=f.supports("agent-stats"),n=W.useLazyLoadQuery(V,{scopeId:`project:${S.id}`,resourceGroup:F||"default",skipTotalResourceWithinResourceGroup:!s,skipAgentStats:!a,isSuperAdmin:q(_,"superadmin"),agentNodeFilter:`schedulable == true & status == "ALIVE" & scaling_group == "${F}"`,aliveAgentFilter:'status == "ALIVE"',schedulableAgentFilter:'status == "ALIVE" & schedulable == true'},{fetchPolicy:u===Q?"store-and-network":"network-only",fetchKey:u});U(()=>{m(()=>{k()})},3e4);const g=b([{id:"activeSessions",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:e.jsx(C.Suspense,{fallback:e.jsx(K,{style:{padding:`0px ${d.marginMD}px`}}),children:e.jsx(Y,{queryRef:n,isRefetching:o,title:y("session.ActiveSessions")})})}},s&&{id:"totalResourceWithinResourceGroup",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.TotalResourceWithinResourceGroupFragment&&e.jsx(z,{queryRef:n.TotalResourceWithinResourceGroupFragment,refetching:o})}},a&&n.AgentStatsFragment&&{id:"agentStats",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:e.jsx(C.Suspense,{fallback:e.jsx(K,{style:{padding:`0px ${d.marginMD}px`}}),children:e.jsx(X,{queryRef:n.AgentStatsFragment,isRefetching:o})})}},{id:"activeAgents",rowSpan:4,columnSpan:4,definition:{minRowSpan:3,minColumnSpan:4},data:{content:e.jsx(C.Suspense,{fallback:e.jsx(K,{style:{padding:`0px ${d.marginMD}px`}}),children:e.jsx(Z,{fetchKey:u,onChangeFetchKey:()=>k()})})}},{id:"recentlyCreatedSession",rowSpan:3,columnSpan:4,definition:{minRowSpan:2,minColumnSpan:2},data:{content:e.jsx(ee,{queryRef:n,isRefetching:o,project:J(S)})}}]),p=O(g,l=>!E(i,t=>t.id===l.id)),A=[...b(R(i,l=>{var r;const t=(r=E(g,v=>v.id===l.id))==null?void 0:r.data;return t?{...l,data:t}:void 0})),...p];return e.jsx(ne,{movable:!0,resizable:!0,bordered:!0,items:A,onItemsChange:l=>{const t=[...l.detail.items];c(R(t,r=>H(r,"data")))}})};export{ye as default};
//# sourceMappingURL=AdminDashboardPage-BVRe0dKc.js.map
