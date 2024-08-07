import{_ as e,n as i,e as t,t as o,B as r,b as s,I as a,a as l,i as n,d as u,p as c,x as d,g as p,f as h}from"./backend-ai-webui-Cvl-SpQz.js";import"./backend-ai-multi-select-O9VeKYmT.js";import"./mwc-switch-Dl-Uk4v9.js";import"./vaadin-grid-BXsNAAkf.js";import"./vaadin-item-C14ahZ1t.js";import{r as v}from"./state-DHMhK3Qz.js";import"./mwc-check-list-item-BwnFSR0R.js";import"./dir-utils-BVJL0QLI.js";import"./vaadin-item-mixin-CaRaow76.js";import"./active-mixin-lW8Qt-OC.js";let m=class extends r{constructor(){super(),this._boundControlRenderer=this._controlRenderer.bind(this),this.allowedSessionTypes=["interactive","batch","inference"],this.enableSchedulerOpts=!1,this.enableWSProxyAddr=!1,this.enableIsPublic=!1,this.functionCount=0,this.active=!1,this.schedulerTypes=["fifo","lifo","drf"],this.resourceGroups=[],this.resourceGroupInfo={},this.domains=[]}static get styles(){return[s,a,l,n`
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
      `]}firstUpdated(){this.notification=globalThis.lablupNotification}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.enableSchedulerOpts=globalThis.backendaiclient.supports("scheduler-opts"),this.enableWSProxyAddr=globalThis.backendaiclient.supports("wsproxy-addr"),this.enableIsPublic=globalThis.backendaiclient.supports("is-public"),globalThis.backendaiclient.scalingGroup.list_available().then((e=>{this.resourceGroups=e.scaling_groups})).catch((e=>{this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)})),globalThis.backendaiclient.domain.list().then((({domains:e})=>{this.domains=e,this.requestUpdate()})).catch((e=>{this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)}))}),!0):(this.enableSchedulerOpts=globalThis.backendaiclient.supports("scheduler-opts"),this.enableWSProxyAddr=globalThis.backendaiclient.supports("wsproxy-addr"),this.enableIsPublic=globalThis.backendaiclient.supports("is-public"),globalThis.backendaiclient.scalingGroup.list_available().then((e=>{this.resourceGroups=e.scaling_groups})).catch((e=>{this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)})),globalThis.backendaiclient.domain.list().then((({domains:e})=>{this.domains=e,this.requestUpdate()})).catch((e=>{this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)}))))}_activeStatusRenderer(e,i,t){c(d`
        <lablup-shields
          app=""
          color=${t.item.is_active?"green":"red"}
          description=${t.item.is_active?"active":"inactive"}
          ui="flat"
        ></lablup-shields>
      `,e)}_isPublicRenderer(e,i,t){c(d`
        <lablup-shields
          app=""
          color=${t.item.is_public?"blue":"darkgreen"}
          description=${t.item.is_public?"public":"private"}
          ui="flat"
        ></lablup-shields>
      `,e)}_indexRenderer(e,i,t){const o=t.index+1;c(d`
        <div>${o}</div>
      `,e)}_launchDialogById(e){var i;(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector(e)).show()}_hideDialogById(e){var i;(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector(e)).hide()}_controlRenderer(e,i,t){c(d`
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
      `,e)}_validateResourceGroupName(){const e=this.resourceGroups.map((e=>e.name));this.resourceGroupNameInput.validityTransform=(i,t)=>{if(t.valid){const t=!e.includes(i);return t||(this.resourceGroupNameInput.validationMessage=p("resourceGroup.ResourceGroupAlreadyExist")),{valid:t,customError:!t}}return t.valueMissing?(this.resourceGroupNameInput.validationMessage=p("resourceGroup.ResourceGroupNameRequired"),{valid:t.valid,valueMissing:!t.valid}):(this.resourceGroupNameInput.validationMessage=p("resourceGroup.EnterValidResourceGroupName"),{valid:t.valid,customError:!t.valid})}}_createResourceGroup(){var e;if(this.resourceGroupNameInput.checkValidity()&&this._verifyCreateSchedulerOpts()){this._saveSchedulerOpts();const i=this.resourceGroupNameInput.value,t=this.resourceGroupDescriptionInput.value,o=this.resourceGroupSchedulerSelect.value,r=this.resourceGroupActiveSwitch.selected,s=this.resourceGroupDomainSelect.value,a={description:t,is_active:r,driver:"static",driver_opts:"{}",scheduler:o};if(this.enableSchedulerOpts&&(a.scheduler_opts=JSON.stringify(this.schedulerOpts)),this.enableWSProxyAddr){const e=this.resourceGroupWSProxyaddressInput.value;a.wsproxy_addr=e}this.enableIsPublic&&(a.is_public=null===(e=this.resourceGroupPublicSwitch)||void 0===e?void 0:e.selected),globalThis.backendaiclient.scalingGroup.create(i,a).then((({create_scaling_group:e})=>e.ok?globalThis.backendaiclient.scalingGroup.associate_domain(s,i):Promise.reject(e.msg))).then((({associate_scaling_group_with_domain:e})=>{e.ok?(this.notification.text=p("resourceGroup.ResourceGroupCreated"),this._refreshList(),this.resourceGroupNameInput.value="",this.resourceGroupDescriptionInput.value=""):(this.notification.text=u.relieve(e.title),this.notification.detail=e.msg),this._hideDialogById("#resource-group-dialog"),this.notification.show()})).catch((e=>{this.notification.text=u.relieve(e.title),this.notification.detail=e,this._hideDialogById("#resource-group-dialog"),this.notification.show(!0,e)}))}}_modifyResourceGroup(){var e;if(!1===this._verifyModifySchedulerOpts())return;this._saveSchedulerOpts();const i=this.resourceGroupDescriptionInput.value,t=this.resourceGroupSchedulerSelect.value,o=this.resourceGroupActiveSwitch.selected,r=this.schedulerOpts,s=this.resourceGroupInfo.name,a={};if(i!==this.resourceGroupInfo.description&&(a.description=i),t!==this.resourceGroupInfo.scheduler&&(a.scheduler=t),o!==this.resourceGroupInfo.is_active&&(a.is_active=o),this.enableWSProxyAddr){let e=this.resourceGroupWSProxyaddressInput.value;e.endsWith("/")&&(e=e.slice(0,e.length-1)),e!==this.resourceGroupInfo.wsproxy_addr&&(a.wsproxy_addr=e)}if(this.enableSchedulerOpts&&r!==this.resourceGroupInfo.scheduler_opts&&(a.scheduler_opts=JSON.stringify(r)),this.enableIsPublic){const i=null===(e=this.resourceGroupPublicSwitch)||void 0===e?void 0:e.selected;i!==this.resourceGroupInfo.is_public&&(a.is_public=i)}if(0===Object.keys(a).length)return this.notification.text=p("resourceGroup.NochangesMade"),void this.notification.show();globalThis.backendaiclient.scalingGroup.update(s,a).then((({modify_scaling_group:e})=>{e.ok?(this.notification.text=p("resourceGroup.ResourceGroupModified"),this._refreshList()):(this.notification.text=u.relieve(e.msg),this.notification.detail=e.msg),this._hideDialogById("#resource-group-dialog"),this.notification.show()}))}_deleteResourceGroup(){const e=this.resourceGroupInfo.name;if(this.deleteResourceGroupInput.value!==e)return this.notification.text=p("resourceGroup.ResourceGroupNameNotMatch"),void this.notification.show();globalThis.backendaiclient.scalingGroup.delete(e).then((({delete_scaling_group:e})=>{e.ok?(this.notification.text=p("resourceGroup.ResourceGroupDeleted"),this._refreshList(),this.deleteResourceGroupInput.value=""):(this.notification.text=u.relieve(e.msg),this.notification.detail=e.msg),this._hideDialogById("#delete-resource-group-dialog"),this.notification.show()}))}_refreshList(){globalThis.backendaiclient.scalingGroup.list_available().then((({scaling_groups:e})=>{this.resourceGroups=e,this.requestUpdate()}))}_initializeCreateSchedulerOpts(){var e,i,t;const o=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#scheduler-options-input-form");this.allowedSessionTypesSelect.items=this.allowedSessionTypes,this.allowedSessionTypesSelect.selectedItemList=["interactive","batch"],this.resourceGroupSchedulerSelect.value="fifo",o.open=!1,(null===(i=this.timeoutInput)||void 0===i?void 0:i.value)&&(this.timeoutInput.value=""),(null===(t=this.numberOfRetriesToSkip)||void 0===t?void 0:t.value)&&(this.numberOfRetriesToSkip.value="")}_initializeModifySchedulerOpts(e="",i){var t;switch(e){case"allowed_session_types":this.allowedSessionTypesSelect.items=this.allowedSessionTypes,this.allowedSessionTypesSelect.selectedItemList=i;break;case"pending_timeout":this.timeoutInput.value=i;break;case"config":this.numberOfRetriesToSkip.value=null!==(t=i.num_retries_to_skip)&&void 0!==t?t:""}}_verifyCreateSchedulerOpts(){const e=[this.timeoutInput,this.numberOfRetriesToSkip].filter((e=>!e.checkValidity()));return e.push(...[this.allowedSessionTypesSelect.selectedItemList].filter((e=>0===e.length))),!(e.length>0)}_verifyModifySchedulerOpts(){const e=[this.timeoutInput,this.numberOfRetriesToSkip].filter((e=>!e.checkValidity()));return e.push(...[this.allowedSessionTypesSelect.selectedItemList].filter((e=>0===e.length))),!(e.length>0)}_saveSchedulerOpts(){this.schedulerOpts={},this.schedulerOpts.allowed_session_types=this.allowedSessionTypesSelect.selectedItemList,""!==this.timeoutInput.value&&(this.schedulerOpts.pending_timeout=this.timeoutInput.value),""!==this.numberOfRetriesToSkip.value&&Object.assign(this.schedulerOpts,{config:{num_retries_to_skip:this.numberOfRetriesToSkip.value}})}_launchCreateDialog(){this.enableSchedulerOpts&&this._initializeCreateSchedulerOpts(),this.resourceGroupInfo={},this._launchDialogById("#resource-group-dialog")}_launchDeleteDialog(e){this.resourceGroupInfo=e,this.deleteResourceGroupInput.value="",this._launchDialogById("#delete-resource-group-dialog")}_launchDetailDialog(e){this.resourceGroupInfo=e,this._launchDialogById("#resource-group-detail-dialog")}_launchModifyDialog(e){if(this.resourceGroupInfo=e,this.enableSchedulerOpts){const e=JSON.parse(this.resourceGroupInfo.scheduler_opts);Object.entries(e).forEach((([e,i])=>{this._initializeModifySchedulerOpts(e,i)}))}this._launchDialogById("#resource-group-dialog")}render(){var e,i,t,o,r,s,a,l,n,u,c,v,m,g,b,f,y,G,x,w,_,S;return d`
      <h4 class="horizontal flex center center-justified layout">
        <span>${h("resourceGroup.ResourceGroups")}</span>
        <span class="flex"></span>
        <mwc-button
          raised
          icon="add"
          label="${h("button.Add")}"
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
            header="${h("resourceGroup.Name")}"
            path="name"
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${h("resourceGroup.Description")}"
            path="description"
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${h("resourceGroup.ActiveStatus")}"
            resizable
            .renderer=${this._activeStatusRenderer}
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${h("resourceGroup.PublicStatus")}"
            resizable
            .renderer=${this._isPublicRenderer}
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${h("resourceGroup.Driver")}"
            path="driver"
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${h("resourceGroup.Scheduler")}"
            path="scheduler"
            resizable
          ></vaadin-grid-column>
          ${this.enableWSProxyAddr?d`
                <vaadin-grid-column
                  resizable
                  header="${h("resourceGroup.WsproxyAddress")}"
                  path="wsproxy_addr"
                  resizable
                ></vaadin-grid-column>
              `:d``}
          <vaadin-grid-column
            frozen-to-end
            resizable
            width="150px"
            header="${h("general.Control")}"
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
          ${(null===(e=this.resourceGroupInfo)||void 0===e?void 0:e.name)?h("resourceGroup.ModifyResourceGroup"):h("resourceGroup.CreateResourceGroup")}
        </span>
        <div slot="content" class="login-panel intro centered">
          ${0===Object.keys(this.resourceGroupInfo).length?d`
                <mwc-select
                  required
                  id="resource-group-domain"
                  label="${h("resourceGroup.SelectDomain")}"
                >
                  ${this.domains.map(((e,i)=>d`
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
                  label="${h("resourceGroup.ResourceGroupName")}"
                  maxLength="64"
                  placeholder="${h("maxLength.64chars")}"
                  validationMessage="${h("data.explorer.ValueRequired")}"
                  required
                  autoValidate
                  @change="${()=>this._validateResourceGroupName()}"
                ></mwc-textfield>
              `:d`
                <mwc-textfield
                  type="text"
                  disabled
                  label="${h("resourceGroup.ResourceGroupName")}"
                  value="${null===(i=this.resourceGroupInfo)||void 0===i?void 0:i.name}"
                ></mwc-textfield>
              `}
          <mwc-textarea
            name="description"
            id="resource-group-description"
            label="${h("resourceGroup.Description")}"
            maxLength="512"
            placeholder="${h("maxLength.512chars")}"
            value="${null!==(o=null===(t=this.resourceGroupInfo)||void 0===t?void 0:t.description)&&void 0!==o?o:""}"
          ></mwc-textarea>
          <mwc-select
            id="resource-group-scheduler"
            label="${h("resourceGroup.SelectScheduler")}"
            required
            value="${0===Object.keys(this.resourceGroupInfo).length?"fifo":this.resourceGroupInfo.scheduler}"
          >
            ${this.schedulerTypes.map((e=>d`
                <mwc-list-item value="${e}">${e}</mwc-list-item>
              `))}
          </mwc-select>
          <backend-ai-multi-select
            open-up
            required
            id="allowed-session-types"
            label="${h("resourceGroup.AllowedSessionTypes")}*"
            validation-message="${h("credential.validation.PleaseSelectOptions")}"
            style="width:100%; --select-title-padding-left: 16px;"
          ></backend-ai-multi-select>
          ${this.enableWSProxyAddr?d`
                <mwc-textfield
                  id="resource-group-wsproxy-address"
                  type="url"
                  label="${h("resourceGroup.WsproxyAddress")}"
                  placeholder="http://localhost:10200"
                  value="${null!==(s=null===(r=this.resourceGroupInfo)||void 0===r?void 0:r.wsproxy_addr)&&void 0!==s?s:""}"
                ></mwc-textfield>
              `:d``}
          <div class="horizontal layout flex wrap center justified">
            <p style="margin-left: 18px;">${h("resourceGroup.Active")}</p>
            <mwc-switch
              id="resource-group-active"
              style="margin-right:10px;"
              ?selected="${!(Object.keys(this.resourceGroupInfo).length>0)||this.resourceGroupInfo.is_active}"
            ></mwc-switch>
            ${this.enableIsPublic?d`
                  <p style="margin-left: 18px;">
                    ${h("resourceGroup.Public")}
                  </p>
                  <mwc-switch
                    id="resource-group-public"
                    style="margin-right:10px;"
                    ?selected="${!(Object.keys(this.resourceGroupInfo).length>0)||this.resourceGroupInfo.is_public}"
                  ></mwc-switch>
                `:d``}
          </div>
          ${this.enableSchedulerOpts?d`
                <br />
                <lablup-expansion id="scheduler-options-input-form">
                  <span slot="title">
                    ${h("resourceGroup.SchedulerOptions")}
                  </span>
                  <div class="vertical layout flex">
                    <mwc-textfield
                      type="number"
                      value="0"
                      id="pending-timeout"
                      label="pending timeout"
                      placeholder="0"
                      suffix="${h("resourceGroup.TimeoutSeconds")}"
                      validationMessage="${h("settings.InvalidValue")}"
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
                      suffix="${h("resourceGroup.RetriesToSkip")}"
                      validationMessage="${h("settings.InvalidValue")}"
                      autoValidate
                      min="0"
                      value="${null!==(m=null===(v=null===(c=null===(u=this.resourceGroupInfo)||void 0===u?void 0:u.scheduler_opts)||void 0===c?void 0:c.config)||void 0===v?void 0:v.num_retries_to_skip)&&void 0!==m?m:""}"
                    ></mwc-textfield>
                  </div>
                </lablup-expansion>
              `:d``}
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          ${Object.keys(this.resourceGroupInfo).length>0?d`
                <mwc-button
                  class="full"
                  unelevated
                  icon="save"
                  label="${h("button.Save")}"
                  @click="${this._modifyResourceGroup}"
                ></mwc-button>
              `:d`
                <mwc-button
                  class="full"
                  unelevated
                  icon="add"
                  label="${h("button.Create")}"
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
        <span slot="title">${h("dialog.warning.CannotBeUndone")}</span>
        <div slot="content">
          <mwc-textfield
            id="delete-resource-group"
            type="text"
            label="${h("resourceGroup.TypeResourceGroupNameToDelete")}"
            maxLength="64"
            placeholder="${h("maxLength.64chars")}"
          ></mwc-textfield>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            outlined
            label="${h("button.Cancel")}"
            @click="${e=>this._hideDialog(e)}"
          ></mwc-button>
          <mwc-button
            raised
            class="warning fg red"
            label="${h("button.Delete")}"
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
        ${Object.keys(this.resourceGroupInfo).length>0?d`
              <span slot="title" class="horizontal center layout">
                <span style="margin-right:15px;">
                  ${p("resourceGroup.ResourceGroupDetail")}
                </span>
              </span>
              <div slot="content" class="intro">
                <div class="horizontal layout" style="margin-bottom:15px;">
                  <div style="width:250px;">
                    <h4>${p("credential.Information")}</h4>
                    <div role="listbox" class="vertical layout">
                      <vaadin-item>
                        <div>
                          <strong>${p("resourceGroup.Name")}</strong>
                        </div>
                        <div class="scheduler-option-value">
                          ${this.resourceGroupInfo.name}
                        </div>
                      </vaadin-item>
                      <vaadin-item>
                        <div>
                          <strong>
                            ${p("resourceGroup.ActiveStatus")}
                          </strong>
                        </div>
                        <lablup-shields
                          app=""
                          color=${this.resourceGroupInfo.is_active?"green":"red"}
                          description=${(null===(g=this.resourceGroupInfo)||void 0===g?void 0:g.is_active)?"active":"inactive"}
                          ui="flat"
                        ></lablup-shields>
                      </vaadin-item>
                      ${this.enableIsPublic?d`
                            <vaadin-item>
                              <div>
                                <strong>
                                  ${p("resourceGroup.PublicStatus")}
                                </strong>
                              </div>
                              <lablup-shields
                                app=""
                                color=${this.resourceGroupInfo.is_public?"blue":"darkgreen"}
                                description=${(null===(b=this.resourceGroupInfo)||void 0===b?void 0:b.is_public)?"public":"private"}
                                ui="flat"
                              ></lablup-shields>
                            </vaadin-item>
                          `:d``}
                      <vaadin-item>
                        <div>
                          <strong>${p("resourceGroup.Driver")}</strong>
                        </div>
                        <div class="scheduler-option-value">
                          ${null===(f=this.resourceGroupInfo)||void 0===f?void 0:f.driver}
                        </div>
                      </vaadin-item>
                      <vaadin-item>
                        <div>
                          <strong>${p("resourceGroup.Scheduler")}</strong>
                        </div>
                        <div class="scheduler-option-value">
                          ${null===(y=this.resourceGroupInfo)||void 0===y?void 0:y.scheduler}
                        </div>
                      </vaadin-item>
                      ${this.enableWSProxyAddr?d`
                            <vaadin-item>
                              <div>
                                <strong>
                                  ${p("resourceGroup.WsproxyAddress")}
                                </strong>
                              </div>
                              <div class="scheduler-option-value">
                                ${null!==(x=null===(G=this.resourceGroupInfo)||void 0===G?void 0:G.wsproxy_addr)&&void 0!==x?x:"none"}
                              </div>
                            </vaadin-item>
                          `:d``}
                    </div>
                  </div>
                  <div class="center vertial layout" style="width:250px;">
                    <div>
                      <h4 class="horizontal center layout">
                        ${h("resourceGroup.SchedulerOptions")}
                      </h4>
                      <div role="listbox">
                        ${this.enableSchedulerOpts?d`
                              ${Object.entries(JSON.parse(null===(w=this.resourceGroupInfo)||void 0===w?void 0:w.scheduler_opts)).map((([e,i])=>"allowed_session_types"===e?d`
                                    <vaadin-item>
                                      <div>
                                        <strong>allowed session types</strong>
                                      </div>
                                      <div class="scheduler-option-value">
                                        ${i.join(", ")}
                                      </div>
                                    </vaadin-item>
                                  `:"pending_timeout"===e?d`
                                    <vaadin-item>
                                      <div>
                                        <strong>pending timeout</strong>
                                      </div>
                                      <div class="scheduler-option-value">
                                        ${i+" "+p("resourceGroup.TimeoutSeconds")}
                                      </div>
                                    </vaadin-item>
                                  `:"config"===e&&i.num_retries_to_skip?d`
                                      <vaadin-item>
                                        <div>
                                          <strong>
                                            # retries to skip pending session
                                          </strong>
                                        </div>
                                        <div class="scheduler-option-value">
                                          ${i.num_retries_to_skip+" "+p("resourceGroup.RetriesToSkip")}
                                        </div>
                                      </vaadin-item>
                                    `:""))}
                            `:d``}
                      </div>
                    </div>
                    <div>
                      <h4 class="horizontal center layout">
                        ${h("resourceGroup.DriverOptions")}
                      </h4>
                      <div role="listbox"></div>
                    </div>
                  </div>
                </div>
                <div>
                  <h4>${h("resourceGroup.Description")}</h4>
                  <mwc-textarea
                    readonly
                    value="${null!==(S=null===(_=this.resourceGroupInfo)||void 0===_?void 0:_.description)&&void 0!==S?S:""}"
                  ></mwc-textarea>
                </div>
              </div>
            `:""}
      </backend-ai-dialog>
    `}};e([i({type:Object})],m.prototype,"_boundControlRenderer",void 0),e([i({type:Array})],m.prototype,"domains",void 0),e([i({type:Object})],m.prototype,"resourceGroupInfo",void 0),e([i({type:Array})],m.prototype,"resourceGroups",void 0),e([i({type:Array})],m.prototype,"schedulerTypes",void 0),e([i({type:Object})],m.prototype,"schedulerOpts",void 0),e([v()],m.prototype,"allowedSessionTypes",void 0),e([i({type:Boolean})],m.prototype,"enableSchedulerOpts",void 0),e([i({type:Boolean})],m.prototype,"enableWSProxyAddr",void 0),e([i({type:Boolean})],m.prototype,"enableIsPublic",void 0),e([i({type:Number})],m.prototype,"functionCount",void 0),e([t("#resource-group-name")],m.prototype,"resourceGroupNameInput",void 0),e([t("#resource-group-description")],m.prototype,"resourceGroupDescriptionInput",void 0),e([t("#resource-group-domain")],m.prototype,"resourceGroupDomainSelect",void 0),e([t("#resource-group-scheduler")],m.prototype,"resourceGroupSchedulerSelect",void 0),e([t("#resource-group-active")],m.prototype,"resourceGroupActiveSwitch",void 0),e([t("#resource-group-public")],m.prototype,"resourceGroupPublicSwitch",void 0),e([t("#resource-group-wsproxy-address")],m.prototype,"resourceGroupWSProxyaddressInput",void 0),e([t("#allowed-session-types")],m.prototype,"allowedSessionTypesSelect",void 0),e([t("#num-retries-to-skip")],m.prototype,"numberOfRetriesToSkip",void 0),e([t("#pending-timeout")],m.prototype,"timeoutInput",void 0),e([t("#delete-resource-group")],m.prototype,"deleteResourceGroupInput",void 0),m=e([o("backend-ai-resource-group-list")],m);
