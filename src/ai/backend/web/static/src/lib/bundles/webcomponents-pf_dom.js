/**
@license @nocompile
Copyright (c) 2018 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at http://polymer.github.io/LICENSE.txt
The complete set of authors may be found at http://polymer.github.io/AUTHORS.txt
The complete set of contributors may be found at http://polymer.github.io/CONTRIBUTORS.txt
Code distributed by Google as part of the polymer project is also
subject to an additional IP rights grant found at http://polymer.github.io/PATENTS.txt
*/
(function(){/*

 Copyright (c) 2016 The Polymer Project Authors. All rights reserved.
 This code may only be used under the BSD style license found at
 http://polymer.github.io/LICENSE.txt The complete set of authors may be found
 at http://polymer.github.io/AUTHORS.txt The complete set of contributors may
 be found at http://polymer.github.io/CONTRIBUTORS.txt Code distributed by
 Google as part of the polymer project is also subject to an additional IP
 rights grant found at http://polymer.github.io/PATENTS.txt
*/
'use strict';function aa(a){var c=0;return function(){return c<a.length?{done:!1,value:a[c++]}:{done:!0}}}function h(a){var c="undefined"!=typeof Symbol&&Symbol.iterator&&a[Symbol.iterator];return c?c.call(a):{next:aa(a)}}var k=document.createEvent("Event");k.initEvent("foo",!0,!0);k.preventDefault();
if(!k.defaultPrevented){var ba=Event.prototype.preventDefault;Event.prototype.preventDefault=function(){this.cancelable&&(ba.call(this),Object.defineProperty(this,"defaultPrevented",{get:function(){return!0},configurable:!0}))}}var l=/Trident/.test(navigator.userAgent);
if(!window.Event||l&&"function"!==typeof window.Event){var m=window.Event;window.Event=function(a,c){c=c||{};var d=document.createEvent("Event");d.initEvent(a,!!c.bubbles,!!c.cancelable);return d};if(m){for(var n in m)window.Event[n]=m[n];window.Event.prototype=m.prototype}}
if(!window.CustomEvent||l&&"function"!==typeof window.CustomEvent)window.CustomEvent=function(a,c){c=c||{};var d=document.createEvent("CustomEvent");d.initCustomEvent(a,!!c.bubbles,!!c.cancelable,c.detail);return d},window.CustomEvent.prototype=window.Event.prototype;
if(!window.MouseEvent||l&&"function"!==typeof window.MouseEvent){var p=window.MouseEvent;window.MouseEvent=function(a,c){c=c||{};var d=document.createEvent("MouseEvent");d.initMouseEvent(a,!!c.bubbles,!!c.cancelable,c.view||window,c.detail,c.screenX,c.screenY,c.clientX,c.clientY,c.ctrlKey,c.altKey,c.shiftKey,c.metaKey,c.button,c.relatedTarget);return d};if(p)for(var q in p)window.MouseEvent[q]=p[q];window.MouseEvent.prototype=p.prototype};var r,ca=function(){function a(){e++}var c=!1,d=!1,b={get capture(){return c=!0},get once(){return d=!0}},e=0,f=document.createElement("div");f.addEventListener("click",a,b);var g=c&&d;g&&(f.dispatchEvent(new Event("click")),f.dispatchEvent(new Event("click")),g=1==e);f.removeEventListener("click",a,b);return g}(),t=null!==(r=window.EventTarget)&&void 0!==r?r:window.Node;
if(!ca&&"addEventListener"in t.prototype){var u=function(a){if(!a||"object"!==typeof a&&"function"!==typeof a){var c=!!a;a=!1}else c=!!a.capture,a=!!a.once;return{capture:c,once:a}},da=t.prototype.addEventListener,v=t.prototype.removeEventListener,ea=new WeakMap,fa=new WeakMap,w=function(a,c,d){var b=d?ea:fa;d=b.get(a);void 0===d&&b.set(a,d=new Map);a=d.get(c);void 0===a&&d.set(c,a=new WeakMap);return a};t.prototype.addEventListener=function(a,c,d){var b=this;if(null!=c){d=u(d);var e=d.capture;d=
d.once;var f=w(this,a,e);if(!f.has(c)){var g=d?function(U){f.delete(c);v.call(b,a,g,e);if("function"===typeof c)return c.call(b,U);if("function"===typeof(null===c||void 0===c?void 0:c.handleEvent))return c.handleEvent(U)}:null;f.set(c,g);da.call(this,a,null!==g&&void 0!==g?g:c,e)}}};t.prototype.removeEventListener=function(a,c,d){if(null!=c){d=u(d).capture;var b=w(this,a,d),e=b.get(c);void 0!==e&&(b.delete(c),v.call(this,a,null!==e&&void 0!==e?e:c,d))}}};/*

Copyright (c) 2018 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at
http://polymer.github.io/LICENSE.txt The complete set of authors may be found at
http://polymer.github.io/AUTHORS.txt The complete set of contributors may be
found at http://polymer.github.io/CONTRIBUTORS.txt Code distributed by Google as
part of the polymer project is also subject to an additional IP rights grant
found at http://polymer.github.io/PATENTS.txt
*/
Object.getOwnPropertyDescriptor(Node.prototype,"baseURI")||Object.defineProperty(Node.prototype,"baseURI",{get:function(){var a=(this.ownerDocument||this).querySelector("base[href]");return a&&a.href||window.location.href},configurable:!0,enumerable:!0});/*

Copyright (c) 2020 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at
http://polymer.github.io/LICENSE.txt The complete set of authors may be found at
http://polymer.github.io/AUTHORS.txt The complete set of contributors may be
found at http://polymer.github.io/CONTRIBUTORS.txt Code distributed by Google as
part of the polymer project is also subject to an additional IP rights grant
found at http://polymer.github.io/PATENTS.txt
*/
var x,y,z=Element.prototype,A=null!==(x=Object.getOwnPropertyDescriptor(z,"attributes"))&&void 0!==x?x:Object.getOwnPropertyDescriptor(Node.prototype,"attributes"),ha=null!==(y=null===A||void 0===A?void 0:A.get)&&void 0!==y?y:function(){return this.attributes},ia=Array.prototype.map;z.hasOwnProperty("getAttributeNames")||(z.getAttributeNames=function(){return ia.call(ha.call(this),function(a){return a.name})});var B,C=Element.prototype;C.hasOwnProperty("matches")||(C.matches=null!==(B=C.webkitMatchesSelector)&&void 0!==B?B:C.msMatchesSelector);/*

Copyright (c) 2020 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at http://polymer.github.io/LICENSE.txt
The complete set of authors may be found at http://polymer.github.io/AUTHORS.txt
The complete set of contributors may be found at http://polymer.github.io/CONTRIBUTORS.txt
Code distributed by Google as part of the polymer project is also
subject to an additional IP rights grant found at http://polymer.github.io/PATENTS.txt
*/
var ja=Node.prototype.appendChild;function D(a){a=a.prototype;a.hasOwnProperty("append")||Object.defineProperty(a,"append",{configurable:!0,enumerable:!0,writable:!0,value:function(c){for(var d=[],b=0;b<arguments.length;++b)d[b]=arguments[b];d=h(d);for(b=d.next();!b.done;b=d.next())b=b.value,ja.call(this,"string"===typeof b?document.createTextNode(b):b)}})}D(Document);D(DocumentFragment);D(Element);var E,F,ka=Node.prototype.insertBefore,la=null!==(F=null===(E=Object.getOwnPropertyDescriptor(Node.prototype,"firstChild"))||void 0===E?void 0:E.get)&&void 0!==F?F:function(){return this.firstChild};
function G(a){a=a.prototype;a.hasOwnProperty("prepend")||Object.defineProperty(a,"prepend",{configurable:!0,enumerable:!0,writable:!0,value:function(c){for(var d=[],b=0;b<arguments.length;++b)d[b]=arguments[b];b=la.call(this);d=h(d);for(var e=d.next();!e.done;e=d.next())e=e.value,ka.call(this,"string"===typeof e?document.createTextNode(e):e,b)}})}G(Document);G(DocumentFragment);G(Element);var H,I,ma=Node.prototype.appendChild,na=Node.prototype.removeChild,oa=null!==(I=null===(H=Object.getOwnPropertyDescriptor(Node.prototype,"firstChild"))||void 0===H?void 0:H.get)&&void 0!==I?I:function(){return this.firstChild};
function J(a){a=a.prototype;a.hasOwnProperty("replaceChildren")||Object.defineProperty(a,"replaceChildren",{configurable:!0,enumerable:!0,writable:!0,value:function(c){for(var d=[],b=0;b<arguments.length;++b)d[b]=arguments[b];for(;null!==(b=oa.call(this));)na.call(this,b);d=h(d);for(b=d.next();!b.done;b=d.next())b=b.value,ma.call(this,"string"===typeof b?document.createTextNode(b):b)}})}J(Document);J(DocumentFragment);J(Element);var K,L,M,N,pa=Node.prototype.insertBefore,qa=null!==(L=null===(K=Object.getOwnPropertyDescriptor(Node.prototype,"parentNode"))||void 0===K?void 0:K.get)&&void 0!==L?L:function(){return this.parentNode},ra=null!==(N=null===(M=Object.getOwnPropertyDescriptor(Node.prototype,"nextSibling"))||void 0===M?void 0:M.get)&&void 0!==N?N:function(){return this.nextSibling};
function O(a){a=a.prototype;a.hasOwnProperty("after")||Object.defineProperty(a,"after",{configurable:!0,enumerable:!0,writable:!0,value:function(c){for(var d=[],b=0;b<arguments.length;++b)d[b]=arguments[b];b=qa.call(this);if(null!==b){var e=ra.call(this);d=h(d);for(var f=d.next();!f.done;f=d.next())f=f.value,pa.call(b,"string"===typeof f?document.createTextNode(f):f,e)}}})}O(CharacterData);O(Element);var P,Q,sa=Node.prototype.insertBefore,ta=null!==(Q=null===(P=Object.getOwnPropertyDescriptor(Node.prototype,"parentNode"))||void 0===P?void 0:P.get)&&void 0!==Q?Q:function(){return this.parentNode};
function R(a){a=a.prototype;a.hasOwnProperty("before")||Object.defineProperty(a,"before",{configurable:!0,enumerable:!0,writable:!0,value:function(c){for(var d=[],b=0;b<arguments.length;++b)d[b]=arguments[b];b=ta.call(this);if(null!==b){d=h(d);for(var e=d.next();!e.done;e=d.next())e=e.value,sa.call(b,"string"===typeof e?document.createTextNode(e):e,this)}}})}R(CharacterData);R(Element);var S,T,ua=Node.prototype.removeChild,va=null!==(T=null===(S=Object.getOwnPropertyDescriptor(Node.prototype,"parentNode"))||void 0===S?void 0:S.get)&&void 0!==T?T:function(){return this.parentNode};function V(a){a=a.prototype;a.hasOwnProperty("remove")||Object.defineProperty(a,"remove",{configurable:!0,enumerable:!0,writable:!0,value:function(){var c=va.call(this);c&&ua.call(c,this)}})}V(CharacterData);V(Element);var W,X,wa=Node.prototype.insertBefore,xa=Node.prototype.removeChild,ya=null!==(X=null===(W=Object.getOwnPropertyDescriptor(Node.prototype,"parentNode"))||void 0===W?void 0:W.get)&&void 0!==X?X:function(){return this.parentNode};
function Y(a){a=a.prototype;a.hasOwnProperty("replaceWith")||Object.defineProperty(a,"replaceWith",{configurable:!0,enumerable:!0,writable:!0,value:function(c){for(var d=[],b=0;b<arguments.length;++b)d[b]=arguments[b];b=ya.call(this);if(null!==b){d=h(d);for(var e=d.next();!e.done;e=d.next())e=e.value,wa.call(b,"string"===typeof e?document.createTextNode(e):e,this);xa.call(b,this)}}})}Y(CharacterData);Y(Element);var Z=window.Element.prototype,za=window.HTMLElement.prototype,Aa=window.SVGElement.prototype;!za.hasOwnProperty("classList")||Z.hasOwnProperty("classList")||Aa.hasOwnProperty("classList")||Object.defineProperty(Z,"classList",Object.getOwnPropertyDescriptor(za,"classList"));}).call(this);

//# sourceMappingURL=webcomponents-pf_dom.js.map
