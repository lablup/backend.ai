const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["assets/AdminComputeSessionListPage-B4Dompuo.js","assets/index-B-6GqBhJ.js","assets/index-HL1IssMN.css","assets/BAIAdminProjectSelect-B2xlnf4n.js"])))=>i.map(i=>d[i]);
import{i as he,u as Ce,ac as Ne,a as ve,aO as Le,ag as be,bt as Ae,l as U,ak as Ie,ez as Te,a8 as we,Z as Pe,ad as Me,bG as xe,r as Be,j as n,F as je,cb as Re,s as De,Q as Ve,bM as Ee,am as Oe,ej as Qe,aT as ye,bh as Ge,ao as Ue,dx as ze,c as Se,bN as _e,aY as $e,ap as We,ht as He,cp as Ye,ai as qe,ca as Ze,b_ as Je,dQ as Xe,aV as en,cr as ke,d as nn}from"./index-B-6GqBhJ.js";import{u as an,B as sn}from"./BAIResourceGroupSelect-D-ou9BhS.js";import ln from"./SessionDetailAndContainerLogOpenerLegacy-DFS6QjgN.js";import"./SessionDetailDrawer-_Qk8OrZd.js";import"./scroll-text-CncKp3rA.js";import"./orderBy-BcAKhHRm.js";import"./FolderLink-BixUYyr6.js";import"./zip-DUWDYNfS.js";import"./unzip-DGQyn8Q9.js";import"./ScopedAuditLog-D4HOQVjA.js";import"./BAIGraphQLPropertyFilter-Bp1GJNAy.js";import"./rotate-ccw-clock-DIhz6B-L.js";const Ke=(function(){var e={defaultValue:20,kind:"LocalArgument",name:"first"},s={defaultValue:0,kind:"LocalArgument",name:"offset"},r={defaultValue:null,kind:"LocalArgument",name:"resource_group_id"},p=[{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"resource_group_id",variableName:"resource_group_id"}],l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},m=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],f={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},y=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[l,o,i,d],storageKey:null}],storageKey:null},t],_={alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null};return{fragment:{argumentDefinitions:[e,s,r],kind:"Fragment",metadata:null,name:"PendingSessionNodeListQuery",selections:[{alias:null,args:p,concreteType:"SessionPendingQueueConnection",kind:"LinkedField",name:"session_pending_queue",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"SessionPendingQueueEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[l,{args:null,kind:"FragmentSpread",name:"SessionDetailDrawerFragment"},{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"},{args:null,kind:"FragmentSpread",name:"EditSessionPriorityModalFragment"}],storageKey:null}],storageKey:null},action:"THROW"},t],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[r,e,s],kind:"Operation",name:"PendingSessionNodeListQuery",selections:[{alias:null,args:p,concreteType:"SessionPendingQueueConnection",kind:"LinkedField",name:"session_pending_queue",plural:!1,selections:[{alias:null,args:null,concreteType:"SessionPendingQueueEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},o,i,{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},l],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},d,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[o,i,l],storageKey:null}],storageKey:null},t],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},c,g,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:m,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:m,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},c,l],storageKey:null},l,o,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},d,f,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:y,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:y,storageKey:null},f,{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},_,{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},g,{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},_,{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domain_name",storageKey:null}],storageKey:null}],storageKey:null},t],storageKey:null}]},params:{cacheID:"8abfd23bc4d95f2d1e8ae5b5354ab1e5",id:null,metadata:{},name:"PendingSessionNodeListQuery",operationKind:"query",text:`query PendingSessionNodeListQuery(
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
`}}})();Ke.hash="4b2123e18974d3e3a0839a2acca5b55e";const tn=()=>{"use memo";const e=he.c(96),{t:s}=Ce(),{token:r}=Ne.useToken(),p=ve();let l;e[0]!==p?(l=p.isManagerVersionCompatibleWith("26.4.0"),e[0]=p,e[1]=l):l=e[1];const t=l,[o,i]=Le();let d;e[2]===Symbol.for("react.memo_cache_sentinel")?(d=be.withOptions({history:"replace"}),e[2]=d):d=e[2];const[c,g]=Ae("resourceGroup",d),m=U.useDeferredValue(o);let f;e[3]===Symbol.for("react.memo_cache_sentinel")?(f={isActive:!0},e[3]=f):f=e[3];const y=an(f);let _;e[4]!==y||e[5]!==c?(_=Ie(y,c)?c??void 0:Te(y),e[4]=y,e[5]=c,e[6]=_):_=e[6];const z=_,Fe=U.useDeferredValue(z),[se,le]=we("table_column_overrides.PendingSessionNodeList");let W;e[7]===Symbol.for("react.memo_cache_sentinel")?(W=[],e[7]=W):W=e[7];const[S,H]=U.useState(W),[te,fe]=U.useState(!1),oe=Pe(),F=Me();let Y;e[8]===Symbol.for("react.memo_cache_sentinel")?(Y={current:1,pageSize:10},e[8]=Y):Y=e[8];const{baiPaginationOption:k,tablePaginationOption:h,setTablePaginationOption:C}=xe(Y),ie=Fe??"";let q;e[9]!==k.first||e[10]!==k.offset||e[11]!==ie?(q={resource_group_id:ie,first:k.first,offset:k.offset},e[9]=k.first,e[10]=k.offset,e[11]=ie,e[12]=q):q=e[12];const re=q,de=U.useDeferredValue(re);let Z;e[13]===Symbol.for("react.memo_cache_sentinel")?(Z=Ke,e[13]=Z):Z=e[13];const ue=m===Ge?"store-and-network":"network-only";let J;e[14]!==m||e[15]!==ue?(J={fetchKey:m,fetchPolicy:ue},e[14]=m,e[15]=ue,e[16]=J):J=e[16];const{session_pending_queue:a}=Be.useLazyLoadQuery(Z,de,J);let K;e[17]!==s?(K=s("adminSession.PendingSessionsScopedToResourceGroup"),e[17]=s,e[18]=K):K=e[18];let N;e[19]!==K?(N=n.jsx(Ue,{type:"info",showIcon:!0,description:K}),e[19]=K,e[20]=N):N=e[20];let v;e[21]!==s?(v=s("session.ResourceGroup"),e[21]=s,e[22]=v):v=e[22];let X;e[23]===Symbol.for("react.memo_cache_sentinel")?(X={marginBottom:0},e[23]=X):X=e[23];let ee,ne;e[24]===Symbol.for("react.memo_cache_sentinel")?(ee={isActive:!0},ne={minWidth:100},e[24]=ee,e[25]=ne):(ee=e[24],ne=e[25]);const ce=z!==Fe;let L;e[26]!==s?(L=s("general.ResourceGroup"),e[26]=s,e[27]=L):L=e[27];let b;e[28]!==g||e[29]!==C?(b=u=>{g(u??null),C({current:1}),H([])},e[28]=g,e[29]=C,e[30]=b):b=e[30];let A;e[31]!==z||e[32]!==ce||e[33]!==L||e[34]!==b?(A=n.jsx(sn,{filter:ee,style:ne,loading:ce,popupMatchSelectWidth:!1,tooltip:L,value:z,onChange:b}),e[31]=z,e[32]=ce,e[33]=L,e[34]=b,e[35]=A):A=e[35];let I;e[36]!==v||e[37]!==A?(I=n.jsx(je.Item,{label:v,style:X,children:A}),e[36]=v,e[37]=A,e[38]=I):I=e[38];let T;e[39]!==t||e[40]!==S||e[41]!==s||e[42]!==r?(T=t&&S.length>0&&n.jsxs(n.Fragment,{children:[n.jsx(Re,{count:S.length,onClearSelection:()=>H([])}),n.jsx(De,{content:s("button.Settings"),placement:"above",alignment:"start",children:n.jsx(Ve,{icon:n.jsx(Ee,{style:{color:r.colorInfo}}),onClick:()=>{fe(!0)}})})]}),e[39]=t,e[40]=S,e[41]=s,e[42]=r,e[43]=T):T=e[43];const me=de!==re||m!==o;let w;e[44]!==i?(w=u=>{i(u)},e[44]=i,e[45]=w):w=e[45];let P;e[46]!==o||e[47]!==me||e[48]!==w?(P=n.jsx(ze,{settingId:"pending-session-list",defaultAutoUpdateDelay:1e4,loading:me,value:o,onChange:w}),e[46]=o,e[47]=me,e[48]=w,e[49]=P):P=e[49];let M;e[50]!==T||e[51]!==P?(M=n.jsxs(Se,{gap:"xs",children:[T,P]}),e[50]=T,e[51]=P,e[52]=M):M=e[52];let x;e[53]!==I||e[54]!==M?(x=n.jsxs(Se,{align:"stretch",justify:"between",children:[I,M]}),e[53]=I,e[54]=M,e[55]=x):x=e[55];let B;e[56]!==t||e[57]!==S||e[58]!==(a==null?void 0:a.edges)?(B=t?{type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(u){return{disabled:u.status!=="PENDING"}},onChange:u=>{Qe(u,ye(a==null?void 0:a.edges.map(on)),H)},selectedRowKeys:Oe(S,rn)}:void 0,e[56]=t,e[57]=S,e[58]=a==null?void 0:a.edges,e[59]=B):B=e[59];let j;e[60]!==F.hash||e[61]!==F.pathname||e[62]!==F.search||e[63]!==oe?(j=u=>{const $=new URLSearchParams(F.search);$.set("sessionDetail",u.row_id),oe({pathname:F.pathname,hash:F.hash,search:$.toString()},{state:{sessionDetailDrawerFrgmt:u,createdAt:new Date().toISOString()}})},e[60]=F.hash,e[61]=F.pathname,e[62]=F.search,e[63]=oe,e[64]=j):j=e[64];const ge=de!==re;let R;e[65]!==(a==null?void 0:a.edges)?(R=ye(a==null?void 0:a.edges.map(dn)),e[65]=a==null?void 0:a.edges,e[66]=R):R=e[66];const pe=(a==null?void 0:a.count)??0;let D;e[67]!==C?(D=(u,$)=>{_e(u)&&_e($)&&C({current:u,pageSize:$})},e[67]=C,e[68]=D):D=e[68];let V;e[69]!==pe||e[70]!==D||e[71]!==h.current||e[72]!==h.pageSize?(V={pageSize:h.pageSize,current:h.current,total:pe,onChange:D},e[69]=pe,e[70]=D,e[71]=h.current,e[72]=h.pageSize,e[73]=V):V=e[73];let E;e[74]!==se||e[75]!==le?(E={columnOverrides:se,onColumnOverridesChange:le},e[74]=se,e[75]=le,e[76]=E):E=e[76];let O;e[77]!==t||e[78]!==B||e[79]!==j||e[80]!==ge||e[81]!==R||e[82]!==V||e[83]!==E?(O=n.jsx($e,{disableSorter:!0,enablePriorityColumn:t,rowSelection:B,onClickSessionName:j,loading:ge,sessionsFrgmt:R,pagination:V,tableSettings:E}),e[77]=t,e[78]=B,e[79]=j,e[80]=ge,e[81]=R,e[82]=V,e[83]=E,e[84]=O):O=e[84];let Q;e[85]!==i?(Q=u=>{fe(!1),u&&(H([]),i())},e[85]=i,e[86]=Q):Q=e[86];let G;e[87]!==te||e[88]!==S||e[89]!==Q?(G=n.jsx(We,{children:n.jsx(He,{sessionFrgmts:S,open:te,onRequestClose:Q})}),e[87]=te,e[88]=S,e[89]=Q,e[90]=G):G=e[90];let ae;return e[91]!==N||e[92]!==x||e[93]!==O||e[94]!==G?(ae=n.jsxs(Se,{direction:"column",align:"stretch",gap:"sm",children:[N,x,O,G]}),e[91]=N,e[92]=x,e[93]=O,e[94]=G,e[95]=ae):ae=e[95],ae};function on(e){return e==null?void 0:e.node}function rn(e){return e.id}function dn(e){return e==null?void 0:e.node}const un=Je.lazy(()=>Xe(()=>import("./AdminComputeSessionListPage-B4Dompuo.js"),__vite__mapDeps([0,1,2,3]))),cn=Ze(["compute-sessions","pending-sessions"]).withDefault("compute-sessions"),Nn=()=>{"use memo";const e=he.c(18),{t:s}=Ce(),{currentTab:r,onTabChange:p}=Ye(cn);let l;e[0]!==s?(l=qe([{key:"compute-sessions",label:s("webui.menu.Sessions")},{key:"pending-sessions",label:s("adminSession.PendingSessions")}]),e[0]=s,e[1]=l):l=e[1];let t;e[2]===Symbol.for("react.memo_cache_sentinel")?(t=n.jsx(en,{}),e[2]=t):t=e[2];let o;e[3]!==r?(o=r==="compute-sessions"&&n.jsx(ke,{children:n.jsx(un,{})}),e[3]=r,e[4]=o):o=e[4];let i;e[5]!==r?(i=r==="pending-sessions"&&n.jsx(ke,{children:n.jsx(tn,{})}),e[5]=r,e[6]=i):i=e[6];let d;e[7]!==o||e[8]!==i?(d=n.jsxs(U.Suspense,{fallback:t,children:[o,i]}),e[7]=o,e[8]=i,e[9]=d):d=e[9];let c;e[10]!==r||e[11]!==p||e[12]!==l||e[13]!==d?(c=n.jsx(nn,{activeTabKey:r,onTabChange:p,tabList:l,children:d}),e[10]=r,e[11]=p,e[12]=l,e[13]=d,e[14]=c):c=e[14];let g;e[15]===Symbol.for("react.memo_cache_sentinel")?(g=n.jsx(ln,{project:null}),e[15]=g):g=e[15];let m;return e[16]!==c?(m=n.jsxs(n.Fragment,{children:[c,g]}),e[16]=c,e[17]=m):m=e[17],m};export{Nn as default};
//# sourceMappingURL=AdminSessionPage-DbYi8PZd.js.map
