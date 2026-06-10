import{h as bl,u as Kl,j as n,r as Fe,ay as Nl,B as Ce,bH as Ml,A as Rl,v as Al,p as xl,aW as Pl,br as jl,bs as Dl,cV as _l,bt as Bl,a4 as Vl,at as wl,am as Ol,i as vl,aM as El,a6 as Ul,aw as $l,cb as ql,aC as Gl,b2 as Ql,aY as zl,cW as Wl,a_ as Hl,N as Sl,T as dl,cX as Jl,b6 as Yl,a7 as Xl}from"./index-CuMUOZIG.js";import{B as Zl,D as en}from"./DeploymentRevisionDetailDrawer-CqqYIRLX.js";import{p as ln,B as nn,a as an}from"./BAIModelDeploymentNodes-DHF_sHto.js";import{B as tn}from"./BAIGraphQLPropertyFilter-BJSph4O9.js";import"./FolderLink-B_vcYigG.js";import"./BAIId-BIK-PEa4.js";import"./BooleanTag-CNCumd6I.js";const hl=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"input"}],l=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"DeploymentListPageDeleteMutation",selections:l,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"DeploymentListPageDeleteMutation",selections:l},params:{cacheID:"4639cd2572faeb586296319d8202e23a",id:null,metadata:{},name:"DeploymentListPageDeleteMutation",operationKind:"mutation",text:`mutation DeploymentListPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}}();hl.hash="867cc2a31d2fc3342a0bafe7502c0483";const Cl=function(){var e={defaultValue:null,kind:"LocalArgument",name:"filter"},l={defaultValue:null,kind:"LocalArgument",name:"limit"},r={defaultValue:null,kind:"LocalArgument",name:"offset"},o={defaultValue:null,kind:"LocalArgument",name:"orderBy"},u=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],g={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},De={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},b=[g],L={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},K={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null};return{fragment:{argumentDefinitions:[e,l,r,o],kind:"Fragment",metadata:null,name:"DeploymentListPageQuery",selections:[{alias:null,args:u,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[g,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[d,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[c,C],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[d,S,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,o,l,r],kind:"Operation",name:"DeploymentListPageQuery",selections:[{alias:null,args:u,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[g,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[d,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},c,C,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},De,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[c],storageKey:null},d],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategyGQL",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"totalReplicas",args:null,concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:b,storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:b,storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[d,S,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[d,c],storageKey:null},L,K,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},De,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[c,d],storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfoGQL",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[L,K,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[d,c,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[d,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[d,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"53bff8826d7d44ab0d2b257821cb85f8",id:null,metadata:{},name:"DeploymentListPageQuery",operationKind:"query",text:`query DeploymentListPageQuery(
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
  modelRuntimeConfig {
    runtimeVariant {
      name
      id
    }
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
    }
  }
  modelDefinition {
    models {
      name
      modelPath
      service {
        startCommand
        port
        healthCheck {
          path
          initialDelay
          maxRetries
          interval
          maxWaitTime
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
}
`}}}();Cl.hash="7e57808b70c4eb1aab4a7a4d8af607d7";const sn=()=>{"use memo";var yl,fl,kl;const e=bl.c(171),{t:l}=Kl(),{message:r}=Rl.useApp(),{logger:o}=Al(),u=xl(),[g,d]=Pl(!1),{setLeft:c,setRight:C}=d,[S,De]=Fe.useState(null),[b,L]=Fe.useState(null),[K,cl]=Fe.useState(null);let Le;e[0]===Symbol.for("react.memo_cache_sentinel")?(Le={current:1,pageSize:10},e[0]=Le):Le=e[0];const{baiPaginationOption:T,tablePaginationOption:I,setTablePaginationOption:y}=jl(Le);let Te,Ie;e[1]===Symbol.for("react.memo_cache_sentinel")?(Te={filter:_l(rn),order:Dl(an),statusCategory:Dl(["running","finished"]).withDefault("running")},Ie={history:"replace"},e[1]=Te,e[2]=Ie):(Te=e[1],Ie=e[2]);const[s,f]=Bl(Te,Ie),[ze,We]=Vl("table_column_overrides.DeploymentListPage"),[ve,k]=wl(),Ne=Ol();let Me;e[3]!==s.order?(Me=ln(s.order),e[3]=s.order,e[4]=Me):Me=e[4];const Se=Me;let Re;e[5]!==Se?(Re=Se?[{field:Se.field,direction:Se.direction}]:void 0,e[5]=Se,e[6]=Re):Re=e[6];const He=Re;let Ae;e[7]===Symbol.for("react.memo_cache_sentinel")?(Ae=["STOPPED"],e[7]=Ae):Ae=e[7];const ml=Ae;let xe;e[8]!==s.statusCategory?(xe=s.statusCategory==="finished"?{status:{in:ml}}:{status:{notIn:ml}},e[8]=s.statusCategory,e[9]=xe):xe=e[9];const Je=xe;let Pe;e[10]!==Ne.id?(Pe=Ne.id?{projectId:{equals:Ne.id}}:{},e[10]=Ne.id,e[11]=Pe):Pe=e[11];const Ye=Pe;let je;e[12]!==s.filter?(je=s.filter??{},e[12]=s.filter,e[13]=je):je=e[13];const Xe=je;let N;e[14]!==Ye||e[15]!==Je||e[16]!==Xe?(N={...Xe,...Je,...Ye},e[14]=Ye,e[15]=Je,e[16]=Xe,e[17]=N):N=e[17];let _e;e[18]!==T.limit||e[19]!==T.offset||e[20]!==He||e[21]!==N?(_e={filter:N,orderBy:He,limit:T.limit,offset:T.offset},e[18]=T.limit,e[19]=T.offset,e[20]=He,e[21]=N,e[22]=_e):_e=e[22];const pl=_e,gl=Fe.useDeferredValue(pl),be=Fe.useDeferredValue(ve);let Be;e[23]===Symbol.for("react.memo_cache_sentinel")?(Be=Cl,e[23]=Be):Be=e[23];const Ze=be===$l?"store-and-network":"network-only";let Ve;e[24]!==be||e[25]!==Ze?(Ve={fetchPolicy:Ze,fetchKey:be},e[24]=be,e[25]=Ze,e[26]=Ve):Ve=e[26];const{myDeployments:a}=vl.useLazyLoadQuery(Be,gl,Ve);let m,Ke,we,M;e[27]!==b||e[28]!==S||e[29]!==(a==null?void 0:a.count)||e[30]!==(a==null?void 0:a.edges)?(m=El(Ul(a==null?void 0:a.edges,"node")),M=(a==null?void 0:a.count)??0,Ke=S==null?null:m.find(t=>t.id===S)??null,we=b==null?null:m.find(t=>t.id===b)??null,e[27]=b,e[28]=S,e[29]=a==null?void 0:a.count,e[30]=a==null?void 0:a.edges,e[31]=m,e[32]=Ke,e[33]=we,e[34]=M):(m=e[31],Ke=e[32],we=e[33],M=e[34]);const i=we,R=gl!==pl||be!==ve;let Oe;e[35]===Symbol.for("react.memo_cache_sentinel")?(Oe=hl,e[35]=Oe):Oe=e[35];const[el,ll]=vl.useMutation(Oe);let A;e[36]!==l?(A=l("deployment.filter.Name"),e[36]=l,e[37]=A):A=e[37];let x;e[38]!==A?(x={key:"name",propertyLabel:A,type:"string"},e[38]=A,e[39]=x):x=e[39];let P;e[40]!==l?(P=l("deployment.filter.Tags"),e[40]=l,e[41]=P):P=e[41];let j;e[42]!==P?(j={key:"tags",propertyLabel:P,type:"string"},e[42]=P,e[43]=j):j=e[43];let _;e[44]!==l?(_=l("deployment.filter.EndpointUrl"),e[44]=l,e[45]=_):_=e[45];let B;e[46]!==_?(B={key:"endpointUrl",propertyLabel:_,type:"string"},e[46]=_,e[47]=B):B=e[47];let V;e[48]!==l?(V=l("deployment.filter.OpenToPublic"),e[48]=l,e[49]=V):V=e[49];let w;e[50]!==V?(w={key:"openToPublic",propertyLabel:V,type:"boolean"},e[50]=V,e[51]=w):w=e[51];let Ee;e[52]!==x||e[53]!==j||e[54]!==B||e[55]!==w?(Ee=[x,j,B,w],e[52]=x,e[53]=j,e[54]=B,e[55]=w,e[56]=Ee):Ee=e[56];const nl=Ee,Ll=on;let Ue;e[57]===Symbol.for("react.memo_cache_sentinel")?(Ue={flexShrink:1},e[57]=Ue):Ue=e[57];const Tl=s.statusCategory;let O;e[58]!==f||e[59]!==y?(O=t=>{f({statusCategory:t.target.value}),y({current:1})},e[58]=f,e[59]=y,e[60]=O):O=e[60];let E;e[61]!==l?(E=l("deployment.Running"),e[61]=l,e[62]=E):E=e[62];let U;e[63]!==E?(U={label:E,value:"running"},e[63]=E,e[64]=U):U=e[64];let $;e[65]!==l?($=l("deployment.status.Terminated"),e[65]=l,e[66]=$):$=e[66];let q;e[67]!==$?(q={label:$,value:"finished"},e[67]=$,e[68]=q):q=e[68];let G;e[69]!==U||e[70]!==q?(G=[U,q],e[69]=U,e[70]=q,e[71]=G):G=e[71];let Q;e[72]!==s.statusCategory||e[73]!==O||e[74]!==G?(Q=n.jsx(ql,{value:Tl,onChange:O,options:G}),e[72]=s.statusCategory,e[73]=O,e[74]=G,e[75]=Q):Q=e[75];const al=s.filter??void 0;let z;e[76]!==f||e[77]!==y?(z=t=>{f({filter:t??null}),y({current:1})},e[76]=f,e[77]=y,e[78]=z):z=e[78];let W;e[79]!==nl||e[80]!==al||e[81]!==z?(W=n.jsx(tn,{filterProperties:nl,value:al,onChange:z}),e[79]=nl,e[80]=al,e[81]=z,e[82]=W):W=e[82];let H;e[83]!==Q||e[84]!==W?(H=n.jsxs(Ce,{gap:"sm",align:"start",wrap:"wrap",style:Ue,children:[Q,W]}),e[83]=Q,e[84]=W,e[85]=H):H=e[85];let J;e[86]!==ve||e[87]!==R||e[88]!==k?(J=n.jsx(Gl,{autoUpdateDelay:15e3,value:ve,onChange:k,loading:R}),e[86]=ve,e[87]=R,e[88]=k,e[89]=J):J=e[89];let Y;e[90]!==l?(Y=l("deployment.CreateDeployment"),e[90]=l,e[91]=Y):Y=e[91];let X;e[92]!==C||e[93]!==Y?(X=n.jsx(Ql,{type:"primary",onClick:C,children:Y}),e[92]=C,e[93]=Y,e[94]=X):X=e[94];let Z;e[95]!==J||e[96]!==X?(Z=n.jsxs(Ce,{gap:"xs",align:"center",children:[J,X]}),e[95]=J,e[96]=X,e[97]=Z):Z=e[97];let ee;e[98]!==H||e[99]!==Z?(ee=n.jsxs(Ce,{justify:"between",wrap:"wrap",gap:"sm",children:[H,Z]}),e[98]=H,e[99]=Z,e[100]=ee):ee=e[100];let le;e[101]!==f?(le=t=>{f({order:t??null})},e[101]=f,e[102]=le):le=e[102];let ne;e[103]!==y?(ne=(t,h)=>{y({current:t,pageSize:h})},e[103]=y,e[104]=ne):ne=e[104];let ae;e[105]!==ne||e[106]!==I.current||e[107]!==I.pageSize||e[108]!==M?(ae={current:I.current,pageSize:I.pageSize,total:M,onChange:ne},e[105]=ne,e[106]=I.current,e[107]=I.pageSize,e[108]=M,e[109]=ae):ae=e[109];let te;e[110]!==ze||e[111]!==We?(te={columnOverrides:ze,onColumnOverridesChange:We},e[110]=ze,e[111]=We,e[112]=te):te=e[112];let ie;e[113]!==m||e[114]!==l||e[115]!==u?(ie=t=>{const h=["name","currentRevisionNumber","status","replicaSummary","model","createdAt","id","endpointUrl","tags","updatedAt","openToPublic","resourceGroup"],Il=new Set(["name","currentRevisionNumber","status","replicaSummary","model","createdAt"]);return t.filter(p=>h.includes(p.key)).map(p=>{let he=p;return p.key==="name"?he={...p,render:(Fl,F)=>{var v,Qe;const D=Ll((v=F.metadata)==null?void 0:v.status);return n.jsx(zl,{title:((Qe=F.metadata)==null?void 0:Qe.name)??"-",onTitleClick:()=>u(`/deployments/${Sl(F.id)}`),copyable:!0,showActions:"always",actions:[{key:"edit",title:l("deployment.EditDeployment"),icon:n.jsx(Wl,{}),disabled:D,onClick:()=>De(F.id)},{key:"delete",title:l("deployment.DeleteDeployment"),icon:n.jsx(Hl,{}),type:"danger",disabled:D,onClick:()=>L(F.id)}]})}}:p.key==="currentRevisionNumber"?he={...p,render:(Fl,F)=>{const D=m.find(Qe=>Qe.id===F.id),v=D==null?void 0:D.currentRevision;return(v==null?void 0:v.revisionNumber)==null?n.jsx(dl.Text,{type:"secondary",children:"-"}):n.jsx(dl.Link,{onClick:()=>cl(v),children:`#${v.revisionNumber}`})}}:p.key==="tags"&&(he={...p,render:(Fl,F)=>n.jsx(Zl,{metadataFrgmt:F.metadata,stopRowClick:!0,onTagClick:D=>{u({pathname:"/deployments",search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:D}})}).toString()})},fallback:n.jsx(dl.Text,{type:"secondary",children:"-"})})}),p.key==="name"?he:{...he,defaultHidden:!Il.has(p.key)}})},e[113]=m,e[114]=l,e[115]=u,e[116]=ie):ie=e[116];let se;e[117]!==m||e[118]!==R||e[119]!==s.order||e[120]!==le||e[121]!==ae||e[122]!==te||e[123]!==ie?(se=n.jsx(nn,{deploymentsFrgmt:m,loading:R,order:s.order,onChangeOrder:le,pagination:ae,tableSettings:te,customizeColumns:ie}),e[117]=m,e[118]=R,e[119]=s.order,e[120]=le,e[121]=ae,e[122]=te,e[123]=ie,e[124]=se):se=e[124];let re;e[125]!==ee||e[126]!==se?(re=n.jsxs(Ce,{direction:"column",align:"stretch",gap:"sm",children:[ee,se]}),e[125]=ee,e[126]=se,e[127]=re):re=e[127];const tl=g||!!Ke,il=Ke??null;let oe;e[128]!==c||e[129]!==k?(oe=t=>{c(),De(null),t&&k()},e[128]=c,e[129]=k,e[130]=oe):oe=e[130];let ue;e[131]!==tl||e[132]!==il||e[133]!==oe?(ue=n.jsx(Jl,{open:tl,deploymentFrgmt:il,onRequestClose:oe}),e[131]=tl,e[132]=il,e[133]=oe,e[134]=ue):ue=e[134];const sl=!!i;let de;e[135]!==l?(de=l("deployment.DeleteDeployment"),e[135]=l,e[136]=de):de=e[136];let ce;e[137]!==l?(ce=l("deployment.Deployment"),e[137]=l,e[138]=ce):ce=e[138];let me;e[139]!==i?(me=i?[{key:i.id,label:((yl=i.metadata)==null?void 0:yl.name)??""}]:[],e[139]=i,e[140]=me):me=e[140];const rl=((fl=i==null?void 0:i.metadata)==null?void 0:fl.name)??"",ol=((kl=i==null?void 0:i.metadata)==null?void 0:kl.name)??"";let pe;e[141]!==ol?(pe={placeholder:ol},e[141]=ol,e[142]=pe):pe=e[142];let ge;e[143]!==ll?(ge={loading:ll},e[143]=ll,e[144]=ge):ge=e[144];let ye;e[145]!==el||e[146]!==i||e[147]!==o||e[148]!==r||e[149]!==l||e[150]!==k?(ye=()=>{i&&el({variables:{input:{id:Sl(i.id)??i.id}},onCompleted:(t,h)=>{if(h&&h.length>0){o.error("Failed to delete deployment",h),r.error(l("deployment.FailedToDeleteDeployment"));return}r.success(l("deployment.DeploymentDeleted")),L(null),k()},onError:t=>{o.error("Failed to delete deployment",t),r.error(l("deployment.FailedToDeleteDeployment"))}})},e[145]=el,e[146]=i,e[147]=o,e[148]=r,e[149]=l,e[150]=k,e[151]=ye):ye=e[151];let $e;e[152]===Symbol.for("react.memo_cache_sentinel")?($e=()=>L(null),e[152]=$e):$e=e[152];let fe;e[153]!==sl||e[154]!==de||e[155]!==ce||e[156]!==me||e[157]!==rl||e[158]!==pe||e[159]!==ge||e[160]!==ye?(fe=n.jsx(Yl,{open:sl,title:de,target:ce,items:me,confirmText:rl,requireConfirmInput:!0,inputProps:pe,okButtonProps:ge,onOk:ye,onCancel:$e}),e[153]=sl,e[154]=de,e[155]=ce,e[156]=me,e[157]=rl,e[158]=pe,e[159]=ge,e[160]=ye,e[161]=fe):fe=e[161];const ul=!!K;let qe;e[162]===Symbol.for("react.memo_cache_sentinel")?(qe=()=>cl(null),e[162]=qe):qe=e[162];let ke;e[163]!==K||e[164]!==ul?(ke=n.jsx(Xl,{children:n.jsx(en,{open:ul,revisionFrgmt:K,onClose:qe})}),e[163]=K,e[164]=ul,e[165]=ke):ke=e[165];let Ge;return e[166]!==re||e[167]!==ue||e[168]!==fe||e[169]!==ke?(Ge=n.jsxs(n.Fragment,{children:[re,ue,fe,ke]}),e[166]=re,e[167]=ue,e[168]=fe,e[169]=ke,e[170]=Ge):Ge=e[170],Ge},fn=()=>{"use memo";const e=bl.c(6),{t:l}=Kl();let r;e[0]!==l?(r=l("webui.menu.Deployments"),e[0]=l,e[1]=r):r=e[1];let o;e[2]===Symbol.for("react.memo_cache_sentinel")?(o={body:{paddingTop:0}},e[2]=o):o=e[2];let u;e[3]===Symbol.for("react.memo_cache_sentinel")?(u=n.jsx(Fe.Suspense,{fallback:n.jsx(Nl,{active:!0}),children:n.jsx(sn,{})}),e[3]=u):u=e[3];let g;return e[4]!==r?(g=n.jsx(Ce,{direction:"column",align:"stretch",gap:"md",children:n.jsx(Ml,{variant:"borderless",title:r,styles:o,children:u})}),e[4]=r,e[5]=g):g=e[5],g};function rn(e){return typeof e=="object"&&e!==null&&!Array.isArray(e)?e:{}}function on(e){return!e||e==="%future added value"?!1:["STOPPING","STOPPED","TERMINATED"].includes(e)}export{fn as default};
//# sourceMappingURL=DeploymentListPage-8RvRQTry.js.map
