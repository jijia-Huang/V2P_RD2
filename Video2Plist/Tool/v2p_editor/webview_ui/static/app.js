// V2P Editor WebView JavaScript

let currentReport = null;
let currentFrames = [];
let currentFrameIndex = 0;
let isPlaying = false;
let playInterval = null;
let frameImages = {}; // 緩存已載入的影格圖片
let isUserScrolling = false; // 標記用戶是否正在手動滾動
let scrollTimeout = null; // 滾動超時計時器

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    // 支援 Enter 鍵載入資料夾
    const folderPathInput = document.getElementById('folder-path');
    if (folderPathInput) {
        folderPathInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                loadFolder();
            }
        });
    }

    // 支援拖放
    setupDragAndDrop();
    
    // 監聽影格列表的滾動事件，檢測用戶手動滾動
    const framesContainer = document.querySelector('.frames-container');
    if (framesContainer) {
        let lastScrollTop = framesContainer.scrollTop;
        let isProgrammaticScroll = false;
        
        framesContainer.addEventListener('wheel', function(e) {
            // 用戶手動滾動
            isUserScrolling = true;
            // 清除之前的計時器
            if (scrollTimeout) {
                clearTimeout(scrollTimeout);
            }
            // 3秒後重置標記（假設用戶停止滾動）
            scrollTimeout = setTimeout(function() {
                isUserScrolling = false;
            }, 3000);
        });
        
        framesContainer.addEventListener('scroll', function(e) {
            const currentScrollTop = framesContainer.scrollTop;
            
            // 如果是程式觸發的滾動，忽略
            if (isProgrammaticScroll) {
                isProgrammaticScroll = false;
                return;
            }
            
            // 如果滾動位置改變且不是程式觸發的，則是用戶滾動
            if (Math.abs(currentScrollTop - lastScrollTop) > 1) {
                isUserScrolling = true;
                if (scrollTimeout) {
                    clearTimeout(scrollTimeout);
                }
                scrollTimeout = setTimeout(function() {
                    isUserScrolling = false;
                }, 3000);
            }
            
            lastScrollTop = currentScrollTop;
        });
        
        // 攔截所有可能的程式滾動
        const originalScrollIntoView = Element.prototype.scrollIntoView;
        Element.prototype.scrollIntoView = function(...args) {
            // 如果正在播放，完全阻止自動滾動
            if (isPlaying) {
                return;
            }
            // 否則正常執行
            isProgrammaticScroll = true;
            return originalScrollIntoView.apply(this, args);
        };
    }
});

// 設置拖放功能
function setupDragAndDrop() {
    const container = document.querySelector('.app-container');
    
    container.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        container.style.backgroundColor = '#e3f2fd';
    });

    container.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        container.style.backgroundColor = '';
    });

    container.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        container.style.backgroundColor = '';

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            // 檢查是否為資料夾（在瀏覽器中無法直接獲取資料夾路徑）
            // 所以這裡只處理檔案路徑，實際使用時需要通過 API 選擇資料夾
            if (file.path) {
                const folderPath = file.path.substring(0, file.path.lastIndexOf('\\'));
                document.getElementById('folder-path').value = folderPath;
                loadFolder(folderPath);
            }
        }
    });
}

// 瀏覽資料夾
async function browseFolder() {
    if (!window.pywebview || !window.pywebview.api) {
        showMessage('無法連接到後端 API', 'error');
        return;
    }

    try {
        const result = await window.pywebview.api.selectFolder();
        if (result && result.success) {
            document.getElementById('folder-path').value = result.path;
            await loadFolder(result.path);
        } else {
            showMessage(result ? result.error : '選擇資料夾失敗', 'error');
        }
    } catch (error) {
        showMessage(`選擇資料夾失敗：${error.message || error}`, 'error');
    }
}

// 載入資料夾
async function loadFolder(folderPath) {
    const pathInput = document.getElementById('folder-path');
    const path = folderPath || pathInput.value.trim();

    if (!path) {
        showMessage('請輸入資料夾路徑', 'error');
        return;
    }

    if (!window.pywebview || !window.pywebview.api) {
        showMessage('無法連接到後端 API', 'error');
        return;
    }

    // 更新狀態
    updateStatus('正在檢查資料夾...');

    try {
        const result = await window.pywebview.api.inspectFolder(path);
        if (result && result.success) {
            currentReport = result.report;
            updateStatus(`已載入：${currentReport.folder}`);
            populateMetadata();
            populateFiles();
            populateLogs();
            await populateFrames();
            document.getElementById('content-panel').style.display = 'block';
        } else {
            showMessage(result ? result.error : '檢查資料夾失敗', 'error');
            updateStatus('載入失敗');
            document.getElementById('content-panel').style.display = 'none';
        }
    } catch (error) {
        showMessage(`載入失敗：${error.message || error}`, 'error');
        updateStatus('載入失敗');
        document.getElementById('content-panel').style.display = 'none';
    }
}

// 更新狀態
function updateStatus(message) {
    const statusEl = document.getElementById('status');
    if (statusEl) {
        statusEl.textContent = message;
    }
}

// 填充 Metadata
function populateMetadata() {
    if (!currentReport || !currentReport.metadata) {
        return;
    }

    const meta = currentReport.metadata;
    document.getElementById('info-name').textContent = meta.name || currentReport.name || '--';
    document.getElementById('info-fps').textContent = meta.fps || '--';
    document.getElementById('info-frame-count').textContent = meta.frame_count || '--';
    document.getElementById('info-plist-count').textContent = meta.plist_count || '--';
    
    const maxWidth = meta.max_width || '-';
    const maxHeight = meta.max_height || '-';
    document.getElementById('info-max-size').textContent = `${maxWidth}x${maxHeight}`;
    
    document.getElementById('info-frame-size').textContent = meta.frame_size || '--';
    document.getElementById('info-creation-time').textContent = meta.creation_time || '--';
    document.getElementById('info-tool-version').textContent = meta.tool_version || '--';
    document.getElementById('info-output-format').textContent = meta.output_format || '--';

    // 設置 FPS
    if (meta.fps) {
        document.getElementById('fps-input').value = meta.fps;
    }
}

// 填充檔案狀態
function populateFiles() {
    if (!currentReport || !currentReport.file_status) {
        return;
    }

    const tbody = document.getElementById('file-table-body');
    tbody.innerHTML = '';

    currentReport.file_status.forEach(status => {
        const tr = document.createElement('tr');
        const statusText = status.exists ? '✅ 正常' : '⚠ 缺少';
        const extraText = status.extra && status.extra !== 'OK' ? ` - ${status.extra}` : '';
        
        tr.innerHTML = `
            <td>${status.path}</td>
            <td>${statusText}${extraText}</td>
        `;
        tbody.appendChild(tr);
    });
}

// 填充錯誤/警示
function populateLogs() {
    if (!currentReport) {
        return;
    }

    const logContent = document.getElementById('log-content');
    
    if (!currentReport.errors || currentReport.errors.length === 0) {
        if (!currentReport.warnings || currentReport.warnings.length === 0) {
            logContent.innerHTML = '<div>檔案結構正常，未發現問題。</div>';
            return;
        }
    }

    let html = '';
    if (currentReport.errors && currentReport.errors.length > 0) {
        currentReport.errors.forEach(err => {
            html += `<div class="error">[ERROR] ${err}</div>`;
        });
    }
    if (currentReport.warnings && currentReport.warnings.length > 0) {
        currentReport.warnings.forEach(warn => {
            html += `<div class="warn">[WARN] ${warn}</div>`;
        });
    }

    logContent.innerHTML = html;
}

// 填充影格列表
async function populateFrames() {
    if (!window.pywebview || !window.pywebview.api) {
        return;
    }

    try {
        const result = await window.pywebview.api.getFramesList();
        if (result && result.success) {
            currentFrames = result.frames;
            currentFrameIndex = 0;
            frameImages = {}; // 清除緩存

            const tbody = document.getElementById('frames-table-body');
            tbody.innerHTML = '';

            currentFrames.forEach((frame, idx) => {
                const tr = document.createElement('tr');
                tr.dataset.index = idx;
                tr.innerHTML = `
                    <td>${frame.frame_index}</td>
                    <td>${frame.name}</td>
                    <td>${frame.sheet}</td>
                    <td>${frame.size}</td>
                `;
                tr.addEventListener('click', () => selectFrame(idx));
                if (idx === 0) {
                    tr.classList.add('selected');
                }
                tbody.appendChild(tr);
            });

            // 載入第一個影格
            if (currentFrames.length > 0) {
                await showFrame(0);
            }
        }
    } catch (error) {
        console.error('取得影格列表失敗:', error);
    }
}

// 選擇影格
async function selectFrame(index) {
    pausePlayback();
    
    // 更新選中狀態（手動選擇時才滾動）
    const rows = document.querySelectorAll('#frames-table-body tr');
    rows.forEach((row, idx) => {
        if (idx === index) {
            row.classList.add('selected');
            // 手動選擇時才滾動到可見位置
            row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
            row.classList.remove('selected');
        }
    });

    await showFrame(index);
}

// 顯示影格
async function showFrame(index) {
    if (index < 0 || index >= currentFrames.length) {
        return;
    }

    currentFrameIndex = index;
    const frame = currentFrames[index];

    // 更新計數器
    document.getElementById('frame-counter').textContent = `${index + 1}/${currentFrames.length}`;
    
    // 更新詳細資訊
    document.getElementById('frame-detail').textContent = 
        `${frame.name} | ${frame.sheet} | ${frame.size}`;

    // 載入圖片
    if (!window.pywebview || !window.pywebview.api) {
        return;
    }

    try {
        // 檢查緩存
        if (frameImages[index]) {
            displayFrameImage(frameImages[index]);
            return;
        }

        const result = await window.pywebview.api.getFrameImage(index);
        if (result && result.success) {
            frameImages[index] = result.image;
            displayFrameImage(result.image);
        } else {
            console.error('取得影格圖片失敗:', result ? result.error : '未知錯誤');
        }
    } catch (error) {
        console.error('載入影格失敗:', error);
    }
}

// 顯示影格圖片
function displayFrameImage(imageData) {
    const img = document.getElementById('preview-image');
    const placeholder = document.getElementById('preview-placeholder');
    
    if (img && imageData) {
        img.src = imageData;
        img.style.display = 'block';
        if (placeholder) {
            placeholder.style.display = 'none';
        }
    }
}

// 顯示上一幀
async function showPreviousFrame() {
    pausePlayback();
    if (currentFrames.length === 0) return;
    
    const prevIndex = currentFrameIndex > 0 ? currentFrameIndex - 1 : currentFrames.length - 1;
    await showFrame(prevIndex);
    
    // 更新選中狀態（手動切換時才滾動）
    const rows = document.querySelectorAll('#frames-table-body tr');
    rows.forEach((row, idx) => {
        if (idx === prevIndex) {
            row.classList.add('selected');
            // 使用 'nearest' 避免過度滾動
            row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
            row.classList.remove('selected');
        }
    });
}

// 顯示下一幀
async function showNextFrame() {
    pausePlayback();
    if (currentFrames.length === 0) return;
    
    const nextIndex = currentFrameIndex < currentFrames.length - 1 ? currentFrameIndex + 1 : 0;
    await showFrame(nextIndex);
    
    // 更新選中狀態（手動切換時才滾動）
    const rows = document.querySelectorAll('#frames-table-body tr');
    rows.forEach((row, idx) => {
        if (idx === nextIndex) {
            row.classList.add('selected');
            // 使用 'nearest' 避免過度滾動
            row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
            row.classList.remove('selected');
        }
    });
}

// 開始播放
function startPlayback() {
    if (currentFrames.length === 0) return;
    
    isPlaying = true;
    const fps = parseFloat(document.getElementById('fps-input').value) || 24;
    const delay = 1000 / fps;

    playInterval = setInterval(async () => {
        if (!isPlaying) {
            clearInterval(playInterval);
            return;
        }

        const loop = document.getElementById('loop-checkbox').checked;
        const nextIndex = currentFrameIndex < currentFrames.length - 1 
            ? currentFrameIndex + 1 
            : (loop ? 0 : currentFrames.length - 1);

        if (nextIndex === currentFrames.length - 1 && !loop) {
            pausePlayback();
            return;
        }

        await showFrame(nextIndex);
        
        // 更新選中狀態（播放模式下完全禁用自動滾動，只更新樣式）
        const rows = document.querySelectorAll('#frames-table-body tr');
        const framesContainer = document.querySelector('.frames-container');
        
        // 保存當前滾動位置，防止任何自動滾動
        const savedScrollTop = framesContainer ? framesContainer.scrollTop : 0;
        
        rows.forEach((row, idx) => {
            if (idx === nextIndex) {
                row.classList.add('selected');
                // 播放模式下完全禁用自動滾動，讓用戶可以自由滾動
                // 不調用 scrollIntoView，不調用 focus，只更新選中樣式
                // 確保不會觸發任何滾動
            } else {
                row.classList.remove('selected');
            }
        });
        
        // 強制恢復滾動位置（防止任何自動滾動改變位置）
        if (framesContainer) {
            requestAnimationFrame(() => {
                if (framesContainer.scrollTop !== savedScrollTop) {
                    framesContainer.scrollTop = savedScrollTop;
                }
            });
        }
    }, delay);
}

// 暫停播放
function pausePlayback() {
    isPlaying = false;
    if (playInterval) {
        clearInterval(playInterval);
        playInterval = null;
    }
    // 重置滾動標記
    isUserScrolling = false;
    if (scrollTimeout) {
        clearTimeout(scrollTimeout);
        scrollTimeout = null;
    }
}

// 複製報告
async function copyReport() {
    if (!window.pywebview || !window.pywebview.api) {
        showMessage('無法連接到後端 API', 'error');
        return;
    }

    if (!currentReport) {
        showMessage('請先載入 V2P 輸出資料夾', 'error');
        return;
    }

    try {
        const result = await window.pywebview.api.copyReport();
        if (result && result.success) {
            showMessage(result.message || '已複製 JSON 報告到剪貼簿', 'success');
        } else {
            showMessage(result ? result.error : '複製失敗', 'error');
        }
    } catch (error) {
        showMessage(`複製失敗：${error.message || error}`, 'error');
    }
}

// 顯示訊息
function showMessage(message, type) {
    // 簡單的 alert，可以改進為更美觀的通知
    if (type === 'error') {
        alert(`錯誤：${message}`);
    } else if (type === 'success') {
        alert(`成功：${message}`);
    } else {
        alert(message);
    }
}

