import{_ as e,e as t,n as i,t as o,s,b as a,I as l,a0 as r,a as d,u as c,c as n,i as m,x as p}from"./backend-ai-webui-dvRyOX_e.js";import"./mwc-check-list-item-BMr63zxO.js";import{r as h}from"./state-BGEx6bYL.js";var v;let u=v=class extends s{constructor(){super(),this.label="",this.validationMessage="",this.enableClearButton=!1,this.openUp=!1,this.required=!1,this._valid=!0,this.selectedItemList=[],this.items=[]}static get styles(){return[a,l,r,d,c,n,m`
        lablup-shields {
          margin: 1px;
        }

        span.title {
          font-size: var(--select-title-font-size, 14px);
          font-weight: var(--select-title-font-weight, 500);
          padding-left: var(--select-title-padding-left, 0px);
        }

        mwc-button {
          margin: var(--selected-item-margin, 3px);
          --mdc-theme-primary: var(--selected-item-theme-color);
          --mdc-theme-on-primary: var(--selected-item-theme-font-color);
          --mdc-typography-font-family: var(--selected-item-font-family);
          --mdc-typography-button-font-size: var(--selected-item-font-size);
          --mdc-typography-button-text-transform: var(
            --selected-item-text-transform
          );
        }

        mwc-button[unelevated] {
          --mdc-theme-primary: var(--selected-item-unelevated-theme-color);
          --mdc-theme-on-primary: var(
            --selected-item-unelevated-theme-font-color
          );
        }

        mwc-button[outlined] {
          --mdc-theme-primary: var(--selected-item-outlined-theme-color);
          --mdc-theme-on-primary: var(
            --selected-item-outlined-theme-font-color
          );
        }

        mwc-list {
          font-family: var(--token-fontFamily);
          width: 100%;
          position: absolute;
          left: 0;
          right: 0;
          z-index: 1;
          border-radius: var(--select-background-border-radius);
          background-color: var(--select-background-color, #efefef);
          --mdc-theme-primary: var(--select-primary-theme);
          --mdc-theme-secondary: var(--select-secondary-theme);
          --mdc-theme-on-surface: var(--selected-item-disabled-text-color);
          box-shadow: var(--select-box-shadow);
        }

        mwc-list > mwc-check-list-item {
          background-color: var(--select-background-color, #efefef);
          color: var(--select-color);
        }

        div.invalid {
          border: 1px solid var(--select-error-color, #b00020);
        }

        .selected-area {
          background-color: var(--select-background-color, #efefef);
          border-radius: var(--selected-area-border-radius, 5px);
          border: var(
            --selected-area-border,
            1px solid var(--token-colorBorder, rgba(0, 0, 0, 1))
          );
          padding: var(--selected-area-padding, 10px);
          min-height: var(--selected-area-min-height, 24px);
          height: var(--selected-area-height, auto);
        }

        .expand {
          transform: rotateX(180deg) !important;
        }

        .validation-msg {
          font-size: var(--selected-validation-msg-font-size, 12px);
          padding-right: var(--selected-validation-msg-padding, 16px);
          padding-left: var(--selected-validation-msg-padding, 16px);
          color: var(--select-error-color, #b00020);
        }
      `]}_showMenu(){this._modifyListPosition(this.items.length),this.menu.style.display=""}_hideMenu(){this.dropdownIcon.on=!1,this.dropdownIcon.classList.remove("expand"),this.menu.style.display="none"}_toggleMenuVisibility(e){this.dropdownIcon.classList.toggle("expand"),e.detail.isOn?this._showMenu():this._hideMenu()}_modifyListPosition(e=0){const t=`-${v.DEFAULT_ITEM_HEIGHT*e+(e===this.items.length?v.DEFAULT_ITEM_MARGIN:0)}px`;this.openUp?this.comboBox.style.top=t:this.comboBox.style.bottom=t}_updateSelection(e){const t=[...e.detail.index],i=this.comboBox.items.filter(((e,i,o)=>t.includes(i))).map((e=>e.value));this.selectedItemList=i,this._checkValidity()}_deselectItem(e){const t=e.target;this.comboBox.selected.forEach(((e,i,o)=>{e.value===t&&this.comboBox.toggle(i)})),this.selectedItemList=this.selectedItemList.filter((e=>e!==t.label))}_deselectAllItems(){this.comboBox.selected.forEach(((e,t,i)=>{this.comboBox.toggle(t)})),this.selectedItemList=[]}_checkValidity(){this._valid=!this.required||this.selectedItemList.length>0}firstUpdated(){var e,t;this.openUp=null!==this.getAttribute("open-up"),this.label=null!==(e=this.getAttribute("label"))&&void 0!==e?e:"",this.validationMessage=null!==(t=this.getAttribute("validation-message"))&&void 0!==t?t:"",this._checkValidity()}connectedCallback(){super.connectedCallback()}disconnectedCallback(){super.disconnectedCallback()}render(){return p`
      <span class="title">${this.label}</span>
      <div class="layout ${this.openUp?"vertical-reverse":"vertical"}">
        <div
          class="horizontal layout justified start selected-area center ${this.required&&0===this.selectedItemList.length?"invalid":""}"
        >
          <div class="horizontal layout start-justified wrap">
            ${this.selectedItemList.map((e=>p`
                <mwc-button
                  unelevated
                  trailingIcon
                  label=${e}
                  icon="close"
                  @click=${e=>this._deselectItem(e)}
                ></mwc-button>
              `))}
          </div>
          <mwc-icon-button-toggle
            id="dropdown-icon"
            onIcon="arrow_drop_down"
            offIcon="arrow_drop_down"
            @icon-button-toggle-change="${e=>this._toggleMenuVisibility(e)}"
          ></mwc-icon-button-toggle>
        </div>
        <div
          id="menu"
          class="vertical layout flex"
          style="position:relative;display:none;"
        >
          <mwc-list
            id="list"
            activatable
            multi
            @selected="${e=>this._updateSelection(e)}"
          >
            ${this.items.map((e=>p`
                <mwc-check-list-item
                  value=${e}
                  ?selected="${this.selectedItemList.includes(e)}"
                >
                  ${e}
                </mwc-check-list-item>
              `))}
          </mwc-list>
        </div>
      </div>
      <span
        class="validation-msg"
        style="display:${this._valid?"none":"block"}"
      >
        ${this.validationMessage}
      </span>
    `}};u.DEFAULT_ITEM_HEIGHT=56,u.DEFAULT_ITEM_MARGIN=25,e([t("#list")],u.prototype,"comboBox",void 0),e([t("#menu",!0)],u.prototype,"menu",void 0),e([t("#dropdown-icon",!0)],u.prototype,"dropdownIcon",void 0),e([i({type:Array})],u.prototype,"selectedItemList",void 0),e([i({type:Array})],u.prototype,"items",void 0),e([i({type:String,attribute:"label"})],u.prototype,"label",void 0),e([i({type:String,attribute:"validation-message"})],u.prototype,"validationMessage",void 0),e([i({type:Boolean,attribute:"enable-clear-button"})],u.prototype,"enableClearButton",void 0),e([i({type:Boolean,attribute:"open-up"})],u.prototype,"openUp",void 0),e([i({type:Boolean,attribute:"required"})],u.prototype,"required",void 0),e([h()],u.prototype,"_valid",void 0),u=v=e([o("backend-ai-multi-select")],u);
