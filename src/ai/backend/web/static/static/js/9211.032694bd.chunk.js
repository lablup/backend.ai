"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[9211],{9211:(e,n,l)=>{l.r(n),l.d(n,{default:()=>f});var t,a=l(51593),i=l(11899),o=l(94126),s=l(45719),r=l(60822),d=l(45679),c=l(11371),u=l(15934),m=l(89608),p=l.n(m),b=(l(43373),l(56762)),g=l(88522),y=l(73689);const f=e=>{let{...n}=e;const{t:m}=(0,b.Bd)(),{value:f,dispatchEvent:h}=(0,s.useWebComponentInfo)();let v;try{v=JSON.parse(f||"")}catch(E){v={open:!1,userEmail:""}}const{open:S,userEmail:$}=v,x=(0,a.CX)(),j=null===x||void 0===x?void 0:x.supports("sudo-session-enabled"),{isTOTPSupported:O,isLoading:k}=(0,i.F4)(),{user:w}=(0,g.useLazyLoadQuery)(void 0!==t?t:t=l(52536),{email:$,isNotSupportSudoSessionEnabled:!j,isTOTPSupported:null!==O&&void 0!==O&&O}),A={xxl:1,xl:1,lg:1,md:1,sm:1,xs:1};return(0,y.jsxs)(o.A,{open:S,onCancel:()=>{h("cancel",null)},centered:!0,title:m("credential.UserDetail"),footer:[(0,y.jsx)(r.Ay,{type:"primary",onClick:()=>{h("cancel",null)},children:m("button.OK")},"ok")],...n,children:[(0,y.jsx)("br",{}),(0,y.jsxs)(d.A,{size:"small",column:A,title:m("credential.Information"),labelStyle:{width:"50%"},children:[(0,y.jsx)(d.A.Item,{label:m("credential.UserID"),children:null===w||void 0===w?void 0:w.email}),(0,y.jsx)(d.A.Item,{label:m("credential.UserName"),children:null===w||void 0===w?void 0:w.username}),(0,y.jsx)(d.A.Item,{label:m("credential.FullName"),children:null===w||void 0===w?void 0:w.full_name}),(0,y.jsx)(d.A.Item,{label:m("credential.MainAccessKey"),children:null===w||void 0===w?void 0:w.main_access_key}),(0,y.jsx)(d.A.Item,{label:m("credential.DescActiveUser"),children:"active"===(null===w||void 0===w?void 0:w.status)?m("button.Yes"):m("button.No")}),(0,y.jsx)(d.A.Item,{label:m("credential.DescRequirePasswordChange"),children:null!==w&&void 0!==w&&w.need_password_change?m("button.Yes"):m("button.No")}),j&&(0,y.jsx)(d.A.Item,{label:m("credential.EnableSudoSession"),children:null!==w&&void 0!==w&&w.sudo_session_enabled?m("button.Yes"):m("button.No")}),O&&(0,y.jsx)(d.A.Item,{label:m("webui.menu.TotpActivated"),children:(0,y.jsx)(c.A,{spinning:k,children:null!==w&&void 0!==w&&w.totp_activated?m("button.Yes"):m("button.No")})})]}),(0,y.jsx)("br",{}),(0,y.jsxs)(d.A,{size:"small",column:A,title:m("credential.Association"),labelStyle:{width:"50%"},children:[(0,y.jsx)(d.A.Item,{label:m("credential.Domain"),children:null===w||void 0===w?void 0:w.domain_name}),(0,y.jsx)(d.A.Item,{label:m("credential.Role"),children:null===w||void 0===w?void 0:w.role})]}),(0,y.jsx)("br",{}),(0,y.jsx)(d.A,{title:m("credential.ProjectAndGroup"),labelStyle:{width:"50%"},children:(0,y.jsx)(d.A.Item,{children:p().map(null===w||void 0===w?void 0:w.groups,(e=>(0,y.jsx)(u.A,{children:null===e||void 0===e?void 0:e.name},null===e||void 0===e?void 0:e.id)))})})]})}},52536:(e,n,l)=>{l.r(n),l.d(n,{default:()=>a});const t=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"email"},{defaultValue:null,kind:"LocalArgument",name:"isNotSupportSudoSessionEnabled"},{defaultValue:null,kind:"LocalArgument",name:"isTOTPSupported"}],n=[{kind:"Variable",name:"email",variableName:"email"}],l={alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"need_password_change",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"full_name",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"description",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"domain_name",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"role",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},u={alias:null,args:null,concreteType:"UserGroup",kind:"LinkedField",name:"groups",plural:!0,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"sudo_session_enabled",storageKey:null},p={condition:"isTOTPSupported",kind:"Condition",passingValue:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"totp_activated",storageKey:null}]},b={alias:null,args:null,kind:"ScalarField",name:"main_access_key",storageKey:null};return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"UserInfoModalQuery",selections:[{alias:null,args:n,concreteType:"User",kind:"LinkedField",name:"user",plural:!1,selections:[l,t,a,i,o,s,r,d,u,m,p,b],storageKey:null}],type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"UserInfoModalQuery",selections:[{alias:null,args:n,concreteType:"User",kind:"LinkedField",name:"user",plural:!1,selections:[l,t,a,i,o,s,r,d,u,m,p,b,c],storageKey:null}]},params:{cacheID:"129326e5b3fef57774f2f8359d108efb",id:null,metadata:{},name:"UserInfoModalQuery",operationKind:"query",text:'query UserInfoModalQuery(\n  $email: String\n  $isNotSupportSudoSessionEnabled: Boolean!\n  $isTOTPSupported: Boolean!\n) {\n  user(email: $email) {\n    email\n    username\n    need_password_change\n    full_name\n    description\n    status\n    domain_name\n    role\n    groups {\n      id\n      name\n    }\n    sudo_session_enabled @skipOnClient(if: $isNotSupportSudoSessionEnabled)\n    totp_activated @include(if: $isTOTPSupported)\n    main_access_key @since(version: "23.09.7")\n    id\n  }\n}\n'}}}();t.hash="e2f5a5bfd435e95cb128afc7a7fbcd46";const a=t},45679:(e,n,l)=>{l.d(n,{A:()=>N});var t=l(43373),a=l(13001),i=l.n(a),o=l(98479),s=l(67085),r=l(19783),d=l(32597);const c={xxl:3,xl:3,lg:3,md:3,sm:2,xs:1},u=t.createContext({});var m=l(92510),p=function(e,n){var l={};for(var t in e)Object.prototype.hasOwnProperty.call(e,t)&&n.indexOf(t)<0&&(l[t]=e[t]);if(null!=e&&"function"===typeof Object.getOwnPropertySymbols){var a=0;for(t=Object.getOwnPropertySymbols(e);a<t.length;a++)n.indexOf(t[a])<0&&Object.prototype.propertyIsEnumerable.call(e,t[a])&&(l[t[a]]=e[t[a]])}return l};function b(e,n,l){const a=t.useMemo((()=>{return n||(e=l,(0,m.A)(e).map((e=>Object.assign(Object.assign({},null===e||void 0===e?void 0:e.props),{key:e.key}))));var e}),[n,l]);return t.useMemo((()=>a.map((n=>{var{span:l}=n,t=p(n,["span"]);return Object.assign(Object.assign({},t),{span:"number"===typeof l?l:(0,o.ko)(e,l)})}))),[a,e])}function g(e,n,l){let t=e,a=!1;return(void 0===l||l>n)&&(t=Object.assign(Object.assign({},e),{span:n}),a=void 0!==l),[t,a]}const y=(e,n)=>{const[l,a]=(0,t.useMemo)((()=>function(e,n){const l=[];let t=[],a=n,i=!1;return e.filter((e=>e)).forEach(((o,s)=>{const r=null===o||void 0===o?void 0:o.span,d=r||1;if(s===e.length-1){const[e,n]=g(o,a,r);return i=i||n,t.push(e),void l.push(t)}if(d<a)a-=d,t.push(o);else{const[e,s]=g(o,a,d);i=i||s,t.push(e),l.push(t),a=n,t=[]}})),[l,i]}(n,e)),[n,e]);return l},f=e=>{let{children:n}=e;return n};function h(e){return void 0!==e&&null!==e}const v=e=>{const{itemPrefixCls:n,component:l,span:a,className:o,style:s,labelStyle:r,contentStyle:d,bordered:c,label:u,content:m,colon:p,type:b}=e,g=l;return c?t.createElement(g,{className:i()({[`${n}-item-label`]:"label"===b,[`${n}-item-content`]:"content"===b},o),style:s,colSpan:a},h(u)&&t.createElement("span",{style:r},u),h(m)&&t.createElement("span",{style:d},m)):t.createElement(g,{className:i()(`${n}-item`,o),style:s,colSpan:a},t.createElement("div",{className:`${n}-item-container`},(u||0===u)&&t.createElement("span",{className:i()(`${n}-item-label`,{[`${n}-item-no-colon`]:!p}),style:r},u),(m||0===m)&&t.createElement("span",{className:i()(`${n}-item-content`),style:d},m)))};function S(e,n,l){let{colon:a,prefixCls:i,bordered:o}=n,{component:s,type:r,showLabel:d,showContent:c,labelStyle:u,contentStyle:m}=l;return e.map(((e,n)=>{let{label:l,children:p,prefixCls:b=i,className:g,style:y,labelStyle:f,contentStyle:h,span:S=1,key:$}=e;return"string"===typeof s?t.createElement(v,{key:`${r}-${$||n}`,className:g,style:y,labelStyle:Object.assign(Object.assign({},u),f),contentStyle:Object.assign(Object.assign({},m),h),span:S,colon:a,component:s,itemPrefixCls:b,bordered:o,label:d?l:null,content:c?p:null,type:r}):[t.createElement(v,{key:`label-${$||n}`,className:g,style:Object.assign(Object.assign(Object.assign({},u),y),f),span:1,colon:a,component:s[0],itemPrefixCls:b,bordered:o,label:l,type:"label"}),t.createElement(v,{key:`content-${$||n}`,className:g,style:Object.assign(Object.assign(Object.assign({},m),y),h),span:2*S-1,component:s[1],itemPrefixCls:b,bordered:o,content:p,type:"content"})]}))}const $=e=>{const n=t.useContext(u),{prefixCls:l,vertical:a,row:i,index:o,bordered:s}=e;return a?t.createElement(t.Fragment,null,t.createElement("tr",{key:`label-${o}`,className:`${l}-row`},S(i,e,Object.assign({component:"th",type:"label",showLabel:!0},n))),t.createElement("tr",{key:`content-${o}`,className:`${l}-row`},S(i,e,Object.assign({component:"td",type:"content",showContent:!0},n)))):t.createElement("tr",{key:o,className:`${l}-row`},S(i,e,Object.assign({component:s?["th","td"]:"td",type:"item",showLabel:!0,showContent:!0},n)))};var x=l(87),j=l(10751),O=l(64188),k=l(8299);const w=e=>{const{componentCls:n,labelBg:l}=e;return{[`&${n}-bordered`]:{[`> ${n}-view`]:{overflow:"hidden",border:`${(0,x.zA)(e.lineWidth)} ${e.lineType} ${e.colorSplit}`,"> table":{tableLayout:"auto"},[`${n}-row`]:{borderBottom:`${(0,x.zA)(e.lineWidth)} ${e.lineType} ${e.colorSplit}`,"&:last-child":{borderBottom:"none"},[`> ${n}-item-label, > ${n}-item-content`]:{padding:`${(0,x.zA)(e.padding)} ${(0,x.zA)(e.paddingLG)}`,borderInlineEnd:`${(0,x.zA)(e.lineWidth)} ${e.lineType} ${e.colorSplit}`,"&:last-child":{borderInlineEnd:"none"}},[`> ${n}-item-label`]:{color:e.colorTextSecondary,backgroundColor:l,"&::after":{display:"none"}}}},[`&${n}-middle`]:{[`${n}-row`]:{[`> ${n}-item-label, > ${n}-item-content`]:{padding:`${(0,x.zA)(e.paddingSM)} ${(0,x.zA)(e.paddingLG)}`}}},[`&${n}-small`]:{[`${n}-row`]:{[`> ${n}-item-label, > ${n}-item-content`]:{padding:`${(0,x.zA)(e.paddingXS)} ${(0,x.zA)(e.padding)}`}}}}}},A=(0,O.OF)("Descriptions",(e=>(e=>{const{componentCls:n,extraColor:l,itemPaddingBottom:t,itemPaddingEnd:a,colonMarginRight:i,colonMarginLeft:o,titleMarginBottom:s}=e;return{[n]:Object.assign(Object.assign(Object.assign({},(0,j.dF)(e)),w(e)),{"&-rtl":{direction:"rtl"},[`${n}-header`]:{display:"flex",alignItems:"center",marginBottom:s},[`${n}-title`]:Object.assign(Object.assign({},j.L9),{flex:"auto",color:e.titleColor,fontWeight:e.fontWeightStrong,fontSize:e.fontSizeLG,lineHeight:e.lineHeightLG}),[`${n}-extra`]:{marginInlineStart:"auto",color:l,fontSize:e.fontSize},[`${n}-view`]:{width:"100%",borderRadius:e.borderRadiusLG,table:{width:"100%",tableLayout:"fixed",borderCollapse:"collapse"}},[`${n}-row`]:{"> th, > td":{paddingBottom:t,paddingInlineEnd:a},"> th:last-child, > td:last-child":{paddingInlineEnd:0},"&:last-child":{borderBottom:"none","> th, > td":{paddingBottom:0}}},[`${n}-item-label`]:{color:e.colorTextTertiary,fontWeight:"normal",fontSize:e.fontSize,lineHeight:e.lineHeight,textAlign:"start","&::after":{content:'":"',position:"relative",top:-.5,marginInline:`${(0,x.zA)(o)} ${(0,x.zA)(i)}`},[`&${n}-item-no-colon::after`]:{content:'""'}},[`${n}-item-no-label`]:{"&::after":{margin:0,content:'""'}},[`${n}-item-content`]:{display:"table-cell",flex:1,color:e.contentColor,fontSize:e.fontSize,lineHeight:e.lineHeight,wordBreak:"break-word",overflowWrap:"break-word"},[`${n}-item`]:{paddingBottom:0,verticalAlign:"top","&-container":{display:"flex",[`${n}-item-label`]:{display:"inline-flex",alignItems:"baseline"},[`${n}-item-content`]:{display:"inline-flex",alignItems:"baseline",minWidth:0}}},"&-middle":{[`${n}-row`]:{"> th, > td":{paddingBottom:e.paddingSM}}},"&-small":{[`${n}-row`]:{"> th, > td":{paddingBottom:e.paddingXS}}}})}})((0,k.oX)(e,{}))),(e=>({labelBg:e.colorFillAlter,titleColor:e.colorText,titleMarginBottom:e.fontSizeSM*e.lineHeightSM,itemPaddingBottom:e.padding,itemPaddingEnd:e.padding,colonMarginRight:e.marginXS,colonMarginLeft:e.marginXXS/2,contentColor:e.colorText,extraColor:e.colorText})));var E=function(e,n){var l={};for(var t in e)Object.prototype.hasOwnProperty.call(e,t)&&n.indexOf(t)<0&&(l[t]=e[t]);if(null!=e&&"function"===typeof Object.getOwnPropertySymbols){var a=0;for(t=Object.getOwnPropertySymbols(e);a<t.length;a++)n.indexOf(t[a])<0&&Object.prototype.propertyIsEnumerable.call(e,t[a])&&(l[t[a]]=e[t[a]])}return l};const C=e=>{const{prefixCls:n,title:l,extra:a,column:m,colon:p=!0,bordered:g,layout:f,children:h,className:v,rootClassName:S,style:x,size:j,labelStyle:O,contentStyle:k,items:w}=e,C=E(e,["prefixCls","title","extra","column","colon","bordered","layout","children","className","rootClassName","style","size","labelStyle","contentStyle","items"]),{getPrefixCls:N,direction:_,descriptions:I}=t.useContext(s.QO),z=N("descriptions",n),T=(0,d.A)(),P=t.useMemo((()=>{var e;return"number"===typeof m?m:null!==(e=(0,o.ko)(T,Object.assign(Object.assign({},c),m)))&&void 0!==e?e:3}),[T,m]),F=b(T,w,h),L=(0,r.A)(j),K=y(P,F),[M,B,U]=A(z),D=t.useMemo((()=>({labelStyle:O,contentStyle:k})),[O,k]);return M(t.createElement(u.Provider,{value:D},t.createElement("div",Object.assign({className:i()(z,null===I||void 0===I?void 0:I.className,{[`${z}-${L}`]:L&&"default"!==L,[`${z}-bordered`]:!!g,[`${z}-rtl`]:"rtl"===_},v,S,B,U),style:Object.assign(Object.assign({},null===I||void 0===I?void 0:I.style),x)},C),(l||a)&&t.createElement("div",{className:`${z}-header`},l&&t.createElement("div",{className:`${z}-title`},l),a&&t.createElement("div",{className:`${z}-extra`},a)),t.createElement("div",{className:`${z}-view`},t.createElement("table",null,t.createElement("tbody",null,K.map(((e,n)=>t.createElement($,{key:n,index:n,colon:p,prefixCls:z,vertical:"vertical"===f,bordered:g,row:e})))))))))};C.Item=f;const N=C}}]);
//# sourceMappingURL=9211.032694bd.chunk.js.map