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
});

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
