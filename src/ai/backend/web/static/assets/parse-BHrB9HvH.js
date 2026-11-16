import{t as e}from"./defineProperty-BbfpZ9Tg.js";import{i as t,n,t as r}from"./classPrivateFieldGet2-CB7J8LIR.js";
/*!
* Copyright (c) Squirrel Chat et al., All rights reserved.
* SPDX-License-Identifier: BSD-3-Clause
*
* Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are met:
*
* 1. Redistributions of source code must retain the above copyright notice, this
*    list of conditions and the following disclaimer.
* 2. Redistributions in binary form must reproduce the above copyright notice,
*    this list of conditions and the following disclaimer in the
*    documentation and/or other materials provided with the distribution.
* 3. Neither the name of the copyright holder nor the names of its contributors
*    may be used to endorse or promote products derived from this software without
*    specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
* ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
* FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
* DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
* SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
* CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
* OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
* OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/
var i=/^(\d{4}-\d{2}-\d{2})?[T ]?(?:(\d{2}):\d{2}(?::\d{2}(?:\.\d+)?)?)?(Z|[-+]\d{2}:\d{2})?$/i,a=new WeakMap,o=new WeakMap,s=new WeakMap,c=class e extends Date{constructor(e){let r=!0,c=!0,l=`Z`;if(typeof e==`string`){let t=e.match(i);t?(t[1]||(r=!1,e=`0000-01-01T${e}`),c=!!t[2],c&&e[10]===` `&&(e=e.replace(` `,`T`)),t[2]&&+t[2]>23?e=``:(l=t[3]||null,e=e.toUpperCase(),!l&&c&&(e+=`Z`))):e=``}super(e),t(this,a,!1),t(this,o,!1),t(this,s,null),isNaN(this.getTime())||(n(a,this,r),n(o,this,c),n(s,this,l))}isDateTime(){return r(a,this)&&r(o,this)}isLocal(){return!r(a,this)||!r(o,this)||!r(s,this)}isDate(){return r(a,this)&&!r(o,this)}isTime(){return r(o,this)&&!r(a,this)}isValid(){return r(a,this)||r(o,this)}toISOString(){let e=super.toISOString();if(this.isDate())return e.slice(0,10);if(this.isTime())return e.slice(11,23);if(r(s,this)===null)return e.slice(0,-1);if(r(s,this)===`Z`)return e;let t=r(s,this).slice(1,3)*60+ +r(s,this).slice(4,6);return t=r(s,this)[0]===`-`?t:-t,new Date(this.getTime()-t*6e4).toISOString().slice(0,-1)+r(s,this)}static wrapAsOffsetDateTime(t,r=`Z`){let i=new e(t);return n(s,i,r),i}static wrapAsLocalDateTime(t){let r=new e(t);return n(s,r,null),r}static wrapAsLocalDate(t){let r=new e(t);return n(o,r,!1),n(s,r,null),r}static wrapAsLocalTime(t){let r=new e(t);return n(a,r,!1),n(s,r,null),r}};
/*!
* Copyright (c) Squirrel Chat et al., All rights reserved.
* SPDX-License-Identifier: BSD-3-Clause
*
* Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are met:
*
* 1. Redistributions of source code must retain the above copyright notice, this
*    list of conditions and the following disclaimer.
* 2. Redistributions in binary form must reproduce the above copyright notice,
*    this list of conditions and the following disclaimer in the
*    documentation and/or other materials provided with the distribution.
* 3. Neither the name of the copyright holder nor the names of its contributors
*    may be used to endorse or promote products derived from this software without
*    specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
* ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
* FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
* DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
* SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
* CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
* OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
* OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/
function l(e,t){let n=e.slice(0,t).split(/\r\n|\n|\r/g);return[n.length,n.pop().length+1]}function u(e,t,n){let r=e.split(/\r\n|\n|\r/g),i=``,a=(Math.log10(t+1)|0)+1;for(let e=t-1;e<=t+1;e++){let o=r[e-1];o&&(i+=e.toString().padEnd(a,` `),i+=`:  `,i+=o,i+=`
`,e===t&&(i+=` `.repeat(a+n+2),i+=`^
`))}return i}var d=class extends Error{constructor(t,n){let[r,i]=l(n.toml,n.ptr),a=u(n.toml,r,i);super(`Invalid TOML document: ${t}\n\n${a}`,n),e(this,`line`,void 0),e(this,`column`,void 0),e(this,`codeblock`,void 0),this.line=r,this.column=i,this.codeblock=a}},f=/^((0x[0-9a-fA-F](_?[0-9a-fA-F])*)|(([+-]|0[ob])?\d(_?\d)*))$/,p=/^[+-]?\d(_?\d)*(\.\d(_?\d)*)?([eE][+-]?\d(_?\d)*)?$/,m=/^[+-]?0[0-9_]/
/*!
* Copyright (c) Squirrel Chat et al., All rights reserved.
* SPDX-License-Identifier: BSD-3-Clause
*
* Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are met:
*
* 1. Redistributions of source code must retain the above copyright notice, this
*    list of conditions and the following disclaimer.
* 2. Redistributions in binary form must reproduce the above copyright notice,
*    this list of conditions and the following disclaimer in the
*    documentation and/or other materials provided with the distribution.
* 3. Neither the name of the copyright holder nor the names of its contributors
*    may be used to endorse or promote products derived from this software without
*    specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
* ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
* FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
* DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
* SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
* CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
* OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
* OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/
;function h(e,t){let n=e[t++],r=n,i=n===`'`,a=n===e[t]&&n===e[t+1];a&&(e[t+=2]===`
`?t++:e[t]===`\r`&&e[t+1]===`
`&&(t+=2));let o=``,s=t,c=0;for(let l=t;l<e.length;l++)if(n=e[l],a&&(n===`
`||n===`\r`&&e[l+1]===`
`))c=c&&3;else if(n<` `&&n!==`	`||n===``)throw new d(`control characters are not allowed in strings`,{toml:e,ptr:l});else if((!c||c===3)&&n===r&&(!a||e[l+1]===r&&e[l+2]===r))return a&&(e[l+3]===r&&l++,e[l+3]===r&&l++),[c?o:o+e.slice(s,l),l+(a?3:1)];else if(!c)!i&&n===`\\`&&(o+=e.slice(s,s=l),c=1);else if(c===1){if(n===`x`||n===`u`||n===`U`){let t=0,r=n===`x`?2:n===`u`?4:8;for(let n=0;n<r;n++,l++){let n=e.charCodeAt(l+1),r=n>=48&&n<=57?n-48:n>=65&&n<=70?n-65+10:n>=97&&n<=102?n-97+10:-1;if(r<0)throw new d(`invalid non-hex character in unicode escape`,{toml:e,ptr:l+1});t=t<<4|r}if(t<0||t>1114111||t>=55296&&t<=57343)throw new d(`invalid unicode escape`,{toml:e,ptr:l});o+=String.fromCodePoint(t),s=l+1,c=0}else if(n===` `||n===`	`)c=2;else{if(n===`b`)o+=`\b`;else if(n===`t`)o+=`	`;else if(n===`n`)o+=`
`;else if(n===`f`)o+=`\f`;else if(n===`r`)o+=`\r`;else if(n===`e`)o+=`\x1B`;else if(n===`"`)o+=`"`;else if(n===`\\`)o+=`\\`;else throw new d(`unrecognized escape sequence`,{toml:e,ptr:l});s=l+1,c=0}}else if(n!==` `&&n!==`	`){if(c===2)throw new d(`invalid escape: only line-ending whitespace may be escaped`,{toml:e,ptr:s});c=+(!i&&n===`\\`),s=l}throw new d(`unfinished string`,{toml:e,ptr:t})}function g(e,t,n,r){if(e===`true`)return!0;if(e===`false`)return!1;if(e===`-inf`)return-1/0;if(e===`inf`||e===`+inf`)return 1/0;if(e===`nan`||e===`+nan`||e===`-nan`)return NaN;if(e===`-0`)return r?0n:0;let i=f.test(e);if(i||p.test(e)){if(m.test(e))throw new d(`leading zeroes are not allowed`,{toml:t,ptr:n});e=e.replace(/_/g,``);let a=+e;if(isNaN(a))throw new d(`invalid number`,{toml:t,ptr:n});if(i){if((i=!Number.isSafeInteger(a))&&!r)throw new d(`integer value cannot be represented losslessly`,{toml:t,ptr:n});(i||r===!0)&&(a=BigInt(e))}return a}let a=new c(e);if(!a.isValid())throw new d(`invalid value`,{toml:t,ptr:n});return a}
/*!
* Copyright (c) Squirrel Chat et al., All rights reserved.
* SPDX-License-Identifier: BSD-3-Clause
*
* Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are met:
*
* 1. Redistributions of source code must retain the above copyright notice, this
*    list of conditions and the following disclaimer.
* 2. Redistributions in binary form must reproduce the above copyright notice,
*    this list of conditions and the following disclaimer in the
*    documentation and/or other materials provided with the distribution.
* 3. Neither the name of the copyright holder nor the names of its contributors
*    may be used to endorse or promote products derived from this software without
*    specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
* ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
* FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
* DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
* SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
* CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
* OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
* OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/
function _(e,t=0,n=e.length){let r=e.indexOf(`
`,t);return e[r-1]===`\r`&&r--,r<=n?r:-1}function v(e,t){for(let n=t;n<e.length;n++){let r=e[n];if(r===`
`)return n;if(r===`\r`&&e[n+1]===`
`)return n+1;if(r<` `&&r!==`	`||r===``)throw new d(`control characters are not allowed in comments`,{toml:e,ptr:t})}return e.length}function y(e,t,n,r){let i;for(;;){for(;(i=e[t])===` `||i===`	`||!n&&(i===`
`||i===`\r`&&e[t+1]===`
`);)t++;if(r||i!==`#`)break;t=v(e,t)}return t}function b(e,t,n,r,i=!1){if(!r)return t=_(e,t),t<0?e.length:t;for(let a=t;a<e.length;a++){let t=e[a];if(t===`#`){if(a=_(e,a),a<0)break}else if(t===n)return a+1;else if(t===r||i&&(t===`
`||t===`\r`&&e[a+1]===`
`))return a}throw new d(`cannot find end of structure`,{toml:e,ptr:t})}
/*!
* Copyright (c) Squirrel Chat et al., All rights reserved.
* SPDX-License-Identifier: BSD-3-Clause
*
* Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are met:
*
* 1. Redistributions of source code must retain the above copyright notice, this
*    list of conditions and the following disclaimer.
* 2. Redistributions in binary form must reproduce the above copyright notice,
*    this list of conditions and the following disclaimer in the
*    documentation and/or other materials provided with the distribution.
* 3. Neither the name of the copyright holder nor the names of its contributors
*    may be used to endorse or promote products derived from this software without
*    specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
* ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
* FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
* DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
* SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
* CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
* OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
* OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/
function x(e,t,n){let r=e.slice(t,n),i=r.indexOf(`#`);return i>-1&&(v(e,i),r=r.slice(0,i)),[r.trimEnd(),i]}function S(e,t,n,r,i){if(r===0)throw new d(`document contains excessively nested structures. aborting.`,{toml:e,ptr:t});let a=e[t];if(a===`[`||a===`{`){let[o,s]=a===`[`?E(e,t,r,i):T(e,t,r,i);if(n){if(s=y(e,s),e[s]===`,`)s++;else if(e[s]!==n)throw new d(`expected comma or end of structure`,{toml:e,ptr:s})}return[o,s]}if(a===`"`||a===`'`){let[r,i]=h(e,t);if(n){if(i=y(e,i),e[i]&&e[i]!==`,`&&e[i]!==n&&e[i]!==`
`&&e[i]!==`\r`)throw new d(`unexpected character encountered`,{toml:e,ptr:i});e[i]===`,`&&i++}return[r,i]}let o=b(e,t,`,`,n),s=x(e,t,o-+(e[o-1]===`,`));if(!s[0])throw new d(`incomplete key-value declaration: no value specified`,{toml:e,ptr:t});return n&&s[1]>-1&&(o=y(e,t+s[1]),e[o]===`,`&&o++),[g(s[0],e,t,i),o]}
/*!
* Copyright (c) Squirrel Chat et al., All rights reserved.
* SPDX-License-Identifier: BSD-3-Clause
*
* Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are met:
*
* 1. Redistributions of source code must retain the above copyright notice, this
*    list of conditions and the following disclaimer.
* 2. Redistributions in binary form must reproduce the above copyright notice,
*    this list of conditions and the following disclaimer in the
*    documentation and/or other materials provided with the distribution.
* 3. Neither the name of the copyright holder nor the names of its contributors
*    may be used to endorse or promote products derived from this software without
*    specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
* ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
* FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
* DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
* SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
* CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
* OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
* OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/
var C=/^[a-zA-Z0-9-_]+[ \t]*$/;function w(e,t,n=`=`){let r=t-1,i=[],a=e.indexOf(n,t);if(a<0)throw new d(`incomplete key-value: cannot find end of key`,{toml:e,ptr:t});do{let o=e[t=++r];if(o!==` `&&o!==`	`){if(o===`"`||o===`'`){if(o===e[t+1]&&o===e[t+2])throw new d(`multiline strings are not allowed in keys`,{toml:e,ptr:t});let[s,c]=h(e,t);r=e.indexOf(`.`,c);let l=e.slice(c,r<0||r>a?a:r),u=_(l);if(u>-1)throw new d(`newlines are not allowed in keys`,{toml:e,ptr:t+r+u});if(l.trimStart())throw new d(`found extra tokens after the string part`,{toml:e,ptr:c});if(a<c&&(a=e.indexOf(n,c),a<0))throw new d(`incomplete key-value: cannot find end of key`,{toml:e,ptr:t});i.push(s)}else{r=e.indexOf(`.`,t);let n=e.slice(t,r<0||r>a?a:r);if(!C.test(n))throw new d(`only letter, numbers, dashes and underscores are allowed in keys`,{toml:e,ptr:t});i.push(n.trimEnd())}}}while(r+1&&r<a);return[i,y(e,a+1,!0,!0)]}function T(e,t,n,r){let i={},a=new Set,o;for(t++;(o=e[t++])!==`}`&&o;)if(o===`,`)throw new d(`expected value, found comma`,{toml:e,ptr:t-1});else if(o===`#`)t=v(e,t);else if(o!==` `&&o!==`	`&&o!==`
`&&o!==`\r`){let o,s=i,c=!1,[l,u]=w(e,t-1);for(let n=0;n<l.length;n++){if(n&&(s=c?s[o]:s[o]={}),o=l[n],(c=Object.hasOwn(s,o))&&(typeof s[o]!=`object`||a.has(s[o])))throw new d(`trying to redefine an already defined value`,{toml:e,ptr:t});!c&&o===`__proto__`&&Object.defineProperty(s,o,{enumerable:!0,configurable:!0,writable:!0})}if(c)throw new d(`trying to redefine an already defined value`,{toml:e,ptr:t});let[f,p]=S(e,u,`}`,n-1,r);a.add(f),s[o]=f,t=p}if(!o)throw new d(`unfinished table encountered`,{toml:e,ptr:t});return[i,t]}function E(e,t,n,r){let i=[],a;for(t++;(a=e[t++])!==`]`&&a;)if(a===`,`)throw new d(`expected value, found comma`,{toml:e,ptr:t-1});else if(a===`#`)t=v(e,t);else if(a!==` `&&a!==`	`&&a!==`
`&&a!==`\r`){let a=S(e,t-1,`]`,n-1,r);i.push(a[0]),t=a[1]}if(!a)throw new d(`unfinished array encountered`,{toml:e,ptr:t});return[i,t]}
/*!
* Copyright (c) Squirrel Chat et al., All rights reserved.
* SPDX-License-Identifier: BSD-3-Clause
*
* Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are met:
*
* 1. Redistributions of source code must retain the above copyright notice, this
*    list of conditions and the following disclaimer.
* 2. Redistributions in binary form must reproduce the above copyright notice,
*    this list of conditions and the following disclaimer in the
*    documentation and/or other materials provided with the distribution.
* 3. Neither the name of the copyright holder nor the names of its contributors
*    may be used to endorse or promote products derived from this software without
*    specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
* ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
* FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
* DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
* SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
* CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
* OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
* OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/
function D(e,t,n,r){let i=t,a=n,o,s=!1,c;for(let t=0;t<e.length;t++){var l,u;if(t){if(i=s?i[o]:i[o]={},a=(c=a[o]).c,r===0&&(c.t===1||c.t===2))return null;if(c.t===2){let e=i.length-1;i=i[e],a=a[e].c}}if(o=e[t],(s=Object.hasOwn(i,o))&&((l=a[o])==null?void 0:l.t)===0&&(u=a[o])!=null&&u.d)return null;s||(o===`__proto__`&&(Object.defineProperty(i,o,{enumerable:!0,configurable:!0,writable:!0}),Object.defineProperty(a,o,{enumerable:!0,configurable:!0,writable:!0})),a[o]={t:t<e.length-1&&r===2?3:r,d:!1,i:0,c:{}})}if(c=a[o],c.t!==r&&(r!==1||c.t!==3)||(r===2&&(c.d||(c.d=!0,i[o]=[]),i[o].push(i={}),c.c[c.i++]=c={t:1,d:!1,i:0,c:{}}),c.d))return null;if(c.d=!0,r===1)i=s?i[o]:i[o]={};else if(r===0&&s)return null;return[o,i,c.c]}function O(e,{maxDepth:t=1e3,integersAsBigInt:n}={}){let r={},i={},a=r,o=i;for(let s=y(e,0);s<e.length;){if(e[s]===`[`){let t=e[++s]===`[`,n=w(e,s+=+t,`]`);if(t){if(e[n[1]-1]!==`]`)throw new d(`expected end of table declaration`,{toml:e,ptr:n[1]-1});n[1]++}let c=D(n[0],r,i,t?2:1);if(!c)throw new d(`trying to redefine an already defined table or value`,{toml:e,ptr:s});o=c[2],a=c[1],s=n[1]}else{let r=w(e,s),i=D(r[0],a,o,0);if(!i)throw new d(`trying to redefine an already defined table or value`,{toml:e,ptr:s});let c=S(e,r[1],void 0,t,n);i[1][i[0]]=c[0],s=c[1]}if(s=y(e,s,!0),e[s]&&e[s]!==`
`&&e[s]!==`\r`)throw new d(`each key-value declaration must be followed by an end-of-line`,{toml:e,ptr:s});s=y(e,s)}return r}export{O as t};
