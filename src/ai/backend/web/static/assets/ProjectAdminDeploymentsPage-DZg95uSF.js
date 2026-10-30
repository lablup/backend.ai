import{c as vl,u as Il,b as Al,n as a,bu as Nl,x as bl,c0 as Pl,aK as Ml,cb as Vl,a as Rl,i as Sl,j as xl,k as Bl,g as _l,l as El,m as wl,r as Kl,q as Ol,s as Ul,bb as $l,B as Dl,w as ql,C as il,T as zl,L as Ql,N as Gl,z as Hl}from"./index-CwWAznqi.js";import{A as Wl}from"./AutoUpdateFetchKeyButton-MZ4HY-Ai.js";import{D as Jl,a as Yl}from"./DeploymentSettingModal-B8BbcaQs.js";import{u as Xl}from"./reactPaginationQueryOptions-Bt4rkB5i.js";import{r as A,k as Zl,a as en}from"./icons-BgdBQS0N.js";import{m as ln}from"./lodash-RhKGq0BF.js";import{B as nn,a as an}from"./BAIModelDeploymentNodes-BNyQD-Ld.js";import{B as tn}from"./BAIGraphQLPropertyFilter-BwM0Jjll.js";import{i as rn}from"./BAIDeploymentStatusBadge-axTa07mq.js";import{B as sn}from"./BAINameActionCell-BZc0os_M.js";import{B as on}from"./BAIEntityLabelSettingModal-zXhyYD10.js";import{B as un}from"./BAIDeleteConfirmModal-CUutQ4aO.js";import{t as dn}from"./BAIEntityLabelTokens-BWz7hwXT.js";import"./BAIFetchKeyButton-DApd5OLT.js";import"./useControllableValue-BmgV_ECW.js";import"./ButtonGroup-DPQvGHtt.js";import"./parseCliCommand-DLNI3aPC.js";import"./FolderLink-DaaLvORM.js";import"./BAIVFolderIdenticon-PgyEX4dv.js";import"./SourceCodeView-jXLvuWSO.js";import"./CodeBlock-CV2dJgqa.js";import"./useScrollableArea-Bsuw_xFk.js";import"./BAIId-C7PlhBcJ.js";import"./BAIImageNodeSimpleTagV2-grs0QBeV.js";import"./BAIDoubleToken-DmnYFlRB.js";import"./BAITextHighlighter-9-PRKuKt.js";import"./Token-B6wppFPd.js";import"./useBAIIconPath-kZbqwXZ-.js";import"./BAIResourceNumberWithIcon-jmo0jZh2.js";import"./astryxPlacement-BxR6_qos.js";import"./BAIMetadataList-BYZUwKjA.js";import"./BAIProjectResourceGroupSelect-CKRGsOXh.js";import"./NumberInput-BX3bbN7A.js";import"./NumberInput-BAShrYzU.js";import"./useLocale-tF6sKPhr.js";import"./TagsInput-B_f8kLOn.js";import"./Tokenizer-Czn8bbzO.js";import"./groupItems-BfxkhRY8.js";import"./characters-DWaYg7k3.js";import"./CheckboxInput-Dvbz8RhO.js";import"./BAIBooleanToken-C7s4YZH-.js";import"./BAIEntityLabelCell-DciPKo0X.js";import"./BAITable-BJsxYyy0.js";import"./Table-SIAPvWUk.js";import"./MenuBottomSheetActionList-DfgiyqqP.js";import"./Pagination-cBiGXF8Y.js";import"./BAIPowerSearchAdapters-Cpa0dtdE.js";import"./DateRangeInput-BafIu0I7.js";import"./BottomSheet-C7Cy7dyi.js";import"./astryxTagVariant-CibgwVXb.js";import"./BAIBulkErrorModal-B1rud_RV.js";const Ll=(function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e},params:{cacheID:"1463ddcf31aa971e7f72ca3901c5db76",id:null,metadata:{},name:"ProjectAdminDeploymentsPageDeleteMutation",operationKind:"mutation",text:`mutation ProjectAdminDeploymentsPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}})();Ll.hash="42ff73332d0c41e5828ba82d49920b78";const hl=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},y={defaultValue:null,kind:"LocalArgument",name:"offset"},l={defaultValue:null,kind:"LocalArgument",name:"orderBy"},d={defaultValue:null,kind:"LocalArgument",name:"projectId"},m=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{fields:[{kind:"Variable",name:"projectId",variableName:"projectId"}],kind:"ObjectValue",name:"scope"}],u={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},v={alias:null,args:null,kind:"ScalarField",name:"entityId",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},I={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},N={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},L={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},c={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[i,g,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},Ie={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},Le={alias:null,args:null,kind:"ScalarField",name:"fieldId",storageKey:null},F={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},b=[g,F],k={alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},o=[k,F];return{fragment:{argumentDefinitions:[n,e,y,l,d],kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:m,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[u,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[i,v,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[g,I],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[i,N,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[d,n,l,e,y],kind:"Operation",name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:m,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[u,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[i,v,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},g,I,L,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[g],storageKey:null},i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[u],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[i,N,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[c,Ie,h,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"subpath",storageKey:null}],storageKey:null},Le,L,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:b,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[g,i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:b,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},F,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[g,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[k],storageKey:null},i],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[Ie,h,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},c],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageV2TagEntry",kind:"LinkedField",name:"tags",plural:!0,selections:o,storageKey:null},{alias:null,args:null,concreteType:"ImageV2LabelEntry",kind:"LinkedField",name:"labels",plural:!0,selections:o,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[g,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"command",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:[{kind:"Literal",name:"limit",value:100}],concreteType:"EntityLabelConnection",kind:"LinkedField",name:"entityLabels",plural:!1,selections:[{alias:null,args:null,concreteType:"EntityLabelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"EntityLabel",kind:"LinkedField",name:"node",plural:!1,selections:[k,F,i,Le],storageKey:null}],storageKey:null}],storageKey:"entityLabels(limit:100)"},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[i,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"971e7c2b5c1e92919ee06a44c4e9806e",id:null,metadata:{},name:"ProjectAdminDeploymentsPageQuery",operationKind:"query",text:`query ProjectAdminDeploymentsPageQuery(
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
`}}})();hl.hash="e252fb97e4abec2e8e1bd26d423dc617";const mn=n=>{"use memo";var ul,dl,ml,cl,pl,yl,gl,fl,kl,Fl;const e=vl.c(169),{projectId:y}=n,{t:l}=Il(),{message:d}=$l.useApp(),{logger:m}=Pl(),u=Ml(),i=Vl(),[v,g]=A.useState(null),[I,N]=A.useState(null),L=Rl("deployment"),[c,Ie]=A.useState(null),[h,Le]=A.useState(null);let F;e[0]===Symbol.for("react.memo_cache_sentinel")?(F={current:1,pageSize:10},e[0]=F):F=e[0];const{baiPaginationOption:b,tablePaginationOption:k,setTablePaginationOption:o}=Xl(F);let Ce,je;e[1]===Symbol.for("react.memo_cache_sentinel")?(Ce={filter:xl(cn),order:Sl(an),statusCategory:Sl(["running","finished"]).withDefault("running")},je={history:"replace"},e[1]=Ce,e[2]=je):(Ce=e[1],je=e[2]);const[r,p]=Bl(Ce,je),[qe,ze]=_l("table_column_overrides.ProjectAdminDeploymentsPage"),[he,S]=El();let Ae;e[3]===Symbol.for("react.memo_cache_sentinel")?(Ae=["STOPPED"],e[3]=Ae):Ae=e[3];const rl=Ae;let Ne;e[4]!==r.statusCategory?(Ne=r.statusCategory==="finished"?{status:{in:rl}}:{status:{notIn:rl}},e[4]=r.statusCategory,e[5]=Ne):Ne=e[5];const Qe=Ne;let P;e[6]!==r.filter?(P=r.filter??{},e[6]=r.filter,e[7]=P):P=e[7];let M;e[8]!==Qe||e[9]!==P?(M={...P,...Qe},e[8]=Qe,e[9]=P,e[10]=M):M=e[10];let V;e[11]!==r.order?(V=wl(r.order),e[11]=r.order,e[12]=V):V=e[12];let Pe;e[13]!==b.limit||e[14]!==b.offset||e[15]!==y||e[16]!==M||e[17]!==V?(Pe={projectId:y,filter:M,orderBy:V,limit:b.limit,offset:b.offset},e[13]=b.limit,e[14]=b.offset,e[15]=y,e[16]=M,e[17]=V,e[18]=Pe):Pe=e[18];const sl=Pe,ol=A.useDeferredValue(sl),Te=A.useDeferredValue(he);let Me;e[19]===Symbol.for("react.memo_cache_sentinel")?(Me=hl,e[19]=Me):Me=e[19];const Ge=Te===Ul?"store-and-network":"network-only";let Ve;e[20]!==Te||e[21]!==Ge?(Ve={fetchKey:Te,fetchPolicy:Ge},e[20]=Te,e[21]=Ge,e[22]=Ve):Ve=e[22];const R=Kl.useLazyLoadQuery(Me,ol,Ve);let f,T,Re,x;e[23]!==((ul=R.projectDeployments)==null?void 0:ul.count)||e[24]!==((dl=R.projectDeployments)==null?void 0:dl.edges)||e[25]!==I||e[26]!==v?(f=Ol(ln((ml=R.projectDeployments)==null?void 0:ml.edges,"node")),x=((cl=R.projectDeployments)==null?void 0:cl.count)??0,T=v==null?null:f.find(t=>t.id===v)??null,Re=I==null?null:f.find(t=>t.id===I)??null,e[23]=(pl=R.projectDeployments)==null?void 0:pl.count,e[24]=(yl=R.projectDeployments)==null?void 0:yl.edges,e[25]=I,e[26]=v,e[27]=f,e[28]=T,e[29]=Re,e[30]=x):(f=e[27],T=e[28],Re=e[29],x=e[30]);const s=Re,B=ol!==sl||Te!==he;let xe;e[31]===Symbol.for("react.memo_cache_sentinel")?(xe=Ll,e[31]=xe):xe=e[31];const[He,We]=Kl.useMutation(xe);let _;e[32]!==l?(_=l("deployment.filter.Name"),e[32]=l,e[33]=_):_=e[33];let E;e[34]!==_?(E={key:"name",propertyLabel:_,type:"string"},e[34]=_,e[35]=E):E=e[35];let w;e[36]!==l?(w=l("deployment.filter.EndpointUrl"),e[36]=l,e[37]=w):w=e[37];let O;e[38]!==w?(O={key:"endpointUrl",propertyLabel:w,type:"string"},e[38]=w,e[39]=O):O=e[39];let U;e[40]!==l?(U=l("deployment.filter.OpenToPublic"),e[40]=l,e[41]=U):U=e[41];let $;e[42]!==U?($={key:"openToPublic",propertyLabel:U,type:"boolean"},e[42]=U,e[43]=$):$=e[43];let q;e[44]!==L||e[45]!==l?(q=L?[{key:"labels.some.key",propertyLabel:l("entityLabel.LabelKey"),type:"string"},{key:"labels.some.value",propertyLabel:l("entityLabel.LabelValue"),type:"string"}]:[],e[44]=L,e[45]=l,e[46]=q):q=e[46];let Be;e[47]!==E||e[48]!==O||e[49]!==$||e[50]!==q?(Be=[E,O,$,...q],e[47]=E,e[48]=O,e[49]=$,e[50]=q,e[51]=Be):Be=e[51];const Je=Be;let _e;e[52]===Symbol.for("react.memo_cache_sentinel")?(_e={flexShrink:1},e[52]=_e):_e=e[52];const Tl=r.statusCategory;let z;e[53]!==p||e[54]!==o?(z=t=>{p({statusCategory:t}),o({current:1})},e[53]=p,e[54]=o,e[55]=z):z=e[55];let Q;e[56]!==l?(Q=l("deployment.Running"),e[56]=l,e[57]=Q):Q=e[57];let G;e[58]!==Q?(G=a.jsx(Dl,{value:"running",label:Q}),e[58]=Q,e[59]=G):G=e[59];let H;e[60]!==l?(H=l("deployment.status.Terminated"),e[60]=l,e[61]=H):H=e[61];let W;e[62]!==H?(W=a.jsx(Dl,{value:"finished",label:H}),e[62]=H,e[63]=W):W=e[63];let J;e[64]!==r.statusCategory||e[65]!==z||e[66]!==G||e[67]!==W?(J=a.jsxs(ql,{value:Tl,onChange:z,children:[G,W]}),e[64]=r.statusCategory,e[65]=z,e[66]=G,e[67]=W,e[68]=J):J=e[68];const Ye=r.filter??void 0;let Y;e[69]!==p||e[70]!==o?(Y=t=>{p({filter:t??null}),o({current:1})},e[69]=p,e[70]=o,e[71]=Y):Y=e[71];let X;e[72]!==Je||e[73]!==Ye||e[74]!==Y?(X=a.jsx(tn,{filterProperties:Je,value:Ye,onChange:Y}),e[72]=Je,e[73]=Ye,e[74]=Y,e[75]=X):X=e[75];let Z;e[76]!==J||e[77]!==X?(Z=a.jsxs(il,{gap:"sm",align:"start",wrap:"wrap",style:_e,children:[J,X]}),e[76]=J,e[77]=X,e[78]=Z):Z=e[78];let ee;e[79]!==S?(ee=t=>S(t),e[79]=S,e[80]=ee):ee=e[80];let le;e[81]!==he||e[82]!==B||e[83]!==ee?(le=a.jsx(Wl,{settingId:"project-admin-deployments",defaultAutoUpdateDelay:15e3,loading:B,value:he,onChange:ee}),e[81]=he,e[82]=B,e[83]=ee,e[84]=le):le=e[84];let ne;e[85]!==Z||e[86]!==le?(ne=a.jsxs(il,{justify:"between",wrap:"wrap",gap:"sm",children:[Z,le]}),e[85]=Z,e[86]=le,e[87]=ne):ne=e[87];const Xe=L?Ie:void 0;let ae;e[88]!==p||e[89]!==o?(ae=t=>{p({filter:dn(t)}),o({current:1})},e[88]=p,e[89]=o,e[90]=ae):ae=e[90];let te;e[91]!==p?(te=t=>{p({order:t??null})},e[91]=p,e[92]=te):te=e[92];let ie;e[93]!==o?(ie=(t,C)=>{o({current:t,pageSize:C})},e[93]=o,e[94]=ie):ie=e[94];let re;e[95]!==ie||e[96]!==k.current||e[97]!==k.pageSize||e[98]!==x?(re={current:k.current,pageSize:k.pageSize,total:x,onChange:ie},e[95]=ie,e[96]=k.current,e[97]=k.pageSize,e[98]=x,e[99]=re):re=e[99];let se;e[100]!==qe||e[101]!==ze?(se={columnOverrides:qe,onColumnOverridesChange:ze},e[100]=qe,e[101]=ze,e[102]=se):se=e[102];let oe;e[103]!==i||e[104]!==f||e[105]!==l||e[106]!==u?(oe=t=>{const C=["name","currentRevisionNumber","status","labels","replicaSummary","model","createdAt","owner","id","endpointUrl","updatedAt","openToPublic","resourceGroup","domainName","projectId"],Cl=new Set(["name","currentRevisionNumber","status","labels","replicaSummary","model","createdAt","owner"]);return t.filter(K=>C.includes(K.key)).map(K=>{let Ue=K;return K.key==="name"?Ue={...K,render:(jl,j)=>{var D,$e;const ve=rn((D=j.metadata)==null?void 0:D.status);return a.jsx(sn,{title:(($e=j.metadata)==null?void 0:$e.name)??"-",onTitleClick:()=>u(i(`deployments/${j.entityId}`)),copyable:!0,showActions:"always",actions:[{key:"edit",title:l("deployment.EditDeployment"),icon:a.jsx(Zl,{}),disabled:ve,onClick:()=>g(j.id)},{key:"delete",title:l("deployment.DeleteDeployment"),icon:a.jsx(en,{size:"1em"}),type:"danger",disabled:ve,onClick:()=>N(j.id)}]})}}:K.key==="currentRevisionNumber"&&(Ue={...K,render:(jl,j)=>{const ve=f.find($e=>$e.id===j.id),D=ve==null?void 0:ve.currentRevision;return(D==null?void 0:D.revisionNumber)==null?a.jsx(zl,{color:"secondary",children:"-"}):a.jsx(Ql,{onClick:()=>Le(D),children:`#${D.revisionNumber}`})}}),K.key==="name"?Ue:{...Ue,defaultHidden:!Cl.has(K.key)}})},e[103]=i,e[104]=f,e[105]=l,e[106]=u,e[107]=oe):oe=e[107];let ue;e[108]!==f||e[109]!==B||e[110]!==r.order||e[111]!==Xe||e[112]!==ae||e[113]!==te||e[114]!==re||e[115]!==se||e[116]!==oe?(ue=a.jsx(nn,{onEditLabels:Xe,showLabelsByDefault:!0,onLabelClick:ae,deploymentsFrgmt:f,loading:B,order:r.order,onChangeOrder:te,pagination:re,tableSettings:se,customizeColumns:oe}),e[108]=f,e[109]=B,e[110]=r.order,e[111]=Xe,e[112]=ae,e[113]=te,e[114]=re,e[115]=se,e[116]=oe,e[117]=ue):ue=e[117];let de;e[118]!==ne||e[119]!==ue?(de=a.jsxs(il,{direction:"column",align:"stretch",gap:"sm",children:[ne,ue]}),e[118]=ne,e[119]=ue,e[120]=de):de=e[120];const Ze=!!c;let me;e[121]!==c?(me=c?[{entityId:c.entityId,name:((gl=c.metadata)==null?void 0:gl.name)??void 0}]:[],e[121]=c,e[122]=me):me=e[122];const el=c==null?void 0:c.entityLabels;let ce;e[123]!==S?(ce=t=>{Ie(null),t&&S()},e[123]=S,e[124]=ce):ce=e[124];let pe;e[125]!==Ze||e[126]!==me||e[127]!==el||e[128]!==ce?(pe=a.jsx(on,{open:Ze,entityType:"deployment",targets:me,entityLabelsFrgmt:el,onRequestClose:ce}),e[125]=Ze,e[126]=me,e[127]=el,e[128]=ce,e[129]=pe):pe=e[129];let ye;e[130]!==T?(ye=T!=null&&a.jsx(Jl,{open:!0,deploymentFrgmt:T,onRequestClose:()=>{g(null)}}),e[130]=T,e[131]=ye):ye=e[131];const ll=!!s;let ge;e[132]!==l?(ge=l("deployment.DeleteDeployment"),e[132]=l,e[133]=ge):ge=e[133];let fe;e[134]!==l?(fe=l("deployment.Deployment"),e[134]=l,e[135]=fe):fe=e[135];let ke;e[136]!==s?(ke=s?[{key:s.id,label:((fl=s.metadata)==null?void 0:fl.name)??""}]:[],e[136]=s,e[137]=ke):ke=e[137];const nl=((kl=s==null?void 0:s.metadata)==null?void 0:kl.name)??"",al=((Fl=s==null?void 0:s.metadata)==null?void 0:Fl.name)??"";let Fe;e[138]!==al?(Fe={placeholder:al},e[138]=al,e[139]=Fe):Fe=e[139];let be;e[140]!==We?(be={loading:We},e[140]=We,e[141]=be):be=e[141];let Se;e[142]!==He||e[143]!==s||e[144]!==m||e[145]!==d||e[146]!==l||e[147]!==S?(Se=()=>{s&&He({variables:{input:{id:s.entityId}},onCompleted:(t,C)=>{if(C&&C.length>0){m.error("Failed to delete deployment",C),d.error(l("deployment.FailedToDeleteDeployment"));return}d.success(l("deployment.DeploymentDeleted")),N(null),S()},onError:t=>{m.error("Failed to delete deployment",t),d.error(l("deployment.FailedToDeleteDeployment"))}})},e[142]=He,e[143]=s,e[144]=m,e[145]=d,e[146]=l,e[147]=S,e[148]=Se):Se=e[148];let Ee;e[149]===Symbol.for("react.memo_cache_sentinel")?(Ee=()=>N(null),e[149]=Ee):Ee=e[149];let Ke;e[150]!==ll||e[151]!==ge||e[152]!==fe||e[153]!==ke||e[154]!==nl||e[155]!==Fe||e[156]!==be||e[157]!==Se?(Ke=a.jsx(un,{open:ll,title:ge,target:fe,items:ke,confirmText:nl,requireConfirmInput:!0,inputProps:Fe,okButtonProps:be,onOk:Se,onCancel:Ee}),e[150]=ll,e[151]=ge,e[152]=fe,e[153]=ke,e[154]=nl,e[155]=Fe,e[156]=be,e[157]=Se,e[158]=Ke):Ke=e[158];const tl=!!h;let we;e[159]===Symbol.for("react.memo_cache_sentinel")?(we=()=>Le(null),e[159]=we):we=e[159];let De;e[160]!==h||e[161]!==tl?(De=a.jsx(Gl,{children:a.jsx(Yl,{open:tl,revisionFrgmt:h,onClose:we})}),e[160]=h,e[161]=tl,e[162]=De):De=e[162];let Oe;return e[163]!==de||e[164]!==pe||e[165]!==ye||e[166]!==Ke||e[167]!==De?(Oe=a.jsxs(a.Fragment,{children:[de,pe,ye,Ke,De]}),e[163]=de,e[164]=pe,e[165]=ye,e[166]=Ke,e[167]=De,e[168]=Oe):Oe=e[168],Oe},da=()=>{"use memo";const n=vl.c(9),{t:e}=Il(),y=Al();let l;n[0]!==e?(l=e("webui.menu.ProjectDeployments"),n[0]=e,n[1]=l):l=n[1];let d;n[2]===Symbol.for("react.memo_cache_sentinel")?(d={header:{borderBottom:"none"},body:{paddingTop:0}},n[2]=d):d=n[2];let m;n[3]===Symbol.for("react.memo_cache_sentinel")?(m=a.jsx(bl,{}),n[3]=m):m=n[3];let u;n[4]!==y.id?(u=a.jsx(Nl,{children:a.jsx(A.Suspense,{fallback:m,children:y.id?a.jsx(mn,{projectId:y.id}):a.jsx(bl,{})})}),n[4]=y.id,n[5]=u):u=n[5];let i;return n[6]!==l||n[7]!==u?(i=a.jsx(Hl,{variant:"borderless",title:l,styles:d,children:u}),n[6]=l,n[7]=u,n[8]=i):i=n[8],i};function cn(n){return typeof n=="object"&&n!==null&&!Array.isArray(n)?n:{}}export{da as default};
//# sourceMappingURL=ProjectAdminDeploymentsPage-DZg95uSF.js.map
