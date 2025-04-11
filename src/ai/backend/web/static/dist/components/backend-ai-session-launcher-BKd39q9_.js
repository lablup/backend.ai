import{Y as e,F as t,H as i,ae as r,M as o,_ as s,L as n,a1 as a,J as l,a0 as c,af as d,V as u,a3 as h,W as p,X as m,ag as f,ah as g,ai as v,aj as b,Z as _,n as y,e as x,t as w,h as k,b as S,I as T,a as C,a6 as M,c as P,i as $,k as L,B as E,d as R,f as A,r as N,ak as I,al as D,am as O,an as F,ao as z,q as W,z as B,p as j,T as H,E as U,P as V,C as G,ap as q,aq as Z,ar as K,G as X,g as Y,s as J,l as Q,Q as ee,A as te}from"./backend-ai-webui-CuYxUCgf.js";import"./lablup-progress-bar-C_dQSfpj.js";import"./mwc-check-list-item-B3NHddRA.js";
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-LIcense-Identifier: Apache-2.0
 */const ie=e`.mdc-slider{cursor:pointer;height:48px;margin:0 24px;position:relative;touch-action:pan-y}.mdc-slider .mdc-slider__track{height:4px;position:absolute;top:50%;transform:translateY(-50%);width:100%}.mdc-slider .mdc-slider__track--active,.mdc-slider .mdc-slider__track--inactive{display:flex;height:100%;position:absolute;width:100%}.mdc-slider .mdc-slider__track--active{border-radius:3px;height:6px;overflow:hidden;top:-1px}.mdc-slider .mdc-slider__track--active_fill{border-top:6px solid;box-sizing:border-box;height:100%;width:100%;position:relative;-webkit-transform-origin:left;transform-origin:left}[dir=rtl] .mdc-slider .mdc-slider__track--active_fill,.mdc-slider .mdc-slider__track--active_fill[dir=rtl]{-webkit-transform-origin:right;transform-origin:right}.mdc-slider .mdc-slider__track--inactive{border-radius:2px;height:4px;left:0;top:0}.mdc-slider .mdc-slider__track--inactive::before{position:absolute;box-sizing:border-box;width:100%;height:100%;top:0;left:0;border:1px solid transparent;border-radius:inherit;content:"";pointer-events:none}@media screen and (forced-colors: active){.mdc-slider .mdc-slider__track--inactive::before{border-color:CanvasText}}.mdc-slider .mdc-slider__track--active_fill{border-color:#6200ee;border-color:var(--mdc-theme-primary, #6200ee)}.mdc-slider.mdc-slider--disabled .mdc-slider__track--active_fill{border-color:#000;border-color:var(--mdc-theme-on-surface, #000)}.mdc-slider .mdc-slider__track--inactive{background-color:#6200ee;background-color:var(--mdc-theme-primary, #6200ee);opacity:.24}.mdc-slider.mdc-slider--disabled .mdc-slider__track--inactive{background-color:#000;background-color:var(--mdc-theme-on-surface, #000);opacity:.24}.mdc-slider .mdc-slider__value-indicator-container{bottom:44px;left:50%;left:var(--slider-value-indicator-container-left, 50%);pointer-events:none;position:absolute;right:var(--slider-value-indicator-container-right);transform:translateX(-50%);transform:var(--slider-value-indicator-container-transform, translateX(-50%))}.mdc-slider .mdc-slider__value-indicator{transition:transform 100ms 0ms cubic-bezier(0.4, 0, 1, 1);align-items:center;border-radius:4px;display:flex;height:32px;padding:0 12px;transform:scale(0);transform-origin:bottom}.mdc-slider .mdc-slider__value-indicator::before{border-left:6px solid transparent;border-right:6px solid transparent;border-top:6px solid;bottom:-5px;content:"";height:0;left:50%;left:var(--slider-value-indicator-caret-left, 50%);position:absolute;right:var(--slider-value-indicator-caret-right);transform:translateX(-50%);transform:var(--slider-value-indicator-caret-transform, translateX(-50%));width:0}.mdc-slider .mdc-slider__value-indicator::after{position:absolute;box-sizing:border-box;width:100%;height:100%;top:0;left:0;border:1px solid transparent;border-radius:inherit;content:"";pointer-events:none}@media screen and (forced-colors: active){.mdc-slider .mdc-slider__value-indicator::after{border-color:CanvasText}}.mdc-slider .mdc-slider__thumb--with-indicator .mdc-slider__value-indicator-container{pointer-events:auto}.mdc-slider .mdc-slider__thumb--with-indicator .mdc-slider__value-indicator{transition:transform 100ms 0ms cubic-bezier(0, 0, 0.2, 1);transform:scale(1)}@media(prefers-reduced-motion){.mdc-slider .mdc-slider__value-indicator,.mdc-slider .mdc-slider__thumb--with-indicator .mdc-slider__value-indicator{transition:none}}.mdc-slider .mdc-slider__value-indicator-text{-moz-osx-font-smoothing:grayscale;-webkit-font-smoothing:antialiased;font-family:Roboto, sans-serif;font-family:var(--mdc-typography-subtitle2-font-family, var(--mdc-typography-font-family, Roboto, sans-serif));font-size:0.875rem;font-size:var(--mdc-typography-subtitle2-font-size, 0.875rem);line-height:1.375rem;line-height:var(--mdc-typography-subtitle2-line-height, 1.375rem);font-weight:500;font-weight:var(--mdc-typography-subtitle2-font-weight, 500);letter-spacing:0.0071428571em;letter-spacing:var(--mdc-typography-subtitle2-letter-spacing, 0.0071428571em);text-decoration:inherit;text-decoration:var(--mdc-typography-subtitle2-text-decoration, inherit);text-transform:inherit;text-transform:var(--mdc-typography-subtitle2-text-transform, inherit)}.mdc-slider .mdc-slider__value-indicator{background-color:#000;opacity:.6}.mdc-slider .mdc-slider__value-indicator::before{border-top-color:#000}.mdc-slider .mdc-slider__value-indicator{color:#fff;color:var(--mdc-theme-on-primary, #fff)}.mdc-slider .mdc-slider__thumb{display:flex;height:48px;left:-24px;outline:none;position:absolute;user-select:none;width:48px}.mdc-slider .mdc-slider__thumb--top{z-index:1}.mdc-slider .mdc-slider__thumb--top .mdc-slider__thumb-knob,.mdc-slider .mdc-slider__thumb--top.mdc-slider__thumb:hover .mdc-slider__thumb-knob,.mdc-slider .mdc-slider__thumb--top.mdc-slider__thumb--focused .mdc-slider__thumb-knob{border-style:solid;border-width:1px;box-sizing:content-box}.mdc-slider .mdc-slider__thumb-knob{box-shadow:0px 2px 1px -1px rgba(0, 0, 0, 0.2),0px 1px 1px 0px rgba(0, 0, 0, 0.14),0px 1px 3px 0px rgba(0,0,0,.12);border:10px solid;border-radius:50%;box-sizing:border-box;height:20px;left:50%;position:absolute;top:50%;transform:translate(-50%, -50%);width:20px}.mdc-slider .mdc-slider__thumb-knob{background-color:#6200ee;background-color:var(--mdc-theme-primary, #6200ee);border-color:#6200ee;border-color:var(--mdc-theme-primary, #6200ee)}.mdc-slider .mdc-slider__thumb--top .mdc-slider__thumb-knob,.mdc-slider .mdc-slider__thumb--top.mdc-slider__thumb:hover .mdc-slider__thumb-knob,.mdc-slider .mdc-slider__thumb--top.mdc-slider__thumb--focused .mdc-slider__thumb-knob{border-color:#fff}.mdc-slider.mdc-slider--disabled .mdc-slider__thumb-knob{background-color:#000;background-color:var(--mdc-theme-on-surface, #000);border-color:#000;border-color:var(--mdc-theme-on-surface, #000)}.mdc-slider.mdc-slider--disabled .mdc-slider__thumb--top .mdc-slider__thumb-knob,.mdc-slider.mdc-slider--disabled .mdc-slider__thumb--top.mdc-slider__thumb:hover .mdc-slider__thumb-knob,.mdc-slider.mdc-slider--disabled .mdc-slider__thumb--top.mdc-slider__thumb--focused .mdc-slider__thumb-knob{border-color:#fff}.mdc-slider .mdc-slider__thumb::before,.mdc-slider .mdc-slider__thumb::after{background-color:#6200ee;background-color:var(--mdc-ripple-color, var(--mdc-theme-primary, #6200ee))}.mdc-slider .mdc-slider__thumb:hover::before,.mdc-slider .mdc-slider__thumb.mdc-ripple-surface--hover::before{opacity:0.04;opacity:var(--mdc-ripple-hover-opacity, 0.04)}.mdc-slider .mdc-slider__thumb.mdc-ripple-upgraded--background-focused::before,.mdc-slider .mdc-slider__thumb:not(.mdc-ripple-upgraded):focus::before{transition-duration:75ms;opacity:0.12;opacity:var(--mdc-ripple-focus-opacity, 0.12)}.mdc-slider .mdc-slider__thumb:not(.mdc-ripple-upgraded)::after{transition:opacity 150ms linear}.mdc-slider .mdc-slider__thumb:not(.mdc-ripple-upgraded):active::after{transition-duration:75ms;opacity:0.12;opacity:var(--mdc-ripple-press-opacity, 0.12)}.mdc-slider .mdc-slider__thumb.mdc-ripple-upgraded{--mdc-ripple-fg-opacity:var(--mdc-ripple-press-opacity, 0.12)}.mdc-slider .mdc-slider__tick-marks{align-items:center;box-sizing:border-box;display:flex;height:100%;justify-content:space-between;padding:0 1px;position:absolute;width:100%}.mdc-slider .mdc-slider__tick-mark--active,.mdc-slider .mdc-slider__tick-mark--inactive{border-radius:50%;height:2px;width:2px}.mdc-slider .mdc-slider__tick-mark--active{background-color:#fff;background-color:var(--mdc-theme-on-primary, #fff);opacity:.6}.mdc-slider.mdc-slider--disabled .mdc-slider__tick-mark--active{background-color:#fff;background-color:var(--mdc-theme-on-primary, #fff);opacity:.6}.mdc-slider .mdc-slider__tick-mark--inactive{background-color:#6200ee;background-color:var(--mdc-theme-primary, #6200ee);opacity:.6}.mdc-slider.mdc-slider--disabled .mdc-slider__tick-mark--inactive{background-color:#000;background-color:var(--mdc-theme-on-surface, #000);opacity:.6}.mdc-slider--discrete .mdc-slider__thumb,.mdc-slider--discrete .mdc-slider__track--active_fill{transition:transform 80ms ease}@media(prefers-reduced-motion){.mdc-slider--discrete .mdc-slider__thumb,.mdc-slider--discrete .mdc-slider__track--active_fill{transition:none}}.mdc-slider--disabled{opacity:.38;cursor:auto}.mdc-slider--disabled .mdc-slider__thumb{pointer-events:none}.mdc-slider__input{cursor:pointer;left:0;margin:0;height:100%;opacity:0;pointer-events:none;position:absolute;top:0;width:100%}:host{outline:none;display:block;-webkit-tap-highlight-color:transparent}.ripple{--mdc-ripple-color:#6200ee;--mdc-ripple-color:var(--mdc-theme-primary, #6200ee)}`
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
 */;var re,oe;!function(e){e[e.ACTIVE=0]="ACTIVE",e[e.INACTIVE=1]="INACTIVE"}(re||(re={})),function(e){e[e.START=1]="START",e[e.END=2]="END"}(oe||(oe={}));
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
var se={animation:{prefixed:"-webkit-animation",standard:"animation"},transform:{prefixed:"-webkit-transform",standard:"transform"},transition:{prefixed:"-webkit-transition",standard:"transition"}};function ne(e,t){if(function(e){return Boolean(e.document)&&"function"==typeof e.document.createElement}(e)&&t in se){var i=e.document.createElement("div"),r=se[t],o=r.standard,s=r.prefixed;return o in i.style?o:s}return t}
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
 */var ae,le="mdc-slider--disabled",ce="mdc-slider--discrete",de="mdc-slider--range",ue="mdc-slider__thumb--focused",he="mdc-slider__thumb--top",pe="mdc-slider__thumb--with-indicator",me="mdc-slider--tick-marks",fe=1,ge=0,ve=5,be="aria-valuetext",_e="disabled",ye="min",xe="max",we="value",ke="step",Se="data-min-range",Te="--slider-value-indicator-caret-left",Ce="--slider-value-indicator-caret-right",Me="--slider-value-indicator-caret-transform",Pe="--slider-value-indicator-container-left",$e="--slider-value-indicator-container-right",Le="--slider-value-indicator-container-transform";!function(e){e.SLIDER_UPDATE="slider_update"}(ae||(ae={}));var Ee="undefined"!=typeof window,Re=function(e){function o(t){var s=e.call(this,i(i({},o.defaultAdapter),t))||this;return s.initialStylesRemoved=!1,s.isDisabled=!1,s.isDiscrete=!1,s.step=fe,s.minRange=ge,s.hasTickMarks=!1,s.isRange=!1,s.thumb=null,s.downEventClientX=null,s.startThumbKnobWidth=0,s.endThumbKnobWidth=0,s.animFrame=new r,s}return t(o,e),Object.defineProperty(o,"defaultAdapter",{get:function(){return{hasClass:function(){return!1},addClass:function(){},removeClass:function(){},addThumbClass:function(){},removeThumbClass:function(){},getAttribute:function(){return null},getInputValue:function(){return""},setInputValue:function(){},getInputAttribute:function(){return null},setInputAttribute:function(){return null},removeInputAttribute:function(){return null},focusInput:function(){},isInputFocused:function(){return!1},shouldHideFocusStylesForPointerEvents:function(){return!1},getThumbKnobWidth:function(){return 0},getValueIndicatorContainerWidth:function(){return 0},getThumbBoundingClientRect:function(){return{top:0,right:0,bottom:0,left:0,width:0,height:0}},getBoundingClientRect:function(){return{top:0,right:0,bottom:0,left:0,width:0,height:0}},isRTL:function(){return!1},setThumbStyleProperty:function(){},removeThumbStyleProperty:function(){},setTrackActiveStyleProperty:function(){},removeTrackActiveStyleProperty:function(){},setValueIndicatorText:function(){},getValueToAriaValueTextFn:function(){return null},updateTickMarks:function(){},setPointerCapture:function(){},emitChangeEvent:function(){},emitInputEvent:function(){},emitDragStartEvent:function(){},emitDragEndEvent:function(){},registerEventHandler:function(){},deregisterEventHandler:function(){},registerThumbEventHandler:function(){},deregisterThumbEventHandler:function(){},registerInputEventHandler:function(){},deregisterInputEventHandler:function(){},registerBodyEventHandler:function(){},deregisterBodyEventHandler:function(){},registerWindowEventHandler:function(){},deregisterWindowEventHandler:function(){}}},enumerable:!1,configurable:!0}),o.prototype.init=function(){var e=this;this.isDisabled=this.adapter.hasClass(le),this.isDiscrete=this.adapter.hasClass(ce),this.hasTickMarks=this.adapter.hasClass(me),this.isRange=this.adapter.hasClass(de);var t=this.convertAttributeValueToNumber(this.adapter.getInputAttribute(ye,this.isRange?oe.START:oe.END),ye),i=this.convertAttributeValueToNumber(this.adapter.getInputAttribute(xe,oe.END),xe),r=this.convertAttributeValueToNumber(this.adapter.getInputAttribute(we,oe.END),we),o=this.isRange?this.convertAttributeValueToNumber(this.adapter.getInputAttribute(we,oe.START),we):t,s=this.adapter.getInputAttribute(ke,oe.END),n=s?this.convertAttributeValueToNumber(s,ke):this.step,a=this.adapter.getAttribute(Se),l=a?this.convertAttributeValueToNumber(a,Se):this.minRange;this.validateProperties({min:t,max:i,value:r,valueStart:o,step:n,minRange:l}),this.min=t,this.max=i,this.value=r,this.valueStart=o,this.step=n,this.minRange=l,this.numDecimalPlaces=Ae(this.step),this.valueBeforeDownEvent=r,this.valueStartBeforeDownEvent=o,this.mousedownOrTouchstartListener=this.handleMousedownOrTouchstart.bind(this),this.moveListener=this.handleMove.bind(this),this.pointerdownListener=this.handlePointerdown.bind(this),this.pointerupListener=this.handlePointerup.bind(this),this.thumbMouseenterListener=this.handleThumbMouseenter.bind(this),this.thumbMouseleaveListener=this.handleThumbMouseleave.bind(this),this.inputStartChangeListener=function(){e.handleInputChange(oe.START)},this.inputEndChangeListener=function(){e.handleInputChange(oe.END)},this.inputStartFocusListener=function(){e.handleInputFocus(oe.START)},this.inputEndFocusListener=function(){e.handleInputFocus(oe.END)},this.inputStartBlurListener=function(){e.handleInputBlur(oe.START)},this.inputEndBlurListener=function(){e.handleInputBlur(oe.END)},this.resizeListener=this.handleResize.bind(this),this.registerEventHandlers()},o.prototype.destroy=function(){this.deregisterEventHandlers()},o.prototype.setMin=function(e){this.min=e,this.isRange||(this.valueStart=e),this.updateUI()},o.prototype.setMax=function(e){this.max=e,this.updateUI()},o.prototype.getMin=function(){return this.min},o.prototype.getMax=function(){return this.max},o.prototype.getValue=function(){return this.value},o.prototype.setValue=function(e){if(this.isRange&&e<this.valueStart+this.minRange)throw new Error("end thumb value ("+e+") must be >= start thumb value ("+this.valueStart+") + min range ("+this.minRange+")");this.updateValue(e,oe.END)},o.prototype.getValueStart=function(){if(!this.isRange)throw new Error("`valueStart` is only applicable for range sliders.");return this.valueStart},o.prototype.setValueStart=function(e){if(!this.isRange)throw new Error("`valueStart` is only applicable for range sliders.");if(this.isRange&&e>this.value-this.minRange)throw new Error("start thumb value ("+e+") must be <= end thumb value ("+this.value+") - min range ("+this.minRange+")");this.updateValue(e,oe.START)},o.prototype.setStep=function(e){this.step=e,this.numDecimalPlaces=Ae(e),this.updateUI()},o.prototype.setMinRange=function(e){if(!this.isRange)throw new Error("`minRange` is only applicable for range sliders.");if(e<0)throw new Error("`minRange` must be non-negative. Current value: "+e);if(this.value-this.valueStart<e)throw new Error("start thumb value ("+this.valueStart+") and end thumb value ("+this.value+") must differ by at least "+e+".");this.minRange=e},o.prototype.setIsDiscrete=function(e){this.isDiscrete=e,this.updateValueIndicatorUI(),this.updateTickMarksUI()},o.prototype.getStep=function(){return this.step},o.prototype.getMinRange=function(){if(!this.isRange)throw new Error("`minRange` is only applicable for range sliders.");return this.minRange},o.prototype.setHasTickMarks=function(e){this.hasTickMarks=e,this.updateTickMarksUI()},o.prototype.getDisabled=function(){return this.isDisabled},o.prototype.setDisabled=function(e){this.isDisabled=e,e?(this.adapter.addClass(le),this.isRange&&this.adapter.setInputAttribute(_e,"",oe.START),this.adapter.setInputAttribute(_e,"",oe.END)):(this.adapter.removeClass(le),this.isRange&&this.adapter.removeInputAttribute(_e,oe.START),this.adapter.removeInputAttribute(_e,oe.END))},o.prototype.getIsRange=function(){return this.isRange},o.prototype.layout=function(e){var t=(void 0===e?{}:e).skipUpdateUI;this.rect=this.adapter.getBoundingClientRect(),this.isRange&&(this.startThumbKnobWidth=this.adapter.getThumbKnobWidth(oe.START),this.endThumbKnobWidth=this.adapter.getThumbKnobWidth(oe.END)),t||this.updateUI()},o.prototype.handleResize=function(){this.layout()},o.prototype.handleDown=function(e){if(!this.isDisabled){this.valueStartBeforeDownEvent=this.valueStart,this.valueBeforeDownEvent=this.value;var t=null!=e.clientX?e.clientX:e.targetTouches[0].clientX;this.downEventClientX=t;var i=this.mapClientXOnSliderScale(t);this.thumb=this.getThumbFromDownEvent(t,i),null!==this.thumb&&(this.handleDragStart(e,i,this.thumb),this.updateValue(i,this.thumb,{emitInputEvent:!0}))}},o.prototype.handleMove=function(e){if(!this.isDisabled){e.preventDefault();var t=null!=e.clientX?e.clientX:e.targetTouches[0].clientX,i=null!=this.thumb;if(this.thumb=this.getThumbFromMoveEvent(t),null!==this.thumb){var r=this.mapClientXOnSliderScale(t);i||(this.handleDragStart(e,r,this.thumb),this.adapter.emitDragStartEvent(r,this.thumb)),this.updateValue(r,this.thumb,{emitInputEvent:!0})}}},o.prototype.handleUp=function(){var e,t;if(!this.isDisabled&&null!==this.thumb){(null===(t=(e=this.adapter).shouldHideFocusStylesForPointerEvents)||void 0===t?void 0:t.call(e))&&this.handleInputBlur(this.thumb);var i=this.thumb===oe.START?this.valueStartBeforeDownEvent:this.valueBeforeDownEvent,r=this.thumb===oe.START?this.valueStart:this.value;i!==r&&this.adapter.emitChangeEvent(r,this.thumb),this.adapter.emitDragEndEvent(r,this.thumb),this.thumb=null}},o.prototype.handleThumbMouseenter=function(){this.isDiscrete&&this.isRange&&(this.adapter.addThumbClass(pe,oe.START),this.adapter.addThumbClass(pe,oe.END))},o.prototype.handleThumbMouseleave=function(){var e,t;this.isDiscrete&&this.isRange&&(!(null===(t=(e=this.adapter).shouldHideFocusStylesForPointerEvents)||void 0===t?void 0:t.call(e))&&(this.adapter.isInputFocused(oe.START)||this.adapter.isInputFocused(oe.END))||this.thumb||(this.adapter.removeThumbClass(pe,oe.START),this.adapter.removeThumbClass(pe,oe.END)))},o.prototype.handleMousedownOrTouchstart=function(e){var t=this,i="mousedown"===e.type?"mousemove":"touchmove";this.adapter.registerBodyEventHandler(i,this.moveListener);var r=function(){t.handleUp(),t.adapter.deregisterBodyEventHandler(i,t.moveListener),t.adapter.deregisterEventHandler("mouseup",r),t.adapter.deregisterEventHandler("touchend",r)};this.adapter.registerBodyEventHandler("mouseup",r),this.adapter.registerBodyEventHandler("touchend",r),this.handleDown(e)},o.prototype.handlePointerdown=function(e){0===e.button&&(null!=e.pointerId&&this.adapter.setPointerCapture(e.pointerId),this.adapter.registerEventHandler("pointermove",this.moveListener),this.handleDown(e))},o.prototype.handleInputChange=function(e){var t=Number(this.adapter.getInputValue(e));e===oe.START?this.setValueStart(t):this.setValue(t),this.adapter.emitChangeEvent(e===oe.START?this.valueStart:this.value,e),this.adapter.emitInputEvent(e===oe.START?this.valueStart:this.value,e)},o.prototype.handleInputFocus=function(e){if(this.adapter.addThumbClass(ue,e),this.isDiscrete&&(this.adapter.addThumbClass(pe,e),this.isRange)){var t=e===oe.START?oe.END:oe.START;this.adapter.addThumbClass(pe,t)}},o.prototype.handleInputBlur=function(e){if(this.adapter.removeThumbClass(ue,e),this.isDiscrete&&(this.adapter.removeThumbClass(pe,e),this.isRange)){var t=e===oe.START?oe.END:oe.START;this.adapter.removeThumbClass(pe,t)}},o.prototype.handleDragStart=function(e,t,i){var r,o;this.adapter.emitDragStartEvent(t,i),this.adapter.focusInput(i),(null===(o=(r=this.adapter).shouldHideFocusStylesForPointerEvents)||void 0===o?void 0:o.call(r))&&this.handleInputFocus(i),e.preventDefault()},o.prototype.getThumbFromDownEvent=function(e,t){if(!this.isRange)return oe.END;var i=this.adapter.getThumbBoundingClientRect(oe.START),r=this.adapter.getThumbBoundingClientRect(oe.END),o=e>=i.left&&e<=i.right,s=e>=r.left&&e<=r.right;return o&&s?null:o?oe.START:s?oe.END:t<this.valueStart?oe.START:t>this.value?oe.END:t-this.valueStart<=this.value-t?oe.START:oe.END},o.prototype.getThumbFromMoveEvent=function(e){if(null!==this.thumb)return this.thumb;if(null===this.downEventClientX)throw new Error("`downEventClientX` is null after move event.");return Math.abs(this.downEventClientX-e)<ve?this.thumb:e<this.downEventClientX?this.adapter.isRTL()?oe.END:oe.START:this.adapter.isRTL()?oe.START:oe.END},o.prototype.updateUI=function(e){e?this.updateThumbAndInputAttributes(e):(this.updateThumbAndInputAttributes(oe.START),this.updateThumbAndInputAttributes(oe.END)),this.updateThumbAndTrackUI(e),this.updateValueIndicatorUI(e),this.updateTickMarksUI()},o.prototype.updateThumbAndInputAttributes=function(e){if(e){var t=this.isRange&&e===oe.START?this.valueStart:this.value,i=String(t);this.adapter.setInputAttribute(we,i,e),this.isRange&&e===oe.START?this.adapter.setInputAttribute(ye,String(t+this.minRange),oe.END):this.isRange&&e===oe.END&&this.adapter.setInputAttribute(xe,String(t-this.minRange),oe.START),this.adapter.getInputValue(e)!==i&&this.adapter.setInputValue(i,e);var r=this.adapter.getValueToAriaValueTextFn();r&&this.adapter.setInputAttribute(be,r(t,e),e)}},o.prototype.updateValueIndicatorUI=function(e){if(this.isDiscrete){var t=this.isRange&&e===oe.START?this.valueStart:this.value;this.adapter.setValueIndicatorText(t,e===oe.START?oe.START:oe.END),!e&&this.isRange&&this.adapter.setValueIndicatorText(this.valueStart,oe.START)}},o.prototype.updateTickMarksUI=function(){if(this.isDiscrete&&this.hasTickMarks){var e=(this.valueStart-this.min)/this.step,t=(this.value-this.valueStart)/this.step+1,i=(this.max-this.value)/this.step,r=Array.from({length:e}).fill(re.INACTIVE),o=Array.from({length:t}).fill(re.ACTIVE),s=Array.from({length:i}).fill(re.INACTIVE);this.adapter.updateTickMarks(r.concat(o).concat(s))}},o.prototype.mapClientXOnSliderScale=function(e){var t=(e-this.rect.left)/this.rect.width;this.adapter.isRTL()&&(t=1-t);var i=this.min+t*(this.max-this.min);return i===this.max||i===this.min?i:Number(this.quantize(i).toFixed(this.numDecimalPlaces))},o.prototype.quantize=function(e){var t=Math.round((e-this.min)/this.step);return this.min+t*this.step},o.prototype.updateValue=function(e,t,i){var r=(void 0===i?{}:i).emitInputEvent;if(e=this.clampValue(e,t),this.isRange&&t===oe.START){if(this.valueStart===e)return;this.valueStart=e}else{if(this.value===e)return;this.value=e}this.updateUI(t),r&&this.adapter.emitInputEvent(t===oe.START?this.valueStart:this.value,t)},o.prototype.clampValue=function(e,t){return e=Math.min(Math.max(e,this.min),this.max),this.isRange&&t===oe.START&&e>this.value-this.minRange?this.value-this.minRange:this.isRange&&t===oe.END&&e<this.valueStart+this.minRange?this.valueStart+this.minRange:e},o.prototype.updateThumbAndTrackUI=function(e){var t=this,i=this.max,r=this.min,o=(this.value-this.valueStart)/(i-r),s=o*this.rect.width,n=this.adapter.isRTL(),a=Ee?ne(window,"transform"):"transform";if(this.isRange){var l=this.adapter.isRTL()?(i-this.value)/(i-r)*this.rect.width:(this.valueStart-r)/(i-r)*this.rect.width,c=l+s;this.animFrame.request(ae.SLIDER_UPDATE,(function(){!n&&e===oe.START||n&&e!==oe.START?(t.adapter.setTrackActiveStyleProperty("transform-origin","right"),t.adapter.setTrackActiveStyleProperty("left","auto"),t.adapter.setTrackActiveStyleProperty("right",t.rect.width-c+"px")):(t.adapter.setTrackActiveStyleProperty("transform-origin","left"),t.adapter.setTrackActiveStyleProperty("right","auto"),t.adapter.setTrackActiveStyleProperty("left",l+"px")),t.adapter.setTrackActiveStyleProperty(a,"scaleX("+o+")");var i=n?c:l,r=t.adapter.isRTL()?l:c;e!==oe.START&&e&&t.initialStylesRemoved||(t.adapter.setThumbStyleProperty(a,"translateX("+i+"px)",oe.START),t.alignValueIndicator(oe.START,i)),e!==oe.END&&e&&t.initialStylesRemoved||(t.adapter.setThumbStyleProperty(a,"translateX("+r+"px)",oe.END),t.alignValueIndicator(oe.END,r)),t.removeInitialStyles(n),t.updateOverlappingThumbsUI(i,r,e)}))}else this.animFrame.request(ae.SLIDER_UPDATE,(function(){var e=n?t.rect.width-s:s;t.adapter.setThumbStyleProperty(a,"translateX("+e+"px)",oe.END),t.alignValueIndicator(oe.END,e),t.adapter.setTrackActiveStyleProperty(a,"scaleX("+o+")"),t.removeInitialStyles(n)}))},o.prototype.alignValueIndicator=function(e,t){if(this.isDiscrete){var i=this.adapter.getThumbBoundingClientRect(e).width/2,r=this.adapter.getValueIndicatorContainerWidth(e),o=this.adapter.getBoundingClientRect().width;r/2>t+i?(this.adapter.setThumbStyleProperty(Te,i+"px",e),this.adapter.setThumbStyleProperty(Ce,"auto",e),this.adapter.setThumbStyleProperty(Me,"translateX(-50%)",e),this.adapter.setThumbStyleProperty(Pe,"0",e),this.adapter.setThumbStyleProperty($e,"auto",e),this.adapter.setThumbStyleProperty(Le,"none",e)):r/2>o-t+i?(this.adapter.setThumbStyleProperty(Te,"auto",e),this.adapter.setThumbStyleProperty(Ce,i+"px",e),this.adapter.setThumbStyleProperty(Me,"translateX(50%)",e),this.adapter.setThumbStyleProperty(Pe,"auto",e),this.adapter.setThumbStyleProperty($e,"0",e),this.adapter.setThumbStyleProperty(Le,"none",e)):(this.adapter.setThumbStyleProperty(Te,"50%",e),this.adapter.setThumbStyleProperty(Ce,"auto",e),this.adapter.setThumbStyleProperty(Me,"translateX(-50%)",e),this.adapter.setThumbStyleProperty(Pe,"50%",e),this.adapter.setThumbStyleProperty($e,"auto",e),this.adapter.setThumbStyleProperty(Le,"translateX(-50%)",e))}},o.prototype.removeInitialStyles=function(e){if(!this.initialStylesRemoved){var t=e?"right":"left";this.adapter.removeThumbStyleProperty(t,oe.END),this.isRange&&this.adapter.removeThumbStyleProperty(t,oe.START),this.initialStylesRemoved=!0,this.resetTrackAndThumbAnimation()}},o.prototype.resetTrackAndThumbAnimation=function(){var e=this;if(this.isDiscrete){var t=Ee?ne(window,"transition"):"transition",i="none 0s ease 0s";this.adapter.setThumbStyleProperty(t,i,oe.END),this.isRange&&this.adapter.setThumbStyleProperty(t,i,oe.START),this.adapter.setTrackActiveStyleProperty(t,i),requestAnimationFrame((function(){e.adapter.removeThumbStyleProperty(t,oe.END),e.adapter.removeTrackActiveStyleProperty(t),e.isRange&&e.adapter.removeThumbStyleProperty(t,oe.START)}))}},o.prototype.updateOverlappingThumbsUI=function(e,t,i){var r=!1;if(this.adapter.isRTL()){var o=e-this.startThumbKnobWidth/2;r=t+this.endThumbKnobWidth/2>=o}else{r=e+this.startThumbKnobWidth/2>=t-this.endThumbKnobWidth/2}r?(this.adapter.addThumbClass(he,i||oe.END),this.adapter.removeThumbClass(he,i===oe.START?oe.END:oe.START)):(this.adapter.removeThumbClass(he,oe.START),this.adapter.removeThumbClass(he,oe.END))},o.prototype.convertAttributeValueToNumber=function(e,t){if(null===e)throw new Error("MDCSliderFoundation: `"+t+"` must be non-null.");var i=Number(e);if(isNaN(i))throw new Error("MDCSliderFoundation: `"+t+"` value is `"+e+"`, but must be a number.");return i},o.prototype.validateProperties=function(e){var t=e.min,i=e.max,r=e.value,o=e.valueStart,s=e.step,n=e.minRange;if(t>=i)throw new Error("MDCSliderFoundation: min must be strictly less than max. Current: [min: "+t+", max: "+i+"]");if(s<=0)throw new Error("MDCSliderFoundation: step must be a positive number. Current step: "+s);if(this.isRange){if(r<t||r>i||o<t||o>i)throw new Error("MDCSliderFoundation: values must be in [min, max] range. Current values: [start value: "+o+", end value: "+r+", min: "+t+", max: "+i+"]");if(o>r)throw new Error("MDCSliderFoundation: start value must be <= end value. Current values: [start value: "+o+", end value: "+r+"]");if(n<0)throw new Error("MDCSliderFoundation: minimum range must be non-negative. Current min range: "+n);if(r-o<n)throw new Error("MDCSliderFoundation: start value and end value must differ by at least "+n+". Current values: [start value: "+o+", end value: "+r+"]");var a=(o-t)/s,l=(r-t)/s;if(!Number.isInteger(parseFloat(a.toFixed(6)))||!Number.isInteger(parseFloat(l.toFixed(6))))throw new Error("MDCSliderFoundation: Slider values must be valid based on the step value ("+s+"). Current values: [start value: "+o+", end value: "+r+", min: "+t+"]")}else{if(r<t||r>i)throw new Error("MDCSliderFoundation: value must be in [min, max] range. Current values: [value: "+r+", min: "+t+", max: "+i+"]");l=(r-t)/s;if(!Number.isInteger(parseFloat(l.toFixed(6))))throw new Error("MDCSliderFoundation: Slider value must be valid based on the step value ("+s+"). Current value: "+r)}},o.prototype.registerEventHandlers=function(){this.adapter.registerWindowEventHandler("resize",this.resizeListener),o.SUPPORTS_POINTER_EVENTS?(this.adapter.registerEventHandler("pointerdown",this.pointerdownListener),this.adapter.registerEventHandler("pointerup",this.pointerupListener)):(this.adapter.registerEventHandler("mousedown",this.mousedownOrTouchstartListener),this.adapter.registerEventHandler("touchstart",this.mousedownOrTouchstartListener)),this.isRange&&(this.adapter.registerThumbEventHandler(oe.START,"mouseenter",this.thumbMouseenterListener),this.adapter.registerThumbEventHandler(oe.START,"mouseleave",this.thumbMouseleaveListener),this.adapter.registerInputEventHandler(oe.START,"change",this.inputStartChangeListener),this.adapter.registerInputEventHandler(oe.START,"focus",this.inputStartFocusListener),this.adapter.registerInputEventHandler(oe.START,"blur",this.inputStartBlurListener)),this.adapter.registerThumbEventHandler(oe.END,"mouseenter",this.thumbMouseenterListener),this.adapter.registerThumbEventHandler(oe.END,"mouseleave",this.thumbMouseleaveListener),this.adapter.registerInputEventHandler(oe.END,"change",this.inputEndChangeListener),this.adapter.registerInputEventHandler(oe.END,"focus",this.inputEndFocusListener),this.adapter.registerInputEventHandler(oe.END,"blur",this.inputEndBlurListener)},o.prototype.deregisterEventHandlers=function(){this.adapter.deregisterWindowEventHandler("resize",this.resizeListener),o.SUPPORTS_POINTER_EVENTS?(this.adapter.deregisterEventHandler("pointerdown",this.pointerdownListener),this.adapter.deregisterEventHandler("pointerup",this.pointerupListener)):(this.adapter.deregisterEventHandler("mousedown",this.mousedownOrTouchstartListener),this.adapter.deregisterEventHandler("touchstart",this.mousedownOrTouchstartListener)),this.isRange&&(this.adapter.deregisterThumbEventHandler(oe.START,"mouseenter",this.thumbMouseenterListener),this.adapter.deregisterThumbEventHandler(oe.START,"mouseleave",this.thumbMouseleaveListener),this.adapter.deregisterInputEventHandler(oe.START,"change",this.inputStartChangeListener),this.adapter.deregisterInputEventHandler(oe.START,"focus",this.inputStartFocusListener),this.adapter.deregisterInputEventHandler(oe.START,"blur",this.inputStartBlurListener)),this.adapter.deregisterThumbEventHandler(oe.END,"mouseenter",this.thumbMouseenterListener),this.adapter.deregisterThumbEventHandler(oe.END,"mouseleave",this.thumbMouseleaveListener),this.adapter.deregisterInputEventHandler(oe.END,"change",this.inputEndChangeListener),this.adapter.deregisterInputEventHandler(oe.END,"focus",this.inputEndFocusListener),this.adapter.deregisterInputEventHandler(oe.END,"blur",this.inputEndBlurListener)},o.prototype.handlePointerup=function(){this.handleUp(),this.adapter.deregisterEventHandler("pointermove",this.moveListener)},o.SUPPORTS_POINTER_EVENTS=Ee&&Boolean(window.PointerEvent)&&!(["iPad Simulator","iPhone Simulator","iPod Simulator","iPad","iPhone","iPod"].includes(navigator.platform)||navigator.userAgent.includes("Mac")&&"ontouchend"in document),o}(o);function Ae(e){var t=/(?:\.(\d+))?(?:[eE]([+\-]?\d+))?$/.exec(String(e));if(!t)return 0;var i=t[1]||"",r=t[2]||0;return Math.max(0,("0"===i?0:i.length)-Number(r))}
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */class Ne extends u{constructor(){super(...arguments),this.mdcFoundationClass=Re,this.disabled=!1,this.min=0,this.max=100,this.valueEnd=0,this.name="",this.step=1,this.withTickMarks=!1,this.discrete=!1,this.tickMarks=[],this.trackTransformOriginStyle="",this.trackLeftStyle="",this.trackRightStyle="",this.trackTransitionStyle="",this.endThumbWithIndicator=!1,this.endThumbTop=!1,this.shouldRenderEndRipple=!1,this.endThumbTransformStyle="",this.endThumbTransitionStyle="",this.endThumbCssProperties={},this.valueToAriaTextTransform=null,this.valueToValueIndicatorTransform=e=>`${e}`,this.boundMoveListener=null,this.endRippleHandlers=new h((()=>(this.shouldRenderEndRipple=!0,this.endRipple)))}update(e){if(e.has("valueEnd")&&this.mdcFoundation){this.mdcFoundation.setValue(this.valueEnd);const e=this.mdcFoundation.getValue();e!==this.valueEnd&&(this.valueEnd=e)}e.has("discrete")&&(this.discrete||(this.tickMarks=[])),super.update(e)}render(){return this.renderRootEl(p`
      ${this.renderStartInput()}
      ${this.renderEndInput()}
      ${this.renderTrack()}
      ${this.renderTickMarks()}
      ${this.renderStartThumb()}
      ${this.renderEndThumb()}`)}renderRootEl(e){const t=m({"mdc-slider--disabled":this.disabled,"mdc-slider--discrete":this.discrete});return p`
    <div
        class="mdc-slider ${t}"
        @pointerdown=${this.onPointerdown}
        @pointerup=${this.onPointerup}
        @contextmenu=${this.onContextmenu}>
      ${e}
    </div>`}renderStartInput(){return f}renderEndInput(){var e;return p`
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
          aria-label=${g(this.ariaLabel)}
          aria-labelledby=${g(this.ariaLabelledBy)}
          aria-describedby=${g(this.ariaDescribedBy)}
          aria-valuetext=${g(null===(e=this.valueToAriaTextTransform)||void 0===e?void 0:e.call(this,this.valueEnd))}>
    `}renderTrack(){return f}renderTickMarks(){return this.withTickMarks?p`
      <div class="mdc-slider__tick-marks">
        ${this.tickMarks.map((e=>{const t=e===re.ACTIVE;return p`<div class="${t?"mdc-slider__tick-mark--active":"mdc-slider__tick-mark--inactive"}"></div>`}))}
      </div>`:f}renderStartThumb(){return f}renderEndThumb(){const e=m({"mdc-slider__thumb--with-indicator":this.endThumbWithIndicator,"mdc-slider__thumb--top":this.endThumbTop}),t=v(Object.assign({"-webkit-transform":this.endThumbTransformStyle,transform:this.endThumbTransformStyle,"-webkit-transition":this.endThumbTransitionStyle,transition:this.endThumbTransitionStyle,left:this.endThumbTransformStyle||"rtl"===getComputedStyle(this).direction?"":`calc(${(this.valueEnd-this.min)/(this.max-this.min)*100}% - 24px)`,right:this.endThumbTransformStyle||"rtl"!==getComputedStyle(this).direction?"":`calc(${(this.valueEnd-this.min)/(this.max-this.min)*100}% - 24px)`},this.endThumbCssProperties)),i=this.shouldRenderEndRipple?p`<mwc-ripple class="ripple" unbounded></mwc-ripple>`:f;return p`
      <div
          class="mdc-slider__thumb end ${e}"
          style=${t}
          @mouseenter=${this.onEndMouseenter}
          @mouseleave=${this.onEndMouseleave}>
        ${i}
        ${this.renderValueIndicator(this.valueToValueIndicatorTransform(this.valueEnd))}
        <div class="mdc-slider__thumb-knob"></div>
      </div>
    `}renderValueIndicator(e){return this.discrete?p`
    <div class="mdc-slider__value-indicator-container" aria-hidden="true">
      <div class="mdc-slider__value-indicator">
        <span class="mdc-slider__value-indicator-text">
          ${e}
        </span>
      </div>
    </div>`:f}disconnectedCallback(){super.disconnectedCallback(),this.mdcFoundation&&this.mdcFoundation.destroy()}createAdapter(){}async firstUpdated(){super.firstUpdated(),await this.layout(!0)}updated(e){super.updated(e),this.mdcFoundation&&(e.has("disabled")&&this.mdcFoundation.setDisabled(this.disabled),e.has("min")&&this.mdcFoundation.setMin(this.min),e.has("max")&&this.mdcFoundation.setMax(this.max),e.has("step")&&this.mdcFoundation.setStep(this.step),e.has("discrete")&&this.mdcFoundation.setIsDiscrete(this.discrete),e.has("withTickMarks")&&this.mdcFoundation.setHasTickMarks(this.withTickMarks))}async layout(e=!1){var t;null===(t=this.mdcFoundation)||void 0===t||t.layout({skipUpdateUI:e}),this.requestUpdate(),await this.updateComplete}onEndChange(e){var t;this.valueEnd=Number(e.target.value),null===(t=this.mdcFoundation)||void 0===t||t.handleInputChange(oe.END)}onEndFocus(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleInputFocus(oe.END),this.endRippleHandlers.startFocus()}onEndBlur(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleInputBlur(oe.END),this.endRippleHandlers.endFocus()}onEndMouseenter(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleThumbMouseenter(),this.endRippleHandlers.startHover()}onEndMouseleave(){var e;null===(e=this.mdcFoundation)||void 0===e||e.handleThumbMouseleave(),this.endRippleHandlers.endHover()}onPointerdown(e){this.layout(),this.mdcFoundation&&(this.mdcFoundation.handlePointerdown(e),this.boundMoveListener=this.mdcFoundation.handleMove.bind(this.mdcFoundation),this.mdcRoot.addEventListener("pointermove",this.boundMoveListener))}onPointerup(){this.mdcFoundation&&(this.mdcFoundation.handleUp(),this.boundMoveListener&&(this.mdcRoot.removeEventListener("pointermove",this.boundMoveListener),this.boundMoveListener=null))}onContextmenu(e){e.preventDefault()}setFormData(e){this.name&&e.append(this.name,`${this.valueEnd}`)}}s([n("input.end")],Ne.prototype,"formElement",void 0),s([n(".mdc-slider")],Ne.prototype,"mdcRoot",void 0),s([n(".end.mdc-slider__thumb")],Ne.prototype,"endThumb",void 0),s([n(".end.mdc-slider__thumb .mdc-slider__thumb-knob")],Ne.prototype,"endThumbKnob",void 0),s([n(".end.mdc-slider__thumb .mdc-slider__value-indicator-container")],Ne.prototype,"endValueIndicatorContainer",void 0),s([a(".end .ripple")],Ne.prototype,"endRipple",void 0),s([l({type:Boolean,reflect:!0})],Ne.prototype,"disabled",void 0),s([l({type:Number})],Ne.prototype,"min",void 0),s([l({type:Number})],Ne.prototype,"max",void 0),s([l({type:Number})],Ne.prototype,"valueEnd",void 0),s([l({type:String})],Ne.prototype,"name",void 0),s([l({type:Number})],Ne.prototype,"step",void 0),s([l({type:Boolean})],Ne.prototype,"withTickMarks",void 0),s([l({type:Boolean})],Ne.prototype,"discrete",void 0),s([c()],Ne.prototype,"tickMarks",void 0),s([c()],Ne.prototype,"trackTransformOriginStyle",void 0),s([c()],Ne.prototype,"trackLeftStyle",void 0),s([c()],Ne.prototype,"trackRightStyle",void 0),s([c()],Ne.prototype,"trackTransitionStyle",void 0),s([c()],Ne.prototype,"endThumbWithIndicator",void 0),s([c()],Ne.prototype,"endThumbTop",void 0),s([c()],Ne.prototype,"shouldRenderEndRipple",void 0),s([c()],Ne.prototype,"endThumbTransformStyle",void 0),s([c()],Ne.prototype,"endThumbTransitionStyle",void 0),s([c()],Ne.prototype,"endThumbCssProperties",void 0),s([d,l({type:String,attribute:"aria-label"})],Ne.prototype,"ariaLabel",void 0),s([d,l({type:String,attribute:"aria-labelledby"})],Ne.prototype,"ariaLabelledBy",void 0),s([d,l({type:String,attribute:"aria-describedby"})],Ne.prototype,"ariaDescribedBy",void 0);
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
class Ie extends Ne{get value(){return this.valueEnd}set value(e){this.valueEnd=e}renderTrack(){const e=v({"transform-origin":this.trackTransformOriginStyle,left:this.trackLeftStyle,right:this.trackRightStyle,"-webkit-transform":`scaleX(${(this.valueEnd-this.min)/(this.max-this.min)})`,transform:`scaleX(${(this.valueEnd-this.min)/(this.max-this.min)})`,"-webkit-transition":this.trackTransitionStyle,transition:this.trackTransitionStyle});return p`
      <div class="mdc-slider__track">
        <div class="mdc-slider__track--inactive"></div>
        <div class="mdc-slider__track--active">
          <div
              class="mdc-slider__track--active_fill"
              style=${e}>
          </div>
        </div>
      </div>`}createAdapter(){return{addClass:e=>{if("mdc-slider--disabled"===e)this.disabled=!0},removeClass:e=>{if("mdc-slider--disabled"===e)this.disabled=!1},hasClass:e=>{switch(e){case"mdc-slider--disabled":return this.disabled;case"mdc-slider--discrete":return this.discrete;default:return!1}},addThumbClass:(e,t)=>{if(t!==oe.START&&"mdc-slider__thumb--with-indicator"===e)this.endThumbWithIndicator=!0},removeThumbClass:(e,t)=>{if(t!==oe.START&&"mdc-slider__thumb--with-indicator"===e)this.endThumbWithIndicator=!1},registerEventHandler:()=>{},deregisterEventHandler:()=>{},registerBodyEventHandler:(e,t)=>{document.body.addEventListener(e,t)},deregisterBodyEventHandler:(e,t)=>{document.body.removeEventListener(e,t)},registerInputEventHandler:(e,t,i)=>{e!==oe.START&&this.formElement.addEventListener(t,i)},deregisterInputEventHandler:(e,t,i)=>{e!==oe.START&&this.formElement.removeEventListener(t,i)},registerThumbEventHandler:()=>{},deregisterThumbEventHandler:()=>{},registerWindowEventHandler:(e,t)=>{window.addEventListener(e,t)},deregisterWindowEventHandler:(e,t)=>{window.addEventListener(e,t)},emitChangeEvent:(e,t)=>{if(t===oe.START)return;const i=new CustomEvent("change",{bubbles:!0,composed:!0,detail:{value:e,thumb:t}});this.dispatchEvent(i)},emitDragEndEvent:(e,t)=>{t!==oe.START&&this.endRippleHandlers.endPress()},emitDragStartEvent:(e,t)=>{t!==oe.START&&this.endRippleHandlers.startPress()},emitInputEvent:(e,t)=>{if(t===oe.START)return;const i=new CustomEvent("input",{bubbles:!0,composed:!0,detail:{value:e,thumb:t}});this.dispatchEvent(i)},focusInput:e=>{e!==oe.START&&this.formElement.focus()},getAttribute:()=>"",getBoundingClientRect:()=>this.mdcRoot.getBoundingClientRect(),getInputAttribute:(e,t)=>{if(t===oe.START)return null;switch(e){case"min":return this.min.toString();case"max":return this.max.toString();case"value":return this.valueEnd.toString();case"step":return this.step.toString();default:return null}},getInputValue:e=>e===oe.START?"":this.valueEnd.toString(),getThumbBoundingClientRect:e=>e===oe.START?this.getBoundingClientRect():this.endThumb.getBoundingClientRect(),getThumbKnobWidth:e=>e===oe.START?0:this.endThumbKnob.getBoundingClientRect().width,getValueIndicatorContainerWidth:e=>e===oe.START?0:this.endValueIndicatorContainer.getBoundingClientRect().width,getValueToAriaValueTextFn:()=>this.valueToAriaTextTransform,isInputFocused:e=>{if(e===oe.START)return!1;const t=b();return t[t.length-1]===this.formElement},isRTL:()=>"rtl"===getComputedStyle(this).direction,setInputAttribute:(e,t,i)=>{oe.START},removeInputAttribute:e=>{},setThumbStyleProperty:(e,t,i)=>{if(i!==oe.START)switch(e){case"transform":case"-webkit-transform":this.endThumbTransformStyle=t;break;case"transition":case"-webkit-transition":this.endThumbTransitionStyle=t;break;default:e.startsWith("--")&&(this.endThumbCssProperties[e]=t)}},removeThumbStyleProperty:(e,t)=>{if(t!==oe.START)switch(e){case"left":case"right":break;case"transition":case"-webkit-transition":this.endThumbTransitionStyle=""}},setTrackActiveStyleProperty:(e,t)=>{switch(e){case"transform-origin":this.trackTransformOriginStyle=t;break;case"left":this.trackLeftStyle=t;break;case"right":this.trackRightStyle=t;break;case"transform":case"-webkit-transform":break;case"transition":case"-webkit-transition":this.trackTransitionStyle=t}},removeTrackActiveStyleProperty:e=>{switch(e){case"transition":case"-webkit-transition":this.trackTransitionStyle=""}},setInputValue:(e,t)=>{t!==oe.START&&(this.valueEnd=Number(e))},setPointerCapture:e=>{this.mdcRoot.setPointerCapture(e)},setValueIndicatorText:()=>{},updateTickMarks:e=>{this.tickMarks=e}}}}s([l({type:Number})],Ie.prototype,"value",null);
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
let De=class extends Ie{};De.styles=[ie],De=s([_("mwc-slider")],De);let Oe=class extends k{static get styles(){return[S,T,C,M,P,$`
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
      `]}render(){return L`
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
    `}constructor(){super(),this.editable=!1,this.pin=!1,this.markers=!1,this.marker_limit=30,this.disabled=!1;new IntersectionObserver(((e,t)=>{e.forEach((e=>{e.intersectionRatio>0&&(this.value!==this.slider.value&&(this.slider.value=this.value),this.slider.layout())}))}),{}).observe(this)}firstUpdated(){this.editable&&(this.textfield.style.display="flex"),this.checkMarkerDisplay()}update(e){Array.from(e.keys()).some((e=>["value","min","max"].includes(e)))&&this.min==this.max&&(this.max=this.max+1,this.value=this.min,this.disabled=!0),super.update(e)}updated(e){e.forEach(((e,t)=>{["min","max","step"].includes(t)&&this.checkMarkerDisplay()}))}syncToText(){this.value=this.slider.value}syncToSlider(){this.textfield.step=this.step;const e=Math.round(this.textfield.value/this.step)*this.step;var t;this.textfield.value=e.toFixed((t=this.step,Math.floor(t)===t?0:t.toString().split(".")[1].length||0)),this.textfield.value>this.max&&(this.textfield.value=this.max),this.textfield.value<this.min&&(this.textfield.value=this.min),this.value=this.textfield.value;const i=new CustomEvent("change",{detail:{}});this.dispatchEvent(i)}checkMarkerDisplay(){this.markers&&(this.max-this.min)/this.step>this.marker_limit&&this.slider.removeAttribute("markers")}};s([y({type:Number})],Oe.prototype,"step",void 0),s([y({type:Number})],Oe.prototype,"value",void 0),s([y({type:Number})],Oe.prototype,"max",void 0),s([y({type:Number})],Oe.prototype,"min",void 0),s([y({type:String})],Oe.prototype,"prefix",void 0),s([y({type:String})],Oe.prototype,"suffix",void 0),s([y({type:Boolean})],Oe.prototype,"editable",void 0),s([y({type:Boolean})],Oe.prototype,"pin",void 0),s([y({type:Boolean})],Oe.prototype,"markers",void 0),s([y({type:Number})],Oe.prototype,"marker_limit",void 0),s([y({type:Boolean})],Oe.prototype,"disabled",void 0),s([x("#slider",!0)],Oe.prototype,"slider",void 0),s([x("#textfield",!0)],Oe.prototype,"textfield",void 0),Oe=s([w("lablup-slider")],Oe);let Fe=class extends E{constructor(){super(),this.is_connected=!1,this.direction="horizontal",this.location="",this.aliases=Object(),this.aggregate_updating=!1,this.project_resource_monitor=!1,this.active=!1,this.resourceBroker=globalThis.resourceBroker,this.notification=globalThis.lablupNotification,this.init_resource()}static get is(){return"backend-ai-resource-monitor"}static get styles(){return[S,T,C,M,P,$`
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
      `]}init_resource(){this.total_slot={},this.total_resource_group_slot={},this.total_project_slot={},this.used_slot={},this.used_resource_group_slot={},this.used_project_slot={},this.available_slot={},this.used_slot_percent={},this.used_resource_group_slot_percent={},this.used_project_slot_percent={},this.concurrency_used=0,this.concurrency_max=0,this.concurrency_limit=0,this._status="inactive",this.scaling_groups=[{name:""}],this.scaling_group="",this.sessions_list=[],this.metric_updating=!1,this.metadata_updating=!1}firstUpdated(){new ResizeObserver((()=>{this._updateToggleResourceMonitorDisplay()})).observe(this.resourceGauge),document.addEventListener("backend-ai-group-changed",(e=>{this.scaling_group="",this._updatePageVariables(!0)})),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.is_connected=!0,setInterval((()=>{this._periodicUpdateResourcePolicy()}),2e4)}),{once:!0}):this.is_connected=!0,document.addEventListener("backend-ai-session-list-refreshed",(()=>{this._updatePageVariables(!0)}))}async _periodicUpdateResourcePolicy(){return this.active?(await this._refreshResourcePolicy(),this.aggregateResource("refresh-resource-policy"),Promise.resolve(!0)):Promise.resolve(!1)}async updateScalingGroup(e=!1,t){await this.resourceBroker.updateScalingGroup(e,t.target.value),this.active&&!0===e&&(await this._refreshResourcePolicy(),this.aggregateResource("update-scaling-group"))}async _viewStateChanged(e){await this.updateComplete,this.active&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.project_resource_monitor=this.resourceBroker.allow_project_resource_monitor,this._updatePageVariables(!0)}),{once:!0}):(this.project_resource_monitor=this.resourceBroker.allow_project_resource_monitor,await this._updatePageVariables(!0)))}async _updatePageVariables(e){return this.active&&!1===this.metadata_updating?(this.metadata_updating=!0,await this.resourceBroker._updatePageVariables(e),this.sessions_list=this.resourceBroker.sessions_list,await this._refreshResourcePolicy(),this.aggregateResource("update-page-variable"),this.metadata_updating=!1,Promise.resolve(!0)):Promise.resolve(!1)}_updateToggleResourceMonitorDisplay(){var e,t;const i=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#resource-legend"),r=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#resource-gauge-toggle-button");document.body.clientWidth>750&&"horizontal"==this.direction?(i.style.display="flex",i.style.marginTop="0",Array.from(this.resourceGauge.children).forEach((e=>{e.style.display="flex"}))):r.selected?(i.style.display="flex",i.style.marginTop="0",document.body.clientWidth<750&&(this.resourceGauge.style.left="20px",this.resourceGauge.style.right="20px"),Array.from(this.resourceGauge.children).forEach((e=>{e.style.display="flex"}))):(Array.from(this.resourceGauge.children).forEach((e=>{e.style.display="none"})),i.style.display="none")}async _refreshResourcePolicy(e=!1){return this.active?this.resourceBroker._refreshResourcePolicy().then((e=>(!1===e&&setTimeout((()=>{this._refreshResourcePolicy()}),2500),this.concurrency_used=this.resourceBroker.concurrency_used,this.concurrency_max=this.concurrency_used>this.resourceBroker.concurrency_max?this.concurrency_used:this.resourceBroker.concurrency_max,Promise.resolve(!0)))).catch((e=>(this.metadata_updating=!1,e&&e.message?(this.notification.text=R.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=R.relieve(e.title),this.notification.show(!0,e)),Promise.resolve(!1)))):Promise.resolve(!0)}_aliasName(e){const t=this.resourceBroker.imageTagAlias,i=this.resourceBroker.imageTagReplace;for(const[t,r]of Object.entries(i)){const i=new RegExp(t);if(i.test(e))return e.replace(i,r)}return e in t?t[e]:e}async _aggregateResourceUse(e=""){return this.resourceBroker._aggregateCurrentResource(e).then((t=>!1===t?setTimeout((()=>{this._aggregateResourceUse(e)}),1e3):(this.concurrency_used=this.resourceBroker.concurrency_used,this.scaling_group=this.resourceBroker.scaling_group,this.scaling_groups=this.resourceBroker.scaling_groups,this.total_slot=this.resourceBroker.total_slot,this.total_resource_group_slot=this.resourceBroker.total_resource_group_slot,this.total_project_slot=this.resourceBroker.total_project_slot,this.used_slot=this.resourceBroker.used_slot,this.used_resource_group_slot=this.resourceBroker.used_resource_group_slot,this.used_project_slot=this.resourceBroker.used_project_slot,this.used_project_slot_percent=this.resourceBroker.used_project_slot_percent,this.concurrency_limit=this.resourceBroker.concurrency_limit,this.available_slot=this.resourceBroker.available_slot,this.used_slot_percent=this.resourceBroker.used_slot_percent,this.used_resource_group_slot_percent=this.resourceBroker.used_resource_group_slot_percent,Promise.resolve(!0)))).then((()=>Promise.resolve(!0))).catch((e=>(e&&e.message&&(console.log(e),this.notification.text=R.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)),Promise.resolve(!1))))}aggregateResource(e=""){void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._aggregateResourceUse(e)}),!0):this._aggregateResourceUse(e)}_numberWithPostfix(e,t=""){return isNaN(parseInt(e))?"":parseInt(e)+t}_prefixFormatWithoutTrailingZeros(e="0",t){const i="string"==typeof e?parseFloat(e):e;return parseFloat(i.toFixed(t)).toString()}_prefixFormat(e="0",t){var i;return"string"==typeof e?null===(i=parseFloat(e))||void 0===i?void 0:i.toFixed(t):null==e?void 0:e.toFixed(t)}render(){return L`
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
            ${this.total_slot.cuda_device?L`
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
                `:L``}
            ${this.resourceBroker.total_slot.cuda_shares&&this.resourceBroker.total_slot.cuda_shares>0?L`
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
                `:L``}
            ${this.total_slot.rocm_device?L`
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
                `:L``}
            ${this.total_slot.tpu_device?L`
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
                `:L``}
            ${this.total_slot.ipu_device?L`
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
                `:L``}
            ${this.total_slot.atom_device?L`
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
                `:L``}
            ${this.total_slot.atom_plus_device?L`
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
                `:L``}
            ${this.total_slot.gaudi2_device?L`
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
                `:L``}
            ${this.total_slot.warboy_device?L`
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
                `:L``}
            ${this.total_slot.rngd_device?L`
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
                `:L``}
            ${this.total_slot.hyperaccel_lpu_device?L`
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
                `:L``}
            <div class="layout horizontal center-justified monitor">
              <div
                class="layout vertical center center-justified resource-name"
              >
                <span class="gauge-name">
                  ${A("session.launcher.Sessions")}
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
              ${A("session.launcher.ResourceMonitorToggle")}
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
            ${A("session.launcher.CurrentResourceGroup")}
            (${this.scaling_group})
          </span>
        </div>
        <div
          class="layout horizontal center ${"vertical"===this.direction?"start-justified":"end-justified"}"
        >
          <div class="resource-legend-icon end"></div>
          <span class="resource-legend">
            ${A("session.launcher.UserResourceLimit")}
          </span>
        </div>
      </div>
      ${"vertical"===this.direction&&!0===this.project_resource_monitor&&(this.total_project_slot.cpu>0||this.total_project_slot.cpu===1/0)?L`
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
                    ${A("session.launcher.Project")}
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
                  ${this.total_project_slot.cuda_device?L`
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
                      `:L``}
                  ${this.total_project_slot.cuda_shares?L`
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
                      `:L``}
                  ${this.total_project_slot.rocm_device?L`
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
                      `:L``}
                  ${this.total_project_slot.tpu_device?L`
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
                      `:L``}
                  ${this.total_project_slot.ipu_device?L`
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
                      `:L``}
                  ${this.total_project_slot.atom_device?L`
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
                      `:L``}
                  ${this.total_project_slot.warboy_device?L`
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
                      `:L``}
                  ${this.total_project_slot.rngd_device?L`
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
                      `:L``}
                  ${this.total_project_slot.hyperaccel_lpu_device?L`
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
                      `:L``}
                </div>
                <div class="flex"></div>
              </div>
            </div>
          `:L``}
    `}};s([y({type:Boolean})],Fe.prototype,"is_connected",void 0),s([y({type:String})],Fe.prototype,"direction",void 0),s([y({type:String})],Fe.prototype,"location",void 0),s([y({type:Object})],Fe.prototype,"aliases",void 0),s([y({type:Object})],Fe.prototype,"total_slot",void 0),s([y({type:Object})],Fe.prototype,"total_resource_group_slot",void 0),s([y({type:Object})],Fe.prototype,"total_project_slot",void 0),s([y({type:Object})],Fe.prototype,"used_slot",void 0),s([y({type:Object})],Fe.prototype,"used_resource_group_slot",void 0),s([y({type:Object})],Fe.prototype,"used_project_slot",void 0),s([y({type:Object})],Fe.prototype,"available_slot",void 0),s([y({type:Number})],Fe.prototype,"concurrency_used",void 0),s([y({type:Number})],Fe.prototype,"concurrency_max",void 0),s([y({type:Number})],Fe.prototype,"concurrency_limit",void 0),s([y({type:Object})],Fe.prototype,"used_slot_percent",void 0),s([y({type:Object})],Fe.prototype,"used_resource_group_slot_percent",void 0),s([y({type:Object})],Fe.prototype,"used_project_slot_percent",void 0),s([y({type:String})],Fe.prototype,"default_language",void 0),s([y({type:Boolean})],Fe.prototype,"_status",void 0),s([y({type:Number})],Fe.prototype,"num_sessions",void 0),s([y({type:String})],Fe.prototype,"scaling_group",void 0),s([y({type:Array})],Fe.prototype,"scaling_groups",void 0),s([y({type:Array})],Fe.prototype,"sessions_list",void 0),s([y({type:Boolean})],Fe.prototype,"metric_updating",void 0),s([y({type:Boolean})],Fe.prototype,"metadata_updating",void 0),s([y({type:Boolean})],Fe.prototype,"aggregate_updating",void 0),s([y({type:Object})],Fe.prototype,"scaling_group_selection_box",void 0),s([y({type:Boolean})],Fe.prototype,"project_resource_monitor",void 0),s([y({type:Object})],Fe.prototype,"resourceBroker",void 0),s([x("#resource-gauges")],Fe.prototype,"resourceGauge",void 0),Fe=s([w("backend-ai-resource-monitor")],Fe);let ze=class extends k{constructor(){super(...arguments),this.title="",this.message="",this.panelId="",this.horizontalsize="",this.headerColor="",this.elevation=1,this.autowidth=!1,this.width=350,this.widthpct=0,this.height=0,this.marginWidth=14,this.minwidth=0,this.maxwidth=0,this.pinned=!1,this.disabled=!1,this.narrow=!1,this.noheader=!1,this.scrollableY=!1}static get styles(){return[T,C,$`
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
      `]}render(){return L`
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
    `}firstUpdated(){var e,t,i,r,o,s,n;if(this.pinned||null==this.panelId){const r=null===(e=this.shadowRoot)||void 0===e?void 0:e.getElementById("button");null===(i=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("h4"))||void 0===i||i.removeChild(r)}const a=null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector(".card"),l=null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector(".content"),c=null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#header");this.autowidth?a.style.width="auto":a.style.width=0!==this.widthpct?this.widthpct+"%":this.width+"px",this.minwidth&&(a.style.minWidth=this.minwidth+"px"),this.maxwidth&&(a.style.minWidth=this.maxwidth+"px"),"2x"===this.horizontalsize?a.style.width=2*this.width+28+"px":"3x"===this.horizontalsize?a.style.width=3*this.width+56+"px":"4x"==this.horizontalsize&&(a.style.width=4*this.width+84+"px"),a.style.margin=this.marginWidth+"px",""!==this.headerColor&&(c.style.backgroundColor=this.headerColor),this.narrow&&((null===(n=this.shadowRoot)||void 0===n?void 0:n.querySelector("div.card > div")).style.margin="0",c.style.marginBottom="0"),this.height>0&&(130==this.height?a.style.height="fit-content":(l.style.height=this.height-70+"px",a.style.height=this.height+"px")),this.noheader&&(c.style.display="none"),this.scrollableY&&(l.style.overflowY="auto",l.style.overflowX="hidden")}_removePanel(){}};s([y({type:String})],ze.prototype,"title",void 0),s([y({type:String})],ze.prototype,"message",void 0),s([y({type:String})],ze.prototype,"panelId",void 0),s([y({type:String})],ze.prototype,"horizontalsize",void 0),s([y({type:String})],ze.prototype,"headerColor",void 0),s([y({type:Number})],ze.prototype,"elevation",void 0),s([y({type:Boolean})],ze.prototype,"autowidth",void 0),s([y({type:Number})],ze.prototype,"width",void 0),s([y({type:Number})],ze.prototype,"widthpct",void 0),s([y({type:Number})],ze.prototype,"height",void 0),s([y({type:Number})],ze.prototype,"marginWidth",void 0),s([y({type:Number})],ze.prototype,"minwidth",void 0),s([y({type:Number})],ze.prototype,"maxwidth",void 0),s([y({type:Boolean})],ze.prototype,"pinned",void 0),s([y({type:Boolean})],ze.prototype,"disabled",void 0),s([y({type:Boolean})],ze.prototype,"narrow",void 0),s([y({type:Boolean})],ze.prototype,"noheader",void 0),s([y({type:Boolean})],ze.prototype,"scrollableY",void 0),ze=s([w("lablup-activity-panel")],ze);const We=$`
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
`,Be=$`
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
`;var je=navigator.userAgent,He=navigator.platform,Ue=/gecko\/\d/i.test(je),Ve=/MSIE \d/.test(je),Ge=/Trident\/(?:[7-9]|\d{2,})\..*rv:(\d+)/.exec(je),qe=/Edge\/(\d+)/.exec(je),Ze=Ve||Ge||qe,Ke=Ze&&(Ve?document.documentMode||6:+(qe||Ge)[1]),Xe=!qe&&/WebKit\//.test(je),Ye=Xe&&/Qt\/\d+\.\d+/.test(je),Je=!qe&&/Chrome\//.test(je),Qe=/Opera\//.test(je),et=/Apple Computer/.test(navigator.vendor),tt=/Mac OS X 1\d\D([8-9]|\d\d)\D/.test(je),it=/PhantomJS/.test(je),rt=et&&(/Mobile\/\w+/.test(je)||navigator.maxTouchPoints>2),ot=/Android/.test(je),st=rt||ot||/webOS|BlackBerry|Opera Mini|Opera Mobi|IEMobile/i.test(je),nt=rt||/Mac/.test(He),at=/\bCrOS\b/.test(je),lt=/win/i.test(He),ct=Qe&&je.match(/Version\/(\d*\.\d*)/);ct&&(ct=Number(ct[1])),ct&&ct>=15&&(Qe=!1,Xe=!0);var dt=nt&&(Ye||Qe&&(null==ct||ct<12.11)),ut=Ue||Ze&&Ke>=9;function ht(e){return new RegExp("(^|\\s)"+e+"(?:$|\\s)\\s*")}var pt,mt=function(e,t){let i=e.className,r=ht(t).exec(i);if(r){let t=i.slice(r.index+r[0].length);e.className=i.slice(0,r.index)+(t?r[1]+t:"")}};function ft(e){for(let t=e.childNodes.length;t>0;--t)e.removeChild(e.firstChild);return e}function gt(e,t){return ft(e).appendChild(t)}function vt(e,t,i,r){let o=document.createElement(e);if(i&&(o.className=i),r&&(o.style.cssText=r),"string"==typeof t)o.appendChild(document.createTextNode(t));else if(t)for(let e=0;e<t.length;++e)o.appendChild(t[e]);return o}function bt(e,t,i,r){let o=vt(e,t,i,r);return o.setAttribute("role","presentation"),o}function _t(e,t){if(3==t.nodeType&&(t=t.parentNode),e.contains)return e.contains(t);do{if(11==t.nodeType&&(t=t.host),t==e)return!0}while(t=t.parentNode)}function yt(){let e;try{e=document.activeElement}catch(t){e=document.body||null}for(;e&&e.shadowRoot&&e.shadowRoot.activeElement;)e=e.shadowRoot.activeElement;return e}function xt(e,t){let i=e.className;ht(t).test(i)||(e.className+=(i?" ":"")+t)}function wt(e,t){let i=e.split(" ");for(let e=0;e<i.length;e++)i[e]&&!ht(i[e]).test(t)&&(t+=" "+i[e]);return t}pt=document.createRange?function(e,t,i,r){let o=document.createRange();return o.setEnd(r||e,i),o.setStart(e,t),o}:function(e,t,i){let r=document.body.createTextRange();try{r.moveToElementText(e.parentNode)}catch(e){return r}return r.collapse(!0),r.moveEnd("character",i),r.moveStart("character",t),r};var kt=function(e){e.select()};function St(e){let t=Array.prototype.slice.call(arguments,1);return function(){return e.apply(null,t)}}function Tt(e,t,i){t||(t={});for(let r in e)!e.hasOwnProperty(r)||!1===i&&t.hasOwnProperty(r)||(t[r]=e[r]);return t}function Ct(e,t,i,r,o){null==t&&-1==(t=e.search(/[^\s\u00a0]/))&&(t=e.length);for(let s=r||0,n=o||0;;){let r=e.indexOf("\t",s);if(r<0||r>=t)return n+(t-s);n+=r-s,n+=i-n%i,s=r+1}}rt?kt=function(e){e.selectionStart=0,e.selectionEnd=e.value.length}:Ze&&(kt=function(e){try{e.select()}catch(e){}});var Mt=class{constructor(){this.id=null,this.f=null,this.time=0,this.handler=St(this.onTimeout,this)}onTimeout(e){e.id=0,e.time<=+new Date?e.f():setTimeout(e.handler,e.time-+new Date)}set(e,t){this.f=t;const i=+new Date+e;(!this.id||i<this.time)&&(clearTimeout(this.id),this.id=setTimeout(this.handler,e),this.time=i)}};function Pt(e,t){for(let i=0;i<e.length;++i)if(e[i]==t)return i;return-1}var $t=50,Lt={toString:function(){return"CodeMirror.Pass"}},Et={scroll:!1},Rt={origin:"*mouse"},At={origin:"+move"};function Nt(e,t,i){for(let r=0,o=0;;){let s=e.indexOf("\t",r);-1==s&&(s=e.length);let n=s-r;if(s==e.length||o+n>=t)return r+Math.min(n,t-o);if(o+=s-r,o+=i-o%i,r=s+1,o>=t)return r}}var It=[""];function Dt(e){for(;It.length<=e;)It.push(Ot(It)+" ");return It[e]}function Ot(e){return e[e.length-1]}function Ft(e,t){let i=[];for(let r=0;r<e.length;r++)i[r]=t(e[r],r);return i}function zt(){}function Wt(e,t){let i;return Object.create?i=Object.create(e):(zt.prototype=e,i=new zt),t&&Tt(t,i),i}var Bt=/[\u00df\u0587\u0590-\u05f4\u0600-\u06ff\u3040-\u309f\u30a0-\u30ff\u3400-\u4db5\u4e00-\u9fcc\uac00-\ud7af]/;function jt(e){return/\w/.test(e)||e>""&&(e.toUpperCase()!=e.toLowerCase()||Bt.test(e))}function Ht(e,t){return t?!!(t.source.indexOf("\\w")>-1&&jt(e))||t.test(e):jt(e)}function Ut(e){for(let t in e)if(e.hasOwnProperty(t)&&e[t])return!1;return!0}var Vt=/[\u0300-\u036f\u0483-\u0489\u0591-\u05bd\u05bf\u05c1\u05c2\u05c4\u05c5\u05c7\u0610-\u061a\u064b-\u065e\u0670\u06d6-\u06dc\u06de-\u06e4\u06e7\u06e8\u06ea-\u06ed\u0711\u0730-\u074a\u07a6-\u07b0\u07eb-\u07f3\u0816-\u0819\u081b-\u0823\u0825-\u0827\u0829-\u082d\u0900-\u0902\u093c\u0941-\u0948\u094d\u0951-\u0955\u0962\u0963\u0981\u09bc\u09be\u09c1-\u09c4\u09cd\u09d7\u09e2\u09e3\u0a01\u0a02\u0a3c\u0a41\u0a42\u0a47\u0a48\u0a4b-\u0a4d\u0a51\u0a70\u0a71\u0a75\u0a81\u0a82\u0abc\u0ac1-\u0ac5\u0ac7\u0ac8\u0acd\u0ae2\u0ae3\u0b01\u0b3c\u0b3e\u0b3f\u0b41-\u0b44\u0b4d\u0b56\u0b57\u0b62\u0b63\u0b82\u0bbe\u0bc0\u0bcd\u0bd7\u0c3e-\u0c40\u0c46-\u0c48\u0c4a-\u0c4d\u0c55\u0c56\u0c62\u0c63\u0cbc\u0cbf\u0cc2\u0cc6\u0ccc\u0ccd\u0cd5\u0cd6\u0ce2\u0ce3\u0d3e\u0d41-\u0d44\u0d4d\u0d57\u0d62\u0d63\u0dca\u0dcf\u0dd2-\u0dd4\u0dd6\u0ddf\u0e31\u0e34-\u0e3a\u0e47-\u0e4e\u0eb1\u0eb4-\u0eb9\u0ebb\u0ebc\u0ec8-\u0ecd\u0f18\u0f19\u0f35\u0f37\u0f39\u0f71-\u0f7e\u0f80-\u0f84\u0f86\u0f87\u0f90-\u0f97\u0f99-\u0fbc\u0fc6\u102d-\u1030\u1032-\u1037\u1039\u103a\u103d\u103e\u1058\u1059\u105e-\u1060\u1071-\u1074\u1082\u1085\u1086\u108d\u109d\u135f\u1712-\u1714\u1732-\u1734\u1752\u1753\u1772\u1773\u17b7-\u17bd\u17c6\u17c9-\u17d3\u17dd\u180b-\u180d\u18a9\u1920-\u1922\u1927\u1928\u1932\u1939-\u193b\u1a17\u1a18\u1a56\u1a58-\u1a5e\u1a60\u1a62\u1a65-\u1a6c\u1a73-\u1a7c\u1a7f\u1b00-\u1b03\u1b34\u1b36-\u1b3a\u1b3c\u1b42\u1b6b-\u1b73\u1b80\u1b81\u1ba2-\u1ba5\u1ba8\u1ba9\u1c2c-\u1c33\u1c36\u1c37\u1cd0-\u1cd2\u1cd4-\u1ce0\u1ce2-\u1ce8\u1ced\u1dc0-\u1de6\u1dfd-\u1dff\u200c\u200d\u20d0-\u20f0\u2cef-\u2cf1\u2de0-\u2dff\u302a-\u302f\u3099\u309a\ua66f-\ua672\ua67c\ua67d\ua6f0\ua6f1\ua802\ua806\ua80b\ua825\ua826\ua8c4\ua8e0-\ua8f1\ua926-\ua92d\ua947-\ua951\ua980-\ua982\ua9b3\ua9b6-\ua9b9\ua9bc\uaa29-\uaa2e\uaa31\uaa32\uaa35\uaa36\uaa43\uaa4c\uaab0\uaab2-\uaab4\uaab7\uaab8\uaabe\uaabf\uaac1\uabe5\uabe8\uabed\udc00-\udfff\ufb1e\ufe00-\ufe0f\ufe20-\ufe26\uff9e\uff9f]/;function Gt(e){return e.charCodeAt(0)>=768&&Vt.test(e)}function qt(e,t,i){for(;(i<0?t>0:t<e.length)&&Gt(e.charAt(t));)t+=i;return t}function Zt(e,t,i){let r=t>i?-1:1;for(;;){if(t==i)return t;let o=(t+i)/2,s=r<0?Math.ceil(o):Math.floor(o);if(s==t)return e(s)?t:i;e(s)?i=s:t=s+r}}var Kt=null;function Xt(e,t,i){let r;Kt=null;for(let o=0;o<e.length;++o){let s=e[o];if(s.from<t&&s.to>t)return o;s.to==t&&(s.from!=s.to&&"before"==i?r=o:Kt=o),s.from==t&&(s.from!=s.to&&"before"!=i?r=o:Kt=o)}return null!=r?r:Kt}var Yt=function(){let e=/[\u0590-\u05f4\u0600-\u06ff\u0700-\u08ac]/,t=/[stwN]/,i=/[LRr]/,r=/[Lb1n]/,o=/[1n]/;function s(e,t,i){this.level=e,this.from=t,this.to=i}return function(n,a){let l="ltr"==a?"L":"R";if(0==n.length||"ltr"==a&&!e.test(n))return!1;let c=n.length,d=[];for(let e=0;e<c;++e)d.push((u=n.charCodeAt(e))<=247?"bbbbbbbbbtstwsbbbbbbbbbbbbbbssstwNN%%%NNNNNN,N,N1111111111NNNNNNNLLLLLLLLLLLLLLLLLLLLLLLLLLNNNNNNLLLLLLLLLLLLLLLLLLLLLLLLLLNNNNbbbbbbsbbbbbbbbbbbbbbbbbbbbbbbbbb,N%%%%NNNNLNNNNN%%11NLNNN1LNNNNNLLLLLLLLLLLLLLLLLLLLLLLNLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLN".charAt(u):1424<=u&&u<=1524?"R":1536<=u&&u<=1785?"nnnnnnNNr%%r,rNNmmmmmmmmmmmrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrmmmmmmmmmmmmmmmmmmmmmnnnnnnnnnn%nnrrrmrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrmmmmmmmnNmmmmmmrrmmNmmmmrr1111111111".charAt(u-1536):1774<=u&&u<=2220?"r":8192<=u&&u<=8203?"w":8204==u?"b":"L");var u;for(let e=0,t=l;e<c;++e){let i=d[e];"m"==i?d[e]=t:t=i}for(let e=0,t=l;e<c;++e){let r=d[e];"1"==r&&"r"==t?d[e]="n":i.test(r)&&(t=r,"r"==r&&(d[e]="R"))}for(let e=1,t=d[0];e<c-1;++e){let i=d[e];"+"==i&&"1"==t&&"1"==d[e+1]?d[e]="1":","!=i||t!=d[e+1]||"1"!=t&&"n"!=t||(d[e]=t),t=i}for(let e=0;e<c;++e){let t=d[e];if(","==t)d[e]="N";else if("%"==t){let t;for(t=e+1;t<c&&"%"==d[t];++t);let i=e&&"!"==d[e-1]||t<c&&"1"==d[t]?"1":"N";for(let r=e;r<t;++r)d[r]=i;e=t-1}}for(let e=0,t=l;e<c;++e){let r=d[e];"L"==t&&"1"==r?d[e]="L":i.test(r)&&(t=r)}for(let e=0;e<c;++e)if(t.test(d[e])){let i;for(i=e+1;i<c&&t.test(d[i]);++i);let r="L"==(e?d[e-1]:l),o=r==("L"==(i<c?d[i]:l))?r?"L":"R":l;for(let t=e;t<i;++t)d[t]=o;e=i-1}let h,p=[];for(let e=0;e<c;)if(r.test(d[e])){let t=e;for(++e;e<c&&r.test(d[e]);++e);p.push(new s(0,t,e))}else{let t=e,i=p.length,r="rtl"==a?1:0;for(++e;e<c&&"L"!=d[e];++e);for(let n=t;n<e;)if(o.test(d[n])){t<n&&(p.splice(i,0,new s(1,t,n)),i+=r);let a=n;for(++n;n<e&&o.test(d[n]);++n);p.splice(i,0,new s(2,a,n)),i+=r,t=n}else++n;t<e&&p.splice(i,0,new s(1,t,e))}return"ltr"==a&&(1==p[0].level&&(h=n.match(/^\s+/))&&(p[0].from=h[0].length,p.unshift(new s(0,0,h[0].length))),1==Ot(p).level&&(h=n.match(/\s+$/))&&(Ot(p).to-=h[0].length,p.push(new s(0,c-h[0].length,c)))),"rtl"==a?p.reverse():p}}();function Jt(e,t){let i=e.order;return null==i&&(i=e.order=Yt(e.text,t)),i}var Qt=[],ei=function(e,t,i){if(e.addEventListener)e.addEventListener(t,i,!1);else if(e.attachEvent)e.attachEvent("on"+t,i);else{let r=e._handlers||(e._handlers={});r[t]=(r[t]||Qt).concat(i)}};function ti(e,t){return e._handlers&&e._handlers[t]||Qt}function ii(e,t,i){if(e.removeEventListener)e.removeEventListener(t,i,!1);else if(e.detachEvent)e.detachEvent("on"+t,i);else{let r=e._handlers,o=r&&r[t];if(o){let e=Pt(o,i);e>-1&&(r[t]=o.slice(0,e).concat(o.slice(e+1)))}}}function ri(e,t){let i=ti(e,t);if(!i.length)return;let r=Array.prototype.slice.call(arguments,2);for(let e=0;e<i.length;++e)i[e].apply(null,r)}function oi(e,t,i){return"string"==typeof t&&(t={type:t,preventDefault:function(){this.defaultPrevented=!0}}),ri(e,i||t.type,e,t),di(t)||t.codemirrorIgnore}function si(e){let t=e._handlers&&e._handlers.cursorActivity;if(!t)return;let i=e.curOp.cursorActivityHandlers||(e.curOp.cursorActivityHandlers=[]);for(let e=0;e<t.length;++e)-1==Pt(i,t[e])&&i.push(t[e])}function ni(e,t){return ti(e,t).length>0}function ai(e){e.prototype.on=function(e,t){ei(this,e,t)},e.prototype.off=function(e,t){ii(this,e,t)}}function li(e){e.preventDefault?e.preventDefault():e.returnValue=!1}function ci(e){e.stopPropagation?e.stopPropagation():e.cancelBubble=!0}function di(e){return null!=e.defaultPrevented?e.defaultPrevented:0==e.returnValue}function ui(e){li(e),ci(e)}function hi(e){return e.target||e.srcElement}function pi(e){let t=e.which;return null==t&&(1&e.button?t=1:2&e.button?t=3:4&e.button&&(t=2)),nt&&e.ctrlKey&&1==t&&(t=3),t}var mi,fi,gi=function(){if(Ze&&Ke<9)return!1;let e=vt("div");return"draggable"in e||"dragDrop"in e}();function vi(e){if(null==mi){let t=vt("span","​");gt(e,vt("span",[t,document.createTextNode("x")])),0!=e.firstChild.offsetHeight&&(mi=t.offsetWidth<=1&&t.offsetHeight>2&&!(Ze&&Ke<8))}let t=mi?vt("span","​"):vt("span"," ",null,"display: inline-block; width: 1px; margin-right: -1px");return t.setAttribute("cm-text",""),t}function bi(e){if(null!=fi)return fi;let t=gt(e,document.createTextNode("AخA")),i=pt(t,0,1).getBoundingClientRect(),r=pt(t,1,2).getBoundingClientRect();return ft(e),!(!i||i.left==i.right)&&(fi=r.right-i.right<3)}var _i=3!="\n\nb".split(/\n/).length?e=>{let t=0,i=[],r=e.length;for(;t<=r;){let r=e.indexOf("\n",t);-1==r&&(r=e.length);let o=e.slice(t,"\r"==e.charAt(r-1)?r-1:r),s=o.indexOf("\r");-1!=s?(i.push(o.slice(0,s)),t+=s+1):(i.push(o),t=r+1)}return i}:e=>e.split(/\r\n?|\n/),yi=window.getSelection?e=>{try{return e.selectionStart!=e.selectionEnd}catch(e){return!1}}:e=>{let t;try{t=e.ownerDocument.selection.createRange()}catch(e){}return!(!t||t.parentElement()!=e)&&0!=t.compareEndPoints("StartToEnd",t)},xi=(()=>{let e=vt("div");return"oncopy"in e||(e.setAttribute("oncopy","return;"),"function"==typeof e.oncopy)})(),wi=null;var ki={},Si={};function Ti(e,t){arguments.length>2&&(t.dependencies=Array.prototype.slice.call(arguments,2)),ki[e]=t}function Ci(e){if("string"==typeof e&&Si.hasOwnProperty(e))e=Si[e];else if(e&&"string"==typeof e.name&&Si.hasOwnProperty(e.name)){let t=Si[e.name];"string"==typeof t&&(t={name:t}),(e=Wt(t,e)).name=t.name}else{if("string"==typeof e&&/^[\w\-]+\/[\w\-]+\+xml$/.test(e))return Ci("application/xml");if("string"==typeof e&&/^[\w\-]+\/[\w\-]+\+json$/.test(e))return Ci("application/json")}return"string"==typeof e?{name:e}:e||{name:"null"}}function Mi(e,t){t=Ci(t);let i=ki[t.name];if(!i)return Mi(e,"text/plain");let r=i(e,t);if(Pi.hasOwnProperty(t.name)){let e=Pi[t.name];for(let t in e)e.hasOwnProperty(t)&&(r.hasOwnProperty(t)&&(r["_"+t]=r[t]),r[t]=e[t])}if(r.name=t.name,t.helperType&&(r.helperType=t.helperType),t.modeProps)for(let e in t.modeProps)r[e]=t.modeProps[e];return r}var Pi={};function $i(e,t){Tt(t,Pi.hasOwnProperty(e)?Pi[e]:Pi[e]={})}function Li(e,t){if(!0===t)return t;if(e.copyState)return e.copyState(t);let i={};for(let e in t){let r=t[e];r instanceof Array&&(r=r.concat([])),i[e]=r}return i}function Ei(e,t){let i;for(;e.innerMode&&(i=e.innerMode(t),i&&i.mode!=e);)t=i.state,e=i.mode;return i||{mode:e,state:t}}function Ri(e,t,i){return!e.startState||e.startState(t,i)}var Ai=class{constructor(e,t,i){this.pos=this.start=0,this.string=e,this.tabSize=t||8,this.lastColumnPos=this.lastColumnValue=0,this.lineStart=0,this.lineOracle=i}eol(){return this.pos>=this.string.length}sol(){return this.pos==this.lineStart}peek(){return this.string.charAt(this.pos)||void 0}next(){if(this.pos<this.string.length)return this.string.charAt(this.pos++)}eat(e){let t,i=this.string.charAt(this.pos);if(t="string"==typeof e?i==e:i&&(e.test?e.test(i):e(i)),t)return++this.pos,i}eatWhile(e){let t=this.pos;for(;this.eat(e););return this.pos>t}eatSpace(){let e=this.pos;for(;/[\s\u00a0]/.test(this.string.charAt(this.pos));)++this.pos;return this.pos>e}skipToEnd(){this.pos=this.string.length}skipTo(e){let t=this.string.indexOf(e,this.pos);if(t>-1)return this.pos=t,!0}backUp(e){this.pos-=e}column(){return this.lastColumnPos<this.start&&(this.lastColumnValue=Ct(this.string,this.start,this.tabSize,this.lastColumnPos,this.lastColumnValue),this.lastColumnPos=this.start),this.lastColumnValue-(this.lineStart?Ct(this.string,this.lineStart,this.tabSize):0)}indentation(){return Ct(this.string,null,this.tabSize)-(this.lineStart?Ct(this.string,this.lineStart,this.tabSize):0)}match(e,t,i){if("string"!=typeof e){let i=this.string.slice(this.pos).match(e);return i&&i.index>0?null:(i&&!1!==t&&(this.pos+=i[0].length),i)}{let r=e=>i?e.toLowerCase():e;if(r(this.string.substr(this.pos,e.length))==r(e))return!1!==t&&(this.pos+=e.length),!0}}current(){return this.string.slice(this.start,this.pos)}hideFirstChars(e,t){this.lineStart+=e;try{return t()}finally{this.lineStart-=e}}lookAhead(e){let t=this.lineOracle;return t&&t.lookAhead(e)}baseToken(){let e=this.lineOracle;return e&&e.baseToken(this.pos)}};function Ni(e,t){if((t-=e.first)<0||t>=e.size)throw new Error("There is no line "+(t+e.first)+" in the document.");let i=e;for(;!i.lines;)for(let e=0;;++e){let r=i.children[e],o=r.chunkSize();if(t<o){i=r;break}t-=o}return i.lines[t]}function Ii(e,t,i){let r=[],o=t.line;return e.iter(t.line,i.line+1,(e=>{let s=e.text;o==i.line&&(s=s.slice(0,i.ch)),o==t.line&&(s=s.slice(t.ch)),r.push(s),++o})),r}function Di(e,t,i){let r=[];return e.iter(t,i,(e=>{r.push(e.text)})),r}function Oi(e,t){let i=t-e.height;if(i)for(let t=e;t;t=t.parent)t.height+=i}function Fi(e){if(null==e.parent)return null;let t=e.parent,i=Pt(t.lines,e);for(let e=t.parent;e;t=e,e=e.parent)for(let r=0;e.children[r]!=t;++r)i+=e.children[r].chunkSize();return i+t.first}function zi(e,t){let i=e.first;e:do{for(let r=0;r<e.children.length;++r){let o=e.children[r],s=o.height;if(t<s){e=o;continue e}t-=s,i+=o.chunkSize()}return i}while(!e.lines);let r=0;for(;r<e.lines.length;++r){let i=e.lines[r].height;if(t<i)break;t-=i}return i+r}function Wi(e,t){return t>=e.first&&t<e.first+e.size}function Bi(e,t){return String(e.lineNumberFormatter(t+e.firstLineNumber))}function ji(e,t,i=null){if(!(this instanceof ji))return new ji(e,t,i);this.line=e,this.ch=t,this.sticky=i}function Hi(e,t){return e.line-t.line||e.ch-t.ch}function Ui(e,t){return e.sticky==t.sticky&&0==Hi(e,t)}function Vi(e){return ji(e.line,e.ch)}function Gi(e,t){return Hi(e,t)<0?t:e}function qi(e,t){return Hi(e,t)<0?e:t}function Zi(e,t){return Math.max(e.first,Math.min(t,e.first+e.size-1))}function Ki(e,t){if(t.line<e.first)return ji(e.first,0);let i=e.first+e.size-1;return t.line>i?ji(i,Ni(e,i).text.length):function(e,t){let i=e.ch;return null==i||i>t?ji(e.line,t):i<0?ji(e.line,0):e}(t,Ni(e,t.line).text.length)}function Xi(e,t){let i=[];for(let r=0;r<t.length;r++)i[r]=Ki(e,t[r]);return i}var Yi=class{constructor(e,t){this.state=e,this.lookAhead=t}},Ji=class{constructor(e,t,i,r){this.state=t,this.doc=e,this.line=i,this.maxLookAhead=r||0,this.baseTokens=null,this.baseTokenPos=1}lookAhead(e){let t=this.doc.getLine(this.line+e);return null!=t&&e>this.maxLookAhead&&(this.maxLookAhead=e),t}baseToken(e){if(!this.baseTokens)return null;for(;this.baseTokens[this.baseTokenPos]<=e;)this.baseTokenPos+=2;let t=this.baseTokens[this.baseTokenPos+1];return{type:t&&t.replace(/( |^)overlay .*/,""),size:this.baseTokens[this.baseTokenPos]-e}}nextLine(){this.line++,this.maxLookAhead>0&&this.maxLookAhead--}static fromSaved(e,t,i){return t instanceof Yi?new Ji(e,Li(e.mode,t.state),i,t.lookAhead):new Ji(e,Li(e.mode,t),i)}save(e){let t=!1!==e?Li(this.doc.mode,this.state):this.state;return this.maxLookAhead>0?new Yi(t,this.maxLookAhead):t}};function Qi(e,t,i,r){let o=[e.state.modeGen],s={};lr(e,t.text,e.doc.mode,i,((e,t)=>o.push(e,t)),s,r);let n=i.state;for(let r=0;r<e.state.overlays.length;++r){i.baseTokens=o;let a=e.state.overlays[r],l=1,c=0;i.state=!0,lr(e,t.text,a.mode,i,((e,t)=>{let i=l;for(;c<e;){let t=o[l];t>e&&o.splice(l,1,e,o[l+1],t),l+=2,c=Math.min(e,t)}if(t)if(a.opaque)o.splice(i,l-i,e,"overlay "+t),l=i+2;else for(;i<l;i+=2){let e=o[i+1];o[i+1]=(e?e+" ":"")+"overlay "+t}}),s),i.state=n,i.baseTokens=null,i.baseTokenPos=1}return{styles:o,classes:s.bgClass||s.textClass?s:null}}function er(e,t,i){if(!t.styles||t.styles[0]!=e.state.modeGen){let r=tr(e,Fi(t)),o=t.text.length>e.options.maxHighlightLength&&Li(e.doc.mode,r.state),s=Qi(e,t,r);o&&(r.state=o),t.stateAfter=r.save(!o),t.styles=s.styles,s.classes?t.styleClasses=s.classes:t.styleClasses&&(t.styleClasses=null),i===e.doc.highlightFrontier&&(e.doc.modeFrontier=Math.max(e.doc.modeFrontier,++e.doc.highlightFrontier))}return t.styles}function tr(e,t,i){let r=e.doc,o=e.display;if(!r.mode.startState)return new Ji(r,!0,t);let s=function(e,t,i){let r,o,s=e.doc,n=i?-1:t-(e.doc.mode.innerMode?1e3:100);for(let a=t;a>n;--a){if(a<=s.first)return s.first;let t=Ni(s,a-1),n=t.stateAfter;if(n&&(!i||a+(n instanceof Yi?n.lookAhead:0)<=s.modeFrontier))return a;let l=Ct(t.text,null,e.options.tabSize);(null==o||r>l)&&(o=a-1,r=l)}return o}(e,t,i),n=s>r.first&&Ni(r,s-1).stateAfter,a=n?Ji.fromSaved(r,n,s):new Ji(r,Ri(r.mode),s);return r.iter(s,t,(i=>{ir(e,i.text,a);let r=a.line;i.stateAfter=r==t-1||r%5==0||r>=o.viewFrom&&r<o.viewTo?a.save():null,a.nextLine()})),i&&(r.modeFrontier=a.line),a}function ir(e,t,i,r){let o=e.doc.mode,s=new Ai(t,e.options.tabSize,i);for(s.start=s.pos=r||0,""==t&&rr(o,i.state);!s.eol();)or(o,s,i.state),s.start=s.pos}function rr(e,t){if(e.blankLine)return e.blankLine(t);if(!e.innerMode)return;let i=Ei(e,t);return i.mode.blankLine?i.mode.blankLine(i.state):void 0}function or(e,t,i,r){for(let o=0;o<10;o++){r&&(r[0]=Ei(e,i).mode);let o=e.token(t,i);if(t.pos>t.start)return o}throw new Error("Mode "+e.name+" failed to advance stream.")}var sr=class{constructor(e,t,i){this.start=e.start,this.end=e.pos,this.string=e.current(),this.type=t||null,this.state=i}};function nr(e,t,i,r){let o,s,n=e.doc,a=n.mode,l=Ni(n,(t=Ki(n,t)).line),c=tr(e,t.line,i),d=new Ai(l.text,e.options.tabSize,c);for(r&&(s=[]);(r||d.pos<t.ch)&&!d.eol();)d.start=d.pos,o=or(a,d,c.state),r&&s.push(new sr(d,o,Li(n.mode,c.state)));return r?s:new sr(d,o,c.state)}function ar(e,t){if(e)for(;;){let i=e.match(/(?:^|\s+)line-(background-)?(\S+)/);if(!i)break;e=e.slice(0,i.index)+e.slice(i.index+i[0].length);let r=i[1]?"bgClass":"textClass";null==t[r]?t[r]=i[2]:new RegExp("(?:^|\\s)"+i[2]+"(?:$|\\s)").test(t[r])||(t[r]+=" "+i[2])}return e}function lr(e,t,i,r,o,s,n){let a=i.flattenSpans;null==a&&(a=e.options.flattenSpans);let l,c=0,d=null,u=new Ai(t,e.options.tabSize,r),h=e.options.addModeClass&&[null];for(""==t&&ar(rr(i,r.state),s);!u.eol();){if(u.pos>e.options.maxHighlightLength?(a=!1,n&&ir(e,t,r,u.pos),u.pos=t.length,l=null):l=ar(or(i,u,r.state,h),s),h){let e=h[0].name;e&&(l="m-"+(l?e+" "+l:e))}if(!a||d!=l){for(;c<u.start;)c=Math.min(u.start,c+5e3),o(c,d);d=l}u.start=u.pos}for(;c<u.pos;){let e=Math.min(u.pos,c+5e3);o(e,d),c=e}}var cr=!1,dr=!1;function ur(e,t,i){this.marker=e,this.from=t,this.to=i}function hr(e,t){if(e)for(let i=0;i<e.length;++i){let r=e[i];if(r.marker==t)return r}}function pr(e,t){let i;for(let r=0;r<e.length;++r)e[r]!=t&&(i||(i=[])).push(e[r]);return i}function mr(e,t){if(t.full)return null;let i=Wi(e,t.from.line)&&Ni(e,t.from.line).markedSpans,r=Wi(e,t.to.line)&&Ni(e,t.to.line).markedSpans;if(!i&&!r)return null;let o=t.from.ch,s=t.to.ch,n=0==Hi(t.from,t.to),a=function(e,t,i){let r;if(e)for(let o=0;o<e.length;++o){let s=e[o],n=s.marker;if(null==s.from||(n.inclusiveLeft?s.from<=t:s.from<t)||s.from==t&&"bookmark"==n.type&&(!i||!s.marker.insertLeft)){let e=null==s.to||(n.inclusiveRight?s.to>=t:s.to>t);(r||(r=[])).push(new ur(n,s.from,e?null:s.to))}}return r}(i,o,n),l=function(e,t,i){let r;if(e)for(let o=0;o<e.length;++o){let s=e[o],n=s.marker;if(null==s.to||(n.inclusiveRight?s.to>=t:s.to>t)||s.from==t&&"bookmark"==n.type&&(!i||s.marker.insertLeft)){let e=null==s.from||(n.inclusiveLeft?s.from<=t:s.from<t);(r||(r=[])).push(new ur(n,e?null:s.from-t,null==s.to?null:s.to-t))}}return r}(r,s,n),c=1==t.text.length,d=Ot(t.text).length+(c?o:0);if(a)for(let e=0;e<a.length;++e){let t=a[e];if(null==t.to){let e=hr(l,t.marker);e?c&&(t.to=null==e.to?null:e.to+d):t.to=o}}if(l)for(let e=0;e<l.length;++e){let t=l[e];if(null!=t.to&&(t.to+=d),null==t.from){hr(a,t.marker)||(t.from=d,c&&(a||(a=[])).push(t))}else t.from+=d,c&&(a||(a=[])).push(t)}a&&(a=fr(a)),l&&l!=a&&(l=fr(l));let u=[a];if(!c){let e,i=t.text.length-2;if(i>0&&a)for(let t=0;t<a.length;++t)null==a[t].to&&(e||(e=[])).push(new ur(a[t].marker,null,null));for(let t=0;t<i;++t)u.push(e);u.push(l)}return u}function fr(e){for(let t=0;t<e.length;++t){let i=e[t];null!=i.from&&i.from==i.to&&!1!==i.marker.clearWhenEmpty&&e.splice(t--,1)}return e.length?e:null}function gr(e){let t=e.markedSpans;if(t){for(let i=0;i<t.length;++i)t[i].marker.detachLine(e);e.markedSpans=null}}function vr(e,t){if(t){for(let i=0;i<t.length;++i)t[i].marker.attachLine(e);e.markedSpans=t}}function br(e){return e.inclusiveLeft?-1:0}function _r(e){return e.inclusiveRight?1:0}function yr(e,t){let i=e.lines.length-t.lines.length;if(0!=i)return i;let r=e.find(),o=t.find(),s=Hi(r.from,o.from)||br(e)-br(t);if(s)return-s;let n=Hi(r.to,o.to)||_r(e)-_r(t);return n||t.id-e.id}function xr(e,t){let i,r=dr&&e.markedSpans;if(r)for(let e,o=0;o<r.length;++o)e=r[o],e.marker.collapsed&&null==(t?e.from:e.to)&&(!i||yr(i,e.marker)<0)&&(i=e.marker);return i}function wr(e){return xr(e,!0)}function kr(e){return xr(e,!1)}function Sr(e,t){let i,r=dr&&e.markedSpans;if(r)for(let e=0;e<r.length;++e){let o=r[e];o.marker.collapsed&&(null==o.from||o.from<t)&&(null==o.to||o.to>t)&&(!i||yr(i,o.marker)<0)&&(i=o.marker)}return i}function Tr(e,t,i,r,o){let s=Ni(e,t),n=dr&&s.markedSpans;if(n)for(let e=0;e<n.length;++e){let t=n[e];if(!t.marker.collapsed)continue;let s=t.marker.find(0),a=Hi(s.from,i)||br(t.marker)-br(o),l=Hi(s.to,r)||_r(t.marker)-_r(o);if(!(a>=0&&l<=0||a<=0&&l>=0)&&(a<=0&&(t.marker.inclusiveRight&&o.inclusiveLeft?Hi(s.to,i)>=0:Hi(s.to,i)>0)||a>=0&&(t.marker.inclusiveRight&&o.inclusiveLeft?Hi(s.from,r)<=0:Hi(s.from,r)<0)))return!0}}function Cr(e){let t;for(;t=wr(e);)e=t.find(-1,!0).line;return e}function Mr(e,t){let i=Ni(e,t),r=Cr(i);return i==r?t:Fi(r)}function Pr(e,t){if(t>e.lastLine())return t;let i,r=Ni(e,t);if(!$r(e,r))return t;for(;i=kr(r);)r=i.find(1,!0).line;return Fi(r)+1}function $r(e,t){let i=dr&&t.markedSpans;if(i)for(let r,o=0;o<i.length;++o)if(r=i[o],r.marker.collapsed){if(null==r.from)return!0;if(!r.marker.widgetNode&&0==r.from&&r.marker.inclusiveLeft&&Lr(e,t,r))return!0}}function Lr(e,t,i){if(null==i.to){let t=i.marker.find(1,!0);return Lr(e,t.line,hr(t.line.markedSpans,i.marker))}if(i.marker.inclusiveRight&&i.to==t.text.length)return!0;for(let r,o=0;o<t.markedSpans.length;++o)if(r=t.markedSpans[o],r.marker.collapsed&&!r.marker.widgetNode&&r.from==i.to&&(null==r.to||r.to!=i.from)&&(r.marker.inclusiveLeft||i.marker.inclusiveRight)&&Lr(e,t,r))return!0}function Er(e){let t=0,i=(e=Cr(e)).parent;for(let r=0;r<i.lines.length;++r){let o=i.lines[r];if(o==e)break;t+=o.height}for(let e=i.parent;e;i=e,e=i.parent)for(let r=0;r<e.children.length;++r){let o=e.children[r];if(o==i)break;t+=o.height}return t}function Rr(e){if(0==e.height)return 0;let t,i=e.text.length,r=e;for(;t=wr(r);){let e=t.find(0,!0);r=e.from.line,i+=e.from.ch-e.to.ch}for(r=e;t=kr(r);){let e=t.find(0,!0);i-=r.text.length-e.from.ch,r=e.to.line,i+=r.text.length-e.to.ch}return i}function Ar(e){let t=e.display,i=e.doc;t.maxLine=Ni(i,i.first),t.maxLineLength=Rr(t.maxLine),t.maxLineChanged=!0,i.iter((e=>{let i=Rr(e);i>t.maxLineLength&&(t.maxLineLength=i,t.maxLine=e)}))}var Nr=class{constructor(e,t,i){this.text=e,vr(this,t),this.height=i?i(this):1}lineNo(){return Fi(this)}};function Ir(e){e.parent=null,gr(e)}ai(Nr);var Dr={},Or={};function Fr(e,t){if(!e||/^\s*$/.test(e))return null;let i=t.addModeClass?Or:Dr;return i[e]||(i[e]=e.replace(/\S+/g,"cm-$&"))}function zr(e,t){let i=bt("span",null,null,Xe?"padding-right: .1px":null),r={pre:bt("pre",[i],"CodeMirror-line"),content:i,col:0,pos:0,cm:e,trailingSpace:!1,splitSpaces:e.getOption("lineWrapping")};t.measure={};for(let i=0;i<=(t.rest?t.rest.length:0);i++){let o,s=i?t.rest[i-1]:t.line;r.pos=0,r.addToken=Br,bi(e.display.measure)&&(o=Jt(s,e.doc.direction))&&(r.addToken=jr(r.addToken,o)),r.map=[],Ur(s,r,er(e,s,t!=e.display.externalMeasured&&Fi(s))),s.styleClasses&&(s.styleClasses.bgClass&&(r.bgClass=wt(s.styleClasses.bgClass,r.bgClass||"")),s.styleClasses.textClass&&(r.textClass=wt(s.styleClasses.textClass,r.textClass||""))),0==r.map.length&&r.map.push(0,0,r.content.appendChild(vi(e.display.measure))),0==i?(t.measure.map=r.map,t.measure.cache={}):((t.measure.maps||(t.measure.maps=[])).push(r.map),(t.measure.caches||(t.measure.caches=[])).push({}))}if(Xe){let e=r.content.lastChild;(/\bcm-tab\b/.test(e.className)||e.querySelector&&e.querySelector(".cm-tab"))&&(r.content.className="cm-tab-wrap-hack")}return ri(e,"renderLine",e,t.line,r.pre),r.pre.className&&(r.textClass=wt(r.pre.className,r.textClass||"")),r}function Wr(e){let t=vt("span","•","cm-invalidchar");return t.title="\\u"+e.charCodeAt(0).toString(16),t.setAttribute("aria-label",t.title),t}function Br(e,t,i,r,o,s,n){if(!t)return;let a,l=e.splitSpaces?function(e,t){if(e.length>1&&!/  /.test(e))return e;let i=t,r="";for(let t=0;t<e.length;t++){let o=e.charAt(t);" "!=o||!i||t!=e.length-1&&32!=e.charCodeAt(t+1)||(o=" "),r+=o,i=" "==o}return r}(t,e.trailingSpace):t,c=e.cm.state.specialChars,d=!1;if(c.test(t)){a=document.createDocumentFragment();let i=0;for(;;){c.lastIndex=i;let r,o=c.exec(t),s=o?o.index-i:t.length-i;if(s){let t=document.createTextNode(l.slice(i,i+s));Ze&&Ke<9?a.appendChild(vt("span",[t])):a.appendChild(t),e.map.push(e.pos,e.pos+s,t),e.col+=s,e.pos+=s}if(!o)break;if(i+=s+1,"\t"==o[0]){let t=e.cm.options.tabSize,i=t-e.col%t;r=a.appendChild(vt("span",Dt(i),"cm-tab")),r.setAttribute("role","presentation"),r.setAttribute("cm-text","\t"),e.col+=i}else"\r"==o[0]||"\n"==o[0]?(r=a.appendChild(vt("span","\r"==o[0]?"␍":"␤","cm-invalidchar")),r.setAttribute("cm-text",o[0]),e.col+=1):(r=e.cm.options.specialCharPlaceholder(o[0]),r.setAttribute("cm-text",o[0]),Ze&&Ke<9?a.appendChild(vt("span",[r])):a.appendChild(r),e.col+=1);e.map.push(e.pos,e.pos+1,r),e.pos++}}else e.col+=t.length,a=document.createTextNode(l),e.map.push(e.pos,e.pos+t.length,a),Ze&&Ke<9&&(d=!0),e.pos+=t.length;if(e.trailingSpace=32==l.charCodeAt(t.length-1),i||r||o||d||s||n){let t=i||"";r&&(t+=r),o&&(t+=o);let l=vt("span",[a],t,s);if(n)for(let e in n)n.hasOwnProperty(e)&&"style"!=e&&"class"!=e&&l.setAttribute(e,n[e]);return e.content.appendChild(l)}e.content.appendChild(a)}function jr(e,t){return(i,r,o,s,n,a,l)=>{o=o?o+" cm-force-border":"cm-force-border";let c=i.pos,d=c+r.length;for(;;){let u;for(let e=0;e<t.length&&(u=t[e],!(u.to>c&&u.from<=c));e++);if(u.to>=d)return e(i,r,o,s,n,a,l);e(i,r.slice(0,u.to-c),o,s,null,a,l),s=null,r=r.slice(u.to-c),c=u.to}}}function Hr(e,t,i,r){let o=!r&&i.widgetNode;o&&e.map.push(e.pos,e.pos+t,o),!r&&e.cm.display.input.needsContentAttribute&&(o||(o=e.content.appendChild(document.createElement("span"))),o.setAttribute("cm-marker",i.id)),o&&(e.cm.display.input.setUneditable(o),e.content.appendChild(o)),e.pos+=t,e.trailingSpace=!1}function Ur(e,t,i){let r=e.markedSpans,o=e.text,s=0;if(!r){for(let e=1;e<i.length;e+=2)t.addToken(t,o.slice(s,s=i[e]),Fr(i[e+1],t.cm.options));return}let n,a,l,c,d,u,h,p=o.length,m=0,f=1,g="",v=0;for(;;){if(v==m){l=c=d=a="",h=null,u=null,v=1/0;let e,i=[];for(let t=0;t<r.length;++t){let o=r[t],s=o.marker;if("bookmark"==s.type&&o.from==m&&s.widgetNode)i.push(s);else if(o.from<=m&&(null==o.to||o.to>m||s.collapsed&&o.to==m&&o.from==m)){if(null!=o.to&&o.to!=m&&v>o.to&&(v=o.to,c=""),s.className&&(l+=" "+s.className),s.css&&(a=(a?a+";":"")+s.css),s.startStyle&&o.from==m&&(d+=" "+s.startStyle),s.endStyle&&o.to==v&&(e||(e=[])).push(s.endStyle,o.to),s.title&&((h||(h={})).title=s.title),s.attributes)for(let e in s.attributes)(h||(h={}))[e]=s.attributes[e];s.collapsed&&(!u||yr(u.marker,s)<0)&&(u=o)}else o.from>m&&v>o.from&&(v=o.from)}if(e)for(let t=0;t<e.length;t+=2)e[t+1]==v&&(c+=" "+e[t]);if(!u||u.from==m)for(let e=0;e<i.length;++e)Hr(t,0,i[e]);if(u&&(u.from||0)==m){if(Hr(t,(null==u.to?p+1:u.to)-m,u.marker,null==u.from),null==u.to)return;u.to==m&&(u=!1)}}if(m>=p)break;let e=Math.min(p,v);for(;;){if(g){let i=m+g.length;if(!u){let r=i>e?g.slice(0,e-m):g;t.addToken(t,r,n?n+l:l,d,m+r.length==v?c:"",a,h)}if(i>=e){g=g.slice(e-m),m=e;break}m=i,d=""}g=o.slice(s,s=i[f++]),n=Fr(i[f++],t.cm.options)}}}function Vr(e,t,i){this.line=t,this.rest=function(e){let t,i;for(;t=kr(e);)e=t.find(1,!0).line,(i||(i=[])).push(e);return i}(t),this.size=this.rest?Fi(Ot(this.rest))-i+1:1,this.node=this.text=null,this.hidden=$r(e,t)}function Gr(e,t,i){let r,o=[];for(let s=t;s<i;s=r){let t=new Vr(e.doc,Ni(e.doc,s),s);r=s+t.size,o.push(t)}return o}var qr=null;var Zr=null;function Kr(e,t){let i=ti(e,t);if(!i.length)return;let r,o=Array.prototype.slice.call(arguments,2);qr?r=qr.delayedCallbacks:Zr?r=Zr:(r=Zr=[],setTimeout(Xr,0));for(let e=0;e<i.length;++e)r.push((()=>i[e].apply(null,o)))}function Xr(){let e=Zr;Zr=null;for(let t=0;t<e.length;++t)e[t]()}function Yr(e,t,i,r){for(let o=0;o<t.changes.length;o++){let s=t.changes[o];"text"==s?eo(e,t):"gutter"==s?io(e,t,i,r):"class"==s?to(e,t):"widget"==s&&ro(e,t,r)}t.changes=null}function Jr(e){return e.node==e.text&&(e.node=vt("div",null,null,"position: relative"),e.text.parentNode&&e.text.parentNode.replaceChild(e.node,e.text),e.node.appendChild(e.text),Ze&&Ke<8&&(e.node.style.zIndex=2)),e.node}function Qr(e,t){let i=e.display.externalMeasured;return i&&i.line==t.line?(e.display.externalMeasured=null,t.measure=i.measure,i.built):zr(e,t)}function eo(e,t){let i=t.text.className,r=Qr(e,t);t.text==t.node&&(t.node=r.pre),t.text.parentNode.replaceChild(r.pre,t.text),t.text=r.pre,r.bgClass!=t.bgClass||r.textClass!=t.textClass?(t.bgClass=r.bgClass,t.textClass=r.textClass,to(e,t)):i&&(t.text.className=i)}function to(e,t){!function(e,t){let i=t.bgClass?t.bgClass+" "+(t.line.bgClass||""):t.line.bgClass;if(i&&(i+=" CodeMirror-linebackground"),t.background)i?t.background.className=i:(t.background.parentNode.removeChild(t.background),t.background=null);else if(i){let r=Jr(t);t.background=r.insertBefore(vt("div",null,i),r.firstChild),e.display.input.setUneditable(t.background)}}(e,t),t.line.wrapClass?Jr(t).className=t.line.wrapClass:t.node!=t.text&&(t.node.className="");let i=t.textClass?t.textClass+" "+(t.line.textClass||""):t.line.textClass;t.text.className=i||""}function io(e,t,i,r){if(t.gutter&&(t.node.removeChild(t.gutter),t.gutter=null),t.gutterBackground&&(t.node.removeChild(t.gutterBackground),t.gutterBackground=null),t.line.gutterClass){let i=Jr(t);t.gutterBackground=vt("div",null,"CodeMirror-gutter-background "+t.line.gutterClass,`left: ${e.options.fixedGutter?r.fixedPos:-r.gutterTotalWidth}px; width: ${r.gutterTotalWidth}px`),e.display.input.setUneditable(t.gutterBackground),i.insertBefore(t.gutterBackground,t.text)}let o=t.line.gutterMarkers;if(e.options.lineNumbers||o){let s=Jr(t),n=t.gutter=vt("div",null,"CodeMirror-gutter-wrapper",`left: ${e.options.fixedGutter?r.fixedPos:-r.gutterTotalWidth}px`);if(n.setAttribute("aria-hidden","true"),e.display.input.setUneditable(n),s.insertBefore(n,t.text),t.line.gutterClass&&(n.className+=" "+t.line.gutterClass),!e.options.lineNumbers||o&&o["CodeMirror-linenumbers"]||(t.lineNumber=n.appendChild(vt("div",Bi(e.options,i),"CodeMirror-linenumber CodeMirror-gutter-elt",`left: ${r.gutterLeft["CodeMirror-linenumbers"]}px; width: ${e.display.lineNumInnerWidth}px`))),o)for(let t=0;t<e.display.gutterSpecs.length;++t){let i=e.display.gutterSpecs[t].className,s=o.hasOwnProperty(i)&&o[i];s&&n.appendChild(vt("div",[s],"CodeMirror-gutter-elt",`left: ${r.gutterLeft[i]}px; width: ${r.gutterWidth[i]}px`))}}}function ro(e,t,i){t.alignable&&(t.alignable=null);let r=ht("CodeMirror-linewidget");for(let e,i=t.node.firstChild;i;i=e)e=i.nextSibling,r.test(i.className)&&t.node.removeChild(i);so(e,t,i)}function oo(e,t,i,r){let o=Qr(e,t);return t.text=t.node=o.pre,o.bgClass&&(t.bgClass=o.bgClass),o.textClass&&(t.textClass=o.textClass),to(e,t),io(e,t,i,r),so(e,t,r),t.node}function so(e,t,i){if(no(e,t.line,t,i,!0),t.rest)for(let r=0;r<t.rest.length;r++)no(e,t.rest[r],t,i,!1)}function no(e,t,i,r,o){if(!t.widgets)return;let s=Jr(i);for(let n=0,a=t.widgets;n<a.length;++n){let t=a[n],l=vt("div",[t.node],"CodeMirror-linewidget"+(t.className?" "+t.className:""));t.handleMouseEvents||l.setAttribute("cm-ignore-events","true"),ao(t,l,i,r),e.display.input.setUneditable(l),o&&t.above?s.insertBefore(l,i.gutter||i.text):s.appendChild(l),Kr(t,"redraw")}}function ao(e,t,i,r){if(e.noHScroll){(i.alignable||(i.alignable=[])).push(t);let o=r.wrapperWidth;t.style.left=r.fixedPos+"px",e.coverGutter||(o-=r.gutterTotalWidth,t.style.paddingLeft=r.gutterTotalWidth+"px"),t.style.width=o+"px"}e.coverGutter&&(t.style.zIndex=5,t.style.position="relative",e.noHScroll||(t.style.marginLeft=-r.gutterTotalWidth+"px"))}function lo(e){if(null!=e.height)return e.height;let t=e.doc.cm;if(!t)return 0;if(!_t(document.body,e.node)){let i="position: relative;";e.coverGutter&&(i+="margin-left: -"+t.display.gutters.offsetWidth+"px;"),e.noHScroll&&(i+="width: "+t.display.wrapper.clientWidth+"px;"),gt(t.display.measure,vt("div",[e.node],null,i))}return e.height=e.node.parentNode.offsetHeight}function co(e,t){for(let i=hi(t);i!=e.wrapper;i=i.parentNode)if(!i||1==i.nodeType&&"true"==i.getAttribute("cm-ignore-events")||i.parentNode==e.sizer&&i!=e.mover)return!0}function uo(e){return e.lineSpace.offsetTop}function ho(e){return e.mover.offsetHeight-e.lineSpace.offsetHeight}function po(e){if(e.cachedPaddingH)return e.cachedPaddingH;let t=gt(e.measure,vt("pre","x","CodeMirror-line-like")),i=window.getComputedStyle?window.getComputedStyle(t):t.currentStyle,r={left:parseInt(i.paddingLeft),right:parseInt(i.paddingRight)};return isNaN(r.left)||isNaN(r.right)||(e.cachedPaddingH=r),r}function mo(e){return $t-e.display.nativeBarWidth}function fo(e){return e.display.scroller.clientWidth-mo(e)-e.display.barWidth}function go(e){return e.display.scroller.clientHeight-mo(e)-e.display.barHeight}function vo(e,t,i){if(e.line==t)return{map:e.measure.map,cache:e.measure.cache};for(let i=0;i<e.rest.length;i++)if(e.rest[i]==t)return{map:e.measure.maps[i],cache:e.measure.caches[i]};for(let t=0;t<e.rest.length;t++)if(Fi(e.rest[t])>i)return{map:e.measure.maps[t],cache:e.measure.caches[t],before:!0}}function bo(e,t,i,r){return xo(e,yo(e,t),i,r)}function _o(e,t){if(t>=e.display.viewFrom&&t<e.display.viewTo)return e.display.view[Jo(e,t)];let i=e.display.externalMeasured;return i&&t>=i.lineN&&t<i.lineN+i.size?i:void 0}function yo(e,t){let i=Fi(t),r=_o(e,i);r&&!r.text?r=null:r&&r.changes&&(Yr(e,r,i,qo(e)),e.curOp.forceUpdate=!0),r||(r=function(e,t){let i=Fi(t=Cr(t)),r=e.display.externalMeasured=new Vr(e.doc,t,i);r.lineN=i;let o=r.built=zr(e,r);return r.text=o.pre,gt(e.display.lineMeasure,o.pre),r}(e,t));let o=vo(r,t,i);return{line:t,view:r,rect:null,map:o.map,cache:o.cache,before:o.before,hasHeights:!1}}function xo(e,t,i,r,o){t.before&&(i=-1);let s,n=i+(r||"");return t.cache.hasOwnProperty(n)?s=t.cache[n]:(t.rect||(t.rect=t.view.text.getBoundingClientRect()),t.hasHeights||(!function(e,t,i){let r=e.options.lineWrapping,o=r&&fo(e);if(!t.measure.heights||r&&t.measure.width!=o){let e=t.measure.heights=[];if(r){t.measure.width=o;let r=t.text.firstChild.getClientRects();for(let t=0;t<r.length-1;t++){let o=r[t],s=r[t+1];Math.abs(o.bottom-s.bottom)>2&&e.push((o.bottom+s.top)/2-i.top)}}e.push(i.bottom-i.top)}}(e,t.view,t.rect),t.hasHeights=!0),s=function(e,t,i,r){let o,s=So(t.map,i,r),n=s.node,a=s.start,l=s.end,c=s.collapse;if(3==n.nodeType){for(let e=0;e<4;e++){for(;a&&Gt(t.line.text.charAt(s.coverStart+a));)--a;for(;s.coverStart+l<s.coverEnd&&Gt(t.line.text.charAt(s.coverStart+l));)++l;if(o=Ze&&Ke<9&&0==a&&l==s.coverEnd-s.coverStart?n.parentNode.getBoundingClientRect():To(pt(n,a,l).getClientRects(),r),o.left||o.right||0==a)break;l=a,a-=1,c="right"}Ze&&Ke<11&&(o=function(e,t){if(!window.screen||null==screen.logicalXDPI||screen.logicalXDPI==screen.deviceXDPI||!function(e){if(null!=wi)return wi;let t=gt(e,vt("span","x")),i=t.getBoundingClientRect(),r=pt(t,0,1).getBoundingClientRect();return wi=Math.abs(i.left-r.left)>1}(e))return t;let i=screen.logicalXDPI/screen.deviceXDPI,r=screen.logicalYDPI/screen.deviceYDPI;return{left:t.left*i,right:t.right*i,top:t.top*r,bottom:t.bottom*r}}(e.display.measure,o))}else{let t;a>0&&(c=r="right"),o=e.options.lineWrapping&&(t=n.getClientRects()).length>1?t["right"==r?t.length-1:0]:n.getBoundingClientRect()}if(Ze&&Ke<9&&!a&&(!o||!o.left&&!o.right)){let t=n.parentNode.getClientRects()[0];o=t?{left:t.left,right:t.left+Go(e.display),top:t.top,bottom:t.bottom}:ko}let d=o.top-t.rect.top,u=o.bottom-t.rect.top,h=(d+u)/2,p=t.view.measure.heights,m=0;for(;m<p.length-1&&!(h<p[m]);m++);let f=m?p[m-1]:0,g=p[m],v={left:("right"==c?o.right:o.left)-t.rect.left,right:("left"==c?o.left:o.right)-t.rect.left,top:f,bottom:g};o.left||o.right||(v.bogus=!0);e.options.singleCursorHeightPerLine||(v.rtop=d,v.rbottom=u);return v}(e,t,i,r),s.bogus||(t.cache[n]=s)),{left:s.left,right:s.right,top:o?s.rtop:s.top,bottom:o?s.rbottom:s.bottom}}var wo,ko={left:0,right:0,top:0,bottom:0};function So(e,t,i){let r,o,s,n,a,l;for(let c=0;c<e.length;c+=3)if(a=e[c],l=e[c+1],t<a?(o=0,s=1,n="left"):t<l?(o=t-a,s=o+1):(c==e.length-3||t==l&&e[c+3]>t)&&(s=l-a,o=s-1,t>=l&&(n="right")),null!=o){if(r=e[c+2],a==l&&i==(r.insertLeft?"left":"right")&&(n=i),"left"==i&&0==o)for(;c&&e[c-2]==e[c-3]&&e[c-1].insertLeft;)r=e[2+(c-=3)],n="left";if("right"==i&&o==l-a)for(;c<e.length-3&&e[c+3]==e[c+4]&&!e[c+5].insertLeft;)r=e[(c+=3)+2],n="right";break}return{node:r,start:o,end:s,collapse:n,coverStart:a,coverEnd:l}}function To(e,t){let i=ko;if("left"==t)for(let t=0;t<e.length&&(i=e[t]).left==i.right;t++);else for(let t=e.length-1;t>=0&&(i=e[t]).left==i.right;t--);return i}function Co(e){if(e.measure&&(e.measure.cache={},e.measure.heights=null,e.rest))for(let t=0;t<e.rest.length;t++)e.measure.caches[t]={}}function Mo(e){e.display.externalMeasure=null,ft(e.display.lineMeasure);for(let t=0;t<e.display.view.length;t++)Co(e.display.view[t])}function Po(e){Mo(e),e.display.cachedCharWidth=e.display.cachedTextHeight=e.display.cachedPaddingH=null,e.options.lineWrapping||(e.display.maxLineChanged=!0),e.display.lineNumChars=null}function $o(){return Je&&ot?-(document.body.getBoundingClientRect().left-parseInt(getComputedStyle(document.body).marginLeft)):window.pageXOffset||(document.documentElement||document.body).scrollLeft}function Lo(){return Je&&ot?-(document.body.getBoundingClientRect().top-parseInt(getComputedStyle(document.body).marginTop)):window.pageYOffset||(document.documentElement||document.body).scrollTop}function Eo(e){let t=0;if(e.widgets)for(let i=0;i<e.widgets.length;++i)e.widgets[i].above&&(t+=lo(e.widgets[i]));return t}function Ro(e,t,i,r,o){if(!o){let e=Eo(t);i.top+=e,i.bottom+=e}if("line"==r)return i;r||(r="local");let s=Er(t);if("local"==r?s+=uo(e.display):s-=e.display.viewOffset,"page"==r||"window"==r){let t=e.display.lineSpace.getBoundingClientRect();s+=t.top+("window"==r?0:Lo());let o=t.left+("window"==r?0:$o());i.left+=o,i.right+=o}return i.top+=s,i.bottom+=s,i}function Ao(e,t,i){if("div"==i)return t;let r=t.left,o=t.top;if("page"==i)r-=$o(),o-=Lo();else if("local"==i||!i){let t=e.display.sizer.getBoundingClientRect();r+=t.left,o+=t.top}let s=e.display.lineSpace.getBoundingClientRect();return{left:r-s.left,top:o-s.top}}function No(e,t,i,r,o){return r||(r=Ni(e.doc,t.line)),Ro(e,r,bo(e,r,t.ch,o),i)}function Io(e,t,i,r,o,s){function n(t,n){let a=xo(e,o,t,n?"right":"left",s);return n?a.left=a.right:a.right=a.left,Ro(e,r,a,i)}r=r||Ni(e.doc,t.line),o||(o=yo(e,r));let a=Jt(r,e.doc.direction),l=t.ch,c=t.sticky;if(l>=r.text.length?(l=r.text.length,c="before"):l<=0&&(l=0,c="after"),!a)return n("before"==c?l-1:l,"before"==c);function d(e,t,i){return n(i?e-1:e,1==a[t].level!=i)}let u=Xt(a,l,c),h=Kt,p=d(l,u,"before"==c);return null!=h&&(p.other=d(l,h,"before"!=c)),p}function Do(e,t){let i=0;t=Ki(e.doc,t),e.options.lineWrapping||(i=Go(e.display)*t.ch);let r=Ni(e.doc,t.line),o=Er(r)+uo(e.display);return{left:i,right:i,top:o,bottom:o+r.height}}function Oo(e,t,i,r,o){let s=ji(e,t,i);return s.xRel=o,r&&(s.outside=r),s}function Fo(e,t,i){let r=e.doc;if((i+=e.display.viewOffset)<0)return Oo(r.first,0,null,-1,-1);let o=zi(r,i),s=r.first+r.size-1;if(o>s)return Oo(r.first+r.size-1,Ni(r,s).text.length,null,1,1);t<0&&(t=0);let n=Ni(r,o);for(;;){let s=jo(e,n,o,t,i),a=Sr(n,s.ch+(s.xRel>0||s.outside>0?1:0));if(!a)return s;let l=a.find(1);if(l.line==o)return l;n=Ni(r,o=l.line)}}function zo(e,t,i,r){r-=Eo(t);let o=t.text.length,s=Zt((t=>xo(e,i,t-1).bottom<=r),o,0);return o=Zt((t=>xo(e,i,t).top>r),s,o),{begin:s,end:o}}function Wo(e,t,i,r){return i||(i=yo(e,t)),zo(e,t,i,Ro(e,t,xo(e,i,r),"line").top)}function Bo(e,t,i,r){return!(e.bottom<=i)&&(e.top>i||(r?e.left:e.right)>t)}function jo(e,t,i,r,o){o-=Er(t);let s=yo(e,t),n=Eo(t),a=0,l=t.text.length,c=!0,d=Jt(t,e.doc.direction);if(d){let n=(e.options.lineWrapping?Uo:Ho)(e,t,i,s,d,r,o);c=1!=n.level,a=c?n.from:n.to-1,l=c?n.to:n.from-1}let u,h,p=null,m=null,f=Zt((t=>{let i=xo(e,s,t);return i.top+=n,i.bottom+=n,!!Bo(i,r,o,!1)&&(i.top<=o&&i.left<=r&&(p=t,m=i),!0)}),a,l),g=!1;if(m){let e=r-m.left<m.right-r,t=e==c;f=p+(t?0:1),h=t?"after":"before",u=e?m.left:m.right}else{c||f!=l&&f!=a||f++,h=0==f?"after":f==t.text.length?"before":xo(e,s,f-(c?1:0)).bottom+n<=o==c?"after":"before";let r=Io(e,ji(i,f,h),"line",t,s);u=r.left,g=o<r.top?-1:o>=r.bottom?1:0}return f=qt(t.text,f,1),Oo(i,f,h,g,r-u)}function Ho(e,t,i,r,o,s,n){let a=Zt((a=>{let l=o[a],c=1!=l.level;return Bo(Io(e,ji(i,c?l.to:l.from,c?"before":"after"),"line",t,r),s,n,!0)}),0,o.length-1),l=o[a];if(a>0){let c=1!=l.level,d=Io(e,ji(i,c?l.from:l.to,c?"after":"before"),"line",t,r);Bo(d,s,n,!0)&&d.top>n&&(l=o[a-1])}return l}function Uo(e,t,i,r,o,s,n){let{begin:a,end:l}=zo(e,t,r,n);/\s/.test(t.text.charAt(l-1))&&l--;let c=null,d=null;for(let t=0;t<o.length;t++){let i=o[t];if(i.from>=l||i.to<=a)continue;let n=xo(e,r,1!=i.level?Math.min(l,i.to)-1:Math.max(a,i.from)).right,u=n<s?s-n+1e9:n-s;(!c||d>u)&&(c=i,d=u)}return c||(c=o[o.length-1]),c.from<a&&(c={from:a,to:c.to,level:c.level}),c.to>l&&(c={from:c.from,to:l,level:c.level}),c}function Vo(e){if(null!=e.cachedTextHeight)return e.cachedTextHeight;if(null==wo){wo=vt("pre",null,"CodeMirror-line-like");for(let e=0;e<49;++e)wo.appendChild(document.createTextNode("x")),wo.appendChild(vt("br"));wo.appendChild(document.createTextNode("x"))}gt(e.measure,wo);let t=wo.offsetHeight/50;return t>3&&(e.cachedTextHeight=t),ft(e.measure),t||1}function Go(e){if(null!=e.cachedCharWidth)return e.cachedCharWidth;let t=vt("span","xxxxxxxxxx"),i=vt("pre",[t],"CodeMirror-line-like");gt(e.measure,i);let r=t.getBoundingClientRect(),o=(r.right-r.left)/10;return o>2&&(e.cachedCharWidth=o),o||10}function qo(e){let t=e.display,i={},r={},o=t.gutters.clientLeft;for(let s=t.gutters.firstChild,n=0;s;s=s.nextSibling,++n){let t=e.display.gutterSpecs[n].className;i[t]=s.offsetLeft+s.clientLeft+o,r[t]=s.clientWidth}return{fixedPos:Zo(t),gutterTotalWidth:t.gutters.offsetWidth,gutterLeft:i,gutterWidth:r,wrapperWidth:t.wrapper.clientWidth}}function Zo(e){return e.scroller.getBoundingClientRect().left-e.sizer.getBoundingClientRect().left}function Ko(e){let t=Vo(e.display),i=e.options.lineWrapping,r=i&&Math.max(5,e.display.scroller.clientWidth/Go(e.display)-3);return o=>{if($r(e.doc,o))return 0;let s=0;if(o.widgets)for(let e=0;e<o.widgets.length;e++)o.widgets[e].height&&(s+=o.widgets[e].height);return i?s+(Math.ceil(o.text.length/r)||1)*t:s+t}}function Xo(e){let t=e.doc,i=Ko(e);t.iter((e=>{let t=i(e);t!=e.height&&Oi(e,t)}))}function Yo(e,t,i,r){let o=e.display;if(!i&&"true"==hi(t).getAttribute("cm-not-content"))return null;let s,n,a=o.lineSpace.getBoundingClientRect();try{s=t.clientX-a.left,n=t.clientY-a.top}catch(e){return null}let l,c=Fo(e,s,n);if(r&&c.xRel>0&&(l=Ni(e.doc,c.line).text).length==c.ch){let t=Ct(l,l.length,e.options.tabSize)-l.length;c=ji(c.line,Math.max(0,Math.round((s-po(e.display).left)/Go(e.display))-t))}return c}function Jo(e,t){if(t>=e.display.viewTo)return null;if((t-=e.display.viewFrom)<0)return null;let i=e.display.view;for(let e=0;e<i.length;e++)if((t-=i[e].size)<0)return e}function Qo(e,t,i,r){null==t&&(t=e.doc.first),null==i&&(i=e.doc.first+e.doc.size),r||(r=0);let o=e.display;if(r&&i<o.viewTo&&(null==o.updateLineNumbers||o.updateLineNumbers>t)&&(o.updateLineNumbers=t),e.curOp.viewChanged=!0,t>=o.viewTo)dr&&Mr(e.doc,t)<o.viewTo&&ts(e);else if(i<=o.viewFrom)dr&&Pr(e.doc,i+r)>o.viewFrom?ts(e):(o.viewFrom+=r,o.viewTo+=r);else if(t<=o.viewFrom&&i>=o.viewTo)ts(e);else if(t<=o.viewFrom){let t=is(e,i,i+r,1);t?(o.view=o.view.slice(t.index),o.viewFrom=t.lineN,o.viewTo+=r):ts(e)}else if(i>=o.viewTo){let i=is(e,t,t,-1);i?(o.view=o.view.slice(0,i.index),o.viewTo=i.lineN):ts(e)}else{let s=is(e,t,t,-1),n=is(e,i,i+r,1);s&&n?(o.view=o.view.slice(0,s.index).concat(Gr(e,s.lineN,n.lineN)).concat(o.view.slice(n.index)),o.viewTo+=r):ts(e)}let s=o.externalMeasured;s&&(i<s.lineN?s.lineN+=r:t<s.lineN+s.size&&(o.externalMeasured=null))}function es(e,t,i){e.curOp.viewChanged=!0;let r=e.display,o=e.display.externalMeasured;if(o&&t>=o.lineN&&t<o.lineN+o.size&&(r.externalMeasured=null),t<r.viewFrom||t>=r.viewTo)return;let s=r.view[Jo(e,t)];if(null==s.node)return;let n=s.changes||(s.changes=[]);-1==Pt(n,i)&&n.push(i)}function ts(e){e.display.viewFrom=e.display.viewTo=e.doc.first,e.display.view=[],e.display.viewOffset=0}function is(e,t,i,r){let o,s=Jo(e,t),n=e.display.view;if(!dr||i==e.doc.first+e.doc.size)return{index:s,lineN:i};let a=e.display.viewFrom;for(let e=0;e<s;e++)a+=n[e].size;if(a!=t){if(r>0){if(s==n.length-1)return null;o=a+n[s].size-t,s++}else o=a-t;t+=o,i+=o}for(;Mr(e.doc,i)!=i;){if(s==(r<0?0:n.length-1))return null;i+=r*n[s-(r<0?1:0)].size,s+=r}return{index:s,lineN:i}}function rs(e){let t=e.display.view,i=0;for(let e=0;e<t.length;e++){let r=t[e];r.hidden||r.node&&!r.changes||++i}return i}function os(e){e.display.input.showSelection(e.display.input.prepareSelection())}function ss(e,t=!0){let i=e.doc,r={},o=r.cursors=document.createDocumentFragment(),s=r.selection=document.createDocumentFragment();for(let r=0;r<i.sel.ranges.length;r++){if(!t&&r==i.sel.primIndex)continue;let n=i.sel.ranges[r];if(n.from().line>=e.display.viewTo||n.to().line<e.display.viewFrom)continue;let a=n.empty();(a||e.options.showCursorWhenSelecting)&&ns(e,n.head,o),a||ls(e,n,s)}return r}function ns(e,t,i){let r=Io(e,t,"div",null,null,!e.options.singleCursorHeightPerLine),o=i.appendChild(vt("div"," ","CodeMirror-cursor"));if(o.style.left=r.left+"px",o.style.top=r.top+"px",o.style.height=Math.max(0,r.bottom-r.top)*e.options.cursorHeight+"px",r.other){let e=i.appendChild(vt("div"," ","CodeMirror-cursor CodeMirror-secondarycursor"));e.style.display="",e.style.left=r.other.left+"px",e.style.top=r.other.top+"px",e.style.height=.85*(r.other.bottom-r.other.top)+"px"}}function as(e,t){return e.top-t.top||e.left-t.left}function ls(e,t,i){let r=e.display,o=e.doc,s=document.createDocumentFragment(),n=po(e.display),a=n.left,l=Math.max(r.sizerWidth,fo(e)-r.sizer.offsetLeft)-n.right,c="ltr"==o.direction;function d(e,t,i,r){t<0&&(t=0),t=Math.round(t),r=Math.round(r),s.appendChild(vt("div",null,"CodeMirror-selected",`position: absolute; left: ${e}px;\n                             top: ${t}px; width: ${null==i?l-e:i}px;\n                             height: ${r-t}px`))}function u(t,i,r){let s,n,u=Ni(o,t),h=u.text.length;function p(i,r){return No(e,ji(t,i),"div",u,r)}function m(t,i,r){let o=Wo(e,u,null,t),s="ltr"==i==("after"==r)?"left":"right";return p("after"==r?o.begin:o.end-(/\s/.test(u.text.charAt(o.end-1))?2:1),s)[s]}let f=Jt(u,o.direction);return function(e,t,i,r){if(!e)return r(t,i,"ltr",0);let o=!1;for(let s=0;s<e.length;++s){let n=e[s];(n.from<i&&n.to>t||t==i&&n.to==t)&&(r(Math.max(n.from,t),Math.min(n.to,i),1==n.level?"rtl":"ltr",s),o=!0)}o||r(t,i,"ltr")}(f,i||0,null==r?h:r,((e,t,o,u)=>{let g="ltr"==o,v=p(e,g?"left":"right"),b=p(t-1,g?"right":"left"),_=null==i&&0==e,y=null==r&&t==h,x=0==u,w=!f||u==f.length-1;if(b.top-v.top<=3){let e=(c?y:_)&&w,t=(c?_:y)&&x?a:(g?v:b).left,i=e?l:(g?b:v).right;d(t,v.top,i-t,v.bottom)}else{let i,r,s,n;g?(i=c&&_&&x?a:v.left,r=c?l:m(e,o,"before"),s=c?a:m(t,o,"after"),n=c&&y&&w?l:b.right):(i=c?m(e,o,"before"):a,r=!c&&_&&x?l:v.right,s=!c&&y&&w?a:b.left,n=c?m(t,o,"after"):l),d(i,v.top,r-i,v.bottom),v.bottom<b.top&&d(a,v.bottom,null,b.top),d(s,b.top,n-s,b.bottom)}(!s||as(v,s)<0)&&(s=v),as(b,s)<0&&(s=b),(!n||as(v,n)<0)&&(n=v),as(b,n)<0&&(n=b)})),{start:s,end:n}}let h=t.from(),p=t.to();if(h.line==p.line)u(h.line,h.ch,p.ch);else{let e=Ni(o,h.line),t=Ni(o,p.line),i=Cr(e)==Cr(t),r=u(h.line,h.ch,i?e.text.length+1:null).end,s=u(p.line,i?0:null,p.ch).start;i&&(r.top<s.top-2?(d(r.right,r.top,null,r.bottom),d(a,s.top,s.left,s.bottom)):d(r.right,r.top,s.left-r.right,r.bottom)),r.bottom<s.top&&d(a,r.bottom,null,s.top)}i.appendChild(s)}function cs(e){if(!e.state.focused)return;let t=e.display;clearInterval(t.blinker);let i=!0;t.cursorDiv.style.visibility="",e.options.cursorBlinkRate>0?t.blinker=setInterval((()=>{e.hasFocus()||ps(e),t.cursorDiv.style.visibility=(i=!i)?"":"hidden"}),e.options.cursorBlinkRate):e.options.cursorBlinkRate<0&&(t.cursorDiv.style.visibility="hidden")}function ds(e){e.hasFocus()||(e.display.input.focus(),e.state.focused||hs(e))}function us(e){e.state.delayingBlurEvent=!0,setTimeout((()=>{e.state.delayingBlurEvent&&(e.state.delayingBlurEvent=!1,e.state.focused&&ps(e))}),100)}function hs(e,t){e.state.delayingBlurEvent&&!e.state.draggingText&&(e.state.delayingBlurEvent=!1),"nocursor"!=e.options.readOnly&&(e.state.focused||(ri(e,"focus",e,t),e.state.focused=!0,xt(e.display.wrapper,"CodeMirror-focused"),e.curOp||e.display.selForContextMenu==e.doc.sel||(e.display.input.reset(),Xe&&setTimeout((()=>e.display.input.reset(!0)),20)),e.display.input.receivedFocus()),cs(e))}function ps(e,t){e.state.delayingBlurEvent||(e.state.focused&&(ri(e,"blur",e,t),e.state.focused=!1,mt(e.display.wrapper,"CodeMirror-focused")),clearInterval(e.display.blinker),setTimeout((()=>{e.state.focused||(e.display.shift=!1)}),150))}function ms(e){let t=e.display,i=t.lineDiv.offsetTop;for(let r=0;r<t.view.length;r++){let o,s=t.view[r],n=e.options.lineWrapping,a=0;if(s.hidden)continue;if(Ze&&Ke<8){let e=s.node.offsetTop+s.node.offsetHeight;o=e-i,i=e}else{let e=s.node.getBoundingClientRect();o=e.bottom-e.top,!n&&s.text.firstChild&&(a=s.text.firstChild.getBoundingClientRect().right-e.left-1)}let l=s.line.height-o;if((l>.005||l<-.005)&&(Oi(s.line,o),fs(s.line),s.rest))for(let e=0;e<s.rest.length;e++)fs(s.rest[e]);if(a>e.display.sizerWidth){let t=Math.ceil(a/Go(e.display));t>e.display.maxLineLength&&(e.display.maxLineLength=t,e.display.maxLine=s.line,e.display.maxLineChanged=!0)}}}function fs(e){if(e.widgets)for(let t=0;t<e.widgets.length;++t){let i=e.widgets[t],r=i.node.parentNode;r&&(i.height=r.offsetHeight)}}function gs(e,t,i){let r=i&&null!=i.top?Math.max(0,i.top):e.scroller.scrollTop;r=Math.floor(r-uo(e));let o=i&&null!=i.bottom?i.bottom:r+e.wrapper.clientHeight,s=zi(t,r),n=zi(t,o);if(i&&i.ensure){let r=i.ensure.from.line,o=i.ensure.to.line;r<s?(s=r,n=zi(t,Er(Ni(t,r))+e.wrapper.clientHeight)):Math.min(o,t.lastLine())>=n&&(s=zi(t,Er(Ni(t,o))-e.wrapper.clientHeight),n=o)}return{from:s,to:Math.max(n,s+1)}}function vs(e,t){let i=e.display,r=Vo(e.display);t.top<0&&(t.top=0);let o=e.curOp&&null!=e.curOp.scrollTop?e.curOp.scrollTop:i.scroller.scrollTop,s=go(e),n={};t.bottom-t.top>s&&(t.bottom=t.top+s);let a=e.doc.height+ho(i),l=t.top<r,c=t.bottom>a-r;if(t.top<o)n.scrollTop=l?0:t.top;else if(t.bottom>o+s){let e=Math.min(t.top,(c?a:t.bottom)-s);e!=o&&(n.scrollTop=e)}let d=e.options.fixedGutter?0:i.gutters.offsetWidth,u=e.curOp&&null!=e.curOp.scrollLeft?e.curOp.scrollLeft:i.scroller.scrollLeft-d,h=fo(e)-i.gutters.offsetWidth,p=t.right-t.left>h;return p&&(t.right=t.left+h),t.left<10?n.scrollLeft=0:t.left<u?n.scrollLeft=Math.max(0,t.left+d-(p?0:10)):t.right>h+u-3&&(n.scrollLeft=t.right+(p?0:10)-h),n}function bs(e,t){null!=t&&(xs(e),e.curOp.scrollTop=(null==e.curOp.scrollTop?e.doc.scrollTop:e.curOp.scrollTop)+t)}function _s(e){xs(e);let t=e.getCursor();e.curOp.scrollToPos={from:t,to:t,margin:e.options.cursorScrollMargin}}function ys(e,t,i){null==t&&null==i||xs(e),null!=t&&(e.curOp.scrollLeft=t),null!=i&&(e.curOp.scrollTop=i)}function xs(e){let t=e.curOp.scrollToPos;if(t){e.curOp.scrollToPos=null,ws(e,Do(e,t.from),Do(e,t.to),t.margin)}}function ws(e,t,i,r){let o=vs(e,{left:Math.min(t.left,i.left),top:Math.min(t.top,i.top)-r,right:Math.max(t.right,i.right),bottom:Math.max(t.bottom,i.bottom)+r});ys(e,o.scrollLeft,o.scrollTop)}function ks(e,t){Math.abs(e.doc.scrollTop-t)<2||(Ue||Zs(e,{top:t}),Ss(e,t,!0),Ue&&Zs(e),Hs(e,100))}function Ss(e,t,i){t=Math.max(0,Math.min(e.display.scroller.scrollHeight-e.display.scroller.clientHeight,t)),(e.display.scroller.scrollTop!=t||i)&&(e.doc.scrollTop=t,e.display.scrollbars.setScrollTop(t),e.display.scroller.scrollTop!=t&&(e.display.scroller.scrollTop=t))}function Ts(e,t,i,r){t=Math.max(0,Math.min(t,e.display.scroller.scrollWidth-e.display.scroller.clientWidth)),(i?t==e.doc.scrollLeft:Math.abs(e.doc.scrollLeft-t)<2)&&!r||(e.doc.scrollLeft=t,Ys(e),e.display.scroller.scrollLeft!=t&&(e.display.scroller.scrollLeft=t),e.display.scrollbars.setScrollLeft(t))}function Cs(e){let t=e.display,i=t.gutters.offsetWidth,r=Math.round(e.doc.height+ho(e.display));return{clientHeight:t.scroller.clientHeight,viewHeight:t.wrapper.clientHeight,scrollWidth:t.scroller.scrollWidth,clientWidth:t.scroller.clientWidth,viewWidth:t.wrapper.clientWidth,barLeft:e.options.fixedGutter?i:0,docHeight:r,scrollHeight:r+mo(e)+t.barHeight,nativeBarWidth:t.nativeBarWidth,gutterWidth:i}}function Ms(e,t){t||(t=Cs(e));let i=e.display.barWidth,r=e.display.barHeight;Ps(e,t);for(let t=0;t<4&&i!=e.display.barWidth||r!=e.display.barHeight;t++)i!=e.display.barWidth&&e.options.lineWrapping&&ms(e),Ps(e,Cs(e)),i=e.display.barWidth,r=e.display.barHeight}function Ps(e,t){let i=e.display,r=i.scrollbars.update(t);i.sizer.style.paddingRight=(i.barWidth=r.right)+"px",i.sizer.style.paddingBottom=(i.barHeight=r.bottom)+"px",i.heightForcer.style.borderBottom=r.bottom+"px solid transparent",r.right&&r.bottom?(i.scrollbarFiller.style.display="block",i.scrollbarFiller.style.height=r.bottom+"px",i.scrollbarFiller.style.width=r.right+"px"):i.scrollbarFiller.style.display="",r.bottom&&e.options.coverGutterNextToScrollbar&&e.options.fixedGutter?(i.gutterFiller.style.display="block",i.gutterFiller.style.height=r.bottom+"px",i.gutterFiller.style.width=t.gutterWidth+"px"):i.gutterFiller.style.display=""}var $s={native:class{constructor(e,t,i){this.cm=i;let r=this.vert=vt("div",[vt("div",null,null,"min-width: 1px")],"CodeMirror-vscrollbar"),o=this.horiz=vt("div",[vt("div",null,null,"height: 100%; min-height: 1px")],"CodeMirror-hscrollbar");r.tabIndex=o.tabIndex=-1,e(r),e(o),ei(r,"scroll",(()=>{r.clientHeight&&t(r.scrollTop,"vertical")})),ei(o,"scroll",(()=>{o.clientWidth&&t(o.scrollLeft,"horizontal")})),this.checkedZeroWidth=!1,Ze&&Ke<8&&(this.horiz.style.minHeight=this.vert.style.minWidth="18px")}update(e){let t=e.scrollWidth>e.clientWidth+1,i=e.scrollHeight>e.clientHeight+1,r=e.nativeBarWidth;if(i){this.vert.style.display="block",this.vert.style.bottom=t?r+"px":"0";let i=e.viewHeight-(t?r:0);this.vert.firstChild.style.height=Math.max(0,e.scrollHeight-e.clientHeight+i)+"px"}else this.vert.style.display="",this.vert.firstChild.style.height="0";if(t){this.horiz.style.display="block",this.horiz.style.right=i?r+"px":"0",this.horiz.style.left=e.barLeft+"px";let t=e.viewWidth-e.barLeft-(i?r:0);this.horiz.firstChild.style.width=Math.max(0,e.scrollWidth-e.clientWidth+t)+"px"}else this.horiz.style.display="",this.horiz.firstChild.style.width="0";return!this.checkedZeroWidth&&e.clientHeight>0&&(0==r&&this.zeroWidthHack(),this.checkedZeroWidth=!0),{right:i?r:0,bottom:t?r:0}}setScrollLeft(e){this.horiz.scrollLeft!=e&&(this.horiz.scrollLeft=e),this.disableHoriz&&this.enableZeroWidthBar(this.horiz,this.disableHoriz,"horiz")}setScrollTop(e){this.vert.scrollTop!=e&&(this.vert.scrollTop=e),this.disableVert&&this.enableZeroWidthBar(this.vert,this.disableVert,"vert")}zeroWidthHack(){let e=nt&&!tt?"12px":"18px";this.horiz.style.height=this.vert.style.width=e,this.horiz.style.pointerEvents=this.vert.style.pointerEvents="none",this.disableHoriz=new Mt,this.disableVert=new Mt}enableZeroWidthBar(e,t,i){e.style.pointerEvents="auto",t.set(1e3,(function r(){let o=e.getBoundingClientRect();("vert"==i?document.elementFromPoint(o.right-1,(o.top+o.bottom)/2):document.elementFromPoint((o.right+o.left)/2,o.bottom-1))!=e?e.style.pointerEvents="none":t.set(1e3,r)}))}clear(){let e=this.horiz.parentNode;e.removeChild(this.horiz),e.removeChild(this.vert)}},null:class{update(){return{bottom:0,right:0}}setScrollLeft(){}setScrollTop(){}clear(){}}};function Ls(e){e.display.scrollbars&&(e.display.scrollbars.clear(),e.display.scrollbars.addClass&&mt(e.display.wrapper,e.display.scrollbars.addClass)),e.display.scrollbars=new $s[e.options.scrollbarStyle]((t=>{e.display.wrapper.insertBefore(t,e.display.scrollbarFiller),ei(t,"mousedown",(()=>{e.state.focused&&setTimeout((()=>e.display.input.focus()),0)})),t.setAttribute("cm-not-content","true")}),((t,i)=>{"horizontal"==i?Ts(e,t):ks(e,t)}),e),e.display.scrollbars.addClass&&xt(e.display.wrapper,e.display.scrollbars.addClass)}var Es=0;function Rs(e){var t;e.curOp={cm:e,viewChanged:!1,startHeight:e.doc.height,forceUpdate:!1,updateInput:0,typing:!1,changeObjs:null,cursorActivityHandlers:null,cursorActivityCalled:0,selectionChanged:!1,updateMaxLine:!1,scrollLeft:null,scrollTop:null,scrollToPos:null,focus:!1,id:++Es},t=e.curOp,qr?qr.ops.push(t):t.ownsGroup=qr={ops:[t],delayedCallbacks:[]}}function As(e){let t=e.curOp;t&&function(e,t){let i=e.ownsGroup;if(i)try{!function(e){let t=e.delayedCallbacks,i=0;do{for(;i<t.length;i++)t[i].call(null);for(let t=0;t<e.ops.length;t++){let i=e.ops[t];if(i.cursorActivityHandlers)for(;i.cursorActivityCalled<i.cursorActivityHandlers.length;)i.cursorActivityHandlers[i.cursorActivityCalled++].call(null,i.cm)}}while(i<t.length)}(i)}finally{qr=null,t(i)}}(t,(e=>{for(let t=0;t<e.ops.length;t++)e.ops[t].cm.curOp=null;!function(e){let t=e.ops;for(let e=0;e<t.length;e++)Ns(t[e]);for(let e=0;e<t.length;e++)Is(t[e]);for(let e=0;e<t.length;e++)Ds(t[e]);for(let e=0;e<t.length;e++)Os(t[e]);for(let e=0;e<t.length;e++)Fs(t[e])}(e)}))}function Ns(e){let t=e.cm,i=t.display;!function(e){let t=e.display;!t.scrollbarsClipped&&t.scroller.offsetWidth&&(t.nativeBarWidth=t.scroller.offsetWidth-t.scroller.clientWidth,t.heightForcer.style.height=mo(e)+"px",t.sizer.style.marginBottom=-t.nativeBarWidth+"px",t.sizer.style.borderRightWidth=mo(e)+"px",t.scrollbarsClipped=!0)}(t),e.updateMaxLine&&Ar(t),e.mustUpdate=e.viewChanged||e.forceUpdate||null!=e.scrollTop||e.scrollToPos&&(e.scrollToPos.from.line<i.viewFrom||e.scrollToPos.to.line>=i.viewTo)||i.maxLineChanged&&t.options.lineWrapping,e.update=e.mustUpdate&&new Vs(t,e.mustUpdate&&{top:e.scrollTop,ensure:e.scrollToPos},e.forceUpdate)}function Is(e){e.updatedDisplay=e.mustUpdate&&Gs(e.cm,e.update)}function Ds(e){let t=e.cm,i=t.display;e.updatedDisplay&&ms(t),e.barMeasure=Cs(t),i.maxLineChanged&&!t.options.lineWrapping&&(e.adjustWidthTo=bo(t,i.maxLine,i.maxLine.text.length).left+3,t.display.sizerWidth=e.adjustWidthTo,e.barMeasure.scrollWidth=Math.max(i.scroller.clientWidth,i.sizer.offsetLeft+e.adjustWidthTo+mo(t)+t.display.barWidth),e.maxScrollLeft=Math.max(0,i.sizer.offsetLeft+e.adjustWidthTo-fo(t))),(e.updatedDisplay||e.selectionChanged)&&(e.preparedSelection=i.input.prepareSelection())}function Os(e){let t=e.cm;null!=e.adjustWidthTo&&(t.display.sizer.style.minWidth=e.adjustWidthTo+"px",e.maxScrollLeft<t.doc.scrollLeft&&Ts(t,Math.min(t.display.scroller.scrollLeft,e.maxScrollLeft),!0),t.display.maxLineChanged=!1);let i=e.focus&&e.focus==yt();e.preparedSelection&&t.display.input.showSelection(e.preparedSelection,i),(e.updatedDisplay||e.startHeight!=t.doc.height)&&Ms(t,e.barMeasure),e.updatedDisplay&&Xs(t,e.barMeasure),e.selectionChanged&&cs(t),t.state.focused&&e.updateInput&&t.display.input.reset(e.typing),i&&ds(e.cm)}function Fs(e){let t=e.cm,i=t.display,r=t.doc;if(e.updatedDisplay&&qs(t,e.update),null==i.wheelStartX||null==e.scrollTop&&null==e.scrollLeft&&!e.scrollToPos||(i.wheelStartX=i.wheelStartY=null),null!=e.scrollTop&&Ss(t,e.scrollTop,e.forceScroll),null!=e.scrollLeft&&Ts(t,e.scrollLeft,!0,!0),e.scrollToPos){let i=function(e,t,i,r){let o;null==r&&(r=0),e.options.lineWrapping||t!=i||(i="before"==(t=t.ch?ji(t.line,"before"==t.sticky?t.ch-1:t.ch,"after"):t).sticky?ji(t.line,t.ch+1,"before"):t);for(let s=0;s<5;s++){let s=!1,n=Io(e,t),a=i&&i!=t?Io(e,i):n;o={left:Math.min(n.left,a.left),top:Math.min(n.top,a.top)-r,right:Math.max(n.left,a.left),bottom:Math.max(n.bottom,a.bottom)+r};let l=vs(e,o),c=e.doc.scrollTop,d=e.doc.scrollLeft;if(null!=l.scrollTop&&(ks(e,l.scrollTop),Math.abs(e.doc.scrollTop-c)>1&&(s=!0)),null!=l.scrollLeft&&(Ts(e,l.scrollLeft),Math.abs(e.doc.scrollLeft-d)>1&&(s=!0)),!s)break}return o}(t,Ki(r,e.scrollToPos.from),Ki(r,e.scrollToPos.to),e.scrollToPos.margin);!function(e,t){if(oi(e,"scrollCursorIntoView"))return;let i=e.display,r=i.sizer.getBoundingClientRect(),o=null;if(t.top+r.top<0?o=!0:t.bottom+r.top>(window.innerHeight||document.documentElement.clientHeight)&&(o=!1),null!=o&&!it){let r=vt("div","​",null,`position: absolute;\n                         top: ${t.top-i.viewOffset-uo(e.display)}px;\n                         height: ${t.bottom-t.top+mo(e)+i.barHeight}px;\n                         left: ${t.left}px; width: ${Math.max(2,t.right-t.left)}px;`);e.display.lineSpace.appendChild(r),r.scrollIntoView(o),e.display.lineSpace.removeChild(r)}}(t,i)}let o=e.maybeHiddenMarkers,s=e.maybeUnhiddenMarkers;if(o)for(let e=0;e<o.length;++e)o[e].lines.length||ri(o[e],"hide");if(s)for(let e=0;e<s.length;++e)s[e].lines.length&&ri(s[e],"unhide");i.wrapper.offsetHeight&&(r.scrollTop=t.display.scroller.scrollTop),e.changeObjs&&ri(t,"changes",t,e.changeObjs),e.update&&e.update.finish()}function zs(e,t){if(e.curOp)return t();Rs(e);try{return t()}finally{As(e)}}function Ws(e,t){return function(){if(e.curOp)return t.apply(e,arguments);Rs(e);try{return t.apply(e,arguments)}finally{As(e)}}}function Bs(e){return function(){if(this.curOp)return e.apply(this,arguments);Rs(this);try{return e.apply(this,arguments)}finally{As(this)}}}function js(e){return function(){let t=this.cm;if(!t||t.curOp)return e.apply(this,arguments);Rs(t);try{return e.apply(this,arguments)}finally{As(t)}}}function Hs(e,t){e.doc.highlightFrontier<e.display.viewTo&&e.state.highlight.set(t,St(Us,e))}function Us(e){let t=e.doc;if(t.highlightFrontier>=e.display.viewTo)return;let i=+new Date+e.options.workTime,r=tr(e,t.highlightFrontier),o=[];t.iter(r.line,Math.min(t.first+t.size,e.display.viewTo+500),(s=>{if(r.line>=e.display.viewFrom){let i=s.styles,n=s.text.length>e.options.maxHighlightLength?Li(t.mode,r.state):null,a=Qi(e,s,r,!0);n&&(r.state=n),s.styles=a.styles;let l=s.styleClasses,c=a.classes;c?s.styleClasses=c:l&&(s.styleClasses=null);let d=!i||i.length!=s.styles.length||l!=c&&(!l||!c||l.bgClass!=c.bgClass||l.textClass!=c.textClass);for(let e=0;!d&&e<i.length;++e)d=i[e]!=s.styles[e];d&&o.push(r.line),s.stateAfter=r.save(),r.nextLine()}else s.text.length<=e.options.maxHighlightLength&&ir(e,s.text,r),s.stateAfter=r.line%5==0?r.save():null,r.nextLine();if(+new Date>i)return Hs(e,e.options.workDelay),!0})),t.highlightFrontier=r.line,t.modeFrontier=Math.max(t.modeFrontier,r.line),o.length&&zs(e,(()=>{for(let t=0;t<o.length;t++)es(e,o[t],"text")}))}var Vs=class{constructor(e,t,i){let r=e.display;this.viewport=t,this.visible=gs(r,e.doc,t),this.editorIsHidden=!r.wrapper.offsetWidth,this.wrapperHeight=r.wrapper.clientHeight,this.wrapperWidth=r.wrapper.clientWidth,this.oldDisplayWidth=fo(e),this.force=i,this.dims=qo(e),this.events=[]}signal(e,t){ni(e,t)&&this.events.push(arguments)}finish(){for(let e=0;e<this.events.length;e++)ri.apply(null,this.events[e])}};function Gs(e,t){let i=e.display,r=e.doc;if(t.editorIsHidden)return ts(e),!1;if(!t.force&&t.visible.from>=i.viewFrom&&t.visible.to<=i.viewTo&&(null==i.updateLineNumbers||i.updateLineNumbers>=i.viewTo)&&i.renderedView==i.view&&0==rs(e))return!1;Js(e)&&(ts(e),t.dims=qo(e));let o=r.first+r.size,s=Math.max(t.visible.from-e.options.viewportMargin,r.first),n=Math.min(o,t.visible.to+e.options.viewportMargin);i.viewFrom<s&&s-i.viewFrom<20&&(s=Math.max(r.first,i.viewFrom)),i.viewTo>n&&i.viewTo-n<20&&(n=Math.min(o,i.viewTo)),dr&&(s=Mr(e.doc,s),n=Pr(e.doc,n));let a=s!=i.viewFrom||n!=i.viewTo||i.lastWrapHeight!=t.wrapperHeight||i.lastWrapWidth!=t.wrapperWidth;!function(e,t,i){let r=e.display;0==r.view.length||t>=r.viewTo||i<=r.viewFrom?(r.view=Gr(e,t,i),r.viewFrom=t):(r.viewFrom>t?r.view=Gr(e,t,r.viewFrom).concat(r.view):r.viewFrom<t&&(r.view=r.view.slice(Jo(e,t))),r.viewFrom=t,r.viewTo<i?r.view=r.view.concat(Gr(e,r.viewTo,i)):r.viewTo>i&&(r.view=r.view.slice(0,Jo(e,i)))),r.viewTo=i}(e,s,n),i.viewOffset=Er(Ni(e.doc,i.viewFrom)),e.display.mover.style.top=i.viewOffset+"px";let l=rs(e);if(!a&&0==l&&!t.force&&i.renderedView==i.view&&(null==i.updateLineNumbers||i.updateLineNumbers>=i.viewTo))return!1;let c=function(e){if(e.hasFocus())return null;let t=yt();if(!t||!_t(e.display.lineDiv,t))return null;let i={activeElt:t};if(window.getSelection){let t=window.getSelection();t.anchorNode&&t.extend&&_t(e.display.lineDiv,t.anchorNode)&&(i.anchorNode=t.anchorNode,i.anchorOffset=t.anchorOffset,i.focusNode=t.focusNode,i.focusOffset=t.focusOffset)}return i}(e);return l>4&&(i.lineDiv.style.display="none"),function(e,t,i){let r=e.display,o=e.options.lineNumbers,s=r.lineDiv,n=s.firstChild;function a(t){let i=t.nextSibling;return Xe&&nt&&e.display.currentWheelTarget==t?t.style.display="none":t.parentNode.removeChild(t),i}let l=r.view,c=r.viewFrom;for(let r=0;r<l.length;r++){let d=l[r];if(d.hidden);else if(d.node&&d.node.parentNode==s){for(;n!=d.node;)n=a(n);let r=o&&null!=t&&t<=c&&d.lineNumber;d.changes&&(Pt(d.changes,"gutter")>-1&&(r=!1),Yr(e,d,c,i)),r&&(ft(d.lineNumber),d.lineNumber.appendChild(document.createTextNode(Bi(e.options,c)))),n=d.node.nextSibling}else{let t=oo(e,d,c,i);s.insertBefore(t,n)}c+=d.size}for(;n;)n=a(n)}(e,i.updateLineNumbers,t.dims),l>4&&(i.lineDiv.style.display=""),i.renderedView=i.view,function(e){if(e&&e.activeElt&&e.activeElt!=yt()&&(e.activeElt.focus(),!/^(INPUT|TEXTAREA)$/.test(e.activeElt.nodeName)&&e.anchorNode&&_t(document.body,e.anchorNode)&&_t(document.body,e.focusNode))){let t=window.getSelection(),i=document.createRange();i.setEnd(e.anchorNode,e.anchorOffset),i.collapse(!1),t.removeAllRanges(),t.addRange(i),t.extend(e.focusNode,e.focusOffset)}}(c),ft(i.cursorDiv),ft(i.selectionDiv),i.gutters.style.height=i.sizer.style.minHeight=0,a&&(i.lastWrapHeight=t.wrapperHeight,i.lastWrapWidth=t.wrapperWidth,Hs(e,400)),i.updateLineNumbers=null,!0}function qs(e,t){let i=t.viewport;for(let r=!0;;r=!1){if(r&&e.options.lineWrapping&&t.oldDisplayWidth!=fo(e))r&&(t.visible=gs(e.display,e.doc,i));else if(i&&null!=i.top&&(i={top:Math.min(e.doc.height+ho(e.display)-go(e),i.top)}),t.visible=gs(e.display,e.doc,i),t.visible.from>=e.display.viewFrom&&t.visible.to<=e.display.viewTo)break;if(!Gs(e,t))break;ms(e);let o=Cs(e);os(e),Ms(e,o),Xs(e,o),t.force=!1}t.signal(e,"update",e),e.display.viewFrom==e.display.reportedViewFrom&&e.display.viewTo==e.display.reportedViewTo||(t.signal(e,"viewportChange",e,e.display.viewFrom,e.display.viewTo),e.display.reportedViewFrom=e.display.viewFrom,e.display.reportedViewTo=e.display.viewTo)}function Zs(e,t){let i=new Vs(e,t);if(Gs(e,i)){ms(e),qs(e,i);let t=Cs(e);os(e),Ms(e,t),Xs(e,t),i.finish()}}function Ks(e){let t=e.gutters.offsetWidth;e.sizer.style.marginLeft=t+"px",Kr(e,"gutterChanged",e)}function Xs(e,t){e.display.sizer.style.minHeight=t.docHeight+"px",e.display.heightForcer.style.top=t.docHeight+"px",e.display.gutters.style.height=t.docHeight+e.display.barHeight+mo(e)+"px"}function Ys(e){let t=e.display,i=t.view;if(!(t.alignWidgets||t.gutters.firstChild&&e.options.fixedGutter))return;let r=Zo(t)-t.scroller.scrollLeft+e.doc.scrollLeft,o=t.gutters.offsetWidth,s=r+"px";for(let t=0;t<i.length;t++)if(!i[t].hidden){e.options.fixedGutter&&(i[t].gutter&&(i[t].gutter.style.left=s),i[t].gutterBackground&&(i[t].gutterBackground.style.left=s));let r=i[t].alignable;if(r)for(let e=0;e<r.length;e++)r[e].style.left=s}e.options.fixedGutter&&(t.gutters.style.left=r+o+"px")}function Js(e){if(!e.options.lineNumbers)return!1;let t=e.doc,i=Bi(e.options,t.first+t.size-1),r=e.display;if(i.length!=r.lineNumChars){let t=r.measure.appendChild(vt("div",[vt("div",i)],"CodeMirror-linenumber CodeMirror-gutter-elt")),o=t.firstChild.offsetWidth,s=t.offsetWidth-o;return r.lineGutter.style.width="",r.lineNumInnerWidth=Math.max(o,r.lineGutter.offsetWidth-s)+1,r.lineNumWidth=r.lineNumInnerWidth+s,r.lineNumChars=r.lineNumInnerWidth?i.length:-1,r.lineGutter.style.width=r.lineNumWidth+"px",Ks(e.display),!0}return!1}function Qs(e,t){let i=[],r=!1;for(let o=0;o<e.length;o++){let s=e[o],n=null;if("string"!=typeof s&&(n=s.style,s=s.className),"CodeMirror-linenumbers"==s){if(!t)continue;r=!0}i.push({className:s,style:n})}return t&&!r&&i.push({className:"CodeMirror-linenumbers",style:null}),i}function en(e){let t=e.gutters,i=e.gutterSpecs;ft(t),e.lineGutter=null;for(let r=0;r<i.length;++r){let{className:o,style:s}=i[r],n=t.appendChild(vt("div",null,"CodeMirror-gutter "+o));s&&(n.style.cssText=s),"CodeMirror-linenumbers"==o&&(e.lineGutter=n,n.style.width=(e.lineNumWidth||1)+"px")}t.style.display=i.length?"":"none",Ks(e)}function tn(e){en(e.display),Qo(e),Ys(e)}function rn(e,t,i,r){let o=this;this.input=i,o.scrollbarFiller=vt("div",null,"CodeMirror-scrollbar-filler"),o.scrollbarFiller.setAttribute("cm-not-content","true"),o.gutterFiller=vt("div",null,"CodeMirror-gutter-filler"),o.gutterFiller.setAttribute("cm-not-content","true"),o.lineDiv=bt("div",null,"CodeMirror-code"),o.selectionDiv=vt("div",null,null,"position: relative; z-index: 1"),o.cursorDiv=vt("div",null,"CodeMirror-cursors"),o.measure=vt("div",null,"CodeMirror-measure"),o.lineMeasure=vt("div",null,"CodeMirror-measure"),o.lineSpace=bt("div",[o.measure,o.lineMeasure,o.selectionDiv,o.cursorDiv,o.lineDiv],null,"position: relative; outline: none");let s=bt("div",[o.lineSpace],"CodeMirror-lines");o.mover=vt("div",[s],null,"position: relative"),o.sizer=vt("div",[o.mover],"CodeMirror-sizer"),o.sizerWidth=null,o.heightForcer=vt("div",null,null,"position: absolute; height: "+$t+"px; width: 1px;"),o.gutters=vt("div",null,"CodeMirror-gutters"),o.lineGutter=null,o.scroller=vt("div",[o.sizer,o.heightForcer,o.gutters],"CodeMirror-scroll"),o.scroller.setAttribute("tabIndex","-1"),o.wrapper=vt("div",[o.scrollbarFiller,o.gutterFiller,o.scroller],"CodeMirror"),Ze&&Ke<8&&(o.gutters.style.zIndex=-1,o.scroller.style.paddingRight=0),Xe||Ue&&st||(o.scroller.draggable=!0),e&&(e.appendChild?e.appendChild(o.wrapper):e(o.wrapper)),o.viewFrom=o.viewTo=t.first,o.reportedViewFrom=o.reportedViewTo=t.first,o.view=[],o.renderedView=null,o.externalMeasured=null,o.viewOffset=0,o.lastWrapHeight=o.lastWrapWidth=0,o.updateLineNumbers=null,o.nativeBarWidth=o.barHeight=o.barWidth=0,o.scrollbarsClipped=!1,o.lineNumWidth=o.lineNumInnerWidth=o.lineNumChars=null,o.alignWidgets=!1,o.cachedCharWidth=o.cachedTextHeight=o.cachedPaddingH=null,o.maxLine=null,o.maxLineLength=0,o.maxLineChanged=!1,o.wheelDX=o.wheelDY=o.wheelStartX=o.wheelStartY=null,o.shift=!1,o.selForContextMenu=null,o.activeTouch=null,o.gutterSpecs=Qs(r.gutters,r.lineNumbers),en(o),i.init(o)}var on=0,sn=null;function nn(e){let t=e.wheelDeltaX,i=e.wheelDeltaY;return null==t&&e.detail&&e.axis==e.HORIZONTAL_AXIS&&(t=e.detail),null==i&&e.detail&&e.axis==e.VERTICAL_AXIS?i=e.detail:null==i&&(i=e.wheelDelta),{x:t,y:i}}function an(e){let t=nn(e);return t.x*=sn,t.y*=sn,t}function ln(e,t){let i=nn(t),r=i.x,o=i.y,s=e.display,n=s.scroller,a=n.scrollWidth>n.clientWidth,l=n.scrollHeight>n.clientHeight;if(r&&a||o&&l){if(o&&nt&&Xe)e:for(let i=t.target,r=s.view;i!=n;i=i.parentNode)for(let t=0;t<r.length;t++)if(r[t].node==i){e.display.currentWheelTarget=i;break e}if(r&&!Ue&&!Qe&&null!=sn)return o&&l&&ks(e,Math.max(0,n.scrollTop+o*sn)),Ts(e,Math.max(0,n.scrollLeft+r*sn)),(!o||o&&l)&&li(t),void(s.wheelStartX=null);if(o&&null!=sn){let t=o*sn,i=e.doc.scrollTop,r=i+s.wrapper.clientHeight;t<0?i=Math.max(0,i+t-50):r=Math.min(e.doc.height,r+t+50),Zs(e,{top:i,bottom:r})}on<20&&(null==s.wheelStartX?(s.wheelStartX=n.scrollLeft,s.wheelStartY=n.scrollTop,s.wheelDX=r,s.wheelDY=o,setTimeout((()=>{if(null==s.wheelStartX)return;let e=n.scrollLeft-s.wheelStartX,t=n.scrollTop-s.wheelStartY,i=t&&s.wheelDY&&t/s.wheelDY||e&&s.wheelDX&&e/s.wheelDX;s.wheelStartX=s.wheelStartY=null,i&&(sn=(sn*on+i)/(on+1),++on)}),200)):(s.wheelDX+=r,s.wheelDY+=o))}}Ze?sn=-.53:Ue?sn=15:Je?sn=-.7:et&&(sn=-1/3);var cn=class{constructor(e,t){this.ranges=e,this.primIndex=t}primary(){return this.ranges[this.primIndex]}equals(e){if(e==this)return!0;if(e.primIndex!=this.primIndex||e.ranges.length!=this.ranges.length)return!1;for(let t=0;t<this.ranges.length;t++){let i=this.ranges[t],r=e.ranges[t];if(!Ui(i.anchor,r.anchor)||!Ui(i.head,r.head))return!1}return!0}deepCopy(){let e=[];for(let t=0;t<this.ranges.length;t++)e[t]=new dn(Vi(this.ranges[t].anchor),Vi(this.ranges[t].head));return new cn(e,this.primIndex)}somethingSelected(){for(let e=0;e<this.ranges.length;e++)if(!this.ranges[e].empty())return!0;return!1}contains(e,t){t||(t=e);for(let i=0;i<this.ranges.length;i++){let r=this.ranges[i];if(Hi(t,r.from())>=0&&Hi(e,r.to())<=0)return i}return-1}},dn=class{constructor(e,t){this.anchor=e,this.head=t}from(){return qi(this.anchor,this.head)}to(){return Gi(this.anchor,this.head)}empty(){return this.head.line==this.anchor.line&&this.head.ch==this.anchor.ch}};function un(e,t,i){let r=e&&e.options.selectionsMayTouch,o=t[i];t.sort(((e,t)=>Hi(e.from(),t.from()))),i=Pt(t,o);for(let e=1;e<t.length;e++){let o=t[e],s=t[e-1],n=Hi(s.to(),o.from());if(r&&!o.empty()?n>0:n>=0){let r=qi(s.from(),o.from()),n=Gi(s.to(),o.to()),a=s.empty()?o.from()==o.head:s.from()==s.head;e<=i&&--i,t.splice(--e,2,new dn(a?n:r,a?r:n))}}return new cn(t,i)}function hn(e,t){return new cn([new dn(e,t||e)],0)}function pn(e){return e.text?ji(e.from.line+e.text.length-1,Ot(e.text).length+(1==e.text.length?e.from.ch:0)):e.to}function mn(e,t){if(Hi(e,t.from)<0)return e;if(Hi(e,t.to)<=0)return pn(t);let i=e.line+t.text.length-(t.to.line-t.from.line)-1,r=e.ch;return e.line==t.to.line&&(r+=pn(t).ch-t.to.ch),ji(i,r)}function fn(e,t){let i=[];for(let r=0;r<e.sel.ranges.length;r++){let o=e.sel.ranges[r];i.push(new dn(mn(o.anchor,t),mn(o.head,t)))}return un(e.cm,i,e.sel.primIndex)}function gn(e,t,i){return e.line==t.line?ji(i.line,e.ch-t.ch+i.ch):ji(i.line+(e.line-t.line),e.ch)}function vn(e){e.doc.mode=Mi(e.options,e.doc.modeOption),bn(e)}function bn(e){e.doc.iter((e=>{e.stateAfter&&(e.stateAfter=null),e.styles&&(e.styles=null)})),e.doc.modeFrontier=e.doc.highlightFrontier=e.doc.first,Hs(e,100),e.state.modeGen++,e.curOp&&Qo(e)}function _n(e,t){return 0==t.from.ch&&0==t.to.ch&&""==Ot(t.text)&&(!e.cm||e.cm.options.wholeLineUpdateBefore)}function yn(e,t,i,r){function o(e){return i?i[e]:null}function s(e,i,o){!function(e,t,i,r){e.text=t,e.stateAfter&&(e.stateAfter=null),e.styles&&(e.styles=null),null!=e.order&&(e.order=null),gr(e),vr(e,i);let o=r?r(e):1;o!=e.height&&Oi(e,o)}(e,i,o,r),Kr(e,"change",e,t)}function n(e,t){let i=[];for(let s=e;s<t;++s)i.push(new Nr(c[s],o(s),r));return i}let a=t.from,l=t.to,c=t.text,d=Ni(e,a.line),u=Ni(e,l.line),h=Ot(c),p=o(c.length-1),m=l.line-a.line;if(t.full)e.insert(0,n(0,c.length)),e.remove(c.length,e.size-c.length);else if(_n(e,t)){let t=n(0,c.length-1);s(u,u.text,p),m&&e.remove(a.line,m),t.length&&e.insert(a.line,t)}else if(d==u)if(1==c.length)s(d,d.text.slice(0,a.ch)+h+d.text.slice(l.ch),p);else{let t=n(1,c.length-1);t.push(new Nr(h+d.text.slice(l.ch),p,r)),s(d,d.text.slice(0,a.ch)+c[0],o(0)),e.insert(a.line+1,t)}else if(1==c.length)s(d,d.text.slice(0,a.ch)+c[0]+u.text.slice(l.ch),o(0)),e.remove(a.line+1,m);else{s(d,d.text.slice(0,a.ch)+c[0],o(0)),s(u,h+u.text.slice(l.ch),p);let t=n(1,c.length-1);m>1&&e.remove(a.line+1,m-1),e.insert(a.line+1,t)}Kr(e,"change",e,t)}function xn(e,t,i){!function e(r,o,s){if(r.linked)for(let n=0;n<r.linked.length;++n){let a=r.linked[n];if(a.doc==o)continue;let l=s&&a.sharedHist;i&&!l||(t(a.doc,l),e(a.doc,r,l))}}(e,null,!0)}function wn(e,t){if(t.cm)throw new Error("This document is already in use.");e.doc=t,t.cm=e,Xo(e),vn(e),kn(e),e.options.lineWrapping||Ar(e),e.options.mode=t.modeOption,Qo(e)}function kn(e){("rtl"==e.doc.direction?xt:mt)(e.display.lineDiv,"CodeMirror-rtl")}function Sn(e){this.done=[],this.undone=[],this.undoDepth=e?e.undoDepth:1/0,this.lastModTime=this.lastSelTime=0,this.lastOp=this.lastSelOp=null,this.lastOrigin=this.lastSelOrigin=null,this.generation=this.maxGeneration=e?e.maxGeneration:1}function Tn(e,t){let i={from:Vi(t.from),to:pn(t),text:Ii(e,t.from,t.to)};return Ln(e,i,t.from.line,t.to.line+1),xn(e,(e=>Ln(e,i,t.from.line,t.to.line+1)),!0),i}function Cn(e){for(;e.length;){if(!Ot(e).ranges)break;e.pop()}}function Mn(e,t,i,r){let o=e.history;o.undone.length=0;let s,n,a=+new Date;if((o.lastOp==r||o.lastOrigin==t.origin&&t.origin&&("+"==t.origin.charAt(0)&&o.lastModTime>a-(e.cm?e.cm.options.historyEventDelay:500)||"*"==t.origin.charAt(0)))&&(s=function(e,t){return t?(Cn(e.done),Ot(e.done)):e.done.length&&!Ot(e.done).ranges?Ot(e.done):e.done.length>1&&!e.done[e.done.length-2].ranges?(e.done.pop(),Ot(e.done)):void 0}(o,o.lastOp==r)))n=Ot(s.changes),0==Hi(t.from,t.to)&&0==Hi(t.from,n.to)?n.to=pn(t):s.changes.push(Tn(e,t));else{let i=Ot(o.done);for(i&&i.ranges||$n(e.sel,o.done),s={changes:[Tn(e,t)],generation:o.generation},o.done.push(s);o.done.length>o.undoDepth;)o.done.shift(),o.done[0].ranges||o.done.shift()}o.done.push(i),o.generation=++o.maxGeneration,o.lastModTime=o.lastSelTime=a,o.lastOp=o.lastSelOp=r,o.lastOrigin=o.lastSelOrigin=t.origin,n||ri(e,"historyAdded")}function Pn(e,t,i,r){let o=e.history,s=r&&r.origin;i==o.lastSelOp||s&&o.lastSelOrigin==s&&(o.lastModTime==o.lastSelTime&&o.lastOrigin==s||function(e,t,i,r){let o=t.charAt(0);return"*"==o||"+"==o&&i.ranges.length==r.ranges.length&&i.somethingSelected()==r.somethingSelected()&&new Date-e.history.lastSelTime<=(e.cm?e.cm.options.historyEventDelay:500)}(e,s,Ot(o.done),t))?o.done[o.done.length-1]=t:$n(t,o.done),o.lastSelTime=+new Date,o.lastSelOrigin=s,o.lastSelOp=i,r&&!1!==r.clearRedo&&Cn(o.undone)}function $n(e,t){let i=Ot(t);i&&i.ranges&&i.equals(e)||t.push(e)}function Ln(e,t,i,r){let o=t["spans_"+e.id],s=0;e.iter(Math.max(e.first,i),Math.min(e.first+e.size,r),(i=>{i.markedSpans&&((o||(o=t["spans_"+e.id]={}))[s]=i.markedSpans),++s}))}function En(e){if(!e)return null;let t;for(let i=0;i<e.length;++i)e[i].marker.explicitlyCleared?t||(t=e.slice(0,i)):t&&t.push(e[i]);return t?t.length?t:null:e}function Rn(e,t){let i=function(e,t){let i=t["spans_"+e.id];if(!i)return null;let r=[];for(let e=0;e<t.text.length;++e)r.push(En(i[e]));return r}(e,t),r=mr(e,t);if(!i)return r;if(!r)return i;for(let e=0;e<i.length;++e){let t=i[e],o=r[e];if(t&&o)e:for(let e=0;e<o.length;++e){let i=o[e];for(let e=0;e<t.length;++e)if(t[e].marker==i.marker)continue e;t.push(i)}else o&&(i[e]=o)}return i}function An(e,t,i){let r=[];for(let s=0;s<e.length;++s){let n=e[s];if(n.ranges){r.push(i?cn.prototype.deepCopy.call(n):n);continue}let a=n.changes,l=[];r.push({changes:l});for(let e=0;e<a.length;++e){let i,r=a[e];if(l.push({from:r.from,to:r.to,text:r.text}),t)for(var o in r)(i=o.match(/^spans_(\d+)$/))&&Pt(t,Number(i[1]))>-1&&(Ot(l)[o]=r[o],delete r[o])}}return r}function Nn(e,t,i,r){if(r){let r=e.anchor;if(i){let e=Hi(t,r)<0;e!=Hi(i,r)<0?(r=t,t=i):e!=Hi(t,i)<0&&(t=i)}return new dn(r,t)}return new dn(i||t,t)}function In(e,t,i,r,o){null==o&&(o=e.cm&&(e.cm.display.shift||e.extend)),Wn(e,new cn([Nn(e.sel.primary(),t,i,o)],0),r)}function Dn(e,t,i){let r=[],o=e.cm&&(e.cm.display.shift||e.extend);for(let i=0;i<e.sel.ranges.length;i++)r[i]=Nn(e.sel.ranges[i],t[i],null,o);Wn(e,un(e.cm,r,e.sel.primIndex),i)}function On(e,t,i,r){let o=e.sel.ranges.slice(0);o[t]=i,Wn(e,un(e.cm,o,e.sel.primIndex),r)}function Fn(e,t,i,r){Wn(e,hn(t,i),r)}function zn(e,t,i){let r=e.history.done,o=Ot(r);o&&o.ranges?(r[r.length-1]=t,Bn(e,t,i)):Wn(e,t,i)}function Wn(e,t,i){Bn(e,t,i),Pn(e,e.sel,e.cm?e.cm.curOp.id:NaN,i)}function Bn(e,t,i){(ni(e,"beforeSelectionChange")||e.cm&&ni(e.cm,"beforeSelectionChange"))&&(t=function(e,t,i){let r={ranges:t.ranges,update:function(t){this.ranges=[];for(let i=0;i<t.length;i++)this.ranges[i]=new dn(Ki(e,t[i].anchor),Ki(e,t[i].head))},origin:i&&i.origin};return ri(e,"beforeSelectionChange",e,r),e.cm&&ri(e.cm,"beforeSelectionChange",e.cm,r),r.ranges!=t.ranges?un(e.cm,r.ranges,r.ranges.length-1):t}(e,t,i));let r=i&&i.bias||(Hi(t.primary().head,e.sel.primary().head)<0?-1:1);jn(e,Un(e,t,r,!0)),i&&!1===i.scroll||!e.cm||"nocursor"==e.cm.getOption("readOnly")||_s(e.cm)}function jn(e,t){t.equals(e.sel)||(e.sel=t,e.cm&&(e.cm.curOp.updateInput=1,e.cm.curOp.selectionChanged=!0,si(e.cm)),Kr(e,"cursorActivity",e))}function Hn(e){jn(e,Un(e,e.sel,null,!1))}function Un(e,t,i,r){let o;for(let s=0;s<t.ranges.length;s++){let n=t.ranges[s],a=t.ranges.length==e.sel.ranges.length&&e.sel.ranges[s],l=Gn(e,n.anchor,a&&a.anchor,i,r),c=Gn(e,n.head,a&&a.head,i,r);(o||l!=n.anchor||c!=n.head)&&(o||(o=t.ranges.slice(0,s)),o[s]=new dn(l,c))}return o?un(e.cm,o,t.primIndex):t}function Vn(e,t,i,r,o){let s=Ni(e,t.line);if(s.markedSpans)for(let n=0;n<s.markedSpans.length;++n){let a=s.markedSpans[n],l=a.marker,c="selectLeft"in l?!l.selectLeft:l.inclusiveLeft,d="selectRight"in l?!l.selectRight:l.inclusiveRight;if((null==a.from||(c?a.from<=t.ch:a.from<t.ch))&&(null==a.to||(d?a.to>=t.ch:a.to>t.ch))){if(o&&(ri(l,"beforeCursorEnter"),l.explicitlyCleared)){if(s.markedSpans){--n;continue}break}if(!l.atomic)continue;if(i){let n,a=l.find(r<0?1:-1);if((r<0?d:c)&&(a=qn(e,a,-r,a&&a.line==t.line?s:null)),a&&a.line==t.line&&(n=Hi(a,i))&&(r<0?n<0:n>0))return Vn(e,a,t,r,o)}let a=l.find(r<0?-1:1);return(r<0?c:d)&&(a=qn(e,a,r,a.line==t.line?s:null)),a?Vn(e,a,t,r,o):null}}return t}function Gn(e,t,i,r,o){let s=r||1,n=Vn(e,t,i,s,o)||!o&&Vn(e,t,i,s,!0)||Vn(e,t,i,-s,o)||!o&&Vn(e,t,i,-s,!0);return n||(e.cantEdit=!0,ji(e.first,0))}function qn(e,t,i,r){return i<0&&0==t.ch?t.line>e.first?Ki(e,ji(t.line-1)):null:i>0&&t.ch==(r||Ni(e,t.line)).text.length?t.line<e.first+e.size-1?ji(t.line+1,0):null:new ji(t.line,t.ch+i)}function Zn(e){e.setSelection(ji(e.firstLine(),0),ji(e.lastLine()),Et)}function Kn(e,t,i){let r={canceled:!1,from:t.from,to:t.to,text:t.text,origin:t.origin,cancel:()=>r.canceled=!0};return i&&(r.update=(t,i,o,s)=>{t&&(r.from=Ki(e,t)),i&&(r.to=Ki(e,i)),o&&(r.text=o),void 0!==s&&(r.origin=s)}),ri(e,"beforeChange",e,r),e.cm&&ri(e.cm,"beforeChange",e.cm,r),r.canceled?(e.cm&&(e.cm.curOp.updateInput=2),null):{from:r.from,to:r.to,text:r.text,origin:r.origin}}function Xn(e,t,i){if(e.cm){if(!e.cm.curOp)return Ws(e.cm,Xn)(e,t,i);if(e.cm.state.suppressEdits)return}if((ni(e,"beforeChange")||e.cm&&ni(e.cm,"beforeChange"))&&!(t=Kn(e,t,!0)))return;let r=cr&&!i&&function(e,t,i){let r=null;if(e.iter(t.line,i.line+1,(e=>{if(e.markedSpans)for(let t=0;t<e.markedSpans.length;++t){let i=e.markedSpans[t].marker;!i.readOnly||r&&-1!=Pt(r,i)||(r||(r=[])).push(i)}})),!r)return null;let o=[{from:t,to:i}];for(let e=0;e<r.length;++e){let t=r[e],i=t.find(0);for(let e=0;e<o.length;++e){let r=o[e];if(Hi(r.to,i.from)<0||Hi(r.from,i.to)>0)continue;let s=[e,1],n=Hi(r.from,i.from),a=Hi(r.to,i.to);(n<0||!t.inclusiveLeft&&!n)&&s.push({from:r.from,to:i.from}),(a>0||!t.inclusiveRight&&!a)&&s.push({from:i.to,to:r.to}),o.splice.apply(o,s),e+=s.length-3}}return o}(e,t.from,t.to);if(r)for(let i=r.length-1;i>=0;--i)Yn(e,{from:r[i].from,to:r[i].to,text:i?[""]:t.text,origin:t.origin});else Yn(e,t)}function Yn(e,t){if(1==t.text.length&&""==t.text[0]&&0==Hi(t.from,t.to))return;let i=fn(e,t);Mn(e,t,i,e.cm?e.cm.curOp.id:NaN),ea(e,t,i,mr(e,t));let r=[];xn(e,((e,i)=>{i||-1!=Pt(r,e.history)||(oa(e.history,t),r.push(e.history)),ea(e,t,null,mr(e,t))}))}function Jn(e,t,i){let r=e.cm&&e.cm.state.suppressEdits;if(r&&!i)return;let o,s=e.history,n=e.sel,a="undo"==t?s.done:s.undone,l="undo"==t?s.undone:s.done,c=0;for(;c<a.length&&(o=a[c],i?!o.ranges||o.equals(e.sel):o.ranges);c++);if(c==a.length)return;for(s.lastOrigin=s.lastSelOrigin=null;;){if(o=a.pop(),!o.ranges){if(r)return void a.push(o);break}if($n(o,l),i&&!o.equals(e.sel))return void Wn(e,o,{clearRedo:!1});n=o}let d=[];$n(n,l),l.push({changes:d,generation:s.generation}),s.generation=o.generation||++s.maxGeneration;let u=ni(e,"beforeChange")||e.cm&&ni(e.cm,"beforeChange");for(let i=o.changes.length-1;i>=0;--i){let r=o.changes[i];if(r.origin=t,u&&!Kn(e,r,!1))return void(a.length=0);d.push(Tn(e,r));let s=i?fn(e,r):Ot(a);ea(e,r,s,Rn(e,r)),!i&&e.cm&&e.cm.scrollIntoView({from:r.from,to:pn(r)});let n=[];xn(e,((e,t)=>{t||-1!=Pt(n,e.history)||(oa(e.history,r),n.push(e.history)),ea(e,r,null,Rn(e,r))}))}}function Qn(e,t){if(0!=t&&(e.first+=t,e.sel=new cn(Ft(e.sel.ranges,(e=>new dn(ji(e.anchor.line+t,e.anchor.ch),ji(e.head.line+t,e.head.ch)))),e.sel.primIndex),e.cm)){Qo(e.cm,e.first,e.first-t,t);for(let t=e.cm.display,i=t.viewFrom;i<t.viewTo;i++)es(e.cm,i,"gutter")}}function ea(e,t,i,r){if(e.cm&&!e.cm.curOp)return Ws(e.cm,ea)(e,t,i,r);if(t.to.line<e.first)return void Qn(e,t.text.length-1-(t.to.line-t.from.line));if(t.from.line>e.lastLine())return;if(t.from.line<e.first){let i=t.text.length-1-(e.first-t.from.line);Qn(e,i),t={from:ji(e.first,0),to:ji(t.to.line+i,t.to.ch),text:[Ot(t.text)],origin:t.origin}}let o=e.lastLine();t.to.line>o&&(t={from:t.from,to:ji(o,Ni(e,o).text.length),text:[t.text[0]],origin:t.origin}),t.removed=Ii(e,t.from,t.to),i||(i=fn(e,t)),e.cm?function(e,t,i){let r=e.doc,o=e.display,s=t.from,n=t.to,a=!1,l=s.line;e.options.lineWrapping||(l=Fi(Cr(Ni(r,s.line))),r.iter(l,n.line+1,(e=>{if(e==o.maxLine)return a=!0,!0})));r.sel.contains(t.from,t.to)>-1&&si(e);yn(r,t,i,Ko(e)),e.options.lineWrapping||(r.iter(l,s.line+t.text.length,(e=>{let t=Rr(e);t>o.maxLineLength&&(o.maxLine=e,o.maxLineLength=t,o.maxLineChanged=!0,a=!1)})),a&&(e.curOp.updateMaxLine=!0));(function(e,t){if(e.modeFrontier=Math.min(e.modeFrontier,t),e.highlightFrontier<t-10)return;let i=e.first;for(let r=t-1;r>i;r--){let o=Ni(e,r).stateAfter;if(o&&(!(o instanceof Yi)||r+o.lookAhead<t)){i=r+1;break}}e.highlightFrontier=Math.min(e.highlightFrontier,i)})(r,s.line),Hs(e,400);let c=t.text.length-(n.line-s.line)-1;t.full?Qo(e):s.line!=n.line||1!=t.text.length||_n(e.doc,t)?Qo(e,s.line,n.line+1,c):es(e,s.line,"text");let d=ni(e,"changes"),u=ni(e,"change");if(u||d){let i={from:s,to:n,text:t.text,removed:t.removed,origin:t.origin};u&&Kr(e,"change",e,i),d&&(e.curOp.changeObjs||(e.curOp.changeObjs=[])).push(i)}e.display.selForContextMenu=null}(e.cm,t,r):yn(e,t,r),Bn(e,i,Et),e.cantEdit&&Gn(e,ji(e.firstLine(),0))&&(e.cantEdit=!1)}function ta(e,t,i,r,o){r||(r=i),Hi(r,i)<0&&([i,r]=[r,i]),"string"==typeof t&&(t=e.splitLines(t)),Xn(e,{from:i,to:r,text:t,origin:o})}function ia(e,t,i,r){i<e.line?e.line+=r:t<e.line&&(e.line=t,e.ch=0)}function ra(e,t,i,r){for(let o=0;o<e.length;++o){let s=e[o],n=!0;if(s.ranges){s.copied||(s=e[o]=s.deepCopy(),s.copied=!0);for(let e=0;e<s.ranges.length;e++)ia(s.ranges[e].anchor,t,i,r),ia(s.ranges[e].head,t,i,r)}else{for(let e=0;e<s.changes.length;++e){let o=s.changes[e];if(i<o.from.line)o.from=ji(o.from.line+r,o.from.ch),o.to=ji(o.to.line+r,o.to.ch);else if(t<=o.to.line){n=!1;break}}n||(e.splice(0,o+1),o=0)}}}function oa(e,t){let i=t.from.line,r=t.to.line,o=t.text.length-(r-i)-1;ra(e.done,i,r,o),ra(e.undone,i,r,o)}function sa(e,t,i,r){let o=t,s=t;return"number"==typeof t?s=Ni(e,Zi(e,t)):o=Fi(t),null==o?null:(r(s,o)&&e.cm&&es(e.cm,o,i),s)}function na(e){this.lines=e,this.parent=null;let t=0;for(let i=0;i<e.length;++i)e[i].parent=this,t+=e[i].height;this.height=t}function aa(e){this.children=e;let t=0,i=0;for(let r=0;r<e.length;++r){let o=e[r];t+=o.chunkSize(),i+=o.height,o.parent=this}this.size=t,this.height=i,this.parent=null}na.prototype={chunkSize(){return this.lines.length},removeInner(e,t){for(let i=e,r=e+t;i<r;++i){let e=this.lines[i];this.height-=e.height,Ir(e),Kr(e,"delete")}this.lines.splice(e,t)},collapse(e){e.push.apply(e,this.lines)},insertInner(e,t,i){this.height+=i,this.lines=this.lines.slice(0,e).concat(t).concat(this.lines.slice(e));for(let e=0;e<t.length;++e)t[e].parent=this},iterN(e,t,i){for(let r=e+t;e<r;++e)if(i(this.lines[e]))return!0}},aa.prototype={chunkSize(){return this.size},removeInner(e,t){this.size-=t;for(let i=0;i<this.children.length;++i){let r=this.children[i],o=r.chunkSize();if(e<o){let s=Math.min(t,o-e),n=r.height;if(r.removeInner(e,s),this.height-=n-r.height,o==s&&(this.children.splice(i--,1),r.parent=null),0==(t-=s))break;e=0}else e-=o}if(this.size-t<25&&(this.children.length>1||!(this.children[0]instanceof na))){let e=[];this.collapse(e),this.children=[new na(e)],this.children[0].parent=this}},collapse(e){for(let t=0;t<this.children.length;++t)this.children[t].collapse(e)},insertInner(e,t,i){this.size+=t.length,this.height+=i;for(let r=0;r<this.children.length;++r){let o=this.children[r],s=o.chunkSize();if(e<=s){if(o.insertInner(e,t,i),o.lines&&o.lines.length>50){let e=o.lines.length%25+25;for(let t=e;t<o.lines.length;){let e=new na(o.lines.slice(t,t+=25));o.height-=e.height,this.children.splice(++r,0,e),e.parent=this}o.lines=o.lines.slice(0,e),this.maybeSpill()}break}e-=s}},maybeSpill(){if(this.children.length<=10)return;let e=this;do{let t=new aa(e.children.splice(e.children.length-5,5));if(e.parent){e.size-=t.size,e.height-=t.height;let i=Pt(e.parent.children,e);e.parent.children.splice(i+1,0,t)}else{let i=new aa(e.children);i.parent=e,e.children=[i,t],e=i}t.parent=e.parent}while(e.children.length>10);e.parent.maybeSpill()},iterN(e,t,i){for(let r=0;r<this.children.length;++r){let o=this.children[r],s=o.chunkSize();if(e<s){let r=Math.min(t,s-e);if(o.iterN(e,r,i))return!0;if(0==(t-=r))break;e=0}else e-=s}}};var la=class{constructor(e,t,i){if(i)for(let e in i)i.hasOwnProperty(e)&&(this[e]=i[e]);this.doc=e,this.node=t}clear(){let e=this.doc.cm,t=this.line.widgets,i=this.line,r=Fi(i);if(null==r||!t)return;for(let e=0;e<t.length;++e)t[e]==this&&t.splice(e--,1);t.length||(i.widgets=null);let o=lo(this);Oi(i,Math.max(0,i.height-o)),e&&(zs(e,(()=>{ca(e,i,-o),es(e,r,"widget")})),Kr(e,"lineWidgetCleared",e,this,r))}changed(){let e=this.height,t=this.doc.cm,i=this.line;this.height=null;let r=lo(this)-e;r&&($r(this.doc,i)||Oi(i,i.height+r),t&&zs(t,(()=>{t.curOp.forceUpdate=!0,ca(t,i,r),Kr(t,"lineWidgetChanged",t,this,Fi(i))})))}};function ca(e,t,i){Er(t)<(e.curOp&&e.curOp.scrollTop||e.doc.scrollTop)&&bs(e,i)}ai(la);var da=0,ua=class{constructor(e,t){this.lines=[],this.type=t,this.doc=e,this.id=++da}clear(){if(this.explicitlyCleared)return;let e=this.doc.cm,t=e&&!e.curOp;if(t&&Rs(e),ni(this,"clear")){let e=this.find();e&&Kr(this,"clear",e.from,e.to)}let i=null,r=null;for(let t=0;t<this.lines.length;++t){let o=this.lines[t],s=hr(o.markedSpans,this);e&&!this.collapsed?es(e,Fi(o),"text"):e&&(null!=s.to&&(r=Fi(o)),null!=s.from&&(i=Fi(o))),o.markedSpans=pr(o.markedSpans,s),null==s.from&&this.collapsed&&!$r(this.doc,o)&&e&&Oi(o,Vo(e.display))}if(e&&this.collapsed&&!e.options.lineWrapping)for(let t=0;t<this.lines.length;++t){let i=Cr(this.lines[t]),r=Rr(i);r>e.display.maxLineLength&&(e.display.maxLine=i,e.display.maxLineLength=r,e.display.maxLineChanged=!0)}null!=i&&e&&this.collapsed&&Qo(e,i,r+1),this.lines.length=0,this.explicitlyCleared=!0,this.atomic&&this.doc.cantEdit&&(this.doc.cantEdit=!1,e&&Hn(e.doc)),e&&Kr(e,"markerCleared",e,this,i,r),t&&As(e),this.parent&&this.parent.clear()}find(e,t){let i,r;null==e&&"bookmark"==this.type&&(e=1);for(let o=0;o<this.lines.length;++o){let s=this.lines[o],n=hr(s.markedSpans,this);if(null!=n.from&&(i=ji(t?s:Fi(s),n.from),-1==e))return i;if(null!=n.to&&(r=ji(t?s:Fi(s),n.to),1==e))return r}return i&&{from:i,to:r}}changed(){let e=this.find(-1,!0),t=this,i=this.doc.cm;e&&i&&zs(i,(()=>{let r=e.line,o=Fi(e.line),s=_o(i,o);if(s&&(Co(s),i.curOp.selectionChanged=i.curOp.forceUpdate=!0),i.curOp.updateMaxLine=!0,!$r(t.doc,r)&&null!=t.height){let e=t.height;t.height=null;let i=lo(t)-e;i&&Oi(r,r.height+i)}Kr(i,"markerChanged",i,this)}))}attachLine(e){if(!this.lines.length&&this.doc.cm){let e=this.doc.cm.curOp;e.maybeHiddenMarkers&&-1!=Pt(e.maybeHiddenMarkers,this)||(e.maybeUnhiddenMarkers||(e.maybeUnhiddenMarkers=[])).push(this)}this.lines.push(e)}detachLine(e){if(this.lines.splice(Pt(this.lines,e),1),!this.lines.length&&this.doc.cm){let e=this.doc.cm.curOp;(e.maybeHiddenMarkers||(e.maybeHiddenMarkers=[])).push(this)}}};function ha(e,t,i,r,o){if(r&&r.shared)return function(e,t,i,r,o){r=Tt(r),r.shared=!1;let s=[ha(e,t,i,r,o)],n=s[0],a=r.widgetNode;return xn(e,(e=>{a&&(r.widgetNode=a.cloneNode(!0)),s.push(ha(e,Ki(e,t),Ki(e,i),r,o));for(let t=0;t<e.linked.length;++t)if(e.linked[t].isParent)return;n=Ot(s)})),new pa(s,n)}(e,t,i,r,o);if(e.cm&&!e.cm.curOp)return Ws(e.cm,ha)(e,t,i,r,o);let s=new ua(e,o),n=Hi(t,i);if(r&&Tt(r,s,!1),n>0||0==n&&!1!==s.clearWhenEmpty)return s;if(s.replacedWith&&(s.collapsed=!0,s.widgetNode=bt("span",[s.replacedWith],"CodeMirror-widget"),r.handleMouseEvents||s.widgetNode.setAttribute("cm-ignore-events","true"),r.insertLeft&&(s.widgetNode.insertLeft=!0)),s.collapsed){if(Tr(e,t.line,t,i,s)||t.line!=i.line&&Tr(e,i.line,t,i,s))throw new Error("Inserting collapsed marker partially overlapping an existing one");dr=!0}s.addToHistory&&Mn(e,{from:t,to:i,origin:"markText"},e.sel,NaN);let a,l=t.line,c=e.cm;if(e.iter(l,i.line+1,(e=>{c&&s.collapsed&&!c.options.lineWrapping&&Cr(e)==c.display.maxLine&&(a=!0),s.collapsed&&l!=t.line&&Oi(e,0),function(e,t){e.markedSpans=e.markedSpans?e.markedSpans.concat([t]):[t],t.marker.attachLine(e)}(e,new ur(s,l==t.line?t.ch:null,l==i.line?i.ch:null)),++l})),s.collapsed&&e.iter(t.line,i.line+1,(t=>{$r(e,t)&&Oi(t,0)})),s.clearOnEnter&&ei(s,"beforeCursorEnter",(()=>s.clear())),s.readOnly&&(cr=!0,(e.history.done.length||e.history.undone.length)&&e.clearHistory()),s.collapsed&&(s.id=++da,s.atomic=!0),c){if(a&&(c.curOp.updateMaxLine=!0),s.collapsed)Qo(c,t.line,i.line+1);else if(s.className||s.startStyle||s.endStyle||s.css||s.attributes||s.title)for(let e=t.line;e<=i.line;e++)es(c,e,"text");s.atomic&&Hn(c.doc),Kr(c,"markerAdded",c,s)}return s}ai(ua);var pa=class{constructor(e,t){this.markers=e,this.primary=t;for(let t=0;t<e.length;++t)e[t].parent=this}clear(){if(!this.explicitlyCleared){this.explicitlyCleared=!0;for(let e=0;e<this.markers.length;++e)this.markers[e].clear();Kr(this,"clear")}}find(e,t){return this.primary.find(e,t)}};function ma(e){return e.findMarks(ji(e.first,0),e.clipPos(ji(e.lastLine())),(e=>e.parent))}function fa(e){for(let t=0;t<e.length;t++){let i=e[t],r=[i.primary.doc];xn(i.primary.doc,(e=>r.push(e)));for(let e=0;e<i.markers.length;e++){let t=i.markers[e];-1==Pt(r,t.doc)&&(t.parent=null,i.markers.splice(e--,1))}}}ai(pa);var ga=0,va=function(e,t,i,r,o){if(!(this instanceof va))return new va(e,t,i,r,o);null==i&&(i=0),aa.call(this,[new na([new Nr("",null)])]),this.first=i,this.scrollTop=this.scrollLeft=0,this.cantEdit=!1,this.cleanGeneration=1,this.modeFrontier=this.highlightFrontier=i;let s=ji(i,0);this.sel=hn(s),this.history=new Sn(null),this.id=++ga,this.modeOption=t,this.lineSep=r,this.direction="rtl"==o?"rtl":"ltr",this.extend=!1,"string"==typeof e&&(e=this.splitLines(e)),yn(this,{from:s,to:s,text:e}),Wn(this,hn(s),Et)};va.prototype=Wt(aa.prototype,{constructor:va,iter:function(e,t,i){i?this.iterN(e-this.first,t-e,i):this.iterN(this.first,this.first+this.size,e)},insert:function(e,t){let i=0;for(let e=0;e<t.length;++e)i+=t[e].height;this.insertInner(e-this.first,t,i)},remove:function(e,t){this.removeInner(e-this.first,t)},getValue:function(e){let t=Di(this,this.first,this.first+this.size);return!1===e?t:t.join(e||this.lineSeparator())},setValue:js((function(e){let t=ji(this.first,0),i=this.first+this.size-1;Xn(this,{from:t,to:ji(i,Ni(this,i).text.length),text:this.splitLines(e),origin:"setValue",full:!0},!0),this.cm&&ys(this.cm,0,0),Wn(this,hn(t),Et)})),replaceRange:function(e,t,i,r){ta(this,e,t=Ki(this,t),i=i?Ki(this,i):t,r)},getRange:function(e,t,i){let r=Ii(this,Ki(this,e),Ki(this,t));return!1===i?r:r.join(i||this.lineSeparator())},getLine:function(e){let t=this.getLineHandle(e);return t&&t.text},getLineHandle:function(e){if(Wi(this,e))return Ni(this,e)},getLineNumber:function(e){return Fi(e)},getLineHandleVisualStart:function(e){return"number"==typeof e&&(e=Ni(this,e)),Cr(e)},lineCount:function(){return this.size},firstLine:function(){return this.first},lastLine:function(){return this.first+this.size-1},clipPos:function(e){return Ki(this,e)},getCursor:function(e){let t,i=this.sel.primary();return t=null==e||"head"==e?i.head:"anchor"==e?i.anchor:"end"==e||"to"==e||!1===e?i.to():i.from(),t},listSelections:function(){return this.sel.ranges},somethingSelected:function(){return this.sel.somethingSelected()},setCursor:js((function(e,t,i){Fn(this,Ki(this,"number"==typeof e?ji(e,t||0):e),null,i)})),setSelection:js((function(e,t,i){Fn(this,Ki(this,e),Ki(this,t||e),i)})),extendSelection:js((function(e,t,i){In(this,Ki(this,e),t&&Ki(this,t),i)})),extendSelections:js((function(e,t){Dn(this,Xi(this,e),t)})),extendSelectionsBy:js((function(e,t){Dn(this,Xi(this,Ft(this.sel.ranges,e)),t)})),setSelections:js((function(e,t,i){if(!e.length)return;let r=[];for(let t=0;t<e.length;t++)r[t]=new dn(Ki(this,e[t].anchor),Ki(this,e[t].head||e[t].anchor));null==t&&(t=Math.min(e.length-1,this.sel.primIndex)),Wn(this,un(this.cm,r,t),i)})),addSelection:js((function(e,t,i){let r=this.sel.ranges.slice(0);r.push(new dn(Ki(this,e),Ki(this,t||e))),Wn(this,un(this.cm,r,r.length-1),i)})),getSelection:function(e){let t,i=this.sel.ranges;for(let e=0;e<i.length;e++){let r=Ii(this,i[e].from(),i[e].to());t=t?t.concat(r):r}return!1===e?t:t.join(e||this.lineSeparator())},getSelections:function(e){let t=[],i=this.sel.ranges;for(let r=0;r<i.length;r++){let o=Ii(this,i[r].from(),i[r].to());!1!==e&&(o=o.join(e||this.lineSeparator())),t[r]=o}return t},replaceSelection:function(e,t,i){let r=[];for(let t=0;t<this.sel.ranges.length;t++)r[t]=e;this.replaceSelections(r,t,i||"+input")},replaceSelections:js((function(e,t,i){let r=[],o=this.sel;for(let t=0;t<o.ranges.length;t++){let s=o.ranges[t];r[t]={from:s.from(),to:s.to(),text:this.splitLines(e[t]),origin:i}}let s=t&&"end"!=t&&function(e,t,i){let r=[],o=ji(e.first,0),s=o;for(let n=0;n<t.length;n++){let a=t[n],l=gn(a.from,o,s),c=gn(pn(a),o,s);if(o=a.to,s=c,"around"==i){let t=e.sel.ranges[n],i=Hi(t.head,t.anchor)<0;r[n]=new dn(i?c:l,i?l:c)}else r[n]=new dn(l,l)}return new cn(r,e.sel.primIndex)}(this,r,t);for(let e=r.length-1;e>=0;e--)Xn(this,r[e]);s?zn(this,s):this.cm&&_s(this.cm)})),undo:js((function(){Jn(this,"undo")})),redo:js((function(){Jn(this,"redo")})),undoSelection:js((function(){Jn(this,"undo",!0)})),redoSelection:js((function(){Jn(this,"redo",!0)})),setExtending:function(e){this.extend=e},getExtending:function(){return this.extend},historySize:function(){let e=this.history,t=0,i=0;for(let i=0;i<e.done.length;i++)e.done[i].ranges||++t;for(let t=0;t<e.undone.length;t++)e.undone[t].ranges||++i;return{undo:t,redo:i}},clearHistory:function(){this.history=new Sn(this.history),xn(this,(e=>e.history=this.history),!0)},markClean:function(){this.cleanGeneration=this.changeGeneration(!0)},changeGeneration:function(e){return e&&(this.history.lastOp=this.history.lastSelOp=this.history.lastOrigin=null),this.history.generation},isClean:function(e){return this.history.generation==(e||this.cleanGeneration)},getHistory:function(){return{done:An(this.history.done),undone:An(this.history.undone)}},setHistory:function(e){let t=this.history=new Sn(this.history);t.done=An(e.done.slice(0),null,!0),t.undone=An(e.undone.slice(0),null,!0)},setGutterMarker:js((function(e,t,i){return sa(this,e,"gutter",(e=>{let r=e.gutterMarkers||(e.gutterMarkers={});return r[t]=i,!i&&Ut(r)&&(e.gutterMarkers=null),!0}))})),clearGutter:js((function(e){this.iter((t=>{t.gutterMarkers&&t.gutterMarkers[e]&&sa(this,t,"gutter",(()=>(t.gutterMarkers[e]=null,Ut(t.gutterMarkers)&&(t.gutterMarkers=null),!0)))}))})),lineInfo:function(e){let t;if("number"==typeof e){if(!Wi(this,e))return null;if(t=e,!(e=Ni(this,e)))return null}else if(t=Fi(e),null==t)return null;return{line:t,handle:e,text:e.text,gutterMarkers:e.gutterMarkers,textClass:e.textClass,bgClass:e.bgClass,wrapClass:e.wrapClass,widgets:e.widgets}},addLineClass:js((function(e,t,i){return sa(this,e,"gutter"==t?"gutter":"class",(e=>{let r="text"==t?"textClass":"background"==t?"bgClass":"gutter"==t?"gutterClass":"wrapClass";if(e[r]){if(ht(i).test(e[r]))return!1;e[r]+=" "+i}else e[r]=i;return!0}))})),removeLineClass:js((function(e,t,i){return sa(this,e,"gutter"==t?"gutter":"class",(e=>{let r="text"==t?"textClass":"background"==t?"bgClass":"gutter"==t?"gutterClass":"wrapClass",o=e[r];if(!o)return!1;if(null==i)e[r]=null;else{let t=o.match(ht(i));if(!t)return!1;let s=t.index+t[0].length;e[r]=o.slice(0,t.index)+(t.index&&s!=o.length?" ":"")+o.slice(s)||null}return!0}))})),addLineWidget:js((function(e,t,i){return function(e,t,i,r){let o=new la(e,i,r),s=e.cm;return s&&o.noHScroll&&(s.display.alignWidgets=!0),sa(e,t,"widget",(t=>{let i=t.widgets||(t.widgets=[]);if(null==o.insertAt?i.push(o):i.splice(Math.min(i.length,Math.max(0,o.insertAt)),0,o),o.line=t,s&&!$r(e,t)){let i=Er(t)<e.scrollTop;Oi(t,t.height+lo(o)),i&&bs(s,o.height),s.curOp.forceUpdate=!0}return!0})),s&&Kr(s,"lineWidgetAdded",s,o,"number"==typeof t?t:Fi(t)),o}(this,e,t,i)})),removeLineWidget:function(e){e.clear()},markText:function(e,t,i){return ha(this,Ki(this,e),Ki(this,t),i,i&&i.type||"range")},setBookmark:function(e,t){let i={replacedWith:t&&(null==t.nodeType?t.widget:t),insertLeft:t&&t.insertLeft,clearWhenEmpty:!1,shared:t&&t.shared,handleMouseEvents:t&&t.handleMouseEvents};return ha(this,e=Ki(this,e),e,i,"bookmark")},findMarksAt:function(e){let t=[],i=Ni(this,(e=Ki(this,e)).line).markedSpans;if(i)for(let r=0;r<i.length;++r){let o=i[r];(null==o.from||o.from<=e.ch)&&(null==o.to||o.to>=e.ch)&&t.push(o.marker.parent||o.marker)}return t},findMarks:function(e,t,i){e=Ki(this,e),t=Ki(this,t);let r=[],o=e.line;return this.iter(e.line,t.line+1,(s=>{let n=s.markedSpans;if(n)for(let s=0;s<n.length;s++){let a=n[s];null!=a.to&&o==e.line&&e.ch>=a.to||null==a.from&&o!=e.line||null!=a.from&&o==t.line&&a.from>=t.ch||i&&!i(a.marker)||r.push(a.marker.parent||a.marker)}++o})),r},getAllMarks:function(){let e=[];return this.iter((t=>{let i=t.markedSpans;if(i)for(let t=0;t<i.length;++t)null!=i[t].from&&e.push(i[t].marker)})),e},posFromIndex:function(e){let t,i=this.first,r=this.lineSeparator().length;return this.iter((o=>{let s=o.text.length+r;if(s>e)return t=e,!0;e-=s,++i})),Ki(this,ji(i,t))},indexFromPos:function(e){let t=(e=Ki(this,e)).ch;if(e.line<this.first||e.ch<0)return 0;let i=this.lineSeparator().length;return this.iter(this.first,e.line,(e=>{t+=e.text.length+i})),t},copy:function(e){let t=new va(Di(this,this.first,this.first+this.size),this.modeOption,this.first,this.lineSep,this.direction);return t.scrollTop=this.scrollTop,t.scrollLeft=this.scrollLeft,t.sel=this.sel,t.extend=!1,e&&(t.history.undoDepth=this.history.undoDepth,t.setHistory(this.getHistory())),t},linkedDoc:function(e){e||(e={});let t=this.first,i=this.first+this.size;null!=e.from&&e.from>t&&(t=e.from),null!=e.to&&e.to<i&&(i=e.to);let r=new va(Di(this,t,i),e.mode||this.modeOption,t,this.lineSep,this.direction);return e.sharedHist&&(r.history=this.history),(this.linked||(this.linked=[])).push({doc:r,sharedHist:e.sharedHist}),r.linked=[{doc:this,isParent:!0,sharedHist:e.sharedHist}],function(e,t){for(let i=0;i<t.length;i++){let r=t[i],o=r.find(),s=e.clipPos(o.from),n=e.clipPos(o.to);if(Hi(s,n)){let t=ha(e,s,n,r.primary,r.primary.type);r.markers.push(t),t.parent=r}}}(r,ma(this)),r},unlinkDoc:function(e){if(e instanceof hl&&(e=e.doc),this.linked)for(let t=0;t<this.linked.length;++t){if(this.linked[t].doc==e){this.linked.splice(t,1),e.unlinkDoc(this),fa(ma(this));break}}if(e.history==this.history){let t=[e.id];xn(e,(e=>t.push(e.id)),!0),e.history=new Sn(null),e.history.done=An(this.history.done,t),e.history.undone=An(this.history.undone,t)}},iterLinkedDocs:function(e){xn(this,e)},getMode:function(){return this.mode},getEditor:function(){return this.cm},splitLines:function(e){return this.lineSep?e.split(this.lineSep):_i(e)},lineSeparator:function(){return this.lineSep||"\n"},setDirection:js((function(e){var t;("rtl"!=e&&(e="ltr"),e!=this.direction)&&(this.direction=e,this.iter((e=>e.order=null)),this.cm&&zs(t=this.cm,(()=>{kn(t),Qo(t)})))}))}),va.prototype.eachLine=va.prototype.iter;var ba=va,_a=0;function ya(e){let t=this;if(xa(t),oi(t,e)||co(t.display,e))return;li(e),Ze&&(_a=+new Date);let i=Yo(t,e,!0),r=e.dataTransfer.files;if(i&&!t.isReadOnly())if(r&&r.length&&window.FileReader&&window.File){let e=r.length,o=Array(e),s=0;const n=()=>{++s==e&&Ws(t,(()=>{i=Ki(t.doc,i);let e={from:i,to:i,text:t.doc.splitLines(o.filter((e=>null!=e)).join(t.doc.lineSeparator())),origin:"paste"};Xn(t.doc,e),zn(t.doc,hn(Ki(t.doc,i),Ki(t.doc,pn(e))))}))()},a=(e,i)=>{if(t.options.allowDropFileTypes&&-1==Pt(t.options.allowDropFileTypes,e.type))return void n();let r=new FileReader;r.onerror=()=>n(),r.onload=()=>{let e=r.result;/[\x00-\x08\x0e-\x1f]{2}/.test(e)||(o[i]=e),n()},r.readAsText(e)};for(let e=0;e<r.length;e++)a(r[e],e)}else{if(t.state.draggingText&&t.doc.sel.contains(i)>-1)return t.state.draggingText(e),void setTimeout((()=>t.display.input.focus()),20);try{let r=e.dataTransfer.getData("Text");if(r){let e;if(t.state.draggingText&&!t.state.draggingText.copy&&(e=t.listSelections()),Bn(t.doc,hn(i,i)),e)for(let i=0;i<e.length;++i)ta(t.doc,"",e[i].anchor,e[i].head,"drag");t.replaceSelection(r,"around","paste"),t.display.input.focus()}}catch(e){}}}function xa(e){e.display.dragCursor&&(e.display.lineSpace.removeChild(e.display.dragCursor),e.display.dragCursor=null)}function wa(e){if(!document.getElementsByClassName)return;let t=document.getElementsByClassName("CodeMirror"),i=[];for(let e=0;e<t.length;e++){let r=t[e].CodeMirror;r&&i.push(r)}i.length&&i[0].operation((()=>{for(let t=0;t<i.length;t++)e(i[t])}))}var ka=!1;function Sa(){ka||(!function(){let e;ei(window,"resize",(()=>{null==e&&(e=setTimeout((()=>{e=null,wa(Ta)}),100))})),ei(window,"blur",(()=>wa(ps)))}(),ka=!0)}function Ta(e){let t=e.display;t.cachedCharWidth=t.cachedTextHeight=t.cachedPaddingH=null,t.scrollbarsClipped=!1,e.setSize()}var Ca={3:"Pause",8:"Backspace",9:"Tab",13:"Enter",16:"Shift",17:"Ctrl",18:"Alt",19:"Pause",20:"CapsLock",27:"Esc",32:"Space",33:"PageUp",34:"PageDown",35:"End",36:"Home",37:"Left",38:"Up",39:"Right",40:"Down",44:"PrintScrn",45:"Insert",46:"Delete",59:";",61:"=",91:"Mod",92:"Mod",93:"Mod",106:"*",107:"=",109:"-",110:".",111:"/",145:"ScrollLock",173:"-",186:";",187:"=",188:",",189:"-",190:".",191:"/",192:"`",219:"[",220:"\\",221:"]",222:"'",224:"Mod",63232:"Up",63233:"Down",63234:"Left",63235:"Right",63272:"Delete",63273:"Home",63275:"End",63276:"PageUp",63277:"PageDown",63302:"Insert"};for(let e=0;e<10;e++)Ca[e+48]=Ca[e+96]=String(e);for(let e=65;e<=90;e++)Ca[e]=String.fromCharCode(e);for(let e=1;e<=12;e++)Ca[e+111]=Ca[e+63235]="F"+e;var Ma={};function Pa(e){let t,i,r,o,s=e.split(/-(?!$)/);e=s[s.length-1];for(let e=0;e<s.length-1;e++){let n=s[e];if(/^(cmd|meta|m)$/i.test(n))o=!0;else if(/^a(lt)?$/i.test(n))t=!0;else if(/^(c|ctrl|control)$/i.test(n))i=!0;else{if(!/^s(hift)?$/i.test(n))throw new Error("Unrecognized modifier name: "+n);r=!0}}return t&&(e="Alt-"+e),i&&(e="Ctrl-"+e),o&&(e="Cmd-"+e),r&&(e="Shift-"+e),e}function $a(e){let t={};for(let i in e)if(e.hasOwnProperty(i)){let r=e[i];if(/^(name|fallthrough|(de|at)tach)$/.test(i))continue;if("..."==r){delete e[i];continue}let o=Ft(i.split(" "),Pa);for(let e=0;e<o.length;e++){let i,s;e==o.length-1?(s=o.join(" "),i=r):(s=o.slice(0,e+1).join(" "),i="...");let n=t[s];if(n){if(n!=i)throw new Error("Inconsistent bindings for "+s)}else t[s]=i}delete e[i]}for(let i in t)e[i]=t[i];return e}function La(e,t,i,r){let o=(t=Na(t)).call?t.call(e,r):t[e];if(!1===o)return"nothing";if("..."===o)return"multi";if(null!=o&&i(o))return"handled";if(t.fallthrough){if("[object Array]"!=Object.prototype.toString.call(t.fallthrough))return La(e,t.fallthrough,i,r);for(let o=0;o<t.fallthrough.length;o++){let s=La(e,t.fallthrough[o],i,r);if(s)return s}}}function Ea(e){let t="string"==typeof e?e:Ca[e.keyCode];return"Ctrl"==t||"Alt"==t||"Shift"==t||"Mod"==t}function Ra(e,t,i){let r=e;return t.altKey&&"Alt"!=r&&(e="Alt-"+e),(dt?t.metaKey:t.ctrlKey)&&"Ctrl"!=r&&(e="Ctrl-"+e),(dt?t.ctrlKey:t.metaKey)&&"Mod"!=r&&(e="Cmd-"+e),!i&&t.shiftKey&&"Shift"!=r&&(e="Shift-"+e),e}function Aa(e,t){if(Qe&&34==e.keyCode&&e.char)return!1;let i=Ca[e.keyCode];return null!=i&&!e.altGraphKey&&(3==e.keyCode&&e.code&&(i=e.code),Ra(i,e,t))}function Na(e){return"string"==typeof e?Ma[e]:e}function Ia(e,t){let i=e.doc.sel.ranges,r=[];for(let e=0;e<i.length;e++){let o=t(i[e]);for(;r.length&&Hi(o.from,Ot(r).to)<=0;){let e=r.pop();if(Hi(e.from,o.from)<0){o.from=e.from;break}}r.push(o)}zs(e,(()=>{for(let t=r.length-1;t>=0;t--)ta(e.doc,"",r[t].from,r[t].to,"+delete");_s(e)}))}function Da(e,t,i){let r=qt(e.text,t+i,i);return r<0||r>e.text.length?null:r}function Oa(e,t,i){let r=Da(e,t.ch,i);return null==r?null:new ji(t.line,r,i<0?"after":"before")}function Fa(e,t,i,r,o){if(e){"rtl"==t.doc.direction&&(o=-o);let e=Jt(i,t.doc.direction);if(e){let s,n=o<0?Ot(e):e[0],a=o<0==(1==n.level)?"after":"before";if(n.level>0||"rtl"==t.doc.direction){let e=yo(t,i);s=o<0?i.text.length-1:0;let r=xo(t,e,s).top;s=Zt((i=>xo(t,e,i).top==r),o<0==(1==n.level)?n.from:n.to-1,s),"before"==a&&(s=Da(i,s,1))}else s=o<0?n.to:n.from;return new ji(r,s,a)}}return new ji(r,o<0?i.text.length:0,o<0?"before":"after")}Ma.basic={Left:"goCharLeft",Right:"goCharRight",Up:"goLineUp",Down:"goLineDown",End:"goLineEnd",Home:"goLineStartSmart",PageUp:"goPageUp",PageDown:"goPageDown",Delete:"delCharAfter",Backspace:"delCharBefore","Shift-Backspace":"delCharBefore",Tab:"defaultTab","Shift-Tab":"indentAuto",Enter:"newlineAndIndent",Insert:"toggleOverwrite",Esc:"singleSelection"},Ma.pcDefault={"Ctrl-A":"selectAll","Ctrl-D":"deleteLine","Ctrl-Z":"undo","Shift-Ctrl-Z":"redo","Ctrl-Y":"redo","Ctrl-Home":"goDocStart","Ctrl-End":"goDocEnd","Ctrl-Up":"goLineUp","Ctrl-Down":"goLineDown","Ctrl-Left":"goGroupLeft","Ctrl-Right":"goGroupRight","Alt-Left":"goLineStart","Alt-Right":"goLineEnd","Ctrl-Backspace":"delGroupBefore","Ctrl-Delete":"delGroupAfter","Ctrl-S":"save","Ctrl-F":"find","Ctrl-G":"findNext","Shift-Ctrl-G":"findPrev","Shift-Ctrl-F":"replace","Shift-Ctrl-R":"replaceAll","Ctrl-[":"indentLess","Ctrl-]":"indentMore","Ctrl-U":"undoSelection","Shift-Ctrl-U":"redoSelection","Alt-U":"redoSelection",fallthrough:"basic"},Ma.emacsy={"Ctrl-F":"goCharRight","Ctrl-B":"goCharLeft","Ctrl-P":"goLineUp","Ctrl-N":"goLineDown","Ctrl-A":"goLineStart","Ctrl-E":"goLineEnd","Ctrl-V":"goPageDown","Shift-Ctrl-V":"goPageUp","Ctrl-D":"delCharAfter","Ctrl-H":"delCharBefore","Alt-Backspace":"delWordBefore","Ctrl-K":"killLine","Ctrl-T":"transposeChars","Ctrl-O":"openLine"},Ma.macDefault={"Cmd-A":"selectAll","Cmd-D":"deleteLine","Cmd-Z":"undo","Shift-Cmd-Z":"redo","Cmd-Y":"redo","Cmd-Home":"goDocStart","Cmd-Up":"goDocStart","Cmd-End":"goDocEnd","Cmd-Down":"goDocEnd","Alt-Left":"goGroupLeft","Alt-Right":"goGroupRight","Cmd-Left":"goLineLeft","Cmd-Right":"goLineRight","Alt-Backspace":"delGroupBefore","Ctrl-Alt-Backspace":"delGroupAfter","Alt-Delete":"delGroupAfter","Cmd-S":"save","Cmd-F":"find","Cmd-G":"findNext","Shift-Cmd-G":"findPrev","Cmd-Alt-F":"replace","Shift-Cmd-Alt-F":"replaceAll","Cmd-[":"indentLess","Cmd-]":"indentMore","Cmd-Backspace":"delWrappedLineLeft","Cmd-Delete":"delWrappedLineRight","Cmd-U":"undoSelection","Shift-Cmd-U":"redoSelection","Ctrl-Up":"goDocStart","Ctrl-Down":"goDocEnd",fallthrough:["basic","emacsy"]},Ma.default=nt?Ma.macDefault:Ma.pcDefault;var za={selectAll:Zn,singleSelection:e=>e.setSelection(e.getCursor("anchor"),e.getCursor("head"),Et),killLine:e=>Ia(e,(t=>{if(t.empty()){let i=Ni(e.doc,t.head.line).text.length;return t.head.ch==i&&t.head.line<e.lastLine()?{from:t.head,to:ji(t.head.line+1,0)}:{from:t.head,to:ji(t.head.line,i)}}return{from:t.from(),to:t.to()}})),deleteLine:e=>Ia(e,(t=>({from:ji(t.from().line,0),to:Ki(e.doc,ji(t.to().line+1,0))}))),delLineLeft:e=>Ia(e,(e=>({from:ji(e.from().line,0),to:e.from()}))),delWrappedLineLeft:e=>Ia(e,(t=>{let i=e.charCoords(t.head,"div").top+5;return{from:e.coordsChar({left:0,top:i},"div"),to:t.from()}})),delWrappedLineRight:e=>Ia(e,(t=>{let i=e.charCoords(t.head,"div").top+5,r=e.coordsChar({left:e.display.lineDiv.offsetWidth+100,top:i},"div");return{from:t.from(),to:r}})),undo:e=>e.undo(),redo:e=>e.redo(),undoSelection:e=>e.undoSelection(),redoSelection:e=>e.redoSelection(),goDocStart:e=>e.extendSelection(ji(e.firstLine(),0)),goDocEnd:e=>e.extendSelection(ji(e.lastLine())),goLineStart:e=>e.extendSelectionsBy((t=>Wa(e,t.head.line)),{origin:"+move",bias:1}),goLineStartSmart:e=>e.extendSelectionsBy((t=>Ba(e,t.head)),{origin:"+move",bias:1}),goLineEnd:e=>e.extendSelectionsBy((t=>function(e,t){let i=Ni(e.doc,t),r=function(e){let t;for(;t=kr(e);)e=t.find(1,!0).line;return e}(i);r!=i&&(t=Fi(r));return Fa(!0,e,i,t,-1)}(e,t.head.line)),{origin:"+move",bias:-1}),goLineRight:e=>e.extendSelectionsBy((t=>{let i=e.cursorCoords(t.head,"div").top+5;return e.coordsChar({left:e.display.lineDiv.offsetWidth+100,top:i},"div")}),At),goLineLeft:e=>e.extendSelectionsBy((t=>{let i=e.cursorCoords(t.head,"div").top+5;return e.coordsChar({left:0,top:i},"div")}),At),goLineLeftSmart:e=>e.extendSelectionsBy((t=>{let i=e.cursorCoords(t.head,"div").top+5,r=e.coordsChar({left:0,top:i},"div");return r.ch<e.getLine(r.line).search(/\S/)?Ba(e,t.head):r}),At),goLineUp:e=>e.moveV(-1,"line"),goLineDown:e=>e.moveV(1,"line"),goPageUp:e=>e.moveV(-1,"page"),goPageDown:e=>e.moveV(1,"page"),goCharLeft:e=>e.moveH(-1,"char"),goCharRight:e=>e.moveH(1,"char"),goColumnLeft:e=>e.moveH(-1,"column"),goColumnRight:e=>e.moveH(1,"column"),goWordLeft:e=>e.moveH(-1,"word"),goGroupRight:e=>e.moveH(1,"group"),goGroupLeft:e=>e.moveH(-1,"group"),goWordRight:e=>e.moveH(1,"word"),delCharBefore:e=>e.deleteH(-1,"codepoint"),delCharAfter:e=>e.deleteH(1,"char"),delWordBefore:e=>e.deleteH(-1,"word"),delWordAfter:e=>e.deleteH(1,"word"),delGroupBefore:e=>e.deleteH(-1,"group"),delGroupAfter:e=>e.deleteH(1,"group"),indentAuto:e=>e.indentSelection("smart"),indentMore:e=>e.indentSelection("add"),indentLess:e=>e.indentSelection("subtract"),insertTab:e=>e.replaceSelection("\t"),insertSoftTab:e=>{let t=[],i=e.listSelections(),r=e.options.tabSize;for(let o=0;o<i.length;o++){let s=i[o].from(),n=Ct(e.getLine(s.line),s.ch,r);t.push(Dt(r-n%r))}e.replaceSelections(t)},defaultTab:e=>{e.somethingSelected()?e.indentSelection("add"):e.execCommand("insertTab")},transposeChars:e=>zs(e,(()=>{let t=e.listSelections(),i=[];for(let r=0;r<t.length;r++){if(!t[r].empty())continue;let o=t[r].head,s=Ni(e.doc,o.line).text;if(s)if(o.ch==s.length&&(o=new ji(o.line,o.ch-1)),o.ch>0)o=new ji(o.line,o.ch+1),e.replaceRange(s.charAt(o.ch-1)+s.charAt(o.ch-2),ji(o.line,o.ch-2),o,"+transpose");else if(o.line>e.doc.first){let t=Ni(e.doc,o.line-1).text;t&&(o=new ji(o.line,1),e.replaceRange(s.charAt(0)+e.doc.lineSeparator()+t.charAt(t.length-1),ji(o.line-1,t.length-1),o,"+transpose"))}i.push(new dn(o,o))}e.setSelections(i)})),newlineAndIndent:e=>zs(e,(()=>{let t=e.listSelections();for(let i=t.length-1;i>=0;i--)e.replaceRange(e.doc.lineSeparator(),t[i].anchor,t[i].head,"+input");t=e.listSelections();for(let i=0;i<t.length;i++)e.indentLine(t[i].from().line,null,!0);_s(e)})),openLine:e=>e.replaceSelection("\n","start"),toggleOverwrite:e=>e.toggleOverwrite()};function Wa(e,t){let i=Ni(e.doc,t),r=Cr(i);return r!=i&&(t=Fi(r)),Fa(!0,e,r,t,1)}function Ba(e,t){let i=Wa(e,t.line),r=Ni(e.doc,i.line),o=Jt(r,e.doc.direction);if(!o||0==o[0].level){let e=Math.max(i.ch,r.text.search(/\S/)),o=t.line==i.line&&t.ch<=e&&t.ch;return ji(i.line,o?0:e,i.sticky)}return i}function ja(e,t,i){if("string"==typeof t&&!(t=za[t]))return!1;e.display.input.ensurePolled();let r=e.display.shift,o=!1;try{e.isReadOnly()&&(e.state.suppressEdits=!0),i&&(e.display.shift=!1),o=t(e)!=Lt}finally{e.display.shift=r,e.state.suppressEdits=!1}return o}var Ha=new Mt;function Ua(e,t,i,r){let o=e.state.keySeq;if(o){if(Ea(t))return"handled";if(/\'$/.test(t)?e.state.keySeq=null:Ha.set(50,(()=>{e.state.keySeq==o&&(e.state.keySeq=null,e.display.input.reset())})),Va(e,o+" "+t,i,r))return!0}return Va(e,t,i,r)}function Va(e,t,i,r){let o=function(e,t,i){for(let r=0;r<e.state.keyMaps.length;r++){let o=La(t,e.state.keyMaps[r],i,e);if(o)return o}return e.options.extraKeys&&La(t,e.options.extraKeys,i,e)||La(t,e.options.keyMap,i,e)}(e,t,r);return"multi"==o&&(e.state.keySeq=t),"handled"==o&&Kr(e,"keyHandled",e,t,i),"handled"!=o&&"multi"!=o||(li(i),cs(e)),!!o}function Ga(e,t){let i=Aa(t,!0);return!!i&&(t.shiftKey&&!e.state.keySeq?Ua(e,"Shift-"+i,t,(t=>ja(e,t,!0)))||Ua(e,i,t,(t=>{if("string"==typeof t?/^go[A-Z]/.test(t):t.motion)return ja(e,t)})):Ua(e,i,t,(t=>ja(e,t))))}var qa=null;function Za(e){let t=this;if(e.target&&e.target!=t.display.input.getField())return;if(t.curOp.focus=yt(),oi(t,e))return;Ze&&Ke<11&&27==e.keyCode&&(e.returnValue=!1);let i=e.keyCode;t.display.shift=16==i||e.shiftKey;let r=Ga(t,e);Qe&&(qa=r?i:null,r||88!=i||xi||!(nt?e.metaKey:e.ctrlKey)||t.replaceSelection("",null,"cut")),Ue&&!nt&&!r&&46==i&&e.shiftKey&&!e.ctrlKey&&document.execCommand&&document.execCommand("cut"),18!=i||/\bCodeMirror-crosshair\b/.test(t.display.lineDiv.className)||function(e){let t=e.display.lineDiv;function i(e){18!=e.keyCode&&e.altKey||(mt(t,"CodeMirror-crosshair"),ii(document,"keyup",i),ii(document,"mouseover",i))}xt(t,"CodeMirror-crosshair"),ei(document,"keyup",i),ei(document,"mouseover",i)}(t)}function Ka(e){16==e.keyCode&&(this.doc.sel.shift=!1),oi(this,e)}function Xa(e){let t=this;if(e.target&&e.target!=t.display.input.getField())return;if(co(t.display,e)||oi(t,e)||e.ctrlKey&&!e.altKey||nt&&e.metaKey)return;let i=e.keyCode,r=e.charCode;if(Qe&&i==qa)return qa=null,void li(e);if(Qe&&(!e.which||e.which<10)&&Ga(t,e))return;let o=String.fromCharCode(null==r?i:r);"\b"!=o&&(function(e,t,i){return Ua(e,"'"+i+"'",t,(t=>ja(e,t,!0)))}(t,e,o)||t.display.input.onKeyPress(e))}var Ya,Ja,Qa=class{constructor(e,t,i){this.time=e,this.pos=t,this.button=i}compare(e,t,i){return this.time+400>e&&0==Hi(t,this.pos)&&i==this.button}};function el(e){let t=this,i=t.display;if(oi(t,e)||i.activeTouch&&i.input.supportsTouch())return;if(i.input.ensurePolled(),i.shift=e.shiftKey,co(i,e))return void(Xe||(i.scroller.draggable=!1,setTimeout((()=>i.scroller.draggable=!0),100)));if(rl(t,e))return;let r=Yo(t,e),o=pi(e),s=r?function(e,t){let i=+new Date;return Ja&&Ja.compare(i,e,t)?(Ya=Ja=null,"triple"):Ya&&Ya.compare(i,e,t)?(Ja=new Qa(i,e,t),Ya=null,"double"):(Ya=new Qa(i,e,t),Ja=null,"single")}(r,o):"single";window.focus(),1==o&&t.state.selectingText&&t.state.selectingText(e),r&&function(e,t,i,r,o){let s="Click";"double"==r?s="Double"+s:"triple"==r&&(s="Triple"+s);return s=(1==t?"Left":2==t?"Middle":"Right")+s,Ua(e,Ra(s,o),o,(t=>{if("string"==typeof t&&(t=za[t]),!t)return!1;let r=!1;try{e.isReadOnly()&&(e.state.suppressEdits=!0),r=t(e,i)!=Lt}finally{e.state.suppressEdits=!1}return r}))}(t,o,r,s,e)||(1==o?r?function(e,t,i,r){Ze?setTimeout(St(ds,e),0):e.curOp.focus=yt();let o,s=function(e,t,i){let r=e.getOption("configureMouse"),o=r?r(e,t,i):{};if(null==o.unit){let e=at?i.shiftKey&&i.metaKey:i.altKey;o.unit=e?"rectangle":"single"==t?"char":"double"==t?"word":"line"}(null==o.extend||e.doc.extend)&&(o.extend=e.doc.extend||i.shiftKey);null==o.addNew&&(o.addNew=nt?i.metaKey:i.ctrlKey);null==o.moveOnDrag&&(o.moveOnDrag=!(nt?i.altKey:i.ctrlKey));return o}(e,i,r),n=e.doc.sel;e.options.dragDrop&&gi&&!e.isReadOnly()&&"single"==i&&(o=n.contains(t))>-1&&(Hi((o=n.ranges[o]).from(),t)<0||t.xRel>0)&&(Hi(o.to(),t)>0||t.xRel<0)?function(e,t,i,r){let o=e.display,s=!1,n=Ws(e,(t=>{Xe&&(o.scroller.draggable=!1),e.state.draggingText=!1,e.state.delayingBlurEvent&&(e.hasFocus()?e.state.delayingBlurEvent=!1:us(e)),ii(o.wrapper.ownerDocument,"mouseup",n),ii(o.wrapper.ownerDocument,"mousemove",a),ii(o.scroller,"dragstart",l),ii(o.scroller,"drop",n),s||(li(t),r.addNew||In(e.doc,i,null,null,r.extend),Xe&&!et||Ze&&9==Ke?setTimeout((()=>{o.wrapper.ownerDocument.body.focus({preventScroll:!0}),o.input.focus()}),20):o.input.focus())})),a=function(e){s=s||Math.abs(t.clientX-e.clientX)+Math.abs(t.clientY-e.clientY)>=10},l=()=>s=!0;Xe&&(o.scroller.draggable=!0);e.state.draggingText=n,n.copy=!r.moveOnDrag,ei(o.wrapper.ownerDocument,"mouseup",n),ei(o.wrapper.ownerDocument,"mousemove",a),ei(o.scroller,"dragstart",l),ei(o.scroller,"drop",n),e.state.delayingBlurEvent=!0,setTimeout((()=>o.input.focus()),20),o.scroller.dragDrop&&o.scroller.dragDrop()}(e,r,t,s):function(e,t,i,r){Ze&&us(e);let o=e.display,s=e.doc;li(t);let n,a,l=s.sel,c=l.ranges;r.addNew&&!r.extend?(a=s.sel.contains(i),n=a>-1?c[a]:new dn(i,i)):(n=s.sel.primary(),a=s.sel.primIndex);if("rectangle"==r.unit)r.addNew||(n=new dn(i,i)),i=Yo(e,t,!0,!0),a=-1;else{let t=tl(e,i,r.unit);n=r.extend?Nn(n,t.anchor,t.head,r.extend):t}r.addNew?-1==a?(a=c.length,Wn(s,un(e,c.concat([n]),a),{scroll:!1,origin:"*mouse"})):c.length>1&&c[a].empty()&&"char"==r.unit&&!r.extend?(Wn(s,un(e,c.slice(0,a).concat(c.slice(a+1)),0),{scroll:!1,origin:"*mouse"}),l=s.sel):On(s,a,n,Rt):(a=0,Wn(s,new cn([n],0),Rt),l=s.sel);let d=i;function u(t){if(0!=Hi(d,t))if(d=t,"rectangle"==r.unit){let r=[],o=e.options.tabSize,n=Ct(Ni(s,i.line).text,i.ch,o),c=Ct(Ni(s,t.line).text,t.ch,o),d=Math.min(n,c),u=Math.max(n,c);for(let n=Math.min(i.line,t.line),a=Math.min(e.lastLine(),Math.max(i.line,t.line));n<=a;n++){let e=Ni(s,n).text,t=Nt(e,d,o);d==u?r.push(new dn(ji(n,t),ji(n,t))):e.length>t&&r.push(new dn(ji(n,t),ji(n,Nt(e,u,o))))}r.length||r.push(new dn(i,i)),Wn(s,un(e,l.ranges.slice(0,a).concat(r),a),{origin:"*mouse",scroll:!1}),e.scrollIntoView(t)}else{let i,o=n,c=tl(e,t,r.unit),d=o.anchor;Hi(c.anchor,d)>0?(i=c.head,d=qi(o.from(),c.anchor)):(i=c.anchor,d=Gi(o.to(),c.head));let u=l.ranges.slice(0);u[a]=function(e,t){let{anchor:i,head:r}=t,o=Ni(e.doc,i.line);if(0==Hi(i,r)&&i.sticky==r.sticky)return t;let s=Jt(o);if(!s)return t;let n=Xt(s,i.ch,i.sticky),a=s[n];if(a.from!=i.ch&&a.to!=i.ch)return t;let l,c=n+(a.from==i.ch==(1!=a.level)?0:1);if(0==c||c==s.length)return t;if(r.line!=i.line)l=(r.line-i.line)*("ltr"==e.doc.direction?1:-1)>0;else{let e=Xt(s,r.ch,r.sticky),t=e-n||(r.ch-i.ch)*(1==a.level?-1:1);l=e==c-1||e==c?t<0:t>0}let d=s[c+(l?-1:0)],u=l==(1==d.level),h=u?d.from:d.to,p=u?"after":"before";return i.ch==h&&i.sticky==p?t:new dn(new ji(i.line,h,p),r)}(e,new dn(Ki(s,d),i)),Wn(s,un(e,u,a),Rt)}}let h=o.wrapper.getBoundingClientRect(),p=0;function m(t){let i=++p,n=Yo(e,t,!0,"rectangle"==r.unit);if(n)if(0!=Hi(n,d)){e.curOp.focus=yt(),u(n);let r=gs(o,s);(n.line>=r.to||n.line<r.from)&&setTimeout(Ws(e,(()=>{p==i&&m(t)})),150)}else{let r=t.clientY<h.top?-20:t.clientY>h.bottom?20:0;r&&setTimeout(Ws(e,(()=>{p==i&&(o.scroller.scrollTop+=r,m(t))})),50)}}function f(t){e.state.selectingText=!1,p=1/0,t&&(li(t),o.input.focus()),ii(o.wrapper.ownerDocument,"mousemove",g),ii(o.wrapper.ownerDocument,"mouseup",v),s.history.lastSelOrigin=null}let g=Ws(e,(e=>{0!==e.buttons&&pi(e)?m(e):f(e)})),v=Ws(e,f);e.state.selectingText=v,ei(o.wrapper.ownerDocument,"mousemove",g),ei(o.wrapper.ownerDocument,"mouseup",v)}(e,r,t,s)}(t,r,s,e):hi(e)==i.scroller&&li(e):2==o?(r&&In(t.doc,r),setTimeout((()=>i.input.focus()),20)):3==o&&(ut?t.display.input.onContextMenu(e):us(t)))}function tl(e,t,i){if("char"==i)return new dn(t,t);if("word"==i)return e.findWordAt(t);if("line"==i)return new dn(ji(t.line,0),Ki(e.doc,ji(t.line+1,0)));let r=i(e,t);return new dn(r.from,r.to)}function il(e,t,i,r){let o,s;if(t.touches)o=t.touches[0].clientX,s=t.touches[0].clientY;else try{o=t.clientX,s=t.clientY}catch(e){return!1}if(o>=Math.floor(e.display.gutters.getBoundingClientRect().right))return!1;r&&li(t);let n=e.display,a=n.lineDiv.getBoundingClientRect();if(s>a.bottom||!ni(e,i))return di(t);s-=a.top-n.viewOffset;for(let r=0;r<e.display.gutterSpecs.length;++r){let a=n.gutters.childNodes[r];if(a&&a.getBoundingClientRect().right>=o){return ri(e,i,e,zi(e.doc,s),e.display.gutterSpecs[r].className,t),di(t)}}}function rl(e,t){return il(e,t,"gutterClick",!0)}function ol(e,t){co(e.display,t)||function(e,t){return!!ni(e,"gutterContextMenu")&&il(e,t,"gutterContextMenu",!1)}(e,t)||oi(e,t,"contextmenu")||ut||e.display.input.onContextMenu(t)}function sl(e){e.display.wrapper.className=e.display.wrapper.className.replace(/\s*cm-s-\S+/g,"")+e.options.theme.replace(/(^|\s)\s*/g," cm-s-"),Po(e)}var nl={toString:function(){return"CodeMirror.Init"}},al={},ll={};function cl(e,t,i){if(!t!=!(i&&i!=nl)){let i=e.display.dragFunctions,r=t?ei:ii;r(e.display.scroller,"dragstart",i.start),r(e.display.scroller,"dragenter",i.enter),r(e.display.scroller,"dragover",i.over),r(e.display.scroller,"dragleave",i.leave),r(e.display.scroller,"drop",i.drop)}}function dl(e){e.options.lineWrapping?(xt(e.display.wrapper,"CodeMirror-wrap"),e.display.sizer.style.minWidth="",e.display.sizerWidth=null):(mt(e.display.wrapper,"CodeMirror-wrap"),Ar(e)),Xo(e),Qo(e),Po(e),setTimeout((()=>Ms(e)),100)}function ul(e,t){if(!(this instanceof ul))return new ul(e,t);this.options=t=t?Tt(t):{},Tt(al,t,!1);let i=t.value;"string"==typeof i?i=new ba(i,t.mode,null,t.lineSeparator,t.direction):t.mode&&(i.modeOption=t.mode),this.doc=i;let r=new ul.inputStyles[t.inputStyle](this),o=this.display=new rn(e,i,r,t);o.wrapper.CodeMirror=this,sl(this),t.lineWrapping&&(this.display.wrapper.className+=" CodeMirror-wrap"),Ls(this),this.state={keyMaps:[],overlays:[],modeGen:0,overwrite:!1,delayingBlurEvent:!1,focused:!1,suppressEdits:!1,pasteIncoming:-1,cutIncoming:-1,selectingText:!1,draggingText:!1,highlight:new Mt,keySeq:null,specialChars:null},t.autofocus&&!st&&o.input.focus(),Ze&&Ke<11&&setTimeout((()=>this.display.input.reset(!0)),20),function(e){let t=e.display;ei(t.scroller,"mousedown",Ws(e,el)),ei(t.scroller,"dblclick",Ze&&Ke<11?Ws(e,(t=>{if(oi(e,t))return;let i=Yo(e,t);if(!i||rl(e,t)||co(e.display,t))return;li(t);let r=e.findWordAt(i);In(e.doc,r.anchor,r.head)})):t=>oi(e,t)||li(t));ei(t.scroller,"contextmenu",(t=>ol(e,t))),ei(t.input.getField(),"contextmenu",(i=>{t.scroller.contains(i.target)||ol(e,i)}));let i,r={end:0};function o(){t.activeTouch&&(i=setTimeout((()=>t.activeTouch=null),1e3),r=t.activeTouch,r.end=+new Date)}function s(e){if(1!=e.touches.length)return!1;let t=e.touches[0];return t.radiusX<=1&&t.radiusY<=1}function n(e,t){if(null==t.left)return!0;let i=t.left-e.left,r=t.top-e.top;return i*i+r*r>400}ei(t.scroller,"touchstart",(o=>{if(!oi(e,o)&&!s(o)&&!rl(e,o)){t.input.ensurePolled(),clearTimeout(i);let e=+new Date;t.activeTouch={start:e,moved:!1,prev:e-r.end<=300?r:null},1==o.touches.length&&(t.activeTouch.left=o.touches[0].pageX,t.activeTouch.top=o.touches[0].pageY)}})),ei(t.scroller,"touchmove",(()=>{t.activeTouch&&(t.activeTouch.moved=!0)})),ei(t.scroller,"touchend",(i=>{let r=t.activeTouch;if(r&&!co(t,i)&&null!=r.left&&!r.moved&&new Date-r.start<300){let o,s=e.coordsChar(t.activeTouch,"page");o=!r.prev||n(r,r.prev)?new dn(s,s):!r.prev.prev||n(r,r.prev.prev)?e.findWordAt(s):new dn(ji(s.line,0),Ki(e.doc,ji(s.line+1,0))),e.setSelection(o.anchor,o.head),e.focus(),li(i)}o()})),ei(t.scroller,"touchcancel",o),ei(t.scroller,"scroll",(()=>{t.scroller.clientHeight&&(ks(e,t.scroller.scrollTop),Ts(e,t.scroller.scrollLeft,!0),ri(e,"scroll",e))})),ei(t.scroller,"mousewheel",(t=>ln(e,t))),ei(t.scroller,"DOMMouseScroll",(t=>ln(e,t))),ei(t.wrapper,"scroll",(()=>t.wrapper.scrollTop=t.wrapper.scrollLeft=0)),t.dragFunctions={enter:t=>{oi(e,t)||ui(t)},over:t=>{oi(e,t)||(!function(e,t){let i=Yo(e,t);if(!i)return;let r=document.createDocumentFragment();ns(e,i,r),e.display.dragCursor||(e.display.dragCursor=vt("div",null,"CodeMirror-cursors CodeMirror-dragcursors"),e.display.lineSpace.insertBefore(e.display.dragCursor,e.display.cursorDiv)),gt(e.display.dragCursor,r)}(e,t),ui(t))},start:t=>function(e,t){if(Ze&&(!e.state.draggingText||+new Date-_a<100))ui(t);else if(!oi(e,t)&&!co(e.display,t)&&(t.dataTransfer.setData("Text",e.getSelection()),t.dataTransfer.effectAllowed="copyMove",t.dataTransfer.setDragImage&&!et)){let i=vt("img",null,null,"position: fixed; left: 0; top: 0;");i.src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==",Qe&&(i.width=i.height=1,e.display.wrapper.appendChild(i),i._top=i.offsetTop),t.dataTransfer.setDragImage(i,0,0),Qe&&i.parentNode.removeChild(i)}}(e,t),drop:Ws(e,ya),leave:t=>{oi(e,t)||xa(e)}};let a=t.input.getField();ei(a,"keyup",(t=>Ka.call(e,t))),ei(a,"keydown",Ws(e,Za)),ei(a,"keypress",Ws(e,Xa)),ei(a,"focus",(t=>hs(e,t))),ei(a,"blur",(t=>ps(e,t)))}(this),Sa(),Rs(this),this.curOp.forceUpdate=!0,wn(this,i),t.autofocus&&!st||this.hasFocus()?setTimeout((()=>{this.hasFocus()&&!this.state.focused&&hs(this)}),20):ps(this);for(let e in ll)ll.hasOwnProperty(e)&&ll[e](this,t[e],nl);Js(this),t.finishInit&&t.finishInit(this);for(let e=0;e<pl.length;++e)pl[e](this);As(this),Xe&&t.lineWrapping&&"optimizelegibility"==getComputedStyle(o.lineDiv).textRendering&&(o.lineDiv.style.textRendering="auto")}ul.defaults=al,ul.optionHandlers=ll;var hl=ul;var pl=[];function ml(e,t,i,r){let o,s=e.doc;null==i&&(i="add"),"smart"==i&&(s.mode.indent?o=tr(e,t).state:i="prev");let n=e.options.tabSize,a=Ni(s,t),l=Ct(a.text,null,n);a.stateAfter&&(a.stateAfter=null);let c,d=a.text.match(/^\s*/)[0];if(r||/\S/.test(a.text)){if("smart"==i&&(c=s.mode.indent(o,a.text.slice(d.length),a.text),c==Lt||c>150)){if(!r)return;i="prev"}}else c=0,i="not";"prev"==i?c=t>s.first?Ct(Ni(s,t-1).text,null,n):0:"add"==i?c=l+e.options.indentUnit:"subtract"==i?c=l-e.options.indentUnit:"number"==typeof i&&(c=l+i),c=Math.max(0,c);let u="",h=0;if(e.options.indentWithTabs)for(let e=Math.floor(c/n);e;--e)h+=n,u+="\t";if(h<c&&(u+=Dt(c-h)),u!=d)return ta(s,u,ji(t,0),ji(t,d.length),"+input"),a.stateAfter=null,!0;for(let e=0;e<s.sel.ranges.length;e++){let i=s.sel.ranges[e];if(i.head.line==t&&i.head.ch<d.length){let i=ji(t,d.length);On(s,e,new dn(i,i));break}}}ul.defineInitHook=e=>pl.push(e);var fl=null;function gl(e){fl=e}function vl(e,t,i,r,o){let s=e.doc;e.display.shift=!1,r||(r=s.sel);let n=+new Date-200,a="paste"==o||e.state.pasteIncoming>n,l=_i(t),c=null;if(a&&r.ranges.length>1)if(fl&&fl.text.join("\n")==t){if(r.ranges.length%fl.text.length==0){c=[];for(let e=0;e<fl.text.length;e++)c.push(s.splitLines(fl.text[e]))}}else l.length==r.ranges.length&&e.options.pasteLinesPerSelection&&(c=Ft(l,(e=>[e])));let d=e.curOp.updateInput;for(let t=r.ranges.length-1;t>=0;t--){let d=r.ranges[t],u=d.from(),h=d.to();d.empty()&&(i&&i>0?u=ji(u.line,u.ch-i):e.state.overwrite&&!a?h=ji(h.line,Math.min(Ni(s,h.line).text.length,h.ch+Ot(l).length)):a&&fl&&fl.lineWise&&fl.text.join("\n")==l.join("\n")&&(u=h=ji(u.line,0)));let p={from:u,to:h,text:c?c[t%c.length]:l,origin:o||(a?"paste":e.state.cutIncoming>n?"cut":"+input")};Xn(e.doc,p),Kr(e,"inputRead",e,p)}t&&!a&&_l(e,t),_s(e),e.curOp.updateInput<2&&(e.curOp.updateInput=d),e.curOp.typing=!0,e.state.pasteIncoming=e.state.cutIncoming=-1}function bl(e,t){let i=e.clipboardData&&e.clipboardData.getData("Text");if(i)return e.preventDefault(),t.isReadOnly()||t.options.disableInput||zs(t,(()=>vl(t,i,0,null,"paste"))),!0}function _l(e,t){if(!e.options.electricChars||!e.options.smartIndent)return;let i=e.doc.sel;for(let r=i.ranges.length-1;r>=0;r--){let o=i.ranges[r];if(o.head.ch>100||r&&i.ranges[r-1].head.line==o.head.line)continue;let s=e.getModeAt(o.head),n=!1;if(s.electricChars){for(let i=0;i<s.electricChars.length;i++)if(t.indexOf(s.electricChars.charAt(i))>-1){n=ml(e,o.head.line,"smart");break}}else s.electricInput&&s.electricInput.test(Ni(e.doc,o.head.line).text.slice(0,o.head.ch))&&(n=ml(e,o.head.line,"smart"));n&&Kr(e,"electricInput",e,o.head.line)}}function yl(e){let t=[],i=[];for(let r=0;r<e.doc.sel.ranges.length;r++){let o=e.doc.sel.ranges[r].head.line,s={anchor:ji(o,0),head:ji(o+1,0)};i.push(s),t.push(e.getRange(s.anchor,s.head))}return{text:t,ranges:i}}function xl(e,t,i,r){e.setAttribute("autocorrect",i?"":"off"),e.setAttribute("autocapitalize",r?"":"off"),e.setAttribute("spellcheck",!!t)}function wl(){let e=vt("textarea",null,null,"position: absolute; bottom: -1em; padding: 0; width: 1px; height: 1em; outline: none"),t=vt("div",[e],null,"overflow: hidden; position: relative; width: 3px; height: 0px;");return Xe?e.style.width="1000px":e.setAttribute("wrap","off"),rt&&(e.style.border="1px solid black"),xl(e),t}function kl(e,t,i,r,o){let s=t,n=i,a=Ni(e,t.line),l=o&&"rtl"==e.direction?-i:i;function c(s){let n;if("codepoint"==r){let e=a.text.charCodeAt(t.ch+(i>0?0:-1));if(isNaN(e))n=null;else{let r=i>0?e>=55296&&e<56320:e>=56320&&e<57343;n=new ji(t.line,Math.max(0,Math.min(a.text.length,t.ch+i*(r?2:1))),-i)}}else n=o?function(e,t,i,r){let o=Jt(t,e.doc.direction);if(!o)return Oa(t,i,r);i.ch>=t.text.length?(i.ch=t.text.length,i.sticky="before"):i.ch<=0&&(i.ch=0,i.sticky="after");let s=Xt(o,i.ch,i.sticky),n=o[s];if("ltr"==e.doc.direction&&n.level%2==0&&(r>0?n.to>i.ch:n.from<i.ch))return Oa(t,i,r);let a,l=(e,i)=>Da(t,e instanceof ji?e.ch:e,i),c=i=>e.options.lineWrapping?(a=a||yo(e,t),Wo(e,t,a,i)):{begin:0,end:t.text.length},d=c("before"==i.sticky?l(i,-1):i.ch);if("rtl"==e.doc.direction||1==n.level){let e=1==n.level==r<0,t=l(i,e?1:-1);if(null!=t&&(e?t<=n.to&&t<=d.end:t>=n.from&&t>=d.begin)){let r=e?"before":"after";return new ji(i.line,t,r)}}let u=(e,t,r)=>{let s=(e,t)=>t?new ji(i.line,l(e,1),"before"):new ji(i.line,e,"after");for(;e>=0&&e<o.length;e+=t){let i=o[e],n=t>0==(1!=i.level),a=n?r.begin:l(r.end,-1);if(i.from<=a&&a<i.to)return s(a,n);if(a=n?i.from:l(i.to,-1),r.begin<=a&&a<r.end)return s(a,n)}},h=u(s+r,r,d);if(h)return h;let p=r>0?d.end:l(d.begin,-1);return null==p||r>0&&p==t.text.length||(h=u(r>0?0:o.length-1,r,c(p)),!h)?null:h}(e.cm,a,t,i):Oa(a,t,i);if(null==n){if(s||!function(){let i=t.line+l;return!(i<e.first||i>=e.first+e.size)&&(t=new ji(i,t.ch,t.sticky),a=Ni(e,i))}())return!1;t=Fa(o,e.cm,a,t.line,l)}else t=n;return!0}if("char"==r||"codepoint"==r)c();else if("column"==r)c(!0);else if("word"==r||"group"==r){let o=null,s="group"==r,n=e.cm&&e.cm.getHelper(t,"wordChars");for(let e=!0;!(i<0)||c(!e);e=!1){let r=a.text.charAt(t.ch)||"\n",l=Ht(r,n)?"w":s&&"\n"==r?"n":!s||/\s/.test(r)?null:"p";if(!s||e||l||(l="s"),o&&o!=l){i<0&&(i=1,c(),t.sticky="after");break}if(l&&(o=l),i>0&&!c(!e))break}}let d=Gn(e,t,s,n,!0);return Ui(s,d)&&(d.hitSide=!0),d}function Sl(e,t,i,r){let o,s,n=e.doc,a=t.left;if("page"==r){let r=Math.min(e.display.wrapper.clientHeight,window.innerHeight||document.documentElement.clientHeight),s=Math.max(r-.5*Vo(e.display),3);o=(i>0?t.bottom:t.top)+i*s}else"line"==r&&(o=i>0?t.bottom+3:t.top-3);for(;s=Fo(e,a,o),s.outside;){if(i<0?o<=0:o>=n.height){s.hitSide=!0;break}o+=5*i}return s}var Tl=class{constructor(e){this.cm=e,this.lastAnchorNode=this.lastAnchorOffset=this.lastFocusNode=this.lastFocusOffset=null,this.polling=new Mt,this.composing=null,this.gracePeriod=!1,this.readDOMTimeout=null}init(e){let t=this,i=t.cm,r=t.div=e.lineDiv;function o(e){for(let t=e.target;t;t=t.parentNode){if(t==r)return!0;if(/\bCodeMirror-(?:line)?widget\b/.test(t.className))break}return!1}function s(e){if(!o(e)||oi(i,e))return;if(i.somethingSelected())gl({lineWise:!1,text:i.getSelections()}),"cut"==e.type&&i.replaceSelection("",null,"cut");else{if(!i.options.lineWiseCopyCut)return;{let t=yl(i);gl({lineWise:!0,text:t.text}),"cut"==e.type&&i.operation((()=>{i.setSelections(t.ranges,0,Et),i.replaceSelection("",null,"cut")}))}}if(e.clipboardData){e.clipboardData.clearData();let t=fl.text.join("\n");if(e.clipboardData.setData("Text",t),e.clipboardData.getData("Text")==t)return void e.preventDefault()}let s=wl(),n=s.firstChild;i.display.lineSpace.insertBefore(s,i.display.lineSpace.firstChild),n.value=fl.text.join("\n");let a=yt();kt(n),setTimeout((()=>{i.display.lineSpace.removeChild(s),a.focus(),a==r&&t.showPrimarySelection()}),50)}r.contentEditable=!0,xl(r,i.options.spellcheck,i.options.autocorrect,i.options.autocapitalize),ei(r,"paste",(e=>{!o(e)||oi(i,e)||bl(e,i)||Ke<=11&&setTimeout(Ws(i,(()=>this.updateFromDOM())),20)})),ei(r,"compositionstart",(e=>{this.composing={data:e.data,done:!1}})),ei(r,"compositionupdate",(e=>{this.composing||(this.composing={data:e.data,done:!1})})),ei(r,"compositionend",(e=>{this.composing&&(e.data!=this.composing.data&&this.readFromDOMSoon(),this.composing.done=!0)})),ei(r,"touchstart",(()=>t.forceCompositionEnd())),ei(r,"input",(()=>{this.composing||this.readFromDOMSoon()})),ei(r,"copy",s),ei(r,"cut",s)}screenReaderLabelChanged(e){e?this.div.setAttribute("aria-label",e):this.div.removeAttribute("aria-label")}prepareSelection(){let e=ss(this.cm,!1);return e.focus=yt()==this.div,e}showSelection(e,t){e&&this.cm.display.view.length&&((e.focus||t)&&this.showPrimarySelection(),this.showMultipleSelections(e))}getSelection(){return this.cm.display.wrapper.ownerDocument.getSelection()}showPrimarySelection(){let e=this.getSelection(),t=this.cm,i=t.doc.sel.primary(),r=i.from(),o=i.to();if(t.display.viewTo==t.display.viewFrom||r.line>=t.display.viewTo||o.line<t.display.viewFrom)return void e.removeAllRanges();let s=$l(t,e.anchorNode,e.anchorOffset),n=$l(t,e.focusNode,e.focusOffset);if(s&&!s.bad&&n&&!n.bad&&0==Hi(qi(s,n),r)&&0==Hi(Gi(s,n),o))return;let a=t.display.view,l=r.line>=t.display.viewFrom&&Ml(t,r)||{node:a[0].measure.map[2],offset:0},c=o.line<t.display.viewTo&&Ml(t,o);if(!c){let e=a[a.length-1].measure,t=e.maps?e.maps[e.maps.length-1]:e.map;c={node:t[t.length-1],offset:t[t.length-2]-t[t.length-3]}}if(!l||!c)return void e.removeAllRanges();let d,u=e.rangeCount&&e.getRangeAt(0);try{d=pt(l.node,l.offset,c.offset,c.node)}catch(e){}d&&(!Ue&&t.state.focused?(e.collapse(l.node,l.offset),d.collapsed||(e.removeAllRanges(),e.addRange(d))):(e.removeAllRanges(),e.addRange(d)),u&&null==e.anchorNode?e.addRange(u):Ue&&this.startGracePeriod()),this.rememberSelection()}startGracePeriod(){clearTimeout(this.gracePeriod),this.gracePeriod=setTimeout((()=>{this.gracePeriod=!1,this.selectionChanged()&&this.cm.operation((()=>this.cm.curOp.selectionChanged=!0))}),20)}showMultipleSelections(e){gt(this.cm.display.cursorDiv,e.cursors),gt(this.cm.display.selectionDiv,e.selection)}rememberSelection(){let e=this.getSelection();this.lastAnchorNode=e.anchorNode,this.lastAnchorOffset=e.anchorOffset,this.lastFocusNode=e.focusNode,this.lastFocusOffset=e.focusOffset}selectionInEditor(){let e=this.getSelection();if(!e.rangeCount)return!1;let t=e.getRangeAt(0).commonAncestorContainer;return _t(this.div,t)}focus(){"nocursor"!=this.cm.options.readOnly&&(this.selectionInEditor()&&yt()==this.div||this.showSelection(this.prepareSelection(),!0),this.div.focus())}blur(){this.div.blur()}getField(){return this.div}supportsTouch(){return!0}receivedFocus(){let e=this;this.selectionInEditor()?this.pollSelection():zs(this.cm,(()=>e.cm.curOp.selectionChanged=!0)),this.polling.set(this.cm.options.pollInterval,(function t(){e.cm.state.focused&&(e.pollSelection(),e.polling.set(e.cm.options.pollInterval,t))}))}selectionChanged(){let e=this.getSelection();return e.anchorNode!=this.lastAnchorNode||e.anchorOffset!=this.lastAnchorOffset||e.focusNode!=this.lastFocusNode||e.focusOffset!=this.lastFocusOffset}pollSelection(){if(null!=this.readDOMTimeout||this.gracePeriod||!this.selectionChanged())return;let e=this.getSelection(),t=this.cm;if(ot&&Je&&this.cm.display.gutterSpecs.length&&function(e){for(let t=e;t;t=t.parentNode)if(/CodeMirror-gutter-wrapper/.test(t.className))return!0;return!1}(e.anchorNode))return this.cm.triggerOnKeyDown({type:"keydown",keyCode:8,preventDefault:Math.abs}),this.blur(),void this.focus();if(this.composing)return;this.rememberSelection();let i=$l(t,e.anchorNode,e.anchorOffset),r=$l(t,e.focusNode,e.focusOffset);i&&r&&zs(t,(()=>{Wn(t.doc,hn(i,r),Et),(i.bad||r.bad)&&(t.curOp.selectionChanged=!0)}))}pollContent(){null!=this.readDOMTimeout&&(clearTimeout(this.readDOMTimeout),this.readDOMTimeout=null);let e,t,i,r=this.cm,o=r.display,s=r.doc.sel.primary(),n=s.from(),a=s.to();if(0==n.ch&&n.line>r.firstLine()&&(n=ji(n.line-1,Ni(r.doc,n.line-1).length)),a.ch==Ni(r.doc,a.line).text.length&&a.line<r.lastLine()&&(a=ji(a.line+1,0)),n.line<o.viewFrom||a.line>o.viewTo-1)return!1;n.line==o.viewFrom||0==(e=Jo(r,n.line))?(t=Fi(o.view[0].line),i=o.view[0].node):(t=Fi(o.view[e].line),i=o.view[e-1].node.nextSibling);let l,c,d=Jo(r,a.line);if(d==o.view.length-1?(l=o.viewTo-1,c=o.lineDiv.lastChild):(l=Fi(o.view[d+1].line)-1,c=o.view[d+1].node.previousSibling),!i)return!1;let u=r.doc.splitLines(function(e,t,i,r,o){let s="",n=!1,a=e.doc.lineSeparator(),l=!1;function c(e){return t=>t.id==e}function d(){n&&(s+=a,l&&(s+=a),n=l=!1)}function u(e){e&&(d(),s+=e)}function h(t){if(1==t.nodeType){let i=t.getAttribute("cm-text");if(i)return void u(i);let s,p=t.getAttribute("cm-marker");if(p){let t=e.findMarks(ji(r,0),ji(o+1,0),c(+p));return void(t.length&&(s=t[0].find(0))&&u(Ii(e.doc,s.from,s.to).join(a)))}if("false"==t.getAttribute("contenteditable"))return;let m=/^(pre|div|p|li|table|br)$/i.test(t.nodeName);if(!/^br$/i.test(t.nodeName)&&0==t.textContent.length)return;m&&d();for(let e=0;e<t.childNodes.length;e++)h(t.childNodes[e]);/^(pre|p)$/i.test(t.nodeName)&&(l=!0),m&&(n=!0)}else 3==t.nodeType&&u(t.nodeValue.replace(/\u200b/g,"").replace(/\u00a0/g," "))}for(;h(t),t!=i;)t=t.nextSibling,l=!1;return s}(r,i,c,t,l)),h=Ii(r.doc,ji(t,0),ji(l,Ni(r.doc,l).text.length));for(;u.length>1&&h.length>1;)if(Ot(u)==Ot(h))u.pop(),h.pop(),l--;else{if(u[0]!=h[0])break;u.shift(),h.shift(),t++}let p=0,m=0,f=u[0],g=h[0],v=Math.min(f.length,g.length);for(;p<v&&f.charCodeAt(p)==g.charCodeAt(p);)++p;let b=Ot(u),_=Ot(h),y=Math.min(b.length-(1==u.length?p:0),_.length-(1==h.length?p:0));for(;m<y&&b.charCodeAt(b.length-m-1)==_.charCodeAt(_.length-m-1);)++m;if(1==u.length&&1==h.length&&t==n.line)for(;p&&p>n.ch&&b.charCodeAt(b.length-m-1)==_.charCodeAt(_.length-m-1);)p--,m++;u[u.length-1]=b.slice(0,b.length-m).replace(/^\u200b+/,""),u[0]=u[0].slice(p).replace(/\u200b+$/,"");let x=ji(t,p),w=ji(l,h.length?Ot(h).length-m:0);return u.length>1||u[0]||Hi(x,w)?(ta(r.doc,u,x,w,"+input"),!0):void 0}ensurePolled(){this.forceCompositionEnd()}reset(){this.forceCompositionEnd()}forceCompositionEnd(){this.composing&&(clearTimeout(this.readDOMTimeout),this.composing=null,this.updateFromDOM(),this.div.blur(),this.div.focus())}readFromDOMSoon(){null==this.readDOMTimeout&&(this.readDOMTimeout=setTimeout((()=>{if(this.readDOMTimeout=null,this.composing){if(!this.composing.done)return;this.composing=null}this.updateFromDOM()}),80))}updateFromDOM(){!this.cm.isReadOnly()&&this.pollContent()||zs(this.cm,(()=>Qo(this.cm)))}setUneditable(e){e.contentEditable="false"}onKeyPress(e){0==e.charCode||this.composing||(e.preventDefault(),this.cm.isReadOnly()||Ws(this.cm,vl)(this.cm,String.fromCharCode(null==e.charCode?e.keyCode:e.charCode),0))}readOnlyChanged(e){this.div.contentEditable=String("nocursor"!=e)}onContextMenu(){}resetPosition(){}},Cl=Tl;function Ml(e,t){let i=_o(e,t.line);if(!i||i.hidden)return null;let r=Ni(e.doc,t.line),o=vo(i,r,t.line),s=Jt(r,e.doc.direction),n="left";if(s){n=Xt(s,t.ch)%2?"right":"left"}let a=So(o.map,t.ch,n);return a.offset="right"==a.collapse?a.end:a.start,a}function Pl(e,t){return t&&(e.bad=!0),e}function $l(e,t,i){let r;if(t==e.display.lineDiv){if(r=e.display.lineDiv.childNodes[i],!r)return Pl(e.clipPos(ji(e.display.viewTo-1)),!0);t=null,i=0}else for(r=t;;r=r.parentNode){if(!r||r==e.display.lineDiv)return null;if(r.parentNode&&r.parentNode==e.display.lineDiv)break}for(let o=0;o<e.display.view.length;o++){let s=e.display.view[o];if(s.node==r)return Ll(s,t,i)}}function Ll(e,t,i){let r=e.text.firstChild,o=!1;if(!t||!_t(r,t))return Pl(ji(Fi(e.line),0),!0);if(t==r&&(o=!0,t=r.childNodes[i],i=0,!t)){let t=e.rest?Ot(e.rest):e.line;return Pl(ji(Fi(t),t.text.length),o)}let s=3==t.nodeType?t:null,n=t;for(s||1!=t.childNodes.length||3!=t.firstChild.nodeType||(s=t.firstChild,i&&(i=s.nodeValue.length));n.parentNode!=r;)n=n.parentNode;let a=e.measure,l=a.maps;function c(t,i,r){for(let o=-1;o<(l?l.length:0);o++){let s=o<0?a.map:l[o];for(let n=0;n<s.length;n+=3){let a=s[n+2];if(a==t||a==i){let i=Fi(o<0?e.line:e.rest[o]),l=s[n]+r;return(r<0||a!=t)&&(l=s[n+(r?1:0)]),ji(i,l)}}}}let d=c(s,n,i);if(d)return Pl(d,o);for(let e=n.nextSibling,t=s?s.nodeValue.length-i:0;e;e=e.nextSibling){if(d=c(e,e.firstChild,0),d)return Pl(ji(d.line,d.ch-t),o);t+=e.textContent.length}for(let e=n.previousSibling,t=i;e;e=e.previousSibling){if(d=c(e,e.firstChild,-1),d)return Pl(ji(d.line,d.ch+t),o);t+=e.textContent.length}}Tl.prototype.needsContentAttribute=!0;var El=class{constructor(e){this.cm=e,this.prevInput="",this.pollingFast=!1,this.polling=new Mt,this.hasSelection=!1,this.composing=null}init(e){let t=this,i=this.cm;this.createField(e);const r=this.textarea;function o(e){if(!oi(i,e)){if(i.somethingSelected())gl({lineWise:!1,text:i.getSelections()});else{if(!i.options.lineWiseCopyCut)return;{let o=yl(i);gl({lineWise:!0,text:o.text}),"cut"==e.type?i.setSelections(o.ranges,null,Et):(t.prevInput="",r.value=o.text.join("\n"),kt(r))}}"cut"==e.type&&(i.state.cutIncoming=+new Date)}}e.wrapper.insertBefore(this.wrapper,e.wrapper.firstChild),rt&&(r.style.width="0px"),ei(r,"input",(()=>{Ze&&Ke>=9&&this.hasSelection&&(this.hasSelection=null),t.poll()})),ei(r,"paste",(e=>{oi(i,e)||bl(e,i)||(i.state.pasteIncoming=+new Date,t.fastPoll())})),ei(r,"cut",o),ei(r,"copy",o),ei(e.scroller,"paste",(o=>{if(co(e,o)||oi(i,o))return;if(!r.dispatchEvent)return i.state.pasteIncoming=+new Date,void t.focus();const s=new Event("paste");s.clipboardData=o.clipboardData,r.dispatchEvent(s)})),ei(e.lineSpace,"selectstart",(t=>{co(e,t)||li(t)})),ei(r,"compositionstart",(()=>{let e=i.getCursor("from");t.composing&&t.composing.range.clear(),t.composing={start:e,range:i.markText(e,i.getCursor("to"),{className:"CodeMirror-composing"})}})),ei(r,"compositionend",(()=>{t.composing&&(t.poll(),t.composing.range.clear(),t.composing=null)}))}createField(e){this.wrapper=wl(),this.textarea=this.wrapper.firstChild}screenReaderLabelChanged(e){e?this.textarea.setAttribute("aria-label",e):this.textarea.removeAttribute("aria-label")}prepareSelection(){let e=this.cm,t=e.display,i=e.doc,r=ss(e);if(e.options.moveInputWithCursor){let o=Io(e,i.sel.primary().head,"div"),s=t.wrapper.getBoundingClientRect(),n=t.lineDiv.getBoundingClientRect();r.teTop=Math.max(0,Math.min(t.wrapper.clientHeight-10,o.top+n.top-s.top)),r.teLeft=Math.max(0,Math.min(t.wrapper.clientWidth-10,o.left+n.left-s.left))}return r}showSelection(e){let t=this.cm.display;gt(t.cursorDiv,e.cursors),gt(t.selectionDiv,e.selection),null!=e.teTop&&(this.wrapper.style.top=e.teTop+"px",this.wrapper.style.left=e.teLeft+"px")}reset(e){if(this.contextMenuPending||this.composing)return;let t=this.cm;if(t.somethingSelected()){this.prevInput="";let e=t.getSelection();this.textarea.value=e,t.state.focused&&kt(this.textarea),Ze&&Ke>=9&&(this.hasSelection=e)}else e||(this.prevInput=this.textarea.value="",Ze&&Ke>=9&&(this.hasSelection=null))}getField(){return this.textarea}supportsTouch(){return!1}focus(){if("nocursor"!=this.cm.options.readOnly&&(!st||yt()!=this.textarea))try{this.textarea.focus()}catch(e){}}blur(){this.textarea.blur()}resetPosition(){this.wrapper.style.top=this.wrapper.style.left=0}receivedFocus(){this.slowPoll()}slowPoll(){this.pollingFast||this.polling.set(this.cm.options.pollInterval,(()=>{this.poll(),this.cm.state.focused&&this.slowPoll()}))}fastPoll(){let e=!1,t=this;t.pollingFast=!0,t.polling.set(20,(function i(){t.poll()||e?(t.pollingFast=!1,t.slowPoll()):(e=!0,t.polling.set(60,i))}))}poll(){let e=this.cm,t=this.textarea,i=this.prevInput;if(this.contextMenuPending||!e.state.focused||yi(t)&&!i&&!this.composing||e.isReadOnly()||e.options.disableInput||e.state.keySeq)return!1;let r=t.value;if(r==i&&!e.somethingSelected())return!1;if(Ze&&Ke>=9&&this.hasSelection===r||nt&&/[\uf700-\uf7ff]/.test(r))return e.display.input.reset(),!1;if(e.doc.sel==e.display.selForContextMenu){let e=r.charCodeAt(0);if(8203!=e||i||(i="​"),8666==e)return this.reset(),this.cm.execCommand("undo")}let o=0,s=Math.min(i.length,r.length);for(;o<s&&i.charCodeAt(o)==r.charCodeAt(o);)++o;return zs(e,(()=>{vl(e,r.slice(o),i.length-o,null,this.composing?"*compose":null),r.length>1e3||r.indexOf("\n")>-1?t.value=this.prevInput="":this.prevInput=r,this.composing&&(this.composing.range.clear(),this.composing.range=e.markText(this.composing.start,e.getCursor("to"),{className:"CodeMirror-composing"}))})),!0}ensurePolled(){this.pollingFast&&this.poll()&&(this.pollingFast=!1)}onKeyPress(){Ze&&Ke>=9&&(this.hasSelection=null),this.fastPoll()}onContextMenu(e){let t=this,i=t.cm,r=i.display,o=t.textarea;t.contextMenuPending&&t.contextMenuPending();let s=Yo(i,e),n=r.scroller.scrollTop;if(!s||Qe)return;i.options.resetSelectionOnContextMenu&&-1==i.doc.sel.contains(s)&&Ws(i,Wn)(i.doc,hn(s),Et);let a,l=o.style.cssText,c=t.wrapper.style.cssText,d=t.wrapper.offsetParent.getBoundingClientRect();function u(){if(null!=o.selectionStart){let e=i.somethingSelected(),s="​"+(e?o.value:"");o.value="⇚",o.value=s,t.prevInput=e?"":"​",o.selectionStart=1,o.selectionEnd=s.length,r.selForContextMenu=i.doc.sel}}function h(){if(t.contextMenuPending==h&&(t.contextMenuPending=!1,t.wrapper.style.cssText=c,o.style.cssText=l,Ze&&Ke<9&&r.scrollbars.setScrollTop(r.scroller.scrollTop=n),null!=o.selectionStart)){(!Ze||Ze&&Ke<9)&&u();let e=0,s=()=>{r.selForContextMenu==i.doc.sel&&0==o.selectionStart&&o.selectionEnd>0&&"​"==t.prevInput?Ws(i,Zn)(i):e++<10?r.detectingSelectAll=setTimeout(s,500):(r.selForContextMenu=null,r.input.reset())};r.detectingSelectAll=setTimeout(s,200)}}if(t.wrapper.style.cssText="position: static",o.style.cssText=`position: absolute; width: 30px; height: 30px;\n      top: ${e.clientY-d.top-5}px; left: ${e.clientX-d.left-5}px;\n      z-index: 1000; background: ${Ze?"rgba(255, 255, 255, .05)":"transparent"};\n      outline: none; border-width: 0; outline: none; overflow: hidden; opacity: .05; filter: alpha(opacity=5);`,Xe&&(a=window.scrollY),r.input.focus(),Xe&&window.scrollTo(null,a),r.input.reset(),i.somethingSelected()||(o.value=t.prevInput=" "),t.contextMenuPending=h,r.selForContextMenu=i.doc.sel,clearTimeout(r.detectingSelectAll),Ze&&Ke>=9&&u(),ut){ui(e);let t=()=>{ii(window,"mouseup",t),setTimeout(h,20)};ei(window,"mouseup",t)}else setTimeout(h,50)}readOnlyChanged(e){e||this.reset(),this.textarea.disabled="nocursor"==e,this.textarea.readOnly=!!e}setUneditable(){}},Rl=El;El.prototype.needsContentAttribute=!1,function(e){let t=e.optionHandlers;function i(i,r,o,s){e.defaults[i]=r,o&&(t[i]=s?(e,t,i)=>{i!=nl&&o(e,t,i)}:o)}e.defineOption=i,e.Init=nl,i("value","",((e,t)=>e.setValue(t)),!0),i("mode",null,((e,t)=>{e.doc.modeOption=t,vn(e)}),!0),i("indentUnit",2,vn,!0),i("indentWithTabs",!1),i("smartIndent",!0),i("tabSize",4,(e=>{bn(e),Po(e),Qo(e)}),!0),i("lineSeparator",null,((e,t)=>{if(e.doc.lineSep=t,!t)return;let i=[],r=e.doc.first;e.doc.iter((e=>{for(let o=0;;){let s=e.text.indexOf(t,o);if(-1==s)break;o=s+t.length,i.push(ji(r,s))}r++}));for(let r=i.length-1;r>=0;r--)ta(e.doc,t,i[r],ji(i[r].line,i[r].ch+t.length))})),i("specialChars",/[\u0000-\u001f\u007f-\u009f\u00ad\u061c\u200b\u200e\u200f\u2028\u2029\ufeff\ufff9-\ufffc]/g,((e,t,i)=>{e.state.specialChars=new RegExp(t.source+(t.test("\t")?"":"|\t"),"g"),i!=nl&&e.refresh()})),i("specialCharPlaceholder",Wr,(e=>e.refresh()),!0),i("electricChars",!0),i("inputStyle",st?"contenteditable":"textarea",(()=>{throw new Error("inputStyle can not (yet) be changed in a running editor")}),!0),i("spellcheck",!1,((e,t)=>e.getInputField().spellcheck=t),!0),i("autocorrect",!1,((e,t)=>e.getInputField().autocorrect=t),!0),i("autocapitalize",!1,((e,t)=>e.getInputField().autocapitalize=t),!0),i("rtlMoveVisually",!lt),i("wholeLineUpdateBefore",!0),i("theme","default",(e=>{sl(e),tn(e)}),!0),i("keyMap","default",((e,t,i)=>{let r=Na(t),o=i!=nl&&Na(i);o&&o.detach&&o.detach(e,r),r.attach&&r.attach(e,o||null)})),i("extraKeys",null),i("configureMouse",null),i("lineWrapping",!1,dl,!0),i("gutters",[],((e,t)=>{e.display.gutterSpecs=Qs(t,e.options.lineNumbers),tn(e)}),!0),i("fixedGutter",!0,((e,t)=>{e.display.gutters.style.left=t?Zo(e.display)+"px":"0",e.refresh()}),!0),i("coverGutterNextToScrollbar",!1,(e=>Ms(e)),!0),i("scrollbarStyle","native",(e=>{Ls(e),Ms(e),e.display.scrollbars.setScrollTop(e.doc.scrollTop),e.display.scrollbars.setScrollLeft(e.doc.scrollLeft)}),!0),i("lineNumbers",!1,((e,t)=>{e.display.gutterSpecs=Qs(e.options.gutters,t),tn(e)}),!0),i("firstLineNumber",1,tn,!0),i("lineNumberFormatter",(e=>e),tn,!0),i("showCursorWhenSelecting",!1,os,!0),i("resetSelectionOnContextMenu",!0),i("lineWiseCopyCut",!0),i("pasteLinesPerSelection",!0),i("selectionsMayTouch",!1),i("readOnly",!1,((e,t)=>{"nocursor"==t&&(ps(e),e.display.input.blur()),e.display.input.readOnlyChanged(t)})),i("screenReaderLabel",null,((e,t)=>{t=""===t?null:t,e.display.input.screenReaderLabelChanged(t)})),i("disableInput",!1,((e,t)=>{t||e.display.input.reset()}),!0),i("dragDrop",!0,cl),i("allowDropFileTypes",null),i("cursorBlinkRate",530),i("cursorScrollMargin",0),i("cursorHeight",1,os,!0),i("singleCursorHeightPerLine",!0,os,!0),i("workTime",100),i("workDelay",100),i("flattenSpans",!0,bn,!0),i("addModeClass",!1,bn,!0),i("pollInterval",100),i("undoDepth",200,((e,t)=>e.doc.history.undoDepth=t)),i("historyEventDelay",1250),i("viewportMargin",10,(e=>e.refresh()),!0),i("maxHighlightLength",1e4,bn,!0),i("moveInputWithCursor",!0,((e,t)=>{t||e.display.input.resetPosition()})),i("tabindex",null,((e,t)=>e.display.input.getField().tabIndex=t||"")),i("autofocus",null),i("direction","ltr",((e,t)=>e.doc.setDirection(t)),!0),i("phrases",null)}(ul),function(e){let t=e.optionHandlers,i=e.helpers={};e.prototype={constructor:e,focus:function(){window.focus(),this.display.input.focus()},setOption:function(e,i){let r=this.options,o=r[e];r[e]==i&&"mode"!=e||(r[e]=i,t.hasOwnProperty(e)&&Ws(this,t[e])(this,i,o),ri(this,"optionChange",this,e))},getOption:function(e){return this.options[e]},getDoc:function(){return this.doc},addKeyMap:function(e,t){this.state.keyMaps[t?"push":"unshift"](Na(e))},removeKeyMap:function(e){let t=this.state.keyMaps;for(let i=0;i<t.length;++i)if(t[i]==e||t[i].name==e)return t.splice(i,1),!0},addOverlay:Bs((function(t,i){let r=t.token?t:e.getMode(this.options,t);if(r.startState)throw new Error("Overlays may not be stateful.");!function(e,t,i){let r=0,o=i(t);for(;r<e.length&&i(e[r])<=o;)r++;e.splice(r,0,t)}(this.state.overlays,{mode:r,modeSpec:t,opaque:i&&i.opaque,priority:i&&i.priority||0},(e=>e.priority)),this.state.modeGen++,Qo(this)})),removeOverlay:Bs((function(e){let t=this.state.overlays;for(let i=0;i<t.length;++i){let r=t[i].modeSpec;if(r==e||"string"==typeof e&&r.name==e)return t.splice(i,1),this.state.modeGen++,void Qo(this)}})),indentLine:Bs((function(e,t,i){"string"!=typeof t&&"number"!=typeof t&&(t=null==t?this.options.smartIndent?"smart":"prev":t?"add":"subtract"),Wi(this.doc,e)&&ml(this,e,t,i)})),indentSelection:Bs((function(e){let t=this.doc.sel.ranges,i=-1;for(let r=0;r<t.length;r++){let o=t[r];if(o.empty())o.head.line>i&&(ml(this,o.head.line,e,!0),i=o.head.line,r==this.doc.sel.primIndex&&_s(this));else{let s=o.from(),n=o.to(),a=Math.max(i,s.line);i=Math.min(this.lastLine(),n.line-(n.ch?0:1))+1;for(let t=a;t<i;++t)ml(this,t,e);let l=this.doc.sel.ranges;0==s.ch&&t.length==l.length&&l[r].from().ch>0&&On(this.doc,r,new dn(s,l[r].to()),Et)}}})),getTokenAt:function(e,t){return nr(this,e,t)},getLineTokens:function(e,t){return nr(this,ji(e),t,!0)},getTokenTypeAt:function(e){e=Ki(this.doc,e);let t,i=er(this,Ni(this.doc,e.line)),r=0,o=(i.length-1)/2,s=e.ch;if(0==s)t=i[2];else for(;;){let e=r+o>>1;if((e?i[2*e-1]:0)>=s)o=e;else{if(!(i[2*e+1]<s)){t=i[2*e+2];break}r=e+1}}let n=t?t.indexOf("overlay "):-1;return n<0?t:0==n?null:t.slice(0,n-1)},getModeAt:function(t){let i=this.doc.mode;return i.innerMode?e.innerMode(i,this.getTokenAt(t).state).mode:i},getHelper:function(e,t){return this.getHelpers(e,t)[0]},getHelpers:function(e,t){let r=[];if(!i.hasOwnProperty(t))return r;let o=i[t],s=this.getModeAt(e);if("string"==typeof s[t])o[s[t]]&&r.push(o[s[t]]);else if(s[t])for(let e=0;e<s[t].length;e++){let i=o[s[t][e]];i&&r.push(i)}else s.helperType&&o[s.helperType]?r.push(o[s.helperType]):o[s.name]&&r.push(o[s.name]);for(let e=0;e<o._global.length;e++){let t=o._global[e];t.pred(s,this)&&-1==Pt(r,t.val)&&r.push(t.val)}return r},getStateAfter:function(e,t){let i=this.doc;return tr(this,(e=Zi(i,null==e?i.first+i.size-1:e))+1,t).state},cursorCoords:function(e,t){let i,r=this.doc.sel.primary();return i=null==e?r.head:"object"==typeof e?Ki(this.doc,e):e?r.from():r.to(),Io(this,i,t||"page")},charCoords:function(e,t){return No(this,Ki(this.doc,e),t||"page")},coordsChar:function(e,t){return Fo(this,(e=Ao(this,e,t||"page")).left,e.top)},lineAtHeight:function(e,t){return e=Ao(this,{top:e,left:0},t||"page").top,zi(this.doc,e+this.display.viewOffset)},heightAtLine:function(e,t,i){let r,o=!1;if("number"==typeof e){let t=this.doc.first+this.doc.size-1;e<this.doc.first?e=this.doc.first:e>t&&(e=t,o=!0),r=Ni(this.doc,e)}else r=e;return Ro(this,r,{top:0,left:0},t||"page",i||o).top+(o?this.doc.height-Er(r):0)},defaultTextHeight:function(){return Vo(this.display)},defaultCharWidth:function(){return Go(this.display)},getViewport:function(){return{from:this.display.viewFrom,to:this.display.viewTo}},addWidget:function(e,t,i,r,o){let s=this.display,n=(e=Io(this,Ki(this.doc,e))).bottom,a=e.left;if(t.style.position="absolute",t.setAttribute("cm-ignore-events","true"),this.display.input.setUneditable(t),s.sizer.appendChild(t),"over"==r)n=e.top;else if("above"==r||"near"==r){let i=Math.max(s.wrapper.clientHeight,this.doc.height),o=Math.max(s.sizer.clientWidth,s.lineSpace.clientWidth);("above"==r||e.bottom+t.offsetHeight>i)&&e.top>t.offsetHeight?n=e.top-t.offsetHeight:e.bottom+t.offsetHeight<=i&&(n=e.bottom),a+t.offsetWidth>o&&(a=o-t.offsetWidth)}t.style.top=n+"px",t.style.left=t.style.right="","right"==o?(a=s.sizer.clientWidth-t.offsetWidth,t.style.right="0px"):("left"==o?a=0:"middle"==o&&(a=(s.sizer.clientWidth-t.offsetWidth)/2),t.style.left=a+"px"),i&&function(e,t){let i=vs(e,t);null!=i.scrollTop&&ks(e,i.scrollTop),null!=i.scrollLeft&&Ts(e,i.scrollLeft)}(this,{left:a,top:n,right:a+t.offsetWidth,bottom:n+t.offsetHeight})},triggerOnKeyDown:Bs(Za),triggerOnKeyPress:Bs(Xa),triggerOnKeyUp:Ka,triggerOnMouseDown:Bs(el),execCommand:function(e){if(za.hasOwnProperty(e))return za[e].call(null,this)},triggerElectric:Bs((function(e){_l(this,e)})),findPosH:function(e,t,i,r){let o=1;t<0&&(o=-1,t=-t);let s=Ki(this.doc,e);for(let e=0;e<t&&(s=kl(this.doc,s,o,i,r),!s.hitSide);++e);return s},moveH:Bs((function(e,t){this.extendSelectionsBy((i=>this.display.shift||this.doc.extend||i.empty()?kl(this.doc,i.head,e,t,this.options.rtlMoveVisually):e<0?i.from():i.to()),At)})),deleteH:Bs((function(e,t){let i=this.doc.sel,r=this.doc;i.somethingSelected()?r.replaceSelection("",null,"+delete"):Ia(this,(i=>{let o=kl(r,i.head,e,t,!1);return e<0?{from:o,to:i.head}:{from:i.head,to:o}}))})),findPosV:function(e,t,i,r){let o=1,s=r;t<0&&(o=-1,t=-t);let n=Ki(this.doc,e);for(let e=0;e<t;++e){let e=Io(this,n,"div");if(null==s?s=e.left:e.left=s,n=Sl(this,e,o,i),n.hitSide)break}return n},moveV:Bs((function(e,t){let i=this.doc,r=[],o=!this.display.shift&&!i.extend&&i.sel.somethingSelected();if(i.extendSelectionsBy((s=>{if(o)return e<0?s.from():s.to();let n=Io(this,s.head,"div");null!=s.goalColumn&&(n.left=s.goalColumn),r.push(n.left);let a=Sl(this,n,e,t);return"page"==t&&s==i.sel.primary()&&bs(this,No(this,a,"div").top-n.top),a}),At),r.length)for(let e=0;e<i.sel.ranges.length;e++)i.sel.ranges[e].goalColumn=r[e]})),findWordAt:function(e){let t=Ni(this.doc,e.line).text,i=e.ch,r=e.ch;if(t){let o=this.getHelper(e,"wordChars");"before"!=e.sticky&&r!=t.length||!i?++r:--i;let s=t.charAt(i),n=Ht(s,o)?e=>Ht(e,o):/\s/.test(s)?e=>/\s/.test(e):e=>!/\s/.test(e)&&!Ht(e);for(;i>0&&n(t.charAt(i-1));)--i;for(;r<t.length&&n(t.charAt(r));)++r}return new dn(ji(e.line,i),ji(e.line,r))},toggleOverwrite:function(e){null!=e&&e==this.state.overwrite||((this.state.overwrite=!this.state.overwrite)?xt(this.display.cursorDiv,"CodeMirror-overwrite"):mt(this.display.cursorDiv,"CodeMirror-overwrite"),ri(this,"overwriteToggle",this,this.state.overwrite))},hasFocus:function(){return this.display.input.getField()==yt()},isReadOnly:function(){return!(!this.options.readOnly&&!this.doc.cantEdit)},scrollTo:Bs((function(e,t){ys(this,e,t)})),getScrollInfo:function(){let e=this.display.scroller;return{left:e.scrollLeft,top:e.scrollTop,height:e.scrollHeight-mo(this)-this.display.barHeight,width:e.scrollWidth-mo(this)-this.display.barWidth,clientHeight:go(this),clientWidth:fo(this)}},scrollIntoView:Bs((function(e,t){null==e?(e={from:this.doc.sel.primary().head,to:null},null==t&&(t=this.options.cursorScrollMargin)):"number"==typeof e?e={from:ji(e,0),to:null}:null==e.from&&(e={from:e,to:null}),e.to||(e.to=e.from),e.margin=t||0,null!=e.from.line?function(e,t){xs(e),e.curOp.scrollToPos=t}(this,e):ws(this,e.from,e.to,e.margin)})),setSize:Bs((function(e,t){let i=e=>"number"==typeof e||/^\d+$/.test(String(e))?e+"px":e;null!=e&&(this.display.wrapper.style.width=i(e)),null!=t&&(this.display.wrapper.style.height=i(t)),this.options.lineWrapping&&Mo(this);let r=this.display.viewFrom;this.doc.iter(r,this.display.viewTo,(e=>{if(e.widgets)for(let t=0;t<e.widgets.length;t++)if(e.widgets[t].noHScroll){es(this,r,"widget");break}++r})),this.curOp.forceUpdate=!0,ri(this,"refresh",this)})),operation:function(e){return zs(this,e)},startOperation:function(){return Rs(this)},endOperation:function(){return As(this)},refresh:Bs((function(){let e=this.display.cachedTextHeight;Qo(this),this.curOp.forceUpdate=!0,Po(this),ys(this,this.doc.scrollLeft,this.doc.scrollTop),Ks(this.display),(null==e||Math.abs(e-Vo(this.display))>.5||this.options.lineWrapping)&&Xo(this),ri(this,"refresh",this)})),swapDoc:Bs((function(e){let t=this.doc;return t.cm=null,this.state.selectingText&&this.state.selectingText(),wn(this,e),Po(this),this.display.input.reset(),ys(this,e.scrollLeft,e.scrollTop),this.curOp.forceScroll=!0,Kr(this,"swapDoc",this,t),t})),phrase:function(e){let t=this.options.phrases;return t&&Object.prototype.hasOwnProperty.call(t,e)?t[e]:e},getInputField:function(){return this.display.input.getField()},getWrapperElement:function(){return this.display.wrapper},getScrollerElement:function(){return this.display.scroller},getGutterElement:function(){return this.display.gutters}},ai(e),e.registerHelper=function(t,r,o){i.hasOwnProperty(t)||(i[t]=e[t]={_global:[]}),i[t][r]=o},e.registerGlobalHelper=function(t,r,o,s){e.registerHelper(t,r,s),i[t]._global.push({pred:o,val:s})}}(ul);var Al,Nl="iter insert remove copy getEditor constructor".split(" ");for(let e in ba.prototype)ba.prototype.hasOwnProperty(e)&&Pt(Nl,e)<0&&(ul.prototype[e]=function(e){return function(){return e.apply(this.doc,arguments)}}(ba.prototype[e]));ai(ba),ul.inputStyles={textarea:Rl,contenteditable:Cl},ul.defineMode=function(e){ul.defaults.mode||"null"==e||(ul.defaults.mode=e),Ti.apply(this,arguments)},ul.defineMIME=function(e,t){Si[e]=t},ul.defineMode("null",(()=>({token:e=>e.skipToEnd()}))),ul.defineMIME("text/plain","null"),ul.defineExtension=(e,t)=>{ul.prototype[e]=t},ul.defineDocExtension=(e,t)=>{ba.prototype[e]=t},ul.fromTextArea=function(e,t){if((t=t?Tt(t):{}).value=e.value,!t.tabindex&&e.tabIndex&&(t.tabindex=e.tabIndex),!t.placeholder&&e.placeholder&&(t.placeholder=e.placeholder),null==t.autofocus){let i=yt();t.autofocus=i==e||null!=e.getAttribute("autofocus")&&i==document.body}function i(){e.value=o.getValue()}let r;if(e.form&&(ei(e.form,"submit",i),!t.leaveSubmitMethodAlone)){let t=e.form;r=t.submit;try{let e=t.submit=()=>{i(),t.submit=r,t.submit(),t.submit=e}}catch(e){}}t.finishInit=o=>{o.save=i,o.getTextArea=()=>e,o.toTextArea=()=>{o.toTextArea=isNaN,i(),e.parentNode.removeChild(o.getWrapperElement()),e.style.display="",e.form&&(ii(e.form,"submit",i),t.leaveSubmitMethodAlone||"function"!=typeof e.form.submit||(e.form.submit=r))}},e.style.display="none";let o=ul((t=>e.parentNode.insertBefore(t,e.nextSibling)),t);return o},(Al=ul).off=ii,Al.on=ei,Al.wheelEventPixels=an,Al.Doc=ba,Al.splitLines=_i,Al.countColumn=Ct,Al.findColumn=Nt,Al.isWordChar=jt,Al.Pass=Lt,Al.signal=ri,Al.Line=Nr,Al.changeEnd=pn,Al.scrollbarModel=$s,Al.Pos=ji,Al.cmpPos=Hi,Al.modes=ki,Al.mimeModes=Si,Al.resolveMode=Ci,Al.getMode=Mi,Al.modeExtensions=Pi,Al.extendMode=$i,Al.copyState=Li,Al.startState=Ri,Al.innerMode=Ei,Al.commands=za,Al.keyMap=Ma,Al.keyName=Aa,Al.isModifierKey=Ea,Al.lookupKey=La,Al.normalizeKeyMap=$a,Al.StringStream=Ai,Al.SharedTextMarker=pa,Al.TextMarker=ua,Al.LineWidget=la,Al.e_preventDefault=li,Al.e_stopPropagation=ci,Al.e_stop=ui,Al.addClass=xt,Al.contains=_t,Al.rmClass=mt,Al.keyNames=Ca,ul.version="5.61.0";var Il=ul;self.CodeMirror=Il;var Dl,Ol=class extends HTMLElement{static get observedAttributes(){return["src","readonly","mode","theme"]}attributeChangedCallback(e,t,i){this.__initialized&&t!==i&&(this[e]="readonly"===e?null!==i:i)}get readonly(){return this.editor.getOption("readOnly")}set readonly(e){this.editor.setOption("readOnly",e)}get mode(){return this.editor.getOption("mode")}set mode(e){this.editor.setOption("mode",e)}get theme(){return this.editor.getOption("theme")}set theme(e){this.editor.setOption("theme",e)}get src(){return this.getAttribute("src")}set src(e){this.setAttribute("src",e),this.setSrc()}get value(){return this.editor.getValue()}set value(e){this.__initialized?this.setValueForced(e):this.__preInitValue=e}constructor(){super();const e=e=>"childList"===e.type&&(Array.from(e.addedNodes).some((e=>"LINK"===e.tagName))||Array.from(e.removedNodes).some((e=>"LINK"===e.tagName)));this.__observer=new MutationObserver(((t,i)=>{t.some(e)&&this.refreshStyles(),this.lookupInnerScript((e=>{this.value=e}))})),this.__observer.observe(this,{childList:!0,characterData:!0,subtree:!0}),this.__initialized=!1,this.__element=null,this.editor=null}async connectedCallback(){const e=this.attachShadow({mode:"open"}),t=document.createElement("template"),i=document.createElement("style");i.innerHTML="\n/* BASICS */\n\n.CodeMirror {\n  /* Set height, width, borders, and global font properties here */\n  font-family: monospace;\n  height: auto;\n  color: black;\n  direction: ltr;\n}\n\n/* PADDING */\n\n.CodeMirror-lines {\n  padding: 4px 0; /* Vertical padding around content */\n}\n.CodeMirror pre.CodeMirror-line,\n.CodeMirror pre.CodeMirror-line-like {\n  padding: 0 4px; /* Horizontal padding of content */\n}\n\n.CodeMirror-scrollbar-filler, .CodeMirror-gutter-filler {\n  background-color: white; /* The little square between H and V scrollbars */\n}\n\n/* GUTTER */\n\n.CodeMirror-gutters {\n  border-right: 1px solid #ddd;\n  background-color: #f7f7f7;\n  white-space: nowrap;\n}\n.CodeMirror-linenumbers {}\n.CodeMirror-linenumber {\n  padding: 0 3px 0 5px;\n  min-width: 20px;\n  text-align: right;\n  color: #999;\n  white-space: nowrap;\n}\n\n.CodeMirror-guttermarker { color: black; }\n.CodeMirror-guttermarker-subtle { color: #999; }\n\n/* CURSOR */\n\n.CodeMirror-cursor {\n  border-left: 1px solid black;\n  border-right: none;\n  width: 0;\n}\n/* Shown when moving in bi-directional text */\n.CodeMirror div.CodeMirror-secondarycursor {\n  border-left: 1px solid silver;\n}\n.cm-fat-cursor .CodeMirror-cursor {\n  width: auto;\n  border: 0 !important;\n  background: #7e7;\n}\n.cm-fat-cursor div.CodeMirror-cursors {\n  z-index: 1;\n}\n.cm-fat-cursor-mark {\n  background-color: rgba(20, 255, 20, 0.5);\n  -webkit-animation: blink 1.06s steps(1) infinite;\n  -moz-animation: blink 1.06s steps(1) infinite;\n  animation: blink 1.06s steps(1) infinite;\n}\n.cm-animate-fat-cursor {\n  width: auto;\n  border: 0;\n  -webkit-animation: blink 1.06s steps(1) infinite;\n  -moz-animation: blink 1.06s steps(1) infinite;\n  animation: blink 1.06s steps(1) infinite;\n  background-color: #7e7;\n}\n@-moz-keyframes blink {\n  0% {}\n  50% { background-color: transparent; }\n  100% {}\n}\n@-webkit-keyframes blink {\n  0% {}\n  50% { background-color: transparent; }\n  100% {}\n}\n@keyframes blink {\n  0% {}\n  50% { background-color: transparent; }\n  100% {}\n}\n\n/* Can style cursor different in overwrite (non-insert) mode */\n.CodeMirror-overwrite .CodeMirror-cursor {}\n\n.cm-tab { display: inline-block; text-decoration: inherit; }\n\n.CodeMirror-rulers {\n  position: absolute;\n  left: 0; right: 0; top: -50px; bottom: 0;\n  overflow: hidden;\n}\n.CodeMirror-ruler {\n  border-left: 1px solid #ccc;\n  top: 0; bottom: 0;\n  position: absolute;\n}\n\n/* DEFAULT THEME */\n\n.cm-s-default .cm-header {color: blue;}\n.cm-s-default .cm-quote {color: #090;}\n.cm-negative {color: #d44;}\n.cm-positive {color: #292;}\n.cm-header, .cm-strong {font-weight: bold;}\n.cm-em {font-style: italic;}\n.cm-link {text-decoration: underline;}\n.cm-strikethrough {text-decoration: line-through;}\n\n.cm-s-default .cm-keyword {color: #708;}\n.cm-s-default .cm-atom {color: #219;}\n.cm-s-default .cm-number {color: #164;}\n.cm-s-default .cm-def {color: #00f;}\n.cm-s-default .cm-variable,\n.cm-s-default .cm-punctuation,\n.cm-s-default .cm-property,\n.cm-s-default .cm-operator {}\n.cm-s-default .cm-variable-2 {color: #05a;}\n.cm-s-default .cm-variable-3, .cm-s-default .cm-type {color: #085;}\n.cm-s-default .cm-comment {color: #a50;}\n.cm-s-default .cm-string {color: #a11;}\n.cm-s-default .cm-string-2 {color: #f50;}\n.cm-s-default .cm-meta {color: #555;}\n.cm-s-default .cm-qualifier {color: #555;}\n.cm-s-default .cm-builtin {color: #30a;}\n.cm-s-default .cm-bracket {color: #997;}\n.cm-s-default .cm-tag {color: #170;}\n.cm-s-default .cm-attribute {color: #00c;}\n.cm-s-default .cm-hr {color: #999;}\n.cm-s-default .cm-link {color: #00c;}\n\n.cm-s-default .cm-error {color: #f00;}\n.cm-invalidchar {color: #f00;}\n\n.CodeMirror-composing { border-bottom: 2px solid; }\n\n/* Default styles for common addons */\n\ndiv.CodeMirror span.CodeMirror-matchingbracket {color: #0b0;}\ndiv.CodeMirror span.CodeMirror-nonmatchingbracket {color: #a22;}\n.CodeMirror-matchingtag { background: rgba(255, 150, 0, .3); }\n.CodeMirror-activeline-background {background: #e8f2ff;}\n\n/* STOP */\n\n/* The rest of this file contains styles related to the mechanics of\n    the editor. You probably shouldn't touch them. */\n\n.CodeMirror {\n  position: relative;\n  overflow: hidden;\n  background: white;\n}\n\n.CodeMirror-scroll {\n  overflow: scroll !important; /* Things will break if this is overridden */\n  /* 50px is the magic margin used to hide the element's real scrollbars */\n  /* See overflow: hidden in .CodeMirror */\n  margin-bottom: -50px; margin-right: -50px;\n  padding-bottom: 50px;\n  height: 100%;\n  outline: none; /* Prevent dragging from highlighting the element */\n  position: relative;\n}\n.CodeMirror-sizer {\n  position: relative;\n  border-right: 50px solid transparent;\n}\n\n/* The fake, visible scrollbars. Used to force redraw during scrolling\n    before actual scrolling happens, thus preventing shaking and\n    flickering artifacts. */\n.CodeMirror-vscrollbar, .CodeMirror-hscrollbar, .CodeMirror-scrollbar-filler, .CodeMirror-gutter-filler {\n  position: absolute;\n  z-index: 6;\n  display: none;\n}\n.CodeMirror-vscrollbar {\n  right: 0; top: 0;\n  overflow-x: hidden;\n  overflow-y: scroll;\n}\n.CodeMirror-hscrollbar {\n  bottom: 0; left: 0;\n  overflow-y: hidden;\n  overflow-x: scroll;\n}\n.CodeMirror-scrollbar-filler {\n  right: 0; bottom: 0;\n}\n.CodeMirror-gutter-filler {\n  left: 0; bottom: 0;\n}\n\n.CodeMirror-gutters {\n  position: absolute; left: 0; top: 0;\n  min-height: 100%;\n  z-index: 3;\n}\n.CodeMirror-gutter {\n  white-space: normal;\n  height: 100%;\n  display: inline-block;\n  vertical-align: top;\n  margin-bottom: -50px;\n}\n.CodeMirror-gutter-wrapper {\n  position: absolute;\n  z-index: 4;\n  background: none !important;\n  border: none !important;\n}\n.CodeMirror-gutter-background {\n  position: absolute;\n  top: 0; bottom: 0;\n  z-index: 4;\n}\n.CodeMirror-gutter-elt {\n  position: absolute;\n  cursor: default;\n  z-index: 4;\n}\n.CodeMirror-gutter-wrapper ::selection { background-color: transparent }\n.CodeMirror-gutter-wrapper ::-moz-selection { background-color: transparent }\n\n.CodeMirror-lines {\n  cursor: text;\n  min-height: 1px; /* prevents collapsing before first draw */\n}\n.CodeMirror pre.CodeMirror-line,\n.CodeMirror pre.CodeMirror-line-like {\n  /* Reset some styles that the rest of the page might have set */\n  -moz-border-radius: 0; -webkit-border-radius: 0; border-radius: 0;\n  border-width: 0;\n  background: transparent;\n  font-family: inherit;\n  font-size: inherit;\n  margin: 0;\n  white-space: pre;\n  word-wrap: normal;\n  line-height: inherit;\n  color: inherit;\n  z-index: 2;\n  position: relative;\n  overflow: visible;\n  -webkit-tap-highlight-color: transparent;\n  -webkit-font-variant-ligatures: contextual;\n  font-variant-ligatures: contextual;\n}\n.CodeMirror-wrap pre.CodeMirror-line,\n.CodeMirror-wrap pre.CodeMirror-line-like {\n  word-wrap: break-word;\n  white-space: pre-wrap;\n  word-break: normal;\n}\n\n.CodeMirror-linebackground {\n  position: absolute;\n  left: 0; right: 0; top: 0; bottom: 0;\n  z-index: 0;\n}\n\n.CodeMirror-linewidget {\n  position: relative;\n  z-index: 2;\n  padding: 0.1px; /* Force widget margins to stay inside of the container */\n}\n\n.CodeMirror-widget {}\n\n.CodeMirror-rtl pre { direction: rtl; }\n\n.CodeMirror-code {\n  outline: none;\n}\n\n/* Force content-box sizing for the elements where we expect it */\n.CodeMirror-scroll,\n.CodeMirror-sizer,\n.CodeMirror-gutter,\n.CodeMirror-gutters,\n.CodeMirror-linenumber {\n  -moz-box-sizing: content-box;\n  box-sizing: content-box;\n}\n\n.CodeMirror-measure {\n  position: absolute;\n  width: 100%;\n  height: 0;\n  overflow: hidden;\n  visibility: hidden;\n}\n\n.CodeMirror-cursor {\n  position: absolute;\n  pointer-events: none;\n}\n.CodeMirror-measure pre { position: static; }\n\ndiv.CodeMirror-cursors {\n  visibility: hidden;\n  position: relative;\n  z-index: 3;\n}\ndiv.CodeMirror-dragcursors {\n  visibility: visible;\n}\n\n.CodeMirror-focused div.CodeMirror-cursors {\n  visibility: visible;\n}\n\n.CodeMirror-selected { background: #d9d9d9; }\n.CodeMirror-focused .CodeMirror-selected { background: #d7d4f0; }\n.CodeMirror-crosshair { cursor: crosshair; }\n.CodeMirror-line::selection, .CodeMirror-line > span::selection, .CodeMirror-line > span > span::selection { background: #d7d4f0; }\n.CodeMirror-line::-moz-selection, .CodeMirror-line > span::-moz-selection, .CodeMirror-line > span > span::-moz-selection { background: #d7d4f0; }\n\n.cm-searching {\n  background-color: #ffa;\n  background-color: rgba(255, 255, 0, .4);\n}\n\n/* Used to force a border model for a node */\n.cm-force-border { padding-right: .1px; }\n\n@media print {\n  /* Hide the cursor when printing */\n  .CodeMirror div.CodeMirror-cursors {\n    visibility: hidden;\n  }\n}\n\n/* See issue #2901 */\n.cm-tab-wrap-hack:after { content: ''; }\n\n/* Help users use markselection to safely style text background */\nspan.CodeMirror-selectedtext { background: none; }\n",t.innerHTML=Ol.template(),e.appendChild(i),e.appendChild(t.content.cloneNode(!0)),this.style.display="block",this.__element=e.querySelector("textarea");const r=this.hasAttribute("mode")?this.getAttribute("mode"):"null",o=this.hasAttribute("theme")?this.getAttribute("theme"):"default";let s=this.getAttribute("readonly");""===s?s=!0:"nocursor"!==s&&(s=!1),this.refreshStyles(),this.lookupInnerScript((e=>{this.value=e}));let n=Il.defaults.viewportMargin;if(this.hasAttribute("viewport-margin")){const e=this.getAttribute("viewport-margin").toLowerCase();n="infinity"===e?1/0:parseInt(e)}this.editor=Il.fromTextArea(this.__element,{lineNumbers:!0,readOnly:s,mode:r,theme:o,viewportMargin:n}),this.hasAttribute("src")&&this.setSrc(),await new Promise((e=>setTimeout(e,50))),this.__initialized=!0,void 0!==this.__preInitValue&&this.setValueForced(this.__preInitValue)}disconnectedCallback(){this.editor&&this.editor.toTextArea(),this.editor=null,this.__initialized=!1,this.__observer.disconnect()}async setSrc(){const e=this.getAttribute("src"),t=await this.fetchSrc(e);this.value=t}async setValueForced(e){this.editor.swapDoc(Il.Doc(e,this.getAttribute("mode"))),this.editor.refresh()}async fetchSrc(e){return(await fetch(e)).text()}refreshStyles(){Array.from(this.shadowRoot.children).forEach((e=>{"LINK"===e.tagName&&"stylesheet"===e.getAttribute("rel")&&e.remove()})),Array.from(this.children).forEach((e=>{"LINK"===e.tagName&&"stylesheet"===e.getAttribute("rel")&&this.shadowRoot.appendChild(e.cloneNode(!0))}))}static template(){return'\n      <textarea style="display:inherit; width:inherit; height:inherit;"></textarea>\n    '}lookupInnerScript(e){const t=this.querySelector("script");if(t&&"wc-content"===t.getAttribute("type")){let i=Ol.dedentText(t.innerHTML);i=i.replace(/&lt;(\/?script)(.*?)&gt;/g,"<$1$2>"),e(i)}}static dedentText(e){const t=e.split("\n");""===t[0]&&t.splice(0,1);const i=t[0];let r=0;const o="\t"===i[0]?"\t":" ";for(;i[r]===o;)r+=1;const s=[];for(const e of t){let t=e;for(let e=0;e<r&&t[0]===o;e++)t=t.substring(1);s.push(t)}return""===s[s.length-1]&&s.splice(s.length-1,1),s.join("\n")}};customElements.define("wc-codemirror",Ol),Dl=function(e){function t(e){return new RegExp("^(("+e.join(")|(")+"))\\b")}var i,r=t(["and","or","not","is"]),o=["as","assert","break","class","continue","def","del","elif","else","except","finally","for","from","global","if","import","lambda","pass","raise","return","try","while","with","yield","in"],s=["abs","all","any","bin","bool","bytearray","callable","chr","classmethod","compile","complex","delattr","dict","dir","divmod","enumerate","eval","filter","float","format","frozenset","getattr","globals","hasattr","hash","help","hex","id","input","int","isinstance","issubclass","iter","len","list","locals","map","max","memoryview","min","next","object","oct","open","ord","pow","property","range","repr","reversed","round","set","setattr","slice","sorted","staticmethod","str","sum","super","tuple","type","vars","zip","__import__","NotImplemented","Ellipsis","__debug__"];function n(e){return e.scopes[e.scopes.length-1]}e.registerHelper("hintWords","python",o.concat(s)),e.defineMode("python",(function(i,a){for(var l="error",c=a.delimiters||a.singleDelimiters||/^[\(\)\[\]\{\}@,:`=;\.\\]/,d=[a.singleOperators,a.doubleOperators,a.doubleDelimiters,a.tripleDelimiters,a.operators||/^([-+*/%\/&|^]=?|[<>=]+|\/\/=?|\*\*=?|!=|[~!@]|\.\.\.)/],u=0;u<d.length;u++)d[u]||d.splice(u--,1);var h=a.hangingIndent||i.indentUnit,p=o,m=s;null!=a.extra_keywords&&(p=p.concat(a.extra_keywords)),null!=a.extra_builtins&&(m=m.concat(a.extra_builtins));var f=!(a.version&&Number(a.version)<3);if(f){var g=a.identifiers||/^[_A-Za-z\u00A1-\uFFFF][_A-Za-z0-9\u00A1-\uFFFF]*/;p=p.concat(["nonlocal","False","True","None","async","await"]),m=m.concat(["ascii","bytes","exec","print"]);var v=new RegExp("^(([rbuf]|(br)|(fr))?('{3}|\"{3}|['\"]))","i")}else g=a.identifiers||/^[_A-Za-z][_A-Za-z0-9]*/,p=p.concat(["exec","print"]),m=m.concat(["apply","basestring","buffer","cmp","coerce","execfile","file","intern","long","raw_input","reduce","reload","unichr","unicode","xrange","False","True","None"]),v=new RegExp("^(([rubf]|(ur)|(br))?('{3}|\"{3}|['\"]))","i");var b=t(p),_=t(m);function y(e,t){var i=e.sol()&&"\\"!=t.lastToken;if(i&&(t.indent=e.indentation()),i&&"py"==n(t).type){var r=n(t).offset;if(e.eatSpace()){var o=e.indentation();return o>r?w(t):o<r&&k(e,t)&&"#"!=e.peek()&&(t.errorToken=!0),null}var s=x(e,t);return r>0&&k(e,t)&&(s+=" "+l),s}return x(e,t)}function x(e,t,i){if(e.eatSpace())return null;if(!i&&e.match(/^#.*/))return"comment";if(e.match(/^[0-9\.]/,!1)){var o=!1;if(e.match(/^[\d_]*\.\d+(e[\+\-]?\d+)?/i)&&(o=!0),e.match(/^[\d_]+\.\d*/)&&(o=!0),e.match(/^\.\d+/)&&(o=!0),o)return e.eat(/J/i),"number";var s=!1;if(e.match(/^0x[0-9a-f_]+/i)&&(s=!0),e.match(/^0b[01_]+/i)&&(s=!0),e.match(/^0o[0-7_]+/i)&&(s=!0),e.match(/^[1-9][\d_]*(e[\+\-]?[\d_]+)?/)&&(e.eat(/J/i),s=!0),e.match(/^0(?![\dx])/i)&&(s=!0),s)return e.eat(/L/i),"number"}if(e.match(v))return-1!==e.current().toLowerCase().indexOf("f")?(t.tokenize=function(e,t){for(;"rubf".indexOf(e.charAt(0).toLowerCase())>=0;)e=e.substr(1);var i=1==e.length,r="string";function o(e){return function(t,i){var r=x(t,i,!0);return"punctuation"==r&&("{"==t.current()?i.tokenize=o(e+1):"}"==t.current()&&(i.tokenize=e>1?o(e-1):s)),r}}function s(s,n){for(;!s.eol();)if(s.eatWhile(/[^'"\{\}\\]/),s.eat("\\")){if(s.next(),i&&s.eol())return r}else{if(s.match(e))return n.tokenize=t,r;if(s.match("{{"))return r;if(s.match("{",!1))return n.tokenize=o(0),s.current()?r:n.tokenize(s,n);if(s.match("}}"))return r;if(s.match("}"))return l;s.eat(/['"]/)}if(i){if(a.singleLineStringErrors)return l;n.tokenize=t}return r}return s.isString=!0,s}(e.current(),t.tokenize),t.tokenize(e,t)):(t.tokenize=function(e,t){for(;"rubf".indexOf(e.charAt(0).toLowerCase())>=0;)e=e.substr(1);var i=1==e.length,r="string";function o(o,s){for(;!o.eol();)if(o.eatWhile(/[^'"\\]/),o.eat("\\")){if(o.next(),i&&o.eol())return r}else{if(o.match(e))return s.tokenize=t,r;o.eat(/['"]/)}if(i){if(a.singleLineStringErrors)return l;s.tokenize=t}return r}return o.isString=!0,o}(e.current(),t.tokenize),t.tokenize(e,t));for(var n=0;n<d.length;n++)if(e.match(d[n]))return"operator";return e.match(c)?"punctuation":"."==t.lastToken&&e.match(g)?"property":e.match(b)||e.match(r)?"keyword":e.match(_)?"builtin":e.match(/^(self|cls)\b/)?"variable-2":e.match(g)?"def"==t.lastToken||"class"==t.lastToken?"def":"variable":(e.next(),i?null:l)}function w(e){for(;"py"!=n(e).type;)e.scopes.pop();e.scopes.push({offset:n(e).offset+i.indentUnit,type:"py",align:null})}function k(e,t){for(var i=e.indentation();t.scopes.length>1&&n(t).offset>i;){if("py"!=n(t).type)return!0;t.scopes.pop()}return n(t).offset!=i}function S(e,t){e.sol()&&(t.beginningOfLine=!0);var i=t.tokenize(e,t),r=e.current();if(t.beginningOfLine&&"@"==r)return e.match(g,!1)?"meta":f?"operator":l;if(/\S/.test(r)&&(t.beginningOfLine=!1),"variable"!=i&&"builtin"!=i||"meta"!=t.lastToken||(i="meta"),"pass"!=r&&"return"!=r||(t.dedent+=1),"lambda"==r&&(t.lambda=!0),":"==r&&!t.lambda&&"py"==n(t).type&&e.match(/^\s*(?:#|$)/,!1)&&w(t),1==r.length&&!/string|comment/.test(i)){var o="[({".indexOf(r);if(-1!=o&&function(e,t,i){var r=e.match(/^[\s\[\{\(]*(?:#|$)/,!1)?null:e.column()+1;t.scopes.push({offset:t.indent+h,type:i,align:r})}(e,t,"])}".slice(o,o+1)),-1!=(o="])}".indexOf(r))){if(n(t).type!=r)return l;t.indent=t.scopes.pop().offset-h}}return t.dedent>0&&e.eol()&&"py"==n(t).type&&(t.scopes.length>1&&t.scopes.pop(),t.dedent-=1),i}return{startState:function(e){return{tokenize:y,scopes:[{offset:e||0,type:"py",align:null}],indent:e||0,lastToken:null,lambda:!1,dedent:0}},token:function(e,t){var i=t.errorToken;i&&(t.errorToken=!1);var r=S(e,t);return r&&"comment"!=r&&(t.lastToken="keyword"==r||"punctuation"==r?e.current():r),"punctuation"==r&&(r=null),e.eol()&&t.lambda&&(t.lambda=!1),i?r+" "+l:r},indent:function(t,i){if(t.tokenize!=y)return t.tokenize.isString?e.Pass:0;var r=n(t),o=r.type==i.charAt(0);return null!=r.align?r.align-(o?1:0):r.offset-(o?h:0)},electricInput:/^\s*[\}\]\)]$/,closeBrackets:{triples:"'\""},lineComment:"#",fold:"indent"}})),e.defineMIME("text/x-python","python"),e.defineMIME("text/x-cython",{name:"python",extra_keywords:(i="by cdef cimport cpdef ctypedef enum except extern gil include nogil property public readonly struct union DEF IF ELIF ELSE",i.split(" "))})},"object"==typeof exports&&"object"==typeof module?Dl(require("../../lib/codemirror")):"function"==typeof define&&define.amd?define(["../../lib/codemirror"],Dl):Dl(CodeMirror),function(e){"object"==typeof exports&&"object"==typeof module?e(require("../../lib/codemirror")):"function"==typeof define&&define.amd?define(["../../lib/codemirror"],e):e(CodeMirror)}((function(e){e.defineMode("shell",(function(){var t={};function i(e,i){for(var r=0;r<i.length;r++)t[i[r]]=e}var r=["true","false"],o=["if","then","do","else","elif","while","until","for","in","esac","fi","fin","fil","done","exit","set","unset","export","function"],s=["ab","awk","bash","beep","cat","cc","cd","chown","chmod","chroot","clear","cp","curl","cut","diff","echo","find","gawk","gcc","get","git","grep","hg","kill","killall","ln","ls","make","mkdir","openssl","mv","nc","nl","node","npm","ping","ps","restart","rm","rmdir","sed","service","sh","shopt","shred","source","sort","sleep","ssh","start","stop","su","sudo","svn","tee","telnet","top","touch","vi","vim","wall","wc","wget","who","write","yes","zsh"];function n(e,i){if(e.eatSpace())return null;var r,o=e.sol(),s=e.next();if("\\"===s)return e.next(),null;if("'"===s||'"'===s||"`"===s)return i.tokens.unshift(a(s,"`"===s?"quote":"string")),d(e,i);if("#"===s)return o&&e.eat("!")?(e.skipToEnd(),"meta"):(e.skipToEnd(),"comment");if("$"===s)return i.tokens.unshift(c),d(e,i);if("+"===s||"="===s)return"operator";if("-"===s)return e.eat("-"),e.eatWhile(/\w/),"attribute";if("<"==s){if(e.match("<<"))return"operator";var n=e.match(/^<-?\s*['"]?([^'"]*)['"]?/);if(n)return i.tokens.unshift((r=n[1],function(e,t){return e.sol()&&e.string==r&&t.tokens.shift(),e.skipToEnd(),"string-2"})),"string-2"}if(/\d/.test(s)&&(e.eatWhile(/\d/),e.eol()||!/\w/.test(e.peek())))return"number";e.eatWhile(/[\w-]/);var l=e.current();return"="===e.peek()&&/\w+/.test(l)?"def":t.hasOwnProperty(l)?t[l]:null}function a(e,t){var i="("==e?")":"{"==e?"}":e;return function(r,o){for(var s,n=!1;null!=(s=r.next());){if(s===i&&!n){o.tokens.shift();break}if("$"===s&&!n&&"'"!==e&&r.peek()!=i){n=!0,r.backUp(1),o.tokens.unshift(c);break}if(!n&&e!==i&&s===e)return o.tokens.unshift(a(e,t)),d(r,o);if(!n&&/['"]/.test(s)&&!/['"]/.test(e)){o.tokens.unshift(l(s,"string")),r.backUp(1);break}n=!n&&"\\"===s}return t}}function l(e,t){return function(i,r){return r.tokens[0]=a(e,t),i.next(),d(i,r)}}e.registerHelper("hintWords","shell",r.concat(o,s)),i("atom",r),i("keyword",o),i("builtin",s);var c=function(e,t){t.tokens.length>1&&e.eat("$");var i=e.next();return/['"({]/.test(i)?(t.tokens[0]=a(i,"("==i?"quote":"{"==i?"def":"string"),d(e,t)):(/\d/.test(i)||e.eatWhile(/\w/),t.tokens.shift(),"def")};function d(e,t){return(t.tokens[0]||n)(e,t)}return{startState:function(){return{tokens:[]}},token:function(e,t){return d(e,t)},closeBrackets:"()[]{}''\"\"``",lineComment:"#",fold:"brace"}})),e.defineMIME("text/x-sh","shell"),e.defineMIME("application/x-sh","shell")})),function(e){"object"==typeof exports&&"object"==typeof module?e(require("../../lib/codemirror")):"function"==typeof define&&define.amd?define(["../../lib/codemirror"],e):e(CodeMirror)}((function(e){e.defineMode("yaml",(function(){var e=new RegExp("\\b(("+["true","false","on","off","yes","no"].join(")|(")+"))$","i");return{token:function(t,i){var r=t.peek(),o=i.escaped;if(i.escaped=!1,"#"==r&&(0==t.pos||/\s/.test(t.string.charAt(t.pos-1))))return t.skipToEnd(),"comment";if(t.match(/^('([^']|\\.)*'?|"([^"]|\\.)*"?)/))return"string";if(i.literal&&t.indentation()>i.keyCol)return t.skipToEnd(),"string";if(i.literal&&(i.literal=!1),t.sol()){if(i.keyCol=0,i.pair=!1,i.pairStart=!1,t.match("---"))return"def";if(t.match("..."))return"def";if(t.match(/\s*-\s+/))return"meta"}if(t.match(/^(\{|\}|\[|\])/))return"{"==r?i.inlinePairs++:"}"==r?i.inlinePairs--:"["==r?i.inlineList++:i.inlineList--,"meta";if(i.inlineList>0&&!o&&","==r)return t.next(),"meta";if(i.inlinePairs>0&&!o&&","==r)return i.keyCol=0,i.pair=!1,i.pairStart=!1,t.next(),"meta";if(i.pairStart){if(t.match(/^\s*(\||\>)\s*/))return i.literal=!0,"meta";if(t.match(/^\s*(\&|\*)[a-z0-9\._-]+\b/i))return"variable-2";if(0==i.inlinePairs&&t.match(/^\s*-?[0-9\.\,]+\s?$/))return"number";if(i.inlinePairs>0&&t.match(/^\s*-?[0-9\.\,]+\s?(?=(,|}))/))return"number";if(t.match(e))return"keyword"}return!i.pair&&t.match(/^\s*(?:[,\[\]{}&*!|>'"%@`][^\s'":]|[^,\[\]{}#&*!|>'"%@`])[^#]*?(?=\s*:($|\s))/)?(i.pair=!0,i.keyCol=t.indentation(),"atom"):i.pair&&t.match(/^:\s*/)?(i.pairStart=!0,"meta"):(i.pairStart=!1,i.escaped="\\"==r,t.next(),null)},startState:function(){return{pair:!1,pairStart:!1,keyCol:0,inlinePairs:0,inlineList:0,literal:!1,escaped:!1}},lineComment:"#",fold:"indent"}})),e.defineMIME("text/x-yaml","yaml"),e.defineMIME("text/yaml","yaml")}));let Fl=class extends k{constructor(){super(),this.config=Object(),this.mode="shell",this.theme="monokai",this.src="",this.readonly=!1,this.useLineWrapping=!1,this.required=!1,this.validationMessage="",this.validationMessageIcon="warning",this.config={tabSize:2,indentUnit:2,cursorScrollMargin:50,lineNumbers:!0,matchBrackets:!0,styleActiveLine:!0,viewportMargin:1/0,extraKeys:{}}}firstUpdated(){this._initEditor()}_initEditor(){this.editorEl.__initialized?(this.editor=this.editorEl.editor,Object.assign(this.editor.options,this.config),this.editor.setOption("lineWrapping",this.useLineWrapping),this.refresh()):setTimeout(this._initEditor.bind(this),100)}refresh(){globalThis.setTimeout((()=>this.editor.refresh()),100)}focus(){globalThis.setTimeout((()=>{this.editor.execCommand("goDocEnd"),this.editor.focus(),this.refresh()}),100)}getValue(){return this.editor.getValue()}setValue(e){this.editor.setValue(e),this.refresh()}_validateInput(){if(this.required){if(""===this.getValue())return this.showValidationMessage(),this.editorEl.style.border="2px solid red",!1;this.hideValidationMessage(),this.editorEl.style.border="none"}return!0}showValidationMessage(){this.validationMessageEl.style.display="flex"}hideValidationMessage(){this.validationMessageEl.style.display="none"}static get styles(){return[S,T,C,Be,We,$`
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
      `]}render(){return L`
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
    `}};s([y({type:Object})],Fl.prototype,"config",void 0),s([y({type:String})],Fl.prototype,"mode",void 0),s([y({type:String})],Fl.prototype,"theme",void 0),s([y({type:String})],Fl.prototype,"src",void 0),s([y({type:Boolean})],Fl.prototype,"readonly",void 0),s([y({type:Boolean})],Fl.prototype,"useLineWrapping",void 0),s([y({type:Boolean})],Fl.prototype,"required",void 0),s([y({type:String})],Fl.prototype,"validationMessage",void 0),s([y({type:String})],Fl.prototype,"validationMessageIcon",void 0),s([x("#validation-message")],Fl.prototype,"validationMessageEl",void 0),s([x("#codemirror-editor")],Fl.prototype,"editorEl",void 0),Fl=s([w("lablup-codemirror")],Fl),
/**
 * @license
 * Copyright (c) 2017 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
N("vaadin-text-field",I,{moduleId:"lumo-text-field-styles"});
/**
 * @license
 * Copyright (c) 2021 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const zl=e=>class extends(D(e)){static get properties(){return{autocomplete:{type:String},autocorrect:{type:String},autocapitalize:{type:String,reflectToAttribute:!0}}}static get delegateAttrs(){return[...super.delegateAttrs,"autocapitalize","autocomplete","autocorrect"]}get __data(){return this.__dataValue||{}}set __data(e){this.__dataValue=e}_inputElementChanged(e){super._inputElementChanged(e),e&&(e.value&&e.value!==this.value&&(console.warn(`Please define value on the <${this.localName}> component!`),e.value=""),this.value&&(e.value=this.value))}_setFocused(e){super._setFocused(e),!e&&document.hasFocus()&&this.validate()}_onInput(e){super._onInput(e),this.invalid&&this.validate()}_valueChanged(e,t){super._valueChanged(e,t),void 0!==t&&this.invalid&&this.validate()}}
/**
 * @license
 * Copyright (c) 2021 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,Wl=e=>class extends(zl(e)){static get properties(){return{maxlength:{type:Number},minlength:{type:Number},pattern:{type:String}}}static get delegateAttrs(){return[...super.delegateAttrs,"maxlength","minlength","pattern"]}static get constraints(){return[...super.constraints,"maxlength","minlength","pattern"]}constructor(){super(),this._setType("text")}get clearElement(){return this.$.clearButton}ready(){super.ready(),this.addController(new O(this,(e=>{this._setInputElement(e),this._setFocusElement(e),this.stateTarget=e,this.ariaTarget=e}))),this.addController(new F(this.inputElement,this._labelController))}}
/**
 * @license
 * Copyright (c) 2017 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;N("vaadin-text-field",z,{moduleId:"vaadin-text-field-styles"});class Bl extends(Wl(H(U(V)))){static get is(){return"vaadin-text-field"}static get template(){return W`
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
    `}static get properties(){return{maxlength:{type:Number},minlength:{type:Number}}}ready(){super.ready(),this._tooltipController=new B(this),this._tooltipController.setPosition("top"),this._tooltipController.setAriaTarget(this.inputElement),this.addController(this._tooltipController)}}j(Bl),
/**
 * @license
 * Copyright (c) 2016 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
N("vaadin-grid-filter",$`
    :host {
      display: inline-flex;
      max-width: 100%;
    }

    ::slotted(*) {
      width: 100%;
      box-sizing: border-box;
    }
  `,{moduleId:"vaadin-grid-filter-styles"});const jl=e=>class extends(G(e)){static get properties(){return{path:{type:String,sync:!0},value:{type:String,notify:!0,sync:!0},_textField:{type:Object,sync:!0}}}static get observers(){return["_filterChanged(path, value, _textField)"]}ready(){super.ready(),this._filterController=new q(this,"","vaadin-text-field",{initializer:e=>{e.addEventListener("input",(e=>{this.value=e.target.value})),this._textField=e}}),this.addController(this._filterController)}_filterChanged(e,t,i){void 0!==e&&void 0!==t&&i&&(i.value=t,this._debouncerFilterChanged=Z.debounce(this._debouncerFilterChanged,K.after(200),(()=>{this.dispatchEvent(new CustomEvent("filter-changed",{bubbles:!0}))})))}focus(){this._textField&&this._textField.focus()}}
/**
 * @license
 * Copyright (c) 2016 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;class Hl extends(jl(H(V))){static get template(){return W`<slot></slot>`}static get is(){return"vaadin-grid-filter"}}j(Hl);
/**
 * @license
 * Copyright (c) 2016 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const Ul=e=>class extends e{static get properties(){return{path:{type:String,sync:!0},header:{type:String,sync:!0}}}static get observers(){return["_onHeaderRendererOrBindingChanged(_headerRenderer, _headerCell, path, header)"]}_defaultHeaderRenderer(e,t){let i=e.firstElementChild,r=i?i.firstElementChild:void 0;i||(i=document.createElement("vaadin-grid-filter"),r=document.createElement("vaadin-text-field"),r.setAttribute("theme","small"),r.setAttribute("style","max-width: 100%;"),r.setAttribute("focus-target",""),i.appendChild(r),e.appendChild(i)),i.path=this.path,r.label=this.__getHeader(this.header,this.path)}_computeHeaderRenderer(){return this._defaultHeaderRenderer}__getHeader(e,t){return e||(t?this._generateHeader(t):void 0)}}
/**
 * @license
 * Copyright (c) 2016 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;class Vl extends(Ul(X)){static get is(){return"vaadin-grid-filter-column"}}j(Vl);let Gl=class extends E{constructor(){super(),this.is_connected=!1,this.enableLaunchButton=!1,this.hideLaunchButton=!1,this.hideEnvDialog=!1,this.hidePreOpenPortDialog=!1,this.enableInferenceWorkload=!1,this.location="",this.mode="normal",this.newSessionDialogTitle="",this.importScript="",this.importFilename="",this.imageRequirements=Object(),this.resourceLimits=Object(),this.userResourceLimit=Object(),this.aliases=Object(),this.tags=Object(),this.icons=Object(),this.imageInfo=Object(),this.kernel="",this.marker_limit=25,this.gpu_modes=[],this.gpu_step=.1,this.cpu_metric={min:"1",max:"1"},this.mem_metric={min:"1",max:"1"},this.shmem_metric={min:.0625,max:1,preferred:.0625},this.npu_device_metric={min:0,max:0},this.rocm_device_metric={min:"0",max:"0"},this.tpu_device_metric={min:"1",max:"1"},this.ipu_device_metric={min:"0",max:"0"},this.atom_device_metric={min:"0",max:"0"},this.atom_plus_device_metric={min:"0",max:"0"},this.gaudi2_device_metric={min:"0",max:"0"},this.warboy_device_metric={min:"0",max:"0"},this.rngd_device_metric={min:"0",max:"0"},this.hyperaccel_lpu_device_metric={min:"0",max:"0"},this.cluster_metric={min:1,max:1},this.cluster_mode_list=["single-node","multi-node"],this.cluster_support=!1,this.folderMapping=Object(),this.customFolderMapping=Object(),this.aggregate_updating=!1,this.resourceGauge=Object(),this.sessionType="interactive",this.ownerFeatureInitialized=!1,this.ownerDomain="",this.project_resource_monitor=!1,this._default_language_updated=!1,this._default_version_updated=!1,this._helpDescription="",this._helpDescriptionTitle="",this._helpDescriptionIcon="",this._NPUDeviceNameOnSlider="GPU",this.max_cpu_core_per_session=128,this.max_mem_per_container=1536,this.max_cuda_device_per_container=16,this.max_cuda_shares_per_container=16,this.max_rocm_device_per_container=10,this.max_tpu_device_per_container=8,this.max_ipu_device_per_container=8,this.max_atom_device_per_container=4,this.max_atom_plus_device_per_container=4,this.max_gaudi2_device_per_container=4,this.max_warboy_device_per_container=4,this.max_rngd_device_per_container=4,this.max_hyperaccel_lpu_device_per_container=4,this.max_shm_per_container=8,this.allow_manual_image_name_for_session=!1,this.cluster_size=1,this.deleteEnvInfo=Object(),this.deleteEnvRow=Object(),this.environ_values=Object(),this.vfolder_select_expansion=Object(),this.currentIndex=1,this._nonAutoMountedFolderGrid=Object(),this._modelFolderGrid=Object(),this._debug=!1,this._boundFolderToMountListRenderer=this.folderToMountListRenderer.bind(this),this._boundFolderMapRenderer=this.folderMapRenderer.bind(this),this._boundPathRenderer=this.infoHeaderRenderer.bind(this),this.scheduledTime="",this.sessionInfoObj={environment:"",version:[""]},this.launchButtonMessageTextContent=Y("session.launcher.Launch"),this.isExceedMaxCountForPreopenPorts=!1,this.maxCountForPreopenPorts=10,this.allowCustomResourceAllocation=!0,this.allowNEOSessionLauncher=!1,this.active=!1,this.ownerKeypairs=[],this.ownerGroups=[],this.ownerScalingGroups=[],this.resourceBroker=globalThis.resourceBroker,this.notification=globalThis.lablupNotification,this.environ=[],this.preOpenPorts=[],this.init_resource()}static get is(){return"backend-ai-session-launcher"}static get styles(){return[S,T,C,M,P,$`
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
      `]}init_resource(){this.versions=["Not Selected"],this.languages=[],this.gpu_mode="none",this.total_slot={},this.total_resource_group_slot={},this.total_project_slot={},this.used_slot={},this.used_resource_group_slot={},this.used_project_slot={},this.available_slot={},this.used_slot_percent={},this.used_resource_group_slot_percent={},this.used_project_slot_percent={},this.resource_templates=[],this.resource_templates_filtered=[],this.vfolders=[],this.selectedVfolders=[],this.nonAutoMountedVfolders=[],this.modelVfolders=[],this.autoMountedVfolders=[],this.default_language="",this.concurrency_used=0,this.concurrency_max=0,this.concurrency_limit=2,this.max_containers_per_session=1,this._status="inactive",this.cpu_request=1,this.mem_request=1,this.shmem_request=.0625,this.gpu_request=0,this.gpu_request_type="cuda.device",this.session_request=1,this.scaling_groups=[{name:""}],this.scaling_group="",this.sessions_list=[],this.metric_updating=!1,this.metadata_updating=!1,this.cluster_size=1,this.cluster_mode="single-node",this.ownerFeatureInitialized=!1,this.ownerDomain="",this.ownerKeypairs=[],this.ownerGroups=[],this.ownerScalingGroups=[]}firstUpdated(){var e,t,i,r,o,s;this.environment.addEventListener("selected",this.updateLanguage.bind(this)),this.version_selector.addEventListener("selected",(()=>{this.updateResourceAllocationPane()})),null===(e=this.shadowRoot)||void 0===e||e.querySelectorAll("lablup-expansion").forEach((e=>{e.addEventListener("keydown",(e=>{e.stopPropagation()}),!0)})),this.resourceGauge=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#resource-gauges"),document.addEventListener("backend-ai-group-changed",(()=>{this._updatePageVariables(!0)})),document.addEventListener("backend-ai-resource-broker-updated",(()=>{})),!0===this.hideLaunchButton&&((null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#launch-session")).style.display="none"),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.max_cpu_core_per_session=globalThis.backendaiclient._config.maxCPUCoresPerContainer||128,this.max_mem_per_container=globalThis.backendaiclient._config.maxMemoryPerContainer||1536,this.max_cuda_device_per_container=globalThis.backendaiclient._config.maxCUDADevicesPerContainer||16,this.max_cuda_shares_per_container=globalThis.backendaiclient._config.maxCUDASharesPerContainer||16,this.max_rocm_device_per_container=globalThis.backendaiclient._config.maxROCMDevicesPerContainer||10,this.max_tpu_device_per_container=globalThis.backendaiclient._config.maxTPUDevicesPerContainer||8,this.max_ipu_device_per_container=globalThis.backendaiclient._config.maxIPUDevicesPerContainer||8,this.max_atom_device_per_container=globalThis.backendaiclient._config.maxATOMDevicesPerContainer||8,this.max_atom_plus_device_per_container=globalThis.backendaiclient._config.maxATOMPlUSDevicesPerContainer||8,this.max_gaudi2_device_per_container=globalThis.backendaiclient._config.maxGaudi2DevicesPerContainer||8,this.max_warboy_device_per_container=globalThis.backendaiclient._config.maxWarboyDevicesPerContainer||8,this.max_rngd_device_per_container=globalThis.backendaiclient._config.maxRNGDDevicesPerContainer||8,this.max_hyperaccel_lpu_device_per_container=globalThis.backendaiclient._config.maxHyperaccelLPUDevicesPerContainer||8,this.max_shm_per_container=globalThis.backendaiclient._config.maxShmPerContainer||8,void 0!==globalThis.backendaiclient._config.allow_manual_image_name_for_session&&"allow_manual_image_name_for_session"in globalThis.backendaiclient._config&&""!==globalThis.backendaiclient._config.allow_manual_image_name_for_session?this.allow_manual_image_name_for_session=globalThis.backendaiclient._config.allow_manual_image_name_for_session:this.allow_manual_image_name_for_session=!1,globalThis.backendaiclient.supports("multi-container")&&(this.cluster_support=!0),this.maxCountForPreopenPorts=globalThis.backendaiclient._config.maxCountForPreopenPorts,this.allowCustomResourceAllocation=globalThis.backendaiclient._config.allowCustomResourceAllocation,this.is_connected=!0,this._debug=globalThis.backendaiwebui.debug,this._enableLaunchButton()}),{once:!0}):(this.max_cpu_core_per_session=globalThis.backendaiclient._config.maxCPUCoresPerContainer||128,this.max_mem_per_container=globalThis.backendaiclient._config.maxMemoryPerContainer||1536,this.max_cuda_device_per_container=globalThis.backendaiclient._config.maxCUDADevicesPerContainer||16,this.max_cuda_shares_per_container=globalThis.backendaiclient._config.maxCUDASharesPerContainer||16,this.max_rocm_device_per_container=globalThis.backendaiclient._config.maxROCMDevicesPerContainer||10,this.max_tpu_device_per_container=globalThis.backendaiclient._config.maxTPUDevicesPerContainer||8,this.max_ipu_device_per_container=globalThis.backendaiclient._config.maxIPUDevicesPerContainer||8,this.max_atom_device_per_container=globalThis.backendaiclient._config.maxATOMDevicesPerContainer||8,this.max_atom_plus_device_per_container=globalThis.backendaiclient._config.maxATOMPlUSDevicesPerContainer||8,this.max_gaudi2_device_per_container=globalThis.backendaiclient._config.maxGaudi2DevicesPerContainer||8,this.max_warboy_device_per_container=globalThis.backendaiclient._config.maxWarboyDevicesPerContainer||8,this.max_rngd_device_per_container=globalThis.backendaiclient._config.maxRNGDDevicesPerContainer||8,this.max_hyperaccel_lpu_device_per_container=globalThis.backendaiclient._config.maxHyperaccelLPUDevicesPerContainer||8,this.max_shm_per_container=globalThis.backendaiclient._config.maxShmPerContainer||8,void 0!==globalThis.backendaiclient._config.allow_manual_image_name_for_session&&"allow_manual_image_name_for_session"in globalThis.backendaiclient._config&&""!==globalThis.backendaiclient._config.allow_manual_image_name_for_session?this.allow_manual_image_name_for_session=globalThis.backendaiclient._config.allow_manual_image_name_for_session:this.allow_manual_image_name_for_session=!1,globalThis.backendaiclient.supports("multi-container")&&(this.cluster_support=!0),this.maxCountForPreopenPorts=globalThis.backendaiclient._config.maxCountForPreopenPorts,this.allowCustomResourceAllocation=globalThis.backendaiclient._config.allowCustomResourceAllocation,this.is_connected=!0,this._debug=globalThis.backendaiwebui.debug,this._enableLaunchButton()),this.modifyEnvDialog.addEventListener("dialog-closing-confirm",(e=>{var t;const i={},r=null===(t=this.modifyEnvContainer)||void 0===t?void 0:t.querySelectorAll(".row");Array.prototype.filter.call(r,(e=>(e=>Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>0===e.value.length)).length<=1)(e))).map((e=>(e=>{const t=Array.prototype.map.call(e.querySelectorAll("mwc-textfield"),(e=>e.value));return i[t[0]]=t[1],t})(e)));((e,t)=>{const i=Object.getOwnPropertyNames(e),r=Object.getOwnPropertyNames(t);if(i.length!=r.length)return!1;for(let r=0;r<i.length;r++){const o=i[r];if(e[o]!==t[o])return!1}return!0})(i,this.environ_values)?(this.modifyEnvDialog.closeWithConfirmation=!1,this.closeDialog("modify-env-dialog")):(this.hideEnvDialog=!0,this.openDialog("env-config-confirmation"))})),this.modifyPreOpenPortDialog.addEventListener("dialog-closing-confirm",(()=>{var e;const t=null===(e=this.modifyPreOpenPortContainer)||void 0===e?void 0:e.querySelectorAll(".row:not(.header) mwc-textfield"),i=Array.from(t).filter((e=>""!==e.value)).map((e=>e.value));var r,o;r=i,o=this.preOpenPorts,r.length===o.length&&r.every(((e,t)=>e===o[t]))?(this.modifyPreOpenPortDialog.closeWithConfirmation=!1,this.closeDialog("modify-preopen-ports-dialog")):(this.hidePreOpenPortDialog=!0,this.openDialog("preopen-ports-config-confirmation"))})),this.currentIndex=1,this.progressLength=null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelectorAll(".progress").length,this._nonAutoMountedFolderGrid=null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("#non-auto-mounted-folder-grid"),this._modelFolderGrid=null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#model-folder-grid"),globalThis.addEventListener("resize",(()=>{document.body.dispatchEvent(new Event("click"))}))}_enableLaunchButton(){this.resourceBroker.image_updating?(this.enableLaunchButton=!1,setTimeout((()=>{this._enableLaunchButton()}),1e3)):("inference"===this.mode?this.languages=this.resourceBroker.languages.filter((e=>""!==e.name&&"INFERENCE"===this.resourceBroker.imageRoles[e.name])):this.languages=this.resourceBroker.languages.filter((e=>""===e.name||"COMPUTE"===this.resourceBroker.imageRoles[e.name])),this.enableLaunchButton=!0)}_updateSelectedScalingGroup(){this.scaling_groups=this.resourceBroker.scaling_groups;const e=this.scalingGroups.items.find((e=>e.value===this.resourceBroker.scaling_group));if(""===this.resourceBroker.scaling_group||void 0===e)return void setTimeout((()=>{this._updateSelectedScalingGroup()}),500);const t=this.scalingGroups.items.indexOf(e);this.scalingGroups.select(-1),this.scalingGroups.select(t),this.scalingGroups.value=e.value,this.scalingGroups.requestUpdate()}async updateScalingGroup(e=!1,t){this.active&&(await this.resourceBroker.updateScalingGroup(e,t.target.value),!0===e?await this._refreshResourcePolicy():await this.updateResourceAllocationPane("session dialog"))}_initializeFolderMapping(){var e;this.folderMapping={};(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll(".alias")).forEach((e=>{e.value=""}))}async _updateSelectedFolder(e=!1){var t,i,r;if(this._nonAutoMountedFolderGrid&&this._nonAutoMountedFolderGrid.selectedItems){let o=this._nonAutoMountedFolderGrid.selectedItems;o=o.concat(this._modelFolderGrid.selectedItems);let s=[];o.length>0&&(s=o.map((e=>e.name)),e&&this._unselectAllSelectedFolder()),this.selectedVfolders=s;for(const e of this.selectedVfolders){if((null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#vfolder-alias-"+e)).value.length>0&&(this.folderMapping[e]=(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#vfolder-alias-"+e)).value),e in this.folderMapping&&this.selectedVfolders.includes(this.folderMapping[e]))return delete this.folderMapping[e],(null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector("#vfolder-alias-"+e)).value="",await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!0)}}return Promise.resolve(!0)}_unselectAllSelectedFolder(){[this._nonAutoMountedFolderGrid,this._modelFolderGrid].forEach((e=>{e&&e.selectedItems&&(e.selectedItems.forEach((e=>{e.selected=!1})),e.selectedItems=[])})),this.selectedVfolders=[]}_checkSelectedItems(){[this._nonAutoMountedFolderGrid,this._modelFolderGrid].forEach((e=>{if(e&&e.selectedItems){const t=e.selectedItems;let i=[];t.length>0&&(e.selectedItems=[],i=t.map((e=>null==e?void 0:e.id)),e.querySelectorAll("vaadin-checkbox").forEach((e=>{var t;i.includes(null===(t=e.__item)||void 0===t?void 0:t.id)&&(e.checked=!0)})))}}))}_preProcessingSessionInfo(){var e,t;let i,r;if(null===(e=this.manualImageName)||void 0===e?void 0:e.value){const e=this.manualImageName.value.split(":");i=e[0],r=e.slice(-1)[0].split("-")}else{if(void 0===this.kernel||!1!==(null===(t=this.version_selector)||void 0===t?void 0:t.disabled))return!1;i=this.kernel,r=this.version_selector.selectedText.split("/")}return this.sessionInfoObj.environment=i.split("/").pop(),this.sessionInfoObj.version=[r[0].toUpperCase()].concat(1!==r.length?r.slice(1).map((e=>e.toUpperCase())):[""]),!0}async _viewStateChanged(){if(await this.updateComplete,!this.active)return;const e=()=>{this.enableInferenceWorkload=globalThis.backendaiclient.supports("inference-workload")};void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.project_resource_monitor=this.resourceBroker.allow_project_resource_monitor,this._updatePageVariables(!0),this._disableEnterKey(),e()}),{once:!0}):(this.project_resource_monitor=this.resourceBroker.allow_project_resource_monitor,await this._updatePageVariables(!0),this._disableEnterKey(),e())}async _updatePageVariables(e){this.active&&!1===this.metadata_updating&&(this.metadata_updating=!0,await this.resourceBroker._updatePageVariables(e),this._updateSelectedScalingGroup(),this.sessions_list=this.resourceBroker.sessions_list,await this._refreshResourcePolicy(),this.aggregateResource("update-page-variable"),this.metadata_updating=!1)}async _refreshResourcePolicy(){return this.resourceBroker._refreshResourcePolicy().then((()=>{var e;this.concurrency_used=this.resourceBroker.concurrency_used,this.userResourceLimit=this.resourceBroker.userResourceLimit,this.concurrency_max=this.resourceBroker.concurrency_max,this.max_containers_per_session=null!==(e=this.resourceBroker.max_containers_per_session)&&void 0!==e?e:1,this.gpu_mode=this.resourceBroker.gpu_mode,this.gpu_step=this.resourceBroker.gpu_step,this.gpu_modes=this.resourceBroker.gpu_modes,this.updateResourceAllocationPane("refresh resource policy")})).catch((e=>{this.metadata_updating=!1,e&&e.message?(this.notification.text=R.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=R.relieve(e.title),this.notification.show(!0,e))}))}async _launchSessionDialog(){var e;const t=!globalThis.backendaioptions.get("classic_session_launcher",!1);if(!0===this.allowNEOSessionLauncher&&t){const e="/session/start?formValues="+encodeURIComponent(JSON.stringify({resourceGroup:this.resourceBroker.scaling_group}));return J.dispatch(Q(decodeURIComponent(e),{})),void document.dispatchEvent(new CustomEvent("react-navigate",{detail:e}))}if(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready||!0===this.resourceBroker.image_updating)setTimeout((()=>{this._launchSessionDialog()}),1e3);else{this.folderMapping=Object(),this._resetProgress(),await this.selectDefaultLanguage();const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector('lablup-expansion[name="ownership"]');globalThis.backendaiclient.is_admin?t.style.display="block":t.style.display="none",this._updateSelectedScalingGroup(),await this._refreshResourcePolicy(),this.requestUpdate(),this.newSessionDialog.show()}}_generateKernelIndex(e,t){return e+":"+t}_moveToLastProgress(){this.moveProgress(4)}_newSessionWithConfirmation(){var e,t,i,r;const o=null===(t=null===(e=this._nonAutoMountedFolderGrid)||void 0===e?void 0:e.selectedItems)||void 0===t?void 0:t.map((e=>e.name)).length,s=null===(r=null===(i=this._modelFolderGrid)||void 0===i?void 0:i.selectedItems)||void 0===r?void 0:r.map((e=>e.name)).length;if(this.currentIndex==this.progressLength){if("inference"===this.mode||void 0!==o&&o>0||void 0!==s&&s>0)return this._newSession();this.launchConfirmationDialog.show()}else this._moveToLastProgress()}_newSession(){var e,t,i,r,o,s,n,a,l,c,d,u;let h,p,m;if(this.launchConfirmationDialog.hide(),this.manualImageName&&this.manualImageName.value){const e=this.manualImageName.value.split(":");p=e.splice(-1,1)[0],h=e.join(":"),m=["x86_64","aarch64"].includes(this.manualImageName.value.split("@").pop())?this.manualImageName.value.split("@").pop():void 0,m&&(h=this.manualImageName.value.split("@")[0])}else{const s=this.environment.selected;h=null!==(e=null==s?void 0:s.id)&&void 0!==e?e:"",p=null!==(i=null===(t=this.version_selector.selected)||void 0===t?void 0:t.value)&&void 0!==i?i:"",m=null!==(o=null===(r=this.version_selector.selected)||void 0===r?void 0:r.getAttribute("architecture"))&&void 0!==o?o:void 0}this.sessionType=(null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#session-type")).value;let f=(null===(n=this.shadowRoot)||void 0===n?void 0:n.querySelector("#session-name")).value;const g=(null===(a=this.shadowRoot)||void 0===a?void 0:a.querySelector("#session-name")).checkValidity();let v=this.selectedVfolders;if(this.cpu_request=parseInt(this.cpuResourceSlider.value),this.mem_request=parseFloat(this.memoryResourceSlider.value),this.shmem_request=parseFloat(this.sharedMemoryResourceSlider.value),this.gpu_request=parseFloat(this.npuResourceSlider.value),this.session_request=parseInt(this.sessionResourceSlider.value),this.num_sessions=this.session_request,this.sessions_list.includes(f))return this.notification.text=Y("session.launcher.DuplicatedSessionName"),void this.notification.show();if(!g)return this.notification.text=Y("session.launcher.SessionNameAllowCondition"),void this.notification.show();if(""===h||""===p||"Not Selected"===p)return this.notification.text=Y("session.launcher.MustSpecifyVersion"),void this.notification.show();this.scaling_group=this.scalingGroups.value;const b={};b.group_name=globalThis.backendaiclient.current_group,b.domain=globalThis.backendaiclient._config.domainName,b.scaling_group=this.scaling_group,b.type=this.sessionType,globalThis.backendaiclient.supports("multi-container")&&(b.cluster_mode=this.cluster_mode,b.cluster_size=this.cluster_size),b.maxWaitSeconds=15;const _=null===(l=this.shadowRoot)||void 0===l?void 0:l.querySelector("#owner-enabled");if(_&&_.checked&&(b.group_name=this.ownerGroupSelect.value,b.domain=this.ownerDomain,b.scaling_group=this.ownerScalingGroupSelect.value,b.owner_access_key=this.ownerAccesskeySelect.value,!(b.group_name&&b.domain&&b.scaling_group&&b.owner_access_key)))return this.notification.text=Y("session.launcher.NotEnoughOwnershipInfo"),void this.notification.show();switch(b.cpu=this.cpu_request,this.gpu_request_type){case"cuda.shares":b["cuda.shares"]=this.gpu_request;break;case"cuda.device":b["cuda.device"]=this.gpu_request;break;case"rocm.device":b["rocm.device"]=this.gpu_request;break;case"tpu.device":b["tpu.device"]=this.gpu_request;break;case"ipu.device":b["ipu.device"]=this.gpu_request;break;case"atom.device":b["atom.device"]=this.gpu_request;break;case"atom-plus.device":b["atom-plus.device"]=this.gpu_request;break;case"gaudi2.device":b["gaudi2.device"]=this.gpu_request;break;case"warboy.device":b["warboy.device"]=this.gpu_request;break;case"rngd.device":b["rngd.device"]=this.gpu_request;break;case"hyperaccel-lpu.device":b["hyperaccel-lpu.device"]=this.gpu_request;break;default:this.gpu_request>0&&this.gpu_mode&&(b[this.gpu_mode]=this.gpu_request)}let y;"Infinity"===String(this.memoryResourceSlider.value)?b.mem=String(this.memoryResourceSlider.value):b.mem=String(this.mem_request)+"g",this.shmem_request>this.mem_request&&(this.shmem_request=this.mem_request,this.notification.text=Y("session.launcher.SharedMemorySettingIsReduced"),this.notification.show()),this.mem_request>4&&this.shmem_request<1&&(this.shmem_request=1),b.shmem=String(this.shmem_request)+"g",0==f.length&&(f=this.generateSessionId()),y=this._debug&&""!==this.manualImageName.value||this.manualImageName&&""!==this.manualImageName.value?m?h:this.manualImageName.value:this._generateKernelIndex(h,p);let x={};if("inference"===this.mode){if(!(y in this.resourceBroker.imageRuntimeConfig)||!("model-path"in this.resourceBroker.imageRuntimeConfig[y]))return this.notification.text=Y("session.launcher.ImageDoesNotProvideModelPath"),void this.notification.show();v=Object.keys(this.customFolderMapping),x[v]=this.resourceBroker.imageRuntimeConfig[y]["model-path"]}else x=this.folderMapping;if(0!==v.length&&(b.mounts=v,0!==Object.keys(x).length)){b.mount_map={};for(const e in x)({}).hasOwnProperty.call(x,e)&&(x[e].startsWith("/")?b.mount_map[e]=x[e]:b.mount_map[e]="/home/work/"+x[e])}if("import"===this.mode&&""!==this.importScript&&(b.bootstrap_script=this.importScript),"batch"===this.sessionType&&(b.startupCommand=this.commandEditor.getValue(),this.scheduledTime&&(b.startsAt=this.scheduledTime)),this.environ_values&&0!==Object.keys(this.environ_values).length&&(b.env=this.environ_values),this.preOpenPorts.length>0&&(b.preopen_ports=[...new Set(this.preOpenPorts.map((e=>Number(e))))]),!1===this.openMPSwitch.selected){const e=(null===(c=this.shadowRoot)||void 0===c?void 0:c.querySelector("#OpenMPCore")).value,t=(null===(d=this.shadowRoot)||void 0===d?void 0:d.querySelector("#OpenBLASCore")).value;b.env=null!==(u=b.env)&&void 0!==u?u:{},b.env.OMP_NUM_THREADS=e?Math.max(0,parseInt(e)).toString():"1",b.env.OPENBLAS_NUM_THREADS=t?Math.max(0,parseInt(t)).toString():"1"}this.launchButton.disabled=!0,this.launchButtonMessageTextContent=Y("session.Preparing"),this.notification.text=Y("session.PreparingSession"),this.notification.show();const w=[],k=this._getRandomString();if(this.num_sessions>1)for(let e=1;e<=this.num_sessions;e++){const t={kernelName:y,sessionName:`${f}-${k}-${e}`,architecture:m,config:b};w.push(t)}else w.push({kernelName:y,sessionName:f,architecture:m,config:b});const S=w.map((e=>this.tasker.add(Y("general.Session")+": "+e.sessionName,this._createKernel(e.kernelName,e.sessionName,e.architecture,e.config),"","session","",Y("eduapi.CreatingComputeSession"),Y("eduapi.ComputeSessionPrepared"),!0)));Promise.all(S).then((e=>{var t;this.newSessionDialog.hide(),this.launchButton.disabled=!1,this.launchButtonMessageTextContent=Y("session.launcher.ConfirmAndLaunch"),this._resetProgress(),setTimeout((()=>{this.metadata_updating=!0,this.aggregateResource("session-creation"),this.metadata_updating=!1}),1500);const i=new CustomEvent("backend-ai-session-list-refreshed",{detail:"running"});document.dispatchEvent(i),1===e.length&&"batch"!==this.sessionType&&(null===(t=e[0])||void 0===t||t.taskobj.then((e=>{let t;t="kernelId"in e?{"session-name":e.kernelId,"access-key":"",mode:this.mode}:{"session-uuid":e.sessionId,"session-name":e.sessionName,"access-key":"",mode:this.mode};const i=e.servicePorts;!0===Array.isArray(i)?t["app-services"]=i.map((e=>e.name)):t["app-services"]=[],"import"===this.mode&&(t.runtime="jupyter",t.filename=this.importFilename),"inference"===this.mode&&(t.runtime=t["app-services"].find((e=>!["ttyd","sshd"].includes(e)))),i.length>0&&globalThis.appLauncher.showLauncher(t)})).catch((e=>{}))),this._updateSelectedFolder(!1),this._initializeFolderMapping()})).catch((e=>{e&&e.message?(this.notification.text=R.relieve(e.message),e.description?this.notification.text=R.relieve(e.description):this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=R.relieve(e.title),this.notification.show(!0,e));const t=new CustomEvent("backend-ai-session-list-refreshed",{detail:"running"});document.dispatchEvent(t),this.launchButton.disabled=!1,this.launchButtonMessageTextContent=Y("session.launcher.ConfirmAndLaunch")}))}_getRandomString(){let e=Math.floor(52*Math.random()*52*52);let t="";for(let r=0;r<3;r++)t+=(i=e%52)<26?String.fromCharCode(65+i):String.fromCharCode(97+i-26),e=Math.floor(e/52);var i;return t}_createKernel(e,t,i,r){const o=globalThis.backendaiclient.createIfNotExists(e,t,r,3e4,i);return o.then((e=>{(null==e?void 0:e.created)||(this.notification.text=Y("session.launcher.SessionAlreadyExists"),this.notification.show())})).catch((e=>{e&&e.message?("statusCode"in e&&408===e.statusCode?this.notification.text=Y("session.launcher.SessionStillPreparing"):e.description?this.notification.text=R.relieve(e.description):this.notification.text=R.relieve(e.message),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=R.relieve(e.title),this.notification.show(!0,e))})),o}_hideSessionDialog(){this.newSessionDialog.hide()}_aliasName(e){const t=this.resourceBroker.imageTagAlias,i=this.resourceBroker.imageTagReplace;for(const[t,r]of Object.entries(i)){const i=new RegExp(t);if(i.test(e))return e.replace(i,r)}return e in t?t[e]:e}_updateVersions(e){if(e in this.resourceBroker.supports){{this.version_selector.disabled=!0;const t=[];for(const i of this.resourceBroker.supports[e])for(const r of this.resourceBroker.imageArchitectures[e+":"+i])t.push({version:i,architecture:r});t.sort(((e,t)=>e.version>t.version?1:-1)),t.reverse(),this.versions=t,this.kernel=e}return void 0!==this.versions?this.version_selector.layout(!0).then((()=>{this.version_selector.select(1),this.version_selector.value=this.versions[0].version,this.version_selector.architecture=this.versions[0].architecture,this._updateVersionSelectorText(this.version_selector.value,this.version_selector.architecture),this.version_selector.disabled=!1,this.environ_values={},this.updateResourceAllocationPane("update versions")})):void 0}}_updateVersionSelectorText(e,t){const i=this._getVersionInfo(e,t),r=[];i.forEach((e=>{""!==e.tag&&null!==e.tag&&r.push(e.tag)})),this.version_selector.selectedText=r.join(" / ")}generateSessionId(){let e="";const t="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";for(let i=0;i<8;i++)e+=t.charAt(Math.floor(62*Math.random()));return e+"-session"}async _updateVirtualFolderList(){return this.resourceBroker.updateVirtualFolderList().then((()=>{this.vfolders=this.resourceBroker.vfolders.filter((e=>"ready"===e.status))}))}async _aggregateResourceUse(e=""){return this.resourceBroker._aggregateCurrentResource(e).then((async e=>(this.concurrency_used=this.resourceBroker.concurrency_used,this.scaling_group=this.resourceBroker.scaling_group,this.scaling_groups=this.resourceBroker.scaling_groups,this.resource_templates=this.resourceBroker.resource_templates,this.resource_templates_filtered=this.resourceBroker.resource_templates_filtered,this.total_slot=this.resourceBroker.total_slot,this.total_resource_group_slot=this.resourceBroker.total_resource_group_slot,this.total_project_slot=this.resourceBroker.total_project_slot,this.used_slot=this.resourceBroker.used_slot,this.used_resource_group_slot=this.resourceBroker.used_resource_group_slot,this.used_project_slot=this.resourceBroker.used_project_slot,this.used_project_slot_percent=this.resourceBroker.used_project_slot_percent,this.concurrency_limit=this.resourceBroker.concurrency_limit&&this.resourceBroker.concurrency_limit>1?this.resourceBroker.concurrency_limit:1,this.available_slot=this.resourceBroker.available_slot,this.used_slot_percent=this.resourceBroker.used_slot_percent,this.used_resource_group_slot_percent=this.resourceBroker.used_resource_group_slot_percent,await this.updateComplete,Promise.resolve(!0)))).catch((e=>(e&&e.message&&(e.description?this.notification.text=R.relieve(e.description):this.notification.text=R.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)),Promise.resolve(!1))))}aggregateResource(e=""){void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._aggregateResourceUse(e)}),!0):this._aggregateResourceUse(e)}async updateResourceAllocationPane(e=""){var t,i;if(1==this.metric_updating)return;if("refresh resource policy"===e)return this.metric_updating=!1,this._aggregateResourceUse("update-metric").then((()=>this.updateResourceAllocationPane("after refresh resource policy")));const r=this.environment.selected,o=this.version_selector.selected;if(null===o)return void(this.metric_updating=!1);const s=o.value,n=o.getAttribute("architecture");if(this._updateVersionSelectorText(s,n),null==r||r.getAttribute("disabled"))this.metric_updating=!1;else if(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready)document.addEventListener("backend-ai-connected",(()=>{this.updateResourceAllocationPane(e)}),!0);else{if(this.metric_updating=!0,await this._aggregateResourceUse("update-metric"),await this._updateVirtualFolderList(),this.autoMountedVfolders=this.vfolders.filter((e=>e.name.startsWith("."))),this.enableInferenceWorkload?(this.modelVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")&&"model"===e.usage_mode)),this.nonAutoMountedVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")&&"general"===e.usage_mode))):this.nonAutoMountedVfolders=this.vfolders.filter((e=>!e.name.startsWith("."))),0===Object.keys(this.resourceBroker.resourceLimits).length)return void(this.metric_updating=!1);const e=r.id,o=s;if(""===e||""===o)return void(this.metric_updating=!1);const n=e+":"+o,a=this.resourceBroker.resourceLimits[n];if(!a)return void(this.metric_updating=!1);this.gpu_mode=this.resourceBroker.gpu_mode,this.gpu_step=this.resourceBroker.gpu_step,this.gpu_modes=this.resourceBroker.gpu_modes,globalThis.backendaiclient.supports("multi-container")&&this.cluster_size>1&&(this.gpu_step=1);const l=this.resourceBroker.available_slot;this.cpuResourceSlider.disabled=!1,this.memoryResourceSlider.disabled=!1,this.npuResourceSlider.disabled=!1,globalThis.backendaiclient.supports("multi-container")&&(this.cluster_size=1,this.clusterSizeSlider.value=this.cluster_size),this.sessionResourceSlider.disabled=!1,this.launchButton.disabled=!1,this.launchButtonMessageTextContent=Y("session.launcher.ConfirmAndLaunch");let c=!1,d={min:.0625,max:2,preferred:.0625};if(this.npu_device_metric={min:0,max:0},a.forEach((e=>{if("cpu"===e.key){const t={...e};t.min=parseInt(t.min),["cpu","mem","cuda_device","cuda_shares","rocm_device","tpu_device","ipu_device","atom_device","atom_plus_device","gaudi2_device","warboy_device","rngd.device","hyperaccel_lpu_device"].forEach((e=>{e in this.total_resource_group_slot&&(l[e]=this.total_resource_group_slot[e])})),"cpu"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null===t.max?t.max=Math.min(parseInt(this.userResourceLimit.cpu),l.cpu,this.max_cpu_core_per_session):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit.cpu),l.cpu,this.max_cpu_core_per_session):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null===t.max?t.max=Math.min(this.available_slot.cpu,this.max_cpu_core_per_session):t.max=Math.min(parseInt(t.max),l.cpu,this.max_cpu_core_per_session),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.cpuResourceSlider.disabled=!0),this.cpu_metric=t,this.cluster_support&&"single-node"===this.cluster_mode&&(this.cluster_metric.max=Math.min(t.max,this.max_containers_per_session),this.cluster_metric.min>this.cluster_metric.max?this.cluster_metric.min=this.cluster_metric.max:this.cluster_metric.min=t.min)}if("cuda.device"===e.key&&"cuda.device"==this.gpu_mode){const t={...e};t.min=parseInt(t.min),"cuda.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["cuda.device"]),parseInt(l.cuda_device),this.max_cuda_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["cuda.device"]),l.cuda_device,this.max_cuda_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.cuda_device),this.max_cuda_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.cuda_device),this.max_cuda_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this.npu_device_metric=t,this._NPUDeviceNameOnSlider="GPU"}if("cuda.shares"===e.key&&"cuda.shares"===this.gpu_mode){const t={...e};t.min=parseFloat(t.min),"cuda.shares"in this.userResourceLimit?0===parseFloat(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseFloat(this.userResourceLimit["cuda.shares"]),parseFloat(l.cuda_shares),this.max_cuda_shares_per_container):t.max=Math.min(parseFloat(t.max),parseFloat(this.userResourceLimit["cuda.shares"]),parseFloat(l.cuda_shares),this.max_cuda_shares_per_container):0===parseFloat(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseFloat(l.cuda_shares),this.max_cuda_shares_per_container):t.max=Math.min(parseFloat(t.max),parseFloat(l.cuda_shares),this.max_cuda_shares_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this.cuda_shares_metric=t,t.max>0&&(this.npu_device_metric=t),this._NPUDeviceNameOnSlider="GPU"}if("rocm.device"===e.key&&"rocm.device"===this.gpu_mode){const t={...e};t.min=parseInt(t.min),t.max=parseInt(t.max),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this.npu_device_metric=t,this._NPUDeviceNameOnSlider="GPU"}if("tpu.device"===e.key){const t={...e};t.min=parseInt(t.min),"tpu.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["tpu.device"]),parseInt(l.tpu_device),this.max_tpu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["tpu.device"]),l.tpu_device,this.max_tpu_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.tpu_device),this.max_tpu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.tpu_device),this.max_tpu_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this.npu_device_metric=t,this._NPUDeviceNameOnSlider="TPU"}if("ipu.device"===e.key){const t={...e};t.min=parseInt(t.min),"ipu.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["ipu.device"]),parseInt(l.ipu_device),this.max_ipu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["ipu.device"]),l.ipu_device,this.max_ipu_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.ipu_device),this.max_ipu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.ipu_device),this.max_ipu_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this.npu_device_metric=t,this._NPUDeviceNameOnSlider="IPU"}if("atom.device"===e.key){const t={...e};t.min=parseInt(t.min),"atom.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["atom.device"]),parseInt(l.atom_device),this.max_atom_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["atom.device"]),l.atom_device,this.max_atom_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.atom_device),this.max_atom_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.atom_device),this.max_atom_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="ATOM",this.npu_device_metric=t}if("atom-plus.device"===e.key){const t={...e};t.min=parseInt(t.min),"atom-plus.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["atom-plus.device"]),parseInt(l.atom_plus_device),this.max_atom_plus_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["atom-plus.device"]),l.atom_plus_device,this.max_atom_plus_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.atom_plus_device),this.max_atom_plus_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.atom_plus_device),this.max_atom_plus_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="ATOM+",this.npu_device_metric=t}if("gaudi2.device"===e.key){const t={...e};t.min=parseInt(t.min),"gaudi2.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["gaudi2.device"]),parseInt(l.gaudi2_device),this.max_gaudi2_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["gaudi2.device"]),l.gaudi2_device,this.max_gaudi2_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.gaudi2_device),this.max_gaudi2_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.gaudi2_device),this.max_gaudi2_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="Gaudi 2",this.npu_device_metric=t}if("warboy.device"===e.key){const t={...e};t.min=parseInt(t.min),"warboy.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["warboy.device"]),parseInt(l.cuda_device),this.max_cuda_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["warboy.device"]),l.cuda_device,this.max_cuda_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.warboy_device),this.max_warboy_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.warboy_device),this.max_warboy_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="Warboy",this.npu_device_metric=t}if("rngd.device"===e.key){const t={...e};t.min=parseInt(t.min),"rngd.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["rngd.device"]),parseInt(l.cuda_device),this.max_cuda_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["rngd.device"]),l.cuda_device,this.max_cuda_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.rngd_device),this.max_rngd_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.rngd_device),this.max_rngd_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="RNGD",this.npu_device_metric=t}if("hyperaccel-lpu.device"===e.key){const t={...e};t.min=parseInt(t.min),"hyperaccel-lpu.device"in this.userResourceLimit?0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.userResourceLimit["hyperaccel-lpu.device"]),parseInt(l.hyperaccel_lpu_device),this.max_hyperaccel_lpu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(this.userResourceLimit["hyperaccel-lpu.device"]),l.hyperaccel_lpu_device,this.max_hyperaccel_lpu_device_per_container):0===parseInt(t.max)||"Infinity"===t.max||isNaN(t.max)||null==t.max?t.max=Math.min(parseInt(this.available_slot.hyperaccel_lpu_device),this.max_hyperaccel_lpu_device_per_container):t.max=Math.min(parseInt(t.max),parseInt(l.hyperaccel_lpu_device),this.max_hyperaccel_lpu_device_per_container),t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.npuResourceSlider.disabled=!0),this._NPUDeviceNameOnSlider="Hyperaccel LPU",this.npu_device_metric=t}if("mem"===e.key){const t={...e};t.min=globalThis.backendaiclient.utils.changeBinaryUnit(t.min,"g"),t.min<.1&&(t.min=.1),t.max||(t.max=0);const i=globalThis.backendaiclient.utils.changeBinaryUnit(t.max,"g","g");if("mem"in this.userResourceLimit){const e=globalThis.backendaiclient.utils.changeBinaryUnit(this.userResourceLimit.mem,"g");isNaN(parseInt(i))||0===parseInt(i)?t.max=Math.min(parseFloat(e),l.mem,this.max_mem_per_container):t.max=Math.min(parseFloat(i),parseFloat(e),l.mem,this.max_mem_per_container)}else 0!==parseInt(t.max)&&"Infinity"!==t.max&&!0!==isNaN(t.max)?t.max=Math.min(parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(t.max,"g","g")),l.mem,this.max_mem_per_container):t.max=Math.min(l.mem,this.max_mem_per_container);t.min>=t.max&&(t.min>t.max&&(t.min=t.max,c=!0),this.memoryResourceSlider.disabled=!0),t.min=Number(t.min.toFixed(2)),t.max=Number(t.max.toFixed(2)),this.mem_metric=t}"shmem"===e.key&&(d={...e},d.preferred="preferred"in d?globalThis.backendaiclient.utils.changeBinaryUnit(d.preferred,"g","g"):.0625)})),d.max=this.max_shm_per_container,d.min=.0625,d.min>=d.max&&(d.min>d.max&&(d.min=d.max,c=!0),this.sharedMemoryResourceSlider.disabled=!0),d.min=Number(d.min.toFixed(2)),d.max=Number(d.max.toFixed(2)),this.shmem_metric=d,0==this.npu_device_metric.min&&0==this.npu_device_metric.max)if(this.npuResourceSlider.disabled=!0,this.npuResourceSlider.value=0,this.resource_templates.length>0){const e=[];for(let t=0;t<this.resource_templates.length;t++)"cuda_device"in this.resource_templates[t]||"cuda_shares"in this.resource_templates[t]?(parseFloat(this.resource_templates[t].cuda_device)<=0&&!("cuda_shares"in this.resource_templates[t])||parseFloat(this.resource_templates[t].cuda_shares)<=0&&!("cuda_device"in this.resource_templates[t])||parseFloat(this.resource_templates[t].cuda_device)<=0&&parseFloat(this.resource_templates[t].cuda_shares)<=0)&&e.push(this.resource_templates[t]):e.push(this.resource_templates[t]);this.resource_templates_filtered=e}else this.resource_templates_filtered=this.resource_templates;else this.npuResourceSlider.disabled=!1,this.npuResourceSlider.value=this.npu_device_metric.max,this.resource_templates_filtered=this.resource_templates;if(this.resource_templates_filtered.length>0){const e=this.resource_templates_filtered[0];this._chooseResourceTemplate(e),this.resourceTemplatesSelect.layout(!0).then((()=>this.resourceTemplatesSelect.layoutOptions())).then((()=>{this.resourceTemplatesSelect.select(1)}))}else this._updateResourceIndicator(this.cpu_metric.min,this.mem_metric.min,"none",0);c?(this.cpuResourceSlider.disabled=!0,this.memoryResourceSlider.disabled=!0,this.npuResourceSlider.disabled=!0,this.sessionResourceSlider.disabled=!0,this.sharedMemoryResourceSlider.disabled=!0,this.launchButton.disabled=!0,(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector(".allocation-check")).style.display="none",this.cluster_support&&(this.clusterSizeSlider.disabled=!0),this.launchButtonMessageTextContent=Y("session.launcher.NotEnoughResource")):(this.cpuResourceSlider.disabled=!1,this.memoryResourceSlider.disabled=!1,this.npuResourceSlider.disabled=!1,this.sessionResourceSlider.disabled=!1,this.sharedMemoryResourceSlider.disabled=!1,this.launchButton.disabled=!1,(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector(".allocation-check")).style.display="flex",this.cluster_support&&(this.clusterSizeSlider.disabled=!1)),this.npu_device_metric.min==this.npu_device_metric.max&&this.npu_device_metric.max<1&&(this.npuResourceSlider.disabled=!0),this.concurrency_limit<=1&&(this.sessionResourceSlider.min=1,this.sessionResourceSlider.max=2,this.sessionResourceSlider.value=1,this.sessionResourceSlider.disabled=!0),this.max_containers_per_session<=1&&"single-node"===this.cluster_mode&&(this.clusterSizeSlider.min=1,this.clusterSizeSlider.max=2,this.clusterSizeSlider.value=1,this.clusterSizeSlider.disabled=!0),this.metric_updating=!1}}updateLanguage(){const e=this.environment.selected;if(null===e)return;const t=e.id;this._updateVersions(t)}folderToMountListRenderer(e,t,i){ee(L`
        <div style="font-size:14px;text-overflow:ellipsis;overflow:hidden;">
          ${i.item.name}
        </div>
        <span style="font-size:10px;">${i.item.host}</span>
      `,e)}folderMapRenderer(e,t,i){ee(L`
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
      `,e)}infoHeaderRenderer(e,t){ee(L`
        <div class="horizontal layout center">
          <span id="vfolder-header-title">
            ${A("session.launcher.FolderAlias")}
          </span>
          <mwc-icon-button
            icon="info"
            class="fg green info"
            @click="${e=>this._showPathDescription(e)}"
          ></mwc-icon-button>
        </div>
      `,e)}_showPathDescription(e){null!=e&&e.stopPropagation(),this._helpDescriptionTitle=Y("session.launcher.FolderAlias"),this._helpDescription=Y("session.launcher.DescFolderAlias"),this._helpDescriptionIcon="",this.helpDescriptionDialog.show()}helpDescTagCount(e){let t=0;let i=e.indexOf(e);for(;-1!==i;)t++,i=e.indexOf("<p>",i+1);return t}setPathContent(e,t){var i;const r=e.children[e.children.length-1],o=r.children[r.children.length-1];if(o.children.length<t+1){const e=document.createElement("div");e.setAttribute("class","horizontal layout flex center");const t=document.createElement("mwc-checkbox");t.setAttribute("id","hide-guide");const r=document.createElement("span");r.append(document.createTextNode(`${Y("dialog.hide.DoNotShowThisAgain")}`)),e.appendChild(t),e.appendChild(r),o.appendChild(e);const s=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#hide-guide");null==s||s.addEventListener("change",(e=>{if(null!==e.target){e.stopPropagation();e.target.checked?localStorage.setItem("backendaiwebui.pathguide","false"):localStorage.setItem("backendaiwebui.pathguide","true")}}))}}async _updateFolderMap(e,t){var i,r;if(""===t)return e in this.folderMapping&&delete this.folderMapping[e],await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!0);if(e!==t){if(this.selectedVfolders.includes(t))return this.notification.text=Y("session.launcher.FolderAliasOverlapping"),this.notification.show(),delete this.folderMapping[e],(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#vfolder-alias-"+e)).value="",await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!1);for(const i in this.folderMapping)if({}.hasOwnProperty.call(this.folderMapping,i)&&this.folderMapping[i]==t)return this.notification.text=Y("session.launcher.FolderAliasOverlapping"),this.notification.show(),delete this.folderMapping[e],(null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector("#vfolder-alias-"+e)).value="",await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!1);return this.folderMapping[e]=t,await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!0)}return Promise.resolve(!0)}changed(e){console.log(e)}isEmpty(e){return 0===e.length}_toggleAdvancedSettings(){var e;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#advanced-resource-settings")).toggle()}_setClusterMode(e){this.cluster_mode=e.target.value}_setClusterSize(e){this.cluster_size=e.target.value>0?Math.round(e.target.value):0,this.clusterSizeSlider.value=this.cluster_size;let t=1;globalThis.backendaiclient.supports("multi-container")&&(this.cluster_size>1||(t=0),this.gpu_step=this.resourceBroker.gpu_step,this._setSessionLimit(t))}_setSessionLimit(e=1){e>0?(this.sessionResourceSlider.value=e,this.session_request=e,this.sessionResourceSlider.disabled=!0):(this.sessionResourceSlider.max=this.concurrency_limit,this.sessionResourceSlider.disabled=!1)}_chooseResourceTemplate(e){var t;let i;i=void 0!==(null==e?void 0:e.cpu)?e:null===(t=e.target)||void 0===t?void 0:t.closest("mwc-list-item");const r=i.cpu,o=i.mem,s=i.cuda_device,n=i.cuda_shares,a=i.rocm_device,l=i.tpu_device,c=i.ipu_device,d=i.atom_device,u=i.atom_plus_device,h=i.gaudi2_device,p=i.warboy_device,m=i.rngd_device,f=i.hyperaccel_lpu_device;let g,v;void 0!==s&&Number(s)>0||void 0!==n&&Number(n)>0?void 0===n?(g="cuda.device",v=s):(g="cuda.shares",v=n):void 0!==a&&Number(a)>0?(g="rocm.device",v=a):void 0!==l&&Number(l)>0?(g="tpu.device",v=l):void 0!==c&&Number(c)>0?(g="ipu.device",v=c):void 0!==d&&Number(d)>0?(g="atom.device",v=d):void 0!==u&&Number(u)>0?(g="atom-plus.device",v=u):void 0!==h&&Number(h)>0?(g="gaudi2.device",v=h):void 0!==p&&Number(p)>0?(g="warboy.device",v=p):void 0!==m&&Number(m)>0?(g="rngd.device",v=m):void 0!==f&&Number(f)>0?(g="hyperaccel-lpu.device",v=f):(g="none",v=0);const b=i.shmem?i.shmem:this.shmem_metric;this.shmem_request="number"!=typeof b?b.preferred:b||.0625,this._updateResourceIndicator(r,o,g,v)}_updateResourceIndicator(e,t,i,r){this.cpuResourceSlider.value=e,this.memoryResourceSlider.value=t,this.npuResourceSlider.value=r,this.sharedMemoryResourceSlider.value=this.shmem_request,this.cpu_request=e,this.mem_request=t,this.gpu_request=r,this.gpu_request_type=i}async selectDefaultLanguage(e=!1,t=""){if(!0===this._default_language_updated&&!1===e)return;""!==t?this.default_language=t:void 0!==globalThis.backendaiclient._config.default_session_environment&&"default_session_environment"in globalThis.backendaiclient._config&&""!==globalThis.backendaiclient._config.default_session_environment?this.languages.map((e=>e.name)).includes(globalThis.backendaiclient._config.default_session_environment)?this.default_language=globalThis.backendaiclient._config.default_session_environment:""!==this.languages[0].name?this.default_language=this.languages[0].name:this.default_language=this.languages[1].name:this.languages.length>1?this.default_language=this.languages[1].name:0!==this.languages.length?this.default_language=this.languages[0].name:this.default_language="index.docker.io/lablup/ngc-tensorflow";const i=this.environment.items.find((e=>e.value===this.default_language));if(void 0===i&&void 0!==globalThis.backendaiclient&&!1===globalThis.backendaiclient.ready)return setTimeout((()=>(console.log("Environment selector is not ready yet. Trying to set the default language again."),this.selectDefaultLanguage(e,t))),500),Promise.resolve(!0);const r=this.environment.items.indexOf(i);return this.environment.select(r),this._default_language_updated=!0,Promise.resolve(!0)}_selectDefaultVersion(e){return!1}async _fetchSessionOwnerGroups(){var e;this.ownerFeatureInitialized||(this.ownerGroupSelect.addEventListener("selected",this._fetchSessionOwnerScalingGroups.bind(this)),this.ownerFeatureInitialized=!0);const t=this.ownerEmailInput.value;if(!this.ownerEmailInput.checkValidity()||""===t||void 0===t)return this.notification.text=Y("credential.validation.InvalidEmailAddress"),this.notification.show(),this.ownerKeypairs=[],void(this.ownerGroups=[]);const i=await globalThis.backendaiclient.keypair.list(t,["access_key"]),r=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#owner-enabled");if(this.ownerKeypairs=i.keypairs,this.ownerKeypairs.length<1)return this.notification.text=Y("session.launcher.NoActiveKeypair"),this.notification.show(),r.checked=!1,r.disabled=!0,this.ownerKeypairs=[],void(this.ownerGroups=[]);this.ownerAccesskeySelect.layout(!0).then((()=>{this.ownerAccesskeySelect.select(0),this.ownerAccesskeySelect.createAdapter().setSelectedText(this.ownerKeypairs[0].access_key)}));try{const e=await globalThis.backendaiclient.user.get(t,["domain_name","groups {id name}"]);this.ownerDomain=e.user.domain_name,this.ownerGroups=e.user.groups}catch(e){return this.notification.text=Y("session.launcher.NotEnoughOwnershipInfo"),void this.notification.show()}this.ownerGroups.length&&this.ownerGroupSelect.layout(!0).then((()=>{this.ownerGroupSelect.select(0),this.ownerGroupSelect.createAdapter().setSelectedText(this.ownerGroups[0].name)})),r.disabled=!1}async _fetchSessionOwnerScalingGroups(){const e=this.ownerGroupSelect.value;if(!e)return void(this.ownerScalingGroups=[]);const t=await globalThis.backendaiclient.scalingGroup.list(e);this.ownerScalingGroups=t.scaling_groups,this.ownerScalingGroups&&this.ownerScalingGroupSelect.layout(!0).then((()=>{this.ownerScalingGroupSelect.select(0),this.ownerGroupSelect.createAdapter().setSelectedText(this.ownerScalingGroups[0].name)}))}async _fetchDelegatedSessionVfolder(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#owner-enabled"),i=this.ownerEmailInput.value;this.ownerKeypairs.length>0&&t&&t.checked?(await this.resourceBroker.updateVirtualFolderList(i),this.vfolders=this.resourceBroker.vfolders):await this._updateVirtualFolderList(),this.autoMountedVfolders=this.vfolders.filter((e=>e.name.startsWith("."))),this.enableInferenceWorkload?(this.modelVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")&&"model"===e.usage_mode)),this.nonAutoMountedVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")&&"general"===e.usage_mode))):this.nonAutoMountedVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")))}_toggleResourceGauge(){""==this.resourceGauge.style.display||"flex"==this.resourceGauge.style.display||"block"==this.resourceGauge.style.display?this.resourceGauge.style.display="none":(document.body.clientWidth<750?(this.resourceGauge.style.left="20px",this.resourceGauge.style.right="20px",this.resourceGauge.style.backgroundColor="var(--paper-red-800)"):this.resourceGauge.style.backgroundColor="transparent",this.resourceGauge.style.display="flex")}_showKernelDescription(e,t){e.stopPropagation();const i=t.kernelname;i in this.resourceBroker.imageInfo&&"description"in this.resourceBroker.imageInfo[i]?(this._helpDescriptionTitle=this.resourceBroker.imageInfo[i].name,this._helpDescription=this.resourceBroker.imageInfo[i].description||Y("session.launcher.NoDescriptionFound"),this._helpDescriptionIcon=t.icon,this.helpDescriptionDialog.show()):(i in this.imageInfo?this._helpDescriptionTitle=this.resourceBroker.imageInfo[i].name:this._helpDescriptionTitle=i,this._helpDescription=Y("session.launcher.NoDescriptionFound"))}_showResourceDescription(e,t){e.stopPropagation();const i={cpu:{name:Y("session.launcher.CPU"),desc:Y("session.launcher.DescCPU")},mem:{name:Y("session.launcher.Memory"),desc:Y("session.launcher.DescMemory")},shmem:{name:Y("session.launcher.SharedMemory"),desc:Y("session.launcher.DescSharedMemory")},gpu:{name:Y("session.launcher.AIAccelerator"),desc:Y("session.launcher.DescAIAccelerator")},session:{name:Y("session.launcher.TitleSession"),desc:Y("session.launcher.DescSession")},"single-node":{name:Y("session.launcher.SingleNode"),desc:Y("session.launcher.DescSingleNode")},"multi-node":{name:Y("session.launcher.MultiNode"),desc:Y("session.launcher.DescMultiNode")},"openmp-optimization":{name:Y("session.launcher.OpenMPOptimization"),desc:Y("session.launcher.DescOpenMPOptimization")}};t in i&&(this._helpDescriptionTitle=i[t].name,this._helpDescription=i[t].desc,this._helpDescriptionIcon="",this.helpDescriptionDialog.show())}_showEnvConfigDescription(e){e.stopPropagation(),this._helpDescriptionTitle=Y("session.launcher.EnvironmentVariableTitle"),this._helpDescription=Y("session.launcher.DescSetEnv"),this._helpDescriptionIcon="",this.helpDescriptionDialog.show()}_showPreOpenPortConfigDescription(e){e.stopPropagation(),this._helpDescriptionTitle=Y("session.launcher.PreOpenPortTitle"),this._helpDescription=Y("session.launcher.DescSetPreOpenPort"),this._helpDescriptionIcon="",this.helpDescriptionDialog.show()}_resourceTemplateToCustom(){this.resourceTemplatesSelect.selectedText=Y("session.launcher.CustomResourceApplied"),this._updateResourceIndicator(this.cpu_request,this.mem_request,this.gpu_mode,this.gpu_request)}_applyResourceValueChanges(e,t=!0){const i=e.target.value;switch(e.target.id.split("-")[0]){case"cpu":this.cpu_request=i;break;case"mem":this.mem_request=i;break;case"shmem":this.shmem_request=i;break;case"gpu":this.gpu_request=i;break;case"session":this.session_request=i;break;case"cluster":this._changeTotalAllocationPane()}this.requestUpdate(),t?this._resourceTemplateToCustom():this._setClusterSize(e)}_changeTotalAllocationPane(){var e,t;this._deleteAllocationPaneShadow();const i=this.clusterSizeSlider.value;if(i>1){const r=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#resource-allocated-box-shadow");for(let e=0;e<=Math.min(5,i-1);e+=1){const t=document.createElement("div");t.classList.add("horizontal","layout","center","center-justified","resource-allocated-box","allocation-shadow"),t.style.position="absolute",t.style.top="-"+(5+5*e)+"px",t.style.left=5+5*e+"px";const i=this.isDarkMode?88-2*e:245+2*e;t.style.backgroundColor="rgb("+i+","+i+","+i+")",t.style.borderColor=this.isDarkMode?"none":"rgb("+(i-10)+","+(i-10)+","+(i-10)+")",t.style.zIndex=(6-e).toString(),r.appendChild(t)}(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#total-allocation-pane")).appendChild(r)}}_deleteAllocationPaneShadow(){var e;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#resource-allocated-box-shadow")).innerHTML=""}_updateShmemLimit(){const e=parseFloat(this.memoryResourceSlider.value);let t=this.sharedMemoryResourceSlider.value;parseFloat(t)>e?(t=e,this.shmem_request=t,this.sharedMemoryResourceSlider.value=t,this.sharedMemoryResourceSlider.max=t,this.notification.text=Y("session.launcher.SharedMemorySettingIsReduced"),this.notification.show()):this.max_shm_per_container>t&&(this.sharedMemoryResourceSlider.max=e>this.max_shm_per_container?this.max_shm_per_container:e)}_roundResourceAllocation(e,t){return parseFloat(e).toFixed(t)}_conditionalGiBtoMiB(e){return e<1?this._roundResourceAllocation((1024*e).toFixed(0),2):this._roundResourceAllocation(e,2)}_conditionalGiBtoMiBunit(e){return e<1?"MiB":"GiB"}_getVersionInfo(e,t){const i=[],r=e.split("-");if(i.push({tag:this._aliasName(r[0]),color:"blue",size:"60px"}),r.length>1&&(this.kernel+":"+e in this.imageRequirements&&"framework"in this.imageRequirements[this.kernel+":"+e]?i.push({tag:this.imageRequirements[this.kernel+":"+e].framework,color:"red",size:"110px"}):i.push({tag:this._aliasName(r[1]),color:"red",size:"110px"})),i.push({tag:t,color:"lightgreen",size:"90px"}),r.length>2){let e=this._aliasName(r.slice(2).join("-"));e=e.split(":"),e.length>1?i.push({tag:e.slice(1).join(":"),app:e[0],color:"green",size:"110px"}):i.push({tag:e[0],color:"green",size:"110px"})}return i}_disableEnterKey(){var e;null===(e=this.shadowRoot)||void 0===e||e.querySelectorAll("lablup-expansion").forEach((e=>{e.onkeydown=e=>{"Enter"===e.key&&e.preventDefault()}}))}_validateInput(e){const t=e.target.closest("mwc-textfield");t.value&&(t.value=Math.round(t.value),t.value=globalThis.backendaiclient.utils.clamp(t.value,t.min,t.max))}_validateSessionName(){this.sessionName.validityTransform=(e,t)=>{if(t.valid){const t=!this.resourceBroker.sessions_list.includes(e);return t||(this.sessionName.validationMessage=Y("session.launcher.DuplicatedSessionName")),{valid:t,customError:!t}}return t.patternMismatch?(this.sessionName.validationMessage=Y("session.launcher.SessionNameAllowCondition"),{valid:t.valid,patternMismatch:!t.valid}):(this.sessionName.validationMessage=Y("session.validation.EnterValidSessionName"),{valid:t.valid,customError:!t.valid})}}_appendEnvRow(e="",t=""){var i,r;const o=null===(i=this.modifyEnvContainer)||void 0===i?void 0:i.children[this.modifyEnvContainer.children.length-1],s=this._createEnvRow(e,t);null===(r=this.modifyEnvContainer)||void 0===r||r.insertBefore(s,o)}_appendPreOpenPortRow(e=null){var t,i;const r=null===(t=this.modifyPreOpenPortContainer)||void 0===t?void 0:t.children[this.modifyPreOpenPortContainer.children.length-1],o=this._createPreOpenPortRow(e);null===(i=this.modifyPreOpenPortContainer)||void 0===i||i.insertBefore(o,r),this._updateisExceedMaxCountForPreopenPorts()}_createEnvRow(e="",t=""){const i=document.createElement("div");i.setAttribute("class","horizontal layout center row");const r=document.createElement("mwc-textfield");r.setAttribute("value",e);const o=document.createElement("mwc-textfield");o.setAttribute("value",t);const s=document.createElement("mwc-icon-button");return s.setAttribute("icon","remove"),s.setAttribute("class","green minus-btn"),s.addEventListener("click",(e=>this._removeEnvItem(e))),i.append(r),i.append(o),i.append(s),i}_createPreOpenPortRow(e){const t=document.createElement("div");t.setAttribute("class","horizontal layout center row");const i=document.createElement("mwc-textfield");e&&i.setAttribute("value",e),i.setAttribute("type","number"),i.setAttribute("min","1024"),i.setAttribute("max","65535");const r=document.createElement("mwc-icon-button");return r.setAttribute("icon","remove"),r.setAttribute("class","green minus-btn"),r.addEventListener("click",(e=>this._removePreOpenPortItem(e))),t.append(i),t.append(r),t}_removeEnvItem(e){e.target.parentNode.remove()}_removePreOpenPortItem(e){e.target.parentNode.remove(),this._updateisExceedMaxCountForPreopenPorts()}_removeEmptyEnv(){var e;const t=null===(e=this.modifyEnvContainer)||void 0===e?void 0:e.querySelectorAll(".row");Array.prototype.filter.call(t,(e=>(e=>2===Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>""===e.value)).length)(e))).map(((e,t)=>{(0!==t||this.environ.length>0)&&e.parentNode.removeChild(e)}))}_removeEmptyPreOpenPorts(){var e;const t=null===(e=this.modifyPreOpenPortContainer)||void 0===e?void 0:e.querySelectorAll(".row:not(.header)");Array.prototype.filter.call(t,(e=>(e=>1===Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>""===e.value)).length)(e))).map(((e,t)=>{(0!==t||this.preOpenPorts.length>0)&&e.parentNode.removeChild(e)})),this._updateisExceedMaxCountForPreopenPorts()}modifyEnv(){this._parseEnvVariableList(),this._saveEnvVariableList(),this.modifyEnvDialog.closeWithConfirmation=!1,this.modifyEnvDialog.hide(),this.notification.text=Y("session.launcher.EnvironmentVariableConfigurationDone"),this.notification.show()}modifyPreOpenPorts(){var e;const t=null===(e=this.modifyPreOpenPortContainer)||void 0===e?void 0:e.querySelectorAll(".row:not(.header) mwc-textfield");if(!(0===Array.from(t).filter((e=>!e.checkValidity())).length))return this.notification.text=Y("session.launcher.PreOpenPortRange"),void this.notification.show();this._parseAndSavePreOpenPortList(),this.modifyPreOpenPortDialog.closeWithConfirmation=!1,this.modifyPreOpenPortDialog.hide(),this.notification.text=Y("session.launcher.PreOpenPortConfigurationDone"),this.notification.show()}_loadEnv(){this.environ.forEach((e=>{this._appendEnvRow(e.name,e.value)}))}_loadPreOpenPorts(){this.preOpenPorts.forEach((e=>{this._appendPreOpenPortRow(e)}))}_showEnvDialog(){this._removeEmptyEnv(),this.modifyEnvDialog.closeWithConfirmation=!0,this.modifyEnvDialog.show()}_showPreOpenPortDialog(){this._removeEmptyPreOpenPorts(),this.modifyPreOpenPortDialog.closeWithConfirmation=!0,this.modifyPreOpenPortDialog.show()}_closeAndResetEnvInput(){this._clearEnvRows(!0),this.closeDialog("env-config-confirmation"),this.hideEnvDialog&&(this._loadEnv(),this.modifyEnvDialog.closeWithConfirmation=!1,this.modifyEnvDialog.hide())}_closeAndResetPreOpenPortInput(){this._clearPreOpenPortRows(!0),this.closeDialog("preopen-ports-config-confirmation"),this.hidePreOpenPortDialog&&(this._loadPreOpenPorts(),this.modifyPreOpenPortDialog.closeWithConfirmation=!1,this.modifyPreOpenPortDialog.hide())}_parseEnvVariableList(){var e;this.environ_values={};const t=null===(e=this.modifyEnvContainer)||void 0===e?void 0:e.querySelectorAll(".row:not(.header)"),i=e=>{const t=Array.prototype.map.call(e.querySelectorAll("mwc-textfield"),(e=>e.value));return this.environ_values[t[0]]=t[1],t};Array.prototype.filter.call(t,(e=>(e=>0===Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>0===e.value.length)).length)(e))).map((e=>i(e)))}_saveEnvVariableList(){this.environ=Object.entries(this.environ_values).map((([e,t])=>({name:e,value:t})))}_parseAndSavePreOpenPortList(){var e;const t=null===(e=this.modifyPreOpenPortContainer)||void 0===e?void 0:e.querySelectorAll(".row:not(.header) mwc-textfield");this.preOpenPorts=Array.from(t).filter((e=>""!==e.value)).map((e=>e.value))}_resetEnvironmentVariables(){this.environ=[],this.environ_values={},null!==this.modifyEnvDialog&&this._clearEnvRows(!0)}_resetPreOpenPorts(){this.preOpenPorts=[],null!==this.modifyPreOpenPortDialog&&this._clearPreOpenPortRows(!0)}_clearEnvRows(e=!1){var t;const i=null===(t=this.modifyEnvContainer)||void 0===t?void 0:t.querySelectorAll(".row"),r=i[0];if(!e){const e=e=>Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>e.value.length>0)).length>0;if(Array.prototype.filter.call(i,(t=>e(t))).length>0)return this.hideEnvDialog=!1,void this.openDialog("env-config-confirmation")}null==r||r.querySelectorAll("mwc-textfield").forEach((e=>{e.value=""})),i.forEach(((e,t)=>{0!==t&&e.remove()}))}_clearPreOpenPortRows(e=!1){var t;const i=null===(t=this.modifyPreOpenPortContainer)||void 0===t?void 0:t.querySelectorAll(".row"),r=i[0];if(!e){const e=e=>Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>e.value.length>0)).length>0;if(Array.prototype.filter.call(i,(t=>e(t))).length>0)return this.hidePreOpenPortDialog=!1,void this.openDialog("preopen-ports-config-confirmation")}null==r||r.querySelectorAll("mwc-textfield").forEach((e=>{e.value=""})),i.forEach(((e,t)=>{0!==t&&e.remove()}))}openDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).show()}closeDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).hide()}validateSessionLauncherInput(){if(1===this.currentIndex){const e="batch"!==this.sessionType||this.commandEditor._validateInput(),t="batch"!==this.sessionType||!this.scheduledTime||new Date(this.scheduledTime).getTime()>(new Date).getTime(),i=this.sessionName.checkValidity();if(!e||!t||!i)return!1}return!0}async moveProgress(e){var t,i,r,o;if(!this.validateSessionLauncherInput())return;const s=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#progress-0"+this.currentIndex);this.currentIndex+=e,"inference"===this.mode&&2==this.currentIndex&&(this.currentIndex+=e),this.currentIndex>this.progressLength&&(this.currentIndex=globalThis.backendaiclient.utils.clamp(this.currentIndex+e,this.progressLength,1));const n=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#progress-0"+this.currentIndex);s.classList.remove("active"),n.classList.add("active"),this.prevButton.style.visibility=1==this.currentIndex?"hidden":"visible",this.nextButton.style.visibility=this.currentIndex==this.progressLength?"hidden":"visible",this.launchButton.disabled||(this.launchButtonMessageTextContent=this.progressLength==this.currentIndex?Y("session.launcher.Launch"):Y("session.launcher.ConfirmAndLaunch")),null===(r=this._nonAutoMountedFolderGrid)||void 0===r||r.clearCache(),null===(o=this._modelFolderGrid)||void 0===o||o.clearCache(),2===this.currentIndex&&(await this._fetchDelegatedSessionVfolder(),this._checkSelectedItems())}_resetProgress(){this.moveProgress(1-this.currentIndex),this._resetEnvironmentVariables(),this._resetPreOpenPorts(),this._unselectAllSelectedFolder(),this._deleteAllocationPaneShadow()}_calculateProgress(){const e=this.progressLength>0?this.progressLength:1;return((this.currentIndex>0?this.currentIndex:1)/e).toFixed(2)}_acceleratorName(e){const t={"cuda.device":"GPU","cuda.shares":"GPU","rocm.device":"GPU","tpu.device":"TPU","ipu.device":"IPU","atom.device":"ATOM","atom-plus.device":"ATOM+","gaudi2.device":"Gaudi 2","warboy.device":"Warboy","rngd.device":"RNGD","hyperaccel-lpu.device":"Hyperaccel LPU"};return e in t?t[e]:"GPU"}_toggleEnvironmentSelectUI(){var e;const t=!!(null===(e=this.manualImageName)||void 0===e?void 0:e.value);this.environment.disabled=this.version_selector.disabled=t;const i=t?-1:1;this.environment.select(i),this.version_selector.select(i)}_toggleHPCOptimization(){var e;const t=this.openMPSwitch.selected;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#HPCOptimizationOptions")).style.display=t?"none":"block"}_toggleStartUpCommandEditor(e){var t;this.sessionType=e.target.value;const i="batch"===this.sessionType;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#batch-mode-config-section")).style.display=i?"inline-flex":"none",i&&(this.commandEditor.refresh(),this.commandEditor.focus())}_updateisExceedMaxCountForPreopenPorts(){var e,t,i;const r=null!==(i=null===(t=null===(e=this.modifyPreOpenPortContainer)||void 0===e?void 0:e.querySelectorAll("mwc-textfield"))||void 0===t?void 0:t.length)&&void 0!==i?i:0;this.isExceedMaxCountForPreopenPorts=r>=this.maxCountForPreopenPorts}render(){var e,t;return L`
      <link rel="stylesheet" href="resources/fonts/font-awesome-all.min.css" />
      <link rel="stylesheet" href="resources/custom.css" />
      <mwc-button
        class="primary-action"
        id="launch-session"
        ?disabled="${!this.enableLaunchButton}"
        icon="power_settings_new"
        @click="${()=>this._launchSessionDialog()}"
      >
        ${A("session.launcher.Start")}
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
          ${this.newSessionDialogTitle?this.newSessionDialogTitle:A("session.launcher.StartNewSession")}
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
              label="${Y("session.launcher.SessionType")}"
              required
              fixedMenuPosition
              value="${this.sessionType}"
              @selected="${e=>this._toggleStartUpCommandEditor(e)}"
            >
              ${"inference"===this.mode?L`
                    <mwc-list-item value="inference" selected>
                      ${A("session.launcher.InferenceMode")}
                    </mwc-list-item>
                  `:L`
                    <mwc-list-item value="batch">
                      ${A("session.launcher.BatchMode")}
                    </mwc-list-item>
                    <mwc-list-item value="interactive" selected>
                      ${A("session.launcher.InteractiveMode")}
                    </mwc-list-item>
                  `}
            </mwc-select>
            <mwc-select
              id="environment"
              icon="code"
              label="${Y("session.launcher.Environments")}"
              required
              fixedMenuPosition
              value="${this.default_language}"
            >
              <mwc-list-item
                selected
                graphic="icon"
                style="display:none!important;"
              >
                ${A("session.launcher.ChooseEnvironment")}
              </mwc-list-item>
              ${this.languages.map((e=>L`
                  ${!1===e.clickable?L`
                        <h5
                          style="font-size:12px;padding: 0 10px 3px 10px;margin:0; border-bottom:1px solid var(--token-colorBorder, #ccc);"
                          role="separator"
                          disabled="true"
                        >
                          ${e.basename}
                        </h5>
                      `:L`
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
                              ${e.tags?e.tags.map((e=>L`
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
              label="${Y("session.launcher.Version")}"
              required
              fixedMenuPosition
            >
              <mwc-list-item
                selected
                style="display:none!important"
              ></mwc-list-item>
              ${"Not Selected"===this.versions[0]&&1===this.versions.length?L``:L`
                    <h5
                      style="font-size:12px;padding: 0 10px 3px 15px;margin:0; border-bottom:1px solid var(--token-colorBorder, #ccc);"
                      role="separator"
                      disabled="true"
                      class="horizontal layout"
                    >
                      <div style="width:60px;">
                        ${A("session.launcher.Version")}
                      </div>
                      <div style="width:110px;">
                        ${A("session.launcher.Base")}
                      </div>
                      <div style="width:90px;">
                        ${A("session.launcher.Architecture")}
                      </div>
                      <div style="width:110px;">
                        ${A("session.launcher.Requirements")}
                      </div>
                    </h5>
                    ${this.versions.map((({version:e,architecture:t})=>L`
                        <mwc-list-item
                          id="${e}"
                          architecture="${t}"
                          value="${e}"
                          style="min-height:35px;height:auto;"
                        >
                          <span style="display:none">${e}</span>
                          <div class="horizontal layout end-justified">
                            ${this._getVersionInfo(e||"",t).map((e=>L`
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
            ${this._debug||this.allow_manual_image_name_for_session?L`
                  <mwc-textfield
                    id="image-name"
                    type="text"
                    class="flex"
                    value=""
                    icon="assignment_turned_in"
                    label="${Y("session.launcher.ManualImageName")}"
                    @change=${e=>this._toggleEnvironmentSelectUI()}
                  ></mwc-textfield>
                `:L``}
            <mwc-textfield
              id="session-name"
              placeholder="${Y("session.launcher.SessionNameOptional")}"
              pattern="^[a-zA-Z0-9]([a-zA-Z0-9\\-_\\.]{2,})[a-zA-Z0-9]$"
              minLength="4"
              maxLength="64"
              icon="label"
              helper="${Y("inputLimit.4to64chars")}"
              validationMessage="${Y("session.launcher.SessionNameAllowCondition")}"
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
                ${A("session.launcher.BatchModeConfig")}
              </span>
              <div class="horizontal layout start-justified">
                <div style="width:370px;font-size:12px;">
                  ${A("session.launcher.StartUpCommand")}*
                </div>
              </div>
              <lablup-codemirror
                id="command-editor"
                mode="shell"
                required
                validationMessage="${A("dialog.warning.Required")}"
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
                ${A("session.launcher.SetEnvironmentVariable")}
              </span>
              <div class="environment-variables-container">
                ${this.environ.length>0?L`
                      <div
                        class="horizontal flex center center-justified layout"
                        style="overflow-x:hidden;"
                      >
                        <div role="listbox">
                          <h4>
                            ${Y("session.launcher.EnvironmentVariable")}
                          </h4>
                          ${this.environ.map((e=>L`
                              <mwc-textfield
                                disabled
                                value="${e.name}"
                              ></mwc-textfield>
                            `))}
                        </div>
                        <div role="listbox" style="margin-left:15px;">
                          <h4>
                            ${Y("session.launcher.EnvironmentVariableValue")}
                          </h4>
                          ${this.environ.map((e=>L`
                              <mwc-textfield
                                disabled
                                value="${e.value}"
                              ></mwc-textfield>
                            `))}
                        </div>
                      </div>
                    `:L`
                      <div class="vertical layout center flex blank-box">
                        <span>${A("session.launcher.NoEnvConfigured")}</span>
                      </div>
                    `}
              </div>
            </lablup-expansion>
            ${this.maxCountForPreopenPorts>0?L`
                  <lablup-expansion
                    leftIconName="expand_more"
                    rightIconName="settings"
                    .rightCustomFunction="${()=>this._showPreOpenPortDialog()}"
                  >
                    <span slot="title">
                      ${A("session.launcher.SetPreopenPorts")}
                    </span>
                    <div class="preopen-ports-container">
                      ${this.preOpenPorts.length>0?L`
                            <div
                              class="horizontal flex center layout"
                              style="overflow-x:hidden;margin:auto 5px;"
                            >
                              ${this.preOpenPorts.map((e=>L`
                                  <lablup-shields
                                    color="lightgrey"
                                    description="${e}"
                                    style="padding:4px;"
                                  ></lablup-shields>
                                `))}
                            </div>
                          `:L`
                            <div class="vertical layout center flex blank-box">
                              <span>
                                ${A("session.launcher.NoPreOpenPortsConfigured")}
                              </span>
                            </div>
                          `}
                    </div>
                  </lablup-expansion>
                `:L``}
            <lablup-expansion
              name="ownership"
              style="--expansion-content-padding:15px 0;"
            >
              <span slot="title">
                ${A("session.launcher.SetSessionOwner")}
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
                    label="${Y("session.launcher.OwnerEmail")}"
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
                  label="${Y("session.launcher.OwnerAccessKey")}"
                  icon="vpn_key"
                  fixedMenuPosition
                  naturalMenuWidth
                >
                  ${this.ownerKeypairs.map((e=>L`
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
                    label="${Y("session.launcher.OwnerGroup")}"
                    icon="group_work"
                    fixedMenuPosition
                    naturalMenuWidth
                  >
                    ${this.ownerGroups.map((e=>L`
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
                    label="${Y("session.launcher.OwnerResourceGroup")}"
                    icon="storage"
                    fixedMenuPosition
                  >
                    ${this.ownerScalingGroups.map((e=>L`
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
                  <p>${A("session.launcher.LaunchSessionWithAccessKey")}</p>
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
              <span slot="title">${A("session.launcher.FolderToMount")}</span>
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
                    header="${A("session.launcher.FolderToMountList")}"
                    path="name"
                    resizable
                    .renderer="${this._boundFolderToMountListRenderer}"
                  ></vaadin-grid-filter-column>
                  <vaadin-grid-column
                    width="135px"
                    path=" ${A("session.launcher.FolderAlias")}"
                    .renderer="${this._boundFolderMapRenderer}"
                    .headerRenderer="${this._boundPathRenderer}"
                  ></vaadin-grid-column>
                </vaadin-grid>
                ${this.vfolders.length>0?L``:L`
                      <div class="vertical layout center flex blank-box-medium">
                        <span>
                          ${A("session.launcher.NoAvailableFolderToMount")}
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
                ${A("session.launcher.ModelStorageToMount")}
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
                    header="${A("session.launcher.ModelStorageToMount")}"
                    path="name"
                    resizable
                    .renderer="${this._boundFolderToMountListRenderer}"
                  ></vaadin-grid-filter-column>
                  <vaadin-grid-column
                    width="135px"
                    path=" ${A("session.launcher.FolderAlias")}"
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
              <span slot="title">${A("session.launcher.MountedFolders")}</span>
              <div class="vfolder-mounted-list">
                ${this.selectedVfolders.length>0||this.autoMountedVfolders.length>0?L`
                      <ul class="vfolder-list">
                        ${this.selectedVfolders.map((e=>L`
                            <li>
                              <mwc-icon>folder_open</mwc-icon>
                              ${e}
                              ${e in this.folderMapping?this.folderMapping[e].startsWith("/")?L`
                                      (&#10140; ${this.folderMapping[e]})
                                    `:L`
                                      (&#10140;
                                      /home/work/${this.folderMapping[e]})
                                    `:L`
                                    (&#10140; /home/work/${e})
                                  `}
                            </li>
                          `))}
                        ${this.autoMountedVfolders.map((e=>L`
                            <li>
                              <mwc-icon>folder_special</mwc-icon>
                              ${e.name}
                            </li>
                          `))}
                      </ul>
                    `:L`
                      <div class="vertical layout center flex blank-box-large">
                        <span>${A("session.launcher.NoFolderMounted")}</span>
                      </div>
                    `}
              </div>
            </lablup-expansion>
          </div>
          <div id="progress-03" class="progress center layout fade">
            <div class="horizontal center layout">
              <mwc-select
                id="scaling-groups"
                label="${Y("session.launcher.ResourceGroup")}"
                icon="storage"
                required
                fixedMenuPosition
                @selected="${e=>this.updateScalingGroup(!0,e)}"
              >
                ${this.scaling_groups.map((e=>L`
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
                label="${this.isEmpty(this.resource_templates_filtered)?"":Y("session.launcher.ResourceAllocation")}"
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
                    ${A("session.launcher.SharedMemory")}
                  </div>
                  <div style="width:90px;text-align:right;">
                    ${A("session.launcher.Accelerator")}
                  </div>
                </h5>
                ${this.resource_templates_filtered.map((e=>L`
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
                          ${e.shmem?L`
                                ${parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(e.shared_memory,"g")).toFixed(2)}
                                GiB
                              `:L`
                                64MB
                              `}
                        </div>
                        <div style="width:80px;text-align:right;">
                          ${e.cuda_device&&e.cuda_device>0?L`
                                ${e.cuda_device} GPU
                              `:L``}
                          ${e.cuda_shares&&e.cuda_shares>0?L`
                                ${e.cuda_shares} GPU
                              `:L``}
                          ${e.rocm_device&&e.rocm_device>0?L`
                                ${e.rocm_device} GPU
                              `:L``}
                          ${e.tpu_device&&e.tpu_device>0?L`
                                ${e.tpu_device} TPU
                              `:L``}
                          ${e.ipu_device&&e.ipu_device>0?L`
                                ${e.ipu_device} IPU
                              `:L``}
                          ${e.atom_device&&e.atom_device>0?L`
                                ${e.atom_device} ATOM
                              `:L``}
                          ${e.atom_plus_device&&e.atom_plus_device>0?L`
                                ${e.atom_plus_device} ATOM+
                              `:L``}
                          ${e.gaudi2_device&&e.gaudi2_device>0?L`
                                ${e.gaudi2_device} Gaudi 2
                              `:L``}
                          ${e.warboy_device&&e.warboy_device>0?L`
                                ${e.warboy_device} Warboy
                              `:L``}
                          ${e.rngd_device&&e.rngd_device>0?L`
                                ${e.rngd_device} RNGD
                              `:L``}
                          ${e.hyperaccel_lpu_device&&e.hyperaccel_lpu_device>0?L`
                                ${e.hyperaccel_lpu_device} Hyperaccel LPU
                              `:L``}
                        </div>
                        <div style="display:none">)</div>
                      </div>
                    </mwc-list-item>
                  `))}
                ${this.isEmpty(this.resource_templates_filtered)?L`
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
                          <h4>${A("session.launcher.NoSuitablePreset")}</h4>
                          <div style="font-size:12px;">
                            Use advanced settings to
                            <br />
                            start custom session
                          </div>
                        </div>
                      </mwc-list-item>
                    `:L``}
              </mwc-select>
            </div>
            <lablup-expansion
              name="resource-group"
              style="display:${this.allowCustomResourceAllocation?"block":"none"}"
            >
              <span slot="title">
                ${A("session.launcher.CustomAllocation")}
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
                      suffix="${Y("session.launcher.Core")}"
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
                    <div>${A("session.launcher.SharedMemory")}</div>
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
                    <div>${A("webui.menu.AIAccelerator")}</div>
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
                    <div>${A("webui.menu.Sessions")}</div>
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
            ${this.cluster_support?L`
                  <mwc-select
                    id="cluster-mode"
                    label="${Y("session.launcher.ClusterMode")}"
                    required
                    icon="account_tree"
                    fixedMenuPosition
                    value="${this.cluster_mode}"
                    @change="${e=>this._setClusterMode(e)}"
                  >
                    ${this.cluster_mode_list.map((e=>L`
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
                              ${A("single-node"===e?"session.launcher.SingleNode":"session.launcher.MultiNode")}
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
                          ${A("session.launcher.ClusterSize")}
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
                          suffix="${"single-node"===this.cluster_mode?Y("session.launcher.Container"):Y("session.launcher.Node")}"
                        ></lablup-slider>
                      </div>
                    </div>
                  </div>
                `:L``}
            <lablup-expansion name="hpc-option-group">
              <span slot="title">
                ${A("session.launcher.HPCOptimization")}
              </span>
              <div class="vertical center layout">
                <div class="horizontal center center-justified flex layout">
                  <div style="width:313px;">
                    ${A("session.launcher.SwitchOpenMPoptimization")}
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
                      ${A("session.launcher.NumOpenMPthreads")}
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
                      ${A("session.launcher.NumOpenBLASthreads")}
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
            <p class="title">${A("session.SessionInfo")}</p>
            <div class="vertical layout cluster-total-allocation-container">
              ${this._preProcessingSessionInfo()?L`
                    <div
                      class="vertical layout"
                      style="margin-left:10px;margin-bottom:5px;"
                    >
                      <div class="horizontal layout">
                        <div style="margin-right:5px;width:150px;">
                          ${A("session.EnvironmentInfo")}
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
                            ${this.sessionInfoObj.version.map(((e,t)=>t>0?L`
                                  <lablup-shields
                                    color="green"
                                    description="${e}"
                                    ui="round"
                                    style="margin-top:3px;margin-right:3px;"
                                  ></lablup-shields>
                                `:L``))}
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
                          ${A("registry.ProjectName")}
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
                          ${A("session.ResourceGroup")}
                        </div>
                        <div class="vertical layout">${this.scaling_group}</div>
                      </div>
                    </div>
                  `:L``}
            </div>
            <p class="title">${A("session.launcher.TotalAllocation")}</p>
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
                    <p>${A("session.launcher.CPU")}</p>
                    <span>
                      ${this.cpu_request*this.cluster_size*this.session_request}
                    </span>
                    <p>Core</p>
                  </div>
                  <div
                    class="vertical layout center center-justified resource-allocated"
                  >
                    <p>${A("session.launcher.Memory")}</p>
                    <span>
                      ${this._roundResourceAllocation(this.mem_request*this.cluster_size*this.session_request,1)}
                    </span>
                    <p>GiB</p>
                  </div>
                  <div
                    class="vertical layout center center-justified resource-allocated"
                  >
                    <p>${A("session.launcher.SharedMemoryAbbr")}</p>
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
                    <p>${A("session.launcher.GPUSlot")}</p>
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
                      <p>${A("session.launcher.CPU")}</p>
                      <span>${this.cpu_request}</span>
                      <p>Core</p>
                    </div>
                    <div
                      class="vertical layout center center-justified resource-allocated"
                    >
                      <p>${A("session.launcher.Memory")}</p>
                      <span>
                        ${this._roundResourceAllocation(this.mem_request,1)}
                      </span>
                      <p>GiB</p>
                    </div>
                    <div
                      class="vertical layout center center-justified resource-allocated"
                    >
                      <p>${A("session.launcher.SharedMemoryAbbr")}</p>
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
                      <p>${A("session.launcher.GPUSlot")}</p>
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
                  <p class="small">${A("session.launcher.Container")}</p>
                </div>
                <div
                  class="vertical layout center center-justified cluster-allocated"
                  style="z-index:10;"
                >
                  <div class="horizontal layout">
                    <p>${this.cluster_mode,""}</p>
                    <span style="text-align:center;">
                      ${"single-node"===this.cluster_mode?A("session.launcher.SingleNode"):A("session.launcher.MultiNode")}
                    </span>
                  </div>
                  <p class="small">${A("session.launcher.AllocateNode")}</p>
                </div>
              </div>
            </div>
            ${"inference"!==this.mode?L`
                  <p class="title">${A("session.launcher.MountedFolders")}</p>
                  <div
                    id="mounted-folders-container"
                    class="cluster-total-allocation-container"
                  >
                    ${this.selectedVfolders.length>0||this.autoMountedVfolders.length>0?L`
                          <ul class="vfolder-list">
                            ${this.selectedVfolders.map((e=>L`
                                <li>
                                  <mwc-icon>folder_open</mwc-icon>
                                  ${e}
                                  ${e in this.folderMapping?this.folderMapping[e].startsWith("/")?L`
                                          (&#10140; ${this.folderMapping[e]})
                                        `:L`
                                          (&#10140;
                                          /home/work/${this.folderMapping[e]})
                                        `:L`
                                        (&#10140; /home/work/${e})
                                      `}
                                </li>
                              `))}
                            ${this.autoMountedVfolders.map((e=>L`
                                <li>
                                  <mwc-icon>folder_special</mwc-icon>
                                  ${e.name}
                                </li>
                              `))}
                          </ul>
                        `:L`
                          <div class="vertical layout center flex blank-box">
                            <span>
                              ${A("session.launcher.NoFolderMounted")}
                            </span>
                          </div>
                        `}
                  </div>
                `:L``}
            <p class="title">
              ${A("session.launcher.EnvironmentVariablePaneTitle")}
            </p>
            <div
              class="environment-variables-container cluster-total-allocation-container"
            >
              ${this.environ.length>0?L`
                    <div
                      class="horizontal flex center center-justified layout"
                      style="overflow-x:hidden;"
                    >
                      <div role="listbox">
                        <h4>
                          ${Y("session.launcher.EnvironmentVariable")}
                        </h4>
                        ${this.environ.map((e=>L`
                            <mwc-textfield
                              disabled
                              value="${e.name}"
                            ></mwc-textfield>
                          `))}
                      </div>
                      <div role="listbox" style="margin-left:15px;">
                        <h4>
                          ${Y("session.launcher.EnvironmentVariableValue")}
                        </h4>
                        ${this.environ.map((e=>L`
                            <mwc-textfield
                              disabled
                              value="${e.value}"
                            ></mwc-textfield>
                          `))}
                      </div>
                    </div>
                  `:L`
                    <div class="vertical layout center flex blank-box">
                      <span>${A("session.launcher.NoEnvConfigured")}</span>
                    </div>
                  `}
            </div>
            ${this.maxCountForPreopenPorts>0?L`
                  <p class="title">
                    ${A("session.launcher.PreOpenPortPanelTitle")}
                  </p>
                  <div
                    class="preopen-ports-container cluster-total-allocation-container"
                  >
                    ${this.preOpenPorts.length>0?L`
                          <div
                            class="horizontal flex center layout"
                            style="overflow-x:hidden;margin:auto 5px;"
                          >
                            ${this.preOpenPorts.map((e=>L`
                                <lablup-shields
                                  color="lightgrey"
                                  description="${e}"
                                  style="padding:4px;"
                                ></lablup-shields>
                              `))}
                          </div>
                        `:L`
                          <div class="vertical layout center flex blank-box">
                            <span>
                              ${A("session.launcher.NoPreOpenPortsConfigured")}
                            </span>
                          </div>
                        `}
                  </div>
                `:L``}
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
          ${A("session.launcher.SetEnvironmentVariable")}
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
            <div>${A("session.launcher.EnvironmentVariable")}</div>
            <div>${A("session.launcher.EnvironmentVariableValue")}</div>
          </div>
          <div id="modify-env-fields-container" class="layout center">
            ${this.environ.forEach((e=>L`
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
            label="${Y("button.Reset")}"
            @click="${()=>this._clearEnvRows()}"
          ></mwc-button>
          <mwc-button
            unelevated
            slot="footer"
            icon="check"
            style="width:100px"
            label="${Y("button.Save")}"
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
        <span slot="title">${A("session.launcher.SetPreopenPorts")}</span>
        <span slot="action">
          <mwc-icon-button
            icon="info"
            @click="${e=>this._showPreOpenPortConfigDescription(e)}"
            style="pointer-events: auto;"
          ></mwc-icon-button>
        </span>
        <div slot="content" id="modify-preopen-ports-container">
          <div class="horizontal layout center flex justified header">
            <div>${A("session.launcher.PortsTitleWithRange")}</div>
          </div>
          <div class="layout center">
            ${this.preOpenPorts.forEach((e=>L`
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
            label="${Y("button.Reset")}"
            @click="${()=>this._clearPreOpenPortRows()}"
          ></mwc-button>
          <mwc-button
            unelevated
            slot="footer"
            icon="check"
            style="width:100px"
            label="${Y("button.Save")}"
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
          ${""==this._helpDescriptionIcon?L``:L`
                <img
                  slot="graphic"
                  alt="help icon"
                  src="resources/icons/${this._helpDescriptionIcon}"
                  style="width:64px;height:64px;margin-right:10px;"
                />
              `}
          <div style="font-size:14px;">
            ${te(this._helpDescription)}
          </div>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="launch-confirmation-dialog" warning fixed backdrop>
        <span slot="title">${A("session.launcher.NoFolderMounted")}</span>
        <div slot="content" class="vertical layout">
          <p>${A("session.launcher.HomeDirectoryDeletionDialog")}</p>
          <p>${A("session.launcher.LaunchConfirmationDialog")}</p>
          <p>${A("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            unelevated
            class="launch-confirmation-button"
            id="launch-confirmation-button"
            icon="rowing"
            @click="${()=>this._newSession()}"
          >
            ${A("session.launcher.Launch")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="env-config-confirmation" warning fixed>
        <span slot="title">${A("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${A("session.launcher.EnvConfigWillDisappear")}</p>
          <p>${A("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            id="env-config-remain-button"
            label="${Y("button.Cancel")}"
            @click="${()=>this.closeDialog("env-config-confirmation")}"
            style="width:auto;margin-right:10px;"
          ></mwc-button>
          <mwc-button
            unelevated
            id="env-config-reset-button"
            label="${Y("button.DismissAndProceed")}"
            @click="${()=>this._closeAndResetEnvInput()}"
            style="width:auto;"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="preopen-ports-config-confirmation" warning fixed>
        <span slot="title">${A("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${A("session.launcher.PrePortConfigWillDisappear")}</p>
          <p>${A("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            id="preopen-ports-remain-button"
            label="${Y("button.Cancel")}"
            @click="${()=>this.closeDialog("preopen-ports-config-confirmation")}"
            style="width:auto;margin-right:10px;"
          ></mwc-button>
          <mwc-button
            unelevated
            id="preopen-ports-config-reset-button"
            label="${Y("button.DismissAndProceed")}"
            @click="${()=>this._closeAndResetPreOpenPortInput()}"
            style="width:auto;"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};s([y({type:Boolean})],Gl.prototype,"is_connected",void 0),s([y({type:Boolean})],Gl.prototype,"enableLaunchButton",void 0),s([y({type:Boolean})],Gl.prototype,"hideLaunchButton",void 0),s([y({type:Boolean})],Gl.prototype,"hideEnvDialog",void 0),s([y({type:Boolean})],Gl.prototype,"hidePreOpenPortDialog",void 0),s([y({type:Boolean})],Gl.prototype,"enableInferenceWorkload",void 0),s([y({type:String})],Gl.prototype,"location",void 0),s([y({type:String})],Gl.prototype,"mode",void 0),s([y({type:String})],Gl.prototype,"newSessionDialogTitle",void 0),s([y({type:String})],Gl.prototype,"importScript",void 0),s([y({type:String})],Gl.prototype,"importFilename",void 0),s([y({type:Object})],Gl.prototype,"imageRequirements",void 0),s([y({type:Object})],Gl.prototype,"resourceLimits",void 0),s([y({type:Object})],Gl.prototype,"userResourceLimit",void 0),s([y({type:Object})],Gl.prototype,"aliases",void 0),s([y({type:Object})],Gl.prototype,"tags",void 0),s([y({type:Object})],Gl.prototype,"icons",void 0),s([y({type:Object})],Gl.prototype,"imageInfo",void 0),s([y({type:String})],Gl.prototype,"kernel",void 0),s([y({type:Array})],Gl.prototype,"versions",void 0),s([y({type:Array})],Gl.prototype,"languages",void 0),s([y({type:Number})],Gl.prototype,"marker_limit",void 0),s([y({type:String})],Gl.prototype,"gpu_mode",void 0),s([y({type:Array})],Gl.prototype,"gpu_modes",void 0),s([y({type:Number})],Gl.prototype,"gpu_step",void 0),s([y({type:Object})],Gl.prototype,"cpu_metric",void 0),s([y({type:Object})],Gl.prototype,"mem_metric",void 0),s([y({type:Object})],Gl.prototype,"shmem_metric",void 0),s([y({type:Object})],Gl.prototype,"npu_device_metric",void 0),s([y({type:Object})],Gl.prototype,"cuda_shares_metric",void 0),s([y({type:Object})],Gl.prototype,"rocm_device_metric",void 0),s([y({type:Object})],Gl.prototype,"tpu_device_metric",void 0),s([y({type:Object})],Gl.prototype,"ipu_device_metric",void 0),s([y({type:Object})],Gl.prototype,"atom_device_metric",void 0),s([y({type:Object})],Gl.prototype,"atom_plus_device_metric",void 0),s([y({type:Object})],Gl.prototype,"gaudi2_device_metric",void 0),s([y({type:Object})],Gl.prototype,"warboy_device_metric",void 0),s([y({type:Object})],Gl.prototype,"rngd_device_metric",void 0),s([y({type:Object})],Gl.prototype,"hyperaccel_lpu_device_metric",void 0),s([y({type:Object})],Gl.prototype,"cluster_metric",void 0),s([y({type:Array})],Gl.prototype,"cluster_mode_list",void 0),s([y({type:Boolean})],Gl.prototype,"cluster_support",void 0),s([y({type:Object})],Gl.prototype,"images",void 0),s([y({type:Object})],Gl.prototype,"total_slot",void 0),s([y({type:Object})],Gl.prototype,"total_resource_group_slot",void 0),s([y({type:Object})],Gl.prototype,"total_project_slot",void 0),s([y({type:Object})],Gl.prototype,"used_slot",void 0),s([y({type:Object})],Gl.prototype,"used_resource_group_slot",void 0),s([y({type:Object})],Gl.prototype,"used_project_slot",void 0),s([y({type:Object})],Gl.prototype,"available_slot",void 0),s([y({type:Number})],Gl.prototype,"concurrency_used",void 0),s([y({type:Number})],Gl.prototype,"concurrency_max",void 0),s([y({type:Number})],Gl.prototype,"concurrency_limit",void 0),s([y({type:Number})],Gl.prototype,"max_containers_per_session",void 0),s([y({type:Array})],Gl.prototype,"vfolders",void 0),s([y({type:Array})],Gl.prototype,"selectedVfolders",void 0),s([y({type:Array})],Gl.prototype,"autoMountedVfolders",void 0),s([y({type:Array})],Gl.prototype,"modelVfolders",void 0),s([y({type:Array})],Gl.prototype,"nonAutoMountedVfolders",void 0),s([y({type:Object})],Gl.prototype,"folderMapping",void 0),s([y({type:Object})],Gl.prototype,"customFolderMapping",void 0),s([y({type:Object})],Gl.prototype,"used_slot_percent",void 0),s([y({type:Object})],Gl.prototype,"used_resource_group_slot_percent",void 0),s([y({type:Object})],Gl.prototype,"used_project_slot_percent",void 0),s([y({type:Array})],Gl.prototype,"resource_templates",void 0),s([y({type:Array})],Gl.prototype,"resource_templates_filtered",void 0),s([y({type:String})],Gl.prototype,"default_language",void 0),s([y({type:Number})],Gl.prototype,"cpu_request",void 0),s([y({type:Number})],Gl.prototype,"mem_request",void 0),s([y({type:Number})],Gl.prototype,"shmem_request",void 0),s([y({type:Number})],Gl.prototype,"gpu_request",void 0),s([y({type:String})],Gl.prototype,"gpu_request_type",void 0),s([y({type:Number})],Gl.prototype,"session_request",void 0),s([y({type:Boolean})],Gl.prototype,"_status",void 0),s([y({type:Number})],Gl.prototype,"num_sessions",void 0),s([y({type:String})],Gl.prototype,"scaling_group",void 0),s([y({type:Array})],Gl.prototype,"scaling_groups",void 0),s([y({type:Array})],Gl.prototype,"sessions_list",void 0),s([y({type:Boolean})],Gl.prototype,"metric_updating",void 0),s([y({type:Boolean})],Gl.prototype,"metadata_updating",void 0),s([y({type:Boolean})],Gl.prototype,"aggregate_updating",void 0),s([y({type:Object})],Gl.prototype,"scaling_group_selection_box",void 0),s([y({type:Object})],Gl.prototype,"resourceGauge",void 0),s([y({type:String})],Gl.prototype,"sessionType",void 0),s([y({type:Boolean})],Gl.prototype,"ownerFeatureInitialized",void 0),s([y({type:String})],Gl.prototype,"ownerDomain",void 0),s([y({type:Array})],Gl.prototype,"ownerKeypairs",void 0),s([y({type:Array})],Gl.prototype,"ownerGroups",void 0),s([y({type:Array})],Gl.prototype,"ownerScalingGroups",void 0),s([y({type:Boolean})],Gl.prototype,"project_resource_monitor",void 0),s([y({type:Boolean})],Gl.prototype,"_default_language_updated",void 0),s([y({type:Boolean})],Gl.prototype,"_default_version_updated",void 0),s([y({type:String})],Gl.prototype,"_helpDescription",void 0),s([y({type:String})],Gl.prototype,"_helpDescriptionTitle",void 0),s([y({type:String})],Gl.prototype,"_helpDescriptionIcon",void 0),s([y({type:String})],Gl.prototype,"_NPUDeviceNameOnSlider",void 0),s([y({type:Number})],Gl.prototype,"max_cpu_core_per_session",void 0),s([y({type:Number})],Gl.prototype,"max_mem_per_container",void 0),s([y({type:Number})],Gl.prototype,"max_cuda_device_per_container",void 0),s([y({type:Number})],Gl.prototype,"max_cuda_shares_per_container",void 0),s([y({type:Number})],Gl.prototype,"max_rocm_device_per_container",void 0),s([y({type:Number})],Gl.prototype,"max_tpu_device_per_container",void 0),s([y({type:Number})],Gl.prototype,"max_ipu_device_per_container",void 0),s([y({type:Number})],Gl.prototype,"max_atom_device_per_container",void 0),s([y({type:Number})],Gl.prototype,"max_atom_plus_device_per_container",void 0),s([y({type:Number})],Gl.prototype,"max_gaudi2_device_per_container",void 0),s([y({type:Number})],Gl.prototype,"max_warboy_device_per_container",void 0),s([y({type:Number})],Gl.prototype,"max_rngd_device_per_container",void 0),s([y({type:Number})],Gl.prototype,"max_hyperaccel_lpu_device_per_container",void 0),s([y({type:Number})],Gl.prototype,"max_shm_per_container",void 0),s([y({type:Boolean})],Gl.prototype,"allow_manual_image_name_for_session",void 0),s([y({type:Object})],Gl.prototype,"resourceBroker",void 0),s([y({type:Number})],Gl.prototype,"cluster_size",void 0),s([y({type:String})],Gl.prototype,"cluster_mode",void 0),s([y({type:Object})],Gl.prototype,"deleteEnvInfo",void 0),s([y({type:Object})],Gl.prototype,"deleteEnvRow",void 0),s([y({type:Array})],Gl.prototype,"environ",void 0),s([y({type:Array})],Gl.prototype,"preOpenPorts",void 0),s([y({type:Object})],Gl.prototype,"environ_values",void 0),s([y({type:Object})],Gl.prototype,"vfolder_select_expansion",void 0),s([y({type:Number})],Gl.prototype,"currentIndex",void 0),s([y({type:Number})],Gl.prototype,"progressLength",void 0),s([y({type:Object})],Gl.prototype,"_nonAutoMountedFolderGrid",void 0),s([y({type:Object})],Gl.prototype,"_modelFolderGrid",void 0),s([y({type:Boolean})],Gl.prototype,"_debug",void 0),s([y({type:Object})],Gl.prototype,"_boundFolderToMountListRenderer",void 0),s([y({type:Object})],Gl.prototype,"_boundFolderMapRenderer",void 0),s([y({type:Object})],Gl.prototype,"_boundPathRenderer",void 0),s([y({type:String})],Gl.prototype,"scheduledTime",void 0),s([y({type:Object})],Gl.prototype,"schedulerTimer",void 0),s([y({type:Object})],Gl.prototype,"sessionInfoObj",void 0),s([y({type:String})],Gl.prototype,"launchButtonMessageTextContent",void 0),s([y({type:Boolean})],Gl.prototype,"isExceedMaxCountForPreopenPorts",void 0),s([y({type:Number})],Gl.prototype,"maxCountForPreopenPorts",void 0),s([y({type:Boolean})],Gl.prototype,"allowCustomResourceAllocation",void 0),s([y({type:Boolean})],Gl.prototype,"allowNEOSessionLauncher",void 0),s([x("#image-name")],Gl.prototype,"manualImageName",void 0),s([x("#version")],Gl.prototype,"version_selector",void 0),s([x("#environment")],Gl.prototype,"environment",void 0),s([x("#owner-group")],Gl.prototype,"ownerGroupSelect",void 0),s([x("#scaling-groups")],Gl.prototype,"scalingGroups",void 0),s([x("#resource-templates")],Gl.prototype,"resourceTemplatesSelect",void 0),s([x("#owner-scaling-group")],Gl.prototype,"ownerScalingGroupSelect",void 0),s([x("#owner-accesskey")],Gl.prototype,"ownerAccesskeySelect",void 0),s([x("#owner-email")],Gl.prototype,"ownerEmailInput",void 0),s([x("#vfolder-mount-preview")],Gl.prototype,"vfolderMountPreview",void 0),s([x("#launch-button")],Gl.prototype,"launchButton",void 0),s([x("#prev-button")],Gl.prototype,"prevButton",void 0),s([x("#next-button")],Gl.prototype,"nextButton",void 0),s([x("#OpenMPswitch")],Gl.prototype,"openMPSwitch",void 0),s([x("#cpu-resource")],Gl.prototype,"cpuResourceSlider",void 0),s([x("#gpu-resource")],Gl.prototype,"npuResourceSlider",void 0),s([x("#mem-resource")],Gl.prototype,"memoryResourceSlider",void 0),s([x("#shmem-resource")],Gl.prototype,"sharedMemoryResourceSlider",void 0),s([x("#session-resource")],Gl.prototype,"sessionResourceSlider",void 0),s([x("#cluster-size")],Gl.prototype,"clusterSizeSlider",void 0),s([x("#launch-button-msg")],Gl.prototype,"launchButtonMessage",void 0),s([x("#new-session-dialog")],Gl.prototype,"newSessionDialog",void 0),s([x("#modify-env-dialog")],Gl.prototype,"modifyEnvDialog",void 0),s([x("#modify-env-container")],Gl.prototype,"modifyEnvContainer",void 0),s([x("#modify-preopen-ports-dialog")],Gl.prototype,"modifyPreOpenPortDialog",void 0),s([x("#modify-preopen-ports-container")],Gl.prototype,"modifyPreOpenPortContainer",void 0),s([x("#launch-confirmation-dialog")],Gl.prototype,"launchConfirmationDialog",void 0),s([x("#help-description")],Gl.prototype,"helpDescriptionDialog",void 0),s([x("#command-editor")],Gl.prototype,"commandEditor",void 0),s([x("#session-name")],Gl.prototype,"sessionName",void 0),s([x("backend-ai-react-batch-session-scheduled-time-setting")],Gl.prototype,"batchSessionDatePicker",void 0),Gl=s([w("backend-ai-session-launcher")],Gl);
