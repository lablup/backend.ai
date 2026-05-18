const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["assets/AdminComputeSessionListPage-CRjOG_Ho.js","assets/index-M9a7wauv.js"])))=>i.map(i=>d[i]);
import{u as h,au as v,as as b,r as k,a4 as T,p as L,Z as A,aY as I,i as w,ax as M,j as a,B as f,o as P,F as x,ii as j,aD as B,aM as D,ak as K,aN as V,h as R,cU as E,bv as O,a1 as Q,bL as C,bf as U,cW as q,az as z,bK as G}from"./index-M9a7wauv.js";import $ from"./SessionDetailAndContainerLogOpenerLegacy-bOwL2aBZ.js";import"./SessionDetailDrawer-DdbAmY1L.js";import"./corner-down-left-C3b1tE_4.js";import"./FolderLink-B4Tyaydh.js";import"./zip-CWIpHMud.js";import"./unzip-BNy8xCy7.js";import"./BAIGraphQLPropertyFilter-FbNAR0Ex.js";const N=function(){var e={defaultValue:20,kind:"LocalArgument",name:"first"},r={defaultValue:0,kind:"LocalArgument",name:"offset"},S={defaultValue:null,kind:"LocalArgument",name:"resource_group_id"},g=[{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"resource_group_id",variableName:"resource_group_id"}],n={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},_={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},t=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],d={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},i=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[l,m,_,o],storageKey:null}],storageKey:null},n];return{fragment:{argumentDefinitions:[e,r,S],kind:"Fragment",metadata:null,name:"PendingSessionNodeListQuery",selections:[{alias:null,args:g,concreteType:"SessionPendingQueueConnection",kind:"LinkedField",name:"session_pending_queue",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"SessionPendingQueueEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"SessionDetailDrawerFragment"},{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"}],storageKey:null}],storageKey:null},action:"THROW"},n],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[S,e,r],kind:"Operation",name:"PendingSessionNodeListQuery",selections:[{alias:null,args:g,concreteType:"SessionPendingQueueConnection",kind:"LinkedField",name:"session_pending_queue",plural:!1,selections:[{alias:null,args:null,concreteType:"SessionPendingQueueEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},m,_,{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},l],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},o,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[m,_,l],storageKey:null}],storageKey:null},n],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},_,{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:t,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:t,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},l],storageKey:null},l,m,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},o,d,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:i,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:i,storageKey:null},d,{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],storageKey:null}],storageKey:null},n],storageKey:null}]},params:{cacheID:"de8027be7b23981063d2fe0432084439",id:null,metadata:{},name:"PendingSessionNodeListQuery",operationKind:"query",text:`query PendingSessionNodeListQuery(
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
`}}}();N.hash="6db7f3ef05315f718654362f981b9dbf";const W=()=>{const{t:e}=h(),[r,S]=v(),g=b(),n=k.useDeferredValue(r),l=k.useDeferredValue(g),[m,_]=T("table_column_overrides.PendingSessionNodeList"),o=L(),t=A(),{baiPaginationOption:d,tablePaginationOption:i,setTablePaginationOption:F}=I({current:1,pageSize:10}),c=k.useMemo(()=>({resource_group_id:l??"",first:d.first,offset:d.offset}),[l,d]),p=k.useDeferredValue(c),{session_pending_queue:u}=w.useLazyLoadQuery(N,p,{fetchKey:n,fetchPolicy:n===M?"store-and-network":"network-only"});return a.jsxs(f,{direction:"column",align:"stretch",gap:"sm",children:[a.jsx(P,{type:"info",showIcon:!0,description:e("adminSession.PendingSessionsScopedToResourceGroup")}),a.jsxs(f,{align:"stretch",justify:"between",children:[a.jsx(x.Item,{label:e("session.ResourceGroup"),style:{marginBottom:0},children:a.jsx(j,{showSearch:!0,style:{minWidth:100},onChangeInTransition:()=>{F({current:1})},loading:g!==l,popupMatchSelectWidth:!1,tooltip:e("general.ResourceGroup")})}),a.jsx(B,{loading:p!==c||n!==r,autoUpdateDelay:7e3,value:r,onChange:s=>{S(s)}})]}),a.jsx(D,{disableSorter:!0,onClickSessionName:s=>{const y=new URLSearchParams(t.search);y.set("sessionDetail",s.row_id),o({pathname:t.pathname,hash:t.hash,search:y.toString()},{state:{sessionDetailDrawerFrgmt:s,createdAt:new Date().toISOString()}})},loading:p!==c,sessionsFrgmt:V(u==null?void 0:u.edges.map(s=>s==null?void 0:s.node)),pagination:{pageSize:i.pageSize,current:i.current,total:(u==null?void 0:u.count)??0,onChange:(s,y)=>{K(s)&&K(y)&&F({current:s,pageSize:y})}},tableSettings:{columnOverrides:m,onColumnOverridesChange:_}})]})},H=U.lazy(()=>q(()=>import("./AdminComputeSessionListPage-CRjOG_Ho.js"),__vite__mapDeps([0,1]))),le=()=>{"use memo";const e=R.c(23),{t:r}=h();let S,g;e[0]===Symbol.for("react.memo_cache_sentinel")?(S={tab:E.withDefault("compute-sessions")},g={history:"push"},e[0]=S,e[1]=g):(S=e[0],g=e[1]);const[n,l]=O(S,g),m=L(),_=n.tab;let o;e[2]!==l||e[3]!==m?(o=y=>{m({pathname:"/admin-session",search:new URLSearchParams({tab:y}).toString()}),l({tab:y})},e[2]=l,e[3]=m,e[4]=o):o=e[4];let t;e[5]!==r?(t=Q([{key:"compute-sessions",label:r("webui.menu.Sessions")},{key:"pending-sessions",label:r("adminSession.PendingSessions")}]),e[5]=r,e[6]=t):t=e[6];let d;e[7]===Symbol.for("react.memo_cache_sentinel")?(d=a.jsx(z,{active:!0}),e[7]=d):d=e[7];let i;e[8]!==n.tab?(i=n.tab==="compute-sessions"&&a.jsx(C,{children:a.jsx(H,{})}),e[8]=n.tab,e[9]=i):i=e[9];let F;e[10]!==n.tab?(F=n.tab==="pending-sessions"&&a.jsx(C,{children:a.jsx(W,{})}),e[10]=n.tab,e[11]=F):F=e[11];let c;e[12]!==i||e[13]!==F?(c=a.jsxs(k.Suspense,{fallback:d,children:[i,F]}),e[12]=i,e[13]=F,e[14]=c):c=e[14];let p;e[15]!==n.tab||e[16]!==o||e[17]!==t||e[18]!==c?(p=a.jsx(G,{activeTabKey:_,onTabChange:o,tabList:t,children:c}),e[15]=n.tab,e[16]=o,e[17]=t,e[18]=c,e[19]=p):p=e[19];let u;e[20]===Symbol.for("react.memo_cache_sentinel")?(u=a.jsx($,{}),e[20]=u):u=e[20];let s;return e[21]!==p?(s=a.jsxs(a.Fragment,{children:[p,u]}),e[21]=p,e[22]=s):s=e[22],s};export{le as default};
//# sourceMappingURL=AdminSessionPage-BWsyN_kb.js.map
