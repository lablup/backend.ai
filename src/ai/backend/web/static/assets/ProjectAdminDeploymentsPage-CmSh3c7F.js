import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{S as t,Zn as n,f as r}from"./icons-Btg1s2wy.js";import{t as i}from"./compiler-runtime-CZQb2eIb.js";import{vt as a}from"./lodash-ClfL87UH.js";/* empty css            */import{t as o}from"./jsx-runtime-BapUIyWk.js";import{R as s}from"./usePressFeedback-BIoIGSxE.js";import{O as ee,at as c}from"./DefaultProviders-BFjPhnQa.js";import{r as te}from"./Skeleton-D35z7Ria.js";import{t as ne}from"./BAIFlex-BElkJeHW.js";import{t as re}from"./app-shim-DTEBzR8d.js";import{G as ie,d as ae}from"./helper-BWFKT_2Y.js";import{r as oe}from"./hooks-UUY7pxyu.js";import{t as se}from"./react-relay-BfoHYpUf.js";import{t as ce}from"./useBAILogger-CRaS0DnM.js";import{u as le}from"./helper-DF1Eunoe.js";import{t as ue}from"./BAIGraphQLPropertyFilter-CNTUQIkF.js";import{t as de}from"./BAIUnmountAfterClose-Cxr4Dp_U.js";import{t as l}from"./BAISkeleton-MIjJv1Hr.js";import{t as fe}from"./BAIDeleteConfirmModal-CwJ76ZY7.js";import{i as pe,t as me}from"./DeploymentSettingModal-BYp0LIhY.js";import{t as he}from"./BAINameActionCell-BaFf27s9.js";import{t as ge}from"./BAIEntityLabelSettingModal-BzN4qIYx.js";import{i as _e}from"./BAIEntityLabelCell-DOyaclRH.js";import{r as ve,t as ye}from"./BAIModelDeploymentNodes-bPs9qaCp.js";import{i as be,n as xe,o as Se}from"./dist-C3M-rFln.js";import{t as Ce}from"./useCurrentProject-BaleCvMA.js";import{o as we}from"./useRouteScope-Dgi-LDmN.js";import{N as u,ht as d,pt as Te}from"./index-49VU5B_r.js";import{t as Ee}from"./AutoUpdateFetchKeyButton-C-RHyKup.js";import{n as De}from"./reactPaginationQueryOptions-DUCwh22X.js";import{n as Oe,r as ke,t as Ae}from"./DeploymentStatusCategoryControl-Ng0rAYHN.js";import{t as je}from"./DeploymentRevisionDetailDrawer-eT3h35BX.js";var Me=i(),Ne=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`filter`},t={defaultValue:null,kind:`LocalArgument`,name:`limit`},n={defaultValue:null,kind:`LocalArgument`,name:`offset`},r={defaultValue:null,kind:`LocalArgument`,name:`orderBy`},i={defaultValue:null,kind:`LocalArgument`,name:`scope`},a=[{kind:`Variable`,name:`filter`,variableName:`filter`},{kind:`Variable`,name:`limit`,variableName:`limit`},{kind:`Variable`,name:`offset`,variableName:`offset`},{kind:`Variable`,name:`orderBy`,variableName:`orderBy`},{kind:`Variable`,name:`scope`,variableName:`scope`}],o={alias:null,args:null,kind:`ScalarField`,name:`count`,storageKey:null},s={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},ee={alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},c={alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},te={alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null},ne={alias:null,args:null,kind:`ScalarField`,name:`revisionNumber`,storageKey:null},re={alias:null,args:null,kind:`ScalarField`,name:`createdAt`,storageKey:null},ie={alias:null,args:null,concreteType:`VirtualFolderNode`,kind:`LinkedField`,name:`vfolder`,plural:!1,selections:[s,c,{alias:null,args:null,kind:`ScalarField`,name:`row_id`,storageKey:null}],storageKey:null},ae={alias:null,args:null,kind:`ScalarField`,name:`vfolderId`,storageKey:null},oe={alias:null,args:null,kind:`ScalarField`,name:`mountDestination`,storageKey:null},se={alias:null,args:null,kind:`ScalarField`,name:`fieldId`,storageKey:null},ce={alias:null,args:null,kind:`ScalarField`,name:`value`,storageKey:null},le=[c,ce],ue={alias:null,args:null,kind:`ScalarField`,name:`key`,storageKey:null},de=[ue,ce];return{fragment:{argumentDefinitions:[e,t,n,r,i],kind:`Fragment`,metadata:null,name:`ProjectAdminDeploymentsPageQuery`,selections:[{alias:null,args:a,concreteType:`ModelDeploymentConnection`,kind:`LinkedField`,name:`scopedDeployments`,plural:!1,selections:[o,{alias:null,args:null,concreteType:`ModelDeploymentEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ModelDeployment`,kind:`LinkedField`,name:`node`,plural:!1,selections:[s,ee,{args:null,kind:`FragmentSpread`,name:`BAIModelDeploymentNodesFragment`},{args:null,kind:`FragmentSpread`,name:`DeploymentSettingModal_deployment`},{alias:null,args:null,concreteType:`ModelDeploymentMetadata`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:[c,te],storageKey:null},{alias:null,args:null,concreteType:`ModelRevision`,kind:`LinkedField`,name:`currentRevision`,plural:!1,selections:[s,ne,{args:null,kind:`FragmentSpread`,name:`DeploymentRevisionDetail_revision`}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[i,e,r,t,n],kind:`Operation`,name:`ProjectAdminDeploymentsPageQuery`,selections:[{alias:null,args:a,concreteType:`ModelDeploymentConnection`,kind:`LinkedField`,name:`scopedDeployments`,plural:!1,selections:[o,{alias:null,args:null,concreteType:`ModelDeploymentEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ModelDeployment`,kind:`LinkedField`,name:`node`,plural:!1,selections:[s,ee,{alias:null,args:null,kind:`ScalarField`,name:`currentRevisionId`,storageKey:null},{alias:null,args:null,concreteType:`ModelDeploymentMetadata`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`projectId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`domainName`,storageKey:null},c,te,re,{alias:null,args:null,kind:`ScalarField`,name:`updatedAt`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`resourceGroupName`,storageKey:null},{alias:null,args:null,concreteType:`ProjectV2`,kind:`LinkedField`,name:`projectV2`,plural:!1,selections:[{alias:null,args:null,concreteType:`ProjectBasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:[c],storageKey:null},s],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`tags`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ModelDeploymentNetworkAccess`,kind:`LinkedField`,name:`networkAccess`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`endpointUrl`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`preferredDomainName`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`openToPublic`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`DeploymentStrategy`,kind:`LinkedField`,name:`defaultDeploymentStrategy`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`type`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ReplicaState`,kind:`LinkedField`,name:`replicaState`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`replicaCount`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`desiredReplicaCount`,storageKey:null}],storageKey:null},{alias:`runningReplicas`,args:[{kind:`Literal`,name:`filter`,value:{status:{equals:`RUNNING`}}}],concreteType:`ModelReplicaConnection`,kind:`LinkedField`,name:`replicas`,plural:!1,selections:[o],storageKey:`replicas(filter:{"status":{"equals":"RUNNING"}})`},{alias:null,args:null,concreteType:`ModelRevision`,kind:`LinkedField`,name:`currentRevision`,plural:!1,selections:[s,ne,{alias:null,args:null,concreteType:`ModelMountConfig`,kind:`LinkedField`,name:`modelMountConfig`,plural:!1,selections:[ie,ae,oe,{alias:null,args:null,kind:`ScalarField`,name:`definitionPath`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`subpath`,storageKey:null}],storageKey:null},se,re,{alias:null,args:null,concreteType:`ClusterConfig`,kind:`LinkedField`,name:`clusterConfig`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`mode`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`size`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`AllocatedResourceSlot`,kind:`LinkedField`,name:`resourceSlots`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`slotName`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`quantity`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ResourceConfig`,kind:`LinkedField`,name:`resourceConfig`,plural:!1,selections:[{alias:null,args:null,concreteType:`ResourceOpts`,kind:`LinkedField`,name:`resourceOpts`,plural:!1,selections:[{alias:null,args:null,concreteType:`ResourceOptsEntry`,kind:`LinkedField`,name:`entries`,plural:!0,selections:le,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ModelRuntimeConfig`,kind:`LinkedField`,name:`modelRuntimeConfig`,plural:!1,selections:[{alias:null,args:null,concreteType:`RuntimeVariant`,kind:`LinkedField`,name:`runtimeVariant`,plural:!1,selections:[c,s],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`inferenceRuntimeConfig`,storageKey:null},{alias:null,args:null,concreteType:`EnvironmentVariables`,kind:`LinkedField`,name:`environ`,plural:!1,selections:[{alias:null,args:null,concreteType:`EnvironmentVariableEntry`,kind:`LinkedField`,name:`entries`,plural:!0,selections:le,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`RuntimeVariantPresetValue`,kind:`LinkedField`,name:`runtimeVariantPresetValues`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`presetId`,storageKey:null},ce,{alias:null,args:null,concreteType:`RuntimeVariantPreset`,kind:`LinkedField`,name:`preset`,plural:!1,selections:[c,{alias:null,args:null,kind:`ScalarField`,name:`displayName`,storageKey:null},{alias:null,args:null,concreteType:`PresetTargetSpec`,kind:`LinkedField`,name:`targetSpec`,plural:!1,selections:[ue],storageKey:null},s],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ExtraVFolderMountInfo`,kind:`LinkedField`,name:`extraMounts`,plural:!0,selections:[ae,oe,{alias:null,args:null,kind:`ScalarField`,name:`mountPerm`,storageKey:null},ie],storageKey:null},{alias:null,args:null,concreteType:`ImageV2`,kind:`LinkedField`,name:`imageV2`,plural:!1,selections:[s,{alias:null,args:null,concreteType:`ImageV2IdentityInfo`,kind:`LinkedField`,name:`identity`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`canonicalName`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`architecture`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ImageV2MetadataInfo`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:[{alias:null,args:null,concreteType:`ImageV2TagEntry`,kind:`LinkedField`,name:`tags`,plural:!0,selections:de,storageKey:null},{alias:null,args:null,concreteType:`ImageV2LabelEntry`,kind:`LinkedField`,name:`labels`,plural:!0,selections:de,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ModelDefinition`,kind:`LinkedField`,name:`modelDefinition`,plural:!1,selections:[{alias:null,args:null,concreteType:`ModelConfig`,kind:`LinkedField`,name:`models`,plural:!0,selections:[c,{alias:null,args:null,kind:`ScalarField`,name:`modelPath`,storageKey:null},{alias:null,args:null,concreteType:`ModelServiceConfig`,kind:`LinkedField`,name:`service`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`command`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`startCommand`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`shell`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`port`,storageKey:null},{alias:null,args:null,concreteType:`PreStartAction`,kind:`LinkedField`,name:`preStartActions`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`action`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`args`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ModelHealthCheck`,kind:`LinkedField`,name:`healthCheck`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`path`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`initialDelay`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`maxRetries`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`interval`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`maxWaitTime`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`expectedStatusCode`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:[{kind:`Literal`,name:`limit`,value:100}],concreteType:`EntityLabelConnection`,kind:`LinkedField`,name:`entityLabels`,plural:!1,selections:[{alias:null,args:null,concreteType:`EntityLabelEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`EntityLabel`,kind:`LinkedField`,name:`node`,plural:!1,selections:[ue,ce,s,se],storageKey:null}],storageKey:null}],storageKey:`entityLabels(limit:100)`},{alias:null,args:null,concreteType:`UserV2`,kind:`LinkedField`,name:`creator`,plural:!1,selections:[s,{alias:null,args:null,concreteType:`UserV2BasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`email`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`username`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`fullName`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:`173238833d93d5dd782bb15caa4f7967`,id:null,metadata:{},name:`ProjectAdminDeploymentsPageQuery`,operationKind:`query`,text:`query ProjectAdminDeploymentsPageQuery(
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
`}}})();Ne.hash=`ceffac8d26939ee1620ead56f58b960c`;var Pe=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`input`}],t=[{alias:null,args:[{kind:`Variable`,name:`input`,variableName:`input`}],concreteType:`DeleteDeploymentPayload`,kind:`LinkedField`,name:`deleteModelDeployment`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`ProjectAdminDeploymentsPageDeleteMutation`,selections:t,type:`Mutation`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`ProjectAdminDeploymentsPageDeleteMutation`,selections:t},params:{cacheID:`1463ddcf31aa971e7f72ca3901c5db76`,id:null,metadata:{},name:`ProjectAdminDeploymentsPageDeleteMutation`,operationKind:`mutation`,text:`mutation ProjectAdminDeploymentsPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}})();Pe.hash=`42ff73332d0c41e5828ba82d49920b78`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var f=e(n(),1),Fe=se(),p=o(),Ie=e=>{"use memo";var n,i,o,se;let l=(0,Me.c)(158),{projectId:Ce}=e,{t:u}=te(),{message:d}=re.useApp(),{logger:Ie}=ce(),Le=ie(),ze=we(),[Be,Ve]=(0,f.useState)(null),[He,Ue]=(0,f.useState)(null),We=Te(`deployment`),[m,Ge]=(0,f.useState)(null),[Ke,qe]=(0,f.useState)(null),Je;l[0]===Symbol.for(`react.memo_cache_sentinel`)?(Je={current:1,pageSize:10},l[0]=Je):Je=l[0];let{baiPaginationOption:h,tablePaginationOption:g,setTablePaginationOption:_}=De(Je),Ye,Xe;l[1]===Symbol.for(`react.memo_cache_sentinel`)?(Ye={filter:xe(Re),order:be(ve),statusCategory:be(Ae).withDefault(`serving`)},Xe={history:`replace`},l[1]=Ye,l[2]=Xe):(Ye=l[1],Xe=l[2]);let[v,y]=Se(Ye,Xe),[Ze,Qe]=ee(`table_column_overrides.ProjectAdminDeploymentsPage`),[$e,b]=oe(),et;l[3]===v.statusCategory?et=l[4]:(et=ke(v.statusCategory),l[3]=v.statusCategory,l[4]=et);let tt=et,x;l[5]===Ce?x=l[6]:(x={project:[{value:Ce}]},l[5]=Ce,l[6]=x);let S;l[7]===v.filter?S=l[8]:(S=v.filter??{},l[7]=v.filter,l[8]=S);let C;l[9]!==tt||l[10]!==S?(C={...S,...tt},l[9]=tt,l[10]=S,l[11]=C):C=l[11];let w;l[12]===v.order?w=l[13]:(w=ae(v.order),l[12]=v.order,l[13]=w);let nt;l[14]!==h.limit||l[15]!==h.offset||l[16]!==x||l[17]!==C||l[18]!==w?(nt={scope:x,filter:C,orderBy:w,limit:h.limit,offset:h.offset},l[14]=h.limit,l[15]=h.offset,l[16]=x,l[17]=C,l[18]=w,l[19]=nt):nt=l[19];let rt=nt,it=(0,f.useDeferredValue)(rt),at=(0,f.useDeferredValue)($e),ot=at===`first`?`store-and-network`:`network-only`,st;l[20]!==at||l[21]!==ot?(st={fetchKey:at,fetchPolicy:ot},l[20]=at,l[21]=ot,l[22]=st):st=l[22];let T=(0,Fe.useLazyLoadQuery)(Ne,it,st),E,D,ct,O;if(l[23]!==((n=T.scopedDeployments)==null?void 0:n.count)||l[24]!==((i=T.scopedDeployments)==null?void 0:i.edges)||l[25]!==He||l[26]!==Be){var lt,ut,dt,ft;E=le(a((lt=T.scopedDeployments)==null?void 0:lt.edges,`node`)),O=((ut=T.scopedDeployments)==null?void 0:ut.count)??0,D=Be==null?null:E.find(e=>e.id===Be)??null,ct=He==null?null:E.find(e=>e.id===He)??null,l[23]=(dt=T.scopedDeployments)==null?void 0:dt.count,l[24]=(ft=T.scopedDeployments)==null?void 0:ft.edges,l[25]=He,l[26]=Be,l[27]=E,l[28]=D,l[29]=ct,l[30]=O}else E=l[27],D=l[28],ct=l[29],O=l[30];let k=ct,A=it!==rt||at!==$e,[pt,mt]=(0,Fe.useMutation)(Pe),j;l[31]===u?j=l[32]:(j=u(`deployment.filter.Name`),l[31]=u,l[32]=j);let M;l[33]===j?M=l[34]:(M={key:`name`,propertyLabel:j,type:`string`},l[33]=j,l[34]=M);let N;l[35]===u?N=l[36]:(N=u(`deployment.filter.EndpointUrl`),l[35]=u,l[36]=N);let P;l[37]===N?P=l[38]:(P={key:`endpointUrl`,propertyLabel:N,type:`string`},l[37]=N,l[38]=P);let F;l[39]===u?F=l[40]:(F=u(`deployment.filter.OpenToPublic`),l[39]=u,l[40]=F);let I;l[41]===F?I=l[42]:(I={key:`openToPublic`,propertyLabel:F,type:`boolean`},l[41]=F,l[42]=I);let L;l[43]!==We||l[44]!==u?(L=We?[{key:`labels.some.key`,propertyLabel:u(`entityLabel.LabelKey`),type:`string`},{key:`labels.some.value`,propertyLabel:u(`entityLabel.LabelValue`),type:`string`}]:[],l[43]=We,l[44]=u,l[45]=L):L=l[45];let ht;l[46]!==M||l[47]!==P||l[48]!==I||l[49]!==L?(ht=[M,P,I,...L],l[46]=M,l[47]=P,l[48]=I,l[49]=L,l[50]=ht):ht=l[50];let gt=ht,_t;l[51]===Symbol.for(`react.memo_cache_sentinel`)?(_t={flexShrink:1},l[51]=_t):_t=l[51];let R;l[52]!==y||l[53]!==_?(R=e=>{y({statusCategory:e}),_({current:1})},l[52]=y,l[53]=_,l[54]=R):R=l[54];let z;l[55]!==v.statusCategory||l[56]!==R?(z=(0,p.jsx)(Oe,{value:v.statusCategory,onChange:R}),l[55]=v.statusCategory,l[56]=R,l[57]=z):z=l[57];let vt=v.filter??void 0,yt;l[58]!==y||l[59]!==_?(yt=e=>{y({filter:e??null}),_({current:1})},l[58]=y,l[59]=_,l[60]=yt):yt=l[60];let B;l[61]!==gt||l[62]!==vt||l[63]!==yt?(B=(0,p.jsx)(ue,{filterProperties:gt,value:vt,onChange:yt}),l[61]=gt,l[62]=vt,l[63]=yt,l[64]=B):B=l[64];let V;l[65]!==z||l[66]!==B?(V=(0,p.jsxs)(ne,{gap:`sm`,align:`start`,wrap:`wrap`,style:_t,children:[z,B]}),l[65]=z,l[66]=B,l[67]=V):V=l[67];let H;l[68]===b?H=l[69]:(H=e=>b(e),l[68]=b,l[69]=H);let U;l[70]!==$e||l[71]!==A||l[72]!==H?(U=(0,p.jsx)(Ee,{settingId:`project-admin-deployments`,defaultAutoUpdateDelay:15e3,loading:A,value:$e,onChange:H}),l[70]=$e,l[71]=A,l[72]=H,l[73]=U):U=l[73];let W;l[74]!==V||l[75]!==U?(W=(0,p.jsxs)(ne,{justify:`between`,wrap:`wrap`,gap:`sm`,children:[V,U]}),l[74]=V,l[75]=U,l[76]=W):W=l[76];let bt=We?Ge:void 0,G;l[77]!==y||l[78]!==_?(G=e=>{y({filter:_e(e)}),_({current:1})},l[77]=y,l[78]=_,l[79]=G):G=l[79];let K;l[80]===y?K=l[81]:(K=e=>{y({order:e??null})},l[80]=y,l[81]=K);let q;l[82]===_?q=l[83]:(q=(e,t)=>{_({current:e,pageSize:t})},l[82]=_,l[83]=q);let J;l[84]!==q||l[85]!==g.current||l[86]!==g.pageSize||l[87]!==O?(J={current:g.current,pageSize:g.pageSize,total:O,onChange:q},l[84]=q,l[85]=g.current,l[86]=g.pageSize,l[87]=O,l[88]=J):J=l[88];let Y;l[89]!==Ze||l[90]!==Qe?(Y={columnOverrides:Ze,onColumnOverridesChange:Qe},l[89]=Ze,l[90]=Qe,l[91]=Y):Y=l[91];let X;l[92]!==ze||l[93]!==E||l[94]!==u||l[95]!==Le?(X=e=>{let n=[`name`,`currentRevisionNumber`,`status`,`labels`,`replicaSummary`,`model`,`createdAt`,`owner`,`id`,`endpointUrl`,`updatedAt`,`openToPublic`,`resourceGroup`,`domainName`,`projectId`],i=new Set([`name`,`currentRevisionNumber`,`status`,`labels`,`replicaSummary`,`model`,`createdAt`,`owner`]);return e.filter(e=>n.includes(e.key)).map(e=>{let n=e;return e.key===`name`?n={...e,render:(e,n)=>{var i,a;let o=pe((i=n.metadata)==null?void 0:i.status);return(0,p.jsx)(he,{title:((a=n.metadata)==null?void 0:a.name)??`-`,onTitleClick:()=>Le(ze(`deployments/${n.entityId}`)),copyable:!0,showActions:`always`,actions:[{key:`edit`,title:u(`deployment.EditDeployment`),icon:(0,p.jsx)(t,{}),disabled:o,onClick:()=>Ve(n.id)},{key:`delete`,title:u(`deployment.DeleteDeployment`),icon:(0,p.jsx)(r,{size:`1em`}),type:`danger`,disabled:o,onClick:()=>Ue(n.id)}]})}}:e.key===`currentRevisionNumber`&&(n={...e,render:(e,t)=>{let n=E.find(e=>e.id===t.id),r=n==null?void 0:n.currentRevision;return(r==null?void 0:r.revisionNumber)==null?(0,p.jsx)(s,{color:`secondary`,children:`-`}):(0,p.jsx)(c,{onClick:()=>qe(r),children:`#${r.revisionNumber}`})}}),e.key===`name`?n:{...n,defaultHidden:!i.has(e.key)}})},l[92]=ze,l[93]=E,l[94]=u,l[95]=Le,l[96]=X):X=l[96];let Z;l[97]!==E||l[98]!==A||l[99]!==v.order||l[100]!==bt||l[101]!==G||l[102]!==K||l[103]!==J||l[104]!==Y||l[105]!==X?(Z=(0,p.jsx)(ye,{onEditLabels:bt,showLabelsByDefault:!0,onLabelClick:G,deploymentsFrgmt:E,loading:A,order:v.order,onChangeOrder:K,pagination:J,tableSettings:Y,customizeColumns:X}),l[97]=E,l[98]=A,l[99]=v.order,l[100]=bt,l[101]=G,l[102]=K,l[103]=J,l[104]=Y,l[105]=X,l[106]=Z):Z=l[106];let xt;l[107]!==W||l[108]!==Z?(xt=(0,p.jsxs)(ne,{direction:`column`,align:`stretch`,gap:`sm`,children:[W,Z]}),l[107]=W,l[108]=Z,l[109]=xt):xt=l[109];let St=!!m,Ct;if(l[110]!==m){var wt;Ct=m?[{entityId:m.entityId,name:((wt=m.metadata)==null?void 0:wt.name)??void 0}]:[],l[110]=m,l[111]=Ct}else Ct=l[111];let Tt=m==null?void 0:m.entityLabels,Et;l[112]===b?Et=l[113]:(Et=e=>{Ge(null),e&&b()},l[112]=b,l[113]=Et);let Dt;l[114]!==St||l[115]!==Ct||l[116]!==Tt||l[117]!==Et?(Dt=(0,p.jsx)(ge,{open:St,entityType:`deployment`,targets:Ct,entityLabelsFrgmt:Tt,onRequestClose:Et}),l[114]=St,l[115]=Ct,l[116]=Tt,l[117]=Et,l[118]=Dt):Dt=l[118];let Ot;l[119]===D?Ot=l[120]:(Ot=D!=null&&(0,p.jsx)(me,{open:!0,deploymentFrgmt:D,onRequestClose:()=>{Ve(null)}}),l[119]=D,l[120]=Ot);let kt=!!k,At;l[121]===u?At=l[122]:(At=u(`deployment.DeleteDeployment`),l[121]=u,l[122]=At);let jt;l[123]===u?jt=l[124]:(jt=u(`deployment.Deployment`),l[123]=u,l[124]=jt);let Mt;if(l[125]!==k){var Nt;Mt=k?[{key:k.id,label:((Nt=k.metadata)==null?void 0:Nt.name)??``}]:[],l[125]=k,l[126]=Mt}else Mt=l[126];let Pt=(k==null||(o=k.metadata)==null?void 0:o.name)??``,Ft=(k==null||(se=k.metadata)==null?void 0:se.name)??``,Q;l[127]===Ft?Q=l[128]:(Q={placeholder:Ft},l[127]=Ft,l[128]=Q);let It;l[129]===mt?It=l[130]:(It={loading:mt},l[129]=mt,l[130]=It);let Lt;l[131]!==pt||l[132]!==k||l[133]!==Ie||l[134]!==d||l[135]!==u||l[136]!==b?(Lt=()=>{k&&pt({variables:{input:{id:k.entityId}},onCompleted:(e,t)=>{t&&t.length>0?(Ie.error(`Failed to delete deployment`,t),d.error(u(`deployment.FailedToDeleteDeployment`))):(d.success(u(`deployment.DeploymentDeleted`)),Ue(null),b())},onError:e=>{Ie.error(`Failed to delete deployment`,e),d.error(u(`deployment.FailedToDeleteDeployment`))}})},l[131]=pt,l[132]=k,l[133]=Ie,l[134]=d,l[135]=u,l[136]=b,l[137]=Lt):Lt=l[137];let Rt;l[138]===Symbol.for(`react.memo_cache_sentinel`)?(Rt=()=>Ue(null),l[138]=Rt):Rt=l[138];let zt;l[139]!==kt||l[140]!==At||l[141]!==jt||l[142]!==Mt||l[143]!==Pt||l[144]!==Q||l[145]!==It||l[146]!==Lt?(zt=(0,p.jsx)(fe,{open:kt,title:At,target:jt,items:Mt,confirmText:Pt,requireConfirmInput:!0,inputProps:Q,okButtonProps:It,onOk:Lt,onCancel:Rt}),l[139]=kt,l[140]=At,l[141]=jt,l[142]=Mt,l[143]=Pt,l[144]=Q,l[145]=It,l[146]=Lt,l[147]=zt):zt=l[147];let Bt=!!Ke,Vt;l[148]===Symbol.for(`react.memo_cache_sentinel`)?(Vt=()=>qe(null),l[148]=Vt):Vt=l[148];let $;l[149]!==Ke||l[150]!==Bt?($=(0,p.jsx)(de,{children:(0,p.jsx)(je,{open:Bt,revisionFrgmt:Ke,onClose:Vt})}),l[149]=Ke,l[150]=Bt,l[151]=$):$=l[151];let Ht;return l[152]!==xt||l[153]!==Dt||l[154]!==Ot||l[155]!==zt||l[156]!==$?(Ht=(0,p.jsxs)(p.Fragment,{children:[xt,Dt,Ot,zt,$]}),l[152]=xt,l[153]=Dt,l[154]=Ot,l[155]=zt,l[156]=$,l[157]=Ht):Ht=l[157],Ht},Le=()=>{"use memo";let e=(0,Me.c)(9),{t}=te(),n=Ce(),r;e[0]===t?r=e[1]:(r=t(`webui.menu.ProjectDeployments`),e[0]=t,e[1]=r);let i;e[2]===Symbol.for(`react.memo_cache_sentinel`)?(i={header:{borderBottom:`none`},body:{paddingTop:0}},e[2]=i):i=e[2];let a;e[3]===Symbol.for(`react.memo_cache_sentinel`)?(a=(0,p.jsx)(l,{}),e[3]=a):a=e[3];let o;e[4]===n.id?o=e[5]:(o=(0,p.jsx)(u,{children:(0,p.jsx)(f.Suspense,{fallback:a,children:n.id?(0,p.jsx)(Ie,{projectId:n.id}):(0,p.jsx)(l,{})})}),e[4]=n.id,e[5]=o);let s;return e[6]!==r||e[7]!==o?(s=(0,p.jsx)(d,{variant:`borderless`,title:r,styles:i,children:o}),e[6]=r,e[7]=o,e[8]=s):s=e[8],s};function Re(e){return typeof e==`object`&&e&&!Array.isArray(e)?e:{}}export{Le as default};
