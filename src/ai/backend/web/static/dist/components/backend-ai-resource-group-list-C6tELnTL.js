import{_ as e,e as t,n as i,Z as o,t as r,h as s,b as a,I as l,a1 as n,a as c,F as d,c as u,i as p,k as h,B as v,d as m,Q as g,g as b,f}from"./backend-ai-webui-CrYAk2kU.js";import"./mwc-check-list-item-GAU3w8ue.js";import"./mwc-switch-DBXdshNs.js";import"./vaadin-item-cN1jHkT4.js";import"./vaadin-item-mixin-BPsCvSRg.js";var y;let x=y=class extends s{constructor(){super(),this.label="",this.validationMessage="",this.enableClearButton=!1,this.openUp=!1,this.required=!1,this._valid=!0,this.selectedItemList=[],this.items=[]}static get styles(){return[a,l,n,c,d,u,p`
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
      `]}_showMenu(){this._modifyListPosition(this.items.length),this.menu.style.display=""}_hideMenu(){this.dropdownIcon.on=!1,this.dropdownIcon.classList.remove("expand"),this.menu.style.display="none"}_toggleMenuVisibility(e){this.dropdownIcon.classList.toggle("expand"),e.detail.isOn?this._showMenu():this._hideMenu()}_modifyListPosition(e=0){const t=`-${y.DEFAULT_ITEM_HEIGHT*e+(e===this.items.length?y.DEFAULT_ITEM_MARGIN:0)}px`;this.openUp?this.comboBox.style.top=t:this.comboBox.style.bottom=t}_updateSelection(e){const t=[...e.detail.index],i=this.comboBox.items.filter(((e,i,o)=>t.includes(i))).map((e=>e.value));this.selectedItemList=i,this._checkValidity()}_deselectItem(e){const t=e.target;this.comboBox.selected.forEach(((e,i,o)=>{e.value===t&&this.comboBox.toggle(i)})),this.selectedItemList=this.selectedItemList.filter((e=>e!==t.label))}_deselectAllItems(){this.comboBox.selected.forEach(((e,t,i)=>{this.comboBox.toggle(t)})),this.selectedItemList=[]}_checkValidity(){this._valid=!this.required||this.selectedItemList.length>0}firstUpdated(){var e,t;this.openUp=null!==this.getAttribute("open-up"),this.label=null!==(e=this.getAttribute("label"))&&void 0!==e?e:"",this.validationMessage=null!==(t=this.getAttribute("validation-message"))&&void 0!==t?t:"",this._checkValidity()}connectedCallback(){super.connectedCallback()}disconnectedCallback(){super.disconnectedCallback()}render(){return h`
      <span class="title">${this.label}</span>
      <div class="layout ${this.openUp?"vertical-reverse":"vertical"}">
        <div
          class="horizontal layout justified start selected-area center ${this.required&&0===this.selectedItemList.length?"invalid":""}"
        >
          <div class="horizontal layout start-justified wrap">
            ${this.selectedItemList.map((e=>h`
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
            ${this.items.map((e=>h`
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
    `}};x.DEFAULT_ITEM_HEIGHT=56,x.DEFAULT_ITEM_MARGIN=25,e([t("#list")],x.prototype,"comboBox",void 0),e([t("#menu",!0)],x.prototype,"menu",void 0),e([t("#dropdown-icon",!0)],x.prototype,"dropdownIcon",void 0),e([i({type:Array})],x.prototype,"selectedItemList",void 0),e([i({type:Array})],x.prototype,"items",void 0),e([i({type:String,attribute:"label"})],x.prototype,"label",void 0),e([i({type:String,attribute:"validation-message"})],x.prototype,"validationMessage",void 0),e([i({type:Boolean,attribute:"enable-clear-button"})],x.prototype,"enableClearButton",void 0),e([i({type:Boolean,attribute:"open-up"})],x.prototype,"openUp",void 0),e([i({type:Boolean,attribute:"required"})],x.prototype,"required",void 0),e([o()],x.prototype,"_valid",void 0),x=y=e([r("backend-ai-multi-select")],x);let w=class extends v{constructor(){super(),this._boundControlRenderer=this._controlRenderer.bind(this),this.allowedSessionTypes=["interactive","batch","inference"],this.enableSchedulerOpts=!1,this.enableWSProxyAddr=!1,this.enableIsPublic=!1,this.functionCount=0,this.active=!1,this.schedulerTypes=["fifo","lifo","drf"],this.resourceGroups=[],this.resourceGroupInfo={},this.domains=[]}static get styles(){return[a,l,c,p`
        h4 {
          font-weight: 200;
          font-size: 14px;
          margin: 0px;
          padding: 5px 15px 5px 20px;
        }

        backend-ai-dialog {
          --component-min-width: 350px;
        }

        backend-ai-dialog mwc-textfield,
        backend-ai-dialog mwc-textarea {
          width: 100%;
          margin: 5px auto 5px auto;
          --mdc-typography-font-family: var(--token-fontFamily);
          --mdc-theme-primary: var(--general-textfield-selected-color);
        }

        mwc-button[raised] {
          margin-left: var(--token-marginXXS);
        }

        mwc-button.full-size,
        mwc-button.full {
          width: 100%;
          margin: 10px auto;
          background-image: none;
          --mdc-button-outline-width: 2px;
        }

        mwc-textarea {
          height: 135px;
        }

        mwc-select {
          width: 100%;
        }

        mwc-list-item {
          --mdc-menu-item-height: 20px;
        }

        #resource-group-detail-dialog {
          --component-width: 500px;
        }

        #resource-group-dialog {
          --component-width: 350px;
        }

        lablup-expansion {
          --expansion-content-padding: 2px;
          --expansion-header-padding: 16px;
          --expansion-margin-open: 0;
        }

        backend-ai-dialog h4 {
          font-weight: 700;
          font-size: 14px;
          padding: 5px 15px 5px 12px;
          margin: 0 0 10px 0;
          display: block;
          height: 20px;
          border-bottom: 1px solid var(--token-colorBorder, #ddd);
        }

        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 228px);
        }

        vaadin-item {
          padding: 5px 17px 5px 17px;
          font-size: 12px;
          font-weight: 100;
        }

        .scheduler-option-value {
          font-size: 16px;
          font-weight: 700;
        }
      `]}firstUpdated(){this.notification=globalThis.lablupNotification}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.enableSchedulerOpts=globalThis.backendaiclient.supports("scheduler-opts"),this.enableWSProxyAddr=globalThis.backendaiclient.supports("wsproxy-addr"),this.enableIsPublic=globalThis.backendaiclient.supports("is-public"),globalThis.backendaiclient.scalingGroup.list_available().then((e=>{this.resourceGroups=e.scaling_groups})).catch((e=>{this.notification.text=m.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)})),globalThis.backendaiclient.domain.list().then((({domains:e})=>{this.domains=e,this.requestUpdate()})).catch((e=>{this.notification.text=m.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)}))}),!0):(this.enableSchedulerOpts=globalThis.backendaiclient.supports("scheduler-opts"),this.enableWSProxyAddr=globalThis.backendaiclient.supports("wsproxy-addr"),this.enableIsPublic=globalThis.backendaiclient.supports("is-public"),globalThis.backendaiclient.scalingGroup.list_available().then((e=>{this.resourceGroups=e.scaling_groups})).catch((e=>{this.notification.text=m.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)})),globalThis.backendaiclient.domain.list().then((({domains:e})=>{this.domains=e,this.requestUpdate()})).catch((e=>{this.notification.text=m.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)}))))}_activeStatusRenderer(e,t,i){g(h`
        <lablup-shields
          app=""
          color=${i.item.is_active?"green":"red"}
          description=${i.item.is_active?"active":"inactive"}
          ui="flat"
        ></lablup-shields>
      `,e)}_isPublicRenderer(e,t,i){g(h`
        <lablup-shields
          app=""
          color=${i.item.is_public?"blue":"darkgreen"}
          description=${i.item.is_public?"public":"private"}
          ui="flat"
        ></lablup-shields>
      `,e)}_indexRenderer(e,t,i){const o=i.index+1;g(h`
        <div>${o}</div>
      `,e)}_launchDialogById(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector(e)).show()}_hideDialogById(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector(e)).hide()}_controlRenderer(e,t,i){g(h`
        <div id="controls" class="layout horizontal flex center">
          <mwc-icon-button
            class="fg green"
            icon="assignment"
            @click=${()=>this._launchDetailDialog(i.item)}
          ></mwc-icon-button>
          <mwc-icon-button
            class="fg blue"
            icon="settings"
            @click=${()=>this._launchModifyDialog(i.item)}
          ></mwc-icon-button>
          <mwc-icon-button
            class="fg red"
            icon="delete"
            @click=${()=>this._launchDeleteDialog(i.item)}
          ></mwc-icon-button>
        </div>
      `,e)}_validateResourceGroupName(){const e=this.resourceGroups.map((e=>e.name));this.resourceGroupNameInput.validityTransform=(t,i)=>{if(i.valid){const i=!e.includes(t);return i||(this.resourceGroupNameInput.validationMessage=b("resourceGroup.ResourceGroupAlreadyExist")),{valid:i,customError:!i}}return i.valueMissing?(this.resourceGroupNameInput.validationMessage=b("resourceGroup.ResourceGroupNameRequired"),{valid:i.valid,valueMissing:!i.valid}):i.patternMismatch?(this.resourceGroupNameInput.validationMessage=b("resourceGroup.EnterValidResourceGroupName"),{valid:i.valid,patternMismatch:!i.valid}):(this.resourceGroupNameInput.validationMessage=b("resourceGroup.EnterValidResourceGroupName"),{valid:i.valid,customError:!i.valid})}}_createResourceGroup(){var e;if(!this.resourceGroupNameInput.checkValidity()||!this._verifyCreateSchedulerOpts())return this._validateResourceGroupName(),void this.resourceGroupNameInput.reportValidity();{this._saveSchedulerOpts();const t=this.resourceGroupNameInput.value,i=this.resourceGroupDescriptionInput.value,o=this.resourceGroupSchedulerSelect.value,r=this.resourceGroupActiveSwitch.selected,s=this.resourceGroupDomainSelect.value,a={description:i,is_active:r,driver:"static",driver_opts:"{}",scheduler:o};if(this.enableSchedulerOpts&&(a.scheduler_opts=JSON.stringify(this.schedulerOpts)),this.enableWSProxyAddr){const e=this.resourceGroupWSProxyAddressInput.value;a.wsproxy_addr=e}this.enableIsPublic&&(a.is_public=null===(e=this.resourceGroupPublicSwitch)||void 0===e?void 0:e.selected),globalThis.backendaiclient.scalingGroup.create(t,a).then((({create_scaling_group:e})=>e.ok?globalThis.backendaiclient.scalingGroup.associate_domain(s,t):Promise.reject(e.msg))).then((({associate_scaling_group_with_domain:e})=>{e.ok?(this.notification.text=b("resourceGroup.ResourceGroupCreated"),this._refreshList(),this.resourceGroupNameInput.value="",this.resourceGroupDescriptionInput.value=""):(this.notification.text=m.relieve(e.title),this.notification.detail=e.msg),this._hideDialogById("#resource-group-dialog"),this.notification.show()})).catch((e=>{this.notification.text=m.relieve(e.title),this.notification.detail=e,this._hideDialogById("#resource-group-dialog"),this.notification.show(!0,e)}))}}_modifyResourceGroup(){var e;if(!1===this._verifyModifySchedulerOpts())return;this._saveSchedulerOpts();const t=this.resourceGroupDescriptionInput.value,i=this.resourceGroupSchedulerSelect.value,o=this.resourceGroupActiveSwitch.selected,r=this.schedulerOpts,s=this.resourceGroupInfo.name,a={};if(t!==this.resourceGroupInfo.description&&(a.description=t),i!==this.resourceGroupInfo.scheduler&&(a.scheduler=i),o!==this.resourceGroupInfo.is_active&&(a.is_active=o),this.enableWSProxyAddr){let e=this.resourceGroupWSProxyAddressInput.value;e.endsWith("/")&&(e=e.slice(0,e.length-1)),e!==this.resourceGroupInfo.wsproxy_addr&&(a.wsproxy_addr=e)}if(this.enableSchedulerOpts&&r!==this.resourceGroupInfo.scheduler_opts&&(a.scheduler_opts=JSON.stringify(r)),this.enableIsPublic){const t=null===(e=this.resourceGroupPublicSwitch)||void 0===e?void 0:e.selected;t!==this.resourceGroupInfo.is_public&&(a.is_public=t)}if(0===Object.keys(a).length)return this.notification.text=b("resourceGroup.NoChangesMade"),void this.notification.show();globalThis.backendaiclient.scalingGroup.update(s,a).then((({modify_scaling_group:e})=>{e.ok?(this.notification.text=b("resourceGroup.ResourceGroupModified"),this._refreshList()):(this.notification.text=m.relieve(e.msg),this.notification.detail=e.msg),this._hideDialogById("#resource-group-dialog"),this.notification.show()}))}_deleteResourceGroup(){const e=this.resourceGroupInfo.name;if(this.deleteResourceGroupInput.value!==e)return this.notification.text=b("resourceGroup.ResourceGroupNameNotMatch"),void this.notification.show();globalThis.backendaiclient.scalingGroup.delete(e).then((({delete_scaling_group:e})=>{e.ok?(this.notification.text=b("resourceGroup.ResourceGroupDeleted"),this._refreshList(),this.deleteResourceGroupInput.value=""):(this.notification.text=m.relieve(e.msg),this.notification.detail=e.msg),this._hideDialogById("#delete-resource-group-dialog"),this.notification.show()}))}_refreshList(){globalThis.backendaiclient.scalingGroup.list_available().then((({scaling_groups:e})=>{this.resourceGroups=e,this.requestUpdate()}))}_initializeCreateSchedulerOpts(){var e,t,i;const o=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#scheduler-options-input-form");this.allowedSessionTypesSelect.items=this.allowedSessionTypes,this.allowedSessionTypesSelect.selectedItemList=["interactive","batch"],this.resourceGroupSchedulerSelect.value="fifo",o.open=!1,(null===(t=this.timeoutInput)||void 0===t?void 0:t.value)&&(this.timeoutInput.value=""),(null===(i=this.numberOfRetriesToSkip)||void 0===i?void 0:i.value)&&(this.numberOfRetriesToSkip.value="")}_initializeModifySchedulerOpts(e="",t){var i;switch(e){case"allowed_session_types":this.allowedSessionTypesSelect.items=this.allowedSessionTypes,this.allowedSessionTypesSelect.selectedItemList=t;break;case"pending_timeout":this.timeoutInput.value=t;break;case"config":this.numberOfRetriesToSkip.value=null!==(i=t.num_retries_to_skip)&&void 0!==i?i:""}}_verifyCreateSchedulerOpts(){const e=[this.timeoutInput,this.numberOfRetriesToSkip].filter((e=>!e.checkValidity()));return e.push(...[this.allowedSessionTypesSelect.selectedItemList].filter((e=>0===e.length))),!(e.length>0)}_verifyModifySchedulerOpts(){const e=[this.timeoutInput,this.numberOfRetriesToSkip].filter((e=>!e.checkValidity()));return e.push(...[this.allowedSessionTypesSelect.selectedItemList].filter((e=>0===e.length))),!(e.length>0)}_saveSchedulerOpts(){this.schedulerOpts={},this.schedulerOpts.allowed_session_types=this.allowedSessionTypesSelect.selectedItemList,""!==this.timeoutInput.value&&(this.schedulerOpts.pending_timeout=this.timeoutInput.value),""!==this.numberOfRetriesToSkip.value&&Object.assign(this.schedulerOpts,{config:{num_retries_to_skip:this.numberOfRetriesToSkip.value}})}_launchCreateDialog(){this.enableSchedulerOpts&&this._initializeCreateSchedulerOpts(),this.resourceGroupInfo={},this._launchDialogById("#resource-group-dialog")}_launchDeleteDialog(e){this.resourceGroupInfo=e,this.deleteResourceGroupInput.value="",this._launchDialogById("#delete-resource-group-dialog")}_launchDetailDialog(e){this.resourceGroupInfo=e,this._launchDialogById("#resource-group-detail-dialog")}_launchModifyDialog(e){if(this.resourceGroupInfo=e,this.enableSchedulerOpts){const e=JSON.parse(this.resourceGroupInfo.scheduler_opts);Object.entries(e).forEach((([e,t])=>{this._initializeModifySchedulerOpts(e,t)}))}this._launchDialogById("#resource-group-dialog")}_validateWsproxyAddress(e){(this.modifyResourceGroupButton||this.createResourceGroupButton).disabled=!e.checkValidity()}render(){var e,t,i,o,r,s,a,l,n,c,d,u,p,v,m,g,y,x,w,_,G,I;return h`
      <h4 class="horizontal flex center center-justified layout">
        <span>${f("resourceGroup.ResourceGroups")}</span>
        <span class="flex"></span>
        <mwc-button
          raised
          icon="add"
          label="${f("button.Add")}"
          @click=${this._launchCreateDialog}
        ></mwc-button>
      </h4>
      <div class="list-wrapper">
        <vaadin-grid
          theme="row-stripes column-borders compact dark"
          aria-label="Job list"
          .items="${this.resourceGroups}"
        >
          <vaadin-grid-column
            frozen
            flex-grow="0"
            header="#"
            width="40px"
            .renderer=${this._indexRenderer}
          ></vaadin-grid-column>
          <vaadin-grid-column
            frozen
            flex-grow="1"
            header="${f("resourceGroup.Name")}"
            path="name"
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${f("resourceGroup.Description")}"
            path="description"
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${f("resourceGroup.ActiveStatus")}"
            resizable
            .renderer=${this._activeStatusRenderer}
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${f("resourceGroup.PublicStatus")}"
            resizable
            .renderer=${this._isPublicRenderer}
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${f("resourceGroup.Driver")}"
            path="driver"
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${f("resourceGroup.Scheduler")}"
            path="scheduler"
            resizable
          ></vaadin-grid-column>
          ${this.enableWSProxyAddr?h`
                <vaadin-grid-column
                  resizable
                  header="${f("resourceGroup.WsproxyAddress")}"
                  path="wsproxy_addr"
                  resizable
                ></vaadin-grid-column>
              `:h``}
          <vaadin-grid-column
            frozen-to-end
            resizable
            width="150px"
            header="${f("general.Control")}"
            .renderer=${this._boundControlRenderer}
          ></vaadin-grid-column>
        </vaadin-grid>
      </div>
      <backend-ai-dialog
        id="resource-group-dialog"
        fixed
        backdrop
        blockscrolling
      >
        <span slot="title">
          ${(null===(e=this.resourceGroupInfo)||void 0===e?void 0:e.name)?f("resourceGroup.ModifyResourceGroup"):f("resourceGroup.CreateResourceGroup")}
        </span>
        <div slot="content" class="login-panel intro centered">
          ${0===Object.keys(this.resourceGroupInfo).length?h`
                <mwc-select
                  required
                  id="resource-group-domain"
                  label="${f("resourceGroup.SelectDomain")}"
                >
                  ${this.domains.map(((e,t)=>h`
                      <mwc-list-item
                        value="${e.name}"
                        ?selected=${0===t}
                      >
                        ${e.name}
                      </mwc-list-item>
                    `))}
                </mwc-select>
                <mwc-textfield
                  type="text"
                  id="resource-group-name"
                  label="${f("resourceGroup.ResourceGroupName")}"
                  maxLength="64"
                  placeholder="${f("maxLength.64chars")}"
                  required
                  autoValidate
                  pattern="^[\\p{L}\\p{N}]+(?:[\\-_.][\\p{L}\\p{N}]+)*$"
                  @input="${()=>this._validateResourceGroupName()}"
                ></mwc-textfield>
              `:h`
                <mwc-textfield
                  type="text"
                  disabled
                  label="${f("resourceGroup.ResourceGroupName")}"
                  value="${null===(t=this.resourceGroupInfo)||void 0===t?void 0:t.name}"
                ></mwc-textfield>
              `}
          <mwc-textarea
            name="description"
            id="resource-group-description"
            label="${f("resourceGroup.Description")}"
            maxLength="512"
            placeholder="${f("maxLength.512chars")}"
            value="${null!==(o=null===(i=this.resourceGroupInfo)||void 0===i?void 0:i.description)&&void 0!==o?o:""}"
          ></mwc-textarea>
          <mwc-select
            id="resource-group-scheduler"
            label="${f("resourceGroup.SelectScheduler")}"
            required
            value="${0===Object.keys(this.resourceGroupInfo).length?"fifo":this.resourceGroupInfo.scheduler}"
          >
            ${this.schedulerTypes.map((e=>h`
                <mwc-list-item value="${e}">${e}</mwc-list-item>
              `))}
          </mwc-select>
          <backend-ai-multi-select
            open-up
            required
            id="allowed-session-types"
            label="${f("resourceGroup.AllowedSessionTypes")}*"
            validation-message="${f("credential.validation.PleaseSelectOptions")}"
            style="width:100%; --select-title-padding-left: 16px;"
          ></backend-ai-multi-select>
          ${this.enableWSProxyAddr?h`
                <mwc-textfield
                  id="resource-group-wsproxy-address"
                  type="url"
                  label="${f("resourceGroup.WsproxyAddress")}"
                  placeholder="http://localhost:10200"
                  value="${null!==(s=null===(r=this.resourceGroupInfo)||void 0===r?void 0:r.wsproxy_addr)&&void 0!==s?s:""}"
                  autoValidate
                  validationMessage="${f("registry.DescURLFormat")}"
                  @input="${e=>{this._addInputValidator(e.target),this._validateWsproxyAddress(e.target)}}"
                ></mwc-textfield>
              `:h``}
          <div class="horizontal layout flex wrap center justified">
            <p style="margin-left: 18px;">${f("resourceGroup.Active")}</p>
            <mwc-switch
              id="resource-group-active"
              style="margin-right:10px;"
              ?selected="${!(Object.keys(this.resourceGroupInfo).length>0)||this.resourceGroupInfo.is_active}"
            ></mwc-switch>
            ${this.enableIsPublic?h`
                  <p style="margin-left: 18px;">
                    ${f("resourceGroup.Public")}
                  </p>
                  <mwc-switch
                    id="resource-group-public"
                    style="margin-right:10px;"
                    ?selected="${!(Object.keys(this.resourceGroupInfo).length>0)||this.resourceGroupInfo.is_public}"
                  ></mwc-switch>
                `:h``}
          </div>
          ${this.enableSchedulerOpts?h`
                <br />
                <lablup-expansion id="scheduler-options-input-form">
                  <span slot="title">
                    ${f("resourceGroup.SchedulerOptions")}
                  </span>
                  <div class="vertical layout flex">
                    <mwc-textfield
                      type="number"
                      value="0"
                      id="pending-timeout"
                      label="pending timeout"
                      placeholder="0"
                      suffix="${f("resourceGroup.TimeoutSeconds")}"
                      validationMessage="${f("settings.InvalidValue")}"
                      autoValidate
                      min="0"
                      value="${null!==(n=null===(l=null===(a=this.resourceGroupInfo)||void 0===a?void 0:a.scheduler_opts)||void 0===l?void 0:l.pending_timeout)&&void 0!==n?n:""}"
                    ></mwc-textfield>
                    <mwc-textfield
                      type="number"
                      value="0"
                      id="num-retries-to-skip"
                      label="# retries to skip pending session"
                      placeholder="0"
                      suffix="${f("resourceGroup.RetriesToSkip")}"
                      validationMessage="${f("settings.InvalidValue")}"
                      autoValidate
                      min="0"
                      value="${null!==(p=null===(u=null===(d=null===(c=this.resourceGroupInfo)||void 0===c?void 0:c.scheduler_opts)||void 0===d?void 0:d.config)||void 0===u?void 0:u.num_retries_to_skip)&&void 0!==p?p:""}"
                    ></mwc-textfield>
                  </div>
                </lablup-expansion>
              `:h``}
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          ${Object.keys(this.resourceGroupInfo).length>0?h`
                <mwc-button
                  id="modify-resource-group"
                  class="full"
                  unelevated
                  icon="save"
                  label="${f("button.Save")}"
                  @click="${this._modifyResourceGroup}"
                ></mwc-button>
              `:h`
                <mwc-button
                  id="create-resource-group"
                  class="full"
                  unelevated
                  icon="add"
                  label="${f("button.Create")}"
                  @click="${this._createResourceGroup}"
                ></mwc-button>
              `}
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog
        id="delete-resource-group-dialog"
        fixed
        backdrop
        blockscrolling
      >
        <span slot="title">${f("dialog.warning.CannotBeUndone")}</span>
        <div slot="content">
          <mwc-textfield
            id="delete-resource-group"
            type="text"
            label="${f("resourceGroup.TypeResourceGroupNameToDelete")}"
            maxLength="64"
            placeholder="${f("maxLength.64chars")}"
          ></mwc-textfield>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            outlined
            label="${f("button.Cancel")}"
            @click="${e=>this._hideDialog(e)}"
          ></mwc-button>
          <mwc-button
            raised
            class="warning fg red"
            label="${f("button.Delete")}"
            @click="${this._deleteResourceGroup}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog
        id="resource-group-detail-dialog"
        fixed
        backdrop
        blockscrolling
      >
        ${Object.keys(this.resourceGroupInfo).length>0?h`
              <span slot="title" class="horizontal center layout">
                <span style="margin-right:15px;">
                  ${b("resourceGroup.ResourceGroupDetail")}
                </span>
              </span>
              <div slot="content" class="intro">
                <div class="horizontal layout" style="margin-bottom:15px;">
                  <div style="width:250px;">
                    <h4>${b("credential.Information")}</h4>
                    <div role="listbox" class="vertical layout">
                      <vaadin-item>
                        <div>
                          <strong>${b("resourceGroup.Name")}</strong>
                        </div>
                        <div class="scheduler-option-value">
                          ${this.resourceGroupInfo.name}
                        </div>
                      </vaadin-item>
                      <vaadin-item>
                        <div>
                          <strong>
                            ${b("resourceGroup.ActiveStatus")}
                          </strong>
                        </div>
                        <lablup-shields
                          app=""
                          color=${this.resourceGroupInfo.is_active?"green":"red"}
                          description=${(null===(v=this.resourceGroupInfo)||void 0===v?void 0:v.is_active)?"active":"inactive"}
                          ui="flat"
                        ></lablup-shields>
                      </vaadin-item>
                      ${this.enableIsPublic?h`
                            <vaadin-item>
                              <div>
                                <strong>
                                  ${b("resourceGroup.PublicStatus")}
                                </strong>
                              </div>
                              <lablup-shields
                                app=""
                                color=${this.resourceGroupInfo.is_public?"blue":"darkgreen"}
                                description=${(null===(m=this.resourceGroupInfo)||void 0===m?void 0:m.is_public)?"public":"private"}
                                ui="flat"
                              ></lablup-shields>
                            </vaadin-item>
                          `:h``}
                      <vaadin-item>
                        <div>
                          <strong>${b("resourceGroup.Driver")}</strong>
                        </div>
                        <div class="scheduler-option-value">
                          ${null===(g=this.resourceGroupInfo)||void 0===g?void 0:g.driver}
                        </div>
                      </vaadin-item>
                      <vaadin-item>
                        <div>
                          <strong>${b("resourceGroup.Scheduler")}</strong>
                        </div>
                        <div class="scheduler-option-value">
                          ${null===(y=this.resourceGroupInfo)||void 0===y?void 0:y.scheduler}
                        </div>
                      </vaadin-item>
                      ${this.enableWSProxyAddr?h`
                            <vaadin-item>
                              <div>
                                <strong>
                                  ${b("resourceGroup.WsproxyAddress")}
                                </strong>
                              </div>
                              <div class="scheduler-option-value">
                                ${null!==(w=null===(x=this.resourceGroupInfo)||void 0===x?void 0:x.wsproxy_addr)&&void 0!==w?w:"none"}
                              </div>
                            </vaadin-item>
                          `:h``}
                    </div>
                  </div>
                  <div class="center vertial layout" style="width:250px;">
                    <div>
                      <h4 class="horizontal center layout">
                        ${f("resourceGroup.SchedulerOptions")}
                      </h4>
                      <div role="listbox">
                        ${this.enableSchedulerOpts?h`
                              ${Object.entries(JSON.parse(null===(_=this.resourceGroupInfo)||void 0===_?void 0:_.scheduler_opts)).map((([e,t])=>"allowed_session_types"===e?h`
                                    <vaadin-item>
                                      <div>
                                        <strong>allowed session types</strong>
                                      </div>
                                      <div class="scheduler-option-value">
                                        ${t.join(", ")}
                                      </div>
                                    </vaadin-item>
                                  `:"pending_timeout"===e?h`
                                    <vaadin-item>
                                      <div>
                                        <strong>pending timeout</strong>
                                      </div>
                                      <div class="scheduler-option-value">
                                        ${t+" "+b("resourceGroup.TimeoutSeconds")}
                                      </div>
                                    </vaadin-item>
                                  `:"config"===e&&t.num_retries_to_skip?h`
                                      <vaadin-item>
                                        <div>
                                          <strong>
                                            # retries to skip pending session
                                          </strong>
                                        </div>
                                        <div class="scheduler-option-value">
                                          ${t.num_retries_to_skip+" "+b("resourceGroup.RetriesToSkip")}
                                        </div>
                                      </vaadin-item>
                                    `:""))}
                            `:h``}
                      </div>
                    </div>
                    <div>
                      <h4 class="horizontal center layout">
                        ${f("resourceGroup.DriverOptions")}
                      </h4>
                      <div role="listbox"></div>
                    </div>
                  </div>
                </div>
                <div>
                  <h4>${f("resourceGroup.Description")}</h4>
                  <mwc-textarea
                    readonly
                    value="${null!==(I=null===(G=this.resourceGroupInfo)||void 0===G?void 0:G.description)&&void 0!==I?I:""}"
                  ></mwc-textarea>
                </div>
              </div>
            `:""}
      </backend-ai-dialog>
    `}};e([i({type:Object})],w.prototype,"_boundControlRenderer",void 0),e([i({type:Array})],w.prototype,"domains",void 0),e([i({type:Object})],w.prototype,"resourceGroupInfo",void 0),e([i({type:Array})],w.prototype,"resourceGroups",void 0),e([i({type:Array})],w.prototype,"schedulerTypes",void 0),e([i({type:Object})],w.prototype,"schedulerOpts",void 0),e([o()],w.prototype,"allowedSessionTypes",void 0),e([i({type:Boolean})],w.prototype,"enableSchedulerOpts",void 0),e([i({type:Boolean})],w.prototype,"enableWSProxyAddr",void 0),e([i({type:Boolean})],w.prototype,"enableIsPublic",void 0),e([i({type:Number})],w.prototype,"functionCount",void 0),e([t("#resource-group-name")],w.prototype,"resourceGroupNameInput",void 0),e([t("#resource-group-description")],w.prototype,"resourceGroupDescriptionInput",void 0),e([t("#resource-group-domain")],w.prototype,"resourceGroupDomainSelect",void 0),e([t("#resource-group-scheduler")],w.prototype,"resourceGroupSchedulerSelect",void 0),e([t("#resource-group-active")],w.prototype,"resourceGroupActiveSwitch",void 0),e([t("#resource-group-public")],w.prototype,"resourceGroupPublicSwitch",void 0),e([t("#resource-group-wsproxy-address")],w.prototype,"resourceGroupWSProxyAddressInput",void 0),e([t("#allowed-session-types")],w.prototype,"allowedSessionTypesSelect",void 0),e([t("#num-retries-to-skip")],w.prototype,"numberOfRetriesToSkip",void 0),e([t("#pending-timeout")],w.prototype,"timeoutInput",void 0),e([t("#delete-resource-group")],w.prototype,"deleteResourceGroupInput",void 0),e([t("#modify-resource-group")],w.prototype,"modifyResourceGroupButton",void 0),e([t("#create-resource-group")],w.prototype,"createResourceGroupButton",void 0),w=e([r("backend-ai-resource-group-list")],w);
