"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[5405],{94642:(e,t,n)=>{n.d(t,{A:()=>s});var l=n(40991),o=n(55093);const a={icon:{tag:"svg",attrs:{viewBox:"64 64 896 896",focusable:"false"},children:[{tag:"path",attrs:{d:"M880 836H144c-17.7 0-32 14.3-32 32v36c0 4.4 3.6 8 8 8h784c4.4 0 8-3.6 8-8v-36c0-17.7-14.3-32-32-32zm-622.3-84c2 0 4-.2 6-.5L431.9 722c2-.4 3.9-1.3 5.3-2.8l423.9-423.9a9.96 9.96 0 000-14.1L694.9 114.9c-1.9-1.9-4.4-2.9-7.1-2.9s-5.2 1-7.1 2.9L256.8 538.8c-1.5 1.5-2.4 3.3-2.8 5.3l-29.5 168.2a33.5 33.5 0 009.4 29.8c6.6 6.4 14.9 9.9 23.8 9.9z"}}]},name:"edit",theme:"filled"};var r=n(36462),i=function(e,t){return o.createElement(r.A,(0,l.A)({},e,{ref:t,icon:a}))};const s=o.forwardRef(i)},76082:(e,t,n)=>{n.d(t,{A:()=>k});var l=n(55093),o=n(62097),a=n.n(o),r=n(22631),i=n(19541),s=n(41871),c=n(73533);const d={xxl:3,xl:3,lg:3,md:3,sm:2,xs:1},m=l.createContext({});var p=n(62950),b=function(e,t){var n={};for(var l in e)Object.prototype.hasOwnProperty.call(e,l)&&t.indexOf(l)<0&&(n[l]=e[l]);if(null!=e&&"function"===typeof Object.getOwnPropertySymbols){var o=0;for(l=Object.getOwnPropertySymbols(e);o<l.length;o++)t.indexOf(l[o])<0&&Object.prototype.propertyIsEnumerable.call(e,l[o])&&(n[l[o]]=e[l[o]])}return n};function g(e,t,n){const o=l.useMemo((()=>{return t||(e=n,(0,p.A)(e).map((e=>Object.assign(Object.assign({},null===e||void 0===e?void 0:e.props),{key:e.key}))));var e}),[t,n]);return l.useMemo((()=>o.map((t=>{var{span:n}=t,l=b(t,["span"]);return"filled"===n?Object.assign(Object.assign({},l),{filled:!0}):Object.assign(Object.assign({},l),{span:"number"===typeof n?n:(0,r.ko)(e,n)})}))),[o,e])}var u=function(e,t){var n={};for(var l in e)Object.prototype.hasOwnProperty.call(e,l)&&t.indexOf(l)<0&&(n[l]=e[l]);if(null!=e&&"function"===typeof Object.getOwnPropertySymbols){var o=0;for(l=Object.getOwnPropertySymbols(e);o<l.length;o++)t.indexOf(l[o])<0&&Object.prototype.propertyIsEnumerable.call(e,l[o])&&(n[l[o]]=e[l[o]])}return n};const f=(e,t)=>{const[n,o]=(0,l.useMemo)((()=>function(e,t){let n=[],l=[],o=!1,a=0;return e.filter((e=>e)).forEach((e=>{const{filled:r}=e,i=u(e,["filled"]);if(r)return l.push(i),n.push(l),l=[],void(a=0);const s=t-a;a+=e.span||1,a>=t?(a>t?(o=!0,l.push(Object.assign(Object.assign({},i),{span:s}))):l.push(i),n.push(l),l=[],a=0):l.push(i)})),l.length>0&&n.push(l),n=n.map((e=>{const n=e.reduce(((e,t)=>e+(t.span||1)),0);return n<t?(e[e.length-1].span=t-n+1,e):e})),[n,o]}(t,e)),[t,e]);return n},y=e=>{let{children:t}=e;return t};function O(e){return void 0!==e&&null!==e}const v=e=>{const{itemPrefixCls:t,component:n,span:o,className:r,style:i,labelStyle:s,contentStyle:c,bordered:d,label:m,content:p,colon:b,type:g}=e,u=n;return d?l.createElement(u,{className:a()({[`${t}-item-label`]:"label"===g,[`${t}-item-content`]:"content"===g},r),style:i,colSpan:o},O(m)&&l.createElement("span",{style:s},m),O(p)&&l.createElement("span",{style:c},p)):l.createElement(u,{className:a()(`${t}-item`,r),style:i,colSpan:o},l.createElement("div",{className:`${t}-item-container`},(m||0===m)&&l.createElement("span",{className:a()(`${t}-item-label`,{[`${t}-item-no-colon`]:!b}),style:s},m),(p||0===p)&&l.createElement("span",{className:a()(`${t}-item-content`),style:c},p)))};function h(e,t,n){let{colon:o,prefixCls:a,bordered:r}=t,{component:i,type:s,showLabel:c,showContent:d,labelStyle:m,contentStyle:p}=n;return e.map(((e,t)=>{let{label:n,children:b,prefixCls:g=a,className:u,style:f,labelStyle:y,contentStyle:O,span:h=1,key:$}=e;return"string"===typeof i?l.createElement(v,{key:`${s}-${$||t}`,className:u,style:f,labelStyle:Object.assign(Object.assign({},m),y),contentStyle:Object.assign(Object.assign({},p),O),span:h,colon:o,component:i,itemPrefixCls:g,bordered:r,label:c?n:null,content:d?b:null,type:s}):[l.createElement(v,{key:`label-${$||t}`,className:u,style:Object.assign(Object.assign(Object.assign({},m),f),y),span:1,colon:o,component:i[0],itemPrefixCls:g,bordered:r,label:n,type:"label"}),l.createElement(v,{key:`content-${$||t}`,className:u,style:Object.assign(Object.assign(Object.assign({},p),f),O),span:2*h-1,component:i[1],itemPrefixCls:g,bordered:r,content:b,type:"content"})]}))}const $=e=>{const t=l.useContext(m),{prefixCls:n,vertical:o,row:a,index:r,bordered:i}=e;return o?l.createElement(l.Fragment,null,l.createElement("tr",{key:`label-${r}`,className:`${n}-row`},h(a,e,Object.assign({component:"th",type:"label",showLabel:!0},t))),l.createElement("tr",{key:`content-${r}`,className:`${n}-row`},h(a,e,Object.assign({component:"td",type:"content",showContent:!0},t)))):l.createElement("tr",{key:r,className:`${n}-row`},h(a,e,Object.assign({component:i?["th","td"]:"td",type:"item",showLabel:!0,showContent:!0},t)))};var x=n(15103),C=n(28071),j=n(8836),S=n(58670);const E=e=>{const{componentCls:t,labelBg:n}=e;return{[`&${t}-bordered`]:{[`> ${t}-view`]:{border:`${(0,x.zA)(e.lineWidth)} ${e.lineType} ${e.colorSplit}`,"> table":{tableLayout:"auto"},[`${t}-row`]:{borderBottom:`${(0,x.zA)(e.lineWidth)} ${e.lineType} ${e.colorSplit}`,"&:last-child":{borderBottom:"none"},[`> ${t}-item-label, > ${t}-item-content`]:{padding:`${(0,x.zA)(e.padding)} ${(0,x.zA)(e.paddingLG)}`,borderInlineEnd:`${(0,x.zA)(e.lineWidth)} ${e.lineType} ${e.colorSplit}`,"&:last-child":{borderInlineEnd:"none"}},[`> ${t}-item-label`]:{color:e.colorTextSecondary,backgroundColor:n,"&::after":{display:"none"}}}},[`&${t}-middle`]:{[`${t}-row`]:{[`> ${t}-item-label, > ${t}-item-content`]:{padding:`${(0,x.zA)(e.paddingSM)} ${(0,x.zA)(e.paddingLG)}`}}},[`&${t}-small`]:{[`${t}-row`]:{[`> ${t}-item-label, > ${t}-item-content`]:{padding:`${(0,x.zA)(e.paddingXS)} ${(0,x.zA)(e.padding)}`}}}}}},w=(0,j.OF)("Descriptions",(e=>(e=>{const{componentCls:t,extraColor:n,itemPaddingBottom:l,itemPaddingEnd:o,colonMarginRight:a,colonMarginLeft:r,titleMarginBottom:i}=e;return{[t]:Object.assign(Object.assign(Object.assign({},(0,C.dF)(e)),E(e)),{"&-rtl":{direction:"rtl"},[`${t}-header`]:{display:"flex",alignItems:"center",marginBottom:i},[`${t}-title`]:Object.assign(Object.assign({},C.L9),{flex:"auto",color:e.titleColor,fontWeight:e.fontWeightStrong,fontSize:e.fontSizeLG,lineHeight:e.lineHeightLG}),[`${t}-extra`]:{marginInlineStart:"auto",color:n,fontSize:e.fontSize},[`${t}-view`]:{width:"100%",borderRadius:e.borderRadiusLG,table:{width:"100%",tableLayout:"fixed",borderCollapse:"collapse"}},[`${t}-row`]:{"> th, > td":{paddingBottom:l,paddingInlineEnd:o},"> th:last-child, > td:last-child":{paddingInlineEnd:0},"&:last-child":{borderBottom:"none","> th, > td":{paddingBottom:0}}},[`${t}-item-label`]:{color:e.colorTextTertiary,fontWeight:"normal",fontSize:e.fontSize,lineHeight:e.lineHeight,textAlign:"start","&::after":{content:'":"',position:"relative",top:-.5,marginInline:`${(0,x.zA)(r)} ${(0,x.zA)(a)}`},[`&${t}-item-no-colon::after`]:{content:'""'}},[`${t}-item-no-label`]:{"&::after":{margin:0,content:'""'}},[`${t}-item-content`]:{display:"table-cell",flex:1,color:e.contentColor,fontSize:e.fontSize,lineHeight:e.lineHeight,wordBreak:"break-word",overflowWrap:"break-word"},[`${t}-item`]:{paddingBottom:0,verticalAlign:"top","&-container":{display:"flex",[`${t}-item-label`]:{display:"inline-flex",alignItems:"baseline"},[`${t}-item-content`]:{display:"inline-flex",alignItems:"baseline",minWidth:"1em"}}},"&-middle":{[`${t}-row`]:{"> th, > td":{paddingBottom:e.paddingSM}}},"&-small":{[`${t}-row`]:{"> th, > td":{paddingBottom:e.paddingXS}}}})}})((0,S.oX)(e,{}))),(e=>({labelBg:e.colorFillAlter,titleColor:e.colorText,titleMarginBottom:e.fontSizeSM*e.lineHeightSM,itemPaddingBottom:e.padding,itemPaddingEnd:e.padding,colonMarginRight:e.marginXS,colonMarginLeft:e.marginXXS/2,contentColor:e.colorText,extraColor:e.colorText})));var P=function(e,t){var n={};for(var l in e)Object.prototype.hasOwnProperty.call(e,l)&&t.indexOf(l)<0&&(n[l]=e[l]);if(null!=e&&"function"===typeof Object.getOwnPropertySymbols){var o=0;for(l=Object.getOwnPropertySymbols(e);o<l.length;o++)t.indexOf(l[o])<0&&Object.prototype.propertyIsEnumerable.call(e,l[o])&&(n[l[o]]=e[l[o]])}return n};const N=e=>{const{prefixCls:t,title:n,extra:o,column:p,colon:b=!0,bordered:u,layout:y,children:O,className:v,rootClassName:h,style:x,size:C,labelStyle:j,contentStyle:S,items:E}=e,N=P(e,["prefixCls","title","extra","column","colon","bordered","layout","children","className","rootClassName","style","size","labelStyle","contentStyle","items"]),{getPrefixCls:k,direction:z,descriptions:A}=l.useContext(i.QO),I=k("descriptions",t),B=(0,c.A)(),T=l.useMemo((()=>{var e;return"number"===typeof p?p:null!==(e=(0,r.ko)(B,Object.assign(Object.assign({},d),p)))&&void 0!==e?e:3}),[B,p]),L=g(B,E,O),M=(0,s.A)(C),W=f(T,L),[H,X,F]=w(I),R=l.useMemo((()=>({labelStyle:j,contentStyle:S})),[j,S]);return H(l.createElement(m.Provider,{value:R},l.createElement("div",Object.assign({className:a()(I,null===A||void 0===A?void 0:A.className,{[`${I}-${M}`]:M&&"default"!==M,[`${I}-bordered`]:!!u,[`${I}-rtl`]:"rtl"===z},v,h,X,F),style:Object.assign(Object.assign({},null===A||void 0===A?void 0:A.style),x)},N),(n||o)&&l.createElement("div",{className:`${I}-header`},n&&l.createElement("div",{className:`${I}-title`},n),o&&l.createElement("div",{className:`${I}-extra`},o)),l.createElement("div",{className:`${I}-view`},l.createElement("table",null,l.createElement("tbody",null,W.map(((e,t)=>l.createElement($,{key:t,index:t,colon:b,prefixCls:I,vertical:"vertical"===y,bordered:u,row:e})))))))))};N.Item=y;const k=N},25951:(e,t,n)=>{n.d(t,{A:()=>S});var l=n(55093),o=n(86435),a=n(62097),r=n.n(a),i=n(53049),s=n(55393),c=n(19541),d=n(81291),m=n(36861),p=n(87413),b=n(91043),g=n(79427),u=n(67905),f=n(18698),y=n(79827),O=n(8836);const v=(0,O.OF)("Popconfirm",(e=>(e=>{const{componentCls:t,iconCls:n,antCls:l,zIndexPopup:o,colorText:a,colorWarning:r,marginXXS:i,marginXS:s,fontSize:c,fontWeightStrong:d,colorTextHeading:m}=e;return{[t]:{zIndex:o,[`&${l}-popover`]:{fontSize:c},[`${t}-message`]:{marginBottom:s,display:"flex",flexWrap:"nowrap",alignItems:"start",[`> ${t}-message-icon ${n}`]:{color:r,fontSize:c,lineHeight:1,marginInlineEnd:s},[`${t}-title`]:{fontWeight:d,color:m,"&:only-child":{fontWeight:"normal"}},[`${t}-description`]:{marginTop:i,color:a}},[`${t}-buttons`]:{textAlign:"end",whiteSpace:"nowrap",button:{marginInlineStart:s}}}}})(e)),(e=>{const{zIndexPopupBase:t}=e;return{zIndexPopup:t+60}}),{resetStyle:!1});var h=function(e,t){var n={};for(var l in e)Object.prototype.hasOwnProperty.call(e,l)&&t.indexOf(l)<0&&(n[l]=e[l]);if(null!=e&&"function"===typeof Object.getOwnPropertySymbols){var o=0;for(l=Object.getOwnPropertySymbols(e);o<l.length;o++)t.indexOf(l[o])<0&&Object.prototype.propertyIsEnumerable.call(e,l[o])&&(n[l[o]]=e[l[o]])}return n};const $=e=>{const{prefixCls:t,okButtonProps:n,cancelButtonProps:a,title:r,description:i,cancelText:s,okText:d,okType:y="primary",icon:O=l.createElement(o.A,null),showCancel:v=!0,close:h,onConfirm:$,onCancel:x,onPopupClick:C}=e,{getPrefixCls:j}=l.useContext(c.QO),[S]=(0,u.A)("Popconfirm",f.A.Popconfirm),E=(0,p.b)(r),w=(0,p.b)(i);return l.createElement("div",{className:`${t}-inner-content`,onClick:C},l.createElement("div",{className:`${t}-message`},O&&l.createElement("span",{className:`${t}-message-icon`},O),l.createElement("div",{className:`${t}-message-text`},E&&l.createElement("div",{className:`${t}-title`},E),w&&l.createElement("div",{className:`${t}-description`},w))),l.createElement("div",{className:`${t}-buttons`},v&&l.createElement(b.Ay,Object.assign({onClick:x,size:"small"},a),s||(null===S||void 0===S?void 0:S.cancelText)),l.createElement(m.A,{buttonProps:Object.assign(Object.assign({size:"small"},(0,g.DU)(y)),n),actionFn:$,close:h,prefixCls:j("btn"),quitOnNullishReturnValue:!0,emitEvent:!0},d||(null===S||void 0===S?void 0:S.okText))))},x=e=>{const{prefixCls:t,placement:n,className:o,style:a}=e,i=h(e,["prefixCls","placement","className","style"]),{getPrefixCls:s}=l.useContext(c.QO),d=s("popconfirm",t),[m]=v(d);return m(l.createElement(y.Ay,{placement:n,className:r()(d,o),style:a,content:l.createElement($,Object.assign({prefixCls:d},i))}))};var C=function(e,t){var n={};for(var l in e)Object.prototype.hasOwnProperty.call(e,l)&&t.indexOf(l)<0&&(n[l]=e[l]);if(null!=e&&"function"===typeof Object.getOwnPropertySymbols){var o=0;for(l=Object.getOwnPropertySymbols(e);o<l.length;o++)t.indexOf(l[o])<0&&Object.prototype.propertyIsEnumerable.call(e,l[o])&&(n[l[o]]=e[l[o]])}return n};const j=l.forwardRef(((e,t)=>{var n,a;const{prefixCls:m,placement:p="top",trigger:b="click",okType:g="primary",icon:u=l.createElement(o.A,null),children:f,overlayClassName:y,onOpenChange:O,onVisibleChange:h}=e,x=C(e,["prefixCls","placement","trigger","okType","icon","children","overlayClassName","onOpenChange","onVisibleChange"]),{getPrefixCls:j}=l.useContext(c.QO),[S,E]=(0,i.A)(!1,{value:null!==(n=e.open)&&void 0!==n?n:e.visible,defaultValue:null!==(a=e.defaultOpen)&&void 0!==a?a:e.defaultVisible}),w=(e,t)=>{E(e,!0),null===h||void 0===h||h(e),null===O||void 0===O||O(e,t)},P=j("popconfirm",m),N=r()(P,y),[k]=v(P);return k(l.createElement(d.A,Object.assign({},(0,s.A)(x,["title"]),{trigger:b,placement:p,onOpenChange:(t,n)=>{const{disabled:l=!1}=e;l||w(t,n)},open:S,ref:t,overlayClassName:N,content:l.createElement($,Object.assign({okType:g,icon:u},e,{prefixCls:P,close:e=>{w(!1,e)},onConfirm:t=>{var n;return null===(n=e.onConfirm)||void 0===n?void 0:n.call(void 0,t)},onCancel:t=>{var n;w(!1,t),null===(n=e.onCancel)||void 0===n||n.call(void 0,t)}})),"data-popover-inject":!0}),f))}));j._InternalPanelDoNotUseOrYouWillBeFired=x;const S=j}}]);
//# sourceMappingURL=5405.7f2e6eeb.chunk.js.map