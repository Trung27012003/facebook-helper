/* Summernote provides the toolbar and editing commands. This adapter handles Qt transport and paste cleanup. */
(() => {
'use strict';
let bridge=null, programmatic=0,plainPaste=false,revision=0,generation=0;
const allowedStyle=new Set(['font-weight','font-style','text-decoration','font-size','font-family','color','background-color','text-align','vertical-align']);
function luminance(color) {
 const p=document.createElement('span');p.style.color=color;document.body.appendChild(p);
 const channels=getComputedStyle(p).color.match(/[\d.]+/g);p.remove();
 if(!channels||channels.length<3)return null;
 return .2126*Number(channels[0])+.7152*Number(channels[1])+.0722*Number(channels[2]);
}
function cleanHTML(html, pasted=false) {
 const clean=DOMPurify.sanitize(html,{ALLOWED_TAGS:['p','div','span','b','strong','i','em','u','s','sub','sup','br','hr','h1','h2','h3','h4','h5','h6','blockquote','pre','code','ul','ol','li','table','thead','tbody','tfoot','tr','td','th','a','font'],
 ALLOWED_ATTR:['style','href','colspan','rowspan','start','color','face','size'],ALLOW_DATA_ATTR:false});
 const root=document.createElement('div');root.innerHTML=clean;
 // Summernote/Chromium's foreground-color command legitimately emits <font color>.
 for(const font of root.querySelectorAll('font')) {
  const span=document.createElement('span');span.style.cssText=font.style.cssText;
  if(font.hasAttribute('color'))span.style.color=font.getAttribute('color');
  if(font.hasAttribute('face'))span.style.fontFamily=font.getAttribute('face');
  const size=Number(font.getAttribute('size'));if(size>=1&&size<=7)span.style.fontSize=[0,10,13,16,18,24,32,48][size]+'px';
  while(font.firstChild)span.appendChild(font.firstChild);font.replaceWith(span);
 }
 let darkTheme=false;
 for(const el of root.querySelectorAll('[style]')) {
  const bg=el.style.backgroundColor;
  if(bg && bg!=='transparent' && (luminance(bg)??255)<120)darkTheme=true;
 }
 for(const el of root.querySelectorAll('*')) {
  const style=el.style;
  for(const name of Array.from(style)) {
   const value=style.getPropertyValue(name);
   if(!allowedStyle.has(name)||/url\s*\(|expression\s*\(|javascript:|@import/i.test(value)) style.removeProperty(name);
  }
  // Facebook's dark theme is page chrome, not an intentional text highlight.
  if(pasted&&darkTheme) {
   style.removeProperty('background-color');
   if((luminance(style.color)||0)>160)style.removeProperty('color');
   style.removeProperty('font-family');
  }
  if(!style.cssText)el.removeAttribute('style');
  if(el.tagName==='A'&&!/^(https?:|mailto:|tel:)/i.test(el.getAttribute('href')||''))el.removeAttribute('href');
 }
 return root.innerHTML;
}
function plainHTML(html) {
 const root=document.createElement('div');root.innerHTML=html;
 const blockTags=new Set(['P','DIV','H1','H2','H3','H4','H5','H6','BLOCKQUOTE','PRE']);
 function walk(node) {
  if(node.nodeType===3)return node.textContent.replace(/\u00a0/g,' ');
  if(node.nodeType!==1)return '';
  if(node.tagName==='BR')return '\n';
  if(node.tagName==='TABLE')return Array.from(node.rows).map(row=>Array.from(row.cells).map(cell=>Array.from(cell.childNodes).map(walk).join('').trim().replace(/\n+/g,' / ')).join(' | ')).join('\n')+'\n';
  if(node.tagName==='UL'||node.tagName==='OL')return Array.from(node.children).filter(el=>el.tagName==='LI').map((li,index)=>{
   const marker=node.tagName==='OL'?String(Number(node.getAttribute('start')||1)+index)+'.':'•';
   return marker+' '+Array.from(li.childNodes).map(walk).join('').trim();
  }).join('\n')+'\n';
  const inside=Array.from(node.childNodes).map(walk).join('');
  return inside+(blockTags.has(node.tagName)?'\n':'');
 }
 return Array.from(root.childNodes).map(walk).join('').replace(/\n{3,}/g,'\n\n').trim();
}
function snapshot(){const html=cleanHTML($('#editor').summernote('code'));return {html,plain:plainHTML(html),revision,generation};}
function notify(){revision++;if(bridge){const data=snapshot();bridge.changed(data.html,data.plain,!programmatic,revision,generation);}}
function paste(html,text,plain=false) {
 const source=plain?'':html;
 if(source)$('#editor').summernote('pasteHTML',cleanHTML(source,true));
 else $('#editor').summernote('insertText',text||'');
 if(/<img[\s>]/i.test(source)&&bridge)bridge.notice('Đã dán định dạng chữ. Ảnh trong bài cần thêm bằng nút Thêm ảnh.');
 notify();return snapshot();
}
$('#editor').summernote({lang:'vi-VN',height:400,minHeight:180,dialogsInBody:true,disableDragAndDrop:true,
 placeholder:'Soạn bài hoặc Ctrl+V để dán từ Word/Facebook…',
 fontNames:['Arial','Tahoma','Times New Roman','Calibri','Verdana'],fontNamesIgnoreCheck:['Arial','Tahoma','Calibri'],
 toolbar:[['style',['style']],['font',['bold','italic','underline','clear']],['fontname',['fontname']],['fontsize',['fontsize']],['color',['color']],['para',['ul','ol','paragraph']],['table',['table']],['insert',['link','hr']],['view',['fullscreen','codeview','help']]],
 callbacks:{onChange:notify,onKeydown(e){plainPaste=(e.ctrlKey||e.metaKey)&&e.shiftKey&&e.key.toLowerCase()==='v';},onPaste(event){event.preventDefault();const data=(event.originalEvent||event).clipboardData;if(data)paste(data.getData('text/html'),data.getData('text/plain'),plainPaste);plainPaste=false;},onImageUpload(){if(bridge)bridge.notice('Dùng nút Thêm ảnh để đính kèm ảnh tuyển dụng.');}}});
window.editorApi={snapshot,cleanHTML,plainHTML,paste,
 setContent(html,version){if(typeof version==='number')generation=version;programmatic++;try{$('#editor').summernote('code',cleanHTML(html,/qrichtext|-qt-/i.test(html)));$('#editor').summernote('commit');}finally{programmatic--;}return snapshot();},
 command(name,value){$('#editor').summernote(name,value);return snapshot();},
 placeholder(value){$('.note-placeholder').text(value);},
 focus(){$('#editor').summernote('focus');},
 resize(){if(!$('.note-editor').hasClass('fullscreen'))$('.note-editable').css('height',Math.max(180,innerHeight-$('.note-toolbar').outerHeight()-8)+'px');}
};
window.addEventListener('resize',()=>window.editorApi.resize());window.editorApi.resize();
if(typeof qt!=='undefined'&&typeof QWebChannel!=='undefined')new QWebChannel(qt.webChannelTransport,channel=>{bridge=channel.objects.editorBridge;bridge.loaded();});
})();
