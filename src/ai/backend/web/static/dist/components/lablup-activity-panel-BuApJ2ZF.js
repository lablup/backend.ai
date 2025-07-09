import{_ as e,n as t,t as i,h as r,b as s,I as a,a as o,ae as n,c as d,i as c,k as l,a5 as h,V as u,W as p,ai as m,X as v,$ as _,a9 as b,Y as g,a8 as f,aj as y,a2 as w,ab as x,a3 as T,a4 as k,ak as S,al as E,am as $,an as R,a6 as P,e as j,ao as F,ap as C,ac as W,aa as A,B as I,d as D,f as B}from"./backend-ai-webui-CwxbnM88.js";let N=class extends r{constructor(){super(...arguments),this.progress="",this.description=""}static get styles(){return[s,a,o,n,d,c`
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
      `]}render(){return l`
      <link rel="stylesheet" href="resources/custom.css" />
      <div class="horizontal layout flex">
        <slot name="left-desc"></slot>
        <div class="progress">
          <div id="back" class="back"></div>
          <div id="front" class="front"></div>
        </div>
        <slot name="right-desc"></slot>
      </div>
    `}firstUpdated(){var e,t,i;this.progressBar=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#front"),this.frontDesc=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#front"),this.backDesc=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#back"),this.progressBar.style.clipPath="inset(0 0 0 0%)"}async changePct(e){await this.updateComplete,this.progressBar.style.clipPath="inset(0 0 0 "+100*e+"%)"}async changeDesc(e){await this.updateComplete,this.frontDesc.innerHTML="&nbsp;"+e,this.backDesc.innerHTML="&nbsp;"+e}connectedCallback(){super.connectedCallback()}disconnectedCallback(){super.disconnectedCallback()}attributeChangedCallback(e,t,i){"progress"!=e||null===i||isNaN(i)||this.changePct(i),"description"!=e||null===i||i.startsWith("undefined")||this.changeDesc(i),super.attributeChangedCallback(e,t,i)}};e([t({type:Object})],N.prototype,"progressBar",void 0),e([t({type:Object})],N.prototype,"frontDesc",void 0),e([t({type:Object})],N.prototype,"backDesc",void 0),e([t({type:String})],N.prototype,"progress",void 0),e([t({type:String})],N.prototype,"description",void 0),N=e([i("lablup-progress-bar")],N);
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-LIcense-Identifier: Apache-2.0
 */
const L=h`.mdc-slider{cursor:pointer;height:48px;margin:0 24px;position:relative;touch-action:pan-y}.mdc-slider .mdc-slider__track{height:4px;position:absolute;top:50%;transform:translateY(-50%);width:100%}.mdc-slider .mdc-slider__track--active,.mdc-slider .mdc-slider__track--inactive{display:flex;height:100%;position:absolute;width:100%}.mdc-slider .mdc-slider__track--active{border-radius:3px;height:6px;overflow:hidden;top:-1px}.mdc-slider .mdc-slider__track--active_fill{border-top:6px solid;box-sizing:border-box;height:100%;width:100%;position:relative;-webkit-transform-origin:left;transform-origin:left}[dir=rtl] .mdc-slider .mdc-slider__track--active_fill,.mdc-slider .mdc-slider__track--active_fill[dir=rtl]{-webkit-transform-origin:right;transform-origin:right}.mdc-slider .mdc-slider__track--inactive{border-radius:2px;height:4px;left:0;top:0}.mdc-slider .mdc-slider__track--inactive::before{position:absolute;box-sizing:border-box;width:100%;height:100%;top:0;left:0;border:1px solid transparent;border-radius:inherit;content:"";pointer-events:none}@media screen and (forced-colors: active){.mdc-slider .mdc-slider__track--inactive::before{border-color:CanvasText}}.mdc-slider .mdc-slider__track--active_fill{border-color:#6200ee;border-color:var(--mdc-theme-primary, #6200ee)}.mdc-slider.mdc-slider--disabled .mdc-slider__track--active_fill{border-color:#000;border-color:var(--mdc-theme-on-surface, #000)}.mdc-slider .mdc-slider__track--inactive{background-color:#6200ee;background-color:var(--mdc-theme-primary, #6200ee);opacity:.24}.mdc-slider.mdc-slider--disabled .mdc-slider__track--inactive{background-color:#000;background-color:var(--mdc-theme-on-surface, #000);opacity:.24}.mdc-slider .mdc-slider__value-indicator-container{bottom:44px;left:50%;left:var(--slider-value-indicator-container-left, 50%);pointer-events:none;position:absolute;right:var(--slider-value-indicator-container-right);transform:translateX(-50%);transform:var(--slider-value-indicator-container-transform, translateX(-50%))}.mdc-slider .mdc-slider__value-indicator{transition:transform 100ms 0ms cubic-bezier(0.4, 0, 1, 1);align-items:center;border-radius:4px;display:flex;height:32px;padding:0 12px;transform:scale(0);transform-origin:bottom}.mdc-slider .mdc-slider__value-indicator::before{border-left:6px solid transparent;border-right:6px solid transparent;border-top:6px solid;bottom:-5px;content:"";height:0;left:50%;left:var(--slider-value-indicator-caret-left, 50%);position:absolute;right:var(--slider-value-indicator-caret-right);transform:translateX(-50%);transform:var(--slider-value-indicator-caret-transform, translateX(-50%));width:0}.mdc-slider .mdc-slider__value-indicator::after{position:absolute;box-sizing:border-box;width:100%;height:100%;top:0;left:0;border:1px solid transparent;border-radius:inherit;content:"";pointer-events:none}@media screen and (forced-colors: active){.mdc-slider .mdc-slider__value-indicator::after{border-color:CanvasText}}.mdc-slider .mdc-slider__thumb--with-indicator .mdc-slider__value-indicator-container{pointer-events:auto}.mdc-slider .mdc-slider__thumb--with-indicator .mdc-slider__value-indicator{transition:transform 100ms 0ms cubic-bezier(0, 0, 0.2, 1);transform:scale(1)}@media(prefers-reduced-motion){.mdc-slider .mdc-slider__value-indicator,.mdc-slider .mdc-slider__thumb--with-indicator .mdc-slider__value-indicator{transition:none}}.mdc-slider .mdc-slider__value-indicator-text{-moz-osx-font-smoothing:grayscale;-webkit-font-smoothing:antialiased;font-family:Roboto, sans-serif;font-family:var(--mdc-typography-subtitle2-font-family, var(--mdc-typography-font-family, Roboto, sans-serif));font-size:0.875rem;font-size:var(--mdc-typography-subtitle2-font-size, 0.875rem);line-height:1.375rem;line-height:var(--mdc-typography-subtitle2-line-height, 1.375rem);font-weight:500;font-weight:var(--mdc-typography-subtitle2-font-weight, 500);letter-spacing:0.0071428571em;letter-spacing:var(--mdc-typography-subtitle2-letter-spacing, 0.0071428571em);text-decoration:inherit;text-decoration:var(--mdc-typography-subtitle2-text-decoration, inherit);text-transform:inherit;text-transform:var(--mdc-typography-subtitle2-text-transform, inherit)}.mdc-slider .mdc-slider__value-indicator{background-color:#000;opacity:.6}.mdc-slider .mdc-slider__value-indicator::before{border-top-color:#000}.mdc-slider .mdc-slider__value-indicator{color:#fff;color:var(--mdc-theme-on-primary, #fff)}.mdc-slider .mdc-slider__thumb{display:flex;height:48px;left:-24px;outline:none;position:absolute;user-select:none;width:48px}.mdc-slider .mdc-slider__thumb--top{z-index:1}.mdc-slider .mdc-slider__thumb--top .mdc-slider__thumb-knob,.mdc-slider .mdc-slider__thumb--top.mdc-slider__thumb:hover .mdc-slider__thumb-knob,.mdc-slider .mdc-slider__thumb--top.mdc-slider__thumb--focused .mdc-slider__thumb-knob{border-style:solid;border-width:1px;box-sizing:content-box}.mdc-slider .mdc-slider__thumb-knob{box-shadow:0px 2px 1px -1px rgba(0, 0, 0, 0.2),0px 1px 1px 0px rgba(0, 0, 0, 0.14),0px 1px 3px 0px rgba(0,0,0,.12);border:10px solid;border-radius:50%;box-sizing:border-box;height:20px;left:50%;position:absolute;top:50%;transform:translate(-50%, -50%);width:20px}.mdc-slider .mdc-slider__thumb-knob{background-color:#6200ee;background-color:var(--mdc-theme-primary, #6200ee);border-color:#6200ee;border-color:var(--mdc-theme-primary, #6200ee)}.mdc-slider .mdc-slider__thumb--top .mdc-slider__thumb-knob,.mdc-slider .mdc-slider__thumb--top.mdc-slider__thumb:hover .mdc-slider__thumb-knob,.mdc-slider .mdc-slider__thumb--top.mdc-slider__thumb--focused .mdc-slider__thumb-knob{border-color:#fff}.mdc-slider.mdc-slider--disabled .mdc-slider__thumb-knob{background-color:#000;background-color:var(--mdc-theme-on-surface, #000);border-color:#000;border-color:var(--mdc-theme-on-surface, #000)}.mdc-slider.mdc-slider--disabled .mdc-slider__thumb--top .mdc-slider__thumb-knob,.mdc-slider.mdc-slider--disabled .mdc-slider__thumb--top.mdc-slider__thumb:hover .mdc-slider__thumb-knob,.mdc-slider.mdc-slider--disabled .mdc-slider__thumb--top.mdc-slider__thumb--focused .mdc-slider__thumb-knob{border-color:#fff}.mdc-slider .mdc-slider__thumb::before,.mdc-slider .mdc-slider__thumb::after{background-color:#6200ee;background-color:var(--mdc-ripple-color, var(--mdc-theme-primary, #6200ee))}.mdc-slider .mdc-slider__thumb:hover::before,.mdc-slider .mdc-slider__thumb.mdc-ripple-surface--hover::before{opacity:0.04;opacity:var(--mdc-ripple-hover-opacity, 0.04)}.mdc-slider .mdc-slider__thumb.mdc-ripple-upgraded--background-focused::before,.mdc-slider .mdc-slider__thumb:not(.mdc-ripple-upgraded):focus::before{transition-duration:75ms;opacity:0.12;opacity:var(--mdc-ripple-focus-opacity, 0.12)}.mdc-slider .mdc-slider__thumb:not(.mdc-ripple-upgraded)::after{transition:opacity 150ms linear}.mdc-slider .mdc-slider__thumb:not(.mdc-ripple-upgraded):active::after{transition-duration:75ms;opacity:0.12;opacity:var(--mdc-ripple-press-opacity, 0.12)}.mdc-slider .mdc-slider__thumb.mdc-ripple-upgraded{--mdc-ripple-fg-opacity:var(--mdc-ripple-press-opacity, 0.12)}.mdc-slider .mdc-slider__tick-marks{align-items:center;box-sizing:border-box;display:flex;height:100%;justify-content:space-between;padding:0 1px;position:absolute;width:100%}.mdc-slider .mdc-slider__tick-mark--active,.mdc-slider .mdc-slider__tick-mark--inactive{border-radius:50%;height:2px;width:2px}.mdc-slider .mdc-slider__tick-mark--active{background-color:#fff;background-color:var(--mdc-theme-on-primary, #fff);opacity:.6}.mdc-slider.mdc-slider--disabled .mdc-slider__tick-mark--active{background-color:#fff;background-color:var(--mdc-theme-on-primary, #fff);opacity:.6}.mdc-slider .mdc-slider__tick-mark--inactive{background-color:#6200ee;background-color:var(--mdc-theme-primary, #6200ee);opacity:.6}.mdc-slider.mdc-slider--disabled .mdc-slider__tick-mark--inactive{background-color:#000;background-color:var(--mdc-theme-on-surface, #000);opacity:.6}.mdc-slider--discrete .mdc-slider__thumb,.mdc-slider--discrete .mdc-slider__track--active_fill{transition:transform 80ms ease}@media(prefers-reduced-motion){.mdc-slider--discrete .mdc-slider__thumb,.mdc-slider--discrete .mdc-slider__track--active_fill{transition:none}}.mdc-slider--disabled{opacity:.38;cursor:auto}.mdc-slider--disabled .mdc-slider__thumb{pointer-events:none}.mdc-slider__input{cursor:pointer;left:0;margin:0;height:100%;opacity:0;pointer-events:none;position:absolute;top:0;width:100%}:host{outline:none;display:block;-webkit-tap-highlight-color:transparent}.ripple{--mdc-ripple-color:#6200ee;--mdc-ripple-color:var(--mdc-theme-primary, #6200ee)}`
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
 */;var z,M;!function(e){e[e.ACTIVE=0]="ACTIVE",e[e.INACTIVE=1]="INACTIVE"}(z||(z={})),function(e){e[e.START=1]="START",e[e.END=2]="END"}(M||(M={}));
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
var Z={animation:{prefixed:"-webkit-animation",standard:"animation"},transform:{prefixed:"-webkit-transform",standard:"transform"},transition:{prefixed:"-webkit-transition",standard:"transition"}};function H(e,t){if(function(e){return Boolean(e.document)&&"function"==typeof e.document.createElement}(e)&&t in Z){var i=e.document.createElement("div"),r=Z[t],s=r.standard,a=r.prefixed;return s in i.style?s:a}return t}
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
 */var U,O="mdc-slider--disabled",V="mdc-slider--discrete",G="mdc-slider--range",X="mdc-slider__thumb--focused",q="mdc-slider__thumb--top",K="mdc-slider__thumb--with-indicator",Y="mdc-slider--tick-marks",J=1,Q=0,ee=5,te="aria-valuetext",ie="disabled",re="min",se="max",ae="value",oe="step",ne="data-min-range",de="--slider-value-indicator-caret-left",ce="--slider-value-indicator-caret-right",le="--slider-value-indicator-caret-transform",he="--slider-value-indicator-container-left",ue="--slider-value-indicator-container-right",pe="--slider-value-indicator-container-transform";!function(e){e.SLIDER_UPDATE="slider_update"}(U||(U={}));var me="undefined"!=typeof window,ve=function(e){function t(i){var r=e.call(this,p(p({},t.defaultAdapter),i))||this;return r.initialStylesRemoved=!1,r.isDisabled=!1,r.isDiscrete=!1,r.step=J,r.minRange=Q,r.hasTickMarks=!1,r.isRange=!1,r.thumb=null,r.downEventClientX=null,r.startThumbKnobWidth=0,r.endThumbKnobWidth=0,r.animFrame=new m,r}return u(t,e),Object.defineProperty(t,"defaultAdapter",{get:function(){return{hasClass:function(){return!1},addClass:function(){},removeClass:function(){},addThumbClass:function(){},removeThumbClass:function(){},getAttribute:function(){return null},getInputValue:function(){return""},setInputValue:function(){},getInputAttribute:function(){return null},setInputAttribute:function(){return null},removeInputAttribute:function(){return null},focusInput:function(){},isInputFocused:function(){return!1},shouldHideFocusStylesForPointerEvents:function(){return!1},getThumbKnobWidth:function(){return 0},getValueIndicatorContainerWidth:function(){return 0},getThumbBoundingClientRect:function(){return{top:0,right:0,bottom:0,left:0,width:0,height:0}},getBoundingClientRect:function(){return{top:0,right:0,bottom:0,left:0,width:0,height:0}},isRTL:function(){return!1},setThumbStyleProperty:function(){},removeThumbStyleProperty:function(){},setTrackActiveStyleProperty:function(){},removeTrackActiveStyleProperty:function(){},setValueIndicatorText:function(){},getValueToAriaValueTextFn:function(){return null},updateTickMarks:function(){},setPointerCapture:function(){},emitChangeEvent:function(){},emitInputEvent:function(){},emitDragStartEvent:function(){},emitDragEndEvent:function(){},registerEventHandler:function(){},deregisterEventHandler:function(){},registerThumbEventHandler:function(){},deregisterThumbEventHandler:function(){},registerInputEventHandler:function(){},deregisterInputEventHandler:function(){},registerBodyEventHandler:function(){},deregisterBodyEventHandler:function(){},registerWindowEventHandler:function(){},deregisterWindowEventHandler:function(){}}},enumerable:!1,configurable:!0}),t.prototype.init=function(){var e=this;this.isDisabled=this.adapter.hasClass(O),this.isDiscrete=this.adapter.hasClass(V),this.hasTickMarks=this.adapter.hasClass(Y),this.isRange=this.adapter.hasClass(G);var t=this.convertAttributeValueToNumber(this.adapter.getInputAttribute(re,this.isRange?M.START:M.END),re),i=this.convertAttributeValueToNumber(this.adapter.getInputAttribute(se,M.END),se),r=this.convertAttributeValueToNumber(this.adapter.getInputAttribute(ae,M.END),ae),s=this.isRange?this.convertAttributeValueToNumber(this.adapter.getInputAttribute(ae,M.START),ae):t,a=this.adapter.getInputAttribute(oe,M.END),o=a?this.convertAttributeValueToNumber(a,oe):this.step,n=this.adapter.getAttribute(ne),d=n?this.convertAttributeValueToNumber(n,ne):this.minRange;this.validateProperties({min:t,max:i,value:r,valueStart:s,step:o,minRange:d}),this.min=t,this.max=i,this.value=r,this.valueStart=s,this.step=o,this.minRange=d,this.numDecimalPlaces=_e(this.step),this.valueBeforeDownEvent=r,this.valueStartBeforeDownEvent=s,this.mousedownOrTouchstartListener=this.handleMousedownOrTouchstart.bind(this),this.moveListener=this.handleMove.bind(this),this.pointerdownListener=this.handlePointerdown.bind(this),this.pointerupListener=this.handlePointerup.bind(this),this.thumbMouseenterListener=this.handleThumbMouseenter.bind(this),this.thumbMouseleaveListener=this.handleThumbMouseleave.bind(this),this.inputStartChangeListener=function(){e.handleInputChange(M.START)},this.inputEndChangeListener=function(){e.handleInputChange(M.END)},this.inputStartFocusListener=function(){e.handleInputFocus(M.START)},this.inputEndFocusListener=function(){e.handleInputFocus(M.END)},this.inputStartBlurListener=function(){e.handleInputBlur(M.START)},this.inputEndBlurListener=function(){e.handleInputBlur(M.END)},this.resizeListener=this.handleResize.bind(this),this.registerEventHandlers()},t.prototype.destroy=function(){this.deregisterEventHandlers()},t.prototype.setMin=function(e){this.min=e,this.isRange||(this.valueStart=e),this.updateUI()},t.prototype.setMax=function(e){this.max=e,this.updateUI()},t.prototype.getMin=function(){return this.min},t.prototype.getMax=function(){return this.max},t.prototype.getValue=function(){return this.value},t.prototype.setValue=function(e){if(this.isRange&&e<this.valueStart+this.minRange)throw new Error("end thumb value ("+e+") must be >= start thumb value ("+this.valueStart+") + min range ("+this.minRange+")");this.updateValue(e,M.END)},t.prototype.getValueStart=function(){if(!this.isRange)throw new Error("`valueStart` is only applicable for range sliders.");return this.valueStart},t.prototype.setValueStart=function(e){if(!this.isRange)throw new Error("`valueStart` is only applicable for range sliders.");if(this.isRange&&e>this.value-this.minRange)throw new Error("start thumb value ("+e+") must be <= end thumb value ("+this.value+") - min range ("+this.minRange+")");this.updateValue(e,M.START)},t.prototype.setStep=function(e){this.step=e,this.numDecimalPlaces=_e(e),this.updateUI()},t.prototype.setMinRange=function(e){if(!this.isRange)throw new Error("`minRange` is only applicable for range sliders.");if(e<0)throw new Error("`minRange` must be non-negative. Current value: "+e);if(this.value-this.valueStart<e)throw new Error("start thumb value ("+this.valueStart+") and end thumb value ("+this.value+") must differ by at least "+e+".");this.minRange=e},t.prototype.setIsDiscrete=function(e){this.isDiscrete=e,this.updateValueIndicatorUI(),this.updateTickMarksUI()},t.prototype.getStep=function(){return this.step},t.prototype.getMinRange=function(){if(!this.isRange)throw new Error("`minRange` is only applicable for range sliders.");return this.minRange},t.prototype.setHasTickMarks=function(e){this.hasTickMarks=e,this.updateTickMarksUI()},t.prototype.getDisabled=function(){return this.isDisabled},t.prototype.setDisabled=function(e){this.isDisabled=e,e?(this.adapter.addClass(O),this.isRange&&this.adapter.setInputAttribute(ie,"",M.START),this.adapter.setInputAttribute(ie,"",M.END)):(this.adapter.removeClass(O),this.isRange&&this.adapter.removeInputAttribute(ie,M.START),this.adapter.removeInputAttribute(ie,M.END))},t.prototype.getIsRange=function(){return this.isRange},t.prototype.layout=function(e){var t=(void 0===e?{}:e).skipUpdateUI;this.rect=this.adapter.getBoundingClientRect(),this.isRange&&(this.startThumbKnobWidth=this.adapter.getThumbKnobWidth(M.START),this.endThumbKnobWidth=this.adapter.getThumbKnobWidth(M.END)),t||this.updateUI()},t.prototype.handleResize=function(){this.layout()},t.prototype.handleDown=function(e){if(!this.isDisabled){this.valueStartBeforeDownEvent=this.valueStart,this.valueBeforeDownEvent=this.value;var t=null!=e.clientX?e.clientX:e.targetTouches[0].clientX;this.downEventClientX=t;var i=this.mapClientXOnSliderScale(t);this.thumb=this.getThumbFromDownEvent(t,i),null!==this.thumb&&(this.handleDragStart(e,i,this.thumb),this.updateValue(i,this.thumb,{emitInputEvent:!0}))}},t.prototype.handleMove=function(e){if(!this.isDisabled){e.preventDefault();var t=null!=e.clientX?e.clientX:e.targetTouches[0].clientX,i=null!=this.thumb;if(this.thumb=this.getThumbFromMoveEvent(t),null!==this.thumb){var r=this.mapClientXOnSliderScale(t);i||(this.handleDragStart(e,r,this.thumb),this.adapter.emitDragStartEvent(r,this.thumb)),this.updateValue(r,this.thumb,{emitInputEvent:!0})}}},t.prototype.handleUp=function(){var e,t;if(!this.isDisabled&&null!==this.thumb){(null===(t=(e=this.adapter).shouldHideFocusStylesForPointerEvents)||void 0===t?void 0:t.call(e))&&this.handleInputBlur(this.thumb);var i=this.thumb===M.START?this.valueStartBeforeDownEvent:this.valueBeforeDownEvent,r=this.thumb===M.START?this.valueStart:this.value;i!==r&&this.adapter.emitChangeEvent(r,this.thumb),this.adapter.emitDragEndEvent(r,this.thumb),this.thumb=null}},t.prototype.handleThumbMouseenter=function(){this.isDiscrete&&this.isRange&&(this.adapter.addThumbClass(K,M.START),this.adapter.addThumbClass(K,M.END))},t.prototype.handleThumbMouseleave=function(){var e,t;this.isDiscrete&&this.isRange&&(!(null===(t=(e=this.adapter).shouldHideFocusStylesForPointerEvents)||void 0===t?void 0:t.call(e))&&(this.adapter.isInputFocused(M.START)||this.adapter.isInputFocused(M.END))||this.thumb||(this.adapter.removeThumbClass(K,M.START),this.adapter.removeThumbClass(K,M.END)))},t.prototype.handleMousedownOrTouchstart=function(e){var t=this,i="mousedown"===e.type?"mousemove":"touchmove";this.adapter.registerBodyEventHandler(i,this.moveListener);var r=function(){t.handleUp(),t.adapter.deregisterBodyEventHandler(i,t.moveListener),t.adapter.deregisterEventHandler("mouseup",r),t.adapter.deregisterEventHandler("touchend",r)};this.adapter.registerBodyEventHandler("mouseup",r),this.adapter.registerBodyEventHandler("touchend",r),this.handleDown(e)},t.prototype.handlePointerdown=function(e){0===e.button&&(null!=e.pointerId&&this.adapter.setPointerCapture(e.pointerId),this.adapter.registerEventHandler("pointermove",this.moveListener),this.handleDown(e))},t.prototype.handleInputChange=function(e){var t=Number(this.adapter.getInputValue(e));e===M.START?this.setValueStart(t):this.setValue(t),this.adapter.emitChangeEvent(e===M.START?this.valueStart:this.value,e),this.adapter.emitInputEvent(e===M.START?this.valueStart:this.value,e)},t.prototype.handleInputFocus=function(e){if(this.adapter.addThumbClass(X,e),this.isDiscrete&&(this.adapter.addThumbClass(K,e),this.isRange)){var t=e===M.START?M.END:M.START;this.adapter.addThumbClass(K,t)}},t.prototype.handleInputBlur=function(e){if(this.adapter.removeThumbClass(X,e),this.isDiscrete&&(this.adapter.removeThumbClass(K,e),this.isRange)){var t=e===M.START?M.END:M.START;this.adapter.removeThumbClass(K,t)}},t.prototype.handleDragStart=function(e,t,i){var r,s;this.adapter.emitDragStartEvent(t,i),this.adapter.focusInput(i),(null===(s=(r=this.adapter).shouldHideFocusStylesForPointerEvents)||void 0===s?void 0:s.call(r))&&this.handleInputFocus(i),e.preventDefault()},t.prototype.getThumbFromDownEvent=function(e,t){if(!this.isRange)return M.END;var i=this.adapter.getThumbBoundingClientRect(M.START),r=this.adapter.getThumbBoundingClientRect(M.END),s=e>=i.left&&e<=i.right,a=e>=r.left&&e<=r.right;return s&&a?null:s?M.START:a?M.END:t<this.valueStart?M.START:t>this.value?M.END:t-this.valueStart<=this.value-t?M.START:M.END},t.prototype.getThumbFromMoveEvent=function(e){if(null!==this.thumb)return this.thumb;if(null===this.downEventClientX)throw new Error("`downEventClientX` is null after move event.");return Math.abs(this.downEventClientX-e)<ee?this.thumb:e<this.downEventClientX?this.adapter.isRTL()?M.END:M.START:this.adapter.isRTL()?M.START:M.END},t.prototype.updateUI=function(e){e?this.updateThumbAndInputAttributes(e):(this.updateThumbAndInputAttributes(M.START),this.updateThumbAndInputAttributes(M.END)),this.updateThumbAndTrackUI(e),this.updateValueIndicatorUI(e),this.updateTickMarksUI()},t.prototype.updateThumbAndInputAttributes=function(e){if(e){var t=this.isRange&&e===M.START?this.valueStart:this.value,i=String(t);this.adapter.setInputAttribute(ae,i,e),this.isRange&&e===M.START?this.adapter.setInputAttribute(re,String(t+this.minRange),M.END):this.isRange&&e===M.END&&this.adapter.setInputAttribute(se,String(t-this.minRange),M.START),this.adapter.getInputValue(e)!==i&&this.adapter.setInputValue(i,e);var r=this.adapter.getValueToAriaValueTextFn();r&&this.adapter.setInputAttribute(te,r(t,e),e)}},t.prototype.updateValueIndicatorUI=function(e){if(this.isDiscrete){var t=this.isRange&&e===M.START?this.valueStart:this.value;this.adapter.setValueIndicatorText(t,e===M.START?M.START:M.END),!e&&this.isRange&&this.adapter.setValueIndicatorText(this.valueStart,M.START)}},t.prototype.updateTickMarksUI=function(){if(this.isDiscrete&&this.hasTickMarks){var e=(this.valueStart-this.min)/this.step,t=(this.value-this.valueStart)/this.step+1,i=(this.max-this.value)/this.step,r=Array.from({length:e}).fill(z.INACTIVE),s=Array.from({length:t}).fill(z.ACTIVE),a=Array.from({length:i}).fill(z.INACTIVE);this.adapter.updateTickMarks(r.concat(s).concat(a))}},t.prototype.mapClientXOnSliderScale=function(e){var t=(e-this.rect.left)/this.rect.width;this.adapter.isRTL()&&(t=1-t);var i=this.min+t*(this.max-this.min);return i===this.max||i===this.min?i:Number(this.quantize(i).toFixed(this.numDecimalPlaces))},t.prototype.quantize=function(e){var t=Math.round((e-this.min)/this.step);return this.min+t*this.step},t.prototype.updateValue=function(e,t,i){var r=(void 0===i?{}:i).emitInputEvent;if(e=this.clampValue(e,t),this.isRange&&t===M.START){if(this.valueStart===e)return;this.valueStart=e}else{if(this.value===e)return;this.value=e}this.updateUI(t),r&&this.adapter.emitInputEvent(t===M.START?this.valueStart:this.value,t)},t.prototype.clampValue=function(e,t){return e=Math.min(Math.max(e,this.min),this.max),this.isRange&&t===M.START&&e>this.value-this.minRange?this.value-this.minRange:this.isRange&&t===M.END&&e<this.valueStart+this.minRange?this.valueStart+this.minRange:e},t.prototype.updateThumbAndTrackUI=function(e){var t=this,i=this.max,r=this.min,s=(this.value-this.valueStart)/(i-r),a=s*this.rect.width,o=this.adapter.isRTL(),n=me?H(window,"transform"):"transform";if(this.isRange){var d=this.adapter.isRTL()?(i-this.value)/(i-r)*this.rect.width:(this.valueStart-r)/(i-r)*this.rect.width,c=d+a;this.animFrame.request(U.SLIDER_UPDATE,(function(){!o&&e===M.START||o&&e!==M.START?(t.adapter.setTrackActiveStyleProperty("transform-origin","right"),t.adapter.setTrackActiveStyleProperty("left","auto"),t.adapter.setTrackActiveStyleProperty("right",t.rect.width-c+"px")):(t.adapter.setTrackActiveStyleProperty("transform-origin","left"),t.adapter.setTrackActiveStyleProperty("right","auto"),t.adapter.setTrackActiveStyleProperty("left",d+"px")),t.adapter.setTrackActiveStyleProperty(n,"scaleX("+s+")");var i=o?c:d,r=t.adapter.isRTL()?d:c;e!==M.START&&e&&t.initialStylesRemoved||(t.adapter.setThumbStyleProperty(n,"translateX("+i+"px)",M.START),t.alignValueIndicator(M.START,i)),e!==M.END&&e&&t.initialStylesRemoved||(t.adapter.setThumbStyleProperty(n,"translateX("+r+"px)",M.END),t.alignValueIndicator(M.END,r)),t.removeInitialStyles(o),t.updateOverlappingThumbsUI(i,r,e)}))}else this.animFrame.request(U.SLIDER_UPDATE,(function(){var e=o?t.rect.width-a:a;t.adapter.setThumbStyleProperty(n,"translateX("+e+"px)",M.END),t.alignValueIndicator(M.END,e),t.adapter.setTrackActiveStyleProperty(n,"scaleX("+s+")"),t.removeInitialStyles(o)}))},t.prototype.alignValueIndicator=function(e,t){if(this.isDiscrete){var i=this.adapter.getThumbBoundingClientRect(e).width/2,r=this.adapter.getValueIndicatorContainerWidth(e),s=this.adapter.getBoundingClientRect().width;r/2>t+i?(this.adapter.setThumbStyleProperty(de,i+"px",e),this.adapter.setThumbStyleProperty(ce,"auto",e),this.adapter.setThumbStyleProperty(le,"translateX(-50%)",e),this.adapter.setThumbStyleProperty(he,"0",e),this.adapter.setThumbStyleProperty(ue,"auto",e),this.adapter.setThumbStyleProperty(pe,"none",e)):r/2>s-t+i?(this.adapter.setThumbStyleProperty(de,"auto",e),this.adapter.setThumbStyleProperty(ce,i+"px",e),this.adapter.setThumbStyleProperty(le,"translateX(50%)",e),this.adapter.setThumbStyleProperty(he,"auto",e),this.adapter.setThumbStyleProperty(ue,"0",e),this.adapter.setThumbStyleProperty(pe,"none",e)):(this.adapter.setThumbStyleProperty(de,"50%",e),this.adapter.setThumbStyleProperty(ce,"auto",e),this.adapter.setThumbStyleProperty(le,"translateX(-50%)",e),this.adapter.setThumbStyleProperty(he,"50%",e),this.adapter.setThumbStyleProperty(ue,"auto",e),this.adapter.setThumbStyleProperty(pe,"translateX(-50%)",e))}},t.prototype.removeInitialStyles=function(e){if(!this.initialStylesRemoved){var t=e?"right":"left";this.adapter.removeThumbStyleProperty(t,M.END),this.isRange&&this.adapter.removeThumbStyleProperty(t,M.START),this.initialStylesRemoved=!0,this.resetTrackAndThumbAnimation()}},t.prototype.resetTrackAndThumbAnimation=function(){var e=this;if(this.isDiscrete){var t=me?H(window,"transition"):"transition",i="none 0s ease 0s";this.adapter.setThumbStyleProperty(t,i,M.END),this.isRange&&this.adapter.setThumbStyleProperty(t,i,M.START),this.adapter.setTrackActiveStyleProperty(t,i),requestAnimationFrame((function(){e.adapter.removeThumbStyleProperty(t,M.END),e.adapter.removeTrackActiveStyleProperty(t),e.isRange&&e.adapter.removeThumbStyleProperty(t,M.START)}))}},t.prototype.updateOverlappingThumbsUI=function(e,t,i){var r=!1;if(this.adapter.isRTL()){var s=e-this.startThumbKnobWidth/2;r=t+this.endThumbKnobWidth/2>=s}else{r=e+this.startThumbKnobWidth/2>=t-this.endThumbKnobWidth/2}r?(this.adapter.addThumbClass(q,i||M.END),this.adapter.removeThumbClass(q,i===M.START?M.END:M.START)):(this.adapter.removeThumbClass(q,M.START),this.adapter.removeThumbClass(q,M.END))},t.prototype.convertAttributeValueToNumber=function(e,t){if(null===e)throw new Error("MDCSliderFoundation: `"+t+"` must be non-null.");var i=Number(e);if(isNaN(i))throw new Error("MDCSliderFoundation: `"+t+"` value is `"+e+"`, but must be a number.");return i},t.prototype.validateProperties=function(e){var t=e.min,i=e.max,r=e.value,s=e.valueStart,a=e.step,o=e.minRange;if(t>=i)throw new Error("MDCSliderFoundation: min must be strictly less than max. Current: [min: "+t+", max: "+i+"]");if(a<=0)throw new Error("MDCSliderFoundation: step must be a positive number. Current step: "+a);if(this.isRange){if(r<t||r>i||s<t||s>i)throw new Error("MDCSliderFoundation: values must be in [min, max] range. Current values: [start value: "+s+", end value: "+r+", min: "+t+", max: "+i+"]");if(s>r)throw new Error("MDCSliderFoundation: start value must be <= end value. Current values: [start value: "+s+", end value: "+r+"]");if(o<0)throw new Error("MDCSliderFoundation: minimum range must be non-negative. Current min range: "+o);if(r-s<o)throw new Error("MDCSliderFoundation: start value and end value must differ by at least "+o+". Current values: [start value: "+s+", end value: "+r+"]");var n=(s-t)/a,d=(r-t)/a;if(!Number.isInteger(parseFloat(n.toFixed(6)))||!Number.isInteger(parseFloat(d.toFixed(6))))throw new Error("MDCSliderFoundation: Slider values must be valid based on the step value ("+a+"). Current values: [start value: "+s+", end value: "+r+", min: "+t+"]")}else{if(r<t||r>i)throw new Error("MDCSliderFoundation: value must be in [min, max] range. Current values: [value: "+r+", min: "+t+", max: "+i+"]");d=(r-t)/a;if(!Number.isInteger(parseFloat(d.toFixed(6))))throw new Error("MDCSliderFoundation: Slider value must be valid based on the step value ("+a+"). Current value: "+r)}},t.prototype.registerEventHandlers=function(){this.adapter.registerWindowEventHandler("resize",this.resizeListener),t.SUPPORTS_POINTER_EVENTS?(this.adapter.registerEventHandler("pointerdown",this.pointerdownListener),this.adapter.registerEventHandler("pointerup",this.pointerupListener)):(this.adapter.registerEventHandler("mousedown",this.mousedownOrTouchstartListener),this.adapter.registerEventHandler("touchstart",this.mousedownOrTouchstartListener)),this.isRange&&(this.adapter.registerThumbEventHandler(M.START,"mouseenter",this.thumbMouseenterListener),this.adapter.registerThumbEventHandler(M.START,"mouseleave",this.thumbMouseleaveListener),this.adapter.registerInputEventHandler(M.START,"change",this.inputStartChangeListener),this.adapter.registerInputEventHandler(M.START,"focus",this.inputStartFocusListener),this.adapter.registerInputEventHandler(M.START,"blur",this.inputStartBlurListener)),this.adapter.registerThumbEventHandler(M.END,"mouseenter",this.thumbMouseenterListener),this.adapter.registerThumbEventHandler(M.END,"mouseleave",this.thumbMouseleaveListener),this.adapter.registerInputEventHandler(M.END,"change",this.inputEndChangeListener),this.adapter.registerInputEventHandler(M.END,"focus",this.inputEndFocusListener),this.adapter.registerInputEventHandler(M.END,"blur",this.inputEndBlurListener)},t.prototype.deregisterEventHandlers=function(){this.adapter.deregisterWindowEventHandler("resize",this.resizeListener),t.SUPPORTS_POINTER_EVENTS?(this.adapter.deregisterEventHandler("pointerdown",this.pointerdownListener),this.adapter.deregisterEventHandler("pointerup",this.pointerupListener)):(this.adapter.deregisterEventHandler("mousedown",this.mousedownOrTouchstartListener),this.adapter.deregisterEventHandler("touchstart",this.mousedownOrTouchstartListener)),this.isRange&&(this.adapter.deregisterThumbEventHandler(M.START,"mouseenter",this.thumbMouseenterListener),this.adapter.deregisterThumbEventHandler(M.START,"mouseleave",this.thumbMouseleaveListener),this.adapter.deregisterInputEventHandler(M.START,"change",this.inputStartChangeListener),this.adapter.deregisterInputEventHandler(M.START,"focus",this.inputStartFocusListener),this.adapter.deregisterInputEventHandler(M.START,"blur",this.inputStartBlurListener)),this.adapter.deregisterThumbEventHandler(M.END,"mouseenter",this.thumbMouseenterListener),this.adapter.deregisterThumbEventHandler(M.END,"mouseleave",this.thumbMouseleaveListener),this.adapter.deregisterInputEventHandler(M.END,"change",this.inputEndChangeListener),this.adapter.deregisterInputEventHandler(M.END,"focus",this.inputEndFocusListener),this.adapter.deregisterInputEventHandler(M.END,"blur",this.inputEndBlurListener)},t.prototype.handlePointerup=function(){this.handleUp(),this.adapter.deregisterEventHandler("pointermove",this.moveListener)},t.SUPPORTS_POINTER_EVENTS=me&&Boolean(window.PointerEvent)&&!(["iPad Simulator","iPhone Simulator","iPod Simulator","iPad","iPhone","iPod"].includes(navigator.platform)||navigator.userAgent.includes("Mac")&&"ontouchend"in document),t}(v);function _e(e){var t=/(?:\.(\d+))?(?:[eE]([+\-]?\d+))?$/.exec(String(e));if(!t)return 0;var i=t[1]||"",r=t[2]||0;return Math.max(0,("0"===i?0:i.length)-Number(r))}
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */class be extends w{constructor(){super(...arguments),this.mdcFoundationClass=ve,this.disabled=!1,this.min=0,this.max=100,this.valueEnd=0,this.name="",this.step=1,this.withTickMarks=!1,this.discrete=!1,this.tickMarks=[],this.trackTransformOriginStyle="",this.trackLeftStyle="",this.trackRightStyle="",this.trackTransitionStyle="",this.endThumbWithIndicator=!1,this.endThumbTop=!1,this.shouldRenderEndRipple=!1,this.endThumbTransformStyle="",this.endThumbTransitionStyle="",this.endThumbCssProperties={},this.valueToAriaTextTransform=null,this.valueToValueIndicatorTransform=e=>`${e}`,this.boundMoveListener=null,this.endRippleHandlers=new x((()=>(this.shouldRenderEndRipple=!0,this.endRipple)))}update(e){if(e.has("valueEnd")&&this.mdcFoundation){this.mdcFoundation.setValue(this.valueEnd);const e=this.mdcFoundation.getValue();e!==this.valueEnd&&(this.valueEnd=e)}e.has("discrete")&&(this.discrete||(this.tickMarks=[])),super.update(e)}render(){return this.renderRootEl(T`
      ${this.renderStartInput()}
      ${this.renderEndInput()}
      ${this.renderTrack()}
      ${this.renderTickMarks()}
      ${this.renderStartThumb()}
      ${this.renderEndThumb()}`)}renderRootEl(e){const t=k({"mdc-slider--disabled":this.disabled,"mdc-slider--discrete":this.discrete});return T`
    <div
        class="mdc-slider ${t}"
        @pointerdown=${this.onPointerdown}
        @pointerup=${this.onPointerup}
        @contextmenu=${this.onContextmenu}>
      ${e}
    </div>`}renderStartInput(){return S}renderEndInput(){var e;return T`
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
          aria-label=${E(this.ariaLabel)}
          aria-labelledby=${E(this.ariaLabelledBy)}
          aria-describedby=${E(this.ariaDescribedBy)}
          aria-valuetext=${E(null===(e=this.valueToAriaTextTransform)||void 0===e?void 0:e.call(this,this.valueEnd))}>
    `}renderTrack(){return S}renderTickMarks(){return this.withTickMarks?T`
      <div class="mdc-slider__tick-marks">
        ${this.tickMarks.map((e=>{const t=e===z.ACTIVE;return T`<div class="${t?"mdc-slider__tick-mark--active":"mdc-slider__tick-mark--inactive"}"></div>`}))}
      </div>`:S}renderStartThumb(){return S}renderEndThumb(){const e=k({"mdc-slider__thumb--with-indicator":this.endThumbWithIndicator,"mdc-slider__thumb--top":this.endThumbTop}),t=$(Object.assign({"-webkit-transform":this.endThumbTransformStyle,transform:this.endThumbTransformStyle,"-webkit-transition":this.endThumbTransitionStyle,transition:this.endThumbTransitionStyle,left:this.endThumbTransformStyle||"rtl"===getComputedStyle(this).direction?"":`calc(${(this.valueEnd-this.min)/(this.max-this.min)*100}% - 24px)`,right:this.endThumbTransformStyle||"rtl"!==getComputedStyle(this).direction?"":`calc(${(this.valueEnd-this.min)/(this.max-this.min)*100}% - 24px)`},this.endThumbCssProperties)),i=this.shouldRenderEndRipple?T`<mwc-ripple class="ripple" unbounded></mwc-ripple>`:S;return T`
      <div
          class="mdc-slider__thumb end ${e}"
          style=${t}
          @mouseenter=${this.onEndMouseenter}
          @mouseleave=${this.onEndMouseleave}>
        ${i}
        ${this.renderValueIndicator(this.valueToValueIndicatorTransform(this.valueEnd))}
        <div class="mdc-slider__thumb-knob"></div>
      </div>
    `}renderValueIndicator(e){return this.discrete?T`
    <div class="mdc-slider__value-indicator-container" aria-hidden="true">
      <div class="mdc-slider__value-indicator">
        <span class="mdc-slider__value-indicator-text">
          ${e}
        </span>
      </div>
    </div>`:S}disconnectedCallback(){super.disconnectedCallback(),this.mdcFoundation&&this.mdcFoundation.destroy()}createAdapter(){}async firstUpdated(){super.firstUpdated(),await this.layout(!0)}updated(e){super.updated(e),this.mdcFoundation&&(e.has("disabled")&&this.mdcFoundation.setDisabled(this.disabled),e.has("min")&&this.mdcFoundation.setMin(this.min),e.has("max")&&this.mdcFoundation.setMax(this.max),e.has("step")&&this.mdcFoundation.setStep(this.step),e.has("discrete")&&this.mdcFoundation.setIsDiscrete(this.discrete),e.has("withTickMarks")&&this.mdcFoundation.setHasTickMarks(this.withTickMarks))}async layout(e=!1){var t;null===(t=this.mdcFoundation)||void 0===t||t.layout({skipUpdateUI:e}),this.requestUpdate(),await this.updateComplete}onEndChange(e){var t;this.valueEnd=Number(e.target.value),null===(t=this.mdcFoundation)||void 0===t||t.handleInputChange(M.END)}onEndFocus(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleInputFocus(M.END),this.endRippleHandlers.startFocus()}onEndBlur(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleInputBlur(M.END),this.endRippleHandlers.endFocus()}onEndMouseenter(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleThumbMouseenter(),this.endRippleHandlers.startHover()}onEndMouseleave(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleThumbMouseleave(),this.endRippleHandlers.endHover()}onPointerdown(e){this.layout(),this.mdcFoundation&&(this.mdcFoundation.handlePointerdown(e),this.boundMoveListener=this.mdcFoundation.handleMove.bind(this.mdcFoundation),this.mdcRoot.addEventListener("pointermove",this.boundMoveListener))}onPointerup(){this.mdcFoundation&&(this.mdcFoundation.handleUp(),this.boundMoveListener&&(this.mdcRoot.removeEventListener("pointermove",this.boundMoveListener),this.boundMoveListener=null))}onContextmenu(e){e.preventDefault()}setFormData(e){this.name&&e.append(this.name,`${this.valueEnd}`)}}e([_("input.end")],be.prototype,"formElement",void 0),e([_(".mdc-slider")],be.prototype,"mdcRoot",void 0),e([_(".end.mdc-slider__thumb")],be.prototype,"endThumb",void 0),e([_(".end.mdc-slider__thumb .mdc-slider__thumb-knob")],be.prototype,"endThumbKnob",void 0),e([_(".end.mdc-slider__thumb .mdc-slider__value-indicator-container")],be.prototype,"endValueIndicatorContainer",void 0),e([b(".end .ripple")],be.prototype,"endRipple",void 0),e([g({type:Boolean,reflect:!0})],be.prototype,"disabled",void 0),e([g({type:Number})],be.prototype,"min",void 0),e([g({type:Number})],be.prototype,"max",void 0),e([g({type:Number})],be.prototype,"valueEnd",void 0),e([g({type:String})],be.prototype,"name",void 0),e([g({type:Number})],be.prototype,"step",void 0),e([g({type:Boolean})],be.prototype,"withTickMarks",void 0),e([g({type:Boolean})],be.prototype,"discrete",void 0),e([f()],be.prototype,"tickMarks",void 0),e([f()],be.prototype,"trackTransformOriginStyle",void 0),e([f()],be.prototype,"trackLeftStyle",void 0),e([f()],be.prototype,"trackRightStyle",void 0),e([f()],be.prototype,"trackTransitionStyle",void 0),e([f()],be.prototype,"endThumbWithIndicator",void 0),e([f()],be.prototype,"endThumbTop",void 0),e([f()],be.prototype,"shouldRenderEndRipple",void 0),e([f()],be.prototype,"endThumbTransformStyle",void 0),e([f()],be.prototype,"endThumbTransitionStyle",void 0),e([f()],be.prototype,"endThumbCssProperties",void 0),e([y,g({type:String,attribute:"aria-label"})],be.prototype,"ariaLabel",void 0),e([y,g({type:String,attribute:"aria-labelledby"})],be.prototype,"ariaLabelledBy",void 0),e([y,g({type:String,attribute:"aria-describedby"})],be.prototype,"ariaDescribedBy",void 0);
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
class ge extends be{get value(){return this.valueEnd}set value(e){this.valueEnd=e}renderTrack(){const e=$({"transform-origin":this.trackTransformOriginStyle,left:this.trackLeftStyle,right:this.trackRightStyle,"-webkit-transform":`scaleX(${(this.valueEnd-this.min)/(this.max-this.min)})`,transform:`scaleX(${(this.valueEnd-this.min)/(this.max-this.min)})`,"-webkit-transition":this.trackTransitionStyle,transition:this.trackTransitionStyle});return T`
      <div class="mdc-slider__track">
        <div class="mdc-slider__track--inactive"></div>
        <div class="mdc-slider__track--active">
          <div
              class="mdc-slider__track--active_fill"
              style=${e}>
          </div>
        </div>
      </div>`}createAdapter(){return{addClass:e=>{if("mdc-slider--disabled"===e)this.disabled=!0},removeClass:e=>{if("mdc-slider--disabled"===e)this.disabled=!1},hasClass:e=>{switch(e){case"mdc-slider--disabled":return this.disabled;case"mdc-slider--discrete":return this.discrete;default:return!1}},addThumbClass:(e,t)=>{if(t!==M.START&&"mdc-slider__thumb--with-indicator"===e)this.endThumbWithIndicator=!0},removeThumbClass:(e,t)=>{if(t!==M.START&&"mdc-slider__thumb--with-indicator"===e)this.endThumbWithIndicator=!1},registerEventHandler:()=>{},deregisterEventHandler:()=>{},registerBodyEventHandler:(e,t)=>{document.body.addEventListener(e,t)},deregisterBodyEventHandler:(e,t)=>{document.body.removeEventListener(e,t)},registerInputEventHandler:(e,t,i)=>{e!==M.START&&this.formElement.addEventListener(t,i)},deregisterInputEventHandler:(e,t,i)=>{e!==M.START&&this.formElement.removeEventListener(t,i)},registerThumbEventHandler:()=>{},deregisterThumbEventHandler:()=>{},registerWindowEventHandler:(e,t)=>{window.addEventListener(e,t)},deregisterWindowEventHandler:(e,t)=>{window.addEventListener(e,t)},emitChangeEvent:(e,t)=>{if(t===M.START)return;const i=new CustomEvent("change",{bubbles:!0,composed:!0,detail:{value:e,thumb:t}});this.dispatchEvent(i)},emitDragEndEvent:(e,t)=>{t!==M.START&&this.endRippleHandlers.endPress()},emitDragStartEvent:(e,t)=>{t!==M.START&&this.endRippleHandlers.startPress()},emitInputEvent:(e,t)=>{if(t===M.START)return;const i=new CustomEvent("input",{bubbles:!0,composed:!0,detail:{value:e,thumb:t}});this.dispatchEvent(i)},focusInput:e=>{e!==M.START&&this.formElement.focus()},getAttribute:()=>"",getBoundingClientRect:()=>this.mdcRoot.getBoundingClientRect(),getInputAttribute:(e,t)=>{if(t===M.START)return null;switch(e){case"min":return this.min.toString();case"max":return this.max.toString();case"value":return this.valueEnd.toString();case"step":return this.step.toString();default:return null}},getInputValue:e=>e===M.START?"":this.valueEnd.toString(),getThumbBoundingClientRect:e=>e===M.START?this.getBoundingClientRect():this.endThumb.getBoundingClientRect(),getThumbKnobWidth:e=>e===M.START?0:this.endThumbKnob.getBoundingClientRect().width,getValueIndicatorContainerWidth:e=>e===M.START?0:this.endValueIndicatorContainer.getBoundingClientRect().width,getValueToAriaValueTextFn:()=>this.valueToAriaTextTransform,isInputFocused:e=>{if(e===M.START)return!1;const t=R();return t[t.length-1]===this.formElement},isRTL:()=>"rtl"===getComputedStyle(this).direction,setInputAttribute:(e,t,i)=>{M.START},removeInputAttribute:e=>{},setThumbStyleProperty:(e,t,i)=>{if(i!==M.START)switch(e){case"transform":case"-webkit-transform":this.endThumbTransformStyle=t;break;case"transition":case"-webkit-transition":this.endThumbTransitionStyle=t;break;default:e.startsWith("--")&&(this.endThumbCssProperties[e]=t)}},removeThumbStyleProperty:(e,t)=>{if(t!==M.START)switch(e){case"left":case"right":break;case"transition":case"-webkit-transition":this.endThumbTransitionStyle=""}},setTrackActiveStyleProperty:(e,t)=>{switch(e){case"transform-origin":this.trackTransformOriginStyle=t;break;case"left":this.trackLeftStyle=t;break;case"right":this.trackRightStyle=t;break;case"transform":case"-webkit-transform":break;case"transition":case"-webkit-transition":this.trackTransitionStyle=t}},removeTrackActiveStyleProperty:e=>{switch(e){case"transition":case"-webkit-transition":this.trackTransitionStyle=""}},setInputValue:(e,t)=>{t!==M.START&&(this.valueEnd=Number(e))},setPointerCapture:e=>{this.mdcRoot.setPointerCapture(e)},setValueIndicatorText:()=>{},updateTickMarks:e=>{this.tickMarks=e}}}}e([g({type:Number})],ge.prototype,"value",null);
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
let fe=class extends ge{};fe.styles=[L],fe=e([P("mwc-slider")],fe);let ye=class extends r{static get styles(){return[s,a,o,n,d,c`
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
      `]}render(){return l`
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
function we(e,t,i){var r=function(e,t){var i=new Map;xe.has(e)||xe.set(e,{isEnabled:!0,getObservers:function(e){var t=i.get(e)||[];return i.has(e)||i.set(e,t),t},installedProperties:new Set});var r=xe.get(e);if(r.installedProperties.has(t))return r;var s=function(e,t){var i,r=e;for(;r&&!(i=Object.getOwnPropertyDescriptor(r,t));)r=Object.getPrototypeOf(r);return i}(e,t)||{configurable:!0,enumerable:!0,value:e[t],writable:!0},a=p({},s),o=s.get,n=s.set;if("value"in s){delete a.value,delete a.writable;var d=s.value;o=function(){return d},s.writable&&(n=function(e){d=e})}o&&(a.get=function(){return o.call(this)});n&&(a.set=function(e){var i,s,a=o?o.call(this):e;if(n.call(this,e),r.isEnabled&&(!o||e!==a))try{for(var d=F(r.getObservers(t)),c=d.next();!c.done;c=d.next()){(0,c.value)(e,a)}}catch(e){i={error:e}}finally{try{c&&!c.done&&(s=d.return)&&s.call(d)}finally{if(i)throw i.error}}});return r.installedProperties.add(t),Object.defineProperty(e,t,a),r}(e,t),s=r.getObservers(t);return s.push(i),function(){s.splice(s.indexOf(i),1)}}e([t({type:Number})],ye.prototype,"step",void 0),e([t({type:Number})],ye.prototype,"value",void 0),e([t({type:Number})],ye.prototype,"max",void 0),e([t({type:Number})],ye.prototype,"min",void 0),e([t({type:String})],ye.prototype,"prefix",void 0),e([t({type:String})],ye.prototype,"suffix",void 0),e([t({type:Boolean})],ye.prototype,"editable",void 0),e([t({type:Boolean})],ye.prototype,"pin",void 0),e([t({type:Boolean})],ye.prototype,"markers",void 0),e([t({type:Number})],ye.prototype,"marker_limit",void 0),e([t({type:Boolean})],ye.prototype,"disabled",void 0),e([j("#slider",!0)],ye.prototype,"slider",void 0),e([j("#textfield",!0)],ye.prototype,"textfield",void 0),ye=e([i("lablup-slider")],ye);var xe=new WeakMap;
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
var Te,ke,Se=function(e){function t(t){var i=e.call(this,t)||this;return i.unobserves=new Set,i}return u(t,e),t.prototype.destroy=function(){e.prototype.destroy.call(this),this.unobserve()},t.prototype.observe=function(e,t){var i,r,s=this,a=[];try{for(var o=F(Object.keys(t)),n=o.next();!n.done;n=o.next()){var d=n.value,c=t[d].bind(this);a.push(this.observeProperty(e,d,c))}}catch(e){i={error:e}}finally{try{n&&!n.done&&(r=o.return)&&r.call(o)}finally{if(i)throw i.error}}var l=function(){var e,t;try{for(var i=F(a),r=i.next();!r.done;r=i.next()){(0,r.value)()}}catch(t){e={error:t}}finally{try{r&&!r.done&&(t=i.return)&&t.call(i)}finally{if(e)throw e.error}}s.unobserves.delete(l)};return this.unobserves.add(l),l},t.prototype.observeProperty=function(e,t,i){return we(e,t,i)},t.prototype.setObserversEnabled=function(e,t){!function(e,t){var i=xe.get(e);i&&(i.isEnabled=t)}(e,t)},t.prototype.unobserve=function(){var e,t;try{for(var i=F(C([],W(this.unobserves))),r=i.next();!r.done;r=i.next()){(0,r.value)()}}catch(t){e={error:t}}finally{try{r&&!r.done&&(t=i.return)&&t.call(i)}finally{if(e)throw e.error}}},t}(v);
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
 */!function(e){e.PROCESSING="mdc-switch--processing",e.SELECTED="mdc-switch--selected",e.UNSELECTED="mdc-switch--unselected"}(Te||(Te={})),function(e){e.RIPPLE=".mdc-switch__ripple"}(ke||(ke={}));
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
var Ee=function(e){function t(t){var i=e.call(this,t)||this;return i.handleClick=i.handleClick.bind(i),i}return u(t,e),t.prototype.init=function(){this.observe(this.adapter.state,{disabled:this.stopProcessingIfDisabled,processing:this.stopProcessingIfDisabled})},t.prototype.handleClick=function(){this.adapter.state.disabled||(this.adapter.state.selected=!this.adapter.state.selected)},t.prototype.stopProcessingIfDisabled=function(){this.adapter.state.disabled&&(this.adapter.state.processing=!1)},t}(Se);!function(e){function t(){return null!==e&&e.apply(this,arguments)||this}u(t,e),t.prototype.init=function(){e.prototype.init.call(this),this.observe(this.adapter.state,{disabled:this.onDisabledChange,processing:this.onProcessingChange,selected:this.onSelectedChange})},t.prototype.initFromDOM=function(){this.setObserversEnabled(this.adapter.state,!1),this.adapter.state.selected=this.adapter.hasClass(Te.SELECTED),this.onSelectedChange(),this.adapter.state.disabled=this.adapter.isDisabled(),this.adapter.state.processing=this.adapter.hasClass(Te.PROCESSING),this.setObserversEnabled(this.adapter.state,!0),this.stopProcessingIfDisabled()},t.prototype.onDisabledChange=function(){this.adapter.setDisabled(this.adapter.state.disabled)},t.prototype.onProcessingChange=function(){this.toggleClass(this.adapter.state.processing,Te.PROCESSING)},t.prototype.onSelectedChange=function(){this.adapter.setAriaChecked(String(this.adapter.state.selected)),this.toggleClass(this.adapter.state.selected,Te.SELECTED),this.toggleClass(!this.adapter.state.selected,Te.UNSELECTED)},t.prototype.toggleClass=function(e,t){e?this.adapter.addClass(t):this.adapter.removeClass(t)}}(Ee);
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
class $e extends w{constructor(){super(...arguments),this.processing=!1,this.selected=!1,this.ariaLabel="",this.ariaLabelledBy="",this.shouldRenderRipple=!1,this.rippleHandlers=new x((()=>(this.shouldRenderRipple=!0,this.ripple))),this.name="",this.value="on",this.mdcFoundationClass=Ee}setFormData(e){this.name&&this.selected&&e.append(this.name,this.value)}click(){var e,t;this.disabled||(null===(e=this.mdcRoot)||void 0===e||e.focus(),null===(t=this.mdcRoot)||void 0===t||t.click())}render(){return T`
      <button
        type="button"
        class="mdc-switch ${k(this.getRenderClasses())}"
        role="switch"
        aria-checked="${this.selected}"
        aria-label="${E(this.ariaLabel||void 0)}"
        aria-labelledby="${E(this.ariaLabelledBy||void 0)}"
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
    `}getRenderClasses(){return{"mdc-switch--processing":this.processing,"mdc-switch--selected":this.selected,"mdc-switch--unselected":!this.selected}}renderHandle(){return T`
      <div class="mdc-switch__handle">
        ${this.renderShadow()}
        ${this.renderRipple()}
        <div class="mdc-switch__icons">
          ${this.renderOnIcon()}
          ${this.renderOffIcon()}
        </div>
      </div>
    `}renderShadow(){return T`
      <div class="mdc-switch__shadow">
        <div class="mdc-elevation-overlay"></div>
      </div>
    `}renderRipple(){return this.shouldRenderRipple?T`
        <div class="mdc-switch__ripple">
          <mwc-ripple
            internalUseStateLayerCustomProperties
            .disabled="${this.disabled}"
            unbounded>
          </mwc-ripple>
        </div>
      `:T``}renderOnIcon(){return T`
      <svg class="mdc-switch__icon mdc-switch__icon--on" viewBox="0 0 24 24">
        <path d="M19.69,5.23L8.96,15.96l-4.23-4.23L2.96,13.5l6,6L21.46,7L19.69,5.23z" />
      </svg>
    `}renderOffIcon(){return T`
      <svg class="mdc-switch__icon mdc-switch__icon--off" viewBox="0 0 24 24">
        <path d="M20 13H4v-2h16v2z" />
      </svg>
    `}handleClick(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleClick()}handleFocus(){this.rippleHandlers.startFocus()}handleBlur(){this.rippleHandlers.endFocus()}handlePointerDown(e){e.target.setPointerCapture(e.pointerId),this.rippleHandlers.startPress(e)}handlePointerUp(){this.rippleHandlers.endPress()}handlePointerEnter(){this.rippleHandlers.startHover()}handlePointerLeave(){this.rippleHandlers.endHover()}createAdapter(){return{state:this}}}e([g({type:Boolean})],$e.prototype,"processing",void 0),e([g({type:Boolean})],$e.prototype,"selected",void 0),e([y,g({type:String,attribute:"aria-label"})],$e.prototype,"ariaLabel",void 0),e([y,g({type:String,attribute:"aria-labelledby"})],$e.prototype,"ariaLabelledBy",void 0),e([b("mwc-ripple")],$e.prototype,"ripple",void 0),e([f()],$e.prototype,"shouldRenderRipple",void 0),e([g({type:String,reflect:!0})],$e.prototype,"name",void 0),e([g({type:String})],$e.prototype,"value",void 0),e([_("input")],$e.prototype,"formElement",void 0),e([_(".mdc-switch")],$e.prototype,"mdcRoot",void 0),e([A({passive:!0})],$e.prototype,"handlePointerDown",null);
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-LIcense-Identifier: Apache-2.0
 */
const Re=h`.mdc-elevation-overlay{position:absolute;border-radius:inherit;pointer-events:none;opacity:0;opacity:var(--mdc-elevation-overlay-opacity, 0);transition:opacity 280ms cubic-bezier(0.4, 0, 0.2, 1);background-color:#fff;background-color:var(--mdc-elevation-overlay-color, #fff)}.mdc-switch{align-items:center;background:none;border:none;cursor:pointer;display:inline-flex;flex-shrink:0;margin:0;outline:none;overflow:visible;padding:0;position:relative}.mdc-switch:disabled{cursor:default;pointer-events:none}.mdc-switch__track{overflow:hidden;position:relative;width:100%}.mdc-switch__track::before,.mdc-switch__track::after{border:1px solid transparent;border-radius:inherit;box-sizing:border-box;content:"";height:100%;left:0;position:absolute;width:100%}@media screen and (forced-colors: active){.mdc-switch__track::before,.mdc-switch__track::after{border-color:currentColor}}.mdc-switch__track::before{transition:transform 75ms 0ms cubic-bezier(0, 0, 0.2, 1);transform:translateX(0)}.mdc-switch__track::after{transition:transform 75ms 0ms cubic-bezier(0.4, 0, 0.6, 1);transform:translateX(-100%)}[dir=rtl] .mdc-switch__track::after,.mdc-switch__track[dir=rtl]::after{transform:translateX(100%)}.mdc-switch--selected .mdc-switch__track::before{transition:transform 75ms 0ms cubic-bezier(0.4, 0, 0.6, 1);transform:translateX(100%)}[dir=rtl] .mdc-switch--selected .mdc-switch__track::before,.mdc-switch--selected .mdc-switch__track[dir=rtl]::before{transform:translateX(-100%)}.mdc-switch--selected .mdc-switch__track::after{transition:transform 75ms 0ms cubic-bezier(0, 0, 0.2, 1);transform:translateX(0)}.mdc-switch__handle-track{height:100%;pointer-events:none;position:absolute;top:0;transition:transform 75ms 0ms cubic-bezier(0.4, 0, 0.2, 1);left:0;right:auto;transform:translateX(0)}[dir=rtl] .mdc-switch__handle-track,.mdc-switch__handle-track[dir=rtl]{left:auto;right:0}.mdc-switch--selected .mdc-switch__handle-track{transform:translateX(100%)}[dir=rtl] .mdc-switch--selected .mdc-switch__handle-track,.mdc-switch--selected .mdc-switch__handle-track[dir=rtl]{transform:translateX(-100%)}.mdc-switch__handle{display:flex;pointer-events:auto;position:absolute;top:50%;transform:translateY(-50%);left:0;right:auto}[dir=rtl] .mdc-switch__handle,.mdc-switch__handle[dir=rtl]{left:auto;right:0}.mdc-switch__handle::before,.mdc-switch__handle::after{border:1px solid transparent;border-radius:inherit;box-sizing:border-box;content:"";width:100%;height:100%;left:0;position:absolute;top:0;transition:background-color 75ms 0ms cubic-bezier(0.4, 0, 0.2, 1),border-color 75ms 0ms cubic-bezier(0.4, 0, 0.2, 1);z-index:-1}@media screen and (forced-colors: active){.mdc-switch__handle::before,.mdc-switch__handle::after{border-color:currentColor}}.mdc-switch__shadow{border-radius:inherit;bottom:0;left:0;position:absolute;right:0;top:0}.mdc-elevation-overlay{bottom:0;left:0;right:0;top:0}.mdc-switch__ripple{left:50%;position:absolute;top:50%;transform:translate(-50%, -50%);z-index:-1}.mdc-switch:disabled .mdc-switch__ripple{display:none}.mdc-switch__icons{height:100%;position:relative;width:100%;z-index:1}.mdc-switch__icon{bottom:0;left:0;margin:auto;position:absolute;right:0;top:0;opacity:0;transition:opacity 30ms 0ms cubic-bezier(0.4, 0, 1, 1)}.mdc-switch--selected .mdc-switch__icon--on,.mdc-switch--unselected .mdc-switch__icon--off{opacity:1;transition:opacity 45ms 30ms cubic-bezier(0, 0, 0.2, 1)}:host{display:inline-flex;outline:none}input{display:none}.mdc-switch{width:36px;width:var(--mdc-switch-track-width, 36px)}.mdc-switch.mdc-switch--selected:enabled .mdc-switch__handle::after{background:#6200ee;background:var(--mdc-switch-selected-handle-color, var(--mdc-theme-primary, #6200ee))}.mdc-switch.mdc-switch--selected:enabled:hover:not(:focus):not(:active) .mdc-switch__handle::after{background:#310077;background:var(--mdc-switch-selected-hover-handle-color, #310077)}.mdc-switch.mdc-switch--selected:enabled:focus:not(:active) .mdc-switch__handle::after{background:#310077;background:var(--mdc-switch-selected-focus-handle-color, #310077)}.mdc-switch.mdc-switch--selected:enabled:active .mdc-switch__handle::after{background:#310077;background:var(--mdc-switch-selected-pressed-handle-color, #310077)}.mdc-switch.mdc-switch--selected:disabled .mdc-switch__handle::after{background:#424242;background:var(--mdc-switch-disabled-selected-handle-color, #424242)}.mdc-switch.mdc-switch--unselected:enabled .mdc-switch__handle::after{background:#616161;background:var(--mdc-switch-unselected-handle-color, #616161)}.mdc-switch.mdc-switch--unselected:enabled:hover:not(:focus):not(:active) .mdc-switch__handle::after{background:#212121;background:var(--mdc-switch-unselected-hover-handle-color, #212121)}.mdc-switch.mdc-switch--unselected:enabled:focus:not(:active) .mdc-switch__handle::after{background:#212121;background:var(--mdc-switch-unselected-focus-handle-color, #212121)}.mdc-switch.mdc-switch--unselected:enabled:active .mdc-switch__handle::after{background:#212121;background:var(--mdc-switch-unselected-pressed-handle-color, #212121)}.mdc-switch.mdc-switch--unselected:disabled .mdc-switch__handle::after{background:#424242;background:var(--mdc-switch-disabled-unselected-handle-color, #424242)}.mdc-switch .mdc-switch__handle::before{background:#fff;background:var(--mdc-switch-handle-surface-color, var(--mdc-theme-surface, #fff))}.mdc-switch:enabled .mdc-switch__shadow{--mdc-elevation-box-shadow-for-gss:0px 2px 1px -1px rgba(0, 0, 0, 0.2), 0px 1px 1px 0px rgba(0, 0, 0, 0.14), 0px 1px 3px 0px rgba(0, 0, 0, 0.12);box-shadow:0px 2px 1px -1px rgba(0, 0, 0, 0.2), 0px 1px 1px 0px rgba(0, 0, 0, 0.14), 0px 1px 3px 0px rgba(0, 0, 0, 0.12);box-shadow:var(--mdc-switch-handle-elevation, var(--mdc-elevation-box-shadow-for-gss))}.mdc-switch:disabled .mdc-switch__shadow{--mdc-elevation-box-shadow-for-gss:0px 0px 0px 0px rgba(0, 0, 0, 0.2), 0px 0px 0px 0px rgba(0, 0, 0, 0.14), 0px 0px 0px 0px rgba(0, 0, 0, 0.12);box-shadow:0px 0px 0px 0px rgba(0, 0, 0, 0.2), 0px 0px 0px 0px rgba(0, 0, 0, 0.14), 0px 0px 0px 0px rgba(0, 0, 0, 0.12);box-shadow:var(--mdc-switch-disabled-handle-elevation, var(--mdc-elevation-box-shadow-for-gss))}.mdc-switch .mdc-switch__focus-ring-wrapper,.mdc-switch .mdc-switch__handle{height:20px;height:var(--mdc-switch-handle-height, 20px)}.mdc-switch:disabled .mdc-switch__handle::after{opacity:0.38;opacity:var(--mdc-switch-disabled-handle-opacity, 0.38)}.mdc-switch .mdc-switch__handle{border-radius:10px;border-radius:var(--mdc-switch-handle-shape, 10px)}.mdc-switch .mdc-switch__handle{width:20px;width:var(--mdc-switch-handle-width, 20px)}.mdc-switch .mdc-switch__handle-track{width:calc(100% - 20px);width:calc(100% - var(--mdc-switch-handle-width, 20px))}.mdc-switch.mdc-switch--selected:enabled .mdc-switch__icon{fill:#fff;fill:var(--mdc-switch-selected-icon-color, var(--mdc-theme-on-primary, #fff))}.mdc-switch.mdc-switch--selected:disabled .mdc-switch__icon{fill:#fff;fill:var(--mdc-switch-disabled-selected-icon-color, var(--mdc-theme-on-primary, #fff))}.mdc-switch.mdc-switch--unselected:enabled .mdc-switch__icon{fill:#fff;fill:var(--mdc-switch-unselected-icon-color, var(--mdc-theme-on-primary, #fff))}.mdc-switch.mdc-switch--unselected:disabled .mdc-switch__icon{fill:#fff;fill:var(--mdc-switch-disabled-unselected-icon-color, var(--mdc-theme-on-primary, #fff))}.mdc-switch.mdc-switch--selected:disabled .mdc-switch__icons{opacity:0.38;opacity:var(--mdc-switch-disabled-selected-icon-opacity, 0.38)}.mdc-switch.mdc-switch--unselected:disabled .mdc-switch__icons{opacity:0.38;opacity:var(--mdc-switch-disabled-unselected-icon-opacity, 0.38)}.mdc-switch.mdc-switch--selected .mdc-switch__icon{width:18px;width:var(--mdc-switch-selected-icon-size, 18px);height:18px;height:var(--mdc-switch-selected-icon-size, 18px)}.mdc-switch.mdc-switch--unselected .mdc-switch__icon{width:18px;width:var(--mdc-switch-unselected-icon-size, 18px);height:18px;height:var(--mdc-switch-unselected-icon-size, 18px)}.mdc-switch .mdc-switch__ripple{height:48px;height:var(--mdc-switch-state-layer-size, 48px);width:48px;width:var(--mdc-switch-state-layer-size, 48px)}.mdc-switch .mdc-switch__track{height:14px;height:var(--mdc-switch-track-height, 14px)}.mdc-switch:disabled .mdc-switch__track{opacity:0.12;opacity:var(--mdc-switch-disabled-track-opacity, 0.12)}.mdc-switch:enabled .mdc-switch__track::after{background:#d7bbff;background:var(--mdc-switch-selected-track-color, #d7bbff)}.mdc-switch:enabled:hover:not(:focus):not(:active) .mdc-switch__track::after{background:#d7bbff;background:var(--mdc-switch-selected-hover-track-color, #d7bbff)}.mdc-switch:enabled:focus:not(:active) .mdc-switch__track::after{background:#d7bbff;background:var(--mdc-switch-selected-focus-track-color, #d7bbff)}.mdc-switch:enabled:active .mdc-switch__track::after{background:#d7bbff;background:var(--mdc-switch-selected-pressed-track-color, #d7bbff)}.mdc-switch:disabled .mdc-switch__track::after{background:#424242;background:var(--mdc-switch-disabled-selected-track-color, #424242)}.mdc-switch:enabled .mdc-switch__track::before{background:#e0e0e0;background:var(--mdc-switch-unselected-track-color, #e0e0e0)}.mdc-switch:enabled:hover:not(:focus):not(:active) .mdc-switch__track::before{background:#e0e0e0;background:var(--mdc-switch-unselected-hover-track-color, #e0e0e0)}.mdc-switch:enabled:focus:not(:active) .mdc-switch__track::before{background:#e0e0e0;background:var(--mdc-switch-unselected-focus-track-color, #e0e0e0)}.mdc-switch:enabled:active .mdc-switch__track::before{background:#e0e0e0;background:var(--mdc-switch-unselected-pressed-track-color, #e0e0e0)}.mdc-switch:disabled .mdc-switch__track::before{background:#424242;background:var(--mdc-switch-disabled-unselected-track-color, #424242)}.mdc-switch .mdc-switch__track{border-radius:7px;border-radius:var(--mdc-switch-track-shape, 7px)}.mdc-switch.mdc-switch--selected{--mdc-ripple-focus-state-layer-color:var(--mdc-switch-selected-focus-state-layer-color, var(--mdc-theme-primary, #6200ee));--mdc-ripple-focus-state-layer-opacity:var(--mdc-switch-selected-focus-state-layer-opacity, 0.12);--mdc-ripple-hover-state-layer-color:var(--mdc-switch-selected-hover-state-layer-color, var(--mdc-theme-primary, #6200ee));--mdc-ripple-hover-state-layer-opacity:var(--mdc-switch-selected-hover-state-layer-opacity, 0.04);--mdc-ripple-pressed-state-layer-color:var(--mdc-switch-selected-pressed-state-layer-color, var(--mdc-theme-primary, #6200ee));--mdc-ripple-pressed-state-layer-opacity:var(--mdc-switch-selected-pressed-state-layer-opacity, 0.1)}.mdc-switch.mdc-switch--selected:enabled:focus:not(:active){--mdc-ripple-hover-state-layer-color:var(--mdc-switch-selected-focus-state-layer-color, var(--mdc-theme-primary, #6200ee))}.mdc-switch.mdc-switch--selected:enabled:active{--mdc-ripple-hover-state-layer-color:var(--mdc-switch-selected-pressed-state-layer-color, var(--mdc-theme-primary, #6200ee))}.mdc-switch.mdc-switch--unselected{--mdc-ripple-focus-state-layer-color:var(--mdc-switch-unselected-focus-state-layer-color, #424242);--mdc-ripple-focus-state-layer-opacity:var(--mdc-switch-unselected-focus-state-layer-opacity, 0.12);--mdc-ripple-hover-state-layer-color:var(--mdc-switch-unselected-hover-state-layer-color, #424242);--mdc-ripple-hover-state-layer-opacity:var(--mdc-switch-unselected-hover-state-layer-opacity, 0.04);--mdc-ripple-pressed-state-layer-color:var(--mdc-switch-unselected-pressed-state-layer-color, #424242);--mdc-ripple-pressed-state-layer-opacity:var(--mdc-switch-unselected-pressed-state-layer-opacity, 0.1)}.mdc-switch.mdc-switch--unselected:enabled:focus:not(:active){--mdc-ripple-hover-state-layer-color:var(--mdc-switch-unselected-focus-state-layer-color, #424242)}.mdc-switch.mdc-switch--unselected:enabled:active{--mdc-ripple-hover-state-layer-color:var(--mdc-switch-unselected-pressed-state-layer-color, #424242)}@media screen and (forced-colors: active),(-ms-high-contrast: active){.mdc-switch:disabled .mdc-switch__handle::after{opacity:1;opacity:var(--mdc-switch-disabled-handle-opacity, 1)}.mdc-switch.mdc-switch--selected:enabled .mdc-switch__icon{fill:ButtonText;fill:var(--mdc-switch-selected-icon-color, ButtonText)}.mdc-switch.mdc-switch--selected:disabled .mdc-switch__icon{fill:GrayText;fill:var(--mdc-switch-disabled-selected-icon-color, GrayText)}.mdc-switch.mdc-switch--unselected:enabled .mdc-switch__icon{fill:ButtonText;fill:var(--mdc-switch-unselected-icon-color, ButtonText)}.mdc-switch.mdc-switch--unselected:disabled .mdc-switch__icon{fill:GrayText;fill:var(--mdc-switch-disabled-unselected-icon-color, GrayText)}.mdc-switch.mdc-switch--selected:disabled .mdc-switch__icons{opacity:1;opacity:var(--mdc-switch-disabled-selected-icon-opacity, 1)}.mdc-switch.mdc-switch--unselected:disabled .mdc-switch__icons{opacity:1;opacity:var(--mdc-switch-disabled-unselected-icon-opacity, 1)}.mdc-switch:disabled .mdc-switch__track{opacity:1;opacity:var(--mdc-switch-disabled-track-opacity, 1)}}`
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */;let Pe=class extends $e{};Pe.styles=[Re],Pe=e([P("mwc-switch")],Pe);let je=class extends I{constructor(){super(),this.is_connected=!1,this.direction="horizontal",this.location="",this.aliases=Object(),this.aggregate_updating=!1,this.project_resource_monitor=!1,this.active=!1,this.resourceBroker=globalThis.resourceBroker,this.notification=globalThis.lablupNotification,this.init_resource()}static get is(){return"backend-ai-resource-monitor"}static get styles(){return[s,a,o,n,d,c`
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
      `]}init_resource(){this.total_slot={},this.total_resource_group_slot={},this.total_project_slot={},this.used_slot={},this.used_resource_group_slot={},this.used_project_slot={},this.available_slot={},this.used_slot_percent={},this.used_resource_group_slot_percent={},this.used_project_slot_percent={},this.concurrency_used=0,this.concurrency_max=0,this.concurrency_limit=0,this._status="inactive",this.scaling_groups=[{name:""}],this.scaling_group="",this.sessions_list=[],this.metric_updating=!1,this.metadata_updating=!1}firstUpdated(){new ResizeObserver((()=>{this._updateToggleResourceMonitorDisplay()})).observe(this.resourceGauge),document.addEventListener("backend-ai-group-changed",(e=>{this.scaling_group="",this._updatePageVariables(!0)})),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.is_connected=!0,setInterval((()=>{this._periodicUpdateResourcePolicy()}),2e4)}),{once:!0}):this.is_connected=!0,document.addEventListener("backend-ai-session-list-refreshed",(()=>{this._updatePageVariables(!0)}))}async _periodicUpdateResourcePolicy(){return this.active?(await this._refreshResourcePolicy(),this.aggregateResource("refresh-resource-policy"),Promise.resolve(!0)):Promise.resolve(!1)}async updateScalingGroup(e=!1,t){await this.resourceBroker.updateScalingGroup(e,t.target.value),this.active&&!0===e&&(await this._refreshResourcePolicy(),this.aggregateResource("update-scaling-group"))}async _viewStateChanged(e){await this.updateComplete,this.active&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.project_resource_monitor=this.resourceBroker.allow_project_resource_monitor,this._updatePageVariables(!0)}),{once:!0}):(this.project_resource_monitor=this.resourceBroker.allow_project_resource_monitor,await this._updatePageVariables(!0)))}async _updatePageVariables(e){return this.active&&!1===this.metadata_updating?(this.metadata_updating=!0,await this.resourceBroker._updatePageVariables(e),this.sessions_list=this.resourceBroker.sessions_list,await this._refreshResourcePolicy(),this.aggregateResource("update-page-variable"),this.metadata_updating=!1,Promise.resolve(!0)):Promise.resolve(!1)}_updateToggleResourceMonitorDisplay(){var e,t;const i=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#resource-legend"),r=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#resource-gauge-toggle-button");document.body.clientWidth>750&&"horizontal"==this.direction?(i.style.display="flex",i.style.marginTop="0",Array.from(this.resourceGauge.children).forEach((e=>{e.style.display="flex"}))):r.selected?(i.style.display="flex",i.style.marginTop="0",document.body.clientWidth<750&&(this.resourceGauge.style.left="20px",this.resourceGauge.style.right="20px"),Array.from(this.resourceGauge.children).forEach((e=>{e.style.display="flex"}))):(Array.from(this.resourceGauge.children).forEach((e=>{e.style.display="none"})),i.style.display="none")}async _refreshResourcePolicy(e=!1){return this.active?this.resourceBroker._refreshResourcePolicy().then((e=>(!1===e&&setTimeout((()=>{this._refreshResourcePolicy()}),2500),this.concurrency_used=this.resourceBroker.concurrency_used,this.concurrency_max=this.concurrency_used>this.resourceBroker.concurrency_max?this.concurrency_used:this.resourceBroker.concurrency_max,Promise.resolve(!0)))).catch((e=>(this.metadata_updating=!1,e&&e.message?(this.notification.text=D.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=D.relieve(e.title),this.notification.show(!0,e)),Promise.resolve(!1)))):Promise.resolve(!0)}_aliasName(e){const t=this.resourceBroker.imageTagAlias,i=this.resourceBroker.imageTagReplace;for(const[t,r]of Object.entries(i)){const i=new RegExp(t);if(i.test(e))return e.replace(i,r)}return e in t?t[e]:e}async _aggregateResourceUse(e=""){return this.resourceBroker._aggregateCurrentResource(e).then((t=>!1===t?setTimeout((()=>{this._aggregateResourceUse(e)}),1e3):(this.concurrency_used=this.resourceBroker.concurrency_used,this.scaling_group=this.resourceBroker.scaling_group,this.scaling_groups=this.resourceBroker.scaling_groups,this.total_slot=this.resourceBroker.total_slot,this.total_resource_group_slot=this.resourceBroker.total_resource_group_slot,this.total_project_slot=this.resourceBroker.total_project_slot,this.used_slot=this.resourceBroker.used_slot,this.used_resource_group_slot=this.resourceBroker.used_resource_group_slot,this.used_project_slot=this.resourceBroker.used_project_slot,this.used_project_slot_percent=this.resourceBroker.used_project_slot_percent,this.concurrency_limit=this.resourceBroker.concurrency_limit,this.available_slot=this.resourceBroker.available_slot,this.used_slot_percent=this.resourceBroker.used_slot_percent,this.used_resource_group_slot_percent=this.resourceBroker.used_resource_group_slot_percent,Promise.resolve(!0)))).then((()=>Promise.resolve(!0))).catch((e=>(e&&e.message&&(console.log(e),this.notification.text=D.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)),Promise.resolve(!1))))}aggregateResource(e=""){void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._aggregateResourceUse(e)}),!0):this._aggregateResourceUse(e)}_numberWithPostfix(e,t=""){return isNaN(parseInt(e))?"":parseInt(e)+t}_prefixFormatWithoutTrailingZeros(e="0",t){const i="string"==typeof e?parseFloat(e):e;return parseFloat(i.toFixed(t)).toString()}_prefixFormat(e="0",t){var i;return"string"==typeof e?null===(i=parseFloat(e))||void 0===i?void 0:i.toFixed(t):null==e?void 0:e.toFixed(t)}render(){return l`
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
            ${this.total_slot.cuda_device?l`
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
                `:l``}
            ${this.resourceBroker.total_slot.cuda_shares&&this.resourceBroker.total_slot.cuda_shares>0?l`
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
                `:l``}
            ${this.total_slot.rocm_device?l`
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
                `:l``}
            ${this.total_slot.tpu_device?l`
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
                `:l``}
            ${this.total_slot.ipu_device?l`
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
                `:l``}
            ${this.total_slot.atom_device?l`
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
                `:l``}
            ${this.total_slot.atom_plus_device?l`
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
                `:l``}
            ${this.total_slot.gaudi2_device?l`
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
                `:l``}
            ${this.total_slot.warboy_device?l`
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
                `:l``}
            ${this.total_slot.rngd_device?l`
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
                `:l``}
            ${this.total_slot.hyperaccel_lpu_device?l`
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
                `:l``}
            <div class="layout horizontal center-justified monitor">
              <div
                class="layout vertical center center-justified resource-name"
              >
                <span class="gauge-name">
                  ${B("session.launcher.Sessions")}
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
              ${B("session.launcher.ResourceMonitorToggle")}
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
            ${B("session.launcher.CurrentResourceGroup")}
            (${this.scaling_group})
          </span>
        </div>
        <div
          class="layout horizontal center ${"vertical"===this.direction?"start-justified":"end-justified"}"
        >
          <div class="resource-legend-icon end"></div>
          <span class="resource-legend">
            ${B("session.launcher.UserResourceLimit")}
          </span>
        </div>
      </div>
      ${"vertical"===this.direction&&!0===this.project_resource_monitor&&(this.total_project_slot.cpu>0||this.total_project_slot.cpu===1/0)?l`
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
                    ${B("session.launcher.Project")}
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
                  ${this.total_project_slot.cuda_device?l`
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
                      `:l``}
                  ${this.total_project_slot.cuda_shares?l`
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
                      `:l``}
                  ${this.total_project_slot.rocm_device?l`
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
                      `:l``}
                  ${this.total_project_slot.tpu_device?l`
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
                      `:l``}
                  ${this.total_project_slot.ipu_device?l`
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
                      `:l``}
                  ${this.total_project_slot.atom_device?l`
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
                      `:l``}
                  ${this.total_project_slot.warboy_device?l`
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
                      `:l``}
                  ${this.total_project_slot.rngd_device?l`
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
                      `:l``}
                  ${this.total_project_slot.hyperaccel_lpu_device?l`
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
                      `:l``}
                </div>
                <div class="flex"></div>
              </div>
            </div>
          `:l``}
    `}};e([t({type:Boolean})],je.prototype,"is_connected",void 0),e([t({type:String})],je.prototype,"direction",void 0),e([t({type:String})],je.prototype,"location",void 0),e([t({type:Object})],je.prototype,"aliases",void 0),e([t({type:Object})],je.prototype,"total_slot",void 0),e([t({type:Object})],je.prototype,"total_resource_group_slot",void 0),e([t({type:Object})],je.prototype,"total_project_slot",void 0),e([t({type:Object})],je.prototype,"used_slot",void 0),e([t({type:Object})],je.prototype,"used_resource_group_slot",void 0),e([t({type:Object})],je.prototype,"used_project_slot",void 0),e([t({type:Object})],je.prototype,"available_slot",void 0),e([t({type:Number})],je.prototype,"concurrency_used",void 0),e([t({type:Number})],je.prototype,"concurrency_max",void 0),e([t({type:Number})],je.prototype,"concurrency_limit",void 0),e([t({type:Object})],je.prototype,"used_slot_percent",void 0),e([t({type:Object})],je.prototype,"used_resource_group_slot_percent",void 0),e([t({type:Object})],je.prototype,"used_project_slot_percent",void 0),e([t({type:String})],je.prototype,"default_language",void 0),e([t({type:Boolean})],je.prototype,"_status",void 0),e([t({type:Number})],je.prototype,"num_sessions",void 0),e([t({type:String})],je.prototype,"scaling_group",void 0),e([t({type:Array})],je.prototype,"scaling_groups",void 0),e([t({type:Array})],je.prototype,"sessions_list",void 0),e([t({type:Boolean})],je.prototype,"metric_updating",void 0),e([t({type:Boolean})],je.prototype,"metadata_updating",void 0),e([t({type:Boolean})],je.prototype,"aggregate_updating",void 0),e([t({type:Object})],je.prototype,"scaling_group_selection_box",void 0),e([t({type:Boolean})],je.prototype,"project_resource_monitor",void 0),e([t({type:Object})],je.prototype,"resourceBroker",void 0),e([j("#resource-gauges")],je.prototype,"resourceGauge",void 0),je=e([i("backend-ai-resource-monitor")],je);let Fe=class extends r{constructor(){super(...arguments),this.title="",this.message="",this.panelId="",this.horizontalsize="",this.headerColor="",this.elevation=1,this.autowidth=!1,this.width=350,this.widthpct=0,this.height=0,this.marginWidth=14,this.minwidth=0,this.maxwidth=0,this.pinned=!1,this.disabled=!1,this.narrow=!1,this.noheader=!1,this.scrollableY=!1}static get styles(){return[a,o,c`
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
      `]}render(){return l`
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
    `}firstUpdated(){var e,t,i,r,s,a,o;if(this.pinned||null==this.panelId){const r=null===(e=this.shadowRoot)||void 0===e?void 0:e.getElementById("button");null===(i=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("h4"))||void 0===i||i.removeChild(r)}const n=null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector(".card"),d=null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector(".content"),c=null===(a=this.shadowRoot)||void 0===a?void 0:a.querySelector("#header");this.autowidth?n.style.width="auto":n.style.width=0!==this.widthpct?this.widthpct+"%":this.width+"px",this.minwidth&&(n.style.minWidth=this.minwidth+"px"),this.maxwidth&&(n.style.minWidth=this.maxwidth+"px"),"2x"===this.horizontalsize?n.style.width=2*this.width+28+"px":"3x"===this.horizontalsize?n.style.width=3*this.width+56+"px":"4x"==this.horizontalsize&&(n.style.width=4*this.width+84+"px"),n.style.margin=this.marginWidth+"px",""!==this.headerColor&&(c.style.backgroundColor=this.headerColor),this.narrow&&((null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("div.card > div")).style.margin="0",c.style.marginBottom="0"),this.height>0&&(130==this.height?n.style.height="fit-content":(d.style.height=this.height-70+"px",n.style.height=this.height+"px")),this.noheader&&(c.style.display="none"),this.scrollableY&&(d.style.overflowY="auto",d.style.overflowX="hidden")}_removePanel(){}};e([t({type:String})],Fe.prototype,"title",void 0),e([t({type:String})],Fe.prototype,"message",void 0),e([t({type:String})],Fe.prototype,"panelId",void 0),e([t({type:String})],Fe.prototype,"horizontalsize",void 0),e([t({type:String})],Fe.prototype,"headerColor",void 0),e([t({type:Number})],Fe.prototype,"elevation",void 0),e([t({type:Boolean})],Fe.prototype,"autowidth",void 0),e([t({type:Number})],Fe.prototype,"width",void 0),e([t({type:Number})],Fe.prototype,"widthpct",void 0),e([t({type:Number})],Fe.prototype,"height",void 0),e([t({type:Number})],Fe.prototype,"marginWidth",void 0),e([t({type:Number})],Fe.prototype,"minwidth",void 0),e([t({type:Number})],Fe.prototype,"maxwidth",void 0),e([t({type:Boolean})],Fe.prototype,"pinned",void 0),e([t({type:Boolean})],Fe.prototype,"disabled",void 0),e([t({type:Boolean})],Fe.prototype,"narrow",void 0),e([t({type:Boolean})],Fe.prototype,"noheader",void 0),e([t({type:Boolean})],Fe.prototype,"scrollableY",void 0),Fe=e([i("lablup-activity-panel")],Fe);
