import{_ as e,n as i,b as t,e as s,B as o,c as a,I as r,a as l,q as n,d as c,i as d,f as u,g as p,m as h,x as m,t as v,w as y,Q as _}from"./backend-ai-webui-45991858.js";import{J as g}from"./vaadin-iconset-6df57566.js";import"./backend-ai-list-status-3729db9d.js";import"./lablup-grid-sort-filter-column-aaed165a.js";import"./vaadin-grid-9c58de6c.js";import"./vaadin-grid-filter-column-6eee22d1.js";import"./vaadin-grid-sort-column-64ff581b.js";import"./vaadin-item-debf19ae.js";import"./backend-ai-multi-select-e516ca4b.js";import"./mwc-switch-ae556d04.js";import"./lablup-activity-panel-5f8f4051.js";import"./mwc-formfield-2b8629fe.js";import"./mwc-tab-bar-b2673269.js";import"./dir-utils-fd56b6df.js";import"./vaadin-item-mixin-0f1c0947.js";import"./mwc-check-list-item-99dff446.js";var f;class b extends Error{constructor(e){super(e),Object.setPrototypeOf(this,b.prototype),this.title="Unable to delete keypair"}}let w=f=class extends o{constructor(){super(),this.keypairInfo={user_id:"1",access_key:"ABC",secret_key:"ABC",last_used:"",is_admin:!1,resource_policy:"",rate_limit:5e3,concurrency_used:0,num_queries:0,created_at:""},this.isAdmin=!1,this.condition="active",this.keypairs=[],this.resourcePolicy=Object(),this.indicator=Object(),this._boundKeyageRenderer=this.keyageRenderer.bind(this),this._boundControlRenderer=this.controlRenderer.bind(this),this._boundAccessKeyRenderer=this.accessKeyRenderer.bind(this),this._boundPermissionRenderer=this.permissionRenderer.bind(this),this._boundResourcePolicyRenderer=this.resourcePolicyRenderer.bind(this),this._boundAllocationRenderer=this.allocationRenderer.bind(this),this._boundUserIdRenderer=this.userIdRenderer.bind(this),this.keypairGrid=Object(),this.listCondition="loading",this._totalCredentialCount=0,this.isUserInfoMaskEnabled=!1,this.deleteKeyPairUserName="",this.deleteKeyPairAccessKey="",this.supportMainAccessKey=!1,this._mainAccessKeyList=[]}static get styles(){return[a,r,l,n,c,d`
        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 229px);
        }

        mwc-icon-button {
          --mdc-icon-size: 24px;
          padding: 0;
        }

        mwc-icon {
          --mdc-icon-size: 16px;
          padding: 0;
        }

        vaadin-item {
          font-size: 13px;
          font-weight: 100;
        }

        vaadin-item div[secondary] {
          font-weight: 400;
        }

        div.indicator,
        span.indicator {
          font-size: 9px;
          margin-right: 5px;
        }

        div.configuration {
          width: 100px !important;
        }

        div.configuration mwc-icon {
          padding-right: 5px;
        }

        #keypair-modify-save {
          --button-bg: var(--paper-light-green-50);
          --button-bg-hover: var(--paper-green-100);
          --button-bg-active: var(--paper-green-600);
        }

        #policy-list {
          width: 100%;
        }

        backend-ai-dialog {
          --component-min-width: 400px;
        }

        backend-ai-dialog h4 {
          font-size: 14px;
          padding: 5px 15px 5px 12px;
          margin: 0 0 10px 0;
          display: block;
          height: 20px;
          border-bottom: 1px solid #ddd;
        }

        mwc-button,
        mwc-button[unelevated],
        mwc-button[outlined] {
          background-image: none;
          --mdc-theme-primary: var(--general-button-background-color);
          --mdc-theme-on-primary: var(--general-button-color);
          --mdc-typography-font-family: var(--token-fontFamily);
        }
      `]}firstUpdated(){this.notification=globalThis.lablupNotification}async _viewStateChanged(e){var i;await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{var e;this._refreshKeyData(),this.isAdmin=globalThis.backendaiclient.is_admin,this.supportMainAccessKey=globalThis.backendaiclient.supports("main-access-key"),this.isUserInfoMaskEnabled=globalThis.backendaiclient._config.maskUserInfo,this.keypairGrid=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#keypair-grid")}),!0):(this._refreshKeyData(),this.isAdmin=globalThis.backendaiclient.is_admin,this.supportMainAccessKey=globalThis.backendaiclient.supports("main-access-key"),this.isUserInfoMaskEnabled=globalThis.backendaiclient._config.maskUserInfo,this.keypairGrid=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#keypair-grid")))}_refreshKeyData(e=null){var i;let t=!0;if("active"===this.condition)t=!0;else t=!1;return this.listCondition="loading",null===(i=this._listStatus)||void 0===i||i.show(),globalThis.backendaiclient.resourcePolicy.get().then((e=>{const i=e.keypair_resource_policies;this.resourcePolicy=globalThis.backendaiclient.utils.gqlToObject(i,"name")})).then((()=>globalThis.backendaiclient.keypair.list(e,["access_key","is_active","is_admin","user_id","created_at","last_used","concurrency_limit","concurrency_used","rate_limit","num_queries","resource_policy"],t))).then((async e=>{var i;if(this.supportMainAccessKey)try{const e=await globalThis.backendaiclient.user.list(!0,["main_access_key"]),i=await globalThis.backendaiclient.user.list(!1,["main_access_key"]);e.users&&i.users&&(this._mainAccessKeyList=[...e.users,...i.users].map((e=>e.main_access_key)))}catch(e){throw e}const t=e.keypairs;Object.keys(t).map(((e,i)=>{const s=t[e];if(s.resource_policy in this.resourcePolicy){for(const e in this.resourcePolicy[s.resource_policy])"created_at"!==e&&(s[e]=this.resourcePolicy[s.resource_policy][e],"total_resource_slots"===e&&(s.total_resource_slots=JSON.parse(this.resourcePolicy[s.resource_policy][e])));s.created_at_formatted=this._humanReadableTime(s.created_at),s.elapsed=this._elapsed(s.created_at),"cpu"in s.total_resource_slots||"UNLIMITED"===s.default_for_unspecified&&(s.total_resource_slots.cpu="-"),"mem"in s.total_resource_slots?s.total_resource_slots.mem=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(s.total_resource_slots.mem,"g")):"UNLIMITED"===s.default_for_unspecified&&(s.total_resource_slots.mem="-"),"cuda.device"in s.total_resource_slots&&(s.total_resource_slots.cuda_device=s.total_resource_slots["cuda.device"]),"cuda.shares"in s.total_resource_slots&&(s.total_resource_slots.cuda_shares=s.total_resource_slots["cuda.shares"]),"cuda_device"in s.total_resource_slots==!1&&"cuda_shares"in s.total_resource_slots==!1&&"UNLIMITED"===s.default_for_unspecified&&(s.total_resource_slots.cuda_shares="-",s.total_resource_slots.cuda_device="-"),"rocm.device"in s.total_resource_slots&&(s.total_resource_slots.rocm_device=s.total_resource_slots["rocm.device"]),"rocm_device"in s.total_resource_slots==!1&&"UNLIMITED"===s.default_for_unspecified&&(s.total_resource_slots.rocm_device="-"),"tpu.device"in s.total_resource_slots&&(s.total_resource_slots.tpu_device=s.total_resource_slots["tpu.device"]),"tpu_device"in s.total_resource_slots==!1&&"UNLIMITED"===s.default_for_unspecified&&(s.total_resource_slots.tpu_device="-"),"ipu.device"in s.total_resource_slots&&(s.total_resource_slots.ipu_device=s.total_resource_slots["ipu.device"]),"ipu_device"in s.total_resource_slots==!1&&"UNLIMITED"===s.default_for_unspecified&&(s.total_resource_slots.ipu_device="-"),"atom.device"in s.total_resource_slots&&(s.total_resource_slots.tpu_device=s.total_resource_slots["atom.device"]),"atom_device"in s.total_resource_slots==!1&&"UNLIMITED"===s.default_for_unspecified&&(s.total_resource_slots.atom_device="-"),"warboy.device"in s.total_resource_slots&&(s.total_resource_slots.tpu_device=s.total_resource_slots["warboy.device"]),"warboy_device"in s.total_resource_slots==!1&&"UNLIMITED"===s.default_for_unspecified&&(s.total_resource_slots.warboy_device="-"),["cpu","mem","cuda_shares","cuda_device","rocm_device","tpu_device","ipu_device","atom_device","warboy_device"].forEach((e=>{s.total_resource_slots[e]=this._markIfUnlimited(s.total_resource_slots[e])})),s.max_vfolder_size=this._markIfUnlimited(f.bytesToGB(s.max_vfolder_size))}})),this.keypairs=t,0==this.keypairs.length?this.listCondition="no-data":null===(i=this._listStatus)||void 0===i||i.hide()})).catch((e=>{var i;null===(i=this._listStatus)||void 0===i||i.hide(),console.log(e),e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}async _showKeypairDetail(e){const i=e.target.closest("#controls")["access-key"];try{const e=await this._getKeyData(i);this.keypairInfo=e.keypair,this.keypairInfoDialog.show()}catch(e){e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}}async _modifyResourcePolicy(e){const i=e.target.closest("#controls")["access-key"];try{const e=await this._getKeyData(i);this.keypairInfo=e.keypair,this.policyListSelect.value=this.keypairInfo.resource_policy,this.rateLimit.value=this.keypairInfo.rate_limit.toString(),this.keypairModifyDialog.show()}catch(e){e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}}async _getKeyData(e){return globalThis.backendaiclient.keypair.info(e,["access_key","secret_key","is_active","is_admin","user_id","created_at","last_used","concurrency_limit","concurrency_used","rate_limit","num_queries","resource_policy"])}refresh(){this._refreshKeyData()}_isActive(){return"active"===this.condition}_deleteKeyPairDialog(e){const i=e.target.closest("#controls"),t=i["user-id"],s=i["access-key"];this.deleteKeyPairUserName=t,this.deleteKeyPairAccessKey=s,this.deleteKeyPairDialog.show()}_deleteKey(e){globalThis.backendaiclient.keypair.delete(this.deleteKeyPairAccessKey).then((e=>{if(e.delete_keypair&&!e.delete_keypair.ok)throw new b(e.delete_keypair.msg);this.notification.text=p("credential.KeySeccessfullyDeleted"),this.notification.show(),this.refresh(),this.deleteKeyPairDialog.hide()})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_revokeKey(e){this._mutateKey(e,!1)}_reuseKey(e){this._mutateKey(e,!0)}_mutateKey(e,i){const t=e.target.closest("#controls")["access-key"],s=this.keypairs.find(this._findKeyItem,t),o={is_active:i,is_admin:s.is_admin,resource_policy:s.resource_policy,rate_limit:s.rate_limit,concurrency_limit:s.concurrency_limit};globalThis.backendaiclient.keypair.mutate(t,o).then((e=>{const i=new CustomEvent("backend-ai-credential-refresh",{detail:this});document.dispatchEvent(i)})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_findKeyItem(e){return e.access_key=this}_elapsed(e,i){const t=new Date(e),s=(this.condition,new Date),o=Math.floor((s.getTime()-t.getTime())/1e3);return Math.floor(o/86400)}_humanReadableTime(e){return new Date(e).toUTCString()}_indexRenderer(e,i,t){const s=t.index+1;h(m`
        <div>${s}</div>
      `,e)}_markIfUnlimited(e){return["-",0,"Unlimited",1/0,"Infinity"].includes(e)?"∞":e}keyageRenderer(e,i,t){h(m`
        <div class="layout vertical">
          <span>${t.item.elapsed} ${v("credential.Days")}</span>
          <span class="indicator">(${t.item.created_at_formatted})</span>
        </div>
      `,e)}controlRenderer(e,i,t){var s;h(m`
        <div
          id="controls"
          class="layout horizontal flex center"
          .access-key="${t.item.access_key}"
          .user-id="${t.item.user_id}"
        >
          <mwc-icon-button
            class="fg green"
            icon="assignment"
            fab
            flat
            inverted
            @click="${e=>this._showKeypairDetail(e)}"
          ></mwc-icon-button>
          <mwc-icon-button
            class="fg blue"
            icon="settings"
            fab
            flat
            inverted
            @click="${e=>this._modifyResourcePolicy(e)}"
          ></mwc-icon-button>
          ${this.isAdmin&&this._isActive()?m`
                <mwc-icon-button
                  class="fg blue"
                  icon="delete"
                  fab
                  flat
                  inverted
                  @click="${e=>this._revokeKey(e)}"
                ></mwc-icon-button>
                <mwc-icon-button
                  class="fg red"
                  icon="delete_forever"
                  fab
                  ?disabled=${this._mainAccessKeyList.includes(null===(s=t.item)||void 0===s?void 0:s.access_key)}
                  flat
                  inverted
                  @click="${e=>this._deleteKeyPairDialog(e)}"
                ></mwc-icon-button>
              `:m``}
          ${!1===this._isActive()?m`
                <mwc-icon-button
                  class="fg blue"
                  icon="redo"
                  fab
                  flat
                  inverted
                  @click="${e=>this._reuseKey(e)}"
                ></mwc-icon-button>
              `:m``}
        </div>
      `,e)}accessKeyRenderer(e,i,t){var s;h(m`
        <div class="vertical layout flex">
          <div class="monospace">${t.item.access_key}</div>
          ${this._mainAccessKeyList.includes(null===(s=t.item)||void 0===s?void 0:s.access_key)?m`
                <lablup-shields
                  app=""
                  color="red"
                  description="${v("credential.MainAccessKey")}"
                  ui="flat"
                ></lablup-shields>
              `:m``}
        </div>
      `,e)}permissionRenderer(e,i,t){h(m`
        <div class="layout horizontal center flex">
          ${t.item.is_admin?m`
                <lablup-shields
                  app=""
                  color="red"
                  description="admin"
                  ui="flat"
                ></lablup-shields>
              `:m``}
          <lablup-shields app="" description="user" ui="flat"></lablup-shields>
        </div>
      `,e)}resourcePolicyRenderer(e,i,t){h(m`
        <div class="layout horizontal wrap center">
          <span>${t.item.resource_policy}</span>
        </div>
        <div class="layout horizontal wrap center">
          <div class="layout horizontal configuration">
            <mwc-icon class="fg green">developer_board</mwc-icon>
            <span>${t.item.total_resource_slots.cpu}</span>
            <span class="indicator">${v("general.cores")}</span>
          </div>
          <div class="layout horizontal configuration">
            <mwc-icon class="fg green">memory</mwc-icon>
            <span>${t.item.total_resource_slots.mem}</span>
            <span class="indicator">GiB</span>
          </div>
        </div>
        <div class="layout horizontal wrap center">
          ${t.item.total_resource_slots.cuda_device?m`
                <div class="layout horizontal configuration">
                  <mwc-icon class="fg green">view_module</mwc-icon>
                  <span>${t.item.total_resource_slots.cuda_device}</span>
                  <span class="indicator">GPU</span>
                </div>
              `:m``}
          ${t.item.total_resource_slots.cuda_shares?m`
                <div class="layout horizontal configuration">
                  <mwc-icon class="fg green">view_module</mwc-icon>
                  <span>${t.item.total_resource_slots.cuda_shares}</span>
                  <span class="indicator">fGPU</span>
                </div>
              `:m``}
        </div>
        <div class="layout horizontal wrap center">
          <div class="layout horizontal configuration">
            <mwc-icon class="fg green">cloud_queue</mwc-icon>
            <span>${t.item.max_vfolder_size}</span>
            <span class="indicator">GB</span>
          </div>
        </div>
        <div class="layout horizontal configuration">
          <mwc-icon class="fg green">folder</mwc-icon>
          <span>${t.item.max_vfolder_count}</span>
          <span class="indicator">${v("general.Folders")}</span>
        </div>
      `,e)}allocationRenderer(e,i,t){h(m`
        <div class="layout horizontal center flex">
          <div class="vertical start layout">
            <div style="font-size:11px;width:40px;">
              ${t.item.concurrency_used} /
              ${t.item.concurrency_limit}
            </div>
            <span class="indicator">Sess.</span>
          </div>
          <div class="vertical start layout">
            <span style="font-size:8px">
              ${t.item.rate_limit}
              <span class="indicator">req./15m.</span>
            </span>
            <span style="font-size:8px">
              ${t.item.num_queries}
              <span class="indicator">queries</span>
            </span>
          </div>
        </div>
      `,e)}userIdRenderer(e,i,t){h(m`
        <span>${this._getUserId(t.item.user_id)}</span>
      `,e)}_validateRateLimit(){this.rateLimit.validityTransform=(e,i)=>i.valid?0!==e.length&&!isNaN(Number(e))&&Number(e)<100?(this.rateLimit.validationMessage=p("credential.WarningLessRateLimit"),{valid:!i.valid,customError:!i.valid}):{valid:i.valid,customError:!i.valid}:i.valueMissing?(this.rateLimit.validationMessage=p("credential.RateLimitInputRequired"),{valid:i.valid,customError:!i.valid}):i.rangeOverflow?(this.rateLimit.value=e=5e4.toString(),this.rateLimit.validationMessage=p("credential.RateLimitValidation"),{valid:i.valid,customError:!i.valid}):i.rangeUnderflow?(this.rateLimit.value=e="1",this.rateLimit.validationMessage=p("credential.RateLimitValidation"),{valid:i.valid,customError:!i.valid}):(this.rateLimit.validationMessage=p("credential.InvalidRateLimitValue"),{valid:i.valid,customError:!i.valid})}openDialog(e){var i;(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+e)).show()}closeDialog(e){var i;(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+e)).hide()}_saveKeypairModification(e=!1){const i=this.policyListSelect.value,t=Number(this.rateLimit.value);if(!(this.rateLimit.checkValidity()||t<100&&e))return t<100&&!e?void this.openDialog("keypair-confirmation"):void 0;let s={};i!==this.keypairInfo.resource_policy&&(s={...s,resource_policy:i}),t!==this.keypairInfo.rate_limit&&(s={...s,rate_limit:t}),0===Object.entries(s).length?(this.notification.text=p("credential.NoChanges"),this.notification.show()):globalThis.backendaiclient.keypair.mutate(this.keypairInfo.access_key,s).then((e=>{e.modify_keypair.ok?(this.keypairInfo.resource_policy===i&&this.keypairInfo.rate_limit===t?this.notification.text=p("credential.NoChanges"):this.notification.text=p("environment.SuccessfullyModified"),this.refresh()):this.notification.text=p("dialog.ErrorOccurred"),this.notification.show()})),this.closeDialog("keypair-modify-dialog")}_confirmAndSaveKeypairModification(){this.closeDialog("keypair-confirmation"),this._saveKeypairModification(!0)}_adjustRateLimit(){const e=Number(this.rateLimit.value);e>5e4&&(this.rateLimit.value=5e4.toString()),e<=0&&(this.rateLimit.value="1")}static bytesToGB(e,i=1){return e?(e/10**9).toFixed(i):e}_getUserId(e=""){if(this.isUserInfoMaskEnabled){const i=2,t=e.split("@")[0].length-i;e=globalThis.backendaiutils._maskString(e,"*",i,t)}return e}_getAccessKey(e=""){if(this.isUserInfoMaskEnabled){const i=4,t=e.length-i;e=globalThis.backendaiutils._maskString(e,"*",i,t)}return e}render(){return m`
      <div class="list-wrapper">
        <vaadin-grid
          theme="row-stripes column-borders compact dark"
          aria-label="Credential list"
          id="keypair-grid"
          .items="${this.keypairs}"
        >
          <vaadin-grid-column
            width="40px"
            flex-grow="0"
            header="#"
            text-align="center"
            .renderer="${this._indexRenderer.bind(this)}"
          ></vaadin-grid-column>
          <lablup-grid-sort-filter-column
            path="user_id"
            auto-width
            header="${v("credential.UserID")}"
            resizable
            .renderer="${this._boundUserIdRenderer}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="access_key"
            auto-width
            header="${v("general.AccessKey")}"
            resizable
            .renderer="${this._boundAccessKeyRenderer}"
          ></lablup-grid-sort-filter-column>
          <vaadin-grid-sort-column
            resizable
            header="${v("credential.Permission")}"
            path="admin"
            .renderer="${this._boundPermissionRenderer}"
          ></vaadin-grid-sort-column>
          <vaadin-grid-sort-column
            auto-width
            resizable
            header="${v("credential.KeyAge")}"
            path="created_at"
            .renderer="${this._boundKeyageRenderer}"
          ></vaadin-grid-sort-column>
          <vaadin-grid-column
            width="200px"
            resizable
            header="${v("credential.ResourcePolicy")}"
            .renderer="${this._boundResourcePolicyRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            auto-width
            resizable
            header="${v("credential.Allocation")}"
            .renderer="${this._boundAllocationRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            width="208px"
            resizable
            header="${v("general.Control")}"
            .renderer="${this._boundControlRenderer}"
          ></vaadin-grid-column>
        </vaadin-grid>
        <backend-ai-list-status
          id="list-status"
          statusCondition="${this.listCondition}"
          message="${p("credential.NoCredentialToDisplay")}"
        ></backend-ai-list-status>
      </div>
      <backend-ai-dialog id="delete-keypair-dialog" fixed backdrop>
        <span slot="title">${v("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>
            You are deleting the credentials of user
            <span style="color:red">${this.deleteKeyPairUserName}</span>
            .
          </p>
          <p>${v("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            label="${v("button.Cancel")}"
            @click="${e=>this._hideDialog(e)}"
          ></mwc-button>
          <mwc-button
            unelevated
            label="${v("button.Okay")}"
            @click="${e=>this._deleteKey(e)}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog
        id="keypair-info-dialog"
        fixed
        backdrop
        blockscrolling
        container="${document.body}"
      >
        <span slot="title">${v("credential.KeypairDetail")}</span>
        <div slot="action" class="horizontal end-justified flex layout">
          ${this.keypairInfo.is_admin?m`
                <lablup-shields
                  class="layout horizontal center"
                  app=""
                  color="red"
                  description="admin"
                  ui="flat"
                ></lablup-shields>
              `:m``}
          <lablup-shields
            class="layout horizontal center"
            app=""
            description="user"
            ui="flat"
          ></lablup-shields>
        </div>
        <div slot="content" class="intro">
          <div class="horizontal layout">
            <div style="width:335px;">
              <h4>${v("credential.Information")}</h4>
              <div role="listbox" style="margin: 0;">
                <vaadin-item>
                  <div><strong>${v("credential.UserID")}</strong></div>
                  <div secondary>${this.keypairInfo.user_id}</div>
                </vaadin-item>
                <vaadin-item>
                  <div><strong>${v("general.AccessKey")}</strong></div>
                  <div secondary>${this.keypairInfo.access_key}</div>
                </vaadin-item>
                <vaadin-item>
                  <div><strong>${v("general.SecretKey")}</strong></div>
                  <div secondary>${this.keypairInfo.secret_key}</div>
                </vaadin-item>
                <vaadin-item>
                  <div><strong>${v("credential.Created")}</strong></div>
                  <div secondary>${this.keypairInfo.created_at}</div>
                </vaadin-item>
                <vaadin-item>
                  <div><strong>${v("credential.Lastused")}</strong></div>
                  <div secondary>${this.keypairInfo.last_used}</div>
                </vaadin-item>
              </div>
            </div>
            <div style="width:335px;">
              <h4>${v("credential.Allocation")}</h4>
              <div role="listbox" style="margin: 0;">
                <vaadin-item>
                  <div><strong>${v("credential.ResourcePolicy")}</strong></div>
                  <div secondary>${this.keypairInfo.resource_policy}</div>
                </vaadin-item>
                <vaadin-item>
                  <div>
                    <strong>${v("credential.NumberOfQueries")}</strong>
                  </div>
                  <div secondary>${this.keypairInfo.num_queries}</div>
                </vaadin-item>
                <vaadin-item>
                  <div>
                    <strong>${v("credential.ConcurrentSessions")}</strong>
                  </div>
                  <div secondary>
                    ${this.keypairInfo.concurrency_used}
                    ${v("credential.active")} /
                    ${this.keypairInfo.concurrency_used}
                    ${v("credential.concurrentsessions")}.
                  </div>
                </vaadin-item>
                <vaadin-item>
                  <div><strong>${v("credential.RateLimit")}</strong></div>
                  <div secondary>
                    ${this.keypairInfo.rate_limit}
                    ${v("credential.for900seconds")}.
                  </div>
                </vaadin-item>
              </div>
            </div>
          </div>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog
        id="keypair-modify-dialog"
        fixed
        backdrop
        blockscrolling
      >
        <span slot="title">
          ${v("credential.ModifyKeypairResourcePolicy")}
        </span>

        <div slot="content" class="vertical layout">
          <div class="vertical layout center-justified">
            <mwc-select
              id="policy-list"
              label="${v("credential.SelectPolicy")}"
            >
              ${Object.keys(this.resourcePolicy).map((e=>m`
                  <mwc-list-item value=${this.resourcePolicy[e].name}>
                    ${this.resourcePolicy[e].name}
                  </mwc-list-item>
                `))}
            </mwc-select>
          </div>
          <div class="vertical layout center-justified">
            <mwc-textfield
              type="number"
              id="rate-limit"
              min="1"
              max="50000"
              label="${v("credential.RateLimit")}"
              validationMessage="${v("credential.RateLimitValidation")}"
              helper="${v("credential.RateLimitValidation")}"
              @change="${()=>this._validateRateLimit()}"
              value="${this.keypairInfo.rate_limit}"
            ></mwc-textfield>
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            unelevated
            fullwidth
            id="keypair-modify-save"
            icon="check"
            label="${v("button.SaveChanges")}"
            @click="${()=>this._saveKeypairModification()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="keypair-confirmation" warning fixed>
        <span slot="title">${v("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${v("credential.WarningLessRateLimit")}</p>
          <p>${v("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            label="${p("button.Cancel")}"
            @click="${e=>this._hideDialog(e)}"
            style="width:auto;margin-right:10px;"
          ></mwc-button>
          <mwc-button
            unelevated
            label="${p("button.DismissAndProceed")}"
            @click="${()=>this._confirmAndSaveKeypairModification()}"
            style="width:auto;"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};var x;e([i({type:Object})],w.prototype,"notification",void 0),e([i({type:Object})],w.prototype,"keypairInfo",void 0),e([i({type:Boolean})],w.prototype,"isAdmin",void 0),e([i({type:String})],w.prototype,"condition",void 0),e([i({type:Array})],w.prototype,"keypairs",void 0),e([i({type:Object})],w.prototype,"resourcePolicy",void 0),e([i({type:Object})],w.prototype,"indicator",void 0),e([i({type:Object})],w.prototype,"_boundKeyageRenderer",void 0),e([i({type:Object})],w.prototype,"_boundControlRenderer",void 0),e([i({type:Object})],w.prototype,"_boundAccessKeyRenderer",void 0),e([i({type:Object})],w.prototype,"_boundPermissionRenderer",void 0),e([i({type:Object})],w.prototype,"_boundResourcePolicyRenderer",void 0),e([i({type:Object})],w.prototype,"_boundAllocationRenderer",void 0),e([i({type:Object})],w.prototype,"_boundUserIdRenderer",void 0),e([i({type:Object})],w.prototype,"keypairGrid",void 0),e([i({type:String})],w.prototype,"listCondition",void 0),e([i({type:Number})],w.prototype,"_totalCredentialCount",void 0),e([i({type:Boolean})],w.prototype,"isUserInfoMaskEnabled",void 0),e([i({type:String})],w.prototype,"deleteKeyPairUserName",void 0),e([i({type:String})],w.prototype,"deleteKeyPairAccessKey",void 0),e([i({type:Boolean})],w.prototype,"supportMainAccessKey",void 0),e([i({type:Array})],w.prototype,"_mainAccessKeyList",void 0),e([t("#keypair-info-dialog")],w.prototype,"keypairInfoDialog",void 0),e([t("#keypair-modify-dialog")],w.prototype,"keypairModifyDialog",void 0),e([t("#delete-keypair-dialog")],w.prototype,"deleteKeyPairDialog",void 0),e([t("#policy-list")],w.prototype,"policyListSelect",void 0),e([t("#rate-limit")],w.prototype,"rateLimit",void 0),e([t("#list-status")],w.prototype,"_listStatus",void 0),w=f=e([s("backend-ai-credential-list")],w);class k{static getValue(){return 1e6}}let $=x=class extends o{constructor(){super(),this.visible=!1,this.listCondition="loading",this.keypairs={},this.resourcePolicy=[],this.keypairInfo={},this.active=!1,this.condition="active",this.current_policy_name="",this.enableSessionLifetime=!1,this.enableParsingStoragePermissions=!1,this._boundResourceRenderer=Object(),this._boundConcurrencyRenderer=this.concurrencyRenderer.bind(this),this._boundControlRenderer=this.controlRenderer.bind(this),this._boundPolicyNameRenderer=this.policyNameRenderer.bind(this),this._boundClusterSizeRenderer=this.clusterSizeRenderer.bind(this),this._boundStorageNodesRenderer=this.storageNodesRenderer.bind(this),this.is_super_admin=!1,this.isSupportMaxVfolderCountInUserResourcePolicy=!1,this.all_vfolder_hosts=[],this.allowed_vfolder_hosts={},this.vfolderPermissions=[],this.resource_policy_names=[],this._boundResourceRenderer=this.resourceRenderer.bind(this)}static get styles(){return[a,r,l,d`
        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 229px);
        }

        mwc-checkbox {
          margin-left: 0;
          --mdc-icon-size: 14px;
          --mdc-checkbox-ripple-size: 20px;
          --mdc-checkbox-state-layer-size: 14px;
        }

        mwc-formfield {
          font-size: 8px;
          --mdc-typography-body2-font-size: 10px;
        }

        mwc-icon.indicator {
          --mdc-icon-size: 16px;
        }

        vaadin-item {
          font-size: 13px;
          font-weight: 100;
        }

        div.indicator,
        span.indicator {
          font-size: 9px;
          margin-right: 5px;
        }

        div.configuration {
          width: 100px !important;
        }

        div.configuration mwc-icon {
          padding-right: 5px;
        }

        div.sessions-section {
          width: 167px;
          margin-bottom: 10px;
        }

        mwc-textfield {
          width: 100%;
          --mdc-text-field-fill-color: transparent;
          --mdc-theme-primary: var(--general-textfield-selected-color);
          --mdc-typography-font-family: var(--token-fontFamily);
        }

        mwc-textfield.resource-input {
          width: 5rem;
        }

        mwc-list-item {
          --mdc-menu-item-height: auto;
          font-size: 14px;
        }

        backend-ai-dialog {
          --component-min-width: 350px;
          --component-max-width: 390px;
        }
        backend-ai-dialog h4 {
          font-size: 14px;
          padding: 5px 15px 5px 12px;
          margin: 0 0 10px 0;
          display: block;
          height: 20px;
          border-bottom: 1px solid #ddd;
        }
        div.popup-right-margin {
          margin-right: 5px;
        }
        div.popup-left-margin {
          margin-left: 5px;
        }
        div.popup-both-margin {
          margin-left: 5px;
          margin-right: 5px;
        }
      `]}render(){return m`
      <div class="list-wrapper">
        <vaadin-grid
          theme="row-stripes column-borders compact dark"
          aria-label="Resource Policy list"
          .items="${this.resourcePolicy}"
        >
          <vaadin-grid-column
            frozen
            width="40px"
            flex-grow="0"
            header="#"
            text-align="center"
            .renderer="${this._indexRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-sort-column
            frozen
            resizable
            header="${v("resourcePolicy.Name")}"
            path="name"
            .renderer="${this._boundPolicyNameRenderer}"
          ></vaadin-grid-sort-column>
          <vaadin-grid-column
            width="180px"
            resizable
            header="${v("resourcePolicy.Resources")}"
            .renderer="${this._boundResourceRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            resizable
            header="${v("resourcePolicy.Concurrency")}"
            .renderer="${this._boundConcurrencyRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-sort-column
            resizable
            header="${v("resourcePolicy.ClusterSize")}"
            path="max_containers_per_session"
            .renderer="${this._boundClusterSizeRenderer}"
          ></vaadin-grid-sort-column>
          <vaadin-grid-column
            resizable
            header="${v("resourcePolicy.StorageNodes")}"
            .renderer="${this._boundStorageNodesRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            frozen-to-end
            width="110px"
            resizable
            header="${v("general.Control")}"
            .renderer="${this._boundControlRenderer}"
          ></vaadin-grid-column>
        </vaadin-grid>
        <backend-ai-list-status
          id="list-status"
          statusCondition="${this.listCondition}"
          message="${p("resourcePolicy.NoResourcePolicyToDisplay")}"
        ></backend-ai-list-status>
      </div>
      <backend-ai-dialog
        id="modify-policy-dialog"
        fixed
        backdrop
        blockscrolling
        narrowLayout
      >
        <span slot="title">${v("resourcePolicy.UpdateResourcePolicy")}</span>
        <div slot="content">
          <mwc-textfield
            id="id_new_policy_name"
            label="${v("resourcePolicy.PolicyName")}"
            disabled
          ></mwc-textfield>
          <h4>${v("resourcePolicy.ResourcePolicy")}</h4>
          <div class="horizontal justified layout distancing">
            <div class="vertical layout popup-right-margin">
              <mwc-textfield
                label="CPU"
                class="discrete resource-input"
                id="cpu-resource"
                type="number"
                min="0"
                max="512"
                @change="${e=>this._validateResourceInput(e)}"
              ></mwc-textfield>
              <mwc-formfield
                label="${v("resourcePolicy.Unlimited")}"
                class="unlimited"
              >
                <mwc-checkbox
                  @change="${e=>this._toggleCheckbox(e)}"
                ></mwc-checkbox>
              </mwc-formfield>
            </div>
            <div class="vertical layout popup-both-margin">
              <mwc-textfield
                label="RAM(GB)"
                class="resource-input"
                id="ram-resource"
                type="number"
                min="0"
                max="100000"
                step="0.01"
                @change="${e=>this._validateResourceInput(e)}"
              ></mwc-textfield>
              <mwc-formfield
                label="${v("resourcePolicy.Unlimited")}"
                class="unlimited"
              >
                <mwc-checkbox
                  @change="${e=>this._toggleCheckbox(e)}"
                ></mwc-checkbox>
              </mwc-formfield>
            </div>
            <div class="vertical layout popup-both-margin">
              <mwc-textfield
                label="GPU"
                class="discrete resource-input"
                id="gpu-resource"
                type="number"
                min="0"
                max="64"
                @change="${e=>this._validateResourceInput(e)}"
              ></mwc-textfield>
              <mwc-formfield
                label="${v("resourcePolicy.Unlimited")}"
                class="unlimited"
              >
                <mwc-checkbox
                  @change="${e=>this._toggleCheckbox(e)}"
                ></mwc-checkbox>
              </mwc-formfield>
            </div>
            <div class="vertical layout popup-left-margin">
              <mwc-textfield
                label="fGPU"
                class="resource-input"
                id="fgpu-resource"
                type="number"
                min="0"
                max="256"
                step="0.1"
                @change="${e=>this._validateResourceInput(e)}"
              ></mwc-textfield>
              <mwc-formfield
                label="${v("resourcePolicy.Unlimited")}"
                class="unlimited"
              >
                <mwc-checkbox
                  @change="${e=>this._toggleCheckbox(e)}"
                ></mwc-checkbox>
              </mwc-formfield>
            </div>
          </div>
          <h4>${v("resourcePolicy.Sessions")}</h4>
          <div class="horizontal layout justified distancing wrap">
            <div
              class="vertical left layout ${this.enableSessionLifetime?"sessions-section":""}"
            >
              <mwc-textfield
                label="${v("resourcePolicy.ContainerPerSession")}"
                class="discrete"
                id="container-per-session-limit"
                type="number"
                min="0"
                max="100"
                @change="${e=>this._validateResourceInput(e)}"
              ></mwc-textfield>
              <mwc-formfield
                label="${v("resourcePolicy.Unlimited")}"
                class="unlimited"
              >
                <mwc-checkbox
                  @change="${e=>this._toggleCheckbox(e)}"
                ></mwc-checkbox>
              </mwc-formfield>
            </div>
            <div
              class="vertical left layout ${this.enableSessionLifetime?"sessions-section":""}"
            >
              <mwc-textfield
                label="${v("resourcePolicy.IdleTimeoutSec")}"
                class="discrete"
                id="idle-timeout"
                type="number"
                min="0"
                max="15552000"
                @change="${e=>this._validateResourceInput(e)}"
              ></mwc-textfield>
              <mwc-formfield
                label="${v("resourcePolicy.Unlimited")}"
                class="unlimited"
              >
                <mwc-checkbox
                  @change="${e=>this._toggleCheckbox(e)}"
                ></mwc-checkbox>
              </mwc-formfield>
            </div>
            <div
              class="vertical left layout ${this.enableSessionLifetime?"sessions-section":""}"
            >
              <mwc-textfield
                label="${v("resourcePolicy.ConcurrentJobs")}"
                class="discrete"
                id="concurrency-limit"
                type="number"
                min="0"
                max="100"
                @change="${e=>this._validateResourceInput(e)}"
              ></mwc-textfield>
              <mwc-formfield
                label="${v("resourcePolicy.Unlimited")}"
                class="unlimited"
              >
                <mwc-checkbox
                  @change="${e=>this._toggleCheckbox(e)}"
                ></mwc-checkbox>
              </mwc-formfield>
            </div>
            <div
              class="vertical left layout ${this.enableSessionLifetime?"sessions-section":""}"
              style="${this.enableSessionLifetime?"":"display:none;"}"
            >
              <mwc-textfield
                label="${v("resourcePolicy.MaxSessionLifeTime")}"
                class="discrete"
                id="session-lifetime"
                type="number"
                min="0"
                max="100"
                @change="${e=>this._validateResourceInput(e)}"
              ></mwc-textfield>
              <mwc-formfield
                label="${v("resourcePolicy.Unlimited")}"
                class="unlimited"
              >
                <mwc-checkbox
                  @change="${e=>this._toggleCheckbox(e)}"
                ></mwc-checkbox>
              </mwc-formfield>
            </div>
          </div>
          <h4 style="margin-bottom:0px;">${v("resourcePolicy.Folders")}</h4>
          <div class="vertical center layout distancing" id="dropdown-area">
            <backend-ai-multi-select
              open-up
              id="allowed-vfolder-hosts"
              label="${v("resourcePolicy.AllowedHosts")}"
              style="width:100%;"
            ></backend-ai-multi-select>
            <div
              class="horizontal layout justified"
              style=${this.isSupportMaxVfolderCountInUserResourcePolicy?"display:none;":"width:100%;"}
            >
              <mwc-textfield
                label="${v("credential.Max#")}"
                class="discrete"
                id="vfolder-count-limit"
                type="number"
                min="0"
                max="50"
                @change="${e=>this._validateResourceInput(e)}"
              ></mwc-textfield>
            </div>
          </div>
        </div>
        <div
          slot="footer"
          class="horizontal end-justified flex layout distancing"
        >
          <mwc-button
            raised
            class="full"
            id="create-policy-button"
            icon="check"
            label="${v("button.Update")}"
            @click="${()=>this._modifyResourcePolicy()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog
        id="delete-policy-dialog"
        fixed
        backdrop
        blockscrolling
      >
        <span slot="title">${v("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${v("resourcePolicy.AboutToDeleteResourcePolicy")}</p>
          <p style="text-align:center;color:blue;">
            ${this.current_policy_name}
          </p>
          <p>
            ${v("dialog.warning.CannotBeUndone")}
            ${v("dialog.ask.DoYouWantToProceed")}
          </p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            class="operation"
            label="${v("button.Cancel")}"
            @click="${e=>this._hideDialog(e)}"
          ></mwc-button>
          <mwc-button
            unelevated
            class="operation"
            label="${v("button.Okay")}"
            @click="${()=>this._deleteResourcePolicy()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}_indexRenderer(e,i,t){const s=t.index+1;h(m`
        <div>${s}</div>
      `,e)}_displayResourcesByResourceUnit(e=0,i=!1,t=""){let s=0;const o=this._markIfUnlimited(e,i);switch(t=t.toLowerCase()){case"cpu":case"cuda_device":case"max_vfolder_count":s=0;break;case"mem":case"cuda_shares":s=1}return["∞","-"].includes(o)?o:Number(o).toFixed(s)}resourceRenderer(e,i,t){h(m`
        <div class="layout horizontal wrap center">
          <div class="layout horizontal configuration">
            <mwc-icon class="fg green indicator">developer_board</mwc-icon>
            <span>
              ${this._displayResourcesByResourceUnit(t.item.total_resource_slots.cpu,!1,"cpu")}
            </span>
            <span class="indicator">cores</span>
          </div>
          <div class="layout horizontal configuration">
            <mwc-icon class="fg green indicator">memory</mwc-icon>
            <span>
              ${this._displayResourcesByResourceUnit(t.item.total_resource_slots.mem,!1,"mem")}
            </span>
            <span class="indicator">GB</span>
          </div>
        </div>
        <div class="layout horizontal wrap center">
          ${t.item.total_resource_slots.cuda_device?m`
                <div class="layout horizontal configuration">
                  <mwc-icon class="fg green indicator">view_module</mwc-icon>
                  <span>
                    ${this._displayResourcesByResourceUnit(t.item.total_resource_slots.cuda_device,!1,"cuda_device")}
                  </span>
                  <span class="indicator">GPU</span>
                </div>
              `:m``}
          ${t.item.total_resource_slots.cuda_shares?m`
                <div class="layout horizontal configuration">
                  <mwc-icon class="fg green indicator">view_module</mwc-icon>
                  <span>
                    ${this._displayResourcesByResourceUnit(t.item.total_resource_slots.cuda_shares,!1,"cuda_shares")}
                  </span>
                  <span class="indicator">fGPU</span>
                </div>
              `:m``}
        </div>
        ${this.isSupportMaxVfolderCountInUserResourcePolicy?m``:m`
              <div class="layout horizontal wrap center">
                <div class="layout horizontal configuration">
                  <mwc-icon class="fg green indicator">folder</mwc-icon>
                  <span>
                    ${this._displayResourcesByResourceUnit(t.item.max_vfolder_count,!1,"max_vfolder_count")}
                  </span>
                  <span class="indicator">Folders</span>
                </div>
              </div>
            `}
      `,e)}concurrencyRenderer(e,i,t){h(m`
        <div>
          ${[0,k.getValue()].includes(t.item.max_concurrent_sessions)?"∞":t.item.max_concurrent_sessions}
        </div>
      `,e)}controlRenderer(e,i,t){h(m`
        <div
          id="controls"
          class="layout horizontal flex center"
          .policy-name="${t.item.name}"
        >
          <mwc-icon-button
            icon="settings"
            class="fg blue controls-running"
            ?disabled=${!this.is_super_admin}
            @click="${e=>this._launchResourcePolicyDialog(e)}"
          ></mwc-icon-button>
          <mwc-icon-button
            icon="delete"
            class="fg red controls-running"
            ?disabled=${!this.is_super_admin}
            @click="${e=>this._openDeleteResourcePolicyListDialog(e)}"
          ></mwc-icon-button>
        </div>
      `,e)}policyNameRenderer(e,i,t){h(m`
        <div class="layout horizontal center flex">
          <div>${t.item.name}</div>
        </div>
      `,e)}clusterSizeRenderer(e,i,t){h(m`
        <div>
          ${[0,k.getValue()].includes(t.item.max_containers_per_session)?"∞":t.item.max_containers_per_session}
        </div>
      `,e)}storageNodesRenderer(e,i,t){let s=JSON.parse(t.item.allowed_vfolder_hosts);this.enableParsingStoragePermissions&&(s=Object.keys(s)),h(m`
        <div class="layout horizontal center flex">
          <div class="vertical start layout around-justified">
            ${s.map((e=>m`
                <lablup-shields
                  app=""
                  color="darkgreen"
                  ui="round"
                  description="${e}"
                  style="margin-bottom:3px;"
                ></lablup-shields>
              `))}
          </div>
        </div>
      `,e)}firstUpdated(){this.notification=globalThis.lablupNotification,this.selectAreaHeight=this.dropdownArea.offsetHeight?this.dropdownArea.offsetHeight:"123px"}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.enableSessionLifetime=globalThis.backendaiclient.supports("session-lifetime"),this.enableParsingStoragePermissions=globalThis.backendaiclient.supports("fine-grained-storage-permissions"),this.isSupportMaxVfolderCountInUserResourcePolicy=globalThis.backendaiclient.supports("max-vfolder-count-in-user-resource-policy"),this.is_super_admin=globalThis.backendaiclient.is_superadmin,this._refreshPolicyData(),this.enableParsingStoragePermissions&&this._getVfolderPermissions()}),!0):(this.enableSessionLifetime=globalThis.backendaiclient.supports("session-lifetime"),this.enableParsingStoragePermissions=globalThis.backendaiclient.supports("fine-grained-storage-permissions"),this.isSupportMaxVfolderCountInUserResourcePolicy=globalThis.backendaiclient.supports("max-vfolder-count-in-user-resource-policy"),this.is_super_admin=globalThis.backendaiclient.is_superadmin,this._refreshPolicyData(),this.enableParsingStoragePermissions&&this._getVfolderPermissions()))}_getVfolderPermissions(){globalThis.backendaiclient.storageproxy.getAllPermissions().then((e=>{this.vfolderPermissions=e.vfolder_host_permission_list}))}_launchResourcePolicyDialog(e){this.updateCurrentPolicyToDialog(e),this._getAllStorageHostsInfo().then((()=>{this.allowedVfolderHostsSelect.items=this.all_vfolder_hosts,this.allowedVfolderHostsSelect.selectedItemList=this.allowed_vfolder_hosts,this.modifyPolicyDialog.show()})).catch((e=>{e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_openDeleteResourcePolicyListDialog(e){this.updateCurrentPolicyToDialog(e),this.deletePolicyDialog.show()}updateCurrentPolicyToDialog(e){const i=e.target.closest("#controls")["policy-name"],t=globalThis.backendaiclient.utils.gqlToObject(this.resourcePolicy,"name");this.resource_policy_names=Object.keys(t);const s=t[i];let o;o=this.enableParsingStoragePermissions?Object.keys(JSON.parse(s.allowed_vfolder_hosts)):s.allowed_vfolder_hosts,this.newPolicyName.value=i,this.current_policy_name=i,this.cpuResource.value=this._updateUnlimitedValue(s.total_resource_slots.cpu),this.ramResource.value=this._updateUnlimitedValue(s.total_resource_slots.mem),this.gpuResource.value=this._updateUnlimitedValue(s.total_resource_slots.cuda_device),this.fgpuResource.value=this._updateUnlimitedValue(s.total_resource_slots.cuda_shares),this.concurrencyLimit.value=this._updateUnlimitedValue(s.max_concurrent_sessions),this.idleTimeout.value=this._updateUnlimitedValue(s.idle_timeout),this.containerPerSessionLimit.value=this._updateUnlimitedValue(s.max_containers_per_session),this.enableSessionLifetime&&(this.sessionLifetime.value=this._updateUnlimitedValue(s.max_session_lifetime),this._updateInputStatus(this.sessionLifetime)),this._updateInputStatus(this.cpuResource),this._updateInputStatus(this.ramResource),this._updateInputStatus(this.gpuResource),this._updateInputStatus(this.fgpuResource),this._updateInputStatus(this.concurrencyLimit),this._updateInputStatus(this.idleTimeout),this._updateInputStatus(this.containerPerSessionLimit),this.vfolderCountLimitInput.value=s.max_vfolder_count,this.allowed_vfolder_hosts=o}_refreshPolicyData(){var e;return this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show(),globalThis.backendaiclient.resourcePolicy.get().then((e=>e.keypair_resource_policies)).then((e=>{var i;const t=e;Object.keys(t).map(((e,i)=>{const s=t[e];s.total_resource_slots=JSON.parse(s.total_resource_slots),"cpu"in s.total_resource_slots||"UNLIMITED"===s.default_for_unspecified&&(s.total_resource_slots.cpu="Unlimited"),"mem"in s.total_resource_slots?s.total_resource_slots.mem=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(s.total_resource_slots.mem,"g")):"UNLIMITED"===s.default_for_unspecified&&(s.total_resource_slots.mem="Unlimited"),"cuda.device"in s.total_resource_slots?0===s.total_resource_slots["cuda.device"]&&"UNLIMITED"===s.default_for_unspecified?s.total_resource_slots.cuda_device="Unlimited":s.total_resource_slots.cuda_device=s.total_resource_slots["cuda.device"]:"UNLIMITED"===s.default_for_unspecified&&(s.total_resource_slots.cuda_device="Unlimited"),"cuda.shares"in s.total_resource_slots?0===s.total_resource_slots["cuda.shares"]&&"UNLIMITED"===s.default_for_unspecified?s.total_resource_slots.cuda_shares="Unlimited":s.total_resource_slots.cuda_shares=s.total_resource_slots["cuda.shares"]:"UNLIMITED"===s.default_for_unspecified&&(s.total_resource_slots.cuda_shares="Unlimited")})),this.resourcePolicy=t,0==Object.keys(this.resourcePolicy).length?this.listCondition="no-data":null===(i=this._listStatus)||void 0===i||i.hide()})).catch((e=>{var i;null===(i=this._listStatus)||void 0===i||i.hide(),console.log(e),e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}refresh(){this._refreshPolicyData()}_isActive(){return"active"===this.condition}static bytesToGB(e,i=0){const t=Math.pow(10,i);return(Math.round(e/10**9*t)/t).toFixed(i)}static gBToBytes(e=0){return Math.round(10**9*e)}_parseSelectedAllowedVfolderHostWithPermissions(e){const i={};return e.forEach((e=>{Object.assign(i,{[e]:this.vfolderPermissions})})),i}_readResourcePolicyInput(){const e={};let i;i=this.enableParsingStoragePermissions?JSON.stringify(this._parseSelectedAllowedVfolderHostWithPermissions(this.allowedVfolderHostsSelect.selectedItemList)):this.allowedVfolderHostsSelect.selectedItemList,this._validateUserInput(this.cpuResource),this._validateUserInput(this.ramResource),this._validateUserInput(this.gpuResource),this._validateUserInput(this.fgpuResource),this._validateUserInput(this.concurrencyLimit),this._validateUserInput(this.idleTimeout),this._validateUserInput(this.containerPerSessionLimit),this._validateUserInput(this.vfolderCountLimitInput),e.cpu=this.cpuResource.value,e.mem=this.ramResource.value+"g",e["cuda.device"]=parseInt(this.gpuResource.value),e["cuda.shares"]=parseFloat(this.fgpuResource.value),this.concurrencyLimit.value=["",0].includes(this.concurrencyLimit.value)?k.getValue().toString():this.concurrencyLimit.value,this.idleTimeout.value=""===this.idleTimeout.value?"0":this.idleTimeout.value,this.containerPerSessionLimit.value=["",0].includes(this.containerPerSessionLimit.value)?k.getValue().toString():this.containerPerSessionLimit.value,this.vfolderCountLimitInput.value=""===this.vfolderCountLimitInput.value?"0":this.vfolderCountLimitInput.value,Object.keys(e).map((i=>{isNaN(parseFloat(e[i]))&&delete e[i]}));const t={default_for_unspecified:"UNLIMITED",total_resource_slots:JSON.stringify(e),max_concurrent_sessions:parseInt(this.concurrencyLimit.value),max_containers_per_session:parseInt(this.containerPerSessionLimit.value),idle_timeout:this.idleTimeout.value,max_vfolder_count:0,allowed_vfolder_hosts:i};return this.isSupportMaxVfolderCountInUserResourcePolicy||(t.max_vfolder_count=parseInt(this.vfolderCountLimitInput.value)),this.enableSessionLifetime&&(this._validateUserInput(this.sessionLifetime),this.sessionLifetime.value=""===this.sessionLifetime.value?"0":this.sessionLifetime.value,t.max_session_lifetime=parseInt(this.sessionLifetime.value)),t}_modifyResourcePolicy(){try{const e=this._readResourcePolicyInput();globalThis.backendaiclient.resourcePolicy.mutate(this.current_policy_name,e).then((({modify_keypair_resource_policy:e})=>{e.ok?(this.modifyPolicyDialog.hide(),this.notification.text=p("resourcePolicy.SuccessfullyUpdated"),this.notification.show(),this.refresh()):e.msg&&(this.modifyPolicyDialog.hide(),this.notification.text=u.relieve(e.msg),this.notification.show(),this.refresh())})).catch((e=>{console.log(e),e&&e.message&&(this.modifyPolicyDialog.hide(),this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}catch(e){this.notification.text=e.message,this.notification.show()}}_deleteResourcePolicy(){const e=this.current_policy_name;globalThis.backendaiclient.resourcePolicy.delete(e).then((({delete_keypair_resource_policy:e})=>{e.ok?(this.deletePolicyDialog.hide(),this.notification.text=p("resourcePolicy.SuccessfullyDeleted"),this.notification.show(),this.refresh()):e.msg&&(this.deletePolicyDialog.hide(),this.notification.text=u.relieve(e.msg),this.notification.show(),this.refresh())})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_toggleCheckbox(e){var i;const t=e.target,s=t.checked,o=t.closest("div").querySelector("mwc-textfield");o.disabled=s,o.disabled||""===o.value&&(o.value=null!==(i=o.min)&&void 0!==i?i:0)}_validateResourceInput(e){const i=e.target.closest("mwc-textfield"),t=i.closest("div").querySelector("mwc-formfield.unlimited"),s=t?t.querySelector("mwc-checkbox"):null;if(i.classList.contains("discrete")&&(i.value=Math.round(i.value)),i.value<=0&&(i.value="concurrency-limit"===i.id||"container-per-session-limit"===i.id?1:0),!i.valid){const e=i.step?(o=i.step)%1?o.toString().split(".")[1].length:0:0;i.value=e>0?Math.min(i.value,i.value<0?i.min:i.max).toFixed(e):Math.min(Math.round(i.value),i.value<0?i.min:i.max)}var o;s&&(i.disabled=s.checked=i.value==parseFloat(i.min))}_updateUnlimitedValue(e){return["-",0,"0","Unlimited",1/0,"Infinity",k.getValue()].includes(e)?"":e}_validateUserInput(e){if(e.disabled)e.value="";else if(""===e.value)throw new Error(p("resourcePolicy.CannotCreateResourcePolicy"))}_updateInputStatus(e){const i=e,t=i.closest("div").querySelector("mwc-checkbox");""===i.value||0===i.value||["concurrency-limit","container-per-session-limit"].includes(i.id)&&i.value===k.getValue()?(i.disabled=!0,t.checked=!0):(i.disabled=!1,t.checked=!1)}_markIfUnlimited(e,i=!1){return["-",0,"0","Unlimited",1/0,"Infinity"].includes(e)?"∞":["NaN",NaN].includes(e)?"-":i?x.bytesToGB(e,1):e}_getAllStorageHostsInfo(){return globalThis.backendaiclient.vfolder.list_all_hosts().then((e=>{this.all_vfolder_hosts=e.allowed})).catch((e=>{throw e}))}};e([i({type:Boolean})],$.prototype,"visible",void 0),e([i({type:String})],$.prototype,"listCondition",void 0),e([i({type:Object})],$.prototype,"keypairs",void 0),e([i({type:Array})],$.prototype,"resourcePolicy",void 0),e([i({type:Object})],$.prototype,"keypairInfo",void 0),e([i({type:Boolean,reflect:!0})],$.prototype,"active",void 0),e([i({type:String})],$.prototype,"condition",void 0),e([i({type:Array})],$.prototype,"resource_policy_names",void 0),e([i({type:String})],$.prototype,"current_policy_name",void 0),e([i({type:Number})],$.prototype,"selectAreaHeight",void 0),e([i({type:Boolean})],$.prototype,"enableSessionLifetime",void 0),e([i({type:Boolean})],$.prototype,"enableParsingStoragePermissions",void 0),e([i({type:Object})],$.prototype,"_boundResourceRenderer",void 0),e([i({type:Object})],$.prototype,"_boundConcurrencyRenderer",void 0),e([i({type:Object})],$.prototype,"_boundControlRenderer",void 0),e([i({type:Object})],$.prototype,"_boundPolicyNameRenderer",void 0),e([i({type:Object})],$.prototype,"_boundClusterSizeRenderer",void 0),e([i({type:Object})],$.prototype,"_boundStorageNodesRenderer",void 0),e([t("#dropdown-area")],$.prototype,"dropdownArea",void 0),e([t("#vfolder-count-limit")],$.prototype,"vfolderCountLimitInput",void 0),e([t("#cpu-resource")],$.prototype,"cpuResource",void 0),e([t("#ram-resource")],$.prototype,"ramResource",void 0),e([t("#gpu-resource")],$.prototype,"gpuResource",void 0),e([t("#fgpu-resource")],$.prototype,"fgpuResource",void 0),e([t("#concurrency-limit")],$.prototype,"concurrencyLimit",void 0),e([t("#idle-timeout")],$.prototype,"idleTimeout",void 0),e([t("#container-per-session-limit")],$.prototype,"containerPerSessionLimit",void 0),e([t("#session-lifetime")],$.prototype,"sessionLifetime",void 0),e([t("#delete-policy-dialog")],$.prototype,"deletePolicyDialog",void 0),e([t("#modify-policy-dialog")],$.prototype,"modifyPolicyDialog",void 0),e([t("#allowed-vfolder-hosts")],$.prototype,"allowedVfolderHostsSelect",void 0),e([t("#id_new_policy_name")],$.prototype,"newPolicyName",void 0),e([t("#list-status")],$.prototype,"_listStatus",void 0),e([y()],$.prototype,"all_vfolder_hosts",void 0),e([y()],$.prototype,"allowed_vfolder_hosts",void 0),e([y()],$.prototype,"is_super_admin",void 0),e([y()],$.prototype,"vfolderPermissions",void 0),e([y()],$.prototype,"isSupportMaxVfolderCountInUserResourcePolicy",void 0),$=x=e([s("backend-ai-resource-policy-list")],$);let P=class extends o{constructor(){super(),this.isAdmin=!1,this.editMode=!1,this.users=[],this.userInfo=Object(),this.userInfoGroups=[],this.userEmail="",this.openUserInfoModal=!1,this.openUserSettingModal=!1,this.condition="",this._boundControlRenderer=this.controlRenderer.bind(this),this._userIdRenderer=this.userIdRenderer.bind(this),this._userNameRenderer=this.userNameRenderer.bind(this),this._userStatusRenderer=this.userStatusRenderer.bind(this),this._totpActivatedRenderer=this.totpActivatedRenderer.bind(this),this.signoutUserName="",this.notification=Object(),this.listCondition="loading",this._totalUserCount=0,this.isUserInfoMaskEnabled=!1,this.totpSupported=!1,this.totpActivated=!1,this.supportMainAccessKey=!1,this.userStatus={active:"Active",inactive:"Inactive","before-verification":"Before Verification",deleted:"Deleted"}}static get styles(){return[a,r,l,n,c,d`
        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 229px);
        }

        backend-ai-dialog h4 {
          font-size: 14px;
          padding: 5px 15px 5px 12px;
          margin: 0 0 10px 0;
          display: block;
          height: 20px;
          border-bottom: 1px solid #ddd;
        }

        vaadin-item {
          font-size: 13px;
          font-weight: 100;
        }

        div.indicator,
        span.indicator {
          font-size: 9px;
          margin-right: 5px;
        }

        div.configuration {
          width: 70px !important;
        }

        div.password-area {
          width: 100%;
          max-width: 322px;
        }

        mwc-textfield.display-textfield {
          --mdc-text-field-disabled-ink-color: var(--token-colorText);
        }

        backend-ai-dialog li {
          font-family: var(--token-fontFamily);
          font-size: 16px;
        }

        mwc-button,
        mwc-button[unelevated],
        mwc-button[outlined] {
          background-image: none;
          --mdc-theme-primary: var(--general-button-background-color);
          --mdc-theme-on-primary: var(--general-button-color);
          --mdc-typography-font-family: var(--token-fontFamily);
        }

        mwc-select.full-width {
          width: 100%;
          /* Need to be set when fixedMenuPosition attribute is enabled */
          --mdc-menu-max-width: 330px;
          --mdc-menu-min-width: 330px;
        }

        mwc-textfield,
        mwc-textarea {
          width: 100%;
          --mdc-typography-font-family: var(--token-fontFamily);
          --mdc-typography-textfield-font-size: 14px;
          --mdc-typography-textarea-font-size: 14px;
          --mdc-text-field-fill-color: transparent;
          --mdc-theme-primary: var(--general-textfield-selected-color);
        }

        p.label {
          font-size: 16px;
          font-family: var(--token-fontFamily);
          color: var(--general-sidebar-color);
          width: 270px;
        }

        mwc-icon.totp {
          --mdc-icon-size: 24px;
        }
      `]}firstUpdated(){this.notification=globalThis.lablupNotification,this.addEventListener("user-list-updated",(()=>{this.refresh()}))}async _viewStateChanged(e){var i,t,s;await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(async()=>{var e,i,t;this.totpSupported=(null===(e=globalThis.backendaiclient)||void 0===e?void 0:e.supports("2FA"))&&await(null===(i=globalThis.backendaiclient)||void 0===i?void 0:i.isManagerSupportingTOTP()),this.supportMainAccessKey=null===(t=globalThis.backendaiclient)||void 0===t?void 0:t.supports("main-access-key"),this._refreshUserData(),this.isAdmin=globalThis.backendaiclient.is_admin,this.isUserInfoMaskEnabled=globalThis.backendaiclient._config.maskUserInfo}),!0):(this.totpSupported=(null===(i=globalThis.backendaiclient)||void 0===i?void 0:i.supports("2FA"))&&await(null===(t=globalThis.backendaiclient)||void 0===t?void 0:t.isManagerSupportingTOTP()),this.supportMainAccessKey=null===(s=globalThis.backendaiclient)||void 0===s?void 0:s.supports("main-access-key"),this._refreshUserData(),this.isAdmin=globalThis.backendaiclient.is_admin,this.isUserInfoMaskEnabled=globalThis.backendaiclient._config.maskUserInfo))}_refreshUserData(){var e;let i=!0;if("active"===this.condition)i=!0;else i=!1;this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show();const t=["email","username","need_password_change","full_name","description","is_active","domain_name","role","groups {id name}","status","main_access_key"];return this.totpSupported&&t.push("totp_activated"),globalThis.backendaiclient.user.list(i,t).then((e=>{var i;const t=e.users;this.users=t,0==this.users.length?this.listCondition="no-data":null===(i=this._listStatus)||void 0===i||i.hide()})).catch((e=>{var i;null===(i=this._listStatus)||void 0===i||i.hide(),console.log(e),e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}async _openUserSettingModal(e){const i=e.target.closest("#controls");this.userEmail=i["user-id"],this.openUserSettingModal=!0}async _openUserInfoModal(e){const i=e.target.closest("#controls");this.userEmail=i["user-id"],this.openUserInfoModal=!0}_signoutUserDialog(e){const i=e.target.closest("#controls")["user-id"];this.signoutUserName=i,this.signoutUserDialog.show()}_signoutUser(){globalThis.backendaiclient.user.delete(this.signoutUserName).then((e=>{this.notification.text=p("credential.SignoutSeccessfullyFinished"),this.notification.show(),this._refreshUserData(),this.signoutUserDialog.hide()})).catch((e=>{console.log(e),void 0!==e.message?(this.notification.text=u.relieve(e.title),this.notification.detail=e.message):this.notification.text=u.relieve("Signout failed. Check your permission and try again."),this.notification.show()}))}async _getUserData(e){const i=["email","username","need_password_change","full_name","description","status","domain_name","role","groups {id name}","main_access_key"];return this.totpSupported&&i.push("totp_activated"),globalThis.backendaiclient.user.get(e,i)}refresh(){this._refreshUserData(),this.userGrid.clearCache()}_isActive(){return"active"===this.condition}_elapsed(e,i){const t=new Date(e);let s;s=(this.condition,new Date);const o=Math.floor((s.getTime()-t.getTime())/1e3);return Math.floor(o/86400)}_humanReadableTime(e){return new Date(e).toUTCString()}_markIfUnlimited(e){return["-",0,"Unlimited",1/0,"Infinity"].includes(e)?"∞":e}_getUserId(e=""){if(e&&this.isUserInfoMaskEnabled){const i=2,t=e.split("@")[0].length-i;e=globalThis.backendaiutils._maskString(e,"*",i,t)}return e}_getUsername(e=""){if(e&&this.isUserInfoMaskEnabled){const i=2,t=e.length-i;e=globalThis.backendaiutils._maskString(e,"*",i,t)}return e}async _setTotpActivated(){if(this.totpSupported){const e=await globalThis.backendaiclient.user.get(globalThis.backendaiclient.email,["totp_activated"]);this.totpActivated=e.user.totp_activated}}_indexRenderer(e,i,t){const s=t.index+1;h(m`
        <div>${s}</div>
      `,e)}controlRenderer(e,i,t){h(m`
        <div
          id="controls"
          class="layout horizontal flex center"
          .user-id="${t.item.email}"
        >
          <mwc-icon-button
            class="fg green"
            icon="assignment"
            @click="${e=>this._openUserInfoModal(e)}"
          ></mwc-icon-button>
          <mwc-icon-button
            class="fg blue"
            icon="settings"
            @click="${e=>this._openUserSettingModal(e)}"
          ></mwc-icon-button>
          ${globalThis.backendaiclient.is_superadmin&&this._isActive()?m`
                <mwc-icon-button
                  class="fg red controls-running"
                  icon="delete_forever"
                  @click="${e=>this._signoutUserDialog(e)}"
                ></mwc-icon-button>
              `:m``}
        </div>
      `,e)}userIdRenderer(e,i,t){h(m`
        <span>${this._getUserId(t.item.email)}</span>
      `,e)}userNameRenderer(e,i,t){h(m`
        <span>${this._getUsername(t.item.username)}</span>
      `,e)}userStatusRenderer(e,i,t){const s="active"===t.item.status?"green":"lightgrey";h(m`
        <lablup-shields
          app=""
          color="${s}"
          description="${t.item.status}"
          ui="flat"
        ></lablup-shields>
      `,e)}totpActivatedRenderer(e,i,t){var s;h(m`
        <div class="layout horizontal center center-justified wrap">
          ${(null===(s=t.item)||void 0===s?void 0:s.totp_activated)?m`
                <mwc-icon class="fg green totp">check_circle</mwc-icon>
              `:m`
                <mwc-icon class="fg red totp">block</mwc-icon>
              `}
        </div>
      `,e)}render(){return m`
      <link rel="stylesheet" href="resources/custom.css" />
      <lablup-loading-spinner id="loading-spinner"></lablup-loading-spinner>
      <div class="list-wrapper">
        <vaadin-grid
          theme="row-stripes column-borders compact dark"
          aria-label="User list"
          id="user-grid"
          .items="${this.users}"
        >
          <vaadin-grid-column
            width="40px"
            flex-grow="0"
            header="#"
            text-align="center"
            .renderer="${this._indexRenderer.bind(this)}"
          ></vaadin-grid-column>
          <lablup-grid-sort-filter-column
            auto-width
            path="email"
            header="${v("credential.UserID")}"
            resizable
            .renderer="${this._userIdRenderer.bind(this)}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            auto-width
            path="username"
            header="${v("credential.Name")}"
            resizable
            .renderer="${this._userNameRenderer}"
          ></lablup-grid-sort-filter-column>
          ${this.totpSupported?m`
                <vaadin-grid-sort-column
                  auto-width
                  flex-grow="0"
                  path="totp_activated"
                  header="${v("webui.menu.TotpActivated")}"
                  resizable
                  .renderer="${this._totpActivatedRenderer.bind(this)}"
                ></vaadin-grid-sort-column>
              `:m``}
          ${"active"!==this.condition?m`
                <lablup-grid-sort-filter-column
                  auto-width
                  path="status"
                  header="${v("credential.Status")}"
                  resizable
                  .renderer="${this._userStatusRenderer}"
                ></lablup-grid-sort-filter-column>
              `:m``}
          ${this.supportMainAccessKey?m`
                <vaadin-grid-filter-column
                  auto-width
                  path="main_access_key"
                  resizable
                  header="${v("credential.MainAccessKey")}"
                ></vaadin-grid-filter-column>
              `:m``}
          <vaadin-grid-column
            frozen-to-end
            width="160px"
            resizable
            header="${v("general.Control")}"
            .renderer="${this._boundControlRenderer}"
          ></vaadin-grid-column>
        </vaadin-grid>
        <backend-ai-list-status
          id="list-status"
          statusCondition="${this.listCondition}"
          message="${p("credential.NoUserToDisplay")}"
        ></backend-ai-list-status>
      </div>
      <backend-ai-dialog id="signout-user-dialog" fixed backdrop>
        <span slot="title">${v("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>
            You are inactivating the user
            <span style="color:red">${this.signoutUserName}</span>
            .
          </p>
          <p>${v("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            label="${v("button.Cancel")}"
            @click="${e=>this._hideDialog(e)}"
          ></mwc-button>
          <mwc-button
            unelevated
            label="${v("button.Okay")}"
            @click="${()=>this._signoutUser()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      ${this.openUserInfoModal?m`
            <backend-ai-react-user-info-dialog
              value="${JSON.stringify({open:this.openUserInfoModal,userEmail:this.userEmail})}"
              @cancel="${()=>this.openUserInfoModal=!1}"
            ></backend-ai-react-user-info-dialog>
          `:m``}
      ${this.openUserSettingModal?m`
            <backend-ai-react-user-setting-dialog
              value="${JSON.stringify({open:this.openUserSettingModal,userEmail:this.userEmail})}"
              @ok="${()=>{this.openUserSettingModal=!1,this.refresh()}}"
              @cancel="${()=>this.openUserSettingModal=!1}"
            ></backend-ai-react-user-setting-dialog>
          `:m``}
    `}};e([i({type:Boolean})],P.prototype,"isAdmin",void 0),e([i({type:Boolean})],P.prototype,"editMode",void 0),e([i({type:Array})],P.prototype,"users",void 0),e([i({type:Object})],P.prototype,"userInfo",void 0),e([i({type:Array})],P.prototype,"userInfoGroups",void 0),e([i({type:String})],P.prototype,"userEmail",void 0),e([i({type:Boolean})],P.prototype,"openUserInfoModal",void 0),e([i({type:Boolean})],P.prototype,"openUserSettingModal",void 0),e([i({type:String})],P.prototype,"condition",void 0),e([i({type:Object})],P.prototype,"_boundControlRenderer",void 0),e([i({type:Object})],P.prototype,"_userIdRenderer",void 0),e([i({type:Object})],P.prototype,"_userNameRenderer",void 0),e([i({type:Object})],P.prototype,"_userStatusRenderer",void 0),e([i({type:Object})],P.prototype,"_totpActivatedRenderer",void 0),e([i({type:Object})],P.prototype,"keypairs",void 0),e([i({type:String})],P.prototype,"signoutUserName",void 0),e([i({type:Object})],P.prototype,"notification",void 0),e([i({type:String})],P.prototype,"listCondition",void 0),e([i({type:Number})],P.prototype,"_totalUserCount",void 0),e([i({type:Boolean})],P.prototype,"isUserInfoMaskEnabled",void 0),e([i({type:Boolean})],P.prototype,"totpSupported",void 0),e([i({type:Boolean})],P.prototype,"totpActivated",void 0),e([i({type:Boolean})],P.prototype,"supportMainAccessKey",void 0),e([i({type:Object})],P.prototype,"userStatus",void 0),e([t("#user-grid")],P.prototype,"userGrid",void 0),e([t("#loading-spinner")],P.prototype,"spinner",void 0),e([t("#list-status")],P.prototype,"_listStatus",void 0),e([t("#password")],P.prototype,"passwordInput",void 0),e([t("#confirm")],P.prototype,"confirmInput",void 0),e([t("#username")],P.prototype,"usernameInput",void 0),e([t("#full_name")],P.prototype,"fullNameInput",void 0),e([t("#description")],P.prototype,"descriptionInput",void 0),e([t("#status")],P.prototype,"statusSelect",void 0),e([t("#signout-user-dialog")],P.prototype,"signoutUserDialog",void 0),P=e([s("backend-ai-user-list")],P);let I=class extends o{constructor(){super(),this.concurrency_limit={},this.idle_timeout={},this.session_lifetime={},this.container_per_session_limit={},this.vfolder_max_limit={},this.rate_metric=[1e3,2e3,3e3,4e3,5e3,1e4,5e4],this.resource_policies=Object(),this.isAdmin=!1,this.isSuperAdmin=!1,this._status="inactive",this.new_access_key="",this.new_secret_key="",this._activeTab="users",this.notification=Object(),this._defaultFileName="",this.enableSessionLifetime=!1,this.enableParsingStoragePermissions=!1,this.activeUserInnerTab="active",this.activeCredentialInnerTab="active",this.default_vfolder_host="",this.isSupportMaxVfolderCountInUserResourcePolicy=!1,this.all_vfolder_hosts=[],this.resource_policy_names=[]}static get styles(){return[a,r,l,n,c,d`
        #new-keypair-dialog {
          min-width: 350px;
          height: 100%;
        }

        div.card > h4 {
          margin-bottom: 0px;
          background-color: var(--token-colorBgContainer);
        }

        div.card h3 {
          padding-top: 0;
          padding-right: 15px;
          padding-bottom: 0;
        }

        div.card div.card {
          margin: 0;
          padding: 0;
          --card-elevation: 0;
        }

        div.sessions-section {
          width: 167px;
          margin-bottom: 10px;
        }

        #user-lists > h4,
        #credential-lists > h4 {
          padding-top: 0 !important;
          padding-bottom: 0 !important;
        }

        mwc-tab-bar.sub-bar mwc-tab {
          --mdc-tab-height: 46px;
          --mdc-text-transform: none;
        }

        mwc-list-item {
          height: auto;
          font-size: 12px;
          --mdc-theme-primary: var(--general-sidebar-color);
        }

        mwc-checkbox {
          margin-left: 0;
          --mdc-icon-size: 14px;
          --mdc-checkbox-ripple-size: 20px;
          --mdc-checkbox-state-layer-size: 14px;
        }

        mwc-formfield {
          font-size: 8px;
          --mdc-typography-body2-font-size: 10px;
        }

        mwc-textfield {
          width: 100%;
          --mdc-text-field-fill-color: transparent;
          --mdc-theme-primary: var(--general-textfield-selected-color);
          --mdc-typography-font-family: var(--token-fontFamily);
        }

        mwc-textfield.resource-input {
          width: 5rem;
        }

        mwc-textfield#export-file-name {
          margin-bottom: 10px;
        }

        mwc-textfield#id_user_name {
          margin-bottom: 18px;
        }

        mwc-menu {
          --mdc-menu-item-height: auto;
        }

        mwc-menu#dropdown-menu {
          position: relative;
          left: -10px;
          top: 50px;
        }

        mwc-icon-button {
          --mdc-icon-size: 20px;
          color: var(--paper-grey-700);
        }

        mwc-icon-button#dropdown-menu-button {
          margin-left: 10px;
        }

        backend-ai-dialog {
          --component-min-width: 350px;
          --component-max-width: 390px;
        }

        backend-ai-dialog h4 {
          font-size: 14px;
          padding: 5px 15px 5px 12px;
          margin: 0 0 10px 0;
          display: block;
          height: 20px;
          border-bottom: 1px solid #ddd;
        }

        div.popup-right-margin {
          margin-right: 5px;
        }
        div.popup-left-margin {
          margin-left: 5px;
        }
        div.popup-both-margin {
          margin-left: 5px;
          margin-right: 5px;
        }

        @media screen and (max-width: 805px) {
          mwc-tab,
          mwc-button {
            --mdc-typography-button-font-size: 10px;
          }
        }
      `]}firstUpdated(){this.notification=globalThis.lablupNotification,document.addEventListener("backend-ai-credential-refresh",(()=>{this.activeCredentialList.refresh(),this.inactiveCredentialList.refresh()}),!0),this._addInputValidator(this.userIdInput),this.selectAreaHeight=this.dropdownArea.offsetHeight?this.dropdownArea.offsetHeight:"123px"}async _preparePage(){!0!==globalThis.backendaiclient.is_admin?this.disablePage():(this.isAdmin=!0,!0===globalThis.backendaiclient.is_superadmin&&(this.isSuperAdmin=!0)),this._activeTab="user-lists",this._addValidatorToPolicyInput(),this._getResourceInfo(),this._getResourcePolicies(),this._updateInputStatus(this.cpu_resource),this._updateInputStatus(this.ram_resource),this._updateInputStatus(this.gpu_resource),this._updateInputStatus(this.fgpu_resource),this._updateInputStatus(this.concurrency_limit),this._updateInputStatus(this.idle_timeout),this._updateInputStatus(this.container_per_session_limit),this.enableSessionLifetime&&this._updateInputStatus(this.session_lifetime),this.vfolder_max_limit.value=10,this._defaultFileName=this._getDefaultCSVFileName(),await this._runAction()}async _viewStateChanged(e){if(await this.updateComplete,!1===e)return this.resourcePolicyList.active=!1,this.activeUserList.active=!1,void(this._status="inactive");this.resourcePolicyList.active=!0,this.activeUserList.active=!0,this._status="active",void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.enableSessionLifetime=globalThis.backendaiclient.supports("session-lifetime"),this.enableParsingStoragePermissions=globalThis.backendaiclient.supports("fine-grained-storage-permissions"),this.isSupportMaxVfolderCountInUserResourcePolicy=globalThis.backendaiclient.supports("max-vfolder-count-in-user-resource-policy"),this._preparePage(),this.enableParsingStoragePermissions&&this._getVfolderPermissions()})):(this.enableSessionLifetime=globalThis.backendaiclient.supports("session-lifetime"),this.enableParsingStoragePermissions=globalThis.backendaiclient.supports("fine-grained-storage-permissions"),this.isSupportMaxVfolderCountInUserResourcePolicy=globalThis.backendaiclient.supports("max-vfolder-count-in-user-resource-policy"),this._preparePage(),this.enableParsingStoragePermissions&&this._getVfolderPermissions())}_getVfolderPermissions(){globalThis.backendaiclient.storageproxy.getAllPermissions().then((e=>{this.vfolderPermissions=e.vfolder_host_permission_list}))}_parseSelectedAllowedVfolderHostWithPermissions(e){const i={};return e.forEach((e=>{Object.assign(i,{[e]:this.vfolderPermissions})})),i}async _launchKeyPairDialog(){await this._getResourcePolicies(),this.newKeypairDialog.show(),this.userIdInput.value=""}_getAllStorageHostsInfo(){return globalThis.backendaiclient.vfolder.list_all_hosts().then((e=>{this.all_vfolder_hosts=e.allowed,this.default_vfolder_host=e.default})).catch((e=>{throw e}))}_launchResourcePolicyDialog(){Promise.allSettled([this._getAllStorageHostsInfo(),this._getResourcePolicies()]).then((e=>{this.newPolicyNameInput.mdcFoundation.setValid(!0),this.newPolicyNameInput.isUiValid=!0,this.newPolicyNameInput.value="",this.allowedVfolderHostsSelect.items=this.all_vfolder_hosts,this.allowedVfolderHostsSelect.selectedItemList=[this.default_vfolder_host],this.newPolicyDialog.show()})).catch((e=>{e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_launchUserAddDialog(){this.newUserDialog.show()}async _getResourcePolicies(){const e=["name","default_for_unspecified","total_resource_slots","max_concurrent_sessions","max_containers_per_session"];return this.enableSessionLifetime&&e.push("max_session_lifetime"),globalThis.backendaiclient.resourcePolicy.get(null,e).then((e=>{const i=globalThis.backendaiclient.utils.gqlToObject(e.keypair_resource_policies,"name"),t=globalThis.backendaiclient.utils.gqlToList(e.keypair_resource_policies,"name");this.resource_policies=i,this.resource_policy_names=t,this.resourcePolicy.layout(!0).then((()=>{this.resourcePolicy.select(0)})),this.rateLimit.layout(!0).then((()=>{this.rateLimit.select(0)}))}))}_addKeyPair(){let e="";if(!this.userIdInput.checkValidity())return;e=this.userIdInput.value;const i=this.resourcePolicy.value,t=parseInt(this.rateLimit.value);globalThis.backendaiclient.keypair.add(e,!0,!1,i,t).then((e=>{if(e.create_keypair.ok)this.newKeypairDialog.hide(),this.notification.text=p("credential.KeypairCreated"),this.notification.show(),this.activeCredentialList.refresh();else if(e.create_keypair.msg){const i=e.create_keypair.msg.split(":")[1];this.notification.text=p("credential.UserNotFound")+i,this.notification.show()}else this.notification.text=p("dialog.ErrorOccurred"),this.notification.show()})).catch((e=>{console.log(e),e&&e.message&&(this.newKeypairDialog.hide(),this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_readResourcePolicyInput(){const e={};let i;i=this.enableParsingStoragePermissions?JSON.stringify(this._parseSelectedAllowedVfolderHostWithPermissions(this.allowedVfolderHostsSelect.selectedItemList)):this.allowedVfolderHostsSelect.selectedItemList,this._validateUserInput(this.cpu_resource),this._validateUserInput(this.ram_resource),this._validateUserInput(this.gpu_resource),this._validateUserInput(this.fgpu_resource),this._validateUserInput(this.concurrency_limit),this._validateUserInput(this.idle_timeout),this._validateUserInput(this.container_per_session_limit),this._validateUserInput(this.vfolder_max_limit),e.cpu=this.cpu_resource.value,e.mem=this.ram_resource.value+"g",e["cuda.device"]=parseInt(this.gpu_resource.value),e["cuda.shares"]=parseFloat(this.fgpu_resource.value),this.concurrency_limit.value=""===this.concurrency_limit.value?0:parseInt(this.concurrency_limit.value),this.idle_timeout.value=""===this.idle_timeout.value?0:parseInt(this.idle_timeout.value),this.container_per_session_limit.value=""===this.container_per_session_limit.value?0:parseInt(this.container_per_session_limit.value),Object.keys(e).map((i=>{isNaN(parseFloat(e[i]))&&delete e[i]})),this.vfolder_max_limit.value=""===this.vfolder_max_limit.value?0:parseInt(this.vfolder_max_limit.value);const t={default_for_unspecified:"UNLIMITED",total_resource_slots:JSON.stringify(e),max_concurrent_sessions:this.concurrency_limit.value,max_containers_per_session:this.container_per_session_limit.value,idle_timeout:this.idle_timeout.value,max_vfolder_count:this.vfolder_max_limit.value,max_vfolder_size:-1,allowed_vfolder_hosts:i};return this.enableSessionLifetime&&(this._validateUserInput(this.session_lifetime),this.session_lifetime.value=""===this.session_lifetime.value?0:parseInt(this.session_lifetime.value),t.max_session_lifetime=this.session_lifetime.value),t}_addResourcePolicy(){if(this.newPolicyNameInput.checkValidity())try{this.newPolicyNameInput.checkValidity();const e=this.newPolicyNameInput.value;if(""===e)throw new Error(p("resourcePolicy.PolicyNameEmpty"));const i=this._readResourcePolicyInput();globalThis.backendaiclient.resourcePolicy.add(e,i).then((e=>{this.newPolicyDialog.hide(),this.notification.text=p("resourcePolicy.SuccessfullyCreated"),this.notification.show(),this.resourcePolicyList.refresh()})).catch((e=>{console.log(e),e&&e.message&&(this.newPolicyDialog.hide(),this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}catch(e){this.notification.text=e.message,this.notification.show()}else this.newPolicyNameInput.reportValidity()}_addUser(){const e=this.userEmailInput.value,i=""!==this.userNameInput.value?this.userNameInput.value:e.split("@")[0],t=this.userPasswordInput.value;if(!this.userEmailInput.checkValidity()||!this.userPasswordInput.checkValidity()||!this.userPasswordConfirmInput.checkValidity())return;const s={username:i,password:t,need_password_change:!1,full_name:i,description:`${i}'s Account`,is_active:!0,domain_name:"default",role:"user"};globalThis.backendaiclient.group.list().then((i=>{const t=i.groups.find((e=>"default"===e.name)).id;return Promise.resolve(globalThis.backendaiclient.user.create(e,{...s,group_ids:[t]}))})).then((e=>{this.newUserDialog.hide(),e.create_user.ok?(this.notification.text=p("credential.UserAccountCreated"),this.activeUserList.refresh()):this.notification.text=p("credential.UserAccountCreatedError"),this.notification.show(),this.userEmailInput.value="",this.userNameInput.value="",this.userPasswordInput.value="",this.userPasswordConfirmInput.value=""}))}disablePage(){var e;const i=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll(".admin");for(let e=0;e<i.length;e++)i[e].style.display="none"}_showTab(e){var i,t,s,o;const a=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelectorAll(".tab-content");for(let e=0;e<a.length;e++)a[e].style.display="none";this._activeTab=e.title,(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e.title)).style.display="block";const r=this._activeTab.substring(0,this._activeTab.length-1);let l;switch(this._activeTab){case"user-lists":l=null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("mwc-tab[title="+this.activeUserInnerTab+"-"+r+"]"),this._showList(l);break;case"credential-lists":l=null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("mwc-tab[title="+this.activeCredentialInnerTab+"-"+r+"]"),this._showList(l)}}_showList(e){var i,t,s,o;const a=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelectorAll(".list-content");for(let e=0;e<a.length;e++)a[e].style.display="none";(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e.title)).style.display="block";const r=e.title.split("-");"user"==r[1]?this.activeUserInnerTab=r[0]:this.activeCredentialInnerTab=r[0];const l=new CustomEvent("user-list-updated",{});null===(o=null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#"+e.title))||void 0===o||o.dispatchEvent(l)}_toggleCheckbox(e){const i=e.target,t=i.checked,s=i.closest("div").querySelector("mwc-textfield");s.disabled=t,s.disabled||""===s.value&&(s.value=0)}_validateResourceInput(e){const i=e.target.closest("mwc-textfield"),t=i.closest("div").querySelector("mwc-formfield.unlimited"),s=t?t.querySelector("mwc-checkbox"):null;if(i.classList.contains("discrete")&&(i.value=Math.round(i.value)),i.value<=0&&(i.value="concurrency-limit"===i.id||"container-per-session-limit"===i.id?1:0),!i.valid){const e=i.step?(o=i.step)%1?o.toString().split(".")[1].length:0:0;i.value=e>0?Math.min(i.value,i.value<0?i.min:i.max).toFixed(e):Math.min(Math.round(i.value),i.value<0?i.min:i.max)}var o;s&&(i.disabled=s.checked=i.value==parseFloat(i.min))}_updateUnlimitedValue(e){return["-",0,"0","Unlimited",1/0,"Infinity"].includes(e)?"":e}_validateUserInput(e){if(e.disabled)e.value="";else if(""===e.value)throw new Error(p("resourcePolicy.CannotCreateResourcePolicy"))}_addValidatorToPolicyInput(){this.newPolicyNameInput.validityTransform=(e,i)=>{if(!i)return this.newPolicyNameInput.validationMessage=p("credential.validation.PolicyName"),{valid:!1,valueMissing:!0};if(i.valid){const i=!this.resource_policy_names.includes(e);return i||(this.newPolicyNameInput.validationMessage=p("credential.validation.NameAlreadyExists")),{valid:i,customError:!i}}return i.patternMismatch?(this.newPolicyNameInput.validationMessage=p("credential.validation.LetterNumber-_dot"),{valid:i.valid,patternMismatch:!i.valid}):i.valueMissing?(this.newPolicyNameInput.validationMessage=p("credential.validation.PolicyName"),{valid:i.valid,valueMissing:!i.valid}):(this.newPolicyNameInput.validationMessage=p("credential.validation.LetterNumber-_dot"),{valid:i.valid,patternMismatch:!i.valid})}}_updateInputStatus(e){const i=e,t=i.closest("div").querySelector("mwc-checkbox");""===i.value||"0"===i.value?(i.disabled=!0,t&&(t.checked=!0)):(i.disabled=!1,t&&(t.checked=!1))}_openExportToCsvDialog(){this._defaultFileName=this._getDefaultCSVFileName(),this.exportToCsvDialog.show()}_exportToCSV(){if(!this.exportFileNameInput.validity.valid)return;let e,i,t,s,o;switch(this._activeTab){case"user-lists":e=this.activeUserList.users,e.map((e=>{["password","need_password_change"].forEach((i=>delete e[i]))})),g.exportToCsv(this.exportFileNameInput.value,e);break;case"credential-lists":i=this.activeCredentialList.keypairs,t=this.inactiveCredentialList.keypairs,s=i.concat(t),s.map((e=>{["is_admin"].forEach((i=>delete e[i]))})),g.exportToCsv(this.exportFileNameInput.value,s);break;case"resource-policy-lists":o=this.resourcePolicyList.resourcePolicy,g.exportToCsv(this.exportFileNameInput.value,o)}this.notification.text=p("session.DownloadingCSVFile"),this.notification.show(),this.exportToCsvDialog.hide()}_getResourceInfo(){var e,i,t,s,o,a,r,l,n;this.cpu_resource=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#cpu-resource"),this.ram_resource=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#ram-resource"),this.gpu_resource=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#gpu-resource"),this.fgpu_resource=null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#fgpu-resource"),this.concurrency_limit=null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("#concurrency-limit"),this.idle_timeout=null===(a=this.shadowRoot)||void 0===a?void 0:a.querySelector("#idle-timeout"),this.container_per_session_limit=null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector("#container-per-session-limit"),this.vfolder_max_limit=null===(l=this.shadowRoot)||void 0===l?void 0:l.querySelector("#vfolder-count-limit"),this.enableSessionLifetime&&(this.session_lifetime=null===(n=this.shadowRoot)||void 0===n?void 0:n.querySelector("#session-lifetime"))}_getDefaultCSVFileName(){return(new Date).toISOString().substring(0,10)+"_"+(new Date).toTimeString().slice(0,8).replace(/:/gi,"-")}_toggleDropdown(e){var i;const t=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#dropdown-menu"),s=e.target;t.anchor=s,t.open||t.show()}_validatePassword1(){this.userPasswordConfirmInput.reportValidity(),this.userPasswordInput.validityTransform=(e,i)=>i.valid?{valid:i.valid,customError:!i.valid}:i.valueMissing?(this.userPasswordInput.validationMessage=p("signup.PasswordInputRequired"),{valid:i.valid,customError:!i.valid}):(this.userPasswordInput.validationMessage=p("signup.PasswordInvalid"),{valid:i.valid,customError:!i.valid})}_validatePassword2(){this.userPasswordConfirmInput.validityTransform=(e,i)=>{if(i.valid){const e=this.userPasswordInput.value===this.userPasswordConfirmInput.value;return e||(this.userPasswordConfirmInput.validationMessage=p("signup.PasswordNotMatched")),{valid:e,customError:!e}}return i.valueMissing?(this.userPasswordConfirmInput.validationMessage=p("signup.PasswordInputRequired"),{valid:i.valid,customError:!i.valid}):(this.userPasswordConfirmInput.validationMessage=p("signup.PasswordInvalid"),{valid:i.valid,customError:!i.valid})}}_validatePassword(){this._validatePassword1(),this._validatePassword2()}_togglePasswordVisibility(e){const i=e.__on,t=e.closest("div").querySelector("mwc-textfield");i?t.setAttribute("type","text"):t.setAttribute("type","password")}static gBToBytes(e=0){const i=Math.pow(10,9);return Math.round(i*e)}async _runAction(){var e,i,t;location.search.includes("action")&&(location.search.includes("add")&&await this._launchKeyPairDialog(),this._showTab(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("mwc-tab[title=credential-lists]")),null===(t=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("mwc-tab-bar.main-bar"))||void 0===t||t.setAttribute("activeindex","1"))}render(){return m`
      <link rel="stylesheet" href="resources/custom.css">
      <lablup-activity-panel noheader narrow autowidth>
        <div slot="message">
          <h3 class="tab horizontal wrap layout">
           <mwc-tab-bar class="main-bar">
            <mwc-tab title="user-lists" label="${v("credential.Users")}"
                @click="${e=>this._showTab(e.target)}"></mwc-tab>
            <mwc-tab title="credential-lists" label="${v("credential.Credentials")}"
                @click="${e=>this._showTab(e.target)}"></mwc-tab>
            <mwc-tab title="resource-policy-lists" label="${v("credential.ResourcePolicies")}"
                @click="${e=>this._showTab(e.target)}"></mwc-tab>
           </mwc-tab-bar>
            ${this.isAdmin?m`
                    <span class="flex"></span>
                    <div style="position: relative;">
                      <mwc-icon-button
                        id="dropdown-menu-button"
                        icon="more_horiz"
                        raised
                        @click="${e=>this._toggleDropdown(e)}"
                      ></mwc-icon-button>
                      <mwc-menu id="dropdown-menu">
                        <mwc-list-item>
                          <a
                            class="horizontal layout start center export-csv"
                            @click="${this._openExportToCsvDialog}"
                          >
                            <mwc-icon
                              style="color:var(--token-colorTextSecondary);padding-right:10px;"
                            >
                              get_app
                            </mwc-icon>
                            ${v("credential.exportCSV")}
                          </a>
                        </mwc-list-item>
                      </mwc-menu>
                    </div>
                  `:m``}
          </h3>
          <div id="user-lists" class="admin item tab-content card">
            <h4 class="horizontal flex center center-justified layout">
              <mwc-tab-bar class="sub-bar">
                <mwc-tab title="active-user-list" label="${v("credential.Active")}"
                    @click="${e=>this._showList(e.target)}"></mwc-tab>
                <mwc-tab title="inactive-user-list" label="${v("credential.Inactive")}"
                    @click="${e=>this._showList(e.target)}"></mwc-tab>
              </mwc-tab-bar>
              <span class="flex"></span>
              <mwc-button raised id="add-user" icon="add" label="${v("credential.CreateUser")}"
                  @click="${this._launchUserAddDialog}"></mwc-button>
            </h4>
            <div>
              <backend-ai-user-list class="list-content" id="active-user-list" condition="active" ?active="${"user-lists"===this._activeTab}"></backend-ai-user-list>
              <backend-ai-user-list class="list-content" id="inactive-user-list" style="display:none;" ?active="${"user-lists"===this._activeTab}"></backend-ai-user-list>
            </div>
          </div>
          <div id="credential-lists" class="item tab-content card" style="display:none;">
            <h4 class="horizontal flex center center-justified layout">
              <mwc-tab-bar class="sub-bar">
                <mwc-tab title="active-credential-list" label="${v("credential.Active")}"
                    @click="${e=>this._showList(e.target)}"></mwc-tab>
                <mwc-tab title="inactive-credential-list" label="${v("credential.Inactive")}"
                    @click="${e=>this._showList(e.target)}"></mwc-tab>
              </mwc-tab-bar>
              <div class="flex"></div>
              <mwc-button raised id="add-keypair" icon="add" label="${v("credential.AddCredential")}"
                  @click="${this._launchKeyPairDialog}"></mwc-button>
            </h4>
            <backend-ai-credential-list class="list-content" id="active-credential-list" condition="active" ?active="${"credential-lists"===this._activeTab}"></backend-ai-credential-list>
            <backend-ai-credential-list class="list-content" style="display:none;" id="inactive-credential-list" condition="inactive" ?active="${"credential-lists"===this._activeTab}"></backend-ai-credential-list>
          </div>
          <div id="resource-policy-lists" class="admin item tab-content card" style="display:none;">
            <h4 class="horizontal flex center center-justified layout">
              <span>${v("credential.PolicyGroup")}</span>
              <span class="flex"></span>
              <mwc-button raised id="add-policy" icon="add" label="${v("credential.CreatePolicy")}"
                          ?disabled="${!this.isSuperAdmin}"
                          @click="${this._launchResourcePolicyDialog}"></mwc-button>
            </h4>
            <div>
              <backend-ai-resource-policy-list id="resource-policy-list" ?active="${"resource-policy-lists"===this._activeTab}"></backend-ai-resource-policy-list>
            </div>
          </div>
        </div>
      </lablup-activity-panel>
      <backend-ai-dialog id="new-keypair-dialog" fixed backdrop blockscrolling>
        <span slot="title">${v("credential.AddCredential")}</span>
        <div slot="content">
          <div class="vertical center-justified layout center">
            <mwc-textfield
                type="email"
                name="new_user_id"
                id="id_new_user_id"
                label="${v("credential.UserIDAsEmail")}"
                validationMessage="${v("credential.UserIDRequired")}"
                required
                maxLength="64"
                placeholder="${v("maxLength.64chars")}"
                autoValidate></mwc-textfield>

            <mwc-select id="resource-policy" label="${v("credential.ResourcePolicy")}" style="width:100%;margin:10px 0;">
              ${this.resource_policy_names.map((e=>m`
                  <mwc-list-item value="${e}">${e}</mwc-list-item>
                `))}
            </mwc-select>
            <mwc-select id="rate-limit" label="${v("credential.RateLimitFor15min")}" style="width:100%;margin:10px 0;">
              ${this.rate_metric.map((e=>m`
                  <mwc-list-item value="${e}">${e}</mwc-list-item>
                `))}
            </mwc-select>
            <!--<lablup-expansion name="advanced-keypair-info" summary="${v("general.Advanced")}" style="width:100%;">
              <div class="vertical layout center">
              <mwc-textfield
                  type="text"
                  name="new_access_key"
                  id="id_new_access_key"
                  label="${v("credential.UserIDAsEmail")}"
                  autoValidate></mwc-textfield>
              <mwc-textfield
                  type="text"
                  name="new_access_key"
                  id="id_new_secret_key"
                  label="${v("credential.AccessKeyOptional")}"
                  autoValidate
                  .value="${this.new_access_key}"><mwc-textfield>
              </div>
            </lablup-expansion>-->
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button raised id="create-keypair-button" icon="add" label="${v("general.Add")}" fullwidth
          @click="${this._addKeyPair}"></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="new-policy-dialog" fixed backdrop blockscrolling narrowLayout>
        <span slot="title">${v("credential.CreateResourcePolicy")}</span>
        <div slot="content">
          <mwc-textfield id="id_new_policy_name" label="${v("resourcePolicy.PolicyName")}"
                         validationMessage="${v("data.explorer.ValueRequired")}"
                         maxLength="64"
                         placeholder="${v("maxLength.64chars")}"
                         required></mwc-textfield>
          <h4>${v("resourcePolicy.ResourcePolicy")}</h4>
          <div class="horizontal center layout distancing">
            <div class="vertical layout popup-right-margin">
              <mwc-textfield label="CPU" class="discrete resource-input" id="cpu-resource" type="number" min="0" max="512"
                            @change="${e=>this._validateResourceInput(e)}"></mwc-textfield>
              <mwc-formfield label="${v("resourcePolicy.Unlimited")}" class="unlimited">
                  <mwc-checkbox @change="${e=>this._toggleCheckbox(e)}"></mwc-checkbox>
              </mwc-formfield>
            </div>
            <div class="vertical layout popup-both-margin">
              <mwc-textfield label="RAM(GB)" class="resource-input" id="ram-resource" type="number" min="0" max="100000" step="0.01"
                            @change="${e=>this._validateResourceInput(e)}"></mwc-textfield>
              <mwc-formfield label="${v("resourcePolicy.Unlimited")}" class="unlimited">
                <mwc-checkbox @change="${e=>this._toggleCheckbox(e)}"></mwc-checkbox>
              </mwc-formfield>
            </div>
            <div class="vertical layout popup-both-margin">
              <mwc-textfield label="GPU" class="resource-input" id="gpu-resource" type="number" min="0" max="64"
                            @change="${e=>this._validateResourceInput(e)}"></mwc-textfield>
              <mwc-formfield label="${v("resourcePolicy.Unlimited")}" class="unlimited">
                  <mwc-checkbox @change="${e=>this._toggleCheckbox(e)}"></mwc-checkbox>
              </mwc-formfield>
            </div>
            <div class="vertical layout popup-left-margin">
              <mwc-textfield label="fGPU" class="resource-input" id="fgpu-resource" type="number" min="0" max="256" step="0.1"
                            @change="${e=>this._validateResourceInput(e)}"></mwc-textfield>
              <mwc-formfield label="${v("resourcePolicy.Unlimited")}" class="unlimited">
                  <mwc-checkbox @change="${e=>this._toggleCheckbox(e)}"></mwc-checkbox>
              </mwc-formfield>
            </div>
          </div>
          <h4>${v("resourcePolicy.Sessions")}</h4>
          <div class="horizontal justified layout distancing wrap">
            <div class="vertical left layout ${this.enableSessionLifetime?"sessions-section":""}">
                <mwc-textfield label="${v("resourcePolicy.ContainerPerSession")}" class="discrete" id="container-per-session-limit" type="number" min="0" max="100"
                    @change="${e=>this._validateResourceInput(e)}"></mwc-textfield>
                <mwc-formfield label="${v("resourcePolicy.Unlimited")}" class="unlimited">
                    <mwc-checkbox @change="${e=>this._toggleCheckbox(e)}"></mwc-checkbox>
                </mwc-formfield>
              </div>
              <div class="vertical left layout ${this.enableSessionLifetime?"sessions-section":""}">
                <mwc-textfield label="${v("resourcePolicy.IdleTimeoutSec")}" class="discrete" id="idle-timeout" type="number" min="0" max="1552000"
                  @change="${e=>this._validateResourceInput(e)}"></mwc-textfield>
                <mwc-formfield label="${v("resourcePolicy.Unlimited")}" class="unlimited">
                    <mwc-checkbox @change="${e=>this._toggleCheckbox(e)}"></mwc-checkbox>
                </mwc-formfield>
              </div>
              <div class="vertical left layout ${this.enableSessionLifetime?"sessions-section":""}">
                  <mwc-textfield label="${v("resourcePolicy.ConcurrentJobs")}" class="discrete" id="concurrency-limit" type="number" min="0" max="100"
                      @change="${e=>this._validateResourceInput(e)}"></mwc-textfield>
                <mwc-formfield label="${v("resourcePolicy.Unlimited")}" class="unlimited">
                    <mwc-checkbox @change="${e=>this._toggleCheckbox(e)}"></mwc-checkbox>
                </mwc-formfield>
              </div>
              <div class="vertical left layout ${this.enableSessionLifetime?"sessions-section":""}"
                style="${this.enableSessionLifetime?"":"display:none;"}">
                <mwc-textfield label="${v("resourcePolicy.MaxSessionLifeTime")}" class="discrete" id="session-lifetime" type="number" min="0" max="100"
                    @change="${e=>this._validateResourceInput(e)}"></mwc-textfield>
                <mwc-formfield label="${v("resourcePolicy.Unlimited")}" class="unlimited">
                    <mwc-checkbox @change="${e=>this._toggleCheckbox(e)}"></mwc-checkbox>
                </mwc-formfield>
              </div>
          </div>
          <h4 style="margin-bottom:0px;">${v("resourcePolicy.Folders")}</h4>
          <div class="vertical center layout distancing" id="dropdown-area">
            <backend-ai-multi-select open-up id="allowed-vfolder-hosts" label="${v("resourcePolicy.AllowedHosts")}" style="width:100%;"></backend-ai-multi-select>
            <div
              class="horizontal layout justified"
              style=${this.isSupportMaxVfolderCountInUserResourcePolicy?"display:none;":"width:100%;"}
            >
              <mwc-textfield
                label="${v("credential.Max#")}"
                class="discrete"
                id="vfolder-count-limit"
                type="number"
                min="0"
                max="50"
                @change="${e=>this._validateResourceInput(e)}"
              ></mwc-textfield>
            </div>
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout distancing">
          <mwc-button
              unelevated
              fullwidth
              id="create-policy-button"
              icon="check"
              label="${v("credential.Create")}"
              @click="${()=>this._addResourcePolicy()}"></mwc-button>
        </div>
      </backend-ai-dialog>
      </backend-ai-dialog>
      <backend-ai-dialog id="new-user-dialog" fixed backdrop blockscrolling>
        <span slot="title">${v("credential.CreateUser")}</span>
        <div slot="content">
          <mwc-textfield
              type="email"
              name="user_email"
              id="id_user_email"
              label="${v("general.E-Mail")}"
              autoValidate
              required
              placeholder="${p("maxLength.64chars")}"
              maxLength="64"
              validationMessage="${p("credential.validation.InvalidEmailAddress")}">
          </mwc-textfield>
          <mwc-textfield
              type="text"
              name="user_name"
              id="id_user_name"
              label="${v("general.Username")}"
              placeholder="${p("maxLength.64chars")}"
              maxLength="64">
          </mwc-textfield>
          <div class="horizontal flex layout">
            <mwc-textfield
                type="password"
                name="user_password"
                id="id_user_password"
                label="${v("general.Password")}"
                autoValidate
                required
                pattern=${_.passwordRegex}
                validationMessage="${p("signup.PasswordInvalid")}"
                @change="${()=>this._validatePassword()}"
                maxLength="64">
            </mwc-textfield>
            <mwc-icon-button-toggle off onIcon="visibility" offIcon="visibility_off"
                @click="${e=>this._togglePasswordVisibility(e.target)}">
            </mwc-icon-button-toggle>
          </div>
          <div class="horizontal flex layout">
            <mwc-textfield
                type="password"
                name="user_confirm"
                id="id_user_confirm"
                label="${v("general.ConfirmPassword")}"
                autoValidate
                required
                pattern=${_.passwordRegex}
                validationMessage="${p("signup.PasswordNotMatched")}"
                @change="${()=>this._validatePassword()}"
                maxLength="64">
            </mwc-textfield>
            <mwc-icon-button-toggle off onIcon="visibility" offIcon="visibility_off"
                @click="${e=>this._togglePasswordVisibility(e.target)}">
            </mwc-icon-button-toggle>
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button raised id="create-user-button" icon="add" label="${v("credential.CreateUser")}" fullwidth
          @click="${this._addUser}"></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="export-to-csv" fixed backdrop blockscrolling>
        <span slot="title">${v("credential.ExportCSVFile")} (${this._activeTab})</span>

        <div slot="content" class="intro centered login-panel">
          <mwc-textfield id="export-file-name" label="${p("credential.FileName")}"
                          validationMessage="${p("credential.validation.LetterNumber-_dot")}"
                          value="${this._activeTab+"_"+this._defaultFileName}" required
                          placeholder="${v("maxLength.255chars")}"
                          maxLength="255"
          ></mwc-textfield>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
              unelevated
              fullwidth
              icon="get_app"
              label="${v("credential.ExportCSVFile")}"
              class="export-csv"
              @click="${this._exportToCSV}"></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};e([i({type:Object})],I.prototype,"cpu_resource",void 0),e([i({type:Object})],I.prototype,"ram_resource",void 0),e([i({type:Object})],I.prototype,"gpu_resource",void 0),e([i({type:Object})],I.prototype,"fgpu_resource",void 0),e([i({type:Object})],I.prototype,"concurrency_limit",void 0),e([i({type:Object})],I.prototype,"idle_timeout",void 0),e([i({type:Object})],I.prototype,"session_lifetime",void 0),e([i({type:Object})],I.prototype,"container_per_session_limit",void 0),e([i({type:Object})],I.prototype,"vfolder_max_limit",void 0),e([i({type:Array})],I.prototype,"rate_metric",void 0),e([i({type:Object})],I.prototype,"resource_policies",void 0),e([i({type:Array})],I.prototype,"resource_policy_names",void 0),e([i({type:Boolean})],I.prototype,"isAdmin",void 0),e([i({type:Boolean})],I.prototype,"isSuperAdmin",void 0),e([i({type:String})],I.prototype,"_status",void 0),e([i({type:String})],I.prototype,"new_access_key",void 0),e([i({type:String})],I.prototype,"new_secret_key",void 0),e([i({type:String})],I.prototype,"_activeTab",void 0),e([i({type:Object})],I.prototype,"notification",void 0),e([i({type:String})],I.prototype,"_defaultFileName",void 0),e([i({type:Number})],I.prototype,"selectAreaHeight",void 0),e([i({type:Boolean})],I.prototype,"enableSessionLifetime",void 0),e([i({type:Boolean})],I.prototype,"enableParsingStoragePermissions",void 0),e([i({type:String})],I.prototype,"activeUserInnerTab",void 0),e([i({type:String})],I.prototype,"activeCredentialInnerTab",void 0),e([t("#active-credential-list")],I.prototype,"activeCredentialList",void 0),e([t("#inactive-credential-list")],I.prototype,"inactiveCredentialList",void 0),e([t("#active-user-list")],I.prototype,"activeUserList",void 0),e([t("#resource-policy-list")],I.prototype,"resourcePolicyList",void 0),e([t("#dropdown-area")],I.prototype,"dropdownArea",void 0),e([t("#rate-limit")],I.prototype,"rateLimit",void 0),e([t("#resource-policy")],I.prototype,"resourcePolicy",void 0),e([t("#id_user_email")],I.prototype,"userEmailInput",void 0),e([t("#id_new_policy_name")],I.prototype,"newPolicyNameInput",void 0),e([t("#id_new_user_id")],I.prototype,"userIdInput",void 0),e([t("#id_user_confirm")],I.prototype,"userPasswordConfirmInput",void 0),e([t("#id_user_name")],I.prototype,"userNameInput",void 0),e([t("#id_user_password")],I.prototype,"userPasswordInput",void 0),e([t("#new-keypair-dialog")],I.prototype,"newKeypairDialog",void 0),e([t("#new-policy-dialog")],I.prototype,"newPolicyDialog",void 0),e([t("#new-user-dialog")],I.prototype,"newUserDialog",void 0),e([t("#export-to-csv")],I.prototype,"exportToCsvDialog",void 0),e([t("#export-file-name")],I.prototype,"exportFileNameInput",void 0),e([t("#allowed-vfolder-hosts")],I.prototype,"allowedVfolderHostsSelect",void 0),e([y()],I.prototype,"all_vfolder_hosts",void 0),e([y()],I.prototype,"default_vfolder_host",void 0),e([y()],I.prototype,"vfolderPermissions",void 0),e([y()],I.prototype,"isSupportMaxVfolderCountInUserResourcePolicy",void 0),I=e([s("backend-ai-credential-view")],I);
