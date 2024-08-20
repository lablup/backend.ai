import{v as __extends,w as __assign,M as MDCFoundation,_ as __decorate,y as observer,z as ariaProperty,F as FormElement,R as RippleHandlers,A as x,C as addHasRemoveClass,E as o$3,G as l$1,H as i$2,J as Debouncer,K as animationFrame,m as defineCustomElement,P as PolymerElement,r as registerStyles,i as i$3,L as ElementMixin,T as ThemableMixin,o as html,n as n$4,e as e$6,t as t$2,B as BackendAIPage,b as BackendAiStyles,I as IronFlex,a as IronFlexAlignment,c as IronPositioning,x as x$1,f as translate,g as get,j as store,k as navigate,p as j,d as BackendAIPainKiller,q as o$4}from"./backend-ai-webui-dvRyOX_e.js";import"./backend-ai-list-status-CpZuh1nO.js";import"./backend-ai-session-launcher-DU0kNHBS.js";import"./lablup-grid-sort-filter-column-C2aexclr.js";import"./lablup-loading-spinner-DTpOeT_t.js";import"./mwc-formfield-azaYbQhE.js";import{C as ColumnBaseMixin,u as updateColumnOrders,a as ColumnObserver}from"./vaadin-grid-DjH0sPLR.js";import"./vaadin-grid-filter-column-Bstvob6v.js";import"./vaadin-grid-selection-column-DHR7-_MG.js";import"./vaadin-grid-sort-column-Bkfboj4k.js";import"./vaadin-item-FWhoAebV.js";import{r as r$2}from"./state-BGEx6bYL.js";import"./mwc-switch-C1VxcxVe.js";import"./mwc-tab-bar-RQBvmmHz.js";import"./lablup-progress-bar-DeByvCD9.js";import"./mwc-check-list-item-BMr63zxO.js";import"./dir-utils-BTQok0yH.js";import"./active-mixin-_JOWYQWx.js";import"./vaadin-item-mixin-Eeh1qf5y.js";!function(e){"object"==typeof exports&&"undefined"!=typeof module?module.exports=e():"function"==typeof define&&define.amd?define([],e):("undefined"!=typeof window?window:"undefined"!=typeof global?global:"undefined"!=typeof self?self:this).tus=e()}((function(){var define;return function e(t,i,o){function r(n,s){if(!i[n]){if(!t[n]){var l="function"==typeof require&&require;if(!s&&l)return l(n,!0);if(a)return a(n,!0);var d=new Error("Cannot find module '"+n+"'");throw d.code="MODULE_NOT_FOUND",d}var c=i[n]={exports:{}};t[n][0].call(c.exports,(function(e){return r(t[n][1][e]||e)}),c,c.exports,e,t,i,o)}return i[n].exports}for(var a="function"==typeof require&&require,n=0;n<o.length;n++)r(o[n]);return r}({1:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=void 0;var o=s(e("./isReactNative")),r=s(e("./uriToBlob")),a=s(e("./isCordova")),n=s(e("./readAsByteArray"));function s(e){return e&&e.__esModule?e:{default:e}}function l(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}function d(e,t,i){return t&&function(e,t){for(var i=0;i<t.length;i++){var o=t[i];o.enumerable=o.enumerable||!1,o.configurable=!0,"value"in o&&(o.writable=!0),Object.defineProperty(e,o.key,o)}}(e.prototype,t),e}var c=function(){function e(t){l(this,e),this._file=t,this.size=t.size}return d(e,[{key:"slice",value:function(e,t){if((0,a.default)())return(0,n.default)(this._file.slice(e,t));var i=this._file.slice(e,t);return Promise.resolve({value:i})}},{key:"close",value:function(){}}]),e}(),u=function(){function e(t,i){l(this,e),this._chunkSize=i,this._buffer=void 0,this._bufferOffset=0,this._reader=t,this._done=!1}return d(e,[{key:"slice",value:function(e,t){return e<this._bufferOffset?Promise.reject(new Error("Requested data is before the reader's current offset")):this._readUntilEnoughDataOrDone(e,t)}},{key:"_readUntilEnoughDataOrDone",value:function(e,t){var i=this,o=t<=this._bufferOffset+h(this._buffer);if(this._done||o){var r=this._getDataFromBuffer(e,t),a=null==r&&this._done;return Promise.resolve({value:r,done:a})}return this._reader.read().then((function(o){var r=o.value;return o.done?i._done=!0:void 0===i._buffer?i._buffer=r:i._buffer=function(e,t){if(e.concat)return e.concat(t);if(e instanceof Blob)return new Blob([e,t],{type:e.type});if(e.set){var i=new e.constructor(e.length+t.length);return i.set(e),i.set(t,e.length),i}throw new Error("Unknown data type")}(i._buffer,r),i._readUntilEnoughDataOrDone(e,t)}))}},{key:"_getDataFromBuffer",value:function(e,t){e>this._bufferOffset&&(this._buffer=this._buffer.slice(e-this._bufferOffset),this._bufferOffset=e);var i=0===h(this._buffer);return this._done&&i?null:this._buffer.slice(0,t-e)}},{key:"close",value:function(){this._reader.cancel&&this._reader.cancel()}}]),e}();function h(e){return void 0===e?0:void 0!==e.size?e.size:e.length}var p=function(){function e(){l(this,e)}return d(e,[{key:"openFile",value:function(e,t){return(0,o.default)()&&e&&void 0!==e.uri?(0,r.default)(e.uri).then((function(e){return new c(e)})).catch((function(e){throw new Error("tus: cannot fetch `file.uri` as Blob, make sure the uri is correct and accessible. "+e)})):"function"==typeof e.slice&&void 0!==e.size?Promise.resolve(new c(e)):"function"==typeof e.read?(t=+t,isFinite(t)?Promise.resolve(new u(e,t)):Promise.reject(new Error("cannot create source for stream without a finite value for the `chunkSize` option"))):Promise.reject(new Error("source object may only be an instance of File, Blob, or Reader in this environment"))}}]),e}();i.default=p},{"./isCordova":5,"./isReactNative":6,"./readAsByteArray":7,"./uriToBlob":8}],2:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=function(e,t){return(0,r.default)()?Promise.resolve(function(e,t){var i=e.exif?function(e){var t=0;if(0===e.length)return t;for(var i=0;i<e.length;i++){t=(t<<5)-t+e.charCodeAt(i),t&=t}return t}(JSON.stringify(e.exif)):"noexif";return["tus-rn",e.name||"noname",e.size||"nosize",i,t.endpoint].join("/")}(e,t)):Promise.resolve(["tus-br",e.name,e.type,e.size,e.lastModified,t.endpoint].join("-"))};var o,r=(o=e("./isReactNative"))&&o.__esModule?o:{default:o}},{"./isReactNative":6}],3:[function(e,t,i){function o(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}function r(e,t,i){return t&&function(e,t){for(var i=0;i<t.length;i++){var o=t[i];o.enumerable=o.enumerable||!1,o.configurable=!0,"value"in o&&(o.writable=!0),Object.defineProperty(e,o.key,o)}}(e.prototype,t),e}Object.defineProperty(i,"__esModule",{value:!0}),i.default=void 0;var a=function(){function e(){o(this,e)}return r(e,[{key:"createRequest",value:function(e,t){return new n(e,t)}},{key:"getName",value:function(){return"XHRHttpStack"}}]),e}();i.default=a;var n=function(){function e(t,i){o(this,e),this._xhr=new XMLHttpRequest,this._xhr.open(t,i,!0),this._method=t,this._url=i,this._headers={}}return r(e,[{key:"getMethod",value:function(){return this._method}},{key:"getURL",value:function(){return this._url}},{key:"setHeader",value:function(e,t){this._xhr.setRequestHeader(e,t),this._headers[e]=t}},{key:"getHeader",value:function(e){return this._headers[e]}},{key:"setProgressHandler",value:function(e){"upload"in this._xhr&&(this._xhr.upload.onprogress=function(t){t.lengthComputable&&e(t.loaded)})}},{key:"send",value:function(e){var t=this,i=0<arguments.length&&void 0!==e?e:null;return new Promise((function(e,o){t._xhr.onload=function(){e(new s(t._xhr))},t._xhr.onerror=function(e){o(e)},t._xhr.send(i)}))}},{key:"abort",value:function(){return this._xhr.abort(),Promise.resolve()}},{key:"getUnderlyingObject",value:function(){return this._xhr}}]),e}(),s=function(){function e(t){o(this,e),this._xhr=t}return r(e,[{key:"getStatus",value:function(){return this._xhr.status}},{key:"getHeader",value:function(e){return this._xhr.getResponseHeader(e)}},{key:"getBody",value:function(){return this._xhr.responseText}},{key:"getUnderlyingObject",value:function(){return this._xhr}}]),e}()},{}],4:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),Object.defineProperty(i,"enableDebugLog",{enumerable:!0,get:function(){return a.enableDebugLog}}),Object.defineProperty(i,"canStoreURLs",{enumerable:!0,get:function(){return n.canStoreURLs}}),i.isSupported=i.defaultOptions=i.Upload=void 0;var o=c(e("../upload")),r=c(e("../noopUrlStorage")),a=e("../logger"),n=e("./urlStorage"),s=c(e("./httpStack")),l=c(e("./fileReader")),d=c(e("./fingerprint"));function c(e){return e&&e.__esModule?e:{default:e}}function u(e){return(u="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e})(e)}function h(e,t){for(var i=0;i<t.length;i++){var o=t[i];o.enumerable=o.enumerable||!1,o.configurable=!0,"value"in o&&(o.writable=!0),Object.defineProperty(e,o.key,o)}}function p(e,t){return(p=Object.setPrototypeOf||function(e,t){return e.__proto__=t,e})(e,t)}function m(e){return(m=Object.setPrototypeOf?Object.getPrototypeOf:function(e){return e.__proto__||Object.getPrototypeOf(e)})(e)}function f(e,t){var i,o=Object.keys(e);return Object.getOwnPropertySymbols&&(i=Object.getOwnPropertySymbols(e),t&&(i=i.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),o.push.apply(o,i)),o}function g(e){for(var t=1;t<arguments.length;t++){var i=null!=arguments[t]?arguments[t]:{};t%2?f(Object(i),!0).forEach((function(t){v(e,t,i[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(i)):f(Object(i)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(i,t))}))}return e}function v(e,t,i){return t in e?Object.defineProperty(e,t,{value:i,enumerable:!0,configurable:!0,writable:!0}):e[t]=i,e}var b=g({},o.default.defaultOptions,{httpStack:new s.default,fileReader:new l.default,urlStorage:n.canStoreURLs?new n.WebStorageUrlStorage:new r.default,fingerprint:d.default});i.defaultOptions=b;var _=function(){!function(e,t){if("function"!=typeof t&&null!==t)throw new TypeError("Super expression must either be null or a function");e.prototype=Object.create(t&&t.prototype,{constructor:{value:e,writable:!0,configurable:!0}}),t&&p(e,t)}(r,o.default);var e,t,i=function(e){return function(){var t,i,o=m(e);return!(i=function(){if("undefined"!=typeof Reflect&&Reflect.construct&&!Reflect.construct.sham){if("function"==typeof Proxy)return 1;try{return Date.prototype.toString.call(Reflect.construct(Date,[],(function(){}))),1}catch(e){return}}}()?(t=m(this).constructor,Reflect.construct(o,arguments,t)):o.apply(this,arguments))||"object"!==u(i)&&"function"!=typeof i?function(e){if(void 0!==e)return e;throw new ReferenceError("this hasn't been initialised - super() hasn't been called")}(this):i}}(r);function r(){var e=0<arguments.length&&void 0!==arguments[0]?arguments[0]:null,t=1<arguments.length&&void 0!==arguments[1]?arguments[1]:{};return function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,r),t=g({},b,{},t),i.call(this,e,t)}return e=r,t=[{key:"terminate",value:function(e,t,i){return t=g({},b,{},t),o.default.terminate(e,t,i)}}],null&&h(e.prototype,null),t&&h(e,t),r}();i.Upload=_;var y=window,w=y.XMLHttpRequest,x=y.Blob,$=w&&x&&"function"==typeof x.prototype.slice;i.isSupported=$},{"../logger":11,"../noopUrlStorage":12,"../upload":13,"./fileReader":1,"./fingerprint":2,"./httpStack":3,"./urlStorage":9}],5:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=void 0,i.default=function(){return"undefined"!=typeof window&&(void 0!==window.PhoneGap||void 0!==window.Cordova||void 0!==window.cordova)}},{}],6:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=void 0,i.default=function(){return"undefined"!=typeof navigator&&"string"==typeof navigator.product&&"reactnative"===navigator.product.toLowerCase()}},{}],7:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=function(e){return new Promise((function(t,i){var o=new FileReader;o.onload=function(){var e=new Uint8Array(o.result);t({value:e})},o.onerror=function(e){i(e)},o.readAsArrayBuffer(e)}))}},{}],8:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=function(e){return new Promise((function(t,i){var o=new XMLHttpRequest;o.responseType="blob",o.onload=function(){var e=o.response;t(e)},o.onerror=function(e){i(e)},o.open("GET",e),o.send()}))}},{}],9:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.WebStorageUrlStorage=i.canStoreURLs=void 0;var o=!1;try{o="localStorage"in window;var r="tusSupport";localStorage.setItem(r,localStorage.getItem(r))}catch(e){if(e.code!==e.SECURITY_ERR&&e.code!==e.QUOTA_EXCEEDED_ERR)throw e;o=!1}i.canStoreURLs=o;var a=function(){function e(){!function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,e)}var t;return(t=[{key:"findAllUploads",value:function(){var e=this._findEntries("tus::");return Promise.resolve(e)}},{key:"findUploadsByFingerprint",value:function(e){var t=this._findEntries("tus::".concat(e,"::"));return Promise.resolve(t)}},{key:"removeUpload",value:function(e){return localStorage.removeItem(e),Promise.resolve()}},{key:"addUpload",value:function(e,t){var i=Math.round(1e12*Math.random()),o="tus::".concat(e,"::").concat(i);return localStorage.setItem(o,JSON.stringify(t)),Promise.resolve(o)}},{key:"_findEntries",value:function(e){for(var t=[],i=0;i<localStorage.length;i++){var o=localStorage.key(i);if(0===o.indexOf(e))try{var r=JSON.parse(localStorage.getItem(o));r.urlStorageKey=o,t.push(r)}catch(e){}}return t}}])&&function(e,t){for(var i=0;i<t.length;i++){var o=t[i];o.enumerable=o.enumerable||!1,o.configurable=!0,"value"in o&&(o.writable=!0),Object.defineProperty(e,o.key,o)}}(e.prototype,t),e}();i.WebStorageUrlStorage=a},{}],10:[function(e,t,i){function o(e){return(o="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e})(e)}function r(e){var t="function"==typeof Map?new Map:void 0;return(r=function(e){if(null===e||(i=e,-1===Function.toString.call(i).indexOf("[native code]")))return e;var i;if("function"!=typeof e)throw new TypeError("Super expression must either be null or a function");if(void 0!==t){if(t.has(e))return t.get(e);t.set(e,o)}function o(){return a(e,arguments,l(this).constructor)}return o.prototype=Object.create(e.prototype,{constructor:{value:o,enumerable:!1,writable:!0,configurable:!0}}),s(o,e)})(e)}function a(e,t,i){return(a=n()?Reflect.construct:function(e,t,i){var o=[null];o.push.apply(o,t);var r=new(Function.bind.apply(e,o));return i&&s(r,i.prototype),r}).apply(null,arguments)}function n(){if("undefined"!=typeof Reflect&&Reflect.construct&&!Reflect.construct.sham){if("function"==typeof Proxy)return 1;try{return Date.prototype.toString.call(Reflect.construct(Date,[],(function(){}))),1}catch(e){return}}}function s(e,t){return(s=Object.setPrototypeOf||function(e,t){return e.__proto__=t,e})(e,t)}function l(e){return(l=Object.setPrototypeOf?Object.getPrototypeOf:function(e){return e.__proto__||Object.getPrototypeOf(e)})(e)}Object.defineProperty(i,"__esModule",{value:!0}),i.default=void 0;var d=function(){!function(e,t){if("function"!=typeof t&&null!==t)throw new TypeError("Super expression must either be null or a function");e.prototype=Object.create(t&&t.prototype,{constructor:{value:e,writable:!0,configurable:!0}}),t&&s(e,t)}(t,r(Error));var e=function(e){return function(){var t,i,r=l(e);return!(i=n()?(t=l(this).constructor,Reflect.construct(r,arguments,t)):r.apply(this,arguments))||"object"!==o(i)&&"function"!=typeof i?function(e){if(void 0!==e)return e;throw new ReferenceError("this hasn't been initialised - super() hasn't been called")}(this):i}}(t);function t(i){var o,r,a,n,s,l,d=1<arguments.length&&void 0!==arguments[1]?arguments[1]:null,c=2<arguments.length&&void 0!==arguments[2]?arguments[2]:null,u=3<arguments.length&&void 0!==arguments[3]?arguments[3]:null;return function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,t),(o=e.call(this,i)).originalRequest=c,o.originalResponse=u,null!=(o.causingError=d)&&(i+=", caused by ".concat(d.toString())),null!=c&&(r=c.getHeader("X-Request-ID")||"n/a",a=c.getMethod(),n=c.getURL(),s=u?u.getStatus():"n/a",l=u?u.getBody()||"":"n/a",i+=", originated from request (method: ".concat(a,", url: ").concat(n,", response code: ").concat(s,", response text: ").concat(l,", request id: ").concat(r,")")),o.message=i,o}return t}();i.default=d},{}],11:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.enableDebugLog=function(){o=!0};var o=!(i.log=function(e){o&&console.log(e)})},{}],12:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=void 0;var o=function(){function e(){!function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,e)}var t;return(t=[{key:"listAllUploads",value:function(){return Promise.resolve([])}},{key:"findUploadsByFingerprint",value:function(){return Promise.resolve([])}},{key:"removeUpload",value:function(){return Promise.resolve()}},{key:"addUpload",value:function(){return Promise.resolve(null)}}])&&function(e,t){for(var i=0;i<t.length;i++){var o=t[i];o.enumerable=o.enumerable||!1,o.configurable=!0,"value"in o&&(o.writable=!0),Object.defineProperty(e,o.key,o)}}(e.prototype,t),e}();i.default=o},{}],13:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=void 0;var o=l(e("./error")),r=l(e("./uuid")),a=e("js-base64"),n=l(e("url-parse")),s=e("./logger");function l(e){return e&&e.__esModule?e:{default:e}}function d(e,t){var i,o=Object.keys(e);return Object.getOwnPropertySymbols&&(i=Object.getOwnPropertySymbols(e),t&&(i=i.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),o.push.apply(o,i)),o}function c(e){for(var t=1;t<arguments.length;t++){var i=null!=arguments[t]?arguments[t]:{};t%2?d(Object(i),!0).forEach((function(t){u(e,t,i[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(i)):d(Object(i)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(i,t))}))}return e}function u(e,t,i){return t in e?Object.defineProperty(e,t,{value:i,enumerable:!0,configurable:!0,writable:!0}):e[t]=i,e}function h(e,t){for(var i=0;i<t.length;i++){var o=t[i];o.enumerable=o.enumerable||!1,o.configurable=!0,"value"in o&&(o.writable=!0),Object.defineProperty(e,o.key,o)}}var p=function(){function e(t,i){!function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,e),"resume"in i&&console.log("tus: The `resume` option has been removed in tus-js-client v2. Please use the URL storage API instead."),this.options=i,this._urlStorage=this.options.urlStorage,this.file=t,this.url=null,this._req=null,this._fingerprint=null,this._urlStorageKey=null,this._offset=null,this._aborted=!1,this._size=null,this._source=null,this._retryAttempt=0,this._retryTimeout=null,this._offsetBeforeRetry=0,this._parallelUploads=null,this._parallelUploadUrls=null}var t,i,r;return t=e,r=[{key:"terminate",value:function(t,i,r){var a=1<arguments.length&&void 0!==i?i:{};if("function"==typeof a||"function"==typeof(2<arguments.length?r:void 0))throw new Error("tus: the terminate function does not accept a callback since v2 anymore; please use the returned Promise instead");var n=g("DELETE",t,a);return n.send().then((function(e){if(204!==e.getStatus())throw new o.default("tus: unexpected response while terminating upload",null,n,e)})).catch((function(i){if(i instanceof o.default||(i=new o.default("tus: failed to terminate upload",i,n,null)),!v(i,0,a))throw i;var r=a.retryDelays[0],s=a.retryDelays.slice(1),l=c({},a,{retryDelays:s});return new Promise((function(e){return setTimeout(e,r)})).then((function(){return e.terminate(t,l)}))}))}}],(i=[{key:"findPreviousUploads",value:function(){var e=this;return this.options.fingerprint(this.file,this.options).then((function(t){return e._urlStorage.findUploadsByFingerprint(t)}))}},{key:"resumeFromPreviousUpload",value:function(e){this.url=e.uploadUrl||null,this._parallelUploadUrls=e.parallelUploadUrls||null,this._urlStorageKey=e.urlStorageKey}},{key:"start",value:function(){var e,t=this,i=this.file;i?this.options.endpoint||this.options.uploadUrl?null==(e=this.options.retryDelays)||"[object Array]"===Object.prototype.toString.call(e)?(1<this.options.parallelUploads&&["uploadUrl","uploadSize","uploadLengthDeferred"].forEach((function(e){t.options[e]&&t._emitError(new Error("tus: cannot use the ".concat(e," option when parallelUploads is enabled")))})),this.options.fingerprint(i,this.options).then((function(e){return null==e?(0,s.log)("No fingerprint was calculated meaning that the upload cannot be stored in the URL storage."):(0,s.log)("Calculated fingerprint: ".concat(e)),t._fingerprint=e,t._source?t._source:t.options.fileReader.openFile(i,t.options.chunkSize)})).then((function(e){t._source=e,1<t.options.parallelUploads||null!=t._parallelUploadUrls?t._startParallelUpload():t._startSingleUpload()})).catch((function(e){t._emitError(e)}))):this._emitError(new Error("tus: the `retryDelays` option must either be an array or null")):this._emitError(new Error("tus: neither an endpoint or an upload URL is provided")):this._emitError(new Error("tus: no file or stream to upload provided"))}},{key:"_startParallelUpload",value:function(){var t=this,i=this._size=this._source.size,o=0;this._parallelUploads=[];var r=null!=this._parallelUploadUrls?this._parallelUploadUrls.length:this.options.parallelUploads,a=function(e,t,i){for(var o=Math.floor(e/t),r=[],a=0;a<t;a++)r.push({start:o*a,end:o*(a+1)});return r[t-1].end=e,i&&r.forEach((function(e,t){e.uploadUrl=i[t]||null})),r}(this._source.size,r,this._parallelUploadUrls);this._parallelUploadUrls=new Array(a.length);var n,l=a.map((function(r,n){var s=0;return t._source.slice(r.start,r.end).then((function(l){var d=l.value;return new Promise((function(l,u){var h=c({},t.options,{uploadUrl:r.uploadUrl||null,storeFingerprintForResuming:!1,removeFingerprintOnSuccess:!1,parallelUploads:1,metadata:{},headers:c({},t.options.headers,{"Upload-Concat":"partial"}),onSuccess:l,onError:u,onProgress:function(e){o=o-s+e,s=e,t._emitProgress(o,i)},_onUploadUrlAvailable:function(){t._parallelUploadUrls[n]=p.url,t._parallelUploadUrls.filter((function(e){return!!e})).length===a.length&&t._saveUploadInUrlStorage()}}),p=new e(d,h);p.start(),t._parallelUploads.push(p)}))}))}));Promise.all(l).then((function(){(n=t._openRequest("POST",t.options.endpoint)).setHeader("Upload-Concat","final;".concat(t._parallelUploadUrls.join(" ")));var e=m(t.options.metadata);return""!==e&&n.setHeader("Upload-Metadata",e),t._sendRequest(n,null)})).then((function(e){var i;f(e.getStatus(),200)?null!=(i=e.getHeader("Location"))?(t.url=b(t.options.endpoint,i),(0,s.log)("Created upload at ".concat(t.url)),t._emitSuccess()):t._emitHttpError(n,e,"tus: invalid or missing Location header"):t._emitHttpError(n,e,"tus: unexpected response while creating upload")})).catch((function(e){t._emitError(e)}))}},{key:"_startSingleUpload",value:function(){if(this.options.uploadLengthDeferred)this._size=null;else if(null!=this.options.uploadSize){if(this._size=+this.options.uploadSize,isNaN(this._size))return void this._emitError(new Error("tus: cannot convert `uploadSize` option into a number"))}else if(this._size=this._source.size,null==this._size)return void this._emitError(new Error("tus: cannot automatically derive upload's size from input and must be specified manually using the `uploadSize` option"));return this._aborted=!1,null!=this.url?((0,s.log)("Resuming upload from previous URL: ".concat(this.url)),void this._resumeUpload()):null!=this.options.uploadUrl?((0,s.log)("Resuming upload from provided URL: ".concat(this.options.url)),this.url=this.options.uploadUrl,void this._resumeUpload()):((0,s.log)("Creating a new upload"),void this._createUpload())}},{key:"abort",value:function(t,i){var o=this;if("function"==typeof i)throw new Error("tus: the abort function does not accept a callback since v2 anymore; please use the returned Promise instead");return null!=this._parallelUploads&&this._parallelUploads.forEach((function(e){e.abort(t)})),null!==this._req&&(this._req.abort(),this._source.close()),this._aborted=!0,null!=this._retryTimeout&&(clearTimeout(this._retryTimeout),this._retryTimeout=null),t&&null!=this.url?e.terminate(this.url,this.options).then((function(){return o._removeFromUrlStorage()})):Promise.resolve()}},{key:"_emitHttpError",value:function(e,t,i,r){this._emitError(new o.default(i,r,e,t))}},{key:"_emitError",value:function(e){var t=this;if(!this._aborted){if(null!=this.options.retryDelays&&(null!=this._offset&&this._offset>this._offsetBeforeRetry&&(this._retryAttempt=0),v(e,this._retryAttempt,this.options))){var i=this.options.retryDelays[this._retryAttempt++];return this._offsetBeforeRetry=this._offset,void(this._retryTimeout=setTimeout((function(){t.start()}),i))}if("function"!=typeof this.options.onError)throw e;this.options.onError(e)}}},{key:"_emitSuccess",value:function(){this.options.removeFingerprintOnSuccess&&this._removeFromUrlStorage(),"function"==typeof this.options.onSuccess&&this.options.onSuccess()}},{key:"_emitProgress",value:function(e,t){"function"==typeof this.options.onProgress&&this.options.onProgress(e,t)}},{key:"_emitChunkComplete",value:function(e,t,i){"function"==typeof this.options.onChunkComplete&&this.options.onChunkComplete(e,t,i)}},{key:"_createUpload",value:function(){var e,t,i=this;this.options.endpoint?(e=this._openRequest("POST",this.options.endpoint),this.options.uploadLengthDeferred?e.setHeader("Upload-Defer-Length",1):e.setHeader("Upload-Length",this._size),""!==(t=m(this.options.metadata))&&e.setHeader("Upload-Metadata",t),(this.options.uploadDataDuringCreation&&!this.options.uploadLengthDeferred?(this._offset=0,this._addChunkToRequest(e)):this._sendRequest(e,null)).then((function(t){if(f(t.getStatus(),200)){var o=t.getHeader("Location");if(null!=o){if(i.url=b(i.options.endpoint,o),(0,s.log)("Created upload at ".concat(i.url)),"function"==typeof i.options._onUploadUrlAvailable&&i.options._onUploadUrlAvailable(),0===i._size)return i._emitSuccess(),void i._source.close();i._saveUploadInUrlStorage(),i.options.uploadDataDuringCreation?i._handleUploadResponse(e,t):(i._offset=0,i._performUpload())}else i._emitHttpError(e,t,"tus: invalid or missing Location header")}else i._emitHttpError(e,t,"tus: unexpected response while creating upload")})).catch((function(t){i._emitHttpError(e,null,"tus: failed to create upload",t)}))):this._emitError(new Error("tus: unable to create upload because no endpoint is provided"))}},{key:"_resumeUpload",value:function(){var e=this,t=this._openRequest("HEAD",this.url);this._sendRequest(t,null).then((function(i){var o=i.getStatus();if(!f(o,200))return f(o,400)&&e._removeFromUrlStorage(),423===o?void e._emitHttpError(t,i,"tus: upload is currently locked; retry later"):e.options.endpoint?(e.url=null,void e._createUpload()):void e._emitHttpError(t,i,"tus: unable to resume upload (new upload cannot be created without an endpoint)");var r=parseInt(i.getHeader("Upload-Offset"),10);if(isNaN(r))e._emitHttpError(t,i,"tus: invalid or missing offset value");else{var a=parseInt(i.getHeader("Upload-Length"),10);if(!isNaN(a)||e.options.uploadLengthDeferred){if("function"==typeof e.options._onUploadUrlAvailable&&e.options._onUploadUrlAvailable(),r===a)return e._emitProgress(a,a),void e._emitSuccess();e._offset=r,e._performUpload()}else e._emitHttpError(t,i,"tus: invalid or missing length value")}})).catch((function(i){e._emitHttpError(t,null,"tus: failed to resume upload",i)}))}},{key:"_performUpload",value:function(){var e,t=this;this._aborted||(this.options.overridePatchMethod?(e=this._openRequest("POST",this.url)).setHeader("X-HTTP-Method-Override","PATCH"):e=this._openRequest("PATCH",this.url),e.setHeader("Upload-Offset",this._offset),this._addChunkToRequest(e).then((function(i){f(i.getStatus(),200)?t._handleUploadResponse(e,i):t._emitHttpError(e,i,"tus: unexpected response while uploading chunk")})).catch((function(i){t._aborted||t._emitHttpError(e,null,"tus: failed to upload chunk at offset "+t._offset,i)})))}},{key:"_addChunkToRequest",value:function(e){var t=this,i=this._offset,o=this._offset+this.options.chunkSize;return e.setProgressHandler((function(e){t._emitProgress(i+e,t._size)})),e.setHeader("Content-Type","application/offset+octet-stream"),(o===1/0||o>this._size)&&!this.options.uploadLengthDeferred&&(o=this._size),this._source.slice(i,o).then((function(i){var o=i.value,r=i.done;return t.options.uploadLengthDeferred&&r&&(t._size=t._offset+(o&&o.size?o.size:0),e.setHeader("Upload-Length",t._size)),null===o?t._sendRequest(e):(t._emitProgress(t._offset,t._size),t._sendRequest(e,o))}))}},{key:"_handleUploadResponse",value:function(e,t){var i=parseInt(t.getHeader("Upload-Offset"),10);if(isNaN(i))this._emitHttpError(e,t,"tus: invalid or missing offset value");else{if(this._emitProgress(i,this._size),this._emitChunkComplete(i-this._offset,i,this._size),(this._offset=i)==this._size)return this._emitSuccess(),void this._source.close();this._performUpload()}}},{key:"_openRequest",value:function(e,t){var i=g(e,t,this.options);return this._req=i}},{key:"_removeFromUrlStorage",value:function(){var e=this;this._urlStorageKey&&(this._urlStorage.removeUpload(this._urlStorageKey).catch((function(t){e._emitError(t)})),this._urlStorageKey=null)}},{key:"_saveUploadInUrlStorage",value:function(){var e,t=this;this.options.storeFingerprintForResuming&&this._fingerprint&&(e={size:this._size,metadata:this.options.metadata,creationTime:(new Date).toString()},this._parallelUploads?e.parallelUploadUrls=this._parallelUploadUrls:e.uploadUrl=this.url,this._urlStorage.addUpload(this._fingerprint,e).then((function(e){return t._urlStorageKey=e})).catch((function(e){t._emitError(e)})))}},{key:"_sendRequest",value:function(e,t){var i=this,o=1<arguments.length&&void 0!==t?t:null;return"function"==typeof this.options.onBeforeRequest&&this.options.onBeforeRequest(e),e.send(o).then((function(t){return"function"==typeof i.options.onAfterResponse&&i.options.onAfterResponse(e,t),t}))}}])&&h(t.prototype,i),r&&h(t,r),e}();function m(e){var t=[];for(var i in e)t.push(i+" "+a.Base64.encode(e[i]));return t.join(",")}function f(e,t){return t<=e&&e<t+100}function g(e,t,i){var o=i.httpStack.createRequest(e,t);o.setHeader("Tus-Resumable","1.0.0");var a,n=i.headers||{};for(var s in n)o.setHeader(s,n[s]);return i.addRequestId&&(a=(0,r.default)(),o.setHeader("X-Request-ID",a)),o}function v(e,t,i){var o,r=e.originalResponse?e.originalResponse.getStatus():0,a=!f(r,400)||409===r||423===r;return null!=i.retryDelays&&t<i.retryDelays.length&&null!=e.originalRequest&&a&&(o=!0,"undefined"!=typeof window&&"navigator"in window&&!1===window.navigator.onLine&&(o=!1),o)}function b(e,t){return new n.default(t,e).toString()}p.defaultOptions={endpoint:null,uploadUrl:null,metadata:{},fingerprint:null,uploadSize:null,onProgress:null,onChunkComplete:null,onSuccess:null,onError:null,_onUploadUrlAvailable:null,overridePatchMethod:!1,headers:{},addRequestId:!1,onBeforeRequest:null,onAfterResponse:null,chunkSize:1/0,retryDelays:[0,1e3,3e3,5e3],parallelUploads:1,storeFingerprintForResuming:!0,removeFingerprintOnSuccess:!1,uploadLengthDeferred:!1,uploadDataDuringCreation:!1,urlStorage:null,fileReader:null,httpStack:null},i.default=p},{"./error":10,"./logger":11,"./uuid":14,"js-base64":15,"url-parse":18}],14:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=function(){return"xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g,(function(e){var t=16*Math.random()|0;return("x"==e?t:3&t|8).toString(16)}))}},{}],15:[function(require,module,exports){(function(global){var Gk,Hk;Gk="undefined"!=typeof self?self:"undefined"!=typeof window?window:void 0!==global?global:this,Hk=function(global){var _Base64=global.Base64,version="2.4.9",buffer;if(void 0!==module&&module.exports)try{buffer=eval("require('buffer').Buffer")}catch(e){buffer=void 0}var b64chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",b64tab=function(e){for(var t={},i=0,o=e.length;i<o;i++)t[e.charAt(i)]=i;return t}(b64chars),fromCharCode=String.fromCharCode,cb_utob=function(e){if(e.length<2)return(t=e.charCodeAt(0))<128?e:t<2048?fromCharCode(192|t>>>6)+fromCharCode(128|63&t):fromCharCode(224|t>>>12&15)+fromCharCode(128|t>>>6&63)+fromCharCode(128|63&t);var t=65536+1024*(e.charCodeAt(0)-55296)+(e.charCodeAt(1)-56320);return fromCharCode(240|t>>>18&7)+fromCharCode(128|t>>>12&63)+fromCharCode(128|t>>>6&63)+fromCharCode(128|63&t)},re_utob=/[\uD800-\uDBFF][\uDC00-\uDFFFF]|[^\x00-\x7F]/g,utob=function(e){return e.replace(re_utob,cb_utob)},cb_encode=function(e){var t=[0,2,1][e.length%3],i=e.charCodeAt(0)<<16|(1<e.length?e.charCodeAt(1):0)<<8|(2<e.length?e.charCodeAt(2):0);return[b64chars.charAt(i>>>18),b64chars.charAt(i>>>12&63),2<=t?"=":b64chars.charAt(i>>>6&63),1<=t?"=":b64chars.charAt(63&i)].join("")},btoa=global.btoa?function(e){return global.btoa(e)}:function(e){return e.replace(/[\s\S]{1,3}/g,cb_encode)},_encode=buffer?buffer.from&&Uint8Array&&buffer.from!==Uint8Array.from?function(e){return(e.constructor===buffer.constructor?e:buffer.from(e)).toString("base64")}:function(e){return(e.constructor===buffer.constructor?e:new buffer(e)).toString("base64")}:function(e){return btoa(utob(e))},encode=function(e,t){return t?_encode(String(e)).replace(/[+\/]/g,(function(e){return"+"==e?"-":"_"})).replace(/=/g,""):_encode(String(e))},encodeURI=function(e){return encode(e,!0)},re_btou=new RegExp(["[À-ß][-¿]","[à-ï][-¿]{2}","[ð-÷][-¿]{3}"].join("|"),"g"),cb_btou=function(e){switch(e.length){case 4:var t=((7&e.charCodeAt(0))<<18|(63&e.charCodeAt(1))<<12|(63&e.charCodeAt(2))<<6|63&e.charCodeAt(3))-65536;return fromCharCode(55296+(t>>>10))+fromCharCode(56320+(1023&t));case 3:return fromCharCode((15&e.charCodeAt(0))<<12|(63&e.charCodeAt(1))<<6|63&e.charCodeAt(2));default:return fromCharCode((31&e.charCodeAt(0))<<6|63&e.charCodeAt(1))}},btou=function(e){return e.replace(re_btou,cb_btou)},cb_decode=function(e){var t=e.length,i=t%4,o=(0<t?b64tab[e.charAt(0)]<<18:0)|(1<t?b64tab[e.charAt(1)]<<12:0)|(2<t?b64tab[e.charAt(2)]<<6:0)|(3<t?b64tab[e.charAt(3)]:0),r=[fromCharCode(o>>>16),fromCharCode(o>>>8&255),fromCharCode(255&o)];return r.length-=[0,0,2,1][i],r.join("")},atob=global.atob?function(e){return global.atob(e)}:function(e){return e.replace(/[\s\S]{1,4}/g,cb_decode)},_decode=buffer?buffer.from&&Uint8Array&&buffer.from!==Uint8Array.from?function(e){return(e.constructor===buffer.constructor?e:buffer.from(e,"base64")).toString()}:function(e){return(e.constructor===buffer.constructor?e:new buffer(e,"base64")).toString()}:function(e){return btou(atob(e))},decode=function(e){return _decode(String(e).replace(/[-_]/g,(function(e){return"-"==e?"+":"/"})).replace(/[^A-Za-z0-9\+\/]/g,""))},noConflict=function(){var e=global.Base64;return global.Base64=_Base64,e},noEnum;return global.Base64={VERSION:version,atob:atob,btoa:btoa,fromBase64:decode,toBase64:encode,utob:utob,encode:encode,encodeURI:encodeURI,btou:btou,decode:decode,noConflict:noConflict,__buffer__:buffer},"function"==typeof Object.defineProperty&&(noEnum=function(e){return{value:e,enumerable:!1,writable:!0,configurable:!0}},global.Base64.extendString=function(){Object.defineProperty(String.prototype,"fromBase64",noEnum((function(){return decode(this)}))),Object.defineProperty(String.prototype,"toBase64",noEnum((function(e){return encode(this,e)}))),Object.defineProperty(String.prototype,"toBase64URI",noEnum((function(){return encode(this,!0)})))}),global.Meteor&&(Base64=global.Base64),void 0!==module&&module.exports&&(module.exports.Base64=global.Base64),{Base64:global.Base64}},"object"==typeof exports&&void 0!==module?module.exports=Hk(Gk):Hk(Gk)}).call(this,"undefined"!=typeof global?global:"undefined"!=typeof self?self:"undefined"!=typeof window?window:{})},{}],16:[function(e,t,i){var o=Object.prototype.hasOwnProperty;function r(e){return decodeURIComponent(e.replace(/\+/g," "))}i.stringify=function(e,t){t=t||"";var i=[];for(var r in"string"!=typeof t&&(t="?"),e)o.call(e,r)&&i.push(encodeURIComponent(r)+"="+encodeURIComponent(e[r]));return i.length?t+i.join("&"):""},i.parse=function(e){for(var t,i=/([^=?&]+)=?([^&]*)/g,o={};t=i.exec(e);){var a=r(t[1]),n=r(t[2]);a in o||(o[a]=n)}return o}},{}],17:[function(e,t,i){t.exports=function(e,t){if(t=t.split(":")[0],!(e=+e))return!1;switch(t){case"http":case"ws":return 80!==e;case"https":case"wss":return 443!==e;case"ftp":return 21!==e;case"gopher":return 70!==e;case"file":return!1}return 0!==e}},{}],18:[function(e,t,i){(function(i){var o=e("requires-port"),r=e("querystringify"),a=/^([a-z][a-z0-9.+-]*:)?(\/\/)?([\S\s]*)/i,n=/^[A-Za-z][A-Za-z0-9+-.]*:\/\//,s=[["#","hash"],["?","query"],function(e){return e.replace("\\","/")},["/","pathname"],["@","auth",1],[NaN,"host",void 0,1,1],[/:(\d+)$/,"port",void 0,1],[NaN,"hostname",void 0,1,1]],l={hash:1,query:1};function d(e){var t,o=i&&i.location||{},r={},a=typeof(e=e||o);if("blob:"===e.protocol)r=new u(unescape(e.pathname),{});else if("string"==a)for(t in r=new u(e,{}),l)delete r[t];else if("object"==a){for(t in e)t in l||(r[t]=e[t]);void 0===r.slashes&&(r.slashes=n.test(e.href))}return r}function c(e){var t=a.exec(e);return{protocol:t[1]?t[1].toLowerCase():"",slashes:!!t[2],rest:t[3]}}function u(e,t,i){if(!(this instanceof u))return new u(e,t,i);var a,n,l,h,p,m,f=s.slice(),g=typeof t,v=this,b=0;for("object"!=g&&"string"!=g&&(i=t,t=null),i&&"function"!=typeof i&&(i=r.parse),t=d(t),a=!(n=c(e||"")).protocol&&!n.slashes,v.slashes=n.slashes||a&&t.slashes,v.protocol=n.protocol||t.protocol||"",e=n.rest,n.slashes||(f[3]=[/(.*)/,"pathname"]);b<f.length;b++)"function"!=typeof(h=f[b])?(l=h[0],m=h[1],l!=l?v[m]=e:"string"==typeof l?~(p=e.indexOf(l))&&(e="number"==typeof h[2]?(v[m]=e.slice(0,p),e.slice(p+h[2])):(v[m]=e.slice(p),e.slice(0,p))):(p=l.exec(e))&&(v[m]=p[1],e=e.slice(0,p.index)),v[m]=v[m]||a&&h[3]&&t[m]||"",h[4]&&(v[m]=v[m].toLowerCase())):e=h(e);i&&(v.query=i(v.query)),a&&t.slashes&&"/"!==v.pathname.charAt(0)&&(""!==v.pathname||""!==t.pathname)&&(v.pathname=function(e,t){for(var i=(t||"/").split("/").slice(0,-1).concat(e.split("/")),o=i.length,r=i[o-1],a=!1,n=0;o--;)"."===i[o]?i.splice(o,1):".."===i[o]?(i.splice(o,1),n++):n&&(0===o&&(a=!0),i.splice(o,1),n--);return a&&i.unshift(""),"."!==r&&".."!==r||i.push(""),i.join("/")}(v.pathname,t.pathname)),o(v.port,v.protocol)||(v.host=v.hostname,v.port=""),v.username=v.password="",v.auth&&(h=v.auth.split(":"),v.username=h[0]||"",v.password=h[1]||""),v.origin=v.protocol&&v.host&&"file:"!==v.protocol?v.protocol+"//"+v.host:"null",v.href=v.toString()}u.prototype={set:function(e,t,i){var a,n=this;switch(e){case"query":"string"==typeof t&&t.length&&(t=(i||r.parse)(t)),n[e]=t;break;case"port":n[e]=t,o(t,n.protocol)?t&&(n.host=n.hostname+":"+t):(n.host=n.hostname,n[e]="");break;case"hostname":n[e]=t,n.port&&(t+=":"+n.port),n.host=t;break;case"host":n[e]=t,/:\d+$/.test(t)?(t=t.split(":"),n.port=t.pop(),n.hostname=t.join(":")):(n.hostname=t,n.port="");break;case"protocol":n.protocol=t.toLowerCase(),n.slashes=!i;break;case"pathname":case"hash":t?(a="pathname"===e?"/":"#",n[e]=t.charAt(0)!==a?a+t:t):n[e]=t;break;default:n[e]=t}for(var l=0;l<s.length;l++){var d=s[l];d[4]&&(n[d[1]]=n[d[1]].toLowerCase())}return n.origin=n.protocol&&n.host&&"file:"!==n.protocol?n.protocol+"//"+n.host:"null",n.href=n.toString(),n},toString:function(e){e&&"function"==typeof e||(e=r.stringify);var t,i=this,o=i.protocol;o&&":"!==o.charAt(o.length-1)&&(o+=":");var a=o+(i.slashes?"//":"");return i.username&&(a+=i.username,i.password&&(a+=":"+i.password),a+="@"),a+=i.host+i.pathname,(t="object"==typeof i.query?e(i.query):i.query)&&(a+="?"!==t.charAt(0)?"?"+t:t),i.hash&&(a+=i.hash),a}},u.extractProtocol=c,u.location=d,u.qs=r,t.exports=u}).call(this,"undefined"!=typeof global?global:"undefined"!=typeof self?self:"undefined"!=typeof window?window:{})},{querystringify:16,"requires-port":17}]},{},[4])(4)}));var tus$1=tus;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const e$5=e=>t=>"function"==typeof t?((e,t)=>(customElements.define(e,t),t))(e,t):((e,t)=>{const{kind:i,elements:o}=t;return{kind:i,elements:o,finisher(t){customElements.define(e,t)}}})(e,t)
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */,i$1=(e,t)=>"method"===t.kind&&t.descriptor&&!("value"in t.descriptor)?{...t,finisher(i){i.createProperty(t.key,e)}}:{kind:"field",key:Symbol(),placement:"own",descriptor:{},originalKey:t.key,initializer(){"function"==typeof t.initializer&&(this[t.key]=t.initializer.call(this))},finisher(i){i.createProperty(t.key,e)}},e$4=(e,t,i)=>{t.constructor.createProperty(i,e)};function n$3(e){return(t,i)=>void 0!==i?e$4(e,t,i):i$1(e,t)
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */}function t$1(e){return n$3({...e,state:!0})}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const o$2=({finisher:e,descriptor:t})=>(i,o)=>{var r;if(void 0===o){const o=null!==(r=i.originalKey)&&void 0!==r?r:i.key,a=null!=t?{kind:"method",placement:"prototype",key:o,descriptor:t(i.key)}:{...i,key:o};return null!=e&&(a.finisher=function(t){e(t,o)}),a}{const r=i.constructor;void 0!==t&&Object.defineProperty(i,o,t(o)),null==e||e(r,o)}}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */;function e$3(e){return o$2({finisher:(t,i)=>{Object.assign(t.prototype[i],e)}})}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */function i(e,t){return o$2({descriptor:t=>{const i={get(){var t,i;return null!==(i=null===(t=this.renderRoot)||void 0===t?void 0:t.querySelector(e))&&void 0!==i?i:null},enumerable:!0,configurable:!0};return i}})}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */function e$2(e){return o$2({descriptor:t=>({async get(){var t;return await this.updateComplete,null===(t=this.renderRoot)||void 0===t?void 0:t.querySelector(e)},enumerable:!0,configurable:!0})})}
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */var n$2;null===(n$2=window.HTMLSlotElement)||void 0===n$2||n$2.prototype.assignedElements;
/**
 * @license
 * Copyright 2020 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
const selectionController=Symbol("selection controller");class SingleSelectionSet{constructor(){this.selected=null,this.ordered=null,this.set=new Set}}class SingleSelectionController{constructor(e){this.sets={},this.focusedSet=null,this.mouseIsDown=!1,this.updating=!1,e.addEventListener("keydown",(e=>{this.keyDownHandler(e)})),e.addEventListener("mousedown",(()=>{this.mousedownHandler()})),e.addEventListener("mouseup",(()=>{this.mouseupHandler()}))}static getController(e){const t=!("global"in e)||"global"in e&&e.global?document:e.getRootNode();let i=t[selectionController];return void 0===i&&(i=new SingleSelectionController(t),t[selectionController]=i),i}keyDownHandler(e){const t=e.target;"checked"in t&&this.has(t)&&("ArrowRight"==e.key||"ArrowDown"==e.key?this.selectNext(t):"ArrowLeft"!=e.key&&"ArrowUp"!=e.key||this.selectPrevious(t))}mousedownHandler(){this.mouseIsDown=!0}mouseupHandler(){this.mouseIsDown=!1}has(e){return this.getSet(e.name).set.has(e)}selectPrevious(e){const t=this.getOrdered(e),i=t.indexOf(e),o=t[i-1]||t[t.length-1];return this.select(o),o}selectNext(e){const t=this.getOrdered(e),i=t.indexOf(e),o=t[i+1]||t[0];return this.select(o),o}select(e){e.click()}focus(e){if(this.mouseIsDown)return;const t=this.getSet(e.name),i=this.focusedSet;this.focusedSet=t,i!=t&&t.selected&&t.selected!=e&&t.selected.focus()}isAnySelected(e){const t=this.getSet(e.name);for(const e of t.set)if(e.checked)return!0;return!1}getOrdered(e){const t=this.getSet(e.name);return t.ordered||(t.ordered=Array.from(t.set),t.ordered.sort(((e,t)=>e.compareDocumentPosition(t)==Node.DOCUMENT_POSITION_PRECEDING?1:0))),t.ordered}getSet(e){return this.sets[e]||(this.sets[e]=new SingleSelectionSet),this.sets[e]}register(e){const t=e.name||e.getAttribute("name")||"",i=this.getSet(t);i.set.add(e),i.ordered=null}unregister(e){const t=this.getSet(e.name);t.set.delete(e),t.ordered=null,t.selected==e&&(t.selected=null)}update(e){if(this.updating)return;this.updating=!0;const t=this.getSet(e.name);if(e.checked){for(const i of t.set)i!=e&&(i.checked=!1);t.selected=e}if(this.isAnySelected(e))for(const e of t.set){if(void 0===e.formElementTabIndex)break;e.formElementTabIndex=e.checked?0:-1}this.updating=!1}}
/**
 * @license
 * Copyright 2016 Google Inc.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */var strings={NATIVE_CONTROL_SELECTOR:".mdc-radio__native-control"},cssClasses={DISABLED:"mdc-radio--disabled",ROOT:"mdc-radio"},MDCRadioFoundation=function(e){function t(i){return e.call(this,__assign(__assign({},t.defaultAdapter),i))||this}return __extends(t,e),Object.defineProperty(t,"cssClasses",{get:function(){return cssClasses},enumerable:!1,configurable:!0}),Object.defineProperty(t,"strings",{get:function(){return strings},enumerable:!1,configurable:!0}),Object.defineProperty(t,"defaultAdapter",{get:function(){return{addClass:function(){},removeClass:function(){},setNativeControlDisabled:function(){}}},enumerable:!1,configurable:!0}),t.prototype.setDisabled=function(e){var i=t.cssClasses.DISABLED;this.adapter.setNativeControlDisabled(e),e?this.adapter.addClass(i):this.adapter.removeClass(i)},t}(MDCFoundation);
/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t=window,e$1=t.ShadowRoot&&(void 0===t.ShadyCSS||t.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,s$1=Symbol(),n$1=new WeakMap;let o$1=class{constructor(e,t,i){if(this._$cssResult$=!0,i!==s$1)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const t=this.t;if(e$1&&void 0===e){const i=void 0!==t&&1===t.length;i&&(e=n$1.get(t)),void 0===e&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),i&&n$1.set(t,e))}return e}toString(){return this.cssText}};const r$1=e=>new o$1("string"==typeof e?e:e+"",void 0,s$1),S=(e,i)=>{e$1?e.adoptedStyleSheets=i.map((e=>e instanceof CSSStyleSheet?e:e.styleSheet)):i.forEach((i=>{const o=document.createElement("style"),r=t.litNonce;void 0!==r&&o.setAttribute("nonce",r),o.textContent=i.cssText,e.appendChild(o)}))},c=e$1?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t="";for(const i of e.cssRules)t+=i.cssText;return r$1(t)})(e):e
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */;var s;const e=window,r=e.trustedTypes,h=r?r.emptyScript:"",o=e.reactiveElementPolyfillSupport,n={toAttribute(e,t){switch(t){case Boolean:e=e?h:null;break;case Object:case Array:e=null==e?e:JSON.stringify(e)}return e},fromAttribute(e,t){let i=e;switch(t){case Boolean:i=null!==e;break;case Number:i=null===e?null:Number(e);break;case Object:case Array:try{i=JSON.parse(e)}catch(e){i=null}}return i}},a=(e,t)=>t!==e&&(t==t||e==e),l={attribute:!0,type:String,converter:n,reflect:!1,hasChanged:a},d="finalized";class u extends HTMLElement{constructor(){super(),this._$Ei=new Map,this.isUpdatePending=!1,this.hasUpdated=!1,this._$El=null,this._$Eu()}static addInitializer(e){var t;this.finalize(),(null!==(t=this.h)&&void 0!==t?t:this.h=[]).push(e)}static get observedAttributes(){this.finalize();const e=[];return this.elementProperties.forEach(((t,i)=>{const o=this._$Ep(i,t);void 0!==o&&(this._$Ev.set(o,i),e.push(o))})),e}static createProperty(e,t=l){if(t.state&&(t.attribute=!1),this.finalize(),this.elementProperties.set(e,t),!t.noAccessor&&!this.prototype.hasOwnProperty(e)){const i="symbol"==typeof e?Symbol():"__"+e,o=this.getPropertyDescriptor(e,i,t);void 0!==o&&Object.defineProperty(this.prototype,e,o)}}static getPropertyDescriptor(e,t,i){return{get(){return this[t]},set(o){const r=this[e];this[t]=o,this.requestUpdate(e,r,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)||l}static finalize(){if(this.hasOwnProperty(d))return!1;this[d]=!0;const e=Object.getPrototypeOf(this);if(e.finalize(),void 0!==e.h&&(this.h=[...e.h]),this.elementProperties=new Map(e.elementProperties),this._$Ev=new Map,this.hasOwnProperty("properties")){const e=this.properties,t=[...Object.getOwnPropertyNames(e),...Object.getOwnPropertySymbols(e)];for(const i of t)this.createProperty(i,e[i])}return this.elementStyles=this.finalizeStyles(this.styles),!0}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const i=new Set(e.flat(1/0).reverse());for(const e of i)t.unshift(c(e))}else void 0!==e&&t.push(c(e));return t}static _$Ep(e,t){const i=t.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof e?e.toLowerCase():void 0}_$Eu(){var e;this._$E_=new Promise((e=>this.enableUpdating=e)),this._$AL=new Map,this._$Eg(),this.requestUpdate(),null===(e=this.constructor.h)||void 0===e||e.forEach((e=>e(this)))}addController(e){var t,i;(null!==(t=this._$ES)&&void 0!==t?t:this._$ES=[]).push(e),void 0!==this.renderRoot&&this.isConnected&&(null===(i=e.hostConnected)||void 0===i||i.call(e))}removeController(e){var t;null===(t=this._$ES)||void 0===t||t.splice(this._$ES.indexOf(e)>>>0,1)}_$Eg(){this.constructor.elementProperties.forEach(((e,t)=>{this.hasOwnProperty(t)&&(this._$Ei.set(t,this[t]),delete this[t])}))}createRenderRoot(){var e;const t=null!==(e=this.shadowRoot)&&void 0!==e?e:this.attachShadow(this.constructor.shadowRootOptions);return S(t,this.constructor.elementStyles),t}connectedCallback(){var e;void 0===this.renderRoot&&(this.renderRoot=this.createRenderRoot()),this.enableUpdating(!0),null===(e=this._$ES)||void 0===e||e.forEach((e=>{var t;return null===(t=e.hostConnected)||void 0===t?void 0:t.call(e)}))}enableUpdating(e){}disconnectedCallback(){var e;null===(e=this._$ES)||void 0===e||e.forEach((e=>{var t;return null===(t=e.hostDisconnected)||void 0===t?void 0:t.call(e)}))}attributeChangedCallback(e,t,i){this._$AK(e,i)}_$EO(e,t,i=l){var o;const r=this.constructor._$Ep(e,i);if(void 0!==r&&!0===i.reflect){const a=(void 0!==(null===(o=i.converter)||void 0===o?void 0:o.toAttribute)?i.converter:n).toAttribute(t,i.type);this._$El=e,null==a?this.removeAttribute(r):this.setAttribute(r,a),this._$El=null}}_$AK(e,t){var i;const o=this.constructor,r=o._$Ev.get(e);if(void 0!==r&&this._$El!==r){const e=o.getPropertyOptions(r),a="function"==typeof e.converter?{fromAttribute:e.converter}:void 0!==(null===(i=e.converter)||void 0===i?void 0:i.fromAttribute)?e.converter:n;this._$El=r,this[r]=a.fromAttribute(t,e.type),this._$El=null}}requestUpdate(e,t,i){let o=!0;void 0!==e&&(((i=i||this.constructor.getPropertyOptions(e)).hasChanged||a)(this[e],t)?(this._$AL.has(e)||this._$AL.set(e,t),!0===i.reflect&&this._$El!==e&&(void 0===this._$EC&&(this._$EC=new Map),this._$EC.set(e,i))):o=!1),!this.isUpdatePending&&o&&(this._$E_=this._$Ej())}async _$Ej(){this.isUpdatePending=!0;try{await this._$E_}catch(e){Promise.reject(e)}const e=this.scheduleUpdate();return null!=e&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){var e;if(!this.isUpdatePending)return;this.hasUpdated,this._$Ei&&(this._$Ei.forEach(((e,t)=>this[t]=e)),this._$Ei=void 0);let t=!1;const i=this._$AL;try{t=this.shouldUpdate(i),t?(this.willUpdate(i),null===(e=this._$ES)||void 0===e||e.forEach((e=>{var t;return null===(t=e.hostUpdate)||void 0===t?void 0:t.call(e)})),this.update(i)):this._$Ek()}catch(e){throw t=!1,this._$Ek(),e}t&&this._$AE(i)}willUpdate(e){}_$AE(e){var t;null===(t=this._$ES)||void 0===t||t.forEach((e=>{var t;return null===(t=e.hostUpdated)||void 0===t?void 0:t.call(e)})),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$Ek(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$E_}shouldUpdate(e){return!0}update(e){void 0!==this._$EC&&(this._$EC.forEach(((e,t)=>this._$EO(t,this[t],e))),this._$EC=void 0),this._$Ek()}updated(e){}firstUpdated(e){}}u[d]=!0,u.elementProperties=new Map,u.elementStyles=[],u.shadowRootOptions={mode:"open"},null==o||o({ReactiveElement:u}),(null!==(s=e.reactiveElementVersions)&&void 0!==s?s:e.reactiveElementVersions=[]).push("1.6.3");
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
class RadioBase extends FormElement{constructor(){super(...arguments),this._checked=!1,this.useStateLayerCustomProperties=!1,this.global=!1,this.disabled=!1,this.value="on",this.name="",this.reducedTouchTarget=!1,this.mdcFoundationClass=MDCRadioFoundation,this.formElementTabIndex=0,this.focused=!1,this.shouldRenderRipple=!1,this.rippleElement=null,this.rippleHandlers=new RippleHandlers((()=>(this.shouldRenderRipple=!0,this.ripple.then((e=>{this.rippleElement=e})),this.ripple)))}get checked(){return this._checked}set checked(e){var t,i;const o=this._checked;e!==o&&(this._checked=e,this.formElement&&(this.formElement.checked=e),null===(t=this._selectionController)||void 0===t||t.update(this),!1===e&&(null===(i=this.formElement)||void 0===i||i.blur()),this.requestUpdate("checked",o),this.dispatchEvent(new Event("checked",{bubbles:!0,composed:!0})))}_handleUpdatedValue(e){this.formElement.value=e}renderRipple(){return this.shouldRenderRipple?x`<mwc-ripple unbounded accent
        .internalUseStateLayerCustomProperties="${this.useStateLayerCustomProperties}"
        .disabled="${this.disabled}"></mwc-ripple>`:""}get isRippleActive(){var e;return(null===(e=this.rippleElement)||void 0===e?void 0:e.isActive)||!1}connectedCallback(){super.connectedCallback(),this._selectionController=SingleSelectionController.getController(this),this._selectionController.register(this),this._selectionController.update(this)}disconnectedCallback(){this._selectionController.unregister(this),this._selectionController=void 0}focus(){this.formElement.focus()}createAdapter(){return Object.assign(Object.assign({},addHasRemoveClass(this.mdcRoot)),{setNativeControlDisabled:e=>{this.formElement.disabled=e}})}handleFocus(){this.focused=!0,this.handleRippleFocus()}handleClick(){this.formElement.focus()}handleBlur(){this.focused=!1,this.formElement.blur(),this.rippleHandlers.endFocus()}setFormData(e){this.name&&this.checked&&e.append(this.name,this.value)}render(){const e={"mdc-radio--touch":!this.reducedTouchTarget,"mdc-ripple-upgraded--background-focused":this.focused,"mdc-radio--disabled":this.disabled};return x`
      <div class="mdc-radio ${o$3(e)}">
        <input
          tabindex="${this.formElementTabIndex}"
          class="mdc-radio__native-control"
          type="radio"
          name="${this.name}"
          aria-label="${l$1(this.ariaLabel)}"
          aria-labelledby="${l$1(this.ariaLabelledBy)}"
          .checked="${this.checked}"
          .value="${this.value}"
          ?disabled="${this.disabled}"
          @change="${this.changeHandler}"
          @focus="${this.handleFocus}"
          @click="${this.handleClick}"
          @blur="${this.handleBlur}"
          @mousedown="${this.handleRippleMouseDown}"
          @mouseenter="${this.handleRippleMouseEnter}"
          @mouseleave="${this.handleRippleMouseLeave}"
          @touchstart="${this.handleRippleTouchStart}"
          @touchend="${this.handleRippleDeactivate}"
          @touchcancel="${this.handleRippleDeactivate}">
        <div class="mdc-radio__background">
          <div class="mdc-radio__outer-circle"></div>
          <div class="mdc-radio__inner-circle"></div>
        </div>
        ${this.renderRipple()}
      </div>`}handleRippleMouseDown(e){const t=()=>{window.removeEventListener("mouseup",t),this.handleRippleDeactivate()};window.addEventListener("mouseup",t),this.rippleHandlers.startPress(e)}handleRippleTouchStart(e){this.rippleHandlers.startPress(e)}handleRippleDeactivate(){this.rippleHandlers.endPress()}handleRippleMouseEnter(){this.rippleHandlers.startHover()}handleRippleMouseLeave(){this.rippleHandlers.endHover()}handleRippleFocus(){this.rippleHandlers.startFocus()}changeHandler(){this.checked=this.formElement.checked}}__decorate([i(".mdc-radio")],RadioBase.prototype,"mdcRoot",void 0),__decorate([i("input")],RadioBase.prototype,"formElement",void 0),__decorate([t$1()],RadioBase.prototype,"useStateLayerCustomProperties",void 0),__decorate([n$3({type:Boolean})],RadioBase.prototype,"global",void 0),__decorate([n$3({type:Boolean,reflect:!0})],RadioBase.prototype,"checked",null),__decorate([n$3({type:Boolean}),observer((function(e){this.mdcFoundation.setDisabled(e)}))],RadioBase.prototype,"disabled",void 0),__decorate([n$3({type:String}),observer((function(e){this._handleUpdatedValue(e)}))],RadioBase.prototype,"value",void 0),__decorate([n$3({type:String})],RadioBase.prototype,"name",void 0),__decorate([n$3({type:Boolean})],RadioBase.prototype,"reducedTouchTarget",void 0),__decorate([n$3({type:Number})],RadioBase.prototype,"formElementTabIndex",void 0),__decorate([t$1()],RadioBase.prototype,"focused",void 0),__decorate([t$1()],RadioBase.prototype,"shouldRenderRipple",void 0),__decorate([e$2("mwc-ripple")],RadioBase.prototype,"ripple",void 0),__decorate([ariaProperty,n$3({attribute:"aria-label"})],RadioBase.prototype,"ariaLabel",void 0),__decorate([ariaProperty,n$3({attribute:"aria-labelledby"})],RadioBase.prototype,"ariaLabelledBy",void 0),__decorate([e$3({passive:!0})],RadioBase.prototype,"handleRippleTouchStart",null);
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-LIcense-Identifier: Apache-2.0
 */
const styles=i$2`.mdc-touch-target-wrapper{display:inline}.mdc-radio{padding:calc((40px - 20px) / 2)}.mdc-radio .mdc-radio__native-control:enabled:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle{border-color:rgba(0, 0, 0, 0.54)}.mdc-radio .mdc-radio__native-control:enabled:checked+.mdc-radio__background .mdc-radio__outer-circle{border-color:#018786;border-color:var(--mdc-theme-secondary, #018786)}.mdc-radio .mdc-radio__native-control:enabled+.mdc-radio__background .mdc-radio__inner-circle{border-color:#018786;border-color:var(--mdc-theme-secondary, #018786)}.mdc-radio [aria-disabled=true] .mdc-radio__native-control:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio .mdc-radio__native-control:disabled:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle{border-color:rgba(0, 0, 0, 0.38)}.mdc-radio [aria-disabled=true] .mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio .mdc-radio__native-control:disabled:checked+.mdc-radio__background .mdc-radio__outer-circle{border-color:rgba(0, 0, 0, 0.38)}.mdc-radio [aria-disabled=true] .mdc-radio__native-control+.mdc-radio__background .mdc-radio__inner-circle,.mdc-radio .mdc-radio__native-control:disabled+.mdc-radio__background .mdc-radio__inner-circle{border-color:rgba(0, 0, 0, 0.38)}.mdc-radio .mdc-radio__background::before{background-color:#018786;background-color:var(--mdc-theme-secondary, #018786)}.mdc-radio .mdc-radio__background::before{top:calc(-1 * (40px - 20px) / 2);left:calc(-1 * (40px - 20px) / 2);width:40px;height:40px}.mdc-radio .mdc-radio__native-control{top:calc((40px - 40px) / 2);right:calc((40px - 40px) / 2);left:calc((40px - 40px) / 2);width:40px;height:40px}@media screen and (forced-colors: active),(-ms-high-contrast: active){.mdc-radio.mdc-radio--disabled [aria-disabled=true] .mdc-radio__native-control:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio.mdc-radio--disabled .mdc-radio__native-control:disabled:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle{border-color:GrayText}.mdc-radio.mdc-radio--disabled [aria-disabled=true] .mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio.mdc-radio--disabled .mdc-radio__native-control:disabled:checked+.mdc-radio__background .mdc-radio__outer-circle{border-color:GrayText}.mdc-radio.mdc-radio--disabled [aria-disabled=true] .mdc-radio__native-control+.mdc-radio__background .mdc-radio__inner-circle,.mdc-radio.mdc-radio--disabled .mdc-radio__native-control:disabled+.mdc-radio__background .mdc-radio__inner-circle{border-color:GrayText}}.mdc-radio{display:inline-block;position:relative;flex:0 0 auto;box-sizing:content-box;width:20px;height:20px;cursor:pointer;will-change:opacity,transform,border-color,color}.mdc-radio__background{display:inline-block;position:relative;box-sizing:border-box;width:20px;height:20px}.mdc-radio__background::before{position:absolute;transform:scale(0, 0);border-radius:50%;opacity:0;pointer-events:none;content:"";transition:opacity 120ms 0ms cubic-bezier(0.4, 0, 0.6, 1),transform 120ms 0ms cubic-bezier(0.4, 0, 0.6, 1)}.mdc-radio__outer-circle{position:absolute;top:0;left:0;box-sizing:border-box;width:100%;height:100%;border-width:2px;border-style:solid;border-radius:50%;transition:border-color 120ms 0ms cubic-bezier(0.4, 0, 0.6, 1)}.mdc-radio__inner-circle{position:absolute;top:0;left:0;box-sizing:border-box;width:100%;height:100%;transform:scale(0, 0);border-width:10px;border-style:solid;border-radius:50%;transition:transform 120ms 0ms cubic-bezier(0.4, 0, 0.6, 1),border-color 120ms 0ms cubic-bezier(0.4, 0, 0.6, 1)}.mdc-radio__native-control{position:absolute;margin:0;padding:0;opacity:0;cursor:inherit;z-index:1}.mdc-radio--touch{margin-top:4px;margin-bottom:4px;margin-right:4px;margin-left:4px}.mdc-radio--touch .mdc-radio__native-control{top:calc((40px - 48px) / 2);right:calc((40px - 48px) / 2);left:calc((40px - 48px) / 2);width:48px;height:48px}.mdc-radio.mdc-ripple-upgraded--background-focused .mdc-radio__focus-ring,.mdc-radio:not(.mdc-ripple-upgraded):focus .mdc-radio__focus-ring{pointer-events:none;border:2px solid transparent;border-radius:6px;box-sizing:content-box;position:absolute;top:50%;left:50%;transform:translate(-50%, -50%);height:100%;width:100%}@media screen and (forced-colors: active){.mdc-radio.mdc-ripple-upgraded--background-focused .mdc-radio__focus-ring,.mdc-radio:not(.mdc-ripple-upgraded):focus .mdc-radio__focus-ring{border-color:CanvasText}}.mdc-radio.mdc-ripple-upgraded--background-focused .mdc-radio__focus-ring::after,.mdc-radio:not(.mdc-ripple-upgraded):focus .mdc-radio__focus-ring::after{content:"";border:2px solid transparent;border-radius:8px;display:block;position:absolute;top:50%;left:50%;transform:translate(-50%, -50%);height:calc(100% + 4px);width:calc(100% + 4px)}@media screen and (forced-colors: active){.mdc-radio.mdc-ripple-upgraded--background-focused .mdc-radio__focus-ring::after,.mdc-radio:not(.mdc-ripple-upgraded):focus .mdc-radio__focus-ring::after{border-color:CanvasText}}.mdc-radio__native-control:checked+.mdc-radio__background,.mdc-radio__native-control:disabled+.mdc-radio__background{transition:opacity 120ms 0ms cubic-bezier(0, 0, 0.2, 1),transform 120ms 0ms cubic-bezier(0, 0, 0.2, 1)}.mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio__native-control:disabled+.mdc-radio__background .mdc-radio__outer-circle{transition:border-color 120ms 0ms cubic-bezier(0, 0, 0.2, 1)}.mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__inner-circle,.mdc-radio__native-control:disabled+.mdc-radio__background .mdc-radio__inner-circle{transition:transform 120ms 0ms cubic-bezier(0, 0, 0.2, 1),border-color 120ms 0ms cubic-bezier(0, 0, 0.2, 1)}.mdc-radio--disabled{cursor:default;pointer-events:none}.mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__inner-circle{transform:scale(0.5);transition:transform 120ms 0ms cubic-bezier(0, 0, 0.2, 1),border-color 120ms 0ms cubic-bezier(0, 0, 0.2, 1)}.mdc-radio__native-control:disabled+.mdc-radio__background,[aria-disabled=true] .mdc-radio__native-control+.mdc-radio__background{cursor:default}.mdc-radio__native-control:focus+.mdc-radio__background::before{transform:scale(1);opacity:.12;transition:opacity 120ms 0ms cubic-bezier(0, 0, 0.2, 1),transform 120ms 0ms cubic-bezier(0, 0, 0.2, 1)}:host{display:inline-block;outline:none}.mdc-radio{vertical-align:bottom}.mdc-radio .mdc-radio__native-control:enabled:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle{border-color:var(--mdc-radio-unchecked-color, rgba(0, 0, 0, 0.54))}.mdc-radio [aria-disabled=true] .mdc-radio__native-control:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio .mdc-radio__native-control:disabled:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle{border-color:var(--mdc-radio-disabled-color, rgba(0, 0, 0, 0.38))}.mdc-radio [aria-disabled=true] .mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio .mdc-radio__native-control:disabled:checked+.mdc-radio__background .mdc-radio__outer-circle{border-color:var(--mdc-radio-disabled-color, rgba(0, 0, 0, 0.38))}.mdc-radio [aria-disabled=true] .mdc-radio__native-control+.mdc-radio__background .mdc-radio__inner-circle,.mdc-radio .mdc-radio__native-control:disabled+.mdc-radio__background .mdc-radio__inner-circle{border-color:var(--mdc-radio-disabled-color, rgba(0, 0, 0, 0.38))}`
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */;let Radio=class extends RadioBase{};Radio.styles=[styles],Radio=__decorate([e$5("mwc-radio")],Radio);
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const GridColumnGroupMixin=e=>class extends(ColumnBaseMixin(e)){static get properties(){return{_childColumns:{value(){return this._getChildColumns(this)}},flexGrow:{type:Number,readOnly:!0,sync:!0},width:{type:String,readOnly:!0},_visibleChildColumns:Array,_colSpan:Number,_rootColumns:Array}}static get observers(){return["_groupFrozenChanged(frozen, _rootColumns)","_groupFrozenToEndChanged(frozenToEnd, _rootColumns)","_groupHiddenChanged(hidden)","_colSpanChanged(_colSpan, _headerCell, _footerCell)","_groupOrderChanged(_order, _rootColumns)","_groupReorderStatusChanged(_reorderStatus, _rootColumns)","_groupResizableChanged(resizable, _rootColumns)"]}connectedCallback(){super.connectedCallback(),this._addNodeObserver(),this._updateFlexAndWidth()}disconnectedCallback(){super.disconnectedCallback(),this._observer&&this._observer.disconnect()}_columnPropChanged(e,t){"hidden"===e&&(this._preventHiddenSynchronization=!0,this._updateVisibleChildColumns(this._childColumns),this._preventHiddenSynchronization=!1),/flexGrow|width|hidden|_childColumns/u.test(e)&&this._updateFlexAndWidth(),"frozen"!==e||this.frozen||(this.frozen=t),"lastFrozen"!==e||this._lastFrozen||(this._lastFrozen=t),"frozenToEnd"!==e||this.frozenToEnd||(this.frozenToEnd=t),"firstFrozenToEnd"!==e||this._firstFrozenToEnd||(this._firstFrozenToEnd=t)}_groupOrderChanged(e,t){if(t){const i=t.slice(0);if(!e)return void i.forEach((e=>{e._order=0}));const o=10**(/(0+)$/u.exec(e).pop().length-(1+~~(Math.log(t.length)/Math.LN10)));i[0]&&i[0]._order&&i.sort(((e,t)=>e._order-t._order)),updateColumnOrders(i,o,e)}}_groupReorderStatusChanged(e,t){void 0!==e&&void 0!==t&&t.forEach((t=>{t._reorderStatus=e}))}_groupResizableChanged(e,t){void 0!==e&&void 0!==t&&t.forEach((t=>{t.resizable=e}))}_updateVisibleChildColumns(e){this._visibleChildColumns=Array.prototype.filter.call(e,(e=>!e.hidden)),this._colSpan=this._visibleChildColumns.length,this._updateAutoHidden()}_updateFlexAndWidth(){if(this._visibleChildColumns){if(this._visibleChildColumns.length>0){const e=this._visibleChildColumns.reduce(((e,t)=>e+=` + ${(t.width||"0px").replace("calc","")}`),"").substring(3);this._setWidth(`calc(${e})`)}else this._setWidth("0px");this._setFlexGrow(Array.prototype.reduce.call(this._visibleChildColumns,((e,t)=>e+t.flexGrow),0))}}__scheduleAutoFreezeWarning(e,t){if(this._grid){const i=t.replace(/([A-Z])/gu,"-$1").toLowerCase(),o=e[0][t]||e[0].hasAttribute(i);e.every((e=>(e[t]||e.hasAttribute(i))===o))||(this._grid.__autoFreezeWarningDebouncer=Debouncer.debounce(this._grid.__autoFreezeWarningDebouncer,animationFrame,(()=>{console.warn(`WARNING: Joining ${t} and non-${t} Grid columns inside the same column group! This will automatically freeze all the joined columns to avoid rendering issues. If this was intentional, consider marking each joined column explicitly as ${t}. Otherwise, exclude the ${t} columns from the joined group.`)})))}}_groupFrozenChanged(e,t){void 0!==t&&void 0!==e&&!1!==e&&(this.__scheduleAutoFreezeWarning(t,"frozen"),Array.from(t).forEach((t=>{t.frozen=e})))}_groupFrozenToEndChanged(e,t){void 0!==t&&void 0!==e&&!1!==e&&(this.__scheduleAutoFreezeWarning(t,"frozenToEnd"),Array.from(t).forEach((t=>{t.frozenToEnd=e})))}_groupHiddenChanged(e){(e||this.__groupHiddenInitialized)&&this._synchronizeHidden(),this.__groupHiddenInitialized=!0}_updateAutoHidden(){const e=this._autoHidden;this._autoHidden=0===(this._visibleChildColumns||[]).length,(e||this._autoHidden)&&(this.hidden=this._autoHidden)}_synchronizeHidden(){this._childColumns&&!this._preventHiddenSynchronization&&this._childColumns.forEach((e=>{e.hidden=this.hidden}))}_colSpanChanged(e,t,i){t&&(t.setAttribute("colspan",e),this._grid&&this._grid._a11yUpdateCellColspan(t,e)),i&&(i.setAttribute("colspan",e),this._grid&&this._grid._a11yUpdateCellColspan(i,e))}_getChildColumns(e){return ColumnObserver.getColumns(e)}_addNodeObserver(){this._observer=new ColumnObserver(this,(()=>{this._preventHiddenSynchronization=!0,this._rootColumns=this._getChildColumns(this),this._childColumns=this._rootColumns,this._updateVisibleChildColumns(this._childColumns),this._preventHiddenSynchronization=!1,this._grid&&this._grid._debounceUpdateColumnTree&&this._grid._debounceUpdateColumnTree()})),this._observer.flush()}_isColumnElement(e){return e.nodeType===Node.ELEMENT_NODE&&/\bcolumn\b/u.test(e.localName)}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;class GridColumnGroup extends(GridColumnGroupMixin(PolymerElement)){static get is(){return"vaadin-grid-column-group"}}defineCustomElement(GridColumnGroup),registerStyles("vaadin-progress-bar",i$3`
    :host {
      height: calc(var(--lumo-size-l) / 10);
      margin: var(--lumo-space-s) 0;
    }

    [part='bar'] {
      border-radius: var(--lumo-border-radius-m);
      background-color: var(--lumo-contrast-10pct);
    }

    [part='value'] {
      border-radius: var(--lumo-border-radius-m);
      background-color: var(--lumo-primary-color);
      /* Use width instead of transform to preserve border radius */
      transform: none;
      width: calc(var(--vaadin-progress-value) * 100%);
      will-change: width;
      transition: 0.1s width linear;
    }

    /* Indeterminate mode */
    :host([indeterminate]) [part='value'] {
      --lumo-progress-indeterminate-progress-bar-background: linear-gradient(
        to right,
        var(--lumo-primary-color-10pct) 10%,
        var(--lumo-primary-color)
      );
      --lumo-progress-indeterminate-progress-bar-background-reverse: linear-gradient(
        to left,
        var(--lumo-primary-color-10pct) 10%,
        var(--lumo-primary-color)
      );
      width: 100%;
      background-color: transparent !important;
      background-image: var(--lumo-progress-indeterminate-progress-bar-background);
      opacity: 0.75;
      will-change: transform;
      animation: vaadin-progress-indeterminate 1.6s infinite cubic-bezier(0.645, 0.045, 0.355, 1);
    }

    @keyframes vaadin-progress-indeterminate {
      0% {
        transform: scaleX(0.015);
        transform-origin: 0% 0%;
      }

      25% {
        transform: scaleX(0.4);
      }

      50% {
        transform: scaleX(0.015);
        transform-origin: 100% 0%;
        background-image: var(--lumo-progress-indeterminate-progress-bar-background);
      }

      50.1% {
        transform: scaleX(0.015);
        transform-origin: 100% 0%;
        background-image: var(--lumo-progress-indeterminate-progress-bar-background-reverse);
      }

      75% {
        transform: scaleX(0.4);
      }

      100% {
        transform: scaleX(0.015);
        transform-origin: 0% 0%;
        background-image: var(--lumo-progress-indeterminate-progress-bar-background-reverse);
      }
    }

    :host(:not([aria-valuenow])) [part='value']::before,
    :host([indeterminate]) [part='value']::before {
      content: '';
      display: block;
      width: 100%;
      height: 100%;
      border-radius: inherit;
      background-color: var(--lumo-primary-color);
      will-change: opacity;
      animation: vaadin-progress-pulse3 1.6s infinite cubic-bezier(0.645, 0.045, 0.355, 1);
    }

    @keyframes vaadin-progress-pulse3 {
      0% {
        opacity: 1;
      }

      10% {
        opacity: 0;
      }

      40% {
        opacity: 0;
      }

      50% {
        opacity: 1;
      }

      50.1% {
        opacity: 1;
      }

      60% {
        opacity: 0;
      }

      90% {
        opacity: 0;
      }

      100% {
        opacity: 1;
      }
    }

    /* Contrast color */
    :host([theme~='contrast']) [part='value'],
    :host([theme~='contrast']) [part='value']::before {
      background-color: var(--lumo-contrast-80pct);
      --lumo-progress-indeterminate-progress-bar-background: linear-gradient(
        to right,
        var(--lumo-contrast-5pct) 10%,
        var(--lumo-contrast-80pct)
      );
      --lumo-progress-indeterminate-progress-bar-background-reverse: linear-gradient(
        to left,
        var(--lumo-contrast-5pct) 10%,
        var(--lumo-contrast-60pct)
      );
    }

    /* Error color */
    :host([theme~='error']) [part='value'],
    :host([theme~='error']) [part='value']::before {
      background-color: var(--lumo-error-color);
      --lumo-progress-indeterminate-progress-bar-background: linear-gradient(
        to right,
        var(--lumo-error-color-10pct) 10%,
        var(--lumo-error-color)
      );
      --lumo-progress-indeterminate-progress-bar-background-reverse: linear-gradient(
        to left,
        var(--lumo-error-color-10pct) 10%,
        var(--lumo-error-color)
      );
    }

    /* Primary color */
    :host([theme~='success']) [part='value'],
    :host([theme~='success']) [part='value']::before {
      background-color: var(--lumo-success-color);
      --lumo-progress-indeterminate-progress-bar-background: linear-gradient(
        to right,
        var(--lumo-success-color-10pct) 10%,
        var(--lumo-success-color)
      );
      --lumo-progress-indeterminate-progress-bar-background-reverse: linear-gradient(
        to left,
        var(--lumo-success-color-10pct) 10%,
        var(--lumo-success-color)
      );
    }

    /* RTL specific styles */
    :host([indeterminate][dir='rtl']) [part='value'] {
      --lumo-progress-indeterminate-progress-bar-background: linear-gradient(
        to left,
        var(--lumo-primary-color-10pct) 10%,
        var(--lumo-primary-color)
      );
      --lumo-progress-indeterminate-progress-bar-background-reverse: linear-gradient(
        to right,
        var(--lumo-primary-color-10pct) 10%,
        var(--lumo-primary-color)
      );
      animation: vaadin-progress-indeterminate-rtl 1.6s infinite cubic-bezier(0.355, 0.045, 0.645, 1);
    }

    :host(:not([aria-valuenow])[dir='rtl']) [part='value']::before,
    :host([indeterminate][dir='rtl']) [part='value']::before {
      animation: vaadin-progress-pulse3 1.6s infinite cubic-bezier(0.355, 0.045, 0.645, 1);
    }

    @keyframes vaadin-progress-indeterminate-rtl {
      0% {
        transform: scaleX(0.015);
        transform-origin: 100% 0%;
      }

      25% {
        transform: scaleX(0.4);
      }

      50% {
        transform: scaleX(0.015);
        transform-origin: 0% 0%;
        background-image: var(--lumo-progress-indeterminate-progress-bar-background);
      }

      50.1% {
        transform: scaleX(0.015);
        transform-origin: 0% 0%;
        background-image: var(--lumo-progress-indeterminate-progress-bar-background-reverse);
      }

      75% {
        transform: scaleX(0.4);
      }

      100% {
        transform: scaleX(0.015);
        transform-origin: 100% 0%;
        background-image: var(--lumo-progress-indeterminate-progress-bar-background-reverse);
      }
    }

    /* Contrast color */
    :host([theme~='contrast'][dir='rtl']) [part='value'],
    :host([theme~='contrast'][dir='rtl']) [part='value']::before {
      --lumo-progress-indeterminate-progress-bar-background: linear-gradient(
        to left,
        var(--lumo-contrast-5pct) 10%,
        var(--lumo-contrast-80pct)
      );
      --lumo-progress-indeterminate-progress-bar-background-reverse: linear-gradient(
        to right,
        var(--lumo-contrast-5pct) 10%,
        var(--lumo-contrast-60pct)
      );
    }

    /* Error color */
    :host([theme~='error'][dir='rtl']) [part='value'],
    :host([theme~='error'][dir='rtl']) [part='value']::before {
      --lumo-progress-indeterminate-progress-bar-background: linear-gradient(
        to left,
        var(--lumo-error-color-10pct) 10%,
        var(--lumo-error-color)
      );
      --lumo-progress-indeterminate-progress-bar-background-reverse: linear-gradient(
        to right,
        var(--lumo-error-color-10pct) 10%,
        var(--lumo-error-color)
      );
    }

    /* Primary color */
    :host([theme~='success'][dir='rtl']) [part='value'],
    :host([theme~='success'][dir='rtl']) [part='value']::before {
      --lumo-progress-indeterminate-progress-bar-background: linear-gradient(
        to left,
        var(--lumo-success-color-10pct) 10%,
        var(--lumo-success-color)
      );
      --lumo-progress-indeterminate-progress-bar-background-reverse: linear-gradient(
        to right,
        var(--lumo-success-color-10pct) 10%,
        var(--lumo-success-color)
      );
    }
  `,{moduleId:"lumo-progress-bar"});const template=document.createElement("template");template.innerHTML="\n  <style>\n    @keyframes vaadin-progress-pulse3 {\n      0% { opacity: 1; }\n      10% { opacity: 0; }\n      40% { opacity: 0; }\n      50% { opacity: 1; }\n      50.1% { opacity: 1; }\n      60% { opacity: 0; }\n      90% { opacity: 0; }\n      100% { opacity: 1; }\n    }\n  </style>\n",document.head.appendChild(template.content);
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const progressBarStyles=i$3`
  :host {
    display: block;
    width: 100%; /* prevent collapsing inside non-stretching column flex */
    height: 8px;
  }

  :host([hidden]) {
    display: none !important;
  }

  [part='bar'] {
    height: 100%;
  }

  [part='value'] {
    height: 100%;
    transform-origin: 0 50%;
    transform: scaleX(var(--vaadin-progress-value));
  }

  :host([dir='rtl']) [part='value'] {
    transform-origin: 100% 50%;
  }

  @media (forced-colors: active) {
    [part='bar'] {
      outline: 1px solid;
    }

    [part='value'] {
      background-color: AccentColor !important;
      forced-color-adjust: none;
    }
  }
`
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,ProgressMixin=e=>class extends e{static get properties(){return{value:{type:Number,observer:"_valueChanged"},min:{type:Number,value:0,observer:"_minChanged"},max:{type:Number,value:1,observer:"_maxChanged"},indeterminate:{type:Boolean,value:!1,reflectToAttribute:!0}}}static get observers(){return["_normalizedValueChanged(value, min, max)"]}ready(){super.ready(),this.setAttribute("role","progressbar")}_normalizedValueChanged(e,t,i){const o=this._normalizeValue(e,t,i);this.style.setProperty("--vaadin-progress-value",o)}_valueChanged(e){this.setAttribute("aria-valuenow",e)}_minChanged(e){this.setAttribute("aria-valuemin",e)}_maxChanged(e){this.setAttribute("aria-valuemax",e)}_normalizeValue(e,t,i){let o;return e||0===e?t>=i?o=1:(o=(e-t)/(i-t),o=Math.min(Math.max(o,0),1)):o=0,o}}
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;registerStyles("vaadin-progress-bar",progressBarStyles,{moduleId:"vaadin-progress-bar-styles"});class ProgressBar extends(ElementMixin(ThemableMixin(ProgressMixin(PolymerElement)))){static get is(){return"vaadin-progress-bar"}static get template(){return html`
      <div part="bar">
        <div part="value"></div>
      </div>
    `}}defineCustomElement(ProgressBar);let BackendAiStorageList=class extends BackendAIPage{constructor(){super(),this._APIMajorVersion=5,this.storageType="general",this.folders=[],this.folderInfo=Object(),this.is_admin=!1,this.enableStorageProxy=!1,this.enableInferenceWorkload=!1,this.enableVfolderTrashBin=!1,this.authenticated=!1,this.renameFolderName="",this.deleteFolderName="",this.deleteFolderID="",this.leaveFolderName="",this.explorer=Object(),this.explorerFiles=[],this.existingFile="",this.invitees=[],this.selectedFolder="",this.selectedFolderType="",this.downloadURL="",this.uploadFiles=[],this.currentUploadFile=Object(),this.fileUploadQueue=[],this.fileUploadCount=0,this.concurrentFileUploadLimit=2,this.vhost="",this.vhosts=[],this.allowedGroups=[],this.indicator=Object(),this.notification=Object(),this.listCondition="loading",this.allowed_folder_type=[],this.uploadFilesExist=!1,this._boundIndexRenderer=Object(),this._boundTypeRenderer=Object(),this._boundFolderListRenderer=Object(),this._boundControlFolderListRenderer=Object(),this._boundTrashBinControlFolderListRenderer=Object(),this._boundControlFileListRenderer=Object(),this._boundPermissionViewRenderer=Object(),this._boundOwnerRenderer=Object(),this._boundFileNameRenderer=Object(),this._boundCreatedTimeRenderer=Object(),this._boundSizeRenderer=Object(),this._boundPermissionRenderer=Object(),this._boundCloneableRenderer=Object(),this._boundQuotaRenderer=Object(),this._boundUploadListRenderer=Object(),this._boundUploadProgressRenderer=Object(),this._boundInviteeInfoRenderer=Object(),this._boundIDRenderer=Object(),this._boundStatusRenderer=Object(),this._uploadFlag=!0,this._folderRefreshing=!1,this.lastQueryTime=0,this.isWritable=!1,this.permissions={rw:"Read-Write",ro:"Read-Only",wd:"Delete"},this._maxFileUploadSize=-1,this.oldFileExtension="",this.newFileExtension="",this.is_dir=!1,this._isDirectorySizeVisible=!0,this.minimumResource={cpu:1,mem:.5},this.filebrowserSupportedImages=[],this.systemRoleSupportedImages=[],this.volumeInfo=Object(),this.quotaSupportStorageBackends=["xfs","weka","spectrumscale","netapp","vast","cephfs","ddn"],this.quotaUnit={MB:Math.pow(10,6),GB:Math.pow(10,9),TB:Math.pow(10,12),PB:Math.pow(10,15),MiB:Math.pow(2,20),GiB:Math.pow(2,30),TiB:Math.pow(2,40),PiB:Math.pow(2,50)},this.maxSize={value:0,unit:"MB"},this.quota={value:0,unit:"MB"},this.directoryBasedUsage=!1,this._unionedAllowedPermissionByVolume=Object(),this._boundIndexRenderer=this.indexRenderer.bind(this),this._boundTypeRenderer=this.typeRenderer.bind(this),this._boundControlFolderListRenderer=this.controlFolderListRenderer.bind(this),this._boundTrashBinControlFolderListRenderer=this.trashBinControlFolderListRenderer.bind(this),this._boundControlFileListRenderer=this.controlFileListRenderer.bind(this),this._boundPermissionViewRenderer=this.permissionViewRenderer.bind(this),this._boundCloneableRenderer=this.CloneableRenderer.bind(this),this._boundOwnerRenderer=this.OwnerRenderer.bind(this),this._boundFileNameRenderer=this.fileNameRenderer.bind(this),this._boundCreatedTimeRenderer=this.createdTimeRenderer.bind(this),this._boundSizeRenderer=this.sizeRenderer.bind(this),this._boundPermissionRenderer=this.permissionRenderer.bind(this),this._boundFolderListRenderer=this.folderListRenderer.bind(this),this._boundQuotaRenderer=this.quotaRenderer.bind(this),this._boundUploadListRenderer=this.uploadListRenderer.bind(this),this._boundUploadProgressRenderer=this.uploadProgressRenderer.bind(this),this._boundInviteeInfoRenderer=this.inviteeInfoRenderer.bind(this),this._boundIDRenderer=this.iDRenderer.bind(this),this._boundStatusRenderer=this.statusRenderer.bind(this)}static get styles(){return[BackendAiStyles,IronFlex,IronFlexAlignment,IronPositioning,i$3`
        vaadin-grid {
          border: 0 !important;
          height: calc(100vh - 460px);
        }

        vaadin-grid.folderlist {
          border: 0;
          font-size: 14px;
        }

        vaadin-grid.explorer {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 370px);
        }

        #session-launcher {
          --component-width: 235px;
        }

        span.title {
          margin: auto 10px;
          min-width: 35px;
        }

        ul {
          padding-left: 0;
        }

        ul li {
          list-style: none;
          font-size: 13px;
        }

        span.indicator {
          width: 100px;
          font-size: 10px;
        }

        .info-indicator {
          min-width: 90px;
          padding: 0 10px;
        }

        div.big.indicator {
          font-size: 48px;
          margin-top: 10px;
          margin-bottom: 10px;
        }

        mwc-icon-button {
          --mdc-icon-size: 24px;
        }
        mwc-icon {
          --mdc-icon-size: 16px;
          padding: 0;
        }

        mwc-icon-button.tiny {
          width: 35px;
          height: 35px;
        }

        mwc-icon.cloneable {
          padding-top: 10px;
        }

        .warning {
          color: red;
        }

        vaadin-item {
          font-size: 13px;
          font-weight: 100;
        }

        mwc-checkbox {
          --mdc-theme-secondary: var(--general-checkbox-color);
        }

        #folder-explorer-dialog {
          width: calc(100% - 250px); /* 250px is width for drawer menu */
          --component-height: calc(100vh - 200px); /* calc(100vh - 170px); */
          right: 0;
          top: 0;
          margin: 170px 0 0 0;
        }

        #folder-explorer-dialog.mini_ui {
          width: calc(
            100% - 88px
          ); /* 88px is width for mini-ui icon of drawer menu */
        }

        /* #folder-explorer-dialog vaadin-grid vaadin-grid-column {
          height: 32px !important;
        }*/

        #folder-explorer-dialog vaadin-grid mwc-icon-button {
          --mdc-icon-size: 24px;
          --mdc-icon-button-size: 28px;
          background-color: transparent;
        }

        #filebrowser-notification-dialog {
          --component-width: 350px;
        }

        vaadin-text-field {
          --vaadin-text-field-default-width: auto;
        }

        vaadin-grid-cell-content {
          overflow: visible;
        }

        div.breadcrumb {
          color: #637282;
          font-size: 1em;
          margin-bottom: 10px;
          margin-left: 20px;
        }

        div.breadcrumb span:first-child {
          display: none;
        }

        .breadcrumb li:before {
          padding: 3px;
          transform: rotate(-45deg) translateY(-2px);
          transition: color ease-in 0.2s;
          border: solid;
          border-width: 0 2px 2px 0;
          border-color: var(--token-colorBorder, #242424);
          margin-right: 10px;
          content: '';
          display: inline-block;
        }

        .breadcrumb li {
          display: inline-block;
          font-size: 16px;
        }

        .breadcrumb mwc-icon-button {
          --mdc-icon-size: 20px;
          --mdc-icon-button-size: 22px;
        }

        mwc-textfield {
          width: 100%;
          /* --mdc-text-field-label-ink-color: var(--token-colorText); */
        }

        mwc-textfield.red {
          --mdc-theme-primary: var(--paper-red-400) !important;
        }

        mwc-textfield#modify-folder-quota {
          width: 100%;
          max-width: 200px;
          padding: 0;
        }

        mwc-button {
          --mdc-typography-button-font-size: 12px;
        }

        mwc-button#readonly-btn {
          width: 150px;
        }

        div#upload {
          margin: 0;
          padding: 0;
        }

        div#dropzone {
          display: none;
          position: absolute;
          top: 0;
          height: 100%;
          width: 100%;
          z-index: 10;
        }

        div#dropzone,
        div#dropzone p {
          margin: 0;
          padding: 0;
          width: 100%;
          background: rgba(211, 211, 211, 0.5);
          text-align: center;
        }

        .progress {
          padding: 30px 10px;
          border: 1px solid lightgray;
        }

        .progress-item {
          padding: 10px 30px;
        }

        backend-ai-dialog mwc-textfield,
        backend-ai-dialog mwc-select {
          --mdc-typography-label-font-size: var(--token-fontSizeSM, 12px);
        }

        mwc-select#modify-folder-quota-unit {
          width: 120px;
          --mdc-menu-min-width: 120px;
          --mdc-menu-max-width: 120px;
        }

        mwc-select.full-width {
          width: 100%;
        }

        mwc-select.full-width.fixed-position > mwc-list-item {
          width: 288px; // default width
        }

        mwc-select.fixed-position {
          /* Need to be set when fixedMenuPosition attribute is enabled */
          --mdc-menu-max-width: 320px;
          --mdc-menu-min-width: 320px;
        }

        mwc-select#modify-folder-quota-unit > mwc-list-item {
          width: 88px; // default width
        }

        mwc-select.fixed-position > mwc-list-item {
          width: 147px; // default width
        }

        #modify-permission-dialog {
          --component-min-width: 600px;
        }

        backend-ai-dialog {
          --component-min-width: 350px;
        }

        backend-ai-dialog#modify-folder-dialog {
          --component-max-width: 375px;
        }

        .apply-grayscale {
          -webkit-filter: grayscale(1);
          filter: grayscale(1);
        }

        img#filebrowser-img,
        img#ssh-img {
          width: 18px;
          margin: 15px 10px;
        }

        @media screen and (max-width: 700px) {
          #folder-explorer-dialog,
          #folder-explorer-dialog.mini_ui {
            min-width: 410px;
            --component-width: 100%;
            width: 100%;
            position: absolute;
            margin-left: auto;
            margin-right: auto;
            left: 0px;
            right: 0px;
          }
        }

        @media screen and (max-width: 750px) {
          #folder-explorer-dialog,
          #folder-explorer-dialog.mini_ui {
            --component-width: auto;
          }

          mwc-button {
            width: auto;
          }
          mwc-button > span {
            display: none;
          }
          #modify-permission-dialog {
            --component-min-width: 100%;
          }
        }

        @media screen and (min-width: 900px) {
          #folder-explorer-dialog,
          #folder-explorer-dialog.mini_ui {
            --component-width: calc(100% - 45px); /* calc(100% - 30px); */
          }
        }
      `]}_toggleFileListCheckbox(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll(".multiple-action-buttons");this.fileListGrid.selectedItems.length>0?[].forEach.call(t,(e=>{e.style.display="block"})):[].forEach.call(t,(e=>{e.style.display="none"}))}_updateQuotaInputHumanReadableValue(){let e="MB";const t=Number(this.modifyFolderQuotaInput.value)*this.quotaUnit[this.modifyFolderQuotaUnitSelect.value],i=this.maxSize.value*this.quotaUnit[this.maxSize.unit];[this.modifyFolderQuotaInput.value,e]=globalThis.backendaiutils._humanReadableFileSize(t).split(" "),["Bytes","KB","MB"].includes(e)?(this.modifyFolderQuotaInput.value="MB"===e?Number(this.modifyFolderQuotaInput.value)<1?"1":Math.round(Number(this.modifyFolderQuotaInput.value)).toString():"1",e="MB"):(this.modifyFolderQuotaInput.value=parseFloat(this.modifyFolderQuotaInput.value).toFixed(1),i<t&&(this.modifyFolderQuotaInput.value=this.maxSize.value.toString(),e=this.maxSize.unit)),this.modifyFolderQuotaInput.step="MB"===this.modifyFolderQuotaUnitSelect.value?0:.1;const o=this.modifyFolderQuotaUnitSelect.items.findIndex((t=>t.value===e));this.modifyFolderQuotaUnitSelect.select(o)}render(){var e,t,i,o;return x$1`
      <lablup-loading-spinner id="loading-spinner"></lablup-loading-spinner>
      <backend-ai-session-launcher
        mode="inference"
        location="data"
        hideLaunchButton
        id="session-launcher"
        ?active="${!0===this.active}"
        .newSessionDialogTitle="${translate("session.launcher.StartModelServing")}"
      ></backend-ai-session-launcher>
      <div class="list-wrapper">
        <vaadin-grid
          class="folderlist"
          id="folder-list-grid"
          theme="row-stripes column-borders wrap-cell-content compact dark"
          column-reordering-allowed
          aria-label="Folder list"
          .items="${this.folders}"
        >
          <vaadin-grid-column
            width="40px"
            flex-grow="0"
            resizable
            header="#"
            text-align="center"
            .renderer="${this._boundIndexRenderer}"
          ></vaadin-grid-column>
          <lablup-grid-sort-filter-column
            path="name"
            width="80px"
            resizable
            .renderer="${this._boundFolderListRenderer}"
            header="${translate("data.folders.Name")}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="id"
            width="130px"
            flex-grow="0"
            resizable
            header="ID"
            .renderer="${this._boundIDRenderer}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="host"
            width="105px"
            flex-grow="0"
            resizable
            header="${translate("data.folders.Location")}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="status"
            width="80px"
            flex-grow="0"
            resizable
            .renderer="${this._boundStatusRenderer}"
            header="${translate("data.folders.Status")}"
          ></lablup-grid-sort-filter-column>
          ${this.directoryBasedUsage?x$1`
                <vaadin-grid-sort-column
                  id="folder-quota-column"
                  path="max_size"
                  width="95px"
                  flex-grow="0"
                  resizable
                  header="${translate("data.folders.FolderQuota")}"
                  .renderer="${this._boundQuotaRenderer}"
                ></vaadin-grid-sort-column>
              `:x$1``}
          <lablup-grid-sort-filter-column
            path="ownership_type"
            width="70px"
            flex-grow="0"
            resizable
            header="${translate("data.folders.Type")}"
            .renderer="${this._boundTypeRenderer}"
          ></lablup-grid-sort-filter-column>
          <vaadin-grid-column
            width="95px"
            flex-grow="0"
            resizable
            header="${translate("data.folders.Permission")}"
            .renderer="${this._boundPermissionViewRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            auto-width
            flex-grow="0"
            resizable
            header="${translate("data.folders.Owner")}"
            .renderer="${this._boundOwnerRenderer}"
          ></vaadin-grid-column>
          ${this.enableStorageProxy&&"model"===this.storageType&&this.is_admin?x$1`
                <vaadin-grid-column
                  auto-width
                  flex-grow="0"
                  resizable
                  header="${translate("data.folders.Cloneable")}"
                  .renderer="${this._boundCloneableRenderer}"
                ></vaadin-grid-column>
              `:x$1``}
          ${"deadVFolderStatus"!==this.storageType?x$1`
                <vaadin-grid-column
                  auto-width
                  resizable
                  header="${translate("data.folders.Control")}"
                  .renderer="${this._boundControlFolderListRenderer}"
                ></vaadin-grid-column>
              `:x$1`
                <vaadin-grid-column
                  auto-width
                  resizable
                  header="${translate("data.folders.Control")}"
                  .renderer="${this._boundTrashBinControlFolderListRenderer}"
                ></vaadin-grid-column>
              `}
        </vaadin-grid>
        <backend-ai-list-status
          id="list-status"
          statusCondition="${this.listCondition}"
          message="${get("data.folders.NoFolderToDisplay")}"
        ></backend-ai-list-status>
      </div>
      <backend-ai-dialog id="modify-folder-dialog" fixed backdrop>
        <span slot="title">${translate("data.folders.FolderOptionUpdate")}</span>
        <div slot="content" class="vertical layout flex">
          <div
            class="vertical layout"
            id="modify-quota-controls"
            style="display:${this.directoryBasedUsage&&this._checkFolderSupportDirectoryBasedUsage(this.folderInfo.host)?"flex":"none"}"
          >
            <div class="horizontal layout center justified">
              <mwc-textfield
                id="modify-folder-quota"
                label="${translate("data.folders.FolderQuota")}"
                value="${this.maxSize.value}"
                type="number"
                min="0"
                step="0.1"
                @change="${()=>this._updateQuotaInputHumanReadableValue()}"
              ></mwc-textfield>
              <mwc-select
                class="fixed-position"
                id="modify-folder-quota-unit"
                @change="${()=>this._updateQuotaInputHumanReadableValue()}"
                fixedMenuPosition
              >
                ${Object.keys(this.quotaUnit).map(((e,t)=>x$1`
                    <mwc-list-item
                      value="${e}"
                      ?selected="${e==this.maxSize.unit}"
                    >
                      ${e}
                    </mwc-list-item>
                  `))}
              </mwc-select>
            </div>
            <span class="helper-text">
              ${translate("data.folders.MaxFolderQuota")} :
              ${this.maxSize.value+" "+this.maxSize.unit}
            </span>
          </div>
          <mwc-select
            class="full-width fixed-position"
            id="update-folder-permission"
            style="width:100%;"
            label="${translate("data.Permission")}"
            fixedMenuPosition
          >
            ${Object.keys(this.permissions).map((e=>x$1`
                <mwc-list-item value="${this.permissions[e]}">
                  ${this.permissions[e]}
                </mwc-list-item>
              `))}
          </mwc-select>
          ${this.enableStorageProxy&&"model"===this.storageType&&this.is_admin?x$1`
                <div
                  id="update-folder-cloneable-container"
                  class="horizontal layout flex wrap center justified"
                >
                  <p style="color:rgba(0, 0, 0, 0.6);margin-left:10px;">
                    ${translate("data.folders.Cloneable")}
                  </p>
                  <mwc-switch
                    id="update-folder-cloneable"
                    style="margin-right:10px;"
                  ></mwc-switch>
                </div>
              `:x$1``}
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            unelevated
            fullwidth
            type="submit"
            icon="edit"
            id="update-button"
            @click="${()=>this._updateFolder()}"
          >
            ${translate("data.Update")}
          </mwc-button>
        </div>
      </backend-ai-dialog>

      <backend-ai-dialog id="modify-folder-name-dialog" fixed backdrop>
        <span slot="title">${translate("data.folders.RenameAFolder")}</span>
        <div slot="content" class="vertical layout flex">
          <mwc-textfield
            id="clone-folder-src"
            label="${translate("data.ExistingFolderName")}"
            value="${this.renameFolderName}"
            disabled
          ></mwc-textfield>
          <mwc-textfield
            class="red"
            id="new-folder-name"
            label="${translate("data.folders.TypeNewFolderName")}"
            pattern="^[a-zA-Z0-9._-]*$"
            autoValidate
            validationMessage="${translate("data.Allowslettersnumbersand-_dot")}"
            maxLength="64"
            placeholder="${get("maxLength.64chars")}"
            @change="${()=>this._validateFolderName(!0)}"
          ></mwc-textfield>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            unelevated
            fullwidth
            type="submit"
            icon="edit"
            id="update-button"
            @click="${()=>this._updateFolderName()}"
          >
            ${translate("data.Update")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="delete-folder-without-confirm-dialog">
        <span slot="title">${translate("data.folders.MoveToTrash")}</span>
        <div slot="content">
          <div>
            ${translate("data.folders.MoveToTrashDescription",{folderName:this.deleteFolderName||""})}
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            raised
            fullwidth
            class="warning fg red"
            type="submit"
            icon="delete"
            id="delete-without-confirm-button"
            @click="${()=>{this._deleteFolder(this.deleteFolderID),this.closeDialog("delete-folder-without-confirm-dialog")}}"
          >
            ${translate("data.folders.MoveToTrash")}
          </mwc-button>
        </div>
      </backend-ai-dialog>

      <backend-ai-dialog id="delete-folder-dialog" fixed backdrop>
        <span slot="title">${translate("data.folders.DeleteAFolder")}</span>
        <div slot="content">
          <div class="warning" style="margin-left:16px;">
            ${translate("dialog.warning.CannotBeUndone")}
          </div>
          <mwc-textfield
            class="red"
            id="delete-folder-name"
            label="${translate("data.folders.TypeFolderNameToDelete")}"
            maxLength="64"
            placeholder="${get("maxLength.64chars")}"
          ></mwc-textfield>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            unelevated
            fullwidth
            type="submit"
            icon="close"
            id="delete-button"
            @click="${()=>this._deleteFolderWithCheck()}"
          >
            ${translate("data.folders.Delete")}
          </mwc-button>
        </div>
      </backend-ai-dialog>

      <backend-ai-dialog id="leave-folder-dialog" fixed backdrop>
        <span slot="title">${translate("data.folders.LeaveAFolder")}</span>
        <div slot="content">
          <div class="warning" style="margin-left:16px;">
            ${translate("dialog.warning.CannotBeUndone")}
          </div>
          <mwc-textfield
            class="red"
            id="leave-folder-name"
            label="${translate("data.folders.TypeFolderNameToLeave")}"
            maxLength="64"
            placeholder="${get("maxLength.64chars")}"
          ></mwc-textfield>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            unelevated
            fullwidth
            type="submit"
            id="leave-button"
            @click="${()=>this._leaveFolderWithCheck()}"
          >
            ${translate("data.folders.Leave")}
          </mwc-button>
        </div>
      </backend-ai-dialog>

      <backend-ai-dialog id="info-folder-dialog" fixed backdrop>
        <span slot="title">${this.folderInfo.name}</span>
        <div slot="content" role="listbox" style="margin: 0;width:100%;">
          <div
            class="horizontal justified layout wrap"
            style="margin-top:15px;"
          >
            <div class="vertical layout center info-indicator">
              <div class="big indicator">${this.folderInfo.host}</div>
              <span>${translate("data.folders.Location")}</span>
            </div>
            ${this.directoryBasedUsage?x$1`
                  <div class="vertical layout center info-indicator">
                    <div class="big indicator">
                      ${this.folderInfo.numFiles<0?"many":this.folderInfo.numFiles}
                    </div>
                    <span>${translate("data.folders.NumberOfFiles")}</span>
                  </div>
                `:x$1``}
          </div>
          <mwc-list>
            <mwc-list-item twoline>
              <span><strong>ID</strong></span>
              <span class="monospace" slot="secondary">
                ${this.folderInfo.id}
              </span>
            </mwc-list-item>
            ${this.folderInfo.is_owner?x$1`
                  <mwc-list-item twoline>
                    <span>
                      <strong>${translate("data.folders.Ownership")}</strong>
                    </span>
                    <span slot="secondary">
                      ${translate("data.folders.DescYouAreFolderOwner")}
                    </span>
                  </mwc-list-item>
                `:x$1``}
            ${"undefined"!==this.folderInfo.usage_mode?x$1`
                  <mwc-list-item twoline>
                    <span><strong>${translate("data.UsageMode")}</strong></span>
                    <span slot="secondary">${this.folderInfo.usage_mode}</span>
                  </mwc-list-item>
                `:x$1``}
            ${this.folderInfo.permission?x$1`
                  <mwc-list-item twoline>
                    <span>
                      <strong>${translate("data.folders.Permission")}</strong>
                    </span>
                    <div slot="secondary" class="horizontal layout">
                      ${this._hasPermission(this.folderInfo,"r")?x$1`
                            <lablup-shields
                              app=""
                              color="green"
                              description="R"
                              ui="flat"
                            ></lablup-shields>
                          `:x$1``}
                      ${this._hasPermission(this.folderInfo,"w")?x$1`
                            <lablup-shields
                              app=""
                              color="blue"
                              description="W"
                              ui="flat"
                            ></lablup-shields>
                          `:x$1``}
                      ${this._hasPermission(this.folderInfo,"d")?x$1`
                            <lablup-shields
                              app=""
                              color="red"
                              description="D"
                              ui="flat"
                            ></lablup-shields>
                          `:x$1``}
                    </div>
                  </mwc-list-item>
                `:x$1``}
            ${this.enableStorageProxy?x$1`
                  <mwc-list-item twoline>
                    <span>
                      <strong>${translate("data.folders.Cloneable")}</strong>
                    </span>
                    <span class="monospace" slot="secondary">
                      ${this.folderInfo.cloneable?x$1`
                            <mwc-icon class="cloneable" style="color:green;">
                              check_circle
                            </mwc-icon>
                          `:x$1`
                            <mwc-icon class="cloneable" style="color:red;">
                              block
                            </mwc-icon>
                          `}
                    </span>
                  </mwc-list-item>
                `:x$1``}
            ${this.directoryBasedUsage&&this._checkFolderSupportDirectoryBasedUsage(this.folderInfo.host)?x$1`
                  <mwc-list-item twoline>
                    <span>
                      <strong>${translate("data.folders.FolderUsage")}</strong>
                    </span>
                    <span class="monospace" slot="secondary">
                      ${translate("data.folders.FolderUsing")}:
                      ${this.folderInfo.used_bytes>=0?globalThis.backendaiutils._humanReadableFileSize(this.folderInfo.used_bytes):"Undefined"}
                      / ${translate("data.folders.FolderQuota")}:
                      ${this.folderInfo.max_size>=0?globalThis.backendaiutils._humanReadableFileSize(this.folderInfo.max_size*this.quotaUnit.MiB):"Undefined"}
                      ${this.folderInfo.used_bytes>=0&&this.folderInfo.max_size>=0?x$1`
                            <vaadin-progress-bar
                              value="${this.folderInfo.used_bytes/this.folderInfo.max_size/2**20}"
                            ></vaadin-progress-bar>
                          `:x$1``}
                    </span>
                  </mwc-list-item>
                `:x$1`
                  <mwc-list-item twoline>
                    <span>
                      <strong>${translate("data.folders.FolderUsage")}</strong>
                    </span>
                    <span class="monospace" slot="secondary">
                      ${translate("data.folders.FolderUsing")}:
                      ${this.folderInfo.used_bytes>=0?globalThis.backendaiutils._humanReadableFileSize(this.folderInfo.used_bytes):"Undefined"}
                    </span>
                  </mwc-list-item>
                `}
          </mwc-list>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog
        id="folder-explorer-dialog"
        class="folder-explorer"
        narrowLayout
        scrimClickAction
        @dialog-closed=${()=>{this.triggerCloseFilebrowserToReact()}}
      >
        <span slot="title" style="margin-right:1rem;">${this.explorer.id}</span>
        <div
          slot="action"
          class="horizontal layout space-between folder-action-buttons center"
        >
          <div class="flex"></div>
          ${this.isWritable?x$1`
                <mwc-button
                  outlined
                  class="multiple-action-buttons fg red"
                  icon="delete"
                  @click="${()=>this._openDeleteMultipleFileDialog()}"
                  style="display:none;"
                >
                  <span>${translate("data.explorer.Delete")}</span>
                </mwc-button>
                <div id="add-btn-cover">
                  <mwc-button
                    id="add-btn"
                    icon="upload_file"
                    ?disabled=${!this.isWritable}
                    @click="${e=>this._uploadBtnClick(e)}"
                  >
                    <span>${translate("data.explorer.UploadFiles")}</span>
                  </mwc-button>
                </div>
                <div>
                  <mwc-button
                    id="add-folder-btn"
                    icon="drive_folder_upload"
                    ?disabled=${!this.isWritable}
                    @click="${e=>this._uploadBtnClick(e)}"
                  >
                    <span>${translate("data.explorer.UploadFolder")}</span>
                  </mwc-button>
                </div>
                <div id="mkdir-cover">
                  <mwc-button
                    id="mkdir"
                    class="tooltip"
                    icon="create_new_folder"
                    ?disabled=${!this.isWritable}
                    @click="${()=>this._mkdirDialog()}"
                  >
                    <span>${translate("data.explorer.NewFolder")}</span>
                  </mwc-button>
                </div>
              `:x$1`
                <mwc-button id="readonly-btn" disabled>
                  <span>${translate("data.explorer.ReadonlyFolder")}</span>
                </mwc-button>
              `}
          <div id="filebrowser-btn-cover">
            <mwc-button
              id="filebrowser-btn"
              @click="${()=>this._executeFileBrowser()}"
            >
              <img
                id="filebrowser-img"
                alt="File Browser"
                src="./resources/icons/filebrowser.svg"
              />
              <span>${translate("data.explorer.ExecuteFileBrowser")}</span>
            </mwc-button>
          </div>
          <div>
            <mwc-button
              id="ssh-btn"
              title="SSH / SFTP"
              @click="${()=>this._executeSSHProxyAgent()}"
            >
              <img
                id="ssh-img"
                alt="SSH / SFTP"
                src="/resources/icons/sftp.png"
              />
              <span>${translate("data.explorer.RunSSH/SFTPserver")}</span>
            </mwc-button>
          </div>
        </div>
        <div slot="content">
          <div class="breadcrumb">
            ${this.explorer.breadcrumb?x$1`
                  <ul>
                    ${this.explorer.breadcrumb.map((e=>x$1`
                        <li>
                          ${"."===e?x$1`
                                <mwc-icon-button
                                  icon="folder_open"
                                  dest="${e}"
                                  @click="${e=>this._gotoFolder(e)}"
                                ></mwc-icon-button>
                              `:x$1`
                                <a
                                  outlined
                                  class="goto"
                                  path="item"
                                  @click="${e=>this._gotoFolder(e)}"
                                  dest="${e}"
                                >
                                  ${e}
                                </a>
                              `}
                        </li>
                      `))}
                  </ul>
                `:x$1``}
          </div>
          <div id="dropzone"><p>drag</p></div>
          <input
            type="file"
            id="fileInput"
            @change="${e=>this._uploadInputChange(e)}"
            hidden
            multiple
          />
          <input
            type="file"
            id="folderInput"
            @change="${e=>this._uploadInputChange(e)}"
            hidden
            webkitdirectory
            mozdirectory
            directory
            multiple
          />
          ${this.uploadFilesExist?x$1`
                <div class="horizontal layout start-justified">
                  <mwc-button
                    icon="cancel"
                    id="cancel_upload"
                    @click="${()=>this._cancelUpload()}"
                  >
                    ${translate("data.explorer.StopUploading")}
                  </mwc-button>
                </div>
                <div class="horizontal layout center progress-item flex">
                  ${(null===(e=this.currentUploadFile)||void 0===e?void 0:e.complete)?x$1`
                        <mwc-icon>check</mwc-icon>
                      `:x$1``}
                  <div
                    class="vertical layout progress-item"
                    style="width:100%;"
                  >
                    <span>${null===(t=this.currentUploadFile)||void 0===t?void 0:t.name}</span>
                    <vaadin-progress-bar
                      value="${null===(i=this.currentUploadFile)||void 0===i?void 0:i.progress}"
                    ></vaadin-progress-bar>
                    <span>${null===(o=this.currentUploadFile)||void 0===o?void 0:o.caption}</span>
                  </div>
                </div>
                <!-- <vaadin-grid class="progress" theme="row-stripes compact" aria-label="uploadFiles" .items="${this.uploadFiles}" height-by-rows>
            <vaadin-grid-column width="100px" flex-grow="0" .renderer="${this._boundUploadListRenderer}"></vaadin-grid-column>
            <vaadin-grid-column .renderer="${this._boundUploadProgressRenderer}"></vaadin-grid-column>
          </vaadin-grid> -->
              `:x$1``}
          <vaadin-grid
            id="file-list-grid"
            class="explorer"
            theme="row-stripes compact dark"
            aria-label="Explorer"
            .items="${this.explorerFiles}"
          >
            <vaadin-grid-selection-column
              auto-select
            ></vaadin-grid-selection-column>
            <vaadin-grid-column
              width="40px"
              flex-grow="0"
              resizable
              header="#"
              .renderer="${this._boundIndexRenderer}"
            ></vaadin-grid-column>
            <vaadin-grid-sort-column
              flex-grow="2"
              resizable
              header="${translate("data.explorer.Name")}"
              path="filename"
              .renderer="${this._boundFileNameRenderer}"
            ></vaadin-grid-sort-column>
            <vaadin-grid-sort-column
              flex-grow="2"
              resizable
              header="${translate("data.explorer.Created")}"
              path="ctime"
              .renderer="${this._boundCreatedTimeRenderer}"
            ></vaadin-grid-sort-column>
            <vaadin-grid-sort-column
              auto-width
              resizable
              header="${translate("data.explorer.Size")}"
              path="size"
              .renderer="${this._boundSizeRenderer}"
            ></vaadin-grid-sort-column>
            <vaadin-grid-column
              resizable
              auto-width
              header="${translate("data.explorer.Actions")}"
              .renderer="${this._boundControlFileListRenderer}"
            ></vaadin-grid-column>
          </vaadin-grid>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="mkdir-dialog" fixed backdrop>
        <span slot="title">${translate("data.explorer.CreateANewFolder")}</span>
        <div slot="content">
          <mwc-textfield
            id="mkdir-name"
            label="${translate("data.explorer.Foldername")}"
            @change="${()=>this._validatePathName()}"
            required
            maxLength="255"
            placeholder="${get("maxLength.255chars")}"
            validationMessage="${get("data.explorer.ValueRequired")}"
          ></mwc-textfield>
          <br />
        </div>
        <div
          slot="footer"
          class="horizontal center-justified flex layout distancing"
        >
          <mwc-button
            icon="rowing"
            unelevated
            fullwidth
            type="submit"
            id="mkdir-btn"
            @click="${e=>this._mkdir(e)}"
          >
            ${translate("button.Create")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="share-folder-dialog" fixed backdrop>
        <span slot="title">${translate("data.explorer.ShareFolder")}</span>
        <div slot="content" role="listbox" style="margin: 0;width:100%;">
          <div style="margin: 10px 0px">${translate("data.explorer.People")}</div>
          <div class="vertical layout flex" id="textfields">
            <div class="horizontal layout">
              <div style="flex-grow: 2">
                <mwc-textfield
                  class="share-email"
                  type="email"
                  id="first-email"
                  label="${translate("data.explorer.EnterEmailAddress")}"
                  maxLength="64"
                  placeholder="${get("maxLength.64chars")}"
                ></mwc-textfield>
              </div>
              <div>
                <mwc-icon-button
                  icon="add"
                  @click="${()=>this._addTextField()}"
                ></mwc-icon-button>
                <mwc-icon-button
                  icon="remove"
                  @click="${()=>this._removeTextField()}"
                ></mwc-icon-button>
              </div>
            </div>
          </div>
          <div style="margin: 10px 0px">${translate("data.explorer.Permissions")}</div>
          <div style="display: flex; justify-content: space-evenly;">
            <mwc-formfield label="${translate("data.folders.View")}">
              <mwc-radio
                name="share-folder-permission"
                checked
                value="ro"
              ></mwc-radio>
            </mwc-formfield>
            <mwc-formfield label="${translate("data.folders.Edit")}">
              <mwc-radio name="share-folder-permission" value="rw"></mwc-radio>
            </mwc-formfield>
            <mwc-formfield label="${translate("data.folders.EditDelete")}">
              <mwc-radio name="share-folder-permission" value="wd"></mwc-radio>
            </mwc-formfield>
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            icon="share"
            type="button"
            unelevated
            fullwidth
            id="share-button"
            @click=${e=>this._shareFolder(e)}
          >
            ${translate("button.Share")}
          </mwc-button>
        </div>
      </backend-ai-dialog>

      <backend-ai-dialog id="modify-permission-dialog" fixed backdrop>
        <span slot="title">${translate("data.explorer.ModifyPermissions")}</span>
        <div slot="content" role="listbox" style="margin: 0; padding: 10px;">
          <vaadin-grid
            theme="row-stripes column-borders compact dark"
            .items="${this.invitees}"
          >
            <vaadin-grid-column
              width="30px"
              flex-grow="0"
              header="#"
              .renderer="${this._boundIndexRenderer}"
            ></vaadin-grid-column>
            <vaadin-grid-column
              header="${translate("data.explorer.InviteeEmail")}"
              .renderer="${this._boundInviteeInfoRenderer}"
            ></vaadin-grid-column>
            <vaadin-grid-column
              header="${translate("data.explorer.Permission")}"
              .renderer="${this._boundPermissionRenderer}"
            ></vaadin-grid-column>
          </vaadin-grid>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            icon="check"
            type="button"
            unelevated
            fullwidth
            @click=${()=>this._modifySharedFolderPermissions()}
          >
            ${translate("button.SaveChanges")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="rename-file-dialog" fixed backdrop blockscrolling>
        <span slot="title">${translate("data.explorer.RenameAFile")}</span>
        <div slot="content">
          <mwc-textfield
            class="red"
            id="new-file-name"
            label="${translate("data.explorer.NewFileName")}"
            required
            @change="${()=>this._validateExistingFileName()}"
            auto-validate
            style="width:320px;"
            maxLength="255"
            placeholder="${get("maxLength.255chars")}"
            autoFocus
          ></mwc-textfield>
          <div id="old-file-name" style="padding-left:15px;height:2.5em;"></div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            icon="edit"
            fullwidth
            type="button"
            id="rename-file-button"
            unelevated
            @click="${()=>this._compareFileExtension()}"
          >
            ${translate("data.explorer.RenameAFile")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="delete-file-dialog" fixed backdrop>
        <span slot="title">${translate("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>
            ${translate("dialog.warning.CannotBeUndone")}
            ${translate("dialog.ask.DoYouWantToProceed")}
          </p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button outlined @click="${e=>this._hideDialog(e)}">
            ${translate("button.Cancel")}
          </mwc-button>
          <mwc-button raised @click="${e=>this._deleteFileWithCheck(e)}">
            ${translate("button.Okay")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="download-file-dialog" fixed backdrop>
        <span slot="title">${translate("data.explorer.DownloadFile")}</span>
        <div slot="content">
          <a href="${this.downloadURL}">
            <mwc-button outlined>
              ${translate("data.explorer.TouchToDownload")}
            </mwc-button>
          </a>
        </div>
        <div
          slot="footer"
          class="horizontal end-justified flex layout distancing"
        >
          <mwc-button @click="${e=>this._hideDialog(e)}">
            ${translate("button.Close")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="file-extension-change-dialog" fixed backdrop>
        <span slot="title">${translate("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${translate("data.explorer.FileExtensionChanged")}</p>
        </div>
        <div
          slot="footer"
          class="horizontal center-justified flex layout distancing"
        >
          <mwc-button
            outlined
            fullwidth
            @click="${e=>this._keepFileExtension()}"
          >
            ${"ko"!==globalThis.backendaioptions.get("language","default","general")?x$1`
                  ${get("data.explorer.KeepFileExtension")+this.oldFileExtension}
                `:x$1`
                  ${this.oldFileExtension+get("data.explorer.KeepFileExtension")}
                `}
          </mwc-button>
          <mwc-button unelevated fullwidth @click="${()=>this._renameFile()}">
            ${"ko"!==globalThis.backendaioptions.get("language","default","general")?x$1`
                  ${this.newFileExtension?get("data.explorer.UseNewFileExtension")+this.newFileExtension:get("data.explorer.RemoveFileExtension")}
                `:x$1`
                  ${this.newFileExtension?this.newFileExtension+get("data.explorer.UseNewFileExtension"):get("data.explorer.RemoveFileExtension")}
                `}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog
        id="filebrowser-notification-dialog"
        fixed
        backdrop
        narrowLayout
      >
        <span slot="title">${translate("dialog.title.Notice")}</span>
        <div slot="content" style="margin: 15px;">
          <span>${translate("data.explorer.ReadOnlyFolderOnFileBrowser")}</span>
        </div>
        <div
          slot="footer"
          class="flex horizontal layout center justified"
          style="margin: 15px 15px 15px 0px;"
        >
          <div class="horizontal layout start-justified center">
            <mwc-checkbox
              @change="${e=>this._toggleShowFilebrowserNotification(e)}"
            ></mwc-checkbox>
            <span style="font-size:0.8rem;">
              ${get("dialog.hide.DonotShowThisAgain")}
            </span>
          </div>
          <mwc-button unelevated @click="${e=>this._hideDialog(e)}">
            ${translate("button.Confirm")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="delete-from-trash-bin-dialog" fixed backdrop>
        <span slot="title">${translate("dialog.title.DeleteForever")}</span>
        <div slot="content">
          <div class="warning">${translate("dialog.warning.DeleteForeverDesc")}</div>
          <mwc-textfield
            class="red"
            id="delete-from-trash-bin-name-input"
            label="${translate("data.folders.TypeFolderNameToDelete")}"
            maxLength="64"
            placeholder="${get("maxLength.64chars")}"
          ></mwc-textfield>
        </div>
        <div
          slot="footer"
          class="horizontal end-justified flex layout"
          style="gap:5px;"
        >
          <mwc-button outlined @click="${e=>this._hideDialog(e)}">
            ${translate("button.Cancel")}
          </mwc-button>
          <mwc-button
            raised
            class="warning fg red"
            @click="${()=>this._deleteFromTrashBin()}"
          >
            ${translate("data.folders.DeleteForever")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
    `}firstUpdated(){var e,t,i;this._addEventListenerDropZone(),this._mkdir=this._mkdir.bind(this),this.fileListGrid.addEventListener("selected-items-changed",(()=>{this._toggleFileListCheckbox()})),this.indicator=globalThis.lablupIndicator,this.notification=globalThis.lablupNotification;const o=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll("mwc-textfield");for(const e of Array.from(o))this._addInputValidator(e);["data","automount","model"].includes(this.storageType)?(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("vaadin-grid.folderlist")).style.height="calc(100vh - 464px)":(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("vaadin-grid.folderlist")).style.height="calc(100vh - 420px)",document.addEventListener("backend-ai-group-changed",(e=>this._refreshFolderList(!0,"group-changed"))),document.addEventListener("backend-ai-ui-changed",(e=>this._refreshFolderUI(e))),this._refreshFolderUI({detail:{"mini-ui":globalThis.mini_ui}})}_modifySharedFolderPermissions(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll("#modify-permission-dialog mwc-select"),i=Array.prototype.filter.call(t,((e,t)=>e.value!==this.invitees[t].perm)).map(((e,t)=>({perm:"kickout"===e.value?null:e.value,user:this.invitees[t].shared_to.uuid,vfolder:this.invitees[t].vfolder_id}))).map((e=>globalThis.backendaiclient.vfolder.modify_invitee_permission(e)));Promise.all(i).then((e=>{0===e.length?this.notification.text=get("data.permission.NoChanges"):this.notification.text=get("data.permission.PermissionModified"),this.notification.show(),this.modifyPermissionDialog.hide()}))}_isUncontrollableStatus(e){return["performing","cloning","mounted","error","delete-pending","delete-ongoing","deleted-complete","delete-error","purge-ongoing","deleting"].includes(e)}_isDeadVFolderStatus(e){return["delete-pending","delete-ongoing","delete-complete","delete-error","deleting"].includes(e)}_moveTo(e=""){const t=""!==e?e:"summary";store.dispatch(navigate(decodeURIComponent(t),{})),document.dispatchEvent(new CustomEvent("react-navigate",{detail:e}))}permissionRenderer(e,t,i){j(x$1`
        <mwc-select label="${translate("data.folders.SelectPermission")}">
          <mwc-list-item value="ro" ?selected="${"ro"===i.item.perm}">
            ${translate("data.folders.View")}
          </mwc-list-item>
          <mwc-list-item value="rw" ?selected="${"rw"===i.item.perm}">
            ${translate("data.folders.Edit")}
          </mwc-list-item>
          <mwc-list-item value="wd" ?selected="${"wd"===i.item.perm}">
            ${translate("data.folders.EditDelete")}
          </mwc-list-item>
          <mwc-list-item value="kickout"">
            ${translate("data.folders.KickOut")}
          </mwc-list-item>
        </mwc-select>
      `,e)}folderListRenderer(e,t,i){j(x$1`
        <div
          class="controls layout flex horizontal start-justified center wrap"
          folder-id="${i.item.id}"
          folder-name="${i.item.name}"
          folder-type="${i.item.type}"
        >
          ${this._hasPermission(i.item,"r")?x$1`
                <mwc-icon-button
                  class="fg blue controls-running"
                  icon="folder_open"
                  title=${translate("data.folders.OpenAFolder")}
                  @click="${()=>{this.triggerOpenFilebrowserToReact(i)}}"
                  ?disabled="${this._isUncontrollableStatus(i.item.status)}"
                  .folder-id="${i.item.name}"
                ></mwc-icon-button>
              `:x$1``}
          <div
            @click="${e=>!this._isUncontrollableStatus(i.item.status)&&this.triggerOpenFilebrowserToReact(i)}"
            .folder-id="${i.item.name}"
            style="cursor:${this._isUncontrollableStatus(i.item.status)?"default":"pointer"};"
          >
            ${i.item.name}
          </div>
        </div>
      `,e)}quotaRenderer(e,t,i){let o="-";this._checkFolderSupportDirectoryBasedUsage(i.item.host)&&i.item.max_size&&(o=globalThis.backendaiutils._humanReadableFileSize(i.item.max_size*this.quotaUnit.MiB)),j(x$1`
        <div class="horizontal layout center center-justified">
          ${o}
        </div>
      `,e)}uploadListRenderer(e,t,i){j(x$1`
        <vaadin-item class="progress-item">
          <div>
            ${i.item.complete?x$1`
                  <mwc-icon>check</mwc-icon>
                `:x$1``}
          </div>
        </vaadin-item>
      `,e)}uploadProgressRenderer(e,t,i){j(x$1`
        <vaadin-item>
          <span>${i.item.name}</span>
          ${i.item.complete?x$1``:x$1`
                <div>
                  <vaadin-progress-bar
                    value="${i.item.progress}"
                  ></vaadin-progress-bar>
                </div>
                <div>
                  <span>${i.item.caption}</span>
                </div>
              `}
        </vaadin-item>
      `,e)}inviteeInfoRenderer(e,t,i){j(x$1`
        <div>${i.item.shared_to.email}</div>
      `,e)}iDRenderer(e,t,i){j(x$1`
        <div class="layout vertical">
          <span class="indicator monospace">${i.item.id}</span>
        </div>
      `,e)}statusRenderer(e,t,i){let o;switch(i.item.status){case"ready":o="green";break;case"performing":case"cloning":case"mounted":o="blue";break;case"delete-ongoing":o="yellow";break;default:o="grey"}j(x$1`
        <lablup-shields
          app=""
          color="${o}"
          description="${i.item.status}"
          ui="flat"
        ></lablup-shields>
      `,e)}_addTextField(){var e,t;const i=document.createElement("mwc-textfield");i.label=get("data.explorer.EnterEmailAddress"),i.type="email",i.className="share-email",i.style.width="auto",i.style.marginRight="83px",null===(t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#textfields"))||void 0===t||t.appendChild(i)}_removeTextField(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#textfields");t.children.length>1&&t.lastChild&&t.removeChild(t.lastChild)}indexRenderer(e,t,i){j(x$1`
        ${this._indexFrom1(i.index)}
      `,e)}controlFolderListRenderer(e,t,i){var o;const r=(null!==(o=this._unionedAllowedPermissionByVolume[i.item.host])&&void 0!==o?o:[]).includes("invite-others")&&!i.item.name.startsWith(".");j(x$1`
        <div
          class="controls layout flex center wrap"
          folder-id="${i.item.id}"
          folder-name="${i.item.name}"
          folder-type="${i.item.type}"
        >
          ${this.enableInferenceWorkload&&"model"==i.item.usage_mode?x$1`
                <mwc-icon-button
                  class="fg green controls-running"
                  icon="play_arrow"
                  @click="${e=>this._moveTo("/service/start?model="+i.item.id)}"
                  ?disabled="${this._isUncontrollableStatus(i.item.status)}"
                  id="${i.item.id+"-serve"}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.item.id+"-serve"}"
                  text="${translate("data.folders.Serve")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:x$1``}
          <mwc-icon-button
            class="fg green controls-running"
            icon="info"
            @click="${e=>this._infoFolder(e)}"
            ?disabled="${this._isUncontrollableStatus(i.item.status)}"
            id="${i.item.id+"-folderinfo"}"
          ></mwc-icon-button>
          <vaadin-tooltip
            for="${i.item.id+"-folderinfo"}"
            text="${translate("data.folders.FolderInfo")}"
            position="top-start"
          ></vaadin-tooltip>
          <!--${this._hasPermission(i.item,"r")&&this.enableStorageProxy?x$1`
                <mwc-icon-button
                  class="fg blue controls-running"
                  icon="content_copy"
                  ?disabled=${!i.item.cloneable}
                  @click="${()=>{this._requestCloneFolder(i.item)}}"
                  id="${i.item.id+"-clone"}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.item.id+"-clone"}"
                  text="${translate("data.folders.CloneFolder")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:x$1``}-->
          ${i.item.is_owner?x$1`
                <mwc-icon-button
                  class="fg ${"user"==i.item.type?"blue":"green"} controls-running"
                  icon="share"
                  @click="${e=>this._shareFolderDialog(e)}"
                  ?disabled="${this._isUncontrollableStatus(i.item.status)}"
                  style="display: ${r?"":"none"}"
                  id="${i.item.id+"-share"}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.item.id+"-share"}"
                  text="${translate("data.folders.ShareFolder")}"
                  position="top-start"
                ></vaadin-tooltip>
                <mwc-icon-button
                  class="fg blue controls-running"
                  icon="perm_identity"
                  @click=${e=>this._modifyPermissionDialog(i.item.id)}
                  ?disabled="${this._isUncontrollableStatus(i.item.status)}"
                  style="display: ${r?"":"none"}"
                  id="${i.item.id+"-modifypermission"}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.item.id+"-modifypermission"}"
                  text="${translate("data.folders.ModifyPermissions")}"
                  position="top-start"
                ></vaadin-tooltip>
                <mwc-icon-button
                  class="fg ${"user"==i.item.type?"blue":"green"} controls-running"
                  icon="create"
                  @click="${e=>this._renameFolderDialog(e)}"
                  ?disabled="${this._isUncontrollableStatus(i.item.status)}"
                  id="${i.item.id+"-rename"}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.item.id+"-rename"}"
                  text="${translate("data.folders.Rename")}"
                  position="top-start"
                ></vaadin-tooltip>
                <mwc-icon-button
                  class="fg blue controls-running"
                  icon="settings"
                  @click="${e=>this._modifyFolderOptionDialog(e)}"
                  ?disabled="${this._isUncontrollableStatus(i.item.status)}"
                  id="${i.item.id+"-optionupdate"}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.item.id+"-optionupdate"}"
                  text="${translate("data.folders.FolderOptionUpdate")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:x$1``}
          ${i.item.is_owner||this._hasPermission(i.item,"d")||"group"===i.item.type&&this.is_admin?x$1`
                <mwc-icon-button
                  class="fg ${this.enableVfolderTrashBin?"blue":"red"} controls-running"
                  icon="delete"
                  @click="${e=>this._deleteFolderDialog(e)}"
                  ?disabled="${this._isUncontrollableStatus(i.item.status)}"
                  id="${i.item.id+"-delete"}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.item.id+"-delete"}"
                  text="${translate("data.folders.MoveToTrash")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:x$1``}
          ${i.item.is_owner||"user"!=i.item.type?x$1``:x$1`
                <mwc-icon-button
                  class="fg red controls-running"
                  icon="remove_circle"
                  @click="${e=>this._leaveInvitedFolderDialog(e)}"
                  ?disabled="${this._isUncontrollableStatus(i.item.status)}"
                  id="${i.item.id+"-leavefolder"}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.item.id+"-leavefolder"}"
                  text="${translate("data.folders.LeaveFolder")}"
                  position="top-start"
                ></vaadin-tooltip>
              `}
        </div>
      `,e)}trashBinControlFolderListRenderer(e,t,i){j(x$1`
        <div
          class="controls layout flex center wrap"
          folder-id="${i.item.id}"
          folder-name="${i.item.name}"
          folder-type="${i.item.type}"
        >
          <mwc-icon-button
            class="fg green controls-running"
            icon="info"
            @click="${e=>this._infoFolder(e)}"
            id="${i.item.id+"-folderinfo"}"
          ></mwc-icon-button>
          <vaadin-tooltip
            for="${i.item.id+"-folderinfo"}"
            text="${translate("data.folders.FolderInfo")}"
            position="top-start"
          ></vaadin-tooltip>
          ${i.item.is_owner||this._hasPermission(i.item,"d")||"group"===i.item.type&&this.is_admin?x$1`
                <mwc-icon-button
                  class="fg blue controls-running"
                  icon="redo"
                  ?disabled=${"delete-pending"!==i.item.status}
                  @click="${e=>this._restoreFolder(e)}"
                  id="${i.item.id+"-restore"}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.item.id+"-restore"}"
                  text="${translate("data.folders.Restore")}"
                  position="top-start"
                ></vaadin-tooltip>
                <mwc-icon-button
                  class="fg red controls-running"
                  icon="delete_forever"
                  ?disabled=${"delete-pending"!==i.item.status}
                  @click="${e=>{this.openDeleteFromTrashBinDialog(e)}}"
                  id="${i.item.id+"-delete-forever"}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.item.id+"-delete-forever"}"
                  text="${translate("data.folders.DeleteForever")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:x$1``}
        </div>
      `,e)}controlFileListRenderer(e,t,i){j(x$1`
        <div class="flex layout wrap">
          <mwc-icon-button
            id="${i.item.filename+"-download-btn"}"
            class="tiny fg blue"
            icon="cloud_download"
            style="pointer-events: auto !important;"
            ?disabled="${!this._isDownloadable(this.vhost)}"
            filename="${i.item.filename}"
            @click="${e=>this._downloadFile(e,this._isDir(i.item))}"
          ></mwc-icon-button>
          ${this._isDownloadable(this.vhost)?x$1``:x$1`
                <vaadin-tooltip
                  for="${i.item.filename+"-download-btn"}"
                  text="${translate("data.explorer.DownloadNotAllowed")}"
                  position="top-start"
                ></vaadin-tooltip>
              `}
          <mwc-icon-button
            id="rename-btn"
            ?disabled="${!this.isWritable}"
            class="tiny fg green"
            icon="edit"
            required
            filename="${i.item.filename}"
            @click="${e=>this._openRenameFileDialog(e,this._isDir(i.item))}"
          ></mwc-icon-button>
          <mwc-icon-button
            id="delete-btn"
            ?disabled="${!this.isWritable}"
            class="tiny fg red"
            icon="delete_forever"
            filename="${i.item.filename}"
            @click="${e=>this._openDeleteFileDialog(e)}"
          ></mwc-icon-button>
        </div>
      `,e)}fileNameRenderer(e,t,i){j(x$1`
        ${this._isDir(i.item)?x$1`
              <div
                class="indicator horizontal center layout"
                name="${i.item.filename}"
              >
                <mwc-icon-button
                  class="fg controls-running"
                  icon="folder_open"
                  name="${i.item.filename}"
                  @click="${e=>this._enqueueFolder(e)}"
                ></mwc-icon-button>
                ${i.item.filename}
              </div>
            `:x$1`
              <div class="indicator horizontal center layout">
                <mwc-icon-button
                  class="fg controls-running"
                  icon="insert_drive_file"
                ></mwc-icon-button>
                ${i.item.filename}
              </div>
            `}
      `,e)}permissionViewRenderer(e,t,i){j(x$1`
        <div class="horizontal center-justified wrap layout">
          ${this._hasPermission(i.item,"r")?x$1`
                <lablup-shields
                  app=""
                  color="green"
                  description="R"
                  ui="flat"
                ></lablup-shields>
              `:x$1``}
          ${this._hasPermission(i.item,"w")?x$1`
                <lablup-shields
                  app=""
                  color="blue"
                  description="W"
                  ui="flat"
                ></lablup-shields>
              `:x$1``}
          ${this._hasPermission(i.item,"d")?x$1`
                <lablup-shields
                  app=""
                  color="red"
                  description="D"
                  ui="flat"
                ></lablup-shields>
              `:x$1``}
        </div>
      `,e)}OwnerRenderer(e,t,i){j(x$1`
        ${i.item.is_owner?x$1`
              <div
                class="horizontal center-justified center layout"
                style="pointer-events: none;"
              >
                <mwc-icon-button class="fg green" icon="done"></mwc-icon-button>
              </div>
            `:x$1``}
      `,e)}CloneableRenderer(e,t,i){j(x$1`
        ${i.item.cloneable?x$1`
              <div
                class="horizontal center-justified center layout"
                style="pointer-events: none;"
              >
                <mwc-icon-button class="fg green" icon="done"></mwc-icon-button>
              </div>
            `:x$1``}
      `,e)}createdTimeRenderer(e,t,i){j(x$1`
        <div class="layout vertical">
          <span>${this._humanReadableTime(i.item.ctime)}</span>
        </div>
      `,e)}sizeRenderer(e,t,i){j(x$1`
        <div class="layout horizontal">
          ${"DIRECTORY"!==i.item.type.toUpperCase()||this._isDirectorySizeVisible?x$1`
                <span>${i.item.size}</span>
              `:x$1`
                <span class="monospace">-</span>
              `}
        </div>
      `,e)}typeRenderer(e,t,i){j(x$1`
        <div class="layout vertical center-justified">
          ${"user"==i.item.type?x$1`
                <mwc-icon>person</mwc-icon>
              `:x$1`
                <mwc-icon class="fg green">group</mwc-icon>
              `}
        </div>
      `,e)}async _getCurrentKeypairResourcePolicy(){const e=globalThis.backendaiclient._config.accessKey;return(await globalThis.backendaiclient.keypair.info(e,["resource_policy"])).keypair.resource_policy}async _getVolumeInformation(){const e=await globalThis.backendaiclient.vfolder.list_hosts();this.volumeInfo=e.volume_info||{}}async _getAllowedVFolderHostsByCurrentUserInfo(){var e,t;const[i,o]=await Promise.all([globalThis.backendaiclient.vfolder.list_hosts(),this._getCurrentKeypairResourcePolicy()]),r=globalThis.backendaiclient._config.domainName,a=globalThis.backendaiclient.current_group_id(),n=await globalThis.backendaiclient.storageproxy.getAllowedVFolderHostsByCurrentUserInfo(r,a,o),s=JSON.parse((null===(e=null==n?void 0:n.domain)||void 0===e?void 0:e.allowed_vfolder_hosts)||"{}"),l=JSON.parse((null===(t=null==n?void 0:n.group)||void 0===t?void 0:t.allowed_vfolder_hosts)||"{}"),d=JSON.parse((null==n?void 0:n.keypair_resource_policy.allowed_vfolder_hosts)||"{}");this._unionedAllowedPermissionByVolume=Object.assign({},...i.allowed.map((e=>{return{[e]:(t=[s[e],l[e],d[e]],[...new Set([].concat(...t))])};var t}))),this.folderListGrid.clearCache()}_checkFolderSupportDirectoryBasedUsage(e){var t;if(!e||globalThis.backendaiclient.supports("deprecated-max-quota-scope-in-keypair-resource-policy"))return!1;const i=null===(t=this.volumeInfo[e])||void 0===t?void 0:t.backend;return this.quotaSupportStorageBackends.includes(i)}async refreshFolderList(){return this._triggerFolderListChanged(),this.folderListGrid&&this.folderListGrid.clearCache(),await this._refreshFolderList(!0,"refreshFolderList")}_refreshFolderList(e=!1,t="unknown"){var i;if(this._folderRefreshing||!this.active)return;if(Date.now()-this.lastQueryTime<1e3)return;this._folderRefreshing=!0,this.lastQueryTime=Date.now(),this.listCondition="loading",null===(i=this._listStatus)||void 0===i||i.show(),this._getMaxSize();let o=null;o=globalThis.backendaiclient.current_group_id(),globalThis.backendaiclient.vfolder.list(o).then((e=>{var t;let i=e.filter((e=>(this.enableInferenceWorkload||"general"!==this.storageType||e.name.startsWith(".")||"model"!=e.usage_mode)&&("general"!==this.storageType||e.name.startsWith(".")||"general"!=e.usage_mode)&&("data"!==this.storageType||e.name.startsWith(".")||"data"!=e.usage_mode)?"automount"===this.storageType&&e.name.startsWith(".")?e:"model"!==this.storageType||e.name.startsWith(".")||"model"!=e.usage_mode?"deadVFolderStatus"===this.storageType&&this._isDeadVFolderStatus(e.status)?e:void 0:e:e));"deadVFolderStatus"!==this.storageType&&(i=i.filter((e=>!this._isDeadVFolderStatus(e.status)))),i=i.filter((e=>"delete-complete"!==e.status)),this.folders=i,this._triggerFolderListChanged(),0==this.folders.length?this.listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide(),this._folderRefreshing=!1})).catch((()=>{this._folderRefreshing=!1})),globalThis.backendaiclient.vfolder.list_hosts().then((t=>{this.active&&!e&&setTimeout((()=>{this._refreshFolderList(!1,"loop")}),3e4)}))}_refreshFolderUI(e){Object.prototype.hasOwnProperty.call(e.detail,"mini-ui")&&!0===e.detail["mini-ui"]?this.folderExplorerDialog.classList.add("mini_ui"):this.folderExplorerDialog.classList.remove("mini_ui")}async _checkImageSupported(){const e=(await globalThis.backendaiclient.image.list(["name","tag","registry","digest","installed","labels { key value }","resource_limits { key min max }"],!0,!0)).images;this.filebrowserSupportedImages=e.filter((e=>e.labels.find((e=>"ai.backend.service-ports"===e.key&&e.value.toLowerCase().includes("filebrowser"))))),this.systemRoleSupportedImages=e.filter((e=>e.labels.find((e=>"ai.backend.role"===e.key&&e.value.toLowerCase().includes("system")))))}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(async()=>{this.is_admin=globalThis.backendaiclient.is_admin,this.enableStorageProxy=globalThis.backendaiclient.supports("storage-proxy"),this.enableInferenceWorkload=globalThis.backendaiclient.supports("inference-workload"),this.enableVfolderTrashBin=globalThis.backendaiclient.supports("vfolder-trash-bin"),this.authenticated=!0,this._APIMajorVersion=globalThis.backendaiclient.APIMajorVersion,this._maxFileUploadSize=globalThis.backendaiclient._config.maxFileUploadSize,this.directoryBasedUsage=globalThis.backendaiclient._config.directoryBasedUsage&&!globalThis.backendaiclient.supports("deprecated-max-quota-scope-in-keypair-resource-policy"),this._isDirectorySizeVisible=globalThis.backendaiclient._config.isDirectorySizeVisible,this._getAllowedVFolderHostsByCurrentUserInfo(),this._checkImageSupported(),this._getVolumeInformation(),this._refreshFolderList(!1,"viewStatechanged")}),!0):(this.is_admin=globalThis.backendaiclient.is_admin,this.enableStorageProxy=globalThis.backendaiclient.supports("storage-proxy"),this.enableInferenceWorkload=globalThis.backendaiclient.supports("inference-workload"),this.enableVfolderTrashBin=globalThis.backendaiclient.supports("vfolder-trash-bin"),this.authenticated=!0,this._APIMajorVersion=globalThis.backendaiclient.APIMajorVersion,this._maxFileUploadSize=globalThis.backendaiclient._config.maxFileUploadSize,this.directoryBasedUsage=globalThis.backendaiclient._config.directoryBasedUsage&&!globalThis.backendaiclient.supports("deprecated-max-quota-scope-in-keypair-resource-policy"),this._isDirectorySizeVisible=globalThis.backendaiclient._config.isDirectorySizeVisible,this._getAllowedVFolderHostsByCurrentUserInfo(),this._checkImageSupported(),this._getVolumeInformation(),this._refreshFolderList(!1,"viewStatechanged")))}_folderExplorerDialog(){this.openDialog("folder-explorer-dialog")}_mkdirDialog(){this.mkdirNameInput.value="",this.openDialog("mkdir-dialog")}openDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).show()}closeDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).hide()}_indexFrom1(e){return e+1}_hasPermission(e,t){return!!e.permission.includes(t)||!(!e.permission.includes("w")||"r"!==t)}_getControlName(e){return e.target.closest(".controls").getAttribute("folder-name")}_getControlID(e){return e.target.closest(".controls").getAttribute("folder-id")}_getControlType(e){return e.target.closest(".controls").getAttribute("folder-type")}_infoFolder(e){const t=this._getControlName(e);globalThis.backendaiclient.vfolder.info(t).then((e=>{this.folderInfo=e,this.openDialog("info-folder-dialog")})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=BackendAIPainKiller.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_modifyFolderOptionDialog(e){globalThis.backendaiclient.vfolder.name=this._getControlName(e);globalThis.backendaiclient.vfolder.info(globalThis.backendaiclient.vfolder.name).then((e=>{this.folderInfo=e;const t=this.folderInfo.permission;let i=Object.keys(this.permissions).indexOf(t);i=i>0?i:0,this.updateFolderPermissionSelect.select(i),this.updateFolderCloneableSwitch&&(this.updateFolderCloneableSwitch.selected=this.folderInfo.cloneable),this.directoryBasedUsage&&this._checkFolderSupportDirectoryBasedUsage(this.folderInfo.host)&&([this.quota.value,this.quota.unit]=globalThis.backendaiutils._humanReadableFileSize(this.folderInfo.max_size*this.quotaUnit.MiB).split(" "),this.modifyFolderQuotaInput.value=this.quota.value.toString(),this.modifyFolderQuotaUnitSelect.value="Bytes"==this.quota.unit?"MB":this.quota.unit),this.openDialog("modify-folder-dialog")})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=BackendAIPainKiller.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}async _updateFolder(){var e;let t=!1,i=!1;const o={};if(this.updateFolderPermissionSelect){let t=this.updateFolderPermissionSelect.value;t=null!==(e=Object.keys(this.permissions).find((e=>this.permissions[e]===t)))&&void 0!==e?e:"",t&&this.folderInfo.permission!==t&&(o.permission=t)}this.updateFolderCloneableSwitch&&(i=this.updateFolderCloneableSwitch.selected,o.cloneable=i);const r=[];if(Object.keys(o).length>0){const e=globalThis.backendaiclient.vfolder.update_folder(o,globalThis.backendaiclient.vfolder.name);r.push(e)}if(this.directoryBasedUsage&&this._checkFolderSupportDirectoryBasedUsage(this.folderInfo.host)){const e=this.modifyFolderQuotaInput.value?BigInt(Number(this.modifyFolderQuotaInput.value)*this.quotaUnit[this.modifyFolderQuotaUnitSelect.value]).toString():"0";if(this.quota.value!=Number(this.modifyFolderQuotaInput.value)||this.quota.unit!=this.modifyFolderQuotaUnitSelect.value){const t=globalThis.backendaiclient.vfolder.set_quota(this.folderInfo.host,this.folderInfo.id,e.toString());r.push(t)}}r.length>0&&await Promise.all(r).then((()=>{this.notification.text=get("data.folders.FolderUpdated"),this.notification.show(),this._refreshFolderList(!0,"updateFolder")})).catch((e=>{console.log(e),e&&e.message&&(t=!0,this.notification.text=BackendAIPainKiller.relieve(e.message),this.notification.show(!0,e))})),t||this.closeDialog("modify-folder-dialog")}async _updateFolderName(){globalThis.backendaiclient.vfolder.name=this.renameFolderName;const e=this.newFolderNameInput.value;if(this.newFolderNameInput.reportValidity(),e){if(!this.newFolderNameInput.checkValidity())return;try{await globalThis.backendaiclient.vfolder.rename(e),this.notification.text=get("data.folders.FolderRenamed"),this.notification.show(),this._refreshFolderList(!0,"updateFolder"),this.closeDialog("modify-folder-name-dialog")}catch(e){this.notification.text=BackendAIPainKiller.relieve(e.message),this.notification.show(!0,e)}}}_renameFolderDialog(e){this.renameFolderName=this._getControlName(e),this.newFolderNameInput.value="",this.openDialog("modify-folder-name-dialog")}_deleteFolderDialog(e){this.deleteFolderID=this._getControlID(e)||"",this.deleteFolderName=this._getControlName(e)||"",this.deleteFolderNameInput.value="",this.enableVfolderTrashBin?this.openDialog("delete-folder-without-confirm-dialog"):this.openDialog("delete-folder-dialog")}openDeleteFromTrashBinDialog(e){this.deleteFolderID=this._getControlID(e)||"",this.deleteFolderName=this._getControlName(e)||"",this.deleteFromTrashBinNameInput.value="",this.openDialog("delete-from-trash-bin-dialog")}_deleteFolderWithCheck(){if(this.deleteFolderNameInput.value!==this.deleteFolderName)return this.notification.text=get("data.folders.FolderNameMismatched"),void this.notification.show();this.closeDialog("delete-folder-dialog");const e=this.enableVfolderTrashBin?this.deleteFolderID:this.deleteFolderName;this._deleteFolder(e)}_deleteFolder(e){(this.enableVfolderTrashBin?globalThis.backendaiclient.vfolder.delete_by_id(e):globalThis.backendaiclient.vfolder.delete(e)).then((async e=>{e.msg?(this.notification.text=get("data.folders.CannotDeleteFolder"),this.notification.show(!0)):(this.notification.text=this.enableVfolderTrashBin?get("data.folders.MovedToTrashBin",{folderName:this.deleteFolderName||""}):get("data.folders.FolderDeleted",{folderName:this.deleteFolderName||""}),this.notification.show(),await this.refreshFolderList())})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=BackendAIPainKiller.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_inferModel(e){const t=this._getControlName(e);this.sessionLauncher.customFolderMapping={},this.sessionLauncher.customFolderMapping[t]="mount",this.sessionLauncher._launchSessionDialog()}async _checkVfolderMounted(e=""){}_requestCloneFolder(e){}_leaveInvitedFolderDialog(e){this.leaveFolderName=this._getControlName(e),this.leaveFolderNameInput.value="",this.openDialog("leave-folder-dialog")}_leaveFolderWithCheck(){if(this.leaveFolderNameInput.value!==this.leaveFolderName)return this.notification.text=get("data.folders.FolderNameMismatched"),void this.notification.show();this.closeDialog("leave-folder-dialog"),this._leaveFolder(this.leaveFolderName)}_leaveFolder(e){globalThis.backendaiclient.vfolder.leave_invited(e).then((async e=>{this.notification.text=get("data.folders.FolderDisconnected"),this.notification.show(),await this.refreshFolderList()})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=BackendAIPainKiller.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}async _getMaxSize(){}_triggerFolderListChanged(){const e=new CustomEvent("backend-ai-folder-list-changed");document.dispatchEvent(e)}_validateExistingFileName(){this.newFileNameInput.validityTransform=(e,t)=>{if(t.valid){const e=/[`~!@#$%^&*()|+=?;:'",<>{}[\]\\/]/gi;let t;return this.newFileNameInput.value===this.renameFileDialog.querySelector("#old-file-name").textContent?(this.newFileNameInput.validationMessage=get("data.EnterDifferentValue"),t=!1,{valid:t,customError:!t}):(t=!0,t=!e.test(this.newFileNameInput.value),t||(this.newFileNameInput.validationMessage=get("data.Allowslettersnumbersand-_dot")),{valid:t,customError:!t})}return t.valueMissing?(this.newFileNameInput.validationMessage=get("data.FileandFoldernameRequired"),{valid:t.valid,customError:!t.valid}):(this.newFileNameInput.validationMessage=get("data.Allowslettersnumbersand-_dot"),{valid:t.valid,customError:!t.valid})}}_validateFolderName(e=!1){var t;const i=e?this.newFolderNameInput:null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#add-folder-name");i.validityTransform=(t,o)=>{if(o.valid){let t;const o=/[`~!@#$%^&*()|+=?;:'",<>{}[\]\\/\s]/gi;if(e){if(i.value===this.renameFolderName)return i.validationMessage=get("data.EnterDifferentValue"),t=!1,{valid:t,customError:!t};t=!0}return t=!o.test(i.value),t||(i.validationMessage=get("data.Allowslettersnumbersand-_dot")),{valid:t,customError:!t}}return o.valueMissing?(i.validationMessage=get("data.FolderNameRequired"),{valid:o.valid,customError:!o.valid}):(i.validationMessage=get("data.Allowslettersnumbersand-_dot"),{valid:o.valid,customError:!o.valid})}}async _clearExplorer(e=this.explorer.breadcrumb.join("/"),t=this.explorer.id,i=!1){const o=await globalThis.backendaiclient.vfolder.list_files(e,t);if(this.fileListGrid.selectedItems=[],this._APIMajorVersion<6)this.explorer.files=JSON.parse(o.files);else{const e=JSON.parse(o.files);e.forEach(((e,t)=>{let i="FILE";if(e.filename===o.items[t].name)i=o.items[t].type;else for(let t=0;t<o.items.length;t++)if(e.filename===o.items[t].name){i=o.items[t].type;break}e.type=i})),this.explorer.files=e}this.explorerFiles=this.explorer.files,i&&(0!==this.filebrowserSupportedImages.length&&0!==this.systemRoleSupportedImages.length||await this._checkImageSupported(),this._toggleFilebrowserButton(),this._toggleSSHSessionButton(),this.openDialog("folder-explorer-dialog"))}_toggleFilebrowserButton(){var e,t;const i=!!(this.filebrowserSupportedImages.length>0&&this._isResourceEnough()),o=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#filebrowser-img"),r=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#filebrowser-btn");if(o&&r){r.disabled=!i;const e=i?"":"apply-grayscale";o.setAttribute("class",e)}}triggerOpenFilebrowserToReact(e){const t=new URLSearchParams(window.location.search);t.set("folder",e.item.id),document.dispatchEvent(new CustomEvent("react-navigate",{detail:{pathname:"/data",search:t.toString()}}))}triggerCloseFilebrowserToReact(){const e=new URLSearchParams(window.location.search);e.delete("folder"),document.dispatchEvent(new CustomEvent("react-navigate",{detail:{pathname:window.location.pathname,search:e.toString()}}))}_folderExplorer(e){this.vhost=e.item.host;const t=e.item.name,i=this._hasPermission(e.item,"w")||e.item.is_owner||"group"===e.item.type&&this.is_admin,o={id:t,uuid:e.item.id,breadcrumb:["."]};this.isWritable=i,this.explorer=o,this._clearExplorer(o.breadcrumb.join("/"),o.id,!0)}_enqueueFolder(e){const t=e.target;t.setAttribute("disabled","true");const i=e.target.getAttribute("name");this.explorer.breadcrumb.push(i),this._clearExplorer().then((e=>{t.removeAttribute("disabled")}))}_gotoFolder(e){const t=e.target.getAttribute("dest");let i=this.explorer.breadcrumb;const o=i.indexOf(t);-1!==o&&(i=i.slice(0,o+1),this.explorer.breadcrumb=i,this._clearExplorer(i.join("/"),this.explorer.id,!1))}_mkdir(e){const t=this.mkdirNameInput.value,i=this.explorer;if(this.mkdirNameInput.reportValidity(),this.mkdirNameInput.checkValidity()){globalThis.backendaiclient.vfolder.mkdir([...i.breadcrumb,t].join("/"),i.id).catch((e=>{e&e.message?(this.notification.text=BackendAIPainKiller.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=BackendAIPainKiller.relieve(e.title),this.notification.show(!0,e))})).then((e=>{this.closeDialog("mkdir-dialog"),this._clearExplorer()}))}}_isDir(e){return this._APIMajorVersion<6?e.mode.startsWith("d"):"DIRECTORY"===e.type}_addEventListenerDropZone(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#dropzone");t.addEventListener("dragleave",(()=>{t.style.display="none"})),this.folderExplorerDialog.addEventListener("dragover",(e=>(e.stopPropagation(),e.preventDefault(),!this.isWritable||(e.dataTransfer.dropEffect="copy",t.style.display="flex",!1)))),this.folderExplorerDialog.addEventListener("drop",(e=>{let i=!1;if(e.stopPropagation(),e.preventDefault(),t.style.display="none",this.isWritable){for(let t=0;t<e.dataTransfer.files.length;t++)if(e.dataTransfer.items[t].webkitGetAsEntry().isFile){const i=e.dataTransfer.files[t];if(this._maxFileUploadSize>0&&i.size>this._maxFileUploadSize)return this.notification.text=get("data.explorer.FileUploadSizeLimit")+` (${globalThis.backendaiutils._humanReadableFileSize(this._maxFileUploadSize)})`,void this.notification.show();if(this.explorerFiles.find((e=>e.filename===i.name))){window.confirm(`${get("data.explorer.FileAlreadyExists")}\n${i.name}\n${get("data.explorer.DoYouWantToOverwrite")}`)&&(i.progress=0,i.caption="",i.error=!1,i.complete=!1,this.uploadFiles.push(i))}else i.progress=0,i.caption="",i.error=!1,i.complete=!1,this.uploadFiles.push(i)}else i||(this.filebrowserSupportedImages.length>0?(this.notification.text=get("data.explorer.ClickFilebrowserButton"),this.notification.show()):(this.notification.text=get("data.explorer.NoImagesSupportingFileBrowser"),this.notification.show())),i=!0;for(let e=0;e<this.uploadFiles.length;e++)this.fileUpload(this.uploadFiles[e]),this._clearExplorer()}else this.notification.text=get("data.explorer.WritePermissionRequiredInUploadFiles"),this.notification.show()}))}_uploadBtnClick(e){var t,i;const o="add-folder-btn"===e.target.id?null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#folderInput"):null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#fileInput");if(o&&document.createEvent){const e=document.createEvent("MouseEvents");e.initEvent("click",!0,!1),o.dispatchEvent(e)}}getFolderName(e){var t;return null===(t=(e.webkitRelativePath||e.name).split("/"))||void 0===t?void 0:t[0]}_uploadInputChange(e){var t,i;const o=e.target.files.length,r="folderInput"===e.target.id,a=r?null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#folderInput"):null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#fileInput");let n=!1,s=!1;if(e.target.files.length>0&&r){const t=e.target.files[0];if(this.explorerFiles.find((e=>e.filename===this.getFolderName(t)))&&(s=window.confirm(`${get("data.explorer.FolderAlreadyExists")}\n${this.getFolderName(t)}\n${get("data.explorer.DoYouWantToOverwrite")}`),!s))return void(a.value="")}for(let t=0;t<o;t++){const i=e.target.files[t];let o="";const r="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";for(let e=0;e<5;e++)o+=r.charAt(Math.floor(Math.random()*r.length));if(this._maxFileUploadSize>0&&i.size>this._maxFileUploadSize)return this.notification.text=get("data.explorer.FileUploadSizeLimit")+` (${globalThis.backendaiutils._humanReadableFileSize(this._maxFileUploadSize)})`,void this.notification.show();if(0!==i.size){if(this.explorerFiles.find((e=>e.filename===i.name))&&!s){window.confirm(`${get("data.explorer.FileAlreadyExists")}\n${i.name}\n${get("data.explorer.DoYouWantToOverwrite")}`)&&(i.id=o,i.progress=0,i.caption="",i.error=!1,i.complete=!1,this.uploadFiles.push(i))}else i.id=o,i.progress=0,i.caption="",i.error=!1,i.complete=!1,this.uploadFiles.push(i)}else n=!0}for(let e=0;e<this.uploadFiles.length;e++)this.fileUpload(this.uploadFiles[e]);(n||r)&&(this.notification.text=get("data.explorer.EmptyFilesAndFoldersAreNotUploaded"),this.notification.show()),a.value=""}runFileUploadQueue(e=null){let t;null!==e&&this.fileUploadQueue.push(e);for(let e=this.fileUploadCount;e<this.concurrentFileUploadLimit;e++)this.fileUploadQueue.length>0&&(t=this.fileUploadQueue.shift(),this.fileUploadCount=this.fileUploadCount+1,t.start())}fileUpload(e){this._uploadFlag=!0,this.uploadFilesExist=this.uploadFiles.length>0;const t=this.explorer.breadcrumb.concat(e.webkitRelativePath||e.name).join("/");globalThis.backendaiclient.vfolder.create_upload_session(t,e,this.explorer.id).then((i=>{const o=(new Date).getTime(),r=new tus$1.Upload(e,{endpoint:i,retryDelays:[0,3e3,5e3,1e4,2e4],uploadUrl:i,chunkSize:15728640,metadata:{filename:t,filetype:e.type},onError:t=>{console.log("Failed because: "+t),this.currentUploadFile=this.uploadFiles[this.uploadFiles.indexOf(e)],this.fileUploadCount=this.fileUploadCount-1,this.runFileUploadQueue()},onProgress:(t,i)=>{if(this.currentUploadFile=this.uploadFiles[this.uploadFiles.indexOf(e)],!this._uploadFlag)return r.abort(),this.uploadFiles[this.uploadFiles.indexOf(e)].caption="Canceling...",this.uploadFiles=this.uploadFiles.slice(),void setTimeout((()=>{this.uploadFiles=[],this.uploadFilesExist=!1,this.fileUploadCount=this.fileUploadCount-1}),1e3);const a=(new Date).getTime(),n=(t/1048576/((a-o)/1e3)).toFixed(1)+"MB/s",s=Math.floor((i-t)/(t/(a-o)*1e3));let l=get("data.explorer.LessThan10Sec");if(s>=86400)l=get("data.explorer.MoreThanADay");else if(s>10){l=`${Math.floor(s/3600)}:${Math.floor(s%3600/60)}:${s%60}`}const d=(t/i*100).toFixed(1);this.uploadFiles[this.uploadFiles.indexOf(e)].progress=t/i,this.uploadFiles[this.uploadFiles.indexOf(e)].caption=`${d}% / Time left : ${l} / Speed : ${n}`,this.uploadFiles=this.uploadFiles.slice()},onSuccess:()=>{this._clearExplorer(),this.currentUploadFile=this.uploadFiles[this.uploadFiles.indexOf(e)],this.uploadFiles[this.uploadFiles.indexOf(e)].complete=!0,this.uploadFiles=this.uploadFiles.slice(),setTimeout((()=>{this.uploadFiles.splice(this.uploadFiles.indexOf(e),1),this.uploadFilesExist=this.uploadFiles.length>0,this.uploadFiles=this.uploadFiles.slice(),this.fileUploadCount=this.fileUploadCount-1,this.runFileUploadQueue()}),1e3)}});this.runFileUploadQueue(r)}))}_cancelUpload(){this._uploadFlag=!1}_downloadFile(e,t=!1){if(!this._isDownloadable(this.vhost))return this.notification.text=get("data.explorer.DownloadNotAllowed"),void this.notification.show();const i=e.target.getAttribute("filename"),o=this.explorer.breadcrumb.concat(i).join("/");globalThis.backendaiclient.vfolder.request_download_token(o,this.explorer.id,t).then((e=>{const o=e.token;let r;if(r=this._APIMajorVersion<6?globalThis.backendaiclient.vfolder.get_download_url_with_token(o):`${e.url}?token=${e.token}&archive=${t}`,globalThis.iOSSafari)this.downloadURL=r,this.downloadFileDialog.show(),URL.revokeObjectURL(r);else{const e=document.createElement("a");e.style.display="none",e.addEventListener("click",(function(e){e.stopPropagation()})),e.href=r,e.download=i,document.body.appendChild(e),e.click(),document.body.removeChild(e),URL.revokeObjectURL(r)}}))}_compareFileExtension(){var e;const t=this.newFileNameInput.value,i=null!==(e=this.renameFileDialog.querySelector("#old-file-name").textContent)&&void 0!==e?e:"",o=/\.([0-9a-z]+)$/i,r=t.match(o),a=i.match(o);t.includes(".")&&r?this.newFileExtension=r[1].toLowerCase():this.newFileExtension="",i.includes(".")&&a?this.oldFileExtension=a[1].toLowerCase():this.oldFileExtension="",t?this.newFileExtension!==this.oldFileExtension?this.fileExtensionChangeDialog.show():this.oldFileExtension?this._keepFileExtension():this._renameFile():this._renameFile()}_keepFileExtension(){let e=this.newFileNameInput.value;e=this.newFileExtension?e.replace(new RegExp(this.newFileExtension+"$"),this.oldFileExtension):e+"."+this.oldFileExtension,this.newFileNameInput.value=e,this._renameFile()}_executeFileBrowser(){if(this._isResourceEnough())if(this.filebrowserSupportedImages.length>0){const e=localStorage.getItem("backendaiwebui.filebrowserNotification");null!=e&&"true"!==e||this.isWritable||this.fileBrowserNotificationDialog.show(),this._launchFileBrowserSession(),this._toggleFilebrowserButton()}else this.notification.text=get("data.explorer.NoImagesSupportingFileBrowser"),this.notification.show();else this.notification.text=get("data.explorer.NotEnoughResourceForFileBrowserSession"),this.notification.show()}_toggleShowFilebrowserNotification(e){const t=e.target;if(t){const e=(!t.checked).toString();localStorage.setItem("backendaiwebui.filebrowserNotification",e)}}async _launchFileBrowserSession(){let e;const t={},i=this.filebrowserSupportedImages.filter((e=>e.name.toLowerCase().includes("filebrowser")&&e.installed))[0],o=i.registry+"/"+i.name+":"+i.tag;t.mounts=[this.explorer.id],t.cpu=1,t.mem=this.minimumResource.mem+"g",t.domain=globalThis.backendaiclient._config.domainName,t.group_name=globalThis.backendaiclient.current_group;const r=await this.indicator.start("indeterminate");return globalThis.backendaiclient.get_resource_slots().then((e=>(r.set(20,get("data.explorer.ExecutingFileBrowser")),globalThis.backendaiclient.createIfNotExists(o,null,t,1e4,void 0)))).then((async t=>{const i=t.servicePorts;e={"session-uuid":t.sessionId,"session-name":t.sessionName,"access-key":"",runtime:"filebrowser",arguments:{"--root":"/home/work/"+this.explorer.id}},i.length>0&&i.filter((e=>"filebrowser"===e.name)).length>0&&globalThis.appLauncher.showLauncher(e),this.folderExplorerDialog.open&&this.closeDialog("folder-explorer-dialog"),r.end(1e3)})).catch((e=>{this.notification.text=BackendAIPainKiller.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e),r.end(100)}))}_executeSSHProxyAgent(){var e,t;(null===(t=null===(e=this.volumeInfo[this.vhost])||void 0===e?void 0:e.sftp_scaling_groups)||void 0===t?void 0:t.length)>0?this.systemRoleSupportedImages.length>0?(this._launchSystemRoleSSHSession(),this._toggleSSHSessionButton()):(this.notification.text=get("data.explorer.NoImagesSupportingSystemSession"),this.notification.show()):(this.notification.text=get("data.explorer.SFTPSessionNotAvailable"),this.notification.show())}async _launchSystemRoleSSHSession(){var e;const t={},i=globalThis.backendaiclient._config.systemSSHImage,o=this.systemRoleSupportedImages.filter((e=>e.installed))[0],r=""!==i?i:o.registry+"/"+o.name+":"+o.tag;t.mounts=[this.explorer.id],t.cpu=1,t.mem="256m",t.domain=globalThis.backendaiclient._config.domainName,t.scaling_group=null===(e=this.volumeInfo[this.vhost])||void 0===e?void 0:e.sftp_scaling_groups[0],t.group_name=globalThis.backendaiclient.current_group;const a=await this.indicator.start("indeterminate");return(async()=>{try{await globalThis.backendaiclient.get_resource_slots(),a.set(50,get("data.explorer.StartingSSH/SFTPSession"));const e=await globalThis.backendaiclient.createIfNotExists(r,`sftp-${this.explorer.uuid}`,t,15e3,void 0);if("CANCELLED"===e.status)return this.notification.text=BackendAIPainKiller.relieve(get("data.explorer.NumberOfSFTPSessionsExceededTitle")),this.notification.detail=get("data.explorer.NumberOfSFTPSessionsExceededBody"),this.notification.show(!0,{title:get("data.explorer.NumberOfSFTPSessionsExceededTitle"),message:get("data.explorer.NumberOfSFTPSessionsExceededBody")}),void a.end(100);const i=await globalThis.backendaiclient.get_direct_access_info(e.sessionId),o=i.public_host.replace(/^https?:\/\//,""),n=i.sshd_ports,s=new CustomEvent("read-ssh-key-and-launch-ssh-dialog",{detail:{sessionUuid:e.sessionId,host:o,port:n,mounted:this.explorer.id}});document.dispatchEvent(s),a.end(100)}catch(e){this.notification.text=BackendAIPainKiller.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e),a.end(100)}})()}_toggleSSHSessionButton(){var e,t;const i=this.systemRoleSupportedImages.length>0,o=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#ssh-img"),r=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#ssh-btn");if(o&&r){r.disabled=!i;const e=i?"":"apply-grayscale";o.setAttribute("class",e)}}_openRenameFileDialog(e,t=!1){const i=e.target.getAttribute("filename");this.renameFileDialog.querySelector("#old-file-name").textContent=i,this.newFileNameInput.value=i,this.renameFileDialog.filename=i,this.renameFileDialog.show(),this.is_dir=t,this.newFileNameInput.addEventListener("focus",(e=>{const t=i.replace(/\.([0-9a-z]+)$/i,"").length;this.newFileNameInput.setSelectionRange(0,t)})),this.newFileNameInput.focus()}_renameFile(){const e=this.renameFileDialog.filename,t=this.explorer.breadcrumb.concat(e).join("/"),i=this.newFileNameInput.value;if(this.fileExtensionChangeDialog.hide(),this.newFileNameInput.reportValidity(),this.newFileNameInput.checkValidity()){if(e===i)return this.newFileNameInput.focus(),this.notification.text=get("data.folders.SameFileName"),void this.notification.show();globalThis.backendaiclient.vfolder.rename_file(t,i,this.explorer.id,this.is_dir).then((e=>{this.notification.text=get("data.folders.FileRenamed"),this.notification.show(),this._clearExplorer(),this.renameFileDialog.hide()})).catch((e=>{console.error(e),e&&e.message&&(this.notification.text=e.title,this.notification.detail=e.message,this.notification.show(!0,e))}))}}_openDeleteFileDialog(e){const t=e.target.getAttribute("filename");this.deleteFileDialog.filename=t,this.deleteFileDialog.files=[],this.deleteFileDialog.show()}_openDeleteMultipleFileDialog(e){this.deleteFileDialog.files=this.fileListGrid.selectedItems,this.deleteFileDialog.filename="",this.deleteFileDialog.show()}_deleteFileWithCheck(e){const t=this.deleteFileDialog.files;if(t.length>0){const e=[];t.forEach((t=>{const i=this.explorer.breadcrumb.concat(t.filename).join("/");e.push(i)}));globalThis.backendaiclient.vfolder.delete_files(e,!0,this.explorer.id).then((e=>{this.notification.text=1==t.length?get("data.folders.FileDeleted"):get("data.folders.MultipleFilesDeleted"),this.notification.show(),this._clearExplorer(),this.deleteFileDialog.hide()}))}else if(""!=this.deleteFileDialog.filename){const e=this.explorer.breadcrumb.concat(this.deleteFileDialog.filename).join("/");globalThis.backendaiclient.vfolder.delete_files([e],!0,this.explorer.id).then((e=>{this.notification.text=get("data.folders.FileDeleted"),this.notification.show(),this._clearExplorer(),this.deleteFileDialog.hide()}))}}_deleteFile(e){const t=e.target.getAttribute("filename"),i=this.explorer.breadcrumb.concat(t).join("/");globalThis.backendaiclient.vfolder.delete_files([i],!0,this.explorer.id).then((e=>{this.notification.text=get("data.folders.FileDeleted"),this.notification.show(),this._clearExplorer()}))}_isResourceEnough(){const e=new CustomEvent("backend-ai-calculate-current-resource");document.dispatchEvent(e);const t=globalThis.backendaioptions.get("current-resource");return!!(t&&(t.cpu="string"==typeof t.cpu?parseInt(t.cpu):t.cpu,t.cpu>=this.minimumResource.cpu&&t.mem>=this.minimumResource.mem))}_humanReadableTime(e){const t=new Date(1e3*e),i=t.getTimezoneOffset()/60,o=t.getHours();return t.setHours(o-i),t.toUTCString()}_isDownloadable(e){var t;return(null!==(t=this._unionedAllowedPermissionByVolume[e])&&void 0!==t?t:[]).includes("download-file")}_initializeSharingFolderDialogLayout(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll("#share-folder-dialog mwc-textfield.share-email");t.length>1&&t.forEach((e=>{var t;"first-email"!==e.id&&(null===(t=e.parentNode)||void 0===t||t.removeChild(e))}))}_shareFolderDialog(e){this.selectedFolder=this._getControlName(e),this.selectedFolderType=this._getControlType(e),this._initializeSharingFolderDialogLayout(),this.openDialog("share-folder-dialog")}_modifyPermissionDialog(e){globalThis.backendaiclient.vfolder.list_invitees(e).then((e=>{this.invitees=e.shared,this.modifyPermissionDialog.updateComplete.then((()=>{this.openDialog("modify-permission-dialog")}))}))}_shareFolder(e){var t,i;const o=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll("mwc-textfield.share-email"),r=Array.prototype.filter.call(o,(e=>e.isUiValid&&""!==e.value)).map((e=>e.value.trim())),a=(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("mwc-radio[name=share-folder-permission][checked]")).value;if(0===r.length){this.notification.text=get("data.invitation.NoValidEmails"),this.notification.show(),this.shareFolderDialog.hide();for(const e of Array.from(o))e.value="";return}let n;n="user"===this.selectedFolderType?globalThis.backendaiclient.vfolder.invite(a,r,this.selectedFolder):globalThis.backendaiclient.vfolder.share(a,r,this.selectedFolder);const s=(e,t)=>e.filter((e=>!t.includes(e)));n.then((e=>{var t;let i;if("user"===this.selectedFolderType)if(e.invited_ids&&e.invited_ids.length>0){i=get("data.invitation.Invited");const t=s(r,e.invited_ids);t.length>0&&(i=get("data.invitation.FolderSharingNotAvailableToUser")+t.join(", "))}else i=get("data.invitation.NoOneWasInvited");else if(e.shared_emails&&e.shared_emails.length>0){i=get("data.invitation.Shared");const t=s(r,e.shared_emails);t.length>0&&(i=get("data.invitation.FolderSharingNotAvailableToUser")+t.join(", "))}else i=get("data.invitation.NoOneWasShared");this.notification.text=i,this.notification.show(),this.shareFolderDialog.hide();for(let e=o.length-1;e>0;e--){const i=o[e];null===(t=i.parentElement)||void 0===t||t.removeChild(i)}})).catch((e=>{e&&e.message&&(this.notification.text=BackendAIPainKiller.relieve(e.message),this.notification.detail=e.message),this.notification.show()}))}_validatePathName(){this.mkdirNameInput.validityTransform=(e,t)=>{if(t.valid){let e=/^([^`~!@#$%^&*()|+=?;:'",<>{}[\]\r\n/]{1,})+(\/[^`~!@#$%^&*()|+=?;:'",<>{}[\]\r\n/]{1,})*([/,\\]{0,1})$/gm.test(this.mkdirNameInput.value);return e&&"./"!==this.mkdirNameInput.value||(this.mkdirNameInput.validationMessage=get("data.explorer.ValueShouldBeStarted"),e=!1),{valid:e,customError:!e}}return t.valueMissing?(this.mkdirNameInput.validationMessage=get("data.explorer.ValueRequired"),{valid:t.valid,customError:!t.valid}):{valid:t.valid,customError:!t.valid}}}_restoreFolder(e){const t=this._getControlID(e)||"";globalThis.backendaiclient.vfolder.restore_from_trash_bin(t).then((async e=>{this.notification.text=get("data.folders.FolderRestored",{folderName:this.deleteFolderName||""}),this.notification.show(),await this.refreshFolderList()})).catch((e=>{e&&e.message&&(this.notification.text=BackendAIPainKiller.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_deleteFromTrashBin(){if(this.deleteFromTrashBinNameInput.value!==this.deleteFolderName)return this.notification.text=get("data.folders.FolderNameMismatched"),void this.notification.show();globalThis.backendaiclient.vfolder.delete_from_trash_bin(this.deleteFolderID).then((async e=>{this.notification.text=get("data.folders.FolderDeletedForever",{folderName:this.deleteFolderName||""}),this.notification.show(),await this.refreshFolderList()})).catch((e=>{e&&e.message&&(this.notification.text=BackendAIPainKiller.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))})),this.closeDialog("delete-from-trash-bin-dialog"),this.deleteFromTrashBinNameInput.value=""}};__decorate([n$4({type:Number})],BackendAiStorageList.prototype,"_APIMajorVersion",void 0),__decorate([n$4({type:String})],BackendAiStorageList.prototype,"storageType",void 0),__decorate([n$4({type:Array})],BackendAiStorageList.prototype,"folders",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"folderInfo",void 0),__decorate([n$4({type:Boolean})],BackendAiStorageList.prototype,"is_admin",void 0),__decorate([n$4({type:Boolean})],BackendAiStorageList.prototype,"enableStorageProxy",void 0),__decorate([n$4({type:Boolean})],BackendAiStorageList.prototype,"enableInferenceWorkload",void 0),__decorate([n$4({type:Boolean})],BackendAiStorageList.prototype,"enableVfolderTrashBin",void 0),__decorate([n$4({type:Boolean})],BackendAiStorageList.prototype,"authenticated",void 0),__decorate([n$4({type:String})],BackendAiStorageList.prototype,"renameFolderName",void 0),__decorate([n$4({type:String})],BackendAiStorageList.prototype,"deleteFolderName",void 0),__decorate([n$4({type:String})],BackendAiStorageList.prototype,"deleteFolderID",void 0),__decorate([n$4({type:String})],BackendAiStorageList.prototype,"leaveFolderName",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"explorer",void 0),__decorate([n$4({type:Array})],BackendAiStorageList.prototype,"explorerFiles",void 0),__decorate([n$4({type:String})],BackendAiStorageList.prototype,"existingFile",void 0),__decorate([n$4({type:Array})],BackendAiStorageList.prototype,"invitees",void 0),__decorate([n$4({type:String})],BackendAiStorageList.prototype,"selectedFolder",void 0),__decorate([n$4({type:String})],BackendAiStorageList.prototype,"selectedFolderType",void 0),__decorate([n$4({type:String})],BackendAiStorageList.prototype,"downloadURL",void 0),__decorate([n$4({type:Array})],BackendAiStorageList.prototype,"uploadFiles",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"currentUploadFile",void 0),__decorate([n$4({type:Array})],BackendAiStorageList.prototype,"fileUploadQueue",void 0),__decorate([n$4({type:Number})],BackendAiStorageList.prototype,"fileUploadCount",void 0),__decorate([n$4({type:Number})],BackendAiStorageList.prototype,"concurrentFileUploadLimit",void 0),__decorate([n$4({type:String})],BackendAiStorageList.prototype,"vhost",void 0),__decorate([n$4({type:Array})],BackendAiStorageList.prototype,"vhosts",void 0),__decorate([n$4({type:Array})],BackendAiStorageList.prototype,"allowedGroups",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"indicator",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"notification",void 0),__decorate([n$4({type:String})],BackendAiStorageList.prototype,"listCondition",void 0),__decorate([n$4({type:Array})],BackendAiStorageList.prototype,"allowed_folder_type",void 0),__decorate([n$4({type:Boolean})],BackendAiStorageList.prototype,"uploadFilesExist",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundIndexRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundTypeRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundFolderListRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundControlFolderListRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundTrashBinControlFolderListRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundControlFileListRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundPermissionViewRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundOwnerRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundFileNameRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundCreatedTimeRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundSizeRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundPermissionRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundCloneableRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundQuotaRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundUploadListRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundUploadProgressRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundInviteeInfoRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundIDRenderer",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"_boundStatusRenderer",void 0),__decorate([n$4({type:Boolean})],BackendAiStorageList.prototype,"_uploadFlag",void 0),__decorate([n$4({type:Boolean})],BackendAiStorageList.prototype,"_folderRefreshing",void 0),__decorate([n$4({type:Number})],BackendAiStorageList.prototype,"lastQueryTime",void 0),__decorate([n$4({type:Boolean})],BackendAiStorageList.prototype,"isWritable",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"permissions",void 0),__decorate([n$4({type:Number})],BackendAiStorageList.prototype,"_maxFileUploadSize",void 0),__decorate([n$4({type:Number})],BackendAiStorageList.prototype,"selectAreaHeight",void 0),__decorate([n$4({type:String})],BackendAiStorageList.prototype,"oldFileExtension",void 0),__decorate([n$4({type:String})],BackendAiStorageList.prototype,"newFileExtension",void 0),__decorate([n$4({type:Boolean})],BackendAiStorageList.prototype,"is_dir",void 0),__decorate([n$4({type:Boolean})],BackendAiStorageList.prototype,"_isDirectorySizeVisible",void 0),__decorate([n$4({type:Number})],BackendAiStorageList.prototype,"minimumResource",void 0),__decorate([n$4({type:Array})],BackendAiStorageList.prototype,"filebrowserSupportedImages",void 0),__decorate([n$4({type:Array})],BackendAiStorageList.prototype,"systemRoleSupportedImages",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"volumeInfo",void 0),__decorate([n$4({type:Array})],BackendAiStorageList.prototype,"quotaSupportStorageBackends",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"quotaUnit",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"maxSize",void 0),__decorate([n$4({type:Object})],BackendAiStorageList.prototype,"quota",void 0),__decorate([n$4({type:Boolean})],BackendAiStorageList.prototype,"directoryBasedUsage",void 0),__decorate([e$6("#loading-spinner")],BackendAiStorageList.prototype,"spinner",void 0),__decorate([e$6("#list-status")],BackendAiStorageList.prototype,"_listStatus",void 0),__decorate([e$6("#modify-folder-quota")],BackendAiStorageList.prototype,"modifyFolderQuotaInput",void 0),__decorate([e$6("#modify-folder-quota-unit")],BackendAiStorageList.prototype,"modifyFolderQuotaUnitSelect",void 0),__decorate([e$6("#file-list-grid")],BackendAiStorageList.prototype,"fileListGrid",void 0),__decorate([e$6("#folder-list-grid")],BackendAiStorageList.prototype,"folderListGrid",void 0),__decorate([e$6("#mkdir-name")],BackendAiStorageList.prototype,"mkdirNameInput",void 0),__decorate([e$6("#delete-folder-name")],BackendAiStorageList.prototype,"deleteFolderNameInput",void 0),__decorate([e$6("#delete-from-trash-bin-name-input")],BackendAiStorageList.prototype,"deleteFromTrashBinNameInput",void 0),__decorate([e$6("#new-folder-name")],BackendAiStorageList.prototype,"newFolderNameInput",void 0),__decorate([e$6("#new-file-name")],BackendAiStorageList.prototype,"newFileNameInput",void 0),__decorate([e$6("#leave-folder-name")],BackendAiStorageList.prototype,"leaveFolderNameInput",void 0),__decorate([e$6("#update-folder-permission")],BackendAiStorageList.prototype,"updateFolderPermissionSelect",void 0),__decorate([e$6("#update-folder-cloneable")],BackendAiStorageList.prototype,"updateFolderCloneableSwitch",void 0),__decorate([e$6("#rename-file-dialog")],BackendAiStorageList.prototype,"renameFileDialog",void 0),__decorate([e$6("#delete-file-dialog")],BackendAiStorageList.prototype,"deleteFileDialog",void 0),__decorate([e$6("#filebrowser-notification-dialog")],BackendAiStorageList.prototype,"fileBrowserNotificationDialog",void 0),__decorate([e$6("#file-extension-change-dialog")],BackendAiStorageList.prototype,"fileExtensionChangeDialog",void 0),__decorate([e$6("#folder-explorer-dialog")],BackendAiStorageList.prototype,"folderExplorerDialog",void 0),__decorate([e$6("#download-file-dialog")],BackendAiStorageList.prototype,"downloadFileDialog",void 0),__decorate([e$6("#modify-permission-dialog")],BackendAiStorageList.prototype,"modifyPermissionDialog",void 0),__decorate([e$6("#share-folder-dialog")],BackendAiStorageList.prototype,"shareFolderDialog",void 0),__decorate([e$6("#session-launcher")],BackendAiStorageList.prototype,"sessionLauncher",void 0),__decorate([r$2()],BackendAiStorageList.prototype,"_unionedAllowedPermissionByVolume",void 0),BackendAiStorageList=__decorate([t$2("backend-ai-storage-list")],BackendAiStorageList);let BackendAIData=class extends BackendAIPage{constructor(){super(...arguments),this.apiMajorVersion="",this.folderListFetchKey="first",this.is_admin=!1,this.enableStorageProxy=!1,this.enableInferenceWorkload=!1,this.enableModelStore=!1,this.supportVFolderTrashBin=!1,this.authenticated=!1,this.vhost="",this.selectedVhost="",this.vhosts=[],this.usageModes=["General"],this.permissions=["Read-Write","Read-Only","Delete"],this.allowedGroups=[],this.allowedModelTypeGroups=[],this.groupListByUsage=[],this.generalTypeGroups=[],this.allowed_folder_type=[],this.notification=Object(),this.folderLists=Object(),this._status="inactive",this.active=!1,this._vfolderInnatePermissionSupport=!1,this.storageInfo=Object(),this._activeTab="general",this._helpDescription="",this._helpDescriptionTitle="",this._helpDescriptionIcon="",this._helpDescriptionStorageProxyInfo=Object(),this.cloneFolderName="",this.storageProxyInfo=Object(),this.folderType="user",this.currentGroupIdx=0,this.openFolderExplorer=e=>{var t,i;if(null===(t=null==e?void 0:e.detail)||void 0===t?void 0:t.vFolder){const t="general"===this._activeTab?this.generalFolderStorageListElement:"model"===this._activeTab?this.modelFolderStorageListElement:"automount"===this._activeTab?this.automountFolderStorageListElement:"data"===this._activeTab?this.dataFolderStorageListElement:"trash-bin"===this._activeTab?this.trashBinFolderStorageListElement:null;null==t||t._folderExplorer({item:null===(i=null==e?void 0:e.detail)||void 0===i?void 0:i.vFolder})}},this.openAddFolderDialog=()=>this._addFolderDialog()}static get styles(){return[BackendAiStyles,IronFlex,IronFlexAlignment,IronPositioning,i$3`
        ul {
          padding-left: 0;
        }

        ul li {
          list-style: none;
          font-size: 13px;
        }

        span.indicator {
          width: 100px;
          font-size: 10px;
        }

        .tab-content {
          border: 0;
          font-size: 14px;
        }

        mwc-textfield {
          width: 100%;
          --mdc-text-field-fill-color: transparent;
        }

        mwc-textfield.red {
          --mdc-theme-primary: var(--paper-red-400) !important;
        }

        #add-folder-dialog,
        #clone-folder-dialog {
          --component-width: 375px;
        }

        #help-description {
          --component-width: 350px;
        }

        mwc-select {
          width: 50%;
          margin-bottom: 10px;
          /* Need to be set when fixedMenuPosition attribute is enabled */
          --mdc-menu-max-width: 345px;
          --mdc-menu-min-width: 172.5px;
          --mdc-select-max-width: 345px;
          --mdc-select-min-width: 172.5px;
        }

        mwc-select.full-width.fixed-position {
          width: 100%;
          /* Need to be set when fixedMenuPosition attribute is enabled */
          --mdc-menu-max-width: 345px;
          --mdc-menu-min-width: 345px;
          --mdc-select-max-width: 345px;
          --mdc-select-min-width: 345px;
        }

        mwc-select.fixed-position {
          /* Need to be set when fixedMenuPosition attribute is enabled */
          --mdc-menu-max-width: 172.5px;
          --mdc-menu-min-width: 172.5px;
          --mdc-select-max-width: 172.5px;
          --mdc-select-min-width: 172.5px;
        }

        mwc-select mwc-icon-button {
          --mdc-icon-button-size: 24px;
          color: var(--general-textfield-selected-color);
        }

        #help-description {
          --dialog-width: 350px;
        }

        #help-description p {
          padding: 5px !important;
        }

        .storage-status-indicator {
          width: 90px;
          color: black;
        }

        div.big {
          font-size: 72px;
        }

        .storage-chart-wrapper {
          margin: 20px 50px 0px 50px;
        }

        h4#default-quota-unit {
          display: none;
        }

        @media screen and (max-width: 750px) {
          mwc-tab {
            --mdc-typography-button-font-size: 10px;
          }

          mwc-button > span {
            display: none;
          }
        }

        .host-status-indicator {
          height: 16px;
          padding-left: 8px;
          padding-right: 8px;
          border-radius: 8px;
          font-size: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #fff;
        }

        .host-status-indicator.adequate {
          background-color: rgba(58, 178, 97, 1);
        }

        .host-status-indicator.caution {
          background-color: rgb(223, 179, 23);
        }

        .host-status-indicator.insufficient {
          background-color: #ef5350;
        }
      `]}renderStatusIndicator(e,t){const i=e<70?0:e<90?1:2,o=["Adequate","Caution","Insufficient"][i],r=[translate("data.usage.Adequate"),translate("data.usage.Caution"),translate("data.usage.Insufficient")][i];return x$1`
      <div
        class="host-status-indicator ${o.toLocaleLowerCase()} self-center"
      >
        ${t?r:""}
      </div>
    `}render(){var e,t,i,o,r,a,n,s,l,d,c,u,h,p,m,f,g,v;return x$1`
      <link rel="stylesheet" href="resources/custom.css" />
      <div class="vertical layout">
        <div>
          <div slot="message">
            <div
              style="display: ${"general"===this._activeTab?"block":"none"};"
            >
              <backend-ai-storage-list
                id="general-folder-storage"
                storageType="general"
                ?active="${!0===this.active&&"general"===this._activeTab}"
              ></backend-ai-storage-list>
            </div>
            <div
              style="display: ${"data"===this._activeTab?"block":"none"};"
            >
              <backend-ai-storage-list
                id="data-folder-storage"
                storageType="data"
                ?active="${!0===this.active&&"data"===this._activeTab}"
              ></backend-ai-storage-list>
            </div>
            <div
              style="display: ${"automount"===this._activeTab?"block":"none"};"
            >
              <backend-ai-storage-list
                id="automount-folder-storage"
                storageType="automount"
                ?active="${!0===this.active&&"automount"===this._activeTab}"
              ></backend-ai-storage-list>
            </div>
            ${this.enableInferenceWorkload?x$1`
                  <div
                    style="display: ${"model"===this._activeTab?"block":"none"};"
                  >
                    <backend-ai-storage-list
                      id="model-folder-storage"
                      storageType="model"
                      ?active="${!0===this.active&&"model"===this._activeTab}"
                    ></backend-ai-storage-list>
                  </div>
                `:x$1``}
            ${this.enableModelStore?x$1`
                  <backend-ai-react-model-store-list
                    id="model-store-folder-lists"
                    class="tab-content"
                    style="display:none;"
                    ?active="${!0===this.active&&"modelStore"===this._activeTab}"
                  ></backend-ai-react-model-store-list>
                `:x$1``}
            ${this.supportVFolderTrashBin?x$1`
                  <div
                    style="display: ${"trash-bin"===this._activeTab?"block":"none"};"
                  >
                    <backend-ai-storage-list
                      id="trash-bin-folder-storage"
                      storageType="deadVFolderStatus"
                      ?active="${!0===this.active&&"trash-bin"===this._activeTab}"
                    ></backend-ai-storage-list>
                  </div>
                `:x$1``}
          </div>
        </div>
      </div>
      <backend-ai-dialog id="add-folder-dialog" fixed backdrop>
        <span slot="title">${translate("data.CreateANewStorageFolder")}</span>
        <div slot="content" class="vertical layout flex">
          <mwc-textfield
            id="add-folder-name"
            label="${translate("data.Foldername")}"
            @change="${()=>this._validateFolderName()}"
            pattern="^[a-zA-Z0-9._-]*$"
            required
            validationMessage="${translate("data.Allowslettersnumbersand-_dot")}"
            maxLength="64"
            placeholder="${translate("maxLength.64chars")}"
          ></mwc-textfield>
          <mwc-select
            class="full-width fixed-position"
            id="add-folder-host"
            label="${translate("data.Host")}"
            fixedMenuPosition
            @selected=${e=>this.selectedVhost=e.target.value}
          >
            ${this.vhosts.map((e=>{var t,i,o;const r=this.storageProxyInfo[e]&&(null===(t=this.storageProxyInfo[e])||void 0===t?void 0:t.usage)&&(null===(o=null===(i=this.storageProxyInfo[e])||void 0===i?void 0:i.usage)||void 0===o?void 0:o.percentage);return x$1`
                <mwc-list-item
                  hasMeta
                  .value="${e}"
                  ?selected="${e===this.vhost}"
                >
                  <div class="horizontal layout justified center">
                    <span>${e}</span>
                    ${x$1`
                      &nbsp;
                      ${"number"==typeof r?this.renderStatusIndicator(r,!1):""}
                    `}
                  </div>
                  <mwc-icon-button
                    slot="meta"
                    icon="info"
                    @click="${t=>this._showStorageDescription(t,e)}"
                  ></mwc-icon-button>
                </mwc-list-item>
              `}))}
          </mwc-select>
          <div
            class="horizontal layout start"
            style="margin-top:-5px;margin-bottom:10px;padding-left:16px;font-size:12px;"
          >
            ${"number"==typeof(null===(t=null===(e=this.storageProxyInfo[this.selectedVhost])||void 0===e?void 0:e.usage)||void 0===t?void 0:t.percentage)?x$1`
                  ${translate("data.usage.StatusOfSelectedHost")}:&nbsp;${this.renderStatusIndicator(null===(o=null===(i=this.storageProxyInfo[this.selectedVhost])||void 0===i?void 0:i.usage)||void 0===o?void 0:o.percentage,!0)}
                `:x$1``}
          </div>
          <div class="horizontal layout">
            <mwc-select
              id="add-folder-type"
              label="${translate("data.Type")}"
              style="width:${this.is_admin&&this.allowed_folder_type.includes("group")?"50%":"100%"}"
              @change=${()=>{this._toggleFolderTypeInput(),this._toggleGroupSelect()}}
              required
            >
              ${this.allowed_folder_type.includes("user")?x$1`
                    <mwc-list-item value="user" selected>
                      ${translate("data.User")}
                    </mwc-list-item>
                  `:x$1``}
              ${this.is_admin&&this.allowed_folder_type.includes("group")?x$1`
                    <mwc-list-item
                      value="group"
                      ?selected="${!this.allowed_folder_type.includes("user")}"
                    >
                      ${translate("data.Project")}
                    </mwc-list-item>
                  `:x$1``}
            </mwc-select>
            ${this.is_admin&&this.allowed_folder_type.includes("group")?x$1`
                  <mwc-select
                    class="fixed-position"
                    id="add-folder-group"
                    ?disabled=${"user"===this.folderType}
                    label="${translate("data.Project")}"
                    FixedMenuPosition
                  >
                    ${this.groupListByUsage.map(((e,t)=>x$1`
                        <mwc-list-item
                          value="${e.name}"
                          ?selected="${this.currentGroupIdx===t}"
                        >
                          ${e.name}
                        </mwc-list-item>
                      `))}
                  </mwc-select>
                `:x$1``}
          </div>
          ${this._vfolderInnatePermissionSupport?x$1`
                <div class="horizontal layout">
                  <mwc-select
                    class="fixed-position"
                    id="add-folder-usage-mode"
                    label="${translate("data.UsageMode")}"
                    fixedMenuPosition
                    @change=${()=>{this._toggleGroupSelect()}}
                  >
                    ${this.usageModes.map(((e,t)=>x$1`
                        <mwc-list-item value="${e}" ?selected="${0===t}">
                          ${e}
                        </mwc-list-item>
                      `))}
                  </mwc-select>
                  <mwc-select
                    class="fixed-position"
                    id="add-folder-permission"
                    label="${translate("data.Permission")}"
                    fixedMenuPosition
                  >
                    ${this.permissions.map(((e,t)=>x$1`
                        <mwc-list-item value="${e}" ?selected="${0===t}">
                          ${e}
                        </mwc-list-item>
                      `))}
                  </mwc-select>
                </div>
              `:x$1``}
          ${this.enableStorageProxy?x$1`
                <div
                  id="cloneable-container"
                  class="horizontal layout flex wrap center justified"
                  style="display:none;"
                >
                  <p style="margin-left:10px;">
                    ${translate("data.folders.Cloneable")}
                  </p>
                  <mwc-switch
                    id="add-folder-cloneable"
                    style="margin-right:10px;"
                  ></mwc-switch>
                </div>
              `:x$1``}
          <div style="font-size:11px;">
            ${translate("data.DialogFolderStartingWithDotAutomount")}
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex">
          <mwc-button
            unelevated
            fullwidth
            id="add-button"
            icon="rowing"
            label="${translate("data.Create")}"
            @click="${()=>this._addFolder()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="clone-folder-dialog" fixed backdrop>
        <span slot="title">${translate("data.folders.CloneAFolder")}</span>
        <div slot="content" style="width:100%;">
          <mwc-textfield
            id="clone-folder-src"
            label="${translate("data.FolderToCopy")}"
            value="${this.cloneFolderName}"
            disabled
          ></mwc-textfield>
          <mwc-textfield
            id="clone-folder-name"
            label="${translate("data.Foldername")}"
            @change="${()=>this._validateFolderName()}"
            pattern="^[a-zA-Z0-9._-]*$"
            required
            validationMessage="${translate("data.Allowslettersnumbersand-_dot")}"
            maxLength="64"
            placeholder="${translate("maxLength.64chars")}"
          ></mwc-textfield>
          <mwc-select
            class="full-width fixed-position"
            id="clone-folder-host"
            label="${translate("data.Host")}"
            fixedMenuPosition
          >
            ${this.vhosts.map(((e,t)=>x$1`
                <mwc-list-item hasMeta value="${e}" ?selected="${0===t}">
                  <span>${e}</span>
                  <mwc-icon-button
                    slot="meta"
                    icon="info"
                    @click="${t=>this._showStorageDescription(t,e)}"
                  ></mwc-icon-button>
                </mwc-list-item>
              `))}
          </mwc-select>
          <div class="horizontal layout">
            <mwc-select
              id="clone-folder-type"
              label="${translate("data.Type")}"
              style="width:${this.is_admin&&this.allowed_folder_type.includes("group")?"50%":"100%"}"
            >
              ${this.allowed_folder_type.includes("user")?x$1`
                    <mwc-list-item value="user" selected>
                      ${translate("data.User")}
                    </mwc-list-item>
                  `:x$1``}
              ${this.is_admin&&this.allowed_folder_type.includes("group")?x$1`
                    <mwc-list-item
                      value="group"
                      ?selected="${!this.allowed_folder_type.includes("user")}"
                    >
                      ${translate("data.Project")}
                    </mwc-list-item>
                  `:x$1``}
            </mwc-select>
            ${this.is_admin&&this.allowed_folder_type.includes("group")?x$1`
                  <mwc-select
                    class="fixed-position"
                    id="clone-folder-group"
                    label="${translate("data.Project")}"
                    FixedMenuPosition
                  >
                    ${this.allowedGroups.map(((e,t)=>x$1`
                        <mwc-list-item
                          value="${e.name}"
                          ?selected="${e.name===globalThis.backendaiclient.current_group}"
                        >
                          ${e.name}
                        </mwc-list-item>
                      `))}
                  </mwc-select>
                `:x$1``}
          </div>
          ${this._vfolderInnatePermissionSupport?x$1`
                <div class="horizontal layout">
                  <mwc-select
                    class="fixed-position"
                    id="clone-folder-usage-mode"
                    label="${translate("data.UsageMode")}"
                    FixedMenuPosition
                  >
                    ${this.usageModes.map(((e,t)=>x$1`
                        <mwc-list-item value="${e}" ?selected="${0===t}">
                          ${e}
                        </mwc-list-item>
                      `))}
                  </mwc-select>
                  <mwc-select
                    class="fixed-position"
                    id="clone-folder-permission"
                    label="${translate("data.Permission")}"
                    FixedMenuPosition
                  >
                    ${this.permissions.map(((e,t)=>x$1`
                        <mwc-list-item value="${e}" ?selected="${0===t}">
                          ${e}
                        </mwc-list-item>
                      `))}
                  </mwc-select>
                </div>
              `:x$1``}
          ${this.enableStorageProxy?x$1`
                <div class="horizontal layout flex wrap center justified">
                  <p style="color:rgba(0, 0, 0, 0.6);">
                    ${translate("data.folders.Cloneable")}
                  </p>
                  <mwc-switch
                    id="clone-folder-cloneable"
                    style="margin-right:10px;"
                  ></mwc-switch>
                </div>
              `:x$1``}
          <div style="font-size:11px;">
            ${translate("data.DialogFolderStartingWithDotAutomount")}
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex">
          <mwc-button
            unelevated
            fullwidth
            id="clone-button"
            icon="file_copy"
            label="${translate("data.Create")}"
            @click="${()=>this._cloneFolder()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="help-description" fixed backdrop>
        <span slot="title">${this._helpDescriptionTitle}</span>
        <div slot="content" class="vertical layout">
          <div class="horizontal layout center">
            ${""==this._helpDescriptionIcon?x$1``:x$1`
                  <img
                    slot="graphic"
                    src="resources/icons/${this._helpDescriptionIcon}"
                    style="width:64px;height:64px;margin-right:10px;"
                  />
                `}
            <p style="font-size:14px;width:256px;">
              ${o$4(this._helpDescription)}
            </p>
          </div>
          ${void 0!==(null===(a=null===(r=this._helpDescriptionStorageProxyInfo)||void 0===r?void 0:r.usage)||void 0===a?void 0:a.percentage)?x$1`
                <div class="vertical layout" style="padding-left:8px;">
                  <span><strong>${translate("data.usage.Status")}</strong></span>
                  <div class="horizontal layout">
                    ${this.renderStatusIndicator(null===(s=null===(n=this._helpDescriptionStorageProxyInfo)||void 0===n?void 0:n.usage)||void 0===s?void 0:s.percentage,!0)}
                  </div>
                  (${Math.floor(null===(d=null===(l=this._helpDescriptionStorageProxyInfo)||void 0===l?void 0:l.usage)||void 0===d?void 0:d.percentage)}%
                  ${translate("data.usage.used")}
                  ${(null===(u=null===(c=this._helpDescriptionStorageProxyInfo)||void 0===c?void 0:c.usage)||void 0===u?void 0:u.total)&&(null===(p=null===(h=this._helpDescriptionStorageProxyInfo)||void 0===h?void 0:h.usage)||void 0===p?void 0:p.used)?x$1`
                        ,
                        ${globalThis.backendaiutils._humanReadableFileSize(null===(f=null===(m=this._helpDescriptionStorageProxyInfo)||void 0===m?void 0:m.usage)||void 0===f?void 0:f.used)}
                        /
                        ${globalThis.backendaiutils._humanReadableFileSize(null===(v=null===(g=this._helpDescriptionStorageProxyInfo)||void 0===g?void 0:g.usage)||void 0===v?void 0:v.total)}
                      `:x$1``}
                  )
                </div>
              `:x$1``}
        </div>
      </backend-ai-dialog>
    `}firstUpdated(){var e;this.notification=globalThis.lablupNotification,this.folderLists=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll("backend-ai-storage-list"),fetch("resources/storage_metadata.json").then((e=>e.json())).then((e=>{const t=Object();for(const i in e.storageInfo)({}).hasOwnProperty.call(e.storageInfo,i)&&(t[i]={},"name"in e.storageInfo[i]&&(t[i].name=e.storageInfo[i].name),"description"in e.storageInfo[i]?t[i].description=e.storageInfo[i].description:t[i].description=get("data.NoStorageDescriptionFound"),"icon"in e.storageInfo[i]?t[i].icon=e.storageInfo[i].icon:t[i].icon="local.png","dialects"in e.storageInfo[i]&&e.storageInfo[i].dialects.forEach((e=>{t[e]=t[i]})));this.storageInfo=t})),this.options={responsive:!0,maintainAspectRatio:!0,legend:{display:!0,position:"bottom",align:"center",labels:{fontSize:20,boxWidth:10}}},void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._getStorageProxyInformation()}),!0):this._getStorageProxyInformation(),document.addEventListener("backend-ai-folder-list-changed",(()=>{this.folderListFetchKey=(new Date).toISOString()})),document.addEventListener("backend-ai-vfolder-cloning",(e=>{if(e.detail){const t=e.detail;this.cloneFolderName=t.name,this._cloneFolderDialog()}}))}connectedCallback(){super.connectedCallback(),document.addEventListener("folderExplorer:open",this.openFolderExplorer),document.dispatchEvent(new CustomEvent("backend-ai-data-view:connected"))}disconnectedCallback(){super.disconnectedCallback(),document.removeEventListener("folderExplorer:open",this.openFolderExplorer),document.dispatchEvent(new CustomEvent("backend-ai-data-view:disconnected"))}async _viewStateChanged(e){if(await this.updateComplete,!1===e)return;const t=()=>{this.is_admin=globalThis.backendaiclient.is_admin,this.authenticated=!0,this.enableStorageProxy=globalThis.backendaiclient.supports("storage-proxy"),this.enableInferenceWorkload=globalThis.backendaiclient.supports("inference-workload"),this.enableModelStore=globalThis.backendaiclient.supports("model-store")&&globalThis.backendaiclient._config.enableModelStore,this.supportVFolderTrashBin=globalThis.backendaiclient.supports("vfolder-trash-bin"),this.enableInferenceWorkload&&!this.usageModes.includes("Model")&&this.usageModes.push("Model"),this.apiMajorVersion=globalThis.backendaiclient.APIMajorVersion,this._getStorageProxyInformation(),globalThis.backendaiclient.isAPIVersionCompatibleWith("v4.20191215")&&(this._vfolderInnatePermissionSupport=!0),globalThis.backendaiclient.vfolder.list_allowed_types().then((e=>{this.allowed_folder_type=e}))};void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{t()}),!0):t()}_toggleFolderTypeInput(){this.folderType=this.addFolderTypeSelect.value}_getAutoSelectedVhostName(e){var t;const i=Math.min(...Object.values(e.volume_info).map((e=>{var t;return null===(t=null==e?void 0:e.usage)||void 0===t?void 0:t.percentage})));return null!==(t=Object.keys(e.volume_info).find((t=>{var o,r;return(null===(r=null===(o=e.volume_info[t])||void 0===o?void 0:o.usage)||void 0===r?void 0:r.percentage)===i})))&&void 0!==t?t:e.default}_getAutoSelectedVhostInfo(e){var t;const i=Math.min(...Object.values(e.volume_info).map((e=>{var t;return null===(t=null==e?void 0:e.usage)||void 0===t?void 0:t.percentage})));return null!==(t=Object.values(e.volume_info).find((e=>{var t;return(null===(t=null==e?void 0:e.usage)||void 0===t?void 0:t.percentage)===i})))&&void 0!==t?t:e.volume_info[e.default]}async _getAutoSelectedVhostIncludedList(){const e=await globalThis.backendaiclient.vfolder.list_hosts();return e.allowed.length>1&&(e.allowed.unshift(`auto (${this._getAutoSelectedVhostName(e)})`),e.volume_info[`auto (${this._getAutoSelectedVhostName(e)})`]=this._getAutoSelectedVhostInfo(e)),e}async _cloneFolderDialog(){const e=await this._getAutoSelectedVhostIncludedList();if(this.addFolderNameInput.value="",this.vhosts=e.allowed,this.vhosts.length>1?this.vhost=this.selectedVhost=`auto (${this._getAutoSelectedVhostName(e)})`:this.vhost=this.selectedVhost=e.default,this.allowed_folder_type.includes("group")){const e=await globalThis.backendaiclient.group.list();this.allowedGroups=e.groups}this.cloneFolderNameInput.value=await this._checkFolderNameAlreadyExists(this.cloneFolderName),this.openDialog("clone-folder-dialog")}async _addFolderDialog(){var e;const t=await this._getAutoSelectedVhostIncludedList();if(this.addFolderNameInput.value="",this.vhosts=t.allowed,this.vhosts.length>1?this.vhost=this.selectedVhost=`auto (${this._getAutoSelectedVhostName(t)})`:this.vhost=this.selectedVhost=t.default,this.allowed_folder_type.includes("group")){const t=await globalThis.backendaiclient.group.list(void 0,void 0,void 0,["GENERAL","MODEL_STORE"]);this.allowedModelTypeGroups=[],this.allowedGroups=[],null===(e=null==t?void 0:t.groups)||void 0===e||e.forEach((e=>{"MODEL_STORE"===e.type?this.allowedModelTypeGroups.push(e):this.allowedGroups.push(e)})),this._toggleGroupSelect()}this.openDialog("add-folder-dialog")}async _getStorageProxyInformation(){const e=await this._getAutoSelectedVhostIncludedList();this.storageProxyInfo=e.volume_info||{}}openDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).show()}closeDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).hide()}_showStorageDescription(e,t){var i;e.stopPropagation(),t in this.storageInfo?(this._helpDescriptionTitle=this.storageInfo[t].name,this._helpDescriptionIcon=this.storageInfo[t].icon,this._helpDescription=this.storageInfo[t].description):(this._helpDescriptionTitle=t,this._helpDescriptionIcon="local.png",this._helpDescription=get("data.NoStorageDescriptionFound")),this._helpDescriptionStorageProxyInfo=this.storageProxyInfo[t];(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#help-description")).show()}_indexFrom1(e){return e+1}_toggleGroupSelect(){var e;this.groupListByUsage="Model"!==(null===(e=this.addFolderUsageModeSelect)||void 0===e?void 0:e.value)?this.allowedGroups:[...this.allowedGroups,...this.allowedModelTypeGroups],this.addFolderGroupSelect&&this.addFolderGroupSelect.layout(!0).then((()=>{this.groupListByUsage.length>0?(this.currentGroupIdx=this.addFolderGroupSelect.items.findIndex((e=>e.value===globalThis.backendaiclient.current_group)),this.currentGroupIdx=this.currentGroupIdx<0?0:this.currentGroupIdx,this.addFolderGroupSelect.createAdapter().setSelectedText(this.groupListByUsage[this.currentGroupIdx].name)):this.addFolderGroupSelect.disabled=!0})),this._toggleCloneableSwitch()}_toggleCloneableSwitch(){var e;this.cloneableContainer&&("Model"===(null===(e=this.addFolderUsageModeSelect)||void 0===e?void 0:e.value)&&this.is_admin?this.cloneableContainer.style.display="flex":this.cloneableContainer.style.display="none")}_addFolder(){var e,t,i;const o=this.addFolderNameInput.value;let r=(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#add-folder-host")).value;const a=r.match(/^auto \((.+)\)$/);a&&(r=a[1]);let n,s=this.addFolderTypeSelect.value;const l=this.addFolderUsageModeSelect,d=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#add-folder-permission"),c=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#add-folder-cloneable");let u="",h="",p=!1;if(!1===["user","group"].includes(s)&&(s="user"),n="user"===s?"":this.is_admin?this.addFolderGroupSelect.value:globalThis.backendaiclient.current_group,l&&(u=l.value,u=u.toLowerCase()),d)switch(h=d.value,h){case"Read-Write":default:h="rw";break;case"Read-Only":h="ro";break;case"Delete":h="wd"}if(c&&(p=c.selected),this.addFolderNameInput.reportValidity(),this.addFolderNameInput.checkValidity()){globalThis.backendaiclient.vfolder.create(o,r,n,u,h,p).then((()=>{this.notification.text=get("data.folders.FolderCreated"),this.notification.show(),this._refreshFolderList()})).catch((e=>{e&&e.message&&(this.notification.text=BackendAIPainKiller.relieve(e.message),this.notification.detail=e.message,this.notification.show(!0,e))})),this.closeDialog("add-folder-dialog")}}async _cloneFolder(){var e,t,i,o,r;const a=await this._checkFolderNameAlreadyExists(this.cloneFolderNameInput.value,!0);let n=(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#clone-folder-host")).value;const s=n.match(/^auto \((.+)\)$/);s&&(n=s[1]),(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#clone-folder-type")).value;const l=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#clone-folder-usage-mode"),d=null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("#clone-folder-permission"),c=null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector("#clone-folder-cloneable");let u="",h="",p=!1;if(l&&(u=l.value,u=u.toLowerCase()),d)switch(h=d.value,h){case"Read-Write":default:h="rw";break;case"Read-Only":h="ro";break;case"Delete":h="wd"}if(p=!!c&&c.selected,this.cloneFolderNameInput.reportValidity(),this.cloneFolderNameInput.checkValidity()){const e={cloneable:p,permission:h,target_host:n,target_name:a,usage_mode:u};globalThis.backendaiclient.vfolder.clone(e,this.cloneFolderName).then((()=>{this.notification.text=get("data.folders.FolderCloned"),this.notification.show(),this._refreshFolderList()})).catch((e=>{e&&e.message&&(this.notification.text=BackendAIPainKiller.relieve(e.message),this.notification.detail=e.message,this.notification.show(!0,e))})),this.closeDialog("clone-folder-dialog")}}_validateFolderName(){this.addFolderNameInput.validityTransform=(e,t)=>{if(t.valid){let e=!/[`~!@#$%^&*()|+=?;:'",<>{}[\]\\/\s]/gi.test(this.addFolderNameInput.value);return e||(this.addFolderNameInput.validationMessage=get("data.Allowslettersnumbersand-_dot")),this.addFolderNameInput.value.length>64&&(e=!1,this.addFolderNameInput.validationMessage=get("data.FolderNameTooLong")),{valid:e,customError:!e}}return t.valueMissing?(this.addFolderNameInput.validationMessage=get("data.FolderNameRequired"),{valid:t.valid,customError:!t.valid}):(this.addFolderNameInput.validationMessage=get("data.Allowslettersnumbersand-_dot"),{valid:t.valid,customError:!t.valid})}}_refreshFolderList(){for(const e of this.folderLists)e.refreshFolderList()}async _checkFolderNameAlreadyExists(e,t=!1){const i=globalThis.backendaiclient.current_group_id(),o=(await globalThis.backendaiclient.vfolder.list(i)).map((e=>e.name));if(o.includes(e)){t&&(this.notification.text=get("import.FolderAlreadyExists"),this.notification.show());let i=1,r=e;for(;o.includes(r);)r=e+"_"+i,i++;e=r}return e}};__decorate([n$4({type:String})],BackendAIData.prototype,"apiMajorVersion",void 0),__decorate([n$4({type:String})],BackendAIData.prototype,"folderListFetchKey",void 0),__decorate([n$4({type:Boolean})],BackendAIData.prototype,"is_admin",void 0),__decorate([n$4({type:Boolean})],BackendAIData.prototype,"enableStorageProxy",void 0),__decorate([n$4({type:Boolean})],BackendAIData.prototype,"enableInferenceWorkload",void 0),__decorate([n$4({type:Boolean})],BackendAIData.prototype,"enableModelStore",void 0),__decorate([n$4({type:Boolean})],BackendAIData.prototype,"supportVFolderTrashBin",void 0),__decorate([n$4({type:Boolean})],BackendAIData.prototype,"authenticated",void 0),__decorate([n$4({type:String})],BackendAIData.prototype,"vhost",void 0),__decorate([n$4({type:String})],BackendAIData.prototype,"selectedVhost",void 0),__decorate([n$4({type:Array})],BackendAIData.prototype,"vhosts",void 0),__decorate([n$4({type:Array})],BackendAIData.prototype,"usageModes",void 0),__decorate([n$4({type:Array})],BackendAIData.prototype,"permissions",void 0),__decorate([n$4({type:Array})],BackendAIData.prototype,"allowedGroups",void 0),__decorate([n$4({type:Array})],BackendAIData.prototype,"allowedModelTypeGroups",void 0),__decorate([n$4({type:Array})],BackendAIData.prototype,"groupListByUsage",void 0),__decorate([n$4({type:Array})],BackendAIData.prototype,"generalTypeGroups",void 0),__decorate([n$4({type:Array})],BackendAIData.prototype,"allowed_folder_type",void 0),__decorate([n$4({type:Object})],BackendAIData.prototype,"notification",void 0),__decorate([n$4({type:Object})],BackendAIData.prototype,"folderLists",void 0),__decorate([n$4({type:String})],BackendAIData.prototype,"_status",void 0),__decorate([n$4({type:Boolean,reflect:!0})],BackendAIData.prototype,"active",void 0),__decorate([n$4({type:Boolean})],BackendAIData.prototype,"_vfolderInnatePermissionSupport",void 0),__decorate([n$4({type:Object})],BackendAIData.prototype,"storageInfo",void 0),__decorate([n$4({type:String})],BackendAIData.prototype,"_activeTab",void 0),__decorate([n$4({type:String})],BackendAIData.prototype,"_helpDescription",void 0),__decorate([n$4({type:String})],BackendAIData.prototype,"_helpDescriptionTitle",void 0),__decorate([n$4({type:String})],BackendAIData.prototype,"_helpDescriptionIcon",void 0),__decorate([n$4({type:Object})],BackendAIData.prototype,"_helpDescriptionStorageProxyInfo",void 0),__decorate([n$4({type:Object})],BackendAIData.prototype,"options",void 0),__decorate([n$4({type:Number})],BackendAIData.prototype,"capacity",void 0),__decorate([n$4({type:String})],BackendAIData.prototype,"cloneFolderName",void 0),__decorate([n$4({type:Object})],BackendAIData.prototype,"storageProxyInfo",void 0),__decorate([n$4({type:String})],BackendAIData.prototype,"folderType",void 0),__decorate([n$4({type:Number})],BackendAIData.prototype,"currentGroupIdx",void 0),__decorate([e$6("#add-folder-name")],BackendAIData.prototype,"addFolderNameInput",void 0),__decorate([e$6("#clone-folder-name")],BackendAIData.prototype,"cloneFolderNameInput",void 0),__decorate([e$6("#add-folder-usage-mode")],BackendAIData.prototype,"addFolderUsageModeSelect",void 0),__decorate([e$6("#add-folder-group")],BackendAIData.prototype,"addFolderGroupSelect",void 0),__decorate([e$6("#add-folder-type")],BackendAIData.prototype,"addFolderTypeSelect",void 0),__decorate([e$6("#cloneable-container")],BackendAIData.prototype,"cloneableContainer",void 0),__decorate([e$6("#general-folder-storage")],BackendAIData.prototype,"generalFolderStorageListElement",void 0),__decorate([e$6("#data-folder-storage")],BackendAIData.prototype,"dataFolderStorageListElement",void 0),__decorate([e$6("#automount-folder-storage")],BackendAIData.prototype,"automountFolderStorageListElement",void 0),__decorate([e$6("#model-folder-storage")],BackendAIData.prototype,"modelFolderStorageListElement",void 0),__decorate([e$6("#trash-bin-folder-storage")],BackendAIData.prototype,"trashBinFolderStorageListElement",void 0),BackendAIData=__decorate([t$2("backend-ai-data-view")],BackendAIData);
