(self.webpackChunkereader=self.webpackChunkereader||[]).push([[622],{70348:function(n,e,t){var s=t(5485);n.exports=function(){var n=new s.Template({code:function(n,e,t){var s=this;return s.b(t=t||""),s.b("<!DOCTYPE html>"),s.b("\n"+t),s.b('<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">'),s.b("\n"+t),s.b("<head>"),s.b("\n"+t),s.b("    <title>Access Placeholder</title>"),s.b("\n"+t),s.b('    <link rel="stylesheet" type="text/css" href="'),s.b(s.v(s.f("iframeContentCSSUrl",n,e,0))),s.b('"/>'),s.b("\n"+t),s.b("</head>"),s.b("\n"+t),s.b("<body>"),s.b("\n"+t),s.b('<div class="access-placeholder">'),s.b("\n"+t),s.b('    <div class="access-placeholder__content">'),s.b("\n"+t),s.b('        <div class="access-placeholder__number">'),s.b(s.v(s.f("number",n,e,0))),s.b("</div>"),s.b("\n"+t),s.b('        <p class="access-placeholder__label">Missing access to content section</p>'),s.b("\n"+t),s.b('        <div class="access-placeholder__text"><span class="text-decimal">'),s.b(s.v(s.f("number",n,e,0))),s.b(". </span>"),s.b(s.v(s.f("title",n,e,0))),s.b("</div>"),s.b("\n"+t),s.b('        <a href="'),s.b(s.v(s.f("accessUrl",n,e,0))),s.b('" class="access-link" target="_blank">'),s.b("\n"+t),s.b("            buy access"),s.b("\n"+t),s.b('            <span class="icon material-icons">arrow_forward</span>'),s.b("\n"+t),s.b("        </a>"),s.b("\n"+t),s.b("    </div>"),s.b("\n"+t),s.b('    <div class="access-icon__container">'),s.b("\n"+t),s.b('        <span class="access-icon material-icons">lock</span>'),s.b("\n"+t),s.b("    </div>"),s.b("\n"),s.b("\n"+t),s.b("</div>"),s.b("\n"+t),s.b("</body>"),s.b("\n"+t),s.b("</html>"),s.fl()},partials:{},subs:{}},'<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\n<head>\n    <title>Access Placeholder</title>\n    <link rel="stylesheet" type="text/css" href="{{iframeContentCSSUrl}}"/>\n</head>\n<body>\n<div class="access-placeholder">\n    <div class="access-placeholder__content">\n        <div class="access-placeholder__number">{{number}}</div>\n        <p class="access-placeholder__label">Missing access to content section</p>\n        <div class="access-placeholder__text"><span class="text-decimal">{{number}}. </span>{{title}}</div>\n        <a href="{{accessUrl}}" class="access-link" target="_blank">\n            buy access\n            <span class="icon material-icons">arrow_forward</span>\n        </a>\n    </div>\n    <div class="access-icon__container">\n        <span class="access-icon material-icons">lock</span>\n    </div>\n\n</div>\n</body>\n</html>',s);return n.render.apply(n,arguments)}},60213:function(n,e,t){var s=t(5485);n.exports=function(){var n=new s.Template({code:function(n,e,t){var s=this;return s.b(t=t||""),s.b('<div class="ad-indicator">'),s.b("\n"+t),s.b('    <span class="hor-line"></span>'),s.b("\n"+t),s.b('    <span class="ad-indicator-message">Advertisement '),s.s(s.f("leading",n,e,1),n,e,0,127,132,"{{ }}")&&(s.rs(n,e,(function(n,e,t){t.b("Start")})),n.pop()),s.s(s.f("trailing",n,e,1),n,e,0,157,160,"{{ }}")&&(s.rs(n,e,(function(n,e,t){t.b("End")})),n.pop()),s.b("</span>"),s.b("\n"+t),s.b('    <span class="hor-line"></span>'),s.b("\n"+t),s.b("</div>"),s.fl()},partials:{},subs:{}},'<div class="ad-indicator">\n    <span class="hor-line"></span>\n    <span class="ad-indicator-message">Advertisement {{#leading}}Start{{/leading}}{{#trailing}}End{{/trailing}}</span>\n    <span class="hor-line"></span>\n</div>',s);return n.render.apply(n,arguments)}},27440:function(n,e,t){var s=t(5485);n.exports=function(){var n=new s.Template({code:function(n,e,t){var s=this;return s.b(t=t||""),s.b("<!DOCTYPE html>"),s.b("\n"+t),s.b('<html class="campaignFrame" xml:lang="en">'),s.b("\n"+t),s.b("<head>"),s.b("\n"+t),s.b("    <title>Atypon ad place holder</title>"),s.b("\n"+t),s.b('    <meta name="viewport" content="width=640, height=824"/>'),s.b("\n"+t),s.b('    <style type="text/css">'),s.b("\n"+t),s.b("        .campaign > * {"),s.b("\n"+t),s.b("            box-sizing: border-box;"),s.b("\n"+t),s.b("            margin: auto;"),s.b("\n"+t),s.b("            max-height: 100%;"),s.b("\n"+t),s.b("            max-width: 100%;"),s.b("\n"+t),s.b("        }"),s.b("\n"+t),s.b("        .campaign {"),s.b("\n"+t),s.b("            margin: 0;"),s.b("\n"+t),s.b("            text-align: center;"),s.b("\n"+t),s.b("        }"),s.b("\n"+t),s.b("        .campaign.pdf img {"),s.b("\n"+t),s.b("            display: block;"),s.b("\n"+t),s.b("            width: 100%;"),s.b("\n"+t),s.b("        }"),s.b("\n"+t),s.b("    </style>"),s.b("\n"),s.b("\n"+t),s.s(s.d("settings.isPdf",n,e,1),n,e,0,564,775,"{{ }}")&&(s.rs(n,e,(function(n,e,s){s.b('    <link rel="stylesheet" href="'),s.b(s.v(s.d("settings.src",n,e,0))),s.b('css/base.min.css" />'),s.b("\n"+t),s.b('    <link rel="stylesheet" href="'),s.b(s.v(s.d("settings.src",n,e,0))),s.b('css/fancy.min.css" />'),s.b("\n"+t),s.b('    <link rel="stylesheet" href="'),s.b(s.v(s.d("settings.src",n,e,0))),s.b('css/pdf.css" />'),s.b("\n"+t)})),n.pop()),s.b("\n"+t),s.b("    <script>"),s.b("\n"+t),s.b("        window.readerConfig  = {"),s.b("\n"+t),s.b('            issn: "'),s.b(s.v(s.d("settings.adsData.issn",n,e,0))),s.b('",'),s.b("\n"+t),s.b('            eissn: "'),s.b(s.v(s.d("settings.adsData.eissn",n,e,0))),s.b('",'),s.b("\n"+t),s.b('            issue:"'),s.b(s.v(s.d("settings.adsData.issue",n,e,0))),s.b('",'),s.b("\n"+t),s.b('            volume:"'),s.b(s.v(s.d("settings.adsData.volume",n,e,0))),s.b('",'),s.b("\n"+t),s.b('            doi:"'),s.b(s.v(s.d("settings.adsData.doi",n,e,0))),s.b('"'),s.b("\n"+t),s.b("        };"),s.b("\n"+t),s.b('        window.addEventListener("googleAdsLoaded", function (e) {'),s.b("\n"+t),s.b("            let detail = e.detail;"),s.b("\n"+t),s.b("            if (!detail.isEmpty) {"),s.b("\n"+t),s.b('                window.parent.window.dispatchEvent(new CustomEvent("showGoogleAds", {detail: detail}));'),s.b("\n"+t),s.b("            }"),s.b("\n"+t),s.b('            document.getElementsByTagName("iframe")[0].contentDocument.addEventListener("DOMMouseScroll", triggerScroll)'),s.b("\n"+t),s.b('            document.getElementsByTagName("iframe")[0].contentDocument.addEventListener("mousewheel", triggerScroll)'),s.b("\n"+t),s.b("        });"),s.b("\n"),s.b("\n"+t),s.b("        function triggerScroll(e) {"),s.b("\n"+t),s.b("            e.stopPropagation();"),s.b("\n"+t),s.b("            window.parent.window.EREADER.throttledHorizontal(e);"),s.b("\n"+t),s.b("        }"),s.b("\n"),s.b("\n"+t),s.b("    <\/script>"),s.b("\n"),s.b("\n"+t),s.b("</head>"),s.b("\n"+t),s.b("<body>"),s.b("\n"),s.b("\n"+t),s.b('<div data-index = "'),s.b(s.v(s.d("settings.adIndex",n,e,0))),s.b('" class="campaign '),s.s(s.d("settings.isPdf",n,e,1),n,e,0,1847,1853,"{{ }}")&&(s.rs(n,e,(function(n,e,t){t.b("pdf w0")})),n.pop()),s.b('">'),s.b("\n"+t),s.b("    "),s.b(s.t(s.d("settings.html",n,e,0))),s.b("\n"+t),s.b("</div>"),s.b("\n"),s.b("\n"+t),s.b("</body>"),s.b("\n"+t),s.b("</html>"),s.b("\n"),s.fl()},partials:{},subs:{}},'<!DOCTYPE html>\n<html class="campaignFrame" xml:lang="en">\n<head>\n    <title>Atypon ad place holder</title>\n    <meta name="viewport" content="width=640, height=824"/>\n    <style type="text/css">\n        .campaign > * {\n            box-sizing: border-box;\n            margin: auto;\n            max-height: 100%;\n            max-width: 100%;\n        }\n        .campaign {\n            margin: 0;\n            text-align: center;\n        }\n        .campaign.pdf img {\n            display: block;\n            width: 100%;\n        }\n    </style>\n\n    {{#settings.isPdf}}\n    <link rel="stylesheet" href="{{settings.src}}css/base.min.css" />\n    <link rel="stylesheet" href="{{settings.src}}css/fancy.min.css" />\n    <link rel="stylesheet" href="{{settings.src}}css/pdf.css" />\n    {{/settings.isPdf}}\n\n    <script>\n        window.readerConfig  = {\n            issn: "{{settings.adsData.issn}}",\n            eissn: "{{settings.adsData.eissn}}",\n            issue:"{{settings.adsData.issue}}",\n            volume:"{{settings.adsData.volume}}",\n            doi:"{{settings.adsData.doi}}"\n        };\n        window.addEventListener("googleAdsLoaded", function (e) {\n            let detail = e.detail;\n            if (!detail.isEmpty) {\n                window.parent.window.dispatchEvent(new CustomEvent("showGoogleAds", {detail: detail}));\n            }\n            document.getElementsByTagName("iframe")[0].contentDocument.addEventListener("DOMMouseScroll", triggerScroll)\n            document.getElementsByTagName("iframe")[0].contentDocument.addEventListener("mousewheel", triggerScroll)\n        });\n\n        function triggerScroll(e) {\n            e.stopPropagation();\n            window.parent.window.EREADER.throttledHorizontal(e);\n        }\n\n    <\/script>\n\n</head>\n<body>\n\n<div data-index = "{{settings.adIndex}}" class="campaign {{#settings.isPdf}}pdf w0{{/settings.isPdf}}">\n    {{{settings.html}}}\n</div>\n\n</body>\n</html>\n',s);return n.render.apply(n,arguments)}},30426:function(n,e,t){var s=t(5485);n.exports=function(){var n=new s.Template({code:function(n,e,t){var s=this;return s.b(t=t||""),s.b('<div class="image-loading-failed-indicator" style="font-family: Arial, Helvetica, Sans Serif; display: inline-flex; align-items: center; position: absolute; color: #737380; border-radius: 22px; background-color: white; padding: 6px 12px" >'),s.b("\n"+t),s.b('    <svg xmlns="http://www.w3.org/2000/svg" style="fill: #9999AA; width: 16px; height: 16px" viewBox="0 0 24 24" fill="white" width="24px" height="24px"><path d="M0 0h24v24H0V0z" fill="none"/><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5v-4.58l.99.99 4-4 4 4 4-3.99L19 12.43V19zm0-9.41l-1.01-1.01-4 4.01-4-4-4 4-.99-1V5h14v4.59z"/></svg>'),s.b("\n"+t),s.b('    <span style="margin-left: 4px; font-size: 12px; color: #737380; font-weight: 500; line-height: 18px">Image failed to load</span>'),s.b("\n"+t),s.b("</div>"),s.fl()},partials:{},subs:{}},'<div class="image-loading-failed-indicator" style="font-family: Arial, Helvetica, Sans Serif; display: inline-flex; align-items: center; position: absolute; color: #737380; border-radius: 22px; background-color: white; padding: 6px 12px" >\n    <svg xmlns="http://www.w3.org/2000/svg" style="fill: #9999AA; width: 16px; height: 16px" viewBox="0 0 24 24" fill="white" width="24px" height="24px"><path d="M0 0h24v24H0V0z" fill="none"/><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5v-4.58l.99.99 4-4 4 4 4-3.99L19 12.43V19zm0-9.41l-1.01-1.01-4 4.01-4-4-4 4-.99-1V5h14v4.59z"/></svg>\n    <span style="margin-left: 4px; font-size: 12px; color: #737380; font-weight: 500; line-height: 18px">Image failed to load</span>\n</div>',s);return n.render.apply(n,arguments)}},79713:function(n,e,t){var s=t(5485);n.exports=function(){var n=new s.Template({code:function(n,e,t){var s=this;return s.b(t=t||""),s.b('<svg id="dots"'),s.b("\n"+t),s.b('     xmlns="http://www.w3.org/2000/svg"'),s.b("\n"+t),s.b('     width="25%"'),s.b("\n"+t),s.b('     height="44"'),s.b("\n"+t),s.b('     viewBox="0 0 164 44"'),s.b("\n"+t),s.b('     fill="none"'),s.b("\n"+t),s.b(">"),s.b("\n"+t),s.b('    <g transform="translate(14 22)">'),s.b("\n"+t),s.b('        <circle cx="0" cy="0" r="14" fill="#B8B8CC">'),s.b("\n"+t),s.b("            <animateTransform"),s.b("\n"+t),s.b('                    attributeName="transform"'),s.b("\n"+t),s.b('                    type="scale"'),s.b("\n"+t),s.b('                    begin="-0.375s"'),s.b("\n"+t),s.b('                    calcMode="spline"'),s.b("\n"+t),s.b('                    keySplines="0.3 0 0.7 1;0.3 0 0.7 1"'),s.b("\n"+t),s.b('                    values="0;1;0"'),s.b("\n"+t),s.b('                    keyTimes="0;0.5;1"'),s.b("\n"+t),s.b('                    dur="2s"'),s.b("\n"+t),s.b('                    repeatCount="indefinite"'),s.b("\n"+t),s.b("            />"),s.b("\n"+t),s.b("        </circle>"),s.b("\n"+t),s.b("    </g>"),s.b("\n"+t),s.b('    <g transform="translate(74 22)">'),s.b("\n"+t),s.b('        <circle cx="0" cy="0" r="18" fill="#B8B8CC">'),s.b("\n"+t),s.b("            <animateTransform"),s.b("\n"+t),s.b('                    attributeName="transform"'),s.b("\n"+t),s.b('                    type="scale"'),s.b("\n"+t),s.b('                    begin="-0.25s"'),s.b("\n"+t),s.b('                    calcMode="spline"'),s.b("\n"+t),s.b('                    keySplines="0.3 0 0.7 1;0.3 0 0.7 1"'),s.b("\n"+t),s.b('                    values="0;1;0"'),s.b("\n"+t),s.b('                    keyTimes="0;0.5;1"'),s.b("\n"+t),s.b('                    dur="2s"'),s.b("\n"+t),s.b('                    repeatCount="indefinite"'),s.b("\n"+t),s.b("            />"),s.b("\n"+t),s.b("        </circle>"),s.b("\n"+t),s.b("    </g>"),s.b("\n"+t),s.b('    <g transform="translate(142 22)">'),s.b("\n"+t),s.b('        <circle cx="0" cy="0" r="22" fill="#B8B8CC">'),s.b("\n"+t),s.b("            <animateTransform"),s.b("\n"+t),s.b('                    attributeName="transform"'),s.b("\n"+t),s.b('                    type="scale"'),s.b("\n"+t),s.b('                    begin="-0.125s"'),s.b("\n"+t),s.b('                    calcMode="spline"'),s.b("\n"+t),s.b('                    keySplines="0.3 0 0.7 1;0.3 0 0.7 1"'),s.b("\n"+t),s.b('                    values="0;1;0"'),s.b("\n"+t),s.b('                    keyTimes="0;0.5;1"'),s.b("\n"+t),s.b('                    dur="2s"'),s.b("\n"+t),s.b('                    repeatCount="indefinite"'),s.b("\n"+t),s.b("            />"),s.b("\n"+t),s.b("        </circle>"),s.b("\n"+t),s.b("    </g>"),s.b("\n"+t),s.b("</svg>"),s.b("\n"),s.fl()},partials:{},subs:{}},'<svg id="dots"\n     xmlns="http://www.w3.org/2000/svg"\n     width="25%"\n     height="44"\n     viewBox="0 0 164 44"\n     fill="none"\n>\n    <g transform="translate(14 22)">\n        <circle cx="0" cy="0" r="14" fill="#B8B8CC">\n            <animateTransform\n                    attributeName="transform"\n                    type="scale"\n                    begin="-0.375s"\n                    calcMode="spline"\n                    keySplines="0.3 0 0.7 1;0.3 0 0.7 1"\n                    values="0;1;0"\n                    keyTimes="0;0.5;1"\n                    dur="2s"\n                    repeatCount="indefinite"\n            />\n        </circle>\n    </g>\n    <g transform="translate(74 22)">\n        <circle cx="0" cy="0" r="18" fill="#B8B8CC">\n            <animateTransform\n                    attributeName="transform"\n                    type="scale"\n                    begin="-0.25s"\n                    calcMode="spline"\n                    keySplines="0.3 0 0.7 1;0.3 0 0.7 1"\n                    values="0;1;0"\n                    keyTimes="0;0.5;1"\n                    dur="2s"\n                    repeatCount="indefinite"\n            />\n        </circle>\n    </g>\n    <g transform="translate(142 22)">\n        <circle cx="0" cy="0" r="22" fill="#B8B8CC">\n            <animateTransform\n                    attributeName="transform"\n                    type="scale"\n                    begin="-0.125s"\n                    calcMode="spline"\n                    keySplines="0.3 0 0.7 1;0.3 0 0.7 1"\n                    values="0;1;0"\n                    keyTimes="0;0.5;1"\n                    dur="2s"\n                    repeatCount="indefinite"\n            />\n        </circle>\n    </g>\n</svg>\n',s);return n.render.apply(n,arguments)}},18912:function(n,e,t){var s=t(5485);n.exports=function(){var n=new s.Template({code:function(n,e,t){var s=this;return s.b(t=t||""),s.b('<svg width="204" height="204" viewBox="0 0 204 204" fill="none" xmlns="http://www.w3.org/2000/svg">'),s.b("\n"+t),s.b('    <g opacity="0.6" filter="url(#filter0_di)">'),s.b("\n"+t),s.b('        <g transform="translate(102 98)">'),s.b("\n"+t),s.b('            <circle cx="0" cy="0" r="38" fill="#E1E1EA">'),s.b("\n"+t),s.b("                <animateTransform"),s.b("\n"+t),s.b('                        attributeName="transform"'),s.b("\n"+t),s.b('                        type="scale"'),s.b("\n"+t),s.b('                        values="0;0.5;1"'),s.b("\n"+t),s.b('                        keyTimes="0;0.5;1"'),s.b("\n"+t),s.b('                        dur="2s"'),s.b("\n"+t),s.b('                        repeatCount="indefinite"'),s.b("\n"+t),s.b("                />"),s.b("\n"+t),s.b('                <animate attributeName=\'opacity\' values="1;0.5;0" keyTimes="0;0.5;1" dur="2s" repeatCount="indefinite"/>'),s.b("\n"+t),s.b("            </circle>"),s.b("\n"+t),s.b("        </g>"),s.b("\n"+t),s.b("    </g>"),s.b("\n"+t),s.b("    <defs>"),s.b("\n"+t),s.b('        <filter id="filter0_di" x="0" y="0" width="204" height="204" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">'),s.b("\n"+t),s.b('            <feFlood flood-opacity="0" result="BackgroundImageFix"/>'),s.b("\n"+t),s.b('            <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"/>'),s.b("\n"+t),s.b('            <feOffset dy="4"/>'),s.b("\n"+t),s.b('            <feGaussianBlur stdDeviation="32"/>'),s.b("\n"+t),s.b('            <feColorMatrix type="matrix" values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 1 0"/>'),s.b("\n"+t),s.b('            <feBlend mode="normal" in2="BackgroundImageFix" result="effect1_dropShadow"/>'),s.b("\n"+t),s.b('            <feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow" result="shape"/>'),s.b("\n"+t),s.b('            <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" result="hardAlpha"/>'),s.b("\n"+t),s.b("            <feOffset/>"),s.b("\n"+t),s.b('            <feGaussianBlur stdDeviation="16"/>'),s.b("\n"+t),s.b('            <feComposite in2="hardAlpha" operator="arithmetic" k2="-1" k3="1"/>'),s.b("\n"+t),s.b('            <feColorMatrix type="matrix" values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 1 0"/>'),s.b("\n"+t),s.b('            <feBlend mode="normal" in2="shape" result="effect2_innerShadow"/>'),s.b("\n"+t),s.b("        </filter>"),s.b("\n"+t),s.b("    </defs>"),s.b("\n"+t),s.b("</svg>"),s.b("\n"),s.fl()},partials:{},subs:{}},'<svg width="204" height="204" viewBox="0 0 204 204" fill="none" xmlns="http://www.w3.org/2000/svg">\n    <g opacity="0.6" filter="url(#filter0_di)">\n        <g transform="translate(102 98)">\n            <circle cx="0" cy="0" r="38" fill="#E1E1EA">\n                <animateTransform\n                        attributeName="transform"\n                        type="scale"\n                        values="0;0.5;1"\n                        keyTimes="0;0.5;1"\n                        dur="2s"\n                        repeatCount="indefinite"\n                />\n                <animate attributeName=\'opacity\' values="1;0.5;0" keyTimes="0;0.5;1" dur="2s" repeatCount="indefinite"/>\n            </circle>\n        </g>\n    </g>\n    <defs>\n        <filter id="filter0_di" x="0" y="0" width="204" height="204" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">\n            <feFlood flood-opacity="0" result="BackgroundImageFix"/>\n            <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"/>\n            <feOffset dy="4"/>\n            <feGaussianBlur stdDeviation="32"/>\n            <feColorMatrix type="matrix" values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 1 0"/>\n            <feBlend mode="normal" in2="BackgroundImageFix" result="effect1_dropShadow"/>\n            <feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow" result="shape"/>\n            <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" result="hardAlpha"/>\n            <feOffset/>\n            <feGaussianBlur stdDeviation="16"/>\n            <feComposite in2="hardAlpha" operator="arithmetic" k2="-1" k3="1"/>\n            <feColorMatrix type="matrix" values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 1 0"/>\n            <feBlend mode="normal" in2="shape" result="effect2_innerShadow"/>\n        </filter>\n    </defs>\n</svg>\n',s);return n.render.apply(n,arguments)}},77463:function(n,e,t){var s=t(5485);n.exports=function(){var n=new s.Template({code:function(n,e,t){var s=this;return s.b(t=t||""),s.b('<div id="'),s.s(s.d("settings.id",n,e,1),n,e,0,88,103,"{{ }}")&&(s.rs(n,e,(function(n,e,t){t.b(t.v(t.d("settings.id",n,e,0)))})),n.pop()),s.s(s.d("settings.id",n,e,1),n,e,1,0,0,"")||s.b("mediaContainer"),s.b('" class="'),s.b(s.v(s.d("settings.class",n,e,0))),s.b('">'),s.b("\n"+t),s.b('    <nav class="top-row">'),s.b("\n"+t),s.b('        <h4 id="mediaContainer_title" title="">'),s.b(s.t(s.d("settings.title",n,e,0))),s.b("</h4>"),s.b("\n"+t),s.b('        <button class="btn closeBtn"'),s.b("\n"+t),s.b('                title="Close media container"'),s.b("\n"+t),s.b('                type="button"'),s.b("\n"+t),s.b('                tabindex="0"'),s.b("\n"+t),s.b('                onClick="'),s.b("\n"+t),s.b("                    $('#"),s.s(s.d("settings.id",n,e,1),n,e,0,502,517,"{{ }}")&&(s.rs(n,e,(function(n,e,t){t.b(t.v(t.d("settings.id",n,e,0)))})),n.pop()),s.s(s.d("settings.id",n,e,1),n,e,1,0,0,"")||s.b("mediaContainer"),s.b("').remove();"),s.b("\n"+t),s.b("\t\t\t\t\t$('.tooltip').tooltip('hide');\">"),s.b("\n"+t),s.b("            CLOSE"),s.b("\n"+t),s.b("        </button>"),s.b("\n"+t),s.b("    </nav>"),s.b("\n"+t),s.b('    <div class="content-row">'),s.b(s.t(s.d("settings.content",n,e,0))),s.b("</div>"),s.b("\n"+t),s.b("</div>"),s.b("\n"),s.fl()},partials:{},subs:{}},'{{! if an id is passed use that or else use \'mediaContainer\'}}\n<div id="{{#settings.id}}{{settings.id}}{{/settings.id}}{{^settings.id}}mediaContainer{{/settings.id}}" class="{{settings.class}}">\n    <nav class="top-row">\n        <h4 id="mediaContainer_title" title="">{{{settings.title}}}</h4>\n        <button class="btn closeBtn"\n                title="Close media container"\n                type="button"\n                tabindex="0"\n                onClick="\n                    $(\'#{{#settings.id}}{{settings.id}}{{/settings.id}}{{^settings.id}}mediaContainer{{/settings.id}}\').remove();\n\t\t\t\t\t$(\'.tooltip\').tooltip(\'hide\');">\n            CLOSE\n        </button>\n    </nav>\n    <div class="content-row">{{{settings.content}}}</div>\n</div>\n',s);return n.render.apply(n,arguments)}},53978:function(n,e,t){var s=t(5485);n.exports=function(){var n=new s.Template({code:function(n,e,t){var s=this;return s.b(t=t||""),s.b("<!DOCTYPE html>"),s.b("\n"+t),s.b('<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">'),s.b("\n"+t),s.b("<head>"),s.b("\n"+t),s.b("    <title>Offline No Access Placeholder</title>"),s.b("\n"+t),s.b('    <link rel="stylesheet" type="text/css" href="'),s.b(s.v(s.f("iframeContentCSSUrl",n,e,0))),s.b('"/>'),s.b("\n"+t),s.b("</head>"),s.b("\n"+t),s.b("<body>"),s.b("\n"+t),s.b('    <div class="access-placeholder offline-no-access-placeholder">'),s.b("\n"+t),s.b('        <div class="access-placeholder__content">'),s.b("\n"+t),s.b('            <div class="access-placeholder__number">'),s.b(s.v(s.f("number",n,e,0))),s.b("</div>"),s.b("\n"+t),s.b('            <p class="access-placeholder__label">The following content is not available offline</p>'),s.b("\n"+t),s.b('            <div class="access-placeholder__text"><span class="text-decimal">'),s.b(s.v(s.f("number",n,e,0))),s.b(". </span>"),s.b(s.v(s.f("title",n,e,0))),s.b("</div>"),s.b("\n"+t),s.b('            <ul class="access-placeholder__columns">'),s.b("\n"+t),s.b('                <li class="single-column"></li>'),s.b("\n"+t),s.b('                <li class="single-column"></li>'),s.b("\n"+t),s.b('                <li class="single-column"></li>'),s.b("\n"+t),s.b('                <li class="single-column"></li>'),s.b("\n"+t),s.b('                <li class="single-column"></li>'),s.b("\n"+t),s.b('                <li class="single-column"></li>'),s.b("\n"+t),s.b('                <li class="single-column"></li>'),s.b("\n"+t),s.b("            </ul>"),s.b("\n"+t),s.b("        </div>"),s.b("\n"+t),s.b('        <div class="access-icon__container">'),s.b("\n"+t),s.b('            <span class="access-icon material-icons">wifi_off</span>'),s.b("\n"+t),s.b("        </div>"),s.b("\n"+t),s.b("    </div>"),s.b("\n"+t),s.b("</body>"),s.b("\n"+t),s.b("</html>"),s.fl()},partials:{},subs:{}},'<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\n<head>\n    <title>Offline No Access Placeholder</title>\n    <link rel="stylesheet" type="text/css" href="{{iframeContentCSSUrl}}"/>\n</head>\n<body>\n    <div class="access-placeholder offline-no-access-placeholder">\n        <div class="access-placeholder__content">\n            <div class="access-placeholder__number">{{number}}</div>\n            <p class="access-placeholder__label">The following content is not available offline</p>\n            <div class="access-placeholder__text"><span class="text-decimal">{{number}}. </span>{{title}}</div>\n            <ul class="access-placeholder__columns">\n                <li class="single-column"></li>\n                <li class="single-column"></li>\n                <li class="single-column"></li>\n                <li class="single-column"></li>\n                <li class="single-column"></li>\n                <li class="single-column"></li>\n                <li class="single-column"></li>\n            </ul>\n        </div>\n        <div class="access-icon__container">\n            <span class="access-icon material-icons">wifi_off</span>\n        </div>\n    </div>\n</body>\n</html>',s);return n.render.apply(n,arguments)}},46682:function(n,e,t){var s=t(5485);n.exports=function(){var n=new s.Template({code:function(n,e,t){var s=this;return s.b(t=t||""),s.b('<div id="epub-reader-container">'),s.b("\n"+t),s.b('    <div id="epub-reader-frame">'),s.b("\n"+t),s.b("    </div>"),s.b("\n"+t),s.b("</div>"),s.b("\n"),s.b("\n"),s.fl()},partials:{},subs:{}},'<div id="epub-reader-container">\n    <div id="epub-reader-frame">\n    </div>\n</div>\n\n',s);return n.render.apply(n,arguments)}}}]);