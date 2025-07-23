function toggleSelected(btn) {
  btn.classList.toggle('selected');
}

function getCurrentDate() {
  const options = { weekday: 'long', day: 'numeric', month: 'numeric', year: 'numeric' };
  return new Date().toLocaleDateString('de-DE', options);
}

function updateDateTime() {
  const dateElements = document.querySelectorAll('.date');
  dateElements.forEach(el => {
    el.textContent = getCurrentDate();
  });
}

// Bei Seitenladung das Datum aktualisieren
document.addEventListener('DOMContentLoaded', function() {
  updateDateTime();
  
  // Starte die News-Bilder Animation nur auf der Startseite
  if (window.location.pathname === '/' || window.location.pathname === '/start') {
    initNewsImagesAnimation();
  }
  
  // Für Feed-Seite: Keine Artikel-Daten mehr erforderlich, da keine Karussell-Funktionalität
});

// News Images Animation
let newsImages = [];
let currentLeftIndex = 0;
let currentRightIndex = 1;

async function initNewsImagesAnimation() {
  try {
    const response = await fetch('/api/news-images');
    const data = await response.json();
    
    if (data.success && data.images.length > 0) {
      newsImages = data.images;
      startImageRotation();
    }
  } catch (error) {
    console.error('Error loading news images:', error);
  }
}

function startImageRotation() {
  if (newsImages.length === 0) return;
  
  const leftImage = document.getElementById('leftImage');
  const rightImage = document.getElementById('rightImage');
  
  if (!leftImage || !rightImage) return;
  
  // Initiale Bilder setzen
  updateImages();
  
  // Rotation alle 3.5 Sekunden
  setInterval(() => {
    updateImages();
  }, 3500);
}

function updateImages() {
  const leftImage = document.getElementById('leftImage');
  const rightImage = document.getElementById('rightImage');
  const leftTitle = document.getElementById('leftTitle');
  const rightTitle = document.getElementById('rightTitle');
  
  if (!leftImage || !rightImage || !leftTitle || !rightTitle || newsImages.length === 0) return;
  
  // Linke Seite: Gerade Indizes (0, 2, 4, 6, ...)
  const leftImageData = newsImages[currentLeftIndex * 2];
  if (leftImageData) {
    leftImage.classList.remove('active');
    leftTitle.classList.remove('active');
    setTimeout(() => {
      leftImage.src = leftImageData.url;
      leftImage.alt = leftImageData.title;
      leftTitle.textContent = leftImageData.title;
      leftImage.classList.add('active');
      leftTitle.classList.add('active');
    }, 200);
  }
  
  // Rechte Seite: Ungerade Indizes (1, 3, 5, 7, ...)
  const rightImageData = newsImages[currentRightIndex * 2 + 1];
  if (rightImageData) {
    rightImage.classList.remove('active');
    rightTitle.classList.remove('active');
    setTimeout(() => {
      rightImage.src = rightImageData.url;
      rightImage.alt = rightImageData.title;
      rightTitle.textContent = rightImageData.title;
      rightImage.classList.add('active');
      rightTitle.classList.add('active');
    }, 200);
  }
  
  // Indizes für nächstes Bild aktualisieren
  currentLeftIndex = (currentLeftIndex + 1) % Math.floor(newsImages.length / 2);
  currentRightIndex = (currentRightIndex + 1) % Math.floor(newsImages.length / 2);
}

// Funktionen für Flask-Integration
function collectSelectedCategories() {
  const selectedCategories = [];
  document.querySelectorAll('.category-buttons .option-button.selected').forEach(button => {
    selectedCategories.push(button.getAttribute('data-value'));
  });
  return selectedCategories;
}

function collectSelectedFormat() {
  const formatElement = document.querySelector('.format-buttons .option-button.selected');
  return formatElement ? formatElement.getAttribute('data-value') : null;
}

function collectUserData() {
  const ageGroup = document.querySelector('.age-buttons .option-button.selected')?.getAttribute('data-value');
  const gender = document.querySelector('.gender-buttons .option-button.selected')?.getAttribute('data-value');
  const language = document.getElementById('lang')?.value;
  const dialect = document.getElementById('dialect')?.value;
  
  return {
    ageGroup: ageGroup,
    gender: gender,
    language: language,
    dialect: dialect
  };
}

function submitForm(formType) {
  let formData = new FormData();
  
  if (formType === 'user-info') {
    const userData = collectUserData();
    formData.append('age_group', userData.ageGroup || '');
    formData.append('gender', userData.gender || '');
    formData.append('language', userData.language || '');
    formData.append('dialect', userData.dialect || '');
    
    fetch('/submit-user-info', {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if(data.success) {
        window.location.href = '/categories';
      }
    });
  } 
  else if (formType === 'categories') {
    const categories = collectSelectedCategories();
    const format = collectSelectedFormat();
    
    formData.append('categories', JSON.stringify(categories));
    formData.append('format', format || '');
    
    fetch('/submit-categories', {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if(data.success) {
        window.location.href = '/feed';
      }
    });
  }
}
