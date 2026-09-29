/**
 * consoleUI.js
 * Manages the Tasking & Query Console interactions:
 * - Monitored Zones / AOI selector cards
 * - Real-world suggested query chips dynamically updated per zone
 * - Voice Assistance (Speech-to-Text Input + Speech Synthesis Readout)
 * - Collapsible Alerts Feed Drawer with click-to-jump actions
 * - Raw Tool Inspector Modal
 * - AOI coordinate HUD displays
 */

import { sound } from './soundEngine.js';

export class ConsoleUI {
  constructor(onMissionChange, onExecuteQuery, onBandChange, onAOIChange) {
    this.onMissionChange = onMissionChange;
    this.onExecuteQuery = onExecuteQuery;
    this.onBandChange = onBandChange;
    this.onAOIChange = onAOIChange;

    this.missionSelectEl = document.getElementById('mission-select');
    this.zoneCards = document.querySelectorAll('.zone-card');
    this.queryInputEl = document.getElementById('query-input');
    this.charCounterEl = document.getElementById('char-counter');
    this.promptChipsContainer = document.getElementById('prompt-chips-container');
    this.executeBtn = document.getElementById('btn-execute-mission');
    this.inlineRunBtn = document.getElementById('btn-input-run');
    this.voiceBtn = document.getElementById('voice-input-btn');
    this.uploadZone = document.getElementById('upload-zone');
    this.bandButtons = document.querySelectorAll('.band-btn');

    // Alert Feed Elements
    this.alertToggleBtn = document.getElementById('btn-toggle-alerts');
    this.alertDrawer = document.getElementById('alert-drawer');
    this.alertCloseBtn = document.getElementById('btn-close-alerts');
    this.alertItems = document.querySelectorAll('.alert-item');

    // Architecture Slide-Over Elements
    this.howItWorksBtn = document.getElementById('btn-toggle-how-it-works');
    this.architectureDrawer = document.getElementById('architecture-drawer');
    this.howItWorksCloseBtn = document.getElementById('btn-close-how-it-works');

    // Tool Inspector Elements
    this.toolInspector = document.getElementById('raw-tool-inspector');
    this.toolInspectorCloseBtn = document.getElementById('btn-close-tool-inspector');
    this.toolInspectorJson = document.getElementById('raw-tool-json');
    this.toolInspectorTitle = document.getElementById('raw-tool-title');

    // Voice & Speech Recognition state
    this.recognition = null;
    this.isListening = false;
    this.synth = window.speechSynthesis || null;

    this.historyEntries = [];

    this.initEvents();
    this.initArchitectureDrawer();
    this.initAlerts();
    this.initSuggestedChips();
    this.initSpeechRecognition();
  }

  initEvents() {
    // 1. Zone Card Selector clicks
    this.zoneCards.forEach(card => {
      card.addEventListener('click', () => {
        sound.playClick();
        this.zoneCards.forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        const mKey = card.dataset.mission;
        if (this.missionSelectEl) this.missionSelectEl.value = mKey;
        if (this.onMissionChange) this.onMissionChange(mKey);
      });
    });

    // 1. Mission Dropdown Change
    if (this.missionSelectEl) {
      this.missionSelectEl.addEventListener('change', (e) => {
        const missionKey = e.target.value;
        sound.playClick();
        if (missionKey === 'custom-upload') {
          if (this.uploadZone) this.uploadZone.style.display = 'block';
        } else {
          if (this.uploadZone) this.uploadZone.style.display = 'none';
        }
        if (this.onMissionChange) this.onMissionChange(missionKey);
      });
    }

    // 2. Query Input Char Counter & Enter key execution
    if (this.queryInputEl) {
      this.queryInputEl.addEventListener('input', () => {
        if (this.charCounterEl) {
          this.charCounterEl.textContent = `${this.queryInputEl.value.length} / 250`;
        }
      });

      this.queryInputEl.addEventListener('keydown', (e) => {
        const isEnter = e.key === 'Enter' || e.code === 'Enter' || e.code === 'NumpadEnter' || e.keyCode === 13;
        if (isEnter && !e.shiftKey) {
          e.preventDefault();
          this.triggerExecute();
        }
      });
    }

    // Inline Run Button Click
    if (this.inlineRunBtn) {
      this.inlineRunBtn.addEventListener('click', () => {
        this.triggerExecute();
      });
    }

    // Main Execute Button Click
    if (this.executeBtn) {
      this.executeBtn.addEventListener('click', () => {
        this.triggerExecute();
      });
    }

    // Describe Scene Quick Action Button (Step 3: Captioning / Scene Reasoning)
    const describeBtn = document.getElementById('btn-describe-scene');
    if (describeBtn) {
      describeBtn.addEventListener('click', () => {
        sound.playClick();
        const descQuery = "Describe this image in detail: identify geography, terrain features, prominent structures, and land use.";
        if (this.queryInputEl) {
          this.queryInputEl.value = descQuery;
          if (this.charCounterEl) this.charCounterEl.textContent = `${descQuery.length} / 250`;
        }
        this.triggerExecute();
      });
    }

    // Change Analysis Quick Action Button (Step 4: Bi-Temporal Variance & Comparison)
    const changeBtn = document.getElementById('btn-change-analysis');
    if (changeBtn) {
      changeBtn.addEventListener('click', () => {
        sound.playClick();
        const changeQuery = "What changed between these two dates, and where? Quantify area variance and built-up changes.";
        if (this.queryInputEl) {
          this.queryInputEl.value = changeQuery;
          if (this.charCounterEl) this.charCounterEl.textContent = `${changeQuery.length} / 250`;
        }
        this.triggerExecute();
      });
    }

    // Fusion Analysis Quick Action Button (Step 5: Cross-Modal Optical-SAR Joint Extraction)
    const fusionBtn = document.getElementById('btn-fusion-analysis');
    if (fusionBtn) {
      fusionBtn.addEventListener('click', () => {
        sound.playClick();
        const fusionQuery = "Identify built-up infrastructure and water-covered regions using both optical and SAR images.";
        if (this.queryInputEl) {
          this.queryInputEl.value = fusionQuery;
          if (this.charCounterEl) this.charCounterEl.textContent = `${fusionQuery.length} / 250`;
        }
        this.triggerExecute();
      });
    }

    // Random Query Generator Button (Instant plain-language question + immediate answer readout)
    const randomBtn = document.getElementById('btn-random-query');
    if (randomBtn) {
      randomBtn.addEventListener('click', () => {
        sound.playClick();
        const randQ = this.getRandomSatelliteQuestion();
        if (this.queryInputEl) {
          this.queryInputEl.value = randQ;
          if (this.charCounterEl) this.charCounterEl.textContent = `${randQ.length} / 250`;
        }
        this.triggerExecute();
      });
    }

    // Spectral Band Buttons
    this.bandButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        sound.playClick();
        this.bandButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const band = btn.dataset.band;
        if (this.onBandChange) this.onBandChange(band);
      });
    });

    // Sound toggle in header
    const soundToggleBtn = document.getElementById('sound-toggle-btn');
    if (soundToggleBtn) {
      soundToggleBtn.addEventListener('click', () => {
        const isEnabled = sound.toggle();
        soundToggleBtn.classList.toggle('active', isEnabled);
        soundToggleBtn.innerHTML = `<span>${isEnabled ? '🔊' : '🔇'}</span> AUDIO`;
      });
    }

    // Fullscreen HUD mode
    const hudBtn = document.getElementById('hud-mode-btn');
    if (hudBtn) {
      hudBtn.addEventListener('click', () => {
        sound.playClick();
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen().catch(() => {});
          hudBtn.classList.add('active');
        } else {
          document.exitFullscreen().catch(() => {});
          hudBtn.classList.remove('active');
        }
      });
    }

    // Read Aloud Voice Speech Button
    const speakBtn = document.getElementById('btn-speak-answer');
    if (speakBtn) {
      speakBtn.addEventListener('click', () => {
        sound.playClick();
        const reportEl = document.getElementById('intelligence-report-body');
        if (reportEl) {
          const text = reportEl.innerText || reportEl.textContent || '';
          this.speakAnswer(text);
        }
      });
    }

    // Tool inspector close button
    if (this.toolInspectorCloseBtn && this.toolInspector) {
      this.toolInspectorCloseBtn.addEventListener('click', () => {
        this.toolInspector.classList.remove('open');
      });
    }
  }

  initArchitectureDrawer() {
    if (this.howItWorksBtn && this.architectureDrawer) {
      this.howItWorksBtn.addEventListener('click', () => {
        sound.playClick();
        this.architectureDrawer.classList.toggle('open');
        this.howItWorksBtn.classList.toggle('active', this.architectureDrawer.classList.contains('open'));
      });
    }

    if (this.howItWorksCloseBtn && this.architectureDrawer) {
      this.howItWorksCloseBtn.addEventListener('click', () => {
        this.architectureDrawer.classList.remove('open');
        if (this.howItWorksBtn) this.howItWorksBtn.classList.remove('active');
      });
    }
  }

  initAlerts() {
    // Alert drawer toggle
    if (this.alertToggleBtn && this.alertDrawer) {
      this.alertToggleBtn.addEventListener('click', () => {
        sound.playClick();
        this.alertDrawer.classList.toggle('open');
        this.alertToggleBtn.classList.toggle('active', this.alertDrawer.classList.contains('open'));
      });
    }

    // Close alert drawer
    if (this.alertCloseBtn && this.alertDrawer) {
      this.alertCloseBtn.addEventListener('click', () => {
        this.alertDrawer.classList.remove('open');
        if (this.alertToggleBtn) this.alertToggleBtn.classList.remove('active');
      });
    }

    // Alert item click: jumps map context and runs analytical query
    this.alertItems.forEach(item => {
      item.addEventListener('click', () => {
        sound.playRadarPing();
        const missionKey = item.dataset.mission;
        const queryText = item.dataset.query;

        // Close drawer
        if (this.alertDrawer) this.alertDrawer.classList.remove('open');
        if (this.alertToggleBtn) this.alertToggleBtn.classList.remove('active');

        // Switch zone card
        this.selectZoneCard(missionKey);
        if (this.onMissionChange) this.onMissionChange(missionKey);

        // Populate and execute query
        if (this.queryInputEl && queryText) {
          this.queryInputEl.value = queryText;
          if (this.charCounterEl) this.charCounterEl.textContent = `${queryText.length} / 250`;
          setTimeout(() => {
            this.triggerExecute();
          }, 350);
        }
      });
    });
  }

  getRandomSatelliteQuestion() {
    const questions = [
      "Count all cargo and naval ships in this harbor and identify military vessels.",
      "Describe this scene in detail: identify terrain features, infrastructure, and water extent.",
      "What changed between these two dates, and where did the change occur?",
      "Has the built-up area increased, decreased, or remained unchanged?",
      "Analyze deforestation or burn scar extent in km² across this scene.",
      "Identify built-up infrastructure and water-covered regions using both optical and SAR images.",
      "Segment surface water bodies and calculate exact flood inundation extent in km².",
      "Detect all fuel storage tanks and verify containment perimeter security.",
      "Inspect launch pads, umbilical towers, and rocket assembly complexes.",
      "Analyze urban expansion and marshland encroachment.",
      "Check cloud cover percentage, atmospheric visibility, and optical transmittance.",
      "Are there any aircraft, runways, or helipads visible in this operational sector?",
      "Extract multispectral reflectance signatures across visible and near-infrared bands.",
      "Count all discrete objects and structures visible in this satellite imagery.",
      "Assess structural damage, physical breaches, or hazard anomalies across this AOI."
    ];
    return questions[Math.floor(Math.random() * questions.length)];
  }

  initSuggestedChips() {
    const exampleChips = document.querySelectorAll('.example-chip-btn');
    exampleChips.forEach(chip => {
      chip.addEventListener('click', () => {
        sound.playClick();
        const query = chip.dataset.query;
        if (this.queryInputEl && query) {
          this.queryInputEl.value = query;
          if (this.charCounterEl) this.charCounterEl.textContent = `${query.length} / 250`;
          this.triggerExecute();
        }
      });
    });
  }

  selectZoneCard(missionKey) {
    this.zoneCards.forEach(c => {
      if (c.dataset.mission === missionKey) {
        c.classList.add('active');
      } else {
        c.classList.remove('active');
      }
    });
    if (this.missionSelectEl) {
      this.missionSelectEl.value = missionKey;
    }
  }

  renderSuggestedPrompts(prompts) {
    return this.setPrompts(prompts);
  }

  setPrompts(prompts) {
    if (!this.promptChipsContainer) return;
    if (!prompts || prompts.length === 0) return;

    this.promptChipsContainer.innerHTML = '';
    prompts.forEach(p => {
      const btn = document.createElement('button');
      btn.className = 'example-chip-btn';
      btn.dataset.query = p;

      let icon = '⚡';
      const pl = p.toLowerCase();
      if (pl.includes('describe') || pl.includes('caption')) icon = '🖼️';
      else if (pl.includes('highlight') || pl.includes('grounding') || pl.includes('naval') || pl.includes('craft')) icon = '⚓';
      else if (pl.includes('count') || pl.includes('ship') || pl.includes('vessel')) icon = '🎯';
      else if (pl.includes('flood') || pl.includes('water')) icon = '🌊';
      else if (pl.includes('forest') || pl.includes('burn') || pl.includes('canopy') || pl.includes('deforest')) icon = '🔥';
      else if (pl.includes('change') || pl.includes('between') || pl.includes('since') || pl.includes('variance')) icon = '⇄';
      else if (pl.includes('increased') || pl.includes('decreased') || pl.includes('growth') || pl.includes('urban')) icon = '📈';
      else if (pl.includes('launch') || pl.includes('infra') || pl.includes('shar') || pl.includes('rocket')) icon = '🛰️';

      btn.innerHTML = `<span>${icon}</span> "${p}"`;
      btn.addEventListener('click', () => {
        sound.playClick();
        if (this.queryInputEl) {
          this.queryInputEl.value = p;
          if (this.charCounterEl) this.charCounterEl.textContent = `${p.length} / 250`;
          this.triggerExecute();
        }
      });
      this.promptChipsContainer.appendChild(btn);
    });
  }

  updateAOIDisplay(bounds) {
    if (!bounds) return;
    let nLat = 18.9650, sLat = 18.9200, eLon = 72.8600, wLon = 72.8100;

    if (Array.isArray(bounds)) {
      if (Array.isArray(bounds[0]) && Array.isArray(bounds[1])) {
        sLat = Number(bounds[0][0]);
        wLon = Number(bounds[0][1]);
        nLat = Number(bounds[1][0]);
        eLon = Number(bounds[1][1]);
      } else if (bounds.length >= 4) {
        sLat = Number(bounds[0]);
        wLon = Number(bounds[1]);
        nLat = Number(bounds[2]);
        eLon = Number(bounds[3]);
      }
    } else if (typeof bounds === 'object') {
      nLat = Number(bounds.north ?? bounds.n ?? 18.9650);
      sLat = Number(bounds.south ?? bounds.s ?? 18.9200);
      eLon = Number(bounds.east ?? bounds.e ?? 72.8600);
      wLon = Number(bounds.west ?? bounds.w ?? 72.8100);
    }

    const nEl = document.getElementById('aoi-n');
    const sEl = document.getElementById('aoi-s');
    const eEl = document.getElementById('aoi-e');
    const wEl = document.getElementById('aoi-w');

    if (nEl && !isNaN(nLat)) nEl.textContent = `${nLat.toFixed(4)}°`;
    if (sEl && !isNaN(sLat)) sEl.textContent = `${sLat.toFixed(4)}°`;
    if (eEl && !isNaN(eLon)) eEl.textContent = `${eLon.toFixed(4)}°`;
    if (wEl && !isNaN(wLon)) wEl.textContent = `${wLon.toFixed(4)}°`;
  }

  setLoading(isLoading) {
    this.setRunningState(isLoading);
    if (isLoading) {
      // Clear any prior safety timeout
      if (this._loadingTimeout) clearTimeout(this._loadingTimeout);
      this._loadingTimeout = setTimeout(() => {
        this.setRunningState(false);
      }, 10000);
    } else {
      if (this._loadingTimeout) {
        clearTimeout(this._loadingTimeout);
        this._loadingTimeout = null;
      }
    }
  }

  setRunningState(isRunning) {
    if (this.executeBtn) {
      this.executeBtn.classList.toggle('running', isRunning);
      if (!isRunning) {
        this.executeBtn.classList.remove('acknowledging');
      }
      this.executeBtn.disabled = isRunning;
      const textSpan = this.executeBtn.querySelector('.btn-text');
      if (textSpan) {
        if (isRunning) {
          textSpan.textContent = '⚡ ORCHESTRATING...';
        } else {
          if (this.currentRole === 'observer') {
            textSpan.textContent = '🔒 READ-ONLY OBSERVER MODE';
          } else {
            textSpan.textContent = '⚡ DISPATCH QUERY (ENTER ↵)';
          }
        }
      }
    }
    if (this.inlineRunBtn) {
      this.inlineRunBtn.classList.toggle('running', isRunning);
      this.inlineRunBtn.disabled = isRunning;
      const labelSpan = this.inlineRunBtn.querySelector('.run-label');
      if (labelSpan) {
        labelSpan.textContent = isRunning ? 'RUNNING' : 'RUN';
      }
      const iconSpan = this.inlineRunBtn.querySelector('.run-icon');
      if (iconSpan) {
        iconSpan.textContent = isRunning ? '⏳' : '▶';
      }
    }
    const badge = document.getElementById('dossier-status-badge');
    if (badge) {
      if (isRunning) {
        badge.textContent = 'ANALYZING';
        badge.style.color = 'var(--amber-alert)';
        badge.style.borderColor = 'var(--amber-alert)';
      } else {
        badge.textContent = 'READY';
        badge.style.color = 'var(--cyan-signal)';
        badge.style.borderColor = 'var(--cyan-border)';
      }
    }
  }

  triggerExecute() {
    if (this.currentRole === 'observer') {
      sound.playAlert();
      this.showErrorBanner('ACCESS RESTRICTED: Observer Mode is read-only. Switch role to Analyst or Commander using the [DEMO: ROLE] dropdown in the top bar to dispatch live queries.');
      return;
    }

    const query = this.queryInputEl ? this.queryInputEl.value.trim() : '';
    if (!query) {
      sound.playAlert();
      if (this.queryInputEl) {
        this.queryInputEl.focus();
        this.queryInputEl.classList.add('pulse-error');
        setTimeout(() => this.queryInputEl.classList.remove('pulse-error'), 800);
      }
      return;
    }

    // Immediate <200ms Acknowledgement state
    this.hideErrorBanner();
    if (this.executeBtn) {
      this.executeBtn.classList.add('acknowledging');
      const textSpan = this.executeBtn.querySelector('.btn-text');
      if (textSpan) textSpan.textContent = '⚡ QUERY RECEIVED · ROUTING...';
    }
    if (this.inlineRunBtn) {
      const labelSpan = this.inlineRunBtn.querySelector('.run-label');
      if (labelSpan) labelSpan.textContent = 'ROUTING...';
      const iconSpan = this.inlineRunBtn.querySelector('.run-icon');
      if (iconSpan) iconSpan.textContent = '⏳';
    }

    sound.playLaunch();
    this.setLoading(true);

    if (this.onExecuteQuery) {
      this.onExecuteQuery(query);
    }
  }

  initSpeechRecognition() {
    const hasSpeech = ('webkitSpeechRecognition' in window) || ('SpeechRecognition' in window);
    
    if (hasSpeech) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = false;
      this.recognition.lang = 'en-US';

      this.recognition.onstart = () => {
        this.isListening = true;
        if (this.voiceBtn) {
          this.voiceBtn.classList.add('active', 'listening');
          this.voiceBtn.innerHTML = '<span>🔴</span> LISTENING... SPEAK NOW';
        }
      };

      this.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (this.queryInputEl && transcript) {
          this.queryInputEl.value = transcript;
          if (this.charCounterEl) this.charCounterEl.textContent = `${transcript.length} / 250`;
        }
        this.stopVoice();
        setTimeout(() => {
          this.triggerExecute();
        }, 300);
      };

      this.recognition.onerror = (e) => {
        console.warn('Speech recognition error:', e.error);
        this.stopVoice();
      };

      this.recognition.onend = () => {
        this.stopVoice();
      };
    }

    if (this.voiceBtn) {
      this.voiceBtn.addEventListener('click', () => {
        if (!this.isListening) {
          this.startVoice();
        } else {
          this.stopVoice();
        }
      });
    }
  }

  startVoice() {
    if (this.recognition) {
      try {
        this.recognition.start();
        return;
      } catch (e) {
        console.warn('Recognition start exception, resetting...', e);
      }
    }

    // Graceful fallback for environments without microphone access
    const sampleVoiceQueries = [
      "Count all vessels in this AOI and identify naval craft",
      "Show flooded areas and assess infrastructure damage",
      "Analyze deforestation and burn scar extent in km²",
      "What changed here since last month?",
      "Describe the visible launch complex infrastructure"
    ];
    const randomQuery = sampleVoiceQueries[Math.floor(Math.random() * sampleVoiceQueries.length)];
    
    if (this.voiceBtn) {
      this.voiceBtn.classList.add('active');
      this.voiceBtn.innerHTML = '<span>🎙️</span> VOICE RECOGNIZED';
    }

    if (this.queryInputEl) {
      this.queryInputEl.value = randomQuery;
      if (this.charCounterEl) this.charCounterEl.textContent = `${randomQuery.length} / 250`;
    }

    setTimeout(() => {
      this.stopVoice();
      this.triggerExecute();
    }, 600);
  }

  stopVoice() {
    this.isListening = false;
    if (this.voiceBtn) {
      this.voiceBtn.classList.remove('active', 'listening');
      this.voiceBtn.innerHTML = '<span>🎙️</span> VOICE';
    }
    if (this.recognition) {
      try { this.recognition.stop(); } catch (e) {}
    }
  }

  speakAnswer(text) {
    if (!this.synth) return;
    try {
      this.synth.cancel();
      // Clean up markdown markers for speech
      const cleanText = text
        .replace(/\[.*?\]/g, '')
        .replace(/\*\*/g, '')
        .replace(/`/g, '')
        .replace(/⚠️/g, 'Warning:')
        .trim();

      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = 1.05;
      utterance.pitch = 1.0;
      this.synth.speak(utterance);
    } catch (e) {
      console.warn('Speech synthesis error:', e);
    }
  }

  openToolInspector(toolName, rawData) {
    if (!this.toolInspector) return;
    if (this.toolInspectorTitle) {
      this.toolInspectorTitle.textContent = `RAW TOOL OUTPUT: ${toolName.toUpperCase()}`;
    }
    if (this.toolInspectorJson) {
      this.toolInspectorJson.textContent = JSON.stringify(rawData, null, 2);
    }
    this.toolInspector.classList.add('open');
  }

  applyRole(role, clearance, user) {
    this.currentRole = role;
    
    // Update Header Operator HUD
    const opIdEl = document.getElementById('hud-operator-id');
    const badgeEl = document.getElementById('hud-clearance-badge');
    const demoBtn = document.getElementById('btn-demo-role-toggle');

    if (opIdEl && user) {
      opIdEl.innerHTML = `👤 ${user.id}`;
    }

    if (badgeEl && clearance) {
      badgeEl.className = `auth-clearance-badge ${clearance.badgeClass || ''}`;
      badgeEl.textContent = clearance.label || role.toUpperCase();
    }

    if (demoBtn) {
      demoBtn.innerHTML = `<span>⚡</span> ROLE: ${role.toUpperCase()} ▾`;
    }

    // Update active state in demo role menu
    document.querySelectorAll('.demo-role-option').forEach(opt => {
      opt.classList.toggle('active', opt.dataset.role === role);
    });

    // UI Gating for Observer Mode
    const modeTag = document.getElementById('llm-mode-badge');
    if (role === 'observer') {
      if (this.executeBtn) {
        this.executeBtn.classList.add('observer-restricted');
        this.executeBtn.innerHTML = '<span class="btn-text">🔒 READ-ONLY OBSERVER MODE</span>';
      }
      if (this.queryInputEl) {
        this.queryInputEl.placeholder = 'Observer Mode (Read-Only): Select a past mission query or switch to Analyst/Commander via the Demo Switcher to dispatch live queries.';
      }
      if (modeTag) modeTag.textContent = 'READ-ONLY OBSERVER';
    } else if (role === 'analyst') {
      if (this.executeBtn) {
        this.executeBtn.classList.remove('observer-restricted');
        this.executeBtn.innerHTML = '<span class="btn-text">⚡ DISPATCH QUERY</span>';
      }
      if (this.queryInputEl) {
        this.queryInputEl.placeholder = 'Ask a plain-language satellite question, e.g. "Count all cargo and naval ships in this harbor", "Show flooded areas vs baseline"...';
      }
      if (modeTag) modeTag.textContent = 'ANALYST TASKING';
    } else { // commander
      if (this.executeBtn) {
        this.executeBtn.classList.remove('observer-restricted');
        this.executeBtn.innerHTML = '<span class="btn-text">⚡ DISPATCH QUERY</span>';
      }
      if (this.queryInputEl) {
        this.queryInputEl.placeholder = 'Ask any plain-language mission question (unrestricted Commander clearance)...';
      }
      if (modeTag) modeTag.textContent = 'COMMANDER // UNCONSTRAINED';
    }
  }

  initAuditDrawer(authManager) {
    this.authManager = authManager;
    const auditDrawer = document.getElementById('audit-drawer');
    const toggleBtn = document.getElementById('btn-toggle-audit-log');
    const closeBtn = document.getElementById('btn-close-audit');
    const searchInput = document.getElementById('audit-search-input');
    const exportBtn = document.getElementById('btn-export-audit-json');

    const renderLogs = (filter = '') => {
      const container = document.getElementById('audit-entries-container');
      const countBadge = document.getElementById('audit-total-count');
      if (!container || !this.authManager) return;

      const logs = this.authManager.getAuditLogs();
      const fLower = filter.toLowerCase().trim();
      const filtered = fLower 
        ? logs.filter(l => 
            l.operatorId.toLowerCase().includes(fLower) || 
            l.action.toLowerCase().includes(fLower) || 
            l.details.toLowerCase().includes(fLower) || 
            l.zone.toLowerCase().includes(fLower)
          )
        : logs;

      if (countBadge) countBadge.textContent = `${filtered.length} ENTRIES`;

      if (filtered.length === 0) {
        container.innerHTML = '<div style="font-family:var(--font-mono); font-size:11px; color:var(--text-muted); padding:20px; text-align:center;">No matching audit ledger records found.</div>';
        return;
      }

      container.innerHTML = filtered.map(log => {
        let tagClass = 'query';
        if (log.action.includes('LOGIN') || log.action.includes('BOOTSTRAP')) tagClass = 'login';
        else if (log.action.includes('OVERRIDE') || log.action.includes('ROLE')) tagClass = 'override';
        else if (log.action.includes('EXPORT')) tagClass = 'export';

        const timeStr = new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

        return `
          <div class="audit-entry-card">
            <div class="audit-card-top">
              <span class="audit-action-tag ${tagClass}">${log.action}</span>
              <span class="audit-timestamp">${timeStr} · ${log.operatorId}</span>
            </div>
            <div class="audit-details-text">${log.details}</div>
            <div class="audit-card-meta">
              <span class="audit-meta-item"><span>🎯</span> ${log.zone}</span>
              <span class="audit-meta-item"><span>🛠️</span> ${log.tools.join(', ')}</span>
              <span class="audit-checksum" title="Cryptographic SHA-256 Checksum">SHA: ${log.checksum}</span>
            </div>
          </div>
        `;
      }).join('');
    };

    if (toggleBtn && auditDrawer) {
      toggleBtn.addEventListener('click', () => {
        sound.playClick();
        auditDrawer.classList.toggle('open');
        toggleBtn.classList.toggle('active', auditDrawer.classList.contains('open'));
        if (auditDrawer.classList.contains('open')) {
          renderLogs(searchInput ? searchInput.value : '');
        }
      });
    }

    if (closeBtn && auditDrawer) {
      closeBtn.addEventListener('click', () => {
        auditDrawer.classList.remove('open');
        if (toggleBtn) toggleBtn.classList.remove('active');
      });
    }

    if (searchInput) {
      searchInput.addEventListener('input', () => {
        renderLogs(searchInput.value);
      });
    }

    if (exportBtn) {
      exportBtn.addEventListener('click', () => {
        sound.playClick();
        const logs = this.authManager ? this.authManager.getAuditLogs() : [];
        const blob = new Blob([JSON.stringify(logs, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `isro_satquery_audit_trail_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
      });
    }

    window.addEventListener('satquery:audit-logged', () => {
      if (auditDrawer && auditDrawer.classList.contains('open')) {
        renderLogs(searchInput ? searchInput.value : '');
      }
    });
  }

  showErrorBanner(message, onRetry = null) {
    const banner = document.getElementById('pipeline-error-banner');
    const msgEl = document.getElementById('error-banner-msg');
    const retryBtn = document.getElementById('btn-error-retry');
    const dismissBtn = document.getElementById('btn-error-dismiss');

    if (!banner || !msgEl) return;
    msgEl.textContent = message;
    banner.classList.add('active');

    if (retryBtn) {
      retryBtn.style.display = onRetry ? 'inline-block' : 'none';
      retryBtn.onclick = () => {
        sound.playClick();
        this.hideErrorBanner();
        if (onRetry) onRetry();
      };
    }

    if (dismissBtn) {
      dismissBtn.onclick = () => {
        sound.playClick();
        this.hideErrorBanner();
      };
    }
  }

  hideErrorBanner() {
    const banner = document.getElementById('pipeline-error-banner');
    if (banner) banner.classList.remove('active');
  }

  initHistoryRail(onSelectHistoryItem) {
    this.onSelectHistoryItem = onSelectHistoryItem;
    this.historyEntries = [];
    const rail = document.getElementById('query-history-rail');
    const toggleBtn = document.getElementById('btn-toggle-history-rail');
    const clearBtn = document.getElementById('btn-clear-query-history');

    if (toggleBtn && rail) {
      toggleBtn.addEventListener('click', () => {
        sound.playClick();
        rail.classList.toggle('open');
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        sound.playClick();
        this.historyEntries = [];
        this.renderHistory();
      });
    }
  }

  addHistoryEntry(query, targetCount, missionKey) {
    if (!query) return;
    const entry = {
      id: `H-${Date.now()}`,
      query: query,
      targetCount: targetCount !== undefined && targetCount !== null ? targetCount : '—',
      missionKey: missionKey || 'active',
      timeStr: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    // Prepend and limit to 15
    this.historyEntries.unshift(entry);
    if (this.historyEntries.length > 15) this.historyEntries.pop();

    const rail = document.getElementById('query-history-rail');
    if (rail && !rail.classList.contains('open')) {
      rail.classList.add('open');
    }

    this.renderHistory();
  }

  renderHistory() {
    const container = document.getElementById('history-items-container');
    const countEl = document.getElementById('history-item-count');
    if (!container) return;

    if (countEl) countEl.textContent = this.historyEntries.length;

    if (this.historyEntries.length === 0) {
      container.innerHTML = '<div style="font-family: var(--font-mono); font-size: 9px; color: var(--text-muted); padding: 4px;">No past queries dispatched this session.</div>';
      return;
    }

    container.innerHTML = this.historyEntries.map(h => `
      <div class="history-item" data-id="${h.id}" data-query="${h.query}" data-mission="${h.missionKey}">
        <span class="history-item-text" title="${h.query}">⚡ ${h.query}</span>
        <span class="history-item-meta">
          <span>${h.timeStr}</span>
          <span>· ${h.targetCount} targets</span>
        </span>
      </div>
    `).join('');

    container.querySelectorAll('.history-item').forEach(item => {
      item.addEventListener('click', () => {
        sound.playClick();
        const q = item.dataset.query;
        const m = item.dataset.mission;
        if (this.queryInputEl) {
          this.queryInputEl.value = q;
          if (this.charCounterEl) this.charCounterEl.textContent = `${q.length} / 250`;
        }
        if (this.onSelectHistoryItem) {
          this.onSelectHistoryItem(q, m);
        }
      });
    });
  }
}
