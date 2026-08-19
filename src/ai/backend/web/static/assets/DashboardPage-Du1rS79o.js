import{ag as J,t as R,j as n,ah as O,ai as E,aj as Y,i as Z,u as D,a as M,ak as $,ae as w,al as ee,am as P,a9 as G,B as W,an as Q,r as _,a3 as ne,ao as ae,k as q,ap as te,T as x,aq as se,ar as le,as as ie,at as oe,m as re,w as de,x as ue,au as ce,aa as me,av as ge,aw as K,ax as pe,ay as Se,a7 as B,az as C,aA as ye,aB as Fe,aC as fe,ab as ke,ac as V,af as _e}from"./index-DB7yUW94.js";import{S as ve,A as Ce,a as he,R as Le}from"./SessionCountDashboardItem-DCqGZ_o8.js";import{B as Ie}from"./BAIBoard-DZgyXYP0.js";import{Q as Te}from"./QuotaPerStorageVolumePanelCard-Zd0iYgl1.js";import{B as b}from"./BAIPanelItem-8rJxVaPx.js";import"./AgentList--zuMQEUW.js";import"./BAIAdminResourceGroupSelect-C2WMzGiy.js";import"./SessionDetailDrawer-3BikG1o_.js";import"./BAIId-DEscoFqK.js";import"./corner-down-left-YcyydeqR.js";import"./FolderLink-DJPzhdHs.js";import"./zip-DRoFeMJl.js";import"./unzip-kgVO-3Vy.js";import"./ScopedAuditLog-BgqNEK4R.js";import"./camelCase-D3Ek1WIG.js";import"./BAIGraphQLPropertyFilter-URVW9R-R.js";import"./union-CChSQL5X.js";import"./WarningOutlined-BN1g72Bn.js";const A=({title:e,status:a="error",children:d,style:g})=>{const{t:s}=J(),{token:t}=R.useToken();return n.jsx(O,{fallbackRender:()=>n.jsx("div",{"data-bai-board-item-status":a,style:{height:"100%",paddingInline:t.paddingXL,paddingBottom:t.padding,...g},children:n.jsx(E,{title:e,extra:n.jsx(Y,{title:s("comp:BAIBoardItemErrorBoundary.UnexpectedError"),type:a})})}),children:d})},z=(function(){var e={defaultValue:null,kind:"LocalArgument",name:"agentNodeFilter"},a={defaultValue:null,kind:"LocalArgument",name:"isSuperAdmin"},d={defaultValue:null,kind:"LocalArgument",name:"resourceGroup"},g={defaultValue:null,kind:"LocalArgument",name:"scopeId"},s={defaultValue:null,kind:"LocalArgument",name:"skipTotalResourceWithinResourceGroup"},t=[{kind:"Variable",name:"scopeId",variableName:"scopeId"}],u={kind:"Literal",name:"first",value:0},y={kind:"Variable",name:"scope_id",variableName:"scopeId"},l={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},F=[l],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},v={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},h=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],p={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},m=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[i,S,c,o],storageKey:null}],storageKey:null},l],N=[i,o,{alias:null,args:null,kind:"ScalarField",name:"available_slots",storageKey:null},k,f];return{fragment:{argumentDefinitions:[e,a,d,g,s],kind:"Fragment",metadata:null,name:"DashboardPageQuery",selections:[{args:t,kind:"FragmentSpread",name:"SessionCountDashboardItemFragment"},{args:t,kind:"FragmentSpread",name:"RecentlyCreatedSessionFragment"},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{fragment:{kind:"InlineFragment",selections:[{args:[{kind:"Variable",name:"agentNodeFilter",variableName:"agentNodeFilter"},{kind:"Variable",name:"isSuperAdmin",variableName:"isSuperAdmin"},{kind:"Variable",name:"resourceGroup",variableName:"resourceGroup"}],kind:"FragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{fragment:{kind:"InlineFragment",selections:[{args:null,kind:"FragmentSpread",name:"AgentStatsFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"AgentStatsFragment"}]}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[g,d,s,a,e],kind:"Operation",name:"DashboardPageQuery",selections:[{alias:"myInteractive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},u,y],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:F,storageKey:null},{alias:"myBatch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},u,y],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:F,storageKey:null},{alias:"myInference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},u,y],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:F,storageKey:null},{alias:"myUpload",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},u,y],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:F,storageKey:null},{alias:null,args:[{kind:"Literal",name:"filter",value:'status == "running"'},{kind:"Literal",name:"first",value:5},{kind:"Literal",name:"order",value:"-created_at"},y],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[i,S,c,o,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},r,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},k,{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},v,{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},i,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},c,{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:h,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:h,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},v,i],storageKey:null},S,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},o,r,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},p,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[S,c,i],storageKey:null}],storageKey:null},l],storageKey:null},f,p,{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:m,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:m,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{condition:"isSuperAdmin",kind:"Condition",passingValue:!1,selections:[{alias:null,args:[{kind:"Literal",name:"filter",value:"schedulable == true"},{kind:"Literal",name:"limit",value:1e3},{kind:"Literal",name:"offset",value:0},{kind:"Variable",name:"scaling_group",variableName:"resourceGroup"},{kind:"Literal",name:"status",value:"ALIVE"}],concreteType:"AgentSummaryList",kind:"LinkedField",name:"agent_summary_list",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentSummary",kind:"LinkedField",name:"items",plural:!0,selections:N,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"total_count",storageKey:null}],storageKey:null}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"agentNodeFilter"},{kind:"Literal",name:"first",value:100}],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AgentNode",kind:"LinkedField",name:"node",plural:!1,selections:N,storageKey:null}],storageKey:null},l],storageKey:null}]}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{alias:null,args:null,concreteType:"AgentStats",kind:"LinkedField",name:"agentStats",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentResource",kind:"LinkedField",name:"totalResource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"free",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capacity",storageKey:null}],storageKey:null}],storageKey:null}]}]},params:{cacheID:"94e72a3e59948f23b3181bf31c5a5a8e",id:null,metadata:{},name:"DashboardPageQuery",operationKind:"query",text:`query DashboardPageQuery(
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
`}}})();z.hash="c569b4f4d4f8ee32a4f369157d8a1348";const Ke=()=>{"use memo";const e=Z.c(21),{t:a}=D(),{token:d}=R.useToken(),g=M();let s;e[0]===Symbol.for("react.memo_cache_sentinel")?(s=["vhostInfo"],e[0]=s):s=e[0];let t;e[1]!==g?(t={queryKey:s,queryFn:()=>g.vfolder.list_hosts()},e[1]=g,e[2]=t):t=e[2];const{data:u}=$(t);let y;e[3]!==(u==null?void 0:u.volume_info)?(y=w(ee((u==null?void 0:u.volume_info)??{}),Ae),e[3]=u==null?void 0:u.volume_info,e[4]=y):y=e[4];const l=y;let F;e[5]!==l?(F=l?{id:l[0],...l[1]}:void 0,e[5]=l,e[6]=F):F=e[6];const i=F;let S;e[7]!==d.padding||e[8]!==d.paddingXL?(S={paddingInline:d.paddingXL,paddingBottom:d.padding},e[7]=d.padding,e[8]=d.paddingXL,e[9]=S):S=e[9];let c;e[10]!==a?(c=a("data.QuotaPerStorageVolume"),e[10]=a,e[11]=c):c=e[11];let o;e[12]!==c?(o=n.jsx(E,{title:c}),e[12]=c,e[13]=o):o=e[13];let r;e[14]!==i||e[15]!==a?(r=i?n.jsx(Te,{defaultVolumeInfo:i}):n.jsx(P,{image:P.PRESENTED_IMAGE_SIMPLE,description:a("storageHost.QuotaDoesNotSupported")}),e[14]=i,e[15]=a,e[16]=r):r=e[16];let k;return e[17]!==S||e[18]!==o||e[19]!==r?(k=n.jsxs(W,{direction:"column",align:"stretch",style:S,children:[o,r]}),e[17]=S,e[18]=o,e[19]=r,e[20]=k):k=e[20],k};function Ae(e){const[,a]=e;return G(a==null?void 0:a.capabilities,"quota")}const U=(function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"name"}],a={alias:null,args:null,kind:"ScalarField",name:"max_vfolder_count",storageKey:null},d=[a],g=[{kind:"Variable",name:"name",variableName:"name"}],s=[a,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"StorageStatusPanelCardQuery",selections:[{alias:null,args:null,concreteType:"UserResourcePolicy",kind:"LinkedField",name:"user_resource_policy",plural:!1,selections:d,storageKey:null},{alias:null,args:g,concreteType:"ProjectResourcePolicy",kind:"LinkedField",name:"project_resource_policy",plural:!1,selections:d,storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"StorageStatusPanelCardQuery",selections:[{alias:null,args:null,concreteType:"UserResourcePolicy",kind:"LinkedField",name:"user_resource_policy",plural:!1,selections:s,storageKey:null},{alias:null,args:g,concreteType:"ProjectResourcePolicy",kind:"LinkedField",name:"project_resource_policy",plural:!1,selections:s,storageKey:null}]},params:{cacheID:"6a4458681167a38a930cf05173cf0d90",id:null,metadata:{},name:"StorageStatusPanelCardQuery",operationKind:"query",text:`query StorageStatusPanelCardQuery(
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
`}}})();U.hash="33191e01e0635b3635f28c7383463c39";const Re=ie(({css:e,token:a})=>({invitationTooltip:e`
    .ant-tooltip-arrow {
      right: 0;
      bottom: ${a.size}px;
    }
    .ant-tooltip-content {
      left: ${a.sizeXS}px;
      bottom: ${a.size}px;
    }
  `})),j=90,Ne=({fetchKey:e,onRequestBadgeClick:a,style:d,...g})=>{const{t:s}=D(),{token:t}=R.useToken(),{styles:u}=Re(),y=M(),l=Q();if(!l.name)throw new Error("Project name is required for StorageStatusPanelCard");if(!l.id)throw new Error("Project ID is required for StorageStatusPanelCard");const F=_.useDeferredValue(e),[i,{updateInvitations:S}]=ne(),c=i.length;ae(()=>{S()},[e]);const o=m=>G(["delete-ongoing","delete-complete","delete-error"],m),{data:r}=$({queryKey:["vfolders",{deferredFetchKey:F,id:l.id}],queryFn:()=>{if(!(l!=null&&l.id))throw new Error("Project ID is required for StorageStatusPanelCard");return y.vfolder.list(l.id)}}),k=r==null?void 0:r.filter(m=>m.is_owner&&m.ownership_type==="user"&&!o(m.status)).length,v=r==null?void 0:r.filter(m=>m.ownership_type==="group"&&!o(m.status)).length,h=r==null?void 0:r.filter(m=>!m.is_owner&&m.ownership_type==="user"&&!o(m.status)).length,{user_resource_policy:p,project_resource_policy:f}=q.useLazyLoadQuery(U,{name:l.name});return n.jsxs(W,{direction:"column",align:"stretch",style:{paddingInline:t.paddingXL,paddingBottom:t.padding,...d},...g,children:[n.jsx(E,{title:s("data.FolderStatus")}),n.jsxs(te,{rowGap:t.marginXL,columnGap:t.marginXL,dividerColor:t.colorBorder,dividerInset:t.marginXS,dividerWidth:t.lineWidth,children:[n.jsx(b,{title:s("data.MyFolders"),value:k,unit:p!=null&&p.max_vfolder_count?`/ ${p==null?void 0:p.max_vfolder_count}`:void 0,style:{maxWidth:j},color:t.colorText}),n.jsx(b,{title:s("data.ProjectFolders"),value:v,unit:f!=null&&f.max_vfolder_count?`/ ${f==null?void 0:f.max_vfolder_count}`:void 0,style:{maxWidth:j},color:t.colorText}),n.jsx(b,{title:c>0?n.jsx("a",{onClick:()=>{a==null||a()},children:n.jsx(se,{title:s("data.InvitedFoldersTooltip",{count:c}),rootClassName:u.invitationTooltip,placement:"topRight",children:n.jsx(le,{count:`+${c}`,offset:[-`${t.sizeXS}`,-`${t.sizeXS}`],style:{zIndex:50},children:n.jsx(x.Text,{style:{fontSize:t.fontSizeHeading5},children:s("data.InvitedFolders")})})})}):n.jsx(x.Text,{style:{fontSize:t.fontSizeHeading5},children:s("data.InvitedFolders")}),value:n.jsx(x.Text,{style:{fontSize:t.fontSizeHeading1},children:h}),style:{maxWidth:j}})]})]})},He=()=>{const{token:e}=R.useToken(),{t:a}=D(),d=Q(),g=oe(),s=re(),t=M(),u=de(),y=ue(),[l,F]=ce(),i=_.useDeferredValue(l),[S,c]=_.useTransition(),o=S||l!==i,[r,k]=me("dashboard_board_items"),v=ge(),h=t.supports("agent-stats"),p=q.useLazyLoadQuery(z,{scopeId:`project:${d.id}`,resourceGroup:g||"default",skipTotalResourceWithinResourceGroup:!v,isSuperAdmin:K(s,"superadmin"),agentNodeFilter:`schedulable == true & status == "ALIVE" & scaling_group == "${g}"`},{fetchPolicy:i===pe?"store-and-network":"network-only",fetchKey:i});Se(()=>{c(()=>{F()})},15e3);const f=B([{id:"mySession",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(_.Suspense,{fallback:n.jsx(C,{active:!0,style:{padding:`0px ${e.marginMD}px`}}),children:n.jsx(ve,{queryRef:p,isRefetching:o,title:K(s,"superadmin")?a("session.ActiveSessions"):a("session.MySessions")})})}},{id:"myResource",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(A,{title:a("webui.menu.MyResources"),status:"error",children:n.jsx(_.Suspense,{fallback:n.jsx(C,{active:!0,style:{padding:e.marginMD}}),children:n.jsx(ye,{fetchKey:i,refetching:o})})})}},{id:"myResourceWithinResourceGroup",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(A,{title:a("webui.menu.MyResourcesInResourceGroup"),status:"error",children:n.jsx(_.Suspense,{fallback:n.jsx(C,{active:!0,style:{padding:e.marginMD}}),children:n.jsx(Fe,{fetchKey:i,refetching:o})})})}},{id:"folderStatus",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(A,{title:a("data.FolderStatus"),status:"error",children:n.jsx(_.Suspense,{fallback:n.jsx(C,{active:!0,style:{padding:e.marginMD}}),children:n.jsx(Ne,{fetchKey:i,onRequestBadgeClick:()=>{u({pathname:y("data"),search:new URLSearchParams({invitation:"true"}).toString()})}})})})}},{id:"quotaPerStorageVolume",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(A,{title:a("data.QuotaPerStorageVolume"),status:"error",children:n.jsx(_.Suspense,{fallback:n.jsx(C,{active:!0,style:{padding:e.marginMD}}),children:n.jsx(Ke,{})})})}},v&&{id:"totalResourceWithinResourceGroup",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:p.TotalResourceWithinResourceGroupFragment&&n.jsx(fe,{queryRef:p.TotalResourceWithinResourceGroupFragment,refetching:o})}},K(s,"superadmin")&&h&&p.AgentStatsFragment&&{id:"agentStats",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(_.Suspense,{fallback:n.jsx(C,{active:!0,style:{padding:`0px ${e.marginMD}px`}}),children:n.jsx(Ce,{queryRef:p.AgentStatsFragment,isRefetching:o})})}},K(s,"superadmin")&&{id:"activeAgents",rowSpan:4,columnSpan:4,definition:{minRowSpan:3,minColumnSpan:4},data:{content:n.jsx(_.Suspense,{fallback:n.jsx(C,{active:!0,style:{padding:`0px ${e.marginMD}px`}}),children:n.jsx(he,{fetchKey:i,onChangeFetchKey:()=>F()})})}},{id:"recentlyCreatedSession",rowSpan:3,columnSpan:4,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(Le,{queryRef:p,isRefetching:o})}}]),m=ke(f,L=>!w(r,I=>I.id===L.id)),X=[...B(V(r,L=>{var T;const I=(T=w(f,H=>H.id===L.id))==null?void 0:T.data;return I?{...L,data:I}:void 0})),...m];return n.jsx(Ie,{movable:!0,resizable:!0,bordered:!0,items:X,onItemsChange:L=>{const I=[...L.detail.items];k(V(I,T=>_e(T,"data")))}})};export{He as default};
//# sourceMappingURL=DashboardPage-Du1rS79o.js.map
