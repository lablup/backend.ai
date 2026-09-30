import{aA as Xn,ab as Ge,j as s,aB as Jn,aC as on,aD as Yn,aE as Hn,i as G,u as fe,aF as Cn,aG as Zn,at as yn,aH as He,aI as ea,aJ as na,K as sn,aK as Tn,aL as fn,aM as Kn,c as $,aN as Ln,l as E,aO as aa,aP as ta,aQ as la,aR as sa,aS as An,aT as dn,t as ra,z as Qe,r as Xe,aU as Nn,aV as Ne,aW as ia,Y as un,Z as In,a7 as Ue,aX as Sn,N as oa,ac as Rn,aY as da,aZ as ua,a_ as ca,a$ as xn,s as en,P as ma,b0 as ga,F as Ee,b1 as pa,a8 as ya,b2 as fa,b3 as Sa,E as ka,a as kn,b4 as jn,ap as Fa,b5 as _a,b6 as ba,aj as Dn,ad as ha,b7 as va,a2 as cn,q as Ca,b8 as Ta,b9 as Ka,ba as La,bb as Aa,bc as Na,bd as nn,be as Ia,W as Ra,ah as bn,bf as xa,bg as ja,al as mn,ao as Da,bh as Ma,bi as wa,bj as Ea,aq as Mn}from"./index-Bq7-uTgl.js";import{A as Va,a as Pa,S as Ba,R as $a}from"./SessionCountDashboardItem-Bzs8Il1R.js";import{B as Oa}from"./BAIBoard-CiVaeVwn.js";import{B as Ga}from"./BAIModelDeploymentNodes-BJxOZwNT.js";import{B as qa}from"./BAIGraphQLPropertyFilter-BBtdM8Jh.js";import{Q as za}from"./QuotaPerStorageVolumePanelCard-BjDXgJDD.js";import{B as gn}from"./BAIPanelItem-D2Mrs_qK.js";import"./AgentList-DfHTjVtG.js";import"./sessionStatusBuckets-DQKZxHEC.js";import"./BAIAdminResourceGroupSelect-Ne9LT16v.js";import"./refresh-cw-2Q7hvcGX.js";import"./SessionDetailDrawer-Ba4XTWgM.js";import"./scroll-text-D0DWMIA7.js";import"./orderBy-DTaVA3tg.js";import"./FolderLink-Dlxwcc-O.js";import"./zip-DAoeM2hf.js";import"./unzip-xudXSyre.js";import"./ScopedAuditLog-Dzol7HPP.js";import"./rotate-ccw-clock-CuUFXStU.js";import"./BAIBooleanToken-DWum6Ri7.js";import"./BAIDeploymentTagTokens-BaRPnlxf.js";import"./usePrimaryColors-t8gas3Uo.js";const We=({title:n,status:e="error",children:a,style:d})=>{const{t:l}=Xn(),{token:r}=Ge.useToken();return s.jsx(Jn,{fallbackRender:()=>s.jsx("div",{"data-bai-board-item-status":e,style:{height:"100%",paddingInline:r.paddingXL,paddingBottom:r.padding,...d},children:s.jsx(on,{title:n,extra:s.jsx(Yn,{title:l("comp:BAIBoardItemErrorBoundary.UnexpectedError"),type:e})})}),children:a})},wn=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"agentNodeFilter"},e={defaultValue:null,kind:"LocalArgument",name:"aliveAgentFilter"},a={defaultValue:null,kind:"LocalArgument",name:"isSuperAdmin"},d={defaultValue:null,kind:"LocalArgument",name:"resourceGroup"},l={defaultValue:null,kind:"LocalArgument",name:"schedulableAgentFilter"},r={defaultValue:null,kind:"LocalArgument",name:"scopeId"},u={defaultValue:null,kind:"LocalArgument",name:"skipTotalResourceWithinResourceGroup"},i=[{kind:"Variable",name:"scopeId",variableName:"scopeId"}],m={kind:"Literal",name:"first",value:0},p={kind:"Variable",name:"scope_id",variableName:"scopeId"},t={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o=[t],g={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},K={alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},_={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},T=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],b={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},I={alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},F=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[g,f,c,S],storageKey:null}],storageKey:null},t],h=[g,S,{alias:null,args:null,kind:"ScalarField",name:"available_slots",storageKey:null},K,I],R={kind:"Literal",name:"first",value:1};return{fragment:{argumentDefinitions:[n,e,a,d,l,r,u],kind:"Fragment",metadata:null,name:"DashboardPageQuery",selections:[{args:i,kind:"FragmentSpread",name:"SessionCountDashboardItemFragment"},{args:i,kind:"FragmentSpread",name:"RecentlyCreatedSessionFragment"},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{fragment:{kind:"InlineFragment",selections:[{args:[{kind:"Variable",name:"agentNodeFilter",variableName:"agentNodeFilter"},{kind:"Variable",name:"isSuperAdmin",variableName:"isSuperAdmin"},{kind:"Variable",name:"resourceGroup",variableName:"resourceGroup"}],kind:"FragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{fragment:{kind:"InlineFragment",selections:[{args:[{kind:"Variable",name:"aliveAgentFilter",variableName:"aliveAgentFilter"},{kind:"Variable",name:"schedulableAgentFilter",variableName:"schedulableAgentFilter"}],kind:"FragmentSpread",name:"AgentStatsFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"AgentStatsFragment"}]}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[r,d,u,a,n,e,l],kind:"Operation",name:"DashboardPageQuery",selections:[{alias:"myInteractive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},m,p],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:o,storageKey:null},{alias:"myBatch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},m,p],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:o,storageKey:null},{alias:"myInference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},m,p],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:o,storageKey:null},{alias:"myUpload",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},m,p],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:o,storageKey:null},{alias:null,args:[{kind:"Literal",name:"filter",value:'status == "running"'},{kind:"Literal",name:"first",value:5},{kind:"Literal",name:"order",value:"-created_at"},p],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[g,f,c,S,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},k,y,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},K,{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},_,{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},g,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:T,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:T,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},_,g],storageKey:null},f,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},S,y,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},b,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},g],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[f,c,g],storageKey:null}],storageKey:null},t],storageKey:null},I,b,{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:F,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:F,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},k,{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domain_name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{condition:"isSuperAdmin",kind:"Condition",passingValue:!1,selections:[{alias:null,args:[{kind:"Literal",name:"filter",value:"schedulable == true"},{kind:"Literal",name:"limit",value:1e3},{kind:"Literal",name:"offset",value:0},{kind:"Variable",name:"scaling_group",variableName:"resourceGroup"},{kind:"Literal",name:"status",value:"ALIVE"}],concreteType:"AgentSummaryList",kind:"LinkedField",name:"agent_summary_list",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentSummary",kind:"LinkedField",name:"items",plural:!0,selections:h,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"total_count",storageKey:null}],storageKey:null}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"agentNodeFilter"},{kind:"Literal",name:"first",value:100}],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AgentNode",kind:"LinkedField",name:"node",plural:!1,selections:h,storageKey:null}],storageKey:null},t],storageKey:null}]}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{alias:null,args:null,concreteType:"AgentStats",kind:"LinkedField",name:"agentStats",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentResource",kind:"LinkedField",name:"totalResource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"free",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capacity",storageKey:null}],storageKey:null}],storageKey:null},{alias:"aliveAgents",args:[{kind:"Variable",name:"filter",variableName:"aliveAgentFilter"},R],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:o,storageKey:null},{alias:"schedulableAgents",args:[{kind:"Variable",name:"filter",variableName:"schedulableAgentFilter"},R],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:o,storageKey:null}]}]},params:{cacheID:"815bdbb309adb47623be35848f2ac46c",id:null,metadata:{},name:"DashboardPageQuery",operationKind:"query",text:`query DashboardPageQuery(
  $scopeId: ScopeField
  $resourceGroup: String
  $skipTotalResourceWithinResourceGroup: Boolean!
  $isSuperAdmin: Boolean!
  $agentNodeFilter: String!
  $aliveAgentFilter: String!
  $schedulableAgentFilter: String!
) {
  ...SessionCountDashboardItemFragment_3vJUag
  ...RecentlyCreatedSessionFragment_3vJUag
  ...TotalResourceWithinResourceGroupFragment_2otDCj @skip(if: $skipTotalResourceWithinResourceGroup)
  ...AgentStatsFragment_rQkRq @include(if: $isSuperAdmin)
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
`}}})();wn.hash="010e4f1c56e89b2d778a8e76ae4aa39c";/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */const Fn=Hn(!1),Ua=()=>{"use memo";const n=G.c(10),{t:e}=fe(),[a,d]=Cn(Fn),l=a?"secondary":"primary";let r;n[0]===Symbol.for("react.memo_cache_sentinel")?(r=s.jsx(Zn,{size:"1em"}),n[0]=r):r=n[0];let u;n[1]!==a||n[2]!==e?(u=e(a?"button.Close":"dashboard.Edit"),n[1]=a,n[2]=e,n[3]=u):u=n[3];let i;n[4]!==d?(i=()=>d(Qa),n[4]=d,n[5]=i):i=n[5];let m;return n[6]!==l||n[7]!==u||n[8]!==i?(m=s.jsx(yn,{variant:l,size:"sm",icon:r,label:u,onClick:i}),n[6]=l,n[7]=u,n[8]=i,n[9]=m):m=n[9],m};function Qa(n){return!n}/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */const an=[],rn={resourceTable:{rowSpan:3,columnSpan:2,definition:{minRowSpan:3,minColumnSpan:2}},resourceCount:{rowSpan:2,columnSpan:1,definition:{minRowSpan:2,minColumnSpan:1}},sessionResourceGrid:{rowSpan:4,columnSpan:4,definition:{minRowSpan:2,minColumnSpan:2}}},Wa=n=>({id:`${n.resourceType}-${ea()}`,panelType:n.panelType,descriptor:{resourceType:n.resourceType,title:n.title,filter:n.filter??null,order:n.order??null,gridView:n.panelType==="sessionResourceGrid"?n.gridView??He:null}}),Xa=n=>{"use memo";const e=G.c(10),{title:a,onEdit:d,onRemove:l}=n,{t:r}=fe();if(!na(Fn)||!d&&!l)return null;let i;e[0]!==d||e[1]!==r?(i=d?s.jsx(sn,{variant:"ghost",size:"sm",label:r("button.Edit"),tooltip:r("button.Edit"),icon:s.jsx(Tn,{size:"1em"}),onClick:d}):null,e[0]=d,e[1]=r,e[2]=i):i=e[2];let m;e[3]!==l||e[4]!==r||e[5]!==a?(m=l?s.jsx(fn,{title:r("dialog.ask.DoYouWantToDeleteSomething",{name:a}),isDanger:!0,onConfirm:l,children:s.jsx(sn,{variant:"ghost",size:"sm",label:r("button.Delete"),tooltip:r("button.Delete"),icon:s.jsx(Kn,{size:"1em"})})}):null,e[3]=l,e[4]=r,e[5]=a,e[6]=m):m=e[6];let p;return e[7]!==i||e[8]!==m?(p=s.jsxs($,{align:"center",gap:"xxs",children:[i,m]}),e[7]=i,e[8]=m,e[9]=p):p=e[9],p},_n=n=>{"use memo";const e=G.c(30),{title:a,onEdit:d,onRemove:l,children:r}=n,{token:u}=Ge.useToken(),[i,m]=Ln(),[p,t]=E.useTransition();let o;e[0]!==u.paddingXL?(o={paddingInline:u.paddingXL,height:"100%"},e[0]=u.paddingXL,e[1]=o):o=e[1];let g;e[2]!==m?(g=()=>{t(()=>{m()})},e[2]=m,e[3]=g):g=e[3];let f;e[4]===Symbol.for("react.memo_cache_sentinel")?(f={backgroundColor:"transparent"},e[4]=f):f=e[4];let c;e[5]!==p||e[6]!==g?(c=s.jsx(aa,{size:"small",loading:p,value:"",onChange:g,type:"text",style:f}),e[5]=p,e[6]=g,e[7]=c):c=e[7];let S;e[8]!==d||e[9]!==l||e[10]!==a?(S=s.jsx(Xa,{title:a,onEdit:d,onRemove:l}),e[8]=d,e[9]=l,e[10]=a,e[11]=S):S=e[11];let k;e[12]!==c||e[13]!==S?(k=s.jsxs($,{align:"center",gap:"xxs",children:[c,S]}),e[12]=c,e[13]=S,e[14]=k):k=e[14];let y;e[15]!==k||e[16]!==a?(y=s.jsx(on,{title:a,extra:k}),e[15]=k,e[16]=a,e[17]=y):y=e[17];let K;e[18]!==u.margin?(K={flex:1,overflowY:"auto",overflowX:"hidden",marginBottom:u.margin},e[18]=u.margin,e[19]=K):K=e[19];let _;e[20]!==r||e[21]!==i?(_=r(i),e[20]=r,e[21]=i,e[22]=_):_=e[22];let T;e[23]!==K||e[24]!==_?(T=s.jsx($,{direction:"column",align:"stretch",style:K,children:_}),e[23]=K,e[24]=_,e[25]=T):T=e[25];let b;return e[26]!==o||e[27]!==T||e[28]!==y?(b=s.jsxs($,{direction:"column",align:"stretch",style:o,children:[y,T]}),e[26]=o,e[27]=T,e[28]=y,e[29]=b):b=e[29],b},En=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},a={defaultValue:null,kind:"LocalArgument",name:"offset"},d={defaultValue:null,kind:"LocalArgument",name:"orderBy"},l=[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],concreteType:"VFolderConnection",kind:"LinkedField",name:"adminVfoldersV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},{alias:null,args:null,concreteType:"VFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"usageMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[n,e,a,d],kind:"Fragment",metadata:null,name:"resourceRegistryVfolderQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[n,d,e,a],kind:"Operation",name:"resourceRegistryVfolderQuery",selections:l},params:{cacheID:"0bf78ebbd78040d6acf4915a3b7744cc",id:null,metadata:{},name:"resourceRegistryVfolderQuery",operationKind:"query",text:`query resourceRegistryVfolderQuery(
  $filter: VFolderFilter
  $orderBy: [VFolderOrderBy!]
  $limit: Int
  $offset: Int
) {
  adminVfoldersV2(filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
    count
    edges {
      node {
        id
        host
        status
        metadata {
          name
          usageMode
          createdAt
        }
      }
    }
  }
}
`}}})();En.hash="f0f996cac5aac86ee5907d16f7b69a3c";const Vn=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},a={defaultValue:null,kind:"LocalArgument",name:"offset"},d={defaultValue:null,kind:"LocalArgument",name:"orderBy"},l=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],r={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null};return{fragment:{argumentDefinitions:[n,e,a,d],kind:"Fragment",metadata:null,name:"resourceRegistryDeploymentQuery",selections:[{alias:null,args:l,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[r,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[u,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[n,d,e,a],kind:"Operation",name:"resourceRegistryDeploymentQuery",selections:[{alias:null,args:l,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[r,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[u,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},i,{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[i],storageKey:null},u],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[r],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[u,{alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[u,i],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[u,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"de03280bc473b7caac1876a7850c4a3b",id:null,metadata:{},name:"resourceRegistryDeploymentQuery",operationKind:"query",text:`query resourceRegistryDeploymentQuery(
  $filter: DeploymentFilter
  $orderBy: [DeploymentOrderBy!]
  $limit: Int
  $offset: Int
) {
  myDeployments(filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
    count
    edges {
      node {
        id
        ...BAIModelDeploymentNodesFragment
      }
    }
  }
}

fragment BAIDeploymentOwnerInfo_deployment on ModelDeployment {
  id
  creator @since(version: "26.4.3") {
    id
    basicInfo {
      email
      username
      fullName
    }
  }
}

fragment BAIDeploymentTagTokens_metadata on ModelDeploymentMetadata {
  tags
}

fragment BAIModelDeploymentNodesFragment on ModelDeployment {
  id
  currentRevisionId
  metadata {
    projectId
    domainName
    name
    status
    tags
    createdAt
    updatedAt
    resourceGroupName
    projectV2 @since(version: "26.4.3") {
      basicInfo {
        name
      }
      id
    }
    ...BAIDeploymentTagTokens_metadata
  }
  networkAccess {
    endpointUrl
    preferredDomainName
    openToPublic
  }
  defaultDeploymentStrategy {
    type
  }
  replicaState {
    desiredReplicaCount
  }
  runningReplicas: replicas(filter: {status: {equals: RUNNING}}) {
    count
  }
  currentRevision @since(version: "26.4.3") {
    id
    revisionNumber
    modelMountConfig {
      vfolder {
        id
        name
      }
    }
  }
  ...BAIDeploymentOwnerInfo_deployment
}
`}}})();Vn.hash="4e7a525297dc8b70a0c7765c072ffe4b";const Pn=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"first"},a={defaultValue:null,kind:"LocalArgument",name:"offset"},d={defaultValue:null,kind:"LocalArgument",name:"order"},l={defaultValue:null,kind:"LocalArgument",name:"scopeId"},r=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"order",variableName:"order"},{kind:"Variable",name:"scope_id",variableName:"scopeId"}],u={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},c=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],S={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},k=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[i,m,p,t],storageKey:null}],storageKey:null},u];return{fragment:{argumentDefinitions:[n,e,a,d,l],kind:"Fragment",metadata:null,name:"resourceRegistrySessionQuery",selections:[{alias:null,args:r,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[u,{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[i,{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,e,a,n,d],kind:"Operation",name:"resourceRegistrySessionQuery",selections:[{alias:null,args:r,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[u,{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[i,m,p,t,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},o,g,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},f,{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},i,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:c,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:c,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},f,i],storageKey:null},m,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},t,g,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},S,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[m,p,i],storageKey:null}],storageKey:null},u],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},S,{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:k,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:k,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},o,{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domain_name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"a6dd57e32e9306ae38344f280ca4ab55",id:null,metadata:{},name:"resourceRegistrySessionQuery",operationKind:"query",text:`query resourceRegistrySessionQuery(
  $scopeId: ScopeField
  $first: Int
  $offset: Int
  $filter: String
  $order: String
) {
  compute_session_nodes(scope_id: $scopeId, first: $first, offset: $offset, filter: $filter, order: $order) {
    count
    edges {
      node {
        id
        ...SessionNodesFragment
      }
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
`}}})();Pn.hash="bb92c247cff2de74130007224eef9d02";/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

 Every session field the manager's queryfilter accepts
 (`gql_legacy/session.py::_queryfilter_fieldspec`), so a custom panel can
 express any condition the backend supports instead of the three the picker
 used to offer (FR-3654).
*/const Ja=n=>n.map(e=>({label:e,value:e})),Ya=["PENDING","DEPRIORITIZING","RESERVED","SCHEDULED","PREPARING","PULLING","PREPARED","CREATING","RUNNING","RESTARTING","RUNNING_DEGRADED","PREEMPTED","RESCHEDULING","TERMINATING","TERMINATED","ERROR","CANCELLED"],Ha=["interactive","batch","inference","system"],Za=["undefined","success","failure"],et=["single-node","multi-node"],hn=(n,e,a)=>({key:n,propertyLabel:e,type:"uuid",rule:{message:a("general.InvalidUUID"),validate:d=>ta(d.toLowerCase())}}),tn=(n,e,a)=>({key:n,propertyLabel:e,type:"string",defaultOperator:"==",strictSelection:!0,options:Ja(a)}),nt=n=>[{key:"name",propertyLabel:n("session.SessionName"),type:"string"},tn("status",n("session.Status"),Ya),tn("type",n("session.SessionType"),Ha),{key:"scaling_group",propertyLabel:n("session.ResourceGroup"),type:"string"},{key:"agent_ids",propertyLabel:n("session.Agent"),type:"string"},{key:"image",propertyLabel:n("general.Image"),type:"string"},{key:"user_email",propertyLabel:n("session.launcher.OwnerEmail"),type:"string"},hn("user_id",n("credential.UserID"),n),{key:"full_name",propertyLabel:n("credential.FullName"),type:"string"},{key:"access_key",propertyLabel:n("general.AccessKey"),type:"string"},{key:"domain_name",propertyLabel:n("credential.Domain"),type:"string"},tn("cluster_mode",n("session.ClusterMode"),et),{key:"cluster_size",propertyLabel:n("session.launcher.ClusterSize"),type:"number"},{key:"priority",propertyLabel:n("session.Priority"),type:"number"},tn("result",n("session.Result"),Za),{key:"status_info",propertyLabel:n("session.StatusInfo"),type:"string"},{key:"startup_command",propertyLabel:n("session.StartupCommand"),type:"string"},hn("id",n("session.SessionId"),n),{key:"created_at",propertyLabel:n("session.CreatedAt"),type:"datetime"},{key:"starts_at",propertyLabel:n("session.StartsAt"),type:"datetime"},{key:"terminated_at",propertyLabel:n("session.TerminatedAt"),type:"datetime"}],at=n=>n?ra(n).format("lll"):"-",tt=()=>({filter:n,order:e,limit:a,offset:d})=>({filter:typeof n=="string"?void 0:n??void 0,orderBy:An(e??null),limit:a,offset:d}),Bn=n=>n?{count:n.count,nodes:dn(n.edges.map(e=>e==null?void 0:e.node))}:null,lt={key:"session",labelKey:"webui.menu.Sessions",defaultOrder:"-created_at",kind:"sessionNodes",query:Pn,getStringFilterProperties:nt,buildVariables:({filter:n,order:e,limit:a,offset:d,projectId:l})=>({scopeId:`project:${l}`,first:a,offset:d,filter:typeof n=="string"&&n?n:void 0,order:e??"-created_at"}),selectConnection:n=>{const e=n.compute_session_nodes;return e?{count:e.count??0,nodes:dn(e.edges.map(a=>a==null?void 0:a.node))}:null}},st={key:"deployment",labelKey:"webui.menu.Deployments",defaultOrder:"-createdAt",kind:"deploymentNodes",query:Vn,getFilterProperties:n=>[{key:"name",propertyLabel:n("deployment.filter.Name"),type:"string"},{key:"tags",propertyLabel:n("deployment.filter.Tags"),type:"string"},{key:"endpointUrl",propertyLabel:n("deployment.filter.EndpointUrl"),type:"string"},{key:"openToPublic",propertyLabel:n("deployment.filter.OpenToPublic"),type:"boolean"}],buildVariables:({filter:n,order:e,limit:a,offset:d,projectId:l})=>({filter:{...typeof n=="string"?{}:n??{},...l?{projectId:{equals:l}}:{}},orderBy:An(e??null),limit:a,offset:d}),selectConnection:n=>Bn(n.myDeployments)},rt={key:"vfolder",labelKey:"webui.menu.Data&Storage",defaultOrder:"-createdAt",minRole:"superadmin",query:En,getFilterProperties:n=>[{key:"name",propertyLabel:n("data.folders.Name"),type:"string"},{key:"host",propertyLabel:n("data.folders.Location"),type:"string"}],getColumns:n=>[{key:"name",dataIndex:"name",title:n("data.folders.Name"),sorter:!0,render:(e,a)=>{var d;return(d=a.metadata)==null?void 0:d.name}},{key:"host",dataIndex:"host",title:n("data.folders.Location"),sorter:!0},{key:"status",dataIndex:"status",title:n("general.Status"),sorter:!0,minWidth:140,render:(e,a)=>a.status?s.jsx(la,{label:a.status,variant:sa("vfolder",a.status)}):null},{key:"createdAt",dataIndex:"createdAt",title:n("general.CreatedAt"),sorter:!0,render:(e,a)=>{var d;return at((d=a.metadata)==null?void 0:d.createdAt)}}],buildVariables:tt(),selectConnection:n=>Bn(n.adminVfoldersV2)},ye={session:lt,deployment:st,vfolder:rt},it=Object.keys(ye),ot=n=>it.filter(e=>{const a=ye[e].minRole;return a?a==="superadmin"?n==="superadmin":n==="superadmin"||n==="admin":!0}),Ze=(n,e)=>{if(n.title)return n.title;const a=ye[n.resourceType];return a?e(a.labelKey):n.resourceType},dt=n=>{"use memo";const e=G.c(12),{descriptor:a,fetchKey:d,onEdit:l,onRemove:r}=n,{t:u}=fe(),{token:i}=Ge.useToken();let m;e[0]!==a||e[1]!==u?(m=Ze(a,u),e[0]=a,e[1]=u,e[2]=m):m=e[2];const p=m;let t;e[3]!==a||e[4]!==d||e[5]!==i.padding?(t=g=>s.jsx($,{direction:"row",wrap:"wrap",gap:"lg",children:s.jsx(Nn,{style:{paddingBlock:i.padding},children:s.jsx(E.Suspense,{fallback:s.jsx(Ne,{}),children:s.jsx($n,{descriptor:a,fetchKey:`${d??""}:${g}`},`${a.resourceType}:${JSON.stringify(a.filter??null)}`)})})}),e[3]=a,e[4]=d,e[5]=i.padding,e[6]=t):t=e[6];let o;return e[7]!==l||e[8]!==r||e[9]!==t||e[10]!==p?(o=s.jsx(_n,{title:p,onEdit:l,onRemove:r,children:t}),e[7]=l,e[8]=r,e[9]=t,e[10]=p,e[11]=o):o=e[11],o},$n=n=>{"use memo";const e=G.c(16),{descriptor:a,fetchKey:d}=n,{t:l}=fe(),r=Qe(),u=ye[a.resourceType];let i;e[0]!==u||e[1]!==r.id||e[2]!==a.filter||e[3]!==a.order?(i=u.buildVariables({filter:a.filter??void 0,order:a.order??u.defaultOrder,limit:1,offset:0,projectId:r.id??""}),e[0]=u,e[1]=r.id,e[2]=a.filter,e[3]=a.order,e[4]=i):i=e[4];const m=i,p=E.useDeferredValue(m),t=E.useDeferredValue(d);let o;e[5]!==t?(o={fetchPolicy:"store-and-network",fetchKey:t},e[5]=t,e[6]=o):o=e[6];const g=Xe.useLazyLoadQuery(u.query,p,o);let f;e[7]!==u||e[8]!==g?(f=u.selectConnection(g),e[7]=u,e[8]=g,e[9]=f):f=e[9];const c=f;let S;e[10]!==u.labelKey||e[11]!==l?(S=l(u.labelKey),e[10]=u.labelKey,e[11]=l,e[12]=S):S=e[12];const k=(c==null?void 0:c.count)??0;let y;return e[13]!==S||e[14]!==k?(y=s.jsx(ia,{title:S,current:k,progressMode:"hidden"}),e[13]=S,e[14]=k,e[15]=y):y=e[15],y},ut=["name","status","replicaSummary","model","createdAt"],On=n=>{"use memo";const e=G.c(36),{descriptor:a,fetchKey:d,onChangeOrder:l,disableNavigation:r}=n,u=Qe(),i=un(),m=In(),p=ye.deployment,[t,o]=Ue("table_column_overrides.DashboardDeploymentPanel");let g;e[0]===Symbol.for("react.memo_cache_sentinel")?(g={current:1,pageSize:10},e[0]=g):g=e[0];const{baiPaginationOption:f,tablePaginationOption:c,setTablePaginationOption:S}=Sn(g),k=a.order??p.defaultOrder;let y;e[1]!==f.limit||e[2]!==f.offset||e[3]!==u.id||e[4]!==a.filter||e[5]!==k?(y=p.buildVariables({filter:a.filter??void 0,order:k,limit:f.limit,offset:f.offset,projectId:u.id??""}),e[1]=f.limit,e[2]=f.offset,e[3]=u.id,e[4]=a.filter,e[5]=k,e[6]=y):y=e[6];const K=y,_=E.useDeferredValue(K),T=E.useDeferredValue(d);let b;e[7]!==T?(b={fetchPolicy:"store-and-network",fetchKey:T},e[7]=T,e[8]=b):b=e[8];const F=Xe.useLazyLoadQuery(p.query,_,b).myDeployments;let h;e[9]!==(F==null?void 0:F.edges)?(h=dn(F==null?void 0:F.edges.map(ct)),e[9]=F==null?void 0:F.edges,e[10]=h):h=e[10];const R=h,x=!l;let L;e[11]!==l?(L=l?M=>l(M??void 0):void 0,e[11]=l,e[12]=L):L=e[12];const j=_!==K||T!==d;let A;e[13]!==m||e[14]!==r||e[15]!==i?(A=M=>M.filter(mt).map(V=>V.key==="name"&&!r?{...V,onTitleClick:q=>{i(`${m("deployments")}/${oa(q.id)}`)}}:V),e[13]=m,e[14]=r,e[15]=i,e[16]=A):A=e[16];const v=(F==null?void 0:F.count)??0;let C;e[17]!==S?(C=(M,V)=>{S({current:M,pageSize:V})},e[17]=S,e[18]=C):C=e[18];let N;e[19]!==C||e[20]!==v||e[21]!==c.current||e[22]!==c.pageSize?(N={pageSize:c.pageSize,current:c.current,total:v,onChange:C},e[19]=C,e[20]=v,e[21]=c.current,e[22]=c.pageSize,e[23]=N):N=e[23];let D;e[24]!==t||e[25]!==o?(D={columnOverrides:t,onColumnOverridesChange:o},e[24]=t,e[25]=o,e[26]=D):D=e[26];let w;return e[27]!==R||e[28]!==k||e[29]!==N||e[30]!==D||e[31]!==x||e[32]!==L||e[33]!==j||e[34]!==A?(w=s.jsx(Ga,{deploymentsFrgmt:R,order:k,disableSorter:x,onChangeOrder:L,loading:j,customizeColumns:A,pagination:N,tableSettings:D}),e[27]=R,e[28]=k,e[29]=N,e[30]=D,e[31]=x,e[32]=L,e[33]=j,e[34]=A,e[35]=w):w=e[35],w};function ct(n){return n==null?void 0:n.node}function mt(n){return ut.includes(String(n.key))}const Gn=n=>{"use memo";const e=G.c(36),{descriptor:a,fetchKey:d,onChangeOrder:l,disableSessionDetail:r}=n,u=Qe(),i=un(),m=Rn(),p=ye.session,[t,o]=Ue("table_column_overrides.DashboardSessionPanel");let g;e[0]===Symbol.for("react.memo_cache_sentinel")?(g={current:1,pageSize:10},e[0]=g):g=e[0];const{baiPaginationOption:f,tablePaginationOption:c,setTablePaginationOption:S}=Sn(g),k=a.order??p.defaultOrder;let y;e[1]!==f.limit||e[2]!==f.offset||e[3]!==u.id||e[4]!==a.filter||e[5]!==k?(y=p.buildVariables({filter:a.filter??void 0,order:k,limit:f.limit,offset:f.offset,projectId:u.id??""}),e[1]=f.limit,e[2]=f.offset,e[3]=u.id,e[4]=a.filter,e[5]=k,e[6]=y):y=e[6];const K=y,_=E.useDeferredValue(K),T=E.useDeferredValue(d);let b;e[7]!==T?(b={fetchPolicy:"store-and-network",fetchKey:T},e[7]=T,e[8]=b):b=e[8];const F=Xe.useLazyLoadQuery(p.query,_,b).compute_session_nodes;let h;e[9]!==(F==null?void 0:F.edges)?(h=dn(F==null?void 0:F.edges.map(gt)),e[9]=F==null?void 0:F.edges,e[10]=h):h=e[10];const R=h,x=!l;let L;e[11]!==l?(L=l?M=>l(M??void 0):void 0,e[11]=l,e[12]=L):L=e[12];const j=_!==K||T!==d;let A;e[13]!==r||e[14]!==m||e[15]!==i?(A=r?void 0:M=>{const V=new URLSearchParams(m.search);V.set("sessionDetail",M.row_id),i({pathname:m.pathname,hash:m.hash,search:V.toString()},{state:{sessionDetailDrawerFrgmt:M,createdAt:new Date().toISOString()}})},e[13]=r,e[14]=m,e[15]=i,e[16]=A):A=e[16];const v=(F==null?void 0:F.count)??0;let C;e[17]!==S?(C=(M,V)=>{S({current:M,pageSize:V})},e[17]=S,e[18]=C):C=e[18];let N;e[19]!==C||e[20]!==v||e[21]!==c.current||e[22]!==c.pageSize?(N={pageSize:c.pageSize,current:c.current,total:v,onChange:C},e[19]=C,e[20]=v,e[21]=c.current,e[22]=c.pageSize,e[23]=N):N=e[23];let D;e[24]!==t||e[25]!==o?(D={columnOverrides:t,onColumnOverridesChange:o},e[24]=t,e[25]=o,e[26]=D):D=e[26];let w;return e[27]!==k||e[28]!==R||e[29]!==N||e[30]!==D||e[31]!==x||e[32]!==L||e[33]!==j||e[34]!==A?(w=s.jsx(da,{sessionsFrgmt:R,order:k,disableSorter:x,onChangeOrder:L,loading:j,onClickSessionName:A,pagination:N,tableSettings:D}),e[27]=k,e[28]=R,e[29]=N,e[30]=D,e[31]=x,e[32]=L,e[33]=j,e[34]=A,e[35]=w):w=e[35],w};function gt(n){return n==null?void 0:n.node}const pt=n=>{"use memo";const e=G.c(11),{descriptor:a,fetchKey:d,onEdit:l,onRemove:r}=n,{t:u}=fe();let i;e[0]!==a||e[1]!==u?(i=Ze(a,u),e[0]=a,e[1]=u,e[2]=i):i=e[2];const m=i;let p;e[3]!==a||e[4]!==d?(p=o=>{var g,f;return s.jsx(E.Suspense,{fallback:s.jsx(Ne,{}),children:((g=ye[a.resourceType])==null?void 0:g.kind)==="deploymentNodes"?s.jsx(On,{descriptor:a,fetchKey:`${d??""}:${o}`},`${a.resourceType}:${JSON.stringify(a.filter??null)}:${a.order??""}`):((f=ye[a.resourceType])==null?void 0:f.kind)==="sessionNodes"?s.jsx(Gn,{descriptor:a,fetchKey:`${d??""}:${o}`},`${a.resourceType}:${JSON.stringify(a.filter??null)}:${a.order??""}`):s.jsx(qn,{descriptor:a,fetchKey:`${d??""}:${o}`},`${a.resourceType}:${JSON.stringify(a.filter??null)}:${a.order??""}`)})},e[3]=a,e[4]=d,e[5]=p):p=e[5];let t;return e[6]!==l||e[7]!==r||e[8]!==p||e[9]!==m?(t=s.jsx(_n,{title:m,onEdit:l,onRemove:r,children:p}),e[6]=l,e[7]=r,e[8]=p,e[9]=m,e[10]=t):t=e[10],t},qn=n=>{"use memo";var A;const e=G.c(46),{descriptor:a,fetchKey:d,onChangeOrder:l}=n,{t:r}=fe(),u=Qe(),i=ye[a.resourceType];let m;e[0]===Symbol.for("react.memo_cache_sentinel")?(m={current:1,pageSize:10},e[0]=m):m=e[0];const{baiPaginationOption:p,tablePaginationOption:t,setTablePaginationOption:o}=Sn(m),g=a.order??i.defaultOrder;let f;e[1]!==p.limit||e[2]!==p.offset||e[3]!==i||e[4]!==u.id||e[5]!==a.filter||e[6]!==g?(f=i.buildVariables({filter:a.filter??void 0,order:g,limit:p.limit,offset:p.offset,projectId:u.id??""}),e[1]=p.limit,e[2]=p.offset,e[3]=i,e[4]=u.id,e[5]=a.filter,e[6]=g,e[7]=f):f=e[7];const c=f,S=E.useDeferredValue(c),k=E.useDeferredValue(d);let y;e[8]!==k?(y={fetchPolicy:"store-and-network",fetchKey:k},e[8]=k,e[9]=y):y=e[9];const K=Xe.useLazyLoadQuery(i.query,S,y);let _,T,b,I,F,h;if(e[10]!==i||e[11]!==K||e[12]!==k||e[13]!==S||e[14]!==d||e[15]!==l||e[16]!==r||e[17]!==c){if(T=i.selectConnection(K),b=S!==c||k!==d,e[24]!==i||e[25]!==l||e[26]!==r){const v=((A=i.getColumns)==null?void 0:A.call(i,r))??[];_=ua,I="id",F=l?[...v]:v.map(yt),e[24]=i,e[25]=l,e[26]=r,e[27]=_,e[28]=I,e[29]=F}else _=e[27],I=e[28],F=e[29];h=[...(T==null?void 0:T.nodes)??[]],e[10]=i,e[11]=K,e[12]=k,e[13]=S,e[14]=d,e[15]=l,e[16]=r,e[17]=c,e[18]=_,e[19]=T,e[20]=b,e[21]=I,e[22]=F,e[23]=h}else _=e[18],T=e[19],b=e[20],I=e[21],F=e[22],h=e[23];const R=(T==null?void 0:T.count)??0;let x;e[30]!==o?(x=(v,C)=>o({current:v,pageSize:C}),e[30]=o,e[31]=x):x=e[31];let L;e[32]!==R||e[33]!==x||e[34]!==t.current||e[35]!==t.pageSize?(L={current:t.current,pageSize:t.pageSize,total:R,onChange:x},e[32]=R,e[33]=x,e[34]=t.current,e[35]=t.pageSize,e[36]=L):L=e[36];let j;return e[37]!==_||e[38]!==b||e[39]!==l||e[40]!==g||e[41]!==I||e[42]!==F||e[43]!==h||e[44]!==L?(j=s.jsx(_,{rowKey:I,columns:F,dataSource:h,loading:b,order:g,onChangeOrder:l,pagination:L}),e[37]=_,e[38]=b,e[39]=l,e[40]=g,e[41]=I,e[42]=F,e[43]=h,e[44]=L,e[45]=j):j=e[45],j};function yt(n){return{...n,sorter:!1}}const ft=n=>{"use memo";const e=G.c(11),{descriptor:a,fetchKey:d,onEdit:l,onRemove:r}=n,{t:u}=fe();let i;e[0]!==a||e[1]!==u?(i=Ze(a,u),e[0]=a,e[1]=u,e[2]=i):i=e[2];const m=i;let p;e[3]!==a||e[4]!==d?(p=o=>s.jsx(E.Suspense,{fallback:s.jsx(Ne,{}),children:s.jsx(zn,{descriptor:a,fetchKey:`${d??""}:${o}`},`${JSON.stringify(a.filter??null)}:${a.order??""}`)}),e[3]=a,e[4]=d,e[5]=p):p=e[5];let t;return e[6]!==l||e[7]!==r||e[8]!==p||e[9]!==m?(t=s.jsx(_n,{title:m,onEdit:l,onRemove:r,children:p}),e[6]=l,e[7]=r,e[8]=p,e[9]=m,e[10]=t):t=e[10],t},zn=n=>{"use memo";const e=G.c(12),{descriptor:a,fetchKey:d,onChangeViewParams:l,disableSessionDetail:r}=n,u=Qe(),i=un(),m=Rn(),p=typeof a.filter=="string"?a.filter:null,t=a.order??null,o=u.id??null,g=d??"",f=a.gridView??He;let c;e[0]!==r||e[1]!==m||e[2]!==i?(c=r?void 0:k=>{const y=new URLSearchParams(m.search);y.set("sessionDetail",k),i({pathname:m.pathname,hash:m.hash,search:y.toString()})},e[0]=r,e[1]=m,e[2]=i,e[3]=c):c=e[3];let S;return e[4]!==l||e[5]!==p||e[6]!==t||e[7]!==o||e[8]!==g||e[9]!==f||e[10]!==c?(S=s.jsx(ca,{filter:p,order:t,projectId:o,fetchKey:g,viewParams:f,onChangeViewParams:l,onClickSession:c}),e[4]=l,e[5]=p,e[6]=t,e[7]=o,e[8]=g,e[9]=f,e[10]=c,e[11]=S):S=e[11],S};/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */const Un={resourceTable:pt,resourceCount:dt,sessionResourceGrid:ft},Qn={resourceTable:"dashboard.panelModal.Table",resourceCount:"dashboard.panelModal.Count",sessionResourceGrid:"session.resourceGrid.GridView"},vn=(n,{gridEnabled:e,forcePanelType:a})=>{const d=["resourceTable","resourceCount"];return n==="session"&&(e||a==="sessionResourceGrid")&&d.push("sessionResourceGrid"),d},St=(n,{gridEnabled:e})=>n.panelType==="sessionResourceGrid"&&!e?"resourceTable":n.panelType,ln=n=>Array.isArray(n)?n.filter(e=>{if(!e||typeof e!="object")return!1;const a=e;return typeof a.id=="string"&&a.panelType in Un&&!!a.descriptor&&a.descriptor.resourceType in ye&&(a.descriptor.title===void 0||typeof a.descriptor.title=="string")}):[],kt=n=>{"use memo";const e=G.c(43);let a;e[0]!==n?(a=n===void 0?{}:n,e[0]=n,e[1]=a):a=e[1];const{enabled:d,fetchKey:l,onRequestEdit:r}=a,u=d===void 0?!0:d,{t:i}=fe(),m=xn(),[p,t]=Ue("custom_dashboard_panels"),[,o]=Ue("dashboard_board_items"),[g]=Ue("experimental_session_resource_grid");let f,c,S,k,y,K,_;if(e[2]!==u||e[3]!==l||e[4]!==g||e[5]!==r||e[6]!==o||e[7]!==t||e[8]!==p||e[9]!==i||e[10]!==m){k=u?p?ln(p):[...an]:[];let F;e[18]!==m?(c=ot(m),F=new Set(c),e[18]=m,e[19]=c,e[20]=F):(c=e[19],F=e[20]);const h=F;let R;e[21]!==t?(R=v=>{t(C=>[...ln(C??an),Wa(v)])},e[21]=t,e[22]=R):R=e[22],f=R,_=(v,C)=>{const N=k.find(D=>D.id===v);if(N&&N.panelType!==C.panelType){const D=rn[C.panelType]??rn.resourceTable;o(w=>Array.isArray(w)?w.map(M=>M.id===v?{id:v,...D}:M):w)}t(D=>ln(D??an).map(w=>w.id===v?{...w,panelType:C.panelType,descriptor:{resourceType:C.resourceType,title:C.title,filter:C.filter??null,order:C.order??null,gridView:C.panelType==="sessionResourceGrid"?C.gridView??He:null}}:w))};let x;e[23]!==o||e[24]!==t?(x=v=>{t(C=>ln(C??an).filter(N=>N.id!==v)),o(C=>Array.isArray(C)?C.filter(N=>N.id!==v):C)},e[23]=o,e[24]=t,e[25]=x):x=e[25],y=x;let L;e[26]!==h?(L=v=>h.has(v.descriptor.resourceType),e[26]=h,e[27]=L):L=e[27];const j=k.filter(L);S=j.map(Ft);let A;e[28]!==l||e[29]!==g||e[30]!==r||e[31]!==y||e[32]!==i?(A=v=>{const C=Un[St(v,{gridEnabled:!!g})],N=s.jsx(We,{title:Ze(v.descriptor,i),status:"error",children:C?s.jsx(C,{descriptor:v.descriptor,fetchKey:l,onEdit:r?()=>r(v):void 0,onRemove:()=>y(v.id)}):null},`${v.panelType}:${JSON.stringify(v.descriptor)}`);return[v.id,N]},e[28]=l,e[29]=g,e[30]=r,e[31]=y,e[32]=i,e[33]=A):A=e[33],K=new Map(j.map(A)),e[2]=u,e[3]=l,e[4]=g,e[5]=r,e[6]=o,e[7]=t,e[8]=p,e[9]=i,e[10]=m,e[11]=f,e[12]=c,e[13]=S,e[14]=k,e[15]=y,e[16]=K,e[17]=_}else f=e[11],c=e[12],S=e[13],k=e[14],y=e[15],K=e[16],_=e[17];const T=K,b=!!g;let I;return e[34]!==f||e[35]!==c||e[36]!==T||e[37]!==S||e[38]!==k||e[39]!==y||e[40]!==b||e[41]!==_?(I={panels:k,availableResources:c,gridEnabled:b,customDefaultLayout:S,customContentById:T,addPanel:f,updatePanel:_,removePanel:y},e[34]=f,e[35]=c,e[36]=T,e[37]=S,e[38]=k,e[39]=y,e[40]=b,e[41]=_,e[42]=I):I=e[42],I};function Ft(n){return{id:n.id,...rn[n.panelType]??rn.resourceTable}}const _t=n=>{"use memo";const e=G.c(47),{panels:a,availableResources:d,gridEnabled:l,onRequestAdd:r,onRequestEdit:u,onRemove:i,onResetLayout:m}=n,p=l===void 0?!1:l,{t}=fe(),{token:o}=Ge.useToken();let g;e[0]!==d?(g=new Set(d),e[0]=d,e[1]=g):g=e[1];const f=g,c=`1px solid ${o.colorBorder}`;let S;e[2]!==c||e[3]!==o.paddingLG?(S={width:320,flexShrink:0,paddingLeft:o.paddingLG,borderLeft:c,overflow:"auto"},e[2]=c,e[3]=o.paddingLG,e[4]=S):S=e[4];let k;e[5]!==t?(k=t("dashboard.editSider.Title"),e[5]=t,e[6]=k):k=e[6];let y;e[7]!==k?(y=s.jsx(en,{strong:!0,children:k}),e[7]=k,e[8]=y):y=e[8];let K;e[9]===Symbol.for("react.memo_cache_sentinel")?(K=s.jsx(ma,{size:"1em"}),e[9]=K):K=e[9];let _;e[10]!==t?(_=t("button.Add"),e[10]=t,e[11]=_):_=e[11];let T;e[12]!==r||e[13]!==_?(T=s.jsx(yn,{variant:"primary",size:"sm",icon:K,label:_,onClick:r}),e[12]=r,e[13]=_,e[14]=T):T=e[14];let b;e[15]!==y||e[16]!==T?(b=s.jsxs($,{direction:"row",justify:"between",align:"center",gap:"sm",children:[y,T]}),e[15]=y,e[16]=T,e[17]=b):b=e[17];let I;e[18]!==f||e[19]!==p||e[20]!==i||e[21]!==u||e[22]!==a||e[23]!==t||e[24]!==o.colorBorderSecondary||e[25]!==o.fontSizeSM||e[26]!==o.paddingXS?(I=a.length===0?s.jsx(en,{type:"secondary",children:t("dashboard.editSider.Empty")}):s.jsx($,{direction:"column",align:"stretch",children:a.map(v=>{var V;const C=Ze(v.descriptor,t),N=t(((V=ye[v.descriptor.resourceType])==null?void 0:V.labelKey)??v.descriptor.resourceType),D=f.has(v.descriptor.resourceType),w=v.panelType==="sessionResourceGrid"&&!p,M=[t(w?"dashboard.editSider.GridDisabled":Qn[v.panelType]??v.panelType),v.descriptor.title?N:void 0,D?void 0:t("dashboard.editSider.RequiresSuperadmin")].filter(Boolean).join(" · ");return s.jsxs($,{direction:"row",justify:"between",align:"center",gap:"sm",style:{paddingBlock:o.paddingXS,borderBottom:`1px solid ${o.colorBorderSecondary}`},children:[s.jsxs($,{direction:"column",align:"stretch",style:{flex:1,minWidth:0},children:[s.jsx(en,{ellipsis:!0,children:C}),s.jsx(en,{type:"secondary",ellipsis:{tooltip:M},style:{fontSize:o.fontSizeSM},children:M})]}),s.jsxs($,{direction:"row",align:"center",gap:"xxs",children:[s.jsx(sn,{variant:"ghost",size:"sm",label:t("button.Edit"),tooltip:t("button.Edit"),icon:s.jsx(Tn,{size:"1em"}),onClick:()=>u(v)}),s.jsx(fn,{title:t("dialog.ask.DoYouWantToDeleteSomething",{name:C}),isDanger:!0,onConfirm:()=>i(v.id),children:s.jsx(sn,{variant:"ghost",size:"sm",label:t("button.Delete"),tooltip:t("button.Delete"),icon:s.jsx(Kn,{size:"1em"})})})]})]},v.id)})}),e[18]=f,e[19]=p,e[20]=i,e[21]=u,e[22]=a,e[23]=t,e[24]=o.colorBorderSecondary,e[25]=o.fontSizeSM,e[26]=o.paddingXS,e[27]=I):I=e[27];let F;e[28]!==t?(F=t("dashboard.editSider.ResetLayout"),e[28]=t,e[29]=F):F=e[29];let h;e[30]!==t?(h=t("dashboard.editSider.ResetLayoutDescription"),e[30]=t,e[31]=h):h=e[31];let R;e[32]===Symbol.for("react.memo_cache_sentinel")?(R=s.jsx(ga,{size:"1em"}),e[32]=R):R=e[32];let x;e[33]!==t?(x=t("dashboard.editSider.ResetLayout"),e[33]=t,e[34]=x):x=e[34];let L;e[35]!==x?(L=s.jsx(yn,{variant:"secondary",size:"sm",icon:R,label:x}),e[35]=x,e[36]=L):L=e[36];let j;e[37]!==m||e[38]!==F||e[39]!==h||e[40]!==L?(j=s.jsx(fn,{title:F,description:h,isDanger:!0,onConfirm:m,children:L}),e[37]=m,e[38]=F,e[39]=h,e[40]=L,e[41]=j):j=e[41];let A;return e[42]!==b||e[43]!==I||e[44]!==j||e[45]!==S?(A=s.jsxs($,{direction:"column",align:"stretch",gap:"md",style:S,children:[b,I,j]}),e[42]=b,e[43]=I,e[44]=j,e[45]=S,e[46]=A):A=e[46],A},bt=n=>{"use memo";var Je,qe;const e=G.c(178),{open:a,onRequestClose:d,initialPanel:l,availableResources:r,gridEnabled:u,onSubmit:i,afterClose:m}=n,p=u===void 0?!1:u,{t}=fe(),{token:o}=Ge.useToken(),[g]=Ee.useForm(),f=r[0],c=(l==null?void 0:l.descriptor.resourceType)??f;let S;e[0]!==r||e[1]!==l||e[2]!==c?(S=l&&!r.includes(c)?[...r,c]:r,e[0]=r,e[1]=l,e[2]=c,e[3]=S):S=e[3];const k=S,[y,K]=E.useState((l==null?void 0:l.descriptor.order)??null),[_,T]=E.useState((l==null?void 0:l.descriptor.gridView)??He),b=Ee.useWatch("resourceType",g)??c,I=Ee.useWatch("panelType",g)??(l==null?void 0:l.panelType)??"resourceTable",F=Ee.useWatch("filter",g)??void 0,h=ye[b];let R,x,L,j,A,v,C,N,D,w,M,V,q,De,Ve,U,Se,Ie,Re,Q,ke,_e,xe,W,B,X,Fe;if(e[4]!==m||e[5]!==g||e[6]!==p||e[7]!==_||e[8]!==l||e[9]!==c||e[10]!==d||e[11]!==i||e[12]!==a||e[13]!==y||e[14]!==b||e[15]!==t){const z=vn(b,{gridEnabled:p,forcePanelType:l==null?void 0:l.panelType});let we;e[43]!==g||e[44]!==_||e[45]!==d||e[46]!==i||e[47]!==y?(we=async()=>{var Oe;let P;try{P=await g.validateFields()}catch{return}i({panelType:P.panelType,resourceType:P.resourceType,title:((Oe=P.title)==null?void 0:Oe.trim())||void 0,filter:P.filter??null,order:y,gridView:P.panelType==="sessionResourceGrid"?_:null}),d()},e[43]=g,e[44]=_,e[45]=d,e[46]=i,e[47]=y,e[48]=we):we=e[48];const Ye=we;A=ya,De=a,Ve="min(960px, 95vw)",e[49]!==l||e[50]!==t?(U=t(l?"dashboard.panelModal.EditPanel":"dashboard.panelModal.AddPanel"),e[49]=l,e[50]=t,e[51]=U):U=e[51],e[52]!==l||e[53]!==t?(Se=t(l?"button.Save":"button.Add"),e[52]=l,e[53]=t,e[54]=Se):Se=e[54],Ie=Ye,Re=d,Q=m,j=Ee,w=g,M="vertical";const Be=(l==null?void 0:l.panelType)??"resourceTable",$e=l==null?void 0:l.descriptor.title,je=(l==null?void 0:l.descriptor.filter)??void 0;e[55]!==c||e[56]!==Be||e[57]!==$e||e[58]!==je?(V={panelType:Be,resourceType:c,title:$e,filter:je},e[55]=c,e[56]=Be,e[57]=$e,e[58]=je,e[59]=V):V=e[59],e[60]!==g||e[61]!==p||e[62]!==(l==null?void 0:l.panelType)?(q=P=>{P.resourceType&&(g.setFieldsValue({filter:void 0}),K(null),T(He),vn(P.resourceType,{gridEnabled:p,forcePanelType:l==null?void 0:l.panelType}).includes(g.getFieldValue("panelType"))||g.setFieldsValue({panelType:"resourceTable"}))},e[60]=g,e[61]=p,e[62]=l==null?void 0:l.panelType,e[63]=q):q=e[63],L=$,v="row",C="start",N="md",D="wrap",x=Ee.Item,xe="panelType",e[64]!==t?(W=t("dashboard.panelModal.PanelType"),e[64]=t,e[65]=W):W=e[65],B=!0;let pe;e[66]!==t?(pe=t("dashboard.panelModal.PanelTypeRequired"),e[66]=t,e[67]=pe):pe=e[67],e[68]!==pe?(X=[{required:!0,message:pe}],e[68]=pe,e[69]=X):X=e[69],e[70]===Symbol.for("react.memo_cache_sentinel")?(Fe={flexShrink:0},e[70]=Fe):Fe=e[70],R=fa,e[71]!==t?(ke=t("dashboard.panelModal.PanelType"),e[71]=t,e[72]=ke):ke=e[72];let Ae;e[73]!==t?(Ae=P=>({value:P,label:t(Qn[P])}),e[73]=t,e[74]=Ae):Ae=e[74],_e=z.map(Ae),e[4]=m,e[5]=g,e[6]=p,e[7]=_,e[8]=l,e[9]=c,e[10]=d,e[11]=i,e[12]=a,e[13]=y,e[14]=b,e[15]=t,e[16]=R,e[17]=x,e[18]=L,e[19]=j,e[20]=A,e[21]=v,e[22]=C,e[23]=N,e[24]=D,e[25]=w,e[26]=M,e[27]=V,e[28]=q,e[29]=De,e[30]=Ve,e[31]=U,e[32]=Se,e[33]=Ie,e[34]=Re,e[35]=Q,e[36]=ke,e[37]=_e,e[38]=xe,e[39]=W,e[40]=B,e[41]=X,e[42]=Fe}else R=e[16],x=e[17],L=e[18],j=e[19],A=e[20],v=e[21],C=e[22],N=e[23],D=e[24],w=e[25],M=e[26],V=e[27],q=e[28],De=e[29],Ve=e[30],U=e[31],Se=e[32],Ie=e[33],Re=e[34],Q=e[35],ke=e[36],_e=e[37],xe=e[38],W=e[39],B=e[40],X=e[41],Fe=e[42];let J;e[75]!==R||e[76]!==ke||e[77]!==_e?(J=s.jsx(R,{label:ke,options:_e}),e[75]=R,e[76]=ke,e[77]=_e,e[78]=J):J=e[78];let Y;e[79]!==x||e[80]!==J||e[81]!==xe||e[82]!==W||e[83]!==B||e[84]!==X||e[85]!==Fe?(Y=s.jsx(x,{name:xe,label:W,required:B,rules:X,style:Fe,children:J}),e[79]=x,e[80]=J,e[81]=xe,e[82]=W,e[83]=B,e[84]=X,e[85]=Fe,e[86]=Y):Y=e[86];let H;e[87]!==t?(H=t("dashboard.panelModal.DataSource"),e[87]=t,e[88]=H):H=e[88];let be;e[89]!==t?(be=t("dashboard.panelModal.DataSourceRequired"),e[89]=t,e[90]=be):be=e[90];let Z;e[91]!==be?(Z=[{required:!0,message:be}],e[91]=be,e[92]=Z):Z=e[92];let he;e[93]===Symbol.for("react.memo_cache_sentinel")?(he={flex:1,minWidth:180},e[93]=he):he=e[93];let ee;e[94]!==t?(ee=t("dashboard.panelModal.DataSource"),e[94]=t,e[95]=ee):ee=e[95];let ne;if(e[96]!==k||e[97]!==t){let z;e[99]!==t?(z=we=>({value:we,label:t(ye[we].labelKey)}),e[99]=t,e[100]=z):z=e[100],ne=k.map(z),e[96]=k,e[97]=t,e[98]=ne}else ne=e[98];let ve;e[101]!==ee||e[102]!==ne?(ve=s.jsx(Sa,{label:ee,options:ne}),e[101]=ee,e[102]=ne,e[103]=ve):ve=e[103];let ae;e[104]!==H||e[105]!==Z||e[106]!==ve?(ae=s.jsx(Ee.Item,{name:"resourceType",label:H,required:!0,rules:Z,style:he,children:ve}),e[104]=H,e[105]=Z,e[106]=ve,e[107]=ae):ae=e[107];let te;e[108]!==t?(te=t("dashboard.panelModal.TitleOptional"),e[108]=t,e[109]=te):te=e[109];let le;e[110]!==t?(le=t("dashboard.panelModal.TitleDescription"),e[110]=t,e[111]=le):le=e[111];let Ce;e[112]===Symbol.for("react.memo_cache_sentinel")?(Ce={flex:1,minWidth:180},e[112]=Ce):Ce=e[112];let Te;e[113]!==t?(Te=t("dashboard.panelModal.TitleOptional"),e[113]=t,e[114]=Te):Te=e[114];let se;e[115]!==h.labelKey||e[116]!==t?(se=t(h.labelKey),e[115]=h.labelKey,e[116]=t,e[117]=se):se=e[117];let re;e[118]!==Te||e[119]!==se?(re=s.jsx(ka,{label:Te,placeholder:se,hasClear:!0}),e[118]=Te,e[119]=se,e[120]=re):re=e[120];let ie;e[121]!==te||e[122]!==le||e[123]!==re?(ie=s.jsx(Ee.Item,{name:"title",label:te,extra:le,style:Ce,children:re}),e[121]=te,e[122]=le,e[123]=re,e[124]=ie):ie=e[124];let oe;e[125]!==L||e[126]!==v||e[127]!==C||e[128]!==N||e[129]!==D||e[130]!==Y||e[131]!==ae||e[132]!==ie?(oe=s.jsxs(L,{direction:v,align:C,gap:N,wrap:D,children:[Y,ae,ie]}),e[125]=L,e[126]=v,e[127]=C,e[128]=N,e[129]=D,e[130]=Y,e[131]=ae,e[132]=ie,e[133]=oe):oe=e[133];let de;e[134]!==t?(de=t("dashboard.panelModal.Condition"),e[134]=t,e[135]=de):de=e[135];let Ke;e[136]!==h||e[137]!==t?(Ke=h.kind==="sessionNodes"?s.jsx(pa,{filterProperties:((Je=h.getStringFilterProperties)==null?void 0:Je.call(h,t))??[]}):s.jsx(qa,{style:{width:"100%"},filterProperties:[...((qe=h.getFilterProperties)==null?void 0:qe.call(h,t))??[]]}),e[136]=h,e[137]=t,e[138]=Ke):Ke=e[138];let ue;e[139]!==de||e[140]!==Ke?(ue=s.jsx(Ee.Item,{name:"filter",label:de,children:Ke}),e[139]=de,e[140]=Ke,e[141]=ue):ue=e[141];let ce;e[142]!==j||e[143]!==w||e[144]!==M||e[145]!==V||e[146]!==q||e[147]!==oe||e[148]!==ue?(ce=s.jsxs(j,{form:w,layout:M,initialValues:V,onValuesChange:q,children:[oe,ue]}),e[142]=j,e[143]=w,e[144]=M,e[145]=V,e[146]=q,e[147]=oe,e[148]=ue,e[149]=ce):ce=e[149];const Pe=`1px solid ${o.colorBorderSecondary}`;let me;e[150]!==Pe||e[151]!==o.borderRadius||e[152]!==o.paddingSM?(me={border:Pe,borderRadius:o.borderRadius,padding:o.paddingSM,maxHeight:360,overflow:"auto"},e[150]=Pe,e[151]=o.borderRadius,e[152]=o.paddingSM,e[153]=me):me=e[153];let Le;e[154]!==h.kind||e[155]!==h.labelKey||e[156]!==F||e[157]!==_||e[158]!==a||e[159]!==y||e[160]!==I||e[161]!==b||e[162]!==t?(Le=a?s.jsx(We,{title:t(h.labelKey),status:"error",children:s.jsx(E.Suspense,{fallback:s.jsx(Ne,{}),children:I==="resourceCount"?s.jsx($,{align:"center",justify:"center",children:s.jsx($n,{descriptor:{resourceType:b,filter:F??null,order:y}},`${b}:${JSON.stringify(F??null)}`)}):I==="sessionResourceGrid"?s.jsx(zn,{descriptor:{resourceType:b,filter:F??null,order:y,gridView:_},onChangeViewParams:T,disableSessionDetail:!0},`${b}:${JSON.stringify(F??null)}`):h.kind==="deploymentNodes"?s.jsx(On,{descriptor:{resourceType:b,filter:F??null,order:y},onChangeOrder:z=>K(z??null),disableNavigation:!0},`${b}:${JSON.stringify(F??null)}`):h.kind==="sessionNodes"?s.jsx(Gn,{descriptor:{resourceType:b,filter:F??null,order:y},onChangeOrder:z=>K(z??null),disableSessionDetail:!0},`${b}:${JSON.stringify(F??null)}`):s.jsx(qn,{descriptor:{resourceType:b,filter:F??null,order:y},onChangeOrder:z=>K(z??null)},`${b}:${JSON.stringify(F??null)}`)})},`${I}:${b}:${JSON.stringify(F??null)}`):null,e[154]=h.kind,e[155]=h.labelKey,e[156]=F,e[157]=_,e[158]=a,e[159]=y,e[160]=I,e[161]=b,e[162]=t,e[163]=Le):Le=e[163];let ge;e[164]!==me||e[165]!==Le?(ge=s.jsx($,{direction:"column",align:"stretch",gap:"xs",children:s.jsx("div",{style:me,children:Le})}),e[164]=me,e[165]=Le,e[166]=ge):ge=e[166];let Me;return e[167]!==A||e[168]!==De||e[169]!==Ve||e[170]!==U||e[171]!==Se||e[172]!==Ie||e[173]!==Re||e[174]!==Q||e[175]!==ce||e[176]!==ge?(Me=s.jsxs(A,{open:De,width:Ve,title:U,okText:Se,onOk:Ie,onCancel:Re,afterClose:Q,children:[ce,ge]}),e[167]=A,e[168]=De,e[169]=Ve,e[170]=U,e[171]=Se,e[172]=Ie,e[173]=Re,e[174]=Q,e[175]=ce,e[176]=ge,e[177]=Me):Me=e[177],Me};/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */const ht=({persistedLayout:n,defaultLayout:e,renderableIds:a})=>{const d=new Set(n.map(l=>l.id));return[...n.filter(l=>a.has(l.id)),...e.filter(l=>!d.has(l.id))]},vt=(n,e)=>{const a=new Set(n.map(l=>l.id)),d=[...n];return e.forEach((l,r)=>{a.has(l.id)||d.splice(Math.min(r,d.length),0,l)}),d},Ct=()=>{"use memo";const n=G.c(21),{t:e}=fe(),{token:a}=Ge.useToken(),d=kn();let l;n[0]===Symbol.for("react.memo_cache_sentinel")?(l=["vhostInfo"],n[0]=l):l=n[0];let r;n[1]!==d?(r={queryKey:l,queryFn:()=>d.vfolder.list_hosts()},n[1]=d,n[2]=r):r=n[2];const{data:u}=jn(r);let i;n[3]!==(u==null?void 0:u.volume_info)?(i=Fa(_a((u==null?void 0:u.volume_info)??{}),Tt),n[3]=u==null?void 0:u.volume_info,n[4]=i):i=n[4];const m=i;let p;n[5]!==m?(p=m?{id:m[0],...m[1]}:void 0,n[5]=m,n[6]=p):p=n[6];const t=p;let o;n[7]!==a.padding||n[8]!==a.paddingXL?(o={paddingInline:a.paddingXL,paddingBottom:a.padding},n[7]=a.padding,n[8]=a.paddingXL,n[9]=o):o=n[9];let g;n[10]!==e?(g=e("data.QuotaPerStorageVolume"),n[10]=e,n[11]=g):g=n[11];let f;n[12]!==g?(f=s.jsx(on,{title:g}),n[12]=g,n[13]=f):f=n[13];let c;n[14]!==t||n[15]!==e?(c=t?s.jsx(za,{defaultVolumeInfo:t}):s.jsx(ba,{title:e("storageHost.QuotaDoesNotSupported"),isCompact:!0}),n[14]=t,n[15]=e,n[16]=c):c=n[16];let S;return n[17]!==o||n[18]!==f||n[19]!==c?(S=s.jsxs($,{direction:"column",align:"stretch",style:o,children:[f,c]}),n[17]=o,n[18]=f,n[19]=c,n[20]=S):S=n[20],S};function Tt(n){const[,e]=n;return Dn(e==null?void 0:e.capabilities,"quota")}const Wn=(function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"name"}],e={alias:null,args:null,kind:"ScalarField",name:"max_vfolder_count",storageKey:null},a=[e],d=[{kind:"Variable",name:"name",variableName:"name"}],l=[e,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}];return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"StorageStatusPanelCardQuery",selections:[{alias:null,args:null,concreteType:"UserResourcePolicy",kind:"LinkedField",name:"user_resource_policy",plural:!1,selections:a,storageKey:null},{alias:null,args:d,concreteType:"ProjectResourcePolicy",kind:"LinkedField",name:"project_resource_policy",plural:!1,selections:a,storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"StorageStatusPanelCardQuery",selections:[{alias:null,args:null,concreteType:"UserResourcePolicy",kind:"LinkedField",name:"user_resource_policy",plural:!1,selections:l,storageKey:null},{alias:null,args:d,concreteType:"ProjectResourcePolicy",kind:"LinkedField",name:"project_resource_policy",plural:!1,selections:l,storageKey:null}]},params:{cacheID:"6a4458681167a38a930cf05173cf0d90",id:null,metadata:{},name:"StorageStatusPanelCardQuery",operationKind:"query",text:`query StorageStatusPanelCardQuery(
  $name: String!
) {
  user_resource_policy {
    max_vfolder_count
    id
  }
  project_resource_policy(name: $name) {
    max_vfolder_count
    id
  }
}
`}}})();Wn.hash="33191e01e0635b3635f28c7383463c39";const pn=90,Kt=({fetchKey:n,onRequestBadgeClick:e,style:a,...d})=>{const{t:l}=fe(),{token:r}=Ge.useToken(),u=kn(),i=Qe();if(!i.name)throw new Error("Project name is required for StorageStatusPanelCard");if(!i.id)throw new Error("Project ID is required for StorageStatusPanelCard");const m=E.useDeferredValue(n),[p,{updateInvitations:t}]=ha(),o=p.length;va(()=>{t()},[n]);const g=_=>Dn(["delete-ongoing","delete-complete","delete-error"],_),{data:f}=jn({queryKey:["vfolders",{deferredFetchKey:m,id:i.id}],queryFn:()=>{if(!(i!=null&&i.id))throw new Error("Project ID is required for StorageStatusPanelCard");return u.vfolder.list(i.id)}}),c=f==null?void 0:f.filter(_=>_.is_owner&&_.ownership_type==="user"&&!g(_.status)).length,S=f==null?void 0:f.filter(_=>_.ownership_type==="group"&&!g(_.status)).length,k=f==null?void 0:f.filter(_=>!_.is_owner&&_.ownership_type==="user"&&!g(_.status)).length,{user_resource_policy:y,project_resource_policy:K}=Xe.useLazyLoadQuery(Wn,{name:i.name});return s.jsxs($,{direction:"column",align:"stretch",style:{paddingInline:r.paddingXL,paddingBottom:r.padding,...a},...d,children:[s.jsx(on,{title:l("data.FolderStatus")}),s.jsxs(Nn,{rowGap:r.marginXL,columnGap:r.marginXL,dividerColor:r.colorBorder,dividerInset:r.marginXS,dividerWidth:r.lineWidth,children:[s.jsx(gn,{title:l("data.MyFolders"),value:c,unit:y!=null&&y.max_vfolder_count?`/ ${y==null?void 0:y.max_vfolder_count}`:void 0,style:{maxWidth:pn},color:r.colorText}),s.jsx(gn,{title:l("data.ProjectFolders"),value:S,unit:K!=null&&K.max_vfolder_count?`/ ${K==null?void 0:K.max_vfolder_count}`:void 0,style:{maxWidth:pn},color:r.colorText}),s.jsx(gn,{title:o>0?s.jsx("a",{onClick:()=>{e==null||e()},children:s.jsx(Ca,{content:l("data.InvitedFoldersTooltip",{count:o}),placement:"above",alignment:"end",children:s.jsx(Ta,{count:`+${o}`,variant:"error",offset:[-r.sizeXS,-r.sizeXS],style:{zIndex:50},title:l("data.InvitedFoldersTooltip",{count:o}),children:s.jsx(cn,{size:"lg",children:l("data.InvitedFolders")})})})}):s.jsx(cn,{size:"lg",children:l("data.InvitedFolders")}),value:s.jsx(cn,{size:"4xl",children:k}),style:{maxWidth:pn}})]})]})},Yt=()=>{"use memo";const n=G.c(121),{token:e}=Ge.useToken(),{t:a}=fe(),d=Qe(),l=Ka(),r=xn(),u=kn(),i=un(),m=In(),[p,t]=Ln(),o=E.useDeferredValue(p),[g,f]=E.useTransition(),c=g||p!==o,[S,k]=Ue("dashboard_board_items"),[y]=Ue("experimental_custom_dashboard_panels"),[K,_]=Cn(Fn),T=La(Aa);let b,I;n[0]!==y||n[1]!==T||n[2]!==_?(b=()=>{if(y)return T(s.jsx(Ua,{})),()=>{T(null),_(!1)}},I=[y,T,_],n[0]=y,n[1]=T,n[2]=_,n[3]=b,n[4]=I):(b=n[3],I=n[4]),E.useEffect(b,I);let F;n[5]===Symbol.for("react.memo_cache_sentinel")?(F={open:!1},n[5]=F):F=n[5];const[h,R]=E.useState(F),x=E.useRef(null),L=!!y;let j;n[6]===Symbol.for("react.memo_cache_sentinel")?(j=O=>R({open:!0,panel:O}),n[6]=j):j=n[6];let A;n[7]!==o||n[8]!==L?(A={enabled:L,fetchKey:o,onRequestEdit:j},n[7]=o,n[8]=L,n[9]=A):A=n[9];const{panels:v,availableResources:C,gridEnabled:N,customDefaultLayout:D,customContentById:w,addPanel:M,updatePanel:V,removePanel:q}=kt(A),De=Na(),Ve=u.supports("agent-stats");let U;n[10]===Symbol.for("react.memo_cache_sentinel")?(U=wn,n[10]=U):U=n[10];const Se=`project:${d.id}`,Ie=l||"default",Re=!De;let Q;n[11]!==r?(Q=nn(r,"superadmin"),n[11]=r,n[12]=Q):Q=n[12];const ke=`schedulable == true & status == "ALIVE" & scaling_group == "${l}"`;let _e;n[13]!==Q||n[14]!==ke||n[15]!==Se||n[16]!==Ie||n[17]!==Re?(_e={scopeId:Se,resourceGroup:Ie,skipTotalResourceWithinResourceGroup:Re,isSuperAdmin:Q,agentNodeFilter:ke,aliveAgentFilter:'status == "ALIVE"',schedulableAgentFilter:'status == "ALIVE" & schedulable == true'},n[13]=Q,n[14]=ke,n[15]=Se,n[16]=Ie,n[17]=Re,n[18]=_e):_e=n[18];const xe=o===Ma?"store-and-network":"network-only";let W;n[19]!==o||n[20]!==xe?(W={fetchPolicy:xe,fetchKey:o},n[19]=o,n[20]=xe,n[21]=W):W=n[21];const B=Xe.useLazyLoadQuery(U,_e,W);let X;n[22]!==t?(X=()=>{f(()=>{t()})},n[22]=t,n[23]=X):X=n[23],Ia(X,15e3);const Fe=`0px ${e.marginMD}px`;let J;n[24]!==Fe?(J=s.jsx(Ne,{style:{padding:Fe}}),n[24]=Fe,n[25]=J):J=n[25];let Y;n[26]!==a||n[27]!==r?(Y=nn(r,"superadmin")?a("session.ActiveSessions"):a("session.MySessions"),n[26]=a,n[27]=r,n[28]=Y):Y=n[28];let H;n[29]!==c||n[30]!==B||n[31]!==Y?(H=s.jsx(Ba,{queryRef:B,isRefetching:c,title:Y}),n[29]=c,n[30]=B,n[31]=Y,n[32]=H):H=n[32];let be;n[33]!==J||n[34]!==H?(be=s.jsx(E.Suspense,{fallback:J,children:H}),n[33]=J,n[34]=H,n[35]=be):be=n[35];let Z;n[36]!==a?(Z=a("webui.menu.MyResources"),n[36]=a,n[37]=Z):Z=n[37];let he;n[38]!==e.marginMD?(he=s.jsx(Ne,{style:{padding:e.marginMD}}),n[38]=e.marginMD,n[39]=he):he=n[39];let ee;n[40]!==o||n[41]!==c?(ee=s.jsx(wa,{fetchKey:o,refetching:c}),n[40]=o,n[41]=c,n[42]=ee):ee=n[42];let ne;n[43]!==he||n[44]!==ee?(ne=s.jsx(E.Suspense,{fallback:he,children:ee}),n[43]=he,n[44]=ee,n[45]=ne):ne=n[45];let ve;n[46]!==Z||n[47]!==ne?(ve=s.jsx(We,{title:Z,status:"error",children:ne}),n[46]=Z,n[47]=ne,n[48]=ve):ve=n[48];let ae;n[49]!==a?(ae=a("webui.menu.MyResourcesInResourceGroup"),n[49]=a,n[50]=ae):ae=n[50];let te;n[51]!==e.marginMD?(te=s.jsx(Ne,{style:{padding:e.marginMD}}),n[51]=e.marginMD,n[52]=te):te=n[52];let le;n[53]!==o||n[54]!==c?(le=s.jsx(Ea,{fetchKey:o,refetching:c}),n[53]=o,n[54]=c,n[55]=le):le=n[55];let Ce;n[56]!==te||n[57]!==le?(Ce=s.jsx(E.Suspense,{fallback:te,children:le}),n[56]=te,n[57]=le,n[58]=Ce):Ce=n[58];let Te;n[59]!==ae||n[60]!==Ce?(Te=s.jsx(We,{title:ae,status:"error",children:Ce}),n[59]=ae,n[60]=Ce,n[61]=Te):Te=n[61];let se;n[62]!==a?(se=a("data.FolderStatus"),n[62]=a,n[63]=se):se=n[63];let re;n[64]!==e.marginMD?(re=s.jsx(Ne,{style:{padding:e.marginMD}}),n[64]=e.marginMD,n[65]=re):re=n[65];let ie;n[66]!==m||n[67]!==i?(ie=()=>{i({pathname:m("data"),search:new URLSearchParams({invitation:"true"}).toString()})},n[66]=m,n[67]=i,n[68]=ie):ie=n[68];let oe;n[69]!==o||n[70]!==ie?(oe=s.jsx(Kt,{fetchKey:o,onRequestBadgeClick:ie}),n[69]=o,n[70]=ie,n[71]=oe):oe=n[71];let de;n[72]!==re||n[73]!==oe?(de=s.jsx(E.Suspense,{fallback:re,children:oe}),n[72]=re,n[73]=oe,n[74]=de):de=n[74];let Ke;n[75]!==se||n[76]!==de?(Ke=s.jsx(We,{title:se,status:"error",children:de}),n[75]=se,n[76]=de,n[77]=Ke):Ke=n[77];let ue;n[78]!==a?(ue=a("data.QuotaPerStorageVolume"),n[78]=a,n[79]=ue):ue=n[79];let ce;n[80]!==e.marginMD?(ce=s.jsx(Ne,{style:{padding:e.marginMD}}),n[80]=e.marginMD,n[81]=ce):ce=n[81];let Pe;n[82]===Symbol.for("react.memo_cache_sentinel")?(Pe=s.jsx(Ct,{}),n[82]=Pe):Pe=n[82];let me;n[83]!==ce?(me=s.jsx(E.Suspense,{fallback:ce,children:Pe}),n[83]=ce,n[84]=me):me=n[84];let Le;n[85]!==ue||n[86]!==me?(Le=s.jsx(We,{title:ue,status:"error",children:me}),n[85]=ue,n[86]=me,n[87]=Le):Le=n[87];let ge;n[88]!==d?(ge=Ra(d),n[88]=d,n[89]=ge):ge=n[89];let Me;n[90]!==c||n[91]!==B||n[92]!==ge?(Me=s.jsx($a,{queryRef:B,isRefetching:c,project:ge}),n[90]=c,n[91]=B,n[92]=ge,n[93]=Me):Me=n[93];const Je=bn([{id:"mySession",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:be}},{id:"myResource",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:ve}},{id:"myResourceWithinResourceGroup",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:Te}},{id:"folderStatus",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:Ke}},{id:"quotaPerStorageVolume",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:Le}},De&&{id:"totalResourceWithinResourceGroup",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:B.TotalResourceWithinResourceGroupFragment&&s.jsx(xa,{queryRef:B.TotalResourceWithinResourceGroupFragment,refetching:c})}},nn(r,"superadmin")&&Ve&&B.AgentStatsFragment&&{id:"agentStats",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:s.jsx(E.Suspense,{fallback:s.jsx(Ne,{style:{padding:`0px ${e.marginMD}px`}}),children:s.jsx(Va,{queryRef:B.AgentStatsFragment,isRefetching:c})})}},nn(r,"superadmin")&&{id:"activeAgents",rowSpan:4,columnSpan:4,definition:{minRowSpan:3,minColumnSpan:4},data:{content:s.jsx(E.Suspense,{fallback:s.jsx(Ne,{style:{padding:`0px ${e.marginMD}px`}}),children:s.jsx(Pa,{fetchKey:o,onChangeFetchKey:()=>t()})})}},{id:"recentlyCreatedSession",rowSpan:3,columnSpan:4,definition:{minRowSpan:2,minColumnSpan:2},data:{content:Me}}]),qe=new Map;ja(Je,O=>{qe.set(O.id,O.data)}),w.forEach((O,ze)=>{qe.set(ze,{content:O})});const z=[...mn(Je,Lt),...D],we=ht({persistedLayout:Array.isArray(S)?S:[],defaultLayout:z,renderableIds:new Set(qe.keys())}),Ye=bn(mn(we,O=>{const ze=qe.get(O.id);return ze?{...O,data:ze}:void 0}));let Be;n[94]===Symbol.for("react.memo_cache_sentinel")?(Be={width:"100%"},n[94]=Be):Be=n[94];let $e;n[95]===Symbol.for("react.memo_cache_sentinel")?($e={flex:1,minWidth:0},n[95]=$e):$e=n[95];let je;n[96]!==S||n[97]!==k?(je=O=>{k(vt(mn(O.detail.items,At),Array.isArray(S)?S:[]))},n[96]=S,n[97]=k,n[98]=je):je=n[98];let pe;n[99]!==Ye||n[100]!==je?(pe=s.jsx("div",{ref:x,style:$e,children:s.jsx(Oa,{movable:!0,resizable:!0,bordered:!0,items:Ye,onItemsChange:je})}),n[99]=Ye,n[100]=je,n[101]=pe):pe=n[101];let Ae;n[102]!==C||n[103]!==y||n[104]!==K||n[105]!==N||n[106]!==v||n[107]!==q||n[108]!==k?(Ae=y&&K?s.jsx(_t,{panels:v,availableResources:C,gridEnabled:N,onRequestAdd:()=>R({open:!0}),onRequestEdit:O=>R({open:!0,panel:O}),onRemove:q,onResetLayout:()=>k([])}):null,n[102]=C,n[103]=y,n[104]=K,n[105]=N,n[106]=v,n[107]=q,n[108]=k,n[109]=Ae):Ae=n[109];let P;n[110]!==M||n[111]!==C||n[112]!==y||n[113]!==N||n[114]!==h||n[115]!==V?(P=y?s.jsx(Da,{children:s.jsx(bt,{open:h.open,initialPanel:h.panel,availableResources:C,gridEnabled:N,onRequestClose:()=>R({open:!1}),onSubmit:O=>{h.panel?V(h.panel.id,O):(M(O),requestAnimationFrame(()=>{var ze;(ze=x.current)==null||ze.scrollIntoView({block:"end",behavior:"smooth"})}))}})}):null,n[110]=M,n[111]=C,n[112]=y,n[113]=N,n[114]=h,n[115]=V,n[116]=P):P=n[116];let Oe;return n[117]!==pe||n[118]!==Ae||n[119]!==P?(Oe=s.jsxs($,{direction:"row",align:"stretch",gap:"lg",style:Be,children:[pe,Ae,P]}),n[117]=pe,n[118]=Ae,n[119]=P,n[120]=Oe):Oe=n[120],Oe};function Lt(n){return Mn(n,"data")}function At(n){return Mn(n,"data")}export{Yt as default};
//# sourceMappingURL=DashboardPage-CPvkyRhH.js.map
