/*! For license information please see 9365.c854fda4.chunk.js.LICENSE.txt */
"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[2757,9365],{95762:(e,t,n)=>{n.d(t,{A:()=>c});var r=n(72338),o=n(66596),l=n(12221),i=n(46976),s=n.n(i),a=(n(55093),n(79569));const c=e=>{let{title:t,valueLabel:n,percent:i,width:c,strokeColor:u,labelStyle:d,size:p="small"}=e;const{token:v}=o.A.useToken(),h="small"===p?v.fontSizeSM:"middle"===p?v.fontSize:v.fontSizeLG;return(0,a.jsxs)(r.A,{style:{padding:1,border:`1px solid ${v.colorBorder}`,borderRadius:3,backgroundColor:v.colorBgContainerDisabled,...s().isNumber(c)||s().isString(c)?{width:c}:{flex:1}},direction:"column",align:"stretch",children:[(0,a.jsx)(r.A,{style:{height:"100%",width:`${!i||s().isNaN(i)?0:s().min([i,100])}%`,position:"absolute",left:0,top:0,backgroundColor:null!==u&&void 0!==u?u:v.colorSuccess,opacity:.7,zIndex:0,overflow:"hidden"}}),(0,a.jsxs)(r.A,{direction:"row",justify:"between",children:[(0,a.jsx)(l.A.Text,{style:{fontSize:h,...d},children:t}),(0,a.jsx)(l.A.Text,{style:{fontSize:h,color:s().isNaN(i)||s().isUndefined(i)?v.colorTextDisabled:void 0,...d},children:n})]})]})}},8570:(e,t,n)=>{n.d(t,{Ay:()=>S});n(72375);var r=n(85730),o=n(72338),l=n(72932),i=n(72757),s=n(66596),a=n(171),c=n(47543),u=n(2556),d=n(5975),p=n(1364),v=n(25913),h=n(91043),f=n(46976),y=n.n(f),m=n(55093),g=n(33364),b=n(79569);const x={string:"ilike",boolean:"=="},k={boolean:[{label:"True",value:"true"},{label:"False",value:"false"}],string:void 0},A={boolean:!0};const S=e=>{var t;let{filterProperties:n,value:f,onChange:S,defaultValue:C,loading:j,...w}=e;const[z,_]=(0,r.A)({}),M=(0,m.useRef)(null),[O,T]=(0,m.useState)(!1),[E,I]=(0,r.A)({value:f,defaultValue:C,onChange:S}),$=(0,m.useMemo)((()=>{if(void 0===E)return[];return E.split("&").map((e=>e.trim())).map((e=>{var t,r;const{property:o,operator:l,value:i}=function(e){const[t,...n]=e.split(/\s+(?=(?:(?:[^"]*"){2})*[^"]*$)/),[r,...o]=n.join(" ").split(/\s+(?=(?:(?:[^"]*"){2})*[^"]*$)/);return{property:t,operator:r,value:o.join(" ").replace(/^"|"$/g,"")}}(e);return{property:o,operator:l,value:i,propertyLabel:(null===(t=y().find(n,(e=>e.key===o)))||void 0===t?void 0:t.propertyLabel)||o,type:(null===(r=y().find(n,(e=>e.key===o)))||void 0===r?void 0:r.type)||"string"}}))}),[E,n]),{t:N}=(0,g.Bd)(),L=y().map(n,(e=>({label:e.propertyLabel,value:e.key,filter:e}))),[R,F]=(0,m.useState)(L[0].filter),{list:B,remove:D,push:V,resetList:K,getKey:P}=(0,i.A)($),{token:X}=s.A.useToken(),[q,U]=(0,m.useState)(!0),[H,G]=(0,m.useState)(!1);(0,m.useEffect)((()=>{if(0===B.length)I(void 0);else{const t=y().map(B,(e=>{const t="string"===e.type?`"${e.value}"`:e.value;return`${e.property} ${e.operator} ${t}`}));I((e="&",t.join(` ${e} `)))}var e}),[B,I]);const W=e=>{var t,n,r;if(y().isEmpty(e))return;if(R.strictSelection||A[R.type]){if(!y().find(R.options||k[R.type],(t=>t.value===e)))return}const o=!(null!==(t=R.rule)&&void 0!==t&&t.validate)||R.rule.validate(e);if(U(o),!o)return;_("");const l=R.defaultOperator||x[R.type],i="ilike"===l||"like"===l?`%${e}%`:`${e}`;V({property:R.key,propertyLabel:R.propertyLabel,operator:l,value:i,label:null===(n=R.options)||void 0===n||null===(r=n.find((t=>t.value===e)))||void 0===r?void 0:r.label,type:R.type})};return(0,b.jsxs)(o.A,{direction:"column",gap:"xs",style:{flex:1},align:"start",children:[(0,b.jsxs)(a.A.Compact,{children:[(0,b.jsx)(c.A,{popupMatchSelectWidth:!1,options:L,value:R.key,onChange:(e,t)=>{F(y().castArray(t)[0].filter)},onSelect:()=>{var e;null===(e=M.current)||void 0===e||e.focus(),T(!0),U(!0)},showSearch:!0,optionFilterProp:"label"}),(0,b.jsx)(u.A,{title:q||!H?"":null===(t=R.rule)||void 0===t?void 0:t.message,open:!q&&H,color:X.colorError,children:(0,b.jsx)(d.A,{ref:M,value:z,open:O,onDropdownVisibleChange:T,onSelect:W,onChange:e=>{U(!0),_(e)},style:{minWidth:200},options:y().filter(R.options||k[R.type],(e=>{var t;return!!y().isEmpty(z)||(null===(t=e.label)||void 0===t?void 0:t.toString().includes(z))})),placeholder:N("propertyFilter.placeHolder"),onBlur:()=>{G(!1)},onFocus:()=>{G(!0)},children:(0,b.jsx)(p.A.Search,{onSearch:W,allowClear:!0,status:!q&&H?"error":void 0})})})]}),B.length>0&&(0,b.jsxs)(o.A,{direction:"row",gap:"xs",wrap:"wrap",style:{alignSelf:"stretch"},children:[y().map(B,((e,t)=>{return(0,b.jsxs)(v.A,{closable:!0,onClose:()=>{D(t)},style:{margin:0},children:[e.propertyLabel,":"," ",e.label||(n=e.value,n.replace(/^%|%$/g,""))]},P(t));var n})),B.length>1&&(0,b.jsx)(u.A,{title:N("propertyFilter.ResetFilter"),children:(0,b.jsx)(h.Ay,{size:"small",icon:(0,b.jsx)(l.A,{style:{color:X.colorTextSecondary}}),type:"text",onClick:()=>{K([])}})})]})]})}},42388:(e,t,n)=>{n.d(t,{A:()=>g,s:()=>m});var r=n(72375),o=n(7971),l=n(81530),i=n(72338),s=n(66596),a=n(12221),c=n(2556),u=n(46976),d=n.n(u),p=n(10709),v=n(55093),h=n(79569);const f=e=>{var t,n;let{type:c,value:u,extra:p,opts:v,hideTooltip:f=!1,max:y}=e;const{token:g}=s.A.useToken(),b=(0,l.Nw)(),{mergedResourceSlots:x}=(0,o.Hv)(b||void 0),k=e=>{var t,n,o;return null!==x&&void 0!==x&&null!==(t=x[c])&&void 0!==t&&t.number_format.binary?Number(null===(n=(0,r.Is)(e,"g",3,!0))||void 0===n?void 0:n.numberFixed).toString():((null===x||void 0===x||null===(o=x[c])||void 0===o?void 0:o.number_format.round_length)||0)>0?parseFloat(e).toFixed(2):e};return(0,h.jsxs)(i.A,{direction:"row",gap:"xxs",children:[null!==x&&void 0!==x&&x[c]?(0,h.jsx)(m,{type:c,showTooltip:!f}):c,(0,h.jsxs)(a.A.Text,{children:[k(u),d().isUndefined(y)?null:"Infinity"===y?"~\u221e":`~${k(y)}`]}),(0,h.jsx)(a.A.Text,{type:"secondary",children:(null===x||void 0===x||null===(t=x[c])||void 0===t?void 0:t.display_unit)||""}),"mem"===c&&null!==v&&void 0!==v&&v.shmem&&(null===v||void 0===v?void 0:v.shmem)>0?(0,h.jsxs)(a.A.Text,{type:"secondary",style:{fontSize:g.fontSizeSM},children:["(SHM:"," ",null===(n=(0,r.Is)(v.shmem+"b","g",2,!0))||void 0===n?void 0:n.numberFixed,"GiB)"]}):null,p]})},y=e=>{let{size:t=16,children:n}=e;return(0,h.jsx)("mwc-icon",{style:{"--mdc-icon-size":`${t+2}px`,width:t,height:t},children:n})},m=e=>{var t,n;let{type:r,size:l=16,showIcon:s=!0,showUnit:a=!0,showTooltip:u=!0,...d}=e;const v={cpu:(0,h.jsx)(y,{size:l,children:"developer_board"}),mem:(0,h.jsx)(y,{size:l,children:"memory"}),"cuda.device":"/resources/icons/file_type_cuda.svg","cuda.shares":"/resources/icons/file_type_cuda.svg","rocm.device":"/resources/icons/rocm.svg","tpu.device":(0,h.jsx)(y,{size:l,children:"view_module"}),"ipu.device":(0,h.jsx)(y,{size:l,children:"view_module"}),"atom.device":"/resources/icons/rebel.svg","atom-plus.device":"/resources/icons/rebel.svg","gaudi2.device":"/resources/icons/gaudi.svg","warboy.device":"/resources/icons/furiosa.svg","rngd.device":"/resources/icons/furiosa.svg","hyperaccel-lpu.device":"/resources/icons/npu_generic.svg"},f=null!==(t=v[r])&&void 0!==t?t:(0,h.jsx)(p.A,{}),{mergedResourceSlots:m}=(0,o.Hv)(),g="string"===typeof f?(0,h.jsx)("img",{...d,style:{height:l,alignSelf:"center",...d.style||{}},src:v[r]||"",alt:r}):(0,h.jsx)(i.A,{style:{width:16,height:16},children:f||r});return u?(0,h.jsx)(c.A,{title:(null===(n=m[r])||void 0===n?void 0:n.description)||r,children:g}):(0,h.jsx)(i.A,{style:{pointerEvents:"none"},children:g})},g=v.memo(f)},74325:(e,t,n)=>{n.d(t,{A:()=>h});var r=n(88543),o=n(76975),l=n(66596),i=n(79597),s=n(1364),a=n(88221),c=n(46976),u=n.n(c),d=n(55093),p=n(33364),v=n(79569);const h=e=>{var t;let{open:n,onRequestClose:c,columns:h,hiddenColumnKeys:f,...y}=e;const m=(0,d.useRef)(null),{t:g}=(0,p.Bd)(),{token:b}=l.A.useToken(),x=u().map(h,(e=>{return"string"===typeof e.title?{label:e.title,value:u().toString(e.key)}:"object"===typeof e.title&&"props"in e.title?{label:(t=e.title,d.Children.map(t.props.children,(e=>{if("string"===typeof e)return e}))),value:u().toString(e.key)}:{label:void 0,value:u().toString(e.key)};var t}));return(0,v.jsx)(r.A,{title:g("table.SettingTable"),open:n,destroyOnClose:!0,centered:!0,onOk:()=>{var e;null===(e=m.current)||void 0===e||e.validateFields().then((e=>{c(e)})).catch((()=>{}))},onCancel:()=>{c()},...y,children:(0,v.jsxs)(i.A,{ref:m,preserve:!1,initialValues:{selectedColumnKeys:null===(t=u().map(x,"value"))||void 0===t?void 0:t.filter((e=>!u().includes(f,e)))},layout:"vertical",children:[(0,v.jsx)(i.A.Item,{name:"searchInput",label:g("table.SelectColumnToDisplay"),style:{marginBottom:0},children:(0,v.jsx)(s.A,{prefix:(0,v.jsx)(o.A,{}),style:{marginBottom:b.marginSM},placeholder:g("table.SearchTableColumn")})}),(0,v.jsx)(i.A.Item,{noStyle:!0,shouldUpdate:(e,t)=>e.searchInput!==t.searchInput,children:e=>{let{getFieldValue:t}=e;const n=t("searchInput")?u().toLower(t("searchInput")):void 0,r=u().map(x,(e=>u().toLower(u().toString(e.label)).includes(n||"")?e:{...e,style:{display:"none"}}));return(0,v.jsx)(i.A.Item,{name:"selectedColumnKeys",style:{height:220,overflowY:"auto"},children:(0,v.jsx)(a.A.Group,{options:r,style:{flexDirection:"column"}})})}})]})})}},54690:(e,t,n)=>{n.d(t,{w4:()=>i});var r=n(46976),o=n.n(r),l=n(55093);n(63821),n(2647);const i=e=>{const[t,n]=(0,l.useState)(e);return{baiPaginationOption:{limit:t.pageSize,offset:t.current>1?(t.current-1)*t.pageSize:0},tablePaginationOption:{pageSize:t.pageSize,current:t.current},setTablePaginationOption:e=>{o().isEqual(e,t)||n((t=>({...t,...e})))}}}},53767:(e,t,n)=>{n.a(e,(async(e,r)=>{try{n.d(t,{a:()=>i});var o=n(39768),l=e([o]);o=(l.then?(await l)():l)[0];const i=e=>{const[t,n]=(0,o.q)(`hiddenColumnKeys.${e}`);return[t,n]};r()}catch(i){r(i)}}))},42926:(e,t,n)=>{n.d(t,{A:()=>a});var r=n(40991),o=n(55093);const l={icon:{tag:"svg",attrs:{viewBox:"64 64 896 896",focusable:"false"},children:[{tag:"path",attrs:{d:"M696 480H328c-4.4 0-8 3.6-8 8v48c0 4.4 3.6 8 8 8h368c4.4 0 8-3.6 8-8v-48c0-4.4-3.6-8-8-8z"}},{tag:"path",attrs:{d:"M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z"}}]},name:"minus-circle",theme:"outlined"};var i=n(36462),s=function(e,t){return o.createElement(i.A,(0,r.A)({},e,{ref:t,icon:l}))};const a=o.forwardRef(s)},72757:(e,t,n)=>{n.d(t,{A:()=>i});var r=n(92509),o=n(55093),l=n(24685);const i=function(e){void 0===e&&(e=[]);var t=(0,o.useRef)(-1),n=(0,o.useRef)([]),i=(0,o.useCallback)((function(e){t.current+=1,n.current.splice(e,0,t.current)}),[]),s=(0,r.zs)((0,o.useState)((function(){return e.forEach((function(e,t){i(t)})),e})),2),a=s[0],c=s[1],u=(0,o.useCallback)((function(e){n.current=[],c((function(){return e.forEach((function(e,t){i(t)})),e}))}),[]),d=(0,o.useCallback)((function(e,t){c((function(n){var o=(0,r.fX)([],(0,r.zs)(n),!1);return o.splice(e,0,t),i(e),o}))}),[]),p=(0,o.useCallback)((function(e){return n.current[e]}),[]),v=(0,o.useCallback)((function(e){return n.current.findIndex((function(t){return t===e}))}),[]),h=(0,o.useCallback)((function(e,t){c((function(n){var o=(0,r.fX)([],(0,r.zs)(n),!1);return t.forEach((function(t,n){i(e+n)})),o.splice.apply(o,(0,r.fX)([e,0],(0,r.zs)(t),!1)),o}))}),[]),f=(0,o.useCallback)((function(e,t){c((function(n){var o=(0,r.fX)([],(0,r.zs)(n),!1);return o[e]=t,o}))}),[]),y=(0,o.useCallback)((function(e){c((function(t){var o=(0,r.fX)([],(0,r.zs)(t),!1);o.splice(e,1);try{n.current.splice(e,1)}catch(l){console.error(l)}return o}))}),[]),m=(0,o.useCallback)((function(e){Array.isArray(e)?e.length&&c((function(t){var r=[],o=t.filter((function(t,n){var o=!e.includes(n);return o&&r.push(p(n)),o}));return n.current=r,o})):l.A&&console.error('`indexes` parameter of `batchRemove` function expected to be an array, but got "'.concat(typeof e,'".'))}),[]),g=(0,o.useCallback)((function(e,t){e!==t&&c((function(o){var l=(0,r.fX)([],(0,r.zs)(o),!1),i=l.filter((function(t,n){return n!==e}));i.splice(t,0,l[e]);try{var s=n.current.filter((function(t,n){return n!==e}));s.splice(t,0,n.current[e]),n.current=s}catch(a){console.error(a)}return i}))}),[]),b=(0,o.useCallback)((function(e){c((function(t){return i(t.length),t.concat([e])}))}),[]),x=(0,o.useCallback)((function(){try{n.current=n.current.slice(0,n.current.length-1)}catch(e){console.error(e)}c((function(e){return e.slice(0,e.length-1)}))}),[]),k=(0,o.useCallback)((function(e){c((function(t){return i(0),[e].concat(t)}))}),[]),A=(0,o.useCallback)((function(){try{n.current=n.current.slice(1,n.current.length)}catch(e){console.error(e)}c((function(e){return e.slice(1,e.length)}))}),[]),S=(0,o.useCallback)((function(e){return e.map((function(e,t){return{key:t,item:e}})).sort((function(e,t){return v(e.key)-v(t.key)})).filter((function(e){return!!e.item})).map((function(e){return e.item}))}),[]);return{list:a,insert:d,merge:h,replace:f,remove:y,batchRemove:m,getKey:p,getIndex:v,move:g,push:b,pop:x,unshift:k,shift:A,sortList:S,resetList:u}}},5975:(e,t,n)=>{n.d(t,{A:()=>m});var r=n(55093),o=n(62097),l=n.n(o),i=n(62950),s=n(55393),a=n(75725),c=n(95555),u=n(19541),d=n(47543);const{Option:p}=d.A;function v(e){return(null===e||void 0===e?void 0:e.type)&&(e.type.isSelectOption||e.type.isSelectOptGroup)}const h=(e,t)=>{var n;const{prefixCls:o,className:c,popupClassName:h,dropdownClassName:f,children:y,dataSource:m}=e,g=(0,i.A)(y);let b;1===g.length&&r.isValidElement(g[0])&&!v(g[0])&&([b]=g);const x=b?()=>b:void 0;let k;k=g.length&&v(g[0])?y:m?m.map((e=>{if(r.isValidElement(e))return e;switch(typeof e){case"string":return r.createElement(p,{key:e,value:e},e);case"object":{const{value:t}=e;return r.createElement(p,{key:t,value:t},e.text)}default:return}})):[];const{getPrefixCls:A}=r.useContext(u.QO),S=A("select",o),[C]=(0,a.YK)("SelectLike",null===(n=e.dropdownStyle)||void 0===n?void 0:n.zIndex);return r.createElement(d.A,Object.assign({ref:t,suffixIcon:null},(0,s.A)(e,["dataSource","dropdownClassName"]),{prefixCls:S,popupClassName:h||f,dropdownStyle:Object.assign(Object.assign({},e.dropdownStyle),{zIndex:C}),className:l()(`${S}-auto-complete`,c),mode:d.A.SECRET_COMBOBOX_MODE_DO_NOT_USE,getInputElement:x}),k)},f=r.forwardRef(h),y=(0,c.A)(f);f.Option=p,f._InternalPanelDoNotUseOrYouWillBeFired=y;const m=f},10709:(e,t,n)=>{n.d(t,{A:()=>r});const r=(0,n(26490).A)("Microchip",[["path",{d:"M18 12h2",key:"quuxs7"}],["path",{d:"M18 16h2",key:"zsn3lv"}],["path",{d:"M18 20h2",key:"9x5y9y"}],["path",{d:"M18 4h2",key:"1luxfb"}],["path",{d:"M18 8h2",key:"nxqzg"}],["path",{d:"M4 12h2",key:"1ltxp0"}],["path",{d:"M4 16h2",key:"8a5zha"}],["path",{d:"M4 20h2",key:"27dk57"}],["path",{d:"M4 4h2",key:"10groj"}],["path",{d:"M4 8h2",key:"18vq6w"}],["path",{d:"M8 2a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2h-1.5c-.276 0-.494.227-.562.495a2 2 0 0 1-3.876 0C9.994 2.227 9.776 2 9.5 2z",key:"1681fp"}]])}}]);
//# sourceMappingURL=9365.c854fda4.chunk.js.map