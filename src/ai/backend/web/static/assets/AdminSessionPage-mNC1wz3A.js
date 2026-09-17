const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["assets/AdminComputeSessionListPage-8MyVqpSd.js","assets/index-DPebpL40.js","assets/index-CiPL7ix-.css","assets/BAIAdminProjectSelect-N8l8_IVM.js"])))=>i.map(i=>d[i]);
import{i as pe,u as Se,ab as fe,a as ye,aN as _e,b8 as ke,l as Q,a7 as he,Y as Ce,ac as Ke,bE as Ne,r as Le,j as n,F as ve,c9 as be,q as Ae,O as Ie,bK as Te,al as we,ew as Pe,aS as ce,bg as Me,an as xe,ht as je,cz as Be,c as de,bL as me,aX as Re,ao as De,hu as Ee,cm as Ve,ah as Oe,c8 as Ue,bY as Qe,e4 as ze,aU as Ge,co as ge,d as $e}from"./index-DPebpL40.js";import We from"./SessionDetailAndContainerLogOpenerLegacy-CGHRsnz0.js";import"./SessionDetailDrawer-CHJu8GbK.js";import"./BAIId-oHD2WVBQ.js";import"./FolderLink-rZTSRFdj.js";import"./zip-dqg4xnl6.js";import"./unzip-CzK734fj.js";import"./ScopedAuditLog-Dwul8NSy.js";import"./BAIGraphQLPropertyFilter-CPqP1l9W.js";import"./rotate-ccw-clock-CpAeUoLy.js";const Fe=(function(){var e={defaultValue:20,kind:"LocalArgument",name:"first"},s={defaultValue:0,kind:"LocalArgument",name:"offset"},r={defaultValue:null,kind:"LocalArgument",name:"resource_group_id"},p=[{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"resource_group_id",variableName:"resource_group_id"}],l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},g=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],y={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},f=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[l,i,o,u],storageKey:null}],storageKey:null},t],c={alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null};return{fragment:{argumentDefinitions:[e,s,r],kind:"Fragment",metadata:null,name:"PendingSessionNodeListQuery",selections:[{alias:null,args:p,concreteType:"SessionPendingQueueConnection",kind:"LinkedField",name:"session_pending_queue",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"SessionPendingQueueEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[l,{args:null,kind:"FragmentSpread",name:"SessionDetailDrawerFragment"},{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"},{args:null,kind:"FragmentSpread",name:"EditSessionPriorityModalFragment"}],storageKey:null}],storageKey:null},action:"THROW"},t],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[r,e,s],kind:"Operation",name:"PendingSessionNodeListQuery",selections:[{alias:null,args:p,concreteType:"SessionPendingQueueConnection",kind:"LinkedField",name:"session_pending_queue",plural:!1,selections:[{alias:null,args:null,concreteType:"SessionPendingQueueEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},i,o,{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},l],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},u,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[i,o,l],storageKey:null}],storageKey:null},t],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},d,S,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},o,{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:g,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:g,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},d,l],storageKey:null},l,i,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},u,y,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:f,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:f,storageKey:null},y,{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},c,{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},S,{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},c],storageKey:null}],storageKey:null},t],storageKey:null}]},params:{cacheID:"676b64d1e46c8516acd0a558b8c02dae",id:null,metadata:{},name:"PendingSessionNodeListQuery",operationKind:"query",text:`query PendingSessionNodeListQuery(
  $resource_group_id: String!
  $first: Int = 20
  $offset: Int = 0
) {
  session_pending_queue(resource_group_id: $resource_group_id, first: $first, offset: $offset) {
    edges {
      node {
        id
        ...SessionDetailDrawerFragment
        ...SessionNodesFragment
        ...EditSessionPriorityModalFragment
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
`}}})();Fe.hash="4b2123e18974d3e3a0839a2acca5b55e";const Ye=()=>{"use memo";const e=pe.c(88),{t:s}=Se(),{token:r}=fe.useToken(),p=ye();let l;e[0]!==p?(l=p.isManagerVersionCompatibleWith("26.4.0"),e[0]=p,e[1]=l):l=e[1];const t=l,[i,o]=_e(),u=ke(),d=Q.useDeferredValue(i),S=Q.useDeferredValue(u),[g,y]=he("table_column_overrides.PendingSessionNodeList");let f;e[2]===Symbol.for("react.memo_cache_sentinel")?(f=[],e[2]=f):f=e[2];const[c,G]=Q.useState(f),[Z,ue]=Q.useState(!1),ee=Ce(),F=Ke();let $;e[3]===Symbol.for("react.memo_cache_sentinel")?($={current:1,pageSize:10},e[3]=$):$=e[3];const{baiPaginationOption:_,tablePaginationOption:k,setTablePaginationOption:h}=Ne($),ne=S??"";let W;e[4]!==_.first||e[5]!==_.offset||e[6]!==ne?(W={resource_group_id:ne,first:_.first,offset:_.offset},e[4]=_.first,e[5]=_.offset,e[6]=ne,e[7]=W):W=e[7];const ae=W,se=Q.useDeferredValue(ae);let Y;e[8]===Symbol.for("react.memo_cache_sentinel")?(Y=Fe,e[8]=Y):Y=e[8];const le=d===Me?"store-and-network":"network-only";let q;e[9]!==d||e[10]!==le?(q={fetchKey:d,fetchPolicy:le},e[9]=d,e[10]=le,e[11]=q):q=e[11];const{session_pending_queue:a}=Le.useLazyLoadQuery(Y,se,q);let C;e[12]!==s?(C=s("adminSession.PendingSessionsScopedToResourceGroup"),e[12]=s,e[13]=C):C=e[13];let K;e[14]!==C?(K=n.jsx(xe,{type:"info",showIcon:!0,description:C}),e[14]=C,e[15]=K):K=e[15];let N;e[16]!==s?(N=s("session.ResourceGroup"),e[16]=s,e[17]=N):N=e[17];let H;e[18]===Symbol.for("react.memo_cache_sentinel")?(H={marginBottom:0},e[18]=H):H=e[18];let X;e[19]===Symbol.for("react.memo_cache_sentinel")?(X={minWidth:100},e[19]=X):X=e[19];let L;e[20]!==h?(L=()=>{h({current:1}),G([])},e[20]=h,e[21]=L):L=e[21];const te=u!==S;let v;e[22]!==s?(v=s("general.ResourceGroup"),e[22]=s,e[23]=v):v=e[23];let b;e[24]!==L||e[25]!==te||e[26]!==v?(b=n.jsx(je,{showSearch:!0,style:X,onChangeInTransition:L,loading:te,popupMatchSelectWidth:!1,tooltip:v}),e[24]=L,e[25]=te,e[26]=v,e[27]=b):b=e[27];let A;e[28]!==N||e[29]!==b?(A=n.jsx(ve.Item,{label:N,style:H,children:b}),e[28]=N,e[29]=b,e[30]=A):A=e[30];let I;e[31]!==t||e[32]!==c||e[33]!==s||e[34]!==r?(I=t&&c.length>0&&n.jsxs(n.Fragment,{children:[n.jsx(be,{count:c.length,onClearSelection:()=>G([])}),n.jsx(Ae,{content:s("button.Settings"),placement:"above",alignment:"start",children:n.jsx(Ie,{icon:n.jsx(Te,{style:{color:r.colorInfo}}),onClick:()=>{ue(!0)}})})]}),e[31]=t,e[32]=c,e[33]=s,e[34]=r,e[35]=I):I=e[35];const oe=se!==ae||d!==i;let T;e[36]!==o?(T=m=>{o(m)},e[36]=o,e[37]=T):T=e[37];let w;e[38]!==i||e[39]!==oe||e[40]!==T?(w=n.jsx(Be,{settingId:"pending-session-list",defaultAutoUpdateDelay:1e4,loading:oe,value:i,onChange:T}),e[38]=i,e[39]=oe,e[40]=T,e[41]=w):w=e[41];let P;e[42]!==I||e[43]!==w?(P=n.jsxs(de,{gap:"xs",children:[I,w]}),e[42]=I,e[43]=w,e[44]=P):P=e[44];let M;e[45]!==A||e[46]!==P?(M=n.jsxs(de,{align:"stretch",justify:"between",children:[A,P]}),e[45]=A,e[46]=P,e[47]=M):M=e[47];let x;e[48]!==t||e[49]!==c||e[50]!==(a==null?void 0:a.edges)?(x=t?{type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(m){return{disabled:m.status!=="PENDING"}},onChange:m=>{Pe(m,ce(a==null?void 0:a.edges.map(qe)),G)},selectedRowKeys:we(c,He)}:void 0,e[48]=t,e[49]=c,e[50]=a==null?void 0:a.edges,e[51]=x):x=e[51];let j;e[52]!==F.hash||e[53]!==F.pathname||e[54]!==F.search||e[55]!==ee?(j=m=>{const z=new URLSearchParams(F.search);z.set("sessionDetail",m.row_id),ee({pathname:F.pathname,hash:F.hash,search:z.toString()},{state:{sessionDetailDrawerFrgmt:m,createdAt:new Date().toISOString()}})},e[52]=F.hash,e[53]=F.pathname,e[54]=F.search,e[55]=ee,e[56]=j):j=e[56];const ie=se!==ae;let B;e[57]!==(a==null?void 0:a.edges)?(B=ce(a==null?void 0:a.edges.map(Xe)),e[57]=a==null?void 0:a.edges,e[58]=B):B=e[58];const re=(a==null?void 0:a.count)??0;let R;e[59]!==h?(R=(m,z)=>{me(m)&&me(z)&&h({current:m,pageSize:z})},e[59]=h,e[60]=R):R=e[60];let D;e[61]!==re||e[62]!==R||e[63]!==k.current||e[64]!==k.pageSize?(D={pageSize:k.pageSize,current:k.current,total:re,onChange:R},e[61]=re,e[62]=R,e[63]=k.current,e[64]=k.pageSize,e[65]=D):D=e[65];let E;e[66]!==g||e[67]!==y?(E={columnOverrides:g,onColumnOverridesChange:y},e[66]=g,e[67]=y,e[68]=E):E=e[68];let V;e[69]!==t||e[70]!==x||e[71]!==j||e[72]!==ie||e[73]!==B||e[74]!==D||e[75]!==E?(V=n.jsx(Re,{disableSorter:!0,enablePriorityColumn:t,rowSelection:x,onClickSessionName:j,loading:ie,sessionsFrgmt:B,pagination:D,tableSettings:E}),e[69]=t,e[70]=x,e[71]=j,e[72]=ie,e[73]=B,e[74]=D,e[75]=E,e[76]=V):V=e[76];let O;e[77]!==o?(O=m=>{ue(!1),m&&(G([]),o())},e[77]=o,e[78]=O):O=e[78];let U;e[79]!==Z||e[80]!==c||e[81]!==O?(U=n.jsx(De,{children:n.jsx(Ee,{sessionFrgmts:c,open:Z,onRequestClose:O})}),e[79]=Z,e[80]=c,e[81]=O,e[82]=U):U=e[82];let J;return e[83]!==M||e[84]!==V||e[85]!==U||e[86]!==K?(J=n.jsxs(de,{direction:"column",align:"stretch",gap:"sm",children:[K,M,V,U]}),e[83]=M,e[84]=V,e[85]=U,e[86]=K,e[87]=J):J=e[87],J};function qe(e){return e==null?void 0:e.node}function He(e){return e.id}function Xe(e){return e==null?void 0:e.node}const Je=Qe.lazy(()=>ze(()=>import("./AdminComputeSessionListPage-8MyVqpSd.js"),__vite__mapDeps([0,1,2,3]))),Ze=Ue(["compute-sessions","pending-sessions"]).withDefault("compute-sessions"),cn=()=>{"use memo";const e=pe.c(18),{t:s}=Se(),{currentTab:r,onTabChange:p}=Ve(Ze);let l;e[0]!==s?(l=Oe([{key:"compute-sessions",label:s("webui.menu.Sessions")},{key:"pending-sessions",label:s("adminSession.PendingSessions")}]),e[0]=s,e[1]=l):l=e[1];let t;e[2]===Symbol.for("react.memo_cache_sentinel")?(t=n.jsx(Ge,{}),e[2]=t):t=e[2];let i;e[3]!==r?(i=r==="compute-sessions"&&n.jsx(ge,{children:n.jsx(Je,{})}),e[3]=r,e[4]=i):i=e[4];let o;e[5]!==r?(o=r==="pending-sessions"&&n.jsx(ge,{children:n.jsx(Ye,{})}),e[5]=r,e[6]=o):o=e[6];let u;e[7]!==i||e[8]!==o?(u=n.jsxs(Q.Suspense,{fallback:t,children:[i,o]}),e[7]=i,e[8]=o,e[9]=u):u=e[9];let d;e[10]!==r||e[11]!==p||e[12]!==l||e[13]!==u?(d=n.jsx($e,{activeTabKey:r,onTabChange:p,tabList:l,children:u}),e[10]=r,e[11]=p,e[12]=l,e[13]=u,e[14]=d):d=e[14];let S;e[15]===Symbol.for("react.memo_cache_sentinel")?(S=n.jsx(We,{project:null}),e[15]=S):S=e[15];let g;return e[16]!==d?(g=n.jsxs(n.Fragment,{children:[d,S]}),e[16]=d,e[17]=g):g=e[17],g};export{cn as default};
//# sourceMappingURL=AdminSessionPage-mNC1wz3A.js.map
