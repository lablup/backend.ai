const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["assets/AdminComputeSessionListPage-DPzp9rby.js","assets/index-DB7yUW94.js","assets/index-CDgRDCYd.css","assets/BAIAdminProjectSelect-Bwu7O4oY.js"])))=>i.map(i=>d[i]);
import{u as N,au as L,at as v,r as y,aa as b,w as T,a2 as A,aY as I,k as w,ax as M,j as n,B as f,q as P,F as j,j2 as x,bX as B,aM as D,b7 as C,aN as V,i as R,bH as E,a7 as O,bt as Q,bg as q,d9 as U,az as z,bI as K,bJ as G}from"./index-DB7yUW94.js";import $ from"./SessionDetailAndContainerLogOpenerLegacy-2sQP8fwW.js";import"./SessionDetailDrawer-3BikG1o_.js";import"./BAIId-DEscoFqK.js";import"./corner-down-left-YcyydeqR.js";import"./FolderLink-DJPzhdHs.js";import"./zip-DRoFeMJl.js";import"./unzip-kgVO-3Vy.js";import"./ScopedAuditLog-BgqNEK4R.js";import"./camelCase-D3Ek1WIG.js";import"./BAIGraphQLPropertyFilter-URVW9R-R.js";import"./union-CChSQL5X.js";import"./WarningOutlined-BN1g72Bn.js";const h=(function(){var e={defaultValue:20,kind:"LocalArgument",name:"first"},d={defaultValue:0,kind:"LocalArgument",name:"offset"},l={defaultValue:null,kind:"LocalArgument",name:"resource_group_id"},c=[{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"resource_group_id",variableName:"resource_group_id"}],a={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},m=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],F={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},p=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[s,t,o,r],storageKey:null}],storageKey:null},a];return{fragment:{argumentDefinitions:[e,d,l],kind:"Fragment",metadata:null,name:"PendingSessionNodeListQuery",selections:[{alias:null,args:c,concreteType:"SessionPendingQueueConnection",kind:"LinkedField",name:"session_pending_queue",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"SessionPendingQueueEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"SessionDetailDrawerFragment"},{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"}],storageKey:null}],storageKey:null},action:"THROW"},a],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,e,d],kind:"Operation",name:"PendingSessionNodeListQuery",selections:[{alias:null,args:c,concreteType:"SessionPendingQueueConnection",kind:"LinkedField",name:"session_pending_queue",plural:!1,selections:[{alias:null,args:null,concreteType:"SessionPendingQueueEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[s,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},t,o,{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},s],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},r,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[t,o,s],storageKey:null}],storageKey:null},a],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},i,u,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},o,{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:m,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:m,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},i,s],storageKey:null},s,t,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},r,F,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:p,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:p,storageKey:null},F,{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},u,{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],storageKey:null}],storageKey:null},a],storageKey:null}]},params:{cacheID:"d864f547c93b1528556936e74befdb7a",id:null,metadata:{},name:"PendingSessionNodeListQuery",operationKind:"query",text:`query PendingSessionNodeListQuery(
  $resource_group_id: String!
  $first: Int = 20
  $offset: Int = 0
) {
  session_pending_queue(resource_group_id: $resource_group_id, first: $first, offset: $offset) {
    edges {
      node {
        ...SessionDetailDrawerFragment
        ...SessionNodesFragment
        id
      }
    }
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
`}}})();h.hash="6db7f3ef05315f718654362f981b9dbf";const W=()=>{const{t:e}=N(),[d,l]=L(),c=v(),a=y.useDeferredValue(d),s=y.useDeferredValue(c),[t,o]=b("table_column_overrides.PendingSessionNodeList"),r=T(),i=A(),{baiPaginationOption:u,tablePaginationOption:m,setTablePaginationOption:F}=I({current:1,pageSize:10}),p=y.useMemo(()=>({resource_group_id:s??"",first:u.first,offset:u.offset}),[s,u]),k=y.useDeferredValue(p),{session_pending_queue:S}=w.useLazyLoadQuery(h,k,{fetchKey:a,fetchPolicy:a===M?"store-and-network":"network-only"});return n.jsxs(f,{direction:"column",align:"stretch",gap:"sm",children:[n.jsx(P,{type:"info",showIcon:!0,description:e("adminSession.PendingSessionsScopedToResourceGroup")}),n.jsxs(f,{align:"stretch",justify:"between",children:[n.jsx(j.Item,{label:e("session.ResourceGroup"),style:{marginBottom:0},children:n.jsx(x,{showSearch:!0,style:{minWidth:100},onChangeInTransition:()=>{F({current:1})},loading:c!==s,popupMatchSelectWidth:!1,tooltip:e("general.ResourceGroup")})}),n.jsx(B,{settingId:"pending-session-list",defaultAutoUpdateDelay:1e4,loading:k!==p||a!==d,value:d,onChange:g=>{l(g)}})]}),n.jsx(D,{disableSorter:!0,onClickSessionName:g=>{const _=new URLSearchParams(i.search);_.set("sessionDetail",g.row_id),r({pathname:i.pathname,hash:i.hash,search:_.toString()},{state:{sessionDetailDrawerFrgmt:g,createdAt:new Date().toISOString()}})},loading:k!==p,sessionsFrgmt:V(S==null?void 0:S.edges.map(g=>g==null?void 0:g.node)),pagination:{pageSize:m.pageSize,current:m.current,total:(S==null?void 0:S.count)??0,onChange:(g,_)=>{C(g)&&C(_)&&F({current:g,pageSize:_})}},tableSettings:{columnOverrides:t,onColumnOverridesChange:o}})]})},H=q.lazy(()=>U(()=>import("./AdminComputeSessionListPage-DPzp9rby.js"),__vite__mapDeps([0,1,2,3]))),Y=Q(["compute-sessions","pending-sessions"]).withDefault("compute-sessions"),ue=()=>{"use memo";const e=R.c(18),{t:d}=N(),{currentTab:l,onTabChange:c}=E(Y);let a;e[0]!==d?(a=O([{key:"compute-sessions",label:d("webui.menu.Sessions")},{key:"pending-sessions",label:d("adminSession.PendingSessions")}]),e[0]=d,e[1]=a):a=e[1];let s;e[2]===Symbol.for("react.memo_cache_sentinel")?(s=n.jsx(z,{active:!0}),e[2]=s):s=e[2];let t;e[3]!==l?(t=l==="compute-sessions"&&n.jsx(K,{children:n.jsx(H,{})}),e[3]=l,e[4]=t):t=e[4];let o;e[5]!==l?(o=l==="pending-sessions"&&n.jsx(K,{children:n.jsx(W,{})}),e[5]=l,e[6]=o):o=e[6];let r;e[7]!==t||e[8]!==o?(r=n.jsxs(y.Suspense,{fallback:s,children:[t,o]}),e[7]=t,e[8]=o,e[9]=r):r=e[9];let i;e[10]!==l||e[11]!==c||e[12]!==a||e[13]!==r?(i=n.jsx(G,{activeTabKey:l,onTabChange:c,tabList:a,children:r}),e[10]=l,e[11]=c,e[12]=a,e[13]=r,e[14]=i):i=e[14];let u;e[15]===Symbol.for("react.memo_cache_sentinel")?(u=n.jsx($,{}),e[15]=u):u=e[15];let m;return e[16]!==i?(m=n.jsxs(n.Fragment,{children:[i,u]}),e[16]=i,e[17]=m):m=e[17],m};export{ue as default};
//# sourceMappingURL=AdminSessionPage-B5HofHlA.js.map
