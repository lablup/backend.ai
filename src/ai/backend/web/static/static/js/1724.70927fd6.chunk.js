"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[1724],{5621:(e,n,t)=>{t.d(n,{A:()=>c});var a=t(29871),l=t(48713),r=t(45901),i=t.n(r),o=t(76998),s=t(23446);const c=e=>{let n,{values:t=[]}=e;return 0===t.length?null:(n=t[0]&&("string"===typeof t[0]||o.isValidElement(t[0]))?t.map((e=>({label:e,color:"blue"}))):t,(0,s.jsx)(a.A,{direction:"row",children:i().map(n,((e,t)=>(0,s.jsx)(l.A,{style:i().last(n)===e?void 0:{margin:0,marginRight:-1},color:e.color,children:e.label},t)))}))}},55256:(e,n,t)=>{t.d(n,{Ay:()=>b,Kk:()=>y,p3:()=>v,sT:()=>m,vB:()=>g});var a=t(83468),l=t(5621),r=t(29871),i=t(48713),o=t(45901),s=t.n(o),c=t(76998),d=t(23446);const u=e=>{let{image:n,...t}=e;n=n||"";const[,{getImageAliasName:r,getBaseVersion:i,tagAlias:o}]=(0,a.Gj)();return(0,d.jsx)(l.A,{values:[{label:o(r(n)),color:"blue"},{label:i(n),color:"green"}],...t})},g=e=>{let{image:n,...t}=e;n=n||"";const[,{getBaseVersion:l,tagAlias:r}]=(0,a.Gj)();return(0,d.jsx)(i.A,{color:"green",...t,children:r(l(n))})},m=e=>{let{image:n,...t}=e;n=n||"";const[,{getBaseImage:l,tagAlias:r}]=(0,a.Gj)();return(0,d.jsx)(i.A,{color:"green",...t,children:r(l(n))})},p=e=>{let{image:n,...t}=e;n=n||"";const[,{getArchitecture:l,tagAlias:r}]=(0,a.Gj)();return(0,d.jsx)(i.A,{color:"green",...t,children:r(l(n))})},y=e=>{let{image:n,...t}=e;n=n||"";const[,{getImageLang:l,tagAlias:r}]=(0,a.Gj)();return(0,d.jsx)(i.A,{color:"green",...t,children:r(l(n))})},v=e=>{let{image:n,labels:t,...o}=e;n=n||"",t=t||[];const[,{getFilteredRequirementsTags:c,getCustomTag:u,tagAlias:g}]=(0,a.Gj)();return(0,d.jsxs)(r.A,{children:[s().map(c(n),((e,n)=>(0,d.jsx)(i.A,{color:"blue",...o,children:g(e||"")},n))),(0,d.jsx)(l.A,{color:"cyan",values:[{label:"Customized",color:"cyan"},{label:u(t),color:"cyan"}],...o})]})},f=(e,n)=>{let{image:t,style:a={}}=e;return t=t||"",(0,d.jsxs)(d.Fragment,{children:[(0,d.jsx)(u,{image:t}),(0,d.jsx)(m,{image:t}),(0,d.jsx)(p,{image:t})]})},b=c.memo(f)},34680:(e,n,t)=>{t.d(n,{A:()=>p});var a=t(34103),l=t(83786),r=t(50840),i=t(7121),o=t(63284),s=t(87627),c=t(45901),d=t.n(c),u=t(76998),g=t(77678),m=t(23446);const p=e=>{let{open:n,onRequestClose:t,columns:c,displayedColumnKeys:p,...y}=e;const v=(0,u.useRef)(null),{t:f}=(0,g.Bd)(),{token:b}=r.A.useToken(),x=c.map((e=>{return"string"===typeof e.title?{label:e.title,value:d().toString(e.key)}:"object"===typeof e.title&&"props"in e.title?{label:(n=e.title,u.Children.map(n.props.children,(e=>{if("string"===typeof e)return e}))),value:d().toString(e.key)}:{label:void 0,value:d().toString(e.key)};var n}));return(0,m.jsx)(a.A,{title:f("table.SettingTable"),open:n,destroyOnClose:!0,centered:!0,onOk:()=>{var e;null===(e=v.current)||void 0===e||e.validateFields().then((e=>{t(e)})).catch((()=>{}))},onCancel:()=>{t()},...y,children:(0,m.jsxs)(i.A,{ref:v,preserve:!1,initialValues:{selectedColumnKeys:p||x.map((e=>e.value))},layout:"vertical",children:[(0,m.jsx)(i.A.Item,{name:"searchInput",label:f("table.SelectColumnToDisplay"),style:{marginBottom:0},children:(0,m.jsx)(o.A,{prefix:(0,m.jsx)(l.A,{}),style:{marginBottom:b.marginSM},placeholder:f("table.SearchTableColumn")})}),(0,m.jsx)(i.A.Item,{noStyle:!0,shouldUpdate:(e,n)=>e.searchInput!==n.searchInput,children:e=>{let{getFieldValue:n}=e;const t=n("searchInput")?d().toLower(n("searchInput")):void 0,a=x.map((e=>d().toLower(d().toString(e.label)).includes(t||"")?e:{...e,style:{display:"none"}}));return(0,m.jsx)(i.A.Item,{name:"selectedColumnKeys",style:{height:220,overflowY:"auto"},children:(0,m.jsx)(s.A.Group,{options:a,style:{flexDirection:"column"}})})}})]})})}},21724:(e,n,t)=>{t.r(n),t.d(n,{default:()=>O});var a,l,r=t(29871),i=t(36009),o=t(55256),s=t(34680),c=t(30032),d=t(83468),u=t(97041),g=t(63718),m=t(44355),p=t(50840),y=t(78969),v=t(97080),f=t(59065),b=t(6932),x=t(29475),h=t(94120),A=t(45901),k=t.n(A),C=t(76998),j=t(77678),S=t(3606),_=t(23446);const O=e=>{let{children:n}=e;const{t:A}=(0,j.Bd)(),{token:O}=p.A.useToken(),{message:T}=y.A.useApp(),[I,K]=(0,C.useState)(!1),[F]=(0,C.useState)("images"),[P,E]=(0,C.useTransition)(),[w,B]=(0,d.Tw)("initial-fetch"),[N,z]=(0,C.useState)(),[,{getNamespace:M,getImageLang:V,getBaseVersion:D,getBaseImage:L,getCustomTag:R,getFilteredRequirementsTags:q}]=(0,d.Gj)(),{customized_images:Q}=(0,S.useLazyLoadQuery)(void 0!==a?a:a=t(38867),{},{fetchPolicy:"initial-fetch"===w?"store-and-network":"network-only",fetchKey:w}),[U,X]=(0,S.useMutation)(void 0!==l?l:l=t(60681)),G=[{title:A("environment.Registry"),dataIndex:"registry",key:"registry",sorter:(e,n)=>null!==e&&void 0!==e&&e.registry&&null!==n&&void 0!==n&&n.registry?e.registry.localeCompare(n.registry):0},{title:A("environment.Architecture"),dataIndex:"architecture",key:"architecture",sorter:(e,n)=>null!==e&&void 0!==e&&e.architecture&&null!==n&&void 0!==n&&n.architecture?e.architecture.localeCompare(n.architecture):0},{title:A("environment.Namespace"),key:"namespace",sorter:(e,n)=>{const t=M((0,c.A_)(e)||""),a=M((0,c.A_)(n)||"");return t&&a?t.localeCompare(a):0},render:(e,n)=>(0,_.jsx)("span",{children:M((0,c.A_)(n)||"")})},{title:A("environment.Language"),key:"lang",sorter:(e,n)=>{const t=V((0,c.A_)(e)||""),a=V((0,c.A_)(n)||"");return t&&a?t.localeCompare(a):0},render:(e,n)=>(0,_.jsx)(o.Kk,{image:(0,c.A_)(n)||"",color:"green"})},{title:A("environment.Version"),key:"baseversion",sorter:(e,n)=>{const t=D((0,c.A_)(e)||""),a=D((0,c.A_)(n)||"");return t&&a?t.localeCompare(a):0},render:(e,n)=>(0,_.jsx)(o.vB,{image:(0,c.A_)(n)||"",color:"green"})},{title:A("environment.Base"),key:"baseimage",sorter:(e,n)=>{const t=L((0,c.A_)(e)||""),a=L((0,c.A_)(n)||"");return t&&a?t.localeCompare(a):0},render:(e,n)=>(0,_.jsx)(o.sT,{image:(0,c.A_)(n)||""})},{title:A("environment.Constraint"),key:"constraint",sorter:(e,n)=>{const t=e=>{const n=(0,c.A_)(e)||"",t=k().get(e,"labels",[]);return q(n).join("")+"Customized"+R(t)},a=t(e),l=t(n);return a&&l?a.localeCompare(l):0},render:(e,n)=>(0,_.jsx)(o.p3,{image:(0,c.A_)(n)||"",labels:null===n||void 0===n?void 0:n.labels})},{title:A("environment.Digest"),dataIndex:"digest",key:"digest",sorter:(e,n)=>null!==e&&void 0!==e&&e.digest&&null!==n&&void 0!==n&&n.digest?e.digest.localeCompare(n.digest):0},{title:A("general.Control"),key:"control",fixed:"right",render:(e,n)=>(0,_.jsxs)(r.A,{direction:"row",align:"stretch",justify:"center",gap:"xxs",children:[(0,_.jsx)(v.A.Text,{copyable:{text:(0,c.A_)(n)||""},style:{paddingTop:O.paddingXXS,paddingBottom:O.paddingXXS}}),(0,_.jsx)(f.A,{title:A("dialog.ask.DoYouWantToProceed"),description:A("dialog.warning.CannotBeUndone"),okType:"danger",okText:A("button.Delete"),onConfirm:()=>{null!==n&&void 0!==n&&n.id&&(z(n.id+w),U({variables:{id:n.id},onCompleted(e,n){var t;n?T.error(null===(t=n[0])||void 0===t?void 0:t.message):(E((()=>{B()})),T.success(A("environment.CustomizedImageSuccessfullyDeleted")))},onError(e){T.error(null===e||void 0===e?void 0:e.message)}}))},children:(0,_.jsx)(b.Ay,{type:"text",icon:(0,_.jsx)(u.A,{}),danger:!0,loading:X&&N===(null===n||void 0===n?void 0:n.id)+w,disabled:X&&N!==(null===n||void 0===n?void 0:n.id)+w})})]})}],[W,Y]=(0,m.A)("backendaiwebui.MyEnvironmentPage.displayedColumnKeys",{defaultValue:G.map((e=>k().toString(e.key)))});return(0,_.jsxs)(r.A,{direction:"column",align:"stretch",gap:"xs",children:[(0,_.jsx)(r.A,{direction:"column",align:"stretch",children:(0,_.jsx)(x.A,{tabList:[{key:"images",label:A("environment.Images")}],activeTabKey:F,styles:{body:{padding:0,paddingTop:1}},children:(0,_.jsxs)(C.Suspense,{fallback:(0,_.jsx)(i.A,{}),children:[(0,_.jsx)(h.A,{loading:P,columns:G.filter((e=>null===W||void 0===W?void 0:W.includes(k().toString(e.key)))),dataSource:Q,rowKey:"id",scroll:{x:"max-content"},pagination:!1}),(0,_.jsx)(r.A,{justify:"end",style:{padding:O.paddingXXS},children:(0,_.jsx)(b.Ay,{type:"text",icon:(0,_.jsx)(g.A,{}),onClick:()=>{K(!0)}})})]})})}),(0,_.jsx)(s.A,{open:I,onRequestClose:e=>{(null===e||void 0===e?void 0:e.selectedColumnKeys)&&Y(null===e||void 0===e?void 0:e.selectedColumnKeys),K(!I)},columns:G,displayedColumnKeys:W||[]})]})}},60681:(e,n,t)=>{t.r(n),t.d(n,{default:()=>l});const a=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"id"}],n=[{kind:"Variable",name:"image_id",variableName:"id"}],t=[{alias:null,args:null,kind:"ScalarField",name:"ok",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"msg",storageKey:null}],a=[{alias:null,args:n,concreteType:"UntagImageFromRegistry",kind:"LinkedField",name:"untag_image_from_registry",plural:!1,selections:t,storageKey:null},{alias:null,args:n,concreteType:"ForgetImageById",kind:"LinkedField",name:"forget_image_by_id",plural:!1,selections:t,storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"MyEnvironmentPageForgetAndUntagMutation",selections:a,type:"Mutations",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"MyEnvironmentPageForgetAndUntagMutation",selections:a},params:{cacheID:"5b4f7c5bc899b115592fccdc6efe534d",id:null,metadata:{},name:"MyEnvironmentPageForgetAndUntagMutation",operationKind:"mutation",text:"mutation MyEnvironmentPageForgetAndUntagMutation(\n  $id: String!\n) {\n  untag_image_from_registry(image_id: $id) {\n    ok\n    msg\n  }\n  forget_image_by_id(image_id: $id) {\n    ok\n    msg\n  }\n}\n"}}}();a.hash="c32a5d49badf02c6b0693522e8e84c82";const l=a},38867:(e,n,t)=>{t.r(n),t.d(n,{default:()=>l});const a=function(){var e=[{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"customized_images",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"humanized_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"digest",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"supported_accelerators",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"MyEnvironmentPageQuery",selections:e,type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"MyEnvironmentPageQuery",selections:e},params:{cacheID:"c1773ff683a165a627b1084bb7f99dfc",id:null,metadata:{},name:"MyEnvironmentPageQuery",operationKind:"query",text:"query MyEnvironmentPageQuery {\n  customized_images {\n    id\n    name\n    humanized_name\n    tag\n    registry\n    architecture\n    digest\n    labels {\n      key\n      value\n    }\n    supported_accelerators\n  }\n}\n"}}}();a.hash="239a93f593bbc6b5d31bbe53ca71e10d";const l=a},83786:(e,n,t)=>{t.d(n,{A:()=>s});var a=t(58168),l=t(76998),r=t(70253),i=t(13410),o=function(e,n){return l.createElement(i.A,(0,a.A)({},e,{ref:n,icon:r.A}))};const s=l.forwardRef(o)},59065:(e,n,t)=>{t.d(n,{A:()=>S});var a=t(76998),l=t(24916),r=t(34156),i=t.n(r),o=t(23551),s=t(19727),c=t(28037),d=t(20315),u=t(47917),g=t(8357),m=t(6932),p=t(50675),y=t(29457),v=t(41271),f=t(59395),b=t(55864);const x=(0,b.OF)("Popconfirm",(e=>(e=>{const{componentCls:n,iconCls:t,antCls:a,zIndexPopup:l,colorText:r,colorWarning:i,marginXXS:o,marginXS:s,fontSize:c,fontWeightStrong:d,colorTextHeading:u}=e;return{[n]:{zIndex:l,["&".concat(a,"-popover")]:{fontSize:c},["".concat(n,"-message")]:{marginBottom:s,display:"flex",flexWrap:"nowrap",alignItems:"start",["> ".concat(n,"-message-icon ").concat(t)]:{color:i,fontSize:c,lineHeight:1,marginInlineEnd:s},["".concat(n,"-title")]:{fontWeight:d,color:u,"&:only-child":{fontWeight:"normal"}},["".concat(n,"-description")]:{marginTop:o,color:r}},["".concat(n,"-buttons")]:{textAlign:"end",whiteSpace:"nowrap",button:{marginInlineStart:s}}}}})(e)),(e=>{const{zIndexPopupBase:n}=e;return{zIndexPopup:n+60}}),{resetStyle:!1});var h=function(e,n){var t={};for(var a in e)Object.prototype.hasOwnProperty.call(e,a)&&n.indexOf(a)<0&&(t[a]=e[a]);if(null!=e&&"function"===typeof Object.getOwnPropertySymbols){var l=0;for(a=Object.getOwnPropertySymbols(e);l<a.length;l++)n.indexOf(a[l])<0&&Object.prototype.propertyIsEnumerable.call(e,a[l])&&(t[a[l]]=e[a[l]])}return t};const A=e=>{const{prefixCls:n,okButtonProps:t,cancelButtonProps:r,title:o,description:s,cancelText:d,okText:f,okType:b="primary",icon:x=a.createElement(l.A,null),showCancel:h=!0,close:A,onConfirm:k,onCancel:C,onPopupClick:j}=e,{getPrefixCls:S}=a.useContext(c.QO),[_]=(0,y.A)("Popconfirm",v.A.Popconfirm),O=(0,g.b)(o),T=(0,g.b)(s);return a.createElement("div",{className:"".concat(n,"-inner-content"),onClick:j},a.createElement("div",{className:"".concat(n,"-message")},x&&a.createElement("span",{className:"".concat(n,"-message-icon")},x),a.createElement("div",{className:"".concat(n,"-message-text")},O&&a.createElement("div",{className:i()("".concat(n,"-title"))},O),T&&a.createElement("div",{className:"".concat(n,"-description")},T))),a.createElement("div",{className:"".concat(n,"-buttons")},h&&a.createElement(m.Ay,Object.assign({onClick:C,size:"small"},r),d||(null===_||void 0===_?void 0:_.cancelText)),a.createElement(u.A,{buttonProps:Object.assign(Object.assign({size:"small"},(0,p.DU)(b)),t),actionFn:k,close:A,prefixCls:S("btn"),quitOnNullishReturnValue:!0,emitEvent:!0},f||(null===_||void 0===_?void 0:_.okText))))},k=e=>{const{prefixCls:n,placement:t,className:l,style:r}=e,o=h(e,["prefixCls","placement","className","style"]),{getPrefixCls:s}=a.useContext(c.QO),d=s("popconfirm",n),[u]=x(d);return u(a.createElement(f.Ay,{placement:t,className:i()(d,l),style:r,content:a.createElement(A,Object.assign({prefixCls:d},o))}))};var C=function(e,n){var t={};for(var a in e)Object.prototype.hasOwnProperty.call(e,a)&&n.indexOf(a)<0&&(t[a]=e[a]);if(null!=e&&"function"===typeof Object.getOwnPropertySymbols){var l=0;for(a=Object.getOwnPropertySymbols(e);l<a.length;l++)n.indexOf(a[l])<0&&Object.prototype.propertyIsEnumerable.call(e,a[l])&&(t[a[l]]=e[a[l]])}return t};const j=a.forwardRef(((e,n)=>{var t,r;const{prefixCls:u,placement:g="top",trigger:m="click",okType:p="primary",icon:y=a.createElement(l.A,null),children:v,overlayClassName:f,onOpenChange:b,onVisibleChange:h}=e,k=C(e,["prefixCls","placement","trigger","okType","icon","children","overlayClassName","onOpenChange","onVisibleChange"]),{getPrefixCls:j}=a.useContext(c.QO),[S,_]=(0,o.A)(!1,{value:null!==(t=e.open)&&void 0!==t?t:e.visible,defaultValue:null!==(r=e.defaultOpen)&&void 0!==r?r:e.defaultVisible}),O=(e,n)=>{_(e,!0),null===h||void 0===h||h(e),null===b||void 0===b||b(e,n)},T=j("popconfirm",u),I=i()(T,f),[K]=x(T);return K(a.createElement(d.A,Object.assign({},(0,s.A)(k,["title"]),{trigger:m,placement:g,onOpenChange:(n,t)=>{const{disabled:a=!1}=e;a||O(n,t)},open:S,ref:n,overlayClassName:I,content:a.createElement(A,Object.assign({okType:p,icon:y},e,{prefixCls:T,close:e=>{O(!1,e)},onConfirm:n=>{var t;return null===(t=e.onConfirm)||void 0===t?void 0:t.call(void 0,n)},onCancel:n=>{var t;O(!1,n),null===(t=e.onCancel)||void 0===t||t.call(void 0,n)}})),"data-popover-inject":!0}),v))}));j._InternalPanelDoNotUseOrYouWillBeFired=k;const S=j}}]);
//# sourceMappingURL=1724.70927fd6.chunk.js.map