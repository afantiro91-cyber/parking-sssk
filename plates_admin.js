// Jednostavan JS za plates_admin.html
// - Dohvaća listu tablica
// - Omogućava dodavanje/azuriranje/brisanje

async function fetchPlates(){
  const res = await fetch('/api/plates');
  const j = await res.json();
  return j.plates || [];
}

function renderSpots(selectEl){
  selectEl.innerHTML='';
  for(let i=1;i<=15;i++){
    const opt=document.createElement('option'); opt.value=i; opt.textContent=i; selectEl.appendChild(opt);
  }
}

function renderList(plates){
  const ul=document.getElementById('platesList'); ul.innerHTML='';
  if(!plates.length){ ul.innerHTML='<li>Još nema spremljenih tablica.</li>'; return }
  plates.sort((a,b)=>a.spot-b.spot);
  for(const p of plates){
    const li=document.createElement('li'); li.textContent = `#${p.spot} → ${p.plate}`; ul.appendChild(li);
  }
}

async function refresh(){
  const plates = await fetchPlates();
  renderList(plates);
}

async function addOrUpdate(){
  const plate = document.getElementById('plateInput').value.trim();
  const spot = parseInt(document.getElementById('spotSelect').value,10);
  if(!plate){ alert('Unesite tablicu!'); return }
  // PUT /api/plates/<spot>
  const res = await fetch(`/api/plates/${spot}`, {method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({plate})});
  const j = await res.json(); if(!j.success){ alert('Greška: '+(j.message||'')) }
  await refresh();
}

async function remove(){
  const spot = parseInt(document.getElementById('spotSelect').value,10);
  const res = await fetch(`/api/plates/${spot}`, {method:'DELETE'});
  const j = await res.json(); if(!j.success){ alert('Greška: '+(j.message||'')) }
  await refresh();
}

async function initPop(){
  if(!confirm('Ovo će zamijeniti postojeće tablice. Nastaviti?')) return;
  // Prompt user to enter 15 plates quickly (simple sequence or leave blank placeholders)
  const plates = [];
  for(let i=1;i<=15;i++){
    const val = prompt(`Unesite tablicu za mjesto #${i} (ostavite prazno za "MJESTO${i}")`,'');
    plates.push({spot:i, plate: val? val : `MJESTO${i}`});
  }
  const res = await fetch('/api/plates', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({plates})});
  const j = await res.json(); if(!j.success){ alert('Greška: '+(j.message||'')) }
  await refresh();
}

async function downloadJSON(){
  const plates = await fetchPlates();
  const a=document.createElement('a'); a.href = 'data:application/json;charset=utf-8,'+encodeURIComponent(JSON.stringify(plates, null, 2));
  a.download='plates_data.json'; a.click();
}

window.addEventListener('load', async ()=>{
  renderSpots(document.getElementById('spotSelect'));
  document.getElementById('addBtn').addEventListener('click', addOrUpdate);
  document.getElementById('removeBtn').addEventListener('click', remove);
  document.getElementById('refreshBtn').addEventListener('click', refresh);
  document.getElementById('initBtn').addEventListener('click', initPop);
  document.getElementById('downloadBtn').addEventListener('click', downloadJSON);
  await refresh();
});