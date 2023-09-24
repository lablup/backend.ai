import{j as e,r as t,i,T as s,D as n,P as o,k as a,_ as r,n as l,b as c,e as d,B as p,c as h,I as u,a as m,f as g,l as b,x as _,g as v,t as f,o as y,m as w,d as k}from"./backend-ai-webui-75df15ed.js";import{J as x}from"./json_to_csv-35c9e191.js";import"./backend-ai-resource-monitor-21ef3974.js";import"./backend-ai-session-launcher-676818a7.js";import"./backend-ai-list-status-fa13c15b.js";import"./lablup-grid-sort-filter-column-54638b7b.js";import"./lablup-progress-bar-b230f3e3.js";import{i as A}from"./vaadin-grid-461d199a.js";import"./vaadin-grid-filter-column-2b22f222.js";import"./vaadin-grid-selection-column-29a490b5.js";import"./vaadin-grid-sort-column-d722536e.js";import"./vaadin-iconset-c8fcdcfd.js";import"./lablup-activity-panel-86e1deef.js";import"./mwc-formfield-5cf6c683.js";import"./mwc-tab-bar-45ba859c.js";import"./mwc-switch-13f7c132.js";import"./lablup-codemirror-59c15e56.js";import"./slider-3f740add.js";import"./mwc-check-list-item-5618f22b.js";import"./media-query-controller-bc25d693.js";import"./dir-utils-f5050166.js";
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */var S;!function(e){e[e.EOS=0]="EOS",e[e.Text=1]="Text",e[e.Incomplete=2]="Incomplete",e[e.ESC=3]="ESC",e[e.Unknown=4]="Unknown",e[e.SGR=5]="SGR",e[e.OSCURL=6]="OSCURL"}(S||(S={}));var T=function(){function e(){this.VERSION="4.0.3",this.setup_palettes(),this._use_classes=!1,this._escape_for_html=!0,this.bold=!1,this.fg=this.bg=null,this._buffer="",this._url_whitelist={http:1,https:1}}return Object.defineProperty(e.prototype,"use_classes",{get:function(){return this._use_classes},set:function(e){this._use_classes=e},enumerable:!0,configurable:!0}),Object.defineProperty(e.prototype,"escape_for_html",{get:function(){return this._escape_for_html},set:function(e){this._escape_for_html=e},enumerable:!0,configurable:!0}),Object.defineProperty(e.prototype,"url_whitelist",{get:function(){return this._url_whitelist},set:function(e){this._url_whitelist=e},enumerable:!0,configurable:!0}),e.prototype.setup_palettes=function(){var e=this;this.ansi_colors=[[{rgb:[0,0,0],class_name:"ansi-black"},{rgb:[187,0,0],class_name:"ansi-red"},{rgb:[0,187,0],class_name:"ansi-green"},{rgb:[187,187,0],class_name:"ansi-yellow"},{rgb:[0,0,187],class_name:"ansi-blue"},{rgb:[187,0,187],class_name:"ansi-magenta"},{rgb:[0,187,187],class_name:"ansi-cyan"},{rgb:[255,255,255],class_name:"ansi-white"}],[{rgb:[85,85,85],class_name:"ansi-bright-black"},{rgb:[255,85,85],class_name:"ansi-bright-red"},{rgb:[0,255,0],class_name:"ansi-bright-green"},{rgb:[255,255,85],class_name:"ansi-bright-yellow"},{rgb:[85,85,255],class_name:"ansi-bright-blue"},{rgb:[255,85,255],class_name:"ansi-bright-magenta"},{rgb:[85,255,255],class_name:"ansi-bright-cyan"},{rgb:[255,255,255],class_name:"ansi-bright-white"}]],this.palette_256=[],this.ansi_colors.forEach((function(t){t.forEach((function(t){e.palette_256.push(t)}))}));for(var t=[0,95,135,175,215,255],i=0;i<6;++i)for(var s=0;s<6;++s)for(var n=0;n<6;++n){var o={rgb:[t[i],t[s],t[n]],class_name:"truecolor"};this.palette_256.push(o)}for(var a=8,r=0;r<24;++r,a+=10){var l={rgb:[a,a,a],class_name:"truecolor"};this.palette_256.push(l)}},e.prototype.escape_txt_for_html=function(e){return e.replace(/[&<>]/gm,(function(e){return"&"===e?"&amp;":"<"===e?"&lt;":">"===e?"&gt;":void 0}))},e.prototype.append_buffer=function(e){var t=this._buffer+e;this._buffer=t},e.prototype.__makeTemplateObject=function(e,t){return Object.defineProperty?Object.defineProperty(e,"raw",{value:t}):e.raw=t,e},e.prototype.get_next_packet=function(){var e={kind:S.EOS,text:"",url:""},t=this._buffer.length;if(0==t)return e;var i,s,n,o,a=this._buffer.indexOf("");if(-1==a)return e.kind=S.Text,e.text=this._buffer,this._buffer="",e;if(a>0)return e.kind=S.Text,e.text=this._buffer.slice(0,a),this._buffer=this._buffer.slice(a),e;if(0==a){if(1==t)return e.kind=S.Incomplete,e;var r=this._buffer.charAt(1);if("["!=r&&"]"!=r)return e.kind=S.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;if("["==r){if(this._csi_regex||(this._csi_regex=$(this.__makeTemplateObject(["\n                        ^                           # beginning of line\n                                                    #\n                                                    # First attempt\n                        (?:                         # legal sequence\n                          [                      # CSI\n                          ([<-?]?)              # private-mode char\n                          ([d;]*)                    # any digits or semicolons\n                          ([ -/]?               # an intermediate modifier\n                          [@-~])                # the command\n                        )\n                        |                           # alternate (second attempt)\n                        (?:                         # illegal sequence\n                          [                      # CSI\n                          [ -~]*                # anything legal\n                          ([\0-:])              # anything illegal\n                        )\n                    "],["\n                        ^                           # beginning of line\n                                                    #\n                                                    # First attempt\n                        (?:                         # legal sequence\n                          \\x1b\\[                      # CSI\n                          ([\\x3c-\\x3f]?)              # private-mode char\n                          ([\\d;]*)                    # any digits or semicolons\n                          ([\\x20-\\x2f]?               # an intermediate modifier\n                          [\\x40-\\x7e])                # the command\n                        )\n                        |                           # alternate (second attempt)\n                        (?:                         # illegal sequence\n                          \\x1b\\[                      # CSI\n                          [\\x20-\\x7e]*                # anything legal\n                          ([\\x00-\\x1f:])              # anything illegal\n                        )\n                    "]))),null===(d=this._buffer.match(this._csi_regex)))return e.kind=S.Incomplete,e;if(d[4])return e.kind=S.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;""!=d[1]||"m"!=d[3]?e.kind=S.Unknown:e.kind=S.SGR,e.text=d[2];var l=d[0].length;return this._buffer=this._buffer.slice(l),e}if("]"==r){if(t<4)return e.kind=S.Incomplete,e;if("8"!=this._buffer.charAt(2)||";"!=this._buffer.charAt(3))return e.kind=S.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;this._osc_st||(this._osc_st=(i=this.__makeTemplateObject(["\n                        (?:                         # legal sequence\n                          (\\)                    # ESC                           |                           # alternate\n                          ()                      # BEL (what xterm did)\n                        )\n                        |                           # alternate (second attempt)\n                        (                           # illegal sequence\n                          [\0-]                 # anything illegal\n                          |                           # alternate\n                          [\b-]                 # anything illegal\n                          |                           # alternate\n                          [-]                 # anything illegal\n                        )\n                    "],["\n                        (?:                         # legal sequence\n                          (\\x1b\\\\)                    # ESC \\\n                          |                           # alternate\n                          (\\x07)                      # BEL (what xterm did)\n                        )\n                        |                           # alternate (second attempt)\n                        (                           # illegal sequence\n                          [\\x00-\\x06]                 # anything illegal\n                          |                           # alternate\n                          [\\x08-\\x1a]                 # anything illegal\n                          |                           # alternate\n                          [\\x1c-\\x1f]                 # anything illegal\n                        )\n                    "]),s=i.raw[0],n=/^\s+|\s+\n|\s*#[\s\S]*?\n|\n/gm,o=s.replace(n,""),new RegExp(o,"g"))),this._osc_st.lastIndex=0;var c=this._osc_st.exec(this._buffer);if(null===c)return e.kind=S.Incomplete,e;if(c[3])return e.kind=S.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;var d,p=this._osc_st.exec(this._buffer);if(null===p)return e.kind=S.Incomplete,e;if(p[3])return e.kind=S.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;if(this._osc_regex||(this._osc_regex=$(this.__makeTemplateObject(["\n                        ^                           # beginning of line\n                                                    #\n                        ]8;                    # OSC Hyperlink\n                        [ -:<-~]*       # params (excluding ;)\n                        ;                           # end of params\n                        ([!-~]{0,512})        # URL capture\n                        (?:                         # ST\n                          (?:\\)                  # ESC                           |                           # alternate\n                          (?:)                    # BEL (what xterm did)\n                        )\n                        ([!-~]+)              # TEXT capture\n                        ]8;;                   # OSC Hyperlink End\n                        (?:                         # ST\n                          (?:\\)                  # ESC                           |                           # alternate\n                          (?:)                    # BEL (what xterm did)\n                        )\n                    "],["\n                        ^                           # beginning of line\n                                                    #\n                        \\x1b\\]8;                    # OSC Hyperlink\n                        [\\x20-\\x3a\\x3c-\\x7e]*       # params (excluding ;)\n                        ;                           # end of params\n                        ([\\x21-\\x7e]{0,512})        # URL capture\n                        (?:                         # ST\n                          (?:\\x1b\\\\)                  # ESC \\\n                          |                           # alternate\n                          (?:\\x07)                    # BEL (what xterm did)\n                        )\n                        ([\\x21-\\x7e]+)              # TEXT capture\n                        \\x1b\\]8;;                   # OSC Hyperlink End\n                        (?:                         # ST\n                          (?:\\x1b\\\\)                  # ESC \\\n                          |                           # alternate\n                          (?:\\x07)                    # BEL (what xterm did)\n                        )\n                    "]))),null===(d=this._buffer.match(this._osc_regex)))return e.kind=S.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;e.kind=S.OSCURL,e.url=d[1],e.text=d[2];l=d[0].length;return this._buffer=this._buffer.slice(l),e}}},e.prototype.ansi_to_html=function(e){this.append_buffer(e);for(var t=[];;){var i=this.get_next_packet();if(i.kind==S.EOS||i.kind==S.Incomplete)break;i.kind!=S.ESC&&i.kind!=S.Unknown&&(i.kind==S.Text?t.push(this.transform_to_html(this.with_state(i))):i.kind==S.SGR?this.process_ansi(i):i.kind==S.OSCURL&&t.push(this.process_hyperlink(i)))}return t.join("")},e.prototype.with_state=function(e){return{bold:this.bold,fg:this.fg,bg:this.bg,text:e.text}},e.prototype.process_ansi=function(e){for(var t=e.text.split(";");t.length>0;){var i=t.shift(),s=parseInt(i,10);if(isNaN(s)||0===s)this.fg=this.bg=null,this.bold=!1;else if(1===s)this.bold=!0;else if(22===s)this.bold=!1;else if(39===s)this.fg=null;else if(49===s)this.bg=null;else if(s>=30&&s<38)this.fg=this.ansi_colors[0][s-30];else if(s>=40&&s<48)this.bg=this.ansi_colors[0][s-40];else if(s>=90&&s<98)this.fg=this.ansi_colors[1][s-90];else if(s>=100&&s<108)this.bg=this.ansi_colors[1][s-100];else if((38===s||48===s)&&t.length>0){var n=38===s,o=t.shift();if("5"===o&&t.length>0){var a=parseInt(t.shift(),10);a>=0&&a<=255&&(n?this.fg=this.palette_256[a]:this.bg=this.palette_256[a])}if("2"===o&&t.length>2){var r=parseInt(t.shift(),10),l=parseInt(t.shift(),10),c=parseInt(t.shift(),10);if(r>=0&&r<=255&&l>=0&&l<=255&&c>=0&&c<=255){var d={rgb:[r,l,c],class_name:"truecolor"};n?this.fg=d:this.bg=d}}}}},e.prototype.transform_to_html=function(e){var t=e.text;if(0===t.length)return t;if(this._escape_for_html&&(t=this.escape_txt_for_html(t)),!e.bold&&null===e.fg&&null===e.bg)return t;var i=[],s=[],n=e.fg,o=e.bg;e.bold&&i.push("font-weight:bold"),this._use_classes?(n&&("truecolor"!==n.class_name?s.push(n.class_name+"-fg"):i.push("color:rgb("+n.rgb.join(",")+")")),o&&("truecolor"!==o.class_name?s.push(o.class_name+"-bg"):i.push("background-color:rgb("+o.rgb.join(",")+")"))):(n&&i.push("color:rgb("+n.rgb.join(",")+")"),o&&i.push("background-color:rgb("+o.rgb+")"));var a="",r="";return s.length&&(a=' class="'+s.join(" ")+'"'),i.length&&(r=' style="'+i.join(";")+'"'),"<span"+r+a+">"+t+"</span>"},e.prototype.process_hyperlink=function(e){var t=e.url.split(":");return t.length<1?"":this._url_whitelist[t[0]]?'<a href="'+this.escape_txt_for_html(e.url)+'">'+this.escape_txt_for_html(e.text)+"</a>":""},e}();function $(e){var t=e.raw[0].replace(/^\s+|\s+\n|\s*#[\s\S]*?\n|\n/gm,"");return new RegExp(t)}t("vaadin-grid-tree-toggle",i`
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
const C=document.createElement("template");C.innerHTML="\n  <style>\n    @font-face {\n      font-family: \"vaadin-grid-tree-icons\";\n      src: url(data:application/font-woff;charset=utf-8;base64,d09GRgABAAAAAAQkAA0AAAAABrwAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAABGRlRNAAAECAAAABoAAAAcgHwa6EdERUYAAAPsAAAAHAAAAB4AJwAOT1MvMgAAAZQAAAA/AAAAYA8TBIJjbWFwAAAB8AAAAFUAAAFeGJvXWmdhc3AAAAPkAAAACAAAAAgAAAAQZ2x5ZgAAAlwAAABLAAAAhIrPOhFoZWFkAAABMAAAACsAAAA2DsJI02hoZWEAAAFcAAAAHQAAACQHAgPHaG10eAAAAdQAAAAZAAAAHAxVAgBsb2NhAAACSAAAABIAAAASAIAAVG1heHAAAAF8AAAAGAAAACAACgAFbmFtZQAAAqgAAAECAAACTwflzbdwb3N0AAADrAAAADYAAABZQ7Ajh3icY2BkYGAA4twv3Vfi+W2+MnCzMIDANSOmbGSa2YEZRHEwMIEoAAoiB6sAeJxjYGRgYD7w/wADAwsDCDA7MDAyoAI2AFEEAtIAAAB4nGNgZGBg4GBgZgDRDAxMDGgAAAGbABB4nGNgZp7JOIGBlYGBaSbTGQYGhn4IzfiawZiRkwEVMAqgCTA4MDA+38d84P8BBgdmIAapQZJVYGAEAGc/C54AeJxjYYAAxlAIzQTELAwMBxgZGB0ACy0BYwAAAHicY2BgYGaAYBkGRgYQiADyGMF8FgYbIM3FwMHABISMDArP9/3/+/8/WJXC8z0Q9v8nEp5gHVwMMMAIMo+RDYiZoQJMQIKJARUA7WBhGN4AACFKDtoAAAAAAAAAAAgACAAQABgAJgA0AEIAAHichYvBEYBADAKBVHBjBT4swl9KS2k05o0XHd/yW1hAfBFwCv9sIlJu3nZaNS3PXAaXXHI8Lge7DlzF7C1RgXc7xkK6+gvcD2URmQB4nK2RQWoCMRiFX3RUqtCli65yADModOMBLLgQSqHddRFnQghIAnEUvEA3vUUP0LP0Fj1G+yb8R5iEhO9/ef/7FwFwj28o9EthiVp4hBlehcfUP4Ur8o/wBAv8CU+xVFvhOR7UB7tUdUdlVRJ6HnHWTnhM/V24In8JT5j/KzzFSi2E53hUz7jCcrcIiDDwyKSW1JEct2HdIPH1DFytbUM0PofWdNk5E5oUqb/Q6HHBiVGZpfOXkyUMEj5IyBuNmYZQjBobfsuassvnkKLe1OuBBj0VQ8cRni2xjLWsHaM0jrjx3peYA0/vrdmUYqe9iy7bzrX6eNP7Jh1SijX+AaUVbB8AAHicY2BiwA84GBgYmRiYGJkZmBlZGFkZ2djScyoLMgzZS/MyDQwMwLSruZMzlHaB0q4A76kLlwAAAAEAAf//AA94nGNgZGBg4AFiMSBmYmAEQnYgZgHzGAAD6wA2eJxjYGBgZACCKxJigiD6mhFTNowGACmcA/8AAA==) format('woff');\n      font-weight: normal;\n      font-style: normal;\n    }\n  </style>\n",document.head.appendChild(C.content);class I extends(s(n(o))){static get template(){return a`
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
    `}static get is(){return"vaadin-grid-tree-toggle"}static get properties(){return{level:{type:Number,value:0,observer:"_levelChanged"},leaf:{type:Boolean,value:!1,reflectToAttribute:!0},expanded:{type:Boolean,value:!1,reflectToAttribute:!0,notify:!0}}}ready(){super.ready(),this.addEventListener("click",(e=>this._onClick(e)))}_onClick(e){this.leaf||A(e.target)||e.target instanceof HTMLLabelElement||(e.preventDefault(),this.expanded=!this.expanded)}_levelChanged(e){const t=Number(e).toString();this.style.setProperty("---level",t)}}var D;customElements.define(I.is,I);let E=D=class extends p{constructor(){super(),this.active=!1,this.condition="running",this.jobs=Object(),this.compute_sessions=[],this.filterAccessKey="",this.sessionNameField="name",this.appSupportList=[],this.appTemplate=Object(),this.imageInfo=Object(),this._boundControlRenderer=this.controlRenderer.bind(this),this._boundConfigRenderer=this.configRenderer.bind(this),this._boundUsageRenderer=this.usageRenderer.bind(this),this._boundReservationRenderer=this.reservationRenderer.bind(this),this._boundIdleChecksHeaderderer=this.idleChecksHeaderRenderer.bind(this),this._boundIdleChecksRenderer=this.idleChecksRenderer.bind(this),this._boundAgentRenderer=this.agentRenderer.bind(this),this._boundSessionInfoRenderer=this.sessionInfoRenderer.bind(this),this._boundArchitectureRenderer=this.architectureRenderer.bind(this),this._boundCheckboxRenderer=this.checkboxRenderer.bind(this),this._boundUserInfoRenderer=this.userInfoRenderer.bind(this),this._boundStatusRenderer=this.statusRenderer.bind(this),this._boundSessionTypeRenderer=this.sessionTypeRenderer.bind(this),this.refreshing=!1,this.is_admin=!1,this.is_superadmin=!1,this._connectionMode="API",this.notification=Object(),this.enableScalingGroup=!1,this.isDisplayingAllocatedShmemEnabled=!1,this.listCondition="loading",this.refreshTimer=Object(),this.kernel_labels=Object(),this.kernel_icons=Object(),this.indicator=Object(),this._helpDescription="",this._helpDescriptionTitle="",this._helpDescriptionIcon="",this.statusColorTable=new Proxy({"idle-timeout":"green","user-requested":"green",scheduled:"green","failed-to-start":"red","creation-failed":"red","self-terminated":"green"},{get:(e,t)=>e.hasOwnProperty(t)?e[t]:"lightgrey"}),this.idleChecksTable=new Proxy({network_timeout:"NetworkIdleTimeout",session_lifetime:"MaxSessionLifetime",utilization:"UtilizationIdleTimeout",expire_after:"ExpiresAfter",grace_period:"GracePeriod",cpu_util:"CPU",mem:"MEM",cuda_util:"GPU",cuda_mem:"GPU(MEM)"},{get:(e,t)=>e.hasOwnProperty(t)?e[t]:""}),this.sessionTypeColorTable=new Proxy({INTERACTIVE:"green",BATCH:"darkgreen",INFERENCE:"blue"},{get:(e,t)=>e.hasOwnProperty(t)?e[t]:"lightgrey"}),this.sshPort=0,this.vncPort=0,this.current_page=1,this.session_page_limit=50,this.total_session_count=0,this._APIMajorVersion=5,this.selectedSessionStatus=Object(),this.isUserInfoMaskEnabled=!1,this._isContainerCommitEnabled=!1,this.getUtilizationCheckerColor=(e,t=null)=>{const i="#527A42",s="#D8B541",n="#e05d44";if(t){let o=i;return"and"===t?Object.values(e).every((([e,t])=>e<Math.min(2*t,t+5)))?o=n:Object.values(e).every((([e,t])=>e<Math.min(10*t,t+10)))&&(o=s):"or"===t&&(Object.values(e).some((([e,t])=>e<Math.min(2*t,t+5)))?o=n:Object.values(e).some((([e,t])=>e<Math.min(10*t,t+10)))&&(o=s)),o}{const[t,o]=e;return t<2*o?n:t<10*o?s:i}},this._selected_items=[],this.terminationQueue=[],this.activeIdleCheckList=new Set}static get styles(){return[h,u,m,i`
        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 265px);
        }

        mwc-icon.pagination {
          color: var(--paper-grey-700);
        }

        lablup-expansion {
          width: 100%;
          --expansion-header-padding: 15px;
          --expansion-header-font-size: 14px;
        }

        mwc-button.pagination {
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

        mwc-button.pagination[disabled] {
          --button-shadow-color: transparent;
        }

        mwc-icon-button.controls-running {
          --mdc-icon-size: 24px;
        }

        img.indicator-icon {
          width: 16px;
          height: 16px;
          padding-right: 5px;
        }

        mwc-checkbox {
          margin: 0 0 0 -6px;
          padding: 0;
        }

        mwc-icon {
          margin-right: 5px;
        }

        mwc-icon.indicator {
          --mdc-icon-size: 16px;
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

        #terminate-selected-sessions-dialog,
        #terminate-session-dialog {
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
          font-size: 12px;
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

        #help-description p,
        #help-description strong {
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

        mwc-button.multiple-action-button {
          --mdc-theme-primary: var(--paper-red-600);
          --mdc-theme-on-primary: white;
        }

        div.pagination-label {
          background-color: var(--paper-grey-100);
          min-width: 60px;
          font-size: 12px;
          font-family: var(--general-font-family);
          padding-top: 5px;
          width: auto;
          text-align: center;
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
          font-family: var(--general-font-family);
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
      `]}get _isRunning(){return["batch","interactive","inference","system","running","others"].includes(this.condition)}get _isIntegratedCondition(){return["running","finished","others"].includes(this.condition)}_isPreparing(e){return-1!==["RESTARTING","PREPARING","PULLING"].indexOf(e)}_isError(e){return"ERROR"===e}_isPending(e){return"PENDING"===e}_isFinished(e){return["TERMINATED","CANCELLED","TERMINATING"].includes(e)}firstUpdated(){this.imageInfo=globalThis.backendaimetadata.imageInfo,this.kernel_icons=globalThis.backendaimetadata.icons,this.kernel_labels=globalThis.backendaimetadata.kernel_labels,document.addEventListener("backend-ai-metadata-image-loaded",(()=>{this.imageInfo=globalThis.backendaimetadata.imageInfo,this.kernel_icons=globalThis.backendaimetadata.icons,this.kernel_labels=globalThis.backendaimetadata.kernel_labels}),{once:!0}),this.refreshTimer=null,this.notification=globalThis.lablupNotification,this.indicator=globalThis.lablupIndicator,document.addEventListener("backend-ai-group-changed",(e=>this.refreshList(!0,!1))),document.addEventListener("backend-ai-ui-changed",(e=>this._refreshWorkDialogUI(e))),document.addEventListener("backend-ai-clear-timeout",(()=>{clearTimeout(this.refreshTimer)})),this._refreshWorkDialogUI({detail:{"mini-ui":globalThis.mini_ui}})}async _viewStateChanged(e){var t;await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{var e;globalThis.backendaiclient.is_admin?this.accessKeyFilterInput.style.display="block":(this.accessKeyFilterInput.style.display="none",this.accessKeyFilterHelperText.style.display="none",(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("vaadin-grid")).style.height="calc(100vh - 225px)!important"),globalThis.backendaiclient.APIMajorVersion<5&&(this.sessionNameField="sess_id"),this.is_admin=globalThis.backendaiclient.is_admin,this.is_superadmin=globalThis.backendaiclient.is_superadmin,this._connectionMode=globalThis.backendaiclient._config._connectionMode,this.enableScalingGroup=globalThis.backendaiclient.supports("scaling-group"),this.isDisplayingAllocatedShmemEnabled=globalThis.backendaiclient.supports("display-allocated-shmem"),this._APIMajorVersion=globalThis.backendaiclient.APIMajorVersion,this.isUserInfoMaskEnabled=globalThis.backendaiclient._config.maskUserInfo,this._isContainerCommitEnabled=globalThis.backendaiclient._config.enableContainerCommit&&globalThis.backendaiclient.supports("image-commit"),this._refreshJobData()}),!0):(globalThis.backendaiclient.is_admin?(this.accessKeyFilterInput.style.display="block",this.accessKeyFilterHelperText.style.display="block"):(this.accessKeyFilterInput.style.display="none",this.accessKeyFilterHelperText.style.display="none",(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("vaadin-grid")).style.height="calc(100vh - 225px)!important"),globalThis.backendaiclient.APIMajorVersion<5&&(this.sessionNameField="sess_id"),this.is_admin=globalThis.backendaiclient.is_admin,this.is_superadmin=globalThis.backendaiclient.is_superadmin,this._connectionMode=globalThis.backendaiclient._config._connectionMode,this.enableScalingGroup=globalThis.backendaiclient.supports("scaling-group"),this.isDisplayingAllocatedShmemEnabled=globalThis.backendaiclient.supports("display-allocated-shmem"),this._APIMajorVersion=globalThis.backendaiclient.APIMajorVersion,this.isUserInfoMaskEnabled=globalThis.backendaiclient._config.maskUserInfo,this._isContainerCommitEnabled=globalThis.backendaiclient._config.enableContainerCommit&&globalThis.backendaiclient.supports("image-commit"),this._refreshJobData()))}async refreshList(e=!0,t=!0){return this._refreshJobData(e,t)}async _refreshJobData(e=!1,t=!0){if(await this.updateComplete,!0!==this.active)return;if(!0===this.refreshing)return;let i;switch(this.refreshing=!0,i="RUNNING",this.condition){case"running":case"interactive":case"system":case"batch":case"inference":case"others":i=["RUNNING","RESTARTING","TERMINATING","PENDING","SCHEDULED","PREPARING","PULLING","ERROR"];break;case"finished":i=["TERMINATED","CANCELLED"];break;default:i=["RUNNING","RESTARTING","TERMINATING","PENDING","SCHEDULED","PREPARING","PULLING"]}!globalThis.backendaiclient.supports("avoid-hol-blocking")&&i.includes("SCHEDULED")&&(i=i.filter((e=>"SCHEDULED"!==e))),globalThis.backendaiclient.supports("detailed-session-states")&&(i=i.join(","));const s=["id","session_id","name","image","architecture","created_at","terminated_at","status","status_info","service_ports","mounts","resource_opts","occupied_slots","access_key","starts_at","type"];globalThis.backendaiclient.supports("multi-container")&&s.push("cluster_size"),globalThis.backendaiclient.supports("multi-node")&&s.push("cluster_mode"),globalThis.backendaiclient.supports("session-detail-status")&&s.push("status_data"),globalThis.backendaiclient.supports("idle-checks")&&s.push("idle_checks"),globalThis.backendaiclient.supports("inference-workload")&&s.push("inference_metrics"),globalThis.backendaiclient.supports("sftp-scaling-group")&&s.push("main_kernel_role"),this.enableScalingGroup&&s.push("scaling_group"),"SESSION"===this._connectionMode&&s.push("user_email"),globalThis.backendaiclient.is_superadmin?s.push("containers {container_id agent occupied_slots live_stat last_stat}"):s.push("containers {container_id occupied_slots live_stat last_stat}"),globalThis.backendaiclient._config.hideAgents||s.push("containers {agent}");const n=globalThis.backendaiclient.current_group_id();this._isContainerCommitEnabled&&i.includes("RUNNING")&&s.push("commit_status"),globalThis.backendaiclient.computeSession.list(s,i,this.filterAccessKey,this.session_page_limit,(this.current_page-1)*this.session_page_limit,n,1e4).then((i=>{var s,n,o;this.total_session_count=i.compute_session_list.total_count;let a,r=i.compute_session_list.items;if(0===this.total_session_count?(this.listCondition="no-data",null===(s=this._listStatus)||void 0===s||s.show(),this.total_session_count=1):["interactive","batch","inference"].includes(this.condition)&&0===r.filter((e=>e.type.toLowerCase()===this.condition)).length||"system"===this.condition&&0===r.filter((e=>e.main_kernel_role.toLowerCase()===this.condition)).length?(this.listCondition="no-data",null===(n=this._listStatus)||void 0===n||n.show()):null===(o=this._listStatus)||void 0===o||o.hide(),void 0!==r&&0!=r.length){const e=this.compute_sessions,t=[];Object.keys(e).map(((i,s)=>{t.push(e[i].session_id)})),Object.keys(r).map(((e,t)=>{var i,s,n;const o=r[e],a=JSON.parse(o.occupied_slots),l=r[e].image.split("/")[2]||r[e].image.split("/")[1];if(r[e].cpu_slot=parseInt(a.cpu),r[e].mem_slot=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(a.mem,"g")),r[e].mem_slot=r[e].mem_slot.toFixed(2),r[e].elapsed=this._elapsed(r[e].created_at,r[e].terminated_at),r[e].created_at_hr=this._humanReadableTime(r[e].created_at),r[e].starts_at_hr=r[e].starts_at?this._humanReadableTime(r[e].starts_at):"",globalThis.backendaiclient.supports("idle-checks")){const t=JSON.parse(o.idle_checks||"{}");t&&(r[e].idle_checks=t),t&&t.network_timeout&&t.network_timeout.remaining&&(r[e].idle_checks.network_timeout.remaining=D.secondsToDHMS(t.network_timeout.remaining),null===(i=this.activeIdleCheckList)||void 0===i||i.add("network_timeout")),t&&t.session_lifetime&&t.session_lifetime.remaining&&(r[e].idle_checks.session_lifetime.remaining=D.secondsToDHMS(t.session_lifetime.remaining),null===(s=this.activeIdleCheckList)||void 0===s||s.add("session_lifetime")),t&&t.utilization&&t.utilization.remaining&&(r[e].idle_checks.utilization.remaining=D.secondsToDHMS(t.utilization.remaining),null===(n=this.activeIdleCheckList)||void 0===n||n.add("utilization"))}if(r[e].containers&&r[e].containers.length>0){const t=r[e].containers[0],i=t.live_stat?JSON.parse(t.live_stat):null;r[e].agent=t.agent,i&&i.cpu_used?r[e].cpu_used_time=this._automaticScaledTime(i.cpu_used.current):r[e].cpu_used_time=this._automaticScaledTime(0),i&&i.cpu_util?r[e].cpu_util=i.cpu_util.current:r[e].cpu_util=0,i&&i.mem?r[e].mem_current=i.mem.current:r[e].mem_current=0,i&&i.io_read?r[e].io_read_bytes_mb=D.bytesToMB(i.io_read.current):r[e].io_read_bytes_mb=0,i&&i.io_write?r[e].io_write_bytes_mb=D.bytesToMB(i.io_write.current):r[e].io_write_bytes_mb=0,i&&i.cuda_util?r[e].cuda_util=i.cuda_util.current:r[e].cuda_util=0,i&&i.rocm_util?r[e].rocm_util=i.rocm_util:r[e].rocm_util=0,i&&i.tpu_util?r[e].tpu_util=i.tpu_util:r[e].tpu_util=0,i&&i.ipu_util?r[e].ipu_util=i.ipu_util:r[e].ipu_util=0,i&&i.atom_util?r[e].atom_util=i.atom_util:r[e].atom_util=0,i&&i.cuda_mem?r[e].cuda_mem_ratio=i.cuda_mem.current/i.cuda_mem.capacity||0:r[e].cuda_mem_ratio=null}const c=JSON.parse(r[e].service_ports);r[e].service_ports=c,!0===Array.isArray(c)?(r[e].app_services=c.map((e=>e.name)),r[e].app_services_option={},c.forEach((t=>{"allowed_arguments"in t&&(r[e].app_services_option[t.name]=t.allowed_arguments)}))):(r[e].app_services=[],r[e].app_services_option={}),0!==r[e].app_services.length&&["batch","interactive","inference","system","running"].includes(this.condition)?r[e].appSupport=!0:r[e].appSupport=!1,["batch","interactive","inference","system","running"].includes(this.condition)?r[e].running=!0:r[e].running=!1,"cuda.device"in a&&(r[e].cuda_gpu_slot=parseInt(a["cuda.device"])),"rocm.device"in a&&(r[e].rocm_gpu_slot=parseInt(a["rocm.device"])),"tpu.device"in a&&(r[e].tpu_slot=parseInt(a["tpu.device"])),"ipu.device"in a&&(r[e].ipu_slot=parseInt(a["ipu.device"])),"atom.device"in a&&(r[e].atom_slot=parseInt(a["atom.device"])),"warboy.device"in a&&(r[e].warboy_slot=parseInt(a["warboy.device"])),"cuda.shares"in a&&(r[e].cuda_fgpu_slot=parseFloat(a["cuda.shares"]).toFixed(2)),r[e].kernel_image=l,r[e].icon=this._getKernelIcon(o.image),r[e].sessionTags=this._getKernelInfo(o.image);const d=o.image.split("/");r[e].cluster_size=parseInt(r[e].cluster_size);const p=d[d.length-1].split(":")[1],h=p.split("-");void 0!==h[1]?(r[e].baseversion=h[0],r[e].baseimage=h[1],r[e].additional_reqs=h.slice(1,h.length).map((e=>e.toUpperCase()))):void 0!==r[e].tag?r[e].baseversion=r[e].tag:r[e].baseversion=p,this._selected_items.includes(r[e].session_id)?r[e].checked=!0:r[e].checked=!1}))}if(["batch","interactive","inference"].includes(this.condition)){const e=r.reduce(((e,t)=>("SYSTEM"!==t.main_kernel_role&&e[t.type.toLowerCase()].push(t),e)),{batch:[],interactive:[],inference:[]});r=e[this.condition]}else r="system"===this.condition?r.filter((e=>"SYSTEM"===e.main_kernel_role)):r.filter((e=>"SYSTEM"!==e.main_kernel_role));if(this.compute_sessions=r,this._grid.recalculateColumnWidths(),this.requestUpdate(),this.refreshing=!1,!0===this.active){if(!0===e){const e=new CustomEvent("backend-ai-resource-refreshed",{detail:{}});document.dispatchEvent(e)}!0===t&&(a=["batch","interactive","inference","system","running"].includes(this.condition)?7e3:3e4,this.refreshTimer=setTimeout((()=>{this._refreshJobData()}),a))}})).catch((e=>{var i;if(this.refreshing=!1,this.active&&t){const e=["batch","interactive","inference","system","running"].includes(this.condition)?2e4:12e4;this.refreshTimer=setTimeout((()=>{this._refreshJobData()}),e)}null===(i=this._listStatus)||void 0===i||i.hide(),console.log(e),e&&e.message&&(this.notification.text=g.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_refreshWorkDialogUI(e){Object.prototype.hasOwnProperty.call(e.detail,"mini-ui")&&!0===e.detail["mini-ui"]?this.workDialog.classList.add("mini_ui"):this.workDialog.classList.remove("mini_ui")}_humanReadableTime(e){return(e=new Date(e)).toLocaleString()}_getKernelInfo(e){const t=[];if(void 0===e)return[];const i=e.split("/"),s=(i[2]||i[1]).split(":")[0];if(s in this.kernel_labels)t.push(this.kernel_labels[s]);else{const i=e.split("/");let s,n;3===i.length?(s=i[1],n=i[2]):i.length>3?(s=i.slice(2,i.length-1).join("/"),n=i[i.length-1]):(s="",n=i[1]),n=n.split(":")[0],n=s?s+"/"+n:n,t.push([{category:"Env",tag:`${n}`,color:"lightgrey"}])}return t}_getKernelIcon(e){if(void 0===e)return[];const t=e.split("/"),i=(t[2]||t[1]).split(":")[0];return i in this.kernel_icons?this.kernel_icons[i]:""}_automaticScaledTime(e){let t=Object();const i=["D","H","M","S"],s=[864e5,36e5,6e4,1e3];for(let n=0;n<s.length;n++)Math.floor(e/s[n])>0&&(t[i[n]]=Math.floor(e/s[n]),e%=s[n]);return 0===Object.keys(t).length&&(t=e>0?{MS:e}:{NODATA:1}),t}static bytesToMB(e,t=1){return Number(e/10**6).toFixed(1)}static bytesToGiB(e,t=2){return e?(e/2**30).toFixed(t):e}_elapsed(e,t){return globalThis.backendaiclient.utils.elapsedTime(e,t)}_indexRenderer(e,t,i){const s=i.index+1;b(_`
        <div>${s}</div>
      `,e)}async sendRequest(e){let t,i;try{"GET"==e.method&&(e.body=void 0),t=await fetch(e.uri,e);const s=t.headers.get("Content-Type");if(i=s.startsWith("application/json")||s.startsWith("application/problem+json")?await t.json():s.startsWith("text/")?await t.text():await t.blob(),!t.ok)throw i}catch(e){}return i}async _terminateApp(e){const t=globalThis.backendaiclient._config.accessKey,i=await globalThis.appLauncher._getProxyURL(e),s={method:"GET",uri:new URL(`proxy/${t}/${e}`,i).href};return this.sendRequest(s).then((s=>{this.total_session_count-=1;let n=new URL(`proxy/${t}/${e}/delete`,i);if(localStorage.getItem("backendaiwebui.appproxy-permit-key")&&(n.searchParams.set("permit_key",localStorage.getItem("backendaiwebui.appproxy-permit-key")||""),n=new URL(n.href)),void 0!==s&&404!==s.code){const e={method:"GET",uri:n.href,credentials:"include",mode:"cors"};return this.sendRequest(e)}return Promise.resolve(!0)})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=g.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_getProxyToken(){let e="local";return void 0!==globalThis.backendaiclient._config.proxyToken&&(e=globalThis.backendaiclient._config.proxyToken),e}_showLogs(e){const t=e.target.closest("#controls"),i=t["session-uuid"],s=t["session-name"],n=globalThis.backendaiclient.APIMajorVersion<5?s:i,o=t["access-key"];globalThis.backendaiclient.get_logs(n,o,15e3).then((e=>{const t=(new T).ansi_to_html(e.result.logs);setTimeout((()=>{var e,n;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#work-title")).innerHTML=`${s} (${i})`,(null===(n=this.shadowRoot)||void 0===n?void 0:n.querySelector("#work-area")).innerHTML=`<pre>${t}</pre>`||v("session.NoLogs"),this.workDialog.sessionUuid=i,this.workDialog.sessionName=s,this.workDialog.accessKey=o,this.workDialog.show()}),100)})).catch((e=>{e&&e.message?(this.notification.text=g.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=g.relieve(e.title),this.notification.show(!0,e))}))}_downloadLogs(){const e=this.workDialog.sessionUuid,t=this.workDialog.sessionName,i=globalThis.backendaiclient.APIMajorVersion<5?t:e,s=this.workDialog.accessKey;globalThis.backendaiclient.get_logs(i,s,15e3).then((e=>{const i=e.result.logs;globalThis.backendaiutils.exportToTxt(t,i),this.notification.text=v("session.DownloadingSessionLogs"),this.notification.show()})).catch((e=>{e&&e.message?(this.notification.text=g.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=g.relieve(e.title),this.notification.show(!0,e))}))}_refreshLogs(){const e=this.workDialog.sessionUuid,t=this.workDialog.sessionName,i=globalThis.backendaiclient.APIMajorVersion<5?t:e,s=this.workDialog.accessKey;globalThis.backendaiclient.get_logs(i,s,15e3).then((e=>{var t;const i=(new T).ansi_to_html(e.result.logs);(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#work-area")).innerHTML=`<pre>${i}</pre>`||v("session.NoLogs")})).catch((e=>{e&&e.message?(this.notification.text=g.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=g.relieve(e.title),this.notification.show(!0,e))}))}_showAppLauncher(e){const t=e.target.closest("#controls");return globalThis.appLauncher.showLauncher(t)}async _runTerminal(e){const t=e.target.closest("#controls")["session-uuid"];return globalThis.appLauncher.runTerminal(t)}async _getCommitSessionStatus(e=""){let t=!1;return""!==e&&globalThis.backendaiclient.computeSession.getCommitSessionStatus(e).then((e=>{t=e})).catch((e=>{console.log(e)})),t}async _requestCommitSession(e){try{const t=await globalThis.backendaiclient.computeSession.commitSession(e.session.name),i=Object.assign(e,{taskId:t.bgtask_id});this._addCommitSessionToTasker(t,i),this._applyContainerCommitAsBackgroundTask(i),this.notification.text=v("session.CommitOnGoing"),this.notification.show()}catch(e){console.log(e),e&&e.message&&(this.notification.text=g.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}finally{this.commitSessionDialog.hide()}}_applyContainerCommitAsBackgroundTask(e){const t=globalThis.backendaiclient.maintenance.attach_background_task(e.taskId);t.addEventListener("bgtask_done",(i=>{this.notification.text=v("session.CommitFinished"),this.notification.show(),this._removeCommitSessionFromTasker(e.taskId),t.close()})),t.addEventListener("bgtask_failed",(i=>{throw this.notification.text=v("session.CommitFailed"),this.notification.show(!0),this._removeCommitSessionFromTasker(e.taskId),t.close(),new Error("Commit session request has been failed.")})),t.addEventListener("bgtask_cancelled",(i=>{throw this.notification.text=v("session.CommitFailed"),this.notification.show(!0),this._removeCommitSessionFromTasker(e.taskId),t.close(),new Error("Commit session request has been cancelled.")}))}_addCommitSessionToTasker(e=null,t){var i;globalThis.tasker.add(v("session.CommitSession")+t.session.name,null!==e&&"function"==typeof e?e:null,null!==(i=t.taskId)&&void 0!==i?i:"","commit","remove-later")}_removeCommitSessionFromTasker(e=""){globalThis.tasker.remove(e)}_getCurrentContainerCommitInfoListFromLocalStorage(){return JSON.parse(localStorage.getItem("backendaiwebui.settings.user.container_commit_sessions")||"[]")}_saveCurrentContainerCommitInfoToLocalStorage(e){const t=this._getCurrentContainerCommitInfoListFromLocalStorage();t.push(e),globalThis.backendaioptions.set("container_commit_sessions",JSON.stringify(t))}_removeFinishedContainerCommitInfoFromLocalStorage(e="",t=""){let i=this._getCurrentContainerCommitInfoListFromLocalStorage();i=i.filter((i=>i.session.id!==e&&i.taskId!==t)),globalThis.backendaioptions.set("container_commit_sessions",JSON.stringify(i))}_openCommitSessionDialog(e){const t=e.target.closest("#controls"),i=t["session-name"],s=t["session-uuid"],n=t["kernel-image"];this.commitSessionDialog.sessionName=i,this.commitSessionDialog.sessionId=s,this.commitSessionDialog.kernelImage=n,this.commitSessionDialog.show()}_openTerminateSessionDialog(e){const t=e.target.closest("#controls"),i=t["session-name"],s=t["session-uuid"],n=t["access-key"];this.terminateSessionDialog.sessionName=i,this.terminateSessionDialog.sessionId=s,this.terminateSessionDialog.accessKey=n,this.terminateSessionDialog.show()}_terminateSession(e){const t=e.target.closest("#controls"),i=t["session-uuid"],s=t["access-key"];return this.terminationQueue.includes(i)?(this.notification.text=v("session.AlreadyTerminatingSession"),this.notification.show(),!1):this._terminateKernel(i,s)}_terminateSessionWithCheck(e=!1){var t;return this.terminationQueue.includes(this.terminateSessionDialog.sessionId)?(this.notification.text=v("session.AlreadyTerminatingSession"),this.notification.show(),!1):(this.listCondition="loading",null===(t=this._listStatus)||void 0===t||t.show(),this._terminateKernel(this.terminateSessionDialog.sessionId,this.terminateSessionDialog.accessKey,e).then((e=>{this._selected_items=[],this._clearCheckboxes(),this.terminateSessionDialog.hide(),this.notification.text=v("session.SessionTerminated"),this.notification.show();const t=new CustomEvent("backend-ai-resource-refreshed",{detail:"running"});document.dispatchEvent(t)})).catch((e=>{this._selected_items=[],this._clearCheckboxes(),this.terminateSessionDialog.hide(),this.notification.text=g.relieve("Problem occurred during termination."),this.notification.show(!0,e);const t=new CustomEvent("backend-ai-resource-refreshed",{detail:"running"});document.dispatchEvent(t)})))}_openTerminateSelectedSessionsDialog(e){this.terminateSelectedSessionsDialog.show()}_clearCheckboxes(){var e;[...Array.from(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll("mwc-checkbox.list-check"))].forEach((e=>{e.removeAttribute("checked")}))}_terminateSelectedSessionsWithCheck(e=!1){var t;this.listCondition="loading",null===(t=this._listStatus)||void 0===t||t.show();const i=this._selected_items.map((t=>this._terminateKernel(t.session_id,t.access_key,e)));return this._selected_items=[],Promise.all(i).then((e=>{this.terminateSelectedSessionsDialog.hide(),this._clearCheckboxes(),this.multipleActionButtons.style.display="none",this.notification.text=v("session.SessionsTerminated"),this.notification.show()})).catch((e=>{this.terminateSelectedSessionsDialog.hide(),this._clearCheckboxes(),this.notification.text=g.relieve("Problem occurred during termination."),this.notification.show(!0,e)}))}_terminateSelectedSessions(){var e;this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show();const t=this._selected_items.map((e=>this._terminateKernel(e.session_id,e.access_key)));return Promise.all(t).then((e=>{this._selected_items=[],this._clearCheckboxes(),this.multipleActionButtons.style.display="none",this.notification.text=v("session.SessionsTerminated"),this.notification.show()})).catch((e=>{var t;null===(t=this._listStatus)||void 0===t||t.hide(),this._selected_items=[],this._clearCheckboxes(),this.notification.text="description"in e?g.relieve(e.description):g.relieve("Problem occurred during termination."),this.notification.show(!0,e)}))}_requestDestroySession(e,t,i){globalThis.backendaiclient.destroy(e,t,i).then((e=>{setTimeout((async()=>{this.terminationQueue=[];const e=new CustomEvent("backend-ai-session-list-refreshed",{detail:"running"});document.dispatchEvent(e)}),1e3)})).catch((e=>{const t=new CustomEvent("backend-ai-session-list-refreshed",{detail:"running"});document.dispatchEvent(t),this.notification.text="description"in e?g.relieve(e.description):g.relieve("Problem occurred during termination."),this.notification.show(!0,e)}))}async _terminateKernel(e,t,i=!1){return this.terminationQueue.push(e),this._terminateApp(e).then((()=>{this._requestDestroySession(e,t,i)})).catch((s=>{s&&s.message&&(404==s.statusCode||500==s.statusCode?this._requestDestroySession(e,t,i):(this.notification.text=g.relieve(s.title),this.notification.detail=s.message,this.notification.show(!0,s)))}))}_hideDialog(e){var t;const i=e.target.closest("backend-ai-dialog");if(i.hide(),"ssh-dialog"===i.id){const e=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#sshkey-download-link");globalThis.URL.revokeObjectURL(e.href)}}_updateFilterAccessKey(e){this.filterAccessKey=e.target.value,this.refreshTimer&&(clearTimeout(this.refreshTimer),this._refreshJobData())}_createMountedFolderDropdown(e,t){const i=e.target,s=document.createElement("mwc-menu");s.anchor=i,s.className="dropdown-menu",s.style.boxShadow="0 1px 1px rgba(0, 0, 0, 0.2)",s.setAttribute("open",""),s.setAttribute("fixed",""),s.setAttribute("x","10"),s.setAttribute("y","15"),t.length>=1&&(t.map(((e,i)=>{const n=document.createElement("mwc-list-item");n.style.height="25px",n.style.fontWeight="400",n.style.fontSize="14px",n.style.fontFamily="var(--general-font-family)",n.innerHTML=t.length>1?e:v("session.OnlyOneFolderAttached"),s.appendChild(n)})),document.body.appendChild(s))}_removeMountedFolderDropdown(){var e;const t=document.getElementsByClassName("dropdown-menu");for(;t[0];)null===(e=t[0].parentNode)||void 0===e||e.removeChild(t[0])}_renderStatusDetail(){var e,t,i,s,n,o,a,r,l;const c=JSON.parse(this.selectedSessionStatus.data);c.reserved_time=this.selectedSessionStatus.reserved_time;const d=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#status-detail"),p=[];if(p.push(_`
      <div class="vertical layout justified start">
        <h3 style="width:100%;padding-left:15px;border-bottom:1px solid #ccc;">
          ${v("session.Status")}
        </h3>
        <lablup-shields
          color="${this.statusColorTable[this.selectedSessionStatus.info]}"
          description="${this.selectedSessionStatus.info}"
          ui="round"
          style="padding-left:10px;padding-right:10px;"
        ></lablup-shields>
      </div>
    `),c.hasOwnProperty("kernel")||c.hasOwnProperty("session"))p.push(_`
        <div class="vertical layout start flex" style="width:100%;">
          <div style="width:100%;">
            <h3
              style="width:100%;padding-left:15px;border-bottom:1px solid #ccc;"
            >
              ${v("session.StatusDetail")}
            </h3>
            <div class="vertical layout flex" style="width:100%;">
              <mwc-list>
                <mwc-list-item twoline noninteractive class="predicate-check">
                  <span class="subheading">
                    <strong>Kernel Exit Code</strong>
                  </span>
                  <span
                    class="monospace predicate-check-comment"
                    slot="secondary"
                  >
                    ${null!==(i=null===(t=c.kernel)||void 0===t?void 0:t.exit_code)&&void 0!==i?i:"null"}
                  </span>
                </mwc-list-item>
                <mwc-list-item twoline noninteractive class="predicate-check">
                  <span class="subheading">Session Status</span>
                  <span
                    class="monospace predicate-check-comment"
                    slot="secondary"
                  >
                    ${null===(s=c.session)||void 0===s?void 0:s.status}
                  </span>
                </mwc-list-item>
              </mwc-list>
            </div>
          </div>
        </div>
      `);else if(c.hasOwnProperty("scheduler")){const e=null!==(o=null===(n=c.scheduler.failed_predicates)||void 0===n?void 0:n.length)&&void 0!==o?o:0,t=null!==(r=null===(a=c.scheduler.passed_predicates)||void 0===a?void 0:a.length)&&void 0!==r?r:0;p.push(_`
        <div class="vertical layout start flex" style="width:100%;">
          <div style="width:100%;">
            <h3
              style="width:100%;padding-left:15px;border-bottom:1px solid #ccc;"
            >
              ${v("session.StatusDetail")}
            </h3>
            <div class="vertical layout flex" style="width:100%;">
              <mwc-list>
                <mwc-list-item twoline noninteractive class="predicate-check">
                  <span class="subheading">${v("session.Message")}</span>
                  <span
                    class="monospace predicate-check-comment"
                    slot="secondary"
                  >
                    ${c.scheduler.msg}
                  </span>
                </mwc-list-item>
                <mwc-list-item twoline noninteractive class="predicate-check">
                  <span class="subheading">
                    ${v("session.TotalRetries")}
                  </span>
                  <span
                    class="monospace predicate-check-comment"
                    slot="secondary"
                  >
                    ${c.scheduler.retries}
                  </span>
                </mwc-list-item>
                <mwc-list-item twoline noninteractive class="predicate-check">
                  <span class="subheading">${v("session.LastTry")}</span>
                  <span
                    class="monospace predicate-check-comment"
                    slot="secondary"
                  >
                    ${this._humanReadableTime(c.scheduler.last_try)}
                  </span>
                </mwc-list-item>
              </mwc-list>
            </div>
          </div>
          <lablup-expansion summary="Predicates">
            <div slot="title" class="horizontal layout center start-justified">
              ${e>0?_`
                    <mwc-icon class="fg red">cancel</mwc-icon>
                  `:_`
                    <mwc-icon class="fg green">check_circle</mwc-icon>
                  `}
              Predicate Checks
            </div>
            <span slot="description">
              ${e>0?" "+(e+" Failed, "):""}
              ${t+" Passed"}
            </span>
            <mwc-list>
              ${c.scheduler.failed_predicates.map((e=>_`
                  ${"reserved_time"===e.name?_`
                        <mwc-list-item
                          twoline
                          graphic="icon"
                          noninteractive
                          class="predicate-check"
                        >
                          <span>${e.name}</span>
                          <span
                            slot="secondary"
                            class="predicate-check-comment"
                          >
                            ${e.msg+": "+c.reserved_time}
                          </span>
                          <mwc-icon
                            slot="graphic"
                            class="fg red inverted status-check"
                          >
                            close
                          </mwc-icon>
                        </mwc-list-item>
                      `:_`
                        <mwc-list-item
                          twoline
                          graphic="icon"
                          noninteractive
                          class="predicate-check"
                        >
                          <span>${e.name}</span>
                          <span
                            slot="secondary"
                            class="predicate-check-comment"
                          >
                            ${e.msg}
                          </span>
                          <mwc-icon
                            slot="graphic"
                            class="fg red inverted status-check"
                          >
                            close
                          </mwc-icon>
                        </mwc-list-item>
                      `}
                  <li divider role="separator"></li>
                `))}
              ${c.scheduler.passed_predicates.map((e=>_`
                  <mwc-list-item graphic="icon" noninteractive>
                    <span style="padding-left:3px;">${e.name}</span>
                    <mwc-icon
                      slot="graphic"
                      class="fg green inverted status-check"
                      style="padding-left:5px;"
                    >
                      checked
                    </mwc-icon>
                  </mwc-list-item>
                  <li divider role="separator"></li>
                `))}
            </mwc-list>
          </lablup-expansion>
        </div>
      `)}else if(c.hasOwnProperty("error")){const e=null!==(l=c.error.collection)&&void 0!==l?l:[c.error];p.push(_`
        <div class="vertical layout start flex" style="width:100%;">
          <div style="width:100%;">
            <h3
              style="width:100%;padding-left:15px;border-bottom:1px solid #ccc;"
            >
              ${v("session.StatusDetail")}
            </h3>
            ${e.map((e=>_`
                <div
                  style="border-radius: 4px;background-color:var(--paper-grey-300);padding:10px;margin:10px;"
                >
                  <div class="vertical layout start">
                    <span class="subheading">Error</span>
                    <lablup-shields
                      color="red"
                      description=${e.name}
                      ui="round"
                    ></lablup-shields>
                  </div>
                  ${!this.is_superadmin&&globalThis.backendaiclient._config.hideAgents||!e.agent_id?_``:_`
                        <div class="vertical layout start">
                          <span class="subheading">Agent ID</span>
                          <span>${e.agent_id}</span>
                        </div>
                      `}
                  <div class="vertical layout start">
                    <span class="subheading">Message</span>
                    <span class="error-description">${e.repr}</span>
                  </div>
                  ${e.traceback?_`
                        <div class="vertical layout start">
                          <span class="subheading">Traceback</span>
                          <pre
                            style="display: block; overflow: auto; width: 100%; height: 400px;"
                          >
${e.traceback}</pre
                          >
                        </div>
                      `:_``}
                </div>
              `))}
          </div>
        </div>
      `)}else p.push(_`
        <div class="vertical layout start flex" style="width:100%;">
          <h3
            style="width:100%;padding-left:15px;border-bottom:1px solid #ccc;"
          >
            Detail
          </h3>
          <span style="margin:20px;">No Detail.</span>
        </div>
      `);b(p,d)}_openStatusDetailDialog(e,t,i){this.selectedSessionStatus={info:e,data:t,reserved_time:i},this._renderStatusDetail(),this.sessionStatusInfoDialog.show()}_validateSessionName(e){const t=this.compute_sessions.map((e=>e[this.sessionNameField])),i=e.target.parentNode,s=i.querySelector("#session-name-field").innerText,n=i.querySelector("#session-rename-field");n.validityTransform=(e,i)=>{if(i.valid){const i=!t.includes(e)||e===s;return i||(n.validationMessage=v("session.Validation.SessionNameAlreadyExist")),{valid:i,customError:!i}}return i.valueMissing?(n.validationMessage=v("session.Validation.SessionNameRequired"),{valid:i.valid,valueMissing:!i.valid}):i.patternMismatch?(n.validationMessage=v("session.Validation.SluggedStrings"),{valid:i.valid,patternMismatch:!i.valid}):(n.validationMessage=v("session.Validation.EnterValidSessionName"),{valid:i.valid,customError:!i.valid})}}_renameSessionName(e,t){const i=t.target.parentNode,s=i.querySelector("#session-name-field"),n=i.querySelector("#session-rename-field"),o=i.querySelector("#session-rename-icon");if("none"===s.style.display){if(!n.checkValidity())return n.reportValidity(),void(o.on=!0);{const t=globalThis.backendaiclient.APIMajorVersion<5?s.value:e;globalThis.backendaiclient.rename(t,n.value).then((e=>{this.refreshList(),this.notification.text=v("session.SessionRenamed"),this.notification.show()})).catch((e=>{n.value=s.innerText,e&&e.message&&(this.notification.text=g.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))})).finally((()=>{this._toggleSessionNameField(s,n)}))}}else this._toggleSessionNameField(s,n)}_toggleSessionNameField(e,t){"block"===t.style.display?(e.style.display="block",t.style.display="none"):(e.style.display="none",t.style.display="block",t.focus())}static secondsToDHMS(e){const t=Math.floor(e/86400),i=Math.floor(e%86400/3600),s=Math.floor(e%3600/60),n=parseInt(e)%60,o=t<0||i<0||s<0||n<0?v("session.TimeoutExceeded"):"",a=`${void 0!==t&&t>0?String(t)+"d":""}${i.toString().padStart(2,"0")}:${s.toString().padStart(2,"0")}:${n.toString().padStart(2,"0")}`;return o.length>0?o:a}_getIdleSessionTimeout(e){if(globalThis.backendaiutils.isEmpty(e))return null;let t="",i=1/0;for(const[s,n]of Object.entries(e))null!=n&&"number"==typeof n&&null!=i&&n<i&&(t=s,i=n);return i?[t,D.secondsToDHMS(i)]:null}_openIdleChecksInfoDialog(){var e,t,i;this._helpDescriptionTitle=v("session.IdleChecks"),this._helpDescription=`\n      <p>${v("session.IdleChecksDesc")}</p>\n      ${(null===(e=this.activeIdleCheckList)||void 0===e?void 0:e.has("session_lifetime"))?`\n        <strong>${v("session.MaxSessionLifetime")}</strong>\n        <p>${v("session.MaxSessionLifetimeDesc")}</p>\n        `:""}\n      ${(null===(t=this.activeIdleCheckList)||void 0===t?void 0:t.has("network_timeout"))?`\n        <strong>${v("session.NetworkIdleTimeout")}</strong>\n        <p>${v("session.NetworkIdleTimeoutDesc")}</p>\n      `:""}\n      ${(null===(i=this.activeIdleCheckList)||void 0===i?void 0:i.has("utilization"))?`\n        <strong>${v("session.UtilizationIdleTimeout")}</strong>\n        <p>${v("session.UtilizationIdleTimeoutDesc")}</p>\n        <div style="margin:10px 5% 20px 5%;">\n          <li>\n            <span style="font-weight:500">${v("session.GracePeriod")}</span>\n            <div style="padding-left:20px;">${v("session.GracePeriodDesc")}</div>\n          </li>\n          <li>\n            <span style="font-weight:500">${v("session.UtilizationThreshold")}</span>\n            <div style="padding-left:20px;">${v("session.UtilizationThresholdDesc")}</div>\n          </li>\n        </div>\n      `:""}\n    `,this.helpDescriptionDialog.show()}async _openSFTPSessionConnectionInfoDialog(e){const t=await globalThis.backendaiclient.get_direct_access_info(e),i=t.public_host.replace(/^https?:\/\//,""),s=t.sshd_ports,n=new CustomEvent("read-ssh-key-and-launch-ssh-dialog",{detail:{sessionUuid:e,host:i,port:s}});document.dispatchEvent(n)}_createUtilizationIdleCheckDropdown(e,t){const i=e.target,s=document.createElement("mwc-menu");s.anchor=i,s.className="util-dropdown-menu",s.style.boxShadow="0 1px 1px rgba(0, 0, 0, 0.2)",s.setAttribute("open",""),s.setAttribute("fixed",""),s.setAttribute("corner","BOTTOM_START");let n=_``;globalThis.backendaiutils.isEmpty(t)||(n=_`
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
          <div>
            ${v("session.Utilization")} / ${v("session.Threshold")} (%)
          </div>
        </mwc-list-item>
        ${Object.keys(t).map((e=>{let[i,s]=t[e];i=i>=0?parseFloat(i).toFixed(1):"-";const n=this.getUtilizationCheckerColor([i,s]);return _`
            <mwc-list-item class="util-detail-menu-content">
              <div>
                <div>${this.idleChecksTable[e]}</div>
                <div style="color:${n}">${i} / ${s}</div>
              </div>
            </mwc-list-item>
          `}))}
      `,document.body.appendChild(s)),b(n,s)}_removeUtilizationIdleCheckDropdown(){var e;const t=document.getElementsByClassName("util-dropdown-menu");for(;t[0];)null===(e=t[0].parentNode)||void 0===e||e.removeChild(t[0])}sessionTypeRenderer(e,t,i){const s=JSON.parse(i.item.inference_metrics||"{}");b(_`
        <div class="layout vertical start">
          <lablup-shields
            color="${this.sessionTypeColorTable[i.item.type]}"
            description="${i.item.type}"
            ui="round"
          ></lablup-shields>
          ${"INFERENCE"===i.item.type?_`
                <span style="font-size:12px;margin-top:5px;">
                  Inference requests: ${s.requests}
                </span>
                <span style="font-size:12px;">
                  Inference API last response time (ms):
                  ${s.last_response_ms}
                </span>
              `:""}
        </div>
      `,e)}sessionInfoRenderer(e,t,i){"system"===this.condition?b(_`
          <style>
            #session-name-field {
              display: block;
              white-space: pre-wrap;
              word-break: break-all;
            }
          </style>
          <div class="layout vertical start">
            <div class="horizontal center center-justified layout">
              <pre id="session-name-field">
${i.item.mounts[0]} SFTP Session</pre
              >
            </div>
          </div>
        `,e):b(_`
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
              --mdc-typography-font-family: var(
                --general-monospace-font-family
              );
              --mdc-typography-subtitle1-font-family: var(
                --general-monospace-font-family
              );
            }
            #session-rename-icon {
              --mdc-icon-size: 20px;
            }
          </style>
          <div class="layout vertical start">
            <div class="horizontal center center-justified layout">
              <pre id="session-name-field">
${i.item[this.sessionNameField]}</pre
              >
              ${this._isRunning&&!this._isPreparing(i.item.status)&&globalThis.backendaiclient.email==i.item.user_email?_`
                    <mwc-textfield
                      id="session-rename-field"
                      required
                      autoValidate
                      pattern="^(?:[a-zA-Z0-9][a-zA-Z0-9._-]{2,}[a-zA-Z0-9])?$"
                      maxLength="64"
                      validationMessage="${v("session.Validation.EnterValidSessionName")}"
                      value="${i.item[this.sessionNameField]}"
                      @input="${e=>this._validateSessionName(e)}"
                    ></mwc-textfield>
                    <mwc-icon-button-toggle
                      id="session-rename-icon"
                      onIcon="done"
                      offIcon="edit"
                      @click="${e=>this._renameSessionName(i.item.session_id,e)}"
                    ></mwc-icon-button-toggle>
                  `:_``}
            </div>
            <div class="horizontal center center-justified layout">
              ${i.item.icon?_`
                    <img
                      src="resources/icons/${i.item.icon}"
                      style="width:32px;height:32px;margin-right:10px;"
                    />
                  `:_``}
              <div class="vertical start layout">
                ${i.item.sessionTags?i.item.sessionTags.map((e=>_`
                        <div class="horizontal center layout">
                          ${e.map((e=>("Env"===e.category&&(e.category=e.tag),e.category&&i.item.baseversion&&(e.tag=i.item.baseversion),_`
                              <lablup-shields
                                app="${void 0===e.category?"":e.category}"
                                color="${e.color}"
                                description="${e.tag}"
                                ui="round"
                                class="right-below-margin"
                              ></lablup-shields>
                            `)))}
                        </div>
                      `)):_``}
                ${i.item.additional_reqs?_`
                      <div class="layout horizontal center wrap">
                        ${i.item.additional_reqs.map((e=>_`
                            <lablup-shields
                              app=""
                              color="green"
                              description="${e}"
                              ui="round"
                              class="right-below-margin"
                            ></lablup-shields>
                          `))}
                      </div>
                    `:_``}
                ${i.item.cluster_size>1?_`
                      <div class="layout horizontal center wrap">
                        <lablup-shields
                          app="${"single-node"===i.item.cluster_mode?"Multi-container":"Multi-node"}"
                          color="blue"
                          description="${"X "+i.item.cluster_size}"
                          ui="round"
                          class="right-below-margin"
                        ></lablup-shields>
                      </div>
                    `:_``}
              </div>
            </div>
          </div>
        `,e)}architectureRenderer(e,t,i){b(_`
        <lablup-shields
          app=""
          color="lightgreen"
          description="${i.item.architecture}"
          ui="round"
        ></lablup-shields>
      `,e)}controlRenderer(e,t,i){var s;let n=!0;n="API"===this._connectionMode&&i.item.access_key===globalThis.backendaiclient._config._accessKey||i.item.user_email===globalThis.backendaiclient.email,b(_`
        <div
          id="controls"
          class="layout horizontal wrap center"
          .session-uuid="${i.item.session_id}"
          .session-name="${i.item[this.sessionNameField]}"
          .access-key="${i.item.access_key}"
          .kernel-image="${i.item.kernel_image}"
          .app-services="${i.item.app_services}"
          .app-services-option="${i.item.app_services_option}"
          .service-ports="${i.item.service_ports}"
        >
          ${i.item.appSupport&&"system"!==this.condition?_`
                <mwc-icon-button
                  class="fg controls-running green"
                  id="${i.index+"-apps"}"
                  @click="${e=>this._showAppLauncher(e)}"
                  ?disabled="${!n}"
                  icon="apps"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.index+"-apps"}"
                  text="${f("session.SeeAppDialog")}"
                  position="top-start"
                ></vaadin-tooltip>
                <mwc-icon-button
                  class="fg controls-running"
                  id="${i.index+"-terminal"}"
                  ?disabled="${!n}"
                  @click="${e=>this._runTerminal(e)}"
                >
                  <svg
                    version="1.1"
                    id="Capa_1"
                    xmlns="http://www.w3.org/2000/svg"
                    xmlns:xlink="http://www.w3.org/1999/xlink"
                    x="0px"
                    y="0px"
                    width="471.362px"
                    height="471.362px"
                    viewBox="0 0 471.362 471.362"
                    style="enable-background:new 0 0 471.362 471.362;"
                    xml:space="preserve"
                  >
                    <g>
                      <g>
                        <path
                          d="M468.794,355.171c-1.707-1.718-3.897-2.57-6.563-2.57H188.145c-2.664,0-4.854,0.853-6.567,2.57
                    c-1.711,1.711-2.565,3.897-2.565,6.563v18.274c0,2.662,0.854,4.853,2.565,6.563c1.713,1.712,3.903,2.57,6.567,2.57h274.086
                    c2.666,0,4.856-0.858,6.563-2.57c1.711-1.711,2.567-3.901,2.567-6.563v-18.274C471.365,359.068,470.513,356.882,468.794,355.171z"
                        />
                        <path
                          d="M30.259,85.075c-1.903-1.903-4.093-2.856-6.567-2.856s-4.661,0.953-6.563,2.856L2.852,99.353
                    C0.95,101.255,0,103.442,0,105.918c0,2.478,0.95,4.664,2.852,6.567L115.06,224.69L2.852,336.896C0.95,338.799,0,340.989,0,343.46
                    c0,2.478,0.95,4.665,2.852,6.567l14.276,14.273c1.903,1.906,4.089,2.854,6.563,2.854s4.665-0.951,6.567-2.854l133.048-133.045
                    c1.903-1.902,2.853-4.096,2.853-6.57c0-2.473-0.95-4.663-2.853-6.565L30.259,85.075z"
                        />
                      </g>
                    </g>
                  </svg>
                </mwc-icon-button>
                <vaadin-tooltip
                  for="${i.index+"-terminal"}"
                  text="${f("session.ExecuteTerminalApp")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:_``}
          ${this._isRunning&&"system"===this.condition?_`
                <mwc-icon-button
                  class="fg green controls-running"
                  id="${i.index+"-sftp-connection-info"}"
                  @click="${()=>this._openSFTPSessionConnectionInfoDialog(i.item.id)}"
                >
                  <img src="/resources/icons/sftp.png" />
                </mwc-icon-button>
                <vaadin-tooltip
                  for="${i.index+"-sftp-connection-info"}"
                  text="${f("data.explorer.RunSSH/SFTPserver")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:_``}
          ${this._isRunning&&!this._isPreparing(i.item.status)||this._isError(i.item.status)?_`
                <mwc-icon-button
                  class="fg red controls-running"
                  id="${i.index+"-power"}"
                  ?disabled=${!this._isPending(i.item.status)&&"ongoing"===(null===(s=i.item)||void 0===s?void 0:s.commit_status)}
                  icon="power_settings_new"
                  @click="${e=>this._openTerminateSessionDialog(e)}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.index+"-power"}"
                  text="${f("session.TerminateSession")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:_``}
          ${(this._isRunning&&!this._isPreparing(i.item.status)||this._APIMajorVersion>4)&&!this._isPending(i.item.status)?_`
                <mwc-icon-button
                  class="fg blue controls-running"
                  id="${i.index+"-assignment"}"
                  icon="assignment"
                  @click="${e=>this._showLogs(e)}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.index+"-assignment"}"
                  text="${f("session.SeeContainerLogs")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:_`
                <mwc-icon-button
                  fab
                  flat
                  inverted
                  disabled
                  class="fg controls-running"
                  id="${i.index+"-assignment"}"
                  icon="assignment"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.index+"-assignment"}"
                  text="${f("session.NoLogMsgAvailable")}"
                  position="top-start"
                ></vaadin-tooltip>
              `}
          ${this._isContainerCommitEnabled?_`
                <mwc-icon-button
                  class="fg blue controls-running"
                  id="${i.index+"-archive"}"
                  ?disabled=${this._isPending(i.item.status)||this._isPreparing(i.item.status)||this._isError(i.item.status)||this._isFinished(i.item.status)||"BATCH"===i.item.type||"ongoing"===i.item.commit_status}
                  icon="archive"
                  @click="${e=>this._openCommitSessionDialog(e)}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.index+"-archive"}"
                  text="${f("session.RequestContainerCommit")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:_``}
        </div>
      `,e)}configRenderer(e,t,i){const s=i.item.mounts.map((e=>e.startsWith("[")?JSON.parse(e.replace(/'/g,'"'))[0]:e));"system"===this.condition?b(_``,e):b(_`
          <div class="layout horizontal center flex">
            <div class="layout horizontal center configuration">
              ${i.item.mounts.length>0?_`
                    <mwc-icon class="fg green indicator">folder_open</mwc-icon>
                    <button
                      class="mount-button"
                      @mouseenter="${e=>this._createMountedFolderDropdown(e,s)}"
                      @mouseleave="${()=>this._removeMountedFolderDropdown()}"
                    >
                      ${s.join(", ")}
                    </button>
                  `:_`
                    <mwc-icon class="no-mount indicator">folder_open</mwc-icon>
                    <span class="no-mount">No mount</span>
                  `}
            </div>
          </div>
          ${i.item.scaling_group?_`
                <div class="layout horizontal center flex">
                  <div class="layout horizontal center configuration">
                    <mwc-icon class="fg green indicator">work</mwc-icon>
                    <span>${i.item.scaling_group}</span>
                    <span class="indicator">RG</span>
                  </div>
                </div>
              `:_``}
          <div class="layout vertical flex" style="padding-left: 25px">
            <div class="layout horizontal center configuration">
              <mwc-icon class="fg green indicator">developer_board</mwc-icon>
              <span>${i.item.cpu_slot}</span>
              <span class="indicator">${f("session.core")}</span>
            </div>
            <div class="layout horizontal center configuration">
              <mwc-icon class="fg green indicator">memory</mwc-icon>
              <span>${i.item.mem_slot}</span>
              <span class="indicator">GiB</span>
              ${this.isDisplayingAllocatedShmemEnabled?_`
                    <span class="indicator">
                      ${"(SHM: "+this._aggregateSharedMemory(JSON.parse(i.item.resource_opts))+"GiB)"}
                    </span>
                  `:_``}
            </div>
            <div class="layout horizontal center configuration">
              ${i.item.cuda_gpu_slot?_`
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/file_type_cuda.svg"
                    />
                    <span>${i.item.cuda_gpu_slot}</span>
                    <span class="indicator">GPU</span>
                  `:_``}
              ${!i.item.cuda_gpu_slot&&i.item.cuda_fgpu_slot?_`
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/file_type_cuda.svg"
                    />
                    <span>${i.item.cuda_fgpu_slot}</span>
                    <span class="indicator">FGPU</span>
                  `:_``}
              ${i.item.rocm_gpu_slot?_`
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/ROCm.png"
                    />
                    <span>${i.item.rocm_gpu_slot}</span>
                    <span class="indicator">GPU</span>
                  `:_``}
              ${i.item.tpu_slot?_`
                    <mwc-icon class="fg green indicator">view_module</mwc-icon>
                    <span>${i.item.tpu_slot}</span>
                    <span class="indicator">TPU</span>
                  `:_``}
              ${i.item.ipu_slot?_`
                    <mwc-icon class="fg green indicator">view_module</mwc-icon>
                    <span>${i.item.ipu_slot}</span>
                    <span class="indicator">IPU</span>
                  `:_``}
              ${i.item.atom_slot?_`
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/rebel.svg"
                    />
                    <span>${i.item.atom_slot}</span>
                    <span class="indicator">ATOM</span>
                  `:_``}
              ${i.item.warboy_slot?_`
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/furiosa.svg"
                    />
                    <span>${i.item.warboy_slot}</span>
                    <span class="indicator">Warboy</span>
                  `:_``}
              ${i.item.cuda_gpu_slot||i.item.cuda_fgpu_slot||i.item.rocm_gpu_slot||i.item.tpu_slot||i.item.ipu_slot||i.item.atom_slot||i.item.warboy_slot?_``:_`
                    <mwc-icon class="fg green indicator">view_module</mwc-icon>
                    <span>-</span>
                    <span class="indicator">GPU</span>
                  `}
            </div>
          </div>
        `,e)}usageRenderer(e,t,i){["batch","interactive","inference","running"].includes(this.condition)?b(_`
          <div class="vertical start start-justified layout">
            <div class="horizontal start-justified center layout">
              <div class="usage-items">CPU</div>
              <div class="horizontal start-justified center layout">
                <lablup-progress-bar
                  class="usage"
                  progress="${i.item.cpu_util/(100*i.item.cpu_slot)}"
                  description=""
                ></lablup-progress-bar>
              </div>
            </div>
            <div class="horizontal start-justified center layout">
              <div class="usage-items">RAM</div>
              <div class="horizontal start-justified center layout">
                <lablup-progress-bar
                  class="usage"
                  progress="${i.item.mem_current/(1e9*i.item.mem_slot)}"
                  description=""
                ></lablup-progress-bar>
              </div>
            </div>
            ${i.item.cuda_gpu_slot&&parseInt(i.item.cuda_gpu_slot)>0?_`
                  <div class="horizontal start-justified center layout">
                    <div class="usage-items">GPU(util)</div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${i.item.cuda_util/(100*i.item.cuda_gpu_slot)}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:_``}
            ${i.item.cuda_fgpu_slot&&parseFloat(i.item.cuda_fgpu_slot)>0?_`
                  <div class="horizontal start-justified center layout">
                    <div class="usage-items">GPU(util)</div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${i.item.cuda_util/(100*i.item.cuda_fgpu_slot)}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:_``}
            ${i.item.rocm_gpu_slot&&parseFloat(i.item.cuda_rocm_gpu_slot)>0?_`
                  <div class="horizontal start-justified center layout">
                    <div class="usage-items">GPU(util)</div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${i.item.rocm_util/(100*i.item.rocm_gpu_slot)}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:_``}
            ${i.item.cuda_fgpu_slot||i.item.rocm_gpu_slot?_`
                  <div class="horizontal start-justified center layout">
                    <div class="usage-items">GPU(mem)</div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${i.item.cuda_mem_ratio}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:_``}
            ${i.item.tpu_slot&&parseFloat(i.item.tpu_slot)>0?_`
                  <div class="horizontal start-justified center layout">
                    <div class="usage-items">TPU(util)</div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${i.item.tpu_util/(100*i.item.tpu_slot)}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:_``}
            ${i.item.ipu_slot&&parseFloat(i.item.ipu_slot)>0?_`
                  <div class="horizontal start-justified center layout">
                    <div class="usage-items">IPU(util)</div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${i.item.ipu_util/(100*i.item.ipu_slot)}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:_``}
            ${i.item.atom_slot&&parseFloat(i.item.atom_slot)>0?_`
                  <div class="horizontal start-justified center layout">
                    <div class="usage-items">ATOM(util)</div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${i.item.atom_util/(100*i.item.atom_slot)}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:_``}
            <div class="horizontal start-justified center layout">
              <div class="usage-items">I/O</div>
              <div
                style="font-size:8px;"
                class="horizontal start-justified center layout"
              >
                R: ${i.item.io_read_bytes_mb} MB / W:
                ${i.item.io_write_bytes_mb} MB
              </div>
            </div>
          </div>
        `,e):"finished"===this.condition&&b(_`
          <div class="layout horizontal center flex">
            <mwc-icon class="fg green indicator" style="margin-right:3px;">
              developer_board
            </mwc-icon>
            ${i.item.cpu_used_time.D?_`
                  <div class="vertical center-justified center layout">
                    <span style="font-size:11px">
                      ${i.item.cpu_used_time.D}
                    </span>
                    <span class="indicator">day</span>
                  </div>
                `:_``}
            ${i.item.cpu_used_time.H?_`
                  <div class="vertical center-justified center layout">
                    <span style="font-size:11px">
                      ${i.item.cpu_used_time.H}
                    </span>
                    <span class="indicator">hour</span>
                  </div>
                `:_``}
            ${i.item.cpu_used_time.M?_`
                  <div class="vertical start layout">
                    <span style="font-size:11px">
                      ${i.item.cpu_used_time.M}
                    </span>
                    <span class="indicator">min.</span>
                  </div>
                `:_``}
            ${i.item.cpu_used_time.S?_`
                  <div class="vertical start layout">
                    <span style="font-size:11px">
                      ${i.item.cpu_used_time.S}
                    </span>
                    <span class="indicator">sec.</span>
                  </div>
                `:_``}
            ${i.item.cpu_used_time.MS?_`
                  <div class="vertical start layout">
                    <span style="font-size:11px">
                      ${i.item.cpu_used_time.MS}
                    </span>
                    <span class="indicator">msec.</span>
                  </div>
                `:_``}
            ${i.item.cpu_used_time.NODATA?_`
                  <div class="vertical start layout">
                    <span style="font-size:11px">No data</span>
                  </div>
                `:_``}
          </div>
          <div class="layout horizontal center flex">
            <mwc-icon class="fg blue indicator" style="margin-right:3px;">
              device_hub
            </mwc-icon>
            <div class="vertical start layout">
              <span style="font-size:9px">
                ${i.item.io_read_bytes_mb}
                <span class="indicator">MB</span>
              </span>
              <span class="indicator">READ</span>
            </div>
            <div class="vertical start layout">
              <span style="font-size:8px">
                ${i.item.io_write_bytes_mb}
                <span class="indicator">MB</span>
              </span>
              <span class="indicator">WRITE</span>
            </div>
          </div>
        `,e)}reservationRenderer(e,t,i){b(_`
        <div class="layout vertical" style="padding:3px auto;">
          <span>${i.item.created_at_hr}</span>
          <lablup-shields
            app="${f("session.ElapsedTime")}"
            color="darkgreen"
            style="margin:3px 0;"
            description="${i.item.elapsed}"
            ui="round"
          ></lablup-shields>
        </div>
      `,e)}idleChecksHeaderRenderer(e,t){b(_`
        <div class="horizontal layout center">
          <div>${f("session.IdleChecks")}</div>
          <mwc-icon-button
            class="fg grey"
            icon="info"
            @click="${()=>this._openIdleChecksInfoDialog()}"
          ></mwc-icon-button>
        </div>
      `,e)}idleChecksRenderer(e,t,i){var s;const n=null===(s=Object.keys(i.item.idle_checks))||void 0===s?void 0:s.map((e=>{var t,s;const n=i.item.idle_checks[e],o=null==n?void 0:n.remaining;if(!o)return;const a=globalThis.backendaiclient.utils.elapsedTimeToTotalSeconds(o),r=null==n?void 0:n.remaining_time_type;let l,c="#527A42";return!a||a<3600?c="#e05d44":a<14400&&(c="#D8B541"),"utilization"===e&&(null==n?void 0:n.extra)&&(!a||a<14400)&&(c=this.getUtilizationCheckerColor(null===(t=null==n?void 0:n.extra)||void 0===t?void 0:t.resources,null===(s=null==n?void 0:n.extra)||void 0===s?void 0:s.thresholds_check_operator)),l="utilization"===e?_`
            <button
              class="idle-check-key"
              style="color:#42a5f5;"
              @mouseenter="${e=>{var t,s,n;return this._createUtilizationIdleCheckDropdown(e,null===(n=null===(s=null===(t=i.item.idle_checks)||void 0===t?void 0:t.utilization)||void 0===s?void 0:s.extra)||void 0===n?void 0:n.resources)}}"
              @mouseleave="${()=>this._removeUtilizationIdleCheckDropdown()}"
            >
              ${v("session."+this.idleChecksTable[e])}
            </button>
          `:_`
            <button class="idle-check-key" style="color:#222222;">
              ${v("session."+this.idleChecksTable[e])}
            </button>
          `,e in this.idleChecksTable?_`
            <div class="layout vertical" style="padding:3px auto;">
              <div style="margin:4px;">
                ${l}
                <br />
                <strong style="color:${c}">${o}</strong>
                <div class="idle-type">
                  ${v("session."+this.idleChecksTable[r])}
                </div>
              </div>
            </div>
          `:_``})),o=_`
      ${n}
    `;b(o,e)}agentRenderer(e,t,i){b(_`
        <div class="layout vertical">
          <span>${i.item.agent}</span>
        </div>
      `,e)}_toggleCheckbox(e){const t=this._selected_items.findIndex((t=>t.session_id==e.session_id));-1===t?this._selected_items.push(e):this._selected_items.splice(t,1),this._selected_items.length>0?this.multipleActionButtons.style.display="block":this.multipleActionButtons.style.display="none"}_aggregateSharedMemory(e){let t=0;return Object.keys(e).forEach((i=>{var s,n;t+=Number(null!==(n=null===(s=e[i])||void 0===s?void 0:s.shmem)&&void 0!==n?n:0)})),D.bytesToGiB(t)}checkboxRenderer(e,t,i){this._isRunning&&!this._isPreparing(i.item.status)||this._APIMajorVersion>4?b(_`
          <mwc-checkbox
            class="list-check"
            style="display:contents;"
            ?checked="${!0===i.item.checked}"
            @click="${()=>this._toggleCheckbox(i.item)}"
          ></mwc-checkbox>
        `,e):b(_``,e)}userInfoRenderer(e,t,i){const s="API"===this._connectionMode?i.item.access_key:i.item.user_email;b(_`
        <div class="layout vertical">
          <span class="indicator">${this._getUserId(s)}</span>
        </div>
      `,e)}statusRenderer(e,t,i){var s;b(_`
        <div class="horizontal layout center">
          <span style="font-size: 12px;">${i.item.status}</span>
          ${i.item.status_data&&"{}"!==i.item.status_data?_`
                <mwc-icon-button
                  class="fg green status"
                  icon="help"
                  @click="${()=>{var e;return this._openStatusDetailDialog(null!==(e=i.item.status_info)&&void 0!==e?e:"",i.item.status_data,i.item.starts_at_hr)}}"
                ></mwc-icon-button>
              `:_``}
        </div>
        ${i.item.status_info?_`
              <div class="layout horizontal">
                <lablup-shields
                  id="${i.item.name}"
                  app=""
                  color="${this.statusColorTable[i.item.status_info]}"
                  description="${i.item.status_info}"
                  ui="round"
                ></lablup-shields>
              </div>
            `:_``}
        ${this._isContainerCommitEnabled&&void 0!==(null===(s=i.item)||void 0===s?void 0:s.commit_status)?_`
              <lablup-shields
                app=""
                color="${this._setColorOfStatusInformation(i.item.commit_status)}"
                class="right-below-margin"
                description=${"ongoing"===i.item.commit_status?"commit on-going":""}
              ></lablup-shields>
            `:_``}
      `,e)}_setColorOfStatusInformation(e="ready"){return"ready"===e?"green":"lightgrey"}_getUserId(e=""){if(e&&this.isUserInfoMaskEnabled){const t=/^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/.test(e),i=t?2:0,s=t?e.split("@")[0].length-i:0;e=globalThis.backendaiutils._maskString(e,"*",i,s)}return e}_renderCommitSessionConfirmationDialog(e){var t,i,s;return _`
      <backend-ai-dialog id="commit-session-dialog" fixed backdrop>
        <span slot="title">${f("session.CommitSession")}</span>
        <div slot="content" class="vertical layout center flex">
          <span style="font-size:14px;margin:auto 20px;">
            ${f("session.DescCommitSession")}
          </span>
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
              <span class="subheading">
                <strong>Environment and Version</strong>
              </span>
              <span class="monospace" slot="secondary">
                ${e?_`
                      <lablup-shields
                        app="${""===e.environment?"-":e.environment}"
                        color="blue"
                        description="${""===e.version?"-":e.version}"
                        ui="round"
                        class="right-below-margin"
                      ></lablup-shields>
                    `:_``}
              </span>
            </mwc-list-item>
            <mwc-list-item twoline noninteractive class="commit-session-info">
              <span class="subheading">Tags</span>
              <span class="monospace horizontal layout" slot="secondary">
                ${e?null===(s=null==e?void 0:e.tags)||void 0===s?void 0:s.map((e=>_`
                        <lablup-shields
                          app=""
                          color="green"
                          description="${e}"
                          ui="round"
                          class="right-below-margin"
                        ></lablup-shields>
                      `)):_`
                      <lablup-shields
                        app=""
                        color="green"
                        description="-"
                        ui="round"
                        style="right-below-margin"
                      ></lablup-shields>
                    `}
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
            label="${f("button.Commit")}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}_parseSessionInfoToCommitSessionInfo(e="",t="",i=""){const s=["",""],[n,o]=e?e.split(":"):s,[a,...r]=o?o.split("-"):s;return{environment:n,version:a,tags:r,session:{name:t,id:i}}}render(){var e,t,i;return _`
      <link rel="stylesheet" href="resources/custom.css">
      <div class="layout horizontal center filters">
        <div id="multiple-action-buttons" style="display:none;">
          <mwc-button icon="delete" class="multiple-action-button" raised style="margin:8px;"
                           @click="${()=>this._openTerminateSelectedSessionsDialog()}">${f("session.Terminate")}</mwc-button>
        </div>
        <span class="flex"></span>
        <div class="vertical layout" style="display:none">
          <mwc-textfield id="access-key-filter" type="search" maxLength="64"
                      label="${f("general.AccessKey")}" no-label-float .value="${this.filterAccessKey}"
                      style="margin-right:20px;"
                      @change="${e=>this._updateFilterAccessKey(e)}">
          </mwc-textfield>
          <span id="access-key-filter-helper-text">${f("maxLength.64chars")}</span>
        </div>
      </div>
      <div class="list-wrapper">
        <vaadin-grid id="list-grid" theme="row-stripes column-borders compact" aria-label="Session list"
          .items="${this.compute_sessions}" height-by-rows>
          ${this._isRunning?_`
                  <vaadin-grid-column
                    frozen
                    width="60px"
                    flex-grow="0"
                    text-align="center"
                    .renderer="${this._boundCheckboxRenderer}"
                  ></vaadin-grid-column>
                `:_``}
          <vaadin-grid-column frozen width="40px" flex-grow="0" header="#" .renderer="${this._indexRenderer}"></vaadin-grid-column>
          ${this.is_admin?_`
                  <lablup-grid-sort-filter-column
                    frozen
                    path="${"API"===this._connectionMode?"access_key":"user_email"}"
                    header="${"API"===this._connectionMode?"API Key":"User ID"}"
                    resizable
                    .renderer="${this._boundUserInfoRenderer}"
                  ></lablup-grid-sort-filter-column>
                `:_``}
          <lablup-grid-sort-filter-column frozen path="${this.sessionNameField}" auto-width header="${f("session.SessionInfo")}" resizable
                                     .renderer="${this._boundSessionInfoRenderer}">
          </lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column width="120px" path="status" header="${f("session.Status")}" resizable
                                     .renderer="${this._boundStatusRenderer}">
          </lablup-grid-sort-filter-column>
          <vaadin-grid-column width=${this._isContainerCommitEnabled?"260px":"210px"} flex-grow="0" resizable header="${f("general.Control")}"
                              .renderer="${this._boundControlRenderer}"></vaadin-grid-column>
          <vaadin-grid-column width="200px" flex-grow="0" resizable header="${f("session.Configuration")}"
                              .renderer="${this._boundConfigRenderer}"></vaadin-grid-column>
          <vaadin-grid-column width="140px" flex-grow="0" resizable header="${f("session.Usage")}"
                              .renderer="${this._boundUsageRenderer}">
          </vaadin-grid-column>
          <vaadin-grid-sort-column resizable width="180px" flex-grow="0" header="${f("session.Reservation")}"
                                   path="created_at" .renderer="${this._boundReservationRenderer}">
          </vaadin-grid-sort-column>
          ${globalThis.backendaiclient.supports("idle-checks")&&this.activeIdleCheckList.size>0?_`
                  <vaadin-grid-column
                    resizable
                    auto-width
                    flex-grow="0"
                    .headerRenderer="${this._boundIdleChecksHeaderderer}"
                    .renderer="${this._boundIdleChecksRenderer}"
                  ></vaadin-grid-column>
                `:_``}
          <lablup-grid-sort-filter-column width="110px" path="architecture" header="${f("session.Architecture")}" resizable
                                     .renderer="${this._boundArchitectureRenderer}">
          </lablup-grid-sort-filter-column>
          ${this._isIntegratedCondition?_`
                  <lablup-grid-sort-filter-column
                    path="type"
                    width="140px"
                    flex-grow="0"
                    header="${f("session.launcher.SessionType")}"
                    resizable
                    .renderer="${this._boundSessionTypeRenderer}"
                  ></lablup-grid-sort-filter-column>
                `:_``}
          ${this.is_superadmin||!globalThis.backendaiclient._config.hideAgents?_`
                  <lablup-grid-sort-filter-column
                    path="agent"
                    auto-width
                    flex-grow="0"
                    resizable
                    header="${f("session.Agent")}"
                    .renderer="${this._boundAgentRenderer}"
                  ></lablup-grid-sort-filter-column>
                `:_``}
          </vaadin-grid>
          <backend-ai-list-status id="list-status" statusCondition="${this.listCondition}" message="${v("session.NoSessionToDisplay")}"></backend-ai-list-status>
        </div>
      </div>
      <div class="horizontal center-justified layout flex" style="padding: 10px;">
        <mwc-icon-button
          class="pagination"
          id="previous-page"
          icon="navigate_before"
          ?disabled="${1===this.current_page}"
          @click="${e=>this._updateSessionPage(e)}"></mwc-icon-button>
        <div class="pagination-label">
        ${this.current_page} / ${Math.ceil(this.total_session_count/this.session_page_limit)}</div>
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
        <iframe id="work-page" style="border-style: none;display: none;width: 100%;"></iframe>
      </backend-ai-dialog>
      <backend-ai-dialog id="terminate-session-dialog" fixed backdrop>
        <span slot="title">${f("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${f("usersettings.SessionTerminationDialog")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button class="warning fg red" @click="${()=>this._terminateSessionWithCheck(!0)}">
            ${f("button.ForceTerminate")}
          </mwc-button>
          <span class="flex"></span>
          <mwc-button class="cancel" @click="${e=>this._hideDialog(e)}">${f("button.Cancel")}
          </mwc-button>
          <mwc-button class="ok" raised @click="${()=>this._terminateSessionWithCheck()}">${f("button.Okay")}</mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="terminate-selected-sessions-dialog" fixed backdrop>
        <span slot="title">${f("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${f("usersettings.SessionTerminationDialog")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button class="warning fg red"
                      @click="${()=>this._terminateSelectedSessionsWithCheck(!0)}">${f("button.ForceTerminate")}
          </mwc-button>
          <span class="flex"></span>
          <mwc-button class="cancel" @click="${e=>this._hideDialog(e)}">${f("button.Cancel")}
          </mwc-button>
          <mwc-button class="ok" raised @click="${()=>this._terminateSelectedSessionsWithCheck()}">${f("button.Okay")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="status-detail-dialog" narrowLayout fixed backdrop>
        <span slot="title">${f("session.StatusInfo")}</span>
        <div slot="content" id="status-detail"></div>
      </backend-ai-dialog>
      <backend-ai-dialog id="help-description" narrowLayout fixed backdrop>
        <span slot="title">${this._helpDescriptionTitle}</span>
        <div slot="content" class="horizontal layout center" style="margin:5px;">
        ${""==this._helpDescriptionIcon?_``:_`
                <img
                  slot="graphic"
                  alt="help icon"
                  src="resources/icons/${this._helpDescriptionIcon}"
                  style="width:64px;height:64px;margin-right:10px;"
                />
              `}
          <div style="font-size:14px;">${y(this._helpDescription)}</div>
        </div>
      </backend-ai-dialog>
      ${this._renderCommitSessionConfirmationDialog(this._parseSessionInfoToCommitSessionInfo(null===(e=this.commitSessionDialog)||void 0===e?void 0:e.kernelImage,null===(t=this.commitSessionDialog)||void 0===t?void 0:t.sessionName,null===(i=this.commitSessionDialog)||void 0===i?void 0:i.sessionId))}
    `}_updateSessionPage(e){"previous-page"===e.target.id?this.current_page-=1:this.current_page+=1,this.refreshList()}};var R;r([l({type:Boolean,reflect:!0})],E.prototype,"active",void 0),r([l({type:String})],E.prototype,"condition",void 0),r([l({type:Object})],E.prototype,"jobs",void 0),r([l({type:Array})],E.prototype,"compute_sessions",void 0),r([l({type:Array})],E.prototype,"terminationQueue",void 0),r([l({type:String})],E.prototype,"filterAccessKey",void 0),r([l({type:String})],E.prototype,"sessionNameField",void 0),r([l({type:Array})],E.prototype,"appSupportList",void 0),r([l({type:Object})],E.prototype,"appTemplate",void 0),r([l({type:Object})],E.prototype,"imageInfo",void 0),r([l({type:Array})],E.prototype,"_selected_items",void 0),r([l({type:Object})],E.prototype,"_boundControlRenderer",void 0),r([l({type:Object})],E.prototype,"_boundConfigRenderer",void 0),r([l({type:Object})],E.prototype,"_boundUsageRenderer",void 0),r([l({type:Object})],E.prototype,"_boundReservationRenderer",void 0),r([l({type:Object})],E.prototype,"_boundIdleChecksHeaderderer",void 0),r([l({type:Object})],E.prototype,"_boundIdleChecksRenderer",void 0),r([l({type:Object})],E.prototype,"_boundAgentRenderer",void 0),r([l({type:Object})],E.prototype,"_boundSessionInfoRenderer",void 0),r([l({type:Object})],E.prototype,"_boundArchitectureRenderer",void 0),r([l({type:Object})],E.prototype,"_boundCheckboxRenderer",void 0),r([l({type:Object})],E.prototype,"_boundUserInfoRenderer",void 0),r([l({type:Object})],E.prototype,"_boundStatusRenderer",void 0),r([l({type:Object})],E.prototype,"_boundSessionTypeRenderer",void 0),r([l({type:Boolean})],E.prototype,"refreshing",void 0),r([l({type:Boolean})],E.prototype,"is_admin",void 0),r([l({type:Boolean})],E.prototype,"is_superadmin",void 0),r([l({type:String})],E.prototype,"_connectionMode",void 0),r([l({type:Object})],E.prototype,"notification",void 0),r([l({type:Boolean})],E.prototype,"enableScalingGroup",void 0),r([l({type:Boolean})],E.prototype,"isDisplayingAllocatedShmemEnabled",void 0),r([l({type:String})],E.prototype,"listCondition",void 0),r([l({type:Object})],E.prototype,"refreshTimer",void 0),r([l({type:Object})],E.prototype,"kernel_labels",void 0),r([l({type:Object})],E.prototype,"kernel_icons",void 0),r([l({type:Object})],E.prototype,"indicator",void 0),r([l({type:String})],E.prototype,"_helpDescription",void 0),r([l({type:String})],E.prototype,"_helpDescriptionTitle",void 0),r([l({type:String})],E.prototype,"_helpDescriptionIcon",void 0),r([l({type:Set})],E.prototype,"activeIdleCheckList",void 0),r([l({type:Proxy})],E.prototype,"statusColorTable",void 0),r([l({type:Proxy})],E.prototype,"idleChecksTable",void 0),r([l({type:Proxy})],E.prototype,"sessionTypeColorTable",void 0),r([l({type:Number})],E.prototype,"sshPort",void 0),r([l({type:Number})],E.prototype,"vncPort",void 0),r([l({type:Number})],E.prototype,"current_page",void 0),r([l({type:Number})],E.prototype,"session_page_limit",void 0),r([l({type:Number})],E.prototype,"total_session_count",void 0),r([l({type:Number})],E.prototype,"_APIMajorVersion",void 0),r([l({type:Object})],E.prototype,"selectedSessionStatus",void 0),r([l({type:Boolean})],E.prototype,"isUserInfoMaskEnabled",void 0),r([c("#loading-spinner")],E.prototype,"spinner",void 0),r([c("#list-grid")],E.prototype,"_grid",void 0),r([c("#access-key-filter")],E.prototype,"accessKeyFilterInput",void 0),r([c("#multiple-action-buttons")],E.prototype,"multipleActionButtons",void 0),r([c("#access-key-filter-helper-text")],E.prototype,"accessKeyFilterHelperText",void 0),r([c("#terminate-session-dialog")],E.prototype,"terminateSessionDialog",void 0),r([c("#terminate-selected-sessions-dialog")],E.prototype,"terminateSelectedSessionsDialog",void 0),r([c("#status-detail-dialog")],E.prototype,"sessionStatusInfoDialog",void 0),r([c("#work-dialog")],E.prototype,"workDialog",void 0),r([c("#help-description")],E.prototype,"helpDescriptionDialog",void 0),r([c("#commit-session-dialog")],E.prototype,"commitSessionDialog",void 0),r([c("#commit-current-session-path-input")],E.prototype,"commitSessionInput",void 0),r([c("#list-status")],E.prototype,"_listStatus",void 0),E=D=r([d("backend-ai-session-list")],E);let j=R=class extends p{constructor(){super(),this._status="inactive",this.active=!1,this.is_admin=!1,this.enableInferenceWorkload=!1,this.enableSFTPSession=!1,this.filterAccessKey="",this._connectionMode="API",this._defaultFileName="",this.active=!1,this._status="inactive"}static get styles(){return[h,u,m,w,k,i`
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

        mwc-menu {
          --mdc-theme-surface: #f1f1f1;
          --mdc-menu-item-height: auto;
        }

        mwc-menu#dropdown-menu {
          position: relative;
          left: -170px;
          top: 50px;
        }

        mwc-list-item {
          font-size: 14px;
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
      `]}firstUpdated(){this.notification=globalThis.lablupNotification,document.addEventListener("backend-ai-session-list-refreshed",(()=>{this.runningJobs.refreshList(!0,!1)})),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.is_admin=globalThis.backendaiclient.is_admin,this._connectionMode=globalThis.backendaiclient._config._connectionMode}),!0):(this.is_admin=globalThis.backendaiclient.is_admin,this._connectionMode=globalThis.backendaiclient._config._connectionMode)}async _viewStateChanged(e){if(await this.updateComplete,!1===e){this.resourceMonitor.removeAttribute("active"),this._status="inactive";for(let e=0;e<this.sessionList.length;e++)this.sessionList[e].removeAttribute("active");return}const t=()=>{this.enableInferenceWorkload=globalThis.backendaiclient.supports("inference-workload"),this.enableSFTPSession=globalThis.backendaiclient.supports("sftp-scaling-group"),this.resourceMonitor.setAttribute("active","true"),this.runningJobs.setAttribute("active","true"),this._status="active"};void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{t()}),!0):t()}_toggleDialogCheckbox(e){const t=e.target,i=this.dateFromInput,s=this.dateToInput;i.disabled=t.checked,s.disabled=t.checked}_triggerClearTimeout(){const e=new CustomEvent("backend-ai-clear-timeout");document.dispatchEvent(e)}_showTab(e){var t,i,s;const n=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".tab-content");for(let e=0;e<n.length;e++)n[e].style.display="none";(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+e.title+"-lists")).style.display="block";for(let e=0;e<this.sessionList.length;e++)this.sessionList[e].removeAttribute("active");this._triggerClearTimeout(),(null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#"+e.title+"-jobs")).setAttribute("active","true")}_toggleDropdown(e){const t=this.dropdownMenu,i=e.target;t.anchor=i,t.open||t.show()}_openExportToCsvDialog(){const e=this.dropdownMenu;e.open&&e.close(),console.log("Downloading CSV File..."),this._defaultFileName=this._getDefaultCSVFileName(),this.exportToCsvDialog.show()}_getFirstDateOfMonth(){const e=new Date;return new Date(e.getFullYear(),e.getMonth(),2).toISOString().substring(0,10)}_getDefaultCSVFileName(){return(new Date).toISOString().substring(0,10)+"_"+(new Date).toTimeString().slice(0,8).replace(/:/gi,"-")}_validateDateRange(){const e=this.dateToInput,t=this.dateFromInput;if(e.value&&t.value){new Date(e.value).getTime()<new Date(t.value).getTime()&&(e.value=t.value)}}_automaticScaledTime(e){let t=Object();const i=["D","H","M","S"],s=[864e5,36e5,6e4,1e3];for(let n=0;n<s.length;n++)Math.floor(e/s[n])>0&&(t[i[n]]=Math.floor(e/s[n]),e%=s[n]);return 0===Object.keys(t).length&&(t=e>0?{MS:e}:{NODATA:1}),t}static bytesToMiB(e,t=1){return Number(e/2**20).toFixed(1)}_exportToCSV(){const e=this.exportFileNameInput;if(!e.validity.valid)return;const t=[];let i;i=globalThis.backendaiclient.supports("avoid-hol-blocking")?["RUNNING","RESTARTING","TERMINATING","PENDING","SCHEDULED","PREPARING","PULLING","TERMINATED","CANCELLED","ERROR"]:["RUNNING","RESTARTING","TERMINATING","PENDING","PREPARING","PULLING","TERMINATED","CANCELLED","ERROR"],globalThis.backendaiclient.supports("detailed-session-states")&&(i=i.join(","));const s=["id","name","image","created_at","terminated_at","status","status_info","access_key"];"SESSION"===this._connectionMode&&s.push("user_email"),globalThis.backendaiclient.is_superadmin?s.push("containers {container_id agent occupied_slots live_stat last_stat}"):s.push("containers {container_id occupied_slots live_stat last_stat}");const n=globalThis.backendaiclient.current_group_id();globalThis.backendaiclient.computeSession.listAll(s,i,this.filterAccessKey,100,0,n).then((i=>{const s=i;if(0===s.length)return this.notification.text=v("session.NoSession"),this.notification.show(),void this.exportToCsvDialog.hide();s.forEach((e=>{const i={};if(i.id=e.id,i.name=e.name,i.image=e.image.split("/")[2]||e.image.split("/")[1],i.status=e.status,i.status_info=e.status_info,i.access_key=e.access_key,i.created_at=e.created_at,i.terminated_at=e.terminated_at,e.containers&&e.containers.length>0){const t=e.containers[0];i.container_id=t.container_id;const s=t.occupied_slots?JSON.parse(t.occupied_slots):null;s&&(i.cpu_slot=parseInt(s.cpu),i.mem_slot=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(s.mem,"g")).toFixed(2),s["cuda.shares"]&&(i.cuda_shares=s["cuda.shares"]),s["cuda.device"]&&(i.cuda_device=s["cuda.device"]),s["tpu.device"]&&(i.tpu_device=s["tpu.device"]),s["rocm.device"]&&(i.rocm_device=s["rocm.device"]),s["ipu.device"]&&(i.ipu_device=s["ipu.device"]),s["atom.device"]&&(i.atom_device=s["atom.device"]),s["warboy.device"]&&(i.warboy_device=s["warboy.device"]));const n=t.live_stat?JSON.parse(t.live_stat):null;n&&(n.cpu_used&&n.cpu_used.current?i.cpu_used_time=this._automaticScaledTime(n.cpu_used.current):i.cpu_used_time=0,n.io_read?i.io_read_bytes_mb=R.bytesToMiB(n.io_read.current):i.io_read_bytes_mb=0,n.io_write?i.io_write_bytes_mb=R.bytesToMiB(n.io_write.current):i.io_write_bytes_mb=0),t.agent&&(i.agent=t.agent)}t.push(i)})),x.exportToCsv(e.value,t),this.notification.text=v("session.DownloadingCSVFile"),this.notification.show(),this.exportToCsvDialog.hide()}))}render(){return _`
      <link rel="stylesheet" href="resources/custom.css" />
      <lablup-activity-panel
        title="${f("summary.ResourceStatistics")}"
        elevation="1"
        autowidth
      >
        <div slot="message">
          <backend-ai-resource-monitor
            location="session"
            id="resource-monitor"
            ?active="${!0===this.active}"
          ></backend-ai-resource-monitor>
        </div>
      </lablup-activity-panel>
      <lablup-activity-panel
        title="${f("summary.Announcement")}"
        elevation="1"
        horizontalsize="2x"
        style="display:none;"
      ></lablup-activity-panel>
      <lablup-activity-panel elevation="1" autowidth narrow noheader>
        <div slot="message">
          <h3
            class="tab horizontal center layout"
            style="margin-top:0;margin-bottom:0;"
          >
            <div class="scroll hide-scrollbar">
              <div
                class="horizontal layout flex start-justified"
                style="width:70%;"
              >
                <mwc-tab-bar>
                  <mwc-tab
                    title="running"
                    label="${f("session.Running")}"
                    @click="${e=>this._showTab(e.target)}"
                  ></mwc-tab>
                  <mwc-tab
                    title="interactive"
                    label="${f("session.Interactive")}"
                    @click="${e=>this._showTab(e.target)}"
                  ></mwc-tab>
                  <mwc-tab
                    title="batch"
                    label="${f("session.Batch")}"
                    @click="${e=>this._showTab(e.target)}"
                  ></mwc-tab>
                  ${this.enableInferenceWorkload?_`
                        <mwc-tab
                          title="inference"
                          label="${f("session.Inference")}"
                          @click="${e=>this._showTab(e.target)}"
                        ></mwc-tab>
                      `:_``}
                  ${this.enableSFTPSession?_`
                        <mwc-tab
                          title="system"
                          label="${f("session.System")}"
                          @click="${e=>this._showTab(e.target)}"
                        ></mwc-tab>
                      `:_``}
                  <mwc-tab
                    title="finished"
                    label="${f("session.Finished")}"
                    @click="${e=>this._showTab(e.target)}"
                  ></mwc-tab>
                </mwc-tab-bar>
              </div>
            </div>
            ${this.is_admin?_`
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
                          class="horizontal layout start center"
                          @click="${()=>this._openExportToCsvDialog()}"
                        >
                          <mwc-icon style="color:#242424;padding-right:10px;">
                            get_app
                          </mwc-icon>
                          ${f("session.exportCSV")}
                        </a>
                      </mwc-list-item>
                    </mwc-menu>
                  </div>
                `:_``}
            <div
              class="horizontal layout flex end-justified"
              style="margin-right:20px;"
            >
              <backend-ai-session-launcher
                location="session"
                id="session-launcher"
                ?active="${!0===this.active}"
              ></backend-ai-session-launcher>
            </div>
          </h3>
          <div id="running-lists" class="tab-content">
            <backend-ai-session-list
              id="running-jobs"
              condition="running"
            ></backend-ai-session-list>
          </div>
          <div id="interactive-lists" class="tab-content" style="display:none;">
            <backend-ai-session-list
              id="interactive-jobs"
              condition="interactive"
            ></backend-ai-session-list>
          </div>
          <div id="batch-lists" class="tab-content" style="display:none;">
            <backend-ai-session-list
              id="batch-jobs"
              condition="batch"
            ></backend-ai-session-list>
          </div>
          ${this.enableInferenceWorkload?_`
                <div
                  id="inference-lists"
                  class="tab-content"
                  style="display:none;"
                >
                  <backend-ai-session-list
                    id="inference-jobs"
                    condition="inference"
                  ></backend-ai-session-list>
                </div>
              `:_``}
          ${this.enableSFTPSession?_`
                <div
                  id="system-lists"
                  class="tab-content"
                  style="display:none;"
                >
                  <backend-ai-session-list
                    id="system-jobs"
                    condition="system"
                  ></backend-ai-session-list>
                </div>
              `:_``}
          <div id="finished-lists" class="tab-content" style="display:none;">
            <backend-ai-session-list
              id="finished-jobs"
              condition="finished"
            ></backend-ai-session-list>
          </div>
          <div id="others-lists" class="tab-content" style="display:none;">
            <backend-ai-session-list
              id="others-jobs"
              condition="others"
            ></backend-ai-session-list>
          </div>
        </div>
      </lablup-activity-panel>
      <backend-ai-dialog id="export-to-csv" fixed backdrop>
        <span slot="title">${f("session.ExportSessionListToCSVFile")}</span>
        <div slot="content">
          <mwc-textfield
            id="export-file-name"
            label="File name"
            validationMessage="${f("data.explorer.ValueRequired")}"
            value="${"session_"+this._defaultFileName}"
            required
            style="margin-bottom:10px;"
          ></mwc-textfield>
          <div class="horizontal center layout" style="display:none;">
            <mwc-textfield
              id="date-from"
              label="From"
              type="date"
              style="margin-right:10px;"
              value="${this._getFirstDateOfMonth()}"
              required
              @change="${this._validateDateRange}"
            ></mwc-textfield>
            <mwc-textfield
              id="date-to"
              label="To"
              type="date"
              value="${(new Date).toISOString().substring(0,10)}"
              required
              @change="${this._validateDateRange}"
            ></mwc-textfield>
          </div>
          <div class="horizontal center layout">
            <mwc-formfield label="Export All-time data">
              <mwc-checkbox
                id="export-csv-checkbox"
                @change="${e=>this._toggleDialogCheckbox(e)}"
              ></mwc-checkbox>
            </mwc-formfield>
          </div>
        </div>
        <div slot="footer" class="horizontal flex layout">
          <mwc-button
            unelevated
            fullwidth
            icon="get_app"
            label="${f("session.ExportCSVFile")}"
            @click="${this._exportToCSV}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};r([l({type:String})],j.prototype,"_status",void 0),r([l({type:Boolean,reflect:!0})],j.prototype,"active",void 0),r([l({type:Boolean})],j.prototype,"is_admin",void 0),r([l({type:Boolean})],j.prototype,"enableInferenceWorkload",void 0),r([l({type:Boolean})],j.prototype,"enableSFTPSession",void 0),r([l({type:String})],j.prototype,"filterAccessKey",void 0),r([l({type:String})],j.prototype,"_connectionMode",void 0),r([l({type:Object})],j.prototype,"_defaultFileName",void 0),r([function(t){return e({descriptor:e=>({get(){var e,i;return null!==(i=null===(e=this.renderRoot)||void 0===e?void 0:e.querySelectorAll(t))&&void 0!==i?i:[]},enumerable:!0,configurable:!0})})}("backend-ai-session-list")],j.prototype,"sessionList",void 0),r([c("#running-jobs")],j.prototype,"runningJobs",void 0),r([c("#resource-monitor")],j.prototype,"resourceMonitor",void 0),r([c("#export-file-name")],j.prototype,"exportFileNameInput",void 0),r([c("#date-from")],j.prototype,"dateFromInput",void 0),r([c("#date-to")],j.prototype,"dateToInput",void 0),r([c("#dropdown-menu")],j.prototype,"dropdownMenu",void 0),r([c("#export-to-csv")],j.prototype,"exportToCsvDialog",void 0),j=R=r([d("backend-ai-session-view")],j);
