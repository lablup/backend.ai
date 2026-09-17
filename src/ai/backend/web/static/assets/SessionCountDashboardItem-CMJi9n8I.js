import{u as Z,ac as ee,l as ne,j as n,c as h,aD as ae,aP as se,i as Ae,bk as Te,r as ge,bl as Ne,bm as C,bn as H,al as be,bo as Re,am as De,ar as me,aV as Ee,bp as xe,bq as Me,br as Fe,bs as we,bt as je,ag as Be,aY as Ve,O as Pe,aT as Qe,ap as Ue,aU as qe,aW as $e}from"./index-B-6GqBhJ.js";import{A as ze}from"./AgentList-BUaGq6nS.js";import{S as Xe}from"./SessionDetailDrawer-_Qk8OrZd.js";const We=({fetchKey:l,onChangeFetchKey:e})=>{const{t:a}=Z(),{token:i}=ee.useToken(),[t,d]=ne.useTransition();return n.jsxs(h,{direction:"column",align:"stretch",style:{paddingInline:i.paddingXL,height:"100%"},children:[n.jsx(ae,{title:a("activeAgent.ActiveAgents"),tooltip:a("activeAgent.ActiveAgentsTooltip",{count:5}),extra:n.jsx(se,{size:"small",loading:t,value:"",onChange:s=>{d(()=>{e==null||e(s)})},type:"text",style:{backgroundColor:"transparent"}})}),n.jsx(h,{direction:"column",align:"stretch",style:{flex:1,overflowY:"auto",overflowX:"hidden",marginBottom:i.margin},children:n.jsx(ze,{fetchKey:l,onChangeFetchKey:e,headerProps:{style:{display:"none"}},tableProps:{pagination:{pageSize:3,showSizeChanger:!1}}})})]})},ke={fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"AgentStatsRefetchQuery",selections:[{args:null,kind:"FragmentSpread",name:"AgentStatsFragment"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"AgentStatsRefetchQuery",selections:[{alias:null,args:null,concreteType:"AgentStats",kind:"LinkedField",name:"agentStats",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentResource",kind:"LinkedField",name:"totalResource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"free",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capacity",storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"b2605aadfb3d6bd4a21f3f7887043e31",id:null,metadata:{},name:"AgentStatsRefetchQuery",operationKind:"query",text:`query AgentStatsRefetchQuery {
  ...AgentStatsFragment
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
`}};ke.hash="458be767c066ba74fbebc3d9d84638ca";const _e={argumentDefinitions:[],kind:"Fragment",metadata:{refetch:{connection:null,fragmentPathInResult:[],operation:ke}},name:"AgentStatsFragment",selections:[{alias:null,args:null,concreteType:"AgentStats",kind:"LinkedField",name:"agentStats",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentResource",kind:"LinkedField",name:"totalResource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"free",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capacity",storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null};_e.hash="458be767c066ba74fbebc3d9d84638ca";const He=l=>{"use memo";var pe,ye,fe;const e=Ae.c(86);let a,i,t,d;e[0]!==l?({queryRef:d,isRefetching:i,extra:a,...t}=l,e[0]=l,e[1]=a,e[2]=i,e[3]=t,e[4]=d):(a=e[1],i=e[2],t=e[3],d=e[4]);const{t:s}=Z(),{token:u}=ee.useToken(),[F,k]=ne.useTransition();let c;e[5]===Symbol.for("react.memo_cache_sentinel")?(c={defaultValue:"used",trigger:"onDisplayTypeChange",defaultValuePropName:"defaultDisplayType"},e[5]=c):c=e[5];const[o,m]=Te(t,c);let _;e[6]===Symbol.for("react.memo_cache_sentinel")?(_=_e,e[6]=_):_=e[6];const[L,Q]=ge.useRefetchableFragment(_,d),r=Ne();let te;e:{const P=(pe=L.agentStats)==null?void 0:pe.totalResource;if(!P){let S;e[7]===Symbol.for("react.memo_cache_sentinel")?(S={cpu:null,memory:null,accelerators:[]},e[7]=S):S=e[7],te=S;break e}const p=P.free,y=P.used,g=P.capacity,U=(ye=r==null?void 0:r.resourceSlotsInRG)==null?void 0:ye.cpu,f=(fe=r==null?void 0:r.resourceSlotsInRG)==null?void 0:fe.mem;let O;e[8]!==g||e[9]!==U||e[10]!==p||e[11]!==y?(O=U?{used:{current:C(y.cpu||0),total:C(g.cpu||0)},free:{current:C(p.cpu||0),total:C(g.cpu||0)},metadata:{title:U.human_readable_name,displayUnit:U.display_unit}}:null,e[8]=g,e[9]=U,e[10]=p,e[11]=y,e[12]=O):O=e[12];const re=O;let G;e[13]!==g||e[14]!==p||e[15]!==f||e[16]!==y?(G=f?{used:{current:H(y.mem||0,f.display_unit),total:H(g.mem||0,f.display_unit)},free:{current:H(p.mem||0,f.display_unit),total:H(g.mem||0,f.display_unit)},metadata:{title:f.human_readable_name,displayUnit:f.display_unit}}:null,e[13]=g,e[14]=p,e[15]=f,e[16]=y,e[17]=G):G=e[17];const de=G;let J;if(e[18]!==g||e[19]!==p||e[20]!==r.resourceSlotsInRG||e[21]!==y){let S;e[23]!==g||e[24]!==p||e[25]!==y?(S=(ce,W)=>{if(!ce)return null;const Ie=p[W]||0,Ke=y[W]||0,Se=g[W]||0;return{key:W,used:{current:C(Ke),total:C(Se)},free:{current:C(Ie),total:C(Se)},metadata:{title:ce.human_readable_name,displayUnit:ce.display_unit}}},e[23]=g,e[24]=p,e[25]=y,e[26]=S):S=e[26],J=be(Re(De(me(r==null?void 0:r.resourceSlotsInRG,["cpu","mem"]),S)),Oe),e[18]=g,e[19]=p,e[20]=r.resourceSlotsInRG,e[21]=y,e[22]=J}else J=e[22];const ue=J;let Y;e[27]!==ue||e[28]!==re||e[29]!==de?(Y={cpu:re,memory:de,accelerators:ue},e[27]=ue,e[28]=re,e[29]=de,e[30]=Y):Y=e[30],te=Y}const le=te;let v;e[31]!==t.style||e[32]!==u.padding||e[33]!==u.paddingXL?(v={paddingInline:u.paddingXL,paddingBottom:u.padding,...t.style},e[31]=t.style,e[32]=u.padding,e[33]=u.paddingXL,e[34]=v):v=e[34];let I;e[35]!==t?(I=me(t,["style"]),e[35]=t,e[36]=I):I=e[36];let K;e[37]!==s?(K=s("agentStats.AgentStats"),e[37]=s,e[38]=K):K=e[38];let A;e[39]!==K?(A=n.jsx(Me,{level:5,children:K}),e[39]=K,e[40]=A):A=e[40];let T;e[41]!==s?(T=s("agentStats.AgentStatsDescription"),e[41]=s,e[42]=T):T=e[42];let q;e[43]!==s?(q=s("dashboard.Used"),e[43]=s,e[44]=q):q=e[44];let $;e[45]!==s?($=s("dashboard.Free"),e[45]=s,e[46]=$):$=e[46];const ie=`${q}/${$}`;let N;e[47]!==m?(N=P=>m(P),e[47]=m,e[48]=N):N=e[48];let b;e[49]!==s?(b=s("dashboard.Used"),e[49]=s,e[50]=b):b=e[50];let R;e[51]!==b?(R=n.jsx(Fe,{value:"used",label:b}),e[51]=b,e[52]=R):R=e[52];let D;e[53]!==s?(D=s("dashboard.Free"),e[53]=s,e[54]=D):D=e[54];let E;e[55]!==D?(E=n.jsx(Fe,{value:"free",label:D}),e[55]=D,e[56]=E):E=e[56];let x;e[57]!==o||e[58]!==ie||e[59]!==N||e[60]!==R||e[61]!==E?(x=n.jsxs(we,{size:"sm",label:ie,value:o,onChange:N,children:[R,E]}),e[57]=o,e[58]=ie,e[59]=N,e[60]=R,e[61]=E,e[62]=x):x=e[62];const oe=F||i;let M;e[63]!==Q?(M=()=>{k(()=>{Q({},{fetchPolicy:"network-only"})})},e[63]=Q,e[64]=M):M=e[64];let z;e[65]===Symbol.for("react.memo_cache_sentinel")?(z={backgroundColor:"transparent"},e[65]=z):z=e[65];let w;e[66]!==oe||e[67]!==M?(w=n.jsx(se,{size:"small",loading:oe,value:"",onChange:M,type:"text",style:z}),e[66]=oe,e[67]=M,e[68]=w):w=e[68];let j;e[69]!==a||e[70]!==x||e[71]!==w?(j=n.jsxs(h,{gap:"xs",wrap:"wrap",children:[x,w,a]}),e[69]=a,e[70]=x,e[71]=w,e[72]=j):j=e[72];let B;e[73]!==j||e[74]!==A||e[75]!==T?(B=n.jsx(ae,{title:A,tooltip:T,extra:j}),e[73]=j,e[74]=A,e[75]=T,e[76]=B):B=e[76];let V;e[77]!==le||e[78]!==o||e[79]!==r.isLoading?(V=r.isLoading?n.jsx(Ee,{}):n.jsx(xe,{resourceData:le,displayType:o==="used"?"used":"free",progressMode:"normal"}),e[77]=le,e[78]=o,e[79]=r.isLoading,e[80]=V):V=e[80];let X;return e[81]!==B||e[82]!==V||e[83]!==v||e[84]!==I?(X=n.jsxs(h,{direction:"column",align:"stretch",style:v,...I,children:[B,V]}),e[81]=B,e[82]=V,e[83]=v,e[84]=I,e[85]=X):X=e[85],X};function Oe(l){return!!(l.used.current||l.used.total)}const Ce=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"scopeId"}],e={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},F=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],k={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[e,a,i,t],storageKey:null}],storageKey:null},c];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"RecentlyCreatedSessionRefetchQuery",selections:[{args:[{kind:"Variable",name:"scopeId",variableName:"scopeId"}],kind:"FragmentSpread",name:"RecentlyCreatedSessionFragment"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"RecentlyCreatedSessionRefetchQuery",selections:[{alias:null,args:[{kind:"Literal",name:"filter",value:'status == "running"'},{kind:"Literal",name:"first",value:5},{kind:"Literal",name:"order",value:"-created_at"},{kind:"Variable",name:"scope_id",variableName:"scopeId"}],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[e,a,i,t,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},d,s,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},u,{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},e,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:F,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:F,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},u,e],storageKey:null},a,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},t,s,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},k,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},e],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[a,i,e],storageKey:null}],storageKey:null},c],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},k,{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:o,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:o,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},d,{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domain_name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"77a85c4bd3c3b5c9c5243ec4ea2c0964",id:null,metadata:{},name:"RecentlyCreatedSessionRefetchQuery",operationKind:"query",text:`query RecentlyCreatedSessionRefetchQuery(
  $scopeId: ScopeField
) {
  ...RecentlyCreatedSessionFragment_3vJUag
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
`}}})();Ce.hash="aeaa38c05c8fe2c9a07946ed4a3fe214";const he={argumentDefinitions:[{defaultValue:null,kind:"LocalArgument",name:"scopeId"}],kind:"Fragment",metadata:{refetch:{connection:null,fragmentPathInResult:[],operation:Ce}},name:"RecentlyCreatedSessionFragment",selections:[{alias:null,args:[{kind:"Literal",name:"filter",value:'status == "running"'},{kind:"Literal",name:"first",value:5},{kind:"Literal",name:"order",value:"-created_at"},{kind:"Variable",name:"scope_id",variableName:"scopeId"}],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null};he.hash="aeaa38c05c8fe2c9a07946ed4a3fe214";const Ze=({queryRef:l,isRefetching:e,project:a})=>{var o;const{t:i}=Z(),{token:t}=ee.useToken(),[d,s]=je("sessionDetail",Be.withOptions({history:"push"})),[u,F]=ne.useTransition(),[k,c]=ge.useRefetchableFragment(he,l);return n.jsxs(n.Fragment,{children:[n.jsxs(h,{direction:"column",align:"stretch",style:{paddingInline:t.paddingXL,height:"100%"},children:[n.jsx(ae,{title:i("session.RecentlyCreatedSessions"),tooltip:i("session.RecentlyCreatedSessionsTooltip",{count:5}),extra:n.jsx(se,{size:"small",loading:u||e,value:"",onChange:()=>{F(()=>{c({},{fetchPolicy:"network-only"})})},type:"text",style:{backgroundColor:"transparent"}})}),n.jsx(h,{direction:"column",align:"stretch",style:{flex:1,overflowY:"auto",overflowX:"hidden",marginBottom:t.margin},children:n.jsx(Ve,{sessionsFrgmt:Qe((o=k.compute_session_nodes)==null?void 0:o.edges.map(m=>m==null?void 0:m.node)),onClickSessionName:m=>{s(Pe(m.id))},pagination:!1,disableSorter:!0,style:{overflowY:"hidden"}})})]}),n.jsx(Ue,{children:n.jsx(Xe,{open:!!d,sessionId:d||void 0,project:a,onClose:()=>{s(null)}})})]})},Le=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"scopeId"}],e={kind:"Literal",name:"first",value:0},a={kind:"Variable",name:"scope_id",variableName:"scopeId"},i=[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"SessionCountDashboardItemRefetchQuery",selections:[{args:[{kind:"Variable",name:"scopeId",variableName:"scopeId"}],kind:"FragmentSpread",name:"SessionCountDashboardItemFragment"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"SessionCountDashboardItemRefetchQuery",selections:[{alias:"myInteractive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},e,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:i,storageKey:null},{alias:"myBatch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},e,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:i,storageKey:null},{alias:"myInference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},e,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:i,storageKey:null},{alias:"myUpload",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},e,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:i,storageKey:null}]},params:{cacheID:"4e2a7d64eccfa5e512354e770190e051",id:null,metadata:{},name:"SessionCountDashboardItemRefetchQuery",operationKind:"query",text:`query SessionCountDashboardItemRefetchQuery(
  $scopeId: ScopeField
) {
  ...SessionCountDashboardItemFragment_3vJUag
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
`}}})();Le.hash="19e666cf346850c01eda18c6889928ae";const ve=(function(){var l={kind:"Literal",name:"first",value:0},e={kind:"Variable",name:"scope_id",variableName:"scopeId"},a=[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}];return{argumentDefinitions:[{defaultValue:null,kind:"LocalArgument",name:"scopeId"}],kind:"Fragment",metadata:{refetch:{connection:null,fragmentPathInResult:[],operation:Le}},name:"SessionCountDashboardItemFragment",selections:[{alias:"myInteractive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},l,e],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:a,storageKey:null},{alias:"myBatch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},l,e],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:a,storageKey:null},{alias:"myInference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},l,e],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:a,storageKey:null},{alias:"myUpload",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},l,e],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:a,storageKey:null}],type:"Query",abstractKey:null}})();ve.hash="19e666cf346850c01eda18c6889928ae";const en=({queryRef:l,isRefetching:e,title:a,...i})=>{const{t}=Z(),{token:d}=ee.useToken(),[s,u]=ne.useTransition(),[F,k]=ge.useRefetchableFragment(ve,l),{myInteractive:c,myBatch:o,myInference:m,myUpload:_}=F||{},L=(Q,r)=>n.jsx($e,{title:Q,current:r,progressMode:"hidden"});return n.jsxs(h,{direction:"column",align:"stretch",style:{paddingInline:d.paddingXL,...i.style},...me(i,["style"]),children:[n.jsx(ae,{title:a,extra:n.jsx(se,{size:"small",loading:s||e,value:"",onChange:()=>{u(()=>{k({},{fetchPolicy:"network-only"})})},type:"text",style:{backgroundColor:"transparent"}})}),n.jsx(h,{direction:"row",wrap:"wrap",gap:"lg",children:n.jsxs(qe,{style:{paddingBlock:d.padding},children:[L(t("session.Interactive"),(c==null?void 0:c.count)||0),L(t("session.Batch"),(o==null?void 0:o.count)||0),L(t("session.Inference"),(m==null?void 0:m.count)||0),L(t("session.System"),(_==null?void 0:_.count)||0)]})})]})};export{He as A,Ze as R,en as S,We as a};
//# sourceMappingURL=SessionCountDashboardItem-CMJi9n8I.js.map
