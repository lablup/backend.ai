import{r as e,a9 as t,az as a,aA as i,aB as r,aC as s,l,$ as n,T as d,N as o,P as u,Z as h,af as p,J as c,a6 as g}from"./backend-ai-webui-45991858.js";import{G as v}from"./vaadin-grid-9c58de6c.js";
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */e("vaadin-text-field",t,{moduleId:"lumo-text-field-styles"});
/**
 * @license
 * Copyright (c) 2021 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const _=e=>class extends(a(e)){static get properties(){return{autocomplete:{type:String},autocorrect:{type:String},autocapitalize:{type:String,reflectToAttribute:!0}}}static get delegateAttrs(){return[...super.delegateAttrs,"autocapitalize","autocomplete","autocorrect"]}get __data(){return this.__dataValue||{}}set __data(e){this.__dataValue=e}_inputElementChanged(e){super._inputElementChanged(e),e&&(e.value&&e.value!==this.value&&(console.warn(`Please define value on the <${this.localName}> component!`),e.value=""),this.value&&(e.value=this.value))}_setFocused(e){super._setFocused(e),!e&&document.hasFocus()&&this.validate()}_onInput(e){super._onInput(e),this.invalid&&this.validate()}_valueChanged(e,t){super._valueChanged(e,t),void 0!==t&&this.invalid&&this.validate()}}
/**
 * @license
 * Copyright (c) 2021 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,m=e=>class extends(_(e)){static get properties(){return{maxlength:{type:Number},minlength:{type:Number},pattern:{type:String}}}static get delegateAttrs(){return[...super.delegateAttrs,"maxlength","minlength","pattern"]}static get constraints(){return[...super.constraints,"maxlength","minlength","pattern"]}constructor(){super(),this._setType("text")}get clearElement(){return this.$.clearButton}ready(){super.ready(),this.addController(new i(this,(e=>{this._setInputElement(e),this._setFocusElement(e),this.stateTarget=e,this.ariaTarget=e}))),this.addController(new r(this.inputElement,this._labelController))}}
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;e("vaadin-text-field",s,{moduleId:"vaadin-text-field-styles"});class f extends(m(d(o(u)))){static get is(){return"vaadin-text-field"}static get template(){return l`
      <style>
        [part='input-field'] {
          flex-grow: 0;
        }
      </style>

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
    `}static get properties(){return{maxlength:{type:Number},minlength:{type:Number}}}ready(){super.ready(),this._tooltipController=new n(this),this._tooltipController.setPosition("top"),this.addController(this._tooltipController)}}customElements.define(f.is,f);
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
class x extends(h(u)){static get template(){return l`
      <style>
        :host {
          display: inline-flex;
          max-width: 100%;
        }

        ::slotted(*) {
          width: 100%;
          box-sizing: border-box;
        }
      </style>
      <slot></slot>
    `}static get is(){return"vaadin-grid-filter"}static get properties(){return{path:String,value:{type:String,notify:!0},_textField:{type:Object}}}static get observers(){return["_filterChanged(path, value, _textField)"]}ready(){super.ready(),this._filterController=new p(this,"","vaadin-text-field",{initializer:e=>{e.addEventListener("value-changed",(e=>{this.value=e.detail.value})),this._textField=e}}),this.addController(this._filterController)}_filterChanged(e,t,a){void 0!==e&&void 0!==t&&a&&(void 0===this._previousValue&&""===t||(a.value=t,this._previousValue=t,this._debouncerFilterChanged=c.debounce(this._debouncerFilterChanged,g.after(200),(()=>{this.dispatchEvent(new CustomEvent("filter-changed",{bubbles:!0}))}))))}focus(){this._textField&&this._textField.focus()}}customElements.define(x.is,x);
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
class b extends v{static get is(){return"vaadin-grid-filter-column"}static get properties(){return{path:String,header:String}}static get observers(){return["_onHeaderRendererOrBindingChanged(_headerRenderer, _headerCell, path, header, _filterValue)"]}constructor(){super(),this.__boundOnFilterValueChanged=this.__onFilterValueChanged.bind(this)}_defaultHeaderRenderer(e,t){let a=e.firstElementChild,i=a?a.firstElementChild:void 0;a||(a=document.createElement("vaadin-grid-filter"),i=document.createElement("vaadin-text-field"),i.setAttribute("theme","small"),i.setAttribute("style","max-width: 100%;"),i.setAttribute("focus-target",""),i.addEventListener("value-changed",this.__boundOnFilterValueChanged),a.appendChild(i),e.appendChild(a)),a.path=this.path,a.value=this._filterValue,i.__rendererValue=this._filterValue,i.value=this._filterValue,i.label=this.__getHeader(this.header,this.path)}_computeHeaderRenderer(){return this._defaultHeaderRenderer}__onFilterValueChanged(e){e.detail.value!==e.target.__rendererValue&&(this._filterValue=e.detail.value)}__getHeader(e,t){return e||(t?this._generateHeader(t):void 0)}}customElements.define(b.is,b);
