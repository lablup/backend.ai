import{_ as i,c as t,t as e,B as o,a,I as s,b as l,d as n,e as c,i as d,C as r,f as h,g as f,h as g,k as v}from"./backend-ai-webui-CiZihJrO.js";let p=class extends o{constructor(){super(...arguments),this.webUIShell=Object(),this.clientConfig=Object(),this.client=Object(),this.notification=Object(),this.successDialog=Object(),this.failDialog=Object()}static get styles(){return[a,s,l,n,c,d`
        mwc-textfield {
          width: 100%;
          --mdc-text-field-fill-color: var(--general-menu-color);
          --mdc-theme-primary: var(--general-textfield-selected-color);
          --mdc-typography-font-family: var(--token-fontFamily);
        }
      `]}_initClient(i){var t,e;this.webUIShell=document.querySelector("#webui-shell"),this.notification=globalThis.lablupNotification,this.successDialog=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#verification-success-dialog"),this.failDialog=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#verification-fail-dialog"),this.clientConfig=new r("","",i,"SESSION"),this.client=new h(this.clientConfig,"Backend.AI Web UI."),this.successDialog.addEventListener("didHide",(()=>{this._redirectToLoginPage()})),this.failDialog.addEventListener("didHide",(()=>{this._redirectToLoginPage()}))}_redirectToLoginPage(){window.location.href="/"}async verify(i){const t=new URLSearchParams(window.location.search).get("verification_code");if(this._initClient(i),t)try{await this.client.cloud.verify_email(t),this.successDialog.show()}catch(i){this.notification.text=f("signUp.VerificationError"),this.notification.show(),window.setTimeout((()=>this.failDialog.show()),100)}else this.failDialog.show()}async sendVerificationCode(){var i;const t=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#email");if(t.value&&t.validity.valid)try{await this.client.cloud.send_verification_email(t.value),this.notification.text=f("signUp.EmailSent"),this.notification.show()}catch(i){this.notification.text=i.message||f("signUp.SendError"),this.notification.show()}}render(){return v`
      <link rel="stylesheet" href="resources/custom.css" />
      <backend-ai-dialog
        id="verification-success-dialog"
        fixed
        backdrop
        blockscrolling
        persistent
        style="padding:0;"
      >
        <span slot="title">${g("signUp.EmailVerified")}</span>

        <div slot="content">
          <div class="horizontal layout center">
            <p style="width:256px;">${g("signUp.EmailVerifiedMessage")}</p>
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            unelevated
            fullwidth
            label="${g("login.Login")}"
            @click="${()=>this._redirectToLoginPage()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>

      <backend-ai-dialog
        id="verification-fail-dialog"
        fixed
        backdrop
        blockscrolling
        persistent
        style="padding:0;"
      >
        <span slot="title">${g("signUp.EmailVerificationFailed")}</span>

        <div slot="content">
          <div class="horizontal layout center">
            <p style="width:256px;">
              ${g("signUp.EmailVerificationFailedMessage")}
            </p>
          </div>
          <div style="margin:20px;">
            <mwc-textfield
              id="email"
              label="${g("data.explorer.EnterEmailAddress")}"
              autofocus
              auto-validate
              validationMessage="${g("signUp.InvalidEmail")}"
              pattern="^[A-Z0-9a-z#-_]+@.+\\..+$"
              maxLength="64"
              placeholder="${g("maxLength.64chars")}"
            ></mwc-textfield>
            <div style="height:1em"></div>
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            unelevated
            fullwidth
            label="${g("signUp.SendEmail")}"
            @click="${()=>this.sendVerificationCode()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};i([t({type:Object})],p.prototype,"webUIShell",void 0),i([t({type:Object})],p.prototype,"clientConfig",void 0),i([t({type:Object})],p.prototype,"client",void 0),i([t({type:Object})],p.prototype,"notification",void 0),i([t({type:Object})],p.prototype,"successDialog",void 0),i([t({type:Object})],p.prototype,"failDialog",void 0),p=i([e("backend-ai-email-verification-view")],p);
