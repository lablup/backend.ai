import{aB as Xn,ac as Oe,j as s,aC as Jn,aD as on,aE as Hn,aF as Yn,i as G,u as pe,aG as Cn,aH as Zn,au as yn,aI as He,aJ as ea,aK as na,N as sn,aL as Tn,aM as fn,aN as Kn,c as O,aO as Ln,l as E,aP as aa,aQ as ta,g as la,aR as sa,aS as In,aT as dn,v as ra,A as Qe,r as Je,aU as Nn,aV as Ae,aW as ia,Z as un,_ as An,a8 as Ue,aX as Sn,O as oa,ad as Rn,aY as da,aZ as ua,a_ as ca,a$ as xn,t as en,P as ma,b0 as ga,F as Pe,b1 as pa,a9 as ya,b2 as fa,b3 as Sa,H as ka,a as kn,b4 as jn,aq as Fa,b5 as _a,b6 as ba,ak as Dn,ae as ha,b7 as va,a3 as cn,s as Ca,b8 as Ta,b9 as Ka,ba as La,bb as Ia,bc as Na,bd as nn,be as Aa,X as Ra,ai as bn,bf as xa,bg as ja,am as mn,ap as Da,bh as Ma,bi as wa,bj as Ea,ar as Mn}from"./index-Dd8bt51s.js";import{A as Va,a as Pa,S as Ba,R as $a}from"./SessionCountDashboardItem-aIlwtPZe.js";import{B as Oa}from"./BAIBoard-B_ukdVyc.js";import{B as Ga}from"./BAIModelDeploymentNodes-DNHPSRJh.js";import{B as qa}from"./BAIGraphQLPropertyFilter-DFTNvxk2.js";import{Q as za}from"./QuotaPerStorageVolumePanelCard-CB7J3otI.js";import{B as gn}from"./BAIPanelItem-CPyFehRR.js";import"./AgentList-LVfJhqz5.js";import"./sessionStatusBuckets-DbmNcNIk.js";import"./BAITag-D3A3qz0g.js";import"./BAIAdminResourceGroupSelect-CCtZUjz1.js";import"./refresh-cw-DPWwh74x.js";import"./SessionDetailDrawer-7fG4IZlx.js";import"./scroll-text-DNEzU_J_.js";import"./orderBy-DeGPShMh.js";import"./FolderLink-D4qbPYJm.js";import"./zip-H1NqZ52a.js";import"./unzip-Bdpeidfv.js";import"./ScopedAuditLog-B2lTQRXM.js";import"./rotate-ccw-clock-U4w_srLr.js";import"./BAIDeploymentTagChips-Bi-0dBi-.js";import"./BooleanTag-CxaMBtbA.js";import"./usePrimaryColors-D4M9hYxu.js";const Xe=({title:n,status:e="error",children:a,style:o})=>{const{t:l}=Xn(),{token:i}=Oe.useToken();return s.jsx(Jn,{fallbackRender:()=>s.jsx("div",{"data-bai-board-item-status":e,style:{height:"100%",paddingInline:i.paddingXL,paddingBottom:i.padding,...o},children:s.jsx(on,{title:n,extra:s.jsx(Hn,{title:l("comp:BAIBoardItemErrorBoundary.UnexpectedError"),type:e})})}),children:a})},wn=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"agentNodeFilter"},e={defaultValue:null,kind:"LocalArgument",name:"isSuperAdmin"},a={defaultValue:null,kind:"LocalArgument",name:"resourceGroup"},o={defaultValue:null,kind:"LocalArgument",name:"scopeId"},l={defaultValue:null,kind:"LocalArgument",name:"skipTotalResourceWithinResourceGroup"},i=[{kind:"Variable",name:"scopeId",variableName:"scopeId"}],u={kind:"Literal",name:"first",value:0},r={kind:"Variable",name:"scope_id",variableName:"scopeId"},m={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},p=[m],t={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},K=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],F={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},T={alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},b=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[t,d,g,f],storageKey:null}],storageKey:null},m],A=[t,f,{alias:null,args:null,kind:"ScalarField",name:"available_slots",storageKey:null},k,T];return{fragment:{argumentDefinitions:[n,e,a,o,l],kind:"Fragment",metadata:null,name:"DashboardPageQuery",selections:[{args:i,kind:"FragmentSpread",name:"SessionCountDashboardItemFragment"},{args:i,kind:"FragmentSpread",name:"RecentlyCreatedSessionFragment"},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{fragment:{kind:"InlineFragment",selections:[{args:[{kind:"Variable",name:"agentNodeFilter",variableName:"agentNodeFilter"},{kind:"Variable",name:"isSuperAdmin",variableName:"isSuperAdmin"},{kind:"Variable",name:"resourceGroup",variableName:"resourceGroup"}],kind:"FragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{fragment:{kind:"InlineFragment",selections:[{args:null,kind:"FragmentSpread",name:"AgentStatsFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"AgentStatsFragment"}]}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[o,a,l,e,n],kind:"Operation",name:"DashboardPageQuery",selections:[{alias:"myInteractive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},u,r],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:p,storageKey:null},{alias:"myBatch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},u,r],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:p,storageKey:null},{alias:"myInference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},u,r],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:p,storageKey:null},{alias:"myUpload",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},u,r],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:p,storageKey:null},{alias:null,args:[{kind:"Literal",name:"filter",value:'status == "running"'},{kind:"Literal",name:"first",value:5},{kind:"Literal",name:"order",value:"-created_at"},r],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[t,d,g,f,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},c,S,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},k,{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},y,{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},t,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:K,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:K,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},y,t],storageKey:null},d,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},f,S,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},F,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},t],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[d,g,t],storageKey:null}],storageKey:null},m],storageKey:null},T,F,{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:b,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:b,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},c,{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domain_name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{condition:"isSuperAdmin",kind:"Condition",passingValue:!1,selections:[{alias:null,args:[{kind:"Literal",name:"filter",value:"schedulable == true"},{kind:"Literal",name:"limit",value:1e3},{kind:"Literal",name:"offset",value:0},{kind:"Variable",name:"scaling_group",variableName:"resourceGroup"},{kind:"Literal",name:"status",value:"ALIVE"}],concreteType:"AgentSummaryList",kind:"LinkedField",name:"agent_summary_list",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentSummary",kind:"LinkedField",name:"items",plural:!0,selections:A,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"total_count",storageKey:null}],storageKey:null}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"agentNodeFilter"},{kind:"Literal",name:"first",value:100}],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AgentNode",kind:"LinkedField",name:"node",plural:!1,selections:A,storageKey:null}],storageKey:null},m],storageKey:null}]}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{alias:null,args:null,concreteType:"AgentStats",kind:"LinkedField",name:"agentStats",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentResource",kind:"LinkedField",name:"totalResource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"free",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capacity",storageKey:null}],storageKey:null}],storageKey:null}]}]},params:{cacheID:"498b91106c06470231a1fc03564ad0a5",id:null,metadata:{},name:"DashboardPageQuery",operationKind:"query",text:`query DashboardPageQuery(
  $scopeId: ScopeField
  $resourceGroup: String
  $skipTotalResourceWithinResourceGroup: Boolean!
  $isSuperAdmin: Boolean!
  $agentNodeFilter: String!
) {
  ...SessionCountDashboardItemFragment_3vJUag
  ...RecentlyCreatedSessionFragment_3vJUag
  ...TotalResourceWithinResourceGroupFragment_2otDCj @skip(if: $skipTotalResourceWithinResourceGroup)
  ...AgentStatsFragment @include(if: $isSuperAdmin)
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
`}}})();wn.hash="c569b4f4d4f8ee32a4f369157d8a1348";/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */const Fn=Yn(!1),Ua=()=>{"use memo";const n=G.c(10),{t:e}=pe(),[a,o]=Cn(Fn),l=a?"secondary":"primary";let i;n[0]===Symbol.for("react.memo_cache_sentinel")?(i=s.jsx(Zn,{size:"1em"}),n[0]=i):i=n[0];let u;n[1]!==a||n[2]!==e?(u=e(a?"button.Close":"dashboard.Edit"),n[1]=a,n[2]=e,n[3]=u):u=n[3];let r;n[4]!==o?(r=()=>o(Qa),n[4]=o,n[5]=r):r=n[5];let m;return n[6]!==l||n[7]!==u||n[8]!==r?(m=s.jsx(yn,{variant:l,size:"sm",icon:i,label:u,onClick:r}),n[6]=l,n[7]=u,n[8]=r,n[9]=m):m=n[9],m};function Qa(n){return!n}/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */const an=[],rn={resourceTable:{rowSpan:3,columnSpan:2,definition:{minRowSpan:3,minColumnSpan:2}},resourceCount:{rowSpan:2,columnSpan:1,definition:{minRowSpan:2,minColumnSpan:1}},sessionResourceGrid:{rowSpan:4,columnSpan:4,definition:{minRowSpan:2,minColumnSpan:2}}},Wa=n=>({id:`${n.resourceType}-${ea()}`,panelType:n.panelType,descriptor:{resourceType:n.resourceType,title:n.title,filter:n.filter??null,order:n.order??null,gridView:n.panelType==="sessionResourceGrid"?n.gridView??He:null}}),Xa=n=>{"use memo";const e=G.c(10),{title:a,onEdit:o,onRemove:l}=n,{t:i}=pe();if(!na(Fn)||!o&&!l)return null;let r;e[0]!==o||e[1]!==i?(r=o?s.jsx(sn,{variant:"ghost",size:"sm",label:i("button.Edit"),tooltip:i("button.Edit"),icon:s.jsx(Tn,{size:"1em"}),onClick:o}):null,e[0]=o,e[1]=i,e[2]=r):r=e[2];let m;e[3]!==l||e[4]!==i||e[5]!==a?(m=l?s.jsx(fn,{title:i("dialog.ask.DoYouWantToDeleteSomething",{name:a}),isDanger:!0,onConfirm:l,children:s.jsx(sn,{variant:"ghost",size:"sm",label:i("button.Delete"),tooltip:i("button.Delete"),icon:s.jsx(Kn,{size:"1em"})})}):null,e[3]=l,e[4]=i,e[5]=a,e[6]=m):m=e[6];let p;return e[7]!==r||e[8]!==m?(p=s.jsxs(O,{align:"center",gap:"xxs",children:[r,m]}),e[7]=r,e[8]=m,e[9]=p):p=e[9],p},_n=n=>{"use memo";const e=G.c(30),{title:a,onEdit:o,onRemove:l,children:i}=n,{token:u}=Oe.useToken(),[r,m]=Ln(),[p,t]=E.useTransition();let d;e[0]!==u.paddingXL?(d={paddingInline:u.paddingXL,height:"100%"},e[0]=u.paddingXL,e[1]=d):d=e[1];let g;e[2]!==m?(g=()=>{t(()=>{m()})},e[2]=m,e[3]=g):g=e[3];let f;e[4]===Symbol.for("react.memo_cache_sentinel")?(f={backgroundColor:"transparent"},e[4]=f):f=e[4];let c;e[5]!==p||e[6]!==g?(c=s.jsx(aa,{size:"small",loading:p,value:"",onChange:g,type:"text",style:f}),e[5]=p,e[6]=g,e[7]=c):c=e[7];let S;e[8]!==o||e[9]!==l||e[10]!==a?(S=s.jsx(Xa,{title:a,onEdit:o,onRemove:l}),e[8]=o,e[9]=l,e[10]=a,e[11]=S):S=e[11];let k;e[12]!==c||e[13]!==S?(k=s.jsxs(O,{align:"center",gap:"xxs",children:[c,S]}),e[12]=c,e[13]=S,e[14]=k):k=e[14];let y;e[15]!==k||e[16]!==a?(y=s.jsx(on,{title:a,extra:k}),e[15]=k,e[16]=a,e[17]=y):y=e[17];let K;e[18]!==u.margin?(K={flex:1,overflowY:"auto",overflowX:"hidden",marginBottom:u.margin},e[18]=u.margin,e[19]=K):K=e[19];let F;e[20]!==i||e[21]!==r?(F=i(r),e[20]=i,e[21]=r,e[22]=F):F=e[22];let T;e[23]!==K||e[24]!==F?(T=s.jsx(O,{direction:"column",align:"stretch",style:K,children:F}),e[23]=K,e[24]=F,e[25]=T):T=e[25];let b;return e[26]!==d||e[27]!==T||e[28]!==y?(b=s.jsxs(O,{direction:"column",align:"stretch",style:d,children:[y,T]}),e[26]=d,e[27]=T,e[28]=y,e[29]=b):b=e[29],b},En=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},a={defaultValue:null,kind:"LocalArgument",name:"offset"},o={defaultValue:null,kind:"LocalArgument",name:"orderBy"},l=[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],concreteType:"VFolderConnection",kind:"LinkedField",name:"adminVfoldersV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},{alias:null,args:null,concreteType:"VFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"usageMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[n,e,a,o],kind:"Fragment",metadata:null,name:"resourceRegistryVfolderQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[n,o,e,a],kind:"Operation",name:"resourceRegistryVfolderQuery",selections:l},params:{cacheID:"0bf78ebbd78040d6acf4915a3b7744cc",id:null,metadata:{},name:"resourceRegistryVfolderQuery",operationKind:"query",text:`query resourceRegistryVfolderQuery(
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
`}}})();En.hash="f0f996cac5aac86ee5907d16f7b69a3c";const Vn=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},a={defaultValue:null,kind:"LocalArgument",name:"offset"},o={defaultValue:null,kind:"LocalArgument",name:"orderBy"},l=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],i={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null};return{fragment:{argumentDefinitions:[n,e,a,o],kind:"Fragment",metadata:null,name:"resourceRegistryDeploymentQuery",selections:[{alias:null,args:l,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[u,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[n,o,e,a],kind:"Operation",name:"resourceRegistryDeploymentQuery",selections:[{alias:null,args:l,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[u,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},r,{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[r],storageKey:null},u],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[i],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[u,{alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[u,r],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[u,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"cc812d4b4b88bdca0d559ec176b74575",id:null,metadata:{},name:"resourceRegistryDeploymentQuery",operationKind:"query",text:`query resourceRegistryDeploymentQuery(
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

fragment BAIDeploymentTagChips_metadata on ModelDeploymentMetadata {
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
    ...BAIDeploymentTagChips_metadata
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
`}}})();Vn.hash="4e7a525297dc8b70a0c7765c072ffe4b";const Pn=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"first"},a={defaultValue:null,kind:"LocalArgument",name:"offset"},o={defaultValue:null,kind:"LocalArgument",name:"order"},l={defaultValue:null,kind:"LocalArgument",name:"scopeId"},i=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"order",variableName:"order"},{kind:"Variable",name:"scope_id",variableName:"scopeId"}],u={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},c=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],S={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},k=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[r,m,p,t],storageKey:null}],storageKey:null},u];return{fragment:{argumentDefinitions:[n,e,a,o,l],kind:"Fragment",metadata:null,name:"resourceRegistrySessionQuery",selections:[{alias:null,args:i,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[u,{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[r,{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,e,a,n,o],kind:"Operation",name:"resourceRegistrySessionQuery",selections:[{alias:null,args:i,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[u,{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[r,m,p,t,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},d,g,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},f,{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},r,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:c,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:c,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},f,r],storageKey:null},m,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},t,g,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},S,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},r],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[m,p,r],storageKey:null}],storageKey:null},u],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},S,{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:k,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:k,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},d,{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domain_name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"2a9508f0350d25e09060931af3d84c09",id:null,metadata:{},name:"resourceRegistrySessionQuery",operationKind:"query",text:`query resourceRegistrySessionQuery(
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
`}}})();Pn.hash="bb92c247cff2de74130007224eef9d02";/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

 Every session field the manager's queryfilter accepts
 (`gql_legacy/session.py::_queryfilter_fieldspec`), so a custom panel can
 express any condition the backend supports instead of the three the picker
 used to offer (FR-3654).
*/const Ja=n=>n.map(e=>({label:e,value:e})),Ha=["PENDING","DEPRIORITIZING","RESERVED","SCHEDULED","PREPARING","PULLING","PREPARED","CREATING","RUNNING","RESTARTING","RUNNING_DEGRADED","PREEMPTED","RESCHEDULING","TERMINATING","TERMINATED","ERROR","CANCELLED"],Ya=["interactive","batch","inference","system"],Za=["undefined","success","failure"],et=["single-node","multi-node"],hn=(n,e,a)=>({key:n,propertyLabel:e,type:"uuid",rule:{message:a("general.InvalidUUID"),validate:o=>ta(o.toLowerCase())}}),tn=(n,e,a)=>({key:n,propertyLabel:e,type:"string",defaultOperator:"==",strictSelection:!0,options:Ja(a)}),nt=n=>[{key:"name",propertyLabel:n("session.SessionName"),type:"string"},tn("status",n("session.Status"),Ha),tn("type",n("session.SessionType"),Ya),{key:"scaling_group",propertyLabel:n("session.ResourceGroup"),type:"string"},{key:"agent_ids",propertyLabel:n("session.Agent"),type:"string"},{key:"image",propertyLabel:n("general.Image"),type:"string"},{key:"user_email",propertyLabel:n("session.launcher.OwnerEmail"),type:"string"},hn("user_id",n("credential.UserID"),n),{key:"full_name",propertyLabel:n("credential.FullName"),type:"string"},{key:"access_key",propertyLabel:n("general.AccessKey"),type:"string"},{key:"domain_name",propertyLabel:n("credential.Domain"),type:"string"},tn("cluster_mode",n("session.ClusterMode"),et),{key:"cluster_size",propertyLabel:n("session.launcher.ClusterSize"),type:"number"},{key:"priority",propertyLabel:n("session.Priority"),type:"number"},tn("result",n("session.Result"),Za),{key:"status_info",propertyLabel:n("session.StatusInfo"),type:"string"},{key:"startup_command",propertyLabel:n("session.StartupCommand"),type:"string"},hn("id",n("session.SessionId"),n),{key:"created_at",propertyLabel:n("session.CreatedAt"),type:"datetime"},{key:"starts_at",propertyLabel:n("session.StartsAt"),type:"datetime"},{key:"terminated_at",propertyLabel:n("session.TerminatedAt"),type:"datetime"}],at=n=>n?ra(n).format("lll"):"-",tt=()=>({filter:n,order:e,limit:a,offset:o})=>({filter:typeof n=="string"?void 0:n??void 0,orderBy:In(e??null),limit:a,offset:o}),Bn=n=>n?{count:n.count,nodes:dn(n.edges.map(e=>e==null?void 0:e.node))}:null,lt={key:"session",labelKey:"webui.menu.Sessions",defaultOrder:"-created_at",kind:"sessionNodes",query:Pn,getStringFilterProperties:nt,buildVariables:({filter:n,order:e,limit:a,offset:o,projectId:l})=>({scopeId:`project:${l}`,first:a,offset:o,filter:typeof n=="string"&&n?n:void 0,order:e??"-created_at"}),selectConnection:n=>{const e=n.compute_session_nodes;return e?{count:e.count??0,nodes:dn(e.edges.map(a=>a==null?void 0:a.node))}:null}},st={key:"deployment",labelKey:"webui.menu.Deployments",defaultOrder:"-createdAt",kind:"deploymentNodes",query:Vn,getFilterProperties:n=>[{key:"name",propertyLabel:n("deployment.filter.Name"),type:"string"},{key:"tags",propertyLabel:n("deployment.filter.Tags"),type:"string"},{key:"endpointUrl",propertyLabel:n("deployment.filter.EndpointUrl"),type:"string"},{key:"openToPublic",propertyLabel:n("deployment.filter.OpenToPublic"),type:"boolean"}],buildVariables:({filter:n,order:e,limit:a,offset:o,projectId:l})=>({filter:{...typeof n=="string"?{}:n??{},...l?{projectId:{equals:l}}:{}},orderBy:In(e??null),limit:a,offset:o}),selectConnection:n=>Bn(n.myDeployments)},rt={key:"vfolder",labelKey:"webui.menu.Data&Storage",defaultOrder:"-createdAt",minRole:"superadmin",query:En,getFilterProperties:n=>[{key:"name",propertyLabel:n("data.folders.Name"),type:"string"},{key:"host",propertyLabel:n("data.folders.Location"),type:"string"}],getColumns:n=>[{key:"name",dataIndex:"name",title:n("data.folders.Name"),sorter:!0,render:(e,a)=>{var o;return(o=a.metadata)==null?void 0:o.name}},{key:"host",dataIndex:"host",title:n("data.folders.Location"),sorter:!0},{key:"status",dataIndex:"status",title:n("general.Status"),sorter:!0,minWidth:140,render:(e,a)=>a.status?s.jsx(la,{label:a.status,variant:sa("vfolder",a.status)}):null},{key:"createdAt",dataIndex:"createdAt",title:n("general.CreatedAt"),sorter:!0,render:(e,a)=>{var o;return at((o=a.metadata)==null?void 0:o.createdAt)}}],buildVariables:tt(),selectConnection:n=>Bn(n.adminVfoldersV2)},ge={session:lt,deployment:st,vfolder:rt},it=Object.keys(ge),ot=n=>it.filter(e=>{const a=ge[e].minRole;return a?a==="superadmin"?n==="superadmin":n==="superadmin"||n==="admin":!0}),Ye=(n,e)=>{if(n.title)return n.title;const a=ge[n.resourceType];return a?e(a.labelKey):n.resourceType},dt=n=>{"use memo";const e=G.c(12),{descriptor:a,fetchKey:o,onEdit:l,onRemove:i}=n,{t:u}=pe(),{token:r}=Oe.useToken();let m;e[0]!==a||e[1]!==u?(m=Ye(a,u),e[0]=a,e[1]=u,e[2]=m):m=e[2];const p=m;let t;e[3]!==a||e[4]!==o||e[5]!==r.padding?(t=g=>s.jsx(O,{direction:"row",wrap:"wrap",gap:"lg",children:s.jsx(Nn,{style:{paddingBlock:r.padding},children:s.jsx(E.Suspense,{fallback:s.jsx(Ae,{}),children:s.jsx($n,{descriptor:a,fetchKey:`${o??""}:${g}`},`${a.resourceType}:${JSON.stringify(a.filter??null)}`)})})}),e[3]=a,e[4]=o,e[5]=r.padding,e[6]=t):t=e[6];let d;return e[7]!==l||e[8]!==i||e[9]!==t||e[10]!==p?(d=s.jsx(_n,{title:p,onEdit:l,onRemove:i,children:t}),e[7]=l,e[8]=i,e[9]=t,e[10]=p,e[11]=d):d=e[11],d},$n=n=>{"use memo";const e=G.c(16),{descriptor:a,fetchKey:o}=n,{t:l}=pe(),i=Qe(),u=ge[a.resourceType];let r;e[0]!==u||e[1]!==i.id||e[2]!==a.filter||e[3]!==a.order?(r=u.buildVariables({filter:a.filter??void 0,order:a.order??u.defaultOrder,limit:1,offset:0,projectId:i.id??""}),e[0]=u,e[1]=i.id,e[2]=a.filter,e[3]=a.order,e[4]=r):r=e[4];const m=r,p=E.useDeferredValue(m),t=E.useDeferredValue(o);let d;e[5]!==t?(d={fetchPolicy:"store-and-network",fetchKey:t},e[5]=t,e[6]=d):d=e[6];const g=Je.useLazyLoadQuery(u.query,p,d);let f;e[7]!==u||e[8]!==g?(f=u.selectConnection(g),e[7]=u,e[8]=g,e[9]=f):f=e[9];const c=f;let S;e[10]!==u.labelKey||e[11]!==l?(S=l(u.labelKey),e[10]=u.labelKey,e[11]=l,e[12]=S):S=e[12];const k=(c==null?void 0:c.count)??0;let y;return e[13]!==S||e[14]!==k?(y=s.jsx(ia,{title:S,current:k,progressMode:"hidden"}),e[13]=S,e[14]=k,e[15]=y):y=e[15],y},ut=["name","status","replicaSummary","model","createdAt"],On=n=>{"use memo";const e=G.c(36),{descriptor:a,fetchKey:o,onChangeOrder:l,disableNavigation:i}=n,u=Qe(),r=un(),m=An(),p=ge.deployment,[t,d]=Ue("table_column_overrides.DashboardDeploymentPanel");let g;e[0]===Symbol.for("react.memo_cache_sentinel")?(g={current:1,pageSize:10},e[0]=g):g=e[0];const{baiPaginationOption:f,tablePaginationOption:c,setTablePaginationOption:S}=Sn(g),k=a.order??p.defaultOrder;let y;e[1]!==f.limit||e[2]!==f.offset||e[3]!==u.id||e[4]!==a.filter||e[5]!==k?(y=p.buildVariables({filter:a.filter??void 0,order:k,limit:f.limit,offset:f.offset,projectId:u.id??""}),e[1]=f.limit,e[2]=f.offset,e[3]=u.id,e[4]=a.filter,e[5]=k,e[6]=y):y=e[6];const K=y,F=E.useDeferredValue(K),T=E.useDeferredValue(o);let b;e[7]!==T?(b={fetchPolicy:"store-and-network",fetchKey:T},e[7]=T,e[8]=b):b=e[8];const _=Je.useLazyLoadQuery(p.query,F,b).myDeployments;let v;e[9]!==(_==null?void 0:_.edges)?(v=dn(_==null?void 0:_.edges.map(ct)),e[9]=_==null?void 0:_.edges,e[10]=v):v=e[10];const j=v,R=!l;let L;e[11]!==l?(L=l?M=>l(M??void 0):void 0,e[11]=l,e[12]=L):L=e[12];const x=F!==K||T!==o;let I;e[13]!==m||e[14]!==i||e[15]!==r?(I=M=>M.filter(mt).map(V=>V.key==="name"&&!i?{...V,onTitleClick:z=>{r(`${m("deployments")}/${oa(z.id)}`)}}:V),e[13]=m,e[14]=i,e[15]=r,e[16]=I):I=e[16];const h=(_==null?void 0:_.count)??0;let C;e[17]!==S?(C=(M,V)=>{S({current:M,pageSize:V})},e[17]=S,e[18]=C):C=e[18];let N;e[19]!==C||e[20]!==h||e[21]!==c.current||e[22]!==c.pageSize?(N={pageSize:c.pageSize,current:c.current,total:h,onChange:C},e[19]=C,e[20]=h,e[21]=c.current,e[22]=c.pageSize,e[23]=N):N=e[23];let D;e[24]!==t||e[25]!==d?(D={columnOverrides:t,onColumnOverridesChange:d},e[24]=t,e[25]=d,e[26]=D):D=e[26];let w;return e[27]!==j||e[28]!==k||e[29]!==N||e[30]!==D||e[31]!==R||e[32]!==L||e[33]!==x||e[34]!==I?(w=s.jsx(Ga,{deploymentsFrgmt:j,order:k,disableSorter:R,onChangeOrder:L,loading:x,customizeColumns:I,pagination:N,tableSettings:D}),e[27]=j,e[28]=k,e[29]=N,e[30]=D,e[31]=R,e[32]=L,e[33]=x,e[34]=I,e[35]=w):w=e[35],w};function ct(n){return n==null?void 0:n.node}function mt(n){return ut.includes(String(n.key))}const Gn=n=>{"use memo";const e=G.c(36),{descriptor:a,fetchKey:o,onChangeOrder:l,disableSessionDetail:i}=n,u=Qe(),r=un(),m=Rn(),p=ge.session,[t,d]=Ue("table_column_overrides.DashboardSessionPanel");let g;e[0]===Symbol.for("react.memo_cache_sentinel")?(g={current:1,pageSize:10},e[0]=g):g=e[0];const{baiPaginationOption:f,tablePaginationOption:c,setTablePaginationOption:S}=Sn(g),k=a.order??p.defaultOrder;let y;e[1]!==f.limit||e[2]!==f.offset||e[3]!==u.id||e[4]!==a.filter||e[5]!==k?(y=p.buildVariables({filter:a.filter??void 0,order:k,limit:f.limit,offset:f.offset,projectId:u.id??""}),e[1]=f.limit,e[2]=f.offset,e[3]=u.id,e[4]=a.filter,e[5]=k,e[6]=y):y=e[6];const K=y,F=E.useDeferredValue(K),T=E.useDeferredValue(o);let b;e[7]!==T?(b={fetchPolicy:"store-and-network",fetchKey:T},e[7]=T,e[8]=b):b=e[8];const _=Je.useLazyLoadQuery(p.query,F,b).compute_session_nodes;let v;e[9]!==(_==null?void 0:_.edges)?(v=dn(_==null?void 0:_.edges.map(gt)),e[9]=_==null?void 0:_.edges,e[10]=v):v=e[10];const j=v,R=!l;let L;e[11]!==l?(L=l?M=>l(M??void 0):void 0,e[11]=l,e[12]=L):L=e[12];const x=F!==K||T!==o;let I;e[13]!==i||e[14]!==m||e[15]!==r?(I=i?void 0:M=>{const V=new URLSearchParams(m.search);V.set("sessionDetail",M.row_id),r({pathname:m.pathname,hash:m.hash,search:V.toString()},{state:{sessionDetailDrawerFrgmt:M,createdAt:new Date().toISOString()}})},e[13]=i,e[14]=m,e[15]=r,e[16]=I):I=e[16];const h=(_==null?void 0:_.count)??0;let C;e[17]!==S?(C=(M,V)=>{S({current:M,pageSize:V})},e[17]=S,e[18]=C):C=e[18];let N;e[19]!==C||e[20]!==h||e[21]!==c.current||e[22]!==c.pageSize?(N={pageSize:c.pageSize,current:c.current,total:h,onChange:C},e[19]=C,e[20]=h,e[21]=c.current,e[22]=c.pageSize,e[23]=N):N=e[23];let D;e[24]!==t||e[25]!==d?(D={columnOverrides:t,onColumnOverridesChange:d},e[24]=t,e[25]=d,e[26]=D):D=e[26];let w;return e[27]!==k||e[28]!==j||e[29]!==N||e[30]!==D||e[31]!==R||e[32]!==L||e[33]!==x||e[34]!==I?(w=s.jsx(da,{sessionsFrgmt:j,order:k,disableSorter:R,onChangeOrder:L,loading:x,onClickSessionName:I,pagination:N,tableSettings:D}),e[27]=k,e[28]=j,e[29]=N,e[30]=D,e[31]=R,e[32]=L,e[33]=x,e[34]=I,e[35]=w):w=e[35],w};function gt(n){return n==null?void 0:n.node}const pt=n=>{"use memo";const e=G.c(11),{descriptor:a,fetchKey:o,onEdit:l,onRemove:i}=n,{t:u}=pe();let r;e[0]!==a||e[1]!==u?(r=Ye(a,u),e[0]=a,e[1]=u,e[2]=r):r=e[2];const m=r;let p;e[3]!==a||e[4]!==o?(p=d=>{var g,f;return s.jsx(E.Suspense,{fallback:s.jsx(Ae,{}),children:((g=ge[a.resourceType])==null?void 0:g.kind)==="deploymentNodes"?s.jsx(On,{descriptor:a,fetchKey:`${o??""}:${d}`},`${a.resourceType}:${JSON.stringify(a.filter??null)}:${a.order??""}`):((f=ge[a.resourceType])==null?void 0:f.kind)==="sessionNodes"?s.jsx(Gn,{descriptor:a,fetchKey:`${o??""}:${d}`},`${a.resourceType}:${JSON.stringify(a.filter??null)}:${a.order??""}`):s.jsx(qn,{descriptor:a,fetchKey:`${o??""}:${d}`},`${a.resourceType}:${JSON.stringify(a.filter??null)}:${a.order??""}`)})},e[3]=a,e[4]=o,e[5]=p):p=e[5];let t;return e[6]!==l||e[7]!==i||e[8]!==p||e[9]!==m?(t=s.jsx(_n,{title:m,onEdit:l,onRemove:i,children:p}),e[6]=l,e[7]=i,e[8]=p,e[9]=m,e[10]=t):t=e[10],t},qn=n=>{"use memo";var I;const e=G.c(46),{descriptor:a,fetchKey:o,onChangeOrder:l}=n,{t:i}=pe(),u=Qe(),r=ge[a.resourceType];let m;e[0]===Symbol.for("react.memo_cache_sentinel")?(m={current:1,pageSize:10},e[0]=m):m=e[0];const{baiPaginationOption:p,tablePaginationOption:t,setTablePaginationOption:d}=Sn(m),g=a.order??r.defaultOrder;let f;e[1]!==p.limit||e[2]!==p.offset||e[3]!==r||e[4]!==u.id||e[5]!==a.filter||e[6]!==g?(f=r.buildVariables({filter:a.filter??void 0,order:g,limit:p.limit,offset:p.offset,projectId:u.id??""}),e[1]=p.limit,e[2]=p.offset,e[3]=r,e[4]=u.id,e[5]=a.filter,e[6]=g,e[7]=f):f=e[7];const c=f,S=E.useDeferredValue(c),k=E.useDeferredValue(o);let y;e[8]!==k?(y={fetchPolicy:"store-and-network",fetchKey:k},e[8]=k,e[9]=y):y=e[9];const K=Je.useLazyLoadQuery(r.query,S,y);let F,T,b,A,_,v;if(e[10]!==r||e[11]!==K||e[12]!==k||e[13]!==S||e[14]!==o||e[15]!==l||e[16]!==i||e[17]!==c){if(T=r.selectConnection(K),b=S!==c||k!==o,e[24]!==r||e[25]!==l||e[26]!==i){const h=((I=r.getColumns)==null?void 0:I.call(r,i))??[];F=ua,A="id",_=l?[...h]:h.map(yt),e[24]=r,e[25]=l,e[26]=i,e[27]=F,e[28]=A,e[29]=_}else F=e[27],A=e[28],_=e[29];v=[...(T==null?void 0:T.nodes)??[]],e[10]=r,e[11]=K,e[12]=k,e[13]=S,e[14]=o,e[15]=l,e[16]=i,e[17]=c,e[18]=F,e[19]=T,e[20]=b,e[21]=A,e[22]=_,e[23]=v}else F=e[18],T=e[19],b=e[20],A=e[21],_=e[22],v=e[23];const j=(T==null?void 0:T.count)??0;let R;e[30]!==d?(R=(h,C)=>d({current:h,pageSize:C}),e[30]=d,e[31]=R):R=e[31];let L;e[32]!==j||e[33]!==R||e[34]!==t.current||e[35]!==t.pageSize?(L={current:t.current,pageSize:t.pageSize,total:j,onChange:R},e[32]=j,e[33]=R,e[34]=t.current,e[35]=t.pageSize,e[36]=L):L=e[36];let x;return e[37]!==F||e[38]!==b||e[39]!==l||e[40]!==g||e[41]!==A||e[42]!==_||e[43]!==v||e[44]!==L?(x=s.jsx(F,{rowKey:A,columns:_,dataSource:v,loading:b,order:g,onChangeOrder:l,pagination:L}),e[37]=F,e[38]=b,e[39]=l,e[40]=g,e[41]=A,e[42]=_,e[43]=v,e[44]=L,e[45]=x):x=e[45],x};function yt(n){return{...n,sorter:!1}}const ft=n=>{"use memo";const e=G.c(11),{descriptor:a,fetchKey:o,onEdit:l,onRemove:i}=n,{t:u}=pe();let r;e[0]!==a||e[1]!==u?(r=Ye(a,u),e[0]=a,e[1]=u,e[2]=r):r=e[2];const m=r;let p;e[3]!==a||e[4]!==o?(p=d=>s.jsx(E.Suspense,{fallback:s.jsx(Ae,{}),children:s.jsx(zn,{descriptor:a,fetchKey:`${o??""}:${d}`},`${JSON.stringify(a.filter??null)}:${a.order??""}`)}),e[3]=a,e[4]=o,e[5]=p):p=e[5];let t;return e[6]!==l||e[7]!==i||e[8]!==p||e[9]!==m?(t=s.jsx(_n,{title:m,onEdit:l,onRemove:i,children:p}),e[6]=l,e[7]=i,e[8]=p,e[9]=m,e[10]=t):t=e[10],t},zn=n=>{"use memo";const e=G.c(12),{descriptor:a,fetchKey:o,onChangeViewParams:l,disableSessionDetail:i}=n,u=Qe(),r=un(),m=Rn(),p=typeof a.filter=="string"?a.filter:null,t=a.order??null,d=u.id??null,g=o??"",f=a.gridView??He;let c;e[0]!==i||e[1]!==m||e[2]!==r?(c=i?void 0:k=>{const y=new URLSearchParams(m.search);y.set("sessionDetail",k),r({pathname:m.pathname,hash:m.hash,search:y.toString()})},e[0]=i,e[1]=m,e[2]=r,e[3]=c):c=e[3];let S;return e[4]!==l||e[5]!==p||e[6]!==t||e[7]!==d||e[8]!==g||e[9]!==f||e[10]!==c?(S=s.jsx(ca,{filter:p,order:t,projectId:d,fetchKey:g,viewParams:f,onChangeViewParams:l,onClickSession:c}),e[4]=l,e[5]=p,e[6]=t,e[7]=d,e[8]=g,e[9]=f,e[10]=c,e[11]=S):S=e[11],S};/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */const Un={resourceTable:pt,resourceCount:dt,sessionResourceGrid:ft},Qn={resourceTable:"dashboard.panelModal.Table",resourceCount:"dashboard.panelModal.Count",sessionResourceGrid:"session.resourceGrid.GridView"},vn=(n,{gridEnabled:e,forcePanelType:a})=>{const o=["resourceTable","resourceCount"];return n==="session"&&(e||a==="sessionResourceGrid")&&o.push("sessionResourceGrid"),o},St=(n,{gridEnabled:e})=>n.panelType==="sessionResourceGrid"&&!e?"resourceTable":n.panelType,ln=n=>Array.isArray(n)?n.filter(e=>{if(!e||typeof e!="object")return!1;const a=e;return typeof a.id=="string"&&a.panelType in Un&&!!a.descriptor&&a.descriptor.resourceType in ge&&(a.descriptor.title===void 0||typeof a.descriptor.title=="string")}):[],kt=n=>{"use memo";const e=G.c(43);let a;e[0]!==n?(a=n===void 0?{}:n,e[0]=n,e[1]=a):a=e[1];const{enabled:o,fetchKey:l,onRequestEdit:i}=a,u=o===void 0?!0:o,{t:r}=pe(),m=xn(),[p,t]=Ue("custom_dashboard_panels"),[,d]=Ue("dashboard_board_items"),[g]=Ue("experimental_session_resource_grid");let f,c,S,k,y,K,F;if(e[2]!==u||e[3]!==l||e[4]!==g||e[5]!==i||e[6]!==d||e[7]!==t||e[8]!==p||e[9]!==r||e[10]!==m){k=u?p?ln(p):[...an]:[];let _;e[18]!==m?(c=ot(m),_=new Set(c),e[18]=m,e[19]=c,e[20]=_):(c=e[19],_=e[20]);const v=_;let j;e[21]!==t?(j=h=>{t(C=>[...ln(C??an),Wa(h)])},e[21]=t,e[22]=j):j=e[22],f=j,F=(h,C)=>{const N=k.find(D=>D.id===h);if(N&&N.panelType!==C.panelType){const D=rn[C.panelType]??rn.resourceTable;d(w=>Array.isArray(w)?w.map(M=>M.id===h?{id:h,...D}:M):w)}t(D=>ln(D??an).map(w=>w.id===h?{...w,panelType:C.panelType,descriptor:{resourceType:C.resourceType,title:C.title,filter:C.filter??null,order:C.order??null,gridView:C.panelType==="sessionResourceGrid"?C.gridView??He:null}}:w))};let R;e[23]!==d||e[24]!==t?(R=h=>{t(C=>ln(C??an).filter(N=>N.id!==h)),d(C=>Array.isArray(C)?C.filter(N=>N.id!==h):C)},e[23]=d,e[24]=t,e[25]=R):R=e[25],y=R;let L;e[26]!==v?(L=h=>v.has(h.descriptor.resourceType),e[26]=v,e[27]=L):L=e[27];const x=k.filter(L);S=x.map(Ft);let I;e[28]!==l||e[29]!==g||e[30]!==i||e[31]!==y||e[32]!==r?(I=h=>{const C=Un[St(h,{gridEnabled:!!g})],N=s.jsx(Xe,{title:Ye(h.descriptor,r),status:"error",children:C?s.jsx(C,{descriptor:h.descriptor,fetchKey:l,onEdit:i?()=>i(h):void 0,onRemove:()=>y(h.id)}):null},`${h.panelType}:${JSON.stringify(h.descriptor)}`);return[h.id,N]},e[28]=l,e[29]=g,e[30]=i,e[31]=y,e[32]=r,e[33]=I):I=e[33],K=new Map(x.map(I)),e[2]=u,e[3]=l,e[4]=g,e[5]=i,e[6]=d,e[7]=t,e[8]=p,e[9]=r,e[10]=m,e[11]=f,e[12]=c,e[13]=S,e[14]=k,e[15]=y,e[16]=K,e[17]=F}else f=e[11],c=e[12],S=e[13],k=e[14],y=e[15],K=e[16],F=e[17];const T=K,b=!!g;let A;return e[34]!==f||e[35]!==c||e[36]!==T||e[37]!==S||e[38]!==k||e[39]!==y||e[40]!==b||e[41]!==F?(A={panels:k,availableResources:c,gridEnabled:b,customDefaultLayout:S,customContentById:T,addPanel:f,updatePanel:F,removePanel:y},e[34]=f,e[35]=c,e[36]=T,e[37]=S,e[38]=k,e[39]=y,e[40]=b,e[41]=F,e[42]=A):A=e[42],A};function Ft(n){return{id:n.id,...rn[n.panelType]??rn.resourceTable}}const _t=n=>{"use memo";const e=G.c(47),{panels:a,availableResources:o,gridEnabled:l,onRequestAdd:i,onRequestEdit:u,onRemove:r,onResetLayout:m}=n,p=l===void 0?!1:l,{t}=pe(),{token:d}=Oe.useToken();let g;e[0]!==o?(g=new Set(o),e[0]=o,e[1]=g):g=e[1];const f=g,c=`1px solid ${d.colorBorder}`;let S;e[2]!==c||e[3]!==d.paddingLG?(S={width:320,flexShrink:0,paddingLeft:d.paddingLG,borderLeft:c,overflow:"auto"},e[2]=c,e[3]=d.paddingLG,e[4]=S):S=e[4];let k;e[5]!==t?(k=t("dashboard.editSider.Title"),e[5]=t,e[6]=k):k=e[6];let y;e[7]!==k?(y=s.jsx(en,{strong:!0,children:k}),e[7]=k,e[8]=y):y=e[8];let K;e[9]===Symbol.for("react.memo_cache_sentinel")?(K=s.jsx(ma,{size:"1em"}),e[9]=K):K=e[9];let F;e[10]!==t?(F=t("button.Add"),e[10]=t,e[11]=F):F=e[11];let T;e[12]!==i||e[13]!==F?(T=s.jsx(yn,{variant:"primary",size:"sm",icon:K,label:F,onClick:i}),e[12]=i,e[13]=F,e[14]=T):T=e[14];let b;e[15]!==y||e[16]!==T?(b=s.jsxs(O,{direction:"row",justify:"between",align:"center",gap:"sm",children:[y,T]}),e[15]=y,e[16]=T,e[17]=b):b=e[17];let A;e[18]!==f||e[19]!==p||e[20]!==r||e[21]!==u||e[22]!==a||e[23]!==t||e[24]!==d.colorBorderSecondary||e[25]!==d.fontSizeSM||e[26]!==d.paddingXS?(A=a.length===0?s.jsx(en,{type:"secondary",children:t("dashboard.editSider.Empty")}):s.jsx(O,{direction:"column",align:"stretch",children:a.map(h=>{var V;const C=Ye(h.descriptor,t),N=t(((V=ge[h.descriptor.resourceType])==null?void 0:V.labelKey)??h.descriptor.resourceType),D=f.has(h.descriptor.resourceType),w=h.panelType==="sessionResourceGrid"&&!p,M=[t(w?"dashboard.editSider.GridDisabled":Qn[h.panelType]??h.panelType),h.descriptor.title?N:void 0,D?void 0:t("dashboard.editSider.RequiresSuperadmin")].filter(Boolean).join(" · ");return s.jsxs(O,{direction:"row",justify:"between",align:"center",gap:"sm",style:{paddingBlock:d.paddingXS,borderBottom:`1px solid ${d.colorBorderSecondary}`},children:[s.jsxs(O,{direction:"column",align:"stretch",style:{flex:1,minWidth:0},children:[s.jsx(en,{ellipsis:!0,children:C}),s.jsx(en,{type:"secondary",ellipsis:{tooltip:M},style:{fontSize:d.fontSizeSM},children:M})]}),s.jsxs(O,{direction:"row",align:"center",gap:"xxs",children:[s.jsx(sn,{variant:"ghost",size:"sm",label:t("button.Edit"),tooltip:t("button.Edit"),icon:s.jsx(Tn,{size:"1em"}),onClick:()=>u(h)}),s.jsx(fn,{title:t("dialog.ask.DoYouWantToDeleteSomething",{name:C}),isDanger:!0,onConfirm:()=>r(h.id),children:s.jsx(sn,{variant:"ghost",size:"sm",label:t("button.Delete"),tooltip:t("button.Delete"),icon:s.jsx(Kn,{size:"1em"})})})]})]},h.id)})}),e[18]=f,e[19]=p,e[20]=r,e[21]=u,e[22]=a,e[23]=t,e[24]=d.colorBorderSecondary,e[25]=d.fontSizeSM,e[26]=d.paddingXS,e[27]=A):A=e[27];let _;e[28]!==t?(_=t("dashboard.editSider.ResetLayout"),e[28]=t,e[29]=_):_=e[29];let v;e[30]!==t?(v=t("dashboard.editSider.ResetLayoutDescription"),e[30]=t,e[31]=v):v=e[31];let j;e[32]===Symbol.for("react.memo_cache_sentinel")?(j=s.jsx(ga,{size:"1em"}),e[32]=j):j=e[32];let R;e[33]!==t?(R=t("dashboard.editSider.ResetLayout"),e[33]=t,e[34]=R):R=e[34];let L;e[35]!==R?(L=s.jsx(yn,{variant:"secondary",size:"sm",icon:j,label:R}),e[35]=R,e[36]=L):L=e[36];let x;e[37]!==m||e[38]!==_||e[39]!==v||e[40]!==L?(x=s.jsx(fn,{title:_,description:v,isDanger:!0,onConfirm:m,children:L}),e[37]=m,e[38]=_,e[39]=v,e[40]=L,e[41]=x):x=e[41];let I;return e[42]!==b||e[43]!==A||e[44]!==x||e[45]!==S?(I=s.jsxs(O,{direction:"column",align:"stretch",gap:"md",style:S,children:[b,A,x]}),e[42]=b,e[43]=A,e[44]=x,e[45]=S,e[46]=I):I=e[46],I},bt=n=>{"use memo";var qe,Ze;const e=G.c(180),{open:a,onRequestClose:o,initialPanel:l,availableResources:i,gridEnabled:u,onSubmit:r,afterClose:m}=n,p=u===void 0?!1:u,{t}=pe(),{token:d}=Oe.useToken(),[g]=Pe.useForm(),f=i[0],c=(l==null?void 0:l.descriptor.resourceType)??f;let S;e[0]!==i||e[1]!==l||e[2]!==c?(S=l&&!i.includes(c)?[...i,c]:i,e[0]=i,e[1]=l,e[2]=c,e[3]=S):S=e[3];const k=S,[y,K]=E.useState((l==null?void 0:l.descriptor.order)??null),[F,T]=E.useState((l==null?void 0:l.descriptor.gridView)??He),b=Pe.useWatch("resourceType",g)??c,A=Pe.useWatch("panelType",g)??(l==null?void 0:l.panelType)??"resourceTable",_=Pe.useWatch("filter",g)??void 0,v=ge[b];let j,R,L,x,I,h,C,N,D,w,M,V,z,Ee,Be,ke,ye,fe,Re,Q,xe,W,je,Fe,B,_e,Se,q;if(e[4]!==m||e[5]!==g||e[6]!==p||e[7]!==F||e[8]!==l||e[9]!==c||e[10]!==o||e[11]!==r||e[12]!==a||e[13]!==y||e[14]!==b||e[15]!==t){const U=vn(b,{gridEnabled:p,forcePanelType:l==null?void 0:l.panelType});let Ie;e[44]!==g||e[45]!==F||e[46]!==o||e[47]!==r||e[48]!==y?(Ie=async()=>{var P;let $;try{$=await g.validateFields()}catch{return}r({panelType:$.panelType,resourceType:$.resourceType,title:((P=$.title)==null?void 0:P.trim())||void 0,filter:$.filter??null,order:y,gridView:$.panelType==="sessionResourceGrid"?F:null}),o()},e[44]=g,e[45]=F,e[46]=o,e[47]=r,e[48]=y,e[49]=Ie):Ie=e[49];const We=Ie;I=ya,Ee=a,Be=!0,ke="min(960px, 95vw)",e[50]!==l||e[51]!==t?(ye=t(l?"dashboard.panelModal.EditPanel":"dashboard.panelModal.AddPanel"),e[50]=l,e[51]=t,e[52]=ye):ye=e[52],e[53]!==l||e[54]!==t?(fe=t(l?"button.Save":"button.Add"),e[53]=l,e[54]=t,e[55]=fe):fe=e[55],Re=We,Q=o,xe=m,x=Pe,w=g,M="vertical";const $e=(l==null?void 0:l.panelType)??"resourceTable",Me=l==null?void 0:l.descriptor.title,we=(l==null?void 0:l.descriptor.filter)??void 0;e[56]!==c||e[57]!==$e||e[58]!==Me||e[59]!==we?(V={panelType:$e,resourceType:c,title:Me,filter:we},e[56]=c,e[57]=$e,e[58]=Me,e[59]=we,e[60]=V):V=e[60],e[61]!==g||e[62]!==p||e[63]!==(l==null?void 0:l.panelType)?(z=$=>{$.resourceType&&(g.setFieldsValue({filter:void 0}),K(null),T(He),vn($.resourceType,{gridEnabled:p,forcePanelType:l==null?void 0:l.panelType}).includes(g.getFieldValue("panelType"))||g.setFieldsValue({panelType:"resourceTable"}))},e[61]=g,e[62]=p,e[63]=l==null?void 0:l.panelType,e[64]=z):z=e[64],L=O,h="row",C="start",N="md",D="wrap",R=Pe.Item,Fe="panelType",e[65]!==t?(B=t("dashboard.panelModal.PanelType"),e[65]=t,e[66]=B):B=e[66],_e=!0;let me;e[67]!==t?(me=t("dashboard.panelModal.PanelTypeRequired"),e[67]=t,e[68]=me):me=e[68],e[69]!==me?(Se=[{required:!0,message:me}],e[69]=me,e[70]=Se):Se=e[70],e[71]===Symbol.for("react.memo_cache_sentinel")?(q={flexShrink:0},e[71]=q):q=e[71],j=fa,e[72]!==t?(W=t("dashboard.panelModal.PanelType"),e[72]=t,e[73]=W):W=e[73];let Ne;e[74]!==t?(Ne=$=>({value:$,label:t(Qn[$])}),e[74]=t,e[75]=Ne):Ne=e[75],je=U.map(Ne),e[4]=m,e[5]=g,e[6]=p,e[7]=F,e[8]=l,e[9]=c,e[10]=o,e[11]=r,e[12]=a,e[13]=y,e[14]=b,e[15]=t,e[16]=j,e[17]=R,e[18]=L,e[19]=x,e[20]=I,e[21]=h,e[22]=C,e[23]=N,e[24]=D,e[25]=w,e[26]=M,e[27]=V,e[28]=z,e[29]=Ee,e[30]=Be,e[31]=ke,e[32]=ye,e[33]=fe,e[34]=Re,e[35]=Q,e[36]=xe,e[37]=W,e[38]=je,e[39]=Fe,e[40]=B,e[41]=_e,e[42]=Se,e[43]=q}else j=e[16],R=e[17],L=e[18],x=e[19],I=e[20],h=e[21],C=e[22],N=e[23],D=e[24],w=e[25],M=e[26],V=e[27],z=e[28],Ee=e[29],Be=e[30],ke=e[31],ye=e[32],fe=e[33],Re=e[34],Q=e[35],xe=e[36],W=e[37],je=e[38],Fe=e[39],B=e[40],_e=e[41],Se=e[42],q=e[43];let X;e[76]!==j||e[77]!==W||e[78]!==je?(X=s.jsx(j,{label:W,options:je}),e[76]=j,e[77]=W,e[78]=je,e[79]=X):X=e[79];let J;e[80]!==R||e[81]!==X||e[82]!==Fe||e[83]!==B||e[84]!==_e||e[85]!==Se||e[86]!==q?(J=s.jsx(R,{name:Fe,label:B,required:_e,rules:Se,style:q,children:X}),e[80]=R,e[81]=X,e[82]=Fe,e[83]=B,e[84]=_e,e[85]=Se,e[86]=q,e[87]=J):J=e[87];let be;e[88]!==t?(be=t("dashboard.panelModal.DataSource"),e[88]=t,e[89]=be):be=e[89];let H;e[90]!==t?(H=t("dashboard.panelModal.DataSourceRequired"),e[90]=t,e[91]=H):H=e[91];let Y;e[92]!==H?(Y=[{required:!0,message:H}],e[92]=H,e[93]=Y):Y=e[93];let he;e[94]===Symbol.for("react.memo_cache_sentinel")?(he={flex:1,minWidth:180},e[94]=he):he=e[94];let Z;e[95]!==t?(Z=t("dashboard.panelModal.DataSource"),e[95]=t,e[96]=Z):Z=e[96];let ve;if(e[97]!==k||e[98]!==t){let U;e[100]!==t?(U=Ie=>({value:Ie,label:t(ge[Ie].labelKey)}),e[100]=t,e[101]=U):U=e[101],ve=k.map(U),e[97]=k,e[98]=t,e[99]=ve}else ve=e[99];let ee;e[102]!==Z||e[103]!==ve?(ee=s.jsx(Sa,{label:Z,options:ve}),e[102]=Z,e[103]=ve,e[104]=ee):ee=e[104];let ne;e[105]!==be||e[106]!==Y||e[107]!==ee?(ne=s.jsx(Pe.Item,{name:"resourceType",label:be,required:!0,rules:Y,style:he,children:ee}),e[105]=be,e[106]=Y,e[107]=ee,e[108]=ne):ne=e[108];let ae;e[109]!==t?(ae=t("dashboard.panelModal.TitleOptional"),e[109]=t,e[110]=ae):ae=e[110];let te;e[111]!==t?(te=t("dashboard.panelModal.TitleDescription"),e[111]=t,e[112]=te):te=e[112];let Ve;e[113]===Symbol.for("react.memo_cache_sentinel")?(Ve={flex:1,minWidth:180},e[113]=Ve):Ve=e[113];let le;e[114]!==t?(le=t("dashboard.panelModal.TitleOptional"),e[114]=t,e[115]=le):le=e[115];let se;e[116]!==v.labelKey||e[117]!==t?(se=t(v.labelKey),e[116]=v.labelKey,e[117]=t,e[118]=se):se=e[118];let re;e[119]!==le||e[120]!==se?(re=s.jsx(ka,{label:le,placeholder:se,hasClear:!0}),e[119]=le,e[120]=se,e[121]=re):re=e[121];let ie;e[122]!==ae||e[123]!==te||e[124]!==re?(ie=s.jsx(Pe.Item,{name:"title",label:ae,extra:te,style:Ve,children:re}),e[122]=ae,e[123]=te,e[124]=re,e[125]=ie):ie=e[125];let oe;e[126]!==L||e[127]!==h||e[128]!==C||e[129]!==N||e[130]!==D||e[131]!==J||e[132]!==ne||e[133]!==ie?(oe=s.jsxs(L,{direction:h,align:C,gap:N,wrap:D,children:[J,ne,ie]}),e[126]=L,e[127]=h,e[128]=C,e[129]=N,e[130]=D,e[131]=J,e[132]=ne,e[133]=ie,e[134]=oe):oe=e[134];let Ce;e[135]!==t?(Ce=t("dashboard.panelModal.Condition"),e[135]=t,e[136]=Ce):Ce=e[136];let de;e[137]!==v||e[138]!==t?(de=v.kind==="sessionNodes"?s.jsx(pa,{filterProperties:((qe=v.getStringFilterProperties)==null?void 0:qe.call(v,t))??[]}):s.jsx(qa,{style:{width:"100%"},filterProperties:[...((Ze=v.getFilterProperties)==null?void 0:Ze.call(v,t))??[]]}),e[137]=v,e[138]=t,e[139]=de):de=e[139];let ue;e[140]!==Ce||e[141]!==de?(ue=s.jsx(Pe.Item,{name:"filter",label:Ce,children:de}),e[140]=Ce,e[141]=de,e[142]=ue):ue=e[142];let Te;e[143]!==x||e[144]!==w||e[145]!==M||e[146]!==V||e[147]!==z||e[148]!==oe||e[149]!==ue?(Te=s.jsxs(x,{form:w,layout:M,initialValues:V,onValuesChange:z,children:[oe,ue]}),e[143]=x,e[144]=w,e[145]=M,e[146]=V,e[147]=z,e[148]=oe,e[149]=ue,e[150]=Te):Te=e[150];const De=`1px solid ${d.colorBorderSecondary}`;let Ke;e[151]!==De||e[152]!==d.borderRadius||e[153]!==d.paddingSM?(Ke={border:De,borderRadius:d.borderRadius,padding:d.paddingSM,maxHeight:360,overflow:"auto"},e[151]=De,e[152]=d.borderRadius,e[153]=d.paddingSM,e[154]=Ke):Ke=e[154];let ce;e[155]!==v.kind||e[156]!==v.labelKey||e[157]!==_||e[158]!==F||e[159]!==a||e[160]!==y||e[161]!==A||e[162]!==b||e[163]!==t?(ce=a?s.jsx(Xe,{title:t(v.labelKey),status:"error",children:s.jsx(E.Suspense,{fallback:s.jsx(Ae,{}),children:A==="resourceCount"?s.jsx(O,{align:"center",justify:"center",children:s.jsx($n,{descriptor:{resourceType:b,filter:_??null,order:y}},`${b}:${JSON.stringify(_??null)}`)}):A==="sessionResourceGrid"?s.jsx(zn,{descriptor:{resourceType:b,filter:_??null,order:y,gridView:F},onChangeViewParams:T,disableSessionDetail:!0},`${b}:${JSON.stringify(_??null)}`):v.kind==="deploymentNodes"?s.jsx(On,{descriptor:{resourceType:b,filter:_??null,order:y},onChangeOrder:U=>K(U??null),disableNavigation:!0},`${b}:${JSON.stringify(_??null)}`):v.kind==="sessionNodes"?s.jsx(Gn,{descriptor:{resourceType:b,filter:_??null,order:y},onChangeOrder:U=>K(U??null),disableSessionDetail:!0},`${b}:${JSON.stringify(_??null)}`):s.jsx(qn,{descriptor:{resourceType:b,filter:_??null,order:y},onChangeOrder:U=>K(U??null)},`${b}:${JSON.stringify(_??null)}`)})},`${A}:${b}:${JSON.stringify(_??null)}`):null,e[155]=v.kind,e[156]=v.labelKey,e[157]=_,e[158]=F,e[159]=a,e[160]=y,e[161]=A,e[162]=b,e[163]=t,e[164]=ce):ce=e[164];let Le;e[165]!==Ke||e[166]!==ce?(Le=s.jsx(O,{direction:"column",align:"stretch",gap:"xs",children:s.jsx("div",{style:Ke,children:ce})}),e[165]=Ke,e[166]=ce,e[167]=Le):Le=e[167];let Ge;return e[168]!==I||e[169]!==Ee||e[170]!==Be||e[171]!==ke||e[172]!==ye||e[173]!==fe||e[174]!==Re||e[175]!==Q||e[176]!==xe||e[177]!==Te||e[178]!==Le?(Ge=s.jsxs(I,{open:Ee,destroyOnHidden:Be,width:ke,title:ye,okText:fe,onOk:Re,onCancel:Q,afterClose:xe,children:[Te,Le]}),e[168]=I,e[169]=Ee,e[170]=Be,e[171]=ke,e[172]=ye,e[173]=fe,e[174]=Re,e[175]=Q,e[176]=xe,e[177]=Te,e[178]=Le,e[179]=Ge):Ge=e[179],Ge};/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */const ht=({persistedLayout:n,defaultLayout:e,renderableIds:a})=>{const o=new Set(n.map(l=>l.id));return[...n.filter(l=>a.has(l.id)),...e.filter(l=>!o.has(l.id))]},vt=(n,e)=>{const a=new Set(n.map(l=>l.id)),o=[...n];return e.forEach((l,i)=>{a.has(l.id)||o.splice(Math.min(i,o.length),0,l)}),o},Ct=()=>{"use memo";const n=G.c(21),{t:e}=pe(),{token:a}=Oe.useToken(),o=kn();let l;n[0]===Symbol.for("react.memo_cache_sentinel")?(l=["vhostInfo"],n[0]=l):l=n[0];let i;n[1]!==o?(i={queryKey:l,queryFn:()=>o.vfolder.list_hosts()},n[1]=o,n[2]=i):i=n[2];const{data:u}=jn(i);let r;n[3]!==(u==null?void 0:u.volume_info)?(r=Fa(_a((u==null?void 0:u.volume_info)??{}),Tt),n[3]=u==null?void 0:u.volume_info,n[4]=r):r=n[4];const m=r;let p;n[5]!==m?(p=m?{id:m[0],...m[1]}:void 0,n[5]=m,n[6]=p):p=n[6];const t=p;let d;n[7]!==a.padding||n[8]!==a.paddingXL?(d={paddingInline:a.paddingXL,paddingBottom:a.padding},n[7]=a.padding,n[8]=a.paddingXL,n[9]=d):d=n[9];let g;n[10]!==e?(g=e("data.QuotaPerStorageVolume"),n[10]=e,n[11]=g):g=n[11];let f;n[12]!==g?(f=s.jsx(on,{title:g}),n[12]=g,n[13]=f):f=n[13];let c;n[14]!==t||n[15]!==e?(c=t?s.jsx(za,{defaultVolumeInfo:t}):s.jsx(ba,{title:e("storageHost.QuotaDoesNotSupported"),isCompact:!0}),n[14]=t,n[15]=e,n[16]=c):c=n[16];let S;return n[17]!==d||n[18]!==f||n[19]!==c?(S=s.jsxs(O,{direction:"column",align:"stretch",style:d,children:[f,c]}),n[17]=d,n[18]=f,n[19]=c,n[20]=S):S=n[20],S};function Tt(n){const[,e]=n;return Dn(e==null?void 0:e.capabilities,"quota")}const Wn=(function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"name"}],e={alias:null,args:null,kind:"ScalarField",name:"max_vfolder_count",storageKey:null},a=[e],o=[{kind:"Variable",name:"name",variableName:"name"}],l=[e,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}];return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"StorageStatusPanelCardQuery",selections:[{alias:null,args:null,concreteType:"UserResourcePolicy",kind:"LinkedField",name:"user_resource_policy",plural:!1,selections:a,storageKey:null},{alias:null,args:o,concreteType:"ProjectResourcePolicy",kind:"LinkedField",name:"project_resource_policy",plural:!1,selections:a,storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"StorageStatusPanelCardQuery",selections:[{alias:null,args:null,concreteType:"UserResourcePolicy",kind:"LinkedField",name:"user_resource_policy",plural:!1,selections:l,storageKey:null},{alias:null,args:o,concreteType:"ProjectResourcePolicy",kind:"LinkedField",name:"project_resource_policy",plural:!1,selections:l,storageKey:null}]},params:{cacheID:"6a4458681167a38a930cf05173cf0d90",id:null,metadata:{},name:"StorageStatusPanelCardQuery",operationKind:"query",text:`query StorageStatusPanelCardQuery(
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
`}}})();Wn.hash="33191e01e0635b3635f28c7383463c39";const pn=90,Kt=({fetchKey:n,onRequestBadgeClick:e,style:a,...o})=>{const{t:l}=pe(),{token:i}=Oe.useToken(),u=kn(),r=Qe();if(!r.name)throw new Error("Project name is required for StorageStatusPanelCard");if(!r.id)throw new Error("Project ID is required for StorageStatusPanelCard");const m=E.useDeferredValue(n),[p,{updateInvitations:t}]=ha(),d=p.length;va(()=>{t()},[n]);const g=F=>Dn(["delete-ongoing","delete-complete","delete-error"],F),{data:f}=jn({queryKey:["vfolders",{deferredFetchKey:m,id:r.id}],queryFn:()=>{if(!(r!=null&&r.id))throw new Error("Project ID is required for StorageStatusPanelCard");return u.vfolder.list(r.id)}}),c=f==null?void 0:f.filter(F=>F.is_owner&&F.ownership_type==="user"&&!g(F.status)).length,S=f==null?void 0:f.filter(F=>F.ownership_type==="group"&&!g(F.status)).length,k=f==null?void 0:f.filter(F=>!F.is_owner&&F.ownership_type==="user"&&!g(F.status)).length,{user_resource_policy:y,project_resource_policy:K}=Je.useLazyLoadQuery(Wn,{name:r.name});return s.jsxs(O,{direction:"column",align:"stretch",style:{paddingInline:i.paddingXL,paddingBottom:i.padding,...a},...o,children:[s.jsx(on,{title:l("data.FolderStatus")}),s.jsxs(Nn,{rowGap:i.marginXL,columnGap:i.marginXL,dividerColor:i.colorBorder,dividerInset:i.marginXS,dividerWidth:i.lineWidth,children:[s.jsx(gn,{title:l("data.MyFolders"),value:c,unit:y!=null&&y.max_vfolder_count?`/ ${y==null?void 0:y.max_vfolder_count}`:void 0,style:{maxWidth:pn},color:i.colorText}),s.jsx(gn,{title:l("data.ProjectFolders"),value:S,unit:K!=null&&K.max_vfolder_count?`/ ${K==null?void 0:K.max_vfolder_count}`:void 0,style:{maxWidth:pn},color:i.colorText}),s.jsx(gn,{title:d>0?s.jsx("a",{onClick:()=>{e==null||e()},children:s.jsx(Ca,{content:l("data.InvitedFoldersTooltip",{count:d}),placement:"above",alignment:"end",children:s.jsx(Ta,{count:`+${d}`,variant:"error",offset:[-i.sizeXS,-i.sizeXS],style:{zIndex:50},title:l("data.InvitedFoldersTooltip",{count:d}),children:s.jsx(cn,{size:"lg",children:l("data.InvitedFolders")})})})}):s.jsx(cn,{size:"lg",children:l("data.InvitedFolders")}),value:s.jsx(cn,{size:"4xl",children:k}),style:{maxWidth:pn}})]})]})},Yt=()=>{"use memo";const n=G.c(121),{token:e}=Oe.useToken(),{t:a}=pe(),o=Qe(),l=Ka(),i=xn(),u=kn(),r=un(),m=An(),[p,t]=Ln(),d=E.useDeferredValue(p),[g,f]=E.useTransition(),c=g||p!==d,[S,k]=Ue("dashboard_board_items"),[y]=Ue("experimental_custom_dashboard_panels"),[K,F]=Cn(Fn),T=La(Ia);let b,A;n[0]!==y||n[1]!==T||n[2]!==F?(b=()=>{if(y)return T(s.jsx(Ua,{})),()=>{T(null),F(!1)}},A=[y,T,F],n[0]=y,n[1]=T,n[2]=F,n[3]=b,n[4]=A):(b=n[3],A=n[4]),E.useEffect(b,A);let _;n[5]===Symbol.for("react.memo_cache_sentinel")?(_={open:!1},n[5]=_):_=n[5];const[v,j]=E.useState(_),R=E.useRef(null),L=!!y;let x;n[6]===Symbol.for("react.memo_cache_sentinel")?(x=P=>j({open:!0,panel:P}),n[6]=x):x=n[6];let I;n[7]!==d||n[8]!==L?(I={enabled:L,fetchKey:d,onRequestEdit:x},n[7]=d,n[8]=L,n[9]=I):I=n[9];const{panels:h,availableResources:C,gridEnabled:N,customDefaultLayout:D,customContentById:w,addPanel:M,updatePanel:V,removePanel:z}=kt(I),Ee=Na(),Be=u.supports("agent-stats");let ke;n[10]===Symbol.for("react.memo_cache_sentinel")?(ke=wn,n[10]=ke):ke=n[10];const ye=`project:${o.id}`,fe=l||"default",Re=!Ee;let Q;n[11]!==i?(Q=nn(i,"superadmin"),n[11]=i,n[12]=Q):Q=n[12];const xe=`schedulable == true & status == "ALIVE" & scaling_group == "${l}"`;let W;n[13]!==Q||n[14]!==xe||n[15]!==ye||n[16]!==fe||n[17]!==Re?(W={scopeId:ye,resourceGroup:fe,skipTotalResourceWithinResourceGroup:Re,isSuperAdmin:Q,agentNodeFilter:xe},n[13]=Q,n[14]=xe,n[15]=ye,n[16]=fe,n[17]=Re,n[18]=W):W=n[18];const je=d===Ma?"store-and-network":"network-only";let Fe;n[19]!==d||n[20]!==je?(Fe={fetchPolicy:je,fetchKey:d},n[19]=d,n[20]=je,n[21]=Fe):Fe=n[21];const B=Je.useLazyLoadQuery(ke,W,Fe);let _e;n[22]!==t?(_e=()=>{f(()=>{t()})},n[22]=t,n[23]=_e):_e=n[23],Aa(_e,15e3);const Se=`0px ${e.marginMD}px`;let q;n[24]!==Se?(q=s.jsx(Ae,{style:{padding:Se}}),n[24]=Se,n[25]=q):q=n[25];let X;n[26]!==a||n[27]!==i?(X=nn(i,"superadmin")?a("session.ActiveSessions"):a("session.MySessions"),n[26]=a,n[27]=i,n[28]=X):X=n[28];let J;n[29]!==c||n[30]!==B||n[31]!==X?(J=s.jsx(Ba,{queryRef:B,isRefetching:c,title:X}),n[29]=c,n[30]=B,n[31]=X,n[32]=J):J=n[32];let be;n[33]!==q||n[34]!==J?(be=s.jsx(E.Suspense,{fallback:q,children:J}),n[33]=q,n[34]=J,n[35]=be):be=n[35];let H;n[36]!==a?(H=a("webui.menu.MyResources"),n[36]=a,n[37]=H):H=n[37];let Y;n[38]!==e.marginMD?(Y=s.jsx(Ae,{style:{padding:e.marginMD}}),n[38]=e.marginMD,n[39]=Y):Y=n[39];let he;n[40]!==d||n[41]!==c?(he=s.jsx(wa,{fetchKey:d,refetching:c}),n[40]=d,n[41]=c,n[42]=he):he=n[42];let Z;n[43]!==Y||n[44]!==he?(Z=s.jsx(E.Suspense,{fallback:Y,children:he}),n[43]=Y,n[44]=he,n[45]=Z):Z=n[45];let ve;n[46]!==H||n[47]!==Z?(ve=s.jsx(Xe,{title:H,status:"error",children:Z}),n[46]=H,n[47]=Z,n[48]=ve):ve=n[48];let ee;n[49]!==a?(ee=a("webui.menu.MyResourcesInResourceGroup"),n[49]=a,n[50]=ee):ee=n[50];let ne;n[51]!==e.marginMD?(ne=s.jsx(Ae,{style:{padding:e.marginMD}}),n[51]=e.marginMD,n[52]=ne):ne=n[52];let ae;n[53]!==d||n[54]!==c?(ae=s.jsx(Ea,{fetchKey:d,refetching:c}),n[53]=d,n[54]=c,n[55]=ae):ae=n[55];let te;n[56]!==ne||n[57]!==ae?(te=s.jsx(E.Suspense,{fallback:ne,children:ae}),n[56]=ne,n[57]=ae,n[58]=te):te=n[58];let Ve;n[59]!==ee||n[60]!==te?(Ve=s.jsx(Xe,{title:ee,status:"error",children:te}),n[59]=ee,n[60]=te,n[61]=Ve):Ve=n[61];let le;n[62]!==a?(le=a("data.FolderStatus"),n[62]=a,n[63]=le):le=n[63];let se;n[64]!==e.marginMD?(se=s.jsx(Ae,{style:{padding:e.marginMD}}),n[64]=e.marginMD,n[65]=se):se=n[65];let re;n[66]!==m||n[67]!==r?(re=()=>{r({pathname:m("data"),search:new URLSearchParams({invitation:"true"}).toString()})},n[66]=m,n[67]=r,n[68]=re):re=n[68];let ie;n[69]!==d||n[70]!==re?(ie=s.jsx(Kt,{fetchKey:d,onRequestBadgeClick:re}),n[69]=d,n[70]=re,n[71]=ie):ie=n[71];let oe;n[72]!==se||n[73]!==ie?(oe=s.jsx(E.Suspense,{fallback:se,children:ie}),n[72]=se,n[73]=ie,n[74]=oe):oe=n[74];let Ce;n[75]!==le||n[76]!==oe?(Ce=s.jsx(Xe,{title:le,status:"error",children:oe}),n[75]=le,n[76]=oe,n[77]=Ce):Ce=n[77];let de;n[78]!==a?(de=a("data.QuotaPerStorageVolume"),n[78]=a,n[79]=de):de=n[79];let ue;n[80]!==e.marginMD?(ue=s.jsx(Ae,{style:{padding:e.marginMD}}),n[80]=e.marginMD,n[81]=ue):ue=n[81];let Te;n[82]===Symbol.for("react.memo_cache_sentinel")?(Te=s.jsx(Ct,{}),n[82]=Te):Te=n[82];let De;n[83]!==ue?(De=s.jsx(E.Suspense,{fallback:ue,children:Te}),n[83]=ue,n[84]=De):De=n[84];let Ke;n[85]!==de||n[86]!==De?(Ke=s.jsx(Xe,{title:de,status:"error",children:De}),n[85]=de,n[86]=De,n[87]=Ke):Ke=n[87];let ce;n[88]!==o?(ce=Ra(o),n[88]=o,n[89]=ce):ce=n[89];let Le;n[90]!==c||n[91]!==B||n[92]!==ce?(Le=s.jsx($a,{queryRef:B,isRefetching:c,project:ce}),n[90]=c,n[91]=B,n[92]=ce,n[93]=Le):Le=n[93];const Ge=bn([{id:"mySession",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:be}},{id:"myResource",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:ve}},{id:"myResourceWithinResourceGroup",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:Ve}},{id:"folderStatus",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:Ce}},{id:"quotaPerStorageVolume",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:Ke}},Ee&&{id:"totalResourceWithinResourceGroup",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:B.TotalResourceWithinResourceGroupFragment&&s.jsx(xa,{queryRef:B.TotalResourceWithinResourceGroupFragment,refetching:c})}},nn(i,"superadmin")&&Be&&B.AgentStatsFragment&&{id:"agentStats",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:s.jsx(E.Suspense,{fallback:s.jsx(Ae,{style:{padding:`0px ${e.marginMD}px`}}),children:s.jsx(Va,{queryRef:B.AgentStatsFragment,isRefetching:c})})}},nn(i,"superadmin")&&{id:"activeAgents",rowSpan:4,columnSpan:4,definition:{minRowSpan:3,minColumnSpan:4},data:{content:s.jsx(E.Suspense,{fallback:s.jsx(Ae,{style:{padding:`0px ${e.marginMD}px`}}),children:s.jsx(Pa,{fetchKey:d,onChangeFetchKey:()=>t()})})}},{id:"recentlyCreatedSession",rowSpan:3,columnSpan:4,definition:{minRowSpan:2,minColumnSpan:2},data:{content:Le}}]),qe=new Map;ja(Ge,P=>{qe.set(P.id,P.data)}),w.forEach((P,ze)=>{qe.set(ze,{content:P})});const Ze=[...mn(Ge,Lt),...D],U=ht({persistedLayout:Array.isArray(S)?S:[],defaultLayout:Ze,renderableIds:new Set(qe.keys())}),Ie=bn(mn(U,P=>{const ze=qe.get(P.id);return ze?{...P,data:ze}:void 0}));let We;n[94]===Symbol.for("react.memo_cache_sentinel")?(We={width:"100%"},n[94]=We):We=n[94];let $e;n[95]===Symbol.for("react.memo_cache_sentinel")?($e={flex:1,minWidth:0},n[95]=$e):$e=n[95];let Me;n[96]!==S||n[97]!==k?(Me=P=>{k(vt(mn(P.detail.items,It),Array.isArray(S)?S:[]))},n[96]=S,n[97]=k,n[98]=Me):Me=n[98];let we;n[99]!==Ie||n[100]!==Me?(we=s.jsx("div",{ref:R,style:$e,children:s.jsx(Oa,{movable:!0,resizable:!0,bordered:!0,items:Ie,onItemsChange:Me})}),n[99]=Ie,n[100]=Me,n[101]=we):we=n[101];let me;n[102]!==C||n[103]!==y||n[104]!==K||n[105]!==N||n[106]!==h||n[107]!==z||n[108]!==k?(me=y&&K?s.jsx(_t,{panels:h,availableResources:C,gridEnabled:N,onRequestAdd:()=>j({open:!0}),onRequestEdit:P=>j({open:!0,panel:P}),onRemove:z,onResetLayout:()=>k([])}):null,n[102]=C,n[103]=y,n[104]=K,n[105]=N,n[106]=h,n[107]=z,n[108]=k,n[109]=me):me=n[109];let Ne;n[110]!==M||n[111]!==C||n[112]!==y||n[113]!==N||n[114]!==v||n[115]!==V?(Ne=y?s.jsx(Da,{children:s.jsx(bt,{open:v.open,initialPanel:v.panel,availableResources:C,gridEnabled:N,onRequestClose:()=>j({open:!1}),onSubmit:P=>{v.panel?V(v.panel.id,P):(M(P),requestAnimationFrame(()=>{var ze;(ze=R.current)==null||ze.scrollIntoView({block:"end",behavior:"smooth"})}))}})}):null,n[110]=M,n[111]=C,n[112]=y,n[113]=N,n[114]=v,n[115]=V,n[116]=Ne):Ne=n[116];let $;return n[117]!==we||n[118]!==me||n[119]!==Ne?($=s.jsxs(O,{direction:"row",align:"stretch",gap:"lg",style:We,children:[we,me,Ne]}),n[117]=we,n[118]=me,n[119]=Ne,n[120]=$):$=n[120],$};function Lt(n){return Mn(n,"data")}function It(n){return Mn(n,"data")}export{Yt as default};
//# sourceMappingURL=DashboardPage-DHOOlw-U.js.map
