import{r as e,i as t,aN as r,ax as i,bg as o,by as s,aq as n,bz as a,aw as l,b4 as d,b5 as h,k as c,al as _,E as u,T as p,P as g,v as m,u as f,az as b,V as v,W as C,D as w,bA as y,as as x,X as z,w as E,Y as A,ak as I,bB as R,bC as S,b0 as F,aZ as T,bD as k,bE as $,bF as P,bG as D}from"./backend-ai-webui-661d9e43.js";import{A as O,a as L,g as N}from"./dir-utils-38e4cf3d.js";e("vaadin-checkbox",t`
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
      box-shadow: 0 0 0 1px var(--lumo-base-color), 0 0 0 3px var(--lumo-primary-color-50pct);
    }

    /* Disabled */
    :host([disabled]) {
      pointer-events: none;
      color: var(--lumo-disabled-text-color);
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
const H=r((e=>class extends(i(o(s(e)))){static get properties(){return{checked:{type:Boolean,value:!1,notify:!0,reflectToAttribute:!0}}}static get delegateProps(){return[...super.delegateProps,"checked"]}_onChange(e){const t=e.target;this._toggleChecked(t.checked),n(t)||t.focus()}_toggleChecked(e){this.checked=e}})),B=e=>class extends(a(H(l(O(e))))){static get properties(){return{indeterminate:{type:Boolean,notify:!0,value:!1,reflectToAttribute:!0},name:{type:String,value:""}}}static get delegateProps(){return[...super.delegateProps,"indeterminate"]}static get delegateAttrs(){return[...super.delegateAttrs,"name"]}constructor(){super(),this._setType("checkbox"),this.value="on"}ready(){super.ready(),this.addController(new d(this,(e=>{this._setInputElement(e),this._setFocusElement(e),this.stateTarget=e,this.ariaTarget=e}))),this.addController(new h(this.inputElement,this._labelController))}_shouldSetActive(e){return"a"!==e.target.localName&&super._shouldSetActive(e)}_toggleChecked(e){this.indeterminate&&(this.indeterminate=!1),super._toggleChecked(e)}}
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
e("vaadin-checkbox",t`
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
`,{moduleId:"vaadin-checkbox-styles"});class M extends(B(u(p(g)))){static get is(){return"vaadin-checkbox"}static get template(){return c`
      <div class="vaadin-checkbox-container">
        <div part="checkbox" aria-hidden="true"></div>
        <slot name="input"></slot>
        <slot name="label"></slot>
      </div>
      <slot name="tooltip"></slot>
    `}ready(){super.ready(),this._tooltipController=new _(this),this.addController(this._tooltipController)}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
function G(e){return Array.from(e.querySelectorAll('[part~="cell"]:not([part~="details-cell"])'))}function U(e,t){[...e.children].forEach(t)}function W(e,t,r){let i=1;e.forEach((e=>{i%10==0&&(i+=1),e._order=r+i*t,i+=1}))}function V(e,t,r){switch(typeof r){case"boolean":e.toggleAttribute(t,r);break;case"string":e.setAttribute(t,r);break;default:e.removeAttribute(t)}}function q(e,t,r){t||""===t?m(e,"part",r):f(e,"part",r)}function K(e,t,r){e.forEach((e=>{q(e,r,t)}))}function j(e,t,r){const i=G(e);Object.entries(t).forEach((([t,o])=>{V(e,t,o);const s=r?`${t}-${o}-row`:`${t}-row`;q(e,o,s),K(i,`${s}-cell`,o)}))}function X(e,t,r,i,o){V(e,t,r),o&&q(e,!1,o),q(e,r,i||`${t}-cell`)}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */customElements.define(M.is,M),e("vaadin-grid",t`
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
  `,{moduleId:"lumo-grid"});const Y=e=>class extends e{static get properties(){return{resizable:{type:Boolean,value(){if("vaadin-grid-column-group"===this.localName)return;const e=this.parentNode;return e&&"vaadin-grid-column-group"===e.localName&&e.resizable||!1}},frozen:{type:Boolean,value:!1},frozenToEnd:{type:Boolean,value:!1},hidden:{type:Boolean,value:!1},header:{type:String},textAlign:{type:String},_lastFrozen:{type:Boolean,value:!1},_firstFrozenToEnd:{type:Boolean,value:!1},_order:Number,_reorderStatus:Boolean,_emptyCells:Array,_headerCell:Object,_footerCell:Object,_grid:Object,__initialized:{type:Boolean,value:!0},headerRenderer:Function,_headerRenderer:{type:Function,computed:"_computeHeaderRenderer(headerRenderer, header, __initialized)"},footerRenderer:Function,_footerRenderer:{type:Function,computed:"_computeFooterRenderer(footerRenderer, __initialized)"},__gridColumnElement:{type:Boolean,value:!0}}}static get observers(){return["_widthChanged(width, _headerCell, _footerCell, _cells.*)","_frozenChanged(frozen, _headerCell, _footerCell, _cells.*)","_frozenToEndChanged(frozenToEnd, _headerCell, _footerCell, _cells.*)","_flexGrowChanged(flexGrow, _headerCell, _footerCell, _cells.*)","_textAlignChanged(textAlign, _cells.*, _headerCell, _footerCell)","_orderChanged(_order, _headerCell, _footerCell, _cells.*)","_lastFrozenChanged(_lastFrozen)","_firstFrozenToEndChanged(_firstFrozenToEnd)","_onRendererOrBindingChanged(_renderer, _cells, _cells.*, path)","_onHeaderRendererOrBindingChanged(_headerRenderer, _headerCell, path, header)","_onFooterRendererOrBindingChanged(_footerRenderer, _footerCell)","_resizableChanged(resizable, _headerCell)","_reorderStatusChanged(_reorderStatus, _headerCell, _footerCell, _cells.*)","_hiddenChanged(hidden, _headerCell, _footerCell, _cells.*)"]}get _grid(){return this._gridValue||(this._gridValue=this._findHostGrid()),this._gridValue}get _allCells(){return[].concat(this._cells||[]).concat(this._emptyCells||[]).concat(this._headerCell).concat(this._footerCell).filter((e=>e))}connectedCallback(){super.connectedCallback(),requestAnimationFrame((()=>{this._grid&&this._allCells.forEach((e=>{e._content.parentNode||this._grid.appendChild(e._content)}))}))}disconnectedCallback(){super.disconnectedCallback(),requestAnimationFrame((()=>{this._grid||this._allCells.forEach((e=>{e._content.parentNode&&e._content.parentNode.removeChild(e._content)}))})),this._gridValue=void 0}ready(){super.ready(),b(this)}_findHostGrid(){let e=this;for(;e&&!/^vaadin.*grid(-pro)?$/u.test(e.localName);)e=e.assignedSlot?e.assignedSlot.parentNode:e.parentNode;return e||void 0}_renderHeaderAndFooter(){this._renderHeaderCellContent(this._headerRenderer,this._headerCell),this._renderFooterCellContent(this._footerRenderer,this._footerCell)}_flexGrowChanged(e){this.parentElement&&this.parentElement._columnPropChanged&&this.parentElement._columnPropChanged("flexGrow"),this._allCells.forEach((t=>{t.style.flexGrow=e}))}_orderChanged(e){this._allCells.forEach((t=>{t.style.order=e}))}_widthChanged(e){this.parentElement&&this.parentElement._columnPropChanged&&this.parentElement._columnPropChanged("width"),this._allCells.forEach((t=>{t.style.width=e}))}_frozenChanged(e){this.parentElement&&this.parentElement._columnPropChanged&&this.parentElement._columnPropChanged("frozen",e),this._allCells.forEach((t=>{X(t,"frozen",e)})),this._grid&&this._grid._frozenCellsChanged&&this._grid._frozenCellsChanged()}_frozenToEndChanged(e){this.parentElement&&this.parentElement._columnPropChanged&&this.parentElement._columnPropChanged("frozenToEnd",e),this._allCells.forEach((t=>{this._grid&&t.parentElement===this._grid.$.sizer||X(t,"frozen-to-end",e)})),this._grid&&this._grid._frozenCellsChanged&&this._grid._frozenCellsChanged()}_lastFrozenChanged(e){this._allCells.forEach((t=>{X(t,"last-frozen",e)})),this.parentElement&&this.parentElement._columnPropChanged&&(this.parentElement._lastFrozen=e)}_firstFrozenToEndChanged(e){this._allCells.forEach((t=>{this._grid&&t.parentElement===this._grid.$.sizer||X(t,"first-frozen-to-end",e)})),this.parentElement&&this.parentElement._columnPropChanged&&(this.parentElement._firstFrozenToEnd=e)}_generateHeader(e){return e.substr(e.lastIndexOf(".")+1).replace(/([A-Z])/gu,"-$1").toLowerCase().replace(/-/gu," ").replace(/^./u,(e=>e.toUpperCase()))}_reorderStatusChanged(e){const t=this.__previousReorderStatus,r=t?`reorder-${t}-cell`:"",i=`reorder-${e}-cell`;this._allCells.forEach((t=>{X(t,"reorder-status",e,i,r)})),this.__previousReorderStatus=e}_resizableChanged(e,t){void 0!==e&&void 0!==t&&t&&[t].concat(this._emptyCells).forEach((t=>{if(t){const r=t.querySelector('[part~="resize-handle"]');if(r&&t.removeChild(r),e){const e=document.createElement("div");e.setAttribute("part","resize-handle"),t.appendChild(e)}}}))}_textAlignChanged(e){if(void 0===e)return;if(-1===["start","end","center"].indexOf(e))return void console.warn('textAlign can only be set as "start", "end" or "center"');let t;"ltr"===getComputedStyle(this._grid).direction?"start"===e?t="left":"end"===e&&(t="right"):"start"===e?t="right":"end"===e&&(t="left"),this._allCells.forEach((r=>{r._content.style.textAlign=e,getComputedStyle(r._content).textAlign!==e&&(r._content.style.textAlign=t)}))}_hiddenChanged(e){this.parentElement&&this.parentElement._columnPropChanged&&this.parentElement._columnPropChanged("hidden",e),!!e!=!!this._previousHidden&&this._grid&&(!0===e&&this._allCells.forEach((e=>{e._content.parentNode&&e._content.parentNode.removeChild(e._content)})),this._grid._debouncerHiddenChanged=v.debounce(this._grid._debouncerHiddenChanged,C,(()=>{this._grid&&this._grid._renderColumnTree&&this._grid._renderColumnTree(this._grid._columnTree)})),this._grid._debounceUpdateFrozenColumn&&this._grid._debounceUpdateFrozenColumn(),this._grid._resetKeyboardNavigation&&this._grid._resetKeyboardNavigation()),this._previousHidden=e}_runRenderer(e,t,r){const i=[t._content,this];r&&r.item&&i.push(r),e.apply(this,i)}__renderCellsContent(e,t){!this.hidden&&this._grid&&t.forEach((t=>{if(!t.parentElement)return;const r=this._grid.__getRowModel(t.parentElement);e&&(t._renderer!==e&&this._clearCellContent(t),t._renderer=e,(r.item||e===this._headerRenderer||e===this._footerRenderer)&&this._runRenderer(e,t,r))}))}_clearCellContent(e){e._content.innerHTML="",delete e._content._$litPart$}_renderHeaderCellContent(e,t){t&&e&&(this.__renderCellsContent(e,[t]),this._grid&&t.parentElement&&this._grid.__debounceUpdateHeaderFooterRowVisibility(t.parentElement))}_onHeaderRendererOrBindingChanged(e,t,...r){this._renderHeaderCellContent(e,t)}_renderBodyCellsContent(e,t){t&&e&&this.__renderCellsContent(e,t)}_onRendererOrBindingChanged(e,t,...r){this._renderBodyCellsContent(e,t)}_renderFooterCellContent(e,t){t&&e&&(this.__renderCellsContent(e,[t]),this._grid&&t.parentElement&&this._grid.__debounceUpdateHeaderFooterRowVisibility(t.parentElement))}_onFooterRendererOrBindingChanged(e,t){this._renderFooterCellContent(e,t)}__setTextContent(e,t){e.textContent!==t&&(e.textContent=t)}__textHeaderRenderer(){this.__setTextContent(this._headerCell._content,this.header)}_defaultHeaderRenderer(){this.path&&this.__setTextContent(this._headerCell._content,this._generateHeader(this.path))}_defaultRenderer(e,t,{item:r}){this.path&&this.__setTextContent(e,this.get(this.path,r))}_defaultFooterRenderer(){}_computeHeaderRenderer(e,t){return e||(null!=t?this.__textHeaderRenderer:this._defaultHeaderRenderer)}_computeRenderer(e){return e||this._defaultRenderer}_computeFooterRenderer(e){return e||this._defaultFooterRenderer}};class J extends(Y(w(g))){static get is(){return"vaadin-grid-column"}static get properties(){return{width:{type:String,value:"100px"},flexGrow:{type:Number,value:1},renderer:Function,_renderer:{type:Function,computed:"_computeRenderer(renderer, __initialized)"},path:{type:String},autoWidth:{type:Boolean,value:!1},_focusButtonMode:{type:Boolean,value:!1},_cells:Array}}}customElements.define(J.is,J),
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
e("vaadin-grid",t`
    @keyframes vaadin-grid-appear {
      to {
        opacity: 1;
      }
    }

    :host {
      display: block;
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
      display: block;
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
      opacity: 0;
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
  `,{moduleId:"vaadin-grid-styles"});
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const Z=e=>class extends e{static get observers(){return["_a11yUpdateGridSize(size, _columnTree, _columnTree.*)"]}_a11yGetHeaderRowCount(e){return e.filter((e=>e.some((e=>e.headerRenderer||e.path||e.header)))).length}_a11yGetFooterRowCount(e){return e.filter((e=>e.some((e=>e.headerRenderer)))).length}_a11yUpdateGridSize(e,t){if(void 0===e||void 0===t)return;const r=t[t.length-1];this.$.table.setAttribute("aria-rowcount",e+this._a11yGetHeaderRowCount(t)+this._a11yGetFooterRowCount(t)),this.$.table.setAttribute("aria-colcount",r&&r.length||0),this._a11yUpdateHeaderRows(),this._a11yUpdateFooterRows()}_a11yUpdateHeaderRows(){U(this.$.header,((e,t)=>{e.setAttribute("aria-rowindex",t+1)}))}_a11yUpdateFooterRows(){U(this.$.footer,((e,t)=>{e.setAttribute("aria-rowindex",this._a11yGetHeaderRowCount(this._columnTree)+this.size+t+1)}))}_a11yUpdateRowRowindex(e,t){e.setAttribute("aria-rowindex",t+this._a11yGetHeaderRowCount(this._columnTree)+1)}_a11yUpdateRowSelected(e,t){e.setAttribute("aria-selected",Boolean(t)),U(e,(e=>{e.setAttribute("aria-selected",Boolean(t))}))}_a11yUpdateRowExpanded(e){this.__isRowExpandable(e)?e.setAttribute("aria-expanded","false"):this.__isRowCollapsible(e)?e.setAttribute("aria-expanded","true"):e.removeAttribute("aria-expanded")}_a11yUpdateRowLevel(e,t){t>0||this.__isRowCollapsible(e)||this.__isRowExpandable(e)?e.setAttribute("aria-level",t+1):e.removeAttribute("aria-level")}_a11ySetRowDetailsCell(e,t){U(e,(e=>{e!==t&&e.setAttribute("aria-controls",t.id)}))}_a11yUpdateCellColspan(e,t){e.setAttribute("aria-colspan",Number(t))}_a11yUpdateSorters(){Array.from(this.querySelectorAll("vaadin-grid-sorter")).forEach((e=>{let t=e.parentNode;for(;t&&"vaadin-grid-cell-content"!==t.localName;)t=t.parentNode;if(t&&t.assignedSlot){t.assignedSlot.parentNode.setAttribute("aria-sort",{asc:"ascending",desc:"descending"}[String(e.direction)]||"none")}}))}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,Q=e=>{if(!e.parentNode)return!1;const t=Array.from(e.parentNode.querySelectorAll("[tabindex], button, input, select, textarea, object, iframe, a[href], area[href]")).filter((e=>{const t=e.getAttribute("part");return!(t&&t.includes("body-cell"))})).includes(e);return!e.disabled&&t&&e.offsetParent&&"hidden"!==getComputedStyle(e).visibility},ee=e=>class extends e{static get properties(){return{activeItem:{type:Object,notify:!0,value:null}}}ready(){super.ready(),this.$.scroller.addEventListener("click",this._onClick.bind(this)),this.addEventListener("cell-activate",this._activateItem.bind(this)),this.addEventListener("row-activate",this._activateItem.bind(this))}_activateItem(e){const t=e.detail.model,r=t?t.item:null;r&&(this.activeItem=this._itemsEqual(this.activeItem,r)?null:r)}_onClick(e){if(e.defaultPrevented)return;const t=e.composedPath(),r=t[t.indexOf(this.$.table)-3];if(!r||r.getAttribute("part").indexOf("details-cell")>-1)return;const i=r._content,o=this.getRootNode().activeElement;i.contains(o)||this._isFocusable(e.target)||e.target instanceof HTMLLabelElement||this.dispatchEvent(new CustomEvent("cell-activate",{detail:{model:this.__getRowModel(r.parentElement)}}))}_isFocusable(e){return Q(e)}};function te(e,t){return e.split(".").reduce(((e,t)=>e[t]),t)}function re(e,t,r){if(0===r.length)return!1;let i=!0;return e.forEach((({path:e})=>{if(!e||-1===e.indexOf("."))return;void 0===te(e.replace(/\.[^.]*$/u,""),r[0])&&(console.warn(`Path "${e}" used for ${t} does not exist in all of the items, ${t} is disabled.`),i=!1)})),i}function ie(e){return[void 0,null].indexOf(e)>=0?"":isNaN(e)?e.toString():e}function oe(e,t){return(e=ie(e))<(t=ie(t))?-1:e>t?1:0}const se=e=>(t,r)=>{let i=e?[...e]:[];t.filters&&re(t.filters,"filtering",i)&&(i=function(e,t){return e.filter((e=>t.every((t=>{const r=ie(te(t.path,e)),i=ie(t.value).toString().toLowerCase();return r.toString().toLowerCase().includes(i)}))))}(i,t.filters)),Array.isArray(t.sortOrders)&&t.sortOrders.length&&re(t.sortOrders,"sorting",i)&&(i=function(e,t){return e.sort(((e,r)=>t.map((t=>"asc"===t.direction?oe(te(t.path,e),te(t.path,r)):"desc"===t.direction?oe(te(t.path,r),te(t.path,e)):0)).reduce(((e,t)=>0!==e?e:t),0)))}(i,t.sortOrders));const o=Math.min(i.length,t.pageSize),s=t.page*o,n=s+o;r(i.slice(s,n),i.length)},ne=e=>class extends e{static get properties(){return{items:Array}}static get observers(){return["__dataProviderOrItemsChanged(dataProvider, items, isAttached, items.*, _filters, _sorters)"]}__setArrayDataProvider(e){const t=se(this.items);t.__items=e,this.setProperties({_arrayDataProvider:t,size:e.length,dataProvider:t})}__dataProviderOrItemsChanged(e,t,r){r&&(this._arrayDataProvider?e!==this._arrayDataProvider?this.setProperties({_arrayDataProvider:void 0,items:void 0}):t?this._arrayDataProvider.__items===t?(this.clearCache(),this.size=this._effectiveSize):this.__setArrayDataProvider(t):(this.setProperties({_arrayDataProvider:void 0,dataProvider:void 0,size:0}),this.clearCache()):t&&this.__setArrayDataProvider(t))}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,ae=e=>class extends e{static get properties(){return{columnReorderingAllowed:{type:Boolean,value:!1},_orderBaseScope:{type:Number,value:1e7}}}static get observers(){return["_updateOrders(_columnTree)"]}ready(){super.ready(),L(this,"track",this._onTrackEvent),this._reorderGhost=this.shadowRoot.querySelector('[part="reorder-ghost"]'),this.addEventListener("touchstart",this._onTouchStart.bind(this)),this.addEventListener("touchmove",this._onTouchMove.bind(this)),this.addEventListener("touchend",this._onTouchEnd.bind(this)),this.addEventListener("contextmenu",this._onContextMenu.bind(this))}_onContextMenu(e){this.hasAttribute("reordering")&&(e.preventDefault(),y||this._onTrackEnd())}_onTouchStart(e){this._startTouchReorderTimeout=setTimeout((()=>{this._onTrackStart({detail:{x:e.touches[0].clientX,y:e.touches[0].clientY}})}),100)}_onTouchMove(e){this._draggedColumn&&e.preventDefault(),clearTimeout(this._startTouchReorderTimeout)}_onTouchEnd(){clearTimeout(this._startTouchReorderTimeout),this._onTrackEnd()}_onTrackEvent(e){if("start"===e.detail.state){const t=e.composedPath(),r=t[t.indexOf(this.$.header)-2];if(!r||!r._content)return;if(r._content.contains(this.getRootNode().activeElement))return;if(this.$.scroller.hasAttribute("column-resizing"))return;this._touchDevice||this._onTrackStart(e)}else"track"===e.detail.state?this._onTrack(e):"end"===e.detail.state&&this._onTrackEnd(e)}_onTrackStart(e){if(!this.columnReorderingAllowed)return;const t=e.composedPath&&e.composedPath();if(t&&t.some((e=>e.hasAttribute&&e.hasAttribute("draggable"))))return;const r=this._cellFromPoint(e.detail.x,e.detail.y);if(r&&r.getAttribute("part").includes("header-cell")){for(this.toggleAttribute("reordering",!0),this._draggedColumn=r._column;1===this._draggedColumn.parentElement.childElementCount;)this._draggedColumn=this._draggedColumn.parentElement;this._setSiblingsReorderStatus(this._draggedColumn,"allowed"),this._draggedColumn._reorderStatus="dragging",this._updateGhost(r),this._reorderGhost.style.visibility="visible",this._updateGhostPosition(e.detail.x,this._touchDevice?e.detail.y-50:e.detail.y),this._autoScroller()}}_onTrack(e){if(!this._draggedColumn)return;const t=this._cellFromPoint(e.detail.x,e.detail.y);if(!t)return;const r=this._getTargetColumn(t,this._draggedColumn);if(this._isSwapAllowed(this._draggedColumn,r)&&this._isSwappableByPosition(r,e.detail.x)){const e=this._columnTree.findIndex((e=>e.includes(r))),t=this._getColumnsInOrder(e),i=t.indexOf(this._draggedColumn),o=t.indexOf(r),s=i<o?1:-1;for(let e=i;e!==o;e+=s)this._swapColumnOrders(this._draggedColumn,t[e+s])}this._updateGhostPosition(e.detail.x,this._touchDevice?e.detail.y-50:e.detail.y),this._lastDragClientX=e.detail.x}_onTrackEnd(){this._draggedColumn&&(this.toggleAttribute("reordering",!1),this._draggedColumn._reorderStatus="",this._setSiblingsReorderStatus(this._draggedColumn,""),this._draggedColumn=null,this._lastDragClientX=null,this._reorderGhost.style.visibility="hidden",this.dispatchEvent(new CustomEvent("column-reorder",{detail:{columns:this._getColumnsInOrder()}})))}_getColumnsInOrder(e=this._columnTree.length-1){return this._columnTree[e].filter((e=>!e.hidden)).sort(((e,t)=>e._order-t._order))}_cellFromPoint(e=0,t=0){this._draggedColumn||this.$.scroller.toggleAttribute("no-content-pointer-events",!0);const r=this.shadowRoot.elementFromPoint(e,t);if(this.$.scroller.toggleAttribute("no-content-pointer-events",!1),r&&r._column)return r}_updateGhostPosition(e,t){const r=this._reorderGhost.getBoundingClientRect(),i=e-r.width/2,o=t-r.height/2,s=parseInt(this._reorderGhost._left||0),n=parseInt(this._reorderGhost._top||0);this._reorderGhost._left=s-(r.left-i),this._reorderGhost._top=n-(r.top-o),this._reorderGhost.style.transform=`translate(${this._reorderGhost._left}px, ${this._reorderGhost._top}px)`}_updateGhost(e){const t=this._reorderGhost;t.textContent=e._content.innerText;const r=window.getComputedStyle(e);return["boxSizing","display","width","height","background","alignItems","padding","border","flex-direction","overflow"].forEach((e=>{t.style[e]=r[e]})),t}_updateOrders(e){void 0!==e&&(e[0].forEach((e=>{e._order=0})),W(e[0],this._orderBaseScope,0))}_setSiblingsReorderStatus(e,t){U(e.parentNode,(r=>{/column/u.test(r.localName)&&this._isSwapAllowed(r,e)&&(r._reorderStatus=t)}))}_autoScroller(){if(this._lastDragClientX){const e=this._lastDragClientX-this.getBoundingClientRect().right+50,t=this.getBoundingClientRect().left-this._lastDragClientX+50;e>0?this.$.table.scrollLeft+=e/10:t>0&&(this.$.table.scrollLeft-=t/10)}this._draggedColumn&&setTimeout((()=>this._autoScroller()),10)}_isSwapAllowed(e,t){if(e&&t){const r=e!==t,i=e.parentElement===t.parentElement,o=e.frozen&&t.frozen||e.frozenToEnd&&t.frozenToEnd||!e.frozen&&!e.frozenToEnd&&!t.frozen&&!t.frozenToEnd;return r&&i&&o}}_isSwappableByPosition(e,t){const r=Array.from(this.$.header.querySelectorAll('tr:not([hidden]) [part~="cell"]')).find((t=>e.contains(t._column))),i=this.$.header.querySelector("tr:not([hidden]) [reorder-status=dragging]").getBoundingClientRect(),o=r.getBoundingClientRect();return o.left>i.left?t>o.right-i.width:t<o.left+i.width}_swapColumnOrders(e,t){[e._order,t._order]=[t._order,e._order],this._debounceUpdateFrozenColumn(),this._updateFirstAndLastColumn()}_getTargetColumn(e,t){if(e&&t){let r=e._column;for(;r.parentElement!==t.parentElement&&r!==this;)r=r.parentElement;return r.parentElement===t.parentElement?r:e._column}}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,le=e=>class extends e{ready(){super.ready();const e=this.$.scroller;L(e,"track",this._onHeaderTrack.bind(this)),e.addEventListener("touchmove",(t=>e.hasAttribute("column-resizing")&&t.preventDefault())),e.addEventListener("contextmenu",(e=>"resize-handle"===e.target.getAttribute("part")&&e.preventDefault())),e.addEventListener("mousedown",(e=>"resize-handle"===e.target.getAttribute("part")&&e.preventDefault()))}_onHeaderTrack(e){const t=e.target;if("resize-handle"===t.getAttribute("part")){let r=t.parentElement._column;for(this.$.scroller.toggleAttribute("column-resizing",!0);"vaadin-grid-column-group"===r.localName;)r=r._childColumns.slice(0).sort(((e,t)=>e._order-t._order)).filter((e=>!e.hidden)).pop();const i=this.__isRTL,o=e.detail.x,s=Array.from(this.$.header.querySelectorAll('[part~="row"]:last-child [part~="cell"]')),n=s.find((e=>e._column===r));if(n.offsetWidth){const e=getComputedStyle(n._content),t=10+parseInt(e.paddingLeft)+parseInt(e.paddingRight)+parseInt(e.borderLeftWidth)+parseInt(e.borderRightWidth)+parseInt(e.marginLeft)+parseInt(e.marginRight);let s;const a=n.offsetWidth,l=n.getBoundingClientRect();s=n.hasAttribute("frozen-to-end")?a+(i?o-l.right:l.left-o):a+(i?l.left-o:o-l.right),r.width=`${Math.max(t,s)}px`,r.flexGrow=0}s.sort(((e,t)=>e._column._order-t._column._order)).forEach(((e,t,r)=>{t<r.indexOf(n)&&(e._column.width=`${e.offsetWidth}px`,e._column.flexGrow=0)}));const a=this._frozenToEndCells[0];if(a&&this.$.table.scrollWidth>this.$.table.offsetWidth){const e=a.getBoundingClientRect(),t=o-(i?e.right:e.left);(i&&t<=0||!i&&t>=0)&&(this.$.table.scrollLeft+=t)}"end"===e.detail.state&&(this.$.scroller.toggleAttribute("column-resizing",!1),this.dispatchEvent(new CustomEvent("column-resize",{detail:{resizedColumn:r}}))),this._resizeHandler()}}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,de=class e{constructor(e,t,r){this.grid=e,this.parentCache=t,this.parentItem=r,this.itemCaches={},this.items={},this.effectiveSize=0,this.size=0,this.pendingRequests={}}isLoading(){return Boolean(Object.keys(this.pendingRequests).length||Object.keys(this.itemCaches).filter((e=>this.itemCaches[e].isLoading()))[0])}getItemForIndex(e){const{cache:t,scaledIndex:r}=this.getCacheAndIndex(e);return t.items[r]}updateSize(){this.effectiveSize=!this.parentItem||this.grid._isExpanded(this.parentItem)?this.size+Object.keys(this.itemCaches).reduce(((e,t)=>{const r=this.itemCaches[t];return r.updateSize(),e+r.effectiveSize}),0):0}ensureSubCacheForScaledIndex(t){if(!this.itemCaches[t]){const r=new e(this.grid,this,this.items[t]);this.itemCaches[t]=r,this.grid._loadPage(0,r)}}getCacheAndIndex(e){let t=e;for(const[e,r]of Object.entries(this.itemCaches)){const i=Number(e);if(t<=i)return{cache:this,scaledIndex:t};if(t<=i+r.effectiveSize)return r.getCacheAndIndex(t-i-1);t-=r.effectiveSize}return{cache:this,scaledIndex:t}}},he=e=>class extends e{static get properties(){return{size:{type:Number,notify:!0},pageSize:{type:Number,value:50,observer:"_pageSizeChanged"},dataProvider:{type:Object,notify:!0,observer:"_dataProviderChanged"},loading:{type:Boolean,notify:!0,readOnly:!0,reflectToAttribute:!0},_cache:{type:Object,value(){return new de(this)}},_hasData:{type:Boolean,value:!1},itemHasChildrenPath:{type:String,value:"children",observer:"__itemHasChildrenPathChanged"},itemIdPath:{type:String,value:null},expandedItems:{type:Object,notify:!0,value:()=>[]},__expandedKeys:{type:Object,computed:"__computeExpandedKeys(itemIdPath, expandedItems.*)"}}}static get observers(){return["_sizeChanged(size)","_expandedItemsChanged(expandedItems.*)"]}_sizeChanged(e){const t=e-this._cache.size;this._cache.size+=t,this._cache.effectiveSize+=t,this._effectiveSize=this._cache.effectiveSize}__itemHasChildrenPathChanged(e,t){(t||"children"!==e)&&this.requestContentUpdate()}_getItem(e,t){if(e>=this._effectiveSize)return;t.index=e;const{cache:r,scaledIndex:i}=this._cache.getCacheAndIndex(e),o=r.items[i];o?(this.__updateLoading(t,!1),this._updateItem(t,o),this._isExpanded(o)&&r.ensureSubCacheForScaledIndex(i)):(this.__updateLoading(t,!0),this._loadPage(this._getPageForIndex(i),r))}__updateLoading(e,t){const r=G(e);V(e,"loading",t),K(r,"loading-row-cell",t)}getItemId(e){return this.itemIdPath?this.get(this.itemIdPath,e):e}_isExpanded(e){return this.__expandedKeys.has(this.getItemId(e))}_expandedItemsChanged(){this._cache.updateSize(),this._effectiveSize=this._cache.effectiveSize,this.__updateVisibleRows()}__computeExpandedKeys(e,t){const r=t.base||[],i=new Set;return r.forEach((e=>{i.add(this.getItemId(e))})),i}expandItem(e){this._isExpanded(e)||(this.expandedItems=[...this.expandedItems,e])}collapseItem(e){this._isExpanded(e)&&(this.expandedItems=this.expandedItems.filter((t=>!this._itemsEqual(t,e))))}_getIndexLevel(e){let{cache:t}=this._cache.getCacheAndIndex(e),r=0;for(;t.parentCache;)t=t.parentCache,r+=1;return r}_loadPage(e,t){if(!t.pendingRequests[e]&&this.dataProvider){this._setLoading(!0),t.pendingRequests[e]=!0;const r={page:e,pageSize:this.pageSize,sortOrders:this._mapSorters(),filters:this._mapFilters(),parentItem:t.parentItem};this.dataProvider(r,((i,o)=>{void 0!==o?t.size=o:r.parentItem&&(t.size=i.length);const s=Array.from(this.$.items.children).map((e=>e._item));i.forEach(((r,i)=>{const o=e*this.pageSize+i;t.items[o]=r,this._isExpanded(r)&&s.indexOf(r)>-1&&t.ensureSubCacheForScaledIndex(o)})),this._hasData=!0,delete t.pendingRequests[e],this._debouncerApplyCachedData=v.debounce(this._debouncerApplyCachedData,x.after(0),(()=>{this._setLoading(!1),this._cache.updateSize(),this._effectiveSize=this._cache.effectiveSize,U(this.$.items,(e=>{if(!e.hidden){this._cache.getItemForIndex(e.index)&&this._getItem(e.index,e)}})),this.__scrollToPendingIndex()})),this._cache.isLoading()||this._debouncerApplyCachedData.flush(),this.__itemsReceived()}))}}_getPageForIndex(e){return Math.floor(e/this.pageSize)}clearCache(){this._cache=new de(this),this._cache.size=this.size||0,this._cache.updateSize(),this._hasData=!1,this.__updateVisibleRows(),this._effectiveSize||this._loadPage(0,this._cache)}_pageSizeChanged(e,t){void 0!==t&&e!==t&&this.clearCache()}_checkSize(){void 0===this.size&&0===this._effectiveSize&&console.warn("The <vaadin-grid> needs the total number of items in order to display rows, which you can specify either by setting the `size` property, or by providing it to the second argument of the `dataProvider` function `callback` call.")}_dataProviderChanged(e,t){void 0!==t&&this.clearCache(),this._ensureFirstPageLoaded(),this._debouncerCheckSize=v.debounce(this._debouncerCheckSize,x.after(2e3),this._checkSize.bind(this))}_ensureFirstPageLoaded(){this._hasData||this._loadPage(0,this._cache)}_itemsEqual(e,t){return this.getItemId(e)===this.getItemId(t)}_getItemIndexInArray(e,t){let r=-1;return t.forEach(((t,i)=>{this._itemsEqual(t,e)&&(r=i)})),r}scrollToIndex(e){super.scrollToIndex(e),isNaN(e)||!this._cache.isLoading()&&this.clientHeight||(this.__pendingScrollToIndex=e)}__scrollToPendingIndex(){if(this.__pendingScrollToIndex&&this.$.items.children.length){const e=this.__pendingScrollToIndex;delete this.__pendingScrollToIndex,this.scrollToIndex(e)}}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,ce="between",_e="on-top-or-between",ue="on-grid",pe="on-top",ge="above",me="below",fe="empty",be=!("draggable"in document.createElement("div")),ve=e=>class extends e{static get properties(){return{dropMode:String,rowsDraggable:Boolean,dragFilter:Function,dropFilter:Function,__dndAutoScrollThreshold:{value:50}}}static get observers(){return["_dragDropAccessChanged(rowsDraggable, dropMode, dragFilter, dropFilter, loading)"]}ready(){super.ready(),this.$.table.addEventListener("dragstart",this._onDragStart.bind(this)),this.$.table.addEventListener("dragend",this._onDragEnd.bind(this)),this.$.table.addEventListener("dragover",this._onDragOver.bind(this)),this.$.table.addEventListener("dragleave",this._onDragLeave.bind(this)),this.$.table.addEventListener("drop",this._onDrop.bind(this)),this.$.table.addEventListener("dragenter",(e=>{this.dropMode&&(e.preventDefault(),e.stopPropagation())}))}_onDragStart(e){if(this.rowsDraggable){let t=e.target;if("vaadin-grid-cell-content"===t.localName&&(t=t.assignedSlot.parentNode.parentNode),t.parentNode!==this.$.items)return;if(e.stopPropagation(),this.toggleAttribute("dragging-rows",!0),this._safari){const e=t.style.transform;t.style.top=/translateY\((.*)\)/u.exec(e)[1],t.style.transform="none",requestAnimationFrame((()=>{t.style.top="",t.style.transform=e}))}const r=t.getBoundingClientRect();be?e.dataTransfer.setDragImage(t):e.dataTransfer.setDragImage(t,e.clientX-r.left,e.clientY-r.top);let i=[t];this._isSelected(t._item)&&(i=this.__getViewportRows().filter((e=>this._isSelected(e._item))).filter((e=>!this.dragFilter||this.dragFilter(this.__getRowModel(e))))),e.dataTransfer.setData("text",this.__formatDefaultTransferData(i)),j(t,{dragstart:i.length>1?`${i.length}`:""}),this.style.setProperty("--_grid-drag-start-x",e.clientX-r.left+20+"px"),this.style.setProperty("--_grid-drag-start-y",e.clientY-r.top+10+"px"),requestAnimationFrame((()=>{j(t,{dragstart:null}),this.style.setProperty("--_grid-drag-start-x",""),this.style.setProperty("--_grid-drag-start-y","")}));const o=new CustomEvent("grid-dragstart",{detail:{draggedItems:i.map((e=>e._item)),setDragData:(t,r)=>e.dataTransfer.setData(t,r),setDraggedItemsCount:e=>t.setAttribute("dragstart",e)}});o.originalEvent=e,this.dispatchEvent(o)}}_onDragEnd(e){this.toggleAttribute("dragging-rows",!1),e.stopPropagation();const t=new CustomEvent("grid-dragend");t.originalEvent=e,this.dispatchEvent(t)}_onDragLeave(e){e.stopPropagation(),this._clearDragStyles()}_onDragOver(e){if(this.dropMode){if(this._dropLocation=void 0,this._dragOverItem=void 0,this.__dndAutoScroll(e.clientY))return void this._clearDragStyles();let t=e.composedPath().find((e=>"tr"===e.localName));if(this._effectiveSize&&this.dropMode!==ue)if(t&&t.parentNode===this.$.items){const r=t.getBoundingClientRect();if(this._dropLocation=pe,this.dropMode===ce){const t=e.clientY-r.top<r.bottom-e.clientY;this._dropLocation=t?ge:me}else this.dropMode===_e&&(e.clientY-r.top<r.height/3?this._dropLocation=ge:e.clientY-r.top>r.height/3*2&&(this._dropLocation=me))}else{if(t)return;if(this.dropMode!==ce&&this.dropMode!==_e)return;t=Array.from(this.$.items.children).filter((e=>!e.hidden)).pop(),this._dropLocation=me}else this._dropLocation=fe;if(t&&t.hasAttribute("drop-disabled"))return void(this._dropLocation=void 0);e.stopPropagation(),e.preventDefault(),this._dropLocation===fe?this.toggleAttribute("dragover",!0):t?(this._dragOverItem=t._item,t.getAttribute("dragover")!==this._dropLocation&&j(t,{dragover:this._dropLocation},!0)):this._clearDragStyles()}}__dndAutoScroll(e){if(this.__dndAutoScrolling)return!0;const t=this.$.header.getBoundingClientRect().bottom,r=this.$.footer.getBoundingClientRect().top,i=t-e+this.__dndAutoScrollThreshold,o=e-r+this.__dndAutoScrollThreshold;let s=0;if(o>0?s=2*o:i>0&&(s=2*-i),s){const e=this.$.table.scrollTop;this.$.table.scrollTop+=s;if(e!==this.$.table.scrollTop)return this.__dndAutoScrolling=!0,setTimeout((()=>{this.__dndAutoScrolling=!1}),20),!0}}__getViewportRows(){const e=this.$.header.getBoundingClientRect().bottom,t=this.$.footer.getBoundingClientRect().top;return Array.from(this.$.items.children).filter((r=>{const i=r.getBoundingClientRect();return i.bottom>e&&i.top<t}))}_clearDragStyles(){this.removeAttribute("dragover"),U(this.$.items,(e=>{j(e,{dragover:null},!0)}))}_onDrop(e){if(this.dropMode){e.stopPropagation(),e.preventDefault();const t=e.dataTransfer.types&&Array.from(e.dataTransfer.types).map((t=>({type:t,data:e.dataTransfer.getData(t)})));this._clearDragStyles();const r=new CustomEvent("grid-drop",{bubbles:e.bubbles,cancelable:e.cancelable,detail:{dropTargetItem:this._dragOverItem,dropLocation:this._dropLocation,dragData:t}});r.originalEvent=e,this.dispatchEvent(r)}}__formatDefaultTransferData(e){return e.map((e=>Array.from(e.children).filter((e=>!e.hidden&&-1===e.getAttribute("part").indexOf("details-cell"))).sort(((e,t)=>e._column._order>t._column._order?1:-1)).map((e=>e._content.textContent.trim())).filter((e=>e)).join("\t"))).join("\n")}_dragDropAccessChanged(){this.filterDragAndDrop()}filterDragAndDrop(){U(this.$.items,(e=>{e.hidden||this._filterDragAndDrop(e,this.__getRowModel(e))}))}_filterDragAndDrop(e,t){const r=this.loading||e.hasAttribute("loading"),i=!this.rowsDraggable||r||this.dragFilter&&!this.dragFilter(t),o=!this.dropMode||r||this.dropFilter&&!this.dropFilter(t);U(e,(e=>{i?e._content.removeAttribute("draggable"):e._content.setAttribute("draggable",!0)})),j(e,{"drag-disabled":!!i,"drop-disabled":!!o})}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */function Ce(e,t){if(!e||!t||e.length!==t.length)return!1;for(let r=0,i=e.length;r<i;r++)if(e[r]instanceof Array&&t[r]instanceof Array){if(!Ce(e[r],t[r]))return!1}else if(e[r]!==t[r])return!1;return!0}const we=e=>class extends e{static get properties(){return{_columnTree:Object}}ready(){super.ready(),this._addNodeObserver()}_hasColumnGroups(e){return e.some((e=>"vaadin-grid-column-group"===e.localName))}_getChildColumns(e){return z.getFlattenedNodes(e).filter(this._isColumnElement)}_flattenColumnGroups(e){return e.map((e=>"vaadin-grid-column-group"===e.localName?this._getChildColumns(e):[e])).reduce(((e,t)=>e.concat(t)),[])}_getColumnTree(){const e=z.getFlattenedNodes(this).filter(this._isColumnElement),t=[e];let r=e;for(;this._hasColumnGroups(r);)r=this._flattenColumnGroups(r),t.push(r);return t}_updateColumnTree(){const e=this._getColumnTree();Ce(e,this._columnTree)||(this._columnTree=e)}_addNodeObserver(){this._observer=new z(this,(e=>{const t=e=>e.filter(this._isColumnElement).length>0;if(t(e.addedNodes)||t(e.removedNodes)){const t=e.removedNodes.flatMap((e=>e._allCells)),r=e=>t.filter((t=>t._content.contains(e))).length;this.__removeSorters(this._sorters.filter(r)),this.__removeFilters(this._filters.filter(r)),this._updateColumnTree()}this._debouncerCheckImports=v.debounce(this._debouncerCheckImports,x.after(2e3),this._checkImports.bind(this)),this._ensureFirstPageLoaded()}))}_checkImports(){["vaadin-grid-column-group","vaadin-grid-filter","vaadin-grid-filter-column","vaadin-grid-tree-toggle","vaadin-grid-selection-column","vaadin-grid-sort-column","vaadin-grid-sorter"].forEach((e=>{const t=this.querySelector(e);!t||t instanceof g||console.warn(`Make sure you have imported the required module for <${e}> element.`)}))}_updateFirstAndLastColumn(){Array.from(this.shadowRoot.querySelectorAll("tr")).forEach((e=>this._updateFirstAndLastColumnForRow(e)))}_updateFirstAndLastColumnForRow(e){Array.from(e.querySelectorAll('[part~="cell"]:not([part~="details-cell"])')).sort(((e,t)=>e._column._order-t._column._order)).forEach(((e,t,r)=>{X(e,"first-column",0===t),X(e,"last-column",t===r.length-1)}))}_isColumnElement(e){return e.nodeType===Node.ELEMENT_NODE&&/\bcolumn\b/u.test(e.localName)}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,ye=e=>class extends e{getEventContext(e){const t={},r=e.__composedPath||e.composedPath(),i=r[r.indexOf(this.$.table)-3];return i?(t.section=["body","header","footer","details"].find((e=>i.getAttribute("part").indexOf(e)>-1)),i._column&&(t.column=i._column),"body"!==t.section&&"details"!==t.section||Object.assign(t,this.__getRowModel(i.parentElement)),t):t}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,xe=e=>class extends e{static get properties(){return{_filters:{type:Array,value:()=>[]}}}ready(){super.ready(),this.addEventListener("filter-changed",this._filterChanged.bind(this))}_filterChanged(e){e.stopPropagation(),this.__addFilter(e.target),this.__applyFilters()}__removeFilters(e){0!==e.length&&(this._filters=this._filters.filter((t=>e.indexOf(t)<0)),this.__applyFilters())}__addFilter(e){-1===this._filters.indexOf(e)&&this._filters.push(e)}__applyFilters(){this.dataProvider&&this.isAttached&&this.clearCache()}_mapFilters(){return this._filters.map((e=>({path:e.path,value:e.value})))}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,ze=e=>class extends e{static get properties(){return{_headerFocusable:{type:Object,observer:"_focusableChanged"},_itemsFocusable:{type:Object,observer:"_focusableChanged"},_footerFocusable:{type:Object,observer:"_focusableChanged"},_navigatingIsHidden:Boolean,_focusedItemIndex:{type:Number,value:0},_focusedColumnOrder:Number,_focusedCell:{type:Object,observer:"_focusedCellChanged"},interacting:{type:Boolean,value:!1,reflectToAttribute:!0,readOnly:!0,observer:"_interactingChanged"}}}get __rowFocusMode(){return this.__isRow(this._itemsFocusable)||this.__isRow(this._headerFocusable)||this.__isRow(this._footerFocusable)}set __rowFocusMode(e){["_itemsFocusable","_footerFocusable","_headerFocusable"].forEach((t=>{const r=this[t];if(e){const e=r&&r.parentElement;this.__isCell(r)?this[t]=e:this.__isCell(e)&&(this[t]=e.parentElement)}else if(!e&&this.__isRow(r)){const e=r.firstElementChild;this[t]=e._focusButton||e}}))}ready(){super.ready(),this._ios||this._android||(this.addEventListener("keydown",this._onKeyDown),this.addEventListener("keyup",this._onKeyUp),this.addEventListener("focusin",this._onFocusIn),this.addEventListener("focusout",this._onFocusOut),this.$.table.addEventListener("focusin",this._onContentFocusIn.bind(this)),this.addEventListener("mousedown",(()=>{this.toggleAttribute("navigating",!1),this._isMousedown=!0,this._focusedColumnOrder=void 0})),this.addEventListener("mouseup",(()=>{this._isMousedown=!1})))}_focusableChanged(e,t){t&&t.setAttribute("tabindex","-1"),e&&this._updateGridSectionFocusTarget(e)}_focusedCellChanged(e,t){t&&f(t,"part","focused-cell"),e&&m(e,"part","focused-cell")}_interactingChanged(){this._updateGridSectionFocusTarget(this._headerFocusable),this._updateGridSectionFocusTarget(this._itemsFocusable),this._updateGridSectionFocusTarget(this._footerFocusable)}__updateItemsFocusable(){if(!this._itemsFocusable)return;const e=this.shadowRoot.activeElement===this._itemsFocusable;this._getVisibleRows().forEach((e=>{if(e.index===this._focusedItemIndex)if(this.__rowFocusMode)this._itemsFocusable=e;else{let t=this._itemsFocusable.parentElement,r=this._itemsFocusable;if(t){this.__isCell(t)&&(r=t,t=t.parentElement);const i=[...t.children].indexOf(r);this._itemsFocusable=this.__getFocusable(e,e.children[i])}}})),e&&this._itemsFocusable.focus()}_onKeyDown(e){const t=e.key;let r;switch(t){case"ArrowUp":case"ArrowDown":case"ArrowLeft":case"ArrowRight":case"PageUp":case"PageDown":case"Home":case"End":r="Navigation";break;case"Enter":case"Escape":case"F2":r="Interaction";break;case"Tab":r="Tab";break;case" ":r="Space"}this._detectInteracting(e),this.interacting&&"Interaction"!==r&&(r=void 0),r&&this[`_on${r}KeyDown`](e,t)}_ensureScrolledToIndex(e){[...this.$.items.children].find((t=>t.index===e))?this.__scrollIntoViewport(e):this.scrollToIndex(e)}__isRowExpandable(e){if(this.itemHasChildrenPath){const t=e._item;return t&&this.get(this.itemHasChildrenPath,t)&&!this._isExpanded(t)}}__isRowCollapsible(e){return this._isExpanded(e._item)}__isDetailsCell(e){return e.matches('[part~="details-cell"]')}__isCell(e){return e instanceof HTMLTableCellElement}__isRow(e){return e instanceof HTMLTableRowElement}__getIndexOfChildElement(e){return Array.prototype.indexOf.call(e.parentNode.children,e)}_onNavigationKeyDown(e,t){e.preventDefault();const r=this._lastVisibleIndex-this._firstVisibleIndex-1,i=this.__isRTL;let o=0,s=0;switch(t){case"ArrowRight":o=i?-1:1;break;case"ArrowLeft":o=i?1:-1;break;case"Home":this.__rowFocusMode||e.ctrlKey?s=-1/0:o=-1/0;break;case"End":this.__rowFocusMode||e.ctrlKey?s=1/0:o=1/0;break;case"ArrowDown":s=1;break;case"ArrowUp":s=-1;break;case"PageDown":s=r;break;case"PageUp":s=-r}const n=e.composedPath().find((e=>this.__isRow(e))),a=e.composedPath().find((e=>this.__isCell(e)));if(this.__rowFocusMode&&!n||!this.__rowFocusMode&&!a)return;const l=i?"ArrowRight":"ArrowLeft";if(t===(i?"ArrowLeft":"ArrowRight")){if(this.__rowFocusMode)return this.__isRowExpandable(n)?void this.expandItem(n._item):(this.__rowFocusMode=!1,void this._onCellNavigation(n.firstElementChild,0,0))}else if(t===l)if(this.__rowFocusMode){if(this.__isRowCollapsible(n))return void this.collapseItem(n._item)}else{if(a===[...n.children].sort(((e,t)=>e._order-t._order))[0]||this.__isDetailsCell(a))return this.__rowFocusMode=!0,void this._onRowNavigation(n,0)}this.__rowFocusMode?this._onRowNavigation(n,s):this._onCellNavigation(a,o,s)}_onRowNavigation(e,t){const{dstRow:r}=this.__navigateRows(t,e);r&&r.focus()}__getIndexInGroup(e,t){return e.parentNode===this.$.items?void 0!==t?t:e.index:this.__getIndexOfChildElement(e)}__navigateRows(e,t,r){const i=this.__getIndexInGroup(t,this._focusedItemIndex),o=t.parentNode,s=(o===this.$.items?this._effectiveSize:o.children.length)-1;let n=Math.max(0,Math.min(i+e,s));if(o!==this.$.items){if(n>i)for(;n<s&&o.children[n].hidden;)n+=1;else if(n<i)for(;n>0&&o.children[n].hidden;)n-=1;return this.toggleAttribute("navigating",!0),{dstRow:o.children[n]}}let a=!1;if(r){const s=this.__isDetailsCell(r);if(o===this.$.items){const r=t._item,o=this._cache.getItemForIndex(n);a=s?0===e:1===e&&this._isDetailsOpened(r)||-1===e&&n!==i&&this._isDetailsOpened(o),a!==s&&(1===e&&a||-1===e&&!a)&&(n=i)}}return this._ensureScrolledToIndex(n),this._focusedItemIndex=n,this.toggleAttribute("navigating",!0),{dstRow:[...o.children].find((e=>!e.hidden&&e.index===n)),dstIsRowDetails:a}}_onCellNavigation(e,t,r){const i=e.parentNode,{dstRow:o,dstIsRowDetails:s}=this.__navigateRows(r,i,e);if(!o)return;const n=this.__getIndexOfChildElement(e),a=this.__isDetailsCell(e),l=i.parentNode,d=this.__getIndexInGroup(i,this._focusedItemIndex);if(void 0===this._focusedColumnOrder&&(this._focusedColumnOrder=a?0:this._getColumns(l,d).filter((e=>!e.hidden))[n]._order),s){[...o.children].find((e=>this.__isDetailsCell(e))).focus()}else{const e=this.__getIndexInGroup(o,this._focusedItemIndex),i=this._getColumns(l,e).filter((e=>!e.hidden)),s=i.map((e=>e._order)).sort(((e,t)=>e-t)),n=s.length-1,d=s.indexOf(s.slice(0).sort(((e,t)=>Math.abs(e-this._focusedColumnOrder)-Math.abs(t-this._focusedColumnOrder)))[0]),h=0===r&&a?d:Math.max(0,Math.min(d+t,n));h!==d&&(this._focusedColumnOrder=void 0);const c=i.reduce(((e,t,r)=>(e[t._order]=r,e)),{}),_=c[s[h]],u=o.children[_];this._scrollHorizontallyToCell(u),u.focus()}}_onInteractionKeyDown(e,t){const r=e.composedPath()[0],i="input"===r.localName&&!/^(button|checkbox|color|file|image|radio|range|reset|submit)$/iu.test(r.type);let o;switch(t){case"Enter":o=!this.interacting||!i;break;case"Escape":o=!1;break;case"F2":o=!this.interacting}const{cell:s}=this._getGridEventLocation(e);if(this.interacting!==o&&null!==s)if(o){const t=s._content.querySelector("[focus-target]")||[...s._content.querySelectorAll("*")].find((e=>this._isFocusable(e)));t&&(e.preventDefault(),t.focus(),this._setInteracting(!0),this.toggleAttribute("navigating",!1))}else e.preventDefault(),this._focusedColumnOrder=void 0,s.focus(),this._setInteracting(!1),this.toggleAttribute("navigating",!0);"Escape"===t&&this._hideTooltip(!0)}_predictFocusStepTarget(e,t){const r=[this.$.table,this._headerFocusable,this._itemsFocusable,this._footerFocusable,this.$.focusexit];let i=r.indexOf(e);for(i+=t;i>=0&&i<=r.length-1;){let e=r[i];if(e&&!this.__rowFocusMode&&(e=r[i].parentNode),e&&!e.hidden)break;i+=t}return r[i]}_onTabKeyDown(e){const t=this._predictFocusStepTarget(e.composedPath()[0],e.shiftKey?-1:1);if(t){if(e.stopPropagation(),t===this.$.table)this.$.table.focus();else if(t===this.$.focusexit)this.$.focusexit.focus();else if(t===this._itemsFocusable){let r=t;const i=this.__isRow(t)?t:t.parentNode;if(this._ensureScrolledToIndex(this._focusedItemIndex),i.index!==this._focusedItemIndex&&this.__isCell(t)){const e=Array.from(i.children).indexOf(this._itemsFocusable),t=Array.from(this.$.items.children).find((e=>!e.hidden&&e.index===this._focusedItemIndex));t&&(r=t.children[e])}e.preventDefault(),r.focus()}else e.preventDefault(),t.focus();this.toggleAttribute("navigating",!0)}}_onSpaceKeyDown(e){e.preventDefault();const t=e.composedPath()[0],r=this.__isRow(t);!r&&t._content&&t._content.firstElementChild||this.dispatchEvent(new CustomEvent(r?"row-activate":"cell-activate",{detail:{model:this.__getRowModel(r?t:t.parentElement)}}))}_onKeyUp(e){if(!/^( |SpaceBar)$/u.test(e.key)||this.interacting)return;e.preventDefault();const t=e.composedPath()[0];if(t._content&&t._content.firstElementChild){const r=this.hasAttribute("navigating");t._content.firstElementChild.dispatchEvent(new MouseEvent("click",{shiftKey:e.shiftKey,bubbles:!0,composed:!0,cancelable:!0})),this.toggleAttribute("navigating",r)}}_onFocusIn(e){this._isMousedown||this.toggleAttribute("navigating",!0);const t=e.composedPath()[0];t===this.$.table||t===this.$.focusexit?(this._predictFocusStepTarget(t,t===this.$.table?1:-1).focus(),this._setInteracting(!1)):this._detectInteracting(e)}_onFocusOut(e){this.toggleAttribute("navigating",!1),this._detectInteracting(e),this._hideTooltip(),this._focusedCell=null}_onContentFocusIn(e){const{section:t,cell:r,row:i}=this._getGridEventLocation(e);if(r||this.__rowFocusMode){if(this._detectInteracting(e),t&&(r||i))if(this._activeRowGroup=t,this.$.header===t?this._headerFocusable=this.__getFocusable(i,r):this.$.items===t?this._itemsFocusable=this.__getFocusable(i,r):this.$.footer===t&&(this._footerFocusable=this.__getFocusable(i,r)),r){const t=this.getEventContext(e);r.dispatchEvent(new CustomEvent("cell-focus",{bubbles:!0,composed:!0,detail:{context:t}})),this._focusedCell=r._focusButton||r,E()&&e.target===r&&this._showTooltip(e)}else this._focusedCell=null;this._detectFocusedItemIndex(e)}}__getFocusable(e,t){return this.__rowFocusMode?e:t._focusButton||t}_detectInteracting(e){const t=e.composedPath().some((e=>"vaadin-grid-cell-content"===e.localName));this._setInteracting(t),this.__updateHorizontalScrollPosition()}_detectFocusedItemIndex(e){const{section:t,row:r}=this._getGridEventLocation(e);t===this.$.items&&(this._focusedItemIndex=r.index)}_updateGridSectionFocusTarget(e){if(!e)return;const t=this._getGridSectionFromFocusTarget(e),r=this.interacting&&t===this._activeRowGroup;e.tabIndex=r?-1:0}_preventScrollerRotatingCellFocus(e,t){e.index===this._focusedItemIndex&&this.hasAttribute("navigating")&&this._activeRowGroup===this.$.items&&(this._navigatingIsHidden=!0,this.toggleAttribute("navigating",!1)),t===this._focusedItemIndex&&this._navigatingIsHidden&&(this._navigatingIsHidden=!1,this.toggleAttribute("navigating",!0))}_getColumns(e,t){let r=this._columnTree.length-1;return e===this.$.header?r=t:e===this.$.footer&&(r=this._columnTree.length-1-t),this._columnTree[r]}__isValidFocusable(e){return this.$.table.contains(e)&&e.offsetHeight}_resetKeyboardNavigation(){if(["header","footer"].forEach((e=>{if(!this.__isValidFocusable(this[`_${e}Focusable`])){const t=[...this.$[e].children].find((e=>e.offsetHeight)),r=t?[...t.children].find((e=>!e.hidden)):null;t&&r&&(this[`_${e}Focusable`]=this.__getFocusable(t,r))}})),!this.__isValidFocusable(this._itemsFocusable)&&this.$.items.firstElementChild){const e=this.__getFirstVisibleItem(),t=e?[...e.children].find((e=>!e.hidden)):null;t&&e&&(delete this._focusedColumnOrder,this._itemsFocusable=this.__getFocusable(e,t))}else this.__updateItemsFocusable()}_scrollHorizontallyToCell(e){if(e.hasAttribute("frozen")||e.hasAttribute("frozen-to-end")||this.__isDetailsCell(e))return;const t=e.getBoundingClientRect(),r=e.parentNode,i=Array.from(r.children).indexOf(e),o=this.$.table.getBoundingClientRect();let s=o.left,n=o.right;for(let e=i-1;e>=0;e--){const t=r.children[e];if(!t.hasAttribute("hidden")&&!this.__isDetailsCell(t)&&(t.hasAttribute("frozen")||t.hasAttribute("frozen-to-end"))){s=t.getBoundingClientRect().right;break}}for(let e=i+1;e<r.children.length;e++){const t=r.children[e];if(!t.hasAttribute("hidden")&&!this.__isDetailsCell(t)&&(t.hasAttribute("frozen")||t.hasAttribute("frozen-to-end"))){n=t.getBoundingClientRect().left;break}}t.left<s&&(this.$.table.scrollLeft+=Math.round(t.left-s)),t.right>n&&(this.$.table.scrollLeft+=Math.round(t.right-n))}_getGridEventLocation(e){const t=e.composedPath(),r=t.indexOf(this.$.table);return{section:r>=1?t[r-1]:null,row:r>=2?t[r-2]:null,cell:r>=3?t[r-3]:null}}_getGridSectionFromFocusTarget(e){return e===this._headerFocusable?this.$.header:e===this._itemsFocusable?this.$.items:e===this._footerFocusable?this.$.footer:null}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,Ee=e=>class extends e{static get properties(){return{detailsOpenedItems:{type:Array,value:()=>[]},rowDetailsRenderer:Function,_detailsCells:{type:Array}}}static get observers(){return["_detailsOpenedItemsChanged(detailsOpenedItems.*, rowDetailsRenderer)","_rowDetailsRendererChanged(rowDetailsRenderer)"]}ready(){super.ready(),this._detailsCellResizeObserver=new ResizeObserver((e=>{e.forEach((({target:e})=>{this._updateDetailsCellHeight(e.parentElement)})),this.__virtualizer.__adapter._resizeHandler()}))}_rowDetailsRendererChanged(e){e&&this._columnTree&&U(this.$.items,(e=>{if(!e.querySelector("[part~=details-cell]")){this._updateRow(e,this._columnTree[this._columnTree.length-1]);const t=this._isDetailsOpened(e._item);this._toggleDetailsCell(e,t)}}))}_detailsOpenedItemsChanged(e,t){"detailsOpenedItems.length"!==e.path&&e.value&&U(this.$.items,(e=>{(e.hasAttribute("details-opened")||t&&this._isDetailsOpened(e._item))&&this._updateItem(e,e._item)}))}_configureDetailsCell(e){e.setAttribute("part","cell details-cell"),e.toggleAttribute("frozen",!0),this._detailsCellResizeObserver.observe(e)}_toggleDetailsCell(e,t){const r=e.querySelector('[part~="details-cell"]');r&&(r.hidden=!t,r.hidden||this.rowDetailsRenderer&&(r._renderer=this.rowDetailsRenderer))}_updateDetailsCellHeight(e){const t=e.querySelector('[part~="details-cell"]');t&&(t.hidden?e.style.removeProperty("padding-bottom"):e.style.setProperty("padding-bottom",`${t.offsetHeight}px`))}_updateDetailsCellHeights(){U(this.$.items,(e=>{this._updateDetailsCellHeight(e)}))}_isDetailsOpened(e){return this.detailsOpenedItems&&-1!==this._getItemIndexInArray(e,this.detailsOpenedItems)}openItemDetails(e){this._isDetailsOpened(e)||(this.detailsOpenedItems=[...this.detailsOpenedItems,e])}closeItemDetails(e){this._isDetailsOpened(e)&&(this.detailsOpenedItems=this.detailsOpenedItems.filter((t=>!this._itemsEqual(t,e))))}}
/**
 * @license
 * Copyright (c) 2021 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,Ae=new ResizeObserver((e=>{setTimeout((()=>{e.forEach((e=>{e.target.resizables?e.target.resizables.forEach((t=>{t._onResize(e.contentRect)})):e.target._onResize(e.contentRect)}))}))})),Ie=r((e=>class extends e{get _observeParent(){return!1}connectedCallback(){if(super.connectedCallback(),Ae.observe(this),this._observeParent){const e=this.parentNode instanceof ShadowRoot?this.parentNode.host:this.parentNode;e.resizables||(e.resizables=new Set,Ae.observe(e)),e.resizables.add(this),this.__parent=e}}disconnectedCallback(){super.disconnectedCallback(),Ae.unobserve(this);const e=this.__parent;if(this._observeParent&&e){const t=e.resizables;t&&(t.delete(this),0===t.size&&Ae.unobserve(e)),this.__parent=null}}_onResize(e){}})),Re=500,Se=e=>class extends(Ie(e)){static get properties(){return{_frozenCells:{type:Array,value:()=>[]},_frozenToEndCells:{type:Array,value:()=>[]},_rowWithFocusedElement:Element}}get _scrollLeft(){return this.$.table.scrollLeft}get _scrollTop(){return this.$.table.scrollTop}set _scrollTop(e){this.$.table.scrollTop=e}ready(){super.ready(),this.scrollTarget=this.$.table,this.$.items.addEventListener("focusin",(e=>{const t=e.composedPath().indexOf(this.$.items);this._rowWithFocusedElement=e.composedPath()[t-1]})),this.$.items.addEventListener("focusout",(()=>{this._rowWithFocusedElement=void 0})),this.$.table.addEventListener("scroll",(()=>this._afterScroll()))}_onResize(){this._updateOverflow(),this.__updateHorizontalScrollPosition()}scrollToIndex(e){e=Math.min(this._effectiveSize-1,Math.max(0,e)),this.__virtualizer.scrollToIndex(e),this.__scrollIntoViewport(e)}__scrollIntoViewport(e){const t=[...this.$.items.children].find((t=>t.index===e));if(t){const e=t.getBoundingClientRect(),r=this.$.footer.getBoundingClientRect().top,i=this.$.header.getBoundingClientRect().bottom;e.bottom>r?this.$.table.scrollTop+=e.bottom-r:e.top<i&&(this.$.table.scrollTop-=i-e.top)}}_scheduleScrolling(){this._scrollingFrame||(this._scrollingFrame=requestAnimationFrame((()=>this.$.scroller.toggleAttribute("scrolling",!0)))),this._debounceScrolling=v.debounce(this._debounceScrolling,x.after(Re),(()=>{cancelAnimationFrame(this._scrollingFrame),delete this._scrollingFrame,this.$.scroller.toggleAttribute("scrolling",!1)}))}_afterScroll(){this.__updateHorizontalScrollPosition(),this.hasAttribute("reordering")||this._scheduleScrolling(),this.hasAttribute("navigating")||this._hideTooltip(!0),this._updateOverflow()}_updateOverflow(){this._debounceOverflow=v.debounce(this._debounceOverflow,C,(()=>{this.__doUpdateOverflow()}))}__doUpdateOverflow(){let e="";const t=this.$.table;t.scrollTop<t.scrollHeight-t.clientHeight&&(e+=" bottom"),t.scrollTop>0&&(e+=" top");const r=N(t,this.getAttribute("dir"));r>0&&(e+=" start"),r<t.scrollWidth-t.clientWidth&&(e+=" end"),this.__isRTL&&(e=e.replace(/start|end/giu,(e=>"start"===e?"end":"start"))),t.scrollLeft<t.scrollWidth-t.clientWidth&&(e+=" right"),t.scrollLeft>0&&(e+=" left");const i=e.trim();i.length>0&&this.getAttribute("overflow")!==i?this.setAttribute("overflow",i):0===i.length&&this.hasAttribute("overflow")&&this.removeAttribute("overflow")}_frozenCellsChanged(){this._debouncerCacheElements=v.debounce(this._debouncerCacheElements,A,(()=>{Array.from(this.shadowRoot.querySelectorAll('[part~="cell"]')).forEach((e=>{e.style.transform=""})),this._frozenCells=Array.prototype.slice.call(this.$.table.querySelectorAll("[frozen]")),this._frozenToEndCells=Array.prototype.slice.call(this.$.table.querySelectorAll("[frozen-to-end]")),this.__updateHorizontalScrollPosition()})),this._debounceUpdateFrozenColumn()}_debounceUpdateFrozenColumn(){this.__debounceUpdateFrozenColumn=v.debounce(this.__debounceUpdateFrozenColumn,A,(()=>this._updateFrozenColumn()))}_updateFrozenColumn(){if(!this._columnTree)return;const e=this._columnTree[this._columnTree.length-1].slice(0);let t,r;e.sort(((e,t)=>e._order-t._order));for(let i=0;i<e.length;i++){const o=e[i];o._lastFrozen=!1,o._firstFrozenToEnd=!1,void 0===r&&o.frozenToEnd&&!o.hidden&&(r=i),o.frozen&&!o.hidden&&(t=i)}void 0!==t&&(e[t]._lastFrozen=!0),void 0!==r&&(e[r]._firstFrozenToEnd=!0)}__updateHorizontalScrollPosition(){const e=this.$.table.scrollWidth,t=this.$.table.clientWidth,r=Math.max(0,this.$.table.scrollLeft),i=N(this.$.table,this.getAttribute("dir")),o=`translate(${-r}px, 0)`;this.$.header.style.transform=o,this.$.footer.style.transform=o,this.$.items.style.transform=o;const s=this.__isRTL?i+t-e:r,n=`translate(${s}px, 0)`;this._frozenCells.forEach((e=>{e.style.transform=n}));const a=`translate(${this.__isRTL?i:r+t-e}px, 0)`;this._frozenToEndCells.forEach((e=>{e.style.transform=a})),this.hasAttribute("navigating")&&this.__rowFocusMode&&this.$.table.style.setProperty("--_grid-horizontal-scroll-position",-s+"px")}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,Fe=e=>class extends e{static get properties(){return{selectedItems:{type:Object,notify:!0,value:()=>[]},__selectedKeys:{type:Object,computed:"__computeSelectedKeys(itemIdPath, selectedItems.*)"}}}static get observers(){return["__selectedItemsChanged(itemIdPath, selectedItems.*)"]}_isSelected(e){return this.__selectedKeys.has(this.getItemId(e))}selectItem(e){this._isSelected(e)||(this.selectedItems=[...this.selectedItems,e])}deselectItem(e){this._isSelected(e)&&(this.selectedItems=this.selectedItems.filter((t=>!this._itemsEqual(t,e))))}_toggleItem(e){this._isSelected(e)?this.deselectItem(e):this.selectItem(e)}__selectedItemsChanged(){this.requestContentUpdate()}__computeSelectedKeys(e,t){const r=t.base||[],i=new Set;return r.forEach((e=>{i.add(this.getItemId(e))})),i}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;let Te="prepend";const ke=e=>class extends e{static get properties(){return{multiSort:{type:Boolean,value:!1},multiSortPriority:{type:String,value:()=>Te},multiSortOnShiftClick:{type:Boolean,value:!1},_sorters:{type:Array,value:()=>[]},_previousSorters:{type:Array,value:()=>[]}}}static setDefaultMultiSortPriority(e){Te=["append","prepend"].includes(e)?e:"prepend"}ready(){super.ready(),this.addEventListener("sorter-changed",this._onSorterChanged)}_onSorterChanged(e){const t=e.target;e.stopPropagation(),t._grid=this,this.__updateSorter(t,e.detail.shiftClick,e.detail.fromSorterClick),this.__applySorters()}__removeSorters(e){0!==e.length&&(this._sorters=this._sorters.filter((t=>e.indexOf(t)<0)),this.multiSort&&this.__updateSortOrders(),this.__applySorters())}__updateSortOrders(){this._sorters.forEach(((e,t)=>{e._order=this._sorters.length>1?t:null}))}__appendSorter(e){e.direction?this._sorters.includes(e)||this._sorters.push(e):this._removeArrayItem(this._sorters,e),this.__updateSortOrders()}__prependSorter(e){this._removeArrayItem(this._sorters,e),e.direction&&this._sorters.unshift(e),this.__updateSortOrders()}__updateSorter(e,t,r){if(e.direction||-1!==this._sorters.indexOf(e))if(e._order=null,this.multiSort&&(!this.multiSortOnShiftClick||!r)||this.multiSortOnShiftClick&&t)"append"===this.multiSortPriority?this.__appendSorter(e):this.__prependSorter(e);else if(e.direction||this.multiSortOnShiftClick){const t=this._sorters.filter((t=>t!==e));this._sorters=e.direction?[e]:[],t.forEach((e=>{e._order=null,e.direction=null}))}}__applySorters(){this.dataProvider&&this.isAttached&&JSON.stringify(this._previousSorters)!==JSON.stringify(this._mapSorters())&&this.clearCache(),this._a11yUpdateSorters(),this._previousSorters=this._mapSorters()}_mapSorters(){return this._sorters.map((e=>({path:e.path,direction:e.direction})))}_removeArrayItem(e,t){const r=e.indexOf(t);r>-1&&e.splice(r,1)}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,$e=e=>class extends e{static get properties(){return{cellClassNameGenerator:Function,cellPartNameGenerator:Function}}static get observers(){return["__cellClassNameGeneratorChanged(cellClassNameGenerator)","__cellPartNameGeneratorChanged(cellPartNameGenerator)"]}__cellClassNameGeneratorChanged(){this.generateCellClassNames()}__cellPartNameGeneratorChanged(){this.generateCellPartNames()}generateCellClassNames(){U(this.$.items,(e=>{e.hidden||e.hasAttribute("loading")||this._generateCellClassNames(e,this.__getRowModel(e))}))}generateCellPartNames(){U(this.$.items,(e=>{e.hidden||e.hasAttribute("loading")||this._generateCellPartNames(e,this.__getRowModel(e))}))}_generateCellClassNames(e,t){U(e,(e=>{if(e.__generatedClasses&&e.__generatedClasses.forEach((t=>e.classList.remove(t))),this.cellClassNameGenerator){const r=this.cellClassNameGenerator(e._column,t);e.__generatedClasses=r&&r.split(" ").filter((e=>e.length>0)),e.__generatedClasses&&e.__generatedClasses.forEach((t=>e.classList.add(t)))}}))}_generateCellPartNames(e,t){U(e,(e=>{if(e.__generatedParts&&e.__generatedParts.forEach((t=>{q(e,null,t)})),this.cellPartNameGenerator){const r=this.cellPartNameGenerator(e._column,t);e.__generatedParts=r&&r.split(" ").filter((e=>e.length>0)),e.__generatedParts&&e.__generatedParts.forEach((t=>{q(e,!0,t)}))}}))}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;class Pe extends(u(p(he(ne(we(ee(Se(Fe(ke(Ee(ze(Z(xe(ae(le(I(ye(ve($e(R(g))))))))))))))))))))){static get template(){return c`
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
    `}static get is(){return"vaadin-grid"}static get observers(){return["_columnTreeChanged(_columnTree, _columnTree.*)","_effectiveSizeChanged(_effectiveSize, __virtualizer, _hasData, _columnTree)"]}static get properties(){return{_safari:{type:Boolean,value:S},_ios:{type:Boolean,value:F},_firefox:{type:Boolean,value:T},_android:{type:Boolean,value:k},_touchDevice:{type:Boolean,value:y},allRowsVisible:{type:Boolean,value:!1,reflectToAttribute:!0},_recalculateColumnWidthOnceLoadingFinished:{type:Boolean,value:!0},isAttached:{value:!1},__gridElement:{type:Boolean,value:!0}}}constructor(){super(),this.addEventListener("animationend",this._onAnimationEnd)}get _firstVisibleIndex(){const e=this.__getFirstVisibleItem();return e?e.index:void 0}get _lastVisibleIndex(){const e=this.__getLastVisibleItem();return e?e.index:void 0}connectedCallback(){super.connectedCallback(),this.isAttached=!0,this.recalculateColumnWidths()}disconnectedCallback(){super.disconnectedCallback(),this.isAttached=!1,this._hideTooltip(!0)}__getFirstVisibleItem(){return this._getVisibleRows().find((e=>this._isInViewport(e)))}__getLastVisibleItem(){return this._getVisibleRows().reverse().find((e=>this._isInViewport(e)))}_isInViewport(e){const t=this.$.table.getBoundingClientRect(),r=e.getBoundingClientRect(),i=this.$.header.getBoundingClientRect().height,o=this.$.footer.getBoundingClientRect().height;return r.bottom>t.top+i&&r.top<t.bottom-o}_getVisibleRows(){return Array.from(this.$.items.children).filter((e=>!e.hidden)).sort(((e,t)=>e.index-t.index))}ready(){super.ready(),this.__virtualizer=new $({createElements:this._createScrollerRows.bind(this),updateElement:this._updateScrollerItem.bind(this),scrollContainer:this.$.items,scrollTarget:this.$.table,reorderElements:!0}),new ResizeObserver((()=>setTimeout((()=>this.__updateFooterPositioning())))).observe(this.$.footer),b(this),this._tooltipController=new _(this),this.addController(this._tooltipController),this._tooltipController.setManual(!0)}__getBodyCellCoordinates(e){if(this.$.items.contains(e)&&"td"===e.localName)return{item:e.parentElement._item,column:e._column}}__focusBodyCell({item:e,column:t}){const r=this._getVisibleRows().find((t=>t._item===e)),i=r&&[...r.children].find((e=>e._column===t));i&&i.focus()}_effectiveSizeChanged(e,t,r,i){if(t&&r&&i){const r=this.shadowRoot.activeElement,i=this.__getBodyCellCoordinates(r),o=t.size||0;t.size=e,t.update(o-1,o-1),e<o&&t.update(e-1,e-1),i&&r.parentElement.hidden&&this.__focusBodyCell(i),this._resetKeyboardNavigation()}}__hasRowsWithClientHeight(){return!!Array.from(this.$.items.children).filter((e=>e.clientHeight)).length}__itemsReceived(){this._recalculateColumnWidthOnceLoadingFinished&&!this._cache.isLoading()&&this.__hasRowsWithClientHeight()&&(this._recalculateColumnWidthOnceLoadingFinished=!1,this.recalculateColumnWidths())}__getIntrinsicWidth(e){if(this.__intrinsicWidthCache.has(e))return this.__intrinsicWidthCache.get(e);const t=this.__calculateIntrinsicWidth(e);return this.__intrinsicWidthCache.set(e,t),t}__calculateIntrinsicWidth(e){const t=e.width,r=e.flexGrow;e.width="auto",e.flexGrow=0;const i=e._allCells.filter((e=>!this.$.items.contains(e)||this._isInViewport(e.parentElement))).reduce(((e,t)=>Math.max(e,t.offsetWidth+1)),0);return e.flexGrow=r,e.width=t,i}__getDistributedWidth(e,t){if(null==e||e===this)return 0;const r=Math.max(this.__getIntrinsicWidth(e),this.__getDistributedWidth(e.parentElement,e));if(!t)return r;const i=r,o=e._visibleChildColumns.map((e=>this.__getIntrinsicWidth(e))).reduce(((e,t)=>e+t),0),s=Math.max(0,i-o),n=this.__getIntrinsicWidth(t)/o*s;return this.__getIntrinsicWidth(t)+n}_recalculateColumnWidths(e){this.__virtualizer.flush(),[...this.$.header.children,...this.$.footer.children].forEach((e=>{e.__debounceUpdateHeaderFooterRowVisibility&&e.__debounceUpdateHeaderFooterRowVisibility.flush()})),this._debouncerHiddenChanged&&this._debouncerHiddenChanged.flush(),this.__intrinsicWidthCache=new Map,e.forEach((e=>{e.width=`${this.__getDistributedWidth(e)}px`}))}recalculateColumnWidths(){if(this._columnTree)if(this._cache.isLoading())this._recalculateColumnWidthOnceLoadingFinished=!0;else{const e=this._getColumns().filter((e=>!e.hidden&&e.autoWidth));this._recalculateColumnWidths(e)}}_createScrollerRows(e){const t=[];for(let r=0;r<e;r++){const e=document.createElement("tr");e.setAttribute("part","row"),e.setAttribute("role","row"),e.setAttribute("tabindex","-1"),this._columnTree&&this._updateRow(e,this._columnTree[this._columnTree.length-1],"body",!1,!0),t.push(e)}return this._columnTree&&this._columnTree[this._columnTree.length-1].forEach((e=>e.isConnected&&e.notifyPath&&e.notifyPath("_cells.*",e._cells))),P(this,(()=>{this._updateFirstAndLastColumn(),this._resetKeyboardNavigation(),this._afterScroll(),this.__itemsReceived()})),t}_createCell(e,t){const r=`vaadin-grid-cell-content-${this._contentIndex=this._contentIndex+1||0}`,i=document.createElement("vaadin-grid-cell-content");i.setAttribute("slot",r);const o=document.createElement(e);o.id=r.replace("-content-","-"),o.setAttribute("role","td"===e?"gridcell":"columnheader"),k||F||(o.addEventListener("mouseenter",(e=>{this.$.scroller.hasAttribute("scrolling")||this._showTooltip(e)})),o.addEventListener("mouseleave",(()=>{this._hideTooltip()})),o.addEventListener("mousedown",(()=>{this._hideTooltip(!0)})));const s=document.createElement("slot");if(s.setAttribute("name",r),t&&t._focusButtonMode){const e=document.createElement("div");e.setAttribute("role","button"),e.setAttribute("tabindex","-1"),o.appendChild(e),o._focusButton=e,o.focus=function(){o._focusButton.focus()},e.appendChild(s)}else o.setAttribute("tabindex","-1"),o.appendChild(s);return o._content=i,i.addEventListener("mousedown",(()=>{if(D){const e=t=>{const r=i.contains(this.getRootNode().activeElement),s=t.composedPath().includes(i);!r&&s&&o.focus(),document.removeEventListener("mouseup",e,!0)};document.addEventListener("mouseup",e,!0)}else setTimeout((()=>{i.contains(this.getRootNode().activeElement)||o.focus()}))})),o}_updateRow(e,t,r="body",i=!1,o=!1){const s=document.createDocumentFragment();U(e,(e=>{e._vacant=!0})),e.innerHTML="",t.filter((e=>!e.hidden)).forEach(((t,n,a)=>{let l;if("body"===r){if(t._cells||(t._cells=[]),l=t._cells.find((e=>e._vacant)),l||(l=this._createCell("td",t),t._cells.push(l)),l.setAttribute("part","cell body-cell"),e.appendChild(l),n===a.length-1&&this.rowDetailsRenderer){this._detailsCells||(this._detailsCells=[]);const t=this._detailsCells.find((e=>e._vacant))||this._createCell("td");-1===this._detailsCells.indexOf(t)&&this._detailsCells.push(t),t._content.parentElement||s.appendChild(t._content),this._configureDetailsCell(t),e.appendChild(t),this._a11ySetRowDetailsCell(e,t),t._vacant=!1}t.notifyPath&&!o&&t.notifyPath("_cells.*",t._cells)}else{const o="header"===r?"th":"td";i||"vaadin-grid-column-group"===t.localName?(l=t[`_${r}Cell`]||this._createCell(o),l._column=t,e.appendChild(l),t[`_${r}Cell`]=l):(t._emptyCells||(t._emptyCells=[]),l=t._emptyCells.find((e=>e._vacant))||this._createCell(o),l._column=t,e.appendChild(l),-1===t._emptyCells.indexOf(l)&&t._emptyCells.push(l)),l.setAttribute("part",`cell ${r}-cell`)}l._content.parentElement||s.appendChild(l._content),l._vacant=!1,l._column=t})),"body"!==r&&this.__debounceUpdateHeaderFooterRowVisibility(e),this.appendChild(s),this._frozenCellsChanged(),this._updateFirstAndLastColumnForRow(e)}__debounceUpdateHeaderFooterRowVisibility(e){e.__debounceUpdateHeaderFooterRowVisibility=v.debounce(e.__debounceUpdateHeaderFooterRowVisibility,A,(()=>this.__updateHeaderFooterRowVisibility(e)))}__updateHeaderFooterRowVisibility(e){if(!e)return;const t=Array.from(e.children).filter((t=>{const r=t._column;if(r._emptyCells&&r._emptyCells.indexOf(t)>-1)return!1;if(e.parentElement===this.$.header){if(r.headerRenderer)return!0;if(null===r.header)return!1;if(r.path||void 0!==r.header)return!0}else if(r.footerRenderer)return!0;return!1}));e.hidden!==!t.length&&(e.hidden=!t.length),this._resetKeyboardNavigation()}_updateScrollerItem(e,t){this._preventScrollerRotatingCellFocus(e,t),this._columnTree&&(this._updateRowOrderParts(e,t),this._a11yUpdateRowRowindex(e,t),this._getItem(t,e))}_columnTreeChanged(e){this._renderColumnTree(e),this.recalculateColumnWidths()}_updateRowOrderParts(e,t=e.index){j(e,{first:0===t,last:t===this._effectiveSize-1,odd:t%2!=0,even:t%2==0})}_updateRowStateParts(e,{expanded:t,selected:r,detailsOpened:i}){j(e,{expanded:t,selected:r,"details-opened":i})}_renderColumnTree(e){for(U(this.$.items,(t=>{this._updateRow(t,e[e.length-1],"body",!1,!0);const r=this.__getRowModel(t);this._updateRowOrderParts(t),this._updateRowStateParts(t,r),this._filterDragAndDrop(t,r)}));this.$.header.children.length<e.length;){const e=document.createElement("tr");e.setAttribute("part","row"),e.setAttribute("role","row"),e.setAttribute("tabindex","-1"),this.$.header.appendChild(e);const t=document.createElement("tr");t.setAttribute("part","row"),t.setAttribute("role","row"),t.setAttribute("tabindex","-1"),this.$.footer.appendChild(t)}for(;this.$.header.children.length>e.length;)this.$.header.removeChild(this.$.header.firstElementChild),this.$.footer.removeChild(this.$.footer.firstElementChild);U(this.$.header,((t,r,i)=>{this._updateRow(t,e[r],"header",r===e.length-1);const o=G(t);K(o,"first-header-row-cell",0===r),K(o,"last-header-row-cell",r===i.length-1)})),U(this.$.footer,((t,r,i)=>{this._updateRow(t,e[e.length-1-r],"footer",0===r);const o=G(t);K(o,"first-footer-row-cell",0===r),K(o,"last-footer-row-cell",r===i.length-1)})),this._updateRow(this.$.sizer,e[e.length-1]),this._resizeHandler(),this._frozenCellsChanged(),this._updateFirstAndLastColumn(),this._resetKeyboardNavigation(),this._a11yUpdateHeaderRows(),this._a11yUpdateFooterRows(),this.__updateFooterPositioning(),this.generateCellClassNames(),this.generateCellPartNames()}__updateFooterPositioning(){this._firefox&&parseFloat(navigator.userAgent.match(/Firefox\/(\d{2,3}.\d)/u)[1])<99&&(this.$.items.style.paddingBottom=0,this.allRowsVisible||(this.$.items.style.paddingBottom=`${this.$.footer.offsetHeight}px`))}_updateItem(e,t){e._item=t;const r=this.__getRowModel(e);this._toggleDetailsCell(e,r.detailsOpened),this._a11yUpdateRowLevel(e,r.level),this._a11yUpdateRowSelected(e,r.selected),this._updateRowStateParts(e,r),this._generateCellClassNames(e,r),this._generateCellPartNames(e,r),this._filterDragAndDrop(e,r),U(e,(e=>{if(e._renderer){const t=e._column||this;e._renderer.call(t,e._content,t,r)}})),this._updateDetailsCellHeight(e),this._a11yUpdateRowExpanded(e,r.expanded)}_resizeHandler(){this._updateDetailsCellHeights(),this.__updateFooterPositioning(),this.__updateHorizontalScrollPosition()}_onAnimationEnd(e){0===e.animationName.indexOf("vaadin-grid-appear")&&(e.stopPropagation(),this.__itemsReceived(),requestAnimationFrame((()=>{this.__scrollToPendingIndex()})))}__getRowModel(e){return{index:e.index,item:e._item,level:this._getIndexLevel(e.index),expanded:this._isExpanded(e._item),selected:this._isSelected(e._item),detailsOpened:!!this.rowDetailsRenderer&&this._isDetailsOpened(e._item)}}_showTooltip(e){const t=this._tooltipController.node;t&&t.isConnected&&(this._tooltipController.setTarget(e.target),this._tooltipController.setContext(this.getEventContext(e)),t._stateController.open({focus:"focusin"===e.type,hover:"mouseenter"===e.type}))}_hideTooltip(e){const t=this._tooltipController.node;t&&t._stateController.close(e)}requestContentUpdate(){this._columnTree&&(this._columnTree.forEach((e=>{e.forEach((e=>{e._renderHeaderAndFooter&&e._renderHeaderAndFooter()}))})),this.__updateVisibleRows())}__updateVisibleRows(e,t){this.__virtualizer&&this.__virtualizer.update(e,t)}}customElements.define(Pe.is,Pe);export{Y as C,J as G,Q as i,W as u};
