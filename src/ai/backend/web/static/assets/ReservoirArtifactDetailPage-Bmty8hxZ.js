import{ad as Fe,i as x,a6 as ae,a1 as Pe,j as n,B as j,bM as L,f as Ye,cB as He,cR as Re,bW as le,b5 as je,gC as Me,A as Ke,bV as Ie,b2 as Le,N as te,t as re,a7 as Xe,gD as Ze,am as Z,aK as ve,m as ne,O as ce,z as de,ac as Ce,aZ as en,bd as nn,h as tn,u as Ee,r as E,aV as an,v as ln,aj as rn,dp as sn,cY as on,F as pe,b4 as Te,c1 as cn,P as dn,d6 as un,d1 as mn,a8 as gn,J as fn,dq as pn,bF as An,au as Ae,$ as vn,a0 as yn,aW as Fn,T as ye,aA as Rn,bI as he,D as Y,c2 as In,fC as kn,b6 as Se,a9 as Tn,a5 as hn}from"./index-DUzRNOsy.js";import{F as Sn}from"./folder-input-Bbs-j6uC.js";import{B as bn}from"./BAIVFolderSelect-C8w3RNN0.js";import{a as Bn,R as Dn,e as xn,B as be,b as Be,d as Pn}from"./BAIImportArtifactModal-Cwe0Cz5H.js";import{B as jn}from"./BAIGraphQLPropertyFilter-qgXPJI5K.js";const Ve={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"BAIArtifactRevisionTableLatestRevisionFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],type:"ArtifactRevision",abstractKey:null};Ve.hash="7598c47b813de8a7d1823fd229eeda60";const Ne={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIArtifactRevisionTableArtifactRevisionFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIArtifactStatusTagFragment"},{args:null,kind:"FragmentSpread",name:"BAIArtifactRevisionDownloadButtonFragment"},{args:null,kind:"FragmentSpread",name:"BAIArtifactRevisionDeleteButtonFragment"}],type:"ArtifactRevision",abstractKey:null};Ne.hash="158ee46c42cc9ac1a45a9f1d359de5db";le.extend(Me);const Mn=({artifactRevisionFrgmt:l,latestRevisionFrgmt:e,customizeColumns:s,...R})=>{const{t:c}=Fe(),r=x.useFragment(Ne,l),i=x.useFragment(Ve,e),h=ae(Pe([{title:c("comp:BAIArtifactRevisionTable.Version"),dataIndex:"version",key:"version",width:"30%",render:(o,v)=>n.jsx("div",{children:n.jsxs(j,{align:"center",gap:"xs",children:[n.jsx(L,{monospace:!0,strong:!0,children:o}),i&&i.id===v.id&&n.jsx(Ye,{color:"blue",children:"Latest"}),v.status==="PULLED"&&n.jsx(He,{children:v.status})]})})},{title:c("comp:BAIArtifactRevisionTable.Status"),dataIndex:"status",key:"status",width:"15%",render:(o,v)=>n.jsx(Bn,{artifactRevisionFrgmt:v})},{title:c("comp:BAIArtifactRevisionTable.Size"),dataIndex:"size",key:"size",width:"15%",render:o=>{var v;return o?n.jsx(L,{monospace:!0,children:(v=Re(o,"auto"))==null?void 0:v.displayValue}):n.jsx(L,{monospace:!0,children:"N/A"})}},{title:c("comp:BAIArtifactTable.Updated"),dataIndex:"updatedAt",key:"updatedAt",width:"15%",render:o=>o?n.jsx(L,{type:"secondary",title:le(o).toString(),children:le(o).fromNow()}):"N/A"}])),p=s?s(h):h;return n.jsx(je,{rowKey:o=>o.id,resizable:!0,columns:p,dataSource:r,scroll:{x:"max-content"},...R})},_e=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"CancelImportArtifactPayload",kind:"LinkedField",name:"cancelImportArtifact",plural:!1,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"artifactRevision",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"BAIPullingArtifactRevisionAlertCancelMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"BAIPullingArtifactRevisionAlertCancelMutation",selections:e},params:{cacheID:"2b4debfb8df103ad97421b0869b31402",id:null,metadata:{},name:"BAIPullingArtifactRevisionAlertCancelMutation",operationKind:"mutation",text:`mutation BAIPullingArtifactRevisionAlertCancelMutation(
  $input: CancelArtifactInput!
) {
  cancelImportArtifact(input: $input) {
    artifactRevision {
      id
      status
    }
  }
}
`}}}();_e.hash="18b2b20bc4ed731fcd89e1469e73b49c";const Oe={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"BAIPullingArtifactRevisionAlertFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null}],type:"ArtifactRevision",abstractKey:null};Oe.hash="8481a07489849ce66e12a3a734be08b5";const Kn=({pullingArtifactRevisionFrgmt:l,onOk:e})=>{const{t:s}=Fe(),{modal:R,message:c}=Ke.useApp(),r=x.useFragment(Oe,l),[i,h]=x.useMutation(_e);return n.jsx(Ie,{type:"info",showIcon:!0,title:s("comp:BAIPullingArtifactRevisionAlert.VersionIsPullingNow",{version:r.version}),action:n.jsx(Le,{type:"text",onClick:()=>{R.confirm({title:s("comp:BAIPullingArtifactRevisionAlert.CancelPull"),content:n.jsxs(j,{direction:"column",align:"stretch",children:[n.jsxs(L,{children:[s("comp:BAIPullingArtifactRevisionAlert.YouAreAboutToCancelThisVersion"),":",n.jsxs(L,{strong:!0,children:[" ",r.version]})]}),n.jsx("br",{}),n.jsxs(L,{type:"danger",children:[n.jsxs(L,{type:"danger",strong:!0,children:[s("comp:BAIPullingArtifactRevisionAlert.WARNING"),":"]})," ",s("comp:BAIPullingArtifactRevisionAlert.CancelingWillRestartThePulling")]})]}),cancelText:s("general.button.Close"),okButtonProps:{danger:!0,loading:h},onOk:()=>{i({variables:{input:{artifactRevisionId:te(r.id)}},onCompleted:(p,o)=>{if(o&&o.length>0){o.forEach(v=>c.error(v.message??s("comp:BAIPullingArtifactRevisionAlert.FailedToCancelThePulling")));return}e==null||e(),c.success(s("comp:BAIPullingArtifactRevisionAlert.VersionPullCanceledSuccessfully",{version:r.version}))},onError:p=>{c.error(p.message??s("comp:BAIPullingArtifactRevisionAlert.FailedToCancelThePulling"))}})}})},children:s("general.button.Cancel")})})},$e={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIDeleteArtifactRevisionsModalArtifactRevisionFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],type:"ArtifactRevision",abstractKey:null};$e.hash="26bb2a6744453c3301f6e2e94a0922c3";const we={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"BAIDeleteArtifactRevisionsModalArtifactFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIArtifactDescriptionsFragment"}],type:"Artifact",abstractKey:null};we.hash="8eac061158289fcc677ac78d52d22410";const Ue=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{kind:"Variable",name:"input",variableName:"input"}],s={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"BAIDeleteArtifactRevisionsModalCleanupVersionMutation",selections:[{alias:null,args:e,concreteType:"CleanupArtifactRevisionsPayload",kind:"LinkedField",name:"cleanupArtifactRevisions",plural:!1,selections:[{alias:null,args:null,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"artifactRevisions",plural:!1,selections:[{alias:null,args:null,concreteType:"ArtifactRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"node",plural:!1,selections:[s],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"BAIDeleteArtifactRevisionsModalCleanupVersionMutation",selections:[{alias:null,args:e,concreteType:"CleanupArtifactRevisionsPayload",kind:"LinkedField",name:"cleanupArtifactRevisions",plural:!1,selections:[{alias:null,args:null,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"artifactRevisions",plural:!1,selections:[{alias:null,args:null,concreteType:"ArtifactRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"node",plural:!1,selections:[s,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"03897a25039ccf906a0013edbae95224",id:null,metadata:{},name:"BAIDeleteArtifactRevisionsModalCleanupVersionMutation",operationKind:"mutation",text:`mutation BAIDeleteArtifactRevisionsModalCleanupVersionMutation(
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
`}}}();Ue.hash="a1b18aa3dacff842d5e39ba15c4e3994";const Ln=({selectedArtifactFrgmt:l,selectedArtifactRevisionFrgmt:e,onOk:s,onCancel:R,...c})=>{const{t:r}=Fe(),{token:i}=re.useToken(),[h,p]=x.useMutation(Ue),o=x.useFragment(we,l),v=x.useFragment($e,e),k=v.filter(d=>d.status!=="PULLING"&&d.status!=="SCANNED"),C=[{title:r("comp:BAIDeleteArtifactModal.Version"),dataIndex:"version",key:"version",render:d=>n.jsx(L,{monospace:!0,children:d}),width:"50%"},{title:r("comp:BAIDeleteArtifactModal.Size"),dataIndex:"size",key:"size",render:d=>{var I;return n.jsx(L,{monospace:!0,children:d?(I=Re(d,"auto"))==null?void 0:I.displayValue:"N/A"})}}];return n.jsx(Xe,{children:n.jsx(Ze,{title:r("comp:BAIDeleteArtifactModal.RemoveVersions"),centered:!0,onOk:d=>{h({variables:{input:{artifactRevisionIds:k.map(I=>te(I.id))}},onCompleted:(I,S)=>{if(S&&S.length>0){S.forEach(B=>{ce.error(B.message??r("comp:BAIDeleteArtifactModal.FailedToRemoveVersions"))});return}const P=I.cleanupArtifactRevisions;if(!P){ce.error(r("comp:BAIDeleteArtifactModal.FailedToRemoveVersions"));return}ce.success(r("comp:BAIDeleteArtifactModal.SuccessFullyRemoved",{count:P.artifactRevisions.edges.length})),s(d)},onError:I=>{ce.error(I.message??r("comp:BAIDeleteArtifactModal.FailedToRemoveVersions"))}})},onCancel:d=>{R(d)},okText:r("general.button.Remove"),cancelText:r("general.button.Cancel"),okButtonProps:{danger:!0,loading:p,disabled:ne(k)||p},...c,children:n.jsxs(j,{direction:"column",gap:"sm",align:"stretch",children:[k.length!==v.length?n.jsx(Ie,{icon:n.jsx(Z,{title:r("comp:BAIDeleteArtifactModal.OnlyVersionsNotInPULLINGOrSCANNED"),children:n.jsx(Dn,{style:{color:i.colorInfo,marginRight:i.marginXS}})}),showIcon:!0,title:r("comp:BAIDeleteArtifactModal.ExcludedVersions",{count:v.length-k.length})}):null,o&&n.jsx(xn,{artifactFrgmt:o}),n.jsx(je,{columns:Pe(C),dataSource:ve(v),pagination:{showSizeChanger:!1}})]})})})},ze={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIArtifactRevisionDeleteButtonFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],type:"ArtifactRevision",abstractKey:null};ze.hash="de15aa32192b0f0d63e3bd7f5f90d2b6";const De=({revisionsFrgmt:l,...e})=>{const{token:s}=re.useToken(),c=x.useFragment(ze,l).some(i=>i.status!=="SCANNED"&&i.status!=="PULLING"),r=e.disabled||e.loading||!c;return n.jsx(de,{icon:n.jsx(en,{}),disabled:r,type:"text",style:{color:r?s.colorTextDisabled:s.colorError,background:r?s.colorBgContainerDisabled:s.colorErrorBg,...e.style},...Ce(e,["style","disabled","loading"])})},Ge=function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"id"},s={defaultValue:null,kind:"LocalArgument",name:"limit"},R={defaultValue:null,kind:"LocalArgument",name:"offset"},c=[{kind:"Variable",name:"id",variableName:"id"}],r={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"description",storageKey:null},p=[i,{alias:null,args:null,kind:"ScalarField",name:"url",storageKey:null}],o={alias:null,args:null,concreteType:"SourceInfo",kind:"LinkedField",name:"registry",plural:!1,selections:p,storageKey:null},v={alias:null,args:null,concreteType:"SourceInfo",kind:"LinkedField",name:"source",plural:!1,selections:p,storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},C={kind:"Literal",name:"orderBy",value:[{direction:"DESC",field:"VERSION"},{direction:"DESC",field:"UPDATED_AT"}]},d=[{kind:"Literal",name:"filter",value:{status:{equals:"PULLING"}}},C],I={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},P={alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null},B={alias:null,args:null,kind:"ScalarField",name:"cursor",storageKey:null},b={alias:null,args:null,concreteType:"PageInfo",kind:"LinkedField",name:"pageInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endCursor",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"hasNextPage",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"hasPreviousPage",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startCursor",storageKey:null}],storageKey:null},V={kind:"ClientExtension",selections:[{alias:null,args:null,kind:"ScalarField",name:"__id",storageKey:null}]},F=[{kind:"Literal",name:"limit",value:1},C],M={alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null},D={alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},t={args:null,kind:"FragmentSpread",name:"BAIImportArtifactModalArtifactRevisionFragment"},K=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},C],T=[{kind:"Literal",name:"is_active",value:!0},{kind:"Literal",name:"type",value:["MODEL_STORE"]}];return{fragment:{argumentDefinitions:[l,e,s,R],kind:"Fragment",metadata:null,name:"ReservoirArtifactDetailPageQuery",selections:[{alias:null,args:c,concreteType:"Artifact",kind:"LinkedField",name:"artifact",plural:!1,selections:[r,i,{args:null,kind:"FragmentSpread",name:"BAIArtifactTypeTagFragment"},h,o,v,k,{alias:"pullingArtifactRevisions",args:d,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"__ReservoirArtifactDetailPage_pullingArtifactRevisions_connection",plural:!1,selections:[I,{alias:null,args:null,concreteType:"ArtifactRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"node",plural:!1,selections:[r,S,{args:null,kind:"FragmentSpread",name:"BAIPullingArtifactRevisionAlertFragment"},P],storageKey:null},B],storageKey:null},b,V],storageKey:'__ReservoirArtifactDetailPage_pullingArtifactRevisions_connection(filter:{"status":{"equals":"PULLING"}},orderBy:[{"direction":"DESC","field":"VERSION"},{"direction":"DESC","field":"UPDATED_AT"}])'},{alias:"latestVersion",args:F,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"revisions",plural:!1,selections:[{alias:null,args:null,concreteType:"ArtifactRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"node",plural:!1,selections:[r,M,D,S,t,{args:null,kind:"FragmentSpread",name:"BAIArtifactRevisionTableLatestRevisionFragment"}],storageKey:null}],storageKey:null}],storageKey:'revisions(limit:1,orderBy:[{"direction":"DESC","field":"VERSION"},{"direction":"DESC","field":"UPDATED_AT"}])'},{alias:null,args:K,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"revisions",plural:!1,selections:[I,{alias:null,args:null,concreteType:"ArtifactRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"node",plural:!1,selections:[r,S,{args:null,kind:"FragmentSpread",name:"BAIArtifactRevisionTableArtifactRevisionFragment"},t,{args:null,kind:"FragmentSpread",name:"BAIDeleteArtifactRevisionsModalArtifactRevisionFragment"},{args:null,kind:"FragmentSpread",name:"BAIArtifactRevisionDeleteButtonFragment"},{args:null,kind:"FragmentSpread",name:"BAIArtifactRevisionDownloadButtonFragment"},{args:null,kind:"FragmentSpread",name:"ImportArtifactRevisionToFolderButtonFragment"},{args:null,kind:"FragmentSpread",name:"ImportArtifactRevisionToFolderModalArtifactRevisionFragment"}],storageKey:null}],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIImportArtifactModalArtifactFragment"},{args:null,kind:"FragmentSpread",name:"BAIDeleteArtifactRevisionsModalArtifactFragment"}],storageKey:null},{alias:null,args:T,concreteType:"Group",kind:"LinkedField",name:"groups",plural:!0,selections:[{args:null,kind:"FragmentSpread",name:"ImportArtifactRevisionToFolderModalModelStoreProjectsFragment"}],storageKey:'groups(is_active:true,type:["MODEL_STORE"])'}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,R,s,l],kind:"Operation",name:"ReservoirArtifactDetailPageQuery",selections:[{alias:null,args:c,concreteType:"Artifact",kind:"LinkedField",name:"artifact",plural:!1,selections:[r,i,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},h,o,v,k,{alias:"pullingArtifactRevisions",args:d,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"revisions",plural:!1,selections:[I,{alias:null,args:null,concreteType:"ArtifactRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"node",plural:!1,selections:[r,S,D,P],storageKey:null},B],storageKey:null},b,V],storageKey:'revisions(filter:{"status":{"equals":"PULLING"}},orderBy:[{"direction":"DESC","field":"VERSION"},{"direction":"DESC","field":"UPDATED_AT"}])'},{alias:"pullingArtifactRevisions",args:d,filters:["filter","orderBy"],handle:"connection",key:"ReservoirArtifactDetailPage_pullingArtifactRevisions",kind:"LinkedHandle",name:"revisions"},{alias:"latestVersion",args:F,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"revisions",plural:!1,selections:[{alias:null,args:null,concreteType:"ArtifactRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"node",plural:!1,selections:[r,M,D,S],storageKey:null}],storageKey:null}],storageKey:'revisions(limit:1,orderBy:[{"direction":"DESC","field":"VERSION"},{"direction":"DESC","field":"UPDATED_AT"}])'},{alias:null,args:K,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"revisions",plural:!1,selections:[I,{alias:null,args:null,concreteType:"ArtifactRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"node",plural:!1,selections:[r,S,D,M,k],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:T,concreteType:"Group",kind:"LinkedField",name:"groups",plural:!0,selections:[r,i],storageKey:'groups(is_active:true,type:["MODEL_STORE"])'}]},params:{cacheID:"857082c87bcf47bbc7556f86a4ab6e29",id:null,metadata:{connection:[{count:null,cursor:null,direction:"bidirectional",path:["artifact","pullingArtifactRevisions"]}]},name:"ReservoirArtifactDetailPageQuery",operationKind:"query",text:`query ReservoirArtifactDetailPageQuery(
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
`}}}();Ge.hash="b72980f66c5575c9b3946d349410ddd2";const qe={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"ImportArtifactRevisionToFolderButtonFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],type:"ArtifactRevision",abstractKey:null};qe.hash="fb4797e7e04df882a22890d1e13925c2";const xe=({revisionsFrgmt:l,...e})=>{const{token:s}=re.useToken(),R=x.useFragment(qe,l),r=!nn(R,i=>i.status==="SCANNED")||e.disabled||e.loading;return n.jsx(de,{icon:n.jsx(Sn,{}),disabled:r,type:"text",style:{color:r?s.colorTextDisabled:s.colorInfo,background:r?s.colorBgContainerDisabled:s.colorInfoBg,...e.style},...Ce(e,["disabled","loading"])})},Qe=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"ImportArtifactsPayload",kind:"LinkedField",name:"importArtifacts",plural:!1,selections:[{alias:null,args:null,concreteType:"ArtifactRevisionConnection",kind:"LinkedField",name:"artifactRevisions",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ArtifactRevisionImportTask",kind:"LinkedField",name:"tasks",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"taskId",storageKey:null},{alias:null,args:null,concreteType:"ArtifactRevision",kind:"LinkedField",name:"artifactRevision",plural:!1,selections:[e,{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,concreteType:"Artifact",kind:"LinkedField",name:"artifact",plural:!1,selections:[e,{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"ImportArtifactRevisionToFolderModalMutation",selections:s,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"ImportArtifactRevisionToFolderModalMutation",selections:s},params:{cacheID:"870d144d05ea4c3ac90a4ce955510b44",id:null,metadata:{},name:"ImportArtifactRevisionToFolderModalMutation",operationKind:"mutation",text:`mutation ImportArtifactRevisionToFolderModalMutation(
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
`}}}();Qe.hash="b59c2a54c55db7b77c2f8e36c51e81a8";const We={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"ImportArtifactRevisionToFolderModalModelStoreProjectsFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],type:"Group",abstractKey:null};We.hash="55dc19bd0c05c3aaf314215595f0c8a0";const Je={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"ImportArtifactRevisionToFolderModalArtifactRevisionFragment",selections:[{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},action:"THROW"}],type:"ArtifactRevision",abstractKey:null};Je.hash="911b8e7ffb3a0042ecb970a90018b1e8";const Cn=l=>{"use memo";const e=tn.c(74);let s,R,c,r;e[0]!==l?({selectedArtifactRevisionFrgmt:r,modelStoreProjectsFrgmt:R,onOk:c,...s}=l,e[0]=l,e[1]=s,e[2]=R,e[3]=c,e[4]=r):(s=e[1],R=e[2],c=e[3],r=e[4]);const{t:i}=Ee(),{token:h}=re.useToken(),{message:p}=Ke.useApp(),o=E.useRef(null),v=E.useRef(null),[k,C]=an(!1),{toggle:d}=C,{logger:I}=ln(),S=rn(),P=sn();let B;e[5]===Symbol.for("react.memo_cache_sentinel")?(B=Je,e[5]=B):B=e[5];const b=x.useFragment(B,r);let V;e[6]===Symbol.for("react.memo_cache_sentinel")?(V=We,e[6]=V):V=e[6];const F=x.useFragment(V,R);let M;e[7]===Symbol.for("react.memo_cache_sentinel")?(M=Qe,e[7]=M):M=e[7];const[D,t]=x.useMutation(M);let K;e[8]!==b?(K=ae(b,En),e[8]=b,e[9]=K):K=e[9];const T=K;let N;e[10]!==i?(N=i("importArtifactRevisionToFolderModal.ImportToFolder"),e[10]=i,e[11]=N):N=e[11];let Q;e[12]!==i?(Q=i("importArtifactRevisionToFolderModal.Import"),e[12]=i,e[13]=Q):Q=e[13];let _;e[14]!==t||e[15]!==b?(_=t||ne(b),e[14]=t,e[15]=b,e[16]=_):_=e[16];let O;e[17]!==t||e[18]!==_?(O={loading:t,disabled:_},e[17]=t,e[18]=_,e[19]=O):O=e[19];let $;e[20]!==D||e[21]!==I||e[22]!==p||e[23]!==c||e[24]!==T||e[25]!==b||e[26]!==i?($=oe=>{var ie;(ie=o.current)==null||ie.validateFields().then(J=>{if(ne(b)){p.error(i("importArtifactRevisionToFolderModal.NoArtifactsSelected"));return}D({variables:{input:{artifactRevisionIds:ae(T,Vn),vfolderId:J.vfolderId?te(J.vfolderId):null,options:{force:!0}}},onCompleted:(ue,me)=>{var ke;if(me&&me.length>0){me.forEach(fe=>p.error(fe.message??i("importArtifactRevisionToFolderModal.FailedToImport")));return}const ge=ue.importArtifacts;if(!ge){p.error(i("importArtifactRevisionToFolderModal.FailedToImport"));return}if(((ke=ge.artifactRevisions)==null?void 0:ke.count)>0){p.success(i("importArtifactRevisionToFolderModal.SuccessfullyImported"));const fe=ge.tasks.filter(Nn).map(_n);c==null||c(oe,fe,J.vfolderId)}else p.error(i("importArtifactRevisionToFolderModal.FailedToImport"))},onError:ue=>{p.error(ue.message??i("importArtifactRevisionToFolderModal.FailedToImport"))}})}).catch(J=>{I.error("ImportArtifactRevisionToFolderModal: Form validation failed",{error:J})})},e[20]=D,e[21]=I,e[22]=p,e[23]=c,e[24]=T,e[25]=b,e[26]=i,e[27]=$):$=e[27];let H;e[28]===Symbol.for("react.memo_cache_sentinel")?(H=["onChange","onBlur"],e[28]=H):H=e[28];let w;e[29]!==i?(w=i("importArtifactRevisionToFolderModal.OverwriteWarning"),e[29]=i,e[30]=w):w=e[30];let U;e[31]!==h.marginMD?(U={marginBottom:h.marginMD},e[31]=h.marginMD,e[32]=U):U=e[32];let z;e[33]!==w||e[34]!==U?(z=n.jsx(Ie,{type:"warning",title:w,showIcon:!0,style:U}),e[33]=w,e[34]=U,e[35]=z):z=e[35];let G;e[36]!==i?(G=i("importArtifactRevisionToFolderModal.FolderMountForModelStore"),e[36]=i,e[37]=G):G=e[37];let X;e[38]===Symbol.for("react.memo_cache_sentinel")?(X=[{required:!0}],e[38]=X):X=e[38];const a=F!=null&&F.id?`group == "${F.id}"`:null;let m;e[39]!==a?(m=on(['ownership_type == "group"',a]),e[39]=a,e[40]=m):m=e[40];let g;e[41]!==m?(g=n.jsx(pe.Item,{name:"vfolderId",noStyle:!0,children:n.jsx(bn,{ref:v,excludeDeleted:!0,filter:m})}),e[41]=m,e[42]=g):g=e[42];let f;e[43]!==S.id||e[44]!==p||e[45]!==F||e[46]!==P||e[47]!==i||e[48]!==d?(f=S.id===(F==null?void 0:F.id)?n.jsx(de,{icon:n.jsx(Te,{}),onClick:()=>{d()}}):n.jsx(cn,{title:i("importArtifactRevisionToFolderModal.ModelStoreProjectRequired"),description:i("importArtifactRevisionToFolderModal.ModelStoreProjectRequiredDescription"),okText:i("button.ChangeProject"),cancelText:i("button.Cancel"),onConfirm:()=>{F&&F.id&&F.name?E.startTransition(()=>{P({projectId:F.id,projectName:F.name}),p.success(i("importArtifactRevisionToFolderModal.CurrentProjectChangedSuccessfully")),d()}):p.error(i("importArtifactRevisionToFolderModal.FailedToRetrieveModelStoreProject"))},children:n.jsx(de,{icon:n.jsx(Te,{})})}),e[43]=S.id,e[44]=p,e[45]=F,e[46]=P,e[47]=i,e[48]=d,e[49]=f):f=e[49];let A;e[50]!==g||e[51]!==f?(A=n.jsxs(j,{gap:"xs",align:"center",children:[g,f]}),e[50]=g,e[51]=f,e[52]=A):A=e[52];let y;e[53]!==G||e[54]!==A?(y=n.jsx(pe.Item,{label:G,name:"vfolderId",rules:X,children:A}),e[53]=G,e[54]=A,e[55]=y):y=e[55];let u;e[56]!==z||e[57]!==y?(u=n.jsx(pe,{ref:o,layout:"vertical",preserve:!1,validateTrigger:H,children:n.jsxs(j,{direction:"column",align:"stretch",children:[z,y]})}),e[56]=z,e[57]=y,e[58]=u):u=e[58];let q;e[59]!==s||e[60]!==$||e[61]!==u||e[62]!==N||e[63]!==Q||e[64]!==O?(q=n.jsx(dn,{title:N,okText:Q,centered:!0,destroyOnHidden:!0,...s,okButtonProps:O,onOk:$,children:u}),e[59]=s,e[60]=$,e[61]=u,e[62]=N,e[63]=Q,e[64]=O,e[65]=q):q=e[65];let W;e[66]!==d?(W=oe=>{var ie,J;d(),oe&&((ie=o.current)==null||ie.setFieldsValue({vfolderId:un("VirtualFolderNode",mn(oe.id))}),(J=v.current)==null||J.refetch())},e[66]=d,e[67]=W):W=e[67];let ee;e[68]!==k||e[69]!==W?(ee=n.jsx(gn,{open:k,initialValidate:!0,folderType:"model_project",onRequestClose:W}),e[68]=k,e[69]=W,e[70]=ee):ee=e[70];let se;return e[71]!==q||e[72]!==ee?(se=n.jsxs(n.Fragment,{children:[q,ee]}),e[71]=q,e[72]=ee,e[73]=se):se=e[73],se};function En(l){return l.id}function Vn(l){return te(l)}function Nn(l){return l.taskId!=null}function _n(l){const e=l.artifactRevision.artifact;return{taskId:l.taskId,version:l.artifactRevision.version,artifact:{id:te(e.id??""),name:e.name??""}}}le.extend(Me);const{Title:On,Text:$n,Paragraph:wn}=ye,Wn=()=>{var _,O,$,H,w,U,z,G,X;const{token:l}=re.useToken(),{t:e}=Ee(),{upsertNotification:s}=fn(),{artifactId:R}=pn(),[c,r]=An(Ae),[i,h]=E.useState([]),[p,o]=E.useState([]),[v,k]=E.useState([]),[C,d]=E.useState([]),[I,S]=vn({filter:yn(Tn,{})}),P=JSON.stringify(I.filter),{baiPaginationOption:B,tablePaginationOption:b,setTablePaginationOption:V}=Fn({current:1,pageSize:10}),F=E.useMemo(()=>({id:R??"",offset:B.offset,limit:B.limit,filter:JSON.parse(P||"{}")}),[R,B.limit,B.offset,P]),M=E.useDeferredValue(F),D=E.useDeferredValue(c),{artifact:t,groups:K}=x.useLazyLoadQuery(Ge,M,{fetchKey:D===Ae?void 0:D,fetchPolicy:D===Ae?"store-and-network":"network-only"}),T=(O=(_=t==null?void 0:t.latestVersion)==null?void 0:_.edges[0])==null?void 0:O.node,N=ve(($=t==null?void 0:t.pullingArtifactRevisions)==null?void 0:$.edges.map(a=>a==null?void 0:a.node)),Q={key:"control",title:e("general.Control"),fixed:!0,required:!0,render:(a,m)=>{var f;const g=m.status;return n.jsxs(j,{gap:"xs",children:[n.jsx(Z,{title:e("reservoirPage.PullThisVersion"),children:n.jsx(Be,{size:"small",revisionsFrgmt:[m],loading:g==="PULLING"||g==="VERIFYING",onClick:()=>{var A,y;(y=(A=t==null?void 0:t.revisions)==null?void 0:A.edges)==null||y.forEach(u=>{u.node.id===m.id&&k([u.node])})}})}),n.jsx(Z,{title:e("importArtifactRevisionToFolderModal.ImportToFolder"),children:n.jsx(xe,{size:"small",revisionsFrgmt:ae(hn((f=t==null?void 0:t.revisions)==null?void 0:f.edges,A=>A.node.id===m.id),"node"),onClick:()=>{var A,y;(y=(A=t==null?void 0:t.revisions)==null?void 0:A.edges)==null||y.forEach(u=>{u.node.id===m.id&&d([u.node])})}})}),n.jsx(Z,{title:e("reservoirPage.RemoveThisVersion"),children:n.jsx(De,{size:"small",title:e("reservoirPage.RemoveThisVersion"),revisionsFrgmt:[m],onClick:()=>{var A,y;(y=(A=t==null?void 0:t.revisions)==null?void 0:A.edges)==null||y.forEach(u=>{u.node.id===m.id&&o([u.node])})}})})]})}};return n.jsxs("div",{children:[n.jsxs(j,{align:"center",style:{marginBottom:l.marginLG},justify:"between",children:[n.jsxs(j,{align:"center",gap:"xs",children:[n.jsx(On,{level:3,style:{margin:0},children:t==null?void 0:t.name}),t&&n.jsx(be,{artifactTypeFrgmt:t})]}),n.jsx(Rn,{value:c,autoUpdateDelay:15e3,loading:D!==c,onChange:()=>{r()}})]}),N.length>0&&n.jsx(j,{direction:"column",gap:"sm",align:"stretch",style:{marginBottom:l.marginMD},children:N.map(a=>n.jsx(Kn,{pullingArtifactRevisionFrgmt:a,onOk:()=>{r()}},a.id))}),n.jsx(he,{title:e("reservoirPage.BasicInformation"),showDivider:!0,extra:n.jsx(Le,{type:"primary",icon:n.jsx(In,{size:16}),onClick:()=>{T&&k([T])},disabled:!T||T.status!=="SCANNED",children:T?e("reservoirPage.PullLatestVersion",{version:T.version}):"N/A"}),style:{marginBottom:l.marginMD},children:n.jsxs(Y,{column:2,bordered:!0,children:[n.jsx(Y.Item,{label:e("reservoirPage.Name"),children:t==null?void 0:t.name}),n.jsx(Y.Item,{label:e("reservoirPage.Type"),children:t&&n.jsx(be,{artifactTypeFrgmt:t})}),n.jsx(Y.Item,{label:e("reservoirPage.Size"),children:n.jsx(L,{monospace:!0,children:T!=null&&T.size?(H=Re(T.size,"auto"))==null?void 0:H.displayValue:"N/A"})}),n.jsx(Y.Item,{label:e("reservoirPage.Source"),children:t!=null&&t.source?n.jsx(ye.Link,{href:t.source.url??"",target:"_blank",rel:"noopener noreferrer",children:t.source.name||"N/A"}):"N/A"}),n.jsx(Y.Item,{label:e("reservoirPage.Registry"),children:n.jsx(ye,{children:t!=null&&t.registry?`${t.registry.name} (${t.registry.url})`:"N/A"})}),n.jsx(Y.Item,{label:e("reservoirPage.LastUpdated"),span:2,children:t!=null&&t.updatedAt?le(t==null?void 0:t.updatedAt).format("lll"):"N/A"}),n.jsx(Y.Item,{label:e("reservoirPage.Description"),span:2,children:t!=null&&t.description?n.jsx(wn,{children:t.description}):"N/A"})]})}),n.jsx(he,{title:e("reservoirPage.VersionList"),showDivider:!0,style:{marginBottom:l.marginMD},styles:{body:{padding:`${l.paddingSM}px ${l.paddingLG}px ${l.paddingLG}px ${l.paddingLG}px`}},children:n.jsxs(j,{direction:"column",gap:"sm",align:"stretch",children:[n.jsxs(j,{align:"stretch",justify:"between",children:[n.jsx(jn,{combinationMode:"AND",onChange:a=>{S({filter:a??{}},"replaceIn")},filterProperties:[{fixedOperator:"equals",propertyLabel:e("reservoirPage.Status"),key:"status",type:"enum",options:ae(["SCANNED","PULLING","PULLED","VERIFYING","NEEDS_APPROVAL","FAILED","AVAILABLE","REJECTED"],a=>({label:a,value:a}))},{fixedOperator:"contains",propertyLabel:e("reservoirPage.Version"),key:"version",type:"string"},{propertyLabel:e("reservoirPage.Size"),key:"size",type:"number",operators:["equals","greaterThan","greaterOrEqual","lessThan","lessOrEqual"]}]}),i.length>0?n.jsxs(j,{gap:"xs",children:[n.jsxs($n,{children:[i.length," selected"]}),n.jsx(Z,{title:e("reservoirPage.PullSelectedVersions"),children:n.jsx(Be,{type:"default",revisionsFrgmt:i.flatMap(a=>a.data),onClick:()=>{t&&k(i.flatMap(a=>a.data))}})}),n.jsx(Z,{title:e("importArtifactRevisionToFolderModal.ImportToFolder"),children:n.jsx(xe,{type:"default",revisionsFrgmt:i.flatMap(a=>a.data),onClick:()=>{t&&d(kn(i,a=>a.data))}})}),n.jsx(Z,{title:e("reservoirPage.RemoveSelectedVersions"),children:n.jsx(De,{style:{borderColor:l.colorBorder},revisionsFrgmt:i.flatMap(a=>a.data),onClick:()=>{t&&o(i.flatMap(a=>a.data))}})})]}):null]}),n.jsx(Mn,{artifactRevisionFrgmt:ve((U=(w=t==null?void 0:t.revisions)==null?void 0:w.edges)==null?void 0:U.map(a=>a.node)),latestRevisionFrgmt:(G=(z=t==null?void 0:t.latestVersion)==null?void 0:z.edges[0])==null?void 0:G.node,loading:M!==F,pagination:{current:b.current,pageSize:b.pageSize,total:((X=t==null?void 0:t.revisions)==null?void 0:X.count)??0,onChange:(a,m)=>{Se(a)&&Se(m)&&V({current:a,pageSize:m})}},onRow:a=>({onClick:m=>{var A,y;m.stopPropagation();const g=m.target;if(g.closest("button")||g.closest("a")||!t)return;const f=(y=(A=t.revisions)==null?void 0:A.edges.find(u=>u.node.id===a.id))==null?void 0:y.node;f&&h(u=>{const q=u.filter(W=>W.id!==a.id);return q.length===u.length?[...u,{id:a.id,data:f}]:q})}}),rowSelection:{type:"checkbox",onChange:a=>{if(!(t!=null&&t.revisions))return;const m=t.revisions,g=m.edges.map(f=>f.node.id);h(f=>{const A=f.filter(u=>!g.includes(u.id)),y=m.edges.filter(u=>a.includes(u.node.id)).map(u=>({id:u.node.id,data:u.node}));return A.concat(y)})},selectedRowKeys:i.map(a=>a.id)},customizeColumns:a=>[a[0],a[1],Q,...a.slice(2)]})]})}),n.jsx(Pn,{selectedArtifactFrgmt:t??null,selectedArtifactRevisionFrgmt:v,open:!!t&&!ne(v),connectionIds:t!=null&&t.pullingArtifactRevisions?[t.pullingArtifactRevisions.__id]:void 0,onOk:(a,m)=>{k([]),m.forEach(g=>{s({message:e("reservoirPage.PullingArtifact",{name:g.artifact.name,version:g.version}),type:"info",open:!0,duration:0,backgroundTask:{status:"pending",taskId:g.taskId,promise:null,percent:0,onChange:{resolved:(f,A)=>({type:"success",message:e("reservoirPage.SuccessFullyPulledArtifact",{name:g.artifact.name,version:g.version}),showIcon:!0,toText:e("reservoirPage.GoToArtifact"),to:`/reservoir/${g.artifact.id}`}),rejected:(f,A)=>e("reservoirPage.FailedToPullArtifact",{name:g.artifact.name,version:g.version})}}})})},onCancel:()=>{k([])}}),n.jsx(Ln,{selectedArtifactFrgmt:t??null,selectedArtifactRevisionFrgmt:p,onOk:()=>{o([])},onCancel:()=>{o([])},open:!!t&&!ne(p)}),n.jsx(Cn,{selectedArtifactRevisionFrgmt:C,modelStoreProjectsFrgmt:(K==null?void 0:K[0])??void 0,onOk:(a,m,g)=>{d([]),r(),m.forEach(f=>{s({message:e("importArtifactRevisionToFolderModal.ImportingArtifact",{name:f.artifact.name,version:f.version}),type:"info",open:!0,duration:0,backgroundTask:{status:"pending",taskId:f.taskId,promise:null,percent:0,onChange:{resolved:(A,y)=>({type:"success",message:e("importArtifactRevisionToFolderModal.SuccessfullyImportedArtifact",{name:f.artifact.name,version:f.version}),showIcon:!0,toText:e(g?"data.folders.OpenAFolder":"reservoirPage.GoToArtifact"),to:g?{search:new URLSearchParams({folder:te(g)}).toString()}:`/reservoir/${f.artifact.id}`}),rejected:(A,y)=>e("importArtifactRevisionToFolderModal.FailedToImportArtifact",{name:f.artifact.name,version:f.version})}}})})},onCancel:()=>{d([])},open:!!t&&!ne(C)})]})};export{Wn as default};
//# sourceMappingURL=ReservoirArtifactDetailPage-Bmty8hxZ.js.map
