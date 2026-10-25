'use strict';
const base=document.body.dataset.base;
const route=document.body.dataset.route;
const $=s=>document.querySelector(s);
let navPromise,indexPromise;
const loadJSON=async name=>{const r=await fetch(base+'assets/'+name+'.json');if(!r.ok)throw Error('加载失败，请稍后重试');return r.json()};
function drawer(open){document.body.classList.toggle('drawer-open',open);$('#menu-toggle').setAttribute('aria-expanded',String(open));$('#drawer-shade').hidden=!open}
$('#menu-toggle').addEventListener('click',()=>drawer(!document.body.classList.contains('drawer-open')));
$('#drawer-shade').addEventListener('click',()=>drawer(false));
document.querySelectorAll('.expand').forEach(button=>button.addEventListener('click',async()=>{
 const box=document.getElementById(button.getAttribute('aria-controls'));const open=button.getAttribute('aria-expanded')!=='true';button.setAttribute('aria-expanded',String(open));box.hidden=!open;
 if(open&&!box.children.length){try{const lessons=await(navPromise??=loadJSON('navigation'));const lesson=lessons.find(l=>l.number===Number(button.dataset.lesson));lesson.sections.forEach(s=>{const a=document.createElement('a');a.href=base+s.route;const n=document.createElement('span');n.textContent=String(s.section).padStart(2,'0');a.append(n,document.createTextNode(s.title));box.append(a)})}catch(error){box.textContent=error.message;navPromise=null}}
}));
let font=Number(localStorage.getItem('nju-os-font'))||18;
function setFont(value){font=Math.min(24,Math.max(15,value));document.documentElement.style.setProperty('--body-size',font+'px');localStorage.setItem('nju-os-font',font)}
setFont(font);$('#font-down').onclick=()=>setFont(font-1);$('#font-up').onclick=()=>setFont(font+1);
const last=JSON.parse(localStorage.getItem('nju-os-last')||'null');
if(!route&&last&&/^lessons\/\d{2}\/\d{3}\.html$/.test(last.route)){const c=$('#continue-reading');c.href=base+last.route+'#resume';c.hidden=false}
if(route){let timer;const save=()=>{const y=window.scrollY/(document.documentElement.scrollHeight-innerHeight||1);$('#scroll-progress').style.width=(100*y)+'%';clearTimeout(timer);timer=setTimeout(()=>localStorage.setItem('nju-os-last',JSON.stringify({route,progress:y})),400)};window.addEventListener('scroll',save,{passive:true});if(location.hash==='#resume'&&last?.route===route)window.addEventListener('load',()=>setTimeout(()=>window.scrollTo(0,last.progress*(document.documentElement.scrollHeight-innerHeight)),150));else localStorage.setItem('nju-os-last',JSON.stringify({route,progress:0}));const active=$('.nav-sections a[aria-current]');if(active)active.scrollIntoView({block:'center'})}
document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>document.getElementById(b.dataset.close).close());
document.querySelectorAll('dialog').forEach(d=>d.addEventListener('click',event=>{if(event.target===d){const r=d.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)d.close()}}));
const search=$('#search-dialog'),input=$('#search-input'),results=$('#search-results'),status=$('#search-status');
function openSearch(){search.showModal();input.focus();indexPromise??=loadJSON('search');indexPromise.catch(()=>{status.textContent='搜索加载失败，请重新打开搜索重试。';indexPromise=null})}
$('#search-open').onclick=openSearch;
document.addEventListener('keydown',event=>{if((event.metaKey||event.ctrlKey)&&event.key.toLowerCase()==='k'){event.preventDefault();if(!search.open)openSearch()}if(event.key==='Escape')drawer(false)});
let queryId=0,searchTimer;
function highlight(node,text,query){const lower=text.toLowerCase(),needle=query.toLowerCase();let start=0,idx;while((idx=lower.indexOf(needle,start))!==-1){node.append(document.createTextNode(text.slice(start,idx)));const m=document.createElement('mark');m.textContent=text.slice(idx,idx+query.length);node.append(m);start=idx+query.length}node.append(document.createTextNode(text.slice(start)))}
input.addEventListener('input',()=>{clearTimeout(searchTimer);const id=++queryId;searchTimer=setTimeout(async()=>{const q=input.value.trim();results.replaceChildren();if(!q){status.textContent='输入关键词，搜索全部 30 节课。';return}status.textContent='搜索中…';try{const index=await(indexPromise??=loadJSON('search'));if(id!==queryId)return;const needle=q.toLowerCase();const found=index.map(u=>({u,pos:u.text.toLowerCase().indexOf(needle),title:u.title.toLowerCase().includes(needle)})).filter(x=>x.pos>=0||x.title||x.u.lessonTitle.toLowerCase().includes(needle)).sort((a,b)=>Number(b.title)-Number(a.title));status.textContent=`找到 ${found.length} 个小节${found.length>40?'，显示前 40 项':''}`;for(const{u,pos}of found.slice(0,40)){const a=document.createElement('a');a.href=base+u.route;const small=document.createElement('small');small.textContent=`第 ${String(u.lesson).padStart(2,'0')} 课 · ${u.lessonTitle}`;const strong=document.createElement('strong');highlight(strong,u.title,q);const p=document.createElement('p');const start=Math.max(0,pos-40);highlight(p,(start?'…':'')+u.text.slice(start,start+150)+'…',q);a.append(small,strong,p);results.append(a)}}catch(error){status.textContent=error.message;indexPromise=null}},180)});
const imageDialog=$('#image-dialog'),zoom=$('#zoom-image');
function openImage(img){zoom.src=img.src;zoom.alt=img.alt;$('.image-scroll').classList.remove('expanded');$('#zoom-caption').textContent=img.alt+' · 点击图片查看原始尺寸';imageDialog.showModal()}
document.querySelectorAll('.prose img').forEach(img=>{img.addEventListener('click',()=>openImage(img));img.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();openImage(img)}})});
zoom.onclick=()=>$('.image-scroll').classList.toggle('expanded');
