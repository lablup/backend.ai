const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["assets/AdminComputeSessionListPage-GtpIci4M.js","assets/index-DLl5_15D.js","assets/index-CDgRDCYd.css"])))=>i.map(i=>d[i]);
import{u as h,ar as v,ap as b,r as f,a4 as I,p as L,Z as T,aW as A,i as w,au as P,j as a,B as k,o as M,F as j,ij as x,aA as B,aJ as D,b6 as K,aK as V,h as R,cY as E,bu as O,a1 as Q,bJ as C,bf as U,c_ as q,aw as z,bI as G}from"./index-DLl5_15D.js";import $ from"./SessionDetailAndContainerLogOpenerLegacy-BJ41qGsr.js";import"./SessionDetailDrawer-BekQ3rgv.js";import"./BAIId-CUEnOS4w.js";import"./corner-down-left-CAJyc4A5.js";import"./FolderLink-C2HMK66Z.js";import"./zip-DsMATQHn.js";import"./unzip-ML45z091.js";import"./ScopedAuditLog-CBMDUmPr.js";import"./camelCase-psNhqco0.js";import"./BAIGraphQLPropertyFilter-BVY69KXO.js";import"./WarningOutlined-BSgfKkny.js";const N=function(){var e={defaultValue:20,kind:"LocalArgument",name:"first"},d={defaultValue:0,kind:"LocalArgument",name:"offset"},F={defaultValue:null,kind:"LocalArgument",name:"resource_group_id"},m=[{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"resource_group_id",variableName:"resource_group_id"}],n={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},_={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},u=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],i={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},r=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[l,c,_,o],storageKey:null}],storageKey:null},n];return{fragment:{argumentDefinitions:[e,d,F],kind:"Fragment",metadata:null,name:"PendingSessionNodeListQuery",selections:[{alias:null,args:m,concreteType:"SessionPendingQueueConnection",kind:"LinkedField",name:"session_pending_queue",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"SessionPendingQueueEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"SessionDetailDrawerFragment"},{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"}],storageKey:null}],storageKey:null},action:"THROW"},n],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[F,e,d],kind:"Operation",name:"PendingSessionNodeListQuery",selections:[{alias:null,args:m,concreteType:"SessionPendingQueueConnection",kind:"LinkedField",name:"session_pending_queue",plural:!1,selections:[{alias:null,args:null,concreteType:"SessionPendingQueueEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},c,_,{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},l],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},o,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[c,_,l],storageKey:null}],storageKey:null},n],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},t,{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},_,{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:u,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:u,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},t,l],storageKey:null},l,c,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},o,i,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:r,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:r,storageKey:null},i,{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],storageKey:null}],storageKey:null},n],storageKey:null}]},params:{cacheID:"88a2eedb42f134eec5803ad4b57a2706",id:null,metadata:{},name:"PendingSessionNodeListQuery",operationKind:"query",text:`query PendingSessionNodeListQuery(
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
`}}}();N.hash="6db7f3ef05315f718654362f981b9dbf";const W=()=>{const{t:e}=h(),[d,F]=v(),m=b(),n=f.useDeferredValue(d),l=f.useDeferredValue(m),[c,_]=I("table_column_overrides.PendingSessionNodeList"),o=L(),t=T(),{baiPaginationOption:u,tablePaginationOption:i,setTablePaginationOption:r}=A({current:1,pageSize:10}),p=f.useMemo(()=>({resource_group_id:l??"",first:u.first,offset:u.offset}),[l,u]),S=f.useDeferredValue(p),{session_pending_queue:g}=w.useLazyLoadQuery(N,S,{fetchKey:n,fetchPolicy:n===P?"store-and-network":"network-only"});return a.jsxs(k,{direction:"column",align:"stretch",gap:"sm",children:[a.jsx(M,{type:"info",showIcon:!0,description:e("adminSession.PendingSessionsScopedToResourceGroup")}),a.jsxs(k,{align:"stretch",justify:"between",children:[a.jsx(j.Item,{label:e("session.ResourceGroup"),style:{marginBottom:0},children:a.jsx(x,{showSearch:!0,style:{minWidth:100},onChangeInTransition:()=>{r({current:1})},loading:m!==l,popupMatchSelectWidth:!1,tooltip:e("general.ResourceGroup")})}),a.jsx(B,{loading:S!==p||n!==d,autoUpdateDelay:7e3,value:d,onChange:s=>{F(s)}})]}),a.jsx(D,{disableSorter:!0,onClickSessionName:s=>{const y=new URLSearchParams(t.search);y.set("sessionDetail",s.row_id),o({pathname:t.pathname,hash:t.hash,search:y.toString()},{state:{sessionDetailDrawerFrgmt:s,createdAt:new Date().toISOString()}})},loading:S!==p,sessionsFrgmt:V(g==null?void 0:g.edges.map(s=>s==null?void 0:s.node)),pagination:{pageSize:i.pageSize,current:i.current,total:(g==null?void 0:g.count)??0,onChange:(s,y)=>{K(s)&&K(y)&&r({current:s,pageSize:y})}},tableSettings:{columnOverrides:c,onColumnOverridesChange:_}})]})},H=U.lazy(()=>q(()=>import("./AdminComputeSessionListPage-GtpIci4M.js"),__vite__mapDeps([0,1,2]))),re=()=>{"use memo";const e=R.c(23),{t:d}=h();let F,m;e[0]===Symbol.for("react.memo_cache_sentinel")?(F={tab:E.withDefault("compute-sessions")},m={history:"push"},e[0]=F,e[1]=m):(F=e[0],m=e[1]);const[n,l]=O(F,m),c=L(),_=n.tab;let o;e[2]!==l||e[3]!==c?(o=y=>{c({pathname:"/admin-session",search:new URLSearchParams({tab:y}).toString()}),l({tab:y})},e[2]=l,e[3]=c,e[4]=o):o=e[4];let t;e[5]!==d?(t=Q([{key:"compute-sessions",label:d("webui.menu.Sessions")},{key:"pending-sessions",label:d("adminSession.PendingSessions")}]),e[5]=d,e[6]=t):t=e[6];let u;e[7]===Symbol.for("react.memo_cache_sentinel")?(u=a.jsx(z,{active:!0}),e[7]=u):u=e[7];let i;e[8]!==n.tab?(i=n.tab==="compute-sessions"&&a.jsx(C,{children:a.jsx(H,{})}),e[8]=n.tab,e[9]=i):i=e[9];let r;e[10]!==n.tab?(r=n.tab==="pending-sessions"&&a.jsx(C,{children:a.jsx(W,{})}),e[10]=n.tab,e[11]=r):r=e[11];let p;e[12]!==i||e[13]!==r?(p=a.jsxs(f.Suspense,{fallback:u,children:[i,r]}),e[12]=i,e[13]=r,e[14]=p):p=e[14];let S;e[15]!==n.tab||e[16]!==o||e[17]!==t||e[18]!==p?(S=a.jsx(G,{activeTabKey:_,onTabChange:o,tabList:t,children:p}),e[15]=n.tab,e[16]=o,e[17]=t,e[18]=p,e[19]=S):S=e[19];let g;e[20]===Symbol.for("react.memo_cache_sentinel")?(g=a.jsx($,{}),e[20]=g):g=e[20];let s;return e[21]!==S?(s=a.jsxs(a.Fragment,{children:[S,g]}),e[21]=S,e[22]=s):s=e[22],s};export{re as default};
//# sourceMappingURL=AdminSessionPage-Bxv35WVh.js.map
