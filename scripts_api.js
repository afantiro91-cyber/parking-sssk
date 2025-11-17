const TOTAL_SPOTS=5;
let slobodnaMjesta=TOTAL_SPOTS,invalidMjesta=1,reservationCounter=0;
const API_BASE='http://localhost:5000/api';
const form=document.getElementById('uploadForm');
const qrDiv=document.getElementById('qrKod');
const statusDiv=document.getElementById('status');
const slobodnaSpan=document.getElementById('slobodna');
const progressBar=document.getElementById('progressBar');
const dingSound=document.getElementById('dingSound');
const rezervisiBtn=document.getElementById('rezervisiBtn');

// Učitaj stanje iz servera
async function loadStatus(){
    try{
        const r=await fetch(`${API_BASE}/status`);
        if(!r.ok) return;
        const d=await r.json(); if(d.success){ slobodnaMjesta=d.data.available_total; invalidMjesta=d.data.available_invalid; updateDisplay() }
    }catch(e){ console.warn('Server nije dostupan, korištenje lokalnog stanja') }
}

// Ažuriranje prikaza
function setDisabled(state){ rezervisiBtn.disabled=state; rezervisiBtn.style.background=state?'#aaa':'#ff6600' }
function updateDisplay(){ slobodnaSpan.textContent=slobodnaMjesta; progressBar.max=TOTAL_SPOTS; progressBar.value=TOTAL_SPOTS-slobodnaMjesta; setDisabled(slobodnaMjesta<=0) }

// Rezervacija mjesta
form.addEventListener('submit',async function(e){
  e.preventDefault();
  const tipMjesta=document.getElementById('tipMjesta').value, fileInput=document.getElementById('nalaz');
  if(fileInput.files.length===0){ alert('Molimo uploaduj sliku ili nalaz!'); return }
  const file=fileInput.files[0], maxSize=5*1024*1024; if(file.size>maxSize){ alert('Fajl je prevelik! Maksimalno 5MB.'); return }
  if(slobodnaMjesta<=0){ statusDiv.textContent='🚫 Sva mjesta su zauzeta!'; statusDiv.style.color='#ff3333'; return }
  if(tipMjesta==='invalid'&&invalidMjesta<=0){ statusDiv.textContent='🚫 Sva invalidska mjesta su zauzeta!'; statusDiv.style.color='#ff3333'; return }

  try{
    const formData=new FormData(); formData.append('spot_type',tipMjesta); formData.append('user_name','Web korisnik'); formData.append('file',file);
    const r=await fetch(`${API_BASE}/reserve`,{method:'POST',body:formData});
    const result=await r.json();
    if(result.success){
      const canvas=document.createElement('canvas'); new QRious({element:canvas,value:result.qr_value,size:200}); qrDiv.innerHTML="<p style='color: #ffcc00; margin: 0 0 10px 0;'>Vaš QR kod:</p>"; qrDiv.appendChild(canvas);
      slobodnaMjesta--; if(tipMjesta==='invalid') invalidMjesta--; updateDisplay(); dingSound.play(); statusDiv.textContent=`✅ Mjesto (${tipMjesta}) je uspješno rezervisano!`; statusDiv.style.color='#00ff00'; fileInput.value=''; if(slobodnaMjesta===0) setDisabled(true);
    }else{ statusDiv.textContent=result.message; statusDiv.style.color='#ff3333' }
  }catch(err){ console.error('Greška:',err); statusDiv.textContent='❌ Greška pri komunikaciji sa serverom!'; statusDiv.style.color='#ff3333' }
});

// Učitaj stanje pri kreiranju stranice
loadStatus();
