import{i as hl,u as bl,j as n,r as ve,az as Nl,B as Ie,bJ as Pl,A as Rl,E as Al,w as xl,x as Ml,o as Vl,aY as jl,bt as Sl,a6 as _l,a4 as Bl,aa as wl,au as Ol,an as El,k as vl,aN as Ul,ac as $l,ax as ql,c2 as zl,bX as Ql,s as Gl,aZ as Hl,a_ as Jl,V as Kl,T as cl,v as Dl,da as Wl,b8 as Yl}from"./index-DB7yUW94.js";import{i as Xl,B as Zl,D as en}from"./DeploymentRevisionDetailDrawer-d0xOqlsg.js";import{a as ln,p as nn,B as an}from"./BAIModelDeploymentNodes-DhMFfApN.js";import{B as tn}from"./BAIGraphQLPropertyFilter-URVW9R-R.js";import{S as sn}from"./square-pen-BbLd2-Yf.js";import"./parseCliCommand-DLNI3aPC.js";import"./FolderLink-DJPzhdHs.js";import"./BAIId-DEscoFqK.js";import"./BooleanTag-UCS-BJYP.js";const Cl=(function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"input"}],l=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"DeploymentListPageDeleteMutation",selections:l,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"DeploymentListPageDeleteMutation",selections:l},params:{cacheID:"4639cd2572faeb586296319d8202e23a",id:null,metadata:{},name:"DeploymentListPageDeleteMutation",operationKind:"mutation",text:`mutation DeploymentListPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}})();Cl.hash="867cc2a31d2fc3342a0bafe7502c0483";const Ll=(function(){var e={defaultValue:null,kind:"LocalArgument",name:"filter"},l={defaultValue:null,kind:"LocalArgument",name:"limit"},r={defaultValue:null,kind:"LocalArgument",name:"offset"},u={defaultValue:null,kind:"LocalArgument",name:"orderBy"},d=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],o={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},L={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},K={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},Ke={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[c,p,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},D={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},T={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},De=[p,h];return{fragment:{argumentDefinitions:[e,l,r,u],kind:"Fragment",metadata:null,name:"DeploymentListPageQuery",selections:[{alias:null,args:d,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[c,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[p,C],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[c,L,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,u,l,r],kind:"Operation",name:"DeploymentListPageQuery",selections:[{alias:null,args:d,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},p,C,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},K,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[p],storageKey:null},c],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[o],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[c,L,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[Ke,D,T,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},K,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:De,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[p,c],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:De,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},h,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[p,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},c],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[D,T,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},Ke],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[c,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[p,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[c,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"4e6b325179329c7c916583ab20770756",id:null,metadata:{},name:"DeploymentListPageQuery",operationKind:"query",text:`query DeploymentListPageQuery(
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
    runtimeVariantPresetValues @since(version: "26.4.4rc9") {
      presetId
      value
      preset {
        name
        displayName
        targetSpec {
          key
        }
        id
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
`}}})();Ll.hash="7e57808b70c4eb1aab4a7a4d8af607d7";const rn=()=>{"use memo";var yl,fl,kl;const e=hl.c(172),{t:l}=bl(),{message:r}=Rl.useApp(),{logger:u}=Al(),d=xl(),o=Ml(),[c,p]=Vl(!1),{setLeft:C,setRight:L}=p,[K,Ke]=ve.useState(null),[D,T]=ve.useState(null),[h,De]=ve.useState(null);let Ne;e[0]===Symbol.for("react.memo_cache_sentinel")?(Ne={current:1,pageSize:10},e[0]=Ne):Ne=e[0];const{baiPaginationOption:I,tablePaginationOption:N,setTablePaginationOption:y}=jl(Ne);let Pe,Re;e[1]===Symbol.for("react.memo_cache_sentinel")?(Pe={filter:_l(on),order:Sl(ln),statusCategory:Sl(["running","finished"]).withDefault("running")},Re={history:"replace"},e[1]=Pe,e[2]=Re):(Pe=e[1],Re=e[2]);const[s,f]=Bl(Pe,Re),[Je,We]=wl("table_column_overrides.DeploymentListPage"),[he,k]=Ol(),Ae=El();let xe;e[3]!==s.order?(xe=nn(s.order),e[3]=s.order,e[4]=xe):xe=e[4];const be=xe;let Me;e[5]!==be?(Me=be?[{field:be.field,direction:be.direction}]:void 0,e[5]=be,e[6]=Me):Me=e[6];const Ye=Me;let Ve;e[7]===Symbol.for("react.memo_cache_sentinel")?(Ve=["STOPPED"],e[7]=Ve):Ve=e[7];const ml=Ve;let je;e[8]!==s.statusCategory?(je=s.statusCategory==="finished"?{status:{in:ml}}:{status:{notIn:ml}},e[8]=s.statusCategory,e[9]=je):je=e[9];const Xe=je;let _e;e[10]!==Ae.id?(_e=Ae.id?{projectId:{equals:Ae.id}}:{},e[10]=Ae.id,e[11]=_e):_e=e[11];const Ze=_e;let P;e[12]!==s.filter?(P=s.filter??{},e[12]=s.filter,e[13]=P):P=e[13];let R;e[14]!==Ze||e[15]!==Xe||e[16]!==P?(R={...P,...Xe,...Ze},e[14]=Ze,e[15]=Xe,e[16]=P,e[17]=R):R=e[17];let Be;e[18]!==I.limit||e[19]!==I.offset||e[20]!==Ye||e[21]!==R?(Be={filter:R,orderBy:Ye,limit:I.limit,offset:I.offset},e[18]=I.limit,e[19]=I.offset,e[20]=Ye,e[21]=R,e[22]=Be):Be=e[22];const gl=Be,pl=ve.useDeferredValue(gl),Ce=ve.useDeferredValue(he);let we;e[23]===Symbol.for("react.memo_cache_sentinel")?(we=Ll,e[23]=we):we=e[23];const el=Ce===ql?"store-and-network":"network-only";let Oe;e[24]!==Ce||e[25]!==el?(Oe={fetchPolicy:el,fetchKey:Ce},e[24]=Ce,e[25]=el,e[26]=Oe):Oe=e[26];const{myDeployments:a}=vl.useLazyLoadQuery(we,pl,Oe);let m,Le,Ee,A;e[27]!==D||e[28]!==K||e[29]!==(a==null?void 0:a.count)||e[30]!==(a==null?void 0:a.edges)?(m=Ul($l(a==null?void 0:a.edges,"node")),A=(a==null?void 0:a.count)??0,Le=K==null?null:m.find(t=>t.id===K)??null,Ee=D==null?null:m.find(t=>t.id===D)??null,e[27]=D,e[28]=K,e[29]=a==null?void 0:a.count,e[30]=a==null?void 0:a.edges,e[31]=m,e[32]=Le,e[33]=Ee,e[34]=A):(m=e[31],Le=e[32],Ee=e[33],A=e[34]);const i=Ee,x=pl!==gl||Ce!==he;let Ue;e[35]===Symbol.for("react.memo_cache_sentinel")?(Ue=Cl,e[35]=Ue):Ue=e[35];const[ll,nl]=vl.useMutation(Ue);let M;e[36]!==l?(M=l("deployment.filter.Name"),e[36]=l,e[37]=M):M=e[37];let V;e[38]!==M?(V={key:"name",propertyLabel:M,type:"string"},e[38]=M,e[39]=V):V=e[39];let j;e[40]!==l?(j=l("deployment.filter.Tags"),e[40]=l,e[41]=j):j=e[41];let _;e[42]!==j?(_={key:"tags",propertyLabel:j,type:"string"},e[42]=j,e[43]=_):_=e[43];let B;e[44]!==l?(B=l("deployment.filter.EndpointUrl"),e[44]=l,e[45]=B):B=e[45];let w;e[46]!==B?(w={key:"endpointUrl",propertyLabel:B,type:"string"},e[46]=B,e[47]=w):w=e[47];let O;e[48]!==l?(O=l("deployment.filter.OpenToPublic"),e[48]=l,e[49]=O):O=e[49];let E;e[50]!==O?(E={key:"openToPublic",propertyLabel:O,type:"boolean"},e[50]=O,e[51]=E):E=e[51];let $e;e[52]!==V||e[53]!==_||e[54]!==w||e[55]!==E?($e=[V,_,w,E],e[52]=V,e[53]=_,e[54]=w,e[55]=E,e[56]=$e):$e=e[56];const al=$e;let qe;e[57]===Symbol.for("react.memo_cache_sentinel")?(qe={flexShrink:1},e[57]=qe):qe=e[57];const Tl=s.statusCategory;let U;e[58]!==f||e[59]!==y?(U=t=>{f({statusCategory:t.target.value}),y({current:1})},e[58]=f,e[59]=y,e[60]=U):U=e[60];let $;e[61]!==l?($=l("deployment.Running"),e[61]=l,e[62]=$):$=e[62];let q;e[63]!==$?(q={label:$,value:"running"},e[63]=$,e[64]=q):q=e[64];let z;e[65]!==l?(z=l("deployment.status.Terminated"),e[65]=l,e[66]=z):z=e[66];let Q;e[67]!==z?(Q={label:z,value:"finished"},e[67]=z,e[68]=Q):Q=e[68];let G;e[69]!==q||e[70]!==Q?(G=[q,Q],e[69]=q,e[70]=Q,e[71]=G):G=e[71];let H;e[72]!==s.statusCategory||e[73]!==U||e[74]!==G?(H=n.jsx(zl,{value:Tl,onChange:U,options:G}),e[72]=s.statusCategory,e[73]=U,e[74]=G,e[75]=H):H=e[75];const tl=s.filter??void 0;let J;e[76]!==f||e[77]!==y?(J=t=>{f({filter:t??null}),y({current:1})},e[76]=f,e[77]=y,e[78]=J):J=e[78];let W;e[79]!==al||e[80]!==tl||e[81]!==J?(W=n.jsx(tn,{filterProperties:al,value:tl,onChange:J}),e[79]=al,e[80]=tl,e[81]=J,e[82]=W):W=e[82];let Y;e[83]!==H||e[84]!==W?(Y=n.jsxs(Ie,{gap:"sm",align:"start",wrap:"wrap",style:qe,children:[H,W]}),e[83]=H,e[84]=W,e[85]=Y):Y=e[85];let X;e[86]!==he||e[87]!==x||e[88]!==k?(X=n.jsx(Ql,{settingId:"deployment-list",defaultAutoUpdateDelay:15e3,value:he,onChange:k,loading:x}),e[86]=he,e[87]=x,e[88]=k,e[89]=X):X=e[89];let Z;e[90]!==l?(Z=l("deployment.CreateDeployment"),e[90]=l,e[91]=Z):Z=e[91];let ee;e[92]!==L||e[93]!==Z?(ee=n.jsx(Gl,{type:"primary",onClick:L,children:Z}),e[92]=L,e[93]=Z,e[94]=ee):ee=e[94];let le;e[95]!==X||e[96]!==ee?(le=n.jsxs(Ie,{gap:"xs",align:"center",children:[X,ee]}),e[95]=X,e[96]=ee,e[97]=le):le=e[97];let ne;e[98]!==Y||e[99]!==le?(ne=n.jsxs(Ie,{justify:"between",wrap:"wrap",gap:"sm",children:[Y,le]}),e[98]=Y,e[99]=le,e[100]=ne):ne=e[100];let ae;e[101]!==f?(ae=t=>{f({order:t??null})},e[101]=f,e[102]=ae):ae=e[102];let te;e[103]!==y?(te=(t,b)=>{y({current:t,pageSize:b})},e[103]=y,e[104]=te):te=e[104];let ie;e[105]!==te||e[106]!==N.current||e[107]!==N.pageSize||e[108]!==A?(ie={current:N.current,pageSize:N.pageSize,total:A,onChange:te},e[105]=te,e[106]=N.current,e[107]=N.pageSize,e[108]=A,e[109]=ie):ie=e[109];let se;e[110]!==Je||e[111]!==We?(se={columnOverrides:Je,onColumnOverridesChange:We},e[110]=Je,e[111]=We,e[112]=se):se=e[112];let re;e[113]!==o||e[114]!==m||e[115]!==l||e[116]!==d?(re=t=>{const b=["name","currentRevisionNumber","status","replicaSummary","model","createdAt","id","endpointUrl","tags","updatedAt","openToPublic","resourceGroup"],Il=new Set(["name","currentRevisionNumber","status","replicaSummary","model","createdAt"]);return t.filter(g=>b.includes(g.key)).map(g=>{let Te=g;return g.key==="name"?Te={...g,render:(Fl,F)=>{var v,He;const S=Xl((v=F.metadata)==null?void 0:v.status);return n.jsx(Hl,{title:((He=F.metadata)==null?void 0:He.name)??"-",onTitleClick:()=>d(`${o("deployments")}/${Kl(F.id)}`),copyable:!0,showActions:"always",actions:[{key:"edit",title:l("deployment.EditDeployment"),icon:n.jsx(sn,{}),disabled:S,onClick:()=>Ke(F.id)},{key:"delete",title:l("deployment.DeleteDeployment"),icon:n.jsx(Jl,{}),type:"danger",disabled:S,onClick:()=>T(F.id)}]})}}:g.key==="currentRevisionNumber"?Te={...g,render:(Fl,F)=>{const S=m.find(He=>He.id===F.id),v=S==null?void 0:S.currentRevision;return(v==null?void 0:v.revisionNumber)==null?n.jsx(cl.Text,{type:"secondary",children:"-"}):n.jsx(cl.Link,{onClick:()=>De(v),children:`#${v.revisionNumber}`})}}:g.key==="tags"&&(Te={...g,render:(Fl,F)=>n.jsx(Zl,{metadataFrgmt:F.metadata,stopRowClick:!0,onTagClick:S=>{d({pathname:o("deployments"),search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:S}})}).toString()})},fallback:n.jsx(cl.Text,{type:"secondary",children:"-"})})}),g.key==="name"?Te:{...Te,defaultHidden:!Il.has(g.key)}})},e[113]=o,e[114]=m,e[115]=l,e[116]=d,e[117]=re):re=e[117];let oe;e[118]!==m||e[119]!==x||e[120]!==s.order||e[121]!==ae||e[122]!==ie||e[123]!==se||e[124]!==re?(oe=n.jsx(an,{deploymentsFrgmt:m,loading:x,order:s.order,onChangeOrder:ae,pagination:ie,tableSettings:se,customizeColumns:re}),e[118]=m,e[119]=x,e[120]=s.order,e[121]=ae,e[122]=ie,e[123]=se,e[124]=re,e[125]=oe):oe=e[125];let ue;e[126]!==ne||e[127]!==oe?(ue=n.jsxs(Ie,{direction:"column",align:"stretch",gap:"sm",children:[ne,oe]}),e[126]=ne,e[127]=oe,e[128]=ue):ue=e[128];const il=c||!!Le,sl=Le??null;let de;e[129]!==C||e[130]!==k?(de=t=>{C(),Ke(null),t&&k()},e[129]=C,e[130]=k,e[131]=de):de=e[131];let ce;e[132]!==il||e[133]!==sl||e[134]!==de?(ce=n.jsx(Dl,{children:n.jsx(Wl,{open:il,deploymentFrgmt:sl,onRequestClose:de})}),e[132]=il,e[133]=sl,e[134]=de,e[135]=ce):ce=e[135];const rl=!!i;let me;e[136]!==l?(me=l("deployment.DeleteDeployment"),e[136]=l,e[137]=me):me=e[137];let ge;e[138]!==l?(ge=l("deployment.Deployment"),e[138]=l,e[139]=ge):ge=e[139];let pe;e[140]!==i?(pe=i?[{key:i.id,label:((yl=i.metadata)==null?void 0:yl.name)??""}]:[],e[140]=i,e[141]=pe):pe=e[141];const ol=((fl=i==null?void 0:i.metadata)==null?void 0:fl.name)??"",ul=((kl=i==null?void 0:i.metadata)==null?void 0:kl.name)??"";let ye;e[142]!==ul?(ye={placeholder:ul},e[142]=ul,e[143]=ye):ye=e[143];let fe;e[144]!==nl?(fe={loading:nl},e[144]=nl,e[145]=fe):fe=e[145];let ke;e[146]!==ll||e[147]!==i||e[148]!==u||e[149]!==r||e[150]!==l||e[151]!==k?(ke=()=>{i&&ll({variables:{input:{id:Kl(i.id)??i.id}},onCompleted:(t,b)=>{if(b&&b.length>0){u.error("Failed to delete deployment",b),r.error(l("deployment.FailedToDeleteDeployment"));return}r.success(l("deployment.DeploymentDeleted")),T(null),k()},onError:t=>{u.error("Failed to delete deployment",t),r.error(l("deployment.FailedToDeleteDeployment"))}})},e[146]=ll,e[147]=i,e[148]=u,e[149]=r,e[150]=l,e[151]=k,e[152]=ke):ke=e[152];let ze;e[153]===Symbol.for("react.memo_cache_sentinel")?(ze=()=>T(null),e[153]=ze):ze=e[153];let Fe;e[154]!==rl||e[155]!==me||e[156]!==ge||e[157]!==pe||e[158]!==ol||e[159]!==ye||e[160]!==fe||e[161]!==ke?(Fe=n.jsx(Yl,{open:rl,title:me,target:ge,items:pe,confirmText:ol,requireConfirmInput:!0,inputProps:ye,okButtonProps:fe,onOk:ke,onCancel:ze}),e[154]=rl,e[155]=me,e[156]=ge,e[157]=pe,e[158]=ol,e[159]=ye,e[160]=fe,e[161]=ke,e[162]=Fe):Fe=e[162];const dl=!!h;let Qe;e[163]===Symbol.for("react.memo_cache_sentinel")?(Qe=()=>De(null),e[163]=Qe):Qe=e[163];let Se;e[164]!==h||e[165]!==dl?(Se=n.jsx(Dl,{children:n.jsx(en,{open:dl,revisionFrgmt:h,onClose:Qe})}),e[164]=h,e[165]=dl,e[166]=Se):Se=e[166];let Ge;return e[167]!==ue||e[168]!==ce||e[169]!==Fe||e[170]!==Se?(Ge=n.jsxs(n.Fragment,{children:[ue,ce,Fe,Se]}),e[167]=ue,e[168]=ce,e[169]=Fe,e[170]=Se,e[171]=Ge):Ge=e[171],Ge},Fn=()=>{"use memo";const e=hl.c(6),{t:l}=bl();let r;e[0]!==l?(r=l("webui.menu.Deployments"),e[0]=l,e[1]=r):r=e[1];let u;e[2]===Symbol.for("react.memo_cache_sentinel")?(u={body:{paddingTop:0}},e[2]=u):u=e[2];let d;e[3]===Symbol.for("react.memo_cache_sentinel")?(d=n.jsx(ve.Suspense,{fallback:n.jsx(Nl,{active:!0}),children:n.jsx(rn,{})}),e[3]=d):d=e[3];let o;return e[4]!==r?(o=n.jsx(Ie,{direction:"column",align:"stretch",gap:"md",children:n.jsx(Pl,{variant:"borderless",title:r,styles:u,children:d})}),e[4]=r,e[5]=o):o=e[5],o};function on(e){return typeof e=="object"&&e!==null&&!Array.isArray(e)?e:{}}export{Fn as default};
//# sourceMappingURL=DeploymentListPage-BHS-1ElA.js.map
