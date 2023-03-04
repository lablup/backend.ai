import{D as __extends,z as __assign,M as MDCFoundation,_ as __decorate,e,al as observer,c as i,an as o,aj as BaseElement,J as FormElement,y,u as o$1,i as i$1,a as e$1,r as t,G as e$2,q as ariaProperty,H as e$3,R as RippleHandlers,ak as addHasRemoveClass,w as l,B as BackendAIPage,d as BackendAiStyles,I as IronFlex,b as IronFlexAlignment,f as IronPositioning,t as translate,g as get,A,h as BackendAIPainKiller,o as o$2}from"./backend-ai-webui-efd2500f.js";import"./mwc-tab-bar-553aafc2.js";import"./label-06f60db1.js";import"./select-ea0f7a77.js";import"./tab-group-b2aae4b1.js";import"./textfield-8bcb1235.js";import"./chart-js-74e01f0a.js";import"./backend-ai-list-status-9346ef68.js";import"./lablup-grid-sort-filter-column-84561833.js";import{a9 as ColumnBaseMixin,aa as updateColumnOrders,l as Debouncer,ab as animationFrame,F as FlattenedNodesObserver,ac as microTask,P as PolymerElement,r as registerStyles,E as ElementMixin,T as ThemableMixin,h as html}from"./vaadin-grid-af1e810c.js";import"./vaadin-grid-sort-column-46341c17.js";import"./vaadin-grid-filter-column-2949b887.js";import"./vaadin-grid-selection-column-5177358f.js";import"./vaadin-item-styles-0bc384b2.js";import"./vaadin-item-42ec2f48.js";import"./lablup-activity-panel-b5a6a642.js";import"./input-behavior-1a3ba72d.js";import"./radio-behavior-98d80f7f.js";
/**
 * @license
 * Copyright 2017 Google Inc.
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
 */var cssClasses$1={ROOT:"mdc-form-field"},strings$1={LABEL_SELECTOR:".mdc-form-field > label"},MDCFormFieldFoundation=function(e){function t(i){var o=e.call(this,__assign(__assign({},t.defaultAdapter),i))||this;return o.click=function(){o.handleClick()},o}return __extends(t,e),Object.defineProperty(t,"cssClasses",{get:function(){return cssClasses$1},enumerable:!1,configurable:!0}),Object.defineProperty(t,"strings",{get:function(){return strings$1},enumerable:!1,configurable:!0}),Object.defineProperty(t,"defaultAdapter",{get:function(){return{activateInputRipple:function(){},deactivateInputRipple:function(){},deregisterInteractionHandler:function(){},registerInteractionHandler:function(){}}},enumerable:!1,configurable:!0}),t.prototype.init=function(){this.adapter.registerInteractionHandler("click",this.click)},t.prototype.destroy=function(){this.adapter.deregisterInteractionHandler("click",this.click)},t.prototype.handleClick=function(){var e=this;this.adapter.activateInputRipple(),requestAnimationFrame((function(){e.adapter.deactivateInputRipple()}))},t}(MDCFoundation),MDCFormFieldFoundation$1=MDCFormFieldFoundation;
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
class FormfieldBase extends BaseElement{constructor(){super(...arguments),this.alignEnd=!1,this.spaceBetween=!1,this.nowrap=!1,this.label="",this.mdcFoundationClass=MDCFormFieldFoundation$1}createAdapter(){return{registerInteractionHandler:(e,t)=>{this.labelEl.addEventListener(e,t)},deregisterInteractionHandler:(e,t)=>{this.labelEl.removeEventListener(e,t)},activateInputRipple:async()=>{const e=this.input;if(e instanceof FormElement){const t=await e.ripple;t&&t.startPress()}},deactivateInputRipple:async()=>{const e=this.input;if(e instanceof FormElement){const t=await e.ripple;t&&t.endPress()}}}}get input(){var e,t;return null!==(t=null===(e=this.slottedInputs)||void 0===e?void 0:e[0])&&void 0!==t?t:null}render(){const e={"mdc-form-field--align-end":this.alignEnd,"mdc-form-field--space-between":this.spaceBetween,"mdc-form-field--nowrap":this.nowrap};return y`
      <div class="mdc-form-field ${o$1(e)}">
        <slot></slot>
        <label class="mdc-label"
               @click="${this._labelClick}">${this.label}</label>
      </div>`}click(){this._labelClick()}_labelClick(){const e=this.input;e&&(e.focus(),e.click())}}__decorate([e({type:Boolean})],FormfieldBase.prototype,"alignEnd",void 0),__decorate([e({type:Boolean})],FormfieldBase.prototype,"spaceBetween",void 0),__decorate([e({type:Boolean})],FormfieldBase.prototype,"nowrap",void 0),__decorate([e({type:String}),observer((async function(e){var t;null===(t=this.input)||void 0===t||t.setAttribute("aria-label",e)}))],FormfieldBase.prototype,"label",void 0),__decorate([i(".mdc-form-field")],FormfieldBase.prototype,"mdcRoot",void 0),__decorate([o("",!0,"*")],FormfieldBase.prototype,"slottedInputs",void 0),__decorate([i("label")],FormfieldBase.prototype,"labelEl",void 0);
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-LIcense-Identifier: Apache-2.0
 */
const styles$1=i$1`.mdc-form-field{-moz-osx-font-smoothing:grayscale;-webkit-font-smoothing:antialiased;font-family:Roboto, sans-serif;font-family:var(--mdc-typography-body2-font-family, var(--mdc-typography-font-family, Roboto, sans-serif));font-size:0.875rem;font-size:var(--mdc-typography-body2-font-size, 0.875rem);line-height:1.25rem;line-height:var(--mdc-typography-body2-line-height, 1.25rem);font-weight:400;font-weight:var(--mdc-typography-body2-font-weight, 400);letter-spacing:0.0178571429em;letter-spacing:var(--mdc-typography-body2-letter-spacing, 0.0178571429em);text-decoration:inherit;text-decoration:var(--mdc-typography-body2-text-decoration, inherit);text-transform:inherit;text-transform:var(--mdc-typography-body2-text-transform, inherit);color:rgba(0, 0, 0, 0.87);color:var(--mdc-theme-text-primary-on-background, rgba(0, 0, 0, 0.87));display:inline-flex;align-items:center;vertical-align:middle}.mdc-form-field>label{margin-left:0;margin-right:auto;padding-left:4px;padding-right:0;order:0}[dir=rtl] .mdc-form-field>label,.mdc-form-field>label[dir=rtl]{margin-left:auto;margin-right:0}[dir=rtl] .mdc-form-field>label,.mdc-form-field>label[dir=rtl]{padding-left:0;padding-right:4px}.mdc-form-field--nowrap>label{text-overflow:ellipsis;overflow:hidden;white-space:nowrap}.mdc-form-field--align-end>label{margin-left:auto;margin-right:0;padding-left:0;padding-right:4px;order:-1}[dir=rtl] .mdc-form-field--align-end>label,.mdc-form-field--align-end>label[dir=rtl]{margin-left:0;margin-right:auto}[dir=rtl] .mdc-form-field--align-end>label,.mdc-form-field--align-end>label[dir=rtl]{padding-left:4px;padding-right:0}.mdc-form-field--space-between{justify-content:space-between}.mdc-form-field--space-between>label{margin:0}[dir=rtl] .mdc-form-field--space-between>label,.mdc-form-field--space-between>label[dir=rtl]{margin:0}:host{display:inline-flex}.mdc-form-field{width:100%}::slotted(*){-moz-osx-font-smoothing:grayscale;-webkit-font-smoothing:antialiased;font-family:Roboto, sans-serif;font-family:var(--mdc-typography-body2-font-family, var(--mdc-typography-font-family, Roboto, sans-serif));font-size:0.875rem;font-size:var(--mdc-typography-body2-font-size, 0.875rem);line-height:1.25rem;line-height:var(--mdc-typography-body2-line-height, 1.25rem);font-weight:400;font-weight:var(--mdc-typography-body2-font-weight, 400);letter-spacing:0.0178571429em;letter-spacing:var(--mdc-typography-body2-letter-spacing, 0.0178571429em);text-decoration:inherit;text-decoration:var(--mdc-typography-body2-text-decoration, inherit);text-transform:inherit;text-transform:var(--mdc-typography-body2-text-transform, inherit);color:rgba(0, 0, 0, 0.87);color:var(--mdc-theme-text-primary-on-background, rgba(0, 0, 0, 0.87))}::slotted(mwc-switch){margin-right:10px}[dir=rtl] ::slotted(mwc-switch),::slotted(mwc-switch[dir=rtl]){margin-left:10px}`
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */;let Formfield=class extends FormfieldBase{};Formfield.styles=[styles$1],Formfield=__decorate([e$1("mwc-formfield")],Formfield);
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
 */var strings={NATIVE_CONTROL_SELECTOR:".mdc-radio__native-control"},cssClasses={DISABLED:"mdc-radio--disabled",ROOT:"mdc-radio"},MDCRadioFoundation=function(e){function t(i){return e.call(this,__assign(__assign({},t.defaultAdapter),i))||this}return __extends(t,e),Object.defineProperty(t,"cssClasses",{get:function(){return cssClasses},enumerable:!1,configurable:!0}),Object.defineProperty(t,"strings",{get:function(){return strings},enumerable:!1,configurable:!0}),Object.defineProperty(t,"defaultAdapter",{get:function(){return{addClass:function(){},removeClass:function(){},setNativeControlDisabled:function(){}}},enumerable:!1,configurable:!0}),t.prototype.setDisabled=function(e){var i=t.cssClasses.DISABLED;this.adapter.setNativeControlDisabled(e),e?this.adapter.addClass(i):this.adapter.removeClass(i)},t}(MDCFoundation),MDCRadioFoundation$1=MDCRadioFoundation;
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
class RadioBase extends FormElement{constructor(){super(...arguments),this._checked=!1,this.useStateLayerCustomProperties=!1,this.global=!1,this.disabled=!1,this.value="on",this.name="",this.reducedTouchTarget=!1,this.mdcFoundationClass=MDCRadioFoundation$1,this.formElementTabIndex=0,this.focused=!1,this.shouldRenderRipple=!1,this.rippleElement=null,this.rippleHandlers=new RippleHandlers((()=>(this.shouldRenderRipple=!0,this.ripple.then((e=>{this.rippleElement=e})),this.ripple)))}get checked(){return this._checked}set checked(e){var t,i;const o=this._checked;e!==o&&(this._checked=e,this.formElement&&(this.formElement.checked=e),null===(t=this._selectionController)||void 0===t||t.update(this),!1===e&&(null===(i=this.formElement)||void 0===i||i.blur()),this.requestUpdate("checked",o),this.dispatchEvent(new Event("checked",{bubbles:!0,composed:!0})))}_handleUpdatedValue(e){this.formElement.value=e}renderRipple(){return this.shouldRenderRipple?y`<mwc-ripple unbounded accent
        .internalUseStateLayerCustomProperties="${this.useStateLayerCustomProperties}"
        .disabled="${this.disabled}"></mwc-ripple>`:""}get isRippleActive(){var e;return(null===(e=this.rippleElement)||void 0===e?void 0:e.isActive)||!1}connectedCallback(){super.connectedCallback(),this._selectionController=SingleSelectionController.getController(this),this._selectionController.register(this),this._selectionController.update(this)}disconnectedCallback(){this._selectionController.unregister(this),this._selectionController=void 0}focus(){this.formElement.focus()}createAdapter(){return Object.assign(Object.assign({},addHasRemoveClass(this.mdcRoot)),{setNativeControlDisabled:e=>{this.formElement.disabled=e}})}handleFocus(){this.focused=!0,this.handleRippleFocus()}handleClick(){this.formElement.focus()}handleBlur(){this.focused=!1,this.formElement.blur(),this.rippleHandlers.endFocus()}setFormData(e){this.name&&this.checked&&e.append(this.name,this.value)}render(){const e={"mdc-radio--touch":!this.reducedTouchTarget,"mdc-ripple-upgraded--background-focused":this.focused,"mdc-radio--disabled":this.disabled};return y`
      <div class="mdc-radio ${o$1(e)}">
        <input
          tabindex="${this.formElementTabIndex}"
          class="mdc-radio__native-control"
          type="radio"
          name="${this.name}"
          aria-label="${l(this.ariaLabel)}"
          aria-labelledby="${l(this.ariaLabelledBy)}"
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
      </div>`}handleRippleMouseDown(e){const t=()=>{window.removeEventListener("mouseup",t),this.handleRippleDeactivate()};window.addEventListener("mouseup",t),this.rippleHandlers.startPress(e)}handleRippleTouchStart(e){this.rippleHandlers.startPress(e)}handleRippleDeactivate(){this.rippleHandlers.endPress()}handleRippleMouseEnter(){this.rippleHandlers.startHover()}handleRippleMouseLeave(){this.rippleHandlers.endHover()}handleRippleFocus(){this.rippleHandlers.startFocus()}changeHandler(){this.checked=this.formElement.checked}}__decorate([i(".mdc-radio")],RadioBase.prototype,"mdcRoot",void 0),__decorate([i("input")],RadioBase.prototype,"formElement",void 0),__decorate([t()],RadioBase.prototype,"useStateLayerCustomProperties",void 0),__decorate([e({type:Boolean})],RadioBase.prototype,"global",void 0),__decorate([e({type:Boolean,reflect:!0})],RadioBase.prototype,"checked",null),__decorate([e({type:Boolean}),observer((function(e){this.mdcFoundation.setDisabled(e)}))],RadioBase.prototype,"disabled",void 0),__decorate([e({type:String}),observer((function(e){this._handleUpdatedValue(e)}))],RadioBase.prototype,"value",void 0),__decorate([e({type:String})],RadioBase.prototype,"name",void 0),__decorate([e({type:Boolean})],RadioBase.prototype,"reducedTouchTarget",void 0),__decorate([e({type:Number})],RadioBase.prototype,"formElementTabIndex",void 0),__decorate([t()],RadioBase.prototype,"focused",void 0),__decorate([t()],RadioBase.prototype,"shouldRenderRipple",void 0),__decorate([e$2("mwc-ripple")],RadioBase.prototype,"ripple",void 0),__decorate([ariaProperty,e({attribute:"aria-label"})],RadioBase.prototype,"ariaLabel",void 0),__decorate([ariaProperty,e({attribute:"aria-labelledby"})],RadioBase.prototype,"ariaLabelledBy",void 0),__decorate([e$3({passive:!0})],RadioBase.prototype,"handleRippleTouchStart",null);
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-LIcense-Identifier: Apache-2.0
 */
const styles=i$1`.mdc-touch-target-wrapper{display:inline}.mdc-radio{padding:calc((40px - 20px) / 2)}.mdc-radio .mdc-radio__native-control:enabled:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle{border-color:rgba(0, 0, 0, 0.54)}.mdc-radio .mdc-radio__native-control:enabled:checked+.mdc-radio__background .mdc-radio__outer-circle{border-color:#018786;border-color:var(--mdc-theme-secondary, #018786)}.mdc-radio .mdc-radio__native-control:enabled+.mdc-radio__background .mdc-radio__inner-circle{border-color:#018786;border-color:var(--mdc-theme-secondary, #018786)}.mdc-radio [aria-disabled=true] .mdc-radio__native-control:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio .mdc-radio__native-control:disabled:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle{border-color:rgba(0, 0, 0, 0.38)}.mdc-radio [aria-disabled=true] .mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio .mdc-radio__native-control:disabled:checked+.mdc-radio__background .mdc-radio__outer-circle{border-color:rgba(0, 0, 0, 0.38)}.mdc-radio [aria-disabled=true] .mdc-radio__native-control+.mdc-radio__background .mdc-radio__inner-circle,.mdc-radio .mdc-radio__native-control:disabled+.mdc-radio__background .mdc-radio__inner-circle{border-color:rgba(0, 0, 0, 0.38)}.mdc-radio .mdc-radio__background::before{background-color:#018786;background-color:var(--mdc-theme-secondary, #018786)}.mdc-radio .mdc-radio__background::before{top:calc(-1 * (40px - 20px) / 2);left:calc(-1 * (40px - 20px) / 2);width:40px;height:40px}.mdc-radio .mdc-radio__native-control{top:calc((40px - 40px) / 2);right:calc((40px - 40px) / 2);left:calc((40px - 40px) / 2);width:40px;height:40px}@media screen and (forced-colors: active),(-ms-high-contrast: active){.mdc-radio.mdc-radio--disabled [aria-disabled=true] .mdc-radio__native-control:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio.mdc-radio--disabled .mdc-radio__native-control:disabled:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle{border-color:GrayText}.mdc-radio.mdc-radio--disabled [aria-disabled=true] .mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio.mdc-radio--disabled .mdc-radio__native-control:disabled:checked+.mdc-radio__background .mdc-radio__outer-circle{border-color:GrayText}.mdc-radio.mdc-radio--disabled [aria-disabled=true] .mdc-radio__native-control+.mdc-radio__background .mdc-radio__inner-circle,.mdc-radio.mdc-radio--disabled .mdc-radio__native-control:disabled+.mdc-radio__background .mdc-radio__inner-circle{border-color:GrayText}}.mdc-radio{display:inline-block;position:relative;flex:0 0 auto;box-sizing:content-box;width:20px;height:20px;cursor:pointer;will-change:opacity,transform,border-color,color}.mdc-radio__background{display:inline-block;position:relative;box-sizing:border-box;width:20px;height:20px}.mdc-radio__background::before{position:absolute;transform:scale(0, 0);border-radius:50%;opacity:0;pointer-events:none;content:"";transition:opacity 120ms 0ms cubic-bezier(0.4, 0, 0.6, 1),transform 120ms 0ms cubic-bezier(0.4, 0, 0.6, 1)}.mdc-radio__outer-circle{position:absolute;top:0;left:0;box-sizing:border-box;width:100%;height:100%;border-width:2px;border-style:solid;border-radius:50%;transition:border-color 120ms 0ms cubic-bezier(0.4, 0, 0.6, 1)}.mdc-radio__inner-circle{position:absolute;top:0;left:0;box-sizing:border-box;width:100%;height:100%;transform:scale(0, 0);border-width:10px;border-style:solid;border-radius:50%;transition:transform 120ms 0ms cubic-bezier(0.4, 0, 0.6, 1),border-color 120ms 0ms cubic-bezier(0.4, 0, 0.6, 1)}.mdc-radio__native-control{position:absolute;margin:0;padding:0;opacity:0;cursor:inherit;z-index:1}.mdc-radio--touch{margin-top:4px;margin-bottom:4px;margin-right:4px;margin-left:4px}.mdc-radio--touch .mdc-radio__native-control{top:calc((40px - 48px) / 2);right:calc((40px - 48px) / 2);left:calc((40px - 48px) / 2);width:48px;height:48px}.mdc-radio.mdc-ripple-upgraded--background-focused .mdc-radio__focus-ring,.mdc-radio:not(.mdc-ripple-upgraded):focus .mdc-radio__focus-ring{pointer-events:none;border:2px solid transparent;border-radius:6px;box-sizing:content-box;position:absolute;top:50%;left:50%;transform:translate(-50%, -50%);height:100%;width:100%}@media screen and (forced-colors: active){.mdc-radio.mdc-ripple-upgraded--background-focused .mdc-radio__focus-ring,.mdc-radio:not(.mdc-ripple-upgraded):focus .mdc-radio__focus-ring{border-color:CanvasText}}.mdc-radio.mdc-ripple-upgraded--background-focused .mdc-radio__focus-ring::after,.mdc-radio:not(.mdc-ripple-upgraded):focus .mdc-radio__focus-ring::after{content:"";border:2px solid transparent;border-radius:8px;display:block;position:absolute;top:50%;left:50%;transform:translate(-50%, -50%);height:calc(100% + 4px);width:calc(100% + 4px)}@media screen and (forced-colors: active){.mdc-radio.mdc-ripple-upgraded--background-focused .mdc-radio__focus-ring::after,.mdc-radio:not(.mdc-ripple-upgraded):focus .mdc-radio__focus-ring::after{border-color:CanvasText}}.mdc-radio__native-control:checked+.mdc-radio__background,.mdc-radio__native-control:disabled+.mdc-radio__background{transition:opacity 120ms 0ms cubic-bezier(0, 0, 0.2, 1),transform 120ms 0ms cubic-bezier(0, 0, 0.2, 1)}.mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio__native-control:disabled+.mdc-radio__background .mdc-radio__outer-circle{transition:border-color 120ms 0ms cubic-bezier(0, 0, 0.2, 1)}.mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__inner-circle,.mdc-radio__native-control:disabled+.mdc-radio__background .mdc-radio__inner-circle{transition:transform 120ms 0ms cubic-bezier(0, 0, 0.2, 1),border-color 120ms 0ms cubic-bezier(0, 0, 0.2, 1)}.mdc-radio--disabled{cursor:default;pointer-events:none}.mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__inner-circle{transform:scale(0.5);transition:transform 120ms 0ms cubic-bezier(0, 0, 0.2, 1),border-color 120ms 0ms cubic-bezier(0, 0, 0.2, 1)}.mdc-radio__native-control:disabled+.mdc-radio__background,[aria-disabled=true] .mdc-radio__native-control+.mdc-radio__background{cursor:default}.mdc-radio__native-control:focus+.mdc-radio__background::before{transform:scale(1);opacity:.12;transition:opacity 120ms 0ms cubic-bezier(0, 0, 0.2, 1),transform 120ms 0ms cubic-bezier(0, 0, 0.2, 1)}:host{display:inline-block;outline:none}.mdc-radio{vertical-align:bottom}.mdc-radio .mdc-radio__native-control:enabled:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle{border-color:var(--mdc-radio-unchecked-color, rgba(0, 0, 0, 0.54))}.mdc-radio [aria-disabled=true] .mdc-radio__native-control:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio .mdc-radio__native-control:disabled:not(:checked)+.mdc-radio__background .mdc-radio__outer-circle{border-color:var(--mdc-radio-disabled-color, rgba(0, 0, 0, 0.38))}.mdc-radio [aria-disabled=true] .mdc-radio__native-control:checked+.mdc-radio__background .mdc-radio__outer-circle,.mdc-radio .mdc-radio__native-control:disabled:checked+.mdc-radio__background .mdc-radio__outer-circle{border-color:var(--mdc-radio-disabled-color, rgba(0, 0, 0, 0.38))}.mdc-radio [aria-disabled=true] .mdc-radio__native-control+.mdc-radio__background .mdc-radio__inner-circle,.mdc-radio .mdc-radio__native-control:disabled+.mdc-radio__background .mdc-radio__inner-circle{border-color:var(--mdc-radio-disabled-color, rgba(0, 0, 0, 0.38))}`
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */;let Radio=class extends RadioBase{};Radio.styles=[styles],Radio=__decorate([e$1("mwc-radio")],Radio);
/**
 * @license
 * Copyright (c) 2016 - 2022 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
class GridColumnGroup extends(ColumnBaseMixin(PolymerElement)){static get is(){return"vaadin-grid-column-group"}static get properties(){return{_childColumns:{value(){return this._getChildColumns(this)}},flexGrow:{type:Number,readOnly:!0},width:{type:String,readOnly:!0},_visibleChildColumns:Array,_colSpan:Number,_rootColumns:Array}}static get observers(){return["_groupFrozenChanged(frozen, _rootColumns)","_groupFrozenToEndChanged(frozenToEnd, _rootColumns)","_groupHiddenChanged(hidden)","_colSpanChanged(_colSpan, _headerCell, _footerCell)","_groupOrderChanged(_order, _rootColumns)","_groupReorderStatusChanged(_reorderStatus, _rootColumns)","_groupResizableChanged(resizable, _rootColumns)"]}connectedCallback(){super.connectedCallback(),this._addNodeObserver(),this._updateFlexAndWidth()}disconnectedCallback(){super.disconnectedCallback(),this._observer&&this._observer.disconnect()}_columnPropChanged(e,t){"hidden"===e&&(this._preventHiddenSynchronization=!0,this._updateVisibleChildColumns(this._childColumns),this._preventHiddenSynchronization=!1),/flexGrow|width|hidden|_childColumns/.test(e)&&this._updateFlexAndWidth(),"frozen"===e&&(this.frozen=this.frozen||t),"lastFrozen"===e&&(this._lastFrozen=this._lastFrozen||t),"frozenToEnd"===e&&(this.frozenToEnd=this.frozenToEnd||t),"firstFrozenToEnd"===e&&(this._firstFrozenToEnd=this._firstFrozenToEnd||t)}_groupOrderChanged(e,t){if(t){const i=t.slice(0);if(!e)return void i.forEach((e=>{e._order=0}));const o=10**(/(0+)$/.exec(e).pop().length-(1+~~(Math.log(t.length)/Math.LN10)));i[0]&&i[0]._order&&i.sort(((e,t)=>e._order-t._order)),updateColumnOrders(i,o,e)}}_groupReorderStatusChanged(e,t){void 0!==e&&void 0!==t&&t.forEach((t=>{t._reorderStatus=e}))}_groupResizableChanged(e,t){void 0!==e&&void 0!==t&&t.forEach((t=>{t.resizable=e}))}_updateVisibleChildColumns(e){this._visibleChildColumns=Array.prototype.filter.call(e,(e=>!e.hidden)),this._colSpan=this._visibleChildColumns.length,this._updateAutoHidden()}_updateFlexAndWidth(){if(this._visibleChildColumns){if(this._visibleChildColumns.length>0){const e=this._visibleChildColumns.reduce(((e,t)=>e+=` + ${(t.width||"0px").replace("calc","")}`),"").substring(3);this._setWidth(`calc(${e})`)}else this._setWidth("0px");this._setFlexGrow(Array.prototype.reduce.call(this._visibleChildColumns,((e,t)=>e+t.flexGrow),0))}}__scheduleAutoFreezeWarning(e,t){if(this._grid){const i=t.replace(/([A-Z])/g,"-$1").toLowerCase(),o=e[0][t]||e[0].hasAttribute(i);e.every((e=>(e[t]||e.hasAttribute(i))===o))||(this._grid.__autoFreezeWarningDebouncer=Debouncer.debounce(this._grid.__autoFreezeWarningDebouncer,animationFrame,(()=>{console.warn(`WARNING: Joining ${t} and non-${t} Grid columns inside the same column group! This will automatically freeze all the joined columns to avoid rendering issues. If this was intentional, consider marking each joined column explicitly as ${t}. Otherwise, exclude the ${t} columns from the joined group.`)})))}}_groupFrozenChanged(e,t){void 0!==t&&void 0!==e&&!1!==e&&(this.__scheduleAutoFreezeWarning(t,"frozen"),Array.from(t).forEach((t=>{t.frozen=e})))}_groupFrozenToEndChanged(e,t){void 0!==t&&void 0!==e&&!1!==e&&(this.__scheduleAutoFreezeWarning(t,"frozenToEnd"),Array.from(t).forEach((t=>{t.frozenToEnd=e})))}_groupHiddenChanged(e){(e||this.__groupHiddenInitialized)&&this._synchronizeHidden(),this.__groupHiddenInitialized=!0}_updateAutoHidden(){const e=this._autoHidden;this._autoHidden=0===(this._visibleChildColumns||[]).length,(e||this._autoHidden)&&(this.hidden=this._autoHidden)}_synchronizeHidden(){this._childColumns&&!this._preventHiddenSynchronization&&this._childColumns.forEach((e=>{e.hidden=this.hidden}))}_colSpanChanged(e,t,i){t&&(t.setAttribute("colspan",e),this._grid&&this._grid._a11yUpdateCellColspan(t,e)),i&&(i.setAttribute("colspan",e),this._grid&&this._grid._a11yUpdateCellColspan(i,e))}_getChildColumns(e){return FlattenedNodesObserver.getFlattenedNodes(e).filter(this._isColumnElement)}_addNodeObserver(){this._observer=new FlattenedNodesObserver(this,(e=>{(e.addedNodes.filter(this._isColumnElement).length>0||e.removedNodes.filter(this._isColumnElement).length>0)&&(this._preventHiddenSynchronization=!0,this._rootColumns=this._getChildColumns(this),this._childColumns=this._rootColumns,this._updateVisibleChildColumns(this._childColumns),this._preventHiddenSynchronization=!1,microTask.run((()=>{this._grid&&this._grid._updateColumnTree&&this._grid._updateColumnTree()})))})),this._observer.flush()}_isColumnElement(e){return e.nodeType===Node.ELEMENT_NODE&&/\bcolumn\b/.test(e.localName)}}customElements.define(GridColumnGroup.is,GridColumnGroup),registerStyles("vaadin-progress-bar",i$1`
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
 * Copyright (c) 2017 - 2022 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const ProgressMixin=e=>class extends e{static get properties(){return{value:{type:Number,observer:"_valueChanged"},min:{type:Number,value:0,observer:"_minChanged"},max:{type:Number,value:1,observer:"_maxChanged"},indeterminate:{type:Boolean,value:!1,reflectToAttribute:!0}}}static get observers(){return["_normalizedValueChanged(value, min, max)"]}ready(){super.ready(),this.setAttribute("role","progressbar")}_normalizedValueChanged(e,t,i){const o=this._normalizeValue(e,t,i);this.style.setProperty("--vaadin-progress-value",o)}_valueChanged(e){this.setAttribute("aria-valuenow",e)}_minChanged(e){this.setAttribute("aria-valuemin",e)}_maxChanged(e){this.setAttribute("aria-valuemax",e)}_normalizeValue(e,t,i){let o;return e||0===e?t>=i?o=1:(o=(e-t)/(i-t),o=Math.min(Math.max(o,0),1)):o=0,o}}
/**
 * @license
 * Copyright (c) 2017 - 2022 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;class ProgressBar extends(ElementMixin(ThemableMixin(ProgressMixin(PolymerElement)))){static get template(){return html`
      <style>
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

        /* RTL specific styles */

        :host([dir='rtl']) [part='value'] {
          transform-origin: 100% 50%;
        }
      </style>

      <div part="bar">
        <div part="value"></div>
      </div>
    `}static get is(){return"vaadin-progress-bar"}}customElements.define(ProgressBar.is,ProgressBar),
/**
 * @license
 * Copyright (c) 2017 - 2022 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
console.warn('WARNING: Since Vaadin 23.2, "@vaadin/vaadin-progress-bar" is deprecated. Use "@vaadin/progress-bar" instead.'),function(e){"object"==typeof exports&&"undefined"!=typeof module?module.exports=e():"function"==typeof define&&define.amd?define([],e):("undefined"!=typeof window?window:"undefined"!=typeof global?global:"undefined"!=typeof self?self:this).tus=e()}((function(){var define;return function e(t,i,o){function r(n,l){if(!i[n]){if(!t[n]){var s="function"==typeof require&&require;if(!l&&s)return s(n,!0);if(a)return a(n,!0);var d=new Error("Cannot find module '"+n+"'");throw d.code="MODULE_NOT_FOUND",d}var c=i[n]={exports:{}};t[n][0].call(c.exports,(function(e){return r(t[n][1][e]||e)}),c,c.exports,e,t,i,o)}return i[n].exports}for(var a="function"==typeof require&&require,n=0;n<o.length;n++)r(o[n]);return r}({1:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=void 0;var o=l(e("./isReactNative")),r=l(e("./uriToBlob")),a=l(e("./isCordova")),n=l(e("./readAsByteArray"));function l(e){return e&&e.__esModule?e:{default:e}}function s(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}function d(e,t){for(var i=0;i<t.length;i++){var o=t[i];o.enumerable=o.enumerable||!1,o.configurable=!0,"value"in o&&(o.writable=!0),Object.defineProperty(e,o.key,o)}}function c(e,t,i){return t&&d(e.prototype,t),i&&d(e,i),e}var u=function(){function e(t){s(this,e),this._file=t,this.size=t.size}return c(e,[{key:"slice",value:function(e,t){if((0,a.default)())return(0,n.default)(this._file.slice(e,t));var i=this._file.slice(e,t);return Promise.resolve({value:i})}},{key:"close",value:function(){}}]),e}(),p=function(){function e(t,i){s(this,e),this._chunkSize=i,this._buffer=void 0,this._bufferOffset=0,this._reader=t,this._done=!1}return c(e,[{key:"slice",value:function(e,t){return e<this._bufferOffset?Promise.reject(new Error("Requested data is before the reader's current offset")):this._readUntilEnoughDataOrDone(e,t)}},{key:"_readUntilEnoughDataOrDone",value:function(e,t){var i=this,o=t<=this._bufferOffset+h(this._buffer);if(this._done||o){var r=this._getDataFromBuffer(e,t),a=null==r&&this._done;return Promise.resolve({value:r,done:a})}return this._reader.read().then((function(o){var r=o.value;return o.done?i._done=!0:void 0===i._buffer?i._buffer=r:i._buffer=function(e,t){if(e.concat)return e.concat(t);if(e instanceof Blob)return new Blob([e,t],{type:e.type});if(e.set){var i=new e.constructor(e.length+t.length);return i.set(e),i.set(t,e.length),i}throw new Error("Unknown data type")}(i._buffer,r),i._readUntilEnoughDataOrDone(e,t)}))}},{key:"_getDataFromBuffer",value:function(e,t){e>this._bufferOffset&&(this._buffer=this._buffer.slice(e-this._bufferOffset),this._bufferOffset=e);var i=0===h(this._buffer);return this._done&&i?null:this._buffer.slice(0,t-e)}},{key:"close",value:function(){this._reader.cancel&&this._reader.cancel()}}]),e}();function h(e){return void 0===e?0:void 0!==e.size?e.size:e.length}var m=function(){function e(){s(this,e)}return c(e,[{key:"openFile",value:function(e,t){return(0,o.default)()&&e&&void 0!==e.uri?(0,r.default)(e.uri).then((function(e){return new u(e)})).catch((function(e){throw new Error("tus: cannot fetch `file.uri` as Blob, make sure the uri is correct and accessible. "+e)})):"function"==typeof e.slice&&void 0!==e.size?Promise.resolve(new u(e)):"function"==typeof e.read?(t=+t,isFinite(t)?Promise.resolve(new p(e,t)):Promise.reject(new Error("cannot create source for stream without a finite value for the `chunkSize` option"))):Promise.reject(new Error("source object may only be an instance of File, Blob, or Reader in this environment"))}}]),e}();i.default=m},{"./isCordova":5,"./isReactNative":6,"./readAsByteArray":7,"./uriToBlob":8}],2:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=function(e,t){return(0,r.default)()?Promise.resolve(function(e,t){var i=e.exif?function(e){var t=0;if(0===e.length)return t;for(var i=0;i<e.length;i++){t=(t<<5)-t+e.charCodeAt(i),t&=t}return t}(JSON.stringify(e.exif)):"noexif";return["tus-rn",e.name||"noname",e.size||"nosize",i,t.endpoint].join("/")}(e,t)):Promise.resolve(["tus-br",e.name,e.type,e.size,e.lastModified,t.endpoint].join("-"))};var o,r=(o=e("./isReactNative"))&&o.__esModule?o:{default:o}},{"./isReactNative":6}],3:[function(e,t,i){function o(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}function r(e,t){for(var i=0;i<t.length;i++){var o=t[i];o.enumerable=o.enumerable||!1,o.configurable=!0,"value"in o&&(o.writable=!0),Object.defineProperty(e,o.key,o)}}function a(e,t,i){return t&&r(e.prototype,t),i&&r(e,i),e}Object.defineProperty(i,"__esModule",{value:!0}),i.default=void 0;var n=function(){function e(){o(this,e)}return a(e,[{key:"createRequest",value:function(e,t){return new l(e,t)}},{key:"getName",value:function(){return"XHRHttpStack"}}]),e}();i.default=n;var l=function(){function e(t,i){o(this,e),this._xhr=new XMLHttpRequest,this._xhr.open(t,i,!0),this._method=t,this._url=i,this._headers={}}return a(e,[{key:"getMethod",value:function(){return this._method}},{key:"getURL",value:function(){return this._url}},{key:"setHeader",value:function(e,t){this._xhr.setRequestHeader(e,t),this._headers[e]=t}},{key:"getHeader",value:function(e){return this._headers[e]}},{key:"setProgressHandler",value:function(e){"upload"in this._xhr&&(this._xhr.upload.onprogress=function(t){t.lengthComputable&&e(t.loaded)})}},{key:"send",value:function(e){var t=this,i=0<arguments.length&&void 0!==e?e:null;return new Promise((function(e,o){t._xhr.onload=function(){e(new s(t._xhr))},t._xhr.onerror=function(e){o(e)},t._xhr.send(i)}))}},{key:"abort",value:function(){return this._xhr.abort(),Promise.resolve()}},{key:"getUnderlyingObject",value:function(){return this._xhr}}]),e}(),s=function(){function e(t){o(this,e),this._xhr=t}return a(e,[{key:"getStatus",value:function(){return this._xhr.status}},{key:"getHeader",value:function(e){return this._xhr.getResponseHeader(e)}},{key:"getBody",value:function(){return this._xhr.responseText}},{key:"getUnderlyingObject",value:function(){return this._xhr}}]),e}()},{}],4:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),Object.defineProperty(i,"enableDebugLog",{enumerable:!0,get:function(){return a.enableDebugLog}}),Object.defineProperty(i,"canStoreURLs",{enumerable:!0,get:function(){return n.canStoreURLs}}),i.isSupported=i.defaultOptions=i.Upload=void 0;var o=c(e("../upload")),r=c(e("../noopUrlStorage")),a=e("../logger"),n=e("./urlStorage"),l=c(e("./httpStack")),s=c(e("./fileReader")),d=c(e("./fingerprint"));function c(e){return e&&e.__esModule?e:{default:e}}function u(e){return(u="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e})(e)}function p(e,t){for(var i=0;i<t.length;i++){var o=t[i];o.enumerable=o.enumerable||!1,o.configurable=!0,"value"in o&&(o.writable=!0),Object.defineProperty(e,o.key,o)}}function h(e,t){return(h=Object.setPrototypeOf||function(e,t){return e.__proto__=t,e})(e,t)}function m(e){return(m=Object.setPrototypeOf?Object.getPrototypeOf:function(e){return e.__proto__||Object.getPrototypeOf(e)})(e)}function f(e,t){var i,o=Object.keys(e);return Object.getOwnPropertySymbols&&(i=Object.getOwnPropertySymbols(e),t&&(i=i.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),o.push.apply(o,i)),o}function g(e){for(var t=1;t<arguments.length;t++){var i=null!=arguments[t]?arguments[t]:{};t%2?f(Object(i),!0).forEach((function(t){b(e,t,i[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(i)):f(Object(i)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(i,t))}))}return e}function b(e,t,i){return t in e?Object.defineProperty(e,t,{value:i,enumerable:!0,configurable:!0,writable:!0}):e[t]=i,e}var v=g({},o.default.defaultOptions,{httpStack:new l.default,fileReader:new s.default,urlStorage:n.canStoreURLs?new n.WebStorageUrlStorage:new r.default,fingerprint:d.default});i.defaultOptions=v;var _=function(){!function(e,t){if("function"!=typeof t&&null!==t)throw new TypeError("Super expression must either be null or a function");e.prototype=Object.create(t&&t.prototype,{constructor:{value:e,writable:!0,configurable:!0}}),t&&h(e,t)}(r,o.default);var e,t,i=function(e){return function(){var t,i,o,r=m(e);return i=this,!(o=function(){if("undefined"!=typeof Reflect&&Reflect.construct&&!Reflect.construct.sham){if("function"==typeof Proxy)return 1;try{return Date.prototype.toString.call(Reflect.construct(Date,[],(function(){}))),1}catch(e){return}}}()?(t=m(this).constructor,Reflect.construct(r,arguments,t)):r.apply(this,arguments))||"object"!==u(o)&&"function"!=typeof o?function(e){if(void 0!==e)return e;throw new ReferenceError("this hasn't been initialised - super() hasn't been called")}(i):o}}(r);function r(){var e=0<arguments.length&&void 0!==arguments[0]?arguments[0]:null,t=1<arguments.length&&void 0!==arguments[1]?arguments[1]:{};return function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,r),t=g({},v,{},t),i.call(this,e,t)}return e=r,t=[{key:"terminate",value:function(e,t,i){return t=g({},v,{},t),o.default.terminate(e,t,i)}}],null&&p(e.prototype,null),t&&p(e,t),r}();i.Upload=_;var y=window,w=y.XMLHttpRequest,x=y.Blob,k=w&&x&&"function"==typeof x.prototype.slice;i.isSupported=k},{"../logger":11,"../noopUrlStorage":12,"../upload":13,"./fileReader":1,"./fingerprint":2,"./httpStack":3,"./urlStorage":9}],5:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=void 0,i.default=function(){return"undefined"!=typeof window&&(void 0!==window.PhoneGap||void 0!==window.Cordova||void 0!==window.cordova)}},{}],6:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=void 0,i.default=function(){return"undefined"!=typeof navigator&&"string"==typeof navigator.product&&"reactnative"===navigator.product.toLowerCase()}},{}],7:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=function(e){return new Promise((function(t,i){var o=new FileReader;o.onload=function(){var e=new Uint8Array(o.result);t({value:e})},o.onerror=function(e){i(e)},o.readAsArrayBuffer(e)}))}},{}],8:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=function(e){return new Promise((function(t,i){var o=new XMLHttpRequest;o.responseType="blob",o.onload=function(){var e=o.response;t(e)},o.onerror=function(e){i(e)},o.open("GET",e),o.send()}))}},{}],9:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.WebStorageUrlStorage=i.canStoreURLs=void 0;var o=!1;try{o="localStorage"in window;var r="tusSupport";localStorage.setItem(r,localStorage.getItem(r))}catch(e){if(e.code!==e.SECURITY_ERR&&e.code!==e.QUOTA_EXCEEDED_ERR)throw e;o=!1}i.canStoreURLs=o;var a=function(){function e(){!function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,e)}var t;return(t=[{key:"findAllUploads",value:function(){var e=this._findEntries("tus::");return Promise.resolve(e)}},{key:"findUploadsByFingerprint",value:function(e){var t=this._findEntries("tus::".concat(e,"::"));return Promise.resolve(t)}},{key:"removeUpload",value:function(e){return localStorage.removeItem(e),Promise.resolve()}},{key:"addUpload",value:function(e,t){var i=Math.round(1e12*Math.random()),o="tus::".concat(e,"::").concat(i);return localStorage.setItem(o,JSON.stringify(t)),Promise.resolve(o)}},{key:"_findEntries",value:function(e){for(var t=[],i=0;i<localStorage.length;i++){var o=localStorage.key(i);if(0===o.indexOf(e))try{var r=JSON.parse(localStorage.getItem(o));r.urlStorageKey=o,t.push(r)}catch(e){}}return t}}])&&function(e,t){for(var i=0;i<t.length;i++){var o=t[i];o.enumerable=o.enumerable||!1,o.configurable=!0,"value"in o&&(o.writable=!0),Object.defineProperty(e,o.key,o)}}(e.prototype,t),e}();i.WebStorageUrlStorage=a},{}],10:[function(e,t,i){function o(e){return(o="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e})(e)}function r(e){var t="function"==typeof Map?new Map:void 0;return(r=function(e){if(null===e||(i=e,-1===Function.toString.call(i).indexOf("[native code]")))return e;var i;if("function"!=typeof e)throw new TypeError("Super expression must either be null or a function");if(void 0!==t){if(t.has(e))return t.get(e);t.set(e,o)}function o(){return a(e,arguments,s(this).constructor)}return o.prototype=Object.create(e.prototype,{constructor:{value:o,enumerable:!1,writable:!0,configurable:!0}}),l(o,e)})(e)}function a(e,t,i){return(a=n()?Reflect.construct:function(e,t,i){var o=[null];o.push.apply(o,t);var r=new(Function.bind.apply(e,o));return i&&l(r,i.prototype),r}).apply(null,arguments)}function n(){if("undefined"!=typeof Reflect&&Reflect.construct&&!Reflect.construct.sham){if("function"==typeof Proxy)return 1;try{return Date.prototype.toString.call(Reflect.construct(Date,[],(function(){}))),1}catch(e){return}}}function l(e,t){return(l=Object.setPrototypeOf||function(e,t){return e.__proto__=t,e})(e,t)}function s(e){return(s=Object.setPrototypeOf?Object.getPrototypeOf:function(e){return e.__proto__||Object.getPrototypeOf(e)})(e)}Object.defineProperty(i,"__esModule",{value:!0}),i.default=void 0;var d=function(){!function(e,t){if("function"!=typeof t&&null!==t)throw new TypeError("Super expression must either be null or a function");e.prototype=Object.create(t&&t.prototype,{constructor:{value:e,writable:!0,configurable:!0}}),t&&l(e,t)}(t,r(Error));var e=function(e){return function(){var t,i,r,a=s(e);return i=this,!(r=n()?(t=s(this).constructor,Reflect.construct(a,arguments,t)):a.apply(this,arguments))||"object"!==o(r)&&"function"!=typeof r?function(e){if(void 0!==e)return e;throw new ReferenceError("this hasn't been initialised - super() hasn't been called")}(i):r}}(t);function t(i){var o,r,a,n,l,s,d=1<arguments.length&&void 0!==arguments[1]?arguments[1]:null,c=2<arguments.length&&void 0!==arguments[2]?arguments[2]:null,u=3<arguments.length&&void 0!==arguments[3]?arguments[3]:null;return function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,t),(o=e.call(this,i)).originalRequest=c,o.originalResponse=u,null!=(o.causingError=d)&&(i+=", caused by ".concat(d.toString())),null!=c&&(r=c.getHeader("X-Request-ID")||"n/a",a=c.getMethod(),n=c.getURL(),l=u?u.getStatus():"n/a",s=u?u.getBody()||"":"n/a",i+=", originated from request (method: ".concat(a,", url: ").concat(n,", response code: ").concat(l,", response text: ").concat(s,", request id: ").concat(r,")")),o.message=i,o}return t}();i.default=d},{}],11:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.enableDebugLog=function(){o=!0};var o=!(i.log=function(e){o&&console.log(e)})},{}],12:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=void 0;var o=function(){function e(){!function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,e)}var t;return(t=[{key:"listAllUploads",value:function(){return Promise.resolve([])}},{key:"findUploadsByFingerprint",value:function(){return Promise.resolve([])}},{key:"removeUpload",value:function(){return Promise.resolve()}},{key:"addUpload",value:function(){return Promise.resolve(null)}}])&&function(e,t){for(var i=0;i<t.length;i++){var o=t[i];o.enumerable=o.enumerable||!1,o.configurable=!0,"value"in o&&(o.writable=!0),Object.defineProperty(e,o.key,o)}}(e.prototype,t),e}();i.default=o},{}],13:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=void 0;var o=s(e("./error")),r=s(e("./uuid")),a=e("js-base64"),n=s(e("url-parse")),l=e("./logger");function s(e){return e&&e.__esModule?e:{default:e}}function d(e,t){var i,o=Object.keys(e);return Object.getOwnPropertySymbols&&(i=Object.getOwnPropertySymbols(e),t&&(i=i.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),o.push.apply(o,i)),o}function c(e){for(var t=1;t<arguments.length;t++){var i=null!=arguments[t]?arguments[t]:{};t%2?d(Object(i),!0).forEach((function(t){u(e,t,i[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(i)):d(Object(i)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(i,t))}))}return e}function u(e,t,i){return t in e?Object.defineProperty(e,t,{value:i,enumerable:!0,configurable:!0,writable:!0}):e[t]=i,e}function p(e,t){for(var i=0;i<t.length;i++){var o=t[i];o.enumerable=o.enumerable||!1,o.configurable=!0,"value"in o&&(o.writable=!0),Object.defineProperty(e,o.key,o)}}var h=function(){function e(t,i){!function(e,t){if(!(e instanceof t))throw new TypeError("Cannot call a class as a function")}(this,e),"resume"in i&&console.log("tus: The `resume` option has been removed in tus-js-client v2. Please use the URL storage API instead."),this.options=i,this._urlStorage=this.options.urlStorage,this.file=t,this.url=null,this._req=null,this._fingerprint=null,this._urlStorageKey=null,this._offset=null,this._aborted=!1,this._size=null,this._source=null,this._retryAttempt=0,this._retryTimeout=null,this._offsetBeforeRetry=0,this._parallelUploads=null,this._parallelUploadUrls=null}var t,i,r;return t=e,r=[{key:"terminate",value:function(t,i,r){var a=1<arguments.length&&void 0!==i?i:{};if("function"==typeof a||"function"==typeof(2<arguments.length?r:void 0))throw new Error("tus: the terminate function does not accept a callback since v2 anymore; please use the returned Promise instead");var n=g("DELETE",t,a);return n.send().then((function(e){if(204!==e.getStatus())throw new o.default("tus: unexpected response while terminating upload",null,n,e)})).catch((function(i){if(i instanceof o.default||(i=new o.default("tus: failed to terminate upload",i,n,null)),!b(i,0,a))throw i;var r=a.retryDelays[0],l=a.retryDelays.slice(1),s=c({},a,{retryDelays:l});return new Promise((function(e){return setTimeout(e,r)})).then((function(){return e.terminate(t,s)}))}))}}],(i=[{key:"findPreviousUploads",value:function(){var e=this;return this.options.fingerprint(this.file,this.options).then((function(t){return e._urlStorage.findUploadsByFingerprint(t)}))}},{key:"resumeFromPreviousUpload",value:function(e){this.url=e.uploadUrl||null,this._parallelUploadUrls=e.parallelUploadUrls||null,this._urlStorageKey=e.urlStorageKey}},{key:"start",value:function(){var e,t=this,i=this.file;i?this.options.endpoint||this.options.uploadUrl?null==(e=this.options.retryDelays)||"[object Array]"===Object.prototype.toString.call(e)?(1<this.options.parallelUploads&&["uploadUrl","uploadSize","uploadLengthDeferred"].forEach((function(e){t.options[e]&&t._emitError(new Error("tus: cannot use the ".concat(e," option when parallelUploads is enabled")))})),this.options.fingerprint(i,this.options).then((function(e){return null==e?(0,l.log)("No fingerprint was calculated meaning that the upload cannot be stored in the URL storage."):(0,l.log)("Calculated fingerprint: ".concat(e)),t._fingerprint=e,t._source?t._source:t.options.fileReader.openFile(i,t.options.chunkSize)})).then((function(e){t._source=e,1<t.options.parallelUploads||null!=t._parallelUploadUrls?t._startParallelUpload():t._startSingleUpload()})).catch((function(e){t._emitError(e)}))):this._emitError(new Error("tus: the `retryDelays` option must either be an array or null")):this._emitError(new Error("tus: neither an endpoint or an upload URL is provided")):this._emitError(new Error("tus: no file or stream to upload provided"))}},{key:"_startParallelUpload",value:function(){var t=this,i=this._size=this._source.size,o=0;this._parallelUploads=[];var r=null!=this._parallelUploadUrls?this._parallelUploadUrls.length:this.options.parallelUploads,a=function(e,t,i){for(var o=Math.floor(e/t),r=[],a=0;a<t;a++)r.push({start:o*a,end:o*(a+1)});return r[t-1].end=e,i&&r.forEach((function(e,t){e.uploadUrl=i[t]||null})),r}(this._source.size,r,this._parallelUploadUrls);this._parallelUploadUrls=new Array(a.length);var n,s=a.map((function(r,n){var l=0;return t._source.slice(r.start,r.end).then((function(s){var d=s.value;return new Promise((function(s,u){var p=c({},t.options,{uploadUrl:r.uploadUrl||null,storeFingerprintForResuming:!1,removeFingerprintOnSuccess:!1,parallelUploads:1,metadata:{},headers:c({},t.options.headers,{"Upload-Concat":"partial"}),onSuccess:s,onError:u,onProgress:function(e){o=o-l+e,l=e,t._emitProgress(o,i)},_onUploadUrlAvailable:function(){t._parallelUploadUrls[n]=h.url,t._parallelUploadUrls.filter((function(e){return!!e})).length===a.length&&t._saveUploadInUrlStorage()}}),h=new e(d,p);h.start(),t._parallelUploads.push(h)}))}))}));Promise.all(s).then((function(){(n=t._openRequest("POST",t.options.endpoint)).setHeader("Upload-Concat","final;".concat(t._parallelUploadUrls.join(" ")));var e=m(t.options.metadata);return""!==e&&n.setHeader("Upload-Metadata",e),t._sendRequest(n,null)})).then((function(e){var i;f(e.getStatus(),200)?null!=(i=e.getHeader("Location"))?(t.url=v(t.options.endpoint,i),(0,l.log)("Created upload at ".concat(t.url)),t._emitSuccess()):t._emitHttpError(n,e,"tus: invalid or missing Location header"):t._emitHttpError(n,e,"tus: unexpected response while creating upload")})).catch((function(e){t._emitError(e)}))}},{key:"_startSingleUpload",value:function(){if(this.options.uploadLengthDeferred)this._size=null;else if(null!=this.options.uploadSize){if(this._size=+this.options.uploadSize,isNaN(this._size))return void this._emitError(new Error("tus: cannot convert `uploadSize` option into a number"))}else if(this._size=this._source.size,null==this._size)return void this._emitError(new Error("tus: cannot automatically derive upload's size from input and must be specified manually using the `uploadSize` option"));return this._aborted=!1,null!=this.url?((0,l.log)("Resuming upload from previous URL: ".concat(this.url)),void this._resumeUpload()):null!=this.options.uploadUrl?((0,l.log)("Resuming upload from provided URL: ".concat(this.options.url)),this.url=this.options.uploadUrl,void this._resumeUpload()):((0,l.log)("Creating a new upload"),void this._createUpload())}},{key:"abort",value:function(t,i){var o=this;if("function"==typeof i)throw new Error("tus: the abort function does not accept a callback since v2 anymore; please use the returned Promise instead");return null!=this._parallelUploads&&this._parallelUploads.forEach((function(e){e.abort(t)})),null!==this._req&&(this._req.abort(),this._source.close()),this._aborted=!0,null!=this._retryTimeout&&(clearTimeout(this._retryTimeout),this._retryTimeout=null),t&&null!=this.url?e.terminate(this.url,this.options).then((function(){return o._removeFromUrlStorage()})):Promise.resolve()}},{key:"_emitHttpError",value:function(e,t,i,r){this._emitError(new o.default(i,r,e,t))}},{key:"_emitError",value:function(e){var t=this;if(!this._aborted){if(null!=this.options.retryDelays&&(null!=this._offset&&this._offset>this._offsetBeforeRetry&&(this._retryAttempt=0),b(e,this._retryAttempt,this.options))){var i=this.options.retryDelays[this._retryAttempt++];return this._offsetBeforeRetry=this._offset,void(this._retryTimeout=setTimeout((function(){t.start()}),i))}if("function"!=typeof this.options.onError)throw e;this.options.onError(e)}}},{key:"_emitSuccess",value:function(){this.options.removeFingerprintOnSuccess&&this._removeFromUrlStorage(),"function"==typeof this.options.onSuccess&&this.options.onSuccess()}},{key:"_emitProgress",value:function(e,t){"function"==typeof this.options.onProgress&&this.options.onProgress(e,t)}},{key:"_emitChunkComplete",value:function(e,t,i){"function"==typeof this.options.onChunkComplete&&this.options.onChunkComplete(e,t,i)}},{key:"_createUpload",value:function(){var e,t,i=this;this.options.endpoint?(e=this._openRequest("POST",this.options.endpoint),this.options.uploadLengthDeferred?e.setHeader("Upload-Defer-Length",1):e.setHeader("Upload-Length",this._size),""!==(t=m(this.options.metadata))&&e.setHeader("Upload-Metadata",t),(this.options.uploadDataDuringCreation&&!this.options.uploadLengthDeferred?(this._offset=0,this._addChunkToRequest(e)):this._sendRequest(e,null)).then((function(t){if(f(t.getStatus(),200)){var o=t.getHeader("Location");if(null!=o){if(i.url=v(i.options.endpoint,o),(0,l.log)("Created upload at ".concat(i.url)),"function"==typeof i.options._onUploadUrlAvailable&&i.options._onUploadUrlAvailable(),0===i._size)return i._emitSuccess(),void i._source.close();i._saveUploadInUrlStorage(),i.options.uploadDataDuringCreation?i._handleUploadResponse(e,t):(i._offset=0,i._performUpload())}else i._emitHttpError(e,t,"tus: invalid or missing Location header")}else i._emitHttpError(e,t,"tus: unexpected response while creating upload")})).catch((function(t){i._emitHttpError(e,null,"tus: failed to create upload",t)}))):this._emitError(new Error("tus: unable to create upload because no endpoint is provided"))}},{key:"_resumeUpload",value:function(){var e=this,t=this._openRequest("HEAD",this.url);this._sendRequest(t,null).then((function(i){var o=i.getStatus();if(!f(o,200))return f(o,400)&&e._removeFromUrlStorage(),423===o?void e._emitHttpError(t,i,"tus: upload is currently locked; retry later"):e.options.endpoint?(e.url=null,void e._createUpload()):void e._emitHttpError(t,i,"tus: unable to resume upload (new upload cannot be created without an endpoint)");var r=parseInt(i.getHeader("Upload-Offset"),10);if(isNaN(r))e._emitHttpError(t,i,"tus: invalid or missing offset value");else{var a=parseInt(i.getHeader("Upload-Length"),10);if(!isNaN(a)||e.options.uploadLengthDeferred){if("function"==typeof e.options._onUploadUrlAvailable&&e.options._onUploadUrlAvailable(),r===a)return e._emitProgress(a,a),void e._emitSuccess();e._offset=r,e._performUpload()}else e._emitHttpError(t,i,"tus: invalid or missing length value")}})).catch((function(i){e._emitHttpError(t,null,"tus: failed to resume upload",i)}))}},{key:"_performUpload",value:function(){var e,t=this;this._aborted||(this.options.overridePatchMethod?(e=this._openRequest("POST",this.url)).setHeader("X-HTTP-Method-Override","PATCH"):e=this._openRequest("PATCH",this.url),e.setHeader("Upload-Offset",this._offset),this._addChunkToRequest(e).then((function(i){f(i.getStatus(),200)?t._handleUploadResponse(e,i):t._emitHttpError(e,i,"tus: unexpected response while uploading chunk")})).catch((function(i){t._aborted||t._emitHttpError(e,null,"tus: failed to upload chunk at offset "+t._offset,i)})))}},{key:"_addChunkToRequest",value:function(e){var t=this,i=this._offset,o=this._offset+this.options.chunkSize;return e.setProgressHandler((function(e){t._emitProgress(i+e,t._size)})),e.setHeader("Content-Type","application/offset+octet-stream"),(o===1/0||o>this._size)&&!this.options.uploadLengthDeferred&&(o=this._size),this._source.slice(i,o).then((function(i){var o=i.value,r=i.done;return t.options.uploadLengthDeferred&&r&&(t._size=t._offset+(o&&o.size?o.size:0),e.setHeader("Upload-Length",t._size)),null===o?t._sendRequest(e):(t._emitProgress(t._offset,t._size),t._sendRequest(e,o))}))}},{key:"_handleUploadResponse",value:function(e,t){var i=parseInt(t.getHeader("Upload-Offset"),10);if(isNaN(i))this._emitHttpError(e,t,"tus: invalid or missing offset value");else{if(this._emitProgress(i,this._size),this._emitChunkComplete(i-this._offset,i,this._size),(this._offset=i)==this._size)return this._emitSuccess(),void this._source.close();this._performUpload()}}},{key:"_openRequest",value:function(e,t){var i=g(e,t,this.options);return this._req=i}},{key:"_removeFromUrlStorage",value:function(){var e=this;this._urlStorageKey&&(this._urlStorage.removeUpload(this._urlStorageKey).catch((function(t){e._emitError(t)})),this._urlStorageKey=null)}},{key:"_saveUploadInUrlStorage",value:function(){var e,t=this;this.options.storeFingerprintForResuming&&this._fingerprint&&(e={size:this._size,metadata:this.options.metadata,creationTime:(new Date).toString()},this._parallelUploads?e.parallelUploadUrls=this._parallelUploadUrls:e.uploadUrl=this.url,this._urlStorage.addUpload(this._fingerprint,e).then((function(e){return t._urlStorageKey=e})).catch((function(e){t._emitError(e)})))}},{key:"_sendRequest",value:function(e,t){var i=this,o=1<arguments.length&&void 0!==t?t:null;return"function"==typeof this.options.onBeforeRequest&&this.options.onBeforeRequest(e),e.send(o).then((function(t){return"function"==typeof i.options.onAfterResponse&&i.options.onAfterResponse(e,t),t}))}}])&&p(t.prototype,i),r&&p(t,r),e}();function m(e){var t=[];for(var i in e)t.push(i+" "+a.Base64.encode(e[i]));return t.join(",")}function f(e,t){return t<=e&&e<t+100}function g(e,t,i){var o=i.httpStack.createRequest(e,t);o.setHeader("Tus-Resumable","1.0.0");var a,n=i.headers||{};for(var l in n)o.setHeader(l,n[l]);return i.addRequestId&&(a=(0,r.default)(),o.setHeader("X-Request-ID",a)),o}function b(e,t,i){var o,r=e.originalResponse?e.originalResponse.getStatus():0,a=!f(r,400)||409===r||423===r;return null!=i.retryDelays&&t<i.retryDelays.length&&null!=e.originalRequest&&a&&(o=!0,"undefined"!=typeof window&&"navigator"in window&&!1===window.navigator.onLine&&(o=!1),o)}function v(e,t){return new n.default(t,e).toString()}h.defaultOptions={endpoint:null,uploadUrl:null,metadata:{},fingerprint:null,uploadSize:null,onProgress:null,onChunkComplete:null,onSuccess:null,onError:null,_onUploadUrlAvailable:null,overridePatchMethod:!1,headers:{},addRequestId:!1,onBeforeRequest:null,onAfterResponse:null,chunkSize:1/0,retryDelays:[0,1e3,3e3,5e3],parallelUploads:1,storeFingerprintForResuming:!0,removeFingerprintOnSuccess:!1,uploadLengthDeferred:!1,uploadDataDuringCreation:!1,urlStorage:null,fileReader:null,httpStack:null},i.default=h},{"./error":10,"./logger":11,"./uuid":14,"js-base64":15,"url-parse":18}],14:[function(e,t,i){Object.defineProperty(i,"__esModule",{value:!0}),i.default=function(){return"xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g,(function(e){var t=16*Math.random()|0;return("x"==e?t:3&t|8).toString(16)}))}},{}],15:[function(require,module,exports){(function(global){var Gk,Hk;Gk="undefined"!=typeof self?self:"undefined"!=typeof window?window:void 0!==global?global:this,Hk=function(global){var _Base64=global.Base64,version="2.4.9",buffer;if(void 0!==module&&module.exports)try{buffer=eval("require('buffer').Buffer")}catch(e){buffer=void 0}var b64chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",b64tab=function(e){for(var t={},i=0,o=e.length;i<o;i++)t[e.charAt(i)]=i;return t}(b64chars),fromCharCode=String.fromCharCode,cb_utob=function(e){if(e.length<2)return(t=e.charCodeAt(0))<128?e:t<2048?fromCharCode(192|t>>>6)+fromCharCode(128|63&t):fromCharCode(224|t>>>12&15)+fromCharCode(128|t>>>6&63)+fromCharCode(128|63&t);var t=65536+1024*(e.charCodeAt(0)-55296)+(e.charCodeAt(1)-56320);return fromCharCode(240|t>>>18&7)+fromCharCode(128|t>>>12&63)+fromCharCode(128|t>>>6&63)+fromCharCode(128|63&t)},re_utob=/[\uD800-\uDBFF][\uDC00-\uDFFFF]|[^\x00-\x7F]/g,utob=function(e){return e.replace(re_utob,cb_utob)},cb_encode=function(e){var t=[0,2,1][e.length%3],i=e.charCodeAt(0)<<16|(1<e.length?e.charCodeAt(1):0)<<8|(2<e.length?e.charCodeAt(2):0);return[b64chars.charAt(i>>>18),b64chars.charAt(i>>>12&63),2<=t?"=":b64chars.charAt(i>>>6&63),1<=t?"=":b64chars.charAt(63&i)].join("")},btoa=global.btoa?function(e){return global.btoa(e)}:function(e){return e.replace(/[\s\S]{1,3}/g,cb_encode)},_encode=buffer?buffer.from&&Uint8Array&&buffer.from!==Uint8Array.from?function(e){return(e.constructor===buffer.constructor?e:buffer.from(e)).toString("base64")}:function(e){return(e.constructor===buffer.constructor?e:new buffer(e)).toString("base64")}:function(e){return btoa(utob(e))},encode=function(e,t){return t?_encode(String(e)).replace(/[+\/]/g,(function(e){return"+"==e?"-":"_"})).replace(/=/g,""):_encode(String(e))},encodeURI=function(e){return encode(e,!0)},re_btou=new RegExp(["[À-ß][-¿]","[à-ï][-¿]{2}","[ð-÷][-¿]{3}"].join("|"),"g"),cb_btou=function(e){switch(e.length){case 4:var t=((7&e.charCodeAt(0))<<18|(63&e.charCodeAt(1))<<12|(63&e.charCodeAt(2))<<6|63&e.charCodeAt(3))-65536;return fromCharCode(55296+(t>>>10))+fromCharCode(56320+(1023&t));case 3:return fromCharCode((15&e.charCodeAt(0))<<12|(63&e.charCodeAt(1))<<6|63&e.charCodeAt(2));default:return fromCharCode((31&e.charCodeAt(0))<<6|63&e.charCodeAt(1))}},btou=function(e){return e.replace(re_btou,cb_btou)},cb_decode=function(e){var t=e.length,i=t%4,o=(0<t?b64tab[e.charAt(0)]<<18:0)|(1<t?b64tab[e.charAt(1)]<<12:0)|(2<t?b64tab[e.charAt(2)]<<6:0)|(3<t?b64tab[e.charAt(3)]:0),r=[fromCharCode(o>>>16),fromCharCode(o>>>8&255),fromCharCode(255&o)];return r.length-=[0,0,2,1][i],r.join("")},atob=global.atob?function(e){return global.atob(e)}:function(e){return e.replace(/[\s\S]{1,4}/g,cb_decode)},_decode=buffer?buffer.from&&Uint8Array&&buffer.from!==Uint8Array.from?function(e){return(e.constructor===buffer.constructor?e:buffer.from(e,"base64")).toString()}:function(e){return(e.constructor===buffer.constructor?e:new buffer(e,"base64")).toString()}:function(e){return btou(atob(e))},decode=function(e){return _decode(String(e).replace(/[-_]/g,(function(e){return"-"==e?"+":"/"})).replace(/[^A-Za-z0-9\+\/]/g,""))},noConflict=function(){var e=global.Base64;return global.Base64=_Base64,e},noEnum;return global.Base64={VERSION:version,atob:atob,btoa:btoa,fromBase64:decode,toBase64:encode,utob:utob,encode:encode,encodeURI:encodeURI,btou:btou,decode:decode,noConflict:noConflict,__buffer__:buffer},"function"==typeof Object.defineProperty&&(noEnum=function(e){return{value:e,enumerable:!1,writable:!0,configurable:!0}},global.Base64.extendString=function(){Object.defineProperty(String.prototype,"fromBase64",noEnum((function(){return decode(this)}))),Object.defineProperty(String.prototype,"toBase64",noEnum((function(e){return encode(this,e)}))),Object.defineProperty(String.prototype,"toBase64URI",noEnum((function(){return encode(this,!0)})))}),global.Meteor&&(Base64=global.Base64),void 0!==module&&module.exports&&(module.exports.Base64=global.Base64),{Base64:global.Base64}},"object"==typeof exports&&void 0!==module?module.exports=Hk(Gk):Hk(Gk)}).call(this,"undefined"!=typeof global?global:"undefined"!=typeof self?self:"undefined"!=typeof window?window:{})},{}],16:[function(e,t,i){var o=Object.prototype.hasOwnProperty;function r(e){return decodeURIComponent(e.replace(/\+/g," "))}i.stringify=function(e,t){t=t||"";var i=[];for(var r in"string"!=typeof t&&(t="?"),e)o.call(e,r)&&i.push(encodeURIComponent(r)+"="+encodeURIComponent(e[r]));return i.length?t+i.join("&"):""},i.parse=function(e){for(var t,i=/([^=?&]+)=?([^&]*)/g,o={};t=i.exec(e);){var a=r(t[1]),n=r(t[2]);a in o||(o[a]=n)}return o}},{}],17:[function(e,t,i){t.exports=function(e,t){if(t=t.split(":")[0],!(e=+e))return!1;switch(t){case"http":case"ws":return 80!==e;case"https":case"wss":return 443!==e;case"ftp":return 21!==e;case"gopher":return 70!==e;case"file":return!1}return 0!==e}},{}],18:[function(e,t,i){(function(i){var o=e("requires-port"),r=e("querystringify"),a=/^([a-z][a-z0-9.+-]*:)?(\/\/)?([\S\s]*)/i,n=/^[A-Za-z][A-Za-z0-9+-.]*:\/\//,l=[["#","hash"],["?","query"],function(e){return e.replace("\\","/")},["/","pathname"],["@","auth",1],[NaN,"host",void 0,1,1],[/:(\d+)$/,"port",void 0,1],[NaN,"hostname",void 0,1,1]],s={hash:1,query:1};function d(e){var t,o=i&&i.location||{},r={},a=typeof(e=e||o);if("blob:"===e.protocol)r=new u(unescape(e.pathname),{});else if("string"==a)for(t in r=new u(e,{}),s)delete r[t];else if("object"==a){for(t in e)t in s||(r[t]=e[t]);void 0===r.slashes&&(r.slashes=n.test(e.href))}return r}function c(e){var t=a.exec(e);return{protocol:t[1]?t[1].toLowerCase():"",slashes:!!t[2],rest:t[3]}}function u(e,t,i){if(!(this instanceof u))return new u(e,t,i);var a,n,s,p,h,m,f=l.slice(),g=typeof t,b=this,v=0;for("object"!=g&&"string"!=g&&(i=t,t=null),i&&"function"!=typeof i&&(i=r.parse),t=d(t),a=!(n=c(e||"")).protocol&&!n.slashes,b.slashes=n.slashes||a&&t.slashes,b.protocol=n.protocol||t.protocol||"",e=n.rest,n.slashes||(f[3]=[/(.*)/,"pathname"]);v<f.length;v++)"function"!=typeof(p=f[v])?(s=p[0],m=p[1],s!=s?b[m]=e:"string"==typeof s?~(h=e.indexOf(s))&&(e="number"==typeof p[2]?(b[m]=e.slice(0,h),e.slice(h+p[2])):(b[m]=e.slice(h),e.slice(0,h))):(h=s.exec(e))&&(b[m]=h[1],e=e.slice(0,h.index)),b[m]=b[m]||a&&p[3]&&t[m]||"",p[4]&&(b[m]=b[m].toLowerCase())):e=p(e);i&&(b.query=i(b.query)),a&&t.slashes&&"/"!==b.pathname.charAt(0)&&(""!==b.pathname||""!==t.pathname)&&(b.pathname=function(e,t){for(var i=(t||"/").split("/").slice(0,-1).concat(e.split("/")),o=i.length,r=i[o-1],a=!1,n=0;o--;)"."===i[o]?i.splice(o,1):".."===i[o]?(i.splice(o,1),n++):n&&(0===o&&(a=!0),i.splice(o,1),n--);return a&&i.unshift(""),"."!==r&&".."!==r||i.push(""),i.join("/")}(b.pathname,t.pathname)),o(b.port,b.protocol)||(b.host=b.hostname,b.port=""),b.username=b.password="",b.auth&&(p=b.auth.split(":"),b.username=p[0]||"",b.password=p[1]||""),b.origin=b.protocol&&b.host&&"file:"!==b.protocol?b.protocol+"//"+b.host:"null",b.href=b.toString()}u.prototype={set:function(e,t,i){var a,n=this;switch(e){case"query":"string"==typeof t&&t.length&&(t=(i||r.parse)(t)),n[e]=t;break;case"port":n[e]=t,o(t,n.protocol)?t&&(n.host=n.hostname+":"+t):(n.host=n.hostname,n[e]="");break;case"hostname":n[e]=t,n.port&&(t+=":"+n.port),n.host=t;break;case"host":n[e]=t,/:\d+$/.test(t)?(t=t.split(":"),n.port=t.pop(),n.hostname=t.join(":")):(n.hostname=t,n.port="");break;case"protocol":n.protocol=t.toLowerCase(),n.slashes=!i;break;case"pathname":case"hash":t?(a="pathname"===e?"/":"#",n[e]=t.charAt(0)!==a?a+t:t):n[e]=t;break;default:n[e]=t}for(var s=0;s<l.length;s++){var d=l[s];d[4]&&(n[d[1]]=n[d[1]].toLowerCase())}return n.origin=n.protocol&&n.host&&"file:"!==n.protocol?n.protocol+"//"+n.host:"null",n.href=n.toString(),n},toString:function(e){e&&"function"==typeof e||(e=r.stringify);var t,i=this,o=i.protocol;o&&":"!==o.charAt(o.length-1)&&(o+=":");var a=o+(i.slashes?"//":"");return i.username&&(a+=i.username,i.password&&(a+=":"+i.password),a+="@"),a+=i.host+i.pathname,(t="object"==typeof i.query?e(i.query):i.query)&&(a+="?"!==t.charAt(0)?"?"+t:t),i.hash&&(a+=i.hash),a}},u.extractProtocol=c,u.location=d,u.qs=r,t.exports=u}).call(this,"undefined"!=typeof global?global:"undefined"!=typeof self?self:"undefined"!=typeof window?window:{})},{querystringify:16,"requires-port":17}]},{},[4])(4)}));var tus$1=tus;
/**
 @license
 Copyright (c) 2015-2022 Lablup Inc. All rights reserved.
 */let BackendAiStorageList=class extends BackendAIPage{constructor(){super(),this._APIMajorVersion=5,this.storageType="general",this.folders=[],this.folderInfo=Object(),this.is_admin=!1,this.enableStorageProxy=!1,this.authenticated=!1,this.renameFolderName="",this.deleteFolderName="",this.leaveFolderName="",this.explorer=Object(),this.explorerFiles=[],this.existingFile="",this.invitees=[],this.selectedFolder="",this.selectedFolderType="",this.downloadURL="",this.uploadFiles=[],this.fileUploadQueue=[],this.fileUploadCount=0,this.concurrentFileUploadLimit=2,this.vhost="",this.vhosts=[],this.allowedGroups=[],this.indicator=Object(),this.notification=Object(),this.sessionLauncher=Object(),this.listCondition="loading",this.allowed_folder_type=[],this.uploadFilesExist=!1,this._boundIndexRenderer=Object(),this._boundTypeRenderer=Object(),this._boundFolderListRenderer=Object(),this._boundControlFolderListRenderer=Object(),this._boundControlFileListRenderer=Object(),this._boundPermissionViewRenderer=Object(),this._boundOwnerRenderer=Object(),this._boundFileNameRenderer=Object(),this._boundCreatedTimeRenderer=Object(),this._boundPermissionRenderer=Object(),this._boundCloneableRenderer=Object(),this._boundQuotaRenderer=Object(),this._boundUploadListRenderer=Object(),this._boundUploadProgressRenderer=Object(),this._boundInviteeInfoRenderer=Object(),this._boundIDRenderer=Object(),this._boundStatusRenderer=Object(),this._uploadFlag=!0,this._folderRefreshing=!1,this.lastQueryTime=0,this.isWritable=!1,this.permissions={rw:"Read-Write",ro:"Read-Only",wd:"Delete"},this._maxFileUploadSize=-1,this.oldFileExtension="",this.newFileExtension="",this.is_dir=!1,this.minimumResource={cpu:1,mem:.5},this.filebrowserSupportedImages=[],this.storageProxyInfo=Object(),this.quotaSupportStorageBackends=["xfs","weka","spectrumscale"],this.quotaUnit={MiB:Math.pow(2,20),GiB:Math.pow(2,30),TiB:Math.pow(2,40),PiB:Math.pow(2,50)},this.maxSize={value:0,unit:"MiB"},this.quota={value:0,unit:"MiB"},this._boundIndexRenderer=this.indexRenderer.bind(this),this._boundTypeRenderer=this.typeRenderer.bind(this),this._boundControlFolderListRenderer=this.controlFolderListRenderer.bind(this),this._boundControlFileListRenderer=this.controlFileListRenderer.bind(this),this._boundPermissionViewRenderer=this.permissionViewRenderer.bind(this),this._boundCloneableRenderer=this.CloneableRenderer.bind(this),this._boundOwnerRenderer=this.OwnerRenderer.bind(this),this._boundFileNameRenderer=this.fileNameRenderer.bind(this),this._boundCreatedTimeRenderer=this.createdTimeRenderer.bind(this),this._boundPermissionRenderer=this.permissionRenderer.bind(this),this._boundFolderListRenderer=this.folderListRenderer.bind(this),this._boundQuotaRenderer=this.quotaRenderer.bind(this),this._boundUploadListRenderer=this.uploadListRenderer.bind(this),this._boundUploadProgressRenderer=this.uploadProgressRenderer.bind(this),this._boundInviteeInfoRenderer=this.inviteeInfoRenderer.bind(this),this._boundIDRenderer=this.iDRenderer.bind(this),this._boundStatusRenderer=this.statusRenderer.bind(this)}static get styles(){return[BackendAiStyles,IronFlex,IronFlexAlignment,IronPositioning,i$1`
        vaadin-grid {
          border: 0 !important;
          height: calc(100vh - 225px);
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
          margin-top:10px;
          margin-bottom: 10px;
        }

        .folder-action-buttons wl-button {
          margin-right: 10px;
        }

        wl-button > wl-icon {
          --icon-size: 24px;
          padding: 0;
        }

        wl-icon {
          --icon-size: 16px;
          padding: 0;
        }

        wl-button.button {
          width: 330px;
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
          width: calc(100% - 88px); /* 88px is width for mini-ui icon of drawer menu */
        }

        #folder-explorer-dialog vaadin-grid vaadin-grid-column {
          height: 32px !important;
        }

        #folder-explorer-dialog vaadin-grid mwc-icon-button {
          --mdc-icon-size: 24px;
          --mdc-icon-button-size: 28px;
        }

        #filebrowser-notification-dialog {
          --component-width: 350px;
        }

        vaadin-text-field {
          --vaadin-text-field-default-width: auto;
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
          transition: color ease-in .2s;
          border: solid;
          border-width: 0 2px 2px 0;
          border-color: #242424;
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
          --mdc-theme-primary: #242424;
          --mdc-text-field-fill-color: transparent;
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

        wl-button.goto {
          margin: 0;
          padding: 5px;
          min-width: 0;
        }

        wl-button.goto:last-of-type {
          font-weight: bold;
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

        div#dropzone, div#dropzone p {
          margin: 0;
          padding: 0;
          width: 100%;
          background: rgba(211, 211, 211, .5);
          text-align: center;
        }

        .progress {
          padding: 30px 10px;
          border: 1px solid lightgray;
        }

        .progress-item {
          padding: 10px 30px;
        }

        wl-button {
          --button-bg: var(--paper-orange-50);
          --button-bg-hover: var(--paper-orange-100);
          --button-bg-active: var(--paper-orange-600);
          color: var(--paper-orange-900);
        }

        backend-ai-dialog mwc-textfield,
        backend-ai-dialog mwc-select {
          --mdc-typography-font-family: var(--general-font-family);
          --mdc-typography-label-font-size: 12px;
          --mdc-theme-primary: var(--general-textfield-selected-color);
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

        mwc-radio {
          --mdc-theme-secondary: var(--general-textfield-selected-color);
        }

        #textfields wl-textfield,
        wl-label {
          margin-bottom: 20px;
        }

        wl-label {
          --label-font-family: 'Ubuntu', Roboto;
          --label-color: black;
        }
        wl-checkbox {
          --checkbox-color: var(--paper-orange-900);
          --checkbox-color-checked: var(--paper-orange-900);
          --checkbox-bg-checked: var(--paper-orange-900);
          --checkbox-color-disabled-checked: var(--paper-orange-900);
          --checkbox-bg-disabled-checked: var(--paper-orange-900);
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
          -webkit-filter: grayscale(1.0);
          filter: grayscale(1.0);
        }

        img#filebrowser-img {
          width:24px;
          margin:15px 10px;
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
          #folder-explorer-dialog.mini_ui
           {
            --component-width: calc(100% - 45px); /* calc(100% - 30px); */
          }
        }
      `]}_toggleFileListCheckbox(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll(".multiple-action-buttons");this.fileListGrid.selectedItems.length>0?[].forEach.call(t,(e=>{e.style.display="block"})):[].forEach.call(t,(e=>{e.style.display="none"}))}_updateQuotaInputHumanReadableValue(){let e="MiB";const t=Number(this.modifyFolderQuotaInput.value)*this.quotaUnit[this.modifyFolderQuotaUnitSelect.value],i=this.maxSize.value*this.quotaUnit[this.maxSize.unit];[this.modifyFolderQuotaInput.value,e]=globalThis.backendaiutils._humanReadableFileSize(t).split(" "),["Bytes","KiB","MiB"].includes(e)?(this.modifyFolderQuotaInput.value="MiB"===e?Number(this.modifyFolderQuotaInput.value)<1?"1":Math.round(Number(this.modifyFolderQuotaInput.value)).toString():"1",e="MiB"):(this.modifyFolderQuotaInput.value=parseFloat(this.modifyFolderQuotaInput.value).toFixed(1),i<t&&(this.modifyFolderQuotaInput.value=this.maxSize.value.toString(),e=this.maxSize.unit)),this.modifyFolderQuotaInput.step="MiB"===this.modifyFolderQuotaUnitSelect.value?0:.1;const o=this.modifyFolderQuotaUnitSelect.items.findIndex((t=>t.value===e));this.modifyFolderQuotaUnitSelect.select(o)}render(){return y`
      <lablup-loading-spinner id="loading-spinner"></lablup-loading-spinner>
      <div class="list-wrapper">
        <vaadin-grid class="folderlist" theme="row-stripes column-borders wrap-cell-content compact" column-reordering-allowed aria-label="Folder list" .items="${this.folders}">
          <vaadin-grid-column width="40px" flex-grow="0" resizable header="#" text-align="center" .renderer="${this._boundIndexRenderer}">
          </vaadin-grid-column>
          <lablup-grid-sort-filter-column path="name" width="80px" resizable .renderer="${this._boundFolderListRenderer}"
              header="${translate("data.folders.Name")}"></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column path="id" width="130px" flex-grow="0" resizable header="ID" .renderer="${this._boundIDRenderer}">
          </lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column path="host" width="105px" flex-grow="0" resizable
              header="${translate("data.folders.Location")}"></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column path="status" width="80px" flex-grow="0" resizable .renderer="${this._boundStatusRenderer}"
              header="${translate("data.folders.Status")}"></lablup-grid-sort-filter-column>
          <vaadin-grid-sort-column path="max_size" width="95px" flex-grow="0" resizable header="${translate("data.folders.FolderQuota")}" .renderer="${this._boundQuotaRenderer}"></vaadin-grid-sort-column>
          <lablup-grid-sort-filter-column path="ownership_type" width="70px" flex-grow="0" resizable header="${translate("data.folders.Type")}" .renderer="${this._boundTypeRenderer}"></lablup-grid-sort-filter-column>
          <vaadin-grid-column width="95px" flex-grow="0" resizable header="${translate("data.folders.Permission")}" .renderer="${this._boundPermissionViewRenderer}"></vaadin-grid-column>
          <vaadin-grid-column auto-width flex-grow="0" resizable header="${translate("data.folders.Owner")}" .renderer="${this._boundOwnerRenderer}"></vaadin-grid-column>
          ${this.enableStorageProxy?y`
            <!--<vaadin-grid-column
                auto-width flex-grow="0" resizable header="${translate("data.folders.Cloneable")}"
                .renderer="${this._boundCloneableRenderer}"></vaadin-grid-column>`:y``}
          <vaadin-grid-column auto-width resizable header="${translate("data.folders.Control")}" .renderer="${this._boundControlFolderListRenderer}"></vaadin-grid-column>-->
        </vaadin-grid>
        <backend-ai-list-status id="list-status" statusCondition="${this.listCondition}" message="${get("data.folders.NoFolderToDisplay")}"></backend-ai-list-status>
      </div>
      <backend-ai-dialog id="modify-folder-dialog" fixed backdrop>
        <span slot="title">${translate("data.folders.FolderOptionUpdate")}</span>
        <div slot="content" class="vertical layout flex">
          <div class="vertical layout" id="modify-quota-controls"
               style="display:${this._checkFolderSupportSizeQuota(this.folderInfo.host)?"flex":"none"}">
            <div class="horizontal layout center justified">
                <mwc-textfield id="modify-folder-quota" label="${translate("data.folders.FolderQuota")}" value="${this.maxSize.value}"
                    type="number" min="0" step="0.1" @change="${()=>this._updateQuotaInputHumanReadableValue()}"></mwc-textfield>
                <mwc-select class="fixed-position" id="modify-folder-quota-unit" @change="${()=>this._updateQuotaInputHumanReadableValue()}" fixedMenuPosition>
                ${Object.keys(this.quotaUnit).map(((e,t)=>y`
                      <mwc-list-item value="${e}" ?selected="${e==this.maxSize.unit}">${e}</mwc-list-item>
                    `))}
                </mwc-select>
            </div>
            <span class="helper-text">${translate("data.folders.MaxFolderQuota")} : ${this.maxSize.value+" "+this.maxSize.unit}</span>
          </div>
          <mwc-select class="full-width fixed-position" id="update-folder-permission" style="width:100%;" label="${translate("data.Permission")}"
                  fixedMenuPosition>
                  ${Object.keys(this.permissions).map((e=>y`
                    <mwc-list-item value="${this.permissions[e]}">${this.permissions[e]}</mwc-list-item>
                  `))}
          </mwc-select>
          ${this.enableStorageProxy?y`
          <!--<div class="horizontal layout flex wrap center justified">
            <p style="color:rgba(0, 0, 0, 0.6);">
              ${translate("data.folders.Cloneable")}
            </p>
            <mwc-switch id="update-folder-cloneable" style="margin-right:10px;">
            </mwc-switch>
          </div>-->
          `:y``}
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button unelevated fullwidth type="submit" icon="edit" id="update-button" @click="${()=>this._updateFolder()}">
            ${translate("data.Update")}
          </mwc-button>
        </div>
      </backend-ai-dialog>

      <backend-ai-dialog id="modify-folder-name-dialog" fixed backdrop>
        <span slot="title">${translate("data.folders.RenameAFolder")}</span>
        <div slot="content" class="vertical layout flex">
          <mwc-textfield
              id="clone-folder-src" label="${translate("data.ExistingFolderName")}" value="${this.renameFolderName}"
              disabled></mwc-textfield>
          <mwc-textfield class="red" id="new-folder-name" label="${translate("data.folders.TypeNewFolderName")}"
              pattern="^[a-zA-Z0-9\._-]*$" autoValidate validationMessage="${translate("data.Allowslettersnumbersand-_dot")}"
              maxLength="64" placeholder="${get("maxLength.64chars")}"
              @change="${()=>this._validateFolderName(!0)}"></mwc-textfield>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button unelevated fullwidth type="submit" icon="edit" id="update-button" @click="${()=>this._updateFolderName()}">
            ${translate("data.Update")}
          </mwc-button>
        </div>
      </backend-ai-dialog>

      <backend-ai-dialog id="delete-folder-dialog" fixed backdrop>
        <span slot="title">${translate("data.folders.DeleteAFolder")}</span>
        <div slot="content">
          <div class="warning" style="margin-left:16px;">${translate("dialog.warning.CannotBeUndone")}</div>
          <mwc-textfield class="red" id="delete-folder-name" label="${translate("data.folders.TypeFolderNameToDelete")}"
                         maxLength="64" placeholder="${get("maxLength.64chars")}"></mwc-textfield>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button unelevated fullwidth type="submit" icon="close" id="delete-button" @click="${()=>this._deleteFolderWithCheck()}">
            ${translate("data.folders.Delete")}
          </mwc-button>
        </div>
      </backend-ai-dialog>

      <backend-ai-dialog id="leave-folder-dialog" fixed backdrop>
        <span slot="title">${translate("data.folders.LeaveAFolder")}</span>
        <div slot="content">
          <div class="warning" style="margin-left:16px;">${translate("dialog.warning.CannotBeUndone")}</div>
          <mwc-textfield class="red" id="leave-folder-name" label="${translate("data.folders.TypeFolderNameToLeave")}"
                         maxLength="64" placeholder="${get("maxLength.64chars")}"></mwc-textfield>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button unelevated fullwidth type="submit" id="leave-button" @click="${()=>this._leaveFolderWithCheck()}">
            ${translate("data.folders.Leave")}
          </mwc-button>
        </div>
      </backend-ai-dialog>

      <backend-ai-dialog id="info-folder-dialog" fixed backdrop>
        <span slot="title">${this.folderInfo.name}</span>
        <div slot="content" role="listbox" style="margin: 0;width:100%;">
          <div class="horizontal justified layout wrap" style="margin-top:15px;">
              <div class="vertical layout center info-indicator">
                <div class="big indicator">${this.folderInfo.host}</div>
                <span>${translate("data.folders.Location")}</span>
              </div>
            <div class="vertical layout center info-indicator">
              <div class="big indicator">
                ${this.folderInfo.numFiles<0?"many":this.folderInfo.numFiles}
              </div>
              <span>${translate("data.folders.NumberOfFiles")}</span>
            </div>
          </div>
          <mwc-list>
            <mwc-list-item twoline>
              <span><strong>ID</strong></span>
              <span class="monospace" slot="secondary">${this.folderInfo.id}</span>
            </mwc-list-item>
            ${this.folderInfo.is_owner?y`
              <mwc-list-item twoline>
                <span><strong>${translate("data.folders.Ownership")}</strong></span>
                <span slot="secondary">${translate("data.folders.DescYouAreFolderOwner")}</span>
              </mwc-list-item>
            `:y``}
            <mwc-list-item twoline>
              <span><strong>${translate("data.folders.Permission")}</strong></span>
              <div slot="secondary" class="horizontal layout">
              ${this.folderInfo.permission?y`
                ${this._hasPermission(this.folderInfo,"r")?y`
                    <lablup-shields app="" color="green"
                                    description="R" ui="flat"></lablup-shields>`:y``}
                ${this._hasPermission(this.folderInfo,"w")?y`
                    <lablup-shields app="" color="blue"
                                    description="W" ui="flat"></lablup-shields>`:y``}
                ${this._hasPermission(this.folderInfo,"d")?y`
                    <lablup-shields app="" color="red"
                                    description="D" ui="flat"></lablup-shields>`:y``}`:y``}
              </div>
            </mwc-list-item>
            ${this.enableStorageProxy?y`
              <mwc-list-item twoline>
                <span><strong>${translate("data.folders.Cloneable")}</strong></span>
                <span class="monospace" slot="secondary">
                    ${this.folderInfo.cloneable?y`
                    <mwc-icon class="cloneable" style="color:green;">check_circle</mwc-icon>
                    `:y`
                    <mwc-icon class="cloneable" style="color:red;">block</mwc-icon>
                    `}
                </span>
              </mwc-list-item>
            `:y``}
            ${this._checkFolderSupportSizeQuota(this.folderInfo.host)?y`
              <mwc-list-item twoline>
                <span><strong>${translate("data.folders.FolderUsage")}</strong></span>
                <span class="monospace" slot="secondary">
                  ${translate("data.folders.FolderUsing")}: ${this.folderInfo.used_bytes>=0?globalThis.backendaiutils._humanReadableFileSize(this.folderInfo.used_bytes):"Undefined"} /
                  ${translate("data.folders.FolderQuota")}: ${this.folderInfo.max_size>=0?globalThis.backendaiutils._humanReadableFileSize(this.folderInfo.max_size*this.quotaUnit.MiB):"Undefined"}
                  ${this.folderInfo.used_bytes>=0&&this.folderInfo.max_size>=0?y`
                    <vaadin-progress-bar value="${this.folderInfo.used_bytes/this.folderInfo.max_size/2**20}"></vaadin-progress-bar>
                  `:y``}
                </span>
              </mwc-list-item>
            `:y``}
          </mwc-list>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="folder-explorer-dialog" class="folder-explorer" narrowLayout>
        <span slot="title" style="margin-right:1rem;">${this.explorer.id}</span>
        <div slot="action" class="horizontal layout space-between folder-action-buttons center">
          <div class="flex"></div>
          ${this.isWritable?y`
            <mwc-button
                outlined
                class="multiple-action-buttons fg red"
                icon="delete"
                @click="${()=>this._openDeleteMultipleFileDialog()}"
                style="display:none;">
                <span>${translate("data.explorer.Delete")}</span>
            </mwc-button>
            <div id="add-btn-cover">
              <mwc-button
                  id="add-btn"
                  icon="cloud_upload"
                  ?disabled=${!this.isWritable}
                  @click="${e=>this._uploadFileBtnClick(e)}">
                  <span>${translate("data.explorer.UploadFiles")}</span>
              </mwc-button>
            </div>
            <div id="mkdir-cover">
              <mwc-button
                  id="mkdir"
                  class="tooltip"
                  icon="create_new_folder"
                  ?disabled=${!this.isWritable}
                  @click="${()=>this._mkdirDialog()}">
                  <span>${translate("data.explorer.NewFolder")}</span>
              </mwc-button>
            </div>
          `:y`
          <mwc-button
              id="readonly-btn"
              disabled>
            <span>${translate("data.explorer.ReadonlyFolder")}</span>
          </mwc-button>
          `}
          <div id="filebrowser-btn-cover">
            <mwc-button
                id="filebrowser-btn"
                @click="${()=>this._executeFileBrowser()}">
                <img
                  id="filebrowser-img"
                  alt="File Browser"
                  src="./resources/icons/filebrowser.svg"></img>
                <span>${translate("data.explorer.ExecuteFileBrowser")}</span>
            </mwc-button>
          </div>
        </div>
        <div slot="content">
            <div class="breadcrumb">
              ${this.explorer.breadcrumb?y`
                <ul>
                  ${this.explorer.breadcrumb.map((e=>y`
                    <li>
                      ${"."===e?y`
                        <mwc-icon-button
                          icon="folder_open" dest="${e}"
                          @click="${e=>this._gotoFolder(e)}"
                        ></mwc-icon-button>
                      `:y`
                        <a outlined class="goto" path="item" @click="${e=>this._gotoFolder(e)}" dest="${e}">${e}</a>
                      `}
                    </li>
                  `))}
                </ul>
              `:y``}
            </div>
            <div id="dropzone"><p>drag</p></div>
            <input type="file" id="fileInput" @change="${e=>this._uploadFileChange(e)}" hidden multiple>
            ${this.uploadFilesExist?y`
            <div class="horizontal layout start-justified">
              <mwc-button icon="cancel" id="cancel_upload" @click="${()=>this._cancelUpload()}">
                ${translate("data.explorer.StopUploading")}
              </mwc-button>
            </div>
          <vaadin-grid class="progress" theme="row-stripes compact" aria-label="uploadFiles" .items="${this.uploadFiles}" height-by-rows>
            <vaadin-grid-column width="100px" flex-grow="0" .renderer="${this._boundUploadListRenderer}"></vaadin-grid-column>
            <vaadin-grid-column .renderer="${this._boundUploadProgressRenderer}"></vaadin-grid-column>
          </vaadin-grid>`:y``}
          <vaadin-grid id="fileList-grid" class="explorer" theme="row-stripes compact" aria-label="Explorer" .items="${this.explorerFiles}">
            <vaadin-grid-selection-column auto-select></vaadin-grid-selection-column>
            <vaadin-grid-column width="40px" flex-grow="0" resizable header="#" .renderer="${this._boundIndexRenderer}">
            </vaadin-grid-column>
            <vaadin-grid-sort-column flex-grow="2" resizable header="${translate("data.explorer.Name")}" path="filename" .renderer="${this._boundFileNameRenderer}">
            </vaadin-grid-sort-column>
            <vaadin-grid-sort-column flex-grow="2" resizable header="${translate("data.explorer.Created")}" path="ctime" .renderer="${this._boundCreatedTimeRenderer}">
            </vaadin-grid-sort-column>
            <vaadin-grid-sort-column path="size" auto-width resizable header="${translate("data.explorer.Size")}">
            </vaadin-grid-sort-column>
            <vaadin-grid-column resizable auto-width header="${translate("data.explorer.Actions")}" .renderer="${this._boundControlFileListRenderer}">
            </vaadin-grid-column>
          </vaadin-grid>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="mkdir-dialog" fixed backdrop>
        <span slot="title">${translate("data.explorer.CreateANewFolder")}</span>
        <div slot="content">
          <mwc-textfield id="mkdir-name"
                         label="${translate("data.explorer.Foldername")}"
                         @change="${()=>this._validatePathName()}"
                         required
                         maxLength="255" placeholder="${get("maxLength.255chars")}"
                         validationMessage="${get("data.explorer.ValueRequired")}"></mwc-textfield>
          <br/>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout distancing">
          <mwc-button icon="rowing" unelevated fullwidth type="submit" id="mkdir-btn" @click="${e=>this._mkdir(e)}">
            ${translate("button.Create")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="share-folder-dialog" fixed backdrop persistent>
        <span slot="title">${translate("data.explorer.ShareFolder")}</span>
        <div slot="content" role="listbox" style="margin: 0;width:100%;">
          <div style="margin: 10px 0px">${translate("data.explorer.People")}</div>
          <div class="vertical layout flex" id="textfields">
            <div class="horizontal layout">
              <div style="flex-grow: 2">
                <mwc-textfield class="share-email" type="email" id="first-email"
                    label="${translate("data.explorer.EnterEmailAddress")}"
                    maxLength="64" placeholder="${get("maxLength.64chars")}">
                </mwc-textfield>
              </div>
              <div>
                <wl-button fab flat @click="${()=>this._addTextField()}">
                  <wl-icon>add</wl-icon>
                </wl-button>
                <wl-button fab flat @click="${()=>this._removeTextField()}">
                  <wl-icon>remove</wl-icon>
                </wl-button>
              </div>
            </div>
          </div>
          <div style="margin: 10px 0px">${translate("data.explorer.Permissions")}</div>
          <div style="display: flex; justify-content: space-evenly;">
            <mwc-formfield label="${translate("data.folders.View")}">
              <mwc-radio name="share-folder-permission" checked value="ro"></mwc-radio>
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
            @click=${e=>this._shareFolder(e)}>
            ${translate("button.Share")}
          </mwc-button>
        </div>
      </backend-ai-dialog>

      <backend-ai-dialog id="modify-permission-dialog" fixed backdrop>
        <span slot="title">${translate("data.explorer.ModifyPermissions")}</span>
        <div slot="content" role="listbox" style="margin: 0; padding: 10px;">
          <vaadin-grid theme="row-stripes column-borders compact" .items="${this.invitees}">
            <vaadin-grid-column
              width="30px"
              flex-grow="0"
              header="#"
              .renderer="${this._boundIndexRenderer}"
            ></vaadin-grid-column>
            <vaadin-grid-column header="${translate("data.explorer.InviteeEmail")}" .renderer="${this._boundInviteeInfoRenderer}">
            </vaadin-grid-column>
            <vaadin-grid-column header="${translate("data.explorer.Permission")}" .renderer="${this._boundPermissionRenderer}">
            </vaadin-grid-column>
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
          <mwc-textfield class="red" id="new-file-name" label="${translate("data.explorer.NewFileName")}"
          required @change="${()=>this._validateExistingFileName()}" auto-validate style="width:320px;"
          maxLength="255" placeholder="${get("maxLength.255chars")}" autoFocus></mwc-textfield>
          <div id="old-file-name" style="padding-left:15px;height:2.5em;"></div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button icon="edit" fullwidth type="button" id="rename-file-button" unelevated @click="${()=>this._compareFileExtension()}">
            ${translate("data.explorer.RenameAFile")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="delete-file-dialog" fixed backdrop>
        <span slot="title">${translate("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${translate("dialog.warning.CannotBeUndone")}
          ${translate("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button outlined @click="${e=>this._hideDialog(e)}">${translate("button.Cancel")}</mwc-button>
          <mwc-button raised @click="${e=>this._deleteFileWithCheck(e)}">${translate("button.Okay")}</mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="download-file-dialog" fixed backdrop>
        <span slot="title">${translate("data.explorer.DownloadFile")}</span>
        <div slot="content">
          <a href="${this.downloadURL}">
            <mwc-button outlined>${translate("data.explorer.TouchToDownload")}</mwc-button>
          </a>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout distancing">
          <mwc-button @click="${e=>this._hideDialog(e)}">${translate("button.Close")}</mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="file-extension-change-dialog" fixed backdrop>
        <span slot="title">${translate("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${translate("data.explorer.FileExtensionChanged")}</p>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout distancing">
          <mwc-button outlined fullwidth @click="${e=>this._keepFileExtension()}">
            ${"ko"!==globalThis.backendaioptions.get("language")?y`
                ${get("data.explorer.KeepFileExtension")+this.oldFileExtension}
              `:y`
                ${this.oldFileExtension+get("data.explorer.KeepFileExtension")}
              `}
          </mwc-button>
          <mwc-button unelevated fullwidth @click="${()=>this._renameFile()}">
            ${"ko"!==globalThis.backendaioptions.get("language")?y`
                ${this.newFileExtension?get("data.explorer.UseNewFileExtension")+this.newFileExtension:get("data.explorer.RemoveFileExtension")}
              `:y`
                ${this.newFileExtension?this.newFileExtension+get("data.explorer.UseNewFileExtension"):get("data.explorer.RemoveFileExtension")}
              `}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="filebrowser-notification-dialog" fixed backdrop narrowLayout>
        <span slot="title">${translate("dialog.title.Notice")}</span>
        <div slot="content" style="margin: 15px;">
          <span>${translate("data.explorer.ReadOnlyFolderOnFileBrowser")}</span>
        </div>
        <div slot="footer" class="flex horizontal layout center justified" style="margin: 15px 15px 15px 0px;">
          <div class="horizontal layout start-justified center">
            <mwc-checkbox @change="${e=>this._toggleShowFilebrowserNotification(e)}"></mwc-checkbox>
            <span style="font-size:0.8rem;">${get("dialog.hide.DonotShowThisAgain")}</span>
          </div>
          <mwc-button unelevated @click="${e=>this._hideDialog(e)}">${translate("button.Confirm")}</mwc-button>
        </div>
      </backend-ai-dialog>
    `}firstUpdated(){var e,t,i;this._addEventListenerDropZone(),this._mkdir=this._mkdir.bind(this),this.fileListGrid.addEventListener("selected-items-changed",(()=>{this._toggleFileListCheckbox()})),this.indicator=globalThis.lablupIndicator,this.notification=globalThis.lablupNotification;const o=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll("mwc-textfield");for(const e of Array.from(o))this._addInputValidator(e);"automount"===this.storageType?(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("vaadin-grid.folderlist")).style.height="calc(100vh - 230px)":(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("vaadin-grid.folderlist")).style.height="calc(100vh - 185px)",document.addEventListener("backend-ai-group-changed",(e=>this._refreshFolderList(!0,"group-changed"))),document.addEventListener("backend-ai-ui-changed",(e=>this._refreshFolderUI(e))),this._refreshFolderUI({detail:{"mini-ui":globalThis.mini_ui}}),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._getStorageProxyBackendInformation(),this._triggerFolderListChanged()}),!0):(this._getStorageProxyBackendInformation(),this._triggerFolderListChanged());const r=new URL(document.location).searchParams;console.log(r);const a=r.get("folder");console.log(a),a&&console.log(this.folders)}_modifySharedFolderPermissions(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll("#modify-permission-dialog wl-select"),i=Array.prototype.filter.call(t,((e,t)=>e.value!==this.invitees[t].perm)).map(((e,t)=>({perm:"kickout"===e.value?null:e.value,user:this.invitees[t].shared_to.uuid,vfolder:this.invitees[t].vfolder_id}))).map((e=>globalThis.backendaiclient.vfolder.modify_invitee_permission(e)));Promise.all(i).then((e=>{0===e.length?this.notification.text=get("data.permission.NoChanges"):this.notification.text=get("data.permission.PermissionModified"),this.notification.show(),this.modifyPermissionDialog.hide()}))}_checkProcessingStatus(e){return["performing","cloning","deleting","mounted"].includes(e)}permissionRenderer(e,t,i){var o,r;A(y`
      <div class="vertical layout">
        <wl-select label="${translate("data.folders.SelectPermission")}">
          <option ?selected=${"ro"===i.item.perm} value="ro">${translate("data.folders.View")}</option>
          <option ?selected=${"rw"===i.item.perm} value="rw">${translate("data.folders.Edit")}</option>
          <option ?selected=${"wd"===i.item.perm} value="wd">${translate("data.folders.EditDelete")}</option>
          <option value="kickout">${translate("data.folders.KickOut")}</option>
        </wl-select>
      </div>`,e),null===(r=null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("wl-select"))||void 0===r||r.requestUpdate().then((()=>{A(y`
        <div class="vertical layout">
          <wl-select label="${translate("data.folders.SelectPermission")}">
            <option ?selected=${"ro"===i.item.perm} value="ro">${translate("data.folders.View")}</option>
            <option ?selected=${"rw"===i.item.perm} value="rw">${translate("data.folders.Edit")}</option>
            <option ?selected=${"wd"===i.item.perm} value="wd">${translate("data.folders.EditDelete")}</option>
            <option value="kickout">${translate("data.folders.KickOut")}</option>
          </wl-select>
        </div>`,e)}))}folderListRenderer(e,t,i){A(y`
        <div
          id="controls"
          class="layout flex horizontal start-justified center wrap"
          folder-id="${i.item.id}"
          folder-name="${i.item.name}"
          folder-type="${i.item.type}"
        >
          ${this._hasPermission(i.item,"r")?y`
              <mwc-icon-button
                class="fg blue controls-running"
                icon="folder_open"
                title=${translate("data.folders.OpenAFolder")}
                @click="${e=>this._folderExplorer(i)}"
                ?disabled="${this._checkProcessingStatus(i.item.status)}"
                .folder-id="${i.item.name}"></mwc-icon-button>
            `:y``}
          <div @click="${e=>this._folderExplorer(i)}"
               .folder-id="${i.item.name}" style="cursor:pointer;">${i.item.name}</div>
        </div>
      `,e)}quotaRenderer(e,t,i){let o="-";this._checkFolderSupportSizeQuota(i.item.host)&&i.item.max_size&&(o=globalThis.backendaiutils._humanReadableFileSize(i.item.max_size*this.quotaUnit.MiB)),A(y`
        <div class="horizontal layout center center-justified">${o}</div>
      `,e)}uploadListRenderer(e,t,i){A(y`
      <vaadin-item class="progress-item">
        <div>
          ${i.item.complete?y`
            <wl-icon>check</wl-icon>
          `:y``}
        </div>
      </vaadin-item>
      `,e)}uploadProgressRenderer(e,t,i){A(y`
      <vaadin-item>
        <span>${i.item.name}</span>
        ${i.item.complete?y``:y`
        <div>
            <vaadin-progress-bar value="${i.item.progress}"></vaadin-progress-bar>
          </div>
          <div>
            <span>${i.item.caption}</span>
          </div>
        `}
      </vaadin-item>
      `,e)}inviteeInfoRenderer(e,t,i){A(y`
        <div>${i.item.shared_to.email}</div>
      `,e)}iDRenderer(e,t,i){A(y`
      <div class="layout vertical">
        <span class="indicator monospace">${i.item.id}</span>
      </div>
      `,e)}statusRenderer(e,t,i){let o;switch(i.item.status){case"ready":o="green";break;case"performing":case"cloning":case"mounted":o="blue";break;case"deleting":o="yellow";break;default:o="grey"}A(y`
        <lablup-shields app="" color="${o}"
                        description="${i.item.status}" ui="flat"></lablup-shields>
      `,e)}_addTextField(){var e,t;const i=document.createElement("mwc-textfield");i.label=get("data.explorer.EnterEmailAddress"),i.type="email",i.className="share-email",i.style.width="auto",i.style.marginRight="83px",null===(t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#textfields"))||void 0===t||t.appendChild(i)}_removeTextField(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#textfields");t.children.length>1&&t.lastChild&&t.removeChild(t.lastChild)}indexRenderer(e,t,i){A(y`${this._indexFrom1(i.index)}`,e)}controlFolderListRenderer(e,t,i){A(y`
        <div
          id="controls"
          class="layout flex center wrap"
          folder-id="${i.item.id}"
          folder-name="${i.item.name}"
          folder-type="${i.item.type}"
        >
          <mwc-icon-button
            class="fg green controls-running"
            icon="info"
            title=${translate("data.folders.FolderInfo")}
            @click="${e=>this._infoFolder(e)}"
            ?disabled="${this._checkProcessingStatus(i.item.status)}"
          ></mwc-icon-button>
          <!--${this._hasPermission(i.item,"r")&&this.enableStorageProxy?y`
        <mwc-icon-button
          class="fg blue controls-running"
          icon="content_copy"
          disabled
          @click="${()=>{this._requestCloneFolder(i.item)}}"
          ></mwc-icon-button>
      `:y``}-->
      ${i.item.is_owner?y`
          <mwc-icon-button
            class="fg ${"user"==i.item.type?"blue":"green"} controls-running"
            icon="share"
            title=${translate("data.explorer.ShareFolder")}
            @click="${e=>this._shareFolderDialog(e)}"
            ?disabled="${this._checkProcessingStatus(i.item.status)}"
          ></mwc-icon-button>
          <mwc-icon-button
            class="fg cyan controls-running"
            icon="perm_identity"
            title=${translate("data.explorer.ModifyPermissions")}
            @click=${e=>this._modifyPermissionDialog(i.item.id)}
            ?disabled="${this._checkProcessingStatus(i.item.status)}"
          ></mwc-icon-button>
          <mwc-icon-button
            class="fg ${"user"==i.item.type?"blue":"green"} controls-running"
            icon="create"
            title=${translate("data.folders.Rename")}
            @click="${e=>this._renameFolderDialog(e)}"
            ?disabled="${this._checkProcessingStatus(i.item.status)}"
          ></mwc-icon-button>
          <mwc-icon-button
            class="fg blue controls-running"
            icon="settings"
            title=${translate("data.folders.FolderOptionUpdate")}
            @click="${e=>this._modifyFolderOptionDialog(e)}"
            ?disabled="${this._checkProcessingStatus(i.item.status)}"
          ></mwc-icon-button>`:y``}
      ${i.item.is_owner||this._hasPermission(i.item,"d")||"group"===i.item.type&&this.is_admin?y`
          <mwc-icon-button
            class="fg red controls-running"
            icon="delete"
            title=${translate("data.folders.Delete")}
            @click="${e=>this._deleteFolderDialog(e)}"
            ?disabled="${this._checkProcessingStatus(i.item.status)}"
          ></mwc-icon-button>`:y``}
      ${i.item.is_owner||"user"!=i.item.type?y``:y`
          <mwc-icon-button
            class="fg red controls-running"
            icon="remove_circle"
            @click="${e=>this._leaveInvitedFolderDialog(e)}"
            ?disabled="${this._checkProcessingStatus(i.item.status)}"
          ></mwc-icon-button>`}
        </div>
       `,e)}controlFileListRenderer(e,t,i){A(y`
        <div class="flex layout wrap">
          ${this._isDir(i.item)?y`
            <mwc-icon-button id="download-btn" class="tiny fg blue" icon="cloud_download"
                filename="${i.item.filename}" @click="${e=>this._downloadFile(e,!0)}"></mwc-icon-button>
          `:y`
            <mwc-icon-button id="download-btn" class="tiny fg blue" icon="cloud_download"
                filename="${i.item.filename}" @click="${e=>this._downloadFile(e)}"></mwc-icon-button>
          `}
          <mwc-icon-button id="rename-btn" ?disabled="${!this.isWritable}" class="tiny fg green" icon="edit" required
              filename="${i.item.filename}" @click="${e=>this._openRenameFileDialog(e,this._isDir(i.item))}"></mwc-icon-button>
          <mwc-icon-button id="delete-btn" ?disabled="${!this.isWritable}" class="tiny fg red" icon="delete_forever"
              filename="${i.item.filename}" @click="${e=>this._openDeleteFileDialog(e)}"></mwc-icon-button>
        </div>
       `,e)}fileNameRenderer(e,t,i){A(y`
        ${this._isDir(i.item)?y`
          <div class="indicator horizontal center layout" name="${i.item.filename}">
            <mwc-icon-button class="fg controls-running" icon="folder_open" name="${i.item.filename}"
                               @click="${e=>this._enqueueFolder(e)}"></mwc-icon-button>
            ${i.item.filename}
          </div>
       `:y`
          <div class="indicator horizontal center layout">
            <mwc-icon-button class="fg controls-running" icon="insert_drive_file"></mwc-icon-button>
            ${i.item.filename}
          </div>
       `}
      `,e)}permissionViewRenderer(e,t,i){A(y`
        <div class="horizontal center-justified wrap layout">
        ${this._hasPermission(i.item,"r")?y`
            <lablup-shields app="" color="green"
                            description="R" ui="flat"></lablup-shields>`:y``}
        ${this._hasPermission(i.item,"w")?y`
            <lablup-shields app="" color="blue"
                            description="W" ui="flat"></lablup-shields>`:y``}
        ${this._hasPermission(i.item,"d")?y`
            <lablup-shields app="" color="red"
                            description="D" ui="flat"></lablup-shields>`:y``}
        </div>
      `,e)}OwnerRenderer(e,t,i){A(y`
        ${i.item.is_owner?y`
          <div class="horizontal center-justified center layout" style="pointer-events: none;">
            <mwc-icon-button class="fg green" icon="done"></mwc-icon-button>
          </div>`:y``}
      `,e)}CloneableRenderer(e,t,i){A(y`
        ${i.item.cloneable?y`
          <div class="horizontal center-justified center layout">
            <mwc-icon-button class="fg green" icon="done"></mwc-icon-button>
          </div>`:y``}
      `,e)}createdTimeRenderer(e,t,i){A(y`
        <div class="layout vertical">
            <span>${this._humanReadableTime(i.item.ctime)}</span>
        </div>
      `,e)}typeRenderer(e,t,i){A(y`
        <div class="layout vertical center-justified">
        ${"user"==i.item.type?y`<wl-icon>person</wl-icon>`:y`<wl-icon class="fg green">group</wl-icon>`}
        </div>
      `,e)}async _getStorageProxyBackendInformation(){const e=await globalThis.backendaiclient.vfolder.list_hosts();this.storageProxyInfo=e.volume_info||{}}_checkFolderSupportSizeQuota(e){var t;if(!e)return!1;const i=null===(t=this.storageProxyInfo[e])||void 0===t?void 0:t.backend;return!!this.quotaSupportStorageBackends.includes(i)}refreshFolderList(){return this._triggerFolderListChanged(),this._refreshFolderList(!0,"refreshFolderList")}_refreshFolderList(e=!1,t="unknown"){var i;if(this._folderRefreshing||!this.active)return;if(Date.now()-this.lastQueryTime<1e3)return;this._folderRefreshing=!0,this.lastQueryTime=Date.now(),this.listCondition="loading",null===(i=this._listStatus)||void 0===i||i.show(),this._getMaxSize();let o=null;o=globalThis.backendaiclient.current_group_id(),globalThis.backendaiclient.vfolder.list(o).then((e=>{var t;const i=e.filter((e=>"general"!==this.storageType||e.name.startsWith(".")?"automount"===this.storageType&&e.name.startsWith(".")?e:void 0:e));this.folders=i,0==this.folders.length?this.listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide(),this._folderRefreshing=!1})).catch((()=>{this._folderRefreshing=!1})),globalThis.backendaiclient.vfolder.list_hosts().then((t=>{this.active&&!e&&setTimeout((()=>{this._refreshFolderList(!1,"loop")}),3e4)}))}_refreshFolderUI(e){Object.prototype.hasOwnProperty.call(e.detail,"mini-ui")&&!0===e.detail["mini-ui"]?this.folderExplorerDialog.classList.add("mini_ui"):this.folderExplorerDialog.classList.remove("mini_ui")}async _checkFilebrowserSupported(){const e=(await globalThis.backendaiclient.image.list(["name","tag","registry","digest","installed","labels { key value }","resource_limits { key min max }"],!1,!0)).images;this.filebrowserSupportedImages=e.filter((e=>e.installed&&e.labels.find((e=>"ai.backend.service-ports"===e.key&&e.value.toLowerCase().includes("filebrowser")))))}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.is_admin=globalThis.backendaiclient.is_admin,this.enableStorageProxy=globalThis.backendaiclient.supports("storage-proxy"),this.authenticated=!0,this._APIMajorVersion=globalThis.backendaiclient.APIMajorVersion,this._maxFileUploadSize=globalThis.backendaiclient._config.maxFileUploadSize,this._checkFilebrowserSupported(),this._refreshFolderList(!1,"viewStatechanged")}),!0):(this.is_admin=globalThis.backendaiclient.is_admin,this.enableStorageProxy=globalThis.backendaiclient.supports("storage-proxy"),this.authenticated=!0,this._APIMajorVersion=globalThis.backendaiclient.APIMajorVersion,this._maxFileUploadSize=globalThis.backendaiclient._config.maxFileUploadSize,this._checkFilebrowserSupported(),this._refreshFolderList(!1,"viewStatechanged")))}_folderExplorerDialog(){this.openDialog("folder-explorer-dialog")}_mkdirDialog(){this.mkdirNameInput.value="",this.openDialog("mkdir-dialog")}openDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).show()}closeDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).hide()}_indexFrom1(e){return e+1}_hasPermission(e,t){return!!e.permission.includes(t)||!(!e.permission.includes("w")||"r"!==t)}_getControlName(e){return e.target.closest("#controls").getAttribute("folder-name")}_getControlId(e){return e.target.closest("#controls").getAttribute("folder-id")}_getControlType(e){return e.target.closest("#controls").getAttribute("folder-type")}_infoFolder(e){const t=this._getControlName(e);globalThis.backendaiclient.vfolder.info(t).then((e=>{this.folderInfo=e,this.openDialog("info-folder-dialog")})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=BackendAIPainKiller.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_modifyFolderOptionDialog(e){globalThis.backendaiclient.vfolder.name=this._getControlName(e);globalThis.backendaiclient.vfolder.info(globalThis.backendaiclient.vfolder.name).then((e=>{this.folderInfo=e;const t=this.folderInfo.permission;let i=Object.keys(this.permissions).indexOf(t);i=i>0?i:0,this.updateFolderPermissionSelect.select(i),this.updateFolderCloneableSwitch&&(this.updateFolderCloneableSwitch.selected=this.folderInfo.cloneable),this._checkFolderSupportSizeQuota(this.folderInfo.host)&&([this.quota.value,this.quota.unit]=globalThis.backendaiutils._humanReadableFileSize(this.folderInfo.max_size*this.quotaUnit.MiB).split(" "),this.modifyFolderQuotaInput.value=this.quota.value.toString(),this.modifyFolderQuotaUnitSelect.value="Bytes"==this.quota.unit?"MiB":this.quota.unit),this.openDialog("modify-folder-dialog")})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=BackendAIPainKiller.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}async _updateFolder(){var e;let t=!1,i=!1;const o={};if(this.updateFolderPermissionSelect){let t=this.updateFolderPermissionSelect.value;t=null!==(e=Object.keys(this.permissions).find((e=>this.permissions[e]===t)))&&void 0!==e?e:"",t&&this.folderInfo.permission!==t&&(o.permission=t)}this.updateFolderCloneableSwitch&&(i=this.updateFolderCloneableSwitch.selected,o.cloneable=i);const r=[];if(Object.keys(o).length>0){const e=globalThis.backendaiclient.vfolder.update_folder(o,globalThis.backendaiclient.vfolder.name);r.push(e)}if(this._checkFolderSupportSizeQuota(this.folderInfo.host)){const e=this.modifyFolderQuotaInput.value?BigInt(Number(this.modifyFolderQuotaInput.value)*this.quotaUnit[this.modifyFolderQuotaUnitSelect.value]).toString():"0";if(this.quota.value!=Number(this.modifyFolderQuotaInput.value)||this.quota.unit!=this.modifyFolderQuotaUnitSelect.value){const t=globalThis.backendaiclient.vfolder.set_quota(this.folderInfo.host,this.folderInfo.id,e.toString());r.push(t)}}r.length>0&&await Promise.all(r).then((e=>{this.notification.text=get("data.folders.FolderUpdated"),this.notification.show(),this._refreshFolderList(!0,"updateFolder")})).catch((e=>{console.log(e),e&&e.message&&(t=!0,this.notification.text=BackendAIPainKiller.relieve(e.message),this.notification.show(!0,e))})),t||this.closeDialog("modify-folder-dialog")}async _updateFolderName(){globalThis.backendaiclient.vfolder.name=this.renameFolderName;const e=this.newFolderNameInput.value;if(this.newFolderNameInput.reportValidity(),e){if(!this.newFolderNameInput.checkValidity())return;try{await globalThis.backendaiclient.vfolder.rename(e),this.notification.text=get("data.folders.FolderRenamed"),this.notification.show(),this._refreshFolderList(!0,"updateFolder"),this.closeDialog("modify-folder-name-dialog")}catch(e){this.notification.text=BackendAIPainKiller.relieve(e.message),this.notification.show(!0,e)}}}_renameFolderDialog(e){this.renameFolderName=this._getControlName(e),this.newFolderNameInput.value="",this.openDialog("modify-folder-name-dialog")}async _deleteFolderDialog(e){this.deleteFolderName=this._getControlName(e),this.deleteFolderNameInput.value="",this.openDialog("delete-folder-dialog")}_deleteFolderWithCheck(){if(this.deleteFolderNameInput.value!==this.deleteFolderName)return this.notification.text=get("data.folders.FolderNameMismatched"),void this.notification.show();this.closeDialog("delete-folder-dialog"),this._deleteFolder(this.deleteFolderName)}_deleteFolder(e){globalThis.backendaiclient.vfolder.delete(e).then((e=>{e.msg?(this.notification.text=get("data.folders.CannotDeleteFolder"),this.notification.show(!0)):(this.notification.text=get("data.folders.FolderDeleted"),this.notification.show(),this.refreshFolderList(),this._triggerFolderListChanged())})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=BackendAIPainKiller.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}async _checkVfolderMounted(e=""){}_requestCloneFolder(e){}_leaveInvitedFolderDialog(e){this.leaveFolderName=this._getControlName(e),this.leaveFolderNameInput.value="",this.openDialog("leave-folder-dialog")}_leaveFolderWithCheck(){if(this.leaveFolderNameInput.value!==this.leaveFolderName)return this.notification.text=get("data.folders.FolderNameMismatched"),void this.notification.show();this.closeDialog("leave-folder-dialog"),this._leaveFolder(this.leaveFolderName)}_leaveFolder(e){globalThis.backendaiclient.vfolder.leave_invited(e).then((e=>{this.notification.text=get("data.folders.FolderDisconnected"),this.notification.show(),this.refreshFolderList(),this._triggerFolderListChanged()})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=BackendAIPainKiller.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}async _getMaxSize(){const e=globalThis.backendaiclient._config.accessKey,t=(await globalThis.backendaiclient.keypair.info(e,["resource_policy"])).keypair.resource_policy,i=(await globalThis.backendaiclient.resourcePolicy.get(t,["max_vfolder_count","max_vfolder_size"])).keypair_resource_policy.max_vfolder_size;[this.maxSize.value,this.maxSize.unit]=globalThis.backendaiutils._humanReadableFileSize(i).split(" "),["Bytes","KiB","MiB"].includes(this.maxSize.unit)?(this.maxSize.value=this.maxSize.value<1?1:Math.round(this.maxSize.value),this.maxSize.unit="MiB"):this.maxSize.value=Math.round(10*this.maxSize.value)/10}_triggerFolderListChanged(){const e=new CustomEvent("backend-ai-folder-list-changed");document.dispatchEvent(e)}_validateExistingFileName(){this.newFileNameInput.validityTransform=(e,t)=>{if(t.valid){const e=/[`~!@#$%^&*()|+=?;:'",<>{}[\]\\/]/gi;let t;return this.newFileNameInput.value===this.renameFileDialog.querySelector("#old-file-name").textContent?(this.newFileNameInput.validationMessage=get("data.EnterDifferentValue"),t=!1,{valid:t,customError:!t}):(t=!0,t=!e.test(this.newFileNameInput.value),t||(this.newFileNameInput.validationMessage=get("data.Allowslettersnumbersand-_dot")),{valid:t,customError:!t})}return t.valueMissing?(this.newFileNameInput.validationMessage=get("data.FileandFoldernameRequired"),{valid:t.valid,customError:!t.valid}):(this.newFileNameInput.validationMessage=get("data.Allowslettersnumbersand-_dot"),{valid:t.valid,customError:!t.valid})}}_validateFolderName(e=!1){var t;const i=e?this.newFolderNameInput:null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#add-folder-name");i.validityTransform=(t,o)=>{if(o.valid){let t;const o=/[`~!@#$%^&*()|+=?;:'",<>{}[\]\\/\s]/gi;if(e){if(i.value===this.renameFolderName)return i.validationMessage=get("data.EnterDifferentValue"),t=!1,{valid:t,customError:!t};t=!0}return t=!o.test(i.value),t||(i.validationMessage=get("data.Allowslettersnumbersand-_dot")),{valid:t,customError:!t}}return o.valueMissing?(i.validationMessage=get("data.FolderNameRequired"),{valid:o.valid,customError:!o.valid}):(i.validationMessage=get("data.Allowslettersnumbersand-_dot"),{valid:o.valid,customError:!o.valid})}}async _clearExplorer(e=this.explorer.breadcrumb.join("/"),t=this.explorer.id,i=!1){const o=await globalThis.backendaiclient.vfolder.list_files(e,t);if(this.fileListGrid.selectedItems=[],this._APIMajorVersion<6)this.explorer.files=JSON.parse(o.files);else{const e=JSON.parse(o.files);e.forEach(((e,t)=>{let i="FILE";if(e.filename===o.items[t].name)i=o.items[t].type;else for(let t=0;t<o.items.length;t++)if(e.filename===o.items[t].name){i=o.items[t].type;break}e.type=i})),this.explorer.files=e}this.explorerFiles=this.explorer.files,i&&(0===this.filebrowserSupportedImages.length&&await this._checkFilebrowserSupported(),this._toggleFilebrowserButton(),this.openDialog("folder-explorer-dialog"))}_toggleFilebrowserButton(){var e,t;const i=!!(this.filebrowserSupportedImages.length>0&&this._isResourceEnough()),o=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#filebrowser-img"),r=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#filebrowser-btn");if(o&&r){r.disabled=!i;const e=i?"":"apply-grayscale";o.setAttribute("class",e)}}_folderExplorer(e){const t=e.item.name,i=this._hasPermission(e.item,"w")||e.item.is_owner||"group"===e.item.type&&this.is_admin,o={id:t,breadcrumb:["."]},r=new URLSearchParams;r.set("folder",t),window.history.replaceState({},"",`${location.pathname}?${r}`),this.isWritable=i,this.explorer=o,this._clearExplorer(o.breadcrumb.join("/"),o.id,!0)}_enqueueFolder(e){const t=e.target;t.setAttribute("disabled","true");const i=e.target.getAttribute("name");this.explorer.breadcrumb.push(i),this._clearExplorer().then((e=>{t.removeAttribute("disabled")}))}_gotoFolder(e){const t=e.target.getAttribute("dest");let i=this.explorer.breadcrumb;const o=i.indexOf(t);-1!==o&&(i=i.slice(0,o+1),this.explorer.breadcrumb=i,this._clearExplorer(i.join("/"),this.explorer.id,!1))}_mkdir(e){const t=this.mkdirNameInput.value,i=this.explorer;if(this.mkdirNameInput.reportValidity(),this.mkdirNameInput.checkValidity()){globalThis.backendaiclient.vfolder.mkdir([...i.breadcrumb,t].join("/"),i.id).catch((e=>{e&e.message?(this.notification.text=BackendAIPainKiller.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=BackendAIPainKiller.relieve(e.title),this.notification.show(!0,e))})).then((e=>{this.closeDialog("mkdir-dialog"),this._clearExplorer()}))}}_isDir(e){return this._APIMajorVersion<6?e.mode.startsWith("d"):"DIRECTORY"===e.type}_byteToMB(e){return Math.floor(e/1e6)}_addEventListenerDropZone(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#dropzone");t.addEventListener("dragleave",(()=>{t.style.display="none"})),this.folderExplorerDialog.addEventListener("dragover",(e=>(e.stopPropagation(),e.preventDefault(),!this.isWritable||(e.dataTransfer.dropEffect="copy",t.style.display="flex",!1)))),this.folderExplorerDialog.addEventListener("drop",(e=>{let i=!1;if(e.stopPropagation(),e.preventDefault(),t.style.display="none",this.isWritable){for(let t=0;t<e.dataTransfer.files.length;t++)if(e.dataTransfer.items[t].webkitGetAsEntry().isFile){const i=e.dataTransfer.files[t];if(this._maxFileUploadSize>0&&i.size>this._maxFileUploadSize)return this.notification.text=get("data.explorer.FileUploadSizeLimit")+` (${globalThis.backendaiutils._humanReadableFileSize(this._maxFileUploadSize)})`,void this.notification.show();if(this.explorerFiles.find((e=>e.filename===i.name))){window.confirm(`${get("data.explorer.FileAlreadyExists")}\n${i.name}\n${get("data.explorer.DoYouWantToOverwrite")}`)&&(i.progress=0,i.caption="",i.error=!1,i.complete=!1,this.uploadFiles.push(i))}else i.progress=0,i.caption="",i.error=!1,i.complete=!1,this.uploadFiles.push(i)}else i||(this.filebrowserSupportedImages.length>0?(this.notification.text=get("data.explorer.ClickFilebrowserButton"),this.notification.show()):(this.notification.text=get("data.explorer.NoImagesSupportingFileBrowser"),this.notification.show())),i=!0;for(let e=0;e<this.uploadFiles.length;e++)this.fileUpload(this.uploadFiles[e]),this._clearExplorer()}else this.notification.text=get("data.explorer.WritePermissionRequiredInUploadFiles"),this.notification.show()}))}_uploadFileBtnClick(e){var t;const i=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#fileInput");if(i&&document.createEvent){const e=document.createEvent("MouseEvents");e.initEvent("click",!0,!1),i.dispatchEvent(e)}}_uploadFileChange(e){var t;const i=e.target.files.length;for(let t=0;t<i;t++){const i=e.target.files[t];let o="";const r="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";for(let e=0;e<5;e++)o+=r.charAt(Math.floor(Math.random()*r.length));if(this._maxFileUploadSize>0&&i.size>this._maxFileUploadSize)return this.notification.text=get("data.explorer.FileUploadSizeLimit")+` (${globalThis.backendaiutils._humanReadableFileSize(this._maxFileUploadSize)})`,void this.notification.show();if(this.explorerFiles.find((e=>e.filename===i.name))){window.confirm(`${get("data.explorer.FileAlreadyExists")}\n${i.name}\n${get("data.explorer.DoYouWantToOverwrite")}`)&&(i.id=o,i.progress=0,i.caption="",i.error=!1,i.complete=!1,this.uploadFiles.push(i))}else i.id=o,i.progress=0,i.caption="",i.error=!1,i.complete=!1,this.uploadFiles.push(i)}for(let e=0;e<this.uploadFiles.length;e++)this.fileUpload(this.uploadFiles[e]);(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#fileInput")).value=""}runFileUploadQueue(e=null){let t;null!==e&&this.fileUploadQueue.push(e);for(let e=this.fileUploadCount;e<this.concurrentFileUploadLimit;e++)this.fileUploadQueue.length>0&&(t=this.fileUploadQueue.shift(),this.fileUploadCount=this.fileUploadCount+1,t.start())}fileUpload(e){this._uploadFlag=!0,this.uploadFilesExist=this.uploadFiles.length>0;const t=this.explorer.breadcrumb.concat(e.name).join("/");globalThis.backendaiclient.vfolder.create_upload_session(t,e,this.explorer.id).then((i=>{const o=(new Date).getTime(),r=new tus$1.Upload(e,{endpoint:i,retryDelays:[0,3e3,5e3,1e4,2e4],uploadUrl:i,chunkSize:15728640,metadata:{filename:t,filetype:e.type},onError:e=>{console.log("Failed because: "+e),this.fileUploadCount=this.fileUploadCount-1,this.runFileUploadQueue()},onProgress:(t,i)=>{if(!this._uploadFlag)return r.abort(),this.uploadFiles[this.uploadFiles.indexOf(e)].caption="Canceling...",this.uploadFiles=this.uploadFiles.slice(),void setTimeout((()=>{this.uploadFiles=[],this.uploadFilesExist=!1,this.fileUploadCount=this.fileUploadCount-1}),1e3);const a=(new Date).getTime(),n=(t/1048576/((a-o)/1e3)).toFixed(1)+"MB/s",l=Math.floor((i-t)/(t/(a-o)*1e3));let s=get("data.explorer.LessThan10Sec");if(l>=86400)s=get("data.explorer.MoreThanADay");else if(l>10){s=`${Math.floor(l/3600)}:${Math.floor(l%3600/60)}:${l%60}`}const d=(t/i*100).toFixed(1);this.uploadFiles[this.uploadFiles.indexOf(e)].progress=t/i,this.uploadFiles[this.uploadFiles.indexOf(e)].caption=`${d}% / Time left : ${s} / Speed : ${n}`,this.uploadFiles=this.uploadFiles.slice()},onSuccess:()=>{this._clearExplorer(),this.uploadFiles[this.uploadFiles.indexOf(e)].complete=!0,this.uploadFiles=this.uploadFiles.slice(),setTimeout((()=>{this.uploadFiles.splice(this.uploadFiles.indexOf(e),1),this.uploadFilesExist=this.uploadFiles.length>0,this.uploadFiles=this.uploadFiles.slice(),this.fileUploadCount=this.fileUploadCount-1,this.runFileUploadQueue()}),1e3)}});this.runFileUploadQueue(r)}))}_cancelUpload(){this._uploadFlag=!1}_downloadFile(e,t=!1){const i=e.target.getAttribute("filename"),o=this.explorer.breadcrumb.concat(i).join("/");globalThis.backendaiclient.vfolder.request_download_token(o,this.explorer.id,t).then((e=>{const o=e.token;let r;if(r=this._APIMajorVersion<6?globalThis.backendaiclient.vfolder.get_download_url_with_token(o):`${e.url}?token=${e.token}&archive=${t}`,globalThis.iOSSafari)this.downloadURL=r,this.downloadFileDialog.show(),URL.revokeObjectURL(r);else{const e=document.createElement("a");e.style.display="none",e.addEventListener("click",(function(e){e.stopPropagation()})),e.href=r,e.download=i,document.body.appendChild(e),e.click(),document.body.removeChild(e),URL.revokeObjectURL(r)}}))}_compareFileExtension(){var e;const t=this.newFileNameInput.value,i=null!==(e=this.renameFileDialog.querySelector("#old-file-name").textContent)&&void 0!==e?e:"",o=/\.([0-9a-z]+)$/i,r=t.match(o),a=i.match(o);t.includes(".")&&r?this.newFileExtension=r[1].toLowerCase():this.newFileExtension="",i.includes(".")&&a?this.oldFileExtension=a[1].toLowerCase():this.oldFileExtension="",t?this.newFileExtension!==this.oldFileExtension?this.fileExtensionChangeDialog.show():this.oldFileExtension?this._keepFileExtension():this._renameFile():this._renameFile()}_keepFileExtension(){let e=this.newFileNameInput.value;e=this.newFileExtension?e.replace(new RegExp(this.newFileExtension+"$"),this.oldFileExtension):e+"."+this.oldFileExtension,this.newFileNameInput.value=e,this._renameFile()}_executeFileBrowser(){if(this._isResourceEnough())if(this.filebrowserSupportedImages.length>0){const e=localStorage.getItem("backendaiwebui.filebrowserNotification");null!=e&&"true"!==e||this.isWritable||this.fileBrowserNotificationDialog.show(),this._launchSession(),this._toggleFilebrowserButton()}else this.notification.text=get("data.explorer.NoImagesSupportingFileBrowser"),this.notification.show();else this.notification.text=get("data.explorer.NotEnoughResourceForFileBrowserSession"),this.notification.show()}_toggleShowFilebrowserNotification(e){const t=e.target;if(t){const e=(!t.checked).toString();localStorage.setItem("backendaiwebui.filebrowserNotification",e)}}async _launchSession(){let e;const t={},i=this.filebrowserSupportedImages.filter((e=>e.name.toLowerCase().includes("filebrowser")&&e.installed))[0],o=i.registry+"/"+i.name+":"+i.tag;t.mounts=[this.explorer.id],t.cpu=1,t.mem=this.minimumResource.mem+"g",t.domain=globalThis.backendaiclient._config.domainName,t.group_name=globalThis.backendaiclient.current_group;const r=await this.indicator.start("indeterminate");return globalThis.backendaiclient.get_resource_slots().then((e=>(r.set(200,get("data.explorer.ExecutingFileBrowser")),globalThis.backendaiclient.createIfNotExists(o,null,t,1e4,void 0)))).then((async t=>{const i=t.servicePorts;e={"session-uuid":t.sessionId,"session-name":t.sessionName,"access-key":"",runtime:"filebrowser",arguments:{"--root":"/home/work/"+this.explorer.id}},i.length>0&&i.filter((e=>"filebrowser"===e.name)).length>0&&globalThis.appLauncher.showLauncher(e),this.folderExplorerDialog.open&&this.closeDialog("folder-explorer-dialog"),r.end(1e3)})).catch((e=>{this.notification.text=BackendAIPainKiller.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e),r.end(1e3)}))}_openRenameFileDialog(e,t=!1){const i=e.target.getAttribute("filename");this.renameFileDialog.querySelector("#old-file-name").textContent=i,this.newFileNameInput.value=i,this.renameFileDialog.filename=i,this.renameFileDialog.show(),this.is_dir=t,this.newFileNameInput.addEventListener("focus",(e=>{const t=i.replace(/\.([0-9a-z]+)$/i,"").length;this.newFileNameInput.setSelectionRange(0,t)})),this.newFileNameInput.focus()}_renameFile(){const e=this.renameFileDialog.filename,t=this.explorer.breadcrumb.concat(e).join("/"),i=this.newFileNameInput.value;if(this.fileExtensionChangeDialog.hide(),this.newFileNameInput.reportValidity(),this.newFileNameInput.checkValidity()){if(e===i)return this.newFileNameInput.focus(),this.notification.text=get("data.folders.SameFileName"),void this.notification.show();globalThis.backendaiclient.vfolder.rename_file(t,i,this.explorer.id,this.is_dir).then((e=>{this.notification.text=get("data.folders.FileRenamed"),this.notification.show(),this._clearExplorer(),this.renameFileDialog.hide()})).catch((e=>{console.error(e),e&&e.message&&(this.notification.text=e.title,this.notification.detail=e.message,this.notification.show(!0,e))}))}}_openDeleteFileDialog(e){const t=e.target.getAttribute("filename");this.deleteFileDialog.filename=t,this.deleteFileDialog.files=[],this.deleteFileDialog.show()}_openDeleteMultipleFileDialog(e){this.deleteFileDialog.files=this.fileListGrid.selectedItems,this.deleteFileDialog.filename="",this.deleteFileDialog.show()}_deleteFileWithCheck(e){const t=this.deleteFileDialog.files;if(t.length>0){const e=[];t.forEach((t=>{const i=this.explorer.breadcrumb.concat(t.filename).join("/");e.push(i)}));globalThis.backendaiclient.vfolder.delete_files(e,!0,this.explorer.id).then((e=>{this.notification.text=1==t.length?get("data.folders.FileDeleted"):get("data.folders.MultipleFilesDeleted"),this.notification.show(),this._clearExplorer(),this.deleteFileDialog.hide()}))}else if(""!=this.deleteFileDialog.filename){const e=this.explorer.breadcrumb.concat(this.deleteFileDialog.filename).join("/");globalThis.backendaiclient.vfolder.delete_files([e],!0,this.explorer.id).then((e=>{this.notification.text=get("data.folders.FileDeleted"),this.notification.show(),this._clearExplorer(),this.deleteFileDialog.hide()}))}}_deleteFile(e){const t=e.target.getAttribute("filename"),i=this.explorer.breadcrumb.concat(t).join("/");globalThis.backendaiclient.vfolder.delete_files([i],!0,this.explorer.id).then((e=>{this.notification.text=get("data.folders.FileDeleted"),this.notification.show(),this._clearExplorer()}))}_isResourceEnough(){const e=new CustomEvent("backend-ai-calculate-current-resource");document.dispatchEvent(e);const t=globalThis.backendaioptions.get("current-resource");return!!(t&&(t.cpu="string"==typeof t.cpu?parseInt(t.cpu):t.cpu,t.cpu>=this.minimumResource.cpu&&t.mem>=this.minimumResource.mem))}_humanReadableTime(e){const t=new Date(1e3*e),i=t.getTimezoneOffset()/60,o=t.getHours();return t.setHours(o-i),t.toUTCString()}_isDownloadable(e){return!0}_initializeSharingFolderDialogLayout(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll("#share-folder-dialog mwc-textfield.share-email");t.length>1&&t.forEach((e=>{var t;"first-email"!==e.id&&(null===(t=e.parentNode)||void 0===t||t.removeChild(e))}))}_shareFolderDialog(e){this.selectedFolder=this._getControlName(e),this.selectedFolderType=this._getControlType(e),this._initializeSharingFolderDialogLayout(),this.openDialog("share-folder-dialog")}_modifyPermissionDialog(e){globalThis.backendaiclient.vfolder.list_invitees(e).then((e=>{this.invitees=e.shared,this.modifyPermissionDialog.updateComplete.then((()=>{this.openDialog("modify-permission-dialog")}))}))}_shareFolder(e){var t,i;const o=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll("mwc-textfield.share-email"),r=Array.prototype.filter.call(o,(e=>e.isUiValid&&""!==e.value)).map((e=>e.value.trim())),a=(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("mwc-radio[name=share-folder-permission][checked]")).value;if(0===r.length){this.notification.text=get("data.invitation.NoValidEmails"),this.notification.show(),this.shareFolderDialog.hide();for(const e of Array.from(o))e.value="";return}let n;n="user"===this.selectedFolderType?globalThis.backendaiclient.vfolder.invite(a,r,this.selectedFolder):globalThis.backendaiclient.vfolder.share(a,r,this.selectedFolder),n.then((e=>{var t;let i;i="user"===this.selectedFolderType?e.invited_ids&&e.invited_ids.length>0?get("data.invitation.Invited"):get("data.invitation.NoOneWasInvited"):e.shared_emails&&e.shared_emails.length>0?get("data.invitation.Shared"):get("data.invitation.NoOneWasShared"),this.notification.text=i,this.notification.show(),this.shareFolderDialog.hide();for(let e=o.length-1;e>0;e--){const i=o[e];null===(t=i.parentElement)||void 0===t||t.removeChild(i)}})).catch((e=>{"user"===this.selectedFolderType?this.notification.text=get("data.invitation.InvitationError"):this.notification.text=get("data.invitation.SharingError"),e&&e.message&&(this.notification.detail=e.message),this.notification.show(!0,e)}))}_validatePathName(){this.mkdirNameInput.validityTransform=(e,t)=>{if(t.valid){let e=/^([^`~!@#$%^&*()|+=?;:'",<>{}[\]\r\n/]{1,})+(\/[^`~!@#$%^&*()|+=?;:'",<>{}[\]\r\n/]{1,})*([/,\\]{0,1})$/gm.test(this.mkdirNameInput.value);return e&&"./"!==this.mkdirNameInput.value||(this.mkdirNameInput.validationMessage=get("data.explorer.ValueShouldBeStarted"),e=!1),{valid:e,customError:!e}}return t.valueMissing?(this.mkdirNameInput.validationMessage=get("data.explorer.ValueRequired"),{valid:t.valid,customError:!t.valid}):{valid:t.valid,customError:!t.valid}}}};__decorate([e({type:Number})],BackendAiStorageList.prototype,"_APIMajorVersion",void 0),__decorate([e({type:String})],BackendAiStorageList.prototype,"storageType",void 0),__decorate([e({type:Array})],BackendAiStorageList.prototype,"folders",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"folderInfo",void 0),__decorate([e({type:Boolean})],BackendAiStorageList.prototype,"is_admin",void 0),__decorate([e({type:Boolean})],BackendAiStorageList.prototype,"enableStorageProxy",void 0),__decorate([e({type:Boolean})],BackendAiStorageList.prototype,"authenticated",void 0),__decorate([e({type:String})],BackendAiStorageList.prototype,"renameFolderName",void 0),__decorate([e({type:String})],BackendAiStorageList.prototype,"deleteFolderName",void 0),__decorate([e({type:String})],BackendAiStorageList.prototype,"leaveFolderName",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"explorer",void 0),__decorate([e({type:Array})],BackendAiStorageList.prototype,"explorerFiles",void 0),__decorate([e({type:String})],BackendAiStorageList.prototype,"existingFile",void 0),__decorate([e({type:Array})],BackendAiStorageList.prototype,"invitees",void 0),__decorate([e({type:String})],BackendAiStorageList.prototype,"selectedFolder",void 0),__decorate([e({type:String})],BackendAiStorageList.prototype,"selectedFolderType",void 0),__decorate([e({type:String})],BackendAiStorageList.prototype,"downloadURL",void 0),__decorate([e({type:Array})],BackendAiStorageList.prototype,"uploadFiles",void 0),__decorate([e({type:Array})],BackendAiStorageList.prototype,"fileUploadQueue",void 0),__decorate([e({type:Number})],BackendAiStorageList.prototype,"fileUploadCount",void 0),__decorate([e({type:Number})],BackendAiStorageList.prototype,"concurrentFileUploadLimit",void 0),__decorate([e({type:String})],BackendAiStorageList.prototype,"vhost",void 0),__decorate([e({type:Array})],BackendAiStorageList.prototype,"vhosts",void 0),__decorate([e({type:Array})],BackendAiStorageList.prototype,"allowedGroups",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"indicator",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"notification",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"sessionLauncher",void 0),__decorate([e({type:String})],BackendAiStorageList.prototype,"listCondition",void 0),__decorate([e({type:Array})],BackendAiStorageList.prototype,"allowed_folder_type",void 0),__decorate([e({type:Boolean})],BackendAiStorageList.prototype,"uploadFilesExist",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"_boundIndexRenderer",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"_boundTypeRenderer",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"_boundFolderListRenderer",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"_boundControlFolderListRenderer",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"_boundControlFileListRenderer",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"_boundPermissionViewRenderer",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"_boundOwnerRenderer",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"_boundFileNameRenderer",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"_boundCreatedTimeRenderer",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"_boundPermissionRenderer",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"_boundCloneableRenderer",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"_boundQuotaRenderer",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"_boundUploadListRenderer",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"_boundUploadProgressRenderer",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"_boundInviteeInfoRenderer",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"_boundIDRenderer",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"_boundStatusRenderer",void 0),__decorate([e({type:Boolean})],BackendAiStorageList.prototype,"_uploadFlag",void 0),__decorate([e({type:Boolean})],BackendAiStorageList.prototype,"_folderRefreshing",void 0),__decorate([e({type:Number})],BackendAiStorageList.prototype,"lastQueryTime",void 0),__decorate([e({type:Boolean})],BackendAiStorageList.prototype,"isWritable",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"permissions",void 0),__decorate([e({type:Number})],BackendAiStorageList.prototype,"_maxFileUploadSize",void 0),__decorate([e({type:Number})],BackendAiStorageList.prototype,"selectAreaHeight",void 0),__decorate([e({type:String})],BackendAiStorageList.prototype,"oldFileExtension",void 0),__decorate([e({type:String})],BackendAiStorageList.prototype,"newFileExtension",void 0),__decorate([e({type:Boolean})],BackendAiStorageList.prototype,"is_dir",void 0),__decorate([e({type:Number})],BackendAiStorageList.prototype,"minimumResource",void 0),__decorate([e({type:Array})],BackendAiStorageList.prototype,"filebrowserSupportedImages",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"storageProxyInfo",void 0),__decorate([e({type:Array})],BackendAiStorageList.prototype,"quotaSupportStorageBackends",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"quotaUnit",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"maxSize",void 0),__decorate([e({type:Object})],BackendAiStorageList.prototype,"quota",void 0),__decorate([i("#loading-spinner")],BackendAiStorageList.prototype,"spinner",void 0),__decorate([i("#list-status")],BackendAiStorageList.prototype,"_listStatus",void 0),__decorate([i("#modify-folder-quota")],BackendAiStorageList.prototype,"modifyFolderQuotaInput",void 0),__decorate([i("#modify-folder-quota-unit")],BackendAiStorageList.prototype,"modifyFolderQuotaUnitSelect",void 0),__decorate([i("#fileList-grid")],BackendAiStorageList.prototype,"fileListGrid",void 0),__decorate([i("#mkdir-name")],BackendAiStorageList.prototype,"mkdirNameInput",void 0),__decorate([i("#delete-folder-name")],BackendAiStorageList.prototype,"deleteFolderNameInput",void 0),__decorate([i("#new-folder-name")],BackendAiStorageList.prototype,"newFolderNameInput",void 0),__decorate([i("#new-file-name")],BackendAiStorageList.prototype,"newFileNameInput",void 0),__decorate([i("#leave-folder-name")],BackendAiStorageList.prototype,"leaveFolderNameInput",void 0),__decorate([i("#update-folder-permission")],BackendAiStorageList.prototype,"updateFolderPermissionSelect",void 0),__decorate([i("#update-folder-cloneable")],BackendAiStorageList.prototype,"updateFolderCloneableSwitch",void 0),__decorate([i("#rename-file-dialog")],BackendAiStorageList.prototype,"renameFileDialog",void 0),__decorate([i("#delete-file-dialog")],BackendAiStorageList.prototype,"deleteFileDialog",void 0),__decorate([i("#filebrowser-notification-dialog")],BackendAiStorageList.prototype,"fileBrowserNotificationDialog",void 0),__decorate([i("#file-extension-change-dialog")],BackendAiStorageList.prototype,"fileExtensionChangeDialog",void 0),__decorate([i("#folder-explorer-dialog")],BackendAiStorageList.prototype,"folderExplorerDialog",void 0),__decorate([i("#download-file-dialog")],BackendAiStorageList.prototype,"downloadFileDialog",void 0),__decorate([i("#modify-permission-dialog")],BackendAiStorageList.prototype,"modifyPermissionDialog",void 0),__decorate([i("#share-folder-dialog")],BackendAiStorageList.prototype,"shareFolderDialog",void 0),BackendAiStorageList=__decorate([e$1("backend-ai-storage-list")],BackendAiStorageList);let BackendAIData=class extends BackendAIPage{constructor(){super(...arguments),this.apiMajorVersion="",this.folders=Object(),this.folderInfo=Object(),this.is_admin=!1,this.enableStorageProxy=!1,this.authenticated=!1,this.deleteFolderId="",this.vhost="",this.vhosts=[],this.usageModes=["General"],this.permissions=["Read-Write","Read-Only","Delete"],this.allowedGroups=[],this.allowed_folder_type=[],this.notification=Object(),this.folderLists=Object(),this._status="inactive",this.active=!0,this._lists=Object(),this._vfolderInnatePermissionSupport=!1,this.storageInfo=Object(),this._activeTab="general",this._helpDescription="",this._helpDescriptionTitle="",this._helpDescriptionIcon="",this.cloneFolderName="",this.quotaSupportStorageBackends=["xfs","weka","spectrumscale"],this.storageProxyInfo=Object(),this.folderType="user"}static get styles(){return[BackendAiStyles,IronFlex,IronFlexAlignment,IronPositioning,i$1`
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

        .folder-action-buttons wl-button {
          margin-right: 10px;
        }

        wl-button > wl-icon {
          --icon-size: 24px;
          padding: 0;
        }

        wl-icon {
          --icon-size: 16px;
          padding: 0;
        }

        wl-button.button {
          width: 350px;
        }

        wl-card.item {
          height: calc(100vh - 145px) !important;
        }

        .tab-content {
          border: 0;
          font-size: 14px;
        }

        mwc-textfield {
          width: 100%;
          --mdc-theme-primary: #242424;
          --mdc-text-field-fill-color: transparent;
        }

        mwc-textfield.red {
          --mdc-theme-primary: var(--paper-red-400) !important;
        }

        h3.tab {
          background-color: var(--general-tabbar-background-color);
          border-radius: 5px 5px 0px 0px;
          margin: 0px auto;
        }

        mwc-tab-bar {
          --mdc-theme-primary: var(--general-sidebar-selected-color);
          --mdc-text-transform: none;
          --mdc-tab-color-default: var(--general-tabbar-background-color);
          --mdc-tab-text-label-color-default: var(--general-tabbar-tab-disabled-color);
        }

        wl-tab-group {
          --tab-group-indicator-bg: var(--paper-orange-500);
        }

        wl-tab {
          --tab-color: #666666;
          --tab-color-hover: #222222;
          --tab-color-hover-filled: #222222;
          --tab-color-active: #222222;
          --tab-color-active-hover: #222222;
          --tab-color-active-filled: #cccccc;
          --tab-bg-active: var(--paper-orange-50);
          --tab-bg-filled: var(--paper-orange-50);
          --tab-bg-active-hover: var(--paper-orange-100);
        }

        wl-button {
          --button-bg: var(--paper-orange-50);
          --button-bg-hover: var(--paper-orange-100);
          --button-bg-active: var(--paper-orange-600);
          color: var(--paper-orange-900);
        }

        #add-folder-dialog,
        #clone-folder-dialog {
          --component-width: 375px;
        }

        backend-ai-dialog wl-textfield,
        backend-ai-dialog wl-select {
          --input-font-family: var(--general-font-family);
          --input-color-disabled: #222222;
          --input-label-color-disabled: #222222;
          --input-label-font-size: 12px;
          --input-border-style-disabled: 1px solid #cccccc;
        }

        #help-description {
          --component-width: 350px;
        }

        #textfields wl-textfield,
        wl-label {
          margin-bottom: 20px;
        }

        wl-label {
          --label-font-family: 'Ubuntu', Roboto;
          --label-color: black;
        }

        mwc-select {
          width: 50%;
          margin-bottom: 10px;
          --mdc-theme-primary: var(--general-textfield-selected-color);
          --mdc-select-fill-color: transparent;
          --mdc-select-label-ink-color: rgba(0, 0, 0, 0.75);
          --mdc-select-dropdown-icon-color: var(--general-textfield-selected-color);
          --mdc-select-hover-line-color: var(--general-textfield-selected-color);
          --mdc-list-vertical-padding: 5px;
          /* Need to be set when fixedMenuPosition attribute is enabled */
          --mdc-menu-max-width: 345px;
          --mdc-menu-min-width: 172.5px;
          --mdc-select-disabled-ink-color: #cccccc;
        }

        mwc-select.full-width.fixed-position {
          width: 100%;
          /* Need to be set when fixedMenuPosition attribute is enabled */
          --mdc-menu-max-width: 345px;
          --mdc-menu-min-width: 345px;
        }

        mwc-select.fixed-position {
          /* Need to be set when fixedMenuPosition attribute is enabled */
          --mdc-menu-max-width: 172.5px;
          --mdc-menu-min-width: 172.5px;
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

        #automount-folder-lists > div {
          background-color: white;
          color: var(--general-textfield-selected-color);
          border-bottom:0.5px solid var(--general-textfield-selected-color);
        }

        #automount-folder-lists > div > p {
          color: var(--general-sidebar-color);
          margin-left: 10px;
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
          display:none;
        }

        @media screen and (max-width: 750px) {
          mwc-tab {
            --mdc-typography-button-font-size: 10px;
          }

          mwc-button > span {
            display: none;
          }
        }
      `]}render(){return y`
      <link rel="stylesheet" href="resources/custom.css">
      <div class="vertical layout">
        <lablup-activity-panel elevation="1" narrow title=${translate("data.StorageStatus")} autowidth>
          <div slot="message">
            <div class="horizontal layout wrap flex center center-justified">
              <div class="storage-chart-wrapper">
                <chart-js id="storage-status" type="doughnut" .data="${this.folders}" .options="${this.options}" height="250" width="250"></chart-js>
              </div>
              <div class="horizontal layout justified">
                <div class="vertical layout center storage-status-indicator">
                  <div class="big">${this.createdCount}</div>
                  <span>${translate("data.Created")}</span>
                </div>
                <div class="vertical layout center storage-status-indicator">
                  <div class="big">${this.invitedCount}</div>
                  <span>${translate("data.Invited")}</span>
                </div>
                <div class="vertical layout center storage-status-indicator">
                  <div class="big">${this.capacity}</div>
                  <span>${translate("data.Capacity")}</span>
                </div>
              </div>
            </div>
          </div>
        </lablup-activity-panel>
        <lablup-activity-panel elevation="1" noheader narrow autowidth>
          <div slot="message">
            <h3 class="horizontal center flex layout tab">
              <mwc-tab-bar>
                <mwc-tab title="general" label="${translate("data.Folders")}"
                    @click="${e=>this._showTab(e.target)}">
                </mwc-tab>
                <mwc-tab title="automount" label="${translate("data.AutomountFolders")}" @click="${e=>this._showTab(e.target)}"></mwc-tab>
              </mwc-tab-bar>
              <span class="flex"></span>
              <mwc-button dense raised id="add-folder" icon="add" @click="${()=>this._addFolderDialog()}" style="margin-right:15px;">
                <span>${translate("data.NewFolder")}</span>
              </mwc-button>
            </h3>
            <div id="general-folder-lists" class="tab-content">
              <backend-ai-storage-list id="general-folder-storage" storageType="general" ?active="${!0===this.active&&"general"===this._activeTab}"></backend-ai-storage-list>
            </div>
            <div id="automount-folder-lists" class="tab-content" style="display:none;">
              <div class="horizontal layout">
                <p>${translate("data.DialogFolderStartingWithDotAutomount")}</p>
              </div>
              <backend-ai-storage-list id="automount-folder-storage" storageType="automount" ?active="${!0===this.active&&"automount"===this._activeTab}"></backend-ai-storage-list>
            </div>
          </div>
        </lablup-activity-panel>
      </div>
      <backend-ai-dialog id="add-folder-dialog" fixed backdrop>
        <span slot="title">${translate("data.CreateANewStorageFolder")}</span>
        <div slot="content" class="vertical layout flex">
          <mwc-textfield id="add-folder-name" label="${translate("data.Foldername")}"
          @change="${()=>this._validateFolderName()}" pattern="^[a-zA-Z0-9\._-]*$"
            required validationMessage="${translate("data.Allowslettersnumbersand-_dot")}" maxLength="64"
            placeholder="${translate("maxLength.64chars")}"></mwc-textfield>
          <mwc-select class="full-width fixed-position" id="add-folder-host" label="${translate("data.Host")}" fixedMenuPosition>
            ${this.vhosts.map(((e,t)=>y`
              <mwc-list-item hasMeta value="${e}" ?selected="${e===this.vhost}">
                <span>${e}</span>
                <mwc-icon-button slot="meta" icon="info"
                    @click="${t=>this._showStorageDescription(t,e)}">
                </mwc-icon-button>
              </mwc-list-item>
            `))}
          </mwc-select>
          <div class="horizontal layout">
            <mwc-select id="add-folder-type" label="${translate("data.Type")}"
                        style="width:${this.is_admin&&this.allowed_folder_type.includes("group")?"50%":"100%"}"
                        @change=${this._toggleFolderTypeInput} required>
              ${this.allowed_folder_type.includes("user")?y`
                <mwc-list-item value="user" selected>${translate("data.User")}</mwc-list-item>
              `:y``}
              ${this.is_admin&&this.allowed_folder_type.includes("group")?y`
                <mwc-list-item value="group" ?selected="${!this.allowed_folder_type.includes("user")}">${translate("data.Project")}</mwc-list-item>
              `:y``}
            </mwc-select>
            ${this.is_admin&&this.allowed_folder_type.includes("group")?y`
              <mwc-select class="fixed-position" id="add-folder-group" ?disabled=${"user"===this.folderType} label="${translate("data.Project")}" FixedMenuPosition>
                ${this.allowedGroups.map(((e,t)=>y`
                  <mwc-list-item value="${e.name}" ?selected="${0===t}">${e.name}</mwc-list-item>
                `))}
              </mwc-select>
          `:y``}
          </div>
          ${this._vfolderInnatePermissionSupport?y`
            <div class="horizontal layout">
              <mwc-select class="fixed-position" id="add-folder-usage-mode" label="${translate("data.UsageMode")}" fixedMenuPosition>
                ${this.usageModes.map(((e,t)=>y`
                  <mwc-list-item value="${e}" ?selected="${0===t}">${e}</mwc-list-item>
                `))}
              </mwc-select>
              <mwc-select class="fixed-position" id="add-folder-permission" label="${translate("data.Permission")}" fixedMenuPosition>
                ${this.permissions.map(((e,t)=>y`
                  <mwc-list-item value="${e}" ?selected="${0===t}">${e}</mwc-list-item>
                `))}
              </mwc-select>
            </div>
          `:y``}
          ${this.enableStorageProxy?y`
          <!--<div class="horizontal layout flex wrap center justified">
              <p style="color:rgba(0, 0, 0, 0.6);">
                ${translate("data.folders.Cloneable")}
              </p>
              <mwc-switch id="add-folder-cloneable" style="margin-right:10px;">
              </mwc-switch>
            </div>-->
            `:y``}
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
              @click="${()=>this._addFolder()}"></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="clone-folder-dialog" fixed backdrop>
        <span slot="title">${translate("data.folders.CloneAFolder")}</span>
        <div slot="content" style="width:100%;">
          <mwc-textfield id="clone-folder-src" label="${translate("data.FolderToCopy")}" value="${this.cloneFolderName}"
              disabled></mwc-textfield>
          <mwc-textfield id="clone-folder-name" label="${translate("data.Foldername")}"
              @change="${()=>this._validateFolderName()}" pattern="^[a-zA-Z0-9\._-]*$"
              required validationMessage="${translate("data.Allowslettersnumbersand-_dot")}" maxLength="64"
              placeholder="${translate("maxLength.64chars")}"></mwc-textfield>
          <mwc-select class="full-width fixed-position" id="clone-folder-host" label="${translate("data.Host")}" fixedMenuPosition>
            ${this.vhosts.map(((e,t)=>y`
              <mwc-list-item hasMeta value="${e}" ?selected="${0===t}">
                <span>${e}</span>
                <mwc-icon-button slot="meta" icon="info"
                    @click="${t=>this._showStorageDescription(t,e)}">
                </mwc-icon-button>
              </mwc-list-item>
            `))}
          </mwc-select>
          <div class="horizontal layout">
            <mwc-select id="clone-folder-type" label="${translate("data.Type")}"
                        style="width:${this.is_admin&&this.allowed_folder_type.includes("group")?"50%":"100%"}">
              ${this.allowed_folder_type.includes("user")?y`
                <mwc-list-item value="user" selected>${translate("data.User")}</mwc-list-item>
              `:y``}
              ${this.is_admin&&this.allowed_folder_type.includes("group")?y`
                <mwc-list-item value="group" ?selected="${!this.allowed_folder_type.includes("user")}">${translate("data.Project")}</mwc-list-item>
              `:y``}
            </mwc-select>
            ${this.is_admin&&this.allowed_folder_type.includes("group")?y`
                <mwc-select class="fixed-position" id="clone-folder-group" label="${translate("data.Project")}" FixedMenuPosition>
                  ${this.allowedGroups.map(((e,t)=>y`
                    <mwc-list-item value="${e.name}" ?selected="${0===t}">${e.name}</mwc-list-item>
                  `))}
                </mwc-select>
            `:y``}
          </div>
          ${this._vfolderInnatePermissionSupport?y`
            <div class="horizontal layout">
              <mwc-select class="fixed-position" id="clone-folder-usage-mode" label="${translate("data.UsageMode")}" FixedMenuPosition>
                ${this.usageModes.map(((e,t)=>y`
                  <mwc-list-item value="${e}" ?selected="${0===t}">${e}</mwc-list-item>
                `))}
              </mwc-select>
              <mwc-select class="fixed-position" id="clone-folder-permission" label="${translate("data.Permission")}" FixedMenuPosition>
                ${this.permissions.map(((e,t)=>y`
                  <mwc-list-item value="${e}" ?selected="${0===t}">${e}</mwc-list-item>
                `))}
              </mwc-select>
            </div>
          `:y``}
          ${this.enableStorageProxy?y`
          <div class="horizontal layout flex wrap center justified">
              <p style="color:rgba(0, 0, 0, 0.6);">
                ${translate("data.folders.Cloneable")}
              </p>
              <mwc-switch id="clone-folder-cloneable" style="margin-right:10px;">
              </mwc-switch>
            </div>
            `:y``}
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
              @click="${()=>this._cloneFolder()}"></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="help-description" fixed backdrop>
        <span slot="title">${this._helpDescriptionTitle}</span>
        <div slot="content" class="horizontal layout center">
        ${""==this._helpDescriptionIcon?y``:y`
          <img slot="graphic" src="resources/icons/${this._helpDescriptionIcon}" style="width:64px;height:64px;margin-right:10px;" />
          `}
          <p style="font-size:14px;width:256px;">${o$2(this._helpDescription)}</p>
        </div>
      </backend-ai-dialog>
    `}firstUpdated(){var e;this.notification=globalThis.lablupNotification,this.folderLists=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll("backend-ai-storage-list"),fetch("resources/storage_metadata.json").then((e=>e.json())).then((e=>{const t=Object();for(const i in e.storageInfo)({}).hasOwnProperty.call(e.storageInfo,i)&&(t[i]={},"name"in e.storageInfo[i]&&(t[i].name=e.storageInfo[i].name),"description"in e.storageInfo[i]?t[i].description=e.storageInfo[i].description:t[i].description=get("data.NoStorageDescriptionFound"),"icon"in e.storageInfo[i]?t[i].icon=e.storageInfo[i].icon:t[i].icon="local.png","dialects"in e.storageInfo[i]&&e.storageInfo[i].dialects.forEach((e=>{t[e]=t[i]})));this.storageInfo=t})),this.options={responsive:!0,maintainAspectRatio:!0,legend:{display:!0,position:"bottom",align:"center",labels:{fontSize:20,boxWidth:10}}},void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._getStorageProxyBackendInformation()}),!0):this._getStorageProxyBackendInformation(),document.addEventListener("backend-ai-folder-list-changed",(()=>{this._createStorageChart()})),document.addEventListener("backend-ai-vfolder-cloning",(e=>{if(e.detail){const t=e.detail;this.cloneFolderName=t.name,this._cloneFolderDialog()}}))}async _viewStateChanged(e){if(await this.updateComplete,!1===e)return;const t=()=>{this.is_admin=globalThis.backendaiclient.is_admin,this.authenticated=!0,this.enableStorageProxy=globalThis.backendaiclient.supports("storage-proxy"),this.apiMajorVersion=globalThis.backendaiclient.APIMajorVersion,this._getStorageProxyBackendInformation(),globalThis.backendaiclient.isAPIVersionCompatibleWith("v4.20191215")&&(this._vfolderInnatePermissionSupport=!0),globalThis.backendaiclient.vfolder.list_allowed_types().then((e=>{this.allowed_folder_type=e}))};void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{t(),this._createStorageChart()}),!0):(t(),this._createStorageChart())}async _createStorageChart(){const e=globalThis.backendaiclient._config.accessKey,t=(await globalThis.backendaiclient.keypair.info(e,["resource_policy"])).keypair.resource_policy,i=(await globalThis.backendaiclient.resourcePolicy.get(t,["max_vfolder_count"])).keypair_resource_policy.max_vfolder_count,o=globalThis.backendaiclient.current_group_id(),r=await globalThis.backendaiclient.vfolder.list(o);this.createdCount=r.filter((e=>e.is_owner)).length,this.invitedCount=r.length-this.createdCount,this.capacity=this.createdCount<i?i-this.createdCount:0,this.totalCount=this.capacity+this.createdCount+this.invitedCount,this.folders={labels:[get("data.Created"),get("data.Invited"),get("data.Capacity")],datasets:[{data:[this.createdCount,this.invitedCount,this.capacity],backgroundColor:["#722cd7","#60bb43","#efefef"]}]}}_toggleFolderTypeInput(){var e;this.folderType=(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#add-folder-type")).value}_showTab(e){var t,i;const o=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".tab-content");for(let e=0;e<o.length;e++)o[e].style.display="none";(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+e.title+"-folder-lists")).style.display="block",this._activeTab=e.title}async _cloneFolderDialog(){const e=await globalThis.backendaiclient.vfolder.list_hosts();if(this.addFolderNameInput.value="",this.vhosts=e.allowed,this.vhost=e.default,this.allowed_folder_type.includes("group")){const e=await globalThis.backendaiclient.group.list();this.allowedGroups=e.groups}this.cloneFolderNameInput.value=await this._checkFolderNameAlreadyExists(this.cloneFolderName),this.openDialog("clone-folder-dialog")}async _addFolderDialog(){const e=await globalThis.backendaiclient.vfolder.list_hosts();if(this.addFolderNameInput.value="",this.vhosts=e.allowed,this.vhost=e.default,this.allowed_folder_type.includes("group")){const e=await globalThis.backendaiclient.group.list();this.allowedGroups=e.groups}this.openDialog("add-folder-dialog")}async _getStorageProxyBackendInformation(){const e=await globalThis.backendaiclient.vfolder.list_hosts();this.storageProxyInfo=e.volume_info||{}}openDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).show()}closeDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).hide()}_showStorageDescription(e,t){var i;e.stopPropagation(),t in this.storageInfo?(this._helpDescriptionTitle=this.storageInfo[t].name,this._helpDescription=this.storageInfo[t].description,this._helpDescriptionIcon=this.storageInfo[t].icon):(this._helpDescriptionTitle=t,this._helpDescriptionIcon="local.png",this._helpDescription=get("data.NoStorageDescriptionFound"));(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#help-description")).show()}_indexFrom1(e){return e+1}_addFolder(){var e,t,i,o,r,a;const n=this.addFolderNameInput.value,l=(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#add-folder-host")).value;let s,d=(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#add-folder-type")).value;const c=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#add-folder-usage-mode"),u=null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("#add-folder-permission"),p=null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector("#add-folder-cloneable");let h="",m="",f=!1;if(!1===["user","group"].includes(d)&&(d="user"),s="user"===d?"":this.is_admin?(null===(a=this.shadowRoot)||void 0===a?void 0:a.querySelector("#add-folder-group")).value:globalThis.backendaiclient.current_group,c&&(h=c.value,h=h.toLowerCase()),u)switch(m=u.value,m){case"Read-Write":default:m="rw";break;case"Read-Only":m="ro";break;case"Delete":m="wd"}if(p&&(f=p.checked),this.addFolderNameInput.reportValidity(),this.addFolderNameInput.checkValidity()){globalThis.backendaiclient.vfolder.create(n,l,s,h,m,f).then((e=>{this.notification.text=get("data.folders.FolderCreated"),this.notification.show(),this._refreshFolderList()})).catch((e=>{e&&e.message&&(this.notification.text=BackendAIPainKiller.relieve(e.message),this.notification.detail=e.message,this.notification.show(!0,e))})),this.closeDialog("add-folder-dialog")}}async _cloneFolder(){var e,t,i,o,r;const a=await this._checkFolderNameAlreadyExists(this.cloneFolderNameInput.value,!0),n=(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#clone-folder-host")).value;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#clone-folder-type")).value;const l=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#clone-folder-usage-mode"),s=null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("#clone-folder-permission"),d=null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector("#clone-folder-cloneable");let c="",u="",p=!1;if(l&&(c=l.value,c=c.toLowerCase()),s)switch(u=s.value,u){case"Read-Write":default:u="rw";break;case"Read-Only":u="ro";break;case"Delete":u="wd"}if(p=!!d&&d.selected,this.cloneFolderNameInput.reportValidity(),this.cloneFolderNameInput.checkValidity()){const e={cloneable:p,permission:u,target_host:n,target_name:a,usage_mode:c};globalThis.backendaiclient.vfolder.clone(e,this.cloneFolderName).then((e=>{this.notification.text=get("data.folders.FolderCloned"),this.notification.show(),this._refreshFolderList()})).catch((e=>{e&&e.message&&(this.notification.text=BackendAIPainKiller.relieve(e.message),this.notification.detail=e.message,this.notification.show(!0,e))})),this.closeDialog("clone-folder-dialog")}}_validateFolderName(){this.addFolderNameInput.validityTransform=(e,t)=>{if(t.valid){let e=!/[`~!@#$%^&*()|+=?;:'",<>{}[\]\\/\s]/gi.test(this.addFolderNameInput.value);return e||(this.addFolderNameInput.validationMessage=get("data.Allowslettersnumbersand-_dot")),this.addFolderNameInput.value.length>64&&(e=!1,this.addFolderNameInput.validationMessage=get("data.FolderNameTooLong")),{valid:e,customError:!e}}return t.valueMissing?(this.addFolderNameInput.validationMessage=get("data.FolderNameRequired"),{valid:t.valid,customError:!t.valid}):(this.addFolderNameInput.validationMessage=get("data.Allowslettersnumbersand-_dot"),{valid:t.valid,customError:!t.valid})}}_refreshFolderList(){for(const e of this.folderLists)e.refreshFolderList()}async _checkFolderNameAlreadyExists(e,t=!1){const i=globalThis.backendaiclient.current_group_id(),o=(await globalThis.backendaiclient.vfolder.list(i)).map((e=>e.name));if(o.includes(e)){t&&(this.notification.text=get("import.FolderAlreadyExists"),this.notification.show());let i=1,r=e;for(;o.includes(r);)r=e+"_"+i,i++;e=r}return e}};__decorate([e({type:String})],BackendAIData.prototype,"apiMajorVersion",void 0),__decorate([e({type:Object})],BackendAIData.prototype,"folders",void 0),__decorate([e({type:Object})],BackendAIData.prototype,"folderInfo",void 0),__decorate([e({type:Boolean})],BackendAIData.prototype,"is_admin",void 0),__decorate([e({type:Boolean})],BackendAIData.prototype,"enableStorageProxy",void 0),__decorate([e({type:Boolean})],BackendAIData.prototype,"authenticated",void 0),__decorate([e({type:String})],BackendAIData.prototype,"deleteFolderId",void 0),__decorate([e({type:String})],BackendAIData.prototype,"vhost",void 0),__decorate([e({type:Array})],BackendAIData.prototype,"vhosts",void 0),__decorate([e({type:Array})],BackendAIData.prototype,"usageModes",void 0),__decorate([e({type:Array})],BackendAIData.prototype,"permissions",void 0),__decorate([e({type:Array})],BackendAIData.prototype,"allowedGroups",void 0),__decorate([e({type:Array})],BackendAIData.prototype,"allowed_folder_type",void 0),__decorate([e({type:Object})],BackendAIData.prototype,"notification",void 0),__decorate([e({type:Object})],BackendAIData.prototype,"folderLists",void 0),__decorate([e({type:String})],BackendAIData.prototype,"_status",void 0),__decorate([e({type:Boolean})],BackendAIData.prototype,"active",void 0),__decorate([e({type:Object})],BackendAIData.prototype,"_lists",void 0),__decorate([e({type:Boolean})],BackendAIData.prototype,"_vfolderInnatePermissionSupport",void 0),__decorate([e({type:Object})],BackendAIData.prototype,"storageInfo",void 0),__decorate([e({type:String})],BackendAIData.prototype,"_activeTab",void 0),__decorate([e({type:String})],BackendAIData.prototype,"_helpDescription",void 0),__decorate([e({type:String})],BackendAIData.prototype,"_helpDescriptionTitle",void 0),__decorate([e({type:String})],BackendAIData.prototype,"_helpDescriptionIcon",void 0),__decorate([e({type:Object})],BackendAIData.prototype,"options",void 0),__decorate([e({type:Number})],BackendAIData.prototype,"createdCount",void 0),__decorate([e({type:Number})],BackendAIData.prototype,"invitedCount",void 0),__decorate([e({type:Number})],BackendAIData.prototype,"totalCount",void 0),__decorate([e({type:Number})],BackendAIData.prototype,"capacity",void 0),__decorate([e({type:String})],BackendAIData.prototype,"cloneFolderName",void 0),__decorate([e({type:Array})],BackendAIData.prototype,"quotaSupportStorageBackends",void 0),__decorate([e({type:Object})],BackendAIData.prototype,"storageProxyInfo",void 0),__decorate([e({type:String})],BackendAIData.prototype,"folderType",void 0),__decorate([i("#add-folder-name")],BackendAIData.prototype,"addFolderNameInput",void 0),__decorate([i("#clone-folder-name")],BackendAIData.prototype,"cloneFolderNameInput",void 0),BackendAIData=__decorate([e$1("backend-ai-data-view")],BackendAIData);var BackendAIData$1=BackendAIData;export{BackendAIData$1 as default};
