import{j as e,r as t,i,T as s,D as o,P as n,k as a,l as r,m as l,O as c,p as d,q as p,E as h,u,v as m,w as g,y as _,z as b,A as v,_ as f,n as y,b as w,e as k,B as x,c as A,I as S,a as T,f as $,C,x as I,g as D,t as E,o as R,F as M,d as z}from"./backend-ai-webui-aedf1078.js";import"./backend-ai-resource-monitor-e64bed82.js";import{i as j}from"./vaadin-grid-609be2ad.js";import"./vaadin-grid-selection-column-b5d0dd65.js";import"./vaadin-grid-sort-column-8ddab2be.js";import"./vaadin-grid-filter-column-1c454e0f.js";import"./vaadin-iconset-7cb3c777.js";import"./expansion-836f049f.js";import"./backend-ai-list-status-c77c240c.js";import"./lablup-grid-sort-filter-column-c36e5e00.js";import"./lablup-progress-bar-309da793.js";import"./mwc-tab-bar-fc7f3c19.js";import"./lablup-activity-panel-897d665b.js";import"./backend-ai-session-launcher-7bd6e30f.js";import{J as N}from"./json_to_csv-35c9e191.js";import"./mwc-switch-5506e5cb.js";import"./label-4414bd3d.js";import"./dir-utils-086eb4a0.js";import"./radio-behavior-2ca446f6.js";import"./mwc-check-list-item-fbd74804.js";import"./slider-4ea52613.js";import"./media-query-controller-28b1637c.js";import"./textfield-f06e3f8a.js";import"./lablup-codemirror-3d8a6b4f.js";
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */t("vaadin-grid-tree-toggle",i`
    :host {
      --vaadin-grid-tree-toggle-level-offset: 2em;
      align-items: center;
      vertical-align: middle;
      transform: translateX(calc(var(--lumo-space-s) * -1));
      -webkit-tap-highlight-color: transparent;
    }

    :host(:not([leaf])) {
      cursor: default;
    }

    [part='toggle'] {
      display: inline-block;
      font-size: 1.5em;
      line-height: 1;
      width: 1em;
      height: 1em;
      text-align: center;
      color: var(--lumo-contrast-50pct);
      cursor: var(--lumo-clickable-cursor);
      /* Increase touch target area */
      padding: calc(1em / 3);
      margin: calc(1em / -3);
    }

    :host(:not([dir='rtl'])) [part='toggle'] {
      margin-right: 0;
    }

    @media (hover: hover) {
      :host(:hover) [part='toggle'] {
        color: var(--lumo-contrast-80pct);
      }
    }

    [part='toggle']::before {
      font-family: 'lumo-icons';
      display: inline-block;
      height: 100%;
    }

    :host(:not([expanded])) [part='toggle']::before {
      content: var(--lumo-icons-angle-right);
    }

    :host([expanded]) [part='toggle']::before {
      content: var(--lumo-icons-angle-right);
      transform: rotate(90deg);
    }

    /* Experimental support for hierarchy connectors, using an unsupported selector */
    :host([theme~='connectors']) #level-spacer {
      position: relative;
      z-index: -1;
      font-size: 1em;
      height: 1.5em;
    }

    :host([theme~='connectors']) #level-spacer::before {
      display: block;
      content: '';
      margin-top: calc(var(--lumo-space-m) * -1);
      height: calc(var(--lumo-space-m) + 3em);
      background-image: linear-gradient(
        to right,
        transparent calc(var(--vaadin-grid-tree-toggle-level-offset) - 1px),
        var(--lumo-contrast-10pct) calc(var(--vaadin-grid-tree-toggle-level-offset) - 1px)
      );
      background-size: var(--vaadin-grid-tree-toggle-level-offset) var(--vaadin-grid-tree-toggle-level-offset);
      background-position: calc(var(--vaadin-grid-tree-toggle-level-offset) / 2 - 2px) 0;
    }

    /* RTL specific styles */

    :host([dir='rtl']) {
      margin-left: 0;
      margin-right: calc(var(--lumo-space-s) * -1);
    }

    :host([dir='rtl']) [part='toggle'] {
      margin-left: 0;
    }

    :host([dir='rtl'][expanded]) [part='toggle']::before {
      transform: rotate(-90deg);
    }

    :host([dir='rtl'][theme~='connectors']) #level-spacer::before {
      background-image: linear-gradient(
        to left,
        transparent calc(var(--vaadin-grid-tree-toggle-level-offset) - 1px),
        var(--lumo-contrast-10pct) calc(var(--vaadin-grid-tree-toggle-level-offset) - 1px)
      );
      background-position: calc(100% - (var(--vaadin-grid-tree-toggle-level-offset) / 2 - 2px)) 0;
    }

    :host([dir='rtl']:not([expanded])) [part='toggle']::before,
    :host([dir='rtl'][expanded]) [part='toggle']::before {
      content: var(--lumo-icons-angle-left);
    }
  `,{moduleId:"lumo-grid-tree-toggle"});
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const O=document.createElement("template");O.innerHTML="\n  <style>\n    @font-face {\n      font-family: \"vaadin-grid-tree-icons\";\n      src: url(data:application/font-woff;charset=utf-8;base64,d09GRgABAAAAAAQkAA0AAAAABrwAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAABGRlRNAAAECAAAABoAAAAcgHwa6EdERUYAAAPsAAAAHAAAAB4AJwAOT1MvMgAAAZQAAAA/AAAAYA8TBIJjbWFwAAAB8AAAAFUAAAFeGJvXWmdhc3AAAAPkAAAACAAAAAgAAAAQZ2x5ZgAAAlwAAABLAAAAhIrPOhFoZWFkAAABMAAAACsAAAA2DsJI02hoZWEAAAFcAAAAHQAAACQHAgPHaG10eAAAAdQAAAAZAAAAHAxVAgBsb2NhAAACSAAAABIAAAASAIAAVG1heHAAAAF8AAAAGAAAACAACgAFbmFtZQAAAqgAAAECAAACTwflzbdwb3N0AAADrAAAADYAAABZQ7Ajh3icY2BkYGAA4twv3Vfi+W2+MnCzMIDANSOmbGSa2YEZRHEwMIEoAAoiB6sAeJxjYGRgYD7w/wADAwsDCDA7MDAyoAI2AFEEAtIAAAB4nGNgZGBg4GBgZgDRDAxMDGgAAAGbABB4nGNgZp7JOIGBlYGBaSbTGQYGhn4IzfiawZiRkwEVMAqgCTA4MDA+38d84P8BBgdmIAapQZJVYGAEAGc/C54AeJxjYYAAxlAIzQTELAwMBxgZGB0ACy0BYwAAAHicY2BgYGaAYBkGRgYQiADyGMF8FgYbIM3FwMHABISMDArP9/3/+/8/WJXC8z0Q9v8nEp5gHVwMMMAIMo+RDYiZoQJMQIKJARUA7WBhGN4AACFKDtoAAAAAAAAAAAgACAAQABgAJgA0AEIAAHichYvBEYBADAKBVHBjBT4swl9KS2k05o0XHd/yW1hAfBFwCv9sIlJu3nZaNS3PXAaXXHI8Lge7DlzF7C1RgXc7xkK6+gvcD2URmQB4nK2RQWoCMRiFX3RUqtCli65yADModOMBLLgQSqHddRFnQghIAnEUvEA3vUUP0LP0Fj1G+yb8R5iEhO9/ef/7FwFwj28o9EthiVp4hBlehcfUP4Ur8o/wBAv8CU+xVFvhOR7UB7tUdUdlVRJ6HnHWTnhM/V24In8JT5j/KzzFSi2E53hUz7jCcrcIiDDwyKSW1JEct2HdIPH1DFytbUM0PofWdNk5E5oUqb/Q6HHBiVGZpfOXkyUMEj5IyBuNmYZQjBobfsuassvnkKLe1OuBBj0VQ8cRni2xjLWsHaM0jrjx3peYA0/vrdmUYqe9iy7bzrX6eNP7Jh1SijX+AaUVbB8AAHicY2BiwA84GBgYmRiYGJkZmBlZGFkZ2djScyoLMgzZS/MyDQwMwLSruZMzlHaB0q4A76kLlwAAAAEAAf//AA94nGNgZGBg4AFiMSBmYmAEQnYgZgHzGAAD6wA2eJxjYGBgZACCKxJigiD6mhFTNowGACmcA/8AAA==) format('woff');\n      font-weight: normal;\n      font-style: normal;\n    }\n  </style>\n",document.head.appendChild(O.content);class L extends(s(o(n))){static get template(){return a`
      <style>
        :host {
          display: inline-flex;
          align-items: baseline;
          max-width: 100%;

          /* CSS API for :host */
          --vaadin-grid-tree-toggle-level-offset: 1em;
          --_collapsed-icon: '\\e7be\\00a0';
        }

        :host([dir='rtl']) {
          --_collapsed-icon: '\\e7bd\\00a0';
        }

        :host([hidden]) {
          display: none !important;
        }

        :host(:not([leaf])) {
          cursor: pointer;
        }

        #level-spacer,
        [part='toggle'] {
          flex: none;
        }

        #level-spacer {
          display: inline-block;
          width: calc(var(---level, '0') * var(--vaadin-grid-tree-toggle-level-offset));
        }

        [part='toggle']::before {
          font-family: 'vaadin-grid-tree-icons';
          line-height: 1em; /* make icon font metrics not affect baseline */
        }

        :host(:not([expanded])) [part='toggle']::before {
          content: var(--_collapsed-icon);
        }

        :host([expanded]) [part='toggle']::before {
          content: '\\e7bc\\00a0'; /* icon glyph + single non-breaking space */
        }

        :host([leaf]) [part='toggle'] {
          visibility: hidden;
        }

        slot {
          display: block;
          overflow: hidden;
          text-overflow: ellipsis;
        }
      </style>

      <span id="level-spacer"></span>
      <span part="toggle"></span>
      <slot></slot>
    `}static get is(){return"vaadin-grid-tree-toggle"}static get properties(){return{level:{type:Number,value:0,observer:"_levelChanged"},leaf:{type:Boolean,value:!1,reflectToAttribute:!0},expanded:{type:Boolean,value:!1,reflectToAttribute:!0,notify:!0}}}ready(){super.ready(),this.addEventListener("click",(e=>this._onClick(e)))}_onClick(e){this.leaf||j(e.target)||e.target instanceof HTMLLabelElement||(e.preventDefault(),this.expanded=!this.expanded)}_levelChanged(e){const t=Number(e).toString();this.style.setProperty("---level",t)}}customElements.define(L.is,L);let P;t("vaadin-tooltip-overlay",[r,i`
  :host {
    --vaadin-tooltip-offset-top: var(--lumo-space-xs);
    --vaadin-tooltip-offset-bottom: var(--lumo-space-xs);
    --vaadin-tooltip-offset-start: var(--lumo-space-xs);
    --vaadin-tooltip-offset-end: var(--lumo-space-xs);
  }

  [part='overlay'] {
    background: var(--lumo-base-color) linear-gradient(var(--lumo-contrast-5pct), var(--lumo-contrast-5pct));
    color: var(--lumo-body-text-color);
    font-size: var(--lumo-font-size-xs);
    line-height: var(--lumo-line-height-s);
  }

  [part='content'] {
    padding: var(--lumo-space-xs) var(--lumo-space-s);
  }
`],{moduleId:"lumo-tooltip-overlay"}),
/**
 * @license
 * Copyright (c) 2022 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
t("vaadin-tooltip-overlay",i`
    :host {
      z-index: 1100;
    }

    [part='overlay'] {
      max-width: 40ch;
    }

    :host([position^='top'][top-aligned]) [part='overlay'],
    :host([position^='bottom'][top-aligned]) [part='overlay'] {
      margin-top: var(--vaadin-tooltip-offset-top, 0);
    }

    :host([position^='top'][bottom-aligned]) [part='overlay'],
    :host([position^='bottom'][bottom-aligned]) [part='overlay'] {
      margin-bottom: var(--vaadin-tooltip-offset-bottom, 0);
    }

    :host([position^='start'][start-aligned]) [part='overlay'],
    :host([position^='end'][start-aligned]) [part='overlay'] {
      margin-inline-start: var(--vaadin-tooltip-offset-start, 0);
    }

    :host([position^='start'][end-aligned]) [part='overlay'],
    :host([position^='end'][end-aligned]) [part='overlay'] {
      margin-inline-end: var(--vaadin-tooltip-offset-end, 0);
    }

    @media (forced-colors: active) {
      [part='overlay'] {
        outline: 1px dashed;
      }
    }
  `,{moduleId:"vaadin-tooltip-overlay-styles"});class F extends(l(c)){static get is(){return"vaadin-tooltip-overlay"}static get template(){return P||(P=super.template.cloneNode(!0),P.content.querySelector('[part~="overlay"]').removeAttribute("tabindex"),P.content.querySelector('[part~="content"]').innerHTML="<slot></slot>"),P}static get properties(){return{position:{type:String,reflectToAttribute:!0}}}ready(){super.ready(),this.owner=this.__dataHost,this.owner._overlayElement=this}requestContentUpdate(){if(super.requestContentUpdate(),this.toggleAttribute("hidden",""===this.textContent.trim()),this.positionTarget&&this.owner){const e=getComputedStyle(this.owner);["top","bottom","start","end"].forEach((t=>{this.style.setProperty(`--vaadin-tooltip-offset-${t}`,e.getPropertyValue(`--vaadin-tooltip-offset-${t}`))}))}}_updatePosition(){if(super._updatePosition(),this.positionTarget){if("bottom"===this.position||"top"===this.position){const e=this.positionTarget.getBoundingClientRect(),t=this.$.overlay.getBoundingClientRect(),i=e.width/2-t.width/2;if(this.style.left){const e=t.left+i;e>0&&(this.style.left=`${e}px`)}if(this.style.right){const e=parseFloat(this.style.right)+i;e>0&&(this.style.right=`${e}px`)}}if("start"===this.position||"end"===this.position){const e=this.positionTarget.getBoundingClientRect(),t=this.$.overlay.getBoundingClientRect(),i=e.height/2-t.height/2;this.style.top=`${t.top+i}px`}}}}customElements.define(F.is,F);
/**
 * @license
 * Copyright (c) 2022 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const B=500;let U=B,G=B,H=B;const q=new Set;let V=!1,K=null,J=null;class W{constructor(e){this.host=e}get openedProp(){return this.host.manual?"opened":"_autoOpened"}get focusDelay(){const e=this.host;return null!=e.focusDelay&&e.focusDelay>0?e.focusDelay:U}get hoverDelay(){const e=this.host;return null!=e.hoverDelay&&e.hoverDelay>0?e.hoverDelay:G}get hideDelay(){const e=this.host;return null!=e.hideDelay&&e.hideDelay>0?e.hideDelay:H}open(e={immediate:!1}){const{immediate:t,hover:i,focus:s}=e,o=i&&this.hoverDelay>0,n=s&&this.focusDelay>0;t||!o&&!n||this.__closeTimeout?this.__showTooltip():this.__warmupTooltip(n)}close(e){!e&&this.hideDelay>0?this.__scheduleClose():(this.__abortClose(),this._setOpened(!1)),this.__abortWarmUp(),V&&(this.__abortCooldown(),this.__scheduleCooldown())}_isOpened(){return this.host[this.openedProp]}_setOpened(e){this.host[this.openedProp]=e}__flushClosingTooltips(){q.forEach((e=>{e._stateController.close(!0),q.delete(e)}))}__showTooltip(){this.__abortClose(),this.__flushClosingTooltips(),this._setOpened(!0),V=!0,this.__abortWarmUp(),this.__abortCooldown()}__warmupTooltip(e){this._isOpened()||(V?this.__showTooltip():this.__scheduleWarmUp(e))}__abortClose(){this.__closeTimeout&&(clearTimeout(this.__closeTimeout),this.__closeTimeout=null)}__abortCooldown(){J&&(clearTimeout(J),J=null)}__abortWarmUp(){K&&(clearTimeout(K),K=null)}__scheduleClose(){this._isOpened()&&(q.add(this.host),this.__closeTimeout=setTimeout((()=>{q.delete(this.host),this.__closeTimeout=null,this._setOpened(!1)}),this.hideDelay))}__scheduleCooldown(){J=setTimeout((()=>{J=null,V=!1}),this.hideDelay)}__scheduleWarmUp(e){const t=e?this.focusDelay:this.hoverDelay;K=setTimeout((()=>{K=null,V=!0,this.__showTooltip()}),t)}}class Y extends(d(p(h(n)))){static get is(){return"vaadin-tooltip"}static get template(){return a`
      <style>
        :host {
          display: none;
        }
      </style>
      <vaadin-tooltip-overlay
        id="[[_uniqueId]]"
        role="tooltip"
        renderer="[[_renderer]]"
        theme$="[[_theme]]"
        opened="[[__computeOpened(manual, opened, _autoOpened, _isConnected)]]"
        position-target="[[target]]"
        position="[[__effectivePosition]]"
        no-horizontal-overlap$="[[__computeNoHorizontalOverlap(__effectivePosition)]]"
        no-vertical-overlap$="[[__computeNoVerticalOverlap(__effectivePosition)]]"
        horizontal-align="[[__computeHorizontalAlign(__effectivePosition)]]"
        vertical-align="[[__computeVerticalAlign(__effectivePosition)]]"
        on-mouseleave="__onOverlayMouseLeave"
        modeless
      ></vaadin-tooltip-overlay>
    `}static get properties(){return{context:{type:Object,value:()=>({})},focusDelay:{type:Number},for:{type:String,observer:"__forChanged"},hideDelay:{type:Number},hoverDelay:{type:Number},manual:{type:Boolean,value:!1},opened:{type:Boolean,value:!1},position:{type:String},shouldShow:{type:Object,value:()=>(e,t)=>!0},target:{type:Object,observer:"__targetChanged"},text:{type:String,observer:"__textChanged"},generator:{type:Object},_autoOpened:{type:Boolean,observer:"__autoOpenedChanged"},_position:{type:String,value:"bottom"},__effectivePosition:{type:String,computed:"__computePosition(position, _position)"},__isTargetHidden:{type:Boolean,value:!1},_isConnected:{type:Boolean}}}static get observers(){return["__generatorChanged(_overlayElement, generator, context)"]}static setDefaultFocusDelay(e){U=null!=e&&e>=0?e:B}static setDefaultHideDelay(e){H=null!=e&&e>=0?e:B}static setDefaultHoverDelay(e){G=null!=e&&e>=0?e:B}constructor(){super(),this._uniqueId=`vaadin-tooltip-${u()}`,this._renderer=this.__tooltipRenderer.bind(this),this.__onFocusin=this.__onFocusin.bind(this),this.__onFocusout=this.__onFocusout.bind(this),this.__onMouseDown=this.__onMouseDown.bind(this),this.__onMouseEnter=this.__onMouseEnter.bind(this),this.__onMouseLeave=this.__onMouseLeave.bind(this),this.__onKeyDown=this.__onKeyDown.bind(this),this.__onOverlayOpen=this.__onOverlayOpen.bind(this),this.__targetVisibilityObserver=new IntersectionObserver((e=>{e.forEach((e=>this.__onTargetVisibilityChange(e.isIntersecting)))}),{threshold:0}),this._stateController=new W(this)}connectedCallback(){super.connectedCallback(),this._isConnected=!0,document.body.addEventListener("vaadin-overlay-open",this.__onOverlayOpen)}disconnectedCallback(){super.disconnectedCallback(),this._autoOpened&&this._stateController.close(!0),this._isConnected=!1,document.body.removeEventListener("vaadin-overlay-open",this.__onOverlayOpen)}__computeHorizontalAlign(e){return["top-end","bottom-end","start-top","start","start-bottom"].includes(e)?"end":"start"}__computeNoHorizontalOverlap(e){return["start-top","start","start-bottom","end-top","end","end-bottom"].includes(e)}__computeNoVerticalOverlap(e){return["top-start","top-end","top","bottom-start","bottom","bottom-end"].includes(e)}__computeVerticalAlign(e){return["top-start","top-end","top","start-bottom","end-bottom"].includes(e)?"bottom":"top"}__computeOpened(e,t,i,s){return s&&(e?t:i)}__computePosition(e,t){return e||t}__tooltipRenderer(e){e.textContent="function"==typeof this.generator?this.generator(this.context):this.text}__autoOpenedChanged(e,t){e?document.addEventListener("keydown",this.__onKeyDown,!0):t&&document.removeEventListener("keydown",this.__onKeyDown,!0)}__forChanged(e){e&&(this.__setTargetByIdDebouncer=m.debounce(this.__setTargetByIdDebouncer,g,(()=>this.__setTargetById(e))))}__setTargetById(e){if(!this.isConnected)return;const t=this.getRootNode().getElementById(e);t?this.target=t:console.warn(`No element with id="${e}" found to show tooltip.`)}__targetChanged(e,t){t&&(t.removeEventListener("mouseenter",this.__onMouseEnter),t.removeEventListener("mouseleave",this.__onMouseLeave),t.removeEventListener("focusin",this.__onFocusin),t.removeEventListener("focusout",this.__onFocusout),t.removeEventListener("mousedown",this.__onMouseDown),this.__targetVisibilityObserver.unobserve(t),_(t,"aria-describedby",this._uniqueId)),e&&(e.addEventListener("mouseenter",this.__onMouseEnter),e.addEventListener("mouseleave",this.__onMouseLeave),e.addEventListener("focusin",this.__onFocusin),e.addEventListener("focusout",this.__onFocusout),e.addEventListener("mousedown",this.__onMouseDown),requestAnimationFrame((()=>{this.__targetVisibilityObserver.observe(e)})),b(e,"aria-describedby",this._uniqueId))}__onFocusin(e){this.manual||v()&&(this.target.contains(e.relatedTarget)||this.__isShouldShow()&&(this.__focusInside=!0,this.__isTargetHidden||this.__hoverInside&&this._autoOpened||this._stateController.open({focus:!0})))}__onFocusout(e){this.manual||this.target.contains(e.relatedTarget)||(this.__focusInside=!1,this.__hoverInside||this._stateController.close(!0))}__onKeyDown(e){"Escape"===e.key&&(e.stopPropagation(),this._stateController.close(!0))}__onMouseDown(){this._stateController.close(!0)}__onMouseEnter(){this.manual||this.__isShouldShow()&&(this.__hoverInside||(this.__hoverInside=!0,this.__isTargetHidden||this.__focusInside&&this._autoOpened||this._stateController.open({hover:!0})))}__onMouseLeave(e){e.relatedTarget!==this._overlayElement&&this.__handleMouseLeave()}__onOverlayMouseLeave(e){e.relatedTarget!==this.target&&this.__handleMouseLeave()}__handleMouseLeave(){this.manual||(this.__hoverInside=!1,this.__focusInside||this._stateController.close())}__onOverlayOpen(){this.manual||this._overlayElement.opened&&!this._overlayElement._last&&this._stateController.close(!0)}__onTargetVisibilityChange(e){const t=this.__isTargetHidden;this.__isTargetHidden=!e,t&&e&&(this.__focusInside||this.__hoverInside)?this._stateController.open({immediate:!0}):!e&&this._autoOpened&&this._stateController.close(!0)}__isShouldShow(){return"function"!=typeof this.shouldShow||!0===this.shouldShow(this.target,this.context)}__textChanged(e,t){this._overlayElement&&(e||t)&&this._overlayElement.requestContentUpdate()}__generatorChanged(e,t,i){e&&(t===this.__oldTextGenerator&&i===this.__oldContext||e.requestContentUpdate(),this.__oldTextGenerator=t,this.__oldContext=i)}}var Z;customElements.define(Y.is,Y),function(e){e[e.EOS=0]="EOS",e[e.Text=1]="Text",e[e.Incomplete=2]="Incomplete",e[e.ESC=3]="ESC",e[e.Unknown=4]="Unknown",e[e.SGR=5]="SGR",e[e.OSCURL=6]="OSCURL"}(Z||(Z={}));var Q,X=function(){function e(){this.VERSION="4.0.3",this.setup_palettes(),this._use_classes=!1,this._escape_for_html=!0,this.bold=!1,this.fg=this.bg=null,this._buffer="",this._url_whitelist={http:1,https:1}}return Object.defineProperty(e.prototype,"use_classes",{get:function(){return this._use_classes},set:function(e){this._use_classes=e},enumerable:!0,configurable:!0}),Object.defineProperty(e.prototype,"escape_for_html",{get:function(){return this._escape_for_html},set:function(e){this._escape_for_html=e},enumerable:!0,configurable:!0}),Object.defineProperty(e.prototype,"url_whitelist",{get:function(){return this._url_whitelist},set:function(e){this._url_whitelist=e},enumerable:!0,configurable:!0}),e.prototype.setup_palettes=function(){var e=this;this.ansi_colors=[[{rgb:[0,0,0],class_name:"ansi-black"},{rgb:[187,0,0],class_name:"ansi-red"},{rgb:[0,187,0],class_name:"ansi-green"},{rgb:[187,187,0],class_name:"ansi-yellow"},{rgb:[0,0,187],class_name:"ansi-blue"},{rgb:[187,0,187],class_name:"ansi-magenta"},{rgb:[0,187,187],class_name:"ansi-cyan"},{rgb:[255,255,255],class_name:"ansi-white"}],[{rgb:[85,85,85],class_name:"ansi-bright-black"},{rgb:[255,85,85],class_name:"ansi-bright-red"},{rgb:[0,255,0],class_name:"ansi-bright-green"},{rgb:[255,255,85],class_name:"ansi-bright-yellow"},{rgb:[85,85,255],class_name:"ansi-bright-blue"},{rgb:[255,85,255],class_name:"ansi-bright-magenta"},{rgb:[85,255,255],class_name:"ansi-bright-cyan"},{rgb:[255,255,255],class_name:"ansi-bright-white"}]],this.palette_256=[],this.ansi_colors.forEach((function(t){t.forEach((function(t){e.palette_256.push(t)}))}));for(var t=[0,95,135,175,215,255],i=0;i<6;++i)for(var s=0;s<6;++s)for(var o=0;o<6;++o){var n={rgb:[t[i],t[s],t[o]],class_name:"truecolor"};this.palette_256.push(n)}for(var a=8,r=0;r<24;++r,a+=10){var l={rgb:[a,a,a],class_name:"truecolor"};this.palette_256.push(l)}},e.prototype.escape_txt_for_html=function(e){return e.replace(/[&<>]/gm,(function(e){return"&"===e?"&amp;":"<"===e?"&lt;":">"===e?"&gt;":void 0}))},e.prototype.append_buffer=function(e){var t=this._buffer+e;this._buffer=t},e.prototype.__makeTemplateObject=function(e,t){return Object.defineProperty?Object.defineProperty(e,"raw",{value:t}):e.raw=t,e},e.prototype.get_next_packet=function(){var e={kind:Z.EOS,text:"",url:""},t=this._buffer.length;if(0==t)return e;var i,s,o,n,a=this._buffer.indexOf("");if(-1==a)return e.kind=Z.Text,e.text=this._buffer,this._buffer="",e;if(a>0)return e.kind=Z.Text,e.text=this._buffer.slice(0,a),this._buffer=this._buffer.slice(a),e;if(0==a){if(1==t)return e.kind=Z.Incomplete,e;var r=this._buffer.charAt(1);if("["!=r&&"]"!=r)return e.kind=Z.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;if("["==r){if(this._csi_regex||(this._csi_regex=ee(this.__makeTemplateObject(["\n                        ^                           # beginning of line\n                                                    #\n                                                    # First attempt\n                        (?:                         # legal sequence\n                          [                      # CSI\n                          ([<-?]?)              # private-mode char\n                          ([d;]*)                    # any digits or semicolons\n                          ([ -/]?               # an intermediate modifier\n                          [@-~])                # the command\n                        )\n                        |                           # alternate (second attempt)\n                        (?:                         # illegal sequence\n                          [                      # CSI\n                          [ -~]*                # anything legal\n                          ([\0-:])              # anything illegal\n                        )\n                    "],["\n                        ^                           # beginning of line\n                                                    #\n                                                    # First attempt\n                        (?:                         # legal sequence\n                          \\x1b\\[                      # CSI\n                          ([\\x3c-\\x3f]?)              # private-mode char\n                          ([\\d;]*)                    # any digits or semicolons\n                          ([\\x20-\\x2f]?               # an intermediate modifier\n                          [\\x40-\\x7e])                # the command\n                        )\n                        |                           # alternate (second attempt)\n                        (?:                         # illegal sequence\n                          \\x1b\\[                      # CSI\n                          [\\x20-\\x7e]*                # anything legal\n                          ([\\x00-\\x1f:])              # anything illegal\n                        )\n                    "]))),null===(d=this._buffer.match(this._csi_regex)))return e.kind=Z.Incomplete,e;if(d[4])return e.kind=Z.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;""!=d[1]||"m"!=d[3]?e.kind=Z.Unknown:e.kind=Z.SGR,e.text=d[2];var l=d[0].length;return this._buffer=this._buffer.slice(l),e}if("]"==r){if(t<4)return e.kind=Z.Incomplete,e;if("8"!=this._buffer.charAt(2)||";"!=this._buffer.charAt(3))return e.kind=Z.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;this._osc_st||(this._osc_st=(i=this.__makeTemplateObject(["\n                        (?:                         # legal sequence\n                          (\\)                    # ESC                           |                           # alternate\n                          ()                      # BEL (what xterm did)\n                        )\n                        |                           # alternate (second attempt)\n                        (                           # illegal sequence\n                          [\0-]                 # anything illegal\n                          |                           # alternate\n                          [\b-]                 # anything illegal\n                          |                           # alternate\n                          [-]                 # anything illegal\n                        )\n                    "],["\n                        (?:                         # legal sequence\n                          (\\x1b\\\\)                    # ESC \\\n                          |                           # alternate\n                          (\\x07)                      # BEL (what xterm did)\n                        )\n                        |                           # alternate (second attempt)\n                        (                           # illegal sequence\n                          [\\x00-\\x06]                 # anything illegal\n                          |                           # alternate\n                          [\\x08-\\x1a]                 # anything illegal\n                          |                           # alternate\n                          [\\x1c-\\x1f]                 # anything illegal\n                        )\n                    "]),s=i.raw[0],o=/^\s+|\s+\n|\s*#[\s\S]*?\n|\n/gm,n=s.replace(o,""),new RegExp(n,"g"))),this._osc_st.lastIndex=0;var c=this._osc_st.exec(this._buffer);if(null===c)return e.kind=Z.Incomplete,e;if(c[3])return e.kind=Z.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;var d,p=this._osc_st.exec(this._buffer);if(null===p)return e.kind=Z.Incomplete,e;if(p[3])return e.kind=Z.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;if(this._osc_regex||(this._osc_regex=ee(this.__makeTemplateObject(["\n                        ^                           # beginning of line\n                                                    #\n                        ]8;                    # OSC Hyperlink\n                        [ -:<-~]*       # params (excluding ;)\n                        ;                           # end of params\n                        ([!-~]{0,512})        # URL capture\n                        (?:                         # ST\n                          (?:\\)                  # ESC                           |                           # alternate\n                          (?:)                    # BEL (what xterm did)\n                        )\n                        ([!-~]+)              # TEXT capture\n                        ]8;;                   # OSC Hyperlink End\n                        (?:                         # ST\n                          (?:\\)                  # ESC                           |                           # alternate\n                          (?:)                    # BEL (what xterm did)\n                        )\n                    "],["\n                        ^                           # beginning of line\n                                                    #\n                        \\x1b\\]8;                    # OSC Hyperlink\n                        [\\x20-\\x3a\\x3c-\\x7e]*       # params (excluding ;)\n                        ;                           # end of params\n                        ([\\x21-\\x7e]{0,512})        # URL capture\n                        (?:                         # ST\n                          (?:\\x1b\\\\)                  # ESC \\\n                          |                           # alternate\n                          (?:\\x07)                    # BEL (what xterm did)\n                        )\n                        ([\\x21-\\x7e]+)              # TEXT capture\n                        \\x1b\\]8;;                   # OSC Hyperlink End\n                        (?:                         # ST\n                          (?:\\x1b\\\\)                  # ESC \\\n                          |                           # alternate\n                          (?:\\x07)                    # BEL (what xterm did)\n                        )\n                    "]))),null===(d=this._buffer.match(this._osc_regex)))return e.kind=Z.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;e.kind=Z.OSCURL,e.url=d[1],e.text=d[2];l=d[0].length;return this._buffer=this._buffer.slice(l),e}}},e.prototype.ansi_to_html=function(e){this.append_buffer(e);for(var t=[];;){var i=this.get_next_packet();if(i.kind==Z.EOS||i.kind==Z.Incomplete)break;i.kind!=Z.ESC&&i.kind!=Z.Unknown&&(i.kind==Z.Text?t.push(this.transform_to_html(this.with_state(i))):i.kind==Z.SGR?this.process_ansi(i):i.kind==Z.OSCURL&&t.push(this.process_hyperlink(i)))}return t.join("")},e.prototype.with_state=function(e){return{bold:this.bold,fg:this.fg,bg:this.bg,text:e.text}},e.prototype.process_ansi=function(e){for(var t=e.text.split(";");t.length>0;){var i=t.shift(),s=parseInt(i,10);if(isNaN(s)||0===s)this.fg=this.bg=null,this.bold=!1;else if(1===s)this.bold=!0;else if(22===s)this.bold=!1;else if(39===s)this.fg=null;else if(49===s)this.bg=null;else if(s>=30&&s<38)this.fg=this.ansi_colors[0][s-30];else if(s>=40&&s<48)this.bg=this.ansi_colors[0][s-40];else if(s>=90&&s<98)this.fg=this.ansi_colors[1][s-90];else if(s>=100&&s<108)this.bg=this.ansi_colors[1][s-100];else if((38===s||48===s)&&t.length>0){var o=38===s,n=t.shift();if("5"===n&&t.length>0){var a=parseInt(t.shift(),10);a>=0&&a<=255&&(o?this.fg=this.palette_256[a]:this.bg=this.palette_256[a])}if("2"===n&&t.length>2){var r=parseInt(t.shift(),10),l=parseInt(t.shift(),10),c=parseInt(t.shift(),10);if(r>=0&&r<=255&&l>=0&&l<=255&&c>=0&&c<=255){var d={rgb:[r,l,c],class_name:"truecolor"};o?this.fg=d:this.bg=d}}}}},e.prototype.transform_to_html=function(e){var t=e.text;if(0===t.length)return t;if(this._escape_for_html&&(t=this.escape_txt_for_html(t)),!e.bold&&null===e.fg&&null===e.bg)return t;var i=[],s=[],o=e.fg,n=e.bg;e.bold&&i.push("font-weight:bold"),this._use_classes?(o&&("truecolor"!==o.class_name?s.push(o.class_name+"-fg"):i.push("color:rgb("+o.rgb.join(",")+")")),n&&("truecolor"!==n.class_name?s.push(n.class_name+"-bg"):i.push("background-color:rgb("+n.rgb.join(",")+")"))):(o&&i.push("color:rgb("+o.rgb.join(",")+")"),n&&i.push("background-color:rgb("+n.rgb+")"));var a="",r="";return s.length&&(a=' class="'+s.join(" ")+'"'),i.length&&(r=' style="'+i.join(";")+'"'),"<span"+r+a+">"+t+"</span>"},e.prototype.process_hyperlink=function(e){var t=e.url.split(":");return t.length<1?"":this._url_whitelist[t[0]]?'<a href="'+this.escape_txt_for_html(e.url)+'">'+this.escape_txt_for_html(e.text)+"</a>":""},e}();function ee(e){var t=e.raw[0].replace(/^\s+|\s+\n|\s*#[\s\S]*?\n|\n/gm,"");return new RegExp(t)}let te=Q=class extends x{constructor(){super(),this.active=!1,this.condition="running",this.jobs=Object(),this.compute_sessions=[],this.filterAccessKey="",this.sessionNameField="name",this.appSupportList=[],this.appTemplate=Object(),this.imageInfo=Object(),this._boundControlRenderer=this.controlRenderer.bind(this),this._boundConfigRenderer=this.configRenderer.bind(this),this._boundUsageRenderer=this.usageRenderer.bind(this),this._boundReservationRenderer=this.reservationRenderer.bind(this),this._boundIdleChecksHeaderderer=this.idleChecksHeaderRenderer.bind(this),this._boundIdleChecksRenderer=this.idleChecksRenderer.bind(this),this._boundAgentRenderer=this.agentRenderer.bind(this),this._boundSessionInfoRenderer=this.sessionInfoRenderer.bind(this),this._boundArchitectureRenderer=this.architectureRenderer.bind(this),this._boundCheckboxRenderer=this.checkboxRenderer.bind(this),this._boundUserInfoRenderer=this.userInfoRenderer.bind(this),this._boundStatusRenderer=this.statusRenderer.bind(this),this._boundSessionTypeRenderer=this.sessionTypeRenderer.bind(this),this.refreshing=!1,this.is_admin=!1,this.is_superadmin=!1,this._connectionMode="API",this.notification=Object(),this.enableScalingGroup=!1,this.isDisplayingAllocatedShmemEnabled=!1,this.listCondition="loading",this.refreshTimer=Object(),this.kernel_labels=Object(),this.kernel_icons=Object(),this.indicator=Object(),this._helpDescription="",this._helpDescriptionTitle="",this._helpDescriptionIcon="",this.statusColorTable=new Proxy({"idle-timeout":"green","user-requested":"green",scheduled:"green","failed-to-start":"red","creation-failed":"red","self-terminated":"green"},{get:(e,t)=>e.hasOwnProperty(t)?e[t]:"lightgrey"}),this.idleChecksTable=new Proxy({network_timeout:"NetworkIdleTimeout",session_lifetime:"MaxSessionLifetime",utilization:"UtilizationIdleTimeout",expire_after:"ExpiresAfter",grace_period:"GracePeriod",cpu_util:"CPU",mem:"MEM",cuda_util:"GPU",cuda_mem:"GPU(MEM)"},{get:(e,t)=>e.hasOwnProperty(t)?e[t]:""}),this.sessionTypeColorTable=new Proxy({INTERACTIVE:"green",BATCH:"darkgreen",INFERENCE:"blue"},{get:(e,t)=>e.hasOwnProperty(t)?e[t]:"lightgrey"}),this.sshPort=0,this.vncPort=0,this.current_page=1,this.session_page_limit=50,this.total_session_count=0,this._APIMajorVersion=5,this.selectedSessionStatus=Object(),this.isUserInfoMaskEnabled=!1,this._isContainerCommitEnabled=!1,this.getUtilizationCheckerColor=(e,t=null)=>{const i="#527A42",s="#D8B541",o="#e05d44";if(t){let n=i;return"and"===t?Object.values(e).every((([e,t])=>e<Math.min(2*t,t+5)))?n=o:Object.values(e).every((([e,t])=>e<Math.min(10*t,t+10)))&&(n=s):"or"===t&&(Object.values(e).some((([e,t])=>e<Math.min(2*t,t+5)))?n=o:Object.values(e).some((([e,t])=>e<Math.min(10*t,t+10)))&&(n=s)),n}{const[t,n]=e;return t<2*n?o:t<10*n?s:i}},this._selected_items=[],this.terminationQueue=[],this.activeIdleCheckList=new Set}static get styles(){return[A,S,T,i`
        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 265px);
        }

        wl-icon.indicator {
          --icon-size: 16px;
        }

        wl-icon.pagination {
          color: var(--paper-grey-700);
        }

        wl-button.pagination[disabled] wl-icon.pagination {
          color: var(--paper-grey-300);
        }

        wl-icon.warning {
          color: red;
        }

        wl-expansion {
          --expansion-elevation: 0;
          --expansion-elevation-open: 0;
          --expansion-elevation-hover: 0;
          --expansion-margin-open: 0;
          --expansion-content-padding: 0;
          --expansion-header-padding: 5px;
          width: 100%;
        }

        wl-button.pagination {
          width: 15px;
          height: 15px;
          padding: 10px;
          box-shadow: 0px 2px 2px rgba(0, 0, 0, 0.2);
          --button-bg: transparent;
          --button-bg-hover: var(--paper-red-100);
          --button-bg-active: var(--paper-red-600);
          --button-bg-active-flat: var(--paper-red-600);
          --button-bg-disabled: var(--paper-grey-50);
          --button-color-disabled: var(--paper-grey-200);
        }

        wl-button.pagination[disabled] {
          --button-shadow-color: transparent;
        }

        wl-button.controls-running {
          --button-fab-size: 32px;
          --button-padding: 3px;
          margin-right: 5px;
        }

        img.indicator-icon {
          width: 16px;
          height: 16px;
          padding-right: 5px;
        }

        mwc-icon {
          margin-right: 5px;
        }

        mwc-icon.status-check {
          --mdc-icon-size: 16px;
        }

        mwc-icon-button.apps {
          --mdc-icon-button-size: 48px;
          --mdc-icon-size: 36px;
          padding: 3px;
          margin-right: 5px;
        }

        mwc-icon-button.status {
          --mdc-icon-button-size: 36px;
          padding: 0;
        }

        mwc-list-item {
          --mdc-typography-body2-font-size: 12px;
          --mdc-list-item-graphic-margin: 10px;
        }

        mwc-textfield {
          width: 100%;
        }

        lablup-shields.right-below-margin {
          margin-right: 3px;
          margin-bottom: 3px;
        }

        #work-dialog {
          --component-width: calc(100% - 80px);
          --component-height: auto;
          right: 0;
          top: 50px;
        }

        #status-detail-dialog {
          --component-width: 375px;
        }

        #commit-session-dialog {
          --component-width: 390px;
        }

        @media screen and (max-width: 899px) {
          #work-dialog,
          #work-dialog.mini_ui {
            left: 0;
            --component-width: 95%;
          }
        }

        @media screen and (min-width: 900px) {
          #work-dialog {
            left: 100px;
          }

          #work-dialog.mini_ui {
            left: 40px;
          }
        }

        #work-area {
          width: 100%;
          padding: 5px;
          font-size:12px;
          line-height: 12px;
          height: calc(100vh - 120px);
          background-color: #222222;
          color: #efefef;
        }

        #work-area pre {
          white-space: pre-wrap;
          white-space: -moz-pre-wrap;
          white-space: -pre-wrap;
          white-space: -o-pre-wrap;
          word-wrap: break-word;
        }

        #help-description {
          --component-max-width: 70vw;
        }

        #help-description p, #help-description strong {
          padding: 5px 30px !important;
        }

        div.indicator,
        span.indicator {
          font-size: 9px;
          margin-right: 5px;
        }

        div.label,
        span.label {
          font-size: 12px;
        }

        div.configuration {
          width: 90px !important;
          height: 20px;
        }

        div.configuration wl-icon {
          padding-right: 5px;
        }

        span.subheading {
          color: #666;
          font-weight: bold;
        }

        mwc-list-item.commit-session-info {
          height: 100%;
        }

        mwc-list-item.predicate-check {
          height: 100%;
          margin-bottom: 5px;
        }

        .predicate-check-comment {
          white-space: pre-wrap;
        }

        .error-description {
          font-size: 0.8rem;
          word-break: break-word;
        }

        wl-button.multiple-action-button {
          --button-color: var(--paper-red-600);
          --button-color-active: red;
          --button-color-hover: red;
          --button-bg: var(--paper-red-50);
          --button-bg-hover: var(--paper-red-100);
          --button-bg-active: var(--paper-red-600);
          --button-bg-active-flat: var(--paper-red-600);
        }

        wl-label {
          width: 100%;
          background-color: var(--paper-grey-500);
          min-width: 60px;
          font-size: 12px;
          --label-font-family: 'Ubuntu', Roboto;
        }

        lablup-progress-bar.usage {
          --progress-bar-height: 5px;
          --progress-bar-width: 60px;
          margin-bottom: 0;
        }

        div.filters #access-key-filter {
          --input-font-size: small;
          --input-label-font-size: small;
          --input-font-family: var(--general-font-family);
        }

        .mount-button,
        .status-button,
        .idle-check-key {
          border: none;
          background: none;
          padding: 0;
          outline-style: none;
        }

        .no-mount {
          color: var(--paper-grey-400);
        }

        .idle-check-key {
          font-size: 12px;
          font-weight: 500;
        }

        .idle-type {
          font-size: 11px;
          color: var(--paper-grey-600);
          font-weight: 400;
        }

        span#access-key-filter-helper-text {
          margin-top: 3px;
          font-size: 10px;
          color: var(--general-menu-color-2);
        }

        div.usage-items {
          font-size: 8px;
          width: 55px;
        }
      `]}get _isRunning(){return["batch","interactive","inference","system","running","others"].includes(this.condition)}get _isIntegratedCondition(){return["running","finished","others"].includes(this.condition)}_isPreparing(e){return-1!==["RESTARTING","PREPARING","PULLING"].indexOf(e)}_isError(e){return"ERROR"===e}_isPending(e){return"PENDING"===e}_isFinished(e){return["TERMINATED","CANCELLED","TERMINATING"].includes(e)}firstUpdated(){this.imageInfo=globalThis.backendaimetadata.imageInfo,this.kernel_icons=globalThis.backendaimetadata.icons,this.kernel_labels=globalThis.backendaimetadata.kernel_labels,document.addEventListener("backend-ai-metadata-image-loaded",(()=>{this.imageInfo=globalThis.backendaimetadata.imageInfo,this.kernel_icons=globalThis.backendaimetadata.icons,this.kernel_labels=globalThis.backendaimetadata.kernel_labels}),{once:!0}),this.refreshTimer=null,this.notification=globalThis.lablupNotification,this.indicator=globalThis.lablupIndicator,document.addEventListener("backend-ai-group-changed",(e=>this.refreshList(!0,!1))),document.addEventListener("backend-ai-ui-changed",(e=>this._refreshWorkDialogUI(e))),document.addEventListener("backend-ai-clear-timeout",(()=>{clearTimeout(this.refreshTimer)})),this._refreshWorkDialogUI({detail:{"mini-ui":globalThis.mini_ui}})}async _viewStateChanged(e){var t;await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{var e;globalThis.backendaiclient.is_admin?this.accessKeyFilterInput.style.display="block":(this.accessKeyFilterInput.style.display="none",this.accessKeyFilterHelperText.style.display="none",(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("vaadin-grid")).style.height="calc(100vh - 225px)!important"),globalThis.backendaiclient.APIMajorVersion<5&&(this.sessionNameField="sess_id"),this.is_admin=globalThis.backendaiclient.is_admin,this.is_superadmin=globalThis.backendaiclient.is_superadmin,this._connectionMode=globalThis.backendaiclient._config._connectionMode,this.enableScalingGroup=globalThis.backendaiclient.supports("scaling-group"),this.isDisplayingAllocatedShmemEnabled=globalThis.backendaiclient.supports("display-allocated-shmem"),this._APIMajorVersion=globalThis.backendaiclient.APIMajorVersion,this.isUserInfoMaskEnabled=globalThis.backendaiclient._config.maskUserInfo,this._isContainerCommitEnabled=globalThis.backendaiclient._config.enableContainerCommit&&globalThis.backendaiclient.supports("image-commit"),this._refreshJobData()}),!0):(globalThis.backendaiclient.is_admin?(this.accessKeyFilterInput.style.display="block",this.accessKeyFilterHelperText.style.display="block"):(this.accessKeyFilterInput.style.display="none",this.accessKeyFilterHelperText.style.display="none",(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("vaadin-grid")).style.height="calc(100vh - 225px)!important"),globalThis.backendaiclient.APIMajorVersion<5&&(this.sessionNameField="sess_id"),this.is_admin=globalThis.backendaiclient.is_admin,this.is_superadmin=globalThis.backendaiclient.is_superadmin,this._connectionMode=globalThis.backendaiclient._config._connectionMode,this.enableScalingGroup=globalThis.backendaiclient.supports("scaling-group"),this.isDisplayingAllocatedShmemEnabled=globalThis.backendaiclient.supports("display-allocated-shmem"),this._APIMajorVersion=globalThis.backendaiclient.APIMajorVersion,this.isUserInfoMaskEnabled=globalThis.backendaiclient._config.maskUserInfo,this._isContainerCommitEnabled=globalThis.backendaiclient._config.enableContainerCommit&&globalThis.backendaiclient.supports("image-commit"),this._refreshJobData()))}async refreshList(e=!0,t=!0){return this._refreshJobData(e,t)}async _refreshJobData(e=!1,t=!0){if(await this.updateComplete,!0!==this.active)return;if(!0===this.refreshing)return;let i;switch(this.refreshing=!0,i="RUNNING",this.condition){case"running":case"interactive":case"system":case"batch":case"inference":case"others":i=["RUNNING","RESTARTING","TERMINATING","PENDING","SCHEDULED","PREPARING","PULLING","ERROR"];break;case"finished":i=["TERMINATED","CANCELLED"];break;default:i=["RUNNING","RESTARTING","TERMINATING","PENDING","SCHEDULED","PREPARING","PULLING"]}!globalThis.backendaiclient.supports("avoid-hol-blocking")&&i.includes("SCHEDULED")&&(i=i.filter((e=>"SCHEDULED"!==e))),globalThis.backendaiclient.supports("detailed-session-states")&&(i=i.join(","));const s=["id","session_id","name","image","architecture","created_at","terminated_at","status","status_info","service_ports","mounts","resource_opts","occupied_slots","access_key","starts_at","type"];globalThis.backendaiclient.supports("multi-container")&&s.push("cluster_size"),globalThis.backendaiclient.supports("multi-node")&&s.push("cluster_mode"),globalThis.backendaiclient.supports("session-detail-status")&&s.push("status_data"),globalThis.backendaiclient.supports("idle-checks")&&s.push("idle_checks"),globalThis.backendaiclient.supports("inference-workload")&&s.push("inference_metrics"),globalThis.backendaiclient.supports("sftp-scaling-group")&&s.push("main_kernel_role"),this.enableScalingGroup&&s.push("scaling_group"),"SESSION"===this._connectionMode&&s.push("user_email"),globalThis.backendaiclient.is_superadmin?s.push("containers {container_id agent occupied_slots live_stat last_stat}"):s.push("containers {container_id occupied_slots live_stat last_stat}"),globalThis.backendaiclient._config.hideAgents||s.push("containers {agent}");const o=globalThis.backendaiclient.current_group_id();this._isContainerCommitEnabled&&i.includes("RUNNING")&&s.push("commit_status"),globalThis.backendaiclient.computeSession.list(s,i,this.filterAccessKey,this.session_page_limit,(this.current_page-1)*this.session_page_limit,o,1e4).then((i=>{var s,o,n;this.total_session_count=i.compute_session_list.total_count;let a,r=i.compute_session_list.items;if(0===this.total_session_count?(this.listCondition="no-data",null===(s=this._listStatus)||void 0===s||s.show(),this.total_session_count=1):["interactive","batch","inference"].includes(this.condition)&&0===r.filter((e=>e.type.toLowerCase()===this.condition)).length||"system"===this.condition&&0===r.filter((e=>e.main_kernel_role.toLowerCase()===this.condition)).length?(this.listCondition="no-data",null===(o=this._listStatus)||void 0===o||o.show()):null===(n=this._listStatus)||void 0===n||n.hide(),void 0!==r&&0!=r.length){const e=this.compute_sessions,t=[];Object.keys(e).map(((i,s)=>{t.push(e[i].session_id)})),Object.keys(r).map(((e,t)=>{var i,s,o;const n=r[e],a=JSON.parse(n.occupied_slots),l=r[e].image.split("/")[2]||r[e].image.split("/")[1];if(r[e].cpu_slot=parseInt(a.cpu),r[e].mem_slot=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(a.mem,"g")),r[e].mem_slot=r[e].mem_slot.toFixed(2),r[e].elapsed=this._elapsed(r[e].created_at,r[e].terminated_at),r[e].created_at_hr=this._humanReadableTime(r[e].created_at),r[e].starts_at_hr=r[e].starts_at?this._humanReadableTime(r[e].starts_at):"",globalThis.backendaiclient.supports("idle-checks")){const t=JSON.parse(n.idle_checks||"{}");t&&(r[e].idle_checks=t),t&&t.network_timeout&&t.network_timeout.remaining&&(r[e].idle_checks.network_timeout.remaining=Q.secondsToDHMS(t.network_timeout.remaining),null===(i=this.activeIdleCheckList)||void 0===i||i.add("network_timeout")),t&&t.session_lifetime&&t.session_lifetime.remaining&&(r[e].idle_checks.session_lifetime.remaining=Q.secondsToDHMS(t.session_lifetime.remaining),null===(s=this.activeIdleCheckList)||void 0===s||s.add("session_lifetime")),t&&t.utilization&&t.utilization.remaining&&(r[e].idle_checks.utilization.remaining=Q.secondsToDHMS(t.utilization.remaining),null===(o=this.activeIdleCheckList)||void 0===o||o.add("utilization"))}if(r[e].containers&&r[e].containers.length>0){const t=r[e].containers[0],i=t.live_stat?JSON.parse(t.live_stat):null;r[e].agent=t.agent,i&&i.cpu_used?r[e].cpu_used_time=this._automaticScaledTime(i.cpu_used.current):r[e].cpu_used_time=this._automaticScaledTime(0),i&&i.cpu_util?r[e].cpu_util=i.cpu_util.current:r[e].cpu_util=0,i&&i.mem?r[e].mem_current=i.mem.current:r[e].mem_current=0,i&&i.io_read?r[e].io_read_bytes_mb=Q.bytesToMB(i.io_read.current):r[e].io_read_bytes_mb=0,i&&i.io_write?r[e].io_write_bytes_mb=Q.bytesToMB(i.io_write.current):r[e].io_write_bytes_mb=0,i&&i.cuda_util?r[e].cuda_util=i.cuda_util.current:r[e].cuda_util=0,i&&i.rocm_util?r[e].rocm_util=i.rocm_util:r[e].rocm_util=0,i&&i.tpu_util?r[e].tpu_util=i.tpu_util:r[e].tpu_util=0,i&&i.ipu_util?r[e].ipu_util=i.ipu_util:r[e].ipu_util=0,i&&i.atom_util?r[e].atom_util=i.atom_util:r[e].atom_util=0,i&&i.cuda_mem?r[e].cuda_mem_ratio=i.cuda_mem.current/i.cuda_mem.capacity||0:r[e].cuda_mem_ratio=null}const c=JSON.parse(r[e].service_ports);!0===Array.isArray(c)?(r[e].app_services=c.map((e=>e.name)),r[e].app_services_option={},c.forEach((t=>{"allowed_arguments"in t&&(r[e].app_services_option[t.name]=t.allowed_arguments)}))):(r[e].app_services=[],r[e].app_services_option={}),0!==r[e].app_services.length&&["batch","interactive","inference","system","running"].includes(this.condition)?r[e].appSupport=!0:r[e].appSupport=!1,["batch","interactive","inference","system","running"].includes(this.condition)?r[e].running=!0:r[e].running=!1,"cuda.device"in a&&(r[e].cuda_gpu_slot=parseInt(a["cuda.device"])),"rocm.device"in a&&(r[e].rocm_gpu_slot=parseInt(a["rocm.device"])),"tpu.device"in a&&(r[e].tpu_slot=parseInt(a["tpu.device"])),"ipu.device"in a&&(r[e].ipu_slot=parseInt(a["ipu.device"])),"atom.device"in a&&(r[e].atom_slot=parseInt(a["atom.device"])),"warboy.device"in a&&(r[e].warboy_slot=parseInt(a["warboy.device"])),"cuda.shares"in a&&(r[e].cuda_fgpu_slot=parseFloat(a["cuda.shares"]).toFixed(2)),r[e].kernel_image=l,r[e].icon=this._getKernelIcon(n.image),r[e].sessionTags=this._getKernelInfo(n.image);const d=n.image.split("/");r[e].cluster_size=parseInt(r[e].cluster_size);const p=d[d.length-1].split(":")[1],h=p.split("-");void 0!==h[1]?(r[e].baseversion=h[0],r[e].baseimage=h[1],r[e].additional_reqs=h.slice(1,h.length).map((e=>e.toUpperCase()))):void 0!==r[e].tag?r[e].baseversion=r[e].tag:r[e].baseversion=p,this._selected_items.includes(r[e].session_id)?r[e].checked=!0:r[e].checked=!1}))}if(["batch","interactive","inference"].includes(this.condition)){const e=r.reduce(((e,t)=>("SYSTEM"!==t.main_kernel_role&&e[t.type.toLowerCase()].push(t),e)),{batch:[],interactive:[],inference:[]});r=e[this.condition]}else r="system"===this.condition?r.filter((e=>"SYSTEM"===e.main_kernel_role)):r.filter((e=>"SYSTEM"!==e.main_kernel_role));if(this.compute_sessions=r,this._grid.recalculateColumnWidths(),this.requestUpdate(),this.refreshing=!1,!0===this.active){if(!0===e){const e=new CustomEvent("backend-ai-resource-refreshed",{detail:{}});document.dispatchEvent(e)}!0===t&&(a=["batch","interactive","inference","system","running"].includes(this.condition)?7e3:3e4,this.refreshTimer=setTimeout((()=>{this._refreshJobData()}),a))}})).catch((e=>{var i;if(this.refreshing=!1,this.active&&t){const e=["batch","interactive","inference","system","running"].includes(this.condition)?2e4:12e4;this.refreshTimer=setTimeout((()=>{this._refreshJobData()}),e)}null===(i=this._listStatus)||void 0===i||i.hide(),console.log(e),e&&e.message&&(this.notification.text=$.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_refreshWorkDialogUI(e){Object.prototype.hasOwnProperty.call(e.detail,"mini-ui")&&!0===e.detail["mini-ui"]?this.workDialog.classList.add("mini_ui"):this.workDialog.classList.remove("mini_ui")}_humanReadableTime(e){return(e=new Date(e)).toLocaleString()}_getKernelInfo(e){const t=[];if(void 0===e)return[];const i=e.split("/"),s=(i[2]||i[1]).split(":")[0];if(s in this.kernel_labels)t.push(this.kernel_labels[s]);else{const i=e.split("/");let s,o;3===i.length?(s=i[1],o=i[2]):i.length>3?(s=i.slice(2,i.length-1).join("/"),o=i[i.length-1]):(s="",o=i[1]),o=o.split(":")[0],o=s?s+"/"+o:o,t.push([{category:"Env",tag:`${o}`,color:"lightgrey"}])}return t}_getKernelIcon(e){if(void 0===e)return[];const t=e.split("/"),i=(t[2]||t[1]).split(":")[0];return i in this.kernel_icons?this.kernel_icons[i]:""}_automaticScaledTime(e){let t=Object();const i=["D","H","M","S"],s=[864e5,36e5,6e4,1e3];for(let o=0;o<s.length;o++)Math.floor(e/s[o])>0&&(t[i[o]]=Math.floor(e/s[o]),e%=s[o]);return 0===Object.keys(t).length&&(t=e>0?{MS:e}:{NODATA:1}),t}static bytesToMB(e,t=1){return Number(e/10**6).toFixed(1)}static bytesToGiB(e,t=2){return e?(e/2**30).toFixed(t):e}_elapsed(e,t){return globalThis.backendaiclient.utils.elapsedTime(e,t)}_indexRenderer(e,t,i){const s=i.index+1;C(I`
        <div>${s}</div>
      `,e)}async sendRequest(e){let t,i;try{"GET"==e.method&&(e.body=void 0),t=await fetch(e.uri,e);const s=t.headers.get("Content-Type");if(i=s.startsWith("application/json")||s.startsWith("application/problem+json")?await t.json():s.startsWith("text/")?await t.text():await t.blob(),!t.ok)throw i}catch(e){}return i}async _terminateApp(e){const t=globalThis.backendaiclient._config.accessKey,i=await globalThis.appLauncher._getProxyURL(e),s={method:"GET",uri:new URL(`proxy/${t}/${e}`,i).href};return this.sendRequest(s).then((s=>{if(this.total_session_count-=1,void 0!==s&&404!==s.code){const s={method:"GET",uri:new URL(`proxy/${t}/${e}/delete`,i).href,credentials:"include",mode:"cors"};return this.sendRequest(s)}return Promise.resolve(!0)})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=$.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_getProxyToken(){let e="local";return void 0!==globalThis.backendaiclient._config.proxyToken&&(e=globalThis.backendaiclient._config.proxyToken),e}_showLogs(e){const t=e.target.closest("#controls"),i=t["session-uuid"],s=t["session-name"],o=globalThis.backendaiclient.APIMajorVersion<5?s:i,n=t["access-key"];globalThis.backendaiclient.get_logs(o,n,15e3).then((e=>{const t=(new X).ansi_to_html(e.result.logs);setTimeout((()=>{var e,o;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#work-title")).innerHTML=`${s} (${i})`,(null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("#work-area")).innerHTML=`<pre>${t}</pre>`||D("session.NoLogs"),this.workDialog.sessionUuid=i,this.workDialog.sessionName=s,this.workDialog.accessKey=n,this.workDialog.show()}),100)})).catch((e=>{e&&e.message?(this.notification.text=$.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=$.relieve(e.title),this.notification.show(!0,e))}))}_downloadLogs(){const e=this.workDialog.sessionUuid,t=this.workDialog.sessionName,i=globalThis.backendaiclient.APIMajorVersion<5?t:e,s=this.workDialog.accessKey;globalThis.backendaiclient.get_logs(i,s,15e3).then((e=>{const i=e.result.logs;globalThis.backendaiutils.exportToTxt(t,i),this.notification.text=D("session.DownloadingSessionLogs"),this.notification.show()})).catch((e=>{e&&e.message?(this.notification.text=$.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=$.relieve(e.title),this.notification.show(!0,e))}))}_refreshLogs(){const e=this.workDialog.sessionUuid,t=this.workDialog.sessionName,i=globalThis.backendaiclient.APIMajorVersion<5?t:e,s=this.workDialog.accessKey;globalThis.backendaiclient.get_logs(i,s,15e3).then((e=>{var t;const i=(new X).ansi_to_html(e.result.logs);(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#work-area")).innerHTML=`<pre>${i}</pre>`||D("session.NoLogs")})).catch((e=>{e&&e.message?(this.notification.text=$.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=$.relieve(e.title),this.notification.show(!0,e))}))}_showAppLauncher(e){const t=e.target.closest("#controls");return globalThis.appLauncher.showLauncher(t)}async _runTerminal(e){const t=e.target.closest("#controls")["session-uuid"];return globalThis.appLauncher.runTerminal(t)}async _getCommitSessionStatus(e=""){let t=!1;return""!==e&&globalThis.backendaiclient.computeSession.getCommitSessionStatus(e).then((e=>{t=e})).catch((e=>{console.log(e)})),t}async _requestCommitSession(e){try{const t=await globalThis.backendaiclient.computeSession.commitSession(e.session.name),i=Object.assign(e,{taskId:t.bgtask_id});this._addCommitSessionToTasker(t,i),this._applyContainerCommitAsBackgroundTask(i),this.notification.text=D("session.CommitOnGoing"),this.notification.show()}catch(e){console.log(e),e&&e.message&&(this.notification.text=$.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}finally{this.commitSessionDialog.hide()}}_applyContainerCommitAsBackgroundTask(e){const t=globalThis.backendaiclient.maintenance.attach_background_task(e.taskId);t.addEventListener("bgtask_done",(i=>{this.notification.text=D("session.CommitFinished"),this.notification.show(),this._removeCommitSessionFromTasker(e.taskId),t.close()})),t.addEventListener("bgtask_failed",(i=>{throw this.notification.text=D("session.CommitFailed"),this.notification.show(!0),this._removeCommitSessionFromTasker(e.taskId),t.close(),new Error("Commit session request has been failed.")})),t.addEventListener("bgtask_cancelled",(i=>{throw this.notification.text=D("session.CommitFailed"),this.notification.show(!0),this._removeCommitSessionFromTasker(e.taskId),t.close(),new Error("Commit session request has been cancelled.")}))}_addCommitSessionToTasker(e=null,t){var i;globalThis.tasker.add(D("session.CommitSession")+t.session.name,null!==e&&"function"==typeof e?e:null,null!==(i=t.taskId)&&void 0!==i?i:"","commit","remove-later")}_removeCommitSessionFromTasker(e=""){globalThis.tasker.remove(e)}_getCurrentContainerCommitInfoListFromLocalStorage(){return JSON.parse(localStorage.getItem("backendaiwebui.settings.user.container_commit_sessions")||"[]")}_saveCurrentContainerCommitInfoToLocalStorage(e){const t=this._getCurrentContainerCommitInfoListFromLocalStorage();t.push(e),globalThis.backendaioptions.set("container_commit_sessions",JSON.stringify(t))}_removeFinishedContainerCommitInfoFromLocalStorage(e="",t=""){let i=this._getCurrentContainerCommitInfoListFromLocalStorage();i=i.filter((i=>i.session.id!==e&&i.taskId!==t)),globalThis.backendaioptions.set("container_commit_sessions",JSON.stringify(i))}_openCommitSessionDialog(e){const t=e.target.closest("#controls"),i=t["session-name"],s=t["session-uuid"],o=t["kernel-image"];this.commitSessionDialog.sessionName=i,this.commitSessionDialog.sessionId=s,this.commitSessionDialog.kernelImage=o,this.commitSessionDialog.show()}_openTerminateSessionDialog(e){const t=e.target.closest("#controls"),i=t["session-name"],s=t["session-uuid"],o=t["access-key"];this.terminateSessionDialog.sessionName=i,this.terminateSessionDialog.sessionId=s,this.terminateSessionDialog.accessKey=o,this.terminateSessionDialog.show()}_terminateSession(e){const t=e.target.closest("#controls"),i=t["session-uuid"],s=t["access-key"];return this.terminationQueue.includes(i)?(this.notification.text=D("session.AlreadyTerminatingSession"),this.notification.show(),!1):this._terminateKernel(i,s)}_terminateSessionWithCheck(e=!1){var t;return this.terminationQueue.includes(this.terminateSessionDialog.sessionId)?(this.notification.text=D("session.AlreadyTerminatingSession"),this.notification.show(),!1):(this.listCondition="loading",null===(t=this._listStatus)||void 0===t||t.show(),this._terminateKernel(this.terminateSessionDialog.sessionId,this.terminateSessionDialog.accessKey,e).then((e=>{this._selected_items=[],this._clearCheckboxes(),this.terminateSessionDialog.hide(),this.notification.text=D("session.SessionTerminated"),this.notification.show();const t=new CustomEvent("backend-ai-resource-refreshed",{detail:"running"});document.dispatchEvent(t)})).catch((e=>{this._selected_items=[],this._clearCheckboxes(),this.terminateSessionDialog.hide(),this.notification.text=$.relieve("Problem occurred during termination."),this.notification.show(!0,e);const t=new CustomEvent("backend-ai-resource-refreshed",{detail:"running"});document.dispatchEvent(t)})))}_openTerminateSelectedSessionsDialog(e){this.terminateSelectedSessionsDialog.show()}_clearCheckboxes(){var e;[...Array.from(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll("wl-checkbox.list-check"))].forEach((e=>{e.removeAttribute("checked")}))}_terminateSelectedSessionsWithCheck(e=!1){var t;this.listCondition="loading",null===(t=this._listStatus)||void 0===t||t.show();const i=this._selected_items.map((t=>this._terminateKernel(t.session_id,t.access_key,e)));return this._selected_items=[],Promise.all(i).then((e=>{this.terminateSelectedSessionsDialog.hide(),this._clearCheckboxes(),this.multipleActionButtons.style.display="none",this.notification.text=D("session.SessionsTerminated"),this.notification.show()})).catch((e=>{this.terminateSelectedSessionsDialog.hide(),this._clearCheckboxes(),this.notification.text=$.relieve("Problem occurred during termination."),this.notification.show(!0,e)}))}_terminateSelectedSessions(){var e;this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show();const t=this._selected_items.map((e=>this._terminateKernel(e.session_id,e.access_key)));return Promise.all(t).then((e=>{this._selected_items=[],this._clearCheckboxes(),this.multipleActionButtons.style.display="none",this.notification.text=D("session.SessionsTerminated"),this.notification.show()})).catch((e=>{var t;null===(t=this._listStatus)||void 0===t||t.hide(),this._selected_items=[],this._clearCheckboxes(),this.notification.text="description"in e?$.relieve(e.description):$.relieve("Problem occurred during termination."),this.notification.show(!0,e)}))}async _terminateKernel(e,t,i=!1){return this.terminationQueue.push(e),this._terminateApp(e).then((()=>{globalThis.backendaiclient.destroy(e,t,i).then((e=>{setTimeout((async()=>{this.terminationQueue=[];const e=new CustomEvent("backend-ai-session-list-refreshed",{detail:"running"});document.dispatchEvent(e)}),1e3)})).catch((e=>{const t=new CustomEvent("backend-ai-session-list-refreshed",{detail:"running"});document.dispatchEvent(t),this.notification.text="description"in e?$.relieve(e.description):$.relieve("Problem occurred during termination."),this.notification.show(!0,e)}))})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=$.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_hideDialog(e){var t;const i=e.target.closest("backend-ai-dialog");if(i.hide(),"ssh-dialog"===i.id){const e=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#sshkey-download-link");globalThis.URL.revokeObjectURL(e.href)}}_updateFilterAccessKey(e){this.filterAccessKey=e.target.value,this.refreshTimer&&(clearTimeout(this.refreshTimer),this._refreshJobData())}_createMountedFolderDropdown(e,t){const i=e.target,s=document.createElement("mwc-menu");s.anchor=i,s.className="dropdown-menu",s.style.boxShadow="0 1px 1px rgba(0, 0, 0, 0.2)",s.setAttribute("open",""),s.setAttribute("fixed",""),s.setAttribute("x","10"),s.setAttribute("y","15"),t.length>=1&&(t.map(((e,i)=>{const o=document.createElement("mwc-list-item");o.style.height="25px",o.style.fontWeight="400",o.style.fontSize="14px",o.style.fontFamily="var(--general-font-family)",o.innerHTML=t.length>1?e:D("session.OnlyOneFolderAttached"),s.appendChild(o)})),document.body.appendChild(s))}_removeMountedFolderDropdown(){const e=document.getElementsByClassName("dropdown-menu");for(;e[0];)e[0].parentNode.removeChild(e[0])}_renderStatusDetail(){var e,t,i,s,o,n,a,r,l;const c=JSON.parse(this.selectedSessionStatus.data);c.reserved_time=this.selectedSessionStatus.reserved_time;const d=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#status-detail"),p=[];if(p.push(I`
    <div class="vertical layout justified start">
      <h3 style="width:100%;padding-left:15px;border-bottom:1px solid #ccc;">${D("session.Status")}</h3>
      <lablup-shields color="${this.statusColorTable[this.selectedSessionStatus.info]}"
          description="${this.selectedSessionStatus.info}" ui="round" style="padding-left:10px;padding-right:10px;"></lablup-shields>
    </div>`),c.hasOwnProperty("kernel")||c.hasOwnProperty("session"))p.push(I`
        <div class="vertical layout start flex" style="width:100%;">
        <div style="width:100%;">
          <h3 style="width:100%;padding-left:15px;border-bottom:1px solid #ccc;">${D("session.StatusDetail")}</h3>
          <div class="vertical layout flex" style="width:100%;">
            <mwc-list>
              <mwc-list-item twoline noninteractive class="predicate-check">
                <span class="subheading"><strong>Kernel Exit Code</strong></span>
                <span class="monospace predicate-check-comment" slot="secondary">${null!==(i=null===(t=c.kernel)||void 0===t?void 0:t.exit_code)&&void 0!==i?i:"null"}</span>
              </mwc-list-item>
              <mwc-list-item twoline noninteractive class="predicate-check">
                <span class="subheading">Session Status</span>
                <span class="monospace predicate-check-comment" slot="secondary">${null===(s=c.session)||void 0===s?void 0:s.status}</span>
              </mwc-list-item>
            </mwc-list>
          </div>
        </div>
      `);else if(c.hasOwnProperty("scheduler")){const e=null!==(n=null===(o=c.scheduler.failed_predicates)||void 0===o?void 0:o.length)&&void 0!==n?n:0,t=null!==(r=null===(a=c.scheduler.passed_predicates)||void 0===a?void 0:a.length)&&void 0!==r?r:0;p.push(I`
        <div class="vertical layout start flex" style="width:100%;">
          <div style="width:100%;">
            <h3 style="width:100%;padding-left:15px;border-bottom:1px solid #ccc;">${D("session.StatusDetail")}</h3>
            <div class="vertical layout flex" style="width:100%;">
              <mwc-list>
                <mwc-list-item twoline noninteractive class="predicate-check">
                  <span class="subheading">${D("session.Message")}</span>
                  <span class="monospace predicate-check-comment" slot="secondary">${c.scheduler.msg}</span>
                </mwc-list-item>
                <mwc-list-item twoline noninteractive class="predicate-check">
                  <span class="subheading">${D("session.TotalRetries")}</span>
                  <span class="monospace predicate-check-comment" slot="secondary">${c.scheduler.retries}</span>
                </mwc-list-item>
                <mwc-list-item twoline noninteractive class="predicate-check">
                  <span class="subheading">${D("session.LastTry")}</span>
                  <span class="monospace predicate-check-comment" slot="secondary">${this._humanReadableTime(c.scheduler.last_try)}</span>
                </mwc-list-item>
              </mwc-list>
            </div>
          </div>
          <wl-expansion name="predicates" open>
          <div slot="title" class="horizontal layout center start-justified">
            ${e>0?I`
              <mwc-icon class="fg red">cancel</mwc-icon>
              `:I`
              <mwc-icon class="fg green">check_circle</mwc-icon>
            `}
            Predicate Checks
          </div>
          <span slot="description">
            ${e>0?" "+(e+" Failed, "):""}
            ${t+" Passed"}
          </span>
          <mwc-list>
          ${c.scheduler.failed_predicates.map((e=>I`
          ${"reserved_time"===e.name?I`
              <mwc-list-item twoline graphic="icon" noninteractive class="predicate-check">
                <span>${e.name}</span>
                <span slot="secondary" class="predicate-check-comment">${e.msg+": "+c.reserved_time}</span>
                <mwc-icon slot="graphic" class="fg red inverted status-check">close</mwc-icon>
              </mwc-list-item>`:I`
              <mwc-list-item twoline graphic="icon" noninteractive class="predicate-check">
                <span>${e.name}</span>
                <span slot="secondary" class="predicate-check-comment">${e.msg}</span>
                <mwc-icon slot="graphic" class="fg red inverted status-check">close</mwc-icon>
              </mwc-list-item>`}
              <li divider role="separator"></li>`))}
          ${c.scheduler.passed_predicates.map((e=>I`
              <mwc-list-item graphic="icon" noninteractive>
                <span style="padding-left:3px;">${e.name}</span>
                <mwc-icon slot="graphic" class="fg green inverted status-check" style="padding-left:5px;">checked
                </mwc-icon>
              </mwc-list-item>
              <li divider role="separator"></li>
            `))}
          </mwc-list>
        </wl-expansion>
        </div>
    `)}else if(c.hasOwnProperty("error")){const e=null!==(l=c.error.collection)&&void 0!==l?l:[c.error];p.push(I`
      <div class="vertical layout start flex" style="width:100%;">
        <div style="width:100%;">
          <h3 style="width:100%;padding-left:15px;border-bottom:1px solid #ccc;">${D("session.StatusDetail")}</h3>
            ${e.map((e=>I`
              <div style="border-radius: 4px;background-color:var(--paper-grey-300);padding:10px;margin:10px;">
                <div class="vertical layout start">
                  <span class="subheading">Error</span>
                  <lablup-shields color="red" description=${e.name} ui="round"></lablup-shields>
                </div>
                ${!this.is_superadmin&&globalThis.backendaiclient._config.hideAgents||!e.agent_id?I``:I`
                  <div class="vertical layout start">
                    <span class="subheading">Agent ID</span>
                    <span>${e.agent_id}</span>
                  </div>
                `}
                <div class="vertical layout start">
                  <span class="subheading">Message</span>
                  <span class="error-description">${e.repr}</span>
                </div>
                ${e.traceback?I`
                  <div class="vertical layout start">
                    <span class="subheading">Traceback</span>
                    <pre style="display: block; overflow: auto; width: 100%; height: 400px;">${e.traceback}</pre>
                  </div>
                `:I``}
              </div>
              `))}
        </div>
      </div>
      `)}else p.push(I`
        <div class="vertical layout start flex" style="width:100%;">
        <h3 style="width:100%;padding-left:15px;border-bottom:1px solid #ccc;">Detail</h3>
        <span style="margin:20px;">No Detail.</span>
        </div>
      `);C(p,d)}_openStatusDetailDialog(e,t,i){this.selectedSessionStatus={info:e,data:t,reserved_time:i},this._renderStatusDetail(),this.sessionStatusInfoDialog.show()}_validateSessionName(e){const t=this.compute_sessions.map((e=>e[this.sessionNameField])),i=e.target.parentNode,s=i.querySelector("#session-name-field").innerText,o=i.querySelector("#session-rename-field");o.validityTransform=(e,i)=>{if(i.valid){const i=!t.includes(e)||e===s;return i||(o.validationMessage=D("session.Validation.SessionNameAlreadyExist")),{valid:i,customError:!i}}return i.valueMissing?(o.validationMessage=D("session.Validation.SessionNameRequired"),{valid:i.valid,valueMissing:!i.valid}):i.patternMismatch?(o.validationMessage=D("session.Validation.SluggedStrings"),{valid:i.valid,patternMismatch:!i.valid}):(o.validationMessage=D("session.Validation.EnterValidSessionName"),{valid:i.valid,customError:!i.valid})}}_renameSessionName(e,t){const i=t.target.parentNode,s=i.querySelector("#session-name-field"),o=i.querySelector("#session-rename-field"),n=i.querySelector("#session-rename-icon");if("none"===s.style.display){if(!o.checkValidity())return o.reportValidity(),void(n.on=!0);{const t=globalThis.backendaiclient.APIMajorVersion<5?s.value:e;globalThis.backendaiclient.rename(t,o.value).then((e=>{this.refreshList(),this.notification.text=D("session.SessionRenamed"),this.notification.show()})).catch((e=>{o.value=s.innerText,e&&e.message&&(this.notification.text=$.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))})).finally((()=>{this._toggleSessionNameField(s,o)}))}}else this._toggleSessionNameField(s,o)}_toggleSessionNameField(e,t){"block"===t.style.display?(e.style.display="block",t.style.display="none"):(e.style.display="none",t.style.display="block",t.focus())}static secondsToDHMS(e){const t=Math.floor(e/86400),i=Math.floor(e%86400/3600),s=Math.floor(e%3600/60),o=parseInt(e)%60,n=t<0||i<0||s<0||o<0?D("session.TimeoutExceeded"):"",a=`${void 0!==t&&t>0?String(t)+"d":""}${i.toString().padStart(2,"0")}:${s.toString().padStart(2,"0")}:${o.toString().padStart(2,"0")}`;return n.length>0?n:a}_getIdleSessionTimeout(e){if(globalThis.backendaiutils.isEmpty(e))return null;let t="",i=1/0;for(const[s,o]of Object.entries(e))null!=o&&"number"==typeof o&&null!=i&&o<i&&(t=s,i=o);return i?[t,Q.secondsToDHMS(i)]:null}_openIdleChecksInfoDialog(){var e,t,i;this._helpDescriptionTitle=D("session.IdleChecks"),this._helpDescription=`\n      <p>${D("session.IdleChecksDesc")}</p>\n      ${(null===(e=this.activeIdleCheckList)||void 0===e?void 0:e.has("session_lifetime"))?`\n        <strong>${D("session.MaxSessionLifetime")}</strong>\n        <p>${D("session.MaxSessionLifetimeDesc")}</p>\n        `:""}\n      ${(null===(t=this.activeIdleCheckList)||void 0===t?void 0:t.has("network_timeout"))?`\n        <strong>${D("session.NetworkIdleTimeout")}</strong>\n        <p>${D("session.NetworkIdleTimeoutDesc")}</p>\n      `:""}\n      ${(null===(i=this.activeIdleCheckList)||void 0===i?void 0:i.has("utilization"))?`\n        <strong>${D("session.UtilizationIdleTimeout")}</strong>\n        <p>${D("session.UtilizationIdleTimeoutDesc")}</p>\n        <div style="margin:10px 5% 20px 5%;">\n          <li>\n            <span style="font-weight:500">${D("session.GracePeriod")}</span>\n            <div style="padding-left:20px;">${D("session.GracePeriodDesc")}</div>\n          </li>\n          <li>\n            <span style="font-weight:500">${D("session.UtilizationThreshold")}</span>\n            <div style="padding-left:20px;">${D("session.UtilizationThresholdDesc")}</div>\n          </li>\n        </div>\n      `:""}\n    `,this.helpDescriptionDialog.show()}async _openSFTPSessionConnectionInfoDialog(e){const t=await globalThis.backendaiclient.get_direct_access_info(e),i=t.public_host.replace(/^https?:\/\//,""),s=t.sshd_ports,o=new CustomEvent("read-ssh-key-and-launch-ssh-dialog",{detail:{sessionUuid:e,host:i,port:s}});document.dispatchEvent(o)}_createUtilizationIdleCheckDropdown(e,t){const i=e.target,s=document.createElement("mwc-menu");s.anchor=i,s.className="util-dropdown-menu",s.style.boxShadow="0 1px 1px rgba(0, 0, 0, 0.2)",s.setAttribute("open",""),s.setAttribute("fixed",""),s.setAttribute("corner","BOTTOM_START");let o=I``;globalThis.backendaiutils.isEmpty(t)||(o=I`
        <style>
          .util-detail-menu-header {
            height: 25px;
            border: none;
            box-shadow: none;
            justify-content: flex-end;
          }
          .util-detail-menu-header > div {
            font-size: 13px;
            font-family: var(--general-font-family);
            font-weight: 600;
          }
          .util-detail-menu-content {
            height: 25px;
            border: none;
            box-shadow: none;
          }
          .util-detail-menu-content > div {
            display: flex;
            flex-direction: row;
            justify-content: center;
            justify-content: space-between;
            font-size: 12px;
            font-family: var(--general-font-family);
            font-weight: 400;
            min-width: 155px;
          }
        </style>
        <mwc-list-item class="util-detail-menu-header">
          <div>${D("session.Utilization")} / ${D("session.Threshold")} (%)</div>
        </mwc-list-item>${Object.keys(t).map((e=>{let[i,s]=t[e];i=i>=0?parseFloat(i).toFixed(1):"-";const o=this.getUtilizationCheckerColor([i,s]);return I`
              <mwc-list-item class="util-detail-menu-content">
                <div>
                  <div>${this.idleChecksTable[e]}</div>
                  <div style="color:${o}">${i} / ${s}</div>
                </div>
              </mwc-list-item>
            `}))}
      `,document.body.appendChild(s)),C(o,s)}_removeUtilizationIdleCheckDropdown(){const e=document.getElementsByClassName("util-dropdown-menu");for(;e[0];)e[0].parentNode.removeChild(e[0])}sessionTypeRenderer(e,t,i){const s=JSON.parse(i.item.inference_metrics||"{}");C(I`
        <div class="layout vertical start">
          <lablup-shields color="${this.sessionTypeColorTable[i.item.type]}"
              description="${i.item.type}" ui="round"></lablup-shields>
          ${"INFERENCE"===i.item.type?I`
            <span style="font-size:12px;margin-top:5px;">Inference requests: ${s.requests}</span>
            <span style="font-size:12px;">Inference API last response time (ms): ${s.last_response_ms}</span>
          `:""}
        </div>
      `,e)}sessionInfoRenderer(e,t,i){"system"===this.condition?C(I`
          <style>
            #session-name-field {
              display: block;
              white-space: pre-wrap;
              word-break: break-all;
            }
          </style>
          <div class="layout vertical start">
            <div class="horizontal center center-justified layout">
              <pre id="session-name-field">${i.item.mounts[0]} SFTP Session</pre>
            </div>
        `,e):C(I`
          <style>
            #session-name-field {
              display: block;
              margin-left: 16px;
              white-space: pre-wrap;
              word-break: break-all;
            }
            #session-rename-field {
              display: none;
              white-space: normal;
              word-break: break-word;
              font-family: var(--general-monospace-font-family);
              --mdc-ripple-color: transparent;
              --mdc-text-field-fill-color: transparent;
              --mdc-text-field-disabled-fill-color: transparent;
              --mdc-typography-font-family: var(--general-monospace-font-family);
              --mdc-typography-subtitle1-font-family: var(--general-monospace-font-family);
            }
            #session-rename-icon {
              --mdc-icon-size: 20px;
            }
          </style>
          <div class="layout vertical start">
            <div class="horizontal center center-justified layout">
              <pre id="session-name-field">${i.item[this.sessionNameField]}</pre>
              ${this._isRunning&&!this._isPreparing(i.item.status)&&globalThis.backendaiclient.email==i.item.user_email?I`
              <mwc-textfield id="session-rename-field" required autoValidate
                               pattern="^(?:[a-zA-Z0-9][a-zA-Z0-9._-]{2,}[a-zA-Z0-9])?$" maxLength="64"
                               validationMessage="${D("session.Validation.EnterValidSessionName")}"
                               value="${i.item[this.sessionNameField]}"
                               @input="${e=>this._validateSessionName(e)}"></mwc-textfield>
                <mwc-icon-button-toggle id="session-rename-icon" onIcon="done" offIcon="edit"
                                        @click="${e=>this._renameSessionName(i.item.session_id,e)}"></mwc-icon-button-toggle>
              `:I`
              `}
            </div>
            <div class="horizontal center center-justified layout">
            ${i.item.icon?I`
              <img src="resources/icons/${i.item.icon}" style="width:32px;height:32px;margin-right:10px;" />
            `:I`
            `}
              <div class="vertical start layout">
                ${i.item.sessionTags?i.item.sessionTags.map((e=>I`
                <div class="horizontal center layout">
                  ${e.map((e=>("Env"===e.category&&(e.category=e.tag),e.category&&i.item.baseversion&&(e.tag=i.item.baseversion),I`
                  <lablup-shields app="${void 0===e.category?"":e.category}"
                                  color="${e.color}"
                                  description="${e.tag}"
                                  ui="round"
                                  class="right-below-margin"></lablup-shields>
                      `)))}
                </div>`)):I``}
                ${i.item.additional_reqs?I`
                  <div class="layout horizontal center wrap">
                    ${i.item.additional_reqs.map((e=>I`
                        <lablup-shields app=""
                                        color="green"
                                        description="${e}"
                                        ui="round"
                                        class="right-below-margin"></lablup-shields>
                      `))}
                  </div>
                `:I``}
                ${i.item.cluster_size>1?I`
                  <div class="layout horizontal center wrap">
                    <lablup-shields app="${"single-node"===i.item.cluster_mode?"Multi-container":"Multi-node"}"
                                    color="blue"
                                    description="${"X "+i.item.cluster_size}"
                                    ui="round"
                                    class="right-below-margin"></lablup-shields>
                  </div>
                `:I``}
              </div>
            </div>
          </div>
        `,e)}architectureRenderer(e,t,i){C(I`
        <lablup-shields app=""
                        color="lightgreen"
                        description="${i.item.architecture}"
                        ui="round"></lablup-shields>
      `,e)}controlRenderer(e,t,i){var s;let o=!0;o="API"===this._connectionMode&&i.item.access_key===globalThis.backendaiclient._config._accessKey||i.item.user_email===globalThis.backendaiclient.email,C(I`
        <div id="controls" class="layout horizontal wrap center"
             .session-uuid="${i.item.session_id}"
             .session-name="${i.item[this.sessionNameField]}"
             .access-key="${i.item.access_key}"
             .kernel-image="${i.item.kernel_image}"
             .app-services="${i.item.app_services}"
             .app-services-option="${i.item.app_services_option}">
          ${i.item.appSupport&&"system"!==this.condition?I`
            <mwc-icon-button class="fg controls-running green"
                               id="${i.index+"-apps"}"
                               @click="${e=>this._showAppLauncher(e)}"
                               ?disabled="${!o}"
                               icon="apps">
            </mwc-icon-button>
            <vaadin-tooltip for="${i.index+"-apps"}" text="${E("session.SeeAppDialog")}" position="top-start"></vaadin-tooltip>
            <mwc-icon-button class="fg controls-running"
                               id="${i.index+"-terminal"}"
                               ?disabled="${!o}"
                               @click="${e=>this._runTerminal(e)}">
              <svg version="1.1" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
                 width="471.362px" height="471.362px" viewBox="0 0 471.362 471.362" style="enable-background:new 0 0 471.362 471.362;"
                 xml:space="preserve">
              <g>
                <g>
                  <path d="M468.794,355.171c-1.707-1.718-3.897-2.57-6.563-2.57H188.145c-2.664,0-4.854,0.853-6.567,2.57
                    c-1.711,1.711-2.565,3.897-2.565,6.563v18.274c0,2.662,0.854,4.853,2.565,6.563c1.713,1.712,3.903,2.57,6.567,2.57h274.086
                    c2.666,0,4.856-0.858,6.563-2.57c1.711-1.711,2.567-3.901,2.567-6.563v-18.274C471.365,359.068,470.513,356.882,468.794,355.171z"
                    />
                  <path d="M30.259,85.075c-1.903-1.903-4.093-2.856-6.567-2.856s-4.661,0.953-6.563,2.856L2.852,99.353
                    C0.95,101.255,0,103.442,0,105.918c0,2.478,0.95,4.664,2.852,6.567L115.06,224.69L2.852,336.896C0.95,338.799,0,340.989,0,343.46
                    c0,2.478,0.95,4.665,2.852,6.567l14.276,14.273c1.903,1.906,4.089,2.854,6.563,2.854s4.665-0.951,6.567-2.854l133.048-133.045
                    c1.903-1.902,2.853-4.096,2.853-6.57c0-2.473-0.95-4.663-2.853-6.565L30.259,85.075z"/>
                </g>
              </g>
            </svg>
            </mwc-icon-button>
            <vaadin-tooltip for="${i.index+"-terminal"}" text="${E("session.ExecuteTerminalApp")}" position="top-start"></vaadin-tooltip>
          `:I``}
          ${this._isRunning&&"system"===this.condition?I`
          <mwc-icon-button class="fg apps green"
            id="${i.index+"-sftp-connection-info"}"
            @click="${()=>this._openSFTPSessionConnectionInfoDialog(i.item.id)}">
            <img src="/resources/icons/sftp.png"/>
          </mwc-icon-button>
          <vaadin-tooltip for="${i.index+"-sftp-connection-info"}" text="${E("data.explorer.RunSSH/SFTPserver")}" position="top-start"></vaadin-tooltip>
          `:I``}
          ${this._isRunning&&!this._isPreparing(i.item.status)||this._isError(i.item.status)?I`
            <mwc-icon-button class="fg red controls-running" id="${i.index+"-power"}" ?disabled=${!this._isPending(i.item.status)&&"ongoing"===(null===(s=i.item)||void 0===s?void 0:s.commit_status)}
                               icon="power_settings_new" @click="${e=>this._openTerminateSessionDialog(e)}"></mwc-icon-button>
            <vaadin-tooltip for="${i.index+"-power"}" text="${E("session.TerminateSession")}" position="top-start"></vaadin-tooltip>
          `:I``}
          ${(this._isRunning&&!this._isPreparing(i.item.status)||this._APIMajorVersion>4)&&!this._isPending(i.item.status)?I`
            <mwc-icon-button class="fg blue controls-running" id="${i.index+"-assignment"}" icon="assignment"
                               @click="${e=>this._showLogs(e)}"></mwc-icon-button>
            <vaadin-tooltip for="${i.index+"-assignment"}" text="${E("session.SeeContainerLogs")}" position="top-start"></vaadin-tooltip>
          `:I`
            <mwc-icon-button fab flat inverted disabled class="fg controls-running" id="${i.index+"-assignment"}" icon="assignment"></mwc-icon-button>
            <vaadin-tooltip for="${i.index+"-assignment"}" text="${E("session.NoLogMsgAvailable")}" position="top-start"></vaadin-tooltip>
          `}
          ${this._isContainerCommitEnabled?I`
            <mwc-icon-button class="fg blue controls-running"
                             id="${i.index+"-archive"}"
                             ?disabled=${this._isPending(i.item.status)||this._isPreparing(i.item.status)||this._isError(i.item.status)||this._isFinished(i.item.status)||"BATCH"===i.item.type||"ongoing"===i.item.commit_status}
                             icon="archive" @click="${e=>this._openCommitSessionDialog(e)}"></mwc-icon-button>
            <vaadin-tooltip for="${i.index+"-archive"}" text="${E("session.RequestContainerCommit")}" position="top-start"></vaadin-tooltip>
          `:I``}
        </div>
      `,e)}configRenderer(e,t,i){const s=i.item.mounts.map((e=>e.startsWith("[")?JSON.parse(e.replace(/'/g,'"'))[0]:e));"system"===this.condition?C(I``,e):C(I`
          <div class="layout horizontal center flex">
            <div class="layout horizontal center configuration">
              ${i.item.mounts.length>0?I`
                <wl-icon class="fg green indicator">folder_open</wl-icon>
                <button class="mount-button"
                  @mouseenter="${e=>this._createMountedFolderDropdown(e,s)}"
                  @mouseleave="${()=>this._removeMountedFolderDropdown()}">
                  ${s.join(", ")}
                </button>
              `:I`
              <wl-icon class="indicator no-mount">folder_open</wl-icon>
              <span class="no-mount">No mount</span>
              `}
            </div>
          </div>
          ${i.item.scaling_group?I`
          <div class="layout horizontal center flex">
            <div class="layout horizontal center configuration">
              <wl-icon class="fg green indicator">work</wl-icon>
              <span>${i.item.scaling_group}</span>
              <span class="indicator">RG</span>
            </div>
          </div>`:I``}
          <div class="layout vertical flex" style="padding-left: 25px">
            <div class="layout horizontal center configuration">
              <wl-icon class="fg green indicator">developer_board</wl-icon>
              <span>${i.item.cpu_slot}</span>
              <span class="indicator">${E("session.core")}</span>
            </div>
            <div class="layout horizontal center configuration">
              <wl-icon class="fg green indicator">memory</wl-icon>
              <span>${i.item.mem_slot}</span>
              <span class="indicator">GiB</span>
              ${this.isDisplayingAllocatedShmemEnabled?I`
                <span class="indicator">
                  ${"(SHM: "+this._aggregateSharedMemory(JSON.parse(i.item.resource_opts))+"GiB)"}
                </span>
              `:I``}
            </div>
            <div class="layout horizontal center configuration">
              ${i.item.cuda_gpu_slot?I`
                <img class="indicator-icon fg green" src="/resources/icons/file_type_cuda.svg" />
                <span>${i.item.cuda_gpu_slot}</span>
                <span class="indicator">GPU</span>
                `:I``}
              ${!i.item.cuda_gpu_slot&&i.item.cuda_fgpu_slot?I`
                <img class="indicator-icon fg green" src="/resources/icons/file_type_cuda.svg" />
                <span>${i.item.cuda_fgpu_slot}</span>
                <span class="indicator">FGPU</span>
                `:I``}
              ${i.item.rocm_gpu_slot?I`
                <img class="indicator-icon fg green" src="/resources/icons/ROCm.png" />
                <span>${i.item.rocm_gpu_slot}</span>
                <span class="indicator">GPU</span>
                `:I``}
              ${i.item.tpu_slot?I`
                <wl-icon class="fg green indicator">view_module</wl-icon>
                <span>${i.item.tpu_slot}</span>
                <span class="indicator">TPU</span>
                `:I``}
              ${i.item.ipu_slot?I`
                <wl-icon class="fg green indicator">view_module</wl-icon>
                <span>${i.item.tpu_slot}</span>
                <span class="indicator">IPU</span>
                `:I``}
              ${i.item.atom_slot?I`
                <img class="indicator-icon fg green" src="/resources/icons/rebel.svg" />
                <span>${i.item.atom_slot}</span>
                <span class="indicator">ATOM</span>
                `:I``}
              ${i.item.warboy_slot?I`
                <img class="indicator-icon fg green" src="/resources/icons/furiosa.svg" />
                <span>${i.item.warboy_slot}</span>
                <span class="indicator">Warboy</span>
                `:I``}
              ${i.item.cuda_gpu_slot||i.item.cuda_fgpu_slot||i.item.rocm_gpu_slot||i.item.tpu_slot||i.item.ipu_slot||i.item.atom_slot||i.item.warboy_slot?I``:I`
                <wl-icon class="fg green indicator">view_module</wl-icon>
                <span>-</span>
                <span class="indicator">GPU</span>
                `}
            </div>
          </div>
       `,e)}usageRenderer(e,t,i){["batch","interactive","inference","running"].includes(this.condition)?C(I`
        <div class="vertical start start-justified layout">
          <div class="horizontal start-justified center layout">
            <div class="usage-items">CPU</div>
            <div class="horizontal start-justified center layout">
              <lablup-progress-bar class="usage"
                progress="${i.item.cpu_util/(100*i.item.cpu_slot)}"
                description=""
              ></lablup-progress-bar>
            </div>
          </div>
          <div class="horizontal start-justified center layout">
            <div class="usage-items">RAM</div>
            <div class="horizontal start-justified center layout">
              <lablup-progress-bar class="usage"
                progress="${i.item.mem_current/(1e9*i.item.mem_slot)}"
                description=""
              ></lablup-progress-bar>
            </div>
          </div>
          ${i.item.cuda_gpu_slot&&parseInt(i.item.cuda_gpu_slot)>0?I`
          <div class="horizontal start-justified center layout">
            <div class="usage-items">GPU(util)</div>
            <div class="horizontal start-justified center layout">
              <lablup-progress-bar class="usage"
                progress="${i.item.cuda_util/(100*i.item.cuda_gpu_slot)}"
                description=""
              ></lablup-progress-bar>
            </div>
          </div>`:I``}
          ${i.item.cuda_fgpu_slot&&parseFloat(i.item.cuda_fgpu_slot)>0?I`
          <div class="horizontal start-justified center layout">
            <div class="usage-items">GPU(util)</div>
            <div class="horizontal start-justified center layout">
              <lablup-progress-bar class="usage"
                progress="${i.item.cuda_util/(100*i.item.cuda_fgpu_slot)}"
                description=""
              ></lablup-progress-bar>
            </div>
          </div>`:I``}
          ${i.item.rocm_gpu_slot&&parseFloat(i.item.cuda_rocm_gpu_slot)>0?I`
          <div class="horizontal start-justified center layout">
            <div class="usage-items">GPU(util)</div>
            <div class="horizontal start-justified center layout">
              <lablup-progress-bar class="usage"
                progress="${i.item.rocm_util/(100*i.item.rocm_gpu_slot)}"
                description=""
              ></lablup-progress-bar>
            </div>
          </div>`:I``}
          ${i.item.cuda_fgpu_slot||i.item.rocm_gpu_slot?I`
          <div class="horizontal start-justified center layout">
            <div class="usage-items">GPU(mem)</div>
            <div class="horizontal start-justified center layout">
              <lablup-progress-bar class="usage"
                progress="${i.item.cuda_mem_ratio}"
                description=""
              ></lablup-progress-bar>
            </div>
          </div>`:I``}
          ${i.item.tpu_slot&&parseFloat(i.item.tpu_slot)>0?I`
          <div class="horizontal start-justified center layout">
            <div class="usage-items">TPU(util)</div>
            <div class="horizontal start-justified center layout">
              <lablup-progress-bar class="usage"
                progress="${i.item.tpu_util/(100*i.item.tpu_slot)}"
                description=""
              ></lablup-progress-bar>
            </div>
          </div>`:I``}
          ${i.item.ipu_slot&&parseFloat(i.item.ipu_slot)>0?I`
          <div class="horizontal start-justified center layout">
            <div class="usage-items">IPU(util)</div>
            <div class="horizontal start-justified center layout">
              <lablup-progress-bar class="usage"
                progress="${i.item.ipu_util/(100*i.item.ipu_slot)}"
                description=""
              ></lablup-progress-bar>
            </div>
          </div>`:I``}
          ${i.item.atom_slot&&parseFloat(i.item.atom_slot)>0?I`
          <div class="horizontal start-justified center layout">
            <div class="usage-items">ATOM(util)</div>
            <div class="horizontal start-justified center layout">
              <lablup-progress-bar class="usage"
                progress="${i.item.atom_util/(100*i.item.atom_slot)}"
                description=""
              ></lablup-progress-bar>
            </div>
          </div>`:I``}
          <div class="horizontal start-justified center layout">
            <div class="usage-items">I/O</div>
            <div style="font-size:8px;" class="horizontal start-justified center layout">
            R: ${i.item.io_read_bytes_mb} MB /
            W: ${i.item.io_write_bytes_mb} MB
            </div>
          </div>
       </div>
        `,e):"finished"===this.condition&&C(I`
        <div class="layout horizontal center flex">
          <wl-icon class="fg blue indicator" style="margin-right:3px;">developer_board</wl-icon>
          ${i.item.cpu_used_time.D?I`
          <div class="vertical center-justified center layout">
            <span style="font-size:11px">${i.item.cpu_used_time.D}</span>
            <span class="indicator">day</span>
          </div>`:I``}
          ${i.item.cpu_used_time.H?I`
          <div class="vertical center-justified center layout">
            <span style="font-size:11px">${i.item.cpu_used_time.H}</span>
            <span class="indicator">hour</span>
          </div>`:I``}
          ${i.item.cpu_used_time.M?I`
          <div class="vertical start layout">
            <span style="font-size:11px">${i.item.cpu_used_time.M}</span>
            <span class="indicator">min.</span>
          </div>`:I``}
          ${i.item.cpu_used_time.S?I`
          <div class="vertical start layout">
            <span style="font-size:11px">${i.item.cpu_used_time.S}</span>
            <span class="indicator">sec.</span>
          </div>`:I``}
          ${i.item.cpu_used_time.MS?I`
          <div class="vertical start layout">
            <span style="font-size:11px">${i.item.cpu_used_time.MS}</span>
            <span class="indicator">msec.</span>
          </div>`:I``}
          ${i.item.cpu_used_time.NODATA?I`
          <div class="vertical start layout">
            <span style="font-size:11px">No data</span>
          </div>`:I``}
        </div>
        <div class="layout horizontal center flex">
          <wl-icon class="fg blue indicator" style="margin-right:3px;">device_hub</wl-icon>
          <div class="vertical start layout">
            <span style="font-size:9px">${i.item.io_read_bytes_mb}<span class="indicator">MB</span></span>
            <span class="indicator">READ</span>
          </div>
          <div class="vertical start layout">
            <span style="font-size:8px">${i.item.io_write_bytes_mb}<span class="indicator">MB</span></span>
            <span class="indicator">WRITE</span>
          </div>
        </div>`,e)}reservationRenderer(e,t,i){C(I`
        <div class="layout vertical" style="padding:3px auto;">
          <span>${i.item.created_at_hr}</span>
          <lablup-shields app="${E("session.ElapsedTime")}" color="darkgreen" style="margin:3px 0;"
                          description="${i.item.elapsed}" ui="round"></lablup-shields>
        </div>
      `,e)}idleChecksHeaderRenderer(e,t){C(I`
        <div class="horizontal layout center">
          <div>
            ${E("session.IdleChecks")}
          </div>
          <mwc-icon-button class="fg grey" icon="info" @click="${()=>this._openIdleChecksInfoDialog()}"></mwc-icon-button>
        </div>
      `,e)}idleChecksRenderer(e,t,i){var s;const o=null===(s=Object.keys(i.item.idle_checks))||void 0===s?void 0:s.map((e=>{var t,s;const o=i.item.idle_checks[e],n=null==o?void 0:o.remaining;if(!n)return;const a=globalThis.backendaiclient.utils.elapsedTimeToTotalSeconds(n),r=null==o?void 0:o.remaining_time_type;let l,c="#527A42";return!a||a<3600?c="#e05d44":a<14400&&(c="#D8B541"),"utilization"===e&&(null==o?void 0:o.extra)&&(!a||a<14400)&&(c=this.getUtilizationCheckerColor(null===(t=null==o?void 0:o.extra)||void 0===t?void 0:t.resources,null===(s=null==o?void 0:o.extra)||void 0===s?void 0:s.thresholds_check_operator)),l="utilization"===e?I`
          <button
            class="idle-check-key"
            style="color:#42a5f5;"
            @mouseenter="${e=>{var t,s,o;return this._createUtilizationIdleCheckDropdown(e,null===(o=null===(s=null===(t=i.item.idle_checks)||void 0===t?void 0:t.utilization)||void 0===s?void 0:s.extra)||void 0===o?void 0:o.resources)}}"
            @mouseleave="${()=>this._removeUtilizationIdleCheckDropdown()}"
          >
            ${D("session."+this.idleChecksTable[e])}
          </button>
        `:I`
          <button
            class="idle-check-key"
            style="color:#222222;"
          >
            ${D("session."+this.idleChecksTable[e])}
          </button>
        `,e in this.idleChecksTable?I`
          <div class="layout vertical" style="padding:3px auto;">
            <div style="margin:4px;">
              ${l}
              <br/>
              <strong style="color:${c}">${n}</strong>
              <div class="idle-type">${D("session."+this.idleChecksTable[r])}</div>
            </div>
          </div>
        `:I``})),n=I`${o}`;C(n,e)}agentRenderer(e,t,i){C(I`
        <div class="layout vertical">
          <span>${i.item.agent}</span>
        </div>
      `,e)}_toggleCheckbox(e){const t=this._selected_items.findIndex((t=>t.session_id==e.session_id));-1===t?this._selected_items.push(e):this._selected_items.splice(t,1),this._selected_items.length>0?this.multipleActionButtons.style.display="block":this.multipleActionButtons.style.display="none"}_aggregateSharedMemory(e){let t=0;return Object.keys(e).forEach((i=>{var s,o;t+=Number(null!==(o=null===(s=e[i])||void 0===s?void 0:s.shmem)&&void 0!==o?o:0)})),Q.bytesToGiB(t)}checkboxRenderer(e,t,i){this._isRunning&&!this._isPreparing(i.item.status)||this._APIMajorVersion>4?C(I`
            <wl-checkbox class="list-check" style="--checkbox-size:12px;" ?checked="${!0===i.item.checked}" @click="${()=>this._toggleCheckbox(i.item)}"></wl-checkbox>
        `,e):C(I``,e)}userInfoRenderer(e,t,i){const s="API"===this._connectionMode?i.item.access_key:i.item.user_email;C(I`
        <div class="layout vertical">
          <span class="indicator">${this._getUserId(s)}</span>
        </div>
      `,e)}statusRenderer(e,t,i){var s;C(I`
        <div class="horizontal layout center">
          <span style="font-size: 12px;">${i.item.status}</span>
          ${i.item.status_data&&"{}"!==i.item.status_data?I`
            <mwc-icon-button class="fg green status" icon="help"
                @click="${()=>{var e;return this._openStatusDetailDialog(null!==(e=i.item.status_info)&&void 0!==e?e:"",i.item.status_data,i.item.starts_at_hr)}}"></mwc-icon-button>
          `:I``}
        </div>
        ${i.item.status_info?I`
          <div class="layout horizontal">
            <lablup-shields id="${i.item.name}" app="" color="${this.statusColorTable[i.item.status_info]}"
                  description="${i.item.status_info}" ui="round"></lablup-shields>
          </div>
        `:I``}
        ${this._isContainerCommitEnabled&&void 0!==(null===(s=i.item)||void 0===s?void 0:s.commit_status)?I`
          <lablup-shields app="" color="${this._setColorOfStatusInformation(i.item.commit_status)}" class="right-below-margin"
                          description=${"ongoing"===i.item.commit_status?"commit on-going":""}></lablup-shields>
        `:I``}
      `,e)}_setColorOfStatusInformation(e="ready"){return"ready"===e?"green":"lightgrey"}_getUserId(e=""){if(e&&this.isUserInfoMaskEnabled){const t=/^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/.test(e),i=t?2:0,s=t?e.split("@")[0].length-i:0;e=globalThis.backendaiutils._maskString(e,"*",i,s)}return e}_renderCommitSessionConfirmationDialog(e){var t,i,s;return I`
      <backend-ai-dialog id="commit-session-dialog" fixed backdrop>
        <span slot="title">${E("session.CommitSession")}</span>
        <div slot="content" class="vertical layout center flex">
          <span style="font-size:14px;margin:auto 20px;">${E("session.DescCommitSession")}</span>
          <mwc-list style="width:100%">
            <mwc-list-item twoline noninteractive class="commit-session-info">
                <span class="subheading">Session Name</span>
                <span class="monospace" slot="secondary">
                  ${(null===(t=null==e?void 0:e.session)||void 0===t?void 0:t.name)?e.session.name:"-"}
                </span>
            </mwc-list-item>
            <mwc-list-item twoline noninteractive class="commit-session-info">
                <span class="subheading">Session Id</span>
                <span class="monospace" slot="secondary">
                  ${(null===(i=null==e?void 0:e.session)||void 0===i?void 0:i.id)?e.session.id:"-"}
                </span>
            </mwc-list-item>
            <mwc-list-item twoline noninteractive class="commit-session-info">
              <span class="subheading"><strong>Environment and Version</strong></span>
              <span class="monospace" slot="secondary">
                ${e?I`
                  <lablup-shields app="${""===e.environment?"-":e.environment}"
                    color="blue"
                    description="${""===e.version?"-":e.version}"
                    ui="round"
                    class="right-below-margin"></lablup-shields>
                    `:I``}
              </span>
            </mwc-list-item>
            <mwc-list-item twoline noninteractive class="commit-session-info">
              <span class="subheading">Tags</span>
              <span class="monospace horizontal layout" slot="secondary">
                ${e?null===(s=null==e?void 0:e.tags)||void 0===s?void 0:s.map((e=>I`
                    <lablup-shields app=""
                      color="green"
                      description="${e}"
                      ui="round"
                      class="right-below-margin"></lablup-shields>
                  `)):I`
                    <lablup-shields app=""
                      color="green"
                      description="-"
                      ui="round"
                      style="right-below-margin"></lablup-shields>`}
              </span>
            </mwc-list-item>
          </mwc-list>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
              unelevated
              class="ok"
              ?disabled="${""===(null==e?void 0:e.environment)}"
              @click=${()=>this._requestCommitSession(e)}
              label="${E("button.Commit")}"></mwc-button>
        </div>
      </backend-ai-dialog>
    `}_parseSessionInfoToCommitSessionInfo(e="",t="",i=""){const s=["",""],[o,n]=e?e.split(":"):s,[a,...r]=n?n.split("-"):s;return{environment:o,version:a,tags:r,session:{name:t,id:i}}}render(){var e,t,i;return I`
      <link rel="stylesheet" href="resources/custom.css">
      <div class="layout horizontal center filters">
        <div id="multiple-action-buttons" style="display:none;">
          <wl-button outlined class="multiple-action-button" style="margin:8px;--button-shadow-color:0;--button-shadow-color-hover:0;" @click="${()=>this._openTerminateSelectedSessionsDialog()}">
            <wl-icon style="--icon-size: 20px;">delete</wl-icon>
            ${E("session.Terminate")}
          </wl-button>
        </div>
        <span class="flex"></span>
        <div class="vertical layout" style="display:none">
          <wl-textfield id="access-key-filter" type="search" maxLength="64"
                      label="${E("general.AccessKey")}" no-label-float .value="${this.filterAccessKey}"
                      style="margin-right:20px;"
                      @change="${e=>this._updateFilterAccessKey(e)}">
          </wl-textfield>
          <span id="access-key-filter-helper-text">${E("maxLength.64chars")}</span>
        </div>
      </div>
      <div class="list-wrapper">
        <vaadin-grid id="list-grid" theme="row-stripes column-borders compact" aria-label="Session list"
          .items="${this.compute_sessions}" height-by-rows>
          ${this._isRunning?I`
            <vaadin-grid-column frozen width="40px" flex-grow="0" text-align="center" .renderer="${this._boundCheckboxRenderer}">
            </vaadin-grid-column>
          `:I``}
          <vaadin-grid-column frozen width="40px" flex-grow="0" header="#" .renderer="${this._indexRenderer}"></vaadin-grid-column>
          ${this.is_admin?I`
            <lablup-grid-sort-filter-column frozen path="${"API"===this._connectionMode?"access_key":"user_email"}"
                                      header="${"API"===this._connectionMode?"API Key":"User ID"}" resizable
                                      .renderer="${this._boundUserInfoRenderer}">
            </lablup-grid-sort-filter-column>
          `:I``}
          <lablup-grid-sort-filter-column frozen path="${this.sessionNameField}" auto-width header="${E("session.SessionInfo")}" resizable
                                     .renderer="${this._boundSessionInfoRenderer}">
          </lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column width="120px" path="status" header="${E("session.Status")}" resizable
                                     .renderer="${this._boundStatusRenderer}">
          </lablup-grid-sort-filter-column>
          <vaadin-grid-column width=${this._isContainerCommitEnabled?"260px":"210px"} flex-grow="0" resizable header="${E("general.Control")}"
                              .renderer="${this._boundControlRenderer}"></vaadin-grid-column>
          <vaadin-grid-column width="200px" flex-grow="0" resizable header="${E("session.Configuration")}"
                              .renderer="${this._boundConfigRenderer}"></vaadin-grid-column>
          <vaadin-grid-column width="140px" flex-grow="0" resizable header="${E("session.Usage")}"
                              .renderer="${this._boundUsageRenderer}">
          </vaadin-grid-column>
          <vaadin-grid-sort-column resizable width="180px" flex-grow="0" header="${E("session.Reservation")}"
                                   path="created_at" .renderer="${this._boundReservationRenderer}">
          </vaadin-grid-sort-column>
          ${globalThis.backendaiclient.supports("idle-checks")&&this.activeIdleCheckList.size>0?I`
            <vaadin-grid-column resizable auto-width flex-grow="0"
                                .headerRenderer="${this._boundIdleChecksHeaderderer}"
                                .renderer="${this._boundIdleChecksRenderer}">
            </vaadin-grid-column>
          `:I``}
          <lablup-grid-sort-filter-column width="110px" path="architecture" header="${E("session.Architecture")}" resizable
                                     .renderer="${this._boundArchitectureRenderer}">
          </lablup-grid-sort-filter-column>
          ${this._isIntegratedCondition?I`
            <lablup-grid-sort-filter-column path="type" width="140px" flex-grow="0" header="${E("session.launcher.SessionType")}" resizable .renderer="${this._boundSessionTypeRenderer}"></lablup-grid-sort-filter-column>
        `:I``}
          ${this.is_superadmin||!globalThis.backendaiclient._config.hideAgents?I`
            <lablup-grid-sort-filter-column path="agent" auto-width flex-grow="0" resizable header="${E("session.Agent")}"
                                .renderer="${this._boundAgentRenderer}">
            </lablup-grid-sort-filter-column>
                `:I``}
          </vaadin-grid>
          <backend-ai-list-status id="list-status" statusCondition="${this.listCondition}" message="${D("session.NoSessionToDisplay")}"></backend-ai-list-status>
        </div>
      </div>
      <div class="horizontal center-justified layout flex" style="padding: 10px;">
        <mwc-icon-button
          class="pagination"
          id="previous-page"
          icon="navigate_before"
          ?disabled="${1===this.current_page}"
          @click="${e=>this._updateSessionPage(e)}"></mwc-icon-button>
        <wl-label style="padding-top: 5px; width:auto; text-align:center;">
        ${this.current_page} / ${Math.ceil(this.total_session_count/this.session_page_limit)}</wl-label>
        <mwc-icon-button
          class="pagination"
          id="next-page"
          icon="navigate_next"
          ?disabled="${this.total_session_count<=this.session_page_limit*this.current_page}"
          @click="${e=>this._updateSessionPage(e)}"></mwc-icon-button>
      </div>
      <backend-ai-dialog id="work-dialog" narrowLayout scrollable fixed backdrop>
        <span slot="title" id="work-title"></span>
        <div slot="action" class="horizontal layout center">
          <mwc-icon-button fab flat inverted icon="download" @click="${()=>this._downloadLogs()}">
          </mwc-icon-button>
          <mwc-icon-button fab flat inverted icon="refresh" @click="${e=>this._refreshLogs()}">
          </mwc-icon-button>
        </div>
        <div slot="content" id="work-area" style="overflow:scroll;"></div>
        <iframe id="work-page" frameborder="0" border="0" cellspacing="0"
                style="border-style: none;display: none;width: 100%;"></iframe>
      </backend-ai-dialog>
      <backend-ai-dialog id="terminate-session-dialog" fixed backdrop>
        <span slot="title">${E("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${E("usersettings.SessionTerminationDialog")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <wl-button class="warning fg red" inverted flat @click="${()=>this._terminateSessionWithCheck(!0)}">
            ${E("button.ForceTerminate")}
          </wl-button>
          <span class="flex"></span>
          <wl-button class="cancel" inverted flat @click="${e=>this._hideDialog(e)}">${E("button.Cancel")}
          </wl-button>
          <wl-button class="ok" @click="${()=>this._terminateSessionWithCheck()}">${E("button.Okay")}</wl-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="terminate-selected-sessions-dialog" fixed backdrop>
        <span slot="title">${E("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${E("usersettings.SessionTerminationDialog")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <wl-button class="warning fg red" inverted flat
                      @click="${()=>this._terminateSelectedSessionsWithCheck(!0)}">${E("button.ForceTerminate")}
          </wl-button>
          <span class="flex"></span>
          <wl-button class="cancel" inverted flat @click="${e=>this._hideDialog(e)}">${E("button.Cancel")}
          </wl-button>
          <wl-button class="ok" @click="${()=>this._terminateSelectedSessionsWithCheck()}">${E("button.Okay")}
          </wl-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="status-detail-dialog" narrowLayout fixed backdrop>
        <span slot="title">${E("session.StatusInfo")}</span>
        <div slot="content" id="status-detail"></div>
      </backend-ai-dialog>
      <backend-ai-dialog id="help-description" narrowLayout fixed backdrop>
        <span slot="title">${this._helpDescriptionTitle}</span>
        <div slot="content" class="horizontal layout center" style="margin:5px;">
        ${""==this._helpDescriptionIcon?I``:I`
          <img slot="graphic" alt="help icon" src="resources/icons/${this._helpDescriptionIcon}"
               style="width:64px;height:64px;margin-right:10px;"/>
        `}
          <div style="font-size:14px;">${R(this._helpDescription)}</div>
        </div>
      </backend-ai-dialog>
      ${this._renderCommitSessionConfirmationDialog(this._parseSessionInfoToCommitSessionInfo(null===(e=this.commitSessionDialog)||void 0===e?void 0:e.kernelImage,null===(t=this.commitSessionDialog)||void 0===t?void 0:t.sessionName,null===(i=this.commitSessionDialog)||void 0===i?void 0:i.sessionId))}
    `}_updateSessionPage(e){"previous-page"===e.target.id?this.current_page-=1:this.current_page+=1,this.refreshList()}};
/**
 @license
 Copyright (c) 2015-2023 Lablup Inc. All rights reserved.
 */
var ie;f([y({type:Boolean,reflect:!0})],te.prototype,"active",void 0),f([y({type:String})],te.prototype,"condition",void 0),f([y({type:Object})],te.prototype,"jobs",void 0),f([y({type:Array})],te.prototype,"compute_sessions",void 0),f([y({type:Array})],te.prototype,"terminationQueue",void 0),f([y({type:String})],te.prototype,"filterAccessKey",void 0),f([y({type:String})],te.prototype,"sessionNameField",void 0),f([y({type:Array})],te.prototype,"appSupportList",void 0),f([y({type:Object})],te.prototype,"appTemplate",void 0),f([y({type:Object})],te.prototype,"imageInfo",void 0),f([y({type:Array})],te.prototype,"_selected_items",void 0),f([y({type:Object})],te.prototype,"_boundControlRenderer",void 0),f([y({type:Object})],te.prototype,"_boundConfigRenderer",void 0),f([y({type:Object})],te.prototype,"_boundUsageRenderer",void 0),f([y({type:Object})],te.prototype,"_boundReservationRenderer",void 0),f([y({type:Object})],te.prototype,"_boundIdleChecksHeaderderer",void 0),f([y({type:Object})],te.prototype,"_boundIdleChecksRenderer",void 0),f([y({type:Object})],te.prototype,"_boundAgentRenderer",void 0),f([y({type:Object})],te.prototype,"_boundSessionInfoRenderer",void 0),f([y({type:Object})],te.prototype,"_boundArchitectureRenderer",void 0),f([y({type:Object})],te.prototype,"_boundCheckboxRenderer",void 0),f([y({type:Object})],te.prototype,"_boundUserInfoRenderer",void 0),f([y({type:Object})],te.prototype,"_boundStatusRenderer",void 0),f([y({type:Object})],te.prototype,"_boundSessionTypeRenderer",void 0),f([y({type:Boolean})],te.prototype,"refreshing",void 0),f([y({type:Boolean})],te.prototype,"is_admin",void 0),f([y({type:Boolean})],te.prototype,"is_superadmin",void 0),f([y({type:String})],te.prototype,"_connectionMode",void 0),f([y({type:Object})],te.prototype,"notification",void 0),f([y({type:Boolean})],te.prototype,"enableScalingGroup",void 0),f([y({type:Boolean})],te.prototype,"isDisplayingAllocatedShmemEnabled",void 0),f([y({type:String})],te.prototype,"listCondition",void 0),f([y({type:Object})],te.prototype,"refreshTimer",void 0),f([y({type:Object})],te.prototype,"kernel_labels",void 0),f([y({type:Object})],te.prototype,"kernel_icons",void 0),f([y({type:Object})],te.prototype,"indicator",void 0),f([y({type:String})],te.prototype,"_helpDescription",void 0),f([y({type:String})],te.prototype,"_helpDescriptionTitle",void 0),f([y({type:String})],te.prototype,"_helpDescriptionIcon",void 0),f([y({type:Set})],te.prototype,"activeIdleCheckList",void 0),f([y({type:Proxy})],te.prototype,"statusColorTable",void 0),f([y({type:Proxy})],te.prototype,"idleChecksTable",void 0),f([y({type:Proxy})],te.prototype,"sessionTypeColorTable",void 0),f([y({type:Number})],te.prototype,"sshPort",void 0),f([y({type:Number})],te.prototype,"vncPort",void 0),f([y({type:Number})],te.prototype,"current_page",void 0),f([y({type:Number})],te.prototype,"session_page_limit",void 0),f([y({type:Number})],te.prototype,"total_session_count",void 0),f([y({type:Number})],te.prototype,"_APIMajorVersion",void 0),f([y({type:Object})],te.prototype,"selectedSessionStatus",void 0),f([y({type:Boolean})],te.prototype,"isUserInfoMaskEnabled",void 0),f([w("#loading-spinner")],te.prototype,"spinner",void 0),f([w("#list-grid")],te.prototype,"_grid",void 0),f([w("#access-key-filter")],te.prototype,"accessKeyFilterInput",void 0),f([w("#multiple-action-buttons")],te.prototype,"multipleActionButtons",void 0),f([w("#access-key-filter-helper-text")],te.prototype,"accessKeyFilterHelperText",void 0),f([w("#terminate-session-dialog")],te.prototype,"terminateSessionDialog",void 0),f([w("#terminate-selected-sessions-dialog")],te.prototype,"terminateSelectedSessionsDialog",void 0),f([w("#status-detail-dialog")],te.prototype,"sessionStatusInfoDialog",void 0),f([w("#work-dialog")],te.prototype,"workDialog",void 0),f([w("#help-description")],te.prototype,"helpDescriptionDialog",void 0),f([w("#commit-session-dialog")],te.prototype,"commitSessionDialog",void 0),f([w("#commit-current-session-path-input")],te.prototype,"commitSessionInput",void 0),f([w("#list-status")],te.prototype,"_listStatus",void 0),te=Q=f([k("backend-ai-session-list")],te);let se=ie=class extends x{constructor(){super(),this._status="inactive",this.active=!1,this.is_admin=!1,this.enableInferenceWorkload=!1,this.enableSFTPSession=!1,this.filterAccessKey="",this._connectionMode="API",this._defaultFileName="",this.active=!1,this._status="inactive"}static get styles(){return[A,S,T,M,z,i`
        h3.tab {
          background-color: var(--general-tabbar-background-color);
          border-radius: 5px 5px 0 0;
        }
        mwc-tab-bar {
          --mdc-theme-primary: var(--general-sidebar-selected-color);
          --mdc-text-transform: none;
          --mdc-tab-color-default: var(--general-tabbar-background-color);
          --mdc-tab-text-label-color-default: var(--general-sidebar-color);
        }

        wl-button {
          --button-bg:  var(--paper-light-green-50);
          --button-bg-hover:  var(--paper-green-100);
          --button-bg-active:  var(--paper-green-600);
        }

        wl-label.unlimited {
          margin: 12px 0;
        }

        wl-label.warning {
          font-size: 10px;
          --label-color: var(--paper-red-600);
        }

        wl-checkbox#export-csv-checkbox {
          margin-right: 5px;
          --checkbox-size: 10px;
          --checkbox-border-radius: 2px;
          --checkbox-bg-checked: var(--paper-green-800);
          --checkbox-checkmark-stroke-color: var(--paper-lime-100);
          --checkbox-color-checked: var(--paper-green-800);
        }

        backend-ai-dialog wl-textfield {
          padding: 10px 0;
          --input-font-family: var(--general-font-family);
          --input-font-size: 12px;
          --input-color-disabled: #bbbbbb;
          --input-label-color-disabled: #222222;
          --input-label-font-size: 12px;
          --input-border-style-disabled: 1px solid #cccccc;
        }

        mwc-menu {
          --mdc-theme-surface: #f1f1f1;
          --mdc-menu-item-height : auto;
        }

        mwc-menu#dropdown-menu {
          position: relative;
          left: -170px;
          top: 50px;
        }

        mwc-list-item {
          font-size : 14px;
        }

        mwc-icon-button {
          --mdc-icon-size: 20px;
          color: var(--paper-grey-700);
        }

        mwc-icon-button#dropdown-menu-button {
          margin-left: 10px;
        }

        mwc-textfield {
          width: 100%;
          --mdc-text-field-fill-color: transparent;
          --mdc-theme-primary: var(--paper-green-600);
        }

        .hide-scrollbar::-webkit-scrollbar {
          display: none;
        }

        backend-ai-resource-monitor {
          margin: 10px 50px;
        }

        backend-ai-session-launcher#session-launcher {
          --component-width: 100px;
          --component-shadow-color: transparent;
        }
        @media screen and (max-width: 805px) {
          mwc-tab {
            --mdc-typography-button-font-size: 10px;
          }
        }
      `]}firstUpdated(){this.notification=globalThis.lablupNotification,document.addEventListener("backend-ai-session-list-refreshed",(()=>{this.runningJobs.refreshList(!0,!1)})),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.is_admin=globalThis.backendaiclient.is_admin,this._connectionMode=globalThis.backendaiclient._config._connectionMode}),!0):(this.is_admin=globalThis.backendaiclient.is_admin,this._connectionMode=globalThis.backendaiclient._config._connectionMode)}async _viewStateChanged(e){if(await this.updateComplete,!1===e){this.resourceMonitor.removeAttribute("active"),this._status="inactive";for(let e=0;e<this.sessionList.length;e++)this.sessionList[e].removeAttribute("active");return}const t=()=>{this.enableInferenceWorkload=globalThis.backendaiclient.supports("inference-workload"),this.enableSFTPSession=globalThis.backendaiclient.supports("sftp-scaling-group"),this.resourceMonitor.setAttribute("active","true"),this.runningJobs.setAttribute("active","true"),this._status="active"};void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{t()}),!0):t()}_toggleDialogCheckbox(e){const t=e.target,i=this.dateFromInput,s=this.dateToInput;i.disabled=t.checked,s.disabled=t.checked}_triggerClearTimeout(){const e=new CustomEvent("backend-ai-clear-timeout");document.dispatchEvent(e)}_showTab(e){var t,i,s;const o=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".tab-content");for(let e=0;e<o.length;e++)o[e].style.display="none";(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+e.title+"-lists")).style.display="block";for(let e=0;e<this.sessionList.length;e++)this.sessionList[e].removeAttribute("active");this._triggerClearTimeout(),(null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#"+e.title+"-jobs")).setAttribute("active","true")}_toggleDropdown(e){const t=this.dropdownMenu,i=e.target;t.anchor=i,t.open||t.show()}_openExportToCsvDialog(){const e=this.dropdownMenu;e.open&&e.close(),console.log("Downloading CSV File..."),this._defaultFileName=this._getDefaultCSVFileName(),this.exportToCsvDialog.show()}_getFirstDateOfMonth(){const e=new Date;return new Date(e.getFullYear(),e.getMonth(),2).toISOString().substring(0,10)}_getDefaultCSVFileName(){return(new Date).toISOString().substring(0,10)+"_"+(new Date).toTimeString().slice(0,8).replace(/:/gi,"-")}_validateDateRange(){const e=this.dateToInput,t=this.dateFromInput;if(e.value&&t.value){new Date(e.value).getTime()<new Date(t.value).getTime()&&(e.value=t.value)}}_automaticScaledTime(e){let t=Object();const i=["D","H","M","S"],s=[864e5,36e5,6e4,1e3];for(let o=0;o<s.length;o++)Math.floor(e/s[o])>0&&(t[i[o]]=Math.floor(e/s[o]),e%=s[o]);return 0===Object.keys(t).length&&(t=e>0?{MS:e}:{NODATA:1}),t}static bytesToMiB(e,t=1){return Number(e/2**20).toFixed(1)}_exportToCSV(){const e=this.exportFileNameInput;if(!e.validity.valid)return;const t=[];let i;i=globalThis.backendaiclient.supports("avoid-hol-blocking")?["RUNNING","RESTARTING","TERMINATING","PENDING","SCHEDULED","PREPARING","PULLING","TERMINATED","CANCELLED","ERROR"]:["RUNNING","RESTARTING","TERMINATING","PENDING","PREPARING","PULLING","TERMINATED","CANCELLED","ERROR"],globalThis.backendaiclient.supports("detailed-session-states")&&(i=i.join(","));const s=["id","name","image","created_at","terminated_at","status","status_info","access_key"];"SESSION"===this._connectionMode&&s.push("user_email"),globalThis.backendaiclient.is_superadmin?s.push("containers {container_id agent occupied_slots live_stat last_stat}"):s.push("containers {container_id occupied_slots live_stat last_stat}");const o=globalThis.backendaiclient.current_group_id();globalThis.backendaiclient.computeSession.listAll(s,i,this.filterAccessKey,100,0,o).then((i=>{const s=i;if(0===s.length)return this.notification.text=D("session.NoSession"),this.notification.show(),void this.exportToCsvDialog.hide();s.forEach((e=>{const i={};if(i.id=e.id,i.name=e.name,i.image=e.image.split("/")[2]||e.image.split("/")[1],i.status=e.status,i.status_info=e.status_info,i.access_key=e.access_key,i.created_at=e.created_at,i.terminated_at=e.terminated_at,e.containers&&e.containers.length>0){const t=e.containers[0];i.container_id=t.container_id;const s=t.occupied_slots?JSON.parse(t.occupied_slots):null;s&&(i.cpu_slot=parseInt(s.cpu),i.mem_slot=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(s.mem,"g")).toFixed(2),s["cuda.shares"]&&(i.cuda_shares=s["cuda.shares"]),s["cuda.device"]&&(i.cuda_device=s["cuda.device"]),s["tpu.device"]&&(i.tpu_device=s["tpu.device"]),s["rocm.device"]&&(i.rocm_device=s["rocm.device"]),s["ipu.device"]&&(i.ipu_device=s["ipu.device"]),s["atom.device"]&&(i.atom_device=s["atom.device"]),s["warboy.device"]&&(i.warboy_device=s["warboy.device"]));const o=t.live_stat?JSON.parse(t.live_stat):null;o&&(o.cpu_used&&o.cpu_used.current?i.cpu_used_time=this._automaticScaledTime(o.cpu_used.current):i.cpu_used_time=0,o.io_read?i.io_read_bytes_mb=ie.bytesToMiB(o.io_read.current):i.io_read_bytes_mb=0,o.io_write?i.io_write_bytes_mb=ie.bytesToMiB(o.io_write.current):i.io_write_bytes_mb=0),t.agent&&(i.agent=t.agent)}t.push(i)})),N.exportToCsv(e.value,t),this.notification.text=D("session.DownloadingCSVFile"),this.notification.show(),this.exportToCsvDialog.hide()}))}render(){return I`
      <link rel="stylesheet" href="resources/custom.css">
      <lablup-activity-panel title="${E("summary.ResourceStatistics")}" elevation="1" autowidth>
        <div slot="message">
          <backend-ai-resource-monitor location="session" id="resource-monitor" ?active="${!0===this.active}"></backend-ai-resource-monitor>
        </div>
      </lablup-activity-panel>
      <lablup-activity-panel title="${E("summary.Announcement")}" elevation="1" horizontalsize="2x" style="display:none;">
      </lablup-activity-panel>
      <lablup-activity-panel elevation="1" autowidth narrow noheader>
        <div slot="message">
          <h3 class="tab horizontal center layout" style="margin-top:0;margin-bottom:0;">
            <div class="scroll hide-scrollbar">
              <div class="horizontal layout flex start-justified" style="width:70%;">
                <mwc-tab-bar>
                  <mwc-tab title="running" label="${E("session.Running")}" @click="${e=>this._showTab(e.target)}"></mwc-tab>
                  <mwc-tab title="interactive" label="${E("session.Interactive")}" @click="${e=>this._showTab(e.target)}"></mwc-tab>
                  <mwc-tab title="batch" label="${E("session.Batch")}" @click="${e=>this._showTab(e.target)}"></mwc-tab>
                  ${this.enableInferenceWorkload?I`
                  <mwc-tab title="inference" label="${E("session.Inference")}" @click="${e=>this._showTab(e.target)}"></mwc-tab>
                  `:I``}
                  ${this.enableSFTPSession?I`
                  <mwc-tab title="system" label="${E("session.System")}" @click="${e=>this._showTab(e.target)}"></mwc-tab>
                  `:I``}
                  <mwc-tab title="finished" label="${E("session.Finished")}" @click="${e=>this._showTab(e.target)}"></mwc-tab>
                </mwc-tab-bar>
              </div>
            </div>
            ${this.is_admin?I`
              <div style="position: relative;">
                <mwc-icon-button id="dropdown-menu-button" icon="more_horiz" raised
                                  @click="${e=>this._toggleDropdown(e)}"></mwc-icon-button>
                  <mwc-menu id="dropdown-menu">
                    <mwc-list-item>
                      <a class="horizontal layout start center" @click="${()=>this._openExportToCsvDialog()}">
                        <mwc-icon style="color:#242424;padding-right:10px;">get_app</mwc-icon>
                        ${E("session.exportCSV")}
                      </a>
                    </mwc-list-item>
                  </mwc-menu>
                </div>
              `:I``}
            <div class="horizontal layout flex end-justified" style="margin-right:20px;">
              <backend-ai-session-launcher location="session" id="session-launcher" ?active="${!0===this.active}"></backend-ai-session-launcher>
            </div>
          </h3>
          <div id="running-lists" class="tab-content">
            <backend-ai-session-list id="running-jobs" condition="running"></backend-ai-session-list>
          </div>
          <div id="interactive-lists" class="tab-content" style="display:none;">
            <backend-ai-session-list id="interactive-jobs" condition="interactive"></backend-ai-session-list>
          </div>
          <div id="batch-lists" class="tab-content" style="display:none;">
            <backend-ai-session-list id="batch-jobs" condition="batch"></backend-ai-session-list>
          </div>
          ${this.enableInferenceWorkload?I`
          <div id="inference-lists" class="tab-content" style="display:none;">
            <backend-ai-session-list id="inference-jobs" condition="inference"></backend-ai-session-list>
          </div>`:I``}
          ${this.enableSFTPSession?I`
          <div id="system-lists" class="tab-content" style="display:none;">
            <backend-ai-session-list id="system-jobs" condition="system"></backend-ai-session-list>
          </div>`:I``}
          <div id="finished-lists" class="tab-content" style="display:none;">
            <backend-ai-session-list id="finished-jobs" condition="finished"></backend-ai-session-list>
          </div>
          <div id="others-lists" class="tab-content" style="display:none;">
            <backend-ai-session-list id="others-jobs" condition="others"></backend-ai-session-list>
          </div>
        </div>
      </lablup-activity-panel>
      <backend-ai-dialog id="export-to-csv" fixed backdrop>
        <span slot="title">${E("session.ExportSessionListToCSVFile")}</span>
        <div slot="content">
          <mwc-textfield id="export-file-name" label="File name"
                          validationMessage="${E("data.explorer.ValueRequired")}"
                          value="${"session_"+this._defaultFileName}" required
                          style="margin-bottom:10px;"></mwc-textfield>
          <div class="horizontal center layout" style="display:none;">
            <wl-textfield id="date-from" label="From" type="date" style="margin-right:10px;"
                          value="${this._getFirstDateOfMonth()}" required
                          @change="${this._validateDateRange}">
              <wl-icon slot="before">date_range</wl-icon>
            </wl-textfield>
            <wl-textfield id="date-to" label="To" type="date"
                          value="${(new Date).toISOString().substring(0,10)}" required
                          @change="${this._validateDateRange}">
              <wl-icon slot="before">date_range</wl-icon>
            </wl-textfield>
          </div>
          <div class="horizontal center layout" style="display:none;">
            <wl-checkbox id="export-csv-checkbox" @change="${e=>this._toggleDialogCheckbox(e)}"></wl-checkbox>
            <wl-label class="unlimited" for="export-csv-checkbox">Export All-time data</wl-label>
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button unelevated
                      fullwidth
                      icon="get_app"
                      label="${E("session.ExportCSVFile")}"
                      @click="${this._exportToCSV}"></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};f([y({type:String})],se.prototype,"_status",void 0),f([y({type:Boolean,reflect:!0})],se.prototype,"active",void 0),f([y({type:Boolean})],se.prototype,"is_admin",void 0),f([y({type:Boolean})],se.prototype,"enableInferenceWorkload",void 0),f([y({type:Boolean})],se.prototype,"enableSFTPSession",void 0),f([y({type:String})],se.prototype,"filterAccessKey",void 0),f([y({type:String})],se.prototype,"_connectionMode",void 0),f([y({type:Object})],se.prototype,"_defaultFileName",void 0),f([function(t){return e({descriptor:e=>({get(){var e,i;return null!==(i=null===(e=this.renderRoot)||void 0===e?void 0:e.querySelectorAll(t))&&void 0!==i?i:[]},enumerable:!0,configurable:!0})})}("backend-ai-session-list")],se.prototype,"sessionList",void 0),f([w("#running-jobs")],se.prototype,"runningJobs",void 0),f([w("#resource-monitor")],se.prototype,"resourceMonitor",void 0),f([w("#export-file-name")],se.prototype,"exportFileNameInput",void 0),f([w("#date-from")],se.prototype,"dateFromInput",void 0),f([w("#date-to")],se.prototype,"dateToInput",void 0),f([w("#dropdown-menu")],se.prototype,"dropdownMenu",void 0),f([w("#export-to-csv")],se.prototype,"exportToCsvDialog",void 0),se=ie=f([k("backend-ai-session-view")],se);
