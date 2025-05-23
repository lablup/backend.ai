import{_ as e,n as t,t as i,h as r,b as s,I as o,a as n,a6 as a,c as l,i as c,k as d,Y as u,F as h,H as p,aa as m,M as f,L as g,a1 as v,J as b,a0 as _,ab as y,V as x,a3 as w,W as k,X as C,ac as S,ad as T,ae as M,af as P,Z as $,e as E,ag as L,ah as R,a4 as A,a2 as I,B as N,d as D,f as O,ai as F,aj as z,r as W,ak as B,al as j,am as H,an as U,ao as G,q as V,z as q,p as Z,T as K,E as X,P as Y,C as J,ap as Q,aq as ee,ar as te,G as ie,g as re,s as se,l as oe,Q as ne,A as ae}from"./backend-ai-webui-Cm8tlUKt.js";let le=class extends r{constructor(){super(...arguments),this.progress="",this.description=""}static get styles(){return[s,o,n,a,l,c`
        .progress {
          position: relative;
          display: flex;
          height: var(--progress-bar-height, 20px);
          width: var(--progress-bar-width, 186px);
          border: var(--progress-bar-border, 0px);
          border-radius: var(--progress-bar-border-radius, 5px);
          font-size: var(--progress-bar-font-size, 10px);
          font-family: var(--progress-bar-font-family, var(--token-fontFamily));
          overflow: hidden;
        }

        .back {
          display: flex;
          justify-content: left;
          align-items: center;
          width: 100%;
          background: var(--progress-bar-background, var(--paper-green-500));
          color: var(--progress-bar-font-color-inverse, white);
        }

        .front {
          position: absolute;
          display: flex;
          justify-content: left;
          align-items: center;
          left: 0;
          right: 0;
          top: -1px;
          bottom: -1px;
          background: var(--general-progress-bar-bg, #e8e8e8);
          color: var(--progress-bar-font-color, black);
          clip-path: inset(0 0 0 100%);
          -webkit-clip-path: inset(0 0 0 100%);
          transition: clip-path var(--progress-bar-transition-second, 1s) linear;
        }

        .front[slot='description-2'] {
          color: var(--progress-bar-font-color, black);
        }
      `]}render(){return d`
      <link rel="stylesheet" href="resources/custom.css" />
      <div class="horizontal layout flex">
        <slot name="left-desc"></slot>
        <div class="progress">
          <div id="back" class="back"></div>
          <div id="front" class="front"></div>
        </div>
        <slot name="right-desc"></slot>
      </div>
    `}firstUpdated(){var e,t,i;this.progressBar=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#front"),this.frontDesc=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#front"),this.backDesc=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#back"),this.progressBar.style.clipPath="inset(0 0 0 0%)"}async changePct(e){await this.updateComplete,this.progressBar.style.clipPath="inset(0 0 0 "+100*e+"%)"}async changeDesc(e){await this.updateComplete,this.frontDesc.innerHTML="&nbsp;"+e,this.backDesc.innerHTML="&nbsp;"+e}connectedCallback(){super.connectedCallback()}disconnectedCallback(){super.disconnectedCallback()}attributeChangedCallback(e,t,i){"progress"!=e||null===i||isNaN(i)||this.changePct(i),"description"!=e||null===i||i.startsWith("undefined")||this.changeDesc(i),super.attributeChangedCallback(e,t,i)}};e([t({type:Object})],le.prototype,"progressBar",void 0),e([t({type:Object})],le.prototype,"frontDesc",void 0),e([t({type:Object})],le.prototype,"backDesc",void 0),e([t({type:String})],le.prototype,"progress",void 0),e([t({type:String})],le.prototype,"description",void 0),le=e([i("lablup-progress-bar")],le);
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-LIcense-Identifier: Apache-2.0
 */
const ce=u`.mdc-slider{cursor:pointer;height:48px;margin:0 24px;position:relative;touch-action:pan-y}.mdc-slider .mdc-slider__track{height:4px;position:absolute;top:50%;transform:translateY(-50%);width:100%}.mdc-slider .mdc-slider__track--active,.mdc-slider .mdc-slider__track--inactive{display:flex;height:100%;position:absolute;width:100%}.mdc-slider .mdc-slider__track--active{border-radius:3px;height:6px;overflow:hidden;top:-1px}.mdc-slider .mdc-slider__track--active_fill{border-top:6px solid;box-sizing:border-box;height:100%;width:100%;position:relative;-webkit-transform-origin:left;transform-origin:left}[dir=rtl] .mdc-slider .mdc-slider__track--active_fill,.mdc-slider .mdc-slider__track--active_fill[dir=rtl]{-webkit-transform-origin:right;transform-origin:right}.mdc-slider .mdc-slider__track--inactive{border-radius:2px;height:4px;left:0;top:0}.mdc-slider .mdc-slider__track--inactive::before{position:absolute;box-sizing:border-box;width:100%;height:100%;top:0;left:0;border:1px solid transparent;border-radius:inherit;content:"";pointer-events:none}@media screen and (forced-colors: active){.mdc-slider .mdc-slider__track--inactive::before{border-color:CanvasText}}.mdc-slider .mdc-slider__track--active_fill{border-color:#6200ee;border-color:var(--mdc-theme-primary, #6200ee)}.mdc-slider.mdc-slider--disabled .mdc-slider__track--active_fill{border-color:#000;border-color:var(--mdc-theme-on-surface, #000)}.mdc-slider .mdc-slider__track--inactive{background-color:#6200ee;background-color:var(--mdc-theme-primary, #6200ee);opacity:.24}.mdc-slider.mdc-slider--disabled .mdc-slider__track--inactive{background-color:#000;background-color:var(--mdc-theme-on-surface, #000);opacity:.24}.mdc-slider .mdc-slider__value-indicator-container{bottom:44px;left:50%;left:var(--slider-value-indicator-container-left, 50%);pointer-events:none;position:absolute;right:var(--slider-value-indicator-container-right);transform:translateX(-50%);transform:var(--slider-value-indicator-container-transform, translateX(-50%))}.mdc-slider .mdc-slider__value-indicator{transition:transform 100ms 0ms cubic-bezier(0.4, 0, 1, 1);align-items:center;border-radius:4px;display:flex;height:32px;padding:0 12px;transform:scale(0);transform-origin:bottom}.mdc-slider .mdc-slider__value-indicator::before{border-left:6px solid transparent;border-right:6px solid transparent;border-top:6px solid;bottom:-5px;content:"";height:0;left:50%;left:var(--slider-value-indicator-caret-left, 50%);position:absolute;right:var(--slider-value-indicator-caret-right);transform:translateX(-50%);transform:var(--slider-value-indicator-caret-transform, translateX(-50%));width:0}.mdc-slider .mdc-slider__value-indicator::after{position:absolute;box-sizing:border-box;width:100%;height:100%;top:0;left:0;border:1px solid transparent;border-radius:inherit;content:"";pointer-events:none}@media screen and (forced-colors: active){.mdc-slider .mdc-slider__value-indicator::after{border-color:CanvasText}}.mdc-slider .mdc-slider__thumb--with-indicator .mdc-slider__value-indicator-container{pointer-events:auto}.mdc-slider .mdc-slider__thumb--with-indicator .mdc-slider__value-indicator{transition:transform 100ms 0ms cubic-bezier(0, 0, 0.2, 1);transform:scale(1)}@media(prefers-reduced-motion){.mdc-slider .mdc-slider__value-indicator,.mdc-slider .mdc-slider__thumb--with-indicator .mdc-slider__value-indicator{transition:none}}.mdc-slider .mdc-slider__value-indicator-text{-moz-osx-font-smoothing:grayscale;-webkit-font-smoothing:antialiased;font-family:Roboto, sans-serif;font-family:var(--mdc-typography-subtitle2-font-family, var(--mdc-typography-font-family, Roboto, sans-serif));font-size:0.875rem;font-size:var(--mdc-typography-subtitle2-font-size, 0.875rem);line-height:1.375rem;line-height:var(--mdc-typography-subtitle2-line-height, 1.375rem);font-weight:500;font-weight:var(--mdc-typography-subtitle2-font-weight, 500);letter-spacing:0.0071428571em;letter-spacing:var(--mdc-typography-subtitle2-letter-spacing, 0.0071428571em);text-decoration:inherit;text-decoration:var(--mdc-typography-subtitle2-text-decoration, inherit);text-transform:inherit;text-transform:var(--mdc-typography-subtitle2-text-transform, inherit)}.mdc-slider .mdc-slider__value-indicator{background-color:#000;opacity:.6}.mdc-slider .mdc-slider__value-indicator::before{border-top-color:#000}.mdc-slider .mdc-slider__value-indicator{color:#fff;color:var(--mdc-theme-on-primary, #fff)}.mdc-slider .mdc-slider__thumb{display:flex;height:48px;left:-24px;outline:none;position:absolute;user-select:none;width:48px}.mdc-slider .mdc-slider__thumb--top{z-index:1}.mdc-slider .mdc-slider__thumb--top .mdc-slider__thumb-knob,.mdc-slider .mdc-slider__thumb--top.mdc-slider__thumb:hover .mdc-slider__thumb-knob,.mdc-slider .mdc-slider__thumb--top.mdc-slider__thumb--focused .mdc-slider__thumb-knob{border-style:solid;border-width:1px;box-sizing:content-box}.mdc-slider .mdc-slider__thumb-knob{box-shadow:0px 2px 1px -1px rgba(0, 0, 0, 0.2),0px 1px 1px 0px rgba(0, 0, 0, 0.14),0px 1px 3px 0px rgba(0,0,0,.12);border:10px solid;border-radius:50%;box-sizing:border-box;height:20px;left:50%;position:absolute;top:50%;transform:translate(-50%, -50%);width:20px}.mdc-slider .mdc-slider__thumb-knob{background-color:#6200ee;background-color:var(--mdc-theme-primary, #6200ee);border-color:#6200ee;border-color:var(--mdc-theme-primary, #6200ee)}.mdc-slider .mdc-slider__thumb--top .mdc-slider__thumb-knob,.mdc-slider .mdc-slider__thumb--top.mdc-slider__thumb:hover .mdc-slider__thumb-knob,.mdc-slider .mdc-slider__thumb--top.mdc-slider__thumb--focused .mdc-slider__thumb-knob{border-color:#fff}.mdc-slider.mdc-slider--disabled .mdc-slider__thumb-knob{background-color:#000;background-color:var(--mdc-theme-on-surface, #000);border-color:#000;border-color:var(--mdc-theme-on-surface, #000)}.mdc-slider.mdc-slider--disabled .mdc-slider__thumb--top .mdc-slider__thumb-knob,.mdc-slider.mdc-slider--disabled .mdc-slider__thumb--top.mdc-slider__thumb:hover .mdc-slider__thumb-knob,.mdc-slider.mdc-slider--disabled .mdc-slider__thumb--top.mdc-slider__thumb--focused .mdc-slider__thumb-knob{border-color:#fff}.mdc-slider .mdc-slider__thumb::before,.mdc-slider .mdc-slider__thumb::after{background-color:#6200ee;background-color:var(--mdc-ripple-color, var(--mdc-theme-primary, #6200ee))}.mdc-slider .mdc-slider__thumb:hover::before,.mdc-slider .mdc-slider__thumb.mdc-ripple-surface--hover::before{opacity:0.04;opacity:var(--mdc-ripple-hover-opacity, 0.04)}.mdc-slider .mdc-slider__thumb.mdc-ripple-upgraded--background-focused::before,.mdc-slider .mdc-slider__thumb:not(.mdc-ripple-upgraded):focus::before{transition-duration:75ms;opacity:0.12;opacity:var(--mdc-ripple-focus-opacity, 0.12)}.mdc-slider .mdc-slider__thumb:not(.mdc-ripple-upgraded)::after{transition:opacity 150ms linear}.mdc-slider .mdc-slider__thumb:not(.mdc-ripple-upgraded):active::after{transition-duration:75ms;opacity:0.12;opacity:var(--mdc-ripple-press-opacity, 0.12)}.mdc-slider .mdc-slider__thumb.mdc-ripple-upgraded{--mdc-ripple-fg-opacity:var(--mdc-ripple-press-opacity, 0.12)}.mdc-slider .mdc-slider__tick-marks{align-items:center;box-sizing:border-box;display:flex;height:100%;justify-content:space-between;padding:0 1px;position:absolute;width:100%}.mdc-slider .mdc-slider__tick-mark--active,.mdc-slider .mdc-slider__tick-mark--inactive{border-radius:50%;height:2px;width:2px}.mdc-slider .mdc-slider__tick-mark--active{background-color:#fff;background-color:var(--mdc-theme-on-primary, #fff);opacity:.6}.mdc-slider.mdc-slider--disabled .mdc-slider__tick-mark--active{background-color:#fff;background-color:var(--mdc-theme-on-primary, #fff);opacity:.6}.mdc-slider .mdc-slider__tick-mark--inactive{background-color:#6200ee;background-color:var(--mdc-theme-primary, #6200ee);opacity:.6}.mdc-slider.mdc-slider--disabled .mdc-slider__tick-mark--inactive{background-color:#000;background-color:var(--mdc-theme-on-surface, #000);opacity:.6}.mdc-slider--discrete .mdc-slider__thumb,.mdc-slider--discrete .mdc-slider__track--active_fill{transition:transform 80ms ease}@media(prefers-reduced-motion){.mdc-slider--discrete .mdc-slider__thumb,.mdc-slider--discrete .mdc-slider__track--active_fill{transition:none}}.mdc-slider--disabled{opacity:.38;cursor:auto}.mdc-slider--disabled .mdc-slider__thumb{pointer-events:none}.mdc-slider__input{cursor:pointer;left:0;margin:0;height:100%;opacity:0;pointer-events:none;position:absolute;top:0;width:100%}:host{outline:none;display:block;-webkit-tap-highlight-color:transparent}.ripple{--mdc-ripple-color:#6200ee;--mdc-ripple-color:var(--mdc-theme-primary, #6200ee)}`
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
 */;var de,ue;!function(e){e[e.ACTIVE=0]="ACTIVE",e[e.INACTIVE=1]="INACTIVE"}(de||(de={})),function(e){e[e.START=1]="START",e[e.END=2]="END"}(ue||(ue={}));
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
var he={animation:{prefixed:"-webkit-animation",standard:"animation"},transform:{prefixed:"-webkit-transform",standard:"transform"},transition:{prefixed:"-webkit-transition",standard:"transition"}};function pe(e,t){if(function(e){return Boolean(e.document)&&"function"==typeof e.document.createElement}(e)&&t in he){var i=e.document.createElement("div"),r=he[t],s=r.standard,o=r.prefixed;return s in i.style?s:o}return t}
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
 */var me,fe="mdc-slider--disabled",ge="mdc-slider--discrete",ve="mdc-slider--range",be="mdc-slider__thumb--focused",_e="mdc-slider__thumb--top",ye="mdc-slider__thumb--with-indicator",xe="mdc-slider--tick-marks",we=1,ke=0,Ce=5,Se="aria-valuetext",Te="disabled",Me="min",Pe="max",$e="value",Ee="step",Le="data-min-range",Re="--slider-value-indicator-caret-left",Ae="--slider-value-indicator-caret-right",Ie="--slider-value-indicator-caret-transform",Ne="--slider-value-indicator-container-left",De="--slider-value-indicator-container-right",Oe="--slider-value-indicator-container-transform";!function(e){e.SLIDER_UPDATE="slider_update"}(me||(me={}));var Fe="undefined"!=typeof window,ze=function(e){function t(i){var r=e.call(this,p(p({},t.defaultAdapter),i))||this;return r.initialStylesRemoved=!1,r.isDisabled=!1,r.isDiscrete=!1,r.step=we,r.minRange=ke,r.hasTickMarks=!1,r.isRange=!1,r.thumb=null,r.downEventClientX=null,r.startThumbKnobWidth=0,r.endThumbKnobWidth=0,r.animFrame=new m,r}return h(t,e),Object.defineProperty(t,"defaultAdapter",{get:function(){return{hasClass:function(){return!1},addClass:function(){},removeClass:function(){},addThumbClass:function(){},removeThumbClass:function(){},getAttribute:function(){return null},getInputValue:function(){return""},setInputValue:function(){},getInputAttribute:function(){return null},setInputAttribute:function(){return null},removeInputAttribute:function(){return null},focusInput:function(){},isInputFocused:function(){return!1},shouldHideFocusStylesForPointerEvents:function(){return!1},getThumbKnobWidth:function(){return 0},getValueIndicatorContainerWidth:function(){return 0},getThumbBoundingClientRect:function(){return{top:0,right:0,bottom:0,left:0,width:0,height:0}},getBoundingClientRect:function(){return{top:0,right:0,bottom:0,left:0,width:0,height:0}},isRTL:function(){return!1},setThumbStyleProperty:function(){},removeThumbStyleProperty:function(){},setTrackActiveStyleProperty:function(){},removeTrackActiveStyleProperty:function(){},setValueIndicatorText:function(){},getValueToAriaValueTextFn:function(){return null},updateTickMarks:function(){},setPointerCapture:function(){},emitChangeEvent:function(){},emitInputEvent:function(){},emitDragStartEvent:function(){},emitDragEndEvent:function(){},registerEventHandler:function(){},deregisterEventHandler:function(){},registerThumbEventHandler:function(){},deregisterThumbEventHandler:function(){},registerInputEventHandler:function(){},deregisterInputEventHandler:function(){},registerBodyEventHandler:function(){},deregisterBodyEventHandler:function(){},registerWindowEventHandler:function(){},deregisterWindowEventHandler:function(){}}},enumerable:!1,configurable:!0}),t.prototype.init=function(){var e=this;this.isDisabled=this.adapter.hasClass(fe),this.isDiscrete=this.adapter.hasClass(ge),this.hasTickMarks=this.adapter.hasClass(xe),this.isRange=this.adapter.hasClass(ve);var t=this.convertAttributeValueToNumber(this.adapter.getInputAttribute(Me,this.isRange?ue.START:ue.END),Me),i=this.convertAttributeValueToNumber(this.adapter.getInputAttribute(Pe,ue.END),Pe),r=this.convertAttributeValueToNumber(this.adapter.getInputAttribute($e,ue.END),$e),s=this.isRange?this.convertAttributeValueToNumber(this.adapter.getInputAttribute($e,ue.START),$e):t,o=this.adapter.getInputAttribute(Ee,ue.END),n=o?this.convertAttributeValueToNumber(o,Ee):this.step,a=this.adapter.getAttribute(Le),l=a?this.convertAttributeValueToNumber(a,Le):this.minRange;this.validateProperties({min:t,max:i,value:r,valueStart:s,step:n,minRange:l}),this.min=t,this.max=i,this.value=r,this.valueStart=s,this.step=n,this.minRange=l,this.numDecimalPlaces=We(this.step),this.valueBeforeDownEvent=r,this.valueStartBeforeDownEvent=s,this.mousedownOrTouchstartListener=this.handleMousedownOrTouchstart.bind(this),this.moveListener=this.handleMove.bind(this),this.pointerdownListener=this.handlePointerdown.bind(this),this.pointerupListener=this.handlePointerup.bind(this),this.thumbMouseenterListener=this.handleThumbMouseenter.bind(this),this.thumbMouseleaveListener=this.handleThumbMouseleave.bind(this),this.inputStartChangeListener=function(){e.handleInputChange(ue.START)},this.inputEndChangeListener=function(){e.handleInputChange(ue.END)},this.inputStartFocusListener=function(){e.handleInputFocus(ue.START)},this.inputEndFocusListener=function(){e.handleInputFocus(ue.END)},this.inputStartBlurListener=function(){e.handleInputBlur(ue.START)},this.inputEndBlurListener=function(){e.handleInputBlur(ue.END)},this.resizeListener=this.handleResize.bind(this),this.registerEventHandlers()},t.prototype.destroy=function(){this.deregisterEventHandlers()},t.prototype.setMin=function(e){this.min=e,this.isRange||(this.valueStart=e),this.updateUI()},t.prototype.setMax=function(e){this.max=e,this.updateUI()},t.prototype.getMin=function(){return this.min},t.prototype.getMax=function(){return this.max},t.prototype.getValue=function(){return this.value},t.prototype.setValue=function(e){if(this.isRange&&e<this.valueStart+this.minRange)throw new Error("end thumb value ("+e+") must be >= start thumb value ("+this.valueStart+") + min range ("+this.minRange+")");this.updateValue(e,ue.END)},t.prototype.getValueStart=function(){if(!this.isRange)throw new Error("`valueStart` is only applicable for range sliders.");return this.valueStart},t.prototype.setValueStart=function(e){if(!this.isRange)throw new Error("`valueStart` is only applicable for range sliders.");if(this.isRange&&e>this.value-this.minRange)throw new Error("start thumb value ("+e+") must be <= end thumb value ("+this.value+") - min range ("+this.minRange+")");this.updateValue(e,ue.START)},t.prototype.setStep=function(e){this.step=e,this.numDecimalPlaces=We(e),this.updateUI()},t.prototype.setMinRange=function(e){if(!this.isRange)throw new Error("`minRange` is only applicable for range sliders.");if(e<0)throw new Error("`minRange` must be non-negative. Current value: "+e);if(this.value-this.valueStart<e)throw new Error("start thumb value ("+this.valueStart+") and end thumb value ("+this.value+") must differ by at least "+e+".");this.minRange=e},t.prototype.setIsDiscrete=function(e){this.isDiscrete=e,this.updateValueIndicatorUI(),this.updateTickMarksUI()},t.prototype.getStep=function(){return this.step},t.prototype.getMinRange=function(){if(!this.isRange)throw new Error("`minRange` is only applicable for range sliders.");return this.minRange},t.prototype.setHasTickMarks=function(e){this.hasTickMarks=e,this.updateTickMarksUI()},t.prototype.getDisabled=function(){return this.isDisabled},t.prototype.setDisabled=function(e){this.isDisabled=e,e?(this.adapter.addClass(fe),this.isRange&&this.adapter.setInputAttribute(Te,"",ue.START),this.adapter.setInputAttribute(Te,"",ue.END)):(this.adapter.removeClass(fe),this.isRange&&this.adapter.removeInputAttribute(Te,ue.START),this.adapter.removeInputAttribute(Te,ue.END))},t.prototype.getIsRange=function(){return this.isRange},t.prototype.layout=function(e){var t=(void 0===e?{}:e).skipUpdateUI;this.rect=this.adapter.getBoundingClientRect(),this.isRange&&(this.startThumbKnobWidth=this.adapter.getThumbKnobWidth(ue.START),this.endThumbKnobWidth=this.adapter.getThumbKnobWidth(ue.END)),t||this.updateUI()},t.prototype.handleResize=function(){this.layout()},t.prototype.handleDown=function(e){if(!this.isDisabled){this.valueStartBeforeDownEvent=this.valueStart,this.valueBeforeDownEvent=this.value;var t=null!=e.clientX?e.clientX:e.targetTouches[0].clientX;this.downEventClientX=t;var i=this.mapClientXOnSliderScale(t);this.thumb=this.getThumbFromDownEvent(t,i),null!==this.thumb&&(this.handleDragStart(e,i,this.thumb),this.updateValue(i,this.thumb,{emitInputEvent:!0}))}},t.prototype.handleMove=function(e){if(!this.isDisabled){e.preventDefault();var t=null!=e.clientX?e.clientX:e.targetTouches[0].clientX,i=null!=this.thumb;if(this.thumb=this.getThumbFromMoveEvent(t),null!==this.thumb){var r=this.mapClientXOnSliderScale(t);i||(this.handleDragStart(e,r,this.thumb),this.adapter.emitDragStartEvent(r,this.thumb)),this.updateValue(r,this.thumb,{emitInputEvent:!0})}}},t.prototype.handleUp=function(){var e,t;if(!this.isDisabled&&null!==this.thumb){(null===(t=(e=this.adapter).shouldHideFocusStylesForPointerEvents)||void 0===t?void 0:t.call(e))&&this.handleInputBlur(this.thumb);var i=this.thumb===ue.START?this.valueStartBeforeDownEvent:this.valueBeforeDownEvent,r=this.thumb===ue.START?this.valueStart:this.value;i!==r&&this.adapter.emitChangeEvent(r,this.thumb),this.adapter.emitDragEndEvent(r,this.thumb),this.thumb=null}},t.prototype.handleThumbMouseenter=function(){this.isDiscrete&&this.isRange&&(this.adapter.addThumbClass(ye,ue.START),this.adapter.addThumbClass(ye,ue.END))},t.prototype.handleThumbMouseleave=function(){var e,t;this.isDiscrete&&this.isRange&&(!(null===(t=(e=this.adapter).shouldHideFocusStylesForPointerEvents)||void 0===t?void 0:t.call(e))&&(this.adapter.isInputFocused(ue.START)||this.adapter.isInputFocused(ue.END))||this.thumb||(this.adapter.removeThumbClass(ye,ue.START),this.adapter.removeThumbClass(ye,ue.END)))},t.prototype.handleMousedownOrTouchstart=function(e){var t=this,i="mousedown"===e.type?"mousemove":"touchmove";this.adapter.registerBodyEventHandler(i,this.moveListener);var r=function(){t.handleUp(),t.adapter.deregisterBodyEventHandler(i,t.moveListener),t.adapter.deregisterEventHandler("mouseup",r),t.adapter.deregisterEventHandler("touchend",r)};this.adapter.registerBodyEventHandler("mouseup",r),this.adapter.registerBodyEventHandler("touchend",r),this.handleDown(e)},t.prototype.handlePointerdown=function(e){0===e.button&&(null!=e.pointerId&&this.adapter.setPointerCapture(e.pointerId),this.adapter.registerEventHandler("pointermove",this.moveListener),this.handleDown(e))},t.prototype.handleInputChange=function(e){var t=Number(this.adapter.getInputValue(e));e===ue.START?this.setValueStart(t):this.setValue(t),this.adapter.emitChangeEvent(e===ue.START?this.valueStart:this.value,e),this.adapter.emitInputEvent(e===ue.START?this.valueStart:this.value,e)},t.prototype.handleInputFocus=function(e){if(this.adapter.addThumbClass(be,e),this.isDiscrete&&(this.adapter.addThumbClass(ye,e),this.isRange)){var t=e===ue.START?ue.END:ue.START;this.adapter.addThumbClass(ye,t)}},t.prototype.handleInputBlur=function(e){if(this.adapter.removeThumbClass(be,e),this.isDiscrete&&(this.adapter.removeThumbClass(ye,e),this.isRange)){var t=e===ue.START?ue.END:ue.START;this.adapter.removeThumbClass(ye,t)}},t.prototype.handleDragStart=function(e,t,i){var r,s;this.adapter.emitDragStartEvent(t,i),this.adapter.focusInput(i),(null===(s=(r=this.adapter).shouldHideFocusStylesForPointerEvents)||void 0===s?void 0:s.call(r))&&this.handleInputFocus(i),e.preventDefault()},t.prototype.getThumbFromDownEvent=function(e,t){if(!this.isRange)return ue.END;var i=this.adapter.getThumbBoundingClientRect(ue.START),r=this.adapter.getThumbBoundingClientRect(ue.END),s=e>=i.left&&e<=i.right,o=e>=r.left&&e<=r.right;return s&&o?null:s?ue.START:o?ue.END:t<this.valueStart?ue.START:t>this.value?ue.END:t-this.valueStart<=this.value-t?ue.START:ue.END},t.prototype.getThumbFromMoveEvent=function(e){if(null!==this.thumb)return this.thumb;if(null===this.downEventClientX)throw new Error("`downEventClientX` is null after move event.");return Math.abs(this.downEventClientX-e)<Ce?this.thumb:e<this.downEventClientX?this.adapter.isRTL()?ue.END:ue.START:this.adapter.isRTL()?ue.START:ue.END},t.prototype.updateUI=function(e){e?this.updateThumbAndInputAttributes(e):(this.updateThumbAndInputAttributes(ue.START),this.updateThumbAndInputAttributes(ue.END)),this.updateThumbAndTrackUI(e),this.updateValueIndicatorUI(e),this.updateTickMarksUI()},t.prototype.updateThumbAndInputAttributes=function(e){if(e){var t=this.isRange&&e===ue.START?this.valueStart:this.value,i=String(t);this.adapter.setInputAttribute($e,i,e),this.isRange&&e===ue.START?this.adapter.setInputAttribute(Me,String(t+this.minRange),ue.END):this.isRange&&e===ue.END&&this.adapter.setInputAttribute(Pe,String(t-this.minRange),ue.START),this.adapter.getInputValue(e)!==i&&this.adapter.setInputValue(i,e);var r=this.adapter.getValueToAriaValueTextFn();r&&this.adapter.setInputAttribute(Se,r(t,e),e)}},t.prototype.updateValueIndicatorUI=function(e){if(this.isDiscrete){var t=this.isRange&&e===ue.START?this.valueStart:this.value;this.adapter.setValueIndicatorText(t,e===ue.START?ue.START:ue.END),!e&&this.isRange&&this.adapter.setValueIndicatorText(this.valueStart,ue.START)}},t.prototype.updateTickMarksUI=function(){if(this.isDiscrete&&this.hasTickMarks){var e=(this.valueStart-this.min)/this.step,t=(this.value-this.valueStart)/this.step+1,i=(this.max-this.value)/this.step,r=Array.from({length:e}).fill(de.INACTIVE),s=Array.from({length:t}).fill(de.ACTIVE),o=Array.from({length:i}).fill(de.INACTIVE);this.adapter.updateTickMarks(r.concat(s).concat(o))}},t.prototype.mapClientXOnSliderScale=function(e){var t=(e-this.rect.left)/this.rect.width;this.adapter.isRTL()&&(t=1-t);var i=this.min+t*(this.max-this.min);return i===this.max||i===this.min?i:Number(this.quantize(i).toFixed(this.numDecimalPlaces))},t.prototype.quantize=function(e){var t=Math.round((e-this.min)/this.step);return this.min+t*this.step},t.prototype.updateValue=function(e,t,i){var r=(void 0===i?{}:i).emitInputEvent;if(e=this.clampValue(e,t),this.isRange&&t===ue.START){if(this.valueStart===e)return;this.valueStart=e}else{if(this.value===e)return;this.value=e}this.updateUI(t),r&&this.adapter.emitInputEvent(t===ue.START?this.valueStart:this.value,t)},t.prototype.clampValue=function(e,t){return e=Math.min(Math.max(e,this.min),this.max),this.isRange&&t===ue.START&&e>this.value-this.minRange?this.value-this.minRange:this.isRange&&t===ue.END&&e<this.valueStart+this.minRange?this.valueStart+this.minRange:e},t.prototype.updateThumbAndTrackUI=function(e){var t=this,i=this.max,r=this.min,s=(this.value-this.valueStart)/(i-r),o=s*this.rect.width,n=this.adapter.isRTL(),a=Fe?pe(window,"transform"):"transform";if(this.isRange){var l=this.adapter.isRTL()?(i-this.value)/(i-r)*this.rect.width:(this.valueStart-r)/(i-r)*this.rect.width,c=l+o;this.animFrame.request(me.SLIDER_UPDATE,(function(){!n&&e===ue.START||n&&e!==ue.START?(t.adapter.setTrackActiveStyleProperty("transform-origin","right"),t.adapter.setTrackActiveStyleProperty("left","auto"),t.adapter.setTrackActiveStyleProperty("right",t.rect.width-c+"px")):(t.adapter.setTrackActiveStyleProperty("transform-origin","left"),t.adapter.setTrackActiveStyleProperty("right","auto"),t.adapter.setTrackActiveStyleProperty("left",l+"px")),t.adapter.setTrackActiveStyleProperty(a,"scaleX("+s+")");var i=n?c:l,r=t.adapter.isRTL()?l:c;e!==ue.START&&e&&t.initialStylesRemoved||(t.adapter.setThumbStyleProperty(a,"translateX("+i+"px)",ue.START),t.alignValueIndicator(ue.START,i)),e!==ue.END&&e&&t.initialStylesRemoved||(t.adapter.setThumbStyleProperty(a,"translateX("+r+"px)",ue.END),t.alignValueIndicator(ue.END,r)),t.removeInitialStyles(n),t.updateOverlappingThumbsUI(i,r,e)}))}else this.animFrame.request(me.SLIDER_UPDATE,(function(){var e=n?t.rect.width-o:o;t.adapter.setThumbStyleProperty(a,"translateX("+e+"px)",ue.END),t.alignValueIndicator(ue.END,e),t.adapter.setTrackActiveStyleProperty(a,"scaleX("+s+")"),t.removeInitialStyles(n)}))},t.prototype.alignValueIndicator=function(e,t){if(this.isDiscrete){var i=this.adapter.getThumbBoundingClientRect(e).width/2,r=this.adapter.getValueIndicatorContainerWidth(e),s=this.adapter.getBoundingClientRect().width;r/2>t+i?(this.adapter.setThumbStyleProperty(Re,i+"px",e),this.adapter.setThumbStyleProperty(Ae,"auto",e),this.adapter.setThumbStyleProperty(Ie,"translateX(-50%)",e),this.adapter.setThumbStyleProperty(Ne,"0",e),this.adapter.setThumbStyleProperty(De,"auto",e),this.adapter.setThumbStyleProperty(Oe,"none",e)):r/2>s-t+i?(this.adapter.setThumbStyleProperty(Re,"auto",e),this.adapter.setThumbStyleProperty(Ae,i+"px",e),this.adapter.setThumbStyleProperty(Ie,"translateX(50%)",e),this.adapter.setThumbStyleProperty(Ne,"auto",e),this.adapter.setThumbStyleProperty(De,"0",e),this.adapter.setThumbStyleProperty(Oe,"none",e)):(this.adapter.setThumbStyleProperty(Re,"50%",e),this.adapter.setThumbStyleProperty(Ae,"auto",e),this.adapter.setThumbStyleProperty(Ie,"translateX(-50%)",e),this.adapter.setThumbStyleProperty(Ne,"50%",e),this.adapter.setThumbStyleProperty(De,"auto",e),this.adapter.setThumbStyleProperty(Oe,"translateX(-50%)",e))}},t.prototype.removeInitialStyles=function(e){if(!this.initialStylesRemoved){var t=e?"right":"left";this.adapter.removeThumbStyleProperty(t,ue.END),this.isRange&&this.adapter.removeThumbStyleProperty(t,ue.START),this.initialStylesRemoved=!0,this.resetTrackAndThumbAnimation()}},t.prototype.resetTrackAndThumbAnimation=function(){var e=this;if(this.isDiscrete){var t=Fe?pe(window,"transition"):"transition",i="none 0s ease 0s";this.adapter.setThumbStyleProperty(t,i,ue.END),this.isRange&&this.adapter.setThumbStyleProperty(t,i,ue.START),this.adapter.setTrackActiveStyleProperty(t,i),requestAnimationFrame((function(){e.adapter.removeThumbStyleProperty(t,ue.END),e.adapter.removeTrackActiveStyleProperty(t),e.isRange&&e.adapter.removeThumbStyleProperty(t,ue.START)}))}},t.prototype.updateOverlappingThumbsUI=function(e,t,i){var r=!1;if(this.adapter.isRTL()){var s=e-this.startThumbKnobWidth/2;r=t+this.endThumbKnobWidth/2>=s}else{r=e+this.startThumbKnobWidth/2>=t-this.endThumbKnobWidth/2}r?(this.adapter.addThumbClass(_e,i||ue.END),this.adapter.removeThumbClass(_e,i===ue.START?ue.END:ue.START)):(this.adapter.removeThumbClass(_e,ue.START),this.adapter.removeThumbClass(_e,ue.END))},t.prototype.convertAttributeValueToNumber=function(e,t){if(null===e)throw new Error("MDCSliderFoundation: `"+t+"` must be non-null.");var i=Number(e);if(isNaN(i))throw new Error("MDCSliderFoundation: `"+t+"` value is `"+e+"`, but must be a number.");return i},t.prototype.validateProperties=function(e){var t=e.min,i=e.max,r=e.value,s=e.valueStart,o=e.step,n=e.minRange;if(t>=i)throw new Error("MDCSliderFoundation: min must be strictly less than max. Current: [min: "+t+", max: "+i+"]");if(o<=0)throw new Error("MDCSliderFoundation: step must be a positive number. Current step: "+o);if(this.isRange){if(r<t||r>i||s<t||s>i)throw new Error("MDCSliderFoundation: values must be in [min, max] range. Current values: [start value: "+s+", end value: "+r+", min: "+t+", max: "+i+"]");if(s>r)throw new Error("MDCSliderFoundation: start value must be <= end value. Current values: [start value: "+s+", end value: "+r+"]");if(n<0)throw new Error("MDCSliderFoundation: minimum range must be non-negative. Current min range: "+n);if(r-s<n)throw new Error("MDCSliderFoundation: start value and end value must differ by at least "+n+". Current values: [start value: "+s+", end value: "+r+"]");var a=(s-t)/o,l=(r-t)/o;if(!Number.isInteger(parseFloat(a.toFixed(6)))||!Number.isInteger(parseFloat(l.toFixed(6))))throw new Error("MDCSliderFoundation: Slider values must be valid based on the step value ("+o+"). Current values: [start value: "+s+", end value: "+r+", min: "+t+"]")}else{if(r<t||r>i)throw new Error("MDCSliderFoundation: value must be in [min, max] range. Current values: [value: "+r+", min: "+t+", max: "+i+"]");l=(r-t)/o;if(!Number.isInteger(parseFloat(l.toFixed(6))))throw new Error("MDCSliderFoundation: Slider value must be valid based on the step value ("+o+"). Current value: "+r)}},t.prototype.registerEventHandlers=function(){this.adapter.registerWindowEventHandler("resize",this.resizeListener),t.SUPPORTS_POINTER_EVENTS?(this.adapter.registerEventHandler("pointerdown",this.pointerdownListener),this.adapter.registerEventHandler("pointerup",this.pointerupListener)):(this.adapter.registerEventHandler("mousedown",this.mousedownOrTouchstartListener),this.adapter.registerEventHandler("touchstart",this.mousedownOrTouchstartListener)),this.isRange&&(this.adapter.registerThumbEventHandler(ue.START,"mouseenter",this.thumbMouseenterListener),this.adapter.registerThumbEventHandler(ue.START,"mouseleave",this.thumbMouseleaveListener),this.adapter.registerInputEventHandler(ue.START,"change",this.inputStartChangeListener),this.adapter.registerInputEventHandler(ue.START,"focus",this.inputStartFocusListener),this.adapter.registerInputEventHandler(ue.START,"blur",this.inputStartBlurListener)),this.adapter.registerThumbEventHandler(ue.END,"mouseenter",this.thumbMouseenterListener),this.adapter.registerThumbEventHandler(ue.END,"mouseleave",this.thumbMouseleaveListener),this.adapter.registerInputEventHandler(ue.END,"change",this.inputEndChangeListener),this.adapter.registerInputEventHandler(ue.END,"focus",this.inputEndFocusListener),this.adapter.registerInputEventHandler(ue.END,"blur",this.inputEndBlurListener)},t.prototype.deregisterEventHandlers=function(){this.adapter.deregisterWindowEventHandler("resize",this.resizeListener),t.SUPPORTS_POINTER_EVENTS?(this.adapter.deregisterEventHandler("pointerdown",this.pointerdownListener),this.adapter.deregisterEventHandler("pointerup",this.pointerupListener)):(this.adapter.deregisterEventHandler("mousedown",this.mousedownOrTouchstartListener),this.adapter.deregisterEventHandler("touchstart",this.mousedownOrTouchstartListener)),this.isRange&&(this.adapter.deregisterThumbEventHandler(ue.START,"mouseenter",this.thumbMouseenterListener),this.adapter.deregisterThumbEventHandler(ue.START,"mouseleave",this.thumbMouseleaveListener),this.adapter.deregisterInputEventHandler(ue.START,"change",this.inputStartChangeListener),this.adapter.deregisterInputEventHandler(ue.START,"focus",this.inputStartFocusListener),this.adapter.deregisterInputEventHandler(ue.START,"blur",this.inputStartBlurListener)),this.adapter.deregisterThumbEventHandler(ue.END,"mouseenter",this.thumbMouseenterListener),this.adapter.deregisterThumbEventHandler(ue.END,"mouseleave",this.thumbMouseleaveListener),this.adapter.deregisterInputEventHandler(ue.END,"change",this.inputEndChangeListener),this.adapter.deregisterInputEventHandler(ue.END,"focus",this.inputEndFocusListener),this.adapter.deregisterInputEventHandler(ue.END,"blur",this.inputEndBlurListener)},t.prototype.handlePointerup=function(){this.handleUp(),this.adapter.deregisterEventHandler("pointermove",this.moveListener)},t.SUPPORTS_POINTER_EVENTS=Fe&&Boolean(window.PointerEvent)&&!(["iPad Simulator","iPhone Simulator","iPod Simulator","iPad","iPhone","iPod"].includes(navigator.platform)||navigator.userAgent.includes("Mac")&&"ontouchend"in document),t}(f);function We(e){var t=/(?:\.(\d+))?(?:[eE]([+\-]?\d+))?$/.exec(String(e));if(!t)return 0;var i=t[1]||"",r=t[2]||0;return Math.max(0,("0"===i?0:i.length)-Number(r))}
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */class Be extends x{constructor(){super(...arguments),this.mdcFoundationClass=ze,this.disabled=!1,this.min=0,this.max=100,this.valueEnd=0,this.name="",this.step=1,this.withTickMarks=!1,this.discrete=!1,this.tickMarks=[],this.trackTransformOriginStyle="",this.trackLeftStyle="",this.trackRightStyle="",this.trackTransitionStyle="",this.endThumbWithIndicator=!1,this.endThumbTop=!1,this.shouldRenderEndRipple=!1,this.endThumbTransformStyle="",this.endThumbTransitionStyle="",this.endThumbCssProperties={},this.valueToAriaTextTransform=null,this.valueToValueIndicatorTransform=e=>`${e}`,this.boundMoveListener=null,this.endRippleHandlers=new w((()=>(this.shouldRenderEndRipple=!0,this.endRipple)))}update(e){if(e.has("valueEnd")&&this.mdcFoundation){this.mdcFoundation.setValue(this.valueEnd);const e=this.mdcFoundation.getValue();e!==this.valueEnd&&(this.valueEnd=e)}e.has("discrete")&&(this.discrete||(this.tickMarks=[])),super.update(e)}render(){return this.renderRootEl(k`
      ${this.renderStartInput()}
      ${this.renderEndInput()}
      ${this.renderTrack()}
      ${this.renderTickMarks()}
      ${this.renderStartThumb()}
      ${this.renderEndThumb()}`)}renderRootEl(e){const t=C({"mdc-slider--disabled":this.disabled,"mdc-slider--discrete":this.discrete});return k`
    <div
        class="mdc-slider ${t}"
        @pointerdown=${this.onPointerdown}
        @pointerup=${this.onPointerup}
        @contextmenu=${this.onContextmenu}>
      ${e}
    </div>`}renderStartInput(){return S}renderEndInput(){var e;return k`
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
          aria-label=${T(this.ariaLabel)}
          aria-labelledby=${T(this.ariaLabelledBy)}
          aria-describedby=${T(this.ariaDescribedBy)}
          aria-valuetext=${T(null===(e=this.valueToAriaTextTransform)||void 0===e?void 0:e.call(this,this.valueEnd))}>
    `}renderTrack(){return S}renderTickMarks(){return this.withTickMarks?k`
      <div class="mdc-slider__tick-marks">
        ${this.tickMarks.map((e=>{const t=e===de.ACTIVE;return k`<div class="${t?"mdc-slider__tick-mark--active":"mdc-slider__tick-mark--inactive"}"></div>`}))}
      </div>`:S}renderStartThumb(){return S}renderEndThumb(){const e=C({"mdc-slider__thumb--with-indicator":this.endThumbWithIndicator,"mdc-slider__thumb--top":this.endThumbTop}),t=M(Object.assign({"-webkit-transform":this.endThumbTransformStyle,transform:this.endThumbTransformStyle,"-webkit-transition":this.endThumbTransitionStyle,transition:this.endThumbTransitionStyle,left:this.endThumbTransformStyle||"rtl"===getComputedStyle(this).direction?"":`calc(${(this.valueEnd-this.min)/(this.max-this.min)*100}% - 24px)`,right:this.endThumbTransformStyle||"rtl"!==getComputedStyle(this).direction?"":`calc(${(this.valueEnd-this.min)/(this.max-this.min)*100}% - 24px)`},this.endThumbCssProperties)),i=this.shouldRenderEndRipple?k`<mwc-ripple class="ripple" unbounded></mwc-ripple>`:S;return k`
      <div
          class="mdc-slider__thumb end ${e}"
          style=${t}
          @mouseenter=${this.onEndMouseenter}
          @mouseleave=${this.onEndMouseleave}>
        ${i}
        ${this.renderValueIndicator(this.valueToValueIndicatorTransform(this.valueEnd))}
        <div class="mdc-slider__thumb-knob"></div>
      </div>
    `}renderValueIndicator(e){return this.discrete?k`
    <div class="mdc-slider__value-indicator-container" aria-hidden="true">
      <div class="mdc-slider__value-indicator">
        <span class="mdc-slider__value-indicator-text">
          ${e}
        </span>
      </div>
    </div>`:S}disconnectedCallback(){super.disconnectedCallback(),this.mdcFoundation&&this.mdcFoundation.destroy()}createAdapter(){}async firstUpdated(){super.firstUpdated(),await this.layout(!0)}updated(e){super.updated(e),this.mdcFoundation&&(e.has("disabled")&&this.mdcFoundation.setDisabled(this.disabled),e.has("min")&&this.mdcFoundation.setMin(this.min),e.has("max")&&this.mdcFoundation.setMax(this.max),e.has("step")&&this.mdcFoundation.setStep(this.step),e.has("discrete")&&this.mdcFoundation.setIsDiscrete(this.discrete),e.has("withTickMarks")&&this.mdcFoundation.setHasTickMarks(this.withTickMarks))}async layout(e=!1){var t;null===(t=this.mdcFoundation)||void 0===t||t.layout({skipUpdateUI:e}),this.requestUpdate(),await this.updateComplete}onEndChange(e){var t;this.valueEnd=Number(e.target.value),null===(t=this.mdcFoundation)||void 0===t||t.handleInputChange(ue.END)}onEndFocus(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleInputFocus(ue.END),this.endRippleHandlers.startFocus()}onEndBlur(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleInputBlur(ue.END),this.endRippleHandlers.endFocus()}onEndMouseenter(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleThumbMouseenter(),this.endRippleHandlers.startHover()}onEndMouseleave(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleThumbMouseleave(),this.endRippleHandlers.endHover()}onPointerdown(e){this.layout(),this.mdcFoundation&&(this.mdcFoundation.handlePointerdown(e),this.boundMoveListener=this.mdcFoundation.handleMove.bind(this.mdcFoundation),this.mdcRoot.addEventListener("pointermove",this.boundMoveListener))}onPointerup(){this.mdcFoundation&&(this.mdcFoundation.handleUp(),this.boundMoveListener&&(this.mdcRoot.removeEventListener("pointermove",this.boundMoveListener),this.boundMoveListener=null))}onContextmenu(e){e.preventDefault()}setFormData(e){this.name&&e.append(this.name,`${this.valueEnd}`)}}e([g("input.end")],Be.prototype,"formElement",void 0),e([g(".mdc-slider")],Be.prototype,"mdcRoot",void 0),e([g(".end.mdc-slider__thumb")],Be.prototype,"endThumb",void 0),e([g(".end.mdc-slider__thumb .mdc-slider__thumb-knob")],Be.prototype,"endThumbKnob",void 0),e([g(".end.mdc-slider__thumb .mdc-slider__value-indicator-container")],Be.prototype,"endValueIndicatorContainer",void 0),e([v(".end .ripple")],Be.prototype,"endRipple",void 0),e([b({type:Boolean,reflect:!0})],Be.prototype,"disabled",void 0),e([b({type:Number})],Be.prototype,"min",void 0),e([b({type:Number})],Be.prototype,"max",void 0),e([b({type:Number})],Be.prototype,"valueEnd",void 0),e([b({type:String})],Be.prototype,"name",void 0),e([b({type:Number})],Be.prototype,"step",void 0),e([b({type:Boolean})],Be.prototype,"withTickMarks",void 0),e([b({type:Boolean})],Be.prototype,"discrete",void 0),e([_()],Be.prototype,"tickMarks",void 0),e([_()],Be.prototype,"trackTransformOriginStyle",void 0),e([_()],Be.prototype,"trackLeftStyle",void 0),e([_()],Be.prototype,"trackRightStyle",void 0),e([_()],Be.prototype,"trackTransitionStyle",void 0),e([_()],Be.prototype,"endThumbWithIndicator",void 0),e([_()],Be.prototype,"endThumbTop",void 0),e([_()],Be.prototype,"shouldRenderEndRipple",void 0),e([_()],Be.prototype,"endThumbTransformStyle",void 0),e([_()],Be.prototype,"endThumbTransitionStyle",void 0),e([_()],Be.prototype,"endThumbCssProperties",void 0),e([y,b({type:String,attribute:"aria-label"})],Be.prototype,"ariaLabel",void 0),e([y,b({type:String,attribute:"aria-labelledby"})],Be.prototype,"ariaLabelledBy",void 0),e([y,b({type:String,attribute:"aria-describedby"})],Be.prototype,"ariaDescribedBy",void 0);
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
class je extends Be{get value(){return this.valueEnd}set value(e){this.valueEnd=e}renderTrack(){const e=M({"transform-origin":this.trackTransformOriginStyle,left:this.trackLeftStyle,right:this.trackRightStyle,"-webkit-transform":`scaleX(${(this.valueEnd-this.min)/(this.max-this.min)})`,transform:`scaleX(${(this.valueEnd-this.min)/(this.max-this.min)})`,"-webkit-transition":this.trackTransitionStyle,transition:this.trackTransitionStyle});return k`
      <div class="mdc-slider__track">
        <div class="mdc-slider__track--inactive"></div>
        <div class="mdc-slider__track--active">
          <div
              class="mdc-slider__track--active_fill"
              style=${e}>
          </div>
        </div>
      </div>`}createAdapter(){return{addClass:e=>{if("mdc-slider--disabled"===e)this.disabled=!0},removeClass:e=>{if("mdc-slider--disabled"===e)this.disabled=!1},hasClass:e=>{switch(e){case"mdc-slider--disabled":return this.disabled;case"mdc-slider--discrete":return this.discrete;default:return!1}},addThumbClass:(e,t)=>{if(t!==ue.START&&"mdc-slider__thumb--with-indicator"===e)this.endThumbWithIndicator=!0},removeThumbClass:(e,t)=>{if(t!==ue.START&&"mdc-slider__thumb--with-indicator"===e)this.endThumbWithIndicator=!1},registerEventHandler:()=>{},deregisterEventHandler:()=>{},registerBodyEventHandler:(e,t)=>{document.body.addEventListener(e,t)},deregisterBodyEventHandler:(e,t)=>{document.body.removeEventListener(e,t)},registerInputEventHandler:(e,t,i)=>{e!==ue.START&&this.formElement.addEventListener(t,i)},deregisterInputEventHandler:(e,t,i)=>{e!==ue.START&&this.formElement.removeEventListener(t,i)},registerThumbEventHandler:()=>{},deregisterThumbEventHandler:()=>{},registerWindowEventHandler:(e,t)=>{window.addEventListener(e,t)},deregisterWindowEventHandler:(e,t)=>{window.addEventListener(e,t)},emitChangeEvent:(e,t)=>{if(t===ue.START)return;const i=new CustomEvent("change",{bubbles:!0,composed:!0,detail:{value:e,thumb:t}});this.dispatchEvent(i)},emitDragEndEvent:(e,t)=>{t!==ue.START&&this.endRippleHandlers.endPress()},emitDragStartEvent:(e,t)=>{t!==ue.START&&this.endRippleHandlers.startPress()},emitInputEvent:(e,t)=>{if(t===ue.START)return;const i=new CustomEvent("input",{bubbles:!0,composed:!0,detail:{value:e,thumb:t}});this.dispatchEvent(i)},focusInput:e=>{e!==ue.START&&this.formElement.focus()},getAttribute:()=>"",getBoundingClientRect:()=>this.mdcRoot.getBoundingClientRect(),getInputAttribute:(e,t)=>{if(t===ue.START)return null;switch(e){case"min":return this.min.toString();case"max":return this.max.toString();case"value":return this.valueEnd.toString();case"step":return this.step.toString();default:return null}},getInputValue:e=>e===ue.START?"":this.valueEnd.toString(),getThumbBoundingClientRect:e=>e===ue.START?this.getBoundingClientRect():this.endThumb.getBoundingClientRect(),getThumbKnobWidth:e=>e===ue.START?0:this.endThumbKnob.getBoundingClientRect().width,getValueIndicatorContainerWidth:e=>e===ue.START?0:this.endValueIndicatorContainer.getBoundingClientRect().width,getValueToAriaValueTextFn:()=>this.valueToAriaTextTransform,isInputFocused:e=>{if(e===ue.START)return!1;const t=P();return t[t.length-1]===this.formElement},isRTL:()=>"rtl"===getComputedStyle(this).direction,setInputAttribute:(e,t,i)=>{ue.START},removeInputAttribute:e=>{},setThumbStyleProperty:(e,t,i)=>{if(i!==ue.START)switch(e){case"transform":case"-webkit-transform":this.endThumbTransformStyle=t;break;case"transition":case"-webkit-transition":this.endThumbTransitionStyle=t;break;default:e.startsWith("--")&&(this.endThumbCssProperties[e]=t)}},removeThumbStyleProperty:(e,t)=>{if(t!==ue.START)switch(e){case"left":case"right":break;case"transition":case"-webkit-transition":this.endThumbTransitionStyle=""}},setTrackActiveStyleProperty:(e,t)=>{switch(e){case"transform-origin":this.trackTransformOriginStyle=t;break;case"left":this.trackLeftStyle=t;break;case"right":this.trackRightStyle=t;break;case"transform":case"-webkit-transform":break;case"transition":case"-webkit-transition":this.trackTransitionStyle=t}},removeTrackActiveStyleProperty:e=>{switch(e){case"transition":case"-webkit-transition":this.trackTransitionStyle=""}},setInputValue:(e,t)=>{t!==ue.START&&(this.valueEnd=Number(e))},setPointerCapture:e=>{this.mdcRoot.setPointerCapture(e)},setValueIndicatorText:()=>{},updateTickMarks:e=>{this.tickMarks=e}}}}e([b({type:Number})],je.prototype,"value",null);
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
let He=class extends je{};He.styles=[ce],He=e([$("mwc-slider")],He);let Ue=class extends r{static get styles(){return[s,o,n,a,l,c`
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
      `]}render(){return d`
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
    `}constructor(){super(),this.editable=!1,this.pin=!1,this.markers=!1,this.marker_limit=30,this.disabled=!1;new IntersectionObserver(((e,t)=>{e.forEach((e=>{e.intersectionRatio>0&&(this.value!==this.slider.value&&(this.slider.value=this.value),this.slider.layout())}))}),{}).observe(this)}firstUpdated(){this.editable&&(this.textfield.style.display="flex"),this.checkMarkerDisplay()}update(e){Array.from(e.keys()).some((e=>["value","min","max"].includes(e)))&&this.min==this.max&&(this.max=this.max+1,this.value=this.min,this.disabled=!0),super.update(e)}updated(e){e.forEach(((e,t)=>{["min","max","step"].includes(t)&&this.checkMarkerDisplay()}))}syncToText(){this.value=this.slider.value}syncToSlider(){this.textfield.step=this.step;const e=Math.round(this.textfield.value/this.step)*this.step;var t;this.textfield.value=e.toFixed((t=this.step,Math.floor(t)===t?0:t.toString().split(".")[1].length||0)),this.textfield.value>this.max&&(this.textfield.value=this.max),this.textfield.value<this.min&&(this.textfield.value=this.min),this.value=this.textfield.value;const i=new CustomEvent("change",{detail:{}});this.dispatchEvent(i)}checkMarkerDisplay(){this.markers&&(this.max-this.min)/this.step>this.marker_limit&&this.slider.removeAttribute("markers")}};
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
function Ge(e,t,i){var r=function(e,t){var i=new Map;Ve.has(e)||Ve.set(e,{isEnabled:!0,getObservers:function(e){var t=i.get(e)||[];return i.has(e)||i.set(e,t),t},installedProperties:new Set});var r=Ve.get(e);if(r.installedProperties.has(t))return r;var s=function(e,t){var i,r=e;for(;r&&!(i=Object.getOwnPropertyDescriptor(r,t));)r=Object.getPrototypeOf(r);return i}(e,t)||{configurable:!0,enumerable:!0,value:e[t],writable:!0},o=p({},s),n=s.get,a=s.set;if("value"in s){delete o.value,delete o.writable;var l=s.value;n=function(){return l},s.writable&&(a=function(e){l=e})}n&&(o.get=function(){return n.call(this)});a&&(o.set=function(e){var i,s,o=n?n.call(this):e;if(a.call(this,e),r.isEnabled&&(!n||e!==o))try{for(var l=L(r.getObservers(t)),c=l.next();!c.done;c=l.next()){(0,c.value)(e,o)}}catch(e){i={error:e}}finally{try{c&&!c.done&&(s=l.return)&&s.call(l)}finally{if(i)throw i.error}}});return r.installedProperties.add(t),Object.defineProperty(e,t,o),r}(e,t),s=r.getObservers(t);return s.push(i),function(){s.splice(s.indexOf(i),1)}}e([t({type:Number})],Ue.prototype,"step",void 0),e([t({type:Number})],Ue.prototype,"value",void 0),e([t({type:Number})],Ue.prototype,"max",void 0),e([t({type:Number})],Ue.prototype,"min",void 0),e([t({type:String})],Ue.prototype,"prefix",void 0),e([t({type:String})],Ue.prototype,"suffix",void 0),e([t({type:Boolean})],Ue.prototype,"editable",void 0),e([t({type:Boolean})],Ue.prototype,"pin",void 0),e([t({type:Boolean})],Ue.prototype,"markers",void 0),e([t({type:Number})],Ue.prototype,"marker_limit",void 0),e([t({type:Boolean})],Ue.prototype,"disabled",void 0),e([E("#slider",!0)],Ue.prototype,"slider",void 0),e([E("#textfield",!0)],Ue.prototype,"textfield",void 0),Ue=e([i("lablup-slider")],Ue);var Ve=new WeakMap;
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
var qe,Ze,Ke=function(e){function t(t){var i=e.call(this,t)||this;return i.unobserves=new Set,i}return h(t,e),t.prototype.destroy=function(){e.prototype.destroy.call(this),this.unobserve()},t.prototype.observe=function(e,t){var i,r,s=this,o=[];try{for(var n=L(Object.keys(t)),a=n.next();!a.done;a=n.next()){var l=a.value,c=t[l].bind(this);o.push(this.observeProperty(e,l,c))}}catch(e){i={error:e}}finally{try{a&&!a.done&&(r=n.return)&&r.call(n)}finally{if(i)throw i.error}}var d=function(){var e,t;try{for(var i=L(o),r=i.next();!r.done;r=i.next()){(0,r.value)()}}catch(t){e={error:t}}finally{try{r&&!r.done&&(t=i.return)&&t.call(i)}finally{if(e)throw e.error}}s.unobserves.delete(d)};return this.unobserves.add(d),d},t.prototype.observeProperty=function(e,t,i){return Ge(e,t,i)},t.prototype.setObserversEnabled=function(e,t){!function(e,t){var i=Ve.get(e);i&&(i.isEnabled=t)}(e,t)},t.prototype.unobserve=function(){var e,t;try{for(var i=L(R([],A(this.unobserves))),r=i.next();!r.done;r=i.next()){(0,r.value)()}}catch(t){e={error:t}}finally{try{r&&!r.done&&(t=i.return)&&t.call(i)}finally{if(e)throw e.error}}},t}(f);
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
 */!function(e){e.PROCESSING="mdc-switch--processing",e.SELECTED="mdc-switch--selected",e.UNSELECTED="mdc-switch--unselected"}(qe||(qe={})),function(e){e.RIPPLE=".mdc-switch__ripple"}(Ze||(Ze={}));
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
var Xe=function(e){function t(t){var i=e.call(this,t)||this;return i.handleClick=i.handleClick.bind(i),i}return h(t,e),t.prototype.init=function(){this.observe(this.adapter.state,{disabled:this.stopProcessingIfDisabled,processing:this.stopProcessingIfDisabled})},t.prototype.handleClick=function(){this.adapter.state.disabled||(this.adapter.state.selected=!this.adapter.state.selected)},t.prototype.stopProcessingIfDisabled=function(){this.adapter.state.disabled&&(this.adapter.state.processing=!1)},t}(Ke);!function(e){function t(){return null!==e&&e.apply(this,arguments)||this}h(t,e),t.prototype.init=function(){e.prototype.init.call(this),this.observe(this.adapter.state,{disabled:this.onDisabledChange,processing:this.onProcessingChange,selected:this.onSelectedChange})},t.prototype.initFromDOM=function(){this.setObserversEnabled(this.adapter.state,!1),this.adapter.state.selected=this.adapter.hasClass(qe.SELECTED),this.onSelectedChange(),this.adapter.state.disabled=this.adapter.isDisabled(),this.adapter.state.processing=this.adapter.hasClass(qe.PROCESSING),this.setObserversEnabled(this.adapter.state,!0),this.stopProcessingIfDisabled()},t.prototype.onDisabledChange=function(){this.adapter.setDisabled(this.adapter.state.disabled)},t.prototype.onProcessingChange=function(){this.toggleClass(this.adapter.state.processing,qe.PROCESSING)},t.prototype.onSelectedChange=function(){this.adapter.setAriaChecked(String(this.adapter.state.selected)),this.toggleClass(this.adapter.state.selected,qe.SELECTED),this.toggleClass(!this.adapter.state.selected,qe.UNSELECTED)},t.prototype.toggleClass=function(e,t){e?this.adapter.addClass(t):this.adapter.removeClass(t)}}(Xe);
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
class Ye extends x{constructor(){super(...arguments),this.processing=!1,this.selected=!1,this.ariaLabel="",this.ariaLabelledBy="",this.shouldRenderRipple=!1,this.rippleHandlers=new w((()=>(this.shouldRenderRipple=!0,this.ripple))),this.name="",this.value="on",this.mdcFoundationClass=Xe}setFormData(e){this.name&&this.selected&&e.append(this.name,this.value)}click(){var e,t;this.disabled||(null===(e=this.mdcRoot)||void 0===e||e.focus(),null===(t=this.mdcRoot)||void 0===t||t.click())}render(){return k`
      <button
        type="button"
        class="mdc-switch ${C(this.getRenderClasses())}"
        role="switch"
        aria-checked="${this.selected}"
        aria-label="${T(this.ariaLabel||void 0)}"
        aria-labelledby="${T(this.ariaLabelledBy||void 0)}"
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
    `}getRenderClasses(){return{"mdc-switch--processing":this.processing,"mdc-switch--selected":this.selected,"mdc-switch--unselected":!this.selected}}renderHandle(){return k`
      <div class="mdc-switch__handle">
        ${this.renderShadow()}
        ${this.renderRipple()}
        <div class="mdc-switch__icons">
          ${this.renderOnIcon()}
          ${this.renderOffIcon()}
        </div>
      </div>
    `}renderShadow(){return k`
      <div class="mdc-switch__shadow">
        <div class="mdc-elevation-overlay"></div>
      </div>
    `}renderRipple(){return this.shouldRenderRipple?k`
        <div class="mdc-switch__ripple">
          <mwc-ripple
            internalUseStateLayerCustomProperties
            .disabled="${this.disabled}"
            unbounded>
          </mwc-ripple>
        </div>
      `:k``}renderOnIcon(){return k`
      <svg class="mdc-switch__icon mdc-switch__icon--on" viewBox="0 0 24 24">
        <path d="M19.69,5.23L8.96,15.96l-4.23-4.23L2.96,13.5l6,6L21.46,7L19.69,5.23z" />
      </svg>
    `}renderOffIcon(){return k`
      <svg class="mdc-switch__icon mdc-switch__icon--off" viewBox="0 0 24 24">
        <path d="M20 13H4v-2h16v2z" />
      </svg>
    `}handleClick(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleClick()}handleFocus(){this.rippleHandlers.startFocus()}handleBlur(){this.rippleHandlers.endFocus()}handlePointerDown(e){e.target.setPointerCapture(e.pointerId),this.rippleHandlers.startPress(e)}handlePointerUp(){this.rippleHandlers.endPress()}handlePointerEnter(){this.rippleHandlers.startHover()}handlePointerLeave(){this.rippleHandlers.endHover()}createAdapter(){return{state:this}}}e([b({type:Boolean})],Ye.prototype,"processing",void 0),e([b({type:Boolean})],Ye.prototype,"selected",void 0),e([y,b({type:String,attribute:"aria-label"})],Ye.prototype,"ariaLabel",void 0),e([y,b({type:String,attribute:"aria-labelledby"})],Ye.prototype,"ariaLabelledBy",void 0),e([v("mwc-ripple")],Ye.prototype,"ripple",void 0),e([_()],Ye.prototype,"shouldRenderRipple",void 0),e([b({type:String,reflect:!0})],Ye.prototype,"name",void 0),e([b({type:String})],Ye.prototype,"value",void 0),e([g("input")],Ye.prototype,"formElement",void 0),e([g(".mdc-switch")],Ye.prototype,"mdcRoot",void 0),e([I({passive:!0})],Ye.prototype,"handlePointerDown",null);
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-LIcense-Identifier: Apache-2.0
 */
const Je=u`.mdc-elevation-overlay{position:absolute;border-radius:inherit;pointer-events:none;opacity:0;opacity:var(--mdc-elevation-overlay-opacity, 0);transition:opacity 280ms cubic-bezier(0.4, 0, 0.2, 1);background-color:#fff;background-color:var(--mdc-elevation-overlay-color, #fff)}.mdc-switch{align-items:center;background:none;border:none;cursor:pointer;display:inline-flex;flex-shrink:0;margin:0;outline:none;overflow:visible;padding:0;position:relative}.mdc-switch:disabled{cursor:default;pointer-events:none}.mdc-switch__track{overflow:hidden;position:relative;width:100%}.mdc-switch__track::before,.mdc-switch__track::after{border:1px solid transparent;border-radius:inherit;box-sizing:border-box;content:"";height:100%;left:0;position:absolute;width:100%}@media screen and (forced-colors: active){.mdc-switch__track::before,.mdc-switch__track::after{border-color:currentColor}}.mdc-switch__track::before{transition:transform 75ms 0ms cubic-bezier(0, 0, 0.2, 1);transform:translateX(0)}.mdc-switch__track::after{transition:transform 75ms 0ms cubic-bezier(0.4, 0, 0.6, 1);transform:translateX(-100%)}[dir=rtl] .mdc-switch__track::after,.mdc-switch__track[dir=rtl]::after{transform:translateX(100%)}.mdc-switch--selected .mdc-switch__track::before{transition:transform 75ms 0ms cubic-bezier(0.4, 0, 0.6, 1);transform:translateX(100%)}[dir=rtl] .mdc-switch--selected .mdc-switch__track::before,.mdc-switch--selected .mdc-switch__track[dir=rtl]::before{transform:translateX(-100%)}.mdc-switch--selected .mdc-switch__track::after{transition:transform 75ms 0ms cubic-bezier(0, 0, 0.2, 1);transform:translateX(0)}.mdc-switch__handle-track{height:100%;pointer-events:none;position:absolute;top:0;transition:transform 75ms 0ms cubic-bezier(0.4, 0, 0.2, 1);left:0;right:auto;transform:translateX(0)}[dir=rtl] .mdc-switch__handle-track,.mdc-switch__handle-track[dir=rtl]{left:auto;right:0}.mdc-switch--selected .mdc-switch__handle-track{transform:translateX(100%)}[dir=rtl] .mdc-switch--selected .mdc-switch__handle-track,.mdc-switch--selected .mdc-switch__handle-track[dir=rtl]{transform:translateX(-100%)}.mdc-switch__handle{display:flex;pointer-events:auto;position:absolute;top:50%;transform:translateY(-50%);left:0;right:auto}[dir=rtl] .mdc-switch__handle,.mdc-switch__handle[dir=rtl]{left:auto;right:0}.mdc-switch__handle::before,.mdc-switch__handle::after{border:1px solid transparent;border-radius:inherit;box-sizing:border-box;content:"";width:100%;height:100%;left:0;position:absolute;top:0;transition:background-color 75ms 0ms cubic-bezier(0.4, 0, 0.2, 1),border-color 75ms 0ms cubic-bezier(0.4, 0, 0.2, 1);z-index:-1}@media screen and (forced-colors: active){.mdc-switch__handle::before,.mdc-switch__handle::after{border-color:currentColor}}.mdc-switch__shadow{border-radius:inherit;bottom:0;left:0;position:absolute;right:0;top:0}.mdc-elevation-overlay{bottom:0;left:0;right:0;top:0}.mdc-switch__ripple{left:50%;position:absolute;top:50%;transform:translate(-50%, -50%);z-index:-1}.mdc-switch:disabled .mdc-switch__ripple{display:none}.mdc-switch__icons{height:100%;position:relative;width:100%;z-index:1}.mdc-switch__icon{bottom:0;left:0;margin:auto;position:absolute;right:0;top:0;opacity:0;transition:opacity 30ms 0ms cubic-bezier(0.4, 0, 1, 1)}.mdc-switch--selected .mdc-switch__icon--on,.mdc-switch--unselected .mdc-switch__icon--off{opacity:1;transition:opacity 45ms 30ms cubic-bezier(0, 0, 0.2, 1)}:host{display:inline-flex;outline:none}input{display:none}.mdc-switch{width:36px;width:var(--mdc-switch-track-width, 36px)}.mdc-switch.mdc-switch--selected:enabled .mdc-switch__handle::after{background:#6200ee;background:var(--mdc-switch-selected-handle-color, var(--mdc-theme-primary, #6200ee))}.mdc-switch.mdc-switch--selected:enabled:hover:not(:focus):not(:active) .mdc-switch__handle::after{background:#310077;background:var(--mdc-switch-selected-hover-handle-color, #310077)}.mdc-switch.mdc-switch--selected:enabled:focus:not(:active) .mdc-switch__handle::after{background:#310077;background:var(--mdc-switch-selected-focus-handle-color, #310077)}.mdc-switch.mdc-switch--selected:enabled:active .mdc-switch__handle::after{background:#310077;background:var(--mdc-switch-selected-pressed-handle-color, #310077)}.mdc-switch.mdc-switch--selected:disabled .mdc-switch__handle::after{background:#424242;background:var(--mdc-switch-disabled-selected-handle-color, #424242)}.mdc-switch.mdc-switch--unselected:enabled .mdc-switch__handle::after{background:#616161;background:var(--mdc-switch-unselected-handle-color, #616161)}.mdc-switch.mdc-switch--unselected:enabled:hover:not(:focus):not(:active) .mdc-switch__handle::after{background:#212121;background:var(--mdc-switch-unselected-hover-handle-color, #212121)}.mdc-switch.mdc-switch--unselected:enabled:focus:not(:active) .mdc-switch__handle::after{background:#212121;background:var(--mdc-switch-unselected-focus-handle-color, #212121)}.mdc-switch.mdc-switch--unselected:enabled:active .mdc-switch__handle::after{background:#212121;background:var(--mdc-switch-unselected-pressed-handle-color, #212121)}.mdc-switch.mdc-switch--unselected:disabled .mdc-switch__handle::after{background:#424242;background:var(--mdc-switch-disabled-unselected-handle-color, #424242)}.mdc-switch .mdc-switch__handle::before{background:#fff;background:var(--mdc-switch-handle-surface-color, var(--mdc-theme-surface, #fff))}.mdc-switch:enabled .mdc-switch__shadow{--mdc-elevation-box-shadow-for-gss:0px 2px 1px -1px rgba(0, 0, 0, 0.2), 0px 1px 1px 0px rgba(0, 0, 0, 0.14), 0px 1px 3px 0px rgba(0, 0, 0, 0.12);box-shadow:0px 2px 1px -1px rgba(0, 0, 0, 0.2), 0px 1px 1px 0px rgba(0, 0, 0, 0.14), 0px 1px 3px 0px rgba(0, 0, 0, 0.12);box-shadow:var(--mdc-switch-handle-elevation, var(--mdc-elevation-box-shadow-for-gss))}.mdc-switch:disabled .mdc-switch__shadow{--mdc-elevation-box-shadow-for-gss:0px 0px 0px 0px rgba(0, 0, 0, 0.2), 0px 0px 0px 0px rgba(0, 0, 0, 0.14), 0px 0px 0px 0px rgba(0, 0, 0, 0.12);box-shadow:0px 0px 0px 0px rgba(0, 0, 0, 0.2), 0px 0px 0px 0px rgba(0, 0, 0, 0.14), 0px 0px 0px 0px rgba(0, 0, 0, 0.12);box-shadow:var(--mdc-switch-disabled-handle-elevation, var(--mdc-elevation-box-shadow-for-gss))}.mdc-switch .mdc-switch__focus-ring-wrapper,.mdc-switch .mdc-switch__handle{height:20px;height:var(--mdc-switch-handle-height, 20px)}.mdc-switch:disabled .mdc-switch__handle::after{opacity:0.38;opacity:var(--mdc-switch-disabled-handle-opacity, 0.38)}.mdc-switch .mdc-switch__handle{border-radius:10px;border-radius:var(--mdc-switch-handle-shape, 10px)}.mdc-switch .mdc-switch__handle{width:20px;width:var(--mdc-switch-handle-width, 20px)}.mdc-switch .mdc-switch__handle-track{width:calc(100% - 20px);width:calc(100% - var(--mdc-switch-handle-width, 20px))}.mdc-switch.mdc-switch--selected:enabled .mdc-switch__icon{fill:#fff;fill:var(--mdc-switch-selected-icon-color, var(--mdc-theme-on-primary, #fff))}.mdc-switch.mdc-switch--selected:disabled .mdc-switch__icon{fill:#fff;fill:var(--mdc-switch-disabled-selected-icon-color, var(--mdc-theme-on-primary, #fff))}.mdc-switch.mdc-switch--unselected:enabled .mdc-switch__icon{fill:#fff;fill:var(--mdc-switch-unselected-icon-color, var(--mdc-theme-on-primary, #fff))}.mdc-switch.mdc-switch--unselected:disabled .mdc-switch__icon{fill:#fff;fill:var(--mdc-switch-disabled-unselected-icon-color, var(--mdc-theme-on-primary, #fff))}.mdc-switch.mdc-switch--selected:disabled .mdc-switch__icons{opacity:0.38;opacity:var(--mdc-switch-disabled-selected-icon-opacity, 0.38)}.mdc-switch.mdc-switch--unselected:disabled .mdc-switch__icons{opacity:0.38;opacity:var(--mdc-switch-disabled-unselected-icon-opacity, 0.38)}.mdc-switch.mdc-switch--selected .mdc-switch__icon{width:18px;width:var(--mdc-switch-selected-icon-size, 18px);height:18px;height:var(--mdc-switch-selected-icon-size, 18px)}.mdc-switch.mdc-switch--unselected .mdc-switch__icon{width:18px;width:var(--mdc-switch-unselected-icon-size, 18px);height:18px;height:var(--mdc-switch-unselected-icon-size, 18px)}.mdc-switch .mdc-switch__ripple{height:48px;height:var(--mdc-switch-state-layer-size, 48px);width:48px;width:var(--mdc-switch-state-layer-size, 48px)}.mdc-switch .mdc-switch__track{height:14px;height:var(--mdc-switch-track-height, 14px)}.mdc-switch:disabled .mdc-switch__track{opacity:0.12;opacity:var(--mdc-switch-disabled-track-opacity, 0.12)}.mdc-switch:enabled .mdc-switch__track::after{background:#d7bbff;background:var(--mdc-switch-selected-track-color, #d7bbff)}.mdc-switch:enabled:hover:not(:focus):not(:active) .mdc-switch__track::after{background:#d7bbff;background:var(--mdc-switch-selected-hover-track-color, #d7bbff)}.mdc-switch:enabled:focus:not(:active) .mdc-switch__track::after{background:#d7bbff;background:var(--mdc-switch-selected-focus-track-color, #d7bbff)}.mdc-switch:enabled:active .mdc-switch__track::after{background:#d7bbff;background:var(--mdc-switch-selected-pressed-track-color, #d7bbff)}.mdc-switch:disabled .mdc-switch__track::after{background:#424242;background:var(--mdc-switch-disabled-selected-track-color, #424242)}.mdc-switch:enabled .mdc-switch__track::before{background:#e0e0e0;background:var(--mdc-switch-unselected-track-color, #e0e0e0)}.mdc-switch:enabled:hover:not(:focus):not(:active) .mdc-switch__track::before{background:#e0e0e0;background:var(--mdc-switch-unselected-hover-track-color, #e0e0e0)}.mdc-switch:enabled:focus:not(:active) .mdc-switch__track::before{background:#e0e0e0;background:var(--mdc-switch-unselected-focus-track-color, #e0e0e0)}.mdc-switch:enabled:active .mdc-switch__track::before{background:#e0e0e0;background:var(--mdc-switch-unselected-pressed-track-color, #e0e0e0)}.mdc-switch:disabled .mdc-switch__track::before{background:#424242;background:var(--mdc-switch-disabled-unselected-track-color, #424242)}.mdc-switch .mdc-switch__track{border-radius:7px;border-radius:var(--mdc-switch-track-shape, 7px)}.mdc-switch.mdc-switch--selected{--mdc-ripple-focus-state-layer-color:var(--mdc-switch-selected-focus-state-layer-color, var(--mdc-theme-primary, #6200ee));--mdc-ripple-focus-state-layer-opacity:var(--mdc-switch-selected-focus-state-layer-opacity, 0.12);--mdc-ripple-hover-state-layer-color:var(--mdc-switch-selected-hover-state-layer-color, var(--mdc-theme-primary, #6200ee));--mdc-ripple-hover-state-layer-opacity:var(--mdc-switch-selected-hover-state-layer-opacity, 0.04);--mdc-ripple-pressed-state-layer-color:var(--mdc-switch-selected-pressed-state-layer-color, var(--mdc-theme-primary, #6200ee));--mdc-ripple-pressed-state-layer-opacity:var(--mdc-switch-selected-pressed-state-layer-opacity, 0.1)}.mdc-switch.mdc-switch--selected:enabled:focus:not(:active){--mdc-ripple-hover-state-layer-color:var(--mdc-switch-selected-focus-state-layer-color, var(--mdc-theme-primary, #6200ee))}.mdc-switch.mdc-switch--selected:enabled:active{--mdc-ripple-hover-state-layer-color:var(--mdc-switch-selected-pressed-state-layer-color, var(--mdc-theme-primary, #6200ee))}.mdc-switch.mdc-switch--unselected{--mdc-ripple-focus-state-layer-color:var(--mdc-switch-unselected-focus-state-layer-color, #424242);--mdc-ripple-focus-state-layer-opacity:var(--mdc-switch-unselected-focus-state-layer-opacity, 0.12);--mdc-ripple-hover-state-layer-color:var(--mdc-switch-unselected-hover-state-layer-color, #424242);--mdc-ripple-hover-state-layer-opacity:var(--mdc-switch-unselected-hover-state-layer-opacity, 0.04);--mdc-ripple-pressed-state-layer-color:var(--mdc-switch-unselected-pressed-state-layer-color, #424242);--mdc-ripple-pressed-state-layer-opacity:var(--mdc-switch-unselected-pressed-state-layer-opacity, 0.1)}.mdc-switch.mdc-switch--unselected:enabled:focus:not(:active){--mdc-ripple-hover-state-layer-color:var(--mdc-switch-unselected-focus-state-layer-color, #424242)}.mdc-switch.mdc-switch--unselected:enabled:active{--mdc-ripple-hover-state-layer-color:var(--mdc-switch-unselected-pressed-state-layer-color, #424242)}@media screen and (forced-colors: active),(-ms-high-contrast: active){.mdc-switch:disabled .mdc-switch__handle::after{opacity:1;opacity:var(--mdc-switch-disabled-handle-opacity, 1)}.mdc-switch.mdc-switch--selected:enabled .mdc-switch__icon{fill:ButtonText;fill:var(--mdc-switch-selected-icon-color, ButtonText)}.mdc-switch.mdc-switch--selected:disabled .mdc-switch__icon{fill:GrayText;fill:var(--mdc-switch-disabled-selected-icon-color, GrayText)}.mdc-switch.mdc-switch--unselected:enabled .mdc-switch__icon{fill:ButtonText;fill:var(--mdc-switch-unselected-icon-color, ButtonText)}.mdc-switch.mdc-switch--unselected:disabled .mdc-switch__icon{fill:GrayText;fill:var(--mdc-switch-disabled-unselected-icon-color, GrayText)}.mdc-switch.mdc-switch--selected:disabled .mdc-switch__icons{opacity:1;opacity:var(--mdc-switch-disabled-selected-icon-opacity, 1)}.mdc-switch.mdc-switch--unselected:disabled .mdc-switch__icons{opacity:1;opacity:var(--mdc-switch-disabled-unselected-icon-opacity, 1)}.mdc-switch:disabled .mdc-switch__track{opacity:1;opacity:var(--mdc-switch-disabled-track-opacity, 1)}}`
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */;let Qe=class extends Ye{};Qe.styles=[Je],Qe=e([$("mwc-switch")],Qe);let et=class extends N{constructor(){super(),this.is_connected=!1,this.direction="horizontal",this.location="",this.aliases=Object(),this.aggregate_updating=!1,this.project_resource_monitor=!1,this.active=!1,this.resourceBroker=globalThis.resourceBroker,this.notification=globalThis.lablupNotification,this.init_resource()}static get is(){return"backend-ai-resource-monitor"}static get styles(){return[s,o,n,a,l,c`
        mwc-linear-progress {
          height: 5px;
          --mdc-theme-primary: #98be5a;
        }
        .lablup-progress-bar {
          --progress-bar-width: 186px;
        }

        .horizontal-card {
          width: auto;
        }

        .horizontal-panel mwc-linear-progress {
          width: 90px;
        }

        .vertical-panel mwc-linear-progress {
          width: 186px;
        }

        #scaling-group-select-box.horizontal {
          min-height: 80px;
          min-width: 252px;
          margin: 0;
          padding: 0;
        }

        #scaling-group-select-box.vertical {
          padding: 10px 20px;
          min-height: 83px; /* 103px-20px */
        }

        #scaling-group-select-box.horizontal mwc-select {
          width: 250px;
          height: 58px;
        }

        #scaling-group-select-box.vertical mwc-select {
          width: 305px;
          height: 58px;
        }

        .vertical-panel #resource-gauges {
          min-height: 200px;
        }

        mwc-linear-progress.project-bar {
          height: 15px;
        }

        mwc-linear-progress.start-bar {
          border-top-left-radius: 3px;
          border-top-right-radius: 3px;
          --mdc-theme-primary: #3677eb;
        }

        mwc-linear-progress.middle-bar {
          --mdc-theme-primary: #4f8b46;
        }

        mwc-linear-progress.end-bar {
          border-bottom-left-radius: 3px;
          border-bottom-right-radius: 3px;
          --mdc-theme-primary: #98be5a;
        }

        mwc-linear-progress.full-bar {
          border-radius: 3px;
          height: 10px;
        }

        .resources.horizontal .short-indicator mwc-linear-progress {
          width: 50px;
        }

        .resources.horizontal .short-indicator {
          width: 50px;
        }
        span.caption {
          width: 30px;
          display: block;
          font-size: 12px;
          padding-left: 10px;
        }

        div.caption {
          font-size: 12px;
          width: 100px;
        }

        #resource-gauges.horizontal {
          /* left: 160px; */
          /* width: 420px; */
          width: auto;
          height: auto;
          background-color: transparent;
        }

        mwc-icon {
          --icon-size: 24px;
        }

        img.resource-type-icon {
          width: 24px;
          height: 24px;
        }

        @media screen and (max-width: 749px) {
          #resource-gauge-toggle.horizontal {
            display: flex;
          }

          #resource-gauge-toggle.vertical {
            display: none;
          }

          #resource-gauges.horizontal {
            display: none;
          }

          #resource-gauges.vertical {
            display: flex;
          }
        }

        @media screen and (min-width: 750px) {
          #resource-gauge-toggle {
            display: none;
          }

          #resource-gauges.horizontal,
          #resource-gauges.vertical {
            display: flex;
          }
        }

        .indicator {
          font-family: monospace;
        }

        .resource-button {
          height: 140px;
          width: 120px;
          margin: 5px;
          padding: 0;
          font-size: 14px;
        }

        #new-session-dialog {
          z-index: 100;
        }

        #scaling-group-select {
          width: 305px;
          height: 55px;
          --mdc-select-outlined-idle-border-color: #dddddd;
          --mdc-select-outlined-hover-border-color: #dddddd;
          background-color: white !important;
          border-radius: 5px;
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

        .resources .monitor {
          margin-bottom: 15px;
        }

        .resources.vertical .monitor,
        .resources.horizontal .monitor {
          margin-bottom: 10px;
        }

        mwc-select {
          width: 100%;
        }

        div.mdc-select__anchor {
          background-color: white !important;
        }

        mwc-textfield {
          width: 100%;
          --mdc-text-field-idle-line-color: rgba(0, 0, 0, 0.42);
          --mdc-text-field-hover-line-color: rgba(255, 0, 0, 0.87);
          --mdc-text-field-fill-color: transparent;
          --mdc-theme-primary: var(--paper-red-600);
        }

        mwc-textfield#session-name {
          width: 50%;
          padding-top: 20px;
          padding-left: 0;
          margin-left: 0;
          margin-bottom: 1px;
        }

        .vertical-card > #resource-gauges > .monitor > .resource-name {
          width: 60px;
        }

        .horizontal-card > #resource-gauges {
          display: grid !important;
          grid-auto-flow: row;
          grid-template-columns: repeat(auto-fill, 320px);
          justify-content: center;
        }

        @media screen and (min-width: 750px) {
          div#resource-gauges {
            display: flex !important;
          }
        }

        @media screen and (max-width: 1015px) {
          div#resource-gauges {
            justify-content: center;
          }
        }
      `]}init_resource(){this.total_slot={},this.total_resource_group_slot={},this.total_project_slot={},this.used_slot={},this.used_resource_group_slot={},this.used_project_slot={},this.available_slot={},this.used_slot_percent={},this.used_resource_group_slot_percent={},this.used_project_slot_percent={},this.concurrency_used=0,this.concurrency_max=0,this.concurrency_limit=0,this._status="inactive",this.scaling_groups=[{name:""}],this.scaling_group="",this.sessions_list=[],this.metric_updating=!1,this.metadata_updating=!1}firstUpdated(){new ResizeObserver((()=>{this._updateToggleResourceMonitorDisplay()})).observe(this.resourceGauge),document.addEventListener("backend-ai-group-changed",(e=>{this.scaling_group="",this._updatePageVariables(!0)})),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.is_connected=!0,setInterval((()=>{this._periodicUpdateResourcePolicy()}),2e4)}),{once:!0}):this.is_connected=!0,document.addEventListener("backend-ai-session-list-refreshed",(()=>{this._updatePageVariables(!0)}))}async _periodicUpdateResourcePolicy(){return this.active?(await this._refreshResourcePolicy(),this.aggregateResource("refresh-resource-policy"),Promise.resolve(!0)):Promise.resolve(!1)}async updateScalingGroup(e=!1,t){await this.resourceBroker.updateScalingGroup(e,t.target.value),this.active&&!0===e&&(await this._refreshResourcePolicy(),this.aggregateResource("update-scaling-group"))}async _viewStateChanged(e){await this.updateComplete,this.active&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.project_resource_monitor=this.resourceBroker.allow_project_resource_monitor,this._updatePageVariables(!0)}),{once:!0}):(this.project_resource_monitor=this.resourceBroker.allow_project_resource_monitor,await this._updatePageVariables(!0)))}async _updatePageVariables(e){return this.active&&!1===this.metadata_updating?(this.metadata_updating=!0,await this.resourceBroker._updatePageVariables(e),this.sessions_list=this.resourceBroker.sessions_list,await this._refreshResourcePolicy(),this.aggregateResource("update-page-variable"),this.metadata_updating=!1,Promise.resolve(!0)):Promise.resolve(!1)}_updateToggleResourceMonitorDisplay(){var e,t;const i=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#resource-legend"),r=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#resource-gauge-toggle-button");document.body.clientWidth>750&&"horizontal"==this.direction?(i.style.display="flex",i.style.marginTop="0",Array.from(this.resourceGauge.children).forEach((e=>{e.style.display="flex"}))):r.selected?(i.style.display="flex",i.style.marginTop="0",document.body.clientWidth<750&&(this.resourceGauge.style.left="20px",this.resourceGauge.style.right="20px"),Array.from(this.resourceGauge.children).forEach((e=>{e.style.display="flex"}))):(Array.from(this.resourceGauge.children).forEach((e=>{e.style.display="none"})),i.style.display="none")}async _refreshResourcePolicy(e=!1){return this.active?this.resourceBroker._refreshResourcePolicy().then((e=>(!1===e&&setTimeout((()=>{this._refreshResourcePolicy()}),2500),this.concurrency_used=this.resourceBroker.concurrency_used,this.concurrency_max=this.concurrency_used>this.resourceBroker.concurrency_max?this.concurrency_used:this.resourceBroker.concurrency_max,Promise.resolve(!0)))).catch((e=>(this.metadata_updating=!1,e&&e.message?(this.notification.text=D.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=D.relieve(e.title),this.notification.show(!0,e)),Promise.resolve(!1)))):Promise.resolve(!0)}_aliasName(e){const t=this.resourceBroker.imageTagAlias,i=this.resourceBroker.imageTagReplace;for(const[t,r]of Object.entries(i)){const i=new RegExp(t);if(i.test(e))return e.replace(i,r)}return e in t?t[e]:e}async _aggregateResourceUse(e=""){return this.resourceBroker._aggregateCurrentResource(e).then((t=>!1===t?setTimeout((()=>{this._aggregateResourceUse(e)}),1e3):(this.concurrency_used=this.resourceBroker.concurrency_used,this.scaling_group=this.resourceBroker.scaling_group,this.scaling_groups=this.resourceBroker.scaling_groups,this.total_slot=this.resourceBroker.total_slot,this.total_resource_group_slot=this.resourceBroker.total_resource_group_slot,this.total_project_slot=this.resourceBroker.total_project_slot,this.used_slot=this.resourceBroker.used_slot,this.used_resource_group_slot=this.resourceBroker.used_resource_group_slot,this.used_project_slot=this.resourceBroker.used_project_slot,this.used_project_slot_percent=this.resourceBroker.used_project_slot_percent,this.concurrency_limit=this.resourceBroker.concurrency_limit,this.available_slot=this.resourceBroker.available_slot,this.used_slot_percent=this.resourceBroker.used_slot_percent,this.used_resource_group_slot_percent=this.resourceBroker.used_resource_group_slot_percent,Promise.resolve(!0)))).then((()=>Promise.resolve(!0))).catch((e=>(e&&e.message&&(console.log(e),this.notification.text=D.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)),Promise.resolve(!1))))}aggregateResource(e=""){void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._aggregateResourceUse(e)}),!0):this._aggregateResourceUse(e)}_numberWithPostfix(e,t=""){return isNaN(parseInt(e))?"":parseInt(e)+t}_prefixFormatWithoutTrailingZeros(e="0",t){const i="string"==typeof e?parseFloat(e):e;return parseFloat(i.toFixed(t)).toString()}_prefixFormat(e="0",t){var i;return"string"==typeof e?null===(i=parseFloat(e))||void 0===i?void 0:i.toFixed(t):null==e?void 0:e.toFixed(t)}render(){return d`
      <link rel="stylesheet" href="resources/custom.css" />
      <div class="layout ${this.direction} justified flex wrap">
        <div
          id="scaling-group-select-box"
          class="layout horizontal center-justified ${this.direction}"
        >
          <backend-ai-react-resource-group-select
            value=${this.scaling_group}
            @change=${({detail:e})=>{this.updateScalingGroup(!0,{target:{value:e}})}}
          ></backend-ai-react-resource-group-select>
        </div>
        <div class="layout ${this.direction}-card flex wrap">
          <div
            id="resource-gauges"
            class="layout ${this.direction} ${this.direction}-panel resources flex wrap"
          >
            <div class="layout horizontal center-justified monitor">
              <div
                class="layout vertical center center-justified resource-name"
              >
                <div class="gauge-name">CPU</div>
              </div>
              <div class="layout vertical start-justified wrap">
                <lablup-progress-bar
                  id="cpu-usage-bar"
                  class="start"
                  progress="${this.used_resource_group_slot_percent.cpu/100}"
                  description="${this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot.cpu,0)} / ${this._prefixFormatWithoutTrailingZeros(this.total_resource_group_slot.cpu,0)} Cores"
                ></lablup-progress-bar>
                <lablup-progress-bar
                  id="cpu-usage-bar-2"
                  class="end"
                  progress="${this.used_slot_percent.cpu/100}"
                  description="${this._prefixFormatWithoutTrailingZeros(this.used_slot.cpu,0)} / ${this._prefixFormatWithoutTrailingZeros(this.total_slot.cpu,0)} Cores"
                ></lablup-progress-bar>
              </div>
              <div class="layout vertical center center-justified">
                <span class="percentage start-bar">
                  ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot_percent.cpu,1),"%")}
                </span>
                <span class="percentage end-bar">
                  ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_slot_percent.cpu,1),"%")}
                </span>
              </div>
            </div>
            <div class="layout horizontal center-justified monitor">
              <div
                class="layout vertical center center-justified resource-name"
              >
                <span class="gauge-name">RAM</span>
              </div>
              <div class="layout vertical start-justified wrap">
                <lablup-progress-bar
                  id="mem-usage-bar"
                  class="start"
                  progress="${this.used_resource_group_slot_percent.mem/100}"
                  description="${this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot.mem,2)} / ${this._prefixFormatWithoutTrailingZeros(this.total_resource_group_slot.mem,2)} GiB"
                ></lablup-progress-bar>
                <lablup-progress-bar
                  id="mem-usage-bar-2"
                  class="end"
                  progress="${this.used_slot_percent.mem/100}"
                  description="${this._prefixFormatWithoutTrailingZeros(this.used_slot.mem,2)} / ${this._prefixFormatWithoutTrailingZeros(this.total_slot.mem,2)} GiB"
                ></lablup-progress-bar>
              </div>
              <div class="layout vertical center center-justified">
                <span class="percentage start-bar">
                  ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot_percent.mem,1),"%")}
                </span>
                <span class="percentage end-bar">
                  ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_slot_percent.mem,1),"%")}
                </span>
              </div>
            </div>
            ${this.total_slot.cuda_device?d`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <span class="gauge-name">GPU</span>
                    </div>
                    <div class="layout vertical center-justified wrap">
                      <lablup-progress-bar
                        id="gpu-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot.cuda_device/this.total_resource_group_slot.cuda_device}"
                        description="${this._prefixFormat(this.used_resource_group_slot.cuda_device,2)} / ${this._prefixFormat(this.total_resource_group_slot.cuda_device,2)} CUDA GPUs"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="gpu-usage-bar-2"
                        class="end"
                        progress="${this.used_slot.cuda_device}/${this.total_slot.cuda_device}"
                        description="${this._prefixFormat(this.used_slot.cuda_device,2)} / ${this._prefixFormat(this.total_slot.cuda_device,2)} CUDA GPUs"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot_percent.cuda_device,1),"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_slot_percent.cuda_device,1),"%")}
                      </span>
                    </div>
                  </div>
                `:d``}
            ${this.resourceBroker.total_slot.cuda_shares&&this.resourceBroker.total_slot.cuda_shares>0?d`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <span class="gauge-name">FGPU</span>
                    </div>
                    <div class="layout vertical start-justified wrap">
                      <lablup-progress-bar
                        id="fgpu-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot.cuda_shares/this.total_resource_group_slot.cuda_shares}"
                        description="${this._prefixFormat(this.used_resource_group_slot.cuda_shares,2)} / ${this._prefixFormat(this.total_resource_group_slot.cuda_shares,2)} CUDA FGPUs"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="fgpu-usage-bar-2"
                        class="end"
                        progress="${this.used_slot.cuda_shares/this.total_slot.cuda_shares}"
                        description="${this._prefixFormat(this.used_slot.cuda_shares,2)} /
                        ${this._prefixFormat(this.total_slot.cuda_shares,2)} CUDA FGPUs"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot_percent.cuda_shares,1),"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_slot_percent.cuda_shares,1),"%")}
                      </span>
                    </div>
                  </div>
                `:d``}
            ${this.total_slot.rocm_device?d`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <span class="gauge-name">
                        ROCm
                        <br />
                        GPU
                      </span>
                    </div>
                    <div class="layout vertical center-justified wrap">
                      <lablup-progress-bar
                        id="rocm-gpu-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot_percent.rocm_device/100}"
                        description="${this._prefixFormat(this.used_resource_group_slot.rocm_device,2)} / ${this._prefixFormat(this.total_resource_group_slot.rocm_device,2)} ROCm GPUs"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="rocm-gpu-usage-bar-2"
                        class="end"
                        progress="${this.used_slot_percent.rocm_device/100}"
                        buffer="${this.used_slot_percent.rocm_device/100}"
                        description="${this._prefixFormat(this.used_slot.rocm_device,2)} / ${this._prefixFormat(this.total_slot.rocm_device,2)} ROCm GPUs"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot_percent.rocm_device,1),"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_slot_percent.rocm_device,1),"%")}
                      </span>
                    </div>
                  </div>
                `:d``}
            ${this.total_slot.tpu_device?d`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <span class="gauge-name">TPU</span>
                    </div>
                    <div class="layout vertical center-justified wrap">
                      <lablup-progress-bar
                        id="tpu-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot_percent.tpu_device/100}"
                        description="${this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot.tpu_device,2)} / ${this._prefixFormatWithoutTrailingZeros(this.total_resource_group_slot.tpu_device,2)} TPUs"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="tpu-usage-bar-2"
                        class="end"
                        progress="${this.used_slot_percent.tpu_device/100}"
                        buffer="${this.used_slot_percent.tpu_device/100}"
                        description="${this._prefixFormatWithoutTrailingZeros(this.used_slot.tpu_device,2)}/${this._prefixFormatWithoutTrailingZeros(this.total_slot.tpu_device,2)} TPUs"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot_percent.tpu_device,1),"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_slot_percent.tpu_device,1),"%")}
                      </span>
                    </div>
                  </div>
                `:d``}
            ${this.total_slot.ipu_device?d`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <span class="gauge-name">IPU</span>
                    </div>
                    <div class="layout vertical center-justified wrap">
                      <lablup-progress-bar
                        id="ipu-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot_percent.ipu_device/100}"
                        description="${this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot.ipu_device,2)} / ${this._prefixFormatWithoutTrailingZeros(this.total_resource_group_slot.ipu_device,2)} IPUs"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="ipu-usage-bar-2"
                        class="end"
                        progress="${this.used_slot_percent.ipu_device/100}"
                        buffer="${this.used_slot_percent.ipu_device/100}"
                        description="${this._prefixFormatWithoutTrailingZeros(this.used_slot.ipu_device,2)} / ${this._prefixFormatWithoutTrailingZeros(this.total_slot.ipu_device,2)} "
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot_percent.ipu_device,1),"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_slot_percent.ipu_device,1),"%")}
                      </span>
                    </div>
                  </div>
                `:d``}
            ${this.total_slot.atom_device?d`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <span class="gauge-name">ATOM</span>
                    </div>
                    <div class="layout vertical center-justified wrap">
                      <lablup-progress-bar
                        id="atom-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot_percent.atom_device/100}"
                        description="${this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot.atom_device,2)} / ${this._prefixFormatWithoutTrailingZeros(this.total_resource_group_slot.atom_device,2)} ATOMs"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="atom-usage-bar-2"
                        class="end"
                        progress="${this.used_slot_percent.atom_device/100}"
                        buffer="${this.used_slot_percent.atom_device/100}"
                        description="${this._prefixFormatWithoutTrailingZeros(this.used_slot.atom_device,2)} / ${this._prefixFormatWithoutTrailingZeros(this.total_slot.atom_device,2)} ATOMs"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot_percent.atom_device,1),"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_slot_percent.atom_device,1),"%")}
                      </span>
                    </div>
                  </div>
                `:d``}
            ${this.total_slot.atom_plus_device?d`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <span class="gauge-name">ATOM+</span>
                    </div>
                    <div class="layout vertical center-justified wrap">
                      <lablup-progress-bar
                        id="atom-plus-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot_percent.atom_plus_device/100}"
                        description="${this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot.atom_plus_device,2)} / ${this._prefixFormatWithoutTrailingZeros(this.total_resource_group_slot.atom_plus_device,2)} ATOM+"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="atom-plus-usage-bar-2"
                        class="end"
                        progress="${this.used_slot_percent.atom_plus_device/100}"
                        buffer="${this.used_slot_percent.atom_plus_device/100}"
                        description="${this._prefixFormatWithoutTrailingZeros(this.used_slot.atom_plus_device,2)} / ${this._prefixFormatWithoutTrailingZeros(this.total_slot.atom_plus_device,2)} ATOM+"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span
                        class="percentage
                        start-bar
                      "
                      >
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot_percent.atom_plus_device,1),"%")}
                      </span>
                      <span
                        class="percentage
                        end-bar
                      "
                      >
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_slot_percent.atom_plus_device,1),"%")}
                      </span>
                    </div>
                  </div>
                `:d``}
            ${this.total_slot.gaudi2_device?d`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <span class="gauge-name">Gaudi 2</span>
                    </div>
                    <div class="layout vertical center-justified wrap">
                      <lablup-progress-bar
                        id="gaudi-2-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot_percent.gaudi2_device/100}"
                        description="${this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot.gaudi2_device,2)} / ${this._prefixFormatWithoutTrailingZeros(this.total_resource_group_slot.gaudi2_device,2)}"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="gaudi-2-usage-bar-2"
                        class="end"
                        progress="${this.used_slot_percent.gaudi2_device/100}"
                        buffer="${this.used_slot_percent.gaudi2_device/100}"
                        description="${this.used_slot.gaudi2_device}/${this.total_slot.gaudi2_device}"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span
                        class="percentage
                        start-bar
                      "
                      >
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot_percent.gaudi2_device,1),"%")}
                      </span>
                      <span
                        class="percentage
                        end-bar
                      "
                      >
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_slot_percent.gaudi2_device,1),"%")}
                      </span>
                    </div>
                  </div>
                `:d``}
            ${this.total_slot.warboy_device?d`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <span class="gauge-name">Warboy</span>
                    </div>
                    <div class="layout vertical center-justified wrap">
                      <lablup-progress-bar
                        id="warboy-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot_percent.warboy_device/100}"
                        description="${this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot.warboy_device,2)} / ${this._prefixFormatWithoutTrailingZeros(this.total_resource_group_slot.warboy_device,2)} Warboys"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="warboy-usage-bar-2"
                        class="end"
                        progress="${this.used_slot_percent.warboy_device/100}"
                        buffer="${this.used_slot_percent.warboy_device/100}"
                        description="${this._prefixFormatWithoutTrailingZeros(this.used_slot.warboy_device,2)} / ${this._prefixFormatWithoutTrailingZeros(this.total_slot.warboy_device,2)} Warboys"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot_percent.warboy_device,1),"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_slot_percent.warboy_device,1),"%")}
                      </span>
                    </div>
                  </div>
                `:d``}
            ${this.total_slot.rngd_device?d`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <span class="gauge-name">RNGD</span>
                    </div>
                    <div class="layout vertical center-justified wrap">
                      <lablup-progress-bar
                        id="rngd-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot_percent.rngd_device/100}"
                        description="${this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot.rngd_device,2)} / ${this._prefixFormatWithoutTrailingZeros(this.total_resource_group_slot.rngd_device,2)} RNGDs"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="rngd-usage-bar-2"
                        class="end"
                        progress="${this.used_slot_percent.rngd_device/100}"
                        buffer="${this.used_slot_percent.rngd_device/100}"
                        description="${this._prefixFormatWithoutTrailingZeros(this.used_slot.rngd_device,2)} / ${this._prefixFormatWithoutTrailingZeros(this.total_slot.rngd_device,2)} RNGDs"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot_percent.rngd_device,1),"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_slot_percent.rngd_device,1),"%")}
                      </span>
                    </div>
                  </div>
                `:d``}
            ${this.total_slot.hyperaccel_lpu_device?d`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <span class="gauge-name">Hyperaccel LPU</span>
                    </div>
                    <div class="layout vertical center-justified wrap">
                      <lablup-progress-bar
                        id="hyperaccel-lpu-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot_percent.hyperaccel_lpu_device/100}"
                        description="${this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot.hyperaccel_lpu_device,2)} / ${this._prefixFormatWithoutTrailingZeros(this.total_resource_group_slot.hyperaccel_lpu_device,2)} Hyperaccel LPUs"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="hyperaccel-lpu-usage-bar-2"
                        class="end"
                        progress="${this.used_slot_percent.hyperaccel_lpu_device/100}"
                        buffer="${this.used_slot_percent.hyperaccel_lpu_device/100}"
                        description="${this._prefixFormatWithoutTrailingZeros(this.used_slot.hyperaccel_lpu_device,2)} / ${this._prefixFormatWithoutTrailingZeros(this.total_slot.hyperaccel_lpu_device,2)} Hyperaccel LPUs"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_resource_group_slot_percent.hyperaccel_lpu_device,1),"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_slot_percent.hyperaccel_lpu_device,1),"%")}
                      </span>
                    </div>
                  </div>
                `:d``}
            <div class="layout horizontal center-justified monitor">
              <div
                class="layout vertical center center-justified resource-name"
              >
                <span class="gauge-name">
                  ${O("session.launcher.Sessions")}
                </span>
              </div>
              <div class="layout vertical center-justified wrap">
                <lablup-progress-bar
                  id="concurrency-usage-bar"
                  class="start"
                  progress="${this.used_slot_percent.concurrency/100}"
                  description="${this._prefixFormatWithoutTrailingZeros(this.concurrency_used,0)} / ${1e6===this.concurrency_max?"∞":this._prefixFormatWithoutTrailingZeros(this.concurrency_max,2)}"
                ></lablup-progress-bar>
              </div>
              <div class="layout vertical center center-justified">
                <span class="percentage end-bar" style="margin-top:0px;">
                  ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_slot_percent.concurrency,1),"%")}
                </span>
              </div>
            </div>
          </div>
          <div
            class="layout horizontal center end-justified"
            id="resource-gauge-toggle"
          >
            <p style="font-size:12px;margin-right:10px;">
              ${O("session.launcher.ResourceMonitorToggle")}
            </p>
            <mwc-switch
              selected
              class="${this.direction}"
              id="resource-gauge-toggle-button"
              @click="${()=>this._updateToggleResourceMonitorDisplay()}"
            ></mwc-switch>
          </div>
        </div>
      </div>
      <div
        class="vertical start-justified layout ${this.direction}-card"
        id="resource-legend"
      >
        <div
          class="layout horizontal center ${"vertical"===this.direction?"start-justified":"end-justified"}
                    resource-legend-stack"
        >
          <div class="resource-legend-icon start"></div>
          <span
            class="resource-legend"
            style="overflow:hidden;white-space:nowrap;text-overflow:ellipsis;"
          >
            ${O("session.launcher.CurrentResourceGroup")}
            (${this.scaling_group})
          </span>
        </div>
        <div
          class="layout horizontal center ${"vertical"===this.direction?"start-justified":"end-justified"}"
        >
          <div class="resource-legend-icon end"></div>
          <span class="resource-legend">
            ${O("session.launcher.UserResourceLimit")}
          </span>
        </div>
      </div>
      ${"vertical"===this.direction&&!0===this.project_resource_monitor&&(this.total_project_slot.cpu>0||this.total_project_slot.cpu===1/0)?d`
            <hr />
            <div class="vertical start-justified layout">
              <div class="flex"></div>
              <div class="layout horizontal center-justified monitor">
                <div
                  class="layout vertical center center-justified"
                  style="margin-right:5px;"
                >
                  <mwc-icon class="fg blue">group_work</mwc-icon>
                  <span class="gauge-name">
                    ${O("session.launcher.Project")}
                  </span>
                </div>
                <div
                  class="layout vertical start-justified wrap short-indicator"
                >
                  <div class="layout horizontal">
                    <span
                      style="width:35px; margin-left:5px; margin-right:5px;"
                    >
                      CPU
                    </span>
                    <lablup-progress-bar
                      id="cpu-project-usage-bar"
                      class="start"
                      progress="${this.used_project_slot_percent.cpu/100}"
                      description="${this._prefixFormatWithoutTrailingZeros(this.used_project_slot.cpu,0)} / ${this.total_project_slot.cpu===1/0?"∞":this._prefixFormatWithoutTrailingZeros(this.total_project_slot.cpu,0)} Cores"
                    ></lablup-progress-bar>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_project_slot_percent.cpu,1),"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.total_project_slot.cpu,1),"%")}
                      </span>
                    </div>
                  </div>
                  <div class="layout horizontal">
                    <span style="width:35px;margin-left:5px; margin-right:5px;">
                      RAM
                    </span>
                    <lablup-progress-bar
                      id="mem-project-usage-bar"
                      class="end"
                      progress="${this.used_project_slot_percent.mem/100}"
                      description=">${this.used_project_slot.mem} / ${this.total_project_slot.mem===1/0?"∞":this._prefixFormatWithoutTrailingZeros(this.total_project_slot.mem,2)} GiB"
                    ></lablup-progress-bar>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_project_slot_percent.mem,1),"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.total_project_slot.mem,1),"%")}
                      </span>
                    </div>
                  </div>
                  ${this.total_project_slot.cuda_device?d`
                        <div class="layout horizontal">
                          <span
                            style="width:35px;margin-left:5px; margin-right:5px;"
                          >
                            GPU
                          </span>
                          <lablup-progress-bar
                            id="gpu-project-usage-bar"
                            class="end"
                            progress="${this.used_project_slot_percent.cuda_device/100}"
                            description="${this._prefixFormatWithoutTrailingZeros(this.used_project_slot.cuda_device,2)} / ${"Infinity"===this.total_project_slot.cuda_device?"∞":this._prefixFormatWithoutTrailingZeros(this.total_project_slot.cuda_device,2)} CUDA GPUs"
                          ></lablup-progress-bar>
                          <div class="layout vertical center center-justified">
                            <span class="percentage start-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_project_slot_percent.cuda_device,1),"%")}
                            </span>
                            <span class="percentage end-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.total_project_slot.cuda_device,1),"%")}
                            </span>
                          </div>
                        </div>
                      `:d``}
                  ${this.total_project_slot.cuda_shares?d`
                        <div class="layout horizontal">
                          <span
                            style="width:35px;margin-left:5px; margin-right:5px;"
                          >
                            FGPU
                          </span>
                          <lablup-progress-bar
                            id="fgpu-project-usage-bar"
                            class="end"
                            progress="${this.used_project_slot_percent.cuda_shares/100}"
                            description="${this.used_project_slot.cuda_shares}/${"Infinity"===this.total_project_slot.cuda_shares?"∞":this._prefixFormatWithoutTrailingZeros(this.total_project_slot.cuda_shares,2)} CUDA FGPUs"
                          ></lablup-progress-bar>
                          <div class="layout vertical center center-justified">
                            <span class="percentage start-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_project_slot_percent.cuda_shares,1),"%")}
                            </span>
                            <span class="percentage end-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.total_project_slot.cuda_shares,1),"%")}
                            </span>
                          </div>
                        </div>
                      `:d``}
                  ${this.total_project_slot.rocm_device?d`
                        <div class="layout horizontal">
                          <span
                            style="width:35px;margin-left:5px; margin-right:5px;"
                          >
                            GPU
                          </span>
                          <lablup-progress-bar
                            id="rocm-project-usage-bar"
                            class="end"
                            progress="${this.used_project_slot_percent.rocm_device/100}"
                            description="${this.used_project_slot.rocm_device}/${"Infinity"===this.total_project_slot.rocm_device?"∞":this._prefixFormatWithoutTrailingZeros(this.total_project_slot.rocm_device,2)} ROCm GPUs"
                          ></lablup-progress-bar>
                          <div class="layout vertical center center-justified">
                            <span class="percentage start-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_project_slot_percent.rocm_device,1),"%")}
                            </span>
                            <span class="percentage end-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.total_project_slot.rocm_device,1),"%")}
                            </span>
                          </div>
                        </div>
                      `:d``}
                  ${this.total_project_slot.tpu_device?d`
                        <div class="layout horizontal">
                          <span
                            style="width:35px;margin-left:5px; margin-right:5px;"
                          >
                            GPU
                          </span>
                          <lablup-progress-bar
                            id="tpu-project-usage-bar"
                            class="end"
                            progress="${this.used_project_slot_percent.tpu_device/100}"
                            description="${this.used_project_slot.tpu_device}/${"Infinity"===this.total_project_slot.tpu_device?"∞":this._prefixFormatWithoutTrailingZeros(this.total_project_slot.tpu_device,2)} TPUs"
                          ></lablup-progress-bar>
                          <div class="layout vertical center center-justified">
                            <span class="percentage start-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_project_slot_percent.tpu_device,1),"%")}
                            </span>
                            <span class="percentage end-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.total_project_slot.tpu_device,1),"%")}
                            </span>
                          </div>
                        </div>
                      `:d``}
                  ${this.total_project_slot.ipu_device?d`
                        <div class="layout horizontal">
                          <span
                            style="width:35px;margin-left:5px; margin-right:5px;"
                          >
                            IPU
                          </span>
                          <lablup-progress-bar
                            id="ipu-project-usage-bar"
                            class="end"
                            progress="${this.used_project_slot_percent.ipu_device/100}"
                            description="${this.used_project_slot.ipu_device}/${"Infinity"===this.total_project_slot.ipu_device?"∞":this._prefixFormatWithoutTrailingZeros(this.total_project_slot.ipu_device,2)} IPUs"
                          ></lablup-progress-bar>
                          <div class="layout vertical center center-justified">
                            <span class="percentage start-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_project_slot_percent.ipu_device,1),"%")}
                            </span>
                            <span class="percentage end-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.total_project_slot.ipu_device,1),"%")}
                            </span>
                          </div>
                        </div>
                      `:d``}
                  ${this.total_project_slot.atom_device?d`
                        <div class="layout horizontal">
                          <span
                            style="width:35px;margin-left:5px; margin-right:5px;"
                          >
                            ATOM
                          </span>
                          <lablup-progress-bar
                            id="tpu-project-usage-bar"
                            class="end"
                            progress="${this.used_project_slot_percent.atom_device/100}"
                            description="${this.used_project_slot.atom_device}/${"Infinity"===this.total_project_slot.atom_device?"∞":this._prefixFormatWithoutTrailingZeros(this.total_project_slot.atom_device,2)} ATOMs"
                          ></lablup-progress-bar>
                          <div class="layout vertical center center-justified">
                            <span class="percentage start-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_project_slot_percent.atom_device,1),"%")}
                            </span>
                            <span class="percentage end-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.total_project_slot.atom_device,1),"%")}
                            </span>
                          </div>
                        </div>
                      `:d``}
                  ${this.total_project_slot.warboy_device?d`
                        <div class="layout horizontal">
                          <span
                            style="width:35px;margin-left:5px; margin-right:5px;"
                          >
                            Warboy
                          </span>
                          <lablup-progress-bar
                            id="tpu-project-usage-bar"
                            class="end"
                            progress="${this.used_project_slot_percent.warboy_device/100}"
                            description="${this.used_project_slot.warboy_device}/${"Infinity"===this.total_project_slot.warboy_device?"∞":this._prefixFormatWithoutTrailingZeros(this.total_project_slot.warboy_device,2)} Warboys"
                          ></lablup-progress-bar>
                          <div class="layout vertical center center-justified">
                            <span class="percentage start-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_project_slot_percent.warboy_device,1),"%")}
                            </span>
                            <span class="percentage end-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.total_project_slot.warboy_device,1),"%")}
                            </span>
                          </div>
                        </div>
                      `:d``}
                  ${this.total_project_slot.rngd_device?d`
                        <div class="layout horizontal">
                          <span
                            style="width:35px;margin-left:5px; margin-right:5px;"
                          >
                            RNGD
                          </span>
                          <lablup-progress-bar
                            id="tpu-project-usage-bar"
                            class="end"
                            progress="${this.used_project_slot_percent.rngd_device/100}"
                            description="${this.used_project_slot.rngd_device}/${"Infinity"===this.total_project_slot.rngd_device?"∞":this._prefixFormatWithoutTrailingZeros(this.total_project_slot.rngd_device,2)} RNGDs"
                          ></lablup-progress-bar>
                          <div class="layout vertical center center-justified">
                            <span class="percentage start-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_project_slot_percent.rngd_device,1),"%")}
                            </span>
                            <span class="percentage end-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.total_project_slot.rngd_device,1),"%")}
                            </span>
                          </div>
                        </div>
                      `:d``}
                  ${this.total_project_slot.hyperaccel_lpu_device?d`
                        <div class="layout horizontal">
                          <span
                            style="width:35px;margin-left:5px; margin-right:5px;"
                          >
                            Hyperaccel LPU
                          </span>
                          <lablup-progress-bar
                            id="hyperaccel-lpu-project-usage-bar"
                            class="end"
                            progress="${this.used_project_slot_percent.hyperaccel_lpu_device/100}"
                            description="${this.used_project_slot.hyperaccel_lpu_device}/${"Infinity"===this.total_project_slot.hyperaccel_lpu_device?"∞":this._prefixFormatWithoutTrailingZeros(this.total_project_slot.hyperaccel_lpu_device,2)} Hyperaccel LPUs"
                          ></lablup-progress-bar>
                          <div class="layout vertical center center-justified">
                            <span class="percentage start-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.used_project_slot_percent.hyperaccel_lpu_device,1),"%")}
                            </span>
                            <span class="percentage end-bar">
                              ${this._numberWithPostfix(this._prefixFormatWithoutTrailingZeros(this.total_project_slot.hyperaccel_lpu_device,1),"%")}
                            </span>
                          </div>
                        </div>
                      `:d``}
                </div>
                <div class="flex"></div>
              </div>
            </div>
          `:d``}
    `}};e([t({type:Boolean})],et.prototype,"is_connected",void 0),e([t({type:String})],et.prototype,"direction",void 0),e([t({type:String})],et.prototype,"location",void 0),e([t({type:Object})],et.prototype,"aliases",void 0),e([t({type:Object})],et.prototype,"total_slot",void 0),e([t({type:Object})],et.prototype,"total_resource_group_slot",void 0),e([t({type:Object})],et.prototype,"total_project_slot",void 0),e([t({type:Object})],et.prototype,"used_slot",void 0),e([t({type:Object})],et.prototype,"used_resource_group_slot",void 0),e([t({type:Object})],et.prototype,"used_project_slot",void 0),e([t({type:Object})],et.prototype,"available_slot",void 0),e([t({type:Number})],et.prototype,"concurrency_used",void 0),e([t({type:Number})],et.prototype,"concurrency_max",void 0),e([t({type:Number})],et.prototype,"concurrency_limit",void 0),e([t({type:Object})],et.prototype,"used_slot_percent",void 0),e([t({type:Object})],et.prototype,"used_resource_group_slot_percent",void 0),e([t({type:Object})],et.prototype,"used_project_slot_percent",void 0),e([t({type:String})],et.prototype,"default_language",void 0),e([t({type:Boolean})],et.prototype,"_status",void 0),e([t({type:Number})],et.prototype,"num_sessions",void 0),e([t({type:String})],et.prototype,"scaling_group",void 0),e([t({type:Array})],et.prototype,"scaling_groups",void 0),e([t({type:Array})],et.prototype,"sessions_list",void 0),e([t({type:Boolean})],et.prototype,"metric_updating",void 0),e([t({type:Boolean})],et.prototype,"metadata_updating",void 0),e([t({type:Boolean})],et.prototype,"aggregate_updating",void 0),e([t({type:Object})],et.prototype,"scaling_group_selection_box",void 0),e([t({type:Boolean})],et.prototype,"project_resource_monitor",void 0),e([t({type:Object})],et.prototype,"resourceBroker",void 0),e([E("#resource-gauges")],et.prototype,"resourceGauge",void 0),et=e([i("backend-ai-resource-monitor")],et);let tt=class extends r{constructor(){super(...arguments),this.title="",this.message="",this.panelId="",this.horizontalsize="",this.headerColor="",this.elevation=1,this.autowidth=!1,this.width=350,this.widthpct=0,this.height=0,this.marginWidth=14,this.minwidth=0,this.maxwidth=0,this.pinned=!1,this.disabled=!1,this.narrow=!1,this.noheader=!1,this.scrollableY=!1}static get styles(){return[o,n,c`
        div.card {
          display: block;
          background: var(
            --token-colorBgContainer,
            --general-background-color,
            #ffffff
          );
          box-sizing: border-box;
          margin: 0 !important;
          padding: 0;
          border-radius: var(--token-borderRadiusLG);
          width: 280px;
          line-height: 1.1;
          color: var(--token-colorText);
          border: 1px solid var(--token-colorBorderSecondary, #424242);
        }

        div.card > h4 {
          background-color: var(--token-colorBgContainer, #ffffff);
          color: var(--token-colorText, #000000);
          font-size: var(--token-fontSize, 14px);
          font-weight: 400;
          height: 48px;
          padding: 5px 15px 5px 20px;
          margin: 0 0 10px 0;
          border-radius: var(--token-borderRadiusLG) var(--token-borderRadiusLG)
            0 0;
          border-bottom: 1px solid var(--token-colorBorderSecondary, #ddd);
          display: flex;
          white-space: nowrap;
          text-overflow: ellipsis;
          overflow: hidden;
        }

        div.card[disabled] {
          background-color: var(
            --token-colorBgContainerDisabled,
            rgba(0, 0, 0, 0.1)
          );
        }

        div.card > div {
          margin: 20px;
          padding-bottom: 0.5rem;
          font-size: 12px;
          overflow-wrap: break-word;
        }

        ul {
          padding-inline-start: 0;
        }

        #button {
          display: none;
        }

        @media screen and (max-width: 1015px) {
          div.card {
            max-width: 700px;
          }
        }

        @media screen and (max-width: 750px) {
          div.card {
            width: auto;
            height: auto !important;
          }
        }

        @media screen and (max-width: 375px) {
          div.card {
            width: 350px;
          }
        }
      `]}render(){return d`
      <link rel="stylesheet" href="resources/custom.css" />
      <div
        class="card"
        id="activity"
        elevation="${this.elevation}"
        ?disabled="${this.disabled}"
      >
        <h4
          id="header"
          class="horizontal center justified layout"
          style="font-weight:bold"
        >
          <span>${this.title}</span>
          <div class="flex"></div>
          <mwc-icon-button
            id="button"
            class="fg"
            icon="close"
            @click="${()=>this._removePanel()}"
          ></mwc-icon-button>
        </h4>
        <div class="content ${this.disabled?"disabled":"enabled"}">
          <slot name="message"></slot>
        </div>
      </div>
    `}firstUpdated(){var e,t,i,r,s,o,n;if(this.pinned||null==this.panelId){const r=null===(e=this.shadowRoot)||void 0===e?void 0:e.getElementById("button");null===(i=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("h4"))||void 0===i||i.removeChild(r)}const a=null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector(".card"),l=null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector(".content"),c=null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("#header");this.autowidth?a.style.width="auto":a.style.width=0!==this.widthpct?this.widthpct+"%":this.width+"px",this.minwidth&&(a.style.minWidth=this.minwidth+"px"),this.maxwidth&&(a.style.minWidth=this.maxwidth+"px"),"2x"===this.horizontalsize?a.style.width=2*this.width+28+"px":"3x"===this.horizontalsize?a.style.width=3*this.width+56+"px":"4x"==this.horizontalsize&&(a.style.width=4*this.width+84+"px"),a.style.margin=this.marginWidth+"px",""!==this.headerColor&&(c.style.backgroundColor=this.headerColor),this.narrow&&((null===(n=this.shadowRoot)||void 0===n?void 0:n.querySelector("div.card > div")).style.margin="0",c.style.marginBottom="0"),this.height>0&&(130==this.height?a.style.height="fit-content":(l.style.height=this.height-70+"px",a.style.height=this.height+"px")),this.noheader&&(c.style.display="none"),this.scrollableY&&(l.style.overflowY="auto",l.style.overflowX="hidden")}_removePanel(){}};e([t({type:String})],tt.prototype,"title",void 0),e([t({type:String})],tt.prototype,"message",void 0),e([t({type:String})],tt.prototype,"panelId",void 0),e([t({type:String})],tt.prototype,"horizontalsize",void 0),e([t({type:String})],tt.prototype,"headerColor",void 0),e([t({type:Number})],tt.prototype,"elevation",void 0),e([t({type:Boolean})],tt.prototype,"autowidth",void 0),e([t({type:Number})],tt.prototype,"width",void 0),e([t({type:Number})],tt.prototype,"widthpct",void 0),e([t({type:Number})],tt.prototype,"height",void 0),e([t({type:Number})],tt.prototype,"marginWidth",void 0),e([t({type:Number})],tt.prototype,"minwidth",void 0),e([t({type:Number})],tt.prototype,"maxwidth",void 0),e([t({type:Boolean})],tt.prototype,"pinned",void 0),e([t({type:Boolean})],tt.prototype,"disabled",void 0),e([t({type:Boolean})],tt.prototype,"narrow",void 0),e([t({type:Boolean})],tt.prototype,"noheader",void 0),e([t({type:Boolean})],tt.prototype,"scrollableY",void 0),tt=e([i("lablup-activity-panel")],tt);const it=c`
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
`,rt=c`
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
`;var st=navigator.userAgent,ot=navigator.platform,nt=/gecko\/\d/i.test(st),at=/MSIE \d/.test(st),lt=/Trident\/(?:[7-9]|\d{2,})\..*rv:(\d+)/.exec(st),ct=/Edge\/(\d+)/.exec(st),dt=at||lt||ct,ut=dt&&(at?document.documentMode||6:+(ct||lt)[1]),ht=!ct&&/WebKit\//.test(st),pt=ht&&/Qt\/\d+\.\d+/.test(st),mt=!ct&&/Chrome\//.test(st),ft=/Opera\//.test(st),gt=/Apple Computer/.test(navigator.vendor),vt=/Mac OS X 1\d\D([8-9]|\d\d)\D/.test(st),bt=/PhantomJS/.test(st),_t=gt&&(/Mobile\/\w+/.test(st)||navigator.maxTouchPoints>2),yt=/Android/.test(st),xt=_t||yt||/webOS|BlackBerry|Opera Mini|Opera Mobi|IEMobile/i.test(st),wt=_t||/Mac/.test(ot),kt=/\bCrOS\b/.test(st),Ct=/win/i.test(ot),St=ft&&st.match(/Version\/(\d*\.\d*)/);St&&(St=Number(St[1])),St&&St>=15&&(ft=!1,ht=!0);var Tt=wt&&(pt||ft&&(null==St||St<12.11)),Mt=nt||dt&&ut>=9;function Pt(e){return new RegExp("(^|\\s)"+e+"(?:$|\\s)\\s*")}var $t,Et=function(e,t){let i=e.className,r=Pt(t).exec(i);if(r){let t=i.slice(r.index+r[0].length);e.className=i.slice(0,r.index)+(t?r[1]+t:"")}};function Lt(e){for(let t=e.childNodes.length;t>0;--t)e.removeChild(e.firstChild);return e}function Rt(e,t){return Lt(e).appendChild(t)}function At(e,t,i,r){let s=document.createElement(e);if(i&&(s.className=i),r&&(s.style.cssText=r),"string"==typeof t)s.appendChild(document.createTextNode(t));else if(t)for(let e=0;e<t.length;++e)s.appendChild(t[e]);return s}function It(e,t,i,r){let s=At(e,t,i,r);return s.setAttribute("role","presentation"),s}function Nt(e,t){if(3==t.nodeType&&(t=t.parentNode),e.contains)return e.contains(t);do{if(11==t.nodeType&&(t=t.host),t==e)return!0}while(t=t.parentNode)}function Dt(){let e;try{e=document.activeElement}catch(t){e=document.body||null}for(;e&&e.shadowRoot&&e.shadowRoot.activeElement;)e=e.shadowRoot.activeElement;return e}function Ot(e,t){let i=e.className;Pt(t).test(i)||(e.className+=(i?" ":"")+t)}function Ft(e,t){let i=e.split(" ");for(let e=0;e<i.length;e++)i[e]&&!Pt(i[e]).test(t)&&(t+=" "+i[e]);return t}$t=document.createRange?function(e,t,i,r){let s=document.createRange();return s.setEnd(r||e,i),s.setStart(e,t),s}:function(e,t,i){let r=document.body.createTextRange();try{r.moveToElementText(e.parentNode)}catch(e){return r}return r.collapse(!0),r.moveEnd("character",i),r.moveStart("character",t),r};var zt=function(e){e.select()};function Wt(e){let t=Array.prototype.slice.call(arguments,1);return function(){return e.apply(null,t)}}function Bt(e,t,i){t||(t={});for(let r in e)!e.hasOwnProperty(r)||!1===i&&t.hasOwnProperty(r)||(t[r]=e[r]);return t}function jt(e,t,i,r,s){null==t&&-1==(t=e.search(/[^\s\u00a0]/))&&(t=e.length);for(let o=r||0,n=s||0;;){let r=e.indexOf("\t",o);if(r<0||r>=t)return n+(t-o);n+=r-o,n+=i-n%i,o=r+1}}_t?zt=function(e){e.selectionStart=0,e.selectionEnd=e.value.length}:dt&&(zt=function(e){try{e.select()}catch(e){}});var Ht=class{constructor(){this.id=null,this.f=null,this.time=0,this.handler=Wt(this.onTimeout,this)}onTimeout(e){e.id=0,e.time<=+new Date?e.f():setTimeout(e.handler,e.time-+new Date)}set(e,t){this.f=t;const i=+new Date+e;(!this.id||i<this.time)&&(clearTimeout(this.id),this.id=setTimeout(this.handler,e),this.time=i)}};function Ut(e,t){for(let i=0;i<e.length;++i)if(e[i]==t)return i;return-1}var Gt=50,Vt={toString:function(){return"CodeMirror.Pass"}},qt={scroll:!1},Zt={origin:"*mouse"},Kt={origin:"+move"};function Xt(e,t,i){for(let r=0,s=0;;){let o=e.indexOf("\t",r);-1==o&&(o=e.length);let n=o-r;if(o==e.length||s+n>=t)return r+Math.min(n,t-s);if(s+=o-r,s+=i-s%i,r=o+1,s>=t)return r}}var Yt=[""];function Jt(e){for(;Yt.length<=e;)Yt.push(Qt(Yt)+" ");return Yt[e]}function Qt(e){return e[e.length-1]}function ei(e,t){let i=[];for(let r=0;r<e.length;r++)i[r]=t(e[r],r);return i}function ti(){}function ii(e,t){let i;return Object.create?i=Object.create(e):(ti.prototype=e,i=new ti),t&&Bt(t,i),i}var ri=/[\u00df\u0587\u0590-\u05f4\u0600-\u06ff\u3040-\u309f\u30a0-\u30ff\u3400-\u4db5\u4e00-\u9fcc\uac00-\ud7af]/;function si(e){return/\w/.test(e)||e>""&&(e.toUpperCase()!=e.toLowerCase()||ri.test(e))}function oi(e,t){return t?!!(t.source.indexOf("\\w")>-1&&si(e))||t.test(e):si(e)}function ni(e){for(let t in e)if(e.hasOwnProperty(t)&&e[t])return!1;return!0}var ai=/[\u0300-\u036f\u0483-\u0489\u0591-\u05bd\u05bf\u05c1\u05c2\u05c4\u05c5\u05c7\u0610-\u061a\u064b-\u065e\u0670\u06d6-\u06dc\u06de-\u06e4\u06e7\u06e8\u06ea-\u06ed\u0711\u0730-\u074a\u07a6-\u07b0\u07eb-\u07f3\u0816-\u0819\u081b-\u0823\u0825-\u0827\u0829-\u082d\u0900-\u0902\u093c\u0941-\u0948\u094d\u0951-\u0955\u0962\u0963\u0981\u09bc\u09be\u09c1-\u09c4\u09cd\u09d7\u09e2\u09e3\u0a01\u0a02\u0a3c\u0a41\u0a42\u0a47\u0a48\u0a4b-\u0a4d\u0a51\u0a70\u0a71\u0a75\u0a81\u0a82\u0abc\u0ac1-\u0ac5\u0ac7\u0ac8\u0acd\u0ae2\u0ae3\u0b01\u0b3c\u0b3e\u0b3f\u0b41-\u0b44\u0b4d\u0b56\u0b57\u0b62\u0b63\u0b82\u0bbe\u0bc0\u0bcd\u0bd7\u0c3e-\u0c40\u0c46-\u0c48\u0c4a-\u0c4d\u0c55\u0c56\u0c62\u0c63\u0cbc\u0cbf\u0cc2\u0cc6\u0ccc\u0ccd\u0cd5\u0cd6\u0ce2\u0ce3\u0d3e\u0d41-\u0d44\u0d4d\u0d57\u0d62\u0d63\u0dca\u0dcf\u0dd2-\u0dd4\u0dd6\u0ddf\u0e31\u0e34-\u0e3a\u0e47-\u0e4e\u0eb1\u0eb4-\u0eb9\u0ebb\u0ebc\u0ec8-\u0ecd\u0f18\u0f19\u0f35\u0f37\u0f39\u0f71-\u0f7e\u0f80-\u0f84\u0f86\u0f87\u0f90-\u0f97\u0f99-\u0fbc\u0fc6\u102d-\u1030\u1032-\u1037\u1039\u103a\u103d\u103e\u1058\u1059\u105e-\u1060\u1071-\u1074\u1082\u1085\u1086\u108d\u109d\u135f\u1712-\u1714\u1732-\u1734\u1752\u1753\u1772\u1773\u17b7-\u17bd\u17c6\u17c9-\u17d3\u17dd\u180b-\u180d\u18a9\u1920-\u1922\u1927\u1928\u1932\u1939-\u193b\u1a17\u1a18\u1a56\u1a58-\u1a5e\u1a60\u1a62\u1a65-\u1a6c\u1a73-\u1a7c\u1a7f\u1b00-\u1b03\u1b34\u1b36-\u1b3a\u1b3c\u1b42\u1b6b-\u1b73\u1b80\u1b81\u1ba2-\u1ba5\u1ba8\u1ba9\u1c2c-\u1c33\u1c36\u1c37\u1cd0-\u1cd2\u1cd4-\u1ce0\u1ce2-\u1ce8\u1ced\u1dc0-\u1de6\u1dfd-\u1dff\u200c\u200d\u20d0-\u20f0\u2cef-\u2cf1\u2de0-\u2dff\u302a-\u302f\u3099\u309a\ua66f-\ua672\ua67c\ua67d\ua6f0\ua6f1\ua802\ua806\ua80b\ua825\ua826\ua8c4\ua8e0-\ua8f1\ua926-\ua92d\ua947-\ua951\ua980-\ua982\ua9b3\ua9b6-\ua9b9\ua9bc\uaa29-\uaa2e\uaa31\uaa32\uaa35\uaa36\uaa43\uaa4c\uaab0\uaab2-\uaab4\uaab7\uaab8\uaabe\uaabf\uaac1\uabe5\uabe8\uabed\udc00-\udfff\ufb1e\ufe00-\ufe0f\ufe20-\ufe26\uff9e\uff9f]/;function li(e){return e.charCodeAt(0)>=768&&ai.test(e)}function ci(e,t,i){for(;(i<0?t>0:t<e.length)&&li(e.charAt(t));)t+=i;return t}function di(e,t,i){let r=t>i?-1:1;for(;;){if(t==i)return t;let s=(t+i)/2,o=r<0?Math.ceil(s):Math.floor(s);if(o==t)return e(o)?t:i;e(o)?i=o:t=o+r}}var ui=null;function hi(e,t,i){let r;ui=null;for(let s=0;s<e.length;++s){let o=e[s];if(o.from<t&&o.to>t)return s;o.to==t&&(o.from!=o.to&&"before"==i?r=s:ui=s),o.from==t&&(o.from!=o.to&&"before"!=i?r=s:ui=s)}return null!=r?r:ui}var pi=function(){let e=/[\u0590-\u05f4\u0600-\u06ff\u0700-\u08ac]/,t=/[stwN]/,i=/[LRr]/,r=/[Lb1n]/,s=/[1n]/;function o(e,t,i){this.level=e,this.from=t,this.to=i}return function(n,a){let l="ltr"==a?"L":"R";if(0==n.length||"ltr"==a&&!e.test(n))return!1;let c=n.length,d=[];for(let e=0;e<c;++e)d.push((u=n.charCodeAt(e))<=247?"bbbbbbbbbtstwsbbbbbbbbbbbbbbssstwNN%%%NNNNNN,N,N1111111111NNNNNNNLLLLLLLLLLLLLLLLLLLLLLLLLLNNNNNNLLLLLLLLLLLLLLLLLLLLLLLLLLNNNNbbbbbbsbbbbbbbbbbbbbbbbbbbbbbbbbb,N%%%%NNNNLNNNNN%%11NLNNN1LNNNNNLLLLLLLLLLLLLLLLLLLLLLLNLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLN".charAt(u):1424<=u&&u<=1524?"R":1536<=u&&u<=1785?"nnnnnnNNr%%r,rNNmmmmmmmmmmmrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrmmmmmmmmmmmmmmmmmmmmmnnnnnnnnnn%nnrrrmrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrmmmmmmmnNmmmmmmrrmmNmmmmrr1111111111".charAt(u-1536):1774<=u&&u<=2220?"r":8192<=u&&u<=8203?"w":8204==u?"b":"L");var u;for(let e=0,t=l;e<c;++e){let i=d[e];"m"==i?d[e]=t:t=i}for(let e=0,t=l;e<c;++e){let r=d[e];"1"==r&&"r"==t?d[e]="n":i.test(r)&&(t=r,"r"==r&&(d[e]="R"))}for(let e=1,t=d[0];e<c-1;++e){let i=d[e];"+"==i&&"1"==t&&"1"==d[e+1]?d[e]="1":","!=i||t!=d[e+1]||"1"!=t&&"n"!=t||(d[e]=t),t=i}for(let e=0;e<c;++e){let t=d[e];if(","==t)d[e]="N";else if("%"==t){let t;for(t=e+1;t<c&&"%"==d[t];++t);let i=e&&"!"==d[e-1]||t<c&&"1"==d[t]?"1":"N";for(let r=e;r<t;++r)d[r]=i;e=t-1}}for(let e=0,t=l;e<c;++e){let r=d[e];"L"==t&&"1"==r?d[e]="L":i.test(r)&&(t=r)}for(let e=0;e<c;++e)if(t.test(d[e])){let i;for(i=e+1;i<c&&t.test(d[i]);++i);let r="L"==(e?d[e-1]:l),s=r==("L"==(i<c?d[i]:l))?r?"L":"R":l;for(let t=e;t<i;++t)d[t]=s;e=i-1}let h,p=[];for(let e=0;e<c;)if(r.test(d[e])){let t=e;for(++e;e<c&&r.test(d[e]);++e);p.push(new o(0,t,e))}else{let t=e,i=p.length,r="rtl"==a?1:0;for(++e;e<c&&"L"!=d[e];++e);for(let n=t;n<e;)if(s.test(d[n])){t<n&&(p.splice(i,0,new o(1,t,n)),i+=r);let a=n;for(++n;n<e&&s.test(d[n]);++n);p.splice(i,0,new o(2,a,n)),i+=r,t=n}else++n;t<e&&p.splice(i,0,new o(1,t,e))}return"ltr"==a&&(1==p[0].level&&(h=n.match(/^\s+/))&&(p[0].from=h[0].length,p.unshift(new o(0,0,h[0].length))),1==Qt(p).level&&(h=n.match(/\s+$/))&&(Qt(p).to-=h[0].length,p.push(new o(0,c-h[0].length,c)))),"rtl"==a?p.reverse():p}}();function mi(e,t){let i=e.order;return null==i&&(i=e.order=pi(e.text,t)),i}var fi=[],gi=function(e,t,i){if(e.addEventListener)e.addEventListener(t,i,!1);else if(e.attachEvent)e.attachEvent("on"+t,i);else{let r=e._handlers||(e._handlers={});r[t]=(r[t]||fi).concat(i)}};function vi(e,t){return e._handlers&&e._handlers[t]||fi}function bi(e,t,i){if(e.removeEventListener)e.removeEventListener(t,i,!1);else if(e.detachEvent)e.detachEvent("on"+t,i);else{let r=e._handlers,s=r&&r[t];if(s){let e=Ut(s,i);e>-1&&(r[t]=s.slice(0,e).concat(s.slice(e+1)))}}}function _i(e,t){let i=vi(e,t);if(!i.length)return;let r=Array.prototype.slice.call(arguments,2);for(let e=0;e<i.length;++e)i[e].apply(null,r)}function yi(e,t,i){return"string"==typeof t&&(t={type:t,preventDefault:function(){this.defaultPrevented=!0}}),_i(e,i||t.type,e,t),Ti(t)||t.codemirrorIgnore}function xi(e){let t=e._handlers&&e._handlers.cursorActivity;if(!t)return;let i=e.curOp.cursorActivityHandlers||(e.curOp.cursorActivityHandlers=[]);for(let e=0;e<t.length;++e)-1==Ut(i,t[e])&&i.push(t[e])}function wi(e,t){return vi(e,t).length>0}function ki(e){e.prototype.on=function(e,t){gi(this,e,t)},e.prototype.off=function(e,t){bi(this,e,t)}}function Ci(e){e.preventDefault?e.preventDefault():e.returnValue=!1}function Si(e){e.stopPropagation?e.stopPropagation():e.cancelBubble=!0}function Ti(e){return null!=e.defaultPrevented?e.defaultPrevented:0==e.returnValue}function Mi(e){Ci(e),Si(e)}function Pi(e){return e.target||e.srcElement}function $i(e){let t=e.which;return null==t&&(1&e.button?t=1:2&e.button?t=3:4&e.button&&(t=2)),wt&&e.ctrlKey&&1==t&&(t=3),t}var Ei,Li,Ri=function(){if(dt&&ut<9)return!1;let e=At("div");return"draggable"in e||"dragDrop"in e}();function Ai(e){if(null==Ei){let t=At("span","​");Rt(e,At("span",[t,document.createTextNode("x")])),0!=e.firstChild.offsetHeight&&(Ei=t.offsetWidth<=1&&t.offsetHeight>2&&!(dt&&ut<8))}let t=Ei?At("span","​"):At("span"," ",null,"display: inline-block; width: 1px; margin-right: -1px");return t.setAttribute("cm-text",""),t}function Ii(e){if(null!=Li)return Li;let t=Rt(e,document.createTextNode("AخA")),i=$t(t,0,1).getBoundingClientRect(),r=$t(t,1,2).getBoundingClientRect();return Lt(e),!(!i||i.left==i.right)&&(Li=r.right-i.right<3)}var Ni=3!="\n\nb".split(/\n/).length?e=>{let t=0,i=[],r=e.length;for(;t<=r;){let r=e.indexOf("\n",t);-1==r&&(r=e.length);let s=e.slice(t,"\r"==e.charAt(r-1)?r-1:r),o=s.indexOf("\r");-1!=o?(i.push(s.slice(0,o)),t+=o+1):(i.push(s),t=r+1)}return i}:e=>e.split(/\r\n?|\n/),Di=window.getSelection?e=>{try{return e.selectionStart!=e.selectionEnd}catch(e){return!1}}:e=>{let t;try{t=e.ownerDocument.selection.createRange()}catch(e){}return!(!t||t.parentElement()!=e)&&0!=t.compareEndPoints("StartToEnd",t)},Oi=(()=>{let e=At("div");return"oncopy"in e||(e.setAttribute("oncopy","return;"),"function"==typeof e.oncopy)})(),Fi=null;var zi={},Wi={};function Bi(e,t){arguments.length>2&&(t.dependencies=Array.prototype.slice.call(arguments,2)),zi[e]=t}function ji(e){if("string"==typeof e&&Wi.hasOwnProperty(e))e=Wi[e];else if(e&&"string"==typeof e.name&&Wi.hasOwnProperty(e.name)){let t=Wi[e.name];"string"==typeof t&&(t={name:t}),(e=ii(t,e)).name=t.name}else{if("string"==typeof e&&/^[\w\-]+\/[\w\-]+\+xml$/.test(e))return ji("application/xml");if("string"==typeof e&&/^[\w\-]+\/[\w\-]+\+json$/.test(e))return ji("application/json")}return"string"==typeof e?{name:e}:e||{name:"null"}}function Hi(e,t){t=ji(t);let i=zi[t.name];if(!i)return Hi(e,"text/plain");let r=i(e,t);if(Ui.hasOwnProperty(t.name)){let e=Ui[t.name];for(let t in e)e.hasOwnProperty(t)&&(r.hasOwnProperty(t)&&(r["_"+t]=r[t]),r[t]=e[t])}if(r.name=t.name,t.helperType&&(r.helperType=t.helperType),t.modeProps)for(let e in t.modeProps)r[e]=t.modeProps[e];return r}var Ui={};function Gi(e,t){Bt(t,Ui.hasOwnProperty(e)?Ui[e]:Ui[e]={})}function Vi(e,t){if(!0===t)return t;if(e.copyState)return e.copyState(t);let i={};for(let e in t){let r=t[e];r instanceof Array&&(r=r.concat([])),i[e]=r}return i}function qi(e,t){let i;for(;e.innerMode&&(i=e.innerMode(t),i&&i.mode!=e);)t=i.state,e=i.mode;return i||{mode:e,state:t}}function Zi(e,t,i){return!e.startState||e.startState(t,i)}var Ki=class{constructor(e,t,i){this.pos=this.start=0,this.string=e,this.tabSize=t||8,this.lastColumnPos=this.lastColumnValue=0,this.lineStart=0,this.lineOracle=i}eol(){return this.pos>=this.string.length}sol(){return this.pos==this.lineStart}peek(){return this.string.charAt(this.pos)||void 0}next(){if(this.pos<this.string.length)return this.string.charAt(this.pos++)}eat(e){let t,i=this.string.charAt(this.pos);if(t="string"==typeof e?i==e:i&&(e.test?e.test(i):e(i)),t)return++this.pos,i}eatWhile(e){let t=this.pos;for(;this.eat(e););return this.pos>t}eatSpace(){let e=this.pos;for(;/[\s\u00a0]/.test(this.string.charAt(this.pos));)++this.pos;return this.pos>e}skipToEnd(){this.pos=this.string.length}skipTo(e){let t=this.string.indexOf(e,this.pos);if(t>-1)return this.pos=t,!0}backUp(e){this.pos-=e}column(){return this.lastColumnPos<this.start&&(this.lastColumnValue=jt(this.string,this.start,this.tabSize,this.lastColumnPos,this.lastColumnValue),this.lastColumnPos=this.start),this.lastColumnValue-(this.lineStart?jt(this.string,this.lineStart,this.tabSize):0)}indentation(){return jt(this.string,null,this.tabSize)-(this.lineStart?jt(this.string,this.lineStart,this.tabSize):0)}match(e,t,i){if("string"!=typeof e){let i=this.string.slice(this.pos).match(e);return i&&i.index>0?null:(i&&!1!==t&&(this.pos+=i[0].length),i)}{let r=e=>i?e.toLowerCase():e;if(r(this.string.substr(this.pos,e.length))==r(e))return!1!==t&&(this.pos+=e.length),!0}}current(){return this.string.slice(this.start,this.pos)}hideFirstChars(e,t){this.lineStart+=e;try{return t()}finally{this.lineStart-=e}}lookAhead(e){let t=this.lineOracle;return t&&t.lookAhead(e)}baseToken(){let e=this.lineOracle;return e&&e.baseToken(this.pos)}};function Xi(e,t){if((t-=e.first)<0||t>=e.size)throw new Error("There is no line "+(t+e.first)+" in the document.");let i=e;for(;!i.lines;)for(let e=0;;++e){let r=i.children[e],s=r.chunkSize();if(t<s){i=r;break}t-=s}return i.lines[t]}function Yi(e,t,i){let r=[],s=t.line;return e.iter(t.line,i.line+1,(e=>{let o=e.text;s==i.line&&(o=o.slice(0,i.ch)),s==t.line&&(o=o.slice(t.ch)),r.push(o),++s})),r}function Ji(e,t,i){let r=[];return e.iter(t,i,(e=>{r.push(e.text)})),r}function Qi(e,t){let i=t-e.height;if(i)for(let t=e;t;t=t.parent)t.height+=i}function er(e){if(null==e.parent)return null;let t=e.parent,i=Ut(t.lines,e);for(let e=t.parent;e;t=e,e=e.parent)for(let r=0;e.children[r]!=t;++r)i+=e.children[r].chunkSize();return i+t.first}function tr(e,t){let i=e.first;e:do{for(let r=0;r<e.children.length;++r){let s=e.children[r],o=s.height;if(t<o){e=s;continue e}t-=o,i+=s.chunkSize()}return i}while(!e.lines);let r=0;for(;r<e.lines.length;++r){let i=e.lines[r].height;if(t<i)break;t-=i}return i+r}function ir(e,t){return t>=e.first&&t<e.first+e.size}function rr(e,t){return String(e.lineNumberFormatter(t+e.firstLineNumber))}function sr(e,t,i=null){if(!(this instanceof sr))return new sr(e,t,i);this.line=e,this.ch=t,this.sticky=i}function or(e,t){return e.line-t.line||e.ch-t.ch}function nr(e,t){return e.sticky==t.sticky&&0==or(e,t)}function ar(e){return sr(e.line,e.ch)}function lr(e,t){return or(e,t)<0?t:e}function cr(e,t){return or(e,t)<0?e:t}function dr(e,t){return Math.max(e.first,Math.min(t,e.first+e.size-1))}function ur(e,t){if(t.line<e.first)return sr(e.first,0);let i=e.first+e.size-1;return t.line>i?sr(i,Xi(e,i).text.length):function(e,t){let i=e.ch;return null==i||i>t?sr(e.line,t):i<0?sr(e.line,0):e}(t,Xi(e,t.line).text.length)}function hr(e,t){let i=[];for(let r=0;r<t.length;r++)i[r]=ur(e,t[r]);return i}var pr=class{constructor(e,t){this.state=e,this.lookAhead=t}},mr=class{constructor(e,t,i,r){this.state=t,this.doc=e,this.line=i,this.maxLookAhead=r||0,this.baseTokens=null,this.baseTokenPos=1}lookAhead(e){let t=this.doc.getLine(this.line+e);return null!=t&&e>this.maxLookAhead&&(this.maxLookAhead=e),t}baseToken(e){if(!this.baseTokens)return null;for(;this.baseTokens[this.baseTokenPos]<=e;)this.baseTokenPos+=2;let t=this.baseTokens[this.baseTokenPos+1];return{type:t&&t.replace(/( |^)overlay .*/,""),size:this.baseTokens[this.baseTokenPos]-e}}nextLine(){this.line++,this.maxLookAhead>0&&this.maxLookAhead--}static fromSaved(e,t,i){return t instanceof pr?new mr(e,Vi(e.mode,t.state),i,t.lookAhead):new mr(e,Vi(e.mode,t),i)}save(e){let t=!1!==e?Vi(this.doc.mode,this.state):this.state;return this.maxLookAhead>0?new pr(t,this.maxLookAhead):t}};function fr(e,t,i,r){let s=[e.state.modeGen],o={};Cr(e,t.text,e.doc.mode,i,((e,t)=>s.push(e,t)),o,r);let n=i.state;for(let r=0;r<e.state.overlays.length;++r){i.baseTokens=s;let a=e.state.overlays[r],l=1,c=0;i.state=!0,Cr(e,t.text,a.mode,i,((e,t)=>{let i=l;for(;c<e;){let t=s[l];t>e&&s.splice(l,1,e,s[l+1],t),l+=2,c=Math.min(e,t)}if(t)if(a.opaque)s.splice(i,l-i,e,"overlay "+t),l=i+2;else for(;i<l;i+=2){let e=s[i+1];s[i+1]=(e?e+" ":"")+"overlay "+t}}),o),i.state=n,i.baseTokens=null,i.baseTokenPos=1}return{styles:s,classes:o.bgClass||o.textClass?o:null}}function gr(e,t,i){if(!t.styles||t.styles[0]!=e.state.modeGen){let r=vr(e,er(t)),s=t.text.length>e.options.maxHighlightLength&&Vi(e.doc.mode,r.state),o=fr(e,t,r);s&&(r.state=s),t.stateAfter=r.save(!s),t.styles=o.styles,o.classes?t.styleClasses=o.classes:t.styleClasses&&(t.styleClasses=null),i===e.doc.highlightFrontier&&(e.doc.modeFrontier=Math.max(e.doc.modeFrontier,++e.doc.highlightFrontier))}return t.styles}function vr(e,t,i){let r=e.doc,s=e.display;if(!r.mode.startState)return new mr(r,!0,t);let o=function(e,t,i){let r,s,o=e.doc,n=i?-1:t-(e.doc.mode.innerMode?1e3:100);for(let a=t;a>n;--a){if(a<=o.first)return o.first;let t=Xi(o,a-1),n=t.stateAfter;if(n&&(!i||a+(n instanceof pr?n.lookAhead:0)<=o.modeFrontier))return a;let l=jt(t.text,null,e.options.tabSize);(null==s||r>l)&&(s=a-1,r=l)}return s}(e,t,i),n=o>r.first&&Xi(r,o-1).stateAfter,a=n?mr.fromSaved(r,n,o):new mr(r,Zi(r.mode),o);return r.iter(o,t,(i=>{br(e,i.text,a);let r=a.line;i.stateAfter=r==t-1||r%5==0||r>=s.viewFrom&&r<s.viewTo?a.save():null,a.nextLine()})),i&&(r.modeFrontier=a.line),a}function br(e,t,i,r){let s=e.doc.mode,o=new Ki(t,e.options.tabSize,i);for(o.start=o.pos=r||0,""==t&&_r(s,i.state);!o.eol();)yr(s,o,i.state),o.start=o.pos}function _r(e,t){if(e.blankLine)return e.blankLine(t);if(!e.innerMode)return;let i=qi(e,t);return i.mode.blankLine?i.mode.blankLine(i.state):void 0}function yr(e,t,i,r){for(let s=0;s<10;s++){r&&(r[0]=qi(e,i).mode);let s=e.token(t,i);if(t.pos>t.start)return s}throw new Error("Mode "+e.name+" failed to advance stream.")}var xr=class{constructor(e,t,i){this.start=e.start,this.end=e.pos,this.string=e.current(),this.type=t||null,this.state=i}};function wr(e,t,i,r){let s,o,n=e.doc,a=n.mode,l=Xi(n,(t=ur(n,t)).line),c=vr(e,t.line,i),d=new Ki(l.text,e.options.tabSize,c);for(r&&(o=[]);(r||d.pos<t.ch)&&!d.eol();)d.start=d.pos,s=yr(a,d,c.state),r&&o.push(new xr(d,s,Vi(n.mode,c.state)));return r?o:new xr(d,s,c.state)}function kr(e,t){if(e)for(;;){let i=e.match(/(?:^|\s+)line-(background-)?(\S+)/);if(!i)break;e=e.slice(0,i.index)+e.slice(i.index+i[0].length);let r=i[1]?"bgClass":"textClass";null==t[r]?t[r]=i[2]:new RegExp("(?:^|\\s)"+i[2]+"(?:$|\\s)").test(t[r])||(t[r]+=" "+i[2])}return e}function Cr(e,t,i,r,s,o,n){let a=i.flattenSpans;null==a&&(a=e.options.flattenSpans);let l,c=0,d=null,u=new Ki(t,e.options.tabSize,r),h=e.options.addModeClass&&[null];for(""==t&&kr(_r(i,r.state),o);!u.eol();){if(u.pos>e.options.maxHighlightLength?(a=!1,n&&br(e,t,r,u.pos),u.pos=t.length,l=null):l=kr(yr(i,u,r.state,h),o),h){let e=h[0].name;e&&(l="m-"+(l?e+" "+l:e))}if(!a||d!=l){for(;c<u.start;)c=Math.min(u.start,c+5e3),s(c,d);d=l}u.start=u.pos}for(;c<u.pos;){let e=Math.min(u.pos,c+5e3);s(e,d),c=e}}var Sr=!1,Tr=!1;function Mr(e,t,i){this.marker=e,this.from=t,this.to=i}function Pr(e,t){if(e)for(let i=0;i<e.length;++i){let r=e[i];if(r.marker==t)return r}}function $r(e,t){let i;for(let r=0;r<e.length;++r)e[r]!=t&&(i||(i=[])).push(e[r]);return i}function Er(e,t){if(t.full)return null;let i=ir(e,t.from.line)&&Xi(e,t.from.line).markedSpans,r=ir(e,t.to.line)&&Xi(e,t.to.line).markedSpans;if(!i&&!r)return null;let s=t.from.ch,o=t.to.ch,n=0==or(t.from,t.to),a=function(e,t,i){let r;if(e)for(let s=0;s<e.length;++s){let o=e[s],n=o.marker;if(null==o.from||(n.inclusiveLeft?o.from<=t:o.from<t)||o.from==t&&"bookmark"==n.type&&(!i||!o.marker.insertLeft)){let e=null==o.to||(n.inclusiveRight?o.to>=t:o.to>t);(r||(r=[])).push(new Mr(n,o.from,e?null:o.to))}}return r}(i,s,n),l=function(e,t,i){let r;if(e)for(let s=0;s<e.length;++s){let o=e[s],n=o.marker;if(null==o.to||(n.inclusiveRight?o.to>=t:o.to>t)||o.from==t&&"bookmark"==n.type&&(!i||o.marker.insertLeft)){let e=null==o.from||(n.inclusiveLeft?o.from<=t:o.from<t);(r||(r=[])).push(new Mr(n,e?null:o.from-t,null==o.to?null:o.to-t))}}return r}(r,o,n),c=1==t.text.length,d=Qt(t.text).length+(c?s:0);if(a)for(let e=0;e<a.length;++e){let t=a[e];if(null==t.to){let e=Pr(l,t.marker);e?c&&(t.to=null==e.to?null:e.to+d):t.to=s}}if(l)for(let e=0;e<l.length;++e){let t=l[e];if(null!=t.to&&(t.to+=d),null==t.from){Pr(a,t.marker)||(t.from=d,c&&(a||(a=[])).push(t))}else t.from+=d,c&&(a||(a=[])).push(t)}a&&(a=Lr(a)),l&&l!=a&&(l=Lr(l));let u=[a];if(!c){let e,i=t.text.length-2;if(i>0&&a)for(let t=0;t<a.length;++t)null==a[t].to&&(e||(e=[])).push(new Mr(a[t].marker,null,null));for(let t=0;t<i;++t)u.push(e);u.push(l)}return u}function Lr(e){for(let t=0;t<e.length;++t){let i=e[t];null!=i.from&&i.from==i.to&&!1!==i.marker.clearWhenEmpty&&e.splice(t--,1)}return e.length?e:null}function Rr(e){let t=e.markedSpans;if(t){for(let i=0;i<t.length;++i)t[i].marker.detachLine(e);e.markedSpans=null}}function Ar(e,t){if(t){for(let i=0;i<t.length;++i)t[i].marker.attachLine(e);e.markedSpans=t}}function Ir(e){return e.inclusiveLeft?-1:0}function Nr(e){return e.inclusiveRight?1:0}function Dr(e,t){let i=e.lines.length-t.lines.length;if(0!=i)return i;let r=e.find(),s=t.find(),o=or(r.from,s.from)||Ir(e)-Ir(t);if(o)return-o;let n=or(r.to,s.to)||Nr(e)-Nr(t);return n||t.id-e.id}function Or(e,t){let i,r=Tr&&e.markedSpans;if(r)for(let e,s=0;s<r.length;++s)e=r[s],e.marker.collapsed&&null==(t?e.from:e.to)&&(!i||Dr(i,e.marker)<0)&&(i=e.marker);return i}function Fr(e){return Or(e,!0)}function zr(e){return Or(e,!1)}function Wr(e,t){let i,r=Tr&&e.markedSpans;if(r)for(let e=0;e<r.length;++e){let s=r[e];s.marker.collapsed&&(null==s.from||s.from<t)&&(null==s.to||s.to>t)&&(!i||Dr(i,s.marker)<0)&&(i=s.marker)}return i}function Br(e,t,i,r,s){let o=Xi(e,t),n=Tr&&o.markedSpans;if(n)for(let e=0;e<n.length;++e){let t=n[e];if(!t.marker.collapsed)continue;let o=t.marker.find(0),a=or(o.from,i)||Ir(t.marker)-Ir(s),l=or(o.to,r)||Nr(t.marker)-Nr(s);if(!(a>=0&&l<=0||a<=0&&l>=0)&&(a<=0&&(t.marker.inclusiveRight&&s.inclusiveLeft?or(o.to,i)>=0:or(o.to,i)>0)||a>=0&&(t.marker.inclusiveRight&&s.inclusiveLeft?or(o.from,r)<=0:or(o.from,r)<0)))return!0}}function jr(e){let t;for(;t=Fr(e);)e=t.find(-1,!0).line;return e}function Hr(e,t){let i=Xi(e,t),r=jr(i);return i==r?t:er(r)}function Ur(e,t){if(t>e.lastLine())return t;let i,r=Xi(e,t);if(!Gr(e,r))return t;for(;i=zr(r);)r=i.find(1,!0).line;return er(r)+1}function Gr(e,t){let i=Tr&&t.markedSpans;if(i)for(let r,s=0;s<i.length;++s)if(r=i[s],r.marker.collapsed){if(null==r.from)return!0;if(!r.marker.widgetNode&&0==r.from&&r.marker.inclusiveLeft&&Vr(e,t,r))return!0}}function Vr(e,t,i){if(null==i.to){let t=i.marker.find(1,!0);return Vr(e,t.line,Pr(t.line.markedSpans,i.marker))}if(i.marker.inclusiveRight&&i.to==t.text.length)return!0;for(let r,s=0;s<t.markedSpans.length;++s)if(r=t.markedSpans[s],r.marker.collapsed&&!r.marker.widgetNode&&r.from==i.to&&(null==r.to||r.to!=i.from)&&(r.marker.inclusiveLeft||i.marker.inclusiveRight)&&Vr(e,t,r))return!0}function qr(e){let t=0,i=(e=jr(e)).parent;for(let r=0;r<i.lines.length;++r){let s=i.lines[r];if(s==e)break;t+=s.height}for(let e=i.parent;e;i=e,e=i.parent)for(let r=0;r<e.children.length;++r){let s=e.children[r];if(s==i)break;t+=s.height}return t}function Zr(e){if(0==e.height)return 0;let t,i=e.text.length,r=e;for(;t=Fr(r);){let e=t.find(0,!0);r=e.from.line,i+=e.from.ch-e.to.ch}for(r=e;t=zr(r);){let e=t.find(0,!0);i-=r.text.length-e.from.ch,r=e.to.line,i+=r.text.length-e.to.ch}return i}function Kr(e){let t=e.display,i=e.doc;t.maxLine=Xi(i,i.first),t.maxLineLength=Zr(t.maxLine),t.maxLineChanged=!0,i.iter((e=>{let i=Zr(e);i>t.maxLineLength&&(t.maxLineLength=i,t.maxLine=e)}))}var Xr=class{constructor(e,t,i){this.text=e,Ar(this,t),this.height=i?i(this):1}lineNo(){return er(this)}};function Yr(e){e.parent=null,Rr(e)}ki(Xr);var Jr={},Qr={};function es(e,t){if(!e||/^\s*$/.test(e))return null;let i=t.addModeClass?Qr:Jr;return i[e]||(i[e]=e.replace(/\S+/g,"cm-$&"))}function ts(e,t){let i=It("span",null,null,ht?"padding-right: .1px":null),r={pre:It("pre",[i],"CodeMirror-line"),content:i,col:0,pos:0,cm:e,trailingSpace:!1,splitSpaces:e.getOption("lineWrapping")};t.measure={};for(let i=0;i<=(t.rest?t.rest.length:0);i++){let s,o=i?t.rest[i-1]:t.line;r.pos=0,r.addToken=rs,Ii(e.display.measure)&&(s=mi(o,e.doc.direction))&&(r.addToken=ss(r.addToken,s)),r.map=[],ns(o,r,gr(e,o,t!=e.display.externalMeasured&&er(o))),o.styleClasses&&(o.styleClasses.bgClass&&(r.bgClass=Ft(o.styleClasses.bgClass,r.bgClass||"")),o.styleClasses.textClass&&(r.textClass=Ft(o.styleClasses.textClass,r.textClass||""))),0==r.map.length&&r.map.push(0,0,r.content.appendChild(Ai(e.display.measure))),0==i?(t.measure.map=r.map,t.measure.cache={}):((t.measure.maps||(t.measure.maps=[])).push(r.map),(t.measure.caches||(t.measure.caches=[])).push({}))}if(ht){let e=r.content.lastChild;(/\bcm-tab\b/.test(e.className)||e.querySelector&&e.querySelector(".cm-tab"))&&(r.content.className="cm-tab-wrap-hack")}return _i(e,"renderLine",e,t.line,r.pre),r.pre.className&&(r.textClass=Ft(r.pre.className,r.textClass||"")),r}function is(e){let t=At("span","•","cm-invalidchar");return t.title="\\u"+e.charCodeAt(0).toString(16),t.setAttribute("aria-label",t.title),t}function rs(e,t,i,r,s,o,n){if(!t)return;let a,l=e.splitSpaces?function(e,t){if(e.length>1&&!/  /.test(e))return e;let i=t,r="";for(let t=0;t<e.length;t++){let s=e.charAt(t);" "!=s||!i||t!=e.length-1&&32!=e.charCodeAt(t+1)||(s=" "),r+=s,i=" "==s}return r}(t,e.trailingSpace):t,c=e.cm.state.specialChars,d=!1;if(c.test(t)){a=document.createDocumentFragment();let i=0;for(;;){c.lastIndex=i;let r,s=c.exec(t),o=s?s.index-i:t.length-i;if(o){let t=document.createTextNode(l.slice(i,i+o));dt&&ut<9?a.appendChild(At("span",[t])):a.appendChild(t),e.map.push(e.pos,e.pos+o,t),e.col+=o,e.pos+=o}if(!s)break;if(i+=o+1,"\t"==s[0]){let t=e.cm.options.tabSize,i=t-e.col%t;r=a.appendChild(At("span",Jt(i),"cm-tab")),r.setAttribute("role","presentation"),r.setAttribute("cm-text","\t"),e.col+=i}else"\r"==s[0]||"\n"==s[0]?(r=a.appendChild(At("span","\r"==s[0]?"␍":"␤","cm-invalidchar")),r.setAttribute("cm-text",s[0]),e.col+=1):(r=e.cm.options.specialCharPlaceholder(s[0]),r.setAttribute("cm-text",s[0]),dt&&ut<9?a.appendChild(At("span",[r])):a.appendChild(r),e.col+=1);e.map.push(e.pos,e.pos+1,r),e.pos++}}else e.col+=t.length,a=document.createTextNode(l),e.map.push(e.pos,e.pos+t.length,a),dt&&ut<9&&(d=!0),e.pos+=t.length;if(e.trailingSpace=32==l.charCodeAt(t.length-1),i||r||s||d||o||n){let t=i||"";r&&(t+=r),s&&(t+=s);let l=At("span",[a],t,o);if(n)for(let e in n)n.hasOwnProperty(e)&&"style"!=e&&"class"!=e&&l.setAttribute(e,n[e]);return e.content.appendChild(l)}e.content.appendChild(a)}function ss(e,t){return(i,r,s,o,n,a,l)=>{s=s?s+" cm-force-border":"cm-force-border";let c=i.pos,d=c+r.length;for(;;){let u;for(let e=0;e<t.length&&(u=t[e],!(u.to>c&&u.from<=c));e++);if(u.to>=d)return e(i,r,s,o,n,a,l);e(i,r.slice(0,u.to-c),s,o,null,a,l),o=null,r=r.slice(u.to-c),c=u.to}}}function os(e,t,i,r){let s=!r&&i.widgetNode;s&&e.map.push(e.pos,e.pos+t,s),!r&&e.cm.display.input.needsContentAttribute&&(s||(s=e.content.appendChild(document.createElement("span"))),s.setAttribute("cm-marker",i.id)),s&&(e.cm.display.input.setUneditable(s),e.content.appendChild(s)),e.pos+=t,e.trailingSpace=!1}function ns(e,t,i){let r=e.markedSpans,s=e.text,o=0;if(!r){for(let e=1;e<i.length;e+=2)t.addToken(t,s.slice(o,o=i[e]),es(i[e+1],t.cm.options));return}let n,a,l,c,d,u,h,p=s.length,m=0,f=1,g="",v=0;for(;;){if(v==m){l=c=d=a="",h=null,u=null,v=1/0;let e,i=[];for(let t=0;t<r.length;++t){let s=r[t],o=s.marker;if("bookmark"==o.type&&s.from==m&&o.widgetNode)i.push(o);else if(s.from<=m&&(null==s.to||s.to>m||o.collapsed&&s.to==m&&s.from==m)){if(null!=s.to&&s.to!=m&&v>s.to&&(v=s.to,c=""),o.className&&(l+=" "+o.className),o.css&&(a=(a?a+";":"")+o.css),o.startStyle&&s.from==m&&(d+=" "+o.startStyle),o.endStyle&&s.to==v&&(e||(e=[])).push(o.endStyle,s.to),o.title&&((h||(h={})).title=o.title),o.attributes)for(let e in o.attributes)(h||(h={}))[e]=o.attributes[e];o.collapsed&&(!u||Dr(u.marker,o)<0)&&(u=s)}else s.from>m&&v>s.from&&(v=s.from)}if(e)for(let t=0;t<e.length;t+=2)e[t+1]==v&&(c+=" "+e[t]);if(!u||u.from==m)for(let e=0;e<i.length;++e)os(t,0,i[e]);if(u&&(u.from||0)==m){if(os(t,(null==u.to?p+1:u.to)-m,u.marker,null==u.from),null==u.to)return;u.to==m&&(u=!1)}}if(m>=p)break;let e=Math.min(p,v);for(;;){if(g){let i=m+g.length;if(!u){let r=i>e?g.slice(0,e-m):g;t.addToken(t,r,n?n+l:l,d,m+r.length==v?c:"",a,h)}if(i>=e){g=g.slice(e-m),m=e;break}m=i,d=""}g=s.slice(o,o=i[f++]),n=es(i[f++],t.cm.options)}}}function as(e,t,i){this.line=t,this.rest=function(e){let t,i;for(;t=zr(e);)e=t.find(1,!0).line,(i||(i=[])).push(e);return i}(t),this.size=this.rest?er(Qt(this.rest))-i+1:1,this.node=this.text=null,this.hidden=Gr(e,t)}function ls(e,t,i){let r,s=[];for(let o=t;o<i;o=r){let t=new as(e.doc,Xi(e.doc,o),o);r=o+t.size,s.push(t)}return s}var cs=null;var ds=null;function us(e,t){let i=vi(e,t);if(!i.length)return;let r,s=Array.prototype.slice.call(arguments,2);cs?r=cs.delayedCallbacks:ds?r=ds:(r=ds=[],setTimeout(hs,0));for(let e=0;e<i.length;++e)r.push((()=>i[e].apply(null,s)))}function hs(){let e=ds;ds=null;for(let t=0;t<e.length;++t)e[t]()}function ps(e,t,i,r){for(let s=0;s<t.changes.length;s++){let o=t.changes[s];"text"==o?gs(e,t):"gutter"==o?bs(e,t,i,r):"class"==o?vs(e,t):"widget"==o&&_s(e,t,r)}t.changes=null}function ms(e){return e.node==e.text&&(e.node=At("div",null,null,"position: relative"),e.text.parentNode&&e.text.parentNode.replaceChild(e.node,e.text),e.node.appendChild(e.text),dt&&ut<8&&(e.node.style.zIndex=2)),e.node}function fs(e,t){let i=e.display.externalMeasured;return i&&i.line==t.line?(e.display.externalMeasured=null,t.measure=i.measure,i.built):ts(e,t)}function gs(e,t){let i=t.text.className,r=fs(e,t);t.text==t.node&&(t.node=r.pre),t.text.parentNode.replaceChild(r.pre,t.text),t.text=r.pre,r.bgClass!=t.bgClass||r.textClass!=t.textClass?(t.bgClass=r.bgClass,t.textClass=r.textClass,vs(e,t)):i&&(t.text.className=i)}function vs(e,t){!function(e,t){let i=t.bgClass?t.bgClass+" "+(t.line.bgClass||""):t.line.bgClass;if(i&&(i+=" CodeMirror-linebackground"),t.background)i?t.background.className=i:(t.background.parentNode.removeChild(t.background),t.background=null);else if(i){let r=ms(t);t.background=r.insertBefore(At("div",null,i),r.firstChild),e.display.input.setUneditable(t.background)}}(e,t),t.line.wrapClass?ms(t).className=t.line.wrapClass:t.node!=t.text&&(t.node.className="");let i=t.textClass?t.textClass+" "+(t.line.textClass||""):t.line.textClass;t.text.className=i||""}function bs(e,t,i,r){if(t.gutter&&(t.node.removeChild(t.gutter),t.gutter=null),t.gutterBackground&&(t.node.removeChild(t.gutterBackground),t.gutterBackground=null),t.line.gutterClass){let i=ms(t);t.gutterBackground=At("div",null,"CodeMirror-gutter-background "+t.line.gutterClass,`left: ${e.options.fixedGutter?r.fixedPos:-r.gutterTotalWidth}px; width: ${r.gutterTotalWidth}px`),e.display.input.setUneditable(t.gutterBackground),i.insertBefore(t.gutterBackground,t.text)}let s=t.line.gutterMarkers;if(e.options.lineNumbers||s){let o=ms(t),n=t.gutter=At("div",null,"CodeMirror-gutter-wrapper",`left: ${e.options.fixedGutter?r.fixedPos:-r.gutterTotalWidth}px`);if(n.setAttribute("aria-hidden","true"),e.display.input.setUneditable(n),o.insertBefore(n,t.text),t.line.gutterClass&&(n.className+=" "+t.line.gutterClass),!e.options.lineNumbers||s&&s["CodeMirror-linenumbers"]||(t.lineNumber=n.appendChild(At("div",rr(e.options,i),"CodeMirror-linenumber CodeMirror-gutter-elt",`left: ${r.gutterLeft["CodeMirror-linenumbers"]}px; width: ${e.display.lineNumInnerWidth}px`))),s)for(let t=0;t<e.display.gutterSpecs.length;++t){let i=e.display.gutterSpecs[t].className,o=s.hasOwnProperty(i)&&s[i];o&&n.appendChild(At("div",[o],"CodeMirror-gutter-elt",`left: ${r.gutterLeft[i]}px; width: ${r.gutterWidth[i]}px`))}}}function _s(e,t,i){t.alignable&&(t.alignable=null);let r=Pt("CodeMirror-linewidget");for(let e,i=t.node.firstChild;i;i=e)e=i.nextSibling,r.test(i.className)&&t.node.removeChild(i);xs(e,t,i)}function ys(e,t,i,r){let s=fs(e,t);return t.text=t.node=s.pre,s.bgClass&&(t.bgClass=s.bgClass),s.textClass&&(t.textClass=s.textClass),vs(e,t),bs(e,t,i,r),xs(e,t,r),t.node}function xs(e,t,i){if(ws(e,t.line,t,i,!0),t.rest)for(let r=0;r<t.rest.length;r++)ws(e,t.rest[r],t,i,!1)}function ws(e,t,i,r,s){if(!t.widgets)return;let o=ms(i);for(let n=0,a=t.widgets;n<a.length;++n){let t=a[n],l=At("div",[t.node],"CodeMirror-linewidget"+(t.className?" "+t.className:""));t.handleMouseEvents||l.setAttribute("cm-ignore-events","true"),ks(t,l,i,r),e.display.input.setUneditable(l),s&&t.above?o.insertBefore(l,i.gutter||i.text):o.appendChild(l),us(t,"redraw")}}function ks(e,t,i,r){if(e.noHScroll){(i.alignable||(i.alignable=[])).push(t);let s=r.wrapperWidth;t.style.left=r.fixedPos+"px",e.coverGutter||(s-=r.gutterTotalWidth,t.style.paddingLeft=r.gutterTotalWidth+"px"),t.style.width=s+"px"}e.coverGutter&&(t.style.zIndex=5,t.style.position="relative",e.noHScroll||(t.style.marginLeft=-r.gutterTotalWidth+"px"))}function Cs(e){if(null!=e.height)return e.height;let t=e.doc.cm;if(!t)return 0;if(!Nt(document.body,e.node)){let i="position: relative;";e.coverGutter&&(i+="margin-left: -"+t.display.gutters.offsetWidth+"px;"),e.noHScroll&&(i+="width: "+t.display.wrapper.clientWidth+"px;"),Rt(t.display.measure,At("div",[e.node],null,i))}return e.height=e.node.parentNode.offsetHeight}function Ss(e,t){for(let i=Pi(t);i!=e.wrapper;i=i.parentNode)if(!i||1==i.nodeType&&"true"==i.getAttribute("cm-ignore-events")||i.parentNode==e.sizer&&i!=e.mover)return!0}function Ts(e){return e.lineSpace.offsetTop}function Ms(e){return e.mover.offsetHeight-e.lineSpace.offsetHeight}function Ps(e){if(e.cachedPaddingH)return e.cachedPaddingH;let t=Rt(e.measure,At("pre","x","CodeMirror-line-like")),i=window.getComputedStyle?window.getComputedStyle(t):t.currentStyle,r={left:parseInt(i.paddingLeft),right:parseInt(i.paddingRight)};return isNaN(r.left)||isNaN(r.right)||(e.cachedPaddingH=r),r}function $s(e){return Gt-e.display.nativeBarWidth}function Es(e){return e.display.scroller.clientWidth-$s(e)-e.display.barWidth}function Ls(e){return e.display.scroller.clientHeight-$s(e)-e.display.barHeight}function Rs(e,t,i){if(e.line==t)return{map:e.measure.map,cache:e.measure.cache};for(let i=0;i<e.rest.length;i++)if(e.rest[i]==t)return{map:e.measure.maps[i],cache:e.measure.caches[i]};for(let t=0;t<e.rest.length;t++)if(er(e.rest[t])>i)return{map:e.measure.maps[t],cache:e.measure.caches[t],before:!0}}function As(e,t,i,r){return Ds(e,Ns(e,t),i,r)}function Is(e,t){if(t>=e.display.viewFrom&&t<e.display.viewTo)return e.display.view[mo(e,t)];let i=e.display.externalMeasured;return i&&t>=i.lineN&&t<i.lineN+i.size?i:void 0}function Ns(e,t){let i=er(t),r=Is(e,i);r&&!r.text?r=null:r&&r.changes&&(ps(e,r,i,lo(e)),e.curOp.forceUpdate=!0),r||(r=function(e,t){let i=er(t=jr(t)),r=e.display.externalMeasured=new as(e.doc,t,i);r.lineN=i;let s=r.built=ts(e,r);return r.text=s.pre,Rt(e.display.lineMeasure,s.pre),r}(e,t));let s=Rs(r,t,i);return{line:t,view:r,rect:null,map:s.map,cache:s.cache,before:s.before,hasHeights:!1}}function Ds(e,t,i,r,s){t.before&&(i=-1);let o,n=i+(r||"");return t.cache.hasOwnProperty(n)?o=t.cache[n]:(t.rect||(t.rect=t.view.text.getBoundingClientRect()),t.hasHeights||(!function(e,t,i){let r=e.options.lineWrapping,s=r&&Es(e);if(!t.measure.heights||r&&t.measure.width!=s){let e=t.measure.heights=[];if(r){t.measure.width=s;let r=t.text.firstChild.getClientRects();for(let t=0;t<r.length-1;t++){let s=r[t],o=r[t+1];Math.abs(s.bottom-o.bottom)>2&&e.push((s.bottom+o.top)/2-i.top)}}e.push(i.bottom-i.top)}}(e,t.view,t.rect),t.hasHeights=!0),o=function(e,t,i,r){let s,o=zs(t.map,i,r),n=o.node,a=o.start,l=o.end,c=o.collapse;if(3==n.nodeType){for(let e=0;e<4;e++){for(;a&&li(t.line.text.charAt(o.coverStart+a));)--a;for(;o.coverStart+l<o.coverEnd&&li(t.line.text.charAt(o.coverStart+l));)++l;if(s=dt&&ut<9&&0==a&&l==o.coverEnd-o.coverStart?n.parentNode.getBoundingClientRect():Ws($t(n,a,l).getClientRects(),r),s.left||s.right||0==a)break;l=a,a-=1,c="right"}dt&&ut<11&&(s=function(e,t){if(!window.screen||null==screen.logicalXDPI||screen.logicalXDPI==screen.deviceXDPI||!function(e){if(null!=Fi)return Fi;let t=Rt(e,At("span","x")),i=t.getBoundingClientRect(),r=$t(t,0,1).getBoundingClientRect();return Fi=Math.abs(i.left-r.left)>1}(e))return t;let i=screen.logicalXDPI/screen.deviceXDPI,r=screen.logicalYDPI/screen.deviceYDPI;return{left:t.left*i,right:t.right*i,top:t.top*r,bottom:t.bottom*r}}(e.display.measure,s))}else{let t;a>0&&(c=r="right"),s=e.options.lineWrapping&&(t=n.getClientRects()).length>1?t["right"==r?t.length-1:0]:n.getBoundingClientRect()}if(dt&&ut<9&&!a&&(!s||!s.left&&!s.right)){let t=n.parentNode.getClientRects()[0];s=t?{left:t.left,right:t.left+ao(e.display),top:t.top,bottom:t.bottom}:Fs}let d=s.top-t.rect.top,u=s.bottom-t.rect.top,h=(d+u)/2,p=t.view.measure.heights,m=0;for(;m<p.length-1&&!(h<p[m]);m++);let f=m?p[m-1]:0,g=p[m],v={left:("right"==c?s.right:s.left)-t.rect.left,right:("left"==c?s.left:s.right)-t.rect.left,top:f,bottom:g};s.left||s.right||(v.bogus=!0);e.options.singleCursorHeightPerLine||(v.rtop=d,v.rbottom=u);return v}(e,t,i,r),o.bogus||(t.cache[n]=o)),{left:o.left,right:o.right,top:s?o.rtop:o.top,bottom:s?o.rbottom:o.bottom}}var Os,Fs={left:0,right:0,top:0,bottom:0};function zs(e,t,i){let r,s,o,n,a,l;for(let c=0;c<e.length;c+=3)if(a=e[c],l=e[c+1],t<a?(s=0,o=1,n="left"):t<l?(s=t-a,o=s+1):(c==e.length-3||t==l&&e[c+3]>t)&&(o=l-a,s=o-1,t>=l&&(n="right")),null!=s){if(r=e[c+2],a==l&&i==(r.insertLeft?"left":"right")&&(n=i),"left"==i&&0==s)for(;c&&e[c-2]==e[c-3]&&e[c-1].insertLeft;)r=e[2+(c-=3)],n="left";if("right"==i&&s==l-a)for(;c<e.length-3&&e[c+3]==e[c+4]&&!e[c+5].insertLeft;)r=e[(c+=3)+2],n="right";break}return{node:r,start:s,end:o,collapse:n,coverStart:a,coverEnd:l}}function Ws(e,t){let i=Fs;if("left"==t)for(let t=0;t<e.length&&(i=e[t]).left==i.right;t++);else for(let t=e.length-1;t>=0&&(i=e[t]).left==i.right;t--);return i}function Bs(e){if(e.measure&&(e.measure.cache={},e.measure.heights=null,e.rest))for(let t=0;t<e.rest.length;t++)e.measure.caches[t]={}}function js(e){e.display.externalMeasure=null,Lt(e.display.lineMeasure);for(let t=0;t<e.display.view.length;t++)Bs(e.display.view[t])}function Hs(e){js(e),e.display.cachedCharWidth=e.display.cachedTextHeight=e.display.cachedPaddingH=null,e.options.lineWrapping||(e.display.maxLineChanged=!0),e.display.lineNumChars=null}function Us(){return mt&&yt?-(document.body.getBoundingClientRect().left-parseInt(getComputedStyle(document.body).marginLeft)):window.pageXOffset||(document.documentElement||document.body).scrollLeft}function Gs(){return mt&&yt?-(document.body.getBoundingClientRect().top-parseInt(getComputedStyle(document.body).marginTop)):window.pageYOffset||(document.documentElement||document.body).scrollTop}function Vs(e){let t=0;if(e.widgets)for(let i=0;i<e.widgets.length;++i)e.widgets[i].above&&(t+=Cs(e.widgets[i]));return t}function qs(e,t,i,r,s){if(!s){let e=Vs(t);i.top+=e,i.bottom+=e}if("line"==r)return i;r||(r="local");let o=qr(t);if("local"==r?o+=Ts(e.display):o-=e.display.viewOffset,"page"==r||"window"==r){let t=e.display.lineSpace.getBoundingClientRect();o+=t.top+("window"==r?0:Gs());let s=t.left+("window"==r?0:Us());i.left+=s,i.right+=s}return i.top+=o,i.bottom+=o,i}function Zs(e,t,i){if("div"==i)return t;let r=t.left,s=t.top;if("page"==i)r-=Us(),s-=Gs();else if("local"==i||!i){let t=e.display.sizer.getBoundingClientRect();r+=t.left,s+=t.top}let o=e.display.lineSpace.getBoundingClientRect();return{left:r-o.left,top:s-o.top}}function Ks(e,t,i,r,s){return r||(r=Xi(e.doc,t.line)),qs(e,r,As(e,r,t.ch,s),i)}function Xs(e,t,i,r,s,o){function n(t,n){let a=Ds(e,s,t,n?"right":"left",o);return n?a.left=a.right:a.right=a.left,qs(e,r,a,i)}r=r||Xi(e.doc,t.line),s||(s=Ns(e,r));let a=mi(r,e.doc.direction),l=t.ch,c=t.sticky;if(l>=r.text.length?(l=r.text.length,c="before"):l<=0&&(l=0,c="after"),!a)return n("before"==c?l-1:l,"before"==c);function d(e,t,i){return n(i?e-1:e,1==a[t].level!=i)}let u=hi(a,l,c),h=ui,p=d(l,u,"before"==c);return null!=h&&(p.other=d(l,h,"before"!=c)),p}function Ys(e,t){let i=0;t=ur(e.doc,t),e.options.lineWrapping||(i=ao(e.display)*t.ch);let r=Xi(e.doc,t.line),s=qr(r)+Ts(e.display);return{left:i,right:i,top:s,bottom:s+r.height}}function Js(e,t,i,r,s){let o=sr(e,t,i);return o.xRel=s,r&&(o.outside=r),o}function Qs(e,t,i){let r=e.doc;if((i+=e.display.viewOffset)<0)return Js(r.first,0,null,-1,-1);let s=tr(r,i),o=r.first+r.size-1;if(s>o)return Js(r.first+r.size-1,Xi(r,o).text.length,null,1,1);t<0&&(t=0);let n=Xi(r,s);for(;;){let o=ro(e,n,s,t,i),a=Wr(n,o.ch+(o.xRel>0||o.outside>0?1:0));if(!a)return o;let l=a.find(1);if(l.line==s)return l;n=Xi(r,s=l.line)}}function eo(e,t,i,r){r-=Vs(t);let s=t.text.length,o=di((t=>Ds(e,i,t-1).bottom<=r),s,0);return s=di((t=>Ds(e,i,t).top>r),o,s),{begin:o,end:s}}function to(e,t,i,r){return i||(i=Ns(e,t)),eo(e,t,i,qs(e,t,Ds(e,i,r),"line").top)}function io(e,t,i,r){return!(e.bottom<=i)&&(e.top>i||(r?e.left:e.right)>t)}function ro(e,t,i,r,s){s-=qr(t);let o=Ns(e,t),n=Vs(t),a=0,l=t.text.length,c=!0,d=mi(t,e.doc.direction);if(d){let n=(e.options.lineWrapping?oo:so)(e,t,i,o,d,r,s);c=1!=n.level,a=c?n.from:n.to-1,l=c?n.to:n.from-1}let u,h,p=null,m=null,f=di((t=>{let i=Ds(e,o,t);return i.top+=n,i.bottom+=n,!!io(i,r,s,!1)&&(i.top<=s&&i.left<=r&&(p=t,m=i),!0)}),a,l),g=!1;if(m){let e=r-m.left<m.right-r,t=e==c;f=p+(t?0:1),h=t?"after":"before",u=e?m.left:m.right}else{c||f!=l&&f!=a||f++,h=0==f?"after":f==t.text.length?"before":Ds(e,o,f-(c?1:0)).bottom+n<=s==c?"after":"before";let r=Xs(e,sr(i,f,h),"line",t,o);u=r.left,g=s<r.top?-1:s>=r.bottom?1:0}return f=ci(t.text,f,1),Js(i,f,h,g,r-u)}function so(e,t,i,r,s,o,n){let a=di((a=>{let l=s[a],c=1!=l.level;return io(Xs(e,sr(i,c?l.to:l.from,c?"before":"after"),"line",t,r),o,n,!0)}),0,s.length-1),l=s[a];if(a>0){let c=1!=l.level,d=Xs(e,sr(i,c?l.from:l.to,c?"after":"before"),"line",t,r);io(d,o,n,!0)&&d.top>n&&(l=s[a-1])}return l}function oo(e,t,i,r,s,o,n){let{begin:a,end:l}=eo(e,t,r,n);/\s/.test(t.text.charAt(l-1))&&l--;let c=null,d=null;for(let t=0;t<s.length;t++){let i=s[t];if(i.from>=l||i.to<=a)continue;let n=Ds(e,r,1!=i.level?Math.min(l,i.to)-1:Math.max(a,i.from)).right,u=n<o?o-n+1e9:n-o;(!c||d>u)&&(c=i,d=u)}return c||(c=s[s.length-1]),c.from<a&&(c={from:a,to:c.to,level:c.level}),c.to>l&&(c={from:c.from,to:l,level:c.level}),c}function no(e){if(null!=e.cachedTextHeight)return e.cachedTextHeight;if(null==Os){Os=At("pre",null,"CodeMirror-line-like");for(let e=0;e<49;++e)Os.appendChild(document.createTextNode("x")),Os.appendChild(At("br"));Os.appendChild(document.createTextNode("x"))}Rt(e.measure,Os);let t=Os.offsetHeight/50;return t>3&&(e.cachedTextHeight=t),Lt(e.measure),t||1}function ao(e){if(null!=e.cachedCharWidth)return e.cachedCharWidth;let t=At("span","xxxxxxxxxx"),i=At("pre",[t],"CodeMirror-line-like");Rt(e.measure,i);let r=t.getBoundingClientRect(),s=(r.right-r.left)/10;return s>2&&(e.cachedCharWidth=s),s||10}function lo(e){let t=e.display,i={},r={},s=t.gutters.clientLeft;for(let o=t.gutters.firstChild,n=0;o;o=o.nextSibling,++n){let t=e.display.gutterSpecs[n].className;i[t]=o.offsetLeft+o.clientLeft+s,r[t]=o.clientWidth}return{fixedPos:co(t),gutterTotalWidth:t.gutters.offsetWidth,gutterLeft:i,gutterWidth:r,wrapperWidth:t.wrapper.clientWidth}}function co(e){return e.scroller.getBoundingClientRect().left-e.sizer.getBoundingClientRect().left}function uo(e){let t=no(e.display),i=e.options.lineWrapping,r=i&&Math.max(5,e.display.scroller.clientWidth/ao(e.display)-3);return s=>{if(Gr(e.doc,s))return 0;let o=0;if(s.widgets)for(let e=0;e<s.widgets.length;e++)s.widgets[e].height&&(o+=s.widgets[e].height);return i?o+(Math.ceil(s.text.length/r)||1)*t:o+t}}function ho(e){let t=e.doc,i=uo(e);t.iter((e=>{let t=i(e);t!=e.height&&Qi(e,t)}))}function po(e,t,i,r){let s=e.display;if(!i&&"true"==Pi(t).getAttribute("cm-not-content"))return null;let o,n,a=s.lineSpace.getBoundingClientRect();try{o=t.clientX-a.left,n=t.clientY-a.top}catch(e){return null}let l,c=Qs(e,o,n);if(r&&c.xRel>0&&(l=Xi(e.doc,c.line).text).length==c.ch){let t=jt(l,l.length,e.options.tabSize)-l.length;c=sr(c.line,Math.max(0,Math.round((o-Ps(e.display).left)/ao(e.display))-t))}return c}function mo(e,t){if(t>=e.display.viewTo)return null;if((t-=e.display.viewFrom)<0)return null;let i=e.display.view;for(let e=0;e<i.length;e++)if((t-=i[e].size)<0)return e}function fo(e,t,i,r){null==t&&(t=e.doc.first),null==i&&(i=e.doc.first+e.doc.size),r||(r=0);let s=e.display;if(r&&i<s.viewTo&&(null==s.updateLineNumbers||s.updateLineNumbers>t)&&(s.updateLineNumbers=t),e.curOp.viewChanged=!0,t>=s.viewTo)Tr&&Hr(e.doc,t)<s.viewTo&&vo(e);else if(i<=s.viewFrom)Tr&&Ur(e.doc,i+r)>s.viewFrom?vo(e):(s.viewFrom+=r,s.viewTo+=r);else if(t<=s.viewFrom&&i>=s.viewTo)vo(e);else if(t<=s.viewFrom){let t=bo(e,i,i+r,1);t?(s.view=s.view.slice(t.index),s.viewFrom=t.lineN,s.viewTo+=r):vo(e)}else if(i>=s.viewTo){let i=bo(e,t,t,-1);i?(s.view=s.view.slice(0,i.index),s.viewTo=i.lineN):vo(e)}else{let o=bo(e,t,t,-1),n=bo(e,i,i+r,1);o&&n?(s.view=s.view.slice(0,o.index).concat(ls(e,o.lineN,n.lineN)).concat(s.view.slice(n.index)),s.viewTo+=r):vo(e)}let o=s.externalMeasured;o&&(i<o.lineN?o.lineN+=r:t<o.lineN+o.size&&(s.externalMeasured=null))}function go(e,t,i){e.curOp.viewChanged=!0;let r=e.display,s=e.display.externalMeasured;if(s&&t>=s.lineN&&t<s.lineN+s.size&&(r.externalMeasured=null),t<r.viewFrom||t>=r.viewTo)return;let o=r.view[mo(e,t)];if(null==o.node)return;let n=o.changes||(o.changes=[]);-1==Ut(n,i)&&n.push(i)}function vo(e){e.display.viewFrom=e.display.viewTo=e.doc.first,e.display.view=[],e.display.viewOffset=0}function bo(e,t,i,r){let s,o=mo(e,t),n=e.display.view;if(!Tr||i==e.doc.first+e.doc.size)return{index:o,lineN:i};let a=e.display.viewFrom;for(let e=0;e<o;e++)a+=n[e].size;if(a!=t){if(r>0){if(o==n.length-1)return null;s=a+n[o].size-t,o++}else s=a-t;t+=s,i+=s}for(;Hr(e.doc,i)!=i;){if(o==(r<0?0:n.length-1))return null;i+=r*n[o-(r<0?1:0)].size,o+=r}return{index:o,lineN:i}}function _o(e){let t=e.display.view,i=0;for(let e=0;e<t.length;e++){let r=t[e];r.hidden||r.node&&!r.changes||++i}return i}function yo(e){e.display.input.showSelection(e.display.input.prepareSelection())}function xo(e,t=!0){let i=e.doc,r={},s=r.cursors=document.createDocumentFragment(),o=r.selection=document.createDocumentFragment();for(let r=0;r<i.sel.ranges.length;r++){if(!t&&r==i.sel.primIndex)continue;let n=i.sel.ranges[r];if(n.from().line>=e.display.viewTo||n.to().line<e.display.viewFrom)continue;let a=n.empty();(a||e.options.showCursorWhenSelecting)&&wo(e,n.head,s),a||Co(e,n,o)}return r}function wo(e,t,i){let r=Xs(e,t,"div",null,null,!e.options.singleCursorHeightPerLine),s=i.appendChild(At("div"," ","CodeMirror-cursor"));if(s.style.left=r.left+"px",s.style.top=r.top+"px",s.style.height=Math.max(0,r.bottom-r.top)*e.options.cursorHeight+"px",r.other){let e=i.appendChild(At("div"," ","CodeMirror-cursor CodeMirror-secondarycursor"));e.style.display="",e.style.left=r.other.left+"px",e.style.top=r.other.top+"px",e.style.height=.85*(r.other.bottom-r.other.top)+"px"}}function ko(e,t){return e.top-t.top||e.left-t.left}function Co(e,t,i){let r=e.display,s=e.doc,o=document.createDocumentFragment(),n=Ps(e.display),a=n.left,l=Math.max(r.sizerWidth,Es(e)-r.sizer.offsetLeft)-n.right,c="ltr"==s.direction;function d(e,t,i,r){t<0&&(t=0),t=Math.round(t),r=Math.round(r),o.appendChild(At("div",null,"CodeMirror-selected",`position: absolute; left: ${e}px;\n                             top: ${t}px; width: ${null==i?l-e:i}px;\n                             height: ${r-t}px`))}function u(t,i,r){let o,n,u=Xi(s,t),h=u.text.length;function p(i,r){return Ks(e,sr(t,i),"div",u,r)}function m(t,i,r){let s=to(e,u,null,t),o="ltr"==i==("after"==r)?"left":"right";return p("after"==r?s.begin:s.end-(/\s/.test(u.text.charAt(s.end-1))?2:1),o)[o]}let f=mi(u,s.direction);return function(e,t,i,r){if(!e)return r(t,i,"ltr",0);let s=!1;for(let o=0;o<e.length;++o){let n=e[o];(n.from<i&&n.to>t||t==i&&n.to==t)&&(r(Math.max(n.from,t),Math.min(n.to,i),1==n.level?"rtl":"ltr",o),s=!0)}s||r(t,i,"ltr")}(f,i||0,null==r?h:r,((e,t,s,u)=>{let g="ltr"==s,v=p(e,g?"left":"right"),b=p(t-1,g?"right":"left"),_=null==i&&0==e,y=null==r&&t==h,x=0==u,w=!f||u==f.length-1;if(b.top-v.top<=3){let e=(c?y:_)&&w,t=(c?_:y)&&x?a:(g?v:b).left,i=e?l:(g?b:v).right;d(t,v.top,i-t,v.bottom)}else{let i,r,o,n;g?(i=c&&_&&x?a:v.left,r=c?l:m(e,s,"before"),o=c?a:m(t,s,"after"),n=c&&y&&w?l:b.right):(i=c?m(e,s,"before"):a,r=!c&&_&&x?l:v.right,o=!c&&y&&w?a:b.left,n=c?m(t,s,"after"):l),d(i,v.top,r-i,v.bottom),v.bottom<b.top&&d(a,v.bottom,null,b.top),d(o,b.top,n-o,b.bottom)}(!o||ko(v,o)<0)&&(o=v),ko(b,o)<0&&(o=b),(!n||ko(v,n)<0)&&(n=v),ko(b,n)<0&&(n=b)})),{start:o,end:n}}let h=t.from(),p=t.to();if(h.line==p.line)u(h.line,h.ch,p.ch);else{let e=Xi(s,h.line),t=Xi(s,p.line),i=jr(e)==jr(t),r=u(h.line,h.ch,i?e.text.length+1:null).end,o=u(p.line,i?0:null,p.ch).start;i&&(r.top<o.top-2?(d(r.right,r.top,null,r.bottom),d(a,o.top,o.left,o.bottom)):d(r.right,r.top,o.left-r.right,r.bottom)),r.bottom<o.top&&d(a,r.bottom,null,o.top)}i.appendChild(o)}function So(e){if(!e.state.focused)return;let t=e.display;clearInterval(t.blinker);let i=!0;t.cursorDiv.style.visibility="",e.options.cursorBlinkRate>0?t.blinker=setInterval((()=>{e.hasFocus()||$o(e),t.cursorDiv.style.visibility=(i=!i)?"":"hidden"}),e.options.cursorBlinkRate):e.options.cursorBlinkRate<0&&(t.cursorDiv.style.visibility="hidden")}function To(e){e.hasFocus()||(e.display.input.focus(),e.state.focused||Po(e))}function Mo(e){e.state.delayingBlurEvent=!0,setTimeout((()=>{e.state.delayingBlurEvent&&(e.state.delayingBlurEvent=!1,e.state.focused&&$o(e))}),100)}function Po(e,t){e.state.delayingBlurEvent&&!e.state.draggingText&&(e.state.delayingBlurEvent=!1),"nocursor"!=e.options.readOnly&&(e.state.focused||(_i(e,"focus",e,t),e.state.focused=!0,Ot(e.display.wrapper,"CodeMirror-focused"),e.curOp||e.display.selForContextMenu==e.doc.sel||(e.display.input.reset(),ht&&setTimeout((()=>e.display.input.reset(!0)),20)),e.display.input.receivedFocus()),So(e))}function $o(e,t){e.state.delayingBlurEvent||(e.state.focused&&(_i(e,"blur",e,t),e.state.focused=!1,Et(e.display.wrapper,"CodeMirror-focused")),clearInterval(e.display.blinker),setTimeout((()=>{e.state.focused||(e.display.shift=!1)}),150))}function Eo(e){let t=e.display,i=t.lineDiv.offsetTop;for(let r=0;r<t.view.length;r++){let s,o=t.view[r],n=e.options.lineWrapping,a=0;if(o.hidden)continue;if(dt&&ut<8){let e=o.node.offsetTop+o.node.offsetHeight;s=e-i,i=e}else{let e=o.node.getBoundingClientRect();s=e.bottom-e.top,!n&&o.text.firstChild&&(a=o.text.firstChild.getBoundingClientRect().right-e.left-1)}let l=o.line.height-s;if((l>.005||l<-.005)&&(Qi(o.line,s),Lo(o.line),o.rest))for(let e=0;e<o.rest.length;e++)Lo(o.rest[e]);if(a>e.display.sizerWidth){let t=Math.ceil(a/ao(e.display));t>e.display.maxLineLength&&(e.display.maxLineLength=t,e.display.maxLine=o.line,e.display.maxLineChanged=!0)}}}function Lo(e){if(e.widgets)for(let t=0;t<e.widgets.length;++t){let i=e.widgets[t],r=i.node.parentNode;r&&(i.height=r.offsetHeight)}}function Ro(e,t,i){let r=i&&null!=i.top?Math.max(0,i.top):e.scroller.scrollTop;r=Math.floor(r-Ts(e));let s=i&&null!=i.bottom?i.bottom:r+e.wrapper.clientHeight,o=tr(t,r),n=tr(t,s);if(i&&i.ensure){let r=i.ensure.from.line,s=i.ensure.to.line;r<o?(o=r,n=tr(t,qr(Xi(t,r))+e.wrapper.clientHeight)):Math.min(s,t.lastLine())>=n&&(o=tr(t,qr(Xi(t,s))-e.wrapper.clientHeight),n=s)}return{from:o,to:Math.max(n,o+1)}}function Ao(e,t){let i=e.display,r=no(e.display);t.top<0&&(t.top=0);let s=e.curOp&&null!=e.curOp.scrollTop?e.curOp.scrollTop:i.scroller.scrollTop,o=Ls(e),n={};t.bottom-t.top>o&&(t.bottom=t.top+o);let a=e.doc.height+Ms(i),l=t.top<r,c=t.bottom>a-r;if(t.top<s)n.scrollTop=l?0:t.top;else if(t.bottom>s+o){let e=Math.min(t.top,(c?a:t.bottom)-o);e!=s&&(n.scrollTop=e)}let d=e.options.fixedGutter?0:i.gutters.offsetWidth,u=e.curOp&&null!=e.curOp.scrollLeft?e.curOp.scrollLeft:i.scroller.scrollLeft-d,h=Es(e)-i.gutters.offsetWidth,p=t.right-t.left>h;return p&&(t.right=t.left+h),t.left<10?n.scrollLeft=0:t.left<u?n.scrollLeft=Math.max(0,t.left+d-(p?0:10)):t.right>h+u-3&&(n.scrollLeft=t.right+(p?0:10)-h),n}function Io(e,t){null!=t&&(Oo(e),e.curOp.scrollTop=(null==e.curOp.scrollTop?e.doc.scrollTop:e.curOp.scrollTop)+t)}function No(e){Oo(e);let t=e.getCursor();e.curOp.scrollToPos={from:t,to:t,margin:e.options.cursorScrollMargin}}function Do(e,t,i){null==t&&null==i||Oo(e),null!=t&&(e.curOp.scrollLeft=t),null!=i&&(e.curOp.scrollTop=i)}function Oo(e){let t=e.curOp.scrollToPos;if(t){e.curOp.scrollToPos=null,Fo(e,Ys(e,t.from),Ys(e,t.to),t.margin)}}function Fo(e,t,i,r){let s=Ao(e,{left:Math.min(t.left,i.left),top:Math.min(t.top,i.top)-r,right:Math.max(t.right,i.right),bottom:Math.max(t.bottom,i.bottom)+r});Do(e,s.scrollLeft,s.scrollTop)}function zo(e,t){Math.abs(e.doc.scrollTop-t)<2||(nt||un(e,{top:t}),Wo(e,t,!0),nt&&un(e),nn(e,100))}function Wo(e,t,i){t=Math.max(0,Math.min(e.display.scroller.scrollHeight-e.display.scroller.clientHeight,t)),(e.display.scroller.scrollTop!=t||i)&&(e.doc.scrollTop=t,e.display.scrollbars.setScrollTop(t),e.display.scroller.scrollTop!=t&&(e.display.scroller.scrollTop=t))}function Bo(e,t,i,r){t=Math.max(0,Math.min(t,e.display.scroller.scrollWidth-e.display.scroller.clientWidth)),(i?t==e.doc.scrollLeft:Math.abs(e.doc.scrollLeft-t)<2)&&!r||(e.doc.scrollLeft=t,mn(e),e.display.scroller.scrollLeft!=t&&(e.display.scroller.scrollLeft=t),e.display.scrollbars.setScrollLeft(t))}function jo(e){let t=e.display,i=t.gutters.offsetWidth,r=Math.round(e.doc.height+Ms(e.display));return{clientHeight:t.scroller.clientHeight,viewHeight:t.wrapper.clientHeight,scrollWidth:t.scroller.scrollWidth,clientWidth:t.scroller.clientWidth,viewWidth:t.wrapper.clientWidth,barLeft:e.options.fixedGutter?i:0,docHeight:r,scrollHeight:r+$s(e)+t.barHeight,nativeBarWidth:t.nativeBarWidth,gutterWidth:i}}function Ho(e,t){t||(t=jo(e));let i=e.display.barWidth,r=e.display.barHeight;Uo(e,t);for(let t=0;t<4&&i!=e.display.barWidth||r!=e.display.barHeight;t++)i!=e.display.barWidth&&e.options.lineWrapping&&Eo(e),Uo(e,jo(e)),i=e.display.barWidth,r=e.display.barHeight}function Uo(e,t){let i=e.display,r=i.scrollbars.update(t);i.sizer.style.paddingRight=(i.barWidth=r.right)+"px",i.sizer.style.paddingBottom=(i.barHeight=r.bottom)+"px",i.heightForcer.style.borderBottom=r.bottom+"px solid transparent",r.right&&r.bottom?(i.scrollbarFiller.style.display="block",i.scrollbarFiller.style.height=r.bottom+"px",i.scrollbarFiller.style.width=r.right+"px"):i.scrollbarFiller.style.display="",r.bottom&&e.options.coverGutterNextToScrollbar&&e.options.fixedGutter?(i.gutterFiller.style.display="block",i.gutterFiller.style.height=r.bottom+"px",i.gutterFiller.style.width=t.gutterWidth+"px"):i.gutterFiller.style.display=""}var Go={native:class{constructor(e,t,i){this.cm=i;let r=this.vert=At("div",[At("div",null,null,"min-width: 1px")],"CodeMirror-vscrollbar"),s=this.horiz=At("div",[At("div",null,null,"height: 100%; min-height: 1px")],"CodeMirror-hscrollbar");r.tabIndex=s.tabIndex=-1,e(r),e(s),gi(r,"scroll",(()=>{r.clientHeight&&t(r.scrollTop,"vertical")})),gi(s,"scroll",(()=>{s.clientWidth&&t(s.scrollLeft,"horizontal")})),this.checkedZeroWidth=!1,dt&&ut<8&&(this.horiz.style.minHeight=this.vert.style.minWidth="18px")}update(e){let t=e.scrollWidth>e.clientWidth+1,i=e.scrollHeight>e.clientHeight+1,r=e.nativeBarWidth;if(i){this.vert.style.display="block",this.vert.style.bottom=t?r+"px":"0";let i=e.viewHeight-(t?r:0);this.vert.firstChild.style.height=Math.max(0,e.scrollHeight-e.clientHeight+i)+"px"}else this.vert.style.display="",this.vert.firstChild.style.height="0";if(t){this.horiz.style.display="block",this.horiz.style.right=i?r+"px":"0",this.horiz.style.left=e.barLeft+"px";let t=e.viewWidth-e.barLeft-(i?r:0);this.horiz.firstChild.style.width=Math.max(0,e.scrollWidth-e.clientWidth+t)+"px"}else this.horiz.style.display="",this.horiz.firstChild.style.width="0";return!this.checkedZeroWidth&&e.clientHeight>0&&(0==r&&this.zeroWidthHack(),this.checkedZeroWidth=!0),{right:i?r:0,bottom:t?r:0}}setScrollLeft(e){this.horiz.scrollLeft!=e&&(this.horiz.scrollLeft=e),this.disableHoriz&&this.enableZeroWidthBar(this.horiz,this.disableHoriz,"horiz")}setScrollTop(e){this.vert.scrollTop!=e&&(this.vert.scrollTop=e),this.disableVert&&this.enableZeroWidthBar(this.vert,this.disableVert,"vert")}zeroWidthHack(){let e=wt&&!vt?"12px":"18px";this.horiz.style.height=this.vert.style.width=e,this.horiz.style.pointerEvents=this.vert.style.pointerEvents="none",this.disableHoriz=new Ht,this.disableVert=new Ht}enableZeroWidthBar(e,t,i){e.style.pointerEvents="auto",t.set(1e3,(function r(){let s=e.getBoundingClientRect();("vert"==i?document.elementFromPoint(s.right-1,(s.top+s.bottom)/2):document.elementFromPoint((s.right+s.left)/2,s.bottom-1))!=e?e.style.pointerEvents="none":t.set(1e3,r)}))}clear(){let e=this.horiz.parentNode;e.removeChild(this.horiz),e.removeChild(this.vert)}},null:class{update(){return{bottom:0,right:0}}setScrollLeft(){}setScrollTop(){}clear(){}}};function Vo(e){e.display.scrollbars&&(e.display.scrollbars.clear(),e.display.scrollbars.addClass&&Et(e.display.wrapper,e.display.scrollbars.addClass)),e.display.scrollbars=new Go[e.options.scrollbarStyle]((t=>{e.display.wrapper.insertBefore(t,e.display.scrollbarFiller),gi(t,"mousedown",(()=>{e.state.focused&&setTimeout((()=>e.display.input.focus()),0)})),t.setAttribute("cm-not-content","true")}),((t,i)=>{"horizontal"==i?Bo(e,t):zo(e,t)}),e),e.display.scrollbars.addClass&&Ot(e.display.wrapper,e.display.scrollbars.addClass)}var qo=0;function Zo(e){var t;e.curOp={cm:e,viewChanged:!1,startHeight:e.doc.height,forceUpdate:!1,updateInput:0,typing:!1,changeObjs:null,cursorActivityHandlers:null,cursorActivityCalled:0,selectionChanged:!1,updateMaxLine:!1,scrollLeft:null,scrollTop:null,scrollToPos:null,focus:!1,id:++qo},t=e.curOp,cs?cs.ops.push(t):t.ownsGroup=cs={ops:[t],delayedCallbacks:[]}}function Ko(e){let t=e.curOp;t&&function(e,t){let i=e.ownsGroup;if(i)try{!function(e){let t=e.delayedCallbacks,i=0;do{for(;i<t.length;i++)t[i].call(null);for(let t=0;t<e.ops.length;t++){let i=e.ops[t];if(i.cursorActivityHandlers)for(;i.cursorActivityCalled<i.cursorActivityHandlers.length;)i.cursorActivityHandlers[i.cursorActivityCalled++].call(null,i.cm)}}while(i<t.length)}(i)}finally{cs=null,t(i)}}(t,(e=>{for(let t=0;t<e.ops.length;t++)e.ops[t].cm.curOp=null;!function(e){let t=e.ops;for(let e=0;e<t.length;e++)Xo(t[e]);for(let e=0;e<t.length;e++)Yo(t[e]);for(let e=0;e<t.length;e++)Jo(t[e]);for(let e=0;e<t.length;e++)Qo(t[e]);for(let e=0;e<t.length;e++)en(t[e])}(e)}))}function Xo(e){let t=e.cm,i=t.display;!function(e){let t=e.display;!t.scrollbarsClipped&&t.scroller.offsetWidth&&(t.nativeBarWidth=t.scroller.offsetWidth-t.scroller.clientWidth,t.heightForcer.style.height=$s(e)+"px",t.sizer.style.marginBottom=-t.nativeBarWidth+"px",t.sizer.style.borderRightWidth=$s(e)+"px",t.scrollbarsClipped=!0)}(t),e.updateMaxLine&&Kr(t),e.mustUpdate=e.viewChanged||e.forceUpdate||null!=e.scrollTop||e.scrollToPos&&(e.scrollToPos.from.line<i.viewFrom||e.scrollToPos.to.line>=i.viewTo)||i.maxLineChanged&&t.options.lineWrapping,e.update=e.mustUpdate&&new ln(t,e.mustUpdate&&{top:e.scrollTop,ensure:e.scrollToPos},e.forceUpdate)}function Yo(e){e.updatedDisplay=e.mustUpdate&&cn(e.cm,e.update)}function Jo(e){let t=e.cm,i=t.display;e.updatedDisplay&&Eo(t),e.barMeasure=jo(t),i.maxLineChanged&&!t.options.lineWrapping&&(e.adjustWidthTo=As(t,i.maxLine,i.maxLine.text.length).left+3,t.display.sizerWidth=e.adjustWidthTo,e.barMeasure.scrollWidth=Math.max(i.scroller.clientWidth,i.sizer.offsetLeft+e.adjustWidthTo+$s(t)+t.display.barWidth),e.maxScrollLeft=Math.max(0,i.sizer.offsetLeft+e.adjustWidthTo-Es(t))),(e.updatedDisplay||e.selectionChanged)&&(e.preparedSelection=i.input.prepareSelection())}function Qo(e){let t=e.cm;null!=e.adjustWidthTo&&(t.display.sizer.style.minWidth=e.adjustWidthTo+"px",e.maxScrollLeft<t.doc.scrollLeft&&Bo(t,Math.min(t.display.scroller.scrollLeft,e.maxScrollLeft),!0),t.display.maxLineChanged=!1);let i=e.focus&&e.focus==Dt();e.preparedSelection&&t.display.input.showSelection(e.preparedSelection,i),(e.updatedDisplay||e.startHeight!=t.doc.height)&&Ho(t,e.barMeasure),e.updatedDisplay&&pn(t,e.barMeasure),e.selectionChanged&&So(t),t.state.focused&&e.updateInput&&t.display.input.reset(e.typing),i&&To(e.cm)}function en(e){let t=e.cm,i=t.display,r=t.doc;if(e.updatedDisplay&&dn(t,e.update),null==i.wheelStartX||null==e.scrollTop&&null==e.scrollLeft&&!e.scrollToPos||(i.wheelStartX=i.wheelStartY=null),null!=e.scrollTop&&Wo(t,e.scrollTop,e.forceScroll),null!=e.scrollLeft&&Bo(t,e.scrollLeft,!0,!0),e.scrollToPos){let i=function(e,t,i,r){let s;null==r&&(r=0),e.options.lineWrapping||t!=i||(i="before"==(t=t.ch?sr(t.line,"before"==t.sticky?t.ch-1:t.ch,"after"):t).sticky?sr(t.line,t.ch+1,"before"):t);for(let o=0;o<5;o++){let o=!1,n=Xs(e,t),a=i&&i!=t?Xs(e,i):n;s={left:Math.min(n.left,a.left),top:Math.min(n.top,a.top)-r,right:Math.max(n.left,a.left),bottom:Math.max(n.bottom,a.bottom)+r};let l=Ao(e,s),c=e.doc.scrollTop,d=e.doc.scrollLeft;if(null!=l.scrollTop&&(zo(e,l.scrollTop),Math.abs(e.doc.scrollTop-c)>1&&(o=!0)),null!=l.scrollLeft&&(Bo(e,l.scrollLeft),Math.abs(e.doc.scrollLeft-d)>1&&(o=!0)),!o)break}return s}(t,ur(r,e.scrollToPos.from),ur(r,e.scrollToPos.to),e.scrollToPos.margin);!function(e,t){if(yi(e,"scrollCursorIntoView"))return;let i=e.display,r=i.sizer.getBoundingClientRect(),s=null;if(t.top+r.top<0?s=!0:t.bottom+r.top>(window.innerHeight||document.documentElement.clientHeight)&&(s=!1),null!=s&&!bt){let r=At("div","​",null,`position: absolute;\n                         top: ${t.top-i.viewOffset-Ts(e.display)}px;\n                         height: ${t.bottom-t.top+$s(e)+i.barHeight}px;\n                         left: ${t.left}px; width: ${Math.max(2,t.right-t.left)}px;`);e.display.lineSpace.appendChild(r),r.scrollIntoView(s),e.display.lineSpace.removeChild(r)}}(t,i)}let s=e.maybeHiddenMarkers,o=e.maybeUnhiddenMarkers;if(s)for(let e=0;e<s.length;++e)s[e].lines.length||_i(s[e],"hide");if(o)for(let e=0;e<o.length;++e)o[e].lines.length&&_i(o[e],"unhide");i.wrapper.offsetHeight&&(r.scrollTop=t.display.scroller.scrollTop),e.changeObjs&&_i(t,"changes",t,e.changeObjs),e.update&&e.update.finish()}function tn(e,t){if(e.curOp)return t();Zo(e);try{return t()}finally{Ko(e)}}function rn(e,t){return function(){if(e.curOp)return t.apply(e,arguments);Zo(e);try{return t.apply(e,arguments)}finally{Ko(e)}}}function sn(e){return function(){if(this.curOp)return e.apply(this,arguments);Zo(this);try{return e.apply(this,arguments)}finally{Ko(this)}}}function on(e){return function(){let t=this.cm;if(!t||t.curOp)return e.apply(this,arguments);Zo(t);try{return e.apply(this,arguments)}finally{Ko(t)}}}function nn(e,t){e.doc.highlightFrontier<e.display.viewTo&&e.state.highlight.set(t,Wt(an,e))}function an(e){let t=e.doc;if(t.highlightFrontier>=e.display.viewTo)return;let i=+new Date+e.options.workTime,r=vr(e,t.highlightFrontier),s=[];t.iter(r.line,Math.min(t.first+t.size,e.display.viewTo+500),(o=>{if(r.line>=e.display.viewFrom){let i=o.styles,n=o.text.length>e.options.maxHighlightLength?Vi(t.mode,r.state):null,a=fr(e,o,r,!0);n&&(r.state=n),o.styles=a.styles;let l=o.styleClasses,c=a.classes;c?o.styleClasses=c:l&&(o.styleClasses=null);let d=!i||i.length!=o.styles.length||l!=c&&(!l||!c||l.bgClass!=c.bgClass||l.textClass!=c.textClass);for(let e=0;!d&&e<i.length;++e)d=i[e]!=o.styles[e];d&&s.push(r.line),o.stateAfter=r.save(),r.nextLine()}else o.text.length<=e.options.maxHighlightLength&&br(e,o.text,r),o.stateAfter=r.line%5==0?r.save():null,r.nextLine();if(+new Date>i)return nn(e,e.options.workDelay),!0})),t.highlightFrontier=r.line,t.modeFrontier=Math.max(t.modeFrontier,r.line),s.length&&tn(e,(()=>{for(let t=0;t<s.length;t++)go(e,s[t],"text")}))}var ln=class{constructor(e,t,i){let r=e.display;this.viewport=t,this.visible=Ro(r,e.doc,t),this.editorIsHidden=!r.wrapper.offsetWidth,this.wrapperHeight=r.wrapper.clientHeight,this.wrapperWidth=r.wrapper.clientWidth,this.oldDisplayWidth=Es(e),this.force=i,this.dims=lo(e),this.events=[]}signal(e,t){wi(e,t)&&this.events.push(arguments)}finish(){for(let e=0;e<this.events.length;e++)_i.apply(null,this.events[e])}};function cn(e,t){let i=e.display,r=e.doc;if(t.editorIsHidden)return vo(e),!1;if(!t.force&&t.visible.from>=i.viewFrom&&t.visible.to<=i.viewTo&&(null==i.updateLineNumbers||i.updateLineNumbers>=i.viewTo)&&i.renderedView==i.view&&0==_o(e))return!1;fn(e)&&(vo(e),t.dims=lo(e));let s=r.first+r.size,o=Math.max(t.visible.from-e.options.viewportMargin,r.first),n=Math.min(s,t.visible.to+e.options.viewportMargin);i.viewFrom<o&&o-i.viewFrom<20&&(o=Math.max(r.first,i.viewFrom)),i.viewTo>n&&i.viewTo-n<20&&(n=Math.min(s,i.viewTo)),Tr&&(o=Hr(e.doc,o),n=Ur(e.doc,n));let a=o!=i.viewFrom||n!=i.viewTo||i.lastWrapHeight!=t.wrapperHeight||i.lastWrapWidth!=t.wrapperWidth;!function(e,t,i){let r=e.display;0==r.view.length||t>=r.viewTo||i<=r.viewFrom?(r.view=ls(e,t,i),r.viewFrom=t):(r.viewFrom>t?r.view=ls(e,t,r.viewFrom).concat(r.view):r.viewFrom<t&&(r.view=r.view.slice(mo(e,t))),r.viewFrom=t,r.viewTo<i?r.view=r.view.concat(ls(e,r.viewTo,i)):r.viewTo>i&&(r.view=r.view.slice(0,mo(e,i)))),r.viewTo=i}(e,o,n),i.viewOffset=qr(Xi(e.doc,i.viewFrom)),e.display.mover.style.top=i.viewOffset+"px";let l=_o(e);if(!a&&0==l&&!t.force&&i.renderedView==i.view&&(null==i.updateLineNumbers||i.updateLineNumbers>=i.viewTo))return!1;let c=function(e){if(e.hasFocus())return null;let t=Dt();if(!t||!Nt(e.display.lineDiv,t))return null;let i={activeElt:t};if(window.getSelection){let t=window.getSelection();t.anchorNode&&t.extend&&Nt(e.display.lineDiv,t.anchorNode)&&(i.anchorNode=t.anchorNode,i.anchorOffset=t.anchorOffset,i.focusNode=t.focusNode,i.focusOffset=t.focusOffset)}return i}(e);return l>4&&(i.lineDiv.style.display="none"),function(e,t,i){let r=e.display,s=e.options.lineNumbers,o=r.lineDiv,n=o.firstChild;function a(t){let i=t.nextSibling;return ht&&wt&&e.display.currentWheelTarget==t?t.style.display="none":t.parentNode.removeChild(t),i}let l=r.view,c=r.viewFrom;for(let r=0;r<l.length;r++){let d=l[r];if(d.hidden);else if(d.node&&d.node.parentNode==o){for(;n!=d.node;)n=a(n);let r=s&&null!=t&&t<=c&&d.lineNumber;d.changes&&(Ut(d.changes,"gutter")>-1&&(r=!1),ps(e,d,c,i)),r&&(Lt(d.lineNumber),d.lineNumber.appendChild(document.createTextNode(rr(e.options,c)))),n=d.node.nextSibling}else{let t=ys(e,d,c,i);o.insertBefore(t,n)}c+=d.size}for(;n;)n=a(n)}(e,i.updateLineNumbers,t.dims),l>4&&(i.lineDiv.style.display=""),i.renderedView=i.view,function(e){if(e&&e.activeElt&&e.activeElt!=Dt()&&(e.activeElt.focus(),!/^(INPUT|TEXTAREA)$/.test(e.activeElt.nodeName)&&e.anchorNode&&Nt(document.body,e.anchorNode)&&Nt(document.body,e.focusNode))){let t=window.getSelection(),i=document.createRange();i.setEnd(e.anchorNode,e.anchorOffset),i.collapse(!1),t.removeAllRanges(),t.addRange(i),t.extend(e.focusNode,e.focusOffset)}}(c),Lt(i.cursorDiv),Lt(i.selectionDiv),i.gutters.style.height=i.sizer.style.minHeight=0,a&&(i.lastWrapHeight=t.wrapperHeight,i.lastWrapWidth=t.wrapperWidth,nn(e,400)),i.updateLineNumbers=null,!0}function dn(e,t){let i=t.viewport;for(let r=!0;;r=!1){if(r&&e.options.lineWrapping&&t.oldDisplayWidth!=Es(e))r&&(t.visible=Ro(e.display,e.doc,i));else if(i&&null!=i.top&&(i={top:Math.min(e.doc.height+Ms(e.display)-Ls(e),i.top)}),t.visible=Ro(e.display,e.doc,i),t.visible.from>=e.display.viewFrom&&t.visible.to<=e.display.viewTo)break;if(!cn(e,t))break;Eo(e);let s=jo(e);yo(e),Ho(e,s),pn(e,s),t.force=!1}t.signal(e,"update",e),e.display.viewFrom==e.display.reportedViewFrom&&e.display.viewTo==e.display.reportedViewTo||(t.signal(e,"viewportChange",e,e.display.viewFrom,e.display.viewTo),e.display.reportedViewFrom=e.display.viewFrom,e.display.reportedViewTo=e.display.viewTo)}function un(e,t){let i=new ln(e,t);if(cn(e,i)){Eo(e),dn(e,i);let t=jo(e);yo(e),Ho(e,t),pn(e,t),i.finish()}}function hn(e){let t=e.gutters.offsetWidth;e.sizer.style.marginLeft=t+"px",us(e,"gutterChanged",e)}function pn(e,t){e.display.sizer.style.minHeight=t.docHeight+"px",e.display.heightForcer.style.top=t.docHeight+"px",e.display.gutters.style.height=t.docHeight+e.display.barHeight+$s(e)+"px"}function mn(e){let t=e.display,i=t.view;if(!(t.alignWidgets||t.gutters.firstChild&&e.options.fixedGutter))return;let r=co(t)-t.scroller.scrollLeft+e.doc.scrollLeft,s=t.gutters.offsetWidth,o=r+"px";for(let t=0;t<i.length;t++)if(!i[t].hidden){e.options.fixedGutter&&(i[t].gutter&&(i[t].gutter.style.left=o),i[t].gutterBackground&&(i[t].gutterBackground.style.left=o));let r=i[t].alignable;if(r)for(let e=0;e<r.length;e++)r[e].style.left=o}e.options.fixedGutter&&(t.gutters.style.left=r+s+"px")}function fn(e){if(!e.options.lineNumbers)return!1;let t=e.doc,i=rr(e.options,t.first+t.size-1),r=e.display;if(i.length!=r.lineNumChars){let t=r.measure.appendChild(At("div",[At("div",i)],"CodeMirror-linenumber CodeMirror-gutter-elt")),s=t.firstChild.offsetWidth,o=t.offsetWidth-s;return r.lineGutter.style.width="",r.lineNumInnerWidth=Math.max(s,r.lineGutter.offsetWidth-o)+1,r.lineNumWidth=r.lineNumInnerWidth+o,r.lineNumChars=r.lineNumInnerWidth?i.length:-1,r.lineGutter.style.width=r.lineNumWidth+"px",hn(e.display),!0}return!1}function gn(e,t){let i=[],r=!1;for(let s=0;s<e.length;s++){let o=e[s],n=null;if("string"!=typeof o&&(n=o.style,o=o.className),"CodeMirror-linenumbers"==o){if(!t)continue;r=!0}i.push({className:o,style:n})}return t&&!r&&i.push({className:"CodeMirror-linenumbers",style:null}),i}function vn(e){let t=e.gutters,i=e.gutterSpecs;Lt(t),e.lineGutter=null;for(let r=0;r<i.length;++r){let{className:s,style:o}=i[r],n=t.appendChild(At("div",null,"CodeMirror-gutter "+s));o&&(n.style.cssText=o),"CodeMirror-linenumbers"==s&&(e.lineGutter=n,n.style.width=(e.lineNumWidth||1)+"px")}t.style.display=i.length?"":"none",hn(e)}function bn(e){vn(e.display),fo(e),mn(e)}function _n(e,t,i,r){let s=this;this.input=i,s.scrollbarFiller=At("div",null,"CodeMirror-scrollbar-filler"),s.scrollbarFiller.setAttribute("cm-not-content","true"),s.gutterFiller=At("div",null,"CodeMirror-gutter-filler"),s.gutterFiller.setAttribute("cm-not-content","true"),s.lineDiv=It("div",null,"CodeMirror-code"),s.selectionDiv=At("div",null,null,"position: relative; z-index: 1"),s.cursorDiv=At("div",null,"CodeMirror-cursors"),s.measure=At("div",null,"CodeMirror-measure"),s.lineMeasure=At("div",null,"CodeMirror-measure"),s.lineSpace=It("div",[s.measure,s.lineMeasure,s.selectionDiv,s.cursorDiv,s.lineDiv],null,"position: relative; outline: none");let o=It("div",[s.lineSpace],"CodeMirror-lines");s.mover=At("div",[o],null,"position: relative"),s.sizer=At("div",[s.mover],"CodeMirror-sizer"),s.sizerWidth=null,s.heightForcer=At("div",null,null,"position: absolute; height: "+Gt+"px; width: 1px;"),s.gutters=At("div",null,"CodeMirror-gutters"),s.lineGutter=null,s.scroller=At("div",[s.sizer,s.heightForcer,s.gutters],"CodeMirror-scroll"),s.scroller.setAttribute("tabIndex","-1"),s.wrapper=At("div",[s.scrollbarFiller,s.gutterFiller,s.scroller],"CodeMirror"),dt&&ut<8&&(s.gutters.style.zIndex=-1,s.scroller.style.paddingRight=0),ht||nt&&xt||(s.scroller.draggable=!0),e&&(e.appendChild?e.appendChild(s.wrapper):e(s.wrapper)),s.viewFrom=s.viewTo=t.first,s.reportedViewFrom=s.reportedViewTo=t.first,s.view=[],s.renderedView=null,s.externalMeasured=null,s.viewOffset=0,s.lastWrapHeight=s.lastWrapWidth=0,s.updateLineNumbers=null,s.nativeBarWidth=s.barHeight=s.barWidth=0,s.scrollbarsClipped=!1,s.lineNumWidth=s.lineNumInnerWidth=s.lineNumChars=null,s.alignWidgets=!1,s.cachedCharWidth=s.cachedTextHeight=s.cachedPaddingH=null,s.maxLine=null,s.maxLineLength=0,s.maxLineChanged=!1,s.wheelDX=s.wheelDY=s.wheelStartX=s.wheelStartY=null,s.shift=!1,s.selForContextMenu=null,s.activeTouch=null,s.gutterSpecs=gn(r.gutters,r.lineNumbers),vn(s),i.init(s)}var yn=0,xn=null;function wn(e){let t=e.wheelDeltaX,i=e.wheelDeltaY;return null==t&&e.detail&&e.axis==e.HORIZONTAL_AXIS&&(t=e.detail),null==i&&e.detail&&e.axis==e.VERTICAL_AXIS?i=e.detail:null==i&&(i=e.wheelDelta),{x:t,y:i}}function kn(e){let t=wn(e);return t.x*=xn,t.y*=xn,t}function Cn(e,t){let i=wn(t),r=i.x,s=i.y,o=e.display,n=o.scroller,a=n.scrollWidth>n.clientWidth,l=n.scrollHeight>n.clientHeight;if(r&&a||s&&l){if(s&&wt&&ht)e:for(let i=t.target,r=o.view;i!=n;i=i.parentNode)for(let t=0;t<r.length;t++)if(r[t].node==i){e.display.currentWheelTarget=i;break e}if(r&&!nt&&!ft&&null!=xn)return s&&l&&zo(e,Math.max(0,n.scrollTop+s*xn)),Bo(e,Math.max(0,n.scrollLeft+r*xn)),(!s||s&&l)&&Ci(t),void(o.wheelStartX=null);if(s&&null!=xn){let t=s*xn,i=e.doc.scrollTop,r=i+o.wrapper.clientHeight;t<0?i=Math.max(0,i+t-50):r=Math.min(e.doc.height,r+t+50),un(e,{top:i,bottom:r})}yn<20&&(null==o.wheelStartX?(o.wheelStartX=n.scrollLeft,o.wheelStartY=n.scrollTop,o.wheelDX=r,o.wheelDY=s,setTimeout((()=>{if(null==o.wheelStartX)return;let e=n.scrollLeft-o.wheelStartX,t=n.scrollTop-o.wheelStartY,i=t&&o.wheelDY&&t/o.wheelDY||e&&o.wheelDX&&e/o.wheelDX;o.wheelStartX=o.wheelStartY=null,i&&(xn=(xn*yn+i)/(yn+1),++yn)}),200)):(o.wheelDX+=r,o.wheelDY+=s))}}dt?xn=-.53:nt?xn=15:mt?xn=-.7:gt&&(xn=-1/3);var Sn=class{constructor(e,t){this.ranges=e,this.primIndex=t}primary(){return this.ranges[this.primIndex]}equals(e){if(e==this)return!0;if(e.primIndex!=this.primIndex||e.ranges.length!=this.ranges.length)return!1;for(let t=0;t<this.ranges.length;t++){let i=this.ranges[t],r=e.ranges[t];if(!nr(i.anchor,r.anchor)||!nr(i.head,r.head))return!1}return!0}deepCopy(){let e=[];for(let t=0;t<this.ranges.length;t++)e[t]=new Tn(ar(this.ranges[t].anchor),ar(this.ranges[t].head));return new Sn(e,this.primIndex)}somethingSelected(){for(let e=0;e<this.ranges.length;e++)if(!this.ranges[e].empty())return!0;return!1}contains(e,t){t||(t=e);for(let i=0;i<this.ranges.length;i++){let r=this.ranges[i];if(or(t,r.from())>=0&&or(e,r.to())<=0)return i}return-1}},Tn=class{constructor(e,t){this.anchor=e,this.head=t}from(){return cr(this.anchor,this.head)}to(){return lr(this.anchor,this.head)}empty(){return this.head.line==this.anchor.line&&this.head.ch==this.anchor.ch}};function Mn(e,t,i){let r=e&&e.options.selectionsMayTouch,s=t[i];t.sort(((e,t)=>or(e.from(),t.from()))),i=Ut(t,s);for(let e=1;e<t.length;e++){let s=t[e],o=t[e-1],n=or(o.to(),s.from());if(r&&!s.empty()?n>0:n>=0){let r=cr(o.from(),s.from()),n=lr(o.to(),s.to()),a=o.empty()?s.from()==s.head:o.from()==o.head;e<=i&&--i,t.splice(--e,2,new Tn(a?n:r,a?r:n))}}return new Sn(t,i)}function Pn(e,t){return new Sn([new Tn(e,t||e)],0)}function $n(e){return e.text?sr(e.from.line+e.text.length-1,Qt(e.text).length+(1==e.text.length?e.from.ch:0)):e.to}function En(e,t){if(or(e,t.from)<0)return e;if(or(e,t.to)<=0)return $n(t);let i=e.line+t.text.length-(t.to.line-t.from.line)-1,r=e.ch;return e.line==t.to.line&&(r+=$n(t).ch-t.to.ch),sr(i,r)}function Ln(e,t){let i=[];for(let r=0;r<e.sel.ranges.length;r++){let s=e.sel.ranges[r];i.push(new Tn(En(s.anchor,t),En(s.head,t)))}return Mn(e.cm,i,e.sel.primIndex)}function Rn(e,t,i){return e.line==t.line?sr(i.line,e.ch-t.ch+i.ch):sr(i.line+(e.line-t.line),e.ch)}function An(e){e.doc.mode=Hi(e.options,e.doc.modeOption),In(e)}function In(e){e.doc.iter((e=>{e.stateAfter&&(e.stateAfter=null),e.styles&&(e.styles=null)})),e.doc.modeFrontier=e.doc.highlightFrontier=e.doc.first,nn(e,100),e.state.modeGen++,e.curOp&&fo(e)}function Nn(e,t){return 0==t.from.ch&&0==t.to.ch&&""==Qt(t.text)&&(!e.cm||e.cm.options.wholeLineUpdateBefore)}function Dn(e,t,i,r){function s(e){return i?i[e]:null}function o(e,i,s){!function(e,t,i,r){e.text=t,e.stateAfter&&(e.stateAfter=null),e.styles&&(e.styles=null),null!=e.order&&(e.order=null),Rr(e),Ar(e,i);let s=r?r(e):1;s!=e.height&&Qi(e,s)}(e,i,s,r),us(e,"change",e,t)}function n(e,t){let i=[];for(let o=e;o<t;++o)i.push(new Xr(c[o],s(o),r));return i}let a=t.from,l=t.to,c=t.text,d=Xi(e,a.line),u=Xi(e,l.line),h=Qt(c),p=s(c.length-1),m=l.line-a.line;if(t.full)e.insert(0,n(0,c.length)),e.remove(c.length,e.size-c.length);else if(Nn(e,t)){let t=n(0,c.length-1);o(u,u.text,p),m&&e.remove(a.line,m),t.length&&e.insert(a.line,t)}else if(d==u)if(1==c.length)o(d,d.text.slice(0,a.ch)+h+d.text.slice(l.ch),p);else{let t=n(1,c.length-1);t.push(new Xr(h+d.text.slice(l.ch),p,r)),o(d,d.text.slice(0,a.ch)+c[0],s(0)),e.insert(a.line+1,t)}else if(1==c.length)o(d,d.text.slice(0,a.ch)+c[0]+u.text.slice(l.ch),s(0)),e.remove(a.line+1,m);else{o(d,d.text.slice(0,a.ch)+c[0],s(0)),o(u,h+u.text.slice(l.ch),p);let t=n(1,c.length-1);m>1&&e.remove(a.line+1,m-1),e.insert(a.line+1,t)}us(e,"change",e,t)}function On(e,t,i){!function e(r,s,o){if(r.linked)for(let n=0;n<r.linked.length;++n){let a=r.linked[n];if(a.doc==s)continue;let l=o&&a.sharedHist;i&&!l||(t(a.doc,l),e(a.doc,r,l))}}(e,null,!0)}function Fn(e,t){if(t.cm)throw new Error("This document is already in use.");e.doc=t,t.cm=e,ho(e),An(e),zn(e),e.options.lineWrapping||Kr(e),e.options.mode=t.modeOption,fo(e)}function zn(e){("rtl"==e.doc.direction?Ot:Et)(e.display.lineDiv,"CodeMirror-rtl")}function Wn(e){this.done=[],this.undone=[],this.undoDepth=e?e.undoDepth:1/0,this.lastModTime=this.lastSelTime=0,this.lastOp=this.lastSelOp=null,this.lastOrigin=this.lastSelOrigin=null,this.generation=this.maxGeneration=e?e.maxGeneration:1}function Bn(e,t){let i={from:ar(t.from),to:$n(t),text:Yi(e,t.from,t.to)};return Vn(e,i,t.from.line,t.to.line+1),On(e,(e=>Vn(e,i,t.from.line,t.to.line+1)),!0),i}function jn(e){for(;e.length;){if(!Qt(e).ranges)break;e.pop()}}function Hn(e,t,i,r){let s=e.history;s.undone.length=0;let o,n,a=+new Date;if((s.lastOp==r||s.lastOrigin==t.origin&&t.origin&&("+"==t.origin.charAt(0)&&s.lastModTime>a-(e.cm?e.cm.options.historyEventDelay:500)||"*"==t.origin.charAt(0)))&&(o=function(e,t){return t?(jn(e.done),Qt(e.done)):e.done.length&&!Qt(e.done).ranges?Qt(e.done):e.done.length>1&&!e.done[e.done.length-2].ranges?(e.done.pop(),Qt(e.done)):void 0}(s,s.lastOp==r)))n=Qt(o.changes),0==or(t.from,t.to)&&0==or(t.from,n.to)?n.to=$n(t):o.changes.push(Bn(e,t));else{let i=Qt(s.done);for(i&&i.ranges||Gn(e.sel,s.done),o={changes:[Bn(e,t)],generation:s.generation},s.done.push(o);s.done.length>s.undoDepth;)s.done.shift(),s.done[0].ranges||s.done.shift()}s.done.push(i),s.generation=++s.maxGeneration,s.lastModTime=s.lastSelTime=a,s.lastOp=s.lastSelOp=r,s.lastOrigin=s.lastSelOrigin=t.origin,n||_i(e,"historyAdded")}function Un(e,t,i,r){let s=e.history,o=r&&r.origin;i==s.lastSelOp||o&&s.lastSelOrigin==o&&(s.lastModTime==s.lastSelTime&&s.lastOrigin==o||function(e,t,i,r){let s=t.charAt(0);return"*"==s||"+"==s&&i.ranges.length==r.ranges.length&&i.somethingSelected()==r.somethingSelected()&&new Date-e.history.lastSelTime<=(e.cm?e.cm.options.historyEventDelay:500)}(e,o,Qt(s.done),t))?s.done[s.done.length-1]=t:Gn(t,s.done),s.lastSelTime=+new Date,s.lastSelOrigin=o,s.lastSelOp=i,r&&!1!==r.clearRedo&&jn(s.undone)}function Gn(e,t){let i=Qt(t);i&&i.ranges&&i.equals(e)||t.push(e)}function Vn(e,t,i,r){let s=t["spans_"+e.id],o=0;e.iter(Math.max(e.first,i),Math.min(e.first+e.size,r),(i=>{i.markedSpans&&((s||(s=t["spans_"+e.id]={}))[o]=i.markedSpans),++o}))}function qn(e){if(!e)return null;let t;for(let i=0;i<e.length;++i)e[i].marker.explicitlyCleared?t||(t=e.slice(0,i)):t&&t.push(e[i]);return t?t.length?t:null:e}function Zn(e,t){let i=function(e,t){let i=t["spans_"+e.id];if(!i)return null;let r=[];for(let e=0;e<t.text.length;++e)r.push(qn(i[e]));return r}(e,t),r=Er(e,t);if(!i)return r;if(!r)return i;for(let e=0;e<i.length;++e){let t=i[e],s=r[e];if(t&&s)e:for(let e=0;e<s.length;++e){let i=s[e];for(let e=0;e<t.length;++e)if(t[e].marker==i.marker)continue e;t.push(i)}else s&&(i[e]=s)}return i}function Kn(e,t,i){let r=[];for(let o=0;o<e.length;++o){let n=e[o];if(n.ranges){r.push(i?Sn.prototype.deepCopy.call(n):n);continue}let a=n.changes,l=[];r.push({changes:l});for(let e=0;e<a.length;++e){let i,r=a[e];if(l.push({from:r.from,to:r.to,text:r.text}),t)for(var s in r)(i=s.match(/^spans_(\d+)$/))&&Ut(t,Number(i[1]))>-1&&(Qt(l)[s]=r[s],delete r[s])}}return r}function Xn(e,t,i,r){if(r){let r=e.anchor;if(i){let e=or(t,r)<0;e!=or(i,r)<0?(r=t,t=i):e!=or(t,i)<0&&(t=i)}return new Tn(r,t)}return new Tn(i||t,t)}function Yn(e,t,i,r,s){null==s&&(s=e.cm&&(e.cm.display.shift||e.extend)),ia(e,new Sn([Xn(e.sel.primary(),t,i,s)],0),r)}function Jn(e,t,i){let r=[],s=e.cm&&(e.cm.display.shift||e.extend);for(let i=0;i<e.sel.ranges.length;i++)r[i]=Xn(e.sel.ranges[i],t[i],null,s);ia(e,Mn(e.cm,r,e.sel.primIndex),i)}function Qn(e,t,i,r){let s=e.sel.ranges.slice(0);s[t]=i,ia(e,Mn(e.cm,s,e.sel.primIndex),r)}function ea(e,t,i,r){ia(e,Pn(t,i),r)}function ta(e,t,i){let r=e.history.done,s=Qt(r);s&&s.ranges?(r[r.length-1]=t,ra(e,t,i)):ia(e,t,i)}function ia(e,t,i){ra(e,t,i),Un(e,e.sel,e.cm?e.cm.curOp.id:NaN,i)}function ra(e,t,i){(wi(e,"beforeSelectionChange")||e.cm&&wi(e.cm,"beforeSelectionChange"))&&(t=function(e,t,i){let r={ranges:t.ranges,update:function(t){this.ranges=[];for(let i=0;i<t.length;i++)this.ranges[i]=new Tn(ur(e,t[i].anchor),ur(e,t[i].head))},origin:i&&i.origin};return _i(e,"beforeSelectionChange",e,r),e.cm&&_i(e.cm,"beforeSelectionChange",e.cm,r),r.ranges!=t.ranges?Mn(e.cm,r.ranges,r.ranges.length-1):t}(e,t,i));let r=i&&i.bias||(or(t.primary().head,e.sel.primary().head)<0?-1:1);sa(e,na(e,t,r,!0)),i&&!1===i.scroll||!e.cm||"nocursor"==e.cm.getOption("readOnly")||No(e.cm)}function sa(e,t){t.equals(e.sel)||(e.sel=t,e.cm&&(e.cm.curOp.updateInput=1,e.cm.curOp.selectionChanged=!0,xi(e.cm)),us(e,"cursorActivity",e))}function oa(e){sa(e,na(e,e.sel,null,!1))}function na(e,t,i,r){let s;for(let o=0;o<t.ranges.length;o++){let n=t.ranges[o],a=t.ranges.length==e.sel.ranges.length&&e.sel.ranges[o],l=la(e,n.anchor,a&&a.anchor,i,r),c=la(e,n.head,a&&a.head,i,r);(s||l!=n.anchor||c!=n.head)&&(s||(s=t.ranges.slice(0,o)),s[o]=new Tn(l,c))}return s?Mn(e.cm,s,t.primIndex):t}function aa(e,t,i,r,s){let o=Xi(e,t.line);if(o.markedSpans)for(let n=0;n<o.markedSpans.length;++n){let a=o.markedSpans[n],l=a.marker,c="selectLeft"in l?!l.selectLeft:l.inclusiveLeft,d="selectRight"in l?!l.selectRight:l.inclusiveRight;if((null==a.from||(c?a.from<=t.ch:a.from<t.ch))&&(null==a.to||(d?a.to>=t.ch:a.to>t.ch))){if(s&&(_i(l,"beforeCursorEnter"),l.explicitlyCleared)){if(o.markedSpans){--n;continue}break}if(!l.atomic)continue;if(i){let n,a=l.find(r<0?1:-1);if((r<0?d:c)&&(a=ca(e,a,-r,a&&a.line==t.line?o:null)),a&&a.line==t.line&&(n=or(a,i))&&(r<0?n<0:n>0))return aa(e,a,t,r,s)}let a=l.find(r<0?-1:1);return(r<0?c:d)&&(a=ca(e,a,r,a.line==t.line?o:null)),a?aa(e,a,t,r,s):null}}return t}function la(e,t,i,r,s){let o=r||1,n=aa(e,t,i,o,s)||!s&&aa(e,t,i,o,!0)||aa(e,t,i,-o,s)||!s&&aa(e,t,i,-o,!0);return n||(e.cantEdit=!0,sr(e.first,0))}function ca(e,t,i,r){return i<0&&0==t.ch?t.line>e.first?ur(e,sr(t.line-1)):null:i>0&&t.ch==(r||Xi(e,t.line)).text.length?t.line<e.first+e.size-1?sr(t.line+1,0):null:new sr(t.line,t.ch+i)}function da(e){e.setSelection(sr(e.firstLine(),0),sr(e.lastLine()),qt)}function ua(e,t,i){let r={canceled:!1,from:t.from,to:t.to,text:t.text,origin:t.origin,cancel:()=>r.canceled=!0};return i&&(r.update=(t,i,s,o)=>{t&&(r.from=ur(e,t)),i&&(r.to=ur(e,i)),s&&(r.text=s),void 0!==o&&(r.origin=o)}),_i(e,"beforeChange",e,r),e.cm&&_i(e.cm,"beforeChange",e.cm,r),r.canceled?(e.cm&&(e.cm.curOp.updateInput=2),null):{from:r.from,to:r.to,text:r.text,origin:r.origin}}function ha(e,t,i){if(e.cm){if(!e.cm.curOp)return rn(e.cm,ha)(e,t,i);if(e.cm.state.suppressEdits)return}if((wi(e,"beforeChange")||e.cm&&wi(e.cm,"beforeChange"))&&!(t=ua(e,t,!0)))return;let r=Sr&&!i&&function(e,t,i){let r=null;if(e.iter(t.line,i.line+1,(e=>{if(e.markedSpans)for(let t=0;t<e.markedSpans.length;++t){let i=e.markedSpans[t].marker;!i.readOnly||r&&-1!=Ut(r,i)||(r||(r=[])).push(i)}})),!r)return null;let s=[{from:t,to:i}];for(let e=0;e<r.length;++e){let t=r[e],i=t.find(0);for(let e=0;e<s.length;++e){let r=s[e];if(or(r.to,i.from)<0||or(r.from,i.to)>0)continue;let o=[e,1],n=or(r.from,i.from),a=or(r.to,i.to);(n<0||!t.inclusiveLeft&&!n)&&o.push({from:r.from,to:i.from}),(a>0||!t.inclusiveRight&&!a)&&o.push({from:i.to,to:r.to}),s.splice.apply(s,o),e+=o.length-3}}return s}(e,t.from,t.to);if(r)for(let i=r.length-1;i>=0;--i)pa(e,{from:r[i].from,to:r[i].to,text:i?[""]:t.text,origin:t.origin});else pa(e,t)}function pa(e,t){if(1==t.text.length&&""==t.text[0]&&0==or(t.from,t.to))return;let i=Ln(e,t);Hn(e,t,i,e.cm?e.cm.curOp.id:NaN),ga(e,t,i,Er(e,t));let r=[];On(e,((e,i)=>{i||-1!=Ut(r,e.history)||(ya(e.history,t),r.push(e.history)),ga(e,t,null,Er(e,t))}))}function ma(e,t,i){let r=e.cm&&e.cm.state.suppressEdits;if(r&&!i)return;let s,o=e.history,n=e.sel,a="undo"==t?o.done:o.undone,l="undo"==t?o.undone:o.done,c=0;for(;c<a.length&&(s=a[c],i?!s.ranges||s.equals(e.sel):s.ranges);c++);if(c==a.length)return;for(o.lastOrigin=o.lastSelOrigin=null;;){if(s=a.pop(),!s.ranges){if(r)return void a.push(s);break}if(Gn(s,l),i&&!s.equals(e.sel))return void ia(e,s,{clearRedo:!1});n=s}let d=[];Gn(n,l),l.push({changes:d,generation:o.generation}),o.generation=s.generation||++o.maxGeneration;let u=wi(e,"beforeChange")||e.cm&&wi(e.cm,"beforeChange");for(let i=s.changes.length-1;i>=0;--i){let r=s.changes[i];if(r.origin=t,u&&!ua(e,r,!1))return void(a.length=0);d.push(Bn(e,r));let o=i?Ln(e,r):Qt(a);ga(e,r,o,Zn(e,r)),!i&&e.cm&&e.cm.scrollIntoView({from:r.from,to:$n(r)});let n=[];On(e,((e,t)=>{t||-1!=Ut(n,e.history)||(ya(e.history,r),n.push(e.history)),ga(e,r,null,Zn(e,r))}))}}function fa(e,t){if(0!=t&&(e.first+=t,e.sel=new Sn(ei(e.sel.ranges,(e=>new Tn(sr(e.anchor.line+t,e.anchor.ch),sr(e.head.line+t,e.head.ch)))),e.sel.primIndex),e.cm)){fo(e.cm,e.first,e.first-t,t);for(let t=e.cm.display,i=t.viewFrom;i<t.viewTo;i++)go(e.cm,i,"gutter")}}function ga(e,t,i,r){if(e.cm&&!e.cm.curOp)return rn(e.cm,ga)(e,t,i,r);if(t.to.line<e.first)return void fa(e,t.text.length-1-(t.to.line-t.from.line));if(t.from.line>e.lastLine())return;if(t.from.line<e.first){let i=t.text.length-1-(e.first-t.from.line);fa(e,i),t={from:sr(e.first,0),to:sr(t.to.line+i,t.to.ch),text:[Qt(t.text)],origin:t.origin}}let s=e.lastLine();t.to.line>s&&(t={from:t.from,to:sr(s,Xi(e,s).text.length),text:[t.text[0]],origin:t.origin}),t.removed=Yi(e,t.from,t.to),i||(i=Ln(e,t)),e.cm?function(e,t,i){let r=e.doc,s=e.display,o=t.from,n=t.to,a=!1,l=o.line;e.options.lineWrapping||(l=er(jr(Xi(r,o.line))),r.iter(l,n.line+1,(e=>{if(e==s.maxLine)return a=!0,!0})));r.sel.contains(t.from,t.to)>-1&&xi(e);Dn(r,t,i,uo(e)),e.options.lineWrapping||(r.iter(l,o.line+t.text.length,(e=>{let t=Zr(e);t>s.maxLineLength&&(s.maxLine=e,s.maxLineLength=t,s.maxLineChanged=!0,a=!1)})),a&&(e.curOp.updateMaxLine=!0));(function(e,t){if(e.modeFrontier=Math.min(e.modeFrontier,t),e.highlightFrontier<t-10)return;let i=e.first;for(let r=t-1;r>i;r--){let s=Xi(e,r).stateAfter;if(s&&(!(s instanceof pr)||r+s.lookAhead<t)){i=r+1;break}}e.highlightFrontier=Math.min(e.highlightFrontier,i)})(r,o.line),nn(e,400);let c=t.text.length-(n.line-o.line)-1;t.full?fo(e):o.line!=n.line||1!=t.text.length||Nn(e.doc,t)?fo(e,o.line,n.line+1,c):go(e,o.line,"text");let d=wi(e,"changes"),u=wi(e,"change");if(u||d){let i={from:o,to:n,text:t.text,removed:t.removed,origin:t.origin};u&&us(e,"change",e,i),d&&(e.curOp.changeObjs||(e.curOp.changeObjs=[])).push(i)}e.display.selForContextMenu=null}(e.cm,t,r):Dn(e,t,r),ra(e,i,qt),e.cantEdit&&la(e,sr(e.firstLine(),0))&&(e.cantEdit=!1)}function va(e,t,i,r,s){r||(r=i),or(r,i)<0&&([i,r]=[r,i]),"string"==typeof t&&(t=e.splitLines(t)),ha(e,{from:i,to:r,text:t,origin:s})}function ba(e,t,i,r){i<e.line?e.line+=r:t<e.line&&(e.line=t,e.ch=0)}function _a(e,t,i,r){for(let s=0;s<e.length;++s){let o=e[s],n=!0;if(o.ranges){o.copied||(o=e[s]=o.deepCopy(),o.copied=!0);for(let e=0;e<o.ranges.length;e++)ba(o.ranges[e].anchor,t,i,r),ba(o.ranges[e].head,t,i,r)}else{for(let e=0;e<o.changes.length;++e){let s=o.changes[e];if(i<s.from.line)s.from=sr(s.from.line+r,s.from.ch),s.to=sr(s.to.line+r,s.to.ch);else if(t<=s.to.line){n=!1;break}}n||(e.splice(0,s+1),s=0)}}}function ya(e,t){let i=t.from.line,r=t.to.line,s=t.text.length-(r-i)-1;_a(e.done,i,r,s),_a(e.undone,i,r,s)}function xa(e,t,i,r){let s=t,o=t;return"number"==typeof t?o=Xi(e,dr(e,t)):s=er(t),null==s?null:(r(o,s)&&e.cm&&go(e.cm,s,i),o)}function wa(e){this.lines=e,this.parent=null;let t=0;for(let i=0;i<e.length;++i)e[i].parent=this,t+=e[i].height;this.height=t}function ka(e){this.children=e;let t=0,i=0;for(let r=0;r<e.length;++r){let s=e[r];t+=s.chunkSize(),i+=s.height,s.parent=this}this.size=t,this.height=i,this.parent=null}wa.prototype={chunkSize(){return this.lines.length},removeInner(e,t){for(let i=e,r=e+t;i<r;++i){let e=this.lines[i];this.height-=e.height,Yr(e),us(e,"delete")}this.lines.splice(e,t)},collapse(e){e.push.apply(e,this.lines)},insertInner(e,t,i){this.height+=i,this.lines=this.lines.slice(0,e).concat(t).concat(this.lines.slice(e));for(let e=0;e<t.length;++e)t[e].parent=this},iterN(e,t,i){for(let r=e+t;e<r;++e)if(i(this.lines[e]))return!0}},ka.prototype={chunkSize(){return this.size},removeInner(e,t){this.size-=t;for(let i=0;i<this.children.length;++i){let r=this.children[i],s=r.chunkSize();if(e<s){let o=Math.min(t,s-e),n=r.height;if(r.removeInner(e,o),this.height-=n-r.height,s==o&&(this.children.splice(i--,1),r.parent=null),0==(t-=o))break;e=0}else e-=s}if(this.size-t<25&&(this.children.length>1||!(this.children[0]instanceof wa))){let e=[];this.collapse(e),this.children=[new wa(e)],this.children[0].parent=this}},collapse(e){for(let t=0;t<this.children.length;++t)this.children[t].collapse(e)},insertInner(e,t,i){this.size+=t.length,this.height+=i;for(let r=0;r<this.children.length;++r){let s=this.children[r],o=s.chunkSize();if(e<=o){if(s.insertInner(e,t,i),s.lines&&s.lines.length>50){let e=s.lines.length%25+25;for(let t=e;t<s.lines.length;){let e=new wa(s.lines.slice(t,t+=25));s.height-=e.height,this.children.splice(++r,0,e),e.parent=this}s.lines=s.lines.slice(0,e),this.maybeSpill()}break}e-=o}},maybeSpill(){if(this.children.length<=10)return;let e=this;do{let t=new ka(e.children.splice(e.children.length-5,5));if(e.parent){e.size-=t.size,e.height-=t.height;let i=Ut(e.parent.children,e);e.parent.children.splice(i+1,0,t)}else{let i=new ka(e.children);i.parent=e,e.children=[i,t],e=i}t.parent=e.parent}while(e.children.length>10);e.parent.maybeSpill()},iterN(e,t,i){for(let r=0;r<this.children.length;++r){let s=this.children[r],o=s.chunkSize();if(e<o){let r=Math.min(t,o-e);if(s.iterN(e,r,i))return!0;if(0==(t-=r))break;e=0}else e-=o}}};var Ca=class{constructor(e,t,i){if(i)for(let e in i)i.hasOwnProperty(e)&&(this[e]=i[e]);this.doc=e,this.node=t}clear(){let e=this.doc.cm,t=this.line.widgets,i=this.line,r=er(i);if(null==r||!t)return;for(let e=0;e<t.length;++e)t[e]==this&&t.splice(e--,1);t.length||(i.widgets=null);let s=Cs(this);Qi(i,Math.max(0,i.height-s)),e&&(tn(e,(()=>{Sa(e,i,-s),go(e,r,"widget")})),us(e,"lineWidgetCleared",e,this,r))}changed(){let e=this.height,t=this.doc.cm,i=this.line;this.height=null;let r=Cs(this)-e;r&&(Gr(this.doc,i)||Qi(i,i.height+r),t&&tn(t,(()=>{t.curOp.forceUpdate=!0,Sa(t,i,r),us(t,"lineWidgetChanged",t,this,er(i))})))}};function Sa(e,t,i){qr(t)<(e.curOp&&e.curOp.scrollTop||e.doc.scrollTop)&&Io(e,i)}ki(Ca);var Ta=0,Ma=class{constructor(e,t){this.lines=[],this.type=t,this.doc=e,this.id=++Ta}clear(){if(this.explicitlyCleared)return;let e=this.doc.cm,t=e&&!e.curOp;if(t&&Zo(e),wi(this,"clear")){let e=this.find();e&&us(this,"clear",e.from,e.to)}let i=null,r=null;for(let t=0;t<this.lines.length;++t){let s=this.lines[t],o=Pr(s.markedSpans,this);e&&!this.collapsed?go(e,er(s),"text"):e&&(null!=o.to&&(r=er(s)),null!=o.from&&(i=er(s))),s.markedSpans=$r(s.markedSpans,o),null==o.from&&this.collapsed&&!Gr(this.doc,s)&&e&&Qi(s,no(e.display))}if(e&&this.collapsed&&!e.options.lineWrapping)for(let t=0;t<this.lines.length;++t){let i=jr(this.lines[t]),r=Zr(i);r>e.display.maxLineLength&&(e.display.maxLine=i,e.display.maxLineLength=r,e.display.maxLineChanged=!0)}null!=i&&e&&this.collapsed&&fo(e,i,r+1),this.lines.length=0,this.explicitlyCleared=!0,this.atomic&&this.doc.cantEdit&&(this.doc.cantEdit=!1,e&&oa(e.doc)),e&&us(e,"markerCleared",e,this,i,r),t&&Ko(e),this.parent&&this.parent.clear()}find(e,t){let i,r;null==e&&"bookmark"==this.type&&(e=1);for(let s=0;s<this.lines.length;++s){let o=this.lines[s],n=Pr(o.markedSpans,this);if(null!=n.from&&(i=sr(t?o:er(o),n.from),-1==e))return i;if(null!=n.to&&(r=sr(t?o:er(o),n.to),1==e))return r}return i&&{from:i,to:r}}changed(){let e=this.find(-1,!0),t=this,i=this.doc.cm;e&&i&&tn(i,(()=>{let r=e.line,s=er(e.line),o=Is(i,s);if(o&&(Bs(o),i.curOp.selectionChanged=i.curOp.forceUpdate=!0),i.curOp.updateMaxLine=!0,!Gr(t.doc,r)&&null!=t.height){let e=t.height;t.height=null;let i=Cs(t)-e;i&&Qi(r,r.height+i)}us(i,"markerChanged",i,this)}))}attachLine(e){if(!this.lines.length&&this.doc.cm){let e=this.doc.cm.curOp;e.maybeHiddenMarkers&&-1!=Ut(e.maybeHiddenMarkers,this)||(e.maybeUnhiddenMarkers||(e.maybeUnhiddenMarkers=[])).push(this)}this.lines.push(e)}detachLine(e){if(this.lines.splice(Ut(this.lines,e),1),!this.lines.length&&this.doc.cm){let e=this.doc.cm.curOp;(e.maybeHiddenMarkers||(e.maybeHiddenMarkers=[])).push(this)}}};function Pa(e,t,i,r,s){if(r&&r.shared)return function(e,t,i,r,s){r=Bt(r),r.shared=!1;let o=[Pa(e,t,i,r,s)],n=o[0],a=r.widgetNode;return On(e,(e=>{a&&(r.widgetNode=a.cloneNode(!0)),o.push(Pa(e,ur(e,t),ur(e,i),r,s));for(let t=0;t<e.linked.length;++t)if(e.linked[t].isParent)return;n=Qt(o)})),new $a(o,n)}(e,t,i,r,s);if(e.cm&&!e.cm.curOp)return rn(e.cm,Pa)(e,t,i,r,s);let o=new Ma(e,s),n=or(t,i);if(r&&Bt(r,o,!1),n>0||0==n&&!1!==o.clearWhenEmpty)return o;if(o.replacedWith&&(o.collapsed=!0,o.widgetNode=It("span",[o.replacedWith],"CodeMirror-widget"),r.handleMouseEvents||o.widgetNode.setAttribute("cm-ignore-events","true"),r.insertLeft&&(o.widgetNode.insertLeft=!0)),o.collapsed){if(Br(e,t.line,t,i,o)||t.line!=i.line&&Br(e,i.line,t,i,o))throw new Error("Inserting collapsed marker partially overlapping an existing one");Tr=!0}o.addToHistory&&Hn(e,{from:t,to:i,origin:"markText"},e.sel,NaN);let a,l=t.line,c=e.cm;if(e.iter(l,i.line+1,(e=>{c&&o.collapsed&&!c.options.lineWrapping&&jr(e)==c.display.maxLine&&(a=!0),o.collapsed&&l!=t.line&&Qi(e,0),function(e,t){e.markedSpans=e.markedSpans?e.markedSpans.concat([t]):[t],t.marker.attachLine(e)}(e,new Mr(o,l==t.line?t.ch:null,l==i.line?i.ch:null)),++l})),o.collapsed&&e.iter(t.line,i.line+1,(t=>{Gr(e,t)&&Qi(t,0)})),o.clearOnEnter&&gi(o,"beforeCursorEnter",(()=>o.clear())),o.readOnly&&(Sr=!0,(e.history.done.length||e.history.undone.length)&&e.clearHistory()),o.collapsed&&(o.id=++Ta,o.atomic=!0),c){if(a&&(c.curOp.updateMaxLine=!0),o.collapsed)fo(c,t.line,i.line+1);else if(o.className||o.startStyle||o.endStyle||o.css||o.attributes||o.title)for(let e=t.line;e<=i.line;e++)go(c,e,"text");o.atomic&&oa(c.doc),us(c,"markerAdded",c,o)}return o}ki(Ma);var $a=class{constructor(e,t){this.markers=e,this.primary=t;for(let t=0;t<e.length;++t)e[t].parent=this}clear(){if(!this.explicitlyCleared){this.explicitlyCleared=!0;for(let e=0;e<this.markers.length;++e)this.markers[e].clear();us(this,"clear")}}find(e,t){return this.primary.find(e,t)}};function Ea(e){return e.findMarks(sr(e.first,0),e.clipPos(sr(e.lastLine())),(e=>e.parent))}function La(e){for(let t=0;t<e.length;t++){let i=e[t],r=[i.primary.doc];On(i.primary.doc,(e=>r.push(e)));for(let e=0;e<i.markers.length;e++){let t=i.markers[e];-1==Ut(r,t.doc)&&(t.parent=null,i.markers.splice(e--,1))}}}ki($a);var Ra=0,Aa=function(e,t,i,r,s){if(!(this instanceof Aa))return new Aa(e,t,i,r,s);null==i&&(i=0),ka.call(this,[new wa([new Xr("",null)])]),this.first=i,this.scrollTop=this.scrollLeft=0,this.cantEdit=!1,this.cleanGeneration=1,this.modeFrontier=this.highlightFrontier=i;let o=sr(i,0);this.sel=Pn(o),this.history=new Wn(null),this.id=++Ra,this.modeOption=t,this.lineSep=r,this.direction="rtl"==s?"rtl":"ltr",this.extend=!1,"string"==typeof e&&(e=this.splitLines(e)),Dn(this,{from:o,to:o,text:e}),ia(this,Pn(o),qt)};Aa.prototype=ii(ka.prototype,{constructor:Aa,iter:function(e,t,i){i?this.iterN(e-this.first,t-e,i):this.iterN(this.first,this.first+this.size,e)},insert:function(e,t){let i=0;for(let e=0;e<t.length;++e)i+=t[e].height;this.insertInner(e-this.first,t,i)},remove:function(e,t){this.removeInner(e-this.first,t)},getValue:function(e){let t=Ji(this,this.first,this.first+this.size);return!1===e?t:t.join(e||this.lineSeparator())},setValue:on((function(e){let t=sr(this.first,0),i=this.first+this.size-1;ha(this,{from:t,to:sr(i,Xi(this,i).text.length),text:this.splitLines(e),origin:"setValue",full:!0},!0),this.cm&&Do(this.cm,0,0),ia(this,Pn(t),qt)})),replaceRange:function(e,t,i,r){va(this,e,t=ur(this,t),i=i?ur(this,i):t,r)},getRange:function(e,t,i){let r=Yi(this,ur(this,e),ur(this,t));return!1===i?r:r.join(i||this.lineSeparator())},getLine:function(e){let t=this.getLineHandle(e);return t&&t.text},getLineHandle:function(e){if(ir(this,e))return Xi(this,e)},getLineNumber:function(e){return er(e)},getLineHandleVisualStart:function(e){return"number"==typeof e&&(e=Xi(this,e)),jr(e)},lineCount:function(){return this.size},firstLine:function(){return this.first},lastLine:function(){return this.first+this.size-1},clipPos:function(e){return ur(this,e)},getCursor:function(e){let t,i=this.sel.primary();return t=null==e||"head"==e?i.head:"anchor"==e?i.anchor:"end"==e||"to"==e||!1===e?i.to():i.from(),t},listSelections:function(){return this.sel.ranges},somethingSelected:function(){return this.sel.somethingSelected()},setCursor:on((function(e,t,i){ea(this,ur(this,"number"==typeof e?sr(e,t||0):e),null,i)})),setSelection:on((function(e,t,i){ea(this,ur(this,e),ur(this,t||e),i)})),extendSelection:on((function(e,t,i){Yn(this,ur(this,e),t&&ur(this,t),i)})),extendSelections:on((function(e,t){Jn(this,hr(this,e),t)})),extendSelectionsBy:on((function(e,t){Jn(this,hr(this,ei(this.sel.ranges,e)),t)})),setSelections:on((function(e,t,i){if(!e.length)return;let r=[];for(let t=0;t<e.length;t++)r[t]=new Tn(ur(this,e[t].anchor),ur(this,e[t].head||e[t].anchor));null==t&&(t=Math.min(e.length-1,this.sel.primIndex)),ia(this,Mn(this.cm,r,t),i)})),addSelection:on((function(e,t,i){let r=this.sel.ranges.slice(0);r.push(new Tn(ur(this,e),ur(this,t||e))),ia(this,Mn(this.cm,r,r.length-1),i)})),getSelection:function(e){let t,i=this.sel.ranges;for(let e=0;e<i.length;e++){let r=Yi(this,i[e].from(),i[e].to());t=t?t.concat(r):r}return!1===e?t:t.join(e||this.lineSeparator())},getSelections:function(e){let t=[],i=this.sel.ranges;for(let r=0;r<i.length;r++){let s=Yi(this,i[r].from(),i[r].to());!1!==e&&(s=s.join(e||this.lineSeparator())),t[r]=s}return t},replaceSelection:function(e,t,i){let r=[];for(let t=0;t<this.sel.ranges.length;t++)r[t]=e;this.replaceSelections(r,t,i||"+input")},replaceSelections:on((function(e,t,i){let r=[],s=this.sel;for(let t=0;t<s.ranges.length;t++){let o=s.ranges[t];r[t]={from:o.from(),to:o.to(),text:this.splitLines(e[t]),origin:i}}let o=t&&"end"!=t&&function(e,t,i){let r=[],s=sr(e.first,0),o=s;for(let n=0;n<t.length;n++){let a=t[n],l=Rn(a.from,s,o),c=Rn($n(a),s,o);if(s=a.to,o=c,"around"==i){let t=e.sel.ranges[n],i=or(t.head,t.anchor)<0;r[n]=new Tn(i?c:l,i?l:c)}else r[n]=new Tn(l,l)}return new Sn(r,e.sel.primIndex)}(this,r,t);for(let e=r.length-1;e>=0;e--)ha(this,r[e]);o?ta(this,o):this.cm&&No(this.cm)})),undo:on((function(){ma(this,"undo")})),redo:on((function(){ma(this,"redo")})),undoSelection:on((function(){ma(this,"undo",!0)})),redoSelection:on((function(){ma(this,"redo",!0)})),setExtending:function(e){this.extend=e},getExtending:function(){return this.extend},historySize:function(){let e=this.history,t=0,i=0;for(let i=0;i<e.done.length;i++)e.done[i].ranges||++t;for(let t=0;t<e.undone.length;t++)e.undone[t].ranges||++i;return{undo:t,redo:i}},clearHistory:function(){this.history=new Wn(this.history),On(this,(e=>e.history=this.history),!0)},markClean:function(){this.cleanGeneration=this.changeGeneration(!0)},changeGeneration:function(e){return e&&(this.history.lastOp=this.history.lastSelOp=this.history.lastOrigin=null),this.history.generation},isClean:function(e){return this.history.generation==(e||this.cleanGeneration)},getHistory:function(){return{done:Kn(this.history.done),undone:Kn(this.history.undone)}},setHistory:function(e){let t=this.history=new Wn(this.history);t.done=Kn(e.done.slice(0),null,!0),t.undone=Kn(e.undone.slice(0),null,!0)},setGutterMarker:on((function(e,t,i){return xa(this,e,"gutter",(e=>{let r=e.gutterMarkers||(e.gutterMarkers={});return r[t]=i,!i&&ni(r)&&(e.gutterMarkers=null),!0}))})),clearGutter:on((function(e){this.iter((t=>{t.gutterMarkers&&t.gutterMarkers[e]&&xa(this,t,"gutter",(()=>(t.gutterMarkers[e]=null,ni(t.gutterMarkers)&&(t.gutterMarkers=null),!0)))}))})),lineInfo:function(e){let t;if("number"==typeof e){if(!ir(this,e))return null;if(t=e,!(e=Xi(this,e)))return null}else if(t=er(e),null==t)return null;return{line:t,handle:e,text:e.text,gutterMarkers:e.gutterMarkers,textClass:e.textClass,bgClass:e.bgClass,wrapClass:e.wrapClass,widgets:e.widgets}},addLineClass:on((function(e,t,i){return xa(this,e,"gutter"==t?"gutter":"class",(e=>{let r="text"==t?"textClass":"background"==t?"bgClass":"gutter"==t?"gutterClass":"wrapClass";if(e[r]){if(Pt(i).test(e[r]))return!1;e[r]+=" "+i}else e[r]=i;return!0}))})),removeLineClass:on((function(e,t,i){return xa(this,e,"gutter"==t?"gutter":"class",(e=>{let r="text"==t?"textClass":"background"==t?"bgClass":"gutter"==t?"gutterClass":"wrapClass",s=e[r];if(!s)return!1;if(null==i)e[r]=null;else{let t=s.match(Pt(i));if(!t)return!1;let o=t.index+t[0].length;e[r]=s.slice(0,t.index)+(t.index&&o!=s.length?" ":"")+s.slice(o)||null}return!0}))})),addLineWidget:on((function(e,t,i){return function(e,t,i,r){let s=new Ca(e,i,r),o=e.cm;return o&&s.noHScroll&&(o.display.alignWidgets=!0),xa(e,t,"widget",(t=>{let i=t.widgets||(t.widgets=[]);if(null==s.insertAt?i.push(s):i.splice(Math.min(i.length,Math.max(0,s.insertAt)),0,s),s.line=t,o&&!Gr(e,t)){let i=qr(t)<e.scrollTop;Qi(t,t.height+Cs(s)),i&&Io(o,s.height),o.curOp.forceUpdate=!0}return!0})),o&&us(o,"lineWidgetAdded",o,s,"number"==typeof t?t:er(t)),s}(this,e,t,i)})),removeLineWidget:function(e){e.clear()},markText:function(e,t,i){return Pa(this,ur(this,e),ur(this,t),i,i&&i.type||"range")},setBookmark:function(e,t){let i={replacedWith:t&&(null==t.nodeType?t.widget:t),insertLeft:t&&t.insertLeft,clearWhenEmpty:!1,shared:t&&t.shared,handleMouseEvents:t&&t.handleMouseEvents};return Pa(this,e=ur(this,e),e,i,"bookmark")},findMarksAt:function(e){let t=[],i=Xi(this,(e=ur(this,e)).line).markedSpans;if(i)for(let r=0;r<i.length;++r){let s=i[r];(null==s.from||s.from<=e.ch)&&(null==s.to||s.to>=e.ch)&&t.push(s.marker.parent||s.marker)}return t},findMarks:function(e,t,i){e=ur(this,e),t=ur(this,t);let r=[],s=e.line;return this.iter(e.line,t.line+1,(o=>{let n=o.markedSpans;if(n)for(let o=0;o<n.length;o++){let a=n[o];null!=a.to&&s==e.line&&e.ch>=a.to||null==a.from&&s!=e.line||null!=a.from&&s==t.line&&a.from>=t.ch||i&&!i(a.marker)||r.push(a.marker.parent||a.marker)}++s})),r},getAllMarks:function(){let e=[];return this.iter((t=>{let i=t.markedSpans;if(i)for(let t=0;t<i.length;++t)null!=i[t].from&&e.push(i[t].marker)})),e},posFromIndex:function(e){let t,i=this.first,r=this.lineSeparator().length;return this.iter((s=>{let o=s.text.length+r;if(o>e)return t=e,!0;e-=o,++i})),ur(this,sr(i,t))},indexFromPos:function(e){let t=(e=ur(this,e)).ch;if(e.line<this.first||e.ch<0)return 0;let i=this.lineSeparator().length;return this.iter(this.first,e.line,(e=>{t+=e.text.length+i})),t},copy:function(e){let t=new Aa(Ji(this,this.first,this.first+this.size),this.modeOption,this.first,this.lineSep,this.direction);return t.scrollTop=this.scrollTop,t.scrollLeft=this.scrollLeft,t.sel=this.sel,t.extend=!1,e&&(t.history.undoDepth=this.history.undoDepth,t.setHistory(this.getHistory())),t},linkedDoc:function(e){e||(e={});let t=this.first,i=this.first+this.size;null!=e.from&&e.from>t&&(t=e.from),null!=e.to&&e.to<i&&(i=e.to);let r=new Aa(Ji(this,t,i),e.mode||this.modeOption,t,this.lineSep,this.direction);return e.sharedHist&&(r.history=this.history),(this.linked||(this.linked=[])).push({doc:r,sharedHist:e.sharedHist}),r.linked=[{doc:this,isParent:!0,sharedHist:e.sharedHist}],function(e,t){for(let i=0;i<t.length;i++){let r=t[i],s=r.find(),o=e.clipPos(s.from),n=e.clipPos(s.to);if(or(o,n)){let t=Pa(e,o,n,r.primary,r.primary.type);r.markers.push(t),t.parent=r}}}(r,Ea(this)),r},unlinkDoc:function(e){if(e instanceof Pl&&(e=e.doc),this.linked)for(let t=0;t<this.linked.length;++t){if(this.linked[t].doc==e){this.linked.splice(t,1),e.unlinkDoc(this),La(Ea(this));break}}if(e.history==this.history){let t=[e.id];On(e,(e=>t.push(e.id)),!0),e.history=new Wn(null),e.history.done=Kn(this.history.done,t),e.history.undone=Kn(this.history.undone,t)}},iterLinkedDocs:function(e){On(this,e)},getMode:function(){return this.mode},getEditor:function(){return this.cm},splitLines:function(e){return this.lineSep?e.split(this.lineSep):Ni(e)},lineSeparator:function(){return this.lineSep||"\n"},setDirection:on((function(e){var t;("rtl"!=e&&(e="ltr"),e!=this.direction)&&(this.direction=e,this.iter((e=>e.order=null)),this.cm&&tn(t=this.cm,(()=>{zn(t),fo(t)})))}))}),Aa.prototype.eachLine=Aa.prototype.iter;var Ia=Aa,Na=0;function Da(e){let t=this;if(Oa(t),yi(t,e)||Ss(t.display,e))return;Ci(e),dt&&(Na=+new Date);let i=po(t,e,!0),r=e.dataTransfer.files;if(i&&!t.isReadOnly())if(r&&r.length&&window.FileReader&&window.File){let e=r.length,s=Array(e),o=0;const n=()=>{++o==e&&rn(t,(()=>{i=ur(t.doc,i);let e={from:i,to:i,text:t.doc.splitLines(s.filter((e=>null!=e)).join(t.doc.lineSeparator())),origin:"paste"};ha(t.doc,e),ta(t.doc,Pn(ur(t.doc,i),ur(t.doc,$n(e))))}))()},a=(e,i)=>{if(t.options.allowDropFileTypes&&-1==Ut(t.options.allowDropFileTypes,e.type))return void n();let r=new FileReader;r.onerror=()=>n(),r.onload=()=>{let e=r.result;/[\x00-\x08\x0e-\x1f]{2}/.test(e)||(s[i]=e),n()},r.readAsText(e)};for(let e=0;e<r.length;e++)a(r[e],e)}else{if(t.state.draggingText&&t.doc.sel.contains(i)>-1)return t.state.draggingText(e),void setTimeout((()=>t.display.input.focus()),20);try{let r=e.dataTransfer.getData("Text");if(r){let e;if(t.state.draggingText&&!t.state.draggingText.copy&&(e=t.listSelections()),ra(t.doc,Pn(i,i)),e)for(let i=0;i<e.length;++i)va(t.doc,"",e[i].anchor,e[i].head,"drag");t.replaceSelection(r,"around","paste"),t.display.input.focus()}}catch(e){}}}function Oa(e){e.display.dragCursor&&(e.display.lineSpace.removeChild(e.display.dragCursor),e.display.dragCursor=null)}function Fa(e){if(!document.getElementsByClassName)return;let t=document.getElementsByClassName("CodeMirror"),i=[];for(let e=0;e<t.length;e++){let r=t[e].CodeMirror;r&&i.push(r)}i.length&&i[0].operation((()=>{for(let t=0;t<i.length;t++)e(i[t])}))}var za=!1;function Wa(){za||(!function(){let e;gi(window,"resize",(()=>{null==e&&(e=setTimeout((()=>{e=null,Fa(Ba)}),100))})),gi(window,"blur",(()=>Fa($o)))}(),za=!0)}function Ba(e){let t=e.display;t.cachedCharWidth=t.cachedTextHeight=t.cachedPaddingH=null,t.scrollbarsClipped=!1,e.setSize()}var ja={3:"Pause",8:"Backspace",9:"Tab",13:"Enter",16:"Shift",17:"Ctrl",18:"Alt",19:"Pause",20:"CapsLock",27:"Esc",32:"Space",33:"PageUp",34:"PageDown",35:"End",36:"Home",37:"Left",38:"Up",39:"Right",40:"Down",44:"PrintScrn",45:"Insert",46:"Delete",59:";",61:"=",91:"Mod",92:"Mod",93:"Mod",106:"*",107:"=",109:"-",110:".",111:"/",145:"ScrollLock",173:"-",186:";",187:"=",188:",",189:"-",190:".",191:"/",192:"`",219:"[",220:"\\",221:"]",222:"'",224:"Mod",63232:"Up",63233:"Down",63234:"Left",63235:"Right",63272:"Delete",63273:"Home",63275:"End",63276:"PageUp",63277:"PageDown",63302:"Insert"};for(let e=0;e<10;e++)ja[e+48]=ja[e+96]=String(e);for(let e=65;e<=90;e++)ja[e]=String.fromCharCode(e);for(let e=1;e<=12;e++)ja[e+111]=ja[e+63235]="F"+e;var Ha={};function Ua(e){let t,i,r,s,o=e.split(/-(?!$)/);e=o[o.length-1];for(let e=0;e<o.length-1;e++){let n=o[e];if(/^(cmd|meta|m)$/i.test(n))s=!0;else if(/^a(lt)?$/i.test(n))t=!0;else if(/^(c|ctrl|control)$/i.test(n))i=!0;else{if(!/^s(hift)?$/i.test(n))throw new Error("Unrecognized modifier name: "+n);r=!0}}return t&&(e="Alt-"+e),i&&(e="Ctrl-"+e),s&&(e="Cmd-"+e),r&&(e="Shift-"+e),e}function Ga(e){let t={};for(let i in e)if(e.hasOwnProperty(i)){let r=e[i];if(/^(name|fallthrough|(de|at)tach)$/.test(i))continue;if("..."==r){delete e[i];continue}let s=ei(i.split(" "),Ua);for(let e=0;e<s.length;e++){let i,o;e==s.length-1?(o=s.join(" "),i=r):(o=s.slice(0,e+1).join(" "),i="...");let n=t[o];if(n){if(n!=i)throw new Error("Inconsistent bindings for "+o)}else t[o]=i}delete e[i]}for(let i in t)e[i]=t[i];return e}function Va(e,t,i,r){let s=(t=Xa(t)).call?t.call(e,r):t[e];if(!1===s)return"nothing";if("..."===s)return"multi";if(null!=s&&i(s))return"handled";if(t.fallthrough){if("[object Array]"!=Object.prototype.toString.call(t.fallthrough))return Va(e,t.fallthrough,i,r);for(let s=0;s<t.fallthrough.length;s++){let o=Va(e,t.fallthrough[s],i,r);if(o)return o}}}function qa(e){let t="string"==typeof e?e:ja[e.keyCode];return"Ctrl"==t||"Alt"==t||"Shift"==t||"Mod"==t}function Za(e,t,i){let r=e;return t.altKey&&"Alt"!=r&&(e="Alt-"+e),(Tt?t.metaKey:t.ctrlKey)&&"Ctrl"!=r&&(e="Ctrl-"+e),(Tt?t.ctrlKey:t.metaKey)&&"Mod"!=r&&(e="Cmd-"+e),!i&&t.shiftKey&&"Shift"!=r&&(e="Shift-"+e),e}function Ka(e,t){if(ft&&34==e.keyCode&&e.char)return!1;let i=ja[e.keyCode];return null!=i&&!e.altGraphKey&&(3==e.keyCode&&e.code&&(i=e.code),Za(i,e,t))}function Xa(e){return"string"==typeof e?Ha[e]:e}function Ya(e,t){let i=e.doc.sel.ranges,r=[];for(let e=0;e<i.length;e++){let s=t(i[e]);for(;r.length&&or(s.from,Qt(r).to)<=0;){let e=r.pop();if(or(e.from,s.from)<0){s.from=e.from;break}}r.push(s)}tn(e,(()=>{for(let t=r.length-1;t>=0;t--)va(e.doc,"",r[t].from,r[t].to,"+delete");No(e)}))}function Ja(e,t,i){let r=ci(e.text,t+i,i);return r<0||r>e.text.length?null:r}function Qa(e,t,i){let r=Ja(e,t.ch,i);return null==r?null:new sr(t.line,r,i<0?"after":"before")}function el(e,t,i,r,s){if(e){"rtl"==t.doc.direction&&(s=-s);let e=mi(i,t.doc.direction);if(e){let o,n=s<0?Qt(e):e[0],a=s<0==(1==n.level)?"after":"before";if(n.level>0||"rtl"==t.doc.direction){let e=Ns(t,i);o=s<0?i.text.length-1:0;let r=Ds(t,e,o).top;o=di((i=>Ds(t,e,i).top==r),s<0==(1==n.level)?n.from:n.to-1,o),"before"==a&&(o=Ja(i,o,1))}else o=s<0?n.to:n.from;return new sr(r,o,a)}}return new sr(r,s<0?i.text.length:0,s<0?"before":"after")}Ha.basic={Left:"goCharLeft",Right:"goCharRight",Up:"goLineUp",Down:"goLineDown",End:"goLineEnd",Home:"goLineStartSmart",PageUp:"goPageUp",PageDown:"goPageDown",Delete:"delCharAfter",Backspace:"delCharBefore","Shift-Backspace":"delCharBefore",Tab:"defaultTab","Shift-Tab":"indentAuto",Enter:"newlineAndIndent",Insert:"toggleOverwrite",Esc:"singleSelection"},Ha.pcDefault={"Ctrl-A":"selectAll","Ctrl-D":"deleteLine","Ctrl-Z":"undo","Shift-Ctrl-Z":"redo","Ctrl-Y":"redo","Ctrl-Home":"goDocStart","Ctrl-End":"goDocEnd","Ctrl-Up":"goLineUp","Ctrl-Down":"goLineDown","Ctrl-Left":"goGroupLeft","Ctrl-Right":"goGroupRight","Alt-Left":"goLineStart","Alt-Right":"goLineEnd","Ctrl-Backspace":"delGroupBefore","Ctrl-Delete":"delGroupAfter","Ctrl-S":"save","Ctrl-F":"find","Ctrl-G":"findNext","Shift-Ctrl-G":"findPrev","Shift-Ctrl-F":"replace","Shift-Ctrl-R":"replaceAll","Ctrl-[":"indentLess","Ctrl-]":"indentMore","Ctrl-U":"undoSelection","Shift-Ctrl-U":"redoSelection","Alt-U":"redoSelection",fallthrough:"basic"},Ha.emacsy={"Ctrl-F":"goCharRight","Ctrl-B":"goCharLeft","Ctrl-P":"goLineUp","Ctrl-N":"goLineDown","Ctrl-A":"goLineStart","Ctrl-E":"goLineEnd","Ctrl-V":"goPageDown","Shift-Ctrl-V":"goPageUp","Ctrl-D":"delCharAfter","Ctrl-H":"delCharBefore","Alt-Backspace":"delWordBefore","Ctrl-K":"killLine","Ctrl-T":"transposeChars","Ctrl-O":"openLine"},Ha.macDefault={"Cmd-A":"selectAll","Cmd-D":"deleteLine","Cmd-Z":"undo","Shift-Cmd-Z":"redo","Cmd-Y":"redo","Cmd-Home":"goDocStart","Cmd-Up":"goDocStart","Cmd-End":"goDocEnd","Cmd-Down":"goDocEnd","Alt-Left":"goGroupLeft","Alt-Right":"goGroupRight","Cmd-Left":"goLineLeft","Cmd-Right":"goLineRight","Alt-Backspace":"delGroupBefore","Ctrl-Alt-Backspace":"delGroupAfter","Alt-Delete":"delGroupAfter","Cmd-S":"save","Cmd-F":"find","Cmd-G":"findNext","Shift-Cmd-G":"findPrev","Cmd-Alt-F":"replace","Shift-Cmd-Alt-F":"replaceAll","Cmd-[":"indentLess","Cmd-]":"indentMore","Cmd-Backspace":"delWrappedLineLeft","Cmd-Delete":"delWrappedLineRight","Cmd-U":"undoSelection","Shift-Cmd-U":"redoSelection","Ctrl-Up":"goDocStart","Ctrl-Down":"goDocEnd",fallthrough:["basic","emacsy"]},Ha.default=wt?Ha.macDefault:Ha.pcDefault;var tl={selectAll:da,singleSelection:e=>e.setSelection(e.getCursor("anchor"),e.getCursor("head"),qt),killLine:e=>Ya(e,(t=>{if(t.empty()){let i=Xi(e.doc,t.head.line).text.length;return t.head.ch==i&&t.head.line<e.lastLine()?{from:t.head,to:sr(t.head.line+1,0)}:{from:t.head,to:sr(t.head.line,i)}}return{from:t.from(),to:t.to()}})),deleteLine:e=>Ya(e,(t=>({from:sr(t.from().line,0),to:ur(e.doc,sr(t.to().line+1,0))}))),delLineLeft:e=>Ya(e,(e=>({from:sr(e.from().line,0),to:e.from()}))),delWrappedLineLeft:e=>Ya(e,(t=>{let i=e.charCoords(t.head,"div").top+5;return{from:e.coordsChar({left:0,top:i},"div"),to:t.from()}})),delWrappedLineRight:e=>Ya(e,(t=>{let i=e.charCoords(t.head,"div").top+5,r=e.coordsChar({left:e.display.lineDiv.offsetWidth+100,top:i},"div");return{from:t.from(),to:r}})),undo:e=>e.undo(),redo:e=>e.redo(),undoSelection:e=>e.undoSelection(),redoSelection:e=>e.redoSelection(),goDocStart:e=>e.extendSelection(sr(e.firstLine(),0)),goDocEnd:e=>e.extendSelection(sr(e.lastLine())),goLineStart:e=>e.extendSelectionsBy((t=>il(e,t.head.line)),{origin:"+move",bias:1}),goLineStartSmart:e=>e.extendSelectionsBy((t=>rl(e,t.head)),{origin:"+move",bias:1}),goLineEnd:e=>e.extendSelectionsBy((t=>function(e,t){let i=Xi(e.doc,t),r=function(e){let t;for(;t=zr(e);)e=t.find(1,!0).line;return e}(i);r!=i&&(t=er(r));return el(!0,e,i,t,-1)}(e,t.head.line)),{origin:"+move",bias:-1}),goLineRight:e=>e.extendSelectionsBy((t=>{let i=e.cursorCoords(t.head,"div").top+5;return e.coordsChar({left:e.display.lineDiv.offsetWidth+100,top:i},"div")}),Kt),goLineLeft:e=>e.extendSelectionsBy((t=>{let i=e.cursorCoords(t.head,"div").top+5;return e.coordsChar({left:0,top:i},"div")}),Kt),goLineLeftSmart:e=>e.extendSelectionsBy((t=>{let i=e.cursorCoords(t.head,"div").top+5,r=e.coordsChar({left:0,top:i},"div");return r.ch<e.getLine(r.line).search(/\S/)?rl(e,t.head):r}),Kt),goLineUp:e=>e.moveV(-1,"line"),goLineDown:e=>e.moveV(1,"line"),goPageUp:e=>e.moveV(-1,"page"),goPageDown:e=>e.moveV(1,"page"),goCharLeft:e=>e.moveH(-1,"char"),goCharRight:e=>e.moveH(1,"char"),goColumnLeft:e=>e.moveH(-1,"column"),goColumnRight:e=>e.moveH(1,"column"),goWordLeft:e=>e.moveH(-1,"word"),goGroupRight:e=>e.moveH(1,"group"),goGroupLeft:e=>e.moveH(-1,"group"),goWordRight:e=>e.moveH(1,"word"),delCharBefore:e=>e.deleteH(-1,"codepoint"),delCharAfter:e=>e.deleteH(1,"char"),delWordBefore:e=>e.deleteH(-1,"word"),delWordAfter:e=>e.deleteH(1,"word"),delGroupBefore:e=>e.deleteH(-1,"group"),delGroupAfter:e=>e.deleteH(1,"group"),indentAuto:e=>e.indentSelection("smart"),indentMore:e=>e.indentSelection("add"),indentLess:e=>e.indentSelection("subtract"),insertTab:e=>e.replaceSelection("\t"),insertSoftTab:e=>{let t=[],i=e.listSelections(),r=e.options.tabSize;for(let s=0;s<i.length;s++){let o=i[s].from(),n=jt(e.getLine(o.line),o.ch,r);t.push(Jt(r-n%r))}e.replaceSelections(t)},defaultTab:e=>{e.somethingSelected()?e.indentSelection("add"):e.execCommand("insertTab")},transposeChars:e=>tn(e,(()=>{let t=e.listSelections(),i=[];for(let r=0;r<t.length;r++){if(!t[r].empty())continue;let s=t[r].head,o=Xi(e.doc,s.line).text;if(o)if(s.ch==o.length&&(s=new sr(s.line,s.ch-1)),s.ch>0)s=new sr(s.line,s.ch+1),e.replaceRange(o.charAt(s.ch-1)+o.charAt(s.ch-2),sr(s.line,s.ch-2),s,"+transpose");else if(s.line>e.doc.first){let t=Xi(e.doc,s.line-1).text;t&&(s=new sr(s.line,1),e.replaceRange(o.charAt(0)+e.doc.lineSeparator()+t.charAt(t.length-1),sr(s.line-1,t.length-1),s,"+transpose"))}i.push(new Tn(s,s))}e.setSelections(i)})),newlineAndIndent:e=>tn(e,(()=>{let t=e.listSelections();for(let i=t.length-1;i>=0;i--)e.replaceRange(e.doc.lineSeparator(),t[i].anchor,t[i].head,"+input");t=e.listSelections();for(let i=0;i<t.length;i++)e.indentLine(t[i].from().line,null,!0);No(e)})),openLine:e=>e.replaceSelection("\n","start"),toggleOverwrite:e=>e.toggleOverwrite()};function il(e,t){let i=Xi(e.doc,t),r=jr(i);return r!=i&&(t=er(r)),el(!0,e,r,t,1)}function rl(e,t){let i=il(e,t.line),r=Xi(e.doc,i.line),s=mi(r,e.doc.direction);if(!s||0==s[0].level){let e=Math.max(i.ch,r.text.search(/\S/)),s=t.line==i.line&&t.ch<=e&&t.ch;return sr(i.line,s?0:e,i.sticky)}return i}function sl(e,t,i){if("string"==typeof t&&!(t=tl[t]))return!1;e.display.input.ensurePolled();let r=e.display.shift,s=!1;try{e.isReadOnly()&&(e.state.suppressEdits=!0),i&&(e.display.shift=!1),s=t(e)!=Vt}finally{e.display.shift=r,e.state.suppressEdits=!1}return s}var ol=new Ht;function nl(e,t,i,r){let s=e.state.keySeq;if(s){if(qa(t))return"handled";if(/\'$/.test(t)?e.state.keySeq=null:ol.set(50,(()=>{e.state.keySeq==s&&(e.state.keySeq=null,e.display.input.reset())})),al(e,s+" "+t,i,r))return!0}return al(e,t,i,r)}function al(e,t,i,r){let s=function(e,t,i){for(let r=0;r<e.state.keyMaps.length;r++){let s=Va(t,e.state.keyMaps[r],i,e);if(s)return s}return e.options.extraKeys&&Va(t,e.options.extraKeys,i,e)||Va(t,e.options.keyMap,i,e)}(e,t,r);return"multi"==s&&(e.state.keySeq=t),"handled"==s&&us(e,"keyHandled",e,t,i),"handled"!=s&&"multi"!=s||(Ci(i),So(e)),!!s}function ll(e,t){let i=Ka(t,!0);return!!i&&(t.shiftKey&&!e.state.keySeq?nl(e,"Shift-"+i,t,(t=>sl(e,t,!0)))||nl(e,i,t,(t=>{if("string"==typeof t?/^go[A-Z]/.test(t):t.motion)return sl(e,t)})):nl(e,i,t,(t=>sl(e,t))))}var cl=null;function dl(e){let t=this;if(e.target&&e.target!=t.display.input.getField())return;if(t.curOp.focus=Dt(),yi(t,e))return;dt&&ut<11&&27==e.keyCode&&(e.returnValue=!1);let i=e.keyCode;t.display.shift=16==i||e.shiftKey;let r=ll(t,e);ft&&(cl=r?i:null,r||88!=i||Oi||!(wt?e.metaKey:e.ctrlKey)||t.replaceSelection("",null,"cut")),nt&&!wt&&!r&&46==i&&e.shiftKey&&!e.ctrlKey&&document.execCommand&&document.execCommand("cut"),18!=i||/\bCodeMirror-crosshair\b/.test(t.display.lineDiv.className)||function(e){let t=e.display.lineDiv;function i(e){18!=e.keyCode&&e.altKey||(Et(t,"CodeMirror-crosshair"),bi(document,"keyup",i),bi(document,"mouseover",i))}Ot(t,"CodeMirror-crosshair"),gi(document,"keyup",i),gi(document,"mouseover",i)}(t)}function ul(e){16==e.keyCode&&(this.doc.sel.shift=!1),yi(this,e)}function hl(e){let t=this;if(e.target&&e.target!=t.display.input.getField())return;if(Ss(t.display,e)||yi(t,e)||e.ctrlKey&&!e.altKey||wt&&e.metaKey)return;let i=e.keyCode,r=e.charCode;if(ft&&i==cl)return cl=null,void Ci(e);if(ft&&(!e.which||e.which<10)&&ll(t,e))return;let s=String.fromCharCode(null==r?i:r);"\b"!=s&&(function(e,t,i){return nl(e,"'"+i+"'",t,(t=>sl(e,t,!0)))}(t,e,s)||t.display.input.onKeyPress(e))}var pl,ml,fl=class{constructor(e,t,i){this.time=e,this.pos=t,this.button=i}compare(e,t,i){return this.time+400>e&&0==or(t,this.pos)&&i==this.button}};function gl(e){let t=this,i=t.display;if(yi(t,e)||i.activeTouch&&i.input.supportsTouch())return;if(i.input.ensurePolled(),i.shift=e.shiftKey,Ss(i,e))return void(ht||(i.scroller.draggable=!1,setTimeout((()=>i.scroller.draggable=!0),100)));if(_l(t,e))return;let r=po(t,e),s=$i(e),o=r?function(e,t){let i=+new Date;return ml&&ml.compare(i,e,t)?(pl=ml=null,"triple"):pl&&pl.compare(i,e,t)?(ml=new fl(i,e,t),pl=null,"double"):(pl=new fl(i,e,t),ml=null,"single")}(r,s):"single";window.focus(),1==s&&t.state.selectingText&&t.state.selectingText(e),r&&function(e,t,i,r,s){let o="Click";"double"==r?o="Double"+o:"triple"==r&&(o="Triple"+o);return o=(1==t?"Left":2==t?"Middle":"Right")+o,nl(e,Za(o,s),s,(t=>{if("string"==typeof t&&(t=tl[t]),!t)return!1;let r=!1;try{e.isReadOnly()&&(e.state.suppressEdits=!0),r=t(e,i)!=Vt}finally{e.state.suppressEdits=!1}return r}))}(t,s,r,o,e)||(1==s?r?function(e,t,i,r){dt?setTimeout(Wt(To,e),0):e.curOp.focus=Dt();let s,o=function(e,t,i){let r=e.getOption("configureMouse"),s=r?r(e,t,i):{};if(null==s.unit){let e=kt?i.shiftKey&&i.metaKey:i.altKey;s.unit=e?"rectangle":"single"==t?"char":"double"==t?"word":"line"}(null==s.extend||e.doc.extend)&&(s.extend=e.doc.extend||i.shiftKey);null==s.addNew&&(s.addNew=wt?i.metaKey:i.ctrlKey);null==s.moveOnDrag&&(s.moveOnDrag=!(wt?i.altKey:i.ctrlKey));return s}(e,i,r),n=e.doc.sel;e.options.dragDrop&&Ri&&!e.isReadOnly()&&"single"==i&&(s=n.contains(t))>-1&&(or((s=n.ranges[s]).from(),t)<0||t.xRel>0)&&(or(s.to(),t)>0||t.xRel<0)?function(e,t,i,r){let s=e.display,o=!1,n=rn(e,(t=>{ht&&(s.scroller.draggable=!1),e.state.draggingText=!1,e.state.delayingBlurEvent&&(e.hasFocus()?e.state.delayingBlurEvent=!1:Mo(e)),bi(s.wrapper.ownerDocument,"mouseup",n),bi(s.wrapper.ownerDocument,"mousemove",a),bi(s.scroller,"dragstart",l),bi(s.scroller,"drop",n),o||(Ci(t),r.addNew||Yn(e.doc,i,null,null,r.extend),ht&&!gt||dt&&9==ut?setTimeout((()=>{s.wrapper.ownerDocument.body.focus({preventScroll:!0}),s.input.focus()}),20):s.input.focus())})),a=function(e){o=o||Math.abs(t.clientX-e.clientX)+Math.abs(t.clientY-e.clientY)>=10},l=()=>o=!0;ht&&(s.scroller.draggable=!0);e.state.draggingText=n,n.copy=!r.moveOnDrag,gi(s.wrapper.ownerDocument,"mouseup",n),gi(s.wrapper.ownerDocument,"mousemove",a),gi(s.scroller,"dragstart",l),gi(s.scroller,"drop",n),e.state.delayingBlurEvent=!0,setTimeout((()=>s.input.focus()),20),s.scroller.dragDrop&&s.scroller.dragDrop()}(e,r,t,o):function(e,t,i,r){dt&&Mo(e);let s=e.display,o=e.doc;Ci(t);let n,a,l=o.sel,c=l.ranges;r.addNew&&!r.extend?(a=o.sel.contains(i),n=a>-1?c[a]:new Tn(i,i)):(n=o.sel.primary(),a=o.sel.primIndex);if("rectangle"==r.unit)r.addNew||(n=new Tn(i,i)),i=po(e,t,!0,!0),a=-1;else{let t=vl(e,i,r.unit);n=r.extend?Xn(n,t.anchor,t.head,r.extend):t}r.addNew?-1==a?(a=c.length,ia(o,Mn(e,c.concat([n]),a),{scroll:!1,origin:"*mouse"})):c.length>1&&c[a].empty()&&"char"==r.unit&&!r.extend?(ia(o,Mn(e,c.slice(0,a).concat(c.slice(a+1)),0),{scroll:!1,origin:"*mouse"}),l=o.sel):Qn(o,a,n,Zt):(a=0,ia(o,new Sn([n],0),Zt),l=o.sel);let d=i;function u(t){if(0!=or(d,t))if(d=t,"rectangle"==r.unit){let r=[],s=e.options.tabSize,n=jt(Xi(o,i.line).text,i.ch,s),c=jt(Xi(o,t.line).text,t.ch,s),d=Math.min(n,c),u=Math.max(n,c);for(let n=Math.min(i.line,t.line),a=Math.min(e.lastLine(),Math.max(i.line,t.line));n<=a;n++){let e=Xi(o,n).text,t=Xt(e,d,s);d==u?r.push(new Tn(sr(n,t),sr(n,t))):e.length>t&&r.push(new Tn(sr(n,t),sr(n,Xt(e,u,s))))}r.length||r.push(new Tn(i,i)),ia(o,Mn(e,l.ranges.slice(0,a).concat(r),a),{origin:"*mouse",scroll:!1}),e.scrollIntoView(t)}else{let i,s=n,c=vl(e,t,r.unit),d=s.anchor;or(c.anchor,d)>0?(i=c.head,d=cr(s.from(),c.anchor)):(i=c.anchor,d=lr(s.to(),c.head));let u=l.ranges.slice(0);u[a]=function(e,t){let{anchor:i,head:r}=t,s=Xi(e.doc,i.line);if(0==or(i,r)&&i.sticky==r.sticky)return t;let o=mi(s);if(!o)return t;let n=hi(o,i.ch,i.sticky),a=o[n];if(a.from!=i.ch&&a.to!=i.ch)return t;let l,c=n+(a.from==i.ch==(1!=a.level)?0:1);if(0==c||c==o.length)return t;if(r.line!=i.line)l=(r.line-i.line)*("ltr"==e.doc.direction?1:-1)>0;else{let e=hi(o,r.ch,r.sticky),t=e-n||(r.ch-i.ch)*(1==a.level?-1:1);l=e==c-1||e==c?t<0:t>0}let d=o[c+(l?-1:0)],u=l==(1==d.level),h=u?d.from:d.to,p=u?"after":"before";return i.ch==h&&i.sticky==p?t:new Tn(new sr(i.line,h,p),r)}(e,new Tn(ur(o,d),i)),ia(o,Mn(e,u,a),Zt)}}let h=s.wrapper.getBoundingClientRect(),p=0;function m(t){let i=++p,n=po(e,t,!0,"rectangle"==r.unit);if(n)if(0!=or(n,d)){e.curOp.focus=Dt(),u(n);let r=Ro(s,o);(n.line>=r.to||n.line<r.from)&&setTimeout(rn(e,(()=>{p==i&&m(t)})),150)}else{let r=t.clientY<h.top?-20:t.clientY>h.bottom?20:0;r&&setTimeout(rn(e,(()=>{p==i&&(s.scroller.scrollTop+=r,m(t))})),50)}}function f(t){e.state.selectingText=!1,p=1/0,t&&(Ci(t),s.input.focus()),bi(s.wrapper.ownerDocument,"mousemove",g),bi(s.wrapper.ownerDocument,"mouseup",v),o.history.lastSelOrigin=null}let g=rn(e,(e=>{0!==e.buttons&&$i(e)?m(e):f(e)})),v=rn(e,f);e.state.selectingText=v,gi(s.wrapper.ownerDocument,"mousemove",g),gi(s.wrapper.ownerDocument,"mouseup",v)}(e,r,t,o)}(t,r,o,e):Pi(e)==i.scroller&&Ci(e):2==s?(r&&Yn(t.doc,r),setTimeout((()=>i.input.focus()),20)):3==s&&(Mt?t.display.input.onContextMenu(e):Mo(t)))}function vl(e,t,i){if("char"==i)return new Tn(t,t);if("word"==i)return e.findWordAt(t);if("line"==i)return new Tn(sr(t.line,0),ur(e.doc,sr(t.line+1,0)));let r=i(e,t);return new Tn(r.from,r.to)}function bl(e,t,i,r){let s,o;if(t.touches)s=t.touches[0].clientX,o=t.touches[0].clientY;else try{s=t.clientX,o=t.clientY}catch(e){return!1}if(s>=Math.floor(e.display.gutters.getBoundingClientRect().right))return!1;r&&Ci(t);let n=e.display,a=n.lineDiv.getBoundingClientRect();if(o>a.bottom||!wi(e,i))return Ti(t);o-=a.top-n.viewOffset;for(let r=0;r<e.display.gutterSpecs.length;++r){let a=n.gutters.childNodes[r];if(a&&a.getBoundingClientRect().right>=s){return _i(e,i,e,tr(e.doc,o),e.display.gutterSpecs[r].className,t),Ti(t)}}}function _l(e,t){return bl(e,t,"gutterClick",!0)}function yl(e,t){Ss(e.display,t)||function(e,t){return!!wi(e,"gutterContextMenu")&&bl(e,t,"gutterContextMenu",!1)}(e,t)||yi(e,t,"contextmenu")||Mt||e.display.input.onContextMenu(t)}function xl(e){e.display.wrapper.className=e.display.wrapper.className.replace(/\s*cm-s-\S+/g,"")+e.options.theme.replace(/(^|\s)\s*/g," cm-s-"),Hs(e)}var wl={toString:function(){return"CodeMirror.Init"}},kl={},Cl={};function Sl(e,t,i){if(!t!=!(i&&i!=wl)){let i=e.display.dragFunctions,r=t?gi:bi;r(e.display.scroller,"dragstart",i.start),r(e.display.scroller,"dragenter",i.enter),r(e.display.scroller,"dragover",i.over),r(e.display.scroller,"dragleave",i.leave),r(e.display.scroller,"drop",i.drop)}}function Tl(e){e.options.lineWrapping?(Ot(e.display.wrapper,"CodeMirror-wrap"),e.display.sizer.style.minWidth="",e.display.sizerWidth=null):(Et(e.display.wrapper,"CodeMirror-wrap"),Kr(e)),ho(e),fo(e),Hs(e),setTimeout((()=>Ho(e)),100)}function Ml(e,t){if(!(this instanceof Ml))return new Ml(e,t);this.options=t=t?Bt(t):{},Bt(kl,t,!1);let i=t.value;"string"==typeof i?i=new Ia(i,t.mode,null,t.lineSeparator,t.direction):t.mode&&(i.modeOption=t.mode),this.doc=i;let r=new Ml.inputStyles[t.inputStyle](this),s=this.display=new _n(e,i,r,t);s.wrapper.CodeMirror=this,xl(this),t.lineWrapping&&(this.display.wrapper.className+=" CodeMirror-wrap"),Vo(this),this.state={keyMaps:[],overlays:[],modeGen:0,overwrite:!1,delayingBlurEvent:!1,focused:!1,suppressEdits:!1,pasteIncoming:-1,cutIncoming:-1,selectingText:!1,draggingText:!1,highlight:new Ht,keySeq:null,specialChars:null},t.autofocus&&!xt&&s.input.focus(),dt&&ut<11&&setTimeout((()=>this.display.input.reset(!0)),20),function(e){let t=e.display;gi(t.scroller,"mousedown",rn(e,gl)),gi(t.scroller,"dblclick",dt&&ut<11?rn(e,(t=>{if(yi(e,t))return;let i=po(e,t);if(!i||_l(e,t)||Ss(e.display,t))return;Ci(t);let r=e.findWordAt(i);Yn(e.doc,r.anchor,r.head)})):t=>yi(e,t)||Ci(t));gi(t.scroller,"contextmenu",(t=>yl(e,t))),gi(t.input.getField(),"contextmenu",(i=>{t.scroller.contains(i.target)||yl(e,i)}));let i,r={end:0};function s(){t.activeTouch&&(i=setTimeout((()=>t.activeTouch=null),1e3),r=t.activeTouch,r.end=+new Date)}function o(e){if(1!=e.touches.length)return!1;let t=e.touches[0];return t.radiusX<=1&&t.radiusY<=1}function n(e,t){if(null==t.left)return!0;let i=t.left-e.left,r=t.top-e.top;return i*i+r*r>400}gi(t.scroller,"touchstart",(s=>{if(!yi(e,s)&&!o(s)&&!_l(e,s)){t.input.ensurePolled(),clearTimeout(i);let e=+new Date;t.activeTouch={start:e,moved:!1,prev:e-r.end<=300?r:null},1==s.touches.length&&(t.activeTouch.left=s.touches[0].pageX,t.activeTouch.top=s.touches[0].pageY)}})),gi(t.scroller,"touchmove",(()=>{t.activeTouch&&(t.activeTouch.moved=!0)})),gi(t.scroller,"touchend",(i=>{let r=t.activeTouch;if(r&&!Ss(t,i)&&null!=r.left&&!r.moved&&new Date-r.start<300){let s,o=e.coordsChar(t.activeTouch,"page");s=!r.prev||n(r,r.prev)?new Tn(o,o):!r.prev.prev||n(r,r.prev.prev)?e.findWordAt(o):new Tn(sr(o.line,0),ur(e.doc,sr(o.line+1,0))),e.setSelection(s.anchor,s.head),e.focus(),Ci(i)}s()})),gi(t.scroller,"touchcancel",s),gi(t.scroller,"scroll",(()=>{t.scroller.clientHeight&&(zo(e,t.scroller.scrollTop),Bo(e,t.scroller.scrollLeft,!0),_i(e,"scroll",e))})),gi(t.scroller,"mousewheel",(t=>Cn(e,t))),gi(t.scroller,"DOMMouseScroll",(t=>Cn(e,t))),gi(t.wrapper,"scroll",(()=>t.wrapper.scrollTop=t.wrapper.scrollLeft=0)),t.dragFunctions={enter:t=>{yi(e,t)||Mi(t)},over:t=>{yi(e,t)||(!function(e,t){let i=po(e,t);if(!i)return;let r=document.createDocumentFragment();wo(e,i,r),e.display.dragCursor||(e.display.dragCursor=At("div",null,"CodeMirror-cursors CodeMirror-dragcursors"),e.display.lineSpace.insertBefore(e.display.dragCursor,e.display.cursorDiv)),Rt(e.display.dragCursor,r)}(e,t),Mi(t))},start:t=>function(e,t){if(dt&&(!e.state.draggingText||+new Date-Na<100))Mi(t);else if(!yi(e,t)&&!Ss(e.display,t)&&(t.dataTransfer.setData("Text",e.getSelection()),t.dataTransfer.effectAllowed="copyMove",t.dataTransfer.setDragImage&&!gt)){let i=At("img",null,null,"position: fixed; left: 0; top: 0;");i.src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==",ft&&(i.width=i.height=1,e.display.wrapper.appendChild(i),i._top=i.offsetTop),t.dataTransfer.setDragImage(i,0,0),ft&&i.parentNode.removeChild(i)}}(e,t),drop:rn(e,Da),leave:t=>{yi(e,t)||Oa(e)}};let a=t.input.getField();gi(a,"keyup",(t=>ul.call(e,t))),gi(a,"keydown",rn(e,dl)),gi(a,"keypress",rn(e,hl)),gi(a,"focus",(t=>Po(e,t))),gi(a,"blur",(t=>$o(e,t)))}(this),Wa(),Zo(this),this.curOp.forceUpdate=!0,Fn(this,i),t.autofocus&&!xt||this.hasFocus()?setTimeout((()=>{this.hasFocus()&&!this.state.focused&&Po(this)}),20):$o(this);for(let e in Cl)Cl.hasOwnProperty(e)&&Cl[e](this,t[e],wl);fn(this),t.finishInit&&t.finishInit(this);for(let e=0;e<$l.length;++e)$l[e](this);Ko(this),ht&&t.lineWrapping&&"optimizelegibility"==getComputedStyle(s.lineDiv).textRendering&&(s.lineDiv.style.textRendering="auto")}Ml.defaults=kl,Ml.optionHandlers=Cl;var Pl=Ml;var $l=[];function El(e,t,i,r){let s,o=e.doc;null==i&&(i="add"),"smart"==i&&(o.mode.indent?s=vr(e,t).state:i="prev");let n=e.options.tabSize,a=Xi(o,t),l=jt(a.text,null,n);a.stateAfter&&(a.stateAfter=null);let c,d=a.text.match(/^\s*/)[0];if(r||/\S/.test(a.text)){if("smart"==i&&(c=o.mode.indent(s,a.text.slice(d.length),a.text),c==Vt||c>150)){if(!r)return;i="prev"}}else c=0,i="not";"prev"==i?c=t>o.first?jt(Xi(o,t-1).text,null,n):0:"add"==i?c=l+e.options.indentUnit:"subtract"==i?c=l-e.options.indentUnit:"number"==typeof i&&(c=l+i),c=Math.max(0,c);let u="",h=0;if(e.options.indentWithTabs)for(let e=Math.floor(c/n);e;--e)h+=n,u+="\t";if(h<c&&(u+=Jt(c-h)),u!=d)return va(o,u,sr(t,0),sr(t,d.length),"+input"),a.stateAfter=null,!0;for(let e=0;e<o.sel.ranges.length;e++){let i=o.sel.ranges[e];if(i.head.line==t&&i.head.ch<d.length){let i=sr(t,d.length);Qn(o,e,new Tn(i,i));break}}}Ml.defineInitHook=e=>$l.push(e);var Ll=null;function Rl(e){Ll=e}function Al(e,t,i,r,s){let o=e.doc;e.display.shift=!1,r||(r=o.sel);let n=+new Date-200,a="paste"==s||e.state.pasteIncoming>n,l=Ni(t),c=null;if(a&&r.ranges.length>1)if(Ll&&Ll.text.join("\n")==t){if(r.ranges.length%Ll.text.length==0){c=[];for(let e=0;e<Ll.text.length;e++)c.push(o.splitLines(Ll.text[e]))}}else l.length==r.ranges.length&&e.options.pasteLinesPerSelection&&(c=ei(l,(e=>[e])));let d=e.curOp.updateInput;for(let t=r.ranges.length-1;t>=0;t--){let d=r.ranges[t],u=d.from(),h=d.to();d.empty()&&(i&&i>0?u=sr(u.line,u.ch-i):e.state.overwrite&&!a?h=sr(h.line,Math.min(Xi(o,h.line).text.length,h.ch+Qt(l).length)):a&&Ll&&Ll.lineWise&&Ll.text.join("\n")==l.join("\n")&&(u=h=sr(u.line,0)));let p={from:u,to:h,text:c?c[t%c.length]:l,origin:s||(a?"paste":e.state.cutIncoming>n?"cut":"+input")};ha(e.doc,p),us(e,"inputRead",e,p)}t&&!a&&Nl(e,t),No(e),e.curOp.updateInput<2&&(e.curOp.updateInput=d),e.curOp.typing=!0,e.state.pasteIncoming=e.state.cutIncoming=-1}function Il(e,t){let i=e.clipboardData&&e.clipboardData.getData("Text");if(i)return e.preventDefault(),t.isReadOnly()||t.options.disableInput||tn(t,(()=>Al(t,i,0,null,"paste"))),!0}function Nl(e,t){if(!e.options.electricChars||!e.options.smartIndent)return;let i=e.doc.sel;for(let r=i.ranges.length-1;r>=0;r--){let s=i.ranges[r];if(s.head.ch>100||r&&i.ranges[r-1].head.line==s.head.line)continue;let o=e.getModeAt(s.head),n=!1;if(o.electricChars){for(let i=0;i<o.electricChars.length;i++)if(t.indexOf(o.electricChars.charAt(i))>-1){n=El(e,s.head.line,"smart");break}}else o.electricInput&&o.electricInput.test(Xi(e.doc,s.head.line).text.slice(0,s.head.ch))&&(n=El(e,s.head.line,"smart"));n&&us(e,"electricInput",e,s.head.line)}}function Dl(e){let t=[],i=[];for(let r=0;r<e.doc.sel.ranges.length;r++){let s=e.doc.sel.ranges[r].head.line,o={anchor:sr(s,0),head:sr(s+1,0)};i.push(o),t.push(e.getRange(o.anchor,o.head))}return{text:t,ranges:i}}function Ol(e,t,i,r){e.setAttribute("autocorrect",i?"":"off"),e.setAttribute("autocapitalize",r?"":"off"),e.setAttribute("spellcheck",!!t)}function Fl(){let e=At("textarea",null,null,"position: absolute; bottom: -1em; padding: 0; width: 1px; height: 1em; outline: none"),t=At("div",[e],null,"overflow: hidden; position: relative; width: 3px; height: 0px;");return ht?e.style.width="1000px":e.setAttribute("wrap","off"),_t&&(e.style.border="1px solid black"),Ol(e),t}function zl(e,t,i,r,s){let o=t,n=i,a=Xi(e,t.line),l=s&&"rtl"==e.direction?-i:i;function c(o){let n;if("codepoint"==r){let e=a.text.charCodeAt(t.ch+(i>0?0:-1));if(isNaN(e))n=null;else{let r=i>0?e>=55296&&e<56320:e>=56320&&e<57343;n=new sr(t.line,Math.max(0,Math.min(a.text.length,t.ch+i*(r?2:1))),-i)}}else n=s?function(e,t,i,r){let s=mi(t,e.doc.direction);if(!s)return Qa(t,i,r);i.ch>=t.text.length?(i.ch=t.text.length,i.sticky="before"):i.ch<=0&&(i.ch=0,i.sticky="after");let o=hi(s,i.ch,i.sticky),n=s[o];if("ltr"==e.doc.direction&&n.level%2==0&&(r>0?n.to>i.ch:n.from<i.ch))return Qa(t,i,r);let a,l=(e,i)=>Ja(t,e instanceof sr?e.ch:e,i),c=i=>e.options.lineWrapping?(a=a||Ns(e,t),to(e,t,a,i)):{begin:0,end:t.text.length},d=c("before"==i.sticky?l(i,-1):i.ch);if("rtl"==e.doc.direction||1==n.level){let e=1==n.level==r<0,t=l(i,e?1:-1);if(null!=t&&(e?t<=n.to&&t<=d.end:t>=n.from&&t>=d.begin)){let r=e?"before":"after";return new sr(i.line,t,r)}}let u=(e,t,r)=>{let o=(e,t)=>t?new sr(i.line,l(e,1),"before"):new sr(i.line,e,"after");for(;e>=0&&e<s.length;e+=t){let i=s[e],n=t>0==(1!=i.level),a=n?r.begin:l(r.end,-1);if(i.from<=a&&a<i.to)return o(a,n);if(a=n?i.from:l(i.to,-1),r.begin<=a&&a<r.end)return o(a,n)}},h=u(o+r,r,d);if(h)return h;let p=r>0?d.end:l(d.begin,-1);return null==p||r>0&&p==t.text.length||(h=u(r>0?0:s.length-1,r,c(p)),!h)?null:h}(e.cm,a,t,i):Qa(a,t,i);if(null==n){if(o||!function(){let i=t.line+l;return!(i<e.first||i>=e.first+e.size)&&(t=new sr(i,t.ch,t.sticky),a=Xi(e,i))}())return!1;t=el(s,e.cm,a,t.line,l)}else t=n;return!0}if("char"==r||"codepoint"==r)c();else if("column"==r)c(!0);else if("word"==r||"group"==r){let s=null,o="group"==r,n=e.cm&&e.cm.getHelper(t,"wordChars");for(let e=!0;!(i<0)||c(!e);e=!1){let r=a.text.charAt(t.ch)||"\n",l=oi(r,n)?"w":o&&"\n"==r?"n":!o||/\s/.test(r)?null:"p";if(!o||e||l||(l="s"),s&&s!=l){i<0&&(i=1,c(),t.sticky="after");break}if(l&&(s=l),i>0&&!c(!e))break}}let d=la(e,t,o,n,!0);return nr(o,d)&&(d.hitSide=!0),d}function Wl(e,t,i,r){let s,o,n=e.doc,a=t.left;if("page"==r){let r=Math.min(e.display.wrapper.clientHeight,window.innerHeight||document.documentElement.clientHeight),o=Math.max(r-.5*no(e.display),3);s=(i>0?t.bottom:t.top)+i*o}else"line"==r&&(s=i>0?t.bottom+3:t.top-3);for(;o=Qs(e,a,s),o.outside;){if(i<0?s<=0:s>=n.height){o.hitSide=!0;break}s+=5*i}return o}var Bl=class{constructor(e){this.cm=e,this.lastAnchorNode=this.lastAnchorOffset=this.lastFocusNode=this.lastFocusOffset=null,this.polling=new Ht,this.composing=null,this.gracePeriod=!1,this.readDOMTimeout=null}init(e){let t=this,i=t.cm,r=t.div=e.lineDiv;function s(e){for(let t=e.target;t;t=t.parentNode){if(t==r)return!0;if(/\bCodeMirror-(?:line)?widget\b/.test(t.className))break}return!1}function o(e){if(!s(e)||yi(i,e))return;if(i.somethingSelected())Rl({lineWise:!1,text:i.getSelections()}),"cut"==e.type&&i.replaceSelection("",null,"cut");else{if(!i.options.lineWiseCopyCut)return;{let t=Dl(i);Rl({lineWise:!0,text:t.text}),"cut"==e.type&&i.operation((()=>{i.setSelections(t.ranges,0,qt),i.replaceSelection("",null,"cut")}))}}if(e.clipboardData){e.clipboardData.clearData();let t=Ll.text.join("\n");if(e.clipboardData.setData("Text",t),e.clipboardData.getData("Text")==t)return void e.preventDefault()}let o=Fl(),n=o.firstChild;i.display.lineSpace.insertBefore(o,i.display.lineSpace.firstChild),n.value=Ll.text.join("\n");let a=Dt();zt(n),setTimeout((()=>{i.display.lineSpace.removeChild(o),a.focus(),a==r&&t.showPrimarySelection()}),50)}r.contentEditable=!0,Ol(r,i.options.spellcheck,i.options.autocorrect,i.options.autocapitalize),gi(r,"paste",(e=>{!s(e)||yi(i,e)||Il(e,i)||ut<=11&&setTimeout(rn(i,(()=>this.updateFromDOM())),20)})),gi(r,"compositionstart",(e=>{this.composing={data:e.data,done:!1}})),gi(r,"compositionupdate",(e=>{this.composing||(this.composing={data:e.data,done:!1})})),gi(r,"compositionend",(e=>{this.composing&&(e.data!=this.composing.data&&this.readFromDOMSoon(),this.composing.done=!0)})),gi(r,"touchstart",(()=>t.forceCompositionEnd())),gi(r,"input",(()=>{this.composing||this.readFromDOMSoon()})),gi(r,"copy",o),gi(r,"cut",o)}screenReaderLabelChanged(e){e?this.div.setAttribute("aria-label",e):this.div.removeAttribute("aria-label")}prepareSelection(){let e=xo(this.cm,!1);return e.focus=Dt()==this.div,e}showSelection(e,t){e&&this.cm.display.view.length&&((e.focus||t)&&this.showPrimarySelection(),this.showMultipleSelections(e))}getSelection(){return this.cm.display.wrapper.ownerDocument.getSelection()}showPrimarySelection(){let e=this.getSelection(),t=this.cm,i=t.doc.sel.primary(),r=i.from(),s=i.to();if(t.display.viewTo==t.display.viewFrom||r.line>=t.display.viewTo||s.line<t.display.viewFrom)return void e.removeAllRanges();let o=Gl(t,e.anchorNode,e.anchorOffset),n=Gl(t,e.focusNode,e.focusOffset);if(o&&!o.bad&&n&&!n.bad&&0==or(cr(o,n),r)&&0==or(lr(o,n),s))return;let a=t.display.view,l=r.line>=t.display.viewFrom&&Hl(t,r)||{node:a[0].measure.map[2],offset:0},c=s.line<t.display.viewTo&&Hl(t,s);if(!c){let e=a[a.length-1].measure,t=e.maps?e.maps[e.maps.length-1]:e.map;c={node:t[t.length-1],offset:t[t.length-2]-t[t.length-3]}}if(!l||!c)return void e.removeAllRanges();let d,u=e.rangeCount&&e.getRangeAt(0);try{d=$t(l.node,l.offset,c.offset,c.node)}catch(e){}d&&(!nt&&t.state.focused?(e.collapse(l.node,l.offset),d.collapsed||(e.removeAllRanges(),e.addRange(d))):(e.removeAllRanges(),e.addRange(d)),u&&null==e.anchorNode?e.addRange(u):nt&&this.startGracePeriod()),this.rememberSelection()}startGracePeriod(){clearTimeout(this.gracePeriod),this.gracePeriod=setTimeout((()=>{this.gracePeriod=!1,this.selectionChanged()&&this.cm.operation((()=>this.cm.curOp.selectionChanged=!0))}),20)}showMultipleSelections(e){Rt(this.cm.display.cursorDiv,e.cursors),Rt(this.cm.display.selectionDiv,e.selection)}rememberSelection(){let e=this.getSelection();this.lastAnchorNode=e.anchorNode,this.lastAnchorOffset=e.anchorOffset,this.lastFocusNode=e.focusNode,this.lastFocusOffset=e.focusOffset}selectionInEditor(){let e=this.getSelection();if(!e.rangeCount)return!1;let t=e.getRangeAt(0).commonAncestorContainer;return Nt(this.div,t)}focus(){"nocursor"!=this.cm.options.readOnly&&(this.selectionInEditor()&&Dt()==this.div||this.showSelection(this.prepareSelection(),!0),this.div.focus())}blur(){this.div.blur()}getField(){return this.div}supportsTouch(){return!0}receivedFocus(){let e=this;this.selectionInEditor()?this.pollSelection():tn(this.cm,(()=>e.cm.curOp.selectionChanged=!0)),this.polling.set(this.cm.options.pollInterval,(function t(){e.cm.state.focused&&(e.pollSelection(),e.polling.set(e.cm.options.pollInterval,t))}))}selectionChanged(){let e=this.getSelection();return e.anchorNode!=this.lastAnchorNode||e.anchorOffset!=this.lastAnchorOffset||e.focusNode!=this.lastFocusNode||e.focusOffset!=this.lastFocusOffset}pollSelection(){if(null!=this.readDOMTimeout||this.gracePeriod||!this.selectionChanged())return;let e=this.getSelection(),t=this.cm;if(yt&&mt&&this.cm.display.gutterSpecs.length&&function(e){for(let t=e;t;t=t.parentNode)if(/CodeMirror-gutter-wrapper/.test(t.className))return!0;return!1}(e.anchorNode))return this.cm.triggerOnKeyDown({type:"keydown",keyCode:8,preventDefault:Math.abs}),this.blur(),void this.focus();if(this.composing)return;this.rememberSelection();let i=Gl(t,e.anchorNode,e.anchorOffset),r=Gl(t,e.focusNode,e.focusOffset);i&&r&&tn(t,(()=>{ia(t.doc,Pn(i,r),qt),(i.bad||r.bad)&&(t.curOp.selectionChanged=!0)}))}pollContent(){null!=this.readDOMTimeout&&(clearTimeout(this.readDOMTimeout),this.readDOMTimeout=null);let e,t,i,r=this.cm,s=r.display,o=r.doc.sel.primary(),n=o.from(),a=o.to();if(0==n.ch&&n.line>r.firstLine()&&(n=sr(n.line-1,Xi(r.doc,n.line-1).length)),a.ch==Xi(r.doc,a.line).text.length&&a.line<r.lastLine()&&(a=sr(a.line+1,0)),n.line<s.viewFrom||a.line>s.viewTo-1)return!1;n.line==s.viewFrom||0==(e=mo(r,n.line))?(t=er(s.view[0].line),i=s.view[0].node):(t=er(s.view[e].line),i=s.view[e-1].node.nextSibling);let l,c,d=mo(r,a.line);if(d==s.view.length-1?(l=s.viewTo-1,c=s.lineDiv.lastChild):(l=er(s.view[d+1].line)-1,c=s.view[d+1].node.previousSibling),!i)return!1;let u=r.doc.splitLines(function(e,t,i,r,s){let o="",n=!1,a=e.doc.lineSeparator(),l=!1;function c(e){return t=>t.id==e}function d(){n&&(o+=a,l&&(o+=a),n=l=!1)}function u(e){e&&(d(),o+=e)}function h(t){if(1==t.nodeType){let i=t.getAttribute("cm-text");if(i)return void u(i);let o,p=t.getAttribute("cm-marker");if(p){let t=e.findMarks(sr(r,0),sr(s+1,0),c(+p));return void(t.length&&(o=t[0].find(0))&&u(Yi(e.doc,o.from,o.to).join(a)))}if("false"==t.getAttribute("contenteditable"))return;let m=/^(pre|div|p|li|table|br)$/i.test(t.nodeName);if(!/^br$/i.test(t.nodeName)&&0==t.textContent.length)return;m&&d();for(let e=0;e<t.childNodes.length;e++)h(t.childNodes[e]);/^(pre|p)$/i.test(t.nodeName)&&(l=!0),m&&(n=!0)}else 3==t.nodeType&&u(t.nodeValue.replace(/\u200b/g,"").replace(/\u00a0/g," "))}for(;h(t),t!=i;)t=t.nextSibling,l=!1;return o}(r,i,c,t,l)),h=Yi(r.doc,sr(t,0),sr(l,Xi(r.doc,l).text.length));for(;u.length>1&&h.length>1;)if(Qt(u)==Qt(h))u.pop(),h.pop(),l--;else{if(u[0]!=h[0])break;u.shift(),h.shift(),t++}let p=0,m=0,f=u[0],g=h[0],v=Math.min(f.length,g.length);for(;p<v&&f.charCodeAt(p)==g.charCodeAt(p);)++p;let b=Qt(u),_=Qt(h),y=Math.min(b.length-(1==u.length?p:0),_.length-(1==h.length?p:0));for(;m<y&&b.charCodeAt(b.length-m-1)==_.charCodeAt(_.length-m-1);)++m;if(1==u.length&&1==h.length&&t==n.line)for(;p&&p>n.ch&&b.charCodeAt(b.length-m-1)==_.charCodeAt(_.length-m-1);)p--,m++;u[u.length-1]=b.slice(0,b.length-m).replace(/^\u200b+/,""),u[0]=u[0].slice(p).replace(/\u200b+$/,"");let x=sr(t,p),w=sr(l,h.length?Qt(h).length-m:0);return u.length>1||u[0]||or(x,w)?(va(r.doc,u,x,w,"+input"),!0):void 0}ensurePolled(){this.forceCompositionEnd()}reset(){this.forceCompositionEnd()}forceCompositionEnd(){this.composing&&(clearTimeout(this.readDOMTimeout),this.composing=null,this.updateFromDOM(),this.div.blur(),this.div.focus())}readFromDOMSoon(){null==this.readDOMTimeout&&(this.readDOMTimeout=setTimeout((()=>{if(this.readDOMTimeout=null,this.composing){if(!this.composing.done)return;this.composing=null}this.updateFromDOM()}),80))}updateFromDOM(){!this.cm.isReadOnly()&&this.pollContent()||tn(this.cm,(()=>fo(this.cm)))}setUneditable(e){e.contentEditable="false"}onKeyPress(e){0==e.charCode||this.composing||(e.preventDefault(),this.cm.isReadOnly()||rn(this.cm,Al)(this.cm,String.fromCharCode(null==e.charCode?e.keyCode:e.charCode),0))}readOnlyChanged(e){this.div.contentEditable=String("nocursor"!=e)}onContextMenu(){}resetPosition(){}},jl=Bl;function Hl(e,t){let i=Is(e,t.line);if(!i||i.hidden)return null;let r=Xi(e.doc,t.line),s=Rs(i,r,t.line),o=mi(r,e.doc.direction),n="left";if(o){n=hi(o,t.ch)%2?"right":"left"}let a=zs(s.map,t.ch,n);return a.offset="right"==a.collapse?a.end:a.start,a}function Ul(e,t){return t&&(e.bad=!0),e}function Gl(e,t,i){let r;if(t==e.display.lineDiv){if(r=e.display.lineDiv.childNodes[i],!r)return Ul(e.clipPos(sr(e.display.viewTo-1)),!0);t=null,i=0}else for(r=t;;r=r.parentNode){if(!r||r==e.display.lineDiv)return null;if(r.parentNode&&r.parentNode==e.display.lineDiv)break}for(let s=0;s<e.display.view.length;s++){let o=e.display.view[s];if(o.node==r)return Vl(o,t,i)}}function Vl(e,t,i){let r=e.text.firstChild,s=!1;if(!t||!Nt(r,t))return Ul(sr(er(e.line),0),!0);if(t==r&&(s=!0,t=r.childNodes[i],i=0,!t)){let t=e.rest?Qt(e.rest):e.line;return Ul(sr(er(t),t.text.length),s)}let o=3==t.nodeType?t:null,n=t;for(o||1!=t.childNodes.length||3!=t.firstChild.nodeType||(o=t.firstChild,i&&(i=o.nodeValue.length));n.parentNode!=r;)n=n.parentNode;let a=e.measure,l=a.maps;function c(t,i,r){for(let s=-1;s<(l?l.length:0);s++){let o=s<0?a.map:l[s];for(let n=0;n<o.length;n+=3){let a=o[n+2];if(a==t||a==i){let i=er(s<0?e.line:e.rest[s]),l=o[n]+r;return(r<0||a!=t)&&(l=o[n+(r?1:0)]),sr(i,l)}}}}let d=c(o,n,i);if(d)return Ul(d,s);for(let e=n.nextSibling,t=o?o.nodeValue.length-i:0;e;e=e.nextSibling){if(d=c(e,e.firstChild,0),d)return Ul(sr(d.line,d.ch-t),s);t+=e.textContent.length}for(let e=n.previousSibling,t=i;e;e=e.previousSibling){if(d=c(e,e.firstChild,-1),d)return Ul(sr(d.line,d.ch+t),s);t+=e.textContent.length}}Bl.prototype.needsContentAttribute=!0;var ql=class{constructor(e){this.cm=e,this.prevInput="",this.pollingFast=!1,this.polling=new Ht,this.hasSelection=!1,this.composing=null}init(e){let t=this,i=this.cm;this.createField(e);const r=this.textarea;function s(e){if(!yi(i,e)){if(i.somethingSelected())Rl({lineWise:!1,text:i.getSelections()});else{if(!i.options.lineWiseCopyCut)return;{let s=Dl(i);Rl({lineWise:!0,text:s.text}),"cut"==e.type?i.setSelections(s.ranges,null,qt):(t.prevInput="",r.value=s.text.join("\n"),zt(r))}}"cut"==e.type&&(i.state.cutIncoming=+new Date)}}e.wrapper.insertBefore(this.wrapper,e.wrapper.firstChild),_t&&(r.style.width="0px"),gi(r,"input",(()=>{dt&&ut>=9&&this.hasSelection&&(this.hasSelection=null),t.poll()})),gi(r,"paste",(e=>{yi(i,e)||Il(e,i)||(i.state.pasteIncoming=+new Date,t.fastPoll())})),gi(r,"cut",s),gi(r,"copy",s),gi(e.scroller,"paste",(s=>{if(Ss(e,s)||yi(i,s))return;if(!r.dispatchEvent)return i.state.pasteIncoming=+new Date,void t.focus();const o=new Event("paste");o.clipboardData=s.clipboardData,r.dispatchEvent(o)})),gi(e.lineSpace,"selectstart",(t=>{Ss(e,t)||Ci(t)})),gi(r,"compositionstart",(()=>{let e=i.getCursor("from");t.composing&&t.composing.range.clear(),t.composing={start:e,range:i.markText(e,i.getCursor("to"),{className:"CodeMirror-composing"})}})),gi(r,"compositionend",(()=>{t.composing&&(t.poll(),t.composing.range.clear(),t.composing=null)}))}createField(e){this.wrapper=Fl(),this.textarea=this.wrapper.firstChild}screenReaderLabelChanged(e){e?this.textarea.setAttribute("aria-label",e):this.textarea.removeAttribute("aria-label")}prepareSelection(){let e=this.cm,t=e.display,i=e.doc,r=xo(e);if(e.options.moveInputWithCursor){let s=Xs(e,i.sel.primary().head,"div"),o=t.wrapper.getBoundingClientRect(),n=t.lineDiv.getBoundingClientRect();r.teTop=Math.max(0,Math.min(t.wrapper.clientHeight-10,s.top+n.top-o.top)),r.teLeft=Math.max(0,Math.min(t.wrapper.clientWidth-10,s.left+n.left-o.left))}return r}showSelection(e){let t=this.cm.display;Rt(t.cursorDiv,e.cursors),Rt(t.selectionDiv,e.selection),null!=e.teTop&&(this.wrapper.style.top=e.teTop+"px",this.wrapper.style.left=e.teLeft+"px")}reset(e){if(this.contextMenuPending||this.composing)return;let t=this.cm;if(t.somethingSelected()){this.prevInput="";let e=t.getSelection();this.textarea.value=e,t.state.focused&&zt(this.textarea),dt&&ut>=9&&(this.hasSelection=e)}else e||(this.prevInput=this.textarea.value="",dt&&ut>=9&&(this.hasSelection=null))}getField(){return this.textarea}supportsTouch(){return!1}focus(){if("nocursor"!=this.cm.options.readOnly&&(!xt||Dt()!=this.textarea))try{this.textarea.focus()}catch(e){}}blur(){this.textarea.blur()}resetPosition(){this.wrapper.style.top=this.wrapper.style.left=0}receivedFocus(){this.slowPoll()}slowPoll(){this.pollingFast||this.polling.set(this.cm.options.pollInterval,(()=>{this.poll(),this.cm.state.focused&&this.slowPoll()}))}fastPoll(){let e=!1,t=this;t.pollingFast=!0,t.polling.set(20,(function i(){t.poll()||e?(t.pollingFast=!1,t.slowPoll()):(e=!0,t.polling.set(60,i))}))}poll(){let e=this.cm,t=this.textarea,i=this.prevInput;if(this.contextMenuPending||!e.state.focused||Di(t)&&!i&&!this.composing||e.isReadOnly()||e.options.disableInput||e.state.keySeq)return!1;let r=t.value;if(r==i&&!e.somethingSelected())return!1;if(dt&&ut>=9&&this.hasSelection===r||wt&&/[\uf700-\uf7ff]/.test(r))return e.display.input.reset(),!1;if(e.doc.sel==e.display.selForContextMenu){let e=r.charCodeAt(0);if(8203!=e||i||(i="​"),8666==e)return this.reset(),this.cm.execCommand("undo")}let s=0,o=Math.min(i.length,r.length);for(;s<o&&i.charCodeAt(s)==r.charCodeAt(s);)++s;return tn(e,(()=>{Al(e,r.slice(s),i.length-s,null,this.composing?"*compose":null),r.length>1e3||r.indexOf("\n")>-1?t.value=this.prevInput="":this.prevInput=r,this.composing&&(this.composing.range.clear(),this.composing.range=e.markText(this.composing.start,e.getCursor("to"),{className:"CodeMirror-composing"}))})),!0}ensurePolled(){this.pollingFast&&this.poll()&&(this.pollingFast=!1)}onKeyPress(){dt&&ut>=9&&(this.hasSelection=null),this.fastPoll()}onContextMenu(e){let t=this,i=t.cm,r=i.display,s=t.textarea;t.contextMenuPending&&t.contextMenuPending();let o=po(i,e),n=r.scroller.scrollTop;if(!o||ft)return;i.options.resetSelectionOnContextMenu&&-1==i.doc.sel.contains(o)&&rn(i,ia)(i.doc,Pn(o),qt);let a,l=s.style.cssText,c=t.wrapper.style.cssText,d=t.wrapper.offsetParent.getBoundingClientRect();function u(){if(null!=s.selectionStart){let e=i.somethingSelected(),o="​"+(e?s.value:"");s.value="⇚",s.value=o,t.prevInput=e?"":"​",s.selectionStart=1,s.selectionEnd=o.length,r.selForContextMenu=i.doc.sel}}function h(){if(t.contextMenuPending==h&&(t.contextMenuPending=!1,t.wrapper.style.cssText=c,s.style.cssText=l,dt&&ut<9&&r.scrollbars.setScrollTop(r.scroller.scrollTop=n),null!=s.selectionStart)){(!dt||dt&&ut<9)&&u();let e=0,o=()=>{r.selForContextMenu==i.doc.sel&&0==s.selectionStart&&s.selectionEnd>0&&"​"==t.prevInput?rn(i,da)(i):e++<10?r.detectingSelectAll=setTimeout(o,500):(r.selForContextMenu=null,r.input.reset())};r.detectingSelectAll=setTimeout(o,200)}}if(t.wrapper.style.cssText="position: static",s.style.cssText=`position: absolute; width: 30px; height: 30px;\n      top: ${e.clientY-d.top-5}px; left: ${e.clientX-d.left-5}px;\n      z-index: 1000; background: ${dt?"rgba(255, 255, 255, .05)":"transparent"};\n      outline: none; border-width: 0; outline: none; overflow: hidden; opacity: .05; filter: alpha(opacity=5);`,ht&&(a=window.scrollY),r.input.focus(),ht&&window.scrollTo(null,a),r.input.reset(),i.somethingSelected()||(s.value=t.prevInput=" "),t.contextMenuPending=h,r.selForContextMenu=i.doc.sel,clearTimeout(r.detectingSelectAll),dt&&ut>=9&&u(),Mt){Mi(e);let t=()=>{bi(window,"mouseup",t),setTimeout(h,20)};gi(window,"mouseup",t)}else setTimeout(h,50)}readOnlyChanged(e){e||this.reset(),this.textarea.disabled="nocursor"==e,this.textarea.readOnly=!!e}setUneditable(){}},Zl=ql;ql.prototype.needsContentAttribute=!1,function(e){let t=e.optionHandlers;function i(i,r,s,o){e.defaults[i]=r,s&&(t[i]=o?(e,t,i)=>{i!=wl&&s(e,t,i)}:s)}e.defineOption=i,e.Init=wl,i("value","",((e,t)=>e.setValue(t)),!0),i("mode",null,((e,t)=>{e.doc.modeOption=t,An(e)}),!0),i("indentUnit",2,An,!0),i("indentWithTabs",!1),i("smartIndent",!0),i("tabSize",4,(e=>{In(e),Hs(e),fo(e)}),!0),i("lineSeparator",null,((e,t)=>{if(e.doc.lineSep=t,!t)return;let i=[],r=e.doc.first;e.doc.iter((e=>{for(let s=0;;){let o=e.text.indexOf(t,s);if(-1==o)break;s=o+t.length,i.push(sr(r,o))}r++}));for(let r=i.length-1;r>=0;r--)va(e.doc,t,i[r],sr(i[r].line,i[r].ch+t.length))})),i("specialChars",/[\u0000-\u001f\u007f-\u009f\u00ad\u061c\u200b\u200e\u200f\u2028\u2029\ufeff\ufff9-\ufffc]/g,((e,t,i)=>{e.state.specialChars=new RegExp(t.source+(t.test("\t")?"":"|\t"),"g"),i!=wl&&e.refresh()})),i("specialCharPlaceholder",is,(e=>e.refresh()),!0),i("electricChars",!0),i("inputStyle",xt?"contenteditable":"textarea",(()=>{throw new Error("inputStyle can not (yet) be changed in a running editor")}),!0),i("spellcheck",!1,((e,t)=>e.getInputField().spellcheck=t),!0),i("autocorrect",!1,((e,t)=>e.getInputField().autocorrect=t),!0),i("autocapitalize",!1,((e,t)=>e.getInputField().autocapitalize=t),!0),i("rtlMoveVisually",!Ct),i("wholeLineUpdateBefore",!0),i("theme","default",(e=>{xl(e),bn(e)}),!0),i("keyMap","default",((e,t,i)=>{let r=Xa(t),s=i!=wl&&Xa(i);s&&s.detach&&s.detach(e,r),r.attach&&r.attach(e,s||null)})),i("extraKeys",null),i("configureMouse",null),i("lineWrapping",!1,Tl,!0),i("gutters",[],((e,t)=>{e.display.gutterSpecs=gn(t,e.options.lineNumbers),bn(e)}),!0),i("fixedGutter",!0,((e,t)=>{e.display.gutters.style.left=t?co(e.display)+"px":"0",e.refresh()}),!0),i("coverGutterNextToScrollbar",!1,(e=>Ho(e)),!0),i("scrollbarStyle","native",(e=>{Vo(e),Ho(e),e.display.scrollbars.setScrollTop(e.doc.scrollTop),e.display.scrollbars.setScrollLeft(e.doc.scrollLeft)}),!0),i("lineNumbers",!1,((e,t)=>{e.display.gutterSpecs=gn(e.options.gutters,t),bn(e)}),!0),i("firstLineNumber",1,bn,!0),i("lineNumberFormatter",(e=>e),bn,!0),i("showCursorWhenSelecting",!1,yo,!0),i("resetSelectionOnContextMenu",!0),i("lineWiseCopyCut",!0),i("pasteLinesPerSelection",!0),i("selectionsMayTouch",!1),i("readOnly",!1,((e,t)=>{"nocursor"==t&&($o(e),e.display.input.blur()),e.display.input.readOnlyChanged(t)})),i("screenReaderLabel",null,((e,t)=>{t=""===t?null:t,e.display.input.screenReaderLabelChanged(t)})),i("disableInput",!1,((e,t)=>{t||e.display.input.reset()}),!0),i("dragDrop",!0,Sl),i("allowDropFileTypes",null),i("cursorBlinkRate",530),i("cursorScrollMargin",0),i("cursorHeight",1,yo,!0),i("singleCursorHeightPerLine",!0,yo,!0),i("workTime",100),i("workDelay",100),i("flattenSpans",!0,In,!0),i("addModeClass",!1,In,!0),i("pollInterval",100),i("undoDepth",200,((e,t)=>e.doc.history.undoDepth=t)),i("historyEventDelay",1250),i("viewportMargin",10,(e=>e.refresh()),!0),i("maxHighlightLength",1e4,In,!0),i("moveInputWithCursor",!0,((e,t)=>{t||e.display.input.resetPosition()})),i("tabindex",null,((e,t)=>e.display.input.getField().tabIndex=t||"")),i("autofocus",null),i("direction","ltr",((e,t)=>e.doc.setDirection(t)),!0),i("phrases",null)}(Ml),function(e){let t=e.optionHandlers,i=e.helpers={};e.prototype={constructor:e,focus:function(){window.focus(),this.display.input.focus()},setOption:function(e,i){let r=this.options,s=r[e];r[e]==i&&"mode"!=e||(r[e]=i,t.hasOwnProperty(e)&&rn(this,t[e])(this,i,s),_i(this,"optionChange",this,e))},getOption:function(e){return this.options[e]},getDoc:function(){return this.doc},addKeyMap:function(e,t){this.state.keyMaps[t?"push":"unshift"](Xa(e))},removeKeyMap:function(e){let t=this.state.keyMaps;for(let i=0;i<t.length;++i)if(t[i]==e||t[i].name==e)return t.splice(i,1),!0},addOverlay:sn((function(t,i){let r=t.token?t:e.getMode(this.options,t);if(r.startState)throw new Error("Overlays may not be stateful.");!function(e,t,i){let r=0,s=i(t);for(;r<e.length&&i(e[r])<=s;)r++;e.splice(r,0,t)}(this.state.overlays,{mode:r,modeSpec:t,opaque:i&&i.opaque,priority:i&&i.priority||0},(e=>e.priority)),this.state.modeGen++,fo(this)})),removeOverlay:sn((function(e){let t=this.state.overlays;for(let i=0;i<t.length;++i){let r=t[i].modeSpec;if(r==e||"string"==typeof e&&r.name==e)return t.splice(i,1),this.state.modeGen++,void fo(this)}})),indentLine:sn((function(e,t,i){"string"!=typeof t&&"number"!=typeof t&&(t=null==t?this.options.smartIndent?"smart":"prev":t?"add":"subtract"),ir(this.doc,e)&&El(this,e,t,i)})),indentSelection:sn((function(e){let t=this.doc.sel.ranges,i=-1;for(let r=0;r<t.length;r++){let s=t[r];if(s.empty())s.head.line>i&&(El(this,s.head.line,e,!0),i=s.head.line,r==this.doc.sel.primIndex&&No(this));else{let o=s.from(),n=s.to(),a=Math.max(i,o.line);i=Math.min(this.lastLine(),n.line-(n.ch?0:1))+1;for(let t=a;t<i;++t)El(this,t,e);let l=this.doc.sel.ranges;0==o.ch&&t.length==l.length&&l[r].from().ch>0&&Qn(this.doc,r,new Tn(o,l[r].to()),qt)}}})),getTokenAt:function(e,t){return wr(this,e,t)},getLineTokens:function(e,t){return wr(this,sr(e),t,!0)},getTokenTypeAt:function(e){e=ur(this.doc,e);let t,i=gr(this,Xi(this.doc,e.line)),r=0,s=(i.length-1)/2,o=e.ch;if(0==o)t=i[2];else for(;;){let e=r+s>>1;if((e?i[2*e-1]:0)>=o)s=e;else{if(!(i[2*e+1]<o)){t=i[2*e+2];break}r=e+1}}let n=t?t.indexOf("overlay "):-1;return n<0?t:0==n?null:t.slice(0,n-1)},getModeAt:function(t){let i=this.doc.mode;return i.innerMode?e.innerMode(i,this.getTokenAt(t).state).mode:i},getHelper:function(e,t){return this.getHelpers(e,t)[0]},getHelpers:function(e,t){let r=[];if(!i.hasOwnProperty(t))return r;let s=i[t],o=this.getModeAt(e);if("string"==typeof o[t])s[o[t]]&&r.push(s[o[t]]);else if(o[t])for(let e=0;e<o[t].length;e++){let i=s[o[t][e]];i&&r.push(i)}else o.helperType&&s[o.helperType]?r.push(s[o.helperType]):s[o.name]&&r.push(s[o.name]);for(let e=0;e<s._global.length;e++){let t=s._global[e];t.pred(o,this)&&-1==Ut(r,t.val)&&r.push(t.val)}return r},getStateAfter:function(e,t){let i=this.doc;return vr(this,(e=dr(i,null==e?i.first+i.size-1:e))+1,t).state},cursorCoords:function(e,t){let i,r=this.doc.sel.primary();return i=null==e?r.head:"object"==typeof e?ur(this.doc,e):e?r.from():r.to(),Xs(this,i,t||"page")},charCoords:function(e,t){return Ks(this,ur(this.doc,e),t||"page")},coordsChar:function(e,t){return Qs(this,(e=Zs(this,e,t||"page")).left,e.top)},lineAtHeight:function(e,t){return e=Zs(this,{top:e,left:0},t||"page").top,tr(this.doc,e+this.display.viewOffset)},heightAtLine:function(e,t,i){let r,s=!1;if("number"==typeof e){let t=this.doc.first+this.doc.size-1;e<this.doc.first?e=this.doc.first:e>t&&(e=t,s=!0),r=Xi(this.doc,e)}else r=e;return qs(this,r,{top:0,left:0},t||"page",i||s).top+(s?this.doc.height-qr(r):0)},defaultTextHeight:function(){return no(this.display)},defaultCharWidth:function(){return ao(this.display)},getViewport:function(){return{from:this.display.viewFrom,to:this.display.viewTo}},addWidget:function(e,t,i,r,s){let o=this.display,n=(e=Xs(this,ur(this.doc,e))).bottom,a=e.left;if(t.style.position="absolute",t.setAttribute("cm-ignore-events","true"),this.display.input.setUneditable(t),o.sizer.appendChild(t),"over"==r)n=e.top;else if("above"==r||"near"==r){let i=Math.max(o.wrapper.clientHeight,this.doc.height),s=Math.max(o.sizer.clientWidth,o.lineSpace.clientWidth);("above"==r||e.bottom+t.offsetHeight>i)&&e.top>t.offsetHeight?n=e.top-t.offsetHeight:e.bottom+t.offsetHeight<=i&&(n=e.bottom),a+t.offsetWidth>s&&(a=s-t.offsetWidth)}t.style.top=n+"px",t.style.left=t.style.right="","right"==s?(a=o.sizer.clientWidth-t.offsetWidth,t.style.right="0px"):("left"==s?a=0:"middle"==s&&(a=(o.sizer.clientWidth-t.offsetWidth)/2),t.style.left=a+"px"),i&&function(e,t){let i=Ao(e,t);null!=i.scrollTop&&zo(e,i.scrollTop),null!=i.scrollLeft&&Bo(e,i.scrollLeft)}(this,{left:a,top:n,right:a+t.offsetWidth,bottom:n+t.offsetHeight})},triggerOnKeyDown:sn(dl),triggerOnKeyPress:sn(hl),triggerOnKeyUp:ul,triggerOnMouseDown:sn(gl),execCommand:function(e){if(tl.hasOwnProperty(e))return tl[e].call(null,this)},triggerElectric:sn((function(e){Nl(this,e)})),findPosH:function(e,t,i,r){let s=1;t<0&&(s=-1,t=-t);let o=ur(this.doc,e);for(let e=0;e<t&&(o=zl(this.doc,o,s,i,r),!o.hitSide);++e);return o},moveH:sn((function(e,t){this.extendSelectionsBy((i=>this.display.shift||this.doc.extend||i.empty()?zl(this.doc,i.head,e,t,this.options.rtlMoveVisually):e<0?i.from():i.to()),Kt)})),deleteH:sn((function(e,t){let i=this.doc.sel,r=this.doc;i.somethingSelected()?r.replaceSelection("",null,"+delete"):Ya(this,(i=>{let s=zl(r,i.head,e,t,!1);return e<0?{from:s,to:i.head}:{from:i.head,to:s}}))})),findPosV:function(e,t,i,r){let s=1,o=r;t<0&&(s=-1,t=-t);let n=ur(this.doc,e);for(let e=0;e<t;++e){let e=Xs(this,n,"div");if(null==o?o=e.left:e.left=o,n=Wl(this,e,s,i),n.hitSide)break}return n},moveV:sn((function(e,t){let i=this.doc,r=[],s=!this.display.shift&&!i.extend&&i.sel.somethingSelected();if(i.extendSelectionsBy((o=>{if(s)return e<0?o.from():o.to();let n=Xs(this,o.head,"div");null!=o.goalColumn&&(n.left=o.goalColumn),r.push(n.left);let a=Wl(this,n,e,t);return"page"==t&&o==i.sel.primary()&&Io(this,Ks(this,a,"div").top-n.top),a}),Kt),r.length)for(let e=0;e<i.sel.ranges.length;e++)i.sel.ranges[e].goalColumn=r[e]})),findWordAt:function(e){let t=Xi(this.doc,e.line).text,i=e.ch,r=e.ch;if(t){let s=this.getHelper(e,"wordChars");"before"!=e.sticky&&r!=t.length||!i?++r:--i;let o=t.charAt(i),n=oi(o,s)?e=>oi(e,s):/\s/.test(o)?e=>/\s/.test(e):e=>!/\s/.test(e)&&!oi(e);for(;i>0&&n(t.charAt(i-1));)--i;for(;r<t.length&&n(t.charAt(r));)++r}return new Tn(sr(e.line,i),sr(e.line,r))},toggleOverwrite:function(e){null!=e&&e==this.state.overwrite||((this.state.overwrite=!this.state.overwrite)?Ot(this.display.cursorDiv,"CodeMirror-overwrite"):Et(this.display.cursorDiv,"CodeMirror-overwrite"),_i(this,"overwriteToggle",this,this.state.overwrite))},hasFocus:function(){return this.display.input.getField()==Dt()},isReadOnly:function(){return!(!this.options.readOnly&&!this.doc.cantEdit)},scrollTo:sn((function(e,t){Do(this,e,t)})),getScrollInfo:function(){let e=this.display.scroller;return{left:e.scrollLeft,top:e.scrollTop,height:e.scrollHeight-$s(this)-this.display.barHeight,width:e.scrollWidth-$s(this)-this.display.barWidth,clientHeight:Ls(this),clientWidth:Es(this)}},scrollIntoView:sn((function(e,t){null==e?(e={from:this.doc.sel.primary().head,to:null},null==t&&(t=this.options.cursorScrollMargin)):"number"==typeof e?e={from:sr(e,0),to:null}:null==e.from&&(e={from:e,to:null}),e.to||(e.to=e.from),e.margin=t||0,null!=e.from.line?function(e,t){Oo(e),e.curOp.scrollToPos=t}(this,e):Fo(this,e.from,e.to,e.margin)})),setSize:sn((function(e,t){let i=e=>"number"==typeof e||/^\d+$/.test(String(e))?e+"px":e;null!=e&&(this.display.wrapper.style.width=i(e)),null!=t&&(this.display.wrapper.style.height=i(t)),this.options.lineWrapping&&js(this);let r=this.display.viewFrom;this.doc.iter(r,this.display.viewTo,(e=>{if(e.widgets)for(let t=0;t<e.widgets.length;t++)if(e.widgets[t].noHScroll){go(this,r,"widget");break}++r})),this.curOp.forceUpdate=!0,_i(this,"refresh",this)})),operation:function(e){return tn(this,e)},startOperation:function(){return Zo(this)},endOperation:function(){return Ko(this)},refresh:sn((function(){let e=this.display.cachedTextHeight;fo(this),this.curOp.forceUpdate=!0,Hs(this),Do(this,this.doc.scrollLeft,this.doc.scrollTop),hn(this.display),(null==e||Math.abs(e-no(this.display))>.5||this.options.lineWrapping)&&ho(this),_i(this,"refresh",this)})),swapDoc:sn((function(e){let t=this.doc;return t.cm=null,this.state.selectingText&&this.state.selectingText(),Fn(this,e),Hs(this),this.display.input.reset(),Do(this,e.scrollLeft,e.scrollTop),this.curOp.forceScroll=!0,us(this,"swapDoc",this,t),t})),phrase:function(e){let t=this.options.phrases;return t&&Object.prototype.hasOwnProperty.call(t,e)?t[e]:e},getInputField:function(){return this.display.input.getField()},getWrapperElement:function(){return this.display.wrapper},getScrollerElement:function(){return this.display.scroller},getGutterElement:function(){return this.display.gutters}},ki(e),e.registerHelper=function(t,r,s){i.hasOwnProperty(t)||(i[t]=e[t]={_global:[]}),i[t][r]=s},e.registerGlobalHelper=function(t,r,s,o){e.registerHelper(t,r,o),i[t]._global.push({pred:s,val:o})}}(Ml);var Kl,Xl="iter insert remove copy getEditor constructor".split(" ");for(let e in Ia.prototype)Ia.prototype.hasOwnProperty(e)&&Ut(Xl,e)<0&&(Ml.prototype[e]=function(e){return function(){return e.apply(this.doc,arguments)}}(Ia.prototype[e]));ki(Ia),Ml.inputStyles={textarea:Zl,contenteditable:jl},Ml.defineMode=function(e){Ml.defaults.mode||"null"==e||(Ml.defaults.mode=e),Bi.apply(this,arguments)},Ml.defineMIME=function(e,t){Wi[e]=t},Ml.defineMode("null",(()=>({token:e=>e.skipToEnd()}))),Ml.defineMIME("text/plain","null"),Ml.defineExtension=(e,t)=>{Ml.prototype[e]=t},Ml.defineDocExtension=(e,t)=>{Ia.prototype[e]=t},Ml.fromTextArea=function(e,t){if((t=t?Bt(t):{}).value=e.value,!t.tabindex&&e.tabIndex&&(t.tabindex=e.tabIndex),!t.placeholder&&e.placeholder&&(t.placeholder=e.placeholder),null==t.autofocus){let i=Dt();t.autofocus=i==e||null!=e.getAttribute("autofocus")&&i==document.body}function i(){e.value=s.getValue()}let r;if(e.form&&(gi(e.form,"submit",i),!t.leaveSubmitMethodAlone)){let t=e.form;r=t.submit;try{let e=t.submit=()=>{i(),t.submit=r,t.submit(),t.submit=e}}catch(e){}}t.finishInit=s=>{s.save=i,s.getTextArea=()=>e,s.toTextArea=()=>{s.toTextArea=isNaN,i(),e.parentNode.removeChild(s.getWrapperElement()),e.style.display="",e.form&&(bi(e.form,"submit",i),t.leaveSubmitMethodAlone||"function"!=typeof e.form.submit||(e.form.submit=r))}},e.style.display="none";let s=Ml((t=>e.parentNode.insertBefore(t,e.nextSibling)),t);return s},(Kl=Ml).off=bi,Kl.on=gi,Kl.wheelEventPixels=kn,Kl.Doc=Ia,Kl.splitLines=Ni,Kl.countColumn=jt,Kl.findColumn=Xt,Kl.isWordChar=si,Kl.Pass=Vt,Kl.signal=_i,Kl.Line=Xr,Kl.changeEnd=$n,Kl.scrollbarModel=Go,Kl.Pos=sr,Kl.cmpPos=or,Kl.modes=zi,Kl.mimeModes=Wi,Kl.resolveMode=ji,Kl.getMode=Hi,Kl.modeExtensions=Ui,Kl.extendMode=Gi,Kl.copyState=Vi,Kl.startState=Zi,Kl.innerMode=qi,Kl.commands=tl,Kl.keyMap=Ha,Kl.keyName=Ka,Kl.isModifierKey=qa,Kl.lookupKey=Va,Kl.normalizeKeyMap=Ga,Kl.StringStream=Ki,Kl.SharedTextMarker=$a,Kl.TextMarker=Ma,Kl.LineWidget=Ca,Kl.e_preventDefault=Ci,Kl.e_stopPropagation=Si,Kl.e_stop=Mi,Kl.addClass=Ot,Kl.contains=Nt,Kl.rmClass=Et,Kl.keyNames=ja,Ml.version="5.61.0";var Yl=Ml;self.CodeMirror=Yl;var Jl,Ql=class extends HTMLElement{static get observedAttributes(){return["src","readonly","mode","theme"]}attributeChangedCallback(e,t,i){this.__initialized&&t!==i&&(this[e]="readonly"===e?null!==i:i)}get readonly(){return this.editor.getOption("readOnly")}set readonly(e){this.editor.setOption("readOnly",e)}get mode(){return this.editor.getOption("mode")}set mode(e){this.editor.setOption("mode",e)}get theme(){return this.editor.getOption("theme")}set theme(e){this.editor.setOption("theme",e)}get src(){return this.getAttribute("src")}set src(e){this.setAttribute("src",e),this.setSrc()}get value(){return this.editor.getValue()}set value(e){this.__initialized?this.setValueForced(e):this.__preInitValue=e}constructor(){super();const e=e=>"childList"===e.type&&(Array.from(e.addedNodes).some((e=>"LINK"===e.tagName))||Array.from(e.removedNodes).some((e=>"LINK"===e.tagName)));this.__observer=new MutationObserver(((t,i)=>{t.some(e)&&this.refreshStyles(),this.lookupInnerScript((e=>{this.value=e}))})),this.__observer.observe(this,{childList:!0,characterData:!0,subtree:!0}),this.__initialized=!1,this.__element=null,this.editor=null}async connectedCallback(){const e=this.attachShadow({mode:"open"}),t=document.createElement("template"),i=document.createElement("style");i.innerHTML="\n/* BASICS */\n\n.CodeMirror {\n  /* Set height, width, borders, and global font properties here */\n  font-family: monospace;\n  height: auto;\n  color: black;\n  direction: ltr;\n}\n\n/* PADDING */\n\n.CodeMirror-lines {\n  padding: 4px 0; /* Vertical padding around content */\n}\n.CodeMirror pre.CodeMirror-line,\n.CodeMirror pre.CodeMirror-line-like {\n  padding: 0 4px; /* Horizontal padding of content */\n}\n\n.CodeMirror-scrollbar-filler, .CodeMirror-gutter-filler {\n  background-color: white; /* The little square between H and V scrollbars */\n}\n\n/* GUTTER */\n\n.CodeMirror-gutters {\n  border-right: 1px solid #ddd;\n  background-color: #f7f7f7;\n  white-space: nowrap;\n}\n.CodeMirror-linenumbers {}\n.CodeMirror-linenumber {\n  padding: 0 3px 0 5px;\n  min-width: 20px;\n  text-align: right;\n  color: #999;\n  white-space: nowrap;\n}\n\n.CodeMirror-guttermarker { color: black; }\n.CodeMirror-guttermarker-subtle { color: #999; }\n\n/* CURSOR */\n\n.CodeMirror-cursor {\n  border-left: 1px solid black;\n  border-right: none;\n  width: 0;\n}\n/* Shown when moving in bi-directional text */\n.CodeMirror div.CodeMirror-secondarycursor {\n  border-left: 1px solid silver;\n}\n.cm-fat-cursor .CodeMirror-cursor {\n  width: auto;\n  border: 0 !important;\n  background: #7e7;\n}\n.cm-fat-cursor div.CodeMirror-cursors {\n  z-index: 1;\n}\n.cm-fat-cursor-mark {\n  background-color: rgba(20, 255, 20, 0.5);\n  -webkit-animation: blink 1.06s steps(1) infinite;\n  -moz-animation: blink 1.06s steps(1) infinite;\n  animation: blink 1.06s steps(1) infinite;\n}\n.cm-animate-fat-cursor {\n  width: auto;\n  border: 0;\n  -webkit-animation: blink 1.06s steps(1) infinite;\n  -moz-animation: blink 1.06s steps(1) infinite;\n  animation: blink 1.06s steps(1) infinite;\n  background-color: #7e7;\n}\n@-moz-keyframes blink {\n  0% {}\n  50% { background-color: transparent; }\n  100% {}\n}\n@-webkit-keyframes blink {\n  0% {}\n  50% { background-color: transparent; }\n  100% {}\n}\n@keyframes blink {\n  0% {}\n  50% { background-color: transparent; }\n  100% {}\n}\n\n/* Can style cursor different in overwrite (non-insert) mode */\n.CodeMirror-overwrite .CodeMirror-cursor {}\n\n.cm-tab { display: inline-block; text-decoration: inherit; }\n\n.CodeMirror-rulers {\n  position: absolute;\n  left: 0; right: 0; top: -50px; bottom: 0;\n  overflow: hidden;\n}\n.CodeMirror-ruler {\n  border-left: 1px solid #ccc;\n  top: 0; bottom: 0;\n  position: absolute;\n}\n\n/* DEFAULT THEME */\n\n.cm-s-default .cm-header {color: blue;}\n.cm-s-default .cm-quote {color: #090;}\n.cm-negative {color: #d44;}\n.cm-positive {color: #292;}\n.cm-header, .cm-strong {font-weight: bold;}\n.cm-em {font-style: italic;}\n.cm-link {text-decoration: underline;}\n.cm-strikethrough {text-decoration: line-through;}\n\n.cm-s-default .cm-keyword {color: #708;}\n.cm-s-default .cm-atom {color: #219;}\n.cm-s-default .cm-number {color: #164;}\n.cm-s-default .cm-def {color: #00f;}\n.cm-s-default .cm-variable,\n.cm-s-default .cm-punctuation,\n.cm-s-default .cm-property,\n.cm-s-default .cm-operator {}\n.cm-s-default .cm-variable-2 {color: #05a;}\n.cm-s-default .cm-variable-3, .cm-s-default .cm-type {color: #085;}\n.cm-s-default .cm-comment {color: #a50;}\n.cm-s-default .cm-string {color: #a11;}\n.cm-s-default .cm-string-2 {color: #f50;}\n.cm-s-default .cm-meta {color: #555;}\n.cm-s-default .cm-qualifier {color: #555;}\n.cm-s-default .cm-builtin {color: #30a;}\n.cm-s-default .cm-bracket {color: #997;}\n.cm-s-default .cm-tag {color: #170;}\n.cm-s-default .cm-attribute {color: #00c;}\n.cm-s-default .cm-hr {color: #999;}\n.cm-s-default .cm-link {color: #00c;}\n\n.cm-s-default .cm-error {color: #f00;}\n.cm-invalidchar {color: #f00;}\n\n.CodeMirror-composing { border-bottom: 2px solid; }\n\n/* Default styles for common addons */\n\ndiv.CodeMirror span.CodeMirror-matchingbracket {color: #0b0;}\ndiv.CodeMirror span.CodeMirror-nonmatchingbracket {color: #a22;}\n.CodeMirror-matchingtag { background: rgba(255, 150, 0, .3); }\n.CodeMirror-activeline-background {background: #e8f2ff;}\n\n/* STOP */\n\n/* The rest of this file contains styles related to the mechanics of\n    the editor. You probably shouldn't touch them. */\n\n.CodeMirror {\n  position: relative;\n  overflow: hidden;\n  background: white;\n}\n\n.CodeMirror-scroll {\n  overflow: scroll !important; /* Things will break if this is overridden */\n  /* 50px is the magic margin used to hide the element's real scrollbars */\n  /* See overflow: hidden in .CodeMirror */\n  margin-bottom: -50px; margin-right: -50px;\n  padding-bottom: 50px;\n  height: 100%;\n  outline: none; /* Prevent dragging from highlighting the element */\n  position: relative;\n}\n.CodeMirror-sizer {\n  position: relative;\n  border-right: 50px solid transparent;\n}\n\n/* The fake, visible scrollbars. Used to force redraw during scrolling\n    before actual scrolling happens, thus preventing shaking and\n    flickering artifacts. */\n.CodeMirror-vscrollbar, .CodeMirror-hscrollbar, .CodeMirror-scrollbar-filler, .CodeMirror-gutter-filler {\n  position: absolute;\n  z-index: 6;\n  display: none;\n}\n.CodeMirror-vscrollbar {\n  right: 0; top: 0;\n  overflow-x: hidden;\n  overflow-y: scroll;\n}\n.CodeMirror-hscrollbar {\n  bottom: 0; left: 0;\n  overflow-y: hidden;\n  overflow-x: scroll;\n}\n.CodeMirror-scrollbar-filler {\n  right: 0; bottom: 0;\n}\n.CodeMirror-gutter-filler {\n  left: 0; bottom: 0;\n}\n\n.CodeMirror-gutters {\n  position: absolute; left: 0; top: 0;\n  min-height: 100%;\n  z-index: 3;\n}\n.CodeMirror-gutter {\n  white-space: normal;\n  height: 100%;\n  display: inline-block;\n  vertical-align: top;\n  margin-bottom: -50px;\n}\n.CodeMirror-gutter-wrapper {\n  position: absolute;\n  z-index: 4;\n  background: none !important;\n  border: none !important;\n}\n.CodeMirror-gutter-background {\n  position: absolute;\n  top: 0; bottom: 0;\n  z-index: 4;\n}\n.CodeMirror-gutter-elt {\n  position: absolute;\n  cursor: default;\n  z-index: 4;\n}\n.CodeMirror-gutter-wrapper ::selection { background-color: transparent }\n.CodeMirror-gutter-wrapper ::-moz-selection { background-color: transparent }\n\n.CodeMirror-lines {\n  cursor: text;\n  min-height: 1px; /* prevents collapsing before first draw */\n}\n.CodeMirror pre.CodeMirror-line,\n.CodeMirror pre.CodeMirror-line-like {\n  /* Reset some styles that the rest of the page might have set */\n  -moz-border-radius: 0; -webkit-border-radius: 0; border-radius: 0;\n  border-width: 0;\n  background: transparent;\n  font-family: inherit;\n  font-size: inherit;\n  margin: 0;\n  white-space: pre;\n  word-wrap: normal;\n  line-height: inherit;\n  color: inherit;\n  z-index: 2;\n  position: relative;\n  overflow: visible;\n  -webkit-tap-highlight-color: transparent;\n  -webkit-font-variant-ligatures: contextual;\n  font-variant-ligatures: contextual;\n}\n.CodeMirror-wrap pre.CodeMirror-line,\n.CodeMirror-wrap pre.CodeMirror-line-like {\n  word-wrap: break-word;\n  white-space: pre-wrap;\n  word-break: normal;\n}\n\n.CodeMirror-linebackground {\n  position: absolute;\n  left: 0; right: 0; top: 0; bottom: 0;\n  z-index: 0;\n}\n\n.CodeMirror-linewidget {\n  position: relative;\n  z-index: 2;\n  padding: 0.1px; /* Force widget margins to stay inside of the container */\n}\n\n.CodeMirror-widget {}\n\n.CodeMirror-rtl pre { direction: rtl; }\n\n.CodeMirror-code {\n  outline: none;\n}\n\n/* Force content-box sizing for the elements where we expect it */\n.CodeMirror-scroll,\n.CodeMirror-sizer,\n.CodeMirror-gutter,\n.CodeMirror-gutters,\n.CodeMirror-linenumber {\n  -moz-box-sizing: content-box;\n  box-sizing: content-box;\n}\n\n.CodeMirror-measure {\n  position: absolute;\n  width: 100%;\n  height: 0;\n  overflow: hidden;\n  visibility: hidden;\n}\n\n.CodeMirror-cursor {\n  position: absolute;\n  pointer-events: none;\n}\n.CodeMirror-measure pre { position: static; }\n\ndiv.CodeMirror-cursors {\n  visibility: hidden;\n  position: relative;\n  z-index: 3;\n}\ndiv.CodeMirror-dragcursors {\n  visibility: visible;\n}\n\n.CodeMirror-focused div.CodeMirror-cursors {\n  visibility: visible;\n}\n\n.CodeMirror-selected { background: #d9d9d9; }\n.CodeMirror-focused .CodeMirror-selected { background: #d7d4f0; }\n.CodeMirror-crosshair { cursor: crosshair; }\n.CodeMirror-line::selection, .CodeMirror-line > span::selection, .CodeMirror-line > span > span::selection { background: #d7d4f0; }\n.CodeMirror-line::-moz-selection, .CodeMirror-line > span::-moz-selection, .CodeMirror-line > span > span::-moz-selection { background: #d7d4f0; }\n\n.cm-searching {\n  background-color: #ffa;\n  background-color: rgba(255, 255, 0, .4);\n}\n\n/* Used to force a border model for a node */\n.cm-force-border { padding-right: .1px; }\n\n@media print {\n  /* Hide the cursor when printing */\n  .CodeMirror div.CodeMirror-cursors {\n    visibility: hidden;\n  }\n}\n\n/* See issue #2901 */\n.cm-tab-wrap-hack:after { content: ''; }\n\n/* Help users use markselection to safely style text background */\nspan.CodeMirror-selectedtext { background: none; }\n",t.innerHTML=Ql.template(),e.appendChild(i),e.appendChild(t.content.cloneNode(!0)),this.style.display="block",this.__element=e.querySelector("textarea");const r=this.hasAttribute("mode")?this.getAttribute("mode"):"null",s=this.hasAttribute("theme")?this.getAttribute("theme"):"default";let o=this.getAttribute("readonly");""===o?o=!0:"nocursor"!==o&&(o=!1),this.refreshStyles(),this.lookupInnerScript((e=>{this.value=e}));let n=Yl.defaults.viewportMargin;if(this.hasAttribute("viewport-margin")){const e=this.getAttribute("viewport-margin").toLowerCase();n="infinity"===e?1/0:parseInt(e)}this.editor=Yl.fromTextArea(this.__element,{lineNumbers:!0,readOnly:o,mode:r,theme:s,viewportMargin:n}),this.hasAttribute("src")&&this.setSrc(),await new Promise((e=>setTimeout(e,50))),this.__initialized=!0,void 0!==this.__preInitValue&&this.setValueForced(this.__preInitValue)}disconnectedCallback(){this.editor&&this.editor.toTextArea(),this.editor=null,this.__initialized=!1,this.__observer.disconnect()}async setSrc(){const e=this.getAttribute("src"),t=await this.fetchSrc(e);this.value=t}async setValueForced(e){this.editor.swapDoc(Yl.Doc(e,this.getAttribute("mode"))),this.editor.refresh()}async fetchSrc(e){return(await fetch(e)).text()}refreshStyles(){Array.from(this.shadowRoot.children).forEach((e=>{"LINK"===e.tagName&&"stylesheet"===e.getAttribute("rel")&&e.remove()})),Array.from(this.children).forEach((e=>{"LINK"===e.tagName&&"stylesheet"===e.getAttribute("rel")&&this.shadowRoot.appendChild(e.cloneNode(!0))}))}static template(){return'\n      <textarea style="display:inherit; width:inherit; height:inherit;"></textarea>\n    '}lookupInnerScript(e){const t=this.querySelector("script");if(t&&"wc-content"===t.getAttribute("type")){let i=Ql.dedentText(t.innerHTML);i=i.replace(/&lt;(\/?script)(.*?)&gt;/g,"<$1$2>"),e(i)}}static dedentText(e){const t=e.split("\n");""===t[0]&&t.splice(0,1);const i=t[0];let r=0;const s="\t"===i[0]?"\t":" ";for(;i[r]===s;)r+=1;const o=[];for(const e of t){let t=e;for(let e=0;e<r&&t[0]===s;e++)t=t.substring(1);o.push(t)}return""===o[o.length-1]&&o.splice(o.length-1,1),o.join("\n")}};customElements.define("wc-codemirror",Ql),Jl=function(e){function t(e){return new RegExp("^(("+e.join(")|(")+"))\\b")}var i,r=t(["and","or","not","is"]),s=["as","assert","break","class","continue","def","del","elif","else","except","finally","for","from","global","if","import","lambda","pass","raise","return","try","while","with","yield","in"],o=["abs","all","any","bin","bool","bytearray","callable","chr","classmethod","compile","complex","delattr","dict","dir","divmod","enumerate","eval","filter","float","format","frozenset","getattr","globals","hasattr","hash","help","hex","id","input","int","isinstance","issubclass","iter","len","list","locals","map","max","memoryview","min","next","object","oct","open","ord","pow","property","range","repr","reversed","round","set","setattr","slice","sorted","staticmethod","str","sum","super","tuple","type","vars","zip","__import__","NotImplemented","Ellipsis","__debug__"];function n(e){return e.scopes[e.scopes.length-1]}e.registerHelper("hintWords","python",s.concat(o)),e.defineMode("python",(function(i,a){for(var l="error",c=a.delimiters||a.singleDelimiters||/^[\(\)\[\]\{\}@,:`=;\.\\]/,d=[a.singleOperators,a.doubleOperators,a.doubleDelimiters,a.tripleDelimiters,a.operators||/^([-+*/%\/&|^]=?|[<>=]+|\/\/=?|\*\*=?|!=|[~!@]|\.\.\.)/],u=0;u<d.length;u++)d[u]||d.splice(u--,1);var h=a.hangingIndent||i.indentUnit,p=s,m=o;null!=a.extra_keywords&&(p=p.concat(a.extra_keywords)),null!=a.extra_builtins&&(m=m.concat(a.extra_builtins));var f=!(a.version&&Number(a.version)<3);if(f){var g=a.identifiers||/^[_A-Za-z\u00A1-\uFFFF][_A-Za-z0-9\u00A1-\uFFFF]*/;p=p.concat(["nonlocal","False","True","None","async","await"]),m=m.concat(["ascii","bytes","exec","print"]);var v=new RegExp("^(([rbuf]|(br)|(fr))?('{3}|\"{3}|['\"]))","i")}else g=a.identifiers||/^[_A-Za-z][_A-Za-z0-9]*/,p=p.concat(["exec","print"]),m=m.concat(["apply","basestring","buffer","cmp","coerce","execfile","file","intern","long","raw_input","reduce","reload","unichr","unicode","xrange","False","True","None"]),v=new RegExp("^(([rubf]|(ur)|(br))?('{3}|\"{3}|['\"]))","i");var b=t(p),_=t(m);function y(e,t){var i=e.sol()&&"\\"!=t.lastToken;if(i&&(t.indent=e.indentation()),i&&"py"==n(t).type){var r=n(t).offset;if(e.eatSpace()){var s=e.indentation();return s>r?w(t):s<r&&k(e,t)&&"#"!=e.peek()&&(t.errorToken=!0),null}var o=x(e,t);return r>0&&k(e,t)&&(o+=" "+l),o}return x(e,t)}function x(e,t,i){if(e.eatSpace())return null;if(!i&&e.match(/^#.*/))return"comment";if(e.match(/^[0-9\.]/,!1)){var s=!1;if(e.match(/^[\d_]*\.\d+(e[\+\-]?\d+)?/i)&&(s=!0),e.match(/^[\d_]+\.\d*/)&&(s=!0),e.match(/^\.\d+/)&&(s=!0),s)return e.eat(/J/i),"number";var o=!1;if(e.match(/^0x[0-9a-f_]+/i)&&(o=!0),e.match(/^0b[01_]+/i)&&(o=!0),e.match(/^0o[0-7_]+/i)&&(o=!0),e.match(/^[1-9][\d_]*(e[\+\-]?[\d_]+)?/)&&(e.eat(/J/i),o=!0),e.match(/^0(?![\dx])/i)&&(o=!0),o)return e.eat(/L/i),"number"}if(e.match(v))return-1!==e.current().toLowerCase().indexOf("f")?(t.tokenize=function(e,t){for(;"rubf".indexOf(e.charAt(0).toLowerCase())>=0;)e=e.substr(1);var i=1==e.length,r="string";function s(e){return function(t,i){var r=x(t,i,!0);return"punctuation"==r&&("{"==t.current()?i.tokenize=s(e+1):"}"==t.current()&&(i.tokenize=e>1?s(e-1):o)),r}}function o(o,n){for(;!o.eol();)if(o.eatWhile(/[^'"\{\}\\]/),o.eat("\\")){if(o.next(),i&&o.eol())return r}else{if(o.match(e))return n.tokenize=t,r;if(o.match("{{"))return r;if(o.match("{",!1))return n.tokenize=s(0),o.current()?r:n.tokenize(o,n);if(o.match("}}"))return r;if(o.match("}"))return l;o.eat(/['"]/)}if(i){if(a.singleLineStringErrors)return l;n.tokenize=t}return r}return o.isString=!0,o}(e.current(),t.tokenize),t.tokenize(e,t)):(t.tokenize=function(e,t){for(;"rubf".indexOf(e.charAt(0).toLowerCase())>=0;)e=e.substr(1);var i=1==e.length,r="string";function s(s,o){for(;!s.eol();)if(s.eatWhile(/[^'"\\]/),s.eat("\\")){if(s.next(),i&&s.eol())return r}else{if(s.match(e))return o.tokenize=t,r;s.eat(/['"]/)}if(i){if(a.singleLineStringErrors)return l;o.tokenize=t}return r}return s.isString=!0,s}(e.current(),t.tokenize),t.tokenize(e,t));for(var n=0;n<d.length;n++)if(e.match(d[n]))return"operator";return e.match(c)?"punctuation":"."==t.lastToken&&e.match(g)?"property":e.match(b)||e.match(r)?"keyword":e.match(_)?"builtin":e.match(/^(self|cls)\b/)?"variable-2":e.match(g)?"def"==t.lastToken||"class"==t.lastToken?"def":"variable":(e.next(),i?null:l)}function w(e){for(;"py"!=n(e).type;)e.scopes.pop();e.scopes.push({offset:n(e).offset+i.indentUnit,type:"py",align:null})}function k(e,t){for(var i=e.indentation();t.scopes.length>1&&n(t).offset>i;){if("py"!=n(t).type)return!0;t.scopes.pop()}return n(t).offset!=i}function C(e,t){e.sol()&&(t.beginningOfLine=!0);var i=t.tokenize(e,t),r=e.current();if(t.beginningOfLine&&"@"==r)return e.match(g,!1)?"meta":f?"operator":l;if(/\S/.test(r)&&(t.beginningOfLine=!1),"variable"!=i&&"builtin"!=i||"meta"!=t.lastToken||(i="meta"),"pass"!=r&&"return"!=r||(t.dedent+=1),"lambda"==r&&(t.lambda=!0),":"==r&&!t.lambda&&"py"==n(t).type&&e.match(/^\s*(?:#|$)/,!1)&&w(t),1==r.length&&!/string|comment/.test(i)){var s="[({".indexOf(r);if(-1!=s&&function(e,t,i){var r=e.match(/^[\s\[\{\(]*(?:#|$)/,!1)?null:e.column()+1;t.scopes.push({offset:t.indent+h,type:i,align:r})}(e,t,"])}".slice(s,s+1)),-1!=(s="])}".indexOf(r))){if(n(t).type!=r)return l;t.indent=t.scopes.pop().offset-h}}return t.dedent>0&&e.eol()&&"py"==n(t).type&&(t.scopes.length>1&&t.scopes.pop(),t.dedent-=1),i}return{startState:function(e){return{tokenize:y,scopes:[{offset:e||0,type:"py",align:null}],indent:e||0,lastToken:null,lambda:!1,dedent:0}},token:function(e,t){var i=t.errorToken;i&&(t.errorToken=!1);var r=C(e,t);return r&&"comment"!=r&&(t.lastToken="keyword"==r||"punctuation"==r?e.current():r),"punctuation"==r&&(r=null),e.eol()&&t.lambda&&(t.lambda=!1),i?r+" "+l:r},indent:function(t,i){if(t.tokenize!=y)return t.tokenize.isString?e.Pass:0;var r=n(t),s=r.type==i.charAt(0);return null!=r.align?r.align-(s?1:0):r.offset-(s?h:0)},electricInput:/^\s*[\}\]\)]$/,closeBrackets:{triples:"'\""},lineComment:"#",fold:"indent"}})),e.defineMIME("text/x-python","python"),e.defineMIME("text/x-cython",{name:"python",extra_keywords:(i="by cdef cimport cpdef ctypedef enum except extern gil include nogil property public readonly struct union DEF IF ELIF ELSE",i.split(" "))})},"object"==typeof exports&&"object"==typeof module?Jl(require("../../lib/codemirror")):"function"==typeof define&&define.amd?define(["../../lib/codemirror"],Jl):Jl(CodeMirror),function(e){"object"==typeof exports&&"object"==typeof module?e(require("../../lib/codemirror")):"function"==typeof define&&define.amd?define(["../../lib/codemirror"],e):e(CodeMirror)}((function(e){e.defineMode("shell",(function(){var t={};function i(e,i){for(var r=0;r<i.length;r++)t[i[r]]=e}var r=["true","false"],s=["if","then","do","else","elif","while","until","for","in","esac","fi","fin","fil","done","exit","set","unset","export","function"],o=["ab","awk","bash","beep","cat","cc","cd","chown","chmod","chroot","clear","cp","curl","cut","diff","echo","find","gawk","gcc","get","git","grep","hg","kill","killall","ln","ls","make","mkdir","openssl","mv","nc","nl","node","npm","ping","ps","restart","rm","rmdir","sed","service","sh","shopt","shred","source","sort","sleep","ssh","start","stop","su","sudo","svn","tee","telnet","top","touch","vi","vim","wall","wc","wget","who","write","yes","zsh"];function n(e,i){if(e.eatSpace())return null;var r,s=e.sol(),o=e.next();if("\\"===o)return e.next(),null;if("'"===o||'"'===o||"`"===o)return i.tokens.unshift(a(o,"`"===o?"quote":"string")),d(e,i);if("#"===o)return s&&e.eat("!")?(e.skipToEnd(),"meta"):(e.skipToEnd(),"comment");if("$"===o)return i.tokens.unshift(c),d(e,i);if("+"===o||"="===o)return"operator";if("-"===o)return e.eat("-"),e.eatWhile(/\w/),"attribute";if("<"==o){if(e.match("<<"))return"operator";var n=e.match(/^<-?\s*['"]?([^'"]*)['"]?/);if(n)return i.tokens.unshift((r=n[1],function(e,t){return e.sol()&&e.string==r&&t.tokens.shift(),e.skipToEnd(),"string-2"})),"string-2"}if(/\d/.test(o)&&(e.eatWhile(/\d/),e.eol()||!/\w/.test(e.peek())))return"number";e.eatWhile(/[\w-]/);var l=e.current();return"="===e.peek()&&/\w+/.test(l)?"def":t.hasOwnProperty(l)?t[l]:null}function a(e,t){var i="("==e?")":"{"==e?"}":e;return function(r,s){for(var o,n=!1;null!=(o=r.next());){if(o===i&&!n){s.tokens.shift();break}if("$"===o&&!n&&"'"!==e&&r.peek()!=i){n=!0,r.backUp(1),s.tokens.unshift(c);break}if(!n&&e!==i&&o===e)return s.tokens.unshift(a(e,t)),d(r,s);if(!n&&/['"]/.test(o)&&!/['"]/.test(e)){s.tokens.unshift(l(o,"string")),r.backUp(1);break}n=!n&&"\\"===o}return t}}function l(e,t){return function(i,r){return r.tokens[0]=a(e,t),i.next(),d(i,r)}}e.registerHelper("hintWords","shell",r.concat(s,o)),i("atom",r),i("keyword",s),i("builtin",o);var c=function(e,t){t.tokens.length>1&&e.eat("$");var i=e.next();return/['"({]/.test(i)?(t.tokens[0]=a(i,"("==i?"quote":"{"==i?"def":"string"),d(e,t)):(/\d/.test(i)||e.eatWhile(/\w/),t.tokens.shift(),"def")};function d(e,t){return(t.tokens[0]||n)(e,t)}return{startState:function(){return{tokens:[]}},token:function(e,t){return d(e,t)},closeBrackets:"()[]{}''\"\"``",lineComment:"#",fold:"brace"}})),e.defineMIME("text/x-sh","shell"),e.defineMIME("application/x-sh","shell")})),function(e){"object"==typeof exports&&"object"==typeof module?e(require("../../lib/codemirror")):"function"==typeof define&&define.amd?define(["../../lib/codemirror"],e):e(CodeMirror)}((function(e){e.defineMode("yaml",(function(){var e=new RegExp("\\b(("+["true","false","on","off","yes","no"].join(")|(")+"))$","i");return{token:function(t,i){var r=t.peek(),s=i.escaped;if(i.escaped=!1,"#"==r&&(0==t.pos||/\s/.test(t.string.charAt(t.pos-1))))return t.skipToEnd(),"comment";if(t.match(/^('([^']|\\.)*'?|"([^"]|\\.)*"?)/))return"string";if(i.literal&&t.indentation()>i.keyCol)return t.skipToEnd(),"string";if(i.literal&&(i.literal=!1),t.sol()){if(i.keyCol=0,i.pair=!1,i.pairStart=!1,t.match("---"))return"def";if(t.match("..."))return"def";if(t.match(/\s*-\s+/))return"meta"}if(t.match(/^(\{|\}|\[|\])/))return"{"==r?i.inlinePairs++:"}"==r?i.inlinePairs--:"["==r?i.inlineList++:i.inlineList--,"meta";if(i.inlineList>0&&!s&&","==r)return t.next(),"meta";if(i.inlinePairs>0&&!s&&","==r)return i.keyCol=0,i.pair=!1,i.pairStart=!1,t.next(),"meta";if(i.pairStart){if(t.match(/^\s*(\||\>)\s*/))return i.literal=!0,"meta";if(t.match(/^\s*(\&|\*)[a-z0-9\._-]+\b/i))return"variable-2";if(0==i.inlinePairs&&t.match(/^\s*-?[0-9\.\,]+\s?$/))return"number";if(i.inlinePairs>0&&t.match(/^\s*-?[0-9\.\,]+\s?(?=(,|}))/))return"number";if(t.match(e))return"keyword"}return!i.pair&&t.match(/^\s*(?:[,\[\]{}&*!|>'"%@`][^\s'":]|[^,\[\]{}#&*!|>'"%@`])[^#]*?(?=\s*:($|\s))/)?(i.pair=!0,i.keyCol=t.indentation(),"atom"):i.pair&&t.match(/^:\s*/)?(i.pairStart=!0,"meta"):(i.pairStart=!1,i.escaped="\\"==r,t.next(),null)},startState:function(){return{pair:!1,pairStart:!1,keyCol:0,inlinePairs:0,inlineList:0,literal:!1,escaped:!1}},lineComment:"#",fold:"indent"}})),e.defineMIME("text/x-yaml","yaml"),e.defineMIME("text/yaml","yaml")}));let ec=class extends r{constructor(){super(),this.config=Object(),this.mode="shell",this.theme="monokai",this.src="",this.readonly=!1,this.useLineWrapping=!1,this.required=!1,this.validationMessage="",this.validationMessageIcon="warning",this.config={tabSize:2,indentUnit:2,cursorScrollMargin:50,lineNumbers:!0,matchBrackets:!0,styleActiveLine:!0,viewportMargin:1/0,extraKeys:{}}}firstUpdated(){this._initEditor()}_initEditor(){this.editorEl.__initialized?(this.editor=this.editorEl.editor,Object.assign(this.editor.options,this.config),this.editor.setOption("lineWrapping",this.useLineWrapping),this.refresh()):setTimeout(this._initEditor.bind(this),100)}refresh(){globalThis.setTimeout((()=>this.editor.refresh()),100)}focus(){globalThis.setTimeout((()=>{this.editor.execCommand("goDocEnd"),this.editor.focus(),this.refresh()}),100)}getValue(){return this.editor.getValue()}setValue(e){this.editor.setValue(e),this.refresh()}_validateInput(){if(this.required){if(""===this.getValue())return this.showValidationMessage(),this.editorEl.style.border="2px solid red",!1;this.hideValidationMessage(),this.editorEl.style.border="none"}return!0}showValidationMessage(){this.validationMessageEl.style.display="flex"}hideValidationMessage(){this.validationMessageEl.style.display="none"}static get styles(){return[s,o,n,rt,it,c`
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
      `]}render(){return d`
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
    `}};e([t({type:Object})],ec.prototype,"config",void 0),e([t({type:String})],ec.prototype,"mode",void 0),e([t({type:String})],ec.prototype,"theme",void 0),e([t({type:String})],ec.prototype,"src",void 0),e([t({type:Boolean})],ec.prototype,"readonly",void 0),e([t({type:Boolean})],ec.prototype,"useLineWrapping",void 0),e([t({type:Boolean})],ec.prototype,"required",void 0),e([t({type:String})],ec.prototype,"validationMessage",void 0),e([t({type:String})],ec.prototype,"validationMessageIcon",void 0),e([E("#validation-message")],ec.prototype,"validationMessageEl",void 0),e([E("#codemirror-editor")],ec.prototype,"editorEl",void 0),ec=e([i("lablup-codemirror")],ec);
/**
 * @license
 * Copyright 2020 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
class tc extends F{constructor(){super(...arguments),this.left=!1,this.graphic="control"}render(){const e={"mdc-deprecated-list-item__graphic":this.left,"mdc-deprecated-list-item__meta":!this.left},t=this.renderText(),i=this.graphic&&"control"!==this.graphic&&!this.left?this.renderGraphic():k``,r=this.hasMeta&&this.left?this.renderMeta():k``,s=this.renderRipple();return k`
      ${s}
      ${i}
      ${this.left?"":t}
      <span class=${C(e)}>
        <mwc-checkbox
            reducedTouchTarget
            tabindex=${this.tabindex}
            .checked=${this.selected}
            ?disabled=${this.disabled}
            @change=${this.onChange}>
        </mwc-checkbox>
      </span>
      ${this.left?t:""}
      ${r}`}async onChange(e){const t=e.target;this.selected===t.checked||(this._skipPropRequest=!0,this.selected=t.checked,await this.updateComplete,this._skipPropRequest=!1)}}e([g("slot")],tc.prototype,"slotElement",void 0),e([g("mwc-checkbox")],tc.prototype,"checkboxElement",void 0),e([b({type:Boolean})],tc.prototype,"left",void 0),e([b({type:String,reflect:!0})],tc.prototype,"graphic",void 0);
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-LIcense-Identifier: Apache-2.0
 */
const ic=u`:host(:not([twoline])){height:56px}:host(:not([left])) .mdc-deprecated-list-item__meta{height:40px;width:40px}`
/**
 * @license
 * Copyright 2020 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */;let rc=class extends tc{};rc.styles=[z,ic],rc=e([$("mwc-check-list-item")],rc),
/**
 * @license
 * Copyright (c) 2017 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
W("vaadin-text-field",B,{moduleId:"lumo-text-field-styles"});
/**
 * @license
 * Copyright (c) 2021 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const sc=e=>class extends(j(e)){static get properties(){return{autocomplete:{type:String},autocorrect:{type:String},autocapitalize:{type:String,reflectToAttribute:!0}}}static get delegateAttrs(){return[...super.delegateAttrs,"autocapitalize","autocomplete","autocorrect"]}get __data(){return this.__dataValue||{}}set __data(e){this.__dataValue=e}_inputElementChanged(e){super._inputElementChanged(e),e&&(e.value&&e.value!==this.value&&(console.warn(`Please define value on the <${this.localName}> component!`),e.value=""),this.value&&(e.value=this.value))}_setFocused(e){super._setFocused(e),!e&&document.hasFocus()&&this.validate()}_onInput(e){super._onInput(e),this.invalid&&this.validate()}_valueChanged(e,t){super._valueChanged(e,t),void 0!==t&&this.invalid&&this.validate()}}
/**
 * @license
 * Copyright (c) 2021 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,oc=e=>class extends(sc(e)){static get properties(){return{maxlength:{type:Number},minlength:{type:Number},pattern:{type:String}}}static get delegateAttrs(){return[...super.delegateAttrs,"maxlength","minlength","pattern"]}static get constraints(){return[...super.constraints,"maxlength","minlength","pattern"]}constructor(){super(),this._setType("text")}get clearElement(){return this.$.clearButton}ready(){super.ready(),this.addController(new H(this,(e=>{this._setInputElement(e),this._setFocusElement(e),this.stateTarget=e,this.ariaTarget=e}))),this.addController(new U(this.inputElement,this._labelController))}}
/**
 * @license
 * Copyright (c) 2017 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;W("vaadin-text-field",G,{moduleId:"vaadin-text-field-styles"});class nc extends(oc(K(X(Y)))){static get is(){return"vaadin-text-field"}static get template(){return V`
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
    `}static get properties(){return{maxlength:{type:Number},minlength:{type:Number}}}ready(){super.ready(),this._tooltipController=new q(this),this._tooltipController.setPosition("top"),this._tooltipController.setAriaTarget(this.inputElement),this.addController(this._tooltipController)}}Z(nc),
/**
 * @license
 * Copyright (c) 2016 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
W("vaadin-grid-filter",c`
    :host {
      display: inline-flex;
      max-width: 100%;
    }

    ::slotted(*) {
      width: 100%;
      box-sizing: border-box;
    }
  `,{moduleId:"vaadin-grid-filter-styles"});const ac=e=>class extends(J(e)){static get properties(){return{path:{type:String,sync:!0},value:{type:String,notify:!0,sync:!0},_textField:{type:Object,sync:!0}}}static get observers(){return["_filterChanged(path, value, _textField)"]}ready(){super.ready(),this._filterController=new Q(this,"","vaadin-text-field",{initializer:e=>{e.addEventListener("input",(e=>{this.value=e.target.value})),this._textField=e}}),this.addController(this._filterController)}_filterChanged(e,t,i){void 0!==e&&void 0!==t&&i&&(i.value=t,this._debouncerFilterChanged=ee.debounce(this._debouncerFilterChanged,te.after(200),(()=>{this.dispatchEvent(new CustomEvent("filter-changed",{bubbles:!0}))})))}focus(){this._textField&&this._textField.focus()}}
/**
 * @license
 * Copyright (c) 2016 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;class lc extends(ac(K(Y))){static get template(){return V`<slot></slot>`}static get is(){return"vaadin-grid-filter"}}Z(lc);
/**
 * @license
 * Copyright (c) 2016 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const cc=e=>class extends e{static get properties(){return{path:{type:String,sync:!0},header:{type:String,sync:!0}}}static get observers(){return["_onHeaderRendererOrBindingChanged(_headerRenderer, _headerCell, path, header)"]}_defaultHeaderRenderer(e,t){let i=e.firstElementChild,r=i?i.firstElementChild:void 0;i||(i=document.createElement("vaadin-grid-filter"),r=document.createElement("vaadin-text-field"),r.setAttribute("theme","small"),r.setAttribute("style","max-width: 100%;"),r.setAttribute("focus-target",""),i.appendChild(r),e.appendChild(i)),i.path=this.path,r.label=this.__getHeader(this.header,this.path)}_computeHeaderRenderer(){return this._defaultHeaderRenderer}__getHeader(e,t){return e||(t?this._generateHeader(t):void 0)}}
/**
 * @license
 * Copyright (c) 2016 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;class dc extends(cc(ie)){static get is(){return"vaadin-grid-filter-column"}}Z(dc);let uc=class extends N{constructor(){super(),this.is_connected=!1,this.enableLaunchButton=!1,this.hideLaunchButton=!1,this.hideEnvDialog=!1,this.hidePreOpenPortDialog=!1,this.enableInferenceWorkload=!1,this.location="",this.mode="normal",this.newSessionDialogTitle="",this.importScript="",this.importFilename="",this.imageRequirements=Object(),this.resourceLimits=Object(),this.userResourceLimit=Object(),this.aliases=Object(),this.tags=Object(),this.icons=Object(),this.imageInfo=Object(),this.kernel="",this.marker_limit=25,this.gpu_modes=[],this.gpu_step=.1,this.cpu_metric={min:"1",max:"1"},this.mem_metric={min:"1",max:"1"},this.shmem_metric={min:.0625,max:1,preferred:.0625},this.npu_device_metric={min:0,max:0},this.rocm_device_metric={min:"0",max:"0"},this.tpu_device_metric={min:"1",max:"1"},this.ipu_device_metric={min:"0",max:"0"},this.atom_device_metric={min:"0",max:"0"},this.atom_plus_device_metric={min:"0",max:"0"},this.gaudi2_device_metric={min:"0",max:"0"},this.warboy_device_metric={min:"0",max:"0"},this.rngd_device_metric={min:"0",max:"0"},this.hyperaccel_lpu_device_metric={min:"0",max:"0"},this.cluster_metric={min:1,max:1},this.cluster_mode_list=["single-node","multi-node"],this.cluster_support=!1,this.folderMapping=Object(),this.customFolderMapping=Object(),this.aggregate_updating=!1,this.resourceGauge=Object(),this.sessionType="interactive",this.ownerFeatureInitialized=!1,this.ownerDomain="",this.project_resource_monitor=!1,this._default_language_updated=!1,this._default_version_updated=!1,this._helpDescription="",this._helpDescriptionTitle="",this._helpDescriptionIcon="",this._NPUDeviceNameOnSlider="GPU",this.max_cpu_core_per_session=128,this.max_mem_per_container=1536,this.max_cuda_device_per_container=16,this.max_cuda_shares_per_container=16,this.max_rocm_device_per_container=10,this.max_tpu_device_per_container=8,this.max_ipu_device_per_container=8,this.max_atom_device_per_container=4,this.max_atom_plus_device_per_container=4,this.max_gaudi2_device_per_container=4,this.max_warboy_device_per_container=4,this.max_rngd_device_per_container=4,this.max_hyperaccel_lpu_device_per_container=4,this.max_shm_per_container=8,this.allow_manual_image_name_for_session=!1,this.cluster_size=1,this.deleteEnvInfo=Object(),this.deleteEnvRow=Object(),this.environ_values=Object(),this.vfolder_select_expansion=Object(),this.currentIndex=1,this._nonAutoMountedFolderGrid=Object(),this._modelFolderGrid=Object(),this._debug=!1,this._boundFolderToMountListRenderer=this.folderToMountListRenderer.bind(this),this._boundFolderMapRenderer=this.folderMapRenderer.bind(this),this._boundPathRenderer=this.infoHeaderRenderer.bind(this),this.scheduledTime="",this.sessionInfoObj={environment:"",version:[""]},this.launchButtonMessageTextContent=re("session.launcher.Launch"),this.isExceedMaxCountForPreopenPorts=!1,this.maxCountForPreopenPorts=10,this.allowCustomResourceAllocation=!0,this.allowNEOSessionLauncher=!1,this.active=!1,this.ownerKeypairs=[],this.ownerGroups=[],this.ownerScalingGroups=[],this.resourceBroker=globalThis.resourceBroker,this.notification=globalThis.lablupNotification,this.environ=[],this.preOpenPorts=[],this.init_resource()}static get is(){return"backend-ai-session-launcher"}static get styles(){return[s,o,n,a,l,c`
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
      `]}init_resource(){this.versions=["Not Selected"],this.languages=[],this.gpu_mode="none",this.total_slot={},this.total_resource_group_slot={},this.total_project_slot={},this.used_slot={},this.used_resource_group_slot={},this.used_project_slot={},this.available_slot={},this.used_slot_percent={},this.used_resource_group_slot_percent={},this.used_project_slot_percent={},this.resource_templates=[],this.resource_templates_filtered=[],this.vfolders=[],this.selectedVfolders=[],this.nonAutoMountedVfolders=[],this.modelVfolders=[],this.autoMountedVfolders=[],this.default_language="",this.concurrency_used=0,this.concurrency_max=0,this.concurrency_limit=2,this.max_containers_per_session=1,this._status="inactive",this.cpu_request=1,this.mem_request=1,this.shmem_request=.0625,this.gpu_request=0,this.gpu_request_type="cuda.device",this.session_request=1,this.scaling_groups=[{name:""}],this.scaling_group="",this.sessions_list=[],this.metric_updating=!1,this.metadata_updating=!1,this.cluster_size=1,this.cluster_mode="single-node",this.ownerFeatureInitialized=!1,this.ownerDomain="",this.ownerKeypairs=[],this.ownerGroups=[],this.ownerScalingGroups=[]}firstUpdated(){var e,t,i,r,s,o;this.environment.addEventListener("selected",this.updateLanguage.bind(this)),this.version_selector.addEventListener("selected",(()=>{this.updateResourceAllocationPane()})),null===(e=this.shadowRoot)||void 0===e||e.querySelectorAll("lablup-expansion").forEach((e=>{e.addEventListener("keydown",(e=>{e.stopPropagation()}),!0)})),this.resourceGauge=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#resource-gauges"),document.addEventListener("backend-ai-group-changed",(()=>{this._updatePageVariables(!0)})),document.addEventListener("backend-ai-resource-broker-updated",(()=>{})),!0===this.hideLaunchButton&&((null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#launch-session")).style.display="none"),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.max_cpu_core_per_session=globalThis.backendaiclient._config.maxCPUCoresPerContainer||128,this.max_mem_per_container=globalThis.backendaiclient._config.maxMemoryPerContainer||1536,this.max_cuda_device_per_container=globalThis.backendaiclient._config.maxCUDADevicesPerContainer||16,this.max_cuda_shares_per_container=globalThis.backendaiclient._config.maxCUDASharesPerContainer||16,this.max_rocm_device_per_container=globalThis.backendaiclient._config.maxROCMDevicesPerContainer||10,this.max_tpu_device_per_container=globalThis.backendaiclient._config.maxTPUDevicesPerContainer||8,this.max_ipu_device_per_container=globalThis.backendaiclient._config.maxIPUDevicesPerContainer||8,this.max_atom_device_per_container=globalThis.backendaiclient._config.maxATOMDevicesPerContainer||8,this.max_atom_plus_device_per_container=globalThis.backendaiclient._config.maxATOMPlUSDevicesPerContainer||8,this.max_gaudi2_device_per_container=globalThis.backendaiclient._config.maxGaudi2DevicesPerContainer||8,this.max_warboy_device_per_container=globalThis.backendaiclient._config.maxWarboyDevicesPerContainer||8,this.max_rngd_device_per_container=globalThis.backendaiclient._config.maxRNGDDevicesPerContainer||8,this.max_hyperaccel_lpu_device_per_container=globalThis.backendaiclient._config.maxHyperaccelLPUDevicesPerContainer||8,this.max_shm_per_container=globalThis.backendaiclient._config.maxShmPerContainer||8,void 0!==globalThis.backendaiclient._config.allow_manual_image_name_for_session&&"allow_manual_image_name_for_session"in globalThis.backendaiclient._config&&""!==globalThis.backendaiclient._config.allow_manual_image_name_for_session?this.allow_manual_image_name_for_session=globalThis.backendaiclient._config.allow_manual_image_name_for_session:this.allow_manual_image_name_for_session=!1,globalThis.backendaiclient.supports("multi-container")&&(this.cluster_support=!0),this.maxCountForPreopenPorts=globalThis.backendaiclient._config.maxCountForPreopenPorts,this.allowCustomResourceAllocation=globalThis.backendaiclient._config.allowCustomResourceAllocation,this.is_connected=!0,this._debug=globalThis.backendaiwebui.debug,this._enableLaunchButton()}),{once:!0}):(this.max_cpu_core_per_session=globalThis.backendaiclient._config.maxCPUCoresPerContainer||128,this.max_mem_per_container=globalThis.backendaiclient._config.maxMemoryPerContainer||1536,this.max_cuda_device_per_container=globalThis.backendaiclient._config.maxCUDADevicesPerContainer||16,this.max_cuda_shares_per_container=globalThis.backendaiclient._config.maxCUDASharesPerContainer||16,this.max_rocm_device_per_container=globalThis.backendaiclient._config.maxROCMDevicesPerContainer||10,this.max_tpu_device_per_container=globalThis.backendaiclient._config.maxTPUDevicesPerContainer||8,this.max_ipu_device_per_container=globalThis.backendaiclient._config.maxIPUDevicesPerContainer||8,this.max_atom_device_per_container=globalThis.backendaiclient._config.maxATOMDevicesPerContainer||8,this.max_atom_plus_device_per_container=globalThis.backendaiclient._config.maxATOMPlUSDevicesPerContainer||8,this.max_gaudi2_device_per_container=globalThis.backendaiclient._config.maxGaudi2DevicesPerContainer||8,this.max_warboy_device_per_container=globalThis.backendaiclient._config.maxWarboyDevicesPerContainer||8,this.max_rngd_device_per_container=globalThis.backendaiclient._config.maxRNGDDevicesPerContainer||8,this.max_hyperaccel_lpu_device_per_container=globalThis.backendaiclient._config.maxHyperaccelLPUDevicesPerContainer||8,this.max_shm_per_container=globalThis.backendaiclient._config.maxShmPerContainer||8,void 0!==globalThis.backendaiclient._config.allow_manual_image_name_for_session&&"allow_manual_image_name_for_session"in globalThis.backendaiclient._config&&""!==globalThis.backendaiclient._config.allow_manual_image_name_for_session?this.allow_manual_image_name_for_session=globalThis.backendaiclient._config.allow_manual_image_name_for_session:this.allow_manual_image_name_for_session=!1,globalThis.backendaiclient.supports("multi-container")&&(this.cluster_support=!0),this.maxCountForPreopenPorts=globalThis.backendaiclient._config.maxCountForPreopenPorts,this.allowCustomResourceAllocation=globalThis.backendaiclient._config.allowCustomResourceAllocation,this.is_connected=!0,this._debug=globalThis.backendaiwebui.debug,this._enableLaunchButton()),this.modifyEnvDialog.addEventListener("dialog-closing-confirm",(e=>{var t;const i={},r=null===(t=this.modifyEnvContainer)||void 0===t?void 0:t.querySelectorAll(".row");Array.prototype.filter.call(r,(e=>(e=>Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>0===e.value.length)).length<=1)(e))).map((e=>(e=>{const t=Array.prototype.map.call(e.querySelectorAll("mwc-textfield"),(e=>e.value));return i[t[0]]=t[1],t})(e)));((e,t)=>{const i=Object.getOwnPropertyNames(e),r=Object.getOwnPropertyNames(t);if(i.length!=r.length)return!1;for(let r=0;r<i.length;r++){const s=i[r];if(e[s]!==t[s])return!1}return!0})(i,this.environ_values)?(this.modifyEnvDialog.closeWithConfirmation=!1,this.closeDialog("modify-env-dialog")):(this.hideEnvDialog=!0,this.openDialog("env-config-confirmation"))})),this.modifyPreOpenPortDialog.addEventListener("dialog-closing-confirm",(()=>{var e;const t=null===(e=this.modifyPreOpenPortContainer)||void 0===e?void 0:e.querySelectorAll(".row:not(.header) mwc-textfield"),i=Array.from(t).filter((e=>""!==e.value)).map((e=>e.value));var r,s;r=i,s=this.preOpenPorts,r.length===s.length&&r.every(((e,t)=>e===s[t]))?(this.modifyPreOpenPortDialog.closeWithConfirmation=!1,this.closeDialog("modify-preopen-ports-dialog")):(this.hidePreOpenPortDialog=!0,this.openDialog("preopen-ports-config-confirmation"))})),this.currentIndex=1,this.progressLength=null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelectorAll(".progress").length,this._nonAutoMountedFolderGrid=null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#non-auto-mounted-folder-grid"),this._modelFolderGrid=null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("#model-folder-grid"),globalThis.addEventListener("resize",(()=>{document.body.dispatchEvent(new Event("click"))}))}_enableLaunchButton(){this.resourceBroker.image_updating?(this.enableLaunchButton=!1,setTimeout((()=>{this._enableLaunchButton()}),1e3)):("inference"===this.mode?this.languages=this.resourceBroker.languages.filter((e=>""!==e.name&&"INFERENCE"===this.resourceBroker.imageRoles[e.name])):this.languages=this.resourceBroker.languages.filter((e=>""===e.name||"COMPUTE"===this.resourceBroker.imageRoles[e.name])),this.enableLaunchButton=!0)}_updateSelectedScalingGroup(){this.scaling_groups=this.resourceBroker.scaling_groups;const e=this.scalingGroups.items.find((e=>e.value===this.resourceBroker.scaling_group));if(""===this.resourceBroker.scaling_group||void 0===e)return void setTimeout((()=>{this._updateSelectedScalingGroup()}),500);const t=this.scalingGroups.items.indexOf(e);this.scalingGroups.select(-1),this.scalingGroups.select(t),this.scalingGroups.value=e.value,this.scalingGroups.requestUpdate()}async updateScalingGroup(e=!1,t){this.active&&(await this.resourceBroker.updateScalingGroup(e,t.target.value),!0===e?await this._refreshResourcePolicy():await this.updateResourceAllocationPane("session dialog"))}_initializeFolderMapping(){var e;this.folderMapping={};(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll(".alias")).forEach((e=>{e.value=""}))}async _updateSelectedFolder(e=!1){var t,i,r;if(this._nonAutoMountedFolderGrid&&this._nonAutoMountedFolderGrid.selectedItems){let s=this._nonAutoMountedFolderGrid.selectedItems;s=s.concat(this._modelFolderGrid.selectedItems);let o=[];s.length>0&&(o=s.map((e=>e.name)),e&&this._unselectAllSelectedFolder()),this.selectedVfolders=o;for(const e of this.selectedVfolders){if((null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#vfolder-alias-"+e)).value.length>0&&(this.folderMapping[e]=(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#vfolder-alias-"+e)).value),e in this.folderMapping&&this.selectedVfolders.includes(this.folderMapping[e]))return delete this.folderMapping[e],(null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector("#vfolder-alias-"+e)).value="",await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!0)}}return Promise.resolve(!0)}_unselectAllSelectedFolder(){[this._nonAutoMountedFolderGrid,this._modelFolderGrid].forEach((e=>{e&&e.selectedItems&&(e.selectedItems.forEach((e=>{e.selected=!1})),e.selectedItems=[])})),this.selectedVfolders=[]}_checkSelectedItems(){[this._nonAutoMountedFolderGrid,this._modelFolderGrid].forEach((e=>{if(e&&e.selectedItems){const t=e.selectedItems;let i=[];t.length>0&&(e.selectedItems=[],i=t.map((e=>null==e?void 0:e.id)),e.querySelectorAll("vaadin-checkbox").forEach((e=>{var t;i.includes(null===(t=e.__item)||void 0===t?void 0:t.id)&&(e.checked=!0)})))}}))}_preProcessingSessionInfo(){var e,t;let i,r;if(null===(e=this.manualImageName)||void 0===e?void 0:e.value){const e=this.manualImageName.value.split(":");i=e[0],r=e.slice(-1)[0].split("-")}else{if(void 0===this.kernel||!1!==(null===(t=this.version_selector)||void 0===t?void 0:t.disabled))return!1;i=this.kernel,r=this.version_selector.selectedText.split("/")}return this.sessionInfoObj.environment=i.split("/").pop(),this.sessionInfoObj.version=[r[0].toUpperCase()].concat(1!==r.length?r.slice(1).map((e=>e.toUpperCase())):[""]),!0}async _viewStateChanged(){if(await this.updateComplete,!this.active)return;const e=()=>{this.enableInferenceWorkload=globalThis.backendaiclient.supports("inference-workload")};void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.project_resource_monitor=this.resourceBroker.allow_project_resource_monitor,this._updatePageVariables(!0),this._disableEnterKey(),e()}),{once:!0}):(this.project_resource_monitor=this.resourceBroker.allow_project_resource_monitor,await this._updatePageVariables(!0),this._disableEnterKey(),e())}async _updatePageVariables(e){this.active&&!1===this.metadata_updating&&(this.metadata_updating=!0,await this.resourceBroker._updatePageVariables(e),this._updateSelectedScalingGroup(),this.sessions_list=this.resourceBroker.sessions_list,await this._refreshResourcePolicy(),this.aggregateResource("update-page-variable"),this.metadata_updating=!1)}async _refreshResourcePolicy(){return this.resourceBroker._refreshResourcePolicy().then((()=>{var e;this.concurrency_used=this.resourceBroker.concurrency_used,this.userResourceLimit=this.resourceBroker.userResourceLimit,this.concurrency_max=this.resourceBroker.concurrency_max,this.max_containers_per_session=null!==(e=this.resourceBroker.max_containers_per_session)&&void 0!==e?e:1,this.gpu_mode=this.resourceBroker.gpu_mode,this.gpu_step=this.resourceBroker.gpu_step,this.gpu_modes=this.resourceBroker.gpu_modes,this.updateResourceAllocationPane("refresh resource policy")})).catch((e=>{this.metadata_updating=!1,e&&e.message?(this.notification.text=D.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=D.relieve(e.title),this.notification.show(!0,e))}))}async _launchSessionDialog(){var e;const t=!globalThis.backendaioptions.get("classic_session_launcher",!1);if(!0===this.allowNEOSessionLauncher&&t){const e="/session/start?formValues="+encodeURIComponent(JSON.stringify({resourceGroup:this.resourceBroker.scaling_group}));return se.dispatch(oe(decodeURIComponent(e),{})),void document.dispatchEvent(new CustomEvent("react-navigate",{detail:e}))}if(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready||!0===this.resourceBroker.image_updating)setTimeout((()=>{this._launchSessionDialog()}),1e3);else{this.folderMapping=Object(),this._resetProgress(),await this.selectDefaultLanguage();const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector('lablup-expansion[name="ownership"]');globalThis.backendaiclient.is_admin?t.style.display="block":t.style.display="none",this._updateSelectedScalingGroup(),await this._refreshResourcePolicy(),this.requestUpdate(),this.newSessionDialog.show()}}_generateKernelIndex(e,t){return e+":"+t}_moveToLastProgress(){this.moveProgress(4)}_newSessionWithConfirmation(){var e,t,i,r;const s=null===(t=null===(e=this._nonAutoMountedFolderGrid)||void 0===e?void 0:e.selectedItems)||void 0===t?void 0:t.map((e=>e.name)).length,o=null===(r=null===(i=this._modelFolderGrid)||void 0===i?void 0:i.selectedItems)||void 0===r?void 0:r.map((e=>e.name)).length;if(this.currentIndex==this.progressLength){if("inference"===this.mode||void 0!==s&&s>0||void 0!==o&&o>0)return this._newSession();this.launchConfirmationDialog.show()}else this._moveToLastProgress()}_newSession(){var e,t,i,r,s,o,n,a,l,c,d,u;let h,p,m;if(this.launchConfirmationDialog.hide(),this.manualImageName&&this.manualImageName.value){const e=this.manualImageName.value.split(":");p=e.splice(-1,1)[0],h=e.join(":"),m=["x86_64","aarch64"].includes(this.manualImageName.value.split("@").pop())?this.manualImageName.value.split("@").pop():void 0,m&&(h=this.manualImageName.value.split("@")[0])}else{const o=this.environment.selected;h=null!==(e=null==o?void 0:o.id)&&void 0!==e?e:"",p=null!==(i=null===(t=this.version_selector.selected)||void 0===t?void 0:t.value)&&void 0!==i?i:"",m=null!==(s=null===(r=this.version_selector.selected)||void 0===r?void 0:r.getAttribute("architecture"))&&void 0!==s?s:void 0}this.sessionType=(null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("#session-type")).value;let f=(null===(n=this.shadowRoot)||void 0===n?void 0:n.querySelector("#session-name")).value;const g=(null===(a=this.shadowRoot)||void 0===a?void 0:a.querySelector("#session-name")).checkValidity();let v=this.selectedVfolders;if(this.cpu_request=parseInt(this.cpuResourceSlider.value),this.mem_request=parseFloat(this.memoryResourceSlider.value),this.shmem_request=parseFloat(this.sharedMemoryResourceSlider.value),this.gpu_request=parseFloat(this.npuResourceSlider.value),this.session_request=parseInt(this.sessionResourceSlider.value),this.num_sessions=this.session_request,this.sessions_list.includes(f))return this.notification.text=re("session.launcher.DuplicatedSessionName"),void this.notification.show();if(!g)return this.notification.text=re("session.launcher.SessionNameAllowCondition"),void this.notification.show();if(""===h||""===p||"Not Selected"===p)return this.notification.text=re("session.launcher.MustSpecifyVersion"),void this.notification.show();this.scaling_group=this.scalingGroups.value;const b={};b.group_name=globalThis.backendaiclient.current_group,b.domain=globalThis.backendaiclient._config.domainName,b.scaling_group=this.scaling_group,b.type=this.sessionType,globalThis.backendaiclient.supports("multi-container")&&(b.cluster_mode=this.cluster_mode,b.cluster_size=this.cluster_size),b.maxWaitSeconds=15;const _=null===(l=this.shadowRoot)||void 0===l?void 0:l.querySelector("#owner-enabled");if(_&&_.checked&&(b.group_name=this.ownerGroupSelect.value,b.domain=this.ownerDomain,b.scaling_group=this.ownerScalingGroupSelect.value,b.owner_access_key=this.ownerAccesskeySelect.value,!(b.group_name&&b.domain&&b.scaling_group&&b.owner_access_key)))return this.notification.text=re("session.launcher.NotEnoughOwnershipInfo"),void this.notification.show();switch(b.cpu=this.cpu_request,this.gpu_request_type){case"cuda.shares":b["cuda.shares"]=this.gpu_request;break;case"cuda.device":b["cuda.device"]=this.gpu_request;break;case"rocm.device":b["rocm.device"]=this.gpu_request;break;case"tpu.device":b["tpu.device"]=this.gpu_request;break;case"ipu.device":b["ipu.device"]=this.gpu_request;break;case"atom.device":b["atom.device"]=this.gpu_request;break;case"atom-plus.device":b["atom-plus.device"]=this.gpu_request;break;case"gaudi2.device":b["gaudi2.device"]=this.gpu_request;break;case"warboy.device":b["warboy.device"]=this.gpu_request;break;case"rngd.device":b["rngd.device"]=this.gpu_request;break;case"hyperaccel-lpu.device":b["hyperaccel-lpu.device"]=this.gpu_request;break;default:this.gpu_request>0&&this.gpu_mode&&(b[this.gpu_mode]=this.gpu_request)}let y;"Infinity"===String(this.memoryResourceSlider.value)?b.mem=String(this.memoryResourceSlider.value):b.mem=String(this.mem_request)+"g",this.shmem_request>this.mem_request&&(this.shmem_request=this.mem_request,this.notification.text=re("session.launcher.SharedMemorySettingIsReduced"),this.notification.show()),this.mem_request>4&&this.shmem_request<1&&(this.shmem_request=1),b.shmem=String(this.shmem_request)+"g",0==f.length&&(f=this.generateSessionId()),y=this._debug&&""!==this.manualImageName.value||this.manualImageName&&""!==this.manualImageName.value?m?h:this.manualImageName.value:this._generateKernelIndex(h,p);let x={};if("inference"===this.mode){if(!(y in this.resourceBroker.imageRuntimeConfig)||!("model-path"in this.resourceBroker.imageRuntimeConfig[y]))return this.notification.text=re("session.launcher.ImageDoesNotProvideModelPath"),void this.notification.show();v=Object.keys(this.customFolderMapping),x[v]=this.resourceBroker.imageRuntimeConfig[y]["model-path"]}else x=this.folderMapping;if(0!==v.length&&(b.mounts=v,0!==Object.keys(x).length)){b.mount_map={};for(const e in x)({}).hasOwnProperty.call(x,e)&&(x[e].startsWith("/")?b.mount_map[e]=x[e]:b.mount_map[e]="/home/work/"+x[e])}if("import"===this.mode&&""!==this.importScript&&(b.bootstrap_script=this.importScript),"batch"===this.sessionType&&(b.startupCommand=this.commandEditor.getValue(),this.scheduledTime&&(b.startsAt=this.scheduledTime)),this.environ_values&&0!==Object.keys(this.environ_values).length&&(b.env=this.environ_values),this.preOpenPorts.length>0&&(b.preopen_ports=[...new Set(this.preOpenPorts.map((e=>Number(e))))]),!1===this.openMPSwitch.selected){const e=(null===(c=this.shadowRoot)||void 0===c?void 0:c.querySelector("#OpenMPCore")).value,t=(null===(d=this.shadowRoot)||void 0===d?void 0:d.querySelector("#OpenBLASCore")).value;b.env=null!==(u=b.env)&&void 0!==u?u:{},b.env.OMP_NUM_THREADS=e?Math.max(0,parseInt(e)).toString():"1",b.env.OPENBLAS_NUM_THREADS=t?Math.max(0,parseInt(t)).toString():"1"}this.launchButton.disabled=!0,this.launchButtonMessageTextContent=re("session.Preparing"),this.notification.text=re("session.PreparingSession"),this.notification.show();const w=[],k=this._getRandomString();if(this.num_sessions>1)for(let e=1;e<=this.num_sessions;e++){const t={kernelName:y,sessionName:`${f}-${k}-${e}`,architecture:m,config:b};w.push(t)}else w.push({kernelName:y,sessionName:f,architecture:m,config:b});const C=w.map((e=>this.tasker.add(re("general.Session")+": "+e.sessionName,this._createKernel(e.kernelName,e.sessionName,e.architecture,e.config),"","session","",re("eduapi.CreatingComputeSession"),re("eduapi.ComputeSessionPrepared"),!0)));Promise.all(C).then((e=>{var t;this.newSessionDialog.hide(),this.launchButton.disabled=!1,this.launchButtonMessageTextContent=re("session.launcher.ConfirmAndLaunch"),this._resetProgress(),setTimeout((()=>{this.metadata_updating=!0,this.aggregateResource("session-creation"),this.metadata_updating=!1}),1500);const i=new CustomEvent("backend-ai-session-list-refreshed",{detail:"running"});document.dispatchEvent(i),1===e.length&&"batch"!==this.sessionType&&(null===(t=e[0])||void 0===t||t.taskobj.then((e=>{let t;t="kernelId"in e?{"session-name":e.kernelId,"access-key":"",mode:this.mode}:{"session-uuid":e.sessionId,"session-name":e.sessionName,"access-key":"",mode:this.mode};const i=e.servicePorts;!0===Array.isArray(i)?t["app-services"]=i.map((e=>e.name)):t["app-services"]=[],"import"===this.mode&&(t.runtime="jupyter",t.filename=this.importFilename),"inference"===this.mode&&(t.runtime=t["app-services"].find((e=>!["ttyd","sshd"].includes(e)))),i.length>0&&globalThis.appLauncher.showLauncher(t)})).catch((e=>{}))),this._updateSelectedFolder(!1),this._initializeFolderMapping()})).catch((e=>{e&&e.message?(this.notification.text=D.relieve(e.message),e.description?this.notification.text=D.relieve(e.description):this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=D.relieve(e.title),this.notification.show(!0,e));const t=new CustomEvent("backend-ai-session-list-refreshed",{detail:"running"});document.dispatchEvent(t),this.launchButton.disabled=!1,this.launchButtonMessageTextContent=re("session.launcher.ConfirmAndLaunch")}))}_getRandomString(){let e=Math.floor(52*Math.random()*52*52);let t="";for(let r=0;r<3;r++)t+=(i=e%52)<26?String.fromCharCode(65+i):String.fromCharCode(97+i-26),e=Math.floor(e/52);var i;return t}_createKernel(e,t,i,r){const s=globalThis.backendaiclient.createIfNotExists(e,t,r,3e4,i);return s.then((e=>{(null==e?void 0:e.created)||(this.notification.text=re("session.launcher.SessionAlreadyExists"),this.notification.show())})).catch((e=>{e&&e.message?("statusCode"in e&&408===e.statusCode?this.notification.text=re("session.launcher.SessionStillPreparing"):e.description?this.notification.text=D.relieve(e.description):this.notification.text=D.relieve(e.message),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=D.relieve(e.title),this.notification.show(!0,e))})),s}_hideSessionDialog(){this.newSessionDialog.hide()}_aliasName(e){const t=this.resourceBroker.imageTagAlias,i=this.resourceBroker.imageTagReplace;for(const[t,r]of Object.entries(i)){const i=new RegExp(t);if(i.test(e))return e.replace(i,r)}return e in t?t[e]:e}_updateVersions(e){if(e in this.resourceBroker.supports){{this.version_selector.disabled=!0;const t=[];for(const i of this.resourceBroker.supports[e])for(const r of this.resourceBroker.imageArchitectures[e+":"+i])t.push({version:i,architecture:r});t.sort(((e,t)=>e.version>t.version?1:-1)),t.reverse(),this.versions=t,this.kernel=e}return void 0!==this.versions?this.version_selector.layout(!0).then((()=>{this.version_selector.select(1),this.version_selector.value=this.versions[0].version,this.version_selector.architecture=this.versions[0].architecture,this._updateVersionSelectorText(this.version_selector.value,this.version_selector.architecture),this.version_selector.disabled=!1,this.environ_values={},this.updateResourceAllocationPane("update versions")})):void 0}}_updateVersionSelectorText(e,t){const i=this._getVersionInfo(e,t),r=[];i.forEach((e=>{""!==e.tag&&null!==e.tag&&r.push(e.tag)})),this.version_selector.selectedText=r.join(" / ")}generateSessionId(){let e="";const t="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";for(let i=0;i<8;i++)e+=t.charAt(Math.floor(62*Math.random()));return e+"-session"}async _updateVirtualFolderList(){return this.resourceBroker.updateVirtualFolderList().then((()=>{this.vfolders=this.resourceBroker.vfolders.filter((e=>"ready"===e.status))}))}async _aggregateResourceUse(e=""){return this.resourceBroker._aggregateCurrentResource(e).then((async e=>(this.concurrency_used=this.resourceBroker.concurrency_used,this.scaling_group=this.resourceBroker.scaling_group,this.scaling_groups=this.resourceBroker.scaling_groups,this.resource_templates=this.resourceBroker.resource_templates,this.resource_templates_filtered=this.resourceBroker.resource_templates_filtered,this.total_slot=this.resourceBroker.total_slot,this.total_resource_group_slot=this.resourceBroker.total_resource_group_slot,this.total_project_slot=this.resourceBroker.total_project_slot,this.used_slot=this.resourceBroker.used_slot,this.used_resource_group_slot=this.resourceBroker.used_resource_group_slot,this.used_project_slot=this.resourceBroker.used_project_slot,this.used_project_slot_percent=this.resourceBroker.used_project_slot_percent,this.concurrency_limit=this.resourceBroker.concurrency_limit&&this.resourceBroker.concurrency_limit>1?this.resourceBroker.concurrency_limit:1,this.available_slot=this.resourceBroker.available_slot,this.used_slot_percent=this.resourceBroker.used_slot_percent,this.used_resource_group_slot_percent=this.resourceBroker.used_resource_group_slot_percent,await this.updateComplete,Promise.resolve(!0)))).catch((e=>(e&&e.message&&(e.description?this.notification.text=D.relieve(e.description):this.notification.text=D.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)),Promise.resolve(!1))))}aggregateResource(e=""){void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._aggregateResourceUse(e)}),!0):this._aggregateResourceUse(e)}async updateResourceAllocationPane(e=""){var t,i;if(1==this.metric_updating)return;if("refresh resource policy"===e)return this.metric_updating=!1,this._aggregateResourceUse("update-metric").then((()=>this.updateResourceAllocationPane("after refresh resource policy")));const r=this.environment.selected,s=this.version_selector.selected;if(null===s)return void(this.metric_updating=!1);const o=s.value,n=s.getAttribute("architecture");if(this._updateVersionSelectorText(o,n),null==r||r.getAttribute("disabled"))this.metric_updating=!1;else if(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready)document.addEventListener("backend-ai-connected",(()=>{this.updateResourceAllocationPane(e)}),!0);else{if(this.metric_updating=!0,await this._aggregateResourceUse("update-metric"),await this._updateVirtualFolderList(),this.autoMountedVfolders=this.vfolders.filter((e=>e.name.startsWith("."))),this.enableInferenceWorkload?(this.modelVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")&&"model"===e.usage_mode)),this.nonAutoMountedVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")&&"general"===e.usage_mode))):this.nonAutoMountedVfolders=this.vfolders.filter((e=>!e.name.startsWith("."))),0===Object.keys(this.resourceBroker.resourceLimits).length)return void(this.metric_updating=!1);const e=r.id,s=o;if(""===e||""===s)return void(this.metric_updating=!1);const n=e+":"+s,a=this.resourceBroker.resourceLimits[n];if(!a)return void(this.metric_updating=!1);this.gpu_mode=this.resourceBroker.gpu_mode,this.gpu_step=this.resourceBroker.gpu_step,this.gpu_modes=this.resourceBroker.gpu_modes,globalThis.backendaiclient.supports("multi-container")&&this.cluster_size>1&&(this.gpu_step=1);const l=this.resourceBroker.available_slot;this.cpuResourceSlider.disabled=!1,this.memoryResourceSlider.disabled=!1,this.npuResourceSlider.disabled=!1,globalThis.backendaiclient.supports("multi-container")&&(this.cluster_size=1,this.clusterSizeSlider.value=this.cluster_size),this.sessionResourceSlider.disabled=!1,this.launchButton.disabled=!1,this.launchButtonMessageTextContent=re("session.launcher.ConfirmAndLaunch");let c=!1,d={min:.0625,max:2,preferred:.0625};if(this.npu_device_metric={min:0,max:0},a.forEach((e=>{if("cpu"===e.key){const t={...e};t.min=parseInt(t.min),["cpu","mem","cuda_device","cuda_shares","rocm_device","tpu_device","ipu_device","atom_device","atom_plus_device","gaudi2_device","warboy_device","rngd.device","hyperaccel_lpu_device"].forEach((e=>{e in this.total_resource_group_slot&&(l[e]=this.total_resource_group_slot[e])})),"cpu"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null===t.max?t.max=Math.min(parseInt(this.userResourceLimit.cpu),l.cpu,this.max_cpu_core_per_session):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit.cpu),l.cpu,this.max_cpu_core_per_session):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null===t.max?t.max=Math.min(this.available_slot.cpu,this.max_cpu_core_per_session):t.max=Math.min(parseInt(t.max),l.cpu,this.max_cpu_core_per_session),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.cpuResourceSlider.disabled=!0),this.cpu_metric=t,this.cluster_support&&"single-node"===this.cluster_mode&&(this.cluster_metric.max=Math.min(t.max,this.max_containers_per_session),this.cluster_metric.min>this.cluster_metric.max?this.cluster_metric.min=this.cluster_metric.max:this.cluster_metric.min=t.min)}if("cuda.device"===e.key&&"cuda.device"==this.gpu_mode){const t={...e};t.min=parseInt(t.min),"cuda.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["cuda.device"]),parseInt(l.cuda_device),this.max_cuda_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["cuda.device"]),l.cuda_device,this.max_cuda_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.cuda_device),this.max_cuda_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.cuda_device),this.max_cuda_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this.npu_device_metric=t,this._NPUDeviceNameOnSlider="GPU"}if("cuda.shares"===e.key&&"cuda.shares"===this.gpu_mode){const t={...e};t.min=parseFloat(t.min),"cuda.shares"in this.userResourceLimit?0===parseFloat(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseFloat(this.userResourceLimit["cuda.shares"]),parseFloat(l.cuda_shares),this.max_cuda_shares_per_container):t.max=Math.min(parseFloat(t.max),parseFloat(this.userResourceLimit["cuda.shares"]),parseFloat(l.cuda_shares),this.max_cuda_shares_per_container):0===parseFloat(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseFloat(l.cuda_shares),this.max_cuda_shares_per_container):t.max=Math.min(parseFloat(t.max),parseFloat(l.cuda_shares),this.max_cuda_shares_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this.cuda_shares_metric=t,t.max>0&&(this.npu_device_metric=t),this._NPUDeviceNameOnSlider="GPU"}if("rocm.device"===e.key&&"rocm.device"===this.gpu_mode){const t={...e};t.min=parseInt(t.min),t.max=parseInt(t.max),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this.npu_device_metric=t,this._NPUDeviceNameOnSlider="GPU"}if("tpu.device"===e.key){const t={...e};t.min=parseInt(t.min),"tpu.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["tpu.device"]),parseInt(l.tpu_device),this.max_tpu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["tpu.device"]),l.tpu_device,this.max_tpu_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.tpu_device),this.max_tpu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.tpu_device),this.max_tpu_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this.npu_device_metric=t,this._NPUDeviceNameOnSlider="TPU"}if("ipu.device"===e.key){const t={...e};t.min=parseInt(t.min),"ipu.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["ipu.device"]),parseInt(l.ipu_device),this.max_ipu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["ipu.device"]),l.ipu_device,this.max_ipu_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.ipu_device),this.max_ipu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.ipu_device),this.max_ipu_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this.npu_device_metric=t,this._NPUDeviceNameOnSlider="IPU"}if("atom.device"===e.key){const t={...e};t.min=parseInt(t.min),"atom.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["atom.device"]),parseInt(l.atom_device),this.max_atom_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["atom.device"]),l.atom_device,this.max_atom_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.atom_device),this.max_atom_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.atom_device),this.max_atom_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="ATOM",this.npu_device_metric=t}if("atom-plus.device"===e.key){const t={...e};t.min=parseInt(t.min),"atom-plus.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["atom-plus.device"]),parseInt(l.atom_plus_device),this.max_atom_plus_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["atom-plus.device"]),l.atom_plus_device,this.max_atom_plus_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.atom_plus_device),this.max_atom_plus_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.atom_plus_device),this.max_atom_plus_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="ATOM+",this.npu_device_metric=t}if("gaudi2.device"===e.key){const t={...e};t.min=parseInt(t.min),"gaudi2.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["gaudi2.device"]),parseInt(l.gaudi2_device),this.max_gaudi2_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["gaudi2.device"]),l.gaudi2_device,this.max_gaudi2_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.gaudi2_device),this.max_gaudi2_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.gaudi2_device),this.max_gaudi2_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="Gaudi 2",this.npu_device_metric=t}if("warboy.device"===e.key){const t={...e};t.min=parseInt(t.min),"warboy.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["warboy.device"]),parseInt(l.cuda_device),this.max_cuda_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["warboy.device"]),l.cuda_device,this.max_cuda_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.warboy_device),this.max_warboy_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.warboy_device),this.max_warboy_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="Warboy",this.npu_device_metric=t}if("rngd.device"===e.key){const t={...e};t.min=parseInt(t.min),"rngd.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["rngd.device"]),parseInt(l.cuda_device),this.max_cuda_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["rngd.device"]),l.cuda_device,this.max_cuda_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.rngd_device),this.max_rngd_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.rngd_device),this.max_rngd_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="RNGD",this.npu_device_metric=t}if("hyperaccel-lpu.device"===e.key){const t={...e};t.min=parseInt(t.min),"hyperaccel-lpu.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["hyperaccel-lpu.device"]),parseInt(l.hyperaccel_lpu_device),this.max_hyperaccel_lpu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["hyperaccel-lpu.device"]),l.hyperaccel_lpu_device,this.max_hyperaccel_lpu_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.hyperaccel_lpu_device),this.max_hyperaccel_lpu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.hyperaccel_lpu_device),this.max_hyperaccel_lpu_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="Hyperaccel LPU",this.npu_device_metric=t}if("mem"===e.key){const t={...e};t.min=globalThis.backendaiclient.utils.changeBinaryUnit(t.min,"g"),t.min<.1&&(t.min=.1),t.max||(t.max=0);const i=globalThis.backendaiclient.utils.changeBinaryUnit(t.max,"g","g");if("mem"in this.userResourceLimit){const e=globalThis.backendaiclient.utils.changeBinaryUnit(this.userResourceLimit.mem,"g");isNaN(parseInt(i))||0===parseInt(i)?t.max=Math.min(parseFloat(e),l.mem,this.max_mem_per_container):t.max=Math.min(parseFloat(i),parseFloat(e),l.mem,this.max_mem_per_container)}else 0!==parseInt(t.max)&&"Infinity"!==t.max&&!0!==isNaN(t.max)?t.max=Math.min(parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(t.max,"g","g")),l.mem,this.max_mem_per_container):t.max=Math.min(l.mem,this.max_mem_per_container);t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.memoryResourceSlider.disabled=!0),t.min=Number(t.min.toFixed(2)),t.max=Number(t.max.toFixed(2)),this.mem_metric=t}"shmem"===e.key&&(d={...e},d.preferred="preferred"in d?globalThis.backendaiclient.utils.changeBinaryUnit(d.preferred,"g","g"):.0625)})),d.max=this.max_shm_per_container,d.min=.0625,d.min>=d.max&&(d.min>d.max&&(d.min=d.max,c=!0),this.sharedMemoryResourceSlider.disabled=!0),d.min=Number(d.min.toFixed(2)),d.max=Number(d.max.toFixed(2)),this.shmem_metric=d,0==this.npu_device_metric.min&&0==this.npu_device_metric.max)if(this.npuResourceSlider.disabled=!0,this.npuResourceSlider.value=0,this.resource_templates.length>0){const e=[];for(let t=0;t<this.resource_templates.length;t++)"cuda_device"in this.resource_templates[t]||"cuda_shares"in this.resource_templates[t]?(parseFloat(this.resource_templates[t].cuda_device)<=0&&!("cuda_shares"in this.resource_templates[t])||parseFloat(this.resource_templates[t].cuda_shares)<=0&&!("cuda_device"in this.resource_templates[t])||parseFloat(this.resource_templates[t].cuda_device)<=0&&parseFloat(this.resource_templates[t].cuda_shares)<=0)&&e.push(this.resource_templates[t]):e.push(this.resource_templates[t]);this.resource_templates_filtered=e}else this.resource_templates_filtered=this.resource_templates;else this.npuResourceSlider.disabled=!1,this.npuResourceSlider.value=this.npu_device_metric.max,this.resource_templates_filtered=this.resource_templates;if(this.resource_templates_filtered.length>0){const e=this.resource_templates_filtered[0];this._chooseResourceTemplate(e),this.resourceTemplatesSelect.layout(!0).then((()=>this.resourceTemplatesSelect.layoutOptions())).then((()=>{this.resourceTemplatesSelect.select(1)}))}else this._updateResourceIndicator(this.cpu_metric.min,this.mem_metric.min,"none",0);c?(this.cpuResourceSlider.disabled=!0,this.memoryResourceSlider.disabled=!0,this.npuResourceSlider.disabled=!0,this.sessionResourceSlider.disabled=!0,this.sharedMemoryResourceSlider.disabled=!0,this.launchButton.disabled=!0,(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector(".allocation-check")).style.display="none",this.cluster_support&&(this.clusterSizeSlider.disabled=!0),this.launchButtonMessageTextContent=re("session.launcher.NotEnoughResource")):(this.cpuResourceSlider.disabled=!1,this.memoryResourceSlider.disabled=!1,this.npuResourceSlider.disabled=!1,this.sessionResourceSlider.disabled=!1,this.sharedMemoryResourceSlider.disabled=!1,this.launchButton.disabled=!1,(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector(".allocation-check")).style.display="flex",this.cluster_support&&(this.clusterSizeSlider.disabled=!1)),this.npu_device_metric.min==this.npu_device_metric.max&&this.npu_device_metric.max<1&&(this.npuResourceSlider.disabled=!0),this.concurrency_limit<=1&&(this.sessionResourceSlider.min=1,this.sessionResourceSlider.max=2,this.sessionResourceSlider.value=1,this.sessionResourceSlider.disabled=!0),this.max_containers_per_session<=1&&"single-node"===this.cluster_mode&&(this.clusterSizeSlider.min=1,this.clusterSizeSlider.max=2,this.clusterSizeSlider.value=1,this.clusterSizeSlider.disabled=!0),this.metric_updating=!1}}updateLanguage(){const e=this.environment.selected;if(null===e)return;const t=e.id;this._updateVersions(t)}folderToMountListRenderer(e,t,i){ne(d`
        <div style="font-size:14px;text-overflow:ellipsis;overflow:hidden;">
          ${i.item.name}
        </div>
        <span style="font-size:10px;">${i.item.host}</span>
      `,e)}folderMapRenderer(e,t,i){ne(d`
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
      `,e)}infoHeaderRenderer(e,t){ne(d`
        <div class="horizontal layout center">
          <span id="vfolder-header-title">
            ${O("session.launcher.FolderAlias")}
          </span>
          <mwc-icon-button
            icon="info"
            class="fg green info"
            @click="${e=>this._showPathDescription(e)}"
          ></mwc-icon-button>
        </div>
      `,e)}_showPathDescription(e){null!=e&&e.stopPropagation(),this._helpDescriptionTitle=re("session.launcher.FolderAlias"),this._helpDescription=re("session.launcher.DescFolderAlias"),this._helpDescriptionIcon="",this.helpDescriptionDialog.show()}helpDescTagCount(e){let t=0;let i=e.indexOf(e);for(;-1!==i;)t++,i=e.indexOf("<p>",i+1);return t}setPathContent(e,t){var i;const r=e.children[e.children.length-1],s=r.children[r.children.length-1];if(s.children.length<t+1){const e=document.createElement("div");e.setAttribute("class","horizontal layout flex center");const t=document.createElement("mwc-checkbox");t.setAttribute("id","hide-guide");const r=document.createElement("span");r.append(document.createTextNode(`${re("dialog.hide.DoNotShowThisAgain")}`)),e.appendChild(t),e.appendChild(r),s.appendChild(e);const o=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#hide-guide");null==o||o.addEventListener("change",(e=>{if(null!==e.target){e.stopPropagation();e.target.checked?localStorage.setItem("backendaiwebui.pathguide","false"):localStorage.setItem("backendaiwebui.pathguide","true")}}))}}async _updateFolderMap(e,t){var i,r;if(""===t)return e in this.folderMapping&&delete this.folderMapping[e],await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!0);if(e!==t){if(this.selectedVfolders.includes(t))return this.notification.text=re("session.launcher.FolderAliasOverlapping"),this.notification.show(),delete this.folderMapping[e],(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#vfolder-alias-"+e)).value="",await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!1);for(const i in this.folderMapping)if({}.hasOwnProperty.call(this.folderMapping,i)&&this.folderMapping[i]==t)return this.notification.text=re("session.launcher.FolderAliasOverlapping"),this.notification.show(),delete this.folderMapping[e],(null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector("#vfolder-alias-"+e)).value="",await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!1);return this.folderMapping[e]=t,await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!0)}return Promise.resolve(!0)}changed(e){console.log(e)}isEmpty(e){return 0===e.length}_toggleAdvancedSettings(){var e;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#advanced-resource-settings")).toggle()}_setClusterMode(e){this.cluster_mode=e.target.value}_setClusterSize(e){this.cluster_size=e.target.value>0?Math.round(e.target.value):0,this.clusterSizeSlider.value=this.cluster_size;let t=1;globalThis.backendaiclient.supports("multi-container")&&(this.cluster_size>1||(t=0),this.gpu_step=this.resourceBroker.gpu_step,this._setSessionLimit(t))}_setSessionLimit(e=1){e>0?(this.sessionResourceSlider.value=e,this.session_request=e,this.sessionResourceSlider.disabled=!0):(this.sessionResourceSlider.max=this.concurrency_limit,this.sessionResourceSlider.disabled=!1)}_chooseResourceTemplate(e){var t;let i;i=void 0!==(null==e?void 0:e.cpu)?e:null===(t=e.target)||void 0===t?void 0:t.closest("mwc-list-item");const r=i.cpu,s=i.mem,o=i.cuda_device,n=i.cuda_shares,a=i.rocm_device,l=i.tpu_device,c=i.ipu_device,d=i.atom_device,u=i.atom_plus_device,h=i.gaudi2_device,p=i.warboy_device,m=i.rngd_device,f=i.hyperaccel_lpu_device;let g,v;void 0!==o&&Number(o)>0||void 0!==n&&Number(n)>0?void 0===n?(g="cuda.device",v=o):(g="cuda.shares",v=n):void 0!==a&&Number(a)>0?(g="rocm.device",v=a):void 0!==l&&Number(l)>0?(g="tpu.device",v=l):void 0!==c&&Number(c)>0?(g="ipu.device",v=c):void 0!==d&&Number(d)>0?(g="atom.device",v=d):void 0!==u&&Number(u)>0?(g="atom-plus.device",v=u):void 0!==h&&Number(h)>0?(g="gaudi2.device",v=h):void 0!==p&&Number(p)>0?(g="warboy.device",v=p):void 0!==m&&Number(m)>0?(g="rngd.device",v=m):void 0!==f&&Number(f)>0?(g="hyperaccel-lpu.device",v=f):(g="none",v=0);const b=i.shmem?i.shmem:this.shmem_metric;this.shmem_request="number"!=typeof b?b.preferred:b||.0625,this._updateResourceIndicator(r,s,g,v)}_updateResourceIndicator(e,t,i,r){this.cpuResourceSlider.value=e,this.memoryResourceSlider.value=t,this.npuResourceSlider.value=r,this.sharedMemoryResourceSlider.value=this.shmem_request,this.cpu_request=e,this.mem_request=t,this.gpu_request=r,this.gpu_request_type=i}async selectDefaultLanguage(e=!1,t=""){if(!0===this._default_language_updated&&!1===e)return;""!==t?this.default_language=t:void 0!==globalThis.backendaiclient._config.default_session_environment&&"default_session_environment"in globalThis.backendaiclient._config&&""!==globalThis.backendaiclient._config.default_session_environment?this.languages.map((e=>e.name)).includes(globalThis.backendaiclient._config.default_session_environment)?this.default_language=globalThis.backendaiclient._config.default_session_environment:""!==this.languages[0].name?this.default_language=this.languages[0].name:this.default_language=this.languages[1].name:this.languages.length>1?this.default_language=this.languages[1].name:0!==this.languages.length?this.default_language=this.languages[0].name:this.default_language="index.docker.io/lablup/ngc-tensorflow";const i=this.environment.items.find((e=>e.value===this.default_language));if(void 0===i&&void 0!==globalThis.backendaiclient&&!1===globalThis.backendaiclient.ready)return setTimeout((()=>(console.log("Environment selector is not ready yet. Trying to set the default language again."),this.selectDefaultLanguage(e,t))),500),Promise.resolve(!0);const r=this.environment.items.indexOf(i);return this.environment.select(r),this._default_language_updated=!0,Promise.resolve(!0)}_selectDefaultVersion(e){return!1}async _fetchSessionOwnerGroups(){var e;this.ownerFeatureInitialized||(this.ownerGroupSelect.addEventListener("selected",this._fetchSessionOwnerScalingGroups.bind(this)),this.ownerFeatureInitialized=!0);const t=this.ownerEmailInput.value;if(!this.ownerEmailInput.checkValidity()||""===t||void 0===t)return this.notification.text=re("credential.validation.InvalidEmailAddress"),this.notification.show(),this.ownerKeypairs=[],void(this.ownerGroups=[]);const i=await globalThis.backendaiclient.keypair.list(t,["access_key"]),r=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#owner-enabled");if(this.ownerKeypairs=i.keypairs,this.ownerKeypairs.length<1)return this.notification.text=re("session.launcher.NoActiveKeypair"),this.notification.show(),r.checked=!1,r.disabled=!0,this.ownerKeypairs=[],void(this.ownerGroups=[]);this.ownerAccesskeySelect.layout(!0).then((()=>{this.ownerAccesskeySelect.select(0),this.ownerAccesskeySelect.createAdapter().setSelectedText(this.ownerKeypairs[0].access_key)}));try{const e=await globalThis.backendaiclient.user.get(t,["domain_name","groups {id name}"]);this.ownerDomain=e.user.domain_name,this.ownerGroups=e.user.groups}catch(e){return this.notification.text=re("session.launcher.NotEnoughOwnershipInfo"),void this.notification.show()}this.ownerGroups.length&&this.ownerGroupSelect.layout(!0).then((()=>{this.ownerGroupSelect.select(0),this.ownerGroupSelect.createAdapter().setSelectedText(this.ownerGroups[0].name)})),r.disabled=!1}async _fetchSessionOwnerScalingGroups(){const e=this.ownerGroupSelect.value;if(!e)return void(this.ownerScalingGroups=[]);const t=await globalThis.backendaiclient.scalingGroup.list(e);this.ownerScalingGroups=t.scaling_groups,this.ownerScalingGroups&&this.ownerScalingGroupSelect.layout(!0).then((()=>{this.ownerScalingGroupSelect.select(0),this.ownerGroupSelect.createAdapter().setSelectedText(this.ownerScalingGroups[0].name)}))}async _fetchDelegatedSessionVfolder(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#owner-enabled"),i=this.ownerEmailInput.value;this.ownerKeypairs.length>0&&t&&t.checked?(await this.resourceBroker.updateVirtualFolderList(i),this.vfolders=this.resourceBroker.vfolders):await this._updateVirtualFolderList(),this.autoMountedVfolders=this.vfolders.filter((e=>e.name.startsWith("."))),this.enableInferenceWorkload?(this.modelVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")&&"model"===e.usage_mode)),this.nonAutoMountedVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")&&"general"===e.usage_mode))):this.nonAutoMountedVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")))}_toggleResourceGauge(){""==this.resourceGauge.style.display||"flex"==this.resourceGauge.style.display||"block"==this.resourceGauge.style.display?this.resourceGauge.style.display="none":(document.body.clientWidth<750?(this.resourceGauge.style.left="20px",this.resourceGauge.style.right="20px",this.resourceGauge.style.backgroundColor="var(--paper-red-800)"):this.resourceGauge.style.backgroundColor="transparent",this.resourceGauge.style.display="flex")}_showKernelDescription(e,t){e.stopPropagation();const i=t.kernelname;i in this.resourceBroker.imageInfo&&"description"in this.resourceBroker.imageInfo[i]?(this._helpDescriptionTitle=this.resourceBroker.imageInfo[i].name,this._helpDescription=this.resourceBroker.imageInfo[i].description||re("session.launcher.NoDescriptionFound"),this._helpDescriptionIcon=t.icon,this.helpDescriptionDialog.show()):(i in this.imageInfo?this._helpDescriptionTitle=this.resourceBroker.imageInfo[i].name:this._helpDescriptionTitle=i,this._helpDescription=re("session.launcher.NoDescriptionFound"))}_showResourceDescription(e,t){e.stopPropagation();const i={cpu:{name:re("session.launcher.CPU"),desc:re("session.launcher.DescCPU")},mem:{name:re("session.launcher.Memory"),desc:re("session.launcher.DescMemory")},shmem:{name:re("session.launcher.SharedMemory"),desc:`${re("session.launcher.DescSharedMemory")} <br /> <br /> ${re("session.launcher.DescSharedMemoryContext")}`},gpu:{name:re("session.launcher.AIAccelerator"),desc:re("session.launcher.DescAIAccelerator")},session:{name:re("session.launcher.TitleSession"),desc:re("session.launcher.DescSession")},"single-node":{name:re("session.launcher.SingleNode"),desc:re("session.launcher.DescSingleNode")},"multi-node":{name:re("session.launcher.MultiNode"),desc:re("session.launcher.DescMultiNode")},"openmp-optimization":{name:re("session.launcher.OpenMPOptimization"),desc:re("session.launcher.DescOpenMPOptimization")}};t in i&&(this._helpDescriptionTitle=i[t].name,this._helpDescription=i[t].desc,this._helpDescriptionIcon="",this.helpDescriptionDialog.show())}_showEnvConfigDescription(e){e.stopPropagation(),this._helpDescriptionTitle=re("session.launcher.EnvironmentVariableTitle"),this._helpDescription=re("session.launcher.DescSetEnv"),this._helpDescriptionIcon="",this.helpDescriptionDialog.show()}_showPreOpenPortConfigDescription(e){e.stopPropagation(),this._helpDescriptionTitle=re("session.launcher.PreOpenPortTitle"),this._helpDescription=re("session.launcher.DescSetPreOpenPort"),this._helpDescriptionIcon="",this.helpDescriptionDialog.show()}_resourceTemplateToCustom(){this.resourceTemplatesSelect.selectedText=re("session.launcher.CustomResourceApplied"),this._updateResourceIndicator(this.cpu_request,this.mem_request,this.gpu_mode,this.gpu_request)}_applyResourceValueChanges(e,t=!0){const i=e.target.value;switch(e.target.id.split("-")[0]){case"cpu":this.cpu_request=i;break;case"mem":this.mem_request=i;break;case"shmem":this.shmem_request=i;break;case"gpu":this.gpu_request=i;break;case"session":this.session_request=i;break;case"cluster":this._changeTotalAllocationPane()}this.requestUpdate(),t?this._resourceTemplateToCustom():this._setClusterSize(e)}_changeTotalAllocationPane(){var e,t;this._deleteAllocationPaneShadow();const i=this.clusterSizeSlider.value;if(i>1){const r=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#resource-allocated-box-shadow");for(let e=0;e<=Math.min(5,i-1);e+=1){const t=document.createElement("div");t.classList.add("horizontal","layout","center","center-justified","resource-allocated-box","allocation-shadow"),t.style.position="absolute",t.style.top="-"+(5+5*e)+"px",t.style.left=5+5*e+"px";const i=this.isDarkMode?88-2*e:245+2*e;t.style.backgroundColor="rgb("+i+","+i+","+i+")",t.style.borderColor=this.isDarkMode?"none":"rgb("+(i-10)+","+(i-10)+","+(i-10)+")",t.style.zIndex=(6-e).toString(),r.appendChild(t)}(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#total-allocation-pane")).appendChild(r)}}_deleteAllocationPaneShadow(){var e;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#resource-allocated-box-shadow")).innerHTML=""}_updateShmemLimit(){const e=parseFloat(this.memoryResourceSlider.value);let t=this.sharedMemoryResourceSlider.value;parseFloat(t)>e?(t=e,this.shmem_request=t,this.sharedMemoryResourceSlider.value=t,this.sharedMemoryResourceSlider.max=t,this.notification.text=re("session.launcher.SharedMemorySettingIsReduced"),this.notification.show()):this.max_shm_per_container>t&&(this.sharedMemoryResourceSlider.max=e>this.max_shm_per_container?this.max_shm_per_container:e)}_roundResourceAllocation(e,t){return parseFloat(e).toFixed(t)}_conditionalGiBtoMiB(e){return e<1?this._roundResourceAllocation((1024*e).toFixed(0),2):this._roundResourceAllocation(e,2)}_conditionalGiBtoMiBunit(e){return e<1?"MiB":"GiB"}_getVersionInfo(e,t){const i=[],r=e.split("-");if(i.push({tag:this._aliasName(r[0]),color:"blue",size:"60px"}),r.length>1&&(this.kernel+":"+e in this.imageRequirements&&"framework"in this.imageRequirements[this.kernel+":"+e]?i.push({tag:this.imageRequirements[this.kernel+":"+e].framework,color:"red",size:"110px"}):i.push({tag:this._aliasName(r[1]),color:"red",size:"110px"})),i.push({tag:t,color:"lightgreen",size:"90px"}),r.length>2){let e=this._aliasName(r.slice(2).join("-"));e=e.split(":"),e.length>1?i.push({tag:e.slice(1).join(":"),app:e[0],color:"green",size:"110px"}):i.push({tag:e[0],color:"green",size:"110px"})}return i}_disableEnterKey(){var e;null===(e=this.shadowRoot)||void 0===e||e.querySelectorAll("lablup-expansion").forEach((e=>{e.onkeydown=e=>{"Enter"===e.key&&e.preventDefault()}}))}_validateInput(e){const t=e.target.closest("mwc-textfield");t.value&&(t.value=Math.round(t.value),t.value=globalThis.backendaiclient.utils.clamp(t.value,t.min,t.max))}_validateSessionName(){this.sessionName.validityTransform=(e,t)=>{if(t.valid){const t=!this.resourceBroker.sessions_list.includes(e);return t||(this.sessionName.validationMessage=re("session.launcher.DuplicatedSessionName")),{valid:t,customError:!t}}return t.patternMismatch?(this.sessionName.validationMessage=re("session.launcher.SessionNameAllowCondition"),{valid:t.valid,patternMismatch:!t.valid}):(this.sessionName.validationMessage=re("session.validation.EnterValidSessionName"),{valid:t.valid,customError:!t.valid})}}_appendEnvRow(e="",t=""){var i,r;const s=null===(i=this.modifyEnvContainer)||void 0===i?void 0:i.children[this.modifyEnvContainer.children.length-1],o=this._createEnvRow(e,t);null===(r=this.modifyEnvContainer)||void 0===r||r.insertBefore(o,s)}_appendPreOpenPortRow(e=null){var t,i;const r=null===(t=this.modifyPreOpenPortContainer)||void 0===t?void 0:t.children[this.modifyPreOpenPortContainer.children.length-1],s=this._createPreOpenPortRow(e);null===(i=this.modifyPreOpenPortContainer)||void 0===i||i.insertBefore(s,r),this._updateisExceedMaxCountForPreopenPorts()}_createEnvRow(e="",t=""){const i=document.createElement("div");i.setAttribute("class","horizontal layout center row");const r=document.createElement("mwc-textfield");r.setAttribute("value",e);const s=document.createElement("mwc-textfield");s.setAttribute("value",t);const o=document.createElement("mwc-icon-button");return o.setAttribute("icon","remove"),o.setAttribute("class","green minus-btn"),o.addEventListener("click",(e=>this._removeEnvItem(e))),i.append(r),i.append(s),i.append(o),i}_createPreOpenPortRow(e){const t=document.createElement("div");t.setAttribute("class","horizontal layout center row");const i=document.createElement("mwc-textfield");e&&i.setAttribute("value",e),i.setAttribute("type","number"),i.setAttribute("min","1024"),i.setAttribute("max","65535");const r=document.createElement("mwc-icon-button");return r.setAttribute("icon","remove"),r.setAttribute("class","green minus-btn"),r.addEventListener("click",(e=>this._removePreOpenPortItem(e))),t.append(i),t.append(r),t}_removeEnvItem(e){e.target.parentNode.remove()}_removePreOpenPortItem(e){e.target.parentNode.remove(),this._updateisExceedMaxCountForPreopenPorts()}_removeEmptyEnv(){var e;const t=null===(e=this.modifyEnvContainer)||void 0===e?void 0:e.querySelectorAll(".row");Array.prototype.filter.call(t,(e=>(e=>2===Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>""===e.value)).length)(e))).map(((e,t)=>{(0!==t||this.environ.length>0)&&e.parentNode.removeChild(e)}))}_removeEmptyPreOpenPorts(){var e;const t=null===(e=this.modifyPreOpenPortContainer)||void 0===e?void 0:e.querySelectorAll(".row:not(.header)");Array.prototype.filter.call(t,(e=>(e=>1===Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>""===e.value)).length)(e))).map(((e,t)=>{(0!==t||this.preOpenPorts.length>0)&&e.parentNode.removeChild(e)})),this._updateisExceedMaxCountForPreopenPorts()}modifyEnv(){this._parseEnvVariableList(),this._saveEnvVariableList(),this.modifyEnvDialog.closeWithConfirmation=!1,this.modifyEnvDialog.hide(),this.notification.text=re("session.launcher.EnvironmentVariableConfigurationDone"),this.notification.show()}modifyPreOpenPorts(){var e;const t=null===(e=this.modifyPreOpenPortContainer)||void 0===e?void 0:e.querySelectorAll(".row:not(.header) mwc-textfield");if(!(0===Array.from(t).filter((e=>!e.checkValidity())).length))return this.notification.text=re("session.launcher.PreOpenPortRange"),void this.notification.show();this._parseAndSavePreOpenPortList(),this.modifyPreOpenPortDialog.closeWithConfirmation=!1,this.modifyPreOpenPortDialog.hide(),this.notification.text=re("session.launcher.PreOpenPortConfigurationDone"),this.notification.show()}_loadEnv(){this.environ.forEach((e=>{this._appendEnvRow(e.name,e.value)}))}_loadPreOpenPorts(){this.preOpenPorts.forEach((e=>{this._appendPreOpenPortRow(e)}))}_showEnvDialog(){this._removeEmptyEnv(),this.modifyEnvDialog.closeWithConfirmation=!0,this.modifyEnvDialog.show()}_showPreOpenPortDialog(){this._removeEmptyPreOpenPorts(),this.modifyPreOpenPortDialog.closeWithConfirmation=!0,this.modifyPreOpenPortDialog.show()}_closeAndResetEnvInput(){this._clearEnvRows(!0),this.closeDialog("env-config-confirmation"),this.hideEnvDialog&&(this._loadEnv(),this.modifyEnvDialog.closeWithConfirmation=!1,this.modifyEnvDialog.hide())}_closeAndResetPreOpenPortInput(){this._clearPreOpenPortRows(!0),this.closeDialog("preopen-ports-config-confirmation"),this.hidePreOpenPortDialog&&(this._loadPreOpenPorts(),this.modifyPreOpenPortDialog.closeWithConfirmation=!1,this.modifyPreOpenPortDialog.hide())}_parseEnvVariableList(){var e;this.environ_values={};const t=null===(e=this.modifyEnvContainer)||void 0===e?void 0:e.querySelectorAll(".row:not(.header)"),i=e=>{const t=Array.prototype.map.call(e.querySelectorAll("mwc-textfield"),(e=>e.value));return this.environ_values[t[0]]=t[1],t};Array.prototype.filter.call(t,(e=>(e=>0===Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>0===e.value.length)).length)(e))).map((e=>i(e)))}_saveEnvVariableList(){this.environ=Object.entries(this.environ_values).map((([e,t])=>({name:e,value:t})))}_parseAndSavePreOpenPortList(){var e;const t=null===(e=this.modifyPreOpenPortContainer)||void 0===e?void 0:e.querySelectorAll(".row:not(.header) mwc-textfield");this.preOpenPorts=Array.from(t).filter((e=>""!==e.value)).map((e=>e.value))}_resetEnvironmentVariables(){this.environ=[],this.environ_values={},null!==this.modifyEnvDialog&&this._clearEnvRows(!0)}_resetPreOpenPorts(){this.preOpenPorts=[],null!==this.modifyPreOpenPortDialog&&this._clearPreOpenPortRows(!0)}_clearEnvRows(e=!1){var t;const i=null===(t=this.modifyEnvContainer)||void 0===t?void 0:t.querySelectorAll(".row"),r=i[0];if(!e){const e=e=>Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>e.value.length>0)).length>0;if(Array.prototype.filter.call(i,(t=>e(t))).length>0)return this.hideEnvDialog=!1,void this.openDialog("env-config-confirmation")}null==r||r.querySelectorAll("mwc-textfield").forEach((e=>{e.value=""})),i.forEach(((e,t)=>{0!==t&&e.remove()}))}_clearPreOpenPortRows(e=!1){var t;const i=null===(t=this.modifyPreOpenPortContainer)||void 0===t?void 0:t.querySelectorAll(".row"),r=i[0];if(!e){const e=e=>Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>e.value.length>0)).length>0;if(Array.prototype.filter.call(i,(t=>e(t))).length>0)return this.hidePreOpenPortDialog=!1,void this.openDialog("preopen-ports-config-confirmation")}null==r||r.querySelectorAll("mwc-textfield").forEach((e=>{e.value=""})),i.forEach(((e,t)=>{0!==t&&e.remove()}))}openDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).show()}closeDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).hide()}validateSessionLauncherInput(){if(1===this.currentIndex){const e="batch"!==this.sessionType||this.commandEditor._validateInput(),t="batch"!==this.sessionType||!this.scheduledTime||new Date(this.scheduledTime).getTime()>(new Date).getTime(),i=this.sessionName.checkValidity();if(!e||!t||!i)return!1}return!0}async moveProgress(e){var t,i,r,s;if(!this.validateSessionLauncherInput())return;const o=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#progress-0"+this.currentIndex);this.currentIndex+=e,"inference"===this.mode&&2==this.currentIndex&&(this.currentIndex+=e),this.currentIndex>this.progressLength&&(this.currentIndex=globalThis.backendaiclient.utils.clamp(this.currentIndex+e,this.progressLength,1));const n=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#progress-0"+this.currentIndex);o.classList.remove("active"),n.classList.add("active"),this.prevButton.style.visibility=1==this.currentIndex?"hidden":"visible",this.nextButton.style.visibility=this.currentIndex==this.progressLength?"hidden":"visible",this.launchButton.disabled||(this.launchButtonMessageTextContent=this.progressLength==this.currentIndex?re("session.launcher.Launch"):re("session.launcher.ConfirmAndLaunch")),null===(r=this._nonAutoMountedFolderGrid)||void 0===r||r.clearCache(),null===(s=this._modelFolderGrid)||void 0===s||s.clearCache(),2===this.currentIndex&&(await this._fetchDelegatedSessionVfolder(),this._checkSelectedItems())}_resetProgress(){this.moveProgress(1-this.currentIndex),this._resetEnvironmentVariables(),this._resetPreOpenPorts(),this._unselectAllSelectedFolder(),this._deleteAllocationPaneShadow()}_calculateProgress(){const e=this.progressLength>0?this.progressLength:1;return((this.currentIndex>0?this.currentIndex:1)/e).toFixed(2)}_acceleratorName(e){const t={"cuda.device":"GPU","cuda.shares":"GPU","rocm.device":"GPU","tpu.device":"TPU","ipu.device":"IPU","atom.device":"ATOM","atom-plus.device":"ATOM+","gaudi2.device":"Gaudi 2","warboy.device":"Warboy","rngd.device":"RNGD","hyperaccel-lpu.device":"Hyperaccel LPU"};return e in t?t[e]:"GPU"}_toggleEnvironmentSelectUI(){var e;const t=!!(null===(e=this.manualImageName)||void 0===e?void 0:e.value);this.environment.disabled=this.version_selector.disabled=t;const i=t?-1:1;this.environment.select(i),this.version_selector.select(i)}_toggleHPCOptimization(){var e;const t=this.openMPSwitch.selected;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#HPCOptimizationOptions")).style.display=t?"none":"block"}_toggleStartUpCommandEditor(e){var t;this.sessionType=e.target.value;const i="batch"===this.sessionType;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#batch-mode-config-section")).style.display=i?"inline-flex":"none",i&&(this.commandEditor.refresh(),this.commandEditor.focus())}_updateisExceedMaxCountForPreopenPorts(){var e,t,i;const r=null!==(i=null===(t=null===(e=this.modifyPreOpenPortContainer)||void 0===e?void 0:e.querySelectorAll("mwc-textfield"))||void 0===t?void 0:t.length)&&void 0!==i?i:0;this.isExceedMaxCountForPreopenPorts=r>=this.maxCountForPreopenPorts}render(){var e,t;return d`
      <link rel="stylesheet" href="resources/fonts/font-awesome-all.min.css" />
      <link rel="stylesheet" href="resources/custom.css" />
      <mwc-button
        class="primary-action"
        id="launch-session"
        ?disabled="${!this.enableLaunchButton}"
        icon="power_settings_new"
        data-testid="start-session-button"
        @click="${()=>this._launchSessionDialog()}"
      >
        ${O("session.launcher.Start")}
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
          ${this.newSessionDialogTitle?this.newSessionDialogTitle:O("session.launcher.StartNewSession")}
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
              label="${re("session.launcher.SessionType")}"
              required
              fixedMenuPosition
              value="${this.sessionType}"
              @selected="${e=>this._toggleStartUpCommandEditor(e)}"
            >
              ${"inference"===this.mode?d`
                    <mwc-list-item value="inference" selected>
                      ${O("session.launcher.InferenceMode")}
                    </mwc-list-item>
                  `:d`
                    <mwc-list-item value="batch">
                      ${O("session.launcher.BatchMode")}
                    </mwc-list-item>
                    <mwc-list-item value="interactive" selected>
                      ${O("session.launcher.InteractiveMode")}
                    </mwc-list-item>
                  `}
            </mwc-select>
            <mwc-select
              id="environment"
              icon="code"
              label="${re("session.launcher.Environments")}"
              required
              fixedMenuPosition
              value="${this.default_language}"
            >
              <mwc-list-item
                selected
                graphic="icon"
                style="display:none!important;"
              >
                ${O("session.launcher.ChooseEnvironment")}
              </mwc-list-item>
              ${this.languages.map((e=>d`
                  ${!1===e.clickable?d`
                        <h5
                          style="font-size:12px;padding: 0 10px 3px 10px;margin:0; border-bottom:1px solid var(--token-colorBorder, #ccc);"
                          role="separator"
                          disabled="true"
                        >
                          ${e.basename}
                        </h5>
                      `:d`
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
                              ${e.tags?e.tags.map((e=>d`
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
              label="${re("session.launcher.Version")}"
              required
              fixedMenuPosition
            >
              <mwc-list-item
                selected
                style="display:none!important"
              ></mwc-list-item>
              ${"Not Selected"===this.versions[0]&&1===this.versions.length?d``:d`
                    <h5
                      style="font-size:12px;padding: 0 10px 3px 15px;margin:0; border-bottom:1px solid var(--token-colorBorder, #ccc);"
                      role="separator"
                      disabled="true"
                      class="horizontal layout"
                    >
                      <div style="width:60px;">
                        ${O("session.launcher.Version")}
                      </div>
                      <div style="width:110px;">
                        ${O("session.launcher.Base")}
                      </div>
                      <div style="width:90px;">
                        ${O("session.launcher.Architecture")}
                      </div>
                      <div style="width:110px;">
                        ${O("session.launcher.Requirements")}
                      </div>
                    </h5>
                    ${this.versions.map((({version:e,architecture:t})=>d`
                        <mwc-list-item
                          id="${e}"
                          architecture="${t}"
                          value="${e}"
                          style="min-height:35px;height:auto;"
                        >
                          <span style="display:none">${e}</span>
                          <div class="horizontal layout end-justified">
                            ${this._getVersionInfo(e||"",t).map((e=>d`
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
            ${this._debug||this.allow_manual_image_name_for_session?d`
                  <mwc-textfield
                    id="image-name"
                    type="text"
                    class="flex"
                    value=""
                    icon="assignment_turned_in"
                    label="${re("session.launcher.ManualImageName")}"
                    @change=${e=>this._toggleEnvironmentSelectUI()}
                  ></mwc-textfield>
                `:d``}
            <mwc-textfield
              id="session-name"
              placeholder="${re("session.launcher.SessionNameOptional")}"
              pattern="^[a-zA-Z0-9]([a-zA-Z0-9\\-_\\.]{2,})[a-zA-Z0-9]$"
              minLength="4"
              maxLength="64"
              icon="label"
              helper="${re("inputLimit.4to64chars")}"
              validationMessage="${re("session.launcher.SessionNameAllowCondition")}"
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
                ${O("session.launcher.BatchModeConfig")}
              </span>
              <div class="horizontal layout start-justified">
                <div style="width:370px;font-size:12px;">
                  ${O("session.launcher.StartUpCommand")}*
                </div>
              </div>
              <lablup-codemirror
                id="command-editor"
                mode="shell"
                required
                validationMessage="${O("dialog.warning.Required")}"
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
                ${O("session.launcher.SetEnvironmentVariable")}
              </span>
              <div class="environment-variables-container">
                ${this.environ.length>0?d`
                      <div
                        class="horizontal flex center center-justified layout"
                        style="overflow-x:hidden;"
                      >
                        <div role="listbox">
                          <h4>
                            ${re("session.launcher.EnvironmentVariable")}
                          </h4>
                          ${this.environ.map((e=>d`
                              <mwc-textfield
                                disabled
                                value="${e.name}"
                              ></mwc-textfield>
                            `))}
                        </div>
                        <div role="listbox" style="margin-left:15px;">
                          <h4>
                            ${re("session.launcher.EnvironmentVariableValue")}
                          </h4>
                          ${this.environ.map((e=>d`
                              <mwc-textfield
                                disabled
                                value="${e.value}"
                              ></mwc-textfield>
                            `))}
                        </div>
                      </div>
                    `:d`
                      <div class="vertical layout center flex blank-box">
                        <span>${O("session.launcher.NoEnvConfigured")}</span>
                      </div>
                    `}
              </div>
            </lablup-expansion>
            ${this.maxCountForPreopenPorts>0?d`
                  <lablup-expansion
                    leftIconName="expand_more"
                    rightIconName="settings"
                    .rightCustomFunction="${()=>this._showPreOpenPortDialog()}"
                  >
                    <span slot="title">
                      ${O("session.launcher.SetPreopenPorts")}
                    </span>
                    <div class="preopen-ports-container">
                      ${this.preOpenPorts.length>0?d`
                            <div
                              class="horizontal flex center layout"
                              style="overflow-x:hidden;margin:auto 5px;"
                            >
                              ${this.preOpenPorts.map((e=>d`
                                  <lablup-shields
                                    color="lightgrey"
                                    description="${e}"
                                    style="padding:4px;"
                                  ></lablup-shields>
                                `))}
                            </div>
                          `:d`
                            <div class="vertical layout center flex blank-box">
                              <span>
                                ${O("session.launcher.NoPreOpenPortsConfigured")}
                              </span>
                            </div>
                          `}
                    </div>
                  </lablup-expansion>
                `:d``}
            <lablup-expansion
              name="ownership"
              style="--expansion-content-padding:15px 0;"
            >
              <span slot="title">
                ${O("session.launcher.SetSessionOwner")}
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
                    label="${re("session.launcher.OwnerEmail")}"
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
                  label="${re("session.launcher.OwnerAccessKey")}"
                  icon="vpn_key"
                  fixedMenuPosition
                  naturalMenuWidth
                >
                  ${this.ownerKeypairs.map((e=>d`
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
                    label="${re("session.launcher.OwnerGroup")}"
                    icon="group_work"
                    fixedMenuPosition
                    naturalMenuWidth
                  >
                    ${this.ownerGroups.map((e=>d`
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
                    label="${re("session.launcher.OwnerResourceGroup")}"
                    icon="storage"
                    fixedMenuPosition
                  >
                    ${this.ownerScalingGroups.map((e=>d`
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
                  <p>${O("session.launcher.LaunchSessionWithAccessKey")}</p>
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
              <span slot="title">${O("session.launcher.FolderToMount")}</span>
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
                    header="${O("session.launcher.FolderToMountList")}"
                    path="name"
                    resizable
                    .renderer="${this._boundFolderToMountListRenderer}"
                  ></vaadin-grid-filter-column>
                  <vaadin-grid-column
                    width="135px"
                    path=" ${O("session.launcher.FolderAlias")}"
                    .renderer="${this._boundFolderMapRenderer}"
                    .headerRenderer="${this._boundPathRenderer}"
                  ></vaadin-grid-column>
                </vaadin-grid>
                ${this.vfolders.length>0?d``:d`
                      <div class="vertical layout center flex blank-box-medium">
                        <span>
                          ${O("session.launcher.NoAvailableFolderToMount")}
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
                ${O("session.launcher.ModelStorageToMount")}
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
                    header="${O("session.launcher.ModelStorageToMount")}"
                    path="name"
                    resizable
                    .renderer="${this._boundFolderToMountListRenderer}"
                  ></vaadin-grid-filter-column>
                  <vaadin-grid-column
                    width="135px"
                    path=" ${O("session.launcher.FolderAlias")}"
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
              <span slot="title">${O("session.launcher.MountedFolders")}</span>
              <div class="vfolder-mounted-list">
                ${this.selectedVfolders.length>0||this.autoMountedVfolders.length>0?d`
                      <ul class="vfolder-list">
                        ${this.selectedVfolders.map((e=>d`
                            <li>
                              <mwc-icon>folder_open</mwc-icon>
                              ${e}
                              ${e in this.folderMapping?this.folderMapping[e].startsWith("/")?d`
                                      (&#10140; ${this.folderMapping[e]})
                                    `:d`
                                      (&#10140;
                                      /home/work/${this.folderMapping[e]})
                                    `:d`
                                    (&#10140; /home/work/${e})
                                  `}
                            </li>
                          `))}
                        ${this.autoMountedVfolders.map((e=>d`
                            <li>
                              <mwc-icon>folder_special</mwc-icon>
                              ${e.name}
                            </li>
                          `))}
                      </ul>
                    `:d`
                      <div class="vertical layout center flex blank-box-large">
                        <span>${O("session.launcher.NoFolderMounted")}</span>
                      </div>
                    `}
              </div>
            </lablup-expansion>
          </div>
          <div id="progress-03" class="progress center layout fade">
            <div class="horizontal center layout">
              <mwc-select
                id="scaling-groups"
                label="${re("session.launcher.ResourceGroup")}"
                icon="storage"
                required
                fixedMenuPosition
                @selected="${e=>this.updateScalingGroup(!0,e)}"
              >
                ${this.scaling_groups.map((e=>d`
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
                label="${this.isEmpty(this.resource_templates_filtered)?"":re("session.launcher.ResourceAllocation")}"
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
                    ${O("session.launcher.SharedMemory")}
                  </div>
                  <div style="width:90px;text-align:right;">
                    ${O("session.launcher.Accelerator")}
                  </div>
                </h5>
                ${this.resource_templates_filtered.map((e=>d`
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
                          ${e.shmem?d`
                                ${parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(e.shared_memory,"g")).toFixed(2)}
                                GiB
                              `:d`
                                64MB
                              `}
                        </div>
                        <div style="width:80px;text-align:right;">
                          ${e.cuda_device&&e.cuda_device>0?d`
                                ${e.cuda_device} GPU
                              `:d``}
                          ${e.cuda_shares&&e.cuda_shares>0?d`
                                ${e.cuda_shares} GPU
                              `:d``}
                          ${e.rocm_device&&e.rocm_device>0?d`
                                ${e.rocm_device} GPU
                              `:d``}
                          ${e.tpu_device&&e.tpu_device>0?d`
                                ${e.tpu_device} TPU
                              `:d``}
                          ${e.ipu_device&&e.ipu_device>0?d`
                                ${e.ipu_device} IPU
                              `:d``}
                          ${e.atom_device&&e.atom_device>0?d`
                                ${e.atom_device} ATOM
                              `:d``}
                          ${e.atom_plus_device&&e.atom_plus_device>0?d`
                                ${e.atom_plus_device} ATOM+
                              `:d``}
                          ${e.gaudi2_device&&e.gaudi2_device>0?d`
                                ${e.gaudi2_device} Gaudi 2
                              `:d``}
                          ${e.warboy_device&&e.warboy_device>0?d`
                                ${e.warboy_device} Warboy
                              `:d``}
                          ${e.rngd_device&&e.rngd_device>0?d`
                                ${e.rngd_device} RNGD
                              `:d``}
                          ${e.hyperaccel_lpu_device&&e.hyperaccel_lpu_device>0?d`
                                ${e.hyperaccel_lpu_device} Hyperaccel LPU
                              `:d``}
                        </div>
                        <div style="display:none">)</div>
                      </div>
                    </mwc-list-item>
                  `))}
                ${this.isEmpty(this.resource_templates_filtered)?d`
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
                          <h4>${O("session.launcher.NoSuitablePreset")}</h4>
                          <div style="font-size:12px;">
                            Use advanced settings to
                            <br />
                            start custom session
                          </div>
                        </div>
                      </mwc-list-item>
                    `:d``}
              </mwc-select>
            </div>
            <lablup-expansion
              name="resource-group"
              style="display:${this.allowCustomResourceAllocation?"block":"none"}"
            >
              <span slot="title">
                ${O("session.launcher.CustomAllocation")}
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
                      suffix="${re("session.launcher.Core")}"
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
                    <div>${O("session.launcher.SharedMemory")}</div>
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
                    <div>${O("webui.menu.AIAccelerator")}</div>
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
                    <div>${O("webui.menu.Sessions")}</div>
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
            ${this.cluster_support?d`
                  <mwc-select
                    id="cluster-mode"
                    label="${re("session.launcher.ClusterMode")}"
                    required
                    icon="account_tree"
                    fixedMenuPosition
                    value="${this.cluster_mode}"
                    @change="${e=>this._setClusterMode(e)}"
                  >
                    ${this.cluster_mode_list.map((e=>d`
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
                              ${O("single-node"===e?"session.launcher.SingleNode":"session.launcher.MultiNode")}
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
                          ${O("session.launcher.ClusterSize")}
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
                          suffix="${"single-node"===this.cluster_mode?re("session.launcher.Container"):re("session.launcher.Node")}"
                        ></lablup-slider>
                      </div>
                    </div>
                  </div>
                `:d``}
            <lablup-expansion name="hpc-option-group">
              <span slot="title">
                ${O("session.launcher.HPCOptimization")}
              </span>
              <div class="vertical center layout">
                <div class="horizontal center center-justified flex layout">
                  <div style="width:313px;">
                    ${O("session.launcher.SwitchOpenMPoptimization")}
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
                      ${O("session.launcher.NumOpenMPthreads")}
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
                      ${O("session.launcher.NumOpenBLASthreads")}
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
            <p class="title">${O("session.SessionInfo")}</p>
            <div class="vertical layout cluster-total-allocation-container">
              ${this._preProcessingSessionInfo()?d`
                    <div
                      class="vertical layout"
                      style="margin-left:10px;margin-bottom:5px;"
                    >
                      <div class="horizontal layout">
                        <div style="margin-right:5px;width:150px;">
                          ${O("session.EnvironmentInfo")}
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
                            ${this.sessionInfoObj.version.map(((e,t)=>t>0?d`
                                  <lablup-shields
                                    color="green"
                                    description="${e}"
                                    ui="round"
                                    style="margin-top:3px;margin-right:3px;"
                                  ></lablup-shields>
                                `:d``))}
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
                          ${O("registry.ProjectName")}
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
                          ${O("session.ResourceGroup")}
                        </div>
                        <div class="vertical layout">${this.scaling_group}</div>
                      </div>
                    </div>
                  `:d``}
            </div>
            <p class="title">${O("session.launcher.TotalAllocation")}</p>
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
                    <p>${O("session.launcher.CPU")}</p>
                    <span>
                      ${this.cpu_request*this.cluster_size*this.session_request}
                    </span>
                    <p>Core</p>
                  </div>
                  <div
                    class="vertical layout center center-justified resource-allocated"
                  >
                    <p>${O("session.launcher.Memory")}</p>
                    <span>
                      ${this._roundResourceAllocation(this.mem_request*this.cluster_size*this.session_request,1)}
                    </span>
                    <p>GiB</p>
                  </div>
                  <div
                    class="vertical layout center center-justified resource-allocated"
                  >
                    <p>${O("session.launcher.SharedMemoryAbbr")}</p>
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
                    <p>${O("session.launcher.GPUSlot")}</p>
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
                      <p>${O("session.launcher.CPU")}</p>
                      <span>${this.cpu_request}</span>
                      <p>Core</p>
                    </div>
                    <div
                      class="vertical layout center center-justified resource-allocated"
                    >
                      <p>${O("session.launcher.Memory")}</p>
                      <span>
                        ${this._roundResourceAllocation(this.mem_request,1)}
                      </span>
                      <p>GiB</p>
                    </div>
                    <div
                      class="vertical layout center center-justified resource-allocated"
                    >
                      <p>${O("session.launcher.SharedMemoryAbbr")}</p>
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
                      <p>${O("session.launcher.GPUSlot")}</p>
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
                  <p class="small">${O("session.launcher.Container")}</p>
                </div>
                <div
                  class="vertical layout center center-justified cluster-allocated"
                  style="z-index:10;"
                >
                  <div class="horizontal layout">
                    <p>${this.cluster_mode,""}</p>
                    <span style="text-align:center;">
                      ${"single-node"===this.cluster_mode?O("session.launcher.SingleNode"):O("session.launcher.MultiNode")}
                    </span>
                  </div>
                  <p class="small">${O("session.launcher.AllocateNode")}</p>
                </div>
              </div>
            </div>
            ${"inference"!==this.mode?d`
                  <p class="title">${O("session.launcher.MountedFolders")}</p>
                  <div
                    id="mounted-folders-container"
                    class="cluster-total-allocation-container"
                  >
                    ${this.selectedVfolders.length>0||this.autoMountedVfolders.length>0?d`
                          <ul class="vfolder-list">
                            ${this.selectedVfolders.map((e=>d`
                                <li>
                                  <mwc-icon>folder_open</mwc-icon>
                                  ${e}
                                  ${e in this.folderMapping?this.folderMapping[e].startsWith("/")?d`
                                          (&#10140; ${this.folderMapping[e]})
                                        `:d`
                                          (&#10140;
                                          /home/work/${this.folderMapping[e]})
                                        `:d`
                                        (&#10140; /home/work/${e})
                                      `}
                                </li>
                              `))}
                            ${this.autoMountedVfolders.map((e=>d`
                                <li>
                                  <mwc-icon>folder_special</mwc-icon>
                                  ${e.name}
                                </li>
                              `))}
                          </ul>
                        `:d`
                          <div class="vertical layout center flex blank-box">
                            <span>
                              ${O("session.launcher.NoFolderMounted")}
                            </span>
                          </div>
                        `}
                  </div>
                `:d``}
            <p class="title">
              ${O("session.launcher.EnvironmentVariablePaneTitle")}
            </p>
            <div
              class="environment-variables-container cluster-total-allocation-container"
            >
              ${this.environ.length>0?d`
                    <div
                      class="horizontal flex center center-justified layout"
                      style="overflow-x:hidden;"
                    >
                      <div role="listbox">
                        <h4>
                          ${re("session.launcher.EnvironmentVariable")}
                        </h4>
                        ${this.environ.map((e=>d`
                            <mwc-textfield
                              disabled
                              value="${e.name}"
                            ></mwc-textfield>
                          `))}
                      </div>
                      <div role="listbox" style="margin-left:15px;">
                        <h4>
                          ${re("session.launcher.EnvironmentVariableValue")}
                        </h4>
                        ${this.environ.map((e=>d`
                            <mwc-textfield
                              disabled
                              value="${e.value}"
                            ></mwc-textfield>
                          `))}
                      </div>
                    </div>
                  `:d`
                    <div class="vertical layout center flex blank-box">
                      <span>${O("session.launcher.NoEnvConfigured")}</span>
                    </div>
                  `}
            </div>
            ${this.maxCountForPreopenPorts>0?d`
                  <p class="title">
                    ${O("session.launcher.PreOpenPortPanelTitle")}
                  </p>
                  <div
                    class="preopen-ports-container cluster-total-allocation-container"
                  >
                    ${this.preOpenPorts.length>0?d`
                          <div
                            class="horizontal flex center layout"
                            style="overflow-x:hidden;margin:auto 5px;"
                          >
                            ${this.preOpenPorts.map((e=>d`
                                <lablup-shields
                                  color="lightgrey"
                                  description="${e}"
                                  style="padding:4px;"
                                ></lablup-shields>
                              `))}
                          </div>
                        `:d`
                          <div class="vertical layout center flex blank-box">
                            <span>
                              ${O("session.launcher.NoPreOpenPortsConfigured")}
                            </span>
                          </div>
                        `}
                  </div>
                `:d``}
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
          ${O("session.launcher.SetEnvironmentVariable")}
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
            <div>${O("session.launcher.EnvironmentVariable")}</div>
            <div>${O("session.launcher.EnvironmentVariableValue")}</div>
          </div>
          <div id="modify-env-fields-container" class="layout center">
            ${this.environ.forEach((e=>d`
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
            label="${re("button.Reset")}"
            @click="${()=>this._clearEnvRows()}"
          ></mwc-button>
          <mwc-button
            unelevated
            slot="footer"
            icon="check"
            style="width:100px"
            label="${re("button.Save")}"
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
        <span slot="title">${O("session.launcher.SetPreopenPorts")}</span>
        <span slot="action">
          <mwc-icon-button
            icon="info"
            @click="${e=>this._showPreOpenPortConfigDescription(e)}"
            style="pointer-events: auto;"
          ></mwc-icon-button>
        </span>
        <div slot="content" id="modify-preopen-ports-container">
          <div class="horizontal layout center flex justified header">
            <div>${O("session.launcher.PortsTitleWithRange")}</div>
          </div>
          <div class="layout center">
            ${this.preOpenPorts.forEach((e=>d`
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
            label="${re("button.Reset")}"
            @click="${()=>this._clearPreOpenPortRows()}"
          ></mwc-button>
          <mwc-button
            unelevated
            slot="footer"
            icon="check"
            style="width:100px"
            label="${re("button.Save")}"
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
          ${""==this._helpDescriptionIcon?d``:d`
                <img
                  slot="graphic"
                  alt="help icon"
                  src="resources/icons/${this._helpDescriptionIcon}"
                  style="width:64px;height:64px;margin-right:10px;"
                />
              `}
          <div style="font-size:14px;">
            ${ae(this._helpDescription)}
          </div>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="launch-confirmation-dialog" warning fixed backdrop>
        <span slot="title">${O("session.launcher.NoFolderMounted")}</span>
        <div slot="content" class="vertical layout">
          <p>${O("session.launcher.HomeDirectoryDeletionDialog")}</p>
          <p>${O("session.launcher.LaunchConfirmationDialog")}</p>
          <p>${O("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            unelevated
            class="launch-confirmation-button"
            id="launch-confirmation-button"
            icon="rowing"
            @click="${()=>this._newSession()}"
          >
            ${O("session.launcher.Launch")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="env-config-confirmation" warning fixed>
        <span slot="title">${O("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${O("session.launcher.EnvConfigWillDisappear")}</p>
          <p>${O("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            id="env-config-remain-button"
            label="${re("button.Cancel")}"
            @click="${()=>this.closeDialog("env-config-confirmation")}"
            style="width:auto;margin-right:10px;"
          ></mwc-button>
          <mwc-button
            unelevated
            id="env-config-reset-button"
            label="${re("button.DismissAndProceed")}"
            @click="${()=>this._closeAndResetEnvInput()}"
            style="width:auto;"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="preopen-ports-config-confirmation" warning fixed>
        <span slot="title">${O("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${O("session.launcher.PrePortConfigWillDisappear")}</p>
          <p>${O("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            id="preopen-ports-remain-button"
            label="${re("button.Cancel")}"
            @click="${()=>this.closeDialog("preopen-ports-config-confirmation")}"
            style="width:auto;margin-right:10px;"
          ></mwc-button>
          <mwc-button
            unelevated
            id="preopen-ports-config-reset-button"
            label="${re("button.DismissAndProceed")}"
            @click="${()=>this._closeAndResetPreOpenPortInput()}"
            style="width:auto;"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};e([t({type:Boolean})],uc.prototype,"is_connected",void 0),e([t({type:Boolean})],uc.prototype,"enableLaunchButton",void 0),e([t({type:Boolean})],uc.prototype,"hideLaunchButton",void 0),e([t({type:Boolean})],uc.prototype,"hideEnvDialog",void 0),e([t({type:Boolean})],uc.prototype,"hidePreOpenPortDialog",void 0),e([t({type:Boolean})],uc.prototype,"enableInferenceWorkload",void 0),e([t({type:String})],uc.prototype,"location",void 0),e([t({type:String})],uc.prototype,"mode",void 0),e([t({type:String})],uc.prototype,"newSessionDialogTitle",void 0),e([t({type:String})],uc.prototype,"importScript",void 0),e([t({type:String})],uc.prototype,"importFilename",void 0),e([t({type:Object})],uc.prototype,"imageRequirements",void 0),e([t({type:Object})],uc.prototype,"resourceLimits",void 0),e([t({type:Object})],uc.prototype,"userResourceLimit",void 0),e([t({type:Object})],uc.prototype,"aliases",void 0),e([t({type:Object})],uc.prototype,"tags",void 0),e([t({type:Object})],uc.prototype,"icons",void 0),e([t({type:Object})],uc.prototype,"imageInfo",void 0),e([t({type:String})],uc.prototype,"kernel",void 0),e([t({type:Array})],uc.prototype,"versions",void 0),e([t({type:Array})],uc.prototype,"languages",void 0),e([t({type:Number})],uc.prototype,"marker_limit",void 0),e([t({type:String})],uc.prototype,"gpu_mode",void 0),e([t({type:Array})],uc.prototype,"gpu_modes",void 0),e([t({type:Number})],uc.prototype,"gpu_step",void 0),e([t({type:Object})],uc.prototype,"cpu_metric",void 0),e([t({type:Object})],uc.prototype,"mem_metric",void 0),e([t({type:Object})],uc.prototype,"shmem_metric",void 0),e([t({type:Object})],uc.prototype,"npu_device_metric",void 0),e([t({type:Object})],uc.prototype,"cuda_shares_metric",void 0),e([t({type:Object})],uc.prototype,"rocm_device_metric",void 0),e([t({type:Object})],uc.prototype,"tpu_device_metric",void 0),e([t({type:Object})],uc.prototype,"ipu_device_metric",void 0),e([t({type:Object})],uc.prototype,"atom_device_metric",void 0),e([t({type:Object})],uc.prototype,"atom_plus_device_metric",void 0),e([t({type:Object})],uc.prototype,"gaudi2_device_metric",void 0),e([t({type:Object})],uc.prototype,"warboy_device_metric",void 0),e([t({type:Object})],uc.prototype,"rngd_device_metric",void 0),e([t({type:Object})],uc.prototype,"hyperaccel_lpu_device_metric",void 0),e([t({type:Object})],uc.prototype,"cluster_metric",void 0),e([t({type:Array})],uc.prototype,"cluster_mode_list",void 0),e([t({type:Boolean})],uc.prototype,"cluster_support",void 0),e([t({type:Object})],uc.prototype,"images",void 0),e([t({type:Object})],uc.prototype,"total_slot",void 0),e([t({type:Object})],uc.prototype,"total_resource_group_slot",void 0),e([t({type:Object})],uc.prototype,"total_project_slot",void 0),e([t({type:Object})],uc.prototype,"used_slot",void 0),e([t({type:Object})],uc.prototype,"used_resource_group_slot",void 0),e([t({type:Object})],uc.prototype,"used_project_slot",void 0),e([t({type:Object})],uc.prototype,"available_slot",void 0),e([t({type:Number})],uc.prototype,"concurrency_used",void 0),e([t({type:Number})],uc.prototype,"concurrency_max",void 0),e([t({type:Number})],uc.prototype,"concurrency_limit",void 0),e([t({type:Number})],uc.prototype,"max_containers_per_session",void 0),e([t({type:Array})],uc.prototype,"vfolders",void 0),e([t({type:Array})],uc.prototype,"selectedVfolders",void 0),e([t({type:Array})],uc.prototype,"autoMountedVfolders",void 0),e([t({type:Array})],uc.prototype,"modelVfolders",void 0),e([t({type:Array})],uc.prototype,"nonAutoMountedVfolders",void 0),e([t({type:Object})],uc.prototype,"folderMapping",void 0),e([t({type:Object})],uc.prototype,"customFolderMapping",void 0),e([t({type:Object})],uc.prototype,"used_slot_percent",void 0),e([t({type:Object})],uc.prototype,"used_resource_group_slot_percent",void 0),e([t({type:Object})],uc.prototype,"used_project_slot_percent",void 0),e([t({type:Array})],uc.prototype,"resource_templates",void 0),e([t({type:Array})],uc.prototype,"resource_templates_filtered",void 0),e([t({type:String})],uc.prototype,"default_language",void 0),e([t({type:Number})],uc.prototype,"cpu_request",void 0),e([t({type:Number})],uc.prototype,"mem_request",void 0),e([t({type:Number})],uc.prototype,"shmem_request",void 0),e([t({type:Number})],uc.prototype,"gpu_request",void 0),e([t({type:String})],uc.prototype,"gpu_request_type",void 0),e([t({type:Number})],uc.prototype,"session_request",void 0),e([t({type:Boolean})],uc.prototype,"_status",void 0),e([t({type:Number})],uc.prototype,"num_sessions",void 0),e([t({type:String})],uc.prototype,"scaling_group",void 0),e([t({type:Array})],uc.prototype,"scaling_groups",void 0),e([t({type:Array})],uc.prototype,"sessions_list",void 0),e([t({type:Boolean})],uc.prototype,"metric_updating",void 0),e([t({type:Boolean})],uc.prototype,"metadata_updating",void 0),e([t({type:Boolean})],uc.prototype,"aggregate_updating",void 0),e([t({type:Object})],uc.prototype,"scaling_group_selection_box",void 0),e([t({type:Object})],uc.prototype,"resourceGauge",void 0),e([t({type:String})],uc.prototype,"sessionType",void 0),e([t({type:Boolean})],uc.prototype,"ownerFeatureInitialized",void 0),e([t({type:String})],uc.prototype,"ownerDomain",void 0),e([t({type:Array})],uc.prototype,"ownerKeypairs",void 0),e([t({type:Array})],uc.prototype,"ownerGroups",void 0),e([t({type:Array})],uc.prototype,"ownerScalingGroups",void 0),e([t({type:Boolean})],uc.prototype,"project_resource_monitor",void 0),e([t({type:Boolean})],uc.prototype,"_default_language_updated",void 0),e([t({type:Boolean})],uc.prototype,"_default_version_updated",void 0),e([t({type:String})],uc.prototype,"_helpDescription",void 0),e([t({type:String})],uc.prototype,"_helpDescriptionTitle",void 0),e([t({type:String})],uc.prototype,"_helpDescriptionIcon",void 0),e([t({type:String})],uc.prototype,"_NPUDeviceNameOnSlider",void 0),e([t({type:Number})],uc.prototype,"max_cpu_core_per_session",void 0),e([t({type:Number})],uc.prototype,"max_mem_per_container",void 0),e([t({type:Number})],uc.prototype,"max_cuda_device_per_container",void 0),e([t({type:Number})],uc.prototype,"max_cuda_shares_per_container",void 0),e([t({type:Number})],uc.prototype,"max_rocm_device_per_container",void 0),e([t({type:Number})],uc.prototype,"max_tpu_device_per_container",void 0),e([t({type:Number})],uc.prototype,"max_ipu_device_per_container",void 0),e([t({type:Number})],uc.prototype,"max_atom_device_per_container",void 0),e([t({type:Number})],uc.prototype,"max_atom_plus_device_per_container",void 0),e([t({type:Number})],uc.prototype,"max_gaudi2_device_per_container",void 0),e([t({type:Number})],uc.prototype,"max_warboy_device_per_container",void 0),e([t({type:Number})],uc.prototype,"max_rngd_device_per_container",void 0),e([t({type:Number})],uc.prototype,"max_hyperaccel_lpu_device_per_container",void 0),e([t({type:Number})],uc.prototype,"max_shm_per_container",void 0),e([t({type:Boolean})],uc.prototype,"allow_manual_image_name_for_session",void 0),e([t({type:Object})],uc.prototype,"resourceBroker",void 0),e([t({type:Number})],uc.prototype,"cluster_size",void 0),e([t({type:String})],uc.prototype,"cluster_mode",void 0),e([t({type:Object})],uc.prototype,"deleteEnvInfo",void 0),e([t({type:Object})],uc.prototype,"deleteEnvRow",void 0),e([t({type:Array})],uc.prototype,"environ",void 0),e([t({type:Array})],uc.prototype,"preOpenPorts",void 0),e([t({type:Object})],uc.prototype,"environ_values",void 0),e([t({type:Object})],uc.prototype,"vfolder_select_expansion",void 0),e([t({type:Number})],uc.prototype,"currentIndex",void 0),e([t({type:Number})],uc.prototype,"progressLength",void 0),e([t({type:Object})],uc.prototype,"_nonAutoMountedFolderGrid",void 0),e([t({type:Object})],uc.prototype,"_modelFolderGrid",void 0),e([t({type:Boolean})],uc.prototype,"_debug",void 0),e([t({type:Object})],uc.prototype,"_boundFolderToMountListRenderer",void 0),e([t({type:Object})],uc.prototype,"_boundFolderMapRenderer",void 0),e([t({type:Object})],uc.prototype,"_boundPathRenderer",void 0),e([t({type:String})],uc.prototype,"scheduledTime",void 0),e([t({type:Object})],uc.prototype,"schedulerTimer",void 0),e([t({type:Object})],uc.prototype,"sessionInfoObj",void 0),e([t({type:String})],uc.prototype,"launchButtonMessageTextContent",void 0),e([t({type:Boolean})],uc.prototype,"isExceedMaxCountForPreopenPorts",void 0),e([t({type:Number})],uc.prototype,"maxCountForPreopenPorts",void 0),e([t({type:Boolean})],uc.prototype,"allowCustomResourceAllocation",void 0),e([t({type:Boolean})],uc.prototype,"allowNEOSessionLauncher",void 0),e([E("#image-name")],uc.prototype,"manualImageName",void 0),e([E("#version")],uc.prototype,"version_selector",void 0),e([E("#environment")],uc.prototype,"environment",void 0),e([E("#owner-group")],uc.prototype,"ownerGroupSelect",void 0),e([E("#scaling-groups")],uc.prototype,"scalingGroups",void 0),e([E("#resource-templates")],uc.prototype,"resourceTemplatesSelect",void 0),e([E("#owner-scaling-group")],uc.prototype,"ownerScalingGroupSelect",void 0),e([E("#owner-accesskey")],uc.prototype,"ownerAccesskeySelect",void 0),e([E("#owner-email")],uc.prototype,"ownerEmailInput",void 0),e([E("#vfolder-mount-preview")],uc.prototype,"vfolderMountPreview",void 0),e([E("#launch-button")],uc.prototype,"launchButton",void 0),e([E("#prev-button")],uc.prototype,"prevButton",void 0),e([E("#next-button")],uc.prototype,"nextButton",void 0),e([E("#OpenMPswitch")],uc.prototype,"openMPSwitch",void 0),e([E("#cpu-resource")],uc.prototype,"cpuResourceSlider",void 0),e([E("#gpu-resource")],uc.prototype,"npuResourceSlider",void 0),e([E("#mem-resource")],uc.prototype,"memoryResourceSlider",void 0),e([E("#shmem-resource")],uc.prototype,"sharedMemoryResourceSlider",void 0),e([E("#session-resource")],uc.prototype,"sessionResourceSlider",void 0),e([E("#cluster-size")],uc.prototype,"clusterSizeSlider",void 0),e([E("#launch-button-msg")],uc.prototype,"launchButtonMessage",void 0),e([E("#new-session-dialog")],uc.prototype,"newSessionDialog",void 0),e([E("#modify-env-dialog")],uc.prototype,"modifyEnvDialog",void 0),e([E("#modify-env-container")],uc.prototype,"modifyEnvContainer",void 0),e([E("#modify-preopen-ports-dialog")],uc.prototype,"modifyPreOpenPortDialog",void 0),e([E("#modify-preopen-ports-container")],uc.prototype,"modifyPreOpenPortContainer",void 0),e([E("#launch-confirmation-dialog")],uc.prototype,"launchConfirmationDialog",void 0),e([E("#help-description")],uc.prototype,"helpDescriptionDialog",void 0),e([E("#command-editor")],uc.prototype,"commandEditor",void 0),e([E("#session-name")],uc.prototype,"sessionName",void 0),e([E("backend-ai-react-batch-session-scheduled-time-setting")],uc.prototype,"batchSessionDatePicker",void 0),uc=e([i("backend-ai-session-launcher")],uc);
