import{_ as e,n as i,K as t,e as o,t as r,B as s,b as a,I as l,a as n,i as u,d as c,Q as d,k as p,g as h,f as v}from"./backend-ai-webui-DHPXkWFV.js";import"./backend-ai-multi-select-CBExT1w5.js";import"./mwc-switch-4PAREU42.js";import"./vaadin-item-Z-SbxbmW.js";import"./mwc-check-list-item-BOuWYOQ7.js";import"./vaadin-item-mixin-DuqXhN3A.js";let m=class extends s{constructor(){super(),this._boundControlRenderer=this._controlRenderer.bind(this),this.allowedSessionTypes=["interactive","batch","inference"],this.enableSchedulerOpts=!1,this.enableWSProxyAddr=!1,this.enableIsPublic=!1,this.functionCount=0,this.active=!1,this.schedulerTypes=["fifo","lifo","drf"],this.resourceGroups=[],this.resourceGroupInfo={},this.domains=[]}static get styles(){return[a,l,n,u`
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
      `]}firstUpdated(){this.notification=globalThis.lablupNotification}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.enableSchedulerOpts=globalThis.backendaiclient.supports("scheduler-opts"),this.enableWSProxyAddr=globalThis.backendaiclient.supports("wsproxy-addr"),this.enableIsPublic=globalThis.backendaiclient.supports("is-public"),globalThis.backendaiclient.scalingGroup.list_available().then((e=>{this.resourceGroups=e.scaling_groups})).catch((e=>{this.notification.text=c.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)})),globalThis.backendaiclient.domain.list().then((({domains:e})=>{this.domains=e,this.requestUpdate()})).catch((e=>{this.notification.text=c.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)}))}),!0):(this.enableSchedulerOpts=globalThis.backendaiclient.supports("scheduler-opts"),this.enableWSProxyAddr=globalThis.backendaiclient.supports("wsproxy-addr"),this.enableIsPublic=globalThis.backendaiclient.supports("is-public"),globalThis.backendaiclient.scalingGroup.list_available().then((e=>{this.resourceGroups=e.scaling_groups})).catch((e=>{this.notification.text=c.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)})),globalThis.backendaiclient.domain.list().then((({domains:e})=>{this.domains=e,this.requestUpdate()})).catch((e=>{this.notification.text=c.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)}))))}_activeStatusRenderer(e,i,t){d(p`
        <lablup-shields
          app=""
          color=${t.item.is_active?"green":"red"}
          description=${t.item.is_active?"active":"inactive"}
          ui="flat"
        ></lablup-shields>
      `,e)}_isPublicRenderer(e,i,t){d(p`
        <lablup-shields
          app=""
          color=${t.item.is_public?"blue":"darkgreen"}
          description=${t.item.is_public?"public":"private"}
          ui="flat"
        ></lablup-shields>
      `,e)}_indexRenderer(e,i,t){const o=t.index+1;d(p`
        <div>${o}</div>
      `,e)}_launchDialogById(e){var i;(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector(e)).show()}_hideDialogById(e){var i;(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector(e)).hide()}_controlRenderer(e,i,t){d(p`
        <div id="controls" class="layout horizontal flex center">
          <mwc-icon-button
            class="fg green"
            icon="assignment"
            @click=${()=>this._launchDetailDialog(t.item)}
          ></mwc-icon-button>
          <mwc-icon-button
            class="fg blue"
            icon="settings"
            @click=${()=>this._launchModifyDialog(t.item)}
          ></mwc-icon-button>
          <mwc-icon-button
            class="fg red"
            icon="delete"
            @click=${()=>this._launchDeleteDialog(t.item)}
          ></mwc-icon-button>
        </div>
      `,e)}_validateResourceGroupName(){const e=this.resourceGroups.map((e=>e.name));this.resourceGroupNameInput.validityTransform=(i,t)=>{if(t.valid){const t=!e.includes(i);return t||(this.resourceGroupNameInput.validationMessage=h("resourceGroup.ResourceGroupAlreadyExist")),{valid:t,customError:!t}}return t.valueMissing?(this.resourceGroupNameInput.validationMessage=h("resourceGroup.ResourceGroupNameRequired"),{valid:t.valid,valueMissing:!t.valid}):(this.resourceGroupNameInput.validationMessage=h("resourceGroup.EnterValidResourceGroupName"),{valid:t.valid,customError:!t.valid})}}_createResourceGroup(){var e;if(this.resourceGroupNameInput.checkValidity()&&this._verifyCreateSchedulerOpts()){this._saveSchedulerOpts();const i=this.resourceGroupNameInput.value,t=this.resourceGroupDescriptionInput.value,o=this.resourceGroupSchedulerSelect.value,r=this.resourceGroupActiveSwitch.selected,s=this.resourceGroupDomainSelect.value,a={description:t,is_active:r,driver:"static",driver_opts:"{}",scheduler:o};if(this.enableSchedulerOpts&&(a.scheduler_opts=JSON.stringify(this.schedulerOpts)),this.enableWSProxyAddr){const e=this.resourceGroupWSProxyAddressInput.value;a.wsproxy_addr=e}this.enableIsPublic&&(a.is_public=null===(e=this.resourceGroupPublicSwitch)||void 0===e?void 0:e.selected),globalThis.backendaiclient.scalingGroup.create(i,a).then((({create_scaling_group:e})=>e.ok?globalThis.backendaiclient.scalingGroup.associate_domain(s,i):Promise.reject(e.msg))).then((({associate_scaling_group_with_domain:e})=>{e.ok?(this.notification.text=h("resourceGroup.ResourceGroupCreated"),this._refreshList(),this.resourceGroupNameInput.value="",this.resourceGroupDescriptionInput.value=""):(this.notification.text=c.relieve(e.title),this.notification.detail=e.msg),this._hideDialogById("#resource-group-dialog"),this.notification.show()})).catch((e=>{this.notification.text=c.relieve(e.title),this.notification.detail=e,this._hideDialogById("#resource-group-dialog"),this.notification.show(!0,e)}))}}_modifyResourceGroup(){var e;if(!1===this._verifyModifySchedulerOpts())return;this._saveSchedulerOpts();const i=this.resourceGroupDescriptionInput.value,t=this.resourceGroupSchedulerSelect.value,o=this.resourceGroupActiveSwitch.selected,r=this.schedulerOpts,s=this.resourceGroupInfo.name,a={};if(i!==this.resourceGroupInfo.description&&(a.description=i),t!==this.resourceGroupInfo.scheduler&&(a.scheduler=t),o!==this.resourceGroupInfo.is_active&&(a.is_active=o),this.enableWSProxyAddr){let e=this.resourceGroupWSProxyAddressInput.value;e.endsWith("/")&&(e=e.slice(0,e.length-1)),e!==this.resourceGroupInfo.wsproxy_addr&&(a.wsproxy_addr=e)}if(this.enableSchedulerOpts&&r!==this.resourceGroupInfo.scheduler_opts&&(a.scheduler_opts=JSON.stringify(r)),this.enableIsPublic){const i=null===(e=this.resourceGroupPublicSwitch)||void 0===e?void 0:e.selected;i!==this.resourceGroupInfo.is_public&&(a.is_public=i)}if(0===Object.keys(a).length)return this.notification.text=h("resourceGroup.NochangesMade"),void this.notification.show();globalThis.backendaiclient.scalingGroup.update(s,a).then((({modify_scaling_group:e})=>{e.ok?(this.notification.text=h("resourceGroup.ResourceGroupModified"),this._refreshList()):(this.notification.text=c.relieve(e.msg),this.notification.detail=e.msg),this._hideDialogById("#resource-group-dialog"),this.notification.show()}))}_deleteResourceGroup(){const e=this.resourceGroupInfo.name;if(this.deleteResourceGroupInput.value!==e)return this.notification.text=h("resourceGroup.ResourceGroupNameNotMatch"),void this.notification.show();globalThis.backendaiclient.scalingGroup.delete(e).then((({delete_scaling_group:e})=>{e.ok?(this.notification.text=h("resourceGroup.ResourceGroupDeleted"),this._refreshList(),this.deleteResourceGroupInput.value=""):(this.notification.text=c.relieve(e.msg),this.notification.detail=e.msg),this._hideDialogById("#delete-resource-group-dialog"),this.notification.show()}))}_refreshList(){globalThis.backendaiclient.scalingGroup.list_available().then((({scaling_groups:e})=>{this.resourceGroups=e,this.requestUpdate()}))}_initializeCreateSchedulerOpts(){var e,i,t;const o=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#scheduler-options-input-form");this.allowedSessionTypesSelect.items=this.allowedSessionTypes,this.allowedSessionTypesSelect.selectedItemList=["interactive","batch"],this.resourceGroupSchedulerSelect.value="fifo",o.open=!1,(null===(i=this.timeoutInput)||void 0===i?void 0:i.value)&&(this.timeoutInput.value=""),(null===(t=this.numberOfRetriesToSkip)||void 0===t?void 0:t.value)&&(this.numberOfRetriesToSkip.value="")}_initializeModifySchedulerOpts(e="",i){var t;switch(e){case"allowed_session_types":this.allowedSessionTypesSelect.items=this.allowedSessionTypes,this.allowedSessionTypesSelect.selectedItemList=i;break;case"pending_timeout":this.timeoutInput.value=i;break;case"config":this.numberOfRetriesToSkip.value=null!==(t=i.num_retries_to_skip)&&void 0!==t?t:""}}_verifyCreateSchedulerOpts(){const e=[this.timeoutInput,this.numberOfRetriesToSkip].filter((e=>!e.checkValidity()));return e.push(...[this.allowedSessionTypesSelect.selectedItemList].filter((e=>0===e.length))),!(e.length>0)}_verifyModifySchedulerOpts(){const e=[this.timeoutInput,this.numberOfRetriesToSkip].filter((e=>!e.checkValidity()));return e.push(...[this.allowedSessionTypesSelect.selectedItemList].filter((e=>0===e.length))),!(e.length>0)}_saveSchedulerOpts(){this.schedulerOpts={},this.schedulerOpts.allowed_session_types=this.allowedSessionTypesSelect.selectedItemList,""!==this.timeoutInput.value&&(this.schedulerOpts.pending_timeout=this.timeoutInput.value),""!==this.numberOfRetriesToSkip.value&&Object.assign(this.schedulerOpts,{config:{num_retries_to_skip:this.numberOfRetriesToSkip.value}})}_launchCreateDialog(){this.enableSchedulerOpts&&this._initializeCreateSchedulerOpts(),this.resourceGroupInfo={},this._launchDialogById("#resource-group-dialog")}_launchDeleteDialog(e){this.resourceGroupInfo=e,this.deleteResourceGroupInput.value="",this._launchDialogById("#delete-resource-group-dialog")}_launchDetailDialog(e){this.resourceGroupInfo=e,this._launchDialogById("#resource-group-detail-dialog")}_launchModifyDialog(e){if(this.resourceGroupInfo=e,this.enableSchedulerOpts){const e=JSON.parse(this.resourceGroupInfo.scheduler_opts);Object.entries(e).forEach((([e,i])=>{this._initializeModifySchedulerOpts(e,i)}))}this._launchDialogById("#resource-group-dialog")}_validateWsproxyAddress(e){(this.modifyResourceGroupButton||this.createResourceGroupButton).disabled=!e.checkValidity()}render(){var e,i,t,o,r,s,a,l,n,u,c,d,m,g,b,f,y,G,x,w,_,S;return p`
      <h4 class="horizontal flex center center-justified layout">
        <span>${v("resourceGroup.ResourceGroups")}</span>
        <span class="flex"></span>
        <mwc-button
          raised
          icon="add"
          label="${v("button.Add")}"
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
            header="${v("resourceGroup.Name")}"
            path="name"
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${v("resourceGroup.Description")}"
            path="description"
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${v("resourceGroup.ActiveStatus")}"
            resizable
            .renderer=${this._activeStatusRenderer}
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${v("resourceGroup.PublicStatus")}"
            resizable
            .renderer=${this._isPublicRenderer}
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${v("resourceGroup.Driver")}"
            path="driver"
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${v("resourceGroup.Scheduler")}"
            path="scheduler"
            resizable
          ></vaadin-grid-column>
          ${this.enableWSProxyAddr?p`
                <vaadin-grid-column
                  resizable
                  header="${v("resourceGroup.WsproxyAddress")}"
                  path="wsproxy_addr"
                  resizable
                ></vaadin-grid-column>
              `:p``}
          <vaadin-grid-column
            frozen-to-end
            resizable
            width="150px"
            header="${v("general.Control")}"
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
          ${(null===(e=this.resourceGroupInfo)||void 0===e?void 0:e.name)?v("resourceGroup.ModifyResourceGroup"):v("resourceGroup.CreateResourceGroup")}
        </span>
        <div slot="content" class="login-panel intro centered">
          ${0===Object.keys(this.resourceGroupInfo).length?p`
                <mwc-select
                  required
                  id="resource-group-domain"
                  label="${v("resourceGroup.SelectDomain")}"
                >
                  ${this.domains.map(((e,i)=>p`
                      <mwc-list-item
                        value="${e.name}"
                        ?selected=${0===i}
                      >
                        ${e.name}
                      </mwc-list-item>
                    `))}
                </mwc-select>
                <mwc-textfield
                  type="text"
                  id="resource-group-name"
                  label="${v("resourceGroup.ResourceGroupName")}"
                  maxLength="64"
                  placeholder="${v("maxLength.64chars")}"
                  validationMessage="${v("data.explorer.ValueRequired")}"
                  required
                  autoValidate
                  @change="${()=>this._validateResourceGroupName()}"
                ></mwc-textfield>
              `:p`
                <mwc-textfield
                  type="text"
                  disabled
                  label="${v("resourceGroup.ResourceGroupName")}"
                  value="${null===(i=this.resourceGroupInfo)||void 0===i?void 0:i.name}"
                ></mwc-textfield>
              `}
          <mwc-textarea
            name="description"
            id="resource-group-description"
            label="${v("resourceGroup.Description")}"
            maxLength="512"
            placeholder="${v("maxLength.512chars")}"
            value="${null!==(o=null===(t=this.resourceGroupInfo)||void 0===t?void 0:t.description)&&void 0!==o?o:""}"
          ></mwc-textarea>
          <mwc-select
            id="resource-group-scheduler"
            label="${v("resourceGroup.SelectScheduler")}"
            required
            value="${0===Object.keys(this.resourceGroupInfo).length?"fifo":this.resourceGroupInfo.scheduler}"
          >
            ${this.schedulerTypes.map((e=>p`
                <mwc-list-item value="${e}">${e}</mwc-list-item>
              `))}
          </mwc-select>
          <backend-ai-multi-select
            open-up
            required
            id="allowed-session-types"
            label="${v("resourceGroup.AllowedSessionTypes")}*"
            validation-message="${v("credential.validation.PleaseSelectOptions")}"
            style="width:100%; --select-title-padding-left: 16px;"
          ></backend-ai-multi-select>
          ${this.enableWSProxyAddr?p`
                <mwc-textfield
                  id="resource-group-wsproxy-address"
                  type="url"
                  label="${v("resourceGroup.WsproxyAddress")}"
                  placeholder="http://localhost:10200"
                  value="${null!==(s=null===(r=this.resourceGroupInfo)||void 0===r?void 0:r.wsproxy_addr)&&void 0!==s?s:""}"
                  autoValidate
                  validationMessage="${v("registry.DescURLFormat")}"
                  @input="${e=>{this._addInputValidator(e.target),this._validateWsproxyAddress(e.target)}}"
                ></mwc-textfield>
              `:p``}
          <div class="horizontal layout flex wrap center justified">
            <p style="margin-left: 18px;">${v("resourceGroup.Active")}</p>
            <mwc-switch
              id="resource-group-active"
              style="margin-right:10px;"
              ?selected="${!(Object.keys(this.resourceGroupInfo).length>0)||this.resourceGroupInfo.is_active}"
            ></mwc-switch>
            ${this.enableIsPublic?p`
                  <p style="margin-left: 18px;">
                    ${v("resourceGroup.Public")}
                  </p>
                  <mwc-switch
                    id="resource-group-public"
                    style="margin-right:10px;"
                    ?selected="${!(Object.keys(this.resourceGroupInfo).length>0)||this.resourceGroupInfo.is_public}"
                  ></mwc-switch>
                `:p``}
          </div>
          ${this.enableSchedulerOpts?p`
                <br />
                <lablup-expansion id="scheduler-options-input-form">
                  <span slot="title">
                    ${v("resourceGroup.SchedulerOptions")}
                  </span>
                  <div class="vertical layout flex">
                    <mwc-textfield
                      type="number"
                      value="0"
                      id="pending-timeout"
                      label="pending timeout"
                      placeholder="0"
                      suffix="${v("resourceGroup.TimeoutSeconds")}"
                      validationMessage="${v("settings.InvalidValue")}"
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
                      suffix="${v("resourceGroup.RetriesToSkip")}"
                      validationMessage="${v("settings.InvalidValue")}"
                      autoValidate
                      min="0"
                      value="${null!==(m=null===(d=null===(c=null===(u=this.resourceGroupInfo)||void 0===u?void 0:u.scheduler_opts)||void 0===c?void 0:c.config)||void 0===d?void 0:d.num_retries_to_skip)&&void 0!==m?m:""}"
                    ></mwc-textfield>
                  </div>
                </lablup-expansion>
              `:p``}
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          ${Object.keys(this.resourceGroupInfo).length>0?p`
                <mwc-button
                  id="modify-resource-group"
                  class="full"
                  unelevated
                  icon="save"
                  label="${v("button.Save")}"
                  @click="${this._modifyResourceGroup}"
                ></mwc-button>
              `:p`
                <mwc-button
                  id="create-resource-group"
                  class="full"
                  unelevated
                  icon="add"
                  label="${v("button.Create")}"
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
        <span slot="title">${v("dialog.warning.CannotBeUndone")}</span>
        <div slot="content">
          <mwc-textfield
            id="delete-resource-group"
            type="text"
            label="${v("resourceGroup.TypeResourceGroupNameToDelete")}"
            maxLength="64"
            placeholder="${v("maxLength.64chars")}"
          ></mwc-textfield>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            outlined
            label="${v("button.Cancel")}"
            @click="${e=>this._hideDialog(e)}"
          ></mwc-button>
          <mwc-button
            raised
            class="warning fg red"
            label="${v("button.Delete")}"
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
        ${Object.keys(this.resourceGroupInfo).length>0?p`
              <span slot="title" class="horizontal center layout">
                <span style="margin-right:15px;">
                  ${h("resourceGroup.ResourceGroupDetail")}
                </span>
              </span>
              <div slot="content" class="intro">
                <div class="horizontal layout" style="margin-bottom:15px;">
                  <div style="width:250px;">
                    <h4>${h("credential.Information")}</h4>
                    <div role="listbox" class="vertical layout">
                      <vaadin-item>
                        <div>
                          <strong>${h("resourceGroup.Name")}</strong>
                        </div>
                        <div class="scheduler-option-value">
                          ${this.resourceGroupInfo.name}
                        </div>
                      </vaadin-item>
                      <vaadin-item>
                        <div>
                          <strong>
                            ${h("resourceGroup.ActiveStatus")}
                          </strong>
                        </div>
                        <lablup-shields
                          app=""
                          color=${this.resourceGroupInfo.is_active?"green":"red"}
                          description=${(null===(g=this.resourceGroupInfo)||void 0===g?void 0:g.is_active)?"active":"inactive"}
                          ui="flat"
                        ></lablup-shields>
                      </vaadin-item>
                      ${this.enableIsPublic?p`
                            <vaadin-item>
                              <div>
                                <strong>
                                  ${h("resourceGroup.PublicStatus")}
                                </strong>
                              </div>
                              <lablup-shields
                                app=""
                                color=${this.resourceGroupInfo.is_public?"blue":"darkgreen"}
                                description=${(null===(b=this.resourceGroupInfo)||void 0===b?void 0:b.is_public)?"public":"private"}
                                ui="flat"
                              ></lablup-shields>
                            </vaadin-item>
                          `:p``}
                      <vaadin-item>
                        <div>
                          <strong>${h("resourceGroup.Driver")}</strong>
                        </div>
                        <div class="scheduler-option-value">
                          ${null===(f=this.resourceGroupInfo)||void 0===f?void 0:f.driver}
                        </div>
                      </vaadin-item>
                      <vaadin-item>
                        <div>
                          <strong>${h("resourceGroup.Scheduler")}</strong>
                        </div>
                        <div class="scheduler-option-value">
                          ${null===(y=this.resourceGroupInfo)||void 0===y?void 0:y.scheduler}
                        </div>
                      </vaadin-item>
                      ${this.enableWSProxyAddr?p`
                            <vaadin-item>
                              <div>
                                <strong>
                                  ${h("resourceGroup.WsproxyAddress")}
                                </strong>
                              </div>
                              <div class="scheduler-option-value">
                                ${null!==(x=null===(G=this.resourceGroupInfo)||void 0===G?void 0:G.wsproxy_addr)&&void 0!==x?x:"none"}
                              </div>
                            </vaadin-item>
                          `:p``}
                    </div>
                  </div>
                  <div class="center vertial layout" style="width:250px;">
                    <div>
                      <h4 class="horizontal center layout">
                        ${v("resourceGroup.SchedulerOptions")}
                      </h4>
                      <div role="listbox">
                        ${this.enableSchedulerOpts?p`
                              ${Object.entries(JSON.parse(null===(w=this.resourceGroupInfo)||void 0===w?void 0:w.scheduler_opts)).map((([e,i])=>"allowed_session_types"===e?p`
                                    <vaadin-item>
                                      <div>
                                        <strong>allowed session types</strong>
                                      </div>
                                      <div class="scheduler-option-value">
                                        ${i.join(", ")}
                                      </div>
                                    </vaadin-item>
                                  `:"pending_timeout"===e?p`
                                    <vaadin-item>
                                      <div>
                                        <strong>pending timeout</strong>
                                      </div>
                                      <div class="scheduler-option-value">
                                        ${i+" "+h("resourceGroup.TimeoutSeconds")}
                                      </div>
                                    </vaadin-item>
                                  `:"config"===e&&i.num_retries_to_skip?p`
                                      <vaadin-item>
                                        <div>
                                          <strong>
                                            # retries to skip pending session
                                          </strong>
                                        </div>
                                        <div class="scheduler-option-value">
                                          ${i.num_retries_to_skip+" "+h("resourceGroup.RetriesToSkip")}
                                        </div>
                                      </vaadin-item>
                                    `:""))}
                            `:p``}
                      </div>
                    </div>
                    <div>
                      <h4 class="horizontal center layout">
                        ${v("resourceGroup.DriverOptions")}
                      </h4>
                      <div role="listbox"></div>
                    </div>
                  </div>
                </div>
                <div>
                  <h4>${v("resourceGroup.Description")}</h4>
                  <mwc-textarea
                    readonly
                    value="${null!==(S=null===(_=this.resourceGroupInfo)||void 0===_?void 0:_.description)&&void 0!==S?S:""}"
                  ></mwc-textarea>
                </div>
              </div>
            `:""}
      </backend-ai-dialog>
    `}};e([i({type:Object})],m.prototype,"_boundControlRenderer",void 0),e([i({type:Array})],m.prototype,"domains",void 0),e([i({type:Object})],m.prototype,"resourceGroupInfo",void 0),e([i({type:Array})],m.prototype,"resourceGroups",void 0),e([i({type:Array})],m.prototype,"schedulerTypes",void 0),e([i({type:Object})],m.prototype,"schedulerOpts",void 0),e([t()],m.prototype,"allowedSessionTypes",void 0),e([i({type:Boolean})],m.prototype,"enableSchedulerOpts",void 0),e([i({type:Boolean})],m.prototype,"enableWSProxyAddr",void 0),e([i({type:Boolean})],m.prototype,"enableIsPublic",void 0),e([i({type:Number})],m.prototype,"functionCount",void 0),e([o("#resource-group-name")],m.prototype,"resourceGroupNameInput",void 0),e([o("#resource-group-description")],m.prototype,"resourceGroupDescriptionInput",void 0),e([o("#resource-group-domain")],m.prototype,"resourceGroupDomainSelect",void 0),e([o("#resource-group-scheduler")],m.prototype,"resourceGroupSchedulerSelect",void 0),e([o("#resource-group-active")],m.prototype,"resourceGroupActiveSwitch",void 0),e([o("#resource-group-public")],m.prototype,"resourceGroupPublicSwitch",void 0),e([o("#resource-group-wsproxy-address")],m.prototype,"resourceGroupWSProxyAddressInput",void 0),e([o("#allowed-session-types")],m.prototype,"allowedSessionTypesSelect",void 0),e([o("#num-retries-to-skip")],m.prototype,"numberOfRetriesToSkip",void 0),e([o("#pending-timeout")],m.prototype,"timeoutInput",void 0),e([o("#delete-resource-group")],m.prototype,"deleteResourceGroupInput",void 0),e([o("#modify-resource-group")],m.prototype,"modifyResourceGroupButton",void 0),e([o("#create-resource-group")],m.prototype,"createResourceGroupButton",void 0),m=e([r("backend-ai-resource-group-list")],m);
