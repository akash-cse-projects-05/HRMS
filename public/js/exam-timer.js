// public/js/exam-timer.js
// Anti-Cheat & Timed Multi-Step Exam Controller

(function() {
  let currentStep = 0;
  const steps = document.querySelectorAll('.question-step');
  const totalSteps = steps.length;

  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const submitBtn = document.getElementById('submitBtn');
  const stepText = document.getElementById('progressStepText');
  const percentText = document.getElementById('progressPercent');
  const barFill = document.getElementById('progressBarFill');
  const timerDisplay = document.getElementById('questionTimer');
  const tabWarn = document.getElementById('tabSwitchCounter');

  let timerInterval = null;
  let tabSwitches = 0;

  // 1. Anti-Cheat: Tab Switch Detection
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      tabSwitches++;
      if (tabWarn) {
        tabWarn.innerText = `Tab switches: ${tabSwitches} (Logged)`;
        tabWarn.style.color = '#ef4444';
      }
    }
  });

  // 2. Anti-Cheat: Prevent Copy/Paste on Textareas
  document.querySelectorAll('.answer-textarea').forEach(area => {
    area.addEventListener('paste', (e) => {
      e.preventDefault();
      alert('Pasting content is disabled during proctored AI assessments. Please type your answer directly.');
    });

    // Word Counter
    area.addEventListener('input', () => {
      const words = area.value.trim().split(/\s+/).filter(w => w.length > 0).length;
      const counterId = 'wordCount_' + area.id.replace('answer_', '');
      const counter = document.getElementById(counterId);
      if (counter) {
        counter.innerText = `${words} words (${words >= 20 ? 'Optimal depth' : 'min 20 recommended'})`;
        counter.style.color = words >= 20 ? '#10b981' : '#9ca3af';
      }
    });
  });

  // 3. Question Step Navigation
  function updateStepUI() {
    steps.forEach((s, idx) => {
      s.classList.toggle('active', idx === currentStep);
    });

    // Update Jump Nav Buttons
    document.querySelectorAll('.q-jump-btn').forEach((btn, idx) => {
      const stepElem = steps[idx];
      const textarea = stepElem?.querySelector('textarea');
      const isAnswered = textarea && textarea.value.trim().length > 0;

      if (idx === currentStep) {
        btn.style.background = '#2563eb';
        btn.style.color = '#ffffff';
        btn.style.borderColor = '#2563eb';
        btn.style.boxShadow = '0 0 0 3px rgba(37, 99, 235, 0.2)';
      } else if (isAnswered) {
        btn.style.background = '#ecfdf5';
        btn.style.color = '#059669';
        btn.style.borderColor = '#a7f3d0';
        btn.style.boxShadow = 'none';
      } else {
        btn.style.background = '#ffffff';
        btn.style.color = '#475569';
        btn.style.borderColor = '#cbd5e1';
        btn.style.boxShadow = 'none';
      }
    });

    const progress = Math.round(((currentStep + 1) / totalSteps) * 100);
    if (stepText) stepText.innerText = `Question ${currentStep + 1} of ${totalSteps}`;
    if (percentText) percentText.innerText = `${progress}%`;
    if (barFill) barFill.style.width = `${progress}%`;

    if (prevBtn) prevBtn.disabled = currentStep === 0;

    if (currentStep === totalSteps - 1) {
      if (nextBtn) nextBtn.style.display = 'none';
      if (submitBtn) submitBtn.style.display = 'inline-flex';
    } else {
      if (nextBtn) nextBtn.style.display = 'inline-flex';
      if (submitBtn) submitBtn.style.display = 'none';
    }

    // Auto-focus active textarea
    const activeTextarea = steps[currentStep]?.querySelector('textarea');
    if (activeTextarea) activeTextarea.focus();

    // Reset countdown for current step
    resetTimerForStep(currentStep);
  }

  // Hook up question jump buttons
  document.querySelectorAll('.q-jump-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetStep = parseInt(btn.getAttribute('data-jump'), 10);
      if (!isNaN(targetStep) && targetStep >= 0 && targetStep < totalSteps) {
        currentStep = targetStep;
        updateStepUI();
      }
    });
  });

  // 4. Per-Question Timer
  function resetTimerForStep(stepIdx) {
    if (timerInterval) clearInterval(timerInterval);

    const stepElem = steps[stepIdx];
    let secondsLeft = Number(stepElem.getAttribute('data-limit')) || 90;

    function renderTime() {
      const mins = Math.floor(secondsLeft / 60);
      const secs = secondsLeft % 60;
      if (timerDisplay) {
        timerDisplay.innerText = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        if (secondsLeft <= 20) {
          timerDisplay.style.color = '#ef4444';
        } else {
          timerDisplay.style.color = '#f87171';
        }
      }
      if (secondsLeft <= 0) {
        clearInterval(timerInterval);
        // Alert candidate time is up for this question
        if (currentStep < totalSteps - 1) {
          currentStep++;
          updateStepUI();
        }
      }
      secondsLeft--;
    }

    renderTime();
    timerInterval = setInterval(renderTime, 1000);
  }

  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      if (currentStep < totalSteps - 1) {
        currentStep++;
        updateStepUI();
      }
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      if (currentStep > 0) {
        currentStep--;
        updateStepUI();
      }
    });
  }

  // Initial step setup
  if (steps.length > 0) {
    updateStepUI();
  }
})();
