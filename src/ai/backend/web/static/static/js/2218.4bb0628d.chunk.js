"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[2218],{77099:(e,n,t)=>{t.r(n),t.d(n,{default:()=>o});const l=function(){var e={defaultValue:null,kind:"LocalArgument",name:"limit"},n={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"projectID"},l=[{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"project",variableName:"projectID"}],o={alias:null,args:null,kind:"ScalarField",name:"total_count",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"endpoint_id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"url",storageKey:null};return{fragment:{argumentDefinitions:[e,n,t],kind:"Fragment",metadata:null,name:"EndpointSelectQuery",selections:[{alias:null,args:l,concreteType:"EndpointList",kind:"LinkedField",name:"endpoint_list",plural:!1,selections:[o,{alias:null,args:null,concreteType:"Endpoint",kind:"LinkedField",name:"items",plural:!0,selections:[i,a,r,{args:null,kind:"FragmentSpread",name:"EndpointLLMChatCard_endpoint"}],storageKey:null}],storageKey:null}],type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[n,e,t],kind:"Operation",name:"EndpointSelectQuery",selections:[{alias:null,args:l,concreteType:"EndpointList",kind:"LinkedField",name:"endpoint_list",plural:!1,selections:[o,{alias:null,args:null,concreteType:"Endpoint",kind:"LinkedField",name:"items",plural:!0,selections:[i,a,r,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"a527832d0e20b466499e844d3bb1cd38",id:null,metadata:{},name:"EndpointSelectQuery",operationKind:"query",text:"query EndpointSelectQuery(\n  $offset: Int!\n  $limit: Int!\n  $projectID: UUID\n) {\n  endpoint_list(offset: $offset, limit: $limit, project: $projectID) {\n    total_count\n    items {\n      name\n      endpoint_id\n      url\n      ...EndpointLLMChatCard_endpoint\n      id\n    }\n  }\n}\n\nfragment EndpointLLMChatCard_endpoint on Endpoint {\n  endpoint_id\n  url\n}\n"}}}();l.hash="9371630d1c6953eebbc69ad5ab6c05cc";const o=l},18096:(e,n,t)=>{t.d(n,{A:()=>oe});var l=t(89130),o=t(45296),i=t(67378),a=t(60822),r=t(64831),s=t(57442),d=t(43373),c=t(73689);const{Compact:u}=o.A,p=e=>{let{style:n,loading:t,autoFocus:l,onStop:o,onSend:p,...m}=e;const g=(0,d.useRef)(null);return(0,d.useEffect)((()=>{l&&g.current&&g.current.focus()}),[l]),(0,c.jsxs)(u,{style:{width:"100%",...n},children:[(0,c.jsx)(i.A,{ref:g,...m,onPressEnter:e=>{t||p&&p()}}),(0,c.jsx)(a.Ay,{htmlType:"button",icon:t?(0,c.jsx)(r.A,{}):(0,c.jsx)(s.A,{}),onClick:()=>{t?o&&o():p&&p()}})]})};var m=t(69056),g=t(89608),y=t.n(g),h=t(56762);const f=e=>{let{models:n,allowCustomModel:t,...l}=e;const{t:o}=(0,h.Bd)();return(0,c.jsx)(m.A,{placeholder:o("chatui.SelectModel"),style:{fontWeight:"normal"},showSearch:!0,options:y().concat(t?[{label:"Custom",value:"custom"}]:[],y().chain(n).groupBy("group").mapValues((e=>y().map(e,(e=>({label:e.label,value:e.name}))))).map(((e,n)=>({label:"undefined"===n?"Others":n,options:e}))).value()),popupMatchSelectWidth:!1,...l})};var v=t(33789),x=t(24914),b=t(10361),C=t(48401);const j=e=>{let{copyable:n,...t}=e;const[l,o]=(0,d.useState)(!1);return(0,d.useEffect)((()=>{if(l){const e=setTimeout((()=>{o(!1)}),2e3);return()=>clearTimeout(e)}}),[l]),(0,c.jsx)(v.A,{title:l?"Copied!":"Copy",open:!!l||void 0,children:(0,c.jsx)(C.CopyToClipboard,{text:(null===n||void 0===n?void 0:n.text)||"",onCopy:async()=>{o(!0)},children:(0,c.jsx)(a.Ay,{icon:l?(0,c.jsx)(x.A,{}):(0,c.jsx)(b.A,{}),...t})})})};var S=t(85690),k=t(55368),A=t(60228),L=t(65246),w=t(87799);const{Text:E}=S.A,T=e=>{let{children:n}=e;return(0,c.jsx)(A.o,{components:{code(e){const{children:n,className:t,node:l,ref:o,...i}=e,a=/language-(\w+)/.exec(t||""),r=String(n).replace(/\n$/,"");return a?(0,c.jsx)(k.A,{title:(0,c.jsx)(E,{style:{fontWeight:"normal"},type:"secondary",children:a[1]}),type:"inner",size:"small",extra:(0,c.jsx)(j,{type:"text",copyable:{text:"s"}}),styles:{body:{padding:0},header:{margin:0}},children:(0,c.jsx)("div",{style:{margin:"-0.5em 0",width:"100%"},children:(0,c.jsx)(M,{ref:o,...i,PreTag:"div",language:a[1],style:w.A,wrapLongLines:!0,wrapLines:!0,children:r})})}):(0,c.jsx)("code",{...i,className:t,children:n})}},children:n})},O=e=>{let{children:n,...t}=e;return(0,c.jsx)(L.A,{...t,children:n})},M=d.memo(O),I=d.memo(T);var P=t(35343),_=t(50868),F=t(60522),z=t(12731),K=t.n(z),D=t(65928),R=t.n(D),B=t(99261),N=t.n(B);K().extend(R()),K().extend(N());const V=e=>{let{extra:n,message:t,placement:o="left",containerStyle:i,enableExtraHover:a,isStreaming:r}=e;const{token:s}=_.A.useToken(),[u,p]=(0,d.useState)(!1),m=(0,P.A)(t.content,{wait:50});return(0,c.jsxs)(l.A,{direction:"left"===o?"row":"row-reverse",justify:"start",align:"baseline",style:{marginLeft:"left"===o?"0":"15%",marginRight:"right"===o?"0":20,...i},gap:"sm",onMouseEnter:()=>p(!0),onMouseLeave:()=>p(!1),children:["user"!==t.role?(0,c.jsx)(F.A,{icon:"\ud83e\udd16",style:{fontSize:s.fontSizeHeading3}}):null,(0,c.jsxs)(l.A,{direction:"column",align:"left"===o?"start":"end",wrap:"wrap",style:{flex:1},gap:"xxs",children:[(0,c.jsx)(l.A,{align:"stretch",direction:"column",style:{borderRadius:s.borderRadius,borderColor:s.colorBorderSecondary,borderWidth:s.lineWidth,padding:"1em",paddingTop:0,paddingBottom:0,backgroundColor:"user"!==t.role?s.colorBgContainer:s.colorBgContainerDisabled,width:"100%"},children:(0,c.jsx)(I,{children:m+(r?"\n\u25cf":"")})}),(0,c.jsx)(l.A,{style:{fontSize:s.fontSizeSM,...a?{opacity:u?1:0,transition:"opacity 0.2s",transitionDelay:u?"0s":"0.2s"}:{}},children:n})]})]})};var $=t(60266),U=t(44828);const Q=e=>{let{autoScroll:n,atBottom:t,lastMessageContent:l,...o}=e;const i=(0,$.E)(o.onScrollToBottom);return(0,d.useEffect)((()=>{t&&n&&(null===i||void 0===i||i("auto"))}),[t,n,l,i]),(0,c.jsx)(a.Ay,{icon:(0,c.jsx)(U.A,{}),shape:"circle",onClick:()=>{i&&i("click")}})};var q=t(12529),H=t(849);const W=e=>{var n;let{messages:t,isStreaming:o}=e;const i=(0,d.useRef)(null),[a,r]=(0,d.useState)(!0),{token:s}=_.A.useToken(),u="undefined"!==typeof window?1.5*window.innerHeight:0;return(0,c.jsxs)(l.A,{direction:"column",align:"stretch",style:{height:"100%",flex:1},children:[(0,c.jsx)(H.aY,{atBottomStateChange:r,atBottomThreshold:60,computeItemKey:(e,n)=>n.id,data:t,followOutput:"auto",initialTopMostItemIndex:(null===t||void 0===t?void 0:t.length)-1,itemContent:(e,n)=>(0,c.jsx)(V,{message:n,placement:"user"===n.role?"right":"left",containerStyle:{paddingLeft:s.paddingMD,paddingRight:s.paddingMD,paddingTop:0===e?s.paddingMD:0,paddingBottom:e===t.length-1?s.paddingMD:0},isStreaming:"user"!==n.role&&o&&e===t.length-1,enableExtraHover:"user"===n.role,extra:"user"!==n.role?(0,c.jsx)(q.Ay,{children:(0,c.jsx)(j,{type:"text",size:"small",copyable:{text:n.content}})}):(0,c.jsx)(q.Ay,{children:null})},n.id),overscan:u,ref:i}),(0,c.jsx)("div",{style:{position:"absolute",right:"50%",transform:"translateX(+50%)",bottom:s.marginSM,opacity:a?0:1,transition:"opacity 0.2s",transitionDelay:a?"0s":"0.2s"},children:(0,c.jsx)(Q,{atBottom:a,autoScroll:o,onScrollToBottom:e=>{const n=i.current;switch(e){case"auto":null===n||void 0===n||n.scrollToIndex({align:"end",behavior:"auto",index:"LAST"});break;case"click":null===n||void 0===n||n.scrollToIndex({align:"end",behavior:"smooth",index:"LAST"})}},lastMessageContent:null===(n=t[t.length-1])||void 0===n?void 0:n.content})})]})};var X=t(29992),Y=t(76166),G=t(64703),J=t(57958),Z=t(52161),ee=t(20267),ne=t(32141),te=t(23702),le=t(39464);const oe=e=>{var n;let{models:t=[],baseURL:o,headers:r,credentials:s,apiKey:u,fetchOnClient:m,allowCustomModel:g,alert:v,leftExtra:x,inputMessage:b,submitKey:C,onInputChange:j,onSubmitChange:S,...A}=e;const[L,w]=(0,Z.A)(A,{valuePropName:"modelId",trigger:"onModelChange",defaultValue:null===t||void 0===t||null===(n=t[0])||void 0===n?void 0:n.id}),E=(0,d.useRef)(null),{messages:T,error:O,input:M,setInput:I,handleInputChange:P,stop:F,isLoading:z,append:K,setMessages:D}=(0,Y.Y_)({api:o,headers:r,credentials:s,body:{modelId:L},streamMode:"stream-data",fetch:(e,n)=>{if(m||"custom"===L){var t,l,i;const e=JSON.parse(null===n||void 0===n?void 0:n.body),a=(0,X.ry)({baseURL:g?null===(t=E.current)||void 0===t?void 0:t.getFieldValue("baseURL"):o,apiKey:(g?null===(l=E.current)||void 0===l?void 0:l.getFieldValue("token"):u)||"dummy"});return(0,ee.gM)({abortSignal:(null===n||void 0===n?void 0:n.signal)||void 0,model:a(g?null===(i=E.current)||void 0===i?void 0:i.getFieldValue("modelId"):L),messages:null===e||void 0===e?void 0:e.messages}).then((e=>e.toAIStreamResponse()))}return fetch(e,n)}}),{token:R}=_.A.useToken(),{t:B}=(0,h.Bd)();(0,d.useEffect)((()=>{y().isUndefined(b)||I(b)}),[b,I]),(0,d.useEffect)((()=>{!y().isUndefined(C)&&M&&K({role:"user",content:M})}),[C]);const N=[{key:"clear",danger:!0,label:B("chatui.DeleteChatHistory"),icon:(0,c.jsx)(G.A,{}),onClick:()=>{D([])}}];return(0,c.jsxs)(k.A,{bordered:!0,extra:[],...A,title:(0,c.jsx)(l.A,{direction:"column",align:"stretch",gap:"sm",children:(0,c.jsxs)(l.A,{direction:"row",gap:"xs",children:[x,(0,c.jsx)(f,{models:t,value:L,onChange:w,allowCustomModel:g}),(0,c.jsx)(ne.A,{menu:{items:N},trigger:["click"],children:(0,c.jsx)(a.Ay,{type:"link",onClick:e=>e.preventDefault(),icon:(0,c.jsx)(J.A,{}),style:{color:R.colorTextSecondary,width:R.sizeMS}})})]})}),style:{height:"100%",width:"100%",display:"flex",flexDirection:"column"},styles:{body:{backgroundColor:R.colorFillQuaternary,borderRadius:0,flex:1,display:"flex",flexDirection:"column",padding:0,height:"50%",position:"relative"},actions:{paddingLeft:R.paddingContentHorizontal,paddingRight:R.paddingContentHorizontal},header:{zIndex:1}},actions:[(0,c.jsx)(p,{autoFocus:!0,value:M,placeholder:"Say something...",onChange:e=>{P(e),j&&j(e.target.value)},loading:z,onStop:()=>{F()},onSend:()=>{M&&(K({role:"user",content:M}),setTimeout((()=>{I("")}),0),S&&S())}})],children:[(0,c.jsx)(l.A,{direction:"row",style:{padding:R.paddingSM,paddingRight:R.paddingContentHorizontalLG,paddingLeft:R.paddingContentHorizontalLG,backgroundColor:R.colorBgContainer,display:g&&"custom"===L?"flex":"none"},children:(0,c.jsxs)(te.A,{ref:E,layout:"horizontal",size:"small",requiredMark:"optional",style:{flex:1},initialValues:{baseURL:o},children:[v?(0,c.jsx)("div",{style:{marginBottom:R.size},children:v}):null,(0,c.jsx)(te.A.Item,{label:"baseURL",name:"baseURL",rules:[{type:"url"},{required:!0}],children:(0,c.jsx)(i.A,{placeholder:"https://domain/v1"})}),(0,c.jsx)(te.A.Item,{label:"Model ID",name:"modelId",rules:[{required:!0}],children:(0,c.jsx)(i.A,{placeholder:"llm-model"})}),(0,c.jsx)(te.A.Item,{label:"Token",name:"token",children:(0,c.jsx)(i.A,{})})]},o)}),y().isEmpty(null===O||void 0===O?void 0:O.responseBody)?null:(0,c.jsx)(le.A,{message:null===O||void 0===O?void 0:O.responseBody,type:"error",showIcon:!0,style:{margin:R.marginSM},closable:!0}),(0,c.jsx)(W,{messages:T,isStreaming:z})]})}},52218:(e,n,t)=>{t.r(n),t.d(n,{default:()=>F});var l,o=t(89130),i=t(60881),a=t(16522),r=t(52161),s=t(69056),d=t(89608),c=t.n(d),u=t(43373),p=t(88522),m=t(73689);const g=e=>{let{fetchKey:n,...o}=e;const{baiPaginationOption:i}=(0,a.w4)({current:1,pageSize:100}),{endpoint_list:d}=(0,p.useLazyLoadQuery)(void 0!==l?l:l=t(77099),{limit:i.limit,offset:i.offset},{fetchKey:n}),[u,g]=(0,r.A)(o);return(0,m.jsx)(s.A,{showSearch:!0,optionFilterProp:"label",...o,options:c().map(null===d||void 0===d?void 0:d.items,(e=>({label:null===e||void 0===e?void 0:e.name,value:null===e||void 0===e?void 0:e.endpoint_id,endpoint:e}))),value:u,onChange:(e,n)=>{var t;g(e,null===(t=c().castArray(n))||void 0===t?void 0:t[0].endpoint)}})};var y,h=t(18096),f=t(67425),v=t(50868),x=t(51548),b=t(60822),C=t(39464),j=t(28742),S=t(27658),k=t(56762);const A=(0,j.eU)(""),L=(0,j.eU)(void 0),w=e=>{var n,l,o,a;let{basePath:r="v1",closable:s,defaultEndpoint:d,fetchKey:j,isSynchronous:w,onRequestClose:E,onModelChange:T,...O}=e;const{t:M}=(0,k.Bd)(),{token:I}=v.A.useToken(),[P,_]=(0,u.useState)(d||null),F=(0,p.useFragment)(void 0!==y?y:y=t(13318),P),[z,K]=(0,u.useState)(F),[D,R]=(0,S.fp)(A),[B,N]=(0,S.fp)(L),{data:V}=(0,i.nj)({queryKey:["models",j,null===F||void 0===F?void 0:F.endpoint_id],queryFn:()=>{var e;return null!==F&&void 0!==F&&F.url?fetch(new URL(r+"/models",null!==(e=null===F||void 0===F?void 0:F.url)&&void 0!==e?e:void 0).toString()).then((e=>e.json())).catch((e=>({data:[]}))):Promise.resolve({data:[]})}}),$=c().map(null===V||void 0===V?void 0:V.data,(e=>({id:e.id,name:e.id}))),U=(0,u.useId)();return(0,m.jsx)(h.A,{...O,baseURL:null!==F&&void 0!==F&&F.url?new URL(r,null!==(n=null===F||void 0===F?void 0:F.url)&&void 0!==n?n:void 0).toString():void 0,models:$,fetchOnClient:!0,leftExtra:(0,m.jsx)(g,{placeholder:M("chatui.SelectEndpoint"),style:{fontWeight:"normal"},fetchKey:j,showSearch:!0,loading:(null===z||void 0===z?void 0:z.endpoint_id)!==(null===F||void 0===F?void 0:F.endpoint_id),onChange:(e,n)=>{K(n),(0,u.startTransition)((()=>{_(n)}))},value:null===F||void 0===F?void 0:F.endpoint_id,popupMatchSelectWidth:!1}),modelId:null!==(l=null===V||void 0===V||null===(o=V.data)||void 0===o||null===(a=o[0])||void 0===a?void 0:a.id)&&void 0!==l?l:"custom",extra:s?(0,m.jsx)(x.A,{title:M("chatui.DeleteChattingSession"),description:M("chatui.DeleteChattingSessionDescription"),onConfirm:()=>{null===E||void 0===E||E()},okText:M("button.Delete"),okButtonProps:{danger:!0},children:(0,m.jsx)(b.Ay,{icon:(0,m.jsx)(f.A,{}),type:"text",style:{color:I.colorIcon}})}):void 0,allowCustomModel:c().isEmpty($),alert:c().isEmpty($)&&(0,m.jsx)(C.A,{type:"warning",showIcon:!0,message:M("chatui.CannotFindModel")}),inputMessage:w?D:void 0,onInputChange:e=>{R(e)},submitKey:(null===B||void 0===B?void 0:B.id)===U||null===B||void 0===B?void 0:B.key,onSubmitChange:()=>{R(""),w&&N({id:U,key:(new Date).toString()})}})};var E,T=t(4342),O=t(54880),M=t(85690),I=t(15480),P=t(55368),_=t(34948);const F=e=>{let{...n}=e;const{token:l}=v.A.useToken(),{t:i}=(0,k.Bd)(),{list:a,remove:r,getKey:s,push:d}=(0,O.A)(["0","1"]),[g,y]=(0,u.useState)(!1),{endpoint_list:h}=(0,p.useLazyLoadQuery)(void 0!==E?E:E=t(91645),{});return(0,m.jsx)(m.Fragment,{children:(0,m.jsxs)(o.A,{direction:"column",align:"stretch",children:[(0,m.jsxs)(o.A,{direction:"row",justify:"between",wrap:"wrap",gap:"xs",style:{padding:l.paddingContentVertical,paddingLeft:l.paddingContentHorizontalSM,paddingRight:l.paddingContentHorizontalSM},children:[(0,m.jsx)(o.A,{direction:"column",align:"start",children:(0,m.jsx)(M.A.Text,{style:{margin:0,padding:0},children:"LLM Playground"})}),(0,m.jsx)(o.A,{direction:"row",gap:"xs",wrap:"wrap",style:{flexShrink:1},children:(0,m.jsxs)(o.A,{gap:"xs",children:[(0,m.jsx)(M.A.Text,{type:"secondary",children:i("chatui.SyncInput")}),(0,m.jsx)(I.A,{value:g,onClick:e=>{y(e)}}),(0,m.jsx)(b.Ay,{onClick:()=>{d((new Date).toString())},icon:(0,m.jsx)(T.A,{})})]})})]}),(0,m.jsx)(o.A,{gap:"xs",style:{margin:l.margin,marginTop:0,overflow:"auto",height:"calc(100vh - 215px)"},align:"stretch",children:c().map(a,((e,n)=>{var t;return(0,m.jsx)(u.Suspense,{fallback:(0,m.jsx)(P.A,{style:{flex:1},children:(0,m.jsx)(_.A,{active:!0})}),children:(0,m.jsx)(w,{defaultEndpoint:(null===h||void 0===h||null===(t=h.items)||void 0===t?void 0:t[0])||void 0,style:{flex:1},onRequestClose:()=>{r(n)},closable:a.length>1,isSynchronous:g},s(n))},s(n))}))})]})})}},13318:(e,n,t)=>{t.r(n),t.d(n,{default:()=>o});const l={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"EndpointLLMChatCard_endpoint",selections:[{alias:null,args:null,kind:"ScalarField",name:"endpoint_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"url",storageKey:null}],type:"Endpoint",abstractKey:null,hash:"d5fbaab35efda649f9f7847ee51028b6"},o=l},91645:(e,n,t)=>{t.r(n),t.d(n,{default:()=>o});const l=function(){var e=[{kind:"Literal",name:"limit",value:1},{kind:"Literal",name:"offset",value:0}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"LLMPlaygroundPageQuery",selections:[{alias:null,args:e,concreteType:"EndpointList",kind:"LinkedField",name:"endpoint_list",plural:!1,selections:[{alias:null,args:null,concreteType:"Endpoint",kind:"LinkedField",name:"items",plural:!0,selections:[{args:null,kind:"FragmentSpread",name:"EndpointLLMChatCard_endpoint"}],storageKey:null}],storageKey:"endpoint_list(limit:1,offset:0)"}],type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"LLMPlaygroundPageQuery",selections:[{alias:null,args:e,concreteType:"EndpointList",kind:"LinkedField",name:"endpoint_list",plural:!1,selections:[{alias:null,args:null,concreteType:"Endpoint",kind:"LinkedField",name:"items",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpoint_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"url",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}],storageKey:"endpoint_list(limit:1,offset:0)"}]},params:{cacheID:"54bc258ef687e79f7de52ce23fdff394",id:null,metadata:{},name:"LLMPlaygroundPageQuery",operationKind:"query",text:"query LLMPlaygroundPageQuery {\n  endpoint_list(limit: 1, offset: 0) {\n    items {\n      ...EndpointLLMChatCard_endpoint\n      id\n    }\n  }\n}\n\nfragment EndpointLLMChatCard_endpoint on Endpoint {\n  endpoint_id\n  url\n}\n"}}}();l.hash="b72a92e9309dc6b18f2a791e535ea05b";const o=l},16522:(e,n,t)=>{t.d(n,{w4:()=>a});var l=t(89608),o=t.n(l),i=t(43373);t(88522),t(12121);const a=e=>{const[n,t]=(0,i.useState)(e);return{baiPaginationOption:{limit:n.pageSize,offset:n.current>1?(n.current-1)*n.pageSize:0},tablePaginationOption:{pageSize:n.pageSize,current:n.current},setTablePaginationOption:e=>{o().isEqual(e,n)||t((n=>({...n,...e})))}}}},52161:(e,n,t)=>{t.d(n,{A:()=>s});var l=t(81949),o=t(43373),i=t(92685),a=t(53591);const r=function(){var e=(0,l.zs)((0,o.useState)({}),2)[1];return(0,o.useCallback)((function(){return e({})}),[])};const s=function(e,n){void 0===e&&(e={}),void 0===n&&(n={});var t=n.defaultValue,s=n.defaultValuePropName,d=void 0===s?"defaultValue":s,c=n.valuePropName,u=void 0===c?"value":c,p=n.trigger,m=void 0===p?"onChange":p,g=e[u],y=e.hasOwnProperty(u),h=(0,o.useMemo)((function(){return y?g:e.hasOwnProperty(d)?e[d]:t}),[]),f=(0,o.useRef)(h);y&&(f.current=g);var v=r();return[f.current,(0,a.A)((function(n){for(var t=[],o=1;o<arguments.length;o++)t[o-1]=arguments[o];var a=(0,i.Tn)(n)?n(f.current):n;y||(f.current=a,v()),e[m]&&e[m].apply(e,(0,l.fX)([a],(0,l.zs)(t),!1))}))]}},51548:(e,n,t)=>{t.d(n,{A:()=>A});var l=t(43373),o=t(67592),i=t(13001),a=t.n(i),r=t(90049),s=t(76633),d=t(67085),c=t(84131),u=t(565),p=t(781),m=t(60822),g=t(44123),y=t(89689),h=t(47272),f=t(83451),v=t(64188);const x=(0,v.OF)("Popconfirm",(e=>(e=>{const{componentCls:n,iconCls:t,antCls:l,zIndexPopup:o,colorText:i,colorWarning:a,marginXXS:r,marginXS:s,fontSize:d,fontWeightStrong:c,colorTextHeading:u}=e;return{[n]:{zIndex:o,[`&${l}-popover`]:{fontSize:d},[`${n}-message`]:{marginBottom:s,display:"flex",flexWrap:"nowrap",alignItems:"start",[`> ${n}-message-icon ${t}`]:{color:a,fontSize:d,lineHeight:1,marginInlineEnd:s},[`${n}-title`]:{fontWeight:c,color:u,"&:only-child":{fontWeight:"normal"}},[`${n}-description`]:{marginTop:r,color:i}},[`${n}-buttons`]:{textAlign:"end",whiteSpace:"nowrap",button:{marginInlineStart:s}}}}})(e)),(e=>{const{zIndexPopupBase:n}=e;return{zIndexPopup:n+60}}),{resetStyle:!1});var b=function(e,n){var t={};for(var l in e)Object.prototype.hasOwnProperty.call(e,l)&&n.indexOf(l)<0&&(t[l]=e[l]);if(null!=e&&"function"===typeof Object.getOwnPropertySymbols){var o=0;for(l=Object.getOwnPropertySymbols(e);o<l.length;o++)n.indexOf(l[o])<0&&Object.prototype.propertyIsEnumerable.call(e,l[o])&&(t[l[o]]=e[l[o]])}return t};const C=e=>{const{prefixCls:n,okButtonProps:t,cancelButtonProps:i,title:a,description:r,cancelText:s,okText:c,okType:f="primary",icon:v=l.createElement(o.A,null),showCancel:x=!0,close:b,onConfirm:C,onCancel:j,onPopupClick:S}=e,{getPrefixCls:k}=l.useContext(d.QO),[A]=(0,y.A)("Popconfirm",h.A.Popconfirm),L=(0,p.b)(a),w=(0,p.b)(r);return l.createElement("div",{className:`${n}-inner-content`,onClick:S},l.createElement("div",{className:`${n}-message`},v&&l.createElement("span",{className:`${n}-message-icon`},v),l.createElement("div",{className:`${n}-message-text`},L&&l.createElement("div",{className:`${n}-title`},L),w&&l.createElement("div",{className:`${n}-description`},w))),l.createElement("div",{className:`${n}-buttons`},x&&l.createElement(m.Ay,Object.assign({onClick:j,size:"small"},i),s||(null===A||void 0===A?void 0:A.cancelText)),l.createElement(u.A,{buttonProps:Object.assign(Object.assign({size:"small"},(0,g.DU)(f)),t),actionFn:C,close:b,prefixCls:k("btn"),quitOnNullishReturnValue:!0,emitEvent:!0},c||(null===A||void 0===A?void 0:A.okText))))},j=e=>{const{prefixCls:n,placement:t,className:o,style:i}=e,r=b(e,["prefixCls","placement","className","style"]),{getPrefixCls:s}=l.useContext(d.QO),c=s("popconfirm",n),[u]=x(c);return u(l.createElement(f.Ay,{placement:t,className:a()(c,o),style:i,content:l.createElement(C,Object.assign({prefixCls:c},r))}))};var S=function(e,n){var t={};for(var l in e)Object.prototype.hasOwnProperty.call(e,l)&&n.indexOf(l)<0&&(t[l]=e[l]);if(null!=e&&"function"===typeof Object.getOwnPropertySymbols){var o=0;for(l=Object.getOwnPropertySymbols(e);o<l.length;o++)n.indexOf(l[o])<0&&Object.prototype.propertyIsEnumerable.call(e,l[o])&&(t[l[o]]=e[l[o]])}return t};const k=l.forwardRef(((e,n)=>{var t,i;const{prefixCls:u,placement:p="top",trigger:m="click",okType:g="primary",icon:y=l.createElement(o.A,null),children:h,overlayClassName:f,onOpenChange:v,onVisibleChange:b}=e,j=S(e,["prefixCls","placement","trigger","okType","icon","children","overlayClassName","onOpenChange","onVisibleChange"]),{getPrefixCls:k}=l.useContext(d.QO),[A,L]=(0,r.A)(!1,{value:null!==(t=e.open)&&void 0!==t?t:e.visible,defaultValue:null!==(i=e.defaultOpen)&&void 0!==i?i:e.defaultVisible}),w=(e,n)=>{L(e,!0),null===b||void 0===b||b(e),null===v||void 0===v||v(e,n)},E=k("popconfirm",u),T=a()(E,f),[O]=x(E);return O(l.createElement(c.A,Object.assign({},(0,s.A)(j,["title"]),{trigger:m,placement:p,onOpenChange:(n,t)=>{const{disabled:l=!1}=e;l||w(n,t)},open:A,ref:n,overlayClassName:T,content:l.createElement(C,Object.assign({okType:g,icon:y},e,{prefixCls:E,close:e=>{w(!1,e)},onConfirm:n=>{var t;return null===(t=e.onConfirm)||void 0===t?void 0:t.call(void 0,n)},onCancel:n=>{var t;w(!1,n),null===(t=e.onCancel)||void 0===t||t.call(void 0,n)}})),"data-popover-inject":!0}),h))}));k._InternalPanelDoNotUseOrYouWillBeFired=j;const A=k}}]);
//# sourceMappingURL=2218.4bb0628d.chunk.js.map