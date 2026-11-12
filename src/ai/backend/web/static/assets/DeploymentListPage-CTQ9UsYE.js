import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{S as t,Zn as n,f as r}from"./icons-Btg1s2wy.js";import{t as i}from"./compiler-runtime-CZQb2eIb.js";import{ot as a,vt as o}from"./lodash-ClfL87UH.js";/* empty css            */import{t as s}from"./jsx-runtime-BapUIyWk.js";import{R as c}from"./usePressFeedback-BIoIGSxE.js";import{O as l,at as u,d}from"./DefaultProviders-BFjPhnQa.js";import{t as f}from"./Button-BKkkrlg5.js";import{r as ee}from"./Skeleton-D35z7Ria.js";import{t as p}from"./BAIFlex-BElkJeHW.js";import{t as te}from"./app-shim-DTEBzR8d.js";import{G as ne,d as re}from"./helper-BWFKT_2Y.js";import{r as ie}from"./hooks-UUY7pxyu.js";import{t as m}from"./react-relay-BfoHYpUf.js";import{t as ae}from"./useBAILogger-CRaS0DnM.js";import{t as h}from"./useToggle-CAWNf18k.js";import{u as oe}from"./helper-DF1Eunoe.js";import{t as se}from"./BAIGraphQLPropertyFilter-CNTUQIkF.js";import{t as ce}from"./BAIUnmountAfterClose-Cxr4Dp_U.js";import{t as g}from"./BAISkeleton-MIjJv1Hr.js";import{t as le}from"./BAIDeleteConfirmModal-CwJ76ZY7.js";import{i as ue,t as de}from"./DeploymentSettingModal-BYp0LIhY.js";import{t as fe}from"./BAINameActionCell-BaFf27s9.js";import{t as pe}from"./BAIEntityLabelSettingModal-BzN4qIYx.js";import{i as me}from"./BAIEntityLabelCell-DOyaclRH.js";import{r as he,t as ge}from"./BAIModelDeploymentNodes-bPs9qaCp.js";import{i as _e,n as ve,o as ye}from"./dist-C3M-rFln.js";import{t as be}from"./useCurrentProject-BaleCvMA.js";import{o as xe}from"./useRouteScope-Dgi-LDmN.js";import{ht as Se,pt as Ce,t as we}from"./index-49VU5B_r.js";import{t as Te}from"./AutoUpdateFetchKeyButton-C-RHyKup.js";import{n as Ee}from"./reactPaginationQueryOptions-DUCwh22X.js";import{n as De}from"./useCreateActionArrival-CjxWphnh.js";import{n as Oe,r as ke,t as Ae}from"./DeploymentStatusCategoryControl-Ng0rAYHN.js";import{t as je}from"./DeploymentRevisionDetailDrawer-eT3h35BX.js";import{n as Me}from"./WebMCPDeploymentTools-Fx4eckPD.js";var Ne=i(),Pe=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`filter`},t={defaultValue:null,kind:`LocalArgument`,name:`limit`},n={defaultValue:null,kind:`LocalArgument`,name:`offset`},r={defaultValue:null,kind:`LocalArgument`,name:`orderBy`},i={defaultValue:null,kind:`LocalArgument`,name:`scope`},a=[{kind:`Variable`,name:`filter`,variableName:`filter`},{kind:`Variable`,name:`limit`,variableName:`limit`},{kind:`Variable`,name:`offset`,variableName:`offset`},{kind:`Variable`,name:`orderBy`,variableName:`orderBy`},{kind:`Variable`,name:`scope`,variableName:`scope`}],o={alias:null,args:null,kind:`ScalarField`,name:`count`,storageKey:null},s={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},c={alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},l={alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},u={alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null},d={alias:null,args:null,kind:`ScalarField`,name:`revisionNumber`,storageKey:null},f={alias:null,args:null,kind:`ScalarField`,name:`createdAt`,storageKey:null},ee={alias:null,args:null,concreteType:`VirtualFolderNode`,kind:`LinkedField`,name:`vfolder`,plural:!1,selections:[s,l,{alias:null,args:null,kind:`ScalarField`,name:`row_id`,storageKey:null}],storageKey:null},p={alias:null,args:null,kind:`ScalarField`,name:`vfolderId`,storageKey:null},te={alias:null,args:null,kind:`ScalarField`,name:`mountDestination`,storageKey:null},ne={alias:null,args:null,kind:`ScalarField`,name:`fieldId`,storageKey:null},re={alias:null,args:null,kind:`ScalarField`,name:`value`,storageKey:null},ie=[l,re],m={alias:null,args:null,kind:`ScalarField`,name:`key`,storageKey:null},ae=[m,re];return{fragment:{argumentDefinitions:[e,t,n,r,i],kind:`Fragment`,metadata:null,name:`DeploymentListPageQuery`,selections:[{alias:null,args:a,concreteType:`ModelDeploymentConnection`,kind:`LinkedField`,name:`scopedDeployments`,plural:!1,selections:[o,{alias:null,args:null,concreteType:`ModelDeploymentEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ModelDeployment`,kind:`LinkedField`,name:`node`,plural:!1,selections:[s,c,{args:null,kind:`FragmentSpread`,name:`BAIModelDeploymentNodesFragment`},{args:null,kind:`FragmentSpread`,name:`DeploymentSettingModal_deployment`},{args:null,kind:`FragmentSpread`,name:`WebMCPDeploymentTools_deployments`},{alias:null,args:null,concreteType:`ModelDeploymentMetadata`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:[l,u],storageKey:null},{alias:null,args:null,concreteType:`ModelRevision`,kind:`LinkedField`,name:`currentRevision`,plural:!1,selections:[s,d,{args:null,kind:`FragmentSpread`,name:`DeploymentRevisionDetail_revision`}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[i,e,r,t,n],kind:`Operation`,name:`DeploymentListPageQuery`,selections:[{alias:null,args:a,concreteType:`ModelDeploymentConnection`,kind:`LinkedField`,name:`scopedDeployments`,plural:!1,selections:[o,{alias:null,args:null,concreteType:`ModelDeploymentEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ModelDeployment`,kind:`LinkedField`,name:`node`,plural:!1,selections:[s,c,{alias:null,args:null,kind:`ScalarField`,name:`currentRevisionId`,storageKey:null},{alias:null,args:null,concreteType:`ModelDeploymentMetadata`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`projectId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`domainName`,storageKey:null},l,u,f,{alias:null,args:null,kind:`ScalarField`,name:`updatedAt`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`resourceGroupName`,storageKey:null},{alias:null,args:null,concreteType:`ProjectV2`,kind:`LinkedField`,name:`projectV2`,plural:!1,selections:[{alias:null,args:null,concreteType:`ProjectBasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:[l],storageKey:null},s],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`tags`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ModelDeploymentNetworkAccess`,kind:`LinkedField`,name:`networkAccess`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`endpointUrl`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`preferredDomainName`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`openToPublic`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`DeploymentStrategy`,kind:`LinkedField`,name:`defaultDeploymentStrategy`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`type`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ReplicaState`,kind:`LinkedField`,name:`replicaState`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`replicaCount`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`desiredReplicaCount`,storageKey:null}],storageKey:null},{alias:`runningReplicas`,args:[{kind:`Literal`,name:`filter`,value:{status:{equals:`RUNNING`}}}],concreteType:`ModelReplicaConnection`,kind:`LinkedField`,name:`replicas`,plural:!1,selections:[o],storageKey:`replicas(filter:{"status":{"equals":"RUNNING"}})`},{alias:null,args:null,concreteType:`ModelRevision`,kind:`LinkedField`,name:`currentRevision`,plural:!1,selections:[s,d,{alias:null,args:null,concreteType:`ModelMountConfig`,kind:`LinkedField`,name:`modelMountConfig`,plural:!1,selections:[ee,p,te,{alias:null,args:null,kind:`ScalarField`,name:`definitionPath`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`subpath`,storageKey:null}],storageKey:null},ne,f,{alias:null,args:null,concreteType:`ClusterConfig`,kind:`LinkedField`,name:`clusterConfig`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`mode`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`size`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`AllocatedResourceSlot`,kind:`LinkedField`,name:`resourceSlots`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`slotName`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`quantity`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ResourceConfig`,kind:`LinkedField`,name:`resourceConfig`,plural:!1,selections:[{alias:null,args:null,concreteType:`ResourceOpts`,kind:`LinkedField`,name:`resourceOpts`,plural:!1,selections:[{alias:null,args:null,concreteType:`ResourceOptsEntry`,kind:`LinkedField`,name:`entries`,plural:!0,selections:ie,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ModelRuntimeConfig`,kind:`LinkedField`,name:`modelRuntimeConfig`,plural:!1,selections:[{alias:null,args:null,concreteType:`RuntimeVariant`,kind:`LinkedField`,name:`runtimeVariant`,plural:!1,selections:[l,s],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`inferenceRuntimeConfig`,storageKey:null},{alias:null,args:null,concreteType:`EnvironmentVariables`,kind:`LinkedField`,name:`environ`,plural:!1,selections:[{alias:null,args:null,concreteType:`EnvironmentVariableEntry`,kind:`LinkedField`,name:`entries`,plural:!0,selections:ie,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`RuntimeVariantPresetValue`,kind:`LinkedField`,name:`runtimeVariantPresetValues`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`presetId`,storageKey:null},re,{alias:null,args:null,concreteType:`RuntimeVariantPreset`,kind:`LinkedField`,name:`preset`,plural:!1,selections:[l,{alias:null,args:null,kind:`ScalarField`,name:`displayName`,storageKey:null},{alias:null,args:null,concreteType:`PresetTargetSpec`,kind:`LinkedField`,name:`targetSpec`,plural:!1,selections:[m],storageKey:null},s],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ExtraVFolderMountInfo`,kind:`LinkedField`,name:`extraMounts`,plural:!0,selections:[p,te,{alias:null,args:null,kind:`ScalarField`,name:`mountPerm`,storageKey:null},ee],storageKey:null},{alias:null,args:null,concreteType:`ImageV2`,kind:`LinkedField`,name:`imageV2`,plural:!1,selections:[s,{alias:null,args:null,concreteType:`ImageV2IdentityInfo`,kind:`LinkedField`,name:`identity`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`canonicalName`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`architecture`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ImageV2MetadataInfo`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:[{alias:null,args:null,concreteType:`ImageV2TagEntry`,kind:`LinkedField`,name:`tags`,plural:!0,selections:ae,storageKey:null},{alias:null,args:null,concreteType:`ImageV2LabelEntry`,kind:`LinkedField`,name:`labels`,plural:!0,selections:ae,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ModelDefinition`,kind:`LinkedField`,name:`modelDefinition`,plural:!1,selections:[{alias:null,args:null,concreteType:`ModelConfig`,kind:`LinkedField`,name:`models`,plural:!0,selections:[l,{alias:null,args:null,kind:`ScalarField`,name:`modelPath`,storageKey:null},{alias:null,args:null,concreteType:`ModelServiceConfig`,kind:`LinkedField`,name:`service`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`command`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`startCommand`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`shell`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`port`,storageKey:null},{alias:null,args:null,concreteType:`PreStartAction`,kind:`LinkedField`,name:`preStartActions`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`action`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`args`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ModelHealthCheck`,kind:`LinkedField`,name:`healthCheck`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`path`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`initialDelay`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`maxRetries`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`interval`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`maxWaitTime`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`expectedStatusCode`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:[{kind:`Literal`,name:`limit`,value:100}],concreteType:`EntityLabelConnection`,kind:`LinkedField`,name:`entityLabels`,plural:!1,selections:[{alias:null,args:null,concreteType:`EntityLabelEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`EntityLabel`,kind:`LinkedField`,name:`node`,plural:!1,selections:[m,re,s,ne],storageKey:null}],storageKey:null}],storageKey:`entityLabels(limit:100)`},{alias:null,args:null,concreteType:`UserV2`,kind:`LinkedField`,name:`creator`,plural:!1,selections:[s,{alias:null,args:null,concreteType:`UserV2BasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`email`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`username`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`fullName`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:`6235c334e7bc8cdeb1b618cc542bf143`,id:null,metadata:{},name:`DeploymentListPageQuery`,operationKind:`query`,text:`query DeploymentListPageQuery(
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
        ...WebMCPDeploymentTools_deployments
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
    replicaCount
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
    replicaCount
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

fragment WebMCPDeploymentTools_deployments on ModelDeployment {
  id
  metadata {
    name
    status
    createdAt
    updatedAt
    resourceGroupName
  }
  networkAccess {
    endpointUrl
    openToPublic
  }
  replicaState {
    desiredReplicaCount
  }
  runningReplicas: replicas(filter: {status: {equals: RUNNING}}) {
    count
  }
  currentRevision {
    revisionNumber
    modelMountConfig {
      vfolder {
        name
        id
      }
    }
    id
  }
}
`}}})();Pe.hash=`857549ed5e47533c78d5fbbe3571740d`;var Fe=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`input`}],t=[{alias:null,args:[{kind:`Variable`,name:`input`,variableName:`input`}],concreteType:`DeleteDeploymentPayload`,kind:`LinkedField`,name:`deleteModelDeployment`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`DeploymentListPageDeleteMutation`,selections:t,type:`Mutation`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`DeploymentListPageDeleteMutation`,selections:t},params:{cacheID:`4639cd2572faeb586296319d8202e23a`,id:null,metadata:{},name:`DeploymentListPageDeleteMutation`,operationKind:`mutation`,text:`mutation DeploymentListPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}})();Fe.hash=`867cc2a31d2fc3342a0bafe7502c0483`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var _=e(n(),1),Ie=m(),v=s(),Le=e=>{"use memo";var n,i;let s=(0,Ne.c)(181),{isCreating:f,onCloseCreate:m}=e,{t:h}=ee(),{message:g}=te.useApp(),{logger:Se}=ae(),De=ne(),Le=xe(),[Re,Be]=(0,_.useState)(null),[Ve,He]=(0,_.useState)(null),Ue=Ce(`deployment`),[y,We]=(0,_.useState)(null),[Ge,Ke]=(0,_.useState)(null),qe;s[0]===Symbol.for(`react.memo_cache_sentinel`)?(qe={current:1,pageSize:10},s[0]=qe):qe=s[0];let{baiPaginationOption:b,tablePaginationOption:x,setTablePaginationOption:S}=Ee(qe),Je,Ye;s[1]===Symbol.for(`react.memo_cache_sentinel`)?(Je={filter:ve(ze),order:_e(he),statusCategory:_e(Ae).withDefault(`serving`)},Ye={history:`replace`},s[1]=Je,s[2]=Ye):(Je=s[1],Ye=s[2]);let[C,w]=ye(Je,Ye),[T,Xe]=l(`table_column_overrides.DeploymentListPage`),[Ze,E]=ie(),[Qe]=d(),D=be(),$e;s[3]===D?$e=s[4]:($e=we(D),s[3]=D,s[4]=$e);let et=$e,tt;s[5]===C.order?tt=s[6]:(tt=re(C.order),s[5]=C.order,s[6]=tt);let nt=tt,rt;s[7]===C.statusCategory?rt=s[8]:(rt=ke(C.statusCategory),s[7]=C.statusCategory,s[8]=rt);let it=rt,at;s[9]===D.id?at=s[10]:(at=D.id?{projectId:{equals:D.id}}:{},s[9]=D.id,s[10]=at);let ot=at,O;s[11]===Qe.uuid?O=s[12]:(O={user:[{value:Qe.uuid}]},s[11]=Qe.uuid,s[12]=O);let k;s[13]===C.filter?k=s[14]:(k=C.filter??{},s[13]=C.filter,s[14]=k);let A;s[15]!==ot||s[16]!==it||s[17]!==k?(A={...k,...it,...ot},s[15]=ot,s[16]=it,s[17]=k,s[18]=A):A=s[18];let st;s[19]!==b.limit||s[20]!==b.offset||s[21]!==nt||s[22]!==A||s[23]!==O?(st={scope:O,filter:A,orderBy:nt,limit:b.limit,offset:b.offset},s[19]=b.limit,s[20]=b.offset,s[21]=nt,s[22]=A,s[23]=O,s[24]=st):st=s[24];let ct=st,lt=(0,_.useDeferredValue)(ct),ut=(0,_.useDeferredValue)(Ze),dt=ut===`first`?`store-and-network`:`network-only`,ft;s[25]!==ut||s[26]!==dt?(ft={fetchPolicy:dt,fetchKey:ut},s[25]=ut,s[26]=dt,s[27]=ft):ft=s[27];let{scopedDeployments:j}=(0,Ie.useLazyLoadQuery)(Pe,lt,ft),M,N,pt,P;s[28]!==Ve||s[29]!==Re||s[30]!==(j==null?void 0:j.count)||s[31]!==(j==null?void 0:j.edges)?(M=oe(o(j==null?void 0:j.edges,`node`)),P=(j==null?void 0:j.count)??0,N=Re==null?null:M.find(e=>e.id===Re)??null,pt=Ve==null?null:M.find(e=>e.id===Ve)??null,s[28]=Ve,s[29]=Re,s[30]=j==null?void 0:j.count,s[31]=j==null?void 0:j.edges,s[32]=M,s[33]=N,s[34]=pt,s[35]=P):(M=s[32],N=s[33],pt=s[34],P=s[35]);let F=pt,I=lt!==ct||ut!==Ze,[mt,ht]=(0,Ie.useMutation)(Fe),L;s[36]===h?L=s[37]:(L=h(`deployment.filter.Name`),s[36]=h,s[37]=L);let gt;s[38]===L?gt=s[39]:(gt={key:`name`,propertyLabel:L,type:`string`},s[38]=L,s[39]=gt);let R;s[40]===h?R=s[41]:(R=h(`deployment.filter.EndpointUrl`),s[40]=h,s[41]=R);let z;s[42]===R?z=s[43]:(z={key:`endpointUrl`,propertyLabel:R,type:`string`},s[42]=R,s[43]=z);let B;s[44]===h?B=s[45]:(B=h(`deployment.filter.OpenToPublic`),s[44]=h,s[45]=B);let V;s[46]===B?V=s[47]:(V={key:`openToPublic`,propertyLabel:B,type:`boolean`},s[46]=B,s[47]=V);let H;s[48]!==Ue||s[49]!==h?(H=Ue?[{key:`labels.some.key`,propertyLabel:h(`entityLabel.LabelKey`),type:`string`},{key:`labels.some.value`,propertyLabel:h(`entityLabel.LabelValue`),type:`string`}]:[],s[48]=Ue,s[49]=h,s[50]=H):H=s[50];let _t;s[51]!==gt||s[52]!==z||s[53]!==V||s[54]!==H?(_t=[gt,z,V,...H],s[51]=gt,s[52]=z,s[53]=V,s[54]=H,s[55]=_t):_t=s[55];let vt=_t,yt;s[56]===Symbol.for(`react.memo_cache_sentinel`)?(yt={flexShrink:1},s[56]=yt):yt=s[56];let U;s[57]!==w||s[58]!==S?(U=e=>{w({statusCategory:e}),S({current:1})},s[57]=w,s[58]=S,s[59]=U):U=s[59];let W;s[60]!==C.statusCategory||s[61]!==U?(W=(0,v.jsx)(Oe,{value:C.statusCategory,onChange:U}),s[60]=C.statusCategory,s[61]=U,s[62]=W):W=s[62];let bt=C.filter??void 0,G;s[63]!==w||s[64]!==S?(G=e=>{w({filter:e??null}),S({current:1})},s[63]=w,s[64]=S,s[65]=G):G=s[65];let K;s[66]!==vt||s[67]!==bt||s[68]!==G?(K=(0,v.jsx)(se,{filterProperties:vt,value:bt,onChange:G}),s[66]=vt,s[67]=bt,s[68]=G,s[69]=K):K=s[69];let q;s[70]!==W||s[71]!==K?(q=(0,v.jsxs)(p,{gap:`sm`,align:`start`,wrap:`wrap`,style:yt,children:[W,K]}),s[70]=W,s[71]=K,s[72]=q):q=s[72];let J;s[73]!==Ze||s[74]!==I||s[75]!==E?(J=(0,v.jsx)(p,{gap:`xs`,align:`center`,children:(0,v.jsx)(Te,{settingId:`deployment-list`,defaultAutoUpdateDelay:15e3,value:Ze,onChange:E,loading:I})}),s[73]=Ze,s[74]=I,s[75]=E,s[76]=J):J=s[76];let Y;s[77]!==q||s[78]!==J?(Y=(0,v.jsxs)(p,{justify:`between`,wrap:`wrap`,gap:`sm`,children:[q,J]}),s[77]=q,s[78]=J,s[79]=Y):Y=s[79];let xt=lt!==ct,X;s[80]===C.filter?X=s[81]:(X=a(C.filter)?null:JSON.stringify(C.filter),s[80]=C.filter,s[81]=X);let Z;s[82]!==C.order||s[83]!==C.statusCategory||s[84]!==X?(Z={statusCategory:C.statusCategory,filter:X,order:C.order},s[82]=C.order,s[83]=C.statusCategory,s[84]=X,s[85]=Z):Z=s[85];let St=et?N==null?void 0:N.id:null,Ct;s[86]!==T||s[87]!==M||s[88]!==xt||s[89]!==Z||s[90]!==St||s[91]!==x.current||s[92]!==x.pageSize||s[93]!==P?(Ct=(0,v.jsx)(Me,{deploymentsFrgmt:M,columnOverrides:T,page:x.current,pageSize:x.pageSize,total:P,pending:xt,viewParams:Z,editingDeploymentId:St}),s[86]=T,s[87]=M,s[88]=xt,s[89]=Z,s[90]=St,s[91]=x.current,s[92]=x.pageSize,s[93]=P,s[94]=Ct):Ct=s[94];let wt=Ue?We:void 0,Tt;s[95]!==w||s[96]!==S?(Tt=e=>{w({filter:me(e)}),S({current:1})},s[95]=w,s[96]=S,s[97]=Tt):Tt=s[97];let Et;s[98]===w?Et=s[99]:(Et=e=>{w({order:e??null})},s[98]=w,s[99]=Et);let Dt;s[100]===S?Dt=s[101]:(Dt=(e,t)=>{S({current:e,pageSize:t})},s[100]=S,s[101]=Dt);let Ot;s[102]!==Dt||s[103]!==x.current||s[104]!==x.pageSize||s[105]!==P?(Ot={current:x.current,pageSize:x.pageSize,total:P,onChange:Dt},s[102]=Dt,s[103]=x.current,s[104]=x.pageSize,s[105]=P,s[106]=Ot):Ot=s[106];let kt;s[107]!==T||s[108]!==Xe?(kt={columnOverrides:T,onColumnOverridesChange:Xe},s[107]=T,s[108]=Xe,s[109]=kt):kt=s[109];let At;s[110]!==Le||s[111]!==M||s[112]!==h||s[113]!==De?(At=e=>{let n=[`name`,`currentRevisionNumber`,`status`,`labels`,`replicaSummary`,`model`,`createdAt`,`id`,`endpointUrl`,`updatedAt`,`openToPublic`,`resourceGroup`],i=new Set([`name`,`currentRevisionNumber`,`status`,`replicaSummary`,`model`,`createdAt`]);return e.filter(e=>n.includes(e.key)).map(e=>{let n=e;return e.key===`name`?n={...e,render:(e,n)=>{var i,a;let o=ue((i=n.metadata)==null?void 0:i.status);return(0,v.jsx)(fe,{title:((a=n.metadata)==null?void 0:a.name)??`-`,onTitleClick:()=>De(`${Le(`deployments`)}/${n.entityId}`),copyable:!0,showActions:`always`,actions:[{key:`edit`,title:h(`deployment.EditDeployment`),icon:(0,v.jsx)(t,{}),disabled:o,onClick:()=>Be(n.id)},{key:`delete`,title:h(`deployment.DeleteDeployment`),icon:(0,v.jsx)(r,{size:`1em`}),type:`danger`,disabled:o,onClick:()=>He(n.id)}]})}}:e.key===`currentRevisionNumber`&&(n={...e,render:(e,t)=>{let n=M.find(e=>e.id===t.id),r=n==null?void 0:n.currentRevision;return(r==null?void 0:r.revisionNumber)==null?(0,v.jsx)(c,{color:`secondary`,children:`-`}):(0,v.jsx)(u,{onClick:()=>Ke(r),children:`#${r.revisionNumber}`})}}),e.key===`name`?n:{...n,defaultHidden:!i.has(e.key)}})},s[110]=Le,s[111]=M,s[112]=h,s[113]=De,s[114]=At):At=s[114];let jt;s[115]!==M||s[116]!==I||s[117]!==C.order||s[118]!==wt||s[119]!==Tt||s[120]!==Et||s[121]!==Ot||s[122]!==kt||s[123]!==At?(jt=(0,v.jsx)(ge,{onEditLabels:wt,onLabelClick:Tt,deploymentsFrgmt:M,loading:I,order:C.order,onChangeOrder:Et,pagination:Ot,tableSettings:kt,customizeColumns:At}),s[115]=M,s[116]=I,s[117]=C.order,s[118]=wt,s[119]=Tt,s[120]=Et,s[121]=Ot,s[122]=kt,s[123]=At,s[124]=jt):jt=s[124];let Mt;s[125]!==Y||s[126]!==Ct||s[127]!==jt?(Mt=(0,v.jsxs)(p,{direction:`column`,align:`stretch`,gap:`sm`,children:[Y,Ct,jt]}),s[125]=Y,s[126]=Ct,s[127]=jt,s[128]=Mt):Mt=s[128];let Nt=!!y,Pt;if(s[129]!==y){var Ft;Pt=y?[{entityId:y.entityId,name:((Ft=y.metadata)==null?void 0:Ft.name)??void 0}]:[],s[129]=y,s[130]=Pt}else Pt=s[130];let It=y==null?void 0:y.entityLabels,Lt;s[131]===E?Lt=s[132]:(Lt=e=>{We(null),e&&E()},s[131]=E,s[132]=Lt);let Rt;s[133]!==Nt||s[134]!==Pt||s[135]!==It||s[136]!==Lt?(Rt=(0,v.jsx)(pe,{open:Nt,entityType:`deployment`,targets:Pt,entityLabelsFrgmt:It,onRequestClose:Lt}),s[133]=Nt,s[134]=Pt,s[135]=It,s[136]=Lt,s[137]=Rt):Rt=s[137];let zt;s[138]!==N||s[139]!==f||s[140]!==m||s[141]!==et||s[142]!==E?(zt=et!=null&&(0,v.jsx)(ce,{children:(0,v.jsx)(de,{open:f||!!N,deploymentFrgmt:N??null,project:et,onRequestClose:e=>{m(),Be(null),e&&!N&&E()}})}),s[138]=N,s[139]=f,s[140]=m,s[141]=et,s[142]=E,s[143]=zt):zt=s[143];let Bt=!!F,Vt;s[144]===h?Vt=s[145]:(Vt=h(`deployment.DeleteDeployment`),s[144]=h,s[145]=Vt);let Q;s[146]===h?Q=s[147]:(Q=h(`deployment.Deployment`),s[146]=h,s[147]=Q);let Ht;if(s[148]!==F){var Ut;Ht=F?[{key:F.id,label:((Ut=F.metadata)==null?void 0:Ut.name)??``}]:[],s[148]=F,s[149]=Ht}else Ht=s[149];let Wt=(F==null||(n=F.metadata)==null?void 0:n.name)??``,Gt=(F==null||(i=F.metadata)==null?void 0:i.name)??``,Kt;s[150]===Gt?Kt=s[151]:(Kt={placeholder:Gt},s[150]=Gt,s[151]=Kt);let qt;s[152]===ht?qt=s[153]:(qt={loading:ht},s[152]=ht,s[153]=qt);let Jt;s[154]!==mt||s[155]!==F||s[156]!==Se||s[157]!==g||s[158]!==h||s[159]!==E?(Jt=()=>{F&&mt({variables:{input:{id:F.entityId}},onCompleted:(e,t)=>{t&&t.length>0?(Se.error(`Failed to delete deployment`,t),g.error(h(`deployment.FailedToDeleteDeployment`))):(g.success(h(`deployment.DeploymentDeleted`)),He(null),E())},onError:e=>{Se.error(`Failed to delete deployment`,e),g.error(h(`deployment.FailedToDeleteDeployment`))}})},s[154]=mt,s[155]=F,s[156]=Se,s[157]=g,s[158]=h,s[159]=E,s[160]=Jt):Jt=s[160];let Yt;s[161]===Symbol.for(`react.memo_cache_sentinel`)?(Yt=()=>He(null),s[161]=Yt):Yt=s[161];let Xt;s[162]!==Bt||s[163]!==Vt||s[164]!==Q||s[165]!==Ht||s[166]!==Wt||s[167]!==Kt||s[168]!==qt||s[169]!==Jt?(Xt=(0,v.jsx)(le,{open:Bt,title:Vt,target:Q,items:Ht,confirmText:Wt,requireConfirmInput:!0,inputProps:Kt,okButtonProps:qt,onOk:Jt,onCancel:Yt}),s[162]=Bt,s[163]=Vt,s[164]=Q,s[165]=Ht,s[166]=Wt,s[167]=Kt,s[168]=qt,s[169]=Jt,s[170]=Xt):Xt=s[170];let Zt=!!Ge,Qt;s[171]===Symbol.for(`react.memo_cache_sentinel`)?(Qt=()=>Ke(null),s[171]=Qt):Qt=s[171];let $;s[172]!==Ge||s[173]!==Zt?($=(0,v.jsx)(ce,{children:(0,v.jsx)(je,{open:Zt,revisionFrgmt:Ge,onClose:Qt})}),s[172]=Ge,s[173]=Zt,s[174]=$):$=s[174];let $t;return s[175]!==Mt||s[176]!==Rt||s[177]!==zt||s[178]!==Xt||s[179]!==$?($t=(0,v.jsxs)(v.Fragment,{children:[Mt,Rt,zt,Xt,$]}),s[175]=Mt,s[176]=Rt,s[177]=zt,s[178]=Xt,s[179]=$,s[180]=$t):$t=s[180],$t},Re=()=>{"use memo";let e=(0,Ne.c)(15),{t}=ee(),[n,r]=h(!1),{setLeft:i,setRight:a}=r;De(a);let o;e[0]===t?o=e[1]:(o=t(`webui.menu.Deployments`),e[0]=t,e[1]=o);let s;e[2]===t?s=e[3]:(s=t(`deployment.CreateDeployment`),e[2]=t,e[3]=s);let c;e[4]!==a||e[5]!==s?(c=(0,v.jsx)(f,{variant:`primary`,label:s,onClick:a}),e[4]=a,e[5]=s,e[6]=c):c=e[6];let l;e[7]===Symbol.for(`react.memo_cache_sentinel`)?(l=(0,v.jsx)(g,{}),e[7]=l):l=e[7];let u;e[8]!==i||e[9]!==n?(u=(0,v.jsx)(_.Suspense,{fallback:l,children:(0,v.jsx)(Le,{isCreating:n,onCloseCreate:i})}),e[8]=i,e[9]=n,e[10]=u):u=e[10];let d;return e[11]!==o||e[12]!==c||e[13]!==u?(d=(0,v.jsx)(p,{direction:`column`,align:`stretch`,gap:`md`,children:(0,v.jsx)(Se,{variant:`borderless`,title:o,extra:c,children:u})}),e[11]=o,e[12]=c,e[13]=u,e[14]=d):d=e[14],d};function ze(e){return typeof e==`object`&&e&&!Array.isArray(e)?e:{}}export{Re as default};
