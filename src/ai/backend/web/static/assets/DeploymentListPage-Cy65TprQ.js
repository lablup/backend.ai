import{c as Tl,u as Nl,h as jl,n as a,v as Bl,x as El,C as Te,z as _l,bb as wl,c0 as Ol,aK as ql,cb as Ul,a as $l,i as Dl,j as zl,k as Ql,g as Gl,l as Hl,d as Wl,b as Jl,t as Yl,m as Xl,r as Il,q as Zl,s as en,aR as ln,T as Al,B as fl,w as nn,L as an,N as hl}from"./index-CwWAznqi.js";import{A as tn}from"./AutoUpdateFetchKeyButton-MZ4HY-Ai.js";import{D as rn,a as sn}from"./DeploymentSettingModal-B8BbcaQs.js";import{u as on}from"./reactPaginationQueryOptions-Bt4rkB5i.js";import{u as un}from"./useCreateActionArrival-B57hH1B2.js";import{r as R,c as dn,k as mn,a as cn}from"./icons-BgdBQS0N.js";import{m as pn}from"./lodash-RhKGq0BF.js";import{B as gn,a as yn}from"./BAIModelDeploymentNodes-BNyQD-Ld.js";import{B as fn}from"./BAIGraphQLPropertyFilter-BwM0Jjll.js";import{i as kn}from"./BAIDeploymentStatusBadge-axTa07mq.js";import{B as Fn}from"./BAINameActionCell-BZc0os_M.js";import{B as Sn}from"./BAIEntityLabelSettingModal-zXhyYD10.js";import{B as bn}from"./BAIDeleteConfirmModal-CUutQ4aO.js";import{t as vn}from"./BAIEntityLabelTokens-BWz7hwXT.js";import"./BAIFetchKeyButton-DApd5OLT.js";import"./useControllableValue-BmgV_ECW.js";import"./ButtonGroup-DPQvGHtt.js";import"./parseCliCommand-DLNI3aPC.js";import"./FolderLink-DaaLvORM.js";import"./BAIVFolderIdenticon-PgyEX4dv.js";import"./SourceCodeView-jXLvuWSO.js";import"./CodeBlock-CV2dJgqa.js";import"./useScrollableArea-Bsuw_xFk.js";import"./BAIId-C7PlhBcJ.js";import"./BAIImageNodeSimpleTagV2-grs0QBeV.js";import"./BAIDoubleToken-DmnYFlRB.js";import"./BAITextHighlighter-9-PRKuKt.js";import"./Token-B6wppFPd.js";import"./useBAIIconPath-kZbqwXZ-.js";import"./BAIResourceNumberWithIcon-jmo0jZh2.js";import"./astryxPlacement-BxR6_qos.js";import"./BAIMetadataList-BYZUwKjA.js";import"./BAIProjectResourceGroupSelect-CKRGsOXh.js";import"./NumberInput-BX3bbN7A.js";import"./NumberInput-BAShrYzU.js";import"./useLocale-tF6sKPhr.js";import"./TagsInput-B_f8kLOn.js";import"./Tokenizer-Czn8bbzO.js";import"./groupItems-BfxkhRY8.js";import"./characters-DWaYg7k3.js";import"./CheckboxInput-Dvbz8RhO.js";import"./BAIBooleanToken-C7s4YZH-.js";import"./BAIEntityLabelCell-DciPKo0X.js";import"./BAITable-BJsxYyy0.js";import"./Table-SIAPvWUk.js";import"./MenuBottomSheetActionList-DfgiyqqP.js";import"./Pagination-cBiGXF8Y.js";import"./BAIPowerSearchAdapters-Cpa0dtdE.js";import"./DateRangeInput-BafIu0I7.js";import"./BottomSheet-C7Cy7dyi.js";import"./astryxTagVariant-CibgwVXb.js";import"./BAIBulkErrorModal-B1rud_RV.js";const xl=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentListPageDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentListPageDeleteMutation",selections:e},params:{cacheID:"4639cd2572faeb586296319d8202e23a",id:null,metadata:{},name:"DeploymentListPageDeleteMutation",operationKind:"mutation",text:`mutation DeploymentListPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}})();xl.hash="867cc2a31d2fc3342a0bafe7502c0483";const Pl=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},b={defaultValue:null,kind:"LocalArgument",name:"offset"},D={defaultValue:null,kind:"LocalArgument",name:"orderBy"},n={defaultValue:null,kind:"LocalArgument",name:"scope"},m=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{kind:"Variable",name:"scope",variableName:"scope"}],d={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"entityId",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},V={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},C={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[t,r,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},Ne={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},T={alias:null,args:null,kind:"ScalarField",name:"fieldId",storageKey:null},N={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},A=[r,N],v={alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},K=[v,N];return{fragment:{argumentDefinitions:[l,e,b,D,n],kind:"Fragment",metadata:null,name:"DeploymentListPageQuery",selections:[{alias:null,args:m,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"scopedDeployments",plural:!1,selections:[d,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,c,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[r,p],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,g,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[n,l,D,e,b],kind:"Operation",name:"DeploymentListPageQuery",selections:[{alias:null,args:m,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"scopedDeployments",plural:!1,selections:[d,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,c,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},r,p,V,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[r],storageKey:null},t],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[d],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,g,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[C,y,Ne,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"subpath",storageKey:null}],storageKey:null},T,V,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:A,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[r,t],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:A,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},N,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[r,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[v],storageKey:null},t],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[y,Ne,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},C],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[t,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageV2TagEntry",kind:"LinkedField",name:"tags",plural:!0,selections:K,storageKey:null},{alias:null,args:null,concreteType:"ImageV2LabelEntry",kind:"LinkedField",name:"labels",plural:!0,selections:K,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[r,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"command",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:[{kind:"Literal",name:"limit",value:100}],concreteType:"EntityLabelConnection",kind:"LinkedField",name:"entityLabels",plural:!1,selections:[{alias:null,args:null,concreteType:"EntityLabelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"EntityLabel",kind:"LinkedField",name:"node",plural:!1,selections:[v,N,t,T],storageKey:null}],storageKey:null}],storageKey:"entityLabels(limit:100)"},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[t,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"841bc8bd58de1a314756d6460574399f",id:null,metadata:{},name:"DeploymentListPageQuery",operationKind:"query",text:`query DeploymentListPageQuery(
  $scope: DeploymentSearchScope!
  $filter: DeploymentFilter
  $orderBy: [DeploymentOrderBy!]
  $limit: Int
  $offset: Int
) {
  scopedDeployments(scope: $scope, filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
    count
    edges {
      node {
        id
        entityId
        ...BAIModelDeploymentNodesFragment
        ...DeploymentSettingModal_deployment
        metadata {
          name
          status
        }
        currentRevision {
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
  creator {
    id
    basicInfo {
      email
      username
      fullName
    }
  }
}

fragment BAIEntityLabelSettingModalFragment on EntityLabelConnection {
  edges {
    node {
      fieldId
      key
      value
      id
    }
  }
}

fragment BAIEntityLabelTokensFragment on EntityLabelConnection {
  edges {
    node {
      key
      value
      id
    }
  }
}

fragment BAIImageNodeSimpleTagV2Fragment on ImageV2 {
  identity {
    canonicalName
    architecture
  }
  metadata {
    tags {
      key
      value
    }
    labels {
      key
      value
    }
  }
}

fragment BAIModelDeploymentNodesFragment on ModelDeployment {
  id
  entityId
  currentRevisionId
  metadata {
    projectId
    domainName
    name
    status
    createdAt
    updatedAt
    resourceGroupName
    projectV2 {
      basicInfo {
        name
      }
      id
    }
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
  currentRevision {
    id
    revisionNumber
    modelMountConfig {
      vfolder {
        id
        name
      }
    }
  }
  entityLabels(limit: 100) {
    ...BAIEntityLabelTokensFragment
    ...BAIEntityLabelSettingModalFragment
  }
  ...BAIDeploymentOwnerInfo_deployment
}

fragment DeploymentRevisionDetail_revision on ModelRevision {
  id
  fieldId
  revisionNumber
  createdAt
  clusterConfig {
    mode
    size
  }
  resourceSlots {
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
    runtimeVariantPresetValues {
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
    subpath
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
  imageV2 {
    id
    identity {
      canonicalName
      architecture
    }
    ...BAIImageNodeSimpleTagV2Fragment
  }
  modelDefinition {
    models {
      name
      modelPath
      service {
        command @since(version: "26.7.0")
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
  entityId
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
`}}})();Pl.hash="c346f5e7a2fa80e887aefb1866aee20c";const Cl=(l,e)=>a.jsxs(Te,{gap:"xxs",align:"center",children:[l,a.jsx(ln,{content:e,children:a.jsx(Al,{color:"placeholder",style:{cursor:"help"},children:a.jsx(dn,{size:"1em"})})})]}),Kn=l=>{"use memo";var bl,vl,Kl,Ll;const e=Tl.c(183),{isCreating:b,onCloseCreate:D}=l,{t:n}=Nl(),{message:m}=wl.useApp(),{logger:d}=Ol(),t=ql(),c=Ul(),[r,p]=R.useState(null),[g,V]=R.useState(null),C=$l("deployment"),[y,Ne]=R.useState(null),[T,N]=R.useState(null);let A;e[0]===Symbol.for("react.memo_cache_sentinel")?(A={current:1,pageSize:10},e[0]=A):A=e[0];const{baiPaginationOption:v,tablePaginationOption:K,setTablePaginationOption:f}=on(A);let Pe,Me;e[1]===Symbol.for("react.memo_cache_sentinel")?(Pe={filter:zl(Ln),order:Dl(yn),statusCategory:Dl(["serving","paused","finished"]).withDefault("serving")},Me={history:"replace"},e[1]=Pe,e[2]=Me):(Pe=e[1],Me=e[2]);const[o,k]=Ql(Pe,Me),[Xe,Ze]=Gl("table_column_overrides.DeploymentListPage"),[Ae,F]=Hl(),[el]=Wl(),x=Jl();let Re;e[3]!==x?(Re=Yl(x),e[3]=x,e[4]=Re):Re=e[4];const Ve=Re;let je;e[5]!==o.order?(je=Xl(o.order),e[5]=o.order,e[6]=je):je=e[6];const ll=je;let Be;e[7]===Symbol.for("react.memo_cache_sentinel")?(Be=["STOPPED"],e[7]=Be):Be=e[7];const kl=Be;let Ee;e[8]!==o.statusCategory?(Ee=o.statusCategory==="finished"?{status:{in:kl}}:{status:{notIn:kl},desiredReplicas:o.statusCategory==="serving"?{greaterThanOrEqual:1}:{equals:0}},e[8]=o.statusCategory,e[9]=Ee):Ee=e[9];const nl=Ee;let _e;e[10]!==x.id?(_e=x.id?{projectId:{equals:x.id}}:{},e[10]=x.id,e[11]=_e):_e=e[11];const al=_e;let j;e[12]!==el.uuid?(j={user:[{value:el.uuid}]},e[12]=el.uuid,e[13]=j):j=e[13];let B;e[14]!==o.filter?(B=o.filter??{},e[14]=o.filter,e[15]=B):B=e[15];let E;e[16]!==al||e[17]!==nl||e[18]!==B?(E={...B,...nl,...al},e[16]=al,e[17]=nl,e[18]=B,e[19]=E):E=e[19];let we;e[20]!==v.limit||e[21]!==v.offset||e[22]!==ll||e[23]!==E||e[24]!==j?(we={scope:j,filter:E,orderBy:ll,limit:v.limit,offset:v.offset},e[20]=v.limit,e[21]=v.offset,e[22]=ll,e[23]=E,e[24]=j,e[25]=we):we=e[25];const Fl=we,Sl=R.useDeferredValue(Fl),xe=R.useDeferredValue(Ae);let Oe;e[26]===Symbol.for("react.memo_cache_sentinel")?(Oe=Pl,e[26]=Oe):Oe=e[26];const tl=xe===en?"store-and-network":"network-only";let qe;e[27]!==xe||e[28]!==tl?(qe={fetchPolicy:tl,fetchKey:xe},e[27]=xe,e[28]=tl,e[29]=qe):qe=e[29];const{scopedDeployments:s}=Il.useLazyLoadQuery(Oe,Sl,qe);let S,I,Ue,_;e[30]!==g||e[31]!==r||e[32]!==(s==null?void 0:s.count)||e[33]!==(s==null?void 0:s.edges)?(S=Zl(pn(s==null?void 0:s.edges,"node")),_=(s==null?void 0:s.count)??0,I=r==null?null:S.find(i=>i.id===r)??null,Ue=g==null?null:S.find(i=>i.id===g)??null,e[30]=g,e[31]=r,e[32]=s==null?void 0:s.count,e[33]=s==null?void 0:s.edges,e[34]=S,e[35]=I,e[36]=Ue,e[37]=_):(S=e[34],I=e[35],Ue=e[36],_=e[37]);const u=Ue,w=Sl!==Fl||xe!==Ae;let $e;e[38]===Symbol.for("react.memo_cache_sentinel")?($e=xl,e[38]=$e):$e=e[38];const[il,rl]=Il.useMutation($e);let O;e[39]!==n?(O=n("deployment.filter.Name"),e[39]=n,e[40]=O):O=e[40];let q;e[41]!==O?(q={key:"name",propertyLabel:O,type:"string"},e[41]=O,e[42]=q):q=e[42];let U;e[43]!==n?(U=n("deployment.filter.EndpointUrl"),e[43]=n,e[44]=U):U=e[44];let $;e[45]!==U?($={key:"endpointUrl",propertyLabel:U,type:"string"},e[45]=U,e[46]=$):$=e[46];let z;e[47]!==n?(z=n("deployment.filter.OpenToPublic"),e[47]=n,e[48]=z):z=e[48];let Q;e[49]!==z?(Q={key:"openToPublic",propertyLabel:z,type:"boolean"},e[49]=z,e[50]=Q):Q=e[50];let G;e[51]!==C||e[52]!==n?(G=C?[{key:"labels.some.key",propertyLabel:n("entityLabel.LabelKey"),type:"string"},{key:"labels.some.value",propertyLabel:n("entityLabel.LabelValue"),type:"string"}]:[],e[51]=C,e[52]=n,e[53]=G):G=e[53];let ze;e[54]!==q||e[55]!==$||e[56]!==Q||e[57]!==G?(ze=[q,$,Q,...G],e[54]=q,e[55]=$,e[56]=Q,e[57]=G,e[58]=ze):ze=e[58];const sl=ze;let Qe;e[59]===Symbol.for("react.memo_cache_sentinel")?(Qe={flexShrink:1},e[59]=Qe):Qe=e[59];const Ml=o.statusCategory;let H;e[60]!==k||e[61]!==f?(H=i=>{k({statusCategory:i}),f({current:1})},e[60]=k,e[61]=f,e[62]=H):H=e[62];let W;e[63]!==n?(W=Cl(n("deployment.Serving"),n("deployment.ServingTooltip")),e[63]=n,e[64]=W):W=e[64];let J;e[65]!==W?(J=a.jsx(fl,{value:"serving",label:W}),e[65]=W,e[66]=J):J=e[66];let Y;e[67]!==n?(Y=Cl(n("deployment.Paused"),n("deployment.PausedTooltip")),e[67]=n,e[68]=Y):Y=e[68];let X;e[69]!==Y?(X=a.jsx(fl,{value:"paused",label:Y}),e[69]=Y,e[70]=X):X=e[70];let Z;e[71]!==n?(Z=n("deployment.status.Terminated"),e[71]=n,e[72]=Z):Z=e[72];let ee;e[73]!==Z?(ee=a.jsx(fl,{value:"finished",label:Z}),e[73]=Z,e[74]=ee):ee=e[74];let le;e[75]!==o.statusCategory||e[76]!==H||e[77]!==J||e[78]!==X||e[79]!==ee?(le=a.jsxs(nn,{value:Ml,onChange:H,children:[J,X,ee]}),e[75]=o.statusCategory,e[76]=H,e[77]=J,e[78]=X,e[79]=ee,e[80]=le):le=e[80];const ol=o.filter??void 0;let ne;e[81]!==k||e[82]!==f?(ne=i=>{k({filter:i??null}),f({current:1})},e[81]=k,e[82]=f,e[83]=ne):ne=e[83];let ae;e[84]!==sl||e[85]!==ol||e[86]!==ne?(ae=a.jsx(fn,{filterProperties:sl,value:ol,onChange:ne}),e[84]=sl,e[85]=ol,e[86]=ne,e[87]=ae):ae=e[87];let te;e[88]!==le||e[89]!==ae?(te=a.jsxs(Te,{gap:"sm",align:"start",wrap:"wrap",style:Qe,children:[le,ae]}),e[88]=le,e[89]=ae,e[90]=te):te=e[90];let ie;e[91]!==Ae||e[92]!==w||e[93]!==F?(ie=a.jsx(Te,{gap:"xs",align:"center",children:a.jsx(tn,{settingId:"deployment-list",defaultAutoUpdateDelay:15e3,value:Ae,onChange:F,loading:w})}),e[91]=Ae,e[92]=w,e[93]=F,e[94]=ie):ie=e[94];let re;e[95]!==te||e[96]!==ie?(re=a.jsxs(Te,{justify:"between",wrap:"wrap",gap:"sm",children:[te,ie]}),e[95]=te,e[96]=ie,e[97]=re):re=e[97];const ul=C?Ne:void 0;let se;e[98]!==k||e[99]!==f?(se=i=>{k({filter:vn(i)}),f({current:1})},e[98]=k,e[99]=f,e[100]=se):se=e[100];let oe;e[101]!==k?(oe=i=>{k({order:i??null})},e[101]=k,e[102]=oe):oe=e[102];let ue;e[103]!==f?(ue=(i,P)=>{f({current:i,pageSize:P})},e[103]=f,e[104]=ue):ue=e[104];let de;e[105]!==ue||e[106]!==K.current||e[107]!==K.pageSize||e[108]!==_?(de={current:K.current,pageSize:K.pageSize,total:_,onChange:ue},e[105]=ue,e[106]=K.current,e[107]=K.pageSize,e[108]=_,e[109]=de):de=e[109];let me;e[110]!==Xe||e[111]!==Ze?(me={columnOverrides:Xe,onColumnOverridesChange:Ze},e[110]=Xe,e[111]=Ze,e[112]=me):me=e[112];let ce;e[113]!==c||e[114]!==S||e[115]!==n||e[116]!==t?(ce=i=>{const P=["name","currentRevisionNumber","status","labels","replicaSummary","model","createdAt","id","endpointUrl","updatedAt","openToPublic","resourceGroup"],Rl=new Set(["name","currentRevisionNumber","status","replicaSummary","model","createdAt"]);return i.filter(L=>P.includes(L.key)).map(L=>{let Je=L;return L.key==="name"?Je={...L,render:(Vl,M)=>{var h,Ye;const Ce=kn((h=M.metadata)==null?void 0:h.status);return a.jsx(Fn,{title:((Ye=M.metadata)==null?void 0:Ye.name)??"-",onTitleClick:()=>t(`${c("deployments")}/${M.entityId}`),copyable:!0,showActions:"always",actions:[{key:"edit",title:n("deployment.EditDeployment"),icon:a.jsx(mn,{}),disabled:Ce,onClick:()=>p(M.id)},{key:"delete",title:n("deployment.DeleteDeployment"),icon:a.jsx(cn,{size:"1em"}),type:"danger",disabled:Ce,onClick:()=>V(M.id)}]})}}:L.key==="currentRevisionNumber"&&(Je={...L,render:(Vl,M)=>{const Ce=S.find(Ye=>Ye.id===M.id),h=Ce==null?void 0:Ce.currentRevision;return(h==null?void 0:h.revisionNumber)==null?a.jsx(Al,{color:"secondary",children:"-"}):a.jsx(an,{onClick:()=>N(h),children:`#${h.revisionNumber}`})}}),L.key==="name"?Je:{...Je,defaultHidden:!Rl.has(L.key)}})},e[113]=c,e[114]=S,e[115]=n,e[116]=t,e[117]=ce):ce=e[117];let pe;e[118]!==S||e[119]!==w||e[120]!==o.order||e[121]!==ul||e[122]!==se||e[123]!==oe||e[124]!==de||e[125]!==me||e[126]!==ce?(pe=a.jsx(gn,{onEditLabels:ul,onLabelClick:se,deploymentsFrgmt:S,loading:w,order:o.order,onChangeOrder:oe,pagination:de,tableSettings:me,customizeColumns:ce}),e[118]=S,e[119]=w,e[120]=o.order,e[121]=ul,e[122]=se,e[123]=oe,e[124]=de,e[125]=me,e[126]=ce,e[127]=pe):pe=e[127];let ge;e[128]!==re||e[129]!==pe?(ge=a.jsxs(Te,{direction:"column",align:"stretch",gap:"sm",children:[re,pe]}),e[128]=re,e[129]=pe,e[130]=ge):ge=e[130];const dl=!!y;let ye;e[131]!==y?(ye=y?[{entityId:y.entityId,name:((bl=y.metadata)==null?void 0:bl.name)??void 0}]:[],e[131]=y,e[132]=ye):ye=e[132];const ml=y==null?void 0:y.entityLabels;let fe;e[133]!==F?(fe=i=>{Ne(null),i&&F()},e[133]=F,e[134]=fe):fe=e[134];let ke;e[135]!==dl||e[136]!==ye||e[137]!==ml||e[138]!==fe?(ke=a.jsx(Sn,{open:dl,entityType:"deployment",targets:ye,entityLabelsFrgmt:ml,onRequestClose:fe}),e[135]=dl,e[136]=ye,e[137]=ml,e[138]=fe,e[139]=ke):ke=e[139];let Fe;e[140]!==I||e[141]!==b||e[142]!==D||e[143]!==Ve||e[144]!==F?(Fe=Ve!=null&&a.jsx(hl,{children:a.jsx(rn,{open:b||!!I,deploymentFrgmt:I??null,project:Ve,onRequestClose:i=>{D(),p(null),i&&!I&&F()}})}),e[140]=I,e[141]=b,e[142]=D,e[143]=Ve,e[144]=F,e[145]=Fe):Fe=e[145];const cl=!!u;let Se;e[146]!==n?(Se=n("deployment.DeleteDeployment"),e[146]=n,e[147]=Se):Se=e[147];let be;e[148]!==n?(be=n("deployment.Deployment"),e[148]=n,e[149]=be):be=e[149];let ve;e[150]!==u?(ve=u?[{key:u.id,label:((vl=u.metadata)==null?void 0:vl.name)??""}]:[],e[150]=u,e[151]=ve):ve=e[151];const pl=((Kl=u==null?void 0:u.metadata)==null?void 0:Kl.name)??"",gl=((Ll=u==null?void 0:u.metadata)==null?void 0:Ll.name)??"";let Ke;e[152]!==gl?(Ke={placeholder:gl},e[152]=gl,e[153]=Ke):Ke=e[153];let Le;e[154]!==rl?(Le={loading:rl},e[154]=rl,e[155]=Le):Le=e[155];let De;e[156]!==il||e[157]!==u||e[158]!==d||e[159]!==m||e[160]!==n||e[161]!==F?(De=()=>{u&&il({variables:{input:{id:u.entityId}},onCompleted:(i,P)=>{if(P&&P.length>0){d.error("Failed to delete deployment",P),m.error(n("deployment.FailedToDeleteDeployment"));return}m.success(n("deployment.DeploymentDeleted")),V(null),F()},onError:i=>{d.error("Failed to delete deployment",i),m.error(n("deployment.FailedToDeleteDeployment"))}})},e[156]=il,e[157]=u,e[158]=d,e[159]=m,e[160]=n,e[161]=F,e[162]=De):De=e[162];let Ge;e[163]===Symbol.for("react.memo_cache_sentinel")?(Ge=()=>V(null),e[163]=Ge):Ge=e[163];let Ie;e[164]!==cl||e[165]!==Se||e[166]!==be||e[167]!==ve||e[168]!==pl||e[169]!==Ke||e[170]!==Le||e[171]!==De?(Ie=a.jsx(bn,{open:cl,title:Se,target:be,items:ve,confirmText:pl,requireConfirmInput:!0,inputProps:Ke,okButtonProps:Le,onOk:De,onCancel:Ge}),e[164]=cl,e[165]=Se,e[166]=be,e[167]=ve,e[168]=pl,e[169]=Ke,e[170]=Le,e[171]=De,e[172]=Ie):Ie=e[172];const yl=!!T;let He;e[173]===Symbol.for("react.memo_cache_sentinel")?(He=()=>N(null),e[173]=He):He=e[173];let he;e[174]!==T||e[175]!==yl?(he=a.jsx(hl,{children:a.jsx(sn,{open:yl,revisionFrgmt:T,onClose:He})}),e[174]=T,e[175]=yl,e[176]=he):he=e[176];let We;return e[177]!==ge||e[178]!==ke||e[179]!==Fe||e[180]!==Ie||e[181]!==he?(We=a.jsxs(a.Fragment,{children:[ge,ke,Fe,Ie,he]}),e[177]=ge,e[178]=ke,e[179]=Fe,e[180]=Ie,e[181]=he,e[182]=We):We=e[182],We},Ka=()=>{"use memo";const l=Tl.c(15),{t:e}=Nl(),[b,D]=jl(!1),{setLeft:n,setRight:m}=D;un(m);let d;l[0]!==e?(d=e("webui.menu.Deployments"),l[0]=e,l[1]=d):d=l[1];let t;l[2]!==e?(t=e("deployment.CreateDeployment"),l[2]=e,l[3]=t):t=l[3];let c;l[4]!==m||l[5]!==t?(c=a.jsx(Bl,{variant:"primary",label:t,onClick:m}),l[4]=m,l[5]=t,l[6]=c):c=l[6];let r;l[7]===Symbol.for("react.memo_cache_sentinel")?(r=a.jsx(El,{}),l[7]=r):r=l[7];let p;l[8]!==n||l[9]!==b?(p=a.jsx(R.Suspense,{fallback:r,children:a.jsx(Kn,{isCreating:b,onCloseCreate:n})}),l[8]=n,l[9]=b,l[10]=p):p=l[10];let g;return l[11]!==d||l[12]!==c||l[13]!==p?(g=a.jsx(Te,{direction:"column",align:"stretch",gap:"md",children:a.jsx(_l,{variant:"borderless",title:d,extra:c,children:p})}),l[11]=d,l[12]=c,l[13]=p,l[14]=g):g=l[14],g};function Ln(l){return typeof l=="object"&&l!==null&&!Array.isArray(l)?l:{}}export{Ka as default};
//# sourceMappingURL=DeploymentListPage-Cy65TprQ.js.map
