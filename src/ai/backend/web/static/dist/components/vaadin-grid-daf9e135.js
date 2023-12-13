import{v as e,b4 as t,u as r,b5 as i,ap as o,M as s,_ as a,n,A as l,z as d,w as c,b as h,C as _,F as u,R as p,x as m,G as g,H as f,i as b,e as v,r as w,at as C,ai as y,a_ as x,b6 as z,a4 as E,b7 as k,ah as I,aN as R,aO as S,m as A,a1 as F,N as T,T as $,P,b8 as D,b9 as O,am as L,J as H,K as N,D as B,ba as M,a6 as G,L as W,bb as V,bc as U,a5 as q,a0 as j,bd as K,be as X,aI as Y,aF as J,bf as Z,bg as Q,bh as ee,bi as te}from"./backend-ai-webui-ff615d7c.js";import{A as re,a as ie,g as oe}from"./dir-utils-0f2e97d3.js";
/**
 * @license
 * Copyright 2021 Google Inc.
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
 */function se(r,i,o){var s=function(r,i){var o=new Map;ae.has(r)||ae.set(r,{isEnabled:!0,getObservers:function(e){var t=o.get(e)||[];return o.has(e)||o.set(e,t),t},installedProperties:new Set});var s=ae.get(r);if(s.installedProperties.has(i))return s;var a=function(e,t){var r,i=e;for(;i&&!(r=Object.getOwnPropertyDescriptor(i,t));)i=Object.getPrototypeOf(i);return r}(r,i)||{configurable:!0,enumerable:!0,value:r[i],writable:!0},n=e({},a),l=a.get,d=a.set;if("value"in a){delete n.value,delete n.writable;var c=a.value;l=function(){return c},a.writable&&(d=function(e){c=e})}l&&(n.get=function(){return l.call(this)});d&&(n.set=function(e){var r,o,a=l?l.call(this):e;if(d.call(this,e),s.isEnabled&&(!l||e!==a))try{for(var n=t(s.getObservers(i)),c=n.next();!c.done;c=n.next()){(0,c.value)(e,a)}}catch(e){r={error:e}}finally{try{c&&!c.done&&(o=n.return)&&o.call(n)}finally{if(r)throw r.error}}});return s.installedProperties.add(i),Object.defineProperty(r,i,n),s}(r,i),a=s.getObservers(i);return a.push(o),function(){a.splice(a.indexOf(o),1)}}var ae=new WeakMap;
/**
 * @license
 * Copyright 2021 Google Inc.
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
var ne,le,de=function(e){function s(t){var r=e.call(this,t)||this;return r.unobserves=new Set,r}return r(s,e),s.prototype.destroy=function(){e.prototype.destroy.call(this),this.unobserve()},s.prototype.observe=function(e,r){var i,o,s=this,a=[];try{for(var n=t(Object.keys(r)),l=n.next();!l.done;l=n.next()){var d=l.value,c=r[d].bind(this);a.push(this.observeProperty(e,d,c))}}catch(e){i={error:e}}finally{try{l&&!l.done&&(o=n.return)&&o.call(n)}finally{if(i)throw i.error}}var h=function(){var e,r;try{for(var i=t(a),o=i.next();!o.done;o=i.next()){(0,o.value)()}}catch(t){e={error:t}}finally{try{o&&!o.done&&(r=i.return)&&r.call(i)}finally{if(e)throw e.error}}s.unobserves.delete(h)};return this.unobserves.add(h),h},s.prototype.observeProperty=function(e,t,r){return se(e,t,r)},s.prototype.setObserversEnabled=function(e,t){!function(e,t){var r=ae.get(e);r&&(r.isEnabled=t)}(e,t)},s.prototype.unobserve=function(){var e,r;try{for(var s=t(i([],o(this.unobserves))),a=s.next();!a.done;a=s.next()){(0,a.value)()}}catch(t){e={error:t}}finally{try{a&&!a.done&&(r=s.return)&&r.call(s)}finally{if(e)throw e.error}}},s}(s);
/**
 * @license
 * Copyright 2021 Google Inc.
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
 */!function(e){e.PROCESSING="mdc-switch--processing",e.SELECTED="mdc-switch--selected",e.UNSELECTED="mdc-switch--unselected"}(ne||(ne={})),function(e){e.RIPPLE=".mdc-switch__ripple"}(le||(le={}));
/**
 * @license
 * Copyright 2021 Google Inc.
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
var ce=function(e){function t(t){var r=e.call(this,t)||this;return r.handleClick=r.handleClick.bind(r),r}return r(t,e),t.prototype.init=function(){this.observe(this.adapter.state,{disabled:this.stopProcessingIfDisabled,processing:this.stopProcessingIfDisabled})},t.prototype.handleClick=function(){this.adapter.state.disabled||(this.adapter.state.selected=!this.adapter.state.selected)},t.prototype.stopProcessingIfDisabled=function(){this.adapter.state.disabled&&(this.adapter.state.processing=!1)},t}(de);!function(e){function t(){return null!==e&&e.apply(this,arguments)||this}r(t,e),t.prototype.init=function(){e.prototype.init.call(this),this.observe(this.adapter.state,{disabled:this.onDisabledChange,processing:this.onProcessingChange,selected:this.onSelectedChange})},t.prototype.initFromDOM=function(){this.setObserversEnabled(this.adapter.state,!1),this.adapter.state.selected=this.adapter.hasClass(ne.SELECTED),this.onSelectedChange(),this.adapter.state.disabled=this.adapter.isDisabled(),this.adapter.state.processing=this.adapter.hasClass(ne.PROCESSING),this.setObserversEnabled(this.adapter.state,!0),this.stopProcessingIfDisabled()},t.prototype.onDisabledChange=function(){this.adapter.setDisabled(this.adapter.state.disabled)},t.prototype.onProcessingChange=function(){this.toggleClass(this.adapter.state.processing,ne.PROCESSING)},t.prototype.onSelectedChange=function(){this.adapter.setAriaChecked(String(this.adapter.state.selected)),this.toggleClass(this.adapter.state.selected,ne.SELECTED),this.toggleClass(!this.adapter.state.selected,ne.UNSELECTED)},t.prototype.toggleClass=function(e,t){e?this.adapter.addClass(t):this.adapter.removeClass(t)}}(ce);
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
class he extends u{constructor(){super(...arguments),this.processing=!1,this.selected=!1,this.ariaLabel="",this.ariaLabelledBy="",this.shouldRenderRipple=!1,this.rippleHandlers=new p((()=>(this.shouldRenderRipple=!0,this.ripple))),this.name="",this.value="on",this.mdcFoundationClass=ce}setFormData(e){this.name&&this.selected&&e.append(this.name,this.value)}click(){var e,t;this.disabled||(null===(e=this.mdcRoot)||void 0===e||e.focus(),null===(t=this.mdcRoot)||void 0===t||t.click())}render(){return m`
      <button
        type="button"
        class="mdc-switch ${g(this.getRenderClasses())}"
        role="switch"
        aria-checked="${this.selected}"
        aria-label="${f(this.ariaLabel||void 0)}"
        aria-labelledby="${f(this.ariaLabelledBy||void 0)}"
        .disabled=${this.disabled}
        @click=${this.handleClick}
        @focus="${this.handleFocus}"
        @blur="${this.handleBlur}"
        @pointerdown="${this.handlePointerDown}"
        @pointerup="${this.handlePointerUp}"
        @pointerenter="${this.handlePointerEnter}"
        @pointerleave="${this.handlePointerLeave}"
      >
        <div class="mdc-switch__track"></div>
        <div class="mdc-switch__handle-track">
          ${this.renderHandle()}
        </div>
      </button>

      <input
        type="checkbox"
        aria-hidden="true"
        name="${this.name}"
        .checked=${this.selected}
        .value=${this.value}
      >
    `}getRenderClasses(){return{"mdc-switch--processing":this.processing,"mdc-switch--selected":this.selected,"mdc-switch--unselected":!this.selected}}renderHandle(){return m`
      <div class="mdc-switch__handle">
        ${this.renderShadow()}
        ${this.renderRipple()}
        <div class="mdc-switch__icons">
          ${this.renderOnIcon()}
          ${this.renderOffIcon()}
        </div>
      </div>
    `}renderShadow(){return m`
      <div class="mdc-switch__shadow">
        <div class="mdc-elevation-overlay"></div>
      </div>
    `}renderRipple(){return this.shouldRenderRipple?m`
        <div class="mdc-switch__ripple">
          <mwc-ripple
            internalUseStateLayerCustomProperties
            .disabled="${this.disabled}"
            unbounded>
          </mwc-ripple>
        </div>
      `:m``}renderOnIcon(){return m`
      <svg class="mdc-switch__icon mdc-switch__icon--on" viewBox="0 0 24 24">
        <path d="M19.69,5.23L8.96,15.96l-4.23-4.23L2.96,13.5l6,6L21.46,7L19.69,5.23z" />
      </svg>
    `}renderOffIcon(){return m`
      <svg class="mdc-switch__icon mdc-switch__icon--off" viewBox="0 0 24 24">
        <path d="M20 13H4v-2h16v2z" />
      </svg>
    `}handleClick(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleClick()}handleFocus(){this.rippleHandlers.startFocus()}handleBlur(){this.rippleHandlers.endFocus()}handlePointerDown(e){e.target.setPointerCapture(e.pointerId),this.rippleHandlers.startPress(e)}handlePointerUp(){this.rippleHandlers.endPress()}handlePointerEnter(){this.rippleHandlers.startHover()}handlePointerLeave(){this.rippleHandlers.endHover()}createAdapter(){return{state:this}}}a([n({type:Boolean})],he.prototype,"processing",void 0),a([n({type:Boolean})],he.prototype,"selected",void 0),a([l,n({type:String,attribute:"aria-label"})],he.prototype,"ariaLabel",void 0),a([l,n({type:String,attribute:"aria-labelledby"})],he.prototype,"ariaLabelledBy",void 0),a([d("mwc-ripple")],he.prototype,"ripple",void 0),a([c()],he.prototype,"shouldRenderRipple",void 0),a([n({type:String,reflect:!0})],he.prototype,"name",void 0),a([n({type:String})],he.prototype,"value",void 0),a([h("input")],he.prototype,"formElement",void 0),a([h(".mdc-switch")],he.prototype,"mdcRoot",void 0),a([_({passive:!0})],he.prototype,"handlePointerDown",null);
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-LIcense-Identifier: Apache-2.0
 */
const _e=b`.mdc-elevation-overlay{position:absolute;border-radius:inherit;pointer-events:none;opacity:0;opacity:var(--mdc-elevation-overlay-opacity, 0);transition:opacity 280ms cubic-bezier(0.4, 0, 0.2, 1);background-color:#fff;background-color:var(--mdc-elevation-overlay-color, #fff)}.mdc-switch{align-items:center;background:none;border:none;cursor:pointer;display:inline-flex;flex-shrink:0;margin:0;outline:none;overflow:visible;padding:0;position:relative}.mdc-switch:disabled{cursor:default;pointer-events:none}.mdc-switch__track{overflow:hidden;position:relative;width:100%}.mdc-switch__track::before,.mdc-switch__track::after{border:1px solid transparent;border-radius:inherit;box-sizing:border-box;content:"";height:100%;left:0;position:absolute;width:100%}@media screen and (forced-colors: active){.mdc-switch__track::before,.mdc-switch__track::after{border-color:currentColor}}.mdc-switch__track::before{transition:transform 75ms 0ms cubic-bezier(0, 0, 0.2, 1);transform:translateX(0)}.mdc-switch__track::after{transition:transform 75ms 0ms cubic-bezier(0.4, 0, 0.6, 1);transform:translateX(-100%)}[dir=rtl] .mdc-switch__track::after,.mdc-switch__track[dir=rtl]::after{transform:translateX(100%)}.mdc-switch--selected .mdc-switch__track::before{transition:transform 75ms 0ms cubic-bezier(0.4, 0, 0.6, 1);transform:translateX(100%)}[dir=rtl] .mdc-switch--selected .mdc-switch__track::before,.mdc-switch--selected .mdc-switch__track[dir=rtl]::before{transform:translateX(-100%)}.mdc-switch--selected .mdc-switch__track::after{transition:transform 75ms 0ms cubic-bezier(0, 0, 0.2, 1);transform:translateX(0)}.mdc-switch__handle-track{height:100%;pointer-events:none;position:absolute;top:0;transition:transform 75ms 0ms cubic-bezier(0.4, 0, 0.2, 1);left:0;right:auto;transform:translateX(0)}[dir=rtl] .mdc-switch__handle-track,.mdc-switch__handle-track[dir=rtl]{left:auto;right:0}.mdc-switch--selected .mdc-switch__handle-track{transform:translateX(100%)}[dir=rtl] .mdc-switch--selected .mdc-switch__handle-track,.mdc-switch--selected .mdc-switch__handle-track[dir=rtl]{transform:translateX(-100%)}.mdc-switch__handle{display:flex;pointer-events:auto;position:absolute;top:50%;transform:translateY(-50%);left:0;right:auto}[dir=rtl] .mdc-switch__handle,.mdc-switch__handle[dir=rtl]{left:auto;right:0}.mdc-switch__handle::before,.mdc-switch__handle::after{border:1px solid transparent;border-radius:inherit;box-sizing:border-box;content:"";width:100%;height:100%;left:0;position:absolute;top:0;transition:background-color 75ms 0ms cubic-bezier(0.4, 0, 0.2, 1),border-color 75ms 0ms cubic-bezier(0.4, 0, 0.2, 1);z-index:-1}@media screen and (forced-colors: active){.mdc-switch__handle::before,.mdc-switch__handle::after{border-color:currentColor}}.mdc-switch__shadow{border-radius:inherit;bottom:0;left:0;position:absolute;right:0;top:0}.mdc-elevation-overlay{bottom:0;left:0;right:0;top:0}.mdc-switch__ripple{left:50%;position:absolute;top:50%;transform:translate(-50%, -50%);z-index:-1}.mdc-switch:disabled .mdc-switch__ripple{display:none}.mdc-switch__icons{height:100%;position:relative;width:100%;z-index:1}.mdc-switch__icon{bottom:0;left:0;margin:auto;position:absolute;right:0;top:0;opacity:0;transition:opacity 30ms 0ms cubic-bezier(0.4, 0, 1, 1)}.mdc-switch--selected .mdc-switch__icon--on,.mdc-switch--unselected .mdc-switch__icon--off{opacity:1;transition:opacity 45ms 30ms cubic-bezier(0, 0, 0.2, 1)}:host{display:inline-flex;outline:none}input{display:none}.mdc-switch{width:36px;width:var(--mdc-switch-track-width, 36px)}.mdc-switch.mdc-switch--selected:enabled .mdc-switch__handle::after{background:#6200ee;background:var(--mdc-switch-selected-handle-color, var(--mdc-theme-primary, #6200ee))}.mdc-switch.mdc-switch--selected:enabled:hover:not(:focus):not(:active) .mdc-switch__handle::after{background:#310077;background:var(--mdc-switch-selected-hover-handle-color, #310077)}.mdc-switch.mdc-switch--selected:enabled:focus:not(:active) .mdc-switch__handle::after{background:#310077;background:var(--mdc-switch-selected-focus-handle-color, #310077)}.mdc-switch.mdc-switch--selected:enabled:active .mdc-switch__handle::after{background:#310077;background:var(--mdc-switch-selected-pressed-handle-color, #310077)}.mdc-switch.mdc-switch--selected:disabled .mdc-switch__handle::after{background:#424242;background:var(--mdc-switch-disabled-selected-handle-color, #424242)}.mdc-switch.mdc-switch--unselected:enabled .mdc-switch__handle::after{background:#616161;background:var(--mdc-switch-unselected-handle-color, #616161)}.mdc-switch.mdc-switch--unselected:enabled:hover:not(:focus):not(:active) .mdc-switch__handle::after{background:#212121;background:var(--mdc-switch-unselected-hover-handle-color, #212121)}.mdc-switch.mdc-switch--unselected:enabled:focus:not(:active) .mdc-switch__handle::after{background:#212121;background:var(--mdc-switch-unselected-focus-handle-color, #212121)}.mdc-switch.mdc-switch--unselected:enabled:active .mdc-switch__handle::after{background:#212121;background:var(--mdc-switch-unselected-pressed-handle-color, #212121)}.mdc-switch.mdc-switch--unselected:disabled .mdc-switch__handle::after{background:#424242;background:var(--mdc-switch-disabled-unselected-handle-color, #424242)}.mdc-switch .mdc-switch__handle::before{background:#fff;background:var(--mdc-switch-handle-surface-color, var(--mdc-theme-surface, #fff))}.mdc-switch:enabled .mdc-switch__shadow{--mdc-elevation-box-shadow-for-gss:0px 2px 1px -1px rgba(0, 0, 0, 0.2), 0px 1px 1px 0px rgba(0, 0, 0, 0.14), 0px 1px 3px 0px rgba(0, 0, 0, 0.12);box-shadow:0px 2px 1px -1px rgba(0, 0, 0, 0.2), 0px 1px 1px 0px rgba(0, 0, 0, 0.14), 0px 1px 3px 0px rgba(0, 0, 0, 0.12);box-shadow:var(--mdc-switch-handle-elevation, var(--mdc-elevation-box-shadow-for-gss))}.mdc-switch:disabled .mdc-switch__shadow{--mdc-elevation-box-shadow-for-gss:0px 0px 0px 0px rgba(0, 0, 0, 0.2), 0px 0px 0px 0px rgba(0, 0, 0, 0.14), 0px 0px 0px 0px rgba(0, 0, 0, 0.12);box-shadow:0px 0px 0px 0px rgba(0, 0, 0, 0.2), 0px 0px 0px 0px rgba(0, 0, 0, 0.14), 0px 0px 0px 0px rgba(0, 0, 0, 0.12);box-shadow:var(--mdc-switch-disabled-handle-elevation, var(--mdc-elevation-box-shadow-for-gss))}.mdc-switch .mdc-switch__focus-ring-wrapper,.mdc-switch .mdc-switch__handle{height:20px;height:var(--mdc-switch-handle-height, 20px)}.mdc-switch:disabled .mdc-switch__handle::after{opacity:0.38;opacity:var(--mdc-switch-disabled-handle-opacity, 0.38)}.mdc-switch .mdc-switch__handle{border-radius:10px;border-radius:var(--mdc-switch-handle-shape, 10px)}.mdc-switch .mdc-switch__handle{width:20px;width:var(--mdc-switch-handle-width, 20px)}.mdc-switch .mdc-switch__handle-track{width:calc(100% - 20px);width:calc(100% - var(--mdc-switch-handle-width, 20px))}.mdc-switch.mdc-switch--selected:enabled .mdc-switch__icon{fill:#fff;fill:var(--mdc-switch-selected-icon-color, var(--mdc-theme-on-primary, #fff))}.mdc-switch.mdc-switch--selected:disabled .mdc-switch__icon{fill:#fff;fill:var(--mdc-switch-disabled-selected-icon-color, var(--mdc-theme-on-primary, #fff))}.mdc-switch.mdc-switch--unselected:enabled .mdc-switch__icon{fill:#fff;fill:var(--mdc-switch-unselected-icon-color, var(--mdc-theme-on-primary, #fff))}.mdc-switch.mdc-switch--unselected:disabled .mdc-switch__icon{fill:#fff;fill:var(--mdc-switch-disabled-unselected-icon-color, var(--mdc-theme-on-primary, #fff))}.mdc-switch.mdc-switch--selected:disabled .mdc-switch__icons{opacity:0.38;opacity:var(--mdc-switch-disabled-selected-icon-opacity, 0.38)}.mdc-switch.mdc-switch--unselected:disabled .mdc-switch__icons{opacity:0.38;opacity:var(--mdc-switch-disabled-unselected-icon-opacity, 0.38)}.mdc-switch.mdc-switch--selected .mdc-switch__icon{width:18px;width:var(--mdc-switch-selected-icon-size, 18px);height:18px;height:var(--mdc-switch-selected-icon-size, 18px)}.mdc-switch.mdc-switch--unselected .mdc-switch__icon{width:18px;width:var(--mdc-switch-unselected-icon-size, 18px);height:18px;height:var(--mdc-switch-unselected-icon-size, 18px)}.mdc-switch .mdc-switch__ripple{height:48px;height:var(--mdc-switch-state-layer-size, 48px);width:48px;width:var(--mdc-switch-state-layer-size, 48px)}.mdc-switch .mdc-switch__track{height:14px;height:var(--mdc-switch-track-height, 14px)}.mdc-switch:disabled .mdc-switch__track{opacity:0.12;opacity:var(--mdc-switch-disabled-track-opacity, 0.12)}.mdc-switch:enabled .mdc-switch__track::after{background:#d7bbff;background:var(--mdc-switch-selected-track-color, #d7bbff)}.mdc-switch:enabled:hover:not(:focus):not(:active) .mdc-switch__track::after{background:#d7bbff;background:var(--mdc-switch-selected-hover-track-color, #d7bbff)}.mdc-switch:enabled:focus:not(:active) .mdc-switch__track::after{background:#d7bbff;background:var(--mdc-switch-selected-focus-track-color, #d7bbff)}.mdc-switch:enabled:active .mdc-switch__track::after{background:#d7bbff;background:var(--mdc-switch-selected-pressed-track-color, #d7bbff)}.mdc-switch:disabled .mdc-switch__track::after{background:#424242;background:var(--mdc-switch-disabled-selected-track-color, #424242)}.mdc-switch:enabled .mdc-switch__track::before{background:#e0e0e0;background:var(--mdc-switch-unselected-track-color, #e0e0e0)}.mdc-switch:enabled:hover:not(:focus):not(:active) .mdc-switch__track::before{background:#e0e0e0;background:var(--mdc-switch-unselected-hover-track-color, #e0e0e0)}.mdc-switch:enabled:focus:not(:active) .mdc-switch__track::before{background:#e0e0e0;background:var(--mdc-switch-unselected-focus-track-color, #e0e0e0)}.mdc-switch:enabled:active .mdc-switch__track::before{background:#e0e0e0;background:var(--mdc-switch-unselected-pressed-track-color, #e0e0e0)}.mdc-switch:disabled .mdc-switch__track::before{background:#424242;background:var(--mdc-switch-disabled-unselected-track-color, #424242)}.mdc-switch .mdc-switch__track{border-radius:7px;border-radius:var(--mdc-switch-track-shape, 7px)}.mdc-switch.mdc-switch--selected{--mdc-ripple-focus-state-layer-color:var(--mdc-switch-selected-focus-state-layer-color, var(--mdc-theme-primary, #6200ee));--mdc-ripple-focus-state-layer-opacity:var(--mdc-switch-selected-focus-state-layer-opacity, 0.12);--mdc-ripple-hover-state-layer-color:var(--mdc-switch-selected-hover-state-layer-color, var(--mdc-theme-primary, #6200ee));--mdc-ripple-hover-state-layer-opacity:var(--mdc-switch-selected-hover-state-layer-opacity, 0.04);--mdc-ripple-pressed-state-layer-color:var(--mdc-switch-selected-pressed-state-layer-color, var(--mdc-theme-primary, #6200ee));--mdc-ripple-pressed-state-layer-opacity:var(--mdc-switch-selected-pressed-state-layer-opacity, 0.1)}.mdc-switch.mdc-switch--selected:enabled:focus:not(:active){--mdc-ripple-hover-state-layer-color:var(--mdc-switch-selected-focus-state-layer-color, var(--mdc-theme-primary, #6200ee))}.mdc-switch.mdc-switch--selected:enabled:active{--mdc-ripple-hover-state-layer-color:var(--mdc-switch-selected-pressed-state-layer-color, var(--mdc-theme-primary, #6200ee))}.mdc-switch.mdc-switch--unselected{--mdc-ripple-focus-state-layer-color:var(--mdc-switch-unselected-focus-state-layer-color, #424242);--mdc-ripple-focus-state-layer-opacity:var(--mdc-switch-unselected-focus-state-layer-opacity, 0.12);--mdc-ripple-hover-state-layer-color:var(--mdc-switch-unselected-hover-state-layer-color, #424242);--mdc-ripple-hover-state-layer-opacity:var(--mdc-switch-unselected-hover-state-layer-opacity, 0.04);--mdc-ripple-pressed-state-layer-color:var(--mdc-switch-unselected-pressed-state-layer-color, #424242);--mdc-ripple-pressed-state-layer-opacity:var(--mdc-switch-unselected-pressed-state-layer-opacity, 0.1)}.mdc-switch.mdc-switch--unselected:enabled:focus:not(:active){--mdc-ripple-hover-state-layer-color:var(--mdc-switch-unselected-focus-state-layer-color, #424242)}.mdc-switch.mdc-switch--unselected:enabled:active{--mdc-ripple-hover-state-layer-color:var(--mdc-switch-unselected-pressed-state-layer-color, #424242)}@media screen and (forced-colors: active),(-ms-high-contrast: active){.mdc-switch:disabled .mdc-switch__handle::after{opacity:1;opacity:var(--mdc-switch-disabled-handle-opacity, 1)}.mdc-switch.mdc-switch--selected:enabled .mdc-switch__icon{fill:ButtonText;fill:var(--mdc-switch-selected-icon-color, ButtonText)}.mdc-switch.mdc-switch--selected:disabled .mdc-switch__icon{fill:GrayText;fill:var(--mdc-switch-disabled-selected-icon-color, GrayText)}.mdc-switch.mdc-switch--unselected:enabled .mdc-switch__icon{fill:ButtonText;fill:var(--mdc-switch-unselected-icon-color, ButtonText)}.mdc-switch.mdc-switch--unselected:disabled .mdc-switch__icon{fill:GrayText;fill:var(--mdc-switch-disabled-unselected-icon-color, GrayText)}.mdc-switch.mdc-switch--selected:disabled .mdc-switch__icons{opacity:1;opacity:var(--mdc-switch-disabled-selected-icon-opacity, 1)}.mdc-switch.mdc-switch--unselected:disabled .mdc-switch__icons{opacity:1;opacity:var(--mdc-switch-disabled-unselected-icon-opacity, 1)}.mdc-switch:disabled .mdc-switch__track{opacity:1;opacity:var(--mdc-switch-disabled-track-opacity, 1)}}`
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */;let ue=class extends he{};ue.styles=[_e],ue=a([v("mwc-switch")],ue),w("vaadin-checkbox",b`
    :host {
      color: var(--lumo-body-text-color);
      font-size: var(--lumo-font-size-m);
      font-family: var(--lumo-font-family);
      line-height: var(--lumo-line-height-s);
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      -webkit-tap-highlight-color: transparent;
      -webkit-user-select: none;
      -moz-user-select: none;
      user-select: none;
      cursor: default;
      outline: none;
      --_checkbox-size: var(--vaadin-checkbox-size, calc(var(--lumo-size-m) / 2));
    }

    :host([has-label]) ::slotted(label) {
      padding-block: var(--lumo-space-xs);
      padding-inline: var(--lumo-space-xs) var(--lumo-space-s);
    }

    [part='checkbox'] {
      width: var(--_checkbox-size);
      height: var(--_checkbox-size);
      margin: var(--lumo-space-xs);
      position: relative;
      border-radius: var(--lumo-border-radius-s);
      background-color: var(--lumo-contrast-20pct);
      transition: transform 0.2s cubic-bezier(0.12, 0.32, 0.54, 2), background-color 0.15s;
      cursor: var(--lumo-clickable-cursor);
      /* Default field border color */
      --_input-border-color: var(--vaadin-input-field-border-color, var(--lumo-contrast-50pct));
    }

    :host([indeterminate]),
    :host([checked]) {
      --vaadin-input-field-border-color: transparent;
    }

    :host([indeterminate]) [part='checkbox'],
    :host([checked]) [part='checkbox'] {
      background-color: var(--lumo-primary-color);
    }

    /* Checkmark */
    [part='checkbox']::after {
      pointer-events: none;
      font-family: 'lumo-icons';
      content: var(--lumo-icons-checkmark);
      color: var(--lumo-primary-contrast-color);
      font-size: calc(var(--_checkbox-size) + 2px);
      line-height: 1;
      position: absolute;
      top: -1px;
      left: -1px;
      contain: content;
      opacity: 0;
    }

    :host([checked]) [part='checkbox']::after {
      opacity: 1;
    }

    /* Indeterminate checkmark */
    :host([indeterminate]) [part='checkbox']::after {
      content: '';
      opacity: 1;
      top: 45%;
      height: 10%;
      left: 22%;
      right: 22%;
      width: auto;
      border: 0;
      background-color: var(--lumo-primary-contrast-color);
    }

    /* Focus ring */
    :host([focus-ring]) [part='checkbox'] {
      box-shadow: 0 0 0 1px var(--lumo-base-color), 0 0 0 3px var(--lumo-primary-color-50pct),
        inset 0 0 0 var(--_input-border-width, 0) var(--_input-border-color);
    }

    /* Disabled */
    :host([disabled]) {
      pointer-events: none;
      color: var(--lumo-disabled-text-color);
      --vaadin-input-field-border-color: var(--lumo-contrast-20pct);
    }

    :host([disabled]) ::slotted(label) {
      color: inherit;
    }

    :host([disabled]) [part='checkbox'] {
      background-color: var(--lumo-contrast-10pct);
    }

    :host([disabled]) [part='checkbox']::after {
      color: var(--lumo-contrast-30pct);
    }

    :host([indeterminate][disabled]) [part='checkbox']::after {
      background-color: var(--lumo-contrast-30pct);
    }

    /* RTL specific styles */
    :host([dir='rtl'][has-label]) ::slotted(label) {
      padding: var(--lumo-space-xs) var(--lumo-space-xs) var(--lumo-space-xs) var(--lumo-space-s);
    }

    /* Used for activation "halo" */
    [part='checkbox']::before {
      pointer-events: none;
      color: transparent;
      width: 100%;
      height: 100%;
      line-height: var(--_checkbox-size);
      border-radius: inherit;
      background-color: inherit;
      transform: scale(1.4);
      opacity: 0;
      transition: transform 0.1s, opacity 0.8s;
    }

    /* Hover */
    :host(:not([checked]):not([indeterminate]):not([disabled]):hover) [part='checkbox'] {
      background-color: var(--lumo-contrast-30pct);
    }

    /* Disable hover for touch devices */
    @media (pointer: coarse) {
      :host(:not([checked]):not([indeterminate]):not([disabled]):hover) [part='checkbox'] {
        background-color: var(--lumo-contrast-20pct);
      }
    }

    /* Active */
    :host([active]) [part='checkbox'] {
      transform: scale(0.9);
      transition-duration: 0.05s;
    }

    :host([active][checked]) [part='checkbox'] {
      transform: scale(1.1);
    }

    :host([active]:not([checked])) [part='checkbox']::before {
      transition-duration: 0.01s, 0.01s;
      transform: scale(0);
      opacity: 0.4;
    }
  `,{moduleId:"lumo-checkbox"});
/**
 * @license
 * Copyright (c) 2021 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const pe=C((e=>class extends(y(x(z(e)))){static get properties(){return{checked:{type:Boolean,value:!1,notify:!0,reflectToAttribute:!0}}}static get delegateProps(){return[...super.delegateProps,"checked"]}_onChange(e){const t=e.target;this._toggleChecked(t.checked),E(t)||t.focus()}_toggleChecked(e){this.checked=e}})),me=e=>class extends(k(pe(I(re(e))))){static get properties(){return{indeterminate:{type:Boolean,notify:!0,value:!1,reflectToAttribute:!0},name:{type:String,value:""}}}static get delegateProps(){return[...super.delegateProps,"indeterminate"]}static get delegateAttrs(){return[...super.delegateAttrs,"name"]}constructor(){super(),this._setType("checkbox"),this.value="on"}ready(){super.ready(),this.addController(new R(this,(e=>{this._setInputElement(e),this._setFocusElement(e),this.stateTarget=e,this.ariaTarget=e}))),this.addController(new S(this.inputElement,this._labelController))}_shouldSetActive(e){return"a"!==e.target.localName&&super._shouldSetActive(e)}_toggleChecked(e){this.indeterminate&&(this.indeterminate=!1),super._toggleChecked(e)}}
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
w("vaadin-checkbox",b`
  :host {
    display: inline-block;
  }

  :host([hidden]) {
    display: none !important;
  }

  :host([disabled]) {
    -webkit-tap-highlight-color: transparent;
  }

  .vaadin-checkbox-container {
    display: grid;
    grid-template-columns: auto 1fr;
    align-items: baseline;
  }

  [part='checkbox'],
  ::slotted(input),
  ::slotted(label) {
    grid-row: 1;
  }

  [part='checkbox'],
  ::slotted(input) {
    grid-column: 1;
  }

  [part='checkbox'] {
    width: var(--vaadin-checkbox-size, 1em);
    height: var(--vaadin-checkbox-size, 1em);
    --_input-border-width: var(--vaadin-input-field-border-width, 0);
    --_input-border-color: var(--vaadin-input-field-border-color, transparent);
    box-shadow: inset 0 0 0 var(--_input-border-width, 0) var(--_input-border-color);
  }

  [part='checkbox']::before {
    display: block;
    content: '\\202F';
    line-height: var(--vaadin-checkbox-size, 1em);
    contain: paint;
  }

  /* visually hidden */
  ::slotted(input) {
    opacity: 0;
    cursor: inherit;
    margin: 0;
    align-self: stretch;
    -webkit-appearance: none;
  }

  @media (forced-colors: active) {
    [part='checkbox'] {
      outline: 1px solid;
      outline-offset: -1px;
    }

    :host([disabled]) [part='checkbox'],
    :host([disabled]) [part='checkbox']::after {
      outline-color: GrayText;
    }

    :host(:is([checked], [indeterminate])) [part='checkbox']::after {
      outline: 1px solid;
      outline-offset: -1px;
      border-radius: inherit;
    }

    :host([focused]) [part='checkbox'],
    :host([focused]) [part='checkbox']::after {
      outline-width: 2px;
    }
  }
`,{moduleId:"vaadin-checkbox-styles"});class ge extends(me(T($(P)))){static get is(){return"vaadin-checkbox"}static get template(){return A`
      <div class="vaadin-checkbox-container">
        <div part="checkbox" aria-hidden="true"></div>
        <slot name="input"></slot>
        <slot name="label"></slot>
      </div>
      <slot name="tooltip"></slot>
    `}ready(){super.ready(),this._tooltipController=new F(this),this.addController(this._tooltipController)}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
function fe(e){return e.__cells||Array.from(e.querySelectorAll('[part~="cell"]:not([part~="details-cell"])'))}function be(e,t){[...e.children].forEach(t)}function ve(e,t){fe(e).forEach(t),e.__detailsCell&&t(e.__detailsCell)}function we(e,t,r){let i=1;e.forEach((e=>{i%10==0&&(i+=1),e._order=r+i*t,i+=1}))}function Ce(e,t,r){switch(typeof r){case"boolean":e.toggleAttribute(t,r);break;case"string":e.setAttribute(t,r);break;default:e.removeAttribute(t)}}function ye(e,t,r){t||""===t?D(e,"part",r):O(e,"part",r)}function xe(e,t,r){e.forEach((e=>{ye(e,r,t)}))}function ze(e,t){const r=fe(e);Object.entries(t).forEach((([t,i])=>{Ce(e,t,i);const o=`${t}-row`;ye(e,i,o),xe(r,`${o}-cell`,i)}))}function Ee(e,t){const r=fe(e);Object.entries(t).forEach((([t,i])=>{const o=e.getAttribute(t);if(Ce(e,t,i),o){const i=`${t}-${o}-row`;ye(e,!1,i),xe(r,`${i}-cell`,!1)}if(i){const o=`${t}-${i}-row`;ye(e,i,o),xe(r,`${o}-cell`,i)}}))}function ke(e,t,r,i,o){Ce(e,t,r),o&&ye(e,!1,o),ye(e,r,i||`${t}-cell`)}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */customElements.define(ge.is,ge),w("vaadin-grid",b`
    :host {
      font-family: var(--lumo-font-family);
      font-size: var(--lumo-font-size-m);
      line-height: var(--lumo-line-height-s);
      color: var(--lumo-body-text-color);
      background-color: var(--lumo-base-color);
      box-sizing: border-box;
      -webkit-text-size-adjust: 100%;
      -webkit-tap-highlight-color: transparent;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;

      /* For internal use only */
      --_lumo-grid-border-color: var(--lumo-contrast-20pct);
      --_lumo-grid-secondary-border-color: var(--lumo-contrast-10pct);
      --_lumo-grid-border-width: 1px;
      --_lumo-grid-selected-row-color: var(--lumo-primary-color-10pct);
    }

    /* No (outer) border */

    :host(:not([theme~='no-border'])) {
      border: var(--_lumo-grid-border-width) solid var(--_lumo-grid-border-color);
    }

    :host([disabled]) {
      opacity: 0.7;
    }

    /* Cell styles */

    [part~='cell'] {
      min-height: var(--lumo-size-m);
      background-color: var(--lumo-base-color);
    }

    [part~='cell'] ::slotted(vaadin-grid-cell-content) {
      cursor: default;
      padding: var(--lumo-space-xs) var(--lumo-space-m);
    }

    /* Apply row borders by default and introduce the "no-row-borders" variant */
    :host(:not([theme~='no-row-borders'])) [part~='cell']:not([part~='details-cell']) {
      border-top: var(--_lumo-grid-border-width) solid var(--_lumo-grid-secondary-border-color);
    }

    /* Hide first body row top border */
    :host(:not([theme~='no-row-borders'])) [part~='first-row'] [part~='cell']:not([part~='details-cell']) {
      border-top: 0;
      min-height: calc(var(--lumo-size-m) - var(--_lumo-grid-border-width));
    }

    /* Focus-ring */

    [part~='row'] {
      position: relative;
    }

    [part~='row']:focus,
    [part~='focused-cell']:focus {
      outline: none;
    }

    :host([navigating]) [part~='row']:focus::before,
    :host([navigating]) [part~='focused-cell']:focus::before {
      content: '';
      position: absolute;
      top: 0;
      right: 0;
      bottom: 0;
      left: 0;
      pointer-events: none;
      box-shadow: inset 0 0 0 2px var(--lumo-primary-color-50pct);
    }

    :host([navigating]) [part~='row']:focus::before {
      transform: translateX(calc(-1 * var(--_grid-horizontal-scroll-position)));
      z-index: 3;
    }

    /* Drag and Drop styles */
    :host([dragover])::after {
      content: '';
      position: absolute;
      z-index: 100;
      top: 0;
      right: 0;
      bottom: 0;
      left: 0;
      pointer-events: none;
      box-shadow: inset 0 0 0 2px var(--lumo-primary-color-50pct);
    }

    [part~='row'][dragover] {
      z-index: 100 !important;
    }

    [part~='row'][dragover] [part~='cell'] {
      overflow: visible;
    }

    [part~='row'][dragover] [part~='cell']::after {
      content: '';
      position: absolute;
      top: 0;
      right: 0;
      bottom: 0;
      left: 0;
      height: calc(var(--_lumo-grid-border-width) + 2px);
      pointer-events: none;
      background: var(--lumo-primary-color-50pct);
    }

    [part~='row'][dragover] [part~='cell'][last-frozen]::after {
      right: -1px;
    }

    :host([theme~='no-row-borders']) [dragover] [part~='cell']::after {
      height: 2px;
    }

    [part~='row'][dragover='below'] [part~='cell']::after {
      top: 100%;
      bottom: auto;
      margin-top: -1px;
    }

    :host([all-rows-visible]) [part~='last-row'][dragover='below'] [part~='cell']::after {
      height: 1px;
    }

    [part~='row'][dragover='above'] [part~='cell']::after {
      top: auto;
      bottom: 100%;
      margin-bottom: -1px;
    }

    [part~='row'][details-opened][dragover='below'] [part~='cell']:not([part~='details-cell'])::after,
    [part~='row'][details-opened][dragover='above'] [part~='details-cell']::after {
      display: none;
    }

    [part~='row'][dragover][dragover='on-top'] [part~='cell']::after {
      height: 100%;
      opacity: 0.5;
    }

    [part~='row'][dragstart] [part~='cell'] {
      border: none !important;
      box-shadow: none !important;
    }

    [part~='row'][dragstart] [part~='cell'][last-column] {
      border-radius: 0 var(--lumo-border-radius-s) var(--lumo-border-radius-s) 0;
    }

    [part~='row'][dragstart] [part~='cell'][first-column] {
      border-radius: var(--lumo-border-radius-s) 0 0 var(--lumo-border-radius-s);
    }

    #scroller [part~='row'][dragstart]:not([dragstart=''])::after {
      display: block;
      position: absolute;
      left: var(--_grid-drag-start-x);
      top: var(--_grid-drag-start-y);
      z-index: 100;
      content: attr(dragstart);
      align-items: center;
      justify-content: center;
      box-sizing: border-box;
      padding: calc(var(--lumo-space-xs) * 0.8);
      color: var(--lumo-error-contrast-color);
      background-color: var(--lumo-error-color);
      border-radius: var(--lumo-border-radius-m);
      font-family: var(--lumo-font-family);
      font-size: var(--lumo-font-size-xxs);
      line-height: 1;
      font-weight: 500;
      text-transform: initial;
      letter-spacing: initial;
      min-width: calc(var(--lumo-size-s) * 0.7);
      text-align: center;
    }

    /* Headers and footers */

    [part~='header-cell'] ::slotted(vaadin-grid-cell-content),
    [part~='footer-cell'] ::slotted(vaadin-grid-cell-content),
    [part~='reorder-ghost'] {
      font-size: var(--lumo-font-size-s);
      font-weight: 500;
    }

    [part~='footer-cell'] ::slotted(vaadin-grid-cell-content) {
      font-weight: 400;
    }

    [part~='row']:only-child [part~='header-cell'] {
      min-height: var(--lumo-size-xl);
    }

    /* Header borders */

    /* Hide first header row top border */
    :host(:not([theme~='no-row-borders'])) [part~='row']:first-child [part~='header-cell'] {
      border-top: 0;
    }

    [part~='row']:last-child [part~='header-cell'] {
      border-bottom: var(--_lumo-grid-border-width) solid transparent;
    }

    :host(:not([theme~='no-row-borders'])) [part~='row']:last-child [part~='header-cell'] {
      border-bottom-color: var(--_lumo-grid-secondary-border-color);
    }

    /* Overflow uses a stronger border color */
    :host([overflow~='top']) [part~='row']:last-child [part~='header-cell'] {
      border-bottom-color: var(--_lumo-grid-border-color);
    }

    /* Footer borders */

    [part~='row']:first-child [part~='footer-cell'] {
      border-top: var(--_lumo-grid-border-width) solid transparent;
    }

    :host(:not([theme~='no-row-borders'])) [part~='row']:first-child [part~='footer-cell'] {
      border-top-color: var(--_lumo-grid-secondary-border-color);
    }

    /* Overflow uses a stronger border color */
    :host([overflow~='bottom']) [part~='row']:first-child [part~='footer-cell'] {
      border-top-color: var(--_lumo-grid-border-color);
    }

    /* Column reordering */

    :host([reordering]) [part~='cell'] {
      background: linear-gradient(var(--lumo-shade-20pct), var(--lumo-shade-20pct)) var(--lumo-base-color);
    }

    :host([reordering]) [part~='cell'][reorder-status='allowed'] {
      background: var(--lumo-base-color);
    }

    :host([reordering]) [part~='cell'][reorder-status='dragging'] {
      background: linear-gradient(var(--lumo-contrast-5pct), var(--lumo-contrast-5pct)) var(--lumo-base-color);
    }

    [part~='reorder-ghost'] {
      opacity: 0.85;
      box-shadow: var(--lumo-box-shadow-s);
      /* TODO Use the same styles as for the cell element (reorder-ghost copies styles from the cell element) */
      padding: var(--lumo-space-s) var(--lumo-space-m) !important;
    }

    /* Column resizing */

    [part='resize-handle'] {
      width: 3px;
      background-color: var(--lumo-primary-color-50pct);
      opacity: 0;
      transition: opacity 0.2s;
    }

    :host(:not([reordering])) *:not([column-resizing]) [part~='cell']:hover [part='resize-handle'],
    [part='resize-handle']:active {
      opacity: 1;
      transition-delay: 0.15s;
    }

    /* Column borders */

    :host([theme~='column-borders']) [part~='cell']:not([last-column]):not([part~='details-cell']) {
      border-right: var(--_lumo-grid-border-width) solid var(--_lumo-grid-secondary-border-color);
    }

    /* Frozen columns */

    [last-frozen] {
      border-right: var(--_lumo-grid-border-width) solid transparent;
      overflow: hidden;
    }

    :host([overflow~='start']) [part~='cell'][last-frozen]:not([part~='details-cell']) {
      border-right-color: var(--_lumo-grid-border-color);
    }

    [first-frozen-to-end] {
      border-left: var(--_lumo-grid-border-width) solid transparent;
    }

    :host([overflow~='end']) [part~='cell'][first-frozen-to-end]:not([part~='details-cell']) {
      border-left-color: var(--_lumo-grid-border-color);
    }

    /* Row stripes */

    :host([theme~='row-stripes']) [part~='even-row'] [part~='body-cell'],
    :host([theme~='row-stripes']) [part~='even-row'] [part~='details-cell'] {
      background-image: linear-gradient(var(--lumo-contrast-5pct), var(--lumo-contrast-5pct));
      background-repeat: repeat-x;
    }

    /* Selected row */

    /* Raise the selected rows above unselected rows (so that box-shadow can cover unselected rows) */
    :host(:not([reordering])) [part~='row'][selected] {
      z-index: 1;
    }

    :host(:not([reordering])) [part~='row'][selected] [part~='body-cell']:not([part~='details-cell']) {
      background-image: linear-gradient(var(--_lumo-grid-selected-row-color), var(--_lumo-grid-selected-row-color));
      background-repeat: repeat;
    }

    /* Cover the border of an unselected row */
    :host(:not([theme~='no-row-borders'])) [part~='row'][selected] [part~='cell']:not([part~='details-cell']) {
      box-shadow: 0 var(--_lumo-grid-border-width) 0 0 var(--_lumo-grid-selected-row-color);
    }

    /* Compact */

    :host([theme~='compact']) [part~='row']:only-child [part~='header-cell'] {
      min-height: var(--lumo-size-m);
    }

    :host([theme~='compact']) [part~='cell'] {
      min-height: var(--lumo-size-s);
    }

    :host([theme~='compact']) [part~='first-row'] [part~='cell']:not([part~='details-cell']) {
      min-height: calc(var(--lumo-size-s) - var(--_lumo-grid-border-width));
    }

    :host([theme~='compact']) [part~='cell'] ::slotted(vaadin-grid-cell-content) {
      padding: var(--lumo-space-xs) var(--lumo-space-s);
    }

    /* Wrap cell contents */

    :host([theme~='wrap-cell-content']) [part~='cell'] ::slotted(vaadin-grid-cell-content) {
      white-space: normal;
    }

    /* RTL specific styles */

    :host([dir='rtl']) [part~='row'][dragstart] [part~='cell'][last-column] {
      border-radius: var(--lumo-border-radius-s) 0 0 var(--lumo-border-radius-s);
    }

    :host([dir='rtl']) [part~='row'][dragstart] [part~='cell'][first-column] {
      border-radius: 0 var(--lumo-border-radius-s) var(--lumo-border-radius-s) 0;
    }

    :host([dir='rtl'][theme~='column-borders']) [part~='cell']:not([last-column]):not([part~='details-cell']) {
      border-right: none;
      border-left: var(--_lumo-grid-border-width) solid var(--_lumo-grid-secondary-border-color);
    }

    :host([dir='rtl']) [last-frozen] {
      border-right: none;
      border-left: var(--_lumo-grid-border-width) solid transparent;
    }

    :host([dir='rtl']) [first-frozen-to-end] {
      border-left: none;
      border-right: var(--_lumo-grid-border-width) solid transparent;
    }

    :host([dir='rtl'][overflow~='start']) [part~='cell'][last-frozen]:not([part~='details-cell']) {
      border-left-color: var(--_lumo-grid-border-color);
    }

    :host([dir='rtl'][overflow~='end']) [part~='cell'][first-frozen-to-end]:not([part~='details-cell']) {
      border-right-color: var(--_lumo-grid-border-color);
    }
  `,{moduleId:"lumo-grid"});const Ie=e=>class extends e{static get properties(){return{resizable:{type:Boolean,value(){if("vaadin-grid-column-group"===this.localName)return;const e=this.parentNode;return e&&"vaadin-grid-column-group"===e.localName&&e.resizable||!1}},frozen:{type:Boolean,value:!1},frozenToEnd:{type:Boolean,value:!1},hidden:{type:Boolean,value:!1},header:{type:String},textAlign:{type:String},_lastFrozen:{type:Boolean,value:!1},_bodyContentHidden:{type:Boolean,value:!1},_firstFrozenToEnd:{type:Boolean,value:!1},_order:Number,_reorderStatus:Boolean,_emptyCells:Array,_headerCell:Object,_footerCell:Object,_grid:Object,__initialized:{type:Boolean,value:!0},headerRenderer:Function,_headerRenderer:{type:Function,computed:"_computeHeaderRenderer(headerRenderer, header, __initialized)"},footerRenderer:Function,_footerRenderer:{type:Function,computed:"_computeFooterRenderer(footerRenderer, __initialized)"},__gridColumnElement:{type:Boolean,value:!0}}}static get observers(){return["_widthChanged(width, _headerCell, _footerCell, _cells.*)","_frozenChanged(frozen, _headerCell, _footerCell, _cells.*)","_frozenToEndChanged(frozenToEnd, _headerCell, _footerCell, _cells.*)","_flexGrowChanged(flexGrow, _headerCell, _footerCell, _cells.*)","_textAlignChanged(textAlign, _cells.*, _headerCell, _footerCell)","_orderChanged(_order, _headerCell, _footerCell, _cells.*)","_lastFrozenChanged(_lastFrozen)","_firstFrozenToEndChanged(_firstFrozenToEnd)","_onRendererOrBindingChanged(_renderer, _cells, _bodyContentHidden, _cells.*, path)","_onHeaderRendererOrBindingChanged(_headerRenderer, _headerCell, path, header)","_onFooterRendererOrBindingChanged(_footerRenderer, _footerCell)","_resizableChanged(resizable, _headerCell)","_reorderStatusChanged(_reorderStatus, _headerCell, _footerCell, _cells.*)","_hiddenChanged(hidden, _headerCell, _footerCell, _cells.*)"]}get _grid(){return this._gridValue||(this._gridValue=this._findHostGrid()),this._gridValue}get _allCells(){return[].concat(this._cells||[]).concat(this._emptyCells||[]).concat(this._headerCell).concat(this._footerCell).filter((e=>e))}connectedCallback(){super.connectedCallback(),requestAnimationFrame((()=>{this._grid&&this._allCells.forEach((e=>{e._content.parentNode||this._grid.appendChild(e._content)}))}))}disconnectedCallback(){super.disconnectedCallback(),requestAnimationFrame((()=>{this._grid||this._allCells.forEach((e=>{e._content.parentNode&&e._content.parentNode.removeChild(e._content)}))})),this._gridValue=void 0}ready(){super.ready(),L(this)}_findHostGrid(){let e=this;for(;e&&!/^vaadin.*grid(-pro)?$/u.test(e.localName);)e=e.assignedSlot?e.assignedSlot.parentNode:e.parentNode;return e||void 0}_renderHeaderAndFooter(){this._renderHeaderCellContent(this._headerRenderer,this._headerCell),this._renderFooterCellContent(this._footerRenderer,this._footerCell)}_flexGrowChanged(e){this.parentElement&&this.parentElement._columnPropChanged&&this.parentElement._columnPropChanged("flexGrow"),this._allCells.forEach((t=>{t.style.flexGrow=e}))}_orderChanged(e){this._allCells.forEach((t=>{t.style.order=e}))}_widthChanged(e){this.parentElement&&this.parentElement._columnPropChanged&&this.parentElement._columnPropChanged("width"),this._allCells.forEach((t=>{t.style.width=e}))}_frozenChanged(e){this.parentElement&&this.parentElement._columnPropChanged&&this.parentElement._columnPropChanged("frozen",e),this._allCells.forEach((t=>{ke(t,"frozen",e)})),this._grid&&this._grid._frozenCellsChanged&&this._grid._frozenCellsChanged()}_frozenToEndChanged(e){this.parentElement&&this.parentElement._columnPropChanged&&this.parentElement._columnPropChanged("frozenToEnd",e),this._allCells.forEach((t=>{this._grid&&t.parentElement===this._grid.$.sizer||ke(t,"frozen-to-end",e)})),this._grid&&this._grid._frozenCellsChanged&&this._grid._frozenCellsChanged()}_lastFrozenChanged(e){this._allCells.forEach((t=>{ke(t,"last-frozen",e)})),this.parentElement&&this.parentElement._columnPropChanged&&(this.parentElement._lastFrozen=e)}_firstFrozenToEndChanged(e){this._allCells.forEach((t=>{this._grid&&t.parentElement===this._grid.$.sizer||ke(t,"first-frozen-to-end",e)})),this.parentElement&&this.parentElement._columnPropChanged&&(this.parentElement._firstFrozenToEnd=e)}_generateHeader(e){return e.substr(e.lastIndexOf(".")+1).replace(/([A-Z])/gu,"-$1").toLowerCase().replace(/-/gu," ").replace(/^./u,(e=>e.toUpperCase()))}_reorderStatusChanged(e){const t=this.__previousReorderStatus,r=t?`reorder-${t}-cell`:"",i=`reorder-${e}-cell`;this._allCells.forEach((t=>{ke(t,"reorder-status",e,i,r)})),this.__previousReorderStatus=e}_resizableChanged(e,t){void 0!==e&&void 0!==t&&t&&[t].concat(this._emptyCells).forEach((t=>{if(t){const r=t.querySelector('[part~="resize-handle"]');if(r&&t.removeChild(r),e){const e=document.createElement("div");e.setAttribute("part","resize-handle"),t.appendChild(e)}}}))}_textAlignChanged(e){if(void 0===e)return;if(-1===["start","end","center"].indexOf(e))return void console.warn('textAlign can only be set as "start", "end" or "center"');let t;"ltr"===getComputedStyle(this._grid).direction?"start"===e?t="left":"end"===e&&(t="right"):"start"===e?t="right":"end"===e&&(t="left"),this._allCells.forEach((r=>{r._content.style.textAlign=e,getComputedStyle(r._content).textAlign!==e&&(r._content.style.textAlign=t)}))}_hiddenChanged(e){this.parentElement&&this.parentElement._columnPropChanged&&this.parentElement._columnPropChanged("hidden",e),!!e!=!!this._previousHidden&&this._grid&&(!0===e&&this._allCells.forEach((e=>{e._content.parentNode&&e._content.parentNode.removeChild(e._content)})),this._grid._debouncerHiddenChanged=H.debounce(this._grid._debouncerHiddenChanged,N,(()=>{this._grid&&this._grid._renderColumnTree&&this._grid._renderColumnTree(this._grid._columnTree)})),this._grid._debounceUpdateFrozenColumn&&this._grid._debounceUpdateFrozenColumn(),this._grid._resetKeyboardNavigation&&this._grid._resetKeyboardNavigation()),this._previousHidden=e}_runRenderer(e,t,r){const i=[t._content,this];r&&r.item&&i.push(r),e.apply(this,i)}__renderCellsContent(e,t){!this.hidden&&this._grid&&t.forEach((t=>{if(!t.parentElement)return;const r=this._grid.__getRowModel(t.parentElement);e&&(t._renderer!==e&&this._clearCellContent(t),t._renderer=e,(r.item||e===this._headerRenderer||e===this._footerRenderer)&&this._runRenderer(e,t,r))}))}_clearCellContent(e){e._content.innerHTML="",delete e._content._$litPart$}_renderHeaderCellContent(e,t){t&&e&&(this.__renderCellsContent(e,[t]),this._grid&&t.parentElement&&this._grid.__debounceUpdateHeaderFooterRowVisibility(t.parentElement))}_onHeaderRendererOrBindingChanged(e,t,...r){this._renderHeaderCellContent(e,t)}_renderBodyCellsContent(e,t){t&&e&&this.__renderCellsContent(e,t)}_onRendererOrBindingChanged(e,t,...r){this._renderBodyCellsContent(e,t)}_renderFooterCellContent(e,t){t&&e&&(this.__renderCellsContent(e,[t]),this._grid&&t.parentElement&&this._grid.__debounceUpdateHeaderFooterRowVisibility(t.parentElement))}_onFooterRendererOrBindingChanged(e,t){this._renderFooterCellContent(e,t)}__setTextContent(e,t){e.textContent!==t&&(e.textContent=t)}__textHeaderRenderer(){this.__setTextContent(this._headerCell._content,this.header)}_defaultHeaderRenderer(){this.path&&this.__setTextContent(this._headerCell._content,this._generateHeader(this.path))}_defaultRenderer(e,t,{item:r}){this.path&&this.__setTextContent(e,this.get(this.path,r))}_defaultFooterRenderer(){}_computeHeaderRenderer(e,t){return e||(null!=t?this.__textHeaderRenderer:this._defaultHeaderRenderer)}_computeRenderer(e){return e||this._defaultRenderer}_computeFooterRenderer(e){return e||this._defaultFooterRenderer}};class Re extends(Ie(B(P))){static get is(){return"vaadin-grid-column"}static get properties(){return{width:{type:String,value:"100px"},flexGrow:{type:Number,value:1},renderer:Function,_renderer:{type:Function,computed:"_computeRenderer(renderer, __initialized)"},path:{type:String},autoWidth:{type:Boolean,value:!1},_focusButtonMode:{type:Boolean,value:!1},_cells:Array}}}customElements.define(Re.is,Re),
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
w("vaadin-grid",b`
    @keyframes vaadin-grid-appear {
      to {
        opacity: 1;
      }
    }

    :host {
      display: flex;
      flex-direction: column;
      animation: 1ms vaadin-grid-appear;
      height: 400px;
      flex: 1 1 auto;
      align-self: stretch;
      position: relative;
    }

    :host([hidden]) {
      display: none !important;
    }

    :host([disabled]) {
      pointer-events: none;
    }

    #scroller {
      display: flex;
      flex-direction: column;
      min-height: 100%;
      transform: translateY(0);
      width: auto;
      height: auto;
      position: absolute;
      top: 0;
      right: 0;
      bottom: 0;
      left: 0;
    }

    :host([all-rows-visible]) {
      height: auto;
      align-self: flex-start;
      flex-grow: 0;
      width: 100%;
    }

    :host([all-rows-visible]) #scroller {
      width: 100%;
      height: 100%;
      position: relative;
    }

    :host([all-rows-visible]) #items {
      min-height: 1px;
    }

    #table {
      display: flex;
      flex-direction: column;
      width: 100%;
      height: 100%;
      overflow: auto;
      position: relative;
      outline: none;
      /* Workaround for a Desktop Safari bug: new stacking context here prevents the scrollbar from getting hidden */
      z-index: 0;
    }

    #header,
    #footer {
      display: block;
      position: -webkit-sticky;
      position: sticky;
      left: 0;
      overflow: visible;
      width: 100%;
      z-index: 1;
    }

    #header {
      top: 0;
    }

    th {
      text-align: inherit;
    }

    /* Safari doesn't work with "inherit" */
    [safari] th {
      text-align: initial;
    }

    #footer {
      bottom: 0;
    }

    #items {
      flex-grow: 1;
      flex-shrink: 0;
      display: block;
      position: -webkit-sticky;
      position: sticky;
      width: 100%;
      left: 0;
      overflow: visible;
    }

    [part~='row'] {
      display: flex;
      width: 100%;
      box-sizing: border-box;
      margin: 0;
    }

    [part~='row'][loading] [part~='body-cell'] ::slotted(vaadin-grid-cell-content) {
      visibility: hidden;
    }

    [column-rendering='lazy'] [part~='body-cell']:not([frozen]):not([frozen-to-end]) {
      transform: translateX(var(--_grid-lazy-columns-start));
    }

    #items [part~='row'] {
      position: absolute;
    }

    #items [part~='row']:empty {
      height: 100%;
    }

    [part~='cell']:not([part~='details-cell']) {
      flex-shrink: 0;
      flex-grow: 1;
      box-sizing: border-box;
      display: flex;
      width: 100%;
      position: relative;
      align-items: center;
      padding: 0;
      white-space: nowrap;
    }

    [part~='cell'] > [tabindex] {
      display: flex;
      align-items: inherit;
      outline: none;
      position: absolute;
      top: 0;
      bottom: 0;
      left: 0;
      right: 0;
    }

    [part~='details-cell'] {
      position: absolute;
      bottom: 0;
      width: 100%;
      box-sizing: border-box;
      padding: 0;
    }

    [part~='cell'] ::slotted(vaadin-grid-cell-content) {
      display: block;
      width: 100%;
      box-sizing: border-box;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    [hidden] {
      display: none !important;
    }

    [frozen],
    [frozen-to-end] {
      z-index: 2;
      will-change: transform;
    }

    [no-scrollbars][safari] #table,
    [no-scrollbars][firefox] #table {
      overflow: hidden;
    }

    /* Reordering styles */
    :host([reordering]) [part~='cell'] ::slotted(vaadin-grid-cell-content),
    :host([reordering]) [part~='resize-handle'],
    #scroller[no-content-pointer-events] [part~='cell'] ::slotted(vaadin-grid-cell-content) {
      pointer-events: none;
    }

    [part~='reorder-ghost'] {
      visibility: hidden;
      position: fixed;
      pointer-events: none;
      opacity: 0.5;

      /* Prevent overflowing the grid in Firefox */
      top: 0;
      left: 0;
    }

    :host([reordering]) {
      -moz-user-select: none;
      -webkit-user-select: none;
      user-select: none;
    }

    /* Resizing styles */
    [part~='resize-handle'] {
      position: absolute;
      top: 0;
      right: 0;
      height: 100%;
      cursor: col-resize;
      z-index: 1;
    }

    [part~='resize-handle']::before {
      position: absolute;
      content: '';
      height: 100%;
      width: 35px;
      transform: translateX(-50%);
    }

    [last-column] [part~='resize-handle']::before,
    [last-frozen] [part~='resize-handle']::before {
      width: 18px;
      transform: none;
      right: 0;
    }

    [frozen-to-end] [part~='resize-handle'] {
      left: 0;
      right: auto;
    }

    [frozen-to-end] [part~='resize-handle']::before {
      left: 0;
      right: auto;
    }

    [first-frozen-to-end] [part~='resize-handle']::before {
      width: 18px;
      transform: none;
    }

    [first-frozen-to-end] {
      margin-inline-start: auto;
    }

    /* Hide resize handle if scrolled to end */
    :host(:not([overflow~='end'])) [first-frozen-to-end] [part~='resize-handle'] {
      display: none;
    }

    #scroller[column-resizing] {
      -ms-user-select: none;
      -moz-user-select: none;
      -webkit-user-select: none;
      user-select: none;
    }

    /* Sizer styles */
    #sizer {
      display: flex;
      position: absolute;
      visibility: hidden;
    }

    #sizer [part~='details-cell'] {
      display: none !important;
    }

    #sizer [part~='cell'][hidden] {
      display: none !important;
    }

    #sizer [part~='cell'] {
      display: block;
      flex-shrink: 0;
      line-height: 0;
      height: 0 !important;
      min-height: 0 !important;
      max-height: 0 !important;
      padding: 0 !important;
      border: none !important;
    }

    #sizer [part~='cell']::before {
      content: '-';
    }

    #sizer [part~='cell'] ::slotted(vaadin-grid-cell-content) {
      display: none !important;
    }

    /* RTL specific styles */

    :host([dir='rtl']) #items,
    :host([dir='rtl']) #header,
    :host([dir='rtl']) #footer {
      left: auto;
    }

    :host([dir='rtl']) [part~='reorder-ghost'] {
      left: auto;
      right: 0;
    }

    :host([dir='rtl']) [part~='resize-handle'] {
      left: 0;
      right: auto;
    }

    :host([dir='rtl']) [part~='resize-handle']::before {
      transform: translateX(50%);
    }

    :host([dir='rtl']) [last-column] [part~='resize-handle']::before,
    :host([dir='rtl']) [last-frozen] [part~='resize-handle']::before {
      left: 0;
      right: auto;
    }

    :host([dir='rtl']) [frozen-to-end] [part~='resize-handle'] {
      right: 0;
      left: auto;
    }

    :host([dir='rtl']) [frozen-to-end] [part~='resize-handle']::before {
      right: 0;
      left: auto;
    }

    @media (forced-colors: active) {
      [part~='selected-row'] [part~='first-column-cell']::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        bottom: 0;
        border: 2px solid;
      }

      [part~='focused-cell']::before {
        outline: 2px solid !important;
        outline-offset: -1px;
      }
    }
  `,{moduleId:"vaadin-grid-styles"});
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const Se=e=>class extends e{static get observers(){return["_a11yUpdateGridSize(size, _columnTree, _columnTree.*)"]}_a11yGetHeaderRowCount(e){return e.filter((e=>e.some((e=>e.headerRenderer||e.path||e.header)))).length}_a11yGetFooterRowCount(e){return e.filter((e=>e.some((e=>e.headerRenderer)))).length}_a11yUpdateGridSize(e,t){if(void 0===e||void 0===t)return;const r=t[t.length-1];this.$.table.setAttribute("aria-rowcount",e+this._a11yGetHeaderRowCount(t)+this._a11yGetFooterRowCount(t)),this.$.table.setAttribute("aria-colcount",r&&r.length||0),this._a11yUpdateHeaderRows(),this._a11yUpdateFooterRows()}_a11yUpdateHeaderRows(){be(this.$.header,((e,t)=>{e.setAttribute("aria-rowindex",t+1)}))}_a11yUpdateFooterRows(){be(this.$.footer,((e,t)=>{e.setAttribute("aria-rowindex",this._a11yGetHeaderRowCount(this._columnTree)+this.size+t+1)}))}_a11yUpdateRowRowindex(e,t){e.setAttribute("aria-rowindex",t+this._a11yGetHeaderRowCount(this._columnTree)+1)}_a11yUpdateRowSelected(e,t){e.setAttribute("aria-selected",Boolean(t)),ve(e,(e=>{e.setAttribute("aria-selected",Boolean(t))}))}_a11yUpdateRowExpanded(e){this.__isRowExpandable(e)?e.setAttribute("aria-expanded","false"):this.__isRowCollapsible(e)?e.setAttribute("aria-expanded","true"):e.removeAttribute("aria-expanded")}_a11yUpdateRowLevel(e,t){t>0||this.__isRowCollapsible(e)||this.__isRowExpandable(e)?e.setAttribute("aria-level",t+1):e.removeAttribute("aria-level")}_a11ySetRowDetailsCell(e,t){ve(e,(e=>{e!==t&&e.setAttribute("aria-controls",t.id)}))}_a11yUpdateCellColspan(e,t){e.setAttribute("aria-colspan",Number(t))}_a11yUpdateSorters(){Array.from(this.querySelectorAll("vaadin-grid-sorter")).forEach((e=>{let t=e.parentNode;for(;t&&"vaadin-grid-cell-content"!==t.localName;)t=t.parentNode;if(t&&t.assignedSlot){t.assignedSlot.parentNode.setAttribute("aria-sort",{asc:"ascending",desc:"descending"}[String(e.direction)]||"none")}}))}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,Ae=e=>{if(!e.parentNode)return!1;const t=Array.from(e.parentNode.querySelectorAll("[tabindex], button, input, select, textarea, object, iframe, a[href], area[href]")).filter((e=>{const t=e.getAttribute("part");return!(t&&t.includes("body-cell"))})).includes(e);return!e.disabled&&t&&e.offsetParent&&"hidden"!==getComputedStyle(e).visibility},Fe=e=>class extends e{static get properties(){return{activeItem:{type:Object,notify:!0,value:null}}}ready(){super.ready(),this.$.scroller.addEventListener("click",this._onClick.bind(this)),this.addEventListener("cell-activate",this._activateItem.bind(this)),this.addEventListener("row-activate",this._activateItem.bind(this))}_activateItem(e){const t=e.detail.model,r=t?t.item:null;r&&(this.activeItem=this._itemsEqual(this.activeItem,r)?null:r)}_onClick(e){if(e.defaultPrevented)return;const t=e.composedPath(),r=t[t.indexOf(this.$.table)-3];if(!r||r.getAttribute("part").indexOf("details-cell")>-1)return;const i=r._content,o=this.getRootNode().activeElement;i.contains(o)||this._isFocusable(e.target)||e.target instanceof HTMLLabelElement||this.dispatchEvent(new CustomEvent("cell-activate",{detail:{model:this.__getRowModel(r.parentElement)}}))}_isFocusable(e){return Ae(e)}};function Te(e,t){return e.split(".").reduce(((e,t)=>e[t]),t)}function $e(e,t,r){if(0===r.length)return!1;let i=!0;return e.forEach((({path:e})=>{if(!e||-1===e.indexOf("."))return;void 0===Te(e.replace(/\.[^.]*$/u,""),r[0])&&(console.warn(`Path "${e}" used for ${t} does not exist in all of the items, ${t} is disabled.`),i=!1)})),i}function Pe(e){return[void 0,null].indexOf(e)>=0?"":isNaN(e)?e.toString():e}function De(e,t){return(e=Pe(e))<(t=Pe(t))?-1:e>t?1:0}const Oe=e=>(t,r)=>{let i=e?[...e]:[];t.filters&&$e(t.filters,"filtering",i)&&(i=function(e,t){return e.filter((e=>t.every((t=>{const r=Pe(Te(t.path,e)),i=Pe(t.value).toString().toLowerCase();return r.toString().toLowerCase().includes(i)}))))}(i,t.filters)),Array.isArray(t.sortOrders)&&t.sortOrders.length&&$e(t.sortOrders,"sorting",i)&&(i=function(e,t){return e.sort(((e,r)=>t.map((t=>"asc"===t.direction?De(Te(t.path,e),Te(t.path,r)):"desc"===t.direction?De(Te(t.path,r),Te(t.path,e)):0)).reduce(((e,t)=>0!==e?e:t),0)))}(i,t.sortOrders));const o=Math.min(i.length,t.pageSize),s=t.page*o,a=s+o;r(i.slice(s,a),i.length)},Le=e=>class extends e{static get properties(){return{items:Array}}static get observers(){return["__dataProviderOrItemsChanged(dataProvider, items, isAttached, items.*, _filters, _sorters)"]}__setArrayDataProvider(e){const t=Oe(this.items);t.__items=e,this.setProperties({_arrayDataProvider:t,size:e.length,dataProvider:t})}__dataProviderOrItemsChanged(e,t,r){r&&(this._arrayDataProvider?e!==this._arrayDataProvider?this.setProperties({_arrayDataProvider:void 0,items:void 0}):t?this._arrayDataProvider.__items===t?(this.clearCache(),this.size=this._effectiveSize):this.__setArrayDataProvider(t):(this.setProperties({_arrayDataProvider:void 0,dataProvider:void 0,size:0}),this.clearCache()):t&&this.__setArrayDataProvider(t))}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,He=e=>class extends e{static get properties(){return{columnReorderingAllowed:{type:Boolean,value:!1},_orderBaseScope:{type:Number,value:1e7}}}static get observers(){return["_updateOrders(_columnTree)"]}ready(){super.ready(),ie(this,"track",this._onTrackEvent),this._reorderGhost=this.shadowRoot.querySelector('[part="reorder-ghost"]'),this.addEventListener("touchstart",this._onTouchStart.bind(this)),this.addEventListener("touchmove",this._onTouchMove.bind(this)),this.addEventListener("touchend",this._onTouchEnd.bind(this)),this.addEventListener("contextmenu",this._onContextMenu.bind(this))}_onContextMenu(e){this.hasAttribute("reordering")&&(e.preventDefault(),M||this._onTrackEnd())}_onTouchStart(e){this._startTouchReorderTimeout=setTimeout((()=>{this._onTrackStart({detail:{x:e.touches[0].clientX,y:e.touches[0].clientY}})}),100)}_onTouchMove(e){this._draggedColumn&&e.preventDefault(),clearTimeout(this._startTouchReorderTimeout)}_onTouchEnd(){clearTimeout(this._startTouchReorderTimeout),this._onTrackEnd()}_onTrackEvent(e){if("start"===e.detail.state){const t=e.composedPath(),r=t[t.indexOf(this.$.header)-2];if(!r||!r._content)return;if(r._content.contains(this.getRootNode().activeElement))return;if(this.$.scroller.hasAttribute("column-resizing"))return;this._touchDevice||this._onTrackStart(e)}else"track"===e.detail.state?this._onTrack(e):"end"===e.detail.state&&this._onTrackEnd(e)}_onTrackStart(e){if(!this.columnReorderingAllowed)return;const t=e.composedPath&&e.composedPath();if(t&&t.some((e=>e.hasAttribute&&e.hasAttribute("draggable"))))return;const r=this._cellFromPoint(e.detail.x,e.detail.y);if(r&&r.getAttribute("part").includes("header-cell")){for(this.toggleAttribute("reordering",!0),this._draggedColumn=r._column;1===this._draggedColumn.parentElement.childElementCount;)this._draggedColumn=this._draggedColumn.parentElement;this._setSiblingsReorderStatus(this._draggedColumn,"allowed"),this._draggedColumn._reorderStatus="dragging",this._updateGhost(r),this._reorderGhost.style.visibility="visible",this._updateGhostPosition(e.detail.x,this._touchDevice?e.detail.y-50:e.detail.y),this._autoScroller()}}_onTrack(e){if(!this._draggedColumn)return;const t=this._cellFromPoint(e.detail.x,e.detail.y);if(!t)return;const r=this._getTargetColumn(t,this._draggedColumn);if(this._isSwapAllowed(this._draggedColumn,r)&&this._isSwappableByPosition(r,e.detail.x)){const e=this._columnTree.findIndex((e=>e.includes(r))),t=this._getColumnsInOrder(e),i=t.indexOf(this._draggedColumn),o=t.indexOf(r),s=i<o?1:-1;for(let e=i;e!==o;e+=s)this._swapColumnOrders(this._draggedColumn,t[e+s])}this._updateGhostPosition(e.detail.x,this._touchDevice?e.detail.y-50:e.detail.y),this._lastDragClientX=e.detail.x}_onTrackEnd(){this._draggedColumn&&(this.toggleAttribute("reordering",!1),this._draggedColumn._reorderStatus="",this._setSiblingsReorderStatus(this._draggedColumn,""),this._draggedColumn=null,this._lastDragClientX=null,this._reorderGhost.style.visibility="hidden",this.dispatchEvent(new CustomEvent("column-reorder",{detail:{columns:this._getColumnsInOrder()}})))}_getColumnsInOrder(e=this._columnTree.length-1){return this._columnTree[e].filter((e=>!e.hidden)).sort(((e,t)=>e._order-t._order))}_cellFromPoint(e=0,t=0){this._draggedColumn||this.$.scroller.toggleAttribute("no-content-pointer-events",!0);const r=this.shadowRoot.elementFromPoint(e,t);if(this.$.scroller.toggleAttribute("no-content-pointer-events",!1),r&&r._column)return r}_updateGhostPosition(e,t){const r=this._reorderGhost.getBoundingClientRect(),i=e-r.width/2,o=t-r.height/2,s=parseInt(this._reorderGhost._left||0),a=parseInt(this._reorderGhost._top||0);this._reorderGhost._left=s-(r.left-i),this._reorderGhost._top=a-(r.top-o),this._reorderGhost.style.transform=`translate(${this._reorderGhost._left}px, ${this._reorderGhost._top}px)`}_updateGhost(e){const t=this._reorderGhost;t.textContent=e._content.innerText;const r=window.getComputedStyle(e);return["boxSizing","display","width","height","background","alignItems","padding","border","flex-direction","overflow"].forEach((e=>{t.style[e]=r[e]})),t}_updateOrders(e){void 0!==e&&(e[0].forEach((e=>{e._order=0})),we(e[0],this._orderBaseScope,0))}_setSiblingsReorderStatus(e,t){be(e.parentNode,(r=>{/column/u.test(r.localName)&&this._isSwapAllowed(r,e)&&(r._reorderStatus=t)}))}_autoScroller(){if(this._lastDragClientX){const e=this._lastDragClientX-this.getBoundingClientRect().right+50,t=this.getBoundingClientRect().left-this._lastDragClientX+50;e>0?this.$.table.scrollLeft+=e/10:t>0&&(this.$.table.scrollLeft-=t/10)}this._draggedColumn&&setTimeout((()=>this._autoScroller()),10)}_isSwapAllowed(e,t){if(e&&t){const r=e!==t,i=e.parentElement===t.parentElement,o=e.frozen&&t.frozen||e.frozenToEnd&&t.frozenToEnd||!e.frozen&&!e.frozenToEnd&&!t.frozen&&!t.frozenToEnd;return r&&i&&o}}_isSwappableByPosition(e,t){const r=Array.from(this.$.header.querySelectorAll('tr:not([hidden]) [part~="cell"]')).find((t=>e.contains(t._column))),i=this.$.header.querySelector("tr:not([hidden]) [reorder-status=dragging]").getBoundingClientRect(),o=r.getBoundingClientRect();return o.left>i.left?t>o.right-i.width:t<o.left+i.width}_swapColumnOrders(e,t){[e._order,t._order]=[t._order,e._order],this._debounceUpdateFrozenColumn(),this._updateFirstAndLastColumn()}_getTargetColumn(e,t){if(e&&t){let r=e._column;for(;r.parentElement!==t.parentElement&&r!==this;)r=r.parentElement;return r.parentElement===t.parentElement?r:e._column}}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,Ne=e=>class extends e{ready(){super.ready();const e=this.$.scroller;ie(e,"track",this._onHeaderTrack.bind(this)),e.addEventListener("touchmove",(t=>e.hasAttribute("column-resizing")&&t.preventDefault())),e.addEventListener("contextmenu",(e=>"resize-handle"===e.target.getAttribute("part")&&e.preventDefault())),e.addEventListener("mousedown",(e=>"resize-handle"===e.target.getAttribute("part")&&e.preventDefault()))}_onHeaderTrack(e){const t=e.target;if("resize-handle"===t.getAttribute("part")){let r=t.parentElement._column;for(this.$.scroller.toggleAttribute("column-resizing",!0);"vaadin-grid-column-group"===r.localName;)r=r._childColumns.slice(0).sort(((e,t)=>e._order-t._order)).filter((e=>!e.hidden)).pop();const i=this.__isRTL,o=e.detail.x,s=Array.from(this.$.header.querySelectorAll('[part~="row"]:last-child [part~="cell"]')),a=s.find((e=>e._column===r));if(a.offsetWidth){const e=getComputedStyle(a._content),t=10+parseInt(e.paddingLeft)+parseInt(e.paddingRight)+parseInt(e.borderLeftWidth)+parseInt(e.borderRightWidth)+parseInt(e.marginLeft)+parseInt(e.marginRight);let s;const n=a.offsetWidth,l=a.getBoundingClientRect();s=a.hasAttribute("frozen-to-end")?n+(i?o-l.right:l.left-o):n+(i?l.left-o:o-l.right),r.width=`${Math.max(t,s)}px`,r.flexGrow=0}s.sort(((e,t)=>e._column._order-t._column._order)).forEach(((e,t,r)=>{t<r.indexOf(a)&&(e._column.width=`${e.offsetWidth}px`,e._column.flexGrow=0)}));const n=this._frozenToEndCells[0];if(n&&this.$.table.scrollWidth>this.$.table.offsetWidth){const e=n.getBoundingClientRect(),t=o-(i?e.right:e.left);(i&&t<=0||!i&&t>=0)&&(this.$.table.scrollLeft+=t)}"end"===e.detail.state&&(this.$.scroller.toggleAttribute("column-resizing",!1),this.dispatchEvent(new CustomEvent("column-resize",{detail:{resizedColumn:r}}))),this._resizeHandler()}}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,Be=class e{constructor(e,t,r){this.grid=e,this.parentCache=t,this.parentItem=r,this.itemCaches={},this.items={},this.effectiveSize=0,this.size=0,this.pendingRequests={}}isLoading(){return Boolean(Object.keys(this.pendingRequests).length||Object.keys(this.itemCaches).filter((e=>this.itemCaches[e].isLoading()))[0])}getItemForIndex(e){const{cache:t,scaledIndex:r}=this.getCacheAndIndex(e);return t.items[r]}updateSize(){this.effectiveSize=!this.parentItem||this.grid._isExpanded(this.parentItem)?this.size+Object.keys(this.itemCaches).reduce(((e,t)=>{const r=this.itemCaches[t];return r.updateSize(),e+r.effectiveSize}),0):0}ensureSubCacheForScaledIndex(t){if(!this.itemCaches[t]){const r=new e(this.grid,this,this.items[t]);this.itemCaches[t]=r,this.grid._loadPage(0,r)}}getCacheAndIndex(e){let t=e;for(const[e,r]of Object.entries(this.itemCaches)){const i=Number(e);if(t<=i)return{cache:this,scaledIndex:t};if(t<=i+r.effectiveSize)return r.getCacheAndIndex(t-i-1);t-=r.effectiveSize}return{cache:this,scaledIndex:t}}getFlatIndex(e){const t=Math.max(0,Math.min(this.size-1,e));return Object.entries(this.itemCaches).reduce(((e,[r,i])=>t>Number(r)?e+i.effectiveSize:e),t)}},Me=e=>class extends e{static get properties(){return{size:{type:Number,notify:!0},pageSize:{type:Number,value:50,observer:"_pageSizeChanged"},dataProvider:{type:Object,notify:!0,observer:"_dataProviderChanged"},loading:{type:Boolean,notify:!0,readOnly:!0,reflectToAttribute:!0},_cache:{type:Object,value(){return new Be(this)}},_hasData:{type:Boolean,value:!1},itemHasChildrenPath:{type:String,value:"children",observer:"__itemHasChildrenPathChanged"},itemIdPath:{type:String,value:null},expandedItems:{type:Object,notify:!0,value:()=>[]},__expandedKeys:{type:Object,computed:"__computeExpandedKeys(itemIdPath, expandedItems.*)"}}}static get observers(){return["_sizeChanged(size)","_expandedItemsChanged(expandedItems.*)"]}_sizeChanged(e){const t=e-this._cache.size;this._cache.size+=t,this._cache.effectiveSize+=t,this._effectiveSize=this._cache.effectiveSize}__itemHasChildrenPathChanged(e,t){(t||"children"!==e)&&this.requestContentUpdate()}_getItem(e,t){if(e>=this._effectiveSize)return;t.index=e;const{cache:r,scaledIndex:i}=this._cache.getCacheAndIndex(e),o=r.items[i];o?(this.__updateLoading(t,!1),this._updateItem(t,o),this._isExpanded(o)&&r.ensureSubCacheForScaledIndex(i)):(this.__updateLoading(t,!0),this._loadPage(this._getPageForIndex(i),r))}__updateLoading(e,t){const r=fe(e);Ce(e,"loading",t),xe(r,"loading-row-cell",t)}getItemId(e){return this.itemIdPath?this.get(this.itemIdPath,e):e}_isExpanded(e){return this.__expandedKeys.has(this.getItemId(e))}_expandedItemsChanged(){this._cache.updateSize(),this._effectiveSize=this._cache.effectiveSize,this.__updateVisibleRows()}__computeExpandedKeys(e,t){const r=t.base||[],i=new Set;return r.forEach((e=>{i.add(this.getItemId(e))})),i}expandItem(e){this._isExpanded(e)||(this.expandedItems=[...this.expandedItems,e])}collapseItem(e){this._isExpanded(e)&&(this.expandedItems=this.expandedItems.filter((t=>!this._itemsEqual(t,e))))}_getIndexLevel(e){let{cache:t}=this._cache.getCacheAndIndex(e),r=0;for(;t.parentCache;)t=t.parentCache,r+=1;return r}_loadPage(e,t){if(!t.pendingRequests[e]&&this.dataProvider){this._setLoading(!0),t.pendingRequests[e]=!0;const r={page:e,pageSize:this.pageSize,sortOrders:this._mapSorters(),filters:this._mapFilters(),parentItem:t.parentItem};this.dataProvider(r,((i,o)=>{void 0!==o?t.size=o:r.parentItem&&(t.size=i.length),i.forEach(((r,i)=>{const o=e*this.pageSize+i;t.items[o]=r})),this._cache.updateSize(),this._effectiveSize=this._cache.effectiveSize,this._getVisibleRows().forEach((e=>{const{cache:t,scaledIndex:r}=this._cache.getCacheAndIndex(e.index),i=t.items[r];i&&this._isExpanded(i)&&t.ensureSubCacheForScaledIndex(r)})),this._hasData=!0,delete t.pendingRequests[e],this._debouncerApplyCachedData=H.debounce(this._debouncerApplyCachedData,G.after(0),(()=>{this._setLoading(!1),this._getVisibleRows().forEach((e=>{this._cache.getItemForIndex(e.index)&&this._getItem(e.index,e)})),this.__scrollToPendingIndexes()})),this._cache.isLoading()||this._debouncerApplyCachedData.flush(),this._onDataProviderPageLoaded()}))}}_onDataProviderPageLoaded(){}_getPageForIndex(e){return Math.floor(e/this.pageSize)}clearCache(){this._cache=new Be(this),this._cache.size=this.size||0,this._cache.updateSize(),this._hasData=!1,this.__updateVisibleRows(),this._effectiveSize||this._loadPage(0,this._cache)}_pageSizeChanged(e,t){void 0!==t&&e!==t&&this.clearCache()}_checkSize(){void 0===this.size&&0===this._effectiveSize&&console.warn("The <vaadin-grid> needs the total number of items in order to display rows, which you can specify either by setting the `size` property, or by providing it to the second argument of the `dataProvider` function `callback` call.")}_dataProviderChanged(e,t){void 0!==t&&this.clearCache(),this._ensureFirstPageLoaded(),this._debouncerCheckSize=H.debounce(this._debouncerCheckSize,G.after(2e3),this._checkSize.bind(this))}_ensureFirstPageLoaded(){this._hasData||this._loadPage(0,this._cache)}_itemsEqual(e,t){return this.getItemId(e)===this.getItemId(t)}_getItemIndexInArray(e,t){let r=-1;return t.forEach(((t,i)=>{this._itemsEqual(t,e)&&(r=i)})),r}scrollToIndex(...e){let t;for(;t!==(t=this.__getGlobalFlatIndex(e));)this._scrollToFlatIndex(t);!this._cache.isLoading()&&this.clientHeight||(this.__pendingScrollToIndexes=e)}__getGlobalFlatIndex([e,...t],r=this._cache,i=0){e===1/0&&(e=r.size-1);const o=r.getFlatIndex(e),s=r.itemCaches[e];return s&&s.effectiveSize&&t.length?this.__getGlobalFlatIndex(t,s,i+o+1):i+o}__scrollToPendingIndexes(){if(this.__pendingScrollToIndexes&&this.$.items.children.length){const e=this.__pendingScrollToIndexes;delete this.__pendingScrollToIndexes,this.scrollToIndex(...e)}}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,Ge="between",We="on-top-or-between",Ve="on-grid",Ue="on-top",qe="above",je="below",Ke="empty",Xe=!("draggable"in document.createElement("div")),Ye=e=>class extends e{static get properties(){return{dropMode:String,rowsDraggable:Boolean,dragFilter:Function,dropFilter:Function,__dndAutoScrollThreshold:{value:50}}}static get observers(){return["_dragDropAccessChanged(rowsDraggable, dropMode, dragFilter, dropFilter, loading)"]}ready(){super.ready(),this.$.table.addEventListener("dragstart",this._onDragStart.bind(this)),this.$.table.addEventListener("dragend",this._onDragEnd.bind(this)),this.$.table.addEventListener("dragover",this._onDragOver.bind(this)),this.$.table.addEventListener("dragleave",this._onDragLeave.bind(this)),this.$.table.addEventListener("drop",this._onDrop.bind(this)),this.$.table.addEventListener("dragenter",(e=>{this.dropMode&&(e.preventDefault(),e.stopPropagation())}))}_onDragStart(e){if(this.rowsDraggable){let t=e.target;if("vaadin-grid-cell-content"===t.localName&&(t=t.assignedSlot.parentNode.parentNode),t.parentNode!==this.$.items)return;if(e.stopPropagation(),this.toggleAttribute("dragging-rows",!0),this._safari){const e=t.style.transform;t.style.top=/translateY\((.*)\)/u.exec(e)[1],t.style.transform="none",requestAnimationFrame((()=>{t.style.top="",t.style.transform=e}))}const r=t.getBoundingClientRect();Xe?e.dataTransfer.setDragImage(t):e.dataTransfer.setDragImage(t,e.clientX-r.left,e.clientY-r.top);let i=[t];this._isSelected(t._item)&&(i=this.__getViewportRows().filter((e=>this._isSelected(e._item))).filter((e=>!this.dragFilter||this.dragFilter(this.__getRowModel(e))))),e.dataTransfer.setData("text",this.__formatDefaultTransferData(i)),ze(t,{dragstart:i.length>1?`${i.length}`:""}),this.style.setProperty("--_grid-drag-start-x",e.clientX-r.left+20+"px"),this.style.setProperty("--_grid-drag-start-y",e.clientY-r.top+10+"px"),requestAnimationFrame((()=>{ze(t,{dragstart:!1}),this.style.setProperty("--_grid-drag-start-x",""),this.style.setProperty("--_grid-drag-start-y","")}));const o=new CustomEvent("grid-dragstart",{detail:{draggedItems:i.map((e=>e._item)),setDragData:(t,r)=>e.dataTransfer.setData(t,r),setDraggedItemsCount:e=>t.setAttribute("dragstart",e)}});o.originalEvent=e,this.dispatchEvent(o)}}_onDragEnd(e){this.toggleAttribute("dragging-rows",!1),e.stopPropagation();const t=new CustomEvent("grid-dragend");t.originalEvent=e,this.dispatchEvent(t)}_onDragLeave(e){e.stopPropagation(),this._clearDragStyles()}_onDragOver(e){if(this.dropMode){if(this._dropLocation=void 0,this._dragOverItem=void 0,this.__dndAutoScroll(e.clientY))return void this._clearDragStyles();let t=e.composedPath().find((e=>"tr"===e.localName));if(this._effectiveSize&&this.dropMode!==Ve)if(t&&t.parentNode===this.$.items){const r=t.getBoundingClientRect();if(this._dropLocation=Ue,this.dropMode===Ge){const t=e.clientY-r.top<r.bottom-e.clientY;this._dropLocation=t?qe:je}else this.dropMode===We&&(e.clientY-r.top<r.height/3?this._dropLocation=qe:e.clientY-r.top>r.height/3*2&&(this._dropLocation=je))}else{if(t)return;if(this.dropMode!==Ge&&this.dropMode!==We)return;t=Array.from(this.$.items.children).filter((e=>!e.hidden)).pop(),this._dropLocation=je}else this._dropLocation=Ke;if(t&&t.hasAttribute("drop-disabled"))return void(this._dropLocation=void 0);e.stopPropagation(),e.preventDefault(),this._dropLocation===Ke?this.toggleAttribute("dragover",!0):t?(this._dragOverItem=t._item,t.getAttribute("dragover")!==this._dropLocation&&Ee(t,{dragover:this._dropLocation})):this._clearDragStyles()}}__dndAutoScroll(e){if(this.__dndAutoScrolling)return!0;const t=this.$.header.getBoundingClientRect().bottom,r=this.$.footer.getBoundingClientRect().top,i=t-e+this.__dndAutoScrollThreshold,o=e-r+this.__dndAutoScrollThreshold;let s=0;if(o>0?s=2*o:i>0&&(s=2*-i),s){const e=this.$.table.scrollTop;this.$.table.scrollTop+=s;if(e!==this.$.table.scrollTop)return this.__dndAutoScrolling=!0,setTimeout((()=>{this.__dndAutoScrolling=!1}),20),!0}}__getViewportRows(){const e=this.$.header.getBoundingClientRect().bottom,t=this.$.footer.getBoundingClientRect().top;return Array.from(this.$.items.children).filter((r=>{const i=r.getBoundingClientRect();return i.bottom>e&&i.top<t}))}_clearDragStyles(){this.removeAttribute("dragover"),be(this.$.items,(e=>{Ee(e,{dragover:null})}))}_onDrop(e){if(this.dropMode){e.stopPropagation(),e.preventDefault();const t=e.dataTransfer.types&&Array.from(e.dataTransfer.types).map((t=>({type:t,data:e.dataTransfer.getData(t)})));this._clearDragStyles();const r=new CustomEvent("grid-drop",{bubbles:e.bubbles,cancelable:e.cancelable,detail:{dropTargetItem:this._dragOverItem,dropLocation:this._dropLocation,dragData:t}});r.originalEvent=e,this.dispatchEvent(r)}}__formatDefaultTransferData(e){return e.map((e=>Array.from(e.children).filter((e=>!e.hidden&&-1===e.getAttribute("part").indexOf("details-cell"))).sort(((e,t)=>e._column._order>t._column._order?1:-1)).map((e=>e._content.textContent.trim())).filter((e=>e)).join("\t"))).join("\n")}_dragDropAccessChanged(){this.filterDragAndDrop()}filterDragAndDrop(){be(this.$.items,(e=>{e.hidden||this._filterDragAndDrop(e,this.__getRowModel(e))}))}_filterDragAndDrop(e,t){const r=this.loading||e.hasAttribute("loading"),i=!this.rowsDraggable||r||this.dragFilter&&!this.dragFilter(t),o=!this.dropMode||r||this.dropFilter&&!this.dropFilter(t);ve(e,(e=>{i?e._content.removeAttribute("draggable"):e._content.setAttribute("draggable",!0)})),ze(e,{"drag-disabled":!!i,"drop-disabled":!!o})}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */function Je(e,t){if(!e||!t||e.length!==t.length)return!1;for(let r=0,i=e.length;r<i;r++)if(e[r]instanceof Array&&t[r]instanceof Array){if(!Je(e[r],t[r]))return!1}else if(e[r]!==t[r])return!1;return!0}const Ze=e=>class extends e{static get properties(){return{_columnTree:Object}}ready(){super.ready(),this._addNodeObserver()}_hasColumnGroups(e){return e.some((e=>"vaadin-grid-column-group"===e.localName))}_getChildColumns(e){return W.getFlattenedNodes(e).filter(this._isColumnElement)}_flattenColumnGroups(e){return e.map((e=>"vaadin-grid-column-group"===e.localName?this._getChildColumns(e):[e])).reduce(((e,t)=>e.concat(t)),[])}_getColumnTree(){const e=W.getFlattenedNodes(this).filter(this._isColumnElement),t=[e];let r=e;for(;this._hasColumnGroups(r);)r=this._flattenColumnGroups(r),t.push(r);return t}_debounceUpdateColumnTree(){this.__updateColumnTreeDebouncer=H.debounce(this.__updateColumnTreeDebouncer,V,(()=>this._updateColumnTree()))}_updateColumnTree(){const e=this._getColumnTree();Je(e,this._columnTree)||(this._columnTree=e)}_addNodeObserver(){this._observer=new W(this,(e=>{const t=e=>e.filter(this._isColumnElement).length>0;if(t(e.addedNodes)||t(e.removedNodes)){const t=e.removedNodes.flatMap((e=>e._allCells)),r=e=>t.filter((t=>t&&t._content.contains(e))).length;this.__removeSorters(this._sorters.filter(r)),this.__removeFilters(this._filters.filter(r)),this._debounceUpdateColumnTree()}this._debouncerCheckImports=H.debounce(this._debouncerCheckImports,G.after(2e3),this._checkImports.bind(this)),this._ensureFirstPageLoaded()}))}_checkImports(){["vaadin-grid-column-group","vaadin-grid-filter","vaadin-grid-filter-column","vaadin-grid-tree-toggle","vaadin-grid-selection-column","vaadin-grid-sort-column","vaadin-grid-sorter"].forEach((e=>{const t=this.querySelector(e);!t||t instanceof P||console.warn(`Make sure you have imported the required module for <${e}> element.`)}))}_updateFirstAndLastColumn(){Array.from(this.shadowRoot.querySelectorAll("tr")).forEach((e=>this._updateFirstAndLastColumnForRow(e)))}_updateFirstAndLastColumnForRow(e){Array.from(e.querySelectorAll('[part~="cell"]:not([part~="details-cell"])')).sort(((e,t)=>e._column._order-t._column._order)).forEach(((e,t,r)=>{ke(e,"first-column",0===t),ke(e,"last-column",t===r.length-1)}))}_isColumnElement(e){return e.nodeType===Node.ELEMENT_NODE&&/\bcolumn\b/u.test(e.localName)}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,Qe=e=>class extends e{getEventContext(e){const t={},r=e.__composedPath||e.composedPath(),i=r[r.indexOf(this.$.table)-3];return i?(t.section=["body","header","footer","details"].find((e=>i.getAttribute("part").indexOf(e)>-1)),i._column&&(t.column=i._column),"body"!==t.section&&"details"!==t.section||Object.assign(t,this.__getRowModel(i.parentElement)),t):t}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,et=e=>class extends e{static get properties(){return{_filters:{type:Array,value:()=>[]}}}ready(){super.ready(),this.addEventListener("filter-changed",this._filterChanged.bind(this))}_filterChanged(e){e.stopPropagation(),this.__addFilter(e.target),this.__applyFilters()}__removeFilters(e){0!==e.length&&(this._filters=this._filters.filter((t=>e.indexOf(t)<0)),this.__applyFilters())}__addFilter(e){-1===this._filters.indexOf(e)&&this._filters.push(e)}__applyFilters(){this.dataProvider&&this.isAttached&&this.clearCache()}_mapFilters(){return this._filters.map((e=>({path:e.path,value:e.value})))}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,tt=e=>class extends e{static get properties(){return{_headerFocusable:{type:Object,observer:"_focusableChanged"},_itemsFocusable:{type:Object,observer:"_focusableChanged"},_footerFocusable:{type:Object,observer:"_focusableChanged"},_navigatingIsHidden:Boolean,_focusedItemIndex:{type:Number,value:0},_focusedColumnOrder:Number,_focusedCell:{type:Object,observer:"_focusedCellChanged"},interacting:{type:Boolean,value:!1,reflectToAttribute:!0,readOnly:!0,observer:"_interactingChanged"}}}get __rowFocusMode(){return this.__isRow(this._itemsFocusable)||this.__isRow(this._headerFocusable)||this.__isRow(this._footerFocusable)}set __rowFocusMode(e){["_itemsFocusable","_footerFocusable","_headerFocusable"].forEach((t=>{const r=this[t];if(e){const e=r&&r.parentElement;this.__isCell(r)?this[t]=e:this.__isCell(e)&&(this[t]=e.parentElement)}else if(!e&&this.__isRow(r)){const e=r.firstElementChild;this[t]=e._focusButton||e}}))}ready(){super.ready(),this._ios||this._android||(this.addEventListener("keydown",this._onKeyDown),this.addEventListener("keyup",this._onKeyUp),this.addEventListener("focusin",this._onFocusIn),this.addEventListener("focusout",this._onFocusOut),this.$.table.addEventListener("focusin",this._onContentFocusIn.bind(this)),this.addEventListener("mousedown",(()=>{this.toggleAttribute("navigating",!1),this._isMousedown=!0,this._focusedColumnOrder=void 0})),this.addEventListener("mouseup",(()=>{this._isMousedown=!1})))}_focusableChanged(e,t){t&&t.setAttribute("tabindex","-1"),e&&this._updateGridSectionFocusTarget(e)}_focusedCellChanged(e,t){t&&O(t,"part","focused-cell"),e&&D(e,"part","focused-cell")}_interactingChanged(){this._updateGridSectionFocusTarget(this._headerFocusable),this._updateGridSectionFocusTarget(this._itemsFocusable),this._updateGridSectionFocusTarget(this._footerFocusable)}__updateItemsFocusable(){if(!this._itemsFocusable)return;const e=this.shadowRoot.activeElement===this._itemsFocusable;this._getVisibleRows().forEach((e=>{if(e.index===this._focusedItemIndex)if(this.__rowFocusMode)this._itemsFocusable=e;else{let t=this._itemsFocusable.parentElement,r=this._itemsFocusable;if(t){this.__isCell(t)&&(r=t,t=t.parentElement);const i=[...t.children].indexOf(r);this._itemsFocusable=this.__getFocusable(e,e.children[i])}}})),e&&this._itemsFocusable.focus()}_onKeyDown(e){const t=e.key;let r;switch(t){case"ArrowUp":case"ArrowDown":case"ArrowLeft":case"ArrowRight":case"PageUp":case"PageDown":case"Home":case"End":r="Navigation";break;case"Enter":case"Escape":case"F2":r="Interaction";break;case"Tab":r="Tab";break;case" ":r="Space"}this._detectInteracting(e),this.interacting&&"Interaction"!==r&&(r=void 0),r&&this[`_on${r}KeyDown`](e,t)}_ensureScrolledToIndex(e){[...this.$.items.children].find((t=>t.index===e))?this.__scrollIntoViewport(e):this.scrollToIndex(e)}__isRowExpandable(e){if(this.itemHasChildrenPath){const t=e._item;return t&&this.get(this.itemHasChildrenPath,t)&&!this._isExpanded(t)}}__isRowCollapsible(e){return this._isExpanded(e._item)}__isDetailsCell(e){return e.matches('[part~="details-cell"]')}__isCell(e){return e instanceof HTMLTableCellElement}__isRow(e){return e instanceof HTMLTableRowElement}__getIndexOfChildElement(e){return Array.prototype.indexOf.call(e.parentNode.children,e)}_onNavigationKeyDown(e,t){e.preventDefault();const r=this._lastVisibleIndex-this._firstVisibleIndex-1,i=this.__isRTL;let o=0,s=0;switch(t){case"ArrowRight":o=i?-1:1;break;case"ArrowLeft":o=i?1:-1;break;case"Home":this.__rowFocusMode||e.ctrlKey?s=-1/0:o=-1/0;break;case"End":this.__rowFocusMode||e.ctrlKey?s=1/0:o=1/0;break;case"ArrowDown":s=1;break;case"ArrowUp":s=-1;break;case"PageDown":s=r;break;case"PageUp":s=-r}const a=e.composedPath().find((e=>this.__isRow(e))),n=e.composedPath().find((e=>this.__isCell(e)));if(this.__rowFocusMode&&!a||!this.__rowFocusMode&&!n)return;const l=i?"ArrowRight":"ArrowLeft";if(t===(i?"ArrowLeft":"ArrowRight")){if(this.__rowFocusMode)return this.__isRowExpandable(a)?void this.expandItem(a._item):(this.__rowFocusMode=!1,void this._onCellNavigation(a.firstElementChild,0,0))}else if(t===l)if(this.__rowFocusMode){if(this.__isRowCollapsible(a))return void this.collapseItem(a._item)}else{if(n===[...a.children].sort(((e,t)=>e._order-t._order))[0]||this.__isDetailsCell(n))return this.__rowFocusMode=!0,void this._onRowNavigation(a,0)}this.__rowFocusMode?this._onRowNavigation(a,s):this._onCellNavigation(n,o,s)}_onRowNavigation(e,t){const{dstRow:r}=this.__navigateRows(t,e);r&&r.focus()}__getIndexInGroup(e,t){return e.parentNode===this.$.items?void 0!==t?t:e.index:this.__getIndexOfChildElement(e)}__navigateRows(e,t,r){const i=this.__getIndexInGroup(t,this._focusedItemIndex),o=t.parentNode,s=(o===this.$.items?this._effectiveSize:o.children.length)-1;let a=Math.max(0,Math.min(i+e,s));if(o!==this.$.items){if(a>i)for(;a<s&&o.children[a].hidden;)a+=1;else if(a<i)for(;a>0&&o.children[a].hidden;)a-=1;return this.toggleAttribute("navigating",!0),{dstRow:o.children[a]}}let n=!1;if(r){const s=this.__isDetailsCell(r);if(o===this.$.items){const r=t._item,o=this._cache.getItemForIndex(a);n=s?0===e:1===e&&this._isDetailsOpened(r)||-1===e&&a!==i&&this._isDetailsOpened(o),n!==s&&(1===e&&n||-1===e&&!n)&&(a=i)}}return this._ensureScrolledToIndex(a),this._focusedItemIndex=a,this.toggleAttribute("navigating",!0),{dstRow:[...o.children].find((e=>!e.hidden&&e.index===a)),dstIsRowDetails:n}}_onCellNavigation(e,t,r){const i=e.parentNode,{dstRow:o,dstIsRowDetails:s}=this.__navigateRows(r,i,e);if(!o)return;let a=this.__getIndexOfChildElement(e);this.$.items.contains(e)&&(a=[...this.$.sizer.children].findIndex((t=>t._column===e._column)));const n=this.__isDetailsCell(e),l=i.parentNode,d=this.__getIndexInGroup(i,this._focusedItemIndex);if(void 0===this._focusedColumnOrder&&(this._focusedColumnOrder=n?0:this._getColumns(l,d).filter((e=>!e.hidden))[a]._order),s){[...o.children].find((e=>this.__isDetailsCell(e))).focus()}else{const i=this.__getIndexInGroup(o,this._focusedItemIndex),s=this._getColumns(l,i).filter((e=>!e.hidden)),a=s.map((e=>e._order)).sort(((e,t)=>e-t)),d=a.length-1,c=a.indexOf(a.slice(0).sort(((e,t)=>Math.abs(e-this._focusedColumnOrder)-Math.abs(t-this._focusedColumnOrder)))[0]),h=0===r&&n?c:Math.max(0,Math.min(c+t,d));h!==c&&(this._focusedColumnOrder=void 0);const _=s.reduce(((e,t,r)=>(e[t._order]=r,e)),{}),u=_[a[h]];let p;if(this.$.items.contains(e)){const e=this.$.sizer.children[u];this._lazyColumns&&(this.__isColumnInViewport(e._column)||e.scrollIntoView(),this.__updateColumnsBodyContentHidden(),this.__updateHorizontalScrollPosition()),p=[...o.children].find((t=>t._column===e._column)),this._scrollHorizontallyToCell(p)}else p=o.children[u],this._scrollHorizontallyToCell(p);p.focus()}}_onInteractionKeyDown(e,t){const r=e.composedPath()[0],i="input"===r.localName&&!/^(button|checkbox|color|file|image|radio|range|reset|submit)$/iu.test(r.type);let o;switch(t){case"Enter":o=!this.interacting||!i;break;case"Escape":o=!1;break;case"F2":o=!this.interacting}const{cell:s}=this._getGridEventLocation(e);if(this.interacting!==o&&null!==s)if(o){const t=s._content.querySelector("[focus-target]")||[...s._content.querySelectorAll("*")].find((e=>this._isFocusable(e)));t&&(e.preventDefault(),t.focus(),this._setInteracting(!0),this.toggleAttribute("navigating",!1))}else e.preventDefault(),this._focusedColumnOrder=void 0,s.focus(),this._setInteracting(!1),this.toggleAttribute("navigating",!0);"Escape"===t&&this._hideTooltip(!0)}_predictFocusStepTarget(e,t){const r=[this.$.table,this._headerFocusable,this._itemsFocusable,this._footerFocusable,this.$.focusexit];let i=r.indexOf(e);for(i+=t;i>=0&&i<=r.length-1;){let e=r[i];if(e&&!this.__rowFocusMode&&(e=r[i].parentNode),e&&!e.hidden)break;i+=t}let o=r[i];if(o&&o._column&&!this.__isColumnInViewport(o._column)){const e=this._getColumnsInOrder().find((e=>this.__isColumnInViewport(e)));if(e)if(o===this._headerFocusable)o=e._headerCell;else if(o===this._itemsFocusable){const t=o._column._cells.indexOf(o);o=e._cells[t]}else o===this._footerFocusable&&(o=e._footerCell)}return o}_onTabKeyDown(e){const t=this._predictFocusStepTarget(e.composedPath()[0],e.shiftKey?-1:1);if(t){if(e.stopPropagation(),t===this.$.table)this.$.table.focus();else if(t===this.$.focusexit)this.$.focusexit.focus();else if(t===this._itemsFocusable){let r=t;const i=this.__isRow(t)?t:t.parentNode;if(this._ensureScrolledToIndex(this._focusedItemIndex),i.index!==this._focusedItemIndex&&this.__isCell(t)){const e=Array.from(i.children).indexOf(this._itemsFocusable),t=Array.from(this.$.items.children).find((e=>!e.hidden&&e.index===this._focusedItemIndex));t&&(r=t.children[e])}e.preventDefault(),r.focus()}else e.preventDefault(),t.focus();this.toggleAttribute("navigating",!0)}}_onSpaceKeyDown(e){e.preventDefault();const t=e.composedPath()[0],r=this.__isRow(t);!r&&t._content&&t._content.firstElementChild||this.dispatchEvent(new CustomEvent(r?"row-activate":"cell-activate",{detail:{model:this.__getRowModel(r?t:t.parentElement)}}))}_onKeyUp(e){if(!/^( |SpaceBar)$/u.test(e.key)||this.interacting)return;e.preventDefault();const t=e.composedPath()[0];if(t._content&&t._content.firstElementChild){const r=this.hasAttribute("navigating");t._content.firstElementChild.dispatchEvent(new MouseEvent("click",{shiftKey:e.shiftKey,bubbles:!0,composed:!0,cancelable:!0})),this.toggleAttribute("navigating",r)}}_onFocusIn(e){this._isMousedown||this.toggleAttribute("navigating",!0);const t=e.composedPath()[0];t===this.$.table||t===this.$.focusexit?(this._predictFocusStepTarget(t,t===this.$.table?1:-1).focus(),this._setInteracting(!1)):this._detectInteracting(e)}_onFocusOut(e){this.toggleAttribute("navigating",!1),this._detectInteracting(e),this._hideTooltip(),this._focusedCell=null}_onContentFocusIn(e){const{section:t,cell:r,row:i}=this._getGridEventLocation(e);if(r||this.__rowFocusMode){if(this._detectInteracting(e),t&&(r||i))if(this._activeRowGroup=t,this.$.header===t?this._headerFocusable=this.__getFocusable(i,r):this.$.items===t?this._itemsFocusable=this.__getFocusable(i,r):this.$.footer===t&&(this._footerFocusable=this.__getFocusable(i,r)),r){const t=this.getEventContext(e);r.dispatchEvent(new CustomEvent("cell-focus",{bubbles:!0,composed:!0,detail:{context:t}})),this._focusedCell=r._focusButton||r,U()&&e.target===r&&this._showTooltip(e)}else this._focusedCell=null;this._detectFocusedItemIndex(e)}}__getFocusable(e,t){return this.__rowFocusMode?e:t._focusButton||t}_detectInteracting(e){const t=e.composedPath().some((e=>"vaadin-grid-cell-content"===e.localName));this._setInteracting(t),this.__updateHorizontalScrollPosition()}_detectFocusedItemIndex(e){const{section:t,row:r}=this._getGridEventLocation(e);t===this.$.items&&(this._focusedItemIndex=r.index)}_updateGridSectionFocusTarget(e){if(!e)return;const t=this._getGridSectionFromFocusTarget(e),r=this.interacting&&t===this._activeRowGroup;e.tabIndex=r?-1:0}_preventScrollerRotatingCellFocus(e,t){e.index===this._focusedItemIndex&&this.hasAttribute("navigating")&&this._activeRowGroup===this.$.items&&(this._navigatingIsHidden=!0,this.toggleAttribute("navigating",!1)),t===this._focusedItemIndex&&this._navigatingIsHidden&&(this._navigatingIsHidden=!1,this.toggleAttribute("navigating",!0))}_getColumns(e,t){let r=this._columnTree.length-1;return e===this.$.header?r=t:e===this.$.footer&&(r=this._columnTree.length-1-t),this._columnTree[r]}__isValidFocusable(e){return this.$.table.contains(e)&&e.offsetHeight}_resetKeyboardNavigation(){if(["header","footer"].forEach((e=>{if(!this.__isValidFocusable(this[`_${e}Focusable`])){const t=[...this.$[e].children].find((e=>e.offsetHeight)),r=t?[...t.children].find((e=>!e.hidden)):null;t&&r&&(this[`_${e}Focusable`]=this.__getFocusable(t,r))}})),!this.__isValidFocusable(this._itemsFocusable)&&this.$.items.firstElementChild){const e=this.__getFirstVisibleItem(),t=e?[...e.children].find((e=>!e.hidden)):null;t&&e&&(delete this._focusedColumnOrder,this._itemsFocusable=this.__getFocusable(e,t))}else this.__updateItemsFocusable()}_scrollHorizontallyToCell(e){if(e.hasAttribute("frozen")||e.hasAttribute("frozen-to-end")||this.__isDetailsCell(e))return;const t=e.getBoundingClientRect(),r=e.parentNode,i=Array.from(r.children).indexOf(e),o=this.$.table.getBoundingClientRect();let s=o.left,a=o.right;for(let e=i-1;e>=0;e--){const t=r.children[e];if(!t.hasAttribute("hidden")&&!this.__isDetailsCell(t)&&(t.hasAttribute("frozen")||t.hasAttribute("frozen-to-end"))){s=t.getBoundingClientRect().right;break}}for(let e=i+1;e<r.children.length;e++){const t=r.children[e];if(!t.hasAttribute("hidden")&&!this.__isDetailsCell(t)&&(t.hasAttribute("frozen")||t.hasAttribute("frozen-to-end"))){a=t.getBoundingClientRect().left;break}}t.left<s&&(this.$.table.scrollLeft+=Math.round(t.left-s)),t.right>a&&(this.$.table.scrollLeft+=Math.round(t.right-a))}_getGridEventLocation(e){const t=e.composedPath(),r=t.indexOf(this.$.table);return{section:r>=1?t[r-1]:null,row:r>=2?t[r-2]:null,cell:r>=3?t[r-3]:null}}_getGridSectionFromFocusTarget(e){return e===this._headerFocusable?this.$.header:e===this._itemsFocusable?this.$.items:e===this._footerFocusable?this.$.footer:null}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,rt=e=>class extends e{static get properties(){return{detailsOpenedItems:{type:Array,value:()=>[]},rowDetailsRenderer:Function,_detailsCells:{type:Array}}}static get observers(){return["_detailsOpenedItemsChanged(detailsOpenedItems.*, rowDetailsRenderer)","_rowDetailsRendererChanged(rowDetailsRenderer)"]}ready(){super.ready(),this._detailsCellResizeObserver=new ResizeObserver((e=>{e.forEach((({target:e})=>{this._updateDetailsCellHeight(e.parentElement)})),this.__virtualizer.__adapter._resizeHandler()}))}_rowDetailsRendererChanged(e){e&&this._columnTree&&be(this.$.items,(e=>{if(!e.querySelector("[part~=details-cell]")){this._updateRow(e,this._columnTree[this._columnTree.length-1]);const t=this._isDetailsOpened(e._item);this._toggleDetailsCell(e,t)}}))}_detailsOpenedItemsChanged(e,t){"detailsOpenedItems.length"!==e.path&&e.value&&be(this.$.items,(e=>{(e.hasAttribute("details-opened")||t&&this._isDetailsOpened(e._item))&&this._updateItem(e,e._item)}))}_configureDetailsCell(e){e.setAttribute("part","cell details-cell"),e.toggleAttribute("frozen",!0),this._detailsCellResizeObserver.observe(e)}_toggleDetailsCell(e,t){const r=e.querySelector('[part~="details-cell"]');r&&(r.hidden=!t,r.hidden||this.rowDetailsRenderer&&(r._renderer=this.rowDetailsRenderer))}_updateDetailsCellHeight(e){const t=e.querySelector('[part~="details-cell"]');t&&(t.hidden?e.style.removeProperty("padding-bottom"):e.style.setProperty("padding-bottom",`${t.offsetHeight}px`))}_updateDetailsCellHeights(){be(this.$.items,(e=>{this._updateDetailsCellHeight(e)}))}_isDetailsOpened(e){return this.detailsOpenedItems&&-1!==this._getItemIndexInArray(e,this.detailsOpenedItems)}openItemDetails(e){this._isDetailsOpened(e)||(this.detailsOpenedItems=[...this.detailsOpenedItems,e])}closeItemDetails(e){this._isDetailsOpened(e)&&(this.detailsOpenedItems=this.detailsOpenedItems.filter((t=>!this._itemsEqual(t,e))))}}
/**
 * @license
 * Copyright (c) 2022 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,it=document.createElement("div");it.style.position="fixed",it.style.clip="rect(0px, 0px, 0px, 0px)",it.setAttribute("aria-live","polite"),document.body.appendChild(it);
/**
 * @license
 * Copyright (c) 2021 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const ot=new ResizeObserver((e=>{setTimeout((()=>{e.forEach((e=>{e.target.resizables?e.target.resizables.forEach((t=>{t._onResize(e.contentRect)})):e.target._onResize(e.contentRect)}))}))})),st=C((e=>class extends e{get _observeParent(){return!1}connectedCallback(){if(super.connectedCallback(),ot.observe(this),this._observeParent){const e=this.parentNode instanceof ShadowRoot?this.parentNode.host:this.parentNode;e.resizables||(e.resizables=new Set,ot.observe(e)),e.resizables.add(this),this.__parent=e}}disconnectedCallback(){super.disconnectedCallback(),ot.unobserve(this);const e=this.__parent;if(this._observeParent&&e){const t=e.resizables;t&&(t.delete(this),0===t.size&&ot.unobserve(e)),this.__parent=null}}_onResize(e){}})),at=500,nt=100,lt=e=>class extends(st(e)){static get properties(){return{columnRendering:{type:String,value:"eager"},_frozenCells:{type:Array,value:()=>[]},_frozenToEndCells:{type:Array,value:()=>[]},_rowWithFocusedElement:Element}}static get observers(){return["__columnRenderingChanged(_columnTree, columnRendering)"]}get _scrollLeft(){return this.$.table.scrollLeft}get _scrollTop(){return this.$.table.scrollTop}set _scrollTop(e){this.$.table.scrollTop=e}get _lazyColumns(){return"lazy"===this.columnRendering}ready(){super.ready(),this.scrollTarget=this.$.table,this.$.items.addEventListener("focusin",(e=>{const t=e.composedPath().indexOf(this.$.items);this._rowWithFocusedElement=e.composedPath()[t-1]})),this.$.items.addEventListener("focusout",(()=>{this._rowWithFocusedElement=void 0})),this.$.table.addEventListener("scroll",(()=>this._afterScroll()))}_onResize(){if(this._updateOverflow(),this.__updateHorizontalScrollPosition(),this._firefox){const e=!q(this);e&&!1===this.__previousVisible&&(this._scrollTop=this.__memorizedScrollTop||0),this.__previousVisible=e}}_scrollToFlatIndex(e){e=Math.min(this._effectiveSize-1,Math.max(0,e)),this.__virtualizer.scrollToIndex(e),this.__scrollIntoViewport(e)}__scrollIntoViewport(e){const t=[...this.$.items.children].find((t=>t.index===e));if(t){const e=t.getBoundingClientRect(),r=this.$.footer.getBoundingClientRect().top,i=this.$.header.getBoundingClientRect().bottom;e.bottom>r?this.$.table.scrollTop+=e.bottom-r:e.top<i&&(this.$.table.scrollTop-=i-e.top)}}_scheduleScrolling(){this._scrollingFrame||(this._scrollingFrame=requestAnimationFrame((()=>this.$.scroller.toggleAttribute("scrolling",!0)))),this._debounceScrolling=H.debounce(this._debounceScrolling,G.after(at),(()=>{cancelAnimationFrame(this._scrollingFrame),delete this._scrollingFrame,this.$.scroller.toggleAttribute("scrolling",!1)}))}_afterScroll(){if(this.__updateHorizontalScrollPosition(),this.hasAttribute("reordering")||this._scheduleScrolling(),this.hasAttribute("navigating")||this._hideTooltip(!0),this._updateOverflow(),this._debounceColumnContentVisibility=H.debounce(this._debounceColumnContentVisibility,G.after(nt),(()=>{this._lazyColumns&&this.__cachedScrollLeft!==this._scrollLeft&&(this.__cachedScrollLeft=this._scrollLeft,this.__updateColumnsBodyContentHidden())})),this._firefox){!q(this)&&!1!==this.__previousVisible&&(this.__memorizedScrollTop=this._scrollTop)}}__updateColumnsBodyContentHidden(){if(!this._columnTree)return;const e=this._getColumnsInOrder();if(!e[0]||!e[0]._sizerCell)return;let t=!1;if(e.forEach((r=>{const i=this._lazyColumns&&!this.__isColumnInViewport(r);r._bodyContentHidden!==i&&(t=!0,r._cells.forEach((t=>{if(t!==r._sizerCell)if(i)t.remove();else if(t.__parentRow){const i=[...t.__parentRow.children].find((t=>e.indexOf(t._column)>e.indexOf(r)));t.__parentRow.insertBefore(t,i)}}))),r._bodyContentHidden=i})),t&&this._frozenCellsChanged(),this._lazyColumns){const t=[...e].reverse().find((e=>e.frozen)),r=this.__getColumnEnd(t),i=e.find((e=>!e.frozen&&!e._bodyContentHidden));this.__lazyColumnsStart=this.__getColumnStart(i)-r,this.$.items.style.setProperty("--_grid-lazy-columns-start",`${this.__lazyColumnsStart}px`),this._resetKeyboardNavigation()}}__getColumnEnd(e){return e?e._sizerCell.offsetLeft+(this.__isRTL?0:e._sizerCell.offsetWidth):this.__isRTL?this.$.table.clientWidth:0}__getColumnStart(e){return e?e._sizerCell.offsetLeft+(this.__isRTL?e._sizerCell.offsetWidth:0):this.__isRTL?this.$.table.clientWidth:0}__isColumnInViewport(e){return!(!e.frozen&&!e.frozenToEnd)||e._sizerCell.offsetLeft+e._sizerCell.offsetWidth>=this._scrollLeft&&e._sizerCell.offsetLeft<=this._scrollLeft+this.clientWidth}__columnRenderingChanged(e,t){"eager"===t?this.$.scroller.removeAttribute("column-rendering"):this.$.scroller.setAttribute("column-rendering",t),this.__updateColumnsBodyContentHidden()}_updateOverflow(){this._debounceOverflow=H.debounce(this._debounceOverflow,N,(()=>{this.__doUpdateOverflow()}))}__doUpdateOverflow(){let e="";const t=this.$.table;t.scrollTop<t.scrollHeight-t.clientHeight&&(e+=" bottom"),t.scrollTop>0&&(e+=" top");const r=oe(t,this.getAttribute("dir"));r>0&&(e+=" start"),r<t.scrollWidth-t.clientWidth&&(e+=" end"),this.__isRTL&&(e=e.replace(/start|end/giu,(e=>"start"===e?"end":"start"))),t.scrollLeft<t.scrollWidth-t.clientWidth&&(e+=" right"),t.scrollLeft>0&&(e+=" left");const i=e.trim();i.length>0&&this.getAttribute("overflow")!==i?this.setAttribute("overflow",i):0===i.length&&this.hasAttribute("overflow")&&this.removeAttribute("overflow")}_frozenCellsChanged(){this._debouncerCacheElements=H.debounce(this._debouncerCacheElements,V,(()=>{Array.from(this.shadowRoot.querySelectorAll('[part~="cell"]')).forEach((e=>{e.style.transform=""})),this._frozenCells=Array.prototype.slice.call(this.$.table.querySelectorAll("[frozen]")),this._frozenToEndCells=Array.prototype.slice.call(this.$.table.querySelectorAll("[frozen-to-end]")),this.__updateHorizontalScrollPosition()})),this._debounceUpdateFrozenColumn()}_debounceUpdateFrozenColumn(){this.__debounceUpdateFrozenColumn=H.debounce(this.__debounceUpdateFrozenColumn,V,(()=>this._updateFrozenColumn()))}_updateFrozenColumn(){if(!this._columnTree)return;const e=this._columnTree[this._columnTree.length-1].slice(0);let t,r;e.sort(((e,t)=>e._order-t._order));for(let i=0;i<e.length;i++){const o=e[i];o._lastFrozen=!1,o._firstFrozenToEnd=!1,void 0===r&&o.frozenToEnd&&!o.hidden&&(r=i),o.frozen&&!o.hidden&&(t=i)}void 0!==t&&(e[t]._lastFrozen=!0),void 0!==r&&(e[r]._firstFrozenToEnd=!0),this.__updateColumnsBodyContentHidden()}__updateHorizontalScrollPosition(){if(!this._columnTree)return;const e=this.$.table.scrollWidth,t=this.$.table.clientWidth,r=Math.max(0,this.$.table.scrollLeft),i=oe(this.$.table,this.getAttribute("dir")),o=`translate(${-r}px, 0)`;this.$.header.style.transform=o,this.$.footer.style.transform=o,this.$.items.style.transform=o;const s=this.__isRTL?i+t-e:r,a=`translate(${s}px, 0)`;this._frozenCells.forEach((e=>{e.style.transform=a}));const n=this.__isRTL?i:r+t-e,l=`translate(${n}px, 0)`;let d=l;if(this._lazyColumns){const e=this._getColumnsInOrder(),t=[...e].reverse().find((e=>!e.frozenToEnd&&!e._bodyContentHidden)),r=this.__getColumnEnd(t),i=e.find((e=>e.frozenToEnd)),o=n+(this.__getColumnStart(i)-r)+this.__lazyColumnsStart;d=`translate(${o}px, 0)`}this._frozenToEndCells.forEach((e=>{this.$.items.contains(e)?e.style.transform=d:e.style.transform=l})),this.hasAttribute("navigating")&&this.__rowFocusMode&&this.$.table.style.setProperty("--_grid-horizontal-scroll-position",-s+"px")}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,dt=e=>class extends e{static get properties(){return{selectedItems:{type:Object,notify:!0,value:()=>[]},__selectedKeys:{type:Object,computed:"__computeSelectedKeys(itemIdPath, selectedItems.*)"}}}static get observers(){return["__selectedItemsChanged(itemIdPath, selectedItems.*)"]}_isSelected(e){return this.__selectedKeys.has(this.getItemId(e))}selectItem(e){this._isSelected(e)||(this.selectedItems=[...this.selectedItems,e])}deselectItem(e){this._isSelected(e)&&(this.selectedItems=this.selectedItems.filter((t=>!this._itemsEqual(t,e))))}_toggleItem(e){this._isSelected(e)?this.deselectItem(e):this.selectItem(e)}__selectedItemsChanged(){this.requestContentUpdate()}__computeSelectedKeys(e,t){const r=t.base||[],i=new Set;return r.forEach((e=>{i.add(this.getItemId(e))})),i}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;let ct="prepend";const ht=e=>class extends e{static get properties(){return{multiSort:{type:Boolean,value:!1},multiSortPriority:{type:String,value:()=>ct},multiSortOnShiftClick:{type:Boolean,value:!1},_sorters:{type:Array,value:()=>[]},_previousSorters:{type:Array,value:()=>[]}}}static setDefaultMultiSortPriority(e){ct=["append","prepend"].includes(e)?e:"prepend"}ready(){super.ready(),this.addEventListener("sorter-changed",this._onSorterChanged)}_onSorterChanged(e){const t=e.target;e.stopPropagation(),t._grid=this,this.__updateSorter(t,e.detail.shiftClick,e.detail.fromSorterClick),this.__applySorters()}__removeSorters(e){0!==e.length&&(this._sorters=this._sorters.filter((t=>e.indexOf(t)<0)),this.multiSort&&this.__updateSortOrders(),this.__applySorters())}__updateSortOrders(){this._sorters.forEach(((e,t)=>{e._order=this._sorters.length>1?t:null}))}__appendSorter(e){e.direction?this._sorters.includes(e)||this._sorters.push(e):this._removeArrayItem(this._sorters,e),this.__updateSortOrders()}__prependSorter(e){this._removeArrayItem(this._sorters,e),e.direction&&this._sorters.unshift(e),this.__updateSortOrders()}__updateSorter(e,t,r){if(e.direction||-1!==this._sorters.indexOf(e))if(e._order=null,this.multiSort&&(!this.multiSortOnShiftClick||!r)||this.multiSortOnShiftClick&&t)"append"===this.multiSortPriority?this.__appendSorter(e):this.__prependSorter(e);else if(e.direction||this.multiSortOnShiftClick){const t=this._sorters.filter((t=>t!==e));this._sorters=e.direction?[e]:[],t.forEach((e=>{e._order=null,e.direction=null}))}}__applySorters(){this.dataProvider&&this.isAttached&&JSON.stringify(this._previousSorters)!==JSON.stringify(this._mapSorters())&&this.clearCache(),this._a11yUpdateSorters(),this._previousSorters=this._mapSorters()}_mapSorters(){return this._sorters.map((e=>({path:e.path,direction:e.direction})))}_removeArrayItem(e,t){const r=e.indexOf(t);r>-1&&e.splice(r,1)}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,_t=e=>class extends e{static get properties(){return{cellClassNameGenerator:Function,cellPartNameGenerator:Function}}static get observers(){return["__cellClassNameGeneratorChanged(cellClassNameGenerator)","__cellPartNameGeneratorChanged(cellPartNameGenerator)"]}__cellClassNameGeneratorChanged(){this.generateCellClassNames()}__cellPartNameGeneratorChanged(){this.generateCellPartNames()}generateCellClassNames(){be(this.$.items,(e=>{e.hidden||e.hasAttribute("loading")||this._generateCellClassNames(e,this.__getRowModel(e))}))}generateCellPartNames(){be(this.$.items,(e=>{e.hidden||e.hasAttribute("loading")||this._generateCellPartNames(e,this.__getRowModel(e))}))}_generateCellClassNames(e,t){ve(e,(e=>{if(e.__generatedClasses&&e.__generatedClasses.forEach((t=>e.classList.remove(t))),this.cellClassNameGenerator){const r=this.cellClassNameGenerator(e._column,t);e.__generatedClasses=r&&r.split(" ").filter((e=>e.length>0)),e.__generatedClasses&&e.__generatedClasses.forEach((t=>e.classList.add(t)))}}))}_generateCellPartNames(e,t){ve(e,(e=>{if(e.__generatedParts&&e.__generatedParts.forEach((t=>{ye(e,null,t)})),this.cellPartNameGenerator){const r=this.cellPartNameGenerator(e._column,t);e.__generatedParts=r&&r.split(" ").filter((e=>e.length>0)),e.__generatedParts&&e.__generatedParts.forEach((t=>{ye(e,!0,t)}))}}))}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;class ut extends(T($(Me(Le(Ze(Fe(lt(dt(ht(rt(tt(Se(et(He(Ne(j(Qe(Ye(_t(K(P))))))))))))))))))))){static get template(){return A`
      <div
        id="scroller"
        safari$="[[_safari]]"
        ios$="[[_ios]]"
        loading$="[[loading]]"
        column-reordering-allowed$="[[columnReorderingAllowed]]"
      >
        <table id="table" role="treegrid" aria-multiselectable="true" tabindex="0">
          <caption id="sizer" part="row"></caption>
          <thead id="header" role="rowgroup"></thead>
          <tbody id="items" role="rowgroup"></tbody>
          <tfoot id="footer" role="rowgroup"></tfoot>
        </table>

        <div part="reorder-ghost"></div>
      </div>

      <slot name="tooltip"></slot>

      <div id="focusexit" tabindex="0"></div>
    `}static get is(){return"vaadin-grid"}static get observers(){return["_columnTreeChanged(_columnTree, _columnTree.*)","_effectiveSizeChanged(_effectiveSize, __virtualizer, _hasData, _columnTree)"]}static get properties(){return{_safari:{type:Boolean,value:X},_ios:{type:Boolean,value:Y},_firefox:{type:Boolean,value:J},_android:{type:Boolean,value:Z},_touchDevice:{type:Boolean,value:M},allRowsVisible:{type:Boolean,value:!1,reflectToAttribute:!0},__pendingRecalculateColumnWidths:{type:Boolean,value:!0},isAttached:{value:!1},__gridElement:{type:Boolean,value:!0}}}constructor(){super(),this.addEventListener("animationend",this._onAnimationEnd)}get _firstVisibleIndex(){const e=this.__getFirstVisibleItem();return e?e.index:void 0}get _lastVisibleIndex(){const e=this.__getLastVisibleItem();return e?e.index:void 0}connectedCallback(){super.connectedCallback(),this.isAttached=!0,this.recalculateColumnWidths()}disconnectedCallback(){super.disconnectedCallback(),this.isAttached=!1,this._hideTooltip(!0)}__getFirstVisibleItem(){return this._getVisibleRows().find((e=>this._isInViewport(e)))}__getLastVisibleItem(){return this._getVisibleRows().reverse().find((e=>this._isInViewport(e)))}_isInViewport(e){const t=this.$.table.getBoundingClientRect(),r=e.getBoundingClientRect(),i=this.$.header.getBoundingClientRect().height,o=this.$.footer.getBoundingClientRect().height;return r.bottom>t.top+i&&r.top<t.bottom-o}_getVisibleRows(){return Array.from(this.$.items.children).filter((e=>!e.hidden)).sort(((e,t)=>e.index-t.index))}_getRowContainingNode(e){const t=Q("vaadin-grid-cell-content",e);if(!t)return;return t.assignedSlot.parentElement.parentElement}_isItemAssignedToRow(e,t){const r=this.__getRowModel(t);return this.getItemId(e)===this.getItemId(r.item)}ready(){super.ready(),this.__virtualizer=new ee({createElements:this._createScrollerRows.bind(this),updateElement:this._updateScrollerItem.bind(this),scrollContainer:this.$.items,scrollTarget:this.$.table,reorderElements:!0}),new ResizeObserver((()=>setTimeout((()=>{this.__updateFooterPositioning(),this.__updateColumnsBodyContentHidden(),this.__tryToRecalculateColumnWidthsIfPending()})))).observe(this.$.table),L(this),this._tooltipController=new F(this),this.addController(this._tooltipController),this._tooltipController.setManual(!0)}__getBodyCellCoordinates(e){if(this.$.items.contains(e)&&"td"===e.localName)return{item:e.parentElement._item,column:e._column}}__focusBodyCell({item:e,column:t}){const r=this._getVisibleRows().find((t=>t._item===e)),i=r&&[...r.children].find((e=>e._column===t));i&&i.focus()}_focusFirstVisibleRow(){const e=this.__getFirstVisibleItem();this.__rowFocusMode=!0,e.focus()}_effectiveSizeChanged(e,t,r,i){if(t&&r&&i){const r=this.shadowRoot.activeElement,i=this.__getBodyCellCoordinates(r),o=t.size||0;t.size=e,t.update(o-1,o-1),e<o&&t.update(e-1,e-1),i&&r.parentElement.hidden&&this.__focusBodyCell(i),this._resetKeyboardNavigation()}}__hasRowsWithClientHeight(){return!!Array.from(this.$.items.children).filter((e=>e.clientHeight)).length}__getIntrinsicWidth(e){return this.__intrinsicWidthCache.has(e)||this.__calculateAndCacheIntrinsicWidths([e]),this.__intrinsicWidthCache.get(e)}__getDistributedWidth(e,t){if(null==e||e===this)return 0;const r=Math.max(this.__getIntrinsicWidth(e),this.__getDistributedWidth(e.parentElement,e));if(!t)return r;const i=r,o=e._visibleChildColumns.map((e=>this.__getIntrinsicWidth(e))).reduce(((e,t)=>e+t),0),s=Math.max(0,i-o),a=this.__getIntrinsicWidth(t)/o*s;return this.__getIntrinsicWidth(t)+a}_recalculateColumnWidths(e){this.__virtualizer.flush(),[...this.$.header.children,...this.$.footer.children].forEach((e=>{e.__debounceUpdateHeaderFooterRowVisibility&&e.__debounceUpdateHeaderFooterRowVisibility.flush()})),this._debouncerHiddenChanged&&this._debouncerHiddenChanged.flush(),this.__intrinsicWidthCache=new Map;const t=this._firstVisibleIndex,r=this._lastVisibleIndex;this.__viewportRowsCache=this._getVisibleRows().filter((e=>e.index>=t&&e.index<=r)),this.__calculateAndCacheIntrinsicWidths(e),e.forEach((e=>{e.width=`${this.__getDistributedWidth(e)}px`}))}__setVisibleCellContentAutoWidth(e,t){e._allCells.filter((e=>!this.$.items.contains(e)||this.__viewportRowsCache.includes(e.parentElement))).forEach((e=>{e.__measuringAutoWidth=t,e._content.style.width=t?"auto":"",e._content.style.position=t?"absolute":""}))}__getAutoWidthCellsMaxWidth(e){return e._allCells.reduce(((e,t)=>t.__measuringAutoWidth?Math.max(e,t._content.offsetWidth+1):e),0)}__calculateAndCacheIntrinsicWidths(e){e.forEach((e=>this.__setVisibleCellContentAutoWidth(e,!0))),e.forEach((e=>{const t=this.__getAutoWidthCellsMaxWidth(e);this.__intrinsicWidthCache.set(e,t)})),e.forEach((e=>this.__setVisibleCellContentAutoWidth(e,!1)))}recalculateColumnWidths(){if(!this._columnTree)return;if(q(this)||this._cache.isLoading())return void(this.__pendingRecalculateColumnWidths=!0);const e=this._getColumns().filter((e=>!e.hidden&&e.autoWidth));this._recalculateColumnWidths(e)}__tryToRecalculateColumnWidthsIfPending(){this.__pendingRecalculateColumnWidths&&!q(this)&&!this._cache.isLoading()&&this.__hasRowsWithClientHeight()&&(this.__pendingRecalculateColumnWidths=!1,this.recalculateColumnWidths())}_onDataProviderPageLoaded(){super._onDataProviderPageLoaded(),this.__tryToRecalculateColumnWidthsIfPending()}_createScrollerRows(e){const t=[];for(let r=0;r<e;r++){const e=document.createElement("tr");e.setAttribute("part","row"),e.setAttribute("role","row"),e.setAttribute("tabindex","-1"),this._columnTree&&this._updateRow(e,this._columnTree[this._columnTree.length-1],"body",!1,!0),t.push(e)}return this._columnTree&&this._columnTree[this._columnTree.length-1].forEach((e=>e.isConnected&&e.notifyPath&&e.notifyPath("_cells.*",e._cells))),this.__afterCreateScrollerRowsDebouncer=H.debounce(this.__afterCreateScrollerRowsDebouncer,N,(()=>{this._afterScroll(),this.__tryToRecalculateColumnWidthsIfPending()})),t}_createCell(e,t){const r=`vaadin-grid-cell-content-${this._contentIndex=this._contentIndex+1||0}`,i=document.createElement("vaadin-grid-cell-content");i.setAttribute("slot",r);const o=document.createElement(e);o.id=r.replace("-content-","-"),o.setAttribute("role","td"===e?"gridcell":"columnheader"),Z||Y||(o.addEventListener("mouseenter",(e=>{this.$.scroller.hasAttribute("scrolling")||this._showTooltip(e)})),o.addEventListener("mouseleave",(()=>{this._hideTooltip()})),o.addEventListener("mousedown",(()=>{this._hideTooltip(!0)})));const s=document.createElement("slot");if(s.setAttribute("name",r),t&&t._focusButtonMode){const e=document.createElement("div");e.setAttribute("role","button"),e.setAttribute("tabindex","-1"),o.appendChild(e),o._focusButton=e,o.focus=function(){o._focusButton.focus()},e.appendChild(s)}else o.setAttribute("tabindex","-1"),o.appendChild(s);return o._content=i,i.addEventListener("mousedown",(()=>{if(te){const e=t=>{const r=i.contains(this.getRootNode().activeElement),s=t.composedPath().includes(i);!r&&s&&o.focus(),document.removeEventListener("mouseup",e,!0)};document.addEventListener("mouseup",e,!0)}else setTimeout((()=>{i.contains(this.getRootNode().activeElement)||o.focus()}))})),o}_updateRow(e,t,r="body",i=!1,o=!1){const s=document.createDocumentFragment();ve(e,(e=>{e._vacant=!0})),e.innerHTML="","body"===r&&(e.__cells=[],e.__detailsCell=null),t.filter((e=>!e.hidden)).forEach(((t,a,n)=>{let l;if("body"===r){if(t._cells||(t._cells=[]),l=t._cells.find((e=>e._vacant)),l||(l=this._createCell("td",t),t._cells.push(l)),l.setAttribute("part","cell body-cell"),l.__parentRow=e,e.__cells.push(l),t._bodyContentHidden||e.appendChild(l),e===this.$.sizer&&(t._sizerCell=l),a===n.length-1&&this.rowDetailsRenderer){this._detailsCells||(this._detailsCells=[]);const t=this._detailsCells.find((e=>e._vacant))||this._createCell("td");-1===this._detailsCells.indexOf(t)&&this._detailsCells.push(t),t._content.parentElement||s.appendChild(t._content),this._configureDetailsCell(t),e.appendChild(t),e.__detailsCell=t,this._a11ySetRowDetailsCell(e,t),t._vacant=!1}t.notifyPath&&!o&&t.notifyPath("_cells.*",t._cells)}else{const o="header"===r?"th":"td";i||"vaadin-grid-column-group"===t.localName?(l=t[`_${r}Cell`]||this._createCell(o),l._column=t,e.appendChild(l),t[`_${r}Cell`]=l):(t._emptyCells||(t._emptyCells=[]),l=t._emptyCells.find((e=>e._vacant))||this._createCell(o),l._column=t,e.appendChild(l),-1===t._emptyCells.indexOf(l)&&t._emptyCells.push(l)),l.setAttribute("part",`cell ${r}-cell`)}l._content.parentElement||s.appendChild(l._content),l._vacant=!1,l._column=t})),"body"!==r&&this.__debounceUpdateHeaderFooterRowVisibility(e),this.appendChild(s),this._frozenCellsChanged(),this._updateFirstAndLastColumnForRow(e)}__debounceUpdateHeaderFooterRowVisibility(e){e.__debounceUpdateHeaderFooterRowVisibility=H.debounce(e.__debounceUpdateHeaderFooterRowVisibility,V,(()=>this.__updateHeaderFooterRowVisibility(e)))}__updateHeaderFooterRowVisibility(e){if(!e)return;const t=Array.from(e.children).filter((t=>{const r=t._column;if(r._emptyCells&&r._emptyCells.indexOf(t)>-1)return!1;if(e.parentElement===this.$.header){if(r.headerRenderer)return!0;if(null===r.header)return!1;if(r.path||void 0!==r.header)return!0}else if(r.footerRenderer)return!0;return!1}));e.hidden!==!t.length&&(e.hidden=!t.length),this._resetKeyboardNavigation()}_updateScrollerItem(e,t){this._preventScrollerRotatingCellFocus(e,t),this._columnTree&&(this._updateRowOrderParts(e,t),this._a11yUpdateRowRowindex(e,t),this._getItem(t,e))}_columnTreeChanged(e){this._renderColumnTree(e),this.recalculateColumnWidths(),this.__updateColumnsBodyContentHidden()}_updateRowOrderParts(e,t=e.index){ze(e,{first:0===t,last:t===this._effectiveSize-1,odd:t%2!=0,even:t%2==0})}_updateRowStateParts(e,{expanded:t,selected:r,detailsOpened:i}){ze(e,{expanded:t,selected:r,"details-opened":i})}_renderColumnTree(e){for(be(this.$.items,(t=>{this._updateRow(t,e[e.length-1],"body",!1,!0);const r=this.__getRowModel(t);this._updateRowOrderParts(t),this._updateRowStateParts(t,r),this._filterDragAndDrop(t,r)}));this.$.header.children.length<e.length;){const e=document.createElement("tr");e.setAttribute("part","row"),e.setAttribute("role","row"),e.setAttribute("tabindex","-1"),this.$.header.appendChild(e);const t=document.createElement("tr");t.setAttribute("part","row"),t.setAttribute("role","row"),t.setAttribute("tabindex","-1"),this.$.footer.appendChild(t)}for(;this.$.header.children.length>e.length;)this.$.header.removeChild(this.$.header.firstElementChild),this.$.footer.removeChild(this.$.footer.firstElementChild);be(this.$.header,((t,r,i)=>{this._updateRow(t,e[r],"header",r===e.length-1);const o=fe(t);xe(o,"first-header-row-cell",0===r),xe(o,"last-header-row-cell",r===i.length-1)})),be(this.$.footer,((t,r,i)=>{this._updateRow(t,e[e.length-1-r],"footer",0===r);const o=fe(t);xe(o,"first-footer-row-cell",0===r),xe(o,"last-footer-row-cell",r===i.length-1)})),this._updateRow(this.$.sizer,e[e.length-1]),this._resizeHandler(),this._frozenCellsChanged(),this._updateFirstAndLastColumn(),this._resetKeyboardNavigation(),this._a11yUpdateHeaderRows(),this._a11yUpdateFooterRows(),this.__updateFooterPositioning(),this.generateCellClassNames(),this.generateCellPartNames()}__updateFooterPositioning(){this._firefox&&parseFloat(navigator.userAgent.match(/Firefox\/(\d{2,3}.\d)/u)[1])<99&&(this.$.items.style.paddingBottom=0,this.allRowsVisible||(this.$.items.style.paddingBottom=`${this.$.footer.offsetHeight}px`))}_updateItem(e,t){e._item=t;const r=this.__getRowModel(e);this._toggleDetailsCell(e,r.detailsOpened),this._a11yUpdateRowLevel(e,r.level),this._a11yUpdateRowSelected(e,r.selected),this._updateRowStateParts(e,r),this._generateCellClassNames(e,r),this._generateCellPartNames(e,r),this._filterDragAndDrop(e,r),be(e,(e=>{if(e._renderer){const t=e._column||this;e._renderer.call(t,e._content,t,r)}})),this._updateDetailsCellHeight(e),this._a11yUpdateRowExpanded(e,r.expanded)}_resizeHandler(){this._updateDetailsCellHeights(),this.__updateFooterPositioning(),this.__updateHorizontalScrollPosition()}_onAnimationEnd(e){0===e.animationName.indexOf("vaadin-grid-appear")&&(e.stopPropagation(),this.__tryToRecalculateColumnWidthsIfPending(),requestAnimationFrame((()=>{this.__scrollToPendingIndexes()})))}__getRowModel(e){return{index:e.index,item:e._item,level:this._getIndexLevel(e.index),expanded:this._isExpanded(e._item),selected:this._isSelected(e._item),detailsOpened:!!this.rowDetailsRenderer&&this._isDetailsOpened(e._item)}}_showTooltip(e){const t=this._tooltipController.node;t&&t.isConnected&&(this._tooltipController.setTarget(e.target),this._tooltipController.setContext(this.getEventContext(e)),t._stateController.open({focus:"focusin"===e.type,hover:"mouseenter"===e.type}))}_hideTooltip(e){const t=this._tooltipController.node;t&&t._stateController.close(e)}requestContentUpdate(){this._columnTree&&(this._columnTree.forEach((e=>{e.forEach((e=>{e._renderHeaderAndFooter&&e._renderHeaderAndFooter()}))})),this.__updateVisibleRows())}__updateVisibleRows(e,t){this.__virtualizer&&this.__virtualizer.update(e,t)}}customElements.define(ut.is,ut);export{Ie as C,Re as G,Ae as i,we as u};
