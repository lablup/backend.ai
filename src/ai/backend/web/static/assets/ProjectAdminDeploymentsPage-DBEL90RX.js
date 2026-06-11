import{h as Kn,u as bn,an as Tn,j as a,bK as An,r as ke,az as Fn,A as Ln,v as Nn,p as Rn,bt as Pn,bu as Dn,c_ as Mn,bv as xn,a4 as _n,au as Vn,i as Sn,aN as Bn,a6 as wn,ax as On,c1 as En,B as ln,aD as Un,a_ as $n,c$ as qn,b0 as zn,N as vn,T as an,d0 as Qn,b8 as Gn,a7 as Hn,bJ as Jn}from"./index-DluNL-GQ.js";import{i as Wn,B as Yn,D as Xn}from"./DeploymentRevisionDetailDrawer-C-by95-U.js";import{p as Zn,B as el,a as nl}from"./BAIModelDeploymentNodes-CnI-Cj77.js";import{B as ll}from"./BAIGraphQLPropertyFilter-BEXGUJCX.js";import"./FolderLink-HST2MS7p.js";import"./BAIId-qXX3wVPc.js";import"./BooleanTag-CsnTLJdn.js";const hn=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e},params:{cacheID:"1463ddcf31aa971e7f72ca3901c5db76",id:null,metadata:{},name:"ProjectAdminDeploymentsPageDeleteMutation",operationKind:"mutation",text:`mutation ProjectAdminDeploymentsPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}}();hn.hash="42ff73332d0c41e5828ba82d49920b78";const In=function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},m={defaultValue:null,kind:"LocalArgument",name:"offset"},n={defaultValue:null,kind:"LocalArgument",name:"orderBy"},d={defaultValue:null,kind:"LocalArgument",name:"projectId"},u=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{fields:[{kind:"Variable",name:"projectId",variableName:"projectId"}],kind:"ObjectValue",name:"scope"}],o={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},j={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},Fe=[o],I={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[i,g,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},c=[g,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}];return{fragment:{argumentDefinitions:[l,e,m,n,d],kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:u,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[i,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[g,b],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[i,j,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[d,l,n,e,m],kind:"Operation",name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:u,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},g,b,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},h,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[g],storageKey:null},i],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"totalReplicas",args:null,concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:Fe,storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:Fe,storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[i,j,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[I,f,k,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},h,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:c,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[g,i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:c,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[f,k,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},I],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[g,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[i,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"293ff73cb924b3052843cfcab0312ccd",id:null,metadata:{},name:"ProjectAdminDeploymentsPageQuery",operationKind:"query",text:`query ProjectAdminDeploymentsPageQuery(
  $projectId: UUID!
  $filter: DeploymentFilter
  $orderBy: [DeploymentOrderBy!]
  $limit: Int
  $offset: Int
) {
  projectDeployments(scope: {projectId: $projectId}, filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
    count
    edges {
      node {
        id
        ...BAIModelDeploymentNodesFragment
        ...DeploymentSettingModal_deployment
        metadata {
          name
          status
        }
        currentRevision @since(version: "26.4.3") {
          id
          revisionNumber
          ...DeploymentRevisionDetail_revision
        }
      }
    }
  }
}

fragment BAIDeploymentOwnerInfo_deployment on ModelDeployment {
  id
  creator @since(version: "26.4.3") {
    id
    basicInfo {
      email
      username
      fullName
    }
  }
}

fragment BAIDeploymentTagChips_metadata on ModelDeploymentMetadata {
  tags
}

fragment BAIModelDeploymentNodesFragment on ModelDeployment {
  id
  currentRevisionId
  metadata {
    projectId
    domainName
    name
    status
    tags
    createdAt
    updatedAt
    resourceGroupName
    projectV2 @since(version: "26.4.3") {
      basicInfo {
        name
      }
      id
    }
    ...BAIDeploymentTagChips_metadata
  }
  networkAccess {
    endpointUrl
    preferredDomainName
    openToPublic
  }
  defaultDeploymentStrategy {
    type
  }
  replicaState {
    desiredReplicaCount
  }
  totalReplicas: replicas {
    count
  }
  runningReplicas: replicas(filter: {status: {equals: RUNNING}}) {
    count
  }
  currentRevision @since(version: "26.4.3") {
    id
    revisionNumber
    modelMountConfig {
      vfolder {
        id
        name
      }
    }
  }
  ...BAIDeploymentOwnerInfo_deployment
}

fragment DeploymentRevisionDetail_revision on ModelRevision {
  id
  revisionNumber
  createdAt
  clusterConfig {
    mode
    size
  }
  resourceSlots @since(version: "26.4.2") {
    slotName
    quantity
  }
  resourceConfig {
    resourceOpts {
      entries {
        name
        value
      }
    }
  }
  modelRuntimeConfig {
    runtimeVariant {
      name
      id
    }
    inferenceRuntimeConfig
    environ {
      entries {
        name
        value
      }
    }
  }
  modelMountConfig {
    vfolderId
    mountDestination
    definitionPath
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
    }
  }
  extraMounts {
    vfolderId
    mountDestination
    mountPerm
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
    }
  }
  imageV2 @since(version: "26.4.3") {
    id
    identity {
      canonicalName
      architecture
    }
  }
  modelDefinition {
    models {
      name
      modelPath
      service {
        startCommand
        shell
        port
        preStartActions {
          action
          args
        }
        healthCheck {
          path
          initialDelay
          maxRetries
          interval
          maxWaitTime
          expectedStatusCode
        }
      }
    }
  }
}

fragment DeploymentSettingModal_deployment on ModelDeployment {
  id
  metadata {
    name
    tags
    resourceGroupName
  }
  networkAccess {
    openToPublic
  }
  replicaState {
    desiredReplicaCount
  }
}

fragment FolderLink_vfolderNode on VirtualFolderNode {
  row_id
  name
  ...VFolderNodeIdenticonFragment
}

fragment VFolderNodeIdenticonFragment on VirtualFolderNode {
  id
}
`}}}();In.hash="c0915455c90833c0f8fa382e2c4d6319";const al=l=>{"use memo";var on,dn,un,cn,mn,pn,yn,gn,fn;const e=Kn.c(162),{projectId:m}=l,{t:n}=bn(),{message:d}=Ln.useApp(),{logger:u}=Nn(),o=Rn(),[i,g]=ke.useState(null),[b,j]=ke.useState(null),[h,Fe]=ke.useState(null);let I;e[0]===Symbol.for("react.memo_cache_sentinel")?(I={current:1,pageSize:10},e[0]=I):I=e[0];const{baiPaginationOption:f,tablePaginationOption:k,setTablePaginationOption:c}=Pn(I);let he,Ie;e[1]===Symbol.for("react.memo_cache_sentinel")?(he={filter:Mn(tl),order:Dn(nl),statusCategory:Dn(["running","finished"]).withDefault("running")},Ie={history:"replace"},e[1]=he,e[2]=Ie):(he=e[1],Ie=e[2]);const[r,F]=xn(he,Ie),[Ee,Ue]=_n("table_column_overrides.ProjectAdminDeploymentsPage"),[De,D]=Vn();let Ce;e[3]===Symbol.for("react.memo_cache_sentinel")?(Ce=["STOPPED"],e[3]=Ce):Ce=e[3];const tn=Ce;let je;e[4]!==r.statusCategory?(je=r.statusCategory==="finished"?{status:{in:tn}}:{status:{notIn:tn}},e[4]=r.statusCategory,e[5]=je):je=e[5];const $e=je;let Te;e[6]!==r.order?(Te=Zn(r.order),e[6]=r.order,e[7]=Te):Te=e[7];const Se=Te;let Ae;e[8]!==r.filter?(Ae=r.filter??{},e[8]=r.filter,e[9]=Ae):Ae=e[9];const qe=Ae;let T;e[10]!==$e||e[11]!==qe?(T={...qe,...$e},e[10]=$e,e[11]=qe,e[12]=T):T=e[12];let A;e[13]!==Se?(A=Se?[{field:Se.field,direction:Se.direction}]:void 0,e[13]=Se,e[14]=A):A=e[14];let Le;e[15]!==f.limit||e[16]!==f.offset||e[17]!==m||e[18]!==A||e[19]!==T?(Le={projectId:m,filter:T,orderBy:A,limit:f.limit,offset:f.offset},e[15]=f.limit,e[16]=f.offset,e[17]=m,e[18]=A,e[19]=T,e[20]=Le):Le=e[20];const sn=Le,rn=ke.useDeferredValue(sn),ve=ke.useDeferredValue(De);let Ne;e[21]===Symbol.for("react.memo_cache_sentinel")?(Ne=In,e[21]=Ne):Ne=e[21];const ze=ve===On?"store-and-network":"network-only";let Re;e[22]!==ve||e[23]!==ze?(Re={fetchKey:ve,fetchPolicy:ze},e[22]=ve,e[23]=ze,e[24]=Re):Re=e[24];const L=Sn.useLazyLoadQuery(Ne,rn,Re);let p,Ke,Pe,N;e[25]!==((on=L.projectDeployments)==null?void 0:on.count)||e[26]!==((dn=L.projectDeployments)==null?void 0:dn.edges)||e[27]!==b||e[28]!==i?(p=Bn(wn((un=L.projectDeployments)==null?void 0:un.edges,"node")),N=((cn=L.projectDeployments)==null?void 0:cn.count)??0,Ke=i==null?null:p.find(t=>t.id===i)??null,Pe=b==null?null:p.find(t=>t.id===b)??null,e[25]=(mn=L.projectDeployments)==null?void 0:mn.count,e[26]=(pn=L.projectDeployments)==null?void 0:pn.edges,e[27]=b,e[28]=i,e[29]=p,e[30]=Ke,e[31]=Pe,e[32]=N):(p=e[29],Ke=e[30],Pe=e[31],N=e[32]);const s=Pe,R=rn!==sn||ve!==De;let Me;e[33]===Symbol.for("react.memo_cache_sentinel")?(Me=hn,e[33]=Me):Me=e[33];const[Qe,Ge]=Sn.useMutation(Me);let P;e[34]!==n?(P=n("deployment.filter.Name"),e[34]=n,e[35]=P):P=e[35];let M;e[36]!==P?(M={key:"name",propertyLabel:P,type:"string"},e[36]=P,e[37]=M):M=e[37];let x;e[38]!==n?(x=n("deployment.filter.Tags"),e[38]=n,e[39]=x):x=e[39];let _;e[40]!==x?(_={key:"tags",propertyLabel:x,type:"string"},e[40]=x,e[41]=_):_=e[41];let V;e[42]!==n?(V=n("deployment.filter.EndpointUrl"),e[42]=n,e[43]=V):V=e[43];let B;e[44]!==V?(B={key:"endpointUrl",propertyLabel:V,type:"string"},e[44]=V,e[45]=B):B=e[45];let w;e[46]!==n?(w=n("deployment.filter.OpenToPublic"),e[46]=n,e[47]=w):w=e[47];let O;e[48]!==w?(O={key:"openToPublic",propertyLabel:w,type:"boolean"},e[48]=w,e[49]=O):O=e[49];let xe;e[50]!==M||e[51]!==_||e[52]!==B||e[53]!==O?(xe=[M,_,B,O],e[50]=M,e[51]=_,e[52]=B,e[53]=O,e[54]=xe):xe=e[54];const He=xe;let _e;e[55]===Symbol.for("react.memo_cache_sentinel")?(_e={flexShrink:1},e[55]=_e):_e=e[55];const Cn=r.statusCategory;let E;e[56]!==F||e[57]!==c?(E=t=>{F({statusCategory:t.target.value}),c({current:1})},e[56]=F,e[57]=c,e[58]=E):E=e[58];let U;e[59]!==n?(U=n("deployment.Running"),e[59]=n,e[60]=U):U=e[60];let $;e[61]!==U?($={label:U,value:"running"},e[61]=U,e[62]=$):$=e[62];let q;e[63]!==n?(q=n("deployment.status.Terminated"),e[63]=n,e[64]=q):q=e[64];let z;e[65]!==q?(z={label:q,value:"finished"},e[65]=q,e[66]=z):z=e[66];let Q;e[67]!==$||e[68]!==z?(Q=[$,z],e[67]=$,e[68]=z,e[69]=Q):Q=e[69];let G;e[70]!==r.statusCategory||e[71]!==E||e[72]!==Q?(G=a.jsx(En,{optionType:"button",value:Cn,onChange:E,options:Q}),e[70]=r.statusCategory,e[71]=E,e[72]=Q,e[73]=G):G=e[73];const Je=r.filter??void 0;let H;e[74]!==F||e[75]!==c?(H=t=>{F({filter:t??null}),c({current:1})},e[74]=F,e[75]=c,e[76]=H):H=e[76];let J;e[77]!==He||e[78]!==Je||e[79]!==H?(J=a.jsx(ll,{filterProperties:He,value:Je,onChange:H}),e[77]=He,e[78]=Je,e[79]=H,e[80]=J):J=e[80];let W;e[81]!==G||e[82]!==J?(W=a.jsxs(ln,{gap:"sm",align:"start",wrap:"wrap",style:_e,children:[G,J]}),e[81]=G,e[82]=J,e[83]=W):W=e[83];let Y;e[84]!==D?(Y=t=>D(t),e[84]=D,e[85]=Y):Y=e[85];let X;e[86]!==De||e[87]!==R||e[88]!==Y?(X=a.jsx(Un,{loading:R,value:De,onChange:Y,autoUpdateDelay:15e3}),e[86]=De,e[87]=R,e[88]=Y,e[89]=X):X=e[89];let Z;e[90]!==W||e[91]!==X?(Z=a.jsxs(ln,{justify:"between",wrap:"wrap",gap:"sm",children:[W,X]}),e[90]=W,e[91]=X,e[92]=Z):Z=e[92];let ee;e[93]!==F?(ee=t=>{F({order:t??null})},e[93]=F,e[94]=ee):ee=e[94];let ne;e[95]!==c?(ne=(t,C)=>{c({current:t,pageSize:C})},e[95]=c,e[96]=ne):ne=e[96];let le;e[97]!==ne||e[98]!==k.current||e[99]!==k.pageSize||e[100]!==N?(le={current:k.current,pageSize:k.pageSize,total:N,onChange:ne},e[97]=ne,e[98]=k.current,e[99]=k.pageSize,e[100]=N,e[101]=le):le=e[101];let ae;e[102]!==Ee||e[103]!==Ue?(ae={columnOverrides:Ee,onColumnOverridesChange:Ue},e[102]=Ee,e[103]=Ue,e[104]=ae):ae=e[104];let te;e[105]!==p||e[106]!==n||e[107]!==o?(te=t=>{const C=["name","currentRevisionNumber","status","replicaSummary","model","createdAt","owner","id","endpointUrl","tags","updatedAt","openToPublic","resourceGroup","domainName","projectId"],jn=new Set(["name","currentRevisionNumber","status","replicaSummary","model","createdAt","owner"]);return t.filter(y=>C.includes(y.key)).map(y=>{let be=y;return y.key==="name"?be={...y,render:(kn,S)=>{var K,Oe;const v=Wn((K=S.metadata)==null?void 0:K.status);return a.jsx($n,{title:((Oe=S.metadata)==null?void 0:Oe.name)??"-",onTitleClick:()=>o(`/project-admin-deployments/${vn(S.id)}`),copyable:!0,showActions:"always",actions:[{key:"edit",title:n("deployment.EditDeployment"),icon:a.jsx(qn,{}),disabled:v,onClick:()=>g(S.id)},{key:"delete",title:n("deployment.DeleteDeployment"),icon:a.jsx(zn,{}),type:"danger",disabled:v,onClick:()=>j(S.id)}]})}}:y.key==="currentRevisionNumber"?be={...y,render:(kn,S)=>{const v=p.find(Oe=>Oe.id===S.id),K=v==null?void 0:v.currentRevision;return(K==null?void 0:K.revisionNumber)==null?a.jsx(an.Text,{type:"secondary",children:"-"}):a.jsx(an.Link,{onClick:()=>Fe(K),children:`#${K.revisionNumber}`})}}:y.key==="tags"&&(be={...y,render:(kn,S)=>a.jsx(Yn,{metadataFrgmt:S.metadata,stopRowClick:!0,onTagClick:v=>{o({pathname:"/project-admin-deployments",search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:v}})}).toString()})},fallback:a.jsx(an.Text,{type:"secondary",children:"-"})})}),y.key==="name"?be:{...be,defaultHidden:!jn.has(y.key)}})},e[105]=p,e[106]=n,e[107]=o,e[108]=te):te=e[108];let ie;e[109]!==p||e[110]!==R||e[111]!==r.order||e[112]!==ee||e[113]!==le||e[114]!==ae||e[115]!==te?(ie=a.jsx(el,{deploymentsFrgmt:p,loading:R,order:r.order,onChangeOrder:ee,pagination:le,tableSettings:ae,customizeColumns:te}),e[109]=p,e[110]=R,e[111]=r.order,e[112]=ee,e[113]=le,e[114]=ae,e[115]=te,e[116]=ie):ie=e[116];let se;e[117]!==Z||e[118]!==ie?(se=a.jsxs(ln,{direction:"column",align:"stretch",gap:"sm",children:[Z,ie]}),e[117]=Z,e[118]=ie,e[119]=se):se=e[119];const We=!!Ke,Ye=Ke??null;let re;e[120]!==D?(re=t=>{g(null),t&&D()},e[120]=D,e[121]=re):re=e[121];let oe;e[122]!==We||e[123]!==Ye||e[124]!==re?(oe=a.jsx(Qn,{open:We,deploymentFrgmt:Ye,onRequestClose:re}),e[122]=We,e[123]=Ye,e[124]=re,e[125]=oe):oe=e[125];const Xe=!!s;let de;e[126]!==n?(de=n("deployment.DeleteDeployment"),e[126]=n,e[127]=de):de=e[127];let ue;e[128]!==n?(ue=n("deployment.Deployment"),e[128]=n,e[129]=ue):ue=e[129];let ce;e[130]!==s?(ce=s?[{key:s.id,label:((yn=s.metadata)==null?void 0:yn.name)??""}]:[],e[130]=s,e[131]=ce):ce=e[131];const Ze=((gn=s==null?void 0:s.metadata)==null?void 0:gn.name)??"",en=((fn=s==null?void 0:s.metadata)==null?void 0:fn.name)??"";let me;e[132]!==en?(me={placeholder:en},e[132]=en,e[133]=me):me=e[133];let pe;e[134]!==Ge?(pe={loading:Ge},e[134]=Ge,e[135]=pe):pe=e[135];let ye;e[136]!==Qe||e[137]!==s||e[138]!==u||e[139]!==d||e[140]!==n||e[141]!==D?(ye=()=>{s&&Qe({variables:{input:{id:vn(s.id)??s.id}},onCompleted:(t,C)=>{if(C&&C.length>0){u.error("Failed to delete deployment",C),d.error(n("deployment.FailedToDeleteDeployment"));return}d.success(n("deployment.DeploymentDeleted")),j(null),D()},onError:t=>{u.error("Failed to delete deployment",t),d.error(n("deployment.FailedToDeleteDeployment"))}})},e[136]=Qe,e[137]=s,e[138]=u,e[139]=d,e[140]=n,e[141]=D,e[142]=ye):ye=e[142];let Ve;e[143]===Symbol.for("react.memo_cache_sentinel")?(Ve=()=>j(null),e[143]=Ve):Ve=e[143];let ge;e[144]!==Xe||e[145]!==de||e[146]!==ue||e[147]!==ce||e[148]!==Ze||e[149]!==me||e[150]!==pe||e[151]!==ye?(ge=a.jsx(Gn,{open:Xe,title:de,target:ue,items:ce,confirmText:Ze,requireConfirmInput:!0,inputProps:me,okButtonProps:pe,onOk:ye,onCancel:Ve}),e[144]=Xe,e[145]=de,e[146]=ue,e[147]=ce,e[148]=Ze,e[149]=me,e[150]=pe,e[151]=ye,e[152]=ge):ge=e[152];const nn=!!h;let Be;e[153]===Symbol.for("react.memo_cache_sentinel")?(Be=()=>Fe(null),e[153]=Be):Be=e[153];let fe;e[154]!==h||e[155]!==nn?(fe=a.jsx(Hn,{children:a.jsx(Xn,{open:nn,revisionFrgmt:h,onClose:Be})}),e[154]=h,e[155]=nn,e[156]=fe):fe=e[156];let we;return e[157]!==se||e[158]!==oe||e[159]!==ge||e[160]!==fe?(we=a.jsxs(a.Fragment,{children:[se,oe,ge,fe]}),e[157]=se,e[158]=oe,e[159]=ge,e[160]=fe,e[161]=we):we=e[161],we},ml=()=>{"use memo";const l=Kn.c(9),{t:e}=bn(),m=Tn();let n;l[0]!==e?(n=e("webui.menu.ProjectDeployments"),l[0]=e,l[1]=n):n=l[1];let d;l[2]===Symbol.for("react.memo_cache_sentinel")?(d={header:{borderBottom:"none"},body:{paddingTop:0}},l[2]=d):d=l[2];let u;l[3]===Symbol.for("react.memo_cache_sentinel")?(u=a.jsx(Fn,{active:!0}),l[3]=u):u=l[3];let o;l[4]!==m.id?(o=a.jsx(An,{children:a.jsx(ke.Suspense,{fallback:u,children:m.id?a.jsx(al,{projectId:m.id}):a.jsx(Fn,{active:!0})})}),l[4]=m.id,l[5]=o):o=l[5];let i;return l[6]!==n||l[7]!==o?(i=a.jsx(Jn,{variant:"borderless",title:n,styles:d,children:o}),l[6]=n,l[7]=o,l[8]=i):i=l[8],i};function tl(l){return typeof l=="object"&&l!==null&&!Array.isArray(l)?l:{}}export{ml as default};
//# sourceMappingURL=ProjectAdminDeploymentsPage-DBEL90RX.js.map
