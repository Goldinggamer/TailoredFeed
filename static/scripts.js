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

// === INDEX PAGE SPECIFIC FUNCTIONALITY ===
// Multi-Select Dropdown functionality für die Startseite

let selectedCategories = [];

// Funktion zur Initialisierung der Multi-Select Dropdown-Funktionalität
function initializeMultiSelectDropdown() {
    const dropdown = document.getElementById('categoriesDropdown');
    const options = document.getElementById('categoriesOptions');
    const arrow = document.getElementById('dropdownArrow');
    const selectedText = document.getElementById('selectedCategories');
    const customSearchContainer = document.getElementById('customSearchContainer');
    const limitMessage = document.getElementById('categories-limit');
    
    // Nur ausführen wenn die Elemente existieren (Startseite)
    if (!dropdown || !options || !arrow || !selectedText) {
        return;
    }
    
    // Toggle dropdown
    dropdown.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const isOpen = options.style.display === 'block';
        options.style.display = isOpen ? 'none' : 'block';
        arrow.classList.toggle('open', !isOpen);
        dropdown.classList.toggle('active', !isOpen);
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!dropdown.contains(e.target) && !options.contains(e.target)) {
            options.style.display = 'none';
            arrow.classList.remove('open');
            dropdown.classList.remove('active');
        }
    });
    
    // Handle category selection
    document.querySelectorAll('.multi-select-option').forEach(option => {
        const checkbox = option.querySelector('input[type="checkbox"]');
        const label = option.querySelector('label');
        
        // Handle clicks on the entire option div
        option.addEventListener('click', function(e) {
            e.stopPropagation();
            
            // Don't double-toggle if clicking directly on checkbox
            if (e.target.type !== 'checkbox') {
                checkbox.checked = !checkbox.checked;
            }
            
            handleCategoryChange(option, checkbox);
        });
        
        // Handle direct checkbox clicks
        checkbox.addEventListener('change', function(e) {
            e.stopPropagation();
            handleCategoryChange(option, checkbox);
        });
        
        // Handle label clicks
        label.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            checkbox.checked = !checkbox.checked;
            handleCategoryChange(option, checkbox);
        });
    });
    
    function handleCategoryChange(option, checkbox) {
        const value = option.dataset.value;
        
        if (checkbox.checked) {
            if (selectedCategories.length >= 2) {
                checkbox.checked = false;
                limitMessage.style.display = 'block';
                setTimeout(() => {
                    limitMessage.style.display = 'none';
                }, 3000);
                return;
            }
            selectedCategories.push(value);
            option.classList.add('selected');
        } else {
            selectedCategories = selectedCategories.filter(cat => cat !== value);
            option.classList.remove('selected');
            limitMessage.style.display = 'none';
        }
        
        updateSelectedDisplay();
        
        // Show/hide custom search input
        if (selectedCategories.includes('custom')) {
            customSearchContainer.style.display = 'block';
        } else {
            customSearchContainer.style.display = 'none';
            document.getElementById('custom-search-input').value = '';
        }
    }
    
    function updateSelectedDisplay() {
        const categoryNames = {
            'politik': 'Politik',
            'wissenschaft': 'Wissenschaft',
            'wissenswertes': 'Wissenswertes',
            'wirtschaft': 'Wirtschaft',
            'gesundheit': 'Gesundheit',
            'muenchen': 'München',
            'technologie': 'Technologie',
            'sport': 'Sport',
            'custom': 'Custom Suche'
        };
        
        if (selectedCategories.length === 0) {
            selectedText.textContent = 'Bitte wählen';
            selectedText.classList.add('placeholder');
        } else {
            const names = selectedCategories.map(cat => categoryNames[cat]);
            selectedText.textContent = names.join(', ');
            selectedText.classList.remove('placeholder');
        }
    }
}

// Form-Validierung und Submission für die Startseite
function initializeFormSubmission() {
    const form = document.getElementById('userInfoForm');
    
    // Nur ausführen wenn das Formular existiert (Startseite)
    if (!form) {
        return;
    }
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Reset error messages
        document.querySelectorAll('.error-message').forEach(msg => msg.style.display = 'none');
        
        // Get form values
        const complexityLevel = document.getElementById('complexity_level').value;
        const language = document.getElementById('language').value;
        const format = document.getElementById('format').value;
        const customSearchTerm = document.getElementById('custom-search-input').value.trim();
        
        // Validation
        let hasError = false;
        
        if (!complexityLevel) {
            document.getElementById('complexity-error').style.display = 'block';
            hasError = true;
        }
        if (!language) {
            document.getElementById('language-error').style.display = 'block';
            hasError = true;
        }
        if (selectedCategories.length === 0) {
            document.getElementById('categories-error').style.display = 'block';
            hasError = true;
        }
        if (selectedCategories.includes('custom') && !customSearchTerm) {
            document.getElementById('custom-search-error').style.display = 'block';
            hasError = true;
        }
        if (!format) {
            document.getElementById('format-error').style.display = 'block';
            hasError = true;
        }
        
        if (hasError) return;
        
        // Submit form data and redirect to generating news
        fetch('/submit-complete-user-info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                complexity_level: complexityLevel,
                language: language,
                categories: selectedCategories,
                format: format,
                custom_search_term: customSearchTerm
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = '/generating_news';
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ein Fehler ist aufgetreten. Bitte versuche es erneut.');
        });
    });
}

// Funktion zur Initialisierung aller Index-spezifischen Features
function initializeIndexPage() {
    initializeMultiSelectDropdown();
    initializeFormSubmission();
}

// === GENERATING NEWS PAGE SPECIFIC FUNCTIONALITY ===
// News-Generierungs-Funktionalität für die generating_news Seite

function initializeGeneratingNewsPage() {
    // Nur ausführen wenn wir auf der generating_news Seite sind
    if (window.location.pathname !== '/generating_news') {
        return;
    }
    
    // News generieren
    fetch('/generate_news')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Animation beenden und Erfolg anzeigen
                const loadingCircle = document.getElementById('loadingCircle');
                const successIcon = document.getElementById('successIcon');
                const statusText = document.getElementById('statusText');
                
                if (loadingCircle) loadingCircle.style.display = 'none';
                if (successIcon) successIcon.style.display = 'block';
                if (statusText) statusText.textContent = 'Deine News wurden erfolgreich generiert!';
                
                // Automatischer Redirect nach 0.5 Sekunden
                setTimeout(() => {
                    window.location.href = '/feed';
                }, 500);
                
            } else {
                throw new Error(data.error || 'Ein Fehler ist aufgetreten');
            }
        })
        .catch(error => {
            const loadingCircle = document.getElementById('loadingCircle');
            const statusText = document.getElementById('statusText');
            
            if (loadingCircle) loadingCircle.style.display = 'none';
            if (statusText) {
                statusText.textContent = 'Fehler: ' + error.message;
                statusText.style.color = '#ff4444';
            }
        });
}

// === UPDATE NEWS PAGE SPECIFIC FUNCTIONALITY ===
// News-Update-Funktionalität für die update_news Seite

async function startUpdate() {
    const updateBtn = document.getElementById('updateButton');
    const loading = document.getElementById('loading');
    const apiStatus = document.getElementById('apiStatus');
    const dbStatus = document.getElementById('dbStatus');
    const continueButton = document.getElementById('continueButton');
    
    updateBtn.style.display = 'none';
    loading.style.display = 'block';
    
    try {
        // Start API News update
        const apiResponse = await fetch('/update_api_news');
        if (apiResponse.ok) {
            apiStatus.style.display = 'block';
            
            // Start Database update
            const dbResponse = await fetch('/update_database');
            if (dbResponse.ok) {
                dbStatus.style.display = 'block';
                continueButton.style.display = 'inline-block';
            }
        }
    } catch (error) {
        console.error('Error:', error);
    }
    
    loading.style.display = 'none';
}

function initializeUpdateNewsPage() {
    // Nur ausführen wenn wir auf der update_news Seite sind
    if (window.location.pathname !== '/update_news') {
        return;
    }
    
    // startUpdate Funktion global verfügbar machen
    window.startUpdate = startUpdate;
}

// Bei Seitenladung das Datum aktualisieren und spezifische Features laden
document.addEventListener('DOMContentLoaded', function() {
  updateDateTime();
  
  // Prüfen welche Seite geladen wird und entsprechende Features initialisieren
  if (window.location.pathname === '/' || window.location.pathname === '/start') {
    initNewsImagesAnimation();
    initializeIndexPage(); // Index-spezifische Features
  } else if (window.location.pathname === '/generating_news') {
    initializeGeneratingNewsPage(); // Generating News-spezifische Features
  } else if (window.location.pathname === '/update_news') {
    initializeUpdateNewsPage(); // Update News-spezifische Features
  }
});
