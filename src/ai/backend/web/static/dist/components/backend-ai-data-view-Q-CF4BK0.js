import{G as e,H as t,M as i,_ as o,J as r,K as a,L as s,N as d,U as l,V as n,W as c,X as h,Y as p,r as u,i as m,p as g,E as f,T as v,q as b,P as y,n as _,e as w,Z as x,t as $,B as k,b as F,I as S,a as T,c as I,k as R,f as C,g as D,s as N,l as E,Q as P,d as L,A as O}from"./backend-ai-webui-CrYAk2kU.js";import"./backend-ai-list-status-3rh750mO.js";import"./backend-ai-session-launcher-DTKcsfIH.js";import"./mwc-formfield-vL2NZ4ur.js";import"./lablup-loading-spinner-uf3p4g34.js";import"./vaadin-item-cN1jHkT4.js";import"./mwc-switch-DBXdshNs.js";import"./mwc-tab-bar-CsHxdw_J.js";import"./lablup-progress-bar-DHMPQCRx.js";import"./mwc-check-list-item-GAU3w8ue.js";import"./vaadin-item-mixin-BPsCvSRg.js";
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const z=(e,t)=>"method"===t.kind&&t.descriptor&&!("value"in t.descriptor)?{...t,finisher(i){i.createProperty(t.key,e)}}:{kind:"field",key:Symbol(),placement:"own",descriptor:{},originalKey:t.key,initializer(){"function"==typeof t.initializer&&(this[t.key]=t.initializer.call(this))},finisher(i){i.createProperty(t.key,e)}},A=(e,t,i)=>{t.constructor.createProperty(i,e)};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */function M(e){return(t,i)=>void 0!==i?A(e,t,i):z(e,t)
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */}function U(e){return M({...e,state:!0})}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const j=({finisher:e,descriptor:t})=>(i,o)=>{var r;if(void 0===o){const o=null!==(r=i.originalKey)&&void 0!==r?r:i.key,a=null!=t?{kind:"method",placement:"prototype",key:o,descriptor:t(i.key)}:{...i,key:o};return null!=e&&(a.finisher=function(t){e(t,o)}),a}{const r=i.constructor;void 0!==t&&Object.defineProperty(i,o,t(o)),null==e||e(r,o)}}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function B(e,t){return j({descriptor:t=>{const i={get(){var t,i;return null!==(i=null===(t=this.renderRoot)||void 0===t?void 0:t.querySelector(e))&&void 0!==i?i:null},enumerable:!0,configurable:!0};return i}})}
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
var V;null===(V=window.HTMLSlotElement)||void 0===V||V.prototype.assignedElements;
/**
 * @license
 * Copyright 2020 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
const q=Symbol("selection controller");class G{constructor(){this.selected=null,this.ordered=null,this.set=new Set}}class Q{constructor(e){this.sets={},this.focusedSet=null,this.mouseIsDown=!1,this.updating=!1,e.addEventListener("keydown",(e=>{this.keyDownHandler(e)})),e.addEventListener("mousedown",(()=>{this.mousedownHandler()})),e.addEventListener("mouseup",(()=>{this.mouseupHandler()}))}static getController(e){const t=!("global"in e)||"global"in e&&e.global?document:e.getRootNode();let i=t[q];return void 0===i&&(i=new Q(t),t[q]=i),i}keyDownHandler(e){const t=e.target;"checked"in t&&this.has(t)&&("ArrowRight"==e.key||"ArrowDown"==e.key?this.selectNext(t):"ArrowLeft"!=e.key&&"ArrowUp"!=e.key||this.selectPrevious(t))}mousedownHandler(){this.mouseIsDown=!0}mouseupHandler(){this.mouseIsDown=!1}has(e){return this.getSet(e.name).set.has(e)}selectPrevious(e){const t=this.getOrdered(e),i=t.indexOf(e),o=t[i-1]||t[t.length-1];return this.select(o),o}selectNext(e){const t=this.getOrdered(e),i=t.indexOf(e),o=t[i+1]||t[0];return this.select(o),o}select(e){e.click()}focus(e){if(this.mouseIsDown)return;const t=this.getSet(e.name),i=this.focusedSet;this.focusedSet=t,i!=t&&t.selected&&t.selected!=e&&t.selected.focus()}isAnySelected(e){const t=this.getSet(e.name);for(const e of t.set)if(e.checked)return!0;return!1}getOrdered(e){const t=this.getSet(e.name);return t.ordered||(t.ordered=Array.from(t.set),t.ordered.sort(((e,t)=>e.compareDocumentPosition(t)==Node.DOCUMENT_POSITION_PRECEDING?1:0))),t.ordered}getSet(e){return this.sets[e]||(this.sets[e]=new G),this.sets[e]}register(e){const t=e.name||e.getAttribute("name")||"",i=this.getSet(t);i.set.add(e),i.ordered=null}unregister(e){const t=this.getSet(e.name);t.set.delete(e),t.ordered=null,t.selected==e&&(t.selected=null)}update(e){if(this.updating)return;this.updating=!0;const t=this.getSet(e.name);if(e.checked){for(const i of t.set)i!=e&&(i.checked=!1);t.selected=e}if(this.isAnySelected(e))for(const e of t.set){if(void 0===e.formElementTabIndex)break;e.formElementTabIndex=e.checked?0:-1}this.updating=!1}}
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
 */var H={NATIVE_CONTROL_SELECTOR:".mdc-radio__native-control"},W={DISABLED:"mdc-radio--disabled",ROOT:"mdc-radio"},X=function(i){function o(e){return i.call(this,t(t({},o.defaultAdapter),e))||this}return e(o,i),Object.defineProperty(o,"cssClasses",{get:function(){return W},enumerable:!1,configurable:!0}),Object.defineProperty(o,"strings",{get:function(){return H},enumerable:!1,configurable:!0}),Object.defineProperty(o,"defaultAdapter",{get:function(){return{addClass:function(){},removeClass:function(){},setNativeControlDisabled:function(){}}},enumerable:!1,configurable:!0}),o.prototype.setDisabled=function(e){var t=o.cssClasses.DISABLED;this.adapter.setNativeControlDisabled(e),e?this.adapter.addClass(t):this.adapter.removeClass(t)},o}(i);
/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const K=window,J=K.ShadowRoot&&(void 0===K.ShadyCSS||K.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,Z=Symbol(),Y=new WeakMap;let ee=class{constructor(e,t,i){if(this._$cssResult$=!0,i!==Z)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const t=this.t;if(J&&void 0===e){const i=void 0!==t&&1===t.length;i&&(e=Y.get(t)),void 0===e&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),i&&Y.set(t,e))}return e}toString(){return this.cssText}};const te=(e,t)=>{J?e.adoptedStyleSheets=t.map((e=>e instanceof CSSStyleSheet?e:e.styleSheet)):t.forEach((t=>{const i=document.createElement("style"),o=K.litNonce;void 0!==o&&i.setAttribute("nonce",o),i.textContent=t.cssText,e.appendChild(i)}))},ie=J?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t="";for(const i of e.cssRules)t+=i.cssText;return(e=>new ee("string"==typeof e?e:e+"",void 0,Z))(t)})(e):e
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */;var oe;const re=window,ae=re.trustedTypes,se=ae?ae.emptyScript:"",de=re.reactiveElementPolyfillSupport,le={toAttribute(e,t){switch(t){case Boolean:e=e?se:null;break;case Object:case Array:e=null==e?e:JSON.stringify(e)}return e},fromAttribute(e,t){let i=e;switch(t){case Boolean:i=null!==e;break;case Number:i=null===e?null:Number(e);break;case Object:case Array:try{i=JSON.parse(e)}catch(e){i=null}}return i}},ne=(e,t)=>t!==e&&(t==t||e==e),ce={attribute:!0,type:String,converter:le,reflect:!1,hasChanged:ne},he="finalized";class pe extends HTMLElement{constructor(){super(),this._$Ei=new Map,this.isUpdatePending=!1,this.hasUpdated=!1,this._$El=null,this._$Eu()}static addInitializer(e){var t;this.finalize(),(null!==(t=this.h)&&void 0!==t?t:this.h=[]).push(e)}static get observedAttributes(){this.finalize();const e=[];return this.elementProperties.forEach(((t,i)=>{const o=this._$Ep(i,t);void 0!==o&&(this._$Ev.set(o,i),e.push(o))})),e}static createProperty(e,t=ce){if(t.state&&(t.attribute=!1),this.finalize(),this.elementProperties.set(e,t),!t.noAccessor&&!this.prototype.hasOwnProperty(e)){const i="symbol"==typeof e?Symbol():"__"+e,o=this.getPropertyDescriptor(e,i,t);void 0!==o&&Object.defineProperty(this.prototype,e,o)}}static getPropertyDescriptor(e,t,i){return{get(){return this[t]},set(o){const r=this[e];this[t]=o,this.requestUpdate(e,r,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)||ce}static finalize(){if(this.hasOwnProperty(he))return!1;this[he]=!0;const e=Object.getPrototypeOf(this);if(e.finalize(),void 0!==e.h&&(this.h=[...e.h]),this.elementProperties=new Map(e.elementProperties),this._$Ev=new Map,this.hasOwnProperty("properties")){const e=this.properties,t=[...Object.getOwnPropertyNames(e),...Object.getOwnPropertySymbols(e)];for(const i of t)this.createProperty(i,e[i])}return this.elementStyles=this.finalizeStyles(this.styles),!0}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const i=new Set(e.flat(1/0).reverse());for(const e of i)t.unshift(ie(e))}else void 0!==e&&t.push(ie(e));return t}static _$Ep(e,t){const i=t.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof e?e.toLowerCase():void 0}_$Eu(){var e;this._$E_=new Promise((e=>this.enableUpdating=e)),this._$AL=new Map,this._$Eg(),this.requestUpdate(),null===(e=this.constructor.h)||void 0===e||e.forEach((e=>e(this)))}addController(e){var t,i;(null!==(t=this._$ES)&&void 0!==t?t:this._$ES=[]).push(e),void 0!==this.renderRoot&&this.isConnected&&(null===(i=e.hostConnected)||void 0===i||i.call(e))}removeController(e){var t;null===(t=this._$ES)||void 0===t||t.splice(this._$ES.indexOf(e)>>>0,1)}_$Eg(){this.constructor.elementProperties.forEach(((e,t)=>{this.hasOwnProperty(t)&&(this._$Ei.set(t,this[t]),delete this[t])}))}createRenderRoot(){var e;const t=null!==(e=this.shadowRoot)&&void 0!==e?e:this.attachShadow(this.constructor.shadowRootOptions);return te(t,this.constructor.elementStyles),t}connectedCallback(){var e;void 0===this.renderRoot&&(this.renderRoot=this.createRenderRoot()),this.enableUpdating(!0),null===(e=this._$ES)||void 0===e||e.forEach((e=>{var t;return null===(t=e.hostConnected)||void 0===t?void 0:t.call(e)}))}enableUpdating(e){}disconnectedCallback(){var e;null===(e=this._$ES)||void 0===e||e.forEach((e=>{var t;return null===(t=e.hostDisconnected)||void 0===t?void 0:t.call(e)}))}attributeChangedCallback(e,t,i){this._$AK(e,i)}_$EO(e,t,i=ce){var o;const r=this.constructor._$Ep(e,i);if(void 0!==r&&!0===i.reflect){const a=(void 0!==(null===(o=i.converter)||void 0===o?void 0:o.toAttribute)?i.converter:le).toAttribute(t,i.type);this._$El=e,null==a?this.removeAttribute(r):this.setAttribute(r,a),this._$El=null}}_$AK(e,t){var i;const o=this.constructor,r=o._$Ev.get(e);if(void 0!==r&&this._$El!==r){const e=o.getPropertyOptions(r),a="function"==typeof e.converter?{fromAttribute:e.converter}:void 0!==(null===(i=e.converter)||void 0===i?void 0:i.fromAttribute)?e.converter:le;this._$El=r,this[r]=a.fromAttribute(t,e.type),this._$El=null}}requestUpdate(e,t,i){let o=!0;void 0!==e&&(((i=i||this.constructor.getPropertyOptions(e)).hasChanged||ne)(this[e],t)?(this._$AL.has(e)||this._$AL.set(e,t),!0===i.reflect&&this._$El!==e&&(void 0===this._$EC&&(this._$EC=new Map),this._$EC.set(e,i))):o=!1),!this.isUpdatePending&&o&&(this._$E_=this._$Ej())}async _$Ej(){this.isUpdatePending=!0;try{await this._$E_}catch(e){Promise.reject(e)}const e=this.scheduleUpdate();return null!=e&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){var e;if(!this.isUpdatePending)return;this.hasUpdated,this._$Ei&&(this._$Ei.forEach(((e,t)=>this[t]=e)),this._$Ei=void 0);let t=!1;const i=this._$AL;try{t=this.shouldUpdate(i),t?(this.willUpdate(i),null===(e=this._$ES)||void 0===e||e.forEach((e=>{var t;return null===(t=e.hostUpdate)||void 0===t?void 0:t.call(e)})),this.update(i)):this._$Ek()}catch(e){throw t=!1,this._$Ek(),e}t&&this._$AE(i)}willUpdate(e){}_$AE(e){var t;null===(t=this._$ES)||void 0===t||t.forEach((e=>{var t;return null===(t=e.hostUpdated)||void 0===t?void 0:t.call(e)})),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$Ek(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$E_}shouldUpdate(e){return!0}update(e){void 0!==this._$EC&&(this._$EC.forEach(((e,t)=>this._$EO(t,this[t],e))),this._$EC=void 0),this._$Ek()}updated(e){}firstUpdated(e){}}pe[he]=!0,pe.elementProperties=new Map,pe.elementStyles=[],pe.shadowRootOptions={mode:"open"},null==de||de({ReactiveElement:pe}),(null!==(oe=re.reactiveElementVersions)&&void 0!==oe?oe:re.reactiveElementVersions=[]).push("1.6.3");
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
class ue extends s{constructor(){super(...arguments),this._checked=!1,this.useStateLayerCustomProperties=!1,this.global=!1,this.disabled=!1,this.value="on",this.name="",this.reducedTouchTarget=!1,this.mdcFoundationClass=X,this.formElementTabIndex=0,this.focused=!1,this.shouldRenderRipple=!1,this.rippleElement=null,this.rippleHandlers=new d((()=>(this.shouldRenderRipple=!0,this.ripple.then((e=>{this.rippleElement=e})),this.ripple)))}get checked(){return this._checked}set checked(e){var t,i;const o=this._checked;e!==o&&(this._checked=e,this.formElement&&(this.formElement.checked=e),null===(t=this._selectionController)||void 0===t||t.update(this),!1===e&&(null===(i=this.formElement)||void 0===i||i.blur()),this.requestUpdate("checked",o),this.dispatchEvent(new Event("checked",{bubbles:!0,composed:!0})))}_handleUpdatedValue(e){this.formElement.value=e}renderRipple(){return this.shouldRenderRipple?l`<mwc-ripple unbounded accent
        .internalUseStateLayerCustomProperties="${this.useStateLayerCustomProperties}"
        .disabled="${this.disabled}"></mwc-ripple>`:""}get isRippleActive(){var e;return(null===(e=this.rippleElement)||void 0===e?void 0:e.isActive)||!1}connectedCallback(){super.connectedCallback(),this._selectionController=Q.getController(this),this._selectionController.register(this),this._selectionController.update(this)}disconnectedCallback(){this._selectionController.unregister(this),this._selectionController=void 0}focus(){this.formElement.focus()}createAdapter(){return Object.assign(Object.assign({},n(this.mdcRoot)),{setNativeControlDisabled:e=>{this.formElement.disabled=e}})}handleFocus(){this.focused=!0,this.handleRippleFocus()}handleClick(){this.formElement.focus()}handleBlur(){this.focused=!1,this.formElement.blur(),this.rippleHandlers.endFocus()}setFormData(e){this.name&&this.checked&&e.append(this.name,this.value)}render(){const e={"mdc-radio--touch":!this.reducedTouchTarget,"mdc-ripple-upgraded--background-focused":this.focused,"mdc-radio--disabled":this.disabled};return l`
      <div class="mdc-radio ${c(e)}">
        <input
          tabindex="${this.formElementTabIndex}"
          class="mdc-radio__native-control"
          type="radio"
          name="${this.name}"
          aria-label="${h(this.ariaLabel)}"
          aria-labelledby="${h(this.ariaLabelledBy)}"
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
      </div>`}handleRippleMouseDown(e){const t=()=>{window.removeEventListener("mouseup",t),this.handleRippleDeactivate()};window.addEventListener("mouseup",t),this.rippleHandlers.startPress(e)}handleRippleTouchStart(e){this.rippleHandlers.startPress(e)}handleRippleDeactivate(){this.rippleHandlers.endPress()}handleRippleMouseEnter(){this.rippleHandlers.startHover()}handleRippleMouseLeave(){this.rippleHandlers.endHover()}handleRippleFocus(){this.rippleHandlers.startFocus()}changeHandler(){this.checked=this.formElement.checked}}o([B(".mdc-radio")],ue.prototype,"mdcRoot",void 0),o([B("input")],ue.prototype,"formElement",void 0),o([U()],ue.prototype,"useStateLayerCustomProperties",void 0),o([M({type:Boolean})],ue.prototype,"global",void 0),o([M({type:Boolean,reflect:!0})],ue.prototype,"checked",null),o([M({type:Boolean}),r((function(e){this.mdcFoundation.setDisabled(e)}))],ue.prototype,"disabled",void 0),o([M({type:String}),r((function(e){this._handleUpdatedValue(e)}))],ue.prototype,"value",void 0),o([M({type:String})],ue.prototype,"name",void 0),o([M({type:Boolean})],ue.prototype,"reducedTouchTarget",void 0),o([M({type:Number})],ue.prototype,"formElementTabIndex",void 0),o([U()],ue.prototype,"focused",void 0),o([U()],ue.prototype,"shouldRenderRipple",void 0),o([function(e){return j({descriptor:t=>({async get(){var t;return await this.updateComplete,null===(t=this.renderRoot)||void 0===t?void 0:t.querySelector(e)},enumerable:!0,configurable:!0})})}("mwc-ripple")],ue.prototype,"ripple",void 0),o([a,M({attribute:"aria-label"})],ue.prototype,"ariaLabel",void 0),o([a,M({attribute:"aria-labelledby"})],ue.prototype,"ariaLabelledBy",void 0),o([function(e){return j({finisher:(t,i)=>{Object.assign(t.prototype[i],e)}})}({passive:!0})],ue.prototype,"handleRippleTouchStart",null);
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-LIcense-Identifier: Apache-2.0
 */
const me=p`.mdc-touch-target-wrapper{display:inline}.mdc-radio{padding:calc((40px - 20px) / 2)}.mdc-radio .mdc-radio__native-control:enabled:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle{border-color:rgba(0, 0, 0, 0.54)}.mdc-radio .mdc-radio__native-control:enabled:checked+.mdc-radio__background .mdc-radio__outer-circle{border-color:#018786;border-color:var(--mdc-theme-secondary, #018786)}.mdc-radio .mdc-radio__native-control:enabled+.mdc-radio__background .mdc-radio__inner-circle{border-color:#018786;border-color:var(--mdc-theme-secondary, #018786)}.mdc-radio [aria-disabled=true] .mdc-radio__native-control:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio .mdc-radio__native-control:disabled:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle{border-color:rgba(0, 0, 0, 0.38)}.mdc-radio [aria-disabled=true] .mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio .mdc-radio__native-control:disabled:checked+.mdc-radio__background .mdc-radio__outer-circle{border-color:rgba(0, 0, 0, 0.38)}.mdc-radio [aria-disabled=true] .mdc-radio__native-control+.mdc-radio__background .mdc-radio__inner-circle,.mdc-radio .mdc-radio__native-control:disabled+.mdc-radio__background .mdc-radio__inner-circle{border-color:rgba(0, 0, 0, 0.38)}.mdc-radio .mdc-radio__background::before{background-color:#018786;background-color:var(--mdc-theme-secondary, #018786)}.mdc-radio .mdc-radio__background::before{top:calc(-1 * (40px - 20px) / 2);left:calc(-1 * (40px - 20px) / 2);width:40px;height:40px}.mdc-radio .mdc-radio__native-control{top:calc((40px - 40px) / 2);right:calc((40px - 40px) / 2);left:calc((40px - 40px) / 2);width:40px;height:40px}@media screen and (forced-colors: active),(-ms-high-contrast: active){.mdc-radio.mdc-radio--disabled [aria-disabled=true] .mdc-radio__native-control:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio.mdc-radio--disabled .mdc-radio__native-control:disabled:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle{border-color:GrayText}.mdc-radio.mdc-radio--disabled [aria-disabled=true] .mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio.mdc-radio--disabled .mdc-radio__native-control:disabled:checked+.mdc-radio__background .mdc-radio__outer-circle{border-color:GrayText}.mdc-radio.mdc-radio--disabled [aria-disabled=true] .mdc-radio__native-control+.mdc-radio__background .mdc-radio__inner-circle,.mdc-radio.mdc-radio--disabled .mdc-radio__native-control:disabled+.mdc-radio__background .mdc-radio__inner-circle{border-color:GrayText}}.mdc-radio{display:inline-block;position:relative;flex:0 0 auto;box-sizing:content-box;width:20px;height:20px;cursor:pointer;will-change:opacity,transform,border-color,color}.mdc-radio__background{display:inline-block;position:relative;box-sizing:border-box;width:20px;height:20px}.mdc-radio__background::before{position:absolute;transform:scale(0, 0);border-radius:50%;opacity:0;pointer-events:none;content:"";transition:opacity 120ms 0ms cubic-bezier(0.4, 0, 0.6, 1),transform 120ms 0ms cubic-bezier(0.4, 0, 0.6, 1)}.mdc-radio__outer-circle{position:absolute;top:0;left:0;box-sizing:border-box;width:100%;height:100%;border-width:2px;border-style:solid;border-radius:50%;transition:border-color 120ms 0ms cubic-bezier(0.4, 0, 0.6, 1)}.mdc-radio__inner-circle{position:absolute;top:0;left:0;box-sizing:border-box;width:100%;height:100%;transform:scale(0, 0);border-width:10px;border-style:solid;border-radius:50%;transition:transform 120ms 0ms cubic-bezier(0.4, 0, 0.6, 1),border-color 120ms 0ms cubic-bezier(0.4, 0, 0.6, 1)}.mdc-radio__native-control{position:absolute;margin:0;padding:0;opacity:0;cursor:inherit;z-index:1}.mdc-radio--touch{margin-top:4px;margin-bottom:4px;margin-right:4px;margin-left:4px}.mdc-radio--touch .mdc-radio__native-control{top:calc((40px - 48px) / 2);right:calc((40px - 48px) / 2);left:calc((40px - 48px) / 2);width:48px;height:48px}.mdc-radio.mdc-ripple-upgraded--background-focused .mdc-radio__focus-ring,.mdc-radio:not(.mdc-ripple-upgraded):focus .mdc-radio__focus-ring{pointer-events:none;border:2px solid transparent;border-radius:6px;box-sizing:content-box;position:absolute;top:50%;left:50%;transform:translate(-50%, -50%);height:100%;width:100%}@media screen and (forced-colors: active){.mdc-radio.mdc-ripple-upgraded--background-focused .mdc-radio__focus-ring,.mdc-radio:not(.mdc-ripple-upgraded):focus .mdc-radio__focus-ring{border-color:CanvasText}}.mdc-radio.mdc-ripple-upgraded--background-focused .mdc-radio__focus-ring::after,.mdc-radio:not(.mdc-ripple-upgraded):focus .mdc-radio__focus-ring::after{content:"";border:2px solid transparent;border-radius:8px;display:block;position:absolute;top:50%;left:50%;transform:translate(-50%, -50%);height:calc(100% + 4px);width:calc(100% + 4px)}@media screen and (forced-colors: active){.mdc-radio.mdc-ripple-upgraded--background-focused .mdc-radio__focus-ring::after,.mdc-radio:not(.mdc-ripple-upgraded):focus .mdc-radio__focus-ring::after{border-color:CanvasText}}.mdc-radio__native-control:checked+.mdc-radio__background,.mdc-radio__native-control:disabled+.mdc-radio__background{transition:opacity 120ms 0ms cubic-bezier(0, 0, 0.2, 1),transform 120ms 0ms cubic-bezier(0, 0, 0.2, 1)}.mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio__native-control:disabled+.mdc-radio__background .mdc-radio__outer-circle{transition:border-color 120ms 0ms cubic-bezier(0, 0, 0.2, 1)}.mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__inner-circle,.mdc-radio__native-control:disabled+.mdc-radio__background .mdc-radio__inner-circle{transition:transform 120ms 0ms cubic-bezier(0, 0, 0.2, 1),border-color 120ms 0ms cubic-bezier(0, 0, 0.2, 1)}.mdc-radio--disabled{cursor:default;pointer-events:none}.mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__inner-circle{transform:scale(0.5);transition:transform 120ms 0ms cubic-bezier(0, 0, 0.2, 1),border-color 120ms 0ms cubic-bezier(0, 0, 0.2, 1)}.mdc-radio__native-control:disabled+.mdc-radio__background,[aria-disabled=true] .mdc-radio__native-control+.mdc-radio__background{cursor:default}.mdc-radio__native-control:focus+.mdc-radio__background::before{transform:scale(1);opacity:.12;transition:opacity 120ms 0ms cubic-bezier(0, 0, 0.2, 1),transform 120ms 0ms cubic-bezier(0, 0, 0.2, 1)}:host{display:inline-block;outline:none}.mdc-radio{vertical-align:bottom}.mdc-radio .mdc-radio__native-control:enabled:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle{border-color:var(--mdc-radio-unchecked-color, rgba(0, 0, 0, 0.54))}.mdc-radio [aria-disabled=true] .mdc-radio__native-control:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio .mdc-radio__native-control:disabled:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle{border-color:var(--mdc-radio-disabled-color, rgba(0, 0, 0, 0.38))}.mdc-radio [aria-disabled=true] .mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio .mdc-radio__native-control:disabled:checked+.mdc-radio__background .mdc-radio__outer-circle{border-color:var(--mdc-radio-disabled-color, rgba(0, 0, 0, 0.38))}.mdc-radio [aria-disabled=true] .mdc-radio__native-control+.mdc-radio__background .mdc-radio__inner-circle,.mdc-radio .mdc-radio__native-control:disabled+.mdc-radio__background .mdc-radio__inner-circle{border-color:var(--mdc-radio-disabled-color, rgba(0, 0, 0, 0.38))}`
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */;let ge=class extends ue{};ge.styles=[me],ge=o([(e=>t=>"function"==typeof t?((e,t)=>(customElements.define(e,t),t))(e,t):((e,t)=>{const{kind:i,elements:o}=t;return{kind:i,elements:o,finisher(t){customElements.define(e,t)}}})(e,t))("mwc-radio")],ge),u("vaadin-progress-bar",m`
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
  `,{moduleId:"lumo-progress-bar"});const fe=document.createElement("template");fe.innerHTML="\n  <style>\n    @keyframes vaadin-progress-pulse3 {\n      0% { opacity: 1; }\n      10% { opacity: 0; }\n      40% { opacity: 0; }\n      50% { opacity: 1; }\n      50.1% { opacity: 1; }\n      60% { opacity: 0; }\n      90% { opacity: 0; }\n      100% { opacity: 1; }\n    }\n  </style>\n",document.head.appendChild(fe.content);
/**
 * @license
 * Copyright (c) 2017 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const ve=m`
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
 * Copyright (c) 2017 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,be=e=>class extends e{static get properties(){return{value:{type:Number,observer:"_valueChanged"},min:{type:Number,value:0,observer:"_minChanged"},max:{type:Number,value:1,observer:"_maxChanged"},indeterminate:{type:Boolean,value:!1,reflectToAttribute:!0}}}static get observers(){return["_normalizedValueChanged(value, min, max)"]}ready(){super.ready(),this.setAttribute("role","progressbar")}_normalizedValueChanged(e,t,i){const o=this._normalizeValue(e,t,i);this.style.setProperty("--vaadin-progress-value",o)}_valueChanged(e){this.setAttribute("aria-valuenow",e)}_minChanged(e){this.setAttribute("aria-valuemin",e)}_maxChanged(e){this.setAttribute("aria-valuemax",e)}_normalizeValue(e,t,i){let o;return e||0===e?t>=i?o=1:(o=(e-t)/(i-t),o=Math.min(Math.max(o,0),1)):o=0,o}}
/**
 * @license
 * Copyright (c) 2017 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;u("vaadin-progress-bar",ve,{moduleId:"vaadin-progress-bar-styles"});class ye extends(f(v(be(y)))){static get is(){return"vaadin-progress-bar"}static get template(){return b`
      <div part="bar">
        <div part="value"></div>
      </div>
    `}}g(ye);let _e=class extends k{constructor(){super(),this.storageType="general",this.folders=[],this.folderInfo=Object(),this.is_admin=!1,this.enableStorageProxy=!1,this.enableInferenceWorkload=!1,this.enableVfolderTrashBin=!1,this.authenticated=!1,this.renameFolderName="",this.renameFolderID="",this.deleteFolderName="",this.deleteFolderID="",this.leaveFolderName="",this.existingFile="",this.invitees=[],this.selectedFolder="",this.selectedFolderType="",this.indicator=Object(),this.notification=Object(),this.listCondition="loading",this.allowed_folder_type=[],this._boundIndexRenderer=Object(),this._boundTypeRenderer=Object(),this._boundFolderListRenderer=Object(),this._boundControlFolderListRenderer=Object(),this._boundTrashBinControlFolderListRenderer=Object(),this._boundPermissionViewRenderer=Object(),this._boundOwnerRenderer=Object(),this._boundPermissionRenderer=Object(),this._boundCloneableRenderer=Object(),this._boundQuotaRenderer=Object(),this._boundInviteeInfoRenderer=Object(),this._boundIDRenderer=Object(),this._boundStatusRenderer=Object(),this._folderRefreshing=!1,this.lastQueryTime=0,this.permissions={rw:"Read-Write",ro:"Read-Only",wd:"Delete"},this.volumeInfo=Object(),this.quotaSupportStorageBackends=["xfs","weka","spectrumscale","netapp","vast","cephfs","ddn"],this.quotaUnit={MB:Math.pow(10,6),GB:Math.pow(10,9),TB:Math.pow(10,12),PB:Math.pow(10,15),MiB:Math.pow(2,20),GiB:Math.pow(2,30),TiB:Math.pow(2,40),PiB:Math.pow(2,50)},this.maxSize={value:0,unit:"MB"},this.quota={value:0,unit:"MB"},this.directoryBasedUsage=!1,this._unionedAllowedPermissionByVolume=Object(),this._boundIndexRenderer=this.indexRenderer.bind(this),this._boundTypeRenderer=this.typeRenderer.bind(this),this._boundControlFolderListRenderer=this.controlFolderListRenderer.bind(this),this._boundTrashBinControlFolderListRenderer=this.trashBinControlFolderListRenderer.bind(this),this._boundPermissionViewRenderer=this.permissionViewRenderer.bind(this),this._boundCloneableRenderer=this.CloneableRenderer.bind(this),this._boundOwnerRenderer=this.OwnerRenderer.bind(this),this._boundPermissionRenderer=this.permissionRenderer.bind(this),this._boundFolderListRenderer=this.folderListRenderer.bind(this),this._boundQuotaRenderer=this.quotaRenderer.bind(this),this._boundInviteeInfoRenderer=this.inviteeInfoRenderer.bind(this),this._boundIDRenderer=this.iDRenderer.bind(this),this._boundStatusRenderer=this.statusRenderer.bind(this)}static get styles(){return[F,S,T,I,m`
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

        vaadin-text-field {
          --vaadin-text-field-default-width: auto;
        }

        vaadin-grid-cell-content {
          overflow: visible;
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

        @media screen and (max-width: 750px) {
          mwc-button {
            width: auto;
          }
          mwc-button > span {
            display: none;
          }
        }
      `]}_updateQuotaInputHumanReadableValue(){let e="MB";const t=Number(this.modifyFolderQuotaInput.value)*this.quotaUnit[this.modifyFolderQuotaUnitSelect.value],i=this.maxSize.value*this.quotaUnit[this.maxSize.unit];[this.modifyFolderQuotaInput.value,e]=globalThis.backendaiutils._humanReadableFileSize(t).split(" "),["Bytes","KB","MB"].includes(e)?(this.modifyFolderQuotaInput.value="MB"===e?Number(this.modifyFolderQuotaInput.value)<1?"1":Math.round(Number(this.modifyFolderQuotaInput.value)).toString():"1",e="MB"):(this.modifyFolderQuotaInput.value=parseFloat(this.modifyFolderQuotaInput.value).toFixed(1),i<t&&(this.modifyFolderQuotaInput.value=this.maxSize.value.toString(),e=this.maxSize.unit)),this.modifyFolderQuotaInput.step="MB"===this.modifyFolderQuotaUnitSelect.value?0:.1;const o=this.modifyFolderQuotaUnitSelect.items.findIndex((t=>t.value===e));this.modifyFolderQuotaUnitSelect.select(o)}render(){return R`
      <lablup-loading-spinner id="loading-spinner"></lablup-loading-spinner>
      <backend-ai-session-launcher
        mode="inference"
        location="data"
        hideLaunchButton
        id="session-launcher"
        ?active="${!0===this.active}"
        .newSessionDialogTitle="${C("session.launcher.StartModelServing")}"
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
            header="${C("data.folders.Name")}"
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
            header="${C("data.folders.Location")}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="status"
            width="80px"
            flex-grow="0"
            resizable
            .renderer="${this._boundStatusRenderer}"
            header="${C("data.folders.Status")}"
          ></lablup-grid-sort-filter-column>
          ${this.directoryBasedUsage?R`
                <vaadin-grid-sort-column
                  id="folder-quota-column"
                  path="max_size"
                  width="95px"
                  flex-grow="0"
                  resizable
                  header="${C("data.folders.FolderQuota")}"
                  .renderer="${this._boundQuotaRenderer}"
                ></vaadin-grid-sort-column>
              `:R``}
          <lablup-grid-sort-filter-column
            path="ownership_type"
            width="70px"
            flex-grow="0"
            resizable
            header="${C("data.folders.Type")}"
            .renderer="${this._boundTypeRenderer}"
          ></lablup-grid-sort-filter-column>
          <vaadin-grid-column
            width="95px"
            flex-grow="0"
            resizable
            header="${C("data.folders.Permission")}"
            .renderer="${this._boundPermissionViewRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            auto-width
            flex-grow="0"
            resizable
            header="${C("data.folders.Owner")}"
            .renderer="${this._boundOwnerRenderer}"
          ></vaadin-grid-column>
          ${this.enableStorageProxy&&"model"===this.storageType&&this.is_admin?R`
                <vaadin-grid-column
                  auto-width
                  flex-grow="0"
                  resizable
                  header="${C("data.folders.Cloneable")}"
                  .renderer="${this._boundCloneableRenderer}"
                ></vaadin-grid-column>
              `:R``}
          ${"deadVFolderStatus"!==this.storageType?R`
                <vaadin-grid-column
                  auto-width
                  resizable
                  header="${C("data.folders.Control")}"
                  .renderer="${this._boundControlFolderListRenderer}"
                ></vaadin-grid-column>
              `:R`
                <vaadin-grid-column
                  auto-width
                  resizable
                  header="${C("data.folders.Control")}"
                  .renderer="${this._boundTrashBinControlFolderListRenderer}"
                ></vaadin-grid-column>
              `}
        </vaadin-grid>
        <backend-ai-list-status
          id="list-status"
          statusCondition="${this.listCondition}"
          message="${D("data.folders.NoFolderToDisplay")}"
        ></backend-ai-list-status>
      </div>
      <backend-ai-dialog id="modify-folder-dialog" fixed backdrop>
        <span slot="title">${C("data.folders.FolderOptionUpdate")}</span>
        <div slot="content" class="vertical layout flex">
          <div
            class="vertical layout"
            id="modify-quota-controls"
            style="display:${this.directoryBasedUsage&&this._checkFolderSupportDirectoryBasedUsage(this.folderInfo.host)?"flex":"none"}"
          >
            <div class="horizontal layout center justified">
              <mwc-textfield
                id="modify-folder-quota"
                label="${C("data.folders.FolderQuota")}"
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
                ${Object.keys(this.quotaUnit).map(((e,t)=>R`
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
              ${C("data.folders.MaxFolderQuota")} :
              ${this.maxSize.value+" "+this.maxSize.unit}
            </span>
          </div>
          <mwc-select
            class="full-width fixed-position"
            id="update-folder-permission"
            style="width:100%;"
            label="${C("data.Permission")}"
            fixedMenuPosition
          >
            ${Object.keys(this.permissions).map((e=>R`
                <mwc-list-item value="${this.permissions[e]}">
                  ${this.permissions[e]}
                </mwc-list-item>
              `))}
          </mwc-select>
          ${this.enableStorageProxy&&"model"===this.storageType&&this.is_admin?R`
                <div
                  id="update-folder-cloneable-container"
                  class="horizontal layout flex wrap center justified"
                >
                  <p style="color:rgba(0, 0, 0, 0.6);margin-left:10px;">
                    ${C("data.folders.Cloneable")}
                  </p>
                  <mwc-switch
                    id="update-folder-cloneable"
                    style="margin-right:10px;"
                  ></mwc-switch>
                </div>
              `:R``}
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
            ${C("data.Update")}
          </mwc-button>
        </div>
      </backend-ai-dialog>

      <backend-ai-dialog id="modify-folder-name-dialog" fixed backdrop>
        <span slot="title">${C("data.explorer.RenameAFolder")}</span>
        <div slot="content" class="vertical layout flex">
          <mwc-textfield
            id="clone-folder-src"
            label="${C("data.ExistingFolderName")}"
            value="${this.renameFolderName}"
            disabled
          ></mwc-textfield>
          <mwc-textfield
            class="red"
            id="new-folder-name"
            label="${C("data.folders.TypeNewFolderName")}"
            pattern="^[a-zA-Z0-9._-]*$"
            autoValidate
            validationMessage="${C("data.AllowsLettersNumbersAnd-_Dot")}"
            maxLength="64"
            placeholder="${D("maxLength.64chars")}"
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
            ${C("data.Update")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="delete-folder-without-confirm-dialog">
        <span slot="title">${C("data.folders.MoveToTrash")}</span>
        <div slot="content">
          <div>
            ${C("data.folders.MoveToTrashDescription",{folderName:this.deleteFolderName||""})}
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
            ${C("data.folders.MoveToTrash")}
          </mwc-button>
        </div>
      </backend-ai-dialog>

      <backend-ai-dialog id="delete-folder-dialog" fixed backdrop>
        <span slot="title">${C("data.folders.DeleteAFolder")}</span>
        <div slot="content">
          <div class="warning" style="margin-left:16px;">
            ${C("dialog.warning.CannotBeUndone")}
          </div>
          <mwc-textfield
            class="red"
            id="delete-folder-name"
            label="${C("data.folders.TypeFolderNameToDelete")}"
            maxLength="64"
            placeholder="${D("maxLength.64chars")}"
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
            ${C("data.folders.Delete")}
          </mwc-button>
        </div>
      </backend-ai-dialog>

      <backend-ai-dialog id="leave-folder-dialog" fixed backdrop>
        <span slot="title">${C("data.folders.LeaveAFolder")}</span>
        <div slot="content">
          <div class="warning" style="margin-left:16px;">
            ${C("dialog.warning.CannotBeUndone")}
          </div>
          <mwc-textfield
            class="red"
            id="leave-folder-name"
            label="${C("data.folders.TypeFolderNameToLeave")}"
            maxLength="64"
            placeholder="${D("maxLength.64chars")}"
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
            ${C("data.folders.Leave")}
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
              <span>${C("data.folders.Location")}</span>
            </div>
            ${this.directoryBasedUsage?R`
                  <div class="vertical layout center info-indicator">
                    <div class="big indicator">
                      ${this.folderInfo.numFiles<0?"many":this.folderInfo.numFiles}
                    </div>
                    <span>${C("data.folders.NumberOfFiles")}</span>
                  </div>
                `:R``}
          </div>
          <mwc-list>
            <mwc-list-item twoline>
              <span><strong>ID</strong></span>
              <span class="monospace" slot="secondary">
                ${this.folderInfo.id}
              </span>
            </mwc-list-item>
            ${this.folderInfo.is_owner?R`
                  <mwc-list-item twoline>
                    <span>
                      <strong>${C("data.folders.Ownership")}</strong>
                    </span>
                    <span slot="secondary">
                      ${C("data.folders.DescYouAreFolderOwner")}
                    </span>
                  </mwc-list-item>
                `:R``}
            ${"undefined"!==this.folderInfo.usage_mode?R`
                  <mwc-list-item twoline>
                    <span><strong>${C("data.UsageMode")}</strong></span>
                    <span slot="secondary">${this.folderInfo.usage_mode}</span>
                  </mwc-list-item>
                `:R``}
            ${this.folderInfo.permission?R`
                  <mwc-list-item twoline>
                    <span>
                      <strong>${C("data.folders.Permission")}</strong>
                    </span>
                    <div slot="secondary" class="horizontal layout">
                      ${this._hasPermission(this.folderInfo,"r")?R`
                            <lablup-shields
                              app=""
                              color="green"
                              description="R"
                              ui="flat"
                            ></lablup-shields>
                          `:R``}
                      ${this._hasPermission(this.folderInfo,"w")?R`
                            <lablup-shields
                              app=""
                              color="blue"
                              description="W"
                              ui="flat"
                            ></lablup-shields>
                          `:R``}
                      ${this._hasPermission(this.folderInfo,"d")?R`
                            <lablup-shields
                              app=""
                              color="red"
                              description="D"
                              ui="flat"
                            ></lablup-shields>
                          `:R``}
                    </div>
                  </mwc-list-item>
                `:R``}
            ${this.enableStorageProxy?R`
                  <mwc-list-item twoline>
                    <span>
                      <strong>${C("data.folders.Cloneable")}</strong>
                    </span>
                    <span class="monospace" slot="secondary">
                      ${this.folderInfo.cloneable?R`
                            <mwc-icon class="cloneable" style="color:green;">
                              check_circle
                            </mwc-icon>
                          `:R`
                            <mwc-icon class="cloneable" style="color:red;">
                              block
                            </mwc-icon>
                          `}
                    </span>
                  </mwc-list-item>
                `:R``}
            ${this.directoryBasedUsage&&this._checkFolderSupportDirectoryBasedUsage(this.folderInfo.host)?R`
                  <mwc-list-item twoline>
                    <span>
                      <strong>${C("data.folders.FolderUsage")}</strong>
                    </span>
                    <span class="monospace" slot="secondary">
                      ${C("data.folders.FolderUsing")}:
                      ${this.folderInfo.used_bytes>=0?globalThis.backendaiutils._humanReadableFileSize(this.folderInfo.used_bytes):"Undefined"}
                      / ${C("data.folders.FolderQuota")}:
                      ${this.folderInfo.max_size>=0?globalThis.backendaiutils._humanReadableFileSize(this.folderInfo.max_size*this.quotaUnit.MiB):"Undefined"}
                      ${this.folderInfo.used_bytes>=0&&this.folderInfo.max_size>=0?R`
                            <vaadin-progress-bar
                              value="${this.folderInfo.used_bytes/this.folderInfo.max_size/2**20}"
                            ></vaadin-progress-bar>
                          `:R``}
                    </span>
                  </mwc-list-item>
                `:R`
                  <mwc-list-item twoline>
                    <span>
                      <strong>${C("data.folders.FolderUsage")}</strong>
                    </span>
                    <span class="monospace" slot="secondary">
                      ${C("data.folders.FolderUsing")}:
                      ${this.folderInfo.used_bytes>=0?globalThis.backendaiutils._humanReadableFileSize(this.folderInfo.used_bytes):"Undefined"}
                    </span>
                  </mwc-list-item>
                `}
          </mwc-list>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="share-folder-dialog" fixed backdrop>
        <span slot="title">${C("data.explorer.ShareFolder")}</span>
        <div slot="content" role="listbox" style="margin: 0;width:100%;">
          <div style="margin: 10px 0px">${C("data.explorer.People")}</div>
          <div class="vertical layout flex" id="textfields">
            <div class="horizontal layout">
              <div style="flex-grow: 2">
                <mwc-textfield
                  class="share-email"
                  type="email"
                  id="first-email"
                  label="${C("data.explorer.EnterEmailAddress")}"
                  maxLength="64"
                  placeholder="${D("maxLength.64chars")}"
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
          <div style="margin: 10px 0px">${C("data.explorer.Permissions")}</div>
          <div style="display: flex; justify-content: space-evenly;">
            <mwc-formfield label="${C("data.folders.View")}">
              <mwc-radio
                name="share-folder-permission"
                checked
                value="ro"
              ></mwc-radio>
            </mwc-formfield>
            <mwc-formfield label="${C("data.folders.Edit")}">
              <mwc-radio name="share-folder-permission" value="rw"></mwc-radio>
            </mwc-formfield>
            <mwc-formfield label="${C("data.folders.EditDelete")}">
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
            ${C("button.Share")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="delete-from-trash-bin-dialog" fixed backdrop>
        <span slot="title">${C("dialog.title.DeleteForever")}</span>
        <div slot="content">
          <div class="warning">${C("dialog.warning.DeleteForeverDesc")}</div>
          <mwc-textfield
            class="red"
            id="delete-from-trash-bin-name-input"
            label="${C("data.folders.TypeFolderNameToDelete")}"
            maxLength="64"
            placeholder="${D("maxLength.64chars")}"
          ></mwc-textfield>
        </div>
        <div
          slot="footer"
          class="horizontal end-justified flex layout"
          style="gap:5px;"
        >
          <mwc-button outlined @click="${e=>this._hideDialog(e)}">
            ${C("button.Cancel")}
          </mwc-button>
          <mwc-button
            raised
            class="warning fg red"
            @click="${()=>this._deleteFromTrashBin()}"
          >
            ${C("data.folders.DeleteForever")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
    `}firstUpdated(){var e,t,i;this.indicator=globalThis.lablupIndicator,this.notification=globalThis.lablupNotification;const o=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll("mwc-textfield");for(const e of Array.from(o))this._addInputValidator(e);["data","automount","model"].includes(this.storageType)?(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("vaadin-grid.folderlist")).style.height="calc(100vh - 464px)":(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("vaadin-grid.folderlist")).style.height="calc(100vh - 420px)",document.addEventListener("backend-ai-group-changed",(e=>this._refreshFolderList(!0,"group-changed")))}_isUncontrollableStatus(e){return["performing","cloning","mounted","error","delete-pending","delete-ongoing","deleted-complete","delete-error","purge-ongoing","deleting"].includes(e)}_isDeadVFolderStatus(e){return["delete-pending","delete-ongoing","delete-complete","delete-error","deleting"].includes(e)}_moveTo(e=""){const t=""!==e?e:"summary";N.dispatch(E(decodeURIComponent(t),{})),document.dispatchEvent(new CustomEvent("react-navigate",{detail:e}))}permissionRenderer(e,t,i){P(R`
        <mwc-select label="${C("data.folders.SelectPermission")}">
          <mwc-list-item value="ro" ?selected="${"ro"===i.item.perm}">
            ${C("data.folders.View")}
          </mwc-list-item>
          <mwc-list-item value="rw" ?selected="${"rw"===i.item.perm}">
            ${C("data.folders.Edit")}
          </mwc-list-item>
          <mwc-list-item value="wd" ?selected="${"wd"===i.item.perm}">
            ${C("data.folders.EditDelete")}
          </mwc-list-item>
          <mwc-list-item value="kickout">
            ${C("data.folders.KickOut")}
          </mwc-list-item>
        </mwc-select>
      `,e)}folderListRenderer(e,t,i){P(R`
        <div
          class="controls layout flex horizontal start-justified center wrap"
          folder-id="${i.item.id}"
          folder-name="${i.item.name}"
          folder-type="${i.item.type}"
        >
          ${this._hasPermission(i.item,"r")?R`
                <mwc-icon-button
                  class="fg blue controls-running"
                  icon="folder_open"
                  title=${C("data.folders.OpenAFolder")}
                  @click="${()=>{this.triggerOpenFilebrowserToReact(i)}}"
                  ?disabled="${this._isUncontrollableStatus(i.item.status)}"
                  .folder-id="${i.item.name}"
                ></mwc-icon-button>
              `:R``}
          <div
            @click="${e=>!this._isUncontrollableStatus(i.item.status)&&this.triggerOpenFilebrowserToReact(i)}"
            .folder-id="${i.item.name}"
            style="cursor:${this._isUncontrollableStatus(i.item.status)?"default":"pointer"};"
          >
            ${i.item.name}
          </div>
        </div>
      `,e)}quotaRenderer(e,t,i){let o="-";this._checkFolderSupportDirectoryBasedUsage(i.item.host)&&i.item.max_size&&(o=globalThis.backendaiutils._humanReadableFileSize(i.item.max_size*this.quotaUnit.MiB)),P(R`
        <div class="horizontal layout center center-justified">
          ${o}
        </div>
      `,e)}inviteeInfoRenderer(e,t,i){P(R`
        <div>${i.item.shared_to.email}</div>
      `,e)}iDRenderer(e,t,i){P(R`
        <div class="layout vertical">
          <span class="indicator monospace">${i.item.id}</span>
        </div>
      `,e)}statusRenderer(e,t,i){let o;switch(i.item.status){case"ready":o="green";break;case"performing":case"cloning":case"mounted":o="blue";break;case"delete-ongoing":o="yellow";break;default:o="grey"}P(R`
        <lablup-shields
          app=""
          color="${o}"
          description="${i.item.status}"
          ui="flat"
        ></lablup-shields>
      `,e)}_addTextField(){var e,t;const i=document.createElement("mwc-textfield");i.label=D("data.explorer.EnterEmailAddress"),i.type="email",i.className="share-email",i.style.width="auto",i.style.marginRight="83px",null===(t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#textfields"))||void 0===t||t.appendChild(i)}_removeTextField(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#textfields");t.children.length>1&&t.lastChild&&t.removeChild(t.lastChild)}indexRenderer(e,t,i){P(R`
        ${this._indexFrom1(i.index)}
      `,e)}controlFolderListRenderer(e,t,i){var o;const r=(null!==(o=this._unionedAllowedPermissionByVolume[i.item.host])&&void 0!==o?o:[]).includes("invite-others")&&!i.item.name.startsWith(".");P(R`
        <div
          class="controls layout flex center wrap"
          folder-id="${i.item.id}"
          folder-name="${i.item.name}"
          folder-type="${i.item.type}"
        >
          ${this.enableInferenceWorkload&&"model"==i.item.usage_mode?R`
                <mwc-icon-button
                  class="fg green controls-running"
                  icon="play_arrow"
                  @click="${e=>this._moveTo("/service/start?model="+i.item.id)}"
                  ?disabled="${this._isUncontrollableStatus(i.item.status)}"
                  id="${i.item.id+"-serve"}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.item.id+"-serve"}"
                  text="${C("data.folders.Serve")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:R``}
          <mwc-icon-button
            class="fg green controls-running"
            icon="info"
            @click="${e=>this._infoFolder(e)}"
            ?disabled="${this._isUncontrollableStatus(i.item.status)}"
            id="${i.item.id+"-folderinfo"}"
          ></mwc-icon-button>
          <vaadin-tooltip
            for="${i.item.id+"-folderinfo"}"
            text="${C("data.folders.FolderInfo")}"
            position="top-start"
          ></vaadin-tooltip>
          <!--${this._hasPermission(i.item,"r")&&this.enableStorageProxy?R`
                <mwc-icon-button
                  class="fg blue controls-running"
                  icon="content_copy"
                  ?disabled=${!i.item.cloneable}
                  @click="${()=>{this._requestCloneFolder(i.item)}}"
                  id="${i.item.id+"-clone"}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.item.id+"-clone"}"
                  text="${C("data.folders.CloneFolder")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:R``}-->
          ${i.item.is_owner?R`
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
                  text="${C("data.folders.ShareFolder")}"
                  position="top-start"
                ></vaadin-tooltip>
                <mwc-icon-button
                  class="fg blue controls-running"
                  icon="perm_identity"
                  @click=${e=>this._showPermissionSettingModal(i.item.id)}
                  ?disabled="${this._isUncontrollableStatus(i.item.status)}"
                  style="display: ${r?"":"none"}"
                  id="${i.item.id+"-modifypermission"}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.item.id+"-modifypermission"}"
                  text="${C("data.folders.ModifyPermissions")}"
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
                  text="${C("data.folders.Rename")}"
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
                  text="${C("data.folders.FolderOptionUpdate")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:R``}
          ${i.item.is_owner||this._hasPermission(i.item,"d")||"group"===i.item.type&&this.is_admin?R`
                <mwc-icon-button
                  class="fg ${this.enableVfolderTrashBin?"blue":"red"} controls-running"
                  icon="delete"
                  @click="${e=>this._deleteFolderDialog(e)}"
                  ?disabled="${this._isUncontrollableStatus(i.item.status)}"
                  id="${i.item.id+"-delete"}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.item.id+"-delete"}"
                  text="${C("data.folders.MoveToTrash")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:R``}
          ${i.item.is_owner||"user"!=i.item.type?R``:R`
                <mwc-icon-button
                  class="fg red controls-running"
                  icon="remove_circle"
                  @click="${e=>this._leaveInvitedFolderDialog(e)}"
                  ?disabled="${this._isUncontrollableStatus(i.item.status)}"
                  id="${i.item.id+"-leavefolder"}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.item.id+"-leavefolder"}"
                  text="${C("data.folders.LeaveFolder")}"
                  position="top-start"
                ></vaadin-tooltip>
              `}
        </div>
      `,e)}trashBinControlFolderListRenderer(e,t,i){P(R`
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
            text="${C("data.folders.FolderInfo")}"
            position="top-start"
          ></vaadin-tooltip>
          ${i.item.is_owner||this._hasPermission(i.item,"d")||"group"===i.item.type&&this.is_admin?R`
                <mwc-icon-button
                  class="fg blue controls-running"
                  icon="redo"
                  ?disabled=${"delete-pending"!==i.item.status}
                  @click="${e=>this._restoreFolder(e)}"
                  id="${i.item.id+"-restore"}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.item.id+"-restore"}"
                  text="${C("data.folders.Restore")}"
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
                  text="${C("data.folders.DeleteForever")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:R``}
        </div>
      `,e)}permissionViewRenderer(e,t,i){P(R`
        <div class="horizontal center-justified wrap layout">
          ${this._hasPermission(i.item,"r")?R`
                <lablup-shields
                  app=""
                  color="green"
                  description="R"
                  ui="flat"
                ></lablup-shields>
              `:R``}
          ${this._hasPermission(i.item,"w")?R`
                <lablup-shields
                  app=""
                  color="blue"
                  description="W"
                  ui="flat"
                ></lablup-shields>
              `:R``}
          ${this._hasPermission(i.item,"d")?R`
                <lablup-shields
                  app=""
                  color="red"
                  description="D"
                  ui="flat"
                ></lablup-shields>
              `:R``}
        </div>
      `,e)}OwnerRenderer(e,t,i){P(R`
        ${i.item.is_owner?R`
              <div
                class="horizontal center-justified center layout"
                style="pointer-events: none;"
              >
                <mwc-icon-button class="fg green" icon="done"></mwc-icon-button>
              </div>
            `:R``}
      `,e)}CloneableRenderer(e,t,i){P(R`
        ${i.item.cloneable?R`
              <div
                class="horizontal center-justified center layout"
                style="pointer-events: none;"
              >
                <mwc-icon-button class="fg green" icon="done"></mwc-icon-button>
              </div>
            `:R``}
      `,e)}typeRenderer(e,t,i){P(R`
        <div class="layout vertical center-justified">
          ${"user"==i.item.type?R`
                <mwc-icon>person</mwc-icon>
              `:R`
                <mwc-icon class="fg green">group</mwc-icon>
              `}
        </div>
      `,e)}async _getCurrentKeypairResourcePolicy(){const e=globalThis.backendaiclient._config.accessKey;return(await globalThis.backendaiclient.keypair.info(e,["resource_policy"])).keypair.resource_policy}async _getAllowedVFolderHostsByCurrentUserInfo(){var e,t;const[i,o]=await Promise.all([globalThis.backendaiclient.vfolder.list_hosts(),this._getCurrentKeypairResourcePolicy()]),r=globalThis.backendaiclient._config.domainName,a=globalThis.backendaiclient.current_group_id(),s=await globalThis.backendaiclient.storageproxy.getAllowedVFolderHostsByCurrentUserInfo(r,a,o),d=JSON.parse((null===(e=null==s?void 0:s.domain)||void 0===e?void 0:e.allowed_vfolder_hosts)||"{}"),l=JSON.parse((null===(t=null==s?void 0:s.group)||void 0===t?void 0:t.allowed_vfolder_hosts)||"{}"),n=JSON.parse((null==s?void 0:s.keypair_resource_policy.allowed_vfolder_hosts)||"{}");this._unionedAllowedPermissionByVolume=Object.assign({},...i.allowed.map((e=>{return{[e]:(t=[d[e],l[e],n[e]],[...new Set([].concat(...t))])};var t}))),this.folderListGrid.clearCache()}_checkFolderSupportDirectoryBasedUsage(e){var t;if(!e||globalThis.backendaiclient.supports("deprecated-max-quota-scope-in-keypair-resource-policy"))return!1;const i=null===(t=this.volumeInfo[e])||void 0===t?void 0:t.backend;return this.quotaSupportStorageBackends.includes(i)}async refreshFolderList(){return this._triggerFolderListChanged(),this.folderListGrid&&this.folderListGrid.clearCache(),await this._refreshFolderList(!0,"refreshFolderList")}_refreshFolderList(e=!1,t="unknown"){var i;if(this._folderRefreshing||!this.active)return;if(Date.now()-this.lastQueryTime<1e3)return;this._folderRefreshing=!0,this.lastQueryTime=Date.now(),this.listCondition="loading",null===(i=this._listStatus)||void 0===i||i.show(),this._getMaxSize();let o=null;o=globalThis.backendaiclient.current_group_id(),globalThis.backendaiclient.vfolder.list(o).then((e=>{var t;let i=e.filter((e=>(this.enableInferenceWorkload||"general"!==this.storageType||e.name.startsWith(".")||"model"!=e.usage_mode)&&("general"!==this.storageType||e.name.startsWith(".")||"general"!=e.usage_mode)&&("data"!==this.storageType||e.name.startsWith(".")||"data"!=e.usage_mode)?"automount"===this.storageType&&e.name.startsWith(".")?e:"model"!==this.storageType||e.name.startsWith(".")||"model"!=e.usage_mode?"deadVFolderStatus"===this.storageType&&this._isDeadVFolderStatus(e.status)?e:void 0:e:e));"deadVFolderStatus"!==this.storageType&&(i=i.filter((e=>!this._isDeadVFolderStatus(e.status)))),i=i.filter((e=>"delete-complete"!==e.status)),this.folders=i,this._triggerFolderListChanged(),0==this.folders.length?this.listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide(),this._folderRefreshing=!1})).catch((()=>{this._folderRefreshing=!1})),globalThis.backendaiclient.vfolder.list_hosts().then((t=>{this.active&&!e&&setTimeout((()=>{this._refreshFolderList(!1,"loop")}),3e4)}))}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(async()=>{this.is_admin=globalThis.backendaiclient.is_admin,this.enableStorageProxy=globalThis.backendaiclient.supports("storage-proxy"),this.enableInferenceWorkload=globalThis.backendaiclient.supports("inference-workload"),this.enableVfolderTrashBin=globalThis.backendaiclient.supports("vfolder-trash-bin"),this.authenticated=!0,this.directoryBasedUsage=globalThis.backendaiclient._config.directoryBasedUsage&&!globalThis.backendaiclient.supports("deprecated-max-quota-scope-in-keypair-resource-policy"),this._getAllowedVFolderHostsByCurrentUserInfo(),this._refreshFolderList(!1,"viewStatechanged")}),!0):(this.is_admin=globalThis.backendaiclient.is_admin,this.enableStorageProxy=globalThis.backendaiclient.supports("storage-proxy"),this.enableInferenceWorkload=globalThis.backendaiclient.supports("inference-workload"),this.enableVfolderTrashBin=globalThis.backendaiclient.supports("vfolder-trash-bin"),this.authenticated=!0,this.directoryBasedUsage=globalThis.backendaiclient._config.directoryBasedUsage&&!globalThis.backendaiclient.supports("deprecated-max-quota-scope-in-keypair-resource-policy"),this._getAllowedVFolderHostsByCurrentUserInfo(),this._refreshFolderList(!1,"viewStatechanged")))}openDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).show()}closeDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).hide()}_indexFrom1(e){return e+1}_hasPermission(e,t){return!!e.permission.includes(t)||!(!e.permission.includes("w")||"r"!==t)}_getControlName(e){return e.target.closest(".controls").getAttribute("folder-name")}_getControlID(e){return e.target.closest(".controls").getAttribute("folder-id")}_getControlType(e){return e.target.closest(".controls").getAttribute("folder-type")}_infoFolder(e){const t=globalThis.backendaiclient.supports("vfolder-id-based")?this._getControlID(e):this._getControlName(e);globalThis.backendaiclient.vfolder.info(t).then((e=>{this.folderInfo=e,this.openDialog("info-folder-dialog")})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=L.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_modifyFolderOptionDialog(e){globalThis.backendaiclient.vfolder.name=globalThis.backendaiclient.supports("vfolder-id-based")?this._getControlID(e):this._getControlName(e);globalThis.backendaiclient.vfolder.info(globalThis.backendaiclient.vfolder.name).then((e=>{this.folderInfo=e;const t=this.folderInfo.permission;let i=Object.keys(this.permissions).indexOf(t);i=i>0?i:0,this.updateFolderPermissionSelect.select(i),this.updateFolderCloneableSwitch&&(this.updateFolderCloneableSwitch.selected=this.folderInfo.cloneable),this.directoryBasedUsage&&this._checkFolderSupportDirectoryBasedUsage(this.folderInfo.host)&&([this.quota.value,this.quota.unit]=globalThis.backendaiutils._humanReadableFileSize(this.folderInfo.max_size*this.quotaUnit.MiB).split(" "),this.modifyFolderQuotaInput.value=this.quota.value.toString(),this.modifyFolderQuotaUnitSelect.value="Bytes"==this.quota.unit?"MB":this.quota.unit),this.openDialog("modify-folder-dialog")})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=L.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}async _updateFolder(){var e;let t=!1,i=!1;const o={};if(this.updateFolderPermissionSelect){let t=this.updateFolderPermissionSelect.value;t=null!==(e=Object.keys(this.permissions).find((e=>this.permissions[e]===t)))&&void 0!==e?e:"",t&&this.folderInfo.permission!==t&&(o.permission=t)}this.updateFolderCloneableSwitch&&(i=this.updateFolderCloneableSwitch.selected,o.cloneable=i);const r=[];if(Object.keys(o).length>0){const e=globalThis.backendaiclient.vfolder.update_folder(o,globalThis.backendaiclient.vfolder.name);r.push(e)}if(this.directoryBasedUsage&&this._checkFolderSupportDirectoryBasedUsage(this.folderInfo.host)){const e=this.modifyFolderQuotaInput.value?BigInt(Number(this.modifyFolderQuotaInput.value)*this.quotaUnit[this.modifyFolderQuotaUnitSelect.value]).toString():"0";if(this.quota.value!=Number(this.modifyFolderQuotaInput.value)||this.quota.unit!=this.modifyFolderQuotaUnitSelect.value){const t=globalThis.backendaiclient.vfolder.set_quota(this.folderInfo.host,this.folderInfo.id,e.toString());r.push(t)}}r.length>0&&await Promise.all(r).then((()=>{this.notification.text=D("data.folders.FolderUpdated"),this.notification.show(),this._refreshFolderList(!0,"updateFolder")})).catch((e=>{console.log(e),e&&e.message&&(t=!0,this.notification.text=L.relieve(e.message),this.notification.show(!0,e))})),t||this.closeDialog("modify-folder-dialog")}async _updateFolderName(){globalThis.backendaiclient.vfolder.name=this.renameFolderName,globalThis.backendaiclient.vfolder.id=this.renameFolderID;const e=this.newFolderNameInput.value;if(this.newFolderNameInput.reportValidity(),e){if(!this.newFolderNameInput.checkValidity())return;try{await globalThis.backendaiclient.vfolder.rename(e),this.notification.text=D("data.folders.FolderRenamed"),this.notification.show(),this._refreshFolderList(!0,"updateFolder"),this.closeDialog("modify-folder-name-dialog")}catch(e){this.notification.text=L.relieve(e.message),this.notification.show(!0,e)}}}_renameFolderDialog(e){this.renameFolderID=globalThis.backendaiclient.supports("vfolder-id-based")?this._getControlID(e):this._getControlName(e),this.renameFolderName=this._getControlName(e),this.newFolderNameInput.value="",this.openDialog("modify-folder-name-dialog")}_deleteFolderDialog(e){this.deleteFolderID=this._getControlID(e)||"",this.deleteFolderName=this._getControlName(e)||"",this.deleteFolderNameInput.value="",this.enableVfolderTrashBin?this.openDialog("delete-folder-without-confirm-dialog"):this.openDialog("delete-folder-dialog")}openDeleteFromTrashBinDialog(e){this.deleteFolderID=this._getControlID(e)||"",this.deleteFolderName=this._getControlName(e)||"",this.deleteFromTrashBinNameInput.value="",this.openDialog("delete-from-trash-bin-dialog")}_deleteFolderWithCheck(){if(this.deleteFolderNameInput.value!==this.deleteFolderName)return this.notification.text=D("data.folders.FolderNameMismatched"),void this.notification.show();this.closeDialog("delete-folder-dialog");const e=this.enableVfolderTrashBin?this.deleteFolderID:this.deleteFolderName;this._deleteFolder(e)}_deleteFolder(e){(this.enableVfolderTrashBin?globalThis.backendaiclient.vfolder.delete_by_id(e):globalThis.backendaiclient.vfolder.delete(e)).then((async e=>{e.msg?(this.notification.text=D("data.folders.CannotDeleteFolder"),this.notification.show(!0)):(this.notification.text=this.enableVfolderTrashBin?D("data.folders.MovedToTrashBin",{folderName:this.deleteFolderName||""}):D("data.folders.FolderDeleted",{folderName:this.deleteFolderName||""}),this.notification.show(),await this.refreshFolderList())})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=L.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_inferModel(e){const t=this._getControlName(e);this.sessionLauncher.customFolderMapping={},this.sessionLauncher.customFolderMapping[t]="mount",this.sessionLauncher._launchSessionDialog()}async _checkVfolderMounted(e=""){}_requestCloneFolder(e){}_leaveInvitedFolderDialog(e){this.leaveFolderName=this._getControlName(e),this.leaveFolderNameInput.value="",this.openDialog("leave-folder-dialog")}_leaveFolderWithCheck(){if(this.leaveFolderNameInput.value!==this.leaveFolderName)return this.notification.text=D("data.folders.FolderNameMismatched"),void this.notification.show();this.closeDialog("leave-folder-dialog"),this._leaveFolder(this.leaveFolderName)}_leaveFolder(e){globalThis.backendaiclient.vfolder.leave_invited(e).then((async e=>{this.notification.text=D("data.folders.FolderDisconnected"),this.notification.show(),await this.refreshFolderList()})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=L.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}async _getMaxSize(){}_triggerFolderListChanged(){const e=new CustomEvent("backend-ai-folder-list-changed");document.dispatchEvent(e)}_validateFolderName(e=!1){var t;const i=e?this.newFolderNameInput:null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#add-folder-name");i.validityTransform=(t,o)=>{if(o.valid){let t;const o=/[`~!@#$%^&*()|+=?;:'",<>{}[\]\\/\s]/gi;if(e){if(i.value===this.renameFolderName)return i.validationMessage=D("data.EnterDifferentValue"),t=!1,{valid:t,customError:!t};t=!0}return t=!o.test(i.value),t||(i.validationMessage=D("data.AllowsLettersNumbersAnd-_Dot")),{valid:t,customError:!t}}return o.valueMissing?(i.validationMessage=D("data.FolderNameRequired"),{valid:o.valid,customError:!o.valid}):(i.validationMessage=D("data.AllowsLettersNumbersAnd-_Dot"),{valid:o.valid,customError:!o.valid})}}triggerOpenFilebrowserToReact(e){const t=new URLSearchParams(window.location.search);t.set("folder",e.item.id),document.dispatchEvent(new CustomEvent("react-navigate",{detail:{pathname:"/data",search:t.toString()}}))}_humanReadableTime(e){const t=new Date(1e3*e),i=t.getTimezoneOffset()/60,o=t.getHours();return t.setHours(o-i),t.toUTCString()}_initializeSharingFolderDialogLayout(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll("#share-folder-dialog mwc-textfield.share-email");t.length>1&&t.forEach((e=>{var t;"first-email"!==e.id&&(null===(t=e.parentNode)||void 0===t||t.removeChild(e))}))}_shareFolderDialog(e){this.selectedFolder=globalThis.backendaiclient.supports("vfolder-id-based")?this._getControlID(e):this._getControlName(e),this.selectedFolderType=this._getControlType(e),this._initializeSharingFolderDialogLayout(),this.openDialog("share-folder-dialog")}_showPermissionSettingModal(e){const t=new CustomEvent("show-invite-folder-permission-setting",{detail:e,bubbles:!0});document.dispatchEvent(t)}_shareFolder(e){var t,i;const o=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll("mwc-textfield.share-email"),r=Array.prototype.filter.call(o,(e=>e.isUiValid&&""!==e.value)).map((e=>e.value.trim())),a=(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("mwc-radio[name=share-folder-permission][checked]")).value;if(0===r.length){this.notification.text=D("data.invitation.NoValidEmails"),this.notification.show(),this.shareFolderDialog.hide();for(const e of Array.from(o))e.value="";return}let s;s="user"===this.selectedFolderType?globalThis.backendaiclient.vfolder.invite(a,r,this.selectedFolder):globalThis.backendaiclient.vfolder.share(a,r,this.selectedFolder);const d=(e,t)=>e.filter((e=>!t.includes(e)));s.then((e=>{var t;let i;if("user"===this.selectedFolderType)if(e.invited_ids&&e.invited_ids.length>0){i=D("data.invitation.Invited");const t=d(r,e.invited_ids);t.length>0&&(i=D("data.invitation.FolderSharingNotAvailableToUser")+t.join(", "))}else i=D("data.invitation.NoOneWasInvited");else if(e.shared_emails&&e.shared_emails.length>0){i=D("data.invitation.Shared");const t=d(r,e.shared_emails);t.length>0&&(i=D("data.invitation.FolderSharingNotAvailableToUser")+t.join(", "))}else i=D("data.invitation.NoOneWasShared");this.notification.text=i,this.notification.show(),this.shareFolderDialog.hide();for(let e=o.length-1;e>0;e--){const i=o[e];null===(t=i.parentElement)||void 0===t||t.removeChild(i)}})).catch((e=>{e&&e.message&&(this.notification.text=L.relieve(e.message),this.notification.detail=e.message),this.notification.show()}))}_restoreFolder(e){const t=this._getControlID(e)||"";globalThis.backendaiclient.vfolder.restore_from_trash_bin(t).then((async e=>{this.notification.text=D("data.folders.FolderRestored",{folderName:this.deleteFolderName||""}),this.notification.show(),await this.refreshFolderList()})).catch((e=>{e&&e.message&&(this.notification.text=L.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_deleteFromTrashBin(){if(this.deleteFromTrashBinNameInput.value!==this.deleteFolderName)return this.notification.text=D("data.folders.FolderNameMismatched"),void this.notification.show();globalThis.backendaiclient.vfolder.delete_from_trash_bin(this.deleteFolderID).then((async e=>{this.notification.text=D("data.folders.FolderDeletedForever",{folderName:this.deleteFolderName||""}),this.notification.show(),await this.refreshFolderList()})).catch((e=>{e&&e.message&&(this.notification.text=L.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))})),this.closeDialog("delete-from-trash-bin-dialog"),this.deleteFromTrashBinNameInput.value=""}};o([_({type:String})],_e.prototype,"storageType",void 0),o([_({type:Array})],_e.prototype,"folders",void 0),o([_({type:Object})],_e.prototype,"folderInfo",void 0),o([_({type:Boolean})],_e.prototype,"is_admin",void 0),o([_({type:Boolean})],_e.prototype,"enableStorageProxy",void 0),o([_({type:Boolean})],_e.prototype,"enableInferenceWorkload",void 0),o([_({type:Boolean})],_e.prototype,"enableVfolderTrashBin",void 0),o([_({type:Boolean})],_e.prototype,"authenticated",void 0),o([_({type:String})],_e.prototype,"renameFolderName",void 0),o([_({type:String})],_e.prototype,"renameFolderID",void 0),o([_({type:String})],_e.prototype,"deleteFolderName",void 0),o([_({type:String})],_e.prototype,"deleteFolderID",void 0),o([_({type:String})],_e.prototype,"leaveFolderName",void 0),o([_({type:String})],_e.prototype,"existingFile",void 0),o([_({type:Array})],_e.prototype,"invitees",void 0),o([_({type:String})],_e.prototype,"selectedFolder",void 0),o([_({type:String})],_e.prototype,"selectedFolderType",void 0),o([_({type:Object})],_e.prototype,"indicator",void 0),o([_({type:Object})],_e.prototype,"notification",void 0),o([_({type:String})],_e.prototype,"listCondition",void 0),o([_({type:Array})],_e.prototype,"allowed_folder_type",void 0),o([_({type:Object})],_e.prototype,"_boundIndexRenderer",void 0),o([_({type:Object})],_e.prototype,"_boundTypeRenderer",void 0),o([_({type:Object})],_e.prototype,"_boundFolderListRenderer",void 0),o([_({type:Object})],_e.prototype,"_boundControlFolderListRenderer",void 0),o([_({type:Object})],_e.prototype,"_boundTrashBinControlFolderListRenderer",void 0),o([_({type:Object})],_e.prototype,"_boundPermissionViewRenderer",void 0),o([_({type:Object})],_e.prototype,"_boundOwnerRenderer",void 0),o([_({type:Object})],_e.prototype,"_boundPermissionRenderer",void 0),o([_({type:Object})],_e.prototype,"_boundCloneableRenderer",void 0),o([_({type:Object})],_e.prototype,"_boundQuotaRenderer",void 0),o([_({type:Object})],_e.prototype,"_boundInviteeInfoRenderer",void 0),o([_({type:Object})],_e.prototype,"_boundIDRenderer",void 0),o([_({type:Object})],_e.prototype,"_boundStatusRenderer",void 0),o([_({type:Boolean})],_e.prototype,"_folderRefreshing",void 0),o([_({type:Number})],_e.prototype,"lastQueryTime",void 0),o([_({type:Object})],_e.prototype,"permissions",void 0),o([_({type:Number})],_e.prototype,"selectAreaHeight",void 0),o([_({type:Object})],_e.prototype,"volumeInfo",void 0),o([_({type:Array})],_e.prototype,"quotaSupportStorageBackends",void 0),o([_({type:Object})],_e.prototype,"quotaUnit",void 0),o([_({type:Object})],_e.prototype,"maxSize",void 0),o([_({type:Object})],_e.prototype,"quota",void 0),o([_({type:Boolean})],_e.prototype,"directoryBasedUsage",void 0),o([w("#loading-spinner")],_e.prototype,"spinner",void 0),o([w("#list-status")],_e.prototype,"_listStatus",void 0),o([w("#modify-folder-quota")],_e.prototype,"modifyFolderQuotaInput",void 0),o([w("#modify-folder-quota-unit")],_e.prototype,"modifyFolderQuotaUnitSelect",void 0),o([w("#folder-list-grid")],_e.prototype,"folderListGrid",void 0),o([w("#delete-folder-name")],_e.prototype,"deleteFolderNameInput",void 0),o([w("#delete-from-trash-bin-name-input")],_e.prototype,"deleteFromTrashBinNameInput",void 0),o([w("#new-folder-name")],_e.prototype,"newFolderNameInput",void 0),o([w("#leave-folder-name")],_e.prototype,"leaveFolderNameInput",void 0),o([w("#update-folder-permission")],_e.prototype,"updateFolderPermissionSelect",void 0),o([w("#update-folder-cloneable")],_e.prototype,"updateFolderCloneableSwitch",void 0),o([w("#share-folder-dialog")],_e.prototype,"shareFolderDialog",void 0),o([w("#session-launcher")],_e.prototype,"sessionLauncher",void 0),o([x()],_e.prototype,"_unionedAllowedPermissionByVolume",void 0),_e=o([$("backend-ai-storage-list")],_e);let we=class extends k{constructor(){super(...arguments),this.apiMajorVersion="",this.folderListFetchKey="first",this.is_admin=!1,this.enableStorageProxy=!1,this.enableInferenceWorkload=!1,this.enableModelStore=!1,this.supportVFolderTrashBin=!1,this.authenticated=!1,this.vhost="",this.selectedVhost="",this.vhosts=[],this.usageModes=["General"],this.permissions=["Read-Write","Read-Only","Delete"],this.allowedGroups=[],this.allowedModelTypeGroups=[],this.groupListByUsage=[],this.generalTypeGroups=[],this.allowed_folder_type=[],this.notification=Object(),this.folderLists=Object(),this._status="inactive",this.active=!1,this._vfolderInnatePermissionSupport=!1,this.storageInfo=Object(),this._activeTab="general",this._helpDescription="",this._helpDescriptionTitle="",this._helpDescriptionIcon="",this._helpDescriptionStorageProxyInfo=Object(),this.cloneFolderName="",this.cloneFolder="",this.storageProxyInfo=Object(),this.folderType="user",this.currentGroupIdx=0,this.openAddFolderDialog=()=>this._addFolderDialog()}static get styles(){return[F,S,T,I,m`
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
      `]}renderStatusIndicator(e,t){const i=e<70?0:e<90?1:2,o=["Adequate","Caution","Insufficient"][i],r=[C("data.usage.Adequate"),C("data.usage.Caution"),C("data.usage.Insufficient")][i];return R`
      <div
        class="host-status-indicator ${o.toLocaleLowerCase()} self-center"
      >
        ${t?r:""}
      </div>
    `}render(){var e,t,i,o,r,a,s,d,l,n,c,h,p,u,m,g,f,v;return R`
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
            ${this.enableInferenceWorkload?R`
                  <div
                    style="display: ${"model"===this._activeTab?"block":"none"};"
                  >
                    <backend-ai-storage-list
                      id="model-folder-storage"
                      storageType="model"
                      ?active="${!0===this.active&&"model"===this._activeTab}"
                    ></backend-ai-storage-list>
                  </div>
                `:R``}
            ${this.enableModelStore?R`
                  <backend-ai-react-model-store-list
                    id="model-store-folder-lists"
                    class="tab-content"
                    style="display:none;"
                    ?active="${!0===this.active&&"modelStore"===this._activeTab}"
                  ></backend-ai-react-model-store-list>
                `:R``}
            ${this.supportVFolderTrashBin?R`
                  <div
                    style="display: ${"trash-bin"===this._activeTab?"block":"none"};"
                  >
                    <backend-ai-storage-list
                      id="trash-bin-folder-storage"
                      storageType="deadVFolderStatus"
                      ?active="${!0===this.active&&"trash-bin"===this._activeTab}"
                    ></backend-ai-storage-list>
                  </div>
                `:R``}
          </div>
        </div>
      </div>
      <backend-ai-dialog id="add-folder-dialog" fixed backdrop>
        <span slot="title">${C("data.CreateANewStorageFolder")}</span>
        <div slot="content" class="vertical layout flex">
          <mwc-textfield
            id="add-folder-name"
            label="${C("data.Foldername")}"
            @change="${()=>this._validateFolderName()}"
            pattern="^[a-zA-Z0-9._-]*$"
            required
            validationMessage="${C("data.AllowsLettersNumbersAnd-_Dot")}"
            maxLength="64"
            placeholder="${C("maxLength.64chars")}"
          ></mwc-textfield>
          <mwc-select
            class="full-width fixed-position"
            id="add-folder-host"
            label="${C("data.Host")}"
            fixedMenuPosition
            @selected=${e=>this.selectedVhost=e.target.value}
          >
            ${this.vhosts.map((e=>{var t,i,o;const r=this.storageProxyInfo[e]&&(null===(t=this.storageProxyInfo[e])||void 0===t?void 0:t.usage)&&(null===(o=null===(i=this.storageProxyInfo[e])||void 0===i?void 0:i.usage)||void 0===o?void 0:o.percentage);return R`
                <mwc-list-item
                  hasMeta
                  .value="${e}"
                  ?selected="${e===this.vhost}"
                >
                  <div class="horizontal layout justified center">
                    <span>${e}</span>
                    ${R`
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
            ${"number"==typeof(null===(t=null===(e=this.storageProxyInfo[this.selectedVhost])||void 0===e?void 0:e.usage)||void 0===t?void 0:t.percentage)?R`
                  ${C("data.usage.StatusOfSelectedHost")}:&nbsp;${this.renderStatusIndicator(null===(o=null===(i=this.storageProxyInfo[this.selectedVhost])||void 0===i?void 0:i.usage)||void 0===o?void 0:o.percentage,!0)}
                `:R``}
          </div>
          <div class="horizontal layout">
            <mwc-select
              id="add-folder-type"
              label="${C("data.Type")}"
              style="width:${this.is_admin&&this.allowed_folder_type.includes("group")?"50%":"100%"}"
              @change=${()=>{this._toggleFolderTypeInput(),this._toggleGroupSelect()}}
              required
            >
              ${this.allowed_folder_type.includes("user")?R`
                    <mwc-list-item value="user" selected>
                      ${C("data.User")}
                    </mwc-list-item>
                  `:R``}
              ${this.is_admin&&this.allowed_folder_type.includes("group")?R`
                    <mwc-list-item
                      value="group"
                      ?selected="${!this.allowed_folder_type.includes("user")}"
                    >
                      ${C("data.Project")}
                    </mwc-list-item>
                  `:R``}
            </mwc-select>
            ${this.is_admin&&this.allowed_folder_type.includes("group")?R`
                  <mwc-select
                    class="fixed-position"
                    id="add-folder-group"
                    ?disabled=${"user"===this.folderType}
                    label="${C("data.Project")}"
                    FixedMenuPosition
                  >
                    ${this.groupListByUsage.map(((e,t)=>R`
                        <mwc-list-item
                          value="${e.name}"
                          ?selected="${this.currentGroupIdx===t}"
                        >
                          ${e.name}
                        </mwc-list-item>
                      `))}
                  </mwc-select>
                `:R``}
          </div>
          ${this._vfolderInnatePermissionSupport?R`
                <div class="horizontal layout">
                  <mwc-select
                    class="fixed-position"
                    id="add-folder-usage-mode"
                    label="${C("data.UsageMode")}"
                    fixedMenuPosition
                    @change=${()=>{this._toggleGroupSelect()}}
                  >
                    ${this.usageModes.map(((e,t)=>R`
                        <mwc-list-item value="${e}" ?selected="${0===t}">
                          ${e}
                        </mwc-list-item>
                      `))}
                  </mwc-select>
                  <mwc-select
                    class="fixed-position"
                    id="add-folder-permission"
                    label="${C("data.Permission")}"
                    fixedMenuPosition
                  >
                    ${this.permissions.map(((e,t)=>R`
                        <mwc-list-item value="${e}" ?selected="${0===t}">
                          ${e}
                        </mwc-list-item>
                      `))}
                  </mwc-select>
                </div>
              `:R``}
          ${this.enableStorageProxy?R`
                <div
                  id="cloneable-container"
                  class="horizontal layout flex wrap center justified"
                  style="display:none;"
                >
                  <p style="margin-left:10px;">
                    ${C("data.folders.Cloneable")}
                  </p>
                  <mwc-switch
                    id="add-folder-cloneable"
                    style="margin-right:10px;"
                  ></mwc-switch>
                </div>
              `:R``}
          <div style="font-size:11px;">
            ${C("data.DialogFolderStartingWithDotAutomount")}
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex">
          <mwc-button
            unelevated
            fullwidth
            id="add-button"
            icon="rowing"
            label="${C("data.Create")}"
            @click="${()=>this._addFolder()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="clone-folder-dialog" fixed backdrop>
        <span slot="title">${C("data.folders.CloneAFolder")}</span>
        <div slot="content" style="width:100%;">
          <mwc-textfield
            id="clone-folder-src"
            label="${C("data.FolderToCopy")}"
            value="${this.cloneFolderName}"
            disabled
          ></mwc-textfield>
          <mwc-textfield
            id="clone-folder-name"
            label="${C("data.Foldername")}"
            @change="${()=>this._validateFolderName()}"
            pattern="^[a-zA-Z0-9._-]*$"
            required
            validationMessage="${C("data.AllowsLettersNumbersAnd-_Dot")}"
            maxLength="64"
            placeholder="${C("maxLength.64chars")}"
          ></mwc-textfield>
          <mwc-select
            class="full-width fixed-position"
            id="clone-folder-host"
            label="${C("data.Host")}"
            fixedMenuPosition
          >
            ${this.vhosts.map(((e,t)=>R`
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
              label="${C("data.Type")}"
              style="width:${this.is_admin&&this.allowed_folder_type.includes("group")?"50%":"100%"}"
            >
              ${this.allowed_folder_type.includes("user")?R`
                    <mwc-list-item value="user" selected>
                      ${C("data.User")}
                    </mwc-list-item>
                  `:R``}
              ${this.is_admin&&this.allowed_folder_type.includes("group")?R`
                    <mwc-list-item
                      value="group"
                      ?selected="${!this.allowed_folder_type.includes("user")}"
                    >
                      ${C("data.Project")}
                    </mwc-list-item>
                  `:R``}
            </mwc-select>
            ${this.is_admin&&this.allowed_folder_type.includes("group")?R`
                  <mwc-select
                    class="fixed-position"
                    id="clone-folder-group"
                    label="${C("data.Project")}"
                    FixedMenuPosition
                  >
                    ${this.allowedGroups.map(((e,t)=>R`
                        <mwc-list-item
                          value="${e.name}"
                          ?selected="${e.name===globalThis.backendaiclient.current_group}"
                        >
                          ${e.name}
                        </mwc-list-item>
                      `))}
                  </mwc-select>
                `:R``}
          </div>
          ${this._vfolderInnatePermissionSupport?R`
                <div class="horizontal layout">
                  <mwc-select
                    class="fixed-position"
                    id="clone-folder-usage-mode"
                    label="${C("data.UsageMode")}"
                    FixedMenuPosition
                  >
                    ${this.usageModes.map(((e,t)=>R`
                        <mwc-list-item value="${e}" ?selected="${0===t}">
                          ${e}
                        </mwc-list-item>
                      `))}
                  </mwc-select>
                  <mwc-select
                    class="fixed-position"
                    id="clone-folder-permission"
                    label="${C("data.Permission")}"
                    FixedMenuPosition
                  >
                    ${this.permissions.map(((e,t)=>R`
                        <mwc-list-item value="${e}" ?selected="${0===t}">
                          ${e}
                        </mwc-list-item>
                      `))}
                  </mwc-select>
                </div>
              `:R``}
          ${this.enableStorageProxy?R`
                <div class="horizontal layout flex wrap center justified">
                  <p style="color:rgba(0, 0, 0, 0.6);">
                    ${C("data.folders.Cloneable")}
                  </p>
                  <mwc-switch
                    id="clone-folder-cloneable"
                    style="margin-right:10px;"
                  ></mwc-switch>
                </div>
              `:R``}
          <div style="font-size:11px;">
            ${C("data.DialogFolderStartingWithDotAutomount")}
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex">
          <mwc-button
            unelevated
            fullwidth
            id="clone-button"
            icon="file_copy"
            label="${C("data.Create")}"
            @click="${()=>this._cloneFolder()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="help-description" fixed backdrop>
        <span slot="title">${this._helpDescriptionTitle}</span>
        <div slot="content" class="vertical layout">
          <div class="horizontal layout center">
            ${""==this._helpDescriptionIcon?R``:R`
                  <img
                    slot="graphic"
                    src="resources/icons/${this._helpDescriptionIcon}"
                    style="width:64px;height:64px;margin-right:10px;"
                  />
                `}
            <p style="font-size:14px;width:256px;">
              ${O(this._helpDescription)}
            </p>
          </div>
          ${void 0!==(null===(a=null===(r=this._helpDescriptionStorageProxyInfo)||void 0===r?void 0:r.usage)||void 0===a?void 0:a.percentage)?R`
                <div class="vertical layout" style="padding-left:8px;">
                  <span><strong>${C("data.usage.Status")}</strong></span>
                  <div class="horizontal layout">
                    ${this.renderStatusIndicator(null===(d=null===(s=this._helpDescriptionStorageProxyInfo)||void 0===s?void 0:s.usage)||void 0===d?void 0:d.percentage,!0)}
                  </div>
                  (${Math.floor(null===(n=null===(l=this._helpDescriptionStorageProxyInfo)||void 0===l?void 0:l.usage)||void 0===n?void 0:n.percentage)}%
                  ${C("data.usage.Used")}
                  ${(null===(h=null===(c=this._helpDescriptionStorageProxyInfo)||void 0===c?void 0:c.usage)||void 0===h?void 0:h.total)&&(null===(u=null===(p=this._helpDescriptionStorageProxyInfo)||void 0===p?void 0:p.usage)||void 0===u?void 0:u.used)?R`
                        ,
                        ${globalThis.backendaiutils._humanReadableFileSize(null===(g=null===(m=this._helpDescriptionStorageProxyInfo)||void 0===m?void 0:m.usage)||void 0===g?void 0:g.used)}
                        /
                        ${globalThis.backendaiutils._humanReadableFileSize(null===(v=null===(f=this._helpDescriptionStorageProxyInfo)||void 0===f?void 0:f.usage)||void 0===v?void 0:v.total)}
                      `:R``}
                  )
                </div>
              `:R``}
        </div>
      </backend-ai-dialog>
    `}firstUpdated(){var e;this.notification=globalThis.lablupNotification,this.folderLists=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll("backend-ai-storage-list"),fetch("resources/storage_metadata.json").then((e=>e.json())).then((e=>{const t=Object();for(const i in e.storageInfo)({}).hasOwnProperty.call(e.storageInfo,i)&&(t[i]={},"name"in e.storageInfo[i]&&(t[i].name=e.storageInfo[i].name),"description"in e.storageInfo[i]?t[i].description=e.storageInfo[i].description:t[i].description=D("data.NoStorageDescriptionFound"),"icon"in e.storageInfo[i]?t[i].icon=e.storageInfo[i].icon:t[i].icon="local.png","dialects"in e.storageInfo[i]&&e.storageInfo[i].dialects.forEach((e=>{t[e]=t[i]})));this.storageInfo=t})),this.options={responsive:!0,maintainAspectRatio:!0,legend:{display:!0,position:"bottom",align:"center",labels:{fontSize:20,boxWidth:10}}},void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._getStorageProxyInformation()}),!0):this._getStorageProxyInformation(),document.addEventListener("backend-ai-folder-list-changed",(()=>{this.folderListFetchKey=(new Date).toISOString()})),document.addEventListener("backend-ai-vfolder-cloning",(e=>{if(e.detail){const t=e.detail;this.cloneFolderName=t.name,this.cloneFolder=globalThis.backendaiclient.supports("vfolder-id-based")?t.id:t.name,this._cloneFolderDialog()}}))}connectedCallback(){super.connectedCallback(),document.dispatchEvent(new CustomEvent("backend-ai-data-view:connected"))}disconnectedCallback(){super.disconnectedCallback(),document.dispatchEvent(new CustomEvent("backend-ai-data-view:disconnected"))}async _viewStateChanged(e){if(await this.updateComplete,!1===e)return;const t=()=>{this.is_admin=globalThis.backendaiclient.is_admin,this.authenticated=!0,this.enableStorageProxy=globalThis.backendaiclient.supports("storage-proxy"),this.enableInferenceWorkload=globalThis.backendaiclient.supports("inference-workload"),this.enableModelStore=globalThis.backendaiclient.supports("model-store")&&globalThis.backendaiclient._config.enableModelStore,this.supportVFolderTrashBin=globalThis.backendaiclient.supports("vfolder-trash-bin"),this.enableInferenceWorkload&&!this.usageModes.includes("Model")&&this.usageModes.push("Model"),this.apiMajorVersion=globalThis.backendaiclient.APIMajorVersion,this._getStorageProxyInformation(),globalThis.backendaiclient.isAPIVersionCompatibleWith("v4.20191215")&&(this._vfolderInnatePermissionSupport=!0),globalThis.backendaiclient.vfolder.list_allowed_types().then((e=>{this.allowed_folder_type=e}))};void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{t()}),!0):t()}_toggleFolderTypeInput(){this.folderType=this.addFolderTypeSelect.value}_getAutoSelectedVhostName(e){var t;const i=Math.min(...Object.values(e.volume_info).map((e=>{var t;return null===(t=null==e?void 0:e.usage)||void 0===t?void 0:t.percentage})));return null!==(t=Object.keys(e.volume_info).find((t=>{var o,r;return(null===(r=null===(o=e.volume_info[t])||void 0===o?void 0:o.usage)||void 0===r?void 0:r.percentage)===i})))&&void 0!==t?t:e.default}_getAutoSelectedVhostInfo(e){var t;const i=Math.min(...Object.values(e.volume_info).map((e=>{var t;return null===(t=null==e?void 0:e.usage)||void 0===t?void 0:t.percentage})));return null!==(t=Object.values(e.volume_info).find((e=>{var t;return(null===(t=null==e?void 0:e.usage)||void 0===t?void 0:t.percentage)===i})))&&void 0!==t?t:e.volume_info[e.default]}async _getAutoSelectedVhostIncludedList(){const e=await globalThis.backendaiclient.vfolder.list_hosts();return e.allowed.length>1&&(e.allowed.unshift(`auto (${this._getAutoSelectedVhostName(e)})`),e.volume_info[`auto (${this._getAutoSelectedVhostName(e)})`]=this._getAutoSelectedVhostInfo(e)),e}async _cloneFolderDialog(){const e=await this._getAutoSelectedVhostIncludedList();if(this.addFolderNameInput.value="",this.vhosts=e.allowed,this.vhosts.length>1?this.vhost=this.selectedVhost=`auto (${this._getAutoSelectedVhostName(e)})`:this.vhost=this.selectedVhost=e.default,this.allowed_folder_type.includes("group")){const e=await globalThis.backendaiclient.group.list();this.allowedGroups=e.groups}this.cloneFolderNameInput.value=await this._checkFolderNameAlreadyExists(this.cloneFolderName),this.openDialog("clone-folder-dialog")}async _addFolderDialog(){var e;const t=await this._getAutoSelectedVhostIncludedList();if(this.addFolderNameInput.value="",this.vhosts=t.allowed,this.vhosts.length>1?this.vhost=this.selectedVhost=`auto (${this._getAutoSelectedVhostName(t)})`:this.vhost=this.selectedVhost=t.default,this.allowed_folder_type.includes("group")){const t=await globalThis.backendaiclient.group.list(void 0,void 0,void 0,["GENERAL","MODEL_STORE"]);this.allowedModelTypeGroups=[],this.allowedGroups=[],null===(e=null==t?void 0:t.groups)||void 0===e||e.forEach((e=>{"MODEL_STORE"===e.type?this.allowedModelTypeGroups.push(e):this.allowedGroups.push(e)})),this._toggleGroupSelect()}this.openDialog("add-folder-dialog")}async _getStorageProxyInformation(){const e=await this._getAutoSelectedVhostIncludedList();this.storageProxyInfo=e.volume_info||{}}openDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).show()}closeDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).hide()}_showStorageDescription(e,t){var i;e.stopPropagation(),t in this.storageInfo?(this._helpDescriptionTitle=this.storageInfo[t].name,this._helpDescriptionIcon=this.storageInfo[t].icon,this._helpDescription=this.storageInfo[t].description):(this._helpDescriptionTitle=t,this._helpDescriptionIcon="local.png",this._helpDescription=D("data.NoStorageDescriptionFound")),this._helpDescriptionStorageProxyInfo=this.storageProxyInfo[t];(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#help-description")).show()}_indexFrom1(e){return e+1}_toggleGroupSelect(){var e;this.groupListByUsage="Model"!==(null===(e=this.addFolderUsageModeSelect)||void 0===e?void 0:e.value)?this.allowedGroups:[...this.allowedGroups,...this.allowedModelTypeGroups],this.addFolderGroupSelect&&this.addFolderGroupSelect.layout(!0).then((()=>{this.groupListByUsage.length>0?(this.currentGroupIdx=this.addFolderGroupSelect.items.findIndex((e=>e.value===globalThis.backendaiclient.current_group)),this.currentGroupIdx=this.currentGroupIdx<0?0:this.currentGroupIdx,this.addFolderGroupSelect.createAdapter().setSelectedText(this.groupListByUsage[this.currentGroupIdx].name)):this.addFolderGroupSelect.disabled=!0})),this._toggleCloneableSwitch()}_toggleCloneableSwitch(){var e;this.cloneableContainer&&("Model"===(null===(e=this.addFolderUsageModeSelect)||void 0===e?void 0:e.value)&&this.is_admin?this.cloneableContainer.style.display="flex":this.cloneableContainer.style.display="none")}_addFolder(){var e,t,i;const o=this.addFolderNameInput.value;let r=(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#add-folder-host")).value;const a=r.match(/^auto \((.+)\)$/);a&&(r=a[1]);let s,d=this.addFolderTypeSelect.value;const l=this.addFolderUsageModeSelect,n=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#add-folder-permission"),c=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#add-folder-cloneable");let h="",p="",u=!1;if(!1===["user","group"].includes(d)&&(d="user"),s="user"===d?"":this.is_admin?this.addFolderGroupSelect.value:globalThis.backendaiclient.current_group,l&&(h=l.value,h=h.toLowerCase()),n)switch(p=n.value,p){case"Read-Write":default:p="rw";break;case"Read-Only":p="ro";break;case"Delete":p="wd"}if(c&&(u=c.selected),this.addFolderNameInput.reportValidity(),this.addFolderNameInput.checkValidity()){globalThis.backendaiclient.vfolder.create(o,r,s,h,p,u).then((()=>{this.notification.text=D("data.folders.FolderCreated"),this.notification.show(),this._refreshFolderList()})).catch((e=>{e&&e.message&&(this.notification.text=L.relieve(e.message),this.notification.detail=e.message,this.notification.show(!0,e))})),this.closeDialog("add-folder-dialog")}}async _cloneFolder(){var e,t,i,o,r;const a=await this._checkFolderNameAlreadyExists(this.cloneFolderNameInput.value,!0);let s=(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#clone-folder-host")).value;const d=s.match(/^auto \((.+)\)$/);d&&(s=d[1]),(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#clone-folder-type")).value;const l=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#clone-folder-usage-mode"),n=null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("#clone-folder-permission"),c=null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector("#clone-folder-cloneable");let h="",p="",u=!1;if(l&&(h=l.value,h=h.toLowerCase()),n)switch(p=n.value,p){case"Read-Write":default:p="rw";break;case"Read-Only":p="ro";break;case"Delete":p="wd"}if(u=!!c&&c.selected,this.cloneFolderNameInput.reportValidity(),this.cloneFolderNameInput.checkValidity()&&this.cloneFolder){const e={cloneable:u,permission:p,target_host:s,target_name:a,usage_mode:h};globalThis.backendaiclient.vfolder.clone(e,this.cloneFolder).then((()=>{this.notification.text=D("data.folders.FolderCloned"),this.notification.show(),this._refreshFolderList()})).catch((e=>{e&&e.message&&(this.notification.text=L.relieve(e.message),this.notification.detail=e.message,this.notification.show(!0,e))})),this.closeDialog("clone-folder-dialog")}}_validateFolderName(){this.addFolderNameInput.validityTransform=(e,t)=>{if(t.valid){let e=!/[`~!@#$%^&*()|+=?;:'",<>{}[\]\\/\s]/gi.test(this.addFolderNameInput.value);return e||(this.addFolderNameInput.validationMessage=D("data.AllowsLettersNumbersAnd-_Dot")),this.addFolderNameInput.value.length>64&&(e=!1,this.addFolderNameInput.validationMessage=D("data.FolderNameTooLong")),{valid:e,customError:!e}}return t.valueMissing?(this.addFolderNameInput.validationMessage=D("data.FolderNameRequired"),{valid:t.valid,customError:!t.valid}):(this.addFolderNameInput.validationMessage=D("data.AllowsLettersNumbersAnd-_Dot"),{valid:t.valid,customError:!t.valid})}}_refreshFolderList(){for(const e of this.folderLists)e.refreshFolderList()}async _checkFolderNameAlreadyExists(e,t=!1){const i=globalThis.backendaiclient.current_group_id(),o=(await globalThis.backendaiclient.vfolder.list(i)).map((e=>e.name));if(o.includes(e)){t&&(this.notification.text=D("import.FolderAlreadyExists"),this.notification.show());let i=1,r=e;for(;o.includes(r);)r=e+"_"+i,i++;e=r}return e}};o([_({type:String})],we.prototype,"apiMajorVersion",void 0),o([_({type:String})],we.prototype,"folderListFetchKey",void 0),o([_({type:Boolean})],we.prototype,"is_admin",void 0),o([_({type:Boolean})],we.prototype,"enableStorageProxy",void 0),o([_({type:Boolean})],we.prototype,"enableInferenceWorkload",void 0),o([_({type:Boolean})],we.prototype,"enableModelStore",void 0),o([_({type:Boolean})],we.prototype,"supportVFolderTrashBin",void 0),o([_({type:Boolean})],we.prototype,"authenticated",void 0),o([_({type:String})],we.prototype,"vhost",void 0),o([_({type:String})],we.prototype,"selectedVhost",void 0),o([_({type:Array})],we.prototype,"vhosts",void 0),o([_({type:Array})],we.prototype,"usageModes",void 0),o([_({type:Array})],we.prototype,"permissions",void 0),o([_({type:Array})],we.prototype,"allowedGroups",void 0),o([_({type:Array})],we.prototype,"allowedModelTypeGroups",void 0),o([_({type:Array})],we.prototype,"groupListByUsage",void 0),o([_({type:Array})],we.prototype,"generalTypeGroups",void 0),o([_({type:Array})],we.prototype,"allowed_folder_type",void 0),o([_({type:Object})],we.prototype,"notification",void 0),o([_({type:Object})],we.prototype,"folderLists",void 0),o([_({type:String})],we.prototype,"_status",void 0),o([_({type:Boolean,reflect:!0})],we.prototype,"active",void 0),o([_({type:Boolean})],we.prototype,"_vfolderInnatePermissionSupport",void 0),o([_({type:Object})],we.prototype,"storageInfo",void 0),o([_({type:String})],we.prototype,"_activeTab",void 0),o([_({type:String})],we.prototype,"_helpDescription",void 0),o([_({type:String})],we.prototype,"_helpDescriptionTitle",void 0),o([_({type:String})],we.prototype,"_helpDescriptionIcon",void 0),o([_({type:Object})],we.prototype,"_helpDescriptionStorageProxyInfo",void 0),o([_({type:Object})],we.prototype,"options",void 0),o([_({type:Number})],we.prototype,"capacity",void 0),o([_({type:String})],we.prototype,"cloneFolderName",void 0),o([_({type:String})],we.prototype,"cloneFolder",void 0),o([_({type:Object})],we.prototype,"storageProxyInfo",void 0),o([_({type:String})],we.prototype,"folderType",void 0),o([_({type:Number})],we.prototype,"currentGroupIdx",void 0),o([w("#add-folder-name")],we.prototype,"addFolderNameInput",void 0),o([w("#clone-folder-name")],we.prototype,"cloneFolderNameInput",void 0),o([w("#add-folder-usage-mode")],we.prototype,"addFolderUsageModeSelect",void 0),o([w("#add-folder-group")],we.prototype,"addFolderGroupSelect",void 0),o([w("#add-folder-type")],we.prototype,"addFolderTypeSelect",void 0),o([w("#cloneable-container")],we.prototype,"cloneableContainer",void 0),o([w("#general-folder-storage")],we.prototype,"generalFolderStorageListElement",void 0),o([w("#data-folder-storage")],we.prototype,"dataFolderStorageListElement",void 0),o([w("#automount-folder-storage")],we.prototype,"automountFolderStorageListElement",void 0),o([w("#model-folder-storage")],we.prototype,"modelFolderStorageListElement",void 0),o([w("#trash-bin-folder-storage")],we.prototype,"trashBinFolderStorageListElement",void 0),we=o([$("backend-ai-data-view")],we);
