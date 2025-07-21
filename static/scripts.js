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
  
  // Initialisiere Artikel-Daten für Feed-Seite
  if (window.location.pathname === '/feed') {
    initializeArticleData();
  }
});

// Artikel-Daten global speichern
let categoryArticles = {};

function initializeArticleData() {
  const categoryBlocks = document.querySelectorAll('.category-block');
  
  categoryBlocks.forEach((block, index) => {
    const articleDataScript = block.querySelector('.article-data');
    if (articleDataScript) {
      try {
        const articles = JSON.parse(articleDataScript.textContent);
        categoryArticles[index] = {
          articles: articles,
          currentIndex: 0
        };
      } catch (e) {
        console.error('Error parsing article data:', e);
      }
    }
  });
}

function nextArticle(categoryIndex) {
  const categoryData = categoryArticles[categoryIndex];
  if (!categoryData || !categoryData.articles || categoryData.articles.length <= 1) {
    return;
  }
  
  // Nächster Artikel-Index
  categoryData.currentIndex = (categoryData.currentIndex + 1) % categoryData.articles.length;
  
  const currentArticle = categoryData.articles[categoryData.currentIndex];
  const categoryBlock = document.querySelector(`[data-category-index="${categoryIndex}"]`);
  
  if (!categoryBlock || !currentArticle) return;
  
  // Text aktualisieren mit Animation
  const textElement = categoryBlock.querySelector('.category-text');
  const imageElement = categoryBlock.querySelector('.category-image img');
  const noImageElement = categoryBlock.querySelector('.no-image');
  const counterElement = categoryBlock.querySelector('.current-article');
  
  if (textElement) {
    // Fade-out Animation
    textElement.style.opacity = '0.3';
    textElement.style.transform = 'translateX(-20px)';
    
    setTimeout(() => {
      textElement.textContent = currentArticle.content;
      
      // Fade-in Animation
      textElement.style.opacity = '1';
      textElement.style.transform = 'translateX(0)';
    }, 200);
  }
  
  // Bild aktualisieren
  if (currentArticle.images && currentArticle.images.length > 0) {
    if (imageElement) {
      imageElement.style.opacity = '0.3';
      setTimeout(() => {
        imageElement.src = currentArticle.images[0];
        imageElement.style.opacity = '1';
      }, 200);
    } else if (noImageElement) {
      // Ersetze "Kein Bild verfügbar" mit dem neuen Bild
      const categoryImage = categoryBlock.querySelector('.category-image');
      if (categoryImage) {
        categoryImage.innerHTML = `<img src="${currentArticle.images[0]}" alt="Nachrichtenbild" style="opacity: 0.3;">`;
        const newImage = categoryImage.querySelector('img');
        setTimeout(() => {
          newImage.style.opacity = '1';
        }, 200);
      }
    }
  } else {
    // Kein Bild für diesen Artikel
    if (imageElement) {
      const categoryImage = categoryBlock.querySelector('.category-image');
      if (categoryImage) {
        categoryImage.innerHTML = '<div class="no-image">Kein Bild verfügbar</div>';
      }
    }
  }
  
  // Counter aktualisieren
  if (counterElement) {
    counterElement.textContent = categoryData.currentIndex + 1;
  }
  
  // Button-Animation
  const button = categoryBlock.querySelector('.nav-arrow');
  if (button) {
    button.style.transform = 'scale(0.8) rotate(180deg)';
    setTimeout(() => {
      button.style.transform = 'scale(1) rotate(0deg)';
    }, 150);
  }
}

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
