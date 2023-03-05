import{B as t,d as e,I as o,b as i,f as a,i as r,g as s,h as n,y as l,t as c,_ as d,e as p,c as h,a as u}from"./backend-ai-webui-efd2500f.js";import"./backend-ai-chart-f9dd0027.js";import"./backend-ai-session-launcher-92da01ae.js";import"./lablup-activity-panel-b5a6a642.js";import"./chart-js-74e01f0a.js";import"./lablup-progress-bar-71862d63.js";import"./mwc-switch-f419f24b.js";import"./label-06f60db1.js";import"./mwc-check-list-item-5755b77b.js";import"./slider-9a7c3779.js";import"./vaadin-grid-af1e810c.js";import"./vaadin-grid-filter-column-2949b887.js";import"./vaadin-grid-selection-column-5177358f.js";import"./dom-repeat-e7d7736f.js";import"./vaadin-item-styles-0bc384b2.js";import"./expansion-e68cadca.js";import"./radio-behavior-98d80f7f.js";import"./lablup-codemirror-56d20db9.js";
/**
 @license
 Copyright (c) 2015-2022 Lablup Inc. All rights reserved.
 */
let m=class extends t{constructor(){super(...arguments),this.condition="running",this.authenticated=!1,this.indicator=Object(),this.notification=Object(),this.requestURL="",this.queryString="",this.environment="python",this.importNotebookMessage="",this.importGithubMessage="",this.importGitlabMessage="",this.allowedGroups=[],this.allowed_folder_type=[],this.vhost="",this.vhosts=[],this.storageInfo=Object(),this._helpDescription="",this._helpDescriptionTitle="",this._helpDescriptionIcon=""}static get styles(){return[e,o,i,a,r`
        div.description {
          font-size: 14px;
          color: var(--general-sidebar-color);
        }

        #session-launcher {
          --component-width: 235px;
        }

        mwc-textfield, mwc-textarea {
          --mdc-theme-primary: var(--general-textfield-selected-color);
          width: 100%;
          margin: 10px auto;
        }

        mwc-textfield#notebook-url {
          width: 75%;
        }
        mwc-textfield.repo-url {
          width: 100%;
        }
        mwc-textfield#gitlab-default-branch-name {
          margin: inherit;
          width: 30%;
          margin-bottom: 10px;
        }

        mwc-button {
          background-image: none;
          --mdc-theme-primary: #38bd73 !important;
        }

        mwc-button.left-align {
          margin-left: auto;
        }

        mwc-select {
          margin: auto;
          width: 35%;
          margin-bottom: 10px;
          --mdc-theme-primary: var(--general-textfield-selected-color);
          --mdc-select-fill-color: transparent;
          --mdc-select-label-ink-color: rgba(0, 0, 0, 0.75);
          --mdc-select-dropdown-icon-color: var(--general-textfield-selected-color);
          --mdc-select-hover-line-color: var(--general-textfield-selected-color);
          --mdc-list-vertical-padding: 5px;
        }
        mwc-select.github-select {
          margin: inherit;
          width: 440px;
          margin-bottom: 10px;
          --mdc-theme-primary: var(--general-textfield-selected-color);
          --mdc-select-fill-color: transparent;
          --mdc-select-label-ink-color: rgba(0, 0, 0, 0.75);
          --mdc-select-dropdown-icon-color: var(--general-textfield-selected-color);
          --mdc-select-hover-line-color: var(--general-textfield-selected-color);
          --mdc-list-vertical-padding: 5px;
        }

        @media screen and (max-width: 1015px) {
          mwc-textfield#notebook-url {
            width: 85%;
            margin: 10px 0px;
          }
          mwc-textfield.repo-url {
            width: 85%;
            margin: 10px 0px;
          }
          mwc-textfield#gitlab-default-branch-name {
            width: 25%;
            margin: inherit;
          }
          mwc-button {
            width: 36px;
          }
          mwc-button > span {
            display: none;
          }
        }
      `]}firstUpdated(){this.indicator=globalThis.lablupIndicator,this.notification=globalThis.lablupNotification}async _initStorageInfo(){this.allowed_folder_type=await globalThis.backendaiclient.vfolder.list_allowed_types(),await this._getFolderList(),await fetch("resources/storage_metadata.json").then((t=>t.json())).then((t=>{const e=Object();for(const o in t.storageInfo)({}).hasOwnProperty.call(t.storageInfo,o)&&(e[o]={},"name"in t.storageInfo[o]&&(e[o].name=t.storageInfo[o].name),"description"in t.storageInfo[o]?e[o].description=t.storageInfo[o].description:e[o].description=s("data.NoStorageDescriptionFound"),"icon"in t.storageInfo[o]?e[o].icon=t.storageInfo[o].icon:e[o].icon="local.png","dialects"in t.storageInfo[o]&&t.storageInfo[o].dialects.forEach((t=>{e[t]=e[o]})));this.storageInfo=e}))}async _viewStateChanged(t){if(await this.updateComplete,!1===t)return void this.resourceMonitor.removeAttribute("active");this.resourceMonitor.setAttribute("active","true"),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._initStorageInfo(),this.authenticated=!0,this.activeConnected&&this.requestUpdate()}),!0):(this._initStorageInfo(),this.authenticated=!0,this.requestUpdate()),this.requestURL=globalThis.currentPageParams.requestURL;let e=globalThis.currentPageParams.queryString;if(e=e.substring(e.indexOf("?")+1),this.queryString=e,this.importNotebookMessage=this.queryString,this.environment=this.guessEnvironment(this.queryString),""!==e){let t="https://raw.githubusercontent.com/"+this.queryString;t=t.replace("/blob/","/"),this.fetchNotebookURLResource(t)}}getNotebookFromURL(){const t=this.notebookUrlInput.value;""!==t&&(this.queryString=this.regularizeGithubURL(t),this.fetchNotebookURLResource(this.queryString))}regularizeGithubURL(t){return t=(t=t.replace("/blob/","/")).replace("github.com","raw.githubusercontent.com")}fetchNotebookURLResource(t){this.notebookUrlInput.value=t,void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._fetchNotebookURLResource(t)}),!0):this._fetchNotebookURLResource(t)}_fetchNotebookURLResource(t){fetch(t).then((e=>{this.notification.text=s("import.ReadyToImport"),this.importNotebookMessage=this.notification.text,this.notification.show(),this.sessionLauncher.selectDefaultLanguage(!0,this.environment),this.sessionLauncher.importScript="#!/bin/sh\ncurl -O "+t,this.sessionLauncher.importFilename=t.split("/").pop(),this.sessionLauncher._launchSessionDialog()})).catch((t=>{this.notification.text=s("import.NoSuitableResourceFoundOnGivenURL"),this.importNotebookMessage=this.notification.text,this.notification.show()}))}getGitHubRepoFromURL(){var t;let e=(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#github-repo-url")).value,o="master",i="";if(".git"===e.substring(e.length-4,e.length)&&(e=e.split(".git")[0]),e.includes("/tree")){const t=(/\/tree\/[.a-zA-Z.0-9_-]+/.exec(e)||[""])[0],a=(/\/[.a-zA-Z0-9_-]+\/tree\//.exec(e)||[""])[0];e=e.replace(t,""),o=t.replace("/tree/",""),i=a.replace("/tree/","").substring(1),e=e.replace("https://github.com","https://codeload.github.com"),e=e+"/zip/"+o;const r=(/^https?(?=:\/\/)/.exec(e)||[""])[0];return["http","https"].includes(r)?this.importRepoFromURL(e,i):(this.notification.text=s("import.WrongURLType"),this.importNotebookMessage=this.notification.text,this.notification.show(),!1)}{i=e.split("/").slice(-1)[0];const t="https://api.github.com/repos"+new URL(e).pathname;return(async()=>{try{const e=await fetch(t);if(200===e.status){return(await e.json()).default_branch}if(404===e.status)throw"WrongURLType";if(403===e.status||429===e.status){const t=e.headers.get("x-ratelimit-limit"),o=e.headers.get("x-ratelimit-used"),i=e.headers.get("x-ratelimit-remaining");throw console.log(`used count: ${o}, remaining count: ${i}/total count: ${t}\nerror body: ${e.text}`),"0"===i?"GithubAPILimitError|"+o+"|"+i:"GithubAPIEtcError"}throw 500===e.status?"GithubInternalError":(console.log(`error statusCode: ${e.status}, body: ${e.text}`),"GithubAPIEtcError")}catch(t){throw t}})().then((t=>{o=t,e=e.replace("https://github.com","https://codeload.github.com"),e=e+"/zip/"+o;const a=(/^https?(?=:\/\/)/.exec(e)||[""])[0];return["http","https"].includes(a)?this.importRepoFromURL(e,i):(this.notification.text=s("import.WrongURLType"),this.importNotebookMessage=this.notification.text,this.notification.show(),!1)})).catch((t=>{switch(t){case"WrongURLType":this.notification.text=s("import.WrongURLType");break;case"GithubInternalError":this.notification.text=s("import.GithubInternalError");break;default:-1!==t.indexOf("|")?this.notification.text=s("import.GithubAPILimitError"):this.notification.text=s("import.GithubAPIEtcError")}return this.importNotebookMessage=this.notification.text,this.notification.show(),!1}))}}getGitlabRepoFromURL(){var t,e;let o=(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#gitlab-repo-url")).value,i="master";const a=(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#gitlab-default-branch-name")).value;a.length>0&&(i=a);let r="";if(".git"===o.substring(o.length-4,o.length)&&(o=o.split(".git")[0]),o.includes("/tree")){const t=new URL(o).pathname.split("/");r=t[2],i=t[t.length-1],o=o.replace("/tree/","/archive/"),o+="/"+r+"-"+i+".zip";const e=(/^https?(?=:\/\/)/.exec(o)||[""])[0];return["http","https"].includes(e)?this.importRepoFromURL(o,r):(this.notification.text=s("import.WrongURLType"),this.importNotebookMessage=this.notification.text,this.notification.show(),!1)}{r=o.split("/").slice(-1)[0],o=o+"/-/archive/"+i+"/"+r+"-"+i+".zip";const t=(/^https?(?=:\/\/)/.exec(o)||[""])[0];return["http","https"].includes(t)?this.importRepoFromURL(o,r):(this.notification.text=s("import.WrongURLType"),this.importGitlabMessage=this.notification.text,this.notification.show(),!1)}}async importRepoFromURL(t,e){const o={cpu:1,mem:"0.5g"};o.domain=globalThis.backendaiclient._config.domainName,o.group_name=globalThis.backendaiclient.current_group;const i=await this.indicator.start("indeterminate");return i.set(10,s("import.Preparing")),e=await this._checkFolderNameAlreadyExists(e,t),await this._addFolderWithName(e,t),i.set(20,s("import.FolderCreated")),o.mounts=[e],o.bootstrap_script="#!/bin/sh\ncurl -o repo.zip "+t+"\ncd /home/work/"+e+"\nunzip -u /home/work/repo.zip",globalThis.backendaiclient.get_resource_slots().then((t=>(i.set(50,s("import.Downloading")),globalThis.backendaiclient.createIfNotExists(globalThis.backendaiclient._config.default_import_environment,null,o,6e4,void 0)))).then((async t=>{i.set(80,s("import.CleanUpImportTask")),await globalThis.backendaiclient.destroy(t.sessionId),i.set(100,s("import.ImportFinished")),i.end(1e3)})).catch((t=>{this.notification.text=n.relieve(t.title),this.notification.detail=t.message,this.notification.show(!0,t),i.end(1e3)}))}async _addFolderWithName(t,e){var o,i;let a=(await globalThis.backendaiclient.vfolder.list_hosts()).default;return a=e.includes("github.com/")?(null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("#github-add-folder-host")).value:(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#gitlab-add-folder-host")).value,t=await this._checkFolderNameAlreadyExists(t,e),globalThis.backendaiclient.vfolder.create(t,a,"","general","rw").then((o=>{e.includes("github.com/")?this.importNotebookMessage=s("import.FolderName")+t:this.importGitlabMessage=s("import.FolderName")+t})).catch((t=>{console.log(t),t&&t.message&&(this.notification.text=n.relieve(t.title),this.notification.detail=t.message,this.notification.show(!0,t))}))}async _checkFolderNameAlreadyExists(t,e){const o=(await globalThis.backendaiclient.vfolder.list()).map((function(t){return t.name}));if(o.includes(t)){this.notification.text=s("import.FolderAlreadyExists"),e.includes("github.com/")?this.importNotebookMessage=this.notification.text:this.importGitlabMessage=this.notification.text,this.notification.show();let i=1,a=t;for(;o.includes(a);)a=t+"_"+i,i++;t=a}return t}guessEnvironment(t){return t.includes("tensorflow")||t.includes("keras")||t.includes("Keras")?"index.docker.io/lablup/python-tensorflow":t.includes("pytorch")?"index.docker.io/lablup/python-pytorch":t.includes("mxnet")?"index.docker.io/lablup/python-mxnet":"index.docker.io/lablup/python-ff"}createNotebookBadge(){var t;const e=(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#notebook-badge-url")).value,o=this.regularizeGithubURL(e).replace("https://raw.githubusercontent.com/","");let i="";if(""===e)this.notification.text=s("import.NoNotebookCode"),this.notification.show(),this.notebookBadgeCodeInput.value="",this.notebookBadgeCodeMarkdownInput.value="";else{globalThis.isElectron?i="https://cloud.backend.ai/github?":(i=window.location.protocol+"//"+window.location.hostname,window.location.port&&(i=i+":"+window.location.port),i+="/github?");const t=`<a href="${i+o}"><img src="https://www.backend.ai/assets/badge.svg" /></a>`,e=`[![Run on Backend.AI](https://www.backend.ai/assets/badge.svg)](${i+o})`;this.notebookBadgeCodeInput.value=t,this.notebookBadgeCodeMarkdownInput.value=e}}_copyTextArea(t){let e="";if("value"in t.target&&(e=t.target.value),""!==e)if(0===e.length)this.notification.text=s("import.NoNotebookCode"),this.notification.show();else if(void 0!==navigator.clipboard)navigator.clipboard.writeText(e).then((()=>{this.notification.text=s("import.NotebookBadgeCodeCopied"),this.notification.show()}),(t=>{console.error(s("import.CouldNotCopyText"),t)}));else{const t=document.createElement("input");t.type="text",t.value=e,document.body.appendChild(t),t.select(),document.execCommand("copy"),document.body.removeChild(t),this.notification.text=s("import.NotebookBadgeCodeCopied"),this.notification.show()}}async _getFolderList(){const t=await globalThis.backendaiclient.vfolder.list_hosts();if(this.vhosts=t.allowed,this.vhost=t.default,this.allowed_folder_type.includes("group")){const t=await globalThis.backendaiclient.group.list();this.allowedGroups=t.groups}}urlTextfieldChanged(t,e,o){var i;const a=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector(`#${e}`);""!==t.target.value&&t.currentTarget.checkValidity()?(a.removeAttribute("disabled"),this.setAttribute(o,"")):(this.notification.text=s("import.WrongURLType"),a.setAttribute("disabled","true"),this.setAttribute(o,""===t.target.value?"":s("import.WrongURLType")),this.notification.show()),this.requestUpdate()}render(){return l`
      <link rel="stylesheet" href="resources/custom.css">
      <lablup-activity-panel title="${c("import.ImportNotebook")}" elevation="1" horizontalsize="2x">
        <div slot="message">
          <div class="horizontal wrap layout center">
            <mwc-textfield id="notebook-url" label="${c("import.NotebookURL")}"
                           autoValidate validationMessage="${s("import.WrongURLType")}"
                           pattern="^(https?):\/\/([\\w\.\/\-]{1,})\.ipynb$"
                           maxLength="2048" placeholder="${c("maxLength.2048chars")}"
                           @change="${t=>this.urlTextfieldChanged(t,"import-notebook-button","importNotebookMessage")}"></mwc-textfield>
            <mwc-button id="import-notebook-button" disabled icon="cloud_download" @click="${()=>this.getNotebookFromURL()}">
              <span>${c("import.GetAndRunNotebook")}</span>
            </mwc-button>
          </div>
          ${this.importNotebookMessage}
        </div>
      </lablup-activity-panel>
      <backend-ai-session-launcher mode="import" location="import" hideLaunchButton
      id="session-launcher" ?active="${!0===this.active}"
      .newSessionDialogTitle="${c("session.launcher.StartImportedNotebook")}"></backend-ai-session-launcher>
      <div class="horizontal wrap layout">
        <lablup-activity-panel title="${c("summary.ResourceStatistics")}" elevation="1" width="350" height="490" narrow>
          <div slot="message">
              <backend-ai-resource-monitor location="summary" id="resource-monitor" ?active="${!0===this.active}" direction="vertical"></backend-ai-resource-monitor>
          </div>
        </lablup-activity-panel>
        <lablup-activity-panel title="${c("import.CreateNotebookButton")}" elevation="1" height="490">
          <div slot="message">
            <div class="vertical wrap layout center description">
              ${c("import.YouCanCreateNotebookCode")}
              <img src="/resources/badge.svg" style="margin-top:5px;margin-bottom:5px;"/>
              <mwc-textfield id="notebook-badge-url" label="${c("import.NotebookBadgeURL")}"
                             autoValidate validationMessage="${s("import.WrongURLType")}"
                             pattern="^(https?):\/\/([\\w\.\/\-]{1,})\.ipynb$"
                             maxLength="2048" placeholder="${c("maxLength.2048chars")}"
                             @change="${t=>this.urlTextfieldChanged(t,"create-notebook-button")}"></mwc-textfield>
              <mwc-button id="create-notebook-button" disabled fullwidth @click="${()=>this.createNotebookBadge()}" icon="code">${c("import.CreateButtonCode")}</mwc-button>
              <mwc-textarea id="notebook-badge-code" label="${c("import.NotebookBadgeCodeHTML")}" @click="${t=>this._copyTextArea(t)}"></mwc-textarea>
              <mwc-textarea id="notebook-badge-code-markdown" label="${c("import.NotebookBadgeCodeMarkdown")}" @click="${t=>this._copyTextArea(t)}"></mwc-textarea>
            </div>
          </div>
        </lablup-activity-panel>
      </div>
      <div class="horizontal wrap layout">
        <lablup-activity-panel title="${c("import.ImportGithubRepo")}" elevation="1" horizontalsize="2x">
          <div slot="message">
            <div class="description">
              <p>${c("import.RepoWillBeFolder")}</p>
            </div>
            <div class="horizontal wrap layout center">
              <mwc-textfield id="github-repo-url" class="repo-url" label="${c("import.GitHubURL")}"
                             autoValidate validationMessage="${s("import.WrongURLType")}"
                             pattern="^(https?):\/\/github\.com\/([\\w\.\/\-]{1,})$"
                             maxLength="2048" placeholder="${c("maxLength.2048chars")}"
                             @change="${t=>this.urlTextfieldChanged(t,"import-github-repo-button","importGithubMessage")}"></mwc-textfield>
              <mwc-select class="github-select" id="github-add-folder-host" label="${c("data.Host")}">
                ${this.vhosts.map(((t,e)=>l`
                <mwc-list-item hasMeta value="${t}" ?selected="${t===this.vhost}">
                    <span>${t}</span>
                </mwc-list-item>
                `))}
              </mwc-select>
              <mwc-button id="import-github-repo-button" disabled class="left-align" icon="cloud_download" @click="${()=>this.getGitHubRepoFromURL()}">
                <span>${c("import.GetToFolder")}</span>
              </mwc-button>
            </div>
            ${this.importGithubMessage}
          </div>
        </lablup-activity-panel>
      </div>
      <div class="horizontal wrap layout">
        <lablup-activity-panel title="${c("import.ImportGitlabRepo")}" elevation="1" horizontalsize="2x">
          <div slot="message">
            <div class="description">
              <p>${c("import.GitlabRepoWillBeFolder")}</p>
            </div>
            <div class="horizontal wrap layout center">
              <mwc-textfield id="gitlab-repo-url" class="repo-url" label="${c("import.GitlabURL")}"
                             autoValidate validationMessage="${s("import.WrongURLType")}"
                             pattern="^(https?):\/\/gitlab\.com\/([\\w\.\/\-]{1,})$"
                             maxLength="2048" placeholder="${c("maxLength.2048chars")}"
                             @change="${t=>this.urlTextfieldChanged(t,"import-gitlab-repo-button","importGitlabMessage")}"></mwc-textfield>
              <mwc-textfield id="gitlab-default-branch-name" label="${c("import.GitlabDefaultBranch")}"
                             maxLength="200" placeholder="${c("maxLength.200chars")}"></mwc-textfield>
              <mwc-select id="gitlab-add-folder-host" label="${c("data.Host")}">
                ${this.vhosts.map(((t,e)=>l`
                <mwc-list-item hasMeta value="${t}" ?selected="${t===this.vhost}">
                    <span>${t}</span>
                </mwc-list-item>
                `))}
              </mwc-select>
              <mwc-button id="import-gitlab-repo-button" disabled class="left-align" icon="cloud_download" @click="${()=>this.getGitlabRepoFromURL()}">
                <span>${c("import.GetToFolder")}</span>
              </mwc-button>
            </div>
            ${this.importGitlabMessage}
          </div>
        </lablup-activity-panel>
      </div>
`}};d([p({type:String})],m.prototype,"condition",void 0),d([p({type:Boolean})],m.prototype,"authenticated",void 0),d([p({type:Object})],m.prototype,"indicator",void 0),d([p({type:Object})],m.prototype,"notification",void 0),d([p({type:String})],m.prototype,"requestURL",void 0),d([p({type:String})],m.prototype,"queryString",void 0),d([p({type:String})],m.prototype,"environment",void 0),d([p({type:String})],m.prototype,"importNotebookMessage",void 0),d([p({type:String})],m.prototype,"importGithubMessage",void 0),d([p({type:String})],m.prototype,"importGitlabMessage",void 0),d([p({type:Array})],m.prototype,"allowedGroups",void 0),d([p({type:Array})],m.prototype,"allowed_folder_type",void 0),d([p({type:String})],m.prototype,"vhost",void 0),d([p({type:Array})],m.prototype,"vhosts",void 0),d([p({type:Object})],m.prototype,"storageInfo",void 0),d([p({type:String})],m.prototype,"_helpDescription",void 0),d([p({type:String})],m.prototype,"_helpDescriptionTitle",void 0),d([p({type:String})],m.prototype,"_helpDescriptionIcon",void 0),d([h("#loading-spinner")],m.prototype,"spinner",void 0),d([h("#resource-monitor")],m.prototype,"resourceMonitor",void 0),d([h("#session-launcher")],m.prototype,"sessionLauncher",void 0),d([h("#notebook-url")],m.prototype,"notebookUrlInput",void 0),d([h("#notebook-badge-code")],m.prototype,"notebookBadgeCodeInput",void 0),d([h("#notebook-badge-code-markdown")],m.prototype,"notebookBadgeCodeMarkdownInput",void 0),m=d([u("backend-ai-import-view")],m);var b=m;export{b as default};
