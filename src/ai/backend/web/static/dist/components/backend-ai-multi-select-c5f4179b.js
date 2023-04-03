import{G as e,_ as t,H as i,J as a,K as s,L as o,c as r,e as l,a as n,s as c,d,I as h,N as m,b as p,k as u,f as b,i as g,y as v}from"./backend-ai-webui-8cfa3078.js";import{T as y,a as f}from"./textfield-29e3f043.js";import"./mwc-check-list-item-783de9f1.js";let x=class extends f{connectedCallback(){super.connectedCallback(),this.setAttribute("aria-multiline","true")}firstUpdated(e){super.firstUpdated(e),this.refreshHeight()}onInput(e){super.onInput(e),this.refreshHeight()}refreshHeight(){a(this)||requestAnimationFrame((()=>{this.setHeight(1);const e=this.$formElement.scrollHeight;this.setHeight(e)}))}setHeight(e){this.$formElement.style.setProperty("--_textarea-height",""+(null==e?"":`${e}px`))}renderFormElement(){return s` <textarea id="${this.formElementId}" .value="${this.value}" ?required="${this.required}" ?disabled="${this.disabled}" ?readonly="${this.readonly}" aria-label="${o(this.label)}" name="${o(this.name)}" pattern="${o(this.pattern)}" autocomplete="${o(this.autocomplete)}" minlength="${o(this.minLength)}" maxlength="${o(this.maxLength)}" rows="1" tabindex="${this.disabled?-1:0}">
${this.initialValue||""}</textarea> `}};
/**
 @license
 Copyright (c) 2015-2023 Lablup Inc. All rights reserved.
 */
var w;x.styles=[...y.styles,e("::slotted(textarea){height:var(--textarea-height,var(--_textarea-height));min-height:var(--textarea-min-height,var(--textarea-height,var(--_textarea-height)));max-height:var(--textarea-max-height);resize:var(--textarea-resize,none)}:host(:focus) ::slotted(textarea),:host(:hover) ::slotted(textarea){will-change:height}")],x=t([i("wl-textarea")],x);let I=w=class extends c{constructor(){super(),this.label="",this.enableClearButton=!1,this.openUp=!1,this.selectedItemList=[],this.items=[]}static get styles(){return[d,h,m,p,u,b,g`
        lablup-shields {
          margin: 1px;
        }

        span.title {
          font-size: var(--select-title-font-size, 14px);
          font-weight: var(--select-title-font-weight, 500);
        }

        mwc-button {
          margin: var(--selected-item-margin, 3px);
          --mdc-theme-primary: var(--selected-item-theme-color);
          --mdc-theme-on-primary: var(--selected-item-theme-font-color);
          --mdc-typography-font-family: var(--selected-item-font-family);
          --mdc-typography-button-font-size: var(--selected-item-font-size);
          --mdc-typography-button-text-transform: var(--selected-item-text-transform);
        }

        mwc-button[unelevated] {
          --mdc-theme-primary: var(--selected-item-unelevated-theme-color);
          --mdc-theme-on-primary: var(--selected-item-unelevated-theme-font-color);
        }

        mwc-button[outlined] {
          --mdc-theme-primary: var(--selected-item-outlined-theme-color);
          --mdc-theme-on-primary: var(--selected-item-outlined-theme-font-color);
        }
        
        mwc-list {
          font-family: var(--general-font-family);
          width: 100%;
          position: absolute;
          left: 0;
          right: 0;
          z-index: 1;
          border-radius: var(--select-background-border-radius);
          background-color: var(--select-background-color, #efefef);
          --mdc-theme-primary: var(--select-primary-theme);
          --mdc-theme-secondary: var(--select-secondary-theme);
          box-shadow: var(--select-box-shadow);
        }

        mwc-list > mwc-check-list-item {
          background-color: var(--select-background-color, #efefef);
        }

        .selected-area {
          background-color: var(--select-background-color, #efefef);
          border-radius: var(--selected-area-border-radius, 5px);
          border: var(--selected-area-border, 1px solid rgba(0,0,0,1));
          padding: var(--selected-area-padding, 10px);
          min-height: var(--selected-area-min-height, 24px);
          height: var(--selected-area-height, auto);
        }

        .expand {
          transform:rotateX(180deg) !important;
        }
      `]}_showMenu(){this._modifyListPosition(this.items.length),this.menu.style.display=""}_hideMenu(){this.dropdownIcon.on=!1,this.dropdownIcon.classList.remove("expand"),this.menu.style.display="none"}_toggleMenuVisibility(e){this.dropdownIcon.classList.toggle("expand"),e.detail.isOn?this._showMenu():this._hideMenu()}_modifyListPosition(e=0){const t=`-${w.DEFAULT_ITEM_HEIGHT*e+(e===this.items.length?w.DEFAULT_ITEM_MARGIN:0)}px`;this.openUp?this.comboBox.style.top=t:this.comboBox.style.bottom=t}_updateSelection(e){const t=[...e.detail.index],i=this.comboBox.items.filter(((e,i,a)=>t.includes(i))).map((e=>e.value));this.selectedItemList=i}_deselectItem(e){const t=e.target;this.comboBox.selected.forEach(((e,i,a)=>{e.value===t&&this.comboBox.toggle(i)})),this.selectedItemList=this.selectedItemList.filter((e=>e!==t.label))}_deselectAllItems(){this.comboBox.selected.forEach(((e,t,i)=>{this.comboBox.toggle(t)})),this.selectedItemList=[]}firstUpdated(){var e;this.openUp=null!==this.getAttribute("open-up"),this.label=null!==(e=this.getAttribute("label"))&&void 0!==e?e:""}connectedCallback(){super.connectedCallback()}disconnectedCallback(){super.disconnectedCallback()}render(){return v`
    <span class="title">${this.label}</span>
    <div class="layout ${this.openUp?"vertical-reverse":"vertical"}">
      <div class="horizontal layout justified start selected-area center">
        <div class="horizontal layout start-justified wrap">
          ${this.selectedItemList.map((e=>v`
            <mwc-button unelevated trailingIcon label=${e} icon="close"
                @click=${e=>this._deselectItem(e)}></mwc-button>
            `))}
        </div>
        <mwc-icon-button-toggle id="dropdown-icon" 
            onIcon="arrow_drop_down" offIcon="arrow_drop_down"
            @icon-button-toggle-change="${e=>this._toggleMenuVisibility(e)}"></mwc-icon-button-toggle>
      </div>
      <div id="menu" class="vertical layout flex" style="position:relative;display:none;">
        <mwc-list id="list" activatable multi @selected="${e=>this._updateSelection(e)}">
          ${this.items.map((e=>v`
            <mwc-check-list-item value=${e} ?selected="${this.selectedItemList.includes(e)}">${e}</mwc-check-list-item>
          `))}
        </mwc-list>
      </div>
    </div>
    `}};I.DEFAULT_ITEM_HEIGHT=56,I.DEFAULT_ITEM_MARGIN=25,t([r("#list")],I.prototype,"comboBox",void 0),t([r("#menu",!0)],I.prototype,"menu",void 0),t([r("#dropdown-icon",!0)],I.prototype,"dropdownIcon",void 0),t([l({type:Array})],I.prototype,"selectedItemList",void 0),t([l({type:String,attribute:"label"})],I.prototype,"label",void 0),t([l({type:Array})],I.prototype,"items",void 0),t([l({type:Boolean,attribute:"enable-clear-button"})],I.prototype,"enableClearButton",void 0),t([l({type:Boolean,attribute:"open-up"})],I.prototype,"openUp",void 0),I=w=t([n("backend-ai-multi-select")],I);
