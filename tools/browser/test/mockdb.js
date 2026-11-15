(function(){
 var store={}, subs=[];
 function notify(){subs.forEach(function(s){s()})}
 function snapDoc(id,d){return {id:id,exists:!!d,data:function(){return d},metadata:{fromCache:false,hasPendingWrites:false}}}
 function docRef(path){return {id:path.split('/').pop(),path:path,
   get:async function(){return snapDoc(this.id,store[path])},
   set:async function(d){store[path]=JSON.parse(JSON.stringify(d));notify()},
   delete:async function(){delete store[path];notify()},
   update:async function(d){if(!store[path]){var e=new Error('missing');e.code='invalid_argument';throw e}Object.assign(store[path],d);notify()}}}
 function coll(path){var q={field:null,dir:'asc',lim:1000};var api={
   orderBy:function(f,d){q.field=f;q.dir=d||'asc';return api},limit:function(n){q.lim=n;return api},
   onSnapshot:function(next){var run=function(){var docs=Object.keys(store).filter(function(k){return k.indexOf(path+'/')===0}).map(function(k){return snapDoc(k.split('/').pop(),store[k])});
       if(q.field)docs.sort(function(a,b){var x=a.data()[q.field],y=b.data()[q.field];return (x<y?-1:x>y?1:0)*(q.dir==='desc'?-1:1)});
       next({docs:docs.slice(0,q.lim),size:docs.length,empty:!docs.length,metadata:{fromCache:false}})};subs.push(run);setTimeout(run,10);return function(){}},
   doc:function(id){return docRef(path+'/'+id)}};return api}
 window.__mockdb={doc:docRef,collection:coll}; window.__store=store;
})();
