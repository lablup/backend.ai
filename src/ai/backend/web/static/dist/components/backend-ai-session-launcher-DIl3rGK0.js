import{Y as e,G as t,H as i,aA as r,M as n,_ as o,K as s,L as l,N as a,U as c,W as d,aB as u,X as h,aC as p,aD as m,n as f,e as g,t as v,h as b,b as y,I as _,a as x,F as w,c as k,i as S,k as C,r as T,ac as M,aE as E,aF as A,aG as L,aH as P,q as R,z as N,p as I,T as D,E as O,P as $,C as z,ak as F,a7 as B,a8 as W,$ as H,B as U,g as V,d as q,s as j,l as G,Q as K,f as X,A as Y}from"./backend-ai-webui-BJUcX0PI.js";import"./lablup-progress-bar-DIfN72v9.js";import"./mwc-check-list-item-Cpll3j5B.js";
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const Z=(e,t)=>"method"===t.kind&&t.descriptor&&!("value"in t.descriptor)?{...t,finisher(i){i.createProperty(t.key,e)}}:{kind:"field",key:Symbol(),placement:"own",descriptor:{},originalKey:t.key,initializer(){"function"==typeof t.initializer&&(this[t.key]=t.initializer.call(this))},finisher(i){i.createProperty(t.key,e)}},J=(e,t,i)=>{t.constructor.createProperty(i,e)};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */function Q(e){return(t,i)=>void 0!==i?J(e,t,i):Z(e,t)
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */}function ee(e){return Q({...e,state:!0})}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const te=({finisher:e,descriptor:t})=>(i,r)=>{var n;if(void 0===r){const r=null!==(n=i.originalKey)&&void 0!==n?n:i.key,o=null!=t?{kind:"method",placement:"prototype",key:r,descriptor:t(i.key)}:{...i,key:r};return null!=e&&(o.finisher=function(t){e(t,r)}),o}{const n=i.constructor;void 0!==t&&Object.defineProperty(i,r,t(r)),null==e||e(n,r)}}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */;function ie(e,t){return te({descriptor:t=>{const i={get(){var t,i;return null!==(i=null===(t=this.renderRoot)||void 0===t?void 0:t.querySelector(e))&&void 0!==i?i:null},enumerable:!0,configurable:!0};return i}})}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
var re;null===(re=window.HTMLSlotElement)||void 0===re||re.prototype.assignedElements;
/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const ne=window,oe=ne.ShadowRoot&&(void 0===ne.ShadyCSS||ne.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,se=Symbol(),le=new WeakMap;let ae=class{constructor(e,t,i){if(this._$cssResult$=!0,i!==se)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const t=this.t;if(oe&&void 0===e){const i=void 0!==t&&1===t.length;i&&(e=le.get(t)),void 0===e&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),i&&le.set(t,e))}return e}toString(){return this.cssText}};const ce=(e,t)=>{oe?e.adoptedStyleSheets=t.map((e=>e instanceof CSSStyleSheet?e:e.styleSheet)):t.forEach((t=>{const i=document.createElement("style"),r=ne.litNonce;void 0!==r&&i.setAttribute("nonce",r),i.textContent=t.cssText,e.appendChild(i)}))},de=oe?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t="";for(const i of e.cssRules)t+=i.cssText;return(e=>new ae("string"==typeof e?e:e+"",void 0,se))(t)})(e):e
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */;var ue;const he=window,pe=he.trustedTypes,me=pe?pe.emptyScript:"",fe=he.reactiveElementPolyfillSupport,ge={toAttribute(e,t){switch(t){case Boolean:e=e?me:null;break;case Object:case Array:e=null==e?e:JSON.stringify(e)}return e},fromAttribute(e,t){let i=e;switch(t){case Boolean:i=null!==e;break;case Number:i=null===e?null:Number(e);break;case Object:case Array:try{i=JSON.parse(e)}catch(e){i=null}}return i}},ve=(e,t)=>t!==e&&(t==t||e==e),be={attribute:!0,type:String,converter:ge,reflect:!1,hasChanged:ve},ye="finalized";class _e extends HTMLElement{constructor(){super(),this._$Ei=new Map,this.isUpdatePending=!1,this.hasUpdated=!1,this._$El=null,this._$Eu()}static addInitializer(e){var t;this.finalize(),(null!==(t=this.h)&&void 0!==t?t:this.h=[]).push(e)}static get observedAttributes(){this.finalize();const e=[];return this.elementProperties.forEach(((t,i)=>{const r=this._$Ep(i,t);void 0!==r&&(this._$Ev.set(r,i),e.push(r))})),e}static createProperty(e,t=be){if(t.state&&(t.attribute=!1),this.finalize(),this.elementProperties.set(e,t),!t.noAccessor&&!this.prototype.hasOwnProperty(e)){const i="symbol"==typeof e?Symbol():"__"+e,r=this.getPropertyDescriptor(e,i,t);void 0!==r&&Object.defineProperty(this.prototype,e,r)}}static getPropertyDescriptor(e,t,i){return{get(){return this[t]},set(r){const n=this[e];this[t]=r,this.requestUpdate(e,n,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)||be}static finalize(){if(this.hasOwnProperty(ye))return!1;this[ye]=!0;const e=Object.getPrototypeOf(this);if(e.finalize(),void 0!==e.h&&(this.h=[...e.h]),this.elementProperties=new Map(e.elementProperties),this._$Ev=new Map,this.hasOwnProperty("properties")){const e=this.properties,t=[...Object.getOwnPropertyNames(e),...Object.getOwnPropertySymbols(e)];for(const i of t)this.createProperty(i,e[i])}return this.elementStyles=this.finalizeStyles(this.styles),!0}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const i=new Set(e.flat(1/0).reverse());for(const e of i)t.unshift(de(e))}else void 0!==e&&t.push(de(e));return t}static _$Ep(e,t){const i=t.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof e?e.toLowerCase():void 0}_$Eu(){var e;this._$E_=new Promise((e=>this.enableUpdating=e)),this._$AL=new Map,this._$Eg(),this.requestUpdate(),null===(e=this.constructor.h)||void 0===e||e.forEach((e=>e(this)))}addController(e){var t,i;(null!==(t=this._$ES)&&void 0!==t?t:this._$ES=[]).push(e),void 0!==this.renderRoot&&this.isConnected&&(null===(i=e.hostConnected)||void 0===i||i.call(e))}removeController(e){var t;null===(t=this._$ES)||void 0===t||t.splice(this._$ES.indexOf(e)>>>0,1)}_$Eg(){this.constructor.elementProperties.forEach(((e,t)=>{this.hasOwnProperty(t)&&(this._$Ei.set(t,this[t]),delete this[t])}))}createRenderRoot(){var e;const t=null!==(e=this.shadowRoot)&&void 0!==e?e:this.attachShadow(this.constructor.shadowRootOptions);return ce(t,this.constructor.elementStyles),t}connectedCallback(){var e;void 0===this.renderRoot&&(this.renderRoot=this.createRenderRoot()),this.enableUpdating(!0),null===(e=this._$ES)||void 0===e||e.forEach((e=>{var t;return null===(t=e.hostConnected)||void 0===t?void 0:t.call(e)}))}enableUpdating(e){}disconnectedCallback(){var e;null===(e=this._$ES)||void 0===e||e.forEach((e=>{var t;return null===(t=e.hostDisconnected)||void 0===t?void 0:t.call(e)}))}attributeChangedCallback(e,t,i){this._$AK(e,i)}_$EO(e,t,i=be){var r;const n=this.constructor._$Ep(e,i);if(void 0!==n&&!0===i.reflect){const o=(void 0!==(null===(r=i.converter)||void 0===r?void 0:r.toAttribute)?i.converter:ge).toAttribute(t,i.type);this._$El=e,null==o?this.removeAttribute(n):this.setAttribute(n,o),this._$El=null}}_$AK(e,t){var i;const r=this.constructor,n=r._$Ev.get(e);if(void 0!==n&&this._$El!==n){const e=r.getPropertyOptions(n),o="function"==typeof e.converter?{fromAttribute:e.converter}:void 0!==(null===(i=e.converter)||void 0===i?void 0:i.fromAttribute)?e.converter:ge;this._$El=n,this[n]=o.fromAttribute(t,e.type),this._$El=null}}requestUpdate(e,t,i){let r=!0;void 0!==e&&(((i=i||this.constructor.getPropertyOptions(e)).hasChanged||ve)(this[e],t)?(this._$AL.has(e)||this._$AL.set(e,t),!0===i.reflect&&this._$El!==e&&(void 0===this._$EC&&(this._$EC=new Map),this._$EC.set(e,i))):r=!1),!this.isUpdatePending&&r&&(this._$E_=this._$Ej())}async _$Ej(){this.isUpdatePending=!0;try{await this._$E_}catch(e){Promise.reject(e)}const e=this.scheduleUpdate();return null!=e&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){var e;if(!this.isUpdatePending)return;this.hasUpdated,this._$Ei&&(this._$Ei.forEach(((e,t)=>this[t]=e)),this._$Ei=void 0);let t=!1;const i=this._$AL;try{t=this.shouldUpdate(i),t?(this.willUpdate(i),null===(e=this._$ES)||void 0===e||e.forEach((e=>{var t;return null===(t=e.hostUpdate)||void 0===t?void 0:t.call(e)})),this.update(i)):this._$Ek()}catch(e){throw t=!1,this._$Ek(),e}t&&this._$AE(i)}willUpdate(e){}_$AE(e){var t;null===(t=this._$ES)||void 0===t||t.forEach((e=>{var t;return null===(t=e.hostUpdated)||void 0===t?void 0:t.call(e)})),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$Ek(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$E_}shouldUpdate(e){return!0}update(e){void 0!==this._$EC&&(this._$EC.forEach(((e,t)=>this._$EO(t,this[t],e))),this._$EC=void 0),this._$Ek()}updated(e){}firstUpdated(e){}}_e[ye]=!0,_e.elementProperties=new Map,_e.elementStyles=[],_e.shadowRootOptions={mode:"open"},null==fe||fe({ReactiveElement:_e}),(null!==(ue=he.reactiveElementVersions)&&void 0!==ue?ue:he.reactiveElementVersions=[]).push("1.6.3");
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-LIcense-Identifier: Apache-2.0
 */
const xe=e`.mdc-slider{cursor:pointer;height:48px;margin:0 24px;position:relative;touch-action:pan-y}.mdc-slider .mdc-slider__track{height:4px;position:absolute;top:50%;transform:translateY(-50%);width:100%}.mdc-slider .mdc-slider__track--active,.mdc-slider .mdc-slider__track--inactive{display:flex;height:100%;position:absolute;width:100%}.mdc-slider .mdc-slider__track--active{border-radius:3px;height:6px;overflow:hidden;top:-1px}.mdc-slider .mdc-slider__track--active_fill{border-top:6px solid;box-sizing:border-box;height:100%;width:100%;position:relative;-webkit-transform-origin:left;transform-origin:left}[dir=rtl] .mdc-slider .mdc-slider__track--active_fill,.mdc-slider .mdc-slider__track--active_fill[dir=rtl]{-webkit-transform-origin:right;transform-origin:right}.mdc-slider .mdc-slider__track--inactive{border-radius:2px;height:4px;left:0;top:0}.mdc-slider .mdc-slider__track--inactive::before{position:absolute;box-sizing:border-box;width:100%;height:100%;top:0;left:0;border:1px solid transparent;border-radius:inherit;content:"";pointer-events:none}@media screen and (forced-colors: active){.mdc-slider .mdc-slider__track--inactive::before{border-color:CanvasText}}.mdc-slider .mdc-slider__track--active_fill{border-color:#6200ee;border-color:var(--mdc-theme-primary, #6200ee)}.mdc-slider.mdc-slider--disabled .mdc-slider__track--active_fill{border-color:#000;border-color:var(--mdc-theme-on-surface, #000)}.mdc-slider .mdc-slider__track--inactive{background-color:#6200ee;background-color:var(--mdc-theme-primary, #6200ee);opacity:.24}.mdc-slider.mdc-slider--disabled .mdc-slider__track--inactive{background-color:#000;background-color:var(--mdc-theme-on-surface, #000);opacity:.24}.mdc-slider .mdc-slider__value-indicator-container{bottom:44px;left:50%;left:var(--slider-value-indicator-container-left, 50%);pointer-events:none;position:absolute;right:var(--slider-value-indicator-container-right);transform:translateX(-50%);transform:var(--slider-value-indicator-container-transform, translateX(-50%))}.mdc-slider .mdc-slider__value-indicator{transition:transform 100ms 0ms cubic-bezier(0.4, 0, 1, 1);align-items:center;border-radius:4px;display:flex;height:32px;padding:0 12px;transform:scale(0);transform-origin:bottom}.mdc-slider .mdc-slider__value-indicator::before{border-left:6px solid transparent;border-right:6px solid transparent;border-top:6px solid;bottom:-5px;content:"";height:0;left:50%;left:var(--slider-value-indicator-caret-left, 50%);position:absolute;right:var(--slider-value-indicator-caret-right);transform:translateX(-50%);transform:var(--slider-value-indicator-caret-transform, translateX(-50%));width:0}.mdc-slider .mdc-slider__value-indicator::after{position:absolute;box-sizing:border-box;width:100%;height:100%;top:0;left:0;border:1px solid transparent;border-radius:inherit;content:"";pointer-events:none}@media screen and (forced-colors: active){.mdc-slider .mdc-slider__value-indicator::after{border-color:CanvasText}}.mdc-slider .mdc-slider__thumb--with-indicator .mdc-slider__value-indicator-container{pointer-events:auto}.mdc-slider .mdc-slider__thumb--with-indicator .mdc-slider__value-indicator{transition:transform 100ms 0ms cubic-bezier(0, 0, 0.2, 1);transform:scale(1)}@media(prefers-reduced-motion){.mdc-slider .mdc-slider__value-indicator,.mdc-slider .mdc-slider__thumb--with-indicator .mdc-slider__value-indicator{transition:none}}.mdc-slider .mdc-slider__value-indicator-text{-moz-osx-font-smoothing:grayscale;-webkit-font-smoothing:antialiased;font-family:Roboto, sans-serif;font-family:var(--mdc-typography-subtitle2-font-family, var(--mdc-typography-font-family, Roboto, sans-serif));font-size:0.875rem;font-size:var(--mdc-typography-subtitle2-font-size, 0.875rem);line-height:1.375rem;line-height:var(--mdc-typography-subtitle2-line-height, 1.375rem);font-weight:500;font-weight:var(--mdc-typography-subtitle2-font-weight, 500);letter-spacing:0.0071428571em;letter-spacing:var(--mdc-typography-subtitle2-letter-spacing, 0.0071428571em);text-decoration:inherit;text-decoration:var(--mdc-typography-subtitle2-text-decoration, inherit);text-transform:inherit;text-transform:var(--mdc-typography-subtitle2-text-transform, inherit)}.mdc-slider .mdc-slider__value-indicator{background-color:#000;opacity:.6}.mdc-slider .mdc-slider__value-indicator::before{border-top-color:#000}.mdc-slider .mdc-slider__value-indicator{color:#fff;color:var(--mdc-theme-on-primary, #fff)}.mdc-slider .mdc-slider__thumb{display:flex;height:48px;left:-24px;outline:none;position:absolute;user-select:none;width:48px}.mdc-slider .mdc-slider__thumb--top{z-index:1}.mdc-slider .mdc-slider__thumb--top .mdc-slider__thumb-knob,.mdc-slider .mdc-slider__thumb--top.mdc-slider__thumb:hover .mdc-slider__thumb-knob,.mdc-slider .mdc-slider__thumb--top.mdc-slider__thumb--focused .mdc-slider__thumb-knob{border-style:solid;border-width:1px;box-sizing:content-box}.mdc-slider .mdc-slider__thumb-knob{box-shadow:0px 2px 1px -1px rgba(0, 0, 0, 0.2),0px 1px 1px 0px rgba(0, 0, 0, 0.14),0px 1px 3px 0px rgba(0,0,0,.12);border:10px solid;border-radius:50%;box-sizing:border-box;height:20px;left:50%;position:absolute;top:50%;transform:translate(-50%, -50%);width:20px}.mdc-slider .mdc-slider__thumb-knob{background-color:#6200ee;background-color:var(--mdc-theme-primary, #6200ee);border-color:#6200ee;border-color:var(--mdc-theme-primary, #6200ee)}.mdc-slider .mdc-slider__thumb--top .mdc-slider__thumb-knob,.mdc-slider .mdc-slider__thumb--top.mdc-slider__thumb:hover .mdc-slider__thumb-knob,.mdc-slider .mdc-slider__thumb--top.mdc-slider__thumb--focused .mdc-slider__thumb-knob{border-color:#fff}.mdc-slider.mdc-slider--disabled .mdc-slider__thumb-knob{background-color:#000;background-color:var(--mdc-theme-on-surface, #000);border-color:#000;border-color:var(--mdc-theme-on-surface, #000)}.mdc-slider.mdc-slider--disabled .mdc-slider__thumb--top .mdc-slider__thumb-knob,.mdc-slider.mdc-slider--disabled .mdc-slider__thumb--top.mdc-slider__thumb:hover .mdc-slider__thumb-knob,.mdc-slider.mdc-slider--disabled .mdc-slider__thumb--top.mdc-slider__thumb--focused .mdc-slider__thumb-knob{border-color:#fff}.mdc-slider .mdc-slider__thumb::before,.mdc-slider .mdc-slider__thumb::after{background-color:#6200ee;background-color:var(--mdc-ripple-color, var(--mdc-theme-primary, #6200ee))}.mdc-slider .mdc-slider__thumb:hover::before,.mdc-slider .mdc-slider__thumb.mdc-ripple-surface--hover::before{opacity:0.04;opacity:var(--mdc-ripple-hover-opacity, 0.04)}.mdc-slider .mdc-slider__thumb.mdc-ripple-upgraded--background-focused::before,.mdc-slider .mdc-slider__thumb:not(.mdc-ripple-upgraded):focus::before{transition-duration:75ms;opacity:0.12;opacity:var(--mdc-ripple-focus-opacity, 0.12)}.mdc-slider .mdc-slider__thumb:not(.mdc-ripple-upgraded)::after{transition:opacity 150ms linear}.mdc-slider .mdc-slider__thumb:not(.mdc-ripple-upgraded):active::after{transition-duration:75ms;opacity:0.12;opacity:var(--mdc-ripple-press-opacity, 0.12)}.mdc-slider .mdc-slider__thumb.mdc-ripple-upgraded{--mdc-ripple-fg-opacity:var(--mdc-ripple-press-opacity, 0.12)}.mdc-slider .mdc-slider__tick-marks{align-items:center;box-sizing:border-box;display:flex;height:100%;justify-content:space-between;padding:0 1px;position:absolute;width:100%}.mdc-slider .mdc-slider__tick-mark--active,.mdc-slider .mdc-slider__tick-mark--inactive{border-radius:50%;height:2px;width:2px}.mdc-slider .mdc-slider__tick-mark--active{background-color:#fff;background-color:var(--mdc-theme-on-primary, #fff);opacity:.6}.mdc-slider.mdc-slider--disabled .mdc-slider__tick-mark--active{background-color:#fff;background-color:var(--mdc-theme-on-primary, #fff);opacity:.6}.mdc-slider .mdc-slider__tick-mark--inactive{background-color:#6200ee;background-color:var(--mdc-theme-primary, #6200ee);opacity:.6}.mdc-slider.mdc-slider--disabled .mdc-slider__tick-mark--inactive{background-color:#000;background-color:var(--mdc-theme-on-surface, #000);opacity:.6}.mdc-slider--discrete .mdc-slider__thumb,.mdc-slider--discrete .mdc-slider__track--active_fill{transition:transform 80ms ease}@media(prefers-reduced-motion){.mdc-slider--discrete .mdc-slider__thumb,.mdc-slider--discrete .mdc-slider__track--active_fill{transition:none}}.mdc-slider--disabled{opacity:.38;cursor:auto}.mdc-slider--disabled .mdc-slider__thumb{pointer-events:none}.mdc-slider__input{cursor:pointer;left:0;margin:0;height:100%;opacity:0;pointer-events:none;position:absolute;top:0;width:100%}:host{outline:none;display:block;-webkit-tap-highlight-color:transparent}.ripple{--mdc-ripple-color:#6200ee;--mdc-ripple-color:var(--mdc-theme-primary, #6200ee)}`
/**
 * @license
 * Copyright 2020 Google Inc.
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
 */;var we,ke;!function(e){e[e.ACTIVE=0]="ACTIVE",e[e.INACTIVE=1]="INACTIVE"}(we||(we={})),function(e){e[e.START=1]="START",e[e.END=2]="END"}(ke||(ke={}));
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
 */
var Se={animation:{prefixed:"-webkit-animation",standard:"animation"},transform:{prefixed:"-webkit-transform",standard:"transform"},transition:{prefixed:"-webkit-transition",standard:"transition"}};function Ce(e,t){if(function(e){return Boolean(e.document)&&"function"==typeof e.document.createElement}(e)&&t in Se){var i=e.document.createElement("div"),r=Se[t],n=r.standard,o=r.prefixed;return n in i.style?n:o}return t}
/**
 * @license
 * Copyright 2020 Google Inc.
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
 */var Te,Me="mdc-slider--disabled",Ee="mdc-slider--discrete",Ae="mdc-slider--range",Le="mdc-slider__thumb--focused",Pe="mdc-slider__thumb--top",Re="mdc-slider__thumb--with-indicator",Ne="mdc-slider--tick-marks",Ie=1,De=0,Oe=5,$e="aria-valuetext",ze="disabled",Fe="min",Be="max",We="value",He="step",Ue="data-min-range",Ve="--slider-value-indicator-caret-left",qe="--slider-value-indicator-caret-right",je="--slider-value-indicator-caret-transform",Ge="--slider-value-indicator-container-left",Ke="--slider-value-indicator-container-right",Xe="--slider-value-indicator-container-transform";!function(e){e.SLIDER_UPDATE="slider_update"}(Te||(Te={}));var Ye="undefined"!=typeof window,Ze=function(e){function n(t){var o=e.call(this,i(i({},n.defaultAdapter),t))||this;return o.initialStylesRemoved=!1,o.isDisabled=!1,o.isDiscrete=!1,o.step=Ie,o.minRange=De,o.hasTickMarks=!1,o.isRange=!1,o.thumb=null,o.downEventClientX=null,o.startThumbKnobWidth=0,o.endThumbKnobWidth=0,o.animFrame=new r,o}return t(n,e),Object.defineProperty(n,"defaultAdapter",{get:function(){return{hasClass:function(){return!1},addClass:function(){},removeClass:function(){},addThumbClass:function(){},removeThumbClass:function(){},getAttribute:function(){return null},getInputValue:function(){return""},setInputValue:function(){},getInputAttribute:function(){return null},setInputAttribute:function(){return null},removeInputAttribute:function(){return null},focusInput:function(){},isInputFocused:function(){return!1},shouldHideFocusStylesForPointerEvents:function(){return!1},getThumbKnobWidth:function(){return 0},getValueIndicatorContainerWidth:function(){return 0},getThumbBoundingClientRect:function(){return{top:0,right:0,bottom:0,left:0,width:0,height:0}},getBoundingClientRect:function(){return{top:0,right:0,bottom:0,left:0,width:0,height:0}},isRTL:function(){return!1},setThumbStyleProperty:function(){},removeThumbStyleProperty:function(){},setTrackActiveStyleProperty:function(){},removeTrackActiveStyleProperty:function(){},setValueIndicatorText:function(){},getValueToAriaValueTextFn:function(){return null},updateTickMarks:function(){},setPointerCapture:function(){},emitChangeEvent:function(){},emitInputEvent:function(){},emitDragStartEvent:function(){},emitDragEndEvent:function(){},registerEventHandler:function(){},deregisterEventHandler:function(){},registerThumbEventHandler:function(){},deregisterThumbEventHandler:function(){},registerInputEventHandler:function(){},deregisterInputEventHandler:function(){},registerBodyEventHandler:function(){},deregisterBodyEventHandler:function(){},registerWindowEventHandler:function(){},deregisterWindowEventHandler:function(){}}},enumerable:!1,configurable:!0}),n.prototype.init=function(){var e=this;this.isDisabled=this.adapter.hasClass(Me),this.isDiscrete=this.adapter.hasClass(Ee),this.hasTickMarks=this.adapter.hasClass(Ne),this.isRange=this.adapter.hasClass(Ae);var t=this.convertAttributeValueToNumber(this.adapter.getInputAttribute(Fe,this.isRange?ke.START:ke.END),Fe),i=this.convertAttributeValueToNumber(this.adapter.getInputAttribute(Be,ke.END),Be),r=this.convertAttributeValueToNumber(this.adapter.getInputAttribute(We,ke.END),We),n=this.isRange?this.convertAttributeValueToNumber(this.adapter.getInputAttribute(We,ke.START),We):t,o=this.adapter.getInputAttribute(He,ke.END),s=o?this.convertAttributeValueToNumber(o,He):this.step,l=this.adapter.getAttribute(Ue),a=l?this.convertAttributeValueToNumber(l,Ue):this.minRange;this.validateProperties({min:t,max:i,value:r,valueStart:n,step:s,minRange:a}),this.min=t,this.max=i,this.value=r,this.valueStart=n,this.step=s,this.minRange=a,this.numDecimalPlaces=Je(this.step),this.valueBeforeDownEvent=r,this.valueStartBeforeDownEvent=n,this.mousedownOrTouchstartListener=this.handleMousedownOrTouchstart.bind(this),this.moveListener=this.handleMove.bind(this),this.pointerdownListener=this.handlePointerdown.bind(this),this.pointerupListener=this.handlePointerup.bind(this),this.thumbMouseenterListener=this.handleThumbMouseenter.bind(this),this.thumbMouseleaveListener=this.handleThumbMouseleave.bind(this),this.inputStartChangeListener=function(){e.handleInputChange(ke.START)},this.inputEndChangeListener=function(){e.handleInputChange(ke.END)},this.inputStartFocusListener=function(){e.handleInputFocus(ke.START)},this.inputEndFocusListener=function(){e.handleInputFocus(ke.END)},this.inputStartBlurListener=function(){e.handleInputBlur(ke.START)},this.inputEndBlurListener=function(){e.handleInputBlur(ke.END)},this.resizeListener=this.handleResize.bind(this),this.registerEventHandlers()},n.prototype.destroy=function(){this.deregisterEventHandlers()},n.prototype.setMin=function(e){this.min=e,this.isRange||(this.valueStart=e),this.updateUI()},n.prototype.setMax=function(e){this.max=e,this.updateUI()},n.prototype.getMin=function(){return this.min},n.prototype.getMax=function(){return this.max},n.prototype.getValue=function(){return this.value},n.prototype.setValue=function(e){if(this.isRange&&e<this.valueStart+this.minRange)throw new Error("end thumb value ("+e+") must be >= start thumb value ("+this.valueStart+") + min range ("+this.minRange+")");this.updateValue(e,ke.END)},n.prototype.getValueStart=function(){if(!this.isRange)throw new Error("`valueStart` is only applicable for range sliders.");return this.valueStart},n.prototype.setValueStart=function(e){if(!this.isRange)throw new Error("`valueStart` is only applicable for range sliders.");if(this.isRange&&e>this.value-this.minRange)throw new Error("start thumb value ("+e+") must be <= end thumb value ("+this.value+") - min range ("+this.minRange+")");this.updateValue(e,ke.START)},n.prototype.setStep=function(e){this.step=e,this.numDecimalPlaces=Je(e),this.updateUI()},n.prototype.setMinRange=function(e){if(!this.isRange)throw new Error("`minRange` is only applicable for range sliders.");if(e<0)throw new Error("`minRange` must be non-negative. Current value: "+e);if(this.value-this.valueStart<e)throw new Error("start thumb value ("+this.valueStart+") and end thumb value ("+this.value+") must differ by at least "+e+".");this.minRange=e},n.prototype.setIsDiscrete=function(e){this.isDiscrete=e,this.updateValueIndicatorUI(),this.updateTickMarksUI()},n.prototype.getStep=function(){return this.step},n.prototype.getMinRange=function(){if(!this.isRange)throw new Error("`minRange` is only applicable for range sliders.");return this.minRange},n.prototype.setHasTickMarks=function(e){this.hasTickMarks=e,this.updateTickMarksUI()},n.prototype.getDisabled=function(){return this.isDisabled},n.prototype.setDisabled=function(e){this.isDisabled=e,e?(this.adapter.addClass(Me),this.isRange&&this.adapter.setInputAttribute(ze,"",ke.START),this.adapter.setInputAttribute(ze,"",ke.END)):(this.adapter.removeClass(Me),this.isRange&&this.adapter.removeInputAttribute(ze,ke.START),this.adapter.removeInputAttribute(ze,ke.END))},n.prototype.getIsRange=function(){return this.isRange},n.prototype.layout=function(e){var t=(void 0===e?{}:e).skipUpdateUI;this.rect=this.adapter.getBoundingClientRect(),this.isRange&&(this.startThumbKnobWidth=this.adapter.getThumbKnobWidth(ke.START),this.endThumbKnobWidth=this.adapter.getThumbKnobWidth(ke.END)),t||this.updateUI()},n.prototype.handleResize=function(){this.layout()},n.prototype.handleDown=function(e){if(!this.isDisabled){this.valueStartBeforeDownEvent=this.valueStart,this.valueBeforeDownEvent=this.value;var t=null!=e.clientX?e.clientX:e.targetTouches[0].clientX;this.downEventClientX=t;var i=this.mapClientXOnSliderScale(t);this.thumb=this.getThumbFromDownEvent(t,i),null!==this.thumb&&(this.handleDragStart(e,i,this.thumb),this.updateValue(i,this.thumb,{emitInputEvent:!0}))}},n.prototype.handleMove=function(e){if(!this.isDisabled){e.preventDefault();var t=null!=e.clientX?e.clientX:e.targetTouches[0].clientX,i=null!=this.thumb;if(this.thumb=this.getThumbFromMoveEvent(t),null!==this.thumb){var r=this.mapClientXOnSliderScale(t);i||(this.handleDragStart(e,r,this.thumb),this.adapter.emitDragStartEvent(r,this.thumb)),this.updateValue(r,this.thumb,{emitInputEvent:!0})}}},n.prototype.handleUp=function(){var e,t;if(!this.isDisabled&&null!==this.thumb){(null===(t=(e=this.adapter).shouldHideFocusStylesForPointerEvents)||void 0===t?void 0:t.call(e))&&this.handleInputBlur(this.thumb);var i=this.thumb===ke.START?this.valueStartBeforeDownEvent:this.valueBeforeDownEvent,r=this.thumb===ke.START?this.valueStart:this.value;i!==r&&this.adapter.emitChangeEvent(r,this.thumb),this.adapter.emitDragEndEvent(r,this.thumb),this.thumb=null}},n.prototype.handleThumbMouseenter=function(){this.isDiscrete&&this.isRange&&(this.adapter.addThumbClass(Re,ke.START),this.adapter.addThumbClass(Re,ke.END))},n.prototype.handleThumbMouseleave=function(){var e,t;this.isDiscrete&&this.isRange&&(!(null===(t=(e=this.adapter).shouldHideFocusStylesForPointerEvents)||void 0===t?void 0:t.call(e))&&(this.adapter.isInputFocused(ke.START)||this.adapter.isInputFocused(ke.END))||this.thumb||(this.adapter.removeThumbClass(Re,ke.START),this.adapter.removeThumbClass(Re,ke.END)))},n.prototype.handleMousedownOrTouchstart=function(e){var t=this,i="mousedown"===e.type?"mousemove":"touchmove";this.adapter.registerBodyEventHandler(i,this.moveListener);var r=function(){t.handleUp(),t.adapter.deregisterBodyEventHandler(i,t.moveListener),t.adapter.deregisterEventHandler("mouseup",r),t.adapter.deregisterEventHandler("touchend",r)};this.adapter.registerBodyEventHandler("mouseup",r),this.adapter.registerBodyEventHandler("touchend",r),this.handleDown(e)},n.prototype.handlePointerdown=function(e){0===e.button&&(null!=e.pointerId&&this.adapter.setPointerCapture(e.pointerId),this.adapter.registerEventHandler("pointermove",this.moveListener),this.handleDown(e))},n.prototype.handleInputChange=function(e){var t=Number(this.adapter.getInputValue(e));e===ke.START?this.setValueStart(t):this.setValue(t),this.adapter.emitChangeEvent(e===ke.START?this.valueStart:this.value,e),this.adapter.emitInputEvent(e===ke.START?this.valueStart:this.value,e)},n.prototype.handleInputFocus=function(e){if(this.adapter.addThumbClass(Le,e),this.isDiscrete&&(this.adapter.addThumbClass(Re,e),this.isRange)){var t=e===ke.START?ke.END:ke.START;this.adapter.addThumbClass(Re,t)}},n.prototype.handleInputBlur=function(e){if(this.adapter.removeThumbClass(Le,e),this.isDiscrete&&(this.adapter.removeThumbClass(Re,e),this.isRange)){var t=e===ke.START?ke.END:ke.START;this.adapter.removeThumbClass(Re,t)}},n.prototype.handleDragStart=function(e,t,i){var r,n;this.adapter.emitDragStartEvent(t,i),this.adapter.focusInput(i),(null===(n=(r=this.adapter).shouldHideFocusStylesForPointerEvents)||void 0===n?void 0:n.call(r))&&this.handleInputFocus(i),e.preventDefault()},n.prototype.getThumbFromDownEvent=function(e,t){if(!this.isRange)return ke.END;var i=this.adapter.getThumbBoundingClientRect(ke.START),r=this.adapter.getThumbBoundingClientRect(ke.END),n=e>=i.left&&e<=i.right,o=e>=r.left&&e<=r.right;return n&&o?null:n?ke.START:o?ke.END:t<this.valueStart?ke.START:t>this.value?ke.END:t-this.valueStart<=this.value-t?ke.START:ke.END},n.prototype.getThumbFromMoveEvent=function(e){if(null!==this.thumb)return this.thumb;if(null===this.downEventClientX)throw new Error("`downEventClientX` is null after move event.");return Math.abs(this.downEventClientX-e)<Oe?this.thumb:e<this.downEventClientX?this.adapter.isRTL()?ke.END:ke.START:this.adapter.isRTL()?ke.START:ke.END},n.prototype.updateUI=function(e){e?this.updateThumbAndInputAttributes(e):(this.updateThumbAndInputAttributes(ke.START),this.updateThumbAndInputAttributes(ke.END)),this.updateThumbAndTrackUI(e),this.updateValueIndicatorUI(e),this.updateTickMarksUI()},n.prototype.updateThumbAndInputAttributes=function(e){if(e){var t=this.isRange&&e===ke.START?this.valueStart:this.value,i=String(t);this.adapter.setInputAttribute(We,i,e),this.isRange&&e===ke.START?this.adapter.setInputAttribute(Fe,String(t+this.minRange),ke.END):this.isRange&&e===ke.END&&this.adapter.setInputAttribute(Be,String(t-this.minRange),ke.START),this.adapter.getInputValue(e)!==i&&this.adapter.setInputValue(i,e);var r=this.adapter.getValueToAriaValueTextFn();r&&this.adapter.setInputAttribute($e,r(t,e),e)}},n.prototype.updateValueIndicatorUI=function(e){if(this.isDiscrete){var t=this.isRange&&e===ke.START?this.valueStart:this.value;this.adapter.setValueIndicatorText(t,e===ke.START?ke.START:ke.END),!e&&this.isRange&&this.adapter.setValueIndicatorText(this.valueStart,ke.START)}},n.prototype.updateTickMarksUI=function(){if(this.isDiscrete&&this.hasTickMarks){var e=(this.valueStart-this.min)/this.step,t=(this.value-this.valueStart)/this.step+1,i=(this.max-this.value)/this.step,r=Array.from({length:e}).fill(we.INACTIVE),n=Array.from({length:t}).fill(we.ACTIVE),o=Array.from({length:i}).fill(we.INACTIVE);this.adapter.updateTickMarks(r.concat(n).concat(o))}},n.prototype.mapClientXOnSliderScale=function(e){var t=(e-this.rect.left)/this.rect.width;this.adapter.isRTL()&&(t=1-t);var i=this.min+t*(this.max-this.min);return i===this.max||i===this.min?i:Number(this.quantize(i).toFixed(this.numDecimalPlaces))},n.prototype.quantize=function(e){var t=Math.round((e-this.min)/this.step);return this.min+t*this.step},n.prototype.updateValue=function(e,t,i){var r=(void 0===i?{}:i).emitInputEvent;if(e=this.clampValue(e,t),this.isRange&&t===ke.START){if(this.valueStart===e)return;this.valueStart=e}else{if(this.value===e)return;this.value=e}this.updateUI(t),r&&this.adapter.emitInputEvent(t===ke.START?this.valueStart:this.value,t)},n.prototype.clampValue=function(e,t){return e=Math.min(Math.max(e,this.min),this.max),this.isRange&&t===ke.START&&e>this.value-this.minRange?this.value-this.minRange:this.isRange&&t===ke.END&&e<this.valueStart+this.minRange?this.valueStart+this.minRange:e},n.prototype.updateThumbAndTrackUI=function(e){var t=this,i=this.max,r=this.min,n=(this.value-this.valueStart)/(i-r),o=n*this.rect.width,s=this.adapter.isRTL(),l=Ye?Ce(window,"transform"):"transform";if(this.isRange){var a=this.adapter.isRTL()?(i-this.value)/(i-r)*this.rect.width:(this.valueStart-r)/(i-r)*this.rect.width,c=a+o;this.animFrame.request(Te.SLIDER_UPDATE,(function(){!s&&e===ke.START||s&&e!==ke.START?(t.adapter.setTrackActiveStyleProperty("transform-origin","right"),t.adapter.setTrackActiveStyleProperty("left","auto"),t.adapter.setTrackActiveStyleProperty("right",t.rect.width-c+"px")):(t.adapter.setTrackActiveStyleProperty("transform-origin","left"),t.adapter.setTrackActiveStyleProperty("right","auto"),t.adapter.setTrackActiveStyleProperty("left",a+"px")),t.adapter.setTrackActiveStyleProperty(l,"scaleX("+n+")");var i=s?c:a,r=t.adapter.isRTL()?a:c;e!==ke.START&&e&&t.initialStylesRemoved||(t.adapter.setThumbStyleProperty(l,"translateX("+i+"px)",ke.START),t.alignValueIndicator(ke.START,i)),e!==ke.END&&e&&t.initialStylesRemoved||(t.adapter.setThumbStyleProperty(l,"translateX("+r+"px)",ke.END),t.alignValueIndicator(ke.END,r)),t.removeInitialStyles(s),t.updateOverlappingThumbsUI(i,r,e)}))}else this.animFrame.request(Te.SLIDER_UPDATE,(function(){var e=s?t.rect.width-o:o;t.adapter.setThumbStyleProperty(l,"translateX("+e+"px)",ke.END),t.alignValueIndicator(ke.END,e),t.adapter.setTrackActiveStyleProperty(l,"scaleX("+n+")"),t.removeInitialStyles(s)}))},n.prototype.alignValueIndicator=function(e,t){if(this.isDiscrete){var i=this.adapter.getThumbBoundingClientRect(e).width/2,r=this.adapter.getValueIndicatorContainerWidth(e),n=this.adapter.getBoundingClientRect().width;r/2>t+i?(this.adapter.setThumbStyleProperty(Ve,i+"px",e),this.adapter.setThumbStyleProperty(qe,"auto",e),this.adapter.setThumbStyleProperty(je,"translateX(-50%)",e),this.adapter.setThumbStyleProperty(Ge,"0",e),this.adapter.setThumbStyleProperty(Ke,"auto",e),this.adapter.setThumbStyleProperty(Xe,"none",e)):r/2>n-t+i?(this.adapter.setThumbStyleProperty(Ve,"auto",e),this.adapter.setThumbStyleProperty(qe,i+"px",e),this.adapter.setThumbStyleProperty(je,"translateX(50%)",e),this.adapter.setThumbStyleProperty(Ge,"auto",e),this.adapter.setThumbStyleProperty(Ke,"0",e),this.adapter.setThumbStyleProperty(Xe,"none",e)):(this.adapter.setThumbStyleProperty(Ve,"50%",e),this.adapter.setThumbStyleProperty(qe,"auto",e),this.adapter.setThumbStyleProperty(je,"translateX(-50%)",e),this.adapter.setThumbStyleProperty(Ge,"50%",e),this.adapter.setThumbStyleProperty(Ke,"auto",e),this.adapter.setThumbStyleProperty(Xe,"translateX(-50%)",e))}},n.prototype.removeInitialStyles=function(e){if(!this.initialStylesRemoved){var t=e?"right":"left";this.adapter.removeThumbStyleProperty(t,ke.END),this.isRange&&this.adapter.removeThumbStyleProperty(t,ke.START),this.initialStylesRemoved=!0,this.resetTrackAndThumbAnimation()}},n.prototype.resetTrackAndThumbAnimation=function(){var e=this;if(this.isDiscrete){var t=Ye?Ce(window,"transition"):"transition",i="none 0s ease 0s";this.adapter.setThumbStyleProperty(t,i,ke.END),this.isRange&&this.adapter.setThumbStyleProperty(t,i,ke.START),this.adapter.setTrackActiveStyleProperty(t,i),requestAnimationFrame((function(){e.adapter.removeThumbStyleProperty(t,ke.END),e.adapter.removeTrackActiveStyleProperty(t),e.isRange&&e.adapter.removeThumbStyleProperty(t,ke.START)}))}},n.prototype.updateOverlappingThumbsUI=function(e,t,i){var r=!1;if(this.adapter.isRTL()){var n=e-this.startThumbKnobWidth/2;r=t+this.endThumbKnobWidth/2>=n}else{r=e+this.startThumbKnobWidth/2>=t-this.endThumbKnobWidth/2}r?(this.adapter.addThumbClass(Pe,i||ke.END),this.adapter.removeThumbClass(Pe,i===ke.START?ke.END:ke.START)):(this.adapter.removeThumbClass(Pe,ke.START),this.adapter.removeThumbClass(Pe,ke.END))},n.prototype.convertAttributeValueToNumber=function(e,t){if(null===e)throw new Error("MDCSliderFoundation: `"+t+"` must be non-null.");var i=Number(e);if(isNaN(i))throw new Error("MDCSliderFoundation: `"+t+"` value is `"+e+"`, but must be a number.");return i},n.prototype.validateProperties=function(e){var t=e.min,i=e.max,r=e.value,n=e.valueStart,o=e.step,s=e.minRange;if(t>=i)throw new Error("MDCSliderFoundation: min must be strictly less than max. Current: [min: "+t+", max: "+i+"]");if(o<=0)throw new Error("MDCSliderFoundation: step must be a positive number. Current step: "+o);if(this.isRange){if(r<t||r>i||n<t||n>i)throw new Error("MDCSliderFoundation: values must be in [min, max] range. Current values: [start value: "+n+", end value: "+r+", min: "+t+", max: "+i+"]");if(n>r)throw new Error("MDCSliderFoundation: start value must be <= end value. Current values: [start value: "+n+", end value: "+r+"]");if(s<0)throw new Error("MDCSliderFoundation: minimum range must be non-negative. Current min range: "+s);if(r-n<s)throw new Error("MDCSliderFoundation: start value and end value must differ by at least "+s+". Current values: [start value: "+n+", end value: "+r+"]");var l=(n-t)/o,a=(r-t)/o;if(!Number.isInteger(parseFloat(l.toFixed(6)))||!Number.isInteger(parseFloat(a.toFixed(6))))throw new Error("MDCSliderFoundation: Slider values must be valid based on the step value ("+o+"). Current values: [start value: "+n+", end value: "+r+", min: "+t+"]")}else{if(r<t||r>i)throw new Error("MDCSliderFoundation: value must be in [min, max] range. Current values: [value: "+r+", min: "+t+", max: "+i+"]");a=(r-t)/o;if(!Number.isInteger(parseFloat(a.toFixed(6))))throw new Error("MDCSliderFoundation: Slider value must be valid based on the step value ("+o+"). Current value: "+r)}},n.prototype.registerEventHandlers=function(){this.adapter.registerWindowEventHandler("resize",this.resizeListener),n.SUPPORTS_POINTER_EVENTS?(this.adapter.registerEventHandler("pointerdown",this.pointerdownListener),this.adapter.registerEventHandler("pointerup",this.pointerupListener)):(this.adapter.registerEventHandler("mousedown",this.mousedownOrTouchstartListener),this.adapter.registerEventHandler("touchstart",this.mousedownOrTouchstartListener)),this.isRange&&(this.adapter.registerThumbEventHandler(ke.START,"mouseenter",this.thumbMouseenterListener),this.adapter.registerThumbEventHandler(ke.START,"mouseleave",this.thumbMouseleaveListener),this.adapter.registerInputEventHandler(ke.START,"change",this.inputStartChangeListener),this.adapter.registerInputEventHandler(ke.START,"focus",this.inputStartFocusListener),this.adapter.registerInputEventHandler(ke.START,"blur",this.inputStartBlurListener)),this.adapter.registerThumbEventHandler(ke.END,"mouseenter",this.thumbMouseenterListener),this.adapter.registerThumbEventHandler(ke.END,"mouseleave",this.thumbMouseleaveListener),this.adapter.registerInputEventHandler(ke.END,"change",this.inputEndChangeListener),this.adapter.registerInputEventHandler(ke.END,"focus",this.inputEndFocusListener),this.adapter.registerInputEventHandler(ke.END,"blur",this.inputEndBlurListener)},n.prototype.deregisterEventHandlers=function(){this.adapter.deregisterWindowEventHandler("resize",this.resizeListener),n.SUPPORTS_POINTER_EVENTS?(this.adapter.deregisterEventHandler("pointerdown",this.pointerdownListener),this.adapter.deregisterEventHandler("pointerup",this.pointerupListener)):(this.adapter.deregisterEventHandler("mousedown",this.mousedownOrTouchstartListener),this.adapter.deregisterEventHandler("touchstart",this.mousedownOrTouchstartListener)),this.isRange&&(this.adapter.deregisterThumbEventHandler(ke.START,"mouseenter",this.thumbMouseenterListener),this.adapter.deregisterThumbEventHandler(ke.START,"mouseleave",this.thumbMouseleaveListener),this.adapter.deregisterInputEventHandler(ke.START,"change",this.inputStartChangeListener),this.adapter.deregisterInputEventHandler(ke.START,"focus",this.inputStartFocusListener),this.adapter.deregisterInputEventHandler(ke.START,"blur",this.inputStartBlurListener)),this.adapter.deregisterThumbEventHandler(ke.END,"mouseenter",this.thumbMouseenterListener),this.adapter.deregisterThumbEventHandler(ke.END,"mouseleave",this.thumbMouseleaveListener),this.adapter.deregisterInputEventHandler(ke.END,"change",this.inputEndChangeListener),this.adapter.deregisterInputEventHandler(ke.END,"focus",this.inputEndFocusListener),this.adapter.deregisterInputEventHandler(ke.END,"blur",this.inputEndBlurListener)},n.prototype.handlePointerup=function(){this.handleUp(),this.adapter.deregisterEventHandler("pointermove",this.moveListener)},n.SUPPORTS_POINTER_EVENTS=Ye&&Boolean(window.PointerEvent)&&!(["iPad Simulator","iPhone Simulator","iPod Simulator","iPad","iPhone","iPod"].includes(navigator.platform)||navigator.userAgent.includes("Mac")&&"ontouchend"in document),n}(n);function Je(e){var t=/(?:\.(\d+))?(?:[eE]([+\-]?\d+))?$/.exec(String(e));if(!t)return 0;var i=t[1]||"",r=t[2]||0;return Math.max(0,("0"===i?0:i.length)-Number(r))}
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */class Qe extends l{constructor(){super(...arguments),this.mdcFoundationClass=Ze,this.disabled=!1,this.min=0,this.max=100,this.valueEnd=0,this.name="",this.step=1,this.withTickMarks=!1,this.discrete=!1,this.tickMarks=[],this.trackTransformOriginStyle="",this.trackLeftStyle="",this.trackRightStyle="",this.trackTransitionStyle="",this.endThumbWithIndicator=!1,this.endThumbTop=!1,this.shouldRenderEndRipple=!1,this.endThumbTransformStyle="",this.endThumbTransitionStyle="",this.endThumbCssProperties={},this.valueToAriaTextTransform=null,this.valueToValueIndicatorTransform=e=>`${e}`,this.boundMoveListener=null,this.endRippleHandlers=new a((()=>(this.shouldRenderEndRipple=!0,this.endRipple)))}update(e){if(e.has("valueEnd")&&this.mdcFoundation){this.mdcFoundation.setValue(this.valueEnd);const e=this.mdcFoundation.getValue();e!==this.valueEnd&&(this.valueEnd=e)}e.has("discrete")&&(this.discrete||(this.tickMarks=[])),super.update(e)}render(){return this.renderRootEl(c`
      ${this.renderStartInput()}
      ${this.renderEndInput()}
      ${this.renderTrack()}
      ${this.renderTickMarks()}
      ${this.renderStartThumb()}
      ${this.renderEndThumb()}`)}renderRootEl(e){const t=d({"mdc-slider--disabled":this.disabled,"mdc-slider--discrete":this.discrete});return c`
    <div
        class="mdc-slider ${t}"
        @pointerdown=${this.onPointerdown}
        @pointerup=${this.onPointerup}
        @contextmenu=${this.onContextmenu}>
      ${e}
    </div>`}renderStartInput(){return u}renderEndInput(){var e;return c`
      <input
          class="mdc-slider__input end"
          type="range"
          step=${this.step}
          min=${this.min}
          max=${this.max}
          .value=${this.valueEnd}
          @change=${this.onEndChange}
          @focus=${this.onEndFocus}
          @blur=${this.onEndBlur}
          ?disabled=${this.disabled}
          name=${this.name}
          aria-label=${h(this.ariaLabel)}
          aria-labelledby=${h(this.ariaLabelledBy)}
          aria-describedby=${h(this.ariaDescribedBy)}
          aria-valuetext=${h(null===(e=this.valueToAriaTextTransform)||void 0===e?void 0:e.call(this,this.valueEnd))}>
    `}renderTrack(){return u}renderTickMarks(){return this.withTickMarks?c`
      <div class="mdc-slider__tick-marks">
        ${this.tickMarks.map((e=>{const t=e===we.ACTIVE;return c`<div class="${t?"mdc-slider__tick-mark--active":"mdc-slider__tick-mark--inactive"}"></div>`}))}
      </div>`:u}renderStartThumb(){return u}renderEndThumb(){const e=d({"mdc-slider__thumb--with-indicator":this.endThumbWithIndicator,"mdc-slider__thumb--top":this.endThumbTop}),t=p(Object.assign({"-webkit-transform":this.endThumbTransformStyle,transform:this.endThumbTransformStyle,"-webkit-transition":this.endThumbTransitionStyle,transition:this.endThumbTransitionStyle,left:this.endThumbTransformStyle||"rtl"===getComputedStyle(this).direction?"":`calc(${(this.valueEnd-this.min)/(this.max-this.min)*100}% - 24px)`,right:this.endThumbTransformStyle||"rtl"!==getComputedStyle(this).direction?"":`calc(${(this.valueEnd-this.min)/(this.max-this.min)*100}% - 24px)`},this.endThumbCssProperties)),i=this.shouldRenderEndRipple?c`<mwc-ripple class="ripple" unbounded></mwc-ripple>`:u;return c`
      <div
          class="mdc-slider__thumb end ${e}"
          style=${t}
          @mouseenter=${this.onEndMouseenter}
          @mouseleave=${this.onEndMouseleave}>
        ${i}
        ${this.renderValueIndicator(this.valueToValueIndicatorTransform(this.valueEnd))}
        <div class="mdc-slider__thumb-knob"></div>
      </div>
    `}renderValueIndicator(e){return this.discrete?c`
    <div class="mdc-slider__value-indicator-container" aria-hidden="true">
      <div class="mdc-slider__value-indicator">
        <span class="mdc-slider__value-indicator-text">
          ${e}
        </span>
      </div>
    </div>`:u}disconnectedCallback(){super.disconnectedCallback(),this.mdcFoundation&&this.mdcFoundation.destroy()}createAdapter(){}async firstUpdated(){super.firstUpdated(),await this.layout(!0)}updated(e){super.updated(e),this.mdcFoundation&&(e.has("disabled")&&this.mdcFoundation.setDisabled(this.disabled),e.has("min")&&this.mdcFoundation.setMin(this.min),e.has("max")&&this.mdcFoundation.setMax(this.max),e.has("step")&&this.mdcFoundation.setStep(this.step),e.has("discrete")&&this.mdcFoundation.setIsDiscrete(this.discrete),e.has("withTickMarks")&&this.mdcFoundation.setHasTickMarks(this.withTickMarks))}async layout(e=!1){var t;null===(t=this.mdcFoundation)||void 0===t||t.layout({skipUpdateUI:e}),this.requestUpdate(),await this.updateComplete}onEndChange(e){var t;this.valueEnd=Number(e.target.value),null===(t=this.mdcFoundation)||void 0===t||t.handleInputChange(ke.END)}onEndFocus(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleInputFocus(ke.END),this.endRippleHandlers.startFocus()}onEndBlur(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleInputBlur(ke.END),this.endRippleHandlers.endFocus()}onEndMouseenter(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleThumbMouseenter(),this.endRippleHandlers.startHover()}onEndMouseleave(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleThumbMouseleave(),this.endRippleHandlers.endHover()}onPointerdown(e){this.layout(),this.mdcFoundation&&(this.mdcFoundation.handlePointerdown(e),this.boundMoveListener=this.mdcFoundation.handleMove.bind(this.mdcFoundation),this.mdcRoot.addEventListener("pointermove",this.boundMoveListener))}onPointerup(){this.mdcFoundation&&(this.mdcFoundation.handleUp(),this.boundMoveListener&&(this.mdcRoot.removeEventListener("pointermove",this.boundMoveListener),this.boundMoveListener=null))}onContextmenu(e){e.preventDefault()}setFormData(e){this.name&&e.append(this.name,`${this.valueEnd}`)}}o([ie("input.end")],Qe.prototype,"formElement",void 0),o([ie(".mdc-slider")],Qe.prototype,"mdcRoot",void 0),o([ie(".end.mdc-slider__thumb")],Qe.prototype,"endThumb",void 0),o([ie(".end.mdc-slider__thumb .mdc-slider__thumb-knob")],Qe.prototype,"endThumbKnob",void 0),o([ie(".end.mdc-slider__thumb .mdc-slider__value-indicator-container")],Qe.prototype,"endValueIndicatorContainer",void 0),o([function(e){return te({descriptor:t=>({async get(){var t;return await this.updateComplete,null===(t=this.renderRoot)||void 0===t?void 0:t.querySelector(e)},enumerable:!0,configurable:!0})})}(".end .ripple")],Qe.prototype,"endRipple",void 0),o([Q({type:Boolean,reflect:!0})],Qe.prototype,"disabled",void 0),o([Q({type:Number})],Qe.prototype,"min",void 0),o([Q({type:Number})],Qe.prototype,"max",void 0),o([Q({type:Number})],Qe.prototype,"valueEnd",void 0),o([Q({type:String})],Qe.prototype,"name",void 0),o([Q({type:Number})],Qe.prototype,"step",void 0),o([Q({type:Boolean})],Qe.prototype,"withTickMarks",void 0),o([Q({type:Boolean})],Qe.prototype,"discrete",void 0),o([ee()],Qe.prototype,"tickMarks",void 0),o([ee()],Qe.prototype,"trackTransformOriginStyle",void 0),o([ee()],Qe.prototype,"trackLeftStyle",void 0),o([ee()],Qe.prototype,"trackRightStyle",void 0),o([ee()],Qe.prototype,"trackTransitionStyle",void 0),o([ee()],Qe.prototype,"endThumbWithIndicator",void 0),o([ee()],Qe.prototype,"endThumbTop",void 0),o([ee()],Qe.prototype,"shouldRenderEndRipple",void 0),o([ee()],Qe.prototype,"endThumbTransformStyle",void 0),o([ee()],Qe.prototype,"endThumbTransitionStyle",void 0),o([ee()],Qe.prototype,"endThumbCssProperties",void 0),o([s,Q({type:String,attribute:"aria-label"})],Qe.prototype,"ariaLabel",void 0),o([s,Q({type:String,attribute:"aria-labelledby"})],Qe.prototype,"ariaLabelledBy",void 0),o([s,Q({type:String,attribute:"aria-describedby"})],Qe.prototype,"ariaDescribedBy",void 0);
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
class et extends Qe{get value(){return this.valueEnd}set value(e){this.valueEnd=e}renderTrack(){const e=p({"transform-origin":this.trackTransformOriginStyle,left:this.trackLeftStyle,right:this.trackRightStyle,"-webkit-transform":`scaleX(${(this.valueEnd-this.min)/(this.max-this.min)})`,transform:`scaleX(${(this.valueEnd-this.min)/(this.max-this.min)})`,"-webkit-transition":this.trackTransitionStyle,transition:this.trackTransitionStyle});return c`
      <div class="mdc-slider__track">
        <div class="mdc-slider__track--inactive"></div>
        <div class="mdc-slider__track--active">
          <div
              class="mdc-slider__track--active_fill"
              style=${e}>
          </div>
        </div>
      </div>`}createAdapter(){return{addClass:e=>{if("mdc-slider--disabled"===e)this.disabled=!0},removeClass:e=>{if("mdc-slider--disabled"===e)this.disabled=!1},hasClass:e=>{switch(e){case"mdc-slider--disabled":return this.disabled;case"mdc-slider--discrete":return this.discrete;default:return!1}},addThumbClass:(e,t)=>{if(t!==ke.START&&"mdc-slider__thumb--with-indicator"===e)this.endThumbWithIndicator=!0},removeThumbClass:(e,t)=>{if(t!==ke.START&&"mdc-slider__thumb--with-indicator"===e)this.endThumbWithIndicator=!1},registerEventHandler:()=>{},deregisterEventHandler:()=>{},registerBodyEventHandler:(e,t)=>{document.body.addEventListener(e,t)},deregisterBodyEventHandler:(e,t)=>{document.body.removeEventListener(e,t)},registerInputEventHandler:(e,t,i)=>{e!==ke.START&&this.formElement.addEventListener(t,i)},deregisterInputEventHandler:(e,t,i)=>{e!==ke.START&&this.formElement.removeEventListener(t,i)},registerThumbEventHandler:()=>{},deregisterThumbEventHandler:()=>{},registerWindowEventHandler:(e,t)=>{window.addEventListener(e,t)},deregisterWindowEventHandler:(e,t)=>{window.addEventListener(e,t)},emitChangeEvent:(e,t)=>{if(t===ke.START)return;const i=new CustomEvent("change",{bubbles:!0,composed:!0,detail:{value:e,thumb:t}});this.dispatchEvent(i)},emitDragEndEvent:(e,t)=>{t!==ke.START&&this.endRippleHandlers.endPress()},emitDragStartEvent:(e,t)=>{t!==ke.START&&this.endRippleHandlers.startPress()},emitInputEvent:(e,t)=>{if(t===ke.START)return;const i=new CustomEvent("input",{bubbles:!0,composed:!0,detail:{value:e,thumb:t}});this.dispatchEvent(i)},focusInput:e=>{e!==ke.START&&this.formElement.focus()},getAttribute:()=>"",getBoundingClientRect:()=>this.mdcRoot.getBoundingClientRect(),getInputAttribute:(e,t)=>{if(t===ke.START)return null;switch(e){case"min":return this.min.toString();case"max":return this.max.toString();case"value":return this.valueEnd.toString();case"step":return this.step.toString();default:return null}},getInputValue:e=>e===ke.START?"":this.valueEnd.toString(),getThumbBoundingClientRect:e=>e===ke.START?this.getBoundingClientRect():this.endThumb.getBoundingClientRect(),getThumbKnobWidth:e=>e===ke.START?0:this.endThumbKnob.getBoundingClientRect().width,getValueIndicatorContainerWidth:e=>e===ke.START?0:this.endValueIndicatorContainer.getBoundingClientRect().width,getValueToAriaValueTextFn:()=>this.valueToAriaTextTransform,isInputFocused:e=>{if(e===ke.START)return!1;const t=m();return t[t.length-1]===this.formElement},isRTL:()=>"rtl"===getComputedStyle(this).direction,setInputAttribute:(e,t,i)=>{ke.START},removeInputAttribute:e=>{},setThumbStyleProperty:(e,t,i)=>{if(i!==ke.START)switch(e){case"transform":case"-webkit-transform":this.endThumbTransformStyle=t;break;case"transition":case"-webkit-transition":this.endThumbTransitionStyle=t;break;default:e.startsWith("--")&&(this.endThumbCssProperties[e]=t)}},removeThumbStyleProperty:(e,t)=>{if(t!==ke.START)switch(e){case"left":case"right":break;case"transition":case"-webkit-transition":this.endThumbTransitionStyle=""}},setTrackActiveStyleProperty:(e,t)=>{switch(e){case"transform-origin":this.trackTransformOriginStyle=t;break;case"left":this.trackLeftStyle=t;break;case"right":this.trackRightStyle=t;break;case"transform":case"-webkit-transform":break;case"transition":case"-webkit-transition":this.trackTransitionStyle=t}},removeTrackActiveStyleProperty:e=>{switch(e){case"transition":case"-webkit-transition":this.trackTransitionStyle=""}},setInputValue:(e,t)=>{t!==ke.START&&(this.valueEnd=Number(e))},setPointerCapture:e=>{this.mdcRoot.setPointerCapture(e)},setValueIndicatorText:()=>{},updateTickMarks:e=>{this.tickMarks=e}}}}o([Q({type:Number})],et.prototype,"value",null);
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
let tt=class extends et{};tt.styles=[xe],tt=o([(e=>t=>"function"==typeof t?((e,t)=>(customElements.define(e,t),t))(e,t):((e,t)=>{const{kind:i,elements:r}=t;return{kind:i,elements:r,finisher(t){customElements.define(e,t)}}})(e,t))("mwc-slider")],tt);let it=class extends b{static get styles(){return[y,_,x,w,k,S`
        mwc-textfield {
          width: var(--textfield-min-width, 65px);
          height: 40px;
          margin-left: 10px;
        }

        mwc-slider {
          width: var(--slider-width, 100px);
          --mdc-theme-primary: var(--token-colorPrimary);
          --mdc-theme-secondary: var(
            --token-colorPrimary,
            --slider-color,
            '#018786'
          );
          color: var(--token-colorTextSecondary, --paper-grey-700);
        }
      `]}render(){return C`
      <div class="horizontal center layout">
        <mwc-slider
          id="slider"
          class="${this.id}"
          value="${this.value}"
          min="${this.min}"
          max="${this.max}"
          step="${this.step}"
          ?pin="${this.pin}"
          ?disabled="${this.disabled}"
          ?markers="${this.markers}"
          @change="${()=>this.syncToText()}"
        ></mwc-slider>
        <mwc-textfield
          id="textfield"
          class="${this.id}"
          type="number"
          value="${this.value}"
          min="${this.min}"
          max="${this.max}"
          step="${this.step}"
          prefix="${this.prefix}"
          suffix="${this.suffix}"
          ?disabled="${this.disabled}"
          @change="${()=>this.syncToSlider()}"
        ></mwc-textfield>
      </div>
    `}constructor(){super(),this.editable=!1,this.pin=!1,this.markers=!1,this.marker_limit=30,this.disabled=!1;new IntersectionObserver(((e,t)=>{e.forEach((e=>{e.intersectionRatio>0&&(this.value!==this.slider.value&&(this.slider.value=this.value),this.slider.layout())}))}),{}).observe(this)}firstUpdated(){this.editable&&(this.textfield.style.display="flex"),this.checkMarkerDisplay()}update(e){Array.from(e.keys()).some((e=>["value","min","max"].includes(e)))&&this.min==this.max&&(this.max=this.max+1,this.value=this.min,this.disabled=!0),super.update(e)}updated(e){e.forEach(((e,t)=>{["min","max","step"].includes(t)&&this.checkMarkerDisplay()}))}syncToText(){this.value=this.slider.value}syncToSlider(){this.textfield.step=this.step;const e=Math.round(this.textfield.value/this.step)*this.step;var t;this.textfield.value=e.toFixed((t=this.step,Math.floor(t)===t?0:t.toString().split(".")[1].length||0)),this.textfield.value>this.max&&(this.textfield.value=this.max),this.textfield.value<this.min&&(this.textfield.value=this.min),this.value=this.textfield.value;const i=new CustomEvent("change",{detail:{}});this.dispatchEvent(i)}checkMarkerDisplay(){this.markers&&(this.max-this.min)/this.step>this.marker_limit&&this.slider.removeAttribute("markers")}};o([f({type:Number})],it.prototype,"step",void 0),o([f({type:Number})],it.prototype,"value",void 0),o([f({type:Number})],it.prototype,"max",void 0),o([f({type:Number})],it.prototype,"min",void 0),o([f({type:String})],it.prototype,"prefix",void 0),o([f({type:String})],it.prototype,"suffix",void 0),o([f({type:Boolean})],it.prototype,"editable",void 0),o([f({type:Boolean})],it.prototype,"pin",void 0),o([f({type:Boolean})],it.prototype,"markers",void 0),o([f({type:Number})],it.prototype,"marker_limit",void 0),o([f({type:Boolean})],it.prototype,"disabled",void 0),o([g("#slider",!0)],it.prototype,"slider",void 0),o([g("#textfield",!0)],it.prototype,"textfield",void 0),it=o([v("lablup-slider")],it);const rt=S`
  /* BASICS */
  .CodeMirror {
    /* Set height, width, borders, and global font properties here */
    font-family: monospace;
    height: auto;
    color: black;
    direction: ltr;
  }
  /* PADDING */
  .CodeMirror-lines {
    padding: 4px 0; /* Vertical padding around content */
  }
  .CodeMirror pre.CodeMirror-line,
  .CodeMirror pre.CodeMirror-line-like {
    padding: 0 4px; /* Horizontal padding of content */
  }
  .CodeMirror-scrollbar-filler,
  .CodeMirror-gutter-filler {
    background-color: white; /* The little square between H and V scrollbars */
  }
  /* GUTTER */
  .CodeMirror-gutters {
    border-right: 1px solid var(--token-colorBorder, #ccc);
    background-color: #f7f7f7;
    white-space: nowrap;
  }
  .CodeMirror-linenumbers {
  }
  .CodeMirror-linenumber {
    padding: 0 3px 0 5px;
    min-width: 20px;
    text-align: right;
    color: #999;
    white-space: nowrap;
  }
  .CodeMirror-guttermarker {
    color: black;
  }
  .CodeMirror-guttermarker-subtle {
    color: #999;
  }
  /* CURSOR */
  .CodeMirror-cursor {
    border-left: 1px solid black;
    border-right: none;
    width: 0;
  }
  /* Shown when moving in bi-directional text */
  .CodeMirror div.CodeMirror-secondarycursor {
    border-left: 1px solid silver;
  }
  .cm-fat-cursor .CodeMirror-cursor {
    width: auto;
    border: 0 !important;
    background: #7e7;
  }
  .cm-fat-cursor div.CodeMirror-cursors {
    z-index: 1;
  }
  .cm-fat-cursor-mark {
    background-color: rgba(20, 255, 20, 0.5);
    -webkit-animation: blink 1.06s steps(1) infinite;
    -moz-animation: blink 1.06s steps(1) infinite;
    animation: blink 1.06s steps(1) infinite;
  }
  .cm-animate-fat-cursor {
    width: auto;
    border: 0;
    -webkit-animation: blink 1.06s steps(1) infinite;
    -moz-animation: blink 1.06s steps(1) infinite;
    animation: blink 1.06s steps(1) infinite;
    background-color: #7e7;
  }
  @-moz-keyframes blink {
    0% {
    }
    50% {
      background-color: transparent;
    }
    100% {
    }
  }
  @-webkit-keyframes blink {
    0% {
    }
    50% {
      background-color: transparent;
    }
    100% {
    }
  }
  @keyframes blink {
    0% {
    }
    50% {
      background-color: transparent;
    }
    100% {
    }
  }
  /* Can style cursor different in overwrite (non-insert) mode */
  .CodeMirror-overwrite .CodeMirror-cursor {
  }
  .cm-tab {
    display: inline-block;
    text-decoration: inherit;
  }
  .CodeMirror-rulers {
    position: absolute;
    left: 0;
    right: 0;
    top: -50px;
    bottom: 0;
    overflow: hidden;
  }
  .CodeMirror-ruler {
    border-left: 1px solid var(--token-colorBorder, #ccc);
    top: 0;
    bottom: 0;
    position: absolute;
  }
  /* DEFAULT THEME */
  .cm-s-default .cm-header {
    color: blue;
  }
  .cm-s-default .cm-quote {
    color: #090;
  }
  .cm-negative {
    color: #d44;
  }
  .cm-positive {
    color: #292;
  }
  .cm-header,
  .cm-strong {
    font-weight: bold;
  }
  .cm-em {
    font-style: italic;
  }
  .cm-link {
    text-decoration: underline;
  }
  .cm-strikethrough {
    text-decoration: line-through;
  }
  .cm-s-default .cm-keyword {
    color: #708;
  }
  .cm-s-default .cm-atom {
    color: #219;
  }
  .cm-s-default .cm-number {
    color: #164;
  }
  .cm-s-default .cm-def {
    color: #00f;
  }
  .cm-s-default .cm-variable,
  .cm-s-default .cm-punctuation,
  .cm-s-default .cm-property,
  .cm-s-default .cm-operator {
  }
  .cm-s-default .cm-variable-2 {
    color: #05a;
  }
  .cm-s-default .cm-variable-3,
  .cm-s-default .cm-type {
    color: #085;
  }
  .cm-s-default .cm-comment {
    color: #a50;
  }
  .cm-s-default .cm-string {
    color: #a11;
  }
  .cm-s-default .cm-string-2 {
    color: #f50;
  }
  .cm-s-default .cm-meta {
    color: #555;
  }
  .cm-s-default .cm-qualifier {
    color: #555;
  }
  .cm-s-default .cm-builtin {
    color: #30a;
  }
  .cm-s-default .cm-bracket {
    color: #997;
  }
  .cm-s-default .cm-tag {
    color: #170;
  }
  .cm-s-default .cm-attribute {
    color: #00c;
  }
  .cm-s-default .cm-hr {
    color: #999;
  }
  .cm-s-default .cm-link {
    color: #00c;
  }
  .cm-s-default .cm-error {
    color: #f00;
  }
  .cm-invalidchar {
    color: #f00;
  }
  .CodeMirror-composing {
    border-bottom: 2px solid;
  }
  /* Default styles for common addons */
  div.CodeMirror span.CodeMirror-matchingbracket {
    color: #0b0;
  }
  div.CodeMirror span.CodeMirror-nonmatchingbracket {
    color: #a22;
  }
  .CodeMirror-matchingtag {
    background: rgba(255, 150, 0, 0.3);
  }
  .CodeMirror-activeline-background {
    background: #e8f2ff;
  }
  /* STOP */
  /* The rest of this file contains styles related to the mechanics of
      the editor. You probably shouldn't touch them. */
  .CodeMirror {
    position: relative;
    overflow: hidden;
    background: white;
  }
  .CodeMirror-scroll {
    overflow: scroll !important; /* Things will break if this is overridden */
    /* 50px is the magic margin used to hide the element's real scrollbars */
    /* See overflow: hidden in .CodeMirror */
    margin-bottom: -50px;
    margin-right: -50px;
    padding-bottom: 50px;
    height: 100%;
    outline: none; /* Prevent dragging from highlighting the element */
    position: relative;
  }
  .CodeMirror-sizer {
    position: relative;
    border-right: 50px solid transparent;
  }
  /* The fake, visible scrollbars. Used to force redraw during scrolling
      before actual scrolling happens, thus preventing shaking and
      flickering artifacts. */
  .CodeMirror-vscrollbar,
  .CodeMirror-hscrollbar,
  .CodeMirror-scrollbar-filler,
  .CodeMirror-gutter-filler {
    position: absolute;
    z-index: 6;
    display: none;
  }
  .CodeMirror-vscrollbar {
    right: 0;
    top: 0;
    overflow-x: hidden;
    overflow-y: scroll;
  }
  .CodeMirror-hscrollbar {
    bottom: 0;
    left: 0;
    overflow-y: hidden;
    overflow-x: scroll;
  }
  .CodeMirror-scrollbar-filler {
    right: 0;
    bottom: 0;
  }
  .CodeMirror-gutter-filler {
    left: 0;
    bottom: 0;
  }
  .CodeMirror-gutters {
    position: absolute;
    left: 0;
    top: 0;
    min-height: 100%;
    z-index: 3;
  }
  .CodeMirror-gutter {
    white-space: normal;
    height: 100%;
    display: inline-block;
    vertical-align: top;
    margin-bottom: -50px;
  }
  .CodeMirror-gutter-wrapper {
    position: absolute;
    z-index: 4;
    background: none !important;
    border: none !important;
  }
  .CodeMirror-gutter-background {
    position: absolute;
    top: 0;
    bottom: 0;
    z-index: 4;
  }
  .CodeMirror-gutter-elt {
    position: absolute;
    cursor: default;
    z-index: 4;
  }
  .CodeMirror-gutter-wrapper ::selection {
    background-color: transparent;
  }
  .CodeMirror-gutter-wrapper ::-moz-selection {
    background-color: transparent;
  }
  .CodeMirror-lines {
    cursor: text;
    min-height: 1px; /* prevents collapsing before first draw */
  }
  .CodeMirror pre.CodeMirror-line,
  .CodeMirror pre.CodeMirror-line-like {
    /* Reset some styles that the rest of the page might have set */
    -moz-border-radius: 0;
    -webkit-border-radius: 0;
    border-radius: 0;
    border-width: 0;
    background: transparent;
    font-family: inherit;
    font-size: inherit;
    margin: 0;
    white-space: pre;
    word-wrap: normal;
    line-height: inherit;
    color: inherit;
    z-index: 2;
    position: relative;
    overflow: visible;
    -webkit-tap-highlight-color: transparent;
    -webkit-font-variant-ligatures: contextual;
    font-variant-ligatures: contextual;
  }
  .CodeMirror-wrap pre.CodeMirror-line,
  .CodeMirror-wrap pre.CodeMirror-line-like {
    word-wrap: break-word;
    white-space: pre-wrap;
    word-break: normal;
  }
  .CodeMirror-linebackground {
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    bottom: 0;
    z-index: 0;
  }
  .CodeMirror-linewidget {
    position: relative;
    z-index: 2;
    padding: 0.1px; /* Force widget margins to stay inside of the container */
  }
  .CodeMirror-widget {
  }
  .CodeMirror-rtl pre {
    direction: rtl;
  }
  .CodeMirror-code {
    outline: none;
  }
  /* Force content-box sizing for the elements where we expect it */
  .CodeMirror-scroll,
  .CodeMirror-sizer,
  .CodeMirror-gutter,
  .CodeMirror-gutters,
  .CodeMirror-linenumber {
    -moz-box-sizing: content-box;
    box-sizing: content-box;
  }
  .CodeMirror-measure {
    position: absolute;
    width: 100%;
    height: 0;
    overflow: hidden;
    visibility: hidden;
  }
  .CodeMirror-cursor {
    position: absolute;
    pointer-events: none;
  }
  .CodeMirror-measure pre {
    position: static;
  }
  div.CodeMirror-cursors {
    visibility: hidden;
    position: relative;
    z-index: 3;
  }
  div.CodeMirror-dragcursors {
    visibility: visible;
  }
  .CodeMirror-focused div.CodeMirror-cursors {
    visibility: visible;
  }
  .CodeMirror-selected {
    background: #d9d9d9;
  }
  .CodeMirror-focused .CodeMirror-selected {
    background: #d7d4f0;
  }
  .CodeMirror-crosshair {
    cursor: crosshair;
  }
  .CodeMirror-line::selection,
  .CodeMirror-line > span::selection,
  .CodeMirror-line > span > span::selection {
    background: #d7d4f0;
  }
  .CodeMirror-line::-moz-selection,
  .CodeMirror-line > span::-moz-selection,
  .CodeMirror-line > span > span::-moz-selection {
    background: #d7d4f0;
  }
  .cm-searching {
    background-color: #ffa;
    background-color: rgba(255, 255, 0, 0.4);
  }
  /* Used to force a border model for a node */
  .cm-force-border {
    padding-right: 0.1px;
  }
  @media print {
    /* Hide the cursor when printing */
    .CodeMirror div.CodeMirror-cursors {
      visibility: hidden;
    }
  }
  /* See issue #2901 */
  .cm-tab-wrap-hack:after {
    content: '';
  }
  /* Help users use markselection to safely style text background */
  span.CodeMirror-selectedtext {
    background: none;
  }
`,nt=S`
  /* Based on Sublime Text's Monokai theme */

  .cm-s-monokai.CodeMirror {
    background: #272822;
    color: #f8f8f2;
  }
  .cm-s-monokai div.CodeMirror-selected {
    background: #49483e;
  }
  .cm-s-monokai .CodeMirror-line::selection,
  .cm-s-monokai .CodeMirror-line > span::selection,
  .cm-s-monokai .CodeMirror-line > span > span::selection {
    background: rgba(73, 72, 62, 0.99);
  }
  .cm-s-monokai .CodeMirror-line::-moz-selection,
  .cm-s-monokai .CodeMirror-line > span::-moz-selection,
  .cm-s-monokai .CodeMirror-line > span > span::-moz-selection {
    background: rgba(73, 72, 62, 0.99);
  }
  .cm-s-monokai .CodeMirror-gutters {
    background: #272822;
    border-right: 0px;
  }
  .cm-s-monokai .CodeMirror-guttermarker {
    color: white;
  }
  .cm-s-monokai .CodeMirror-guttermarker-subtle {
    color: #d0d0d0;
  }
  .cm-s-monokai .CodeMirror-linenumber {
    color: #d0d0d0;
  }
  .cm-s-monokai .CodeMirror-cursor {
    border-left: 1px solid #f8f8f0;
  }

  .cm-s-monokai span.cm-comment {
    color: #75715e;
  }
  .cm-s-monokai span.cm-atom {
    color: #ae81ff;
  }
  .cm-s-monokai span.cm-number {
    color: #ae81ff;
  }

  .cm-s-monokai span.cm-comment.cm-attribute {
    color: #97b757;
  }
  .cm-s-monokai span.cm-comment.cm-def {
    color: #bc9262;
  }
  .cm-s-monokai span.cm-comment.cm-tag {
    color: #bc6283;
  }
  .cm-s-monokai span.cm-comment.cm-type {
    color: #5998a6;
  }

  .cm-s-monokai span.cm-property,
  .cm-s-monokai span.cm-attribute {
    color: #a6e22e;
  }
  .cm-s-monokai span.cm-keyword {
    color: #f92672;
  }
  .cm-s-monokai span.cm-builtin {
    color: #66d9ef;
  }
  .cm-s-monokai span.cm-string {
    color: #e6db74;
  }

  .cm-s-monokai span.cm-variable {
    color: #f8f8f2;
  }
  .cm-s-monokai span.cm-variable-2 {
    color: #9effff;
  }
  .cm-s-monokai span.cm-variable-3,
  .cm-s-monokai span.cm-type {
    color: #66d9ef;
  }
  .cm-s-monokai span.cm-def {
    color: #fd971f;
  }
  .cm-s-monokai span.cm-bracket {
    color: #f8f8f2;
  }
  .cm-s-monokai span.cm-tag {
    color: #f92672;
  }
  .cm-s-monokai span.cm-header {
    color: #ae81ff;
  }
  .cm-s-monokai span.cm-link {
    color: #ae81ff;
  }
  .cm-s-monokai span.cm-error {
    background: #f92672;
    color: #f8f8f0;
  }

  .cm-s-monokai .CodeMirror-activeline-background {
    background: #373831;
  }
  .cm-s-monokai .CodeMirror-matchingbracket {
    text-decoration: underline;
    color: white !important;
  }
`;var ot=navigator.userAgent,st=navigator.platform,lt=/gecko\/\d/i.test(ot),at=/MSIE \d/.test(ot),ct=/Trident\/(?:[7-9]|\d{2,})\..*rv:(\d+)/.exec(ot),dt=/Edge\/(\d+)/.exec(ot),ut=at||ct||dt,ht=ut&&(at?document.documentMode||6:+(dt||ct)[1]),pt=!dt&&/WebKit\//.test(ot),mt=pt&&/Qt\/\d+\.\d+/.test(ot),ft=!dt&&/Chrome\//.test(ot),gt=/Opera\//.test(ot),vt=/Apple Computer/.test(navigator.vendor),bt=/Mac OS X 1\d\D([8-9]|\d\d)\D/.test(ot),yt=/PhantomJS/.test(ot),_t=vt&&(/Mobile\/\w+/.test(ot)||navigator.maxTouchPoints>2),xt=/Android/.test(ot),wt=_t||xt||/webOS|BlackBerry|Opera Mini|Opera Mobi|IEMobile/i.test(ot),kt=_t||/Mac/.test(st),St=/\bCrOS\b/.test(ot),Ct=/win/i.test(st),Tt=gt&&ot.match(/Version\/(\d*\.\d*)/);Tt&&(Tt=Number(Tt[1])),Tt&&Tt>=15&&(gt=!1,pt=!0);var Mt=kt&&(mt||gt&&(null==Tt||Tt<12.11)),Et=lt||ut&&ht>=9;function At(e){return new RegExp("(^|\\s)"+e+"(?:$|\\s)\\s*")}var Lt,Pt=function(e,t){let i=e.className,r=At(t).exec(i);if(r){let t=i.slice(r.index+r[0].length);e.className=i.slice(0,r.index)+(t?r[1]+t:"")}};function Rt(e){for(let t=e.childNodes.length;t>0;--t)e.removeChild(e.firstChild);return e}function Nt(e,t){return Rt(e).appendChild(t)}function It(e,t,i,r){let n=document.createElement(e);if(i&&(n.className=i),r&&(n.style.cssText=r),"string"==typeof t)n.appendChild(document.createTextNode(t));else if(t)for(let e=0;e<t.length;++e)n.appendChild(t[e]);return n}function Dt(e,t,i,r){let n=It(e,t,i,r);return n.setAttribute("role","presentation"),n}function Ot(e,t){if(3==t.nodeType&&(t=t.parentNode),e.contains)return e.contains(t);do{if(11==t.nodeType&&(t=t.host),t==e)return!0}while(t=t.parentNode)}function $t(){let e;try{e=document.activeElement}catch(t){e=document.body||null}for(;e&&e.shadowRoot&&e.shadowRoot.activeElement;)e=e.shadowRoot.activeElement;return e}function zt(e,t){let i=e.className;At(t).test(i)||(e.className+=(i?" ":"")+t)}function Ft(e,t){let i=e.split(" ");for(let e=0;e<i.length;e++)i[e]&&!At(i[e]).test(t)&&(t+=" "+i[e]);return t}Lt=document.createRange?function(e,t,i,r){let n=document.createRange();return n.setEnd(r||e,i),n.setStart(e,t),n}:function(e,t,i){let r=document.body.createTextRange();try{r.moveToElementText(e.parentNode)}catch(e){return r}return r.collapse(!0),r.moveEnd("character",i),r.moveStart("character",t),r};var Bt=function(e){e.select()};function Wt(e){let t=Array.prototype.slice.call(arguments,1);return function(){return e.apply(null,t)}}function Ht(e,t,i){t||(t={});for(let r in e)!e.hasOwnProperty(r)||!1===i&&t.hasOwnProperty(r)||(t[r]=e[r]);return t}function Ut(e,t,i,r,n){null==t&&-1==(t=e.search(/[^\s\u00a0]/))&&(t=e.length);for(let o=r||0,s=n||0;;){let r=e.indexOf("\t",o);if(r<0||r>=t)return s+(t-o);s+=r-o,s+=i-s%i,o=r+1}}_t?Bt=function(e){e.selectionStart=0,e.selectionEnd=e.value.length}:ut&&(Bt=function(e){try{e.select()}catch(e){}});var Vt=class{constructor(){this.id=null,this.f=null,this.time=0,this.handler=Wt(this.onTimeout,this)}onTimeout(e){e.id=0,e.time<=+new Date?e.f():setTimeout(e.handler,e.time-+new Date)}set(e,t){this.f=t;const i=+new Date+e;(!this.id||i<this.time)&&(clearTimeout(this.id),this.id=setTimeout(this.handler,e),this.time=i)}};function qt(e,t){for(let i=0;i<e.length;++i)if(e[i]==t)return i;return-1}var jt=50,Gt={toString:function(){return"CodeMirror.Pass"}},Kt={scroll:!1},Xt={origin:"*mouse"},Yt={origin:"+move"};function Zt(e,t,i){for(let r=0,n=0;;){let o=e.indexOf("\t",r);-1==o&&(o=e.length);let s=o-r;if(o==e.length||n+s>=t)return r+Math.min(s,t-n);if(n+=o-r,n+=i-n%i,r=o+1,n>=t)return r}}var Jt=[""];function Qt(e){for(;Jt.length<=e;)Jt.push(ei(Jt)+" ");return Jt[e]}function ei(e){return e[e.length-1]}function ti(e,t){let i=[];for(let r=0;r<e.length;r++)i[r]=t(e[r],r);return i}function ii(){}function ri(e,t){let i;return Object.create?i=Object.create(e):(ii.prototype=e,i=new ii),t&&Ht(t,i),i}var ni=/[\u00df\u0587\u0590-\u05f4\u0600-\u06ff\u3040-\u309f\u30a0-\u30ff\u3400-\u4db5\u4e00-\u9fcc\uac00-\ud7af]/;function oi(e){return/\w/.test(e)||e>""&&(e.toUpperCase()!=e.toLowerCase()||ni.test(e))}function si(e,t){return t?!!(t.source.indexOf("\\w")>-1&&oi(e))||t.test(e):oi(e)}function li(e){for(let t in e)if(e.hasOwnProperty(t)&&e[t])return!1;return!0}var ai=/[\u0300-\u036f\u0483-\u0489\u0591-\u05bd\u05bf\u05c1\u05c2\u05c4\u05c5\u05c7\u0610-\u061a\u064b-\u065e\u0670\u06d6-\u06dc\u06de-\u06e4\u06e7\u06e8\u06ea-\u06ed\u0711\u0730-\u074a\u07a6-\u07b0\u07eb-\u07f3\u0816-\u0819\u081b-\u0823\u0825-\u0827\u0829-\u082d\u0900-\u0902\u093c\u0941-\u0948\u094d\u0951-\u0955\u0962\u0963\u0981\u09bc\u09be\u09c1-\u09c4\u09cd\u09d7\u09e2\u09e3\u0a01\u0a02\u0a3c\u0a41\u0a42\u0a47\u0a48\u0a4b-\u0a4d\u0a51\u0a70\u0a71\u0a75\u0a81\u0a82\u0abc\u0ac1-\u0ac5\u0ac7\u0ac8\u0acd\u0ae2\u0ae3\u0b01\u0b3c\u0b3e\u0b3f\u0b41-\u0b44\u0b4d\u0b56\u0b57\u0b62\u0b63\u0b82\u0bbe\u0bc0\u0bcd\u0bd7\u0c3e-\u0c40\u0c46-\u0c48\u0c4a-\u0c4d\u0c55\u0c56\u0c62\u0c63\u0cbc\u0cbf\u0cc2\u0cc6\u0ccc\u0ccd\u0cd5\u0cd6\u0ce2\u0ce3\u0d3e\u0d41-\u0d44\u0d4d\u0d57\u0d62\u0d63\u0dca\u0dcf\u0dd2-\u0dd4\u0dd6\u0ddf\u0e31\u0e34-\u0e3a\u0e47-\u0e4e\u0eb1\u0eb4-\u0eb9\u0ebb\u0ebc\u0ec8-\u0ecd\u0f18\u0f19\u0f35\u0f37\u0f39\u0f71-\u0f7e\u0f80-\u0f84\u0f86\u0f87\u0f90-\u0f97\u0f99-\u0fbc\u0fc6\u102d-\u1030\u1032-\u1037\u1039\u103a\u103d\u103e\u1058\u1059\u105e-\u1060\u1071-\u1074\u1082\u1085\u1086\u108d\u109d\u135f\u1712-\u1714\u1732-\u1734\u1752\u1753\u1772\u1773\u17b7-\u17bd\u17c6\u17c9-\u17d3\u17dd\u180b-\u180d\u18a9\u1920-\u1922\u1927\u1928\u1932\u1939-\u193b\u1a17\u1a18\u1a56\u1a58-\u1a5e\u1a60\u1a62\u1a65-\u1a6c\u1a73-\u1a7c\u1a7f\u1b00-\u1b03\u1b34\u1b36-\u1b3a\u1b3c\u1b42\u1b6b-\u1b73\u1b80\u1b81\u1ba2-\u1ba5\u1ba8\u1ba9\u1c2c-\u1c33\u1c36\u1c37\u1cd0-\u1cd2\u1cd4-\u1ce0\u1ce2-\u1ce8\u1ced\u1dc0-\u1de6\u1dfd-\u1dff\u200c\u200d\u20d0-\u20f0\u2cef-\u2cf1\u2de0-\u2dff\u302a-\u302f\u3099\u309a\ua66f-\ua672\ua67c\ua67d\ua6f0\ua6f1\ua802\ua806\ua80b\ua825\ua826\ua8c4\ua8e0-\ua8f1\ua926-\ua92d\ua947-\ua951\ua980-\ua982\ua9b3\ua9b6-\ua9b9\ua9bc\uaa29-\uaa2e\uaa31\uaa32\uaa35\uaa36\uaa43\uaa4c\uaab0\uaab2-\uaab4\uaab7\uaab8\uaabe\uaabf\uaac1\uabe5\uabe8\uabed\udc00-\udfff\ufb1e\ufe00-\ufe0f\ufe20-\ufe26\uff9e\uff9f]/;function ci(e){return e.charCodeAt(0)>=768&&ai.test(e)}function di(e,t,i){for(;(i<0?t>0:t<e.length)&&ci(e.charAt(t));)t+=i;return t}function ui(e,t,i){let r=t>i?-1:1;for(;;){if(t==i)return t;let n=(t+i)/2,o=r<0?Math.ceil(n):Math.floor(n);if(o==t)return e(o)?t:i;e(o)?i=o:t=o+r}}var hi=null;function pi(e,t,i){let r;hi=null;for(let n=0;n<e.length;++n){let o=e[n];if(o.from<t&&o.to>t)return n;o.to==t&&(o.from!=o.to&&"before"==i?r=n:hi=n),o.from==t&&(o.from!=o.to&&"before"!=i?r=n:hi=n)}return null!=r?r:hi}var mi=function(){let e=/[\u0590-\u05f4\u0600-\u06ff\u0700-\u08ac]/,t=/[stwN]/,i=/[LRr]/,r=/[Lb1n]/,n=/[1n]/;function o(e,t,i){this.level=e,this.from=t,this.to=i}return function(s,l){let a="ltr"==l?"L":"R";if(0==s.length||"ltr"==l&&!e.test(s))return!1;let c=s.length,d=[];for(let e=0;e<c;++e)d.push((u=s.charCodeAt(e))<=247?"bbbbbbbbbtstwsbbbbbbbbbbbbbbssstwNN%%%NNNNNN,N,N1111111111NNNNNNNLLLLLLLLLLLLLLLLLLLLLLLLLLNNNNNNLLLLLLLLLLLLLLLLLLLLLLLLLLNNNNbbbbbbsbbbbbbbbbbbbbbbbbbbbbbbbbb,N%%%%NNNNLNNNNN%%11NLNNN1LNNNNNLLLLLLLLLLLLLLLLLLLLLLLNLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLN".charAt(u):1424<=u&&u<=1524?"R":1536<=u&&u<=1785?"nnnnnnNNr%%r,rNNmmmmmmmmmmmrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrmmmmmmmmmmmmmmmmmmmmmnnnnnnnnnn%nnrrrmrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrmmmmmmmnNmmmmmmrrmmNmmmmrr1111111111".charAt(u-1536):1774<=u&&u<=2220?"r":8192<=u&&u<=8203?"w":8204==u?"b":"L");var u;for(let e=0,t=a;e<c;++e){let i=d[e];"m"==i?d[e]=t:t=i}for(let e=0,t=a;e<c;++e){let r=d[e];"1"==r&&"r"==t?d[e]="n":i.test(r)&&(t=r,"r"==r&&(d[e]="R"))}for(let e=1,t=d[0];e<c-1;++e){let i=d[e];"+"==i&&"1"==t&&"1"==d[e+1]?d[e]="1":","!=i||t!=d[e+1]||"1"!=t&&"n"!=t||(d[e]=t),t=i}for(let e=0;e<c;++e){let t=d[e];if(","==t)d[e]="N";else if("%"==t){let t;for(t=e+1;t<c&&"%"==d[t];++t);let i=e&&"!"==d[e-1]||t<c&&"1"==d[t]?"1":"N";for(let r=e;r<t;++r)d[r]=i;e=t-1}}for(let e=0,t=a;e<c;++e){let r=d[e];"L"==t&&"1"==r?d[e]="L":i.test(r)&&(t=r)}for(let e=0;e<c;++e)if(t.test(d[e])){let i;for(i=e+1;i<c&&t.test(d[i]);++i);let r="L"==(e?d[e-1]:a),n=r==("L"==(i<c?d[i]:a))?r?"L":"R":a;for(let t=e;t<i;++t)d[t]=n;e=i-1}let h,p=[];for(let e=0;e<c;)if(r.test(d[e])){let t=e;for(++e;e<c&&r.test(d[e]);++e);p.push(new o(0,t,e))}else{let t=e,i=p.length,r="rtl"==l?1:0;for(++e;e<c&&"L"!=d[e];++e);for(let s=t;s<e;)if(n.test(d[s])){t<s&&(p.splice(i,0,new o(1,t,s)),i+=r);let l=s;for(++s;s<e&&n.test(d[s]);++s);p.splice(i,0,new o(2,l,s)),i+=r,t=s}else++s;t<e&&p.splice(i,0,new o(1,t,e))}return"ltr"==l&&(1==p[0].level&&(h=s.match(/^\s+/))&&(p[0].from=h[0].length,p.unshift(new o(0,0,h[0].length))),1==ei(p).level&&(h=s.match(/\s+$/))&&(ei(p).to-=h[0].length,p.push(new o(0,c-h[0].length,c)))),"rtl"==l?p.reverse():p}}();function fi(e,t){let i=e.order;return null==i&&(i=e.order=mi(e.text,t)),i}var gi=[],vi=function(e,t,i){if(e.addEventListener)e.addEventListener(t,i,!1);else if(e.attachEvent)e.attachEvent("on"+t,i);else{let r=e._handlers||(e._handlers={});r[t]=(r[t]||gi).concat(i)}};function bi(e,t){return e._handlers&&e._handlers[t]||gi}function yi(e,t,i){if(e.removeEventListener)e.removeEventListener(t,i,!1);else if(e.detachEvent)e.detachEvent("on"+t,i);else{let r=e._handlers,n=r&&r[t];if(n){let e=qt(n,i);e>-1&&(r[t]=n.slice(0,e).concat(n.slice(e+1)))}}}function _i(e,t){let i=bi(e,t);if(!i.length)return;let r=Array.prototype.slice.call(arguments,2);for(let e=0;e<i.length;++e)i[e].apply(null,r)}function xi(e,t,i){return"string"==typeof t&&(t={type:t,preventDefault:function(){this.defaultPrevented=!0}}),_i(e,i||t.type,e,t),Mi(t)||t.codemirrorIgnore}function wi(e){let t=e._handlers&&e._handlers.cursorActivity;if(!t)return;let i=e.curOp.cursorActivityHandlers||(e.curOp.cursorActivityHandlers=[]);for(let e=0;e<t.length;++e)-1==qt(i,t[e])&&i.push(t[e])}function ki(e,t){return bi(e,t).length>0}function Si(e){e.prototype.on=function(e,t){vi(this,e,t)},e.prototype.off=function(e,t){yi(this,e,t)}}function Ci(e){e.preventDefault?e.preventDefault():e.returnValue=!1}function Ti(e){e.stopPropagation?e.stopPropagation():e.cancelBubble=!0}function Mi(e){return null!=e.defaultPrevented?e.defaultPrevented:0==e.returnValue}function Ei(e){Ci(e),Ti(e)}function Ai(e){return e.target||e.srcElement}function Li(e){let t=e.which;return null==t&&(1&e.button?t=1:2&e.button?t=3:4&e.button&&(t=2)),kt&&e.ctrlKey&&1==t&&(t=3),t}var Pi,Ri,Ni=function(){if(ut&&ht<9)return!1;let e=It("div");return"draggable"in e||"dragDrop"in e}();function Ii(e){if(null==Pi){let t=It("span","​");Nt(e,It("span",[t,document.createTextNode("x")])),0!=e.firstChild.offsetHeight&&(Pi=t.offsetWidth<=1&&t.offsetHeight>2&&!(ut&&ht<8))}let t=Pi?It("span","​"):It("span"," ",null,"display: inline-block; width: 1px; margin-right: -1px");return t.setAttribute("cm-text",""),t}function Di(e){if(null!=Ri)return Ri;let t=Nt(e,document.createTextNode("AخA")),i=Lt(t,0,1).getBoundingClientRect(),r=Lt(t,1,2).getBoundingClientRect();return Rt(e),!(!i||i.left==i.right)&&(Ri=r.right-i.right<3)}var Oi=3!="\n\nb".split(/\n/).length?e=>{let t=0,i=[],r=e.length;for(;t<=r;){let r=e.indexOf("\n",t);-1==r&&(r=e.length);let n=e.slice(t,"\r"==e.charAt(r-1)?r-1:r),o=n.indexOf("\r");-1!=o?(i.push(n.slice(0,o)),t+=o+1):(i.push(n),t=r+1)}return i}:e=>e.split(/\r\n?|\n/),$i=window.getSelection?e=>{try{return e.selectionStart!=e.selectionEnd}catch(e){return!1}}:e=>{let t;try{t=e.ownerDocument.selection.createRange()}catch(e){}return!(!t||t.parentElement()!=e)&&0!=t.compareEndPoints("StartToEnd",t)},zi=(()=>{let e=It("div");return"oncopy"in e||(e.setAttribute("oncopy","return;"),"function"==typeof e.oncopy)})(),Fi=null;var Bi={},Wi={};function Hi(e,t){arguments.length>2&&(t.dependencies=Array.prototype.slice.call(arguments,2)),Bi[e]=t}function Ui(e){if("string"==typeof e&&Wi.hasOwnProperty(e))e=Wi[e];else if(e&&"string"==typeof e.name&&Wi.hasOwnProperty(e.name)){let t=Wi[e.name];"string"==typeof t&&(t={name:t}),(e=ri(t,e)).name=t.name}else{if("string"==typeof e&&/^[\w\-]+\/[\w\-]+\+xml$/.test(e))return Ui("application/xml");if("string"==typeof e&&/^[\w\-]+\/[\w\-]+\+json$/.test(e))return Ui("application/json")}return"string"==typeof e?{name:e}:e||{name:"null"}}function Vi(e,t){t=Ui(t);let i=Bi[t.name];if(!i)return Vi(e,"text/plain");let r=i(e,t);if(qi.hasOwnProperty(t.name)){let e=qi[t.name];for(let t in e)e.hasOwnProperty(t)&&(r.hasOwnProperty(t)&&(r["_"+t]=r[t]),r[t]=e[t])}if(r.name=t.name,t.helperType&&(r.helperType=t.helperType),t.modeProps)for(let e in t.modeProps)r[e]=t.modeProps[e];return r}var qi={};function ji(e,t){Ht(t,qi.hasOwnProperty(e)?qi[e]:qi[e]={})}function Gi(e,t){if(!0===t)return t;if(e.copyState)return e.copyState(t);let i={};for(let e in t){let r=t[e];r instanceof Array&&(r=r.concat([])),i[e]=r}return i}function Ki(e,t){let i;for(;e.innerMode&&(i=e.innerMode(t),i&&i.mode!=e);)t=i.state,e=i.mode;return i||{mode:e,state:t}}function Xi(e,t,i){return!e.startState||e.startState(t,i)}var Yi=class{constructor(e,t,i){this.pos=this.start=0,this.string=e,this.tabSize=t||8,this.lastColumnPos=this.lastColumnValue=0,this.lineStart=0,this.lineOracle=i}eol(){return this.pos>=this.string.length}sol(){return this.pos==this.lineStart}peek(){return this.string.charAt(this.pos)||void 0}next(){if(this.pos<this.string.length)return this.string.charAt(this.pos++)}eat(e){let t,i=this.string.charAt(this.pos);if(t="string"==typeof e?i==e:i&&(e.test?e.test(i):e(i)),t)return++this.pos,i}eatWhile(e){let t=this.pos;for(;this.eat(e););return this.pos>t}eatSpace(){let e=this.pos;for(;/[\s\u00a0]/.test(this.string.charAt(this.pos));)++this.pos;return this.pos>e}skipToEnd(){this.pos=this.string.length}skipTo(e){let t=this.string.indexOf(e,this.pos);if(t>-1)return this.pos=t,!0}backUp(e){this.pos-=e}column(){return this.lastColumnPos<this.start&&(this.lastColumnValue=Ut(this.string,this.start,this.tabSize,this.lastColumnPos,this.lastColumnValue),this.lastColumnPos=this.start),this.lastColumnValue-(this.lineStart?Ut(this.string,this.lineStart,this.tabSize):0)}indentation(){return Ut(this.string,null,this.tabSize)-(this.lineStart?Ut(this.string,this.lineStart,this.tabSize):0)}match(e,t,i){if("string"!=typeof e){let i=this.string.slice(this.pos).match(e);return i&&i.index>0?null:(i&&!1!==t&&(this.pos+=i[0].length),i)}{let r=e=>i?e.toLowerCase():e;if(r(this.string.substr(this.pos,e.length))==r(e))return!1!==t&&(this.pos+=e.length),!0}}current(){return this.string.slice(this.start,this.pos)}hideFirstChars(e,t){this.lineStart+=e;try{return t()}finally{this.lineStart-=e}}lookAhead(e){let t=this.lineOracle;return t&&t.lookAhead(e)}baseToken(){let e=this.lineOracle;return e&&e.baseToken(this.pos)}};function Zi(e,t){if((t-=e.first)<0||t>=e.size)throw new Error("There is no line "+(t+e.first)+" in the document.");let i=e;for(;!i.lines;)for(let e=0;;++e){let r=i.children[e],n=r.chunkSize();if(t<n){i=r;break}t-=n}return i.lines[t]}function Ji(e,t,i){let r=[],n=t.line;return e.iter(t.line,i.line+1,(e=>{let o=e.text;n==i.line&&(o=o.slice(0,i.ch)),n==t.line&&(o=o.slice(t.ch)),r.push(o),++n})),r}function Qi(e,t,i){let r=[];return e.iter(t,i,(e=>{r.push(e.text)})),r}function er(e,t){let i=t-e.height;if(i)for(let t=e;t;t=t.parent)t.height+=i}function tr(e){if(null==e.parent)return null;let t=e.parent,i=qt(t.lines,e);for(let e=t.parent;e;t=e,e=e.parent)for(let r=0;e.children[r]!=t;++r)i+=e.children[r].chunkSize();return i+t.first}function ir(e,t){let i=e.first;e:do{for(let r=0;r<e.children.length;++r){let n=e.children[r],o=n.height;if(t<o){e=n;continue e}t-=o,i+=n.chunkSize()}return i}while(!e.lines);let r=0;for(;r<e.lines.length;++r){let i=e.lines[r].height;if(t<i)break;t-=i}return i+r}function rr(e,t){return t>=e.first&&t<e.first+e.size}function nr(e,t){return String(e.lineNumberFormatter(t+e.firstLineNumber))}function or(e,t,i=null){if(!(this instanceof or))return new or(e,t,i);this.line=e,this.ch=t,this.sticky=i}function sr(e,t){return e.line-t.line||e.ch-t.ch}function lr(e,t){return e.sticky==t.sticky&&0==sr(e,t)}function ar(e){return or(e.line,e.ch)}function cr(e,t){return sr(e,t)<0?t:e}function dr(e,t){return sr(e,t)<0?e:t}function ur(e,t){return Math.max(e.first,Math.min(t,e.first+e.size-1))}function hr(e,t){if(t.line<e.first)return or(e.first,0);let i=e.first+e.size-1;return t.line>i?or(i,Zi(e,i).text.length):function(e,t){let i=e.ch;return null==i||i>t?or(e.line,t):i<0?or(e.line,0):e}(t,Zi(e,t.line).text.length)}function pr(e,t){let i=[];for(let r=0;r<t.length;r++)i[r]=hr(e,t[r]);return i}var mr=class{constructor(e,t){this.state=e,this.lookAhead=t}},fr=class{constructor(e,t,i,r){this.state=t,this.doc=e,this.line=i,this.maxLookAhead=r||0,this.baseTokens=null,this.baseTokenPos=1}lookAhead(e){let t=this.doc.getLine(this.line+e);return null!=t&&e>this.maxLookAhead&&(this.maxLookAhead=e),t}baseToken(e){if(!this.baseTokens)return null;for(;this.baseTokens[this.baseTokenPos]<=e;)this.baseTokenPos+=2;let t=this.baseTokens[this.baseTokenPos+1];return{type:t&&t.replace(/( |^)overlay .*/,""),size:this.baseTokens[this.baseTokenPos]-e}}nextLine(){this.line++,this.maxLookAhead>0&&this.maxLookAhead--}static fromSaved(e,t,i){return t instanceof mr?new fr(e,Gi(e.mode,t.state),i,t.lookAhead):new fr(e,Gi(e.mode,t),i)}save(e){let t=!1!==e?Gi(this.doc.mode,this.state):this.state;return this.maxLookAhead>0?new mr(t,this.maxLookAhead):t}};function gr(e,t,i,r){let n=[e.state.modeGen],o={};Cr(e,t.text,e.doc.mode,i,((e,t)=>n.push(e,t)),o,r);let s=i.state;for(let r=0;r<e.state.overlays.length;++r){i.baseTokens=n;let l=e.state.overlays[r],a=1,c=0;i.state=!0,Cr(e,t.text,l.mode,i,((e,t)=>{let i=a;for(;c<e;){let t=n[a];t>e&&n.splice(a,1,e,n[a+1],t),a+=2,c=Math.min(e,t)}if(t)if(l.opaque)n.splice(i,a-i,e,"overlay "+t),a=i+2;else for(;i<a;i+=2){let e=n[i+1];n[i+1]=(e?e+" ":"")+"overlay "+t}}),o),i.state=s,i.baseTokens=null,i.baseTokenPos=1}return{styles:n,classes:o.bgClass||o.textClass?o:null}}function vr(e,t,i){if(!t.styles||t.styles[0]!=e.state.modeGen){let r=br(e,tr(t)),n=t.text.length>e.options.maxHighlightLength&&Gi(e.doc.mode,r.state),o=gr(e,t,r);n&&(r.state=n),t.stateAfter=r.save(!n),t.styles=o.styles,o.classes?t.styleClasses=o.classes:t.styleClasses&&(t.styleClasses=null),i===e.doc.highlightFrontier&&(e.doc.modeFrontier=Math.max(e.doc.modeFrontier,++e.doc.highlightFrontier))}return t.styles}function br(e,t,i){let r=e.doc,n=e.display;if(!r.mode.startState)return new fr(r,!0,t);let o=function(e,t,i){let r,n,o=e.doc,s=i?-1:t-(e.doc.mode.innerMode?1e3:100);for(let l=t;l>s;--l){if(l<=o.first)return o.first;let t=Zi(o,l-1),s=t.stateAfter;if(s&&(!i||l+(s instanceof mr?s.lookAhead:0)<=o.modeFrontier))return l;let a=Ut(t.text,null,e.options.tabSize);(null==n||r>a)&&(n=l-1,r=a)}return n}(e,t,i),s=o>r.first&&Zi(r,o-1).stateAfter,l=s?fr.fromSaved(r,s,o):new fr(r,Xi(r.mode),o);return r.iter(o,t,(i=>{yr(e,i.text,l);let r=l.line;i.stateAfter=r==t-1||r%5==0||r>=n.viewFrom&&r<n.viewTo?l.save():null,l.nextLine()})),i&&(r.modeFrontier=l.line),l}function yr(e,t,i,r){let n=e.doc.mode,o=new Yi(t,e.options.tabSize,i);for(o.start=o.pos=r||0,""==t&&_r(n,i.state);!o.eol();)xr(n,o,i.state),o.start=o.pos}function _r(e,t){if(e.blankLine)return e.blankLine(t);if(!e.innerMode)return;let i=Ki(e,t);return i.mode.blankLine?i.mode.blankLine(i.state):void 0}function xr(e,t,i,r){for(let n=0;n<10;n++){r&&(r[0]=Ki(e,i).mode);let n=e.token(t,i);if(t.pos>t.start)return n}throw new Error("Mode "+e.name+" failed to advance stream.")}var wr=class{constructor(e,t,i){this.start=e.start,this.end=e.pos,this.string=e.current(),this.type=t||null,this.state=i}};function kr(e,t,i,r){let n,o,s=e.doc,l=s.mode,a=Zi(s,(t=hr(s,t)).line),c=br(e,t.line,i),d=new Yi(a.text,e.options.tabSize,c);for(r&&(o=[]);(r||d.pos<t.ch)&&!d.eol();)d.start=d.pos,n=xr(l,d,c.state),r&&o.push(new wr(d,n,Gi(s.mode,c.state)));return r?o:new wr(d,n,c.state)}function Sr(e,t){if(e)for(;;){let i=e.match(/(?:^|\s+)line-(background-)?(\S+)/);if(!i)break;e=e.slice(0,i.index)+e.slice(i.index+i[0].length);let r=i[1]?"bgClass":"textClass";null==t[r]?t[r]=i[2]:new RegExp("(?:^|\\s)"+i[2]+"(?:$|\\s)").test(t[r])||(t[r]+=" "+i[2])}return e}function Cr(e,t,i,r,n,o,s){let l=i.flattenSpans;null==l&&(l=e.options.flattenSpans);let a,c=0,d=null,u=new Yi(t,e.options.tabSize,r),h=e.options.addModeClass&&[null];for(""==t&&Sr(_r(i,r.state),o);!u.eol();){if(u.pos>e.options.maxHighlightLength?(l=!1,s&&yr(e,t,r,u.pos),u.pos=t.length,a=null):a=Sr(xr(i,u,r.state,h),o),h){let e=h[0].name;e&&(a="m-"+(a?e+" "+a:e))}if(!l||d!=a){for(;c<u.start;)c=Math.min(u.start,c+5e3),n(c,d);d=a}u.start=u.pos}for(;c<u.pos;){let e=Math.min(u.pos,c+5e3);n(e,d),c=e}}var Tr=!1,Mr=!1;function Er(e,t,i){this.marker=e,this.from=t,this.to=i}function Ar(e,t){if(e)for(let i=0;i<e.length;++i){let r=e[i];if(r.marker==t)return r}}function Lr(e,t){let i;for(let r=0;r<e.length;++r)e[r]!=t&&(i||(i=[])).push(e[r]);return i}function Pr(e,t){if(t.full)return null;let i=rr(e,t.from.line)&&Zi(e,t.from.line).markedSpans,r=rr(e,t.to.line)&&Zi(e,t.to.line).markedSpans;if(!i&&!r)return null;let n=t.from.ch,o=t.to.ch,s=0==sr(t.from,t.to),l=function(e,t,i){let r;if(e)for(let n=0;n<e.length;++n){let o=e[n],s=o.marker;if(null==o.from||(s.inclusiveLeft?o.from<=t:o.from<t)||o.from==t&&"bookmark"==s.type&&(!i||!o.marker.insertLeft)){let e=null==o.to||(s.inclusiveRight?o.to>=t:o.to>t);(r||(r=[])).push(new Er(s,o.from,e?null:o.to))}}return r}(i,n,s),a=function(e,t,i){let r;if(e)for(let n=0;n<e.length;++n){let o=e[n],s=o.marker;if(null==o.to||(s.inclusiveRight?o.to>=t:o.to>t)||o.from==t&&"bookmark"==s.type&&(!i||o.marker.insertLeft)){let e=null==o.from||(s.inclusiveLeft?o.from<=t:o.from<t);(r||(r=[])).push(new Er(s,e?null:o.from-t,null==o.to?null:o.to-t))}}return r}(r,o,s),c=1==t.text.length,d=ei(t.text).length+(c?n:0);if(l)for(let e=0;e<l.length;++e){let t=l[e];if(null==t.to){let e=Ar(a,t.marker);e?c&&(t.to=null==e.to?null:e.to+d):t.to=n}}if(a)for(let e=0;e<a.length;++e){let t=a[e];if(null!=t.to&&(t.to+=d),null==t.from){Ar(l,t.marker)||(t.from=d,c&&(l||(l=[])).push(t))}else t.from+=d,c&&(l||(l=[])).push(t)}l&&(l=Rr(l)),a&&a!=l&&(a=Rr(a));let u=[l];if(!c){let e,i=t.text.length-2;if(i>0&&l)for(let t=0;t<l.length;++t)null==l[t].to&&(e||(e=[])).push(new Er(l[t].marker,null,null));for(let t=0;t<i;++t)u.push(e);u.push(a)}return u}function Rr(e){for(let t=0;t<e.length;++t){let i=e[t];null!=i.from&&i.from==i.to&&!1!==i.marker.clearWhenEmpty&&e.splice(t--,1)}return e.length?e:null}function Nr(e){let t=e.markedSpans;if(t){for(let i=0;i<t.length;++i)t[i].marker.detachLine(e);e.markedSpans=null}}function Ir(e,t){if(t){for(let i=0;i<t.length;++i)t[i].marker.attachLine(e);e.markedSpans=t}}function Dr(e){return e.inclusiveLeft?-1:0}function Or(e){return e.inclusiveRight?1:0}function $r(e,t){let i=e.lines.length-t.lines.length;if(0!=i)return i;let r=e.find(),n=t.find(),o=sr(r.from,n.from)||Dr(e)-Dr(t);if(o)return-o;let s=sr(r.to,n.to)||Or(e)-Or(t);return s||t.id-e.id}function zr(e,t){let i,r=Mr&&e.markedSpans;if(r)for(let e,n=0;n<r.length;++n)e=r[n],e.marker.collapsed&&null==(t?e.from:e.to)&&(!i||$r(i,e.marker)<0)&&(i=e.marker);return i}function Fr(e){return zr(e,!0)}function Br(e){return zr(e,!1)}function Wr(e,t){let i,r=Mr&&e.markedSpans;if(r)for(let e=0;e<r.length;++e){let n=r[e];n.marker.collapsed&&(null==n.from||n.from<t)&&(null==n.to||n.to>t)&&(!i||$r(i,n.marker)<0)&&(i=n.marker)}return i}function Hr(e,t,i,r,n){let o=Zi(e,t),s=Mr&&o.markedSpans;if(s)for(let e=0;e<s.length;++e){let t=s[e];if(!t.marker.collapsed)continue;let o=t.marker.find(0),l=sr(o.from,i)||Dr(t.marker)-Dr(n),a=sr(o.to,r)||Or(t.marker)-Or(n);if(!(l>=0&&a<=0||l<=0&&a>=0)&&(l<=0&&(t.marker.inclusiveRight&&n.inclusiveLeft?sr(o.to,i)>=0:sr(o.to,i)>0)||l>=0&&(t.marker.inclusiveRight&&n.inclusiveLeft?sr(o.from,r)<=0:sr(o.from,r)<0)))return!0}}function Ur(e){let t;for(;t=Fr(e);)e=t.find(-1,!0).line;return e}function Vr(e,t){let i=Zi(e,t),r=Ur(i);return i==r?t:tr(r)}function qr(e,t){if(t>e.lastLine())return t;let i,r=Zi(e,t);if(!jr(e,r))return t;for(;i=Br(r);)r=i.find(1,!0).line;return tr(r)+1}function jr(e,t){let i=Mr&&t.markedSpans;if(i)for(let r,n=0;n<i.length;++n)if(r=i[n],r.marker.collapsed){if(null==r.from)return!0;if(!r.marker.widgetNode&&0==r.from&&r.marker.inclusiveLeft&&Gr(e,t,r))return!0}}function Gr(e,t,i){if(null==i.to){let t=i.marker.find(1,!0);return Gr(e,t.line,Ar(t.line.markedSpans,i.marker))}if(i.marker.inclusiveRight&&i.to==t.text.length)return!0;for(let r,n=0;n<t.markedSpans.length;++n)if(r=t.markedSpans[n],r.marker.collapsed&&!r.marker.widgetNode&&r.from==i.to&&(null==r.to||r.to!=i.from)&&(r.marker.inclusiveLeft||i.marker.inclusiveRight)&&Gr(e,t,r))return!0}function Kr(e){let t=0,i=(e=Ur(e)).parent;for(let r=0;r<i.lines.length;++r){let n=i.lines[r];if(n==e)break;t+=n.height}for(let e=i.parent;e;i=e,e=i.parent)for(let r=0;r<e.children.length;++r){let n=e.children[r];if(n==i)break;t+=n.height}return t}function Xr(e){if(0==e.height)return 0;let t,i=e.text.length,r=e;for(;t=Fr(r);){let e=t.find(0,!0);r=e.from.line,i+=e.from.ch-e.to.ch}for(r=e;t=Br(r);){let e=t.find(0,!0);i-=r.text.length-e.from.ch,r=e.to.line,i+=r.text.length-e.to.ch}return i}function Yr(e){let t=e.display,i=e.doc;t.maxLine=Zi(i,i.first),t.maxLineLength=Xr(t.maxLine),t.maxLineChanged=!0,i.iter((e=>{let i=Xr(e);i>t.maxLineLength&&(t.maxLineLength=i,t.maxLine=e)}))}var Zr=class{constructor(e,t,i){this.text=e,Ir(this,t),this.height=i?i(this):1}lineNo(){return tr(this)}};function Jr(e){e.parent=null,Nr(e)}Si(Zr);var Qr={},en={};function tn(e,t){if(!e||/^\s*$/.test(e))return null;let i=t.addModeClass?en:Qr;return i[e]||(i[e]=e.replace(/\S+/g,"cm-$&"))}function rn(e,t){let i=Dt("span",null,null,pt?"padding-right: .1px":null),r={pre:Dt("pre",[i],"CodeMirror-line"),content:i,col:0,pos:0,cm:e,trailingSpace:!1,splitSpaces:e.getOption("lineWrapping")};t.measure={};for(let i=0;i<=(t.rest?t.rest.length:0);i++){let n,o=i?t.rest[i-1]:t.line;r.pos=0,r.addToken=on,Di(e.display.measure)&&(n=fi(o,e.doc.direction))&&(r.addToken=sn(r.addToken,n)),r.map=[],an(o,r,vr(e,o,t!=e.display.externalMeasured&&tr(o))),o.styleClasses&&(o.styleClasses.bgClass&&(r.bgClass=Ft(o.styleClasses.bgClass,r.bgClass||"")),o.styleClasses.textClass&&(r.textClass=Ft(o.styleClasses.textClass,r.textClass||""))),0==r.map.length&&r.map.push(0,0,r.content.appendChild(Ii(e.display.measure))),0==i?(t.measure.map=r.map,t.measure.cache={}):((t.measure.maps||(t.measure.maps=[])).push(r.map),(t.measure.caches||(t.measure.caches=[])).push({}))}if(pt){let e=r.content.lastChild;(/\bcm-tab\b/.test(e.className)||e.querySelector&&e.querySelector(".cm-tab"))&&(r.content.className="cm-tab-wrap-hack")}return _i(e,"renderLine",e,t.line,r.pre),r.pre.className&&(r.textClass=Ft(r.pre.className,r.textClass||"")),r}function nn(e){let t=It("span","•","cm-invalidchar");return t.title="\\u"+e.charCodeAt(0).toString(16),t.setAttribute("aria-label",t.title),t}function on(e,t,i,r,n,o,s){if(!t)return;let l,a=e.splitSpaces?function(e,t){if(e.length>1&&!/  /.test(e))return e;let i=t,r="";for(let t=0;t<e.length;t++){let n=e.charAt(t);" "!=n||!i||t!=e.length-1&&32!=e.charCodeAt(t+1)||(n=" "),r+=n,i=" "==n}return r}(t,e.trailingSpace):t,c=e.cm.state.specialChars,d=!1;if(c.test(t)){l=document.createDocumentFragment();let i=0;for(;;){c.lastIndex=i;let r,n=c.exec(t),o=n?n.index-i:t.length-i;if(o){let t=document.createTextNode(a.slice(i,i+o));ut&&ht<9?l.appendChild(It("span",[t])):l.appendChild(t),e.map.push(e.pos,e.pos+o,t),e.col+=o,e.pos+=o}if(!n)break;if(i+=o+1,"\t"==n[0]){let t=e.cm.options.tabSize,i=t-e.col%t;r=l.appendChild(It("span",Qt(i),"cm-tab")),r.setAttribute("role","presentation"),r.setAttribute("cm-text","\t"),e.col+=i}else"\r"==n[0]||"\n"==n[0]?(r=l.appendChild(It("span","\r"==n[0]?"␍":"␤","cm-invalidchar")),r.setAttribute("cm-text",n[0]),e.col+=1):(r=e.cm.options.specialCharPlaceholder(n[0]),r.setAttribute("cm-text",n[0]),ut&&ht<9?l.appendChild(It("span",[r])):l.appendChild(r),e.col+=1);e.map.push(e.pos,e.pos+1,r),e.pos++}}else e.col+=t.length,l=document.createTextNode(a),e.map.push(e.pos,e.pos+t.length,l),ut&&ht<9&&(d=!0),e.pos+=t.length;if(e.trailingSpace=32==a.charCodeAt(t.length-1),i||r||n||d||o||s){let t=i||"";r&&(t+=r),n&&(t+=n);let a=It("span",[l],t,o);if(s)for(let e in s)s.hasOwnProperty(e)&&"style"!=e&&"class"!=e&&a.setAttribute(e,s[e]);return e.content.appendChild(a)}e.content.appendChild(l)}function sn(e,t){return(i,r,n,o,s,l,a)=>{n=n?n+" cm-force-border":"cm-force-border";let c=i.pos,d=c+r.length;for(;;){let u;for(let e=0;e<t.length&&(u=t[e],!(u.to>c&&u.from<=c));e++);if(u.to>=d)return e(i,r,n,o,s,l,a);e(i,r.slice(0,u.to-c),n,o,null,l,a),o=null,r=r.slice(u.to-c),c=u.to}}}function ln(e,t,i,r){let n=!r&&i.widgetNode;n&&e.map.push(e.pos,e.pos+t,n),!r&&e.cm.display.input.needsContentAttribute&&(n||(n=e.content.appendChild(document.createElement("span"))),n.setAttribute("cm-marker",i.id)),n&&(e.cm.display.input.setUneditable(n),e.content.appendChild(n)),e.pos+=t,e.trailingSpace=!1}function an(e,t,i){let r=e.markedSpans,n=e.text,o=0;if(!r){for(let e=1;e<i.length;e+=2)t.addToken(t,n.slice(o,o=i[e]),tn(i[e+1],t.cm.options));return}let s,l,a,c,d,u,h,p=n.length,m=0,f=1,g="",v=0;for(;;){if(v==m){a=c=d=l="",h=null,u=null,v=1/0;let e,i=[];for(let t=0;t<r.length;++t){let n=r[t],o=n.marker;if("bookmark"==o.type&&n.from==m&&o.widgetNode)i.push(o);else if(n.from<=m&&(null==n.to||n.to>m||o.collapsed&&n.to==m&&n.from==m)){if(null!=n.to&&n.to!=m&&v>n.to&&(v=n.to,c=""),o.className&&(a+=" "+o.className),o.css&&(l=(l?l+";":"")+o.css),o.startStyle&&n.from==m&&(d+=" "+o.startStyle),o.endStyle&&n.to==v&&(e||(e=[])).push(o.endStyle,n.to),o.title&&((h||(h={})).title=o.title),o.attributes)for(let e in o.attributes)(h||(h={}))[e]=o.attributes[e];o.collapsed&&(!u||$r(u.marker,o)<0)&&(u=n)}else n.from>m&&v>n.from&&(v=n.from)}if(e)for(let t=0;t<e.length;t+=2)e[t+1]==v&&(c+=" "+e[t]);if(!u||u.from==m)for(let e=0;e<i.length;++e)ln(t,0,i[e]);if(u&&(u.from||0)==m){if(ln(t,(null==u.to?p+1:u.to)-m,u.marker,null==u.from),null==u.to)return;u.to==m&&(u=!1)}}if(m>=p)break;let e=Math.min(p,v);for(;;){if(g){let i=m+g.length;if(!u){let r=i>e?g.slice(0,e-m):g;t.addToken(t,r,s?s+a:a,d,m+r.length==v?c:"",l,h)}if(i>=e){g=g.slice(e-m),m=e;break}m=i,d=""}g=n.slice(o,o=i[f++]),s=tn(i[f++],t.cm.options)}}}function cn(e,t,i){this.line=t,this.rest=function(e){let t,i;for(;t=Br(e);)e=t.find(1,!0).line,(i||(i=[])).push(e);return i}(t),this.size=this.rest?tr(ei(this.rest))-i+1:1,this.node=this.text=null,this.hidden=jr(e,t)}function dn(e,t,i){let r,n=[];for(let o=t;o<i;o=r){let t=new cn(e.doc,Zi(e.doc,o),o);r=o+t.size,n.push(t)}return n}var un=null;var hn=null;function pn(e,t){let i=bi(e,t);if(!i.length)return;let r,n=Array.prototype.slice.call(arguments,2);un?r=un.delayedCallbacks:hn?r=hn:(r=hn=[],setTimeout(mn,0));for(let e=0;e<i.length;++e)r.push((()=>i[e].apply(null,n)))}function mn(){let e=hn;hn=null;for(let t=0;t<e.length;++t)e[t]()}function fn(e,t,i,r){for(let n=0;n<t.changes.length;n++){let o=t.changes[n];"text"==o?bn(e,t):"gutter"==o?_n(e,t,i,r):"class"==o?yn(e,t):"widget"==o&&xn(e,t,r)}t.changes=null}function gn(e){return e.node==e.text&&(e.node=It("div",null,null,"position: relative"),e.text.parentNode&&e.text.parentNode.replaceChild(e.node,e.text),e.node.appendChild(e.text),ut&&ht<8&&(e.node.style.zIndex=2)),e.node}function vn(e,t){let i=e.display.externalMeasured;return i&&i.line==t.line?(e.display.externalMeasured=null,t.measure=i.measure,i.built):rn(e,t)}function bn(e,t){let i=t.text.className,r=vn(e,t);t.text==t.node&&(t.node=r.pre),t.text.parentNode.replaceChild(r.pre,t.text),t.text=r.pre,r.bgClass!=t.bgClass||r.textClass!=t.textClass?(t.bgClass=r.bgClass,t.textClass=r.textClass,yn(e,t)):i&&(t.text.className=i)}function yn(e,t){!function(e,t){let i=t.bgClass?t.bgClass+" "+(t.line.bgClass||""):t.line.bgClass;if(i&&(i+=" CodeMirror-linebackground"),t.background)i?t.background.className=i:(t.background.parentNode.removeChild(t.background),t.background=null);else if(i){let r=gn(t);t.background=r.insertBefore(It("div",null,i),r.firstChild),e.display.input.setUneditable(t.background)}}(e,t),t.line.wrapClass?gn(t).className=t.line.wrapClass:t.node!=t.text&&(t.node.className="");let i=t.textClass?t.textClass+" "+(t.line.textClass||""):t.line.textClass;t.text.className=i||""}function _n(e,t,i,r){if(t.gutter&&(t.node.removeChild(t.gutter),t.gutter=null),t.gutterBackground&&(t.node.removeChild(t.gutterBackground),t.gutterBackground=null),t.line.gutterClass){let i=gn(t);t.gutterBackground=It("div",null,"CodeMirror-gutter-background "+t.line.gutterClass,`left: ${e.options.fixedGutter?r.fixedPos:-r.gutterTotalWidth}px; width: ${r.gutterTotalWidth}px`),e.display.input.setUneditable(t.gutterBackground),i.insertBefore(t.gutterBackground,t.text)}let n=t.line.gutterMarkers;if(e.options.lineNumbers||n){let o=gn(t),s=t.gutter=It("div",null,"CodeMirror-gutter-wrapper",`left: ${e.options.fixedGutter?r.fixedPos:-r.gutterTotalWidth}px`);if(s.setAttribute("aria-hidden","true"),e.display.input.setUneditable(s),o.insertBefore(s,t.text),t.line.gutterClass&&(s.className+=" "+t.line.gutterClass),!e.options.lineNumbers||n&&n["CodeMirror-linenumbers"]||(t.lineNumber=s.appendChild(It("div",nr(e.options,i),"CodeMirror-linenumber CodeMirror-gutter-elt",`left: ${r.gutterLeft["CodeMirror-linenumbers"]}px; width: ${e.display.lineNumInnerWidth}px`))),n)for(let t=0;t<e.display.gutterSpecs.length;++t){let i=e.display.gutterSpecs[t].className,o=n.hasOwnProperty(i)&&n[i];o&&s.appendChild(It("div",[o],"CodeMirror-gutter-elt",`left: ${r.gutterLeft[i]}px; width: ${r.gutterWidth[i]}px`))}}}function xn(e,t,i){t.alignable&&(t.alignable=null);let r=At("CodeMirror-linewidget");for(let e,i=t.node.firstChild;i;i=e)e=i.nextSibling,r.test(i.className)&&t.node.removeChild(i);kn(e,t,i)}function wn(e,t,i,r){let n=vn(e,t);return t.text=t.node=n.pre,n.bgClass&&(t.bgClass=n.bgClass),n.textClass&&(t.textClass=n.textClass),yn(e,t),_n(e,t,i,r),kn(e,t,r),t.node}function kn(e,t,i){if(Sn(e,t.line,t,i,!0),t.rest)for(let r=0;r<t.rest.length;r++)Sn(e,t.rest[r],t,i,!1)}function Sn(e,t,i,r,n){if(!t.widgets)return;let o=gn(i);for(let s=0,l=t.widgets;s<l.length;++s){let t=l[s],a=It("div",[t.node],"CodeMirror-linewidget"+(t.className?" "+t.className:""));t.handleMouseEvents||a.setAttribute("cm-ignore-events","true"),Cn(t,a,i,r),e.display.input.setUneditable(a),n&&t.above?o.insertBefore(a,i.gutter||i.text):o.appendChild(a),pn(t,"redraw")}}function Cn(e,t,i,r){if(e.noHScroll){(i.alignable||(i.alignable=[])).push(t);let n=r.wrapperWidth;t.style.left=r.fixedPos+"px",e.coverGutter||(n-=r.gutterTotalWidth,t.style.paddingLeft=r.gutterTotalWidth+"px"),t.style.width=n+"px"}e.coverGutter&&(t.style.zIndex=5,t.style.position="relative",e.noHScroll||(t.style.marginLeft=-r.gutterTotalWidth+"px"))}function Tn(e){if(null!=e.height)return e.height;let t=e.doc.cm;if(!t)return 0;if(!Ot(document.body,e.node)){let i="position: relative;";e.coverGutter&&(i+="margin-left: -"+t.display.gutters.offsetWidth+"px;"),e.noHScroll&&(i+="width: "+t.display.wrapper.clientWidth+"px;"),Nt(t.display.measure,It("div",[e.node],null,i))}return e.height=e.node.parentNode.offsetHeight}function Mn(e,t){for(let i=Ai(t);i!=e.wrapper;i=i.parentNode)if(!i||1==i.nodeType&&"true"==i.getAttribute("cm-ignore-events")||i.parentNode==e.sizer&&i!=e.mover)return!0}function En(e){return e.lineSpace.offsetTop}function An(e){return e.mover.offsetHeight-e.lineSpace.offsetHeight}function Ln(e){if(e.cachedPaddingH)return e.cachedPaddingH;let t=Nt(e.measure,It("pre","x","CodeMirror-line-like")),i=window.getComputedStyle?window.getComputedStyle(t):t.currentStyle,r={left:parseInt(i.paddingLeft),right:parseInt(i.paddingRight)};return isNaN(r.left)||isNaN(r.right)||(e.cachedPaddingH=r),r}function Pn(e){return jt-e.display.nativeBarWidth}function Rn(e){return e.display.scroller.clientWidth-Pn(e)-e.display.barWidth}function Nn(e){return e.display.scroller.clientHeight-Pn(e)-e.display.barHeight}function In(e,t,i){if(e.line==t)return{map:e.measure.map,cache:e.measure.cache};for(let i=0;i<e.rest.length;i++)if(e.rest[i]==t)return{map:e.measure.maps[i],cache:e.measure.caches[i]};for(let t=0;t<e.rest.length;t++)if(tr(e.rest[t])>i)return{map:e.measure.maps[t],cache:e.measure.caches[t],before:!0}}function Dn(e,t,i,r){return zn(e,$n(e,t),i,r)}function On(e,t){if(t>=e.display.viewFrom&&t<e.display.viewTo)return e.display.view[go(e,t)];let i=e.display.externalMeasured;return i&&t>=i.lineN&&t<i.lineN+i.size?i:void 0}function $n(e,t){let i=tr(t),r=On(e,i);r&&!r.text?r=null:r&&r.changes&&(fn(e,r,i,uo(e)),e.curOp.forceUpdate=!0),r||(r=function(e,t){let i=tr(t=Ur(t)),r=e.display.externalMeasured=new cn(e.doc,t,i);r.lineN=i;let n=r.built=rn(e,r);return r.text=n.pre,Nt(e.display.lineMeasure,n.pre),r}(e,t));let n=In(r,t,i);return{line:t,view:r,rect:null,map:n.map,cache:n.cache,before:n.before,hasHeights:!1}}function zn(e,t,i,r,n){t.before&&(i=-1);let o,s=i+(r||"");return t.cache.hasOwnProperty(s)?o=t.cache[s]:(t.rect||(t.rect=t.view.text.getBoundingClientRect()),t.hasHeights||(!function(e,t,i){let r=e.options.lineWrapping,n=r&&Rn(e);if(!t.measure.heights||r&&t.measure.width!=n){let e=t.measure.heights=[];if(r){t.measure.width=n;let r=t.text.firstChild.getClientRects();for(let t=0;t<r.length-1;t++){let n=r[t],o=r[t+1];Math.abs(n.bottom-o.bottom)>2&&e.push((n.bottom+o.top)/2-i.top)}}e.push(i.bottom-i.top)}}(e,t.view,t.rect),t.hasHeights=!0),o=function(e,t,i,r){let n,o=Wn(t.map,i,r),s=o.node,l=o.start,a=o.end,c=o.collapse;if(3==s.nodeType){for(let e=0;e<4;e++){for(;l&&ci(t.line.text.charAt(o.coverStart+l));)--l;for(;o.coverStart+a<o.coverEnd&&ci(t.line.text.charAt(o.coverStart+a));)++a;if(n=ut&&ht<9&&0==l&&a==o.coverEnd-o.coverStart?s.parentNode.getBoundingClientRect():Hn(Lt(s,l,a).getClientRects(),r),n.left||n.right||0==l)break;a=l,l-=1,c="right"}ut&&ht<11&&(n=function(e,t){if(!window.screen||null==screen.logicalXDPI||screen.logicalXDPI==screen.deviceXDPI||!function(e){if(null!=Fi)return Fi;let t=Nt(e,It("span","x")),i=t.getBoundingClientRect(),r=Lt(t,0,1).getBoundingClientRect();return Fi=Math.abs(i.left-r.left)>1}(e))return t;let i=screen.logicalXDPI/screen.deviceXDPI,r=screen.logicalYDPI/screen.deviceYDPI;return{left:t.left*i,right:t.right*i,top:t.top*r,bottom:t.bottom*r}}(e.display.measure,n))}else{let t;l>0&&(c=r="right"),n=e.options.lineWrapping&&(t=s.getClientRects()).length>1?t["right"==r?t.length-1:0]:s.getBoundingClientRect()}if(ut&&ht<9&&!l&&(!n||!n.left&&!n.right)){let t=s.parentNode.getClientRects()[0];n=t?{left:t.left,right:t.left+co(e.display),top:t.top,bottom:t.bottom}:Bn}let d=n.top-t.rect.top,u=n.bottom-t.rect.top,h=(d+u)/2,p=t.view.measure.heights,m=0;for(;m<p.length-1&&!(h<p[m]);m++);let f=m?p[m-1]:0,g=p[m],v={left:("right"==c?n.right:n.left)-t.rect.left,right:("left"==c?n.left:n.right)-t.rect.left,top:f,bottom:g};n.left||n.right||(v.bogus=!0);e.options.singleCursorHeightPerLine||(v.rtop=d,v.rbottom=u);return v}(e,t,i,r),o.bogus||(t.cache[s]=o)),{left:o.left,right:o.right,top:n?o.rtop:o.top,bottom:n?o.rbottom:o.bottom}}var Fn,Bn={left:0,right:0,top:0,bottom:0};function Wn(e,t,i){let r,n,o,s,l,a;for(let c=0;c<e.length;c+=3)if(l=e[c],a=e[c+1],t<l?(n=0,o=1,s="left"):t<a?(n=t-l,o=n+1):(c==e.length-3||t==a&&e[c+3]>t)&&(o=a-l,n=o-1,t>=a&&(s="right")),null!=n){if(r=e[c+2],l==a&&i==(r.insertLeft?"left":"right")&&(s=i),"left"==i&&0==n)for(;c&&e[c-2]==e[c-3]&&e[c-1].insertLeft;)r=e[2+(c-=3)],s="left";if("right"==i&&n==a-l)for(;c<e.length-3&&e[c+3]==e[c+4]&&!e[c+5].insertLeft;)r=e[(c+=3)+2],s="right";break}return{node:r,start:n,end:o,collapse:s,coverStart:l,coverEnd:a}}function Hn(e,t){let i=Bn;if("left"==t)for(let t=0;t<e.length&&(i=e[t]).left==i.right;t++);else for(let t=e.length-1;t>=0&&(i=e[t]).left==i.right;t--);return i}function Un(e){if(e.measure&&(e.measure.cache={},e.measure.heights=null,e.rest))for(let t=0;t<e.rest.length;t++)e.measure.caches[t]={}}function Vn(e){e.display.externalMeasure=null,Rt(e.display.lineMeasure);for(let t=0;t<e.display.view.length;t++)Un(e.display.view[t])}function qn(e){Vn(e),e.display.cachedCharWidth=e.display.cachedTextHeight=e.display.cachedPaddingH=null,e.options.lineWrapping||(e.display.maxLineChanged=!0),e.display.lineNumChars=null}function jn(){return ft&&xt?-(document.body.getBoundingClientRect().left-parseInt(getComputedStyle(document.body).marginLeft)):window.pageXOffset||(document.documentElement||document.body).scrollLeft}function Gn(){return ft&&xt?-(document.body.getBoundingClientRect().top-parseInt(getComputedStyle(document.body).marginTop)):window.pageYOffset||(document.documentElement||document.body).scrollTop}function Kn(e){let t=0;if(e.widgets)for(let i=0;i<e.widgets.length;++i)e.widgets[i].above&&(t+=Tn(e.widgets[i]));return t}function Xn(e,t,i,r,n){if(!n){let e=Kn(t);i.top+=e,i.bottom+=e}if("line"==r)return i;r||(r="local");let o=Kr(t);if("local"==r?o+=En(e.display):o-=e.display.viewOffset,"page"==r||"window"==r){let t=e.display.lineSpace.getBoundingClientRect();o+=t.top+("window"==r?0:Gn());let n=t.left+("window"==r?0:jn());i.left+=n,i.right+=n}return i.top+=o,i.bottom+=o,i}function Yn(e,t,i){if("div"==i)return t;let r=t.left,n=t.top;if("page"==i)r-=jn(),n-=Gn();else if("local"==i||!i){let t=e.display.sizer.getBoundingClientRect();r+=t.left,n+=t.top}let o=e.display.lineSpace.getBoundingClientRect();return{left:r-o.left,top:n-o.top}}function Zn(e,t,i,r,n){return r||(r=Zi(e.doc,t.line)),Xn(e,r,Dn(e,r,t.ch,n),i)}function Jn(e,t,i,r,n,o){function s(t,s){let l=zn(e,n,t,s?"right":"left",o);return s?l.left=l.right:l.right=l.left,Xn(e,r,l,i)}r=r||Zi(e.doc,t.line),n||(n=$n(e,r));let l=fi(r,e.doc.direction),a=t.ch,c=t.sticky;if(a>=r.text.length?(a=r.text.length,c="before"):a<=0&&(a=0,c="after"),!l)return s("before"==c?a-1:a,"before"==c);function d(e,t,i){return s(i?e-1:e,1==l[t].level!=i)}let u=pi(l,a,c),h=hi,p=d(a,u,"before"==c);return null!=h&&(p.other=d(a,h,"before"!=c)),p}function Qn(e,t){let i=0;t=hr(e.doc,t),e.options.lineWrapping||(i=co(e.display)*t.ch);let r=Zi(e.doc,t.line),n=Kr(r)+En(e.display);return{left:i,right:i,top:n,bottom:n+r.height}}function eo(e,t,i,r,n){let o=or(e,t,i);return o.xRel=n,r&&(o.outside=r),o}function to(e,t,i){let r=e.doc;if((i+=e.display.viewOffset)<0)return eo(r.first,0,null,-1,-1);let n=ir(r,i),o=r.first+r.size-1;if(n>o)return eo(r.first+r.size-1,Zi(r,o).text.length,null,1,1);t<0&&(t=0);let s=Zi(r,n);for(;;){let o=oo(e,s,n,t,i),l=Wr(s,o.ch+(o.xRel>0||o.outside>0?1:0));if(!l)return o;let a=l.find(1);if(a.line==n)return a;s=Zi(r,n=a.line)}}function io(e,t,i,r){r-=Kn(t);let n=t.text.length,o=ui((t=>zn(e,i,t-1).bottom<=r),n,0);return n=ui((t=>zn(e,i,t).top>r),o,n),{begin:o,end:n}}function ro(e,t,i,r){return i||(i=$n(e,t)),io(e,t,i,Xn(e,t,zn(e,i,r),"line").top)}function no(e,t,i,r){return!(e.bottom<=i)&&(e.top>i||(r?e.left:e.right)>t)}function oo(e,t,i,r,n){n-=Kr(t);let o=$n(e,t),s=Kn(t),l=0,a=t.text.length,c=!0,d=fi(t,e.doc.direction);if(d){let s=(e.options.lineWrapping?lo:so)(e,t,i,o,d,r,n);c=1!=s.level,l=c?s.from:s.to-1,a=c?s.to:s.from-1}let u,h,p=null,m=null,f=ui((t=>{let i=zn(e,o,t);return i.top+=s,i.bottom+=s,!!no(i,r,n,!1)&&(i.top<=n&&i.left<=r&&(p=t,m=i),!0)}),l,a),g=!1;if(m){let e=r-m.left<m.right-r,t=e==c;f=p+(t?0:1),h=t?"after":"before",u=e?m.left:m.right}else{c||f!=a&&f!=l||f++,h=0==f?"after":f==t.text.length?"before":zn(e,o,f-(c?1:0)).bottom+s<=n==c?"after":"before";let r=Jn(e,or(i,f,h),"line",t,o);u=r.left,g=n<r.top?-1:n>=r.bottom?1:0}return f=di(t.text,f,1),eo(i,f,h,g,r-u)}function so(e,t,i,r,n,o,s){let l=ui((l=>{let a=n[l],c=1!=a.level;return no(Jn(e,or(i,c?a.to:a.from,c?"before":"after"),"line",t,r),o,s,!0)}),0,n.length-1),a=n[l];if(l>0){let c=1!=a.level,d=Jn(e,or(i,c?a.from:a.to,c?"after":"before"),"line",t,r);no(d,o,s,!0)&&d.top>s&&(a=n[l-1])}return a}function lo(e,t,i,r,n,o,s){let{begin:l,end:a}=io(e,t,r,s);/\s/.test(t.text.charAt(a-1))&&a--;let c=null,d=null;for(let t=0;t<n.length;t++){let i=n[t];if(i.from>=a||i.to<=l)continue;let s=zn(e,r,1!=i.level?Math.min(a,i.to)-1:Math.max(l,i.from)).right,u=s<o?o-s+1e9:s-o;(!c||d>u)&&(c=i,d=u)}return c||(c=n[n.length-1]),c.from<l&&(c={from:l,to:c.to,level:c.level}),c.to>a&&(c={from:c.from,to:a,level:c.level}),c}function ao(e){if(null!=e.cachedTextHeight)return e.cachedTextHeight;if(null==Fn){Fn=It("pre",null,"CodeMirror-line-like");for(let e=0;e<49;++e)Fn.appendChild(document.createTextNode("x")),Fn.appendChild(It("br"));Fn.appendChild(document.createTextNode("x"))}Nt(e.measure,Fn);let t=Fn.offsetHeight/50;return t>3&&(e.cachedTextHeight=t),Rt(e.measure),t||1}function co(e){if(null!=e.cachedCharWidth)return e.cachedCharWidth;let t=It("span","xxxxxxxxxx"),i=It("pre",[t],"CodeMirror-line-like");Nt(e.measure,i);let r=t.getBoundingClientRect(),n=(r.right-r.left)/10;return n>2&&(e.cachedCharWidth=n),n||10}function uo(e){let t=e.display,i={},r={},n=t.gutters.clientLeft;for(let o=t.gutters.firstChild,s=0;o;o=o.nextSibling,++s){let t=e.display.gutterSpecs[s].className;i[t]=o.offsetLeft+o.clientLeft+n,r[t]=o.clientWidth}return{fixedPos:ho(t),gutterTotalWidth:t.gutters.offsetWidth,gutterLeft:i,gutterWidth:r,wrapperWidth:t.wrapper.clientWidth}}function ho(e){return e.scroller.getBoundingClientRect().left-e.sizer.getBoundingClientRect().left}function po(e){let t=ao(e.display),i=e.options.lineWrapping,r=i&&Math.max(5,e.display.scroller.clientWidth/co(e.display)-3);return n=>{if(jr(e.doc,n))return 0;let o=0;if(n.widgets)for(let e=0;e<n.widgets.length;e++)n.widgets[e].height&&(o+=n.widgets[e].height);return i?o+(Math.ceil(n.text.length/r)||1)*t:o+t}}function mo(e){let t=e.doc,i=po(e);t.iter((e=>{let t=i(e);t!=e.height&&er(e,t)}))}function fo(e,t,i,r){let n=e.display;if(!i&&"true"==Ai(t).getAttribute("cm-not-content"))return null;let o,s,l=n.lineSpace.getBoundingClientRect();try{o=t.clientX-l.left,s=t.clientY-l.top}catch(e){return null}let a,c=to(e,o,s);if(r&&c.xRel>0&&(a=Zi(e.doc,c.line).text).length==c.ch){let t=Ut(a,a.length,e.options.tabSize)-a.length;c=or(c.line,Math.max(0,Math.round((o-Ln(e.display).left)/co(e.display))-t))}return c}function go(e,t){if(t>=e.display.viewTo)return null;if((t-=e.display.viewFrom)<0)return null;let i=e.display.view;for(let e=0;e<i.length;e++)if((t-=i[e].size)<0)return e}function vo(e,t,i,r){null==t&&(t=e.doc.first),null==i&&(i=e.doc.first+e.doc.size),r||(r=0);let n=e.display;if(r&&i<n.viewTo&&(null==n.updateLineNumbers||n.updateLineNumbers>t)&&(n.updateLineNumbers=t),e.curOp.viewChanged=!0,t>=n.viewTo)Mr&&Vr(e.doc,t)<n.viewTo&&yo(e);else if(i<=n.viewFrom)Mr&&qr(e.doc,i+r)>n.viewFrom?yo(e):(n.viewFrom+=r,n.viewTo+=r);else if(t<=n.viewFrom&&i>=n.viewTo)yo(e);else if(t<=n.viewFrom){let t=_o(e,i,i+r,1);t?(n.view=n.view.slice(t.index),n.viewFrom=t.lineN,n.viewTo+=r):yo(e)}else if(i>=n.viewTo){let i=_o(e,t,t,-1);i?(n.view=n.view.slice(0,i.index),n.viewTo=i.lineN):yo(e)}else{let o=_o(e,t,t,-1),s=_o(e,i,i+r,1);o&&s?(n.view=n.view.slice(0,o.index).concat(dn(e,o.lineN,s.lineN)).concat(n.view.slice(s.index)),n.viewTo+=r):yo(e)}let o=n.externalMeasured;o&&(i<o.lineN?o.lineN+=r:t<o.lineN+o.size&&(n.externalMeasured=null))}function bo(e,t,i){e.curOp.viewChanged=!0;let r=e.display,n=e.display.externalMeasured;if(n&&t>=n.lineN&&t<n.lineN+n.size&&(r.externalMeasured=null),t<r.viewFrom||t>=r.viewTo)return;let o=r.view[go(e,t)];if(null==o.node)return;let s=o.changes||(o.changes=[]);-1==qt(s,i)&&s.push(i)}function yo(e){e.display.viewFrom=e.display.viewTo=e.doc.first,e.display.view=[],e.display.viewOffset=0}function _o(e,t,i,r){let n,o=go(e,t),s=e.display.view;if(!Mr||i==e.doc.first+e.doc.size)return{index:o,lineN:i};let l=e.display.viewFrom;for(let e=0;e<o;e++)l+=s[e].size;if(l!=t){if(r>0){if(o==s.length-1)return null;n=l+s[o].size-t,o++}else n=l-t;t+=n,i+=n}for(;Vr(e.doc,i)!=i;){if(o==(r<0?0:s.length-1))return null;i+=r*s[o-(r<0?1:0)].size,o+=r}return{index:o,lineN:i}}function xo(e){let t=e.display.view,i=0;for(let e=0;e<t.length;e++){let r=t[e];r.hidden||r.node&&!r.changes||++i}return i}function wo(e){e.display.input.showSelection(e.display.input.prepareSelection())}function ko(e,t=!0){let i=e.doc,r={},n=r.cursors=document.createDocumentFragment(),o=r.selection=document.createDocumentFragment();for(let r=0;r<i.sel.ranges.length;r++){if(!t&&r==i.sel.primIndex)continue;let s=i.sel.ranges[r];if(s.from().line>=e.display.viewTo||s.to().line<e.display.viewFrom)continue;let l=s.empty();(l||e.options.showCursorWhenSelecting)&&So(e,s.head,n),l||To(e,s,o)}return r}function So(e,t,i){let r=Jn(e,t,"div",null,null,!e.options.singleCursorHeightPerLine),n=i.appendChild(It("div"," ","CodeMirror-cursor"));if(n.style.left=r.left+"px",n.style.top=r.top+"px",n.style.height=Math.max(0,r.bottom-r.top)*e.options.cursorHeight+"px",r.other){let e=i.appendChild(It("div"," ","CodeMirror-cursor CodeMirror-secondarycursor"));e.style.display="",e.style.left=r.other.left+"px",e.style.top=r.other.top+"px",e.style.height=.85*(r.other.bottom-r.other.top)+"px"}}function Co(e,t){return e.top-t.top||e.left-t.left}function To(e,t,i){let r=e.display,n=e.doc,o=document.createDocumentFragment(),s=Ln(e.display),l=s.left,a=Math.max(r.sizerWidth,Rn(e)-r.sizer.offsetLeft)-s.right,c="ltr"==n.direction;function d(e,t,i,r){t<0&&(t=0),t=Math.round(t),r=Math.round(r),o.appendChild(It("div",null,"CodeMirror-selected",`position: absolute; left: ${e}px;\n                             top: ${t}px; width: ${null==i?a-e:i}px;\n                             height: ${r-t}px`))}function u(t,i,r){let o,s,u=Zi(n,t),h=u.text.length;function p(i,r){return Zn(e,or(t,i),"div",u,r)}function m(t,i,r){let n=ro(e,u,null,t),o="ltr"==i==("after"==r)?"left":"right";return p("after"==r?n.begin:n.end-(/\s/.test(u.text.charAt(n.end-1))?2:1),o)[o]}let f=fi(u,n.direction);return function(e,t,i,r){if(!e)return r(t,i,"ltr",0);let n=!1;for(let o=0;o<e.length;++o){let s=e[o];(s.from<i&&s.to>t||t==i&&s.to==t)&&(r(Math.max(s.from,t),Math.min(s.to,i),1==s.level?"rtl":"ltr",o),n=!0)}n||r(t,i,"ltr")}(f,i||0,null==r?h:r,((e,t,n,u)=>{let g="ltr"==n,v=p(e,g?"left":"right"),b=p(t-1,g?"right":"left"),y=null==i&&0==e,_=null==r&&t==h,x=0==u,w=!f||u==f.length-1;if(b.top-v.top<=3){let e=(c?_:y)&&w,t=(c?y:_)&&x?l:(g?v:b).left,i=e?a:(g?b:v).right;d(t,v.top,i-t,v.bottom)}else{let i,r,o,s;g?(i=c&&y&&x?l:v.left,r=c?a:m(e,n,"before"),o=c?l:m(t,n,"after"),s=c&&_&&w?a:b.right):(i=c?m(e,n,"before"):l,r=!c&&y&&x?a:v.right,o=!c&&_&&w?l:b.left,s=c?m(t,n,"after"):a),d(i,v.top,r-i,v.bottom),v.bottom<b.top&&d(l,v.bottom,null,b.top),d(o,b.top,s-o,b.bottom)}(!o||Co(v,o)<0)&&(o=v),Co(b,o)<0&&(o=b),(!s||Co(v,s)<0)&&(s=v),Co(b,s)<0&&(s=b)})),{start:o,end:s}}let h=t.from(),p=t.to();if(h.line==p.line)u(h.line,h.ch,p.ch);else{let e=Zi(n,h.line),t=Zi(n,p.line),i=Ur(e)==Ur(t),r=u(h.line,h.ch,i?e.text.length+1:null).end,o=u(p.line,i?0:null,p.ch).start;i&&(r.top<o.top-2?(d(r.right,r.top,null,r.bottom),d(l,o.top,o.left,o.bottom)):d(r.right,r.top,o.left-r.right,r.bottom)),r.bottom<o.top&&d(l,r.bottom,null,o.top)}i.appendChild(o)}function Mo(e){if(!e.state.focused)return;let t=e.display;clearInterval(t.blinker);let i=!0;t.cursorDiv.style.visibility="",e.options.cursorBlinkRate>0?t.blinker=setInterval((()=>{e.hasFocus()||Po(e),t.cursorDiv.style.visibility=(i=!i)?"":"hidden"}),e.options.cursorBlinkRate):e.options.cursorBlinkRate<0&&(t.cursorDiv.style.visibility="hidden")}function Eo(e){e.hasFocus()||(e.display.input.focus(),e.state.focused||Lo(e))}function Ao(e){e.state.delayingBlurEvent=!0,setTimeout((()=>{e.state.delayingBlurEvent&&(e.state.delayingBlurEvent=!1,e.state.focused&&Po(e))}),100)}function Lo(e,t){e.state.delayingBlurEvent&&!e.state.draggingText&&(e.state.delayingBlurEvent=!1),"nocursor"!=e.options.readOnly&&(e.state.focused||(_i(e,"focus",e,t),e.state.focused=!0,zt(e.display.wrapper,"CodeMirror-focused"),e.curOp||e.display.selForContextMenu==e.doc.sel||(e.display.input.reset(),pt&&setTimeout((()=>e.display.input.reset(!0)),20)),e.display.input.receivedFocus()),Mo(e))}function Po(e,t){e.state.delayingBlurEvent||(e.state.focused&&(_i(e,"blur",e,t),e.state.focused=!1,Pt(e.display.wrapper,"CodeMirror-focused")),clearInterval(e.display.blinker),setTimeout((()=>{e.state.focused||(e.display.shift=!1)}),150))}function Ro(e){let t=e.display,i=t.lineDiv.offsetTop;for(let r=0;r<t.view.length;r++){let n,o=t.view[r],s=e.options.lineWrapping,l=0;if(o.hidden)continue;if(ut&&ht<8){let e=o.node.offsetTop+o.node.offsetHeight;n=e-i,i=e}else{let e=o.node.getBoundingClientRect();n=e.bottom-e.top,!s&&o.text.firstChild&&(l=o.text.firstChild.getBoundingClientRect().right-e.left-1)}let a=o.line.height-n;if((a>.005||a<-.005)&&(er(o.line,n),No(o.line),o.rest))for(let e=0;e<o.rest.length;e++)No(o.rest[e]);if(l>e.display.sizerWidth){let t=Math.ceil(l/co(e.display));t>e.display.maxLineLength&&(e.display.maxLineLength=t,e.display.maxLine=o.line,e.display.maxLineChanged=!0)}}}function No(e){if(e.widgets)for(let t=0;t<e.widgets.length;++t){let i=e.widgets[t],r=i.node.parentNode;r&&(i.height=r.offsetHeight)}}function Io(e,t,i){let r=i&&null!=i.top?Math.max(0,i.top):e.scroller.scrollTop;r=Math.floor(r-En(e));let n=i&&null!=i.bottom?i.bottom:r+e.wrapper.clientHeight,o=ir(t,r),s=ir(t,n);if(i&&i.ensure){let r=i.ensure.from.line,n=i.ensure.to.line;r<o?(o=r,s=ir(t,Kr(Zi(t,r))+e.wrapper.clientHeight)):Math.min(n,t.lastLine())>=s&&(o=ir(t,Kr(Zi(t,n))-e.wrapper.clientHeight),s=n)}return{from:o,to:Math.max(s,o+1)}}function Do(e,t){let i=e.display,r=ao(e.display);t.top<0&&(t.top=0);let n=e.curOp&&null!=e.curOp.scrollTop?e.curOp.scrollTop:i.scroller.scrollTop,o=Nn(e),s={};t.bottom-t.top>o&&(t.bottom=t.top+o);let l=e.doc.height+An(i),a=t.top<r,c=t.bottom>l-r;if(t.top<n)s.scrollTop=a?0:t.top;else if(t.bottom>n+o){let e=Math.min(t.top,(c?l:t.bottom)-o);e!=n&&(s.scrollTop=e)}let d=e.options.fixedGutter?0:i.gutters.offsetWidth,u=e.curOp&&null!=e.curOp.scrollLeft?e.curOp.scrollLeft:i.scroller.scrollLeft-d,h=Rn(e)-i.gutters.offsetWidth,p=t.right-t.left>h;return p&&(t.right=t.left+h),t.left<10?s.scrollLeft=0:t.left<u?s.scrollLeft=Math.max(0,t.left+d-(p?0:10)):t.right>h+u-3&&(s.scrollLeft=t.right+(p?0:10)-h),s}function Oo(e,t){null!=t&&(Fo(e),e.curOp.scrollTop=(null==e.curOp.scrollTop?e.doc.scrollTop:e.curOp.scrollTop)+t)}function $o(e){Fo(e);let t=e.getCursor();e.curOp.scrollToPos={from:t,to:t,margin:e.options.cursorScrollMargin}}function zo(e,t,i){null==t&&null==i||Fo(e),null!=t&&(e.curOp.scrollLeft=t),null!=i&&(e.curOp.scrollTop=i)}function Fo(e){let t=e.curOp.scrollToPos;if(t){e.curOp.scrollToPos=null,Bo(e,Qn(e,t.from),Qn(e,t.to),t.margin)}}function Bo(e,t,i,r){let n=Do(e,{left:Math.min(t.left,i.left),top:Math.min(t.top,i.top)-r,right:Math.max(t.right,i.right),bottom:Math.max(t.bottom,i.bottom)+r});zo(e,n.scrollLeft,n.scrollTop)}function Wo(e,t){Math.abs(e.doc.scrollTop-t)<2||(lt||hs(e,{top:t}),Ho(e,t,!0),lt&&hs(e),ls(e,100))}function Ho(e,t,i){t=Math.max(0,Math.min(e.display.scroller.scrollHeight-e.display.scroller.clientHeight,t)),(e.display.scroller.scrollTop!=t||i)&&(e.doc.scrollTop=t,e.display.scrollbars.setScrollTop(t),e.display.scroller.scrollTop!=t&&(e.display.scroller.scrollTop=t))}function Uo(e,t,i,r){t=Math.max(0,Math.min(t,e.display.scroller.scrollWidth-e.display.scroller.clientWidth)),(i?t==e.doc.scrollLeft:Math.abs(e.doc.scrollLeft-t)<2)&&!r||(e.doc.scrollLeft=t,fs(e),e.display.scroller.scrollLeft!=t&&(e.display.scroller.scrollLeft=t),e.display.scrollbars.setScrollLeft(t))}function Vo(e){let t=e.display,i=t.gutters.offsetWidth,r=Math.round(e.doc.height+An(e.display));return{clientHeight:t.scroller.clientHeight,viewHeight:t.wrapper.clientHeight,scrollWidth:t.scroller.scrollWidth,clientWidth:t.scroller.clientWidth,viewWidth:t.wrapper.clientWidth,barLeft:e.options.fixedGutter?i:0,docHeight:r,scrollHeight:r+Pn(e)+t.barHeight,nativeBarWidth:t.nativeBarWidth,gutterWidth:i}}function qo(e,t){t||(t=Vo(e));let i=e.display.barWidth,r=e.display.barHeight;jo(e,t);for(let t=0;t<4&&i!=e.display.barWidth||r!=e.display.barHeight;t++)i!=e.display.barWidth&&e.options.lineWrapping&&Ro(e),jo(e,Vo(e)),i=e.display.barWidth,r=e.display.barHeight}function jo(e,t){let i=e.display,r=i.scrollbars.update(t);i.sizer.style.paddingRight=(i.barWidth=r.right)+"px",i.sizer.style.paddingBottom=(i.barHeight=r.bottom)+"px",i.heightForcer.style.borderBottom=r.bottom+"px solid transparent",r.right&&r.bottom?(i.scrollbarFiller.style.display="block",i.scrollbarFiller.style.height=r.bottom+"px",i.scrollbarFiller.style.width=r.right+"px"):i.scrollbarFiller.style.display="",r.bottom&&e.options.coverGutterNextToScrollbar&&e.options.fixedGutter?(i.gutterFiller.style.display="block",i.gutterFiller.style.height=r.bottom+"px",i.gutterFiller.style.width=t.gutterWidth+"px"):i.gutterFiller.style.display=""}var Go={native:class{constructor(e,t,i){this.cm=i;let r=this.vert=It("div",[It("div",null,null,"min-width: 1px")],"CodeMirror-vscrollbar"),n=this.horiz=It("div",[It("div",null,null,"height: 100%; min-height: 1px")],"CodeMirror-hscrollbar");r.tabIndex=n.tabIndex=-1,e(r),e(n),vi(r,"scroll",(()=>{r.clientHeight&&t(r.scrollTop,"vertical")})),vi(n,"scroll",(()=>{n.clientWidth&&t(n.scrollLeft,"horizontal")})),this.checkedZeroWidth=!1,ut&&ht<8&&(this.horiz.style.minHeight=this.vert.style.minWidth="18px")}update(e){let t=e.scrollWidth>e.clientWidth+1,i=e.scrollHeight>e.clientHeight+1,r=e.nativeBarWidth;if(i){this.vert.style.display="block",this.vert.style.bottom=t?r+"px":"0";let i=e.viewHeight-(t?r:0);this.vert.firstChild.style.height=Math.max(0,e.scrollHeight-e.clientHeight+i)+"px"}else this.vert.style.display="",this.vert.firstChild.style.height="0";if(t){this.horiz.style.display="block",this.horiz.style.right=i?r+"px":"0",this.horiz.style.left=e.barLeft+"px";let t=e.viewWidth-e.barLeft-(i?r:0);this.horiz.firstChild.style.width=Math.max(0,e.scrollWidth-e.clientWidth+t)+"px"}else this.horiz.style.display="",this.horiz.firstChild.style.width="0";return!this.checkedZeroWidth&&e.clientHeight>0&&(0==r&&this.zeroWidthHack(),this.checkedZeroWidth=!0),{right:i?r:0,bottom:t?r:0}}setScrollLeft(e){this.horiz.scrollLeft!=e&&(this.horiz.scrollLeft=e),this.disableHoriz&&this.enableZeroWidthBar(this.horiz,this.disableHoriz,"horiz")}setScrollTop(e){this.vert.scrollTop!=e&&(this.vert.scrollTop=e),this.disableVert&&this.enableZeroWidthBar(this.vert,this.disableVert,"vert")}zeroWidthHack(){let e=kt&&!bt?"12px":"18px";this.horiz.style.height=this.vert.style.width=e,this.horiz.style.pointerEvents=this.vert.style.pointerEvents="none",this.disableHoriz=new Vt,this.disableVert=new Vt}enableZeroWidthBar(e,t,i){e.style.pointerEvents="auto",t.set(1e3,(function r(){let n=e.getBoundingClientRect();("vert"==i?document.elementFromPoint(n.right-1,(n.top+n.bottom)/2):document.elementFromPoint((n.right+n.left)/2,n.bottom-1))!=e?e.style.pointerEvents="none":t.set(1e3,r)}))}clear(){let e=this.horiz.parentNode;e.removeChild(this.horiz),e.removeChild(this.vert)}},null:class{update(){return{bottom:0,right:0}}setScrollLeft(){}setScrollTop(){}clear(){}}};function Ko(e){e.display.scrollbars&&(e.display.scrollbars.clear(),e.display.scrollbars.addClass&&Pt(e.display.wrapper,e.display.scrollbars.addClass)),e.display.scrollbars=new Go[e.options.scrollbarStyle]((t=>{e.display.wrapper.insertBefore(t,e.display.scrollbarFiller),vi(t,"mousedown",(()=>{e.state.focused&&setTimeout((()=>e.display.input.focus()),0)})),t.setAttribute("cm-not-content","true")}),((t,i)=>{"horizontal"==i?Uo(e,t):Wo(e,t)}),e),e.display.scrollbars.addClass&&zt(e.display.wrapper,e.display.scrollbars.addClass)}var Xo=0;function Yo(e){var t;e.curOp={cm:e,viewChanged:!1,startHeight:e.doc.height,forceUpdate:!1,updateInput:0,typing:!1,changeObjs:null,cursorActivityHandlers:null,cursorActivityCalled:0,selectionChanged:!1,updateMaxLine:!1,scrollLeft:null,scrollTop:null,scrollToPos:null,focus:!1,id:++Xo},t=e.curOp,un?un.ops.push(t):t.ownsGroup=un={ops:[t],delayedCallbacks:[]}}function Zo(e){let t=e.curOp;t&&function(e,t){let i=e.ownsGroup;if(i)try{!function(e){let t=e.delayedCallbacks,i=0;do{for(;i<t.length;i++)t[i].call(null);for(let t=0;t<e.ops.length;t++){let i=e.ops[t];if(i.cursorActivityHandlers)for(;i.cursorActivityCalled<i.cursorActivityHandlers.length;)i.cursorActivityHandlers[i.cursorActivityCalled++].call(null,i.cm)}}while(i<t.length)}(i)}finally{un=null,t(i)}}(t,(e=>{for(let t=0;t<e.ops.length;t++)e.ops[t].cm.curOp=null;!function(e){let t=e.ops;for(let e=0;e<t.length;e++)Jo(t[e]);for(let e=0;e<t.length;e++)Qo(t[e]);for(let e=0;e<t.length;e++)es(t[e]);for(let e=0;e<t.length;e++)ts(t[e]);for(let e=0;e<t.length;e++)is(t[e])}(e)}))}function Jo(e){let t=e.cm,i=t.display;!function(e){let t=e.display;!t.scrollbarsClipped&&t.scroller.offsetWidth&&(t.nativeBarWidth=t.scroller.offsetWidth-t.scroller.clientWidth,t.heightForcer.style.height=Pn(e)+"px",t.sizer.style.marginBottom=-t.nativeBarWidth+"px",t.sizer.style.borderRightWidth=Pn(e)+"px",t.scrollbarsClipped=!0)}(t),e.updateMaxLine&&Yr(t),e.mustUpdate=e.viewChanged||e.forceUpdate||null!=e.scrollTop||e.scrollToPos&&(e.scrollToPos.from.line<i.viewFrom||e.scrollToPos.to.line>=i.viewTo)||i.maxLineChanged&&t.options.lineWrapping,e.update=e.mustUpdate&&new cs(t,e.mustUpdate&&{top:e.scrollTop,ensure:e.scrollToPos},e.forceUpdate)}function Qo(e){e.updatedDisplay=e.mustUpdate&&ds(e.cm,e.update)}function es(e){let t=e.cm,i=t.display;e.updatedDisplay&&Ro(t),e.barMeasure=Vo(t),i.maxLineChanged&&!t.options.lineWrapping&&(e.adjustWidthTo=Dn(t,i.maxLine,i.maxLine.text.length).left+3,t.display.sizerWidth=e.adjustWidthTo,e.barMeasure.scrollWidth=Math.max(i.scroller.clientWidth,i.sizer.offsetLeft+e.adjustWidthTo+Pn(t)+t.display.barWidth),e.maxScrollLeft=Math.max(0,i.sizer.offsetLeft+e.adjustWidthTo-Rn(t))),(e.updatedDisplay||e.selectionChanged)&&(e.preparedSelection=i.input.prepareSelection())}function ts(e){let t=e.cm;null!=e.adjustWidthTo&&(t.display.sizer.style.minWidth=e.adjustWidthTo+"px",e.maxScrollLeft<t.doc.scrollLeft&&Uo(t,Math.min(t.display.scroller.scrollLeft,e.maxScrollLeft),!0),t.display.maxLineChanged=!1);let i=e.focus&&e.focus==$t();e.preparedSelection&&t.display.input.showSelection(e.preparedSelection,i),(e.updatedDisplay||e.startHeight!=t.doc.height)&&qo(t,e.barMeasure),e.updatedDisplay&&ms(t,e.barMeasure),e.selectionChanged&&Mo(t),t.state.focused&&e.updateInput&&t.display.input.reset(e.typing),i&&Eo(e.cm)}function is(e){let t=e.cm,i=t.display,r=t.doc;if(e.updatedDisplay&&us(t,e.update),null==i.wheelStartX||null==e.scrollTop&&null==e.scrollLeft&&!e.scrollToPos||(i.wheelStartX=i.wheelStartY=null),null!=e.scrollTop&&Ho(t,e.scrollTop,e.forceScroll),null!=e.scrollLeft&&Uo(t,e.scrollLeft,!0,!0),e.scrollToPos){let i=function(e,t,i,r){let n;null==r&&(r=0),e.options.lineWrapping||t!=i||(i="before"==(t=t.ch?or(t.line,"before"==t.sticky?t.ch-1:t.ch,"after"):t).sticky?or(t.line,t.ch+1,"before"):t);for(let o=0;o<5;o++){let o=!1,s=Jn(e,t),l=i&&i!=t?Jn(e,i):s;n={left:Math.min(s.left,l.left),top:Math.min(s.top,l.top)-r,right:Math.max(s.left,l.left),bottom:Math.max(s.bottom,l.bottom)+r};let a=Do(e,n),c=e.doc.scrollTop,d=e.doc.scrollLeft;if(null!=a.scrollTop&&(Wo(e,a.scrollTop),Math.abs(e.doc.scrollTop-c)>1&&(o=!0)),null!=a.scrollLeft&&(Uo(e,a.scrollLeft),Math.abs(e.doc.scrollLeft-d)>1&&(o=!0)),!o)break}return n}(t,hr(r,e.scrollToPos.from),hr(r,e.scrollToPos.to),e.scrollToPos.margin);!function(e,t){if(xi(e,"scrollCursorIntoView"))return;let i=e.display,r=i.sizer.getBoundingClientRect(),n=null;if(t.top+r.top<0?n=!0:t.bottom+r.top>(window.innerHeight||document.documentElement.clientHeight)&&(n=!1),null!=n&&!yt){let r=It("div","​",null,`position: absolute;\n                         top: ${t.top-i.viewOffset-En(e.display)}px;\n                         height: ${t.bottom-t.top+Pn(e)+i.barHeight}px;\n                         left: ${t.left}px; width: ${Math.max(2,t.right-t.left)}px;`);e.display.lineSpace.appendChild(r),r.scrollIntoView(n),e.display.lineSpace.removeChild(r)}}(t,i)}let n=e.maybeHiddenMarkers,o=e.maybeUnhiddenMarkers;if(n)for(let e=0;e<n.length;++e)n[e].lines.length||_i(n[e],"hide");if(o)for(let e=0;e<o.length;++e)o[e].lines.length&&_i(o[e],"unhide");i.wrapper.offsetHeight&&(r.scrollTop=t.display.scroller.scrollTop),e.changeObjs&&_i(t,"changes",t,e.changeObjs),e.update&&e.update.finish()}function rs(e,t){if(e.curOp)return t();Yo(e);try{return t()}finally{Zo(e)}}function ns(e,t){return function(){if(e.curOp)return t.apply(e,arguments);Yo(e);try{return t.apply(e,arguments)}finally{Zo(e)}}}function os(e){return function(){if(this.curOp)return e.apply(this,arguments);Yo(this);try{return e.apply(this,arguments)}finally{Zo(this)}}}function ss(e){return function(){let t=this.cm;if(!t||t.curOp)return e.apply(this,arguments);Yo(t);try{return e.apply(this,arguments)}finally{Zo(t)}}}function ls(e,t){e.doc.highlightFrontier<e.display.viewTo&&e.state.highlight.set(t,Wt(as,e))}function as(e){let t=e.doc;if(t.highlightFrontier>=e.display.viewTo)return;let i=+new Date+e.options.workTime,r=br(e,t.highlightFrontier),n=[];t.iter(r.line,Math.min(t.first+t.size,e.display.viewTo+500),(o=>{if(r.line>=e.display.viewFrom){let i=o.styles,s=o.text.length>e.options.maxHighlightLength?Gi(t.mode,r.state):null,l=gr(e,o,r,!0);s&&(r.state=s),o.styles=l.styles;let a=o.styleClasses,c=l.classes;c?o.styleClasses=c:a&&(o.styleClasses=null);let d=!i||i.length!=o.styles.length||a!=c&&(!a||!c||a.bgClass!=c.bgClass||a.textClass!=c.textClass);for(let e=0;!d&&e<i.length;++e)d=i[e]!=o.styles[e];d&&n.push(r.line),o.stateAfter=r.save(),r.nextLine()}else o.text.length<=e.options.maxHighlightLength&&yr(e,o.text,r),o.stateAfter=r.line%5==0?r.save():null,r.nextLine();if(+new Date>i)return ls(e,e.options.workDelay),!0})),t.highlightFrontier=r.line,t.modeFrontier=Math.max(t.modeFrontier,r.line),n.length&&rs(e,(()=>{for(let t=0;t<n.length;t++)bo(e,n[t],"text")}))}var cs=class{constructor(e,t,i){let r=e.display;this.viewport=t,this.visible=Io(r,e.doc,t),this.editorIsHidden=!r.wrapper.offsetWidth,this.wrapperHeight=r.wrapper.clientHeight,this.wrapperWidth=r.wrapper.clientWidth,this.oldDisplayWidth=Rn(e),this.force=i,this.dims=uo(e),this.events=[]}signal(e,t){ki(e,t)&&this.events.push(arguments)}finish(){for(let e=0;e<this.events.length;e++)_i.apply(null,this.events[e])}};function ds(e,t){let i=e.display,r=e.doc;if(t.editorIsHidden)return yo(e),!1;if(!t.force&&t.visible.from>=i.viewFrom&&t.visible.to<=i.viewTo&&(null==i.updateLineNumbers||i.updateLineNumbers>=i.viewTo)&&i.renderedView==i.view&&0==xo(e))return!1;gs(e)&&(yo(e),t.dims=uo(e));let n=r.first+r.size,o=Math.max(t.visible.from-e.options.viewportMargin,r.first),s=Math.min(n,t.visible.to+e.options.viewportMargin);i.viewFrom<o&&o-i.viewFrom<20&&(o=Math.max(r.first,i.viewFrom)),i.viewTo>s&&i.viewTo-s<20&&(s=Math.min(n,i.viewTo)),Mr&&(o=Vr(e.doc,o),s=qr(e.doc,s));let l=o!=i.viewFrom||s!=i.viewTo||i.lastWrapHeight!=t.wrapperHeight||i.lastWrapWidth!=t.wrapperWidth;!function(e,t,i){let r=e.display;0==r.view.length||t>=r.viewTo||i<=r.viewFrom?(r.view=dn(e,t,i),r.viewFrom=t):(r.viewFrom>t?r.view=dn(e,t,r.viewFrom).concat(r.view):r.viewFrom<t&&(r.view=r.view.slice(go(e,t))),r.viewFrom=t,r.viewTo<i?r.view=r.view.concat(dn(e,r.viewTo,i)):r.viewTo>i&&(r.view=r.view.slice(0,go(e,i)))),r.viewTo=i}(e,o,s),i.viewOffset=Kr(Zi(e.doc,i.viewFrom)),e.display.mover.style.top=i.viewOffset+"px";let a=xo(e);if(!l&&0==a&&!t.force&&i.renderedView==i.view&&(null==i.updateLineNumbers||i.updateLineNumbers>=i.viewTo))return!1;let c=function(e){if(e.hasFocus())return null;let t=$t();if(!t||!Ot(e.display.lineDiv,t))return null;let i={activeElt:t};if(window.getSelection){let t=window.getSelection();t.anchorNode&&t.extend&&Ot(e.display.lineDiv,t.anchorNode)&&(i.anchorNode=t.anchorNode,i.anchorOffset=t.anchorOffset,i.focusNode=t.focusNode,i.focusOffset=t.focusOffset)}return i}(e);return a>4&&(i.lineDiv.style.display="none"),function(e,t,i){let r=e.display,n=e.options.lineNumbers,o=r.lineDiv,s=o.firstChild;function l(t){let i=t.nextSibling;return pt&&kt&&e.display.currentWheelTarget==t?t.style.display="none":t.parentNode.removeChild(t),i}let a=r.view,c=r.viewFrom;for(let r=0;r<a.length;r++){let d=a[r];if(d.hidden);else if(d.node&&d.node.parentNode==o){for(;s!=d.node;)s=l(s);let r=n&&null!=t&&t<=c&&d.lineNumber;d.changes&&(qt(d.changes,"gutter")>-1&&(r=!1),fn(e,d,c,i)),r&&(Rt(d.lineNumber),d.lineNumber.appendChild(document.createTextNode(nr(e.options,c)))),s=d.node.nextSibling}else{let t=wn(e,d,c,i);o.insertBefore(t,s)}c+=d.size}for(;s;)s=l(s)}(e,i.updateLineNumbers,t.dims),a>4&&(i.lineDiv.style.display=""),i.renderedView=i.view,function(e){if(e&&e.activeElt&&e.activeElt!=$t()&&(e.activeElt.focus(),!/^(INPUT|TEXTAREA)$/.test(e.activeElt.nodeName)&&e.anchorNode&&Ot(document.body,e.anchorNode)&&Ot(document.body,e.focusNode))){let t=window.getSelection(),i=document.createRange();i.setEnd(e.anchorNode,e.anchorOffset),i.collapse(!1),t.removeAllRanges(),t.addRange(i),t.extend(e.focusNode,e.focusOffset)}}(c),Rt(i.cursorDiv),Rt(i.selectionDiv),i.gutters.style.height=i.sizer.style.minHeight=0,l&&(i.lastWrapHeight=t.wrapperHeight,i.lastWrapWidth=t.wrapperWidth,ls(e,400)),i.updateLineNumbers=null,!0}function us(e,t){let i=t.viewport;for(let r=!0;;r=!1){if(r&&e.options.lineWrapping&&t.oldDisplayWidth!=Rn(e))r&&(t.visible=Io(e.display,e.doc,i));else if(i&&null!=i.top&&(i={top:Math.min(e.doc.height+An(e.display)-Nn(e),i.top)}),t.visible=Io(e.display,e.doc,i),t.visible.from>=e.display.viewFrom&&t.visible.to<=e.display.viewTo)break;if(!ds(e,t))break;Ro(e);let n=Vo(e);wo(e),qo(e,n),ms(e,n),t.force=!1}t.signal(e,"update",e),e.display.viewFrom==e.display.reportedViewFrom&&e.display.viewTo==e.display.reportedViewTo||(t.signal(e,"viewportChange",e,e.display.viewFrom,e.display.viewTo),e.display.reportedViewFrom=e.display.viewFrom,e.display.reportedViewTo=e.display.viewTo)}function hs(e,t){let i=new cs(e,t);if(ds(e,i)){Ro(e),us(e,i);let t=Vo(e);wo(e),qo(e,t),ms(e,t),i.finish()}}function ps(e){let t=e.gutters.offsetWidth;e.sizer.style.marginLeft=t+"px",pn(e,"gutterChanged",e)}function ms(e,t){e.display.sizer.style.minHeight=t.docHeight+"px",e.display.heightForcer.style.top=t.docHeight+"px",e.display.gutters.style.height=t.docHeight+e.display.barHeight+Pn(e)+"px"}function fs(e){let t=e.display,i=t.view;if(!(t.alignWidgets||t.gutters.firstChild&&e.options.fixedGutter))return;let r=ho(t)-t.scroller.scrollLeft+e.doc.scrollLeft,n=t.gutters.offsetWidth,o=r+"px";for(let t=0;t<i.length;t++)if(!i[t].hidden){e.options.fixedGutter&&(i[t].gutter&&(i[t].gutter.style.left=o),i[t].gutterBackground&&(i[t].gutterBackground.style.left=o));let r=i[t].alignable;if(r)for(let e=0;e<r.length;e++)r[e].style.left=o}e.options.fixedGutter&&(t.gutters.style.left=r+n+"px")}function gs(e){if(!e.options.lineNumbers)return!1;let t=e.doc,i=nr(e.options,t.first+t.size-1),r=e.display;if(i.length!=r.lineNumChars){let t=r.measure.appendChild(It("div",[It("div",i)],"CodeMirror-linenumber CodeMirror-gutter-elt")),n=t.firstChild.offsetWidth,o=t.offsetWidth-n;return r.lineGutter.style.width="",r.lineNumInnerWidth=Math.max(n,r.lineGutter.offsetWidth-o)+1,r.lineNumWidth=r.lineNumInnerWidth+o,r.lineNumChars=r.lineNumInnerWidth?i.length:-1,r.lineGutter.style.width=r.lineNumWidth+"px",ps(e.display),!0}return!1}function vs(e,t){let i=[],r=!1;for(let n=0;n<e.length;n++){let o=e[n],s=null;if("string"!=typeof o&&(s=o.style,o=o.className),"CodeMirror-linenumbers"==o){if(!t)continue;r=!0}i.push({className:o,style:s})}return t&&!r&&i.push({className:"CodeMirror-linenumbers",style:null}),i}function bs(e){let t=e.gutters,i=e.gutterSpecs;Rt(t),e.lineGutter=null;for(let r=0;r<i.length;++r){let{className:n,style:o}=i[r],s=t.appendChild(It("div",null,"CodeMirror-gutter "+n));o&&(s.style.cssText=o),"CodeMirror-linenumbers"==n&&(e.lineGutter=s,s.style.width=(e.lineNumWidth||1)+"px")}t.style.display=i.length?"":"none",ps(e)}function ys(e){bs(e.display),vo(e),fs(e)}function _s(e,t,i,r){let n=this;this.input=i,n.scrollbarFiller=It("div",null,"CodeMirror-scrollbar-filler"),n.scrollbarFiller.setAttribute("cm-not-content","true"),n.gutterFiller=It("div",null,"CodeMirror-gutter-filler"),n.gutterFiller.setAttribute("cm-not-content","true"),n.lineDiv=Dt("div",null,"CodeMirror-code"),n.selectionDiv=It("div",null,null,"position: relative; z-index: 1"),n.cursorDiv=It("div",null,"CodeMirror-cursors"),n.measure=It("div",null,"CodeMirror-measure"),n.lineMeasure=It("div",null,"CodeMirror-measure"),n.lineSpace=Dt("div",[n.measure,n.lineMeasure,n.selectionDiv,n.cursorDiv,n.lineDiv],null,"position: relative; outline: none");let o=Dt("div",[n.lineSpace],"CodeMirror-lines");n.mover=It("div",[o],null,"position: relative"),n.sizer=It("div",[n.mover],"CodeMirror-sizer"),n.sizerWidth=null,n.heightForcer=It("div",null,null,"position: absolute; height: "+jt+"px; width: 1px;"),n.gutters=It("div",null,"CodeMirror-gutters"),n.lineGutter=null,n.scroller=It("div",[n.sizer,n.heightForcer,n.gutters],"CodeMirror-scroll"),n.scroller.setAttribute("tabIndex","-1"),n.wrapper=It("div",[n.scrollbarFiller,n.gutterFiller,n.scroller],"CodeMirror"),ut&&ht<8&&(n.gutters.style.zIndex=-1,n.scroller.style.paddingRight=0),pt||lt&&wt||(n.scroller.draggable=!0),e&&(e.appendChild?e.appendChild(n.wrapper):e(n.wrapper)),n.viewFrom=n.viewTo=t.first,n.reportedViewFrom=n.reportedViewTo=t.first,n.view=[],n.renderedView=null,n.externalMeasured=null,n.viewOffset=0,n.lastWrapHeight=n.lastWrapWidth=0,n.updateLineNumbers=null,n.nativeBarWidth=n.barHeight=n.barWidth=0,n.scrollbarsClipped=!1,n.lineNumWidth=n.lineNumInnerWidth=n.lineNumChars=null,n.alignWidgets=!1,n.cachedCharWidth=n.cachedTextHeight=n.cachedPaddingH=null,n.maxLine=null,n.maxLineLength=0,n.maxLineChanged=!1,n.wheelDX=n.wheelDY=n.wheelStartX=n.wheelStartY=null,n.shift=!1,n.selForContextMenu=null,n.activeTouch=null,n.gutterSpecs=vs(r.gutters,r.lineNumbers),bs(n),i.init(n)}var xs=0,ws=null;function ks(e){let t=e.wheelDeltaX,i=e.wheelDeltaY;return null==t&&e.detail&&e.axis==e.HORIZONTAL_AXIS&&(t=e.detail),null==i&&e.detail&&e.axis==e.VERTICAL_AXIS?i=e.detail:null==i&&(i=e.wheelDelta),{x:t,y:i}}function Ss(e){let t=ks(e);return t.x*=ws,t.y*=ws,t}function Cs(e,t){let i=ks(t),r=i.x,n=i.y,o=e.display,s=o.scroller,l=s.scrollWidth>s.clientWidth,a=s.scrollHeight>s.clientHeight;if(r&&l||n&&a){if(n&&kt&&pt)e:for(let i=t.target,r=o.view;i!=s;i=i.parentNode)for(let t=0;t<r.length;t++)if(r[t].node==i){e.display.currentWheelTarget=i;break e}if(r&&!lt&&!gt&&null!=ws)return n&&a&&Wo(e,Math.max(0,s.scrollTop+n*ws)),Uo(e,Math.max(0,s.scrollLeft+r*ws)),(!n||n&&a)&&Ci(t),void(o.wheelStartX=null);if(n&&null!=ws){let t=n*ws,i=e.doc.scrollTop,r=i+o.wrapper.clientHeight;t<0?i=Math.max(0,i+t-50):r=Math.min(e.doc.height,r+t+50),hs(e,{top:i,bottom:r})}xs<20&&(null==o.wheelStartX?(o.wheelStartX=s.scrollLeft,o.wheelStartY=s.scrollTop,o.wheelDX=r,o.wheelDY=n,setTimeout((()=>{if(null==o.wheelStartX)return;let e=s.scrollLeft-o.wheelStartX,t=s.scrollTop-o.wheelStartY,i=t&&o.wheelDY&&t/o.wheelDY||e&&o.wheelDX&&e/o.wheelDX;o.wheelStartX=o.wheelStartY=null,i&&(ws=(ws*xs+i)/(xs+1),++xs)}),200)):(o.wheelDX+=r,o.wheelDY+=n))}}ut?ws=-.53:lt?ws=15:ft?ws=-.7:vt&&(ws=-1/3);var Ts=class{constructor(e,t){this.ranges=e,this.primIndex=t}primary(){return this.ranges[this.primIndex]}equals(e){if(e==this)return!0;if(e.primIndex!=this.primIndex||e.ranges.length!=this.ranges.length)return!1;for(let t=0;t<this.ranges.length;t++){let i=this.ranges[t],r=e.ranges[t];if(!lr(i.anchor,r.anchor)||!lr(i.head,r.head))return!1}return!0}deepCopy(){let e=[];for(let t=0;t<this.ranges.length;t++)e[t]=new Ms(ar(this.ranges[t].anchor),ar(this.ranges[t].head));return new Ts(e,this.primIndex)}somethingSelected(){for(let e=0;e<this.ranges.length;e++)if(!this.ranges[e].empty())return!0;return!1}contains(e,t){t||(t=e);for(let i=0;i<this.ranges.length;i++){let r=this.ranges[i];if(sr(t,r.from())>=0&&sr(e,r.to())<=0)return i}return-1}},Ms=class{constructor(e,t){this.anchor=e,this.head=t}from(){return dr(this.anchor,this.head)}to(){return cr(this.anchor,this.head)}empty(){return this.head.line==this.anchor.line&&this.head.ch==this.anchor.ch}};function Es(e,t,i){let r=e&&e.options.selectionsMayTouch,n=t[i];t.sort(((e,t)=>sr(e.from(),t.from()))),i=qt(t,n);for(let e=1;e<t.length;e++){let n=t[e],o=t[e-1],s=sr(o.to(),n.from());if(r&&!n.empty()?s>0:s>=0){let r=dr(o.from(),n.from()),s=cr(o.to(),n.to()),l=o.empty()?n.from()==n.head:o.from()==o.head;e<=i&&--i,t.splice(--e,2,new Ms(l?s:r,l?r:s))}}return new Ts(t,i)}function As(e,t){return new Ts([new Ms(e,t||e)],0)}function Ls(e){return e.text?or(e.from.line+e.text.length-1,ei(e.text).length+(1==e.text.length?e.from.ch:0)):e.to}function Ps(e,t){if(sr(e,t.from)<0)return e;if(sr(e,t.to)<=0)return Ls(t);let i=e.line+t.text.length-(t.to.line-t.from.line)-1,r=e.ch;return e.line==t.to.line&&(r+=Ls(t).ch-t.to.ch),or(i,r)}function Rs(e,t){let i=[];for(let r=0;r<e.sel.ranges.length;r++){let n=e.sel.ranges[r];i.push(new Ms(Ps(n.anchor,t),Ps(n.head,t)))}return Es(e.cm,i,e.sel.primIndex)}function Ns(e,t,i){return e.line==t.line?or(i.line,e.ch-t.ch+i.ch):or(i.line+(e.line-t.line),e.ch)}function Is(e){e.doc.mode=Vi(e.options,e.doc.modeOption),Ds(e)}function Ds(e){e.doc.iter((e=>{e.stateAfter&&(e.stateAfter=null),e.styles&&(e.styles=null)})),e.doc.modeFrontier=e.doc.highlightFrontier=e.doc.first,ls(e,100),e.state.modeGen++,e.curOp&&vo(e)}function Os(e,t){return 0==t.from.ch&&0==t.to.ch&&""==ei(t.text)&&(!e.cm||e.cm.options.wholeLineUpdateBefore)}function $s(e,t,i,r){function n(e){return i?i[e]:null}function o(e,i,n){!function(e,t,i,r){e.text=t,e.stateAfter&&(e.stateAfter=null),e.styles&&(e.styles=null),null!=e.order&&(e.order=null),Nr(e),Ir(e,i);let n=r?r(e):1;n!=e.height&&er(e,n)}(e,i,n,r),pn(e,"change",e,t)}function s(e,t){let i=[];for(let o=e;o<t;++o)i.push(new Zr(c[o],n(o),r));return i}let l=t.from,a=t.to,c=t.text,d=Zi(e,l.line),u=Zi(e,a.line),h=ei(c),p=n(c.length-1),m=a.line-l.line;if(t.full)e.insert(0,s(0,c.length)),e.remove(c.length,e.size-c.length);else if(Os(e,t)){let t=s(0,c.length-1);o(u,u.text,p),m&&e.remove(l.line,m),t.length&&e.insert(l.line,t)}else if(d==u)if(1==c.length)o(d,d.text.slice(0,l.ch)+h+d.text.slice(a.ch),p);else{let t=s(1,c.length-1);t.push(new Zr(h+d.text.slice(a.ch),p,r)),o(d,d.text.slice(0,l.ch)+c[0],n(0)),e.insert(l.line+1,t)}else if(1==c.length)o(d,d.text.slice(0,l.ch)+c[0]+u.text.slice(a.ch),n(0)),e.remove(l.line+1,m);else{o(d,d.text.slice(0,l.ch)+c[0],n(0)),o(u,h+u.text.slice(a.ch),p);let t=s(1,c.length-1);m>1&&e.remove(l.line+1,m-1),e.insert(l.line+1,t)}pn(e,"change",e,t)}function zs(e,t,i){!function e(r,n,o){if(r.linked)for(let s=0;s<r.linked.length;++s){let l=r.linked[s];if(l.doc==n)continue;let a=o&&l.sharedHist;i&&!a||(t(l.doc,a),e(l.doc,r,a))}}(e,null,!0)}function Fs(e,t){if(t.cm)throw new Error("This document is already in use.");e.doc=t,t.cm=e,mo(e),Is(e),Bs(e),e.options.lineWrapping||Yr(e),e.options.mode=t.modeOption,vo(e)}function Bs(e){("rtl"==e.doc.direction?zt:Pt)(e.display.lineDiv,"CodeMirror-rtl")}function Ws(e){this.done=[],this.undone=[],this.undoDepth=e?e.undoDepth:1/0,this.lastModTime=this.lastSelTime=0,this.lastOp=this.lastSelOp=null,this.lastOrigin=this.lastSelOrigin=null,this.generation=this.maxGeneration=e?e.maxGeneration:1}function Hs(e,t){let i={from:ar(t.from),to:Ls(t),text:Ji(e,t.from,t.to)};return Gs(e,i,t.from.line,t.to.line+1),zs(e,(e=>Gs(e,i,t.from.line,t.to.line+1)),!0),i}function Us(e){for(;e.length;){if(!ei(e).ranges)break;e.pop()}}function Vs(e,t,i,r){let n=e.history;n.undone.length=0;let o,s,l=+new Date;if((n.lastOp==r||n.lastOrigin==t.origin&&t.origin&&("+"==t.origin.charAt(0)&&n.lastModTime>l-(e.cm?e.cm.options.historyEventDelay:500)||"*"==t.origin.charAt(0)))&&(o=function(e,t){return t?(Us(e.done),ei(e.done)):e.done.length&&!ei(e.done).ranges?ei(e.done):e.done.length>1&&!e.done[e.done.length-2].ranges?(e.done.pop(),ei(e.done)):void 0}(n,n.lastOp==r)))s=ei(o.changes),0==sr(t.from,t.to)&&0==sr(t.from,s.to)?s.to=Ls(t):o.changes.push(Hs(e,t));else{let i=ei(n.done);for(i&&i.ranges||js(e.sel,n.done),o={changes:[Hs(e,t)],generation:n.generation},n.done.push(o);n.done.length>n.undoDepth;)n.done.shift(),n.done[0].ranges||n.done.shift()}n.done.push(i),n.generation=++n.maxGeneration,n.lastModTime=n.lastSelTime=l,n.lastOp=n.lastSelOp=r,n.lastOrigin=n.lastSelOrigin=t.origin,s||_i(e,"historyAdded")}function qs(e,t,i,r){let n=e.history,o=r&&r.origin;i==n.lastSelOp||o&&n.lastSelOrigin==o&&(n.lastModTime==n.lastSelTime&&n.lastOrigin==o||function(e,t,i,r){let n=t.charAt(0);return"*"==n||"+"==n&&i.ranges.length==r.ranges.length&&i.somethingSelected()==r.somethingSelected()&&new Date-e.history.lastSelTime<=(e.cm?e.cm.options.historyEventDelay:500)}(e,o,ei(n.done),t))?n.done[n.done.length-1]=t:js(t,n.done),n.lastSelTime=+new Date,n.lastSelOrigin=o,n.lastSelOp=i,r&&!1!==r.clearRedo&&Us(n.undone)}function js(e,t){let i=ei(t);i&&i.ranges&&i.equals(e)||t.push(e)}function Gs(e,t,i,r){let n=t["spans_"+e.id],o=0;e.iter(Math.max(e.first,i),Math.min(e.first+e.size,r),(i=>{i.markedSpans&&((n||(n=t["spans_"+e.id]={}))[o]=i.markedSpans),++o}))}function Ks(e){if(!e)return null;let t;for(let i=0;i<e.length;++i)e[i].marker.explicitlyCleared?t||(t=e.slice(0,i)):t&&t.push(e[i]);return t?t.length?t:null:e}function Xs(e,t){let i=function(e,t){let i=t["spans_"+e.id];if(!i)return null;let r=[];for(let e=0;e<t.text.length;++e)r.push(Ks(i[e]));return r}(e,t),r=Pr(e,t);if(!i)return r;if(!r)return i;for(let e=0;e<i.length;++e){let t=i[e],n=r[e];if(t&&n)e:for(let e=0;e<n.length;++e){let i=n[e];for(let e=0;e<t.length;++e)if(t[e].marker==i.marker)continue e;t.push(i)}else n&&(i[e]=n)}return i}function Ys(e,t,i){let r=[];for(let o=0;o<e.length;++o){let s=e[o];if(s.ranges){r.push(i?Ts.prototype.deepCopy.call(s):s);continue}let l=s.changes,a=[];r.push({changes:a});for(let e=0;e<l.length;++e){let i,r=l[e];if(a.push({from:r.from,to:r.to,text:r.text}),t)for(var n in r)(i=n.match(/^spans_(\d+)$/))&&qt(t,Number(i[1]))>-1&&(ei(a)[n]=r[n],delete r[n])}}return r}function Zs(e,t,i,r){if(r){let r=e.anchor;if(i){let e=sr(t,r)<0;e!=sr(i,r)<0?(r=t,t=i):e!=sr(t,i)<0&&(t=i)}return new Ms(r,t)}return new Ms(i||t,t)}function Js(e,t,i,r,n){null==n&&(n=e.cm&&(e.cm.display.shift||e.extend)),rl(e,new Ts([Zs(e.sel.primary(),t,i,n)],0),r)}function Qs(e,t,i){let r=[],n=e.cm&&(e.cm.display.shift||e.extend);for(let i=0;i<e.sel.ranges.length;i++)r[i]=Zs(e.sel.ranges[i],t[i],null,n);rl(e,Es(e.cm,r,e.sel.primIndex),i)}function el(e,t,i,r){let n=e.sel.ranges.slice(0);n[t]=i,rl(e,Es(e.cm,n,e.sel.primIndex),r)}function tl(e,t,i,r){rl(e,As(t,i),r)}function il(e,t,i){let r=e.history.done,n=ei(r);n&&n.ranges?(r[r.length-1]=t,nl(e,t,i)):rl(e,t,i)}function rl(e,t,i){nl(e,t,i),qs(e,e.sel,e.cm?e.cm.curOp.id:NaN,i)}function nl(e,t,i){(ki(e,"beforeSelectionChange")||e.cm&&ki(e.cm,"beforeSelectionChange"))&&(t=function(e,t,i){let r={ranges:t.ranges,update:function(t){this.ranges=[];for(let i=0;i<t.length;i++)this.ranges[i]=new Ms(hr(e,t[i].anchor),hr(e,t[i].head))},origin:i&&i.origin};return _i(e,"beforeSelectionChange",e,r),e.cm&&_i(e.cm,"beforeSelectionChange",e.cm,r),r.ranges!=t.ranges?Es(e.cm,r.ranges,r.ranges.length-1):t}(e,t,i));let r=i&&i.bias||(sr(t.primary().head,e.sel.primary().head)<0?-1:1);ol(e,ll(e,t,r,!0)),i&&!1===i.scroll||!e.cm||"nocursor"==e.cm.getOption("readOnly")||$o(e.cm)}function ol(e,t){t.equals(e.sel)||(e.sel=t,e.cm&&(e.cm.curOp.updateInput=1,e.cm.curOp.selectionChanged=!0,wi(e.cm)),pn(e,"cursorActivity",e))}function sl(e){ol(e,ll(e,e.sel,null,!1))}function ll(e,t,i,r){let n;for(let o=0;o<t.ranges.length;o++){let s=t.ranges[o],l=t.ranges.length==e.sel.ranges.length&&e.sel.ranges[o],a=cl(e,s.anchor,l&&l.anchor,i,r),c=cl(e,s.head,l&&l.head,i,r);(n||a!=s.anchor||c!=s.head)&&(n||(n=t.ranges.slice(0,o)),n[o]=new Ms(a,c))}return n?Es(e.cm,n,t.primIndex):t}function al(e,t,i,r,n){let o=Zi(e,t.line);if(o.markedSpans)for(let s=0;s<o.markedSpans.length;++s){let l=o.markedSpans[s],a=l.marker,c="selectLeft"in a?!a.selectLeft:a.inclusiveLeft,d="selectRight"in a?!a.selectRight:a.inclusiveRight;if((null==l.from||(c?l.from<=t.ch:l.from<t.ch))&&(null==l.to||(d?l.to>=t.ch:l.to>t.ch))){if(n&&(_i(a,"beforeCursorEnter"),a.explicitlyCleared)){if(o.markedSpans){--s;continue}break}if(!a.atomic)continue;if(i){let s,l=a.find(r<0?1:-1);if((r<0?d:c)&&(l=dl(e,l,-r,l&&l.line==t.line?o:null)),l&&l.line==t.line&&(s=sr(l,i))&&(r<0?s<0:s>0))return al(e,l,t,r,n)}let l=a.find(r<0?-1:1);return(r<0?c:d)&&(l=dl(e,l,r,l.line==t.line?o:null)),l?al(e,l,t,r,n):null}}return t}function cl(e,t,i,r,n){let o=r||1,s=al(e,t,i,o,n)||!n&&al(e,t,i,o,!0)||al(e,t,i,-o,n)||!n&&al(e,t,i,-o,!0);return s||(e.cantEdit=!0,or(e.first,0))}function dl(e,t,i,r){return i<0&&0==t.ch?t.line>e.first?hr(e,or(t.line-1)):null:i>0&&t.ch==(r||Zi(e,t.line)).text.length?t.line<e.first+e.size-1?or(t.line+1,0):null:new or(t.line,t.ch+i)}function ul(e){e.setSelection(or(e.firstLine(),0),or(e.lastLine()),Kt)}function hl(e,t,i){let r={canceled:!1,from:t.from,to:t.to,text:t.text,origin:t.origin,cancel:()=>r.canceled=!0};return i&&(r.update=(t,i,n,o)=>{t&&(r.from=hr(e,t)),i&&(r.to=hr(e,i)),n&&(r.text=n),void 0!==o&&(r.origin=o)}),_i(e,"beforeChange",e,r),e.cm&&_i(e.cm,"beforeChange",e.cm,r),r.canceled?(e.cm&&(e.cm.curOp.updateInput=2),null):{from:r.from,to:r.to,text:r.text,origin:r.origin}}function pl(e,t,i){if(e.cm){if(!e.cm.curOp)return ns(e.cm,pl)(e,t,i);if(e.cm.state.suppressEdits)return}if((ki(e,"beforeChange")||e.cm&&ki(e.cm,"beforeChange"))&&!(t=hl(e,t,!0)))return;let r=Tr&&!i&&function(e,t,i){let r=null;if(e.iter(t.line,i.line+1,(e=>{if(e.markedSpans)for(let t=0;t<e.markedSpans.length;++t){let i=e.markedSpans[t].marker;!i.readOnly||r&&-1!=qt(r,i)||(r||(r=[])).push(i)}})),!r)return null;let n=[{from:t,to:i}];for(let e=0;e<r.length;++e){let t=r[e],i=t.find(0);for(let e=0;e<n.length;++e){let r=n[e];if(sr(r.to,i.from)<0||sr(r.from,i.to)>0)continue;let o=[e,1],s=sr(r.from,i.from),l=sr(r.to,i.to);(s<0||!t.inclusiveLeft&&!s)&&o.push({from:r.from,to:i.from}),(l>0||!t.inclusiveRight&&!l)&&o.push({from:i.to,to:r.to}),n.splice.apply(n,o),e+=o.length-3}}return n}(e,t.from,t.to);if(r)for(let i=r.length-1;i>=0;--i)ml(e,{from:r[i].from,to:r[i].to,text:i?[""]:t.text,origin:t.origin});else ml(e,t)}function ml(e,t){if(1==t.text.length&&""==t.text[0]&&0==sr(t.from,t.to))return;let i=Rs(e,t);Vs(e,t,i,e.cm?e.cm.curOp.id:NaN),vl(e,t,i,Pr(e,t));let r=[];zs(e,((e,i)=>{i||-1!=qt(r,e.history)||(xl(e.history,t),r.push(e.history)),vl(e,t,null,Pr(e,t))}))}function fl(e,t,i){let r=e.cm&&e.cm.state.suppressEdits;if(r&&!i)return;let n,o=e.history,s=e.sel,l="undo"==t?o.done:o.undone,a="undo"==t?o.undone:o.done,c=0;for(;c<l.length&&(n=l[c],i?!n.ranges||n.equals(e.sel):n.ranges);c++);if(c==l.length)return;for(o.lastOrigin=o.lastSelOrigin=null;;){if(n=l.pop(),!n.ranges){if(r)return void l.push(n);break}if(js(n,a),i&&!n.equals(e.sel))return void rl(e,n,{clearRedo:!1});s=n}let d=[];js(s,a),a.push({changes:d,generation:o.generation}),o.generation=n.generation||++o.maxGeneration;let u=ki(e,"beforeChange")||e.cm&&ki(e.cm,"beforeChange");for(let i=n.changes.length-1;i>=0;--i){let r=n.changes[i];if(r.origin=t,u&&!hl(e,r,!1))return void(l.length=0);d.push(Hs(e,r));let o=i?Rs(e,r):ei(l);vl(e,r,o,Xs(e,r)),!i&&e.cm&&e.cm.scrollIntoView({from:r.from,to:Ls(r)});let s=[];zs(e,((e,t)=>{t||-1!=qt(s,e.history)||(xl(e.history,r),s.push(e.history)),vl(e,r,null,Xs(e,r))}))}}function gl(e,t){if(0!=t&&(e.first+=t,e.sel=new Ts(ti(e.sel.ranges,(e=>new Ms(or(e.anchor.line+t,e.anchor.ch),or(e.head.line+t,e.head.ch)))),e.sel.primIndex),e.cm)){vo(e.cm,e.first,e.first-t,t);for(let t=e.cm.display,i=t.viewFrom;i<t.viewTo;i++)bo(e.cm,i,"gutter")}}function vl(e,t,i,r){if(e.cm&&!e.cm.curOp)return ns(e.cm,vl)(e,t,i,r);if(t.to.line<e.first)return void gl(e,t.text.length-1-(t.to.line-t.from.line));if(t.from.line>e.lastLine())return;if(t.from.line<e.first){let i=t.text.length-1-(e.first-t.from.line);gl(e,i),t={from:or(e.first,0),to:or(t.to.line+i,t.to.ch),text:[ei(t.text)],origin:t.origin}}let n=e.lastLine();t.to.line>n&&(t={from:t.from,to:or(n,Zi(e,n).text.length),text:[t.text[0]],origin:t.origin}),t.removed=Ji(e,t.from,t.to),i||(i=Rs(e,t)),e.cm?function(e,t,i){let r=e.doc,n=e.display,o=t.from,s=t.to,l=!1,a=o.line;e.options.lineWrapping||(a=tr(Ur(Zi(r,o.line))),r.iter(a,s.line+1,(e=>{if(e==n.maxLine)return l=!0,!0})));r.sel.contains(t.from,t.to)>-1&&wi(e);$s(r,t,i,po(e)),e.options.lineWrapping||(r.iter(a,o.line+t.text.length,(e=>{let t=Xr(e);t>n.maxLineLength&&(n.maxLine=e,n.maxLineLength=t,n.maxLineChanged=!0,l=!1)})),l&&(e.curOp.updateMaxLine=!0));(function(e,t){if(e.modeFrontier=Math.min(e.modeFrontier,t),e.highlightFrontier<t-10)return;let i=e.first;for(let r=t-1;r>i;r--){let n=Zi(e,r).stateAfter;if(n&&(!(n instanceof mr)||r+n.lookAhead<t)){i=r+1;break}}e.highlightFrontier=Math.min(e.highlightFrontier,i)})(r,o.line),ls(e,400);let c=t.text.length-(s.line-o.line)-1;t.full?vo(e):o.line!=s.line||1!=t.text.length||Os(e.doc,t)?vo(e,o.line,s.line+1,c):bo(e,o.line,"text");let d=ki(e,"changes"),u=ki(e,"change");if(u||d){let i={from:o,to:s,text:t.text,removed:t.removed,origin:t.origin};u&&pn(e,"change",e,i),d&&(e.curOp.changeObjs||(e.curOp.changeObjs=[])).push(i)}e.display.selForContextMenu=null}(e.cm,t,r):$s(e,t,r),nl(e,i,Kt),e.cantEdit&&cl(e,or(e.firstLine(),0))&&(e.cantEdit=!1)}function bl(e,t,i,r,n){r||(r=i),sr(r,i)<0&&([i,r]=[r,i]),"string"==typeof t&&(t=e.splitLines(t)),pl(e,{from:i,to:r,text:t,origin:n})}function yl(e,t,i,r){i<e.line?e.line+=r:t<e.line&&(e.line=t,e.ch=0)}function _l(e,t,i,r){for(let n=0;n<e.length;++n){let o=e[n],s=!0;if(o.ranges){o.copied||(o=e[n]=o.deepCopy(),o.copied=!0);for(let e=0;e<o.ranges.length;e++)yl(o.ranges[e].anchor,t,i,r),yl(o.ranges[e].head,t,i,r)}else{for(let e=0;e<o.changes.length;++e){let n=o.changes[e];if(i<n.from.line)n.from=or(n.from.line+r,n.from.ch),n.to=or(n.to.line+r,n.to.ch);else if(t<=n.to.line){s=!1;break}}s||(e.splice(0,n+1),n=0)}}}function xl(e,t){let i=t.from.line,r=t.to.line,n=t.text.length-(r-i)-1;_l(e.done,i,r,n),_l(e.undone,i,r,n)}function wl(e,t,i,r){let n=t,o=t;return"number"==typeof t?o=Zi(e,ur(e,t)):n=tr(t),null==n?null:(r(o,n)&&e.cm&&bo(e.cm,n,i),o)}function kl(e){this.lines=e,this.parent=null;let t=0;for(let i=0;i<e.length;++i)e[i].parent=this,t+=e[i].height;this.height=t}function Sl(e){this.children=e;let t=0,i=0;for(let r=0;r<e.length;++r){let n=e[r];t+=n.chunkSize(),i+=n.height,n.parent=this}this.size=t,this.height=i,this.parent=null}kl.prototype={chunkSize(){return this.lines.length},removeInner(e,t){for(let i=e,r=e+t;i<r;++i){let e=this.lines[i];this.height-=e.height,Jr(e),pn(e,"delete")}this.lines.splice(e,t)},collapse(e){e.push.apply(e,this.lines)},insertInner(e,t,i){this.height+=i,this.lines=this.lines.slice(0,e).concat(t).concat(this.lines.slice(e));for(let e=0;e<t.length;++e)t[e].parent=this},iterN(e,t,i){for(let r=e+t;e<r;++e)if(i(this.lines[e]))return!0}},Sl.prototype={chunkSize(){return this.size},removeInner(e,t){this.size-=t;for(let i=0;i<this.children.length;++i){let r=this.children[i],n=r.chunkSize();if(e<n){let o=Math.min(t,n-e),s=r.height;if(r.removeInner(e,o),this.height-=s-r.height,n==o&&(this.children.splice(i--,1),r.parent=null),0==(t-=o))break;e=0}else e-=n}if(this.size-t<25&&(this.children.length>1||!(this.children[0]instanceof kl))){let e=[];this.collapse(e),this.children=[new kl(e)],this.children[0].parent=this}},collapse(e){for(let t=0;t<this.children.length;++t)this.children[t].collapse(e)},insertInner(e,t,i){this.size+=t.length,this.height+=i;for(let r=0;r<this.children.length;++r){let n=this.children[r],o=n.chunkSize();if(e<=o){if(n.insertInner(e,t,i),n.lines&&n.lines.length>50){let e=n.lines.length%25+25;for(let t=e;t<n.lines.length;){let e=new kl(n.lines.slice(t,t+=25));n.height-=e.height,this.children.splice(++r,0,e),e.parent=this}n.lines=n.lines.slice(0,e),this.maybeSpill()}break}e-=o}},maybeSpill(){if(this.children.length<=10)return;let e=this;do{let t=new Sl(e.children.splice(e.children.length-5,5));if(e.parent){e.size-=t.size,e.height-=t.height;let i=qt(e.parent.children,e);e.parent.children.splice(i+1,0,t)}else{let i=new Sl(e.children);i.parent=e,e.children=[i,t],e=i}t.parent=e.parent}while(e.children.length>10);e.parent.maybeSpill()},iterN(e,t,i){for(let r=0;r<this.children.length;++r){let n=this.children[r],o=n.chunkSize();if(e<o){let r=Math.min(t,o-e);if(n.iterN(e,r,i))return!0;if(0==(t-=r))break;e=0}else e-=o}}};var Cl=class{constructor(e,t,i){if(i)for(let e in i)i.hasOwnProperty(e)&&(this[e]=i[e]);this.doc=e,this.node=t}clear(){let e=this.doc.cm,t=this.line.widgets,i=this.line,r=tr(i);if(null==r||!t)return;for(let e=0;e<t.length;++e)t[e]==this&&t.splice(e--,1);t.length||(i.widgets=null);let n=Tn(this);er(i,Math.max(0,i.height-n)),e&&(rs(e,(()=>{Tl(e,i,-n),bo(e,r,"widget")})),pn(e,"lineWidgetCleared",e,this,r))}changed(){let e=this.height,t=this.doc.cm,i=this.line;this.height=null;let r=Tn(this)-e;r&&(jr(this.doc,i)||er(i,i.height+r),t&&rs(t,(()=>{t.curOp.forceUpdate=!0,Tl(t,i,r),pn(t,"lineWidgetChanged",t,this,tr(i))})))}};function Tl(e,t,i){Kr(t)<(e.curOp&&e.curOp.scrollTop||e.doc.scrollTop)&&Oo(e,i)}Si(Cl);var Ml=0,El=class{constructor(e,t){this.lines=[],this.type=t,this.doc=e,this.id=++Ml}clear(){if(this.explicitlyCleared)return;let e=this.doc.cm,t=e&&!e.curOp;if(t&&Yo(e),ki(this,"clear")){let e=this.find();e&&pn(this,"clear",e.from,e.to)}let i=null,r=null;for(let t=0;t<this.lines.length;++t){let n=this.lines[t],o=Ar(n.markedSpans,this);e&&!this.collapsed?bo(e,tr(n),"text"):e&&(null!=o.to&&(r=tr(n)),null!=o.from&&(i=tr(n))),n.markedSpans=Lr(n.markedSpans,o),null==o.from&&this.collapsed&&!jr(this.doc,n)&&e&&er(n,ao(e.display))}if(e&&this.collapsed&&!e.options.lineWrapping)for(let t=0;t<this.lines.length;++t){let i=Ur(this.lines[t]),r=Xr(i);r>e.display.maxLineLength&&(e.display.maxLine=i,e.display.maxLineLength=r,e.display.maxLineChanged=!0)}null!=i&&e&&this.collapsed&&vo(e,i,r+1),this.lines.length=0,this.explicitlyCleared=!0,this.atomic&&this.doc.cantEdit&&(this.doc.cantEdit=!1,e&&sl(e.doc)),e&&pn(e,"markerCleared",e,this,i,r),t&&Zo(e),this.parent&&this.parent.clear()}find(e,t){let i,r;null==e&&"bookmark"==this.type&&(e=1);for(let n=0;n<this.lines.length;++n){let o=this.lines[n],s=Ar(o.markedSpans,this);if(null!=s.from&&(i=or(t?o:tr(o),s.from),-1==e))return i;if(null!=s.to&&(r=or(t?o:tr(o),s.to),1==e))return r}return i&&{from:i,to:r}}changed(){let e=this.find(-1,!0),t=this,i=this.doc.cm;e&&i&&rs(i,(()=>{let r=e.line,n=tr(e.line),o=On(i,n);if(o&&(Un(o),i.curOp.selectionChanged=i.curOp.forceUpdate=!0),i.curOp.updateMaxLine=!0,!jr(t.doc,r)&&null!=t.height){let e=t.height;t.height=null;let i=Tn(t)-e;i&&er(r,r.height+i)}pn(i,"markerChanged",i,this)}))}attachLine(e){if(!this.lines.length&&this.doc.cm){let e=this.doc.cm.curOp;e.maybeHiddenMarkers&&-1!=qt(e.maybeHiddenMarkers,this)||(e.maybeUnhiddenMarkers||(e.maybeUnhiddenMarkers=[])).push(this)}this.lines.push(e)}detachLine(e){if(this.lines.splice(qt(this.lines,e),1),!this.lines.length&&this.doc.cm){let e=this.doc.cm.curOp;(e.maybeHiddenMarkers||(e.maybeHiddenMarkers=[])).push(this)}}};function Al(e,t,i,r,n){if(r&&r.shared)return function(e,t,i,r,n){r=Ht(r),r.shared=!1;let o=[Al(e,t,i,r,n)],s=o[0],l=r.widgetNode;return zs(e,(e=>{l&&(r.widgetNode=l.cloneNode(!0)),o.push(Al(e,hr(e,t),hr(e,i),r,n));for(let t=0;t<e.linked.length;++t)if(e.linked[t].isParent)return;s=ei(o)})),new Ll(o,s)}(e,t,i,r,n);if(e.cm&&!e.cm.curOp)return ns(e.cm,Al)(e,t,i,r,n);let o=new El(e,n),s=sr(t,i);if(r&&Ht(r,o,!1),s>0||0==s&&!1!==o.clearWhenEmpty)return o;if(o.replacedWith&&(o.collapsed=!0,o.widgetNode=Dt("span",[o.replacedWith],"CodeMirror-widget"),r.handleMouseEvents||o.widgetNode.setAttribute("cm-ignore-events","true"),r.insertLeft&&(o.widgetNode.insertLeft=!0)),o.collapsed){if(Hr(e,t.line,t,i,o)||t.line!=i.line&&Hr(e,i.line,t,i,o))throw new Error("Inserting collapsed marker partially overlapping an existing one");Mr=!0}o.addToHistory&&Vs(e,{from:t,to:i,origin:"markText"},e.sel,NaN);let l,a=t.line,c=e.cm;if(e.iter(a,i.line+1,(e=>{c&&o.collapsed&&!c.options.lineWrapping&&Ur(e)==c.display.maxLine&&(l=!0),o.collapsed&&a!=t.line&&er(e,0),function(e,t){e.markedSpans=e.markedSpans?e.markedSpans.concat([t]):[t],t.marker.attachLine(e)}(e,new Er(o,a==t.line?t.ch:null,a==i.line?i.ch:null)),++a})),o.collapsed&&e.iter(t.line,i.line+1,(t=>{jr(e,t)&&er(t,0)})),o.clearOnEnter&&vi(o,"beforeCursorEnter",(()=>o.clear())),o.readOnly&&(Tr=!0,(e.history.done.length||e.history.undone.length)&&e.clearHistory()),o.collapsed&&(o.id=++Ml,o.atomic=!0),c){if(l&&(c.curOp.updateMaxLine=!0),o.collapsed)vo(c,t.line,i.line+1);else if(o.className||o.startStyle||o.endStyle||o.css||o.attributes||o.title)for(let e=t.line;e<=i.line;e++)bo(c,e,"text");o.atomic&&sl(c.doc),pn(c,"markerAdded",c,o)}return o}Si(El);var Ll=class{constructor(e,t){this.markers=e,this.primary=t;for(let t=0;t<e.length;++t)e[t].parent=this}clear(){if(!this.explicitlyCleared){this.explicitlyCleared=!0;for(let e=0;e<this.markers.length;++e)this.markers[e].clear();pn(this,"clear")}}find(e,t){return this.primary.find(e,t)}};function Pl(e){return e.findMarks(or(e.first,0),e.clipPos(or(e.lastLine())),(e=>e.parent))}function Rl(e){for(let t=0;t<e.length;t++){let i=e[t],r=[i.primary.doc];zs(i.primary.doc,(e=>r.push(e)));for(let e=0;e<i.markers.length;e++){let t=i.markers[e];-1==qt(r,t.doc)&&(t.parent=null,i.markers.splice(e--,1))}}}Si(Ll);var Nl=0,Il=function(e,t,i,r,n){if(!(this instanceof Il))return new Il(e,t,i,r,n);null==i&&(i=0),Sl.call(this,[new kl([new Zr("",null)])]),this.first=i,this.scrollTop=this.scrollLeft=0,this.cantEdit=!1,this.cleanGeneration=1,this.modeFrontier=this.highlightFrontier=i;let o=or(i,0);this.sel=As(o),this.history=new Ws(null),this.id=++Nl,this.modeOption=t,this.lineSep=r,this.direction="rtl"==n?"rtl":"ltr",this.extend=!1,"string"==typeof e&&(e=this.splitLines(e)),$s(this,{from:o,to:o,text:e}),rl(this,As(o),Kt)};Il.prototype=ri(Sl.prototype,{constructor:Il,iter:function(e,t,i){i?this.iterN(e-this.first,t-e,i):this.iterN(this.first,this.first+this.size,e)},insert:function(e,t){let i=0;for(let e=0;e<t.length;++e)i+=t[e].height;this.insertInner(e-this.first,t,i)},remove:function(e,t){this.removeInner(e-this.first,t)},getValue:function(e){let t=Qi(this,this.first,this.first+this.size);return!1===e?t:t.join(e||this.lineSeparator())},setValue:ss((function(e){let t=or(this.first,0),i=this.first+this.size-1;pl(this,{from:t,to:or(i,Zi(this,i).text.length),text:this.splitLines(e),origin:"setValue",full:!0},!0),this.cm&&zo(this.cm,0,0),rl(this,As(t),Kt)})),replaceRange:function(e,t,i,r){bl(this,e,t=hr(this,t),i=i?hr(this,i):t,r)},getRange:function(e,t,i){let r=Ji(this,hr(this,e),hr(this,t));return!1===i?r:r.join(i||this.lineSeparator())},getLine:function(e){let t=this.getLineHandle(e);return t&&t.text},getLineHandle:function(e){if(rr(this,e))return Zi(this,e)},getLineNumber:function(e){return tr(e)},getLineHandleVisualStart:function(e){return"number"==typeof e&&(e=Zi(this,e)),Ur(e)},lineCount:function(){return this.size},firstLine:function(){return this.first},lastLine:function(){return this.first+this.size-1},clipPos:function(e){return hr(this,e)},getCursor:function(e){let t,i=this.sel.primary();return t=null==e||"head"==e?i.head:"anchor"==e?i.anchor:"end"==e||"to"==e||!1===e?i.to():i.from(),t},listSelections:function(){return this.sel.ranges},somethingSelected:function(){return this.sel.somethingSelected()},setCursor:ss((function(e,t,i){tl(this,hr(this,"number"==typeof e?or(e,t||0):e),null,i)})),setSelection:ss((function(e,t,i){tl(this,hr(this,e),hr(this,t||e),i)})),extendSelection:ss((function(e,t,i){Js(this,hr(this,e),t&&hr(this,t),i)})),extendSelections:ss((function(e,t){Qs(this,pr(this,e),t)})),extendSelectionsBy:ss((function(e,t){Qs(this,pr(this,ti(this.sel.ranges,e)),t)})),setSelections:ss((function(e,t,i){if(!e.length)return;let r=[];for(let t=0;t<e.length;t++)r[t]=new Ms(hr(this,e[t].anchor),hr(this,e[t].head||e[t].anchor));null==t&&(t=Math.min(e.length-1,this.sel.primIndex)),rl(this,Es(this.cm,r,t),i)})),addSelection:ss((function(e,t,i){let r=this.sel.ranges.slice(0);r.push(new Ms(hr(this,e),hr(this,t||e))),rl(this,Es(this.cm,r,r.length-1),i)})),getSelection:function(e){let t,i=this.sel.ranges;for(let e=0;e<i.length;e++){let r=Ji(this,i[e].from(),i[e].to());t=t?t.concat(r):r}return!1===e?t:t.join(e||this.lineSeparator())},getSelections:function(e){let t=[],i=this.sel.ranges;for(let r=0;r<i.length;r++){let n=Ji(this,i[r].from(),i[r].to());!1!==e&&(n=n.join(e||this.lineSeparator())),t[r]=n}return t},replaceSelection:function(e,t,i){let r=[];for(let t=0;t<this.sel.ranges.length;t++)r[t]=e;this.replaceSelections(r,t,i||"+input")},replaceSelections:ss((function(e,t,i){let r=[],n=this.sel;for(let t=0;t<n.ranges.length;t++){let o=n.ranges[t];r[t]={from:o.from(),to:o.to(),text:this.splitLines(e[t]),origin:i}}let o=t&&"end"!=t&&function(e,t,i){let r=[],n=or(e.first,0),o=n;for(let s=0;s<t.length;s++){let l=t[s],a=Ns(l.from,n,o),c=Ns(Ls(l),n,o);if(n=l.to,o=c,"around"==i){let t=e.sel.ranges[s],i=sr(t.head,t.anchor)<0;r[s]=new Ms(i?c:a,i?a:c)}else r[s]=new Ms(a,a)}return new Ts(r,e.sel.primIndex)}(this,r,t);for(let e=r.length-1;e>=0;e--)pl(this,r[e]);o?il(this,o):this.cm&&$o(this.cm)})),undo:ss((function(){fl(this,"undo")})),redo:ss((function(){fl(this,"redo")})),undoSelection:ss((function(){fl(this,"undo",!0)})),redoSelection:ss((function(){fl(this,"redo",!0)})),setExtending:function(e){this.extend=e},getExtending:function(){return this.extend},historySize:function(){let e=this.history,t=0,i=0;for(let i=0;i<e.done.length;i++)e.done[i].ranges||++t;for(let t=0;t<e.undone.length;t++)e.undone[t].ranges||++i;return{undo:t,redo:i}},clearHistory:function(){this.history=new Ws(this.history),zs(this,(e=>e.history=this.history),!0)},markClean:function(){this.cleanGeneration=this.changeGeneration(!0)},changeGeneration:function(e){return e&&(this.history.lastOp=this.history.lastSelOp=this.history.lastOrigin=null),this.history.generation},isClean:function(e){return this.history.generation==(e||this.cleanGeneration)},getHistory:function(){return{done:Ys(this.history.done),undone:Ys(this.history.undone)}},setHistory:function(e){let t=this.history=new Ws(this.history);t.done=Ys(e.done.slice(0),null,!0),t.undone=Ys(e.undone.slice(0),null,!0)},setGutterMarker:ss((function(e,t,i){return wl(this,e,"gutter",(e=>{let r=e.gutterMarkers||(e.gutterMarkers={});return r[t]=i,!i&&li(r)&&(e.gutterMarkers=null),!0}))})),clearGutter:ss((function(e){this.iter((t=>{t.gutterMarkers&&t.gutterMarkers[e]&&wl(this,t,"gutter",(()=>(t.gutterMarkers[e]=null,li(t.gutterMarkers)&&(t.gutterMarkers=null),!0)))}))})),lineInfo:function(e){let t;if("number"==typeof e){if(!rr(this,e))return null;if(t=e,!(e=Zi(this,e)))return null}else if(t=tr(e),null==t)return null;return{line:t,handle:e,text:e.text,gutterMarkers:e.gutterMarkers,textClass:e.textClass,bgClass:e.bgClass,wrapClass:e.wrapClass,widgets:e.widgets}},addLineClass:ss((function(e,t,i){return wl(this,e,"gutter"==t?"gutter":"class",(e=>{let r="text"==t?"textClass":"background"==t?"bgClass":"gutter"==t?"gutterClass":"wrapClass";if(e[r]){if(At(i).test(e[r]))return!1;e[r]+=" "+i}else e[r]=i;return!0}))})),removeLineClass:ss((function(e,t,i){return wl(this,e,"gutter"==t?"gutter":"class",(e=>{let r="text"==t?"textClass":"background"==t?"bgClass":"gutter"==t?"gutterClass":"wrapClass",n=e[r];if(!n)return!1;if(null==i)e[r]=null;else{let t=n.match(At(i));if(!t)return!1;let o=t.index+t[0].length;e[r]=n.slice(0,t.index)+(t.index&&o!=n.length?" ":"")+n.slice(o)||null}return!0}))})),addLineWidget:ss((function(e,t,i){return function(e,t,i,r){let n=new Cl(e,i,r),o=e.cm;return o&&n.noHScroll&&(o.display.alignWidgets=!0),wl(e,t,"widget",(t=>{let i=t.widgets||(t.widgets=[]);if(null==n.insertAt?i.push(n):i.splice(Math.min(i.length,Math.max(0,n.insertAt)),0,n),n.line=t,o&&!jr(e,t)){let i=Kr(t)<e.scrollTop;er(t,t.height+Tn(n)),i&&Oo(o,n.height),o.curOp.forceUpdate=!0}return!0})),o&&pn(o,"lineWidgetAdded",o,n,"number"==typeof t?t:tr(t)),n}(this,e,t,i)})),removeLineWidget:function(e){e.clear()},markText:function(e,t,i){return Al(this,hr(this,e),hr(this,t),i,i&&i.type||"range")},setBookmark:function(e,t){let i={replacedWith:t&&(null==t.nodeType?t.widget:t),insertLeft:t&&t.insertLeft,clearWhenEmpty:!1,shared:t&&t.shared,handleMouseEvents:t&&t.handleMouseEvents};return Al(this,e=hr(this,e),e,i,"bookmark")},findMarksAt:function(e){let t=[],i=Zi(this,(e=hr(this,e)).line).markedSpans;if(i)for(let r=0;r<i.length;++r){let n=i[r];(null==n.from||n.from<=e.ch)&&(null==n.to||n.to>=e.ch)&&t.push(n.marker.parent||n.marker)}return t},findMarks:function(e,t,i){e=hr(this,e),t=hr(this,t);let r=[],n=e.line;return this.iter(e.line,t.line+1,(o=>{let s=o.markedSpans;if(s)for(let o=0;o<s.length;o++){let l=s[o];null!=l.to&&n==e.line&&e.ch>=l.to||null==l.from&&n!=e.line||null!=l.from&&n==t.line&&l.from>=t.ch||i&&!i(l.marker)||r.push(l.marker.parent||l.marker)}++n})),r},getAllMarks:function(){let e=[];return this.iter((t=>{let i=t.markedSpans;if(i)for(let t=0;t<i.length;++t)null!=i[t].from&&e.push(i[t].marker)})),e},posFromIndex:function(e){let t,i=this.first,r=this.lineSeparator().length;return this.iter((n=>{let o=n.text.length+r;if(o>e)return t=e,!0;e-=o,++i})),hr(this,or(i,t))},indexFromPos:function(e){let t=(e=hr(this,e)).ch;if(e.line<this.first||e.ch<0)return 0;let i=this.lineSeparator().length;return this.iter(this.first,e.line,(e=>{t+=e.text.length+i})),t},copy:function(e){let t=new Il(Qi(this,this.first,this.first+this.size),this.modeOption,this.first,this.lineSep,this.direction);return t.scrollTop=this.scrollTop,t.scrollLeft=this.scrollLeft,t.sel=this.sel,t.extend=!1,e&&(t.history.undoDepth=this.history.undoDepth,t.setHistory(this.getHistory())),t},linkedDoc:function(e){e||(e={});let t=this.first,i=this.first+this.size;null!=e.from&&e.from>t&&(t=e.from),null!=e.to&&e.to<i&&(i=e.to);let r=new Il(Qi(this,t,i),e.mode||this.modeOption,t,this.lineSep,this.direction);return e.sharedHist&&(r.history=this.history),(this.linked||(this.linked=[])).push({doc:r,sharedHist:e.sharedHist}),r.linked=[{doc:this,isParent:!0,sharedHist:e.sharedHist}],function(e,t){for(let i=0;i<t.length;i++){let r=t[i],n=r.find(),o=e.clipPos(n.from),s=e.clipPos(n.to);if(sr(o,s)){let t=Al(e,o,s,r.primary,r.primary.type);r.markers.push(t),t.parent=r}}}(r,Pl(this)),r},unlinkDoc:function(e){if(e instanceof Aa&&(e=e.doc),this.linked)for(let t=0;t<this.linked.length;++t){if(this.linked[t].doc==e){this.linked.splice(t,1),e.unlinkDoc(this),Rl(Pl(this));break}}if(e.history==this.history){let t=[e.id];zs(e,(e=>t.push(e.id)),!0),e.history=new Ws(null),e.history.done=Ys(this.history.done,t),e.history.undone=Ys(this.history.undone,t)}},iterLinkedDocs:function(e){zs(this,e)},getMode:function(){return this.mode},getEditor:function(){return this.cm},splitLines:function(e){return this.lineSep?e.split(this.lineSep):Oi(e)},lineSeparator:function(){return this.lineSep||"\n"},setDirection:ss((function(e){var t;("rtl"!=e&&(e="ltr"),e!=this.direction)&&(this.direction=e,this.iter((e=>e.order=null)),this.cm&&rs(t=this.cm,(()=>{Bs(t),vo(t)})))}))}),Il.prototype.eachLine=Il.prototype.iter;var Dl=Il,Ol=0;function $l(e){let t=this;if(zl(t),xi(t,e)||Mn(t.display,e))return;Ci(e),ut&&(Ol=+new Date);let i=fo(t,e,!0),r=e.dataTransfer.files;if(i&&!t.isReadOnly())if(r&&r.length&&window.FileReader&&window.File){let e=r.length,n=Array(e),o=0;const s=()=>{++o==e&&ns(t,(()=>{i=hr(t.doc,i);let e={from:i,to:i,text:t.doc.splitLines(n.filter((e=>null!=e)).join(t.doc.lineSeparator())),origin:"paste"};pl(t.doc,e),il(t.doc,As(hr(t.doc,i),hr(t.doc,Ls(e))))}))()},l=(e,i)=>{if(t.options.allowDropFileTypes&&-1==qt(t.options.allowDropFileTypes,e.type))return void s();let r=new FileReader;r.onerror=()=>s(),r.onload=()=>{let e=r.result;/[\x00-\x08\x0e-\x1f]{2}/.test(e)||(n[i]=e),s()},r.readAsText(e)};for(let e=0;e<r.length;e++)l(r[e],e)}else{if(t.state.draggingText&&t.doc.sel.contains(i)>-1)return t.state.draggingText(e),void setTimeout((()=>t.display.input.focus()),20);try{let r=e.dataTransfer.getData("Text");if(r){let e;if(t.state.draggingText&&!t.state.draggingText.copy&&(e=t.listSelections()),nl(t.doc,As(i,i)),e)for(let i=0;i<e.length;++i)bl(t.doc,"",e[i].anchor,e[i].head,"drag");t.replaceSelection(r,"around","paste"),t.display.input.focus()}}catch(e){}}}function zl(e){e.display.dragCursor&&(e.display.lineSpace.removeChild(e.display.dragCursor),e.display.dragCursor=null)}function Fl(e){if(!document.getElementsByClassName)return;let t=document.getElementsByClassName("CodeMirror"),i=[];for(let e=0;e<t.length;e++){let r=t[e].CodeMirror;r&&i.push(r)}i.length&&i[0].operation((()=>{for(let t=0;t<i.length;t++)e(i[t])}))}var Bl=!1;function Wl(){Bl||(!function(){let e;vi(window,"resize",(()=>{null==e&&(e=setTimeout((()=>{e=null,Fl(Hl)}),100))})),vi(window,"blur",(()=>Fl(Po)))}(),Bl=!0)}function Hl(e){let t=e.display;t.cachedCharWidth=t.cachedTextHeight=t.cachedPaddingH=null,t.scrollbarsClipped=!1,e.setSize()}var Ul={3:"Pause",8:"Backspace",9:"Tab",13:"Enter",16:"Shift",17:"Ctrl",18:"Alt",19:"Pause",20:"CapsLock",27:"Esc",32:"Space",33:"PageUp",34:"PageDown",35:"End",36:"Home",37:"Left",38:"Up",39:"Right",40:"Down",44:"PrintScrn",45:"Insert",46:"Delete",59:";",61:"=",91:"Mod",92:"Mod",93:"Mod",106:"*",107:"=",109:"-",110:".",111:"/",145:"ScrollLock",173:"-",186:";",187:"=",188:",",189:"-",190:".",191:"/",192:"`",219:"[",220:"\\",221:"]",222:"'",224:"Mod",63232:"Up",63233:"Down",63234:"Left",63235:"Right",63272:"Delete",63273:"Home",63275:"End",63276:"PageUp",63277:"PageDown",63302:"Insert"};for(let e=0;e<10;e++)Ul[e+48]=Ul[e+96]=String(e);for(let e=65;e<=90;e++)Ul[e]=String.fromCharCode(e);for(let e=1;e<=12;e++)Ul[e+111]=Ul[e+63235]="F"+e;var Vl={};function ql(e){let t,i,r,n,o=e.split(/-(?!$)/);e=o[o.length-1];for(let e=0;e<o.length-1;e++){let s=o[e];if(/^(cmd|meta|m)$/i.test(s))n=!0;else if(/^a(lt)?$/i.test(s))t=!0;else if(/^(c|ctrl|control)$/i.test(s))i=!0;else{if(!/^s(hift)?$/i.test(s))throw new Error("Unrecognized modifier name: "+s);r=!0}}return t&&(e="Alt-"+e),i&&(e="Ctrl-"+e),n&&(e="Cmd-"+e),r&&(e="Shift-"+e),e}function jl(e){let t={};for(let i in e)if(e.hasOwnProperty(i)){let r=e[i];if(/^(name|fallthrough|(de|at)tach)$/.test(i))continue;if("..."==r){delete e[i];continue}let n=ti(i.split(" "),ql);for(let e=0;e<n.length;e++){let i,o;e==n.length-1?(o=n.join(" "),i=r):(o=n.slice(0,e+1).join(" "),i="...");let s=t[o];if(s){if(s!=i)throw new Error("Inconsistent bindings for "+o)}else t[o]=i}delete e[i]}for(let i in t)e[i]=t[i];return e}function Gl(e,t,i,r){let n=(t=Zl(t)).call?t.call(e,r):t[e];if(!1===n)return"nothing";if("..."===n)return"multi";if(null!=n&&i(n))return"handled";if(t.fallthrough){if("[object Array]"!=Object.prototype.toString.call(t.fallthrough))return Gl(e,t.fallthrough,i,r);for(let n=0;n<t.fallthrough.length;n++){let o=Gl(e,t.fallthrough[n],i,r);if(o)return o}}}function Kl(e){let t="string"==typeof e?e:Ul[e.keyCode];return"Ctrl"==t||"Alt"==t||"Shift"==t||"Mod"==t}function Xl(e,t,i){let r=e;return t.altKey&&"Alt"!=r&&(e="Alt-"+e),(Mt?t.metaKey:t.ctrlKey)&&"Ctrl"!=r&&(e="Ctrl-"+e),(Mt?t.ctrlKey:t.metaKey)&&"Mod"!=r&&(e="Cmd-"+e),!i&&t.shiftKey&&"Shift"!=r&&(e="Shift-"+e),e}function Yl(e,t){if(gt&&34==e.keyCode&&e.char)return!1;let i=Ul[e.keyCode];return null!=i&&!e.altGraphKey&&(3==e.keyCode&&e.code&&(i=e.code),Xl(i,e,t))}function Zl(e){return"string"==typeof e?Vl[e]:e}function Jl(e,t){let i=e.doc.sel.ranges,r=[];for(let e=0;e<i.length;e++){let n=t(i[e]);for(;r.length&&sr(n.from,ei(r).to)<=0;){let e=r.pop();if(sr(e.from,n.from)<0){n.from=e.from;break}}r.push(n)}rs(e,(()=>{for(let t=r.length-1;t>=0;t--)bl(e.doc,"",r[t].from,r[t].to,"+delete");$o(e)}))}function Ql(e,t,i){let r=di(e.text,t+i,i);return r<0||r>e.text.length?null:r}function ea(e,t,i){let r=Ql(e,t.ch,i);return null==r?null:new or(t.line,r,i<0?"after":"before")}function ta(e,t,i,r,n){if(e){"rtl"==t.doc.direction&&(n=-n);let e=fi(i,t.doc.direction);if(e){let o,s=n<0?ei(e):e[0],l=n<0==(1==s.level)?"after":"before";if(s.level>0||"rtl"==t.doc.direction){let e=$n(t,i);o=n<0?i.text.length-1:0;let r=zn(t,e,o).top;o=ui((i=>zn(t,e,i).top==r),n<0==(1==s.level)?s.from:s.to-1,o),"before"==l&&(o=Ql(i,o,1))}else o=n<0?s.to:s.from;return new or(r,o,l)}}return new or(r,n<0?i.text.length:0,n<0?"before":"after")}Vl.basic={Left:"goCharLeft",Right:"goCharRight",Up:"goLineUp",Down:"goLineDown",End:"goLineEnd",Home:"goLineStartSmart",PageUp:"goPageUp",PageDown:"goPageDown",Delete:"delCharAfter",Backspace:"delCharBefore","Shift-Backspace":"delCharBefore",Tab:"defaultTab","Shift-Tab":"indentAuto",Enter:"newlineAndIndent",Insert:"toggleOverwrite",Esc:"singleSelection"},Vl.pcDefault={"Ctrl-A":"selectAll","Ctrl-D":"deleteLine","Ctrl-Z":"undo","Shift-Ctrl-Z":"redo","Ctrl-Y":"redo","Ctrl-Home":"goDocStart","Ctrl-End":"goDocEnd","Ctrl-Up":"goLineUp","Ctrl-Down":"goLineDown","Ctrl-Left":"goGroupLeft","Ctrl-Right":"goGroupRight","Alt-Left":"goLineStart","Alt-Right":"goLineEnd","Ctrl-Backspace":"delGroupBefore","Ctrl-Delete":"delGroupAfter","Ctrl-S":"save","Ctrl-F":"find","Ctrl-G":"findNext","Shift-Ctrl-G":"findPrev","Shift-Ctrl-F":"replace","Shift-Ctrl-R":"replaceAll","Ctrl-[":"indentLess","Ctrl-]":"indentMore","Ctrl-U":"undoSelection","Shift-Ctrl-U":"redoSelection","Alt-U":"redoSelection",fallthrough:"basic"},Vl.emacsy={"Ctrl-F":"goCharRight","Ctrl-B":"goCharLeft","Ctrl-P":"goLineUp","Ctrl-N":"goLineDown","Ctrl-A":"goLineStart","Ctrl-E":"goLineEnd","Ctrl-V":"goPageDown","Shift-Ctrl-V":"goPageUp","Ctrl-D":"delCharAfter","Ctrl-H":"delCharBefore","Alt-Backspace":"delWordBefore","Ctrl-K":"killLine","Ctrl-T":"transposeChars","Ctrl-O":"openLine"},Vl.macDefault={"Cmd-A":"selectAll","Cmd-D":"deleteLine","Cmd-Z":"undo","Shift-Cmd-Z":"redo","Cmd-Y":"redo","Cmd-Home":"goDocStart","Cmd-Up":"goDocStart","Cmd-End":"goDocEnd","Cmd-Down":"goDocEnd","Alt-Left":"goGroupLeft","Alt-Right":"goGroupRight","Cmd-Left":"goLineLeft","Cmd-Right":"goLineRight","Alt-Backspace":"delGroupBefore","Ctrl-Alt-Backspace":"delGroupAfter","Alt-Delete":"delGroupAfter","Cmd-S":"save","Cmd-F":"find","Cmd-G":"findNext","Shift-Cmd-G":"findPrev","Cmd-Alt-F":"replace","Shift-Cmd-Alt-F":"replaceAll","Cmd-[":"indentLess","Cmd-]":"indentMore","Cmd-Backspace":"delWrappedLineLeft","Cmd-Delete":"delWrappedLineRight","Cmd-U":"undoSelection","Shift-Cmd-U":"redoSelection","Ctrl-Up":"goDocStart","Ctrl-Down":"goDocEnd",fallthrough:["basic","emacsy"]},Vl.default=kt?Vl.macDefault:Vl.pcDefault;var ia={selectAll:ul,singleSelection:e=>e.setSelection(e.getCursor("anchor"),e.getCursor("head"),Kt),killLine:e=>Jl(e,(t=>{if(t.empty()){let i=Zi(e.doc,t.head.line).text.length;return t.head.ch==i&&t.head.line<e.lastLine()?{from:t.head,to:or(t.head.line+1,0)}:{from:t.head,to:or(t.head.line,i)}}return{from:t.from(),to:t.to()}})),deleteLine:e=>Jl(e,(t=>({from:or(t.from().line,0),to:hr(e.doc,or(t.to().line+1,0))}))),delLineLeft:e=>Jl(e,(e=>({from:or(e.from().line,0),to:e.from()}))),delWrappedLineLeft:e=>Jl(e,(t=>{let i=e.charCoords(t.head,"div").top+5;return{from:e.coordsChar({left:0,top:i},"div"),to:t.from()}})),delWrappedLineRight:e=>Jl(e,(t=>{let i=e.charCoords(t.head,"div").top+5,r=e.coordsChar({left:e.display.lineDiv.offsetWidth+100,top:i},"div");return{from:t.from(),to:r}})),undo:e=>e.undo(),redo:e=>e.redo(),undoSelection:e=>e.undoSelection(),redoSelection:e=>e.redoSelection(),goDocStart:e=>e.extendSelection(or(e.firstLine(),0)),goDocEnd:e=>e.extendSelection(or(e.lastLine())),goLineStart:e=>e.extendSelectionsBy((t=>ra(e,t.head.line)),{origin:"+move",bias:1}),goLineStartSmart:e=>e.extendSelectionsBy((t=>na(e,t.head)),{origin:"+move",bias:1}),goLineEnd:e=>e.extendSelectionsBy((t=>function(e,t){let i=Zi(e.doc,t),r=function(e){let t;for(;t=Br(e);)e=t.find(1,!0).line;return e}(i);r!=i&&(t=tr(r));return ta(!0,e,i,t,-1)}(e,t.head.line)),{origin:"+move",bias:-1}),goLineRight:e=>e.extendSelectionsBy((t=>{let i=e.cursorCoords(t.head,"div").top+5;return e.coordsChar({left:e.display.lineDiv.offsetWidth+100,top:i},"div")}),Yt),goLineLeft:e=>e.extendSelectionsBy((t=>{let i=e.cursorCoords(t.head,"div").top+5;return e.coordsChar({left:0,top:i},"div")}),Yt),goLineLeftSmart:e=>e.extendSelectionsBy((t=>{let i=e.cursorCoords(t.head,"div").top+5,r=e.coordsChar({left:0,top:i},"div");return r.ch<e.getLine(r.line).search(/\S/)?na(e,t.head):r}),Yt),goLineUp:e=>e.moveV(-1,"line"),goLineDown:e=>e.moveV(1,"line"),goPageUp:e=>e.moveV(-1,"page"),goPageDown:e=>e.moveV(1,"page"),goCharLeft:e=>e.moveH(-1,"char"),goCharRight:e=>e.moveH(1,"char"),goColumnLeft:e=>e.moveH(-1,"column"),goColumnRight:e=>e.moveH(1,"column"),goWordLeft:e=>e.moveH(-1,"word"),goGroupRight:e=>e.moveH(1,"group"),goGroupLeft:e=>e.moveH(-1,"group"),goWordRight:e=>e.moveH(1,"word"),delCharBefore:e=>e.deleteH(-1,"codepoint"),delCharAfter:e=>e.deleteH(1,"char"),delWordBefore:e=>e.deleteH(-1,"word"),delWordAfter:e=>e.deleteH(1,"word"),delGroupBefore:e=>e.deleteH(-1,"group"),delGroupAfter:e=>e.deleteH(1,"group"),indentAuto:e=>e.indentSelection("smart"),indentMore:e=>e.indentSelection("add"),indentLess:e=>e.indentSelection("subtract"),insertTab:e=>e.replaceSelection("\t"),insertSoftTab:e=>{let t=[],i=e.listSelections(),r=e.options.tabSize;for(let n=0;n<i.length;n++){let o=i[n].from(),s=Ut(e.getLine(o.line),o.ch,r);t.push(Qt(r-s%r))}e.replaceSelections(t)},defaultTab:e=>{e.somethingSelected()?e.indentSelection("add"):e.execCommand("insertTab")},transposeChars:e=>rs(e,(()=>{let t=e.listSelections(),i=[];for(let r=0;r<t.length;r++){if(!t[r].empty())continue;let n=t[r].head,o=Zi(e.doc,n.line).text;if(o)if(n.ch==o.length&&(n=new or(n.line,n.ch-1)),n.ch>0)n=new or(n.line,n.ch+1),e.replaceRange(o.charAt(n.ch-1)+o.charAt(n.ch-2),or(n.line,n.ch-2),n,"+transpose");else if(n.line>e.doc.first){let t=Zi(e.doc,n.line-1).text;t&&(n=new or(n.line,1),e.replaceRange(o.charAt(0)+e.doc.lineSeparator()+t.charAt(t.length-1),or(n.line-1,t.length-1),n,"+transpose"))}i.push(new Ms(n,n))}e.setSelections(i)})),newlineAndIndent:e=>rs(e,(()=>{let t=e.listSelections();for(let i=t.length-1;i>=0;i--)e.replaceRange(e.doc.lineSeparator(),t[i].anchor,t[i].head,"+input");t=e.listSelections();for(let i=0;i<t.length;i++)e.indentLine(t[i].from().line,null,!0);$o(e)})),openLine:e=>e.replaceSelection("\n","start"),toggleOverwrite:e=>e.toggleOverwrite()};function ra(e,t){let i=Zi(e.doc,t),r=Ur(i);return r!=i&&(t=tr(r)),ta(!0,e,r,t,1)}function na(e,t){let i=ra(e,t.line),r=Zi(e.doc,i.line),n=fi(r,e.doc.direction);if(!n||0==n[0].level){let e=Math.max(i.ch,r.text.search(/\S/)),n=t.line==i.line&&t.ch<=e&&t.ch;return or(i.line,n?0:e,i.sticky)}return i}function oa(e,t,i){if("string"==typeof t&&!(t=ia[t]))return!1;e.display.input.ensurePolled();let r=e.display.shift,n=!1;try{e.isReadOnly()&&(e.state.suppressEdits=!0),i&&(e.display.shift=!1),n=t(e)!=Gt}finally{e.display.shift=r,e.state.suppressEdits=!1}return n}var sa=new Vt;function la(e,t,i,r){let n=e.state.keySeq;if(n){if(Kl(t))return"handled";if(/\'$/.test(t)?e.state.keySeq=null:sa.set(50,(()=>{e.state.keySeq==n&&(e.state.keySeq=null,e.display.input.reset())})),aa(e,n+" "+t,i,r))return!0}return aa(e,t,i,r)}function aa(e,t,i,r){let n=function(e,t,i){for(let r=0;r<e.state.keyMaps.length;r++){let n=Gl(t,e.state.keyMaps[r],i,e);if(n)return n}return e.options.extraKeys&&Gl(t,e.options.extraKeys,i,e)||Gl(t,e.options.keyMap,i,e)}(e,t,r);return"multi"==n&&(e.state.keySeq=t),"handled"==n&&pn(e,"keyHandled",e,t,i),"handled"!=n&&"multi"!=n||(Ci(i),Mo(e)),!!n}function ca(e,t){let i=Yl(t,!0);return!!i&&(t.shiftKey&&!e.state.keySeq?la(e,"Shift-"+i,t,(t=>oa(e,t,!0)))||la(e,i,t,(t=>{if("string"==typeof t?/^go[A-Z]/.test(t):t.motion)return oa(e,t)})):la(e,i,t,(t=>oa(e,t))))}var da=null;function ua(e){let t=this;if(e.target&&e.target!=t.display.input.getField())return;if(t.curOp.focus=$t(),xi(t,e))return;ut&&ht<11&&27==e.keyCode&&(e.returnValue=!1);let i=e.keyCode;t.display.shift=16==i||e.shiftKey;let r=ca(t,e);gt&&(da=r?i:null,r||88!=i||zi||!(kt?e.metaKey:e.ctrlKey)||t.replaceSelection("",null,"cut")),lt&&!kt&&!r&&46==i&&e.shiftKey&&!e.ctrlKey&&document.execCommand&&document.execCommand("cut"),18!=i||/\bCodeMirror-crosshair\b/.test(t.display.lineDiv.className)||function(e){let t=e.display.lineDiv;function i(e){18!=e.keyCode&&e.altKey||(Pt(t,"CodeMirror-crosshair"),yi(document,"keyup",i),yi(document,"mouseover",i))}zt(t,"CodeMirror-crosshair"),vi(document,"keyup",i),vi(document,"mouseover",i)}(t)}function ha(e){16==e.keyCode&&(this.doc.sel.shift=!1),xi(this,e)}function pa(e){let t=this;if(e.target&&e.target!=t.display.input.getField())return;if(Mn(t.display,e)||xi(t,e)||e.ctrlKey&&!e.altKey||kt&&e.metaKey)return;let i=e.keyCode,r=e.charCode;if(gt&&i==da)return da=null,void Ci(e);if(gt&&(!e.which||e.which<10)&&ca(t,e))return;let n=String.fromCharCode(null==r?i:r);"\b"!=n&&(function(e,t,i){return la(e,"'"+i+"'",t,(t=>oa(e,t,!0)))}(t,e,n)||t.display.input.onKeyPress(e))}var ma,fa,ga=class{constructor(e,t,i){this.time=e,this.pos=t,this.button=i}compare(e,t,i){return this.time+400>e&&0==sr(t,this.pos)&&i==this.button}};function va(e){let t=this,i=t.display;if(xi(t,e)||i.activeTouch&&i.input.supportsTouch())return;if(i.input.ensurePolled(),i.shift=e.shiftKey,Mn(i,e))return void(pt||(i.scroller.draggable=!1,setTimeout((()=>i.scroller.draggable=!0),100)));if(_a(t,e))return;let r=fo(t,e),n=Li(e),o=r?function(e,t){let i=+new Date;return fa&&fa.compare(i,e,t)?(ma=fa=null,"triple"):ma&&ma.compare(i,e,t)?(fa=new ga(i,e,t),ma=null,"double"):(ma=new ga(i,e,t),fa=null,"single")}(r,n):"single";window.focus(),1==n&&t.state.selectingText&&t.state.selectingText(e),r&&function(e,t,i,r,n){let o="Click";"double"==r?o="Double"+o:"triple"==r&&(o="Triple"+o);return o=(1==t?"Left":2==t?"Middle":"Right")+o,la(e,Xl(o,n),n,(t=>{if("string"==typeof t&&(t=ia[t]),!t)return!1;let r=!1;try{e.isReadOnly()&&(e.state.suppressEdits=!0),r=t(e,i)!=Gt}finally{e.state.suppressEdits=!1}return r}))}(t,n,r,o,e)||(1==n?r?function(e,t,i,r){ut?setTimeout(Wt(Eo,e),0):e.curOp.focus=$t();let n,o=function(e,t,i){let r=e.getOption("configureMouse"),n=r?r(e,t,i):{};if(null==n.unit){let e=St?i.shiftKey&&i.metaKey:i.altKey;n.unit=e?"rectangle":"single"==t?"char":"double"==t?"word":"line"}(null==n.extend||e.doc.extend)&&(n.extend=e.doc.extend||i.shiftKey);null==n.addNew&&(n.addNew=kt?i.metaKey:i.ctrlKey);null==n.moveOnDrag&&(n.moveOnDrag=!(kt?i.altKey:i.ctrlKey));return n}(e,i,r),s=e.doc.sel;e.options.dragDrop&&Ni&&!e.isReadOnly()&&"single"==i&&(n=s.contains(t))>-1&&(sr((n=s.ranges[n]).from(),t)<0||t.xRel>0)&&(sr(n.to(),t)>0||t.xRel<0)?function(e,t,i,r){let n=e.display,o=!1,s=ns(e,(t=>{pt&&(n.scroller.draggable=!1),e.state.draggingText=!1,e.state.delayingBlurEvent&&(e.hasFocus()?e.state.delayingBlurEvent=!1:Ao(e)),yi(n.wrapper.ownerDocument,"mouseup",s),yi(n.wrapper.ownerDocument,"mousemove",l),yi(n.scroller,"dragstart",a),yi(n.scroller,"drop",s),o||(Ci(t),r.addNew||Js(e.doc,i,null,null,r.extend),pt&&!vt||ut&&9==ht?setTimeout((()=>{n.wrapper.ownerDocument.body.focus({preventScroll:!0}),n.input.focus()}),20):n.input.focus())})),l=function(e){o=o||Math.abs(t.clientX-e.clientX)+Math.abs(t.clientY-e.clientY)>=10},a=()=>o=!0;pt&&(n.scroller.draggable=!0);e.state.draggingText=s,s.copy=!r.moveOnDrag,vi(n.wrapper.ownerDocument,"mouseup",s),vi(n.wrapper.ownerDocument,"mousemove",l),vi(n.scroller,"dragstart",a),vi(n.scroller,"drop",s),e.state.delayingBlurEvent=!0,setTimeout((()=>n.input.focus()),20),n.scroller.dragDrop&&n.scroller.dragDrop()}(e,r,t,o):function(e,t,i,r){ut&&Ao(e);let n=e.display,o=e.doc;Ci(t);let s,l,a=o.sel,c=a.ranges;r.addNew&&!r.extend?(l=o.sel.contains(i),s=l>-1?c[l]:new Ms(i,i)):(s=o.sel.primary(),l=o.sel.primIndex);if("rectangle"==r.unit)r.addNew||(s=new Ms(i,i)),i=fo(e,t,!0,!0),l=-1;else{let t=ba(e,i,r.unit);s=r.extend?Zs(s,t.anchor,t.head,r.extend):t}r.addNew?-1==l?(l=c.length,rl(o,Es(e,c.concat([s]),l),{scroll:!1,origin:"*mouse"})):c.length>1&&c[l].empty()&&"char"==r.unit&&!r.extend?(rl(o,Es(e,c.slice(0,l).concat(c.slice(l+1)),0),{scroll:!1,origin:"*mouse"}),a=o.sel):el(o,l,s,Xt):(l=0,rl(o,new Ts([s],0),Xt),a=o.sel);let d=i;function u(t){if(0!=sr(d,t))if(d=t,"rectangle"==r.unit){let r=[],n=e.options.tabSize,s=Ut(Zi(o,i.line).text,i.ch,n),c=Ut(Zi(o,t.line).text,t.ch,n),d=Math.min(s,c),u=Math.max(s,c);for(let s=Math.min(i.line,t.line),l=Math.min(e.lastLine(),Math.max(i.line,t.line));s<=l;s++){let e=Zi(o,s).text,t=Zt(e,d,n);d==u?r.push(new Ms(or(s,t),or(s,t))):e.length>t&&r.push(new Ms(or(s,t),or(s,Zt(e,u,n))))}r.length||r.push(new Ms(i,i)),rl(o,Es(e,a.ranges.slice(0,l).concat(r),l),{origin:"*mouse",scroll:!1}),e.scrollIntoView(t)}else{let i,n=s,c=ba(e,t,r.unit),d=n.anchor;sr(c.anchor,d)>0?(i=c.head,d=dr(n.from(),c.anchor)):(i=c.anchor,d=cr(n.to(),c.head));let u=a.ranges.slice(0);u[l]=function(e,t){let{anchor:i,head:r}=t,n=Zi(e.doc,i.line);if(0==sr(i,r)&&i.sticky==r.sticky)return t;let o=fi(n);if(!o)return t;let s=pi(o,i.ch,i.sticky),l=o[s];if(l.from!=i.ch&&l.to!=i.ch)return t;let a,c=s+(l.from==i.ch==(1!=l.level)?0:1);if(0==c||c==o.length)return t;if(r.line!=i.line)a=(r.line-i.line)*("ltr"==e.doc.direction?1:-1)>0;else{let e=pi(o,r.ch,r.sticky),t=e-s||(r.ch-i.ch)*(1==l.level?-1:1);a=e==c-1||e==c?t<0:t>0}let d=o[c+(a?-1:0)],u=a==(1==d.level),h=u?d.from:d.to,p=u?"after":"before";return i.ch==h&&i.sticky==p?t:new Ms(new or(i.line,h,p),r)}(e,new Ms(hr(o,d),i)),rl(o,Es(e,u,l),Xt)}}let h=n.wrapper.getBoundingClientRect(),p=0;function m(t){let i=++p,s=fo(e,t,!0,"rectangle"==r.unit);if(s)if(0!=sr(s,d)){e.curOp.focus=$t(),u(s);let r=Io(n,o);(s.line>=r.to||s.line<r.from)&&setTimeout(ns(e,(()=>{p==i&&m(t)})),150)}else{let r=t.clientY<h.top?-20:t.clientY>h.bottom?20:0;r&&setTimeout(ns(e,(()=>{p==i&&(n.scroller.scrollTop+=r,m(t))})),50)}}function f(t){e.state.selectingText=!1,p=1/0,t&&(Ci(t),n.input.focus()),yi(n.wrapper.ownerDocument,"mousemove",g),yi(n.wrapper.ownerDocument,"mouseup",v),o.history.lastSelOrigin=null}let g=ns(e,(e=>{0!==e.buttons&&Li(e)?m(e):f(e)})),v=ns(e,f);e.state.selectingText=v,vi(n.wrapper.ownerDocument,"mousemove",g),vi(n.wrapper.ownerDocument,"mouseup",v)}(e,r,t,o)}(t,r,o,e):Ai(e)==i.scroller&&Ci(e):2==n?(r&&Js(t.doc,r),setTimeout((()=>i.input.focus()),20)):3==n&&(Et?t.display.input.onContextMenu(e):Ao(t)))}function ba(e,t,i){if("char"==i)return new Ms(t,t);if("word"==i)return e.findWordAt(t);if("line"==i)return new Ms(or(t.line,0),hr(e.doc,or(t.line+1,0)));let r=i(e,t);return new Ms(r.from,r.to)}function ya(e,t,i,r){let n,o;if(t.touches)n=t.touches[0].clientX,o=t.touches[0].clientY;else try{n=t.clientX,o=t.clientY}catch(e){return!1}if(n>=Math.floor(e.display.gutters.getBoundingClientRect().right))return!1;r&&Ci(t);let s=e.display,l=s.lineDiv.getBoundingClientRect();if(o>l.bottom||!ki(e,i))return Mi(t);o-=l.top-s.viewOffset;for(let r=0;r<e.display.gutterSpecs.length;++r){let l=s.gutters.childNodes[r];if(l&&l.getBoundingClientRect().right>=n){return _i(e,i,e,ir(e.doc,o),e.display.gutterSpecs[r].className,t),Mi(t)}}}function _a(e,t){return ya(e,t,"gutterClick",!0)}function xa(e,t){Mn(e.display,t)||function(e,t){return!!ki(e,"gutterContextMenu")&&ya(e,t,"gutterContextMenu",!1)}(e,t)||xi(e,t,"contextmenu")||Et||e.display.input.onContextMenu(t)}function wa(e){e.display.wrapper.className=e.display.wrapper.className.replace(/\s*cm-s-\S+/g,"")+e.options.theme.replace(/(^|\s)\s*/g," cm-s-"),qn(e)}var ka={toString:function(){return"CodeMirror.Init"}},Sa={},Ca={};function Ta(e,t,i){if(!t!=!(i&&i!=ka)){let i=e.display.dragFunctions,r=t?vi:yi;r(e.display.scroller,"dragstart",i.start),r(e.display.scroller,"dragenter",i.enter),r(e.display.scroller,"dragover",i.over),r(e.display.scroller,"dragleave",i.leave),r(e.display.scroller,"drop",i.drop)}}function Ma(e){e.options.lineWrapping?(zt(e.display.wrapper,"CodeMirror-wrap"),e.display.sizer.style.minWidth="",e.display.sizerWidth=null):(Pt(e.display.wrapper,"CodeMirror-wrap"),Yr(e)),mo(e),vo(e),qn(e),setTimeout((()=>qo(e)),100)}function Ea(e,t){if(!(this instanceof Ea))return new Ea(e,t);this.options=t=t?Ht(t):{},Ht(Sa,t,!1);let i=t.value;"string"==typeof i?i=new Dl(i,t.mode,null,t.lineSeparator,t.direction):t.mode&&(i.modeOption=t.mode),this.doc=i;let r=new Ea.inputStyles[t.inputStyle](this),n=this.display=new _s(e,i,r,t);n.wrapper.CodeMirror=this,wa(this),t.lineWrapping&&(this.display.wrapper.className+=" CodeMirror-wrap"),Ko(this),this.state={keyMaps:[],overlays:[],modeGen:0,overwrite:!1,delayingBlurEvent:!1,focused:!1,suppressEdits:!1,pasteIncoming:-1,cutIncoming:-1,selectingText:!1,draggingText:!1,highlight:new Vt,keySeq:null,specialChars:null},t.autofocus&&!wt&&n.input.focus(),ut&&ht<11&&setTimeout((()=>this.display.input.reset(!0)),20),function(e){let t=e.display;vi(t.scroller,"mousedown",ns(e,va)),vi(t.scroller,"dblclick",ut&&ht<11?ns(e,(t=>{if(xi(e,t))return;let i=fo(e,t);if(!i||_a(e,t)||Mn(e.display,t))return;Ci(t);let r=e.findWordAt(i);Js(e.doc,r.anchor,r.head)})):t=>xi(e,t)||Ci(t));vi(t.scroller,"contextmenu",(t=>xa(e,t))),vi(t.input.getField(),"contextmenu",(i=>{t.scroller.contains(i.target)||xa(e,i)}));let i,r={end:0};function n(){t.activeTouch&&(i=setTimeout((()=>t.activeTouch=null),1e3),r=t.activeTouch,r.end=+new Date)}function o(e){if(1!=e.touches.length)return!1;let t=e.touches[0];return t.radiusX<=1&&t.radiusY<=1}function s(e,t){if(null==t.left)return!0;let i=t.left-e.left,r=t.top-e.top;return i*i+r*r>400}vi(t.scroller,"touchstart",(n=>{if(!xi(e,n)&&!o(n)&&!_a(e,n)){t.input.ensurePolled(),clearTimeout(i);let e=+new Date;t.activeTouch={start:e,moved:!1,prev:e-r.end<=300?r:null},1==n.touches.length&&(t.activeTouch.left=n.touches[0].pageX,t.activeTouch.top=n.touches[0].pageY)}})),vi(t.scroller,"touchmove",(()=>{t.activeTouch&&(t.activeTouch.moved=!0)})),vi(t.scroller,"touchend",(i=>{let r=t.activeTouch;if(r&&!Mn(t,i)&&null!=r.left&&!r.moved&&new Date-r.start<300){let n,o=e.coordsChar(t.activeTouch,"page");n=!r.prev||s(r,r.prev)?new Ms(o,o):!r.prev.prev||s(r,r.prev.prev)?e.findWordAt(o):new Ms(or(o.line,0),hr(e.doc,or(o.line+1,0))),e.setSelection(n.anchor,n.head),e.focus(),Ci(i)}n()})),vi(t.scroller,"touchcancel",n),vi(t.scroller,"scroll",(()=>{t.scroller.clientHeight&&(Wo(e,t.scroller.scrollTop),Uo(e,t.scroller.scrollLeft,!0),_i(e,"scroll",e))})),vi(t.scroller,"mousewheel",(t=>Cs(e,t))),vi(t.scroller,"DOMMouseScroll",(t=>Cs(e,t))),vi(t.wrapper,"scroll",(()=>t.wrapper.scrollTop=t.wrapper.scrollLeft=0)),t.dragFunctions={enter:t=>{xi(e,t)||Ei(t)},over:t=>{xi(e,t)||(!function(e,t){let i=fo(e,t);if(!i)return;let r=document.createDocumentFragment();So(e,i,r),e.display.dragCursor||(e.display.dragCursor=It("div",null,"CodeMirror-cursors CodeMirror-dragcursors"),e.display.lineSpace.insertBefore(e.display.dragCursor,e.display.cursorDiv)),Nt(e.display.dragCursor,r)}(e,t),Ei(t))},start:t=>function(e,t){if(ut&&(!e.state.draggingText||+new Date-Ol<100))Ei(t);else if(!xi(e,t)&&!Mn(e.display,t)&&(t.dataTransfer.setData("Text",e.getSelection()),t.dataTransfer.effectAllowed="copyMove",t.dataTransfer.setDragImage&&!vt)){let i=It("img",null,null,"position: fixed; left: 0; top: 0;");i.src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==",gt&&(i.width=i.height=1,e.display.wrapper.appendChild(i),i._top=i.offsetTop),t.dataTransfer.setDragImage(i,0,0),gt&&i.parentNode.removeChild(i)}}(e,t),drop:ns(e,$l),leave:t=>{xi(e,t)||zl(e)}};let l=t.input.getField();vi(l,"keyup",(t=>ha.call(e,t))),vi(l,"keydown",ns(e,ua)),vi(l,"keypress",ns(e,pa)),vi(l,"focus",(t=>Lo(e,t))),vi(l,"blur",(t=>Po(e,t)))}(this),Wl(),Yo(this),this.curOp.forceUpdate=!0,Fs(this,i),t.autofocus&&!wt||this.hasFocus()?setTimeout((()=>{this.hasFocus()&&!this.state.focused&&Lo(this)}),20):Po(this);for(let e in Ca)Ca.hasOwnProperty(e)&&Ca[e](this,t[e],ka);gs(this),t.finishInit&&t.finishInit(this);for(let e=0;e<La.length;++e)La[e](this);Zo(this),pt&&t.lineWrapping&&"optimizelegibility"==getComputedStyle(n.lineDiv).textRendering&&(n.lineDiv.style.textRendering="auto")}Ea.defaults=Sa,Ea.optionHandlers=Ca;var Aa=Ea;var La=[];function Pa(e,t,i,r){let n,o=e.doc;null==i&&(i="add"),"smart"==i&&(o.mode.indent?n=br(e,t).state:i="prev");let s=e.options.tabSize,l=Zi(o,t),a=Ut(l.text,null,s);l.stateAfter&&(l.stateAfter=null);let c,d=l.text.match(/^\s*/)[0];if(r||/\S/.test(l.text)){if("smart"==i&&(c=o.mode.indent(n,l.text.slice(d.length),l.text),c==Gt||c>150)){if(!r)return;i="prev"}}else c=0,i="not";"prev"==i?c=t>o.first?Ut(Zi(o,t-1).text,null,s):0:"add"==i?c=a+e.options.indentUnit:"subtract"==i?c=a-e.options.indentUnit:"number"==typeof i&&(c=a+i),c=Math.max(0,c);let u="",h=0;if(e.options.indentWithTabs)for(let e=Math.floor(c/s);e;--e)h+=s,u+="\t";if(h<c&&(u+=Qt(c-h)),u!=d)return bl(o,u,or(t,0),or(t,d.length),"+input"),l.stateAfter=null,!0;for(let e=0;e<o.sel.ranges.length;e++){let i=o.sel.ranges[e];if(i.head.line==t&&i.head.ch<d.length){let i=or(t,d.length);el(o,e,new Ms(i,i));break}}}Ea.defineInitHook=e=>La.push(e);var Ra=null;function Na(e){Ra=e}function Ia(e,t,i,r,n){let o=e.doc;e.display.shift=!1,r||(r=o.sel);let s=+new Date-200,l="paste"==n||e.state.pasteIncoming>s,a=Oi(t),c=null;if(l&&r.ranges.length>1)if(Ra&&Ra.text.join("\n")==t){if(r.ranges.length%Ra.text.length==0){c=[];for(let e=0;e<Ra.text.length;e++)c.push(o.splitLines(Ra.text[e]))}}else a.length==r.ranges.length&&e.options.pasteLinesPerSelection&&(c=ti(a,(e=>[e])));let d=e.curOp.updateInput;for(let t=r.ranges.length-1;t>=0;t--){let d=r.ranges[t],u=d.from(),h=d.to();d.empty()&&(i&&i>0?u=or(u.line,u.ch-i):e.state.overwrite&&!l?h=or(h.line,Math.min(Zi(o,h.line).text.length,h.ch+ei(a).length)):l&&Ra&&Ra.lineWise&&Ra.text.join("\n")==a.join("\n")&&(u=h=or(u.line,0)));let p={from:u,to:h,text:c?c[t%c.length]:a,origin:n||(l?"paste":e.state.cutIncoming>s?"cut":"+input")};pl(e.doc,p),pn(e,"inputRead",e,p)}t&&!l&&Oa(e,t),$o(e),e.curOp.updateInput<2&&(e.curOp.updateInput=d),e.curOp.typing=!0,e.state.pasteIncoming=e.state.cutIncoming=-1}function Da(e,t){let i=e.clipboardData&&e.clipboardData.getData("Text");if(i)return e.preventDefault(),t.isReadOnly()||t.options.disableInput||rs(t,(()=>Ia(t,i,0,null,"paste"))),!0}function Oa(e,t){if(!e.options.electricChars||!e.options.smartIndent)return;let i=e.doc.sel;for(let r=i.ranges.length-1;r>=0;r--){let n=i.ranges[r];if(n.head.ch>100||r&&i.ranges[r-1].head.line==n.head.line)continue;let o=e.getModeAt(n.head),s=!1;if(o.electricChars){for(let i=0;i<o.electricChars.length;i++)if(t.indexOf(o.electricChars.charAt(i))>-1){s=Pa(e,n.head.line,"smart");break}}else o.electricInput&&o.electricInput.test(Zi(e.doc,n.head.line).text.slice(0,n.head.ch))&&(s=Pa(e,n.head.line,"smart"));s&&pn(e,"electricInput",e,n.head.line)}}function $a(e){let t=[],i=[];for(let r=0;r<e.doc.sel.ranges.length;r++){let n=e.doc.sel.ranges[r].head.line,o={anchor:or(n,0),head:or(n+1,0)};i.push(o),t.push(e.getRange(o.anchor,o.head))}return{text:t,ranges:i}}function za(e,t,i,r){e.setAttribute("autocorrect",i?"":"off"),e.setAttribute("autocapitalize",r?"":"off"),e.setAttribute("spellcheck",!!t)}function Fa(){let e=It("textarea",null,null,"position: absolute; bottom: -1em; padding: 0; width: 1px; height: 1em; outline: none"),t=It("div",[e],null,"overflow: hidden; position: relative; width: 3px; height: 0px;");return pt?e.style.width="1000px":e.setAttribute("wrap","off"),_t&&(e.style.border="1px solid black"),za(e),t}function Ba(e,t,i,r,n){let o=t,s=i,l=Zi(e,t.line),a=n&&"rtl"==e.direction?-i:i;function c(o){let s;if("codepoint"==r){let e=l.text.charCodeAt(t.ch+(i>0?0:-1));if(isNaN(e))s=null;else{let r=i>0?e>=55296&&e<56320:e>=56320&&e<57343;s=new or(t.line,Math.max(0,Math.min(l.text.length,t.ch+i*(r?2:1))),-i)}}else s=n?function(e,t,i,r){let n=fi(t,e.doc.direction);if(!n)return ea(t,i,r);i.ch>=t.text.length?(i.ch=t.text.length,i.sticky="before"):i.ch<=0&&(i.ch=0,i.sticky="after");let o=pi(n,i.ch,i.sticky),s=n[o];if("ltr"==e.doc.direction&&s.level%2==0&&(r>0?s.to>i.ch:s.from<i.ch))return ea(t,i,r);let l,a=(e,i)=>Ql(t,e instanceof or?e.ch:e,i),c=i=>e.options.lineWrapping?(l=l||$n(e,t),ro(e,t,l,i)):{begin:0,end:t.text.length},d=c("before"==i.sticky?a(i,-1):i.ch);if("rtl"==e.doc.direction||1==s.level){let e=1==s.level==r<0,t=a(i,e?1:-1);if(null!=t&&(e?t<=s.to&&t<=d.end:t>=s.from&&t>=d.begin)){let r=e?"before":"after";return new or(i.line,t,r)}}let u=(e,t,r)=>{let o=(e,t)=>t?new or(i.line,a(e,1),"before"):new or(i.line,e,"after");for(;e>=0&&e<n.length;e+=t){let i=n[e],s=t>0==(1!=i.level),l=s?r.begin:a(r.end,-1);if(i.from<=l&&l<i.to)return o(l,s);if(l=s?i.from:a(i.to,-1),r.begin<=l&&l<r.end)return o(l,s)}},h=u(o+r,r,d);if(h)return h;let p=r>0?d.end:a(d.begin,-1);return null==p||r>0&&p==t.text.length||(h=u(r>0?0:n.length-1,r,c(p)),!h)?null:h}(e.cm,l,t,i):ea(l,t,i);if(null==s){if(o||!function(){let i=t.line+a;return!(i<e.first||i>=e.first+e.size)&&(t=new or(i,t.ch,t.sticky),l=Zi(e,i))}())return!1;t=ta(n,e.cm,l,t.line,a)}else t=s;return!0}if("char"==r||"codepoint"==r)c();else if("column"==r)c(!0);else if("word"==r||"group"==r){let n=null,o="group"==r,s=e.cm&&e.cm.getHelper(t,"wordChars");for(let e=!0;!(i<0)||c(!e);e=!1){let r=l.text.charAt(t.ch)||"\n",a=si(r,s)?"w":o&&"\n"==r?"n":!o||/\s/.test(r)?null:"p";if(!o||e||a||(a="s"),n&&n!=a){i<0&&(i=1,c(),t.sticky="after");break}if(a&&(n=a),i>0&&!c(!e))break}}let d=cl(e,t,o,s,!0);return lr(o,d)&&(d.hitSide=!0),d}function Wa(e,t,i,r){let n,o,s=e.doc,l=t.left;if("page"==r){let r=Math.min(e.display.wrapper.clientHeight,window.innerHeight||document.documentElement.clientHeight),o=Math.max(r-.5*ao(e.display),3);n=(i>0?t.bottom:t.top)+i*o}else"line"==r&&(n=i>0?t.bottom+3:t.top-3);for(;o=to(e,l,n),o.outside;){if(i<0?n<=0:n>=s.height){o.hitSide=!0;break}n+=5*i}return o}var Ha=class{constructor(e){this.cm=e,this.lastAnchorNode=this.lastAnchorOffset=this.lastFocusNode=this.lastFocusOffset=null,this.polling=new Vt,this.composing=null,this.gracePeriod=!1,this.readDOMTimeout=null}init(e){let t=this,i=t.cm,r=t.div=e.lineDiv;function n(e){for(let t=e.target;t;t=t.parentNode){if(t==r)return!0;if(/\bCodeMirror-(?:line)?widget\b/.test(t.className))break}return!1}function o(e){if(!n(e)||xi(i,e))return;if(i.somethingSelected())Na({lineWise:!1,text:i.getSelections()}),"cut"==e.type&&i.replaceSelection("",null,"cut");else{if(!i.options.lineWiseCopyCut)return;{let t=$a(i);Na({lineWise:!0,text:t.text}),"cut"==e.type&&i.operation((()=>{i.setSelections(t.ranges,0,Kt),i.replaceSelection("",null,"cut")}))}}if(e.clipboardData){e.clipboardData.clearData();let t=Ra.text.join("\n");if(e.clipboardData.setData("Text",t),e.clipboardData.getData("Text")==t)return void e.preventDefault()}let o=Fa(),s=o.firstChild;i.display.lineSpace.insertBefore(o,i.display.lineSpace.firstChild),s.value=Ra.text.join("\n");let l=$t();Bt(s),setTimeout((()=>{i.display.lineSpace.removeChild(o),l.focus(),l==r&&t.showPrimarySelection()}),50)}r.contentEditable=!0,za(r,i.options.spellcheck,i.options.autocorrect,i.options.autocapitalize),vi(r,"paste",(e=>{!n(e)||xi(i,e)||Da(e,i)||ht<=11&&setTimeout(ns(i,(()=>this.updateFromDOM())),20)})),vi(r,"compositionstart",(e=>{this.composing={data:e.data,done:!1}})),vi(r,"compositionupdate",(e=>{this.composing||(this.composing={data:e.data,done:!1})})),vi(r,"compositionend",(e=>{this.composing&&(e.data!=this.composing.data&&this.readFromDOMSoon(),this.composing.done=!0)})),vi(r,"touchstart",(()=>t.forceCompositionEnd())),vi(r,"input",(()=>{this.composing||this.readFromDOMSoon()})),vi(r,"copy",o),vi(r,"cut",o)}screenReaderLabelChanged(e){e?this.div.setAttribute("aria-label",e):this.div.removeAttribute("aria-label")}prepareSelection(){let e=ko(this.cm,!1);return e.focus=$t()==this.div,e}showSelection(e,t){e&&this.cm.display.view.length&&((e.focus||t)&&this.showPrimarySelection(),this.showMultipleSelections(e))}getSelection(){return this.cm.display.wrapper.ownerDocument.getSelection()}showPrimarySelection(){let e=this.getSelection(),t=this.cm,i=t.doc.sel.primary(),r=i.from(),n=i.to();if(t.display.viewTo==t.display.viewFrom||r.line>=t.display.viewTo||n.line<t.display.viewFrom)return void e.removeAllRanges();let o=ja(t,e.anchorNode,e.anchorOffset),s=ja(t,e.focusNode,e.focusOffset);if(o&&!o.bad&&s&&!s.bad&&0==sr(dr(o,s),r)&&0==sr(cr(o,s),n))return;let l=t.display.view,a=r.line>=t.display.viewFrom&&Va(t,r)||{node:l[0].measure.map[2],offset:0},c=n.line<t.display.viewTo&&Va(t,n);if(!c){let e=l[l.length-1].measure,t=e.maps?e.maps[e.maps.length-1]:e.map;c={node:t[t.length-1],offset:t[t.length-2]-t[t.length-3]}}if(!a||!c)return void e.removeAllRanges();let d,u=e.rangeCount&&e.getRangeAt(0);try{d=Lt(a.node,a.offset,c.offset,c.node)}catch(e){}d&&(!lt&&t.state.focused?(e.collapse(a.node,a.offset),d.collapsed||(e.removeAllRanges(),e.addRange(d))):(e.removeAllRanges(),e.addRange(d)),u&&null==e.anchorNode?e.addRange(u):lt&&this.startGracePeriod()),this.rememberSelection()}startGracePeriod(){clearTimeout(this.gracePeriod),this.gracePeriod=setTimeout((()=>{this.gracePeriod=!1,this.selectionChanged()&&this.cm.operation((()=>this.cm.curOp.selectionChanged=!0))}),20)}showMultipleSelections(e){Nt(this.cm.display.cursorDiv,e.cursors),Nt(this.cm.display.selectionDiv,e.selection)}rememberSelection(){let e=this.getSelection();this.lastAnchorNode=e.anchorNode,this.lastAnchorOffset=e.anchorOffset,this.lastFocusNode=e.focusNode,this.lastFocusOffset=e.focusOffset}selectionInEditor(){let e=this.getSelection();if(!e.rangeCount)return!1;let t=e.getRangeAt(0).commonAncestorContainer;return Ot(this.div,t)}focus(){"nocursor"!=this.cm.options.readOnly&&(this.selectionInEditor()&&$t()==this.div||this.showSelection(this.prepareSelection(),!0),this.div.focus())}blur(){this.div.blur()}getField(){return this.div}supportsTouch(){return!0}receivedFocus(){let e=this;this.selectionInEditor()?this.pollSelection():rs(this.cm,(()=>e.cm.curOp.selectionChanged=!0)),this.polling.set(this.cm.options.pollInterval,(function t(){e.cm.state.focused&&(e.pollSelection(),e.polling.set(e.cm.options.pollInterval,t))}))}selectionChanged(){let e=this.getSelection();return e.anchorNode!=this.lastAnchorNode||e.anchorOffset!=this.lastAnchorOffset||e.focusNode!=this.lastFocusNode||e.focusOffset!=this.lastFocusOffset}pollSelection(){if(null!=this.readDOMTimeout||this.gracePeriod||!this.selectionChanged())return;let e=this.getSelection(),t=this.cm;if(xt&&ft&&this.cm.display.gutterSpecs.length&&function(e){for(let t=e;t;t=t.parentNode)if(/CodeMirror-gutter-wrapper/.test(t.className))return!0;return!1}(e.anchorNode))return this.cm.triggerOnKeyDown({type:"keydown",keyCode:8,preventDefault:Math.abs}),this.blur(),void this.focus();if(this.composing)return;this.rememberSelection();let i=ja(t,e.anchorNode,e.anchorOffset),r=ja(t,e.focusNode,e.focusOffset);i&&r&&rs(t,(()=>{rl(t.doc,As(i,r),Kt),(i.bad||r.bad)&&(t.curOp.selectionChanged=!0)}))}pollContent(){null!=this.readDOMTimeout&&(clearTimeout(this.readDOMTimeout),this.readDOMTimeout=null);let e,t,i,r=this.cm,n=r.display,o=r.doc.sel.primary(),s=o.from(),l=o.to();if(0==s.ch&&s.line>r.firstLine()&&(s=or(s.line-1,Zi(r.doc,s.line-1).length)),l.ch==Zi(r.doc,l.line).text.length&&l.line<r.lastLine()&&(l=or(l.line+1,0)),s.line<n.viewFrom||l.line>n.viewTo-1)return!1;s.line==n.viewFrom||0==(e=go(r,s.line))?(t=tr(n.view[0].line),i=n.view[0].node):(t=tr(n.view[e].line),i=n.view[e-1].node.nextSibling);let a,c,d=go(r,l.line);if(d==n.view.length-1?(a=n.viewTo-1,c=n.lineDiv.lastChild):(a=tr(n.view[d+1].line)-1,c=n.view[d+1].node.previousSibling),!i)return!1;let u=r.doc.splitLines(function(e,t,i,r,n){let o="",s=!1,l=e.doc.lineSeparator(),a=!1;function c(e){return t=>t.id==e}function d(){s&&(o+=l,a&&(o+=l),s=a=!1)}function u(e){e&&(d(),o+=e)}function h(t){if(1==t.nodeType){let i=t.getAttribute("cm-text");if(i)return void u(i);let o,p=t.getAttribute("cm-marker");if(p){let t=e.findMarks(or(r,0),or(n+1,0),c(+p));return void(t.length&&(o=t[0].find(0))&&u(Ji(e.doc,o.from,o.to).join(l)))}if("false"==t.getAttribute("contenteditable"))return;let m=/^(pre|div|p|li|table|br)$/i.test(t.nodeName);if(!/^br$/i.test(t.nodeName)&&0==t.textContent.length)return;m&&d();for(let e=0;e<t.childNodes.length;e++)h(t.childNodes[e]);/^(pre|p)$/i.test(t.nodeName)&&(a=!0),m&&(s=!0)}else 3==t.nodeType&&u(t.nodeValue.replace(/\u200b/g,"").replace(/\u00a0/g," "))}for(;h(t),t!=i;)t=t.nextSibling,a=!1;return o}(r,i,c,t,a)),h=Ji(r.doc,or(t,0),or(a,Zi(r.doc,a).text.length));for(;u.length>1&&h.length>1;)if(ei(u)==ei(h))u.pop(),h.pop(),a--;else{if(u[0]!=h[0])break;u.shift(),h.shift(),t++}let p=0,m=0,f=u[0],g=h[0],v=Math.min(f.length,g.length);for(;p<v&&f.charCodeAt(p)==g.charCodeAt(p);)++p;let b=ei(u),y=ei(h),_=Math.min(b.length-(1==u.length?p:0),y.length-(1==h.length?p:0));for(;m<_&&b.charCodeAt(b.length-m-1)==y.charCodeAt(y.length-m-1);)++m;if(1==u.length&&1==h.length&&t==s.line)for(;p&&p>s.ch&&b.charCodeAt(b.length-m-1)==y.charCodeAt(y.length-m-1);)p--,m++;u[u.length-1]=b.slice(0,b.length-m).replace(/^\u200b+/,""),u[0]=u[0].slice(p).replace(/\u200b+$/,"");let x=or(t,p),w=or(a,h.length?ei(h).length-m:0);return u.length>1||u[0]||sr(x,w)?(bl(r.doc,u,x,w,"+input"),!0):void 0}ensurePolled(){this.forceCompositionEnd()}reset(){this.forceCompositionEnd()}forceCompositionEnd(){this.composing&&(clearTimeout(this.readDOMTimeout),this.composing=null,this.updateFromDOM(),this.div.blur(),this.div.focus())}readFromDOMSoon(){null==this.readDOMTimeout&&(this.readDOMTimeout=setTimeout((()=>{if(this.readDOMTimeout=null,this.composing){if(!this.composing.done)return;this.composing=null}this.updateFromDOM()}),80))}updateFromDOM(){!this.cm.isReadOnly()&&this.pollContent()||rs(this.cm,(()=>vo(this.cm)))}setUneditable(e){e.contentEditable="false"}onKeyPress(e){0==e.charCode||this.composing||(e.preventDefault(),this.cm.isReadOnly()||ns(this.cm,Ia)(this.cm,String.fromCharCode(null==e.charCode?e.keyCode:e.charCode),0))}readOnlyChanged(e){this.div.contentEditable=String("nocursor"!=e)}onContextMenu(){}resetPosition(){}},Ua=Ha;function Va(e,t){let i=On(e,t.line);if(!i||i.hidden)return null;let r=Zi(e.doc,t.line),n=In(i,r,t.line),o=fi(r,e.doc.direction),s="left";if(o){s=pi(o,t.ch)%2?"right":"left"}let l=Wn(n.map,t.ch,s);return l.offset="right"==l.collapse?l.end:l.start,l}function qa(e,t){return t&&(e.bad=!0),e}function ja(e,t,i){let r;if(t==e.display.lineDiv){if(r=e.display.lineDiv.childNodes[i],!r)return qa(e.clipPos(or(e.display.viewTo-1)),!0);t=null,i=0}else for(r=t;;r=r.parentNode){if(!r||r==e.display.lineDiv)return null;if(r.parentNode&&r.parentNode==e.display.lineDiv)break}for(let n=0;n<e.display.view.length;n++){let o=e.display.view[n];if(o.node==r)return Ga(o,t,i)}}function Ga(e,t,i){let r=e.text.firstChild,n=!1;if(!t||!Ot(r,t))return qa(or(tr(e.line),0),!0);if(t==r&&(n=!0,t=r.childNodes[i],i=0,!t)){let t=e.rest?ei(e.rest):e.line;return qa(or(tr(t),t.text.length),n)}let o=3==t.nodeType?t:null,s=t;for(o||1!=t.childNodes.length||3!=t.firstChild.nodeType||(o=t.firstChild,i&&(i=o.nodeValue.length));s.parentNode!=r;)s=s.parentNode;let l=e.measure,a=l.maps;function c(t,i,r){for(let n=-1;n<(a?a.length:0);n++){let o=n<0?l.map:a[n];for(let s=0;s<o.length;s+=3){let l=o[s+2];if(l==t||l==i){let i=tr(n<0?e.line:e.rest[n]),a=o[s]+r;return(r<0||l!=t)&&(a=o[s+(r?1:0)]),or(i,a)}}}}let d=c(o,s,i);if(d)return qa(d,n);for(let e=s.nextSibling,t=o?o.nodeValue.length-i:0;e;e=e.nextSibling){if(d=c(e,e.firstChild,0),d)return qa(or(d.line,d.ch-t),n);t+=e.textContent.length}for(let e=s.previousSibling,t=i;e;e=e.previousSibling){if(d=c(e,e.firstChild,-1),d)return qa(or(d.line,d.ch+t),n);t+=e.textContent.length}}Ha.prototype.needsContentAttribute=!0;var Ka=class{constructor(e){this.cm=e,this.prevInput="",this.pollingFast=!1,this.polling=new Vt,this.hasSelection=!1,this.composing=null}init(e){let t=this,i=this.cm;this.createField(e);const r=this.textarea;function n(e){if(!xi(i,e)){if(i.somethingSelected())Na({lineWise:!1,text:i.getSelections()});else{if(!i.options.lineWiseCopyCut)return;{let n=$a(i);Na({lineWise:!0,text:n.text}),"cut"==e.type?i.setSelections(n.ranges,null,Kt):(t.prevInput="",r.value=n.text.join("\n"),Bt(r))}}"cut"==e.type&&(i.state.cutIncoming=+new Date)}}e.wrapper.insertBefore(this.wrapper,e.wrapper.firstChild),_t&&(r.style.width="0px"),vi(r,"input",(()=>{ut&&ht>=9&&this.hasSelection&&(this.hasSelection=null),t.poll()})),vi(r,"paste",(e=>{xi(i,e)||Da(e,i)||(i.state.pasteIncoming=+new Date,t.fastPoll())})),vi(r,"cut",n),vi(r,"copy",n),vi(e.scroller,"paste",(n=>{if(Mn(e,n)||xi(i,n))return;if(!r.dispatchEvent)return i.state.pasteIncoming=+new Date,void t.focus();const o=new Event("paste");o.clipboardData=n.clipboardData,r.dispatchEvent(o)})),vi(e.lineSpace,"selectstart",(t=>{Mn(e,t)||Ci(t)})),vi(r,"compositionstart",(()=>{let e=i.getCursor("from");t.composing&&t.composing.range.clear(),t.composing={start:e,range:i.markText(e,i.getCursor("to"),{className:"CodeMirror-composing"})}})),vi(r,"compositionend",(()=>{t.composing&&(t.poll(),t.composing.range.clear(),t.composing=null)}))}createField(e){this.wrapper=Fa(),this.textarea=this.wrapper.firstChild}screenReaderLabelChanged(e){e?this.textarea.setAttribute("aria-label",e):this.textarea.removeAttribute("aria-label")}prepareSelection(){let e=this.cm,t=e.display,i=e.doc,r=ko(e);if(e.options.moveInputWithCursor){let n=Jn(e,i.sel.primary().head,"div"),o=t.wrapper.getBoundingClientRect(),s=t.lineDiv.getBoundingClientRect();r.teTop=Math.max(0,Math.min(t.wrapper.clientHeight-10,n.top+s.top-o.top)),r.teLeft=Math.max(0,Math.min(t.wrapper.clientWidth-10,n.left+s.left-o.left))}return r}showSelection(e){let t=this.cm.display;Nt(t.cursorDiv,e.cursors),Nt(t.selectionDiv,e.selection),null!=e.teTop&&(this.wrapper.style.top=e.teTop+"px",this.wrapper.style.left=e.teLeft+"px")}reset(e){if(this.contextMenuPending||this.composing)return;let t=this.cm;if(t.somethingSelected()){this.prevInput="";let e=t.getSelection();this.textarea.value=e,t.state.focused&&Bt(this.textarea),ut&&ht>=9&&(this.hasSelection=e)}else e||(this.prevInput=this.textarea.value="",ut&&ht>=9&&(this.hasSelection=null))}getField(){return this.textarea}supportsTouch(){return!1}focus(){if("nocursor"!=this.cm.options.readOnly&&(!wt||$t()!=this.textarea))try{this.textarea.focus()}catch(e){}}blur(){this.textarea.blur()}resetPosition(){this.wrapper.style.top=this.wrapper.style.left=0}receivedFocus(){this.slowPoll()}slowPoll(){this.pollingFast||this.polling.set(this.cm.options.pollInterval,(()=>{this.poll(),this.cm.state.focused&&this.slowPoll()}))}fastPoll(){let e=!1,t=this;t.pollingFast=!0,t.polling.set(20,(function i(){t.poll()||e?(t.pollingFast=!1,t.slowPoll()):(e=!0,t.polling.set(60,i))}))}poll(){let e=this.cm,t=this.textarea,i=this.prevInput;if(this.contextMenuPending||!e.state.focused||$i(t)&&!i&&!this.composing||e.isReadOnly()||e.options.disableInput||e.state.keySeq)return!1;let r=t.value;if(r==i&&!e.somethingSelected())return!1;if(ut&&ht>=9&&this.hasSelection===r||kt&&/[\uf700-\uf7ff]/.test(r))return e.display.input.reset(),!1;if(e.doc.sel==e.display.selForContextMenu){let e=r.charCodeAt(0);if(8203!=e||i||(i="​"),8666==e)return this.reset(),this.cm.execCommand("undo")}let n=0,o=Math.min(i.length,r.length);for(;n<o&&i.charCodeAt(n)==r.charCodeAt(n);)++n;return rs(e,(()=>{Ia(e,r.slice(n),i.length-n,null,this.composing?"*compose":null),r.length>1e3||r.indexOf("\n")>-1?t.value=this.prevInput="":this.prevInput=r,this.composing&&(this.composing.range.clear(),this.composing.range=e.markText(this.composing.start,e.getCursor("to"),{className:"CodeMirror-composing"}))})),!0}ensurePolled(){this.pollingFast&&this.poll()&&(this.pollingFast=!1)}onKeyPress(){ut&&ht>=9&&(this.hasSelection=null),this.fastPoll()}onContextMenu(e){let t=this,i=t.cm,r=i.display,n=t.textarea;t.contextMenuPending&&t.contextMenuPending();let o=fo(i,e),s=r.scroller.scrollTop;if(!o||gt)return;i.options.resetSelectionOnContextMenu&&-1==i.doc.sel.contains(o)&&ns(i,rl)(i.doc,As(o),Kt);let l,a=n.style.cssText,c=t.wrapper.style.cssText,d=t.wrapper.offsetParent.getBoundingClientRect();function u(){if(null!=n.selectionStart){let e=i.somethingSelected(),o="​"+(e?n.value:"");n.value="⇚",n.value=o,t.prevInput=e?"":"​",n.selectionStart=1,n.selectionEnd=o.length,r.selForContextMenu=i.doc.sel}}function h(){if(t.contextMenuPending==h&&(t.contextMenuPending=!1,t.wrapper.style.cssText=c,n.style.cssText=a,ut&&ht<9&&r.scrollbars.setScrollTop(r.scroller.scrollTop=s),null!=n.selectionStart)){(!ut||ut&&ht<9)&&u();let e=0,o=()=>{r.selForContextMenu==i.doc.sel&&0==n.selectionStart&&n.selectionEnd>0&&"​"==t.prevInput?ns(i,ul)(i):e++<10?r.detectingSelectAll=setTimeout(o,500):(r.selForContextMenu=null,r.input.reset())};r.detectingSelectAll=setTimeout(o,200)}}if(t.wrapper.style.cssText="position: static",n.style.cssText=`position: absolute; width: 30px; height: 30px;\n      top: ${e.clientY-d.top-5}px; left: ${e.clientX-d.left-5}px;\n      z-index: 1000; background: ${ut?"rgba(255, 255, 255, .05)":"transparent"};\n      outline: none; border-width: 0; outline: none; overflow: hidden; opacity: .05; filter: alpha(opacity=5);`,pt&&(l=window.scrollY),r.input.focus(),pt&&window.scrollTo(null,l),r.input.reset(),i.somethingSelected()||(n.value=t.prevInput=" "),t.contextMenuPending=h,r.selForContextMenu=i.doc.sel,clearTimeout(r.detectingSelectAll),ut&&ht>=9&&u(),Et){Ei(e);let t=()=>{yi(window,"mouseup",t),setTimeout(h,20)};vi(window,"mouseup",t)}else setTimeout(h,50)}readOnlyChanged(e){e||this.reset(),this.textarea.disabled="nocursor"==e,this.textarea.readOnly=!!e}setUneditable(){}},Xa=Ka;Ka.prototype.needsContentAttribute=!1,function(e){let t=e.optionHandlers;function i(i,r,n,o){e.defaults[i]=r,n&&(t[i]=o?(e,t,i)=>{i!=ka&&n(e,t,i)}:n)}e.defineOption=i,e.Init=ka,i("value","",((e,t)=>e.setValue(t)),!0),i("mode",null,((e,t)=>{e.doc.modeOption=t,Is(e)}),!0),i("indentUnit",2,Is,!0),i("indentWithTabs",!1),i("smartIndent",!0),i("tabSize",4,(e=>{Ds(e),qn(e),vo(e)}),!0),i("lineSeparator",null,((e,t)=>{if(e.doc.lineSep=t,!t)return;let i=[],r=e.doc.first;e.doc.iter((e=>{for(let n=0;;){let o=e.text.indexOf(t,n);if(-1==o)break;n=o+t.length,i.push(or(r,o))}r++}));for(let r=i.length-1;r>=0;r--)bl(e.doc,t,i[r],or(i[r].line,i[r].ch+t.length))})),i("specialChars",/[\u0000-\u001f\u007f-\u009f\u00ad\u061c\u200b\u200e\u200f\u2028\u2029\ufeff\ufff9-\ufffc]/g,((e,t,i)=>{e.state.specialChars=new RegExp(t.source+(t.test("\t")?"":"|\t"),"g"),i!=ka&&e.refresh()})),i("specialCharPlaceholder",nn,(e=>e.refresh()),!0),i("electricChars",!0),i("inputStyle",wt?"contenteditable":"textarea",(()=>{throw new Error("inputStyle can not (yet) be changed in a running editor")}),!0),i("spellcheck",!1,((e,t)=>e.getInputField().spellcheck=t),!0),i("autocorrect",!1,((e,t)=>e.getInputField().autocorrect=t),!0),i("autocapitalize",!1,((e,t)=>e.getInputField().autocapitalize=t),!0),i("rtlMoveVisually",!Ct),i("wholeLineUpdateBefore",!0),i("theme","default",(e=>{wa(e),ys(e)}),!0),i("keyMap","default",((e,t,i)=>{let r=Zl(t),n=i!=ka&&Zl(i);n&&n.detach&&n.detach(e,r),r.attach&&r.attach(e,n||null)})),i("extraKeys",null),i("configureMouse",null),i("lineWrapping",!1,Ma,!0),i("gutters",[],((e,t)=>{e.display.gutterSpecs=vs(t,e.options.lineNumbers),ys(e)}),!0),i("fixedGutter",!0,((e,t)=>{e.display.gutters.style.left=t?ho(e.display)+"px":"0",e.refresh()}),!0),i("coverGutterNextToScrollbar",!1,(e=>qo(e)),!0),i("scrollbarStyle","native",(e=>{Ko(e),qo(e),e.display.scrollbars.setScrollTop(e.doc.scrollTop),e.display.scrollbars.setScrollLeft(e.doc.scrollLeft)}),!0),i("lineNumbers",!1,((e,t)=>{e.display.gutterSpecs=vs(e.options.gutters,t),ys(e)}),!0),i("firstLineNumber",1,ys,!0),i("lineNumberFormatter",(e=>e),ys,!0),i("showCursorWhenSelecting",!1,wo,!0),i("resetSelectionOnContextMenu",!0),i("lineWiseCopyCut",!0),i("pasteLinesPerSelection",!0),i("selectionsMayTouch",!1),i("readOnly",!1,((e,t)=>{"nocursor"==t&&(Po(e),e.display.input.blur()),e.display.input.readOnlyChanged(t)})),i("screenReaderLabel",null,((e,t)=>{t=""===t?null:t,e.display.input.screenReaderLabelChanged(t)})),i("disableInput",!1,((e,t)=>{t||e.display.input.reset()}),!0),i("dragDrop",!0,Ta),i("allowDropFileTypes",null),i("cursorBlinkRate",530),i("cursorScrollMargin",0),i("cursorHeight",1,wo,!0),i("singleCursorHeightPerLine",!0,wo,!0),i("workTime",100),i("workDelay",100),i("flattenSpans",!0,Ds,!0),i("addModeClass",!1,Ds,!0),i("pollInterval",100),i("undoDepth",200,((e,t)=>e.doc.history.undoDepth=t)),i("historyEventDelay",1250),i("viewportMargin",10,(e=>e.refresh()),!0),i("maxHighlightLength",1e4,Ds,!0),i("moveInputWithCursor",!0,((e,t)=>{t||e.display.input.resetPosition()})),i("tabindex",null,((e,t)=>e.display.input.getField().tabIndex=t||"")),i("autofocus",null),i("direction","ltr",((e,t)=>e.doc.setDirection(t)),!0),i("phrases",null)}(Ea),function(e){let t=e.optionHandlers,i=e.helpers={};e.prototype={constructor:e,focus:function(){window.focus(),this.display.input.focus()},setOption:function(e,i){let r=this.options,n=r[e];r[e]==i&&"mode"!=e||(r[e]=i,t.hasOwnProperty(e)&&ns(this,t[e])(this,i,n),_i(this,"optionChange",this,e))},getOption:function(e){return this.options[e]},getDoc:function(){return this.doc},addKeyMap:function(e,t){this.state.keyMaps[t?"push":"unshift"](Zl(e))},removeKeyMap:function(e){let t=this.state.keyMaps;for(let i=0;i<t.length;++i)if(t[i]==e||t[i].name==e)return t.splice(i,1),!0},addOverlay:os((function(t,i){let r=t.token?t:e.getMode(this.options,t);if(r.startState)throw new Error("Overlays may not be stateful.");!function(e,t,i){let r=0,n=i(t);for(;r<e.length&&i(e[r])<=n;)r++;e.splice(r,0,t)}(this.state.overlays,{mode:r,modeSpec:t,opaque:i&&i.opaque,priority:i&&i.priority||0},(e=>e.priority)),this.state.modeGen++,vo(this)})),removeOverlay:os((function(e){let t=this.state.overlays;for(let i=0;i<t.length;++i){let r=t[i].modeSpec;if(r==e||"string"==typeof e&&r.name==e)return t.splice(i,1),this.state.modeGen++,void vo(this)}})),indentLine:os((function(e,t,i){"string"!=typeof t&&"number"!=typeof t&&(t=null==t?this.options.smartIndent?"smart":"prev":t?"add":"subtract"),rr(this.doc,e)&&Pa(this,e,t,i)})),indentSelection:os((function(e){let t=this.doc.sel.ranges,i=-1;for(let r=0;r<t.length;r++){let n=t[r];if(n.empty())n.head.line>i&&(Pa(this,n.head.line,e,!0),i=n.head.line,r==this.doc.sel.primIndex&&$o(this));else{let o=n.from(),s=n.to(),l=Math.max(i,o.line);i=Math.min(this.lastLine(),s.line-(s.ch?0:1))+1;for(let t=l;t<i;++t)Pa(this,t,e);let a=this.doc.sel.ranges;0==o.ch&&t.length==a.length&&a[r].from().ch>0&&el(this.doc,r,new Ms(o,a[r].to()),Kt)}}})),getTokenAt:function(e,t){return kr(this,e,t)},getLineTokens:function(e,t){return kr(this,or(e),t,!0)},getTokenTypeAt:function(e){e=hr(this.doc,e);let t,i=vr(this,Zi(this.doc,e.line)),r=0,n=(i.length-1)/2,o=e.ch;if(0==o)t=i[2];else for(;;){let e=r+n>>1;if((e?i[2*e-1]:0)>=o)n=e;else{if(!(i[2*e+1]<o)){t=i[2*e+2];break}r=e+1}}let s=t?t.indexOf("overlay "):-1;return s<0?t:0==s?null:t.slice(0,s-1)},getModeAt:function(t){let i=this.doc.mode;return i.innerMode?e.innerMode(i,this.getTokenAt(t).state).mode:i},getHelper:function(e,t){return this.getHelpers(e,t)[0]},getHelpers:function(e,t){let r=[];if(!i.hasOwnProperty(t))return r;let n=i[t],o=this.getModeAt(e);if("string"==typeof o[t])n[o[t]]&&r.push(n[o[t]]);else if(o[t])for(let e=0;e<o[t].length;e++){let i=n[o[t][e]];i&&r.push(i)}else o.helperType&&n[o.helperType]?r.push(n[o.helperType]):n[o.name]&&r.push(n[o.name]);for(let e=0;e<n._global.length;e++){let t=n._global[e];t.pred(o,this)&&-1==qt(r,t.val)&&r.push(t.val)}return r},getStateAfter:function(e,t){let i=this.doc;return br(this,(e=ur(i,null==e?i.first+i.size-1:e))+1,t).state},cursorCoords:function(e,t){let i,r=this.doc.sel.primary();return i=null==e?r.head:"object"==typeof e?hr(this.doc,e):e?r.from():r.to(),Jn(this,i,t||"page")},charCoords:function(e,t){return Zn(this,hr(this.doc,e),t||"page")},coordsChar:function(e,t){return to(this,(e=Yn(this,e,t||"page")).left,e.top)},lineAtHeight:function(e,t){return e=Yn(this,{top:e,left:0},t||"page").top,ir(this.doc,e+this.display.viewOffset)},heightAtLine:function(e,t,i){let r,n=!1;if("number"==typeof e){let t=this.doc.first+this.doc.size-1;e<this.doc.first?e=this.doc.first:e>t&&(e=t,n=!0),r=Zi(this.doc,e)}else r=e;return Xn(this,r,{top:0,left:0},t||"page",i||n).top+(n?this.doc.height-Kr(r):0)},defaultTextHeight:function(){return ao(this.display)},defaultCharWidth:function(){return co(this.display)},getViewport:function(){return{from:this.display.viewFrom,to:this.display.viewTo}},addWidget:function(e,t,i,r,n){let o=this.display,s=(e=Jn(this,hr(this.doc,e))).bottom,l=e.left;if(t.style.position="absolute",t.setAttribute("cm-ignore-events","true"),this.display.input.setUneditable(t),o.sizer.appendChild(t),"over"==r)s=e.top;else if("above"==r||"near"==r){let i=Math.max(o.wrapper.clientHeight,this.doc.height),n=Math.max(o.sizer.clientWidth,o.lineSpace.clientWidth);("above"==r||e.bottom+t.offsetHeight>i)&&e.top>t.offsetHeight?s=e.top-t.offsetHeight:e.bottom+t.offsetHeight<=i&&(s=e.bottom),l+t.offsetWidth>n&&(l=n-t.offsetWidth)}t.style.top=s+"px",t.style.left=t.style.right="","right"==n?(l=o.sizer.clientWidth-t.offsetWidth,t.style.right="0px"):("left"==n?l=0:"middle"==n&&(l=(o.sizer.clientWidth-t.offsetWidth)/2),t.style.left=l+"px"),i&&function(e,t){let i=Do(e,t);null!=i.scrollTop&&Wo(e,i.scrollTop),null!=i.scrollLeft&&Uo(e,i.scrollLeft)}(this,{left:l,top:s,right:l+t.offsetWidth,bottom:s+t.offsetHeight})},triggerOnKeyDown:os(ua),triggerOnKeyPress:os(pa),triggerOnKeyUp:ha,triggerOnMouseDown:os(va),execCommand:function(e){if(ia.hasOwnProperty(e))return ia[e].call(null,this)},triggerElectric:os((function(e){Oa(this,e)})),findPosH:function(e,t,i,r){let n=1;t<0&&(n=-1,t=-t);let o=hr(this.doc,e);for(let e=0;e<t&&(o=Ba(this.doc,o,n,i,r),!o.hitSide);++e);return o},moveH:os((function(e,t){this.extendSelectionsBy((i=>this.display.shift||this.doc.extend||i.empty()?Ba(this.doc,i.head,e,t,this.options.rtlMoveVisually):e<0?i.from():i.to()),Yt)})),deleteH:os((function(e,t){let i=this.doc.sel,r=this.doc;i.somethingSelected()?r.replaceSelection("",null,"+delete"):Jl(this,(i=>{let n=Ba(r,i.head,e,t,!1);return e<0?{from:n,to:i.head}:{from:i.head,to:n}}))})),findPosV:function(e,t,i,r){let n=1,o=r;t<0&&(n=-1,t=-t);let s=hr(this.doc,e);for(let e=0;e<t;++e){let e=Jn(this,s,"div");if(null==o?o=e.left:e.left=o,s=Wa(this,e,n,i),s.hitSide)break}return s},moveV:os((function(e,t){let i=this.doc,r=[],n=!this.display.shift&&!i.extend&&i.sel.somethingSelected();if(i.extendSelectionsBy((o=>{if(n)return e<0?o.from():o.to();let s=Jn(this,o.head,"div");null!=o.goalColumn&&(s.left=o.goalColumn),r.push(s.left);let l=Wa(this,s,e,t);return"page"==t&&o==i.sel.primary()&&Oo(this,Zn(this,l,"div").top-s.top),l}),Yt),r.length)for(let e=0;e<i.sel.ranges.length;e++)i.sel.ranges[e].goalColumn=r[e]})),findWordAt:function(e){let t=Zi(this.doc,e.line).text,i=e.ch,r=e.ch;if(t){let n=this.getHelper(e,"wordChars");"before"!=e.sticky&&r!=t.length||!i?++r:--i;let o=t.charAt(i),s=si(o,n)?e=>si(e,n):/\s/.test(o)?e=>/\s/.test(e):e=>!/\s/.test(e)&&!si(e);for(;i>0&&s(t.charAt(i-1));)--i;for(;r<t.length&&s(t.charAt(r));)++r}return new Ms(or(e.line,i),or(e.line,r))},toggleOverwrite:function(e){null!=e&&e==this.state.overwrite||((this.state.overwrite=!this.state.overwrite)?zt(this.display.cursorDiv,"CodeMirror-overwrite"):Pt(this.display.cursorDiv,"CodeMirror-overwrite"),_i(this,"overwriteToggle",this,this.state.overwrite))},hasFocus:function(){return this.display.input.getField()==$t()},isReadOnly:function(){return!(!this.options.readOnly&&!this.doc.cantEdit)},scrollTo:os((function(e,t){zo(this,e,t)})),getScrollInfo:function(){let e=this.display.scroller;return{left:e.scrollLeft,top:e.scrollTop,height:e.scrollHeight-Pn(this)-this.display.barHeight,width:e.scrollWidth-Pn(this)-this.display.barWidth,clientHeight:Nn(this),clientWidth:Rn(this)}},scrollIntoView:os((function(e,t){null==e?(e={from:this.doc.sel.primary().head,to:null},null==t&&(t=this.options.cursorScrollMargin)):"number"==typeof e?e={from:or(e,0),to:null}:null==e.from&&(e={from:e,to:null}),e.to||(e.to=e.from),e.margin=t||0,null!=e.from.line?function(e,t){Fo(e),e.curOp.scrollToPos=t}(this,e):Bo(this,e.from,e.to,e.margin)})),setSize:os((function(e,t){let i=e=>"number"==typeof e||/^\d+$/.test(String(e))?e+"px":e;null!=e&&(this.display.wrapper.style.width=i(e)),null!=t&&(this.display.wrapper.style.height=i(t)),this.options.lineWrapping&&Vn(this);let r=this.display.viewFrom;this.doc.iter(r,this.display.viewTo,(e=>{if(e.widgets)for(let t=0;t<e.widgets.length;t++)if(e.widgets[t].noHScroll){bo(this,r,"widget");break}++r})),this.curOp.forceUpdate=!0,_i(this,"refresh",this)})),operation:function(e){return rs(this,e)},startOperation:function(){return Yo(this)},endOperation:function(){return Zo(this)},refresh:os((function(){let e=this.display.cachedTextHeight;vo(this),this.curOp.forceUpdate=!0,qn(this),zo(this,this.doc.scrollLeft,this.doc.scrollTop),ps(this.display),(null==e||Math.abs(e-ao(this.display))>.5||this.options.lineWrapping)&&mo(this),_i(this,"refresh",this)})),swapDoc:os((function(e){let t=this.doc;return t.cm=null,this.state.selectingText&&this.state.selectingText(),Fs(this,e),qn(this),this.display.input.reset(),zo(this,e.scrollLeft,e.scrollTop),this.curOp.forceScroll=!0,pn(this,"swapDoc",this,t),t})),phrase:function(e){let t=this.options.phrases;return t&&Object.prototype.hasOwnProperty.call(t,e)?t[e]:e},getInputField:function(){return this.display.input.getField()},getWrapperElement:function(){return this.display.wrapper},getScrollerElement:function(){return this.display.scroller},getGutterElement:function(){return this.display.gutters}},Si(e),e.registerHelper=function(t,r,n){i.hasOwnProperty(t)||(i[t]=e[t]={_global:[]}),i[t][r]=n},e.registerGlobalHelper=function(t,r,n,o){e.registerHelper(t,r,o),i[t]._global.push({pred:n,val:o})}}(Ea);var Ya,Za="iter insert remove copy getEditor constructor".split(" ");for(let e in Dl.prototype)Dl.prototype.hasOwnProperty(e)&&qt(Za,e)<0&&(Ea.prototype[e]=function(e){return function(){return e.apply(this.doc,arguments)}}(Dl.prototype[e]));Si(Dl),Ea.inputStyles={textarea:Xa,contenteditable:Ua},Ea.defineMode=function(e){Ea.defaults.mode||"null"==e||(Ea.defaults.mode=e),Hi.apply(this,arguments)},Ea.defineMIME=function(e,t){Wi[e]=t},Ea.defineMode("null",(()=>({token:e=>e.skipToEnd()}))),Ea.defineMIME("text/plain","null"),Ea.defineExtension=(e,t)=>{Ea.prototype[e]=t},Ea.defineDocExtension=(e,t)=>{Dl.prototype[e]=t},Ea.fromTextArea=function(e,t){if((t=t?Ht(t):{}).value=e.value,!t.tabindex&&e.tabIndex&&(t.tabindex=e.tabIndex),!t.placeholder&&e.placeholder&&(t.placeholder=e.placeholder),null==t.autofocus){let i=$t();t.autofocus=i==e||null!=e.getAttribute("autofocus")&&i==document.body}function i(){e.value=n.getValue()}let r;if(e.form&&(vi(e.form,"submit",i),!t.leaveSubmitMethodAlone)){let t=e.form;r=t.submit;try{let e=t.submit=()=>{i(),t.submit=r,t.submit(),t.submit=e}}catch(e){}}t.finishInit=n=>{n.save=i,n.getTextArea=()=>e,n.toTextArea=()=>{n.toTextArea=isNaN,i(),e.parentNode.removeChild(n.getWrapperElement()),e.style.display="",e.form&&(yi(e.form,"submit",i),t.leaveSubmitMethodAlone||"function"!=typeof e.form.submit||(e.form.submit=r))}},e.style.display="none";let n=Ea((t=>e.parentNode.insertBefore(t,e.nextSibling)),t);return n},(Ya=Ea).off=yi,Ya.on=vi,Ya.wheelEventPixels=Ss,Ya.Doc=Dl,Ya.splitLines=Oi,Ya.countColumn=Ut,Ya.findColumn=Zt,Ya.isWordChar=oi,Ya.Pass=Gt,Ya.signal=_i,Ya.Line=Zr,Ya.changeEnd=Ls,Ya.scrollbarModel=Go,Ya.Pos=or,Ya.cmpPos=sr,Ya.modes=Bi,Ya.mimeModes=Wi,Ya.resolveMode=Ui,Ya.getMode=Vi,Ya.modeExtensions=qi,Ya.extendMode=ji,Ya.copyState=Gi,Ya.startState=Xi,Ya.innerMode=Ki,Ya.commands=ia,Ya.keyMap=Vl,Ya.keyName=Yl,Ya.isModifierKey=Kl,Ya.lookupKey=Gl,Ya.normalizeKeyMap=jl,Ya.StringStream=Yi,Ya.SharedTextMarker=Ll,Ya.TextMarker=El,Ya.LineWidget=Cl,Ya.e_preventDefault=Ci,Ya.e_stopPropagation=Ti,Ya.e_stop=Ei,Ya.addClass=zt,Ya.contains=Ot,Ya.rmClass=Pt,Ya.keyNames=Ul,Ea.version="5.61.0";var Ja=Ea;self.CodeMirror=Ja;var Qa,ec=class extends HTMLElement{static get observedAttributes(){return["src","readonly","mode","theme"]}attributeChangedCallback(e,t,i){this.__initialized&&t!==i&&(this[e]="readonly"===e?null!==i:i)}get readonly(){return this.editor.getOption("readOnly")}set readonly(e){this.editor.setOption("readOnly",e)}get mode(){return this.editor.getOption("mode")}set mode(e){this.editor.setOption("mode",e)}get theme(){return this.editor.getOption("theme")}set theme(e){this.editor.setOption("theme",e)}get src(){return this.getAttribute("src")}set src(e){this.setAttribute("src",e),this.setSrc()}get value(){return this.editor.getValue()}set value(e){this.__initialized?this.setValueForced(e):this.__preInitValue=e}constructor(){super();const e=e=>"childList"===e.type&&(Array.from(e.addedNodes).some((e=>"LINK"===e.tagName))||Array.from(e.removedNodes).some((e=>"LINK"===e.tagName)));this.__observer=new MutationObserver(((t,i)=>{t.some(e)&&this.refreshStyles(),this.lookupInnerScript((e=>{this.value=e}))})),this.__observer.observe(this,{childList:!0,characterData:!0,subtree:!0}),this.__initialized=!1,this.__element=null,this.editor=null}async connectedCallback(){const e=this.attachShadow({mode:"open"}),t=document.createElement("template"),i=document.createElement("style");i.innerHTML="\n/* BASICS */\n\n.CodeMirror {\n  /* Set height, width, borders, and global font properties here */\n  font-family: monospace;\n  height: auto;\n  color: black;\n  direction: ltr;\n}\n\n/* PADDING */\n\n.CodeMirror-lines {\n  padding: 4px 0; /* Vertical padding around content */\n}\n.CodeMirror pre.CodeMirror-line,\n.CodeMirror pre.CodeMirror-line-like {\n  padding: 0 4px; /* Horizontal padding of content */\n}\n\n.CodeMirror-scrollbar-filler, .CodeMirror-gutter-filler {\n  background-color: white; /* The little square between H and V scrollbars */\n}\n\n/* GUTTER */\n\n.CodeMirror-gutters {\n  border-right: 1px solid #ddd;\n  background-color: #f7f7f7;\n  white-space: nowrap;\n}\n.CodeMirror-linenumbers {}\n.CodeMirror-linenumber {\n  padding: 0 3px 0 5px;\n  min-width: 20px;\n  text-align: right;\n  color: #999;\n  white-space: nowrap;\n}\n\n.CodeMirror-guttermarker { color: black; }\n.CodeMirror-guttermarker-subtle { color: #999; }\n\n/* CURSOR */\n\n.CodeMirror-cursor {\n  border-left: 1px solid black;\n  border-right: none;\n  width: 0;\n}\n/* Shown when moving in bi-directional text */\n.CodeMirror div.CodeMirror-secondarycursor {\n  border-left: 1px solid silver;\n}\n.cm-fat-cursor .CodeMirror-cursor {\n  width: auto;\n  border: 0 !important;\n  background: #7e7;\n}\n.cm-fat-cursor div.CodeMirror-cursors {\n  z-index: 1;\n}\n.cm-fat-cursor-mark {\n  background-color: rgba(20, 255, 20, 0.5);\n  -webkit-animation: blink 1.06s steps(1) infinite;\n  -moz-animation: blink 1.06s steps(1) infinite;\n  animation: blink 1.06s steps(1) infinite;\n}\n.cm-animate-fat-cursor {\n  width: auto;\n  border: 0;\n  -webkit-animation: blink 1.06s steps(1) infinite;\n  -moz-animation: blink 1.06s steps(1) infinite;\n  animation: blink 1.06s steps(1) infinite;\n  background-color: #7e7;\n}\n@-moz-keyframes blink {\n  0% {}\n  50% { background-color: transparent; }\n  100% {}\n}\n@-webkit-keyframes blink {\n  0% {}\n  50% { background-color: transparent; }\n  100% {}\n}\n@keyframes blink {\n  0% {}\n  50% { background-color: transparent; }\n  100% {}\n}\n\n/* Can style cursor different in overwrite (non-insert) mode */\n.CodeMirror-overwrite .CodeMirror-cursor {}\n\n.cm-tab { display: inline-block; text-decoration: inherit; }\n\n.CodeMirror-rulers {\n  position: absolute;\n  left: 0; right: 0; top: -50px; bottom: 0;\n  overflow: hidden;\n}\n.CodeMirror-ruler {\n  border-left: 1px solid #ccc;\n  top: 0; bottom: 0;\n  position: absolute;\n}\n\n/* DEFAULT THEME */\n\n.cm-s-default .cm-header {color: blue;}\n.cm-s-default .cm-quote {color: #090;}\n.cm-negative {color: #d44;}\n.cm-positive {color: #292;}\n.cm-header, .cm-strong {font-weight: bold;}\n.cm-em {font-style: italic;}\n.cm-link {text-decoration: underline;}\n.cm-strikethrough {text-decoration: line-through;}\n\n.cm-s-default .cm-keyword {color: #708;}\n.cm-s-default .cm-atom {color: #219;}\n.cm-s-default .cm-number {color: #164;}\n.cm-s-default .cm-def {color: #00f;}\n.cm-s-default .cm-variable,\n.cm-s-default .cm-punctuation,\n.cm-s-default .cm-property,\n.cm-s-default .cm-operator {}\n.cm-s-default .cm-variable-2 {color: #05a;}\n.cm-s-default .cm-variable-3, .cm-s-default .cm-type {color: #085;}\n.cm-s-default .cm-comment {color: #a50;}\n.cm-s-default .cm-string {color: #a11;}\n.cm-s-default .cm-string-2 {color: #f50;}\n.cm-s-default .cm-meta {color: #555;}\n.cm-s-default .cm-qualifier {color: #555;}\n.cm-s-default .cm-builtin {color: #30a;}\n.cm-s-default .cm-bracket {color: #997;}\n.cm-s-default .cm-tag {color: #170;}\n.cm-s-default .cm-attribute {color: #00c;}\n.cm-s-default .cm-hr {color: #999;}\n.cm-s-default .cm-link {color: #00c;}\n\n.cm-s-default .cm-error {color: #f00;}\n.cm-invalidchar {color: #f00;}\n\n.CodeMirror-composing { border-bottom: 2px solid; }\n\n/* Default styles for common addons */\n\ndiv.CodeMirror span.CodeMirror-matchingbracket {color: #0b0;}\ndiv.CodeMirror span.CodeMirror-nonmatchingbracket {color: #a22;}\n.CodeMirror-matchingtag { background: rgba(255, 150, 0, .3); }\n.CodeMirror-activeline-background {background: #e8f2ff;}\n\n/* STOP */\n\n/* The rest of this file contains styles related to the mechanics of\n    the editor. You probably shouldn't touch them. */\n\n.CodeMirror {\n  position: relative;\n  overflow: hidden;\n  background: white;\n}\n\n.CodeMirror-scroll {\n  overflow: scroll !important; /* Things will break if this is overridden */\n  /* 50px is the magic margin used to hide the element's real scrollbars */\n  /* See overflow: hidden in .CodeMirror */\n  margin-bottom: -50px; margin-right: -50px;\n  padding-bottom: 50px;\n  height: 100%;\n  outline: none; /* Prevent dragging from highlighting the element */\n  position: relative;\n}\n.CodeMirror-sizer {\n  position: relative;\n  border-right: 50px solid transparent;\n}\n\n/* The fake, visible scrollbars. Used to force redraw during scrolling\n    before actual scrolling happens, thus preventing shaking and\n    flickering artifacts. */\n.CodeMirror-vscrollbar, .CodeMirror-hscrollbar, .CodeMirror-scrollbar-filler, .CodeMirror-gutter-filler {\n  position: absolute;\n  z-index: 6;\n  display: none;\n}\n.CodeMirror-vscrollbar {\n  right: 0; top: 0;\n  overflow-x: hidden;\n  overflow-y: scroll;\n}\n.CodeMirror-hscrollbar {\n  bottom: 0; left: 0;\n  overflow-y: hidden;\n  overflow-x: scroll;\n}\n.CodeMirror-scrollbar-filler {\n  right: 0; bottom: 0;\n}\n.CodeMirror-gutter-filler {\n  left: 0; bottom: 0;\n}\n\n.CodeMirror-gutters {\n  position: absolute; left: 0; top: 0;\n  min-height: 100%;\n  z-index: 3;\n}\n.CodeMirror-gutter {\n  white-space: normal;\n  height: 100%;\n  display: inline-block;\n  vertical-align: top;\n  margin-bottom: -50px;\n}\n.CodeMirror-gutter-wrapper {\n  position: absolute;\n  z-index: 4;\n  background: none !important;\n  border: none !important;\n}\n.CodeMirror-gutter-background {\n  position: absolute;\n  top: 0; bottom: 0;\n  z-index: 4;\n}\n.CodeMirror-gutter-elt {\n  position: absolute;\n  cursor: default;\n  z-index: 4;\n}\n.CodeMirror-gutter-wrapper ::selection { background-color: transparent }\n.CodeMirror-gutter-wrapper ::-moz-selection { background-color: transparent }\n\n.CodeMirror-lines {\n  cursor: text;\n  min-height: 1px; /* prevents collapsing before first draw */\n}\n.CodeMirror pre.CodeMirror-line,\n.CodeMirror pre.CodeMirror-line-like {\n  /* Reset some styles that the rest of the page might have set */\n  -moz-border-radius: 0; -webkit-border-radius: 0; border-radius: 0;\n  border-width: 0;\n  background: transparent;\n  font-family: inherit;\n  font-size: inherit;\n  margin: 0;\n  white-space: pre;\n  word-wrap: normal;\n  line-height: inherit;\n  color: inherit;\n  z-index: 2;\n  position: relative;\n  overflow: visible;\n  -webkit-tap-highlight-color: transparent;\n  -webkit-font-variant-ligatures: contextual;\n  font-variant-ligatures: contextual;\n}\n.CodeMirror-wrap pre.CodeMirror-line,\n.CodeMirror-wrap pre.CodeMirror-line-like {\n  word-wrap: break-word;\n  white-space: pre-wrap;\n  word-break: normal;\n}\n\n.CodeMirror-linebackground {\n  position: absolute;\n  left: 0; right: 0; top: 0; bottom: 0;\n  z-index: 0;\n}\n\n.CodeMirror-linewidget {\n  position: relative;\n  z-index: 2;\n  padding: 0.1px; /* Force widget margins to stay inside of the container */\n}\n\n.CodeMirror-widget {}\n\n.CodeMirror-rtl pre { direction: rtl; }\n\n.CodeMirror-code {\n  outline: none;\n}\n\n/* Force content-box sizing for the elements where we expect it */\n.CodeMirror-scroll,\n.CodeMirror-sizer,\n.CodeMirror-gutter,\n.CodeMirror-gutters,\n.CodeMirror-linenumber {\n  -moz-box-sizing: content-box;\n  box-sizing: content-box;\n}\n\n.CodeMirror-measure {\n  position: absolute;\n  width: 100%;\n  height: 0;\n  overflow: hidden;\n  visibility: hidden;\n}\n\n.CodeMirror-cursor {\n  position: absolute;\n  pointer-events: none;\n}\n.CodeMirror-measure pre { position: static; }\n\ndiv.CodeMirror-cursors {\n  visibility: hidden;\n  position: relative;\n  z-index: 3;\n}\ndiv.CodeMirror-dragcursors {\n  visibility: visible;\n}\n\n.CodeMirror-focused div.CodeMirror-cursors {\n  visibility: visible;\n}\n\n.CodeMirror-selected { background: #d9d9d9; }\n.CodeMirror-focused .CodeMirror-selected { background: #d7d4f0; }\n.CodeMirror-crosshair { cursor: crosshair; }\n.CodeMirror-line::selection, .CodeMirror-line > span::selection, .CodeMirror-line > span > span::selection { background: #d7d4f0; }\n.CodeMirror-line::-moz-selection, .CodeMirror-line > span::-moz-selection, .CodeMirror-line > span > span::-moz-selection { background: #d7d4f0; }\n\n.cm-searching {\n  background-color: #ffa;\n  background-color: rgba(255, 255, 0, .4);\n}\n\n/* Used to force a border model for a node */\n.cm-force-border { padding-right: .1px; }\n\n@media print {\n  /* Hide the cursor when printing */\n  .CodeMirror div.CodeMirror-cursors {\n    visibility: hidden;\n  }\n}\n\n/* See issue #2901 */\n.cm-tab-wrap-hack:after { content: ''; }\n\n/* Help users use markselection to safely style text background */\nspan.CodeMirror-selectedtext { background: none; }\n",t.innerHTML=ec.template(),e.appendChild(i),e.appendChild(t.content.cloneNode(!0)),this.style.display="block",this.__element=e.querySelector("textarea");const r=this.hasAttribute("mode")?this.getAttribute("mode"):"null",n=this.hasAttribute("theme")?this.getAttribute("theme"):"default";let o=this.getAttribute("readonly");""===o?o=!0:"nocursor"!==o&&(o=!1),this.refreshStyles(),this.lookupInnerScript((e=>{this.value=e}));let s=Ja.defaults.viewportMargin;if(this.hasAttribute("viewport-margin")){const e=this.getAttribute("viewport-margin").toLowerCase();s="infinity"===e?1/0:parseInt(e)}this.editor=Ja.fromTextArea(this.__element,{lineNumbers:!0,readOnly:o,mode:r,theme:n,viewportMargin:s}),this.hasAttribute("src")&&this.setSrc(),await new Promise((e=>setTimeout(e,50))),this.__initialized=!0,void 0!==this.__preInitValue&&this.setValueForced(this.__preInitValue)}disconnectedCallback(){this.editor&&this.editor.toTextArea(),this.editor=null,this.__initialized=!1,this.__observer.disconnect()}async setSrc(){const e=this.getAttribute("src"),t=await this.fetchSrc(e);this.value=t}async setValueForced(e){this.editor.swapDoc(Ja.Doc(e,this.getAttribute("mode"))),this.editor.refresh()}async fetchSrc(e){return(await fetch(e)).text()}refreshStyles(){Array.from(this.shadowRoot.children).forEach((e=>{"LINK"===e.tagName&&"stylesheet"===e.getAttribute("rel")&&e.remove()})),Array.from(this.children).forEach((e=>{"LINK"===e.tagName&&"stylesheet"===e.getAttribute("rel")&&this.shadowRoot.appendChild(e.cloneNode(!0))}))}static template(){return'\n      <textarea style="display:inherit; width:inherit; height:inherit;"></textarea>\n    '}lookupInnerScript(e){const t=this.querySelector("script");if(t&&"wc-content"===t.getAttribute("type")){let i=ec.dedentText(t.innerHTML);i=i.replace(/&lt;(\/?script)(.*?)&gt;/g,"<$1$2>"),e(i)}}static dedentText(e){const t=e.split("\n");""===t[0]&&t.splice(0,1);const i=t[0];let r=0;const n="\t"===i[0]?"\t":" ";for(;i[r]===n;)r+=1;const o=[];for(const e of t){let t=e;for(let e=0;e<r&&t[0]===n;e++)t=t.substring(1);o.push(t)}return""===o[o.length-1]&&o.splice(o.length-1,1),o.join("\n")}};customElements.define("wc-codemirror",ec),Qa=function(e){function t(e){return new RegExp("^(("+e.join(")|(")+"))\\b")}var i,r=t(["and","or","not","is"]),n=["as","assert","break","class","continue","def","del","elif","else","except","finally","for","from","global","if","import","lambda","pass","raise","return","try","while","with","yield","in"],o=["abs","all","any","bin","bool","bytearray","callable","chr","classmethod","compile","complex","delattr","dict","dir","divmod","enumerate","eval","filter","float","format","frozenset","getattr","globals","hasattr","hash","help","hex","id","input","int","isinstance","issubclass","iter","len","list","locals","map","max","memoryview","min","next","object","oct","open","ord","pow","property","range","repr","reversed","round","set","setattr","slice","sorted","staticmethod","str","sum","super","tuple","type","vars","zip","__import__","NotImplemented","Ellipsis","__debug__"];function s(e){return e.scopes[e.scopes.length-1]}e.registerHelper("hintWords","python",n.concat(o)),e.defineMode("python",(function(i,l){for(var a="error",c=l.delimiters||l.singleDelimiters||/^[\(\)\[\]\{\}@,:`=;\.\\]/,d=[l.singleOperators,l.doubleOperators,l.doubleDelimiters,l.tripleDelimiters,l.operators||/^([-+*/%\/&|^]=?|[<>=]+|\/\/=?|\*\*=?|!=|[~!@]|\.\.\.)/],u=0;u<d.length;u++)d[u]||d.splice(u--,1);var h=l.hangingIndent||i.indentUnit,p=n,m=o;null!=l.extra_keywords&&(p=p.concat(l.extra_keywords)),null!=l.extra_builtins&&(m=m.concat(l.extra_builtins));var f=!(l.version&&Number(l.version)<3);if(f){var g=l.identifiers||/^[_A-Za-z\u00A1-\uFFFF][_A-Za-z0-9\u00A1-\uFFFF]*/;p=p.concat(["nonlocal","False","True","None","async","await"]),m=m.concat(["ascii","bytes","exec","print"]);var v=new RegExp("^(([rbuf]|(br)|(fr))?('{3}|\"{3}|['\"]))","i")}else g=l.identifiers||/^[_A-Za-z][_A-Za-z0-9]*/,p=p.concat(["exec","print"]),m=m.concat(["apply","basestring","buffer","cmp","coerce","execfile","file","intern","long","raw_input","reduce","reload","unichr","unicode","xrange","False","True","None"]),v=new RegExp("^(([rubf]|(ur)|(br))?('{3}|\"{3}|['\"]))","i");var b=t(p),y=t(m);function _(e,t){var i=e.sol()&&"\\"!=t.lastToken;if(i&&(t.indent=e.indentation()),i&&"py"==s(t).type){var r=s(t).offset;if(e.eatSpace()){var n=e.indentation();return n>r?w(t):n<r&&k(e,t)&&"#"!=e.peek()&&(t.errorToken=!0),null}var o=x(e,t);return r>0&&k(e,t)&&(o+=" "+a),o}return x(e,t)}function x(e,t,i){if(e.eatSpace())return null;if(!i&&e.match(/^#.*/))return"comment";if(e.match(/^[0-9\.]/,!1)){var n=!1;if(e.match(/^[\d_]*\.\d+(e[\+\-]?\d+)?/i)&&(n=!0),e.match(/^[\d_]+\.\d*/)&&(n=!0),e.match(/^\.\d+/)&&(n=!0),n)return e.eat(/J/i),"number";var o=!1;if(e.match(/^0x[0-9a-f_]+/i)&&(o=!0),e.match(/^0b[01_]+/i)&&(o=!0),e.match(/^0o[0-7_]+/i)&&(o=!0),e.match(/^[1-9][\d_]*(e[\+\-]?[\d_]+)?/)&&(e.eat(/J/i),o=!0),e.match(/^0(?![\dx])/i)&&(o=!0),o)return e.eat(/L/i),"number"}if(e.match(v))return-1!==e.current().toLowerCase().indexOf("f")?(t.tokenize=function(e,t){for(;"rubf".indexOf(e.charAt(0).toLowerCase())>=0;)e=e.substr(1);var i=1==e.length,r="string";function n(e){return function(t,i){var r=x(t,i,!0);return"punctuation"==r&&("{"==t.current()?i.tokenize=n(e+1):"}"==t.current()&&(i.tokenize=e>1?n(e-1):o)),r}}function o(o,s){for(;!o.eol();)if(o.eatWhile(/[^'"\{\}\\]/),o.eat("\\")){if(o.next(),i&&o.eol())return r}else{if(o.match(e))return s.tokenize=t,r;if(o.match("{{"))return r;if(o.match("{",!1))return s.tokenize=n(0),o.current()?r:s.tokenize(o,s);if(o.match("}}"))return r;if(o.match("}"))return a;o.eat(/['"]/)}if(i){if(l.singleLineStringErrors)return a;s.tokenize=t}return r}return o.isString=!0,o}(e.current(),t.tokenize),t.tokenize(e,t)):(t.tokenize=function(e,t){for(;"rubf".indexOf(e.charAt(0).toLowerCase())>=0;)e=e.substr(1);var i=1==e.length,r="string";function n(n,o){for(;!n.eol();)if(n.eatWhile(/[^'"\\]/),n.eat("\\")){if(n.next(),i&&n.eol())return r}else{if(n.match(e))return o.tokenize=t,r;n.eat(/['"]/)}if(i){if(l.singleLineStringErrors)return a;o.tokenize=t}return r}return n.isString=!0,n}(e.current(),t.tokenize),t.tokenize(e,t));for(var s=0;s<d.length;s++)if(e.match(d[s]))return"operator";return e.match(c)?"punctuation":"."==t.lastToken&&e.match(g)?"property":e.match(b)||e.match(r)?"keyword":e.match(y)?"builtin":e.match(/^(self|cls)\b/)?"variable-2":e.match(g)?"def"==t.lastToken||"class"==t.lastToken?"def":"variable":(e.next(),i?null:a)}function w(e){for(;"py"!=s(e).type;)e.scopes.pop();e.scopes.push({offset:s(e).offset+i.indentUnit,type:"py",align:null})}function k(e,t){for(var i=e.indentation();t.scopes.length>1&&s(t).offset>i;){if("py"!=s(t).type)return!0;t.scopes.pop()}return s(t).offset!=i}function S(e,t){e.sol()&&(t.beginningOfLine=!0);var i=t.tokenize(e,t),r=e.current();if(t.beginningOfLine&&"@"==r)return e.match(g,!1)?"meta":f?"operator":a;if(/\S/.test(r)&&(t.beginningOfLine=!1),"variable"!=i&&"builtin"!=i||"meta"!=t.lastToken||(i="meta"),"pass"!=r&&"return"!=r||(t.dedent+=1),"lambda"==r&&(t.lambda=!0),":"==r&&!t.lambda&&"py"==s(t).type&&e.match(/^\s*(?:#|$)/,!1)&&w(t),1==r.length&&!/string|comment/.test(i)){var n="[({".indexOf(r);if(-1!=n&&function(e,t,i){var r=e.match(/^[\s\[\{\(]*(?:#|$)/,!1)?null:e.column()+1;t.scopes.push({offset:t.indent+h,type:i,align:r})}(e,t,"])}".slice(n,n+1)),-1!=(n="])}".indexOf(r))){if(s(t).type!=r)return a;t.indent=t.scopes.pop().offset-h}}return t.dedent>0&&e.eol()&&"py"==s(t).type&&(t.scopes.length>1&&t.scopes.pop(),t.dedent-=1),i}return{startState:function(e){return{tokenize:_,scopes:[{offset:e||0,type:"py",align:null}],indent:e||0,lastToken:null,lambda:!1,dedent:0}},token:function(e,t){var i=t.errorToken;i&&(t.errorToken=!1);var r=S(e,t);return r&&"comment"!=r&&(t.lastToken="keyword"==r||"punctuation"==r?e.current():r),"punctuation"==r&&(r=null),e.eol()&&t.lambda&&(t.lambda=!1),i?r+" "+a:r},indent:function(t,i){if(t.tokenize!=_)return t.tokenize.isString?e.Pass:0;var r=s(t),n=r.type==i.charAt(0);return null!=r.align?r.align-(n?1:0):r.offset-(n?h:0)},electricInput:/^\s*[\}\]\)]$/,closeBrackets:{triples:"'\""},lineComment:"#",fold:"indent"}})),e.defineMIME("text/x-python","python"),e.defineMIME("text/x-cython",{name:"python",extra_keywords:(i="by cdef cimport cpdef ctypedef enum except extern gil include nogil property public readonly struct union DEF IF ELIF ELSE",i.split(" "))})},"object"==typeof exports&&"object"==typeof module?Qa(require("../../lib/codemirror")):"function"==typeof define&&define.amd?define(["../../lib/codemirror"],Qa):Qa(CodeMirror),function(e){"object"==typeof exports&&"object"==typeof module?e(require("../../lib/codemirror")):"function"==typeof define&&define.amd?define(["../../lib/codemirror"],e):e(CodeMirror)}((function(e){e.defineMode("shell",(function(){var t={};function i(e,i){for(var r=0;r<i.length;r++)t[i[r]]=e}var r=["true","false"],n=["if","then","do","else","elif","while","until","for","in","esac","fi","fin","fil","done","exit","set","unset","export","function"],o=["ab","awk","bash","beep","cat","cc","cd","chown","chmod","chroot","clear","cp","curl","cut","diff","echo","find","gawk","gcc","get","git","grep","hg","kill","killall","ln","ls","make","mkdir","openssl","mv","nc","nl","node","npm","ping","ps","restart","rm","rmdir","sed","service","sh","shopt","shred","source","sort","sleep","ssh","start","stop","su","sudo","svn","tee","telnet","top","touch","vi","vim","wall","wc","wget","who","write","yes","zsh"];function s(e,i){if(e.eatSpace())return null;var r,n=e.sol(),o=e.next();if("\\"===o)return e.next(),null;if("'"===o||'"'===o||"`"===o)return i.tokens.unshift(l(o,"`"===o?"quote":"string")),d(e,i);if("#"===o)return n&&e.eat("!")?(e.skipToEnd(),"meta"):(e.skipToEnd(),"comment");if("$"===o)return i.tokens.unshift(c),d(e,i);if("+"===o||"="===o)return"operator";if("-"===o)return e.eat("-"),e.eatWhile(/\w/),"attribute";if("<"==o){if(e.match("<<"))return"operator";var s=e.match(/^<-?\s*['"]?([^'"]*)['"]?/);if(s)return i.tokens.unshift((r=s[1],function(e,t){return e.sol()&&e.string==r&&t.tokens.shift(),e.skipToEnd(),"string-2"})),"string-2"}if(/\d/.test(o)&&(e.eatWhile(/\d/),e.eol()||!/\w/.test(e.peek())))return"number";e.eatWhile(/[\w-]/);var a=e.current();return"="===e.peek()&&/\w+/.test(a)?"def":t.hasOwnProperty(a)?t[a]:null}function l(e,t){var i="("==e?")":"{"==e?"}":e;return function(r,n){for(var o,s=!1;null!=(o=r.next());){if(o===i&&!s){n.tokens.shift();break}if("$"===o&&!s&&"'"!==e&&r.peek()!=i){s=!0,r.backUp(1),n.tokens.unshift(c);break}if(!s&&e!==i&&o===e)return n.tokens.unshift(l(e,t)),d(r,n);if(!s&&/['"]/.test(o)&&!/['"]/.test(e)){n.tokens.unshift(a(o,"string")),r.backUp(1);break}s=!s&&"\\"===o}return t}}function a(e,t){return function(i,r){return r.tokens[0]=l(e,t),i.next(),d(i,r)}}e.registerHelper("hintWords","shell",r.concat(n,o)),i("atom",r),i("keyword",n),i("builtin",o);var c=function(e,t){t.tokens.length>1&&e.eat("$");var i=e.next();return/['"({]/.test(i)?(t.tokens[0]=l(i,"("==i?"quote":"{"==i?"def":"string"),d(e,t)):(/\d/.test(i)||e.eatWhile(/\w/),t.tokens.shift(),"def")};function d(e,t){return(t.tokens[0]||s)(e,t)}return{startState:function(){return{tokens:[]}},token:function(e,t){return d(e,t)},closeBrackets:"()[]{}''\"\"``",lineComment:"#",fold:"brace"}})),e.defineMIME("text/x-sh","shell"),e.defineMIME("application/x-sh","shell")})),function(e){"object"==typeof exports&&"object"==typeof module?e(require("../../lib/codemirror")):"function"==typeof define&&define.amd?define(["../../lib/codemirror"],e):e(CodeMirror)}((function(e){e.defineMode("yaml",(function(){var e=new RegExp("\\b(("+["true","false","on","off","yes","no"].join(")|(")+"))$","i");return{token:function(t,i){var r=t.peek(),n=i.escaped;if(i.escaped=!1,"#"==r&&(0==t.pos||/\s/.test(t.string.charAt(t.pos-1))))return t.skipToEnd(),"comment";if(t.match(/^('([^']|\\.)*'?|"([^"]|\\.)*"?)/))return"string";if(i.literal&&t.indentation()>i.keyCol)return t.skipToEnd(),"string";if(i.literal&&(i.literal=!1),t.sol()){if(i.keyCol=0,i.pair=!1,i.pairStart=!1,t.match("---"))return"def";if(t.match("..."))return"def";if(t.match(/\s*-\s+/))return"meta"}if(t.match(/^(\{|\}|\[|\])/))return"{"==r?i.inlinePairs++:"}"==r?i.inlinePairs--:"["==r?i.inlineList++:i.inlineList--,"meta";if(i.inlineList>0&&!n&&","==r)return t.next(),"meta";if(i.inlinePairs>0&&!n&&","==r)return i.keyCol=0,i.pair=!1,i.pairStart=!1,t.next(),"meta";if(i.pairStart){if(t.match(/^\s*(\||\>)\s*/))return i.literal=!0,"meta";if(t.match(/^\s*(\&|\*)[a-z0-9\._-]+\b/i))return"variable-2";if(0==i.inlinePairs&&t.match(/^\s*-?[0-9\.\,]+\s?$/))return"number";if(i.inlinePairs>0&&t.match(/^\s*-?[0-9\.\,]+\s?(?=(,|}))/))return"number";if(t.match(e))return"keyword"}return!i.pair&&t.match(/^\s*(?:[,\[\]{}&*!|>'"%@`][^\s'":]|[^,\[\]{}#&*!|>'"%@`])[^#]*?(?=\s*:($|\s))/)?(i.pair=!0,i.keyCol=t.indentation(),"atom"):i.pair&&t.match(/^:\s*/)?(i.pairStart=!0,"meta"):(i.pairStart=!1,i.escaped="\\"==r,t.next(),null)},startState:function(){return{pair:!1,pairStart:!1,keyCol:0,inlinePairs:0,inlineList:0,literal:!1,escaped:!1}},lineComment:"#",fold:"indent"}})),e.defineMIME("text/x-yaml","yaml"),e.defineMIME("text/yaml","yaml")}));let tc=class extends b{constructor(){super(),this.config=Object(),this.mode="shell",this.theme="monokai",this.src="",this.readonly=!1,this.useLineWrapping=!1,this.required=!1,this.validationMessage="",this.validationMessageIcon="warning",this.config={tabSize:2,indentUnit:2,cursorScrollMargin:50,lineNumbers:!0,matchBrackets:!0,styleActiveLine:!0,viewportMargin:1/0,extraKeys:{}}}firstUpdated(){this._initEditor()}_initEditor(){this.editorEl.__initialized?(this.editor=this.editorEl.editor,Object.assign(this.editor.options,this.config),this.editor.setOption("lineWrapping",this.useLineWrapping),this.refresh()):setTimeout(this._initEditor.bind(this),100)}refresh(){globalThis.setTimeout((()=>this.editor.refresh()),100)}focus(){globalThis.setTimeout((()=>{this.editor.execCommand("goDocEnd"),this.editor.focus(),this.refresh()}),100)}getValue(){return this.editor.getValue()}setValue(e){this.editor.setValue(e),this.refresh()}_validateInput(){if(this.required){if(""===this.getValue())return this.showValidationMessage(),this.editorEl.style.border="2px solid red",!1;this.hideValidationMessage(),this.editorEl.style.border="none"}return!0}showValidationMessage(){this.validationMessageEl.style.display="flex"}hideValidationMessage(){this.validationMessageEl.style.display="none"}static get styles(){return[y,_,x,nt,rt,S`
        .CodeMirror {
          height: auto !important;
          font-size: 15px;
        }

        #validation-message {
          font-size: var(--validation-message-font-size, 12px);
          color: var(--validation-message-color, var(--general-warning-text));
          width: var(--validation-message-width, 100%);
          font-weight: var(--validation-message-font-weight, bold);
        }

        #validation-message mwc-icon {
          font-size: var(--validation-message-font-size, 12px);
          margin-right: 2px;
        }
      `]}render(){return C`
      <div>
        <wc-codemirror
          id="codemirror-editor"
          mode="${this.mode}"
          theme="monokai"
          ?readonly="${this.readonly}"
          @input="${()=>this._validateInput()}"
        >
          <link
            rel="stylesheet"
            href="node_modules/@vanillawc/wc-codemirror/theme/monokai.css"
          />
        </wc-codemirror>
        <div
          id="validation-message"
          class="horizontal layout center"
          style="display:none;"
        >
          <mwc-icon>${this.validationMessageIcon}</mwc-icon>
          <span>${this.validationMessage}</span>
        </div>
      </div>
    `}};o([f({type:Object})],tc.prototype,"config",void 0),o([f({type:String})],tc.prototype,"mode",void 0),o([f({type:String})],tc.prototype,"theme",void 0),o([f({type:String})],tc.prototype,"src",void 0),o([f({type:Boolean})],tc.prototype,"readonly",void 0),o([f({type:Boolean})],tc.prototype,"useLineWrapping",void 0),o([f({type:Boolean})],tc.prototype,"required",void 0),o([f({type:String})],tc.prototype,"validationMessage",void 0),o([f({type:String})],tc.prototype,"validationMessageIcon",void 0),o([g("#validation-message")],tc.prototype,"validationMessageEl",void 0),o([g("#codemirror-editor")],tc.prototype,"editorEl",void 0),tc=o([v("lablup-codemirror")],tc),
/**
 * @license
 * Copyright (c) 2017 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
T("vaadin-text-field",M,{moduleId:"lumo-text-field-styles"});
/**
 * @license
 * Copyright (c) 2021 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const ic=e=>class extends(E(e)){static get properties(){return{autocomplete:{type:String},autocorrect:{type:String},autocapitalize:{type:String,reflectToAttribute:!0}}}static get delegateAttrs(){return[...super.delegateAttrs,"autocapitalize","autocomplete","autocorrect"]}get __data(){return this.__dataValue||{}}set __data(e){this.__dataValue=e}_inputElementChanged(e){super._inputElementChanged(e),e&&(e.value&&e.value!==this.value&&(console.warn(`Please define value on the <${this.localName}> component!`),e.value=""),this.value&&(e.value=this.value))}_setFocused(e){super._setFocused(e),!e&&document.hasFocus()&&this.validate()}_onInput(e){super._onInput(e),this.invalid&&this.validate()}_valueChanged(e,t){super._valueChanged(e,t),void 0!==t&&this.invalid&&this.validate()}}
/**
 * @license
 * Copyright (c) 2021 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,rc=e=>class extends(ic(e)){static get properties(){return{maxlength:{type:Number},minlength:{type:Number},pattern:{type:String}}}static get delegateAttrs(){return[...super.delegateAttrs,"maxlength","minlength","pattern"]}static get constraints(){return[...super.constraints,"maxlength","minlength","pattern"]}constructor(){super(),this._setType("text")}get clearElement(){return this.$.clearButton}ready(){super.ready(),this.addController(new A(this,(e=>{this._setInputElement(e),this._setFocusElement(e),this.stateTarget=e,this.ariaTarget=e}))),this.addController(new L(this.inputElement,this._labelController))}}
/**
 * @license
 * Copyright (c) 2017 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;T("vaadin-text-field",P,{moduleId:"vaadin-text-field-styles"});class nc extends(rc(D(O($)))){static get is(){return"vaadin-text-field"}static get template(){return R`
      <div class="vaadin-field-container">
        <div part="label">
          <slot name="label"></slot>
          <span part="required-indicator" aria-hidden="true" on-click="focus"></span>
        </div>

        <vaadin-input-container
          part="input-field"
          readonly="[[readonly]]"
          disabled="[[disabled]]"
          invalid="[[invalid]]"
          theme$="[[_theme]]"
        >
          <slot name="prefix" slot="prefix"></slot>
          <slot name="input"></slot>
          <slot name="suffix" slot="suffix"></slot>
          <div id="clearButton" part="clear-button" slot="suffix" aria-hidden="true"></div>
        </vaadin-input-container>

        <div part="helper-text">
          <slot name="helper"></slot>
        </div>

        <div part="error-message">
          <slot name="error-message"></slot>
        </div>
      </div>
      <slot name="tooltip"></slot>
    `}static get properties(){return{maxlength:{type:Number},minlength:{type:Number}}}ready(){super.ready(),this._tooltipController=new N(this),this._tooltipController.setPosition("top"),this._tooltipController.setAriaTarget(this.inputElement),this.addController(this._tooltipController)}}I(nc),
/**
 * @license
 * Copyright (c) 2016 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
T("vaadin-grid-filter",S`
    :host {
      display: inline-flex;
      max-width: 100%;
    }

    ::slotted(*) {
      width: 100%;
      box-sizing: border-box;
    }
  `,{moduleId:"vaadin-grid-filter-styles"});const oc=e=>class extends(z(e)){static get properties(){return{path:{type:String,sync:!0},value:{type:String,notify:!0,sync:!0},_textField:{type:Object,sync:!0}}}static get observers(){return["_filterChanged(path, value, _textField)"]}ready(){super.ready(),this._filterController=new F(this,"","vaadin-text-field",{initializer:e=>{e.addEventListener("input",(e=>{this.value=e.target.value})),this._textField=e}}),this.addController(this._filterController)}_filterChanged(e,t,i){void 0!==e&&void 0!==t&&i&&(i.value=t,this._debouncerFilterChanged=B.debounce(this._debouncerFilterChanged,W.after(200),(()=>{this.dispatchEvent(new CustomEvent("filter-changed",{bubbles:!0}))})))}focus(){this._textField&&this._textField.focus()}}
/**
 * @license
 * Copyright (c) 2016 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;class sc extends(oc(D($))){static get template(){return R`<slot></slot>`}static get is(){return"vaadin-grid-filter"}}I(sc);
/**
 * @license
 * Copyright (c) 2016 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const lc=e=>class extends e{static get properties(){return{path:{type:String,sync:!0},header:{type:String,sync:!0}}}static get observers(){return["_onHeaderRendererOrBindingChanged(_headerRenderer, _headerCell, path, header)"]}_defaultHeaderRenderer(e,t){let i=e.firstElementChild,r=i?i.firstElementChild:void 0;i||(i=document.createElement("vaadin-grid-filter"),r=document.createElement("vaadin-text-field"),r.setAttribute("theme","small"),r.setAttribute("style","max-width: 100%;"),r.setAttribute("focus-target",""),i.appendChild(r),e.appendChild(i)),i.path=this.path,r.label=this.__getHeader(this.header,this.path)}_computeHeaderRenderer(){return this._defaultHeaderRenderer}__getHeader(e,t){return e||(t?this._generateHeader(t):void 0)}}
/**
 * @license
 * Copyright (c) 2016 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;class ac extends(lc(H)){static get is(){return"vaadin-grid-filter-column"}}I(ac);let cc=class extends U{constructor(){super(),this.is_connected=!1,this.enableLaunchButton=!1,this.hideLaunchButton=!1,this.hideEnvDialog=!1,this.hidePreOpenPortDialog=!1,this.enableInferenceWorkload=!1,this.location="",this.mode="normal",this.newSessionDialogTitle="",this.importScript="",this.importFilename="",this.imageRequirements=Object(),this.resourceLimits=Object(),this.userResourceLimit=Object(),this.aliases=Object(),this.tags=Object(),this.icons=Object(),this.imageInfo=Object(),this.kernel="",this.marker_limit=25,this.gpu_modes=[],this.gpu_step=.1,this.cpu_metric={min:"1",max:"1"},this.mem_metric={min:"1",max:"1"},this.shmem_metric={min:.0625,max:1,preferred:.0625},this.npu_device_metric={min:0,max:0},this.rocm_device_metric={min:"0",max:"0"},this.tpu_device_metric={min:"1",max:"1"},this.ipu_device_metric={min:"0",max:"0"},this.atom_device_metric={min:"0",max:"0"},this.atom_plus_device_metric={min:"0",max:"0"},this.gaudi2_device_metric={min:"0",max:"0"},this.warboy_device_metric={min:"0",max:"0"},this.rngd_device_metric={min:"0",max:"0"},this.hyperaccel_lpu_device_metric={min:"0",max:"0"},this.cluster_metric={min:1,max:1},this.cluster_mode_list=["single-node","multi-node"],this.cluster_support=!1,this.folderMapping=Object(),this.customFolderMapping=Object(),this.aggregate_updating=!1,this.resourceGauge=Object(),this.sessionType="interactive",this.ownerFeatureInitialized=!1,this.ownerDomain="",this.project_resource_monitor=!1,this._default_language_updated=!1,this._default_version_updated=!1,this._helpDescription="",this._helpDescriptionTitle="",this._helpDescriptionIcon="",this._NPUDeviceNameOnSlider="GPU",this.max_cpu_core_per_session=128,this.max_mem_per_container=1536,this.max_cuda_device_per_container=16,this.max_cuda_shares_per_container=16,this.max_rocm_device_per_container=10,this.max_tpu_device_per_container=8,this.max_ipu_device_per_container=8,this.max_atom_device_per_container=4,this.max_atom_plus_device_per_container=4,this.max_gaudi2_device_per_container=4,this.max_warboy_device_per_container=4,this.max_rngd_device_per_container=4,this.max_hyperaccel_lpu_device_per_container=4,this.max_shm_per_container=8,this.allow_manual_image_name_for_session=!1,this.cluster_size=1,this.deleteEnvInfo=Object(),this.deleteEnvRow=Object(),this.environ_values=Object(),this.vfolder_select_expansion=Object(),this.currentIndex=1,this._nonAutoMountedFolderGrid=Object(),this._modelFolderGrid=Object(),this._debug=!1,this._boundFolderToMountListRenderer=this.folderToMountListRenderer.bind(this),this._boundFolderMapRenderer=this.folderMapRenderer.bind(this),this._boundPathRenderer=this.infoHeaderRenderer.bind(this),this.scheduledTime="",this.sessionInfoObj={environment:"",version:[""]},this.launchButtonMessageTextContent=V("session.launcher.Launch"),this.isExceedMaxCountForPreopenPorts=!1,this.maxCountForPreopenPorts=10,this.allowCustomResourceAllocation=!0,this.allowNEOSessionLauncher=!1,this.active=!1,this.ownerKeypairs=[],this.ownerGroups=[],this.ownerScalingGroups=[],this.resourceBroker=globalThis.resourceBroker,this.notification=globalThis.lablupNotification,this.environ=[],this.preOpenPorts=[],this.init_resource()}static get is(){return"backend-ai-session-launcher"}static get styles(){return[y,_,x,w,k,S`
        h5,
        p,
        span {
          color: var(--token-colorText);
        }

        .slider-list-item {
          padding: 0;
        }

        hr.separator {
          border-top: 1px solid var(--token-colorBorder, #ddd);
        }

        lablup-slider {
          width: 350px !important;
          --textfield-min-width: 135px;
          --slider-width: 210px;
        }

        lablup-progress-bar {
          --progress-bar-width: 100%;
          --progress-bar-height: 10px;
          --progress-bar-border-radius: 0px;
          height: 100%;
          width: 100%;
          --progress-bar-background: var(--general-progress-bar-using);
          /* transition speed for progress bar */
          --progress-bar-transition-second: 0.1s;
          margin: 0;
        }

        vaadin-grid {
          max-height: 335px;
          margin-left: 20px;
        }

        .alias {
          max-width: 145px;
        }

        .progress {
          // padding-top: 15px;
          position: relative;
          z-index: 12;
          display: none;
        }

        .progress.active {
          display: block;
        }

        .resources.horizontal .short-indicator mwc-linear-progress {
          width: 50px;
        }

        .resources.horizontal .short-indicator .gauge-label {
          width: 50px;
        }

        span.caption {
          width: 30px;
          display: block;
          font-size: 12px;
          padding-left: 10px;
          font-weight: 300;
        }

        div.caption {
          font-size: 12px;
          width: 100px;
        }

        img.resource-type-icon {
          width: 24px;
          height: 24px;
        }

        mwc-list-item.resource-type {
          font-size: 14px;
          font-weight: 500;
          height: 20px;
          padding: 5px;
        }

        mwc-slider {
          width: 200px;
        }

        div.vfolder-list,
        div.vfolder-mounted-list,
        #mounted-folders-container,
        .environment-variables-container,
        .preopen-ports-container,
        mwc-select h5 {
          background-color: var(
            --token-colorBgElevated,
            rgba(244, 244, 244, 1)
          );
          color: var(--token-colorText);
          overflow-y: scroll;
        }

        div.vfolder-list,
        div.vfolder-mounted-list {
          max-height: 335px;
        }

        .environment-variables-container,
        .preopen-ports-container {
          font-size: 0.8rem;
          padding: 10px;
        }

        .environment-variables-container mwc-textfield input,
        .preopen-ports-container mwc-textfield input {
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .environment-variables-container mwc-textfield,
        .preopen-ports-container mwc-textfield {
          --mdc-text-field-fill-color: var(--token-colorBgElevated);
          --mdc-text-field-disabled-fill-color: var(--token-colorBgElevated);
          --mdc-text-field-disabled-line-color: var(--token-colorBorder);
        }

        .resources.horizontal .monitor.session {
          margin-left: 5px;
        }

        .gauge-name {
          font-size: 10px;
        }

        .gauge-label {
          width: 100px;
          font-weight: 300;
          font-size: 12px;
        }

        .indicator {
          font-family: monospace;
        }
        .cluster-total-allocation-container {
          border-radius: 10px;
          border: 1px dotted
            var(--token-colorBorder, --general-button-background-color);
          padding-top: 10px;
          margin-left: 15px;
          margin-right: 15px;
        }

        .resource-button {
          height: 140px;
          width: 330px;
          margin: 5px;
          padding: 0;
          font-size: 14px;
        }

        .resource-allocated {
          width: 45px;
          height: 60px;
          font-size: 16px;
          margin: 5px;
          opacity: 1;
          z-index: 11;
        }

        .resource-allocated > p {
          margin: 0 auto;
          font-size: 8px;
        }
        .resource-allocated-box {
          z-index: 10;
          position: relative;
        }
        .resource-allocated-box-shadow {
          position: relative;
          z-index: 1;
          top: -65px;
          height: 200px;
          width: 70px;
          opacity: 1;
        }

        .cluster-allocated {
          min-width: 40px;
          min-height: 40px;
          width: auto;
          height: 70px;
          border-radius: 5px;
          font-size: 1rem;
          margin: 5px;
          padding: 0px 5px;
          background-color: var(--general-button-background-color);
          line-height: 1.2em;
        }

        .cluster-allocated > div.horizontal > p {
          font-size: 1rem;
          margin: 0px;
          line-height: 1.2em;
        }

        .cluster-allocated > p.small {
          font-size: 8px;
          margin: 0px;
          margin-top: 0.5em;
          text-align: center;
          line-height: 1.2em;
        }

        .cluster-allocated {
          p,
          span {
            color: var(--token-colorWhite);
          }
        }

        .resource-allocated > span,
        .cluster-allocated > div.horizontal > span {
          font-weight: bolder;
        }

        .allocation-check {
          margin-bottom: 10px;
        }

        .resource-allocated-box {
          border-radius: 5px;
          margin: 5px;
          z-index: 10;
        }

        #new-session-dialog {
          --component-width: 400px;
          --component-height: 640px;
          --component-max-height: 640px;
          z-index: 100;
        }

        .resource-button.iron-selected {
          --button-color: var(--paper-red-600);
          --button-bg: var(--paper-red-600);
          --button-bg-active: var(--paper-red-600);
          --button-bg-hover: var(--paper-red-600);
          --button-bg-active-flat: var(--paper-orange-50);
          --button-bg-flat: var(--paper-orange-50);
        }

        .resource-button h4 {
          padding: 5px 0;
          margin: 0;
          font-weight: 400;
        }

        .resource-button ul {
          padding: 0;
          list-style-type: none;
        }

        #launch-session {
          width: var(--component-width, auto);
          height: var(--component-height, 36px);
        }

        #launch-session-form {
          height: calc(var(--component-height, auto) - 157px);
        }

        lablup-expansion {
          --expansion-elevation: 0;
          --expansion-elevation-open: 0;
          --expansion-elevation-hover: 0;
          --expansion-header-padding: 16px;
          --expansion-margin-open: 0;
          --expansion-header-font-weight: normal;
          --expansion-header-font-size: 14px;
          --expansion-header-font-color: var(
            --token-colorText,
            rgb(64, 64, 64)
          );
          --expansion-background-color: var(--token-colorBgElevated);
          --expansion-header-background-color: var(--token-colorBgElevated);
        }

        lablup-expansion.vfolder,
        lablup-expansion.editor {
          --expansion-content-padding: 0;
          border-bottom: 1px;
        }

        lablup-expansion[name='resource-group'] {
          --expansion-content-padding: 0 16px;
        }

        .resources .monitor {
          margin-right: 5px;
        }

        .resources.vertical .monitor {
          margin-bottom: 10px;
        }

        .resources.vertical .monitor div:first-child {
          width: 40px;
        }

        vaadin-date-time-picker {
          width: 370px;
          margin-bottom: 10px;
        }

        lablup-codemirror {
          width: 370px;
        }

        mwc-select {
          width: 100%;
          --mdc-list-side-padding: 15px;
          --mdc-list-item__primary-text: {
            height: 20px;
          };
          /* Need to be set when fixedMenuPosition attribute is enabled */
          --mdc-menu-max-width: 400px;
          --mdc-menu-min-width: 400px;
        }

        mwc-select#owner-group,
        mwc-select#owner-scaling-group {
          margin-right: 0;
          padding-right: 0;
          width: 50%;
          --mdc-menu-max-width: 200px;
          --mdc-select-min-width: 190px;
          --mdc-menu-min-width: 200px;
        }

        mwc-textfield {
          width: 100%;
        }

        mwc-textfield#session-name {
          margin-bottom: 1px;
        }

        mwc-button,
        mwc-button[raised],
        mwc-button[unelevated],
        mwc-button[disabled] {
          width: 100%;
        }

        mwc-checkbox {
          --mdc-theme-secondary: var(--general-checkbox-color);
        }

        mwc-checkbox#hide-guide {
          margin-right: 10px;
        }

        #prev-button,
        #next-button {
          color: var(--token-colorPrimary, #27824f);
        }

        #environment {
          --mdc-menu-item-height: 40px;
          max-height: 300px;
        }

        #version {
          --mdc-menu-item-height: 35px;
        }

        #vfolder {
          width: 100%;
        }

        #vfolder-header-title {
          text-align: center;
          font-size: 16px;
          font-family: var(--token-fontFamily);
          font-weight: 500;
        }

        #help-description {
          --component-width: 350px;
        }

        #help-description p {
          padding: 5px !important;
        }

        #launch-confirmation-dialog,
        #env-config-confirmation,
        #preopen-ports-config-confirmation {
          --component-width: 400px;
          --component-font-size: 14px;
        }

        mwc-icon-button.info {
          --mdc-icon-button-size: 30px;
          color: var(--token-colorTextSecondary);
        }

        mwc-icon {
          --mdc-icon-size: 13px;
          margin-right: 2px;
          vertical-align: middle;
        }

        #error-icon {
          width: 24px;
          --mdc-icon-size: 24px;
          margin-right: 10px;
        }

        ul {
          list-style-type: none;
        }

        ul.vfolder-list {
          color: #646464;
          font-size: 12px;
          max-height: inherit;
        }

        ul.vfolder-list > li {
          max-width: 90%;
          display: block;
          text-overflow: ellipsis;
          white-space: nowrap;
          overflow: hidden;
        }

        p.title {
          padding: 15px 15px 0px;
          margin-top: 0;
          font-size: 12px;
          font-weight: 200;
          color: var(--token-colorTextTertiary, #404040);
        }

        #progress-04 p.title {
          font-weight: 400;
        }

        #batch-mode-config-section {
          width: 100%;
          border-bottom: solid 1px var(--token-colorBorder, rgba(0, 0, 0, 0.42));
          margin-bottom: 15px;
        }

        .allocation-shadow {
          height: 70px;
          width: 200px;
          position: absolute;
          top: -5px;
          left: 5px;
          border: 1px solid var(--token-colorBorder, #ccc);
        }

        #modify-env-dialog,
        #modify-preopen-ports-dialog {
          --component-max-height: 550px;
          --component-width: 400px;
        }

        #modify-env-dialog div.container,
        #modify-preopen-ports-dialog div.container {
          display: flex;
          flex-direction: column;
          padding: 0px 30px;
        }

        #modify-env-dialog div.row,
        #modify-env-dialog div.header {
          display: grid;
          grid-template-columns: 4fr 4fr 1fr;
        }

        #modify-env-dialog div[slot='footer'],
        #modify-preopen-ports-dialog div[slot='footer'] {
          display: flex;
          margin-left: auto;
          gap: 15px;
        }

        #modify-env-container mwc-textfield,
        #modify-preopen-ports-dialog mwc-textfield {
          width: 90%;
          margin: auto 5px;
        }

        #env-add-btn,
        #preopen-ports-add-btn {
          margin: 20px auto 10px auto;
        }

        .delete-all-button {
          --mdc-theme-primary: var(--paper-red-600);
        }

        .minus-btn {
          --mdc-icon-size: 20px;
          color: var(--token-colorPrimary, #27824f);
        }

        .environment-variables-container h4,
        .preopen-ports-container h4 {
          margin: 0;
        }

        .environment-variables-container mwc-textfield,
        .preopen-ports-container mwc-textfield {
          --mdc-typography-subtitle1-font-family: var(--token-fontFamily);
          --mdc-text-field-disabled-ink-color: var(--token-colorText);
        }

        .optional-buttons {
          margin: auto 12px;
        }

        .optional-buttons mwc-button {
          width: 50%;
          --mdc-typography-button-font-size: 0.5vw;
        }

        #launch-button-msg {
          color: var(--token-colorWhite);
        }

        [name='resource-group'] mwc-list-item {
          --mdc-ripple-color: transparent;
        }

        @media screen and (max-width: 400px) {
          backend-ai-dialog {
            --component-min-width: 350px;
          }
        }

        @media screen and (max-width: 750px) {
          mwc-button > mwc-icon {
            display: inline-block;
          }
        }

        /* Fading animation */
        .fade {
          -webkit-animation-name: fade;
          -webkit-animation-duration: 1s;
          animation-name: fade;
          animation-duration: 1s;
        }

        @-webkit-keyframes fade {
          from {
            opacity: 0.7;
          }
          to {
            opacity: 1;
          }
        }

        @keyframes fade {
          from {
            opacity: 0.7;
          }
          to {
            opacity: 1;
          }
        }
        #launch-button {
          font-size: 14px;
        }
      `]}init_resource(){this.versions=["Not Selected"],this.languages=[],this.gpu_mode="none",this.total_slot={},this.total_resource_group_slot={},this.total_project_slot={},this.used_slot={},this.used_resource_group_slot={},this.used_project_slot={},this.available_slot={},this.used_slot_percent={},this.used_resource_group_slot_percent={},this.used_project_slot_percent={},this.resource_templates=[],this.resource_templates_filtered=[],this.vfolders=[],this.selectedVfolders=[],this.nonAutoMountedVfolders=[],this.modelVfolders=[],this.autoMountedVfolders=[],this.default_language="",this.concurrency_used=0,this.concurrency_max=0,this.concurrency_limit=2,this.max_containers_per_session=1,this._status="inactive",this.cpu_request=1,this.mem_request=1,this.shmem_request=.0625,this.gpu_request=0,this.gpu_request_type="cuda.device",this.session_request=1,this.scaling_groups=[{name:""}],this.scaling_group="",this.sessions_list=[],this.metric_updating=!1,this.metadata_updating=!1,this.cluster_size=1,this.cluster_mode="single-node",this.ownerFeatureInitialized=!1,this.ownerDomain="",this.ownerKeypairs=[],this.ownerGroups=[],this.ownerScalingGroups=[]}firstUpdated(){var e,t,i,r,n,o;this.environment.addEventListener("selected",this.updateLanguage.bind(this)),this.version_selector.addEventListener("selected",(()=>{this.updateResourceAllocationPane()})),null===(e=this.shadowRoot)||void 0===e||e.querySelectorAll("lablup-expansion").forEach((e=>{e.addEventListener("keydown",(e=>{e.stopPropagation()}),!0)})),this.resourceGauge=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#resource-gauges"),document.addEventListener("backend-ai-group-changed",(()=>{this._updatePageVariables(!0)})),document.addEventListener("backend-ai-resource-broker-updated",(()=>{})),!0===this.hideLaunchButton&&((null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#launch-session")).style.display="none"),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.max_cpu_core_per_session=globalThis.backendaiclient._config.maxCPUCoresPerContainer||128,this.max_mem_per_container=globalThis.backendaiclient._config.maxMemoryPerContainer||1536,this.max_cuda_device_per_container=globalThis.backendaiclient._config.maxCUDADevicesPerContainer||16,this.max_cuda_shares_per_container=globalThis.backendaiclient._config.maxCUDASharesPerContainer||16,this.max_rocm_device_per_container=globalThis.backendaiclient._config.maxROCMDevicesPerContainer||10,this.max_tpu_device_per_container=globalThis.backendaiclient._config.maxTPUDevicesPerContainer||8,this.max_ipu_device_per_container=globalThis.backendaiclient._config.maxIPUDevicesPerContainer||8,this.max_atom_device_per_container=globalThis.backendaiclient._config.maxATOMDevicesPerContainer||8,this.max_atom_plus_device_per_container=globalThis.backendaiclient._config.maxATOMPlUSDevicesPerContainer||8,this.max_gaudi2_device_per_container=globalThis.backendaiclient._config.maxGaudi2DevicesPerContainer||8,this.max_warboy_device_per_container=globalThis.backendaiclient._config.maxWarboyDevicesPerContainer||8,this.max_rngd_device_per_container=globalThis.backendaiclient._config.maxRNGDDevicesPerContainer||8,this.max_hyperaccel_lpu_device_per_container=globalThis.backendaiclient._config.maxHyperaccelLPUDevicesPerContainer||8,this.max_shm_per_container=globalThis.backendaiclient._config.maxShmPerContainer||8,void 0!==globalThis.backendaiclient._config.allow_manual_image_name_for_session&&"allow_manual_image_name_for_session"in globalThis.backendaiclient._config&&""!==globalThis.backendaiclient._config.allow_manual_image_name_for_session?this.allow_manual_image_name_for_session=globalThis.backendaiclient._config.allow_manual_image_name_for_session:this.allow_manual_image_name_for_session=!1,globalThis.backendaiclient.supports("multi-container")&&(this.cluster_support=!0),this.maxCountForPreopenPorts=globalThis.backendaiclient._config.maxCountForPreopenPorts,this.allowCustomResourceAllocation=globalThis.backendaiclient._config.allowCustomResourceAllocation,this.is_connected=!0,this._debug=globalThis.backendaiwebui.debug,this._enableLaunchButton()}),{once:!0}):(this.max_cpu_core_per_session=globalThis.backendaiclient._config.maxCPUCoresPerContainer||128,this.max_mem_per_container=globalThis.backendaiclient._config.maxMemoryPerContainer||1536,this.max_cuda_device_per_container=globalThis.backendaiclient._config.maxCUDADevicesPerContainer||16,this.max_cuda_shares_per_container=globalThis.backendaiclient._config.maxCUDASharesPerContainer||16,this.max_rocm_device_per_container=globalThis.backendaiclient._config.maxROCMDevicesPerContainer||10,this.max_tpu_device_per_container=globalThis.backendaiclient._config.maxTPUDevicesPerContainer||8,this.max_ipu_device_per_container=globalThis.backendaiclient._config.maxIPUDevicesPerContainer||8,this.max_atom_device_per_container=globalThis.backendaiclient._config.maxATOMDevicesPerContainer||8,this.max_atom_plus_device_per_container=globalThis.backendaiclient._config.maxATOMPlUSDevicesPerContainer||8,this.max_gaudi2_device_per_container=globalThis.backendaiclient._config.maxGaudi2DevicesPerContainer||8,this.max_warboy_device_per_container=globalThis.backendaiclient._config.maxWarboyDevicesPerContainer||8,this.max_rngd_device_per_container=globalThis.backendaiclient._config.maxRNGDDevicesPerContainer||8,this.max_hyperaccel_lpu_device_per_container=globalThis.backendaiclient._config.maxHyperaccelLPUDevicesPerContainer||8,this.max_shm_per_container=globalThis.backendaiclient._config.maxShmPerContainer||8,void 0!==globalThis.backendaiclient._config.allow_manual_image_name_for_session&&"allow_manual_image_name_for_session"in globalThis.backendaiclient._config&&""!==globalThis.backendaiclient._config.allow_manual_image_name_for_session?this.allow_manual_image_name_for_session=globalThis.backendaiclient._config.allow_manual_image_name_for_session:this.allow_manual_image_name_for_session=!1,globalThis.backendaiclient.supports("multi-container")&&(this.cluster_support=!0),this.maxCountForPreopenPorts=globalThis.backendaiclient._config.maxCountForPreopenPorts,this.allowCustomResourceAllocation=globalThis.backendaiclient._config.allowCustomResourceAllocation,this.is_connected=!0,this._debug=globalThis.backendaiwebui.debug,this._enableLaunchButton()),this.modifyEnvDialog.addEventListener("dialog-closing-confirm",(e=>{var t;const i={},r=null===(t=this.modifyEnvContainer)||void 0===t?void 0:t.querySelectorAll(".row");Array.prototype.filter.call(r,(e=>(e=>Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>0===e.value.length)).length<=1)(e))).map((e=>(e=>{const t=Array.prototype.map.call(e.querySelectorAll("mwc-textfield"),(e=>e.value));return i[t[0]]=t[1],t})(e)));((e,t)=>{const i=Object.getOwnPropertyNames(e),r=Object.getOwnPropertyNames(t);if(i.length!=r.length)return!1;for(let r=0;r<i.length;r++){const n=i[r];if(e[n]!==t[n])return!1}return!0})(i,this.environ_values)?(this.modifyEnvDialog.closeWithConfirmation=!1,this.closeDialog("modify-env-dialog")):(this.hideEnvDialog=!0,this.openDialog("env-config-confirmation"))})),this.modifyPreOpenPortDialog.addEventListener("dialog-closing-confirm",(()=>{var e;const t=null===(e=this.modifyPreOpenPortContainer)||void 0===e?void 0:e.querySelectorAll(".row:not(.header) mwc-textfield");((e,t)=>e.length===t.length&&e.every(((e,i)=>e===t[i])))(Array.from(t).filter((e=>""!==e.value)).map((e=>e.value)),this.preOpenPorts)?(this.modifyPreOpenPortDialog.closeWithConfirmation=!1,this.closeDialog("modify-preopen-ports-dialog")):(this.hidePreOpenPortDialog=!0,this.openDialog("preopen-ports-config-confirmation"))})),this.currentIndex=1,this.progressLength=null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelectorAll(".progress").length,this._nonAutoMountedFolderGrid=null===(n=this.shadowRoot)||void 0===n?void 0:n.querySelector("#non-auto-mounted-folder-grid"),this._modelFolderGrid=null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("#model-folder-grid"),globalThis.addEventListener("resize",(()=>{document.body.dispatchEvent(new Event("click"))}))}_enableLaunchButton(){this.resourceBroker.image_updating?(this.enableLaunchButton=!1,setTimeout((()=>{this._enableLaunchButton()}),1e3)):("inference"===this.mode?this.languages=this.resourceBroker.languages.filter((e=>""!==e.name&&"INFERENCE"===this.resourceBroker.imageRoles[e.name])):this.languages=this.resourceBroker.languages.filter((e=>""===e.name||"COMPUTE"===this.resourceBroker.imageRoles[e.name])),this.enableLaunchButton=!0)}_updateSelectedScalingGroup(){this.scaling_groups=this.resourceBroker.scaling_groups;const e=this.scalingGroups.items.find((e=>e.value===this.resourceBroker.scaling_group));if(""===this.resourceBroker.scaling_group||void 0===e)return void setTimeout((()=>{this._updateSelectedScalingGroup()}),500);const t=this.scalingGroups.items.indexOf(e);this.scalingGroups.select(-1),this.scalingGroups.select(t),this.scalingGroups.value=e.value,this.scalingGroups.requestUpdate()}async updateScalingGroup(e=!1,t){this.active&&(await this.resourceBroker.updateScalingGroup(e,t.target.value),!0===e?await this._refreshResourcePolicy():await this.updateResourceAllocationPane("session dialog"))}_initializeFolderMapping(){var e;this.folderMapping={};(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll(".alias")).forEach((e=>{e.value=""}))}async _updateSelectedFolder(e=!1){var t,i,r;if(this._nonAutoMountedFolderGrid&&this._nonAutoMountedFolderGrid.selectedItems){let n=this._nonAutoMountedFolderGrid.selectedItems;n=n.concat(this._modelFolderGrid.selectedItems);let o=[];n.length>0&&(o=n.map((e=>e.name)),e&&this._unselectAllSelectedFolder()),this.selectedVfolders=o;for(const e of this.selectedVfolders){if((null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#vfolder-alias-"+e)).value.length>0&&(this.folderMapping[e]=(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#vfolder-alias-"+e)).value),e in this.folderMapping&&this.selectedVfolders.includes(this.folderMapping[e]))return delete this.folderMapping[e],(null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector("#vfolder-alias-"+e)).value="",await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!0)}}return Promise.resolve(!0)}_unselectAllSelectedFolder(){[this._nonAutoMountedFolderGrid,this._modelFolderGrid].forEach((e=>{e&&e.selectedItems&&(e.selectedItems.forEach((e=>{e.selected=!1})),e.selectedItems=[])})),this.selectedVfolders=[]}_checkSelectedItems(){[this._nonAutoMountedFolderGrid,this._modelFolderGrid].forEach((e=>{if(e&&e.selectedItems){const t=e.selectedItems;let i=[];t.length>0&&(e.selectedItems=[],i=t.map((e=>null==e?void 0:e.id)),e.querySelectorAll("vaadin-checkbox").forEach((e=>{var t;i.includes(null===(t=e.__item)||void 0===t?void 0:t.id)&&(e.checked=!0)})))}}))}_preProcessingSessionInfo(){var e,t;let i,r;if(null===(e=this.manualImageName)||void 0===e?void 0:e.value){const e=this.manualImageName.value.split(":");i=e[0],r=e.slice(-1)[0].split("-")}else{if(void 0===this.kernel||!1!==(null===(t=this.version_selector)||void 0===t?void 0:t.disabled))return!1;i=this.kernel,r=this.version_selector.selectedText.split("/")}return this.sessionInfoObj.environment=i.split("/").pop(),this.sessionInfoObj.version=[r[0].toUpperCase()].concat(1!==r.length?r.slice(1).map((e=>e.toUpperCase())):[""]),!0}async _viewStateChanged(){if(await this.updateComplete,!this.active)return;const e=()=>{this.enableInferenceWorkload=globalThis.backendaiclient.supports("inference-workload")};void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.project_resource_monitor=this.resourceBroker.allow_project_resource_monitor,this._updatePageVariables(!0),this._disableEnterKey(),e()}),{once:!0}):(this.project_resource_monitor=this.resourceBroker.allow_project_resource_monitor,await this._updatePageVariables(!0),this._disableEnterKey(),e())}async _updatePageVariables(e){this.active&&!1===this.metadata_updating&&(this.metadata_updating=!0,await this.resourceBroker._updatePageVariables(e),this._updateSelectedScalingGroup(),this.sessions_list=this.resourceBroker.sessions_list,await this._refreshResourcePolicy(),this.aggregateResource("update-page-variable"),this.metadata_updating=!1)}async _refreshResourcePolicy(){return this.resourceBroker._refreshResourcePolicy().then((()=>{var e;this.concurrency_used=this.resourceBroker.concurrency_used,this.userResourceLimit=this.resourceBroker.userResourceLimit,this.concurrency_max=this.resourceBroker.concurrency_max,this.max_containers_per_session=null!==(e=this.resourceBroker.max_containers_per_session)&&void 0!==e?e:1,this.gpu_mode=this.resourceBroker.gpu_mode,this.gpu_step=this.resourceBroker.gpu_step,this.gpu_modes=this.resourceBroker.gpu_modes,this.updateResourceAllocationPane("refresh resource policy")})).catch((e=>{this.metadata_updating=!1,e&&e.message?(this.notification.text=q.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=q.relieve(e.title),this.notification.show(!0,e))}))}async _launchSessionDialog(){var e;const t=!globalThis.backendaioptions.get("classic_session_launcher",!1);if(!0===this.allowNEOSessionLauncher&&t){const e="/session/start?formValues="+encodeURIComponent(JSON.stringify({resourceGroup:this.resourceBroker.scaling_group}));return j.dispatch(G(decodeURIComponent(e),{})),void document.dispatchEvent(new CustomEvent("react-navigate",{detail:e}))}if(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready||!0===this.resourceBroker.image_updating)setTimeout((()=>{this._launchSessionDialog()}),1e3);else{this.folderMapping=Object(),this._resetProgress(),await this.selectDefaultLanguage();const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector('lablup-expansion[name="ownership"]');globalThis.backendaiclient.is_admin?t.style.display="block":t.style.display="none",this._updateSelectedScalingGroup(),await this._refreshResourcePolicy(),this.requestUpdate(),this.newSessionDialog.show()}}_generateKernelIndex(e,t){return e+":"+t}_moveToLastProgress(){this.moveProgress(4)}_newSessionWithConfirmation(){var e,t,i,r;const n=null===(t=null===(e=this._nonAutoMountedFolderGrid)||void 0===e?void 0:e.selectedItems)||void 0===t?void 0:t.map((e=>e.name)).length,o=null===(r=null===(i=this._modelFolderGrid)||void 0===i?void 0:i.selectedItems)||void 0===r?void 0:r.map((e=>e.name)).length;if(this.currentIndex==this.progressLength){if("inference"===this.mode||void 0!==n&&n>0||void 0!==o&&o>0)return this._newSession();this.launchConfirmationDialog.show()}else this._moveToLastProgress()}_newSession(){var e,t,i,r,n,o,s,l,a,c,d,u;let h,p,m;if(this.launchConfirmationDialog.hide(),this.manualImageName&&this.manualImageName.value){const e=this.manualImageName.value.split(":");p=e.splice(-1,1)[0],h=e.join(":"),m=["x86_64","aarch64"].includes(this.manualImageName.value.split("@").pop())?this.manualImageName.value.split("@").pop():void 0,m&&(h=this.manualImageName.value.split("@")[0])}else{const o=this.environment.selected;h=null!==(e=null==o?void 0:o.id)&&void 0!==e?e:"",p=null!==(i=null===(t=this.version_selector.selected)||void 0===t?void 0:t.value)&&void 0!==i?i:"",m=null!==(n=null===(r=this.version_selector.selected)||void 0===r?void 0:r.getAttribute("architecture"))&&void 0!==n?n:void 0}this.sessionType=(null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("#session-type")).value;let f=(null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#session-name")).value;const g=(null===(l=this.shadowRoot)||void 0===l?void 0:l.querySelector("#session-name")).checkValidity();let v=this.selectedVfolders;if(this.cpu_request=parseInt(this.cpuResourceSlider.value),this.mem_request=parseFloat(this.memoryResourceSlider.value),this.shmem_request=parseFloat(this.sharedMemoryResourceSlider.value),this.gpu_request=parseFloat(this.npuResourceSlider.value),this.session_request=parseInt(this.sessionResourceSlider.value),this.num_sessions=this.session_request,this.sessions_list.includes(f))return this.notification.text=V("session.launcher.DuplicatedSessionName"),void this.notification.show();if(!g)return this.notification.text=V("session.launcher.SessionNameAllowCondition"),void this.notification.show();if(""===h||""===p||"Not Selected"===p)return this.notification.text=V("session.launcher.MustSpecifyVersion"),void this.notification.show();this.scaling_group=this.scalingGroups.value;const b={};b.group_name=globalThis.backendaiclient.current_group,b.domain=globalThis.backendaiclient._config.domainName,b.scaling_group=this.scaling_group,b.type=this.sessionType,globalThis.backendaiclient.supports("multi-container")&&(b.cluster_mode=this.cluster_mode,b.cluster_size=this.cluster_size),b.maxWaitSeconds=15;const y=null===(a=this.shadowRoot)||void 0===a?void 0:a.querySelector("#owner-enabled");if(y&&y.checked&&(b.group_name=this.ownerGroupSelect.value,b.domain=this.ownerDomain,b.scaling_group=this.ownerScalingGroupSelect.value,b.owner_access_key=this.ownerAccesskeySelect.value,!(b.group_name&&b.domain&&b.scaling_group&&b.owner_access_key)))return this.notification.text=V("session.launcher.NotEnoughOwnershipInfo"),void this.notification.show();switch(b.cpu=this.cpu_request,this.gpu_request_type){case"cuda.shares":b["cuda.shares"]=this.gpu_request;break;case"cuda.device":b["cuda.device"]=this.gpu_request;break;case"rocm.device":b["rocm.device"]=this.gpu_request;break;case"tpu.device":b["tpu.device"]=this.gpu_request;break;case"ipu.device":b["ipu.device"]=this.gpu_request;break;case"atom.device":b["atom.device"]=this.gpu_request;break;case"atom-plus.device":b["atom-plus.device"]=this.gpu_request;break;case"gaudi2.device":b["gaudi2.device"]=this.gpu_request;break;case"warboy.device":b["warboy.device"]=this.gpu_request;break;case"rngd.device":b["rngd.device"]=this.gpu_request;break;case"hyperaccel-lpu.device":b["hyperaccel-lpu.device"]=this.gpu_request;break;default:this.gpu_request>0&&this.gpu_mode&&(b[this.gpu_mode]=this.gpu_request)}let _;"Infinity"===String(this.memoryResourceSlider.value)?b.mem=String(this.memoryResourceSlider.value):b.mem=String(this.mem_request)+"g",this.shmem_request>this.mem_request&&(this.shmem_request=this.mem_request,this.notification.text=V("session.launcher.SharedMemorySettingIsReduced"),this.notification.show()),this.mem_request>4&&this.shmem_request<1&&(this.shmem_request=1),b.shmem=String(this.shmem_request)+"g",0==f.length&&(f=this.generateSessionId()),_=this._debug&&""!==this.manualImageName.value||this.manualImageName&&""!==this.manualImageName.value?m?h:this.manualImageName.value:this._generateKernelIndex(h,p);let x={};if("inference"===this.mode){if(!(_ in this.resourceBroker.imageRuntimeConfig)||!("model-path"in this.resourceBroker.imageRuntimeConfig[_]))return this.notification.text=V("session.launcher.ImageDoesNotProvideModelPath"),void this.notification.show();v=Object.keys(this.customFolderMapping),x[v]=this.resourceBroker.imageRuntimeConfig[_]["model-path"]}else x=this.folderMapping;if(0!==v.length&&(b.mounts=v,0!==Object.keys(x).length)){b.mount_map={};for(const e in x)({}).hasOwnProperty.call(x,e)&&(x[e].startsWith("/")?b.mount_map[e]=x[e]:b.mount_map[e]="/home/work/"+x[e])}if("import"===this.mode&&""!==this.importScript&&(b.bootstrap_script=this.importScript),"batch"===this.sessionType&&(b.startupCommand=this.commandEditor.getValue(),this.scheduledTime&&(b.startsAt=this.scheduledTime)),this.environ_values&&0!==Object.keys(this.environ_values).length&&(b.env=this.environ_values),this.preOpenPorts.length>0&&(b.preopen_ports=[...new Set(this.preOpenPorts.map((e=>Number(e))))]),!1===this.openMPSwitch.selected){const e=(null===(c=this.shadowRoot)||void 0===c?void 0:c.querySelector("#OpenMPCore")).value,t=(null===(d=this.shadowRoot)||void 0===d?void 0:d.querySelector("#OpenBLASCore")).value;b.env=null!==(u=b.env)&&void 0!==u?u:{},b.env.OMP_NUM_THREADS=e?Math.max(0,parseInt(e)).toString():"1",b.env.OPENBLAS_NUM_THREADS=t?Math.max(0,parseInt(t)).toString():"1"}this.launchButton.disabled=!0,this.launchButtonMessageTextContent=V("session.Preparing"),this.notification.text=V("session.PreparingSession"),this.notification.show();const w=[],k=this._getRandomString();if(this.num_sessions>1)for(let e=1;e<=this.num_sessions;e++){const t={kernelName:_,sessionName:`${f}-${k}-${e}`,architecture:m,config:b};w.push(t)}else w.push({kernelName:_,sessionName:f,architecture:m,config:b});const S=w.map((e=>this.tasker.add(V("general.Session")+": "+e.sessionName,this._createKernel(e.kernelName,e.sessionName,e.architecture,e.config),"","session","",V("eduapi.CreatingComputeSession"),V("eduapi.ComputeSessionPrepared"),!0)));Promise.all(S).then((e=>{var t;this.newSessionDialog.hide(),this.launchButton.disabled=!1,this.launchButtonMessageTextContent=V("session.launcher.ConfirmAndLaunch"),this._resetProgress(),setTimeout((()=>{this.metadata_updating=!0,this.aggregateResource("session-creation"),this.metadata_updating=!1}),1500);const i=new CustomEvent("backend-ai-session-list-refreshed",{detail:"running"});document.dispatchEvent(i),1===e.length&&"batch"!==this.sessionType&&(null===(t=e[0])||void 0===t||t.taskobj.then((e=>{let t;t="kernelId"in e?{"session-name":e.kernelId,"access-key":"",mode:this.mode}:{"session-uuid":e.sessionId,"session-name":e.sessionName,"access-key":"",mode:this.mode};const i=e.servicePorts;!0===Array.isArray(i)?t["app-services"]=i.map((e=>e.name)):t["app-services"]=[],"import"===this.mode&&(t.runtime="jupyter",t.filename=this.importFilename),"inference"===this.mode&&(t.runtime=t["app-services"].find((e=>!["ttyd","sshd"].includes(e)))),i.length>0&&globalThis.appLauncher.showLauncher(t)})).catch((e=>{}))),this._updateSelectedFolder(!1),this._initializeFolderMapping()})).catch((e=>{e&&e.message?(this.notification.text=q.relieve(e.message),e.description?this.notification.text=q.relieve(e.description):this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=q.relieve(e.title),this.notification.show(!0,e));const t=new CustomEvent("backend-ai-session-list-refreshed",{detail:"running"});document.dispatchEvent(t),this.launchButton.disabled=!1,this.launchButtonMessageTextContent=V("session.launcher.ConfirmAndLaunch")}))}_getRandomString(){let e=Math.floor(52*Math.random()*52*52);let t="";for(let r=0;r<3;r++)t+=(i=e%52)<26?String.fromCharCode(65+i):String.fromCharCode(97+i-26),e=Math.floor(e/52);var i;return t}_createKernel(e,t,i,r){const n=globalThis.backendaiclient.createIfNotExists(e,t,r,3e4,i);return n.then((e=>{(null==e?void 0:e.created)||(this.notification.text=V("session.launcher.SessionAlreadyExists"),this.notification.show())})).catch((e=>{e&&e.message?("statusCode"in e&&408===e.statusCode?this.notification.text=V("session.launcher.SessionStillPreparing"):e.description?this.notification.text=q.relieve(e.description):this.notification.text=q.relieve(e.message),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=q.relieve(e.title),this.notification.show(!0,e))})),n}_hideSessionDialog(){this.newSessionDialog.hide()}_aliasName(e){const t=this.resourceBroker.imageTagAlias,i=this.resourceBroker.imageTagReplace;for(const[t,r]of Object.entries(i)){const i=new RegExp(t);if(i.test(e))return e.replace(i,r)}return e in t?t[e]:e}_updateVersions(e){if(e in this.resourceBroker.supports){{this.version_selector.disabled=!0;const t=[];for(const i of this.resourceBroker.supports[e])for(const r of this.resourceBroker.imageArchitectures[e+":"+i])t.push({version:i,architecture:r});t.sort(((e,t)=>e.version>t.version?1:-1)),t.reverse(),this.versions=t,this.kernel=e}return void 0!==this.versions?this.version_selector.layout(!0).then((()=>{this.version_selector.select(1),this.version_selector.value=this.versions[0].version,this.version_selector.architecture=this.versions[0].architecture,this._updateVersionSelectorText(this.version_selector.value,this.version_selector.architecture),this.version_selector.disabled=!1,this.environ_values={},this.updateResourceAllocationPane("update versions")})):void 0}}_updateVersionSelectorText(e,t){const i=this._getVersionInfo(e,t),r=[];i.forEach((e=>{""!==e.tag&&null!==e.tag&&r.push(e.tag)})),this.version_selector.selectedText=r.join(" / ")}generateSessionId(){let e="";const t="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";for(let i=0;i<8;i++)e+=t.charAt(Math.floor(62*Math.random()));return e+"-session"}async _updateVirtualFolderList(){return this.resourceBroker.updateVirtualFolderList().then((()=>{this.vfolders=this.resourceBroker.vfolders.filter((e=>"ready"===e.status))}))}async _aggregateResourceUse(e=""){return this.resourceBroker._aggregateCurrentResource(e).then((async e=>(this.concurrency_used=this.resourceBroker.concurrency_used,this.scaling_group=this.resourceBroker.scaling_group,this.scaling_groups=this.resourceBroker.scaling_groups,this.resource_templates=this.resourceBroker.resource_templates,this.resource_templates_filtered=this.resourceBroker.resource_templates_filtered,this.total_slot=this.resourceBroker.total_slot,this.total_resource_group_slot=this.resourceBroker.total_resource_group_slot,this.total_project_slot=this.resourceBroker.total_project_slot,this.used_slot=this.resourceBroker.used_slot,this.used_resource_group_slot=this.resourceBroker.used_resource_group_slot,this.used_project_slot=this.resourceBroker.used_project_slot,this.used_project_slot_percent=this.resourceBroker.used_project_slot_percent,this.concurrency_limit=this.resourceBroker.concurrency_limit&&this.resourceBroker.concurrency_limit>1?this.resourceBroker.concurrency_limit:1,this.available_slot=this.resourceBroker.available_slot,this.used_slot_percent=this.resourceBroker.used_slot_percent,this.used_resource_group_slot_percent=this.resourceBroker.used_resource_group_slot_percent,await this.updateComplete,Promise.resolve(!0)))).catch((e=>(e&&e.message&&(e.description?this.notification.text=q.relieve(e.description):this.notification.text=q.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)),Promise.resolve(!1))))}aggregateResource(e=""){void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._aggregateResourceUse(e)}),!0):this._aggregateResourceUse(e)}async updateResourceAllocationPane(e=""){var t,i;if(1==this.metric_updating)return;if("refresh resource policy"===e)return this.metric_updating=!1,this._aggregateResourceUse("update-metric").then((()=>this.updateResourceAllocationPane("after refresh resource policy")));const r=this.environment.selected,n=this.version_selector.selected;if(null===n)return void(this.metric_updating=!1);const o=n.value,s=n.getAttribute("architecture");if(this._updateVersionSelectorText(o,s),null==r||r.getAttribute("disabled"))this.metric_updating=!1;else if(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready)document.addEventListener("backend-ai-connected",(()=>{this.updateResourceAllocationPane(e)}),!0);else{if(this.metric_updating=!0,await this._aggregateResourceUse("update-metric"),await this._updateVirtualFolderList(),this.autoMountedVfolders=this.vfolders.filter((e=>e.name.startsWith("."))),this.enableInferenceWorkload?(this.modelVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")&&"model"===e.usage_mode)),this.nonAutoMountedVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")&&"general"===e.usage_mode))):this.nonAutoMountedVfolders=this.vfolders.filter((e=>!e.name.startsWith("."))),0===Object.keys(this.resourceBroker.resourceLimits).length)return void(this.metric_updating=!1);const e=r.id,n=o;if(""===e||""===n)return void(this.metric_updating=!1);const s=e+":"+n,l=this.resourceBroker.resourceLimits[s];if(!l)return void(this.metric_updating=!1);this.gpu_mode=this.resourceBroker.gpu_mode,this.gpu_step=this.resourceBroker.gpu_step,this.gpu_modes=this.resourceBroker.gpu_modes,globalThis.backendaiclient.supports("multi-container")&&this.cluster_size>1&&(this.gpu_step=1);const a=this.resourceBroker.available_slot;this.cpuResourceSlider.disabled=!1,this.memoryResourceSlider.disabled=!1,this.npuResourceSlider.disabled=!1,globalThis.backendaiclient.supports("multi-container")&&(this.cluster_size=1,this.clusterSizeSlider.value=this.cluster_size),this.sessionResourceSlider.disabled=!1,this.launchButton.disabled=!1,this.launchButtonMessageTextContent=V("session.launcher.ConfirmAndLaunch");let c=!1,d={min:.0625,max:2,preferred:.0625};if(this.npu_device_metric={min:0,max:0},l.forEach((e=>{if("cpu"===e.key){const t={...e};t.min=parseInt(t.min),["cpu","mem","cuda_device","cuda_shares","rocm_device","tpu_device","ipu_device","atom_device","atom_plus_device","gaudi2_device","warboy_device","rngd.device","hyperaccel_lpu_device"].forEach((e=>{e in this.total_resource_group_slot&&(a[e]=this.total_resource_group_slot[e])})),"cpu"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null===t.max?t.max=Math.min(parseInt(this.userResourceLimit.cpu),a.cpu,this.max_cpu_core_per_session):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit.cpu),a.cpu,this.max_cpu_core_per_session):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null===t.max?t.max=Math.min(this.available_slot.cpu,this.max_cpu_core_per_session):t.max=Math.min(parseInt(t.max),a.cpu,this.max_cpu_core_per_session),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.cpuResourceSlider.disabled=!0),this.cpu_metric=t,this.cluster_support&&"single-node"===this.cluster_mode&&(this.cluster_metric.max=Math.min(t.max,this.max_containers_per_session),this.cluster_metric.min>this.cluster_metric.max?this.cluster_metric.min=this.cluster_metric.max:this.cluster_metric.min=t.min)}if("cuda.device"===e.key&&"cuda.device"==this.gpu_mode){const t={...e};t.min=parseInt(t.min),"cuda.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["cuda.device"]),parseInt(a.cuda_device),this.max_cuda_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["cuda.device"]),a.cuda_device,this.max_cuda_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.cuda_device),this.max_cuda_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(a.cuda_device),this.max_cuda_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this.npu_device_metric=t,this._NPUDeviceNameOnSlider="GPU"}if("cuda.shares"===e.key&&"cuda.shares"===this.gpu_mode){const t={...e};t.min=parseFloat(t.min),"cuda.shares"in this.userResourceLimit?0===parseFloat(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseFloat(this.userResourceLimit["cuda.shares"]),parseFloat(a.cuda_shares),this.max_cuda_shares_per_container):t.max=Math.min(parseFloat(t.max),parseFloat(this.userResourceLimit["cuda.shares"]),parseFloat(a.cuda_shares),this.max_cuda_shares_per_container):0===parseFloat(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseFloat(a.cuda_shares),this.max_cuda_shares_per_container):t.max=Math.min(parseFloat(t.max),parseFloat(a.cuda_shares),this.max_cuda_shares_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this.cuda_shares_metric=t,t.max>0&&(this.npu_device_metric=t),this._NPUDeviceNameOnSlider="GPU"}if("rocm.device"===e.key&&"rocm.device"===this.gpu_mode){const t={...e};t.min=parseInt(t.min),t.max=parseInt(t.max),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this.npu_device_metric=t,this._NPUDeviceNameOnSlider="GPU"}if("tpu.device"===e.key){const t={...e};t.min=parseInt(t.min),"tpu.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["tpu.device"]),parseInt(a.tpu_device),this.max_tpu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["tpu.device"]),a.tpu_device,this.max_tpu_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.tpu_device),this.max_tpu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(a.tpu_device),this.max_tpu_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this.npu_device_metric=t,this._NPUDeviceNameOnSlider="TPU"}if("ipu.device"===e.key){const t={...e};t.min=parseInt(t.min),"ipu.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["ipu.device"]),parseInt(a.ipu_device),this.max_ipu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["ipu.device"]),a.ipu_device,this.max_ipu_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.ipu_device),this.max_ipu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(a.ipu_device),this.max_ipu_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this.npu_device_metric=t,this._NPUDeviceNameOnSlider="IPU"}if("atom.device"===e.key){const t={...e};t.min=parseInt(t.min),"atom.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["atom.device"]),parseInt(a.atom_device),this.max_atom_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["atom.device"]),a.atom_device,this.max_atom_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.atom_device),this.max_atom_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(a.atom_device),this.max_atom_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="ATOM",this.npu_device_metric=t}if("atom-plus.device"===e.key){const t={...e};t.min=parseInt(t.min),"atom-plus.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["atom-plus.device"]),parseInt(a.atom_plus_device),this.max_atom_plus_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["atom-plus.device"]),a.atom_plus_device,this.max_atom_plus_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.atom_plus_device),this.max_atom_plus_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(a.atom_plus_device),this.max_atom_plus_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="ATOM+",this.npu_device_metric=t}if("gaudi2.device"===e.key){const t={...e};t.min=parseInt(t.min),"gaudi2.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["gaudi2.device"]),parseInt(a.gaudi2_device),this.max_gaudi2_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["gaudi2.device"]),a.gaudi2_device,this.max_gaudi2_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.gaudi2_device),this.max_gaudi2_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(a.gaudi2_device),this.max_gaudi2_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="Gaudi 2",this.npu_device_metric=t}if("warboy.device"===e.key){const t={...e};t.min=parseInt(t.min),"warboy.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["warboy.device"]),parseInt(a.cuda_device),this.max_cuda_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["warboy.device"]),a.cuda_device,this.max_cuda_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.warboy_device),this.max_warboy_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(a.warboy_device),this.max_warboy_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="Warboy",this.npu_device_metric=t}if("rngd.device"===e.key){const t={...e};t.min=parseInt(t.min),"rngd.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["rngd.device"]),parseInt(a.cuda_device),this.max_cuda_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["rngd.device"]),a.cuda_device,this.max_cuda_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.rngd_device),this.max_rngd_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(a.rngd_device),this.max_rngd_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="RNGD",this.npu_device_metric=t}if("hyperaccel-lpu.device"===e.key){const t={...e};t.min=parseInt(t.min),"hyperaccel-lpu.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["hyperaccel-lpu.device"]),parseInt(a.hyperaccel_lpu_device),this.max_hyperaccel_lpu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["hyperaccel-lpu.device"]),a.hyperaccel_lpu_device,this.max_hyperaccel_lpu_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.hyperaccel_lpu_device),this.max_hyperaccel_lpu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(a.hyperaccel_lpu_device),this.max_hyperaccel_lpu_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="Hyperaccel LPU",this.npu_device_metric=t}if("mem"===e.key){const t={...e};t.min=globalThis.backendaiclient.utils.changeBinaryUnit(t.min,"g"),t.min<.1&&(t.min=.1),t.max||(t.max=0);const i=globalThis.backendaiclient.utils.changeBinaryUnit(t.max,"g","g");if("mem"in this.userResourceLimit){const e=globalThis.backendaiclient.utils.changeBinaryUnit(this.userResourceLimit.mem,"g");isNaN(parseInt(i))||0===parseInt(i)?t.max=Math.min(parseFloat(e),a.mem,this.max_mem_per_container):t.max=Math.min(parseFloat(i),parseFloat(e),a.mem,this.max_mem_per_container)}else 0!==parseInt(t.max)&&"Infinity"!==t.max&&!0!==isNaN(t.max)?t.max=Math.min(parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(t.max,"g","g")),a.mem,this.max_mem_per_container):t.max=Math.min(a.mem,this.max_mem_per_container);t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.memoryResourceSlider.disabled=!0),t.min=Number(t.min.toFixed(2)),t.max=Number(t.max.toFixed(2)),this.mem_metric=t}"shmem"===e.key&&(d={...e},d.preferred="preferred"in d?globalThis.backendaiclient.utils.changeBinaryUnit(d.preferred,"g","g"):.0625)})),d.max=this.max_shm_per_container,d.min=.0625,d.min>=d.max&&(d.min>d.max&&(d.min=d.max,c=!0),this.sharedMemoryResourceSlider.disabled=!0),d.min=Number(d.min.toFixed(2)),d.max=Number(d.max.toFixed(2)),this.shmem_metric=d,0==this.npu_device_metric.min&&0==this.npu_device_metric.max)if(this.npuResourceSlider.disabled=!0,this.npuResourceSlider.value=0,this.resource_templates.length>0){const e=[];for(let t=0;t<this.resource_templates.length;t++)"cuda_device"in this.resource_templates[t]||"cuda_shares"in this.resource_templates[t]?(parseFloat(this.resource_templates[t].cuda_device)<=0&&!("cuda_shares"in this.resource_templates[t])||parseFloat(this.resource_templates[t].cuda_shares)<=0&&!("cuda_device"in this.resource_templates[t])||parseFloat(this.resource_templates[t].cuda_device)<=0&&parseFloat(this.resource_templates[t].cuda_shares)<=0)&&e.push(this.resource_templates[t]):e.push(this.resource_templates[t]);this.resource_templates_filtered=e}else this.resource_templates_filtered=this.resource_templates;else this.npuResourceSlider.disabled=!1,this.npuResourceSlider.value=this.npu_device_metric.max,this.resource_templates_filtered=this.resource_templates;if(this.resource_templates_filtered.length>0){const e=this.resource_templates_filtered[0];this._chooseResourceTemplate(e),this.resourceTemplatesSelect.layout(!0).then((()=>this.resourceTemplatesSelect.layoutOptions())).then((()=>{this.resourceTemplatesSelect.select(1)}))}else this._updateResourceIndicator(this.cpu_metric.min,this.mem_metric.min,"none",0);c?(this.cpuResourceSlider.disabled=!0,this.memoryResourceSlider.disabled=!0,this.npuResourceSlider.disabled=!0,this.sessionResourceSlider.disabled=!0,this.sharedMemoryResourceSlider.disabled=!0,this.launchButton.disabled=!0,(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector(".allocation-check")).style.display="none",this.cluster_support&&(this.clusterSizeSlider.disabled=!0),this.launchButtonMessageTextContent=V("session.launcher.NotEnoughResource")):(this.cpuResourceSlider.disabled=!1,this.memoryResourceSlider.disabled=!1,this.npuResourceSlider.disabled=!1,this.sessionResourceSlider.disabled=!1,this.sharedMemoryResourceSlider.disabled=!1,this.launchButton.disabled=!1,(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector(".allocation-check")).style.display="flex",this.cluster_support&&(this.clusterSizeSlider.disabled=!1)),this.npu_device_metric.min==this.npu_device_metric.max&&this.npu_device_metric.max<1&&(this.npuResourceSlider.disabled=!0),this.concurrency_limit<=1&&(this.sessionResourceSlider.min=1,this.sessionResourceSlider.max=2,this.sessionResourceSlider.value=1,this.sessionResourceSlider.disabled=!0),this.max_containers_per_session<=1&&"single-node"===this.cluster_mode&&(this.clusterSizeSlider.min=1,this.clusterSizeSlider.max=2,this.clusterSizeSlider.value=1,this.clusterSizeSlider.disabled=!0),this.metric_updating=!1}}updateLanguage(){const e=this.environment.selected;if(null===e)return;const t=e.id;this._updateVersions(t)}folderToMountListRenderer(e,t,i){K(C`
        <div style="font-size:14px;text-overflow:ellipsis;overflow:hidden;">
          ${i.item.name}
        </div>
        <span style="font-size:10px;">${i.item.host}</span>
      `,e)}folderMapRenderer(e,t,i){K(C`
        <vaadin-text-field
          id="vfolder-alias-${i.item.name}"
          class="alias"
          clear-button-visible
          prevent-invalid-input
          pattern="^[a-zA-Z0-9./_-]*$"
          ?disabled="${!i.selected}"
          theme="small"
          placeholder="/home/work/${i.item.name}"
          @change="${e=>this._updateFolderMap(i.item.name,e.target.value)}"
        ></vaadin-text-field>
      `,e)}infoHeaderRenderer(e,t){K(C`
        <div class="horizontal layout center">
          <span id="vfolder-header-title">
            ${X("session.launcher.FolderAlias")}
          </span>
          <mwc-icon-button
            icon="info"
            class="fg green info"
            @click="${e=>this._showPathDescription(e)}"
          ></mwc-icon-button>
        </div>
      `,e)}_showPathDescription(e){null!=e&&e.stopPropagation(),this._helpDescriptionTitle=V("session.launcher.FolderAlias"),this._helpDescription=V("session.launcher.DescFolderAlias"),this._helpDescriptionIcon="",this.helpDescriptionDialog.show()}helpDescTagCount(e){let t=0;let i=e.indexOf(e);for(;-1!==i;)t++,i=e.indexOf("<p>",i+1);return t}setPathContent(e,t){var i;const r=e.children[e.children.length-1],n=r.children[r.children.length-1];if(n.children.length<t+1){const e=document.createElement("div");e.setAttribute("class","horizontal layout flex center");const t=document.createElement("mwc-checkbox");t.setAttribute("id","hide-guide");const r=document.createElement("span");r.append(document.createTextNode(`${V("dialog.hide.DoNotShowThisAgain")}`)),e.appendChild(t),e.appendChild(r),n.appendChild(e);const o=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#hide-guide");null==o||o.addEventListener("change",(e=>{if(null!==e.target){e.stopPropagation();e.target.checked?localStorage.setItem("backendaiwebui.pathguide","false"):localStorage.setItem("backendaiwebui.pathguide","true")}}))}}async _updateFolderMap(e,t){var i,r;if(""===t)return e in this.folderMapping&&delete this.folderMapping[e],await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!0);if(e!==t){if(this.selectedVfolders.includes(t))return this.notification.text=V("session.launcher.FolderAliasOverlapping"),this.notification.show(),delete this.folderMapping[e],(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#vfolder-alias-"+e)).value="",await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!1);for(const i in this.folderMapping)if({}.hasOwnProperty.call(this.folderMapping,i)&&this.folderMapping[i]==t)return this.notification.text=V("session.launcher.FolderAliasOverlapping"),this.notification.show(),delete this.folderMapping[e],(null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector("#vfolder-alias-"+e)).value="",await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!1);return this.folderMapping[e]=t,await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!0)}return Promise.resolve(!0)}changed(e){console.log(e)}isEmpty(e){return 0===e.length}_toggleAdvancedSettings(){var e;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#advanced-resource-settings")).toggle()}_setClusterMode(e){this.cluster_mode=e.target.value}_setClusterSize(e){this.cluster_size=e.target.value>0?Math.round(e.target.value):0,this.clusterSizeSlider.value=this.cluster_size;let t=1;globalThis.backendaiclient.supports("multi-container")&&(this.cluster_size>1||(t=0),this.gpu_step=this.resourceBroker.gpu_step,this._setSessionLimit(t))}_setSessionLimit(e=1){e>0?(this.sessionResourceSlider.value=e,this.session_request=e,this.sessionResourceSlider.disabled=!0):(this.sessionResourceSlider.max=this.concurrency_limit,this.sessionResourceSlider.disabled=!1)}_chooseResourceTemplate(e){var t;let i;i=void 0!==(null==e?void 0:e.cpu)?e:null===(t=e.target)||void 0===t?void 0:t.closest("mwc-list-item");const r=i.cpu,n=i.mem,o=i.cuda_device,s=i.cuda_shares,l=i.rocm_device,a=i.tpu_device,c=i.ipu_device,d=i.atom_device,u=i.atom_plus_device,h=i.gaudi2_device,p=i.warboy_device,m=i.rngd_device,f=i.hyperaccel_lpu_device;let g,v;void 0!==o&&Number(o)>0||void 0!==s&&Number(s)>0?void 0===s?(g="cuda.device",v=o):(g="cuda.shares",v=s):void 0!==l&&Number(l)>0?(g="rocm.device",v=l):void 0!==a&&Number(a)>0?(g="tpu.device",v=a):void 0!==c&&Number(c)>0?(g="ipu.device",v=c):void 0!==d&&Number(d)>0?(g="atom.device",v=d):void 0!==u&&Number(u)>0?(g="atom-plus.device",v=u):void 0!==h&&Number(h)>0?(g="gaudi2.device",v=h):void 0!==p&&Number(p)>0?(g="warboy.device",v=p):void 0!==m&&Number(m)>0?(g="rngd.device",v=m):void 0!==f&&Number(f)>0?(g="hyperaccel-lpu.device",v=f):(g="none",v=0);const b=i.shmem?i.shmem:this.shmem_metric;this.shmem_request="number"!=typeof b?b.preferred:b||.0625,this._updateResourceIndicator(r,n,g,v)}_updateResourceIndicator(e,t,i,r){this.cpuResourceSlider.value=e,this.memoryResourceSlider.value=t,this.npuResourceSlider.value=r,this.sharedMemoryResourceSlider.value=this.shmem_request,this.cpu_request=e,this.mem_request=t,this.gpu_request=r,this.gpu_request_type=i}async selectDefaultLanguage(e=!1,t=""){if(!0===this._default_language_updated&&!1===e)return;""!==t?this.default_language=t:void 0!==globalThis.backendaiclient._config.default_session_environment&&"default_session_environment"in globalThis.backendaiclient._config&&""!==globalThis.backendaiclient._config.default_session_environment?this.languages.map((e=>e.name)).includes(globalThis.backendaiclient._config.default_session_environment)?this.default_language=globalThis.backendaiclient._config.default_session_environment:""!==this.languages[0].name?this.default_language=this.languages[0].name:this.default_language=this.languages[1].name:this.languages.length>1?this.default_language=this.languages[1].name:0!==this.languages.length?this.default_language=this.languages[0].name:this.default_language="index.docker.io/lablup/ngc-tensorflow";const i=this.environment.items.find((e=>e.value===this.default_language));if(void 0===i&&void 0!==globalThis.backendaiclient&&!1===globalThis.backendaiclient.ready)return setTimeout((()=>(console.log("Environment selector is not ready yet. Trying to set the default language again."),this.selectDefaultLanguage(e,t))),500),Promise.resolve(!0);const r=this.environment.items.indexOf(i);return this.environment.select(r),this._default_language_updated=!0,Promise.resolve(!0)}_selectDefaultVersion(e){return!1}async _fetchSessionOwnerGroups(){var e;this.ownerFeatureInitialized||(this.ownerGroupSelect.addEventListener("selected",this._fetchSessionOwnerScalingGroups.bind(this)),this.ownerFeatureInitialized=!0);const t=this.ownerEmailInput.value;if(!this.ownerEmailInput.checkValidity()||""===t||void 0===t)return this.notification.text=V("credential.validation.InvalidEmailAddress"),this.notification.show(),this.ownerKeypairs=[],void(this.ownerGroups=[]);const i=await globalThis.backendaiclient.keypair.list(t,["access_key"]),r=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#owner-enabled");if(this.ownerKeypairs=i.keypairs,this.ownerKeypairs.length<1)return this.notification.text=V("session.launcher.NoActiveKeypair"),this.notification.show(),r.checked=!1,r.disabled=!0,this.ownerKeypairs=[],void(this.ownerGroups=[]);this.ownerAccesskeySelect.layout(!0).then((()=>{this.ownerAccesskeySelect.select(0),this.ownerAccesskeySelect.createAdapter().setSelectedText(this.ownerKeypairs[0].access_key)}));try{const e=await globalThis.backendaiclient.user.get(t,["domain_name","groups {id name}"]);this.ownerDomain=e.user.domain_name,this.ownerGroups=e.user.groups}catch(e){return this.notification.text=V("session.launcher.NotEnoughOwnershipInfo"),void this.notification.show()}this.ownerGroups.length&&this.ownerGroupSelect.layout(!0).then((()=>{this.ownerGroupSelect.select(0),this.ownerGroupSelect.createAdapter().setSelectedText(this.ownerGroups[0].name)})),r.disabled=!1}async _fetchSessionOwnerScalingGroups(){const e=this.ownerGroupSelect.value;if(!e)return void(this.ownerScalingGroups=[]);const t=await globalThis.backendaiclient.scalingGroup.list(e);this.ownerScalingGroups=t.scaling_groups,this.ownerScalingGroups&&this.ownerScalingGroupSelect.layout(!0).then((()=>{this.ownerScalingGroupSelect.select(0),this.ownerGroupSelect.createAdapter().setSelectedText(this.ownerScalingGroups[0].name)}))}async _fetchDelegatedSessionVfolder(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#owner-enabled"),i=this.ownerEmailInput.value;this.ownerKeypairs.length>0&&t&&t.checked?(await this.resourceBroker.updateVirtualFolderList(i),this.vfolders=this.resourceBroker.vfolders):await this._updateVirtualFolderList(),this.autoMountedVfolders=this.vfolders.filter((e=>e.name.startsWith("."))),this.enableInferenceWorkload?(this.modelVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")&&"model"===e.usage_mode)),this.nonAutoMountedVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")&&"general"===e.usage_mode))):this.nonAutoMountedVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")))}_toggleResourceGauge(){""==this.resourceGauge.style.display||"flex"==this.resourceGauge.style.display||"block"==this.resourceGauge.style.display?this.resourceGauge.style.display="none":(document.body.clientWidth<750?(this.resourceGauge.style.left="20px",this.resourceGauge.style.right="20px",this.resourceGauge.style.backgroundColor="var(--paper-red-800)"):this.resourceGauge.style.backgroundColor="transparent",this.resourceGauge.style.display="flex")}_showKernelDescription(e,t){e.stopPropagation();const i=t.kernelname;i in this.resourceBroker.imageInfo&&"description"in this.resourceBroker.imageInfo[i]?(this._helpDescriptionTitle=this.resourceBroker.imageInfo[i].name,this._helpDescription=this.resourceBroker.imageInfo[i].description||V("session.launcher.NoDescriptionFound"),this._helpDescriptionIcon=t.icon,this.helpDescriptionDialog.show()):(i in this.imageInfo?this._helpDescriptionTitle=this.resourceBroker.imageInfo[i].name:this._helpDescriptionTitle=i,this._helpDescription=V("session.launcher.NoDescriptionFound"))}_showResourceDescription(e,t){e.stopPropagation();const i={cpu:{name:V("session.launcher.CPU"),desc:V("session.launcher.DescCPU")},mem:{name:V("session.launcher.Memory"),desc:V("session.launcher.DescMemory")},shmem:{name:V("session.launcher.SharedMemory"),desc:V("session.launcher.DescSharedMemory")},gpu:{name:V("session.launcher.AIAccelerator"),desc:V("session.launcher.DescAIAccelerator")},session:{name:V("session.launcher.TitleSession"),desc:V("session.launcher.DescSession")},"single-node":{name:V("session.launcher.SingleNode"),desc:V("session.launcher.DescSingleNode")},"multi-node":{name:V("session.launcher.MultiNode"),desc:V("session.launcher.DescMultiNode")},"openmp-optimization":{name:V("session.launcher.OpenMPOptimization"),desc:V("session.launcher.DescOpenMPOptimization")}};t in i&&(this._helpDescriptionTitle=i[t].name,this._helpDescription=i[t].desc,this._helpDescriptionIcon="",this.helpDescriptionDialog.show())}_showEnvConfigDescription(e){e.stopPropagation(),this._helpDescriptionTitle=V("session.launcher.EnvironmentVariableTitle"),this._helpDescription=V("session.launcher.DescSetEnv"),this._helpDescriptionIcon="",this.helpDescriptionDialog.show()}_showPreOpenPortConfigDescription(e){e.stopPropagation(),this._helpDescriptionTitle=V("session.launcher.PreOpenPortTitle"),this._helpDescription=V("session.launcher.DescSetPreOpenPort"),this._helpDescriptionIcon="",this.helpDescriptionDialog.show()}_resourceTemplateToCustom(){this.resourceTemplatesSelect.selectedText=V("session.launcher.CustomResourceApplied"),this._updateResourceIndicator(this.cpu_request,this.mem_request,this.gpu_mode,this.gpu_request)}_applyResourceValueChanges(e,t=!0){const i=e.target.value;switch(e.target.id.split("-")[0]){case"cpu":this.cpu_request=i;break;case"mem":this.mem_request=i;break;case"shmem":this.shmem_request=i;break;case"gpu":this.gpu_request=i;break;case"session":this.session_request=i;break;case"cluster":this._changeTotalAllocationPane()}this.requestUpdate(),t?this._resourceTemplateToCustom():this._setClusterSize(e)}_changeTotalAllocationPane(){var e,t;this._deleteAllocationPaneShadow();const i=this.clusterSizeSlider.value;if(i>1){const r=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#resource-allocated-box-shadow");for(let e=0;e<=Math.min(5,i-1);e+=1){const t=document.createElement("div");t.classList.add("horizontal","layout","center","center-justified","resource-allocated-box","allocation-shadow"),t.style.position="absolute",t.style.top="-"+(5+5*e)+"px",t.style.left=5+5*e+"px";const i=this.isDarkMode?88-2*e:245+2*e;t.style.backgroundColor="rgb("+i+","+i+","+i+")",t.style.borderColor=this.isDarkMode?"none":"rgb("+(i-10)+","+(i-10)+","+(i-10)+")",t.style.zIndex=(6-e).toString(),r.appendChild(t)}(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#total-allocation-pane")).appendChild(r)}}_deleteAllocationPaneShadow(){var e;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#resource-allocated-box-shadow")).innerHTML=""}_updateShmemLimit(){const e=parseFloat(this.memoryResourceSlider.value);let t=this.sharedMemoryResourceSlider.value;parseFloat(t)>e?(t=e,this.shmem_request=t,this.sharedMemoryResourceSlider.value=t,this.sharedMemoryResourceSlider.max=t,this.notification.text=V("session.launcher.SharedMemorySettingIsReduced"),this.notification.show()):this.max_shm_per_container>t&&(this.sharedMemoryResourceSlider.max=e>this.max_shm_per_container?this.max_shm_per_container:e)}_roundResourceAllocation(e,t){return parseFloat(e).toFixed(t)}_conditionalGiBtoMiB(e){return e<1?this._roundResourceAllocation((1024*e).toFixed(0),2):this._roundResourceAllocation(e,2)}_conditionalGiBtoMiBunit(e){return e<1?"MiB":"GiB"}_getVersionInfo(e,t){const i=[],r=e.split("-");if(i.push({tag:this._aliasName(r[0]),color:"blue",size:"60px"}),r.length>1&&(this.kernel+":"+e in this.imageRequirements&&"framework"in this.imageRequirements[this.kernel+":"+e]?i.push({tag:this.imageRequirements[this.kernel+":"+e].framework,color:"red",size:"110px"}):i.push({tag:this._aliasName(r[1]),color:"red",size:"110px"})),i.push({tag:t,color:"lightgreen",size:"90px"}),r.length>2){let e=this._aliasName(r.slice(2).join("-"));e=e.split(":"),e.length>1?i.push({tag:e.slice(1).join(":"),app:e[0],color:"green",size:"110px"}):i.push({tag:e[0],color:"green",size:"110px"})}return i}_disableEnterKey(){var e;null===(e=this.shadowRoot)||void 0===e||e.querySelectorAll("lablup-expansion").forEach((e=>{e.onkeydown=e=>{"Enter"===e.key&&e.preventDefault()}}))}_validateInput(e){const t=e.target.closest("mwc-textfield");t.value&&(t.value=Math.round(t.value),t.value=globalThis.backendaiclient.utils.clamp(t.value,t.min,t.max))}_validateSessionName(){this.sessionName.validityTransform=(e,t)=>{if(t.valid){const t=!this.resourceBroker.sessions_list.includes(e);return t||(this.sessionName.validationMessage=V("session.launcher.DuplicatedSessionName")),{valid:t,customError:!t}}return t.patternMismatch?(this.sessionName.validationMessage=V("session.launcher.SessionNameAllowCondition"),{valid:t.valid,patternMismatch:!t.valid}):(this.sessionName.validationMessage=V("session.validation.EnterValidSessionName"),{valid:t.valid,customError:!t.valid})}}_appendEnvRow(e="",t=""){var i,r;const n=null===(i=this.modifyEnvContainer)||void 0===i?void 0:i.children[this.modifyEnvContainer.children.length-1],o=this._createEnvRow(e,t);null===(r=this.modifyEnvContainer)||void 0===r||r.insertBefore(o,n)}_appendPreOpenPortRow(e=null){var t,i;const r=null===(t=this.modifyPreOpenPortContainer)||void 0===t?void 0:t.children[this.modifyPreOpenPortContainer.children.length-1],n=this._createPreOpenPortRow(e);null===(i=this.modifyPreOpenPortContainer)||void 0===i||i.insertBefore(n,r),this._updateisExceedMaxCountForPreopenPorts()}_createEnvRow(e="",t=""){const i=document.createElement("div");i.setAttribute("class","horizontal layout center row");const r=document.createElement("mwc-textfield");r.setAttribute("value",e);const n=document.createElement("mwc-textfield");n.setAttribute("value",t);const o=document.createElement("mwc-icon-button");return o.setAttribute("icon","remove"),o.setAttribute("class","green minus-btn"),o.addEventListener("click",(e=>this._removeEnvItem(e))),i.append(r),i.append(n),i.append(o),i}_createPreOpenPortRow(e){const t=document.createElement("div");t.setAttribute("class","horizontal layout center row");const i=document.createElement("mwc-textfield");e&&i.setAttribute("value",e),i.setAttribute("type","number"),i.setAttribute("min","1024"),i.setAttribute("max","65535");const r=document.createElement("mwc-icon-button");return r.setAttribute("icon","remove"),r.setAttribute("class","green minus-btn"),r.addEventListener("click",(e=>this._removePreOpenPortItem(e))),t.append(i),t.append(r),t}_removeEnvItem(e){e.target.parentNode.remove()}_removePreOpenPortItem(e){e.target.parentNode.remove(),this._updateisExceedMaxCountForPreopenPorts()}_removeEmptyEnv(){var e;const t=null===(e=this.modifyEnvContainer)||void 0===e?void 0:e.querySelectorAll(".row");Array.prototype.filter.call(t,(e=>(e=>2===Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>""===e.value)).length)(e))).map(((e,t)=>{(0!==t||this.environ.length>0)&&e.parentNode.removeChild(e)}))}_removeEmptyPreOpenPorts(){var e;const t=null===(e=this.modifyPreOpenPortContainer)||void 0===e?void 0:e.querySelectorAll(".row:not(.header)");Array.prototype.filter.call(t,(e=>(e=>1===Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>""===e.value)).length)(e))).map(((e,t)=>{(0!==t||this.preOpenPorts.length>0)&&e.parentNode.removeChild(e)})),this._updateisExceedMaxCountForPreopenPorts()}modifyEnv(){this._parseEnvVariableList(),this._saveEnvVariableList(),this.modifyEnvDialog.closeWithConfirmation=!1,this.modifyEnvDialog.hide(),this.notification.text=V("session.launcher.EnvironmentVariableConfigurationDone"),this.notification.show()}modifyPreOpenPorts(){var e;const t=null===(e=this.modifyPreOpenPortContainer)||void 0===e?void 0:e.querySelectorAll(".row:not(.header) mwc-textfield");if(!(0===Array.from(t).filter((e=>!e.checkValidity())).length))return this.notification.text=V("session.launcher.PreOpenPortRange"),void this.notification.show();this._parseAndSavePreOpenPortList(),this.modifyPreOpenPortDialog.closeWithConfirmation=!1,this.modifyPreOpenPortDialog.hide(),this.notification.text=V("session.launcher.PreOpenPortConfigurationDone"),this.notification.show()}_loadEnv(){this.environ.forEach((e=>{this._appendEnvRow(e.name,e.value)}))}_loadPreOpenPorts(){this.preOpenPorts.forEach((e=>{this._appendPreOpenPortRow(e)}))}_showEnvDialog(){this._removeEmptyEnv(),this.modifyEnvDialog.closeWithConfirmation=!0,this.modifyEnvDialog.show()}_showPreOpenPortDialog(){this._removeEmptyPreOpenPorts(),this.modifyPreOpenPortDialog.closeWithConfirmation=!0,this.modifyPreOpenPortDialog.show()}_closeAndResetEnvInput(){this._clearEnvRows(!0),this.closeDialog("env-config-confirmation"),this.hideEnvDialog&&(this._loadEnv(),this.modifyEnvDialog.closeWithConfirmation=!1,this.modifyEnvDialog.hide())}_closeAndResetPreOpenPortInput(){this._clearPreOpenPortRows(!0),this.closeDialog("preopen-ports-config-confirmation"),this.hidePreOpenPortDialog&&(this._loadPreOpenPorts(),this.modifyPreOpenPortDialog.closeWithConfirmation=!1,this.modifyPreOpenPortDialog.hide())}_parseEnvVariableList(){var e;this.environ_values={};const t=null===(e=this.modifyEnvContainer)||void 0===e?void 0:e.querySelectorAll(".row:not(.header)"),i=e=>{const t=Array.prototype.map.call(e.querySelectorAll("mwc-textfield"),(e=>e.value));return this.environ_values[t[0]]=t[1],t};Array.prototype.filter.call(t,(e=>(e=>0===Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>0===e.value.length)).length)(e))).map((e=>i(e)))}_saveEnvVariableList(){this.environ=Object.entries(this.environ_values).map((([e,t])=>({name:e,value:t})))}_parseAndSavePreOpenPortList(){var e;const t=null===(e=this.modifyPreOpenPortContainer)||void 0===e?void 0:e.querySelectorAll(".row:not(.header) mwc-textfield");this.preOpenPorts=Array.from(t).filter((e=>""!==e.value)).map((e=>e.value))}_resetEnvironmentVariables(){this.environ=[],this.environ_values={},null!==this.modifyEnvDialog&&this._clearEnvRows(!0)}_resetPreOpenPorts(){this.preOpenPorts=[],null!==this.modifyPreOpenPortDialog&&this._clearPreOpenPortRows(!0)}_clearEnvRows(e=!1){var t;const i=null===(t=this.modifyEnvContainer)||void 0===t?void 0:t.querySelectorAll(".row"),r=i[0];if(!e){const e=e=>Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>e.value.length>0)).length>0;if(Array.prototype.filter.call(i,(t=>e(t))).length>0)return this.hideEnvDialog=!1,void this.openDialog("env-config-confirmation")}null==r||r.querySelectorAll("mwc-textfield").forEach((e=>{e.value=""})),i.forEach(((e,t)=>{0!==t&&e.remove()}))}_clearPreOpenPortRows(e=!1){var t;const i=null===(t=this.modifyPreOpenPortContainer)||void 0===t?void 0:t.querySelectorAll(".row"),r=i[0];if(!e){const e=e=>Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>e.value.length>0)).length>0;if(Array.prototype.filter.call(i,(t=>e(t))).length>0)return this.hidePreOpenPortDialog=!1,void this.openDialog("preopen-ports-config-confirmation")}null==r||r.querySelectorAll("mwc-textfield").forEach((e=>{e.value=""})),i.forEach(((e,t)=>{0!==t&&e.remove()}))}openDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).show()}closeDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).hide()}validateSessionLauncherInput(){if(1===this.currentIndex){const e="batch"!==this.sessionType||this.commandEditor._validateInput(),t="batch"!==this.sessionType||!this.scheduledTime||new Date(this.scheduledTime).getTime()>(new Date).getTime(),i=this.sessionName.checkValidity();if(!e||!t||!i)return!1}return!0}async moveProgress(e){var t,i,r,n;if(!this.validateSessionLauncherInput())return;const o=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#progress-0"+this.currentIndex);this.currentIndex+=e,"inference"===this.mode&&2==this.currentIndex&&(this.currentIndex+=e),this.currentIndex>this.progressLength&&(this.currentIndex=globalThis.backendaiclient.utils.clamp(this.currentIndex+e,this.progressLength,1));const s=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#progress-0"+this.currentIndex);o.classList.remove("active"),s.classList.add("active"),this.prevButton.style.visibility=1==this.currentIndex?"hidden":"visible",this.nextButton.style.visibility=this.currentIndex==this.progressLength?"hidden":"visible",this.launchButton.disabled||(this.launchButtonMessageTextContent=this.progressLength==this.currentIndex?V("session.launcher.Launch"):V("session.launcher.ConfirmAndLaunch")),null===(r=this._nonAutoMountedFolderGrid)||void 0===r||r.clearCache(),null===(n=this._modelFolderGrid)||void 0===n||n.clearCache(),2===this.currentIndex&&(await this._fetchDelegatedSessionVfolder(),this._checkSelectedItems())}_resetProgress(){this.moveProgress(1-this.currentIndex),this._resetEnvironmentVariables(),this._resetPreOpenPorts(),this._unselectAllSelectedFolder(),this._deleteAllocationPaneShadow()}_calculateProgress(){const e=this.progressLength>0?this.progressLength:1;return((this.currentIndex>0?this.currentIndex:1)/e).toFixed(2)}_acceleratorName(e){const t={"cuda.device":"GPU","cuda.shares":"GPU","rocm.device":"GPU","tpu.device":"TPU","ipu.device":"IPU","atom.device":"ATOM","atom-plus.device":"ATOM+","gaudi2.device":"Gaudi 2","warboy.device":"Warboy","rngd.device":"RNGD","hyperaccel-lpu.device":"Hyperaccel LPU"};return e in t?t[e]:"GPU"}_toggleEnvironmentSelectUI(){var e;const t=!!(null===(e=this.manualImageName)||void 0===e?void 0:e.value);this.environment.disabled=this.version_selector.disabled=t;const i=t?-1:1;this.environment.select(i),this.version_selector.select(i)}_toggleHPCOptimization(){var e;const t=this.openMPSwitch.selected;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#HPCOptimizationOptions")).style.display=t?"none":"block"}_toggleStartUpCommandEditor(e){var t;this.sessionType=e.target.value;const i="batch"===this.sessionType;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#batch-mode-config-section")).style.display=i?"inline-flex":"none",i&&(this.commandEditor.refresh(),this.commandEditor.focus())}_updateisExceedMaxCountForPreopenPorts(){var e,t,i;const r=null!==(i=null===(t=null===(e=this.modifyPreOpenPortContainer)||void 0===e?void 0:e.querySelectorAll("mwc-textfield"))||void 0===t?void 0:t.length)&&void 0!==i?i:0;this.isExceedMaxCountForPreopenPorts=r>=this.maxCountForPreopenPorts}render(){var e,t;return C`
      <link rel="stylesheet" href="resources/fonts/font-awesome-all.min.css" />
      <link rel="stylesheet" href="resources/custom.css" />
      <mwc-button
        class="primary-action"
        id="launch-session"
        ?disabled="${!this.enableLaunchButton}"
        icon="power_settings_new"
        @click="${()=>this._launchSessionDialog()}"
      >
        ${X("session.launcher.Start")}
      </mwc-button>
      <backend-ai-dialog
        id="new-session-dialog"
        narrowLayout
        fixed
        backdrop
        persistent
        style="position:relative;"
      >
        <span slot="title">
          ${this.newSessionDialogTitle?this.newSessionDialogTitle:X("session.launcher.StartNewSession")}
        </span>
        <form
          slot="content"
          id="launch-session-form"
          class="centered"
          style="position:relative;"
        >
          <div id="progress-01" class="progress center layout fade active">
            <mwc-select
              id="session-type"
              icon="category"
              label="${V("session.launcher.SessionType")}"
              required
              fixedMenuPosition
              value="${this.sessionType}"
              @selected="${e=>this._toggleStartUpCommandEditor(e)}"
            >
              ${"inference"===this.mode?C`
                    <mwc-list-item value="inference" selected>
                      ${X("session.launcher.InferenceMode")}
                    </mwc-list-item>
                  `:C`
                    <mwc-list-item value="batch">
                      ${X("session.launcher.BatchMode")}
                    </mwc-list-item>
                    <mwc-list-item value="interactive" selected>
                      ${X("session.launcher.InteractiveMode")}
                    </mwc-list-item>
                  `}
            </mwc-select>
            <mwc-select
              id="environment"
              icon="code"
              label="${V("session.launcher.Environments")}"
              required
              fixedMenuPosition
              value="${this.default_language}"
            >
              <mwc-list-item
                selected
                graphic="icon"
                style="display:none!important;"
              >
                ${X("session.launcher.ChooseEnvironment")}
              </mwc-list-item>
              ${this.languages.map((e=>C`
                  ${!1===e.clickable?C`
                        <h5
                          style="font-size:12px;padding: 0 10px 3px 10px;margin:0; border-bottom:1px solid var(--token-colorBorder, #ccc);"
                          role="separator"
                          disabled="true"
                        >
                          ${e.basename}
                        </h5>
                      `:C`
                        <mwc-list-item
                          id="${e.name}"
                          value="${e.name}"
                          graphic="icon"
                        >
                          <img
                            slot="graphic"
                            alt="language icon"
                            src="resources/icons/${e.icon}"
                            style="width:24px;height:24px;"
                          />
                          <div
                            class="horizontal justified center flex layout"
                            style="width:325px;"
                          >
                            <div style="padding-right:5px;">
                              ${e.basename}
                            </div>
                            <div
                              class="horizontal layout end-justified center flex"
                            >
                              ${e.tags?e.tags.map((e=>C`
                                      <lablup-shields
                                        style="margin-right:5px;"
                                        color="${e.color}"
                                        description="${e.tag}"
                                      ></lablup-shields>
                                    `)):""}
                              <mwc-icon-button
                                icon="info"
                                class="fg blue info"
                                @click="${t=>this._showKernelDescription(t,e)}"
                              ></mwc-icon-button>
                            </div>
                          </div>
                        </mwc-list-item>
                      `}
                `))}
            </mwc-select>
            <mwc-select
              id="version"
              icon="architecture"
              label="${V("session.launcher.Version")}"
              required
              fixedMenuPosition
            >
              <mwc-list-item
                selected
                style="display:none!important"
              ></mwc-list-item>
              ${"Not Selected"===this.versions[0]&&1===this.versions.length?C``:C`
                    <h5
                      style="font-size:12px;padding: 0 10px 3px 15px;margin:0; border-bottom:1px solid var(--token-colorBorder, #ccc);"
                      role="separator"
                      disabled="true"
                      class="horizontal layout"
                    >
                      <div style="width:60px;">
                        ${X("session.launcher.Version")}
                      </div>
                      <div style="width:110px;">
                        ${X("session.launcher.Base")}
                      </div>
                      <div style="width:90px;">
                        ${X("session.launcher.Architecture")}
                      </div>
                      <div style="width:110px;">
                        ${X("session.launcher.Requirements")}
                      </div>
                    </h5>
                    ${this.versions.map((({version:e,architecture:t})=>C`
                        <mwc-list-item
                          id="${e}"
                          architecture="${t}"
                          value="${e}"
                          style="min-height:35px;height:auto;"
                        >
                          <span style="display:none">${e}</span>
                          <div class="horizontal layout end-justified">
                            ${this._getVersionInfo(e||"",t).map((e=>C`
                                <lablup-shields
                                  style="width:${e.size}!important;"
                                  color="${e.color}"
                                  app="${void 0!==e.app&&""!=e.app&&" "!=e.app?e.app:""}"
                                  description="${e.tag}"
                                  class="horizontal layout center center-justified"
                                ></lablup-shields>
                              `))}
                          </div>
                        </mwc-list-item>
                      `))}
                  `}
            </mwc-select>
            ${this._debug||this.allow_manual_image_name_for_session?C`
                  <mwc-textfield
                    id="image-name"
                    type="text"
                    class="flex"
                    value=""
                    icon="assignment_turned_in"
                    label="${V("session.launcher.ManualImageName")}"
                    @change=${e=>this._toggleEnvironmentSelectUI()}
                  ></mwc-textfield>
                `:C``}
            <mwc-textfield
              id="session-name"
              placeholder="${V("session.launcher.SessionNameOptional")}"
              pattern="^[a-zA-Z0-9]([a-zA-Z0-9\\-_\\.]{2,})[a-zA-Z0-9]$"
              minLength="4"
              maxLength="64"
              icon="label"
              helper="${V("inputLimit.4to64chars")}"
              validationMessage="${V("session.launcher.SessionNameAllowCondition")}"
              autoValidate
              @input="${()=>this._validateSessionName()}"
            ></mwc-textfield>
            <div
              class="vertical layout center flex"
              id="batch-mode-config-section"
              style="display:none;gap:3px;"
            >
              <span
                class="launcher-item-title"
                style="width:386px;padding-left:16px;"
              >
                ${X("session.launcher.BatchModeConfig")}
              </span>
              <div class="horizontal layout start-justified">
                <div style="width:370px;font-size:12px;">
                  ${X("session.launcher.StartUpCommand")}*
                </div>
              </div>
              <lablup-codemirror
                id="command-editor"
                mode="shell"
                required
                validationMessage="${X("dialog.warning.Required")}"
              ></lablup-codemirror>
              <backend-ai-react-batch-session-scheduled-time-setting
                @change=${({detail:e})=>{this.scheduledTime=e}}
                style="align-self:start;margin-left:15px;margin-bottom:10px;"
              ></backend-ai-react-batch-session-scheduled-time-setting>
            </div>
            <lablup-expansion
              leftIconName="expand_more"
              rightIconName="settings"
              .rightCustomFunction="${()=>this._showEnvDialog()}"
            >
              <span slot="title">
                ${X("session.launcher.SetEnvironmentVariable")}
              </span>
              <div class="environment-variables-container">
                ${this.environ.length>0?C`
                      <div
                        class="horizontal flex center center-justified layout"
                        style="overflow-x:hidden;"
                      >
                        <div role="listbox">
                          <h4>
                            ${V("session.launcher.EnvironmentVariable")}
                          </h4>
                          ${this.environ.map((e=>C`
                              <mwc-textfield
                                disabled
                                value="${e.name}"
                              ></mwc-textfield>
                            `))}
                        </div>
                        <div role="listbox" style="margin-left:15px;">
                          <h4>
                            ${V("session.launcher.EnvironmentVariableValue")}
                          </h4>
                          ${this.environ.map((e=>C`
                              <mwc-textfield
                                disabled
                                value="${e.value}"
                              ></mwc-textfield>
                            `))}
                        </div>
                      </div>
                    `:C`
                      <div class="vertical layout center flex blank-box">
                        <span>${X("session.launcher.NoEnvConfigured")}</span>
                      </div>
                    `}
              </div>
            </lablup-expansion>
            ${this.maxCountForPreopenPorts>0?C`
                  <lablup-expansion
                    leftIconName="expand_more"
                    rightIconName="settings"
                    .rightCustomFunction="${()=>this._showPreOpenPortDialog()}"
                  >
                    <span slot="title">
                      ${X("session.launcher.SetPreopenPorts")}
                    </span>
                    <div class="preopen-ports-container">
                      ${this.preOpenPorts.length>0?C`
                            <div
                              class="horizontal flex center layout"
                              style="overflow-x:hidden;margin:auto 5px;"
                            >
                              ${this.preOpenPorts.map((e=>C`
                                  <lablup-shields
                                    color="lightgrey"
                                    description="${e}"
                                    style="padding:4px;"
                                  ></lablup-shields>
                                `))}
                            </div>
                          `:C`
                            <div class="vertical layout center flex blank-box">
                              <span>
                                ${X("session.launcher.NoPreOpenPortsConfigured")}
                              </span>
                            </div>
                          `}
                    </div>
                  </lablup-expansion>
                `:C``}
            <lablup-expansion
              name="ownership"
              style="--expansion-content-padding:15px 0;"
            >
              <span slot="title">
                ${X("session.launcher.SetSessionOwner")}
              </span>
              <div class="vertical layout">
                <div class="horizontal center layout">
                  <mwc-textfield
                    id="owner-email"
                    type="email"
                    class="flex"
                    value=""
                    pattern="^.+@.+..+$"
                    icon="mail"
                    label="${V("session.launcher.OwnerEmail")}"
                    size="40"
                  ></mwc-textfield>
                  <mwc-icon-button
                    icon="refresh"
                    class="blue"
                    @click="${()=>this._fetchSessionOwnerGroups()}"
                  ></mwc-icon-button>
                </div>
                <mwc-select
                  id="owner-accesskey"
                  label="${V("session.launcher.OwnerAccessKey")}"
                  icon="vpn_key"
                  fixedMenuPosition
                  naturalMenuWidth
                >
                  ${this.ownerKeypairs.map((e=>C`
                      <mwc-list-item
                        class="owner-group-dropdown"
                        id="${e.access_key}"
                        value="${e.access_key}"
                      >
                        ${e.access_key}
                      </mwc-list-item>
                    `))}
                </mwc-select>
                <div class="horizontal center layout">
                  <mwc-select
                    id="owner-group"
                    label="${V("session.launcher.OwnerGroup")}"
                    icon="group_work"
                    fixedMenuPosition
                    naturalMenuWidth
                  >
                    ${this.ownerGroups.map((e=>C`
                        <mwc-list-item
                          class="owner-group-dropdown"
                          id="${e.name}"
                          value="${e.name}"
                        >
                          ${e.name}
                        </mwc-list-item>
                      `))}
                  </mwc-select>
                  <mwc-select
                    id="owner-scaling-group"
                    label="${V("session.launcher.OwnerResourceGroup")}"
                    icon="storage"
                    fixedMenuPosition
                  >
                    ${this.ownerScalingGroups.map((e=>C`
                        <mwc-list-item
                          class="owner-group-dropdown"
                          id="${e.name}"
                          value="${e.name}"
                        >
                          ${e.name}
                        </mwc-list-item>
                      `))}
                  </mwc-select>
                </div>
                <div class="horizontal layout start-justified center">
                  <mwc-checkbox id="owner-enabled"></mwc-checkbox>
                  <p>${X("session.launcher.LaunchSessionWithAccessKey")}</p>
                </div>
              </div>
            </lablup-expansion>
          </div>
          <div
            id="progress-02"
            class="progress center layout fade"
            style="padding-top:0;"
          >
            <lablup-expansion class="vfolder" name="vfolder" open>
              <span slot="title">${X("session.launcher.FolderToMount")}</span>
              <div class="vfolder-list">
                <vaadin-grid
                  theme="no-border row-stripes column-borders compact dark"
                  id="non-auto-mounted-folder-grid"
                  aria-label="vfolder list"
                  height-by-rows
                  .items="${this.nonAutoMountedVfolders}"
                  @selected-items-changed="${()=>this._updateSelectedFolder()}"
                >
                  <vaadin-grid-selection-column
                    id="select-column"
                    flex-grow="0"
                    text-align="center"
                    auto-select
                  ></vaadin-grid-selection-column>
                  <vaadin-grid-filter-column
                    header="${X("session.launcher.FolderToMountList")}"
                    path="name"
                    resizable
                    .renderer="${this._boundFolderToMountListRenderer}"
                  ></vaadin-grid-filter-column>
                  <vaadin-grid-column
                    width="135px"
                    path=" ${X("session.launcher.FolderAlias")}"
                    .renderer="${this._boundFolderMapRenderer}"
                    .headerRenderer="${this._boundPathRenderer}"
                  ></vaadin-grid-column>
                </vaadin-grid>
                ${this.vfolders.length>0?C``:C`
                      <div class="vertical layout center flex blank-box-medium">
                        <span>
                          ${X("session.launcher.NoAvailableFolderToMount")}
                        </span>
                      </div>
                    `}
              </div>
            </lablup-expansion>
            <lablup-expansion
              class="vfolder"
              name="vfolder"
              style="display:${this.enableInferenceWorkload?"block":"none"};"
            >
              <span slot="title">
                ${X("session.launcher.ModelStorageToMount")}
              </span>
              <div class="vfolder-list">
                <vaadin-grid
                  theme="no-border row-stripes column-borders compact dark"
                  id="model-folder-grid"
                  aria-label="model storage vfolder list"
                  height-by-rows
                  .items="${this.modelVfolders}"
                  @selected-items-changed="${()=>this._updateSelectedFolder()}"
                >
                  <vaadin-grid-selection-column
                    id="select-column"
                    flex-grow="0"
                    text-align="center"
                    auto-select
                  ></vaadin-grid-selection-column>
                  <vaadin-grid-filter-column
                    header="${X("session.launcher.ModelStorageToMount")}"
                    path="name"
                    resizable
                    .renderer="${this._boundFolderToMountListRenderer}"
                  ></vaadin-grid-filter-column>
                  <vaadin-grid-column
                    width="135px"
                    path=" ${X("session.launcher.FolderAlias")}"
                    .renderer="${this._boundFolderMapRenderer}"
                    .headerRenderer="${this._boundPathRenderer}"
                  ></vaadin-grid-column>
                </vaadin-grid>
              </div>
            </lablup-expansion>
            <lablup-expansion
              id="vfolder-mount-preview"
              class="vfolder"
              name="vfolder"
            >
              <span slot="title">${X("session.launcher.MountedFolders")}</span>
              <div class="vfolder-mounted-list">
                ${this.selectedVfolders.length>0||this.autoMountedVfolders.length>0?C`
                      <ul class="vfolder-list">
                        ${this.selectedVfolders.map((e=>C`
                            <li>
                              <mwc-icon>folder_open</mwc-icon>
                              ${e}
                              ${e in this.folderMapping?this.folderMapping[e].startsWith("/")?C`
                                      (&#10140; ${this.folderMapping[e]})
                                    `:C`
                                      (&#10140;
                                      /home/work/${this.folderMapping[e]})
                                    `:C`
                                    (&#10140; /home/work/${e})
                                  `}
                            </li>
                          `))}
                        ${this.autoMountedVfolders.map((e=>C`
                            <li>
                              <mwc-icon>folder_special</mwc-icon>
                              ${e.name}
                            </li>
                          `))}
                      </ul>
                    `:C`
                      <div class="vertical layout center flex blank-box-large">
                        <span>${X("session.launcher.NoFolderMounted")}</span>
                      </div>
                    `}
              </div>
            </lablup-expansion>
          </div>
          <div id="progress-03" class="progress center layout fade">
            <div class="horizontal center layout">
              <mwc-select
                id="scaling-groups"
                label="${V("session.launcher.ResourceGroup")}"
                icon="storage"
                required
                fixedMenuPosition
                @selected="${e=>this.updateScalingGroup(!0,e)}"
              >
                ${this.scaling_groups.map((e=>C`
                    <mwc-list-item
                      class="scaling-group-dropdown"
                      id="${e.name}"
                      graphic="icon"
                      value="${e.name}"
                    >
                      ${e.name}
                    </mwc-list-item>
                  `))}
              </mwc-select>
            </div>
            <div class="vertical center layout" style="position:relative;">
              <mwc-select
                id="resource-templates"
                label="${this.isEmpty(this.resource_templates_filtered)?"":V("session.launcher.ResourceAllocation")}"
                icon="dashboard_customize"
                ?required="${!this.isEmpty(this.resource_templates_filtered)}"
                fixedMenuPosition
              >
                <mwc-list-item
                  ?selected="${this.isEmpty(this.resource_templates_filtered)}"
                  style="display:none!important;"
                ></mwc-list-item>
                <h5
                  style="font-size:12px;padding: 0 10px 3px 15px;margin:0; border-bottom:1px solid var(--token-colorBorder, #ccc);"
                  role="separator"
                  disabled="true"
                  class="horizontal layout center"
                >
                  <div style="width:110px;">Name</div>
                  <div style="width:50px;text-align:right;">CPU</div>
                  <div style="width:50px;text-align:right;">RAM</div>
                  <div style="width:50px;text-align:right;">
                    ${X("session.launcher.SharedMemory")}
                  </div>
                  <div style="width:90px;text-align:right;">
                    ${X("session.launcher.Accelerator")}
                  </div>
                </h5>
                ${this.resource_templates_filtered.map((e=>C`
                    <mwc-list-item
                      value="${e.name}"
                      id="${e.name}-button"
                      @click="${e=>this._chooseResourceTemplate(e)}"
                      .cpu="${e.cpu}"
                      .mem="${e.mem}"
                      .cuda_device="${e.cuda_device}"
                      .cuda_shares="${e.cuda_shares}"
                      .rocm_device="${e.rocm_device}"
                      .tpu_device="${e.tpu_device}"
                      .ipu_device="${e.ipu_device}"
                      .atom_device="${e.atom_device}"
                      .atom_plus_device="${e.atom_plus_device}"
                      .gaudi2_device="${e.gaudi2_device}"
                      .warboy_device="${e.warboy_device}"
                      .rngd_device="${e.rngd_device}"
                      .hyperaccel_lpu_device="${e.hyperaccel_lpu_device}"
                      .shmem="${e.shmem}"
                    >
                      <div class="horizontal layout end-justified">
                        <div style="width:110px;">${e.name}</div>
                        <div style="display:none">(</div>
                        <div style="width:50px;text-align:right;">
                          ${e.cpu}
                          <span style="display:none">CPU</span>
                        </div>
                        <div style="width:50px;text-align:right;">
                          ${e.mem}GiB
                        </div>
                        <div style="width:60px;text-align:right;">
                          ${e.shmem?C`
                                ${parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(e.shared_memory,"g")).toFixed(2)}
                                GiB
                              `:C`
                                64MB
                              `}
                        </div>
                        <div style="width:80px;text-align:right;">
                          ${e.cuda_device&&e.cuda_device>0?C`
                                ${e.cuda_device} GPU
                              `:C``}
                          ${e.cuda_shares&&e.cuda_shares>0?C`
                                ${e.cuda_shares} GPU
                              `:C``}
                          ${e.rocm_device&&e.rocm_device>0?C`
                                ${e.rocm_device} GPU
                              `:C``}
                          ${e.tpu_device&&e.tpu_device>0?C`
                                ${e.tpu_device} TPU
                              `:C``}
                          ${e.ipu_device&&e.ipu_device>0?C`
                                ${e.ipu_device} IPU
                              `:C``}
                          ${e.atom_device&&e.atom_device>0?C`
                                ${e.atom_device} ATOM
                              `:C``}
                          ${e.atom_plus_device&&e.atom_plus_device>0?C`
                                ${e.atom_plus_device} ATOM+
                              `:C``}
                          ${e.gaudi2_device&&e.gaudi2_device>0?C`
                                ${e.gaudi2_device} Gaudi 2
                              `:C``}
                          ${e.warboy_device&&e.warboy_device>0?C`
                                ${e.warboy_device} Warboy
                              `:C``}
                          ${e.rngd_device&&e.rngd_device>0?C`
                                ${e.rngd_device} RNGD
                              `:C``}
                          ${e.hyperaccel_lpu_device&&e.hyperaccel_lpu_device>0?C`
                                ${e.hyperaccel_lpu_device} Hyperaccel LPU
                              `:C``}
                        </div>
                        <div style="display:none">)</div>
                      </div>
                    </mwc-list-item>
                  `))}
                ${this.isEmpty(this.resource_templates_filtered)?C`
                      <mwc-list-item
                        class="resource-button vertical center start layout"
                        role="option"
                        style="height:140px;width:350px;"
                        type="button"
                        flat
                        inverted
                        outlined
                        disabled
                        selected
                      >
                        <div>
                          <h4>${X("session.launcher.NoSuitablePreset")}</h4>
                          <div style="font-size:12px;">
                            Use advanced settings to
                            <br />
                            start custom session
                          </div>
                        </div>
                      </mwc-list-item>
                    `:C``}
              </mwc-select>
            </div>
            <lablup-expansion
              name="resource-group"
              style="display:${this.allowCustomResourceAllocation?"block":"none"}"
            >
              <span slot="title">
                ${X("session.launcher.CustomAllocation")}
              </span>
              <div class="vertical layout">
                <div>
                  <mwc-list-item hasMeta class="resource-type">
                    <div>CPU</div>
                    <mwc-icon-button
                      slot="meta"
                      icon="info"
                      class="fg info"
                      @click="${e=>this._showResourceDescription(e,"cpu")}"
                    ></mwc-icon-button>
                  </mwc-list-item>
                  <hr class="separator" />
                  <div class="slider-list-item">
                    <lablup-slider
                      id="cpu-resource"
                      class="cpu"
                      step="1"
                      pin
                      snaps
                      expand
                      editable
                      markers
                      tabindex="0"
                      @change="${e=>this._applyResourceValueChanges(e)}"
                      marker_limit="${this.marker_limit}"
                      suffix="${V("session.launcher.Core")}"
                      min="${this.cpu_metric.min}"
                      max="${this.cpu_metric.max}"
                      value="${this.cpu_request}"
                    ></lablup-slider>
                  </div>
                  <mwc-list-item hasMeta class="resource-type">
                    <div>RAM</div>
                    <mwc-icon-button
                      slot="meta"
                      icon="info"
                      class="fg info"
                      @click="${e=>this._showResourceDescription(e,"mem")}"
                    ></mwc-icon-button>
                  </mwc-list-item>
                  <hr class="separator" />
                  <div class="slider-list-item">
                    <lablup-slider
                      id="mem-resource"
                      class="mem"
                      pin
                      snaps
                      expand
                      step="0.05"
                      editable
                      markers
                      tabindex="0"
                      @change="${e=>{this._applyResourceValueChanges(e),this._updateShmemLimit()}}"
                      marker_limit="${this.marker_limit}"
                      suffix="GB"
                      min="${this.mem_metric.min}"
                      max="${this.mem_metric.max}"
                      value="${this.mem_request}"
                    ></lablup-slider>
                  </div>
                  <mwc-list-item hasMeta class="resource-type">
                    <div>${X("session.launcher.SharedMemory")}</div>
                    <mwc-icon-button
                      slot="meta"
                      icon="info"
                      class="fg info"
                      @click="${e=>this._showResourceDescription(e,"shmem")}"
                    ></mwc-icon-button>
                  </mwc-list-item>
                  <hr class="separator" />
                  <div class="slider-list-item">
                    <lablup-slider
                      id="shmem-resource"
                      class="mem"
                      pin
                      snaps
                      step="0.0125"
                      editable
                      markers
                      tabindex="0"
                      @change="${e=>{this._applyResourceValueChanges(e),this._updateShmemLimit()}}"
                      marker_limit="${this.marker_limit}"
                      suffix="GB"
                      min="0.0625"
                      max="${this.shmem_metric.max}"
                      value="${this.shmem_request}"
                    ></lablup-slider>
                  </div>
                  <mwc-list-item hasMeta class="resource-type">
                    <div>${X("webui.menu.AIAccelerator")}</div>
                    <mwc-icon-button
                      slot="meta"
                      icon="info"
                      class="fg info"
                      @click="${e=>this._showResourceDescription(e,"gpu")}"
                    ></mwc-icon-button>
                  </mwc-list-item>
                  <hr class="separator" />
                  <div class="slider-list-item">
                    <lablup-slider
                      id="gpu-resource"
                      class="gpu"
                      pin
                      snaps
                      editable
                      markers
                      step="${this.gpu_step}"
                      @change="${e=>this._applyResourceValueChanges(e)}"
                      marker_limit="${this.marker_limit}"
                      suffix="${this._NPUDeviceNameOnSlider}"
                      min="0.0"
                      max="${this.npu_device_metric.max}"
                      value="${this.gpu_request}"
                    ></lablup-slider>
                  </div>
                  <mwc-list-item hasMeta class="resource-type">
                    <div>${X("webui.menu.Sessions")}</div>
                    <mwc-icon-button
                      slot="meta"
                      icon="info"
                      class="fg info"
                      @click="${e=>this._showResourceDescription(e,"session")}"
                    ></mwc-icon-button>
                  </mwc-list-item>
                  <hr class="separator" />
                  <div class="slider-list-item">
                    <lablup-slider
                      id="session-resource"
                      class="session"
                      pin
                      snaps
                      editable
                      markers
                      step="1"
                      @change="${e=>this._applyResourceValueChanges(e)}"
                      marker_limit="${this.marker_limit}"
                      suffix="#"
                      min="1"
                      max="${this.concurrency_limit}"
                      value="${this.session_request}"
                    ></lablup-slider>
                  </div>
                </div>
              </div>
            </lablup-expansion>
            ${this.cluster_support?C`
                  <mwc-select
                    id="cluster-mode"
                    label="${V("session.launcher.ClusterMode")}"
                    required
                    icon="account_tree"
                    fixedMenuPosition
                    value="${this.cluster_mode}"
                    @change="${e=>this._setClusterMode(e)}"
                  >
                    ${this.cluster_mode_list.map((e=>C`
                        <mwc-list-item
                          class="cluster-mode-dropdown"
                          ?selected="${e===this.cluster_mode}"
                          id="${e}"
                          value="${e}"
                        >
                          <div
                            class="horizontal layout center"
                            style="width:100%;"
                          >
                            <p style="width:300px;margin-left:21px;">
                              ${X("single-node"===e?"session.launcher.SingleNode":"session.launcher.MultiNode")}
                            </p>
                            <mwc-icon-button
                              icon="info"
                              @click="${t=>this._showResourceDescription(t,e)}"
                            ></mwc-icon-button>
                          </div>
                        </mwc-list-item>
                      `))}
                  </mwc-select>
                  <div class="horizontal layout center flex center-justified">
                    <div>
                      <mwc-list-item
                        class="resource-type"
                        style="pointer-events: none;"
                      >
                        <div class="resource-type">
                          ${X("session.launcher.ClusterSize")}
                        </div>
                      </mwc-list-item>
                      <hr class="separator" />
                      <div class="slider-list-item">
                        <lablup-slider
                          id="cluster-size"
                          class="cluster"
                          pin
                          snaps
                          expand
                          editable
                          markers
                          step="1"
                          marker_limit="${this.marker_limit}"
                          min="${this.cluster_metric.min}"
                          max="${this.cluster_metric.max}"
                          value="${this.cluster_size}"
                          @change="${e=>this._applyResourceValueChanges(e,!1)}"
                          suffix="${"single-node"===this.cluster_mode?V("session.launcher.Container"):V("session.launcher.Node")}"
                        ></lablup-slider>
                      </div>
                    </div>
                  </div>
                `:C``}
            <lablup-expansion name="hpc-option-group">
              <span slot="title">
                ${X("session.launcher.HPCOptimization")}
              </span>
              <div class="vertical center layout">
                <div class="horizontal center center-justified flex layout">
                  <div style="width:313px;">
                    ${X("session.launcher.SwitchOpenMPoptimization")}
                  </div>
                  <mwc-switch
                    id="OpenMPswitch"
                    selected
                    @click="${this._toggleHPCOptimization}"
                  ></mwc-switch>
                </div>
                <div id="HPCOptimizationOptions" style="display:none;">
                  <div class="horizontal center layout">
                    <div style="width:200px;">
                      ${X("session.launcher.NumOpenMPthreads")}
                    </div>
                    <mwc-textfield
                      id="OpenMPCore"
                      type="number"
                      placeholder="1"
                      value=""
                      min="0"
                      max="1000"
                      step="1"
                      style="width:120px;"
                      pattern="[0-9]+"
                      @change="${e=>this._validateInput(e)}"
                    ></mwc-textfield>
                    <mwc-icon-button
                      icon="info"
                      class="fg green info"
                      @click="${e=>this._showResourceDescription(e,"openmp-optimization")}"
                    ></mwc-icon-button>
                  </div>
                  <div class="horizontal center layout">
                    <div style="width:200px;">
                      ${X("session.launcher.NumOpenBLASthreads")}
                    </div>
                    <mwc-textfield
                      id="OpenBLASCore"
                      type="number"
                      placeholder="1"
                      value=""
                      min="0"
                      max="1000"
                      step="1"
                      style="width:120px;"
                      pattern="[0-9]+"
                      @change="${e=>this._validateInput(e)}"
                    ></mwc-textfield>
                    <mwc-icon-button
                      icon="info"
                      class="fg green info"
                      @click="${e=>this._showResourceDescription(e,"openmp-optimization")}"
                    ></mwc-icon-button>
                  </div>
                </div>
              </div>
            </lablup-expansion>
          </div>
          <div id="progress-04" class="progress center layout fade">
            <p class="title">${X("session.SessionInfo")}</p>
            <div class="vertical layout cluster-total-allocation-container">
              ${this._preProcessingSessionInfo()?C`
                    <div
                      class="vertical layout"
                      style="margin-left:10px;margin-bottom:5px;"
                    >
                      <div class="horizontal layout">
                        <div style="margin-right:5px;width:150px;">
                          ${X("session.EnvironmentInfo")}
                        </div>
                        <div class="vertical layout">
                          <lablup-shields
                            app="${((null===(e=this.resourceBroker.imageInfo[this.sessionInfoObj.environment])||void 0===e?void 0:e.name)||this.sessionInfoObj.environment).toUpperCase()}"
                            color="green"
                            description="${this.sessionInfoObj.version[0]}"
                            ui="round"
                            style="margin-right:3px;"
                          ></lablup-shields>
                          <div class="horizontal layout">
                            ${this.sessionInfoObj.version.map(((e,t)=>t>0?C`
                                  <lablup-shields
                                    color="green"
                                    description="${e}"
                                    ui="round"
                                    style="margin-top:3px;margin-right:3px;"
                                  ></lablup-shields>
                                `:C``))}
                          </div>
                          <lablup-shields
                            color="blue"
                            description="${"inference"===this.mode?this.mode.toUpperCase():this.sessionType.toUpperCase()}"
                            ui="round"
                            style="margin-top:3px;margin-right:3px;margin-bottom:9px;"
                          ></lablup-shields>
                        </div>
                      </div>
                      <div class="horizontal layout">
                        <div
                          class="vertical layout"
                          style="margin-right:5px;width:150px;"
                        >
                          ${X("registry.ProjectName")}
                        </div>
                        <div class="vertical layout">
                          ${null===(t=globalThis.backendaiclient)||void 0===t?void 0:t.current_group}
                        </div>
                      </div>
                      <div class="horizontal layout">
                        <div
                          class="vertical layout"
                          style="margin-right:5px;width:150px;"
                        >
                          ${X("session.ResourceGroup")}
                        </div>
                        <div class="vertical layout">${this.scaling_group}</div>
                      </div>
                    </div>
                  `:C``}
            </div>
            <p class="title">${X("session.launcher.TotalAllocation")}</p>
            <div
              class="vertical layout center center-justified cluster-total-allocation-container"
            >
              <div
                id="cluster-allocation-pane"
                style="position:relative;${this.cluster_size<=1?"display:none;":""}"
              >
                <div class="horizontal layout resource-allocated-box">
                  <div
                    class="vertical layout center center-justified resource-allocated"
                  >
                    <p>${X("session.launcher.CPU")}</p>
                    <span>
                      ${this.cpu_request*this.cluster_size*this.session_request}
                    </span>
                    <p>Core</p>
                  </div>
                  <div
                    class="vertical layout center center-justified resource-allocated"
                  >
                    <p>${X("session.launcher.Memory")}</p>
                    <span>
                      ${this._roundResourceAllocation(this.mem_request*this.cluster_size*this.session_request,1)}
                    </span>
                    <p>GiB</p>
                  </div>
                  <div
                    class="vertical layout center center-justified resource-allocated"
                  >
                    <p>${X("session.launcher.SharedMemoryAbbr")}</p>
                    <span>
                      ${this._conditionalGiBtoMiB(this.shmem_request*this.cluster_size*this.session_request)}
                    </span>
                    <p>
                      ${this._conditionalGiBtoMiBunit(this.shmem_request*this.cluster_size*this.session_request)}
                    </p>
                  </div>
                  <div
                    class="vertical layout center center-justified resource-allocated"
                  >
                    <p>${this._acceleratorName(this.gpu_request_type)}</p>
                    <span>
                      ${this._roundResourceAllocation(this.gpu_request*this.cluster_size*this.session_request,2)}
                    </span>
                    <p>${X("session.launcher.GPUSlot")}</p>
                  </div>
                </div>
                <div style="height:1em"></div>
              </div>
              <div
                id="total-allocation-container"
                class="horizontal layout center center-justified allocation-check"
              >
                <div id="total-allocation-pane" style="position:relative;">
                  <div class="horizontal layout">
                    <div
                      class="vertical layout center center-justified resource-allocated"
                    >
                      <p>${X("session.launcher.CPU")}</p>
                      <span>${this.cpu_request}</span>
                      <p>Core</p>
                    </div>
                    <div
                      class="vertical layout center center-justified resource-allocated"
                    >
                      <p>${X("session.launcher.Memory")}</p>
                      <span>
                        ${this._roundResourceAllocation(this.mem_request,1)}
                      </span>
                      <p>GiB</p>
                    </div>
                    <div
                      class="vertical layout center center-justified resource-allocated"
                    >
                      <p>${X("session.launcher.SharedMemoryAbbr")}</p>
                      <span>
                        ${this._conditionalGiBtoMiB(this.shmem_request)}
                      </span>
                      <p>
                        ${this._conditionalGiBtoMiBunit(this.shmem_request)}
                      </p>
                    </div>
                    <div
                      class="vertical layout center center-justified resource-allocated"
                    >
                      <p>${this._acceleratorName(this.gpu_request_type)}</p>
                      <span>${this.gpu_request}</span>
                      <p>${X("session.launcher.GPUSlot")}</p>
                    </div>
                  </div>
                  <div id="resource-allocated-box-shadow"></div>
                </div>
                <div
                  class="vertical layout center center-justified cluster-allocated"
                  style="z-index:10;"
                >
                  <div class="horizontal layout">
                    <p>×</p>
                    <span>
                      ${this.cluster_size<=1?this.session_request:this.cluster_size}
                    </span>
                  </div>
                  <p class="small">${X("session.launcher.Container")}</p>
                </div>
                <div
                  class="vertical layout center center-justified cluster-allocated"
                  style="z-index:10;"
                >
                  <div class="horizontal layout">
                    <p>${this.cluster_mode,""}</p>
                    <span style="text-align:center;">
                      ${"single-node"===this.cluster_mode?X("session.launcher.SingleNode"):X("session.launcher.MultiNode")}
                    </span>
                  </div>
                  <p class="small">${X("session.launcher.AllocateNode")}</p>
                </div>
              </div>
            </div>
            ${"inference"!==this.mode?C`
                  <p class="title">${X("session.launcher.MountedFolders")}</p>
                  <div
                    id="mounted-folders-container"
                    class="cluster-total-allocation-container"
                  >
                    ${this.selectedVfolders.length>0||this.autoMountedVfolders.length>0?C`
                          <ul class="vfolder-list">
                            ${this.selectedVfolders.map((e=>C`
                                <li>
                                  <mwc-icon>folder_open</mwc-icon>
                                  ${e}
                                  ${e in this.folderMapping?this.folderMapping[e].startsWith("/")?C`
                                          (&#10140; ${this.folderMapping[e]})
                                        `:C`
                                          (&#10140;
                                          /home/work/${this.folderMapping[e]})
                                        `:C`
                                        (&#10140; /home/work/${e})
                                      `}
                                </li>
                              `))}
                            ${this.autoMountedVfolders.map((e=>C`
                                <li>
                                  <mwc-icon>folder_special</mwc-icon>
                                  ${e.name}
                                </li>
                              `))}
                          </ul>
                        `:C`
                          <div class="vertical layout center flex blank-box">
                            <span>
                              ${X("session.launcher.NoFolderMounted")}
                            </span>
                          </div>
                        `}
                  </div>
                `:C``}
            <p class="title">
              ${X("session.launcher.EnvironmentVariablePaneTitle")}
            </p>
            <div
              class="environment-variables-container cluster-total-allocation-container"
            >
              ${this.environ.length>0?C`
                    <div
                      class="horizontal flex center center-justified layout"
                      style="overflow-x:hidden;"
                    >
                      <div role="listbox">
                        <h4>
                          ${V("session.launcher.EnvironmentVariable")}
                        </h4>
                        ${this.environ.map((e=>C`
                            <mwc-textfield
                              disabled
                              value="${e.name}"
                            ></mwc-textfield>
                          `))}
                      </div>
                      <div role="listbox" style="margin-left:15px;">
                        <h4>
                          ${V("session.launcher.EnvironmentVariableValue")}
                        </h4>
                        ${this.environ.map((e=>C`
                            <mwc-textfield
                              disabled
                              value="${e.value}"
                            ></mwc-textfield>
                          `))}
                      </div>
                    </div>
                  `:C`
                    <div class="vertical layout center flex blank-box">
                      <span>${X("session.launcher.NoEnvConfigured")}</span>
                    </div>
                  `}
            </div>
            ${this.maxCountForPreopenPorts>0?C`
                  <p class="title">
                    ${X("session.launcher.PreOpenPortPanelTitle")}
                  </p>
                  <div
                    class="preopen-ports-container cluster-total-allocation-container"
                  >
                    ${this.preOpenPorts.length>0?C`
                          <div
                            class="horizontal flex center layout"
                            style="overflow-x:hidden;margin:auto 5px;"
                          >
                            ${this.preOpenPorts.map((e=>C`
                                <lablup-shields
                                  color="lightgrey"
                                  description="${e}"
                                  style="padding:4px;"
                                ></lablup-shields>
                              `))}
                          </div>
                        `:C`
                          <div class="vertical layout center flex blank-box">
                            <span>
                              ${X("session.launcher.NoPreOpenPortsConfigured")}
                            </span>
                          </div>
                        `}
                  </div>
                `:C``}
          </div>
        </form>
        <div slot="footer" class="vertical flex layout">
          <div class="horizontal flex layout distancing center-center">
            <mwc-icon-button
              id="prev-button"
              icon="arrow_back"
              style="visibility:hidden;margin-right:12px;"
              @click="${()=>this.moveProgress(-1)}"
            ></mwc-icon-button>
            <mwc-button
              unelevated
              class="launch-button"
              id="launch-button"
              icon="rowing"
              @click="${()=>this._newSessionWithConfirmation()}"
            >
              <span id="launch-button-msg">
                ${this.launchButtonMessageTextContent}
              </span>
            </mwc-button>
            <mwc-icon-button
              id="next-button"
              icon="arrow_forward"
              style="margin-left:12px;"
              @click="${()=>this.moveProgress(1)}"
            ></mwc-icon-button>
          </div>
          <div class="horizontal flex layout">
            <lablup-progress-bar
              progress="${this._calculateProgress()}"
            ></lablup-progress-bar>
          </div>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog
        id="modify-env-dialog"
        fixed
        backdrop
        persistent
        closeWithConfirmation
      >
        <span slot="title">
          ${X("session.launcher.SetEnvironmentVariable")}
        </span>
        <span slot="action">
          <mwc-icon-button
            icon="info"
            @click="${e=>this._showEnvConfigDescription(e)}"
            style="pointer-events: auto;"
          ></mwc-icon-button>
        </span>
        <div slot="content" id="modify-env-container">
          <div class="horizontal layout center flex justified header">
            <div>${X("session.launcher.EnvironmentVariable")}</div>
            <div>${X("session.launcher.EnvironmentVariableValue")}</div>
          </div>
          <div id="modify-env-fields-container" class="layout center">
            ${this.environ.forEach((e=>C`
                <div class="horizontal layout center row">
                  <mwc-textfield value="${e.name}"></mwc-textfield>
                  <mwc-textfield value="${e.value}"></mwc-textfield>
                  <mwc-icon-button
                    class="green minus-btn"
                    icon="remove"
                    @click="${e=>this._removeEnvItem(e)}"
                  ></mwc-icon-button>
                </div>
              `))}
            <div class="horizontal layout center row">
              <mwc-textfield></mwc-textfield>
              <mwc-textfield></mwc-textfield>
              <mwc-icon-button
                class="green minus-btn"
                icon="remove"
                @click="${e=>this._removeEnvItem(e)}"
              ></mwc-icon-button>
            </div>
          </div>
          <mwc-button
            id="env-add-btn"
            outlined
            icon="add"
            class="horizontal flex layout center"
            @click="${()=>this._appendEnvRow()}"
          >
            Add
          </mwc-button>
        </div>
        <div slot="footer" class="horizontal layout">
          <mwc-button
            class="delete-all-button"
            slot="footer"
            icon="delete"
            style="width:100px"
            label="${V("button.Reset")}"
            @click="${()=>this._clearEnvRows()}"
          ></mwc-button>
          <mwc-button
            unelevated
            slot="footer"
            icon="check"
            style="width:100px"
            label="${V("button.Save")}"
            @click="${()=>this.modifyEnv()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog
        id="modify-preopen-ports-dialog"
        fixed
        backdrop
        persistent
        closeWithConfirmation
      >
        <span slot="title">${X("session.launcher.SetPreopenPorts")}</span>
        <span slot="action">
          <mwc-icon-button
            icon="info"
            @click="${e=>this._showPreOpenPortConfigDescription(e)}"
            style="pointer-events: auto;"
          ></mwc-icon-button>
        </span>
        <div slot="content" id="modify-preopen-ports-container">
          <div class="horizontal layout center flex justified header">
            <div>${X("session.launcher.PortsTitleWithRange")}</div>
          </div>
          <div class="layout center">
            ${this.preOpenPorts.forEach((e=>C`
                <div class="horizontal layout center row">
                  <mwc-textfield
                    value="${e}"
                    type="number"
                    min="1024"
                    max="65535"
                  ></mwc-textfield>
                  <mwc-icon-button
                    class="green minus-btn"
                    icon="remove"
                    @click="${e=>this._removePreOpenPortItem(e)}"
                  ></mwc-icon-button>
                </div>
              `))}
            <div class="horizontal layout center row">
              <mwc-textfield
                type="number"
                min="1024"
                max="65535"
              ></mwc-textfield>
              <mwc-icon-button
                class="green minus-btn"
                icon="remove"
                @click="${e=>this._removePreOpenPortItem(e)}"
              ></mwc-icon-button>
            </div>
          </div>
          <mwc-button
            id="preopen-ports-add-btn"
            outlined
            icon="add"
            class="horizontal flex layout center"
            ?disabled="${this.isExceedMaxCountForPreopenPorts}"
            @click="${()=>this._appendPreOpenPortRow()}"
          >
            Add
          </mwc-button>
        </div>
        <div slot="footer" class="horizontal layout">
          <mwc-button
            class="delete-all-button"
            slot="footer"
            icon="delete"
            style="width:100px"
            label="${V("button.Reset")}"
            @click="${()=>this._clearPreOpenPortRows()}"
          ></mwc-button>
          <mwc-button
            unelevated
            slot="footer"
            icon="check"
            style="width:100px"
            label="${V("button.Save")}"
            @click="${()=>this.modifyPreOpenPorts()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="help-description" fixed backdrop>
        <span slot="title">${this._helpDescriptionTitle}</span>
        <div
          slot="content"
          class="horizontal layout center"
          style="margin:5px;"
        >
          ${""==this._helpDescriptionIcon?C``:C`
                <img
                  slot="graphic"
                  alt="help icon"
                  src="resources/icons/${this._helpDescriptionIcon}"
                  style="width:64px;height:64px;margin-right:10px;"
                />
              `}
          <div style="font-size:14px;">
            ${Y(this._helpDescription)}
          </div>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="launch-confirmation-dialog" warning fixed backdrop>
        <span slot="title">${X("session.launcher.NoFolderMounted")}</span>
        <div slot="content" class="vertical layout">
          <p>${X("session.launcher.HomeDirectoryDeletionDialog")}</p>
          <p>${X("session.launcher.LaunchConfirmationDialog")}</p>
          <p>${X("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            unelevated
            class="launch-confirmation-button"
            id="launch-confirmation-button"
            icon="rowing"
            @click="${()=>this._newSession()}"
          >
            ${X("session.launcher.Launch")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="env-config-confirmation" warning fixed>
        <span slot="title">${X("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${X("session.launcher.EnvConfigWillDisappear")}</p>
          <p>${X("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            id="env-config-remain-button"
            label="${V("button.Cancel")}"
            @click="${()=>this.closeDialog("env-config-confirmation")}"
            style="width:auto;margin-right:10px;"
          ></mwc-button>
          <mwc-button
            unelevated
            id="env-config-reset-button"
            label="${V("button.DismissAndProceed")}"
            @click="${()=>this._closeAndResetEnvInput()}"
            style="width:auto;"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="preopen-ports-config-confirmation" warning fixed>
        <span slot="title">${X("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${X("session.launcher.PrePortConfigWillDisappear")}</p>
          <p>${X("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            id="preopen-ports-remain-button"
            label="${V("button.Cancel")}"
            @click="${()=>this.closeDialog("preopen-ports-config-confirmation")}"
            style="width:auto;margin-right:10px;"
          ></mwc-button>
          <mwc-button
            unelevated
            id="preopen-ports-config-reset-button"
            label="${V("button.DismissAndProceed")}"
            @click="${()=>this._closeAndResetPreOpenPortInput()}"
            style="width:auto;"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};o([f({type:Boolean})],cc.prototype,"is_connected",void 0),o([f({type:Boolean})],cc.prototype,"enableLaunchButton",void 0),o([f({type:Boolean})],cc.prototype,"hideLaunchButton",void 0),o([f({type:Boolean})],cc.prototype,"hideEnvDialog",void 0),o([f({type:Boolean})],cc.prototype,"hidePreOpenPortDialog",void 0),o([f({type:Boolean})],cc.prototype,"enableInferenceWorkload",void 0),o([f({type:String})],cc.prototype,"location",void 0),o([f({type:String})],cc.prototype,"mode",void 0),o([f({type:String})],cc.prototype,"newSessionDialogTitle",void 0),o([f({type:String})],cc.prototype,"importScript",void 0),o([f({type:String})],cc.prototype,"importFilename",void 0),o([f({type:Object})],cc.prototype,"imageRequirements",void 0),o([f({type:Object})],cc.prototype,"resourceLimits",void 0),o([f({type:Object})],cc.prototype,"userResourceLimit",void 0),o([f({type:Object})],cc.prototype,"aliases",void 0),o([f({type:Object})],cc.prototype,"tags",void 0),o([f({type:Object})],cc.prototype,"icons",void 0),o([f({type:Object})],cc.prototype,"imageInfo",void 0),o([f({type:String})],cc.prototype,"kernel",void 0),o([f({type:Array})],cc.prototype,"versions",void 0),o([f({type:Array})],cc.prototype,"languages",void 0),o([f({type:Number})],cc.prototype,"marker_limit",void 0),o([f({type:String})],cc.prototype,"gpu_mode",void 0),o([f({type:Array})],cc.prototype,"gpu_modes",void 0),o([f({type:Number})],cc.prototype,"gpu_step",void 0),o([f({type:Object})],cc.prototype,"cpu_metric",void 0),o([f({type:Object})],cc.prototype,"mem_metric",void 0),o([f({type:Object})],cc.prototype,"shmem_metric",void 0),o([f({type:Object})],cc.prototype,"npu_device_metric",void 0),o([f({type:Object})],cc.prototype,"cuda_shares_metric",void 0),o([f({type:Object})],cc.prototype,"rocm_device_metric",void 0),o([f({type:Object})],cc.prototype,"tpu_device_metric",void 0),o([f({type:Object})],cc.prototype,"ipu_device_metric",void 0),o([f({type:Object})],cc.prototype,"atom_device_metric",void 0),o([f({type:Object})],cc.prototype,"atom_plus_device_metric",void 0),o([f({type:Object})],cc.prototype,"gaudi2_device_metric",void 0),o([f({type:Object})],cc.prototype,"warboy_device_metric",void 0),o([f({type:Object})],cc.prototype,"rngd_device_metric",void 0),o([f({type:Object})],cc.prototype,"hyperaccel_lpu_device_metric",void 0),o([f({type:Object})],cc.prototype,"cluster_metric",void 0),o([f({type:Array})],cc.prototype,"cluster_mode_list",void 0),o([f({type:Boolean})],cc.prototype,"cluster_support",void 0),o([f({type:Object})],cc.prototype,"images",void 0),o([f({type:Object})],cc.prototype,"total_slot",void 0),o([f({type:Object})],cc.prototype,"total_resource_group_slot",void 0),o([f({type:Object})],cc.prototype,"total_project_slot",void 0),o([f({type:Object})],cc.prototype,"used_slot",void 0),o([f({type:Object})],cc.prototype,"used_resource_group_slot",void 0),o([f({type:Object})],cc.prototype,"used_project_slot",void 0),o([f({type:Object})],cc.prototype,"available_slot",void 0),o([f({type:Number})],cc.prototype,"concurrency_used",void 0),o([f({type:Number})],cc.prototype,"concurrency_max",void 0),o([f({type:Number})],cc.prototype,"concurrency_limit",void 0),o([f({type:Number})],cc.prototype,"max_containers_per_session",void 0),o([f({type:Array})],cc.prototype,"vfolders",void 0),o([f({type:Array})],cc.prototype,"selectedVfolders",void 0),o([f({type:Array})],cc.prototype,"autoMountedVfolders",void 0),o([f({type:Array})],cc.prototype,"modelVfolders",void 0),o([f({type:Array})],cc.prototype,"nonAutoMountedVfolders",void 0),o([f({type:Object})],cc.prototype,"folderMapping",void 0),o([f({type:Object})],cc.prototype,"customFolderMapping",void 0),o([f({type:Object})],cc.prototype,"used_slot_percent",void 0),o([f({type:Object})],cc.prototype,"used_resource_group_slot_percent",void 0),o([f({type:Object})],cc.prototype,"used_project_slot_percent",void 0),o([f({type:Array})],cc.prototype,"resource_templates",void 0),o([f({type:Array})],cc.prototype,"resource_templates_filtered",void 0),o([f({type:String})],cc.prototype,"default_language",void 0),o([f({type:Number})],cc.prototype,"cpu_request",void 0),o([f({type:Number})],cc.prototype,"mem_request",void 0),o([f({type:Number})],cc.prototype,"shmem_request",void 0),o([f({type:Number})],cc.prototype,"gpu_request",void 0),o([f({type:String})],cc.prototype,"gpu_request_type",void 0),o([f({type:Number})],cc.prototype,"session_request",void 0),o([f({type:Boolean})],cc.prototype,"_status",void 0),o([f({type:Number})],cc.prototype,"num_sessions",void 0),o([f({type:String})],cc.prototype,"scaling_group",void 0),o([f({type:Array})],cc.prototype,"scaling_groups",void 0),o([f({type:Array})],cc.prototype,"sessions_list",void 0),o([f({type:Boolean})],cc.prototype,"metric_updating",void 0),o([f({type:Boolean})],cc.prototype,"metadata_updating",void 0),o([f({type:Boolean})],cc.prototype,"aggregate_updating",void 0),o([f({type:Object})],cc.prototype,"scaling_group_selection_box",void 0),o([f({type:Object})],cc.prototype,"resourceGauge",void 0),o([f({type:String})],cc.prototype,"sessionType",void 0),o([f({type:Boolean})],cc.prototype,"ownerFeatureInitialized",void 0),o([f({type:String})],cc.prototype,"ownerDomain",void 0),o([f({type:Array})],cc.prototype,"ownerKeypairs",void 0),o([f({type:Array})],cc.prototype,"ownerGroups",void 0),o([f({type:Array})],cc.prototype,"ownerScalingGroups",void 0),o([f({type:Boolean})],cc.prototype,"project_resource_monitor",void 0),o([f({type:Boolean})],cc.prototype,"_default_language_updated",void 0),o([f({type:Boolean})],cc.prototype,"_default_version_updated",void 0),o([f({type:String})],cc.prototype,"_helpDescription",void 0),o([f({type:String})],cc.prototype,"_helpDescriptionTitle",void 0),o([f({type:String})],cc.prototype,"_helpDescriptionIcon",void 0),o([f({type:String})],cc.prototype,"_NPUDeviceNameOnSlider",void 0),o([f({type:Number})],cc.prototype,"max_cpu_core_per_session",void 0),o([f({type:Number})],cc.prototype,"max_mem_per_container",void 0),o([f({type:Number})],cc.prototype,"max_cuda_device_per_container",void 0),o([f({type:Number})],cc.prototype,"max_cuda_shares_per_container",void 0),o([f({type:Number})],cc.prototype,"max_rocm_device_per_container",void 0),o([f({type:Number})],cc.prototype,"max_tpu_device_per_container",void 0),o([f({type:Number})],cc.prototype,"max_ipu_device_per_container",void 0),o([f({type:Number})],cc.prototype,"max_atom_device_per_container",void 0),o([f({type:Number})],cc.prototype,"max_atom_plus_device_per_container",void 0),o([f({type:Number})],cc.prototype,"max_gaudi2_device_per_container",void 0),o([f({type:Number})],cc.prototype,"max_warboy_device_per_container",void 0),o([f({type:Number})],cc.prototype,"max_rngd_device_per_container",void 0),o([f({type:Number})],cc.prototype,"max_hyperaccel_lpu_device_per_container",void 0),o([f({type:Number})],cc.prototype,"max_shm_per_container",void 0),o([f({type:Boolean})],cc.prototype,"allow_manual_image_name_for_session",void 0),o([f({type:Object})],cc.prototype,"resourceBroker",void 0),o([f({type:Number})],cc.prototype,"cluster_size",void 0),o([f({type:String})],cc.prototype,"cluster_mode",void 0),o([f({type:Object})],cc.prototype,"deleteEnvInfo",void 0),o([f({type:Object})],cc.prototype,"deleteEnvRow",void 0),o([f({type:Array})],cc.prototype,"environ",void 0),o([f({type:Array})],cc.prototype,"preOpenPorts",void 0),o([f({type:Object})],cc.prototype,"environ_values",void 0),o([f({type:Object})],cc.prototype,"vfolder_select_expansion",void 0),o([f({type:Number})],cc.prototype,"currentIndex",void 0),o([f({type:Number})],cc.prototype,"progressLength",void 0),o([f({type:Object})],cc.prototype,"_nonAutoMountedFolderGrid",void 0),o([f({type:Object})],cc.prototype,"_modelFolderGrid",void 0),o([f({type:Boolean})],cc.prototype,"_debug",void 0),o([f({type:Object})],cc.prototype,"_boundFolderToMountListRenderer",void 0),o([f({type:Object})],cc.prototype,"_boundFolderMapRenderer",void 0),o([f({type:Object})],cc.prototype,"_boundPathRenderer",void 0),o([f({type:String})],cc.prototype,"scheduledTime",void 0),o([f({type:Object})],cc.prototype,"schedulerTimer",void 0),o([f({type:Object})],cc.prototype,"sessionInfoObj",void 0),o([f({type:String})],cc.prototype,"launchButtonMessageTextContent",void 0),o([f({type:Boolean})],cc.prototype,"isExceedMaxCountForPreopenPorts",void 0),o([f({type:Number})],cc.prototype,"maxCountForPreopenPorts",void 0),o([f({type:Boolean})],cc.prototype,"allowCustomResourceAllocation",void 0),o([f({type:Boolean})],cc.prototype,"allowNEOSessionLauncher",void 0),o([g("#image-name")],cc.prototype,"manualImageName",void 0),o([g("#version")],cc.prototype,"version_selector",void 0),o([g("#environment")],cc.prototype,"environment",void 0),o([g("#owner-group")],cc.prototype,"ownerGroupSelect",void 0),o([g("#scaling-groups")],cc.prototype,"scalingGroups",void 0),o([g("#resource-templates")],cc.prototype,"resourceTemplatesSelect",void 0),o([g("#owner-scaling-group")],cc.prototype,"ownerScalingGroupSelect",void 0),o([g("#owner-accesskey")],cc.prototype,"ownerAccesskeySelect",void 0),o([g("#owner-email")],cc.prototype,"ownerEmailInput",void 0),o([g("#vfolder-mount-preview")],cc.prototype,"vfolderMountPreview",void 0),o([g("#launch-button")],cc.prototype,"launchButton",void 0),o([g("#prev-button")],cc.prototype,"prevButton",void 0),o([g("#next-button")],cc.prototype,"nextButton",void 0),o([g("#OpenMPswitch")],cc.prototype,"openMPSwitch",void 0),o([g("#cpu-resource")],cc.prototype,"cpuResourceSlider",void 0),o([g("#gpu-resource")],cc.prototype,"npuResourceSlider",void 0),o([g("#mem-resource")],cc.prototype,"memoryResourceSlider",void 0),o([g("#shmem-resource")],cc.prototype,"sharedMemoryResourceSlider",void 0),o([g("#session-resource")],cc.prototype,"sessionResourceSlider",void 0),o([g("#cluster-size")],cc.prototype,"clusterSizeSlider",void 0),o([g("#launch-button-msg")],cc.prototype,"launchButtonMessage",void 0),o([g("#new-session-dialog")],cc.prototype,"newSessionDialog",void 0),o([g("#modify-env-dialog")],cc.prototype,"modifyEnvDialog",void 0),o([g("#modify-env-container")],cc.prototype,"modifyEnvContainer",void 0),o([g("#modify-preopen-ports-dialog")],cc.prototype,"modifyPreOpenPortDialog",void 0),o([g("#modify-preopen-ports-container")],cc.prototype,"modifyPreOpenPortContainer",void 0),o([g("#launch-confirmation-dialog")],cc.prototype,"launchConfirmationDialog",void 0),o([g("#help-description")],cc.prototype,"helpDescriptionDialog",void 0),o([g("#command-editor")],cc.prototype,"commandEditor",void 0),o([g("#session-name")],cc.prototype,"sessionName",void 0),o([g("backend-ai-react-batch-session-scheduled-time-setting")],cc.prototype,"batchSessionDatePicker",void 0),cc=o([v("backend-ai-session-launcher")],cc);
