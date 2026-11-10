import{u as ie,A as oe,n,C,c as Me,r as he,aQ as je,x as Ve,aE as Pe,B as be,w as Qe,bs as $e,aK as Ue,af as qe,q as ze,N as Ge}from"./index-CwWAznqi.js";import{A as Je}from"./AgentList-ChBuDc4o.js";import{r as re}from"./icons-BgdBQS0N.js";import{B as de}from"./TotalResourceWithinResourceGroup-5-yOE9sR.js";import{B as ue}from"./BAIFetchKeyButton-DApd5OLT.js";import{u as Oe}from"./useControllableValue-BmgV_ECW.js";import{c as v,p as se,R as We,B as Ye}from"./ResourceStatistics-BxTBAXqE.js";import{f as Xe,e as He,m as Ze,q as _e}from"./lodash-RhKGq0BF.js";import{B as en}from"./useSessionNodeLiveStat-D4fXH5-b.js";import{S as nn}from"./SessionDetailDrawer-Cl3e1zK4.js";import{S as an}from"./SessionNodes-DSYGA-eW.js";import{B as tn}from"./BAIRowWrapWithDividers-CE_A-ika.js";const kn=({fetchKey:l,onChangeFetchKey:e})=>{const{t:a}=ie(),{token:i}=oe(),[s,r]=re.useTransition();return n.jsxs(C,{direction:"column",align:"stretch",style:{paddingInline:i("--spacing-8"),height:"100%"},children:[n.jsx(de,{title:a("activeAgent.ActiveAgents"),tooltip:a("activeAgent.ActiveAgentsTooltip",{count:5}),extra:n.jsx(ue,{size:"small",loading:s,value:"",onChange:t=>{r(()=>{e==null||e(t)})},type:"text",style:{backgroundColor:"transparent"}})}),n.jsx(C,{direction:"column",align:"stretch",style:{flex:1,overflowY:"auto",overflowX:"hidden",marginBottom:i("--spacing-4")},children:n.jsx(Je,{fetchKey:l,onChangeFetchKey:e,headerProps:{style:{display:"none"}},tableProps:{pagination:{pageSize:3,showSizeChanger:!1}}})})]})},Ne=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"aliveAgentFilter"},{defaultValue:null,kind:"LocalArgument",name:"schedulableAgentFilter"}],e={kind:"Literal",name:"first",value:1},a=[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"AgentStatsRefetchQuery",selections:[{args:[{kind:"Variable",name:"aliveAgentFilter",variableName:"aliveAgentFilter"},{kind:"Variable",name:"schedulableAgentFilter",variableName:"schedulableAgentFilter"}],kind:"FragmentSpread",name:"AgentStatsFragment"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"AgentStatsRefetchQuery",selections:[{alias:null,args:null,concreteType:"AgentStats",kind:"LinkedField",name:"agentStats",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentResource",kind:"LinkedField",name:"totalResource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"free",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capacity",storageKey:null}],storageKey:null}],storageKey:null},{alias:"aliveAgents",args:[{kind:"Variable",name:"filter",variableName:"aliveAgentFilter"},e],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:a,storageKey:null},{alias:"schedulableAgents",args:[{kind:"Variable",name:"filter",variableName:"schedulableAgentFilter"},e],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:a,storageKey:null}]},params:{cacheID:"94723c46599cac0fa017d69548d9db15",id:null,metadata:{},name:"AgentStatsRefetchQuery",operationKind:"query",text:`query AgentStatsRefetchQuery(
  $aliveAgentFilter: String!
  $schedulableAgentFilter: String!
) {
  ...AgentStatsFragment_rQkRq
}

fragment AgentStatsFragment_rQkRq on Query {
  agentStats {
    totalResource {
      free
      used
      capacity
    }
  }
  aliveAgents: agent_nodes(filter: $aliveAgentFilter, first: 1) {
    count
  }
  schedulableAgents: agent_nodes(filter: $schedulableAgentFilter, first: 1) {
    count
  }
}
`}}})();Ne.hash="184fa590bf7419b2316880010ceb48ed";const Te=(function(){var l={kind:"Literal",name:"first",value:1},e=[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}];return{argumentDefinitions:[{defaultValue:null,kind:"LocalArgument",name:"aliveAgentFilter"},{defaultValue:null,kind:"LocalArgument",name:"schedulableAgentFilter"}],kind:"Fragment",metadata:{refetch:{connection:null,fragmentPathInResult:[],operation:Ne}},name:"AgentStatsFragment",selections:[{alias:null,args:null,concreteType:"AgentStats",kind:"LinkedField",name:"agentStats",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentResource",kind:"LinkedField",name:"totalResource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"free",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capacity",storageKey:null}],storageKey:null}],storageKey:null},{alias:"aliveAgents",args:[{kind:"Variable",name:"filter",variableName:"aliveAgentFilter"},l],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:e,storageKey:null},{alias:"schedulableAgents",args:[{kind:"Variable",name:"filter",variableName:"schedulableAgentFilter"},l],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:e,storageKey:null}],type:"Query",abstractKey:null}})();Te.hash="184fa590bf7419b2316880010ceb48ed";const Fn=l=>{"use memo";var Ce,Ae,ve,Le,Ie;const e=Me.c(102);let a,i,s,r;e[0]!==l?({queryRef:r,isRefetching:i,extra:a,...s}=l,e[0]=l,e[1]=a,e[2]=i,e[3]=s,e[4]=r):(a=e[1],i=e[2],s=e[3],r=e[4]);const{t}=ie(),{token:u}=oe(),[S,A]=re.useTransition();let f;e[5]===Symbol.for("react.memo_cache_sentinel")?(f={defaultValue:"used",trigger:"onDisplayTypeChange",defaultValuePropName:"defaultDisplayType"},e[5]=f):f=e[5];const[m,k]=Oe(s,f);let g;e[6]===Symbol.for("react.memo_cache_sentinel")?(g=Te,e[6]=g):g=e[6];const[o,F]=he.useRefetchableFragment(g,r),d=je();let ce;e:{const O=(Ce=o.agentStats)==null?void 0:Ce.totalResource;if(!O){let h;e[7]===Symbol.for("react.memo_cache_sentinel")?(h={cpu:null,memory:null,accelerators:[]},e[7]=h):h=e[7],ce=h;break e}const p=O.free,y=O.used,c=O.capacity,W=(Ae=d==null?void 0:d.resourceSlotsInRG)==null?void 0:Ae.cpu,_=(ve=d==null?void 0:d.resourceSlotsInRG)==null?void 0:ve.mem;let ee;e[8]!==c||e[9]!==W||e[10]!==p||e[11]!==y?(ee=W?{used:{current:v(y.cpu||0),total:v(c.cpu||0)},free:{current:v(p.cpu||0),total:v(c.cpu||0)},metadata:{title:W.human_readable_name,displayUnit:W.display_unit}}:null,e[8]=c,e[9]=W,e[10]=p,e[11]=y,e[12]=ee):ee=e[12];const fe=ee;let ne;e[13]!==c||e[14]!==p||e[15]!==_||e[16]!==y?(ne=_?{used:{current:se(y.mem||0,_.display_unit),total:se(c.mem||0,_.display_unit)},free:{current:se(p.mem||0,_.display_unit),total:se(c.mem||0,_.display_unit)},metadata:{title:_.human_readable_name,displayUnit:_.display_unit}}:null,e[13]=c,e[14]=p,e[15]=_,e[16]=y,e[17]=ne):ne=e[17];const Se=ne;let ae;if(e[18]!==c||e[19]!==p||e[20]!==d.resourceSlotsInRG||e[21]!==y){let h;e[23]!==c||e[24]!==p||e[25]!==y?(h=(Fe,le)=>{if(!Fe)return null;const Be=p[le]||0,we=y[le]||0,Ke=c[le]||0;return{key:le,used:{current:v(we),total:v(Ke)},free:{current:v(Be),total:v(Ke)},metadata:{title:Fe.human_readable_name,displayUnit:Fe.display_unit}}},e[23]=c,e[24]=p,e[25]=y,e[26]=h):h=e[26],ae=Xe(He(Ze(_e(d==null?void 0:d.resourceSlotsInRG,["cpu","mem"]),h)),ln),e[18]=c,e[19]=p,e[20]=d.resourceSlotsInRG,e[21]=y,e[22]=ae}else ae=e[22];const ke=ae;let te;e[27]!==ke||e[28]!==fe||e[29]!==Se?(te={cpu:fe,memory:Se,accelerators:ke},e[27]=ke,e[28]=fe,e[29]=Se,e[30]=te):te=e[30],ce=te}const me=ce;let L;e[31]!==u?(L=u("--spacing-8"),e[31]=u,e[32]=L):L=e[32];let I;e[33]!==u?(I=u("--spacing-4"),e[33]=u,e[34]=I):I=e[34];let K;e[35]!==s.style||e[36]!==L||e[37]!==I?(K={paddingInline:L,paddingBottom:I,...s.style},e[35]=s.style,e[36]=L,e[37]=I,e[38]=K):K=e[38];let b;e[39]!==s?(b=_e(s,["style"]),e[39]=s,e[40]=b):b=e[40];let N;e[41]!==t?(N=t("agentStats.AgentStats"),e[41]=t,e[42]=N):N=e[42];let T;e[43]!==N?(T=n.jsx(Pe,{level:5,children:N}),e[43]=N,e[44]=T):T=e[44];let R;e[45]!==t?(R=t("agentStats.SchedulableAgents"),e[45]=t,e[46]=R):R=e[46];let D;e[47]!==R?(D={label:R},e[47]=R,e[48]=D):D=e[48];const ge=`${((Le=o.schedulableAgents)==null?void 0:Le.count)??0} / ${((Ie=o.aliveAgents)==null?void 0:Ie.count)??0}`;let E;e[49]!==ge?(E={label:ge},e[49]=ge,e[50]=E):E=e[50];let x;e[51]!==D||e[52]!==E?(x=n.jsx(en,{values:[D,E]}),e[51]=D,e[52]=E,e[53]=x):x=e[53];let B;e[54]!==x||e[55]!==T?(B=n.jsxs(C,{gap:"xs",align:"center",wrap:"wrap",children:[T,x]}),e[54]=x,e[55]=T,e[56]=B):B=e[56];let w;e[57]!==t?(w=t("agentStats.AgentStatsDescription"),e[57]=t,e[58]=w):w=e[58];let Y;e[59]!==t?(Y=t("dashboard.Used"),e[59]=t,e[60]=Y):Y=e[60];let X;e[61]!==t?(X=t("dashboard.Free"),e[61]=t,e[62]=X):X=e[62];const pe=`${Y}/${X}`;let M;e[63]!==k?(M=O=>k(O),e[63]=k,e[64]=M):M=e[64];let j;e[65]!==t?(j=t("dashboard.Used"),e[65]=t,e[66]=j):j=e[66];let V;e[67]!==j?(V=n.jsx(be,{value:"used",label:j}),e[67]=j,e[68]=V):V=e[68];let P;e[69]!==t?(P=t("dashboard.Free"),e[69]=t,e[70]=P):P=e[70];let Q;e[71]!==P?(Q=n.jsx(be,{value:"free",label:P}),e[71]=P,e[72]=Q):Q=e[72];let $;e[73]!==m||e[74]!==pe||e[75]!==M||e[76]!==V||e[77]!==Q?($=n.jsxs(Qe,{size:"sm","aria-label":pe,value:m,onChange:M,children:[V,Q]}),e[73]=m,e[74]=pe,e[75]=M,e[76]=V,e[77]=Q,e[78]=$):$=e[78];const ye=S||i;let U;e[79]!==F?(U=()=>{A(()=>{F({},{fetchPolicy:"network-only"})})},e[79]=F,e[80]=U):U=e[80];let H;e[81]===Symbol.for("react.memo_cache_sentinel")?(H={backgroundColor:"transparent"},e[81]=H):H=e[81];let q;e[82]!==ye||e[83]!==U?(q=n.jsx(ue,{size:"small",loading:ye,value:"",onChange:U,type:"text",style:H}),e[82]=ye,e[83]=U,e[84]=q):q=e[84];let z;e[85]!==a||e[86]!==$||e[87]!==q?(z=n.jsxs(C,{gap:"xs",wrap:"wrap",children:[$,q,a]}),e[85]=a,e[86]=$,e[87]=q,e[88]=z):z=e[88];let G;e[89]!==B||e[90]!==w||e[91]!==z?(G=n.jsx(de,{title:B,tooltip:w,extra:z}),e[89]=B,e[90]=w,e[91]=z,e[92]=G):G=e[92];let J;e[93]!==me||e[94]!==m||e[95]!==d.isLoading?(J=d.isLoading?n.jsx(Ve,{}):n.jsx(We,{resourceData:me,displayType:m==="used"?"used":"free",progressMode:"normal"}),e[93]=me,e[94]=m,e[95]=d.isLoading,e[96]=J):J=e[96];let Z;return e[97]!==G||e[98]!==J||e[99]!==K||e[100]!==b?(Z=n.jsxs(C,{direction:"column",align:"stretch",style:K,...b,children:[G,J]}),e[97]=G,e[98]=J,e[99]=K,e[100]=b,e[101]=Z):Z=e[101],Z};function ln(l){return!!(l.used.current||l.used.total)}const Re=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"scopeId"}],e={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},t=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],u={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},A=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[e,a,i,s],storageKey:null}],storageKey:null},S];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"RecentlyCreatedSessionRefetchQuery",selections:[{args:[{kind:"Variable",name:"scopeId",variableName:"scopeId"}],kind:"FragmentSpread",name:"RecentlyCreatedSessionFragment"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"RecentlyCreatedSessionRefetchQuery",selections:[{alias:null,args:[{kind:"Literal",name:"filter",value:'status == "running"'},{kind:"Literal",name:"first",value:5},{kind:"Literal",name:"order",value:"-created_at"},{kind:"Variable",name:"scope_id",variableName:"scopeId"}],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[e,a,i,s,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},r,{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[e,s,{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:t,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:t,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},u,e],storageKey:null},a,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},r,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},u,{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},e],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[a,i,e],storageKey:null}],storageKey:null},S],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:A,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:A,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domain_name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"cfc7d08bb632adf287537245c04f28c3",id:null,metadata:{},name:"RecentlyCreatedSessionRefetchQuery",operationKind:"query",text:`query RecentlyCreatedSessionRefetchQuery(
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
`}}})();Re.hash="aeaa38c05c8fe2c9a07946ed4a3fe214";const De={argumentDefinitions:[{defaultValue:null,kind:"LocalArgument",name:"scopeId"}],kind:"Fragment",metadata:{refetch:{connection:null,fragmentPathInResult:[],operation:Re}},name:"RecentlyCreatedSessionFragment",selections:[{alias:null,args:[{kind:"Literal",name:"filter",value:'status == "running"'},{kind:"Literal",name:"first",value:5},{kind:"Literal",name:"order",value:"-created_at"},{kind:"Variable",name:"scope_id",variableName:"scopeId"}],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null};De.hash="aeaa38c05c8fe2c9a07946ed4a3fe214";const _n=({queryRef:l,isRefetching:e,project:a})=>{var g;const{t:i}=ie(),{token:s}=oe(),r=$e(),t=Ue(),u=new URLSearchParams(r.search).get("sessionDetail"),S=o=>{const F=new URLSearchParams(r.search);o===null?F.delete("sessionDetail"):F.set("sessionDetail",o),t({search:F.toString(),hash:r.hash})},[A,f]=re.useTransition(),[m,k]=he.useRefetchableFragment(De,l);return n.jsxs(n.Fragment,{children:[n.jsxs(C,{direction:"column",align:"stretch",style:{paddingInline:s("--spacing-8"),height:"100%"},children:[n.jsx(de,{title:i("session.RecentlyCreatedSessions"),tooltip:i("session.RecentlyCreatedSessionsTooltip",{count:5}),extra:n.jsx(ue,{size:"small",loading:A||e,value:"",onChange:()=>{f(()=>{k({},{fetchPolicy:"network-only"})})},type:"text",style:{backgroundColor:"transparent"}})}),n.jsx(C,{direction:"column",align:"stretch",style:{flex:1,overflowY:"auto",overflowX:"hidden",marginBottom:s("--spacing-4")},children:n.jsx(an,{sessionsFrgmt:ze((g=m.compute_session_nodes)==null?void 0:g.edges.map(o=>o==null?void 0:o.node)),onClickSessionName:o=>{S(qe(o.id))},pagination:!1,disableSorter:!0,style:{overflowY:"hidden"}})})]}),n.jsx(Ge,{children:n.jsx(nn,{open:!!u,sessionId:u||void 0,project:a,onClose:()=>{S(null)}})})]})},Ee=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"scopeId"}],e={kind:"Literal",name:"first",value:0},a={kind:"Variable",name:"scope_id",variableName:"scopeId"},i=[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"SessionCountDashboardItemRefetchQuery",selections:[{args:[{kind:"Variable",name:"scopeId",variableName:"scopeId"}],kind:"FragmentSpread",name:"SessionCountDashboardItemFragment"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"SessionCountDashboardItemRefetchQuery",selections:[{alias:"myInteractive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},e,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:i,storageKey:null},{alias:"myBatch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},e,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:i,storageKey:null},{alias:"myInference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},e,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:i,storageKey:null},{alias:"myUpload",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},e,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:i,storageKey:null}]},params:{cacheID:"4e2a7d64eccfa5e512354e770190e051",id:null,metadata:{},name:"SessionCountDashboardItemRefetchQuery",operationKind:"query",text:`query SessionCountDashboardItemRefetchQuery(
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
`}}})();Ee.hash="19e666cf346850c01eda18c6889928ae";const xe=(function(){var l={kind:"Literal",name:"first",value:0},e={kind:"Variable",name:"scope_id",variableName:"scopeId"},a=[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}];return{argumentDefinitions:[{defaultValue:null,kind:"LocalArgument",name:"scopeId"}],kind:"Fragment",metadata:{refetch:{connection:null,fragmentPathInResult:[],operation:Ee}},name:"SessionCountDashboardItemFragment",selections:[{alias:"myInteractive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},l,e],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:a,storageKey:null},{alias:"myBatch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},l,e],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:a,storageKey:null},{alias:"myInference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},l,e],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:a,storageKey:null},{alias:"myUpload",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},l,e],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:a,storageKey:null}],type:"Query",abstractKey:null}})();xe.hash="19e666cf346850c01eda18c6889928ae";const hn=({queryRef:l,isRefetching:e,title:a,...i})=>{const{t:s}=ie(),{token:r}=oe(),[t,u]=re.useTransition(),[S,A]=he.useRefetchableFragment(xe,l),{myInteractive:f,myBatch:m,myInference:k,myUpload:g}=S||{},o=(F,d)=>n.jsx(Ye,{title:F,current:d,progressMode:"hidden"});return n.jsxs(C,{direction:"column",align:"stretch",style:{paddingInline:r("--spacing-8"),...i.style},..._e(i,["style"]),children:[n.jsx(de,{title:a,extra:n.jsx(ue,{size:"small",loading:t||e,value:"",onChange:()=>{u(()=>{A({},{fetchPolicy:"network-only"})})},type:"text",style:{backgroundColor:"transparent"}})}),n.jsx(C,{direction:"row",wrap:"wrap",gap:"lg",children:n.jsxs(tn,{style:{paddingBlock:r("--spacing-4")},children:[o(s("session.Interactive"),(f==null?void 0:f.count)||0),o(s("session.Batch"),(m==null?void 0:m.count)||0),o(s("session.Inference"),(k==null?void 0:k.count)||0),o(s("session.System"),(g==null?void 0:g.count)||0)]})})]})};export{Fn as A,_n as R,hn as S,kn as a};
//# sourceMappingURL=SessionCountDashboardItem-DVMHnqm2.js.map
