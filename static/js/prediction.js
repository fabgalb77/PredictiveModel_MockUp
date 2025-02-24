let currentPatientId = "";
let predictionsData = null;

function init(patientId) {
    currentPatientId = patientId;
}

function requestRecommendation() {
    const recommendButton = document.getElementById("recommendButton");
    recommendButton.disabled = true;
    recommendButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';

    fetch(`/surgical_recommendation/${currentPatientId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Update surgery selections
            Object.entries(data.recommended_surgery).forEach(([level, surgery]) => {
                if (level === "pelvic_fixation") {
                    document.getElementById("pelvicFixation").checked = surgery;
                } else {
                    document.getElementById(`surgery_${level}`).value = surgery;
                }
            });
            
            // Enable prediction button only if there's at least one surgery
            const hasSurgery = checkForSurgicalIntervention();
            document.getElementById("predictButton").disabled = !hasSurgery;
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`Failed to load recommendation: ${error.message}`);
        })
        .finally(() => {
            // Reset recommend button
            recommendButton.disabled = false;
            recommendButton.innerHTML = 'Recommend Surgery';
        });
}

function updateSurgery() {
    // Check if any surgery is selected
    const hasSurgery = checkForSurgicalIntervention();
    
    // Enable prediction button only if there's at least one surgery
    const predictButton = document.getElementById("predictButton");
    predictButton.disabled = !hasSurgery;
    
    // Clear existing predictions if enabled
    if (hasSurgery) {
        clearPredictions();
    }
}

function checkForSurgicalIntervention() {
    // Check all spinal levels
    const levels = ["T12-L1", "L1-L2", "L2-L3", "L3-L4", "L4-L5", "L5-S1"];
    const hasSpinalSurgery = levels.some(level => 
        document.getElementById(`surgery_${level}`).value !== "no_surgery"
    );
    
    // Check pelvic fixation
    const hasPelvicFixation = document.getElementById("pelvicFixation").checked;
    
    // Return true if there's any intervention
    return hasSpinalSurgery || hasPelvicFixation;
}

function clearPredictions() {
    document.getElementById("predictions").classList.add("disabled-overlay");
    document.querySelectorAll(".prediction-value").forEach(el => el.textContent = "-");
    document.querySelectorAll(".confidence-text").forEach(el => el.textContent = "-");
    document.querySelectorAll(".confidence-range").forEach(el => el.style.width = "0%");
    document.querySelectorAll(".confidence-value").forEach(el => el.style.left = "0%");
    document.querySelector(".progress-bar").style.width = "0%";
}

function predictOutcome() {
    const predictButton = document.getElementById("predictButton");
    predictButton.disabled = true;
    predictButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';

    // Collect current surgery plan
    const surgeryPlan = {
        "T12-L1": document.getElementById("surgery_T12-L1").value,
        "L1-L2": document.getElementById("surgery_L1-L2").value,
        "L2-L3": document.getElementById("surgery_L2-L3").value,
        "L3-L4": document.getElementById("surgery_L3-L4").value,
        "L4-L5": document.getElementById("surgery_L4-L5").value,
        "L5-S1": document.getElementById("surgery_L5-S1").value,
        "pelvic_fixation": document.getElementById("pelvicFixation").checked
    };
    
    // Get predictions for current plan
    fetch(`/predict_outcome/${currentPatientId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(surgeryPlan)
    })
    .then(response => response.json())
    .then(data => {
        predictionsData = data;
        updatePredictionDisplay();
        predictButton.disabled = false;
        predictButton.innerHTML = 'Predict Outcome';
    })
    .catch(error => {
        console.error('Error:', error);
        predictButton.disabled = false;
        predictButton.innerHTML = 'Predict Outcome';
    });
}

function updatePredictionDisplay() {
    // Remove disabled overlay
    document.getElementById("predictions").classList.remove("disabled-overlay");
    
    // Update each prediction card
    updatePredictionCard("comiTotal", predictionsData.comi_total);
    updatePredictionCard("backPain", predictionsData.back_pain);
    updatePredictionCard("legPain", predictionsData.leg_pain);
    updatePredictionCard("function", predictionsData.function);
    updatePredictionCard("qualityOfLife", predictionsData.quality_of_life);
    updatePredictionCard("socialDisability", predictionsData.social_disability);
    updatePredictionCard("workDisability", predictionsData.work_disability);
    
    // Update complications risk with progress bar
    const riskData = predictionsData.complications_risk;
    const riskElement = document.getElementById("complicationsRisk");
    const progressBar = riskElement.nextElementSibling.querySelector(".progress-bar");
    const confidenceText = riskElement.parentElement.querySelector(".confidence-text");
    
    riskElement.textContent = riskData.value.toFixed(1) + '%';
    progressBar.style.width = riskData.value + '%';
    confidenceText.textContent = `${riskData.confidence_interval[0].toFixed(1)}% - ${riskData.confidence_interval[1].toFixed(1)}%`;
}

function updatePredictionCard(id, data) {
    const element = document.getElementById(id);
    const container = element.parentElement;
    const confidenceBar = container.querySelector(".confidence-bar");
    const confidenceRange = confidenceBar.querySelector(".confidence-range");
    const confidenceValue = confidenceBar.querySelector(".confidence-value");
    const confidenceText = container.querySelector(".confidence-text");
    
    // Update value
    element.textContent = data.value.toFixed(1);
    
    // Update confidence interval visualization
    const min = 0;
    const max = 10;
    const rangeStart = ((data.confidence_interval[0] - min) / (max - min)) * 100;
    const rangeEnd = ((data.confidence_interval[1] - min) / (max - min)) * 100;
    const valuePosition = ((data.value - min) / (max - min)) * 100;
    
    confidenceRange.style.left = rangeStart + '%';
    confidenceRange.style.width = (rangeEnd - rangeStart) + '%';
    confidenceValue.style.left = valuePosition + '%';
    
    confidenceText.textContent = `${data.confidence_interval[0].toFixed(1)} - ${data.confidence_interval[1].toFixed(1)}`;
}