import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{V as t,Zn as n}from"./icons-Btg1s2wy.js";import{t as r}from"./compiler-runtime-CZQb2eIb.js";import{Mt as i,_t as a,ht as o,mt as s,vt as c}from"./lodash-ClfL87UH.js";/* empty css            */import{t as l}from"./jsx-runtime-BapUIyWk.js";import{R as u,_ as d}from"./usePressFeedback-BIoIGSxE.js";import{O as f,f as ee}from"./DefaultProviders-BFjPhnQa.js";import{t as p}from"./IconButton-DGkWhkpU.js";import{r as te}from"./Skeleton-D35z7Ria.js";import{t as ne}from"./BAIFlex-BElkJeHW.js";import{t as re}from"./app-shim-DTEBzR8d.js";import{H as ie,d as ae,y as oe}from"./helper-BWFKT_2Y.js";import{r as m}from"./hooks-UUY7pxyu.js";import{t as se}from"./react-relay-BfoHYpUf.js";import{l as h,u as ce}from"./helper-DF1Eunoe.js";import{t as le}from"./BAISelect-D7nL9svF.js";import{t as g}from"./BAIGraphQLPropertyFilter-CNTUQIkF.js";import{t as _}from"./BAIText-CtDfjLnS.js";import{t as v}from"./BAISkeleton-MIjJv1Hr.js";import{t as ue}from"./BAIModal-XZIjYM23.js";import{t as de}from"./BAIBulkErrorModal-DLhpdmCU.js";import{t as y}from"./CheckboxInput-DinsfW7h.js";import{t as fe}from"./BAISelectionLabel-BTMbVxpE.js";import{i as pe,n as b,r as me,t as he}from"./sessionStatusBuckets-BAkxkeqQ.js";import{n as x,t as S}from"./BAISegmentedControlItem-erYb9KqU.js";import{t as C}from"./BAINameActionCell-BaFf27s9.js";import{t as w}from"./BAIEntityLabelSettingModal-BzN4qIYx.js";import{i as ge}from"./BAIEntityLabelCell-DOyaclRH.js";import{t as _e}from"./BAIEntityLabelBulkEditButton-CRMSgz-m.js";import{t as ve}from"./BAIScopedUserSelect-D4mVPPjA.js";import{i as T,n as ye,o as be}from"./dist-C3M-rFln.js";import{t as E}from"./useCurrentProject-BaleCvMA.js";import{N as D,ht as O,pt as k}from"./index-49VU5B_r.js";import{t as xe}from"./AutoUpdateFetchKeyButton-C-RHyKup.js";import{n as Se}from"./reactPaginationQueryOptions-DUCwh22X.js";var Ce=r(),A=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`filter`},t={defaultValue:null,kind:`LocalArgument`,name:`limit`},n={defaultValue:null,kind:`LocalArgument`,name:`offset`},r={defaultValue:null,kind:`LocalArgument`,name:`orderBy`},i={defaultValue:null,kind:`LocalArgument`,name:`projectId`},a=[{kind:`Variable`,name:`filter`,variableName:`filter`},{kind:`Variable`,name:`limit`,variableName:`limit`},{kind:`Variable`,name:`offset`,variableName:`offset`},{kind:`Variable`,name:`orderBy`,variableName:`orderBy`},{fields:[{items:[{fields:[{kind:`Variable`,name:`value`,variableName:`projectId`}],kind:`ObjectValue`,name:`project.0`}],kind:`ListValue`,name:`project`}],kind:`ObjectValue`,name:`scope`}],o={alias:null,args:null,kind:`ScalarField`,name:`count`,storageKey:null},s={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},c={alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},l={alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},u=[l],d=[{alias:null,args:null,concreteType:`ResourceSlotEntry`,kind:`LinkedField`,name:`entries`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`resourceType`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`quantity`,storageKey:null}],storageKey:null}],f={alias:null,args:null,kind:`ScalarField`,name:`key`,storageKey:null},ee={alias:null,args:null,kind:`ScalarField`,name:`value`,storageKey:null},p=[f,ee];return{fragment:{argumentDefinitions:[e,t,n,r,i],kind:`Fragment`,metadata:null,name:`ProjectAdminSessionPageQuery`,selections:[{alias:null,args:a,concreteType:`SessionV2Connection`,kind:`LinkedField`,name:`scopedSessionsV2`,plural:!1,selections:[o,{alias:null,args:null,concreteType:`SessionV2Edge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`SessionV2`,kind:`LinkedField`,name:`node`,plural:!1,selections:[s,c,{alias:null,args:null,concreteType:`SessionV2MetadataInfo`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:u,storageKey:null},{args:null,kind:`FragmentSpread`,name:`BAISessionNodesV2Fragment`},{args:null,kind:`FragmentSpread`,name:`TerminateSessionModalForProjectAdminFragment`}],storageKey:null}],storageKey:null}],storageKey:null}],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[i,e,r,t,n],kind:`Operation`,name:`ProjectAdminSessionPageQuery`,selections:[{alias:null,args:a,concreteType:`SessionV2Connection`,kind:`LinkedField`,name:`scopedSessionsV2`,plural:!1,selections:[o,{alias:null,args:null,concreteType:`SessionV2Edge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`SessionV2`,kind:`LinkedField`,name:`node`,plural:!1,selections:[s,c,{alias:null,args:null,concreteType:`SessionV2MetadataInfo`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:[l,{alias:null,args:null,kind:`ScalarField`,name:`sessionType`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`clusterMode`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`clusterSize`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ProjectV2`,kind:`LinkedField`,name:`project`,plural:!1,selections:[s,{alias:null,args:null,concreteType:`ProjectBasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:u,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`SessionV2LifecycleInfo`,kind:`LinkedField`,name:`lifecycle`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`createdAt`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`terminatedAt`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`SessionV2ResourceInfo`,kind:`LinkedField`,name:`resource`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`resourceGroupName`,storageKey:null},{alias:null,args:null,concreteType:`ResourceAllocation`,kind:`LinkedField`,name:`allocation`,plural:!1,selections:[{alias:null,args:null,concreteType:`ResourceSlot`,kind:`LinkedField`,name:`requested`,plural:!1,selections:d,storageKey:null},{alias:null,args:null,concreteType:`ResourceSlot`,kind:`LinkedField`,name:`used`,plural:!1,selections:d,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ImageV2Connection`,kind:`LinkedField`,name:`images`,plural:!1,selections:[{alias:null,args:null,concreteType:`ImageV2Edge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ImageV2`,kind:`LinkedField`,name:`node`,plural:!1,selections:[s,{alias:null,args:null,concreteType:`ImageV2IdentityInfo`,kind:`LinkedField`,name:`identity`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`canonicalName`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`architecture`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ImageV2MetadataInfo`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:[{alias:null,args:null,concreteType:`ImageV2TagEntry`,kind:`LinkedField`,name:`tags`,plural:!0,selections:p,storageKey:null},{alias:null,args:null,concreteType:`ImageV2LabelEntry`,kind:`LinkedField`,name:`labels`,plural:!0,selections:p,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`UserV2`,kind:`LinkedField`,name:`user`,plural:!1,selections:[s,{alias:null,args:null,concreteType:`UserV2BasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`email`,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:[{kind:`Literal`,name:`limit`,value:100}],concreteType:`EntityLabelConnection`,kind:`LinkedField`,name:`entityLabels`,plural:!1,selections:[{alias:null,args:null,concreteType:`EntityLabelEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`EntityLabel`,kind:`LinkedField`,name:`node`,plural:!1,selections:[f,ee,s,{alias:null,args:null,kind:`ScalarField`,name:`fieldId`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:`entityLabels(limit:100)`},{alias:null,args:null,concreteType:`KernelV2Connection`,kind:`LinkedField`,name:`kernels`,plural:!1,selections:[{alias:null,args:null,concreteType:`KernelV2Edge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`KernelV2`,kind:`LinkedField`,name:`node`,plural:!1,selections:[s,{alias:null,args:null,concreteType:`KernelV2ResourceInfo`,kind:`LinkedField`,name:`resource`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`agentId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`containerId`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:`34c9d9ad1370e504253cc173852247e6`,id:null,metadata:{},name:`ProjectAdminSessionPageQuery`,operationKind:`query`,text:`query ProjectAdminSessionPageQuery(
  $projectId: UUID!
  $filter: SessionV2Filter
  $orderBy: [SessionV2OrderBy!]
  $limit: Int
  $offset: Int
) {
  scopedSessionsV2(scope: {project: [{value: $projectId}]}, filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
    count
    edges {
      node {
        id
        entityId
        metadata {
          name
        }
        ...BAISessionNodesV2Fragment
        ...TerminateSessionModalForProjectAdminFragment
      }
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

fragment BAISessionClusterModeV2Fragment on SessionV2MetadataInfo {
  clusterMode
  clusterSize
}

fragment BAISessionNodesV2Fragment on SessionV2 {
  id
  entityId
  project {
    id
    basicInfo {
      name
    }
  }
  metadata {
    name
    ...BAISessionTypeTokenV2Fragment
    ...BAISessionClusterModeV2Fragment
  }
  lifecycle {
    status
    createdAt
    terminatedAt
  }
  resource {
    resourceGroupName
    allocation {
      requested {
        entries {
          resourceType
          quantity
        }
      }
      used {
        entries {
          resourceType
          quantity
        }
      }
    }
  }
  images {
    edges {
      node {
        id
        ...BAIImageNodeSimpleTagV2Fragment
      }
    }
  }
  user {
    id
    basicInfo {
      email
    }
  }
  entityLabels(limit: 100) {
    ...BAIEntityLabelTokensFragment
    ...BAIEntityLabelSettingModalFragment
  }
}

fragment BAISessionTypeTokenV2Fragment on SessionV2MetadataInfo {
  sessionType
}

fragment TerminateSessionModalForProjectAdminFragment on SessionV2 {
  id
  entityId
  metadata {
    name
  }
  kernels {
    edges {
      node {
        id
        resource {
          agentId
          containerId
        }
      }
    }
  }
}
`}}})();A.hash=`dffdafc4db1a23f3470e7b6f8aa0dcd1`;var j=(function(){var e={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null};return{argumentDefinitions:[],kind:`Fragment`,metadata:{plural:!0},name:`TerminateSessionModalForProjectAdminFragment`,selections:[e,{alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},{alias:null,args:null,concreteType:`SessionV2MetadataInfo`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`KernelV2Connection`,kind:`LinkedField`,name:`kernels`,plural:!1,selections:[{alias:null,args:null,concreteType:`KernelV2Edge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`KernelV2`,kind:`LinkedField`,name:`node`,plural:!1,selections:[e,{alias:null,args:null,concreteType:`KernelV2ResourceInfo`,kind:`LinkedField`,name:`resource`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`agentId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`containerId`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:`SessionV2`,abstractKey:null}})();j.hash=`7012eaf26b1804672778ddb998dd1c1e`;var M=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`input`}],t={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},n=[{alias:null,args:[{kind:`Variable`,name:`input`,variableName:`input`}],concreteType:`PartialBulkTerminateSessionsPayload`,kind:`LinkedField`,name:`partialBulkTerminateSessionsV2`,plural:!1,selections:[{alias:null,args:null,concreteType:`SessionTerminationInfo`,kind:`LinkedField`,name:`successes`,plural:!0,selections:[t],storageKey:null},{alias:null,args:null,concreteType:`PartialBulkFailure`,kind:`LinkedField`,name:`failed`,plural:!0,selections:[t,{alias:null,args:null,kind:`ScalarField`,name:`message`,storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`TerminateSessionModalForProjectAdminMutation`,selections:n,type:`Mutation`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`TerminateSessionModalForProjectAdminMutation`,selections:n},params:{cacheID:`813ed9b29eaf96d4b79345999ddd9b4a`,id:null,metadata:{},name:`TerminateSessionModalForProjectAdminMutation`,operationKind:`mutation`,text:`mutation TerminateSessionModalForProjectAdminMutation(
  $input: PartialBulkTerminateSessionsInput!
) {
  partialBulkTerminateSessionsV2(input: $input) {
    successes {
      id
    }
    failed {
      id
      message
    }
  }
}
`}}})();M.hash=`0c40238a78ac4d415a26d0857ec09d7f`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var N=e(n(),1),we=se(),P=l(),Te=e=>{"use memo";var t;let n=(0,Ce.c)(51),r,l,f;n[0]===e?(r=n[1],l=n[2],f=n[3]):({sessionsFrgmt:f,onRequestClose:l,...r}=e,n[0]=e,n[1]=r,n[2]=l,n[3]=f);let{t:p}=te(),{token:ie}=d(),{message:ae}=re.useApp(),oe=ee(),[m,se]=(0,N.useState)(!1),[h,le]=(0,N.useState)(null),g=ce((0,we.useFragment)(j,f)),[v,fe]=(0,we.useMutation)(M),pe;n[4]===l?pe=n[5]:(pe=(e,t)=>{se(!1),l(e,t)},n[4]=l,n[5]=pe);let b=pe,me=(e,t)=>{let n=p(`session.TerminateSessionsPartialFailureDescription`,{failed:e.length,total:g.length});ae.error(n),le({failures:e,total:g.length,terminatedCount:t})},he=e=>{me(g.map(t=>{var n;return{key:t.entityId,name:((n=t.metadata)==null?void 0:n.name)??t.entityId,message:e}}),0)},x;n[6]===p?x=n[7]:(x=p(`session.SessionName`),n[6]=p,n[7]=x);let S;n[8]===x?S=n[9]:(S={key:`name`,title:x,dataIndex:`name`},n[8]=x,n[9]=S);let C;n[10]===p?C=n[11]:(C=p(`dialog.error.Error`),n[10]=p,n[11]=C);let w;n[12]===C?w=n[13]:(w={key:`message`,title:C,dataIndex:`message`},n[12]=C,n[13]=w);let ge;n[14]!==S||n[15]!==w?(ge=[S,w],n[14]=S,n[15]=w,n[16]=ge):ge=n[16];let _e=ge,ve=s(i(a(g,Ee)),I),T;n[17]===p?T=n[18]:(T=p(`session.TerminateSession`),n[17]=p,n[18]=T);let ye;n[19]!==m||n[20]!==p?(ye=p(m?`button.ForceTerminate`:`session.Terminate`),n[19]=m,n[20]=p,n[21]=ye):ye=n[21];let be=m?`primary`:`default`,E;n[22]===be?E=n[23]:(E={type:be},n[22]=be,n[23]=E);let D;n[24]===b?D=n[25]:(D=()=>b(!1),n[24]=b,n[25]=D);let k;n[26]===p?k=n[27]:(k=p(`userSettings.SessionTerminationDialog`),n[26]=p,n[27]=k);let xe;n[28]===k?xe=n[29]:(xe=(0,P.jsx)(u,{children:k}),n[28]=k,n[29]=xe);let Se;n[30]===Symbol.for(`react.memo_cache_sentinel`)?(Se=e=>se(e),n[30]=Se):Se=n[30];let A;n[31]===p?A=n[32]:(A=p(`button.ForceTerminate`),n[31]=p,n[32]=A);let Te;n[33]!==m||n[34]!==A?(Te=(0,P.jsx)(y,{value:m,onChange:Se,children:A}),n[33]=m,n[34]=A,n[35]=Te):Te=n[35];let F=!!h,ke=(h==null?void 0:h.failures.length)??0,L=(h==null?void 0:h.total)??0,R;n[36]!==p||n[37]!==ke||n[38]!==L?(R=p(`session.TerminateSessionsPartialFailureDescription`,{failed:ke,total:L}),n[36]=p,n[37]=ke,n[38]=L,n[39]=R):R=n[39];let z;n[40]===(h==null?void 0:h.failures)?z=n[41]:(z=(h==null?void 0:h.failures)??[],n[40]=h==null?void 0:h.failures,n[41]=z);let B;n[42]!==h||n[43]!==b?(B=()=>{le(null),h&&h.terminatedCount>0&&b(!0,h.failures.map(je))},n[42]=h,n[43]=b,n[44]=B):B=n[44];let Me;return n[45]!==_e||n[46]!==F||n[47]!==R||n[48]!==z||n[49]!==B?(Me=(0,P.jsx)(de,{open:F,alertDescription:R,columns:_e,dataSource:z,onRequestClose:B}),n[45]=_e,n[46]=F,n[47]=R,n[48]=z,n[49]=B,n[50]=Me):Me=n[50],(0,P.jsxs)(P.Fragment,{children:[(0,P.jsx)(ue,{centered:!0,title:T,okText:ye,okType:`danger`,okButtonProps:E,confirmLoading:fe,onOk:()=>{g.length===0?b(!1):v({variables:{input:{ids:g.map(De),forced:m}},onCompleted:(e,t)=>{if(t&&t.length>0){var n;he(((n=t[0])==null?void 0:n.message)??p(`general.ErrorOccurred`));return}let{successes:r,failed:i}=e.partialBulkTerminateSessionsV2;if(i.length===0){ae.success(p(`session.SessionTerminated`)),b(!0);return}let a=o(g.map(Oe));me(i.map(e=>({key:e.id,name:a[e.id]??e.id,message:e.message})),r.length)},onError:e=>{he(e.message)}})},onCancel:D,...r,children:(0,P.jsxs)(ne,{className:`terminate-session-modal-admin-list`,direction:`column`,align:`stretch`,gap:`xs`,children:[xe,(0,P.jsx)(_,{mark:!0,children:g.length===1?((t=g[0])==null||(t=t.metadata)==null?void 0:t.name)??``:`${g.length} sessions`}),Te,m&&(0,P.jsxs)(O,{styles:{body:{padding:ie(`--spacing-4`)}},children:[(0,P.jsx)(u,{as:`p`,display:`block`,color:`danger`,children:p(`session.ForceTerminateWarningMsg`)}),(0,P.jsxs)(`ul`,{children:[(0,P.jsx)(`li`,{children:p(`session.ForceTerminateWarningMsg2`)}),(0,P.jsx)(`li`,{children:p(`session.ForceTerminateWarningMsg3`)})]}),oe===`superadmin`&&(0,P.jsx)(O,{type:`inner`,title:p(`session.ContainerToCleanUp`),children:c(ve,Ae)})]})]})}),Me]})};function F(e){return e==null?void 0:e.node}function Ee(e){var t;return(t=e.kernels)==null||(t=t.edges)==null?void 0:t.map(F)}function I(e){var t;return(e==null||(t=e.resource)==null?void 0:t.agentId)??`-`}function De(e){return e.entityId}function Oe(e){var t;return[e.entityId,(t=e.metadata)==null?void 0:t.name]}function ke(e){var t;return(0,P.jsx)(`li`,{children:(0,P.jsx)(_,{copyable:!0,children:(e==null||(t=e.resource)==null?void 0:t.containerId)??``})},e==null?void 0:e.id)}function Ae(e,t){return(0,P.jsxs)(N.Fragment,{children:[t,(0,P.jsx)(`ul`,{children:e.map(ke)})]},t)}function je(e){return e.key}
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var L=e=>{"use memo";var n,r;let i=(0,Ce.c)(149),{projectId:a}=e,{t:o}=te(),s;i[0]===Symbol.for(`react.memo_cache_sentinel`)?(s=[],i[0]=s):s=i[0];let[c,l]=(0,N.useState)(s),u;i[1]===Symbol.for(`react.memo_cache_sentinel`)?(u=[],i[1]=u):u=i[1];let[d,ee]=(0,N.useState)(u),[re,se]=(0,N.useState)(!1),_=k(`session`),[v,ue]=(0,N.useState)(null),de;i[2]===Symbol.for(`react.memo_cache_sentinel`)?(de={current:1,pageSize:10},i[2]=de):de=i[2];let{baiPaginationOption:y,tablePaginationOption:E,setTablePaginationOption:D}=Se(de),O,j;i[3]===Symbol.for(`react.memo_cache_sentinel`)?(O={statusCategory:T(b).withDefault(`running`),order:T(pe),filter:ye(z)},j={history:`replace`},i[3]=O,i[4]=j):(O=i[3],j=i[4]);let[M,F]=be(O,j),[Ee,I]=m(),De=ie(),Oe;i[5]===De?Oe=i[6]:(Oe=he(De.isManagerVersionCompatibleWith(`26.8.0`)),i[5]=De,i[6]=Oe);let ke=Oe,[Ae,je]=f(`table_column_overrides.ProjectAdminSessionPage`),L=ke[M.statusCategory],R;i[7]===L?R=i[8]:(R={in:L},i[7]=L,i[8]=R);let Pe=R,V;i[9]===M.filter?V=i[10]:(V=M.filter??{},i[9]=M.filter,i[10]=V);let H;i[11]!==Pe||i[12]!==V?(H={...V,status:Pe},i[11]=Pe,i[12]=V,i[13]=H):H=i[13];let U;i[14]===M.order?U=i[15]:(U=ae(M.order)??[{field:`CREATED_AT`,direction:`DESC`}],i[14]=M.order,i[15]=U);let Fe;i[16]!==y.limit||i[17]!==y.offset||i[18]!==a||i[19]!==H||i[20]!==U?(Fe={projectId:a,filter:H,orderBy:U,limit:y.limit,offset:y.offset},i[16]=y.limit,i[17]=y.offset,i[18]=a,i[19]=H,i[20]=U,i[21]=Fe):Fe=i[21];let Ie=Fe,Le=(0,N.useDeferredValue)(Ie),Re=(0,N.useDeferredValue)(Ee),ze=Re===`first`?`store-and-network`:`network-only`,Be;i[22]!==Re||i[23]!==ze?(Be={fetchKey:Re,fetchPolicy:ze},i[22]=Re,i[23]=ze,i[24]=Be):Be=i[24];let Ve=(0,we.useLazyLoadQuery)(A,Le,Be),He;if(i[25]!==((n=Ve.scopedSessionsV2)==null?void 0:n.edges)){var Ue,We;He=ce((Ue=Ve.scopedSessionsV2)==null||(Ue=Ue.edges)==null?void 0:Ue.map(B)),i[25]=(We=Ve.scopedSessionsV2)==null?void 0:We.edges,i[26]=He}else He=i[26];let W=He,Ge=((r=Ve.scopedSessionsV2)==null?void 0:r.count)??0,Ke;i[27]===Symbol.for(`react.memo_cache_sentinel`)?(Ke=e=>{ee(e),se(!0)},i[27]=Ke):Ke=i[27];let qe=Ke,G=Le!==Ie||Re!==Ee,Je;i[28]===Symbol.for(`react.memo_cache_sentinel`)?(Je={flexShrink:1},i[28]=Je):Je=i[28];let Ye=M.statusCategory,K;i[29]!==F||i[30]!==D?(K=e=>{F({statusCategory:e}),D({current:1})},i[29]=F,i[30]=D,i[31]=K):K=i[31];let q;i[32]===o?q=i[33]:(q=o(`session.Running`),i[32]=o,i[33]=q);let J;i[34]===q?J=i[35]:(J=(0,P.jsx)(S,{value:`running`,label:q}),i[34]=q,i[35]=J);let Y;i[36]===o?Y=i[37]:(Y=o(`session.Finished`),i[36]=o,i[37]=Y);let X;i[38]===Y?X=i[39]:(X=(0,P.jsx)(S,{value:`finished`,label:Y}),i[38]=Y,i[39]=X);let Z;i[40]!==M.statusCategory||i[41]!==K||i[42]!==J||i[43]!==X?(Z=(0,P.jsxs)(x,{value:Ye,onChange:K,children:[J,X]}),i[40]=M.statusCategory,i[41]=K,i[42]=J,i[43]=X,i[44]=Z):Z=i[44];let Xe;i[45]===Symbol.for(`react.memo_cache_sentinel`)?(Xe={key:`id`,propertyLabel:`ID`,type:`uuid`},i[45]=Xe):Xe=i[45];let Q;i[46]===o?Q=i[47]:(Q=o(`session.SessionName`),i[46]=o,i[47]=Q);let $;i[48]===Q?$=i[49]:($={key:`name`,propertyLabel:Q,type:`string`},i[48]=Q,i[49]=$);let Ze;i[50]===o?Ze=i[51]:(Ze=o(`session.Owner`),i[50]=o,i[51]=Ze);let Qe;i[52]!==a||i[53]!==o?(Qe=e=>{let{onAddCondition:t,value:n,isDisabled:r}=e;return(0,P.jsx)(N.Suspense,{fallback:(0,P.jsx)(le,{disabled:!0,loading:!0}),children:(0,P.jsx)(ve,{scope:{project:[{value:a}]},valuePropName:`id`,label:o(`session.Owner`),isLabelHidden:!0,value:n,isDisabled:r,onChange:(e,n)=>{var r;return t(e,Array.isArray(n)?(r=n[0])==null?void 0:r.label:n==null?void 0:n.label)}})})},i[52]=a,i[53]=o,i[54]=Qe):Qe=i[54];let $e;i[55]!==Ze||i[56]!==Qe?($e={key:`userUuid`,propertyLabel:Ze,type:`uuid`,renderInput:Qe},i[55]=Ze,i[56]=Qe,i[57]=$e):$e=i[57];let et;i[58]!==_||i[59]!==o?(et=_?[{key:`labels.some.key`,propertyLabel:o(`entityLabel.LabelKey`),type:`string`},{key:`labels.some.value`,propertyLabel:o(`entityLabel.LabelValue`),type:`string`}]:[],i[58]=_,i[59]=o,i[60]=et):et=i[60];let tt;i[61]!==$||i[62]!==$e||i[63]!==et?(tt=[Xe,$,$e,...et],i[61]=$,i[62]=$e,i[63]=et,i[64]=tt):tt=i[64];let nt=M.filter??void 0,rt;i[65]!==F||i[66]!==D?(rt=e=>{F({filter:e??null}),D({current:1})},i[65]=F,i[66]=D,i[67]=rt):rt=i[67];let it;i[68]!==tt||i[69]!==nt||i[70]!==rt?(it=(0,P.jsx)(g,{filterProperties:tt,value:nt,onChange:rt}),i[68]=tt,i[69]=nt,i[70]=rt,i[71]=it):it=i[71];let at;i[72]!==Z||i[73]!==it?(at=(0,P.jsxs)(ne,{gap:`sm`,align:`start`,wrap:`wrap`,style:Je,children:[Z,it]}),i[72]=Z,i[73]=it,i[74]=at):at=i[74];let ot;i[75]!==c||i[76]!==o||i[77]!==I?(ot=c.length>0&&(0,P.jsxs)(P.Fragment,{children:[(0,P.jsx)(fe,{count:c.length,onClearSelection:()=>l([])}),(0,P.jsx)(_e,{entityType:`session`,targets:c.map(Me),onLabelsChanged:()=>I()}),(0,P.jsx)(p,{label:o(`session.TerminateSession`),tooltip:o(`session.TerminateSession`),icon:(0,P.jsx)(t,{color:`var(--color-error)`}),onClick:()=>qe(c)})]}),i[75]=c,i[76]=o,i[77]=I,i[78]=ot):ot=i[78];let st;i[79]===I?st=i[80]:(st=e=>I(e),i[79]=I,i[80]=st);let ct;i[81]!==Ee||i[82]!==G||i[83]!==st?(ct=(0,P.jsx)(xe,{settingId:`project-admin-session`,defaultAutoUpdateDelay:15e3,loading:G,value:Ee,onChange:st}),i[81]=Ee,i[82]=G,i[83]=st,i[84]=ct):ct=i[84];let lt;i[85]!==ot||i[86]!==ct?(lt=(0,P.jsxs)(ne,{gap:`xs`,children:[ot,ct]}),i[85]=ot,i[86]=ct,i[87]=lt):lt=i[87];let ut;i[88]!==at||i[89]!==lt?(ut=(0,P.jsxs)(ne,{direction:`row`,justify:`between`,wrap:`wrap`,gap:`sm`,children:[at,lt]}),i[88]=at,i[89]=lt,i[90]=ut):ut=i[90];let dt=_?ue:void 0,ft;i[91]!==F||i[92]!==D?(ft=e=>{F({filter:ge(e)}),D({current:1})},i[91]=F,i[92]=D,i[93]=ft):ft=i[93];let pt=M.order,mt;i[94]===F?mt=i[95]:(mt=e=>{F({order:e})},i[94]=F,i[95]=mt);let ht;if(i[96]!==c||i[97]!==W){let e;i[99]===W?e=i[100]:(e=e=>{oe(e,W,l)},i[99]=W,i[100]=e);let t;i[101]===c?t=i[102]:(t=c.map(Ne),i[101]=c,i[102]=t),ht={type:`checkbox`,preserveSelectedRowKeys:!0,getCheckboxProps(e){var t;let n=(t=e.lifecycle)==null?void 0:t.status;return{disabled:!!n&&[`TERMINATED`,`CANCELLED`,`TERMINATING`].includes(n)}},onChange:e,selectedRowKeys:t},i[96]=c,i[97]=W,i[98]=ht}else ht=i[98];let gt;i[103]!==W||i[104]!==o?(gt=e=>e.map(e=>e.key===`name`?{...e,render:(e,n)=>{var r,i;let a=(r=n.lifecycle)==null?void 0:r.status,s=!!a&&[`TERMINATED`,`CANCELLED`,`TERMINATING`].includes(a),c=W.find(e=>e.id===n.id);return(0,P.jsx)(C,{title:((i=n.metadata)==null?void 0:i.name)??`-`,showActions:`always`,actions:h([{key:`terminate`,title:o(`session.TerminateSession`),icon:(0,P.jsx)(t,{}),type:`danger`,disabled:s||!c,onClick:()=>c&&qe([c])}])})}}:e),i[103]=W,i[104]=o,i[105]=gt):gt=i[105];let _t;i[106]===D?_t=i[107]:(_t=(e,t)=>{D({current:e,pageSize:t})},i[106]=D,i[107]=_t);let vt;i[108]!==_t||i[109]!==E.current||i[110]!==E.pageSize||i[111]!==Ge?(vt={current:E.current,pageSize:E.pageSize,total:Ge,onChange:_t},i[108]=_t,i[109]=E.current,i[110]=E.pageSize,i[111]=Ge,i[112]=vt):vt=i[112];let yt;i[113]===Symbol.for(`react.memo_cache_sentinel`)?(yt={environment:{hidden:!1},resourceGroup:{hidden:!1},sessionType:{hidden:!1},clusterMode:{hidden:!1},createdAt:{hidden:!1}},i[113]=yt):yt=i[113];let bt;i[114]!==Ae||i[115]!==je?(bt={columnOverrides:Ae,defaultColumnOverrides:yt,onColumnOverridesChange:je},i[114]=Ae,i[115]=je,i[116]=bt):bt=i[116];let xt;i[117]!==G||i[118]!==M.order||i[119]!==W||i[120]!==dt||i[121]!==ft||i[122]!==mt||i[123]!==ht||i[124]!==gt||i[125]!==vt||i[126]!==bt?(xt=(0,P.jsx)(me,{onEditLabels:dt,showLabelsByDefault:!0,onLabelClick:ft,sessionsFrgmt:W,loading:G,order:pt,onChangeOrder:mt,rowSelection:ht,customizeColumns:gt,pagination:vt,tableSettings:bt}),i[117]=G,i[118]=M.order,i[119]=W,i[120]=dt,i[121]=ft,i[122]=mt,i[123]=ht,i[124]=gt,i[125]=vt,i[126]=bt,i[127]=xt):xt=i[127];let St=!!v,Ct;if(i[128]!==v){var wt;Ct=v?[{entityId:v.entityId,name:((wt=v.metadata)==null?void 0:wt.name)??void 0}]:[],i[128]=v,i[129]=Ct}else Ct=i[129];let Tt=v==null?void 0:v.entityLabels,Et;i[130]===I?Et=i[131]:(Et=e=>{ue(null),e&&I()},i[130]=I,i[131]=Et);let Dt;i[132]!==St||i[133]!==Ct||i[134]!==Tt||i[135]!==Et?(Dt=(0,P.jsx)(w,{open:St,entityType:`session`,targets:Ct,entityLabelsFrgmt:Tt,onRequestClose:Et}),i[132]=St,i[133]=Ct,i[134]=Tt,i[135]=Et,i[136]=Dt):Dt=i[136];let Ot;i[137]!==d||i[138]!==I?(Ot=(e,t)=>{se(!1),e&&(l(d.filter(e=>t==null?void 0:t.includes(e.entityId))),I())},i[137]=d,i[138]=I,i[139]=Ot):Ot=i[139];let kt;i[140]!==re||i[141]!==Ot||i[142]!==d?(kt=(0,P.jsx)(Te,{open:re,sessionsFrgmt:d,onRequestClose:Ot}),i[140]=re,i[141]=Ot,i[142]=d,i[143]=kt):kt=i[143];let At;return i[144]!==ut||i[145]!==xt||i[146]!==Dt||i[147]!==kt?(At=(0,P.jsxs)(ne,{direction:`column`,align:`stretch`,gap:`sm`,children:[ut,xt,Dt,kt]}),i[144]=ut,i[145]=xt,i[146]=Dt,i[147]=kt,i[148]=At):At=i[148],At},R=()=>{"use memo";let e=(0,Ce.c)(9),{t}=te(),n=E(),r;e[0]===t?r=e[1]:(r=t(`webui.menu.ProjectSessions`),e[0]=t,e[1]=r);let i;e[2]===Symbol.for(`react.memo_cache_sentinel`)?(i={header:{borderBottom:`none`},body:{paddingTop:0}},e[2]=i):i=e[2];let a;e[3]===Symbol.for(`react.memo_cache_sentinel`)?(a=(0,P.jsx)(v,{}),e[3]=a):a=e[3];let o;e[4]===n.id?o=e[5]:(o=(0,P.jsx)(D,{children:(0,P.jsx)(N.Suspense,{fallback:a,children:n.id?(0,P.jsx)(L,{projectId:n.id}):(0,P.jsx)(v,{})})}),e[4]=n.id,e[5]=o);let s;return e[6]!==r||e[7]!==o?(s=(0,P.jsx)(P.Fragment,{children:(0,P.jsx)(O,{variant:`borderless`,title:r,styles:i,children:o})}),e[6]=r,e[7]=o,e[8]=s):s=e[8],s};function z(e){return e}function B(e){return e==null?void 0:e.node}function Me(e){var t;return{entityId:e.entityId,name:((t=e.metadata)==null?void 0:t.name)??void 0}}function Ne(e){return e.id}export{R as default};
