import{h as Kn,u as bn,aj as An,j as a,bJ as Tn,r as ke,aw as Fn,A as Ln,v as Nn,p as Pn,bs as Rn,bt as Dn,c_ as Mn,bu as xn,a4 as Vn,ar as _n,i as Sn,aK as Bn,a6 as wn,au as On,c0 as En,B as ln,aA as Un,aX as $n,c$ as qn,aZ as Qn,N as vn,T as an,d0 as zn,b7 as Gn,a7 as Hn,bI as Jn}from"./index-DUzRNOsy.js";import{i as Wn,B as Xn,D as Yn}from"./DeploymentRevisionDetailDrawer-D6Bfwmgb.js";import{p as Zn,B as el,a as nl}from"./BAIModelDeploymentNodes-NQmdPeWn.js";import{B as ll}from"./BAIGraphQLPropertyFilter-qgXPJI5K.js";import"./FolderLink-CnlbHxRm.js";import"./BAIId-CNbrZgal.js";import"./BooleanTag-mevBkxIL.js";const hn=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e},params:{cacheID:"1463ddcf31aa971e7f72ca3901c5db76",id:null,metadata:{},name:"ProjectAdminDeploymentsPageDeleteMutation",operationKind:"mutation",text:`mutation ProjectAdminDeploymentsPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}}();hn.hash="42ff73332d0c41e5828ba82d49920b78";const In=function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},c={defaultValue:null,kind:"LocalArgument",name:"offset"},n={defaultValue:null,kind:"LocalArgument",name:"orderBy"},d={defaultValue:null,kind:"LocalArgument",name:"projectId"},u=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{fields:[{kind:"Variable",name:"projectId",variableName:"projectId"}],kind:"ObjectValue",name:"scope"}],o={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},j={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},Fe={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[i,y,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},I={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},f=[y,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}];return{fragment:{argumentDefinitions:[l,e,c,n,d],kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:u,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[i,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[y,b],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[i,j,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[d,l,n,e,c],kind:"Operation",name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:u,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},y,b,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},h,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[y],storageKey:null},i],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[o],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[i,j,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[Fe,I,g,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},h,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:f,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[y,i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:f,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[I,g,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},Fe],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[y,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[i,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"18295edf5049f1b62350290ad9923277",id:null,metadata:{},name:"ProjectAdminDeploymentsPageQuery",operationKind:"query",text:`query ProjectAdminDeploymentsPageQuery(
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
`}}}();In.hash="c0915455c90833c0f8fa382e2c4d6319";const al=l=>{"use memo";var on,dn,un,cn,mn,pn,yn,gn,fn;const e=Kn.c(162),{projectId:c}=l,{t:n}=bn(),{message:d}=Ln.useApp(),{logger:u}=Nn(),o=Pn(),[i,y]=ke.useState(null),[b,j]=ke.useState(null),[h,Fe]=ke.useState(null);let I;e[0]===Symbol.for("react.memo_cache_sentinel")?(I={current:1,pageSize:10},e[0]=I):I=e[0];const{baiPaginationOption:g,tablePaginationOption:f,setTablePaginationOption:k}=Rn(I);let he,Ie;e[1]===Symbol.for("react.memo_cache_sentinel")?(he={filter:Mn(tl),order:Dn(nl),statusCategory:Dn(["running","finished"]).withDefault("running")},Ie={history:"replace"},e[1]=he,e[2]=Ie):(he=e[1],Ie=e[2]);const[s,F]=xn(he,Ie),[Ee,Ue]=Vn("table_column_overrides.ProjectAdminDeploymentsPage"),[De,D]=_n();let Ce;e[3]===Symbol.for("react.memo_cache_sentinel")?(Ce=["STOPPED"],e[3]=Ce):Ce=e[3];const tn=Ce;let je;e[4]!==s.statusCategory?(je=s.statusCategory==="finished"?{status:{in:tn}}:{status:{notIn:tn}},e[4]=s.statusCategory,e[5]=je):je=e[5];const $e=je;let Ae;e[6]!==s.order?(Ae=Zn(s.order),e[6]=s.order,e[7]=Ae):Ae=e[7];const Se=Ae;let Te;e[8]!==s.filter?(Te=s.filter??{},e[8]=s.filter,e[9]=Te):Te=e[9];const qe=Te;let A;e[10]!==$e||e[11]!==qe?(A={...qe,...$e},e[10]=$e,e[11]=qe,e[12]=A):A=e[12];let T;e[13]!==Se?(T=Se?[{field:Se.field,direction:Se.direction}]:void 0,e[13]=Se,e[14]=T):T=e[14];let Le;e[15]!==g.limit||e[16]!==g.offset||e[17]!==c||e[18]!==T||e[19]!==A?(Le={projectId:c,filter:A,orderBy:T,limit:g.limit,offset:g.offset},e[15]=g.limit,e[16]=g.offset,e[17]=c,e[18]=T,e[19]=A,e[20]=Le):Le=e[20];const rn=Le,sn=ke.useDeferredValue(rn),ve=ke.useDeferredValue(De);let Ne;e[21]===Symbol.for("react.memo_cache_sentinel")?(Ne=In,e[21]=Ne):Ne=e[21];const Qe=ve===On?"store-and-network":"network-only";let Pe;e[22]!==ve||e[23]!==Qe?(Pe={fetchKey:ve,fetchPolicy:Qe},e[22]=ve,e[23]=Qe,e[24]=Pe):Pe=e[24];const L=Sn.useLazyLoadQuery(Ne,sn,Pe);let m,Ke,Re,N;e[25]!==((on=L.projectDeployments)==null?void 0:on.count)||e[26]!==((dn=L.projectDeployments)==null?void 0:dn.edges)||e[27]!==b||e[28]!==i?(m=Bn(wn((un=L.projectDeployments)==null?void 0:un.edges,"node")),N=((cn=L.projectDeployments)==null?void 0:cn.count)??0,Ke=i==null?null:m.find(t=>t.id===i)??null,Re=b==null?null:m.find(t=>t.id===b)??null,e[25]=(mn=L.projectDeployments)==null?void 0:mn.count,e[26]=(pn=L.projectDeployments)==null?void 0:pn.edges,e[27]=b,e[28]=i,e[29]=m,e[30]=Ke,e[31]=Re,e[32]=N):(m=e[29],Ke=e[30],Re=e[31],N=e[32]);const r=Re,P=sn!==rn||ve!==De;let Me;e[33]===Symbol.for("react.memo_cache_sentinel")?(Me=hn,e[33]=Me):Me=e[33];const[ze,Ge]=Sn.useMutation(Me);let R;e[34]!==n?(R=n("deployment.filter.Name"),e[34]=n,e[35]=R):R=e[35];let M;e[36]!==R?(M={key:"name",propertyLabel:R,type:"string"},e[36]=R,e[37]=M):M=e[37];let x;e[38]!==n?(x=n("deployment.filter.Tags"),e[38]=n,e[39]=x):x=e[39];let V;e[40]!==x?(V={key:"tags",propertyLabel:x,type:"string"},e[40]=x,e[41]=V):V=e[41];let _;e[42]!==n?(_=n("deployment.filter.EndpointUrl"),e[42]=n,e[43]=_):_=e[43];let B;e[44]!==_?(B={key:"endpointUrl",propertyLabel:_,type:"string"},e[44]=_,e[45]=B):B=e[45];let w;e[46]!==n?(w=n("deployment.filter.OpenToPublic"),e[46]=n,e[47]=w):w=e[47];let O;e[48]!==w?(O={key:"openToPublic",propertyLabel:w,type:"boolean"},e[48]=w,e[49]=O):O=e[49];let xe;e[50]!==M||e[51]!==V||e[52]!==B||e[53]!==O?(xe=[M,V,B,O],e[50]=M,e[51]=V,e[52]=B,e[53]=O,e[54]=xe):xe=e[54];const He=xe;let Ve;e[55]===Symbol.for("react.memo_cache_sentinel")?(Ve={flexShrink:1},e[55]=Ve):Ve=e[55];const Cn=s.statusCategory;let E;e[56]!==F||e[57]!==k?(E=t=>{F({statusCategory:t.target.value}),k({current:1})},e[56]=F,e[57]=k,e[58]=E):E=e[58];let U;e[59]!==n?(U=n("deployment.Running"),e[59]=n,e[60]=U):U=e[60];let $;e[61]!==U?($={label:U,value:"running"},e[61]=U,e[62]=$):$=e[62];let q;e[63]!==n?(q=n("deployment.status.Terminated"),e[63]=n,e[64]=q):q=e[64];let Q;e[65]!==q?(Q={label:q,value:"finished"},e[65]=q,e[66]=Q):Q=e[66];let z;e[67]!==$||e[68]!==Q?(z=[$,Q],e[67]=$,e[68]=Q,e[69]=z):z=e[69];let G;e[70]!==s.statusCategory||e[71]!==E||e[72]!==z?(G=a.jsx(En,{optionType:"button",value:Cn,onChange:E,options:z}),e[70]=s.statusCategory,e[71]=E,e[72]=z,e[73]=G):G=e[73];const Je=s.filter??void 0;let H;e[74]!==F||e[75]!==k?(H=t=>{F({filter:t??null}),k({current:1})},e[74]=F,e[75]=k,e[76]=H):H=e[76];let J;e[77]!==He||e[78]!==Je||e[79]!==H?(J=a.jsx(ll,{filterProperties:He,value:Je,onChange:H}),e[77]=He,e[78]=Je,e[79]=H,e[80]=J):J=e[80];let W;e[81]!==G||e[82]!==J?(W=a.jsxs(ln,{gap:"sm",align:"start",wrap:"wrap",style:Ve,children:[G,J]}),e[81]=G,e[82]=J,e[83]=W):W=e[83];let X;e[84]!==D?(X=t=>D(t),e[84]=D,e[85]=X):X=e[85];let Y;e[86]!==De||e[87]!==P||e[88]!==X?(Y=a.jsx(Un,{loading:P,value:De,onChange:X,autoUpdateDelay:15e3}),e[86]=De,e[87]=P,e[88]=X,e[89]=Y):Y=e[89];let Z;e[90]!==W||e[91]!==Y?(Z=a.jsxs(ln,{justify:"between",wrap:"wrap",gap:"sm",children:[W,Y]}),e[90]=W,e[91]=Y,e[92]=Z):Z=e[92];let ee;e[93]!==F?(ee=t=>{F({order:t??null})},e[93]=F,e[94]=ee):ee=e[94];let ne;e[95]!==k?(ne=(t,C)=>{k({current:t,pageSize:C})},e[95]=k,e[96]=ne):ne=e[96];let le;e[97]!==ne||e[98]!==f.current||e[99]!==f.pageSize||e[100]!==N?(le={current:f.current,pageSize:f.pageSize,total:N,onChange:ne},e[97]=ne,e[98]=f.current,e[99]=f.pageSize,e[100]=N,e[101]=le):le=e[101];let ae;e[102]!==Ee||e[103]!==Ue?(ae={columnOverrides:Ee,onColumnOverridesChange:Ue},e[102]=Ee,e[103]=Ue,e[104]=ae):ae=e[104];let te;e[105]!==m||e[106]!==n||e[107]!==o?(te=t=>{const C=["name","currentRevisionNumber","status","replicaSummary","model","createdAt","owner","id","endpointUrl","tags","updatedAt","openToPublic","resourceGroup","domainName","projectId"],jn=new Set(["name","currentRevisionNumber","status","replicaSummary","model","createdAt","owner"]);return t.filter(p=>C.includes(p.key)).map(p=>{let be=p;return p.key==="name"?be={...p,render:(kn,S)=>{var K,Oe;const v=Wn((K=S.metadata)==null?void 0:K.status);return a.jsx($n,{title:((Oe=S.metadata)==null?void 0:Oe.name)??"-",onTitleClick:()=>o(`/project-admin-deployments/${vn(S.id)}`),copyable:!0,showActions:"always",actions:[{key:"edit",title:n("deployment.EditDeployment"),icon:a.jsx(qn,{}),disabled:v,onClick:()=>y(S.id)},{key:"delete",title:n("deployment.DeleteDeployment"),icon:a.jsx(Qn,{}),type:"danger",disabled:v,onClick:()=>j(S.id)}]})}}:p.key==="currentRevisionNumber"?be={...p,render:(kn,S)=>{const v=m.find(Oe=>Oe.id===S.id),K=v==null?void 0:v.currentRevision;return(K==null?void 0:K.revisionNumber)==null?a.jsx(an.Text,{type:"secondary",children:"-"}):a.jsx(an.Link,{onClick:()=>Fe(K),children:`#${K.revisionNumber}`})}}:p.key==="tags"&&(be={...p,render:(kn,S)=>a.jsx(Xn,{metadataFrgmt:S.metadata,stopRowClick:!0,onTagClick:v=>{o({pathname:"/project-admin-deployments",search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:v}})}).toString()})},fallback:a.jsx(an.Text,{type:"secondary",children:"-"})})}),p.key==="name"?be:{...be,defaultHidden:!jn.has(p.key)}})},e[105]=m,e[106]=n,e[107]=o,e[108]=te):te=e[108];let ie;e[109]!==m||e[110]!==P||e[111]!==s.order||e[112]!==ee||e[113]!==le||e[114]!==ae||e[115]!==te?(ie=a.jsx(el,{deploymentsFrgmt:m,loading:P,order:s.order,onChangeOrder:ee,pagination:le,tableSettings:ae,customizeColumns:te}),e[109]=m,e[110]=P,e[111]=s.order,e[112]=ee,e[113]=le,e[114]=ae,e[115]=te,e[116]=ie):ie=e[116];let re;e[117]!==Z||e[118]!==ie?(re=a.jsxs(ln,{direction:"column",align:"stretch",gap:"sm",children:[Z,ie]}),e[117]=Z,e[118]=ie,e[119]=re):re=e[119];const We=!!Ke,Xe=Ke??null;let se;e[120]!==D?(se=t=>{y(null),t&&D()},e[120]=D,e[121]=se):se=e[121];let oe;e[122]!==We||e[123]!==Xe||e[124]!==se?(oe=a.jsx(zn,{open:We,deploymentFrgmt:Xe,onRequestClose:se}),e[122]=We,e[123]=Xe,e[124]=se,e[125]=oe):oe=e[125];const Ye=!!r;let de;e[126]!==n?(de=n("deployment.DeleteDeployment"),e[126]=n,e[127]=de):de=e[127];let ue;e[128]!==n?(ue=n("deployment.Deployment"),e[128]=n,e[129]=ue):ue=e[129];let ce;e[130]!==r?(ce=r?[{key:r.id,label:((yn=r.metadata)==null?void 0:yn.name)??""}]:[],e[130]=r,e[131]=ce):ce=e[131];const Ze=((gn=r==null?void 0:r.metadata)==null?void 0:gn.name)??"",en=((fn=r==null?void 0:r.metadata)==null?void 0:fn.name)??"";let me;e[132]!==en?(me={placeholder:en},e[132]=en,e[133]=me):me=e[133];let pe;e[134]!==Ge?(pe={loading:Ge},e[134]=Ge,e[135]=pe):pe=e[135];let ye;e[136]!==ze||e[137]!==r||e[138]!==u||e[139]!==d||e[140]!==n||e[141]!==D?(ye=()=>{r&&ze({variables:{input:{id:vn(r.id)??r.id}},onCompleted:(t,C)=>{if(C&&C.length>0){u.error("Failed to delete deployment",C),d.error(n("deployment.FailedToDeleteDeployment"));return}d.success(n("deployment.DeploymentDeleted")),j(null),D()},onError:t=>{u.error("Failed to delete deployment",t),d.error(n("deployment.FailedToDeleteDeployment"))}})},e[136]=ze,e[137]=r,e[138]=u,e[139]=d,e[140]=n,e[141]=D,e[142]=ye):ye=e[142];let _e;e[143]===Symbol.for("react.memo_cache_sentinel")?(_e=()=>j(null),e[143]=_e):_e=e[143];let ge;e[144]!==Ye||e[145]!==de||e[146]!==ue||e[147]!==ce||e[148]!==Ze||e[149]!==me||e[150]!==pe||e[151]!==ye?(ge=a.jsx(Gn,{open:Ye,title:de,target:ue,items:ce,confirmText:Ze,requireConfirmInput:!0,inputProps:me,okButtonProps:pe,onOk:ye,onCancel:_e}),e[144]=Ye,e[145]=de,e[146]=ue,e[147]=ce,e[148]=Ze,e[149]=me,e[150]=pe,e[151]=ye,e[152]=ge):ge=e[152];const nn=!!h;let Be;e[153]===Symbol.for("react.memo_cache_sentinel")?(Be=()=>Fe(null),e[153]=Be):Be=e[153];let fe;e[154]!==h||e[155]!==nn?(fe=a.jsx(Hn,{children:a.jsx(Yn,{open:nn,revisionFrgmt:h,onClose:Be})}),e[154]=h,e[155]=nn,e[156]=fe):fe=e[156];let we;return e[157]!==re||e[158]!==oe||e[159]!==ge||e[160]!==fe?(we=a.jsxs(a.Fragment,{children:[re,oe,ge,fe]}),e[157]=re,e[158]=oe,e[159]=ge,e[160]=fe,e[161]=we):we=e[161],we},ml=()=>{"use memo";const l=Kn.c(9),{t:e}=bn(),c=An();let n;l[0]!==e?(n=e("webui.menu.ProjectDeployments"),l[0]=e,l[1]=n):n=l[1];let d;l[2]===Symbol.for("react.memo_cache_sentinel")?(d={header:{borderBottom:"none"},body:{paddingTop:0}},l[2]=d):d=l[2];let u;l[3]===Symbol.for("react.memo_cache_sentinel")?(u=a.jsx(Fn,{active:!0}),l[3]=u):u=l[3];let o;l[4]!==c.id?(o=a.jsx(Tn,{children:a.jsx(ke.Suspense,{fallback:u,children:c.id?a.jsx(al,{projectId:c.id}):a.jsx(Fn,{active:!0})})}),l[4]=c.id,l[5]=o):o=l[5];let i;return l[6]!==n||l[7]!==o?(i=a.jsx(Jn,{variant:"borderless",title:n,styles:d,children:o}),l[6]=n,l[7]=o,l[8]=i):i=l[8],i};function tl(l){return typeof l=="object"&&l!==null&&!Array.isArray(l)?l:{}}export{ml as default};
//# sourceMappingURL=ProjectAdminDeploymentsPage-BaWsbW4y.js.map
