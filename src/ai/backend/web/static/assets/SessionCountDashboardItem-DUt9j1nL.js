import{u as le,ab as se,l as ie,j as n,c as k,aC as oe,aO as re,i as Me,bk as we,r as Fe,bl as Be,bm as v,bn as te,aj as je,bo as Ve,ak as Pe,aq as ke,aV as Qe,bp as $e,bq as qe,br as Ue,bs as Ie,bt as ze,bu as Xe,ao as Oe,aY as Ge,N as Je,aT as Ye,an as We,aU as He,aW as Ze}from"./index-BQcmV02I.js";import{A as en}from"./AgentList-0jL18p0m.js";import{S as nn}from"./SessionDetailDrawer-DV2bXyCG.js";const on=({fetchKey:l,onChangeFetchKey:e})=>{const{t:a}=le(),{token:i}=se.useToken(),[s,d]=ie.useTransition();return n.jsxs(k,{direction:"column",align:"stretch",style:{paddingInline:i.paddingXL,height:"100%"},children:[n.jsx(oe,{title:a("activeAgent.ActiveAgents"),tooltip:a("activeAgent.ActiveAgentsTooltip",{count:5}),extra:n.jsx(re,{size:"small",loading:s,value:"",onChange:t=>{d(()=>{e==null||e(t)})},type:"text",style:{backgroundColor:"transparent"}})}),n.jsx(k,{direction:"column",align:"stretch",style:{flex:1,overflowY:"auto",overflowX:"hidden",marginBottom:i.margin},children:n.jsx(en,{fetchKey:l,onChangeFetchKey:e,headerProps:{style:{display:"none"}},tableProps:{pagination:{pageSize:3,showSizeChanger:!1}}})})]})},be=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"aliveAgentFilter"},{defaultValue:null,kind:"LocalArgument",name:"schedulableAgentFilter"}],e={kind:"Literal",name:"first",value:1},a=[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"AgentStatsRefetchQuery",selections:[{args:[{kind:"Variable",name:"aliveAgentFilter",variableName:"aliveAgentFilter"},{kind:"Variable",name:"schedulableAgentFilter",variableName:"schedulableAgentFilter"}],kind:"FragmentSpread",name:"AgentStatsFragment"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"AgentStatsRefetchQuery",selections:[{alias:null,args:null,concreteType:"AgentStats",kind:"LinkedField",name:"agentStats",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentResource",kind:"LinkedField",name:"totalResource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"free",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capacity",storageKey:null}],storageKey:null}],storageKey:null},{alias:"aliveAgents",args:[{kind:"Variable",name:"filter",variableName:"aliveAgentFilter"},e],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:a,storageKey:null},{alias:"schedulableAgents",args:[{kind:"Variable",name:"filter",variableName:"schedulableAgentFilter"},e],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:a,storageKey:null}]},params:{cacheID:"f803731d888a4feaf958c31b7ff49d83",id:null,metadata:{},name:"AgentStatsRefetchQuery",operationKind:"query",text:`query AgentStatsRefetchQuery(
  $aliveAgentFilter: String!
  $schedulableAgentFilter: String!
) {
  ...AgentStatsFragment_rQkRq
}

fragment AgentStatsFragment_rQkRq on Query {
  agentStats @since(version: "25.15.0") {
    totalResource {
      free
      used
      capacity
    }
  }
  aliveAgents: agent_nodes(filter: $aliveAgentFilter, first: 1) @since(version: "24.12.0") {
    count
  }
  schedulableAgents: agent_nodes(filter: $schedulableAgentFilter, first: 1) @since(version: "24.12.0") {
    count
  }
}
`}}})();be.hash="5a26ac154e8e8dd31245ff662479f976";const Ke=(function(){var l={kind:"Literal",name:"first",value:1},e=[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}];return{argumentDefinitions:[{defaultValue:null,kind:"LocalArgument",name:"aliveAgentFilter"},{defaultValue:null,kind:"LocalArgument",name:"schedulableAgentFilter"}],kind:"Fragment",metadata:{refetch:{connection:null,fragmentPathInResult:[],operation:be}},name:"AgentStatsFragment",selections:[{alias:null,args:null,concreteType:"AgentStats",kind:"LinkedField",name:"agentStats",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentResource",kind:"LinkedField",name:"totalResource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"free",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capacity",storageKey:null}],storageKey:null}],storageKey:null},{alias:"aliveAgents",args:[{kind:"Variable",name:"filter",variableName:"aliveAgentFilter"},l],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:e,storageKey:null},{alias:"schedulableAgents",args:[{kind:"Variable",name:"filter",variableName:"schedulableAgentFilter"},l],concreteType:"AgentConnection",kind:"LinkedField",name:"agent_nodes",plural:!1,selections:e,storageKey:null}],type:"Query",abstractKey:null}})();Ke.hash="5a26ac154e8e8dd31245ff662479f976";const rn=l=>{"use memo";var _e,Ce,he,ve,Ae;const e=Me.c(98);let a,i,s,d;e[0]!==l?({queryRef:d,isRefetching:i,extra:a,...s}=l,e[0]=l,e[1]=a,e[2]=i,e[3]=s,e[4]=d):(a=e[1],i=e[2],s=e[3],d=e[4]);const{t}=le(),{token:u}=se.useToken(),[F,_]=ie.useTransition();let c;e[5]===Symbol.for("react.memo_cache_sentinel")?(c={defaultValue:"used",trigger:"onDisplayTypeChange",defaultValuePropName:"defaultDisplayType"},e[5]=c):c=e[5];const[o,m]=we(s,c);let C;e[6]===Symbol.for("react.memo_cache_sentinel")?(C=Ke,e[6]=C):C=e[6];const[h,X]=Fe.useRefetchableFragment(C,d),r=Be();let de;e:{const z=(_e=h.agentStats)==null?void 0:_e.totalResource;if(!z){let S;e[7]===Symbol.for("react.memo_cache_sentinel")?(S={cpu:null,memory:null,accelerators:[]},e[7]=S):S=e[7],de=S;break e}const p=z.free,y=z.used,g=z.capacity,O=(Ce=r==null?void 0:r.resourceSlotsInRG)==null?void 0:Ce.cpu,f=(he=r==null?void 0:r.resourceSlotsInRG)==null?void 0:he.mem;let H;e[8]!==g||e[9]!==O||e[10]!==p||e[11]!==y?(H=O?{used:{current:v(y.cpu||0),total:v(g.cpu||0)},free:{current:v(p.cpu||0),total:v(g.cpu||0)},metadata:{title:O.human_readable_name,displayUnit:O.display_unit}}:null,e[8]=g,e[9]=O,e[10]=p,e[11]=y,e[12]=H):H=e[12];const pe=H;let Z;e[13]!==g||e[14]!==p||e[15]!==f||e[16]!==y?(Z=f?{used:{current:te(y.mem||0,f.display_unit),total:te(g.mem||0,f.display_unit)},free:{current:te(p.mem||0,f.display_unit),total:te(g.mem||0,f.display_unit)},metadata:{title:f.human_readable_name,displayUnit:f.display_unit}}:null,e[13]=g,e[14]=p,e[15]=f,e[16]=y,e[17]=Z):Z=e[17];const ye=Z;let ee;if(e[18]!==g||e[19]!==p||e[20]!==r.resourceSlotsInRG||e[21]!==y){let S;e[23]!==g||e[24]!==p||e[25]!==y?(S=(Se,ae)=>{if(!Se)return null;const Ee=p[ae]||0,xe=y[ae]||0,Le=g[ae]||0;return{key:ae,used:{current:v(xe),total:v(Le)},free:{current:v(Ee),total:v(Le)},metadata:{title:Se.human_readable_name,displayUnit:Se.display_unit}}},e[23]=g,e[24]=p,e[25]=y,e[26]=S):S=e[26],ee=je(Ve(Pe(ke(r==null?void 0:r.resourceSlotsInRG,["cpu","mem"]),S)),an),e[18]=g,e[19]=p,e[20]=r.resourceSlotsInRG,e[21]=y,e[22]=ee}else ee=e[22];const fe=ee;let ne;e[27]!==fe||e[28]!==pe||e[29]!==ye?(ne={cpu:pe,memory:ye,accelerators:fe},e[27]=fe,e[28]=pe,e[29]=ye,e[30]=ne):ne=e[30],de=ne}const ue=de;let A;e[31]!==s.style||e[32]!==u.padding||e[33]!==u.paddingXL?(A={paddingInline:u.paddingXL,paddingBottom:u.padding,...s.style},e[31]=s.style,e[32]=u.padding,e[33]=u.paddingXL,e[34]=A):A=e[34];let L;e[35]!==s?(L=ke(s,["style"]),e[35]=s,e[36]=L):L=e[36];let I;e[37]!==t?(I=t("agentStats.AgentStats"),e[37]=t,e[38]=I):I=e[38];let b;e[39]!==I?(b=n.jsx(qe,{level:5,children:I}),e[39]=I,e[40]=b):b=e[40];let K;e[41]!==t?(K=t("agentStats.SchedulableAgents"),e[41]=t,e[42]=K):K=e[42];let N;e[43]!==K?(N={label:K},e[43]=K,e[44]=N):N=e[44];const ce=`${((ve=h.schedulableAgents)==null?void 0:ve.count)??0} / ${((Ae=h.aliveAgents)==null?void 0:Ae.count)??0}`;let T;e[45]!==ce?(T={label:ce},e[45]=ce,e[46]=T):T=e[46];let R;e[47]!==T||e[48]!==N?(R=n.jsx(Ue,{values:[N,T]}),e[47]=T,e[48]=N,e[49]=R):R=e[49];let D;e[50]!==R||e[51]!==b?(D=n.jsxs(k,{gap:"xs",align:"center",wrap:"wrap",children:[b,R]}),e[50]=R,e[51]=b,e[52]=D):D=e[52];let E;e[53]!==t?(E=t("agentStats.AgentStatsDescription"),e[53]=t,e[54]=E):E=e[54];let G;e[55]!==t?(G=t("dashboard.Used"),e[55]=t,e[56]=G):G=e[56];let J;e[57]!==t?(J=t("dashboard.Free"),e[57]=t,e[58]=J):J=e[58];const me=`${G}/${J}`;let x;e[59]!==m?(x=z=>m(z),e[59]=m,e[60]=x):x=e[60];let M;e[61]!==t?(M=t("dashboard.Used"),e[61]=t,e[62]=M):M=e[62];let w;e[63]!==M?(w=n.jsx(Ie,{value:"used",label:M}),e[63]=M,e[64]=w):w=e[64];let B;e[65]!==t?(B=t("dashboard.Free"),e[65]=t,e[66]=B):B=e[66];let j;e[67]!==B?(j=n.jsx(Ie,{value:"free",label:B}),e[67]=B,e[68]=j):j=e[68];let V;e[69]!==o||e[70]!==me||e[71]!==x||e[72]!==w||e[73]!==j?(V=n.jsxs(ze,{size:"sm",label:me,value:o,onChange:x,children:[w,j]}),e[69]=o,e[70]=me,e[71]=x,e[72]=w,e[73]=j,e[74]=V):V=e[74];const ge=F||i;let P;e[75]!==X?(P=()=>{_(()=>{X({},{fetchPolicy:"network-only"})})},e[75]=X,e[76]=P):P=e[76];let Y;e[77]===Symbol.for("react.memo_cache_sentinel")?(Y={backgroundColor:"transparent"},e[77]=Y):Y=e[77];let Q;e[78]!==ge||e[79]!==P?(Q=n.jsx(re,{size:"small",loading:ge,value:"",onChange:P,type:"text",style:Y}),e[78]=ge,e[79]=P,e[80]=Q):Q=e[80];let $;e[81]!==a||e[82]!==V||e[83]!==Q?($=n.jsxs(k,{gap:"xs",wrap:"wrap",children:[V,Q,a]}),e[81]=a,e[82]=V,e[83]=Q,e[84]=$):$=e[84];let q;e[85]!==D||e[86]!==E||e[87]!==$?(q=n.jsx(oe,{title:D,tooltip:E,extra:$}),e[85]=D,e[86]=E,e[87]=$,e[88]=q):q=e[88];let U;e[89]!==ue||e[90]!==o||e[91]!==r.isLoading?(U=r.isLoading?n.jsx(Qe,{}):n.jsx($e,{resourceData:ue,displayType:o==="used"?"used":"free",progressMode:"normal"}),e[89]=ue,e[90]=o,e[91]=r.isLoading,e[92]=U):U=e[92];let W;return e[93]!==q||e[94]!==U||e[95]!==A||e[96]!==L?(W=n.jsxs(k,{direction:"column",align:"stretch",style:A,...L,children:[q,U]}),e[93]=q,e[94]=U,e[95]=A,e[96]=L,e[97]=W):W=e[97],W};function an(l){return!!(l.used.current||l.used.total)}const Ne=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"scopeId"}],e={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},u=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],F={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},_={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[e,a,i,s],storageKey:null}],storageKey:null},c];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"RecentlyCreatedSessionRefetchQuery",selections:[{args:[{kind:"Variable",name:"scopeId",variableName:"scopeId"}],kind:"FragmentSpread",name:"RecentlyCreatedSessionFragment"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"RecentlyCreatedSessionRefetchQuery",selections:[{alias:null,args:[{kind:"Literal",name:"filter",value:'status == "running"'},{kind:"Literal",name:"first",value:5},{kind:"Literal",name:"order",value:"-created_at"},{kind:"Variable",name:"scope_id",variableName:"scopeId"}],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[e,a,i,s,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},d,t,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[e,s,{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:u,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:u,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},F,e],storageKey:null},a,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},t,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},F,_,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},e],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[a,i,e],storageKey:null}],storageKey:null},c],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},_,{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:o,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:o,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},d,{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domain_name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"0e94cc79111f1e48d91679e02b7b46b1",id:null,metadata:{},name:"RecentlyCreatedSessionRefetchQuery",operationKind:"query",text:`query RecentlyCreatedSessionRefetchQuery(
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
  ...SessionStatusBadgeFragment
  ...SessionActionButtonsFragment
  ...BAISessionTypeTokenFragment
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

fragment SessionStatusBadgeFragment on ComputeSessionNode {
  id
  status
  status_info
  status_data
  queue_position @since(version: "25.13.0")
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

fragment SessionStatusDetailModalFragment on ComputeSessionNode {
  id
  name
  status
  status_info
  status_data
  starts_at
  ...SessionStatusBadgeFragment
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
`}}})();Ne.hash="aeaa38c05c8fe2c9a07946ed4a3fe214";const Te={argumentDefinitions:[{defaultValue:null,kind:"LocalArgument",name:"scopeId"}],kind:"Fragment",metadata:{refetch:{connection:null,fragmentPathInResult:[],operation:Ne}},name:"RecentlyCreatedSessionFragment",selections:[{alias:null,args:[{kind:"Literal",name:"filter",value:'status == "running"'},{kind:"Literal",name:"first",value:5},{kind:"Literal",name:"order",value:"-created_at"},{kind:"Variable",name:"scope_id",variableName:"scopeId"}],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null};Te.hash="aeaa38c05c8fe2c9a07946ed4a3fe214";const dn=({queryRef:l,isRefetching:e,project:a})=>{var o;const{t:i}=le(),{token:s}=se.useToken(),[d,t]=Xe("sessionDetail",Oe.withOptions({history:"push"})),[u,F]=ie.useTransition(),[_,c]=Fe.useRefetchableFragment(Te,l);return n.jsxs(n.Fragment,{children:[n.jsxs(k,{direction:"column",align:"stretch",style:{paddingInline:s.paddingXL,height:"100%"},children:[n.jsx(oe,{title:i("session.RecentlyCreatedSessions"),tooltip:i("session.RecentlyCreatedSessionsTooltip",{count:5}),extra:n.jsx(re,{size:"small",loading:u||e,value:"",onChange:()=>{F(()=>{c({},{fetchPolicy:"network-only"})})},type:"text",style:{backgroundColor:"transparent"}})}),n.jsx(k,{direction:"column",align:"stretch",style:{flex:1,overflowY:"auto",overflowX:"hidden",marginBottom:s.margin},children:n.jsx(Ge,{sessionsFrgmt:Ye((o=_.compute_session_nodes)==null?void 0:o.edges.map(m=>m==null?void 0:m.node)),onClickSessionName:m=>{t(Je(m.id))},pagination:!1,disableSorter:!0,style:{overflowY:"hidden"}})})]}),n.jsx(We,{children:n.jsx(nn,{open:!!d,sessionId:d||void 0,project:a,onClose:()=>{t(null)}})})]})},Re=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"scopeId"}],e={kind:"Literal",name:"first",value:0},a={kind:"Variable",name:"scope_id",variableName:"scopeId"},i=[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"SessionCountDashboardItemRefetchQuery",selections:[{args:[{kind:"Variable",name:"scopeId",variableName:"scopeId"}],kind:"FragmentSpread",name:"SessionCountDashboardItemFragment"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"SessionCountDashboardItemRefetchQuery",selections:[{alias:"myInteractive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},e,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:i,storageKey:null},{alias:"myBatch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},e,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:i,storageKey:null},{alias:"myInference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},e,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:i,storageKey:null},{alias:"myUpload",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},e,a],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:i,storageKey:null}]},params:{cacheID:"4e2a7d64eccfa5e512354e770190e051",id:null,metadata:{},name:"SessionCountDashboardItemRefetchQuery",operationKind:"query",text:`query SessionCountDashboardItemRefetchQuery(
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
`}}})();Re.hash="19e666cf346850c01eda18c6889928ae";const De=(function(){var l={kind:"Literal",name:"first",value:0},e={kind:"Variable",name:"scope_id",variableName:"scopeId"},a=[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}];return{argumentDefinitions:[{defaultValue:null,kind:"LocalArgument",name:"scopeId"}],kind:"Fragment",metadata:{refetch:{connection:null,fragmentPathInResult:[],operation:Re}},name:"SessionCountDashboardItemFragment",selections:[{alias:"myInteractive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},l,e],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:a,storageKey:null},{alias:"myBatch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},l,e],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:a,storageKey:null},{alias:"myInference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},l,e],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:a,storageKey:null},{alias:"myUpload",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},l,e],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:a,storageKey:null}],type:"Query",abstractKey:null}})();De.hash="19e666cf346850c01eda18c6889928ae";const un=({queryRef:l,isRefetching:e,title:a,...i})=>{const{t:s}=le(),{token:d}=se.useToken(),[t,u]=ie.useTransition(),[F,_]=Fe.useRefetchableFragment(De,l),{myInteractive:c,myBatch:o,myInference:m,myUpload:C}=F||{},h=(X,r)=>n.jsx(Ze,{title:X,current:r,progressMode:"hidden"});return n.jsxs(k,{direction:"column",align:"stretch",style:{paddingInline:d.paddingXL,...i.style},...ke(i,["style"]),children:[n.jsx(oe,{title:a,extra:n.jsx(re,{size:"small",loading:t||e,value:"",onChange:()=>{u(()=>{_({},{fetchPolicy:"network-only"})})},type:"text",style:{backgroundColor:"transparent"}})}),n.jsx(k,{direction:"row",wrap:"wrap",gap:"lg",children:n.jsxs(He,{style:{paddingBlock:d.padding},children:[h(s("session.Interactive"),(c==null?void 0:c.count)||0),h(s("session.Batch"),(o==null?void 0:o.count)||0),h(s("session.Inference"),(m==null?void 0:m.count)||0),h(s("session.System"),(C==null?void 0:C.count)||0)]})})]})};export{rn as A,dn as R,un as S,on as a};
//# sourceMappingURL=SessionCountDashboardItem-DUt9j1nL.js.map
