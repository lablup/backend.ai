import{ad as ye,i as B,a6 as ae,a1 as De,j as n,B as P,bO as L,f as Ye,cK as He,cJ as Fe,c8 as le,b6 as Pe,gv as je,A as Me,bJ as Re,b3 as de,N as te,t as re,a7 as We,gw as Xe,aq as J,aN as Ae,m as ne,O as ge,z as Ke,ac as Le,a$ as Ze,bd as en,h as nn,u as Ce,r as E,aX as tn,v as an,an as ln,dr as rn,cV as sn,F as fe,ce as ke,bY as on,P as cn,dn,c_ as un,a8 as mn,J as gn,c1 as fn,bG as pn,ax as pe,$ as An,a0 as vn,aY as yn,T as ve,aD as Fn,bK as Te,D as q,cf as Rn,ft as In,ak as he,a9 as kn,a5 as Tn}from"./index-M9a7wauv.js";import{F as hn}from"./folder-input-C87e8JTe.js";import{B as Sn}from"./BAIVFolderSelect-BWLBqXyA.js";import{a as bn,R as xn,e as Bn,B as Se,b as be,d as Dn}from"./BAIImportArtifactModal-CMQ7BkUM.js";import{B as Pn}from"./BAIGraphQLPropertyFilter-FbNAR0Ex.js";const Ee={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"BAIArtifactRevisionTableLatestRevisionFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],type:"ArtifactRevision",abstractKey:null};Ee.hash="7598c47b813de8a7d1823fd229eeda60";const Ne={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIArtifactRevisionTableArtifactRevisionFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIArtifactStatusTagFragment"},{args:null,kind:"FragmentSpread",name:"BAIArtifactRevisionDownloadButtonFragment"},{args:null,kind:"FragmentSpread",name:"BAIArtifactRevisionDeleteButtonFragment"}],type:"ArtifactRevision",abstractKey:null};Ne.hash="158ee46c42cc9ac1a45a9f1d359de5db";le.extend(je);const jn=({artifactRevisionFrgmt:l,latestRevisionFrgmt:e,customizeColumns:r,...R})=>{const{t:c}=ye(),s=B.useFragment(Ne,l),i=B.useFragment(Ee,e),h=ae(De([{title:c("comp:BAIArtifactRevisionTable.Version"),dataIndex:"version",key:"version",width:"30%",render:(o,v)=>n.jsx("div",{children:n.jsxs(P,{align:"center",gap:"xs",children:[n.jsx(L,{monospace:!0,strong:!0,children:o}),i&&i.id===v.id&&n.jsx(Ye,{color:"blue",children:"Latest"}),v.status==="PULLED"&&n.jsx(He,{children:v.status})]})})},{title:c("comp:BAIArtifactRevisionTable.Status"),dataIndex:"status",key:"status",width:"15%",render:(o,v)=>n.jsx(bn,{artifactRevisionFrgmt:v})},{title:c("comp:BAIArtifactRevisionTable.Size"),dataIndex:"size",key:"size",width:"15%",render:o=>{var v;return o?n.jsx(L,{monospace:!0,children:(v=Fe(o,"auto"))==null?void 0:v.displayValue}):n.jsx(L,{monospace:!0,children:"N/A"})}},{title:c("comp:BAIArtifactTable.Updated"),dataIndex:"updatedAt",key:"updatedAt",width:"15%",render:o=>o?n.jsx(L,{type:"secondary",title:le(o).toString(),children:le(o).fromNow()}):"N/A"}])),g=r?r(h):h;return n.jsx(Pe,{rowKey:o=>o.id,resizable:!0,columns:g,dataSource:s,scroll:{x:"max-content"},...R})},Ve=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"CancelImportArtifactPayload",kind:"LinkedField",name:"cancelImportArtifact",plural:!1,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"artifactRevision",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"BAIPullingArtifactRevisionAlertCancelMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"BAIPullingArtifactRevisionAlertCancelMutation",selections:e},params:{cacheID:"2b4debfb8df103ad97421b0869b31402",id:null,metadata:{},name:"BAIPullingArtifactRevisionAlertCancelMutation",operationKind:"mutation",text:`mutation BAIPullingArtifactRevisionAlertCancelMutation(
  $input: CancelArtifactInput!
) {
  cancelImportArtifact(input: $input) {
    artifactRevision {
      id
      status
    }
  }
}
`}}}();Ve.hash="18b2b20bc4ed731fcd89e1469e73b49c";const _e={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"BAIPullingArtifactRevisionAlertFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null}],type:"ArtifactRevision",abstractKey:null};_e.hash="8481a07489849ce66e12a3a734be08b5";const Mn=({pullingArtifactRevisionFrgmt:l,onOk:e})=>{const{t:r}=ye(),{modal:R,message:c}=Me.useApp(),s=B.useFragment(_e,l),[i,h]=B.useMutation(Ve);return n.jsx(Re,{type:"info",showIcon:!0,title:r("comp:BAIPullingArtifactRevisionAlert.VersionIsPullingNow",{version:s.version}),action:n.jsx(de,{type:"text",onClick:()=>{R.confirm({title:r("comp:BAIPullingArtifactRevisionAlert.CancelPull"),content:n.jsxs(P,{direction:"column",align:"stretch",children:[n.jsxs(L,{children:[r("comp:BAIPullingArtifactRevisionAlert.YouAreAboutToCancelThisVersion"),":",n.jsxs(L,{strong:!0,children:[" ",s.version]})]}),n.jsx("br",{}),n.jsxs(L,{type:"danger",children:[n.jsxs(L,{type:"danger",strong:!0,children:[r("comp:BAIPullingArtifactRevisionAlert.WARNING"),":"]})," ",r("comp:BAIPullingArtifactRevisionAlert.CancelingWillRestartThePulling")]})]}),cancelText:r("general.button.Close"),okButtonProps:{danger:!0,loading:h},onOk:()=>{i({variables:{input:{artifactRevisionId:te(s.id)}},onCompleted:(g,o)=>{if(o&&o.length>0){o.forEach(v=>c.error(v.message??r("comp:BAIPullingArtifactRevisionAlert.FailedToCancelThePulling")));return}e==null||e(),c.success(r("comp:BAIPullingArtifactRevisionAlert.VersionPullCanceledSuccessfully",{version:s.version}))},onError:g=>{c.error(g.message??r("comp:BAIPullingArtifactRevisionAlert.FailedToCancelThePulling"))}})}})},children:r("general.button.Cancel")})})},Oe={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIDeleteArtifactRevisionsModalArtifactRevisionFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],type:"ArtifactRevision",abstractKey:null};Oe.hash="26bb2a6744453c3301f6e2e94a0922c3";const $e={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"BAIDeleteArtifactRevisionsModalArtifactFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIArtifactDescriptionsFragment"}],type:"Artifact",abstractKey:null};$e.hash="8eac061158289fcc677ac78d52d22410";const we=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{kind:"Variable",name:"input",variableName:"input"}],r={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"BAIDeleteArtifactRevisionsModalCleanupVersionMutation",selections:[{alias:null,args:e,concreteType:"CleanupArtifactRevisionsPayload",kind:"LinkedField",name:"cleanupArtifactRevisions",plural:!1,selections:[{alias:null,args:null,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"artifactRevisions",plural:!1,selections:[{alias:null,args:null,concreteType:"ArtifactRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"node",plural:!1,selections:[r],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"BAIDeleteArtifactRevisionsModalCleanupVersionMutation",selections:[{alias:null,args:e,concreteType:"CleanupArtifactRevisionsPayload",kind:"LinkedField",name:"cleanupArtifactRevisions",plural:!1,selections:[{alias:null,args:null,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"artifactRevisions",plural:!1,selections:[{alias:null,args:null,concreteType:"ArtifactRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"node",plural:!1,selections:[r,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"03897a25039ccf906a0013edbae95224",id:null,metadata:{},name:"BAIDeleteArtifactRevisionsModalCleanupVersionMutation",operationKind:"mutation",text:`mutation BAIDeleteArtifactRevisionsModalCleanupVersionMutation(
  $input: CleanupArtifactRevisionsInput!
) {
  cleanupArtifactRevisions(input: $input) {
    artifactRevisions {
      edges {
        node {
          status
          id
        }
      }
    }
  }
}
`}}}();we.hash="a1b18aa3dacff842d5e39ba15c4e3994";const Kn=({selectedArtifactFrgmt:l,selectedArtifactRevisionFrgmt:e,onOk:r,onCancel:R,...c})=>{const{t:s}=ye(),{token:i}=re.useToken(),[h,g]=B.useMutation(we),o=B.useFragment($e,l),v=B.useFragment(Oe,e),k=v.filter(d=>d.status!=="PULLING"&&d.status!=="SCANNED"),C=[{title:s("comp:BAIDeleteArtifactModal.Version"),dataIndex:"version",key:"version",render:d=>n.jsx(L,{monospace:!0,children:d}),width:"50%"},{title:s("comp:BAIDeleteArtifactModal.Size"),dataIndex:"size",key:"size",render:d=>{var I;return n.jsx(L,{monospace:!0,children:d?(I=Fe(d,"auto"))==null?void 0:I.displayValue:"N/A"})}}];return n.jsx(We,{children:n.jsx(Xe,{title:s("comp:BAIDeleteArtifactModal.RemoveVersions"),centered:!0,onOk:d=>{h({variables:{input:{artifactRevisionIds:k.map(I=>te(I.id))}},onCompleted:(I,S)=>{if(S&&S.length>0){S.forEach(j=>{ge.error(j.message??s("comp:BAIDeleteArtifactModal.FailedToRemoveVersions"))});return}ge.success(s("comp:BAIDeleteArtifactModal.SuccessFullyRemoved",{count:I.cleanupArtifactRevisions.artifactRevisions.edges.length})),r(d)},onError:I=>{ge.error(I.message??s("comp:BAIDeleteArtifactModal.FailedToRemoveVersions"))}})},onCancel:d=>{R(d)},okText:s("general.button.Remove"),cancelText:s("general.button.Cancel"),okButtonProps:{danger:!0,loading:g,disabled:ne(k)||g},...c,children:n.jsxs(P,{direction:"column",gap:"sm",align:"stretch",children:[k.length!==v.length?n.jsx(Re,{icon:n.jsx(J,{title:s("comp:BAIDeleteArtifactModal.OnlyVersionsNotInPULLINGOrSCANNED"),children:n.jsx(xn,{style:{color:i.colorInfo,marginRight:i.marginXS}})}),showIcon:!0,title:s("comp:BAIDeleteArtifactModal.ExcludedVersions",{count:v.length-k.length})}):null,o&&n.jsx(Bn,{artifactFrgmt:o}),n.jsx(Pe,{columns:De(C),dataSource:Ae(v),pagination:{showSizeChanger:!1}})]})})})},Ue={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIArtifactRevisionDeleteButtonFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],type:"ArtifactRevision",abstractKey:null};Ue.hash="de15aa32192b0f0d63e3bd7f5f90d2b6";const xe=({revisionsFrgmt:l,...e})=>{const{token:r}=re.useToken(),c=B.useFragment(Ue,l).some(i=>i.status!=="SCANNED"&&i.status!=="PULLING"),s=e.disabled||e.loading||!c;return n.jsx(Ke,{icon:n.jsx(Ze,{}),disabled:s,type:"text",style:{color:s?r.colorTextDisabled:r.colorError,background:s?r.colorBgContainerDisabled:r.colorErrorBg,...e.style},...Le(e,["style","disabled","loading"])})},ze=function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"id"},r={defaultValue:null,kind:"LocalArgument",name:"limit"},R={defaultValue:null,kind:"LocalArgument",name:"offset"},c=[{kind:"Variable",name:"id",variableName:"id"}],s={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"description",storageKey:null},g=[i,{alias:null,args:null,kind:"ScalarField",name:"url",storageKey:null}],o={alias:null,args:null,concreteType:"SourceInfo",kind:"LinkedField",name:"registry",plural:!1,selections:g,storageKey:null},v={alias:null,args:null,concreteType:"SourceInfo",kind:"LinkedField",name:"source",plural:!1,selections:g,storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},C={kind:"Literal",name:"orderBy",value:[{direction:"DESC",field:"VERSION"},{direction:"DESC",field:"UPDATED_AT"}]},d=[{kind:"Literal",name:"filter",value:{status:{equals:"PULLING"}}},C],I={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},j={alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null},D={alias:null,args:null,kind:"ScalarField",name:"cursor",storageKey:null},b={alias:null,args:null,concreteType:"PageInfo",kind:"LinkedField",name:"pageInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endCursor",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"hasNextPage",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"hasPreviousPage",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startCursor",storageKey:null}],storageKey:null},N={kind:"ClientExtension",selections:[{alias:null,args:null,kind:"ScalarField",name:"__id",storageKey:null}]},F=[{kind:"Literal",name:"limit",value:1},C],M={alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null},x={alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},t={args:null,kind:"FragmentSpread",name:"BAIImportArtifactModalArtifactRevisionFragment"},K=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},C],T=[{kind:"Literal",name:"is_active",value:!0},{kind:"Literal",name:"type",value:["MODEL_STORE"]}];return{fragment:{argumentDefinitions:[l,e,r,R],kind:"Fragment",metadata:null,name:"ReservoirArtifactDetailPageQuery",selections:[{alias:null,args:c,concreteType:"Artifact",kind:"LinkedField",name:"artifact",plural:!1,selections:[s,i,{args:null,kind:"FragmentSpread",name:"BAIArtifactTypeTagFragment"},h,o,v,k,{alias:"pullingArtifactRevisions",args:d,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"__ReservoirArtifactDetailPage_pullingArtifactRevisions_connection",plural:!1,selections:[I,{alias:null,args:null,concreteType:"ArtifactRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"node",plural:!1,selections:[s,S,{args:null,kind:"FragmentSpread",name:"BAIPullingArtifactRevisionAlertFragment"},j],storageKey:null},D],storageKey:null},b,N],storageKey:'__ReservoirArtifactDetailPage_pullingArtifactRevisions_connection(filter:{"status":{"equals":"PULLING"}},orderBy:[{"direction":"DESC","field":"VERSION"},{"direction":"DESC","field":"UPDATED_AT"}])'},{alias:"latestVersion",args:F,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"revisions",plural:!1,selections:[{alias:null,args:null,concreteType:"ArtifactRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"node",plural:!1,selections:[s,M,x,S,t,{args:null,kind:"FragmentSpread",name:"BAIArtifactRevisionTableLatestRevisionFragment"}],storageKey:null}],storageKey:null}],storageKey:'revisions(limit:1,orderBy:[{"direction":"DESC","field":"VERSION"},{"direction":"DESC","field":"UPDATED_AT"}])'},{alias:null,args:K,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"revisions",plural:!1,selections:[I,{alias:null,args:null,concreteType:"ArtifactRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"node",plural:!1,selections:[s,S,{args:null,kind:"FragmentSpread",name:"BAIArtifactRevisionTableArtifactRevisionFragment"},t,{args:null,kind:"FragmentSpread",name:"BAIDeleteArtifactRevisionsModalArtifactRevisionFragment"},{args:null,kind:"FragmentSpread",name:"BAIArtifactRevisionDeleteButtonFragment"},{args:null,kind:"FragmentSpread",name:"BAIArtifactRevisionDownloadButtonFragment"},{args:null,kind:"FragmentSpread",name:"ImportArtifactRevisionToFolderButtonFragment"},{args:null,kind:"FragmentSpread",name:"ImportArtifactRevisionToFolderModalArtifactRevisionFragment"}],storageKey:null}],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIImportArtifactModalArtifactFragment"},{args:null,kind:"FragmentSpread",name:"BAIDeleteArtifactRevisionsModalArtifactFragment"}],storageKey:null},{alias:null,args:T,concreteType:"Group",kind:"LinkedField",name:"groups",plural:!0,selections:[{args:null,kind:"FragmentSpread",name:"ImportArtifactRevisionToFolderModalModelStoreProjectsFragment"}],storageKey:'groups(is_active:true,type:["MODEL_STORE"])'}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,R,r,l],kind:"Operation",name:"ReservoirArtifactDetailPageQuery",selections:[{alias:null,args:c,concreteType:"Artifact",kind:"LinkedField",name:"artifact",plural:!1,selections:[s,i,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},h,o,v,k,{alias:"pullingArtifactRevisions",args:d,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"revisions",plural:!1,selections:[I,{alias:null,args:null,concreteType:"ArtifactRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"node",plural:!1,selections:[s,S,x,j],storageKey:null},D],storageKey:null},b,N],storageKey:'revisions(filter:{"status":{"equals":"PULLING"}},orderBy:[{"direction":"DESC","field":"VERSION"},{"direction":"DESC","field":"UPDATED_AT"}])'},{alias:"pullingArtifactRevisions",args:d,filters:["filter","orderBy"],handle:"connection",key:"ReservoirArtifactDetailPage_pullingArtifactRevisions",kind:"LinkedHandle",name:"revisions"},{alias:"latestVersion",args:F,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"revisions",plural:!1,selections:[{alias:null,args:null,concreteType:"ArtifactRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"node",plural:!1,selections:[s,M,x,S],storageKey:null}],storageKey:null}],storageKey:'revisions(limit:1,orderBy:[{"direction":"DESC","field":"VERSION"},{"direction":"DESC","field":"UPDATED_AT"}])'},{alias:null,args:K,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"revisions",plural:!1,selections:[I,{alias:null,args:null,concreteType:"ArtifactRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"node",plural:!1,selections:[s,S,x,M,k],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:T,concreteType:"Group",kind:"LinkedField",name:"groups",plural:!0,selections:[s,i],storageKey:'groups(is_active:true,type:["MODEL_STORE"])'}]},params:{cacheID:"857082c87bcf47bbc7556f86a4ab6e29",id:null,metadata:{connection:[{count:null,cursor:null,direction:"bidirectional",path:["artifact","pullingArtifactRevisions"]}]},name:"ReservoirArtifactDetailPageQuery",operationKind:"query",text:`query ReservoirArtifactDetailPageQuery(
  $id: ID!
  $offset: Int!
  $limit: Int!
  $filter: ArtifactRevisionFilter!
) {
  artifact(id: $id) {
    id
    name
    ...BAIArtifactTypeTagFragment
    description
    registry {
      name
      url
    }
    source {
      name
      url
    }
    updatedAt
    pullingArtifactRevisions: revisions(filter: {status: {equals: PULLING}}, orderBy: [{field: VERSION, direction: DESC}, {field: UPDATED_AT, direction: DESC}]) {
      count
      edges {
        node {
          id
          status
          ...BAIPullingArtifactRevisionAlertFragment
          __typename
        }
        cursor
      }
      pageInfo {
        endCursor
        hasNextPage
        hasPreviousPage
        startCursor
      }
    }
    latestVersion: revisions(limit: 1, orderBy: [{field: VERSION, direction: DESC}, {field: UPDATED_AT, direction: DESC}]) {
      edges {
        node {
          id
          size
          version
          status
          ...BAIImportArtifactModalArtifactRevisionFragment
          ...BAIArtifactRevisionTableLatestRevisionFragment
        }
      }
    }
    revisions(offset: $offset, limit: $limit, orderBy: [{field: VERSION, direction: DESC}, {field: UPDATED_AT, direction: DESC}], filter: $filter) {
      count
      edges {
        node {
          id
          status
          ...BAIArtifactRevisionTableArtifactRevisionFragment
          ...BAIImportArtifactModalArtifactRevisionFragment
          ...BAIDeleteArtifactRevisionsModalArtifactRevisionFragment
          ...BAIArtifactRevisionDeleteButtonFragment
          ...BAIArtifactRevisionDownloadButtonFragment
          ...ImportArtifactRevisionToFolderButtonFragment
          ...ImportArtifactRevisionToFolderModalArtifactRevisionFragment
        }
      }
    }
    ...BAIImportArtifactModalArtifactFragment
    ...BAIDeleteArtifactRevisionsModalArtifactFragment
  }
  groups(is_active: true, type: ["MODEL_STORE"]) {
    ...ImportArtifactRevisionToFolderModalModelStoreProjectsFragment
  }
}

fragment BAIArtifactDescriptionsFragment on Artifact {
  name
  description
  source {
    name
    url
  }
  ...BAIArtifactTypeTagFragment
}

fragment BAIArtifactRevisionDeleteButtonFragment on ArtifactRevision {
  status
}

fragment BAIArtifactRevisionDownloadButtonFragment on ArtifactRevision {
  status
}

fragment BAIArtifactRevisionTableArtifactRevisionFragment on ArtifactRevision {
  id
  version
  size
  status
  updatedAt
  ...BAIArtifactStatusTagFragment
  ...BAIArtifactRevisionDownloadButtonFragment
  ...BAIArtifactRevisionDeleteButtonFragment
}

fragment BAIArtifactRevisionTableLatestRevisionFragment on ArtifactRevision {
  id
}

fragment BAIArtifactStatusTagFragment on ArtifactRevision {
  status
}

fragment BAIArtifactTypeTagFragment on Artifact {
  type
}

fragment BAIDeleteArtifactRevisionsModalArtifactFragment on Artifact {
  id
  ...BAIArtifactDescriptionsFragment
}

fragment BAIDeleteArtifactRevisionsModalArtifactRevisionFragment on ArtifactRevision {
  id
  version
  size
  status
}

fragment BAIImportArtifactModalArtifactFragment on Artifact {
  id
  name
  ...BAIArtifactDescriptionsFragment
}

fragment BAIImportArtifactModalArtifactRevisionFragment on ArtifactRevision {
  id
  version
  size
  status
}

fragment BAIPullingArtifactRevisionAlertFragment on ArtifactRevision {
  id
  status
  version
}

fragment ImportArtifactRevisionToFolderButtonFragment on ArtifactRevision {
  status
}

fragment ImportArtifactRevisionToFolderModalArtifactRevisionFragment on ArtifactRevision {
  id
}

fragment ImportArtifactRevisionToFolderModalModelStoreProjectsFragment on Group {
  id
  name
}
`}}}();ze.hash="b72980f66c5575c9b3946d349410ddd2";const Ge={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"ImportArtifactRevisionToFolderButtonFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],type:"ArtifactRevision",abstractKey:null};Ge.hash="fb4797e7e04df882a22890d1e13925c2";const Be=({revisionsFrgmt:l,...e})=>{const{token:r}=re.useToken(),R=B.useFragment(Ge,l),s=!en(R,i=>i.status==="SCANNED")||e.disabled||e.loading;return n.jsx(Ke,{icon:n.jsx(hn,{}),disabled:s,type:"text",style:{color:s?r.colorTextDisabled:r.colorInfo,background:s?r.colorBgContainerDisabled:r.colorInfoBg,...e.style},...Le(e,["disabled","loading"])})},qe=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"ImportArtifactsPayload",kind:"LinkedField",name:"importArtifacts",plural:!1,selections:[{alias:null,args:null,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"artifactRevisions",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ArtifactRevisionImportTask",kind:"LinkedField",name:"tasks",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"taskId",storageKey:null},{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"artifactRevision",plural:!1,selections:[e,{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,concreteType:"Artifact",kind:"LinkedField",name:"artifact",plural:!1,selections:[e,{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"ImportArtifactRevisionToFolderModalMutation",selections:r,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"ImportArtifactRevisionToFolderModalMutation",selections:r},params:{cacheID:"870d144d05ea4c3ac90a4ce955510b44",id:null,metadata:{},name:"ImportArtifactRevisionToFolderModalMutation",operationKind:"mutation",text:`mutation ImportArtifactRevisionToFolderModalMutation(
  $input: ImportArtifactsInput!
) {
  importArtifacts(input: $input) {
    artifactRevisions {
      count
    }
    tasks {
      taskId
      artifactRevision {
        id
        version
        artifact {
          id
          name
        }
      }
    }
  }
}
`}}}();qe.hash="b59c2a54c55db7b77c2f8e36c51e81a8";const Qe={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"ImportArtifactRevisionToFolderModalModelStoreProjectsFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],type:"Group",abstractKey:null};Qe.hash="55dc19bd0c05c3aaf314215595f0c8a0";const Je={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"ImportArtifactRevisionToFolderModalArtifactRevisionFragment",selections:[{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},action:"THROW"}],type:"ArtifactRevision",abstractKey:null};Je.hash="911b8e7ffb3a0042ecb970a90018b1e8";const Ln=l=>{"use memo";const e=nn.c(74);let r,R,c,s;e[0]!==l?({selectedArtifactRevisionFrgmt:s,modelStoreProjectsFrgmt:R,onOk:c,...r}=l,e[0]=l,e[1]=r,e[2]=R,e[3]=c,e[4]=s):(r=e[1],R=e[2],c=e[3],s=e[4]);const{t:i}=Ce(),{token:h}=re.useToken(),{message:g}=Me.useApp(),o=E.useRef(null),v=E.useRef(null),[k,C]=tn(!1),{toggle:d}=C,{logger:I}=an(),S=ln(),j=rn();let D;e[5]===Symbol.for("react.memo_cache_sentinel")?(D=Je,e[5]=D):D=e[5];const b=B.useFragment(D,s);let N;e[6]===Symbol.for("react.memo_cache_sentinel")?(N=Qe,e[6]=N):N=e[6];const F=B.useFragment(N,R);let M;e[7]===Symbol.for("react.memo_cache_sentinel")?(M=qe,e[7]=M):M=e[7];const[x,t]=B.useMutation(M);let K;e[8]!==b?(K=ae(b,Cn),e[8]=b,e[9]=K):K=e[9];const T=K;let V;e[10]!==i?(V=i("importArtifactRevisionToFolderModal.ImportToFolder"),e[10]=i,e[11]=V):V=e[11];let U;e[12]!==i?(U=i("importArtifactRevisionToFolderModal.Import"),e[12]=i,e[13]=U):U=e[13];let _;e[14]!==t||e[15]!==b?(_=t||ne(b),e[14]=t,e[15]=b,e[16]=_):_=e[16];let O;e[17]!==t||e[18]!==_?(O={loading:t,disabled:_},e[17]=t,e[18]=_,e[19]=O):O=e[19];let $;e[20]!==x||e[21]!==I||e[22]!==g||e[23]!==c||e[24]!==T||e[25]!==b||e[26]!==i?($=oe=>{var ie;(ie=o.current)==null||ie.validateFields().then(G=>{if(ne(b)){g.error(i("importArtifactRevisionToFolderModal.NoArtifactsSelected"));return}x({variables:{input:{artifactRevisionIds:ae(T,En),vfolderId:G.vfolderId?te(G.vfolderId):null,options:{force:!0}}},onCompleted:(ce,ue)=>{var Ie;if(ue&&ue.length>0){ue.forEach(me=>g.error(me.message??i("importArtifactRevisionToFolderModal.FailedToImport")));return}if(((Ie=ce.importArtifacts.artifactRevisions)==null?void 0:Ie.count)>0){g.success(i("importArtifactRevisionToFolderModal.SuccessfullyImported"));const me=ce.importArtifacts.tasks.filter(Nn).map(Vn);c==null||c(oe,me,G.vfolderId)}else g.error(i("importArtifactRevisionToFolderModal.FailedToImport"))},onError:ce=>{g.error(ce.message??i("importArtifactRevisionToFolderModal.FailedToImport"))}})}).catch(G=>{I.error("ImportArtifactRevisionToFolderModal: Form validation failed",{error:G})})},e[20]=x,e[21]=I,e[22]=g,e[23]=c,e[24]=T,e[25]=b,e[26]=i,e[27]=$):$=e[27];let Q;e[28]===Symbol.for("react.memo_cache_sentinel")?(Q=["onChange","onBlur"],e[28]=Q):Q=e[28];let w;e[29]!==i?(w=i("importArtifactRevisionToFolderModal.OverwriteWarning"),e[29]=i,e[30]=w):w=e[30];let a;e[31]!==h.marginMD?(a={marginBottom:h.marginMD},e[31]=h.marginMD,e[32]=a):a=e[32];let u;e[33]!==w||e[34]!==a?(u=n.jsx(Re,{type:"warning",title:w,showIcon:!0,style:a}),e[33]=w,e[34]=a,e[35]=u):u=e[35];let m;e[36]!==i?(m=i("importArtifactRevisionToFolderModal.FolderMountForModelStore"),e[36]=i,e[37]=m):m=e[37];let f;e[38]===Symbol.for("react.memo_cache_sentinel")?(f=[{required:!0}],e[38]=f):f=e[38];const y=F!=null&&F.id?`group == "${F.id}"`:null;let p;e[39]!==y?(p=sn(['ownership_type == "group"',y]),e[39]=y,e[40]=p):p=e[40];let A;e[41]!==p?(A=n.jsx(fe.Item,{name:"vfolderId",noStyle:!0,children:n.jsx(Sn,{ref:v,excludeDeleted:!0,filter:p})}),e[41]=p,e[42]=A):A=e[42];let z;e[43]!==S.id||e[44]!==g||e[45]!==F||e[46]!==j||e[47]!==i||e[48]!==d?(z=S.id===(F==null?void 0:F.id)?n.jsx(de,{icon:n.jsx(ke,{}),onClick:()=>{d()}}):n.jsx(on,{title:i("importArtifactRevisionToFolderModal.ModelStoreProjectRequired"),description:i("importArtifactRevisionToFolderModal.ModelStoreProjectRequiredDescription"),okText:i("button.ChangeProject"),cancelText:i("button.Cancel"),onConfirm:()=>{F&&F.id&&F.name?E.startTransition(()=>{j({projectId:F.id,projectName:F.name}),g.success(i("importArtifactRevisionToFolderModal.CurrentProjectChangedSuccessfully")),d()}):g.error(i("importArtifactRevisionToFolderModal.FailedToRetrieveModelStoreProject"))},children:n.jsx(de,{icon:n.jsx(ke,{})})}),e[43]=S.id,e[44]=g,e[45]=F,e[46]=j,e[47]=i,e[48]=d,e[49]=z):z=e[49];let Y;e[50]!==A||e[51]!==z?(Y=n.jsxs(P,{gap:"xs",align:"center",children:[A,z]}),e[50]=A,e[51]=z,e[52]=Y):Y=e[52];let H;e[53]!==m||e[54]!==Y?(H=n.jsx(fe.Item,{label:m,name:"vfolderId",rules:f,children:Y}),e[53]=m,e[54]=Y,e[55]=H):H=e[55];let W;e[56]!==u||e[57]!==H?(W=n.jsx(fe,{ref:o,layout:"vertical",preserve:!1,validateTrigger:Q,children:n.jsxs(P,{direction:"column",align:"stretch",children:[u,H]})}),e[56]=u,e[57]=H,e[58]=W):W=e[58];let X;e[59]!==r||e[60]!==$||e[61]!==W||e[62]!==V||e[63]!==U||e[64]!==O?(X=n.jsx(cn,{title:V,okText:U,centered:!0,destroyOnHidden:!0,...r,okButtonProps:O,onOk:$,children:W}),e[59]=r,e[60]=$,e[61]=W,e[62]=V,e[63]=U,e[64]=O,e[65]=X):X=e[65];let Z;e[66]!==d?(Z=oe=>{var ie,G;d(),oe&&((ie=o.current)==null||ie.setFieldsValue({vfolderId:dn("VirtualFolderNode",un(oe.id))}),(G=v.current)==null||G.refetch())},e[66]=d,e[67]=Z):Z=e[67];let ee;e[68]!==k||e[69]!==Z?(ee=n.jsx(mn,{open:k,initialValidate:!0,folderType:"model_project",onRequestClose:Z}),e[68]=k,e[69]=Z,e[70]=ee):ee=e[70];let se;return e[71]!==X||e[72]!==ee?(se=n.jsxs(n.Fragment,{children:[X,ee]}),e[71]=X,e[72]=ee,e[73]=se):se=e[73],se};function Cn(l){return l.id}function En(l){return te(l)}function Nn(l){return l.taskId!=null}function Vn(l){return{taskId:l.taskId,version:l.artifactRevision.version,artifact:{id:te(l.artifactRevision.artifact.id),name:l.artifactRevision.artifact.name}}}le.extend(je);const{Title:_n,Text:On,Paragraph:$n}=ve,Qn=()=>{var _,O,$,Q,w;const{token:l}=re.useToken(),{t:e}=Ce(),{upsertNotification:r}=gn(),{artifactId:R}=fn(),[c,s]=pn(pe),[i,h]=E.useState([]),[g,o]=E.useState([]),[v,k]=E.useState([]),[C,d]=E.useState([]),[I,S]=An({filter:vn(kn,{})}),j=JSON.stringify(I.filter),{baiPaginationOption:D,tablePaginationOption:b,setTablePaginationOption:N}=yn({current:1,pageSize:10}),F=E.useMemo(()=>({id:R??"",offset:D.offset,limit:D.limit,filter:JSON.parse(j||"{}")}),[R,D.limit,D.offset,j]),M=E.useDeferredValue(F),x=E.useDeferredValue(c),{artifact:t,groups:K}=B.useLazyLoadQuery(ze,M,{fetchKey:x===pe?void 0:x,fetchPolicy:x===pe?"store-and-network":"network-only"}),T=(_=t==null?void 0:t.latestVersion.edges[0])==null?void 0:_.node,V=Ae(t==null?void 0:t.pullingArtifactRevisions.edges.map(a=>a==null?void 0:a.node)),U={key:"control",title:e("general.Control"),fixed:!0,required:!0,render:(a,u)=>{var f;const m=u.status;return n.jsxs(P,{gap:"xs",children:[n.jsx(J,{title:e("reservoirPage.PullThisVersion"),children:n.jsx(be,{size:"small",revisionsFrgmt:[u],loading:m==="PULLING"||m==="VERIFYING",onClick:()=>{var y,p;(p=(y=t==null?void 0:t.revisions)==null?void 0:y.edges)==null||p.forEach(A=>{A.node.id===u.id&&k([A.node])})}})}),n.jsx(J,{title:e("importArtifactRevisionToFolderModal.ImportToFolder"),children:n.jsx(Be,{size:"small",revisionsFrgmt:ae(Tn((f=t==null?void 0:t.revisions)==null?void 0:f.edges,y=>y.node.id===u.id),"node"),onClick:()=>{var y,p;(p=(y=t==null?void 0:t.revisions)==null?void 0:y.edges)==null||p.forEach(A=>{A.node.id===u.id&&d([A.node])})}})}),n.jsx(J,{title:e("reservoirPage.RemoveThisVersion"),children:n.jsx(xe,{size:"small",title:e("reservoirPage.RemoveThisVersion"),revisionsFrgmt:[u],onClick:()=>{var y,p;(p=(y=t==null?void 0:t.revisions)==null?void 0:y.edges)==null||p.forEach(A=>{A.node.id===u.id&&o([A.node])})}})})]})}};return n.jsxs("div",{children:[n.jsxs(P,{align:"center",style:{marginBottom:l.marginLG},justify:"between",children:[n.jsxs(P,{align:"center",gap:"xs",children:[n.jsx(_n,{level:3,style:{margin:0},children:t==null?void 0:t.name}),t&&n.jsx(Se,{artifactTypeFrgmt:t})]}),n.jsx(Fn,{value:c,autoUpdateDelay:15e3,loading:x!==c,onChange:()=>{s()}})]}),V.length>0&&n.jsx(P,{direction:"column",gap:"sm",align:"stretch",style:{marginBottom:l.marginMD},children:V.map(a=>n.jsx(Mn,{pullingArtifactRevisionFrgmt:a,onOk:()=>{s()}},a.id))}),n.jsx(Te,{title:e("reservoirPage.BasicInformation"),showDivider:!0,extra:n.jsx(de,{type:"primary",icon:n.jsx(Rn,{size:16}),onClick:()=>{T&&k([T])},disabled:!T||T.status!=="SCANNED",children:T?e("reservoirPage.PullLatestVersion",{version:T.version}):"N/A"}),style:{marginBottom:l.marginMD},children:n.jsxs(q,{column:2,bordered:!0,children:[n.jsx(q.Item,{label:e("reservoirPage.Name"),children:t==null?void 0:t.name}),n.jsx(q.Item,{label:e("reservoirPage.Type"),children:t&&n.jsx(Se,{artifactTypeFrgmt:t})}),n.jsx(q.Item,{label:e("reservoirPage.Size"),children:n.jsx(L,{monospace:!0,children:T!=null&&T.size?(O=Fe(T.size,"auto"))==null?void 0:O.displayValue:"N/A"})}),n.jsx(q.Item,{label:e("reservoirPage.Source"),children:t!=null&&t.source?n.jsx(ve.Link,{href:t.source.url??"",target:"_blank",rel:"noopener noreferrer",children:t.source.name||"N/A"}):"N/A"}),n.jsx(q.Item,{label:e("reservoirPage.Registry"),children:n.jsx(ve,{children:t!=null&&t.registry?`${t.registry.name} (${t.registry.url})`:"N/A"})}),n.jsx(q.Item,{label:e("reservoirPage.LastUpdated"),span:2,children:t!=null&&t.updatedAt?le(t==null?void 0:t.updatedAt).format("lll"):"N/A"}),n.jsx(q.Item,{label:e("reservoirPage.Description"),span:2,children:t!=null&&t.description?n.jsx($n,{children:t.description}):"N/A"})]})}),n.jsx(Te,{title:e("reservoirPage.VersionList"),showDivider:!0,style:{marginBottom:l.marginMD},styles:{body:{padding:`${l.paddingSM}px ${l.paddingLG}px ${l.paddingLG}px ${l.paddingLG}px`}},children:n.jsxs(P,{direction:"column",gap:"sm",align:"stretch",children:[n.jsxs(P,{align:"stretch",justify:"between",children:[n.jsx(Pn,{combinationMode:"AND",onChange:a=>{S({filter:a??{}},"replaceIn")},filterProperties:[{fixedOperator:"equals",propertyLabel:e("reservoirPage.Status"),key:"status",type:"enum",options:ae(["SCANNED","PULLING","PULLED","VERIFYING","NEEDS_APPROVAL","FAILED","AVAILABLE","REJECTED"],a=>({label:a,value:a}))},{fixedOperator:"contains",propertyLabel:e("reservoirPage.Version"),key:"version",type:"string"},{propertyLabel:e("reservoirPage.Size"),key:"size",type:"number",operators:["equals","greaterThan","greaterOrEqual","lessThan","lessOrEqual"]}]}),i.length>0?n.jsxs(P,{gap:"xs",children:[n.jsxs(On,{children:[i.length," selected"]}),n.jsx(J,{title:e("reservoirPage.PullSelectedVersions"),children:n.jsx(be,{type:"default",revisionsFrgmt:i.flatMap(a=>a.data),onClick:()=>{t&&k(i.flatMap(a=>a.data))}})}),n.jsx(J,{title:e("importArtifactRevisionToFolderModal.ImportToFolder"),children:n.jsx(Be,{type:"default",revisionsFrgmt:i.flatMap(a=>a.data),onClick:()=>{t&&d(In(i,a=>a.data))}})}),n.jsx(J,{title:e("reservoirPage.RemoveSelectedVersions"),children:n.jsx(xe,{style:{borderColor:l.colorBorder},revisionsFrgmt:i.flatMap(a=>a.data),onClick:()=>{t&&o(i.flatMap(a=>a.data))}})})]}):null]}),n.jsx(jn,{artifactRevisionFrgmt:Ae((Q=($=t==null?void 0:t.revisions)==null?void 0:$.edges)==null?void 0:Q.map(a=>a.node)),latestRevisionFrgmt:t==null?void 0:t.latestVersion.edges[0].node,loading:M!==F,pagination:{current:b.current,pageSize:b.pageSize,total:((w=t==null?void 0:t.revisions)==null?void 0:w.count)??0,onChange:(a,u)=>{he(a)&&he(u)&&N({current:a,pageSize:u})}},onRow:a=>({onClick:u=>{var y;u.stopPropagation();const m=u.target;if(m.closest("button")||m.closest("a")||!t)return;const f=(y=t.revisions.edges.find(p=>p.node.id===a.id))==null?void 0:y.node;f&&h(p=>{const A=p.filter(z=>z.id!==a.id);return A.length===p.length?[...p,{id:a.id,data:f}]:A})}}),rowSelection:{type:"checkbox",onChange:a=>{if(!t)return;const u=t.revisions,m=u.edges.map(f=>f.node.id);h(f=>{const y=f.filter(A=>!m.includes(A.id)),p=u.edges.filter(A=>a.includes(A.node.id)).map(A=>({id:A.node.id,data:A.node}));return y.concat(p)})},selectedRowKeys:i.map(a=>a.id)},customizeColumns:a=>[a[0],a[1],U,...a.slice(2)]})]})}),n.jsx(Dn,{selectedArtifactFrgmt:t??null,selectedArtifactRevisionFrgmt:v,open:!!t&&!ne(v),connectionIds:t?[t.pullingArtifactRevisions.__id]:void 0,onOk:(a,u)=>{k([]),u.forEach(m=>{r({message:e("reservoirPage.PullingArtifact",{name:m.artifact.name,version:m.version}),type:"info",open:!0,duration:0,backgroundTask:{status:"pending",taskId:m.taskId,promise:null,percent:0,onChange:{resolved:(f,y)=>({type:"success",message:e("reservoirPage.SuccessFullyPulledArtifact",{name:m.artifact.name,version:m.version}),showIcon:!0,toText:e("reservoirPage.GoToArtifact"),to:`/reservoir/${m.artifact.id}`}),rejected:(f,y)=>e("reservoirPage.FailedToPullArtifact",{name:m.artifact.name,version:m.version})}}})})},onCancel:()=>{k([])}}),n.jsx(Kn,{selectedArtifactFrgmt:t??null,selectedArtifactRevisionFrgmt:g,onOk:()=>{o([])},onCancel:()=>{o([])},open:!!t&&!ne(g)}),n.jsx(Ln,{selectedArtifactRevisionFrgmt:C,modelStoreProjectsFrgmt:(K==null?void 0:K[0])??void 0,onOk:(a,u,m)=>{d([]),s(),u.forEach(f=>{r({message:e("importArtifactRevisionToFolderModal.ImportingArtifact",{name:f.artifact.name,version:f.version}),type:"info",open:!0,duration:0,backgroundTask:{status:"pending",taskId:f.taskId,promise:null,percent:0,onChange:{resolved:(y,p)=>({type:"success",message:e("importArtifactRevisionToFolderModal.SuccessfullyImportedArtifact",{name:f.artifact.name,version:f.version}),showIcon:!0,toText:e(m?"data.folders.OpenAFolder":"reservoirPage.GoToArtifact"),to:m?{search:new URLSearchParams({folder:te(m)}).toString()}:`/reservoir/${f.artifact.id}`}),rejected:(y,p)=>e("importArtifactRevisionToFolderModal.FailedToImportArtifact",{name:f.artifact.name,version:f.version})}}})})},onCancel:()=>{d([])},open:!!t&&!ne(C)})]})};export{Qn as default};
//# sourceMappingURL=ReservoirArtifactDetailPage-C57Px57J.js.map
