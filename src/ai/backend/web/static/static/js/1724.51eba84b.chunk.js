"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[1724],{5621:(e,n,a)=>{a.d(n,{A:()=>d});var t=a(29871),l=a(48713),i=a(45901),r=a.n(i),s=a(76998),o=a(23446);const d=e=>{let n,{values:a=[]}=e;return 0===a.length?null:(n=a[0]&&("string"===typeof a[0]||s.isValidElement(a[0]))?a.map((e=>({label:e,color:"blue"}))):a,(0,o.jsx)(t.A,{direction:"row",children:r().map(n,((e,a)=>(0,o.jsx)(l.A,{style:r().last(n)===e?void 0:{margin:0,marginRight:-1},color:e.color,children:e.label},a)))}))}},55256:(e,n,a)=>{a.d(n,{Ay:()=>A,Kk:()=>p,p3:()=>v,sT:()=>m,vB:()=>g});var t=a(83468),l=a(5621),i=a(29871),r=a(48713),s=a(45901),o=a.n(s),d=a(76998),u=a(23446);const c=e=>{let{image:n,...a}=e;n=n||"";const[,{getImageAliasName:i,getBaseVersion:r,tagAlias:s}]=(0,t.Gj)();return(0,u.jsx)(l.A,{values:[{label:s(i(n)),color:"blue"},{label:r(n),color:"green"}],...a})},g=e=>{let{image:n,...a}=e;n=n||"";const[,{getBaseVersion:l,tagAlias:i}]=(0,t.Gj)();return(0,u.jsx)(r.A,{color:"green",...a,children:i(l(n))})},m=e=>{let{image:n,...a}=e;n=n||"";const[,{getBaseImage:l,tagAlias:i}]=(0,t.Gj)();return(0,u.jsx)(r.A,{color:"green",...a,children:i(l(n))})},y=e=>{let{image:n,...a}=e;n=n||"";const[,{getArchitecture:l,tagAlias:i}]=(0,t.Gj)();return(0,u.jsx)(r.A,{color:"green",...a,children:i(l(n))})},p=e=>{let{image:n,...a}=e;n=n||"";const[,{getImageLang:l,tagAlias:i}]=(0,t.Gj)();return(0,u.jsx)(r.A,{color:"green",...a,children:i(l(n))})},v=e=>{let{image:n,labels:a,...s}=e;n=n||"",a=a||[];const[,{getFilteredRequirementsTags:d,getCustomTag:c,tagAlias:g}]=(0,t.Gj)();return(0,u.jsxs)(i.A,{children:[o().map(d(n),((e,n)=>(0,u.jsx)(r.A,{color:"blue",...s,children:g(e||"")},n))),(0,u.jsx)(l.A,{color:"cyan",values:[{label:"Customized",color:"cyan"},{label:c(a),color:"cyan"}],...s})]})},k=(e,n)=>{let{image:a,style:t={}}=e;return a=a||"",(0,u.jsxs)(u.Fragment,{children:[(0,u.jsx)(c,{image:a}),(0,u.jsx)(m,{image:a}),(0,u.jsx)(y,{image:a})]})},A=d.memo(k)},34680:(e,n,a)=>{a.d(n,{A:()=>y});var t=a(25339),l=a(62863),i=a(50840),r=a(65080),s=a(36209),o=a(87627),d=a(45901),u=a.n(d),c=a(76998),g=a(77678),m=a(23446);const y=e=>{let{open:n,onRequestClose:a,columns:d,displayedColumnKeys:y,...p}=e;const v=(0,c.useRef)(null),{t:k}=(0,g.Bd)(),{token:A}=i.A.useToken(),h=d.map((e=>{return"string"===typeof e.title?{label:e.title,value:u().toString(e.key)}:"object"===typeof e.title&&"props"in e.title?{label:(n=e.title,c.Children.map(n.props.children,(e=>{if("string"===typeof e)return e}))),value:u().toString(e.key)}:{label:void 0,value:u().toString(e.key)};var n}));return(0,m.jsx)(t.A,{title:k("table.SettingTable"),open:n,destroyOnClose:!0,centered:!0,onOk:()=>{var e;null===(e=v.current)||void 0===e||e.validateFields().then((e=>{a(e)})).catch((()=>{}))},onCancel:()=>{a()},...p,children:(0,m.jsxs)(r.A,{ref:v,preserve:!1,initialValues:{selectedColumnKeys:y||h.map((e=>e.value))},layout:"vertical",children:[(0,m.jsx)(r.A.Item,{name:"searchInput",label:k("table.SelectColumnToDisplay"),style:{marginBottom:0},children:(0,m.jsx)(s.A,{prefix:(0,m.jsx)(l.A,{}),style:{marginBottom:A.marginSM},placeholder:k("table.SearchTableColumn")})}),(0,m.jsx)(r.A.Item,{noStyle:!0,shouldUpdate:(e,n)=>e.searchInput!==n.searchInput,children:e=>{let{getFieldValue:n}=e;const a=n("searchInput")?u().toLower(n("searchInput")):void 0,t=h.map((e=>u().toLower(u().toString(e.label)).includes(a||"")?e:{...e,style:{display:"none"}}));return(0,m.jsx)(r.A.Item,{name:"selectedColumnKeys",style:{height:220,overflowY:"auto"},children:(0,m.jsx)(o.A.Group,{options:t,style:{flexDirection:"column"}})})}})]})})}},21724:(e,n,a)=>{a.r(n),a.d(n,{default:()=>S});var t,l,i=a(29871),r=a(36009),s=a(55256),o=a(34680),d=a(30032),u=a(83468),c=a(97041),g=a(63718),m=a(44355),y=a(50840),p=a(78969),v=a(24128),k=a(59065),A=a(6932),h=a(29475),b=a(14862),x=a(45901),j=a.n(x),f=a(76998),_=a(77678),C=a(3606),K=a(23446);const S=e=>{let{children:n}=e;const{t:x}=(0,_.Bd)(),{token:S}=y.A.useToken(),{message:F}=p.A.useApp(),[I,T]=(0,f.useState)(!1),[M]=(0,f.useState)("images"),[w,B]=(0,f.useTransition)(),[L,D]=(0,u.Tw)("initial-fetch"),[P,E]=(0,f.useState)(),[,{getNamespace:V,getImageLang:R,getBaseVersion:z,getBaseImage:q,getCustomTag:G,getFilteredRequirementsTags:U}]=(0,u.Gj)(),{customized_images:Q}=(0,C.useLazyLoadQuery)(void 0!==t?t:t=a(38867),{},{fetchPolicy:"initial-fetch"===L?"store-and-network":"network-only",fetchKey:L}),[X,N]=(0,C.useMutation)(void 0!==l?l:l=a(60681)),O=[{title:x("environment.Registry"),dataIndex:"registry",key:"registry",sorter:(e,n)=>null!==e&&void 0!==e&&e.registry&&null!==n&&void 0!==n&&n.registry?e.registry.localeCompare(n.registry):0},{title:x("environment.Architecture"),dataIndex:"architecture",key:"architecture",sorter:(e,n)=>null!==e&&void 0!==e&&e.architecture&&null!==n&&void 0!==n&&n.architecture?e.architecture.localeCompare(n.architecture):0},{title:x("environment.Namespace"),key:"namespace",sorter:(e,n)=>{const a=V((0,d.A_)(e)||""),t=V((0,d.A_)(n)||"");return a&&t?a.localeCompare(t):0},render:(e,n)=>(0,K.jsx)("span",{children:V((0,d.A_)(n)||"")})},{title:x("environment.Language"),key:"lang",sorter:(e,n)=>{const a=R((0,d.A_)(e)||""),t=R((0,d.A_)(n)||"");return a&&t?a.localeCompare(t):0},render:(e,n)=>(0,K.jsx)(s.Kk,{image:(0,d.A_)(n)||"",color:"green"})},{title:x("environment.Version"),key:"baseversion",sorter:(e,n)=>{const a=z((0,d.A_)(e)||""),t=z((0,d.A_)(n)||"");return a&&t?a.localeCompare(t):0},render:(e,n)=>(0,K.jsx)(s.vB,{image:(0,d.A_)(n)||"",color:"green"})},{title:x("environment.Base"),key:"baseimage",sorter:(e,n)=>{const a=q((0,d.A_)(e)||""),t=q((0,d.A_)(n)||"");return a&&t?a.localeCompare(t):0},render:(e,n)=>(0,K.jsx)(s.sT,{image:(0,d.A_)(n)||""})},{title:x("environment.Constraint"),key:"constraint",sorter:(e,n)=>{const a=e=>{const n=(0,d.A_)(e)||"",a=j().get(e,"labels",[]);return U(n).join("")+"Customized"+G(a)},t=a(e),l=a(n);return t&&l?t.localeCompare(l):0},render:(e,n)=>(0,K.jsx)(s.p3,{image:(0,d.A_)(n)||"",labels:null===n||void 0===n?void 0:n.labels})},{title:x("environment.Digest"),dataIndex:"digest",key:"digest",sorter:(e,n)=>null!==e&&void 0!==e&&e.digest&&null!==n&&void 0!==n&&n.digest?e.digest.localeCompare(n.digest):0},{title:x("general.Control"),key:"control",fixed:"right",render:(e,n)=>(0,K.jsxs)(i.A,{direction:"row",align:"stretch",justify:"center",gap:"xxs",children:[(0,K.jsx)(v.A.Text,{copyable:{text:(0,d.A_)(n)||""},style:{paddingTop:S.paddingXXS,paddingBottom:S.paddingXXS}}),(0,K.jsx)(k.A,{title:x("dialog.ask.DoYouWantToProceed"),description:x("dialog.warning.CannotBeUndone"),okType:"danger",okText:x("button.Delete"),onConfirm:()=>{null!==n&&void 0!==n&&n.id&&(E(n.id+L),X({variables:{id:n.id},onCompleted(e,n){var a;n?F.error(null===(a=n[0])||void 0===a?void 0:a.message):(B((()=>{D()})),F.success(x("environment.CustomizedImageSuccessfullyDeleted")))},onError(e){F.error(null===e||void 0===e?void 0:e.message)}}))},children:(0,K.jsx)(A.Ay,{type:"text",icon:(0,K.jsx)(c.A,{}),danger:!0,loading:P===(null===n||void 0===n?void 0:n.id)+L,disabled:N&&P!==(null===n||void 0===n?void 0:n.id)+L})})]})}],[$,Y]=(0,m.A)("backendaiwebui.MyEnvironmentPage.displayedColumnKeys",{defaultValue:O.map((e=>j().toString(e.key)))});return(0,K.jsxs)(i.A,{direction:"column",align:"stretch",gap:"xs",children:[(0,K.jsx)(i.A,{direction:"column",align:"stretch",children:(0,K.jsx)(h.A,{tabList:[{key:"images",label:x("environment.Images")}],activeTabKey:M,styles:{body:{padding:0,paddingTop:1}},children:(0,K.jsxs)(f.Suspense,{fallback:(0,K.jsx)(r.A,{}),children:[(0,K.jsx)(b.A,{loading:w,columns:O.filter((e=>null===$||void 0===$?void 0:$.includes(j().toString(e.key)))),dataSource:Q,rowKey:"id",scroll:{x:"max-content"},pagination:!1}),(0,K.jsx)(i.A,{justify:"end",style:{padding:S.paddingXXS},children:(0,K.jsx)(A.Ay,{type:"text",icon:(0,K.jsx)(g.A,{}),onClick:()=>{T(!0)}})})]})})}),(0,K.jsx)(o.A,{open:I,onRequestClose:e=>{(null===e||void 0===e?void 0:e.selectedColumnKeys)&&Y(null===e||void 0===e?void 0:e.selectedColumnKeys),T(!I)},columns:O,displayedColumnKeys:$||[]})]})}},60681:(e,n,a)=>{a.r(n),a.d(n,{default:()=>l});const t=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"id"}],n=[{kind:"Variable",name:"image_id",variableName:"id"}],a=[{alias:null,args:null,kind:"ScalarField",name:"ok",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"msg",storageKey:null}],t=[{alias:null,args:n,concreteType:"UntagImageFromRegistry",kind:"LinkedField",name:"untag_image_from_registry",plural:!1,selections:a,storageKey:null},{alias:null,args:n,concreteType:"ForgetImageById",kind:"LinkedField",name:"forget_image_by_id",plural:!1,selections:a,storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"MyEnvironmentPageForgetAndUntagMutation",selections:t,type:"Mutations",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"MyEnvironmentPageForgetAndUntagMutation",selections:t},params:{cacheID:"5b4f7c5bc899b115592fccdc6efe534d",id:null,metadata:{},name:"MyEnvironmentPageForgetAndUntagMutation",operationKind:"mutation",text:"mutation MyEnvironmentPageForgetAndUntagMutation(\n  $id: String!\n) {\n  untag_image_from_registry(image_id: $id) {\n    ok\n    msg\n  }\n  forget_image_by_id(image_id: $id) {\n    ok\n    msg\n  }\n}\n"}}}();t.hash="c32a5d49badf02c6b0693522e8e84c82";const l=t},38867:(e,n,a)=>{a.r(n),a.d(n,{default:()=>l});const t=function(){var e=[{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"customized_images",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"humanized_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"digest",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"supported_accelerators",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"MyEnvironmentPageQuery",selections:e,type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"MyEnvironmentPageQuery",selections:e},params:{cacheID:"c1773ff683a165a627b1084bb7f99dfc",id:null,metadata:{},name:"MyEnvironmentPageQuery",operationKind:"query",text:"query MyEnvironmentPageQuery {\n  customized_images {\n    id\n    name\n    humanized_name\n    tag\n    registry\n    architecture\n    digest\n    labels {\n      key\n      value\n    }\n    supported_accelerators\n  }\n}\n"}}}();t.hash="239a93f593bbc6b5d31bbe53ca71e10d";const l=t}}]);
//# sourceMappingURL=1724.51eba84b.chunk.js.map