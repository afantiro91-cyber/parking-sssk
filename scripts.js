const TOTAL_SPOTS = 5;
let slobodnaMjesta = TOTAL_SPOTS;
let invalidMjesta = 1;
let reservationCounter = 0;

const form = document.getElementById('uploadForm');
const qrDiv = document.getElementById('qrKod');
const statusDiv = document.getElementById('status');
const slobodnaSpan = document.getElementById('slobodna');
const progressBar = document.getElementById('progressBar');
const dingSound = document.getElementById('dingSound');
const rezervisiBtn = document.getElementById('rezervisiBtn');

// Load data from localStorage on page load
function loadData(){
    const s=localStorage.getItem('parkingData');
    if(!s) return;
    const d=JSON.parse(s);
    slobodnaMjesta=d.slobodnaMjesta||slobodnaMjesta;
    invalidMjesta=d.invalidMjesta||invalidMjesta;
    reservationCounter=d.reservationCounter||reservationCounter;
    updateDisplay();
}

// Save data to localStorage
function saveData(){
    localStorage.setItem('parkingData',JSON.stringify({slobodnaMjesta,invalidMjesta,reservationCounter}));
}

// Update display elements
function setDisabled(state){
    rezervisiBtn.disabled=state;
    rezervisiBtn.style.background=state?'#aaa':'#ff6600';
}

function updateDisplay(){
    slobodnaSpan.textContent=slobodnaMjesta;
    progressBar.max=TOTAL_SPOTS; progressBar.value=TOTAL_SPOTS-slobodnaMjesta;
    setDisabled(slobodnaMjesta<=0);
}

// Load data on page start
loadData();

form.addEventListener("submit", function (e) {
    e.preventDefault();

    const tipMjesta = document.getElementById("tipMjesta").value;
    const fileInput = document.getElementById("nalaz");

  if(fileInput.files.length===0){ alert('Molimo uploaduj sliku ili nalaz!'); return }
  const file=fileInput.files[0],maxSize=5*1024*1024;
  if(file.size>maxSize){ alert('Fajl je prevelik! Maksimalno 5MB.'); return }
  if(slobodnaMjesta<=0){ statusDiv.textContent='🚫 Sva mjesta su zauzeta!'; statusDiv.style.color='#ff3333'; setDisabled(true); return }
  if(tipMjesta==='invalid'&&invalidMjesta<=0){ statusDiv.textContent='🚫 Sva invalidska mjesta su zauzeta!'; statusDiv.style.color='#ff3333'; return }

  reservationCounter++; const timestamp=new Date().getTime();
  const qrValue=`Parking-${tipMjesta.toUpperCase()}-${reservationCounter}-${timestamp}`;
  const canvas=document.createElement('canvas'); new QRious({element:canvas,value:qrValue,size:200});
  qrDiv.innerHTML="<p style='color: #ffcc00; margin: 0 0 10px 0;'>Vaš QR kod:</p>"; qrDiv.appendChild(canvas);

  if(tipMjesta==='invalid') invalidMjesta--;
  slobodnaMjesta--; updateDisplay(); saveData();
  dingSound.play(); statusDiv.textContent=`✅ Mjesto (${tipMjesta}) je uspješno rezervisano!`; statusDiv.style.color='#00ff00';
  fileInput.value=''; if(slobodnaMjesta===0){ statusDiv.textContent='🚫 Sva mjesta su sada zauzeta!'; statusDiv.style.color='#ff3333'; setDisabled(true) }
});
