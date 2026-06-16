import{h as Kl,u as bl,j as n,r as Fe,aw as Tl,B as Le,bI as Nl,A as Al,v as Rl,p as Ml,aV as xl,bs as Pl,bt as Sl,c_ as jl,bu as _l,a4 as Vl,ar as Bl,aj as wl,i as vl,aK as Ol,a6 as El,au as $l,c0 as Ul,aA as ql,b2 as Ql,aX as zl,c$ as Gl,aZ as Hl,N as Dl,T as cl,d0 as Wl,b7 as Jl,a7 as Xl}from"./index-DUzRNOsy.js";import{i as Yl,B as Zl,D as en}from"./DeploymentRevisionDetailDrawer-D6Bfwmgb.js";import{p as ln,B as nn,a as an}from"./BAIModelDeploymentNodes-NQmdPeWn.js";import{B as tn}from"./BAIGraphQLPropertyFilter-qgXPJI5K.js";import"./FolderLink-CnlbHxRm.js";import"./BAIId-CNbrZgal.js";import"./BooleanTag-mevBkxIL.js";const hl=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"input"}],l=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"DeploymentListPageDeleteMutation",selections:l,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"DeploymentListPageDeleteMutation",selections:l},params:{cacheID:"4639cd2572faeb586296319d8202e23a",id:null,metadata:{},name:"DeploymentListPageDeleteMutation",operationKind:"mutation",text:`mutation DeploymentListPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}}();hl.hash="867cc2a31d2fc3342a0bafe7502c0483";const Cl=function(){var e={defaultValue:null,kind:"LocalArgument",name:"filter"},l={defaultValue:null,kind:"LocalArgument",name:"limit"},r={defaultValue:null,kind:"LocalArgument",name:"offset"},o={defaultValue:null,kind:"LocalArgument",name:"orderBy"},u=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],p={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},D={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},Se={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},K={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[d,c,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},L={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},ve=[c,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}];return{fragment:{argumentDefinitions:[e,l,r,o],kind:"Fragment",metadata:null,name:"DeploymentListPageQuery",selections:[{alias:null,args:u,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[p,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[d,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[c,C],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[d,D,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,o,l,r],kind:"Operation",name:"DeploymentListPageQuery",selections:[{alias:null,args:u,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[p,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[d,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},c,C,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},Se,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[c],storageKey:null},d],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[p],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[d,D,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[K,L,b,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},Se,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:ve,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[c,d],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:ve,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[L,b,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},K],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[d,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[d,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"c9362f4b73a6d5186bd2991d494b6584",id:null,metadata:{},name:"DeploymentListPageQuery",operationKind:"query",text:`query DeploymentListPageQuery(
  $filter: DeploymentFilter
  $orderBy: [DeploymentOrderBy!]
  $limit: Int
  $offset: Int
) {
  myDeployments(filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
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
`}}}();Cl.hash="7e57808b70c4eb1aab4a7a4d8af607d7";const sn=()=>{"use memo";var yl,fl,kl;const e=Kl.c(171),{t:l}=bl(),{message:r}=Al.useApp(),{logger:o}=Rl(),u=Ml(),[p,d]=xl(!1),{setLeft:c,setRight:C}=d,[D,Se]=Fe.useState(null),[K,L]=Fe.useState(null),[b,ve]=Fe.useState(null);let Ie;e[0]===Symbol.for("react.memo_cache_sentinel")?(Ie={current:1,pageSize:10},e[0]=Ie):Ie=e[0];const{baiPaginationOption:I,tablePaginationOption:T,setTablePaginationOption:y}=Pl(Ie);let Te,Ne;e[1]===Symbol.for("react.memo_cache_sentinel")?(Te={filter:jl(rn),order:Sl(an),statusCategory:Sl(["running","finished"]).withDefault("running")},Ne={history:"replace"},e[1]=Te,e[2]=Ne):(Te=e[1],Ne=e[2]);const[s,f]=_l(Te,Ne),[He,We]=Vl("table_column_overrides.DeploymentListPage"),[De,k]=Bl(),Ae=wl();let Re;e[3]!==s.order?(Re=ln(s.order),e[3]=s.order,e[4]=Re):Re=e[4];const Ke=Re;let Me;e[5]!==Ke?(Me=Ke?[{field:Ke.field,direction:Ke.direction}]:void 0,e[5]=Ke,e[6]=Me):Me=e[6];const Je=Me;let xe;e[7]===Symbol.for("react.memo_cache_sentinel")?(xe=["STOPPED"],e[7]=xe):xe=e[7];const ml=xe;let Pe;e[8]!==s.statusCategory?(Pe=s.statusCategory==="finished"?{status:{in:ml}}:{status:{notIn:ml}},e[8]=s.statusCategory,e[9]=Pe):Pe=e[9];const Xe=Pe;let je;e[10]!==Ae.id?(je=Ae.id?{projectId:{equals:Ae.id}}:{},e[10]=Ae.id,e[11]=je):je=e[11];const Ye=je;let _e;e[12]!==s.filter?(_e=s.filter??{},e[12]=s.filter,e[13]=_e):_e=e[13];const Ze=_e;let N;e[14]!==Ye||e[15]!==Xe||e[16]!==Ze?(N={...Ze,...Xe,...Ye},e[14]=Ye,e[15]=Xe,e[16]=Ze,e[17]=N):N=e[17];let Ve;e[18]!==I.limit||e[19]!==I.offset||e[20]!==Je||e[21]!==N?(Ve={filter:N,orderBy:Je,limit:I.limit,offset:I.offset},e[18]=I.limit,e[19]=I.offset,e[20]=Je,e[21]=N,e[22]=Ve):Ve=e[22];const gl=Ve,pl=Fe.useDeferredValue(gl),be=Fe.useDeferredValue(De);let Be;e[23]===Symbol.for("react.memo_cache_sentinel")?(Be=Cl,e[23]=Be):Be=e[23];const el=be===$l?"store-and-network":"network-only";let we;e[24]!==be||e[25]!==el?(we={fetchPolicy:el,fetchKey:be},e[24]=be,e[25]=el,e[26]=we):we=e[26];const{myDeployments:a}=vl.useLazyLoadQuery(Be,pl,we);let m,he,Oe,A;e[27]!==K||e[28]!==D||e[29]!==(a==null?void 0:a.count)||e[30]!==(a==null?void 0:a.edges)?(m=Ol(El(a==null?void 0:a.edges,"node")),A=(a==null?void 0:a.count)??0,he=D==null?null:m.find(t=>t.id===D)??null,Oe=K==null?null:m.find(t=>t.id===K)??null,e[27]=K,e[28]=D,e[29]=a==null?void 0:a.count,e[30]=a==null?void 0:a.edges,e[31]=m,e[32]=he,e[33]=Oe,e[34]=A):(m=e[31],he=e[32],Oe=e[33],A=e[34]);const i=Oe,R=pl!==gl||be!==De;let Ee;e[35]===Symbol.for("react.memo_cache_sentinel")?(Ee=hl,e[35]=Ee):Ee=e[35];const[ll,nl]=vl.useMutation(Ee);let M;e[36]!==l?(M=l("deployment.filter.Name"),e[36]=l,e[37]=M):M=e[37];let x;e[38]!==M?(x={key:"name",propertyLabel:M,type:"string"},e[38]=M,e[39]=x):x=e[39];let P;e[40]!==l?(P=l("deployment.filter.Tags"),e[40]=l,e[41]=P):P=e[41];let j;e[42]!==P?(j={key:"tags",propertyLabel:P,type:"string"},e[42]=P,e[43]=j):j=e[43];let _;e[44]!==l?(_=l("deployment.filter.EndpointUrl"),e[44]=l,e[45]=_):_=e[45];let V;e[46]!==_?(V={key:"endpointUrl",propertyLabel:_,type:"string"},e[46]=_,e[47]=V):V=e[47];let B;e[48]!==l?(B=l("deployment.filter.OpenToPublic"),e[48]=l,e[49]=B):B=e[49];let w;e[50]!==B?(w={key:"openToPublic",propertyLabel:B,type:"boolean"},e[50]=B,e[51]=w):w=e[51];let $e;e[52]!==x||e[53]!==j||e[54]!==V||e[55]!==w?($e=[x,j,V,w],e[52]=x,e[53]=j,e[54]=V,e[55]=w,e[56]=$e):$e=e[56];const al=$e;let Ue;e[57]===Symbol.for("react.memo_cache_sentinel")?(Ue={flexShrink:1},e[57]=Ue):Ue=e[57];const Ll=s.statusCategory;let O;e[58]!==f||e[59]!==y?(O=t=>{f({statusCategory:t.target.value}),y({current:1})},e[58]=f,e[59]=y,e[60]=O):O=e[60];let E;e[61]!==l?(E=l("deployment.Running"),e[61]=l,e[62]=E):E=e[62];let $;e[63]!==E?($={label:E,value:"running"},e[63]=E,e[64]=$):$=e[64];let U;e[65]!==l?(U=l("deployment.status.Terminated"),e[65]=l,e[66]=U):U=e[66];let q;e[67]!==U?(q={label:U,value:"finished"},e[67]=U,e[68]=q):q=e[68];let Q;e[69]!==$||e[70]!==q?(Q=[$,q],e[69]=$,e[70]=q,e[71]=Q):Q=e[71];let z;e[72]!==s.statusCategory||e[73]!==O||e[74]!==Q?(z=n.jsx(Ul,{value:Ll,onChange:O,options:Q}),e[72]=s.statusCategory,e[73]=O,e[74]=Q,e[75]=z):z=e[75];const tl=s.filter??void 0;let G;e[76]!==f||e[77]!==y?(G=t=>{f({filter:t??null}),y({current:1})},e[76]=f,e[77]=y,e[78]=G):G=e[78];let H;e[79]!==al||e[80]!==tl||e[81]!==G?(H=n.jsx(tn,{filterProperties:al,value:tl,onChange:G}),e[79]=al,e[80]=tl,e[81]=G,e[82]=H):H=e[82];let W;e[83]!==z||e[84]!==H?(W=n.jsxs(Le,{gap:"sm",align:"start",wrap:"wrap",style:Ue,children:[z,H]}),e[83]=z,e[84]=H,e[85]=W):W=e[85];let J;e[86]!==De||e[87]!==R||e[88]!==k?(J=n.jsx(ql,{autoUpdateDelay:15e3,value:De,onChange:k,loading:R}),e[86]=De,e[87]=R,e[88]=k,e[89]=J):J=e[89];let X;e[90]!==l?(X=l("deployment.CreateDeployment"),e[90]=l,e[91]=X):X=e[91];let Y;e[92]!==C||e[93]!==X?(Y=n.jsx(Ql,{type:"primary",onClick:C,children:X}),e[92]=C,e[93]=X,e[94]=Y):Y=e[94];let Z;e[95]!==J||e[96]!==Y?(Z=n.jsxs(Le,{gap:"xs",align:"center",children:[J,Y]}),e[95]=J,e[96]=Y,e[97]=Z):Z=e[97];let ee;e[98]!==W||e[99]!==Z?(ee=n.jsxs(Le,{justify:"between",wrap:"wrap",gap:"sm",children:[W,Z]}),e[98]=W,e[99]=Z,e[100]=ee):ee=e[100];let le;e[101]!==f?(le=t=>{f({order:t??null})},e[101]=f,e[102]=le):le=e[102];let ne;e[103]!==y?(ne=(t,h)=>{y({current:t,pageSize:h})},e[103]=y,e[104]=ne):ne=e[104];let ae;e[105]!==ne||e[106]!==T.current||e[107]!==T.pageSize||e[108]!==A?(ae={current:T.current,pageSize:T.pageSize,total:A,onChange:ne},e[105]=ne,e[106]=T.current,e[107]=T.pageSize,e[108]=A,e[109]=ae):ae=e[109];let te;e[110]!==He||e[111]!==We?(te={columnOverrides:He,onColumnOverridesChange:We},e[110]=He,e[111]=We,e[112]=te):te=e[112];let ie;e[113]!==m||e[114]!==l||e[115]!==u?(ie=t=>{const h=["name","currentRevisionNumber","status","replicaSummary","model","createdAt","id","endpointUrl","tags","updatedAt","openToPublic","resourceGroup"],Il=new Set(["name","currentRevisionNumber","status","replicaSummary","model","createdAt"]);return t.filter(g=>h.includes(g.key)).map(g=>{let Ce=g;return g.key==="name"?Ce={...g,render:(Fl,F)=>{var v,Ge;const S=Yl((v=F.metadata)==null?void 0:v.status);return n.jsx(zl,{title:((Ge=F.metadata)==null?void 0:Ge.name)??"-",onTitleClick:()=>u(`/deployments/${Dl(F.id)}`),copyable:!0,showActions:"always",actions:[{key:"edit",title:l("deployment.EditDeployment"),icon:n.jsx(Gl,{}),disabled:S,onClick:()=>Se(F.id)},{key:"delete",title:l("deployment.DeleteDeployment"),icon:n.jsx(Hl,{}),type:"danger",disabled:S,onClick:()=>L(F.id)}]})}}:g.key==="currentRevisionNumber"?Ce={...g,render:(Fl,F)=>{const S=m.find(Ge=>Ge.id===F.id),v=S==null?void 0:S.currentRevision;return(v==null?void 0:v.revisionNumber)==null?n.jsx(cl.Text,{type:"secondary",children:"-"}):n.jsx(cl.Link,{onClick:()=>ve(v),children:`#${v.revisionNumber}`})}}:g.key==="tags"&&(Ce={...g,render:(Fl,F)=>n.jsx(Zl,{metadataFrgmt:F.metadata,stopRowClick:!0,onTagClick:S=>{u({pathname:"/deployments",search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:S}})}).toString()})},fallback:n.jsx(cl.Text,{type:"secondary",children:"-"})})}),g.key==="name"?Ce:{...Ce,defaultHidden:!Il.has(g.key)}})},e[113]=m,e[114]=l,e[115]=u,e[116]=ie):ie=e[116];let se;e[117]!==m||e[118]!==R||e[119]!==s.order||e[120]!==le||e[121]!==ae||e[122]!==te||e[123]!==ie?(se=n.jsx(nn,{deploymentsFrgmt:m,loading:R,order:s.order,onChangeOrder:le,pagination:ae,tableSettings:te,customizeColumns:ie}),e[117]=m,e[118]=R,e[119]=s.order,e[120]=le,e[121]=ae,e[122]=te,e[123]=ie,e[124]=se):se=e[124];let re;e[125]!==ee||e[126]!==se?(re=n.jsxs(Le,{direction:"column",align:"stretch",gap:"sm",children:[ee,se]}),e[125]=ee,e[126]=se,e[127]=re):re=e[127];const il=p||!!he,sl=he??null;let oe;e[128]!==c||e[129]!==k?(oe=t=>{c(),Se(null),t&&k()},e[128]=c,e[129]=k,e[130]=oe):oe=e[130];let ue;e[131]!==il||e[132]!==sl||e[133]!==oe?(ue=n.jsx(Wl,{open:il,deploymentFrgmt:sl,onRequestClose:oe}),e[131]=il,e[132]=sl,e[133]=oe,e[134]=ue):ue=e[134];const rl=!!i;let de;e[135]!==l?(de=l("deployment.DeleteDeployment"),e[135]=l,e[136]=de):de=e[136];let ce;e[137]!==l?(ce=l("deployment.Deployment"),e[137]=l,e[138]=ce):ce=e[138];let me;e[139]!==i?(me=i?[{key:i.id,label:((yl=i.metadata)==null?void 0:yl.name)??""}]:[],e[139]=i,e[140]=me):me=e[140];const ol=((fl=i==null?void 0:i.metadata)==null?void 0:fl.name)??"",ul=((kl=i==null?void 0:i.metadata)==null?void 0:kl.name)??"";let ge;e[141]!==ul?(ge={placeholder:ul},e[141]=ul,e[142]=ge):ge=e[142];let pe;e[143]!==nl?(pe={loading:nl},e[143]=nl,e[144]=pe):pe=e[144];let ye;e[145]!==ll||e[146]!==i||e[147]!==o||e[148]!==r||e[149]!==l||e[150]!==k?(ye=()=>{i&&ll({variables:{input:{id:Dl(i.id)??i.id}},onCompleted:(t,h)=>{if(h&&h.length>0){o.error("Failed to delete deployment",h),r.error(l("deployment.FailedToDeleteDeployment"));return}r.success(l("deployment.DeploymentDeleted")),L(null),k()},onError:t=>{o.error("Failed to delete deployment",t),r.error(l("deployment.FailedToDeleteDeployment"))}})},e[145]=ll,e[146]=i,e[147]=o,e[148]=r,e[149]=l,e[150]=k,e[151]=ye):ye=e[151];let qe;e[152]===Symbol.for("react.memo_cache_sentinel")?(qe=()=>L(null),e[152]=qe):qe=e[152];let fe;e[153]!==rl||e[154]!==de||e[155]!==ce||e[156]!==me||e[157]!==ol||e[158]!==ge||e[159]!==pe||e[160]!==ye?(fe=n.jsx(Jl,{open:rl,title:de,target:ce,items:me,confirmText:ol,requireConfirmInput:!0,inputProps:ge,okButtonProps:pe,onOk:ye,onCancel:qe}),e[153]=rl,e[154]=de,e[155]=ce,e[156]=me,e[157]=ol,e[158]=ge,e[159]=pe,e[160]=ye,e[161]=fe):fe=e[161];const dl=!!b;let Qe;e[162]===Symbol.for("react.memo_cache_sentinel")?(Qe=()=>ve(null),e[162]=Qe):Qe=e[162];let ke;e[163]!==b||e[164]!==dl?(ke=n.jsx(Xl,{children:n.jsx(en,{open:dl,revisionFrgmt:b,onClose:Qe})}),e[163]=b,e[164]=dl,e[165]=ke):ke=e[165];let ze;return e[166]!==re||e[167]!==ue||e[168]!==fe||e[169]!==ke?(ze=n.jsxs(n.Fragment,{children:[re,ue,fe,ke]}),e[166]=re,e[167]=ue,e[168]=fe,e[169]=ke,e[170]=ze):ze=e[170],ze},yn=()=>{"use memo";const e=Kl.c(6),{t:l}=bl();let r;e[0]!==l?(r=l("webui.menu.Deployments"),e[0]=l,e[1]=r):r=e[1];let o;e[2]===Symbol.for("react.memo_cache_sentinel")?(o={body:{paddingTop:0}},e[2]=o):o=e[2];let u;e[3]===Symbol.for("react.memo_cache_sentinel")?(u=n.jsx(Fe.Suspense,{fallback:n.jsx(Tl,{active:!0}),children:n.jsx(sn,{})}),e[3]=u):u=e[3];let p;return e[4]!==r?(p=n.jsx(Le,{direction:"column",align:"stretch",gap:"md",children:n.jsx(Nl,{variant:"borderless",title:r,styles:o,children:u})}),e[4]=r,e[5]=p):p=e[5],p};function rn(e){return typeof e=="object"&&e!==null&&!Array.isArray(e)?e:{}}export{yn as default};
//# sourceMappingURL=DeploymentListPage-CmxuMulO.js.map
