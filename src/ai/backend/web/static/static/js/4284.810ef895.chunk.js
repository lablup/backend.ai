"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[4284],{44520:(e,n,l)=>{l.d(n,{A:()=>m});var t,i=l(83468),a=l(71155),r=l(50840),o=l(20307),s=l(6932),d=(l(76998),l(77678)),c=l(3606),u=l(23446);const m=e=>{let{endpointFrgmt:n}=e;const{t:m}=(0,d.Bd)(),{token:p}=r.A.useToken(),g=(0,i.CX)(),y=(0,c.useFragment)(void 0!==t?t:t=l(21553),n);return g.supports("model-serving-endpoint-user-info")?(null===y||void 0===y?void 0:y.created_user_email)===(null===y||void 0===y?void 0:y.session_owner_email)?(null===y||void 0===y?void 0:y.session_owner_email)||"":(0,u.jsxs)(u.Fragment,{children:[(null===y||void 0===y?void 0:y.session_owner_email)||"",(0,u.jsx)(o.A,{title:m("modelService.ServiceDelegatedFrom",{createdUser:(null===y||void 0===y?void 0:y.created_user_email)||"",sessionOwner:(null===y||void 0===y?void 0:y.session_owner_email)||""}),children:(0,u.jsx)(s.Ay,{size:"small",type:"text",icon:(0,u.jsx)(a.A,{}),style:{color:p.colorTextSecondary}})})]}):g.email||""}},73819:(e,n,l)=>{l.d(n,{A:()=>o});var t,i=l(48713),a=(l(76998),l(3606)),r=l(23446);const o=e=>{var n;let{endpointFrgmt:o}=e;const s=(0,a.useFragment)(void 0!==t?t:t=l(82740),o);let d="default";switch(null===s||void 0===s||null===(n=s.status)||void 0===n?void 0:n.toUpperCase()){case"RUNNING":case"HEALTHY":d="success"}return(0,r.jsx)(i.A,{color:d,children:null===s||void 0===s?void 0:s.status})}},34680:(e,n,l)=>{l.d(n,{A:()=>g});var t=l(25339),i=l(62863),a=l(50840),r=l(65080),o=l(24377),s=l(87627),d=l(45901),c=l.n(d),u=l(76998),m=l(77678),p=l(23446);const g=e=>{let{open:n,onRequestClose:l,columns:d,displayedColumnKeys:g,...y}=e;const v=(0,u.useRef)(null),{t:f}=(0,m.Bd)(),{token:k}=a.A.useToken(),x=d.map((e=>{return"string"===typeof e.title?{label:e.title,value:c().toString(e.key)}:"object"===typeof e.title&&"props"in e.title?{label:(n=e.title,u.Children.map(n.props.children,(e=>{if("string"===typeof e)return e}))),value:c().toString(e.key)}:{label:void 0,value:c().toString(e.key)};var n}));return(0,p.jsx)(t.A,{title:f("table.SettingTable"),open:n,destroyOnClose:!0,centered:!0,onOk:()=>{var e;null===(e=v.current)||void 0===e||e.validateFields().then((e=>{l(e)})).catch((()=>{}))},onCancel:()=>{l()},...y,children:(0,p.jsxs)(r.A,{ref:v,preserve:!1,initialValues:{selectedColumnKeys:g||x.map((e=>e.value))},layout:"vertical",children:[(0,p.jsx)(r.A.Item,{name:"searchInput",label:f("table.SelectColumnToDisplay"),style:{marginBottom:0},children:(0,p.jsx)(o.A,{prefix:(0,p.jsx)(i.A,{}),style:{marginBottom:k.marginSM},placeholder:f("table.SearchTableColumn")})}),(0,p.jsx)(r.A.Item,{noStyle:!0,shouldUpdate:(e,n)=>e.searchInput!==n.searchInput,children:e=>{let{getFieldValue:n}=e;const l=n("searchInput")?c().toLower(n("searchInput")):void 0,t=x.map((e=>c().toLower(c().toString(e.label)).includes(l||"")?e:{...e,style:{display:"none"}}));return(0,p.jsx)(r.A.Item,{name:"selectedColumnKeys",style:{height:220,overflowY:"auto"},children:(0,p.jsx)(s.A.Group,{options:t,style:{flexDirection:"column"}})})}})]})})}},21553:(e,n,l)=>{l.r(n),l.d(n,{default:()=>i});const t={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"EndpointOwnerInfoFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_user_email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"session_owner_email",storageKey:null}],type:"Endpoint",abstractKey:null,hash:"fb21a441c8873205b5092ae1a5a7157e"},i=t},82740:(e,n,l)=>{l.r(n),l.d(n,{default:()=>i});const t={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"EndpointStatusTagFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],type:"Endpoint",abstractKey:null,hash:"3b31efa50b55edddcb210b59003dc479"},i=t},94284:(e,n,l)=>{l.r(n),l.d(n,{default:()=>$});var t=l(44520),i=l(73819),a=l(29871),r=l(34680),o=l(30032),s=l(83468),d=l(16162),c=l(17413),u=l(96495),m=l(63718),p=l(97041),g=l(187),y=l(57277),v=l(93792),f=l(76998),k=l(21112),x=l(32693);var _=function(e){if(e.id,"undefined"===typeof cancelAnimationFrame)return clearInterval(e.id);cancelAnimationFrame(e.id)};const S=function(e,n,l){var t=null===l||void 0===l?void 0:l.immediate,i=(0,k.A)(e),a=(0,f.useRef)(),r=(0,f.useCallback)((function(){a.current&&_(a.current)}),[]);return(0,f.useEffect)((function(){if((0,x.Et)(n)&&!(n<0))return t&&i.current(),a.current=function(e,n){if(void 0===n&&(n=0),"undefined"===typeof requestAnimationFrame)return{id:setInterval(e,n)};var l=Date.now(),t={id:0},i=function(){Date.now()-l>=n&&(e(),l=Date.now()),t.id=requestAnimationFrame(i)};return t.id=requestAnimationFrame(i),t}((function(){i.current()}),n),r}),[n]),r};var h,b=l(44355),A=l(50840),C=l(24128),j=l(6932),F=l(59065),w=l(24717),E=l(71537),T=l(14455),K=l.n(T),O=l(45901),I=l.n(O),L=l(77678),P=l(3606),D=l(98322),N=l(23446);const $=e=>{let{children:n}=e;const{t:k}=(0,L.Bd)(),x=(0,s.CX)(),_=(0,s.f0)(),{token:T}=A.A.useToken(),O=(0,u.hd)(),[$,z]=(0,f.useState)(!1),[V,R]=(0,f.useState)(null),[B]=(0,f.useState)({current:1,pageSize:100}),[q,U]=(0,f.useTransition)(),[Q,H]=(0,s.Tw)("initial-fetch"),[W,X]=(0,f.useState)(),[Y]=(0,d.U6)(),M=[{title:k("modelService.EndpointName"),dataIndex:"endpoint_id",key:"endpointName",fixed:"left",render:(e,n)=>(0,N.jsx)(D.N_,{to:"/serving/"+e,children:n.name})},{title:k("modelService.EndpointId"),dataIndex:"endpoint_id",key:"endpoint_id",width:310,render:e=>(0,N.jsx)(C.A.Text,{code:!0,children:e})},{title:k("modelService.ServiceEndpoint"),dataIndex:"endpoint_id",key:"url",render:(e,n)=>n.url?(0,N.jsx)(C.A.Link,{copyable:!0,href:n.url,target:"_blank",children:n.url}):"-"},{title:k("modelService.Controls"),dataIndex:"controls",key:"controls",render:(e,n)=>{var l,t,i,r;return(0,N.jsxs)(a.A,{direction:"row",align:"stretch",children:[(0,N.jsx)(j.Ay,{type:"text",icon:(0,N.jsx)(m.A,{}),style:n.desired_session_count<0||"destroying"===(null===(l=n.status)||void 0===l?void 0:l.toLowerCase())||n.created_user_email&&n.created_user_email!==Y.email?{color:T.colorTextDisabled}:{color:T.colorInfo},disabled:n.desired_session_count<0||"destroying"===(null===(t=n.status)||void 0===t?void 0:t.toLowerCase())||!!n.created_user_email&&n.created_user_email!==Y.email,onClick:()=>{_("/service/update/"+n.endpoint_id)}}),(0,N.jsx)(F.A,{title:k("dialog.ask.DoYouWantToDeleteSomething",{name:n.name}),description:k("dialog.warning.CannotBeUndone"),okType:"danger",okText:k("button.Delete"),onConfirm:()=>{X(n.endpoint_id),ne.mutate((null===V||void 0===V?void 0:V.endpoint_id)||"",{onSuccess:e=>{U((()=>{H()})),w.Ay.success(k("modelService.ServiceTerminated",{name:null===V||void 0===V?void 0:V.name}))},onError:e=>{console.log(e),w.Ay.error(k("modelService.FailedToTerminateService"))}})},children:(0,N.jsx)(j.Ay,{type:"text",icon:(0,N.jsx)(p.A,{style:n.desired_session_count<0||"destroying"===(null===(i=n.status)||void 0===i?void 0:i.toLowerCase())?void 0:{color:T.colorError}}),loading:ne.isPending&&W===n.endpoint_id,disabled:n.desired_session_count<0||"destroying"===(null===(r=n.status)||void 0===r?void 0:r.toLowerCase()),onClick:()=>{R(n)}})})]})}},{title:k("modelService.Status"),key:"status",render:(e,n)=>(0,N.jsx)(i.A,{endpointFrgmt:n})},...x.is_admin?[{title:k("modelService.Owner"),dataIndex:"created_user_email",key:"session_owner",render:(e,n)=>(0,N.jsx)(t.A,{endpointFrgmt:n})}]:[],{title:k("modelService.CreatedAt"),dataIndex:"created_at",key:"createdAt",render:e=>K()(e).format("ll LT"),defaultSortOrder:"descend",sortDirections:["descend","ascend","descend"],sorter:(e,n)=>{const l=K()(e.created_at),t=K()(n.created_at);return l.diff(t)}},{title:k("modelService.DesiredSessionCount"),dataIndex:"desired_session_count",key:"desiredSessionCount",render:e=>e<0?"-":e},{title:(0,N.jsxs)(a.A,{direction:"column",align:"start",children:[k("modelService.RoutingsCount"),(0,N.jsx)("br",{}),(0,N.jsxs)(C.A.Text,{type:"secondary",style:{fontWeight:"normal"},children:["(",k("modelService.Active/Total"),")"]})]}),key:"routingCount",render:(e,n)=>{var l;return I().filter(n.routings,(e=>"HEALTHY"===(null===e||void 0===e?void 0:e.status))).length+" / "+(null===(l=n.routings)||void 0===l?void 0:l.length)}},{title:k("modelService.Public"),key:"public",render:(e,n)=>n.open_to_public?(0,N.jsx)(g.A,{style:{color:T.colorSuccess}}):(0,N.jsx)(y.A,{style:{color:T.colorTextSecondary}})}],[G,J]=(0,b.A)("backendaiwebui.EndpointListPage.displayedColumnKeys",{defaultValue:M.map((e=>I().toString(e.key)))});S((()=>{(0,f.startTransition)((()=>{H()}))}),7e3);const{endpoint_list:Z}=(0,P.useLazyLoadQuery)(void 0!==h?h:h=l(69139),{offset:(B.current-1)*B.pageSize,limit:B.pageSize,projectID:O.id},{fetchPolicy:"initial-fetch"===Q?"store-and-network":"network-only",fetchKey:Q}),ee=I().sortBy(null===Z||void 0===Z?void 0:Z.items,"name"),ne=(0,c.ET)({mutationFn:e=>(0,o.hu)({method:"DELETE",url:"/services/"+e,client:x})});return(0,N.jsxs)(N.Fragment,{children:[(0,N.jsxs)(a.A,{direction:"column",align:"stretch",children:[(0,N.jsxs)(a.A,{direction:"row",justify:"between",wrap:"wrap",gap:"xs",style:{padding:T.paddingContentVertical,paddingLeft:T.paddingContentHorizontalSM,paddingRight:T.paddingContentHorizontalSM},children:[(0,N.jsx)(a.A,{direction:"column",align:"start",children:(0,N.jsx)(C.A.Text,{style:{margin:0,padding:0},children:k("modelService.Services")})}),(0,N.jsx)(a.A,{direction:"row",gap:"xs",wrap:"wrap",style:{flexShrink:1},children:(0,N.jsxs)(a.A,{gap:"xs",children:[(0,N.jsx)(j.Ay,{icon:(0,N.jsx)(v.A,{}),loading:q,onClick:()=>{U((()=>H()))}}),(0,N.jsx)(j.Ay,{type:"primary",onClick:()=>{_("/service/start")},children:k("modelService.StartService")})]})})]}),(0,N.jsxs)(f.Suspense,{fallback:(0,N.jsx)("div",{children:"loading.."}),children:[(0,N.jsx)(E.A,{loading:q,scroll:{x:"max-content"},rowKey:"endpoint_id",dataSource:ee||[],columns:M.filter((e=>null===G||void 0===G?void 0:G.includes(I().toString(e.key))))}),(0,N.jsx)(a.A,{justify:"end",style:{padding:T.paddingXXS},children:(0,N.jsx)(j.Ay,{type:"text",icon:(0,N.jsx)(m.A,{}),onClick:()=>{z(!0)}})})]})]}),(0,N.jsx)(r.A,{open:$,onRequestClose:e=>{(null===e||void 0===e?void 0:e.selectedColumnKeys)&&J(null===e||void 0===e?void 0:e.selectedColumnKeys),z(!$)},columns:M,displayedColumnKeys:G||[]})]})}},69139:(e,n,l)=>{l.r(n),l.d(n,{default:()=>i});const t=function(){var e={defaultValue:null,kind:"LocalArgument",name:"limit"},n={defaultValue:null,kind:"LocalArgument",name:"offset"},l={defaultValue:null,kind:"LocalArgument",name:"projectID"},t=[{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"project",variableName:"projectID"}],i={alias:null,args:null,kind:"ScalarField",name:"total_count",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"endpoint_id",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"model",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"domain",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"project",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"resource_group",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"resource_slots",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"url",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"open_to_public",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},v={alias:null,args:null,kind:"ScalarField",name:"desired_session_count",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"routing_id",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"endpoint",storageKey:null},x={alias:null,args:null,kind:"ScalarField",name:"session",storageKey:null},_={alias:null,args:null,kind:"ScalarField",name:"traffic_ratio",storageKey:null},S={alias:null,args:null,concreteType:"RuntimeVariantInfo",kind:"LinkedField",name:"runtime_variant",plural:!1,selections:[a,{alias:null,args:null,kind:"ScalarField",name:"human_readable_name",storageKey:null}],storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"created_user_email",storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null};return{fragment:{argumentDefinitions:[e,n,l],kind:"Fragment",metadata:null,name:"EndpointListPageQuery",selections:[{alias:null,args:t,concreteType:"EndpointList",kind:"LinkedField",name:"endpoint_list",plural:!1,selections:[i,{alias:null,args:null,concreteType:"Endpoint",kind:"LinkedField",name:"items",plural:!0,selections:[a,r,o,s,d,c,u,m,p,g,y,{kind:"RequiredField",field:v,action:"NONE",path:"endpoint_list.items.desired_session_count"},{alias:null,args:null,concreteType:"Routing",kind:"LinkedField",name:"routings",plural:!0,selections:[f,k,x,_,d],storageKey:null},S,h,{args:null,kind:"FragmentSpread",name:"EndpointOwnerInfoFragment"},{args:null,kind:"FragmentSpread",name:"EndpointStatusTagFragment"}],storageKey:null}],storageKey:null}],type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[n,e,l],kind:"Operation",name:"EndpointListPageQuery",selections:[{alias:null,args:t,concreteType:"EndpointList",kind:"LinkedField",name:"endpoint_list",plural:!1,selections:[i,{alias:null,args:null,concreteType:"Endpoint",kind:"LinkedField",name:"items",plural:!0,selections:[a,r,o,s,d,c,u,m,p,g,y,v,{alias:null,args:null,concreteType:"Routing",kind:"LinkedField",name:"routings",plural:!0,selections:[f,k,x,_,d,b],storageKey:null},S,h,b,{alias:null,args:null,kind:"ScalarField",name:"session_owner_email",storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"33d744477c45761eba5a9577678bd62e",id:null,metadata:{},name:"EndpointListPageQuery",operationKind:"query",text:'query EndpointListPageQuery(\n  $offset: Int!\n  $limit: Int!\n  $projectID: UUID\n) {\n  endpoint_list(offset: $offset, limit: $limit, project: $projectID) {\n    total_count\n    items {\n      name\n      endpoint_id\n      model\n      domain\n      status\n      project\n      resource_group\n      resource_slots\n      url\n      open_to_public\n      created_at @since(version: "23.09.0")\n      desired_session_count\n      routings {\n        routing_id\n        endpoint\n        session\n        traffic_ratio\n        status\n        id\n      }\n      runtime_variant @since(version: "24.03.5") {\n        name\n        human_readable_name\n      }\n      created_user_email @since(version: "23.09.8")\n      ...EndpointOwnerInfoFragment\n      ...EndpointStatusTagFragment\n      id\n    }\n  }\n}\n\nfragment EndpointOwnerInfoFragment on Endpoint {\n  id\n  created_user_email @since(version: "23.09.8")\n  session_owner_email @since(version: "23.09.8")\n}\n\nfragment EndpointStatusTagFragment on Endpoint {\n  id\n  status\n}\n'}}}();t.hash="8d0358f328e4270cfec475084a51ff4e";const i=t},59065:(e,n,l)=>{l.d(n,{A:()=>C});var t=l(76998),i=l(58736),a=l(34156),r=l.n(a),o=l(23551),s=l(19727),d=l(28037),c=l(20315),u=l(47917),m=l(8357),p=l(6932),g=l(50675),y=l(29457),v=l(41271),f=l(59395),k=l(6132);const x=(0,k.OF)("Popconfirm",(e=>(e=>{const{componentCls:n,iconCls:l,antCls:t,zIndexPopup:i,colorText:a,colorWarning:r,marginXXS:o,marginXS:s,fontSize:d,fontWeightStrong:c,colorTextHeading:u}=e;return{[n]:{zIndex:i,[`&${t}-popover`]:{fontSize:d},[`${n}-message`]:{marginBottom:s,display:"flex",flexWrap:"nowrap",alignItems:"start",[`> ${n}-message-icon ${l}`]:{color:r,fontSize:d,lineHeight:1,marginInlineEnd:s},[`${n}-title`]:{fontWeight:c,color:u,"&:only-child":{fontWeight:"normal"}},[`${n}-description`]:{marginTop:o,color:a}},[`${n}-buttons`]:{textAlign:"end",whiteSpace:"nowrap",button:{marginInlineStart:s}}}}})(e)),(e=>{const{zIndexPopupBase:n}=e;return{zIndexPopup:n+60}}),{resetStyle:!1});var _=function(e,n){var l={};for(var t in e)Object.prototype.hasOwnProperty.call(e,t)&&n.indexOf(t)<0&&(l[t]=e[t]);if(null!=e&&"function"===typeof Object.getOwnPropertySymbols){var i=0;for(t=Object.getOwnPropertySymbols(e);i<t.length;i++)n.indexOf(t[i])<0&&Object.prototype.propertyIsEnumerable.call(e,t[i])&&(l[t[i]]=e[t[i]])}return l};const S=e=>{const{prefixCls:n,okButtonProps:l,cancelButtonProps:a,title:r,description:o,cancelText:s,okText:c,okType:f="primary",icon:k=t.createElement(i.A,null),showCancel:x=!0,close:_,onConfirm:S,onCancel:h,onPopupClick:b}=e,{getPrefixCls:A}=t.useContext(d.QO),[C]=(0,y.A)("Popconfirm",v.A.Popconfirm),j=(0,m.b)(r),F=(0,m.b)(o);return t.createElement("div",{className:`${n}-inner-content`,onClick:b},t.createElement("div",{className:`${n}-message`},k&&t.createElement("span",{className:`${n}-message-icon`},k),t.createElement("div",{className:`${n}-message-text`},j&&t.createElement("div",{className:`${n}-title`},j),F&&t.createElement("div",{className:`${n}-description`},F))),t.createElement("div",{className:`${n}-buttons`},x&&t.createElement(p.Ay,Object.assign({onClick:h,size:"small"},a),s||(null===C||void 0===C?void 0:C.cancelText)),t.createElement(u.A,{buttonProps:Object.assign(Object.assign({size:"small"},(0,g.DU)(f)),l),actionFn:S,close:_,prefixCls:A("btn"),quitOnNullishReturnValue:!0,emitEvent:!0},c||(null===C||void 0===C?void 0:C.okText))))},h=e=>{const{prefixCls:n,placement:l,className:i,style:a}=e,o=_(e,["prefixCls","placement","className","style"]),{getPrefixCls:s}=t.useContext(d.QO),c=s("popconfirm",n),[u]=x(c);return u(t.createElement(f.Ay,{placement:l,className:r()(c,i),style:a,content:t.createElement(S,Object.assign({prefixCls:c},o))}))};var b=function(e,n){var l={};for(var t in e)Object.prototype.hasOwnProperty.call(e,t)&&n.indexOf(t)<0&&(l[t]=e[t]);if(null!=e&&"function"===typeof Object.getOwnPropertySymbols){var i=0;for(t=Object.getOwnPropertySymbols(e);i<t.length;i++)n.indexOf(t[i])<0&&Object.prototype.propertyIsEnumerable.call(e,t[i])&&(l[t[i]]=e[t[i]])}return l};const A=t.forwardRef(((e,n)=>{var l,a;const{prefixCls:u,placement:m="top",trigger:p="click",okType:g="primary",icon:y=t.createElement(i.A,null),children:v,overlayClassName:f,onOpenChange:k,onVisibleChange:_}=e,h=b(e,["prefixCls","placement","trigger","okType","icon","children","overlayClassName","onOpenChange","onVisibleChange"]),{getPrefixCls:A}=t.useContext(d.QO),[C,j]=(0,o.A)(!1,{value:null!==(l=e.open)&&void 0!==l?l:e.visible,defaultValue:null!==(a=e.defaultOpen)&&void 0!==a?a:e.defaultVisible}),F=(e,n)=>{j(e,!0),null===_||void 0===_||_(e),null===k||void 0===k||k(e,n)},w=A("popconfirm",u),E=r()(w,f),[T]=x(w);return T(t.createElement(c.A,Object.assign({},(0,s.A)(h,["title"]),{trigger:p,placement:m,onOpenChange:(n,l)=>{const{disabled:t=!1}=e;t||F(n,l)},open:C,ref:n,overlayClassName:E,content:t.createElement(S,Object.assign({okType:g,icon:y},e,{prefixCls:w,close:e=>{F(!1,e)},onConfirm:n=>{var l;return null===(l=e.onConfirm)||void 0===l?void 0:l.call(void 0,n)},onCancel:n=>{var l;F(!1,n),null===(l=e.onCancel)||void 0===l||l.call(void 0,n)}})),"data-popover-inject":!0}),v))}));A._InternalPanelDoNotUseOrYouWillBeFired=h;const C=A}}]);
//# sourceMappingURL=4284.810ef895.chunk.js.map