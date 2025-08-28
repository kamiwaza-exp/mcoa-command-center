// RF Monitor Module for MCOA Dashboard
class RFMonitor {
    constructor() {
        this.data = [];
        this.currentIndex = 0;
        this.isRunning = false;
        this.isPaused = false;
        this.detections = [];
        this.spectrumHistory = [];
        this.maxHistory = 100;
        this.initialized = false;
    }
    
    init() {
        if (this.initialized) return;
        
        // Get elements
        this.modal = document.getElementById('rf-monitor-modal');
        this.spectrumCanvas = document.getElementById('rf-spectrum-canvas');
        this.timelineCanvas = document.getElementById('rf-timeline-canvas');
        this.detectionList = document.getElementById('rf-detection-list');
        this.timeDisplay = document.getElementById('rf-time-display');
        this.alertBox = document.getElementById('rf-alert-box');
        
        // Get status lights
        this.sensorStatus = document.getElementById('rf-sensor-status');
        this.scanStatus = document.getElementById('rf-scan-status');
        this.threatStatus = document.getElementById('rf-threat-status');
        
        // Get buttons
        this.startBtn = document.getElementById('rf-start-btn');
        this.pauseBtn = document.getElementById('rf-pause-btn');
        this.resetBtn = document.getElementById('rf-reset-btn');
        this.closeBtn = document.getElementById('rf-monitor-modal-close');
        
        // Report buttons
        this.saveReportBtn = document.getElementById('rf-save-report');
        this.downloadPdfBtn = document.getElementById('rf-download-pdf');
        this.transmitReportBtn = document.getElementById('rf-transmit-report');
        this.closeReportBtn = document.getElementById('rf-close-report');
        
        // Set up canvas contexts
        if (this.spectrumCanvas) {
            this.spectrumCtx = this.spectrumCanvas.getContext('2d');
            this.timelineCtx = this.timelineCanvas.getContext('2d');
        }
        
        // Add event listeners
        this.startBtn?.addEventListener('click', () => this.start());
        this.pauseBtn?.addEventListener('click', () => this.pause());
        this.resetBtn?.addEventListener('click', () => this.reset());
        this.closeBtn?.addEventListener('click', () => this.close());
        
        // Report action listeners
        this.saveReportBtn?.addEventListener('click', () => this.saveReport());
        this.downloadPdfBtn?.addEventListener('click', () => this.downloadPDF());
        this.transmitReportBtn?.addEventListener('click', () => this.transmitReport());
        this.closeReportBtn?.addEventListener('click', () => this.closeReportPanel());
        
        this.initialized = true;
        this.loadData();
    }
    
    async loadData() {
        try {
            const response = await fetch('/api/rf/data');
            const result = await response.json();
            
            if (result.status === 'success') {
                this.data = result.data;
                console.log(`Loaded ${this.data.length} RF spectrum samples`);
                // Set sensor status to active
                if (this.sensorStatus) {
                    this.sensorStatus.classList.add('active');
                }
            }
        } catch (error) {
            console.error('Error loading RF data:', error);
            // Use fallback data generation
            this.generateFallbackData();
        }
    }
    
    generateFallbackData() {
        this.data = [];
        for (let i = 0; i < 120; i++) {
            const hasDrone = i >= 30 && i <= 50;
            const spectrum = [];
            
            const frequencies = [433, 915, 1575, 2437, 5800];
            frequencies.forEach(freq => {
                let power = -120 + Math.random() * 20;
                if (hasDrone && (freq === 2437 || freq === 5800)) {
                    power = -50 + Math.random() * 10;
                }
                spectrum.push({ freq_mhz: freq, power_dbm: power });
            });
            
            this.data.push({
                spectrum: spectrum,
                detections: hasDrone ? [{
                    type: 'DRONE_SUSPECTED',
                    confidence: 0.85,
                    drone_type: 'DJI_Phantom',
                    description: 'DJI Phantom detected'
                }] : []
            });
        }
    }
    
    show() {
        this.init();
        this.modal.classList.remove('hidden');
        this.resizeCanvas();
    }
    
    close() {
        this.modal.classList.add('hidden');
        this.reset();
    }
    
    resizeCanvas() {
        if (!this.spectrumCanvas) return;
        
        // Set canvas dimensions
        this.spectrumCanvas.width = this.spectrumCanvas.offsetWidth;
        this.spectrumCanvas.height = 300;
        
        this.timelineCanvas.width = this.timelineCanvas.offsetWidth;
        this.timelineCanvas.height = 150;
    }
    
    start() {
        if (!this.isRunning) {
            this.isRunning = true;
            this.isPaused = false;
            this.startBtn.disabled = true;
            this.pauseBtn.disabled = false;
            this.scanStatus.classList.add('active');
            this.animate();
        }
    }
    
    pause() {
        this.isPaused = !this.isPaused;
        this.pauseBtn.textContent = this.isPaused ? '▶️ RESUME' : '⏸️ PAUSE';
    }
    
    reset() {
        this.isRunning = false;
        this.isPaused = false;
        this.currentIndex = 0;
        this.detections = [];
        this.spectrumHistory = [];
        
        if (this.startBtn) this.startBtn.disabled = false;
        if (this.pauseBtn) {
            this.pauseBtn.disabled = true;
            this.pauseBtn.textContent = '⏸️ PAUSE';
        }
        if (this.scanStatus) this.scanStatus.classList.remove('active');
        if (this.threatStatus) this.threatStatus.classList.remove('alert');
        if (this.detectionList) this.detectionList.innerHTML = '';
        if (this.alertBox) this.alertBox.style.display = 'none';
        
        this.clearCanvas();
    }
    
    clearCanvas() {
        if (this.spectrumCtx) {
            this.spectrumCtx.clearRect(0, 0, this.spectrumCanvas.width, this.spectrumCanvas.height);
        }
        if (this.timelineCtx) {
            this.timelineCtx.clearRect(0, 0, this.timelineCanvas.width, this.timelineCanvas.height);
        }
    }
    
    animate() {
        if (!this.isRunning) return;
        
        if (!this.isPaused && this.currentIndex < this.data.length) {
            this.processFrame(this.data[this.currentIndex]);
            this.currentIndex++;
        }
        
        // Update time display
        const elapsed = Math.floor(this.currentIndex / 2);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        if (this.timeDisplay) {
            this.timeDisplay.textContent = 
                `00:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
        
        // Loop when done
        if (this.currentIndex >= this.data.length) {
            this.currentIndex = 0;
        }
        
        setTimeout(() => this.animate(), 500);
    }
    
    processFrame(frame) {
        this.drawSpectrum(frame.spectrum);
        this.updateTimeline(frame);
        
        if (frame.detections && frame.detections.length > 0) {
            this.handleDetection(frame.detections[0]);
        } else {
            // No detection - reset threat status and tracking
            if (this.threatStatus) this.threatStatus.classList.remove('alert');
            if (this.alertBox) this.alertBox.style.display = 'none';
            
            // If no detection for 5 seconds, reset the drone tracking
            const now = Date.now();
            if (this.lastDetectionTime && (now - this.lastDetectionTime > 5000)) {
                this.currentDroneId = null;  // Reset drone tracking
            }
        }
    }
    
    drawSpectrum(spectrum) {
        if (!this.spectrumCtx) return;
        
        const ctx = this.spectrumCtx;
        const width = this.spectrumCanvas.width;
        const height = this.spectrumCanvas.height;
        
        // Clear with fade effect
        ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
        ctx.fillRect(0, 0, width, height);
        
        // Draw grid
        ctx.strokeStyle = '#003300';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 10; i++) {
            const y = (height / 10) * i;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }
        
        // Draw spectrum bars
        const barWidth = width / spectrum.length;
        spectrum.forEach((point, index) => {
            const x = index * barWidth;
            const normalizedPower = (point.power_dbm + 150) / 130;
            const barHeight = normalizedPower * height;
            
            // Color based on power
            let color;
            if (point.power_dbm > -60) {
                color = 'rgb(255, 0, 0)';
            } else if (point.power_dbm > -80) {
                color = 'rgb(255, 255, 0)';
            } else if (point.power_dbm > -100) {
                color = 'rgb(0, 255, 0)';
            } else {
                color = 'rgb(0, 100, 0)';
            }
            
            ctx.fillStyle = color;
            ctx.fillRect(x, height - barHeight, barWidth - 2, barHeight);
            
            // Glow effect for strong signals
            if (point.power_dbm > -60) {
                ctx.shadowColor = color;
                ctx.shadowBlur = 10;
                ctx.fillRect(x, height - barHeight, barWidth - 2, barHeight);
                ctx.shadowBlur = 0;
            }
        });
    }
    
    updateTimeline(frame) {
        if (!this.timelineCtx) return;
        
        this.spectrumHistory.push(frame);
        if (this.spectrumHistory.length > this.maxHistory) {
            this.spectrumHistory.shift();
        }
        
        const ctx = this.timelineCtx;
        const width = this.timelineCanvas.width;
        const height = this.timelineCanvas.height;
        
        ctx.fillStyle = '#000';
        ctx.fillRect(0, 0, width, height);
        
        const pixelHeight = height / this.maxHistory;
        const pixelWidth = width / frame.spectrum.length;
        
        this.spectrumHistory.forEach((histFrame, timeIndex) => {
            const y = timeIndex * pixelHeight;
            
            histFrame.spectrum.forEach((point, freqIndex) => {
                const x = freqIndex * pixelWidth;
                const intensity = (point.power_dbm + 150) / 130;
                const r = Math.floor(255 * intensity);
                const g = Math.floor(255 * (1 - Math.abs(intensity - 0.5) * 2));
                const b = Math.floor(255 * (1 - intensity));
                
                ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
                ctx.fillRect(x, y, pixelWidth, pixelHeight);
            });
        });
    }
    
    handleDetection(detection) {
        const now = Date.now();
        this.lastDetectionTime = now;  // Track when we last saw a detection
        
        if (this.threatStatus) this.threatStatus.classList.add('alert');
        
        if (this.alertBox) {
            this.alertBox.style.display = 'block';
            setTimeout(() => {
                this.alertBox.style.display = 'none';
            }, 2000);
        }
        
        this.addDetectionToList(detection);
        
        // Throttle report generation - only generate once per detection event
        const timeSinceLastReport = now - (this.lastReportTime || 0);
        const isDifferentDrone = this.currentDroneId && this.currentDroneId !== detection.drone_type;
        
        // Only generate report if:
        // 1. No report generated yet, OR
        // 2. Different drone detected, OR
        // 3. It's been more than 30 seconds since last report (for same drone)
        if (!this.lastReportTime || isDifferentDrone || timeSinceLastReport > 30000) {
            this.generateDroneReport(detection);
            this.lastReportTime = now;
            this.currentDroneId = detection.drone_type; // Track current drone
            this.playAlertSound();  // Only play sound for new reports
        }
    }
    
    async generateDroneReport(detection) {
        // Show report panel with generating status
        const reportPanel = document.getElementById('rf-report-panel');
        const reportStatus = document.getElementById('rf-report-status');
        const reportContent = document.getElementById('rf-report-content');
        
        if (reportPanel) {
            reportPanel.style.display = 'block';
            reportStatus.innerHTML = '<span class="generating-indicator">⏳ Generating Report...</span>';
            reportContent.innerHTML = '';
        }
        
        // Get current frame data
        const currentFrame = this.data[this.currentIndex - 1] || this.data[0];
        
        try {
            // Call API to generate report
            const response = await fetch('/api/rf/generate-drone-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    detection: detection,
                    spectrum: currentFrame.spectrum,
                    timestamp: new Date().toISOString()
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                // Display the report
                reportStatus.innerHTML = '<span class="report-ready">✅ Report Generated</span>';
                reportContent.innerHTML = `<pre class="rf-report-text">${result.report}</pre>`;
                
                // Add threat level indicator
                if (result.threat_level === 'HIGH') {
                    reportStatus.innerHTML += '<span class="threat-high">⚠️ HIGH THREAT</span>';
                } else if (result.threat_level === 'MODERATE') {
                    reportStatus.innerHTML += '<span class="threat-moderate">⚠️ MODERATE THREAT</span>';
                }
                
                // Store report for later actions
                this.currentReport = result;
            }
        } catch (error) {
            console.error('Error generating report:', error);
            reportStatus.innerHTML = '<span class="report-error">❌ Report Generation Failed</span>';
        }
    }
    
    addDetectionToList(detection) {
        if (!this.detectionList) return;
        
        const item = document.createElement('div');
        item.className = 'rf-detection-item active';
        item.innerHTML = `
            <strong>${detection.drone_type || 'Unknown'}</strong><br>
            <small>${new Date().toLocaleTimeString()}</small>
            <div class="rf-confidence-bar">
                <div class="rf-confidence-fill" style="width: ${detection.confidence * 100}%"></div>
            </div>
        `;
        
        this.detectionList.insertBefore(item, this.detectionList.firstChild);
        if (this.detectionList.children.length > 5) {
            this.detectionList.removeChild(this.detectionList.lastChild);
        }
        
        setTimeout(() => item.classList.remove('active'), 3000);
    }
    
    playAlertSound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            gainNode.gain.value = 0.1;
            
            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.1);
        } catch (e) {
            // Silent fail if audio not available
        }
    }
    
    saveReport() {
        if (!this.currentReport) return;
        
        // Create a blob and download
        const blob = new Blob([this.currentReport.report], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `drone_detection_${new Date().getTime()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        // Show confirmation
        const reportStatus = document.getElementById('rf-report-status');
        if (reportStatus) {
            reportStatus.innerHTML += '<span class="save-success"> 💾 Saved</span>';
        }
    }
    
    transmitReport() {
        if (!this.currentReport) return;
        
        // Simulate transmission
        const reportStatus = document.getElementById('rf-report-status');
        if (reportStatus) {
            reportStatus.innerHTML += '<span class="transmit-progress"> 📡 Transmitting...</span>';
            
            setTimeout(() => {
                reportStatus.innerHTML += '<span class="transmit-success"> ✅ Transmitted to HQ</span>';
                // Could actually send via WebSocket to command chat here
            }, 1500);
        }
    }
    
    closeReportPanel() {
        const reportPanel = document.getElementById('rf-report-panel');
        if (reportPanel) {
            reportPanel.style.display = 'none';
        }
    }
    
    async downloadPDF() {
        if (!this.currentReport) return;
        
        const reportStatus = document.getElementById('rf-report-status');
        if (reportStatus) {
            reportStatus.innerHTML += '<span class="pdf-progress"> 📄 Generating PDF...</span>';
        }
        
        try {
            // Send report data to generate PDF
            const response = await fetch('/api/rf/generate-drone-report-pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    report: this.currentReport.report,
                    drone_type: this.currentReport.drone_type,
                    threat_level: this.currentReport.threat_level
                })
            });
            
            if (response.ok) {
                // Get the PDF blob
                const blob = await response.blob();
                
                // Create download link
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `drone_detection_${new Date().getTime()}.pdf`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                // Show success
                if (reportStatus) {
                    reportStatus.innerHTML += '<span class="pdf-success"> ✅ PDF Downloaded</span>';
                }
            } else {
                throw new Error('PDF generation failed');
            }
        } catch (error) {
            console.error('Error downloading PDF:', error);
            if (reportStatus) {
                reportStatus.innerHTML += '<span class="pdf-error"> ❌ PDF Generation Failed</span>';
            }
        }
    }
}

// Initialize RF Monitor instance
let rfMonitor = null;

// Initialize when DOM is ready
function initRFMonitor() {
    const rfMonitorBtn = document.getElementById('rf-monitor-btn');
    if (rfMonitorBtn) {
        rfMonitorBtn.addEventListener('click', () => {
            if (!rfMonitor) {
                rfMonitor = new RFMonitor();
            }
            rfMonitor.show();
        });
    }
}

// Export for use in dashboard.js if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { RFMonitor, initRFMonitor };
}