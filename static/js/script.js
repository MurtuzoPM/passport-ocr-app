document.addEventListener('DOMContentLoaded', () => {
    // API Check & Status Initialization
    checkAPIStatus();

    // Tab Navigation Elements
    const tabSingle = document.getElementById('tab-single');
    const tabBatch = document.getElementById('tab-batch');
    const singleScanView = document.getElementById('single-scan-view');
    const batchScanView = document.getElementById('batch-scan-view');

    // Tab Switching Logic
    tabSingle.addEventListener('click', () => {
        switchTab(tabSingle, tabBatch, singleScanView, batchScanView);
    });

    tabBatch.addEventListener('click', () => {
        switchTab(tabBatch, tabSingle, batchScanView, singleScanView);
    });

    // ==========================================
    // 1. SINGLE PASSPORT SCANNING WORKFLOW
    // ==========================================
    const dropzoneSingle = document.getElementById('dropzone-single');
    const fileSingleInput = document.getElementById('file-single');
    const fileInfoSingle = document.getElementById('file-info-single');
    const fileNameSingle = document.getElementById('file-name-single');
    const fileSizeSingle = document.getElementById('file-size-single');
    const btnRemoveSingle = document.getElementById('btn-remove-single');
    const btnScanSingle = document.getElementById('btn-scan-single');

    const placeholderSingle = document.getElementById('placeholder-single');
    const spinnerSingle = document.getElementById('spinner-single');
    const resultsSingle = document.getElementById('results-single');

    let activeSingleFile = null;

    // Trigger file dialog
    dropzoneSingle.addEventListener('click', (e) => {
        if (e.target !== fileSingleInput) {
            fileSingleInput.click();
        }
    });

    // Dropzone drag-over styles
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzoneSingle.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzoneSingle.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzoneSingle.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzoneSingle.classList.remove('dragover');
        }, false);
    });

    // Capture dropped files
    dropzoneSingle.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleSingleFileSelection(files[0]);
        }
    });

    // Capture dialog selection
    fileSingleInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleSingleFileSelection(e.target.files[0]);
        }
    });

    // Clean single selection
    btnRemoveSingle.addEventListener('click', (e) => {
        e.stopPropagation();
        clearSingleSelection();
    });

    function handleSingleFileSelection(file) {
        // Validate size limit (50MB)
        if (file.size > 50 * 1024 * 1024) {
            alert('File exceeds maximum size limit of 50 MB.');
            return;
        }

        activeSingleFile = file;
        fileNameSingle.textContent = file.name;
        fileSizeSingle.textContent = formatBytes(file.size);
        
        fileInfoSingle.classList.remove('hidden');
        btnScanSingle.removeAttribute('disabled');
        btnScanSingle.classList.replace('bg-slate-200', 'bg-indigo-600');
        btnScanSingle.classList.replace('text-slate-400', 'text-white');
        btnScanSingle.classList.replace('cursor-not-allowed', 'hover:bg-indigo-700');
    }

    function clearSingleSelection() {
        activeSingleFile = null;
        fileSingleInput.value = '';
        fileInfoSingle.classList.add('hidden');
        
        btnScanSingle.setAttribute('disabled', 'true');
        btnScanSingle.classList.replace('bg-indigo-600', 'bg-slate-200');
        btnScanSingle.classList.replace('text-white', 'text-slate-400');
        btnScanSingle.classList.replace('hover:bg-indigo-700', 'cursor-not-allowed');

        placeholderSingle.classList.remove('hidden');
        spinnerSingle.classList.add('hidden');
        resultsSingle.classList.add('hidden');
    }

    // Submit single file for OCR
    btnScanSingle.addEventListener('click', async () => {
        if (!activeSingleFile) return;

        // Visual layout switch
        placeholderSingle.classList.add('hidden');
        resultsSingle.classList.add('hidden');
        spinnerSingle.classList.remove('hidden');

        const formData = new FormData();
        formData.append('file', activeSingleFile);

        try {
            const response = await fetch('/api/extract', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                renderSingleResults(result.data, result.processing_time);
            } else {
                alert(`Error: ${result.error || 'Failed to scan document'}`);
                clearSingleSelection();
            }
        } catch (error) {
            console.error('Scan Request Failed:', error);
            alert('System connection failure. Please make sure Flask is running locally or inspect logs.');
            clearSingleSelection();
        } finally {
            spinnerSingle.classList.add('hidden');
        }
    });

    function renderSingleResults(data, seconds) {
        // Elements mapping
        const passNum = document.getElementById('res-pass-num');
        const nameField = document.getElementById('res-name');
        const dobField = document.getElementById('res-dob');
        const genderField = document.getElementById('res-gender');
        const nationalityField = document.getElementById('res-nationality');
        const expiryField = document.getElementById('res-expiry');
        const timeField = document.getElementById('res-time');
        const mrzBadge = document.getElementById('res-mrz-badge');
        const confBadge = document.getElementById('res-confidence-badge');
        const confBar = document.getElementById('res-confidence-bar');
        const rawJsonBlock = document.getElementById('res-raw-json');

        // Text mappings
        passNum.textContent = data.passport_number || 'N/A';
        nameField.textContent = data.full_name || 'N/A';
        dobField.textContent = data.date_of_birth || 'N/A';
        genderField.textContent = data.gender || 'N/A';
        nationalityField.textContent = data.nationality || 'N/A';
        expiryField.textContent = data.expiry_date || 'N/A';
        
        timeField.textContent = `Scan Time: ${seconds}s`;

        // MRZ Display
        if (data.mrz_detected) {
            mrzBadge.textContent = 'MRZ Matches';
            mrzBadge.parentElement.className = 'text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2.5 py-1 flex items-center space-x-1.5 shadow-sm';
        } else {
            mrzBadge.textContent = 'Visual Fallback (No MRZ)';
            mrzBadge.parentElement.className = 'text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-2.5 py-1 flex items-center space-x-1.5 shadow-sm';
        }

        // Confidence metrics
        const pct = Math.round(data.confidence * 100);
        confBadge.textContent = `${pct}%`;
        confBar.style.width = `${pct}%`;

        if (pct >= 85) {
            confBar.className = "bg-emerald-500 h-2.5 rounded-full transition-all duration-1000";
            confBadge.className = "text-xs font-bold text-emerald-700 bg-emerald-50 rounded-md px-2 py-0.5";
        } else if (pct >= 60) {
            confBar.className = "bg-amber-500 h-2.5 rounded-full transition-all duration-1000";
            confBadge.className = "text-xs font-bold text-amber-700 bg-amber-50 rounded-md px-2 py-0.5";
        } else {
            confBar.className = "bg-rose-500 h-2.5 rounded-full transition-all duration-1000";
            confBadge.className = "text-xs font-bold text-rose-700 bg-rose-50 rounded-md px-2 py-0.5";
        }

        // Raw code printing
        rawJsonBlock.textContent = JSON.stringify(data, null, 2);

        // Transition outputs
        resultsSingle.classList.remove('hidden');
        resultsSingle.classList.add('fade-in');
    }

    // Single JSON Exports
    document.getElementById('btn-copy-json').addEventListener('click', () => {
        const rawText = document.getElementById('res-raw-json').textContent;
        copyTextToClipboard(rawText);
    });

    document.getElementById('btn-download-json').addEventListener('click', () => {
        const rawText = document.getElementById('res-raw-json').textContent;
        const filename = (activeSingleFile ? activeSingleFile.name.split('.')[0] : 'passport_data') + '.json';
        downloadJSON(rawText, filename);
    });


    // ==========================================
    // 2. BATCH PASSPORT SCANNING WORKFLOW
    // ==========================================
    const dropzoneBatch = document.getElementById('dropzone-batch');
    const fileBatchInput = document.getElementById('file-batch');
    const batchCount = document.getElementById('batch-count');
    const btnScanBatch = document.getElementById('btn-scan-batch');
    const btnClearBatch = document.getElementById('btn-clear-batch');

    const placeholderBatch = document.getElementById('placeholder-batch');
    const batchResultsTable = document.getElementById('batch-results-table-container');
    const batchTableBody = document.getElementById('batch-table-body');
    const batchProgressLoader = document.getElementById('batch-progress-loader');
    const batchLoaderText = document.getElementById('batch-loader-text');
    const batchLoaderPercent = document.getElementById('batch-loader-percent');
    const batchLoaderBar = document.getElementById('batch-loader-bar');

    const batchStatsCard = document.getElementById('batch-stats-card');
    const btnBatchDownloadAll = document.getElementById('btn-batch-download-all');

    let batchQueue = [];
    let batchOutputs = [];

    // Select files triggers
    dropzoneBatch.addEventListener('click', (e) => {
        if (e.target !== fileBatchInput) {
            fileBatchInput.click();
        }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzoneBatch.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzoneBatch.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzoneBatch.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzoneBatch.classList.remove('dragover');
        }, false);
    });

    dropzoneBatch.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt.files.length > 0) {
            addFilesToBatch(dt.files);
        }
    });

    fileBatchInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            addFilesToBatch(e.target.files);
        }
    });

    btnClearBatch.addEventListener('click', () => {
        clearBatchQueue();
    });

    function addFilesToBatch(filesList) {
        for (let i = 0; i < filesList.length; i++) {
            const file = filesList[i];
            if (file.size <= 50 * 1024 * 1024) {
                // Ensure duplicate names are ignored or processed
                batchQueue.push(file);
            } else {
                alert(`Skipped ${file.name} - exceeds 50 MB threshold.`);
            }
        }
        updateBatchUI();
    }

    function updateBatchUI() {
        if (batchQueue.length > 0) {
            batchCount.textContent = `${batchQueue.length} file(s) loaded`;
            
            btnScanBatch.removeAttribute('disabled');
            btnScanBatch.classList.replace('bg-slate-200', 'bg-indigo-600');
            btnScanBatch.classList.replace('text-slate-400', 'text-white');
            btnScanBatch.classList.replace('cursor-not-allowed', 'hover:bg-indigo-700');

            btnClearBatch.classList.remove('hidden');
        } else {
            clearBatchQueue();
        }
    }

    function clearBatchQueue() {
        batchQueue = [];
        batchOutputs = [];
        fileBatchInput.value = '';
        batchCount.textContent = '0 files';
        
        btnScanBatch.setAttribute('disabled', 'true');
        btnScanBatch.classList.replace('bg-indigo-600', 'bg-slate-200');
        btnScanBatch.classList.replace('text-white', 'text-slate-400');
        btnScanBatch.classList.replace('hover:bg-indigo-700', 'cursor-not-allowed');

        btnClearBatch.classList.add('hidden');
        placeholderBatch.classList.remove('hidden');
        batchResultsTable.classList.add('hidden');
        batchProgressLoader.classList.add('hidden');
        batchStatsCard.classList.add('hidden');
        btnBatchDownloadAll.classList.add('hidden');
        batchTableBody.innerHTML = '';
    }

    // Process Sequential Batch Queue to maintain CPU / GPU resource boundaries gracefully
    btnScanBatch.addEventListener('click', async () => {
        if (batchQueue.length === 0) return;

        // Visual setup
        placeholderBatch.classList.add('hidden');
        batchResultsTable.classList.remove('hidden');
        batchTableBody.innerHTML = '';
        
        batchProgressLoader.classList.remove('hidden');
        btnScanBatch.setAttribute('disabled', 'true');
        btnClearBatch.classList.add('hidden');

        batchOutputs = [];
        const totalFiles = batchQueue.length;
        let successfulScans = 0;
        let cumulativeTime = 0.0;
        let sumConfidence = 0;

        // Create empty rows for each file in queue as a loading visualization
        batchQueue.forEach((file, index) => {
            const tr = document.createElement('tr');
            tr.id = `batch-row-${index}`;
            tr.className = 'hover:bg-slate-50/50 border-b border-slate-100 transition-colors duration-200';
            tr.innerHTML = `
                <td class="px-6 py-4 font-semibold text-slate-700 truncate max-w-[140px]" title="${file.name}">${file.name}</td>
                <td class="px-6 py-4 text-slate-400 font-mono">-</td>
                <td class="px-6 py-4 text-slate-400">-</td>
                <td class="px-6 py-4">
                    <div class="w-16 bg-slate-100 h-1.5 rounded-full overflow-hidden">
                        <div class="bg-indigo-600 h-1.5 w-0"></div>
                    </div>
                </td>
                <td class="px-6 py-4">
                    <span class="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold text-slate-500 bg-slate-100">
                        <i class="fa-solid fa-hourglass-start mr-1.5 animate-spin"></i> Queued
                    </span>
                </td>
                <td class="px-6 py-4 text-right">-</td>
            `;
            batchTableBody.appendChild(tr);
        });

        // Run sequential upload queries
        for (let idx = 0; idx < totalFiles; idx++) {
            const file = batchQueue[idx];
            const row = document.getElementById(`batch-row-${idx}`);

            // Update Progress Bar Indicator
            const currentPct = Math.round((idx / totalFiles) * 100);
            batchLoaderText.textContent = `Analyzing file ${idx + 1} of ${totalFiles}: ${file.name}`;
            batchLoaderPercent.textContent = `${currentPct}%`;
            batchLoaderBar.style.width = `${currentPct}%`;

            // Mark Row as Active
            row.querySelector('td:nth-child(5)').innerHTML = `
                <span class="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold text-indigo-700 bg-indigo-50 border border-indigo-100">
                    <i class="fa-solid fa-spinner mr-1.5 animate-spin"></i> Processing
                </span>
            `;

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/api/extract', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();

                if (result.success && result.data) {
                    successfulScans++;
                    cumulativeTime += parseFloat(result.processing_time || 0);
                    sumConfidence += (result.data.confidence || 0);

                    batchOutputs.push({
                        filename: file.name,
                        success: true,
                        data: result.data,
                        processing_time: result.processing_time
                    });

                    // Update Row with Extracted Info
                    updateBatchTableRow(row, result.data, idx);
                } else {
                    throw new Error(result.error || 'Server rejected request');
                }
            } catch (err) {
                console.error(`Error scanning index ${idx}:`, err);
                batchOutputs.push({
                    filename: file.name,
                    success: false,
                    error: err.message || 'Processing Error'
                });

                // Update Row as Error
                updateBatchTableRowError(row, err.message || 'Failed OCR');
            }
        }

        // Mark Loader as Complete
        batchLoaderText.textContent = `Processing session finalized. ${successfulScans} of ${totalFiles} images completed successfully.`;
        batchLoaderPercent.textContent = '100%';
        batchLoaderBar.style.width = '100%';
        batchLoaderBar.className = "bg-emerald-500 h-2 rounded-full transition-all duration-300";

        // Display Session Statistics Card
        const avgConfVal = successfulScans > 0 ? Math.round((sumConfidence / successfulScans) * 100) : 0;
        
        document.getElementById('stats-total').textContent = totalFiles;
        document.getElementById('stats-success').textContent = successfulScans;
        document.getElementById('stats-avg-conf').textContent = `${avgConfVal}%`;
        document.getElementById('stats-time').textContent = `${cumulativeTime.toFixed(2)}s`;
        
        batchStatsCard.classList.remove('hidden');
        batchStatsCard.classList.add('fade-in');

        if (successfulScans > 0) {
            btnBatchDownloadAll.classList.remove('hidden');
        }
        btnClearBatch.classList.remove('hidden');
    });

    function updateBatchTableRow(row, data, listIndex) {
        const pct = Math.round(data.confidence * 100);
        let barClass = 'bg-rose-500';
        let badgeClass = 'text-rose-700 bg-rose-50';
        if (pct >= 85) {
            barClass = 'bg-emerald-500';
            badgeClass = 'text-emerald-700 bg-emerald-50';
        } else if (pct >= 60) {
            barClass = 'bg-amber-500';
            badgeClass = 'text-amber-700 bg-amber-50';
        }

        row.querySelector('td:nth-child(2)').textContent = data.passport_number || 'N/A';
        row.querySelector('td:nth-child(2)').className = 'px-6 py-4 font-mono font-bold text-slate-800';
        row.querySelector('td:nth-child(3)').textContent = data.full_name || 'N/A';
        row.querySelector('td:nth-child(3)').className = 'px-6 py-4 font-semibold text-slate-800';
        row.querySelector('td:nth-child(4)').innerHTML = `
            <div class="flex items-center space-x-2">
                <div class="w-16 bg-slate-100 h-1.5 rounded-full overflow-hidden">
                    <div class="${barClass} h-1.5" style="width: ${pct}%"></div>
                </div>
                <span class="text-[11px] font-bold text-slate-600">${pct}%</span>
            </div>
        `;
        row.querySelector('td:nth-child(5)').innerHTML = `
            <span class="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-100 shadow-sm">
                <span class="h-1.5 w-1.5 rounded-full bg-emerald-500 mr-1.5"></span> Success
            </span>
        `;
        
        // Modal Trigger inspect button
        row.querySelector('td:nth-child(6)').innerHTML = `
            <button onclick="inspectBatchJSON(${listIndex})" class="text-indigo-600 hover:text-indigo-900 hover:bg-indigo-50 p-1.5 rounded-lg text-xs font-semibold flex items-center justify-end space-x-1 ml-auto">
                <i class="fa-solid fa-code"></i>
                <span>Inspect JSON</span>
            </button>
        `;
    }

    function updateBatchTableRowError(row, errorMsg) {
        row.querySelector('td:nth-child(5)').innerHTML = `
            <span class="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold text-rose-700 bg-rose-50 border border-rose-100">
                <i class="fa-solid fa-circle-xmark mr-1.5"></i> Failed
            </span>
        `;
        row.querySelector('td:nth-child(6)').textContent = errorMsg;
        row.querySelector('td:nth-child(6)').className = 'px-6 py-4 text-right text-[11px] text-slate-400 font-medium truncate max-w-[120px]';
    }

    // Global inspect access binded dynamically
    window.inspectBatchJSON = function(index) {
        const output = batchOutputs[index];
        if (output && output.success) {
            const modal = document.getElementById('json-modal');
            const content = document.getElementById('modal-json-content');
            content.textContent = JSON.stringify(output.data, null, 2);
            modal.classList.remove('hidden');
        }
    };

    // Close Modal Bindings
    const closeModal = () => document.getElementById('json-modal').classList.add('hidden');
    document.getElementById('btn-close-modal').addEventListener('click', closeModal);
    document.getElementById('modal-overlay').addEventListener('click', closeModal);
    
    document.getElementById('btn-modal-copy').addEventListener('click', () => {
        const text = document.getElementById('modal-json-content').textContent;
        copyTextToClipboard(text);
    });

    // Batch Export All Trigger
    btnBatchDownloadAll.addEventListener('click', () => {
        if (batchOutputs.length === 0) return;
        downloadJSON(JSON.stringify(batchOutputs, null, 2), `passport_batch_results.json`);
    });


    // ==========================================
    // 3. UTILITY HELPER FUNCTIONS
    // ==========================================
    async function checkAPIStatus() {
        const dot = document.getElementById('api-status-dot');
        const text = document.getElementById('api-status-text');

        try {
            const res = await fetch('/health');
            const data = await res.json();
            if (data.status === 'healthy') {
                dot.className = 'relative inline-flex rounded-full h-2 w-2 bg-emerald-500';
                text.textContent = data.easyocr_available ? 'Engine Active' : 'Fallback Active';
            } else {
                throw new Error();
            }
        } catch {
            dot.className = 'relative inline-flex rounded-full h-2 w-2 bg-rose-500';
            text.textContent = 'API Offline';
        }
    }

    function switchTab(activeTab, inactiveTab, showView, hideView) {
        activeTab.className = 'tab-btn px-6 py-2.5 rounded-lg text-sm font-semibold bg-white text-slate-900 shadow-sm flex items-center space-x-2';
        inactiveTab.className = 'tab-btn px-6 py-2.5 rounded-lg text-sm font-semibold text-slate-600 hover:text-slate-900 flex items-center space-x-2';
        
        showView.classList.remove('hidden');
        showView.classList.add('fade-in');
        hideView.classList.add('hidden');
    }

    function formatBytes(bytes, decimals = 1) {
        if (!+bytes) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
    }

    function copyTextToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            alert('JSON copied to clipboard successfully!');
        }).catch(err => {
            // Textarea Fallback
            const el = document.createElement('textarea');
            el.value = text;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);
            alert('JSON copied to clipboard successfully!');
        });
    }

    function downloadJSON(text, filename) {
        const blob = new Blob([text], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
});
