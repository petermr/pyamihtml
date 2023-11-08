;if(CloudflareApps.matchPage(CloudflareApps.installs['bqF6zvcO85Mp'].URLPatterns)){(function(modules){var installedModules={};function __webpack_require__(moduleId){if(installedModules[moduleId]){return installedModules[moduleId].exports;}
var module=installedModules[moduleId]={i:moduleId,l:false,exports:{}};modules[moduleId].call(module.exports,module,module.exports,__webpack_require__);module.l=true;return module.exports;}
__webpack_require__.m=modules;__webpack_require__.c=installedModules;__webpack_require__.i=function(value){return value;};__webpack_require__.d=function(exports,name,getter){if(!__webpack_require__.o(exports,name)){Object.defineProperty(exports,name,{configurable:false,enumerable:true,get:getter});}};__webpack_require__.n=function(module){var getter=module&&module.__esModule?function getDefault(){return module['default'];}:function getModuleExports(){return module;};__webpack_require__.d(getter,'a',getter);return getter;};__webpack_require__.o=function(object,property){return Object.prototype.hasOwnProperty.call(object,property);};__webpack_require__.p="";return __webpack_require__(__webpack_require__.s=5);})
([(function(module,exports,__webpack_require__){var pSlice=Array.prototype.slice;var objectKeys=__webpack_require__(3);var isArguments=__webpack_require__(2);var deepEqual=module.exports=function(actual,expected,opts){if(!opts)opts={};if(actual===expected){return true;}else if(actual instanceof Date&&expected instanceof Date){return actual.getTime()===expected.getTime();}else if(!actual||!expected||typeof actual!='object'&&typeof expected!='object'){return opts.strict?actual===expected:actual==expected;}else{return objEquiv(actual,expected,opts);}}
function isUndefinedOrNull(value){return value===null||value===undefined;}
function isBuffer(x){if(!x||typeof x!=='object'||typeof x.length!=='number')return false;if(typeof x.copy!=='function'||typeof x.slice!=='function'){return false;}
if(x.length>0&&typeof x[0]!=='number')return false;return true;}
function objEquiv(a,b,opts){var i,key;if(isUndefinedOrNull(a)||isUndefinedOrNull(b))
return false;if(a.prototype!==b.prototype)return false;if(isArguments(a)){if(!isArguments(b)){return false;}
a=pSlice.call(a);b=pSlice.call(b);return deepEqual(a,b,opts);}
if(isBuffer(a)){if(!isBuffer(b)){return false;}
if(a.length!==b.length)return false;for(i=0;i<a.length;i++){if(a[i]!==b[i])return false;}
return true;}
try{var ka=objectKeys(a),kb=objectKeys(b);}catch(e){return false;}
if(ka.length!=kb.length)
return false;ka.sort();kb.sort();for(i=ka.length-1;i>=0;i--){if(ka[i]!=kb[i])
return false;}
for(i=ka.length-1;i>=0;i--){key=ka[i];if(!deepEqual(a[key],b[key],opts))return false;}
return typeof a===typeof b;}}),(function(module,exports,__webpack_require__){"use strict";Object.defineProperty(exports,'__esModule',{value:true})
exports.default=stringToHash
function stringToHash(){var string=arguments.length>0&&arguments[0]!==undefined?arguments[0]:''
var hash=0
if(string.length===0)return hash
for(var i=0;i<string.length;i++){var chr=string.charCodeAt(i)
hash=(hash<<5)-hash+chr
hash|=0}
return hash}}),(function(module,exports){var supportsArgumentsClass=(function(){return Object.prototype.toString.call(arguments)})()=='[object Arguments]';exports=module.exports=supportsArgumentsClass?supported:unsupported;exports.supported=supported;function supported(object){return Object.prototype.toString.call(object)=='[object Arguments]';};exports.unsupported=unsupported;function unsupported(object){return object&&typeof object=='object'&&typeof object.length=='number'&&Object.prototype.hasOwnProperty.call(object,'callee')&&!Object.prototype.propertyIsEnumerable.call(object,'callee')||false;};}),(function(module,exports){exports=module.exports=typeof Object.keys==='function'?Object.keys:shim;exports.shim=shim;function shim(obj){var keys=[];for(var key in obj)keys.push(key);return keys;}}),,(function(module,exports,__webpack_require__){"use strict";var _deepEqual=__webpack_require__(0)
var _deepEqual2=_interopRequireDefault(_deepEqual)
var _stringToHash=__webpack_require__(1)
var _stringToHash2=_interopRequireDefault(_stringToHash)
function _interopRequireDefault(obj){return obj&&obj.__esModule?obj:{default:obj}}
(function(){'use strict'
if(!window.addEventListener)return
var hash=void 0
var options=CloudflareApps.installs['bqF6zvcO85Mp'].options
var product=CloudflareApps.installs['bqF6zvcO85Mp'].product
var localStorage=window.localStorage||{}
var previewMessageIndex=0
var LOCAL_STORAGE_PREFIX='cf-welcome-bar-hashes-seen-'
var VISIBILITY_ATTRIBUTE='data-cf-welcome-bar-visibility'
var DAY_DURATION=172800000
var documentElementOriginallyPositionStatic=window.getComputedStyle(document.documentElement).position==='static'
var element=document.createElement('cloudflare-app')
element.setAttribute('app','welcome-bar')
var htmlStyle=document.createElement('style')
document.head.appendChild(htmlStyle)
var elementStyle=document.createElement('style')
document.head.appendChild(elementStyle)
function getMaxZIndex(){var max=0
var elements=document.getElementsByTagName('*')
Array.prototype.slice.call(elements).forEach(function(element){var zIndex=parseInt(document.defaultView.getComputedStyle(element).zIndex,10)
max=zIndex?Math.max(max,zIndex):max})
return max}
function setPageStyles(){setHTMLStyle()
setFixedElementStyles()}
function setHTMLStyle(){if(!document.body)return
var style=''
if(documentElementOriginallyPositionStatic&&isShown()){style='\n        html {\n          position: relative;\n          top: '+element.clientHeight+'px;\n        }\n      '}
htmlStyle.innerHTML=style}
function setFixedElementStyles(){function removeTopStyle(node){var currentStyle=node.getAttribute('style')
if(!currentStyle)return
node.setAttribute('style',currentStyle.replace(/top[^]+?/g,''))}
var elementHeight=element.clientHeight
var allNodes=document.querySelectorAll('*:not([app="welcome-bar"]):not([data-cfapps-welcome-bar-adjusted-fixed-element-original-top])')
Array.prototype.forEach.call(allNodes,function(node){var computedStyle=window.getComputedStyle(node)
var boundingClientRect=node.getBoundingClientRect()
var isSticky=computedStyle.position==='sticky'
var isFixed=computedStyle.position==='fixed'
var isBottomFixed=computedStyle.bottom==='0px'&&boundingClientRect.bottom===window.innerHeight&&boundingClientRect.top>=elementHeight
if("bqF6zvcO85Mp"==='preview'&&node.nodeName==='IFRAME'&&node.src.indexOf('https://embedded.cloudflareapps.com')!==-1){return}
if((isFixed||isSticky)&&!isBottomFixed){var top=boundingClientRect.top
var styleTop=parseInt(computedStyle.top,10)
if(isSticky||top===styleTop&&top<=elementHeight){node.setAttribute('data-cfapps-welcome-bar-adjusted-fixed-element-original-top',top)}}})
var adjustedNodes=document.querySelectorAll('[data-cfapps-welcome-bar-adjusted-fixed-element-original-top]')
Array.prototype.forEach.call(adjustedNodes,function(node){removeTopStyle(node)
var computedStyle=window.getComputedStyle(node)
var isFixedOrSticky=computedStyle.position==='fixed'||computedStyle.position==='sticky'
if(isFixedOrSticky&&isShown()&&elementHeight>0){var newTop=(parseInt(computedStyle.top,10)||0)+elementHeight
node.style.top=newTop+'px'}})}
function isShown(){return document.documentElement.getAttribute(VISIBILITY_ATTRIBUTE)==='visible'}
function cleanUpExpiredHashes(){var weekAgo=Date.now()-DAY_DURATION*7
Object.keys(localStorage).filter(function(key){return key.startsWith(LOCAL_STORAGE_PREFIX)}).filter(function(key){return weekAgo>localStorage[key]}).forEach(function(key){return delete localStorage[key]})}
function getLocalStorageKey(){return LOCAL_STORAGE_PREFIX+hash}
function hideWelcomeBar(){var _ref=arguments.length>0&&arguments[0]!==undefined?arguments[0]:{persist:false},persist=_ref.persist
document.documentElement.setAttribute(VISIBILITY_ATTRIBUTE,'hidden')
element.removeAttribute('data-slide-animation')
if(persist){try{localStorage[getLocalStorageKey()]=Date.now()}catch(e){}}
setPageStyles()}
var hideWelcomeBarPersist=hideWelcomeBar.bind(null,{persist:true})
function cancelAnimation(){element.removeEventListener('transitionend',hideWelcomeBar)
element.removeAttribute('data-slide-animation')}
function updateAnimation(){if(!options.behavior.automaticallyHide){cancelAnimation()
return}
element.addEventListener('transitionend',hideWelcomeBar)
element.addEventListener('mouseover',cancelAnimation)
element.addEventListener('click',cancelAnimation)
window.requestAnimationFrame(function(){element.setAttribute('data-slide-animation','')
window.requestAnimationFrame(function(){element.setAttribute('data-slide-animation','complete')})})}
function updateElementStyle(){elementStyle.innerHTML='\n      cloudflare-app[app="welcome-bar"] {\n        background-color: '+options.theme.backgroundColor+';\n        color: '+options.theme.textColor+';\n      }\n\n      @media (max-width: 768px) {\n        cloudflare-app[app="welcome-bar"][data-style="prominent"] .alert-cta-button,\n        cloudflare-app[app="welcome-bar"][data-style="prominent"] .alert-cta-button:hover,\n        cloudflare-app[app="welcome-bar"][data-style="prominent"] .alert-cta-button:active {\n          color: '+options.theme.textColor+';\n        }\n      }\n\n      @media (min-width: 768px) {\n        cloudflare-app[app="welcome-bar"][data-style="prominent"] .alert-cta-button,\n        cloudflare-app[app="welcome-bar"][data-style="prominent"] .alert-cta-button:hover,\n        cloudflare-app[app="welcome-bar"][data-style="prominent"] .alert-cta-button:active {\n          background-color: '+options.theme.buttonBackgroundColor+' !important;\n          color: '+(options.theme.buttonTextColorStrategy==='auto'?options.theme.backgroundColor:options.theme.buttonTextColor)+' !important;\n        }\n      }\n    '
element.setAttribute('data-style',options.theme.style)}
function hasSeenHash(){var foundHash=false
try{foundHash=!!localStorage[getLocalStorageKey()]}catch(e){}
return foundHash}
function updateElement(){var isPro=product&&product.id==='pro'
var message=void 0,cta=void 0
var shouldShow=true
if(!options.messagePlan||options.messagePlan==='single'){var _options=options
message=_options.message
cta=_options.cta}else if(!options.messages.length){shouldShow=false}else{var messageIndex=void 0
if("bqF6zvcO85Mp"==='preview'){messageIndex=previewMessageIndex}else{messageIndex=Math.floor(Math.random()*options.messages.length)}
if(!options.messages.length)return
var entry=options.messages[messageIndex];message=entry.message
cta=entry.cta
if(isPro&&entry.useEndDate){var endDate=new Date(entry.endDate)
var now=new Date()
shouldShow=endDate<now}}
hash=(0,_stringToHash2.default)(message)
if("bqF6zvcO85Mp"!=='preview'&&(!shouldShow||hasSeenHash())){hideWelcomeBar()
return}
updateElementStyle()
element.innerHTML=''
element.style.zIndex=getMaxZIndex()+1
var messageContainer=document.createElement('alert-message')
var messageContent=document.createElement('alert-message-content')
messageContent.textContent=(message||'').trim()||'We just launched an amazing new product!'
messageContent.innerHTML=messageContent.innerHTML.replace(/\n/g,'<br />')
messageContainer.appendChild(messageContent)
if(cta.show){var ctaButton=document.createElement('a')
ctaButton.className='alert-cta-button'
ctaButton.textContent=(cta.label||'').trim()||'More info'
if(cta.newWindow)ctaButton.target='_blank'
if(cta.url)ctaButton.href=cta.url
messageContent.appendChild(ctaButton)}
element.appendChild(messageContainer)
if(options.behavior.showCloseButton){var dismissButton=document.createElement('alert-dismiss')
dismissButton.setAttribute('role','button')
dismissButton.textContent='×'
dismissButton.addEventListener('click',hideWelcomeBarPersist)
element.appendChild(dismissButton)}
document.documentElement.setAttribute(VISIBILITY_ATTRIBUTE,'visible')
updateAnimation()}
function bootstrap(){cleanUpExpiredHashes()
document.body.appendChild(element)
updateElement()
window.requestAnimationFrame(setPageStyles)
window.addEventListener('resize',setPageStyles)}
window.CloudflareApps.installs['bqF6zvcO85Mp'].scope={updateOptions:function updateOptions(nextOptions){if(nextOptions.messages.length!==options.messages.length){previewMessageIndex=nextOptions.messages.length-1}else{for(var i=0;i<nextOptions.messages.length;i++){var oldEntry=options.messages[i]
var nextEntry=nextOptions.messages[i]
if(!(0,_deepEqual2.default)(nextEntry,oldEntry)){previewMessageIndex=i
break}}}
options=nextOptions
updateElement()
setPageStyles()},updateProduct:function updateProduct(nextProduct){product=nextProduct
updateElement()
setPageStyles()},updateTheme:function updateTheme(nextOptions){var themeStyleChanged=nextOptions.theme.style!==options.theme.style
options=nextOptions
updateElementStyle()
if(themeStyleChanged)setPageStyles()
if(!isShown()){document.documentElement.setAttribute(VISIBILITY_ATTRIBUTE,'visible')}}}
if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',bootstrap)}else{bootstrap()}})()})]);};(function(){try{var link=document.createElement('link');link.rel='stylesheet';link.href='data:text/css;charset=utf-8;base64,LyoKICBTcGVjaWZpY2l0eSB0byBjb21iYXQgdGhpbmdzIGxpa2UgdGhpcyAoZnJvbSBDTk4uY29tIGFzIG9mIDYvNi8xNik6CgogIGJvZHkgPiA6bm90KC5uYXYpIHsKICAgIC13ZWJraXQtdHJhbnNmb3JtOiBub25lICFpbXBvcnRhbnQ7CiAgICB0cmFuc2Zvcm06IG5vbmUgIWltcG9ydGFudDsKICB9CiovCmh0bWwgPiBib2R5ID4gY2xvdWRmbGFyZS1hcHBbYXBwPSJ3ZWxjb21lLWJhciJdIHsKICBkaXNwbGF5OiBibG9jazsKICBkaXNwbGF5OiAtd2Via2l0LWJveDsKICBkaXNwbGF5OiAtbXMtZmxleGJveDsKICBkaXNwbGF5OiBmbGV4OwogIC13ZWJraXQtYm94LWFsaWduOiBjZW50ZXI7CiAgICAgIC1tcy1mbGV4LWFsaWduOiBjZW50ZXI7CiAgICAgICAgICBhbGlnbi1pdGVtczogY2VudGVyOwogIC13ZWJraXQtYm94LXBhY2s6IGp1c3RpZnk7CiAgICAgIC1tcy1mbGV4LXBhY2s6IGp1c3RpZnk7CiAgICAgICAgICBqdXN0aWZ5LWNvbnRlbnQ6IHNwYWNlLWJldHdlZW47CiAgZm9udC1zaXplOiAxNnB4OwogIG1pbi1oZWlnaHQ6IDIuNWVtOwogIGxpbmUtaGVpZ2h0OiAxOwogIG92ZXJmbG93OiBoaWRkZW47CiAgcG9zaXRpb246IGZpeGVkOwogIHRvcDogMDsKICBsZWZ0OiAwOwogIHJpZ2h0OiAwOwogIC13ZWJraXQtZm9udC1zbW9vdGhpbmc6IGFudGlhbGlhc2VkOwogIC1tb3otb3N4LWZvbnQtc21vb3RoaW5nOiBncmF5c2NhbGU7CiAgLXdlYmtpdC11c2VyLXNlbGVjdDogbm9uZTsKICAtd2Via2l0LXRyYW5zZm9ybTogdHJhbnNsYXRlM2QoMCwgLTMwMCUsIDApOwogICAgICAgICAgdHJhbnNmb3JtOiB0cmFuc2xhdGUzZCgwLCAtMzAwJSwgMCk7Cn0KCmh0bWwgPiBib2R5ID4gY2xvdWRmbGFyZS1hcHBbYXBwPSJ3ZWxjb21lLWJhciJdOjpiZWZvcmUgewogIGNvbnRlbnQ6ICIiOwogIHBvc2l0aW9uOiBhYnNvbHV0ZTsKICB0b3A6IDA7CiAgbGVmdDogMDsKICByaWdodDogMDsKICBib3R0b206IDA7CiAgYmFja2dyb3VuZDogcmdiYSgwLCAwLCAwLCAuMDUpOwogIC13ZWJraXQtdHJhbnNmb3JtOiB0cmFuc2xhdGUzZCgtMTAwJSwgMCwgMCk7CiAgICAgICAgICB0cmFuc2Zvcm06IHRyYW5zbGF0ZTNkKC0xMDAlLCAwLCAwKTsKfQoKaHRtbCA+IGJvZHkgPiBjbG91ZGZsYXJlLWFwcFthcHA9IndlbGNvbWUtYmFyIl1bZGF0YS1zbGlkZS1hbmltYXRpb25dOjpiZWZvcmUgewogIHRyYW5zaXRpb246IC13ZWJraXQtdHJhbnNmb3JtIGVhc2Utb3V0IDhzOwogIHRyYW5zaXRpb246IHRyYW5zZm9ybSBlYXNlLW91dCA4czsKICB0cmFuc2l0aW9uOiB0cmFuc2Zvcm0gZWFzZS1vdXQgOHMsIC13ZWJraXQtdHJhbnNmb3JtIGVhc2Utb3V0IDhzOwp9CgpodG1sID4gYm9keSA+IGNsb3VkZmxhcmUtYXBwW2FwcD0id2VsY29tZS1iYXIiXVtkYXRhLXNsaWRlLWFuaW1hdGlvbj0iY29tcGxldGUiXTo6YmVmb3JlIHsKICAtd2Via2l0LXRyYW5zZm9ybTogdHJhbnNsYXRlM2QoMCwgMCwgMCk7CiAgICAgICAgICB0cmFuc2Zvcm06IHRyYW5zbGF0ZTNkKDAsIDAsIDApOwp9CgpodG1sW2RhdGEtY2Ytd2VsY29tZS1iYXItdmlzaWJpbGl0eT0idmlzaWJsZSJdID4gYm9keSA+IGNsb3VkZmxhcmUtYXBwW2FwcD0id2VsY29tZS1iYXIiXSB7CiAgLXdlYmtpdC10cmFuc2Zvcm06IHRyYW5zbGF0ZTNkKDAsIDAsIDApICFpbXBvcnRhbnQ7CiAgICAgICAgICB0cmFuc2Zvcm06IHRyYW5zbGF0ZTNkKDAsIDAsIDApICFpbXBvcnRhbnQ7Cn0KCmNsb3VkZmxhcmUtYXBwW2FwcD0id2VsY29tZS1iYXIiXSBhbGVydC1tZXNzYWdlIHsKICBkaXNwbGF5OiAtd2Via2l0LWJveDsKICBkaXNwbGF5OiAtbXMtZmxleGJveDsKICBkaXNwbGF5OiBmbGV4OwogIC13ZWJraXQtYm94LWZsZXg6IDE7CiAgICAgIC1tcy1mbGV4OiAxIDEgYXV0bzsKICAgICAgICAgIGZsZXg6IDEgMSBhdXRvOwogIC13ZWJraXQtYm94LXBhY2s6IGNlbnRlcjsKICAgICAgLW1zLWZsZXgtcGFjazogY2VudGVyOwogICAgICAgICAganVzdGlmeS1jb250ZW50OiBjZW50ZXI7Cn0KCmNsb3VkZmxhcmUtYXBwW2FwcD0id2VsY29tZS1iYXIiXSBhbGVydC1tZXNzYWdlLWNvbnRlbnQgewogIGRpc3BsYXk6IC13ZWJraXQtYm94OwogIGRpc3BsYXk6IC1tcy1mbGV4Ym94OwogIGRpc3BsYXk6IGZsZXg7CiAgLXdlYmtpdC1ib3gtYWxpZ246IGNlbnRlcjsKICAgICAgLW1zLWZsZXgtYWxpZ246IGNlbnRlcjsKICAgICAgICAgIGFsaWduLWl0ZW1zOiBjZW50ZXI7CiAgZm9udC1zaXplOiAxLjFlbTsKICBsaW5lLWhlaWdodDogMS4yOwogIGZvbnQtd2VpZ2h0OiA1MDA7CiAgbWF4LXdpZHRoOiA3MDBweDsKfQoKQGZvbnQtZmFjZSB7CiAgZm9udC1mYW1pbHk6ICJjZmFwcHMtd2VsY29tZS1iYXItaWNvbnMiOwogIGZvbnQtc3R5bGU6IG5vcm1hbDsKICBmb250LXdlaWdodDogbm9ybWFsOwogIHNyYzogdXJsKGRhdGE6YXBwbGljYXRpb24veC1mb250LXdvZmY7Y2hhcnNldD11dGYtODtiYXNlNjQsZDA5R1JrOVVWRThBQUFPZ0FBb0FBQUFBQlh3QUFRQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUJEUmtZZ0FBQUE5QUFBQU1BQUFBRFJLamNwVDBaR1ZFMEFBQUcwQUFBQUdnQUFBQnh6Q2MyZVQxTXZNZ0FBQWRBQUFBQklBQUFBWUlES0JTbGpiV0Z3QUFBQ0dBQUFBRGNBQUFGQ0FBMGk0V2hsWVdRQUFBSlFBQUFBTHdBQUFEWUR0dFlXYUdobFlRQUFBb0FBQUFBZ0FBQUFKQWF0QWVob2JYUjRBQUFDb0FBQUFBZ0FBQUFJQS9vQUFHMWhlSEFBQUFLb0FBQUFCZ0FBQUFZQUFsQUFibUZ0WlFBQUFyQUFBQURZQUFBQnNFbkJCMXB3YjNOMEFBQURpQUFBQUJZQUFBQWcvNTBBWjNpY1kyUmdZV0ZnWkdUa1NVMU1UeTNTelV6T3p5dG1ZR1JpWUdSdy9DSEQ5RU9XK1ljRVN3OFBZd1FQODBjZUZqa3VCcFlPRGZudWJqaURoNzI3NU1la1h4MnNNZ3hkL0RJTURBSXlETDJDTWd3Y01nd25oUmlZUWNid01rZ3dLQmRscG1lVUpHZWtsaFhsNXlGWmhHd25Bd05qT3dNVEk2T0NlZmZIWHp3ZkdUOSsvUENSK2FQWTk2Ty9idncreXZieFg1SG9MNTRQLzNqWStYNU0rdEVpK2lmOHg0eUFpQjlhZjFML0FQR3hVRmErSHhORnVrVzdlYmdBT2taR28zaWNZMkJnWUdRQWdnc0ZEb2tnK3FMUHNYa3dHZ0JFWWdibEFBQjRuR05nWnZ6TE9JR0JsWUdEMVpoMUpnTURveHlFWnI3T2tNWWt4QUFFckF3UTBNQ0FDZ0xTWEZNWUhCU3NGS3pZMHY2bE1leGcvc0lnRGhSbWhDdFFBRUpHQUVROUMyOTRuR05nWUdCbWdHQVpCa1lHRUxBQjhoakJmQllHQlNETkFvUkF2b0xWLy84UTh2NXhxRW9HUmpZR0dITjRBaUk4QndDWTRnY05BSGljWTJCa1lHQUE0aTNQNzJySDg5dDhaZURtWUFDQml6N0g1aUhvL3k4Wi96Ri9BWEk1R0poQW9nQnFkdzFDQUhpY1kyQmtZR0QrOHY4bHd3N0d2d3dNLy84ei9tTUFpcUFBSmdEQWh3ZVhBZjBBQUFIOUFBQUFBRkFBQUFJQUFIaWNqWSs5RGNJd0VJVmZJRUhpUjVTSTBnVVNsU003QWdvR29LU2tSOGlLMHNTU3d3eU13QmlNd1FDTXdRRFVQSnNyS0Npd2RQWjNkKzkrREdDQ0t6TEVrMkdNdVhBUEJZeHdIMHRjaEhOcTdzSUYrU2s4d0RpYlVwbmxRMFptcVNweUR5TXNoUHZZWXlPY1UzTVRMc2dQNFFINUJZY2phdDRCR2cxTzhHalJBZTVZdTZDYmsyL3BmTVVsc2t2K09iMGgxU3RVS1BrUGhTM3RkOWRQemxLbHNhSlZKSXMxMi9uMnZQT2hkcW9xamRxcXIrbjByTkVyWFJsTDRUL2JIbEsrWXo1bTQ3eTRGdzR1ZEkxdmxTM05YMzNlRWhCRE1uaWNZMkJtQUlQL3N4alNnQlFqQXhvQUFDNnFBZ1FBQUE9PSkgZm9ybWF0KCJ3b2ZmIik7Cn0KCmNsb3VkZmxhcmUtYXBwW2FwcD0id2VsY29tZS1iYXIiXSAuYWxlcnQtY3RhLWJ1dHRvbiB7CiAgZGlzcGxheTogLXdlYmtpdC1ib3ggIWltcG9ydGFudDsKICBkaXNwbGF5OiAtbXMtZmxleGJveCAhaW1wb3J0YW50OwogIGRpc3BsYXk6IGZsZXggIWltcG9ydGFudDsKICAtd2Via2l0LWJveC1hbGlnbjogY2VudGVyICFpbXBvcnRhbnQ7CiAgICAgIC1tcy1mbGV4LWFsaWduOiBjZW50ZXIgIWltcG9ydGFudDsKICAgICAgICAgIGFsaWduLWl0ZW1zOiBjZW50ZXIgIWltcG9ydGFudDsKICBib3JkZXI6IDAgIWltcG9ydGFudDsKICBib3gtc2hhZG93OiBub25lICFpbXBvcnRhbnQ7CiAgY3Vyc29yOiBwb2ludGVyICFpbXBvcnRhbnQ7CiAgZGlzcGxheTogaW5saW5lLWJsb2NrICFpbXBvcnRhbnQ7CiAgLXdlYmtpdC1ib3gtZmxleDogMCAhaW1wb3J0YW50OwogICAgICAtbXMtZmxleDogMCAwIGF1dG8gIWltcG9ydGFudDsKICAgICAgICAgIGZsZXg6IDAgMCBhdXRvICFpbXBvcnRhbnQ7CiAgZm9udC1zaXplOiAuODVlbSAhaW1wb3J0YW50OwogIGZvbnQtd2VpZ2h0OiBib2xkICFpbXBvcnRhbnQ7CiAgaGVpZ2h0OiBhdXRvICFpbXBvcnRhbnQ7CiAgbGV0dGVyLXNwYWNpbmc6IC4wOGVtOwogIGxpbmUtaGVpZ2h0OiAuOTUgIWltcG9ydGFudDsKICBtYXgtd2lkdGg6IDE2ZW0gIWltcG9ydGFudDsKICBvcGFjaXR5OiAuODU7CiAgb3ZlcmZsb3c6IHZpc2libGUgIWltcG9ydGFudDsKICBwb3NpdGlvbjogcmVsYXRpdmUgIWltcG9ydGFudDsKICB0ZXh0LWRlY29yYXRpb246IG5vbmUgIWltcG9ydGFudDsKICB0ZXh0LWluZGVudDogLjA4ZW07CiAgdGV4dC1vdmVyZmxvdzogZWxsaXBzaXMgIWltcG9ydGFudDsKICB0ZXh0LXRyYW5zZm9ybTogdXBwZXJjYXNlICFpbXBvcnRhbnQ7CiAgd2hpdGUtc3BhY2U6IG5vd3JhcCAhaW1wb3J0YW50OwogIHdpZHRoOiBhdXRvICFpbXBvcnRhbnQ7Cn0KCmNsb3VkZmxhcmUtYXBwW2FwcD0id2VsY29tZS1iYXIiXSAuYWxlcnQtY3RhLWJ1dHRvbjo6YWZ0ZXIgewogIGNvbG9yOiBpbmhlcml0ICFpbXBvcnRhbnQ7CiAgY29udGVudDogIlwyMDNBIjsKICBkaXNwbGF5OiBpbmxpbmUtYmxvY2sgIWltcG9ydGFudDsKICBmb250LWZhbWlseTogImNmYXBwcy13ZWxjb21lLWJhci1pY29ucyI7CiAgZm9udC1zaXplOiAxLjNlbSAhaW1wb3J0YW50OwogIGZvbnQtc3R5bGU6IG5vcm1hbDsKICBmb250LXdlaWdodDogaW5oZXJpdDsKICBsaW5lLWhlaWdodDogLjggIWltcG9ydGFudDsKICBtYXJnaW4tdG9wOiAtMXB4ICFpbXBvcnRhbnQ7CiAgbWFyZ2luLXRvcDogYXV0byAhaW1wb3J0YW50OwogIHBhZGRpbmctbGVmdDogLjNlbSAhaW1wb3J0YW50OwogIHBvc2l0aW9uOiBhYnNvbHV0ZTsKICBsZWZ0OiAxMDAlOwp9CgpjbG91ZGZsYXJlLWFwcFthcHA9IndlbGNvbWUtYmFyIl0gYWxlcnQtZGlzbWlzcyB7CiAgY3Vyc29yOiBwb2ludGVyOwogIGNvbG9yOiByZ2JhKDEwLCAxMCwgMTAsIC4yNSk7CiAgZGlzcGxheTogaW5saW5lLWJsb2NrOwogIC13ZWJraXQtYm94LWZsZXg6IDA7CiAgICAgIC1tcy1mbGV4OiAwIDAgYXV0bzsKICAgICAgICAgIGZsZXg6IDAgMCBhdXRvOwogIGZvbnQtZmFtaWx5OiAiSGVsdmV0aWNhIE5ldWUiLCBIZWx2ZXRpY2EsIEFyaWFsLCBzYW5zLXNlcmlmOwogIGZvbnQtc2l6ZTogMmVtOwogIGZvbnQtd2VpZ2h0OiAzMDA7CiAgaGVpZ2h0OiAxZW07CiAgbGluZS1oZWlnaHQ6IC43NWVtOwogIG1hcmdpbjogMCAuMmVtOwogIC13ZWJraXQtdXNlci1zZWxlY3Q6IG5vbmU7CiAgICAgLW1vei11c2VyLXNlbGVjdDogbm9uZTsKICAgICAgLW1zLXVzZXItc2VsZWN0OiBub25lOwogICAgICAgICAgdXNlci1zZWxlY3Q6IG5vbmU7CiAgd2lkdGg6IC45ZW07Cn0KCmNsb3VkZmxhcmUtYXBwW2FwcD0id2VsY29tZS1iYXIiXSBhbGVydC1kaXNtaXNzOmhvdmVyIHsKICBjb2xvcjogcmdiYSgxMCwgMTAsIDEwLCAuNSk7Cn0KCmh0bWwgPiBib2R5ID4gY2xvdWRmbGFyZS1hcHBbYXBwPSJ3ZWxjb21lLWJhciJdW2RhdGEtc3R5bGU9InNsaW0iXSB7CiAgZm9udC1zaXplOiAuOTJlbTsKICBtaW4taGVpZ2h0OiAyLjJlbTsKfQoKaHRtbCA+IGJvZHkgPiBjbG91ZGZsYXJlLWFwcFthcHA9IndlbGNvbWUtYmFyIl1bZGF0YS1zdHlsZT0icHJvbWluZW50Il0gLmFsZXJ0LWN0YS1idXR0b24gewogIGJvcmRlci1yYWRpdXM6IC4xNWVtOwp9CgpAbWVkaWEgKG1pbi13aWR0aDogNzY4cHgpIHsKICBjbG91ZGZsYXJlLWFwcFthcHA9IndlbGNvbWUtYmFyIl0gewogICAgcGFkZGluZzogLjVlbSAwOwogIH0KCiAgY2xvdWRmbGFyZS1hcHBbYXBwPSJ3ZWxjb21lLWJhciJdW2RhdGEtc3R5bGU9InByb21pbmVudCJdIC5hbGVydC1jdGEtYnV0dG9uIHsKICAgIHBhZGRpbmc6IC42NWVtIDEuNzVlbSAuNmVtIC45ZW0gIWltcG9ydGFudDsKICB9CgogIGNsb3VkZmxhcmUtYXBwW2FwcD0id2VsY29tZS1iYXIiXVtkYXRhLXN0eWxlPSJwcm9taW5lbnQiXSAuYWxlcnQtY3RhLWJ1dHRvbjo6YWZ0ZXIgewogICAgbGVmdDogYXV0bzsKICB9CgogIGNsb3VkZmxhcmUtYXBwW2FwcD0id2VsY29tZS1iYXIiXSAuYWxlcnQtY3RhLWJ1dHRvbiB7CiAgICBtYXJnaW4tbGVmdDogMWVtOwogIH0KfQoKQG1lZGlhIChtYXgtd2lkdGg6IDc2OHB4KSB7CiAgaHRtbCA+IGJvZHkgPiBjbG91ZGZsYXJlLWFwcFthcHA9IndlbGNvbWUtYmFyIl0gewogICAgLXdlYmtpdC1ib3gtYWxpZ246IGNlbnRlcjsKICAgICAgICAtbXMtZmxleC1hbGlnbjogY2VudGVyOwogICAgICAgICAgICBhbGlnbi1pdGVtczogY2VudGVyOwogICAgZm9udC1zaXplOiAuOTJlbTsKICAgIG1pbi1oZWlnaHQ6IDIuMmVtOwogICAgcGFkZGluZzogLjVlbSAwIC41ZW0gLjVlbTsKICB9CgogIGNsb3VkZmxhcmUtYXBwW2FwcD0id2VsY29tZS1iYXIiXSAuYWxlcnQtY3RhLWJ1dHRvbiB7CiAgICBtYXJnaW4tdG9wOiAuNWVtOwogICAgZGlzcGxheTogYmxvY2sgIWltcG9ydGFudDsKICAgIC13ZWJraXQtYm94LWZsZXg6IDA7CiAgICAgICAgLW1zLWZsZXg6IDAgMCBhdXRvOwogICAgICAgICAgICBmbGV4OiAwIDAgYXV0bzsKICB9CgogIGNsb3VkZmxhcmUtYXBwW2FwcD0id2VsY29tZS1iYXIiXSBhbGVydC1tZXNzYWdlLWNvbnRlbnQgewogICAgLXdlYmtpdC1ib3gtb3JpZW50OiB2ZXJ0aWNhbCAhaW1wb3J0YW50OwogICAgLXdlYmtpdC1ib3gtZGlyZWN0aW9uOiBub3JtYWwgIWltcG9ydGFudDsKICAgICAgICAtbXMtZmxleC1mbG93OiBjb2x1bW4gbm93cmFwICFpbXBvcnRhbnQ7CiAgICAgICAgICAgIGZsZXgtZmxvdzogY29sdW1uIG5vd3JhcCAhaW1wb3J0YW50OwogICAgLXdlYmtpdC1ib3gtYWxpZ246IHN0YXJ0ICFpbXBvcnRhbnQ7CiAgICAgICAgLW1zLWZsZXgtYWxpZ246IHN0YXJ0ICFpbXBvcnRhbnQ7CiAgICAgICAgICAgIGFsaWduLWl0ZW1zOiBmbGV4LXN0YXJ0ICFpbXBvcnRhbnQ7CiAgfQp9Cgo=';document.getElementsByTagName('head')[0].appendChild(link);}catch(e){}})();