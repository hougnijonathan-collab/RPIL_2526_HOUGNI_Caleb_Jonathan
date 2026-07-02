const form = document.getElementById("search-form");
const matieresInput = document.getElementById("matieres");
const suggestionsBox = document.getElementById("matieres-suggestions");

const resultsSection = document.getElementById("results-section");
const resultsList = document.getElementById("results-list");
const resultsCount = document.getElementById("results-count");
const emptyState = document.getElementById("empty-state");
const errorState = document.getElementById("error-state");
const errorText = document.getElementById("error-text");
const submitBtn = form.querySelector("button[type='submit']");

// -----------------------------------------------------------------------
// Charger les matières existantes pour aider la saisie (chips cliquables)
// -----------------------------------------------------------------------
async function chargerSuggestions() {
  try {
    const res = await fetch("/api/matieres");
    const matieres = await res.json();
    suggestionsBox.innerHTML = "";
    matieres.forEach((matiere) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "suggestion-chip";
      chip.textContent = matiere;
      chip.addEventListener("click", () => {
        const current = matieresInput.value
          .split(",")
          .map((m) => m.trim())
          .filter(Boolean);
        if (!current.includes(matiere)) {
          current.push(matiere);
          matieresInput.value = current.join(", ");
        }
      });
      suggestionsBox.appendChild(chip);
    });
  } catch (e) {
    // Silencieux : les suggestions sont un simple confort, pas bloquant
  }
}

function formatLabelFormat(format) {
  switch (format) {
    case "presentiel": return "Présentiel";
    case "en_ligne": return "En ligne";
    case "les_deux": return "Présentiel ou en ligne";
    default: return format;
  }
}

function afficherResultats(data) {
  resultsList.innerHTML = "";

  if (data.nombre_resultats === 0) {
    resultsSection.classList.add("hidden");
    emptyState.classList.remove("hidden");
    return;
  }

  emptyState.classList.add("hidden");
  resultsSection.classList.remove("hidden");
  resultsCount.textContent = `${data.nombre_resultats} résultat${data.nombre_resultats > 1 ? "s" : ""}`;

  data.resultats.forEach((mentor) => {
    const card = document.createElement("div");
    card.className = "mentor-card";

    const tags = mentor.matieres_communes
      .map((m) => `<span class="tag">${m}</span>`)
      .join("");

    card.innerHTML = `
      <div>
        <p class="mentor-name">${mentor.nom}</p>
        <div class="mentor-meta">
          <div>${tags}</div>
          <div><strong>Disponibilité :</strong> ${mentor.disponibilites}</div>
          <div><strong>Format :</strong> ${formatLabelFormat(mentor.format_mentorat)} &middot; <strong>Filière :</strong> ${mentor.filiere}</div>
        </div>
      </div>
      <div class="score-badge">
        <div class="score-number">${mentor.score}</div>
        <div class="score-label">Compatibilité</div>
      </div>
    `;
    resultsList.appendChild(card);
  });
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  errorState.classList.add("hidden");
  emptyState.classList.add("hidden");
  resultsSection.classList.add("hidden");

  submitBtn.disabled = true;
  submitBtn.textContent = "Recherche en cours...";

  const payload = {
    matieres: matieresInput.value,
    heure: document.getElementById("heure").value,
    filiere: document.getElementById("filiere").value,
  };

  try {
    const res = await fetch("/api/rechercher", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (!res.ok) {
      errorText.textContent = data.erreur || "Une erreur est survenue.";
      errorState.classList.remove("hidden");
    } else {
      afficherResultats(data);
    }
  } catch (err) {
    errorText.textContent = "Impossible de contacter le serveur. Réessayez.";
    errorState.classList.remove("hidden");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Rechercher un mentor";
  }
});

chargerSuggestions();
