import{_ as e,e as t,c as i,a as s,s as o,d as n,I as a,b as r,k as l,f as d,i as c,y as h,B as u,h as p,g as m,Z as _,t as v,o as g}from"./backend-ai-webui-4b02c088.js";import"./lablup-progress-bar-b0e5bcbd.js";import"./mwc-check-list-item-81004ff1.js";import"./slider-d1a6e840.js";import{r as f,n as y,o as b,T as x,D as w,j as k,P as D,h as C,p as S,q as I,s as T,A as E,t as P,l as $,E as M,k as A,v as O,w as z,x as R,y as B,z as F,B as V,H as L,I as N,J as q,K as j,L as H,M as G,N as W,O as U,Q as Y,e as K,R as X,g as Q,S as J,U as Z,V as ee,W as te,X as ie,Y as se,Z as oe,_ as ne,$ as ae,a0 as re}from"./vaadin-grid-29ec191a.js";import{i as le,I as de,a as ce,b as he,r as ue,h as pe,F as me}from"./vaadin-grid-filter-column-6a650597.js";import"./vaadin-grid-selection-column-d16c73ef.js";import{i as _e}from"./vaadin-item-styles-2991341a.js";import"./expansion-4ecf0e05.js";import"./label-fece23ff.js";import"./lablup-codemirror-aef5e7e5.js";
/**
 @license
 Copyright (c) 2015-2023 Lablup Inc. All rights reserved.
 */let ve=class extends o{static get styles(){return[n,a,r,l,d,c`
        mwc-textfield {
          width: var(--textfield-min-width, 65px);
          height: 40px;
          margin-left: 10px;
          // --mdc-theme-primary: transparent;
          --mdc-text-field-hover-line-color: transparent;
          --mdc-text-field-idle-line-color: transparent;
        }

        mwc-slider {
          width: var(--slider-width, 100px);
          --mdc-theme-secondary: var(--slider-color, '#018786');
          color: var(--paper-grey-700);
        }
      `]}render(){return h`
      <div class="horizontal center layout">
        <mwc-slider
          id="slider" class="${this.id}"
          value="${this.value}" min="${this.min}" max="${this.max}" step="${this.step}"
          ?pin="${this.pin}"
          ?disabled="${this.disabled}"
          ?markers="${this.markers}"
          @change="${()=>this.syncToText()}"
        ></mwc-slider>
        <mwc-textfield
          id="textfield" class="${this.id}"
          type="number"
          value="${this.value}" min="${this.min}" max="${this.max}" step="${this.step}"
          prefix="${this.prefix}" suffix="${this.suffix}"
          ?disabled="${this.disabled}"
          @change="${()=>this.syncToSlider()}"
        ></mwc-textfield>
      </div>
    `}constructor(){super(),this.editable=!1,this.pin=!1,this.markers=!1,this.marker_limit=30,this.disabled=!1;new IntersectionObserver(((e,t)=>{e.forEach((e=>{e.intersectionRatio>0&&(this.value!==this.slider.value&&(this.slider.value=this.value),this.slider.layout())}))}),{}).observe(this)}firstUpdated(){this.editable&&(this.textfield.style.display="flex"),this.checkMarkerDisplay()}update(e){Array.from(e.keys()).some((e=>["value","min","max"].includes(e)))&&this.min==this.max&&(this.max=this.max+1,this.value=this.min,this.disabled=!0),super.update(e)}updated(e){e.forEach(((e,t)=>{["min","max","step"].includes(t)&&this.checkMarkerDisplay()}))}syncToText(){this.value=this.slider.value}syncToSlider(){this.textfield.step=this.step;const e=Math.round(this.textfield.value/this.step)*this.step;var t;this.textfield.value=e.toFixed((t=this.step,Math.floor(t)===t?0:t.toString().split(".")[1].length||0)),this.textfield.value>this.max&&(this.textfield.value=this.max),this.textfield.value<this.min&&(this.textfield.value=this.min),this.value=this.textfield.value;const i=new CustomEvent("change",{detail:{}});this.dispatchEvent(i)}checkMarkerDisplay(){this.markers&&(this.max-this.min)/this.step>this.marker_limit&&this.slider.removeAttribute("markers")}};e([t({type:Number})],ve.prototype,"step",void 0),e([t({type:Number})],ve.prototype,"value",void 0),e([t({type:Number})],ve.prototype,"max",void 0),e([t({type:Number})],ve.prototype,"min",void 0),e([t({type:String})],ve.prototype,"prefix",void 0),e([t({type:String})],ve.prototype,"suffix",void 0),e([t({type:Boolean})],ve.prototype,"editable",void 0),e([t({type:Boolean})],ve.prototype,"pin",void 0),e([t({type:Boolean})],ve.prototype,"markers",void 0),e([t({type:Number})],ve.prototype,"marker_limit",void 0),e([t({type:Boolean})],ve.prototype,"disabled",void 0),e([i("#slider",!0)],ve.prototype,"slider",void 0),e([i("#textfield",!0)],ve.prototype,"textfield",void 0),ve=e([s("lablup-slider")],ve);
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const ge=c`
  :host {
    top: var(--lumo-space-m);
    right: var(--lumo-space-m);
    bottom: var(--lumo-space-m);
    left: var(--lumo-space-m);
    /* Workaround for Edge issue (only on Surface), where an overflowing vaadin-list-box inside vaadin-select-overlay makes the overlay transparent */
    /* stylelint-disable-next-line */
    outline: 0px solid transparent;
  }

  [part='overlay'] {
    background-color: var(--lumo-base-color);
    background-image: linear-gradient(var(--lumo-tint-5pct), var(--lumo-tint-5pct));
    border-radius: var(--lumo-border-radius-m);
    box-shadow: 0 0 0 1px var(--lumo-shade-5pct), var(--lumo-box-shadow-m);
    color: var(--lumo-body-text-color);
    font-family: var(--lumo-font-family);
    font-size: var(--lumo-font-size-m);
    font-weight: 400;
    line-height: var(--lumo-line-height-m);
    letter-spacing: 0;
    text-transform: none;
    -webkit-text-size-adjust: 100%;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  [part='content'] {
    padding: var(--lumo-space-xs);
  }

  [part='backdrop'] {
    background-color: var(--lumo-shade-20pct);
    animation: 0.2s lumo-overlay-backdrop-enter both;
    will-change: opacity;
  }

  @keyframes lumo-overlay-backdrop-enter {
    0% {
      opacity: 0;
    }
  }

  :host([closing]) [part='backdrop'] {
    animation: 0.2s lumo-overlay-backdrop-exit both;
  }

  @keyframes lumo-overlay-backdrop-exit {
    100% {
      opacity: 0;
    }
  }

  @keyframes lumo-overlay-dummy-animation {
    0% {
      opacity: 1;
    }

    100% {
      opacity: 1;
    }
  }
`;f("",ge,{moduleId:"lumo-overlay"}),f("vaadin-overlay",ge,{moduleId:"lumo-vaadin-overlay"});
/**
 * @license
 * Copyright (c) 2021 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const fe=[];class ye{constructor(e){this.host=e,this.__trapNode=null,this.__onKeyDown=this.__onKeyDown.bind(this)}get __focusableElements(){return y(this.__trapNode)}get __focusedElementIndex(){const e=this.__focusableElements;return e.indexOf(e.filter(b).pop())}hostConnected(){document.addEventListener("keydown",this.__onKeyDown)}hostDisconnected(){document.removeEventListener("keydown",this.__onKeyDown)}trapFocus(e){if(this.__trapNode=e,0===this.__focusableElements.length)throw this.__trapNode=null,new Error("The trap node should have at least one focusable descendant or be focusable itself.");fe.push(this),-1===this.__focusedElementIndex&&this.__focusableElements[0].focus()}releaseFocus(){this.__trapNode=null,fe.pop()}__onKeyDown(e){if(this.__trapNode&&this===Array.from(fe).pop()&&"Tab"===e.key){e.preventDefault();const t=e.shiftKey;this.__focusNextElement(t)}}__focusNextElement(e=!1){const t=this.__focusableElements,i=e?-1:1,s=this.__focusedElementIndex,o=t[(t.length+s+i)%t.length];o.focus(),"input"===o.localName&&o.select()}}
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */class be extends(x(w(k(D)))){static get template(){return C`
      <style>
        :host {
          z-index: 200;
          position: fixed;

          /* Despite of what the names say, <vaadin-overlay> is just a container
          for position/sizing/alignment. The actual overlay is the overlay part. */

          /* Default position constraints: the entire viewport. Note: themes can
          override this to introduce gaps between the overlay and the viewport. */
          top: 0;
          right: 0;
          bottom: var(--vaadin-overlay-viewport-bottom);
          left: 0;

          /* Use flexbox alignment for the overlay part. */
          display: flex;
          flex-direction: column; /* makes dropdowns sizing easier */
          /* Align to center by default. */
          align-items: center;
          justify-content: center;

          /* Allow centering when max-width/max-height applies. */
          margin: auto;

          /* The host is not clickable, only the overlay part is. */
          pointer-events: none;

          /* Remove tap highlight on touch devices. */
          -webkit-tap-highlight-color: transparent;

          /* CSS API for host */
          --vaadin-overlay-viewport-bottom: 0;
        }

        :host([hidden]),
        :host(:not([opened]):not([closing])) {
          display: none !important;
        }

        [part='overlay'] {
          -webkit-overflow-scrolling: touch;
          overflow: auto;
          pointer-events: auto;

          /* Prevent overflowing the host in MSIE 11 */
          max-width: 100%;
          box-sizing: border-box;

          -webkit-tap-highlight-color: initial; /* reenable tap highlight inside */
        }

        [part='backdrop'] {
          z-index: -1;
          content: '';
          background: rgba(0, 0, 0, 0.5);
          position: fixed;
          top: 0;
          left: 0;
          bottom: 0;
          right: 0;
          pointer-events: auto;
        }
      </style>

      <div id="backdrop" part="backdrop" hidden$="[[!withBackdrop]]"></div>
      <div part="overlay" id="overlay" tabindex="0">
        <div part="content" id="content">
          <slot></slot>
        </div>
      </div>
    `}static get is(){return"vaadin-overlay"}static get properties(){return{opened:{type:Boolean,notify:!0,observer:"_openedChanged",reflectToAttribute:!0},owner:Element,renderer:Function,withBackdrop:{type:Boolean,value:!1,reflectToAttribute:!0},model:Object,modeless:{type:Boolean,value:!1,reflectToAttribute:!0,observer:"_modelessChanged"},hidden:{type:Boolean,reflectToAttribute:!0,observer:"_hiddenChanged"},focusTrap:{type:Boolean,value:!1},restoreFocusOnClose:{type:Boolean,value:!1},restoreFocusNode:{type:HTMLElement},_mouseDownInside:{type:Boolean},_mouseUpInside:{type:Boolean},_oldOwner:Element,_oldModel:Object,_oldRenderer:Object,_oldOpened:Boolean}}static get observers(){return["_rendererOrDataChanged(renderer, owner, model, opened)"]}static get __attachedInstances(){return Array.from(document.body.children).filter((e=>e instanceof be&&!e.hasAttribute("closing"))).sort(((e,t)=>e.__zIndex-t.__zIndex||0))}constructor(){super(),this._boundMouseDownListener=this._mouseDownListener.bind(this),this._boundMouseUpListener=this._mouseUpListener.bind(this),this._boundOutsideClickListener=this._outsideClickListener.bind(this),this._boundKeydownListener=this._keydownListener.bind(this),S&&(this._boundIosResizeListener=()=>this._detectIosNavbar()),this.__focusTrapController=new ye(this)}get _last(){return this===be.__attachedInstances.pop()}ready(){super.ready(),this.addEventListener("click",(()=>{})),this.$.backdrop.addEventListener("click",(()=>{})),this.addController(this.__focusTrapController),I(this)}_detectIosNavbar(){if(!this.opened)return;const e=window.innerHeight,t=window.innerWidth>e,i=document.documentElement.clientHeight;t&&i>e?this.style.setProperty("--vaadin-overlay-viewport-bottom",i-e+"px"):this.style.setProperty("--vaadin-overlay-viewport-bottom","0")}close(e){const t=new CustomEvent("vaadin-overlay-close",{bubbles:!0,cancelable:!0,detail:{sourceEvent:e}});this.dispatchEvent(t),t.defaultPrevented||(this.opened=!1)}connectedCallback(){super.connectedCallback(),this._boundIosResizeListener&&(this._detectIosNavbar(),window.addEventListener("resize",this._boundIosResizeListener))}disconnectedCallback(){super.disconnectedCallback(),this._boundIosResizeListener&&window.removeEventListener("resize",this._boundIosResizeListener)}requestContentUpdate(){this.renderer&&this.renderer.call(this.owner,this,this.owner,this.model)}_mouseDownListener(e){this._mouseDownInside=e.composedPath().indexOf(this.$.overlay)>=0}_mouseUpListener(e){this._mouseUpInside=e.composedPath().indexOf(this.$.overlay)>=0}_shouldCloseOnOutsideClick(e){return this._last}_outsideClickListener(e){if(e.composedPath().includes(this.$.overlay)||this._mouseDownInside||this._mouseUpInside)return this._mouseDownInside=!1,void(this._mouseUpInside=!1);if(!this._shouldCloseOnOutsideClick(e))return;const t=new CustomEvent("vaadin-overlay-outside-click",{bubbles:!0,cancelable:!0,detail:{sourceEvent:e}});this.dispatchEvent(t),this.opened&&!t.defaultPrevented&&this.close(e)}_keydownListener(e){if(this._last&&(!this.modeless||e.composedPath().includes(this.$.overlay))&&"Escape"===e.key){const t=new CustomEvent("vaadin-overlay-escape-press",{bubbles:!0,cancelable:!0,detail:{sourceEvent:e}});this.dispatchEvent(t),this.opened&&!t.defaultPrevented&&this.close(e)}}_openedChanged(e,t){e?(this.__restoreFocusNode=this._getActiveElement(),this._animatedOpening(),T(this,(()=>{this.focusTrap&&this.__focusTrapController.trapFocus(this.$.overlay);const e=new CustomEvent("vaadin-overlay-open",{bubbles:!0});this.dispatchEvent(e)})),document.addEventListener("keydown",this._boundKeydownListener),this.modeless||this._addGlobalListeners()):t&&(this.focusTrap&&this.__focusTrapController.releaseFocus(),this._animatedClosing(),document.removeEventListener("keydown",this._boundKeydownListener),this.modeless||this._removeGlobalListeners())}_hiddenChanged(e){e&&this.hasAttribute("closing")&&this._flushAnimation("closing")}_shouldAnimate(){const e=getComputedStyle(this),t=e.getPropertyValue("animation-name");return!("none"===e.getPropertyValue("display"))&&t&&"none"!==t}_enqueueAnimation(e,t){const i=`__${e}Handler`,s=e=>{e&&e.target!==this||(t(),this.removeEventListener("animationend",s),delete this[i])};this[i]=s,this.addEventListener("animationend",s)}_flushAnimation(e){const t=`__${e}Handler`;"function"==typeof this[t]&&this[t]()}_animatedOpening(){this.parentNode===document.body&&this.hasAttribute("closing")&&this._flushAnimation("closing"),this._attachOverlay(),this.modeless||this._enterModalState(),this.setAttribute("opening",""),this._shouldAnimate()?this._enqueueAnimation("opening",(()=>{this._finishOpening()})):this._finishOpening()}_attachOverlay(){this._placeholder=document.createComment("vaadin-overlay-placeholder"),this.parentNode.insertBefore(this._placeholder,this),document.body.appendChild(this),this.bringToFront()}_finishOpening(){this.removeAttribute("opening")}_finishClosing(){this._detachOverlay(),this.$.overlay.style.removeProperty("pointer-events"),this.removeAttribute("closing"),this.dispatchEvent(new CustomEvent("vaadin-overlay-closed"))}_animatedClosing(){if(this.hasAttribute("opening")&&this._flushAnimation("opening"),this._placeholder){this._exitModalState();const e=this.restoreFocusNode||this.__restoreFocusNode;if(this.restoreFocusOnClose&&e){const t=this._getActiveElement();(t===document.body||this._deepContains(t))&&setTimeout((()=>e.focus())),this.__restoreFocusNode=null}this.setAttribute("closing",""),this.dispatchEvent(new CustomEvent("vaadin-overlay-closing")),this._shouldAnimate()?this._enqueueAnimation("closing",(()=>{this._finishClosing()})):this._finishClosing()}}_detachOverlay(){this._placeholder.parentNode.insertBefore(this,this._placeholder),this._placeholder.parentNode.removeChild(this._placeholder)}_modelessChanged(e){e?(this._removeGlobalListeners(),this._exitModalState()):this.opened&&(this._addGlobalListeners(),this._enterModalState())}_addGlobalListeners(){document.addEventListener("mousedown",this._boundMouseDownListener),document.addEventListener("mouseup",this._boundMouseUpListener),document.documentElement.addEventListener("click",this._boundOutsideClickListener,!0)}_enterModalState(){"none"!==document.body.style.pointerEvents&&(this._previousDocumentPointerEvents=document.body.style.pointerEvents,document.body.style.pointerEvents="none"),be.__attachedInstances.forEach((e=>{e!==this&&(e.shadowRoot.querySelector('[part="overlay"]').style.pointerEvents="none")}))}_removeGlobalListeners(){document.removeEventListener("mousedown",this._boundMouseDownListener),document.removeEventListener("mouseup",this._boundMouseUpListener),document.documentElement.removeEventListener("click",this._boundOutsideClickListener,!0)}_exitModalState(){void 0!==this._previousDocumentPointerEvents&&(document.body.style.pointerEvents=this._previousDocumentPointerEvents,delete this._previousDocumentPointerEvents);const e=be.__attachedInstances;let t;for(;(t=e.pop())&&(t===this||(t.shadowRoot.querySelector('[part="overlay"]').style.removeProperty("pointer-events"),t.modeless)););}_rendererOrDataChanged(e,t,i,s){const o=this._oldOwner!==t||this._oldModel!==i;this._oldModel=i,this._oldOwner=t;const n=this._oldRenderer!==e;this._oldRenderer=e;const a=this._oldOpened!==s;this._oldOpened=s,n&&(this.innerHTML="",delete this._$litPart$),s&&e&&(n||a||o)&&this.requestContentUpdate()}_getActiveElement(){let e=document.activeElement||document.body;for(;e.shadowRoot&&e.shadowRoot.activeElement;)e=e.shadowRoot.activeElement;return e}_deepContains(e){if(this.contains(e))return!0;let t=e;const i=e.ownerDocument;for(;t&&t!==i&&t!==this;)t=t.parentNode||t.host;return t===this}bringToFront(){let e="";const t=be.__attachedInstances.filter((e=>e!==this)).pop();if(t){e=t.__zIndex+1}this.style.zIndex=e,this.__zIndex=e||parseFloat(getComputedStyle(this).zIndex)}}customElements.define(be.is,be);
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const xe=c`
  :host([opening]),
  :host([closing]) {
    animation: 0.14s lumo-overlay-dummy-animation;
  }

  [part='overlay'] {
    will-change: opacity, transform;
  }

  :host([opening]) [part='overlay'] {
    animation: 0.1s lumo-menu-overlay-enter ease-out both;
  }

  @keyframes lumo-menu-overlay-enter {
    0% {
      opacity: 0;
      transform: translateY(-4px);
    }
  }

  :host([closing]) [part='overlay'] {
    animation: 0.1s lumo-menu-overlay-exit both;
  }

  @keyframes lumo-menu-overlay-exit {
    100% {
      opacity: 0;
    }
  }
`;f("",xe,{moduleId:"lumo-menu-overlay-core"});const we=[ge,xe,c`
  /* Small viewport (bottom sheet) styles */
  /* Use direct media queries instead of the state attributes ([phone] and [fullscreen]) provided by the elements */
  @media (max-width: 420px), (max-height: 420px) {
    :host {
      top: 0 !important;
      right: 0 !important;
      bottom: var(--vaadin-overlay-viewport-bottom, 0) !important;
      left: 0 !important;
      align-items: stretch !important;
      justify-content: flex-end !important;
    }

    [part='overlay'] {
      max-height: 50vh;
      width: 100vw;
      border-radius: 0;
      box-shadow: var(--lumo-box-shadow-xl);
    }

    /* The content part scrolls instead of the overlay part, because of the gradient fade-out */
    [part='content'] {
      padding: 30px var(--lumo-space-m);
      max-height: inherit;
      box-sizing: border-box;
      -webkit-overflow-scrolling: touch;
      overflow: auto;
      -webkit-mask-image: linear-gradient(transparent, #000 40px, #000 calc(100% - 40px), transparent);
      mask-image: linear-gradient(transparent, #000 40px, #000 calc(100% - 40px), transparent);
    }

    [part='backdrop'] {
      display: block;
    }

    /* Animations */

    :host([opening]) [part='overlay'] {
      animation: 0.2s lumo-mobile-menu-overlay-enter cubic-bezier(0.215, 0.61, 0.355, 1) both;
    }

    :host([closing]),
    :host([closing]) [part='backdrop'] {
      animation-delay: 0.14s;
    }

    :host([closing]) [part='overlay'] {
      animation: 0.14s 0.14s lumo-mobile-menu-overlay-exit cubic-bezier(0.55, 0.055, 0.675, 0.19) both;
    }
  }

  @keyframes lumo-mobile-menu-overlay-enter {
    0% {
      transform: translateY(150%);
    }
  }

  @keyframes lumo-mobile-menu-overlay-exit {
    100% {
      transform: translateY(150%);
    }
  }
`];f("",we,{moduleId:"lumo-menu-overlay"});f("vaadin-date-picker-overlay",[we,c`
  [part='overlay'] {
    /*
  Width:
      date cell widths
    + month calendar side padding
    + year scroller width
  */
    /* prettier-ignore */
    width:
    calc(
        var(--lumo-size-m) * 7
      + var(--lumo-space-xs) * 2
      + 57px
    );
    height: 100%;
    max-height: calc(var(--lumo-size-m) * 14);
    overflow: hidden;
    -webkit-tap-highlight-color: transparent;
  }

  [part='overlay'] {
    flex-direction: column;
  }

  [part='content'] {
    padding: 0;
    height: 100%;
    overflow: hidden;
    -webkit-mask-image: none;
    mask-image: none;
  }

  :host([top-aligned]) [part~='overlay'] {
    margin-top: var(--lumo-space-xs);
  }

  :host([bottom-aligned]) [part~='overlay'] {
    margin-bottom: var(--lumo-space-xs);
  }

  @media (max-width: 420px), (max-height: 420px) {
    [part='overlay'] {
      width: 100vw;
      height: 70vh;
      max-height: 70vh;
    }
  }
`],{moduleId:"lumo-date-picker-overlay"});f("vaadin-button",c`
  :host {
    /* Sizing */
    --lumo-button-size: var(--lumo-size-m);
    min-width: calc(var(--lumo-button-size) * 2);
    height: var(--lumo-button-size);
    padding: 0 calc(var(--lumo-button-size) / 3 + var(--lumo-border-radius-m) / 2);
    margin: var(--lumo-space-xs) 0;
    box-sizing: border-box;
    /* Style */
    font-family: var(--lumo-font-family);
    font-size: var(--lumo-font-size-m);
    font-weight: 500;
    color: var(--_lumo-button-color, var(--lumo-primary-text-color));
    background-color: var(--_lumo-button-background-color, var(--lumo-contrast-5pct));
    border-radius: var(--lumo-border-radius-m);
    cursor: var(--lumo-clickable-cursor);
    -webkit-tap-highlight-color: transparent;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    flex-shrink: 0;
  }

  /* Set only for the internal parts so we don't affect the host vertical alignment */
  [part='label'],
  [part='prefix'],
  [part='suffix'] {
    line-height: var(--lumo-line-height-xs);
  }

  [part='label'] {
    padding: calc(var(--lumo-button-size) / 6) 0;
  }

  :host([theme~='small']) {
    font-size: var(--lumo-font-size-s);
    --lumo-button-size: var(--lumo-size-s);
  }

  :host([theme~='large']) {
    font-size: var(--lumo-font-size-l);
    --lumo-button-size: var(--lumo-size-l);
  }

  /* For interaction states */
  :host::before,
  :host::after {
    content: '';
    /* We rely on the host always being relative */
    position: absolute;
    z-index: 1;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    background-color: currentColor;
    border-radius: inherit;
    opacity: 0;
    pointer-events: none;
  }

  /* Hover */

  @media (any-hover: hover) {
    :host(:hover)::before {
      opacity: 0.02;
    }
  }

  /* Active */

  :host::after {
    transition: opacity 1.4s, transform 0.1s;
    filter: blur(8px);
  }

  :host([active])::before {
    opacity: 0.05;
    transition-duration: 0s;
  }

  :host([active])::after {
    opacity: 0.1;
    transition-duration: 0s, 0s;
    transform: scale(0);
  }

  /* Keyboard focus */

  :host([focus-ring]) {
    box-shadow: 0 0 0 2px var(--lumo-primary-color-50pct);
  }

  :host([theme~='primary'][focus-ring]) {
    box-shadow: 0 0 0 1px var(--lumo-base-color), 0 0 0 3px var(--lumo-primary-color-50pct);
  }

  /* Types (primary, tertiary, tertiary-inline */

  :host([theme~='tertiary']),
  :host([theme~='tertiary-inline']) {
    background-color: transparent !important;
    min-width: 0;
  }

  :host([theme~='tertiary']) {
    padding: 0 calc(var(--lumo-button-size) / 6);
  }

  :host([theme~='tertiary-inline'])::before {
    display: none;
  }

  :host([theme~='tertiary-inline']) {
    margin: 0;
    height: auto;
    padding: 0;
    line-height: inherit;
    font-size: inherit;
  }

  :host([theme~='tertiary-inline']) [part='label'] {
    padding: 0;
    overflow: visible;
    line-height: inherit;
  }

  :host([theme~='primary']) {
    background-color: var(--_lumo-button-primary-background-color, var(--lumo-primary-color));
    color: var(--_lumo-button-primary-color, var(--lumo-primary-contrast-color));
    font-weight: 600;
    min-width: calc(var(--lumo-button-size) * 2.5);
  }

  :host([theme~='primary'])::before {
    background-color: black;
  }

  @media (any-hover: hover) {
    :host([theme~='primary']:hover)::before {
      opacity: 0.05;
    }
  }

  :host([theme~='primary'][active])::before {
    opacity: 0.1;
  }

  :host([theme~='primary'][active])::after {
    opacity: 0.2;
  }

  /* Colors (success, error, contrast) */

  :host([theme~='success']) {
    color: var(--lumo-success-text-color);
  }

  :host([theme~='success'][theme~='primary']) {
    background-color: var(--lumo-success-color);
    color: var(--lumo-success-contrast-color);
  }

  :host([theme~='error']) {
    color: var(--lumo-error-text-color);
  }

  :host([theme~='error'][theme~='primary']) {
    background-color: var(--lumo-error-color);
    color: var(--lumo-error-contrast-color);
  }

  :host([theme~='contrast']) {
    color: var(--lumo-contrast);
  }

  :host([theme~='contrast'][theme~='primary']) {
    background-color: var(--lumo-contrast);
    color: var(--lumo-base-color);
  }

  /* Disabled state. Keep selectors after other color variants. */

  :host([disabled]) {
    pointer-events: none;
    color: var(--lumo-disabled-text-color);
  }

  :host([theme~='primary'][disabled]) {
    background-color: var(--lumo-contrast-30pct);
    color: var(--lumo-base-color);
  }

  :host([theme~='primary'][disabled]) [part] {
    opacity: 0.7;
  }

  /* Icons */

  [part] ::slotted(vaadin-icon) {
    display: inline-block;
    width: var(--lumo-icon-size-m);
    height: var(--lumo-icon-size-m);
  }

  /* Vaadin icons are based on a 16x16 grid (unlike Lumo and Material icons with 24x24), so they look too big by default */
  [part] ::slotted(vaadin-icon[icon^='vaadin:']) {
    padding: 0.25em;
    box-sizing: border-box !important;
  }

  [part='prefix'] {
    margin-left: -0.25em;
    margin-right: 0.25em;
  }

  [part='suffix'] {
    margin-left: 0.25em;
    margin-right: -0.25em;
  }

  /* Icon-only */

  :host([theme~='icon']:not([theme~='tertiary-inline'])) {
    min-width: var(--lumo-button-size);
    padding-left: calc(var(--lumo-button-size) / 4);
    padding-right: calc(var(--lumo-button-size) / 4);
  }

  :host([theme~='icon']) [part='prefix'],
  :host([theme~='icon']) [part='suffix'] {
    margin-left: 0;
    margin-right: 0;
  }

  /* RTL specific styles */

  :host([dir='rtl']) [part='prefix'] {
    margin-left: 0.25em;
    margin-right: -0.25em;
  }

  :host([dir='rtl']) [part='suffix'] {
    margin-left: -0.25em;
    margin-right: 0.25em;
  }

  :host([dir='rtl'][theme~='icon']) [part='prefix'],
  :host([dir='rtl'][theme~='icon']) [part='suffix'] {
    margin-left: 0;
    margin-right: 0;
  }
`,{moduleId:"lumo-button"});
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const ke=c`
  :host {
    display: inline-block;
    position: relative;
    outline: none;
    white-space: nowrap;
    -webkit-user-select: none;
    -moz-user-select: none;
    user-select: none;
  }

  :host([hidden]) {
    display: none !important;
  }

  /* Aligns the button with form fields when placed on the same line.
  Note, to make it work, the form fields should have the same "::before" pseudo-element. */
  .vaadin-button-container::before {
    content: '\\2003';
    display: inline-block;
    width: 0;
    max-height: 100%;
  }

  .vaadin-button-container {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    width: 100%;
    height: 100%;
    min-height: inherit;
    text-shadow: inherit;
  }

  [part='prefix'],
  [part='suffix'] {
    flex: none;
  }

  [part='label'] {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
`,De=e=>class extends(E(P($(e)))){static get properties(){return{tabindex:{type:Number,value:0,reflectToAttribute:!0}}}get _activeKeys(){return["Enter"," "]}ready(){super.ready(),this.hasAttribute("role")||this.setAttribute("role","button")}_onKeyDown(e){super._onKeyDown(e),this._activeKeys.includes(e.key)&&(e.preventDefault(),this.click())}}
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;f("vaadin-button",ke,{moduleId:"vaadin-button-styles"});class Ce extends(De(M(x(k(D))))){static get is(){return"vaadin-button"}static get template(){return(e=>e`
  <div class="vaadin-button-container">
    <span part="prefix" aria-hidden="true">
      <slot name="prefix"></slot>
    </span>
    <span part="label">
      <slot></slot>
    </span>
    <span part="suffix" aria-hidden="true">
      <slot name="suffix"></slot>
    </span>
  </div>
  <slot name="tooltip"></slot>
`
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */)(C)}ready(){super.ready(),this._tooltipController=new A(this),this.addController(this._tooltipController)}}customElements.define(Ce.is,Ce),f("vaadin-date-picker-year",c`
    :host([current]) [part='year-number'] {
      color: var(--lumo-primary-text-color);
    }

    :host(:not([current])) [part='year-number'],
    [part='year-separator'] {
      opacity: var(--_lumo-date-picker-year-opacity, 0.7);
      transition: 0.2s opacity;
    }

    [part='year-number'],
    [part='year-separator'] {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 50%;
      transform: translateY(-50%);
    }

    [part='year-separator']::after {
      color: var(--lumo-disabled-text-color);
      content: '\\2022';
    }
  `,{moduleId:"lumo-date-picker-year"}),f("vaadin-date-picker-overlay-content",c`
    :host {
      position: relative;
      /* Background for the year scroller, placed here as we are using a mask image on the actual years part */
      background-image: linear-gradient(var(--lumo-shade-5pct), var(--lumo-shade-5pct));
      background-size: 57px 100%;
      background-position: top right;
      background-repeat: no-repeat;
      cursor: default;
    }

    ::slotted([slot='months']) {
      /* Month calendar height:
              header height + margin-bottom
            + weekdays height + margin-bottom
            + date cell heights
            + small margin between month calendars
        */
      /* prettier-ignore */
      --vaadin-infinite-scroller-item-height:
          calc(
              var(--lumo-font-size-l) + var(--lumo-space-m)
            + var(--lumo-font-size-xs) + var(--lumo-space-s)
            + var(--lumo-size-m) * 6
            + var(--lumo-space-s)
          );
      --vaadin-infinite-scroller-buffer-offset: 10%;
      -webkit-mask-image: linear-gradient(transparent, #000 10%, #000 85%, transparent);
      mask-image: linear-gradient(transparent, #000 10%, #000 85%, transparent);
      position: relative;
      margin-right: 57px;
    }

    ::slotted([slot='years']) {
      /* TODO get rid of fixed magic number */
      --vaadin-infinite-scroller-buffer-width: 97px;
      width: 57px;
      height: auto;
      top: 0;
      bottom: 0;
      font-size: var(--lumo-font-size-s);
      box-shadow: inset 2px 0 4px 0 var(--lumo-shade-5pct);
      -webkit-mask-image: linear-gradient(transparent, #000 35%, #000 65%, transparent);
      mask-image: linear-gradient(transparent, #000 35%, #000 65%, transparent);
      cursor: var(--lumo-clickable-cursor);
    }

    ::slotted([slot='years']:hover) {
      --_lumo-date-picker-year-opacity: 1;
    }

    /* TODO unsupported selector */
    #scrollers {
      position: static;
      display: block;
    }

    /* TODO fix this in vaadin-date-picker that it adapts to the width of the year scroller */
    :host([desktop]) ::slotted([slot='months']) {
      right: auto;
    }

    /* Year scroller position indicator */
    ::slotted([slot='years'])::before {
      border: none;
      width: 1em;
      height: 1em;
      background-color: var(--lumo-base-color);
      background-image: linear-gradient(var(--lumo-tint-5pct), var(--lumo-tint-5pct));
      transform: translate(-75%, -50%) rotate(45deg);
      border-top-right-radius: var(--lumo-border-radius-s);
      box-shadow: 2px -2px 6px 0 var(--lumo-shade-5pct);
      z-index: 1;
    }

    [part='toolbar'] {
      padding: var(--lumo-space-s);
      border-bottom-left-radius: var(--lumo-border-radius-l);
      margin-right: 57px;
    }

    [part='toolbar'] ::slotted(vaadin-button) {
      margin: 0;
    }

    /* Narrow viewport mode (fullscreen) */

    :host([fullscreen]) [part='toolbar'] {
      order: -1;
      background-color: var(--lumo-base-color);
    }

    :host([fullscreen]) [part='overlay-header'] {
      order: -2;
      height: var(--lumo-size-m);
      padding: var(--lumo-space-s);
      position: absolute;
      left: 0;
      right: 0;
      justify-content: center;
    }

    :host([fullscreen]) [part='toggle-button'],
    :host([fullscreen]) [part='clear-button'],
    [part='overlay-header'] [part='label'] {
      display: none;
    }

    /* Very narrow screen (year scroller initially hidden) */

    [part='years-toggle-button'] {
      display: flex;
      align-items: center;
      height: var(--lumo-size-s);
      padding: 0 0.5em;
      border-radius: var(--lumo-border-radius-m);
      z-index: 3;
      color: var(--lumo-primary-text-color);
      font-weight: 500;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }

    :host([years-visible]) [part='years-toggle-button'] {
      background-color: var(--lumo-primary-color);
      color: var(--lumo-primary-contrast-color);
    }

    /* TODO magic number (same as used for media-query in vaadin-date-picker-overlay-content) */
    @media screen and (max-width: 374px) {
      :host {
        background-image: none;
      }

      [part='toolbar'],
      ::slotted([slot='months']) {
        margin-right: 0;
      }

      /* TODO make date-picker adapt to the width of the years part */
      ::slotted([slot='years']) {
        --vaadin-infinite-scroller-buffer-width: 90px;
        width: 50px;
        background-color: var(--lumo-shade-5pct);
      }

      :host([years-visible]) ::slotted([slot='months']) {
        padding-left: 50px;
      }
    }
  `,{moduleId:"lumo-date-picker-overlay-content"}),f("vaadin-month-calendar",c`
    :host {
      -moz-user-select: none;
      -webkit-user-select: none;
      -webkit-tap-highlight-color: transparent;
      user-select: none;
      font-size: var(--lumo-font-size-m);
      color: var(--lumo-body-text-color);
      text-align: center;
      padding: 0 var(--lumo-space-xs);
    }

    /* Month header */

    [part='month-header'] {
      color: var(--lumo-header-text-color);
      font-size: var(--lumo-font-size-l);
      line-height: 1;
      font-weight: 500;
      margin-bottom: var(--lumo-space-m);
    }

    /* Week days and numbers */

    [part='weekdays'],
    [part='weekday'],
    [part='week-number'] {
      font-size: var(--lumo-font-size-xxs);
      line-height: 1;
      color: var(--lumo-secondary-text-color);
    }

    [part='weekdays'] {
      margin-bottom: var(--lumo-space-s);
    }

    [part='weekday']:empty,
    [part='week-number'] {
      width: var(--lumo-size-xs);
    }

    /* Date and week number cells */

    [part~='date'],
    [part='week-number'] {
      box-sizing: border-box;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      height: var(--lumo-size-m);
      position: relative;
    }

    [part~='date'] {
      transition: color 0.1s;
    }

    [part~='date']:not(:empty) {
      cursor: var(--lumo-clickable-cursor);
    }

    :host([week-numbers]) [part='weekday']:not(:empty),
    :host([week-numbers]) [part~='date'] {
      width: calc((100% - var(--lumo-size-xs)) / 7);
    }

    /* Today date */

    [part~='date'][part~='today'] {
      color: var(--lumo-primary-text-color);
    }

    /* Focused date */

    [part~='date']::before {
      content: '';
      position: absolute;
      z-index: -1;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      min-width: 2em;
      min-height: 2em;
      width: 80%;
      height: 80%;
      max-height: 100%;
      max-width: 100%;
      border-radius: var(--lumo-border-radius-m);
    }

    [part~='date'][part~='focused']::before {
      box-shadow: 0 0 0 1px var(--lumo-base-color), 0 0 0 3px var(--lumo-primary-color-50pct);
    }

    :host(:not([focused])) [part~='date'][part~='focused']::before {
      animation: vaadin-date-picker-month-calendar-focus-date 1.4s infinite;
    }

    @keyframes vaadin-date-picker-month-calendar-focus-date {
      50% {
        box-shadow: 0 0 0 1px var(--lumo-base-color), 0 0 0 3px transparent;
      }
    }

    [part~='date']:not(:empty):not([part~='disabled']):not([part~='selected']):hover::before {
      background-color: var(--lumo-primary-color-10pct);
    }

    [part~='date'][part~='selected'] {
      color: var(--lumo-primary-contrast-color);
    }

    [part~='date'][part~='selected']::before {
      background-color: var(--lumo-primary-color);
    }

    [part~='date'][part~='disabled'] {
      color: var(--lumo-disabled-text-color);
    }

    @media (pointer: coarse) {
      [part~='date']:hover:not([part~='selected'])::before,
      [part~='focused']:not([part~='selected'])::before {
        display: none;
      }

      [part~='date']:not(:empty):not([part~='disabled']):active::before {
        display: block;
      }

      [part~='date'][part~='selected']::before {
        box-shadow: none;
      }
    }

    /* Disabled */

    :host([disabled]) * {
      color: var(--lumo-disabled-text-color) !important;
    }
  `,{moduleId:"lumo-month-calendar"});const Se=document.createElement("template");Se.innerHTML="\n  <style>\n    @keyframes vaadin-date-picker-month-calendar-focus-date {\n      50% {\n        box-shadow: 0 0 0 2px transparent;\n      }\n    }\n  </style>\n",document.head.appendChild(Se.content);f("vaadin-date-picker",[le,c`
  :host {
    outline: none;
  }

  [part='toggle-button']::before {
    content: var(--lumo-icons-calendar);
  }

  [part='clear-button']::before {
    content: var(--lumo-icons-cross);
  }

  @media (max-width: 420px), (max-height: 420px) {
    [part='overlay-content'] {
      height: 70vh;
    }
  }

  :host([dir='rtl']) [part='input-field'] ::slotted(input) {
    --_lumo-text-field-overflow-mask-image: linear-gradient(to left, transparent, #000 1.25em);
  }

  :host([dir='rtl']) [part='input-field'] ::slotted(input:placeholder-shown) {
    --_lumo-text-field-overflow-mask-image: none;
  }
`],{moduleId:"lumo-date-picker"});
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const Ie={start:"top",end:"bottom"},Te={start:"left",end:"right"},Ee=new ResizeObserver((e=>{setTimeout((()=>{e.forEach((e=>{e.target.__overlay&&e.target.__overlay._updatePosition()}))}))})),Pe=e=>class extends e{static get properties(){return{positionTarget:{type:Object,value:null},horizontalAlign:{type:String,value:"start"},verticalAlign:{type:String,value:"top"},noHorizontalOverlap:{type:Boolean,value:!1},noVerticalOverlap:{type:Boolean,value:!1},requiredVerticalSpace:{type:Number,value:0}}}static get observers(){return["__positionSettingsChanged(horizontalAlign, verticalAlign, noHorizontalOverlap, noVerticalOverlap, requiredVerticalSpace)","__overlayOpenedChanged(opened, positionTarget)"]}constructor(){super(),this.__onScroll=this.__onScroll.bind(this),this._updatePosition=this._updatePosition.bind(this)}connectedCallback(){super.connectedCallback(),this.opened&&this.__addUpdatePositionEventListeners()}disconnectedCallback(){super.disconnectedCallback(),this.__removeUpdatePositionEventListeners()}__addUpdatePositionEventListeners(){window.addEventListener("resize",this._updatePosition),this.__positionTargetAncestorRootNodes=O(this.positionTarget),this.__positionTargetAncestorRootNodes.forEach((e=>{e.addEventListener("scroll",this.__onScroll,!0)}))}__removeUpdatePositionEventListeners(){window.removeEventListener("resize",this._updatePosition),this.__positionTargetAncestorRootNodes&&(this.__positionTargetAncestorRootNodes.forEach((e=>{e.removeEventListener("scroll",this.__onScroll,!0)})),this.__positionTargetAncestorRootNodes=null)}__overlayOpenedChanged(e,t){if(this.__removeUpdatePositionEventListeners(),t&&(t.__overlay=null,Ee.unobserve(t),e&&(this.__addUpdatePositionEventListeners(),t.__overlay=this,Ee.observe(t))),e){const e=getComputedStyle(this);this.__margins||(this.__margins={},["top","bottom","left","right"].forEach((t=>{this.__margins[t]=parseInt(e[t],10)}))),this.setAttribute("dir",e.direction),this._updatePosition(),requestAnimationFrame((()=>this._updatePosition()))}}__positionSettingsChanged(){this._updatePosition()}__onScroll(e){this.contains(e.target)||this._updatePosition()}_updatePosition(){if(!this.positionTarget||!this.opened)return;const e=this.positionTarget.getBoundingClientRect(),t=this.__shouldAlignStartVertically(e);this.style.justifyContent=t?"flex-start":"flex-end";const i=this.__isRTL,s=this.__shouldAlignStartHorizontally(e,i),o=!i&&s||i&&!s;this.style.alignItems=o?"flex-start":"flex-end";const n=this.getBoundingClientRect(),a=this.__calculatePositionInOneDimension(e,n,this.noVerticalOverlap,Ie,this,t),r=this.__calculatePositionInOneDimension(e,n,this.noHorizontalOverlap,Te,this,s);Object.assign(this.style,a,r),this.toggleAttribute("bottom-aligned",!t),this.toggleAttribute("top-aligned",t),this.toggleAttribute("end-aligned",!o),this.toggleAttribute("start-aligned",o)}__shouldAlignStartHorizontally(e,t){const i=Math.max(this.__oldContentWidth||0,this.$.overlay.offsetWidth);this.__oldContentWidth=this.$.overlay.offsetWidth;const s=Math.min(window.innerWidth,document.documentElement.clientWidth),o=!t&&"start"===this.horizontalAlign||t&&"end"===this.horizontalAlign;return this.__shouldAlignStart(e,i,s,this.__margins,o,this.noHorizontalOverlap,Te)}__shouldAlignStartVertically(e){const t=this.requiredVerticalSpace||Math.max(this.__oldContentHeight||0,this.$.overlay.offsetHeight);this.__oldContentHeight=this.$.overlay.offsetHeight;const i=Math.min(window.innerHeight,document.documentElement.clientHeight),s="top"===this.verticalAlign;return this.__shouldAlignStart(e,t,i,this.__margins,s,this.noVerticalOverlap,Ie)}__shouldAlignStart(e,t,i,s,o,n,a){const r=i-e[n?a.end:a.start]-s[a.end],l=e[n?a.start:a.end]-s[a.start],d=o?r:l;return o===(d>(o?l:r)||d>t)}__adjustBottomProperty(e,t,i){let s;if(e===t.end){if(t.end===Ie.end){const e=Math.min(window.innerHeight,document.documentElement.clientHeight);if(i>e&&this.__oldViewportHeight){s=i-(this.__oldViewportHeight-e)}this.__oldViewportHeight=e}if(t.end===Te.end){const e=Math.min(window.innerWidth,document.documentElement.clientWidth);if(i>e&&this.__oldViewportWidth){s=i-(this.__oldViewportWidth-e)}this.__oldViewportWidth=e}}return s}__calculatePositionInOneDimension(e,t,i,s,o,n){const a=n?s.start:s.end,r=n?s.end:s.start,l=parseFloat(o.style[a]||getComputedStyle(o)[a]),d=this.__adjustBottomProperty(a,s,l),c=t[n?s.start:s.end]-e[i===n?s.end:s.start];return{[a]:d?`${d}px`:`${l+c*(n?-1:1)}px`,[r]:""}}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;let $e;f("vaadin-date-picker-overlay",c`
    [part='overlay'] {
      display: flex;
      flex: auto;
    }

    [part~='content'] {
      flex: auto;
    }
  `,{moduleId:"vaadin-date-picker-overlay-styles"});class Me extends(Pe(be)){static get is(){return"vaadin-date-picker-overlay"}static get template(){return $e||($e=super.template.cloneNode(!0),$e.content.querySelector('[part~="overlay"]').removeAttribute("tabindex")),$e}}
/**
@license
Copyright (c) 2017 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at http://polymer.github.io/LICENSE.txt
The complete set of authors may be found at http://polymer.github.io/AUTHORS.txt
The complete set of contributors may be found at http://polymer.github.io/CONTRIBUTORS.txt
Code distributed by Google as part of the polymer project is also
subject to an additional IP rights grant found at http://polymer.github.io/PATENTS.txt
*/
function Ae(e,t,i,s,o){let n;o&&(n="object"==typeof i&&null!==i,n&&(s=e.__dataTemp[t]));let a=s!==i&&(s==s||i==i);return n&&a&&(e.__dataTemp[t]=i),a}customElements.define(Me.is,Me);const Oe=z((e=>class extends e{_shouldPropertyChange(e,t,i){return Ae(this,e,t,i,!0)}})),ze=z((e=>class extends e{static get properties(){return{mutableData:Boolean}}_shouldPropertyChange(e,t,i){return Ae(this,e,t,i,this.mutableData)}}));Oe._mutablePropertyChange=Ae;
/**
@license
Copyright (c) 2017 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at http://polymer.github.io/LICENSE.txt
The complete set of authors may be found at http://polymer.github.io/AUTHORS.txt
The complete set of contributors may be found at http://polymer.github.io/CONTRIBUTORS.txt
Code distributed by Google as part of the polymer project is also
subject to an additional IP rights grant found at http://polymer.github.io/PATENTS.txt
*/
let Re=null;function Be(){return Re}Be.prototype=Object.create(HTMLTemplateElement.prototype,{constructor:{value:Be,writable:!0}});const Fe=R(Be),Ve=Oe(Fe);const Le=R(class{});class Ne extends Le{constructor(e){super(),this._configureProperties(e),this.root=this._stampTemplate(this.__dataHost);let t=[];this.children=t;for(let e=this.root.firstChild;e;e=e.nextSibling)t.push(e),e.__templatizeInstance=this;this.__templatizeOwner&&this.__templatizeOwner.__hideTemplateChildren__&&this._showHideChildren(!0);let i=this.__templatizeOptions;(e&&i.instanceProps||!i.instanceProps)&&this._enableProperties()}_configureProperties(e){if(this.__templatizeOptions.forwardHostProp)for(let e in this.__hostProps)this._setPendingProperty(e,this.__dataHost["_host_"+e]);for(let t in e)this._setPendingProperty(t,e[t])}forwardHostProp(e,t){this._setPendingPropertyOrPath(e,t,!1,!0)&&this.__dataHost._enqueueClient(this)}_addEventListenerToNode(e,t,i){if(this._methodHost&&this.__templatizeOptions.parentModel)this._methodHost._addEventListenerToNode(e,t,(e=>{e.model=this,i(e)}));else{let s=this.__dataHost.__dataHost;s&&s._addEventListenerToNode(e,t,i)}}_showHideChildren(e){!function(e,t){for(let i=0;i<t.length;i++){let s=t[i];if(Boolean(e)!=Boolean(s.__hideTemplateChildren__))if(s.nodeType===Node.TEXT_NODE)e?(s.__polymerTextContent__=s.textContent,s.textContent=""):s.textContent=s.__polymerTextContent__;else if("slot"===s.localName)if(e)s.__polymerReplaced__=document.createComment("hidden-slot"),B(B(s).parentNode).replaceChild(s.__polymerReplaced__,s);else{const e=s.__polymerReplaced__;e&&B(B(e).parentNode).replaceChild(s,e)}else s.style&&(e?(s.__polymerDisplay__=s.style.display,s.style.display="none"):s.style.display=s.__polymerDisplay__);s.__hideTemplateChildren__=e,s._showHideChildren&&s._showHideChildren(e)}}(e,this.children)}_setUnmanagedPropertyToNode(e,t,i){e.__hideTemplateChildren__&&e.nodeType==Node.TEXT_NODE&&"textContent"==t?e.__polymerTextContent__=i:super._setUnmanagedPropertyToNode(e,t,i)}get parentModel(){let e=this.__parentModel;if(!e){let t;e=this;do{e=e.__dataHost.__dataHost}while((t=e.__templatizeOptions)&&!t.parentModel);this.__parentModel=e}return e}dispatchEvent(e){return!0}}Ne.prototype.__dataHost,Ne.prototype.__templatizeOptions,Ne.prototype._methodHost,Ne.prototype.__templatizeOwner,Ne.prototype.__hostProps;const qe=Oe(Ne);function je(e){let t=e.__dataHost;return t&&t._methodHost||t}function He(e,t,i){let s=i.mutableData?qe:Ne;Ye.mixin&&(s=Ye.mixin(s));let o=class extends s{};return o.prototype.__templatizeOptions=i,o.prototype._bindTemplate(e),function(e,t,i,s){let o=i.hostProps||{};for(let t in s.instanceProps){delete o[t];let i=s.notifyInstanceProp;i&&e.prototype._addPropertyEffect(t,e.prototype.PROPERTY_EFFECT_TYPES.NOTIFY,{fn:Ue(t,i)})}if(s.forwardHostProp&&t.__dataHost)for(let t in o)i.hasHostProps||(i.hasHostProps=!0),e.prototype._addPropertyEffect(t,e.prototype.PROPERTY_EFFECT_TYPES.NOTIFY,{fn:function(e,t,i){e.__dataHost._setPendingPropertyOrPath("_host_"+t,i[t],!0,!0)}})}(o,e,t,i),o}function Ge(e,t,i,s){let o=i.forwardHostProp;if(o&&t.hasHostProps){const n="template"==e.localName;let a=t.templatizeTemplateClass;if(!a){if(n){let e=i.mutableData?Ve:Fe;class s extends e{}a=t.templatizeTemplateClass=s}else{const i=e.constructor;class s extends i{}a=t.templatizeTemplateClass=s}let r=t.hostProps;for(let e in r)a.prototype._addPropertyEffect("_host_"+e,a.prototype.PROPERTY_EFFECT_TYPES.PROPAGATE,{fn:We(e,o)}),a.prototype._createNotifyingProperty("_host_"+e);V&&s&&function(e,t,i){const s=i.constructor._properties,{propertyEffects:o}=e,{instanceProps:n}=t;for(let e in o)if(!(s[e]||n&&n[e])){const t=o[e];for(let i=0;i<t.length;i++){const{part:s}=t[i].info;if(!s.signature||!s.signature.static){console.warn(`Property '${e}' used in template but not declared in 'properties'; attribute will not be observed.`);break}}}}(t,i,s)}if(e.__dataProto&&Object.assign(e.__data,e.__dataProto),n)!function(e,t){Re=e,Object.setPrototypeOf(e,t.prototype),new t,Re=null}(e,a),e.__dataTemp={},e.__dataPending=null,e.__dataOld=null,e._enableProperties();else{Object.setPrototypeOf(e,a.prototype);const i=t.hostProps;for(let t in i)if(t="_host_"+t,t in e){const i=e[t];delete e[t],e.__data[t]=i}}}}function We(e,t){return function(e,i,s){t.call(e.__templatizeOwner,i.substring("_host_".length),s[i])}}function Ue(e,t){return function(e,i,s){t.call(e.__templatizeOwner,e,i,s[i])}}function Ye(e,t,i){if(F&&!je(e))throw new Error("strictTemplatePolicy: template owner not trusted");if(i=i||{},e.__templatizeOwner)throw new Error("A <template> can only be templatized once");e.__templatizeOwner=t;let s=(t?t.constructor:Ne)._parseTemplate(e),o=s.templatizeInstanceClass;o||(o=He(e,s,i),s.templatizeInstanceClass=o);const n=je(e);Ge(e,s,i,n);let a=class extends o{};return a.prototype._methodHost=n,a.prototype.__dataHost=e,a.prototype.__templatizeOwner=t,a.prototype.__hostProps=s.hostProps,a}
/**
@license
Copyright (c) 2017 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at http://polymer.github.io/LICENSE.txt
The complete set of authors may be found at http://polymer.github.io/AUTHORS.txt
The complete set of contributors may be found at http://polymer.github.io/CONTRIBUTORS.txt
Code distributed by Google as part of the polymer project is also
subject to an additional IP rights grant found at http://polymer.github.io/PATENTS.txt
*/
class Ke{constructor(){this._asyncModule=null,this._callback=null,this._timer=null}setConfig(e,t){this._asyncModule=e,this._callback=t,this._timer=this._asyncModule.run((()=>{this._timer=null,Xe.delete(this),this._callback()}))}cancel(){this.isActive()&&(this._cancelAsync(),Xe.delete(this))}_cancelAsync(){this.isActive()&&(this._asyncModule.cancel(this._timer),this._timer=null)}flush(){this.isActive()&&(this.cancel(),this._callback())}isActive(){return null!=this._timer}static debounce(e,t,i){return e instanceof Ke?e._cancelAsync():e=new Ke,e.setConfig(t,i),e}}let Xe=new Set;const Qe=function(){const e=Boolean(Xe.size);return Xe.forEach((e=>{try{e.flush()}catch(e){setTimeout((()=>{throw e}))}})),e},Je=function(){let e,t;do{e=window.ShadyDOM&&ShadyDOM.flush(),window.ShadyCSS&&window.ShadyCSS.ScopingShim&&window.ShadyCSS.ScopingShim.flush(),t=Qe()}while(e||t)};
/**
@license
Copyright (c) 2017 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at http://polymer.github.io/LICENSE.txt
The complete set of authors may be found at http://polymer.github.io/AUTHORS.txt
The complete set of contributors may be found at http://polymer.github.io/CONTRIBUTORS.txt
Code distributed by Google as part of the polymer project is also
subject to an additional IP rights grant found at http://polymer.github.io/PATENTS.txt
*/
let Ze=!1;
/**
@license
Copyright (c) 2017 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at http://polymer.github.io/LICENSE.txt
The complete set of authors may be found at http://polymer.github.io/AUTHORS.txt
The complete set of contributors may be found at http://polymer.github.io/CONTRIBUTORS.txt
Code distributed by Google as part of the polymer project is also
subject to an additional IP rights grant found at http://polymer.github.io/PATENTS.txt
*/
const et=ze(D);class tt extends et{static get is(){return"dom-repeat"}static get template(){return null}static get properties(){return{items:{type:Array},as:{type:String,value:"item"},indexAs:{type:String,value:"index"},itemsIndexAs:{type:String,value:"itemsIndex"},sort:{type:Function,observer:"__sortChanged"},filter:{type:Function,observer:"__filterChanged"},observe:{type:String,observer:"__observeChanged"},delay:Number,renderedItemCount:{type:Number,notify:!q,readOnly:!0},initialCount:{type:Number},targetFramerate:{type:Number,value:20},_targetFrameTime:{type:Number,computed:"__computeFrameTime(targetFramerate)"},notifyDomChange:{type:Boolean},reuseChunkedInstances:{type:Boolean}}}static get observers(){return["__itemsChanged(items.*)"]}constructor(){super(),this.__instances=[],this.__renderDebouncer=null,this.__itemsIdxToInstIdx={},this.__chunkCount=null,this.__renderStartTime=null,this.__itemsArrayChanged=!1,this.__shouldMeasureChunk=!1,this.__shouldContinueChunking=!1,this.__chunkingId=0,this.__sortFn=null,this.__filterFn=null,this.__observePaths=null,this.__ctor=null,this.__isDetached=!0,this.template=null,this._templateInfo}disconnectedCallback(){super.disconnectedCallback(),this.__isDetached=!0;for(let e=0;e<this.__instances.length;e++)this.__detachInstance(e);this.__chunkingId&&cancelAnimationFrame(this.__chunkingId)}connectedCallback(){if(super.connectedCallback(),function(){if(L&&!N){if(!Ze){Ze=!0;const e=document.createElement("style");e.textContent="dom-bind,dom-if,dom-repeat{display:none;}",document.head.appendChild(e)}return!0}return!1}()||(this.style.display="none"),this.__isDetached){this.__isDetached=!1;let e=B(B(this).parentNode);for(let t=0;t<this.__instances.length;t++)this.__attachInstance(t,e);this.__chunkingId&&this.__render()}}__ensureTemplatized(){if(!this.__ctor){const e=this;let t=this.template=e._templateInfo?e:this.querySelector("template");if(!t){let e=new MutationObserver((()=>{if(!this.querySelector("template"))throw new Error("dom-repeat requires a <template> child");e.disconnect(),this.__render()}));return e.observe(this,{childList:!0}),!1}let i={};i[this.as]=!0,i[this.indexAs]=!0,i[this.itemsIndexAs]=!0,this.__ctor=Ye(t,this,{mutableData:this.mutableData,parentModel:!0,instanceProps:i,forwardHostProp:function(e,t){let i=this.__instances;for(let s,o=0;o<i.length&&(s=i[o]);o++)s.forwardHostProp(e,t)},notifyInstanceProp:function(e,t,i){if(j(this.as,t)){let s=e[this.itemsIndexAs];t==this.as&&(this.items[s]=i);let o=H(this.as,`${JSCompiler_renameProperty("items",this)}.${s}`,t);this.notifyPath(o,i)}}})}return!0}__getMethodHost(){return this.__dataHost._methodHost||this.__dataHost}__functionFromPropertyValue(e){if("string"==typeof e){let t=e,i=this.__getMethodHost();return function(){return i[t].apply(i,arguments)}}return e}__sortChanged(e){this.__sortFn=this.__functionFromPropertyValue(e),this.items&&this.__debounceRender(this.__render)}__filterChanged(e){this.__filterFn=this.__functionFromPropertyValue(e),this.items&&this.__debounceRender(this.__render)}__computeFrameTime(e){return Math.ceil(1e3/e)}__observeChanged(){this.__observePaths=this.observe&&this.observe.replace(".*",".").split(" ")}__handleObservedPaths(e){if(this.__sortFn||this.__filterFn)if(e){if(this.__observePaths){let t=this.__observePaths;for(let i=0;i<t.length;i++)0===e.indexOf(t[i])&&this.__debounceRender(this.__render,this.delay)}}else this.__debounceRender(this.__render,this.delay)}__itemsChanged(e){this.items&&!Array.isArray(this.items)&&console.warn("dom-repeat expected array for `items`, found",this.items),this.__handleItemPath(e.path,e.value)||("items"===e.path&&(this.__itemsArrayChanged=!0),this.__debounceRender(this.__render))}__debounceRender(e,t=0){var i;this.__renderDebouncer=Ke.debounce(this.__renderDebouncer,t>0?G.after(t):W,e.bind(this)),i=this.__renderDebouncer,Xe.add(i)}render(){this.__debounceRender(this.__render),Je()}__render(){if(!this.__ensureTemplatized())return;let e=this.items||[];const t=this.__sortAndFilterItems(e),i=this.__calculateLimit(t.length);this.__updateInstances(e,i,t),this.initialCount&&(this.__shouldMeasureChunk||this.__shouldContinueChunking)&&(cancelAnimationFrame(this.__chunkingId),this.__chunkingId=requestAnimationFrame((()=>{this.__chunkingId=null,this.__continueChunking()}))),this._setRenderedItemCount(this.__instances.length),q&&!this.notifyDomChange||this.dispatchEvent(new CustomEvent("dom-change",{bubbles:!0,composed:!0}))}__sortAndFilterItems(e){let t=new Array(e.length);for(let i=0;i<e.length;i++)t[i]=i;return this.__filterFn&&(t=t.filter(((t,i,s)=>this.__filterFn(e[t],i,s)))),this.__sortFn&&t.sort(((t,i)=>this.__sortFn(e[t],e[i]))),t}__calculateLimit(e){let t=e;const i=this.__instances.length;if(this.initialCount){let s;!this.__chunkCount||this.__itemsArrayChanged&&!this.reuseChunkedInstances?(t=Math.min(e,this.initialCount),s=Math.max(t-i,0),this.__chunkCount=s||1):(s=Math.min(Math.max(e-i,0),this.__chunkCount),t=Math.min(i+s,e)),this.__shouldMeasureChunk=s===this.__chunkCount,this.__shouldContinueChunking=t<e,this.__renderStartTime=performance.now()}return this.__itemsArrayChanged=!1,t}__continueChunking(){if(this.__shouldMeasureChunk){const e=performance.now()-this.__renderStartTime,t=this._targetFrameTime/e;this.__chunkCount=Math.round(this.__chunkCount*t)||1}this.__shouldContinueChunking&&this.__debounceRender(this.__render)}__updateInstances(e,t,i){const s=this.__itemsIdxToInstIdx={};let o;for(o=0;o<t;o++){let t=this.__instances[o],n=i[o],a=e[n];s[n]=o,t?(t._setPendingProperty(this.as,a),t._setPendingProperty(this.indexAs,o),t._setPendingProperty(this.itemsIndexAs,n),t._flushProperties()):this.__insertInstance(a,o,n)}for(let e=this.__instances.length-1;e>=o;e--)this.__detachAndRemoveInstance(e)}__detachInstance(e){let t=this.__instances[e];const i=B(t.root);for(let e=0;e<t.children.length;e++){let s=t.children[e];i.appendChild(s)}return t}__attachInstance(e,t){let i=this.__instances[e];t.insertBefore(i.root,this)}__detachAndRemoveInstance(e){this.__detachInstance(e),this.__instances.splice(e,1)}__stampInstance(e,t,i){let s={};return s[this.as]=e,s[this.indexAs]=t,s[this.itemsIndexAs]=i,new this.__ctor(s)}__insertInstance(e,t,i){const s=this.__stampInstance(e,t,i);let o=this.__instances[t+1],n=o?o.children[0]:this;return B(B(this).parentNode).insertBefore(s.root,n),this.__instances[t]=s,s}_showHideChildren(e){for(let t=0;t<this.__instances.length;t++)this.__instances[t]._showHideChildren(e)}__handleItemPath(e,t){let i=e.slice(6),s=i.indexOf("."),o=s<0?i:i.substring(0,s);if(o==parseInt(o,10)){let e=s<0?"":i.substring(s+1);this.__handleObservedPaths(e);let n=this.__itemsIdxToInstIdx[o],a=this.__instances[n];if(a){let i=this.as+(e?"."+e:"");a._setPendingPropertyOrPath(i,t,!1,!0),a._flushProperties()}return!0}}itemForElement(e){let t=this.modelForElement(e);return t&&t[this.as]}indexForElement(e){let t=this.modelForElement(e);return t&&t[this.indexAs]}modelForElement(e){return function(e,t){let i;for(;t;)if(i=t.__dataHost?t:t.__templatizeInstance){if(i.__dataHost==e)return i;t=i.__dataHost}else t=B(t).parentNode;return null}(this.template,e)}}function it(e,t){return e instanceof Date&&t instanceof Date&&e.getFullYear()===t.getFullYear()&&e.getMonth()===t.getMonth()&&e.getDate()===t.getDate()}function st(e,t,i){return(!t||e>=t)&&(!i||e<=i)}function ot(e,t){return t.filter((e=>void 0!==e)).reduce(((t,i)=>{if(!i)return t;if(!t)return i;return Math.abs(e.getTime()-i.getTime())<Math.abs(t.getTime()-e.getTime())?i:t}))}function nt(e){return{day:e.getDate(),month:e.getMonth(),year:e.getFullYear()}}function at(e){const t=new Date,i=new Date(t);return i.setDate(1),i.setMonth(parseInt(e)+t.getMonth()),i}function rt(e){const t=/^([-+]\d{1}|\d{2,4}|[-+]\d{6})-(\d{1,2})-(\d{1,2})$/u.exec(e);if(!t)return;const i=new Date(0,0);return i.setFullYear(parseInt(t[1],10)),i.setMonth(parseInt(t[2],10)-1),i.setDate(parseInt(t[3],10)),i}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */customElements.define(tt.is,tt);class lt extends($(x(D))){static get template(){return C`
      <style>
        :host {
          display: block;
        }

        #monthGrid {
          width: 100%;
          border-collapse: collapse;
        }

        #days-container tr,
        #weekdays-container tr {
          display: flex;
        }

        [part~='date'] {
          outline: none;
        }

        [part~='disabled'] {
          pointer-events: none;
        }

        [part='week-number'][hidden],
        [part='weekday'][hidden] {
          display: none;
        }

        [part='weekday'],
        [part~='date'] {
          width: calc(100% / 7);
          padding: 0;
          font-weight: normal;
        }

        [part='weekday']:empty,
        [part='week-number'] {
          width: 12.5%;
          flex-shrink: 0;
          padding: 0;
        }

        :host([week-numbers]) [part='weekday']:not(:empty),
        :host([week-numbers]) [part~='date'] {
          width: 12.5%;
        }
      </style>

      <div part="month-header" id="month-header" aria-hidden="true">[[_getTitle(month, i18n.monthNames)]]</div>
      <table
        id="monthGrid"
        role="grid"
        aria-labelledby="month-header"
        on-touchend="_preventDefault"
        on-touchstart="_onMonthGridTouchStart"
      >
        <thead id="weekdays-container">
          <tr role="row" part="weekdays">
            <th
              part="weekday"
              aria-hidden="true"
              hidden$="[[!_showWeekSeparator(showWeekNumbers, i18n.firstDayOfWeek)]]"
            ></th>
            <template
              is="dom-repeat"
              items="[[_getWeekDayNames(i18n.weekdays, i18n.weekdaysShort, showWeekNumbers, i18n.firstDayOfWeek)]]"
            >
              <th role="columnheader" part="weekday" scope="col" abbr$="[[item.weekDay]]" aria-hidden="true">
                [[item.weekDayShort]]
              </th>
            </template>
          </tr>
        </thead>
        <tbody id="days-container">
          <template is="dom-repeat" items="[[_weeks]]" as="week">
            <tr role="row">
              <td
                part="week-number"
                aria-hidden="true"
                hidden$="[[!_showWeekSeparator(showWeekNumbers, i18n.firstDayOfWeek)]]"
              >
                [[__getWeekNumber(week)]]
              </td>
              <template is="dom-repeat" items="[[week]]">
                <td
                  role="gridcell"
                  part$="[[__getDatePart(item, focusedDate, selectedDate, minDate, maxDate)]]"
                  date="[[item]]"
                  tabindex$="[[__getDayTabindex(item, focusedDate)]]"
                  disabled$="[[__isDayDisabled(item, minDate, maxDate)]]"
                  aria-selected$="[[__getDayAriaSelected(item, selectedDate)]]"
                  aria-disabled$="[[__getDayAriaDisabled(item, minDate, maxDate)]]"
                  aria-label$="[[__getDayAriaLabel(item)]]"
                  >[[_getDate(item)]]</td
                >
              </template>
            </tr>
          </template>
        </tbody>
      </table>
    `}static get is(){return"vaadin-month-calendar"}static get properties(){return{month:{type:Date,value:new Date},selectedDate:{type:Date,notify:!0},focusedDate:Date,showWeekNumbers:{type:Boolean,value:!1},i18n:{type:Object},ignoreTaps:Boolean,_notTapping:Boolean,minDate:{type:Date,value:null},maxDate:{type:Date,value:null},_days:{type:Array,computed:"_getDays(month, i18n.firstDayOfWeek, minDate, maxDate)"},_weeks:{type:Array,computed:"_getWeeks(_days)"},disabled:{type:Boolean,reflectToAttribute:!0,computed:"_isDisabled(month, minDate, maxDate)"}}}static get observers(){return["_showWeekNumbersChanged(showWeekNumbers, i18n.firstDayOfWeek)","__focusedDateChanged(focusedDate, _days)"]}get focusableDateElement(){return[...this.shadowRoot.querySelectorAll("[part~=date]")].find((e=>it(e.date,this.focusedDate)))}ready(){super.ready(),U(this.$.monthGrid,"tap",this._handleTap.bind(this))}_isDisabled(e,t,i){const s=new Date(0,0);s.setFullYear(e.getFullYear()),s.setMonth(e.getMonth()),s.setDate(1);const o=new Date(0,0);return o.setFullYear(e.getFullYear()),o.setMonth(e.getMonth()+1),o.setDate(0),!(t&&i&&t.getMonth()===i.getMonth()&&t.getMonth()===e.getMonth()&&i.getDate()-t.getDate()>=0)&&(!st(s,t,i)&&!st(o,t,i))}_getTitle(e,t){if(void 0!==e&&void 0!==t)return this.i18n.formatTitle(t[e.getMonth()],e.getFullYear())}_onMonthGridTouchStart(){this._notTapping=!1,setTimeout((()=>{this._notTapping=!0}),300)}_dateAdd(e,t){e.setDate(e.getDate()+t)}_applyFirstDayOfWeek(e,t){if(void 0!==e&&void 0!==t)return e.slice(t).concat(e.slice(0,t))}_getWeekDayNames(e,t,i,s){if(void 0!==e&&void 0!==t&&void 0!==i&&void 0!==s)return e=this._applyFirstDayOfWeek(e,s),t=this._applyFirstDayOfWeek(t,s),e=e.map(((e,i)=>({weekDay:e,weekDayShort:t[i]})))}__focusedDateChanged(e,t){t.some((t=>it(t,e)))?this.removeAttribute("aria-hidden"):this.setAttribute("aria-hidden","true")}_getDate(e){return e?e.getDate():""}_showWeekNumbersChanged(e,t){e&&1===t?this.setAttribute("week-numbers",""):this.removeAttribute("week-numbers")}_showWeekSeparator(e,t){return e&&1===t}_isToday(e){return it(new Date,e)}_getDays(e,t){if(void 0===e||void 0===t)return;const i=new Date(0,0);for(i.setFullYear(e.getFullYear()),i.setMonth(e.getMonth()),i.setDate(1);i.getDay()!==t;)this._dateAdd(i,-1);const s=[],o=i.getMonth(),n=e.getMonth();for(;i.getMonth()===n||i.getMonth()===o;)s.push(i.getMonth()===n?new Date(i.getTime()):null),this._dateAdd(i,1);return s}_getWeeks(e){return e.reduce(((e,t,i)=>(i%7==0&&e.push([]),e[e.length-1].push(t),e)),[])}_handleTap(e){this.ignoreTaps||this._notTapping||!e.target.date||e.target.hasAttribute("disabled")||(this.selectedDate=e.target.date,this.dispatchEvent(new CustomEvent("date-tap",{detail:{date:e.target.date},bubbles:!0,composed:!0})))}_preventDefault(e){e.preventDefault()}__getDatePart(e,t,i,s,o){const n=["date"];return this.__isDayDisabled(e,s,o)&&n.push("disabled"),this.__isDayFocused(e,t)&&n.push("focused"),this.__isDaySelected(e,i)&&n.push("selected"),this._isToday(e)&&n.push("today"),n.join(" ")}__getWeekNumber(e){
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
return function(e){let t=e.getDay();0===t&&(t=7);const i=4-t,s=new Date(e.getTime()+24*i*3600*1e3),o=new Date(0,0);o.setFullYear(s.getFullYear());const n=s.getTime()-o.getTime(),a=Math.round(n/864e5);return Math.floor(a/7+1)}(e.reduce(((e,t)=>!e&&t?t:e)))}__isDayFocused(e,t){return it(e,t)}__isDaySelected(e,t){return it(e,t)}__getDayAriaSelected(e,t){if(this.__isDaySelected(e,t))return"true"}__isDayDisabled(e,t,i){return!st(e,t,i)}__getDayAriaDisabled(e,t,i){if(void 0!==e&&void 0!==t&&void 0!==i)return this.__isDayDisabled(e,t,i)?"true":void 0}__getDayAriaLabel(e){if(!e)return"";let t=`${this._getDate(e)} ${this.i18n.monthNames[e.getMonth()]} ${e.getFullYear()}, ${this.i18n.weekdays[e.getDay()]}`;return this._isToday(e)&&(t+=`, ${this.i18n.today}`),t}__getDayTabindex(e,t){return this.__isDayFocused(e,t)?"0":"-1"}}customElements.define(lt.is,lt);
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
class dt extends D{static get template(){return C`
      <style>
        :host {
          display: block;
          overflow: hidden;
          height: 500px;
        }

        #scroller {
          position: relative;
          height: 100%;
          overflow: auto;
          outline: none;
          margin-right: -40px;
          -webkit-overflow-scrolling: touch;
          overflow-x: hidden;
        }

        #scroller.notouchscroll {
          -webkit-overflow-scrolling: auto;
        }

        #scroller::-webkit-scrollbar {
          display: none;
        }

        .buffer {
          position: absolute;
          width: var(--vaadin-infinite-scroller-buffer-width, 100%);
          box-sizing: border-box;
          padding-right: 40px;
          top: var(--vaadin-infinite-scroller-buffer-offset, 0);
          animation: fadein 0.2s;
        }

        @keyframes fadein {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
      </style>

      <div id="scroller" on-scroll="_scroll">
        <div class="buffer"></div>
        <div class="buffer"></div>
        <div id="fullHeight"></div>
      </div>
    `}static get properties(){return{bufferSize:{type:Number,value:20},_initialScroll:{value:5e5},_initialIndex:{value:0},_buffers:Array,_preventScrollEvent:Boolean,_mayHaveMomentum:Boolean,_initialized:Boolean,active:{type:Boolean,observer:"_activated"}}}get bufferOffset(){return this._buffers[0].offsetTop}get itemHeight(){if(!this._itemHeightVal){const e=getComputedStyle(this).getPropertyValue("--vaadin-infinite-scroller-item-height"),t="background-position";this.$.fullHeight.style.setProperty(t,e);const i=getComputedStyle(this.$.fullHeight).getPropertyValue(t);this.$.fullHeight.style.removeProperty(t),this._itemHeightVal=parseFloat(i)}return this._itemHeightVal}get _bufferHeight(){return this.itemHeight*this.bufferSize}get position(){return(this.$.scroller.scrollTop-this._buffers[0].translateY)/this.itemHeight+this._firstIndex}set position(e){this._preventScrollEvent=!0,e>this._firstIndex&&e<this._firstIndex+2*this.bufferSize?this.$.scroller.scrollTop=this.itemHeight*(e-this._firstIndex)+this._buffers[0].translateY:(this._initialIndex=~~e,this._reset(),this._scrollDisabled=!0,this.$.scroller.scrollTop+=e%1*this.itemHeight,this._scrollDisabled=!1),this._mayHaveMomentum&&(this.$.scroller.classList.add("notouchscroll"),this._mayHaveMomentum=!1,setTimeout((()=>{this.$.scroller.classList.remove("notouchscroll")}),10))}ready(){super.ready(),this._buffers=[...this.shadowRoot.querySelectorAll(".buffer")],this.$.fullHeight.style.height=2*this._initialScroll+"px",Y&&(this.$.scroller.tabIndex=-1)}forceUpdate(){this._debouncerUpdateClones&&(this._buffers[0].updated=this._buffers[1].updated=!1,this._updateClones(),this._debouncerUpdateClones.cancel())}_createElement(){}_updateElement(e,t){}_activated(e){e&&!this._initialized&&(this._createPool(),this._initialized=!0)}_finishInit(){this._initDone||(this._buffers.forEach((e=>{[...e.children].forEach((e=>{this._ensureStampedInstance(e._itemWrapper)}))})),this._buffers[0].translateY||this._reset(),this._initDone=!0,this.dispatchEvent(new CustomEvent("init-done")))}_translateBuffer(e){const t=e?1:0;this._buffers[t].translateY=this._buffers[t?0:1].translateY+this._bufferHeight*(t?-1:1),this._buffers[t].style.transform=`translate3d(0, ${this._buffers[t].translateY}px, 0)`,this._buffers[t].updated=!1,this._buffers.reverse()}_scroll(){if(this._scrollDisabled)return;const e=this.$.scroller.scrollTop;(e<this._bufferHeight||e>2*this._initialScroll-this._bufferHeight)&&(this._initialIndex=~~this.position,this._reset());const t=this.itemHeight+this.bufferOffset,i=e>this._buffers[1].translateY+t,s=e<this._buffers[0].translateY+t;(i||s)&&(this._translateBuffer(s),this._updateClones()),this._preventScrollEvent||(this.dispatchEvent(new CustomEvent("custom-scroll",{bubbles:!1,composed:!0})),this._mayHaveMomentum=!0),this._preventScrollEvent=!1,this._debouncerScrollFinish=K.debounce(this._debouncerScrollFinish,X.after(200),(()=>{const e=this.$.scroller.getBoundingClientRect();this._isVisible(this._buffers[0],e)||this._isVisible(this._buffers[1],e)||(this.position=this.position)}))}_reset(){this._scrollDisabled=!0,this.$.scroller.scrollTop=this._initialScroll,this._buffers[0].translateY=this._initialScroll-this._bufferHeight,this._buffers[1].translateY=this._initialScroll,this._buffers.forEach((e=>{e.style.transform=`translate3d(0, ${e.translateY}px, 0)`})),this._buffers[0].updated=this._buffers[1].updated=!1,this._updateClones(!0),this._debouncerUpdateClones=K.debounce(this._debouncerUpdateClones,X.after(200),(()=>{this._buffers[0].updated=this._buffers[1].updated=!1,this._updateClones()})),this._scrollDisabled=!1}_createPool(){const e=this.getBoundingClientRect();this._buffers.forEach((t=>{for(let i=0;i<this.bufferSize;i++){const i=document.createElement("div");i.style.height=`${this.itemHeight}px`,i.instance={};const s=`vaadin-infinite-scroller-item-content-${Q()}`,o=document.createElement("slot");o.setAttribute("name",s),o._itemWrapper=i,t.appendChild(o),i.setAttribute("slot",s),this.appendChild(i),this._isVisible(i,e)&&this._ensureStampedInstance(i)}})),T(this,(()=>{this._finishInit()}))}_ensureStampedInstance(e){if(e.firstElementChild)return;const t=e.instance;e.instance=this._createElement(),e.appendChild(e.instance),Object.keys(t).forEach((i=>{e.instance.set(i,t[i])}))}_updateClones(e){this._firstIndex=~~((this._buffers[0].translateY-this._initialScroll)/this.itemHeight)+this._initialIndex;const t=e?this.$.scroller.getBoundingClientRect():void 0;this._buffers.forEach(((i,s)=>{if(!i.updated){const o=this._firstIndex+this.bufferSize*s;[...i.children].forEach(((i,s)=>{const n=i._itemWrapper;e&&!this._isVisible(n,t)||this._updateElement(n.instance,o+s)})),i.updated=!0}}))}_isVisible(e,t){const i=e.getBoundingClientRect();return i.bottom>t.top&&i.top<t.bottom}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */const ct=C`
  <style>
    :host {
      --vaadin-infinite-scroller-item-height: 270px;
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      height: 100%;
    }
  </style>
`;let ht;class ut extends dt{static get is(){return"vaadin-date-picker-month-scroller"}static get template(){return ht||(ht=super.template.cloneNode(!0),ht.content.appendChild(ct.content.cloneNode(!0))),ht}static get properties(){return{bufferSize:{type:Number,value:3}}}_createElement(){return document.createElement("vaadin-month-calendar")}_updateElement(e,t){e.month=at(t)}}customElements.define(ut.is,ut);
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const pt=C`
  <style>
    :host {
      --vaadin-infinite-scroller-item-height: 80px;
      width: 50px;
      display: block;
      height: 100%;
      position: absolute;
      right: 0;
      transform: translateX(100%);
      -webkit-tap-highlight-color: transparent;
      -webkit-user-select: none;
      -moz-user-select: none;
      user-select: none;
      /* Center the year scroller position. */
      --vaadin-infinite-scroller-buffer-offset: 50%;
    }

    :host::before {
      content: '';
      display: block;
      background: transparent;
      width: 0;
      height: 0;
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      border-width: 6px;
      border-style: solid;
      border-color: transparent;
      border-left-color: #000;
    }
  </style>
`;let mt;class _t extends dt{static get is(){return"vaadin-date-picker-year-scroller"}static get template(){return mt||(mt=super.template.cloneNode(!0),mt.content.appendChild(pt.content.cloneNode(!0))),mt}static get properties(){return{bufferSize:{type:Number,value:12}}}_createElement(){return document.createElement("vaadin-date-picker-year")}_updateElement(e,t){e.year=this._yearAfterXYears(t)}_yearAfterXYears(e){const t=new Date,i=new Date(t);return i.setFullYear(parseInt(e)+t.getFullYear()),i.getFullYear()}}customElements.define(_t.is,_t);
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
class vt extends(x(D)){static get is(){return"vaadin-date-picker-year"}static get template(){return C`
      <style>
        :host {
          display: block;
          height: 100%;
        }
      </style>
      <div part="year-number">[[year]]</div>
      <div part="year-separator" aria-hidden="true"></div>
    `}static get properties(){return{year:{type:String},selectedDate:{type:Object}}}static get observers(){return["__updateSelected(year, selectedDate)"]}__updateSelected(e,t){this.toggleAttribute("selected",t&&t.getFullYear()===e),this.toggleAttribute("current",e===(new Date).getFullYear())}}customElements.define(vt.is,vt);
/**
 * @license
 * Copyright (c) 2021 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
class gt{constructor(e,t){this.query=e,this.callback=t,this._boundQueryHandler=this._queryHandler.bind(this)}hostConnected(){this._removeListener(),this._mediaQuery=window.matchMedia(this.query),this._addListener(),this._queryHandler(this._mediaQuery)}hostDisconnected(){this._removeListener()}_addListener(){this._mediaQuery&&this._mediaQuery.addListener(this._boundQueryHandler)}_removeListener(){this._mediaQuery&&this._mediaQuery.removeListener(this._boundQueryHandler),this._mediaQuery=null}_queryHandler(e){"function"==typeof this.callback&&this.callback(e.matches)}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */class ft extends(k(x(w(D)))){static get template(){return C`
      <style>
        :host {
          display: flex;
          flex-direction: column;
          height: 100%;
          width: 100%;
          outline: none;
        }

        [part='overlay-header'] {
          display: flex;
          flex-shrink: 0;
          flex-wrap: nowrap;
          align-items: center;
        }

        :host(:not([fullscreen])) [part='overlay-header'] {
          display: none;
        }

        [part='label'] {
          flex-grow: 1;
        }

        [hidden] {
          display: none !important;
        }

        [part='years-toggle-button'] {
          display: flex;
        }

        #scrollers {
          display: flex;
          height: 100%;
          width: 100%;
          position: relative;
          overflow: hidden;
        }

        :host([desktop]) ::slotted([slot='months']) {
          right: 50px;
          transform: none !important;
        }

        :host([desktop]) ::slotted([slot='years']) {
          transform: none !important;
        }

        :host(.animate) ::slotted([slot='months']),
        :host(.animate) ::slotted([slot='years']) {
          transition: all 200ms;
        }

        [part='toolbar'] {
          display: flex;
          justify-content: space-between;
          z-index: 2;
          flex-shrink: 0;
        }
      </style>

      <div part="overlay-header" on-touchend="_preventDefault" aria-hidden="true">
        <div part="label">[[_formatDisplayed(selectedDate, i18n.formatDate, label)]]</div>
        <div part="clear-button" hidden$="[[!selectedDate]]"></div>
        <div part="toggle-button"></div>

        <div part="years-toggle-button" hidden$="[[_desktopMode]]" aria-hidden="true">
          [[_yearAfterXMonths(_visibleMonthIndex)]]
        </div>
      </div>

      <div id="scrollers">
        <slot name="months"></slot>
        <slot name="years"></slot>
      </div>

      <div on-touchend="_preventDefault" role="toolbar" part="toolbar">
        <slot name="today-button"></slot>
        <slot name="cancel-button"></slot>
      </div>
    `}static get is(){return"vaadin-date-picker-overlay-content"}static get properties(){return{scrollDuration:{type:Number,value:300},selectedDate:{type:Date,value:null},focusedDate:{type:Date,notify:!0,observer:"_focusedDateChanged"},_focusedMonthDate:Number,initialPosition:{type:Date,observer:"_initialPositionChanged"},_originDate:{value:new Date},_visibleMonthIndex:Number,_desktopMode:{type:Boolean,observer:"_desktopModeChanged"},_desktopMediaQuery:{type:String,value:"(min-width: 375px)"},_translateX:{observer:"_translateXChanged"},_yearScrollerWidth:{value:50},i18n:{type:Object},showWeekNumbers:{type:Boolean,value:!1},_ignoreTaps:Boolean,_notTapping:Boolean,minDate:Date,maxDate:Date,label:String,_cancelButton:{type:Object},_todayButton:{type:Object},calendars:{type:Array,value:()=>[]},years:{type:Array,value:()=>[]}}}static get observers(){return["__updateCalendars(calendars, i18n, minDate, maxDate, selectedDate, focusedDate, showWeekNumbers, _ignoreTaps, _theme)","__updateCancelButton(_cancelButton, i18n)","__updateTodayButton(_todayButton, i18n, minDate, maxDate)","__updateYears(years, selectedDate, _theme)"]}get __useSubMonthScrolling(){return this._monthScroller.clientHeight<this._monthScroller.itemHeight+this._monthScroller.bufferOffset}get focusableDateElement(){return this.calendars.map((e=>e.focusableDateElement)).find(Boolean)}ready(){super.ready(),this.setAttribute("role","dialog"),U(this.$.scrollers,"track",this._track.bind(this)),U(this.shadowRoot.querySelector('[part="clear-button"]'),"tap",this._clear.bind(this)),U(this.shadowRoot.querySelector('[part="toggle-button"]'),"tap",this._cancel.bind(this)),U(this.shadowRoot.querySelector('[part="years-toggle-button"]'),"tap",this._toggleYearScroller.bind(this)),this.addController(new gt(this._desktopMediaQuery,(e=>{this._desktopMode=e}))),this.addController(new J(this,"today-button","vaadin-button",{observe:!1,initializer:e=>{e.setAttribute("theme","tertiary"),e.addEventListener("keydown",(e=>this.__onTodayButtonKeyDown(e))),U(e,"tap",this._onTodayTap.bind(this)),this._todayButton=e}})),this.addController(new J(this,"cancel-button","vaadin-button",{observe:!1,initializer:e=>{e.setAttribute("theme","tertiary"),e.addEventListener("keydown",(e=>this.__onCancelButtonKeyDown(e))),U(e,"tap",this._cancel.bind(this)),this._cancelButton=e}})),this.__initMonthScroller(),this.__initYearScroller()}connectedCallback(){super.connectedCallback(),this._closeYearScroller(),this._toggleAnimateClass(!0),Z(this.$.scrollers,"pan-y")}focusCancel(){this._cancelButton.focus()}scrollToDate(e,t){const i=this.__useSubMonthScrolling?this._calculateWeekScrollOffset(e):0;this._scrollToPosition(this._differenceInMonths(e,this._originDate)+i,t),this._monthScroller.forceUpdate()}__initMonthScroller(){this.addController(new J(this,"months","vaadin-date-picker-month-scroller",{observe:!1,initializer:e=>{e.addEventListener("custom-scroll",(()=>{this._onMonthScroll()})),e.addEventListener("touchstart",(()=>{this._onMonthScrollTouchStart()})),e.addEventListener("keydown",(e=>{this.__onMonthCalendarKeyDown(e)})),e.addEventListener("init-done",(()=>{const e=[...this.querySelectorAll("vaadin-month-calendar")];e.forEach((e=>{e.addEventListener("selected-date-changed",(e=>{this.selectedDate=e.detail.value}))})),this.calendars=e})),this._monthScroller=e}}))}__initYearScroller(){this.addController(new J(this,"years","vaadin-date-picker-year-scroller",{observe:!1,initializer:e=>{e.setAttribute("aria-hidden","true"),U(e,"tap",(e=>{this._onYearTap(e)})),e.addEventListener("custom-scroll",(()=>{this._onYearScroll()})),e.addEventListener("touchstart",(()=>{this._onYearScrollTouchStart()})),e.addEventListener("init-done",(()=>{this.years=[...this.querySelectorAll("vaadin-date-picker-year")]})),this._yearScroller=e}}))}__updateCancelButton(e,t){e&&(e.textContent=t&&t.cancel)}__updateTodayButton(e,t,i,s){e&&(e.textContent=t&&t.today,e.disabled=!this._isTodayAllowed(i,s))}__updateCalendars(e,t,i,s,o,n,a,r,l){e&&e.length&&e.forEach((e=>{e.setProperties({i18n:t,minDate:i,maxDate:s,focusedDate:n,selectedDate:o,showWeekNumbers:a,ignoreTaps:r}),l?e.setAttribute("theme",l):e.removeAttribute("theme")}))}__updateYears(e,t,i){e&&e.length&&e.forEach((e=>{e.selectedDate=t,i?e.setAttribute("theme",i):e.removeAttribute("theme")}))}_selectDate(e){this.selectedDate=e,this.dispatchEvent(new CustomEvent("date-selected",{detail:{date:e},bubbles:!0,composed:!0}))}_desktopModeChanged(e){this.toggleAttribute("desktop",e)}_focusedDateChanged(e){this.revealDate(e)}revealDate(e,t=!0){if(!e)return;const i=this._differenceInMonths(e,this._originDate);if(this.__useSubMonthScrolling){const s=this._calculateWeekScrollOffset(e);return void this._scrollToPosition(i+s,t)}const s=this._monthScroller.position>i,o=Math.max(this._monthScroller.itemHeight,this._monthScroller.clientHeight-2*this._monthScroller.bufferOffset)/this._monthScroller.itemHeight,n=this._monthScroller.position+o-1<i;s?this._scrollToPosition(i,t):n&&this._scrollToPosition(i-o+1,t)}_calculateWeekScrollOffset(e){const t=new Date(0,0);t.setFullYear(e.getFullYear()),t.setMonth(e.getMonth()),t.setDate(1);let i=0;for(;t.getDate()<e.getDate();)t.setDate(t.getDate()+1),t.getDay()===this.i18n.firstDayOfWeek&&(i+=1);return i/6}_initialPositionChanged(e){this._monthScroller&&this._yearScroller&&(this._monthScroller.active=!0,this._yearScroller.active=!0),this.scrollToDate(e)}_repositionYearScroller(){const e=this._monthScroller.position;this._visibleMonthIndex=Math.floor(e),this._yearScroller.position=(e+this._originDate.getMonth())/12}_repositionMonthScroller(){this._monthScroller.position=12*this._yearScroller.position-this._originDate.getMonth(),this._visibleMonthIndex=Math.floor(this._monthScroller.position)}_onMonthScroll(){this._repositionYearScroller(),this._doIgnoreTaps()}_onYearScroll(){this._repositionMonthScroller(),this._doIgnoreTaps()}_onYearScrollTouchStart(){this._notTapping=!1,setTimeout((()=>{this._notTapping=!0}),300),this._repositionMonthScroller()}_onMonthScrollTouchStart(){this._repositionYearScroller()}_doIgnoreTaps(){this._ignoreTaps=!0,this._debouncer=K.debounce(this._debouncer,X.after(300),(()=>{this._ignoreTaps=!1}))}_formatDisplayed(e,t,i){return e?t(nt(e)):i}_onTodayTap(){const e=new Date;Math.abs(this._monthScroller.position-this._differenceInMonths(e,this._originDate))<.001?(this._selectDate(e),this._close()):this._scrollToCurrentMonth()}_scrollToCurrentMonth(){this.focusedDate&&(this.focusedDate=new Date),this.scrollToDate(new Date,!0)}_onYearTap(e){if(!this._ignoreTaps&&!this._notTapping){const t=(e.detail.y-(this._yearScroller.getBoundingClientRect().top+this._yearScroller.clientHeight/2))/this._yearScroller.itemHeight;this._scrollToPosition(this._monthScroller.position+12*t,!0)}}_scrollToPosition(e,t){if(void 0!==this._targetPosition)return void(this._targetPosition=e);if(!t)return this._monthScroller.position=e,this._targetPosition=void 0,this._repositionYearScroller(),void this.__tryFocusDate();let i;this._targetPosition=e,this._revealPromise=new Promise((e=>{i=e}));let s=0;const o=this._monthScroller.position,n=e=>{s||(s=e);const t=e-s;if(t<this.scrollDuration){const e=(a=t,r=o,l=this._targetPosition-o,d=this.scrollDuration,(a/=d/2)<1?l/2*a*a+r:-l/2*((a-=1)*(a-2)-1)+r);this._monthScroller.position=e,window.requestAnimationFrame(n)}else this.dispatchEvent(new CustomEvent("scroll-animation-finished",{bubbles:!0,composed:!0,detail:{position:this._targetPosition,oldPosition:o}})),this._monthScroller.position=this._targetPosition,this._targetPosition=void 0,i(),this._revealPromise=void 0;var a,r,l,d;setTimeout(this._repositionYearScroller.bind(this),1)};window.requestAnimationFrame(n)}_limit(e,t){return Math.min(t.max,Math.max(t.min,e))}_handleTrack(e){if(Math.abs(e.detail.dx)<10||Math.abs(e.detail.ddy)>10)return;Math.abs(e.detail.ddx)>this._yearScrollerWidth/3&&this._toggleAnimateClass(!0);const t=this._translateX+e.detail.ddx;this._translateX=this._limit(t,{min:0,max:this._yearScrollerWidth})}_track(e){if(!this._desktopMode)switch(e.detail.state){case"start":this._toggleAnimateClass(!1);break;case"track":this._handleTrack(e);break;case"end":this._toggleAnimateClass(!0),this._translateX>=this._yearScrollerWidth/2?this._closeYearScroller():this._openYearScroller()}}_toggleAnimateClass(e){e?this.classList.add("animate"):this.classList.remove("animate")}_toggleYearScroller(){this._isYearScrollerVisible()?this._closeYearScroller():this._openYearScroller()}_openYearScroller(){this._translateX=0,this.setAttribute("years-visible","")}_closeYearScroller(){this.removeAttribute("years-visible"),this._translateX=this._yearScrollerWidth}_isYearScrollerVisible(){return this._translateX<this._yearScrollerWidth/2}_translateXChanged(e){this._desktopMode||(this._monthScroller.style.transform=`translateX(${e-this._yearScrollerWidth}px)`,this._yearScroller.style.transform=`translateX(${e}px)`)}_yearAfterXMonths(e){return at(e).getFullYear()}_differenceInMonths(e,t){return 12*(e.getFullYear()-t.getFullYear())-t.getMonth()+e.getMonth()}_clear(){this._selectDate("")}_close(){this.dispatchEvent(new CustomEvent("close",{bubbles:!0,composed:!0}))}_cancel(){this.focusedDate=this.selectedDate,this._close()}_preventDefault(e){e.preventDefault()}__toggleDate(e){it(e,this.selectedDate)?(this._clear(),this.focusedDate=e):this._selectDate(e)}__onMonthCalendarKeyDown(e){let t=!1;switch(e.key){case"ArrowDown":this._moveFocusByDays(7),t=!0;break;case"ArrowUp":this._moveFocusByDays(-7),t=!0;break;case"ArrowRight":this._moveFocusByDays(this.__isRTL?-1:1),t=!0;break;case"ArrowLeft":this._moveFocusByDays(this.__isRTL?1:-1),t=!0;break;case"Enter":this._selectDate(this.focusedDate),this._close(),t=!0;break;case" ":this.__toggleDate(this.focusedDate),t=!0;break;case"Home":this._moveFocusInsideMonth(this.focusedDate,"minDate"),t=!0;break;case"End":this._moveFocusInsideMonth(this.focusedDate,"maxDate"),t=!0;break;case"PageDown":this._moveFocusByMonths(e.shiftKey?12:1),t=!0;break;case"PageUp":this._moveFocusByMonths(e.shiftKey?-12:-1),t=!0;break;case"Tab":this._onTabKeyDown(e,"calendar")}t&&(e.preventDefault(),e.stopPropagation())}_onTabKeyDown(e,t){switch(e.stopPropagation(),t){case"calendar":e.shiftKey&&(e.preventDefault(),this.hasAttribute("fullscreen")?this.focusCancel():this.__focusInput());break;case"today":e.shiftKey&&(e.preventDefault(),this.focusDateElement());break;case"cancel":e.shiftKey||(e.preventDefault(),this.hasAttribute("fullscreen")?this.focusDateElement():this.__focusInput())}}__onTodayButtonKeyDown(e){"Tab"===e.key&&this._onTabKeyDown(e,"today")}__onCancelButtonKeyDown(e){"Tab"===e.key&&this._onTabKeyDown(e,"cancel")}__focusInput(){this.dispatchEvent(new CustomEvent("focus-input",{bubbles:!0,composed:!0}))}__tryFocusDate(){if(this.__pendingDateFocus){const e=this.focusableDateElement;e&&it(e.date,this.__pendingDateFocus)&&(delete this.__pendingDateFocus,e.focus())}}async focusDate(e,t){const i=e||this.selectedDate||this.initialPosition||new Date;this.focusedDate=i,t||(this._focusedMonthDate=i.getDate()),await this.focusDateElement(!1)}async focusDateElement(e=!0){this.__pendingDateFocus=this.focusedDate,this.calendars.length||await new Promise((e=>{T(this,(()=>{Je(),e()}))})),e&&this.revealDate(this.focusedDate),this._revealPromise&&await this._revealPromise,this.__tryFocusDate()}_focusClosestDate(e){this.focusDate(ot(e,[this.minDate,this.maxDate]))}_focusAllowedDate(e,t,i){this._dateAllowed(e)?this.focusDate(e,i):this._dateAllowed(this.focusedDate)?t>0?this.focusDate(this.maxDate):this.focusDate(this.minDate):this._focusClosestDate(this.focusedDate)}_getDateDiff(e,t){const i=new Date(0,0);return i.setFullYear(this.focusedDate.getFullYear()),i.setMonth(this.focusedDate.getMonth()+e),t&&i.setDate(this.focusedDate.getDate()+t),i}_moveFocusByDays(e){const t=this._getDateDiff(0,e);this._focusAllowedDate(t,e,!1)}_moveFocusByMonths(e){const t=this._getDateDiff(e),i=t.getMonth();this._focusedMonthDate||(this._focusedMonthDate=this.focusedDate.getDate()),t.setDate(this._focusedMonthDate),t.getMonth()!==i&&t.setDate(0),this._focusAllowedDate(t,e,!0)}_moveFocusInsideMonth(e,t){const i=new Date(0,0);i.setFullYear(e.getFullYear()),"minDate"===t?(i.setMonth(e.getMonth()),i.setDate(1)):(i.setMonth(e.getMonth()+1),i.setDate(0)),this._dateAllowed(i)?this.focusDate(i):this._dateAllowed(e)?this.focusDate(this[t]):this._focusClosestDate(e)}_dateAllowed(e,t=this.minDate,i=this.maxDate){return(!t||e>=t)&&(!i||e<=i)}_isTodayAllowed(e,t){const i=new Date,s=new Date(0,0);return s.setFullYear(i.getFullYear()),s.setMonth(i.getMonth()),s.setDate(i.getDate()),this._dateAllowed(s,e,t)}}customElements.define(ft.is,ft);
/**
 * @license
 * Copyright (c) 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const yt=e=>class extends e{static get properties(){return{overlayClass:{type:String},_overlayElement:{type:Object}}}static get observers(){return["__updateOverlayClassNames(overlayClass, _overlayElement)"]}__updateOverlayClassNames(e,t){if(!t)return;if(void 0===e)return;const{classList:i}=t;if(this.__initialClasses||(this.__initialClasses=new Set(i)),Array.isArray(this.__previousClasses)){const e=this.__previousClasses.filter((e=>!this.__initialClasses.has(e)));e.length>0&&i.remove(...e)}const s="string"==typeof e?e.split(" "):[];s.length>0&&i.add(...s),this.__previousClasses=s}}
/**
 * @license
 * Copyright (c) 2021 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;class bt{constructor(e){this.host=e,e.addEventListener("opened-changed",(()=>{e.opened||this.__setVirtualKeyboardEnabled(!1)})),e.addEventListener("blur",(()=>this.__setVirtualKeyboardEnabled(!0))),e.addEventListener("touchstart",(()=>this.__setVirtualKeyboardEnabled(!0)))}__setVirtualKeyboardEnabled(e){this.host.inputElement&&(this.host.inputElement.inputMode=e?"":"none")}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */const xt=e=>class extends(yt(k(ee(de(te(e)))))){static get properties(){return{_selectedDate:{type:Date},_focusedDate:Date,value:{type:String,notify:!0,value:""},initialPosition:String,opened:{type:Boolean,reflectToAttribute:!0,notify:!0,observer:"_openedChanged"},autoOpenDisabled:Boolean,showWeekNumbers:{type:Boolean,value:!1},_fullscreen:{type:Boolean,value:!1},_fullscreenMediaQuery:{value:"(max-width: 420px), (max-height: 420px)"},i18n:{type:Object,value:()=>({monthNames:["January","February","March","April","May","June","July","August","September","October","November","December"],weekdays:["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],weekdaysShort:["Sun","Mon","Tue","Wed","Thu","Fri","Sat"],firstDayOfWeek:0,today:"Today",cancel:"Cancel",referenceDate:"",formatDate(e){const t=String(e.year).replace(/\d+/u,(e=>"0000".substr(e.length)+e));return[e.month+1,e.day,t].join("/")},parseDate(e){const t=e.split("/"),i=new Date;let s,o=i.getMonth(),n=i.getFullYear();if(3===t.length){if(o=parseInt(t[0])-1,s=parseInt(t[1]),n=parseInt(t[2]),t[2].length<3&&n>=0){n=function(e,t,i=0,s=1){if(t>99)throw new Error("The provided year cannot have more than 2 digits.");if(t<0)throw new Error("The provided year cannot be negative.");let o=t+100*Math.floor(e.getFullYear()/100);return e<new Date(o-50,i,s)?o-=100:e>new Date(o+50,i,s)&&(o+=100),o}(this.referenceDate?rt(this.referenceDate):new Date,n,o,s)}}else 2===t.length?(o=parseInt(t[0])-1,s=parseInt(t[1])):1===t.length&&(s=parseInt(t[0]));if(void 0!==s)return{day:s,month:o,year:n}},formatTitle:(e,t)=>`${e} ${t}`})},min:{type:String},max:{type:String},_minDate:{type:Date,computed:"__computeMinOrMaxDate(min)"},_maxDate:{type:Date,computed:"__computeMinOrMaxDate(max)"},_noInput:{type:Boolean,computed:"_isNoInput(inputElement, _fullscreen, _ios, i18n, opened, autoOpenDisabled)"},_ios:{type:Boolean,value:S},_focusOverlayOnOpen:Boolean,_overlayContent:Object}}static get observers(){return["_selectedDateChanged(_selectedDate, i18n.formatDate)","_focusedDateChanged(_focusedDate, i18n.formatDate)","__updateOverlayContent(_overlayContent, i18n, label, _minDate, _maxDate, _focusedDate, _selectedDate, showWeekNumbers)","__updateOverlayContentTheme(_overlayContent, _theme)","__updateOverlayContentFullScreen(_overlayContent, _fullscreen)"]}static get constraints(){return[...super.constraints,"min","max"]}constructor(){super(),this._boundOnClick=this._onClick.bind(this),this._boundOnScroll=this._onScroll.bind(this),this._boundOverlayRenderer=this._overlayRenderer.bind(this)}get clearElement(){return null}get _nativeInput(){return this.inputElement?this.inputElement.focusElement||this.inputElement:null}get _inputValue(){return this.inputElement?this.inputElement.value:void 0}set _inputValue(e){this.inputElement&&(this.inputElement.value=e)}_onFocus(e){super._onFocus(e),this._noInput&&e.target.blur()}_onBlur(e){super._onBlur(e),this.opened||(this.autoOpenDisabled&&this._selectParsedOrFocusedDate(),this.validate(),""===this._inputValue&&""!==this.value&&(this.value=""))}ready(){super.ready(),this.addEventListener("click",this._boundOnClick),this.addController(new gt(this._fullscreenMediaQuery,(e=>{this._fullscreen=e}))),this.addController(new bt(this));const e=this.$.overlay;this._overlayElement=e,e.renderer=this._boundOverlayRenderer,this.addEventListener("mousedown",(()=>this.__bringToFront())),this.addEventListener("touchstart",(()=>this.__bringToFront()))}disconnectedCallback(){super.disconnectedCallback(),this.opened=!1}_propertiesChanged(e,t,i){super._propertiesChanged(e,t,i),"value"in t&&this.__dispatchChange&&(this.dispatchEvent(new CustomEvent("change",{bubbles:!0})),this.__dispatchChange=!1)}open(){this.disabled||this.readonly||(this.opened=!0)}close(){this.$.overlay.close()}_overlayRenderer(e){if(e.firstChild)return;const t=document.createElement("vaadin-date-picker-overlay-content");e.appendChild(t),this._overlayContent=t,t.addEventListener("close",(()=>{this._close()})),t.addEventListener("focus-input",this._focusAndSelect.bind(this)),t.addEventListener("date-tap",(e=>{this.__userConfirmedDate=!0,this._selectDate(e.detail.date),this._close()})),t.addEventListener("date-selected",(e=>{this.__userConfirmedDate=!0,this._selectDate(e.detail.date)})),t.addEventListener("focusin",(()=>{this._keyboardActive&&this._setFocused(!0)})),t.addEventListener("focused-date-changed",(e=>{this._focusedDate=e.detail.value}))}checkValidity(){const e=!this._inputValue||!!this._selectedDate&&this._inputValue===this._getFormattedDate(this.i18n.formatDate,this._selectedDate),t=!this._selectedDate||st(this._selectedDate,this._minDate,this._maxDate);let i=!0;return this.inputElement&&(this.inputElement.checkValidity?i=this.inputElement.checkValidity():this.inputElement.validate&&(i=this.inputElement.validate())),e&&t&&i}_shouldSetFocus(e){return!this._shouldKeepFocusRing}_shouldRemoveFocus(e){return!this.opened}_setFocused(e){super._setFocused(e),this._shouldKeepFocusRing=e&&this._keyboardActive}_selectDate(e){const t=this._formatISO(e);this.value!==t&&(this.__dispatchChange=!0),this._selectedDate=e}_close(){this._focus(),this.close()}__bringToFront(){requestAnimationFrame((()=>{this.$.overlay.bringToFront()}))}_isNoInput(e,t,i,s,o,n){return!e||t&&(!n||o)||i&&o||!s.parseDate}_formatISO(e){if(!(e instanceof Date))return"";const t=(e,t="00")=>(t+e).substr((t+e).length-t.length);let i="",s="0000",o=e.getFullYear();o<0?(o=-o,i="-",s="000000"):e.getFullYear()>=1e4&&(i="+",s="000000");return[i+t(o,s),t(e.getMonth()+1),t(e.getDate())].join("-")}_inputElementChanged(e){super._inputElementChanged(e),e&&(e.autocomplete="off",e.setAttribute("role","combobox"),e.setAttribute("aria-haspopup","dialog"),e.setAttribute("aria-expanded",!!this.opened),this._applyInputValue(this._selectedDate))}_openedChanged(e){this.inputElement&&this.inputElement.setAttribute("aria-expanded",e)}_selectedDateChanged(e,t){if(void 0===e||void 0===t)return;const i=this._formatISO(e);this.__keepInputValue||this._applyInputValue(e),i!==this.value&&(this.validate(),this.value=i),this._ignoreFocusedDateChange=!0,this._focusedDate=e,this._ignoreFocusedDateChange=!1}_focusedDateChanged(e,t){void 0!==e&&void 0!==t&&(this._ignoreFocusedDateChange||this._noInput||this._applyInputValue(e))}_valueChanged(e,t){const i=rt(e);!e||i?(e?it(this._selectedDate,i)||(this._selectedDate=i,void 0!==t&&this.validate()):this._selectedDate=null,this._toggleHasValue(this._hasValue)):this.value=t}__updateOverlayContent(e,t,i,s,o,n,a,r){e&&e.setProperties({i18n:t,label:i,minDate:s,maxDate:o,focusedDate:n,selectedDate:a,showWeekNumbers:r})}__updateOverlayContentTheme(e,t){e&&(t?e.setAttribute("theme",t):e.removeAttribute("theme"))}__updateOverlayContentFullScreen(e,t){e&&e.toggleAttribute("fullscreen",t)}_onOverlayEscapePress(){this._focusedDate=this._selectedDate,this._close()}_onOverlayOpened(){const e=this._getInitialPosition();this._overlayContent.initialPosition=e;const t=this._overlayContent.focusedDate||e;this._overlayContent.scrollToDate(t),this._ignoreFocusedDateChange=!0,this._overlayContent.focusedDate=t,this._ignoreFocusedDateChange=!1,window.addEventListener("scroll",this._boundOnScroll,!0),this._focusOverlayOnOpen?(this._overlayContent.focusDateElement(),this._focusOverlayOnOpen=!1):this._focus(),this._noInput&&this.focusElement&&(this.focusElement.blur(),this._overlayContent.focusDateElement())}_getInitialPosition(){const e=rt(this.initialPosition),t=this._selectedDate||this._overlayContent.initialPosition||e||new Date;return e||st(t,this._minDate,this._maxDate)?t:ot(t,[this._minDate,this._maxDate])}_selectParsedOrFocusedDate(){if(this._ignoreFocusedDateChange=!0,this.i18n.parseDate){const e=this._inputValue||"",t=this._getParsedDate(e);this._isValidDate(t)?this._selectDate(t):(this.__keepInputValue=!0,this._selectDate(null),this._selectedDate=null,this.__keepInputValue=!1)}else this._focusedDate&&this._selectDate(this._focusedDate);this._ignoreFocusedDateChange=!1}_onOverlayClosed(){window.removeEventListener("scroll",this._boundOnScroll,!0),this.__userConfirmedDate?this.__userConfirmedDate=!1:this._selectParsedOrFocusedDate(),this._nativeInput&&this._nativeInput.selectionStart&&(this._nativeInput.selectionStart=this._nativeInput.selectionEnd),this.value||this.validate()}_onScroll(e){e.target!==window&&this._overlayContent.contains(e.target)||this._overlayContent._repositionYearScroller()}_focus(){this._noInput||this.inputElement.focus()}_focusAndSelect(){this._focus(),this._setSelectionRange(0,this._inputValue.length)}_applyInputValue(e){this._inputValue=e?this._getFormattedDate(this.i18n.formatDate,e):""}_getFormattedDate(e,t){return e(nt(t))}_setSelectionRange(e,t){this._nativeInput&&this._nativeInput.setSelectionRange&&this._nativeInput.setSelectionRange(e,t)}_isValidDate(e){return e&&!isNaN(e.getTime())}_onChange(e){""===this._inputValue&&(this.__dispatchChange=!0),e.stopPropagation()}_onClick(e){this._isClearButton(e)||this._onHostClick(e)}_onHostClick(e){this.autoOpenDisabled&&!this._noInput||(e.preventDefault(),this.open())}_onClearButtonClick(e){e.preventDefault(),this.value="",this._inputValue="",this.validate(),this.dispatchEvent(new CustomEvent("change",{bubbles:!0}))}_onKeyDown(e){if(super._onKeyDown(e),this._noInput){-1===[9].indexOf(e.keyCode)&&e.preventDefault()}switch(e.key){case"ArrowDown":case"ArrowUp":e.preventDefault(),this.opened?this._overlayContent.focusDateElement():(this._focusOverlayOnOpen=!0,this.open());break;case"Tab":this.opened&&(e.preventDefault(),e.stopPropagation(),this._setSelectionRange(0,0),e.shiftKey?this._overlayContent.focusCancel():this._overlayContent.focusDateElement())}}_onEnter(e){const t=this.value;this.opened?this.close():this._selectParsedOrFocusedDate(),t===this.value&&this.validate()}_onEscape(e){if(!this.opened)return this.clearButtonVisible&&this.value?(e.stopPropagation(),void this._onClearButtonClick(e)):void(this.autoOpenDisabled?(""===this.inputElement.value&&this._selectDate(null),this._applyInputValue(this._selectedDate)):(this._focusedDate=this._selectedDate,this._selectParsedOrFocusedDate()))}_getParsedDate(e=this._inputValue){const t=this.i18n.parseDate&&this.i18n.parseDate(e);return t&&rt(`${t.year}-${t.month+1}-${t.day}`)}_isClearButton(e){return e.composedPath()[0]===this.clearElement}_onInput(){this.opened||!this.inputElement.value||this.autoOpenDisabled||this.open(),this._userInputValueChanged()}_userInputValueChanged(){if(this._inputValue){const e=this._getParsedDate();this._isValidDate(e)&&(this._ignoreFocusedDateChange=!0,it(e,this._focusedDate)||(this._focusedDate=e),this._ignoreFocusedDateChange=!1)}}__computeMinOrMaxDate(e){return rt(e)}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;f("vaadin-date-picker",he,{moduleId:"vaadin-date-picker-styles"});class wt extends(xt(ce(x(M(D))))){static get is(){return"vaadin-date-picker"}static get template(){return C`
      <style>
        :host([opened]) {
          pointer-events: auto;
        }

        :host([dir='rtl']) [part='input-field'] {
          direction: ltr;
        }

        :host([dir='rtl']) [part='input-field'] ::slotted(input)::placeholder {
          direction: rtl;
          text-align: left;
        }
      </style>

      <div class="vaadin-date-picker-container">
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
          <div id="clearButton" part="clear-button" slot="suffix" aria-hidden="true"></div>
          <div part="toggle-button" slot="suffix" aria-hidden="true" on-click="_toggle"></div>
        </vaadin-input-container>

        <div part="helper-text">
          <slot name="helper"></slot>
        </div>

        <div part="error-message">
          <slot name="error-message"></slot>
        </div>
      </div>

      <vaadin-date-picker-overlay
        id="overlay"
        fullscreen$="[[_fullscreen]]"
        theme$="[[_theme]]"
        opened="{{opened}}"
        on-vaadin-overlay-escape-press="_onOverlayEscapePress"
        on-vaadin-overlay-open="_onOverlayOpened"
        on-vaadin-overlay-closing="_onOverlayClosed"
        restore-focus-on-close
        restore-focus-node="[[inputElement]]"
      ></vaadin-date-picker-overlay>

      <slot name="tooltip"></slot>
    `}get clearElement(){return this.$.clearButton}ready(){super.ready(),this.addController(new ie(this,(e=>{this._setInputElement(e),this._setFocusElement(e),this.stateTarget=e,this.ariaTarget=e}))),this.addController(new se(this.inputElement,this._labelController)),this._tooltipController=new A(this),this.addController(this._tooltipController),this._tooltipController.setPosition("top"),this._tooltipController.setShouldShow((e=>!e.opened));this.shadowRoot.querySelector('[part="toggle-button"]').addEventListener("mousedown",(e=>e.preventDefault())),this.$.overlay.addEventListener("vaadin-overlay-close",this._onVaadinOverlayClose.bind(this))}_onVaadinOverlayClose(e){e.detail.sourceEvent&&e.detail.sourceEvent.composedPath().includes(this)&&e.preventDefault()}_toggle(e){e.stopPropagation(),this.$.overlay.opened?this.close():this.open()}_openedChanged(e){super._openedChanged(e),this.$.overlay.positionTarget=this.shadowRoot.querySelector('[part="input-field"]'),this.$.overlay.noVerticalOverlap=!0}}customElements.define(wt.is,wt);const kt=c`
  :host {
    transition: background-color 100ms;
    overflow: hidden;
    --_lumo-item-selected-icon-display: block;
  }

  @media (any-hover: hover) {
    :host([focused]:not([disabled])) {
      box-shadow: inset 0 0 0 2px var(--lumo-primary-color-50pct);
    }
  }
`;f("vaadin-combo-box-item",[_e,kt],{moduleId:"lumo-combo-box-item"});
/**
 * @license
 * Copyright (c) 2022 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const Dt=c`
  [part~='loader'] {
    box-sizing: border-box;
    width: var(--lumo-icon-size-s);
    height: var(--lumo-icon-size-s);
    border: 2px solid transparent;
    border-color: var(--lumo-primary-color-10pct) var(--lumo-primary-color-10pct) var(--lumo-primary-color)
      var(--lumo-primary-color);
    border-radius: calc(0.5 * var(--lumo-icon-size-s));
    opacity: 0;
    pointer-events: none;
  }

  :host(:not([loading])) [part~='loader'] {
    display: none;
  }

  :host([loading]) [part~='loader'] {
    animation: 1s linear infinite lumo-loader-rotate, 0.3s 0.1s lumo-loader-fade-in both;
  }

  @keyframes lumo-loader-fade-in {
    0% {
      opacity: 0;
    }

    100% {
      opacity: 1;
    }
  }

  @keyframes lumo-loader-rotate {
    0% {
      transform: rotate(0deg);
    }

    100% {
      transform: rotate(360deg);
    }
  }
`,Ct=c`
  [part='content'] {
    padding: 0;
  }

  /* When items are empty, the spinner needs some room */
  :host(:not([closing])) [part~='content'] {
    min-height: calc(2 * var(--lumo-space-s) + var(--lumo-icon-size-s));
  }

  [part~='overlay'] {
    position: relative;
  }

  :host([top-aligned]) [part~='overlay'] {
    margin-top: var(--lumo-space-xs);
  }

  :host([bottom-aligned]) [part~='overlay'] {
    margin-bottom: var(--lumo-space-xs);
  }
`;f("vaadin-combo-box-overlay",[ge,xe,Ct,Dt,c`
  [part~='loader'] {
    position: absolute;
    z-index: 1;
    left: var(--lumo-space-s);
    right: var(--lumo-space-s);
    top: var(--lumo-space-s);
    margin-left: auto;
    margin-inline-start: auto;
    margin-inline-end: 0;
  }

  :host([dir='rtl']) [part~='loader'] {
    left: auto;
    margin-left: 0;
    margin-right: auto;
    margin-inline-start: 0;
    margin-inline-end: auto;
  }
`,c`
      :host {
        --_vaadin-combo-box-items-container-border-width: var(--lumo-space-xs);
        --_vaadin-combo-box-items-container-border-style: solid;
      }
    `],{moduleId:"lumo-combo-box-overlay"}),
/**
 * @license
 * Copyright (c) 2018 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
f("vaadin-time-picker-item",[_e,kt],{moduleId:"lumo-time-picker-item"}),f("vaadin-time-picker-overlay",[ge,xe,Ct,c`
      :host {
        --_vaadin-time-picker-items-container-border-width: var(--lumo-space-xs);
        --_vaadin-time-picker-items-container-border-style: solid;
      }
    `],{moduleId:"lumo-time-picker-overlay"});f("vaadin-time-picker",[le,c`
  [part~='toggle-button']::before {
    content: var(--lumo-icons-clock);
  }

  :host([dir='rtl']) [part='input-field'] ::slotted(input:placeholder-shown) {
    --_lumo-text-field-overflow-mask-image: none;
  }

  :host([dir='rtl']) [part='input-field'] ::slotted(input) {
    --_lumo-text-field-overflow-mask-image: linear-gradient(to left, transparent, #000 1.25em);
  }
`],{moduleId:"lumo-time-picker"});
/**
 * @license
 * Copyright (c) 2015 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const St=e=>class extends e{static get properties(){return{index:{type:Number},item:{type:Object},label:{type:String},selected:{type:Boolean,value:!1,reflectToAttribute:!0},focused:{type:Boolean,value:!1,reflectToAttribute:!0},renderer:{type:Function}}}static get observers(){return["__rendererOrItemChanged(renderer, index, item.*, selected, focused)","__updateLabel(label, renderer)"]}connectedCallback(){super.connectedCallback(),this._owner=this.parentNode.owner;const e=this._owner.getAttribute("dir");e&&this.setAttribute("dir",e)}requestContentUpdate(){if(!this.renderer)return;const e={index:this.index,item:this.item,focused:this.focused,selected:this.selected};this.renderer(this,this._owner,e)}__rendererOrItemChanged(e,t,i){void 0!==i&&void 0!==t&&(this._oldRenderer!==e&&(this.innerHTML="",delete this._$litPart$),e&&(this._oldRenderer=e,this.requestContentUpdate()))}__updateLabel(e,t){t||(this.textContent=e)}}
/**
 * @license
 * Copyright (c) 2018 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;class It extends(St(x(w(D)))){static get is(){return"vaadin-time-picker-item"}static get template(){return C`
      <style>
        :host {
          display: block;
        }

        :host([hidden]) {
          display: none !important;
        }
      </style>
      <span part="checkmark" aria-hidden="true"></span>
      <div part="content">
        <slot></slot>
      </div>
    `}}customElements.define(It.is,It);
/**
 * @license
 * Copyright (c) 2015 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const Tt=class{toString(){return""}},Et=e=>class extends e{static get properties(){return{items:{type:Array,observer:"__itemsChanged"},focusedIndex:{type:Number,observer:"__focusedIndexChanged"},loading:{type:Boolean,observer:"__loadingChanged"},opened:{type:Boolean,observer:"__openedChanged"},selectedItem:{type:Object,observer:"__selectedItemChanged"},itemIdPath:{type:String},owner:{type:Object},getItemLabel:{type:Object},renderer:{type:Object,observer:"__rendererChanged"},theme:{type:String}}}constructor(){super(),this.__boundOnItemClick=this.__onItemClick.bind(this)}get _viewportTotalPaddingBottom(){if(void 0===this._cachedViewportTotalPaddingBottom){const e=window.getComputedStyle(this.$.selector);this._cachedViewportTotalPaddingBottom=[e.paddingBottom,e.borderBottomWidth].map((e=>parseInt(e,10))).reduce(((e,t)=>e+t))}return this._cachedViewportTotalPaddingBottom}ready(){super.ready(),this.setAttribute("role","listbox"),this.id=`${this.localName}-${Q()}`,this.__hostTagName=this.constructor.is.replace("-scroller",""),this.addEventListener("click",(e=>e.stopPropagation())),this.__patchWheelOverScrolling(),this.__virtualizer=new oe({createElements:this.__createElements.bind(this),updateElement:this._updateElement.bind(this),elementsContainer:this,scrollTarget:this,scrollContainer:this.$.selector})}requestContentUpdate(){this.__virtualizer&&this.__virtualizer.update()}scrollIntoView(e){if(!(this.opened&&e>=0))return;const t=this._visibleItemsCount();let i=e;e>this.__virtualizer.lastVisibleIndex-1?(this.__virtualizer.scrollToIndex(e),i=e-t+1):e>this.__virtualizer.firstVisibleIndex&&(i=this.__virtualizer.firstVisibleIndex),this.__virtualizer.scrollToIndex(Math.max(0,i));const s=[...this.children].find((e=>!e.hidden&&e.index===this.__virtualizer.lastVisibleIndex));if(!s||e!==s.index)return;const o=s.getBoundingClientRect(),n=this.getBoundingClientRect(),a=o.bottom-n.bottom+this._viewportTotalPaddingBottom;a>0&&(this.scrollTop+=a)}_isItemSelected(e,t,i){return!(e instanceof Tt)&&(i&&void 0!==e&&void 0!==t?this.get(i,e)===this.get(i,t):e===t)}__itemsChanged(e){this.__virtualizer&&e&&(this.__virtualizer.size=e.length,this.__virtualizer.flush(),this.requestContentUpdate())}__loadingChanged(){this.requestContentUpdate()}__openedChanged(e){e&&this.requestContentUpdate()}__selectedItemChanged(){this.requestContentUpdate()}__focusedIndexChanged(e,t){e!==t&&this.requestContentUpdate(),e>=0&&!this.loading&&this.scrollIntoView(e)}__rendererChanged(e,t){(e||t)&&this.requestContentUpdate()}__createElements(e){return[...Array(e)].map((()=>{const e=document.createElement(`${this.__hostTagName}-item`);return e.addEventListener("click",this.__boundOnItemClick),e.tabIndex="-1",e.style.width="100%",e}))}_updateElement(e,t){const i=this.items[t],s=this.focusedIndex,o=this._isItemSelected(i,this.selectedItem,this.itemIdPath);e.setProperties({item:i,index:t,label:this.getItemLabel(i),selected:o,renderer:this.renderer,focused:!this.loading&&s===t}),e.id=`${this.__hostTagName}-item-${t}`,e.setAttribute("role",void 0!==t&&"option"),e.setAttribute("aria-selected",o.toString()),e.setAttribute("aria-posinset",t+1),e.setAttribute("aria-setsize",this.items.length),this.theme?e.setAttribute("theme",this.theme):e.removeAttribute("theme"),i instanceof Tt&&this.__requestItemByIndex(t)}__onItemClick(e){this.dispatchEvent(new CustomEvent("selection-changed",{detail:{item:e.currentTarget.item}}))}__patchWheelOverScrolling(){this.$.selector.addEventListener("wheel",(e=>{const t=0===this.scrollTop,i=this.scrollHeight-this.scrollTop-this.clientHeight<=1;(t&&e.deltaY<0||i&&e.deltaY>0)&&e.preventDefault()}))}__requestItemByIndex(e){requestAnimationFrame((()=>{this.dispatchEvent(new CustomEvent("index-requested",{detail:{index:e,currentScrollerPos:this._oldScrollerPosition}}))}))}_visibleItemsCount(){this.__virtualizer.scrollToIndex(this.__virtualizer.firstVisibleIndex);return this.__virtualizer.size>0?this.__virtualizer.lastVisibleIndex-this.__virtualizer.firstVisibleIndex+1:0}}
/**
 * @license
 * Copyright (c) 2018 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;
/**
 * @license
 * Copyright (c) 2015 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */class Pt extends(Et(D)){static get is(){return"vaadin-time-picker-scroller"}static get template(){return C`
      <style>
        :host {
          display: block;
          min-height: 1px;
          overflow: auto;

          /* Fixes item background from getting on top of scrollbars on Safari */
          transform: translate3d(0, 0, 0);

          /* Enable momentum scrolling on iOS */
          -webkit-overflow-scrolling: touch;

          /* Fixes scrollbar disappearing when 'Show scroll bars: Always' enabled in Safari */
          box-shadow: 0 0 0 white;
        }

        #selector {
          border-width: var(--_vaadin-time-picker-items-container-border-width);
          border-style: var(--_vaadin-time-picker-items-container-border-style);
          border-color: var(--_vaadin-time-picker-items-container-border-color, transparent);
        }
      </style>
      <div id="selector">
        <slot></slot>
      </div>
    `}}customElements.define(Pt.is,Pt);
/**
 * @license
 * Copyright (c) 2015 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const $t=e=>class extends(Pe(e)){static get observers(){return["_setOverlayWidth(positionTarget, opened)"]}connectedCallback(){super.connectedCallback();const e=this._comboBox,t=e&&e.getAttribute("dir");t&&this.setAttribute("dir",t)}_shouldCloseOnOutsideClick(e){const t=e.composedPath();return!t.includes(this.positionTarget)&&!t.includes(this)}_setOverlayWidth(e,t){if(e&&t){const t=this.localName;this.style.setProperty(`--_${t}-default-width`,`${e.clientWidth}px`);const i=getComputedStyle(this._comboBox).getPropertyValue(`--${t}-width`);""===i?this.style.removeProperty(`--${t}-width`):this.style.setProperty(`--${t}-width`,i),this._updatePosition()}}}
/**
 * @license
 * Copyright (c) 2018 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;let Mt;f("vaadin-time-picker-overlay",c`
    #overlay {
      width: var(--vaadin-time-picker-overlay-width, var(--_vaadin-time-picker-overlay-default-width, auto));
    }

    [part='content'] {
      display: flex;
      flex-direction: column;
      height: 100%;
    }
  `,{moduleId:"vaadin-time-picker-overlay-styles"});class At extends($t(be)){static get is(){return"vaadin-time-picker-overlay"}static get template(){return Mt||(Mt=super.template.cloneNode(!0),Mt.content.querySelector('[part~="overlay"]').removeAttribute("tabindex")),Mt}}
/**
 * @license
 * Copyright (c) 2015 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
function Ot(e){return null!=e}function zt(e,t){return e.findIndex((e=>!(e instanceof Tt)&&t(e)))}customElements.define(At.is,At);const Rt=e=>class extends(yt(k(te(ne(ae(e)))))){static get properties(){return{opened:{type:Boolean,notify:!0,value:!1,reflectToAttribute:!0,observer:"_openedChanged"},autoOpenDisabled:{type:Boolean},readonly:{type:Boolean,value:!1,reflectToAttribute:!0},renderer:Function,items:{type:Array,observer:"_itemsChanged"},allowCustomValue:{type:Boolean,value:!1},filteredItems:{type:Array,observer:"_filteredItemsChanged"},_lastCommittedValue:String,loading:{type:Boolean,value:!1,reflectToAttribute:!0},_focusedIndex:{type:Number,observer:"_focusedIndexChanged",value:-1},filter:{type:String,value:"",notify:!0},selectedItem:{type:Object,notify:!0},itemLabelPath:{type:String,value:"label",observer:"_itemLabelPathChanged"},itemValuePath:{type:String,value:"value"},itemIdPath:String,_toggleElement:{type:Object,observer:"_toggleElementChanged"},_closeOnBlurIsPrevented:Boolean,_scroller:Object,_overlayOpened:{type:Boolean,observer:"_overlayOpenedChanged"}}}static get observers(){return["_selectedItemChanged(selectedItem, itemValuePath, itemLabelPath)","_openedOrItemsChanged(opened, filteredItems, loading)","_updateScroller(_scroller, filteredItems, opened, loading, selectedItem, itemIdPath, _focusedIndex, renderer, theme)"]}constructor(){super(),this._boundOnFocusout=this._onFocusout.bind(this),this._boundOverlaySelectedItemChanged=this._overlaySelectedItemChanged.bind(this),this._boundOnClearButtonMouseDown=this.__onClearButtonMouseDown.bind(this),this._boundOnClick=this._onClick.bind(this),this._boundOnOverlayTouchAction=this._onOverlayTouchAction.bind(this),this._boundOnTouchend=this._onTouchend.bind(this)}get _tagNamePrefix(){return"vaadin-combo-box"}get _nativeInput(){return this.inputElement}get _propertyForValue(){return"value"}get _inputElementValue(){return this.inputElement?this.inputElement[this._propertyForValue]:void 0}set _inputElementValue(e){this.inputElement&&(this.inputElement[this._propertyForValue]=e)}_inputElementChanged(e){super._inputElementChanged(e);const t=this._nativeInput;t&&(t.autocomplete="off",t.autocapitalize="off",t.setAttribute("role","combobox"),t.setAttribute("aria-autocomplete","list"),t.setAttribute("aria-expanded",!!this.opened),t.setAttribute("spellcheck","false"),t.setAttribute("autocorrect","off"),this._revertInputValueToValue(),this.clearElement&&this.clearElement.addEventListener("mousedown",this._boundOnClearButtonMouseDown))}ready(){super.ready(),this._initOverlay(),this._initScroller(),this.addEventListener("focusout",this._boundOnFocusout),this._lastCommittedValue=this.value,this.addEventListener("click",this._boundOnClick),this.addEventListener("touchend",this._boundOnTouchend);const e=()=>{requestAnimationFrame((()=>{this._overlayElement.bringToFront()}))};this.addEventListener("mousedown",e),this.addEventListener("touchstart",e),I(this),this.addController(new bt(this))}disconnectedCallback(){super.disconnectedCallback(),this.close()}requestContentUpdate(){this._scroller&&(this._scroller.requestContentUpdate(),this._getItemElements().forEach((e=>{e.requestContentUpdate()})))}open(){this.disabled||this.readonly||(this.opened=!0)}close(){this.opened=!1}_propertiesChanged(e,t,i){super._propertiesChanged(e,t,i),void 0!==t.filter&&this._filterChanged(t.filter)}_initOverlay(){const e=this.$.overlay;e._comboBox=this,e.addEventListener("touchend",this._boundOnOverlayTouchAction),e.addEventListener("touchmove",this._boundOnOverlayTouchAction),e.addEventListener("mousedown",(e=>e.preventDefault())),e.addEventListener("opened-changed",(e=>{this._overlayOpened=e.detail.value})),this._overlayElement=e}_initScroller(e){const t=`${this._tagNamePrefix}-scroller`,i=this._overlayElement;i.renderer=e=>{e.firstChild||e.appendChild(document.createElement(t))},i.requestContentUpdate();const s=i.querySelector(t);s.owner=e||this,s.getItemLabel=this._getItemLabel.bind(this),s.addEventListener("selection-changed",this._boundOverlaySelectedItemChanged),this._scroller=s}_updateScroller(e,t,i,s,o,n,a,r,l){e&&(i&&(e.style.maxHeight=getComputedStyle(this).getPropertyValue(`--${this._tagNamePrefix}-overlay-max-height`)||"65vh"),e.setProperties({items:i?t:[],opened:i,loading:s,selectedItem:o,itemIdPath:n,focusedIndex:a,renderer:r,theme:l}))}_openedOrItemsChanged(e,t,i){this._overlayOpened=!(!e||!(i||t&&t.length))}_overlayOpenedChanged(e,t){e?(this.dispatchEvent(new CustomEvent("vaadin-combo-box-dropdown-opened",{bubbles:!0,composed:!0})),this._onOpened()):t&&this.filteredItems&&this.filteredItems.length&&(this.close(),this.dispatchEvent(new CustomEvent("vaadin-combo-box-dropdown-closed",{bubbles:!0,composed:!0})))}_focusedIndexChanged(e,t){void 0!==t&&this._updateActiveDescendant(e)}_isInputFocused(){return this.inputElement&&b(this.inputElement)}_updateActiveDescendant(e){const t=this._nativeInput;if(!t)return;const i=this._getItemElements().find((t=>t.index===e));i?t.setAttribute("aria-activedescendant",i.id):t.removeAttribute("aria-activedescendant")}_openedChanged(e,t){if(void 0===t)return;e?(this._openedWithFocusRing=this.hasAttribute("focus-ring"),this._isInputFocused()||re||this.focus(),this._overlayElement.restoreFocusOnClose=!0):(this._onClosed(),this._openedWithFocusRing&&this._isInputFocused()&&this.setAttribute("focus-ring",""));const i=this._nativeInput;i&&(i.setAttribute("aria-expanded",!!e),e?i.setAttribute("aria-controls",this._scroller.id):i.removeAttribute("aria-controls"))}_onOverlayTouchAction(){this._closeOnBlurIsPrevented=!0,this.inputElement.blur(),this._closeOnBlurIsPrevented=!1}_isClearButton(e){return e.composedPath()[0]===this.clearElement}__onClearButtonMouseDown(e){e.preventDefault(),this.inputElement.focus()}_onClearButtonClick(e){e.preventDefault(),this._onClearAction(),this.opened&&this.requestContentUpdate()}_onToggleButtonClick(e){e.preventDefault(),this.opened?this.close():this.open()}_onHostClick(e){this.autoOpenDisabled||(e.preventDefault(),this.open())}_onClick(e){this._isClearButton(e)?this._onClearButtonClick(e):e.composedPath().includes(this._toggleElement)?this._onToggleButtonClick(e):this._onHostClick(e)}_onKeyDown(e){super._onKeyDown(e),"Tab"===e.key?this._overlayElement.restoreFocusOnClose=!1:"ArrowDown"===e.key?(this._onArrowDown(),e.preventDefault()):"ArrowUp"===e.key&&(this._onArrowUp(),e.preventDefault())}_getItemLabel(e){let t=e&&this.itemLabelPath?this.get(this.itemLabelPath,e):void 0;return null==t&&(t=e?e.toString():""),t}_getItemValue(e){let t=e&&this.itemValuePath?this.get(this.itemValuePath,e):void 0;return void 0===t&&(t=e?e.toString():""),t}_onArrowDown(){if(this.opened){const e=this.filteredItems;e&&(this._focusedIndex=Math.min(e.length-1,this._focusedIndex+1),this._prefillFocusedItemLabel())}else this.open()}_onArrowUp(){if(this.opened){if(this._focusedIndex>-1)this._focusedIndex=Math.max(0,this._focusedIndex-1);else{const e=this.filteredItems;e&&(this._focusedIndex=e.length-1)}this._prefillFocusedItemLabel()}else this.open()}_prefillFocusedItemLabel(){if(this._focusedIndex>-1){const e=this.filteredItems[this._focusedIndex];this._inputElementValue=this._getItemLabel(e),this._markAllSelectionRange()}}_setSelectionRange(e,t){this._isInputFocused()&&this.inputElement.setSelectionRange&&this.inputElement.setSelectionRange(e,t)}_markAllSelectionRange(){void 0!==this._inputElementValue&&this._setSelectionRange(0,this._inputElementValue.length)}_clearSelectionRange(){if(void 0!==this._inputElementValue){const e=this._inputElementValue?this._inputElementValue.length:0;this._setSelectionRange(e,e)}}_closeOrCommit(){this.opened||this.loading?this.close():this._commitValue()}_onEnter(e){const t=this._focusedIndex<0&&""!==this._inputElementValue&&this._getItemLabel(this.selectedItem)!==this._inputElementValue;if(!this.allowCustomValue&&t)return e.preventDefault(),void e.stopPropagation();this.opened&&(e.preventDefault(),e.stopPropagation()),this._closeOrCommit()}_onEscape(e){this.autoOpenDisabled?this.opened||this.value!==this._inputElementValue&&this._inputElementValue.length>0?(e.stopPropagation(),this._focusedIndex=-1,this.cancel()):this.clearButtonVisible&&!this.opened&&this.value&&(e.stopPropagation(),this._onClearAction()):this.opened?(e.stopPropagation(),this._focusedIndex>-1?(this._focusedIndex=-1,this._revertInputValue()):this.cancel()):this.clearButtonVisible&&this.value&&(e.stopPropagation(),this._onClearAction())}_toggleElementChanged(e){e&&(e.addEventListener("mousedown",(e=>e.preventDefault())),e.addEventListener("click",(()=>{re&&!this._isInputFocused()&&document.activeElement.blur()})))}_onClearAction(){this.selectedItem=null,this.allowCustomValue&&(this.value=""),this._detectAndDispatchChange()}cancel(){this._revertInputValueToValue(),this._lastCommittedValue=this.value,this._closeOrCommit()}_onOpened(){requestAnimationFrame((()=>{this._scrollIntoView(this._focusedIndex),this._updateActiveDescendant(this._focusedIndex)})),this._lastCommittedValue=this.value}_onClosed(){this.loading&&!this.allowCustomValue||this._commitValue()}_commitValue(){if(this._focusedIndex>-1){const e=this.filteredItems[this._focusedIndex];this.selectedItem!==e&&(this.selectedItem=e),this._inputElementValue=this._getItemLabel(this.selectedItem)}else if(""===this._inputElementValue||void 0===this._inputElementValue)this.selectedItem=null,this.allowCustomValue&&(this.value="");else{const e=[...this.filteredItems||[],this.selectedItem],t=e[this.__getItemIndexByLabel(e,this._inputElementValue)];if(this.allowCustomValue&&!t){const e=this._inputElementValue;this._lastCustomValue=e;const t=new CustomEvent("custom-value-set",{detail:e,composed:!0,cancelable:!0,bubbles:!0});this.dispatchEvent(t),t.defaultPrevented||(this.value=e)}else this.allowCustomValue||this.opened||!t?this._inputElementValue=this.selectedItem?this._getItemLabel(this.selectedItem):this.value||"":this.value=this._getItemValue(t)}this._detectAndDispatchChange(),this._clearSelectionRange(),this.filter=""}_onInput(e){const t=this._inputElementValue,i={};this.filter===t?this._filterChanged(this.filter):i.filter=t,this.opened||this._isClearButton(e)||this.autoOpenDisabled||(i.opened=!0),this.setProperties(i)}_onChange(e){e.stopPropagation()}_itemLabelPathChanged(e){"string"!=typeof e&&console.error("You should set itemLabelPath to a valid string")}_filterChanged(e){this._scrollIntoView(0),this._focusedIndex=-1,this.items?this.filteredItems=this._filterItems(this.items,e):this._filteredItemsChanged(this.filteredItems)}_revertInputValue(){""!==this.filter?this._inputElementValue=this.filter:this._revertInputValueToValue(),this._clearSelectionRange()}_revertInputValueToValue(){this.allowCustomValue&&!this.selectedItem?this._inputElementValue=this.value:this._inputElementValue=this._getItemLabel(this.selectedItem)}_selectedItemChanged(e){if(null==e)this.filteredItems&&(this.allowCustomValue||(this.value=""),this._toggleHasValue(this._hasValue),this._inputElementValue=this.value);else{const t=this._getItemValue(e);if(this.value!==t&&(this.value=t,this.value!==t))return;this._toggleHasValue(!0),this._inputElementValue=this._getItemLabel(e)}this.filteredItems&&(this._focusedIndex=this.filteredItems.indexOf(e))}_valueChanged(e,t){""===e&&void 0===t||(Ot(e)?(this._getItemValue(this.selectedItem)!==e&&this._selectItemForValue(e),!this.selectedItem&&this.allowCustomValue&&(this._inputElementValue=e),this._toggleHasValue(this._hasValue)):this.selectedItem=null,this.filter="",this._lastCommittedValue=void 0)}_detectAndDispatchChange(){this.value!==this._lastCommittedValue&&(this.dispatchEvent(new CustomEvent("change",{bubbles:!0})),this._lastCommittedValue=this.value)}_itemsChanged(e,t){this._ensureItemsOrDataProvider((()=>{this.items=t})),e?this.filteredItems=e.slice(0):t&&(this.filteredItems=null)}_filteredItemsChanged(e,t){const i=t?t[this._focusedIndex]:null,s=this.__getItemIndexByValue(e,this.value);(null===this.selectedItem||void 0===this.selectedItem)&&s>=0&&(this.selectedItem=e[s]);const o=this.__getItemIndexByValue(e,this._getItemValue(i));o>-1?this._focusedIndex=o:this.__setInitialFocusedIndex()}__setInitialFocusedIndex(){const e=this._inputElementValue;void 0===e||e===this._getItemLabel(this.selectedItem)?this._focusedIndex=this.__getItemIndexByLabel(this.filteredItems,this._getItemLabel(this.selectedItem)):this._focusedIndex=this.__getItemIndexByLabel(this.filteredItems,this.filter)}_filterItems(e,t){if(!e)return e;const i=e.filter((e=>(t=t?t.toString().toLowerCase():"",this._getItemLabel(e).toString().toLowerCase().indexOf(t)>-1)));return i}_selectItemForValue(e){const t=this.__getItemIndexByValue(this.filteredItems,e),i=this.selectedItem;t>=0?this.selectedItem=this.filteredItems[t]:this.dataProvider&&void 0===this.selectedItem?this.selectedItem=void 0:this.selectedItem=null,null===this.selectedItem&&null===i&&this._selectedItemChanged(this.selectedItem)}_getItemElements(){return Array.from(this._scroller.querySelectorAll(`${this._tagNamePrefix}-item`))}_scrollIntoView(e){this._scroller&&this._scroller.scrollIntoView(e)}__getItemIndexByValue(e,t){return e&&Ot(t)?zt(e,(e=>this._getItemValue(e)===t)):-1}__getItemIndexByLabel(e,t){return e&&t?zt(e,(e=>this._getItemLabel(e).toString().toLowerCase()===t.toString().toLowerCase())):-1}_overlaySelectedItemChanged(e){e.stopPropagation(),e.detail.item instanceof Tt||this.opened&&(this._focusedIndex=this.filteredItems.indexOf(e.detail.item),this.close())}_onFocusout(e){if(!e.relatedTarget||e.relatedTarget.localName!==`${this._tagNamePrefix}-item`)if(e.relatedTarget!==this._overlayElement){if(!this.readonly&&!this._closeOnBlurIsPrevented){if(!this.opened&&this.allowCustomValue&&this._inputElementValue===this._lastCustomValue)return void delete this._lastCustomValue;this._closeOrCommit()}}else e.composedPath()[0].focus()}_onTouchend(e){this.clearElement&&e.composedPath()[0]===this.clearElement&&(e.preventDefault(),this._onClearAction())}}
/**
 * @license
 * Copyright (c) 2018 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;class Bt extends(Rt(x(D))){static get is(){return"vaadin-time-picker-combo-box"}static get template(){return C`
      <style>
        :host([opened]) {
          pointer-events: auto;
        }
      </style>

      <slot></slot>

      <vaadin-time-picker-overlay
        id="overlay"
        opened="[[_overlayOpened]]"
        loading$="[[loading]]"
        theme$="[[_theme]]"
        position-target="[[positionTarget]]"
        no-vertical-overlap
        restore-focus-node="[[inputElement]]"
      ></vaadin-time-picker-overlay>
    `}static get properties(){return{positionTarget:{type:Object}}}get _tagNamePrefix(){return"vaadin-time-picker"}get clearElement(){return this.querySelector('[part="clear-button"]')}ready(){super.ready(),this.allowCustomValue=!0,this._toggleElement=this.querySelector(".toggle-button"),this.setAttribute("dir","ltr")}}customElements.define(Bt.is,Bt);
/**
 * @license
 * Copyright (c) 2021 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const Ft=e=>class extends(de(e)){static get properties(){return{pattern:{type:String}}}static get delegateAttrs(){return[...super.delegateAttrs,"pattern"]}static get constraints(){return[...super.constraints,"pattern"]}}
/**
 * @license
 * Copyright (c) 2018 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */,Vt="00:00:00.000",Lt="23:59:59.999";f("vaadin-time-picker",he,{moduleId:"vaadin-time-picker-styles"});class Nt extends(Ft(ce(x(M(D))))){static get is(){return"vaadin-time-picker"}static get template(){return C`
      <style>
        /* See https://github.com/vaadin/vaadin-time-picker/issues/145 */
        :host([dir='rtl']) [part='input-field'] {
          direction: ltr;
        }

        :host([dir='rtl']) [part='input-field'] ::slotted(input)::placeholder {
          direction: rtl;
          text-align: left;
        }

        [part~='toggle-button'] {
          cursor: pointer;
        }
      </style>

      <div class="vaadin-time-picker-container">
        <div part="label">
          <slot name="label"></slot>
          <span part="required-indicator" aria-hidden="true" on-click="focus"></span>
        </div>

        <vaadin-time-picker-combo-box
          id="comboBox"
          filtered-items="[[__dropdownItems]]"
          value="{{_comboBoxValue}}"
          opened="{{opened}}"
          disabled="[[disabled]]"
          readonly="[[readonly]]"
          clear-button-visible="[[clearButtonVisible]]"
          auto-open-disabled="[[autoOpenDisabled]]"
          overlay-class="[[overlayClass]]"
          position-target="[[_inputContainer]]"
          theme$="[[_theme]]"
          on-change="__onComboBoxChange"
        >
          <vaadin-input-container
            part="input-field"
            readonly="[[readonly]]"
            disabled="[[disabled]]"
            invalid="[[invalid]]"
            theme$="[[_theme]]"
          >
            <slot name="prefix" slot="prefix"></slot>
            <slot name="input"></slot>
            <div id="clearButton" part="clear-button" slot="suffix" aria-hidden="true"></div>
            <div id="toggleButton" class="toggle-button" part="toggle-button" slot="suffix" aria-hidden="true"></div>
          </vaadin-input-container>
        </vaadin-time-picker-combo-box>

        <div part="helper-text">
          <slot name="helper"></slot>
        </div>

        <div part="error-message">
          <slot name="error-message"></slot>
        </div>
      </div>
      <slot name="tooltip"></slot>
    `}static get properties(){return{value:{type:String,notify:!0,value:""},opened:{type:Boolean,notify:!0,value:!1,reflectToAttribute:!0},min:{type:String,value:""},max:{type:String,value:""},step:{type:Number},autoOpenDisabled:Boolean,overlayClass:{type:String},__dropdownItems:{type:Array},i18n:{type:Object,value:()=>({formatTime:e=>{if(!e)return;const t=(e=0,t="00")=>(t+e).substr((t+e).length-t.length);let i=`${t(e.hours)}:${t(e.minutes)}`;return void 0!==e.seconds&&(i+=`:${t(e.seconds)}`),void 0!==e.milliseconds&&(i+=`.${t(e.milliseconds,"000")}`),i},parseTime:e=>{const t="(\\d|[0-5]\\d)",i=new RegExp(`^(\\d|[0-1]\\d|2[0-3])(?::${t}(?::${t}(?:\\.(\\d{1,3}))?)?)?$`,"u").exec(e);if(i){if(i[4])for(;i[4].length<3;)i[4]+="0";return{hours:i[1],minutes:i[2],seconds:i[3],milliseconds:i[4]}}}})},_comboBoxValue:{type:String,observer:"__comboBoxValueChanged"},_inputContainer:Object}}static get observers(){return["__updateDropdownItems(i18n.*, min, max, step)"]}static get constraints(){return[...super.constraints,"min","max"]}get clearElement(){return this.$.clearButton}ready(){super.ready(),this.addController(new ie(this,(e=>{this._setInputElement(e),this._setFocusElement(e),this.stateTarget=e,this.ariaTarget=e}))),this.addController(new se(this.inputElement,this._labelController)),this._inputContainer=this.shadowRoot.querySelector('[part~="input-field"]'),this._tooltipController=new A(this),this._tooltipController.setShouldShow((e=>!e.opened)),this._tooltipController.setPosition("top"),this.addController(this._tooltipController)}_inputElementChanged(e){super._inputElementChanged(e),e&&this.$.comboBox._setInputElement(e)}open(){this.disabled||this.readonly||(this.opened=!0)}close(){this.opened=!1}checkValidity(){return!(!this.inputElement.checkValidity()||this.value&&!this._timeAllowed(this.i18n.parseTime(this.value))||this._comboBoxValue&&!this.i18n.parseTime(this._comboBoxValue))}_setFocused(e){super._setFocused(e),e||this.validate()}__validDayDivisor(e){return!e||86400%e==0||e<1&&e%1*1e3%1==0}_onKeyDown(e){if(super._onKeyDown(e),this.readonly||this.disabled||this.__dropdownItems.length)return;const t=this.__validDayDivisor(this.step)&&this.step||60;40===e.keyCode?this.__onArrowPressWithStep(-t):38===e.keyCode&&this.__onArrowPressWithStep(t)}_onEscape(){}__onArrowPressWithStep(e){const t=this.__addStep(this.__getMsec(this.__memoValue),e,!0);this.__memoValue=t,this.inputElement.value=this.i18n.formatTime(this.__validateTime(t)),this.__dispatchChange()}__dispatchChange(){this.dispatchEvent(new CustomEvent("change",{bubbles:!0}))}__getMsec(e){let t=60*(e&&e.hours||0)*60*1e3;return t+=60*(e&&e.minutes||0)*1e3,t+=1e3*(e&&e.seconds||0),t+=e&&parseInt(e.milliseconds)||0,t}__getSec(e){let t=60*(e&&e.hours||0)*60;return t+=60*(e&&e.minutes||0),t+=e&&e.seconds||0,t+=e&&e.milliseconds/1e3||0,t}__addStep(e,t,i){0===e&&t<0&&(e=864e5);const s=1e3*t,o=e%s;s<0&&o&&i?e-=o:s>0&&o&&i?e-=o-s:e+=s;const n=Math.floor(e/1e3/60/60);e-=1e3*n*60*60;const a=Math.floor(e/1e3/60);e-=1e3*a*60;const r=Math.floor(e/1e3);return{hours:n<24?n:0,minutes:a,seconds:r,milliseconds:e-=1e3*r}}__updateDropdownItems(e,t,i,s){const o=this.__validateTime(this.__parseISO(t||Vt)),n=this.__getSec(o),a=this.__validateTime(this.__parseISO(i||Lt)),r=this.__getSec(a);if(this.__dropdownItems=this.__generateDropdownList(n,r,s),s!==this.__oldStep){this.__oldStep=s;const e=this.__validateTime(this.__parseISO(this.value));this.__updateValue(e)}this.value&&(this._comboBoxValue=this.i18n.formatTime(this.i18n.parseTime(this.value)))}__generateDropdownList(e,t,i){if(i<900||!this.__validDayDivisor(i))return[];const s=[];i||(i=3600);let o=-i+e;for(;o+i>=e&&o+i<=t;){const e=this.__validateTime(this.__addStep(1e3*o,i));o+=i;const t=this.i18n.formatTime(e);s.push({label:t,value:t})}return s}_valueChanged(e,t){const i=this.__memoValue=this.__parseISO(e),s=this.__formatISO(i)||"";""===e||null===e||i?e!==s?this.value=s:this.__keepInvalidInput?delete this.__keepInvalidInput:this.__updateInputValue(i):this.value=void 0===t?"":t,this._toggleHasValue(this._hasValue)}__comboBoxValueChanged(e,t){if(""===e&&void 0===t)return;const i=this.i18n.parseTime(e),s=this.i18n.formatTime(i)||"";i?e!==s?this._comboBoxValue=s:this.__updateValue(i):(""!==e&&(this.__keepInvalidInput=!0),this.value="")}__onComboBoxChange(e){e.stopPropagation(),this.validate(),this.__dispatchChange()}__updateValue(e){const t=this.__formatISO(this.__validateTime(e))||"";this.value=t}__updateInputValue(e){const t=this.i18n.formatTime(this.__validateTime(e))||"";this._comboBoxValue=t}__validateTime(e){if(e){const t=this.__getStepSegment();e.hours=parseInt(e.hours),e.minutes=parseInt(e.minutes||0),e.seconds=t<3?void 0:parseInt(e.seconds||0),e.milliseconds=t<4?void 0:parseInt(e.milliseconds||0)}return e}__getStepSegment(){return this.step%3600==0?1:this.step%60!=0&&this.step?this.step%1==0?3:this.step<1?4:void 0:2}__formatISO(e){return Nt.properties.i18n.value().formatTime(e)}__parseISO(e){return Nt.properties.i18n.value().parseTime(e)}_timeAllowed(e){const t=this.i18n.parseTime(this.min||Vt),i=this.i18n.parseTime(this.max||Lt);return(!this.__getMsec(t)||this.__getMsec(e)>=this.__getMsec(t))&&(!this.__getMsec(i)||this.__getMsec(e)<=this.__getMsec(i))}_onClearButtonClick(){}_onChange(){}_onInput(){}}customElements.define(Nt.is,Nt);
/**
 * @license
 * Copyright (c) 2019 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const qt=c`
  :host {
    --lumo-text-field-size: var(--lumo-size-m);
    color: var(--lumo-body-text-color);
    font-size: var(--lumo-font-size-m);
    /* align with text-field height + vertical paddings */
    line-height: calc(var(--lumo-text-field-size) + 2 * var(--lumo-space-xs));
    font-family: var(--lumo-font-family);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    -webkit-tap-highlight-color: transparent;
    padding: 0;
  }

  :host::before {
    margin-top: var(--lumo-space-xs);
    height: var(--lumo-text-field-size);
    box-sizing: border-box;
    display: inline-flex;
    align-items: center;
  }

  /* align with text-field label */
  :host([has-label]) [part='label'] {
    padding-bottom: calc(0.5em - var(--lumo-space-xs));
  }

  :host(:not([has-label])) [part='label'],
  :host(:not([has-label]))::before {
    display: none;
  }

  /* align with text-field error message */
  :host([has-error-message]) [part='error-message']::before {
    height: calc(0.4em - var(--lumo-space-xs));
  }

  :host([focused]:not([readonly]):not([disabled])) [part='label'] {
    color: var(--lumo-primary-text-color);
  }

  :host(:hover:not([readonly]):not([disabled]):not([focused])) [part='label'],
  :host(:hover:not([readonly]):not([disabled]):not([focused])) [part='helper-text'] {
    color: var(--lumo-body-text-color);
  }

  /* Touch device adjustment */
  @media (pointer: coarse) {
    :host(:hover:not([readonly]):not([disabled]):not([focused])) [part='label'] {
      color: var(--lumo-secondary-text-color);
    }
  }

  /* Disabled */
  :host([disabled]) [part='label'] {
    color: var(--lumo-disabled-text-color);
    -webkit-text-fill-color: var(--lumo-disabled-text-color);
  }

  /* Small theme */
  :host([theme~='small']) {
    font-size: var(--lumo-font-size-s);
    --lumo-text-field-size: var(--lumo-size-s);
  }

  :host([theme~='small'][has-label]) [part='label'] {
    font-size: var(--lumo-font-size-xs);
  }

  :host([theme~='small'][has-label]) [part='error-message'] {
    font-size: var(--lumo-font-size-xxs);
  }

  /* When custom-field is used with components without outer margin */
  :host([theme~='whitespace'][has-label]) [part='label'] {
    padding-bottom: 0.5em;
  }
`;f("vaadin-custom-field",[ue,pe,qt],{moduleId:"lumo-custom-field"});function jt(e,t){for(;e;){if(e.properties&&e.properties[t])return e.properties[t];e=Object.getPrototypeOf(e)}}f("vaadin-date-time-picker",[c`
  ::slotted([slot='date-picker']) {
    margin-inline-end: 2px;
    --vaadin-input-field-top-end-radius: 0;
    --vaadin-input-field-bottom-end-radius: 0;
  }

  ::slotted([slot='time-picker']) {
    --vaadin-input-field-top-start-radius: 0;
    --vaadin-input-field-bottom-start-radius: 0;
  }
`,ue,pe,qt],{moduleId:"lumo-date-time-picker"}),
/**
 * @license
 * Copyright (c) 2019 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
f("vaadin-date-time-picker",he,{moduleId:"vaadin-date-time-picker"});const Ht=jt(wt,"i18n").value(),Gt=jt(Nt,"i18n").value(),Wt=Object.keys(Ht),Ut=Object.keys(Gt);class Yt extends J{constructor(e,t){super(e,`${t}-picker`,`vaadin-${t}-picker`,{initializer:(e,i)=>{i[`__${t}Picker`]=e}})}}class Kt extends(me(ae($(x(M(D)))))){static get template(){return C`
      <style>
        .vaadin-date-time-picker-container {
          --vaadin-field-default-width: auto;
        }

        .slots {
          display: flex;
          --vaadin-field-default-width: 12em;
        }

        .slots ::slotted([slot='date-picker']) {
          min-width: 0;
          flex: 1 1 auto;
        }

        .slots ::slotted([slot='time-picker']) {
          min-width: 0;
          flex: 1 1.65 auto;
        }
      </style>

      <div class="vaadin-date-time-picker-container">
        <div part="label" on-click="focus">
          <slot name="label"></slot>
          <span part="required-indicator" aria-hidden="true"></span>
        </div>

        <div class="slots">
          <slot name="date-picker" id="dateSlot"></slot>
          <slot name="time-picker" id="timeSlot"></slot>
        </div>

        <div part="helper-text">
          <slot name="helper"></slot>
        </div>

        <div part="error-message">
          <slot name="error-message"></slot>
        </div>
      </div>

      <slot name="tooltip"></slot>
    `}static get is(){return"vaadin-date-time-picker"}static get properties(){return{name:{type:String},value:{type:String,notify:!0,value:"",observer:"__valueChanged"},min:{type:String,observer:"__minChanged"},max:{type:String,observer:"__maxChanged"},__minDateTime:{type:Date,value:""},__maxDateTime:{type:Date,value:""},datePlaceholder:{type:String},timePlaceholder:{type:String},step:{type:Number},initialPosition:String,showWeekNumbers:{type:Boolean},autoOpenDisabled:Boolean,readonly:{type:Boolean,value:!1,reflectToAttribute:!0},autofocus:{type:Boolean},__selectedDateTime:{type:Date},i18n:{type:Object,value:()=>({...Ht,...Gt})},overlayClass:{type:String},__datePicker:{type:HTMLElement,observer:"__datePickerChanged"},__timePicker:{type:HTMLElement,observer:"__timePickerChanged"}}}static get observers(){return["__selectedDateTimeChanged(__selectedDateTime)","__datePlaceholderChanged(datePlaceholder, __datePicker)","__timePlaceholderChanged(timePlaceholder, __timePicker)","__stepChanged(step, __timePicker)","__initialPositionChanged(initialPosition, __datePicker)","__showWeekNumbersChanged(showWeekNumbers, __datePicker)","__requiredChanged(required, __datePicker, __timePicker)","__invalidChanged(invalid, __datePicker, __timePicker)","__disabledChanged(disabled, __datePicker, __timePicker)","__readonlyChanged(readonly, __datePicker, __timePicker)","__i18nChanged(i18n, __datePicker, __timePicker)","__autoOpenDisabledChanged(autoOpenDisabled, __datePicker, __timePicker)","__themeChanged(_theme, __datePicker, __timePicker)","__overlayClassChanged(overlayClass, __datePicker, __timePicker)","__pickersChanged(__datePicker, __timePicker)"]}constructor(){super(),this.__defaultDateMinMaxValue=void 0,this.__defaultTimeMinValue="00:00:00.000",this.__defaultTimeMaxValue="23:59:59.999",this.__changeEventHandler=this.__changeEventHandler.bind(this),this.__valueChangedEventHandler=this.__valueChangedEventHandler.bind(this)}get __inputs(){return[this.__datePicker,this.__timePicker]}get __formattedValue(){const[e,t]=this.__inputs.map((e=>e.value));return e&&t?[e,t].join("T"):""}ready(){super.ready(),this._datePickerController=new Yt(this,"date"),this.addController(this._datePickerController),this._timePickerController=new Yt(this,"time"),this.addController(this._timePickerController),this.autofocus&&!this.disabled&&window.requestAnimationFrame((()=>this.focus())),this.setAttribute("role","group"),this._tooltipController=new A(this),this.addController(this._tooltipController),this._tooltipController.setPosition("top"),this._tooltipController.setShouldShow((e=>e.__datePicker&&!e.__datePicker.opened&&e.__timePicker&&!e.__timePicker.opened)),this.ariaTarget=this}focus(){this.__datePicker.focus()}_setFocused(e){super._setFocused(e),e||this.validate()}_shouldRemoveFocus(e){const t=e.relatedTarget,i=this.__datePicker._overlayContent;return!(this.__datePicker.contains(t)||this.__timePicker.contains(t)||i&&i.contains(t))}__syncI18n(e,t,i=Object.keys(t.i18n)){i.forEach((i=>{t.i18n&&t.i18n.hasOwnProperty(i)&&e.set(`i18n.${i}`,t.i18n[i])}))}__changeEventHandler(e){e.stopPropagation(),this.__dispatchChangeForValue===this.value&&(this.__dispatchChange(),this.validate()),this.__dispatchChangeForValue=void 0}__addInputListeners(e){e.addEventListener("change",this.__changeEventHandler),e.addEventListener("value-changed",this.__valueChangedEventHandler)}__removeInputListeners(e){e.removeEventListener("change",this.__changeEventHandler),e.removeEventListener("value-changed",this.__valueChangedEventHandler)}__isDefaultPicker(e,t){const i=this[`_${t}PickerController`];return i&&e===i.defaultNode}__datePickerChanged(e,t){e&&(t&&(this.__removeInputListeners(t),t.remove()),this.__addInputListeners(e),this.__isDefaultPicker(e,"date")?(e.placeholder=this.datePlaceholder,e.invalid=this.invalid,e.initialPosition=this.initialPosition,e.showWeekNumbers=this.showWeekNumbers,this.__syncI18n(e,this,Wt)):(this.datePlaceholder=e.placeholder,this.initialPosition=e.initialPosition,this.showWeekNumbers=e.showWeekNumbers,this.__syncI18n(this,e,Wt)),e.min=this.__formatDateISO(this.__minDateTime,this.__defaultDateMinMaxValue),e.max=this.__formatDateISO(this.__maxDateTime,this.__defaultDateMinMaxValue),e.validate=()=>{},e._validateInput=()=>{})}__timePickerChanged(e,t){e&&(t&&(this.__removeInputListeners(t),t.remove()),this.__addInputListeners(e),this.__isDefaultPicker(e,"time")?(e.placeholder=this.timePlaceholder,e.step=this.step,e.invalid=this.invalid,this.__syncI18n(e,this,Ut)):(this.timePlaceholder=e.placeholder,this.step=e.step,this.__syncI18n(this,e,Ut)),this.__updateTimePickerMinMax(),e.validate=()=>{})}__updateTimePickerMinMax(){if(this.__timePicker&&this.__datePicker){const e=this.__parseDate(this.__datePicker.value),t=it(this.__minDateTime,this.__maxDateTime),i=this.__timePicker.value;this.__minDateTime&&it(e,this.__minDateTime)||t?this.__timePicker.min=this.__dateToIsoTimeString(this.__minDateTime):this.__timePicker.min=this.__defaultTimeMinValue,this.__maxDateTime&&it(e,this.__maxDateTime)||t?this.__timePicker.max=this.__dateToIsoTimeString(this.__maxDateTime):this.__timePicker.max=this.__defaultTimeMaxValue,this.__timePicker.value!==i&&(this.__timePicker.value=i)}}__i18nChanged(e,t,i){t&&(t.i18n={...t.i18n,...e}),i&&(i.i18n={...i.i18n,...e})}__datePlaceholderChanged(e,t){t&&(t.placeholder=e)}__timePlaceholderChanged(e,t){t&&(t.placeholder=e)}__stepChanged(e,t){t&&t.step!==e&&(t.step=e)}__initialPositionChanged(e,t){t&&(t.initialPosition=e)}__showWeekNumbersChanged(e,t){t&&(t.showWeekNumbers=e)}__invalidChanged(e,t,i){t&&(t.invalid=e),i&&(i.invalid=e)}__requiredChanged(e,t,i){t&&(t.required=e),i&&(i.required=e)}__disabledChanged(e,t,i){t&&(t.disabled=e),i&&(i.disabled=e)}__readonlyChanged(e,t,i){t&&(t.readonly=e),i&&(i.readonly=e)}__parseDate(e){return rt(e)}__formatDateISO(e,t){return e?wt.prototype._formatISO(e):t}__formatTimeISO(e){return Gt.formatTime(e)}__parseTimeISO(e){return Gt.parseTime(e)}__parseDateTime(e){const[t,i]=e.split("T");if(!t||!i)return;const s=this.__parseDate(t);if(!s)return;const o=this.__parseTimeISO(i);return o?(s.setHours(parseInt(o.hours)),s.setMinutes(parseInt(o.minutes||0)),s.setSeconds(parseInt(o.seconds||0)),s.setMilliseconds(parseInt(o.milliseconds||0)),s):void 0}__formatDateTime(e){if(!e)return"";return`${this.__formatDateISO(e,"")}T${this.__dateToIsoTimeString(e)}`}__dateToIsoTimeString(e){return this.__formatTimeISO(this.__validateTime({hours:e.getHours(),minutes:e.getMinutes(),seconds:e.getSeconds(),milliseconds:e.getMilliseconds()}))}__validateTime(e){if(e){const t=this.__getStepSegment();e.seconds=t<3?void 0:e.seconds,e.milliseconds=t<4?void 0:e.milliseconds}return e}checkValidity(){const e=this.__inputs.some((e=>!e.checkValidity())),t=this.required&&this.__inputs.some((e=>!e.value));return!e&&!t}__getStepSegment(){const e=null==this.step?60:parseFloat(this.step);return e%3600==0?1:e%60!=0&&e?e%1==0?3:e<1?4:void 0:2}__dateTimeEquals(e,t){return!!it(e,t)&&(e.getHours()===t.getHours()&&e.getMinutes()===t.getMinutes()&&e.getSeconds()===t.getSeconds()&&e.getMilliseconds()===t.getMilliseconds())}__handleDateTimeChange(e,t,i,s){if(!i)return this[e]="",void(this[t]="");const o=this.__parseDateTime(i);o?this.__dateTimeEquals(this[t],o)||(this[t]=o):this[e]=s}__valueChanged(e,t){this.__handleDateTimeChange("value","__selectedDateTime",e,t),void 0!==t&&(this.__dispatchChangeForValue=e),this.toggleAttribute("has-value",!!e),this.__updateTimePickerMinMax()}__dispatchChange(){this.dispatchEvent(new CustomEvent("change",{bubbles:!0}))}__minChanged(e,t){this.__handleDateTimeChange("min","__minDateTime",e,t),this.__datePicker&&(this.__datePicker.min=this.__formatDateISO(this.__minDateTime,this.__defaultDateMinMaxValue)),this.__updateTimePickerMinMax(),this.__datePicker&&this.__timePicker&&this.value&&this.validate()}__maxChanged(e,t){this.__handleDateTimeChange("max","__maxDateTime",e,t),this.__datePicker&&(this.__datePicker.max=this.__formatDateISO(this.__maxDateTime,this.__defaultDateMinMaxValue)),this.__updateTimePickerMinMax(),this.__datePicker&&this.__timePicker&&this.value&&this.validate()}__selectedDateTimeChanged(e){const t=this.__formatDateTime(e);this.value!==t&&(this.value=t);if(Boolean(this.__datePicker&&this.__datePicker.$)&&!this.__ignoreInputValueChange){this.__ignoreInputValueChange=!0;const[e,t]=this.value.split("T");this.__datePicker.value=e||"",this.__timePicker.value=t||"",this.__ignoreInputValueChange=!1}}__valueChangedEventHandler(){if(this.__ignoreInputValueChange)return;const e=this.__formattedValue,[t,i]=e.split("T");this.__ignoreInputValueChange=!0,this.__updateTimePickerMinMax(),t&&i?e!==this.value&&(this.value=e):this.value="",this.__ignoreInputValueChange=!1}__autoOpenDisabledChanged(e,t,i){t&&(t.autoOpenDisabled=e),i&&(i.autoOpenDisabled=e)}__themeChanged(e,t,i){t&&i&&[t,i].forEach((t=>{e?t.setAttribute("theme",e):t.removeAttribute("theme")}))}__overlayClassChanged(e,t,i){t&&i&&(t.overlayClass=e,i.overlayClass=e)}__pickersChanged(e,t){e&&t&&this.__isDefaultPicker(e,"date")===this.__isDefaultPicker(t,"time")&&(e.value?this.__valueChangedEventHandler():this.value&&(this.__selectedDateTimeChanged(this.__selectedDateTime),(this.min||this.max)&&this.validate()))}}customElements.define(Kt.is,Kt);let Xt=class extends u{constructor(){super(),this.is_connected=!1,this.enableLaunchButton=!1,this.hideLaunchButton=!1,this.hideEnvDialog=!1,this.enableInferenceWorkload=!1,this.location="",this.mode="normal",this.newSessionDialogTitle="",this.importScript="",this.importFilename="",this.imageRequirements=Object(),this.resourceLimits=Object(),this.userResourceLimit=Object(),this.aliases=Object(),this.tags=Object(),this.icons=Object(),this.imageInfo=Object(),this.kernel="",this.marker_limit=25,this.gpu_modes=[],this.gpu_step=.1,this.cpu_metric={min:"1",max:"1"},this.mem_metric={min:"1",max:"1"},this.shmem_metric={min:.0625,max:1,preferred:.0625},this.cuda_device_metric={min:0,max:0},this.rocm_device_metric={min:"0",max:"0"},this.tpu_device_metric={min:"1",max:"1"},this.cluster_metric={min:1,max:1},this.cluster_mode_list=["single-node","multi-node"],this.cluster_support=!1,this.folderMapping=Object(),this.customFolderMapping=Object(),this.aggregate_updating=!1,this.resourceGauge=Object(),this.sessionType="interactive",this.ownerFeatureInitialized=!1,this.ownerDomain="",this.project_resource_monitor=!1,this._default_language_updated=!1,this._default_version_updated=!1,this._helpDescription="",this._helpDescriptionTitle="",this._helpDescriptionIcon="",this.max_cpu_core_per_session=128,this.max_mem_per_container=1536,this.max_cuda_device_per_container=16,this.max_cuda_shares_per_container=16,this.max_shm_per_container=8,this.allow_manual_image_name_for_session=!1,this.cluster_size=1,this.deleteEnvInfo=Object(),this.deleteEnvRow=Object(),this.environ_values=Object(),this.vfolder_select_expansion=Object(),this.currentIndex=1,this._nonAutoMountedFolderGrid=Object(),this._modelFolderGrid=Object(),this._debug=!1,this._boundFolderToMountListRenderer=this.folderToMountListRenderer.bind(this),this._boundFolderMapRenderer=this.folderMapRenderer.bind(this),this._boundPathRenderer=this.infoHeaderRenderer.bind(this),this.useScheduledTime=!1,this.sessionInfoObj={environment:"",version:[""]},this.active=!1,this.ownerKeypairs=[],this.ownerGroups=[],this.ownerScalingGroups=[],this.resourceBroker=globalThis.resourceBroker,this.notification=globalThis.lablupNotification,this.environ=[],this.init_resource()}static get is(){return"backend-ai-session-launcher"}static get styles(){return[n,a,r,l,d,c`
        .slider-list-item {
          padding: 0;
        }

        hr.separator {
          border-top: 1px solid #ddd;
        }

        lablup-slider {
          width: 350px !important;
          --textfield-min-width: 135px;
          --slider-width: 210px;
          --mdc-theme-primary: var(--paper-green-400);
        }

        lablup-progress-bar {
          --progress-bar-width: 100%;
          --progress-bar-height: 10px;
          --progress-bar-border-radius: 0px;
          height: 100%;
          width: 100%;
          --progress-bar-background: var(--general-progress-bar-using);
          /* transition speed for progress bar */
          --progress-bar-transition-second: .1s;
          margin: 0;
        }

        vaadin-grid {
          max-height: 335px;
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
          color: #040716;
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
        .environment-variables-container
         {
          background-color: rgba(244,244,244,1);
          overflow-y: scroll;
        }

        div.vfolder-list,
        div.vfolder-mounted-list {
          max-height: 335px;
        }

        .environment-variables-container {
          font-size: 0.8rem;
          padding: 10px;
        }

        .environment-variables-container wl-textfield input {
          overflow: hidden;
          text-overflow: ellipsis;
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
          border-radius:10px;
          border:1px dotted var(--general-button-background-color);
          padding-top:10px;
          margin-left:15px;
          margin-right:15px;
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
          z-index:11;
        }

        .resource-allocated > p {
          margin: 0 auto;
          font-size: 8px;
        }
        .resource-allocated-box {
          z-index:10;
          position: relative;
        }
        .resource-allocated-box-shadow {
          position:relative;
          z-index:1;
          top: -65px;
          height:200px;
          width:70px;
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
          color: white;
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

        .resource-allocated > span,
        .cluster-allocated > div.horizontal > span {
          font-weight: bolder;
        }

        .allocation-check {
          margin-bottom: 10px;
        }

        .resource-allocated-box {
          background-color: var(--paper-grey-300);
          border-radius: 5px;
          margin: 5px;
          z-index:10;
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

        #launch-session[disabled] {
          background-image: var(--general-sidebar-color);
          --mdc-theme-on-primary: var(--general-button-color);
        }

        #launch-session-form {
          height: calc(var(--component-height, auto) - 157px);
        }

        wl-button > span {
          margin-left: 5px;
          font-weight: normal;
        }

        wl-icon {
          --icon-size: 20px;
        }

        wl-expansion {
          --font-family-serif: var(--general-font-family);
          --expansion-elevation: 0;
          --expansion-elevation-open: 0;
          --expansion-elevation-hover: 0;
          --expansion-header-padding: 16px;
          --expansion-margin-open: 0;
        }

        wl-expansion span[slot="title"] {
          font-size: 12px;
          color: rgb(64, 64, 64);
          font-weight: normal;
        }

        wl-expansion.vfolder,
        wl-expansion.editor {
          --expansion-content-padding: 0;
          border-bottom: 1px;
        }

        wl-expansion span {
          font-size: 20px;
          font-weight: 200;
          display: block;
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
          font-family: var(--general-font-family);
          --mdc-typography-subtitle1-font-family: var(--general-font-family);
          --mdc-theme-primary: var(--paper-red-600);
          --mdc-select-fill-color: transparent;
          --mdc-select-label-ink-color: rgba(0, 0, 0, 0.75);
          --mdc-select-dropdown-icon-color: rgba(255, 0, 0, 0.87);
          --mdc-select-focused-dropdown-icon-color: rgba(255, 0, 0, 0.42);
          --mdc-select-disabled-ink-color: rgba(0, 0, 0, 0.64);
          --mdc-select-disabled-dropdown-icon-color: rgba(255, 0, 0, 0.87);
          --mdc-select-disabled-fill-color: rgba(244, 244, 244, 1);
          --mdc-select-idle-line-color: rgba(0, 0, 0, 0.42);
          --mdc-select-hover-line-color: rgba(255, 0, 0, 0.87);
          --mdc-select-outlined-idle-border-color: rgba(255, 0, 0, 0.42);
          --mdc-select-outlined-hover-border-color: rgba(255, 0, 0, 0.87);
          --mdc-theme-surface: white;
          --mdc-list-vertical-padding: 5px;
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
          font-family: var(--general-font-family);
          --mdc-typography-subtitle1-font-family: var(--general-font-family);
          --mdc-text-field-idle-line-color: rgba(0, 0, 0, 0.42);
          --mdc-text-field-hover-line-color: rgba(255, 0, 0, 0.87);
          --mdc-text-field-fill-color: transparent;
          --mdc-theme-primary: var(--paper-red-600);
        }

        mwc-textfield#session-name {
          margin-bottom: 1px;
        }

        mwc-button, mwc-button[raised], mwc-button[unelevated], mwc-button[disabled] {
          width: 100%;
        }

        mwc-button[disabled] {
          background-image: none;
          --mdc-theme-primary: #ddd;
          --mdc-theme-on-primary: var(--general-sidebar-topbar-background-color);
        }

        mwc-checkbox {
          --mdc-theme-secondary: var(--general-checkbox-color);
        }

        mwc-checkbox#hide-guide {
          margin-right: 10px;
        }

        #prev-button, #next-button {
          color: #27824F;
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

        #vfolder mwc-list-item[disabled] {
          background-color: rgba(255, 0, 0, 0.04) !important;
        }

        #vfolder-header-title {
          text-align: center;
          font-size: 16px;
          font-family: var(--general-font-family);
          font-weight: 500;
        }

        wl-label {
          margin-right: 10px;
          outline: none;
        }

        #help-description {
          --component-width: 350px;
        }

        #help-description p {
          padding: 5px !important;
        }

        #launch-confirmation-dialog, #env-config-confirmation {
          --component-width: 400px;
          --component-font-size: 14px;
        }

        mwc-icon-button.info {
          --mdc-icon-button-size: 30px;
        }

        mwc-icon {
          --mdc-icon-size: 13px;
          margin-right: 2px;
          vertical-align: middle;
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

        mwc-button > mwc-icon {
          display: none;
        }

        p.title {
          padding: 15px 15px 0px;
          margin-top: 0;
          font-size: 12px;
          font-weight: 200;
          color: #404040;
        }

        #progress-04 p.title {
          font-weight: 400;
        }

        #batch-mode-config-section {
          width: 100%;
          border-bottom: solid 1px rgba(0, 0, 0, 0.42);
          margin-bottom: 15px;
        }

        .launcher-item-title {
          font-size: 14px;
          color: #404040;
          font-weight: 400;
          padding-left:16px;
          width: 100%;
        }

        .allocation-shadow {
          height: 70px;
          width: 200px;
          position: absolute;
          top: -5px;
          left: 5px;
          border: 1px solid #ccc;
        }

        #modify-env-dialog {
          --component-max-height: 550px;
          --component-width: 400px;
        }

        #modify-env-dialog div.container {
          display: flex;
          flex-direction: column;
          padding: 0px 30px;
        }

        #modify-env-dialog div.row, #modify-env-dialog div.header {
          display: grid;
          grid-template-columns: 4fr 4fr 1fr;
        }

        #modify-env-dialog div[slot="footer"] {
          display: flex;
          margin-left: auto;
          gap: 15px;
        }

        #modify-env-container mwc-textfield {
          width: 90%;
          margin: auto 5px;
          --mdc-theme-primary: var(--general-textfield-selected-color);
          --mdc-text-field-hover-line-color: transparent;
          --mdc-text-field-idle-line-color: var(--general-textfield-idle-color);
        }

        #env-add-btn {
          margin: 20px auto 10px auto;
        }

        #delete-all-button {
          --mdc-theme-primary: var(--paper-red-600);
        }

        .minus-btn {
          --mdc-icon-size: 20px;
          color: #27824F;
        }

        .environment-variables-container h4 {
          margin: 0;
        }

        .environment-variables-container wl-textfield {
          --input-font-family: var(--general-font-family);
          --input-color-disabled: #222;
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
          from {opacity: .7}
          to {opacity: 1}
        }

        @keyframes fade {
          from {opacity: .7}
          to {opacity: 1}
        }
      `]}init_resource(){this.versions=["Not Selected"],this.languages=[],this.gpu_mode="none",this.total_slot={},this.total_resource_group_slot={},this.total_project_slot={},this.used_slot={},this.used_resource_group_slot={},this.used_project_slot={},this.available_slot={},this.used_slot_percent={},this.used_resource_group_slot_percent={},this.used_project_slot_percent={},this.resource_templates=[],this.resource_templates_filtered=[],this.vfolders=[],this.selectedVfolders=[],this.nonAutoMountedVfolders=[],this.modelVfolders=[],this.autoMountedVfolders=[],this.default_language="",this.concurrency_used=0,this.concurrency_max=0,this.concurrency_limit=2,this.max_containers_per_session=1,this._status="inactive",this.cpu_request=1,this.mem_request=1,this.shmem_request=.0625,this.gpu_request=0,this.gpu_request_type="cuda.device",this.session_request=1,this.scaling_groups=[{name:""}],this.scaling_group="",this.sessions_list=[],this.metric_updating=!1,this.metadata_updating=!1,this.cluster_size=1,this.cluster_mode="single-node",this.ownerFeatureInitialized=!1,this.ownerDomain="",this.ownerKeypairs=[],this.ownerGroups=[],this.ownerScalingGroups=[]}firstUpdated(){var e,t,i,s,o,n;this.environment.addEventListener("selected",this.updateLanguage.bind(this)),this.version_selector.addEventListener("selected",(()=>{this.updateResourceAllocationPane()})),null===(e=this.shadowRoot)||void 0===e||e.querySelectorAll("wl-expansion").forEach((e=>{e.addEventListener("keydown",(e=>{e.stopPropagation()}),!0)})),this.resourceGauge=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#resource-gauges"),document.addEventListener("backend-ai-group-changed",(e=>{this._updatePageVariables(!0)})),document.addEventListener("backend-ai-resource-broker-updated",(e=>{})),!0===this.hideLaunchButton&&((null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#launch-session")).style.display="none"),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.max_cpu_core_per_session=globalThis.backendaiclient._config.maxCPUCoresPerContainer||128,this.max_mem_per_container=globalThis.backendaiclient._config.maxMemoryPerContainer||1536,this.max_cuda_device_per_container=globalThis.backendaiclient._config.maxCUDADevicesPerContainer||16,this.max_cuda_shares_per_container=globalThis.backendaiclient._config.maxCUDASharesPerContainer||16,this.max_shm_per_container=globalThis.backendaiclient._config.maxShmPerContainer||8,void 0!==globalThis.backendaiclient._config.allow_manual_image_name_for_session&&"allow_manual_image_name_for_session"in globalThis.backendaiclient._config&&""!==globalThis.backendaiclient._config.allow_manual_image_name_for_session?this.allow_manual_image_name_for_session=globalThis.backendaiclient._config.allow_manual_image_name_for_session:this.allow_manual_image_name_for_session=!1,globalThis.backendaiclient.supports("multi-container")&&(this.cluster_support=!0),this.is_connected=!0,this._debug=globalThis.backendaiwebui.debug,this._enableLaunchButton()}),{once:!0}):(this.max_cpu_core_per_session=globalThis.backendaiclient._config.maxCPUCoresPerContainer||128,this.max_mem_per_container=globalThis.backendaiclient._config.maxMemoryPerContainer||1536,this.max_cuda_device_per_container=globalThis.backendaiclient._config.maxCUDADevicesPerContainer||16,this.max_cuda_shares_per_container=globalThis.backendaiclient._config.maxCUDASharesPerContainer||16,this.max_shm_per_container=globalThis.backendaiclient._config.maxShmPerContainer||8,void 0!==globalThis.backendaiclient._config.allow_manual_image_name_for_session&&"allow_manual_image_name_for_session"in globalThis.backendaiclient._config&&""!==globalThis.backendaiclient._config.allow_manual_image_name_for_session?this.allow_manual_image_name_for_session=globalThis.backendaiclient._config.allow_manual_image_name_for_session:this.allow_manual_image_name_for_session=!1,globalThis.backendaiclient.supports("multi-container")&&(this.cluster_support=!0),this.is_connected=!0,this._debug=globalThis.backendaiwebui.debug,this._enableLaunchButton()),this.modifyEnvDialog.addEventListener("dialog-closing-confirm",(e=>{var t;const i={},s=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#modify-env-container"),o=null==s?void 0:s.querySelectorAll(".row");Array.prototype.filter.call(o,(e=>(e=>Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>0===e.value.length)).length<=1)(e))).map((e=>(e=>{const t=Array.prototype.map.call(e.querySelectorAll("mwc-textfield"),(e=>e.value));return i[t[0]]=t[1],t})(e)));((e,t)=>{const i=Object.getOwnPropertyNames(e),s=Object.getOwnPropertyNames(t);if(i.length!=s.length)return!1;for(let s=0;s<i.length;s++){const o=i[s];if(e[o]!==t[o])return!1}return!0})(i,this.environ_values)?(this.modifyEnvDialog.closeWithConfirmation=!1,this.closeDialog("modify-env-dialog")):(this.hideEnvDialog=!0,this.openDialog("env-config-confirmation"))})),this.currentIndex=1,this.progressLength=null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelectorAll(".progress").length,this._nonAutoMountedFolderGrid=null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("#non-auto-mounted-folder-grid"),this._modelFolderGrid=null===(n=this.shadowRoot)||void 0===n?void 0:n.querySelector("#model-folder-grid"),globalThis.addEventListener("resize",(()=>{document.body.dispatchEvent(new Event("click"))}))}_enableLaunchButton(){this.resourceBroker.image_updating?(this.enableLaunchButton=!1,setTimeout((()=>{this._enableLaunchButton()}),1e3)):("inference"===this.mode?this.languages=this.resourceBroker.languages.filter((e=>""!==e.name&&"INFERENCE"===this.resourceBroker.imageRoles[e.name])):this.languages=this.resourceBroker.languages.filter((e=>""===e.name||"COMPUTE"===this.resourceBroker.imageRoles[e.name])),this.enableLaunchButton=!0)}_updateSelectedScalingGroup(){this.scaling_groups=this.resourceBroker.scaling_groups;const e=this.scalingGroups.items.find((e=>e.value===this.resourceBroker.scaling_group));if(""===this.resourceBroker.scaling_group||void 0===e)return void setTimeout((()=>{this._updateSelectedScalingGroup()}),500);const t=this.scalingGroups.items.indexOf(e);this.scalingGroups.select(-1),this.scalingGroups.select(t),this.scalingGroups.value=e.value,this.scalingGroups.requestUpdate()}async updateScalingGroup(e=!1,t){this.active&&(await this.resourceBroker.updateScalingGroup(e,t.target.value),!0===e?await this._refreshResourcePolicy():this.updateResourceAllocationPane("session dialog"))}_initializeFolderMapping(){var e;this.folderMapping={};(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll(".alias")).forEach((e=>{e.value=""}))}async _updateSelectedFolder(e=!1){var t,i,s;if(this._nonAutoMountedFolderGrid&&this._nonAutoMountedFolderGrid.selectedItems){let o=this._nonAutoMountedFolderGrid.selectedItems;o=o.concat(this._modelFolderGrid.selectedItems);let n=[];o.length>0&&(n=o.map((e=>e.name)),e&&this._unselectAllSelectedFolder()),this.selectedVfolders=n;for(const e of this.selectedVfolders){if((null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#vfolder-alias-"+e)).value.length>0&&(this.folderMapping[e]=(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#vfolder-alias-"+e)).value),e in this.folderMapping&&this.selectedVfolders.includes(this.folderMapping[e]))return delete this.folderMapping[e],(null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#vfolder-alias-"+e)).value="",await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!0)}}return Promise.resolve(!0)}_unselectAllSelectedFolder(){[this._nonAutoMountedFolderGrid,this._modelFolderGrid].forEach((e=>{e&&e.selectedItems&&(e.selectedItems.forEach((e=>{e.selected=!1})),e.selectedItems=[])})),this.selectedVfolders=[]}_checkSelectedItems(){[this._nonAutoMountedFolderGrid,this._modelFolderGrid].forEach((e=>{if(e&&e.selectedItems){const t=e.selectedItems;let i=[];t.length>0&&(e.selectedItems=[],i=t.map((e=>null==e?void 0:e.id)),e.querySelectorAll("vaadin-checkbox").forEach((e=>{var t;i.includes(null===(t=e.__item)||void 0===t?void 0:t.id)&&(e.checked=!0)})))}}))}_preProcessingSessionInfo(){var e,t;let i,s;if(null===(e=this.manualImageName)||void 0===e?void 0:e.value){const e=this.manualImageName.value.split(":");i=e[0],s=e.slice(-1)[0].split("-")}else{if(void 0===this.kernel||!1!==(null===(t=this.version_selector)||void 0===t?void 0:t.disabled))return!1;i=this.kernel,s=this.version_selector.selectedText.split("/")}return this.sessionInfoObj.environment=i.split("/").pop(),this.sessionInfoObj.version=[s[0].toUpperCase()].concat(1!==s.length?s.slice(1).map((e=>e.toUpperCase())):[""]),!0}async _viewStateChanged(e){if(await this.updateComplete,!this.active)return;const t=()=>{this.enableInferenceWorkload=globalThis.backendaiclient.supports("inference-workload")};void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.project_resource_monitor=this.resourceBroker.allow_project_resource_monitor,this._updatePageVariables(!0),this._disableEnterKey(),t()}),{once:!0}):(this.project_resource_monitor=this.resourceBroker.allow_project_resource_monitor,await this._updatePageVariables(!0),this._disableEnterKey(),t())}async _updatePageVariables(e){this.active&&!1===this.metadata_updating&&(this.metadata_updating=!0,await this.resourceBroker._updatePageVariables(e),this._updateSelectedScalingGroup(),this.sessions_list=this.resourceBroker.sessions_list,await this._refreshResourcePolicy(),this.aggregateResource("update-page-variable"),this.metadata_updating=!1)}async _refreshResourcePolicy(){return this.resourceBroker._refreshResourcePolicy().then((()=>{var e;this.concurrency_used=this.resourceBroker.concurrency_used,this.userResourceLimit=this.resourceBroker.userResourceLimit,this.concurrency_max=this.resourceBroker.concurrency_max,this.max_containers_per_session=null!==(e=this.resourceBroker.max_containers_per_session)&&void 0!==e?e:1,this.gpu_mode=this.resourceBroker.gpu_mode,this.gpu_step=this.resourceBroker.gpu_step,this.gpu_modes=this.resourceBroker.gpu_modes,this.updateResourceAllocationPane("refresh resource policy")})).catch((e=>{this.metadata_updating=!1,e&&e.message?(this.notification.text=p.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=p.relieve(e.title),this.notification.show(!0,e))}))}async _launchSessionDialog(){var e;if(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready||!0===this.resourceBroker.image_updating)setTimeout((()=>{this._launchSessionDialog()}),1e3);else{this.folderMapping=Object(),this._resetProgress(),await this.selectDefaultLanguage();const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector('wl-expansion[name="ownership"]');globalThis.backendaiclient.is_admin?t.style.display="block":t.style.display="none",this._updateSelectedScalingGroup(),await this._refreshResourcePolicy(),this.requestUpdate(),this._toggleScheduleTime(!this.useScheduledTime),this.newSessionDialog.show()}}_generateKernelIndex(e,t){return e+":"+t}_moveToLastProgress(){this.moveProgress(4)}_newSessionWithConfirmation(){var e,t;const i=null===(t=null===(e=this._nonAutoMountedFolderGrid)||void 0===e?void 0:e.selectedItems)||void 0===t?void 0:t.map((e=>e.name)).length;if(this.currentIndex==this.progressLength){if("inference"===this.mode||void 0!==i&&i>0)return this._newSession();this.launchConfirmationDialog.show()}else this._moveToLastProgress()}_newSession(){var e,t,i,s,o,n,a,r,l,d,c,h;let u,_,v;if(this.launchConfirmationDialog.hide(),this.manualImageName&&this.manualImageName.value){const e=this.manualImageName.value.split(":");_=e.splice(-1,1)[0],u=e.join(":")}else{const n=this.environment.selected;u=null!==(e=null==n?void 0:n.id)&&void 0!==e?e:"",_=null!==(i=null===(t=this.version_selector.selected)||void 0===t?void 0:t.value)&&void 0!==i?i:"",v=null!==(o=null===(s=this.version_selector.selected)||void 0===s?void 0:s.getAttribute("architecture"))&&void 0!==o?o:void 0}this.sessionType=(null===(n=this.shadowRoot)||void 0===n?void 0:n.querySelector("#session-type")).value;let g=(null===(a=this.shadowRoot)||void 0===a?void 0:a.querySelector("#session-name")).value;const f=(null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector("#session-name")).checkValidity();let y=this.selectedVfolders;if(this.cpu_request=parseInt(this.cpuResouceSlider.value),this.mem_request=parseFloat(this.memoryResouceSlider.value),this.shmem_request=parseFloat(this.sharedMemoryResouceSlider.value),this.gpu_request=parseFloat(this.gpuResouceSlider.value),this.session_request=parseInt(this.sessionResouceSlider.value),this.num_sessions=this.session_request,this.sessions_list.includes(g))return this.notification.text=m("session.launcher.DuplicatedSessionName"),void this.notification.show();if(!f)return this.notification.text=m("session.launcher.SessionNameAllowCondition"),void this.notification.show();if(""===u||""===_||"Not Selected"===_)return this.notification.text=m("session.launcher.MustSpecifyVersion"),void this.notification.show();this.scaling_group=this.scalingGroups.value;const b={};b.group_name=globalThis.backendaiclient.current_group,b.domain=globalThis.backendaiclient._config.domainName,b.scaling_group=this.scaling_group,b.type=this.sessionType,globalThis.backendaiclient.supports("multi-container")&&(b.cluster_mode=this.cluster_mode,b.cluster_size=this.cluster_size),b.maxWaitSeconds=15;const x=null===(l=this.shadowRoot)||void 0===l?void 0:l.querySelector("#owner-enabled");if(x&&x.checked&&(b.group_name=this.ownerGroupSelect.value,b.domain=this.ownerDomain,b.scaling_group=this.ownerScalingGroupSelect.value,b.owner_access_key=this.ownerAccesskeySelect.value,!(b.group_name&&b.domain&&b.scaling_group&&b.owner_access_key)))return this.notification.text=m("session.launcher.NotEnoughOwnershipInfo"),void this.notification.show();switch(b.cpu=this.cpu_request,this.gpu_request_type){case"cuda.shares":b["cuda.shares"]=this.gpu_request;break;case"cuda.device":b["cuda.device"]=this.gpu_request;break;case"rocm.device":b["rocm.device"]=this.gpu_request;break;case"tpu.device":b["tpu.device"]=this.gpu_request;break;default:this.gpu_request>0&&this.gpu_mode&&(b[this.gpu_mode]=this.gpu_request)}let w;"Infinity"===String(this.memoryResouceSlider.value)?b.mem=String(this.memoryResouceSlider.value):b.mem=String(this.mem_request)+"g",this.shmem_request>this.mem_request&&(this.shmem_request=this.mem_request,this.notification.text=m("session.launcher.SharedMemorySettingIsReduced"),this.notification.show()),this.mem_request>4&&this.shmem_request<1&&(this.shmem_request=1),b.shmem=String(this.shmem_request)+"g",0==g.length&&(g=this.generateSessionId()),w=this._debug&&""!==this.manualImageName.value||this.manualImageName&&""!==this.manualImageName.value?this.manualImageName.value:this._generateKernelIndex(u,_);let k={};if("inference"===this.mode){if(!(w in this.resourceBroker.imageRuntimeConfig)||!("model-path"in this.resourceBroker.imageRuntimeConfig[w]))return this.notification.text=m("session.launcher.ImageDoesNotProvideModelPath"),void this.notification.show();y=Object.keys(this.customFolderMapping),k[y]=this.resourceBroker.imageRuntimeConfig[w]["model-path"]}else k=this.folderMapping;if(console.log("folder mapping:",k),0!==y.length&&(b.mounts=y,0!==Object.keys(k).length)){b.mount_map={};for(const e in k)({}).hasOwnProperty.call(k,e)&&(k[e].startsWith("/")?b.mount_map[e]=k[e]:b.mount_map[e]="/home/work/"+k[e])}if("import"===this.mode&&""!==this.importScript&&(b.bootstrap_script=this.importScript),"batch"===this.sessionType){const e=null===(d=this.shadowRoot)||void 0===d?void 0:d.querySelector("#command-editor");b.startupCommand=e.getValue();const t=this.dateTimePicker.value,i=this.useScheduledTimeSwitch.selected;if(t&&i){const e=()=>{let e=(new Date).getTimezoneOffset();const t=e<0?"+":"-";return e=Math.abs(e),t+(e/60|0).toString().padStart(2,"0")+":"+(e%60).toString().padStart(2,"0")};b.startsAt=t+e()}}if(this.environ_values&&0!==Object.keys(this.environ_values).length&&(b.env=this.environ_values),!1===this.openMPSwitch.selected){const e=(null===(c=this.shadowRoot)||void 0===c?void 0:c.querySelector("#OpenMPCore")).value,t=(null===(h=this.shadowRoot)||void 0===h?void 0:h.querySelector("#OpenBLASCore")).value;b.env.OMP_NUM_THREADS=e?Math.max(0,parseInt(e)).toString():"1",b.env.OPENBLAS_NUM_THREADS=t?Math.max(0,parseInt(t)).toString():"1"}this.launchButton.disabled=!0,this.launchButtonMessage.textContent=m("session.Preparing"),this.notification.text=m("session.PreparingSession"),this.notification.show();const D=[],C=this._getRandomString();if(this.num_sessions>1)for(let e=1;e<=this.num_sessions;e++){const t={kernelName:w,sessionName:`${g}-${C}-${e}`,architecture:v,config:b};D.push(t)}else D.push({kernelName:w,sessionName:g,architecture:v,config:b});const S=D.map((e=>this.tasker.add("Creating "+e.sessionName,this._createKernel(e.kernelName,e.sessionName,e.architecture,e.config),"","session")));Promise.all(S).then((e=>{this.newSessionDialog.hide(),this.launchButton.disabled=!1,this.launchButtonMessage.textContent=m("session.launcher.ConfirmAndLaunch"),this._resetProgress(),setTimeout((()=>{this.metadata_updating=!0,this.aggregateResource("session-creation"),this.metadata_updating=!1}),1500);const t=new CustomEvent("backend-ai-session-list-refreshed",{detail:"running"});document.dispatchEvent(t),1===e.length&&"batch"!==this.sessionType&&e[0].taskobj.then((e=>{let t;t="kernelId"in e?{"session-name":e.kernelId,"access-key":"",mode:this.mode}:{"session-uuid":e.sessionId,"session-name":e.sessionName,"access-key":"",mode:this.mode};const i=e.servicePorts;!0===Array.isArray(i)?t["app-services"]=i.map((e=>e.name)):t["app-services"]=[],"import"===this.mode&&(t.runtime="jupyter",t.filename=this.importFilename),"inference"===this.mode&&(t.runtime=t["app-services"].find((e=>!["ttyd","sshd"].includes(e)))),i.length>0&&globalThis.appLauncher.showLauncher(t)})).catch((e=>{})),this._updateSelectedFolder(!1),this._initializeFolderMapping()})).catch((e=>{e&&e.message?(this.notification.text=p.relieve(e.message),e.description?this.notification.text=p.relieve(e.description):this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=p.relieve(e.title),this.notification.show(!0,e));const t=new CustomEvent("backend-ai-session-list-refreshed",{detail:"running"});document.dispatchEvent(t),this.launchButton.disabled=!1,this.launchButtonMessage.textContent=m("session.launcher.ConfirmAndLaunch")}))}_getRandomString(){let e=Math.floor(52*Math.random()*52*52);let t="";for(let s=0;s<3;s++)t+=(i=e%52)<26?String.fromCharCode(65+i):String.fromCharCode(97+i-26),e=Math.floor(e/52);var i;return t}_createKernel(e,t,i,s){const o=globalThis.backendaiclient.createIfNotExists(e,t,s,2e4,i);return o.catch((e=>{e&&e.message?("statusCode"in e&&408===e.statusCode?this.notification.text=m("session.launcher.sessionStillPreparing"):e.description?this.notification.text=p.relieve(e.description):this.notification.text=p.relieve(e.message),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=p.relieve(e.title),this.notification.show(!0,e))})),o}_hideSessionDialog(){this.newSessionDialog.hide()}_aliasName(e){const t=this.resourceBroker.imageTagAlias,i=this.resourceBroker.imageTagReplace;for(const[t,s]of Object.entries(i)){const i=new RegExp(t);if(i.test(e))return e.replace(i,s)}return e in t?t[e]:e}_updateVersions(e){if(e in this.resourceBroker.supports){{this.version_selector.disabled=!0;const t=[];for(const i of this.resourceBroker.supports[e])for(const s of this.resourceBroker.imageArchitectures[e+":"+i])t.push({version:i,architecture:s});t.sort(((e,t)=>e.version>t.version?1:-1)),t.reverse(),this.versions=t,this.kernel=e}return void 0!==this.versions?this.version_selector.layout(!0).then((()=>{this.version_selector.select(1),this.version_selector.value=this.versions[0].version,this.version_selector.architecture=this.versions[0].architecture,this._updateVersionSelectorText(this.version_selector.value,this.version_selector.architecture),this.version_selector.disabled=!1,this.environ_values={},this.updateResourceAllocationPane("update versions")})):void 0}}_updateVersionSelectorText(e,t){const i=this._getVersionInfo(e,t),s=[];i.forEach((e=>{s.push(e.tag)})),this.version_selector.selectedText=s.join(" / ")}generateSessionId(){let e="";const t="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";for(let i=0;i<8;i++)e+=t.charAt(Math.floor(Math.random()*t.length));return e+"-session"}async _updateVirtualFolderList(){return this.resourceBroker.updateVirtualFolderList().then((()=>{this.vfolders=this.resourceBroker.vfolders}))}async _aggregateResourceUse(e=""){return this.resourceBroker._aggregateCurrentResource(e).then((async e=>(this.concurrency_used=this.resourceBroker.concurrency_used,this.scaling_group=this.resourceBroker.scaling_group,this.scaling_groups=this.resourceBroker.scaling_groups,this.resource_templates=this.resourceBroker.resource_templates,this.resource_templates_filtered=this.resourceBroker.resource_templates_filtered,this.total_slot=this.resourceBroker.total_slot,this.total_resource_group_slot=this.resourceBroker.total_resource_group_slot,this.total_project_slot=this.resourceBroker.total_project_slot,this.used_slot=this.resourceBroker.used_slot,this.used_resource_group_slot=this.resourceBroker.used_resource_group_slot,this.used_project_slot=this.resourceBroker.used_project_slot,this.used_project_slot_percent=this.resourceBroker.used_project_slot_percent,this.concurrency_limit=this.resourceBroker.concurrency_limit&&this.resourceBroker.concurrency_limit>1?this.resourceBroker.concurrency_limit:1,this.available_slot=this.resourceBroker.available_slot,this.used_slot_percent=this.resourceBroker.used_slot_percent,this.used_resource_group_slot_percent=this.resourceBroker.used_resource_group_slot_percent,await this.updateComplete,Promise.resolve(!0)))).catch((e=>(e&&e.message&&(e.description?this.notification.text=p.relieve(e.description):this.notification.text=p.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)),Promise.resolve(!1))))}aggregateResource(e=""){void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._aggregateResourceUse(e)}),!0):this._aggregateResourceUse(e)}async updateResourceAllocationPane(e=""){var t,i;if(1==this.metric_updating)return;if("refresh resource policy"===e)return this.metric_updating=!1,this._aggregateResourceUse("update-metric").then((()=>this.updateResourceAllocationPane("after refresh resource policy")));const s=this.environment.selected,o=this.version_selector.selected;if(null===o)return void(this.metric_updating=!1);const n=o.value,a=o.getAttribute("architecture");if(this._updateVersionSelectorText(n,a),null==s||s.getAttribute("disabled"))this.metric_updating=!1;else if(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready)document.addEventListener("backend-ai-connected",(()=>{this.updateResourceAllocationPane(e)}),!0);else{this.metric_updating=!0;let e=!1;if(!0===globalThis.backendaiclient._config.always_enqueue_compute_session&&(e=!0),await this._aggregateResourceUse("update-metric"),await this._updateVirtualFolderList(),this.autoMountedVfolders=this.vfolders.filter((e=>e.name.startsWith("."))),this.enableInferenceWorkload?(this.modelVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")&&"model"===e.usage_mode)),this.nonAutoMountedVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")&&"general"===e.usage_mode))):this.nonAutoMountedVfolders=this.vfolders.filter((e=>!e.name.startsWith("."))),0===Object.keys(this.resourceBroker.resourceLimits).length)return void(this.metric_updating=!1);const o=s.id,a=n;if(""===o||""===a)return void(this.metric_updating=!1);const r=o+":"+a,l=this.resourceBroker.resourceLimits[r];if(!l)return void(this.metric_updating=!1);this.gpu_mode=this.resourceBroker.gpu_mode,this.gpu_step=this.resourceBroker.gpu_step,this.gpu_modes=this.resourceBroker.gpu_modes,globalThis.backendaiclient.supports("multi-container")&&this.cluster_size>1&&(this.gpu_step=1);const d=this.resourceBroker.available_slot;this.cpuResouceSlider.disabled=!1,this.memoryResouceSlider.disabled=!1,this.gpuResouceSlider.disabled=!1,globalThis.backendaiclient.supports("multi-container")&&(this.cluster_size=1,this.clusterSizeSlider.value=this.cluster_size),this.sessionResouceSlider.disabled=!1,this.launchButton.disabled=!1,this.launchButtonMessage.textContent=m("session.launcher.ConfirmAndLaunch");let c=!1,h={min:.0625,max:2,preferred:.0625};if(this.cuda_device_metric={min:0,max:0},l.forEach((t=>{if("cpu"===t.key){const i={...t};i.min=parseInt(i.min),e&&["cpu","mem","cuda_device","cuda_shares","rocm_device","tpu_device"].forEach((e=>{e in this.total_resource_group_slot&&(d[e]=this.total_resource_group_slot[e])})),"cpu"in this.userResourceLimit?0===parseInt(i.max)||"Infinity"===i.max||isNaN(i.max)||null===i.max?i.max=Math.min(parseInt(this.userResourceLimit.cpu),d.cpu,this.max_cpu_core_per_session):i.max=Math.min(parseInt(i.max),parseInt(this.userResourceLimit.cpu),d.cpu,this.max_cpu_core_per_session):0===parseInt(i.max)||"Infinity"===i.max||isNaN(i.max)||null===i.max?i.max=Math.min(this.available_slot.cpu,this.max_cpu_core_per_session):i.max=Math.min(parseInt(i.max),d.cpu,this.max_cpu_core_per_session),i.min>=i.max&&(i.min>i.max&&(i.min=i.max,c=!0),this.cpuResouceSlider.disabled=!0),this.cpu_metric=i,this.cluster_support&&"single-node"===this.cluster_mode&&(this.cluster_metric.max=Math.min(i.max,this.max_containers_per_session),this.cluster_metric.min>this.cluster_metric.max?this.cluster_metric.min=this.cluster_metric.max:this.cluster_metric.min=i.min)}if("cuda.device"===t.key&&"cuda.device"==this.gpu_mode){const e={...t};e.min=parseInt(e.min),"cuda.device"in this.userResourceLimit?0===parseInt(e.max)||"Infinity"===e.max||isNaN(e.max)||null==e.max?e.max=Math.min(parseInt(this.userResourceLimit["cuda.device"]),parseInt(d.cuda_device),this.max_cuda_device_per_container):e.max=Math.min(parseInt(e.max),parseInt(this.userResourceLimit["cuda.device"]),d.cuda_device,this.max_cuda_device_per_container):0===parseInt(e.max)||"Infinity"===e.max||isNaN(e.max)||null==e.max?e.max=Math.min(parseInt(this.available_slot.cuda_device),this.max_cuda_device_per_container):e.max=Math.min(parseInt(e.max),parseInt(d.cuda_device),this.max_cuda_device_per_container),e.min>=e.max&&(e.min>e.max&&(e.min=e.max,c=!0),this.gpuResouceSlider.disabled=!0),this.cuda_device_metric=e}if("cuda.shares"===t.key&&"cuda.shares"===this.gpu_mode){const e={...t};e.min=parseFloat(e.min),"cuda.shares"in this.userResourceLimit?0===parseFloat(e.max)||"Infinity"===e.max||isNaN(e.max)||null==e.max?e.max=Math.min(parseFloat(this.userResourceLimit["cuda.shares"]),parseFloat(d.cuda_shares),this.max_cuda_shares_per_container):e.max=Math.min(parseFloat(e.max),parseFloat(this.userResourceLimit["cuda.shares"]),parseFloat(d.cuda_shares),this.max_cuda_shares_per_container):0===parseFloat(e.max)||"Infinity"===e.max||isNaN(e.max)||null==e.max?e.max=Math.min(parseFloat(d.cuda_shares),this.max_cuda_shares_per_container):e.max=Math.min(parseFloat(e.max),parseFloat(d.cuda_shares),this.max_cuda_shares_per_container),e.min>=e.max&&(e.min>e.max&&(e.min=e.max,c=!0),this.gpuResouceSlider.disabled=!0),this.cuda_shares_metric=e,e.max>0&&(this.cuda_device_metric=e)}if("rocm.device"===t.key&&"rocm.device"===this.gpu_mode){const e={...t};e.min=parseInt(e.min),e.max=parseInt(e.max),e.min,e.max,this.rocm_device_metric=e}if("tpu.device"===t.key){const e={...t};e.min=parseInt(e.min),e.max=parseInt(e.max),e.min,e.max,this.tpu_device_metric=e}if("mem"===t.key){const e={...t};e.min=globalThis.backendaiclient.utils.changeBinaryUnit(e.min,"g"),e.min<.1&&(e.min=.1),e.max||(e.max=0);const i=globalThis.backendaiclient.utils.changeBinaryUnit(e.max,"g","g");if("mem"in this.userResourceLimit){const t=globalThis.backendaiclient.utils.changeBinaryUnit(this.userResourceLimit.mem,"g");isNaN(parseInt(i))||0===parseInt(i)?e.max=Math.min(parseFloat(t),d.mem,this.max_mem_per_container):e.max=Math.min(parseFloat(i),parseFloat(t),d.mem,this.max_mem_per_container)}else 0!==parseInt(e.max)&&"Infinity"!==e.max&&!0!==isNaN(e.max)?e.max=Math.min(parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(e.max,"g","g")),d.mem,this.max_mem_per_container):e.max=Math.min(d.mem,this.max_mem_per_container);e.min>=e.max&&(e.min>e.max&&(e.min=e.max,c=!0),this.memoryResouceSlider.disabled=!0),e.min=Number(e.min.toFixed(2)),e.max=Number(e.max.toFixed(2)),this.mem_metric=e}"shmem"===t.key&&(h={...t},h.preferred="preferred"in h?globalThis.backendaiclient.utils.changeBinaryUnit(h.preferred,"g","g"):.0625)})),h.max=this.max_shm_per_container,h.min=.0625,h.min>=h.max&&(h.min>h.max&&(h.min=h.max,c=!0),this.sharedMemoryResouceSlider.disabled=!0),h.min=Number(h.min.toFixed(2)),h.max=Number(h.max.toFixed(2)),this.shmem_metric=h,0==this.cuda_device_metric.min&&0==this.cuda_device_metric.max)if(this.gpuResouceSlider.disabled=!0,this.gpuResouceSlider.value=0,this.resource_templates.length>0){const e=[];for(let t=0;t<this.resource_templates.length;t++)"cuda_device"in this.resource_templates[t]||"cuda_shares"in this.resource_templates[t]?(parseFloat(this.resource_templates[t].cuda_device)<=0&&!("cuda_shares"in this.resource_templates[t])||parseFloat(this.resource_templates[t].cuda_shares)<=0&&!("cuda_device"in this.resource_templates[t])||parseFloat(this.resource_templates[t].cuda_device)<=0&&parseFloat(this.resource_templates[t].cuda_shares)<=0)&&e.push(this.resource_templates[t]):e.push(this.resource_templates[t]);this.resource_templates_filtered=e}else this.resource_templates_filtered=this.resource_templates;else this.gpuResouceSlider.disabled=!1,this.gpuResouceSlider.value=this.cuda_device_metric.max,this.resource_templates_filtered=this.resource_templates;if(this.resource_templates_filtered.length>0){const e=this.resource_templates_filtered[0];this._chooseResourceTemplate(e),this.resourceTemplatesSelect.layout(!0).then((()=>this.resourceTemplatesSelect.layoutOptions())).then((()=>{this.resourceTemplatesSelect.select(1)}))}else this._updateResourceIndicator(this.cpu_metric.min,this.mem_metric.min,"none",0);c?(this.cpuResouceSlider.disabled=!0,this.memoryResouceSlider.disabled=!0,this.gpuResouceSlider.disabled=!0,this.sessionResouceSlider.disabled=!0,this.sharedMemoryResouceSlider.disabled=!0,this.launchButton.disabled=!0,(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector(".allocation-check")).style.display="none",this.cluster_support&&(this.clusterSizeSlider.disabled=!0),this.launchButtonMessage.textContent=m("session.launcher.NotEnoughResource")):(this.cpuResouceSlider.disabled=!1,this.memoryResouceSlider.disabled=!1,this.gpuResouceSlider.disabled=!1,this.sessionResouceSlider.disabled=!1,this.sharedMemoryResouceSlider.disabled=!1,this.launchButton.disabled=!1,(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector(".allocation-check")).style.display="flex",this.cluster_support&&(this.clusterSizeSlider.disabled=!1)),this.cuda_device_metric.min==this.cuda_device_metric.max&&this.cuda_device_metric.max<1&&(this.gpuResouceSlider.disabled=!0),this.concurrency_limit<=1&&(this.sessionResouceSlider.min=1,this.sessionResouceSlider.max=2,this.sessionResouceSlider.value=1,this.sessionResouceSlider.disabled=!0),this.max_containers_per_session<=1&&"single-node"===this.cluster_mode&&(this.clusterSizeSlider.min=1,this.clusterSizeSlider.max=2,this.clusterSizeSlider.value=1,this.clusterSizeSlider.disabled=!0),this.metric_updating=!1}}updateLanguage(){const e=this.environment.selected;if(null===e)return;const t=e.id;this._updateVersions(t)}folderToMountListRenderer(e,t,i){_(h`
          <div style="font-size:14px;text-overflow:ellipsis;overflow:hidden;">${i.item.name}</div>
          <span style="font-size:10px;">${i.item.host}</span>
        `,e)}folderMapRenderer(e,t,i){_(h`
          <vaadin-text-field id="vfolder-alias-${i.item.name}" class="alias" clear-button-visible prevent-invalid-input
                             pattern="^[a-zA-Z0-9\./_-]*$" ?disabled="${!i.selected}"
                             theme="small" placeholder="/home/work/${i.item.name}"
                             @change="${e=>this._updateFolderMap(i.item.name,e.target.value)}"></vaadin-text-field>
        `,e)}infoHeaderRenderer(e,t){_(h`
          <div class="horizontal layout center">
            <span id="vfolder-header-title">${v("session.launcher.FolderAlias")}</span>
            <mwc-icon-button icon="info" class="fg green info" @click="${e=>this._showPathDescription(e)}"></mwc-icon-button>
          </div>
        `,e)}_showPathDescription(e){null!=e&&e.stopPropagation(),this._helpDescriptionTitle=m("session.launcher.FolderAlias"),this._helpDescription=m("session.launcher.DescFolderAlias"),this._helpDescriptionIcon="",this.helpDescriptionDialog.show()}helpDescTagCount(e){let t=0;let i=e.indexOf(e);for(;-1!==i;)t++,i=e.indexOf("<p>",i+1);return t}setPathContent(e,t){var i;const s=e.children[e.children.length-1],o=s.children[s.children.length-1];if(o.children.length<t+1){const e=document.createElement("div");e.setAttribute("class","horizontal layout flex center");const t=document.createElement("mwc-checkbox");t.setAttribute("id","hide-guide");const s=document.createElement("span");s.innerHTML=`${m("dialog.hide.DonotShowThisAgain")}`,e.appendChild(t),e.appendChild(s),o.appendChild(e);const n=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#hide-guide");null==n||n.addEventListener("change",(e=>{if(null!==e.target){e.stopPropagation();e.target.checked?localStorage.setItem("backendaiwebui.pathguide","false"):localStorage.setItem("backendaiwebui.pathguide","true")}}))}}async _updateFolderMap(e,t){var i,s;if(""===t)return e in this.folderMapping&&delete this.folderMapping[e],await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!0);if(e!==t){if(this.selectedVfolders.includes(t))return this.notification.text=m("session.launcher.FolderAliasOverlapping"),this.notification.show(),delete this.folderMapping[e],(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#vfolder-alias-"+e)).value="",await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!1);for(const i in this.folderMapping)if({}.hasOwnProperty.call(this.folderMapping,i)&&this.folderMapping[i]==t)return this.notification.text=m("session.launcher.FolderAliasOverlapping"),this.notification.show(),delete this.folderMapping[e],(null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#vfolder-alias-"+e)).value="",await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!1);return this.folderMapping[e]=t,await this.vfolderMountPreview.updateComplete.then((()=>this.requestUpdate())),Promise.resolve(!0)}return Promise.resolve(!0)}changed(e){console.log(e)}isEmpty(e){return 0===e.length}_toggleAdvancedSettings(){var e;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#advanced-resource-settings")).toggle()}_setClusterMode(e){this.cluster_mode=e.target.value}_setClusterSize(e){this.cluster_size=e.target.value>0?Math.round(e.target.value):0,this.clusterSizeSlider.value=this.cluster_size;let t=1;globalThis.backendaiclient.supports("multi-container")&&(this.cluster_size>1||(t=0),this.gpu_step=this.resourceBroker.gpu_step,this._setSessionLimit(t))}_setSessionLimit(e=1){e>0?(this.sessionResouceSlider.value=e,this.session_request=e,this.sessionResouceSlider.disabled=!0):(this.sessionResouceSlider.max=this.concurrency_limit,this.sessionResouceSlider.disabled=!1)}_chooseResourceTemplate(e){var t;let i;i=void 0!==(null==e?void 0:e.cpu)?e:null===(t=e.target)||void 0===t?void 0:t.closest("mwc-list-item");const s=i.cpu,o=i.mem,n=i.cuda_device,a=i.cuda_shares,r=i.rocm_device,l=i.tpu_device;let d,c;void 0!==n||void 0!==a?void 0===n?(d="cuda.shares",c=a):(d="cuda.device",c=n):void 0!==r?(d="rocm.device",c=r):void 0!==l?(d="tpu.device",c=l):(d="none",c=0);const h=i.shmem?i.shmem:this.shmem_metric;this.shmem_request="number"!=typeof h?h.preferred:h||.0625,this._updateResourceIndicator(s,o,d,c)}_updateResourceIndicator(e,t,i,s){this.cpuResouceSlider.value=e,this.memoryResouceSlider.value=t,this.gpuResouceSlider.value=s,this.sharedMemoryResouceSlider.value=this.shmem_request,this.cpu_request=e,this.mem_request=t,this.gpu_request=s,this.gpu_request_type=i}async selectDefaultLanguage(e=!1,t=""){if(!0===this._default_language_updated&&!1===e)return;""!==t?this.default_language=t:void 0!==globalThis.backendaiclient._config.default_session_environment&&"default_session_environment"in globalThis.backendaiclient._config&&""!==globalThis.backendaiclient._config.default_session_environment?this.languages.map((e=>e.name)).includes(globalThis.backendaiclient._config.default_session_environment)?this.default_language=globalThis.backendaiclient._config.default_session_environment:""!==this.languages[0].name?this.default_language=this.languages[0].name:this.default_language=this.languages[1].name:this.languages.length>1?this.default_language=this.languages[1].name:0!==this.languages.length?this.default_language=this.languages[0].name:this.default_language="index.docker.io/lablup/ngc-tensorflow";const i=this.environment.items.find((e=>e.value===this.default_language));if(void 0===i&&void 0!==globalThis.backendaiclient&&!1===globalThis.backendaiclient.ready)return setTimeout((()=>(console.log("Environment selector is not ready yet. Trying to set the default language again."),this.selectDefaultLanguage(e,t))),500),Promise.resolve(!0);const s=this.environment.items.indexOf(i);return this.environment.select(s),this._default_language_updated=!0,Promise.resolve(!0)}_selectDefaultVersion(e){return!1}async _fetchSessionOwnerGroups(){var e;this.ownerFeatureInitialized||(this.ownerGroupSelect.addEventListener("selected",this._fetchSessionOwnerScalingGroups.bind(this)),this.ownerFeatureInitialized=!0);const t=this.ownerEmailInput.value;if(!this.ownerEmailInput.checkValidity())return this.notification.text=m("credential.validation.InvalidEmailAddress"),this.notification.show(),this.ownerKeypairs=[],void(this.ownerGroups=[]);const i=await globalThis.backendaiclient.keypair.list(t,["access_key"]),s=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#owner-enabled");if(this.ownerKeypairs=i.keypairs,this.ownerKeypairs.length<1)return this.notification.text=m("session.launcher.NoActiveKeypair"),this.notification.show(),s.checked=!1,s.disabled=!0,this.ownerKeypairs=[],void(this.ownerGroups=[]);this.ownerAccesskeySelect.layout(!0).then((()=>{this.ownerAccesskeySelect.select(0),this.ownerAccesskeySelect.createAdapter().setSelectedText(this.ownerKeypairs[0].access_key)}));const o=await globalThis.backendaiclient.user.get(t,["domain_name","groups {id name}"]);this.ownerDomain=o.user.domain_name,this.ownerGroups=o.user.groups,this.ownerGroups&&this.ownerGroupSelect.layout(!0).then((()=>{this.ownerGroupSelect.select(0),this.ownerGroupSelect.createAdapter().setSelectedText(this.ownerGroups[0].name)})),s.disabled=!1}async _fetchSessionOwnerScalingGroups(){const e=this.ownerGroupSelect.value;if(!e)return void(this.ownerScalingGroups=[]);const t=await globalThis.backendaiclient.scalingGroup.list(e);this.ownerScalingGroups=t.scaling_groups,this.ownerScalingGroups&&this.ownerScalingGroupSelect.layout(!0).then((()=>{this.ownerScalingGroupSelect.select(0),this.ownerGroupSelect.createAdapter().setSelectedText(this.ownerScalingGroups[0].name)}))}async _fetchDelegatedSessionVfolder(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#owner-enabled"),i=this.ownerEmailInput.value;this.ownerKeypairs.length>0&&t&&t.checked?(await this.resourceBroker.updateVirtualFolderList(i),this.vfolders=this.resourceBroker.vfolders):await this._updateVirtualFolderList(),this.autoMountedVfolders=this.vfolders.filter((e=>e.name.startsWith("."))),this.enableInferenceWorkload?(this.modelVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")&&"model"===e.usage_mode)),this.nonAutoMountedVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")&&"general"===e.usage_mode))):this.nonAutoMountedVfolders=this.vfolders.filter((e=>!e.name.startsWith(".")))}_toggleResourceGauge(){""==this.resourceGauge.style.display||"flex"==this.resourceGauge.style.display||"block"==this.resourceGauge.style.display?this.resourceGauge.style.display="none":(document.body.clientWidth<750?(this.resourceGauge.style.left="20px",this.resourceGauge.style.right="20px",this.resourceGauge.style.backgroundColor="var(--paper-red-800)"):this.resourceGauge.style.backgroundColor="transparent",this.resourceGauge.style.display="flex")}_showKernelDescription(e,t){e.stopPropagation();const i=t.kernelname;i in this.resourceBroker.imageInfo&&"description"in this.resourceBroker.imageInfo[i]?(this._helpDescriptionTitle=this.resourceBroker.imageInfo[i].name,this._helpDescription=this.resourceBroker.imageInfo[i].description||m("session.launcher.NoDescriptionFound"),this._helpDescriptionIcon=t.icon,this.helpDescriptionDialog.show()):(i in this.imageInfo?this._helpDescriptionTitle=this.resourceBroker.imageInfo[i].name:this._helpDescriptionTitle=i,this._helpDescription=m("session.launcher.NoDescriptionFound"))}_showResourceDescription(e,t){e.stopPropagation();const i={cpu:{name:m("session.launcher.CPU"),desc:m("session.launcher.DescCPU")},mem:{name:m("session.launcher.Memory"),desc:m("session.launcher.DescMemory")},shmem:{name:m("session.launcher.SharedMemory"),desc:m("session.launcher.DescSharedMemory")},gpu:{name:m("session.launcher.GPU"),desc:m("session.launcher.DescGPU")},session:{name:m("session.launcher.TitleSession"),desc:m("session.launcher.DescSession")},"single-node":{name:m("session.launcher.SingleNode"),desc:m("session.launcher.DescSingleNode")},"multi-node":{name:m("session.launcher.MultiNode"),desc:m("session.launcher.DescMultiNode")},"openmp-optimization":{name:m("session.launcher.OpenMPOptimization"),desc:m("session.launcher.DescOpenMPOptimization")}};t in i&&(this._helpDescriptionTitle=i[t].name,this._helpDescription=i[t].desc,this._helpDescriptionIcon="",this.helpDescriptionDialog.show())}_showEnvConfigDescription(e){e.stopPropagation(),this._helpDescriptionTitle=m("session.launcher.EnvironmentVariableTitle"),this._helpDescription=m("session.launcher.DescSetEnv"),this._helpDescriptionIcon="",this.helpDescriptionDialog.show()}_resourceTemplateToCustom(){this.resourceTemplatesSelect.selectedText=m("session.launcher.CustomResourceApplied")}_applyResourceValueChanges(e,t=!0){const i=e.target.value;switch(e.target.id.split("-")[0]){case"cpu":this.cpu_request=i;break;case"mem":this.mem_request=i;break;case"shmem":this.shmem_request=i;break;case"gpu":this.gpu_request=i;break;case"session":this.session_request=i;break;case"cluster":this._changeTotalAllocationPane()}this.requestUpdate(),t?this._resourceTemplateToCustom():this._setClusterSize(e)}_changeTotalAllocationPane(){var e,t;this._deleteAllocationPaneShadow();const i=this.clusterSizeSlider.value;if(i>1){const s=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#resource-allocated-box-shadow");for(let e=0;e<Math.min(6,i-1);e+=1){const t=document.createElement("div");t.classList.add("horizontal","layout","center","center-justified","resource-allocated-box","allocation-shadow"),t.style.position="absolute",t.style.top="-"+(5+5*e)+"px",t.style.left=5+5*e+"px";const i=245+2*e;t.style.backgroundColor="rgb("+i+","+i+","+i+")",t.style.borderColor="rgb("+(i-10)+","+(i-10)+","+(i-10)+")",t.style.zIndex=(6-e).toString(),s.appendChild(t)}(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#total-allocation-pane")).appendChild(s)}}_deleteAllocationPaneShadow(){var e;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#resource-allocated-box-shadow")).innerHTML=""}_updateShmemLimit(){const e=parseFloat(this.memoryResouceSlider.value);let t=this.sharedMemoryResouceSlider.value;parseFloat(t)>e?(t=e,this.shmem_request=t,this.sharedMemoryResouceSlider.value=t,this.sharedMemoryResouceSlider.max=t,this.notification.text=m("session.launcher.SharedMemorySettingIsReduced"),this.notification.show()):this.max_shm_per_container>t&&(this.sharedMemoryResouceSlider.max=e>this.max_shm_per_container?this.max_shm_per_container:e)}_roundResourceAllocation(e,t){return parseFloat(e).toFixed(t)}_conditionalGBtoMB(e){return e<1?this._roundResourceAllocation((1024*e).toFixed(0),2):this._roundResourceAllocation(e,2)}_conditionalGBtoMBunit(e){return e<1?"MB":"GB"}_getVersionInfo(e,t){const i=[],s=e.split("-");if(i.push({tag:this._aliasName(s[0]),color:"blue",size:"60px"}),s.length>1&&(this.kernel+":"+e in this.imageRequirements&&"framework"in this.imageRequirements[this.kernel+":"+e]?i.push({tag:this.imageRequirements[this.kernel+":"+e].framework,color:"red",size:"110px"}):i.push({tag:this._aliasName(s[1]),color:"red",size:"110px"})),i.push({tag:t,color:"lightgreen",size:"90px"}),s.length>2){let e=this._aliasName(s.slice(2).join("-"));e=e.split(":"),e.length>1?i.push({tag:e.slice(1).join(":"),app:e[0],color:"green",size:"110px"}):i.push({tag:e[0],color:"green",size:"110px"})}return i}_disableEnterKey(){var e;null===(e=this.shadowRoot)||void 0===e||e.querySelectorAll("wl-expansion").forEach((e=>{e.onKeyDown=e=>{13===e.keyCode&&e.preventDefault()}}))}_validateInput(e){const t=e.target.closest("mwc-textfield");t.value&&(t.value=Math.round(t.value),t.value=globalThis.backendaiclient.utils.clamp(t.value,t.min,t.max))}_appendEnvRow(e="",t=""){var i;const s=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#modify-env-container"),o=null==s?void 0:s.children[s.children.length-1],n=this._createEnvRow(e,t);null==s||s.insertBefore(n,o)}_createEnvRow(e="",t=""){const i=document.createElement("div");i.setAttribute("class","horizontal layout center row");const s=document.createElement("mwc-textfield");s.setAttribute("value",e);const o=document.createElement("mwc-textfield");o.setAttribute("value",t);const n=document.createElement("mwc-icon-button");return n.setAttribute("icon","remove"),n.setAttribute("class","green minus-btn"),n.addEventListener("click",(e=>this._removeEnvItem(e))),i.append(s),i.append(o),i.append(n),i}_removeEnvItem(e){this.deleteEnvRow=e.target.parentNode,this.deleteEnvRow.remove()}_removeEmptyEnv(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#modify-env-container"),i=null==t?void 0:t.querySelectorAll(".row");Array.prototype.filter.call(i,(e=>(e=>2===Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>""===e.value)).length)(e))).map(((e,t)=>{(0!==t||this.environ.length>0)&&e.parentNode.removeChild(e)}))}modifyEnv(){this._parseEnvVariableList(),this._saveEnvVariableList(),this.modifyEnvDialog.closeWithConfirmation=!1,this.modifyEnvDialog.hide(),this.notification.text=m("session.launcher.EnvironmentVariableConfigurationDone"),this.notification.show()}_loadEnv(){this.environ.forEach((e=>{this._appendEnvRow(e.name,e.value)}))}_showEnvDialog(){this._removeEmptyEnv(),this.modifyEnvDialog.closeWithConfirmation=!0,this.modifyEnvDialog.show()}_closeAndResetEnvInput(){this._clearRows(!0),this.closeDialog("env-config-confirmation"),this.hideEnvDialog&&(this._loadEnv(),this.modifyEnvDialog.closeWithConfirmation=!1,this.modifyEnvDialog.hide())}_parseEnvVariableList(){var e;this.environ_values={};const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#modify-env-container"),i=null==t?void 0:t.querySelectorAll(".row:not(.header)"),s=e=>{const t=Array.prototype.map.call(e.querySelectorAll("mwc-textfield"),(e=>e.value));return this.environ_values[t[0]]=t[1],t};Array.prototype.filter.call(i,(e=>(e=>0===Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>0===e.value.length)).length)(e))).map((e=>s(e)))}_saveEnvVariableList(){this.environ=Object.entries(this.environ_values).map((([e,t])=>({name:e,value:t})))}_resetEnvironmentVariables(){this.environ=[],this.environ_values={},null!==this.modifyEnvDialog&&this._clearRows(!0)}_clearRows(e=!1){var t;const i=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#modify-env-container"),s=null==i?void 0:i.querySelectorAll(".row"),o=s[0];if(!e){const e=e=>Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),(e=>e.value.length>0)).length>0;if(Array.prototype.filter.call(s,(t=>e(t))).length>0)return this.hideEnvDialog=!1,void this.openDialog("env-config-confirmation")}null==o||o.querySelectorAll("mwc-textfield").forEach((e=>{e.value=""})),s.forEach(((e,t)=>{0!==t&&e.remove()}))}openDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).show()}closeDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).hide()}async moveProgress(e){var t,i,s,o;const n=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#progress-0"+this.currentIndex);this.currentIndex+=e,"inference"===this.mode&&2==this.currentIndex&&(this.currentIndex+=e),this.currentIndex>this.progressLength&&(this.currentIndex=globalThis.backendaiclient.utils.clamp(this.currentIndex+e,this.progressLength,1));const a=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#progress-0"+this.currentIndex);n.classList.remove("active"),a.classList.add("active"),this.prevButton.style.visibility=1==this.currentIndex?"hidden":"visible",this.nextButton.style.visibility=this.currentIndex==this.progressLength?"hidden":"visible",this.launchButton.disabled||(this.launchButtonMessage.textContent=this.progressLength==this.currentIndex?m("session.launcher.Launch"):m("session.launcher.ConfirmAndLaunch")),null===(s=this._nonAutoMountedFolderGrid)||void 0===s||s.clearCache(),null===(o=this._modelFolderGrid)||void 0===o||o.clearCache(),2===this.currentIndex&&(await this._fetchDelegatedSessionVfolder(),this._checkSelectedItems())}_resetProgress(){this.moveProgress(1-this.currentIndex),this._resetEnvironmentVariables(),this._unselectAllSelectedFolder()}_calculateProgress(){const e=this.progressLength>0?this.progressLength:1;return((this.currentIndex>0?this.currentIndex:1)/e).toFixed(2)}_toggleEnvironmentSelectUI(){var e;const t=!!(null===(e=this.manualImageName)||void 0===e?void 0:e.value);this.environment.disabled=this.version_selector.disabled=t;const i=t?-1:1;this.environment.select(i),this.version_selector.select(i)}_toggleHPCOptimization(){var e;const t=this.openMPSwitch.selected;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#HPCOptimizationOptions")).style.display=t?"none":"block"}_toggleStartUpCommandEditor(e){var t,i;this.sessionType=e.target.value;const s="batch"===this.sessionType;if((null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#batch-mode-config-section")).style.display=s?"inline-flex":"none",s){const e=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#command-editor");e.refresh(),e.focus()}}_toggleScheduleTimeDisplay(){this.useScheduledTime=this.useScheduledTimeSwitch.selected,this.dateTimePicker.style.display=this.useScheduledTime?"block":"none",this._toggleScheduleTime(!this.useScheduledTime)}_toggleScheduleTime(e=!1){e?clearInterval(this.schedulerTimer):this.schedulerTimer=setInterval((()=>{this._getSchedulableTime()}),1e3)}_getSchedulableTime(){const e=e=>e.getFullYear()+"-"+(e.getMonth()+1)+"-"+e.getDate()+"T"+e.getHours()+":"+e.getMinutes()+":"+e.getSeconds();let t=new Date;const i=12e4;let s=new Date(t.getTime()+i);if(this.dateTimePicker.min=e(t),this.dateTimePicker.value&&""!==this.dateTimePicker.value){const o=new Date(this.dateTimePicker.value).getTime();t=new Date,o<=t.getTime()&&(s=new Date(t.getTime()+i),this.dateTimePicker.value=e(s))}else this.dateTimePicker.value=e(s);this._setRelativeTimeStamp()}_setRelativeTimeStamp(){var e,t;const i={year:31536e6,month:2628e6,day:864e5,hour:36e5,minute:6e4,second:1e3},s=null!==(e=globalThis.backendaioptions.get("current_language"))&&void 0!==e?e:"en",o=new Intl.RelativeTimeFormat(s,{numeric:"auto"});(null===(t=this.dateTimePicker)||void 0===t?void 0:t.invalid)?this.dateTimePicker.helperText=m("session.launcher.ResetStartTime"):this.dateTimePicker.helperText=m("session.launcher.SessionStartTime")+((e,t=+new Date)=>{const s=e-t;for(const e in i)if(Math.abs(s)>i[e]||"second"==e){const t=e;return o.format(Math.round(s/i[e]),t)}return m("session.launcher.InfiniteTime")})(+new Date(this.dateTimePicker.value))}render(){var e,t;return h`
      <link rel="stylesheet" href="resources/fonts/font-awesome-all.min.css">
      <link rel="stylesheet" href="resources/custom.css">
      <wl-button raised class="primary-action" id="launch-session" ?disabled="${!this.enableLaunchButton}"
                 @click="${()=>this._launchSessionDialog()}">
        <wl-icon>power_settings_new</wl-icon>
        <span>${v("session.launcher.Start")}</span>
      </wl-button>
      <backend-ai-dialog id="new-session-dialog" narrowLayout fixed backdrop persistent @dialog-closed="${()=>this._toggleScheduleTime(!0)}">
        <span slot="title">${this.newSessionDialogTitle?this.newSessionDialogTitle:v("session.launcher.StartNewSession")}</span>
        <form slot="content" id="launch-session-form" class="centered" style="position:relative;">
          <div id="progress-01" class="progress center layout fade active">
            <mwc-select id="session-type" icon="category" label="${m("session.launcher.SessionType")}" required fixedMenuPosition
                        value="${this.sessionType}" @selected="${e=>this._toggleStartUpCommandEditor(e)}">
              ${"inference"===this.mode?h`
              <mwc-list-item value="inference" selected>
                ${v("session.launcher.InferenceMode")}
              </mwc-list-item>
              `:h`
              <mwc-list-item value="batch">
                ${v("session.launcher.BatchMode")}
              </mwc-list-item>
              <mwc-list-item value="interactive" selected>
                ${v("session.launcher.InteractiveMode")}
              </mwc-list-item>
              `}
            </mwc-select>
            <mwc-select id="environment" icon="code" label="${m("session.launcher.Environments")}" required fixedMenuPosition
                        value="${this.default_language}">
              <mwc-list-item selected graphic="icon" style="display:none!important;">
                ${v("session.launcher.ChooseEnvironment")}
              </mwc-list-item>
              ${this.languages.map((e=>h`
                ${!1===e.clickable?h`
                  <h5 style="font-size:12px;padding: 0 10px 3px 10px;margin:0; border-bottom:1px solid #ccc;"
                      role="separator" disabled="true">${e.basename}</h5>
                `:h`
                  <mwc-list-item id="${e.name}" value="${e.name}" graphic="icon">
                    <img slot="graphic" alt="language icon" src="resources/icons/${e.icon}"
                         style="width:24px;height:24px;"/>
                    <div class="horizontal justified center flex layout" style="width:325px;">
                      <div style="padding-right:5px;">${e.basename}</div>
                      <div class="horizontal layout end-justified center flex">
                        ${e.tags?e.tags.map((e=>h`
                          <lablup-shields style="margin-right:5px;" color="${e.color}"
                                          description="${e.tag}"></lablup-shields>
                        `)):""}
                        <mwc-icon-button icon="info"
                                         class="fg blue info"
                                         @click="${t=>this._showKernelDescription(t,e)}">
                        </mwc-icon-button>
                      </div>
                    </div>
                  </mwc-list-item>
                `}
              `))}
            </mwc-select>
            <mwc-select id="version" icon="architecture" label="${m("session.launcher.Version")}" required fixedMenuPosition>
              <mwc-list-item selected style="display:none!important"></mwc-list-item>
              <h5 style="font-size:12px;padding: 0 10px 3px 15px;margin:0; border-bottom:1px solid #ccc;"
                  role="separator" disabled="true" class="horizontal layout">
                  <div style="width:60px;">${v("session.launcher.Version")}</div>
                  <div style="width:110px;">${v("session.launcher.Base")}</div>
                  <div style="width:90px;">${v("session.launcher.Architecture")}</div>
                <div style="width:110px;">${v("session.launcher.Requirements")}</div>
              </h5>
              ${this.versions.map((({version:e,architecture:t})=>h`
                <mwc-list-item id="${e}" architecture="${t}" value="${e}" style="min-height:35px;height:auto;">
                    <span style="display:none">${e}</span>
                    <div class="horizontal layout end-justified">
                    ${this._getVersionInfo(e||"",t).map((e=>h`
                      <lablup-shields style="width:${e.size}!important;"
                                      color="${e.color}"
                                      app="${void 0!==e.app&&""!=e.app&&" "!=e.app?e.app:""}"
                                      description="${e.tag}"
                                      class="horizontal layout center center-justified">
                      </lablup-shields>
                    `))}
                  </div>
                </mwc-list-item>
              `))}
            </mwc-select>
            ${this._debug||this.allow_manual_image_name_for_session?h`
              <mwc-textfield id="image-name" type="text" class="flex" value="" icon="assignment_turned_in"
                label="${m("session.launcher.ManualImageName")}"
                @change=${e=>this._toggleEnvironmentSelectUI()}></mwc-textfield>
            `:h``}
            <mwc-textfield id="session-name" placeholder="${m("session.launcher.SessionNameOptional")}"
                           pattern="[a-zA-Z0-9_-]{4,}" maxLength="64" icon="label"
                           helper="${m("maxLength.64chars")}"
                           validationMessage="${m("session.launcher.SessionNameAllowCondition")}">
            </mwc-textfield>
            <div class="vertical layout center flex" id="batch-mode-config-section" style="display:none;">
              <span class="launcher-item-title" style="width:386px;">${v("session.launcher.BatchModeConfig")}</span>
              <div class="horizontal layout start-justified">
                <div style="width:370px;font-size:12px;">${v("session.launcher.StartUpCommand")}</div>
              </div>
              <lablup-codemirror id="command-editor" mode="shell"></lablup-codemirror>
              <div class="horizontal center layout justified" style="margin: 10px auto;">
                <div style="width:330px;font-size:12px;">${v("session.launcher.ScheduleTime")}</div>
                <mwc-switch id="use-scheduled-time" @click="${()=>this._toggleScheduleTimeDisplay()}"></mwc-switch>
              </div>
              <vaadin-date-time-picker step="1"
                                       date-placeholder="DD/MM/YYYY"
                                       time-placeholder="hh:mm:ss"
                                       ?required="${this.useScheduledTime}"
                                       @change="${this._getSchedulableTime}"
                                       style="display:none;"></vaadin-date-time-picker>
            </div>
            <div class="horizontal layout center justified">
              <span class="launcher-item-title">${v("session.launcher.SetEnvironmentVariable")}</span>
              <mwc-button
                unelevated
                icon="rule"
                label="${m("session.launcher.Config")}"
                style="width:auto;margin-right:15px;"
                @click="${()=>this._showEnvDialog()}"></mwc-button>
            </div>
            <div class="environment-variables-container" style="margin-top:18px;">
              ${this.environ.length>0?h`
                <div class="horizontal flex center center-justified layout" style="overflow-x:hidden;">
                  <div role="listbox">
                    <h4>${m("session.launcher.EnvironmentVariable")}</h4>
                    ${this.environ.map((e=>h`
                      <wl-textfield disabled value="${e.name}"></wl-textfield>
                    `))}
                  </div>
                  <div role="listbox" style="margin-left:15px;">
                    <h4>${m("session.launcher.EnvironmentVariableValue")}</h4>
                    ${this.environ.map((e=>h`
                      <wl-textfield disabled value="${e.value}"></wl-textfield>
                    `))}
                  </div>
                </div>
              `:h`
                <div class="vertical layout center flex blank-box">
                  <span>${v("session.launcher.NoEnvConfigured")}</span>
                </div>
              `}
            </div>
            <wl-expansion name="ownership" style="--expansion-content-padding:15px 0;">
              <span slot="title">${v("session.launcher.SetSessionOwner")}</span>
              <div class="vertical layout">
                <div class="horizontal center layout">
                  <mwc-textfield id="owner-email" type="email" class="flex" value=""
                                pattern="^.+@.+\..+$" icon="mail"
                                label="${m("session.launcher.OwnerEmail")}" size="40"></mwc-textfield>
                  <mwc-icon-button icon="refresh" class="blue"
                                  @click="${()=>this._fetchSessionOwnerGroups()}">
                  </mwc-icon-button>
                </div>
                <mwc-select id="owner-accesskey" label="${m("session.launcher.OwnerAccessKey")}" icon="vpn_key" fixedMenuPosition naturalMenuWidth>
                  ${this.ownerKeypairs.map((e=>h`
                    <mwc-list-item class="owner-group-dropdown"
                                  id="${e.access_key}"
                                  value="${e.access_key}">
                      ${e.access_key}
                    </mwc-list-item>
                  `))}
                </mwc-select>
                <div class="horizontal center layout">
                  <mwc-select id="owner-group" label="${m("session.launcher.OwnerGroup")}" icon="group_work" fixedMenuPosition naturalMenuWidth>
                    ${this.ownerGroups.map((e=>h`
                      <mwc-list-item class="owner-group-dropdown"
                                    id="${e.name}"
                                    value="${e.name}">
                        ${e.name}
                      </mwc-list-item>
                    `))}
                  </mwc-select>
                  <mwc-select id="owner-scaling-group" label="${m("session.launcher.OwnerResourceGroup")}"
                              icon="storage" fixedMenuPosition>
                    ${this.ownerScalingGroups.map((e=>h`
                      <mwc-list-item class="owner-group-dropdown"
                                    id="${e.name}"
                                    value="${e.name}">
                        ${e.name}
                      </mwc-list-item>
                    `))}
                  </mwc-select>
                </div>
                <div class="horizontal layout start-justified center">
                <mwc-checkbox id="owner-enabled"></mwc-checkbox>
                <p style="color: rgba(0,0,0,0.6);">${v("session.launcher.LaunchSessionWithAccessKey")}</p>
                </div>
              </div>
            </wl-expansion>
          </div>
          <div id="progress-02" class="progress center layout fade" style="padding-top:0;">
          <wl-expansion class="vfolder" name="vfolder" open>
            <span slot="title">${v("session.launcher.FolderToMount")}</span>
            <div class="vfolder-list">
              <vaadin-grid
                  theme="row-stripes column-borders compact"
                  id="non-auto-mounted-folder-grid"
                  aria-label="vfolder list"
                  height-by-rows
                  .items="${this.nonAutoMountedVfolders}"
                  @selected-items-changed="${()=>this._updateSelectedFolder()}">
                <vaadin-grid-selection-column id="select-column"
                                              flex-grow="0"
                                              text-align="center"
                                              auto-select></vaadin-grid-selection-column>
                <vaadin-grid-filter-column header="${v("session.launcher.FolderToMountList")}"
                                           path="name" resizable
                                           .renderer="${this._boundFolderToMountListRenderer}"></vaadin-grid-filter-column>
                <vaadin-grid-column width="135px"
                                    path=" ${v("session.launcher.FolderAlias")}"
                                    .renderer="${this._boundFolderMapRenderer}"
                                    .headerRenderer="${this._boundPathRenderer}"></vaadin-grid-column>
              </vaadin-grid>
              ${this.vfolders.length>0?h``:h`
                <div class="vertical layout center flex blank-box-medium">
                  <span>${v("session.launcher.NoAvailableFolderToMount")}</span>
                </div>
              `}
            </div>
            </wl-expansion>
            <wl-expansion class="vfolder" name="vfolder" style="display:${this.enableInferenceWorkload?"block":"none"};">
              <span slot="title">${v("session.launcher.ModelStorageToMount")}</span>
              <div class="vfolder-list">
                <vaadin-grid
                  theme="row-stripes column-borders compact"
                  id="model-folder-grid"
                  aria-label="model storage vfolder list"
                  height-by-rows
                  .items="${this.modelVfolders}"
                  @selected-items-changed="${()=>this._updateSelectedFolder()}">
                  <vaadin-grid-selection-column id="select-column"
                                                flex-grow="0"
                                                text-align="center"
                                                auto-select></vaadin-grid-selection-column>
                  <vaadin-grid-filter-column header="${v("session.launcher.ModelStorageToMount")}"
                                             path="name" resizable
                                             .renderer="${this._boundFolderToMountListRenderer}"></vaadin-grid-filter-column>
                  <vaadin-grid-column width="135px"
                                      path=" ${v("session.launcher.FolderAlias")}"
                                      .renderer="${this._boundFolderMapRenderer}"
                                      .headerRenderer="${this._boundPathRenderer}"></vaadin-grid-column>
                </vaadin-grid>
              </div>
            </wl-expansion>
            <wl-expansion id="vfolder-mount-preview" class="vfolder" name="vfolder">
              <span slot="title">${v("session.launcher.MountedFolders")}</span>
              <div class="vfolder-mounted-list">
              ${this.selectedVfolders.length>0||this.autoMountedVfolders.length>0?h`
                <ul class="vfolder-list">
                    ${this.selectedVfolders.map((e=>h`
                      <li><mwc-icon>folder_open</mwc-icon>${e}
                      ${e in this.folderMapping?this.folderMapping[e].startsWith("/")?h` (&#10140; ${this.folderMapping[e]})`:h`(&#10140; /home/work/${this.folderMapping[e]})`:h`(&#10140; /home/work/${e})`}
                      </li>
                    `))}
                    ${this.autoMountedVfolders.map((e=>h`
                      <li><mwc-icon>folder_special</mwc-icon>${e.name}</li>
                    `))}
                </ul>
              `:h`
                <div class="vertical layout center flex blank-box-large">
                  <span>${v("session.launcher.NoFolderMounted")}</span>
                </div>
              `}
              </div>
            </wl-expansion>
          </div>
          <div id="progress-03" class="progress center layout fade">
            <div class="horizontal center layout">
              <mwc-select id="scaling-groups" label="${m("session.launcher.ResourceGroup")}"
                          icon="storage" required fixedMenuPosition
                          @selected="${e=>this.updateScalingGroup(!1,e)}">
                ${this.scaling_groups.map((e=>h`
                  <mwc-list-item class="scaling-group-dropdown"
                                 id="${e.name}" graphic="icon"
                                 value="${e.name}">
                    ${e.name}
                  </mwc-list-item>
                `))}
              </mwc-select>
            </div>
            <div class="vertical center layout" style="position:relative;">
              <mwc-select id="resource-templates" label="${this.isEmpty(this.resource_templates_filtered)?"":m("session.launcher.ResourceAllocation")}"
                          icon="dashboard_customize" ?required="${!this.isEmpty(this.resource_templates_filtered)}" fixedMenuPosition>
                <mwc-list-item ?selected="${this.isEmpty(this.resource_templates_filtered)}" style="display:none!important;"></mwc-list-item>
                <h5 style="font-size:12px;padding: 0 10px 3px 15px;margin:0; border-bottom:1px solid #ccc;"
                    role="separator" disabled="true" class="horizontal layout center">
                  <div style="width:110px;">Name</div>
                  <div style="width:50px;text-align:right;">CPU</div>
                  <div style="width:50px;text-align:right;">RAM</div>
                  <div style="width:50px;text-align:right;">${v("session.launcher.SharedMemory")}</div>
                  <div style="width:90px;text-align:right;">${v("session.launcher.Accelerator")}</div>
                </h5>
                ${this.resource_templates_filtered.map((e=>h`
                  <mwc-list-item value="${e.name}"
                            id="${e.name}-button"
                            @click="${e=>this._chooseResourceTemplate(e)}"
                            .cpu="${e.cpu}"
                            .mem="${e.mem}"
                            .cuda_device="${e.cuda_device}"
                            .cuda_shares="${e.cuda_shares}"
                            .rocm_device="${e.rocm_device}"
                            .tpu_device="${e.tpu_device}"
                            .shmem="${e.shmem}">
                    <div class="horizontal layout end-justified">
                      <div style="width:110px;">${e.name}</div>
                      <div style="display:none"> (</div>
                      <div style="width:50px;text-align:right;">${e.cpu}<span style="display:none">CPU</span></div>
                      <div style="width:50px;text-align:right;">${e.mem}GB</div>
                      <div style="width:60px;text-align:right;">${e.shmem?h`
                        ${parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(e.shared_memory,"g")).toFixed(2)} GB
                      `:h`64MB`}
                      </div>
                      <div style="width:80px;text-align:right;">
                        ${e.cuda_device&&e.cuda_device>0?h`${e.cuda_device} CUDA GPU`:h``}
                        ${e.cuda_shares&&e.cuda_shares>0?h`${e.cuda_shares} GPU`:h``}
                        ${e.rocm_device&&e.rocm_device>0?h`${e.rocm_device} ROCM GPU`:h``}
                        ${e.tpu_device&&e.tpu_device>0?h`${e.tpu_device} TPU`:h``}
                      </div>
                      <div style="display:none">)</div>
                    </div>
                  </mwc-list-item>
                `))}
              ${this.isEmpty(this.resource_templates_filtered)?h`
                <mwc-list-item class="resource-button vertical center start layout" role="option"
                               style="height:140px;width:350px;" type="button"
                               flat inverted outlined disabled selected>
                  <div>
                    <h4>${v("session.launcher.NoSuitablePreset")}</h4>
                    <div style="font-size:12px;">Use advanced settings to <br>start custom session</div>
                  </div>
                </mwc-list-item>
              `:h``}
              </mwc-select>
            </div>
            <wl-expansion name="resource-group">
              <span slot="title">${v("session.launcher.CustomAllocation")}</span>
              <div class="vertical layout">
                <div>
                  <mwc-list-item hasMeta class="resource-type">
                    <div>CPU</div>
                    <mwc-icon-button slot="meta" icon="info" class="fg info"
                                     @click="${e=>this._showResourceDescription(e,"cpu")}"></mwc-icon-button>
                  </mwc-list-item>
                  <hr class="separator" />
                  <div class="slider-list-item">
                    <lablup-slider id="cpu-resource" class="cpu" step="1"
                                   pin snaps expand editable markers tabindex="0"
                                   @change="${e=>this._applyResourceValueChanges(e)}"
                                   marker_limit="${this.marker_limit}"
                                   suffix="${m("session.launcher.Core")}"
                                   min="${this.cpu_metric.min}" max="${this.cpu_metric.max}"
                                   value="${this.cpu_request}"></lablup-slider>
                  </div>
                  <mwc-list-item hasMeta class="resource-type">
                    <div>RAM</div>
                    <mwc-icon-button slot="meta" icon="info" class="fg info"
                                     @click="${e=>this._showResourceDescription(e,"mem")}"></mwc-icon-button>
                  </mwc-list-item>
                  <hr class="separator" />
                  <div class="slider-list-item">
                    <lablup-slider id="mem-resource" class="mem"
                                   pin snaps expand step=0.05 editable markers tabindex="0"
                                   @change="${e=>{this._applyResourceValueChanges(e),this._updateShmemLimit()}}"
                                   marker_limit="${this.marker_limit}" suffix="GB"
                                   min="${this.mem_metric.min}" max="${this.mem_metric.max}"
                                   value="${this.mem_request}"></lablup-slider>
                  </div>
                  <mwc-list-item hasMeta class="resource-type">
                    <div>${v("session.launcher.SharedMemory")}</div>
                    <mwc-icon-button slot="meta" icon="info" class="fg info"
                      @click="${e=>this._showResourceDescription(e,"shmem")}"></mwc-icon-button>
                  </mwc-list-item>
                  <hr class="separator" />
                  <div class="slider-list-item">
                    <lablup-slider id="shmem-resource" class="mem"
                                 pin snaps step="0.0125" editable markers tabindex="0"
                                 @change="${e=>{this._applyResourceValueChanges(e),this._updateShmemLimit()}}"
                                 marker_limit="${this.marker_limit}" suffix="GB"
                                 min="0.0625" max="${this.shmem_metric.max}"
                                 value="${this.shmem_request}"></lablup-slider>
                  </div>
                  <mwc-list-item hasMeta class="resource-type">
                    <div>GPU</div>
                    <mwc-icon-button slot="meta" icon="info" class="fg info"
                      @click="${e=>this._showResourceDescription(e,"gpu")}"></mwc-icon-button>
                  </mwc-list-item>
                  <hr class="separator" />
                  <div class="slider-list-item">
                    <lablup-slider id="gpu-resource" class="gpu"
                                   pin snaps editable markers step="${this.gpu_step}"
                                   @change="${e=>this._applyResourceValueChanges(e)}"
                                   marker_limit="${this.marker_limit}" suffix="GPU"
                                   min="0.0" max="${this.cuda_device_metric.max}"
                                   value="${this.gpu_request}"></lablup-slider>
                  </div>
                  <mwc-list-item hasMeta class="resource-type">
                    <div>${v("webui.menu.Sessions")}</div>
                    <mwc-icon-button slot="meta" icon="info" class="fg info"
                      @click="${e=>this._showResourceDescription(e,"session")}"></mwc-icon-button>
                  </mwc-list-item>
                  <hr class="separator" />
                  <div class="slider-list-item">
                    <lablup-slider id="session-resource" class="session"
                                   pin snaps editable markers step="1"
                                   @change="${e=>this._applyResourceValueChanges(e)}"
                                   marker_limit="${this.marker_limit}" suffix="#"
                                   min="1" max="${this.concurrency_limit}"
                                   value="${this.session_request}"></lablup-slider>
                  </div>
                </div>
              </div>
            </wl-expansion>
            ${this.cluster_support?h`
              <mwc-select id="cluster-mode" label="${m("session.launcher.ClusterMode")}" required
                          icon="account_tree" fixedMenuPosition
                          value="${this.cluster_mode}" @change="${e=>this._setClusterMode(e)}">
                ${this.cluster_mode_list.map((e=>h`
                  <mwc-list-item
                      class="cluster-mode-dropdown"
                      ?selected="${e===this.cluster_mode}"
                      id="${e}"
                      value="${e}">
                    <div class="horizontal layout center" style="width:100%;">
                      <p style="width:300px;margin-left:21px;">${v("session.launcher."+e)}</p>
                      <mwc-icon-button
                          icon="info"
                          @click="${t=>this._showResourceDescription(t,e)}">
                      </mwc-icon-button>
                    </div>
                  </mwc-list-item>
                `))}
              </mwc-select>
              <div class="horizontal layout center flex center-justified">
                <div>
                  <mwc-list-item class="resource-type" style="pointer-events: none;">
                    <div class="resource-type">${v("session.launcher.ClusterSize")}</div>
                  </mwc-list-item>
                  <hr class="separator" />
                  <div class="slider-list-item">
                    <lablup-slider id="cluster-size" class="cluster"
                                   pin snaps expand editable markers step="1"
                                   marker_limit="${this.marker_limit}"
                                   min="${this.cluster_metric.min}" max="${this.cluster_metric.max}"
                                   value="${this.cluster_size}"
                                   @change="${e=>this._applyResourceValueChanges(e,!1)}"
                                   suffix="${"single-node"===this.cluster_mode?m("session.launcher.Container"):m("session.launcher.Node")}"></lablup-slider>
                  </div>
                </div>
              </div>
            `:h``}
            <wl-expansion name="hpc-option-group">
              <span slot="title">${v("session.launcher.HPCOptimization")}</span>
              <div class="vertical center layout">
                <div class="horizontal center center-justified flex layout">
                  <div style="width:313px;">${v("session.launcher.SwitchOpenMPoptimization")}</div>
                  <mwc-switch id="OpenMPswitch" selected @click="${this._toggleHPCOptimization}"></mwc-switch>
                </div>
                <div id="HPCOptimizationOptions" style="display:none;">
                  <div class="horizontal center layout">
                    <div style="width:200px;">${v("session.launcher.NumOpenMPthreads")}</div>
                    <mwc-textfield id="OpenMPCore" type="number" placeholder="1"
                                   value="" min="0" max="1000" step="1" style="width:120px;"
                                   pattern="[0-9]+" @change="${e=>this._validateInput(e)}">
                    </mwc-textfield>
                    <mwc-icon-button icon="info" class="fg green info"
                                     @click="${e=>this._showResourceDescription(e,"openmp-optimization")}"></mwc-icon-button>
                  </div>
                  <div class="horizontal center layout">
                    <div style="width:200px;">${v("session.launcher.NumOpenBLASthreads")}</div>
                    <mwc-textfield id="OpenBLASCore" type="number" placeholder="1"
                                   value="" min="0" max="1000" step="1" style="width:120px;"
                                   pattern="[0-9]+" @change="${e=>this._validateInput(e)}">
                    </mwc-textfield>
                    <mwc-icon-button icon="info" class="fg green info"
                                      @click="${e=>this._showResourceDescription(e,"openmp-optimization")}"></mwc-icon-button>
                  </div>
                </div>
              </div>
            </wl-expansion>
          </div>
          <div id="progress-04" class="progress center layout fade">
            <p class="title">${v("session.SessionInfo")}</p>
            <div class="vertical layout cluster-total-allocation-container">
              ${this._preProcessingSessionInfo()?h`
                <div class="vertical layout" style="margin-left:10px;margin-bottom:5px;">
                  <div class="horizontal layout">
                    <div style="margin-right:5px;width:150px;">
                      ${v("session.EnvironmentInfo")}
                    </div>
                    <div class="vertical layout" >
                      <lablup-shields app="${((null===(e=this.resourceBroker.imageInfo[this.sessionInfoObj.environment])||void 0===e?void 0:e.name)||this.sessionInfoObj.environment).toUpperCase()}"
                                      color="green"
                                      description="${this.sessionInfoObj.version[0]}"
                                      ui="round"
                                      style="margin-right:3px;"></lablup-shields>
                      <div class="horizontal layout">
                        ${this.sessionInfoObj.version.map(((e,t)=>t>0?h`
                                <lablup-shields color="green" description="${e}" ui="round"
                                  style="margin-top:3px;margin-right:3px;"></lablup-shields>
                              `:h``))}
                      </div>
                      <lablup-shields color="blue"
                                      description="${"inference"===this.mode?this.mode.toUpperCase():this.sessionType.toUpperCase()}"
                                      ui="round"
                                      style="margin-top:3px;margin-right:3px;margin-bottom:9px;"></lablup-shields>
                    </div>
                  </div>
                  <div class="horizontal layout">
                    <div class="vertical layout" style="margin-right:5px;width:150px;">
                      ${v("registry.ProjectName")}
                    </div>
                    <div class="vertical layout">
                      ${null===(t=globalThis.backendaiclient)||void 0===t?void 0:t.current_group}
                    </div>
                  </div>
                  <div class="horizontal layout">
                    <div class="vertical layout" style="margin-right:5px;width:150px;">
                      ${v("session.ResourceGroup")}
                    </div>
                    <div class="vertical layout">
                      ${this.scaling_group}
                    </div>
                  </div>
                </div>
              `:h``}
            </div>
            <p class="title">${v("session.launcher.TotalAllocation")}</p>
            <div class="vertical layout center center-justified cluster-total-allocation-container">
              <div id="cluster-allocation-pane" style="position:relative;${this.cluster_size<=1?"display:none;":""}">
                <div class="horizontal layout">
                  <div class="vertical layout center center-justified resource-allocated">
                    <p>${v("session.launcher.CPU")}</p>
                    <span>${this.cpu_request*this.cluster_size*this.session_request}</span>
                    <p>Core</p>
                  </div>
                  <div class="vertical layout center center-justified resource-allocated">
                    <p>${v("session.launcher.Memory")}</p>
                    <span>${this._roundResourceAllocation(this.mem_request*this.cluster_size*this.session_request,1)}</span>
                    <p>GB</p>
                  </div>
                  <div class="vertical layout center center-justified resource-allocated">
                    <p>${v("session.launcher.SharedMemoryAbbr")}</p>
                    <span>${this._conditionalGBtoMB(this.shmem_request*this.cluster_size*this.session_request)}</span>
                    <p>${this._conditionalGBtoMBunit(this.shmem_request*this.cluster_size*this.session_request)}</p>
                  </div>
                  <div class="vertical layout center center-justified resource-allocated">
                    <p>${v("session.launcher.GPU")}</p>
                    <span>${this._roundResourceAllocation(this.gpu_request*this.cluster_size*this.session_request,2)}</span>
                    <p>${v("session.launcher.GPUSlot")}</p>
                  </div>
                </div>
                <div style="height:1em"></div>
              </div>
              <div id="total-allocation-container" class="horizontal layout center center-justified allocation-check">
                <div id="total-allocation-pane" style="position:relative;">
                  <div class="horizontal layout resource-allocated-box">
                    <div class="vertical layout center center-justified resource-allocated">
                      <p>${v("session.launcher.CPU")}</p>
                      <span>${this.cpu_request}</span>
                      <p>Core</p>
                    </div>
                    <div class="vertical layout center center-justified resource-allocated">
                      <p>${v("session.launcher.Memory")}</p>
                      <span>${this._roundResourceAllocation(this.mem_request,1)}</span>
                      <p>GB</p>
                    </div>
                    <div class="vertical layout center center-justified resource-allocated">
                      <p>${v("session.launcher.SharedMemoryAbbr")}</p>
                      <span>${this._conditionalGBtoMB(this.shmem_request)}</span>
                      <p>${this._conditionalGBtoMBunit(this.shmem_request)}</p>
                    </div>
                    <div class="vertical layout center center-justified resource-allocated">
                      <p>${v("session.launcher.GPU")}</p>
                      <span>${this.gpu_request}</span>
                      <p>${v("session.launcher.GPUSlot")}</p>
                    </div>
                  </div>
                  <div id="resource-allocated-box-shadow"></div>
                </div>
                <div class="vertical layout center center-justified cluster-allocated" style="z-index:10;">
                  <div class="horizontal layout">
                    <p>×</p>
                    <span>${this.cluster_size<=1?this.session_request:this.cluster_size}</span>
                  </div>
                  <p class="small">${v("session.launcher.Container")}</p>
                </div>
                <div class="vertical layout center center-justified cluster-allocated" style="z-index:10;">
                  <div class="horizontal layout">
                    <p>${this.cluster_mode,""}</p>
                    <span style="text-align:center;">${"single-node"===this.cluster_mode?v("session.launcher.SingleNode"):v("session.launcher.MultiNode")}</span>
                  </div>
                  <p class="small">${v("session.launcher.AllocateNode")}</p>
                </div>
              </div>
            </div>
            ${"inference"!==this.mode?h`
            <p class="title">${v("session.launcher.MountedFolders")}</p>
            <div id="mounted-folders-container">
              ${this.selectedVfolders.length>0||this.autoMountedVfolders.length>0?h`
                <ul class="vfolder-list">
                  ${this.selectedVfolders.map((e=>h`
                    <li><mwc-icon>folder_open</mwc-icon>${e}
                    ${e in this.folderMapping?this.folderMapping[e].startsWith("/")?h` (&#10140; ${this.folderMapping[e]})`:h`(&#10140; /home/work/${this.folderMapping[e]})`:h`(&#10140; /home/work/${e})`}
                    </li>
                  `))}
                  ${this.autoMountedVfolders.map((e=>h`
                    <li><mwc-icon>folder_special</mwc-icon>${e.name}</li>
                  `))}
                </ul>
              `:h`
                <div class="vertical layout center flex blank-box">
                  <span>${v("session.launcher.NoFolderMounted")}</span>
                </div>
              `}
            </div>`:h`

            `}
            <p class="title">${v("session.launcher.EnvironmentVariablePaneTitle")}</p>
            <div class="environment-variables-container">
              ${this.environ.length>0?h`
                <div class="horizontal flex center center-justified layout" style="overflow-x:hidden;">
                  <div role="listbox">
                    <h4>${m("session.launcher.EnvironmentVariable")}</h4>
                    ${this.environ.map((e=>h`
                      <wl-textfield disabled value="${e.name}"></wl-textfield>
                    `))}
                  </div>
                  <div role="listbox" style="margin-left:15px;">
                    <h4>${m("session.launcher.EnvironmentVariableValue")}</h4>
                    ${this.environ.map((e=>h`
                      <wl-textfield disabled value="${e.value}"></wl-textfield>
                    `))}
                  </div>
                </div>
              `:h`
                <div class="vertical layout center flex blank-box">
                  <span>${v("session.launcher.NoEnvConfigured")}</span>
                </div>
              `}
            </div>
          </div>
        </form>
        <div slot="footer" class="vertical flex layout">
          <div class="horizontal flex layout distancing center-center">
            <mwc-icon-button id="prev-button"
                             icon="arrow_back"
                             style="visibility:hidden;margin-right:12px;"
                             @click="${()=>this.moveProgress(-1)}"></mwc-icon-button>
            <mwc-button
                unelevated
                class="launch-button"
                id="launch-button"
                icon="rowing"
                @click="${()=>this._newSessionWithConfirmation()}">
              <span id="launch-button-msg">${v("session.launcher.Launch")}</span>
            </mwc-button>
            <mwc-icon-button id="next-button"
                             icon="arrow_forward"
                             style="margin-left:12px;"
                             @click="${()=>this.moveProgress(1)}"></mwc-icon-button>
          </div>
          <div class="horizontal flex layout">
            <lablup-progress-bar progress="${this._calculateProgress()}"></lablup-progress-bar>
          </div>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="modify-env-dialog" fixed backdrop persistent closeWithConfirmation>
        <span slot="title">${v("session.launcher.SetEnvironmentVariable")}</span>
        <span slot="action">
          <mwc-icon-button icon="info" @click="${e=>this._showEnvConfigDescription(e)}" style="pointer-events: auto;"></mwc-icon-button>
        </span>
        <div slot="content" id="modify-env-container">
          <div class="horizontal layout center flex justified header">
            <div> ${v("session.launcher.EnvironmentVariable")} </div>
            <div> ${v("session.launcher.EnvironmentVariableValue")} </div>
          </div>
          <div id="modify-env-fields-container" class="layout center">
            ${this.environ.forEach((e=>h`
                <div class="horizontal layout center row">
                  <mwc-textfield value="${e.name}"></mwc-textfield>
                  <mwc-textfield value="${e.value}"></mwc-textfield>
                  <mwc-icon-button class="green minus-btn" icon="remove"
                    @click="${e=>this._removeEnvItem(e)}"></mwc-icon-button>
                </div>
              `))}
            <div class="horizontal layout center row">
              <mwc-textfield></mwc-textfield>
              <mwc-textfield></mwc-textfield>
              <mwc-icon-button class="green minus-btn" icon="remove"
                @click="${e=>this._removeEnvItem(e)}"></mwc-icon-button>
            </div>
          </div>
          <mwc-button id="env-add-btn" outlined icon="add" class="horizontal flex layout center"
              @click="${()=>this._appendEnvRow()}">Add</mwc-button>
        </div>
        <div slot="footer" class="horizontal layout">
          <mwc-button
              id="delete-all-button"
              slot="footer"
              icon="delete"
              label="${m("button.Reset")}"
              @click="${()=>this._clearRows()}"></mwc-button>
          <mwc-button
              unelevated
              slot="footer"
              icon="check"
              label="${m("button.Save")}"
              @click="${()=>this.modifyEnv()}"></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="help-description" fixed backdrop>
        <span slot="title">${this._helpDescriptionTitle}</span>
        <div slot="content" class="horizontal layout center" style="margin:5px;">
        ${""==this._helpDescriptionIcon?h``:h`
          <img slot="graphic" alt="help icon" src="resources/icons/${this._helpDescriptionIcon}"
               style="width:64px;height:64px;margin-right:10px;"/>
        `}
          <div style="font-size:14px;">${g(this._helpDescription)}</div>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="launch-confirmation-dialog" warning fixed backdrop>
        <span slot="title">${v("session.launcher.NoFolderMounted")}</span>
        <div slot="content" class="vertical layout">
          <p>${v("session.launcher.HomeDirectoryDeletionDialog")}</p>
          <p>${v("session.launcher.LaunchConfirmationDialog")}</p>
          <p>${v("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
              unelevated
              class="launch-confirmation-button"
              id="launch-confirmation-button"
              icon="rowing"
              @click="${()=>this._newSession()}">
            <span>${v("session.launcher.Launch")}</span>
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="env-config-confirmation" warning fixed>
        <span slot="title">${v("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${v("session.launcher.EnvConfigWillDisappear")}</p>
          <p>${v("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
              id="env-config-remain-button"
              label="${m("button.Cancel")}"
              @click="${()=>this.closeDialog("env-config-confirmation")}"
              style="width:auto;margin-right:10px;">
          </mwc-button>
          <mwc-button
              unelevated
              id="env-config-reset-button"
              label="${m("button.DismissAndProceed")}"
              @click="${()=>this._closeAndResetEnvInput()}"
              style="width:auto;">
          </mwc-button>
        </div>
      </backend-ai-dialog>
    `}};e([t({type:Boolean})],Xt.prototype,"is_connected",void 0),e([t({type:Boolean})],Xt.prototype,"enableLaunchButton",void 0),e([t({type:Boolean})],Xt.prototype,"hideLaunchButton",void 0),e([t({type:Boolean})],Xt.prototype,"hideEnvDialog",void 0),e([t({type:Boolean})],Xt.prototype,"enableInferenceWorkload",void 0),e([t({type:String})],Xt.prototype,"location",void 0),e([t({type:String})],Xt.prototype,"mode",void 0),e([t({type:String})],Xt.prototype,"newSessionDialogTitle",void 0),e([t({type:String})],Xt.prototype,"importScript",void 0),e([t({type:String})],Xt.prototype,"importFilename",void 0),e([t({type:Object})],Xt.prototype,"imageRequirements",void 0),e([t({type:Object})],Xt.prototype,"resourceLimits",void 0),e([t({type:Object})],Xt.prototype,"userResourceLimit",void 0),e([t({type:Object})],Xt.prototype,"aliases",void 0),e([t({type:Object})],Xt.prototype,"tags",void 0),e([t({type:Object})],Xt.prototype,"icons",void 0),e([t({type:Object})],Xt.prototype,"imageInfo",void 0),e([t({type:String})],Xt.prototype,"kernel",void 0),e([t({type:Array})],Xt.prototype,"versions",void 0),e([t({type:Array})],Xt.prototype,"languages",void 0),e([t({type:Number})],Xt.prototype,"marker_limit",void 0),e([t({type:String})],Xt.prototype,"gpu_mode",void 0),e([t({type:Array})],Xt.prototype,"gpu_modes",void 0),e([t({type:Number})],Xt.prototype,"gpu_step",void 0),e([t({type:Object})],Xt.prototype,"cpu_metric",void 0),e([t({type:Object})],Xt.prototype,"mem_metric",void 0),e([t({type:Object})],Xt.prototype,"shmem_metric",void 0),e([t({type:Object})],Xt.prototype,"cuda_device_metric",void 0),e([t({type:Object})],Xt.prototype,"cuda_shares_metric",void 0),e([t({type:Object})],Xt.prototype,"rocm_device_metric",void 0),e([t({type:Object})],Xt.prototype,"tpu_device_metric",void 0),e([t({type:Object})],Xt.prototype,"cluster_metric",void 0),e([t({type:Array})],Xt.prototype,"cluster_mode_list",void 0),e([t({type:Boolean})],Xt.prototype,"cluster_support",void 0),e([t({type:Object})],Xt.prototype,"images",void 0),e([t({type:Object})],Xt.prototype,"total_slot",void 0),e([t({type:Object})],Xt.prototype,"total_resource_group_slot",void 0),e([t({type:Object})],Xt.prototype,"total_project_slot",void 0),e([t({type:Object})],Xt.prototype,"used_slot",void 0),e([t({type:Object})],Xt.prototype,"used_resource_group_slot",void 0),e([t({type:Object})],Xt.prototype,"used_project_slot",void 0),e([t({type:Object})],Xt.prototype,"available_slot",void 0),e([t({type:Number})],Xt.prototype,"concurrency_used",void 0),e([t({type:Number})],Xt.prototype,"concurrency_max",void 0),e([t({type:Number})],Xt.prototype,"concurrency_limit",void 0),e([t({type:Number})],Xt.prototype,"max_containers_per_session",void 0),e([t({type:Array})],Xt.prototype,"vfolders",void 0),e([t({type:Array})],Xt.prototype,"selectedVfolders",void 0),e([t({type:Array})],Xt.prototype,"autoMountedVfolders",void 0),e([t({type:Array})],Xt.prototype,"modelVfolders",void 0),e([t({type:Array})],Xt.prototype,"nonAutoMountedVfolders",void 0),e([t({type:Object})],Xt.prototype,"folderMapping",void 0),e([t({type:Object})],Xt.prototype,"customFolderMapping",void 0),e([t({type:Object})],Xt.prototype,"used_slot_percent",void 0),e([t({type:Object})],Xt.prototype,"used_resource_group_slot_percent",void 0),e([t({type:Object})],Xt.prototype,"used_project_slot_percent",void 0),e([t({type:Array})],Xt.prototype,"resource_templates",void 0),e([t({type:Array})],Xt.prototype,"resource_templates_filtered",void 0),e([t({type:String})],Xt.prototype,"default_language",void 0),e([t({type:Number})],Xt.prototype,"cpu_request",void 0),e([t({type:Number})],Xt.prototype,"mem_request",void 0),e([t({type:Number})],Xt.prototype,"shmem_request",void 0),e([t({type:Number})],Xt.prototype,"gpu_request",void 0),e([t({type:String})],Xt.prototype,"gpu_request_type",void 0),e([t({type:Number})],Xt.prototype,"session_request",void 0),e([t({type:Boolean})],Xt.prototype,"_status",void 0),e([t({type:Number})],Xt.prototype,"num_sessions",void 0),e([t({type:String})],Xt.prototype,"scaling_group",void 0),e([t({type:Array})],Xt.prototype,"scaling_groups",void 0),e([t({type:Array})],Xt.prototype,"sessions_list",void 0),e([t({type:Boolean})],Xt.prototype,"metric_updating",void 0),e([t({type:Boolean})],Xt.prototype,"metadata_updating",void 0),e([t({type:Boolean})],Xt.prototype,"aggregate_updating",void 0),e([t({type:Object})],Xt.prototype,"scaling_group_selection_box",void 0),e([t({type:Object})],Xt.prototype,"resourceGauge",void 0),e([t({type:String})],Xt.prototype,"sessionType",void 0),e([t({type:Boolean})],Xt.prototype,"ownerFeatureInitialized",void 0),e([t({type:String})],Xt.prototype,"ownerDomain",void 0),e([t({type:Array})],Xt.prototype,"ownerKeypairs",void 0),e([t({type:Array})],Xt.prototype,"ownerGroups",void 0),e([t({type:Array})],Xt.prototype,"ownerScalingGroups",void 0),e([t({type:Boolean})],Xt.prototype,"project_resource_monitor",void 0),e([t({type:Boolean})],Xt.prototype,"_default_language_updated",void 0),e([t({type:Boolean})],Xt.prototype,"_default_version_updated",void 0),e([t({type:String})],Xt.prototype,"_helpDescription",void 0),e([t({type:String})],Xt.prototype,"_helpDescriptionTitle",void 0),e([t({type:String})],Xt.prototype,"_helpDescriptionIcon",void 0),e([t({type:Number})],Xt.prototype,"max_cpu_core_per_session",void 0),e([t({type:Number})],Xt.prototype,"max_mem_per_container",void 0),e([t({type:Number})],Xt.prototype,"max_cuda_device_per_container",void 0),e([t({type:Number})],Xt.prototype,"max_cuda_shares_per_container",void 0),e([t({type:Number})],Xt.prototype,"max_shm_per_container",void 0),e([t({type:Boolean})],Xt.prototype,"allow_manual_image_name_for_session",void 0),e([t({type:Object})],Xt.prototype,"resourceBroker",void 0),e([t({type:Number})],Xt.prototype,"cluster_size",void 0),e([t({type:String})],Xt.prototype,"cluster_mode",void 0),e([t({type:Object})],Xt.prototype,"deleteEnvInfo",void 0),e([t({type:Object})],Xt.prototype,"deleteEnvRow",void 0),e([t({type:Array})],Xt.prototype,"environ",void 0),e([t({type:Object})],Xt.prototype,"environ_values",void 0),e([t({type:Object})],Xt.prototype,"vfolder_select_expansion",void 0),e([t({type:Number})],Xt.prototype,"currentIndex",void 0),e([t({type:Number})],Xt.prototype,"progressLength",void 0),e([t({type:Object})],Xt.prototype,"_nonAutoMountedFolderGrid",void 0),e([t({type:Object})],Xt.prototype,"_modelFolderGrid",void 0),e([t({type:Boolean})],Xt.prototype,"_debug",void 0),e([t({type:Object})],Xt.prototype,"_boundFolderToMountListRenderer",void 0),e([t({type:Object})],Xt.prototype,"_boundFolderMapRenderer",void 0),e([t({type:Object})],Xt.prototype,"_boundPathRenderer",void 0),e([t({type:Boolean})],Xt.prototype,"useScheduledTime",void 0),e([t({type:Object})],Xt.prototype,"schedulerTimer",void 0),e([t({type:Object})],Xt.prototype,"sessionInfoObj",void 0),e([i("#image-name")],Xt.prototype,"manualImageName",void 0),e([i("#version")],Xt.prototype,"version_selector",void 0),e([i("#environment")],Xt.prototype,"environment",void 0),e([i("#owner-group")],Xt.prototype,"ownerGroupSelect",void 0),e([i("#scaling-groups")],Xt.prototype,"scalingGroups",void 0),e([i("#resource-templates")],Xt.prototype,"resourceTemplatesSelect",void 0),e([i("#owner-scaling-group")],Xt.prototype,"ownerScalingGroupSelect",void 0),e([i("#owner-accesskey")],Xt.prototype,"ownerAccesskeySelect",void 0),e([i("#owner-email")],Xt.prototype,"ownerEmailInput",void 0),e([i("#vfolder-mount-preview")],Xt.prototype,"vfolderMountPreview",void 0),e([i("#use-scheduled-time")],Xt.prototype,"useScheduledTimeSwitch",void 0),e([i("#launch-button")],Xt.prototype,"launchButton",void 0),e([i("#prev-button")],Xt.prototype,"prevButton",void 0),e([i("#next-button")],Xt.prototype,"nextButton",void 0),e([i("#OpenMPswitch")],Xt.prototype,"openMPSwitch",void 0),e([i("#cpu-resource")],Xt.prototype,"cpuResouceSlider",void 0),e([i("#gpu-resource")],Xt.prototype,"gpuResouceSlider",void 0),e([i("#mem-resource")],Xt.prototype,"memoryResouceSlider",void 0),e([i("#shmem-resource")],Xt.prototype,"sharedMemoryResouceSlider",void 0),e([i("#session-resource")],Xt.prototype,"sessionResouceSlider",void 0),e([i("#cluster-size")],Xt.prototype,"clusterSizeSlider",void 0),e([i("#launch-button-msg")],Xt.prototype,"launchButtonMessage",void 0),e([i("vaadin-date-time-picker")],Xt.prototype,"dateTimePicker",void 0),e([i("#new-session-dialog")],Xt.prototype,"newSessionDialog",void 0),e([i("#modify-env-dialog")],Xt.prototype,"modifyEnvDialog",void 0),e([i("#launch-confirmation-dialog")],Xt.prototype,"launchConfirmationDialog",void 0),e([i("#help-description")],Xt.prototype,"helpDescriptionDialog",void 0),Xt=e([s("backend-ai-session-launcher")],Xt);export{be as O,Pe as P,yt as a,ge as o};
