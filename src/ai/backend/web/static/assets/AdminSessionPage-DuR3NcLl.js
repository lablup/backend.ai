const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["assets/AdminComputeSessionListPage-CtrFaISF.js","assets/index-4XAoWQdC.js","assets/index-CJTJ4MIU.css","assets/BAIAdminProjectSelect-oLGLqaw6.js"])))=>i.map(i=>d[i]);
import{i as _e,u as ke,ab as Ce,aM as Ke,ao as Ne,cB as Le,l as G,ai as Ae,e_ as be,a7 as ve,X as Ie,ac as Te,bJ as Pe,r as we,j as a,_ as Be,cf as xe,q as Me,N as je,bP as Re,ak as De,aT as fe,bk as Ee,am as Ve,dJ as Oe,c as ge,eO as Qe,bQ as Fe,aY as Ge,an as Ue,hL as ze,cs as $e,ag as We,ce as He,c1 as Je,e1 as Ye,aV as Xe,cu as ye,d as Ze}from"./index-4XAoWQdC.js";import{u as qe,B as en}from"./BAIResourceGroupSelect-jox4l-pQ.js";import nn from"./SessionDetailAndContainerLogOpenerLegacy-BYDYWHv3.js";import"./SessionDetailDrawer-r93Udkje.js";import"./scroll-text-CMSbKmDU.js";import"./orderBy-DR_M0o9Z.js";import"./FolderLink-B13SaUe_.js";import"./ScopedAuditLog-BTAaHqWC.js";import"./rotate-ccw-clock-Bp9ZfyAh.js";const he=(function(){var e={defaultValue:20,kind:"LocalArgument",name:"first"},l={defaultValue:0,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"resource_group_id"},m=[{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"resource_group_id",variableName:"resource_group_id"}],s={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},g=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],p={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},y=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[s,o,u,i],storageKey:null}],storageKey:null},d];return{fragment:{argumentDefinitions:[e,l,t],kind:"Fragment",metadata:null,name:"PendingSessionNodeListQuery",selections:[{alias:null,args:m,concreteType:"SessionPendingQueueConnection",kind:"LinkedField",name:"session_pending_queue",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"SessionPendingQueueEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[s,{args:null,kind:"FragmentSpread",name:"SessionDetailDrawerFragment"},{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"},{args:null,kind:"FragmentSpread",name:"EditSessionPriorityModalFragment"}],storageKey:null}],storageKey:null},action:"THROW"},d],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[t,e,l],kind:"Operation",name:"PendingSessionNodeListQuery",selections:[{alias:null,args:m,concreteType:"SessionPendingQueueConnection",kind:"LinkedField",name:"session_pending_queue",plural:!1,selections:[{alias:null,args:null,concreteType:"SessionPendingQueueEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[s,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},o,u,{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},s],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},i,{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[o,u,s],storageKey:null}],storageKey:null},d],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},c,{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:g,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:g,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},c,s],storageKey:null},s,o,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},i,p,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:y,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:y,storageKey:null},p,{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domain_name",storageKey:null}],storageKey:null}],storageKey:null},d],storageKey:null}]},params:{cacheID:"3f30026a415d9c5bbab3359e0e0ce832",id:null,metadata:{},name:"PendingSessionNodeListQuery",operationKind:"query",text:`query PendingSessionNodeListQuery(
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
`}}})();he.hash="4b2123e18974d3e3a0839a2acca5b55e";const an=()=>{"use memo";const e=_e.c(95),{t:l}=ke(),{token:t}=Ce(),[m,s]=Ke();let d;e[0]===Symbol.for("react.memo_cache_sentinel")?(d=Ne.withOptions({history:"replace"}),e[0]=d):d=e[0];const[o,u]=Le("resourceGroup",d),i=G.useDeferredValue(m);let c;e[1]===Symbol.for("react.memo_cache_sentinel")?(c={isActive:!0},e[1]=c):c=e[1];const g=qe(c);let p;e[2]!==g||e[3]!==o?(p=Ae(g,o)?o??void 0:be(g),e[2]=g,e[3]=o,e[4]=p):p=e[4];const y=p,pe=G.useDeferredValue(y),[ee,ne]=ve("table_column_overrides.PendingSessionNodeList");let U;e[5]===Symbol.for("react.memo_cache_sentinel")?(U=[],e[5]=U):U=e[5];const[S,z]=G.useState(U),[ae,Se]=G.useState(!1),se=Ie(),F=Te();let $;e[6]===Symbol.for("react.memo_cache_sentinel")?($={current:1,pageSize:10},e[6]=$):$=e[6];const{baiPaginationOption:_,tablePaginationOption:k,setTablePaginationOption:h}=Pe($),le=pe??"";let W;e[7]!==_.first||e[8]!==_.offset||e[9]!==le?(W={resource_group_id:le,first:_.first,offset:_.offset},e[7]=_.first,e[8]=_.offset,e[9]=le,e[10]=W):W=e[10];const te=W,oe=G.useDeferredValue(te);let H;e[11]===Symbol.for("react.memo_cache_sentinel")?(H=he,e[11]=H):H=e[11];const ie=i===Ee?"store-and-network":"network-only";let J;e[12]!==i||e[13]!==ie?(J={fetchKey:i,fetchPolicy:ie},e[12]=i,e[13]=ie,e[14]=J):J=e[14];const{session_pending_queue:n}=we.useLazyLoadQuery(H,oe,J);let C;e[15]!==l?(C=l("adminSession.PendingSessionsScopedToResourceGroup"),e[15]=l,e[16]=C):C=e[16];let K;e[17]!==C?(K=a.jsx(Ve,{type:"info",showIcon:!0,description:C}),e[17]=C,e[18]=K):K=e[18];let N;e[19]!==l?(N=l("session.ResourceGroup"),e[19]=l,e[20]=N):N=e[20];let Y;e[21]===Symbol.for("react.memo_cache_sentinel")?(Y={marginBottom:0},e[21]=Y):Y=e[21];let X,Z;e[22]===Symbol.for("react.memo_cache_sentinel")?(X={isActive:!0},Z={minWidth:100},e[22]=X,e[23]=Z):(X=e[22],Z=e[23]);const re=y!==pe;let L;e[24]!==l?(L=l("general.ResourceGroup"),e[24]=l,e[25]=L):L=e[25];let A;e[26]!==u||e[27]!==h?(A=r=>{u(r??null),h({current:1}),z([])},e[26]=u,e[27]=h,e[28]=A):A=e[28];let b;e[29]!==y||e[30]!==re||e[31]!==L||e[32]!==A?(b=a.jsx(en,{filter:X,style:Z,loading:re,popupMatchSelectWidth:!1,tooltip:L,value:y,onChange:A}),e[29]=y,e[30]=re,e[31]=L,e[32]=A,e[33]=b):b=e[33];let v;e[34]!==N||e[35]!==b?(v=a.jsx(Be.Item,{label:N,style:Y,children:b}),e[34]=N,e[35]=b,e[36]=v):v=e[36];let I;e[37]!==S.length||e[38]!==l||e[39]!==t?(I=S.length>0&&a.jsxs(a.Fragment,{children:[a.jsx(xe,{count:S.length,onClearSelection:()=>z([])}),a.jsx(Me,{content:l("button.Settings"),placement:"above",alignment:"start",children:a.jsx(je,{icon:a.jsx(Re,{style:{color:t("--color-info")}}),onClick:()=>{Se(!0)}})})]}),e[37]=S.length,e[38]=l,e[39]=t,e[40]=I):I=e[40];const de=oe!==te||i!==m;let T;e[41]!==s?(T=r=>{s(r)},e[41]=s,e[42]=T):T=e[42];let P;e[43]!==m||e[44]!==de||e[45]!==T?(P=a.jsx(Oe,{settingId:"pending-session-list",defaultAutoUpdateDelay:1e4,loading:de,value:m,onChange:T}),e[43]=m,e[44]=de,e[45]=T,e[46]=P):P=e[46];let w;e[47]!==I||e[48]!==P?(w=a.jsxs(ge,{gap:"xs",children:[I,P]}),e[47]=I,e[48]=P,e[49]=w):w=e[49];let B;e[50]!==v||e[51]!==w?(B=a.jsxs(ge,{align:"stretch",justify:"between",children:[v,w]}),e[50]=v,e[51]=w,e[52]=B):B=e[52];let x;if(e[53]!==S||e[54]!==(n==null?void 0:n.edges)){let r;e[56]!==(n==null?void 0:n.edges)?(r=me=>{Qe(me,fe(n==null?void 0:n.edges.map(sn)),z)},e[56]=n==null?void 0:n.edges,e[57]=r):r=e[57];let f;e[58]!==S?(f=De(S,ln),e[58]=S,e[59]=f):f=e[59],x={type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(me){return{disabled:me.status!=="PENDING"}},onChange:r,selectedRowKeys:f},e[53]=S,e[54]=n==null?void 0:n.edges,e[55]=x}else x=e[55];let M;e[60]!==F.hash||e[61]!==F.pathname||e[62]!==F.search||e[63]!==se?(M=r=>{const f=new URLSearchParams(F.search);f.set("sessionDetail",r.row_id),se({pathname:F.pathname,hash:F.hash,search:f.toString()},{state:{sessionDetailDrawerFrgmt:r,createdAt:new Date().toISOString()}})},e[60]=F.hash,e[61]=F.pathname,e[62]=F.search,e[63]=se,e[64]=M):M=e[64];const ue=oe!==te;let j;e[65]!==(n==null?void 0:n.edges)?(j=fe(n==null?void 0:n.edges.map(tn)),e[65]=n==null?void 0:n.edges,e[66]=j):j=e[66];const ce=(n==null?void 0:n.count)??0;let R;e[67]!==h?(R=(r,f)=>{Fe(r)&&Fe(f)&&h({current:r,pageSize:f})},e[67]=h,e[68]=R):R=e[68];let D;e[69]!==ce||e[70]!==R||e[71]!==k.current||e[72]!==k.pageSize?(D={pageSize:k.pageSize,current:k.current,total:ce,onChange:R},e[69]=ce,e[70]=R,e[71]=k.current,e[72]=k.pageSize,e[73]=D):D=e[73];let E;e[74]!==ee||e[75]!==ne?(E={columnOverrides:ee,onColumnOverridesChange:ne},e[74]=ee,e[75]=ne,e[76]=E):E=e[76];let V;e[77]!==x||e[78]!==M||e[79]!==ue||e[80]!==j||e[81]!==D||e[82]!==E?(V=a.jsx(Ge,{disableSorter:!0,enablePriorityColumn:!0,rowSelection:x,onClickSessionName:M,loading:ue,sessionsFrgmt:j,pagination:D,tableSettings:E}),e[77]=x,e[78]=M,e[79]=ue,e[80]=j,e[81]=D,e[82]=E,e[83]=V):V=e[83];let O;e[84]!==s?(O=r=>{Se(!1),r&&(z([]),s())},e[84]=s,e[85]=O):O=e[85];let Q;e[86]!==ae||e[87]!==S||e[88]!==O?(Q=a.jsx(Ue,{children:a.jsx(ze,{sessionFrgmts:S,open:ae,onRequestClose:O})}),e[86]=ae,e[87]=S,e[88]=O,e[89]=Q):Q=e[89];let q;return e[90]!==K||e[91]!==B||e[92]!==V||e[93]!==Q?(q=a.jsxs(ge,{direction:"column",align:"stretch",gap:"sm",children:[K,B,V,Q]}),e[90]=K,e[91]=B,e[92]=V,e[93]=Q,e[94]=q):q=e[94],q};function sn(e){return e==null?void 0:e.node}function ln(e){return e.id}function tn(e){return e==null?void 0:e.node}const on=Je.lazy(()=>Ye(()=>import("./AdminComputeSessionListPage-CtrFaISF.js"),__vite__mapDeps([0,1,2,3]))),rn=He(["compute-sessions","pending-sessions"]).withDefault("compute-sessions"),yn=()=>{"use memo";const e=_e.c(18),{t:l}=ke(),{currentTab:t,onTabChange:m}=$e(rn);let s;e[0]!==l?(s=We([{key:"compute-sessions",label:l("webui.menu.Sessions")},{key:"pending-sessions",label:l("adminSession.PendingSessions")}]),e[0]=l,e[1]=s):s=e[1];let d;e[2]===Symbol.for("react.memo_cache_sentinel")?(d=a.jsx(Xe,{}),e[2]=d):d=e[2];let o;e[3]!==t?(o=t==="compute-sessions"&&a.jsx(ye,{children:a.jsx(on,{})}),e[3]=t,e[4]=o):o=e[4];let u;e[5]!==t?(u=t==="pending-sessions"&&a.jsx(ye,{children:a.jsx(an,{})}),e[5]=t,e[6]=u):u=e[6];let i;e[7]!==o||e[8]!==u?(i=a.jsxs(G.Suspense,{fallback:d,children:[o,u]}),e[7]=o,e[8]=u,e[9]=i):i=e[9];let c;e[10]!==t||e[11]!==m||e[12]!==s||e[13]!==i?(c=a.jsx(Ze,{activeTabKey:t,onTabChange:m,tabList:s,children:i}),e[10]=t,e[11]=m,e[12]=s,e[13]=i,e[14]=c):c=e[14];let g;e[15]===Symbol.for("react.memo_cache_sentinel")?(g=a.jsx(nn,{project:null}),e[15]=g):g=e[15];let p;return e[16]!==c?(p=a.jsxs(a.Fragment,{children:[c,g]}),e[16]=c,e[17]=p):p=e[17],p};export{yn as default};
//# sourceMappingURL=AdminSessionPage-DuR3NcLl.js.map
