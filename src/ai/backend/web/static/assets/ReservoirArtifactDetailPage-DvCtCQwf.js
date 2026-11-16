import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Bt as t,H as n,Qt as r,Zn as i,f as a}from"./icons-Btg1s2wy.js";import{t as o}from"./compiler-runtime-CZQb2eIb.js";import{St as s,T as c,V as l,_t as u,bt as d,nt as f,ot as p,vt as m}from"./lodash-ClfL87UH.js";/* empty css            */import{t as h}from"./jsx-runtime-BapUIyWk.js";import{t as g}from"./Tooltip-QQJy2agO.js";import{L as ee,R as te,_}from"./usePressFeedback-BIoIGSxE.js";import{U as v,at as ne,s as y}from"./DefaultProviders-BFjPhnQa.js";import{t as b}from"./Button-BKkkrlg5.js";import{n as x,r as re}from"./Skeleton-D35z7Ria.js";import{t as S}from"./Form-DK4EItCB.js";import"./form-engine-mhqCLVoE.js";import{t as C}from"./BAIFlex-BElkJeHW.js";import{t as ie}from"./BAIButton-FCOTP7us.js";import{t as w}from"./Badge-8q4sdq1t.js";import{r as T,t as ae}from"./BAIMetadataList-B6UX8yzh.js";import{a as E,t as oe}from"./app-shim-DTEBzR8d.js";import{s as se}from"./useThemeMode-Dg5yAWy7.js";import{ot as ce}from"./helper-BWFKT_2Y.js";import{t as le}from"./hooks-UUY7pxyu.js";import{t as D}from"./react-relay-BfoHYpUf.js";import{t as ue}from"./useBAILogger-CRaS0DnM.js";import{t as de}from"./useToggle-CAWNf18k.js";import{C as fe,S as pe,a as me,l as O,u as k}from"./helper-DF1Eunoe.js";import{t as he}from"./BAISelect-D7nL9svF.js";import{t as A}from"./dayjs.min-PJVk-kyH.js";import{n as ge}from"./BAIPropertyFilter-Bp3-ZYGr.js";import{t as j}from"./BAIGraphQLPropertyFilter-CNTUQIkF.js";import{t as M}from"./BAIUnmountAfterClose-Cxr4Dp_U.js";import{t as _e}from"./BAIQuestionIconWithTooltip-C0Z6oRPw.js";import{t as N}from"./BAIText-CtDfjLnS.js";import{t as ve}from"./BAIModal-XZIjYM23.js";import{t as ye}from"./Banner-ElTQ2msG.js";import{t as P}from"./BAITable-BRd_Ua6I.js";import{a as F,i as I,n as L,r as R,t as be}from"./BAIImportArtifactModal-DDsWMeWH.js";import{t as z}from"./BAIEntityLabelTargetCell-BQUwCrEl.js";import{t as xe}from"./BAIVFolderSelect-BPVplxzQ.js";import{n as Se,o as Ce}from"./dist-C3M-rFln.js";import{r as we}from"./pathBuilder-BpKje1m9.js";import{V as Te,ht as Ee,pt as B,t as De}from"./index-49VU5B_r.js";import{t as Oe}from"./AutoUpdateFetchKeyButton-C-RHyKup.js";import{n as ke}from"./reactPaginationQueryOptions-DUCwh22X.js";import{t as Ae}from"./FolderCreateModal-CeqkMhk8.js";var V={argumentDefinitions:[],kind:`Fragment`,metadata:{plural:!0},name:`BAIArtifactRevisionTableArtifactRevisionFragment`,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`version`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`size`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`updatedAt`,storageKey:null},{args:null,kind:`FragmentSpread`,name:`BAIArtifactStatusBadgeFragment`},{args:null,kind:`FragmentSpread`,name:`BAIArtifactRevisionDownloadButtonFragment`},{args:null,kind:`FragmentSpread`,name:`BAIArtifactRevisionDeleteButtonFragment`}],type:`ArtifactRevision`,abstractKey:null};V.hash=`4b886a8f1069332114e0162802fc049f`;var je={argumentDefinitions:[],kind:`Fragment`,metadata:null,name:`BAIArtifactRevisionTableLatestRevisionFragment`,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null}],type:`ArtifactRevision`,abstractKey:null};je.hash=`7598c47b813de8a7d1823fd229eeda60`;var H=e(A(),1),Me=e(v(),1),U=D(),W=h();H.default.extend(Me.default);var Ne=({artifactRevisionFrgmt:e,latestRevisionFrgmt:t,customizeColumns:n,...r})=>{let{t:i}=x(),a=(0,U.useFragment)(V,e),o=(0,U.useFragment)(je,t),s=m(O([{title:i(`comp:BAIArtifactRevisionTable.Version`),dataIndex:`version`,key:`version`,render:(e,t)=>(0,W.jsx)(`div`,{children:(0,W.jsxs)(C,{align:`center`,gap:`xs`,children:[(0,W.jsx)(N,{monospace:!0,strong:!0,children:e}),o&&o.id===t.id&&(0,W.jsx)(w,{variant:`info`,label:`Latest`}),t.status===`PULLED`&&(0,W.jsx)(w,{variant:`neutral`,label:t.status})]})})},{title:i(`comp:BAIArtifactRevisionTable.Status`),dataIndex:`status`,key:`status`,render:(e,t)=>(0,W.jsx)(F,{artifactRevisionFrgmt:t})},{title:i(`comp:BAIArtifactRevisionTable.Size`),dataIndex:`size`,key:`size`,render:e=>{var t;return e?(0,W.jsx)(N,{monospace:!0,children:(t=me(e,`auto`))==null?void 0:t.displayValue}):(0,W.jsx)(N,{monospace:!0,children:`N/A`})}},{title:i(`comp:BAIArtifactTable.Updated`),dataIndex:`updatedAt`,key:`updatedAt`,render:e=>e?(0,W.jsx)(N,{type:`secondary`,title:(0,H.default)(e).toString(),children:(0,H.default)(e).fromNow()}):`N/A`}])),c=n?n(s):s;return(0,W.jsx)(P,{scroll:{x:`max-content`},rowKey:e=>e.id,resizable:!0,columns:c,dataSource:a,...r})},G={argumentDefinitions:[],kind:`Fragment`,metadata:null,name:`BAIPullingArtifactRevisionAlertFragment`,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`fieldId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`version`,storageKey:null}],type:`ArtifactRevision`,abstractKey:null};G.hash=`e6966f472baffdb60ebb71b731174e9e`;var K=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`input`}],t=[{alias:null,args:[{kind:`Variable`,name:`input`,variableName:`input`}],concreteType:`CancelImportArtifactPayload`,kind:`LinkedField`,name:`cancelImportArtifact`,plural:!1,selections:[{alias:null,args:null,concreteType:`ArtifactRevision`,kind:`LinkedField`,name:`artifactRevision`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`BAIPullingArtifactRevisionAlertCancelMutation`,selections:t,type:`Mutation`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`BAIPullingArtifactRevisionAlertCancelMutation`,selections:t},params:{cacheID:`2b4debfb8df103ad97421b0869b31402`,id:null,metadata:{},name:`BAIPullingArtifactRevisionAlertCancelMutation`,operationKind:`mutation`,text:`mutation BAIPullingArtifactRevisionAlertCancelMutation(
  $input: CancelArtifactInput!
) {
  cancelImportArtifact(input: $input) {
    artifactRevision {
      id
      status
    }
  }
}
`}}})();K.hash=`18b2b20bc4ed731fcd89e1469e73b49c`;var Pe=({pullingArtifactRevisionFrgmt:e,onOk:t})=>{let{t:n}=x(),{modal:r,message:i}=oe.useApp(),a=(0,U.useFragment)(G,e),[o,s]=(0,U.useMutation)(K);return(0,W.jsx)(Te,{type:`info`,showIcon:!0,title:n(`comp:BAIPullingArtifactRevisionAlert.VersionIsPullingNow`,{version:a.version}),action:(0,W.jsx)(ie,{type:`text`,onClick:()=>{r.confirm({title:n(`comp:BAIPullingArtifactRevisionAlert.CancelPull`),content:(0,W.jsxs)(C,{direction:`column`,align:`stretch`,children:[(0,W.jsxs)(N,{children:[n(`comp:BAIPullingArtifactRevisionAlert.YouAreAboutToCancelThisVersion`),`:`,(0,W.jsxs)(N,{strong:!0,children:[`\xA0`,a.version]})]}),(0,W.jsx)(`br`,{}),(0,W.jsxs)(N,{type:`danger`,children:[(0,W.jsxs)(N,{type:`danger`,strong:!0,children:[n(`comp:BAIPullingArtifactRevisionAlert.WARNING`),`:`]}),`\xA0`,n(`comp:BAIPullingArtifactRevisionAlert.CancelingWillRestartThePulling`)]})]}),cancelText:n(`general.button.Close`),okButtonProps:{danger:!0,loading:s},onOk:()=>{o({variables:{input:{artifactRevisionId:a.fieldId}},onCompleted:(e,r)=>{r&&r.length>0?r.forEach(e=>i.error(e.message??n(`comp:BAIPullingArtifactRevisionAlert.FailedToCancelThePulling`))):(t==null||t(),i.success(n(`comp:BAIPullingArtifactRevisionAlert.VersionPullCanceledSuccessfully`,{version:a.version})))},onError:e=>{i.error(e.message??n(`comp:BAIPullingArtifactRevisionAlert.FailedToCancelThePulling`))}})}})},children:n(`general.button.Cancel`)})})},Fe=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`input`}],t=[{kind:`Variable`,name:`input`,variableName:`input`}],n={alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null};return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`BAIDeleteArtifactRevisionsModalCleanupVersionMutation`,selections:[{alias:null,args:t,concreteType:`CleanupArtifactRevisionsPayload`,kind:`LinkedField`,name:`cleanupArtifactRevisions`,plural:!1,selections:[{alias:null,args:null,concreteType:`ArtifactRevisionConnection`,kind:`LinkedField`,name:`artifactRevisions`,plural:!1,selections:[{alias:null,args:null,concreteType:`ArtifactRevisionEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ArtifactRevision`,kind:`LinkedField`,name:`node`,plural:!1,selections:[n],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:`Mutation`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`BAIDeleteArtifactRevisionsModalCleanupVersionMutation`,selections:[{alias:null,args:t,concreteType:`CleanupArtifactRevisionsPayload`,kind:`LinkedField`,name:`cleanupArtifactRevisions`,plural:!1,selections:[{alias:null,args:null,concreteType:`ArtifactRevisionConnection`,kind:`LinkedField`,name:`artifactRevisions`,plural:!1,selections:[{alias:null,args:null,concreteType:`ArtifactRevisionEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ArtifactRevision`,kind:`LinkedField`,name:`node`,plural:!1,selections:[n,{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:`03897a25039ccf906a0013edbae95224`,id:null,metadata:{},name:`BAIDeleteArtifactRevisionsModalCleanupVersionMutation`,operationKind:`mutation`,text:`mutation BAIDeleteArtifactRevisionsModalCleanupVersionMutation(
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
`}}})();Fe.hash=`a1b18aa3dacff842d5e39ba15c4e3994`;var Ie={argumentDefinitions:[],kind:`Fragment`,metadata:null,name:`BAIDeleteArtifactRevisionsModalArtifactFragment`,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{args:null,kind:`FragmentSpread`,name:`BAIArtifactDescriptionsFragment`}],type:`Artifact`,abstractKey:null};Ie.hash=`8eac061158289fcc677ac78d52d22410`;var Le={argumentDefinitions:[],kind:`Fragment`,metadata:{plural:!0},name:`BAIDeleteArtifactRevisionsModalArtifactRevisionFragment`,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`fieldId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`version`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`size`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null}],type:`ArtifactRevision`,abstractKey:null};Le.hash=`621b082dd3c1f76c46533833531e4ecd`;var Re=({selectedArtifactFrgmt:e,selectedArtifactRevisionFrgmt:t,onOk:n,onCancel:r,...i})=>{let{t:a}=x(),{token:o}=_(),[s,c]=(0,U.useMutation)(Fe),l=(0,U.useFragment)(Ie,e),u=(0,U.useFragment)(Le,t),d=u.filter(e=>e.status!==`PULLING`&&e.status!==`SCANNED`),f=[{title:a(`comp:BAIDeleteArtifactModal.Version`),dataIndex:`version`,key:`version`,render:e=>(0,W.jsx)(N,{monospace:!0,children:e}),width:`50%`},{title:a(`comp:BAIDeleteArtifactModal.Size`),dataIndex:`size`,key:`size`,render:e=>{var t;return(0,W.jsx)(N,{monospace:!0,children:e?(t=me(e,`auto`))==null?void 0:t.displayValue:`N/A`})}}];return(0,W.jsx)(M,{children:(0,W.jsx)(ve,{title:a(`comp:BAIDeleteArtifactModal.RemoveVersions`),centered:!0,onOk:e=>{s({variables:{input:{artifactRevisionIds:d.map(e=>e.fieldId)}},onCompleted:(t,r)=>{if(r&&r.length>0){r.forEach(e=>{E.error(e.message??a(`comp:BAIDeleteArtifactModal.FailedToRemoveVersions`))});return}let i=t.cleanupArtifactRevisions;i?(E.success(a(`comp:BAIDeleteArtifactModal.SuccessFullyRemoved`,{count:i.artifactRevisions.edges.length})),n(e)):E.error(a(`comp:BAIDeleteArtifactModal.FailedToRemoveVersions`))},onError:e=>{E.error(e.message??a(`comp:BAIDeleteArtifactModal.FailedToRemoveVersions`))}})},onCancel:e=>{r(e)},okText:a(`general.button.Remove`),cancelText:a(`general.button.Cancel`),okButtonProps:{danger:!0,loading:c,disabled:p(d)||c},...i,children:(0,W.jsxs)(C,{direction:`column`,gap:`sm`,align:`stretch`,children:[d.length===u.length?null:(0,W.jsx)(Te,{icon:(0,W.jsx)(_e,{title:a(`comp:BAIDeleteArtifactModal.OnlyVersionsNotInPULLINGOrSCANNED`),iconProps:{style:{color:o(`--color-info`)}},style:{marginRight:o(`--spacing-2`)}}),showIcon:!0,title:a(`comp:BAIDeleteArtifactModal.ExcludedVersions`,{count:u.length-d.length})}),l&&(0,W.jsx)(L,{artifactFrgmt:l}),(0,W.jsx)(P,{columns:O(f),dataSource:k(u),pagination:{showSizeChanger:!1}})]})})})},q={argumentDefinitions:[],kind:`Fragment`,metadata:{plural:!0},name:`BAIArtifactRevisionDeleteButtonFragment`,selections:[{alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null}],type:`ArtifactRevision`,abstractKey:null};q.hash=`de15aa32192b0f0d63e3bd7f5f90d2b6`;var J=({revisionsFrgmt:e,...t})=>{let{token:n}=_(),r=(0,U.useFragment)(q,e).some(e=>e.status!==`SCANNED`&&e.status!==`PULLING`),i=t.disabled||t.loading||!r;return(0,W.jsx)(ie,{icon:(0,W.jsx)(a,{size:`1em`}),disabled:i,type:`text`,style:{color:n(i?`--color-text-disabled`:`--color-error`),background:n(i?`--color-bg-container-disabled`:`--color-error-bg`),...t.style},...l(t,[`style`,`disabled`,`loading`])})},Y=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`filter`},t={defaultValue:null,kind:`LocalArgument`,name:`id`},n={defaultValue:null,kind:`LocalArgument`,name:`limit`},r={defaultValue:null,kind:`LocalArgument`,name:`offset`},i=[{kind:`Variable`,name:`id`,variableName:`id`}],a={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},o={alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},s={alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},c={alias:null,args:null,kind:`ScalarField`,name:`description`,storageKey:null},l=[s,{alias:null,args:null,kind:`ScalarField`,name:`url`,storageKey:null}],u={alias:null,args:null,concreteType:`SourceInfo`,kind:`LinkedField`,name:`registry`,plural:!1,selections:l,storageKey:null},d={alias:null,args:null,concreteType:`SourceInfo`,kind:`LinkedField`,name:`source`,plural:!1,selections:l,storageKey:null},f={alias:null,args:null,kind:`ScalarField`,name:`updatedAt`,storageKey:null},p={kind:`Literal`,name:`orderBy`,value:[{direction:`DESC`,field:`VERSION`},{direction:`DESC`,field:`UPDATED_AT`}]},m=[{kind:`Literal`,name:`filter`,value:{status:{equals:`PULLING`}}},p],h={alias:null,args:null,kind:`ScalarField`,name:`count`,storageKey:null},g={alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null},ee={alias:null,args:null,kind:`ScalarField`,name:`__typename`,storageKey:null},te={alias:null,args:null,kind:`ScalarField`,name:`cursor`,storageKey:null},_={alias:null,args:null,concreteType:`PageInfo`,kind:`LinkedField`,name:`pageInfo`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`endCursor`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`hasNextPage`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`hasPreviousPage`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`startCursor`,storageKey:null}],storageKey:null},v={kind:`ClientExtension`,selections:[{alias:null,args:null,kind:`ScalarField`,name:`__id`,storageKey:null}]},ne=[{kind:`Literal`,name:`limit`,value:1},p],y={alias:null,args:null,kind:`ScalarField`,name:`size`,storageKey:null},b={alias:null,args:null,kind:`ScalarField`,name:`version`,storageKey:null},x={args:null,kind:`FragmentSpread`,name:`BAIImportArtifactModalArtifactRevisionFragment`},re=[{kind:`Variable`,name:`filter`,variableName:`filter`},{kind:`Variable`,name:`limit`,variableName:`limit`},{kind:`Variable`,name:`offset`,variableName:`offset`},p],S=[{kind:`Literal`,name:`is_active`,value:!0},{kind:`Literal`,name:`type`,value:[`MODEL_STORE`]}],C={alias:null,args:null,kind:`ScalarField`,name:`fieldId`,storageKey:null};return{fragment:{argumentDefinitions:[e,t,n,r],kind:`Fragment`,metadata:null,name:`ReservoirArtifactDetailPageQuery`,selections:[{alias:null,args:i,concreteType:`Artifact`,kind:`LinkedField`,name:`artifact`,plural:!1,selections:[a,o,s,{args:null,kind:`FragmentSpread`,name:`BAIArtifactTypeTokenFragment`},c,u,d,f,{alias:`pullingArtifactRevisions`,args:m,concreteType:`ArtifactRevisionConnection`,kind:`LinkedField`,name:`__ReservoirArtifactDetailPage_pullingArtifactRevisions_connection`,plural:!1,selections:[h,{alias:null,args:null,concreteType:`ArtifactRevisionEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ArtifactRevision`,kind:`LinkedField`,name:`node`,plural:!1,selections:[a,g,{args:null,kind:`FragmentSpread`,name:`BAIPullingArtifactRevisionAlertFragment`},ee],storageKey:null},te],storageKey:null},_,v],storageKey:`__ReservoirArtifactDetailPage_pullingArtifactRevisions_connection(filter:{"status":{"equals":"PULLING"}},orderBy:[{"direction":"DESC","field":"VERSION"},{"direction":"DESC","field":"UPDATED_AT"}])`},{alias:`latestVersion`,args:ne,concreteType:`ArtifactRevisionConnection`,kind:`LinkedField`,name:`revisions`,plural:!1,selections:[{alias:null,args:null,concreteType:`ArtifactRevisionEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ArtifactRevision`,kind:`LinkedField`,name:`node`,plural:!1,selections:[a,y,b,g,x,{args:null,kind:`FragmentSpread`,name:`BAIArtifactRevisionTableLatestRevisionFragment`}],storageKey:null}],storageKey:null}],storageKey:`revisions(limit:1,orderBy:[{"direction":"DESC","field":"VERSION"},{"direction":"DESC","field":"UPDATED_AT"}])`},{alias:null,args:re,concreteType:`ArtifactRevisionConnection`,kind:`LinkedField`,name:`revisions`,plural:!1,selections:[h,{alias:null,args:null,concreteType:`ArtifactRevisionEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ArtifactRevision`,kind:`LinkedField`,name:`node`,plural:!1,selections:[a,g,{args:null,kind:`FragmentSpread`,name:`BAIArtifactRevisionTableArtifactRevisionFragment`},x,{args:null,kind:`FragmentSpread`,name:`BAIDeleteArtifactRevisionsModalArtifactRevisionFragment`},{args:null,kind:`FragmentSpread`,name:`BAIArtifactRevisionDeleteButtonFragment`},{args:null,kind:`FragmentSpread`,name:`BAIArtifactRevisionDownloadButtonFragment`},{args:null,kind:`FragmentSpread`,name:`ImportArtifactRevisionToFolderButtonFragment`},{args:null,kind:`FragmentSpread`,name:`ImportArtifactRevisionToFolderModalArtifactRevisionFragment`}],storageKey:null}],storageKey:null}],storageKey:null},{args:null,kind:`FragmentSpread`,name:`BAIImportArtifactModalArtifactFragment`},{args:null,kind:`FragmentSpread`,name:`BAIDeleteArtifactRevisionsModalArtifactFragment`}],storageKey:null},{alias:null,args:S,concreteType:`Group`,kind:`LinkedField`,name:`groups`,plural:!0,selections:[{args:null,kind:`FragmentSpread`,name:`ImportArtifactRevisionToFolderModalModelStoreProjectsFragment`}],storageKey:`groups(is_active:true,type:["MODEL_STORE"])`}],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[t,r,n,e],kind:`Operation`,name:`ReservoirArtifactDetailPageQuery`,selections:[{alias:null,args:i,concreteType:`Artifact`,kind:`LinkedField`,name:`artifact`,plural:!1,selections:[a,o,s,{alias:null,args:null,kind:`ScalarField`,name:`type`,storageKey:null},c,u,d,f,{alias:`pullingArtifactRevisions`,args:m,concreteType:`ArtifactRevisionConnection`,kind:`LinkedField`,name:`revisions`,plural:!1,selections:[h,{alias:null,args:null,concreteType:`ArtifactRevisionEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ArtifactRevision`,kind:`LinkedField`,name:`node`,plural:!1,selections:[a,g,C,b,ee],storageKey:null},te],storageKey:null},_,v],storageKey:`revisions(filter:{"status":{"equals":"PULLING"}},orderBy:[{"direction":"DESC","field":"VERSION"},{"direction":"DESC","field":"UPDATED_AT"}])`},{alias:`pullingArtifactRevisions`,args:m,filters:[`filter`,`orderBy`],handle:`connection`,key:`ReservoirArtifactDetailPage_pullingArtifactRevisions`,kind:`LinkedHandle`,name:`revisions`},{alias:`latestVersion`,args:ne,concreteType:`ArtifactRevisionConnection`,kind:`LinkedField`,name:`revisions`,plural:!1,selections:[{alias:null,args:null,concreteType:`ArtifactRevisionEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ArtifactRevision`,kind:`LinkedField`,name:`node`,plural:!1,selections:[a,y,b,g,C],storageKey:null}],storageKey:null}],storageKey:`revisions(limit:1,orderBy:[{"direction":"DESC","field":"VERSION"},{"direction":"DESC","field":"UPDATED_AT"}])`},{alias:null,args:re,concreteType:`ArtifactRevisionConnection`,kind:`LinkedField`,name:`revisions`,plural:!1,selections:[h,{alias:null,args:null,concreteType:`ArtifactRevisionEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ArtifactRevision`,kind:`LinkedField`,name:`node`,plural:!1,selections:[a,g,b,y,f,C],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:S,concreteType:`Group`,kind:`LinkedField`,name:`groups`,plural:!0,selections:[a,s],storageKey:`groups(is_active:true,type:["MODEL_STORE"])`}]},params:{cacheID:`a6e802855c2409693ae1093619db2233`,id:null,metadata:{connection:[{count:null,cursor:null,direction:`bidirectional`,path:[`artifact`,`pullingArtifactRevisions`]}]},name:`ReservoirArtifactDetailPageQuery`,operationKind:`query`,text:`query ReservoirArtifactDetailPageQuery(
  $id: ID!
  $offset: Int!
  $limit: Int!
  $filter: ArtifactRevisionFilter!
) {
  artifact(id: $id) {
    id
    entityId
    name
    ...BAIArtifactTypeTokenFragment
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
  ...BAIArtifactTypeTokenFragment
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
  ...BAIArtifactStatusBadgeFragment
  ...BAIArtifactRevisionDownloadButtonFragment
  ...BAIArtifactRevisionDeleteButtonFragment
}

fragment BAIArtifactRevisionTableLatestRevisionFragment on ArtifactRevision {
  id
}

fragment BAIArtifactStatusBadgeFragment on ArtifactRevision {
  status
}

fragment BAIArtifactTypeTokenFragment on Artifact {
  type
}

fragment BAIDeleteArtifactRevisionsModalArtifactFragment on Artifact {
  id
  ...BAIArtifactDescriptionsFragment
}

fragment BAIDeleteArtifactRevisionsModalArtifactRevisionFragment on ArtifactRevision {
  id
  fieldId
  version
  size
  status
}

fragment BAIImportArtifactModalArtifactFragment on Artifact {
  id
  entityId
  name
  ...BAIArtifactDescriptionsFragment
}

fragment BAIImportArtifactModalArtifactRevisionFragment on ArtifactRevision {
  id
  fieldId
  version
  size
  status
}

fragment BAIPullingArtifactRevisionAlertFragment on ArtifactRevision {
  id
  fieldId
  status
  version
}

fragment ImportArtifactRevisionToFolderButtonFragment on ArtifactRevision {
  status
}

fragment ImportArtifactRevisionToFolderModalArtifactRevisionFragment on ArtifactRevision {
  id
  fieldId
}

fragment ImportArtifactRevisionToFolderModalModelStoreProjectsFragment on Group {
  id
  name
}
`}}})();Y.hash=`a67fbf1a7f8fc8cbd337a59681eaab16`;var X={argumentDefinitions:[],kind:`Fragment`,metadata:{plural:!0},name:`ImportArtifactRevisionToFolderButtonFragment`,selections:[{alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null}],type:`ArtifactRevision`,abstractKey:null};X.hash=`fb4797e7e04df882a22890d1e13925c2`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var Z=({revisionsFrgmt:e,...n})=>{let{token:r}=_(),i=(0,U.useFragment)(X,e),a=!c(i,e=>e.status===`SCANNED`)||n.disabled||n.loading;return(0,W.jsx)(ie,{icon:(0,W.jsx)(t,{}),disabled:a,type:`text`,style:{color:r(a?`--color-text-disabled`:`--color-info`),background:r(a?`--color-bg-container-disabled`:`--color-info-bg`),...n.style},...l(n,[`disabled`,`loading`])})},ze=o(),Be={argumentDefinitions:[],kind:`Fragment`,metadata:{plural:!0},name:`ImportArtifactRevisionToFolderModalArtifactRevisionFragment`,selections:[{kind:`RequiredField`,field:{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},action:`THROW`},{alias:null,args:null,kind:`ScalarField`,name:`fieldId`,storageKey:null}],type:`ArtifactRevision`,abstractKey:null};Be.hash=`c861ecf6447307347af2aee9efb8f8fa`;var Ve={argumentDefinitions:[],kind:`Fragment`,metadata:{plural:!0},name:`ImportArtifactRevisionToFolderModalModelStoreProjectsFragment`,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null}],type:`Group`,abstractKey:null};Ve.hash=`03c2ef0be48adf59428cecc52d866468`;var He=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`input`}],t={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},n=[{alias:null,args:[{kind:`Variable`,name:`input`,variableName:`input`}],concreteType:`ImportArtifactsPayload`,kind:`LinkedField`,name:`importArtifacts`,plural:!1,selections:[{alias:null,args:null,concreteType:`ArtifactRevisionConnection`,kind:`LinkedField`,name:`artifactRevisions`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`count`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ArtifactRevisionImportTask`,kind:`LinkedField`,name:`tasks`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`taskId`,storageKey:null},{alias:null,args:null,concreteType:`ArtifactRevision`,kind:`LinkedField`,name:`artifactRevision`,plural:!1,selections:[t,{alias:null,args:null,kind:`ScalarField`,name:`version`,storageKey:null},{alias:null,args:null,concreteType:`Artifact`,kind:`LinkedField`,name:`artifact`,plural:!1,selections:[t,{alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`ImportArtifactRevisionToFolderModalMutation`,selections:n,type:`Mutation`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`ImportArtifactRevisionToFolderModalMutation`,selections:n},params:{cacheID:`262f08ff2a989f5cccb0d71fe230e8ac`,id:null,metadata:{},name:`ImportArtifactRevisionToFolderModalMutation`,operationKind:`mutation`,text:`mutation ImportArtifactRevisionToFolderModalMutation(
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
          entityId
          name
        }
      }
    }
  }
}
`}}})();He.hash=`259eea7c2fef122ffd906edd5d7b9a4c`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var Q=e(i(),1),Ue=e=>{"use memo";let t=(0,ze.c)(113),r,i,a,o;t[0]===e?(r=t[1],i=t[2],a=t[3],o=t[4]):({selectedArtifactRevisionFrgmt:o,modelStoreProjectsFrgmt:i,onOk:a,...r}=e,t[0]=e,t[1]=r,t[2]=i,t[3]=a,t[4]=o);let{t:c}=re(),{token:l}=_(),{message:u}=oe.useApp(),f=(0,Q.useRef)(null),h=(0,Q.useRef)(null),[ee,te]=de(!1),{toggle:v}=te,{logger:ne}=ue(),y=(0,U.useFragment)(Be,o),b=(0,U.useFragment)(Ve,i),x=m(s(b,We),Ge),[w,T]=(0,Q.useState)(),ae;t[5]!==b||t[6]!==w?(ae=d(b,e=>(e==null?void 0:e.id)===w)??(b==null?void 0:b[0]),t[5]=b,t[6]=w,t[7]=ae):ae=t[7];let E=ae,[se,ce]=(0,U.useMutation)(He),le;t[8]===y?le=t[9]:(le=m(y,Ke),t[8]=y,t[9]=le);let D=le,me=ve,O;t[10]===c?O=t[11]:(O=c(`importArtifactRevisionToFolderModal.ImportToFolder`),t[10]=c,t[11]=O);let k;t[12]===c?k=t[13]:(k=c(`importArtifactRevisionToFolderModal.Import`),t[12]=c,t[13]=k);let A;t[14]!==ce||t[15]!==y?(A=ce||p(y),t[14]=ce,t[15]=y,t[16]=A):A=t[16];let j;t[17]!==ce||t[18]!==A?(j={loading:ce,disabled:A},t[17]=ce,t[18]=A,t[19]=j):j=t[19];let M;t[20]!==se||t[21]!==ne||t[22]!==u||t[23]!==a||t[24]!==D||t[25]!==y||t[26]!==c?(M=e=>{var t;(t=f.current)==null||t.validateFields().then(t=>{p(y)?u.error(c(`importArtifactRevisionToFolderModal.NoArtifactsSelected`)):se({variables:{input:{artifactRevisionIds:D,vfolderId:t.vfolderId?fe(t.vfolderId):null,options:{force:!0}}},onCompleted:(n,r)=>{var i;if(r&&r.length>0){r.forEach(e=>u.error(e.message??c(`importArtifactRevisionToFolderModal.FailedToImport`)));return}let o=n.importArtifacts;if(!o)u.error(c(`importArtifactRevisionToFolderModal.FailedToImport`));else if(((i=o.artifactRevisions)==null?void 0:i.count)>0){u.success(c(`importArtifactRevisionToFolderModal.SuccessfullyImported`));let n=o.tasks.filter(qe).map(Je);a==null||a(e,n,t.vfolderId)}else u.error(c(`importArtifactRevisionToFolderModal.FailedToImport`))},onError:e=>{u.error(e.message??c(`importArtifactRevisionToFolderModal.FailedToImport`))}})}).catch(e=>{ne.error(`ImportArtifactRevisionToFolderModal: Form validation failed`,{error:e})})},t[20]=se,t[21]=ne,t[22]=u,t[23]=a,t[24]=D,t[25]=y,t[26]=c,t[27]=M):M=t[27];let _e=S,N;t[28]===Symbol.for(`react.memo_cache_sentinel`)?(N=[`onChange`,`onBlur`],t[28]=N):N=t[28];let P=C,F;t[29]===c?F=t[30]:(F=c(`importArtifactRevisionToFolderModal.OverwriteWarning`),t[29]=c,t[30]=F);let I;t[31]===l?I=t[32]:(I=l(`--spacing-5`),t[31]=l,t[32]=I);let L;t[33]===I?L=t[34]:(L={marginBottom:I},t[33]=I,t[34]=L);let R;t[35]!==F||t[36]!==L?(R=(0,W.jsx)(ye,{role:`alert`,status:`warning`,title:F,style:L}),t[35]=F,t[36]=L,t[37]=R):R=t[37];let be=S,z;t[38]===c?z=t[39]:(z=c(`importArtifactRevisionToFolderModal.ModelStoreProject`),t[38]=c,t[39]=z);let Se=he,Ce=(E==null?void 0:E.id)??void 0,we=p(x),Te=p(x)?`error`:void 0,Ee=p(x)?c(`importArtifactRevisionToFolderModal.FailedToRetrieveModelStoreProject`):void 0,B;t[40]===T?B=t[41]:(B=e=>{var t;T(e),(t=f.current)==null||t.setFieldsValue({vfolderId:void 0})},t[40]=T,t[41]=B);let Oe;t[42]!==Se||t[43]!==x||t[44]!==Ce||t[45]!==we||t[46]!==Te||t[47]!==Ee||t[48]!==B?(Oe=(0,W.jsx)(Se,{"data-testid":`import-artifact-model-store-project-select`,value:Ce,options:x,disabled:we,status:Te,tooltip:Ee,popupMatchSelectWidth:!1,onChange:B}),t[42]=Se,t[43]=x,t[44]=Ce,t[45]=we,t[46]=Te,t[47]=Ee,t[48]=B,t[49]=Oe):Oe=t[49];let ke;t[50]!==be.Item||t[51]!==z||t[52]!==Oe?(ke=(0,W.jsx)(be.Item,{label:z,children:Oe}),t[50]=be.Item,t[51]=z,t[52]=Oe,t[53]=ke):ke=t[53];let V;t[54]===c?V=t[55]:(V=c(`importArtifactRevisionToFolderModal.FolderMountForModelStore`),t[54]=c,t[55]=V);let je;t[56]===Symbol.for(`react.memo_cache_sentinel`)?(je=[{required:!0}],t[56]=je):je=t[56];let H;t[57]===c?H=t[58]:(H=c(`importArtifactRevisionToFolderModal.FolderMountForModelStore`),t[57]=c,t[58]=H);let Me=!(E!=null&&E.id),Ne=`group == "${(E==null?void 0:E.id)??``}"`,G;t[59]===Ne?G=t[60]:(G=ge([`ownership_type == "group"`,Ne]),t[59]=Ne,t[60]=G);let K;t[61]!==H||t[62]!==Me||t[63]!==G?(K=(0,W.jsx)(S.Item,{name:`vfolderId`,noStyle:!0,children:(0,W.jsx)(xe,{ref:h,label:H,isLabelHidden:!0,excludeDeleted:!0,isDisabled:Me,filter:G})}),t[61]=H,t[62]=Me,t[63]=G,t[64]=K):K=t[64];let Pe;t[65]===c?Pe=t[66]:(Pe=c(`importArtifactRevisionToFolderModal.FailedToRetrieveModelStoreProject`),t[65]=c,t[66]=Pe);let Fe=!(E!=null&&E.id),Ie;t[67]===Symbol.for(`react.memo_cache_sentinel`)?(Ie=(0,W.jsx)(n,{}),t[67]=Ie):Ie=t[67];let Le=!(E!=null&&E.id),Re;t[68]===v?Re=t[69]:(Re=()=>{v()},t[68]=v,t[69]=Re);let q;t[70]!==Le||t[71]!==Re?(q=(0,W.jsx)(ie,{icon:Ie,"data-testid":`import-artifact-create-folder-button`,disabled:Le,onClick:Re}),t[70]=Le,t[71]=Re,t[72]=q):q=t[72];let J;t[73]!==Pe||t[74]!==Fe||t[75]!==q?(J=(0,W.jsx)(g,{content:Pe,isEnabled:Fe,children:q}),t[73]=Pe,t[74]=Fe,t[75]=q,t[76]=J):J=t[76];let Y;t[77]!==K||t[78]!==J?(Y=(0,W.jsxs)(C,{gap:`xs`,align:`center`,children:[K,J]}),t[77]=K,t[78]=J,t[79]=Y):Y=t[79];let X;t[80]!==V||t[81]!==Y?(X=(0,W.jsx)(S.Item,{label:V,name:`vfolderId`,rules:je,children:Y}),t[80]=V,t[81]=Y,t[82]=X):X=t[82];let Z;t[83]!==P||t[84]!==R||t[85]!==ke||t[86]!==X?(Z=(0,W.jsxs)(P,{direction:`column`,align:`stretch`,children:[R,ke,X]}),t[83]=P,t[84]=R,t[85]=ke,t[86]=X,t[87]=Z):Z=t[87];let Ue;t[88]!==_e||t[89]!==N||t[90]!==Z?(Ue=(0,W.jsx)(_e,{ref:f,layout:`vertical`,preserve:!1,validateTrigger:N,children:Z}),t[88]=_e,t[89]=N,t[90]=Z,t[91]=Ue):Ue=t[91];let $;t[92]!==me||t[93]!==r||t[94]!==O||t[95]!==Ue||t[96]!==k||t[97]!==j||t[98]!==M?($=(0,W.jsx)(me,{title:O,okText:k,centered:!0,...r,okButtonProps:j,onOk:M,children:Ue}),t[92]=me,t[93]=r,t[94]=O,t[95]=Ue,t[96]=k,t[97]=j,t[98]=M,t[99]=$):$=t[99];let Ye;t[100]===E?Ye=t[101]:(Ye=E??{},t[100]=E,t[101]=Ye);let Xe;t[102]===Ye?Xe=t[103]:(Xe=De(Ye),t[102]=Ye,t[103]=Xe);let Ze;t[104]===v?Ze=t[105]:(Ze=e=>{if(v(),e){var t,n;(t=f.current)==null||t.setFieldsValue({vfolderId:pe(`VirtualFolderNode`,e.entityId)}),(n=h.current)==null||n.refetch()}},t[104]=v,t[105]=Ze);let Qe;t[106]!==ee||t[107]!==Xe||t[108]!==Ze?(Qe=(0,W.jsx)(Ae,{open:ee,project:Xe,initialValidate:!0,folderType:`model_project`,onRequestClose:Ze}),t[106]=ee,t[107]=Xe,t[108]=Ze,t[109]=Qe):Qe=t[109];let $e;return t[110]!==$||t[111]!==Qe?($e=(0,W.jsxs)(W.Fragment,{children:[$,Qe]}),t[110]=$,t[111]=Qe,t[112]=$e):$e=t[112],$e};function We(e){return!!(e!=null&&e.id)}function Ge(e){return{label:e.name,value:e.id}}function Ke(e){return e.fieldId}function qe(e){return e.taskId!=null}function Je(e){let t=e.artifactRevision.artifact;return{taskId:e.taskId,version:e.artifactRevision.version,artifact:{id:t.entityId,name:t.name??``}}}
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
H.default.extend(Me.default);var $=()=>{var e,t,n,i,a,o;let{token:c}=_(),{t:l}=re(),d=B(`artifact`),{upsertNotification:h}=y(),{artifactId:g}=ce(),[v,x]=se(le),[S,ie]=(0,Q.useState)([]),[w,E]=(0,Q.useState)([]),[oe,D]=(0,Q.useState)([]),[ue,de]=(0,Q.useState)([]),[pe,O]=Ce({filter:Se(e=>e).withDefault({})},{history:`replace`}),he=JSON.stringify(pe.filter),{baiPaginationOption:A,tablePaginationOption:ge,setTablePaginationOption:M}=ke({current:1,pageSize:10}),_e=(0,Q.useMemo)(()=>({id:g??``,offset:A.offset,limit:A.limit,filter:JSON.parse(he||`{}`)}),[g,A.limit,A.offset,he]),ve=(0,Q.useDeferredValue)(_e),ye=(0,Q.useDeferredValue)(v),{artifact:P,groups:F}=(0,U.useLazyLoadQuery)(Y,ve,{fetchKey:ye===`first`?void 0:ye,fetchPolicy:ye===`first`?`store-and-network`:`network-only`}),L=P==null||(e=P.latestVersion)==null||(e=e.edges[0])==null?void 0:e.node,xe=k(P==null||(t=P.pullingArtifactRevisions)==null?void 0:t.edges.map(e=>e==null?void 0:e.node)),Te={key:`control`,title:l(`general.Control`),fixed:!0,required:!0,render:(e,t)=>{var n;let r=t.status;return(0,W.jsxs)(C,{gap:`xs`,children:[(0,W.jsx)(I,{size:`small`,title:l(`reservoirPage.PullThisVersion`),revisionsFrgmt:[t],loading:r===`PULLING`||r===`VERIFYING`,onClick:()=>{var e;P==null||(e=P.revisions)==null||(e=e.edges)==null||e.forEach(e=>{e.node.id===t.id&&D([e.node])})}}),(0,W.jsx)(Z,{size:`small`,title:l(`importArtifactRevisionToFolderModal.ImportToFolder`),revisionsFrgmt:m(s(P==null||(n=P.revisions)==null?void 0:n.edges,e=>e.node.id===t.id),`node`),onClick:()=>{var e;P==null||(e=P.revisions)==null||(e=e.edges)==null||e.forEach(e=>{e.node.id===t.id&&de([e.node])})}}),(0,W.jsx)(J,{size:`small`,title:l(`reservoirPage.RemoveThisVersion`),revisionsFrgmt:[t],onClick:()=>{var e;P==null||(e=P.revisions)==null||(e=e.edges)==null||e.forEach(e=>{e.node.id===t.id&&E([e.node])})}})]})}};return(0,W.jsxs)(`div`,{children:[(0,W.jsxs)(C,{align:`center`,style:{marginBottom:c(`--spacing-6`)},justify:`between`,children:[(0,W.jsxs)(C,{align:`center`,gap:`xs`,children:[(0,W.jsx)(ee,{level:3,children:P==null?void 0:P.name}),P&&(0,W.jsx)(R,{artifactTypeFrgmt:P})]}),(0,W.jsx)(Oe,{settingId:`reservoir-artifact-detail`,value:v,loading:ye!==v,onChange:()=>{x()}})]}),xe.length>0&&(0,W.jsx)(C,{direction:`column`,gap:`sm`,align:`stretch`,style:{marginBottom:c(`--spacing-5`)},children:xe.map(e=>(0,W.jsx)(Pe,{pullingArtifactRevisionFrgmt:e,onOk:()=>{x()}},e.id))}),(0,W.jsxs)(Ee,{title:l(`reservoirPage.BasicInformation`),showDivider:!0,extra:(0,W.jsx)(b,{variant:`primary`,icon:(0,W.jsx)(r,{size:16}),onClick:()=>{L&&D([L])},isDisabled:!L||L.status!==`SCANNED`,label:L?l(`reservoirPage.PullLatestVersion`,{version:L.version}):`N/A`}),style:{marginBottom:c(`--spacing-5`)},children:[(0,W.jsxs)(ae,{columns:2,children:[(0,W.jsx)(T,{label:l(`reservoirPage.Name`),children:P==null?void 0:P.name}),(0,W.jsx)(T,{label:l(`reservoirPage.Type`),children:P&&(0,W.jsx)(R,{artifactTypeFrgmt:P})}),(0,W.jsx)(T,{label:l(`reservoirPage.Size`),children:(0,W.jsx)(N,{monospace:!0,children:L!=null&&L.size?(n=me(L.size,`auto`))==null?void 0:n.displayValue:`N/A`})}),(0,W.jsx)(T,{label:l(`reservoirPage.Source`),children:P!=null&&P.source?(0,W.jsx)(ne,{href:P.source.url??``,target:`_blank`,children:P.source.name||`N/A`}):`N/A`}),(0,W.jsx)(T,{label:l(`reservoirPage.Registry`),children:(0,W.jsx)(te,{children:P!=null&&P.registry?`${P.registry.name} (${P.registry.url})`:`N/A`})})]}),(0,W.jsxs)(ae,{columns:`single`,children:[(0,W.jsx)(T,{label:l(`reservoirPage.LastUpdated`),children:P!=null&&P.updatedAt?(0,H.default)(P==null?void 0:P.updatedAt).format(`lll`):`N/A`}),(0,W.jsx)(T,{label:l(`reservoirPage.Description`),children:P!=null&&P.description?(0,W.jsx)(te,{as:`p`,display:`block`,children:P.description}):`N/A`}),d&&P&&(0,W.jsx)(T,{label:l(`entityLabel.Labels`),children:(0,W.jsx)(z,{entityType:`artifact`,entityId:P.entityId,name:P.name})})]})]}),(0,W.jsx)(Ee,{title:l(`reservoirPage.VersionList`),showDivider:!0,style:{marginBottom:c(`--spacing-5`)},styles:{body:{padding:`${c(`--spacing-3`)} ${c(`--spacing-6`)} ${c(`--spacing-6`)} ${c(`--spacing-6`)}`}},children:(0,W.jsxs)(C,{direction:`column`,gap:`sm`,align:`stretch`,children:[(0,W.jsxs)(C,{align:`stretch`,justify:`between`,children:[(0,W.jsx)(j,{combinationMode:`AND`,onChange:e=>{O({filter:e??{}})},filterProperties:[{fixedOperator:`equals`,propertyLabel:l(`reservoirPage.Status`),key:`status`,type:`enum`,options:m([`SCANNED`,`PULLING`,`PULLED`,`VERIFYING`,`NEEDS_APPROVAL`,`FAILED`,`AVAILABLE`,`REJECTED`],e=>({label:e,value:e}))},{fixedOperator:`contains`,propertyLabel:l(`reservoirPage.Version`),key:`version`,type:`string`},{propertyLabel:l(`reservoirPage.Size`),key:`size`,type:`number`,operators:[`equals`,`greaterThan`,`greaterOrEqual`,`lessThan`,`lessOrEqual`]}]}),S.length>0?(0,W.jsxs)(C,{gap:`xs`,children:[(0,W.jsxs)(te,{children:[S.length,` selected`]}),(0,W.jsx)(I,{type:`default`,title:l(`reservoirPage.PullSelectedVersions`),revisionsFrgmt:S.flatMap(e=>e.data),onClick:()=>{P&&D(S.flatMap(e=>e.data))}}),(0,W.jsx)(Z,{type:`default`,title:l(`importArtifactRevisionToFolderModal.ImportToFolder`),revisionsFrgmt:S.flatMap(e=>e.data),onClick:()=>{P&&de(u(S,e=>e.data))}}),(0,W.jsx)(J,{title:l(`reservoirPage.RemoveSelectedVersions`),style:{borderColor:c(`--color-border-emphasized`)},revisionsFrgmt:S.flatMap(e=>e.data),onClick:()=>{P&&E(S.flatMap(e=>e.data))}})]}):null]}),(0,W.jsx)(Ne,{artifactRevisionFrgmt:k(P==null||(i=P.revisions)==null||(i=i.edges)==null?void 0:i.map(e=>e.node)),latestRevisionFrgmt:P==null||(a=P.latestVersion)==null||(a=a.edges[0])==null?void 0:a.node,loading:ve!==_e,pagination:{current:ge.current,pageSize:ge.pageSize,total:(P==null||(o=P.revisions)==null?void 0:o.count)??0,onChange:(e,t)=>{f(e)&&f(t)&&M({current:e,pageSize:t})}},onRow:e=>({onClick:t=>{var n;t.stopPropagation();let r=t.target;if(r.closest(`button`)||r.closest(`a`)||!P)return;let i=(n=P.revisions)==null||(n=n.edges.find(t=>t.node.id===e.id))==null?void 0:n.node;i&&ie(t=>{let n=t.filter(t=>t.id!==e.id);return n.length===t.length?[...t,{id:e.id,data:i}]:n})}}),rowSelection:{type:`checkbox`,onChange:e=>{if(!(P!=null&&P.revisions))return;let t=P.revisions,n=t.edges.map(e=>e.node.id);ie(r=>{let i=r.filter(e=>!n.includes(e.id)),a=t.edges.filter(t=>e.includes(t.node.id)).map(e=>({id:e.node.id,data:e.node}));return i.concat(a)})},selectedRowKeys:S.map(e=>e.id)},customizeColumns:e=>[e[0],e[1],Te,...e.slice(2)]})]})}),(0,W.jsx)(be,{selectedArtifactFrgmt:P??null,selectedArtifactRevisionFrgmt:oe,open:!!P&&!p(oe),connectionIds:P!=null&&P.pullingArtifactRevisions?[P.pullingArtifactRevisions.__id]:void 0,onOk:(e,t)=>{D([]),t.forEach(e=>{h({message:l(`reservoirPage.PullingArtifact`,{name:e.artifact.name,version:e.version}),type:`info`,open:!0,duration:0,backgroundTask:{status:`pending`,taskId:e.taskId,promise:null,percent:0,onChange:{resolved:(t,n)=>({type:`success`,message:l(`reservoirPage.SuccessFullyPulledArtifact`,{name:e.artifact.name,version:e.version}),showIcon:!0,toText:l(`reservoirPage.GoToArtifact`),to:we(`admin`,`reservoir/${e.artifact.id}`)}),rejected:(t,n)=>l(`reservoirPage.FailedToPullArtifact`,{name:e.artifact.name,version:e.version})}}})})},onCancel:()=>{D([])}}),(0,W.jsx)(Re,{selectedArtifactFrgmt:P??null,selectedArtifactRevisionFrgmt:w,onOk:()=>{E([])},onCancel:()=>{E([])},open:!!P&&!p(w)}),(0,W.jsx)(Ue,{selectedArtifactRevisionFrgmt:ue,modelStoreProjectsFrgmt:k(F??[]),onOk:(e,t,n)=>{de([]),x(),t.forEach(e=>{h({message:l(`importArtifactRevisionToFolderModal.ImportingArtifact`,{name:e.artifact.name,version:e.version}),type:`info`,open:!0,duration:0,backgroundTask:{status:`pending`,taskId:e.taskId,promise:null,percent:0,onChange:{resolved:(t,r)=>({type:`success`,message:l(`importArtifactRevisionToFolderModal.SuccessfullyImportedArtifact`,{name:e.artifact.name,version:e.version}),showIcon:!0,toText:l(n?`data.folders.OpenAFolder`:`reservoirPage.GoToArtifact`),to:n?{search:new URLSearchParams({folder:fe(n)}).toString()}:`/reservoir/${e.artifact.id}`}),rejected:(t,n)=>l(`importArtifactRevisionToFolderModal.FailedToImportArtifact`,{name:e.artifact.name,version:e.version})}}})})},onCancel:()=>{de([])},open:!!P&&!p(ue)})]})};export{$ as default};
