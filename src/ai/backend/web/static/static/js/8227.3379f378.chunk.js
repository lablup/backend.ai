"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[8227],{8227:(e,t,n)=>{n.d(t,{A:()=>P});var l=n(53350),o=n(62097),i=n.n(o),a=n(23244),s=n(22028),r=n(39334),c=n(38874);const d={xxl:3,xl:3,lg:3,md:3,sm:2,xs:1},b=l.createContext({});var m=n(83531),u=function(e,t){var n={};for(var l in e)Object.prototype.hasOwnProperty.call(e,l)&&t.indexOf(l)<0&&(n[l]=e[l]);if(null!=e&&"function"===typeof Object.getOwnPropertySymbols){var o=0;for(l=Object.getOwnPropertySymbols(e);o<l.length;o++)t.indexOf(l[o])<0&&Object.prototype.propertyIsEnumerable.call(e,l[o])&&(n[l[o]]=e[l[o]])}return n};function v(e,t,n){const o=l.useMemo((()=>{return t||(e=n,(0,m.A)(e).map((e=>Object.assign(Object.assign({},null===e||void 0===e?void 0:e.props),{key:e.key}))));var e}),[t,n]);return l.useMemo((()=>o.map((t=>{var{span:n}=t,l=u(t,["span"]);return"filled"===n?Object.assign(Object.assign({},l),{filled:!0}):Object.assign(Object.assign({},l),{span:"number"===typeof n?n:(0,a.ko)(e,n)})}))),[o,e])}var p=function(e,t){var n={};for(var l in e)Object.prototype.hasOwnProperty.call(e,l)&&t.indexOf(l)<0&&(n[l]=e[l]);if(null!=e&&"function"===typeof Object.getOwnPropertySymbols){var o=0;for(l=Object.getOwnPropertySymbols(e);o<l.length;o++)t.indexOf(l[o])<0&&Object.prototype.propertyIsEnumerable.call(e,l[o])&&(n[l[o]]=e[l[o]])}return n};const g=(e,t)=>{const[n,o]=(0,l.useMemo)((()=>function(e,t){let n=[],l=[],o=!1,i=0;return e.filter((e=>e)).forEach((e=>{const{filled:a}=e,s=p(e,["filled"]);if(a)return l.push(s),n.push(l),l=[],void(i=0);const r=t-i;i+=e.span||1,i>=t?(i>t?(o=!0,l.push(Object.assign(Object.assign({},s),{span:r}))):l.push(s),n.push(l),l=[],i=0):l.push(s)})),l.length>0&&n.push(l),n=n.map((e=>{const n=e.reduce(((e,t)=>e+(t.span||1)),0);if(n<t){const l=e[e.length-1];return l.span=t-(n-(l.span||1)),e}return e})),[n,o]}(t,e)),[t,e]);return n},y=e=>{let{children:t}=e;return t};function O(e){return void 0!==e&&null!==e}const f=e=>{const{itemPrefixCls:t,component:n,span:o,className:a,style:s,labelStyle:r,contentStyle:c,bordered:d,label:m,content:u,colon:v,type:p,styles:g}=e,y=n,f=l.useContext(b),{classNames:j}=f;return d?l.createElement(y,{className:i()({[`${t}-item-label`]:"label"===p,[`${t}-item-content`]:"content"===p,[`${null===j||void 0===j?void 0:j.label}`]:"label"===p,[`${null===j||void 0===j?void 0:j.content}`]:"content"===p},a),style:s,colSpan:o},O(m)&&l.createElement("span",{style:Object.assign(Object.assign({},r),null===g||void 0===g?void 0:g.label)},m),O(u)&&l.createElement("span",{style:Object.assign(Object.assign({},r),null===g||void 0===g?void 0:g.content)},u)):l.createElement(y,{className:i()(`${t}-item`,a),style:s,colSpan:o},l.createElement("div",{className:`${t}-item-container`},(m||0===m)&&l.createElement("span",{className:i()(`${t}-item-label`,null===j||void 0===j?void 0:j.label,{[`${t}-item-no-colon`]:!v}),style:Object.assign(Object.assign({},r),null===g||void 0===g?void 0:g.label)},m),(u||0===u)&&l.createElement("span",{className:i()(`${t}-item-content`,null===j||void 0===j?void 0:j.content),style:Object.assign(Object.assign({},c),null===g||void 0===g?void 0:g.content)},u)))};function j(e,t,n){let{colon:o,prefixCls:i,bordered:a}=t,{component:s,type:r,showLabel:c,showContent:d,labelStyle:b,contentStyle:m,styles:u}=n;return e.map(((e,t)=>{let{label:n,children:v,prefixCls:p=i,className:g,style:y,labelStyle:O,contentStyle:j,span:$=1,key:h,styles:x}=e;return"string"===typeof s?l.createElement(f,{key:`${r}-${h||t}`,className:g,style:y,styles:{label:Object.assign(Object.assign(Object.assign(Object.assign({},b),null===u||void 0===u?void 0:u.label),O),null===x||void 0===x?void 0:x.label),content:Object.assign(Object.assign(Object.assign(Object.assign({},m),null===u||void 0===u?void 0:u.content),j),null===x||void 0===x?void 0:x.content)},span:$,colon:o,component:s,itemPrefixCls:p,bordered:a,label:c?n:null,content:d?v:null,type:r}):[l.createElement(f,{key:`label-${h||t}`,className:g,style:Object.assign(Object.assign(Object.assign(Object.assign(Object.assign({},b),null===u||void 0===u?void 0:u.label),y),O),null===x||void 0===x?void 0:x.label),span:1,colon:o,component:s[0],itemPrefixCls:p,bordered:a,label:n,type:"label"}),l.createElement(f,{key:`content-${h||t}`,className:g,style:Object.assign(Object.assign(Object.assign(Object.assign(Object.assign({},m),null===u||void 0===u?void 0:u.content),y),j),null===x||void 0===x?void 0:x.content),span:2*$-1,component:s[1],itemPrefixCls:p,bordered:a,content:v,type:"content"})]}))}const $=e=>{const t=l.useContext(b),{prefixCls:n,vertical:o,row:i,index:a,bordered:s}=e;return o?l.createElement(l.Fragment,null,l.createElement("tr",{key:`label-${a}`,className:`${n}-row`},j(i,e,Object.assign({component:"th",type:"label",showLabel:!0},t))),l.createElement("tr",{key:`content-${a}`,className:`${n}-row`},j(i,e,Object.assign({component:"td",type:"content",showContent:!0},t)))):l.createElement("tr",{key:a,className:`${n}-row`},j(i,e,Object.assign({component:s?["th","td"]:"td",type:"item",showLabel:!0,showContent:!0},t)))};var h=n(68049),x=n(92778),S=n(14275),w=n(37453);const E=e=>{const{componentCls:t,labelBg:n}=e;return{[`&${t}-bordered`]:{[`> ${t}-view`]:{border:`${(0,h.unit)(e.lineWidth)} ${e.lineType} ${e.colorSplit}`,"> table":{tableLayout:"auto"},[`${t}-row`]:{borderBottom:`${(0,h.unit)(e.lineWidth)} ${e.lineType} ${e.colorSplit}`,"&:last-child":{borderBottom:"none"},[`> ${t}-item-label, > ${t}-item-content`]:{padding:`${(0,h.unit)(e.padding)} ${(0,h.unit)(e.paddingLG)}`,borderInlineEnd:`${(0,h.unit)(e.lineWidth)} ${e.lineType} ${e.colorSplit}`,"&:last-child":{borderInlineEnd:"none"}},[`> ${t}-item-label`]:{color:e.colorTextSecondary,backgroundColor:n,"&::after":{display:"none"}}}},[`&${t}-middle`]:{[`${t}-row`]:{[`> ${t}-item-label, > ${t}-item-content`]:{padding:`${(0,h.unit)(e.paddingSM)} ${(0,h.unit)(e.paddingLG)}`}}},[`&${t}-small`]:{[`${t}-row`]:{[`> ${t}-item-label, > ${t}-item-content`]:{padding:`${(0,h.unit)(e.paddingXS)} ${(0,h.unit)(e.padding)}`}}}}}},N=(0,S.OF)("Descriptions",(e=>(e=>{const{componentCls:t,extraColor:n,itemPaddingBottom:l,itemPaddingEnd:o,colonMarginRight:i,colonMarginLeft:a,titleMarginBottom:s}=e;return{[t]:Object.assign(Object.assign(Object.assign({},(0,x.dF)(e)),E(e)),{"&-rtl":{direction:"rtl"},[`${t}-header`]:{display:"flex",alignItems:"center",marginBottom:s},[`${t}-title`]:Object.assign(Object.assign({},x.L9),{flex:"auto",color:e.titleColor,fontWeight:e.fontWeightStrong,fontSize:e.fontSizeLG,lineHeight:e.lineHeightLG}),[`${t}-extra`]:{marginInlineStart:"auto",color:n,fontSize:e.fontSize},[`${t}-view`]:{width:"100%",borderRadius:e.borderRadiusLG,table:{width:"100%",tableLayout:"fixed",borderCollapse:"collapse"}},[`${t}-row`]:{"> th, > td":{paddingBottom:l,paddingInlineEnd:o},"> th:last-child, > td:last-child":{paddingInlineEnd:0},"&:last-child":{borderBottom:"none","> th, > td":{paddingBottom:0}}},[`${t}-item-label`]:{color:e.colorTextTertiary,fontWeight:"normal",fontSize:e.fontSize,lineHeight:e.lineHeight,textAlign:"start","&::after":{content:'":"',position:"relative",top:-.5,marginInline:`${(0,h.unit)(a)} ${(0,h.unit)(i)}`},[`&${t}-item-no-colon::after`]:{content:'""'}},[`${t}-item-no-label`]:{"&::after":{margin:0,content:'""'}},[`${t}-item-content`]:{display:"table-cell",flex:1,color:e.contentColor,fontSize:e.fontSize,lineHeight:e.lineHeight,wordBreak:"break-word",overflowWrap:"break-word"},[`${t}-item`]:{paddingBottom:0,verticalAlign:"top","&-container":{display:"flex",[`${t}-item-label`]:{display:"inline-flex",alignItems:"baseline"},[`${t}-item-content`]:{display:"inline-flex",alignItems:"baseline",minWidth:"1em"}}},"&-middle":{[`${t}-row`]:{"> th, > td":{paddingBottom:e.paddingSM}}},"&-small":{[`${t}-row`]:{"> th, > td":{paddingBottom:e.paddingXS}}}})}})((0,w.mergeToken)(e,{}))),(e=>({labelBg:e.colorFillAlter,titleColor:e.colorText,titleMarginBottom:e.fontSizeSM*e.lineHeightSM,itemPaddingBottom:e.padding,itemPaddingEnd:e.padding,colonMarginRight:e.marginXS,colonMarginLeft:e.marginXXS/2,contentColor:e.colorText,extraColor:e.colorText})));var C=function(e,t){var n={};for(var l in e)Object.prototype.hasOwnProperty.call(e,l)&&t.indexOf(l)<0&&(n[l]=e[l]);if(null!=e&&"function"===typeof Object.getOwnPropertySymbols){var o=0;for(l=Object.getOwnPropertySymbols(e);o<l.length;o++)t.indexOf(l[o])<0&&Object.prototype.propertyIsEnumerable.call(e,l[o])&&(n[l[o]]=e[l[o]])}return n};const k=e=>{var t,n,o,m,u,p,y,O;const{prefixCls:f,title:j,extra:h,column:x,colon:S=!0,bordered:w,layout:E,children:k,className:P,rootClassName:B,style:M,size:I,labelStyle:L,contentStyle:z,styles:T,items:W,classNames:A}=e,H=C(e,["prefixCls","title","extra","column","colon","bordered","layout","children","className","rootClassName","style","size","labelStyle","contentStyle","styles","items","classNames"]),{getPrefixCls:_,direction:G,descriptions:X}=l.useContext(s.QO),F=_("descriptions",f),R=(0,c.A)();const D=l.useMemo((()=>{var e;return"number"===typeof x?x:null!==(e=(0,a.ko)(R,Object.assign(Object.assign({},d),x)))&&void 0!==e?e:3}),[R,x]),Q=v(R,W,k),q=(0,r.A)(I),J=g(D,Q),[K,U,V]=N(F),Y=l.useMemo((()=>{var e,t,n,l;return{labelStyle:L,contentStyle:z,styles:{content:Object.assign(Object.assign({},null===(e=null===X||void 0===X?void 0:X.styles)||void 0===e?void 0:e.content),null===T||void 0===T?void 0:T.content),label:Object.assign(Object.assign({},null===(t=null===X||void 0===X?void 0:X.styles)||void 0===t?void 0:t.label),null===T||void 0===T?void 0:T.label)},classNames:{label:i()(null===(n=null===X||void 0===X?void 0:X.classNames)||void 0===n?void 0:n.label,null===A||void 0===A?void 0:A.label),content:i()(null===(l=null===X||void 0===X?void 0:X.classNames)||void 0===l?void 0:l.content,null===A||void 0===A?void 0:A.content)}}}),[L,z,T,A,X]);return K(l.createElement(b.Provider,{value:Y},l.createElement("div",Object.assign({className:i()(F,null===X||void 0===X?void 0:X.className,null===(t=null===X||void 0===X?void 0:X.classNames)||void 0===t?void 0:t.root,null===A||void 0===A?void 0:A.root,{[`${F}-${q}`]:q&&"default"!==q,[`${F}-bordered`]:!!w,[`${F}-rtl`]:"rtl"===G},P,B,U,V),style:Object.assign(Object.assign(Object.assign(Object.assign({},null===X||void 0===X?void 0:X.style),null===(n=null===X||void 0===X?void 0:X.styles)||void 0===n?void 0:n.root),null===T||void 0===T?void 0:T.root),M)},H),(j||h)&&l.createElement("div",{className:i()(`${F}-header`,null===(o=null===X||void 0===X?void 0:X.classNames)||void 0===o?void 0:o.header,null===A||void 0===A?void 0:A.header),style:Object.assign(Object.assign({},null===(m=null===X||void 0===X?void 0:X.styles)||void 0===m?void 0:m.header),null===T||void 0===T?void 0:T.header)},j&&l.createElement("div",{className:i()(`${F}-title`,null===(u=null===X||void 0===X?void 0:X.classNames)||void 0===u?void 0:u.title,null===A||void 0===A?void 0:A.title),style:Object.assign(Object.assign({},null===(p=null===X||void 0===X?void 0:X.styles)||void 0===p?void 0:p.title),null===T||void 0===T?void 0:T.title)},j),h&&l.createElement("div",{className:i()(`${F}-extra`,null===(y=null===X||void 0===X?void 0:X.classNames)||void 0===y?void 0:y.extra,null===A||void 0===A?void 0:A.extra),style:Object.assign(Object.assign({},null===(O=null===X||void 0===X?void 0:X.styles)||void 0===O?void 0:O.extra),null===T||void 0===T?void 0:T.extra)},h)),l.createElement("div",{className:`${F}-view`},l.createElement("table",null,l.createElement("tbody",null,J.map(((e,t)=>l.createElement($,{key:t,index:t,colon:S,prefixCls:F,vertical:"vertical"===E,bordered:w,row:e})))))))))};k.Item=y;const P=k}}]);
//# sourceMappingURL=8227.3379f378.chunk.js.map