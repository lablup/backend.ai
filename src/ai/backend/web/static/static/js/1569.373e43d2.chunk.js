"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[1569],{2655:(e,a,n)=>{n.r(a),n.d(a,{default:()=>l});const t=function(){var e=[{alias:null,args:[{kind:"Literal",name:"is_active",value:!0}],concreteType:"Domain",kind:"LinkedField",name:"domains",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:"domains(is_active:true)"}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DomainSelectorQuery",selections:e,type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"DomainSelectorQuery",selections:e},params:{cacheID:"9df762094b74dc3eb8079edfcc73765f",id:null,metadata:{},name:"DomainSelectorQuery",operationKind:"query",text:"query DomainSelectorQuery {\n  domains(is_active: true) {\n    name\n  }\n}\n"}}}();t.hash="c14d362fa40cf9a3cef5d1d71202cc5f";const l=t},8798:(e,a,n)=>{n.r(a),n.d(a,{default:()=>l});const t={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"QuotaScopeCardFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quota_scope_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"storage_host_name",storageKey:null},{alias:null,args:null,concreteType:"QuotaDetails",kind:"LinkedField",name:"details",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"hard_limit_bytes",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"usage_bytes",storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"QuotaSettingModalFragment"}],type:"QuotaScope",abstractKey:null,hash:"78fe420c92ce5b9c8d5c133d1f9c389f"},l=t},1928:(e,a,n)=>{n.r(a),n.d(a,{default:()=>l});const t=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"quota_scope_id"},{defaultValue:null,kind:"LocalArgument",name:"storage_host_name"}],a=[{alias:null,args:[{kind:"Variable",name:"quota_scope_id",variableName:"quota_scope_id"},{kind:"Variable",name:"storage_host_name",variableName:"storage_host_name"}],concreteType:"UnsetQuotaScope",kind:"LinkedField",name:"unset_quota_scope",plural:!1,selections:[{alias:null,args:null,concreteType:"QuotaScope",kind:"LinkedField",name:"quota_scope",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quota_scope_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"storage_host_name",storageKey:null},{alias:null,args:null,concreteType:"QuotaDetails",kind:"LinkedField",name:"details",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"hard_limit_bytes",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"QuotaScopeCardUnsetMutation",selections:a,type:"Mutations",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"QuotaScopeCardUnsetMutation",selections:a},params:{cacheID:"338836966362b14e823520f40fa56a73",id:null,metadata:{},name:"QuotaScopeCardUnsetMutation",operationKind:"mutation",text:"mutation QuotaScopeCardUnsetMutation(\n  $quota_scope_id: String!\n  $storage_host_name: String!\n) {\n  unset_quota_scope(quota_scope_id: $quota_scope_id, storage_host_name: $storage_host_name) {\n    quota_scope {\n      id\n      quota_scope_id\n      storage_host_name\n      details {\n        hard_limit_bytes\n      }\n    }\n  }\n}\n"}}}();t.hash="272001cc642518fb66015dcc367b9f65";const l=t},31737:(e,a,n)=>{n.r(a),n.d(a,{default:()=>l});const t={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"QuotaSettingModalFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quota_scope_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"storage_host_name",storageKey:null},{alias:null,args:null,concreteType:"QuotaDetails",kind:"LinkedField",name:"details",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"hard_limit_bytes",storageKey:null}],storageKey:null}],type:"QuotaScope",abstractKey:null,hash:"1c5ad8315a2d78cb376e7436dc6a8627"},l=t},5432:(e,a,n)=>{n.r(a),n.d(a,{default:()=>l});const t=function(){var e={defaultValue:null,kind:"LocalArgument",name:"props"},a={defaultValue:null,kind:"LocalArgument",name:"quota_scope_id"},n={defaultValue:null,kind:"LocalArgument",name:"storage_host_name"},t=[{alias:null,args:[{kind:"Variable",name:"props",variableName:"props"},{kind:"Variable",name:"quota_scope_id",variableName:"quota_scope_id"},{kind:"Variable",name:"storage_host_name",variableName:"storage_host_name"}],concreteType:"SetQuotaScope",kind:"LinkedField",name:"set_quota_scope",plural:!1,selections:[{alias:null,args:null,concreteType:"QuotaScope",kind:"LinkedField",name:"quota_scope",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quota_scope_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"storage_host_name",storageKey:null},{alias:null,args:null,concreteType:"QuotaDetails",kind:"LinkedField",name:"details",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"hard_limit_bytes",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[e,a,n],kind:"Fragment",metadata:null,name:"QuotaSettingModalSetMutation",selections:t,type:"Mutations",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[a,n,e],kind:"Operation",name:"QuotaSettingModalSetMutation",selections:t},params:{cacheID:"d337cab9be9523bfde2bfb7d6bed595b",id:null,metadata:{},name:"QuotaSettingModalSetMutation",operationKind:"mutation",text:"mutation QuotaSettingModalSetMutation(\n  $quota_scope_id: String!\n  $storage_host_name: String!\n  $props: QuotaScopeInput!\n) {\n  set_quota_scope(quota_scope_id: $quota_scope_id, storage_host_name: $storage_host_name, props: $props) {\n    quota_scope {\n      id\n      quota_scope_id\n      storage_host_name\n      details {\n        hard_limit_bytes\n      }\n    }\n  }\n}\n"}}}();t.hash="0e8509b3174920c1dd917ece91d41161";const l=t},78191:(e,a,n)=>{n.r(a),n.d(a,{default:()=>l});const t={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"StorageHostResourcePanelFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"backend",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capabilities",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"usage",storageKey:null}],type:"StorageVolume",abstractKey:null,hash:"30a1b4101eeb2fae45385780dbc0ddcc"},l=t},6852:(e,a,n)=>{n.r(a),n.d(a,{default:()=>l});const t=function(){var e={defaultValue:null,kind:"LocalArgument",name:"quota_scope_id"},a={defaultValue:null,kind:"LocalArgument",name:"skipQuotaScope"},n={defaultValue:null,kind:"LocalArgument",name:"storage_host_name"},t=[{kind:"Variable",name:"quota_scope_id",variableName:"quota_scope_id"},{kind:"Variable",name:"storage_host_name",variableName:"storage_host_name"}];return{fragment:{argumentDefinitions:[e,a,n],kind:"Fragment",metadata:null,name:"StorageHostSettingsPanelQuery",selections:[{condition:"skipQuotaScope",kind:"Condition",passingValue:!1,selections:[{alias:null,args:t,concreteType:"QuotaScope",kind:"LinkedField",name:"quota_scope",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"QuotaSettingModalFragment"},{args:null,kind:"FragmentSpread",name:"QuotaScopeCardFragment"}],storageKey:null}]}],type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,n,a],kind:"Operation",name:"StorageHostSettingsPanelQuery",selections:[{condition:"skipQuotaScope",kind:"Condition",passingValue:!1,selections:[{alias:null,args:t,concreteType:"QuotaScope",kind:"LinkedField",name:"quota_scope",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quota_scope_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"storage_host_name",storageKey:null},{alias:null,args:null,concreteType:"QuotaDetails",kind:"LinkedField",name:"details",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"hard_limit_bytes",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"usage_bytes",storageKey:null}],storageKey:null}],storageKey:null}]}]},params:{cacheID:"378699d92e64ba9559bfbe8e533d6c6a",id:null,metadata:{},name:"StorageHostSettingsPanelQuery",operationKind:"query",text:"query StorageHostSettingsPanelQuery(\n  $quota_scope_id: String!\n  $storage_host_name: String!\n  $skipQuotaScope: Boolean!\n) {\n  quota_scope(storage_host_name: $storage_host_name, quota_scope_id: $quota_scope_id) @skip(if: $skipQuotaScope) {\n    ...QuotaSettingModalFragment\n    ...QuotaScopeCardFragment\n    id\n  }\n}\n\nfragment QuotaScopeCardFragment on QuotaScope {\n  id\n  quota_scope_id\n  storage_host_name\n  details {\n    hard_limit_bytes\n    usage_bytes\n  }\n  ...QuotaSettingModalFragment\n}\n\nfragment QuotaSettingModalFragment on QuotaScope {\n  id\n  quota_scope_id\n  storage_host_name\n  details {\n    hard_limit_bytes\n  }\n}\n"}}}();t.hash="ef16372a7f5bf0c1844a65d4b63fe4d9";const l=t},27336:(e,a,n)=>{n.r(a),n.d(a,{default:()=>l});const t={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"StorageHostSettingsPanel_storageVolumeFrgmt",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capabilities",storageKey:null}],type:"StorageVolume",abstractKey:null,hash:"2f9e5e6060806e6f9265e5cbbd325afe"},l=t},99618:(e,a,n)=>{n.r(a),n.d(a,{default:()=>l});const t=function(){var e={defaultValue:null,kind:"LocalArgument",name:"filter"},a={defaultValue:null,kind:"LocalArgument",name:"limit"},n={defaultValue:null,kind:"LocalArgument",name:"offset"},t=[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Literal",name:"is_active",value:!0},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"}],concreteType:"UserList",kind:"LinkedField",name:"user_list",plural:!1,selections:[{alias:null,args:null,concreteType:"User",kind:"LinkedField",name:"items",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"is_active",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_policy",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[e,a,n],kind:"Fragment",metadata:null,name:"UserSelectorQuery",selections:t,type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[a,n,e],kind:"Operation",name:"UserSelectorQuery",selections:t},params:{cacheID:"f552e13a727e58f49a7a7e49a466d4d2",id:null,metadata:{},name:"UserSelectorQuery",operationKind:"query",text:"query UserSelectorQuery(\n  $limit: Int!\n  $offset: Int!\n  $filter: String\n) {\n  user_list(limit: $limit, offset: $offset, filter: $filter, is_active: true) {\n    items {\n      id\n      is_active\n      email\n      resource_policy\n    }\n  }\n}\n"}}}();t.hash="323d93fb2d8eb4ee2d1d3677121f9ad2";const l=t},81569:(e,a,n)=>{n.r(a),n.d(a,{default:()=>X});var t,l=n(89130),i=n(58879),o=n(45679),s=n(64687),r=n(85690),u=n(15934),d=n(89608),c=n.n(d),g=n(56762),m=n(88522),p=n(73689);const _=e=>{let{storageVolumeFrgmt:a}=e;const{t:l}=(0,g.Bd)(),d=(0,m.useFragment)(void 0!==t?t:t=n(78191),a),_=JSON.parse((null===d||void 0===d?void 0:d.usage)||"{}"),y=null===_||void 0===_?void 0:_.used_bytes,S=null===_||void 0===_?void 0:_.capacity_bytes,k={used_bytes:y,capacity_bytes:S,percent:Number((100*(S>0?y/S:0)).toFixed(1))};return(0,p.jsxs)(o.A,{size:"small",bordered:!0,column:3,children:[(0,p.jsxs)(o.A.Item,{label:l("storageHost.Usage"),span:3,children:[(null===k||void 0===k?void 0:k.percent)<100?(0,p.jsx)(s.A,{size:[200,15],percent:null===k||void 0===k?void 0:k.percent,strokeColor:(0,i.yc)(null===k||void 0===k?void 0:k.percent)}):(0,p.jsx)(s.A,{size:[200,15],percent:null===k||void 0===k?void 0:k.percent,status:"exception"}),(0,p.jsxs)(r.A.Text,{type:"secondary",children:[l("storageHost.Used"),":"," "]}),(0,i.sB)(null===k||void 0===k?void 0:k.used_bytes),(0,p.jsx)(r.A.Text,{type:"secondary",children:" / "}),(0,p.jsxs)(r.A.Text,{type:"secondary",children:[l("storageHost.Total"),":"," "]}),(0,i.sB)(null===k||void 0===k?void 0:k.capacity_bytes)]}),(0,p.jsx)(o.A.Item,{label:l("agent.Endpoint"),children:null===d||void 0===d?void 0:d.path}),(0,p.jsx)(o.A.Item,{label:l("agent.BackendType"),children:null===d||void 0===d?void 0:d.backend}),(0,p.jsx)(o.A.Item,{label:l("agent.Capabilities"),children:c().map(null===d||void 0===d?void 0:d.capabilities,(e=>(0,p.jsx)(u.A,{children:e},e)))})]})};var y,S=n(51593),k=n(69056),h=n(43373);const v=e=>{let{onSelectDomain:a,...t}=e;const{t:l}=(0,g.Bd)(),{domains:i}=(0,m.useLazyLoadQuery)(void 0!==y?y:y=n(2655),{},{fetchPolicy:"store-and-network"});return(0,p.jsxs)(k.A,{onChange:(e,n)=>{null===a||void 0===a||a(n)},placeholder:l("storageHost.quotaSettings.SelectDomain"),...t,children:[c().map(i,(e=>(0,p.jsx)(k.A.Option,{domainName:null===e||void 0===e?void 0:e.name,children:null===e||void 0===e?void 0:e.name},null===e||void 0===e?void 0:e.name))),";"]})};var b=n(83348);const f=e=>{let{...a}=e;return(0,p.jsx)(b.A,{...a,disableDefaultFilter:!0})};var F,q,A=n(4342),x=n(88629),K=n(67425),Q=n(50868),j=n(93008),L=n(60822),D=n(77731),H=n(51548),V=n(85029);const C=e=>{let{quotaScopeFrgmt:a,showAddButtonWhenEmpty:t,onClickEdit:o,...s}=e;const{t:r}=(0,g.Bd)(),{token:u}=Q.A.useToken(),d=(0,m.useFragment)(void 0!==F?F:F=n(8798),a),[c,_]=(0,m.useMutation)(void 0!==q?q:q=n(1928)),y=(0,p.jsx)(j.A,{style:{width:"100%"},image:j.A.PRESENTED_IMAGE_SIMPLE,description:(0,p.jsx)("div",{children:r("storageHost.quotaSettings.SelectFirst")})}),S=(0,p.jsx)(j.A,{style:{width:"100%"},image:j.A.PRESENTED_IMAGE_SIMPLE,description:(0,p.jsxs)(p.Fragment,{children:[(0,p.jsx)("div",{style:{margin:10},children:r("storageHost.quotaSettings.ClickSettingButton")}),(0,p.jsx)(L.Ay,{icon:(0,p.jsx)(A.A,{}),onClick:()=>o&&o(),children:r("storageHost.quotaSettings.AddQuotaConfigs")})]})});return(0,p.jsx)(D.A,{bordered:!0,rowKey:"id",columns:[{title:r("storageHost.quotaSettings.QuotaScopeId"),dataIndex:"quota_scope_id",key:"quota_scope_id",render:e=>(0,p.jsx)("code",{children:e})},{title:r("storageHost.HardLimit")+" (GB)",dataIndex:["details","hard_limit_bytes"],key:"hard_limit_bytes",render:e=>(0,p.jsx)(p.Fragment,{children:(0,i.wb)(e)})},{title:r("storageHost.Usage")+" (GB)",dataIndex:["details","usage_bytes"],key:"usage_bytes",render:e=>(0,p.jsx)(p.Fragment,{children:(0,i.wb)(e)})},{title:r("general.Control"),key:"control",render:()=>(0,p.jsxs)(l.A,{gap:u.marginSM,children:[(0,p.jsx)(L.Ay,{icon:(0,p.jsx)(x.A,{}),onClick:()=>o&&o(),children:r("button.Edit")}),(0,p.jsx)(H.A,{title:r("storageHost.quotaSettings.UnsetCustomSettings"),description:r("storageHost.quotaSettings.ConfirmUnsetCustomQuota"),placement:"bottom",onConfirm:()=>{d&&c({variables:{quota_scope_id:d.quota_scope_id,storage_host_name:d.storage_host_name},onCompleted(){V.Ay.success(r("storageHost.quotaSettings.QuotaScopeSuccessfullyUpdated"))},onError(e){V.Ay.error(null===e||void 0===e?void 0:e.message)}})},children:(0,p.jsx)(L.Ay,{loading:_,danger:!0,icon:(0,p.jsx)(K.A,{}),children:r("button.Unset")})})]})}],dataSource:d?[d]:[],locale:{emptyText:t?S:y},pagination:!1})};var T,w,M=n(94126),I=n(23702),P=n(67378);const $=e=>{var a;let{quotaScopeFrgmt:t=null,onRequestClose:l,...o}=e;const{t:s}=(0,g.Bd)(),r=(0,h.useRef)(null),u=(0,m.useFragment)(void 0!==T?T:T=n(31737),t),[d,c]=(0,m.useMutation)(void 0!==w?w:w=n(5432));return(0,p.jsx)(M.A,{...o,destroyOnClose:!0,onOk:e=>{var a;null===(a=r.current)||void 0===a||a.validateFields().then((e=>{d({variables:{quota_scope_id:(null===u||void 0===u?void 0:u.quota_scope_id)||"",storage_host_name:(null===u||void 0===u?void 0:u.storage_host_name)||"",props:{hard_limit_bytes:(0,i._S)(null===e||void 0===e?void 0:e.hard_limit_bytes)}},onCompleted(e){var a,n;null!==e&&void 0!==e&&null!==(a=e.set_quota_scope)&&void 0!==a&&null!==(n=a.quota_scope)&&void 0!==n&&n.id?V.Ay.success(s("storageHost.quotaSettings.QuotaScopeSuccessfullyUpdated")):V.Ay.error(s("dialog.ErrorOccurred")),l()},onError(e){console.log(e),V.Ay.error(null===e||void 0===e?void 0:e.message)}})}))},confirmLoading:c,onCancel:l,title:s("storageHost.quotaSettings.QuotaSettings"),children:(0,p.jsx)(I.A,{ref:r,preserve:!1,labelCol:{span:6},wrapperCol:{span:20},validateTrigger:["onChange","onBlur"],style:{marginBottom:40,marginTop:20},children:(0,p.jsx)(I.A.Item,{name:"hard_limit_bytes",label:s("storageHost.HardLimit"),initialValue:(0,i.wb)(null===u||void 0===u||null===(a=u.details)||void 0===a?void 0:a.hard_limit_bytes),rules:[{pattern:/^\d+(\.\d+)?$/,message:s("storageHost.quotaSettings.AllowNumberAndDot")||"Allows numbers and .(dot) only"}],children:(0,p.jsx)(P.A,{addonAfter:"GB",type:"number",step:.25,style:{width:"70%"}})})})})};var E;const U=e=>{let{onSelectUser:a,...t}=e;const{t:l}=(0,g.Bd)(),[i,o]=(0,h.useState)(""),s=(0,h.useDeferredValue)(i),{user_list:r}=(0,m.useLazyLoadQuery)(void 0!==E?E:E=n(99618),{limit:150,offset:0,filter:0===(null===s||void 0===s?void 0:s.length)?null:'email ilike "%'+s+'%"'},{fetchPolicy:"store-and-network"});return(0,p.jsx)(k.A,{filterOption:!1,searchValue:i,loading:s!==i,onSearch:e=>{o(e)},onChange:e=>{a(c().find(null===r||void 0===r?void 0:r.items,(a=>(null===a||void 0===a?void 0:a.email)===e)))},showSearch:!0,placeholder:l("storageHost.quotaSettings.SelectUser"),options:c().map(null===r||void 0===r?void 0:r.items,(e=>({value:null===e||void 0===e?void 0:e.email,label:null===e||void 0===e?void 0:e.email}))).sort(((e,a)=>e.value&&a.value&&e.value>a.value?1:-1)),...t})};var B,N,R=n(55731),O=n(55368),z=n(11371);const G=e=>{let{storageVolumeFrgmt:a}=e;const{t:t}=(0,g.Bd)(),o=(0,m.useFragment)(void 0!==B?B:B=n(27336),a),[s,r]=(0,h.useTransition)(),u=(0,S.eZ)(),[d,c]=(0,h.useState)("user"),[_,y]=(0,h.useState)(u),[k,b]=(0,h.useState)();(0,h.useState)();const[F,q]=(0,h.useState)(),[A,x]=(0,h.useState)();(0,h.useState)();const K=(0,i.sZ)(d,("project"===d?k:F)||""),[Q,{toggle:j}]=(0,R.A)(!1),[L]=(0,S.Tw)("default"),{quota_scope:D}=(0,m.useLazyLoadQuery)(void 0!==N?N:N=n(6852),{quota_scope_id:K,skipQuotaScope:void 0===K||""===K,storage_host_name:(null===o||void 0===o?void 0:o.id)||""},{fetchPolicy:"network-only",fetchKey:L});return(0,p.jsx)(l.A,{direction:"column",align:"stretch",children:(0,p.jsxs)(O.A,{title:t("storageHost.QuotaSettings"),tabList:[{key:"user",tab:t("storageHost.ForUser")},{key:"project",tab:t("storageHost.ForProject")}],activeTabKey:d,onTabChange:e=>{r((()=>{c(e)}))},children:[(0,p.jsx)(l.A,{justify:"between",children:"project"===d?(0,p.jsx)(l.A,{style:{marginBottom:10},children:(0,p.jsxs)(I.A,{layout:"inline",children:[(0,p.jsx)(I.A.Item,{label:t("resourceGroup.Domain"),children:(0,p.jsx)(v,{style:{width:"20vw",marginRight:10},value:_,onSelectDomain:e=>{r((()=>{y(null===e||void 0===e?void 0:e.domainName),b(void 0)}))}})}),(0,p.jsx)(I.A.Item,{label:t("webui.menu.Project"),children:(0,p.jsx)(f,{style:{width:"20vw"},value:k,disabled:!_,domain:_||"",onSelectProject:e=>{r((()=>{b(null===e||void 0===e?void 0:e.projectId)}))}})})]})}):(0,p.jsx)(I.A,{layout:"inline",children:(0,p.jsx)(I.A.Item,{label:t("data.User"),children:(0,p.jsx)(U,{style:{width:"30vw",marginBottom:10},value:A,onSelectUser:e=>{x(null===e||void 0===e?void 0:e.email),r((()=>{q(null===e||void 0===e?void 0:e.id)}))}})})})}),(0,p.jsx)(z.A,{spinning:s,children:(0,p.jsx)(C,{quotaScopeFrgmt:D||null,onClickEdit:()=>{j()},showAddButtonWhenEmpty:"project"===d&&!!k||"user"===d&&!!F})}),(0,p.jsx)($,{open:Q,quotaScopeFrgmt:D||null,onRequestClose:()=>{j()}})]})})};var W,Z=n(40042),J=n(18150);const X=()=>{var e,a;const{hostname:t}=(0,J.g)(),i=(0,S.CX)(),o=(0,S.f0)(),{t:s}=(0,g.Bd)(),{storage_volume:u}=(0,m.useLazyLoadQuery)(void 0!==W?W:W=n(20136),{id:t||""}),d=null!==(e=null===u||void 0===u||null===(a=u.capabilities)||void 0===a?void 0:a.includes("quota"))&&void 0!==e&&e;return(0,p.jsxs)(l.A,{direction:"column",align:"stretch",gap:"sm",children:[(0,p.jsx)(Z.A,{items:[{title:s("webui.menu.Resources"),onClick:e=>{e.preventDefault(),o("/agent")},href:"/agent"},{title:s("storageHost.StorageSetting")}]}),(0,p.jsx)(r.A.Title,{level:3,style:{margin:0},children:t||""}),(0,p.jsx)(_,{storageVolumeFrgmt:u||null}),i.supports("quota-scope")&&(0,p.jsx)(p.Fragment,{children:d?(0,p.jsx)(h.Suspense,{fallback:(0,p.jsx)("div",{children:"loading..."}),children:(0,p.jsx)(G,{storageVolumeFrgmt:u||null})}):(0,p.jsx)(O.A,{title:s("storageHost.QuotaSettings"),children:(0,p.jsx)(j.A,{image:j.A.PRESENTED_IMAGE_SIMPLE,description:s("storageHost.QuotaDoesNotSupported")})})})]})}},20136:(e,a,n)=>{n.r(a),n.d(a,{default:()=>l});const t=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"id"}],a=[{kind:"Variable",name:"id",variableName:"id"}],n={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"capabilities",storageKey:null};return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"StorageHostSettingPageQuery",selections:[{alias:null,args:a,concreteType:"StorageVolume",kind:"LinkedField",name:"storage_volume",plural:!1,selections:[n,t,{args:null,kind:"FragmentSpread",name:"StorageHostResourcePanelFragment"},{args:null,kind:"FragmentSpread",name:"StorageHostSettingsPanel_storageVolumeFrgmt"}],storageKey:null}],type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"StorageHostSettingPageQuery",selections:[{alias:null,args:a,concreteType:"StorageVolume",kind:"LinkedField",name:"storage_volume",plural:!1,selections:[n,t,{alias:null,args:null,kind:"ScalarField",name:"backend",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"usage",storageKey:null}],storageKey:null}]},params:{cacheID:"821175f86743d9d81be2a55aca371919",id:null,metadata:{},name:"StorageHostSettingPageQuery",operationKind:"query",text:"query StorageHostSettingPageQuery(\n  $id: String\n) {\n  storage_volume(id: $id) {\n    id\n    capabilities\n    ...StorageHostResourcePanelFragment\n    ...StorageHostSettingsPanel_storageVolumeFrgmt\n  }\n}\n\nfragment StorageHostResourcePanelFragment on StorageVolume {\n  id\n  backend\n  capabilities\n  path\n  usage\n}\n\nfragment StorageHostSettingsPanel_storageVolumeFrgmt on StorageVolume {\n  id\n  capabilities\n}\n"}}}();t.hash="f6e77057e83b0449ef99e8918e794b24";const l=t}}]);
//# sourceMappingURL=1569.373e43d2.chunk.js.map