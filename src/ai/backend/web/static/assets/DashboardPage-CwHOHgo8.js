import{ad as U,t as K,j as n,ae as X,af as w,ag as H,h as J,u as E,a as j,l as P,ab as b,ah as O,ai as D,a3 as V,B as $,aj as G,r as v,_ as Y,ak as Z,i as W,al as ee,T as N,am as ne,an as ae,ao as te,ap as se,aq as le,p as ie,ar as oe,a4 as re,as as de,at as T,au as ue,av as ce,a1 as M,aw as L,ax as me,ay as ge,az as pe,a5 as Se,a6 as B,ac as ye}from"./index-r5M52Un8.js";import{S as Fe,A as _e,a as fe,R as ke}from"./SessionCountDashboardItem-CVEwLHtJ.js";import{B as ve}from"./BAIBoard-BoqMBmiL.js";import{Q as Ce}from"./QuotaPerStorageVolumePanelCard-7dG_LPZH.js";import{B as R}from"./BAIPanelItem-C4K83GwQ.js";import"./AgentList-ClOfLM8t.js";import"./BAIAdminResourceGroupSelect-CpJJPia8.js";import"./SessionDetailDrawer-DaYr_a4L.js";import"./corner-down-left-BAQMMY0X.js";import"./FolderLink-CVus6lm-.js";import"./zip-D5nKRYgG.js";import"./unzip-CowBifeB.js";import"./ScopedAuditLog-GhAcxAyr.js";import"./BAIId-DYp9TwD-.js";import"./BAIGraphQLPropertyFilter-CGIFK1tA.js";const A=({title:e,status:a="error",children:d,style:p})=>{const{t:s}=U(),{token:t}=K.useToken();return n.jsx(X,{fallbackRender:()=>n.jsx("div",{"data-bai-board-item-status":a,style:{height:"100%",paddingInline:t.paddingXL,paddingBottom:t.padding,...p},children:n.jsx(w,{title:e,extra:n.jsx(H,{title:s("comp:BAIBoardItemErrorBoundary.UnexpectedError"),type:a})})}),children:d})},Q=function(){var e={defaultValue:null,kind:"LocalArgument",name:"agentNodeFilter"},a={defaultValue:null,kind:"LocalArgument",name:"isSuperAdmin"},d={defaultValue:null,kind:"LocalArgument",name:"resourceGroup"},p={defaultValue:null,kind:"LocalArgument",name:"scopeId"},s={defaultValue:null,kind:"LocalArgument",name:"skipTotalResourceWithinResourceGroup"},t=[{kind:"Variable",name:"scopeId",variableName:"scopeId"}],u={kind:"Literal",name:"first",value:0},r={kind:"Variable",name:"scope_id",variableName:"scopeId"},l={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},c=[l],S={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},F={alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},C=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],f={alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},_=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[S,y,g,m],storageKey:null}],storageKey:null},l],i=[S,m,{alias:null,args:null,kind:"ScalarField",name:"available_slots",storageKey:null},F,f];return{fragment:{argumentDefinitions:[e,a,d,p,s],kind:"Fragment",metadata:null,name:"DashboardPageQuery",selections:[{args:t,kind:"FragmentSpread",name:"SessionCountDashboardItemFragment"},{args:t,kind:"FragmentSpread",name:"RecentlyCreatedSessionFragment"},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{fragment:{kind:"InlineFragment",selections:[{args:[{kind:"Variable",name:"agentNodeFilter",variableName:"agentNodeFilter"},{kind:"Variable",name:"isSuperAdmin",variableName:"isSuperAdmin"},{kind:"Variable",name:"resourceGroup",variableName:"resourceGroup"}],kind:"FragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{fragment:{kind:"InlineFragment",selections:[{args:null,kind:"FragmentSpread",name:"AgentStatsFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"AgentStatsFragment"}]}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[p,d,s,a,e],kind:"Operation",name:"DashboardPageQuery",selections:[{alias:"myInteractive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},u,r],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:c,storageKey:null},{alias:"myBatch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},u,r],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:c,storageKey:null},{alias:"myInference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},u,r],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:c,storageKey:null},{alias:"myUpload",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},u,r],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:c,storageKey:null},{alias:null,args:[{kind:"Literal",name:"filter",value:'status == "running"'},{kind:"Literal",name:"first",value:5},{kind:"Literal",name:"order",value:"-created_at"},r],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[S,y,g,m,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},o,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},F,{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},k,{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},S,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},g,{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:C,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:C,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},k,S],storageKey:null},y,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},m,o,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},S],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[y,g,S],storageKey:null}],storageKey:null},l],storageKey:null},f,{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:_,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:_,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{condition:"isSuperAdmin",kind:"Condition",passingValue:!1,selections:[{alias:null,args:[{kind:"Literal",name:"filter",value:"schedulable == true"},{kind:"Literal",name:"limit",value:1e3},{kind:"Literal",name:"offset",value:0},{kind:"Variable",name:"scaling_group",variableName:"resourceGroup"},{kind:"Literal",name:"status",value:"ALIVE"}],concreteType:"AgentSummaryList",kind:"LinkedField",name:"agent_summary_list",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentSummary",kind:"LinkedField",name:"items",plural:!0,selections:i,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"total_count",storageKey:null}],storageKey:null}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"agentNodeFilter"},{kind:"Literal",name:"first",value:100}],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AgentNode",kind:"LinkedField",name:"node",plural:!1,selections:i,storageKey:null}],storageKey:null},l],storageKey:null}]}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{alias:null,args:null,concreteType:"AgentStats",kind:"LinkedField",name:"agentStats",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentResource",kind:"LinkedField",name:"totalResource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"free",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capacity",storageKey:null}],storageKey:null}],storageKey:null}]}]},params:{cacheID:"4c0202c4e989036c0a3cd370f8ebaa5a",id:null,metadata:{},name:"DashboardPageQuery",operationKind:"query",text:`query DashboardPageQuery(
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
`}}}();Q.hash="c569b4f4d4f8ee32a4f369157d8a1348";const he=()=>{"use memo";const e=J.c(21),{t:a}=E(),{token:d}=K.useToken(),p=j();let s;e[0]===Symbol.for("react.memo_cache_sentinel")?(s=["vhostInfo"],e[0]=s):s=e[0];let t;e[1]!==p?(t={queryKey:s,queryFn:()=>p.vfolder.list_hosts()},e[1]=p,e[2]=t):t=e[2];const{data:u}=P(t);let r;e[3]!==(u==null?void 0:u.volume_info)?(r=b(O((u==null?void 0:u.volume_info)??{}),Le),e[3]=u==null?void 0:u.volume_info,e[4]=r):r=e[4];const l=r;let c;e[5]!==l?(c=l?{id:l[0],...l[1]}:void 0,e[5]=l,e[6]=c):c=e[6];const S=c;let y;e[7]!==d.padding||e[8]!==d.paddingXL?(y={paddingInline:d.paddingXL,paddingBottom:d.padding},e[7]=d.padding,e[8]=d.paddingXL,e[9]=y):y=e[9];let g;e[10]!==a?(g=a("data.QuotaPerStorageVolume"),e[10]=a,e[11]=g):g=e[11];let m;e[12]!==g?(m=n.jsx(w,{title:g}),e[12]=g,e[13]=m):m=e[13];let o;e[14]!==S||e[15]!==a?(o=S?n.jsx(Ce,{defaultVolumeInfo:S}):n.jsx(D,{image:D.PRESENTED_IMAGE_SIMPLE,description:a("storageHost.QuotaDoesNotSupported")}),e[14]=S,e[15]=a,e[16]=o):o=e[16];let F;return e[17]!==y||e[18]!==m||e[19]!==o?(F=n.jsxs($,{direction:"column",align:"stretch",style:y,children:[m,o]}),e[17]=y,e[18]=m,e[19]=o,e[20]=F):F=e[20],F};function Le(e){const[,a]=e;return V(a==null?void 0:a.capabilities,"quota")}const q=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"name"}],a={alias:null,args:null,kind:"ScalarField",name:"max_vfolder_count",storageKey:null},d=[a],p=[{kind:"Variable",name:"name",variableName:"name"}],s=[a,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"StorageStatusPanelCardQuery",selections:[{alias:null,args:null,concreteType:"UserResourcePolicy",kind:"LinkedField",name:"user_resource_policy",plural:!1,selections:d,storageKey:null},{alias:null,args:p,concreteType:"ProjectResourcePolicy",kind:"LinkedField",name:"project_resource_policy",plural:!1,selections:d,storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"StorageStatusPanelCardQuery",selections:[{alias:null,args:null,concreteType:"UserResourcePolicy",kind:"LinkedField",name:"user_resource_policy",plural:!1,selections:s,storageKey:null},{alias:null,args:p,concreteType:"ProjectResourcePolicy",kind:"LinkedField",name:"project_resource_policy",plural:!1,selections:s,storageKey:null}]},params:{cacheID:"6a4458681167a38a930cf05173cf0d90",id:null,metadata:{},name:"StorageStatusPanelCardQuery",operationKind:"query",text:`query StorageStatusPanelCardQuery(
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
`}}}();q.hash="33191e01e0635b3635f28c7383463c39";const Ie=te(({css:e,token:a})=>({invitationTooltip:e`
    .ant-tooltip-arrow {
      right: 0;
      bottom: ${a.size}px;
    }
    .ant-tooltip-content {
      left: ${a.sizeXS}px;
      bottom: ${a.size}px;
    }
  `})),x=90,Te=({fetchKey:e,onRequestBadgeClick:a,style:d,...p})=>{const{t:s}=E(),{token:t}=K.useToken(),{styles:u}=Ie(),r=j(),l=G();if(!l.name)throw new Error("Project name is required for StorageStatusPanelCard");if(!l.id)throw new Error("Project ID is required for StorageStatusPanelCard");const c=v.useDeferredValue(e),[S,{updateInvitations:y}]=Y(),g=S.length;Z(()=>{y()},[e]);const m=i=>V(["delete-ongoing","delete-complete","delete-error"],i),{data:o}=P({queryKey:["vfolders",{deferredFetchKey:c,id:l.id}],queryFn:()=>{if(!(l!=null&&l.id))throw new Error("Project ID is required for StorageStatusPanelCard");return r.vfolder.list(l.id)}}),F=o==null?void 0:o.filter(i=>i.is_owner&&i.ownership_type==="user"&&!m(i.status)).length,k=o==null?void 0:o.filter(i=>i.ownership_type==="group"&&!m(i.status)).length,C=o==null?void 0:o.filter(i=>!i.is_owner&&i.ownership_type==="user"&&!m(i.status)).length,{user_resource_policy:f,project_resource_policy:_}=W.useLazyLoadQuery(q,{name:l.name});return n.jsxs($,{direction:"column",align:"stretch",style:{paddingInline:t.paddingXL,paddingBottom:t.padding,...d},...p,children:[n.jsx(w,{title:s("data.FolderStatus")}),n.jsxs(ee,{rowGap:t.marginXL,columnGap:t.marginXL,dividerColor:t.colorBorder,dividerInset:t.marginXS,dividerWidth:t.lineWidth,children:[n.jsx(R,{title:s("data.MyFolders"),value:F,unit:f!=null&&f.max_vfolder_count?`/ ${f==null?void 0:f.max_vfolder_count}`:void 0,style:{maxWidth:x},color:t.colorText}),n.jsx(R,{title:s("data.ProjectFolders"),value:k,unit:_!=null&&_.max_vfolder_count?`/ ${_==null?void 0:_.max_vfolder_count}`:void 0,style:{maxWidth:x},color:t.colorText}),n.jsx(R,{title:g>0?n.jsx("a",{onClick:()=>{a==null||a()},children:n.jsx(ne,{title:s("data.InvitedFoldersTooltip",{count:g}),rootClassName:u.invitationTooltip,placement:"topRight",children:n.jsx(ae,{count:`+${g}`,offset:[-`${t.sizeXS}`,-`${t.sizeXS}`],style:{zIndex:50},children:n.jsx(N.Text,{style:{fontSize:t.fontSizeHeading5},children:s("data.InvitedFolders")})})})}):n.jsx(N.Text,{style:{fontSize:t.fontSizeHeading5},children:s("data.InvitedFolders")}),value:n.jsx(N.Text,{style:{fontSize:t.fontSizeHeading1},children:C}),style:{maxWidth:x}})]})]})},Ge=()=>{const{token:e}=K.useToken(),{t:a}=E(),d=G(),p=se(),s=le(),t=j(),u=ie(),[r,l]=oe(),[c,S]=v.useTransition(),[y,g]=re("dashboard_board_items"),m=de(),o=t.supports("agent-stats"),F=W.useLazyLoadQuery(Q,{scopeId:`project:${d.id}`,resourceGroup:p||"default",skipTotalResourceWithinResourceGroup:!m,isSuperAdmin:T(s,"superadmin"),agentNodeFilter:`schedulable == true & status == "ALIVE" & scaling_group == "${p}"`},{fetchPolicy:r===ue?"store-and-network":"network-only",fetchKey:r});ce(()=>{S(()=>{l()})},15e3);const k=M([{id:"mySession",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(v.Suspense,{fallback:n.jsx(L,{active:!0,style:{padding:`0px ${e.marginMD}px`}}),children:n.jsx(Fe,{queryRef:F,isRefetching:c,title:T(s,"superadmin")?a("session.ActiveSessions"):a("session.MySessions")})})}},{id:"myResource",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(A,{title:a("webui.menu.MyResources"),status:"error",children:n.jsx(me,{fetchKey:r,refetching:c})})}},{id:"myResourceWithinResourceGroup",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(A,{title:a("webui.menu.MyResourcesInResourceGroup"),status:"error",children:n.jsx(ge,{fetchKey:r,refetching:c})})}},{id:"folderStatus",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(A,{title:a("data.FolderStatus"),status:"error",children:n.jsx(v.Suspense,{fallback:n.jsx(L,{active:!0,style:{padding:e.marginMD}}),children:n.jsx(Te,{fetchKey:r,onRequestBadgeClick:()=>{u({pathname:"/data",search:new URLSearchParams({invitation:"true"}).toString()})}})})})}},{id:"quotaPerStorageVolume",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(A,{title:a("data.QuotaPerStorageVolume"),status:"error",children:n.jsx(v.Suspense,{fallback:n.jsx(L,{active:!0,style:{padding:e.marginMD}}),children:n.jsx(he,{})})})}},m&&{id:"totalResourceWithinResourceGroup",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:F.TotalResourceWithinResourceGroupFragment&&n.jsx(pe,{queryRef:F.TotalResourceWithinResourceGroupFragment,refetching:c})}},T(s,"superadmin")&&o&&F.AgentStatsFragment&&{id:"agentStats",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(v.Suspense,{fallback:n.jsx(L,{active:!0,style:{padding:`0px ${e.marginMD}px`}}),children:n.jsx(_e,{queryRef:F.AgentStatsFragment,isRefetching:c})})}},T(s,"superadmin")&&{id:"activeAgents",rowSpan:4,columnSpan:4,definition:{minRowSpan:3,minColumnSpan:4},data:{content:n.jsx(v.Suspense,{fallback:n.jsx(L,{active:!0,style:{padding:`0px ${e.marginMD}px`}}),children:n.jsx(fe,{fetchKey:r,onChangeFetchKey:()=>l()})})}},{id:"recentlyCreatedSession",rowSpan:3,columnSpan:4,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(ke,{queryRef:F,isRefetching:c})}}]),C=Se(k,i=>!b(y,h=>h.id===i.id)),_=[...M(B(y,i=>{var I;const h=(I=b(k,z=>z.id===i.id))==null?void 0:I.data;return h?{...i,data:h}:void 0})),...C];return n.jsx(ve,{movable:!0,resizable:!0,bordered:!0,items:_,onItemsChange:i=>{const h=[...i.detail.items];g(B(h,I=>ye(I,"data")))}})};export{Ge as default};
//# sourceMappingURL=DashboardPage-CwHOHgo8.js.map
