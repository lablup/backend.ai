"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[9781],{35847:(e,n,l)=>{l.d(n,{A:()=>m});var t,i=l(51593),a=l(65666),r=l(50868),o=l(33789),s=l(60822),d=(l(43373),l(56762)),u=l(88522),c=l(73689);const m=e=>{let{endpointFrgmt:n}=e;const{t:m}=(0,d.Bd)(),{token:g}=r.A.useToken(),p=(0,i.CX)(),y=(0,u.useFragment)(void 0!==t?t:t=l(25608),n);return p.supports("model-serving-endpoint-user-info")?(null===y||void 0===y?void 0:y.created_user_email)===(null===y||void 0===y?void 0:y.session_owner_email)?(null===y||void 0===y?void 0:y.session_owner_email)||"":(0,c.jsxs)(c.Fragment,{children:[(null===y||void 0===y?void 0:y.session_owner_email)||"",(0,c.jsx)(o.A,{title:m("modelService.ServiceDelegatedFrom",{createdUser:(null===y||void 0===y?void 0:y.created_user_email)||"",sessionOwner:(null===y||void 0===y?void 0:y.session_owner_email)||""}),children:(0,c.jsx)(s.Ay,{size:"small",type:"text",icon:(0,c.jsx)(a.A,{}),style:{color:g.colorTextSecondary}})})]}):p.email||""}},66048:(e,n,l)=>{l.d(n,{A:()=>o});var t,i=l(15934),a=(l(43373),l(88522)),r=l(73689);const o=e=>{var n;let{endpointFrgmt:o}=e;const s=(0,a.useFragment)(void 0!==t?t:t=l(84865),o);let d="default";switch(null===s||void 0===s||null===(n=s.status)||void 0===n?void 0:n.toUpperCase()){case"RUNNING":case"HEALTHY":d="success"}return(0,r.jsx)(i.A,{color:d,children:null===s||void 0===s?void 0:s.status})}},30957:(e,n,l)=>{l.d(n,{A:()=>p});var t=l(94126),i=l(1499),a=l(50868),r=l(23702),o=l(67378),s=l(9833),d=l(89608),u=l.n(d),c=l(43373),m=l(56762),g=l(73689);const p=e=>{let{open:n,onRequestClose:l,columns:d,displayedColumnKeys:p,...y}=e;const v=(0,c.useRef)(null),{t:_}=(0,m.Bd)(),{token:f}=a.A.useToken(),k=d.map((e=>{return"string"===typeof e.title?{label:e.title,value:u().toString(e.key)}:"object"===typeof e.title&&"props"in e.title?{label:(n=e.title,c.Children.map(n.props.children,(e=>{if("string"===typeof e)return e}))),value:u().toString(e.key)}:{label:void 0,value:u().toString(e.key)};var n}));return(0,g.jsx)(t.A,{title:_("table.SettingTable"),open:n,destroyOnClose:!0,centered:!0,onOk:()=>{var e;null===(e=v.current)||void 0===e||e.validateFields().then((e=>{l(e)})).catch((()=>{}))},onCancel:()=>{l()},...y,children:(0,g.jsxs)(r.A,{ref:v,preserve:!1,initialValues:{selectedColumnKeys:p||k.map((e=>e.value))},layout:"vertical",children:[(0,g.jsx)(r.A.Item,{name:"searchInput",label:_("table.SelectColumnToDisplay"),style:{marginBottom:0},children:(0,g.jsx)(o.A,{prefix:(0,g.jsx)(i.A,{}),style:{marginBottom:f.marginSM},placeholder:_("table.SearchTableColumn")})}),(0,g.jsx)(r.A.Item,{noStyle:!0,shouldUpdate:(e,n)=>e.searchInput!==n.searchInput,children:e=>{let{getFieldValue:n}=e;const l=n("searchInput")?u().toLower(n("searchInput")):void 0,t=k.map((e=>u().toLower(u().toString(e.label)).includes(l||"")?e:{...e,style:{display:"none"}}));return(0,g.jsx)(r.A.Item,{name:"selectedColumnKeys",style:{height:220,overflowY:"auto"},children:(0,g.jsx)(s.A.Group,{options:t,style:{flexDirection:"column"}})})}})]})})}},25608:(e,n,l)=>{l.r(n),l.d(n,{default:()=>i});const t={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"EndpointOwnerInfoFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_user_email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"session_owner_email",storageKey:null}],type:"Endpoint",abstractKey:null,hash:"fb21a441c8873205b5092ae1a5a7157e"},i=t},84865:(e,n,l)=>{l.r(n),l.d(n,{default:()=>i});const t={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"EndpointStatusTagFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],type:"Endpoint",abstractKey:null,hash:"3b31efa50b55edddcb210b59003dc479"},i=t},9781:(e,n,l)=>{l.r(n),l.d(n,{default:()=>N});var t=l(35847),i=l(66048),a=l(89130),r=l(30957),o=l(58879),s=l(51593),d=l(11899),u=l(60881),c=l(15634),m=l(81850),g=l(64703),p=l(66231),y=l(67425),v=l(40567),_=l(44954),f=l(43373),k=l(46976),S=l(92685);var h=function(e){if(e.id,"undefined"===typeof cancelAnimationFrame)return clearInterval(e.id);cancelAnimationFrame(e.id)};const x=function(e,n,l){var t=null===l||void 0===l?void 0:l.immediate,i=(0,k.A)(e),a=(0,f.useRef)(),r=(0,f.useCallback)((function(){a.current&&h(a.current)}),[]);return(0,f.useEffect)((function(){if((0,S.Et)(n)&&!(n<0))return t&&i.current(),a.current=function(e,n){if(void 0===n&&(n=0),"undefined"===typeof requestAnimationFrame)return{id:setInterval(e,n)};var l=Date.now(),t={id:0},i=function(){Date.now()-l>=n&&(e(),l=Date.now()),t.id=requestAnimationFrame(i)};return t.id=requestAnimationFrame(i),t}((function(){i.current()}),n),r}),[n]),r};var A,F=l(55429),b=l(44733),j=l(50868),K=l(85690),w=l(60822),C=l(2293),T=l(77731),E=l(12731),I=l.n(E),L=l(89608),D=l.n(L),V=l(56762),z=l(88522),O=l(97734),R=l(73689);const N=e=>{let{children:n}=e;const{t:k}=(0,V.Bd)(),{message:S,modal:h}=b.A.useApp(),E=(0,s.CX)(),L=(0,s.f0)(),{token:N}=j.A.useToken(),q=(0,c.hd)(),[P,$]=(0,f.useState)(!1),[B,U]=(0,f.useState)("created&destroying"),H=(0,f.useDeferredValue)(B),[Q,X]=(0,f.useState)({current:1,pageSize:10}),Y=(0,f.useDeferredValue)(Q),G=B!==H||Q!==Y,[M,W]=(0,f.useTransition)(),[J,Z]=(0,s.Tw)("initial-fetch"),[ee,ne]=(0,f.useState)(),[le]=(0,d.U6)(),te=[{title:k("modelService.EndpointName"),dataIndex:"endpoint_id",key:"endpointName",fixed:"left",render:(e,n)=>(0,R.jsx)(O.N_,{to:"/serving/"+e,children:n.name})},{title:k("modelService.EndpointId"),dataIndex:"endpoint_id",key:"endpoint_id",width:310,render:e=>(0,R.jsx)(K.A.Text,{code:!0,children:e})},{title:k("modelService.ServiceEndpoint"),dataIndex:"endpoint_id",key:"url",render:(e,n)=>n.url?(0,R.jsx)(K.A.Link,{copyable:!0,href:n.url,target:"_blank",children:n.url}):"-"},{title:k("modelService.Controls"),dataIndex:"controls",key:"controls",render:(e,n)=>{var l,t,i,r;return(0,R.jsxs)(a.A,{direction:"row",align:"stretch",children:[(0,R.jsx)(w.Ay,{type:"text",icon:(0,R.jsx)(m.A,{}),style:n.desired_session_count<0||"destroying"===(null===(l=n.status)||void 0===l?void 0:l.toLowerCase())||n.created_user_email&&n.created_user_email!==le.email?{color:N.colorTextDisabled}:{color:N.colorInfo},disabled:n.desired_session_count<0||"destroying"===(null===(t=n.status)||void 0===t?void 0:t.toLowerCase())||!!n.created_user_email&&n.created_user_email!==le.email,onClick:()=>{L("/service/update/"+n.endpoint_id)}}),(0,R.jsx)(w.Ay,{type:"text",icon:(0,R.jsx)(g.A,{style:n.desired_session_count<0||"destroying"===(null===(i=n.status)||void 0===i?void 0:i.toLowerCase())?void 0:{color:N.colorError}}),loading:se.isPending&&ee===n.endpoint_id,disabled:n.desired_session_count<0||"destroying"===(null===(r=n.status)||void 0===r?void 0:r.toLowerCase()),onClick:()=>{h.confirm({title:k("dialog.ask.DoYouWantToDeleteSomething",{name:n.name}),content:k("dialog.warning.CannotBeUndone"),okText:k("button.Delete"),okButtonProps:{danger:!0,type:"primary"},onOk:()=>{ne(n.endpoint_id),n.endpoint_id&&se.mutate(n.endpoint_id,{onSuccess:e=>{W((()=>{Z()})),e.success?S.success(k("modelService.ServiceTerminated",{name:null===n||void 0===n?void 0:n.name})):S.error(k("modelService.FailedToTerminateService"))},onError:e=>{S.error(k("modelService.FailedToTerminateService"))}})}})}})]})}},{title:k("modelService.Status"),key:"status",render:(e,n)=>(0,R.jsx)(i.A,{endpointFrgmt:n})},...E.is_admin?[{title:k("modelService.Owner"),dataIndex:"created_user_email",key:"session_owner",render:(e,n)=>(0,R.jsx)(t.A,{endpointFrgmt:n})}]:[],{title:k("modelService.CreatedAt"),dataIndex:"created_at",key:"createdAt",render:e=>I()(e).format("ll LT"),defaultSortOrder:"descend",sortDirections:["descend","ascend","descend"],sorter:(e,n)=>{const l=I()(e.created_at),t=I()(n.created_at);return l.diff(t)}},{title:k("modelService.DesiredSessionCount"),dataIndex:"desired_session_count",key:"desiredSessionCount",render:e=>e<0?"-":e},{title:(0,R.jsxs)(a.A,{direction:"column",align:"start",children:[k("modelService.RoutingsCount"),(0,R.jsx)("br",{}),(0,R.jsxs)(K.A.Text,{type:"secondary",style:{fontWeight:"normal"},children:["(",k("modelService.Active/Total"),")"]})]}),key:"routingCount",render:(e,n)=>{var l;return D().filter(n.routings,(e=>"HEALTHY"===(null===e||void 0===e?void 0:e.status))).length+" / "+(null===(l=n.routings)||void 0===l?void 0:l.length)}},{title:k("modelService.Public"),key:"public",render:(e,n)=>n.open_to_public?(0,R.jsx)(p.A,{style:{color:N.colorSuccess}}):(0,R.jsx)(y.A,{style:{color:N.colorTextSecondary}})}],[ie,ae]=(0,F.A)("backendaiwebui.EndpointListPage.displayedColumnKeys",{defaultValue:te.map((e=>D().toString(e.key)))});x((()=>{(0,f.startTransition)((()=>{Z()}))}),7e3);const{endpoint_list:re}=(0,z.useLazyLoadQuery)(void 0!==A?A:A=l(8132),{offset:(Y.current-1)*Y.pageSize,limit:Y.pageSize,projectID:q.id,filter:"created&destroying"===H?'lifecycle_stage == "created" | lifecycle_stage == "destroying"':`lifecycle_stage == "${H}"`},{fetchPolicy:"network-only",fetchKey:J}),oe=D().sortBy(null===re||void 0===re?void 0:re.items,"name"),se=(0,u.ET)({mutationFn:e=>(0,o.hu)({method:"DELETE",url:"/services/"+e,client:E})});return(0,R.jsxs)(a.A,{direction:"column",align:"stretch",children:[(0,R.jsxs)(a.A,{direction:"row",justify:"between",wrap:"wrap",gap:"xs",style:{padding:N.paddingContentVertical,paddingLeft:N.paddingContentHorizontalSM,paddingRight:N.paddingContentHorizontalSM},children:[(0,R.jsx)(a.A,{direction:"column",align:"start",children:(0,R.jsx)(C.Ay.Group,{value:B,onChange:e=>{var n;U(null===(n=e.target)||void 0===n?void 0:n.value),X({current:1,pageSize:Q.pageSize})},optionType:"button",buttonStyle:"solid",options:[{label:"Active",value:"created&destroying"},{label:"Destroyed",value:"destroyed"}]})}),(0,R.jsx)(a.A,{direction:"row",gap:"xs",wrap:"wrap",style:{flexShrink:1},children:(0,R.jsxs)(a.A,{gap:"xs",children:[(0,R.jsx)(w.Ay,{icon:(0,R.jsx)(v.A,{}),loading:M,onClick:()=>{W((()=>Z()))}}),(0,R.jsx)(w.Ay,{type:"primary",onClick:()=>{L("/service/start")},children:k("modelService.StartService")})]})})]}),(0,R.jsx)(T.A,{loading:{spinning:G,indicator:(0,R.jsx)(_.A,{})},scroll:{x:"max-content"},rowKey:"endpoint_id",dataSource:oe||[],columns:te.filter((e=>null===ie||void 0===ie?void 0:ie.includes(D().toString(e.key)))),pagination:{pageSize:Q.pageSize,current:Q.current,pageSizeOptions:["10","20","50"],total:(null===re||void 0===re?void 0:re.total_count)||0,showSizeChanger:!0,onChange(e,n){X({current:e,pageSize:n})},style:{marginRight:N.marginXS}}}),(0,R.jsx)(a.A,{justify:"end",style:{padding:N.paddingXXS},children:(0,R.jsx)(w.Ay,{type:"text",icon:(0,R.jsx)(m.A,{}),onClick:()=>{$(!0)}})}),(0,R.jsx)(r.A,{open:P,onRequestClose:e=>{(null===e||void 0===e?void 0:e.selectedColumnKeys)&&ae(null===e||void 0===e?void 0:e.selectedColumnKeys),$(!P)},columns:te,displayedColumnKeys:ie||[]})]})}},8132:(e,n,l)=>{l.r(n),l.d(n,{default:()=>i});const t=function(){var e={defaultValue:null,kind:"LocalArgument",name:"filter"},n={defaultValue:null,kind:"LocalArgument",name:"limit"},l={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"projectID"},i=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"project",variableName:"projectID"}],a={alias:null,args:null,kind:"ScalarField",name:"total_count",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"endpoint_id",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"model",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"domain",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"project",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"resource_group",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"resource_slots",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"url",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"open_to_public",storageKey:null},v={alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},_={alias:null,args:null,kind:"ScalarField",name:"desired_session_count",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"routing_id",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"endpoint",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"session",storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"traffic_ratio",storageKey:null},x={alias:null,args:null,concreteType:"RuntimeVariantInfo",kind:"LinkedField",name:"runtime_variant",plural:!1,selections:[r,{alias:null,args:null,kind:"ScalarField",name:"human_readable_name",storageKey:null}],storageKey:null},A={alias:null,args:null,kind:"ScalarField",name:"created_user_email",storageKey:null},F={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null};return{fragment:{argumentDefinitions:[e,n,l,t],kind:"Fragment",metadata:null,name:"EndpointListPageQuery",selections:[{alias:null,args:i,concreteType:"EndpointList",kind:"LinkedField",name:"endpoint_list",plural:!1,selections:[a,{alias:null,args:null,concreteType:"Endpoint",kind:"LinkedField",name:"items",plural:!0,selections:[r,o,s,d,u,c,m,g,p,y,v,{kind:"RequiredField",field:_,action:"NONE",path:"endpoint_list.items.desired_session_count"},{alias:null,args:null,concreteType:"Routing",kind:"LinkedField",name:"routings",plural:!0,selections:[f,k,S,h,u],storageKey:null},x,A,{args:null,kind:"FragmentSpread",name:"EndpointOwnerInfoFragment"},{args:null,kind:"FragmentSpread",name:"EndpointStatusTagFragment"}],storageKey:null}],storageKey:null}],type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,n,t,e],kind:"Operation",name:"EndpointListPageQuery",selections:[{alias:null,args:i,concreteType:"EndpointList",kind:"LinkedField",name:"endpoint_list",plural:!1,selections:[a,{alias:null,args:null,concreteType:"Endpoint",kind:"LinkedField",name:"items",plural:!0,selections:[r,o,s,d,u,c,m,g,p,y,v,_,{alias:null,args:null,concreteType:"Routing",kind:"LinkedField",name:"routings",plural:!0,selections:[f,k,S,h,u,F],storageKey:null},x,A,F,{alias:null,args:null,kind:"ScalarField",name:"session_owner_email",storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"44748285f349a9d059efd5b64975c446",id:null,metadata:{},name:"EndpointListPageQuery",operationKind:"query",text:'query EndpointListPageQuery(\n  $offset: Int!\n  $limit: Int!\n  $projectID: UUID\n  $filter: String\n) {\n  endpoint_list(offset: $offset, limit: $limit, project: $projectID, filter: $filter) {\n    total_count\n    items {\n      name\n      endpoint_id\n      model\n      domain\n      status\n      project\n      resource_group\n      resource_slots\n      url\n      open_to_public\n      created_at @since(version: "23.09.0")\n      desired_session_count\n      routings {\n        routing_id\n        endpoint\n        session\n        traffic_ratio\n        status\n        id\n      }\n      runtime_variant @since(version: "24.03.5") {\n        name\n        human_readable_name\n      }\n      created_user_email @since(version: "23.09.8")\n      ...EndpointOwnerInfoFragment\n      ...EndpointStatusTagFragment\n      id\n    }\n  }\n}\n\nfragment EndpointOwnerInfoFragment on Endpoint {\n  id\n  created_user_email @since(version: "23.09.8")\n  session_owner_email @since(version: "23.09.8")\n}\n\nfragment EndpointStatusTagFragment on Endpoint {\n  id\n  status\n}\n'}}}();t.hash="114c24611862a1a2577a867b9bc71359";const i=t}}]);
//# sourceMappingURL=9781.b4a3a1d5.chunk.js.map