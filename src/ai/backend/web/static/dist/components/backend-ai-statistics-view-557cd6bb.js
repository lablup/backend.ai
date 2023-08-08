import{i as t,r as e,am as i,an as n,ao as a,k as r,T as o,D as s,P as l,ap as d,aq as c,ar as u,X as h,V as m,as as p,ak as g,m as v,O as f,at as y,au as b,av as w,n as _,aw as x,ax as C,ay as T,E as k,q as D,az as M,al as S,v as E,u as U,_ as I,e as A,a as P,s as O,y as W,d as B,I as j,b as q,x as N,f as $,t as L,c as R,B as Y,g as z,o as F}from"./backend-ai-webui-661d9e43.js";import"./progress-spinner-153eedb3.js";import"./tab-group-6baff1e0.js";import"./mwc-tab-bar-064ccbb5.js";import{I as H}from"./vaadin-item-mixin-88cba3b7.js";import{g as K,s as G}from"./dir-utils-38e4cf3d.js";import{B as Q,M as X}from"./media-query-controller-e400dd2c.js";import"./chart-js-49cb22bc.js";import"./radio-behavior-b66ed7c9.js";const V=t`
  :host {
    -webkit-tap-highlight-color: transparent;
    --_lumo-item-selected-icon-display: var(--_lumo-list-box-item-selected-icon-display, block);
  }

  /* Dividers */
  [part='items'] ::slotted(hr) {
    height: 1px;
    border: 0;
    padding: 0;
    margin: var(--lumo-space-s) var(--lumo-border-radius-m);
    background-color: var(--lumo-contrast-10pct);
  }
`;e("vaadin-list-box",V,{moduleId:"lumo-list-box"}),
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
e("vaadin-select-item",i,{moduleId:"lumo-select-item"}),e("vaadin-select-list-box",V,{moduleId:"lumo-select-list-box"});e("vaadin-select",[n,t`
  :host(:not([theme*='align'])) ::slotted([slot='value']) {
    text-align: start;
  }

  [part='input-field'] {
    cursor: var(--lumo-clickable-cursor);
  }

  [part='input-field'] ::slotted([slot='value']) {
    font-weight: 500;
  }

  [part='input-field'] ::slotted([slot='value']:not([placeholder])) {
    color: var(--lumo-body-text-color);
  }

  :host([readonly]) [part='input-field'] ::slotted([slot='value']:not([placeholder])) {
    color: var(--lumo-secondary-text-color);
  }

  /* placeholder styles */
  [part='input-field'] ::slotted([slot='value'][placeholder]) {
    color: var(--lumo-secondary-text-color);
  }

  :host(:is([readonly], [disabled])) ::slotted([slot='value'][placeholder]) {
    opacity: 0;
  }

  [part='toggle-button']::before {
    content: var(--lumo-icons-dropdown);
  }

  /* Highlight the toggle button when hovering over the entire component */
  :host(:hover:not([readonly]):not([disabled])) [part='toggle-button'] {
    color: var(--lumo-contrast-80pct);
  }

  :host([theme~='small']) [part='input-field'] ::slotted([slot='value']) {
    --_lumo-selected-item-height: var(--lumo-size-s);
    --_lumo-selected-item-padding: 0;
  }
`],{moduleId:"lumo-select"}),e("vaadin-select-value-button",t`
    :host {
      font-family: var(--lumo-font-family);
      font-size: var(--lumo-font-size-m);
      padding: 0 0.25em;
      --_lumo-selected-item-height: var(--lumo-size-m);
      --_lumo-selected-item-padding: 0.5em;
    }

    ::slotted(*) {
      min-height: var(--_lumo-selected-item-height);
      padding-top: var(--_lumo-selected-item-padding);
      padding-bottom: var(--_lumo-selected-item-padding);
    }

    ::slotted(*:hover) {
      background-color: transparent;
    }
  `,{moduleId:"lumo-select-value-button"});e("vaadin-select-overlay",[a,t`
  :host {
    --_lumo-item-selected-icon-display: block;
  }

  [part~='overlay'] {
    min-width: var(--vaadin-select-text-field-width);
  }

  /* Small viewport adjustment */
  :host([phone]) {
    top: 0 !important;
    right: 0 !important;
    bottom: var(--vaadin-overlay-viewport-bottom, 0) !important;
    left: 0 !important;
    align-items: stretch;
    justify-content: flex-end;
  }

  :host([theme~='align-left']) {
    text-align: left;
  }

  :host([theme~='align-right']) {
    text-align: right;
  }

  :host([theme~='align-center']) {
    text-align: center;
  }
`],{moduleId:"lumo-select-overlay"});
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
class J extends(H(o(s(l)))){static get is(){return"vaadin-select-item"}static get template(){return r`
      <style>
        :host {
          display: inline-block;
        }

        :host([hidden]) {
          display: none !important;
        }
      </style>
      <span part="checkmark" aria-hidden="true"></span>
      <div part="content">
        <slot></slot>
      </div>
    `}ready(){super.ready(),this.setAttribute("role","option")}}customElements.define(J.is,J);
/**
 * @license
 * Copyright (c) 2022 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const Z=t=>class extends(d(t)){get focused(){return(this._getItems()||[]).find(c)}get _vertical(){return!0}focus(){const t=this._getItems();if(Array.isArray(t)){const e=this._getAvailableIndex(t,0,null,(t=>!u(t)));e>=0&&t[e].focus()}}_getItems(){return Array.from(this.children)}_onKeyDown(t){if(super._onKeyDown(t),t.metaKey||t.ctrlKey)return;const{key:e}=t,i=this._getItems()||[],n=i.indexOf(this.focused);let a,r;const o=!this._vertical&&"rtl"===this.getAttribute("dir")?-1:1;this.__isPrevKey(e)?(r=-o,a=n-o):this.__isNextKey(e)?(r=o,a=n+o):"Home"===e?(r=1,a=0):"End"===e&&(r=-1,a=i.length-1),a=this._getAvailableIndex(i,a,r,(t=>!u(t))),a>=0&&(t.preventDefault(),this._focus(a,!0))}__isPrevKey(t){return this._vertical?"ArrowUp"===t:"ArrowLeft"===t}__isNextKey(t){return this._vertical?"ArrowDown"===t:"ArrowRight"===t}_focus(t,e=!1){const i=this._getItems();this._focusItem(i[t],e)}_focusItem(t){t&&(t.focus(),t.setAttribute("focus-ring",""))}_getAvailableIndex(t,e,i,n){const a=t.length;let r=e;for(let e=0;"number"==typeof r&&e<a;e+=1,r+=i||1){r<0?r=a-1:r>=a&&(r=0);const e=t[r];if(!e.hasAttribute("disabled")&&this.__isMatchingItem(e,n))return r}return-1}__isMatchingItem(t,e){return"function"!=typeof e||e(t)}}
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,tt=t=>class extends(Z(t)){static get properties(){return{_hasVaadinListMixin:{value:!0},disabled:{type:Boolean,value:!1,reflectToAttribute:!0},selected:{type:Number,reflectToAttribute:!0,notify:!0},orientation:{type:String,reflectToAttribute:!0,value:""},items:{type:Array,readOnly:!0,notify:!0},_searchBuf:{type:String,value:""}}}static get observers(){return["_enhanceItems(items, orientation, selected, disabled)"]}get _isRTL(){return!this._vertical&&"rtl"===this.getAttribute("dir")}get _scrollerElement(){return console.warn(`Please implement the '_scrollerElement' property in <${this.localName}>`),this}get _vertical(){return"horizontal"!==this.orientation}focus(){this._observer&&this._observer.flush();const t=this.querySelector('[tabindex="0"]')||(this.items?this.items[0]:null);this._focusItem(t)}ready(){super.ready(),this.addEventListener("click",(t=>this._onClick(t))),this._observer=new h(this,(()=>{this._setItems(this._filterItems(h.getFlattenedNodes(this)))}))}_getItems(){return this.items}_enhanceItems(t,e,i,n){if(!n&&t){this.setAttribute("aria-orientation",e||"vertical"),t.forEach((t=>{e?t.setAttribute("orientation",e):t.removeAttribute("orientation")})),this._setFocusable(i||0);const n=t[i];t.forEach((t=>{t.selected=t===n})),n&&!n.disabled&&this._scrollToItem(i)}}_filterItems(t){return t.filter((t=>t._hasVaadinItemMixin))}_onClick(t){if(t.metaKey||t.shiftKey||t.ctrlKey||t.defaultPrevented)return;const e=this._filterItems(t.composedPath())[0];let i;e&&!e.disabled&&(i=this.items.indexOf(e))>=0&&(this.selected=i)}_searchKey(t,e){this._searchReset=m.debounce(this._searchReset,p.after(500),(()=>{this._searchBuf=""})),this._searchBuf+=e.toLowerCase(),this.items.some((t=>this.__isMatchingKey(t)))||(this._searchBuf=e.toLowerCase());const i=1===this._searchBuf.length?t+1:t;return this._getAvailableIndex(this.items,i,1,(t=>this.__isMatchingKey(t)&&"none"!==getComputedStyle(t).display))}__isMatchingKey(t){return t.textContent.replace(/[^\p{L}\p{Nd}]/gu,"").toLowerCase().startsWith(this._searchBuf)}_onKeyDown(t){if(t.metaKey||t.ctrlKey)return;const e=t.key,i=this.items.indexOf(this.focused);if(/[a-zA-Z0-9]/u.test(e)&&1===e.length){const t=this._searchKey(i,e);t>=0&&this._focus(t)}else super._onKeyDown(t)}_isItemHidden(t){return"none"===getComputedStyle(t).display}_setFocusable(t){t=this._getAvailableIndex(this.items,t,1);const e=this.items[t];this.items.forEach((t=>{t.tabIndex=t===e?0:-1}))}_focus(t){this.items.forEach(((e,i)=>{e.focused=i===t})),this._setFocusable(t),this._scrollToItem(t),super._focus(t)}_scrollToItem(t){const e=this.items[t];if(!e)return;const i=this._vertical?["top","bottom"]:this._isRTL?["right","left"]:["left","right"],n=this._scrollerElement.getBoundingClientRect(),a=(this.items[t+1]||e).getBoundingClientRect(),r=(this.items[t-1]||e).getBoundingClientRect();let o=0;!this._isRTL&&a[i[1]]>=n[i[1]]||this._isRTL&&a[i[1]]<=n[i[1]]?o=a[i[1]]-n[i[1]]:(!this._isRTL&&r[i[0]]<=n[i[0]]||this._isRTL&&r[i[0]]>=n[i[0]])&&(o=r[i[0]]-n[i[0]]),this._scroll(o)}_scroll(t){if(this._vertical)this._scrollerElement.scrollTop+=t;else{const e=this.getAttribute("dir")||"ltr",i=K(this._scrollerElement,e)+t;G(this._scrollerElement,e,i)}}}
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;class et extends(tt(o(s(g(l))))){static get is(){return"vaadin-select-list-box"}static get template(){return r`
      <style>
        :host {
          display: flex;
        }

        :host([hidden]) {
          display: none !important;
        }

        [part='items'] {
          height: 100%;
          width: 100%;
          overflow-y: auto;
          -webkit-overflow-scrolling: touch;
        }
      </style>
      <div part="items">
        <slot></slot>
      </div>
    `}static get properties(){return{orientation:{readOnly:!0}}}get _scrollerElement(){return this.shadowRoot.querySelector('[part="items"]')}ready(){super.ready(),this.setAttribute("role","listbox")}}customElements.define(et.is,et),
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
e("vaadin-select-overlay",t`
    :host {
      align-items: flex-start;
      justify-content: flex-start;
    }
  `,{moduleId:"vaadin-select-overlay-styles"});class it extends(v(f)){static get is(){return"vaadin-select-overlay"}requestContentUpdate(){if(super.requestContentUpdate(),this.owner){const t=this._getMenuElement();this.owner._assignMenuElement(t)}}_getMenuElement(){return Array.from(this.children).find((t=>"style"!==t.localName))}}customElements.define(it.is,it);
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
class nt extends(Q(o(l))){static get is(){return"vaadin-select-value-button"}static get template(){return r`
      <style>
        :host {
          display: inline-block;
          position: relative;
          outline: none;
          white-space: nowrap;
          -webkit-user-select: none;
          -moz-user-select: none;
          user-select: none;
          min-width: 0;
          width: 0;
        }

        ::slotted(*) {
          padding-left: 0;
          padding-right: 0;
          flex: auto;
        }

        /* placeholder styles */
        ::slotted(*:not([selected])) {
          line-height: 1;
        }

        .vaadin-button-container {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          text-align: inherit;
          width: 100%;
          height: 100%;
          min-height: inherit;
          text-shadow: inherit;
        }

        [part='label'] {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          width: 100%;
          line-height: inherit;
        }
      </style>
      <div class="vaadin-button-container">
        <span part="label">
          <slot></slot>
        </span>
      </div>
    `}}customElements.define(nt.is,nt);
/**
 * @license
 * Copyright (c) 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
class at extends y{constructor(t){super(t,"value","vaadin-select-value-button",{initializer:(t,e)=>{e._setFocusElement(t),e.ariaTarget=t,e.stateTarget=t,t.setAttribute("aria-haspopup","listbox")}})}}
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */e("vaadin-select",[b,w],{moduleId:"vaadin-select-styles"});class rt extends(_(x(C(d(T(k(o(l)))))))){static get is(){return"vaadin-select"}static get template(){return r`
      <style>
        ::slotted([slot='value']) {
          flex-grow: 1;
        }
      </style>

      <div class="vaadin-select-container">
        <div part="label" on-click="_onClick">
          <slot name="label"></slot>
          <span part="required-indicator" aria-hidden="true" on-click="focus"></span>
        </div>

        <vaadin-input-container
          part="input-field"
          readonly="[[readonly]]"
          disabled="[[disabled]]"
          invalid="[[invalid]]"
          theme$="[[_theme]]"
          on-click="_onClick"
        >
          <slot name="prefix" slot="prefix"></slot>
          <slot name="value"></slot>
          <div part="toggle-button" slot="suffix" aria-hidden="true" on-mousedown="_onToggleMouseDown"></div>
        </vaadin-input-container>

        <div part="helper-text">
          <slot name="helper"></slot>
        </div>

        <div part="error-message">
          <slot name="error-message"></slot>
        </div>
      </div>

      <vaadin-select-overlay
        position-target="[[_inputContainer]]"
        opened="{{opened}}"
        with-backdrop="[[_phone]]"
        phone$="[[_phone]]"
        theme$="[[_theme]]"
      ></vaadin-select-overlay>

      <slot name="tooltip"></slot>
    `}static get properties(){return{items:{type:Array,observer:"__itemsChanged"},opened:{type:Boolean,value:!1,notify:!0,reflectToAttribute:!0,observer:"_openedChanged"},renderer:Function,value:{type:String,value:"",notify:!0,observer:"_valueChanged"},name:{type:String},placeholder:{type:String},readonly:{type:Boolean,value:!1,reflectToAttribute:!0},_phone:Boolean,_phoneMediaQuery:{value:"(max-width: 420px), (max-height: 420px)"},_inputContainer:Object,_items:Object}}static get delegateAttrs(){return[...super.delegateAttrs,"invalid"]}static get observers(){return["_updateAriaExpanded(opened, focusElement)","_updateSelectedItem(value, _items, placeholder)","_rendererChanged(renderer, _overlayElement)"]}constructor(){super(),this._itemId=`value-${this.localName}-${D()}`}disconnectedCallback(){super.disconnectedCallback(),this.opened=!1}ready(){super.ready(),this._overlayElement=this.shadowRoot.querySelector("vaadin-select-overlay"),this._inputContainer=this.shadowRoot.querySelector('[part~="input-field"]'),this._valueButtonController=new at(this),this.addController(this._valueButtonController),this.addController(new X(this._phoneMediaQuery,(t=>{this._phone=t}))),M(this),this._tooltipController=new S(this),this._tooltipController.setPosition("top"),this.addController(this._tooltipController)}requestContentUpdate(){this._overlayElement&&(this._overlayElement.requestContentUpdate(),this._menuElement&&this._menuElement.items&&this._updateSelectedItem(this.value,this._menuElement.items))}_requiredChanged(t){super._requiredChanged(t),!1===t&&this.validate()}_rendererChanged(t,e){e&&(e.setProperties({owner:this,renderer:t||this.__defaultRenderer}),this.requestContentUpdate())}__itemsChanged(t,e){(t||e)&&this.requestContentUpdate()}_assignMenuElement(t){t&&t!==this.__lastMenuElement&&(this._menuElement=t,this.__initMenuItems(t),t.addEventListener("items-changed",(()=>{this.__initMenuItems(t)})),t.addEventListener("selected-changed",(()=>this.__updateValueButton())),t.addEventListener("keydown",(t=>this._onKeyDownInside(t)),!0),t.addEventListener("click",(()=>{this.__userInteraction=!0,this.opened=!1}),!0),this.__lastMenuElement=t)}__initMenuItems(t){t.items&&(this._items=t.items)}_valueChanged(t,e){this.toggleAttribute("has-value",Boolean(t)),void 0!==e&&this.validate()}_onClick(t){t.preventDefault(),this.opened=!this.readonly}_onToggleMouseDown(t){t.preventDefault()}_onKeyDown(t){if(t.target===this.focusElement&&!this.readonly&&!this.opened)if(/^(Enter|SpaceBar|\s|ArrowDown|Down|ArrowUp|Up)$/u.test(t.key))t.preventDefault(),this.opened=!0;else if(/[\p{L}\p{Nd}]/u.test(t.key)&&1===t.key.length){const e=this._menuElement.selected,i=void 0!==e?e:-1,n=this._menuElement._searchKey(i,t.key);n>=0&&(this.__userInteraction=!0,this._updateAriaLive(!0),this._menuElement.selected=n)}}_onKeyDownInside(t){/^(Tab)$/u.test(t.key)&&(this.opened=!1)}_openedChanged(t,e){if(t){if(this._updateAriaLive(!1),!this._overlayElement||!this._menuElement||!this.focusElement||this.disabled||this.readonly)return void(this.opened=!1);this._overlayElement.style.setProperty("--vaadin-select-text-field-width",`${this._inputContainer.offsetWidth}px`);const t=this.hasAttribute("focus-ring");this._openedWithFocusRing=t,t&&this.removeAttribute("focus-ring"),this._menuElement.focus()}else e&&(this.focus(),this._openedWithFocusRing&&this.setAttribute("focus-ring",""),this.validate())}_updateAriaExpanded(t,e){e&&e.setAttribute("aria-expanded",t?"true":"false")}_updateAriaLive(t){this.focusElement&&(t?this.focusElement.setAttribute("aria-live","polite"):this.focusElement.removeAttribute("aria-live"))}__attachSelectedItem(t){let e;const i=t.getAttribute("label");e=i?this.__createItemElement({label:i}):t.cloneNode(!0),e._sourceItem=t,this.__appendValueItemElement(e,this.focusElement),e.selected=!0}__createItemElement(t){const e=document.createElement(t.component||"vaadin-select-item");return t.label&&(e.textContent=t.label),t.value&&(e.value=t.value),t.disabled&&(e.disabled=t.disabled),e}__appendValueItemElement(t,e){e.appendChild(t),t.removeAttribute("tabindex"),t.removeAttribute("aria-selected"),t.removeAttribute("role"),t.setAttribute("id",this._itemId)}__updateValueButton(){const t=this.focusElement;if(!t)return;t.innerHTML="";const e=this._items[this._menuElement.selected];if(t.removeAttribute("placeholder"),e)this.__attachSelectedItem(e),this._valueChanging||(this._selectedChanging=!0,this.value=e.value||"",this.__userInteraction&&(this.opened=!1,this.dispatchEvent(new CustomEvent("change",{bubbles:!0})),this.__userInteraction=!1),delete this._selectedChanging);else if(this.placeholder){const e=this.__createItemElement({label:this.placeholder});this.__appendValueItemElement(e,t),t.setAttribute("placeholder","")}e||this.placeholder?E(t,"aria-labelledby",this._itemId):U(t,"aria-labelledby",this._itemId)}_updateSelectedItem(t,e){if(e){const i=null==t?t:t.toString();this._menuElement.selected=e.reduce(((t,e,n)=>void 0===t&&e.value===i?n:t),void 0),this._selectedChanging||(this._valueChanging=!0,this.__updateValueButton(),delete this._valueChanging)}}_shouldRemoveFocus(){return!this.opened}_setFocused(t){super._setFocused(t),t||this.validate()}checkValidity(){return!this.required||this.readonly||!!this.value}__defaultRenderer(t,e){if(!this.items||0===this.items.length)return void(t.textContent="");let i=t.firstElementChild;i||(i=document.createElement("vaadin-select-list-box"),t.appendChild(i)),i.textContent="",this.items.forEach((t=>{i.appendChild(this.__createItemElement(t))}))}}function ot(t,e){if(e.length<t)throw new TypeError(t+" argument"+(t>1?"s":"")+" required, but only "+e.length+" present")}function st(t){return st="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},st(t)}function lt(t){return lt="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},lt(t)}function dt(t){ot(1,arguments);var e=Object.prototype.toString.call(t);return t instanceof Date||"object"===lt(t)&&"[object Date]"===e?new Date(t.getTime()):"number"==typeof t||"[object Number]"===e?new Date(t):("string"!=typeof t&&"[object String]"!==e||"undefined"==typeof console||(console.warn("Starting with v2.0.0-beta.1 date-fns doesn't accept strings as date arguments. Please use `parseISO` to parse strings. See: https://github.com/date-fns/date-fns/blob/master/docs/upgradeGuide.md#string-arguments"),console.warn((new Error).stack)),new Date(NaN))}function ct(t){if(ot(1,arguments),!function(t){return ot(1,arguments),t instanceof Date||"object"===st(t)&&"[object Date]"===Object.prototype.toString.call(t)}(t)&&"number"!=typeof t)return!1;var e=dt(t);return!isNaN(Number(e))}function ut(t){if(null===t||!0===t||!1===t)return NaN;var e=Number(t);return isNaN(e)?e:e<0?Math.ceil(e):Math.floor(e)}function ht(t,e){return ot(2,arguments),function(t,e){ot(2,arguments);var i=dt(t).getTime(),n=ut(e);return new Date(i+n)}(t,-ut(e))}customElements.define(rt.is,rt);var mt=864e5;function pt(t){ot(1,arguments);var e=dt(t),i=e.getUTCDay(),n=(i<1?7:0)+i-1;return e.setUTCDate(e.getUTCDate()-n),e.setUTCHours(0,0,0,0),e}function gt(t){ot(1,arguments);var e=dt(t),i=e.getUTCFullYear(),n=new Date(0);n.setUTCFullYear(i+1,0,4),n.setUTCHours(0,0,0,0);var a=pt(n),r=new Date(0);r.setUTCFullYear(i,0,4),r.setUTCHours(0,0,0,0);var o=pt(r);return e.getTime()>=a.getTime()?i+1:e.getTime()>=o.getTime()?i:i-1}var vt=6048e5;function ft(t){ot(1,arguments);var e=dt(t),i=pt(e).getTime()-function(t){ot(1,arguments);var e=gt(t),i=new Date(0);return i.setUTCFullYear(e,0,4),i.setUTCHours(0,0,0,0),pt(i)}(e).getTime();return Math.round(i/vt)+1}var yt={};function bt(){return yt}function wt(t,e){var i,n,a,r,o,s,l,d;ot(1,arguments);var c=bt(),u=ut(null!==(i=null!==(n=null!==(a=null!==(r=null==e?void 0:e.weekStartsOn)&&void 0!==r?r:null==e||null===(o=e.locale)||void 0===o||null===(s=o.options)||void 0===s?void 0:s.weekStartsOn)&&void 0!==a?a:c.weekStartsOn)&&void 0!==n?n:null===(l=c.locale)||void 0===l||null===(d=l.options)||void 0===d?void 0:d.weekStartsOn)&&void 0!==i?i:0);if(!(u>=0&&u<=6))throw new RangeError("weekStartsOn must be between 0 and 6 inclusively");var h=dt(t),m=h.getUTCDay(),p=(m<u?7:0)+m-u;return h.setUTCDate(h.getUTCDate()-p),h.setUTCHours(0,0,0,0),h}function _t(t,e){var i,n,a,r,o,s,l,d;ot(1,arguments);var c=dt(t),u=c.getUTCFullYear(),h=bt(),m=ut(null!==(i=null!==(n=null!==(a=null!==(r=null==e?void 0:e.firstWeekContainsDate)&&void 0!==r?r:null==e||null===(o=e.locale)||void 0===o||null===(s=o.options)||void 0===s?void 0:s.firstWeekContainsDate)&&void 0!==a?a:h.firstWeekContainsDate)&&void 0!==n?n:null===(l=h.locale)||void 0===l||null===(d=l.options)||void 0===d?void 0:d.firstWeekContainsDate)&&void 0!==i?i:1);if(!(m>=1&&m<=7))throw new RangeError("firstWeekContainsDate must be between 1 and 7 inclusively");var p=new Date(0);p.setUTCFullYear(u+1,0,m),p.setUTCHours(0,0,0,0);var g=wt(p,e),v=new Date(0);v.setUTCFullYear(u,0,m),v.setUTCHours(0,0,0,0);var f=wt(v,e);return c.getTime()>=g.getTime()?u+1:c.getTime()>=f.getTime()?u:u-1}var xt=6048e5;function Ct(t,e){ot(1,arguments);var i=dt(t),n=wt(i,e).getTime()-function(t,e){var i,n,a,r,o,s,l,d;ot(1,arguments);var c=bt(),u=ut(null!==(i=null!==(n=null!==(a=null!==(r=null==e?void 0:e.firstWeekContainsDate)&&void 0!==r?r:null==e||null===(o=e.locale)||void 0===o||null===(s=o.options)||void 0===s?void 0:s.firstWeekContainsDate)&&void 0!==a?a:c.firstWeekContainsDate)&&void 0!==n?n:null===(l=c.locale)||void 0===l||null===(d=l.options)||void 0===d?void 0:d.firstWeekContainsDate)&&void 0!==i?i:1),h=_t(t,e),m=new Date(0);return m.setUTCFullYear(h,0,u),m.setUTCHours(0,0,0,0),wt(m,e)}(i,e).getTime();return Math.round(n/xt)+1}function Tt(t,e){for(var i=t<0?"-":"",n=Math.abs(t).toString();n.length<e;)n="0"+n;return i+n}var kt={y:function(t,e){var i=t.getUTCFullYear(),n=i>0?i:1-i;return Tt("yy"===e?n%100:n,e.length)},M:function(t,e){var i=t.getUTCMonth();return"M"===e?String(i+1):Tt(i+1,2)},d:function(t,e){return Tt(t.getUTCDate(),e.length)},a:function(t,e){var i=t.getUTCHours()/12>=1?"pm":"am";switch(e){case"a":case"aa":return i.toUpperCase();case"aaa":return i;case"aaaaa":return i[0];default:return"am"===i?"a.m.":"p.m."}},h:function(t,e){return Tt(t.getUTCHours()%12||12,e.length)},H:function(t,e){return Tt(t.getUTCHours(),e.length)},m:function(t,e){return Tt(t.getUTCMinutes(),e.length)},s:function(t,e){return Tt(t.getUTCSeconds(),e.length)},S:function(t,e){var i=e.length,n=t.getUTCMilliseconds();return Tt(Math.floor(n*Math.pow(10,i-3)),e.length)}},Dt="midnight",Mt="noon",St="morning",Et="afternoon",Ut="evening",It="night",At={G:function(t,e,i){var n=t.getUTCFullYear()>0?1:0;switch(e){case"G":case"GG":case"GGG":return i.era(n,{width:"abbreviated"});case"GGGGG":return i.era(n,{width:"narrow"});default:return i.era(n,{width:"wide"})}},y:function(t,e,i){if("yo"===e){var n=t.getUTCFullYear(),a=n>0?n:1-n;return i.ordinalNumber(a,{unit:"year"})}return kt.y(t,e)},Y:function(t,e,i,n){var a=_t(t,n),r=a>0?a:1-a;return"YY"===e?Tt(r%100,2):"Yo"===e?i.ordinalNumber(r,{unit:"year"}):Tt(r,e.length)},R:function(t,e){return Tt(gt(t),e.length)},u:function(t,e){return Tt(t.getUTCFullYear(),e.length)},Q:function(t,e,i){var n=Math.ceil((t.getUTCMonth()+1)/3);switch(e){case"Q":return String(n);case"QQ":return Tt(n,2);case"Qo":return i.ordinalNumber(n,{unit:"quarter"});case"QQQ":return i.quarter(n,{width:"abbreviated",context:"formatting"});case"QQQQQ":return i.quarter(n,{width:"narrow",context:"formatting"});default:return i.quarter(n,{width:"wide",context:"formatting"})}},q:function(t,e,i){var n=Math.ceil((t.getUTCMonth()+1)/3);switch(e){case"q":return String(n);case"qq":return Tt(n,2);case"qo":return i.ordinalNumber(n,{unit:"quarter"});case"qqq":return i.quarter(n,{width:"abbreviated",context:"standalone"});case"qqqqq":return i.quarter(n,{width:"narrow",context:"standalone"});default:return i.quarter(n,{width:"wide",context:"standalone"})}},M:function(t,e,i){var n=t.getUTCMonth();switch(e){case"M":case"MM":return kt.M(t,e);case"Mo":return i.ordinalNumber(n+1,{unit:"month"});case"MMM":return i.month(n,{width:"abbreviated",context:"formatting"});case"MMMMM":return i.month(n,{width:"narrow",context:"formatting"});default:return i.month(n,{width:"wide",context:"formatting"})}},L:function(t,e,i){var n=t.getUTCMonth();switch(e){case"L":return String(n+1);case"LL":return Tt(n+1,2);case"Lo":return i.ordinalNumber(n+1,{unit:"month"});case"LLL":return i.month(n,{width:"abbreviated",context:"standalone"});case"LLLLL":return i.month(n,{width:"narrow",context:"standalone"});default:return i.month(n,{width:"wide",context:"standalone"})}},w:function(t,e,i,n){var a=Ct(t,n);return"wo"===e?i.ordinalNumber(a,{unit:"week"}):Tt(a,e.length)},I:function(t,e,i){var n=ft(t);return"Io"===e?i.ordinalNumber(n,{unit:"week"}):Tt(n,e.length)},d:function(t,e,i){return"do"===e?i.ordinalNumber(t.getUTCDate(),{unit:"date"}):kt.d(t,e)},D:function(t,e,i){var n=function(t){ot(1,arguments);var e=dt(t),i=e.getTime();e.setUTCMonth(0,1),e.setUTCHours(0,0,0,0);var n=i-e.getTime();return Math.floor(n/mt)+1}(t);return"Do"===e?i.ordinalNumber(n,{unit:"dayOfYear"}):Tt(n,e.length)},E:function(t,e,i){var n=t.getUTCDay();switch(e){case"E":case"EE":case"EEE":return i.day(n,{width:"abbreviated",context:"formatting"});case"EEEEE":return i.day(n,{width:"narrow",context:"formatting"});case"EEEEEE":return i.day(n,{width:"short",context:"formatting"});default:return i.day(n,{width:"wide",context:"formatting"})}},e:function(t,e,i,n){var a=t.getUTCDay(),r=(a-n.weekStartsOn+8)%7||7;switch(e){case"e":return String(r);case"ee":return Tt(r,2);case"eo":return i.ordinalNumber(r,{unit:"day"});case"eee":return i.day(a,{width:"abbreviated",context:"formatting"});case"eeeee":return i.day(a,{width:"narrow",context:"formatting"});case"eeeeee":return i.day(a,{width:"short",context:"formatting"});default:return i.day(a,{width:"wide",context:"formatting"})}},c:function(t,e,i,n){var a=t.getUTCDay(),r=(a-n.weekStartsOn+8)%7||7;switch(e){case"c":return String(r);case"cc":return Tt(r,e.length);case"co":return i.ordinalNumber(r,{unit:"day"});case"ccc":return i.day(a,{width:"abbreviated",context:"standalone"});case"ccccc":return i.day(a,{width:"narrow",context:"standalone"});case"cccccc":return i.day(a,{width:"short",context:"standalone"});default:return i.day(a,{width:"wide",context:"standalone"})}},i:function(t,e,i){var n=t.getUTCDay(),a=0===n?7:n;switch(e){case"i":return String(a);case"ii":return Tt(a,e.length);case"io":return i.ordinalNumber(a,{unit:"day"});case"iii":return i.day(n,{width:"abbreviated",context:"formatting"});case"iiiii":return i.day(n,{width:"narrow",context:"formatting"});case"iiiiii":return i.day(n,{width:"short",context:"formatting"});default:return i.day(n,{width:"wide",context:"formatting"})}},a:function(t,e,i){var n=t.getUTCHours()/12>=1?"pm":"am";switch(e){case"a":case"aa":return i.dayPeriod(n,{width:"abbreviated",context:"formatting"});case"aaa":return i.dayPeriod(n,{width:"abbreviated",context:"formatting"}).toLowerCase();case"aaaaa":return i.dayPeriod(n,{width:"narrow",context:"formatting"});default:return i.dayPeriod(n,{width:"wide",context:"formatting"})}},b:function(t,e,i){var n,a=t.getUTCHours();switch(n=12===a?Mt:0===a?Dt:a/12>=1?"pm":"am",e){case"b":case"bb":return i.dayPeriod(n,{width:"abbreviated",context:"formatting"});case"bbb":return i.dayPeriod(n,{width:"abbreviated",context:"formatting"}).toLowerCase();case"bbbbb":return i.dayPeriod(n,{width:"narrow",context:"formatting"});default:return i.dayPeriod(n,{width:"wide",context:"formatting"})}},B:function(t,e,i){var n,a=t.getUTCHours();switch(n=a>=17?Ut:a>=12?Et:a>=4?St:It,e){case"B":case"BB":case"BBB":return i.dayPeriod(n,{width:"abbreviated",context:"formatting"});case"BBBBB":return i.dayPeriod(n,{width:"narrow",context:"formatting"});default:return i.dayPeriod(n,{width:"wide",context:"formatting"})}},h:function(t,e,i){if("ho"===e){var n=t.getUTCHours()%12;return 0===n&&(n=12),i.ordinalNumber(n,{unit:"hour"})}return kt.h(t,e)},H:function(t,e,i){return"Ho"===e?i.ordinalNumber(t.getUTCHours(),{unit:"hour"}):kt.H(t,e)},K:function(t,e,i){var n=t.getUTCHours()%12;return"Ko"===e?i.ordinalNumber(n,{unit:"hour"}):Tt(n,e.length)},k:function(t,e,i){var n=t.getUTCHours();return 0===n&&(n=24),"ko"===e?i.ordinalNumber(n,{unit:"hour"}):Tt(n,e.length)},m:function(t,e,i){return"mo"===e?i.ordinalNumber(t.getUTCMinutes(),{unit:"minute"}):kt.m(t,e)},s:function(t,e,i){return"so"===e?i.ordinalNumber(t.getUTCSeconds(),{unit:"second"}):kt.s(t,e)},S:function(t,e){return kt.S(t,e)},X:function(t,e,i,n){var a=(n._originalDate||t).getTimezoneOffset();if(0===a)return"Z";switch(e){case"X":return Ot(a);case"XXXX":case"XX":return Wt(a);default:return Wt(a,":")}},x:function(t,e,i,n){var a=(n._originalDate||t).getTimezoneOffset();switch(e){case"x":return Ot(a);case"xxxx":case"xx":return Wt(a);default:return Wt(a,":")}},O:function(t,e,i,n){var a=(n._originalDate||t).getTimezoneOffset();switch(e){case"O":case"OO":case"OOO":return"GMT"+Pt(a,":");default:return"GMT"+Wt(a,":")}},z:function(t,e,i,n){var a=(n._originalDate||t).getTimezoneOffset();switch(e){case"z":case"zz":case"zzz":return"GMT"+Pt(a,":");default:return"GMT"+Wt(a,":")}},t:function(t,e,i,n){var a=n._originalDate||t;return Tt(Math.floor(a.getTime()/1e3),e.length)},T:function(t,e,i,n){return Tt((n._originalDate||t).getTime(),e.length)}};function Pt(t,e){var i=t>0?"-":"+",n=Math.abs(t),a=Math.floor(n/60),r=n%60;if(0===r)return i+String(a);var o=e||"";return i+String(a)+o+Tt(r,2)}function Ot(t,e){return t%60==0?(t>0?"-":"+")+Tt(Math.abs(t)/60,2):Wt(t,e)}function Wt(t,e){var i=e||"",n=t>0?"-":"+",a=Math.abs(t);return n+Tt(Math.floor(a/60),2)+i+Tt(a%60,2)}var Bt=At,jt=function(t,e){switch(t){case"P":return e.date({width:"short"});case"PP":return e.date({width:"medium"});case"PPP":return e.date({width:"long"});default:return e.date({width:"full"})}},qt=function(t,e){switch(t){case"p":return e.time({width:"short"});case"pp":return e.time({width:"medium"});case"ppp":return e.time({width:"long"});default:return e.time({width:"full"})}},Nt={p:qt,P:function(t,e){var i,n=t.match(/(P+)(p+)?/)||[],a=n[1],r=n[2];if(!r)return jt(t,e);switch(a){case"P":i=e.dateTime({width:"short"});break;case"PP":i=e.dateTime({width:"medium"});break;case"PPP":i=e.dateTime({width:"long"});break;default:i=e.dateTime({width:"full"})}return i.replace("{{date}}",jt(a,e)).replace("{{time}}",qt(r,e))}},$t=Nt;var Lt=["D","DD"],Rt=["YY","YYYY"];function Yt(t,e,i){if("YYYY"===t)throw new RangeError("Use `yyyy` instead of `YYYY` (in `".concat(e,"`) for formatting years to the input `").concat(i,"`; see: https://github.com/date-fns/date-fns/blob/master/docs/unicodeTokens.md"));if("YY"===t)throw new RangeError("Use `yy` instead of `YY` (in `".concat(e,"`) for formatting years to the input `").concat(i,"`; see: https://github.com/date-fns/date-fns/blob/master/docs/unicodeTokens.md"));if("D"===t)throw new RangeError("Use `d` instead of `D` (in `".concat(e,"`) for formatting days of the month to the input `").concat(i,"`; see: https://github.com/date-fns/date-fns/blob/master/docs/unicodeTokens.md"));if("DD"===t)throw new RangeError("Use `dd` instead of `DD` (in `".concat(e,"`) for formatting days of the month to the input `").concat(i,"`; see: https://github.com/date-fns/date-fns/blob/master/docs/unicodeTokens.md"))}var zt={lessThanXSeconds:{one:"less than a second",other:"less than {{count}} seconds"},xSeconds:{one:"1 second",other:"{{count}} seconds"},halfAMinute:"half a minute",lessThanXMinutes:{one:"less than a minute",other:"less than {{count}} minutes"},xMinutes:{one:"1 minute",other:"{{count}} minutes"},aboutXHours:{one:"about 1 hour",other:"about {{count}} hours"},xHours:{one:"1 hour",other:"{{count}} hours"},xDays:{one:"1 day",other:"{{count}} days"},aboutXWeeks:{one:"about 1 week",other:"about {{count}} weeks"},xWeeks:{one:"1 week",other:"{{count}} weeks"},aboutXMonths:{one:"about 1 month",other:"about {{count}} months"},xMonths:{one:"1 month",other:"{{count}} months"},aboutXYears:{one:"about 1 year",other:"about {{count}} years"},xYears:{one:"1 year",other:"{{count}} years"},overXYears:{one:"over 1 year",other:"over {{count}} years"},almostXYears:{one:"almost 1 year",other:"almost {{count}} years"}},Ft=function(t,e,i){var n,a=zt[t];return n="string"==typeof a?a:1===e?a.one:a.other.replace("{{count}}",e.toString()),null!=i&&i.addSuffix?i.comparison&&i.comparison>0?"in "+n:n+" ago":n};function Ht(t){return function(){var e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:{},i=e.width?String(e.width):t.defaultWidth;return t.formats[i]||t.formats[t.defaultWidth]}}var Kt={date:Ht({formats:{full:"EEEE, MMMM do, y",long:"MMMM do, y",medium:"MMM d, y",short:"MM/dd/yyyy"},defaultWidth:"full"}),time:Ht({formats:{full:"h:mm:ss a zzzz",long:"h:mm:ss a z",medium:"h:mm:ss a",short:"h:mm a"},defaultWidth:"full"}),dateTime:Ht({formats:{full:"{{date}} 'at' {{time}}",long:"{{date}} 'at' {{time}}",medium:"{{date}}, {{time}}",short:"{{date}}, {{time}}"},defaultWidth:"full"})},Gt={lastWeek:"'last' eeee 'at' p",yesterday:"'yesterday at' p",today:"'today at' p",tomorrow:"'tomorrow at' p",nextWeek:"eeee 'at' p",other:"P"};function Qt(t){return function(e,i){var n;if("formatting"===(null!=i&&i.context?String(i.context):"standalone")&&t.formattingValues){var a=t.defaultFormattingWidth||t.defaultWidth,r=null!=i&&i.width?String(i.width):a;n=t.formattingValues[r]||t.formattingValues[a]}else{var o=t.defaultWidth,s=null!=i&&i.width?String(i.width):t.defaultWidth;n=t.values[s]||t.values[o]}return n[t.argumentCallback?t.argumentCallback(e):e]}}function Xt(t){return function(e){var i=arguments.length>1&&void 0!==arguments[1]?arguments[1]:{},n=i.width,a=n&&t.matchPatterns[n]||t.matchPatterns[t.defaultMatchWidth],r=e.match(a);if(!r)return null;var o,s=r[0],l=n&&t.parsePatterns[n]||t.parsePatterns[t.defaultParseWidth],d=Array.isArray(l)?function(t,e){for(var i=0;i<t.length;i++)if(e(t[i]))return i;return}(l,(function(t){return t.test(s)})):function(t,e){for(var i in t)if(t.hasOwnProperty(i)&&e(t[i]))return i;return}(l,(function(t){return t.test(s)}));return o=t.valueCallback?t.valueCallback(d):d,{value:o=i.valueCallback?i.valueCallback(o):o,rest:e.slice(s.length)}}}var Vt,Jt={code:"en-US",formatDistance:Ft,formatLong:Kt,formatRelative:function(t,e,i,n){return Gt[t]},localize:{ordinalNumber:function(t,e){var i=Number(t),n=i%100;if(n>20||n<10)switch(n%10){case 1:return i+"st";case 2:return i+"nd";case 3:return i+"rd"}return i+"th"},era:Qt({values:{narrow:["B","A"],abbreviated:["BC","AD"],wide:["Before Christ","Anno Domini"]},defaultWidth:"wide"}),quarter:Qt({values:{narrow:["1","2","3","4"],abbreviated:["Q1","Q2","Q3","Q4"],wide:["1st quarter","2nd quarter","3rd quarter","4th quarter"]},defaultWidth:"wide",argumentCallback:function(t){return t-1}}),month:Qt({values:{narrow:["J","F","M","A","M","J","J","A","S","O","N","D"],abbreviated:["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],wide:["January","February","March","April","May","June","July","August","September","October","November","December"]},defaultWidth:"wide"}),day:Qt({values:{narrow:["S","M","T","W","T","F","S"],short:["Su","Mo","Tu","We","Th","Fr","Sa"],abbreviated:["Sun","Mon","Tue","Wed","Thu","Fri","Sat"],wide:["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]},defaultWidth:"wide"}),dayPeriod:Qt({values:{narrow:{am:"a",pm:"p",midnight:"mi",noon:"n",morning:"morning",afternoon:"afternoon",evening:"evening",night:"night"},abbreviated:{am:"AM",pm:"PM",midnight:"midnight",noon:"noon",morning:"morning",afternoon:"afternoon",evening:"evening",night:"night"},wide:{am:"a.m.",pm:"p.m.",midnight:"midnight",noon:"noon",morning:"morning",afternoon:"afternoon",evening:"evening",night:"night"}},defaultWidth:"wide",formattingValues:{narrow:{am:"a",pm:"p",midnight:"mi",noon:"n",morning:"in the morning",afternoon:"in the afternoon",evening:"in the evening",night:"at night"},abbreviated:{am:"AM",pm:"PM",midnight:"midnight",noon:"noon",morning:"in the morning",afternoon:"in the afternoon",evening:"in the evening",night:"at night"},wide:{am:"a.m.",pm:"p.m.",midnight:"midnight",noon:"noon",morning:"in the morning",afternoon:"in the afternoon",evening:"in the evening",night:"at night"}},defaultFormattingWidth:"wide"})},match:{ordinalNumber:(Vt={matchPattern:/^(\d+)(th|st|nd|rd)?/i,parsePattern:/\d+/i,valueCallback:function(t){return parseInt(t,10)}},function(t){var e=arguments.length>1&&void 0!==arguments[1]?arguments[1]:{},i=t.match(Vt.matchPattern);if(!i)return null;var n=i[0],a=t.match(Vt.parsePattern);if(!a)return null;var r=Vt.valueCallback?Vt.valueCallback(a[0]):a[0];return{value:r=e.valueCallback?e.valueCallback(r):r,rest:t.slice(n.length)}}),era:Xt({matchPatterns:{narrow:/^(b|a)/i,abbreviated:/^(b\.?\s?c\.?|b\.?\s?c\.?\s?e\.?|a\.?\s?d\.?|c\.?\s?e\.?)/i,wide:/^(before christ|before common era|anno domini|common era)/i},defaultMatchWidth:"wide",parsePatterns:{any:[/^b/i,/^(a|c)/i]},defaultParseWidth:"any"}),quarter:Xt({matchPatterns:{narrow:/^[1234]/i,abbreviated:/^q[1234]/i,wide:/^[1234](th|st|nd|rd)? quarter/i},defaultMatchWidth:"wide",parsePatterns:{any:[/1/i,/2/i,/3/i,/4/i]},defaultParseWidth:"any",valueCallback:function(t){return t+1}}),month:Xt({matchPatterns:{narrow:/^[jfmasond]/i,abbreviated:/^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/i,wide:/^(january|february|march|april|may|june|july|august|september|october|november|december)/i},defaultMatchWidth:"wide",parsePatterns:{narrow:[/^j/i,/^f/i,/^m/i,/^a/i,/^m/i,/^j/i,/^j/i,/^a/i,/^s/i,/^o/i,/^n/i,/^d/i],any:[/^ja/i,/^f/i,/^mar/i,/^ap/i,/^may/i,/^jun/i,/^jul/i,/^au/i,/^s/i,/^o/i,/^n/i,/^d/i]},defaultParseWidth:"any"}),day:Xt({matchPatterns:{narrow:/^[smtwf]/i,short:/^(su|mo|tu|we|th|fr|sa)/i,abbreviated:/^(sun|mon|tue|wed|thu|fri|sat)/i,wide:/^(sunday|monday|tuesday|wednesday|thursday|friday|saturday)/i},defaultMatchWidth:"wide",parsePatterns:{narrow:[/^s/i,/^m/i,/^t/i,/^w/i,/^t/i,/^f/i,/^s/i],any:[/^su/i,/^m/i,/^tu/i,/^w/i,/^th/i,/^f/i,/^sa/i]},defaultParseWidth:"any"}),dayPeriod:Xt({matchPatterns:{narrow:/^(a|p|mi|n|(in the|at) (morning|afternoon|evening|night))/i,any:/^([ap]\.?\s?m\.?|midnight|noon|(in the|at) (morning|afternoon|evening|night))/i},defaultMatchWidth:"any",parsePatterns:{any:{am:/^a/i,pm:/^p/i,midnight:/^mi/i,noon:/^no/i,morning:/morning/i,afternoon:/afternoon/i,evening:/evening/i,night:/night/i}},defaultParseWidth:"any"})},options:{weekStartsOn:0,firstWeekContainsDate:1}},Zt=/[yYQqMLwIdDecihHKkms]o|(\w)\1*|''|'(''|[^'])+('|$)|./g,te=/P+p+|P+|p+|''|'(''|[^'])+('|$)|./g,ee=/^'([^]*?)'?$/,ie=/''/g,ne=/[a-zA-Z]/;function ae(t,e,i){var n,a,r,o,s,l,d,c,u,h,m,p,g,v,f,y,b,w;ot(2,arguments);var _=String(e),x=bt(),C=null!==(n=null!==(a=null==i?void 0:i.locale)&&void 0!==a?a:x.locale)&&void 0!==n?n:Jt,T=ut(null!==(r=null!==(o=null!==(s=null!==(l=null==i?void 0:i.firstWeekContainsDate)&&void 0!==l?l:null==i||null===(d=i.locale)||void 0===d||null===(c=d.options)||void 0===c?void 0:c.firstWeekContainsDate)&&void 0!==s?s:x.firstWeekContainsDate)&&void 0!==o?o:null===(u=x.locale)||void 0===u||null===(h=u.options)||void 0===h?void 0:h.firstWeekContainsDate)&&void 0!==r?r:1);if(!(T>=1&&T<=7))throw new RangeError("firstWeekContainsDate must be between 1 and 7 inclusively");var k=ut(null!==(m=null!==(p=null!==(g=null!==(v=null==i?void 0:i.weekStartsOn)&&void 0!==v?v:null==i||null===(f=i.locale)||void 0===f||null===(y=f.options)||void 0===y?void 0:y.weekStartsOn)&&void 0!==g?g:x.weekStartsOn)&&void 0!==p?p:null===(b=x.locale)||void 0===b||null===(w=b.options)||void 0===w?void 0:w.weekStartsOn)&&void 0!==m?m:0);if(!(k>=0&&k<=6))throw new RangeError("weekStartsOn must be between 0 and 6 inclusively");if(!C.localize)throw new RangeError("locale must contain localize property");if(!C.formatLong)throw new RangeError("locale must contain formatLong property");var D=dt(t);if(!ct(D))throw new RangeError("Invalid time value");var M=function(t){var e=new Date(Date.UTC(t.getFullYear(),t.getMonth(),t.getDate(),t.getHours(),t.getMinutes(),t.getSeconds(),t.getMilliseconds()));return e.setUTCFullYear(t.getFullYear()),t.getTime()-e.getTime()}(D),S=ht(D,M),E={firstWeekContainsDate:T,weekStartsOn:k,locale:C,_originalDate:D};return _.match(te).map((function(t){var e=t[0];return"p"===e||"P"===e?(0,$t[e])(t,C.formatLong):t})).join("").match(Zt).map((function(n){if("''"===n)return"'";var a=n[0];if("'"===a)return function(t){var e=t.match(ee);if(!e)return t;return e[1].replace(ie,"'")}
/**
 @license
 Copyright (c) 2015-2023 Lablup Inc. All rights reserved.
 */(n);var r,o=Bt[a];if(o)return null!=i&&i.useAdditionalWeekYearTokens||(r=n,-1===Rt.indexOf(r))||Yt(n,e,String(t)),null!=i&&i.useAdditionalDayOfYearTokens||!function(t){return-1!==Lt.indexOf(t)}(n)||Yt(n,e,String(t)),o(S,n,C.localize,E);if(a.match(ne))throw new RangeError("Format string contains an unescaped latin alphabet character `"+a+"`");return n})).join("")}const re={toB:t=>t,toKB:t=>t/1024,toMB:t=>t/1048576,toGB:t=>t/1073741824,toTB:t=>t/1099511627776,log1024:t=>t<=0?0:Math.log(t)/Math.log(1024),readableUnit:function(t){return["B","KB","MB","GB","TB"][Math.floor(this.log1024(t))]},scale:function(t,e=""){let i;return i=""===e?this.readableUnit(Math.min.apply(null,t.map((t=>t.y)))):"MB",{data:t.map((t=>({...t,y:this[`to${i}`](t.y)}))),unit:i}}},oe=t=>"string"!=typeof t?"":t.charAt(0).toUpperCase()+t.slice(1);let se=class extends O{constructor(){super()}firstUpdated(){var t;this.chart=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#chart"),this.collection.axisTitle.y&&(this.type="Sessions"==this.collection.axisTitle.y||"CPU"==this.collection.axisTitle.y?"bar":"line"),this._updateChartData()}_updateChartData(){"bytes"===this.collection.unit_hint&&this.scaleData();const t=this.collection.data[0].map((t=>ae(t.x,"MMM dd HH:mm"))),e={Sessions:"#ec407a",CPU:"#9ccc65",Memory:"#ffa726",GPU:"#26c6da","IO-Read":"#3677eb","IO-Write":"#003f5c"},i="1D"==this.collection.period?8:14,n="1D"==this.collection.period?0:50;this.chartData={labels:t,datasets:[{label:this.collection.axisTitle.y+" ("+this.collection.unit_hint+")",data:this.collection.data[0],barThickness:6,borderWidth:1,borderColor:e[this.collection.axisTitle.y],backgroundColor:e[this.collection.axisTitle.y],parsing:{xAxisKey:"x",yAxisKey:"y"}}]},this.options={responsive:!0,maintainAspectRatio:!1,legend:{display:!0},tooltips:{intersect:!1},scales:{x:{display:!0,ticks:{major:{enabled:!0},source:"data",autoSkip:!0,sampleSize:100,maxTicksLimit:i,maxRotation:n,font:function(t){const e=t.chart.width;return{size:Math.round(e/64)<12?Math.round(e/64):12}}},scaleLabel:{display:!0,align:"end",labelString:this.collection.axisTitle.x}},y:{responsive:!0,beginAtZero:!0,display:!0,ticks:{maxTicksLimit:5,callback:t=>{if(t%1==0)return t},font:function(t){const e=t.chart.height;return{size:Math.round(e/16)<12?Math.round(e/16):12}}},scaleLabel:{display:!0,labelString:oe(this.collection.unit_hint)}}}}}render(){return W`
      <div class="layout vertical center">
        <div id="ctn-chartjs${this.idx}">
        ${"bar"==this.type?W`<chart-js id="chart" type="bar" .data="${this.chartData}" .options="${this.options}"></chart-js>`:W`<chart-js id="chart" type="line" .data="${this.chartData}" .options="${this.options}"></chart-js>`}
        </div>
      </div>
    `}static get properties(){return{collection:{type:Object,hasChanged:(t,e)=>void 0===e||t.period!==e.period}}}static get is(){return"backend-ai-chart"}static get styles(){return[B,j,q]}updated(t){t.has("collection")&&void 0!==t.get("collection")&&this._updateChartData()}scaleData(){const t=this.collection.data.map((t=>re.scale(t,"MB")));this.collection.data=t.map((t=>t.data)),this.collection.unit_hint={B:"Bytes",KB:"KBytes",MB:"MB",GB:"GB",TB:"TB"}[t[0].unit]}};I([A({type:Number})],se.prototype,"idx",void 0),I([A({type:Object})],se.prototype,"collection",void 0),I([A({type:Object})],se.prototype,"chartData",void 0),I([A({type:Object})],se.prototype,"options",void 0),I([A({type:Object})],se.prototype,"chart",void 0),I([A({type:String})],se.prototype,"type",void 0),se=I([P("backend-ai-chart")],se);
/**
 @license
 Copyright (c) 2015-2020 Lablup Inc. All rights reserved.
 */
let le=class extends O{constructor(){super(),this.num_sessions=0,this.used_time="0:00:00.00",this.cpu_used_time="0:00:00.00",this.gpu_used_time="0:00:00.00",this.disk_used=0,this.traffic_used=0}static get styles(){return[j,q,N,$,t`
        wl-card {
          padding: 20px;
        }

        .value {
          padding: 15px;
          font-size: 25px;
          font-weight: bold;
        }

        .desc {
          padding: 0px 15px 20px 15px;
        }
      `]}firstUpdated(){this.formatting()}formatting(){this.used_time=this.usedTimeFormatting(this.used_time),this.cpu_used_time=this.usedTimeFormatting(this.cpu_used_time),this.gpu_used_time=this.usedTimeFormatting(this.gpu_used_time),this.disk_used=Math.floor(this.disk_used/10**9),this.traffic_used=Math.floor(this.traffic_used/2**20)}usedTimeFormatting(t){const e=parseInt(t.substring(0,t.indexOf(":")));let i=parseInt(t.substring(t.indexOf(":")+1,t.lastIndexOf(":")));return i=24*e+i,i+"h "+t.substring(t.lastIndexOf(":")+1,t.indexOf("."))+"m"}render(){return W`
      <wl-card>
        <wl-title level="3">${L("usagepanel.StatisticsForThisMonth")}</wl-title>
        <div class="horizontal layout">
          <div class="vertical center layout">
            <span class="value">${this.num_sessions}</span>
            <span class="desc">${L("usagepanel.NumSessions")}</span>
          </div>
          <div class="vertical center layout">
            <span class="value">${this.used_time}</span>
            <span class="desc">${L("usagepanel.UsedTime")}</span>
          </div>
          <div class="vertical center layout">
            <span class="value">${this.cpu_used_time}</span>
            <span class="desc">${L("usagepanel.CpuUsedTime")}</span>
          </div>
          <div class="vertical center layout">
            <span class="value">${this.gpu_used_time}</span>
            <span class="desc">${L("usagepanel.GpuUsedTime")}</span>
          </div>
          <div class="vertical center layout">
            <span class="value">${this.disk_used}GB</span>
            <span class="desc">${L("usagepanel.DiskUsed")}</span>
          </div>
          <div class="vertical center layout">
            <span class="value">${this.traffic_used}MiB</span>
            <span class="desc">${L("usagepanel.TrafficUsed")}</span>
          </div>
        </div>
      </wl-card>
    `}};I([A({type:Number})],le.prototype,"num_sessions",void 0),I([A({type:String})],le.prototype,"used_time",void 0),I([A({type:String})],le.prototype,"cpu_used_time",void 0),I([A({type:String})],le.prototype,"gpu_used_time",void 0),I([A({type:Number})],le.prototype,"disk_used",void 0),I([A({type:Number})],le.prototype,"traffic_used",void 0),le=I([P("backend-ai-monthly-usage-panel")],le);
/**
 @license
 Copyright (c) 2015-2023 Lablup Inc. All rights reserved.
 */
let de=class extends Y{constructor(){super(),this._map={num_sessions:"Sessions",cpu_allocated:"CPU",mem_allocated:"Memory",gpu_allocated:"GPU",io_read_bytes:"IO-Read",io_write_bytes:"IO-Write"},this.templates={"1D":{interval:1,length:96},"1W":{interval:1,length:672}},this.periodSelectItems=new Array,this.collection=Object(),this.period="1D",this.updating=!1,this.elapsedDays=0,this._helpDescription="",this._helpDescriptionTitle="",this._helpDescriptionIcon="",this.data=[]}static get styles(){return[B,j,q,N,$,t`
        vaadin-select {
          font-size: 14px;
        }

        vaadin-select-item {
          font-size: 14px;
          --lumo-font-family: var(--general-font-family) !important;
        }

        #select-period {
          font-size: 12px;
          color: #8c8484;
          padding-left: 20px;
          padding-right: 8px;
        }

        #help-description {
          --component-width: 70vw;
          --component-padding: 20px 40px;
        }
      `]}attributeChangedCallback(t,e,i){var n;"active"===t&&null!==i?(this.active||this._menuChanged(!0),this.active=!0):(this.active=!1,this._menuChanged(!1),null===(n=this.shadowRoot)||void 0===n||n.querySelectorAll("backend-ai-chart").forEach((t=>{t.wipe()}))),super.attributeChangedCallback(t,e,i)}async _menuChanged(t){var e;await this.updateComplete,!1!==t?this.init():null===(e=this.shadowRoot)||void 0===e||e.querySelectorAll("backend-ai-chart").forEach((t=>{t.wipe()}))}async _viewStateChanged(t){await this.updateComplete,!1!==t&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._getUserInfo(),this.init()}),!0):(this._getUserInfo(),this.init()))}_getUserInfo(){globalThis.backendaiclient.keypair.info(globalThis.backendaiclient._config.accessKey,["created_at"]).then((t=>{const e=t.keypair.created_at,i=new Date(e),n=new Date,a=Math.floor((n.getTime()-i.getTime())/1e3),r=Math.floor(a/86400);this.elapsedDays=r;const o=[{label:z("statistics.1Day"),value:"1D"}];this.elapsedDays>7&&o.push({label:z("statistics.1Week"),value:"1W"}),this.periodSelectItems=o,this.periodSelec.value="1D"}))}init(){if(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready)document.addEventListener("backend-ai-connected",(()=>{this.updating||(this.updating=!0,this.readUserStat().then((t=>{var e;null===(e=this.shadowRoot)||void 0===e||e.querySelectorAll("backend-ai-chart").forEach((t=>{t.init()})),this.updating=!1})).catch((t=>{this.updating=!1})))}),!0);else{if(this.updating)return;this.updating=!0,this.readUserStat().then((t=>{var e;null===(e=this.shadowRoot)||void 0===e||e.querySelectorAll("backend-ai-chart").forEach((t=>{t.init()})),this.updating=!1})).catch((t=>{this.updating=!1}))}}readUserStat(){return globalThis.backendaiclient.resources.user_stats().then((t=>{const{period:e,templates:i}=this;this.data=t;const n={};return n[e]={},Object.keys(this._map).forEach((a=>{n[e][a]={data:[t.filter(((n,a)=>t.length-i[e].length<=a)).map((t=>({x:new Date(1e3*t.date),y:t[a].value})))],labels:[t.filter(((n,a)=>t.length-i[e].length<=a)).map((t=>new Date(1e3*t.date).toString()))],axisTitle:{x:"Date",y:this._map[a]},period:e,unit_hint:t[0][a].unit_hint}})),this.collection=n,this.updateComplete})).catch((t=>{console.log(t)}))}pulldownChange(t){this.period=t.target.value;const{data:e,period:i,collection:n,_map:a,templates:r}=this;i in n||(n[i]={},Object.keys(a).forEach((t=>{n[i][t]={data:[e.filter(((t,n)=>e.length-r[i].length<=n)).map((e=>({x:new Date(1e3*e.date),y:e[t].value})))],axisTitle:{x:"Date",y:a[t]},period:i,unit_hint:e[e.length-1][t].unit_hint}})))}_launchUsageHistoryInfoDialog(){this._helpDescriptionTitle=z("statistics.UsageHistory"),this._helpDescription=`\n      <div class="note-container">\n        <div class="note-title">\n          <mwc-icon class="fg white">info</mwc-icon>\n          <div>Note</div>\n        </div>\n        <div class="note-contents">${z("statistics.UsageHistoryNote")}</div>\n      </div>\n      <p>${z("statistics.UsageHistoryDesc")}</p>\n      <strong>Sessions</strong>\n      <p>${z("statistics.SessionsDesc")}</p>\n      <strong>CPU</strong>\n      <p>${z("statistics.CPUDesc")}</p>\n      <strong>Memory</strong>\n      <p>${z("statistics.MemoryDesc")}</p>\n      <strong>GPU</strong>\n      <p>${z("statistics.GPUDesc")}</p>\n      <strong>IO-Read</strong>\n      <p>${z("statistics.IOReadDesc")}</p>\n      <strong>IO-Write</strong>\n      <p>${z("statistics.IOWriteDesc")}</p>\n    `,this.helpDescriptionDialog.show()}render(){return W`
      <link rel="stylesheet" href="resources/custom.css">
      <div class="card" elevation="0">
        <!--<backend-ai-monthly-usage-panel></backend-ai-monthly-usage-panel>-->
        <div class="horizontal layout center">
          <p id="select-period">${L("statistics.SelectPeriod")}</p>
          <vaadin-select id="period-selector" .items="${this.periodSelectItems}" @change="${t=>this.pulldownChange(t)}"></vaadin-select>
          <mwc-icon-button class="fg green" icon="info" @click="${()=>this._launchUsageHistoryInfoDialog()}"></mwc-icon-button>
        </div>
        ${Object.keys(this.collection).length>0?Object.keys(this._map).map(((t,e)=>W`
              <h3 class="horizontal center layout">
                <span style="color:#222222;">${this._map[t]}</span>
                <span class="flex"></span>
              </h3>
              <div style="width:100%;min-height:180px;">
                <backend-ai-chart
                  idx=${e}
                  .collection=${this.collection[this.period][t]}
                ></backend-ai-chart>
              </div>
            `)):W``}
      </div>
      <backend-ai-dialog id="help-description" fixed backdrop>
        <span slot="title">${this._helpDescriptionTitle}</span>
        <div slot="content" class="horizontal layout center" style="margin:5px;">
        ${""==this._helpDescriptionIcon?W``:W`
          <img slot="graphic" alt="help icon" src="resources/icons/${this._helpDescriptionIcon}"
               style="width:64px;height:64px;margin-right:10px;"/>
        `}
          <div style="font-size:14px;">${F(this._helpDescription)}</div>
        </div>
      </backend-ai-dialog>
    `}};I([A({type:Object})],de.prototype,"_map",void 0),I([A({type:Object})],de.prototype,"templates",void 0),I([A({type:Array})],de.prototype,"periodSelectItems",void 0),I([A({type:Object})],de.prototype,"collection",void 0),I([A({type:String})],de.prototype,"period",void 0),I([A({type:Boolean})],de.prototype,"updating",void 0),I([A({type:Number})],de.prototype,"elapsedDays",void 0),I([A({type:String})],de.prototype,"_helpDescription",void 0),I([A({type:String})],de.prototype,"_helpDescriptionTitle",void 0),I([A({type:String})],de.prototype,"_helpDescriptionIcon",void 0),I([R("#period-selector")],de.prototype,"periodSelec",void 0),I([R("#help-description")],de.prototype,"helpDescriptionDialog",void 0),de=I([P("backend-ai-usage-list")],de);
/**
 @license
 Copyright (c) 2015-2023 Lablup Inc. All rights reserved.
 */
let ce=class extends Y{constructor(){super(...arguments),this._status="inactive"}static get styles(){return[B,j,q,N,$,t`
        wl-card h3.tab {
          padding-top: 0;
          padding-bottom: 0;
          padding-left: 0;
        }
        wl-tab-group {
          --tab-group-indicator-bg: var(--paper-cyan-500);
        }

        wl-tab {
          --tab-color: #666;
          --tab-color-hover: #222;
          --tab-color-hover-filled: #222;
          --tab-color-active: #222;
          --tab-color-active-hover: #222;
          --tab-color-active-filled: #ccc;
          --tab-bg-active: var(--paper-cyan-50);
          --tab-bg-filled: var(--paper-cyan-50);
          --tab-bg-active-hover: var(--paper-cyan-100);
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

        .tab-content {
          width: 100%;
        }
      `]}async _viewStateChanged(t){var e;await this.updateComplete,!1!==t?((null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#usage-list")).setAttribute("active","true"),this._status="active"):this._status="inactive"}_showTab(t){var e,i,n;const a=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll(".tab-content");for(const t of Array.from(a))t.style.display="none";(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+t.title+"-stat")).style.display="block",a.forEach((t=>{t.children[0].removeAttribute("active")})),(null===(n=this.shadowRoot)||void 0===n?void 0:n.querySelector(`#${t.title}-list`)).setAttribute("active","true")}render(){return W`
        <lablup-activity-panel elevation="1" noheader narrow autowidth>
          <div slot="message">
            <h3 class="tab horizontal center layout">
              <mwc-tab-bar>
                <mwc-tab title="usage" label="${L("statistics.UsageHistory")}"></mwc-tab>
              </mwc-tab-bar>
            </h3>
            <div class="horizontal wrap layout">
              <div id="usage-stat" class="tab-content">
                <backend-ai-usage-list id="usage-list"><wl-progress-spinner active></wl-progress-spinner></backend-ai-usage-list>
              </div>
            </div>
          </div>
        </lablup-activity-panel>
      `}};I([A({type:String})],ce.prototype,"_status",void 0),ce=I([P("backend-ai-statistics-view")],ce);var ue=ce;export{ue as default};
