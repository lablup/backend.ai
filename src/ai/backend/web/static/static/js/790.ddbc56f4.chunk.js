"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[790],{33614:function(e,a,n){n.r(a);var t=function(){var e=[{alias:null,args:[{kind:"Literal",name:"is_active",value:!0}],concreteType:"Domain",kind:"LinkedField",name:"domains",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:"domains(is_active:true)"}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DomainSelectorQuery",selections:e,type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"DomainSelectorQuery",selections:e},params:{cacheID:"9df762094b74dc3eb8079edfcc73765f",id:null,metadata:{},name:"DomainSelectorQuery",operationKind:"query",text:"query DomainSelectorQuery {\n  domains(is_active: true) {\n    name\n  }\n}\n"}}}();t.hash="c14d362fa40cf9a3cef5d1d71202cc5f",a.default=t},81674:function(e,a,n){n.r(a);var t={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"QuotaScopeCardFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quota_scope_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"storage_host_name",storageKey:null},{alias:null,args:null,concreteType:"QuotaDetails",kind:"LinkedField",name:"details",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"hard_limit_bytes",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"usage_bytes",storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"QuotaSettingModalFragment"}],type:"QuotaScope",abstractKey:null,hash:"78fe420c92ce5b9c8d5c133d1f9c389f"};a.default=t},96685:function(e,a,n){n.r(a);var t=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"quota_scope_id"},{defaultValue:null,kind:"LocalArgument",name:"storage_host_name"}],a=[{alias:null,args:[{kind:"Variable",name:"quota_scope_id",variableName:"quota_scope_id"},{kind:"Variable",name:"storage_host_name",variableName:"storage_host_name"}],concreteType:"UnsetQuotaScope",kind:"LinkedField",name:"unset_quota_scope",plural:!1,selections:[{alias:null,args:null,concreteType:"QuotaScope",kind:"LinkedField",name:"quota_scope",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quota_scope_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"storage_host_name",storageKey:null},{alias:null,args:null,concreteType:"QuotaDetails",kind:"LinkedField",name:"details",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"hard_limit_bytes",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"QuotaScopeCardUnsetMutation",selections:a,type:"Mutations",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"QuotaScopeCardUnsetMutation",selections:a},params:{cacheID:"338836966362b14e823520f40fa56a73",id:null,metadata:{},name:"QuotaScopeCardUnsetMutation",operationKind:"mutation",text:"mutation QuotaScopeCardUnsetMutation(\n  $quota_scope_id: String!\n  $storage_host_name: String!\n) {\n  unset_quota_scope(quota_scope_id: $quota_scope_id, storage_host_name: $storage_host_name) {\n    quota_scope {\n      id\n      quota_scope_id\n      storage_host_name\n      details {\n        hard_limit_bytes\n      }\n    }\n  }\n}\n"}}}();t.hash="272001cc642518fb66015dcc367b9f65",a.default=t},64133:function(e,a,n){n.r(a);var t={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"QuotaSettingModalFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quota_scope_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"storage_host_name",storageKey:null},{alias:null,args:null,concreteType:"QuotaDetails",kind:"LinkedField",name:"details",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"hard_limit_bytes",storageKey:null}],storageKey:null}],type:"QuotaScope",abstractKey:null,hash:"1c5ad8315a2d78cb376e7436dc6a8627"};a.default=t},95005:function(e,a,n){n.r(a);var t=function(){var e={defaultValue:null,kind:"LocalArgument",name:"props"},a={defaultValue:null,kind:"LocalArgument",name:"quota_scope_id"},n={defaultValue:null,kind:"LocalArgument",name:"storage_host_name"},t=[{alias:null,args:[{kind:"Variable",name:"props",variableName:"props"},{kind:"Variable",name:"quota_scope_id",variableName:"quota_scope_id"},{kind:"Variable",name:"storage_host_name",variableName:"storage_host_name"}],concreteType:"SetQuotaScope",kind:"LinkedField",name:"set_quota_scope",plural:!1,selections:[{alias:null,args:null,concreteType:"QuotaScope",kind:"LinkedField",name:"quota_scope",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quota_scope_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"storage_host_name",storageKey:null},{alias:null,args:null,concreteType:"QuotaDetails",kind:"LinkedField",name:"details",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"hard_limit_bytes",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[e,a,n],kind:"Fragment",metadata:null,name:"QuotaSettingModalSetMutation",selections:t,type:"Mutations",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[a,n,e],kind:"Operation",name:"QuotaSettingModalSetMutation",selections:t},params:{cacheID:"d337cab9be9523bfde2bfb7d6bed595b",id:null,metadata:{},name:"QuotaSettingModalSetMutation",operationKind:"mutation",text:"mutation QuotaSettingModalSetMutation(\n  $quota_scope_id: String!\n  $storage_host_name: String!\n  $props: QuotaScopeInput!\n) {\n  set_quota_scope(quota_scope_id: $quota_scope_id, storage_host_name: $storage_host_name, props: $props) {\n    quota_scope {\n      id\n      quota_scope_id\n      storage_host_name\n      details {\n        hard_limit_bytes\n      }\n    }\n  }\n}\n"}}}();t.hash="0e8509b3174920c1dd917ece91d41161",a.default=t},58156:function(e,a,n){n.r(a);var t={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"StorageHostResourcePanelFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"backend",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capabilities",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"usage",storageKey:null}],type:"StorageVolume",abstractKey:null,hash:"30a1b4101eeb2fae45385780dbc0ddcc"};a.default=t},81047:function(e,a,n){n.r(a);var t=function(){var e={defaultValue:null,kind:"LocalArgument",name:"quota_scope_id"},a={defaultValue:null,kind:"LocalArgument",name:"skipQuotaScope"},n={defaultValue:null,kind:"LocalArgument",name:"storage_host_name"},t=[{kind:"Variable",name:"quota_scope_id",variableName:"quota_scope_id"},{kind:"Variable",name:"storage_host_name",variableName:"storage_host_name"}];return{fragment:{argumentDefinitions:[e,a,n],kind:"Fragment",metadata:null,name:"StorageHostSettingsPanelQuery",selections:[{condition:"skipQuotaScope",kind:"Condition",passingValue:!1,selections:[{alias:null,args:t,concreteType:"QuotaScope",kind:"LinkedField",name:"quota_scope",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"QuotaSettingModalFragment"},{args:null,kind:"FragmentSpread",name:"QuotaScopeCardFragment"}],storageKey:null}]}],type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,n,a],kind:"Operation",name:"StorageHostSettingsPanelQuery",selections:[{condition:"skipQuotaScope",kind:"Condition",passingValue:!1,selections:[{alias:null,args:t,concreteType:"QuotaScope",kind:"LinkedField",name:"quota_scope",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quota_scope_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"storage_host_name",storageKey:null},{alias:null,args:null,concreteType:"QuotaDetails",kind:"LinkedField",name:"details",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"hard_limit_bytes",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"usage_bytes",storageKey:null}],storageKey:null}],storageKey:null}]}]},params:{cacheID:"378699d92e64ba9559bfbe8e533d6c6a",id:null,metadata:{},name:"StorageHostSettingsPanelQuery",operationKind:"query",text:"query StorageHostSettingsPanelQuery(\n  $quota_scope_id: String!\n  $storage_host_name: String!\n  $skipQuotaScope: Boolean!\n) {\n  quota_scope(storage_host_name: $storage_host_name, quota_scope_id: $quota_scope_id) @skip(if: $skipQuotaScope) {\n    ...QuotaSettingModalFragment\n    ...QuotaScopeCardFragment\n    id\n  }\n}\n\nfragment QuotaScopeCardFragment on QuotaScope {\n  id\n  quota_scope_id\n  storage_host_name\n  details {\n    hard_limit_bytes\n    usage_bytes\n  }\n  ...QuotaSettingModalFragment\n}\n\nfragment QuotaSettingModalFragment on QuotaScope {\n  id\n  quota_scope_id\n  storage_host_name\n  details {\n    hard_limit_bytes\n  }\n}\n"}}}();t.hash="ef16372a7f5bf0c1844a65d4b63fe4d9",a.default=t},16678:function(e,a,n){n.r(a);var t={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"StorageHostSettingsPanel_storageVolumeFrgmt",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capabilities",storageKey:null}],type:"StorageVolume",abstractKey:null,hash:"2f9e5e6060806e6f9265e5cbbd325afe"};a.default=t},54880:function(e,a,n){n.r(a);var t=function(){var e={defaultValue:null,kind:"LocalArgument",name:"filter"},a={defaultValue:null,kind:"LocalArgument",name:"limit"},n={defaultValue:null,kind:"LocalArgument",name:"offset"},t=[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Literal",name:"is_active",value:!0},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"}],concreteType:"UserList",kind:"LinkedField",name:"user_list",plural:!1,selections:[{alias:null,args:null,concreteType:"User",kind:"LinkedField",name:"items",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"is_active",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_policy",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[e,a,n],kind:"Fragment",metadata:null,name:"UserSelectorQuery",selections:t,type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[a,n,e],kind:"Operation",name:"UserSelectorQuery",selections:t},params:{cacheID:"f552e13a727e58f49a7a7e49a466d4d2",id:null,metadata:{},name:"UserSelectorQuery",operationKind:"query",text:"query UserSelectorQuery(\n  $limit: Int!\n  $offset: Int!\n  $filter: String\n) {\n  user_list(limit: $limit, offset: $offset, filter: $filter, is_active: true) {\n    items {\n      id\n      is_active\n      email\n      resource_policy\n    }\n  }\n}\n"}}}();t.hash="323d93fb2d8eb4ee2d1d3677121f9ad2",a.default=t},53790:function(e,a,n){n.r(a),n.d(a,{default:function(){return re}});var t,l,i=n(99277),o=n(43255),s=n(93448),r=n(53562),u=n(70389),d=n(82548),c=n(32048),g=n.n(c),m=n(81748),p=n(16980),_=n(2556),y=function(e){var a=e.storageVolumeFrgmt,l=(0,m.$G)().t,i=(0,p.useFragment)(void 0!==t?t:t=n(58156),a),c=JSON.parse((null===i||void 0===i?void 0:i.usage)||"{}"),y=null===c||void 0===c?void 0:c.used_bytes,S=null===c||void 0===c?void 0:c.capacity_bytes,f={used_bytes:y,capacity_bytes:S,percent:Number((100*(S>0?y/S:0)).toFixed(1))};return(0,_.jsxs)(s.Z,{size:"small",bordered:!0,column:3,children:[(0,_.jsxs)(s.Z.Item,{label:l("storageHost.Usage"),span:3,children:[(null===f||void 0===f?void 0:f.percent)<100?(0,_.jsx)(r.Z,{size:[200,15],percent:null===f||void 0===f?void 0:f.percent,strokeColor:(0,o.lA)(null===f||void 0===f?void 0:f.percent)}):(0,_.jsx)(r.Z,{size:[200,15],percent:null===f||void 0===f?void 0:f.percent,status:"exception"}),(0,_.jsxs)(u.Z.Text,{type:"secondary",children:[l("storageHost.Used"),":"," "]}),(0,o.XG)(null===f||void 0===f?void 0:f.used_bytes),(0,_.jsx)(u.Z.Text,{type:"secondary",children:" / "}),(0,_.jsxs)(u.Z.Text,{type:"secondary",children:[l("storageHost.Total"),":"," "]}),(0,o.XG)(null===f||void 0===f?void 0:f.capacity_bytes)]}),(0,_.jsx)(s.Z.Item,{label:l("agent.Endpoint"),children:null===i||void 0===i?void 0:i.path}),(0,_.jsx)(s.Z.Item,{label:l("agent.BackendType"),children:null===i||void 0===i?void 0:i.backend}),(0,_.jsx)(s.Z.Item,{label:l("agent.Capabilities"),children:g().map(null===i||void 0===i?void 0:i.capabilities,(function(e){return(0,_.jsx)(d.Z,{children:e},e)}))})]})},S=n(29439),f=n(40406),v=n(1413),k=n(44925),h=n(72887),b=n(4519),F=["onSelectDomain"],q=function(e){var a=e.onSelectDomain,t=(0,k.Z)(e,F),i=(0,m.$G)().t,o=(0,p.useLazyLoadQuery)(void 0!==l?l:l=n(33614),{},{fetchPolicy:"store-and-network"}).domains;return(0,_.jsxs)(h.Z,(0,v.Z)((0,v.Z)({onChange:function(e,n){null===a||void 0===a||a(n)},placeholder:i("storageHost.quotaSettings.SelectDomain")},t),{},{children:[g().map(o,(function(e){return(0,_.jsx)(h.Z.Option,{domainName:null===e||void 0===e?void 0:e.name,children:null===e||void 0===e?void 0:e.name},null===e||void 0===e?void 0:e.name)})),";"]}))},x=n(13522),Z=n(20558),K=n(87462),Q={icon:{tag:"svg",attrs:{viewBox:"64 64 896 896",focusable:"false"},children:[{tag:"path",attrs:{d:"M880 836H144c-17.7 0-32 14.3-32 32v36c0 4.4 3.6 8 8 8h784c4.4 0 8-3.6 8-8v-36c0-17.7-14.3-32-32-32zm-622.3-84c2 0 4-.2 6-.5L431.9 722c2-.4 3.9-1.3 5.3-2.8l423.9-423.9a9.96 9.96 0 000-14.1L694.9 114.9c-1.9-1.9-4.4-2.9-7.1-2.9s-5.2 1-7.1 2.9L256.8 538.8c-1.5 1.5-2.4 3.3-2.8 5.3l-29.5 168.2a33.5 33.5 0 009.4 29.8c6.6 6.4 14.9 9.9 23.8 9.9z"}}]},name:"edit",theme:"filled"},j=n(9491),L=function(e,a){return b.createElement(j.Z,(0,K.Z)({},e,{ref:a,icon:Q}))};var D,H,V,C,P,T,$,M,w=b.forwardRef(L),U=n(31662),I=n(44036),E=n(54473),A=n(38812),N=n(3597),R=n(41366),G=n(88464),B=["quotaScopeFrgmt","showAddButtonWhenEmpty","onClickEdit"],z=function(e){var a=e.quotaScopeFrgmt,t=e.showAddButtonWhenEmpty,l=e.onClickEdit,s=((0,k.Z)(e,B),(0,m.$G)().t),r=I.Z.useToken().token,u=(0,p.useFragment)(void 0!==D?D:D=n(81674),a),d=(0,p.useMutation)(void 0!==H?H:H=n(96685)),c=(0,S.Z)(d,2),g=c[0],y=c[1],f=(0,_.jsx)(E.Z,{style:{width:"100%"},image:E.Z.PRESENTED_IMAGE_SIMPLE,description:(0,_.jsx)("div",{children:s("storageHost.quotaSettings.SelectFirst")})}),v=(0,_.jsx)(E.Z,{style:{width:"100%"},image:E.Z.PRESENTED_IMAGE_SIMPLE,description:(0,_.jsxs)(_.Fragment,{children:[(0,_.jsx)("div",{style:{margin:10},children:s("storageHost.quotaSettings.ClickSettingButton")}),(0,_.jsx)(A.ZP,{icon:(0,_.jsx)(Z.Z,{}),onClick:function(){return l&&l()},children:s("storageHost.quotaSettings.AddQuotaConfigs")})]})});return(0,_.jsx)(N.Z,{bordered:!0,rowKey:"id",columns:[{title:s("storageHost.quotaSettings.QuotaScopeId"),dataIndex:"quota_scope_id",key:"quota_scope_id",render:function(e){return(0,_.jsx)("code",{children:e})}},{title:s("storageHost.HardLimit")+" (GB)",dataIndex:["details","hard_limit_bytes"],key:"hard_limit_bytes",render:function(e){return(0,_.jsx)(_.Fragment,{children:(0,o.Uz)(e)})}},{title:s("storageHost.Usage")+" (GB)",dataIndex:["details","usage_bytes"],key:"usage_bytes",render:function(e){return(0,_.jsx)(_.Fragment,{children:(0,o.Uz)(e)})}},{title:s("general.Control"),key:"control",render:function(){return(0,_.jsxs)(i.Z,{gap:r.marginSM,children:[(0,_.jsx)(A.ZP,{icon:(0,_.jsx)(w,{}),onClick:function(){return l&&l()},children:s("button.Edit")}),(0,_.jsx)(R.Z,{title:s("storageHost.quotaSettings.UnsetCustomSettings"),description:s("storageHost.quotaSettings.ConfirmUnsetCustomQuota"),placement:"bottom",onConfirm:function(){u&&g({variables:{quota_scope_id:u.quota_scope_id,storage_host_name:u.storage_host_name},onCompleted:function(){G.ZP.success(s("storageHost.quotaSettings.QuotaScopeSuccessfullyUpdated"))},onError:function(e){G.ZP.error(null===e||void 0===e?void 0:e.message)}})},children:(0,_.jsx)(A.ZP,{loading:y,danger:!0,icon:(0,_.jsx)(U.Z,{}),children:s("button.Unset")})})]})}}],dataSource:u?[u]:[],locale:{emptyText:t?v:f},pagination:!1})},O=n(77758),W=n(57054),X=n(38818),J=["quotaScopeFrgmt","onRequestClose"],Y=function(e){var a,t=e.quotaScopeFrgmt,l=void 0===t?null:t,i=e.onRequestClose,s=(0,k.Z)(e,J),r=(0,m.$G)().t,u=(0,b.useRef)(null),d=(0,p.useFragment)(void 0!==V?V:V=n(64133),l),c=(0,p.useMutation)(void 0!==C?C:C=n(95005)),g=(0,S.Z)(c,2),y=g[0],f=g[1];return(0,_.jsx)(O.Z,(0,v.Z)((0,v.Z)({},s),{},{destroyOnClose:!0,onOk:function(e){var a;null===(a=u.current)||void 0===a||a.validateFields().then((function(e){y({variables:{quota_scope_id:(null===d||void 0===d?void 0:d.quota_scope_id)||"",storage_host_name:(null===d||void 0===d?void 0:d.storage_host_name)||"",props:{hard_limit_bytes:(0,o.Hz)(null===e||void 0===e?void 0:e.hard_limit_bytes)}},onCompleted:function(e){var a,n;null!==e&&void 0!==e&&null!==(a=e.set_quota_scope)&&void 0!==a&&null!==(n=a.quota_scope)&&void 0!==n&&n.id?G.ZP.success(r("storageHost.quotaSettings.QuotaScopeSuccessfullyUpdated")):G.ZP.error(r("dialog.ErrorOccurred")),i()},onError:function(e){console.log(e),G.ZP.error(null===e||void 0===e?void 0:e.message)}})}))},confirmLoading:f,onCancel:i,title:r("storageHost.quotaSettings.QuotaSettings"),children:(0,_.jsx)(W.Z,{ref:u,preserve:!1,labelCol:{span:6},wrapperCol:{span:20},validateTrigger:["onChange","onBlur"],style:{marginBottom:40,marginTop:20},children:(0,_.jsx)(W.Z.Item,{name:"hard_limit_bytes",label:r("storageHost.HardLimit"),initialValue:(0,o.Uz)(null===d||void 0===d||null===(a=d.details)||void 0===a?void 0:a.hard_limit_bytes),rules:[{pattern:/^\d+(\.\d+)?$/,message:r("storageHost.quotaSettings.AllowNumberAndDot")||"Allows numbers and .(dot) only"}],children:(0,_.jsx)(X.Z,{addonAfter:"GB",type:"number",step:.25,style:{width:"70%"}})})})}))},ee=["onSelectUser"],ae=function(e){var a=e.onSelectUser,t=(0,k.Z)(e,ee),l=(0,m.$G)().t,i=(0,b.useState)(""),o=(0,S.Z)(i,2),s=o[0],r=o[1],u=(0,b.useDeferredValue)(s),d=(0,p.useLazyLoadQuery)(void 0!==P?P:P=n(54880),{limit:150,offset:0,filter:0===(null===u||void 0===u?void 0:u.length)?null:'email ilike "%'+u+'%"'},{fetchPolicy:"store-and-network"}).user_list;return(0,_.jsx)(h.Z,(0,v.Z)({filterOption:!1,searchValue:s,loading:u!==s,onSearch:function(e){r(e)},onChange:function(e){a(g().find(null===d||void 0===d?void 0:d.items,(function(a){return(null===a||void 0===a?void 0:a.email)===e})))},showSearch:!0,placeholder:l("storageHost.quotaSettings.SelectUser"),options:g().map(null===d||void 0===d?void 0:d.items,(function(e){return{value:null===e||void 0===e?void 0:e.email,label:null===e||void 0===e?void 0:e.email}})).sort((function(e,a){return e.value&&a.value&&e.value>a.value?1:-1}))},t))},ne=n(63703),te=n(86199),le=n(39883),ie=function(e){var a=e.storageVolumeFrgmt,t=(0,m.$G)().t,l=(0,p.useFragment)(void 0!==T?T:T=n(16678),a),s=(0,b.useTransition)(),r=(0,S.Z)(s,2),u=r[0],d=r[1],c=(0,f.tQ)(),g=(0,b.useState)("user"),y=(0,S.Z)(g,2),v=y[0],k=y[1],h=(0,b.useState)(c),F=(0,S.Z)(h,2),Z=F[0],K=F[1],Q=(0,b.useState)(),j=(0,S.Z)(Q,2),L=j[0],D=j[1];(0,b.useState)();var H=(0,b.useState)(),V=(0,S.Z)(H,2),C=V[0],P=V[1],M=(0,b.useState)(),w=(0,S.Z)(M,2),U=w[0],I=w[1];(0,b.useState)();var E=(0,o.VQ)(v,("project"===v?L:C)||""),A=(0,ne.Z)(!1),N=(0,S.Z)(A,2),R=N[0],G=N[1].toggle,B=(0,f.Kr)("default"),O=(0,S.Z)(B,1)[0],X=(0,p.useLazyLoadQuery)(void 0!==$?$:$=n(81047),{quota_scope_id:E,skipQuotaScope:void 0===E||""===E,storage_host_name:(null===l||void 0===l?void 0:l.id)||""},{fetchPolicy:"network-only",fetchKey:O}).quota_scope;return(0,_.jsx)(i.Z,{direction:"column",align:"stretch",children:(0,_.jsxs)(te.Z,{title:t("storageHost.QuotaSettings"),tabList:[{key:"user",tab:t("storageHost.ForUser")},{key:"project",tab:t("storageHost.ForProject")}],activeTabKey:v,onTabChange:function(e){d((function(){k(e)}))},children:[(0,_.jsx)(i.Z,{justify:"between",children:"project"===v?(0,_.jsx)(i.Z,{style:{marginBottom:10},children:(0,_.jsxs)(W.Z,{layout:"inline",children:[(0,_.jsx)(W.Z.Item,{label:t("resourceGroup.Domain"),children:(0,_.jsx)(q,{style:{width:"20vw",marginRight:10},value:Z,onSelectDomain:function(e){d((function(){K(null===e||void 0===e?void 0:e.domainName),D(void 0)}))}})}),(0,_.jsx)(W.Z.Item,{label:t("webui.menu.Project"),children:(0,_.jsx)(x.Z,{style:{width:"20vw"},value:L,disabled:!Z,domain:Z||"",onSelectProject:function(e){d((function(){D(null===e||void 0===e?void 0:e.projectId)}))}})})]})}):(0,_.jsx)(W.Z,{layout:"inline",children:(0,_.jsx)(W.Z.Item,{label:t("data.User"),children:(0,_.jsx)(ae,{style:{width:"30vw",marginBottom:10},value:U,onSelectUser:function(e){I(null===e||void 0===e?void 0:e.email),d((function(){P(null===e||void 0===e?void 0:e.id)}))}})})})}),(0,_.jsx)(le.Z,{spinning:u,children:(0,_.jsx)(z,{quotaScopeFrgmt:X||null,onClickEdit:function(){G()},showAddButtonWhenEmpty:"project"===v&&!!L||"user"===v&&!!C})}),(0,_.jsx)(Y,{open:R,quotaScopeFrgmt:X||null,onRequestClose:function(){G()}})]})})},oe=n(60284),se=n(12674),re=function(){var e,a,t=(0,se.UO)().hostname,l=(0,f.Dj)(),o=(0,f.uB)(),s=(0,m.$G)().t,r=(0,p.useLazyLoadQuery)(void 0!==M?M:M=n(62913),{id:t||""}).storage_volume,d=null!==(e=null===r||void 0===r||null===(a=r.capabilities)||void 0===a?void 0:a.includes("quota"))&&void 0!==e&&e;return(0,_.jsxs)(i.Z,{direction:"column",align:"stretch",gap:"sm",children:[(0,_.jsx)(oe.Z,{items:[{title:s("webui.menu.Resources"),onClick:function(e){e.preventDefault(),o("/agent")},href:"/agent"},{title:s("storageHost.StorageSetting")}]}),(0,_.jsx)(u.Z.Title,{level:3,style:{margin:0},children:t||""}),(0,_.jsx)(y,{storageVolumeFrgmt:r||null}),l.supports("quota-scope")&&(0,_.jsx)(_.Fragment,{children:d?(0,_.jsx)(b.Suspense,{fallback:(0,_.jsx)("div",{children:"loading..."}),children:(0,_.jsx)(ie,{storageVolumeFrgmt:r||null})}):(0,_.jsx)(te.Z,{title:s("storageHost.QuotaSettings"),children:(0,_.jsx)(E.Z,{image:E.Z.PRESENTED_IMAGE_SIMPLE,description:s("storageHost.QuotaDoesNotSupported")})})})]})}},62913:function(e,a,n){n.r(a);var t=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"id"}],a=[{kind:"Variable",name:"id",variableName:"id"}],n={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"capabilities",storageKey:null};return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"StorageHostSettingPageQuery",selections:[{alias:null,args:a,concreteType:"StorageVolume",kind:"LinkedField",name:"storage_volume",plural:!1,selections:[n,t,{args:null,kind:"FragmentSpread",name:"StorageHostResourcePanelFragment"},{args:null,kind:"FragmentSpread",name:"StorageHostSettingsPanel_storageVolumeFrgmt"}],storageKey:null}],type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"StorageHostSettingPageQuery",selections:[{alias:null,args:a,concreteType:"StorageVolume",kind:"LinkedField",name:"storage_volume",plural:!1,selections:[n,t,{alias:null,args:null,kind:"ScalarField",name:"backend",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"usage",storageKey:null}],storageKey:null}]},params:{cacheID:"821175f86743d9d81be2a55aca371919",id:null,metadata:{},name:"StorageHostSettingPageQuery",operationKind:"query",text:"query StorageHostSettingPageQuery(\n  $id: String\n) {\n  storage_volume(id: $id) {\n    id\n    capabilities\n    ...StorageHostResourcePanelFragment\n    ...StorageHostSettingsPanel_storageVolumeFrgmt\n  }\n}\n\nfragment StorageHostResourcePanelFragment on StorageVolume {\n  id\n  backend\n  capabilities\n  path\n  usage\n}\n\nfragment StorageHostSettingsPanel_storageVolumeFrgmt on StorageVolume {\n  id\n  capabilities\n}\n"}}}();t.hash="f6e77057e83b0449ef99e8918e794b24",a.default=t}}]);
//# sourceMappingURL=790.ddbc56f4.chunk.js.map