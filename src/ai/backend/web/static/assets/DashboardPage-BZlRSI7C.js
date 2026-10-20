import{az as el,ab as Ge,j as s,aA as nl,aB as cn,aC as ll,aD as al,i as U,u as Fe,aE as Ln,aF as tl,at as Fn,aG as en,aH as sl,aI as rl,J as dn,aJ as An,aK as bn,aL as In,c as G,aM as Nn,l as V,aN as il,aO as ol,aP as dl,aQ as ul,aR as cl,aS as Rn,aT as mn,t as ml,z as Je,r as Xe,aU as xn,aV as Ee,aW as gl,X as gn,Y as jn,a7 as We,aX as _n,K as pl,ac as En,aY as yl,aZ as fl,a_ as Sl,a$ as Dn,s as an,P as kl,b0 as Fl,_ as $e,b1 as bl,b2 as _l,a8 as hl,b3 as vl,b4 as Cl,E as Tl,a as wn,b5 as Vn,ap as Kl,b6 as Ll,b7 as Al,b8 as Il,ai as Pn,ad as Nl,b9 as Rl,a2 as pn,q as xl,ba as jl,bb as yn,bc as El,bd as Dl,be as wl,bf as Vl,bg as tn,bh as Pl,V as Ml,ag as Cn,bi as Bl,bj as $l,ak as fn,an as Ol,bk as ql,bl as Gl,bm as Ul,aq as Mn}from"./index-4XAoWQdC.js";import{A as zl,a as Ql,S as Wl,R as Jl}from"./SessionCountDashboardItem-Eed1RIE8.js";import{B as Yl}from"./BAIModelDeploymentNodes-BTdMt6K7.js";import{B as Sn}from"./BAIPanelItem-BPMoUeR-.js";import{B as Hl}from"./BAIBoard-Dgbrp-hb.js";import"./AgentList-DPpqhdr5.js";import"./sessionStatusBuckets-DOsrVVEE.js";import"./BAIAdminResourceGroupSelect-BQBUYcyd.js";import"./refresh-cw-CMIe8XML.js";import"./SessionDetailDrawer-r93Udkje.js";import"./scroll-text-CMSbKmDU.js";import"./orderBy-DR_M0o9Z.js";import"./FolderLink-B13SaUe_.js";import"./ScopedAuditLog-BTAaHqWC.js";import"./rotate-ccw-clock-Bp9ZfyAh.js";import"./BAIBooleanToken-D4JLjIi_.js";import"./BAIDeploymentTagTokens-DaVJhxci.js";const He=({title:n,status:e="error",children:l,style:o})=>{const{t}=el(),{token:r}=Ge();return s.jsx(nl,{fallbackRender:()=>s.jsx("div",{"data-bai-board-item-status":e,style:{height:"100%",paddingInline:r("--spacing-8"),paddingBottom:r("--spacing-4"),...o},children:s.jsx(cn,{title:n,extra:s.jsx(ll,{title:t("comp:BAIBoardItemErrorBoundary.UnexpectedError"),type:e})})}),children:l})},Bn=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"agentNodeFilter"},e={defaultValue:null,kind:"LocalArgument",name:"aliveAgentFilter"},l={defaultValue:null,kind:"LocalArgument",name:"isSuperAdmin"},o={defaultValue:null,kind:"LocalArgument",name:"resourceGroup"},t={defaultValue:null,kind:"LocalArgument",name:"schedulableAgentFilter"},r={defaultValue:null,kind:"LocalArgument",name:"scopeId"},d={defaultValue:null,kind:"LocalArgument",name:"skipTotalResourceWithinResourceGroup"},i=[{kind:"Variable",name:"scopeId",variableName:"scopeId"}],y={kind:"Literal",name:"first",value:0},m={kind:"Variable",name:"scope_id",variableName:"scopeId"},a={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},c=[a],g={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},F={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},f=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],T={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},K={alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},_=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[g,u,p,F],storageKey:null}],storageKey:null},a],A=[g,F,{alias:null,args:null,kind:"ScalarField",name:"available_slots",storageKey:null},b,K],S={kind:"Literal",name:"first",value:1};return{fragment:{argumentDefinitions:[n,e,l,o,t,r,d],kind:"Fragment",metadata:null,name:"DashboardPageQuery",selections:[{args:i,kind:"FragmentSpread",name:"SessionCountDashboardItemFragment"},{args:i,kind:"FragmentSpread",name:"RecentlyCreatedSessionFragment"},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{fragment:{kind:"InlineFragment",selections:[{args:[{kind:"Variable",name:"agentNodeFilter",variableName:"agentNodeFilter"},{kind:"Variable",name:"isSuperAdmin",variableName:"isSuperAdmin"},{kind:"Variable",name:"resourceGroup",variableName:"resourceGroup"}],kind:"FragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{fragment:{kind:"InlineFragment",selections:[{args:[{kind:"Variable",name:"aliveAgentFilter",variableName:"aliveAgentFilter"},{kind:"Variable",name:"schedulableAgentFilter",variableName:"schedulableAgentFilter"}],kind:"FragmentSpread",name:"AgentStatsFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"AgentStatsFragment"}]}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[r,o,d,l,n,e,t],kind:"Operation",name:"DashboardPageQuery",selections:[{alias:"myInteractive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},y,m],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:c,storageKey:null},{alias:"myBatch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},y,m],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:c,storageKey:null},{alias:"myInference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},y,m],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:c,storageKey:null},{alias:"myUpload",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},y,m],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:c,storageKey:null},{alias:null,args:[{kind:"Literal",name:"filter",value:'status == "running"'},{kind:"Literal",name:"first",value:5},{kind:"Literal",name:"order",value:"-created_at"},m],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[g,u,p,F,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},k,{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[g,F,{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:f,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:f,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},T,g],storageKey:null},u,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},k,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},b,{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},T,{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},g],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[u,p,g],storageKey:null}],storageKey:null},a],storageKey:null},K,{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:_,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:_,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domain_name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{condition:"isSuperAdmin",kind:"Condition",passingValue:!1,selections:[{alias:null,args:[{kind:"Literal",name:"filter",value:"schedulable == true"},{kind:"Literal",name:"limit",value:100},{kind:"Literal",name:"offset",value:0},{kind:"Variable",name:"scaling_group",variableName:"resourceGroup"},{kind:"Literal",name:"status",value:"ALIVE"}],concreteType:"AgentSummaryList",kind:"LinkedField",name:"agent_summary_list",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentSummary",kind:"LinkedField",name:"items",plural:!0,selections:A,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"total_count",storageKey:null}],storageKey:null}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"agentNodeFilter"},{kind:"Literal",name:"first",value:100}],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AgentNode",kind:"LinkedField",name:"node",plural:!1,selections:A,storageKey:null}],storageKey:null},a],storageKey:null}]}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{alias:null,args:null,concreteType:"AgentStats",kind:"LinkedField",name:"agentStats",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentResource",kind:"LinkedField",name:"totalResource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"free",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capacity",storageKey:null}],storageKey:null}],storageKey:null},{alias:"aliveAgents",args:[{kind:"Variable",name:"filter",variableName:"aliveAgentFilter"},S],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:c,storageKey:null},{alias:"schedulableAgents",args:[{kind:"Variable",name:"filter",variableName:"schedulableAgentFilter"},S],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:c,storageKey:null}]}]},params:{cacheID:"44181f9bb689eb2995c27456bbacde58",id:null,metadata:{},name:"DashboardPageQuery",operationKind:"query",text:`query DashboardPageQuery(
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
  agentStats {
    totalResource {
      free
      used
      capacity
    }
  }
  aliveAgents: agent_nodes(filter: $aliveAgentFilter, first: 1) {
    count
  }
  schedulableAgents: agent_nodes(filter: $schedulableAgentFilter, first: 1) {
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
  priority
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
  vfolder_nodes {
    edges {
      node {
        ...FolderLink_vfolderNode
        id
      }
    }
  }
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
  vfolder_nodes {
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
  owner {
    email
    id
  }
  resource_opts
  status
  vfolder_mounts
  vfolder_nodes {
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
  idle_checks
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
  priority
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
  owner {
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
  queue_position
  cluster_size
  kernel_nodes {
    edges {
      node {
        id
        status
      }
    }
  }
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
  agent_summary_list(limit: 100, offset: 0, status: "ALIVE", scaling_group: $resourceGroup, filter: "schedulable == true") @skip(if: $isSuperAdmin) {
    items {
      id
      status
      available_slots
      occupied_slots
      scaling_group
    }
    total_count
  }
  agent_nodes(filter: $agentNodeFilter, first: 100) @include(if: $isSuperAdmin) {
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
`}}})();Bn.hash="010e4f1c56e89b2d778a8e76ae4aa39c";/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */const hn=al(!1),Xl=()=>{"use memo";const n=U.c(10),{t:e}=Fe(),[l,o]=Ln(hn),t=l?"secondary":"primary";let r;n[0]===Symbol.for("react.memo_cache_sentinel")?(r=s.jsx(tl,{size:"1em"}),n[0]=r):r=n[0];let d;n[1]!==l||n[2]!==e?(d=e(l?"button.Close":"dashboard.Edit"),n[1]=l,n[2]=e,n[3]=d):d=n[3];let i;n[4]!==o?(i=()=>o(Zl),n[4]=o,n[5]=i):i=n[5];let y;return n[6]!==t||n[7]!==d||n[8]!==i?(y=s.jsx(Fn,{variant:t,size:"sm",icon:r,label:d,onClick:i}),n[6]=t,n[7]=d,n[8]=i,n[9]=y):y=n[9],y};function Zl(n){return!n}/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */const sn=[],un={resourceTable:{rowSpan:3,columnSpan:2,definition:{minRowSpan:3,minColumnSpan:2}},resourceCount:{rowSpan:2,columnSpan:1,definition:{minRowSpan:2,minColumnSpan:1}},sessionResourceGrid:{rowSpan:4,columnSpan:4,definition:{minRowSpan:2,minColumnSpan:2}}},ea=n=>({id:`${n.resourceType}-${sl()}`,panelType:n.panelType,descriptor:{resourceType:n.resourceType,title:n.title,filter:n.filter??null,order:n.order??null,gridView:n.panelType==="sessionResourceGrid"?n.gridView??en:null}}),na=n=>{"use memo";const e=U.c(10),{title:l,onEdit:o,onRemove:t}=n,{t:r}=Fe();if(!rl(hn)||!o&&!t)return null;let i;e[0]!==o||e[1]!==r?(i=o?s.jsx(dn,{variant:"ghost",size:"sm",label:r("button.Edit"),tooltip:r("button.Edit"),icon:s.jsx(An,{size:"1em"}),onClick:o}):null,e[0]=o,e[1]=r,e[2]=i):i=e[2];let y;e[3]!==t||e[4]!==r||e[5]!==l?(y=t?s.jsx(bn,{title:r("dialog.ask.DoYouWantToDeleteSomething",{name:l}),isDanger:!0,onConfirm:t,children:s.jsx(dn,{variant:"ghost",size:"sm",label:r("button.Delete"),tooltip:r("button.Delete"),icon:s.jsx(In,{size:"1em"})})}):null,e[3]=t,e[4]=r,e[5]=l,e[6]=y):y=e[6];let m;return e[7]!==i||e[8]!==y?(m=s.jsxs(G,{align:"center",gap:"xxs",children:[i,y]}),e[7]=i,e[8]=y,e[9]=m):m=e[9],m},vn=n=>{"use memo";const e=U.c(34),{title:l,onEdit:o,onRemove:t,children:r}=n,{token:d}=Ge(),[i,y]=Nn(),[m,a]=V.useTransition();let c;e[0]!==d?(c=d("--spacing-8"),e[0]=d,e[1]=c):c=e[1];let g;e[2]!==c?(g={paddingInline:c,height:"100%"},e[2]=c,e[3]=g):g=e[3];let u;e[4]!==y?(u=()=>{a(()=>{y()})},e[4]=y,e[5]=u):u=e[5];let p;e[6]===Symbol.for("react.memo_cache_sentinel")?(p={backgroundColor:"transparent"},e[6]=p):p=e[6];let F;e[7]!==m||e[8]!==u?(F=s.jsx(il,{size:"small",loading:m,value:"",onChange:u,type:"text",style:p}),e[7]=m,e[8]=u,e[9]=F):F=e[9];let k;e[10]!==o||e[11]!==t||e[12]!==l?(k=s.jsx(na,{title:l,onEdit:o,onRemove:t}),e[10]=o,e[11]=t,e[12]=l,e[13]=k):k=e[13];let f;e[14]!==F||e[15]!==k?(f=s.jsxs(G,{align:"center",gap:"xxs",children:[F,k]}),e[14]=F,e[15]=k,e[16]=f):f=e[16];let T;e[17]!==f||e[18]!==l?(T=s.jsx(cn,{title:l,extra:f}),e[17]=f,e[18]=l,e[19]=T):T=e[19];let b;e[20]!==d?(b=d("--spacing-4"),e[20]=d,e[21]=b):b=e[21];let K;e[22]!==b?(K={flex:1,overflowY:"auto",overflowX:"hidden",marginBottom:b},e[22]=b,e[23]=K):K=e[23];let _;e[24]!==r||e[25]!==i?(_=r(i),e[24]=r,e[25]=i,e[26]=_):_=e[26];let A;e[27]!==K||e[28]!==_?(A=s.jsx(G,{direction:"column",align:"stretch",style:K,children:_}),e[27]=K,e[28]=_,e[29]=A):A=e[29];let S;return e[30]!==A||e[31]!==g||e[32]!==T?(S=s.jsxs(G,{direction:"column",align:"stretch",style:g,children:[T,A]}),e[30]=A,e[31]=g,e[32]=T,e[33]=S):S=e[33],S},$n=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},l={defaultValue:null,kind:"LocalArgument",name:"offset"},o={defaultValue:null,kind:"LocalArgument",name:"orderBy"},t=[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],concreteType:"VFolderConnection",kind:"LinkedField",name:"adminVfoldersV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},{alias:null,args:null,concreteType:"VFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"usageMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[n,e,l,o],kind:"Fragment",metadata:null,name:"resourceRegistryVfolderQuery",selections:t,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[n,o,e,l],kind:"Operation",name:"resourceRegistryVfolderQuery",selections:t},params:{cacheID:"0bf78ebbd78040d6acf4915a3b7744cc",id:null,metadata:{},name:"resourceRegistryVfolderQuery",operationKind:"query",text:`query resourceRegistryVfolderQuery(
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
`}}})();$n.hash="f0f996cac5aac86ee5907d16f7b69a3c";const On=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},l={defaultValue:null,kind:"LocalArgument",name:"offset"},o={defaultValue:null,kind:"LocalArgument",name:"orderBy"},t=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],r={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null};return{fragment:{argumentDefinitions:[n,e,l,o],kind:"Fragment",metadata:null,name:"resourceRegistryDeploymentQuery",selections:[{alias:null,args:t,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[r,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[d,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[n,o,e,l],kind:"Operation",name:"resourceRegistryDeploymentQuery",selections:[{alias:null,args:t,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[r,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[d,{alias:null,args:null,kind:"ScalarField",name:"entityId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},i,{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[i],storageKey:null},d],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[r],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[d,{alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[d,i],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:[{kind:"Literal",name:"limit",value:100}],concreteType:"EntityLabelConnection",kind:"LinkedField",name:"entityLabels",plural:!1,selections:[{alias:null,args:null,concreteType:"EntityLabelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"EntityLabel",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},d,{alias:null,args:null,kind:"ScalarField",name:"fieldId",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:"entityLabels(limit:100)"},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[d,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"5ce660766e01d51593167bc5bfb72fb2",id:null,metadata:{},name:"resourceRegistryDeploymentQuery",operationKind:"query",text:`query resourceRegistryDeploymentQuery(
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
  creator {
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

fragment BAIEntityLabelSettingModalFragment on EntityLabelConnection {
  edges {
    node {
      fieldId
      key
      value
      id
    }
  }
}

fragment BAIEntityLabelTokensFragment on EntityLabelConnection {
  edges {
    node {
      key
      value
      id
    }
  }
}

fragment BAIModelDeploymentNodesFragment on ModelDeployment {
  id
  entityId
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
    projectV2 {
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
  currentRevision {
    id
    revisionNumber
    modelMountConfig {
      vfolder {
        id
        name
      }
    }
  }
  entityLabels(limit: 100) {
    ...BAIEntityLabelTokensFragment
    ...BAIEntityLabelSettingModalFragment
  }
  ...BAIDeploymentOwnerInfo_deployment
}
`}}})();On.hash="4e7a525297dc8b70a0c7765c072ffe4b";const qn=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"first"},l={defaultValue:null,kind:"LocalArgument",name:"offset"},o={defaultValue:null,kind:"LocalArgument",name:"order"},t={defaultValue:null,kind:"LocalArgument",name:"scopeId"},r=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"order",variableName:"order"},{kind:"Variable",name:"scope_id",variableName:"scopeId"}],d={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},g=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],u={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},p=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[i,y,m,a],storageKey:null}],storageKey:null},d];return{fragment:{argumentDefinitions:[n,e,l,o,t],kind:"Fragment",metadata:null,name:"resourceRegistrySessionQuery",selections:[{alias:null,args:r,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[d,{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[i,{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[t,e,l,n,o],kind:"Operation",name:"resourceRegistrySessionQuery",selections:[{alias:null,args:r,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[d,{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[i,y,m,a,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},c,{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[i,a,{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:g,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:g,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},u,i],storageKey:null},y,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},c,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},u,{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[y,m,i],storageKey:null}],storageKey:null},d],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:p,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:p,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domain_name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"bfaaba072b8893d044378458f8e55896",id:null,metadata:{},name:"resourceRegistrySessionQuery",operationKind:"query",text:`query resourceRegistrySessionQuery(
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
  priority
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
  vfolder_nodes {
    edges {
      node {
        ...FolderLink_vfolderNode
        id
      }
    }
  }
}

fragment SFTPConnectionInfoModalFragment on ComputeSessionNode {
  row_id
  vfolder_nodes {
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
  owner {
    email
    id
  }
  resource_opts
  status
  vfolder_mounts
  vfolder_nodes {
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
  idle_checks
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
  priority
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
  owner {
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
  queue_position
  cluster_size
  kernel_nodes {
    edges {
      node {
        id
        status
      }
    }
  }
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
`}}})();qn.hash="bb92c247cff2de74130007224eef9d02";/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

 Every session field the manager's queryfilter accepts
 (`gql_legacy/session.py::_queryfilter_fieldspec`), so a custom panel can
 express any condition the backend supports instead of the three the picker
 used to offer (FR-3654).
*/const la=(n,e=l=>l)=>n.map(l=>({label:e(l),value:l})),aa=["PENDING","DEPRIORITIZING","RESERVED","SCHEDULED","PREPARING","PULLING","PREPARED","CREATING","RUNNING","RESTARTING","RUNNING_DEGRADED","PREEMPTED","RESCHEDULING","TERMINATING","TERMINATED","ERROR","CANCELLED"],ta=["interactive","batch","inference","system"],sa=["undefined","success","failure"],ra=["single-node","multi-node"],Tn=(n,e,l)=>({key:n,propertyLabel:e,type:"uuid",rule:{message:l("general.InvalidUUID"),validate:o=>ol(o.toLowerCase())}}),rn=(n,e,l,o)=>({key:n,propertyLabel:e,type:"string",defaultOperator:"==",strictSelection:!0,options:la(l,o)}),ia=n=>[{key:"name",propertyLabel:n("session.SessionName"),type:"string"},rn("status",n("session.Status"),aa),rn("type",n("session.SessionType"),ta,e=>dl(n,e)),{key:"scaling_group",propertyLabel:n("session.ResourceGroup"),type:"string"},{key:"agent_ids",propertyLabel:n("session.Agent"),type:"string"},{key:"image",propertyLabel:n("general.Image"),type:"string"},{key:"user_email",propertyLabel:n("session.launcher.OwnerEmail"),type:"string"},Tn("user_id",n("credential.UserID"),n),{key:"full_name",propertyLabel:n("credential.FullName"),type:"string"},{key:"access_key",propertyLabel:n("general.AccessKey"),type:"string"},rn("cluster_mode",n("session.ClusterMode"),ra),{key:"cluster_size",propertyLabel:n("session.launcher.ClusterSize"),type:"number"},{key:"priority",propertyLabel:n("session.Priority"),type:"number"},rn("result",n("session.Result"),sa),{key:"status_info",propertyLabel:n("session.StatusInfo"),type:"string"},{key:"startup_command",propertyLabel:n("session.StartupCommand"),type:"string"},Tn("id",n("session.SessionId"),n),{key:"created_at",propertyLabel:n("session.CreatedAt"),type:"datetime"},{key:"starts_at",propertyLabel:n("session.StartsAt"),type:"datetime"},{key:"terminated_at",propertyLabel:n("session.TerminatedAt"),type:"datetime"}],oa=n=>n?ml(n).format("lll"):"-",da=()=>({filter:n,order:e,limit:l,offset:o})=>({filter:typeof n=="string"?void 0:n??void 0,orderBy:Rn(e??null),limit:l,offset:o}),Gn=n=>n?{count:n.count,nodes:mn(n.edges.map(e=>e==null?void 0:e.node))}:null,ua={key:"session",labelKey:"webui.menu.Sessions",defaultOrder:"-created_at",kind:"sessionNodes",query:qn,getStringFilterProperties:ia,buildVariables:({filter:n,order:e,limit:l,offset:o,projectId:t})=>({scopeId:`project:${t}`,first:l,offset:o,filter:typeof n=="string"&&n?n:void 0,order:e??"-created_at"}),selectConnection:n=>{const e=n.compute_session_nodes;return e?{count:e.count??0,nodes:mn(e.edges.map(l=>l==null?void 0:l.node))}:null}},ca={key:"deployment",labelKey:"webui.menu.Deployments",defaultOrder:"-createdAt",kind:"deploymentNodes",query:On,getFilterProperties:n=>[{key:"name",propertyLabel:n("deployment.filter.Name"),type:"string"},{key:"tags",propertyLabel:n("deployment.filter.Tags"),type:"string"},{key:"endpointUrl",propertyLabel:n("deployment.filter.EndpointUrl"),type:"string"},{key:"openToPublic",propertyLabel:n("deployment.filter.OpenToPublic"),type:"boolean"}],buildVariables:({filter:n,order:e,limit:l,offset:o,projectId:t})=>({filter:{...typeof n=="string"?{}:n??{},...t?{projectId:{equals:t}}:{}},orderBy:Rn(e??null),limit:l,offset:o}),selectConnection:n=>Gn(n.myDeployments)},ma={key:"vfolder",labelKey:"webui.menu.Data&Storage",defaultOrder:"-createdAt",minRole:"superadmin",query:$n,getFilterProperties:n=>[{key:"name",propertyLabel:n("data.folders.Name"),type:"string"},{key:"host",propertyLabel:n("data.folders.Location"),type:"string"}],getColumns:n=>[{key:"name",dataIndex:"name",title:n("data.folders.Name"),sorter:!0,render:(e,l)=>{var o;return(o=l.metadata)==null?void 0:o.name}},{key:"host",dataIndex:"host",title:n("data.folders.Location"),sorter:!0},{key:"status",dataIndex:"status",title:n("general.Status"),sorter:!0,minWidth:140,render:(e,l)=>l.status?s.jsx(ul,{label:l.status,variant:cl("vfolder",l.status)}):null},{key:"createdAt",dataIndex:"createdAt",title:n("general.CreatedAt"),sorter:!0,render:(e,l)=>{var o;return oa((o=l.metadata)==null?void 0:o.createdAt)}}],buildVariables:da(),selectConnection:n=>Gn(n.adminVfoldersV2)},ke={session:ua,deployment:ca,vfolder:ma},ga=Object.keys(ke),pa=n=>ga.filter(e=>{const l=ke[e].minRole;return l?l==="superadmin"?n==="superadmin":n==="superadmin"||n==="admin":!0}),nn=(n,e)=>{if(n.title)return n.title;const l=ke[n.resourceType];return l?e(l.labelKey):n.resourceType},ya=n=>{"use memo";const e=U.c(12),{descriptor:l,fetchKey:o,onEdit:t,onRemove:r}=n,{t:d}=Fe(),{token:i}=Ge();let y;e[0]!==l||e[1]!==d?(y=nn(l,d),e[0]=l,e[1]=d,e[2]=y):y=e[2];const m=y;let a;e[3]!==l||e[4]!==o||e[5]!==i?(a=g=>s.jsx(G,{direction:"row",wrap:"wrap",gap:"lg",children:s.jsx(xn,{style:{paddingBlock:i("--spacing-4")},children:s.jsx(V.Suspense,{fallback:s.jsx(Ee,{}),children:s.jsx(Un,{descriptor:l,fetchKey:`${o??""}:${g}`},`${l.resourceType}:${JSON.stringify(l.filter??null)}`)})})}),e[3]=l,e[4]=o,e[5]=i,e[6]=a):a=e[6];let c;return e[7]!==t||e[8]!==r||e[9]!==a||e[10]!==m?(c=s.jsx(vn,{title:m,onEdit:t,onRemove:r,children:a}),e[7]=t,e[8]=r,e[9]=a,e[10]=m,e[11]=c):c=e[11],c},Un=n=>{"use memo";const e=U.c(16),{descriptor:l,fetchKey:o}=n,{t}=Fe(),r=Je(),d=ke[l.resourceType];let i;e[0]!==d||e[1]!==r.id||e[2]!==l.filter||e[3]!==l.order?(i=d.buildVariables({filter:l.filter??void 0,order:l.order??d.defaultOrder,limit:1,offset:0,projectId:r.id??""}),e[0]=d,e[1]=r.id,e[2]=l.filter,e[3]=l.order,e[4]=i):i=e[4];const y=i,m=V.useDeferredValue(y),a=V.useDeferredValue(o);let c;e[5]!==a?(c={fetchPolicy:"store-and-network",fetchKey:a},e[5]=a,e[6]=c):c=e[6];const g=Xe.useLazyLoadQuery(d.query,m,c);let u;e[7]!==d||e[8]!==g?(u=d.selectConnection(g),e[7]=d,e[8]=g,e[9]=u):u=e[9];const p=u;let F;e[10]!==d.labelKey||e[11]!==t?(F=t(d.labelKey),e[10]=d.labelKey,e[11]=t,e[12]=F):F=e[12];const k=(p==null?void 0:p.count)??0;let f;return e[13]!==F||e[14]!==k?(f=s.jsx(gl,{title:F,current:k,progressMode:"hidden"}),e[13]=F,e[14]=k,e[15]=f):f=e[15],f},fa=["name","status","replicaSummary","model","createdAt"],zn=n=>{"use memo";const e=U.c(36),{descriptor:l,fetchKey:o,onChangeOrder:t,disableNavigation:r}=n,d=Je(),i=gn(),y=jn(),m=ke.deployment,[a,c]=We("table_column_overrides.DashboardDeploymentPanel");let g;e[0]===Symbol.for("react.memo_cache_sentinel")?(g={current:1,pageSize:10},e[0]=g):g=e[0];const{baiPaginationOption:u,tablePaginationOption:p,setTablePaginationOption:F}=_n(g),k=l.order??m.defaultOrder;let f;e[1]!==u.limit||e[2]!==u.offset||e[3]!==d.id||e[4]!==l.filter||e[5]!==k?(f=m.buildVariables({filter:l.filter??void 0,order:k,limit:u.limit,offset:u.offset,projectId:d.id??""}),e[1]=u.limit,e[2]=u.offset,e[3]=d.id,e[4]=l.filter,e[5]=k,e[6]=f):f=e[6];const T=f,b=V.useDeferredValue(T),K=V.useDeferredValue(o);let _;e[7]!==K?(_={fetchPolicy:"store-and-network",fetchKey:K},e[7]=K,e[8]=_):_=e[8];const S=Xe.useLazyLoadQuery(m.query,b,_).myDeployments;let C;e[9]!==(S==null?void 0:S.edges)?(C=mn(S==null?void 0:S.edges.map(Sa)),e[9]=S==null?void 0:S.edges,e[10]=C):C=e[10];const j=C,R=!t;let I;e[11]!==t?(I=t?w=>t(w??void 0):void 0,e[11]=t,e[12]=I):I=e[12];const x=b!==T||K!==o;let N;e[13]!==y||e[14]!==r||e[15]!==i?(N=w=>w.filter(ka).map(P=>P.key==="name"&&!r?{...P,onTitleClick:O=>{i(`${y("deployments")}/${pl(O.id)}`)}}:P),e[13]=y,e[14]=r,e[15]=i,e[16]=N):N=e[16];const v=(S==null?void 0:S.count)??0;let h;e[17]!==F?(h=(w,P)=>{F({current:w,pageSize:P})},e[17]=F,e[18]=h):h=e[18];let L;e[19]!==h||e[20]!==v||e[21]!==p.current||e[22]!==p.pageSize?(L={pageSize:p.pageSize,current:p.current,total:v,onChange:h},e[19]=h,e[20]=v,e[21]=p.current,e[22]=p.pageSize,e[23]=L):L=e[23];let E;e[24]!==a||e[25]!==c?(E={columnOverrides:a,onColumnOverridesChange:c},e[24]=a,e[25]=c,e[26]=E):E=e[26];let D;return e[27]!==j||e[28]!==k||e[29]!==L||e[30]!==E||e[31]!==R||e[32]!==I||e[33]!==x||e[34]!==N?(D=s.jsx(Yl,{deploymentsFrgmt:j,order:k,disableSorter:R,onChangeOrder:I,loading:x,customizeColumns:N,pagination:L,tableSettings:E}),e[27]=j,e[28]=k,e[29]=L,e[30]=E,e[31]=R,e[32]=I,e[33]=x,e[34]=N,e[35]=D):D=e[35],D};function Sa(n){return n==null?void 0:n.node}function ka(n){return fa.includes(String(n.key))}const Qn=n=>{"use memo";const e=U.c(36),{descriptor:l,fetchKey:o,onChangeOrder:t,disableSessionDetail:r}=n,d=Je(),i=gn(),y=En(),m=ke.session,[a,c]=We("table_column_overrides.DashboardSessionPanel");let g;e[0]===Symbol.for("react.memo_cache_sentinel")?(g={current:1,pageSize:10},e[0]=g):g=e[0];const{baiPaginationOption:u,tablePaginationOption:p,setTablePaginationOption:F}=_n(g),k=l.order??m.defaultOrder;let f;e[1]!==u.limit||e[2]!==u.offset||e[3]!==d.id||e[4]!==l.filter||e[5]!==k?(f=m.buildVariables({filter:l.filter??void 0,order:k,limit:u.limit,offset:u.offset,projectId:d.id??""}),e[1]=u.limit,e[2]=u.offset,e[3]=d.id,e[4]=l.filter,e[5]=k,e[6]=f):f=e[6];const T=f,b=V.useDeferredValue(T),K=V.useDeferredValue(o);let _;e[7]!==K?(_={fetchPolicy:"store-and-network",fetchKey:K},e[7]=K,e[8]=_):_=e[8];const S=Xe.useLazyLoadQuery(m.query,b,_).compute_session_nodes;let C;e[9]!==(S==null?void 0:S.edges)?(C=mn(S==null?void 0:S.edges.map(Fa)),e[9]=S==null?void 0:S.edges,e[10]=C):C=e[10];const j=C,R=!t;let I;e[11]!==t?(I=t?w=>t(w??void 0):void 0,e[11]=t,e[12]=I):I=e[12];const x=b!==T||K!==o;let N;e[13]!==r||e[14]!==y||e[15]!==i?(N=r?void 0:w=>{const P=new URLSearchParams(y.search);P.set("sessionDetail",w.row_id),i({pathname:y.pathname,hash:y.hash,search:P.toString()},{state:{sessionDetailDrawerFrgmt:w,createdAt:new Date().toISOString()}})},e[13]=r,e[14]=y,e[15]=i,e[16]=N):N=e[16];const v=(S==null?void 0:S.count)??0;let h;e[17]!==F?(h=(w,P)=>{F({current:w,pageSize:P})},e[17]=F,e[18]=h):h=e[18];let L;e[19]!==h||e[20]!==v||e[21]!==p.current||e[22]!==p.pageSize?(L={pageSize:p.pageSize,current:p.current,total:v,onChange:h},e[19]=h,e[20]=v,e[21]=p.current,e[22]=p.pageSize,e[23]=L):L=e[23];let E;e[24]!==a||e[25]!==c?(E={columnOverrides:a,onColumnOverridesChange:c},e[24]=a,e[25]=c,e[26]=E):E=e[26];let D;return e[27]!==k||e[28]!==j||e[29]!==L||e[30]!==E||e[31]!==R||e[32]!==I||e[33]!==x||e[34]!==N?(D=s.jsx(yl,{sessionsFrgmt:j,order:k,disableSorter:R,onChangeOrder:I,loading:x,onClickSessionName:N,pagination:L,tableSettings:E}),e[27]=k,e[28]=j,e[29]=L,e[30]=E,e[31]=R,e[32]=I,e[33]=x,e[34]=N,e[35]=D):D=e[35],D};function Fa(n){return n==null?void 0:n.node}const ba=n=>{"use memo";const e=U.c(11),{descriptor:l,fetchKey:o,onEdit:t,onRemove:r}=n,{t:d}=Fe();let i;e[0]!==l||e[1]!==d?(i=nn(l,d),e[0]=l,e[1]=d,e[2]=i):i=e[2];const y=i;let m;e[3]!==l||e[4]!==o?(m=c=>{var g,u;return s.jsx(V.Suspense,{fallback:s.jsx(Ee,{}),children:((g=ke[l.resourceType])==null?void 0:g.kind)==="deploymentNodes"?s.jsx(zn,{descriptor:l,fetchKey:`${o??""}:${c}`},`${l.resourceType}:${JSON.stringify(l.filter??null)}:${l.order??""}`):((u=ke[l.resourceType])==null?void 0:u.kind)==="sessionNodes"?s.jsx(Qn,{descriptor:l,fetchKey:`${o??""}:${c}`},`${l.resourceType}:${JSON.stringify(l.filter??null)}:${l.order??""}`):s.jsx(Wn,{descriptor:l,fetchKey:`${o??""}:${c}`},`${l.resourceType}:${JSON.stringify(l.filter??null)}:${l.order??""}`)})},e[3]=l,e[4]=o,e[5]=m):m=e[5];let a;return e[6]!==t||e[7]!==r||e[8]!==m||e[9]!==y?(a=s.jsx(vn,{title:y,onEdit:t,onRemove:r,children:m}),e[6]=t,e[7]=r,e[8]=m,e[9]=y,e[10]=a):a=e[10],a},Wn=n=>{"use memo";var N;const e=U.c(46),{descriptor:l,fetchKey:o,onChangeOrder:t}=n,{t:r}=Fe(),d=Je(),i=ke[l.resourceType];let y;e[0]===Symbol.for("react.memo_cache_sentinel")?(y={current:1,pageSize:10},e[0]=y):y=e[0];const{baiPaginationOption:m,tablePaginationOption:a,setTablePaginationOption:c}=_n(y),g=l.order??i.defaultOrder;let u;e[1]!==m.limit||e[2]!==m.offset||e[3]!==i||e[4]!==d.id||e[5]!==l.filter||e[6]!==g?(u=i.buildVariables({filter:l.filter??void 0,order:g,limit:m.limit,offset:m.offset,projectId:d.id??""}),e[1]=m.limit,e[2]=m.offset,e[3]=i,e[4]=d.id,e[5]=l.filter,e[6]=g,e[7]=u):u=e[7];const p=u,F=V.useDeferredValue(p),k=V.useDeferredValue(o);let f;e[8]!==k?(f={fetchPolicy:"store-and-network",fetchKey:k},e[8]=k,e[9]=f):f=e[9];const T=Xe.useLazyLoadQuery(i.query,F,f);let b,K,_,A,S,C;if(e[10]!==i||e[11]!==T||e[12]!==k||e[13]!==F||e[14]!==o||e[15]!==t||e[16]!==r||e[17]!==p){if(K=i.selectConnection(T),_=F!==p||k!==o,e[24]!==i||e[25]!==t||e[26]!==r){const v=((N=i.getColumns)==null?void 0:N.call(i,r))??[];b=fl,A="id",S=t?[...v]:v.map(_a),e[24]=i,e[25]=t,e[26]=r,e[27]=b,e[28]=A,e[29]=S}else b=e[27],A=e[28],S=e[29];C=[...(K==null?void 0:K.nodes)??[]],e[10]=i,e[11]=T,e[12]=k,e[13]=F,e[14]=o,e[15]=t,e[16]=r,e[17]=p,e[18]=b,e[19]=K,e[20]=_,e[21]=A,e[22]=S,e[23]=C}else b=e[18],K=e[19],_=e[20],A=e[21],S=e[22],C=e[23];const j=(K==null?void 0:K.count)??0;let R;e[30]!==c?(R=(v,h)=>c({current:v,pageSize:h}),e[30]=c,e[31]=R):R=e[31];let I;e[32]!==j||e[33]!==R||e[34]!==a.current||e[35]!==a.pageSize?(I={current:a.current,pageSize:a.pageSize,total:j,onChange:R},e[32]=j,e[33]=R,e[34]=a.current,e[35]=a.pageSize,e[36]=I):I=e[36];let x;return e[37]!==b||e[38]!==_||e[39]!==t||e[40]!==g||e[41]!==A||e[42]!==S||e[43]!==C||e[44]!==I?(x=s.jsx(b,{rowKey:A,columns:S,dataSource:C,loading:_,order:g,onChangeOrder:t,pagination:I}),e[37]=b,e[38]=_,e[39]=t,e[40]=g,e[41]=A,e[42]=S,e[43]=C,e[44]=I,e[45]=x):x=e[45],x};function _a(n){return{...n,sorter:!1}}const ha=n=>{"use memo";const e=U.c(11),{descriptor:l,fetchKey:o,onEdit:t,onRemove:r}=n,{t:d}=Fe();let i;e[0]!==l||e[1]!==d?(i=nn(l,d),e[0]=l,e[1]=d,e[2]=i):i=e[2];const y=i;let m;e[3]!==l||e[4]!==o?(m=c=>s.jsx(V.Suspense,{fallback:s.jsx(Ee,{}),children:s.jsx(Jn,{descriptor:l,fetchKey:`${o??""}:${c}`},`${JSON.stringify(l.filter??null)}:${l.order??""}`)}),e[3]=l,e[4]=o,e[5]=m):m=e[5];let a;return e[6]!==t||e[7]!==r||e[8]!==m||e[9]!==y?(a=s.jsx(vn,{title:y,onEdit:t,onRemove:r,children:m}),e[6]=t,e[7]=r,e[8]=m,e[9]=y,e[10]=a):a=e[10],a},Jn=n=>{"use memo";const e=U.c(12),{descriptor:l,fetchKey:o,onChangeViewParams:t,disableSessionDetail:r}=n,d=Je(),i=gn(),y=En(),m=typeof l.filter=="string"?l.filter:null,a=l.order??null,c=d.id??null,g=o??"",u=l.gridView??en;let p;e[0]!==r||e[1]!==y||e[2]!==i?(p=r?void 0:k=>{const f=new URLSearchParams(y.search);f.set("sessionDetail",k),i({pathname:y.pathname,hash:y.hash,search:f.toString()})},e[0]=r,e[1]=y,e[2]=i,e[3]=p):p=e[3];let F;return e[4]!==t||e[5]!==m||e[6]!==a||e[7]!==c||e[8]!==g||e[9]!==u||e[10]!==p?(F=s.jsx(Sl,{filter:m,order:a,projectId:c,fetchKey:g,viewParams:u,onChangeViewParams:t,onClickSession:p}),e[4]=t,e[5]=m,e[6]=a,e[7]=c,e[8]=g,e[9]=u,e[10]=p,e[11]=F):F=e[11],F};/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */const Yn={resourceTable:ba,resourceCount:ya,sessionResourceGrid:ha},Hn={resourceTable:"dashboard.panelModal.Table",resourceCount:"dashboard.panelModal.Count",sessionResourceGrid:"session.resourceGrid.GridView"},Kn=(n,{gridEnabled:e,forcePanelType:l})=>{const o=["resourceTable","resourceCount"];return n==="session"&&(e||l==="sessionResourceGrid")&&o.push("sessionResourceGrid"),o},va=(n,{gridEnabled:e})=>n.panelType==="sessionResourceGrid"&&!e?"resourceTable":n.panelType,on=n=>Array.isArray(n)?n.filter(e=>{if(!e||typeof e!="object")return!1;const l=e;return typeof l.id=="string"&&l.panelType in Yn&&!!l.descriptor&&l.descriptor.resourceType in ke&&(l.descriptor.title===void 0||typeof l.descriptor.title=="string")}):[],Ca=n=>{"use memo";const e=U.c(43);let l;e[0]!==n?(l=n===void 0?{}:n,e[0]=n,e[1]=l):l=e[1];const{enabled:o,fetchKey:t,onRequestEdit:r}=l,d=o===void 0?!0:o,{t:i}=Fe(),y=Dn(),[m,a]=We("custom_dashboard_panels"),[,c]=We("dashboard_board_items"),[g]=We("experimental_session_resource_grid");let u,p,F,k,f,T,b;if(e[2]!==d||e[3]!==t||e[4]!==g||e[5]!==r||e[6]!==c||e[7]!==a||e[8]!==m||e[9]!==i||e[10]!==y){k=d?m?on(m):[...sn]:[];let S;e[18]!==y?(p=pa(y),S=new Set(p),e[18]=y,e[19]=p,e[20]=S):(p=e[19],S=e[20]);const C=S;let j;e[21]!==a?(j=v=>{a(h=>[...on(h??sn),ea(v)])},e[21]=a,e[22]=j):j=e[22],u=j,b=(v,h)=>{const L=k.find(E=>E.id===v);if(L&&L.panelType!==h.panelType){const E=un[h.panelType]??un.resourceTable;c(D=>Array.isArray(D)?D.map(w=>w.id===v?{id:v,...E}:w):D)}a(E=>on(E??sn).map(D=>D.id===v?{...D,panelType:h.panelType,descriptor:{resourceType:h.resourceType,title:h.title,filter:h.filter??null,order:h.order??null,gridView:h.panelType==="sessionResourceGrid"?h.gridView??en:null}}:D))};let R;e[23]!==c||e[24]!==a?(R=v=>{a(h=>on(h??sn).filter(L=>L.id!==v)),c(h=>Array.isArray(h)?h.filter(L=>L.id!==v):h)},e[23]=c,e[24]=a,e[25]=R):R=e[25],f=R;let I;e[26]!==C?(I=v=>C.has(v.descriptor.resourceType),e[26]=C,e[27]=I):I=e[27];const x=k.filter(I);F=x.map(Ta);let N;e[28]!==t||e[29]!==g||e[30]!==r||e[31]!==f||e[32]!==i?(N=v=>{const h=Yn[va(v,{gridEnabled:!!g})],L=s.jsx(He,{title:nn(v.descriptor,i),status:"error",children:h?s.jsx(h,{descriptor:v.descriptor,fetchKey:t,onEdit:r?()=>r(v):void 0,onRemove:()=>f(v.id)}):null},`${v.panelType}:${JSON.stringify(v.descriptor)}`);return[v.id,L]},e[28]=t,e[29]=g,e[30]=r,e[31]=f,e[32]=i,e[33]=N):N=e[33],T=new Map(x.map(N)),e[2]=d,e[3]=t,e[4]=g,e[5]=r,e[6]=c,e[7]=a,e[8]=m,e[9]=i,e[10]=y,e[11]=u,e[12]=p,e[13]=F,e[14]=k,e[15]=f,e[16]=T,e[17]=b}else u=e[11],p=e[12],F=e[13],k=e[14],f=e[15],T=e[16],b=e[17];const K=T,_=!!g;let A;return e[34]!==u||e[35]!==p||e[36]!==K||e[37]!==F||e[38]!==k||e[39]!==f||e[40]!==_||e[41]!==b?(A={panels:k,availableResources:p,gridEnabled:_,customDefaultLayout:F,customContentById:K,addPanel:u,updatePanel:b,removePanel:f},e[34]=u,e[35]=p,e[36]=K,e[37]=F,e[38]=k,e[39]=f,e[40]=_,e[41]=b,e[42]=A):A=e[42],A};function Ta(n){return{id:n.id,...un[n.panelType]??un.resourceTable}}const Ka=n=>{"use memo";const e=U.c(49),{panels:l,availableResources:o,gridEnabled:t,onRequestAdd:r,onRequestEdit:d,onRemove:i,onResetLayout:y}=n,m=t===void 0?!1:t,{t:a}=Fe(),{token:c}=Ge();let g;e[0]!==o?(g=new Set(o),e[0]=o,e[1]=g):g=e[1];const u=g;let p;e[2]!==c?(p=c("--spacing-6"),e[2]=c,e[3]=p):p=e[3];let F;e[4]!==c?(F=c("--color-border-emphasized"),e[4]=c,e[5]=F):F=e[5];const k=`1px solid ${F}`;let f;e[6]!==p||e[7]!==k?(f={width:320,flexShrink:0,paddingLeft:p,borderLeft:k,overflow:"auto"},e[6]=p,e[7]=k,e[8]=f):f=e[8];let T;e[9]!==a?(T=a("dashboard.editSider.Title"),e[9]=a,e[10]=T):T=e[10];let b;e[11]!==T?(b=s.jsx(an,{strong:!0,children:T}),e[11]=T,e[12]=b):b=e[12];let K;e[13]===Symbol.for("react.memo_cache_sentinel")?(K=s.jsx(kl,{size:"1em"}),e[13]=K):K=e[13];let _;e[14]!==a?(_=a("button.Add"),e[14]=a,e[15]=_):_=e[15];let A;e[16]!==r||e[17]!==_?(A=s.jsx(Fn,{variant:"primary",size:"sm",icon:K,label:_,onClick:r}),e[16]=r,e[17]=_,e[18]=A):A=e[18];let S;e[19]!==A||e[20]!==b?(S=s.jsxs(G,{direction:"row",justify:"between",align:"center",gap:"sm",children:[b,A]}),e[19]=A,e[20]=b,e[21]=S):S=e[21];let C;e[22]!==u||e[23]!==m||e[24]!==i||e[25]!==d||e[26]!==l||e[27]!==a||e[28]!==c?(C=l.length===0?s.jsx(an,{type:"secondary",children:a("dashboard.editSider.Empty")}):s.jsx(G,{direction:"column",align:"stretch",children:l.map(L=>{var z;const E=nn(L.descriptor,a),D=a(((z=ke[L.descriptor.resourceType])==null?void 0:z.labelKey)??L.descriptor.resourceType),w=u.has(L.descriptor.resourceType),P=L.panelType==="sessionResourceGrid"&&!m,O=[a(P?"dashboard.editSider.GridDisabled":Hn[L.panelType]??L.panelType),L.descriptor.title?D:void 0,w?void 0:a("dashboard.editSider.RequiresSuperadmin")].filter(Boolean).join(" · ");return s.jsxs(G,{direction:"row",justify:"between",align:"center",gap:"sm",style:{paddingBlock:c("--spacing-2"),borderBottom:`1px solid ${c("--color-border")}`},children:[s.jsxs(G,{direction:"column",align:"stretch",style:{flex:1,minWidth:0},children:[s.jsx(an,{ellipsis:!0,children:E}),s.jsx(an,{type:"secondary",ellipsis:{tooltip:O},style:{fontSize:c("--font-size-sm")},children:O})]}),s.jsxs(G,{direction:"row",align:"center",gap:"xxs",children:[s.jsx(dn,{variant:"ghost",size:"sm",label:a("button.Edit"),tooltip:a("button.Edit"),icon:s.jsx(An,{size:"1em"}),onClick:()=>d(L)}),s.jsx(bn,{title:a("dialog.ask.DoYouWantToDeleteSomething",{name:E}),isDanger:!0,onConfirm:()=>i(L.id),children:s.jsx(dn,{variant:"ghost",size:"sm",label:a("button.Delete"),tooltip:a("button.Delete"),icon:s.jsx(In,{size:"1em"})})})]})]},L.id)})}),e[22]=u,e[23]=m,e[24]=i,e[25]=d,e[26]=l,e[27]=a,e[28]=c,e[29]=C):C=e[29];let j;e[30]!==a?(j=a("dashboard.editSider.ResetLayout"),e[30]=a,e[31]=j):j=e[31];let R;e[32]!==a?(R=a("dashboard.editSider.ResetLayoutDescription"),e[32]=a,e[33]=R):R=e[33];let I;e[34]===Symbol.for("react.memo_cache_sentinel")?(I=s.jsx(Fl,{size:"1em"}),e[34]=I):I=e[34];let x;e[35]!==a?(x=a("dashboard.editSider.ResetLayout"),e[35]=a,e[36]=x):x=e[36];let N;e[37]!==x?(N=s.jsx(Fn,{variant:"secondary",size:"sm",icon:I,label:x}),e[37]=x,e[38]=N):N=e[38];let v;e[39]!==y||e[40]!==j||e[41]!==R||e[42]!==N?(v=s.jsx(bn,{title:j,description:R,isDanger:!0,onConfirm:y,children:N}),e[39]=y,e[40]=j,e[41]=R,e[42]=N,e[43]=v):v=e[43];let h;return e[44]!==S||e[45]!==C||e[46]!==v||e[47]!==f?(h=s.jsxs(G,{direction:"column",align:"stretch",gap:"md",style:f,children:[S,C,v]}),e[44]=S,e[45]=C,e[46]=v,e[47]=f,e[48]=h):h=e[48],h},La=n=>{"use memo";var Ue,Be;const e=U.c(184),{open:l,onRequestClose:o,initialPanel:t,availableResources:r,gridEnabled:d,onSubmit:i,afterClose:y}=n,m=d===void 0?!1:d,{t:a}=Fe(),{token:c}=Ge(),[g]=$e.useForm(),u=r[0],p=(t==null?void 0:t.descriptor.resourceType)??u;let F;e[0]!==r||e[1]!==t||e[2]!==p?(F=t&&!r.includes(p)?[...r,p]:r,e[0]=r,e[1]=t,e[2]=p,e[3]=F):F=e[3];const k=F,[f,T]=V.useState((t==null?void 0:t.descriptor.order)??null),[b,K]=V.useState((t==null?void 0:t.descriptor.gridView)??en),_=$e.useWatch("resourceType",g)??p,A=$e.useWatch("panelType",g)??(t==null?void 0:t.panelType)??"resourceTable",S=$e.useWatch("filter",g)??void 0,C=ke[_];let j,R,I,x,N,v,h,L,E,D,w,P,O,z,De,be,_e,W,we,Ce,he,Te,B,J,Ke,ve,Y;if(e[4]!==y||e[5]!==g||e[6]!==m||e[7]!==b||e[8]!==t||e[9]!==p||e[10]!==o||e[11]!==i||e[12]!==l||e[13]!==f||e[14]!==_||e[15]!==a){const $=Kn(_,{gridEnabled:m,forcePanelType:t==null?void 0:t.panelType});let Q;e[43]!==g||e[44]!==b||e[45]!==o||e[46]!==i||e[47]!==f?(Q=async()=>{var Ze;let q;try{q=await g.validateFields()}catch{return}i({panelType:q.panelType,resourceType:q.resourceType,title:((Ze=q.title)==null?void 0:Ze.trim())||void 0,filter:q.filter??null,order:f,gridView:q.panelType==="sessionResourceGrid"?b:null}),o()},e[43]=g,e[44]=b,e[45]=o,e[46]=i,e[47]=f,e[48]=Q):Q=e[48];const Ye=Q;N=hl,z=l,De="min(960px, 95vw)",e[49]!==t||e[50]!==a?(be=a(t?"dashboard.panelModal.EditPanel":"dashboard.panelModal.AddPanel"),e[49]=t,e[50]=a,e[51]=be):be=e[51],e[52]!==t||e[53]!==a?(_e=a(t?"button.Save":"button.Add"),e[52]=t,e[53]=a,e[54]=_e):_e=e[54],W=Ye,we=o,Ce=y,x=$e,D=g,w="vertical";const Ve=(t==null?void 0:t.panelType)??"resourceTable",qe=t==null?void 0:t.descriptor.title,Pe=(t==null?void 0:t.descriptor.filter)??void 0;e[55]!==p||e[56]!==Ve||e[57]!==qe||e[58]!==Pe?(P={panelType:Ve,resourceType:p,title:qe,filter:Pe},e[55]=p,e[56]=Ve,e[57]=qe,e[58]=Pe,e[59]=P):P=e[59],e[60]!==g||e[61]!==m||e[62]!==(t==null?void 0:t.panelType)?(O=q=>{q.resourceType&&(g.setFieldsValue({filter:void 0}),T(null),K(en),Kn(q.resourceType,{gridEnabled:m,forcePanelType:t==null?void 0:t.panelType}).includes(g.getFieldValue("panelType"))||g.setFieldsValue({panelType:"resourceTable"}))},e[60]=g,e[61]=m,e[62]=t==null?void 0:t.panelType,e[63]=O):O=e[63],I=G,v="row",h="start",L="md",E="wrap",R=$e.Item,B="panelType",e[64]!==a?(J=a("dashboard.panelModal.PanelType"),e[64]=a,e[65]=J):J=e[65],Ke=!0;let je;e[66]!==a?(je=a("dashboard.panelModal.PanelTypeRequired"),e[66]=a,e[67]=je):je=e[67],e[68]!==je?(ve=[{required:!0,message:je}],e[68]=je,e[69]=ve):ve=e[69],e[70]===Symbol.for("react.memo_cache_sentinel")?(Y={flexShrink:0},e[70]=Y):Y=e[70],j=vl,e[71]!==a?(he=a("dashboard.panelModal.PanelType"),e[71]=a,e[72]=he):he=e[72];let ze;e[73]!==a?(ze=q=>({value:q,label:a(Hn[q])}),e[73]=a,e[74]=ze):ze=e[74],Te=$.map(ze),e[4]=y,e[5]=g,e[6]=m,e[7]=b,e[8]=t,e[9]=p,e[10]=o,e[11]=i,e[12]=l,e[13]=f,e[14]=_,e[15]=a,e[16]=j,e[17]=R,e[18]=I,e[19]=x,e[20]=N,e[21]=v,e[22]=h,e[23]=L,e[24]=E,e[25]=D,e[26]=w,e[27]=P,e[28]=O,e[29]=z,e[30]=De,e[31]=be,e[32]=_e,e[33]=W,e[34]=we,e[35]=Ce,e[36]=he,e[37]=Te,e[38]=B,e[39]=J,e[40]=Ke,e[41]=ve,e[42]=Y}else j=e[16],R=e[17],I=e[18],x=e[19],N=e[20],v=e[21],h=e[22],L=e[23],E=e[24],D=e[25],w=e[26],P=e[27],O=e[28],z=e[29],De=e[30],be=e[31],_e=e[32],W=e[33],we=e[34],Ce=e[35],he=e[36],Te=e[37],B=e[38],J=e[39],Ke=e[40],ve=e[41],Y=e[42];let Le;e[75]!==j||e[76]!==he||e[77]!==Te?(Le=s.jsx(j,{label:he,options:Te}),e[75]=j,e[76]=he,e[77]=Te,e[78]=Le):Le=e[78];let H;e[79]!==R||e[80]!==Le||e[81]!==B||e[82]!==J||e[83]!==Ke||e[84]!==ve||e[85]!==Y?(H=s.jsx(R,{name:B,label:J,required:Ke,rules:ve,style:Y,children:Le}),e[79]=R,e[80]=Le,e[81]=B,e[82]=J,e[83]=Ke,e[84]=ve,e[85]=Y,e[86]=H):H=e[86];let X;e[87]!==a?(X=a("dashboard.panelModal.DataSource"),e[87]=a,e[88]=X):X=e[88];let Z;e[89]!==a?(Z=a("dashboard.panelModal.DataSourceRequired"),e[89]=a,e[90]=Z):Z=e[90];let ee;e[91]!==Z?(ee=[{required:!0,message:Z}],e[91]=Z,e[92]=ee):ee=e[92];let Me;e[93]===Symbol.for("react.memo_cache_sentinel")?(Me={flex:1,minWidth:180},e[93]=Me):Me=e[93];let M;e[94]!==a?(M=a("dashboard.panelModal.DataSource"),e[94]=a,e[95]=M):M=e[95];let ne;if(e[96]!==k||e[97]!==a){let $;e[99]!==a?($=Q=>({value:Q,label:a(ke[Q].labelKey)}),e[99]=a,e[100]=$):$=e[100],ne=k.map($),e[96]=k,e[97]=a,e[98]=ne}else ne=e[98];let le;e[101]!==M||e[102]!==ne?(le=s.jsx(Cl,{label:M,options:ne}),e[101]=M,e[102]=ne,e[103]=le):le=e[103];let ae;e[104]!==X||e[105]!==ee||e[106]!==le?(ae=s.jsx($e.Item,{name:"resourceType",label:X,required:!0,rules:ee,style:Me,children:le}),e[104]=X,e[105]=ee,e[106]=le,e[107]=ae):ae=e[107];let te;e[108]!==a?(te=a("dashboard.panelModal.TitleOptional"),e[108]=a,e[109]=te):te=e[109];let Ae;e[110]!==a?(Ae=a("dashboard.panelModal.TitleDescription"),e[110]=a,e[111]=Ae):Ae=e[111];let Ie;e[112]===Symbol.for("react.memo_cache_sentinel")?(Ie={flex:1,minWidth:180},e[112]=Ie):Ie=e[112];let se;e[113]!==a?(se=a("dashboard.panelModal.TitleOptional"),e[113]=a,e[114]=se):se=e[114];let re;e[115]!==C.labelKey||e[116]!==a?(re=a(C.labelKey),e[115]=C.labelKey,e[116]=a,e[117]=re):re=e[117];let ie;e[118]!==se||e[119]!==re?(ie=s.jsx(Tl,{label:se,placeholder:re,hasClear:!0}),e[118]=se,e[119]=re,e[120]=ie):ie=e[120];let oe;e[121]!==te||e[122]!==Ae||e[123]!==ie?(oe=s.jsx($e.Item,{name:"title",label:te,extra:Ae,style:Ie,children:ie}),e[121]=te,e[122]=Ae,e[123]=ie,e[124]=oe):oe=e[124];let Ne;e[125]!==I||e[126]!==v||e[127]!==h||e[128]!==L||e[129]!==E||e[130]!==H||e[131]!==ae||e[132]!==oe?(Ne=s.jsxs(I,{direction:v,align:h,gap:L,wrap:E,children:[H,ae,oe]}),e[125]=I,e[126]=v,e[127]=h,e[128]=L,e[129]=E,e[130]=H,e[131]=ae,e[132]=oe,e[133]=Ne):Ne=e[133];let de;e[134]!==a?(de=a("dashboard.panelModal.Condition"),e[134]=a,e[135]=de):de=e[135];let ue;e[136]!==C||e[137]!==a?(ue=C.kind==="sessionNodes"?s.jsx(bl,{filterProperties:((Ue=C.getStringFilterProperties)==null?void 0:Ue.call(C,a))??[]}):s.jsx(_l,{style:{width:"100%"},filterProperties:[...((Be=C.getFilterProperties)==null?void 0:Be.call(C,a))??[]]}),e[136]=C,e[137]=a,e[138]=ue):ue=e[138];let ce;e[139]!==de||e[140]!==ue?(ce=s.jsx($e.Item,{name:"filter",label:de,children:ue}),e[139]=de,e[140]=ue,e[141]=ce):ce=e[141];let me;e[142]!==x||e[143]!==D||e[144]!==w||e[145]!==P||e[146]!==O||e[147]!==Ne||e[148]!==ce?(me=s.jsxs(x,{form:D,layout:w,initialValues:P,onValuesChange:O,children:[Ne,ce]}),e[142]=x,e[143]=D,e[144]=w,e[145]=P,e[146]=O,e[147]=Ne,e[148]=ce,e[149]=me):me=e[149];let Re;e[150]!==c?(Re=c("--color-border"),e[150]=c,e[151]=Re):Re=e[151];const Oe=`1px solid ${Re}`;let ge;e[152]!==c?(ge=c("--radius-inner"),e[152]=c,e[153]=ge):ge=e[153];let pe;e[154]!==c?(pe=c("--spacing-3"),e[154]=c,e[155]=pe):pe=e[155];let ye;e[156]!==Oe||e[157]!==ge||e[158]!==pe?(ye={border:Oe,borderRadius:ge,padding:pe,maxHeight:360,overflow:"auto"},e[156]=Oe,e[157]=ge,e[158]=pe,e[159]=ye):ye=e[159];let fe;e[160]!==C.kind||e[161]!==C.labelKey||e[162]!==S||e[163]!==b||e[164]!==l||e[165]!==f||e[166]!==A||e[167]!==_||e[168]!==a?(fe=l?s.jsx(He,{title:a(C.labelKey),status:"error",children:s.jsx(V.Suspense,{fallback:s.jsx(Ee,{}),children:A==="resourceCount"?s.jsx(G,{align:"center",justify:"center",children:s.jsx(Un,{descriptor:{resourceType:_,filter:S??null,order:f}},`${_}:${JSON.stringify(S??null)}`)}):A==="sessionResourceGrid"?s.jsx(Jn,{descriptor:{resourceType:_,filter:S??null,order:f,gridView:b},onChangeViewParams:K,disableSessionDetail:!0},`${_}:${JSON.stringify(S??null)}`):C.kind==="deploymentNodes"?s.jsx(zn,{descriptor:{resourceType:_,filter:S??null,order:f},onChangeOrder:$=>T($??null),disableNavigation:!0},`${_}:${JSON.stringify(S??null)}`):C.kind==="sessionNodes"?s.jsx(Qn,{descriptor:{resourceType:_,filter:S??null,order:f},onChangeOrder:$=>T($??null),disableSessionDetail:!0},`${_}:${JSON.stringify(S??null)}`):s.jsx(Wn,{descriptor:{resourceType:_,filter:S??null,order:f},onChangeOrder:$=>T($??null)},`${_}:${JSON.stringify(S??null)}`)})},`${A}:${_}:${JSON.stringify(S??null)}`):null,e[160]=C.kind,e[161]=C.labelKey,e[162]=S,e[163]=b,e[164]=l,e[165]=f,e[166]=A,e[167]=_,e[168]=a,e[169]=fe):fe=e[169];let Se;e[170]!==ye||e[171]!==fe?(Se=s.jsx(G,{direction:"column",align:"stretch",gap:"xs",children:s.jsx("div",{style:ye,children:fe})}),e[170]=ye,e[171]=fe,e[172]=Se):Se=e[172];let xe;return e[173]!==N||e[174]!==z||e[175]!==De||e[176]!==be||e[177]!==_e||e[178]!==W||e[179]!==we||e[180]!==Ce||e[181]!==me||e[182]!==Se?(xe=s.jsxs(N,{open:z,width:De,title:be,okText:_e,onOk:W,onCancel:we,afterClose:Ce,children:[me,Se]}),e[173]=N,e[174]=z,e[175]=De,e[176]=be,e[177]=_e,e[178]=W,e[179]=we,e[180]=Ce,e[181]=me,e[182]=Se,e[183]=xe):xe=e[183],xe};/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */const Aa=({persistedLayout:n,defaultLayout:e,renderableIds:l})=>{const o=new Set(n.map(t=>t.id));return[...n.filter(t=>l.has(t.id)),...e.filter(t=>!o.has(t.id))]},Ia=(n,e)=>{const l=new Set(n.map(t=>t.id)),o=[...n];return e.forEach((t,r)=>{l.has(t.id)||o.splice(Math.min(r,o.length),0,t)}),o},Na=()=>{"use memo";const n=U.c(25),{t:e}=Fe(),{token:l}=Ge(),o=wn();let t;n[0]===Symbol.for("react.memo_cache_sentinel")?(t=["vhostInfo"],n[0]=t):t=n[0];let r;n[1]!==o?(r={queryKey:t,queryFn:()=>o.vfolder.list_hosts()},n[1]=o,n[2]=r):r=n[2];const{data:d}=Vn(r);let i;n[3]!==(d==null?void 0:d.volume_info)?(i=Kl(Ll((d==null?void 0:d.volume_info)??{}),Ra),n[3]=d==null?void 0:d.volume_info,n[4]=i):i=n[4];const y=i;let m;n[5]!==y?(m=y?{id:y[0],...y[1]}:void 0,n[5]=y,n[6]=m):m=n[6];const a=m;let c;n[7]!==l?(c=l("--spacing-8"),n[7]=l,n[8]=c):c=n[8];let g;n[9]!==l?(g=l("--spacing-4"),n[9]=l,n[10]=g):g=n[10];let u;n[11]!==c||n[12]!==g?(u={paddingInline:c,paddingBottom:g},n[11]=c,n[12]=g,n[13]=u):u=n[13];let p;n[14]!==e?(p=e("data.QuotaPerStorageVolume"),n[14]=e,n[15]=p):p=n[15];let F;n[16]!==p?(F=s.jsx(cn,{title:p}),n[16]=p,n[17]=F):F=n[17];let k;n[18]!==a||n[19]!==e?(k=a?s.jsx(Al,{defaultVolumeInfo:a}):s.jsx(Il,{title:e("storageHost.QuotaDoesNotSupported"),isCompact:!0}),n[18]=a,n[19]=e,n[20]=k):k=n[20];let f;return n[21]!==u||n[22]!==F||n[23]!==k?(f=s.jsxs(G,{direction:"column",align:"stretch",style:u,children:[F,k]}),n[21]=u,n[22]=F,n[23]=k,n[24]=f):f=n[24],f};function Ra(n){const[,e]=n;return Pn(e==null?void 0:e.capabilities,"quota")}const Xn=(function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"name"}],e={alias:null,args:null,kind:"ScalarField",name:"max_vfolder_count",storageKey:null},l=[e],o=[{kind:"Variable",name:"name",variableName:"name"}],t=[e,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}];return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"StorageStatusPanelCardQuery",selections:[{alias:null,args:null,concreteType:"UserResourcePolicy",kind:"LinkedField",name:"user_resource_policy",plural:!1,selections:l,storageKey:null},{alias:null,args:o,concreteType:"ProjectResourcePolicy",kind:"LinkedField",name:"project_resource_policy",plural:!1,selections:l,storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"StorageStatusPanelCardQuery",selections:[{alias:null,args:null,concreteType:"UserResourcePolicy",kind:"LinkedField",name:"user_resource_policy",plural:!1,selections:t,storageKey:null},{alias:null,args:o,concreteType:"ProjectResourcePolicy",kind:"LinkedField",name:"project_resource_policy",plural:!1,selections:t,storageKey:null}]},params:{cacheID:"6a4458681167a38a930cf05173cf0d90",id:null,metadata:{},name:"StorageStatusPanelCardQuery",operationKind:"query",text:`query StorageStatusPanelCardQuery(
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
`}}})();Xn.hash="33191e01e0635b3635f28c7383463c39";const kn=90,xa=({fetchKey:n,onRequestBadgeClick:e,style:l,...o})=>{const{t}=Fe(),{token:r}=Ge(),d=wn(),i=Je();if(!i.name)throw new Error("Project name is required for StorageStatusPanelCard");if(!i.id)throw new Error("Project ID is required for StorageStatusPanelCard");const y=V.useDeferredValue(n),[m,{updateInvitations:a}]=Nl(),c=m.length;Rl(()=>{a()},[n]);const g=b=>Pn(["delete-ongoing","delete-complete","delete-error"],b),{data:u}=Vn({queryKey:["vfolders",{deferredFetchKey:y,id:i.id}],queryFn:()=>{if(!(i!=null&&i.id))throw new Error("Project ID is required for StorageStatusPanelCard");return d.vfolder.list(i.id)}}),p=u==null?void 0:u.filter(b=>b.is_owner&&b.ownership_type==="user"&&!g(b.status)).length,F=u==null?void 0:u.filter(b=>b.ownership_type==="group"&&!g(b.status)).length,k=u==null?void 0:u.filter(b=>!b.is_owner&&b.ownership_type==="user"&&!g(b.status)).length,{user_resource_policy:f,project_resource_policy:T}=Xe.useLazyLoadQuery(Xn,{name:i.name});return s.jsxs(G,{direction:"column",align:"stretch",style:{paddingInline:r("--spacing-8"),paddingBottom:r("--spacing-4"),...l},...o,children:[s.jsx(cn,{title:t("data.FolderStatus")}),s.jsxs(xn,{rowGap:r("--spacing-8"),columnGap:r("--spacing-8"),dividerColor:r("--color-border-emphasized"),dividerInset:yn(r("--spacing-2")),dividerWidth:parseFloat(r("--border-width")),children:[s.jsx(Sn,{title:t("data.MyFolders"),value:p,unit:f!=null&&f.max_vfolder_count?`/ ${f==null?void 0:f.max_vfolder_count}`:void 0,style:{maxWidth:kn},color:r("--color-text-primary")}),s.jsx(Sn,{title:t("data.ProjectFolders"),value:F,unit:T!=null&&T.max_vfolder_count?`/ ${T==null?void 0:T.max_vfolder_count}`:void 0,style:{maxWidth:kn},color:r("--color-text-primary")}),s.jsx(Sn,{title:c>0?s.jsx("a",{onClick:()=>{e==null||e()},children:s.jsx(xl,{content:t("data.InvitedFoldersTooltip",{count:c}),placement:"above",alignment:"end",children:s.jsx(jl,{count:`+${c}`,variant:"error",offset:[-yn(r("--spacing-2")),-yn(r("--spacing-2"))],style:{zIndex:50},title:t("data.InvitedFoldersTooltip",{count:c}),children:s.jsx(pn,{size:"lg",children:t("data.InvitedFolders")})})})}):s.jsx(pn,{size:"lg",children:t("data.InvitedFolders")}),value:s.jsx(pn,{size:"4xl",children:k}),style:{maxWidth:kn}})]})]})},Xa=()=>{"use memo";const n=U.c(146),{token:e}=Ge(),{t:l}=Fe(),o=Je(),t=El(),r=Dn(),d=gn(),i=jn(),[y,m]=Nn(),a=V.useDeferredValue(y),[c,g]=V.useTransition(),u=c||y!==a,[p,F]=We("dashboard_board_items"),[k]=We("experimental_custom_dashboard_panels"),[f,T]=Ln(hn),b=Dl(wl);let K,_;n[0]!==k||n[1]!==b||n[2]!==T?(K=()=>{if(k)return b(s.jsx(Xl,{})),()=>{b(null),T(!1)}},_=[k,b,T],n[0]=k,n[1]=b,n[2]=T,n[3]=K,n[4]=_):(K=n[3],_=n[4]),V.useEffect(K,_);let A;n[5]===Symbol.for("react.memo_cache_sentinel")?(A={open:!1},n[5]=A):A=n[5];const[S,C]=V.useState(A),j=V.useRef(null),R=!!k;let I;n[6]===Symbol.for("react.memo_cache_sentinel")?(I=M=>C({open:!0,panel:M}),n[6]=I):I=n[6];let x;n[7]!==a||n[8]!==R?(x={enabled:R,fetchKey:a,onRequestEdit:I},n[7]=a,n[8]=R,n[9]=x):x=n[9];const{panels:N,availableResources:v,gridEnabled:h,customDefaultLayout:L,customContentById:E,addPanel:D,updatePanel:w,removePanel:P}=Ca(x),O=Vl();let z;n[10]===Symbol.for("react.memo_cache_sentinel")?(z=Bn,n[10]=z):z=n[10];const De=`project:${o.id}`,be=t||"default",_e=!O;let W;n[11]!==r?(W=tn(r,"superadmin"),n[11]=r,n[12]=W):W=n[12];const we=`schedulable == true & status == "ALIVE" & scaling_group == "${t}"`;let Ce;n[13]!==W||n[14]!==we||n[15]!==De||n[16]!==be||n[17]!==_e?(Ce={scopeId:De,resourceGroup:be,skipTotalResourceWithinResourceGroup:_e,isSuperAdmin:W,agentNodeFilter:we,aliveAgentFilter:'status == "ALIVE"',schedulableAgentFilter:'status == "ALIVE" & schedulable == true'},n[13]=W,n[14]=we,n[15]=De,n[16]=be,n[17]=_e,n[18]=Ce):Ce=n[18];const he=a===ql?"store-and-network":"network-only";let Te;n[19]!==a||n[20]!==he?(Te={fetchPolicy:he,fetchKey:a},n[19]=a,n[20]=he,n[21]=Te):Te=n[21];const B=Xe.useLazyLoadQuery(z,Ce,Te);let J;n[22]!==m?(J=()=>{g(()=>{m()})},n[22]=m,n[23]=J):J=n[23],Pl(J,15e3);let Ke;if(n[24]!==i||n[25]!==o||n[26]!==E||n[27]!==L||n[28]!==a||n[29]!==O||n[30]!==u||n[31]!==p||n[32]!==B||n[33]!==l||n[34]!==e||n[35]!==m||n[36]!==r||n[37]!==d){let M;n[39]!==e?(M=e("--spacing-5"),n[39]=e,n[40]=M):M=n[40];const ne=`0px ${M}`;let le;n[41]!==ne?(le=s.jsx(Ee,{style:{padding:ne}}),n[41]=ne,n[42]=le):le=n[42];let ae;n[43]!==l||n[44]!==r?(ae=tn(r,"superadmin")?l("session.ActiveSessions"):l("session.MySessions"),n[43]=l,n[44]=r,n[45]=ae):ae=n[45];let te;n[46]!==u||n[47]!==B||n[48]!==ae?(te=s.jsx(Wl,{queryRef:B,isRefetching:u,title:ae}),n[46]=u,n[47]=B,n[48]=ae,n[49]=te):te=n[49];let Ae;n[50]!==le||n[51]!==te?(Ae=s.jsx(V.Suspense,{fallback:le,children:te}),n[50]=le,n[51]=te,n[52]=Ae):Ae=n[52];let Ie;n[53]!==l?(Ie=l("webui.menu.MyResources"),n[53]=l,n[54]=Ie):Ie=n[54];let se;n[55]!==e?(se=e("--spacing-5"),n[55]=e,n[56]=se):se=n[56];let re;n[57]!==se?(re=s.jsx(Ee,{style:{padding:se}}),n[57]=se,n[58]=re):re=n[58];let ie;n[59]!==a||n[60]!==u?(ie=s.jsx(Gl,{fetchKey:a,refetching:u}),n[59]=a,n[60]=u,n[61]=ie):ie=n[61];let oe;n[62]!==re||n[63]!==ie?(oe=s.jsx(V.Suspense,{fallback:re,children:ie}),n[62]=re,n[63]=ie,n[64]=oe):oe=n[64];let Ne;n[65]!==Ie||n[66]!==oe?(Ne=s.jsx(He,{title:Ie,status:"error",children:oe}),n[65]=Ie,n[66]=oe,n[67]=Ne):Ne=n[67];let de;n[68]!==l?(de=l("webui.menu.MyResourcesInResourceGroup"),n[68]=l,n[69]=de):de=n[69];let ue;n[70]!==e?(ue=e("--spacing-5"),n[70]=e,n[71]=ue):ue=n[71];let ce;n[72]!==ue?(ce=s.jsx(Ee,{style:{padding:ue}}),n[72]=ue,n[73]=ce):ce=n[73];let me;n[74]!==a||n[75]!==u?(me=s.jsx(Ul,{fetchKey:a,refetching:u}),n[74]=a,n[75]=u,n[76]=me):me=n[76];let Re;n[77]!==ce||n[78]!==me?(Re=s.jsx(V.Suspense,{fallback:ce,children:me}),n[77]=ce,n[78]=me,n[79]=Re):Re=n[79];let Oe;n[80]!==de||n[81]!==Re?(Oe=s.jsx(He,{title:de,status:"error",children:Re}),n[80]=de,n[81]=Re,n[82]=Oe):Oe=n[82];let ge;n[83]!==l?(ge=l("data.FolderStatus"),n[83]=l,n[84]=ge):ge=n[84];let pe;n[85]!==e?(pe=e("--spacing-5"),n[85]=e,n[86]=pe):pe=n[86];let ye;n[87]!==pe?(ye=s.jsx(Ee,{style:{padding:pe}}),n[87]=pe,n[88]=ye):ye=n[88];let fe;n[89]!==i||n[90]!==d?(fe=()=>{d({pathname:i("data"),search:new URLSearchParams({invitation:"true"}).toString()})},n[89]=i,n[90]=d,n[91]=fe):fe=n[91];let Se;n[92]!==a||n[93]!==fe?(Se=s.jsx(xa,{fetchKey:a,onRequestBadgeClick:fe}),n[92]=a,n[93]=fe,n[94]=Se):Se=n[94];let xe;n[95]!==ye||n[96]!==Se?(xe=s.jsx(V.Suspense,{fallback:ye,children:Se}),n[95]=ye,n[96]=Se,n[97]=xe):xe=n[97];let Ue;n[98]!==ge||n[99]!==xe?(Ue=s.jsx(He,{title:ge,status:"error",children:xe}),n[98]=ge,n[99]=xe,n[100]=Ue):Ue=n[100];let Be;n[101]!==l?(Be=l("data.QuotaPerStorageVolume"),n[101]=l,n[102]=Be):Be=n[102];let $;n[103]!==e?($=e("--spacing-5"),n[103]=e,n[104]=$):$=n[104];let Q;n[105]!==$?(Q=s.jsx(Ee,{style:{padding:$}}),n[105]=$,n[106]=Q):Q=n[106];let Ye;n[107]===Symbol.for("react.memo_cache_sentinel")?(Ye=s.jsx(Na,{}),n[107]=Ye):Ye=n[107];let Ve;n[108]!==Q?(Ve=s.jsx(V.Suspense,{fallback:Q,children:Ye}),n[108]=Q,n[109]=Ve):Ve=n[109];let qe;n[110]!==Be||n[111]!==Ve?(qe=s.jsx(He,{title:Be,status:"error",children:Ve}),n[110]=Be,n[111]=Ve,n[112]=qe):qe=n[112];let Pe;n[113]!==o?(Pe=Ml(o),n[113]=o,n[114]=Pe):Pe=n[114];let je;n[115]!==u||n[116]!==B||n[117]!==Pe?(je=s.jsx(Jl,{queryRef:B,isRefetching:u,project:Pe}),n[115]=u,n[116]=B,n[117]=Pe,n[118]=je):je=n[118];const ze=Cn([{id:"mySession",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:Ae}},{id:"myResource",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:Ne}},{id:"myResourceWithinResourceGroup",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:Oe}},{id:"folderStatus",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:Ue}},{id:"quotaPerStorageVolume",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:qe}},O&&{id:"totalResourceWithinResourceGroup",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:B.TotalResourceWithinResourceGroupFragment&&s.jsx(Bl,{queryRef:B.TotalResourceWithinResourceGroupFragment,refetching:u})}},tn(r,"superadmin")&&B.AgentStatsFragment&&{id:"agentStats",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:s.jsx(V.Suspense,{fallback:s.jsx(Ee,{style:{padding:`0px ${e("--spacing-5")}`}}),children:s.jsx(zl,{queryRef:B.AgentStatsFragment,isRefetching:u})})}},tn(r,"superadmin")&&{id:"activeAgents",rowSpan:4,columnSpan:4,definition:{minRowSpan:3,minColumnSpan:4},data:{content:s.jsx(V.Suspense,{fallback:s.jsx(Ee,{style:{padding:`0px ${e("--spacing-5")}`}}),children:s.jsx(Ql,{fetchKey:a,onChangeFetchKey:()=>m()})})}},{id:"recentlyCreatedSession",rowSpan:3,columnSpan:4,definition:{minRowSpan:2,minColumnSpan:2},data:{content:je}}]),q=new Map;$l(ze,Qe=>{q.set(Qe.id,Qe.data)}),E.forEach((Qe,ln)=>{q.set(ln,{content:Qe})});const Ze=[...fn(ze,ja),...L],Zn=Aa({persistedLayout:Array.isArray(p)?p:[],defaultLayout:Ze,renderableIds:new Set(q.keys())});Ke=Cn(fn(Zn,Qe=>{const ln=q.get(Qe.id);return ln?{...Qe,data:ln}:void 0})),n[24]=i,n[25]=o,n[26]=E,n[27]=L,n[28]=a,n[29]=O,n[30]=u,n[31]=p,n[32]=B,n[33]=l,n[34]=e,n[35]=m,n[36]=r,n[37]=d,n[38]=Ke}else Ke=n[38];const ve=Ke;let Y;n[119]===Symbol.for("react.memo_cache_sentinel")?(Y={width:"100%"},n[119]=Y):Y=n[119];let Le;n[120]===Symbol.for("react.memo_cache_sentinel")?(Le={flex:1,minWidth:0},n[120]=Le):Le=n[120];let H;n[121]!==p||n[122]!==F?(H=M=>{F(Ia(fn(M.detail.items,Ea),Array.isArray(p)?p:[]))},n[121]=p,n[122]=F,n[123]=H):H=n[123];let X;n[124]!==ve||n[125]!==H?(X=s.jsx("div",{ref:j,style:Le,children:s.jsx(Hl,{movable:!0,resizable:!0,bordered:!0,items:ve,onItemsChange:H})}),n[124]=ve,n[125]=H,n[126]=X):X=n[126];let Z;n[127]!==v||n[128]!==k||n[129]!==f||n[130]!==h||n[131]!==N||n[132]!==P||n[133]!==F?(Z=k&&f?s.jsx(Ka,{panels:N,availableResources:v,gridEnabled:h,onRequestAdd:()=>C({open:!0}),onRequestEdit:M=>C({open:!0,panel:M}),onRemove:P,onResetLayout:()=>F([])}):null,n[127]=v,n[128]=k,n[129]=f,n[130]=h,n[131]=N,n[132]=P,n[133]=F,n[134]=Z):Z=n[134];let ee;n[135]!==D||n[136]!==v||n[137]!==k||n[138]!==h||n[139]!==S||n[140]!==w?(ee=k?s.jsx(Ol,{children:s.jsx(La,{open:S.open,initialPanel:S.panel,availableResources:v,gridEnabled:h,onRequestClose:()=>C({open:!1}),onSubmit:M=>{S.panel?w(S.panel.id,M):(D(M),requestAnimationFrame(()=>{var ne;(ne=j.current)==null||ne.scrollIntoView({block:"end",behavior:"smooth"})}))}})}):null,n[135]=D,n[136]=v,n[137]=k,n[138]=h,n[139]=S,n[140]=w,n[141]=ee):ee=n[141];let Me;return n[142]!==X||n[143]!==Z||n[144]!==ee?(Me=s.jsxs(G,{direction:"row",align:"stretch",gap:"lg",style:Y,children:[X,Z,ee]}),n[142]=X,n[143]=Z,n[144]=ee,n[145]=Me):Me=n[145],Me};function ja(n){return Mn(n,"data")}function Ea(n){return Mn(n,"data")}export{Xa as default};
//# sourceMappingURL=DashboardPage-BZlRSI7C.js.map
