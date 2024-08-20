import{_ as e,n as t,e as i,t as a,B as s,b as o,I as r,a as n,u as l,c,i as d,d as u,g as p,p as h,x as m,f as v,N as y}from"./backend-ai-webui-dvRyOX_e.js";import{J as _}from"./vaadin-iconset-DPmwx4aL.js";import"./backend-ai-list-status-CpZuh1nO.js";import"./lablup-grid-sort-filter-column-C2aexclr.js";import"./vaadin-grid-DjH0sPLR.js";import"./vaadin-grid-filter-column-Bstvob6v.js";import"./vaadin-grid-sort-column-Bkfboj4k.js";import"./vaadin-item-FWhoAebV.js";import"./backend-ai-multi-select-CmQCUDWg.js";import"./mwc-switch-C1VxcxVe.js";import"./lablup-activity-panel-CUzA1T9h.js";import"./mwc-formfield-azaYbQhE.js";import"./mwc-tab-bar-RQBvmmHz.js";import"./dir-utils-BTQok0yH.js";import"./vaadin-item-mixin-Eeh1qf5y.js";import"./active-mixin-_JOWYQWx.js";import"./mwc-check-list-item-BMr63zxO.js";import"./state-BGEx6bYL.js";var g;class b extends Error{constructor(e){super(e),Object.setPrototypeOf(this,b.prototype),this.title="Unable to delete keypair"}}let f=g=class extends s{constructor(){super(),this.keypairInfo={user_id:"1",access_key:"ABC",secret_key:"ABC",last_used:"",is_admin:!1,resource_policy:"",rate_limit:5e3,concurrency_used:0,num_queries:0,created_at:""},this.isAdmin=!1,this.condition="active",this.keypairs=[],this.resourcePolicy=Object(),this.indicator=Object(),this._boundKeyageRenderer=this.keyageRenderer.bind(this),this._boundControlRenderer=this.controlRenderer.bind(this),this._boundAccessKeyRenderer=this.accessKeyRenderer.bind(this),this._boundPermissionRenderer=this.permissionRenderer.bind(this),this._boundResourcePolicyRenderer=this.resourcePolicyRenderer.bind(this),this._boundAllocationRenderer=this.allocationRenderer.bind(this),this._boundUserIdRenderer=this.userIdRenderer.bind(this),this.keypairGrid=Object(),this.listCondition="loading",this._totalCredentialCount=0,this.isUserInfoMaskEnabled=!1,this.deleteKeyPairUserName="",this.deleteKeyPairAccessKey="",this.supportMainAccessKey=!1,this._mainAccessKeyList=[]}static get styles(){return[o,r,n,l,c,d`
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

        mwc-list-item {
          width: var(--token-mwc-select-item-width, 340px);
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
          border-bottom: 1px solid var(--token-colorBorder, #ccc);
        }

        mwc-button,
        mwc-button[unelevated],
        mwc-button[outlined] {
          background-image: none;
          --mdc-theme-primary: var(--general-button-background-color);
          --mdc-theme-on-primary: var(--general-button-color);
          --mdc-typography-font-family: var(--token-fontFamily);
        }
      `]}firstUpdated(){this.notification=globalThis.lablupNotification}async _viewStateChanged(e){var t;await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{var e;this._refreshKeyData(),this.isAdmin=globalThis.backendaiclient.is_admin,this.supportMainAccessKey=globalThis.backendaiclient.supports("main-access-key"),this.isUserInfoMaskEnabled=globalThis.backendaiclient._config.maskUserInfo,this.keypairGrid=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#keypair-grid")}),!0):(this._refreshKeyData(),this.isAdmin=globalThis.backendaiclient.is_admin,this.supportMainAccessKey=globalThis.backendaiclient.supports("main-access-key"),this.isUserInfoMaskEnabled=globalThis.backendaiclient._config.maskUserInfo,this.keypairGrid=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#keypair-grid")))}_refreshKeyData(e=null){var t;let i=!0;if("active"===this.condition)i=!0;else i=!1;return this.listCondition="loading",null===(t=this._listStatus)||void 0===t||t.show(),globalThis.backendaiclient.resourcePolicy.get().then((e=>{const t=e.keypair_resource_policies;this.resourcePolicy=globalThis.backendaiclient.utils.gqlToObject(t,"name")})).then((()=>globalThis.backendaiclient.keypair.list(e,["access_key","is_active","is_admin","user_id","created_at","last_used","concurrency_limit","concurrency_used","rate_limit","num_queries","resource_policy"],i))).then((async e=>{var t;if(this.supportMainAccessKey)try{const e=await globalThis.backendaiclient.user.list(!0,["main_access_key"]),t=await globalThis.backendaiclient.user.list(!1,["main_access_key"]);e.users&&t.users&&(this._mainAccessKeyList=[...e.users,...t.users].map((e=>e.main_access_key)))}catch(e){throw e}const i=e.keypairs;Object.keys(i).map(((e,t)=>{const a=i[e];if(a.resource_policy in this.resourcePolicy){for(const e in this.resourcePolicy[a.resource_policy])"created_at"!==e&&(a[e]=this.resourcePolicy[a.resource_policy][e],"total_resource_slots"===e&&(a.total_resource_slots=JSON.parse(this.resourcePolicy[a.resource_policy][e])));a.created_at_formatted=this._humanReadableTime(a.created_at),a.elapsed=this._elapsed(a.created_at),"cpu"in a.total_resource_slots||"UNLIMITED"===a.default_for_unspecified&&(a.total_resource_slots.cpu="-"),"mem"in a.total_resource_slots?a.total_resource_slots.mem=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(a.total_resource_slots.mem,"g")):"UNLIMITED"===a.default_for_unspecified&&(a.total_resource_slots.mem="-"),"cuda.device"in a.total_resource_slots&&(a.total_resource_slots.cuda_device=a.total_resource_slots["cuda.device"]),"cuda.shares"in a.total_resource_slots&&(a.total_resource_slots.cuda_shares=a.total_resource_slots["cuda.shares"]),"cuda_device"in a.total_resource_slots==!1&&"cuda_shares"in a.total_resource_slots==!1&&"UNLIMITED"===a.default_for_unspecified&&(a.total_resource_slots.cuda_shares="-",a.total_resource_slots.cuda_device="-"),"rocm.device"in a.total_resource_slots&&(a.total_resource_slots.rocm_device=a.total_resource_slots["rocm.device"]),"rocm_device"in a.total_resource_slots==!1&&"UNLIMITED"===a.default_for_unspecified&&(a.total_resource_slots.rocm_device="-"),"tpu.device"in a.total_resource_slots&&(a.total_resource_slots.tpu_device=a.total_resource_slots["tpu.device"]),"tpu_device"in a.total_resource_slots==!1&&"UNLIMITED"===a.default_for_unspecified&&(a.total_resource_slots.tpu_device="-"),"ipu.device"in a.total_resource_slots&&(a.total_resource_slots.ipu_device=a.total_resource_slots["ipu.device"]),"ipu_device"in a.total_resource_slots==!1&&"UNLIMITED"===a.default_for_unspecified&&(a.total_resource_slots.ipu_device="-"),"atom.device"in a.total_resource_slots&&(a.total_resource_slots.atom_device=a.total_resource_slots["atom.device"]),"atom_device"in a.total_resource_slots==!1&&"UNLIMITED"===a.default_for_unspecified&&(a.total_resource_slots.atom_device="-"),"atom-plus.device"in a.total_resource_slots&&(a.total_resource_slots.atom_plus_device=a.total_resource_slots["atom-plus.device"]),"atom-plus.device"in a.total_resource_slots==!1&&"UNLIMITED"===a.default_for_unspecified&&(a.total_resource_slots.atom_plus_device="-"),"warboy.device"in a.total_resource_slots&&(a.total_resource_slots.warboy_device=a.total_resource_slots["warboy.device"]),"warboy_device"in a.total_resource_slots==!1&&"UNLIMITED"===a.default_for_unspecified&&(a.total_resource_slots.warboy_device="-"),"hyperaccel-lpu.device"in a.total_resource_slots&&(a.total_resource_slots.hyperaccel_lpu_device=a.total_resource_slots["hyperaccel-lpu.device"]),"hyperaccel_lpu_device"in a.total_resource_slots==!1&&"UNLIMITED"===a.default_for_unspecified&&(a.total_resource_slots.hyperaccel_lpu_device="-"),["cpu","mem","cuda_shares","cuda_device","rocm_device","tpu_device","ipu_device","atom_device","atom_plus_device","warboy_device","hyperaccel_lpu_device"].forEach((e=>{a.total_resource_slots[e]=this._markIfUnlimited(a.total_resource_slots[e])})),a.max_vfolder_size=this._markIfUnlimited(g.bytesToGB(a.max_vfolder_size))}})),this.keypairs=i,0==this.keypairs.length?this.listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide()})).catch((e=>{var t;null===(t=this._listStatus)||void 0===t||t.hide(),console.log(e),e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}async _showKeypairDetail(e){const t=e.target.closest("#controls")["access-key"];try{const e=await this._getKeyData(t);this.keypairInfo=e.keypair,this.keypairInfoDialog.show()}catch(e){e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}}async _modifyResourcePolicy(e){const t=e.target.closest("#controls")["access-key"];try{const e=await this._getKeyData(t);this.keypairInfo=e.keypair,this.policyListSelect.value=this.keypairInfo.resource_policy,this.rateLimit.value=this.keypairInfo.rate_limit.toString(),this.keypairModifyDialog.show()}catch(e){e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}}async _getKeyData(e){return globalThis.backendaiclient.keypair.info(e,["access_key","secret_key","is_active","is_admin","user_id","created_at","last_used","concurrency_limit","concurrency_used","rate_limit","num_queries","resource_policy"])}refresh(){this._refreshKeyData()}_isActive(){return"active"===this.condition}_deleteKeyPairDialog(e){const t=e.target.closest("#controls"),i=t["user-id"],a=t["access-key"];this.deleteKeyPairUserName=i,this.deleteKeyPairAccessKey=a,this.deleteKeyPairDialog.show()}_deleteKey(e){globalThis.backendaiclient.keypair.delete(this.deleteKeyPairAccessKey).then((e=>{if(e.delete_keypair&&!e.delete_keypair.ok)throw new b(e.delete_keypair.msg);this.notification.text=p("credential.KeySeccessfullyDeleted"),this.notification.show(),this.refresh(),this.deleteKeyPairDialog.hide()})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_revokeKey(e){this._mutateKey(e,!1)}_reuseKey(e){this._mutateKey(e,!0)}_mutateKey(e,t){const i=e.target.closest("#controls")["access-key"],a=this.keypairs.find(this._findKeyItem,i),s={is_active:t,is_admin:a.is_admin,resource_policy:a.resource_policy,rate_limit:a.rate_limit,concurrency_limit:a.concurrency_limit};globalThis.backendaiclient.keypair.mutate(i,s).then((e=>{const t=new CustomEvent("backend-ai-credential-refresh",{detail:this});document.dispatchEvent(t)})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_findKeyItem(e){return e.access_key=this}_elapsed(e,t){const i=new Date(e),a=(this.condition,new Date),s=Math.floor((a.getTime()-i.getTime())/1e3);return Math.floor(s/86400)}_humanReadableTime(e){return new Date(e).toUTCString()}_indexRenderer(e,t,i){const a=i.index+1;h(m`
        <div>${a}</div>
      `,e)}_markIfUnlimited(e){return["-",0,"Unlimited",1/0,"Infinity"].includes(e)?"∞":e}keyageRenderer(e,t,i){h(m`
        <div class="layout vertical">
          <span>${i.item.elapsed} ${v("credential.Days")}</span>
          <span class="indicator">(${i.item.created_at_formatted})</span>
        </div>
      `,e)}controlRenderer(e,t,i){var a;h(m`
        <div
          id="controls"
          class="layout horizontal flex center"
          .access-key="${i.item.access_key}"
          .user-id="${i.item.user_id}"
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
          ${this.isAdmin&&!this._isActive()?m`
                <mwc-icon-button
                  class="fg red"
                  icon="delete_forever"
                  fab
                  ?disabled=${this._mainAccessKeyList.includes(null===(a=i.item)||void 0===a?void 0:a.access_key)}
                  flat
                  inverted
                  @click="${e=>this._deleteKeyPairDialog(e)}"
                ></mwc-icon-button>
              `:m``}
        </div>
      `,e)}accessKeyRenderer(e,t,i){var a;h(m`
        <div class="vertical layout flex">
          <div class="monospace">${i.item.access_key}</div>
          ${this._mainAccessKeyList.includes(null===(a=i.item)||void 0===a?void 0:a.access_key)?m`
                <lablup-shields
                  app=""
                  color="darkgreen"
                  description="${v("credential.MainAccessKey")}"
                  ui="flat"
                ></lablup-shields>
              `:m``}
        </div>
      `,e)}permissionRenderer(e,t,i){h(m`
        <div class="layout horizontal center flex">
          ${i.item.is_admin?m`
                <lablup-shields
                  app=""
                  color="red"
                  description="admin"
                  ui="flat"
                ></lablup-shields>
              `:m``}
          <lablup-shields app="" description="user" ui="flat"></lablup-shields>
        </div>
      `,e)}resourcePolicyRenderer(e,t,i){h(m`
        <div class="layout horizontal wrap center">
          <span>${i.item.resource_policy}</span>
        </div>
        <div class="layout horizontal wrap center">
          <div class="layout horizontal configuration">
            <mwc-icon class="fg green">developer_board</mwc-icon>
            <span>${i.item.total_resource_slots.cpu}</span>
            <span class="indicator">${v("general.cores")}</span>
          </div>
          <div class="layout horizontal configuration">
            <mwc-icon class="fg green">memory</mwc-icon>
            <span>${i.item.total_resource_slots.mem}</span>
            <span class="indicator">GiB</span>
          </div>
        </div>
        <div class="layout horizontal wrap center">
          ${i.item.total_resource_slots.cuda_device?m`
                <div class="layout horizontal configuration">
                  <mwc-icon class="fg green">view_module</mwc-icon>
                  <span>${i.item.total_resource_slots.cuda_device}</span>
                  <span class="indicator">GPU</span>
                </div>
              `:m``}
          ${i.item.total_resource_slots.cuda_shares?m`
                <div class="layout horizontal configuration">
                  <mwc-icon class="fg green">view_module</mwc-icon>
                  <span>${i.item.total_resource_slots.cuda_shares}</span>
                  <span class="indicator">fGPU</span>
                </div>
              `:m``}
        </div>
        ${globalThis.backendaiclient.supports("deprecated-max-vfolder-count-in-keypair-resource-policy")?m``:m`
              <div class="layout horizontal wrap center">
                <div class="layout horizontal configuration">
                  <mwc-icon class="fg green">cloud_queue</mwc-icon>
                  <span>${i.item.max_vfolder_size}</span>
                  <span class="indicator">GB</span>
                </div>
              </div>
              <div class="layout horizontal configuration">
                <mwc-icon class="fg green">folder</mwc-icon>
                <span>${i.item.max_vfolder_count}</span>
                <span class="indicator">${v("general.Folders")}</span>
              </div>
            `}
        <!-- TODO: Display max_vfolder_count in user resource policy -->
      `,e)}allocationRenderer(e,t,i){h(m`
        <div class="layout horizontal center flex">
          <div class="vertical start layout">
            <div style="font-size:11px;width:40px;">
              ${i.item.concurrency_used} /
              ${i.item.concurrency_limit}
            </div>
            <span class="indicator">Sess.</span>
          </div>
          <div class="vertical start layout">
            <span style="font-size:8px">
              ${i.item.rate_limit}
              <span class="indicator">req./15m.</span>
            </span>
            <span style="font-size:8px">
              ${i.item.num_queries}
              <span class="indicator">queries</span>
            </span>
          </div>
        </div>
      `,e)}userIdRenderer(e,t,i){h(m`
        <span>${this._getUserId(i.item.user_id)}</span>
      `,e)}_validateRateLimit(){this.rateLimit.validityTransform=(e,t)=>t.valid?0!==e.length&&!isNaN(Number(e))&&Number(e)<100?(this.rateLimit.validationMessage=p("credential.WarningLessRateLimit"),{valid:!t.valid,customError:!t.valid}):{valid:t.valid,customError:!t.valid}:t.valueMissing?(this.rateLimit.validationMessage=p("credential.RateLimitInputRequired"),{valid:t.valid,customError:!t.valid}):t.rangeOverflow?(this.rateLimit.value=e=5e4.toString(),this.rateLimit.validationMessage=p("credential.RateLimitValidation"),{valid:t.valid,customError:!t.valid}):t.rangeUnderflow?(this.rateLimit.value=e="1",this.rateLimit.validationMessage=p("credential.RateLimitValidation"),{valid:t.valid,customError:!t.valid}):(this.rateLimit.validationMessage=p("credential.InvalidRateLimitValue"),{valid:t.valid,customError:!t.valid})}openDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).show()}closeDialog(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e)).hide()}_saveKeypairModification(e=!1){const t=this.policyListSelect.value,i=Number(this.rateLimit.value);if(!(this.rateLimit.checkValidity()||i<100&&e))return i<100&&!e?void this.openDialog("keypair-confirmation"):void 0;let a={};t!==this.keypairInfo.resource_policy&&(a={...a,resource_policy:t}),i!==this.keypairInfo.rate_limit&&(a={...a,rate_limit:i}),0===Object.entries(a).length?(this.notification.text=p("credential.NoChanges"),this.notification.show()):globalThis.backendaiclient.keypair.mutate(this.keypairInfo.access_key,a).then((e=>{e.modify_keypair.ok?(this.keypairInfo.resource_policy===t&&this.keypairInfo.rate_limit===i?this.notification.text=p("credential.NoChanges"):this.notification.text=p("environment.SuccessfullyModified"),this.refresh()):this.notification.text=p("dialog.ErrorOccurred"),this.notification.show()})),this.closeDialog("keypair-modify-dialog")}_confirmAndSaveKeypairModification(){this.closeDialog("keypair-confirmation"),this._saveKeypairModification(!0)}_adjustRateLimit(){const e=Number(this.rateLimit.value);e>5e4&&(this.rateLimit.value=5e4.toString()),e<=0&&(this.rateLimit.value="1")}static bytesToGB(e,t=1){return e?(e/10**9).toFixed(t):e}_getUserId(e=""){if(this.isUserInfoMaskEnabled){const t=2,i=e.split("@")[0].length-t;e=globalThis.backendaiutils._maskString(e,"*",t,i)}return e}_getAccessKey(e=""){if(this.isUserInfoMaskEnabled){const t=4,i=e.length-t;e=globalThis.backendaiutils._maskString(e,"*",t,i)}return e}render(){return m`
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
              fixedMenuPosition
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
    `}};e([t({type:Object})],f.prototype,"notification",void 0),e([t({type:Object})],f.prototype,"keypairInfo",void 0),e([t({type:Boolean})],f.prototype,"isAdmin",void 0),e([t({type:String})],f.prototype,"condition",void 0),e([t({type:Array})],f.prototype,"keypairs",void 0),e([t({type:Object})],f.prototype,"resourcePolicy",void 0),e([t({type:Object})],f.prototype,"indicator",void 0),e([t({type:Object})],f.prototype,"_boundKeyageRenderer",void 0),e([t({type:Object})],f.prototype,"_boundControlRenderer",void 0),e([t({type:Object})],f.prototype,"_boundAccessKeyRenderer",void 0),e([t({type:Object})],f.prototype,"_boundPermissionRenderer",void 0),e([t({type:Object})],f.prototype,"_boundResourcePolicyRenderer",void 0),e([t({type:Object})],f.prototype,"_boundAllocationRenderer",void 0),e([t({type:Object})],f.prototype,"_boundUserIdRenderer",void 0),e([t({type:Object})],f.prototype,"keypairGrid",void 0),e([t({type:String})],f.prototype,"listCondition",void 0),e([t({type:Number})],f.prototype,"_totalCredentialCount",void 0),e([t({type:Boolean})],f.prototype,"isUserInfoMaskEnabled",void 0),e([t({type:String})],f.prototype,"deleteKeyPairUserName",void 0),e([t({type:String})],f.prototype,"deleteKeyPairAccessKey",void 0),e([t({type:Boolean})],f.prototype,"supportMainAccessKey",void 0),e([t({type:Array})],f.prototype,"_mainAccessKeyList",void 0),e([i("#keypair-info-dialog")],f.prototype,"keypairInfoDialog",void 0),e([i("#keypair-modify-dialog")],f.prototype,"keypairModifyDialog",void 0),e([i("#delete-keypair-dialog")],f.prototype,"deleteKeyPairDialog",void 0),e([i("#policy-list")],f.prototype,"policyListSelect",void 0),e([i("#rate-limit")],f.prototype,"rateLimit",void 0),e([i("#list-status")],f.prototype,"_listStatus",void 0),f=g=e([a("backend-ai-credential-list")],f);let w=class extends s{constructor(){super(),this.isAdmin=!1,this.editMode=!1,this.users=[],this.userInfo=Object(),this.userInfoGroups=[],this.userEmail="",this.openUserInfoModal=!1,this.openUserSettingModal=!1,this.condition="",this._boundControlRenderer=this.controlRenderer.bind(this),this._userIdRenderer=this.userIdRenderer.bind(this),this._userNameRenderer=this.userNameRenderer.bind(this),this._userStatusRenderer=this.userStatusRenderer.bind(this),this._totpActivatedRenderer=this.totpActivatedRenderer.bind(this),this.signoutUserName="",this.notification=Object(),this.listCondition="loading",this._totalUserCount=0,this.isUserInfoMaskEnabled=!1,this.totpSupported=!1,this.totpActivated=!1,this.supportMainAccessKey=!1,this.userStatus={active:"Active",inactive:"Inactive","before-verification":"Before Verification",deleted:"Deleted"}}static get styles(){return[o,r,n,l,c,d`
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
          border-bottom: 1px solid var(--token-colorBorder, #ccc);
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
      `]}firstUpdated(){this.notification=globalThis.lablupNotification,this.addEventListener("user-list-updated",(()=>{this.refresh()}))}async _viewStateChanged(e){var t,i,a;await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(async()=>{var e,t,i;this.totpSupported=(null===(e=globalThis.backendaiclient)||void 0===e?void 0:e.supports("2FA"))&&await(null===(t=globalThis.backendaiclient)||void 0===t?void 0:t.isManagerSupportingTOTP()),this.supportMainAccessKey=null===(i=globalThis.backendaiclient)||void 0===i?void 0:i.supports("main-access-key"),this._refreshUserData(),this.isAdmin=globalThis.backendaiclient.is_admin,this.isUserInfoMaskEnabled=globalThis.backendaiclient._config.maskUserInfo}),!0):(this.totpSupported=(null===(t=globalThis.backendaiclient)||void 0===t?void 0:t.supports("2FA"))&&await(null===(i=globalThis.backendaiclient)||void 0===i?void 0:i.isManagerSupportingTOTP()),this.supportMainAccessKey=null===(a=globalThis.backendaiclient)||void 0===a?void 0:a.supports("main-access-key"),this._refreshUserData(),this.isAdmin=globalThis.backendaiclient.is_admin,this.isUserInfoMaskEnabled=globalThis.backendaiclient._config.maskUserInfo))}_refreshUserData(){var e;let t=!0;if("active"===this.condition)t=!0;else t=!1;this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show();const i=["email","username","need_password_change","full_name","description","is_active","domain_name","role","groups {id name}","status","main_access_key"];return this.totpSupported&&i.push("totp_activated"),globalThis.backendaiclient.user.list(t,i).then((e=>{var t;const i=e.users;this.users=i,0==this.users.length?this.listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide()})).catch((e=>{var t;null===(t=this._listStatus)||void 0===t||t.hide(),console.log(e),e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}async _openUserSettingModal(e){const t=e.target.closest("#controls");this.userEmail=t["user-id"],this.openUserSettingModal=!0}async _openUserInfoModal(e){const t=e.target.closest("#controls");this.userEmail=t["user-id"],this.openUserInfoModal=!0}_signoutUserDialog(e){const t=e.target.closest("#controls")["user-id"];this.signoutUserName=t,this.signoutUserDialog.show()}_signoutUser(){globalThis.backendaiclient.user.delete(this.signoutUserName).then((e=>{this.notification.text=p("credential.SignoutSeccessfullyFinished"),this.notification.show(),this._refreshUserData(),this.signoutUserDialog.hide()})).catch((e=>{console.log(e),void 0!==e.message?(this.notification.text=u.relieve(e.title),this.notification.detail=e.message):this.notification.text=u.relieve("Signout failed. Check your permission and try again."),this.notification.show()}))}async _getUserData(e){const t=["email","username","need_password_change","full_name","description","status","domain_name","role","groups {id name}","main_access_key"];return this.totpSupported&&t.push("totp_activated"),globalThis.backendaiclient.user.get(e,t)}refresh(){this._refreshUserData(),this.userGrid.clearCache()}_isActive(){return"active"===this.condition}_elapsed(e,t){const i=new Date(e);let a;a=(this.condition,new Date);const s=Math.floor((a.getTime()-i.getTime())/1e3);return Math.floor(s/86400)}_humanReadableTime(e){return new Date(e).toUTCString()}_markIfUnlimited(e){return["-",0,"Unlimited",1/0,"Infinity"].includes(e)?"∞":e}_getUserId(e=""){if(e&&this.isUserInfoMaskEnabled){const t=2,i=e.split("@")[0].length-t;e=globalThis.backendaiutils._maskString(e,"*",t,i)}return e}_getUsername(e=""){if(e&&this.isUserInfoMaskEnabled){const t=2,i=e.length-t;e=globalThis.backendaiutils._maskString(e,"*",t,i)}return e}async _setTotpActivated(){if(this.totpSupported){const e=await globalThis.backendaiclient.user.get(globalThis.backendaiclient.email,["totp_activated"]);this.totpActivated=e.user.totp_activated}}_indexRenderer(e,t,i){const a=i.index+1;h(m`
        <div>${a}</div>
      `,e)}controlRenderer(e,t,i){h(m`
        <div
          id="controls"
          class="layout horizontal flex center"
          .user-id="${i.item.email}"
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
      `,e)}userIdRenderer(e,t,i){h(m`
        <span>${this._getUserId(i.item.email)}</span>
      `,e)}userNameRenderer(e,t,i){h(m`
        <span>${this._getUsername(i.item.username)}</span>
      `,e)}userStatusRenderer(e,t,i){const a="active"===i.item.status?"green":"lightgrey";h(m`
        <lablup-shields
          app=""
          color="${a}"
          description="${i.item.status}"
          ui="flat"
        ></lablup-shields>
      `,e)}totpActivatedRenderer(e,t,i){var a;h(m`
        <div class="layout horizontal center center-justified wrap">
          ${(null===(a=i.item)||void 0===a?void 0:a.totp_activated)?m`
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
            ${v("credential.InactivateTheFollowingUsers")}
            <span style="color:var(--token-red, red)">
              ${this.signoutUserName}
            </span>
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
    `}};e([t({type:Boolean})],w.prototype,"isAdmin",void 0),e([t({type:Boolean})],w.prototype,"editMode",void 0),e([t({type:Array})],w.prototype,"users",void 0),e([t({type:Object})],w.prototype,"userInfo",void 0),e([t({type:Array})],w.prototype,"userInfoGroups",void 0),e([t({type:String})],w.prototype,"userEmail",void 0),e([t({type:Boolean})],w.prototype,"openUserInfoModal",void 0),e([t({type:Boolean})],w.prototype,"openUserSettingModal",void 0),e([t({type:String})],w.prototype,"condition",void 0),e([t({type:Object})],w.prototype,"_boundControlRenderer",void 0),e([t({type:Object})],w.prototype,"_userIdRenderer",void 0),e([t({type:Object})],w.prototype,"_userNameRenderer",void 0),e([t({type:Object})],w.prototype,"_userStatusRenderer",void 0),e([t({type:Object})],w.prototype,"_totpActivatedRenderer",void 0),e([t({type:Object})],w.prototype,"keypairs",void 0),e([t({type:String})],w.prototype,"signoutUserName",void 0),e([t({type:Object})],w.prototype,"notification",void 0),e([t({type:String})],w.prototype,"listCondition",void 0),e([t({type:Number})],w.prototype,"_totalUserCount",void 0),e([t({type:Boolean})],w.prototype,"isUserInfoMaskEnabled",void 0),e([t({type:Boolean})],w.prototype,"totpSupported",void 0),e([t({type:Boolean})],w.prototype,"totpActivated",void 0),e([t({type:Boolean})],w.prototype,"supportMainAccessKey",void 0),e([t({type:Object})],w.prototype,"userStatus",void 0),e([i("#user-grid")],w.prototype,"userGrid",void 0),e([i("#loading-spinner")],w.prototype,"spinner",void 0),e([i("#list-status")],w.prototype,"_listStatus",void 0),e([i("#password")],w.prototype,"passwordInput",void 0),e([i("#confirm")],w.prototype,"confirmInput",void 0),e([i("#username")],w.prototype,"usernameInput",void 0),e([i("#full_name")],w.prototype,"fullNameInput",void 0),e([i("#description")],w.prototype,"descriptionInput",void 0),e([i("#status")],w.prototype,"statusSelect",void 0),e([i("#signout-user-dialog")],w.prototype,"signoutUserDialog",void 0),w=e([a("backend-ai-user-list")],w);let k=class extends s{constructor(){super(),this.vfolder_max_limit={},this.rate_metric=[1e3,2e3,3e3,4e3,5e3,1e4,5e4],this.resource_policies=Object(),this.isAdmin=!1,this.isSuperAdmin=!1,this._status="inactive",this.new_access_key="",this.new_secret_key="",this._activeTab="users",this.notification=Object(),this._defaultFileName="",this.enableSessionLifetime=!1,this.activeUserInnerTab="active",this.activeCredentialInnerTab="active",this.resource_policy_names=[]}static get styles(){return[o,r,n,l,c,d`
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
          border-bottom: 1px solid var(--token-colorBorder, #ccc);
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
      `]}firstUpdated(){this.notification=globalThis.lablupNotification,document.addEventListener("backend-ai-credential-refresh",(()=>{this.activeCredentialList.refresh(),this.inactiveCredentialList.refresh()}),!0),this._addInputValidator(this.userIdInput)}async _preparePage(){!0!==globalThis.backendaiclient.is_admin?this.disablePage():(this.isAdmin=!0,!0===globalThis.backendaiclient.is_superadmin&&(this.isSuperAdmin=!0)),this._activeTab="user-lists",this.vfolder_max_limit.value=10,this._defaultFileName=this._getDefaultCSVFileName(),await this._runAction()}async _viewStateChanged(e){if(await this.updateComplete,!1===e)return this.activeUserList.active=!1,void(this._status="inactive");this.activeUserList.active=!0,this._status="active",void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.enableSessionLifetime=globalThis.backendaiclient.supports("session-lifetime"),this._preparePage()})):(this.enableSessionLifetime=globalThis.backendaiclient.supports("session-lifetime"),this._preparePage())}async _launchKeyPairDialog(){await this._getResourcePolicies(),this.newKeypairDialog.show(),this.userIdInput.value=""}_launchUserAddDialog(){this.newUserDialog.show()}async _getResourcePolicies(){const e=["name","default_for_unspecified","total_resource_slots","max_concurrent_sessions","max_containers_per_session"];return this.enableSessionLifetime&&e.push("max_session_lifetime"),globalThis.backendaiclient.resourcePolicy.get(null,e).then((e=>{const t=globalThis.backendaiclient.utils.gqlToObject(e.keypair_resource_policies,"name"),i=globalThis.backendaiclient.utils.gqlToList(e.keypair_resource_policies,"name");this.resource_policies=t,this.resource_policy_names=i,this.resourcePolicy.layout(!0).then((()=>{this.resourcePolicy.select(0)})),this.rateLimit.layout(!0).then((()=>{this.rateLimit.select(0)}))}))}_addKeyPair(){let e="";if(!this.userIdInput.checkValidity())return;e=this.userIdInput.value;const t=this.resourcePolicy.value,i=parseInt(this.rateLimit.value);globalThis.backendaiclient.keypair.add(e,!0,!1,t,i).then((e=>{if(e.create_keypair.ok)this.newKeypairDialog.hide(),this.notification.text=p("credential.KeypairCreated"),this.notification.show(),this.activeCredentialList.refresh();else if(e.create_keypair.msg){const t=e.create_keypair.msg.split(":")[1];this.notification.text=p("credential.UserNotFound")+t,this.notification.show()}else this.notification.text=p("dialog.ErrorOccurred"),this.notification.show()})).catch((e=>{console.log(e),e&&e.message&&(this.newKeypairDialog.hide(),this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_addUser(){const e=this.userEmailInput.value,t=""!==this.userNameInput.value?this.userNameInput.value:e.split("@")[0],i=this.userPasswordInput.value;if(!this.userEmailInput.checkValidity()||!this.userPasswordInput.checkValidity()||!this.userPasswordConfirmInput.checkValidity())return;const a={username:t,password:i,need_password_change:!1,full_name:t,description:`${t}'s Account`,is_active:!0,domain_name:"default",role:"user"};globalThis.backendaiclient.group.list().then((t=>{const i=t.groups.find((e=>"default"===e.name)).id;return Promise.resolve(globalThis.backendaiclient.user.create(e,{...a,group_ids:[i]}))})).then((e=>{this.newUserDialog.hide(),e.create_user.ok?(this.notification.text=p("credential.UserAccountCreated"),this.activeUserList.refresh()):this.notification.text=p("credential.UserAccountCreatedError"),this.notification.show(),this.userEmailInput.value="",this.userNameInput.value="",this.userPasswordInput.value="",this.userPasswordConfirmInput.value=""}))}disablePage(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll(".admin");for(let e=0;e<t.length;e++)t[e].style.display="none"}_showTab(e){var t,i,a,s;const o=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".tab-content");for(let e=0;e<o.length;e++)o[e].style.display="none";this._activeTab=e.title,(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+e.title)).style.display="block";const r=this._activeTab.substring(0,this._activeTab.length-1);let n;switch(this._activeTab){case"user-lists":n=null===(a=this.shadowRoot)||void 0===a?void 0:a.querySelector("mwc-tab[title="+this.activeUserInnerTab+"-"+r+"]"),this._showList(n);break;case"credential-lists":n=null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("mwc-tab[title="+this.activeCredentialInnerTab+"-"+r+"]"),this._showList(n)}}_showList(e){var t,i,a,s;const o=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".list-content");for(let e=0;e<o.length;e++)o[e].style.display="none";(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+e.title)).style.display="block";const r=e.title.split("-");"user"==r[1]?this.activeUserInnerTab=r[0]:this.activeCredentialInnerTab=r[0];const n=new CustomEvent("user-list-updated",{});null===(s=null===(a=this.shadowRoot)||void 0===a?void 0:a.querySelector("#"+e.title))||void 0===s||s.dispatchEvent(n)}_openExportToCsvDialog(){this._defaultFileName=this._getDefaultCSVFileName(),this.exportToCsvDialog.show()}_exportToCSV(){if(!this.exportFileNameInput.validity.valid)return;let e,t,i,a;switch(this._activeTab){case"user-lists":e=this.activeUserList.users,e.map((e=>{["password","need_password_change"].forEach((t=>delete e[t]))})),_.exportToCsv(this.exportFileNameInput.value,e);break;case"credential-lists":t=this.activeCredentialList.keypairs,i=this.inactiveCredentialList.keypairs,a=t.concat(i),a.map((e=>{["is_admin"].forEach((t=>delete e[t]))})),_.exportToCsv(this.exportFileNameInput.value,a)}this.notification.text=p("session.DownloadingCSVFile"),this.notification.show(),this.exportToCsvDialog.hide()}_getDefaultCSVFileName(){return(new Date).toISOString().substring(0,10)+"_"+(new Date).toTimeString().slice(0,8).replace(/:/gi,"-")}_toggleDropdown(e){var t;const i=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#dropdown-menu"),a=e.target;i.anchor=a,i.open||i.show()}_validatePassword1(){this.userPasswordConfirmInput.reportValidity(),this.userPasswordInput.validityTransform=(e,t)=>t.valid?{valid:t.valid,customError:!t.valid}:t.valueMissing?(this.userPasswordInput.validationMessage=p("signup.PasswordInputRequired"),{valid:t.valid,customError:!t.valid}):(this.userPasswordInput.validationMessage=p("signup.PasswordInvalid"),{valid:t.valid,customError:!t.valid})}_validatePassword2(){this.userPasswordConfirmInput.validityTransform=(e,t)=>{if(t.valid){const e=this.userPasswordInput.value===this.userPasswordConfirmInput.value;return e||(this.userPasswordConfirmInput.validationMessage=p("signup.PasswordNotMatched")),{valid:e,customError:!e}}return t.valueMissing?(this.userPasswordConfirmInput.validationMessage=p("signup.PasswordInputRequired"),{valid:t.valid,customError:!t.valid}):(this.userPasswordConfirmInput.validationMessage=p("signup.PasswordInvalid"),{valid:t.valid,customError:!t.valid})}}_validatePassword(){this._validatePassword1(),this._validatePassword2()}_togglePasswordVisibility(e){const t=e.__on,i=e.closest("div").querySelector("mwc-textfield");t?i.setAttribute("type","text"):i.setAttribute("type","password")}static gBToBytes(e=0){const t=Math.pow(10,9);return Math.round(t*e)}async _runAction(){var e,t,i;location.search.includes("action")&&(location.search.includes("add")&&await this._launchKeyPairDialog(),this._showTab(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("mwc-tab[title=credential-lists]")),null===(i=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("mwc-tab-bar.main-bar"))||void 0===i||i.setAttribute("activeindex","1"))}render(){return m`
      <link rel="stylesheet" href="resources/custom.css" />
      <lablup-activity-panel noheader narrow autowidth>
        <div slot="message">
          <h3 class="tab horizontal wrap layout">
            <mwc-tab-bar class="main-bar">
              <mwc-tab
                title="user-lists"
                label="${v("credential.Users")}"
                @click="${e=>this._showTab(e.target)}"
              ></mwc-tab>
              <mwc-tab
                title="credential-lists"
                label="${v("credential.Credentials")}"
                @click="${e=>this._showTab(e.target)}"
              ></mwc-tab>
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
                <mwc-tab
                  title="active-user-list"
                  label="${v("credential.Active")}"
                  @click="${e=>this._showList(e.target)}"
                ></mwc-tab>
                <mwc-tab
                  title="inactive-user-list"
                  label="${v("credential.Inactive")}"
                  @click="${e=>this._showList(e.target)}"
                ></mwc-tab>
              </mwc-tab-bar>
              <span class="flex"></span>
              <mwc-button
                raised
                id="add-user"
                icon="add"
                label="${v("credential.CreateUser")}"
                @click="${this._launchUserAddDialog}"
              ></mwc-button>
            </h4>
            <div>
              <backend-ai-user-list
                class="list-content"
                id="active-user-list"
                condition="active"
                ?active="${"user-lists"===this._activeTab}"
              ></backend-ai-user-list>
              <backend-ai-user-list
                class="list-content"
                id="inactive-user-list"
                style="display:none;"
                ?active="${"user-lists"===this._activeTab}"
              ></backend-ai-user-list>
            </div>
          </div>
          <div
            id="credential-lists"
            class="item tab-content card"
            style="display:none;"
          >
            <h4 class="horizontal flex center center-justified layout">
              <mwc-tab-bar class="sub-bar">
                <mwc-tab
                  title="active-credential-list"
                  label="${v("credential.Active")}"
                  @click="${e=>this._showList(e.target)}"
                ></mwc-tab>
                <mwc-tab
                  title="inactive-credential-list"
                  label="${v("credential.Inactive")}"
                  @click="${e=>this._showList(e.target)}"
                ></mwc-tab>
              </mwc-tab-bar>
              <div class="flex"></div>
              <mwc-button
                raised
                id="add-keypair"
                icon="add"
                label="${v("credential.AddCredential")}"
                @click="${this._launchKeyPairDialog}"
              ></mwc-button>
            </h4>
            <backend-ai-credential-list
              class="list-content"
              id="active-credential-list"
              condition="active"
              ?active="${"credential-lists"===this._activeTab}"
            ></backend-ai-credential-list>
            <backend-ai-credential-list
              class="list-content"
              style="display:none;"
              id="inactive-credential-list"
              condition="inactive"
              ?active="${"credential-lists"===this._activeTab}"
            ></backend-ai-credential-list>
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
              autoValidate
            ></mwc-textfield>

            <mwc-select
              id="resource-policy"
              label="${v("credential.ResourcePolicy")}"
              style="width:100%;margin:10px 0;"
            >
              ${this.resource_policy_names.map((e=>m`
                  <mwc-list-item value="${e}">${e}</mwc-list-item>
                `))}
            </mwc-select>
            <mwc-select
              id="rate-limit"
              label="${v("credential.RateLimitFor15min")}"
              style="width:100%;margin:10px 0;"
            >
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
          <mwc-button
            raised
            id="create-keypair-button"
            icon="add"
            label="${v("general.Add")}"
            fullwidth
            @click="${this._addKeyPair}"
          ></mwc-button>
        </div>
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
            validationMessage="${p("credential.validation.InvalidEmailAddress")}"
          ></mwc-textfield>
          <mwc-textfield
            type="text"
            name="user_name"
            id="id_user_name"
            label="${v("general.Username")}"
            placeholder="${p("maxLength.64chars")}"
            maxLength="64"
          ></mwc-textfield>
          <div class="horizontal flex layout">
            <mwc-textfield
              type="password"
              name="user_password"
              id="id_user_password"
              label="${v("general.Password")}"
              autoValidate
              required
              pattern=${y.passwordRegex}
              validationMessage="${p("signup.PasswordInvalid")}"
              @change="${()=>this._validatePassword()}"
              maxLength="64"
            ></mwc-textfield>
            <mwc-icon-button-toggle
              off
              onIcon="visibility"
              offIcon="visibility_off"
              @click="${e=>this._togglePasswordVisibility(e.target)}"
            ></mwc-icon-button-toggle>
          </div>
          <div class="horizontal flex layout">
            <mwc-textfield
              type="password"
              name="user_confirm"
              id="id_user_confirm"
              label="${v("general.ConfirmPassword")}"
              autoValidate
              required
              pattern=${y.passwordRegex}
              validationMessage="${p("signup.PasswordNotMatched")}"
              @change="${()=>this._validatePassword()}"
              maxLength="64"
            ></mwc-textfield>
            <mwc-icon-button-toggle
              off
              onIcon="visibility"
              offIcon="visibility_off"
              @click="${e=>this._togglePasswordVisibility(e.target)}"
            ></mwc-icon-button-toggle>
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            raised
            id="create-user-button"
            icon="add"
            label="${v("credential.CreateUser")}"
            fullwidth
            @click="${this._addUser}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="export-to-csv" fixed backdrop blockscrolling>
        <span slot="title">
          ${v("credential.ExportCSVFile")} (${this._activeTab})
        </span>

        <div slot="content" class="intro centered login-panel">
          <mwc-textfield
            id="export-file-name"
            label="${p("credential.FileName")}"
            validationMessage="${p("credential.validation.LetterNumber-_dot")}"
            value="${this._activeTab+"_"+this._defaultFileName}"
            required
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
            @click="${this._exportToCSV}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};e([t({type:Object})],k.prototype,"vfolder_max_limit",void 0),e([t({type:Array})],k.prototype,"rate_metric",void 0),e([t({type:Object})],k.prototype,"resource_policies",void 0),e([t({type:Array})],k.prototype,"resource_policy_names",void 0),e([t({type:Boolean})],k.prototype,"isAdmin",void 0),e([t({type:Boolean})],k.prototype,"isSuperAdmin",void 0),e([t({type:String})],k.prototype,"_status",void 0),e([t({type:String})],k.prototype,"new_access_key",void 0),e([t({type:String})],k.prototype,"new_secret_key",void 0),e([t({type:String})],k.prototype,"_activeTab",void 0),e([t({type:Object})],k.prototype,"notification",void 0),e([t({type:String})],k.prototype,"_defaultFileName",void 0),e([t({type:Boolean})],k.prototype,"enableSessionLifetime",void 0),e([t({type:String})],k.prototype,"activeUserInnerTab",void 0),e([t({type:String})],k.prototype,"activeCredentialInnerTab",void 0),e([i("#active-credential-list")],k.prototype,"activeCredentialList",void 0),e([i("#inactive-credential-list")],k.prototype,"inactiveCredentialList",void 0),e([i("#active-user-list")],k.prototype,"activeUserList",void 0),e([i("#rate-limit")],k.prototype,"rateLimit",void 0),e([i("#resource-policy")],k.prototype,"resourcePolicy",void 0),e([i("#id_user_email")],k.prototype,"userEmailInput",void 0),e([i("#id_new_user_id")],k.prototype,"userIdInput",void 0),e([i("#id_user_confirm")],k.prototype,"userPasswordConfirmInput",void 0),e([i("#id_user_name")],k.prototype,"userNameInput",void 0),e([i("#id_user_password")],k.prototype,"userPasswordInput",void 0),e([i("#new-keypair-dialog")],k.prototype,"newKeypairDialog",void 0),e([i("#new-user-dialog")],k.prototype,"newUserDialog",void 0),e([i("#export-to-csv")],k.prototype,"exportToCsvDialog",void 0),e([i("#export-file-name")],k.prototype,"exportFileNameInput",void 0),k=e([a("backend-ai-credential-view")],k);
