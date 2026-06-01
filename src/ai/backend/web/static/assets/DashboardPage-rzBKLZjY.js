import{ad as J,t as I,j as n,ae as O,af as w,ag as Y,h as Z,u as E,a as D,l as G,ab as j,ah as ee,ai as M,a3 as W,B as R,X as ne,aj as P,T as L,ak as B,al as ae,am as z,an as Q,r as C,_ as te,ao as se,i as q,ap as le,aq as ie,ar as oe,as as re,at as de,p as ue,au as ce,a4 as me,av as ge,aw as K,ax as pe,ay as Se,a1 as V,az as T,aA as ye,aB as fe,aC as ke,a5 as Fe,a6 as $,ac as _e}from"./index-CC9H5FpY.js";import{S as Ce,A as ve,a as he,R as Le}from"./SessionCountDashboardItem-DNHPQZLD.js";import{B as Te}from"./BAIBoard-BUP9zyuD.js";import{Q as Ie}from"./QuotaPerStorageVolumePanelCard-Drd_H98L.js";import"./AgentList-Awul2X7p.js";import"./BAIAdminResourceGroupSelect-e-PSr-gH.js";import"./SessionDetailDrawer-BVjO_cba.js";import"./corner-down-left-BhZTgxok.js";import"./FolderLink-C7chKJFz.js";import"./zip-TaKZGqdT.js";import"./unzip-Cji1UvDK.js";import"./BAIGraphQLPropertyFilter-Ckmil7rC.js";const x=({title:e,status:a="error",children:o,style:c})=>{const{t:s}=J(),{token:t}=I.useToken();return n.jsx(O,{fallbackRender:()=>n.jsx("div",{"data-bai-board-item-status":a,style:{height:"100%",paddingInline:t.paddingXL,paddingBottom:t.padding,...c},children:n.jsx(w,{title:e,extra:n.jsx(Y,{title:s("comp:BAIBoardItemErrorBoundary.UnexpectedError"),type:a})})}),children:o})},U=function(){var e={defaultValue:null,kind:"LocalArgument",name:"agentNodeFilter"},a={defaultValue:null,kind:"LocalArgument",name:"isSuperAdmin"},o={defaultValue:null,kind:"LocalArgument",name:"resourceGroup"},c={defaultValue:null,kind:"LocalArgument",name:"scopeId"},s={defaultValue:null,kind:"LocalArgument",name:"skipTotalResourceWithinResourceGroup"},t=[{kind:"Variable",name:"scopeId",variableName:"scopeId"}],r={kind:"Literal",name:"first",value:0},i={kind:"Variable",name:"scope_id",variableName:"scopeId"},l={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},u=[l],S={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},_=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],v={alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},F=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[S,y,p,g],storageKey:null}],storageKey:null},l],k=[S,g,{alias:null,args:null,kind:"ScalarField",name:"available_slots",storageKey:null},f,v];return{fragment:{argumentDefinitions:[e,a,o,c,s],kind:"Fragment",metadata:null,name:"DashboardPageQuery",selections:[{args:t,kind:"FragmentSpread",name:"SessionCountDashboardItemFragment"},{args:t,kind:"FragmentSpread",name:"RecentlyCreatedSessionFragment"},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{fragment:{kind:"InlineFragment",selections:[{args:[{kind:"Variable",name:"agentNodeFilter",variableName:"agentNodeFilter"},{kind:"Variable",name:"isSuperAdmin",variableName:"isSuperAdmin"},{kind:"Variable",name:"resourceGroup",variableName:"resourceGroup"}],kind:"FragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"TotalResourceWithinResourceGroupFragment"}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{fragment:{kind:"InlineFragment",selections:[{args:null,kind:"FragmentSpread",name:"AgentStatsFragment"}],type:"Query",abstractKey:null},kind:"AliasedInlineFragmentSpread",name:"AgentStatsFragment"}]}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[c,o,s,a,e],kind:"Operation",name:"DashboardPageQuery",selections:[{alias:"myInteractive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},r,i],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:u,storageKey:null},{alias:"myBatch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},r,i],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:u,storageKey:null},{alias:"myInference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},r,i],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:u,storageKey:null},{alias:"myUpload",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},r,i],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:u,storageKey:null},{alias:null,args:[{kind:"Literal",name:"filter",value:'status == "running"'},{kind:"Literal",name:"first",value:5},{kind:"Literal",name:"order",value:"-created_at"},i],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[S,y,p,g,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},d,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},f,{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},S,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},p,{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:_,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:_,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},S],storageKey:null},y,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},g,d,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},S],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[y,p,S],storageKey:null}],storageKey:null},l],storageKey:null},v,{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:F,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:F,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{condition:"skipTotalResourceWithinResourceGroup",kind:"Condition",passingValue:!1,selections:[{condition:"isSuperAdmin",kind:"Condition",passingValue:!1,selections:[{alias:null,args:[{kind:"Literal",name:"filter",value:"schedulable == true"},{kind:"Literal",name:"limit",value:1e3},{kind:"Literal",name:"offset",value:0},{kind:"Variable",name:"scaling_group",variableName:"resourceGroup"},{kind:"Literal",name:"status",value:"ALIVE"}],concreteType:"AgentSummaryList",kind:"LinkedField",name:"agent_summary_list",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentSummary",kind:"LinkedField",name:"items",plural:!0,selections:k,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"total_count",storageKey:null}],storageKey:null}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"agentNodeFilter"},{kind:"Literal",name:"first",value:100}],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AgentNode",kind:"LinkedField",name:"node",plural:!1,selections:k,storageKey:null}],storageKey:null},l],storageKey:null}]}]},{condition:"isSuperAdmin",kind:"Condition",passingValue:!0,selections:[{alias:null,args:null,concreteType:"AgentStats",kind:"LinkedField",name:"agentStats",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentResource",kind:"LinkedField",name:"totalResource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"free",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capacity",storageKey:null}],storageKey:null}],storageKey:null}]}]},params:{cacheID:"7d97e346f454962291c680541356a7aa",id:null,metadata:{},name:"DashboardPageQuery",operationKind:"query",text:`query DashboardPageQuery(
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
`}}}();U.hash="c569b4f4d4f8ee32a4f369157d8a1348";const Ae=()=>{"use memo";const e=Z.c(21),{t:a}=E(),{token:o}=I.useToken(),c=D();let s;e[0]===Symbol.for("react.memo_cache_sentinel")?(s=["vhostInfo"],e[0]=s):s=e[0];let t;e[1]!==c?(t={queryKey:s,queryFn:()=>c.vfolder.list_hosts()},e[1]=c,e[2]=t):t=e[2];const{data:r}=G(t);let i;e[3]!==(r==null?void 0:r.volume_info)?(i=j(ee((r==null?void 0:r.volume_info)??{}),Ke),e[3]=r==null?void 0:r.volume_info,e[4]=i):i=e[4];const l=i;let u;e[5]!==l?(u=l?{id:l[0],...l[1]}:void 0,e[5]=l,e[6]=u):u=e[6];const S=u;let y;e[7]!==o.padding||e[8]!==o.paddingXL?(y={paddingInline:o.paddingXL,paddingBottom:o.padding},e[7]=o.padding,e[8]=o.paddingXL,e[9]=y):y=e[9];let p;e[10]!==a?(p=a("data.QuotaPerStorageVolume"),e[10]=a,e[11]=p):p=e[11];let g;e[12]!==p?(g=n.jsx(w,{title:p}),e[12]=p,e[13]=g):g=e[13];let d;e[14]!==S||e[15]!==a?(d=S?n.jsx(Ie,{defaultVolumeInfo:S}):n.jsx(M,{image:M.PRESENTED_IMAGE_SIMPLE,description:a("storageHost.QuotaDoesNotSupported")}),e[14]=S,e[15]=a,e[16]=d):d=e[16];let f;return e[17]!==y||e[18]!==g||e[19]!==d?(f=n.jsxs(R,{direction:"column",align:"stretch",style:y,children:[g,d]}),e[17]=y,e[18]=g,e[19]=d,e[20]=f):f=e[20],f};function Ke(e){const[,a]=e;return W(a==null?void 0:a.capabilities,"quota")}const X=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"name"}],a={alias:null,args:null,kind:"ScalarField",name:"max_vfolder_count",storageKey:null},o=[a],c=[{kind:"Variable",name:"name",variableName:"name"}],s=[a,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"StorageStatusPanelCardQuery",selections:[{alias:null,args:null,concreteType:"UserResourcePolicy",kind:"LinkedField",name:"user_resource_policy",plural:!1,selections:o,storageKey:null},{alias:null,args:c,concreteType:"ProjectResourcePolicy",kind:"LinkedField",name:"project_resource_policy",plural:!1,selections:o,storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"StorageStatusPanelCardQuery",selections:[{alias:null,args:null,concreteType:"UserResourcePolicy",kind:"LinkedField",name:"user_resource_policy",plural:!1,selections:s,storageKey:null},{alias:null,args:c,concreteType:"ProjectResourcePolicy",kind:"LinkedField",name:"project_resource_policy",plural:!1,selections:s,storageKey:null}]},params:{cacheID:"6a4458681167a38a930cf05173cf0d90",id:null,metadata:{},name:"StorageStatusPanelCardQuery",operationKind:"query",text:`query StorageStatusPanelCardQuery(
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
`}}}();X.hash="33191e01e0635b3635f28c7383463c39";const xe=z(({css:e})=>({progressSteps:e`
    .ant-progress-steps-item {
      border-radius: 100px;
    }
  `})),N=({title:e,value:a,unit:o,percent:c,color:s,progressProps:t,...r})=>{const{token:i}=I.useToken(),{styles:l}=xe(),u=ne();return n.jsxs(R,{...r,direction:"column",style:{minWidth:80,...r.style},justify:"between",align:"start",wrap:"wrap",children:[P(e)?n.jsx(L.Text,{style:{fontSize:i.fontSizeHeading5,wordBreak:"keep-all",textAlign:"left"},children:e}):e,n.jsxs(R,{children:[P(a)||B(a)?n.jsx(L.Text,{style:{fontSize:i.fontSizeHeading1,color:s??u.primary5},children:a}):a,o&&n.jsx(L.Text,{children:o})]}),B(c)&&n.jsx(ae,{percent:c,strokeColor:s??i.colorPrimary,showInfo:!1,steps:12,size:[5,12],className:l.progressSteps,...t})]})},Re=z(({css:e,token:a})=>({invitationTooltip:e`
    .ant-tooltip-arrow {
      right: 0;
      bottom: ${a.size}px;
    }
    .ant-tooltip-content {
      left: ${a.sizeXS}px;
      bottom: ${a.size}px;
    }
  `})),b=90,Ne=({fetchKey:e,onRequestBadgeClick:a,style:o,...c})=>{const{t:s}=E(),{token:t}=I.useToken(),{styles:r}=Re(),i=D(),l=Q();if(!l.name)throw new Error("Project name is required for StorageStatusPanelCard");if(!l.id)throw new Error("Project ID is required for StorageStatusPanelCard");const u=C.useDeferredValue(e),[S,{updateInvitations:y}]=te(),p=S.length;se(()=>{y()},[e]);const g=m=>W(["delete-ongoing","delete-complete","delete-error"],m),{data:d}=G({queryKey:["vfolders",{deferredFetchKey:u,id:l.id}],queryFn:()=>{if(!(l!=null&&l.id))throw new Error("Project ID is required for StorageStatusPanelCard");return i.vfolder.list(l.id)}}),f=d==null?void 0:d.filter(m=>m.is_owner&&m.ownership_type==="user"&&!g(m.status)).length,_=d==null?void 0:d.filter(m=>m.ownership_type==="group"&&!g(m.status)).length,v=d==null?void 0:d.filter(m=>!m.is_owner&&m.ownership_type==="user"&&!g(m.status)).length,{user_resource_policy:F,project_resource_policy:k}=q.useLazyLoadQuery(X,{name:l.name});return n.jsxs(R,{direction:"column",align:"stretch",style:{paddingInline:t.paddingXL,paddingBottom:t.padding,...o},...c,children:[n.jsx(w,{title:s("data.FolderStatus")}),n.jsxs(le,{rowGap:t.marginXL,columnGap:t.marginXL,dividerColor:t.colorBorder,dividerInset:t.marginXS,dividerWidth:t.lineWidth,children:[n.jsx(N,{title:s("data.MyFolders"),value:f,unit:F!=null&&F.max_vfolder_count?`/ ${F==null?void 0:F.max_vfolder_count}`:void 0,style:{maxWidth:b},color:t.colorText}),n.jsx(N,{title:s("data.ProjectFolders"),value:_,unit:k!=null&&k.max_vfolder_count?`/ ${k==null?void 0:k.max_vfolder_count}`:void 0,style:{maxWidth:b},color:t.colorText}),n.jsx(N,{title:p>0?n.jsx("a",{onClick:()=>{a==null||a()},children:n.jsx(ie,{title:s("data.InvitedFoldersTooltip",{count:p}),rootClassName:r.invitationTooltip,placement:"topRight",children:n.jsx(oe,{count:`+${p}`,offset:[-`${t.sizeXS}`,-`${t.sizeXS}`],style:{zIndex:50},children:n.jsx(L.Text,{style:{fontSize:t.fontSizeHeading5},children:s("data.InvitedFolders")})})})}):n.jsx(L.Text,{style:{fontSize:t.fontSizeHeading5},children:s("data.InvitedFolders")}),value:n.jsx(L.Text,{style:{fontSize:t.fontSizeHeading1},children:v}),style:{maxWidth:b}})]})]})},ze=()=>{const{token:e}=I.useToken(),{t:a}=E(),o=Q(),c=re(),s=de(),t=D(),r=ue(),[i,l]=ce(),[u,S]=C.useTransition(),[y,p]=me("dashboard_board_items"),g=ge(),d=t.supports("agent-stats"),f=q.useLazyLoadQuery(U,{scopeId:`project:${o.id}`,resourceGroup:c||"default",skipTotalResourceWithinResourceGroup:!g,isSuperAdmin:K(s,"superadmin"),agentNodeFilter:`schedulable == true & status == "ALIVE" & scaling_group == "${c}"`},{fetchPolicy:i===pe?"store-and-network":"network-only",fetchKey:i});Se(()=>{S(()=>{l()})},15e3);const _=V([{id:"mySession",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(C.Suspense,{fallback:n.jsx(T,{active:!0,style:{padding:`0px ${e.marginMD}px`}}),children:n.jsx(Ce,{queryRef:f,isRefetching:u,title:K(s,"superadmin")?a("session.ActiveSessions"):a("session.MySessions")})})}},{id:"myResource",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(x,{title:a("webui.menu.MyResources"),status:"error",children:n.jsx(ye,{fetchKey:i,refetching:u})})}},{id:"myResourceWithinResourceGroup",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(x,{title:a("webui.menu.MyResourcesInResourceGroup"),status:"error",children:n.jsx(fe,{fetchKey:i,refetching:u})})}},{id:"folderStatus",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(x,{title:a("data.FolderStatus"),status:"error",children:n.jsx(C.Suspense,{fallback:n.jsx(T,{active:!0,style:{padding:e.marginMD}}),children:n.jsx(Ne,{fetchKey:i,onRequestBadgeClick:()=>{r({pathname:"/data",search:new URLSearchParams({invitation:"true"}).toString()})}})})})}},{id:"quotaPerStorageVolume",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(x,{title:a("data.QuotaPerStorageVolume"),status:"error",children:n.jsx(C.Suspense,{fallback:n.jsx(T,{active:!0,style:{padding:e.marginMD}}),children:n.jsx(Ae,{})})})}},g&&{id:"totalResourceWithinResourceGroup",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:f.TotalResourceWithinResourceGroupFragment&&n.jsx(ke,{queryRef:f.TotalResourceWithinResourceGroupFragment,refetching:u})}},K(s,"superadmin")&&d&&f.AgentStatsFragment&&{id:"agentStats",rowSpan:2,columnSpan:2,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(C.Suspense,{fallback:n.jsx(T,{active:!0,style:{padding:`0px ${e.marginMD}px`}}),children:n.jsx(ve,{queryRef:f.AgentStatsFragment,isRefetching:u})})}},K(s,"superadmin")&&{id:"activeAgents",rowSpan:4,columnSpan:4,definition:{minRowSpan:3,minColumnSpan:4},data:{content:n.jsx(C.Suspense,{fallback:n.jsx(T,{active:!0,style:{padding:`0px ${e.marginMD}px`}}),children:n.jsx(he,{fetchKey:i,onChangeFetchKey:()=>l()})})}},{id:"recentlyCreatedSession",rowSpan:3,columnSpan:4,definition:{minRowSpan:2,minColumnSpan:2},data:{content:n.jsx(Le,{queryRef:f,isRefetching:u})}}]),v=Fe(_,m=>!j(y,h=>h.id===m.id)),k=[...V($(y,m=>{var A;const h=(A=j(_,H=>H.id===m.id))==null?void 0:A.data;return h?{...m,data:h}:void 0})),...v];return n.jsx(Te,{movable:!0,resizable:!0,bordered:!0,items:k,onItemsChange:m=>{const h=[...m.detail.items];p($(h,A=>_e(A,"data")))}})};export{ze as default};
//# sourceMappingURL=DashboardPage-rzBKLZjY.js.map
