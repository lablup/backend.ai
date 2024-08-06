import{l as e,r as t,i,m as s,o,T as n,D as a,P as l,_ as r,n as c,e as d,t as p,B as u,b as h,I as m,a as g,d as v,p as b,x as _,g as f,f as y,q as w,u as k,c as x}from"./backend-ai-webui-Cvl-SpQz.js";import{J as A}from"./vaadin-iconset-BZvLGWCK.js";import"./backend-ai-resource-monitor-CC5VpAfR.js";import"./backend-ai-session-launcher-D0P9lnX7.js";import"./backend-ai-list-status-f8CFHFrI.js";import"./lablup-grid-sort-filter-column-yAr0uBsO.js";import"./lablup-progress-bar-EimNTyGU.js";import{i as S}from"./vaadin-grid-BXsNAAkf.js";import"./vaadin-grid-filter-column-CSCqhIok.js";import"./vaadin-grid-selection-column-DJf--6Dp.js";import"./vaadin-grid-sort-column-pQVDIafs.js";import"./lablup-activity-panel-BAVa23-B.js";import"./mwc-formfield-C7IvV2gO.js";import"./mwc-tab-bar-D9RZyju8.js";import"./mwc-switch-Dl-Uk4v9.js";import"./mwc-check-list-item-BwnFSR0R.js";import"./dir-utils-BVJL0QLI.js";import"./active-mixin-lW8Qt-OC.js";
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */let $;var T;!function(e){e[e.EOS=0]="EOS",e[e.Text=1]="Text",e[e.Incomplete=2]="Incomplete",e[e.ESC=3]="ESC",e[e.Unknown=4]="Unknown",e[e.SGR=5]="SGR",e[e.OSCURL=6]="OSCURL"}(T||(T={}));var C=function(){function e(){this.VERSION="4.0.3",this.setup_palettes(),this._use_classes=!1,this._escape_for_html=!0,this.bold=!1,this.fg=this.bg=null,this._buffer="",this._url_whitelist={http:1,https:1}}return Object.defineProperty(e.prototype,"use_classes",{get:function(){return this._use_classes},set:function(e){this._use_classes=e},enumerable:!0,configurable:!0}),Object.defineProperty(e.prototype,"escape_for_html",{get:function(){return this._escape_for_html},set:function(e){this._escape_for_html=e},enumerable:!0,configurable:!0}),Object.defineProperty(e.prototype,"url_whitelist",{get:function(){return this._url_whitelist},set:function(e){this._url_whitelist=e},enumerable:!0,configurable:!0}),e.prototype.setup_palettes=function(){var e=this;this.ansi_colors=[[{rgb:[0,0,0],class_name:"ansi-black"},{rgb:[187,0,0],class_name:"ansi-red"},{rgb:[0,187,0],class_name:"ansi-green"},{rgb:[187,187,0],class_name:"ansi-yellow"},{rgb:[0,0,187],class_name:"ansi-blue"},{rgb:[187,0,187],class_name:"ansi-magenta"},{rgb:[0,187,187],class_name:"ansi-cyan"},{rgb:[255,255,255],class_name:"ansi-white"}],[{rgb:[85,85,85],class_name:"ansi-bright-black"},{rgb:[255,85,85],class_name:"ansi-bright-red"},{rgb:[0,255,0],class_name:"ansi-bright-green"},{rgb:[255,255,85],class_name:"ansi-bright-yellow"},{rgb:[85,85,255],class_name:"ansi-bright-blue"},{rgb:[255,85,255],class_name:"ansi-bright-magenta"},{rgb:[85,255,255],class_name:"ansi-bright-cyan"},{rgb:[255,255,255],class_name:"ansi-bright-white"}]],this.palette_256=[],this.ansi_colors.forEach((function(t){t.forEach((function(t){e.palette_256.push(t)}))}));for(var t=[0,95,135,175,215,255],i=0;i<6;++i)for(var s=0;s<6;++s)for(var o=0;o<6;++o){var n={rgb:[t[i],t[s],t[o]],class_name:"truecolor"};this.palette_256.push(n)}for(var a=8,l=0;l<24;++l,a+=10){var r={rgb:[a,a,a],class_name:"truecolor"};this.palette_256.push(r)}},e.prototype.escape_txt_for_html=function(e){return e.replace(/[&<>]/gm,(function(e){return"&"===e?"&amp;":"<"===e?"&lt;":">"===e?"&gt;":void 0}))},e.prototype.append_buffer=function(e){var t=this._buffer+e;this._buffer=t},e.prototype.__makeTemplateObject=function(e,t){return Object.defineProperty?Object.defineProperty(e,"raw",{value:t}):e.raw=t,e},e.prototype.get_next_packet=function(){var e={kind:T.EOS,text:"",url:""},t=this._buffer.length;if(0==t)return e;var i,s,o,n,a=this._buffer.indexOf("");if(-1==a)return e.kind=T.Text,e.text=this._buffer,this._buffer="",e;if(a>0)return e.kind=T.Text,e.text=this._buffer.slice(0,a),this._buffer=this._buffer.slice(a),e;if(0==a){if(1==t)return e.kind=T.Incomplete,e;var l=this._buffer.charAt(1);if("["!=l&&"]"!=l)return e.kind=T.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;if("["==l){if(this._csi_regex||(this._csi_regex=I(this.__makeTemplateObject(["\n                        ^                           # beginning of line\n                                                    #\n                                                    # First attempt\n                        (?:                         # legal sequence\n                          [                      # CSI\n                          ([<-?]?)              # private-mode char\n                          ([d;]*)                    # any digits or semicolons\n                          ([ -/]?               # an intermediate modifier\n                          [@-~])                # the command\n                        )\n                        |                           # alternate (second attempt)\n                        (?:                         # illegal sequence\n                          [                      # CSI\n                          [ -~]*                # anything legal\n                          ([\0-:])              # anything illegal\n                        )\n                    "],["\n                        ^                           # beginning of line\n                                                    #\n                                                    # First attempt\n                        (?:                         # legal sequence\n                          \\x1b\\[                      # CSI\n                          ([\\x3c-\\x3f]?)              # private-mode char\n                          ([\\d;]*)                    # any digits or semicolons\n                          ([\\x20-\\x2f]?               # an intermediate modifier\n                          [\\x40-\\x7e])                # the command\n                        )\n                        |                           # alternate (second attempt)\n                        (?:                         # illegal sequence\n                          \\x1b\\[                      # CSI\n                          [\\x20-\\x7e]*                # anything legal\n                          ([\\x00-\\x1f:])              # anything illegal\n                        )\n                    "]))),null===(d=this._buffer.match(this._csi_regex)))return e.kind=T.Incomplete,e;if(d[4])return e.kind=T.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;""!=d[1]||"m"!=d[3]?e.kind=T.Unknown:e.kind=T.SGR,e.text=d[2];var r=d[0].length;return this._buffer=this._buffer.slice(r),e}if("]"==l){if(t<4)return e.kind=T.Incomplete,e;if("8"!=this._buffer.charAt(2)||";"!=this._buffer.charAt(3))return e.kind=T.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;this._osc_st||(this._osc_st=(i=this.__makeTemplateObject(["\n                        (?:                         # legal sequence\n                          (\\)                    # ESC                           |                           # alternate\n                          ()                      # BEL (what xterm did)\n                        )\n                        |                           # alternate (second attempt)\n                        (                           # illegal sequence\n                          [\0-]                 # anything illegal\n                          |                           # alternate\n                          [\b-]                 # anything illegal\n                          |                           # alternate\n                          [-]                 # anything illegal\n                        )\n                    "],["\n                        (?:                         # legal sequence\n                          (\\x1b\\\\)                    # ESC \\\n                          |                           # alternate\n                          (\\x07)                      # BEL (what xterm did)\n                        )\n                        |                           # alternate (second attempt)\n                        (                           # illegal sequence\n                          [\\x00-\\x06]                 # anything illegal\n                          |                           # alternate\n                          [\\x08-\\x1a]                 # anything illegal\n                          |                           # alternate\n                          [\\x1c-\\x1f]                 # anything illegal\n                        )\n                    "]),s=i.raw[0],o=/^\s+|\s+\n|\s*#[\s\S]*?\n|\n/gm,n=s.replace(o,""),new RegExp(n,"g"))),this._osc_st.lastIndex=0;var c=this._osc_st.exec(this._buffer);if(null===c)return e.kind=T.Incomplete,e;if(c[3])return e.kind=T.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;var d,p=this._osc_st.exec(this._buffer);if(null===p)return e.kind=T.Incomplete,e;if(p[3])return e.kind=T.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;if(this._osc_regex||(this._osc_regex=I(this.__makeTemplateObject(["\n                        ^                           # beginning of line\n                                                    #\n                        ]8;                    # OSC Hyperlink\n                        [ -:<-~]*       # params (excluding ;)\n                        ;                           # end of params\n                        ([!-~]{0,512})        # URL capture\n                        (?:                         # ST\n                          (?:\\)                  # ESC                           |                           # alternate\n                          (?:)                    # BEL (what xterm did)\n                        )\n                        ([!-~]+)              # TEXT capture\n                        ]8;;                   # OSC Hyperlink End\n                        (?:                         # ST\n                          (?:\\)                  # ESC                           |                           # alternate\n                          (?:)                    # BEL (what xterm did)\n                        )\n                    "],["\n                        ^                           # beginning of line\n                                                    #\n                        \\x1b\\]8;                    # OSC Hyperlink\n                        [\\x20-\\x3a\\x3c-\\x7e]*       # params (excluding ;)\n                        ;                           # end of params\n                        ([\\x21-\\x7e]{0,512})        # URL capture\n                        (?:                         # ST\n                          (?:\\x1b\\\\)                  # ESC \\\n                          |                           # alternate\n                          (?:\\x07)                    # BEL (what xterm did)\n                        )\n                        ([\\x21-\\x7e]+)              # TEXT capture\n                        \\x1b\\]8;;                   # OSC Hyperlink End\n                        (?:                         # ST\n                          (?:\\x1b\\\\)                  # ESC \\\n                          |                           # alternate\n                          (?:\\x07)                    # BEL (what xterm did)\n                        )\n                    "]))),null===(d=this._buffer.match(this._osc_regex)))return e.kind=T.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;e.kind=T.OSCURL,e.url=d[1],e.text=d[2];r=d[0].length;return this._buffer=this._buffer.slice(r),e}}},e.prototype.ansi_to_html=function(e){this.append_buffer(e);for(var t=[];;){var i=this.get_next_packet();if(i.kind==T.EOS||i.kind==T.Incomplete)break;i.kind!=T.ESC&&i.kind!=T.Unknown&&(i.kind==T.Text?t.push(this.transform_to_html(this.with_state(i))):i.kind==T.SGR?this.process_ansi(i):i.kind==T.OSCURL&&t.push(this.process_hyperlink(i)))}return t.join("")},e.prototype.with_state=function(e){return{bold:this.bold,fg:this.fg,bg:this.bg,text:e.text}},e.prototype.process_ansi=function(e){for(var t=e.text.split(";");t.length>0;){var i=t.shift(),s=parseInt(i,10);if(isNaN(s)||0===s)this.fg=this.bg=null,this.bold=!1;else if(1===s)this.bold=!0;else if(22===s)this.bold=!1;else if(39===s)this.fg=null;else if(49===s)this.bg=null;else if(s>=30&&s<38)this.fg=this.ansi_colors[0][s-30];else if(s>=40&&s<48)this.bg=this.ansi_colors[0][s-40];else if(s>=90&&s<98)this.fg=this.ansi_colors[1][s-90];else if(s>=100&&s<108)this.bg=this.ansi_colors[1][s-100];else if((38===s||48===s)&&t.length>0){var o=38===s,n=t.shift();if("5"===n&&t.length>0){var a=parseInt(t.shift(),10);a>=0&&a<=255&&(o?this.fg=this.palette_256[a]:this.bg=this.palette_256[a])}if("2"===n&&t.length>2){var l=parseInt(t.shift(),10),r=parseInt(t.shift(),10),c=parseInt(t.shift(),10);if(l>=0&&l<=255&&r>=0&&r<=255&&c>=0&&c<=255){var d={rgb:[l,r,c],class_name:"truecolor"};o?this.fg=d:this.bg=d}}}}},e.prototype.transform_to_html=function(e){var t=e.text;if(0===t.length)return t;if(this._escape_for_html&&(t=this.escape_txt_for_html(t)),!e.bold&&null===e.fg&&null===e.bg)return t;var i=[],s=[],o=e.fg,n=e.bg;e.bold&&i.push("font-weight:bold"),this._use_classes?(o&&("truecolor"!==o.class_name?s.push(o.class_name+"-fg"):i.push("color:rgb("+o.rgb.join(",")+")")),n&&("truecolor"!==n.class_name?s.push(n.class_name+"-bg"):i.push("background-color:rgb("+n.rgb.join(",")+")"))):(o&&i.push("color:rgb("+o.rgb.join(",")+")"),n&&i.push("background-color:rgb("+n.rgb+")"));var a="",l="";return s.length&&(a=' class="'+s.join(" ")+'"'),i.length&&(l=' style="'+i.join(";")+'"'),"<span"+l+a+">"+t+"</span>"},e.prototype.process_hyperlink=function(e){var t=e.url.split(":");return t.length<1?"":this._url_whitelist[t[0]]?'<a href="'+this.escape_txt_for_html(e.url)+'">'+this.escape_txt_for_html(e.text)+"</a>":""},e}();function I(e){var t=e.raw[0].replace(/^\s+|\s+\n|\s*#[\s\S]*?\n|\n/gm,"");return new RegExp(t)}t("vaadin-grid-tree-toggle",i`
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
const D=document.createElement("template");D.innerHTML="\n  <style>\n    @font-face {\n      font-family: \"vaadin-grid-tree-icons\";\n      src: url(data:application/font-woff;charset=utf-8;base64,d09GRgABAAAAAAQkAA0AAAAABrwAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAABGRlRNAAAECAAAABoAAAAcgHwa6EdERUYAAAPsAAAAHAAAAB4AJwAOT1MvMgAAAZQAAAA/AAAAYA8TBIJjbWFwAAAB8AAAAFUAAAFeGJvXWmdhc3AAAAPkAAAACAAAAAgAAAAQZ2x5ZgAAAlwAAABLAAAAhIrPOhFoZWFkAAABMAAAACsAAAA2DsJI02hoZWEAAAFcAAAAHQAAACQHAgPHaG10eAAAAdQAAAAZAAAAHAxVAgBsb2NhAAACSAAAABIAAAASAIAAVG1heHAAAAF8AAAAGAAAACAACgAFbmFtZQAAAqgAAAECAAACTwflzbdwb3N0AAADrAAAADYAAABZQ7Ajh3icY2BkYGAA4twv3Vfi+W2+MnCzMIDANSOmbGSa2YEZRHEwMIEoAAoiB6sAeJxjYGRgYD7w/wADAwsDCDA7MDAyoAI2AFEEAtIAAAB4nGNgZGBg4GBgZgDRDAxMDGgAAAGbABB4nGNgZp7JOIGBlYGBaSbTGQYGhn4IzfiawZiRkwEVMAqgCTA4MDA+38d84P8BBgdmIAapQZJVYGAEAGc/C54AeJxjYYAAxlAIzQTELAwMBxgZGB0ACy0BYwAAAHicY2BgYGaAYBkGRgYQiADyGMF8FgYbIM3FwMHABISMDArP9/3/+/8/WJXC8z0Q9v8nEp5gHVwMMMAIMo+RDYiZoQJMQIKJARUA7WBhGN4AACFKDtoAAAAAAAAAAAgACAAQABgAJgA0AEIAAHichYvBEYBADAKBVHBjBT4swl9KS2k05o0XHd/yW1hAfBFwCv9sIlJu3nZaNS3PXAaXXHI8Lge7DlzF7C1RgXc7xkK6+gvcD2URmQB4nK2RQWoCMRiFX3RUqtCli65yADModOMBLLgQSqHddRFnQghIAnEUvEA3vUUP0LP0Fj1G+yb8R5iEhO9/ef/7FwFwj28o9EthiVp4hBlehcfUP4Ur8o/wBAv8CU+xVFvhOR7UB7tUdUdlVRJ6HnHWTnhM/V24In8JT5j/KzzFSi2E53hUz7jCcrcIiDDwyKSW1JEct2HdIPH1DFytbUM0PofWdNk5E5oUqb/Q6HHBiVGZpfOXkyUMEj5IyBuNmYZQjBobfsuassvnkKLe1OuBBj0VQ8cRni2xjLWsHaM0jrjx3peYA0/vrdmUYqe9iy7bzrX6eNP7Jh1SijX+AaUVbB8AAHicY2BiwA84GBgYmRiYGJkZmBlZGFkZ2djScyoLMgzZS/MyDQwMwLSruZMzlHaB0q4A76kLlwAAAAEAAf//AA94nGNgZGBg4AFiMSBmYmAEQnYgZgHzGAAD6wA2eJxjYGBgZACCKxJigiD6mhFTNowGACmcA/8AAA==) format('woff');\n      font-weight: normal;\n      font-style: normal;\n    }\n  </style>\n",document.head.appendChild(D.content),t("vaadin-grid-tree-toggle",i`
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
  `,{moduleId:"vaadin-grid-tree-toggle-styles"});const E=e=>class extends e{static get properties(){return{level:{type:Number,value:0,observer:"_levelChanged",sync:!0},leaf:{type:Boolean,value:!1,reflectToAttribute:!0},expanded:{type:Boolean,value:!1,reflectToAttribute:!0,notify:!0,sync:!0}}}constructor(){super(),this.addEventListener("click",(e=>this._onClick(e)))}_onClick(e){this.leaf||S(e.target)||e.target instanceof HTMLLabelElement||(e.preventDefault(),this.expanded=!this.expanded)}_levelChanged(e){const t=Number(e).toString();this.style.setProperty("---level",t)}}
/**
 * @license
 * Copyright (c) 2016 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;class R extends(E(n(a(l)))){static get is(){return"vaadin-grid-tree-toggle"}static get template(){return o`
      <span id="level-spacer"></span>
      <span part="toggle"></span>
      <slot></slot>
    `}}var N;s(R);let j=N=class extends u{constructor(){super(),this.active=!1,this.condition="running",this.jobs=Object(),this.filterAccessKey="",this.sessionNameField="name",this.appSupportList=[],this.appTemplate=Object(),this.imageInfo=Object(),this._boundControlRenderer=this.controlRenderer.bind(this),this._boundConfigRenderer=this.configRenderer.bind(this),this._boundUsageRenderer=this.usageRenderer.bind(this),this._boundReservationRenderer=this.reservationRenderer.bind(this),this._boundIdleChecksHeaderderer=this.idleChecksHeaderRenderer.bind(this),this._boundIdleChecksRenderer=this.idleChecksRenderer.bind(this),this._boundAgentListRenderer=this.agentListRenderer.bind(this),this._boundSessionInfoRenderer=this.sessionInfoRenderer.bind(this),this._boundArchitectureRenderer=this.architectureRenderer.bind(this),this._boundCheckboxRenderer=this.checkboxRenderer.bind(this),this._boundUserInfoRenderer=this.userInfoRenderer.bind(this),this._boundStatusRenderer=this.statusRenderer.bind(this),this._boundSessionTypeRenderer=this.sessionTypeRenderer.bind(this),this.refreshing=!1,this.is_admin=!1,this.is_superadmin=!1,this._connectionMode="API",this.notification=Object(),this.enableScalingGroup=!1,this.isDisplayingAllocatedShmemEnabled=!1,this.listCondition="loading",this.refreshTimer=Object(),this.kernel_labels=Object(),this.kernel_icons=Object(),this.indicator=Object(),this._helpDescription="",this._helpDescriptionTitle="",this._helpDescriptionIcon="",this.statusColorTable=new Proxy({"idle-timeout":"green","user-requested":"green",scheduled:"green","failed-to-start":"red","creation-failed":"red","self-terminated":"green"},{get:(e,t)=>e.hasOwnProperty(t)?e[t]:"lightgrey"}),this.idleChecksTable=new Proxy({network_timeout:"NetworkIdleTimeout",session_lifetime:"MaxSessionLifetime",utilization:"UtilizationIdleTimeout",expire_after:"ExpiresAfter",grace_period:"GracePeriod",cpu_util:"CPU",mem:"MEM",cuda_util:"GPU",cuda_mem:"GPU(MEM)",ipu_util:"IPU",ipu_mem:"IPU(MEM)"},{get:(e,t)=>e.hasOwnProperty(t)?e[t]:t}),this.sessionTypeColorTable=new Proxy({INTERACTIVE:"green",BATCH:"darkgreen",INFERENCE:"blue"},{get:(e,t)=>e.hasOwnProperty(t)?e[t]:"lightgrey"}),this.sshPort=0,this.vncPort=0,this.current_page=1,this.session_page_limit=50,this.total_session_count=0,this._APIMajorVersion=5,this.selectedSessionStatus=Object(),this.isUserInfoMaskEnabled=!1,this.pushImageInsteadOfCommiting=!1,this.canStartImagifying=!1,this.newImageName="",this._isContainerCommitEnabled=!1,this._isPerKernelLogSupported=!1,this.getUtilizationCheckerColor=(e,t=null)=>{const i="var(--token-colorSuccess)",s="var(--token-colorWarning)",o="var(--token-colorError)";if(t){let n=i;return"and"===t?Object.values(e).every((([e,t])=>e<Math.min(2*t,t+5)))?n=o:Object.values(e).every((([e,t])=>e<Math.min(10*t,t+10)))&&(n=s):"or"===t&&(Object.values(e).some((([e,t])=>e<Math.min(2*t,t+5)))?n=o:Object.values(e).some((([e,t])=>e<Math.min(10*t,t+10)))&&(n=s)),n}{const[t,n]=e;return t<2*n?o:t<10*n?s:i}},this.compute_sessions=[],this.selectedKernels=[],this._selected_items=[],this._manualCleanUpNeededContainers=[],this.terminationQueue=[],this.activeIdleCheckList=new Set}static get styles(){return[h,m,g,i`
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

        mwc-checkbox.list-check {
          margin: 6px 0 0 0;
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

        #force-terminate-confirmation-dialog {
          --component-width: 450px;
        }

        ul.force-terminate-confirmation {
          padding-left: 1rem;
        }

        div.force-terminate-confirmation-container-list {
          background-color: rgba(0, 0, 0, 0.2);
          border-radius: 5px;
          padding: 10px;
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
          color: var(--token-colorTextSecondary, #666);
          font-weight: bold;
          font-size: 15px;
        }

        mwc-list-item.commit-session-info {
          height: 100%;
        }

        mwc-list-item.predicate-check {
          height: 100%;
          margin-bottom: 5px;
        }

        .predicate-check-comment {
          white-space: normal;
          font-size: 14px;
        }

        .error-description {
          font-size: 0.8rem;
          word-break: break-word;
        }

        h4.commit-session-title {
          margin-bottom: 0;
        }

        span.commit-session-subheading {
          font-size: smaller;
          font-family: monospace;
        }

        mwc-button.multiple-action-button {
          --mdc-theme-primary: var(--paper-red-600);
          --mdc-theme-on-primary: white;
        }

        div.pagination-label {
          background-color: var(--token-colorBgContainer, --paper-grey-100);
          min-width: 60px;
          font-size: 12px;
          font-family: var(--token-fontFamily);
          padding-top: 5px;
          width: auto;
          text-align: center;
        }

        lablup-progress-bar.usage {
          --progress-bar-height: 5px;
          --progress-bar-width: 120px;
          margin: 2px 0 5px 0;
        }

        div.filters #access-key-filter {
          --input-font-size: small;
          --input-label-font-size: small;
          --input-font-family: var(--token-fontFamily);
        }

        .mount-button,
        .status-button,
        .idle-check-key {
          border: none;
          background: none;
          padding: 0;
          outline-style: none;
          font-family: var(--token-fontFamily);
          color: var(--token-colorText);
        }

        .no-mount {
          color: var(--token-colorTextDisabled, --paper-grey-400);
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
          font-size: 10px;
        }

        div.error-detail-panel {
          border-radius: var(--token-borderRadiusSM, 4px);
          background-color: var(--token-colorBgContainerDisabled);
          padding: var(--token-paddingSM, 10px);
          margin: var(--token-marginSM, 10px);
        }
      `]}get _isRunning(){return["batch","interactive","inference","system","running","others"].includes(this.condition)}get _isIntegratedCondition(){return["running","finished","others"].includes(this.condition)}_isPreparing(e){return-1!==["RESTARTING","PREPARING","PULLING"].indexOf(e)}_isError(e){return"ERROR"===e}_isPending(e){return"PENDING"===e}_isFinished(e){return["TERMINATED","CANCELLED","TERMINATING"].includes(e)}firstUpdated(){this.imageInfo=globalThis.backendaimetadata.imageInfo,this.kernel_icons=globalThis.backendaimetadata.icons,this.kernel_labels=globalThis.backendaimetadata.kernel_labels,document.addEventListener("backend-ai-metadata-image-loaded",(()=>{this.imageInfo=globalThis.backendaimetadata.imageInfo,this.kernel_icons=globalThis.backendaimetadata.icons,this.kernel_labels=globalThis.backendaimetadata.kernel_labels}),{once:!0}),this.refreshTimer=null,this.notification=globalThis.lablupNotification,this.indicator=globalThis.lablupIndicator,document.addEventListener("backend-ai-group-changed",(e=>this.refreshList(!0,!1))),document.addEventListener("backend-ai-ui-changed",(e=>this._refreshWorkDialogUI(e))),document.addEventListener("backend-ai-clear-timeout",(()=>{clearTimeout(this.refreshTimer)})),this._refreshWorkDialogUI({detail:{"mini-ui":globalThis.mini_ui}})}async _viewStateChanged(e){var t;await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{var e;globalThis.backendaiclient.is_admin?this.accessKeyFilterInput.style.display="block":(this.accessKeyFilterInput.style.display="none",this.accessKeyFilterHelperText.style.display="none",(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("vaadin-grid")).style.height="calc(100vh - 225px)!important"),globalThis.backendaiclient.APIMajorVersion<5&&(this.sessionNameField="sess_id"),this.is_admin=globalThis.backendaiclient.is_admin,this.is_superadmin=globalThis.backendaiclient.is_superadmin,this._connectionMode=globalThis.backendaiclient._config._connectionMode,this.enableScalingGroup=globalThis.backendaiclient.supports("scaling-group"),this.isDisplayingAllocatedShmemEnabled=globalThis.backendaiclient.supports("display-allocated-shmem"),this._APIMajorVersion=globalThis.backendaiclient.APIMajorVersion,this.isUserInfoMaskEnabled=globalThis.backendaiclient._config.maskUserInfo,this._isContainerCommitEnabled=globalThis.backendaiclient._config.enableContainerCommit&&globalThis.backendaiclient.supports("image-commit"),this._isPerKernelLogSupported=globalThis.backendaiclient.supports("per-kernel-logs"),this._refreshJobData()}),!0):(globalThis.backendaiclient.is_admin?(this.accessKeyFilterInput.style.display="block",this.accessKeyFilterHelperText.style.display="block"):(this.accessKeyFilterInput.style.display="none",this.accessKeyFilterHelperText.style.display="none",(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("vaadin-grid")).style.height="calc(100vh - 225px)!important"),globalThis.backendaiclient.APIMajorVersion<5&&(this.sessionNameField="sess_id"),this.is_admin=globalThis.backendaiclient.is_admin,this.is_superadmin=globalThis.backendaiclient.is_superadmin,this._connectionMode=globalThis.backendaiclient._config._connectionMode,this.enableScalingGroup=globalThis.backendaiclient.supports("scaling-group"),this.isDisplayingAllocatedShmemEnabled=globalThis.backendaiclient.supports("display-allocated-shmem"),this._APIMajorVersion=globalThis.backendaiclient.APIMajorVersion,this.isUserInfoMaskEnabled=globalThis.backendaiclient._config.maskUserInfo,this._isContainerCommitEnabled=globalThis.backendaiclient._config.enableContainerCommit&&globalThis.backendaiclient.supports("image-commit"),this._isPerKernelLogSupported=globalThis.backendaiclient.supports("per-kernel-logs"),this._refreshJobData()))}async refreshList(e=!0,t=!0){return this._refreshJobData(e,t)}async _refreshJobData(e=!1,t=!0){if(await this.updateComplete,!0!==this.active)return;if(!0===this.refreshing)return;let i;switch(this.refreshing=!0,i="RUNNING",this.condition){case"running":case"interactive":case"system":case"batch":case"inference":case"others":i=["RUNNING","RESTARTING","TERMINATING","PENDING","SCHEDULED","PREPARING","PULLING","ERROR"];break;case"finished":i=["TERMINATED","CANCELLED"];break;default:i=["RUNNING","RESTARTING","TERMINATING","PENDING","SCHEDULED","PREPARING","PULLING"]}!globalThis.backendaiclient.supports("avoid-hol-blocking")&&i.includes("SCHEDULED")&&(i=i.filter((e=>"SCHEDULED"!==e))),globalThis.backendaiclient.supports("detailed-session-states")&&(i=i.join(","));const s=["id","session_id","name","image","architecture","created_at","terminated_at","status","status_info","service_ports","mounts","resource_opts","occupied_slots","access_key","starts_at","type","agents"];globalThis.backendaiclient.supports("multi-container")&&s.push("cluster_size"),globalThis.backendaiclient.supports("multi-node")&&s.push("cluster_mode"),globalThis.backendaiclient.supports("session-detail-status")&&s.push("status_data"),globalThis.backendaiclient.supports("idle-checks")&&s.push("idle_checks"),globalThis.backendaiclient.supports("inference-workload")&&s.push("inference_metrics"),globalThis.backendaiclient.supports("sftp-scaling-group")&&s.push("main_kernel_role"),this.enableScalingGroup&&s.push("scaling_group"),"SESSION"===this._connectionMode&&s.push("user_email"),globalThis.backendaiclient._config.hideAgents||s.push("containers {agent}");const o=globalThis.backendaiclient.current_group_id(),n=["container_id","occupied_slots","live_stat","last_stat"];globalThis.backendaiclient.is_superadmin&&n.push("agent"),globalThis.backendaiclient.supports("per-user-image")&&n.push("kernel_id role local_rank image_object { labels { key value } }"),this._isContainerCommitEnabled&&i.includes("RUNNING")&&s.push("commit_status"),s.push(`containers { ${n.join(" ")} }`),globalThis.backendaiclient.computeSession.list(s,i,this.filterAccessKey,this.session_page_limit,(this.current_page-1)*this.session_page_limit,o,1e4).then((i=>{var s,o,n,a,l;this.total_session_count=(null===(s=null==i?void 0:i.compute_session_list)||void 0===s?void 0:s.total_count)||0;let r,c=null===(o=null==i?void 0:i.compute_session_list)||void 0===o?void 0:o.items;if(0===this.total_session_count?(this.listCondition="no-data",null===(n=this._listStatus)||void 0===n||n.show(),this.total_session_count=1):["interactive","batch","inference"].includes(this.condition)&&0===c.filter((e=>e.type.toLowerCase()===this.condition)).length||"system"===this.condition&&0===c.filter((e=>e.main_kernel_role.toLowerCase()===this.condition)).length?(this.listCondition="no-data",null===(a=this._listStatus)||void 0===a||a.show()):null===(l=this._listStatus)||void 0===l||l.hide(),void 0!==c&&0!=c.length){const e=this.compute_sessions,t=[];Object.keys(e).map(((i,s)=>{t.push(e[i].session_id)})),Object.keys(c).map(((e,t)=>{var i,s,o,n;const a=c[e],l=JSON.parse(a.occupied_slots),r=c[e].image.split("/")[2]||c[e].image.split("/")[1];if(c[e].cpu_slot=parseInt(l.cpu),c[e].mem_slot=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(l.mem,"g")),c[e].mem_slot=c[e].mem_slot.toFixed(2),c[e].elapsed=this._elapsed(c[e].created_at,c[e].terminated_at),c[e].created_at_hr=this._humanReadableTime(c[e].created_at),c[e].starts_at_hr=c[e].starts_at?this._humanReadableTime(c[e].starts_at):"",globalThis.backendaiclient.supports("idle-checks")){const t=JSON.parse(a.idle_checks||"{}");t&&(c[e].idle_checks=t),t&&t.network_timeout&&t.network_timeout.remaining&&(c[e].idle_checks.network_timeout.remaining=N.secondsToDHMS(t.network_timeout.remaining),null===(i=this.activeIdleCheckList)||void 0===i||i.add("network_timeout")),t&&t.session_lifetime&&t.session_lifetime.remaining&&(c[e].idle_checks.session_lifetime.remaining=N.secondsToDHMS(t.session_lifetime.remaining),null===(s=this.activeIdleCheckList)||void 0===s||s.add("session_lifetime")),t&&t.utilization&&t.utilization.remaining&&(c[e].idle_checks.utilization.remaining=N.secondsToDHMS(t.utilization.remaining),null===(o=this.activeIdleCheckList)||void 0===o||o.add("utilization"))}if(c[e].containers&&c[e].containers.length>0){const t={cpu_util:{capacity:0,current:0,ratio:0,slots:"0"},mem:{capacity:0,current:0,ratio:0},io_read:{current:0},io_write:{current:0}};c[e].containers.forEach((i=>{var s,o,n,a,r;const d=JSON.parse(i.live_stat);t.cpu_util.current+=parseFloat(null===(s=null==d?void 0:d.cpu_util)||void 0===s?void 0:s.current),t.cpu_util.capacity+=parseFloat(null===(o=null==d?void 0:d.cpu_util)||void 0===o?void 0:o.capacity),t.mem.current+=parseInt(null===(n=null==d?void 0:d.mem)||void 0===n?void 0:n.current),t.mem.capacity=l.mem,t.io_read.current+=parseFloat(N.bytesToMB(null===(a=null==d?void 0:d.io_read)||void 0===a?void 0:a.current)),t.io_write.current+=parseFloat(N.bytesToMB(null===(r=null==d?void 0:d.io_write)||void 0===r?void 0:r.current)),d&&(Object.keys(d).forEach((e=>{"cpu_util"!==e&&"cpu_used"!==e&&"mem"!==e&&"io_read"!==e&&"io_write"!==e&&"io_scratch_size"!==e&&"net_rx"!==e&&"net_tx"!==e&&(e.includes("_util")||e.includes("_mem"))&&(t[e]||(t[e]={capacity:0,current:0,ratio:0}),t[e].current+=parseFloat(d[e].current),t[e].capacity+=parseFloat(d[e].capacity))})),t.cpu_util.ratio=t.cpu_util.current/t.cpu_util.capacity*c[e].containers.length||0,t.cpu_util.slots=l.cpu,t.mem.ratio=t.mem.current/t.mem.capacity||0,Object.keys(t).forEach((e=>{"cpu_util"!==e&&"mem"!==e&&(-1!==e.indexOf("_util")&&t[e].capacity>0&&(t[e].ratio=t[e].current/100||0),-1!==e.indexOf("_mem")&&t[e].capacity>0&&(t[e].ratio=t[e].current/t[e].capacity||0))})),c[e].live_stat=t)}));const i=c[e].containers[0],s=i.live_stat?JSON.parse(i.live_stat):null;c[e].agent=i.agent,s&&s.cpu_used?c[e].cpu_used_time=this._automaticScaledTime(s.cpu_used.current):c[e].cpu_used_time=this._automaticScaledTime(0),this.is_superadmin&&(c[e].agents_ids_with_container_ids=null===(n=c[e].containers)||void 0===n?void 0:n.map((e=>{var t;return`${e.agent}(${null===(t=e.container_id)||void 0===t?void 0:t.slice(0,4)})`})))}const d=JSON.parse(c[e].service_ports);c[e].service_ports=d,!0===Array.isArray(d)?(c[e].app_services=d.map((e=>e.name)),c[e].app_services_option={},d.forEach((t=>{"allowed_arguments"in t&&(c[e].app_services_option[t.name]=t.allowed_arguments)}))):(c[e].app_services=[],c[e].app_services_option={}),0!==c[e].app_services.length&&["batch","interactive","inference","system","running"].includes(this.condition)?c[e].appSupport=!0:c[e].appSupport=!1,["batch","interactive","inference","system","running"].includes(this.condition)?c[e].running=!0:c[e].running=!1,"cuda.device"in l&&(c[e].cuda_gpu_slot=parseInt(l["cuda.device"])),"rocm.device"in l&&(c[e].rocm_gpu_slot=parseInt(l["rocm.device"])),"tpu.device"in l&&(c[e].tpu_slot=parseInt(l["tpu.device"])),"ipu.device"in l&&(c[e].ipu_slot=parseInt(l["ipu.device"])),"atom.device"in l&&(c[e].atom_slot=parseInt(l["atom.device"])),"atom-plus.device"in l&&(c[e].atom_plus_slot=parseInt(l["atom-plus.device"])),"warboy.device"in l&&(c[e].warboy_slot=parseInt(l["warboy.device"])),"hyperaccel-lpu.device"in l&&(c[e].hyperaccel_lpu_slot=parseInt(l["hyperaccel-lpu.device"])),"cuda.shares"in l&&(c[e].cuda_fgpu_slot=parseFloat(l["cuda.shares"]).toFixed(2)),c[e].kernel_image=r,c[e].icon=this._getKernelIcon(a.image),c[e].sessionTags=this._getKernelInfo(a.image);const p=a.image.split("/");c[e].cluster_size=parseInt(c[e].cluster_size);const u=p[p.length-1].split(":")[1],h=u.split("-");if(void 0!==h[1]){if(c[e].baseversion=h[0],c[e].baseimage=h[1],c[e].additional_reqs=h.slice(1,h.length).filter((e=>e.indexOf("customized_")<0)).map((e=>e.toUpperCase())),c[e].containers[0].image_object){const t=c[e].containers[0].image_object.labels.find((({key:e})=>"ai.backend.customized-image.name"===e));t&&(c[e].additional_reqs=[...c[e].additional_reqs,`Customized-${t.value}`])}}else void 0!==c[e].tag?c[e].baseversion=c[e].tag:c[e].baseversion=u;this._selected_items.includes(c[e].session_id)?c[e].checked=!0:c[e].checked=!1}))}if(["batch","interactive","inference"].includes(this.condition)){const e=c.reduce(((e,t)=>("SYSTEM"!==t.main_kernel_role&&e[t.type.toLowerCase()].push(t),e)),{batch:[],interactive:[],inference:[]});c=e[this.condition]}else c="system"===this.condition?c.filter((e=>"SYSTEM"===e.main_kernel_role)):c.filter((e=>"SYSTEM"!==e.main_kernel_role));if(this.compute_sessions=c,this._grid.recalculateColumnWidths(),this.requestUpdate(),this.refreshing=!1,!0===this.active){if(!0===e){const e=new CustomEvent("backend-ai-resource-refreshed",{detail:{}});document.dispatchEvent(e)}!0===t&&(r=["batch","interactive","inference","system","running"].includes(this.condition)?7e3:3e4,this.refreshTimer=setTimeout((()=>{this._refreshJobData()}),r))}})).catch((e=>{var i;if(this.refreshing=!1,this.active&&t){const e=["batch","interactive","inference","system","running"].includes(this.condition)?2e4:12e4;this.refreshTimer=setTimeout((()=>{this._refreshJobData()}),e)}null===(i=this._listStatus)||void 0===i||i.hide(),e&&e.message&&(this.notification.text=v.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_refreshWorkDialogUI(e){Object.prototype.hasOwnProperty.call(e.detail,"mini-ui")&&!0===e.detail["mini-ui"]?this.workDialog.classList.add("mini_ui"):this.workDialog.classList.remove("mini_ui")}_humanReadableTime(e){return(e=new Date(e)).toLocaleString()}_getKernelInfo(e){const t=[];if(void 0===e)return[];const i=e.split("/"),s=(i[2]||i[1]).split(":")[0];if(s in this.kernel_labels)t.push(this.kernel_labels[s]);else{const i=e.split("/");let s,o;3===i.length?(s=i[1],o=i[2]):i.length>3?(s=null==i?void 0:i.slice(2,i.length-1).join("/"),o=i[i.length-1]):(s="",o=i[1]),o=o.split(":")[0],o=s?s+"/"+o:o,t.push([{category:"Env",tag:`${o}`,color:"lightgrey"}])}return t}_getKernelIcon(e){if(void 0===e)return[];const t=e.split("/"),i=(t[2]||t[1]).split(":")[0];return i in this.kernel_icons?this.kernel_icons[i]:""}_automaticScaledTime(e){let t=Object();const i=["D","H","M","S"],s=[864e5,36e5,6e4,1e3];for(let o=0;o<s.length;o++)Math.floor(e/s[o])>0&&(t[i[o]]=Math.floor(e/s[o]),e%=s[o]);return 0===Object.keys(t).length&&(t=e>0?{MS:e}:{NODATA:1}),t}static bytesToMB(e,t=1){return Number(e/10**6).toFixed(1)}static bytesToGiB(e,t=2){return e?(e/2**30).toFixed(t):e}_elapsed(e,t){return globalThis.backendaiclient.utils.elapsedTime(e,t)}_indexRenderer(e,t,i){const s=i.index+1;b(_`
        <div>${s}</div>
      `,e)}async sendRequest(e){let t,i;try{"GET"==e.method&&(e.body=void 0),t=await fetch(e.uri,e);const s=t.headers.get("Content-Type");if(i=s.startsWith("application/json")||s.startsWith("application/problem+json")?await t.json():s.startsWith("text/")?await t.text():await t.blob(),!t.ok)throw i}catch(e){}return i}async _terminateApp(e){const t=globalThis.backendaiclient._config.accessKey,i=await globalThis.appLauncher._getProxyURL(e),s={method:"GET",uri:new URL(`proxy/${t}/${e}`,i).href};return this.sendRequest(s).then((s=>{this.total_session_count-=1;let o=new URL(`proxy/${t}/${e}/delete`,i);if(localStorage.getItem("backendaiwebui.appproxy-permit-key")&&(o.searchParams.set("permit_key",localStorage.getItem("backendaiwebui.appproxy-permit-key")||""),o=new URL(o.href)),void 0!==s&&404!==s.code){const e={method:"GET",uri:o.href,credentials:"include",mode:"cors"};return this.sendRequest(e)}return Promise.resolve(!0)})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=v.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_getProxyToken(){let e="local";return void 0!==globalThis.backendaiclient._config.proxyToken&&(e=globalThis.backendaiclient._config.proxyToken),e}_setSelectedSession(e){const t=e.target.closest("#controls"),i=t["session-uuid"],s=t["session-name"],o=t["access-key"];this.workDialog.sessionUuid=i,this.workDialog.sessionName=s,this.workDialog.accessKey=o}_setSelectedKernel(){var e;const t=null===(e=this.compute_sessions.find((e=>e.session_id===this.workDialog.sessionUuid)))||void 0===e?void 0:e.containers.map(((e,t)=>((null==e?void 0:e.role)?(null==e?void 0:e.role.includes("main"))?e.role="main1":e.role=`sub${e.local_rank}`:0===t&&(e.role="main1"),e))).sort(((e,t)=>e.role.localeCompare(t.role)));this.selectedKernels=this._isPerKernelLogSupported?t:t.filter((e=>e.role.includes("main")))}_updateLogsByKernelId(){var e,t;this.selectedKernelId=this._isPerKernelLogSupported?null===(t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#kernel-id-select"))||void 0===t?void 0:t.value:null}_showLogs(){globalThis.backendaiclient.get_logs(this.workDialog.sessionUuid,this.workDialog.accessKey,""!==this.selectedKernelId?this.selectedKernelId:null,15e3).then((e=>{var t,i;const s=(new C).ansi_to_html(e.result.logs);(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#work-title")).innerHTML=`${this.workDialog.sessionName} (${this.workDialog.sessionUuid})`,(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#work-area")).innerHTML=`<pre>${s}</pre>`||f("session.NoLogs"),this.workDialog.show()})).catch((e=>{e&&e.message?(this.notification.text=v.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=v.relieve(e.title),this.notification.show(!0,e))}))}_downloadLogs(){const e=this.workDialog.sessionUuid,t=this.workDialog.sessionName,i=globalThis.backendaiclient.APIMajorVersion<5?t:e,s=this.workDialog.accessKey;globalThis.backendaiclient.get_logs(i,s,""!==this.selectedKernelId?this.selectedKernelId:null,15e3).then((e=>{const i=e.result.logs;globalThis.backendaiutils.exportToTxt(t,i),this.notification.text=f("session.DownloadingSessionLogs"),this.notification.show()})).catch((e=>{e&&e.message?(this.notification.text=v.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=v.relieve(e.title),this.notification.show(!0,e))}))}_refreshLogs(){const e=this.workDialog.sessionUuid,t=this.workDialog.sessionName,i=globalThis.backendaiclient.APIMajorVersion<5?t:e,s=this.workDialog.accessKey;globalThis.backendaiclient.get_logs(i,s,""!==this.selectedKernelId?this.selectedKernelId:null,15e3).then((e=>{var t;const i=(new C).ansi_to_html(e.result.logs);(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#work-area")).innerHTML=`<pre>${i}</pre>`||f("session.NoLogs")})).catch((e=>{e&&e.message?(this.notification.text=v.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=v.relieve(e.title),this.notification.show(!0,e))}))}_showAppLauncher(e){const t=e.target.closest("#controls");return globalThis.appLauncher.showLauncher(t)}async _runTerminal(e){const t=e.target.closest("#controls")["session-uuid"];return globalThis.appLauncher.runTerminal(t)}async _getCommitSessionStatus(e=""){let t=!1;return""!==e&&globalThis.backendaiclient.computeSession.getCommitSessionStatus(e).then((e=>{t=e})).catch((e=>{console.log(e)})),t}async _requestCommitSession(e){try{const t=await globalThis.backendaiclient.computeSession.commitSession(e.session.name),i=Object.assign(e,{taskId:t.bgtask_id});this._showCommitStatus(t,i)}catch(e){console.log(e),e&&e.message&&(this.notification.text=v.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}finally{this.commitSessionDialog.hide()}}async _showCommitStatus(e,t){try{this._applyContainerCommitAsBackgroundTask(t)}catch(e){console.log(e),e&&e.message&&(this.notification.text=v.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}finally{this.commitSessionDialog.hide()}}async _requestConvertSessionToimage(e){try{const t=await globalThis.backendaiclient.computeSession.convertSessionToImage(e.session.name,this.newImageName),i=Object.assign(e,{taskId:t.task_id});this._showCommitStatus(t,i)}catch(e){console.log(e),e&&e.message&&(this.notification.text=v.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}finally{this.commitSessionDialog.hide()}}_applyContainerCommitAsBackgroundTask(e){const t="commit-session:"+(new Date).getTime(),i=new CustomEvent("add-bai-notification",{detail:{key:t,message:f("session.CommitSession"),description:f("session.CommitOnGoing"),backgroundTask:{percent:0,status:"pending"},duration:0,open:!0}});document.dispatchEvent(i);const s=new CustomEvent("add-bai-notification",{detail:{key:t,description:f("session.CommitSession"),backgroundTask:{taskId:e.taskId,statusDescriptions:{pending:f("session.CommitOnGoing"),rejected:f("session.CommitFailed"),resolved:f("session.CommitFinished")},renderDataMessage:e=>(null==e?void 0:e.includes("QuotaExceeded"))?f("error.ReachedResourceLimitPleaseContact"):e,status:"pending",percent:0},duration:0}});document.dispatchEvent(s)}_removeCommitSessionFromTasker(e=""){globalThis.tasker.remove(e)}_getCurrentContainerCommitInfoListFromLocalStorage(){return JSON.parse(localStorage.getItem("backendaiwebui.settings.user.container_commit_sessions")||"[]")}_saveCurrentContainerCommitInfoToLocalStorage(e){const t=this._getCurrentContainerCommitInfoListFromLocalStorage();t.push(e),globalThis.backendaioptions.set("container_commit_sessions",JSON.stringify(t))}_removeFinishedContainerCommitInfoFromLocalStorage(e="",t=""){let i=this._getCurrentContainerCommitInfoListFromLocalStorage();i=i.filter((i=>i.session.id!==e&&i.taskId!==t)),globalThis.backendaioptions.set("container_commit_sessions",JSON.stringify(i))}_openCommitSessionDialog(e){var t;const i=e.target.closest("#controls"),s=i["session-name"],o=i["session-uuid"],n=i["kernel-image"];this.commitSessionDialog.sessionName=s,this.commitSessionDialog.sessionId=o,this.commitSessionDialog.kernelImage=n,(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#new-image-name-field")).value="",this.requestUpdate(),this.commitSessionDialog.show()}_openTerminateSessionDialog(e){const t=e.target.closest("#controls"),i=t["session-name"],s=t["session-uuid"],o=t["access-key"];this.terminateSessionDialog.sessionName=i,this.terminateSessionDialog.sessionId=s,this.terminateSessionDialog.accessKey=o,this.terminateSessionDialog.show()}_terminateSession(e){const t=e.target.closest("#controls"),i=t["session-uuid"],s=t["access-key"];return this.terminationQueue.includes(i)?(this.notification.text=f("session.AlreadyTerminatingSession"),this.notification.show(),!1):this._terminateKernel(i,s)}_terminateSessionWithCheck(e=!1){var t;return this.terminationQueue.includes(this.terminateSessionDialog.sessionId)?(this.notification.text=f("session.AlreadyTerminatingSession"),this.notification.show(),!1):(this.listCondition="loading",null===(t=this._listStatus)||void 0===t||t.show(),this._terminateKernel(this.terminateSessionDialog.sessionId,this.terminateSessionDialog.accessKey,e).then((()=>{this._selected_items=[],this._clearCheckboxes(),this.terminateSessionDialog.hide(),this.notification.text=f("session.SessionTerminated"),this.notification.show();const e=new CustomEvent("backend-ai-resource-refreshed",{detail:"running"});document.dispatchEvent(e)})).catch((()=>{this._selected_items=[],this._clearCheckboxes(),this.terminateSessionDialog.hide()})))}static _parseAgentBasedContainers(e){return Object.values(e.reduce(((e,t)=>{var i;return null===(i=t.containers)||void 0===i||i.forEach((t=>{t.agent&&t.container_id&&(e[t.agent]?e[t.agent].containers.includes(t.container_id)||e[t.agent].containers.push(t.container_id):e[t.agent]={agent:t.agent,containers:[t.container_id]})})),e}),{}))}_getManualCleanUpNeededContainers(){this._manualCleanUpNeededContainers=N._parseAgentBasedContainers(this._selected_items.length>0?this._selected_items:this.compute_sessions.filter((e=>(null==e?void 0:e.session_id)===this.terminateSessionDialog.sessionId)))}_openForceTerminateConfirmationDialog(e){this.forceTerminateConfirmationDialog.show()}_openTerminateSelectedSessionsDialog(e){this.terminateSelectedSessionsDialog.show()}_clearCheckboxes(){var e;[...Array.from(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll("mwc-checkbox.list-check"))].forEach((e=>{e.removeAttribute("checked")}))}_terminateSelectedSessionsWithCheck(e=!1){var t;this.listCondition="loading",null===(t=this._listStatus)||void 0===t||t.show();const i=this._selected_items.map((t=>this._terminateKernel(t.session_id,t.access_key,e)));return this._selected_items=[],Promise.all(i).then((()=>{this.terminateSelectedSessionsDialog.hide(),this._clearCheckboxes(),this.multipleActionButtons.style.display="none",this.notification.text=f("session.SessionsTerminated"),this.notification.show()})).catch((()=>{this.terminateSelectedSessionsDialog.hide(),this._clearCheckboxes()}))}_terminateSelectedSessions(){var e;this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show();const t=this._selected_items.map((e=>this._terminateKernel(e.session_id,e.access_key)));return Promise.all(t).then((()=>{this._selected_items=[],this._clearCheckboxes(),this.multipleActionButtons.style.display="none",this.notification.text=f("session.SessionsTerminated"),this.notification.show()})).catch((()=>{var e;null===(e=this._listStatus)||void 0===e||e.hide(),this._selected_items=[],this._clearCheckboxes()}))}_requestDestroySession(e,t,i){globalThis.backendaiclient.destroy(e,t,i).then((e=>{setTimeout((async()=>{this.terminationQueue=[];const e=new CustomEvent("backend-ai-session-list-refreshed",{detail:"running"});document.dispatchEvent(e)}),1e3)})).catch((e=>{const t=new CustomEvent("backend-ai-session-list-refreshed",{detail:"running"});document.dispatchEvent(t),this.notification.text="description"in e?v.relieve(e.description):v.relieve("Problem occurred during termination."),this.notification.show(!0,e)}))}async _terminateKernel(e,t,i=!1){return this.terminationQueue.push(e),this._terminateApp(e).then((()=>this._requestDestroySession(e,t,i))).catch((s=>{throw s&&s.message&&(404==s.statusCode||500==s.statusCode?this._requestDestroySession(e,t,i):(this.notification.text=v.relieve(s.title),this.notification.detail=s.message,this.notification.show(!0,s))),s}))}_hideDialog(e){var t;const i=e.target.closest("backend-ai-dialog");if(i.hide(),"ssh-dialog"===i.id){const e=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#sshkey-download-link");globalThis.URL.revokeObjectURL(e.href)}}_updateFilterAccessKey(e){this.filterAccessKey=e.target.value,this.refreshTimer&&(clearTimeout(this.refreshTimer),this._refreshJobData())}_createMountedFolderDropdown(e,t){const i=e.target,s=document.createElement("mwc-menu");s.anchor=i,s.className="dropdown-menu",s.style.boxShadow="0 1px 1px rgba(0, 0, 0, 0.2)",s.setAttribute("open",""),s.setAttribute("fixed",""),s.setAttribute("x","10"),s.setAttribute("y","15"),t.length>=1&&(t.map(((e,i)=>{const o=document.createElement("mwc-list-item");o.style.height="25px",o.style.fontWeight="400",o.style.fontSize="14px",o.style.fontFamily="var(--token-fontFamily)",o.innerHTML=t.length>1?e:f("session.OnlyOneFolderAttached"),s.appendChild(o)})),document.body.appendChild(s))}_removeMountedFolderDropdown(){var e;const t=document.getElementsByClassName("dropdown-menu");for(;t[0];)null===(e=t[0].parentNode)||void 0===e||e.removeChild(t[0])}_renderStatusDetail(){var e,t,i,s,o,n,a,l,r,c;const d=JSON.parse(this.selectedSessionStatus.data);d.reserved_time=this.selectedSessionStatus.reserved_time;const p=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#status-detail"),u=[];if(u.push(_`
      <div class="vertical layout justified start">
        <h3
          style="width:100%;padding-left:15px;border-bottom:1px solid var(--token-colorBorder, #ccc);"
        >
          ${f("session.Status")}
        </h3>
        <lablup-shields
          color="${this.statusColorTable[this.selectedSessionStatus.info]}"
          description="${this.selectedSessionStatus.info}"
          ui="round"
          style="padding-left:15px;"
        ></lablup-shields>
      </div>
    `),d.hasOwnProperty("kernel")||d.hasOwnProperty("session"))u.push(_`
        <div class="vertical layout start flex" style="width:100%;">
          <div style="width:100%;">
            <h3
              style="width:100%;padding-left:15px;border-bottom:1px solid var(--token-colorBorder, #ccc);"
            >
              ${f("session.StatusDetail")}
            </h3>
            <div class="vertical layout flex" style="width:100%;">
              <mwc-list>
                ${(null===(t=d.kernel)||void 0===t?void 0:t.exit_code)?_`
                      <mwc-list-item
                        twoline
                        noninteractive
                        class="predicate-check"
                      >
                        <span class="subheading">
                          <strong>Kernel Exit Code</strong>
                        </span>
                        <span
                          class="monospace predicate-check-comment"
                          slot="secondary"
                        >
                          ${null===(i=d.kernel)||void 0===i?void 0:i.exit_code}
                        </span>
                      </mwc-list-item>
                    `:_``}
                ${(null===(s=d.session)||void 0===s?void 0:s.status)?_`
                      <mwc-list-item
                        twoline
                        noninteractive
                        class="predicate-check"
                      >
                        <span class="subheading">Session Status</span>
                        <span
                          class="monospace predicate-check-comment"
                          slot="secondary"
                        >
                          ${null===(o=d.session)||void 0===o?void 0:o.status}
                        </span>
                      </mwc-list-item>
                    `:_``}
              </mwc-list>
            </div>
          </div>
        </div>
      `);else if(d.hasOwnProperty("scheduler")){const e=null!==(a=null===(n=d.scheduler.failed_predicates)||void 0===n?void 0:n.length)&&void 0!==a?a:0,t=null!==(r=null===(l=d.scheduler.passed_predicates)||void 0===l?void 0:l.length)&&void 0!==r?r:0;u.push(_`
        <div class="vertical layout start flex" style="width:100%;">
          <div style="width:100%;">
            <h3
              style="width:100%;padding-left:15px;border-bottom:1px solid var(--token-colorBorder, #ccc);margin-bottom:0px;"
            >
              ${f("session.StatusDetail")}
            </h3>
            <div class="vertical layout flex" style="width:100%;">
              <mwc-list>
                ${d.scheduler.msg?_`
                      <mwc-list-item
                        twoline
                        noninteractive
                        class="predicate-check"
                      >
                        <span class="subheading">
                          ${f("session.Message")}
                        </span>
                        <span
                          class="monospace predicate-check-comment"
                          slot="secondary"
                        >
                          ${d.scheduler.msg}
                        </span>
                      </mwc-list-item>
                    `:_``}
                ${d.scheduler.retries?_`
                      <mwc-list-item
                        twoline
                        noninteractive
                        class="predicate-check"
                      >
                        <span class="subheading">
                          ${f("session.TotalRetries")}
                        </span>
                        <span
                          class="monospace predicate-check-comment"
                          slot="secondary"
                        >
                          ${d.scheduler.retries}
                        </span>
                      </mwc-list-item>
                    `:_``}
                ${d.scheduler.last_try?_`
                      <mwc-list-item
                        twoline
                        noninteractive
                        class="predicate-check"
                      >
                        <span class="subheading">
                          ${f("session.LastTry")}
                        </span>
                        <span
                          class="monospace predicate-check-comment"
                          slot="secondary"
                        >
                          ${this._humanReadableTime(d.scheduler.last_try)}
                        </span>
                      </mwc-list-item>
                    `:_``}
              </mwc-list>
            </div>
          </div>
          <lablup-expansion summary="Predicates" open="true">
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
              ${d.scheduler.failed_predicates.map((e=>_`
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
                            ${e.msg+": "+d.reserved_time}
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
              ${d.scheduler.passed_predicates.map((e=>_`
                  <mwc-list-item graphic="icon" noninteractive>
                    <span>${e.name}</span>
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
      `)}else if(d.hasOwnProperty("error")){const e=null!==(c=d.error.collection)&&void 0!==c?c:[d.error];u.push(_`
        <div class="vertical layout start flex" style="width:100%;">
          <div style="width:100%;">
            <h3
              style="width:100%;padding-left:15px;border-bottom:1px solid var(--token-colorBorder, #ccc);"
            >
              ${f("session.StatusDetail")}
            </h3>
            ${e.map((e=>_`
                <div class="error-detail-panel">
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
                            ${e.traceback}
                          </pre
                          >
                        </div>
                      `:_``}
                </div>
              `))}
          </div>
        </div>
      `)}else u.push(_`
        <div class="vertical layout start flex" style="width:100%;">
          <h3
            style="width:100%;padding-left:15px;border-bottom:1px solid var(--token-colorBorder, #ccc);"
          >
            Detail
          </h3>
          <span style="margin:20px;">No Detail.</span>
        </div>
      `);b(u,p)}_openStatusDetailDialog(e,t,i){this.selectedSessionStatus={info:e,data:t,reserved_time:i},this._renderStatusDetail(),this.sessionStatusInfoDialog.show()}_validateSessionName(e){const t=this.compute_sessions.map((e=>e[this.sessionNameField])),i=e.target.parentNode,s=i.querySelector("#session-name-field").innerText,o=i.querySelector("#session-rename-field");o.validityTransform=(e,i)=>{if(i.valid){const i=!t.includes(e)||e===s;return i||(o.validationMessage=f("session.Validation.SessionNameAlreadyExist")),{valid:i,customError:!i}}return i.valueMissing?(o.validationMessage=f("session.Validation.SessionNameRequired"),{valid:i.valid,valueMissing:!i.valid}):i.patternMismatch?(o.validationMessage=f("session.Validation.SluggedStrings"),{valid:i.valid,patternMismatch:!i.valid}):(o.validationMessage=f("session.Validation.EnterValidSessionName"),{valid:i.valid,customError:!i.valid})}}_renameSessionName(e,t){const i=t.target.parentNode,s=i.querySelector("#session-name-field"),o=i.querySelector("#session-rename-field"),n=i.querySelector("#session-rename-icon");if("none"===s.style.display){if(!o.checkValidity())return o.reportValidity(),void(n.on=!0);{const t=globalThis.backendaiclient.APIMajorVersion<5?s.value:e;globalThis.backendaiclient.rename(t,o.value).then((e=>{this.refreshList(),this.notification.text=f("session.SessionRenamed"),this.notification.show()})).catch((e=>{o.value=s.innerText,e&&e.message&&(this.notification.text=v.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))})).finally((()=>{this._toggleSessionNameField(s,o)}))}}else this._toggleSessionNameField(s,o)}_toggleSessionNameField(e,t){"block"===t.style.display?(e.style.display="block",t.style.display="none"):(e.style.display="none",t.style.display="block",t.focus())}static secondsToDHMS(e){const t=Math.floor(e/86400),i=Math.floor(e%86400/3600),s=Math.floor(e%3600/60),o=parseInt(e)%60,n=t<0||i<0||s<0||o<0?f("session.TimeoutExceeded"):"",a=`${void 0!==t&&t>0?String(t)+"d":""}${i.toString().padStart(2,"0")}:${s.toString().padStart(2,"0")}:${o.toString().padStart(2,"0")}`;return n.length>0?n:a}_getIdleSessionTimeout(e){if(globalThis.backendaiutils.isEmpty(e))return null;let t="",i=1/0;for(const[s,o]of Object.entries(e))null!=o&&"number"==typeof o&&null!=i&&o<i&&(t=s,i=o);return i?[t,N.secondsToDHMS(i)]:null}_openIdleChecksInfoDialog(){var e,t,i;this._helpDescriptionTitle=f("session.IdleChecks"),this._helpDescription=`\n      <p>${f("session.IdleChecksDesc")}</p>\n      ${(null===(e=this.activeIdleCheckList)||void 0===e?void 0:e.has("session_lifetime"))?`\n        <strong>${f("session.MaxSessionLifetime")}</strong>\n        <p>${f("session.MaxSessionLifetimeDesc")}</p>\n        `:""}\n      ${(null===(t=this.activeIdleCheckList)||void 0===t?void 0:t.has("network_timeout"))?`\n        <strong>${f("session.NetworkIdleTimeout")}</strong>\n        <p>${f("session.NetworkIdleTimeoutDesc")}</p>\n      `:""}\n      ${(null===(i=this.activeIdleCheckList)||void 0===i?void 0:i.has("utilization"))?`\n        <strong>${f("session.UtilizationIdleTimeout")}</strong>\n        <p>${f("session.UtilizationIdleTimeoutDesc")}</p>\n        <div style="margin:10px 5% 20px 5%;">\n          <li>\n            <span style="font-weight:500">${f("session.GracePeriod")}</span>\n            <div style="padding-left:20px;">${f("session.GracePeriodDesc")}</div>\n          </li>\n          <li>\n            <span style="font-weight:500">${f("session.UtilizationThreshold")}</span>\n            <div style="padding-left:20px;">${f("session.UtilizationThresholdDesc")}</div>\n          </li>\n        </div>\n      `:""}\n    `,this.helpDescriptionDialog.show()}async _openSFTPSessionConnectionInfoDialog(e,t){const i=await globalThis.backendaiclient.get_direct_access_info(e),s=i.public_host.replace(/^https?:\/\//,""),o=i.sshd_ports,n=new CustomEvent("read-ssh-key-and-launch-ssh-dialog",{detail:{sessionUuid:e,host:s,port:o,mounted:t}});document.dispatchEvent(n)}_createUtilizationIdleCheckDropdown(e,t){const i=e.target,s=document.createElement("mwc-menu");s.anchor=i,s.className="util-dropdown-menu",s.style.boxShadow="0 1px 1px rgba(0, 0, 0, 0.2)",s.setAttribute("open",""),s.setAttribute("fixed",""),s.setAttribute("corner","BOTTOM_START");let o=_``;globalThis.backendaiutils.isEmpty(t)||(o=_`
        <style>
          .util-detail-menu-header {
            height: 25px;
            border: none;
            box-shadow: none;
            justify-content: flex-end;
          }
          .util-detail-menu-header > div {
            font-size: 13px;
            font-family: var(--token-fontFamily);
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
            font-family: var(--token-fontFamily);
            font-weight: 400;
            min-width: 155px;
          }
        </style>
        <mwc-list-item class="util-detail-menu-header">
          <div>
            ${f("session.Utilization")} / ${f("session.Threshold")} (%)
          </div>
        </mwc-list-item>
        ${Object.keys(t).map((e=>{let[i,s]=t[e];i=i>=0?parseFloat(i).toFixed(1):"-";const o=this.getUtilizationCheckerColor([i,s]);return _`
            <mwc-list-item class="util-detail-menu-content">
              <div>
                <div>${this.idleChecksTable[e]}</div>
                <div style="color:${o}">${i} / ${s}</div>
              </div>
            </mwc-list-item>
          `}))}
      `,document.body.appendChild(s)),b(o,s)}_removeUtilizationIdleCheckDropdown(){var e;const t=document.getElementsByClassName("util-dropdown-menu");for(;t[0];)null===(e=t[0].parentNode)||void 0===e||e.removeChild(t[0])}sessionTypeRenderer(e,t,i){const s=JSON.parse(i.item.inference_metrics||"{}");b(_`
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
              white-space-collapse: collapse;
            }
          </style>
          <div class="layout vertical start">
            <div class="horizontal center start-justified layout">
              <pre id="session-name-field">
                ${i.item.mounts[0]} SFTP Session
              </pre
              >
            </div>
          </div>
        `,e):b(_`
          <style>
            #session-name-field {
              display: block;
              margin-left: 16px;
              white-space: pre-wrap;
              white-space-collapse: collapse;
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
                      pattern="^[a-zA-Z0-9]([a-zA-Z0-9\\-_\\.]{2,})[a-zA-Z0-9]$"
                      minLength="4"
                      maxLength="64"
                      validationMessage="${f("session.Validation.EnterValidSessionName")}"
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
      `,e)}controlRenderer(e,t,i){var s;let o=!0;o="API"===this._connectionMode&&i.item.access_key===globalThis.backendaiclient._config._accessKey||i.item.user_email===globalThis.backendaiclient.email,b(_`
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
                  ?disabled="${!o}"
                  icon="apps"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.index+"-apps"}"
                  text="${y("session.SeeAppDialog")}"
                  position="top-start"
                ></vaadin-tooltip>
                <mwc-icon-button
                  class="fg controls-running"
                  id="${i.index+"-terminal"}"
                  ?disabled="${!o}"
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
                  text="${y("session.ExecuteTerminalApp")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:_``}
          ${this._isRunning&&"system"===this.condition?_`
                <mwc-icon-button
                  class="fg green controls-running"
                  id="${i.index+"-sftp-connection-info"}"
                  @click="${()=>this._openSFTPSessionConnectionInfoDialog(i.item.id,i.item.mounts.length>0?i.item.mounts.filter((e=>!e.startsWith(".")))[0]:"")}"
                >
                  <img src="/resources/icons/sftp.png" />
                </mwc-icon-button>
                <vaadin-tooltip
                  for="${i.index+"-sftp-connection-info"}"
                  text="${y("data.explorer.RunSSH/SFTPserver")}"
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
                  text="${y("session.TerminateSession")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:_``}
          ${!(this._isRunning&&!this._isPreparing(i.item.status)||this._APIMajorVersion>4)||this._isPending(i.item.status)||this._isPreparing(i.item.status)?_`
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
                  text="${y("session.NoLogMsgAvailable")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:_`
                <mwc-icon-button
                  class="fg blue controls-running"
                  id="${i.index+"-assignment"}"
                  icon="assignment"
                  ?disabled="${"CANCELLED"===i.item.status}"
                  @click="${e=>{var t,i;this._setSelectedSession(e),this._setSelectedKernel(),this.selectedKernelId=null===(t=this.selectedKernels[0])||void 0===t?void 0:t.kernel_id,(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#kernel-id-select")).value=this.selectedKernelId,this._showLogs()}}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.index+"-assignment"}"
                  text="${y("session.SeeContainerLogs")}"
                  position="top-start"
                ></vaadin-tooltip>
              `}
          ${this._isContainerCommitEnabled&&"system"!==this.condition?_`
                <mwc-icon-button
                  class="fg blue controls-running"
                  id="${i.index+"-archive"}"
                  ?disabled=${this._isPending(i.item.status)||this._isPreparing(i.item.status)||this._isError(i.item.status)||this._isFinished(i.item.status)||"BATCH"===i.item.type||"ongoing"===i.item.commit_status||i.item.user_email!==globalThis.backendaiclient.email}
                  icon="archive"
                  @click="${e=>this._openCommitSessionDialog(e)}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${i.index+"-archive"}"
                  text="${y("session.RequestContainerCommit")}"
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
              <span class="indicator">${y("session.core")}</span>
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
                      src="/resources/icons/rocm.svg"
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
              ${i.item.atom_plus_slot?_`
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/rebel.svg"
                    />
                    <span>${i.item.atom_plus_slot}</span>
                    <span class="indicator">ATOM+</span>
                  `:_``}
              ${i.item.warboy_slot?_`
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/furiosa.svg"
                    />
                    <span>${i.item.warboy_slot}</span>
                    <span class="indicator">Warboy</span>
                  `:_``}
              ${i.item.hyeraccel_lpu_slot?_`
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/npu_generic.svg"
                    />
                    <span>${i.item.hyeraccel_lpu_slot}</span>
                    <span class="indicator">Hyperaccel LPU</span>
                  `:_``}
              ${i.item.cuda_gpu_slot||i.item.cuda_fgpu_slot||i.item.rocm_gpu_slot||i.item.tpu_slot||i.item.ipu_slot||i.item.atom_slot||i.item.atom_plus_slot||i.item.warboy_slot||i.item.hyperaccel_lpu_slot?_``:_`
                    <mwc-icon class="fg green indicator">view_module</mwc-icon>
                    <span>-</span>
                    <span class="indicator">GPU</span>
                  `}
            </div>
          </div>
        `,e)}usageRenderer(e,t,i){var s,o,n,a,l,r,c,d,p,u,h,m,g,v,f,y,w,k,x,A,S,$,T,C,I,D,E,R,j,M,z,L,F,O,P,B,U,G,K,H,q,V,J,W,Y,Z,Q,X,ee,te,ie,se,oe,ne,ae,le,re,ce,de,pe,ue,he,me,ge,ve,be,_e,fe;["batch","interactive","inference","running"].includes(this.condition)?b(_`
          <div class="vertical start start-justified layout">
            <div class="vertical start-justified layout">
              <div class="usage-items">
                CPU
                ${(100*(null===(o=null===(s=i.item.live_stat)||void 0===s?void 0:s.cpu_util)||void 0===o?void 0:o.ratio)).toFixed(1)} %
              </div>
              <div class="horizontal start-justified center layout">
                <lablup-progress-bar
                  class="usage"
                  progress="${(null===(a=null===(n=i.item.live_stat)||void 0===n?void 0:n.cpu_util)||void 0===a?void 0:a.ratio)/(null===(r=null===(l=i.item.live_stat)||void 0===l?void 0:l.cpu_util)||void 0===r?void 0:r.slots)||0}"
                  description=""
                ></lablup-progress-bar>
              </div>
            </div>
            <div class="vertical start-justified layout">
              <div class="usage-items">
                RAM
                ${N.bytesToGiB(null===(d=null===(c=i.item.live_stat)||void 0===c?void 0:c.mem)||void 0===d?void 0:d.current,1)}/${N.bytesToGiB(null===(u=null===(p=i.item.live_stat)||void 0===p?void 0:p.mem)||void 0===u?void 0:u.capacity,1)}
                GiB
              </div>
              <div class="horizontal start-justified center layout">
                <lablup-progress-bar
                  class="usage"
                  progress="${null===(m=null===(h=i.item.live_stat)||void 0===h?void 0:h.mem)||void 0===m?void 0:m.ratio}"
                  description=""
                ></lablup-progress-bar>
              </div>
            </div>
            ${i.item.cuda_gpu_slot&&parseInt(i.item.cuda_gpu_slot)>0?_`
                  <div class="vertical start-justified center layout">
                    <div class="usage-items">
                      GPU(util)
                      ${(100*(null===(v=null===(g=i.item.live_stat)||void 0===g?void 0:g.cuda_util)||void 0===v?void 0:v.ratio)).toFixed(1)}
                      %
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${(null===(y=null===(f=i.item.live_stat)||void 0===f?void 0:f.cuda_util)||void 0===y?void 0:y.current)/(null===(k=null===(w=i.item.live_stat)||void 0===w?void 0:w.cuda_util)||void 0===k?void 0:k.capacity)||0}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:_``}
            ${i.item.cuda_fgpu_slot&&parseFloat(i.item.cuda_fgpu_slot)>0?_`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      GPU(util)
                      ${(100*(null===(A=null===(x=i.item.live_stat)||void 0===x?void 0:x.cuda_util)||void 0===A?void 0:A.ratio)).toFixed(1)}
                      %
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${(null===($=null===(S=i.item.live_stat)||void 0===S?void 0:S.cuda_util)||void 0===$?void 0:$.current)/(null===(C=null===(T=i.item.live_stat)||void 0===T?void 0:T.cuda_util)||void 0===C?void 0:C.capacity)||0}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:_``}
            ${i.item.rocm_gpu_slot&&parseFloat(i.item.cuda_rocm_gpu_slot)>0?_`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      GPU(util)
                      ${(100*(null===(D=null===(I=i.item.live_stat)||void 0===I?void 0:I.rocm_util)||void 0===D?void 0:D.ratio)).toFixed(1)}
                      %
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${(null===(R=null===(E=i.item.live_stat)||void 0===E?void 0:E.rocm_util)||void 0===R?void 0:R.current)/(null===(M=null===(j=i.item.live_stat)||void 0===j?void 0:j.rocm_util)||void 0===M?void 0:M.capacity)||0}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:_``}
            ${i.item.cuda_fgpu_slot||i.item.rocm_gpu_slot?_`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      GPU(mem)
                      ${N.bytesToGiB(null===(L=null===(z=i.item.live_stat)||void 0===z?void 0:z.cuda_mem)||void 0===L?void 0:L.current,1)}/${N.bytesToGiB(null===(O=null===(F=i.item.live_stat)||void 0===F?void 0:F.cuda_mem)||void 0===O?void 0:O.capacity,1)}
                      GiB
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${null===(B=null===(P=i.item.live_stat)||void 0===P?void 0:P.cuda_mem)||void 0===B?void 0:B.ratio}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:_``}
            ${i.item.tpu_slot&&parseFloat(i.item.tpu_slot)>0?_`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      TPU(util)
                      ${(100*(null===(G=null===(U=i.item.live_stat)||void 0===U?void 0:U.tpu_util)||void 0===G?void 0:G.ratio)).toFixed(1)}
                      %
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${(null===(H=null===(K=i.item.live_stat)||void 0===K?void 0:K.tpu_util)||void 0===H?void 0:H.current)/(null===(V=null===(q=i.item.live_stat)||void 0===q?void 0:q.tpu_util)||void 0===V?void 0:V.capacity)||0}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:_``}
            ${i.item.ipu_slot&&parseFloat(i.item.ipu_slot)>0?_`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      IPU(util)
                      ${(100*(null===(W=null===(J=i.item.live_stat)||void 0===J?void 0:J.ipu_util)||void 0===W?void 0:W.ratio)).toFixed(1)}
                      %
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${(null===(Q=null===(Z=null===(Y=i.item)||void 0===Y?void 0:Y.live_stat)||void 0===Z?void 0:Z.ipu_util)||void 0===Q?void 0:Q.current)/(null===(te=null===(ee=null===(X=i.item)||void 0===X?void 0:X.live_stat)||void 0===ee?void 0:ee.ipu_util)||void 0===te?void 0:te.capacity)||0}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:_``}
            ${i.item.atom_slot&&parseFloat(i.item.atom_slot)>0?_`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      ATOM(util)
                      ${(100*(null===(se=null===(ie=i.item.live_stat)||void 0===ie?void 0:ie.atom_util)||void 0===se?void 0:se.ratio)).toFixed(1)}
                      %
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${(null===(ae=null===(ne=null===(oe=i.item)||void 0===oe?void 0:oe.live_stat)||void 0===ne?void 0:ne.atom_util)||void 0===ae?void 0:ae.current)/(null===(ce=null===(re=null===(le=i.item)||void 0===le?void 0:le.live_stat)||void 0===re?void 0:re.atom_util)||void 0===ce?void 0:ce.capacity)||0}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:_``}
            <div class="horizontal start-justified center layout">
              <div class="usage-items">I/O</div>
              <div
                style="font-size:10px;margin-left:5px;"
                class="horizontal start-justified center layout"
              >
                R: ${null===(ue=null===(pe=null===(de=i.item)||void 0===de?void 0:de.live_stat)||void 0===pe?void 0:pe.io_read)||void 0===ue?void 0:ue.current.toFixed(1)} MB /
                W: ${null===(ge=null===(me=null===(he=i.item)||void 0===he?void 0:he.live_stat)||void 0===me?void 0:me.io_write)||void 0===ge?void 0:ge.current.toFixed(1)} MB
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
                ${null===(be=null===(ve=i.item.live_stat)||void 0===ve?void 0:ve.io_read)||void 0===be?void 0:be.current.toFixed(1)}
                <span class="indicator">MB</span>
              </span>
              <span class="indicator">READ</span>
            </div>
            <div class="vertical start layout">
              <span style="font-size:8px">
                ${null===(fe=null===(_e=i.item.live_stat)||void 0===_e?void 0:_e.io_write)||void 0===fe?void 0:fe.current.toFixed(1)}
                <span class="indicator">MB</span>
              </span>
              <span class="indicator">WRITE</span>
            </div>
          </div>
        `,e)}reservationRenderer(e,t,i){b(_`
        <div class="layout vertical" style="padding:3px auto;">
          <span>${i.item.created_at_hr}</span>
          <lablup-shields
            app="${y("session.ElapsedTime")}"
            color="darkgreen"
            style="margin:3px 0;"
            description="${i.item.elapsed}"
            ui="round"
          ></lablup-shields>
        </div>
      `,e)}idleChecksHeaderRenderer(e,t){b(_`
        <div class="horizontal layout center">
          <div>${y("session.IdleChecks")}</div>
          <mwc-icon-button
            class="fg grey"
            icon="info"
            @click="${()=>this._openIdleChecksInfoDialog()}"
          ></mwc-icon-button>
        </div>
      `,e)}idleChecksRenderer(e,t,i){var s;const o=null===(s=Object.keys(i.item.idle_checks))||void 0===s?void 0:s.map((e=>{var t,s;const o=i.item.idle_checks[e],n=null==o?void 0:o.remaining;if(!n)return;const a=globalThis.backendaiclient.utils.elapsedTimeToTotalSeconds(n),l=null==o?void 0:o.remaining_time_type;let r,c="var(--token-colorSuccess";return!a||a<3600?c="var(--token-colorError)":a<14400&&(c="var(--token-colorWarning)"),"utilization"===e&&(null==o?void 0:o.extra)&&(!a||a<14400)&&(c=this.getUtilizationCheckerColor(null===(t=null==o?void 0:o.extra)||void 0===t?void 0:t.resources,null===(s=null==o?void 0:o.extra)||void 0===s?void 0:s.thresholds_check_operator)),r="utilization"===e?_`
            <button
              class="idle-check-key"
              style="color:#42a5f5;"
              @mouseenter="${e=>{var t,s,o;return this._createUtilizationIdleCheckDropdown(e,null===(o=null===(s=null===(t=i.item.idle_checks)||void 0===t?void 0:t.utilization)||void 0===s?void 0:s.extra)||void 0===o?void 0:o.resources)}}"
              @mouseleave="${()=>this._removeUtilizationIdleCheckDropdown()}"
            >
              ${f("session."+this.idleChecksTable[e])}
            </button>
          `:_`
            <button class="idle-check-key" style="color:#222222;">
              ${f("session."+this.idleChecksTable[e])}
            </button>
          `,e in this.idleChecksTable?_`
            <div class="layout vertical" style="padding:3px auto;">
              <div style="margin:4px;">
                ${r}
                <br />
                <strong style="color:${c}">${n}</strong>
                <div class="idle-type">
                  ${f("session."+this.idleChecksTable[l])}
                </div>
              </div>
            </div>
          `:_``})),n=_`
      ${o}
    `;b(n,e)}agentListRenderer(e,t,i){var s;b(_`
        <pre>${null===(s=i.item.agents_ids_with_container_ids)||void 0===s?void 0:s.join("\n")}</pre>
      `,e)}_toggleCheckbox(e){const t=this._selected_items.findIndex((t=>t.session_id==e.session_id));-1===t?this._selected_items.push(e):this._selected_items.splice(t,1),this._selected_items.length>0?this.multipleActionButtons.style.display="block":this.multipleActionButtons.style.display="none"}_aggregateSharedMemory(e){let t=0;return Object.keys(e).forEach((i=>{var s,o;t+=Number(null!==(o=null===(s=e[i])||void 0===s?void 0:s.shmem)&&void 0!==o?o:0)})),N.bytesToGiB(t)}checkboxRenderer(e,t,i){this._isRunning&&!this._isPreparing(i.item.status)||this._APIMajorVersion>4?b(_`
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
      `,e)}_setColorOfStatusInformation(e="ready"){return"ready"===e?"green":"lightgrey"}_getUserId(e=""){if(e&&this.isUserInfoMaskEnabled){const t=/^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/.test(e),i=t?2:0,s=t?e.split("@")[0].length-i:0;e=globalThis.backendaiutils._maskString(e,"*",i,s)}return e}_renderCommitSessionConfirmationDialog(e){var t,i,s,o,n,a,l;return _`
      <backend-ai-dialog id="commit-session-dialog" fixed backdrop>
        <span slot="title">${y("session.CommitSession")}</span>
        <div slot="content" class="vertical layout center flex">
          <span style="font-size:14px;">
            ${y("session.DescCommitSession")}
          </span>
          <div class="vertical flex start layout" style="width:100%;">
            <h4 class="commit-session-title">${y("session.SessionName")}</h4>
            <span class="commit-session-subheading">
              ${null!==(i=null===(t=null==e?void 0:e.session)||void 0===t?void 0:t.name)&&void 0!==i?i:"-"}
            </span>
          </div>
          <div class="vertical flex start layout" style="width:100%;">
            <h4 class="commit-session-title">${y("session.SessionId")}</h4>
            <span class="commit-session-subheading">
              ${null!==(o=null===(s=null==e?void 0:e.session)||void 0===s?void 0:s.id)&&void 0!==o?o:"-"}
            </span>
          </div>
          <div class="vertical flex start layout" style="width:100%;">
            <h4 class="commit-session-title">
              ${y("session.EnvironmentAndVersion")}
            </h4>
            <span class="commit-session-subheading">
              ${e?_`
                    <lablup-shields
                      app="${null!==(n=e.environment)&&void 0!==n?n:"-"}"
                      color="blue"
                      description="${null!==(a=e.version)&&void 0!==a?a:"-"}"
                      ui="round"
                      class="right-below-margin"
                    ></lablup-shields>
                  `:_``}
            </span>
          </div>
          <div class="vertical flex start layout" style="width:100%;">
            <h4 class="commit-session-title">${y("session.Tags")}</h4>
            <div class="horizontal wrap layout">
              ${e?null===(l=null==e?void 0:e.tags)||void 0===l?void 0:l.map((e=>_`
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
            </div>
          </div>
          <div class="vertical flex start layout" style="width:100%;">
            <h4 class="commit-session-title">${y("session.SessionName")}</h4>
            <div class="horizontal layout flex" style="width:100%">
              <!--<mwc-checkbox
                class="list-check"
                ?checked="${this.pushImageInsteadOfCommiting}"
                @click="${()=>{this.pushImageInsteadOfCommiting=!this.pushImageInsteadOfCommiting}}"
              ></mwc-checkbox>-->
              <mwc-textfield
                id="new-image-name-field"
                required
                pattern="^[a-zA-Z0-9_\\-]{4,}$"
                minLength="4"
                maxLength="32"
                placeholder="${y("inputLimit.4to32chars")}"
                validationMessage="${f("session.Validation.EnterValidSessionName")}"
                style="margin-top:8px;width:100%;"
                autoValidate
                @input="${this._validateImageName}"
              ></mwc-textfield>
            </div>
          </div>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            unelevated
            class="ok"
            style="font-size:smaller"
            ?disabled="${!this.canStartImagifying}"
            @click=${()=>{this._requestConvertSessionToimage(e)}}
            label="${y("button.PushToImage")}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}_parseSessionInfoToCommitSessionInfo(e="",t="",i=""){const s=["",""],[o,n]=e?e.split(":"):s,[a,...l]=n?n.split("-"):s;return{environment:o,version:a,tags:l,session:{name:t,id:i}}}render(){var e,t,i;return _`
      <link rel="stylesheet" href="resources/custom.css">
      <div class="layout horizontal center filters">
        <div id="multiple-action-buttons" style="display:none;">
          <mwc-button icon="delete" class="multiple-action-button" raised style="margin:8px;"
            @click="${()=>this._openTerminateSelectedSessionsDialog()}">${y("session.Terminate")}
          </mwc-button>
        </div>
        <span class="flex"></span>
        <div class="vertical layout" style="display:none">
          <mwc-textfield id="access-key-filter" type="search" maxLength="64"
            label="${y("general.AccessKey")}" 
            no-label-float .value="${this.filterAccessKey}"
            style="margin-right:20px;"
            @change="${e=>this._updateFilterAccessKey(e)}">
          </mwc-textfield>
          <span id="access-key-filter-helper-text">${y("maxLength.64chars")}</span>
        </div>
      </div>
      <div class="list-wrapper">
        <vaadin-grid id="list-grid" theme="row-stripes column-borders compact dark" aria-label="Session list"
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
          <lablup-grid-sort-filter-column frozen path="${this.sessionNameField}" 
            width="260px"
            header="${y("session.SessionInfo")}" 
            resizable
            .renderer="${this._boundSessionInfoRenderer}"
          >
          </lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column width="120px" path="status" header="${y("session.Status")}" 
            resizable
            .renderer="${this._boundStatusRenderer}">
          </lablup-grid-sort-filter-column>
          <vaadin-grid-column width=${this._isContainerCommitEnabled?"260px":"210px"} flex-grow="0" resizable header="${y("general.Control")}"
                              .renderer="${this._boundControlRenderer}"></vaadin-grid-column>
          <vaadin-grid-column width="200px" flex-grow="0" resizable header="${y("session.Configuration")}"
                              .renderer="${this._boundConfigRenderer}"></vaadin-grid-column>
          <vaadin-grid-column width="140px" flex-grow="0" resizable header="${y("session.Usage")}"
                              .renderer="${this._boundUsageRenderer}">
          </vaadin-grid-column>
          <vaadin-grid-sort-column resizable width="180px" flex-grow="0" header="${y("session.Reservation")}"
                                   path="created_at" .renderer="${this._boundReservationRenderer}">
          </vaadin-grid-sort-column>
          ${globalThis.backendaiclient.supports("idle-checks")&&this.activeIdleCheckList.size>0?_`
                  <vaadin-grid-column
                    resizable
                    width="180px"
                    flex-grow="0"
                    .headerRenderer="${this._boundIdleChecksHeaderderer}"
                    .renderer="${this._boundIdleChecksRenderer}"
                  ></vaadin-grid-column>
                `:_``}
          <lablup-grid-sort-filter-column width="110px" path="architecture" header="${y("session.Architecture")}" resizable
                                     .renderer="${this._boundArchitectureRenderer}">
          </lablup-grid-sort-filter-column>
          ${this._isIntegratedCondition?_`
                  <lablup-grid-sort-filter-column
                    path="type"
                    width="140px"
                    flex-grow="0"
                    header="${y("session.launcher.SessionType")}"
                    resizable
                    .renderer="${this._boundSessionTypeRenderer}"
                  ></lablup-grid-sort-filter-column>
                `:_``}
          ${this.is_superadmin||!globalThis.backendaiclient._config.hideAgents?_`
                  <lablup-grid-sort-filter-column
                    width="140px"
                    flex-grow="0"
                    resizable
                    header="${y("session.Agents")}"
                    .renderer="${this._boundAgentListRenderer}"
                  ></lablup-grid-sort-filter-column>
                `:_``}
          </vaadin-grid>
          <backend-ai-list-status id="list-status" statusCondition="${this.listCondition}" message="${f("session.NoSessionToDisplay")}"></backend-ai-list-status>
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
        <span slot="title" id="work-title">
        </span>
        <div slot="action" class="horizontal layout center">
          <mwc-select
            id="kernel-id-select"
            label="Kernel Role"
            style="display: ${this._isPerKernelLogSupported?"block":"none"}"
            @selected=${()=>{this._updateLogsByKernelId(),this._showLogs()}}
          >
            ${this.selectedKernels.map((e=>_`
                <mwc-list-item
                  value=${e.kernel_id}
                  label="${e.role}"
                  ?selected=${e.role.includes("main")}
                >
                  ${e.role}
                </mwc-list-item>
              `))}
          </mwc-select>
          <mwc-icon-button fab flat inverted icon="download" @click="${()=>this._downloadLogs()}">
          </mwc-icon-button>
          <mwc-icon-button fab flat inverted icon="refresh" @click="${e=>this._refreshLogs()}">
          </mwc-icon-button>
        </div>
        <div slot="content" id="work-area" style="overflow:scroll;"></div>
        <iframe id="work-page" style="border-style: none;display: none;width: 100%;"></iframe>
      </backend-ai-dialog>
      <backend-ai-dialog id="terminate-session-dialog" fixed backdrop>
        <span slot="title">${y("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${y("usersettings.SessionTerminationDialog")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button class="warning fg red" @click="${()=>{this._getManualCleanUpNeededContainers(),this._openForceTerminateConfirmationDialog()}}">
            ${y("button.ForceTerminate")}
          </mwc-button>
          <span class="flex"></span>
          <mwc-button class="cancel" @click="${e=>this._hideDialog(e)}">${y("button.Cancel")}
          </mwc-button>
          <mwc-button class="ok" raised @click="${()=>this._terminateSessionWithCheck()}">${y("button.Okay")}</mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="terminate-selected-sessions-dialog" fixed backdrop>
        <span slot="title">${y("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${y("usersettings.SessionTerminationDialog")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            class="warning fg red"
            @click="${()=>{this._getManualCleanUpNeededContainers(),this._openForceTerminateConfirmationDialog()}}">
            ${y("button.ForceTerminate")}
          </mwc-button>
          <span class="flex"></span>
          <mwc-button class="cancel" @click="${e=>this._hideDialog(e)}">${y("button.Cancel")}
          </mwc-button>
          <mwc-button class="ok" raised @click="${()=>this._terminateSelectedSessionsWithCheck()}">${y("button.Okay")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="force-terminate-confirmation-dialog" fixed backdrop>
        <span slot="title">${y("session.WarningForceTerminateSessions")}</span>
        <div slot="content">
          <span>${y("session.ForceTerminateWarningMsg")}</span>
          <ul class="force-terminate-confirmation">
            <li>${y("session.ForceTerminateWarningMsg2")}</li>
            <li>${y("session.ForceTerminateWarningMsg3")}</li>
          </ul>
          ${this._manualCleanUpNeededContainers.length>0&&this.is_superadmin?_`
                  <div
                    class="vertical layout flex start-justified force-terminate-confirmation-container-list"
                  >
                    <div class="horizontal layout center flex start-justified">
                      <h3 style="margin:0px;">
                        ${y("session.ContainerToCleanUp")}:
                      </h3>
                    </div>
                    ${this._manualCleanUpNeededContainers.map((e=>_`
                        <ul class="force-terminate-confirmation">
                          <li>Agent ID: ${e.agent}</li>
                          <ul class="force-terminate-confirmation">
                            ${e.containers.map((e=>_`
                                <li>
                                  Container ID:
                                  <span class="monospace">${e}</span>
                                </li>
                              `))}
                          </ul>
                          <ul></ul>
                        </ul>
                      `))}
                  </div>
                `:_``}
        </div>
        <div slot="footer" class="horizontal layout flex cetner-justified">
            <mwc-button
              raised
              class="warning fg red"
              style="width:100%;"
              @click="${()=>{this.forceTerminateConfirmationDialog.hide(),this.terminateSessionDialog.open?(this.terminateSessionDialog.hide(),this._terminateSessionWithCheck(!0)):(this.terminateSelectedSessionsDialog.hide(),this._terminateSelectedSessionsWithCheck(!0))}}">
                ${y("button.ForceTerminate")}
            </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="status-detail-dialog" narrowLayout fixed backdrop>
        <span slot="title">${y("session.StatusInfo")}</span>
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
          <div style="font-size:14px;">${w(this._helpDescription)}</div>
        </div>
      </backend-ai-dialog>
      ${this._renderCommitSessionConfirmationDialog(this._parseSessionInfoToCommitSessionInfo(null===(e=this.commitSessionDialog)||void 0===e?void 0:e.kernelImage,null===(t=this.commitSessionDialog)||void 0===t?void 0:t.sessionName,null===(i=this.commitSessionDialog)||void 0===i?void 0:i.sessionId))}
    `}_updateSessionPage(e){"previous-page"===e.target.id?this.current_page-=1:this.current_page+=1,this.refreshList()}_validateImageName(){this.newImageNameInput.validityTransform=(e,t)=>t.valid?(this.canStartImagifying=!0,this.newImageName=e,{valid:t.valid,customError:!t.valid}):(this.canStartImagifying=!1,t.patternMismatch?(this.newImageNameInput.validationMessage=f("session.Validation.EnterValidSessionName"),{valid:t.valid,patternMismatch:!t.valid}):(this.newImageNameInput.validationMessage=f("session.Validation.EnterValidSessionName"),{valid:t.valid,customError:!t.valid}))}};var M;r([c({type:Boolean,reflect:!0})],j.prototype,"active",void 0),r([c({type:String})],j.prototype,"condition",void 0),r([c({type:Object})],j.prototype,"jobs",void 0),r([c({type:Array})],j.prototype,"compute_sessions",void 0),r([c({type:Array})],j.prototype,"terminationQueue",void 0),r([c({type:String})],j.prototype,"filterAccessKey",void 0),r([c({type:String})],j.prototype,"sessionNameField",void 0),r([c({type:Array})],j.prototype,"appSupportList",void 0),r([c({type:Object})],j.prototype,"appTemplate",void 0),r([c({type:Object})],j.prototype,"imageInfo",void 0),r([c({type:Array})],j.prototype,"_selected_items",void 0),r([c({type:Array})],j.prototype,"_manualCleanUpNeededContainers",void 0),r([c({type:Object})],j.prototype,"_boundControlRenderer",void 0),r([c({type:Object})],j.prototype,"_boundConfigRenderer",void 0),r([c({type:Object})],j.prototype,"_boundUsageRenderer",void 0),r([c({type:Object})],j.prototype,"_boundReservationRenderer",void 0),r([c({type:Object})],j.prototype,"_boundIdleChecksHeaderderer",void 0),r([c({type:Object})],j.prototype,"_boundIdleChecksRenderer",void 0),r([c({type:Object})],j.prototype,"_boundAgentListRenderer",void 0),r([c({type:Object})],j.prototype,"_boundSessionInfoRenderer",void 0),r([c({type:Object})],j.prototype,"_boundArchitectureRenderer",void 0),r([c({type:Object})],j.prototype,"_boundCheckboxRenderer",void 0),r([c({type:Object})],j.prototype,"_boundUserInfoRenderer",void 0),r([c({type:Object})],j.prototype,"_boundStatusRenderer",void 0),r([c({type:Object})],j.prototype,"_boundSessionTypeRenderer",void 0),r([c({type:Boolean})],j.prototype,"refreshing",void 0),r([c({type:Boolean})],j.prototype,"is_admin",void 0),r([c({type:Boolean})],j.prototype,"is_superadmin",void 0),r([c({type:String})],j.prototype,"_connectionMode",void 0),r([c({type:Object})],j.prototype,"notification",void 0),r([c({type:Boolean})],j.prototype,"enableScalingGroup",void 0),r([c({type:Boolean})],j.prototype,"isDisplayingAllocatedShmemEnabled",void 0),r([c({type:String})],j.prototype,"listCondition",void 0),r([c({type:Object})],j.prototype,"refreshTimer",void 0),r([c({type:Object})],j.prototype,"kernel_labels",void 0),r([c({type:Object})],j.prototype,"kernel_icons",void 0),r([c({type:Object})],j.prototype,"indicator",void 0),r([c({type:String})],j.prototype,"_helpDescription",void 0),r([c({type:String})],j.prototype,"_helpDescriptionTitle",void 0),r([c({type:String})],j.prototype,"_helpDescriptionIcon",void 0),r([c({type:Set})],j.prototype,"activeIdleCheckList",void 0),r([c({type:Array})],j.prototype,"selectedKernels",void 0),r([c({type:String})],j.prototype,"selectedKernelId",void 0),r([c({type:Proxy})],j.prototype,"statusColorTable",void 0),r([c({type:Proxy})],j.prototype,"idleChecksTable",void 0),r([c({type:Proxy})],j.prototype,"sessionTypeColorTable",void 0),r([c({type:Number})],j.prototype,"sshPort",void 0),r([c({type:Number})],j.prototype,"vncPort",void 0),r([c({type:Number})],j.prototype,"current_page",void 0),r([c({type:Number})],j.prototype,"session_page_limit",void 0),r([c({type:Number})],j.prototype,"total_session_count",void 0),r([c({type:Number})],j.prototype,"_APIMajorVersion",void 0),r([c({type:Object})],j.prototype,"selectedSessionStatus",void 0),r([c({type:Boolean})],j.prototype,"isUserInfoMaskEnabled",void 0),r([c({type:Boolean})],j.prototype,"pushImageInsteadOfCommiting",void 0),r([c({type:Boolean})],j.prototype,"canStartImagifying",void 0),r([c({type:String})],j.prototype,"newImageName",void 0),r([d("#loading-spinner")],j.prototype,"spinner",void 0),r([d("#list-grid")],j.prototype,"_grid",void 0),r([d("#access-key-filter")],j.prototype,"accessKeyFilterInput",void 0),r([d("#new-image-name-field")],j.prototype,"newImageNameInput",void 0),r([d("#multiple-action-buttons")],j.prototype,"multipleActionButtons",void 0),r([d("#access-key-filter-helper-text")],j.prototype,"accessKeyFilterHelperText",void 0),r([d("#terminate-session-dialog")],j.prototype,"terminateSessionDialog",void 0),r([d("#terminate-selected-sessions-dialog")],j.prototype,"terminateSelectedSessionsDialog",void 0),r([d("#force-terminate-confirmation-dialog")],j.prototype,"forceTerminateConfirmationDialog",void 0),r([d("#status-detail-dialog")],j.prototype,"sessionStatusInfoDialog",void 0),r([d("#work-dialog")],j.prototype,"workDialog",void 0),r([d("#help-description")],j.prototype,"helpDescriptionDialog",void 0),r([d("#commit-session-dialog")],j.prototype,"commitSessionDialog",void 0),r([d("#commit-current-session-path-input")],j.prototype,"commitSessionInput",void 0),r([d("#list-status")],j.prototype,"_listStatus",void 0),j=N=r([p("backend-ai-session-list")],j);let z=M=class extends u{constructor(){super(),this._status="inactive",this.active=!1,this.is_admin=!1,this.enableInferenceWorkload=!1,this.enableSFTPSession=!1,this.filterAccessKey="",this._connectionMode="API",this._defaultFileName="",this.active=!1,this._status="inactive"}static get styles(){return[h,m,g,k,x,i`
        mwc-menu {
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
      `]}firstUpdated(){this.notification=globalThis.lablupNotification,document.addEventListener("backend-ai-session-list-refreshed",(()=>{this.runningJobs.refreshList(!0,!1)})),this.resourceBroker=globalThis.resourceBroker,void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.is_admin=globalThis.backendaiclient.is_admin,this._connectionMode=globalThis.backendaiclient._config._connectionMode}),!0):(this.is_admin=globalThis.backendaiclient.is_admin,this._connectionMode=globalThis.backendaiclient._config._connectionMode)}async _viewStateChanged(e){if(await this.updateComplete,!1===e){this.resourceMonitor.removeAttribute("active"),this._status="inactive";for(let e=0;e<this.sessionList.length;e++)this.sessionList[e].removeAttribute("active");return}const t=()=>{this.enableInferenceWorkload=globalThis.backendaiclient.supports("inference-workload"),this.enableSFTPSession=globalThis.backendaiclient.supports("sftp-scaling-group"),this.resourceMonitor.setAttribute("active","true"),this.runningJobs.setAttribute("active","true"),this._status="active"};void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{t()}),!0):t()}_triggerClearTimeout(){const e=new CustomEvent("backend-ai-clear-timeout");document.dispatchEvent(e)}_showTab(e){var t,i,s;const o=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".tab-content");for(let e=0;e<o.length;e++)o[e].style.display="none";(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+e.title+"-lists")).style.display="block";for(let e=0;e<this.sessionList.length;e++)this.sessionList[e].removeAttribute("active");this._triggerClearTimeout(),(null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#"+e.title+"-jobs")).setAttribute("active","true")}_toggleDropdown(e){const t=this.dropdownMenu,i=e.target;t.anchor=i,t.open||t.show()}_openExportToCsvDialog(){const e=this.dropdownMenu;e.open&&e.close(),console.log("Downloading CSV File..."),this._defaultFileName=this._getDefaultCSVFileName(),this.exportToCsvDialog.show()}_getFirstDateOfMonth(){const e=new Date;return new Date(e.getFullYear(),e.getMonth(),2).toISOString().substring(0,10)}_getDefaultCSVFileName(){return(new Date).toISOString().substring(0,10)+"_"+(new Date).toTimeString().slice(0,8).replace(/:/gi,"-")}_validateDateRange(){const e=this.dateToInput,t=this.dateFromInput;if(e.value&&t.value){new Date(e.value).getTime()<new Date(t.value).getTime()&&(e.value=t.value)}}static _automaticScaledTime(e){let t=Object();const i=["D","H","M","S"],s=[864e5,36e5,6e4,1e3];for(let o=0;o<s.length;o++)Math.floor(e/s[o])>0&&(t[i[o]]=Math.floor(e/s[o]),e%=s[o]);return 0===Object.keys(t).length&&(t=e>0?{MS:e}:{NODATA:1}),t}static bytesToMiB(e,t=1){return Number(e/2**20).toFixed(1)}_exportToCSV(){const e=this.exportFileNameInput;if(!e.validity.valid)return;const t=[];let i;i=globalThis.backendaiclient.supports("avoid-hol-blocking")?["RUNNING","RESTARTING","TERMINATING","PENDING","SCHEDULED","PREPARING","PULLING","TERMINATED","CANCELLED","ERROR"]:["RUNNING","RESTARTING","TERMINATING","PENDING","PREPARING","PULLING","TERMINATED","CANCELLED","ERROR"],globalThis.backendaiclient.supports("detailed-session-states")&&(i=i.join(","));const s=["id","name","user_email","image","created_at","terminated_at","status","status_info","access_key","cluster_mode","occupying_slots"];"SESSION"===this._connectionMode&&s.push("user_email"),globalThis.backendaiclient.is_superadmin?s.push("containers {container_id agent occupied_slots live_stat last_stat}"):s.push("containers {container_id occupied_slots live_stat last_stat}");const o=globalThis.backendaiclient.current_group_id(),n=Object.keys(this.resourceBroker.total_slot).filter((e=>!["cpu","mem"].includes(e))),a={cuda_device:"cuda.device",cuda_shares:"cuda.shares",rocm_device:"rocm.device",tpu_device:"tpu.device",ipu_device:"ipu.device",atom_device:"atom.device",atom_plus_device:"atom-plus.device",warboy_device:"warboy.device",hyperaccel_lpu_device:"hyperaccel-lpu.device"};globalThis.backendaiclient.computeSession.listAll(s,i,this.filterAccessKey,100,0,o).then((i=>{const s=i;if(0===s.length)return this.notification.text=f("session.NoSession"),this.notification.show(),void this.exportToCsvDialog.hide();s.forEach((e=>{const i=JSON.parse(e.occupying_slots),s={};if(s.id=e.id,s.name=e.name,s.image=e.image.split("/")[2]||e.image.split("/")[1],s.cluster_mode=e.cluster_mode,s.user_email=e.user_email,s.status=e.status,s.status_info=e.status_info,s.access_key=e.access_key,s.cpu_slot=parseInt(i.cpu),s.mem_slot=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(i.mem,"g")).toFixed(2),n.forEach((e=>{var t;s[e]=null!==(t=i[a[e]])&&void 0!==t?t:0})),s.created_at=e.created_at,s.terminated_at=e.terminated_at,e.containers&&e.containers.length>0){let t=0,i=0,o=0,n=0,a=0,l=0,r=0;const c=[];e.containers.forEach((e=>{c.push(e.agent);const s=e.live_stat?JSON.parse(e.live_stat):null;s&&(s.cpu_used&&s.cpu_used.current&&(t+=parseFloat(s.cpu_used.current)),s.cpu_util&&s.cpu_util.pct&&(i+=parseFloat(s.cpu_util.pct)),s.mem&&s.mem.pct&&(o+=parseFloat(s.mem.pct)),s.cuda_util&&s.cuda_util.pct&&(n+=parseFloat(s.cuda_util.pct)),s.cuda_mem&&s.cuda_mem.current&&(a+=parseFloat(s.cuda_mem.current)),s.io_read&&(l+=parseFloat(s.io_read.current)),s.io_write&&(r+=parseFloat(s.io_write.current)))})),s.agents=[...new Set(c)],s.cpu_used_time=M._automaticScaledTime(t/e.containers.length),s.cpu_util=(i/e.containers.length).toFixed(2),s.mem_util=(o/e.containers.length).toFixed(2),s.cuda_util=(n/e.containers.length).toFixed(2),s.cuda_mem_bytes_mb=M.bytesToMiB(a/e.containers.length),s.io_read_bytes_mb=M.bytesToMiB(l/e.containers.length),s.io_write_bytes_mb=M.bytesToMiB(r/e.containers.length)}t.push(s)})),A.exportToCsv(e.value,t),this.notification.text=f("session.DownloadingCSVFile"),this.notification.show(),this.exportToCsvDialog.hide()}))}render(){return _`
      <link rel="stylesheet" href="resources/custom.css" />
      <div class="vertical layout" style="gap:24px;">
        <lablup-activity-panel
          title="${y("summary.ResourceStatistics")}"
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
          title="${y("summary.Announcement")}"
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
                      label="${y("session.Running")}"
                      @click="${e=>this._showTab(e.target)}"
                    ></mwc-tab>
                    <mwc-tab
                      title="interactive"
                      label="${y("session.Interactive")}"
                      @click="${e=>this._showTab(e.target)}"
                    ></mwc-tab>
                    <mwc-tab
                      title="batch"
                      label="${y("session.Batch")}"
                      @click="${e=>this._showTab(e.target)}"
                    ></mwc-tab>
                    ${this.enableInferenceWorkload?_`
                            <mwc-tab
                              title="inference"
                              label="${y("session.Inference")}"
                              @click="${e=>this._showTab(e.target)}"
                            ></mwc-tab>
                          `:_``}
                    ${this.enableSFTPSession?_`
                            <mwc-tab
                              title="system"
                              label="${y("session.System")}"
                              @click="${e=>this._showTab(e.target)}"
                            ></mwc-tab>
                          `:_``}
                    <mwc-tab
                      title="finished"
                      label="${y("session.Finished")}"
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
                              class="horizontal layout start center export-csv"
                              @click="${()=>this._openExportToCsvDialog()}"
                            >
                              <mwc-icon
                                style="color:var(--token-colorTextSecondary);padding-right:10px;"
                              >
                                get_app
                              </mwc-icon>
                              ${y("session.exportCSV")}
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
                  ?allowNEOSessionLauncher="${!0}"
                ></backend-ai-session-launcher>
              </div>
            </h3>
            <div id="running-lists" class="tab-content">
              <backend-ai-session-list
                id="running-jobs"
                condition="running"
              ></backend-ai-session-list>
            </div>
            <div
              id="interactive-lists"
              class="tab-content"
              style="display:none;"
            >
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
      </div>
      <backend-ai-dialog id="export-to-csv" fixed backdrop>
        <span slot="title">${y("session.ExportSessionListToCSVFile")}</span>
        <div slot="content">
          <mwc-textfield
            id="export-file-name"
            label="File name"
            validationMessage="${y("data.explorer.ValueRequired")}"
            value="${"session_"+this._defaultFileName}"
            required
            style="margin-bottom:10px;"
          ></mwc-textfield>
        <div slot="footer" class="horizontal flex layout">
          <mwc-button
            unelevated
            fullwidth
            icon="get_app"
            label="${y("session.ExportCSVFile")}"
            class="export-csv"
            @click="${this._exportToCSV}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};r([c({type:String})],z.prototype,"_status",void 0),r([c({type:Boolean,reflect:!0})],z.prototype,"active",void 0),r([c({type:Boolean})],z.prototype,"is_admin",void 0),r([c({type:Boolean})],z.prototype,"enableInferenceWorkload",void 0),r([c({type:Boolean})],z.prototype,"enableSFTPSession",void 0),r([c({type:String})],z.prototype,"filterAccessKey",void 0),r([c({type:String})],z.prototype,"_connectionMode",void 0),r([c({type:Object})],z.prototype,"_defaultFileName",void 0),r([c({type:Object})],z.prototype,"resourceBroker",void 0),r([function(t){return(i,s)=>e(i,s,{get(){return(this.renderRoot??($??=document.createDocumentFragment())).querySelectorAll(t)}})}("backend-ai-session-list")],z.prototype,"sessionList",void 0),r([d("#running-jobs")],z.prototype,"runningJobs",void 0),r([d("#resource-monitor")],z.prototype,"resourceMonitor",void 0),r([d("#export-file-name")],z.prototype,"exportFileNameInput",void 0),r([d("#date-from")],z.prototype,"dateFromInput",void 0),r([d("#date-to")],z.prototype,"dateToInput",void 0),r([d("#dropdown-menu")],z.prototype,"dropdownMenu",void 0),r([d("#export-to-csv")],z.prototype,"exportToCsvDialog",void 0),z=M=r([p("backend-ai-session-view")],z);
