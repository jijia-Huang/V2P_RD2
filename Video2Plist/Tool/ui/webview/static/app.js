// 等待 pywebview API 準備好
function waitForAPI() {
    return new Promise((resolve) => {
        if (window.pywebview && window.pywebview.api) {
            resolve();
        } else {
            window.addEventListener('pywebviewready', () => {
                resolve();
            });
        }
    });
}

// 初始化應用
waitForAPI().then(() => {
    initApp();
});

function initApp() {
    // 初始化版本資訊
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.getVersion().then(version => {
            document.getElementById('version').textContent = version;
        });
    }

    // 頁籤切換
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            switchTab(tabName);
        });
    });

    // Slider 值顯示
    const fpsSlider = document.getElementById('fps');
    const fpsValue = document.getElementById('fps-value');
    if (fpsSlider) {
        fpsSlider.addEventListener('input', (e) => {
            fpsValue.textContent = e.target.value;
        });
        
        // FPS 改變時重新提取預覽影格
        fpsSlider.addEventListener('change', async () => {
            if (window.selectedVideoPath) {
                await extractPreviewFrames(window.selectedVideoPath);
            }
        });
    }

    const qualitySlider = document.getElementById('quality');
    const qualityValue = document.getElementById('quality-value');
    qualitySlider.addEventListener('input', (e) => {
        qualityValue.textContent = e.target.value;
    });

    // Frame 尺寸縮放相關初始化
    const enableFrameResizeCheckbox = document.getElementById('enable-frame-resize');
    const frameResizeOptions = document.getElementById('frame-resize-options');
    const lockAspectRatioCheckbox = document.getElementById('lock-aspect-ratio');
    const frameWidthSlider = document.getElementById('frame-width');
    const frameHeightSlider = document.getElementById('frame-height');
    const frameWidthInput = document.getElementById('frame-width-input');
    const frameHeightInput = document.getElementById('frame-height-input');
    const aspectWidthInput = document.getElementById('aspect-width');
    const aspectHeightInput = document.getElementById('aspect-height');
    const frameSizeInfo = document.getElementById('frame-size-info');
    
    // 儲存原始影片尺寸
    window.originalVideoSize = null;
    
    // 同步滑桿和輸入框的函數
    function syncWidthSliderAndInput(value) {
        if (frameWidthSlider) frameWidthSlider.value = value;
        if (frameWidthInput) frameWidthInput.value = value;
    }
    
    function syncHeightSliderAndInput(value) {
        if (frameHeightSlider) frameHeightSlider.value = value;
        if (frameHeightInput) frameHeightInput.value = value;
    }
    
    // 啟用/停用 Frame 縮放選項
    if (enableFrameResizeCheckbox) {
        enableFrameResizeCheckbox.addEventListener('change', (e) => {
            frameResizeOptions.style.display = e.target.checked ? 'block' : 'none';
            updateFrameSizeInfo();
        });
    }
    
    // 鎖定長寬比處理
    if (lockAspectRatioCheckbox) {
        lockAspectRatioCheckbox.addEventListener('change', (e) => {
            if (e.target.checked && window.originalVideoSize) {
                updateFrameSizeFromAspect();
            }
        });
    }
    
    // 寬度滑桿處理
    if (frameWidthSlider) {
        frameWidthSlider.addEventListener('input', (e) => {
            const value = parseInt(e.target.value);
            syncWidthSliderAndInput(value);
            const lockCheckbox = document.getElementById('lock-aspect-ratio');
            if (lockCheckbox && lockCheckbox.checked) {
                updateHeightFromWidth(value);
            } else {
                updateFrameSizeInfo();
            }
        });
    }
    
    // 寬度輸入框處理
    if (frameWidthInput) {
        frameWidthInput.addEventListener('input', (e) => {
            let value = parseInt(e.target.value) || 1;
            // 限制範圍
            if (value < 1) value = 1;
            if (value > 8192) value = 8192;
            syncWidthSliderAndInput(value);
            const lockCheckbox = document.getElementById('lock-aspect-ratio');
            if (lockCheckbox && lockCheckbox.checked) {
                updateHeightFromWidth(value);
            } else {
                updateFrameSizeInfo();
            }
        });
        
        frameWidthInput.addEventListener('blur', (e) => {
            let value = parseInt(e.target.value) || 1;
            if (value < 1) value = 1;
            if (value > 8192) value = 8192;
            syncWidthSliderAndInput(value);
            const lockCheckbox = document.getElementById('lock-aspect-ratio');
            if (lockCheckbox && lockCheckbox.checked) {
                updateHeightFromWidth(value);
            } else {
                updateFrameSizeInfo();
            }
        });
    }
    
    // 高度滑桿處理
    if (frameHeightSlider) {
        frameHeightSlider.addEventListener('input', (e) => {
            const value = parseInt(e.target.value);
            syncHeightSliderAndInput(value);
            const lockCheckbox = document.getElementById('lock-aspect-ratio');
            if (lockCheckbox && lockCheckbox.checked) {
                updateWidthFromHeight(value);
            } else {
                updateFrameSizeInfo();
            }
        });
    }
    
    // 高度輸入框處理
    if (frameHeightInput) {
        frameHeightInput.addEventListener('input', (e) => {
            let value = parseInt(e.target.value) || 1;
            // 限制範圍
            if (value < 1) value = 1;
            if (value > 8192) value = 8192;
            syncHeightSliderAndInput(value);
            const lockCheckbox = document.getElementById('lock-aspect-ratio');
            if (lockCheckbox && lockCheckbox.checked) {
                updateWidthFromHeight(value);
            } else {
                updateFrameSizeInfo();
            }
        });
        
        frameHeightInput.addEventListener('blur', (e) => {
            let value = parseInt(e.target.value) || 1;
            if (value < 1) value = 1;
            if (value > 8192) value = 8192;
            syncHeightSliderAndInput(value);
            const lockCheckbox = document.getElementById('lock-aspect-ratio');
            if (lockCheckbox && lockCheckbox.checked) {
                updateWidthFromHeight(value);
            } else {
                updateFrameSizeInfo();
            }
        });
    }
    
    // 比例輸入處理
    if (aspectWidthInput && aspectHeightInput) {
        aspectWidthInput.addEventListener('input', () => {
            if (lockAspectRatioCheckbox && lockAspectRatioCheckbox.checked) {
                updateFrameSizeFromAspect();
            }
        });
        aspectHeightInput.addEventListener('input', () => {
            if (lockAspectRatioCheckbox && lockAspectRatioCheckbox.checked) {
                updateFrameSizeFromAspect();
            }
        });
    }

    const cleanupDaysSlider = document.getElementById('cleanup-days');
    const cleanupDaysValue = document.getElementById('cleanup-days-value');
    if (cleanupDaysSlider) {
        cleanupDaysSlider.addEventListener('input', (e) => {
            cleanupDaysValue.textContent = e.target.value;
        });
    }

    // 輸出名稱改變時更新輸出路徑
    const outputNameInput = document.getElementById('output-name');
    outputNameInput.addEventListener('input', updateOutputPath);

    // 輸出格式改變時，檢查是否需要禁用去背
    const outputFormatSelect = document.getElementById('output-format');
    const enableBgRemovalCheckbox = document.getElementById('enable-bg-removal-convert');
    if (outputFormatSelect && enableBgRemovalCheckbox) {
        outputFormatSelect.addEventListener('change', (e) => {
            if (e.target.value === 'JPG') {
                enableBgRemovalCheckbox.checked = false;
                enableBgRemovalCheckbox.disabled = true;
            } else {
                enableBgRemovalCheckbox.disabled = false;
            }
        });
        // 初始化時檢查
        if (outputFormatSelect.value === 'JPG') {
            enableBgRemovalCheckbox.disabled = true;
        }
    }

    // 轉換按鈕
    const convertBtn = document.getElementById('convert-btn');
    if (convertBtn) {
        convertBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('轉換按鈕被點擊');
            handleConvert().catch(err => {
                console.error('轉換函數執行錯誤：', err);
            });
        });
    } else {
        console.error('找不到 convert-btn 元素');
    }

    // 載入設定
    loadSettings();
    loadOutputList();
    updateOutputPath();
    loadBgRemovalTolerance();

    // 去背預覽相關初始化
    const toleranceSlider = document.getElementById('tolerance-slider');
    const toleranceValue = document.getElementById('tolerance-value');
    if (toleranceSlider) {
        toleranceSlider.addEventListener('input', (e) => {
            toleranceValue.textContent = e.target.value;
            // 同步到轉換頁面
            syncBgRemovalTolerance(parseInt(e.target.value));
        });
        toleranceSlider.addEventListener('change', async () => {
            if (window.currentFrameIndex) {
                await previewCurrentFrame();
            }
            // 保存容差值到偏好設定
            if (window.pywebview && window.pywebview.api) {
                await window.pywebview.api.saveBgRemovalPreference({
                    enabled: document.getElementById('enable-bg-removal').checked,
                    tolerance: parseInt(toleranceSlider.value)
                });
            }
        });
    }

    const frameSlider = document.getElementById('frame-slider');
    if (frameSlider) {
        frameSlider.addEventListener('input', (e) => {
            updateFrameInfo(parseInt(e.target.value));
        });
        frameSlider.addEventListener('change', async () => {
            await previewCurrentFrame();
        });
    }

    // 自動載入預覽影格
    loadPreviewFrames();
}

function toggleAccordion(id) {
    const accordion = document.getElementById(id).closest('.accordion');
    accordion.classList.toggle('open');
}

function switchTab(tabName) {
    // 更新按鈕狀態
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // 更新內容顯示
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // 載入對應資料
    if (tabName === 'settings') {
        loadSettings();
    } else if (tabName === 'output') {
        loadOutputList();
    } else if (tabName === 'manage') {
        loadLogList();
    } else if (tabName === 'bg-removal') {
        loadPreviewFrames();
    }
}

function updateOutputPath() {
    const outputName = document.getElementById('output-name').value || 'output';
    const outputPathDisplay = document.getElementById('output-path-display');
    if (outputPathDisplay && window.pywebview && window.pywebview.api) {
        window.pywebview.api.getOutputPath(outputName).then(path => {
            outputPathDisplay.value = path || `videos/v2p_${outputName}/`;
        });
    }
}

// Frame 縮放相關函數
function setAspectRatio(width, height) {
    const aspectWidthInput = document.getElementById('aspect-width');
    const aspectHeightInput = document.getElementById('aspect-height');
    if (aspectWidthInput && aspectHeightInput) {
        aspectWidthInput.value = width;
        aspectHeightInput.value = height;
        const lockAspectRatioCheckbox = document.getElementById('lock-aspect-ratio');
        if (lockAspectRatioCheckbox && lockAspectRatioCheckbox.checked) {
            updateFrameSizeFromAspect();
        }
    }
}

function setOriginalAspectRatio() {
    if (window.originalVideoSize) {
        const { width, height } = window.originalVideoSize;
        setAspectRatio(width, height);
    }
}

function updateFrameSizeFromAspect() {
    const aspectWidth = parseInt(document.getElementById('aspect-width').value) || 16;
    const aspectHeight = parseInt(document.getElementById('aspect-height').value) || 9;
    const aspectRatio = aspectWidth / aspectHeight;
    
    const frameWidthSlider = document.getElementById('frame-width');
    const frameWidthInput = document.getElementById('frame-width-input');
    const currentWidth = frameWidthSlider ? parseInt(frameWidthSlider.value) : (frameWidthInput ? parseInt(frameWidthInput.value) : 1920);
    const newHeight = Math.round(currentWidth / aspectRatio);
    
    // 同步更新高度滑桿和輸入框
    const frameHeightSlider = document.getElementById('frame-height');
    const frameHeightInput = document.getElementById('frame-height-input');
    if (frameHeightSlider) frameHeightSlider.value = newHeight;
    if (frameHeightInput) frameHeightInput.value = newHeight;
    updateFrameSizeInfo();
}

function updateHeightFromWidth(width) {
    const aspectWidth = parseInt(document.getElementById('aspect-width').value) || 16;
    const aspectHeight = parseInt(document.getElementById('aspect-height').value) || 9;
    const aspectRatio = aspectWidth / aspectHeight;
    const newHeight = Math.round(width / aspectRatio);
    
    // 同步更新滑桿和輸入框
    const frameHeightSlider = document.getElementById('frame-height');
    const frameHeightInput = document.getElementById('frame-height-input');
    if (frameHeightSlider) frameHeightSlider.value = newHeight;
    if (frameHeightInput) frameHeightInput.value = newHeight;
    updateFrameSizeInfo();
}

function updateWidthFromHeight(height) {
    const aspectWidth = parseInt(document.getElementById('aspect-width').value) || 16;
    const aspectHeight = parseInt(document.getElementById('aspect-height').value) || 9;
    const aspectRatio = aspectWidth / aspectHeight;
    const newWidth = Math.round(height * aspectRatio);
    
    // 同步更新滑桿和輸入框
    const frameWidthSlider = document.getElementById('frame-width');
    const frameWidthInput = document.getElementById('frame-width-input');
    if (frameWidthSlider) frameWidthSlider.value = newWidth;
    if (frameWidthInput) frameWidthInput.value = newWidth;
    updateFrameSizeInfo();
}

function updateFrameSizeInfo() {
    const frameSizeInfo = document.getElementById('frame-size-info');
    if (!frameSizeInfo) return;
    
    const enableResizeCheckbox = document.getElementById('enable-frame-resize');
    const enableResize = enableResizeCheckbox ? enableResizeCheckbox.checked : false;
    if (!enableResize) {
        frameSizeInfo.innerHTML = '<p>ⓘ 提示：請先啟用 Frame 尺寸縮放</p>';
        return;
    }
    
    if (!window.originalVideoSize) {
        frameSizeInfo.innerHTML = '<p>ⓘ 提示：請先上傳影片</p>';
        return;
    }
    
    const originalWidth = window.originalVideoSize.width;
    const originalHeight = window.originalVideoSize.height;
    
    // 從輸入框或滑桿獲取值
    const frameWidthInput = document.getElementById('frame-width-input');
    const frameHeightInput = document.getElementById('frame-height-input');
    const frameWidthSlider = document.getElementById('frame-width');
    const frameHeightSlider = document.getElementById('frame-height');
    
    const targetWidth = frameWidthInput ? parseInt(frameWidthInput.value) : (frameWidthSlider ? parseInt(frameWidthSlider.value) : originalWidth);
    const targetHeight = frameHeightInput ? parseInt(frameHeightInput.value) : (frameHeightSlider ? parseInt(frameHeightSlider.value) : originalHeight);
    
    const originalRatio = (originalWidth / originalHeight).toFixed(2);
    const targetRatio = (targetWidth / targetHeight).toFixed(2);
    
    frameSizeInfo.innerHTML = `<p>ⓘ 原始：${originalWidth}x${originalHeight} (${originalRatio}:1) → 縮放後：${targetWidth}x${targetHeight} (${targetRatio}:1)</p>`;
}

async function selectVideoFile() {
    console.log('selectVideoFile 開始執行');
    if (window.pywebview && window.pywebview.api) {
        try {
            console.log('調用 selectVideoFile API...');
            const result = await window.pywebview.api.selectVideoFile();
            console.log('selectVideoFile API 返回結果：', result);
            
            if (result && result.success) {
                const videoPath = result.path;
                const fileName = videoPath.split(/[/\\]/).pop();
                console.log('影片路徑：', videoPath, '檔案名稱：', fileName);
                
                const videoInfo = document.getElementById('video-info');
                if (!videoInfo) {
                    console.error('找不到 video-info 元素');
                    showMessage('找不到影片資訊顯示區域', 'error');
                    return;
                }
                
                videoInfo.style.display = 'block';
                
                // 儲存檔案路徑供轉換使用
                window.selectedVideoPath = videoPath;
                
                // 獲取影片尺寸並更新 UI
                let videoInfoHTML = `
                    <strong>已選擇檔案：</strong> ${fileName}<br>
                    <strong>完整路徑：</strong> ${videoPath}
                `;
                
                if (result.width && result.height) {
                    console.log('影片尺寸：', result.width, 'x', result.height);
                    window.originalVideoSize = { width: result.width, height: result.height };
                    const aspectRatio = (result.width / result.height).toFixed(2);
                    videoInfoHTML += `<br><strong>原始尺寸：</strong> ${result.width} × ${result.height} 像素 (${aspectRatio}:1)`;
                    
                    // 更新 Frame 縮放預設值
                    try {
                        const frameWidthSlider = document.getElementById('frame-width');
                        const frameHeightSlider = document.getElementById('frame-height');
                        const frameWidthInput = document.getElementById('frame-width-input');
                        const frameHeightInput = document.getElementById('frame-height-input');
                        const aspectWidthEl = document.getElementById('aspect-width');
                        const aspectHeightEl = document.getElementById('aspect-height');
                        
                        // 同步更新滑桿和輸入框
                        if (frameWidthSlider) frameWidthSlider.value = result.width;
                        if (frameWidthInput) frameWidthInput.value = result.width;
                        if (frameHeightSlider) frameHeightSlider.value = result.height;
                        if (frameHeightInput) frameHeightInput.value = result.height;
                        
                        // 更新比例設定
                        const gcd = (a, b) => b === 0 ? a : gcd(b, a % b);
                        const divisor = gcd(result.width, result.height);
                        if (aspectWidthEl) aspectWidthEl.value = result.width / divisor;
                        if (aspectHeightEl) aspectHeightEl.value = result.height / divisor;
                        
                        updateFrameSizeInfo();
                    } catch (e) {
                        console.error('更新 Frame 縮放設定時出錯：', e);
                    }
                } else {
                    console.warn('無法獲取影片尺寸');
                    videoInfoHTML += `<br><small style="color: #999;">⚠️ 無法讀取影片尺寸</small>`;
                }
                
                videoInfo.innerHTML = videoInfoHTML;
                console.log('影片資訊已更新');
                
                // 啟用轉換按鈕
                const convertBtn = document.getElementById('convert-btn');
                if (convertBtn) {
                    convertBtn.disabled = false;
                    console.log('轉換按鈕已啟用');
                } else {
                    console.error('找不到 convert-btn 元素');
                }

                // 自動填入輸出名稱（如果為空）
                const outputNameInput = document.getElementById('output-name');
                if (outputNameInput && !outputNameInput.value) {
                    outputNameInput.value = fileName.replace('.mp4', '');
                    updateOutputPath();
                }

                // 載入影片預覽
                console.log('開始載入影片預覽...');
                try {
                    await loadVideoPreview(videoPath);
                    console.log('影片預覽載入完成');
                } catch (e) {
                    console.error('載入影片預覽失敗：', e);
                }

                // 提取預覽影格
                console.log('開始提取預覽影格...');
                try {
                    await extractPreviewFrames(videoPath);
                    console.log('預覽影格提取完成');
                } catch (e) {
                    console.error('提取預覽影格失敗：', e);
                }
            } else {
                console.error('選擇檔案失敗：', result);
                showMessage(result ? result.error : '選擇檔案失敗', 'error');
            }
        } catch (error) {
            console.error('selectVideoFile 發生錯誤：', error);
            showMessage(`選擇檔案失敗：${error.message || error}`, 'error');
        }
    } else {
        console.error('無法連接到後端 API');
        showMessage('無法連接到後端 API', 'error');
    }
}

async function loadVideoPreview(videoPath) {
    const previewVideo = document.getElementById('preview-video');
    const previewSection = document.getElementById('preview-section');
    
    if (previewVideo && videoPath && previewSection) {
        try {
            // 使用 file:// URL 載入影片
            const videoUrl = `file:///${videoPath.replace(/\\/g, '/')}`;
            previewVideo.src = videoUrl;
            previewSection.style.display = 'block';
            
            // 確保影片載入
            previewVideo.onloadedmetadata = () => {
                console.log('影片載入成功，尺寸：', previewVideo.videoWidth, 'x', previewVideo.videoHeight);
            };
            
            previewVideo.onerror = (e) => {
                console.error('影片載入失敗：', e);
                if (previewSection) {
                    previewSection.innerHTML = '<p style="color: #dc2626;">⚠️ 無法載入影片預覽</p>';
                }
            };
        } catch (error) {
            console.error('載入影片預覽錯誤：', error);
        }
    }
}

async function extractPreviewFrames(videoPath) {
    console.log('extractPreviewFrames 開始執行，影片路徑：', videoPath);
    
    if (!window.pywebview || !window.pywebview.api) {
        console.error('pywebview API 不可用');
        return;
    }

    const previewStatus = document.getElementById('preview-status');
    const previewGallery = document.getElementById('preview-gallery');
    const previewSection = document.getElementById('preview-section');
    
    // 確保預覽區域顯示
    if (previewSection) {
        previewSection.style.display = 'block';
        console.log('預覽區域已顯示');
    } else {
        console.error('找不到 preview-section 元素');
    }
    
    if (previewStatus) {
        previewStatus.textContent = '正在提取預覽影格...';
        previewStatus.style.color = '#666';
    }
    if (previewGallery) {
        previewGallery.innerHTML = '';
    }

    try {
        const fpsEl = document.getElementById('fps');
        const fps = fpsEl ? (parseInt(fpsEl.value) || 24) : 24;
        console.log('FPS：', fps);
        
        const enableResizeCheckbox = document.getElementById('enable-frame-resize');
        const enableResize = enableResizeCheckbox ? enableResizeCheckbox.checked : false;
        // 從輸入框或滑桿獲取值
        const frameWidthInput = document.getElementById('frame-width-input');
        const frameHeightInput = document.getElementById('frame-height-input');
        const frameWidthSlider = document.getElementById('frame-width');
        const frameHeightSlider = document.getElementById('frame-height');
        const targetWidth = enableResize ? (frameWidthInput ? parseInt(frameWidthInput.value) : (frameWidthSlider ? parseInt(frameWidthSlider.value) : 1920)) : null;
        const targetHeight = enableResize ? (frameHeightInput ? parseInt(frameHeightInput.value) : (frameHeightSlider ? parseInt(frameHeightSlider.value) : 1080)) : null;
        const resizeModeRadio = document.querySelector('input[name="resize-mode"]:checked');
        const resizeMode = resizeModeRadio ? resizeModeRadio.value : 'stretch';
        
        console.log('提取預覽影格參數：', {
            videoPath,
            fps,
            enableResize,
            targetWidth,
            targetHeight,
            resizeMode
        });
        
        console.log('調用 extractPreviewFrames API...');
        const result = await window.pywebview.api.extractPreviewFrames({
            videoPath: videoPath,
            fps: fps,
            enableResize: enableResize,
            targetWidth: targetWidth,
            targetHeight: targetHeight,
            resizeMode: resizeMode
        });
        console.log('extractPreviewFrames API 返回結果：', result);

        if (result && result.success) {
            const frames = result.frames || [];
            const frameCount = result.frameCount || 0;
            
            if (previewStatus) {
                previewStatus.textContent = `✅ 已提取 ${frameCount} 個影格供預覽`;
                previewStatus.style.color = '#059669';
            }

            // 顯示預覽影格
            if (previewGallery) {
                previewGallery.innerHTML = '';
                if (frames.length > 0) {
                    frames.forEach((framePath, index) => {
                        const item = document.createElement('div');
                        item.className = 'preview-gallery-item';
                        item.innerHTML = `<img src="file:///${framePath.replace(/\\/g, '/')}" alt="Frame ${index + 1}">`;
                        previewGallery.appendChild(item);
                    });
                } else {
                    previewGallery.innerHTML = '<p style="grid-column: 1 / -1; text-align: center; color: #666;">暫無預覽影格</p>';
                }
            }
        } else {
            if (previewStatus) {
                previewStatus.textContent = `⚠️ 提取預覽影格失敗：${result ? result.error : '未知錯誤'}`;
                previewStatus.style.color = '#dc2626';
            }
        }
    } catch (error) {
        console.error('提取預覽影格錯誤：', error);
        if (previewStatus) {
            previewStatus.textContent = `⚠️ 提取預覽影格失敗：${error.message || error}`;
            previewStatus.style.color = '#dc2626';
        }
    }
}

// FPS 改變時重新提取預覽影格
document.addEventListener('DOMContentLoaded', () => {
    const fpsSlider = document.getElementById('fps');
    if (fpsSlider) {
        fpsSlider.addEventListener('change', async () => {
            if (window.selectedVideoPath) {
                await extractPreviewFrames(window.selectedVideoPath);
            }
        });
    }
});

async function handleConvert() {
    console.log('handleConvert called');
    
    if (!window.selectedVideoPath) {
        showMessage('請先選擇影片檔案', 'error');
        return;
    }

    const videoPath = window.selectedVideoPath;
    const outputNameInput = document.getElementById('output-name');
    const outputName = outputNameInput ? (outputNameInput.value || 'output') : 'output';
    const fps = parseInt(document.getElementById('fps').value) || 24;
    const outputFormat = document.getElementById('output-format').value || 'PNG';
    const quality = parseInt(document.getElementById('quality').value) || 5;
    const maxWidth = parseInt(document.getElementById('max-width').value) || 2048;
    const maxHeight = parseInt(document.getElementById('max-height').value) || 2048;
    const packerRadio = document.querySelector('input[name="packer"]:checked');
    const packerChoice = packerRadio ? packerRadio.value : '自動選擇';
    const useTinyPNG = document.getElementById('use-tinypng') ? document.getElementById('use-tinypng').checked : false;
    const enableBgRemovalCheckbox = document.getElementById('enable-bg-removal-convert');
    const enableBgRemoval = enableBgRemovalCheckbox ? (enableBgRemovalCheckbox.checked && outputFormat === 'PNG') : false;
    const bgRemovalToleranceEl = document.getElementById('bg-removal-tolerance-display');
    const _parsed = bgRemovalToleranceEl ? parseInt(bgRemovalToleranceEl.value, 10) : NaN;
    const bgRemovalTolerance = (!isNaN(_parsed) && _parsed >= 0) ? _parsed : 10;
    
    // Frame 縮放參數
    const enableFrameResizeCheckbox = document.getElementById('enable-frame-resize');
    const enableResize = enableFrameResizeCheckbox ? enableFrameResizeCheckbox.checked : false;
        // 從輸入框或滑桿獲取值
        const frameWidthInput = document.getElementById('frame-width-input');
        const frameHeightInput = document.getElementById('frame-height-input');
        const frameWidthSlider = document.getElementById('frame-width');
        const frameHeightSlider = document.getElementById('frame-height');
        const targetWidth = enableResize ? (frameWidthInput ? parseInt(frameWidthInput.value) : (frameWidthSlider ? parseInt(frameWidthSlider.value) : 1920)) : null;
        const targetHeight = enableResize ? (frameHeightInput ? parseInt(frameHeightInput.value) : (frameHeightSlider ? parseInt(frameHeightSlider.value) : 1080)) : null;
    const resizeModeRadio = document.querySelector('input[name="resize-mode"]:checked');
    const resizeMode = resizeModeRadio ? resizeModeRadio.value : 'stretch';

    console.log('轉換參數：', {
        videoPath,
        outputName,
        fps,
        outputFormat,
        quality,
        maxWidth,
        maxHeight,
        packerChoice,
        useTinyPNG,
        enableBgRemoval,
        bgRemovalTolerance,
        enableResize,
        targetWidth,
        targetHeight,
        resizeMode
    });

    // 顯示進度條
    const progressContainer = document.getElementById('progress-container');
    if (progressContainer) {
        progressContainer.style.display = 'block';
        updateProgress(10, '準備轉換...');
    }

    // 禁用按鈕
    const convertBtn = document.getElementById('convert-btn');
    if (convertBtn) {
        convertBtn.disabled = true;
    }

    // 清除結果顯示
    const resultOutput = document.getElementById('result-output');
    if (resultOutput) {
        resultOutput.innerHTML = '';
    }

    try {
        if (!window.pywebview || !window.pywebview.api) {
            throw new Error('無法連接到後端 API，請確認 WebView 已正確初始化');
        }

        updateProgress(20, '開始轉換...');
        
        console.log('調用 convertVideo API...');
        const result = await window.pywebview.api.convertVideo({
            videoPath: videoPath,
            outputName: outputName,
            fps: fps,
            outputFormat: outputFormat,
            quality: quality,
            maxWidth: maxWidth,
            maxHeight: maxHeight,
            packerChoice: packerChoice,
            useTinyPNG: useTinyPNG,
            enableResize: enableResize,
            targetWidth: targetWidth,
            targetHeight: targetHeight,
            resizeMode: resizeMode,
            enableBgRemoval: enableBgRemoval,
            bgRemovalTolerance: bgRemovalTolerance
        });

        console.log('轉換結果：', result);

        updateProgress(100, '完成');

        if (result && result.success) {
            if (resultOutput) {
                resultOutput.innerHTML = `
                    <div class="success-message">
                        <strong>✅ 轉換成功！</strong><br>
                        輸出位置：${result.outputPath || 'videos 目錄'}<br>
                        動畫名稱：${outputName}
                    </div>
                `;
            }
            loadOutputList();
        } else {
            if (resultOutput) {
                resultOutput.innerHTML = `
                    <div class="error-message">
                        <strong>❌ 轉換失敗</strong><br>
                        ${result ? (result.error || '未知錯誤') : '未返回結果'}
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('轉換錯誤：', error);
        if (resultOutput) {
            resultOutput.innerHTML = `
                <div class="error-message">
                    <strong>❌ 轉換失敗</strong><br>
                    ${error.message || error}
                </div>
            `;
        }
    } finally {
        if (convertBtn) {
            convertBtn.disabled = false;
        }
        if (progressContainer) {
            setTimeout(() => {
                progressContainer.style.display = 'none';
            }, 2000);
        }
    }
}

function updateProgress(percent, message) {
    document.getElementById('progress-fill').style.width = `${percent}%`;
    document.getElementById('progress-text').textContent = `${percent}% - ${message}`;
}

function showMessage(message, type) {
    const messageEl = document.getElementById('result-message');
    messageEl.textContent = message;
    messageEl.className = `result-message ${type}`;
    messageEl.style.display = 'block';

    setTimeout(() => {
        messageEl.style.display = 'none';
    }, 5000);
}

async function loadSettings() {
    if (window.pywebview && window.pywebview.api) {
        const settings = await window.pywebview.api.getSettings();
        if (settings) {
            document.getElementById('ffmpeg-path').value = settings.ffmpegPath || '';
            document.getElementById('texture-packer-path').value = settings.texturePackerPath || '';
            document.getElementById('tinypng-key').value = settings.tinypngKey || '';
        }
    }
}

async function loadBgRemovalTolerance() {
    if (window.pywebview && window.pywebview.api) {
        try {
            const tolerance = await window.pywebview.api.getBgRemovalTolerance();
            const enabled = await window.pywebview.api.getBgRemovalEnabled();
            
            const toleranceDisplay = document.getElementById('bg-removal-tolerance-display');
            const enableBgRemovalCheckbox = document.getElementById('enable-bg-removal-convert');
            
            if (toleranceDisplay) {
                // 容差 0 是有效值，不可用 || 10 否則 0 會被改成 10
                toleranceDisplay.value = (tolerance !== undefined && tolerance !== null && tolerance !== '') ? tolerance : 10;
            }
            
            if (enableBgRemovalCheckbox) {
                enableBgRemovalCheckbox.checked = enabled || false;
            }
        } catch (error) {
            console.error('載入去背設定失敗：', error);
        }
    }
}

function syncBgRemovalTolerance(tolerance) {
    const toleranceDisplay = document.getElementById('bg-removal-tolerance-display');
    if (toleranceDisplay) {
        toleranceDisplay.value = tolerance;
    }
}

function updateSettings() {
    loadSettings();
}

async function saveSettings() {
    if (window.pywebview && window.pywebview.api) {
        const tinypngKey = document.getElementById('tinypng-key').value;
        const result = await window.pywebview.api.saveSettings({
            tinypngKey: tinypngKey
        });
        
        const statusEl = document.getElementById('save-status');
        if (result && result.success) {
            statusEl.textContent = '✅ 設定已儲存';
            statusEl.className = 'status-message success';
        } else {
            statusEl.textContent = `❌ 儲存失敗：${result ? result.error : '未知錯誤'}`;
            statusEl.className = 'status-message error';
        }
    }
}

async function testTexturePacker() {
    if (window.pywebview && window.pywebview.api) {
        const path = document.getElementById('texture-packer-path').value;
        const result = await window.pywebview.api.testTexturePacker(path);
        
        const testResultEl = document.getElementById('test-result');
        testResultEl.style.display = 'block';
        if (result && result.success) {
            testResultEl.textContent = result.message || '✅ TexturePacker 可用';
            testResultEl.className = 'test-result success';
        } else {
            testResultEl.textContent = result ? result.error : '❌ TexturePacker 無法執行';
            testResultEl.className = 'test-result error';
        }
    }
}

async function loadOutputList() {
    if (window.pywebview && window.pywebview.api) {
        const outputs = await window.pywebview.api.getOutputList();
        const selector = document.getElementById('output-selector');
        
        selector.innerHTML = '<option value="">請選擇...</option>';
        if (outputs && outputs.length > 0) {
            outputs.forEach(output => {
                const option = document.createElement('option');
                option.value = output.name;
                option.textContent = output.name;
                selector.appendChild(option);
            });
        }
    }
}

function refreshOutputList() {
    loadOutputList();
}

function previewAnimation() {
    const selector = document.getElementById('output-selector');
    const selected = selector.value;
    if (!selected) {
        showMessage('請先選擇動畫', 'error');
        return;
    }
    // TODO: 實作預覽功能
    showMessage('預覽功能開發中', 'error');
}

function exportAnimation() {
    const selector = document.getElementById('output-selector');
    const selected = selector.value;
    if (!selected) {
        showMessage('請先選擇動畫', 'error');
        return;
    }
    // TODO: 實作匯出功能
    showMessage('匯出功能開發中', 'error');
}

function clearForm() {
    document.getElementById('output-name').value = '';
    document.getElementById('video-info').style.display = 'none';
    document.getElementById('result-output').innerHTML = '';
    document.getElementById('result-message').style.display = 'none';
    window.selectedVideoPath = null;
    document.getElementById('convert-btn').disabled = true;
    updateOutputPath();
}

function cleanupOldFiles() {
    const days = parseInt(document.getElementById('cleanup-days').value);
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.cleanupOldFiles(days).then(result => {
            const outputEl = document.getElementById('manage-output');
            if (result && result.success) {
                outputEl.textContent = `✅ 已清理 ${days} 天前的檔案`;
                outputEl.className = 'status-message success';
            } else {
                outputEl.textContent = `❌ 清理失敗：${result ? result.error : '未知錯誤'}`;
                outputEl.className = 'status-message error';
            }
        });
    }
}

function analyzeDiskUsage() {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.analyzeDiskUsage().then(result => {
            const outputEl = document.getElementById('manage-output');
            if (result && result.success) {
                outputEl.innerHTML = `
                    <strong>磁碟使用分析：</strong><br>
                    總大小：${result.totalSize || 'N/A'}<br>
                    已使用：${result.usedSize || 'N/A'}<br>
                    可用空間：${result.freeSize || 'N/A'}
                `;
                outputEl.className = 'status-message';
            } else {
                outputEl.textContent = `❌ 分析失敗：${result ? result.error : '未知錯誤'}`;
                outputEl.className = 'status-message error';
            }
        });
    }
}

function openOutputFolder() {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.openOutputFolder().then(result => {
            if (result && result.success) {
                showMessage('已開啟輸出資料夾', 'success');
            } else {
                showMessage('開啟失敗', 'error');
            }
        });
    }
}

function loadLogList() {
    // TODO: 實作日誌列表載入
}

function viewLog() {
    const selector = document.getElementById('log-selector');
    const selected = selector.value;
    if (!selected) {
        showMessage('請先選擇日誌檔案', 'error');
        return;
    }
    // TODO: 實作日誌查看功能
    showMessage('日誌查看功能開發中', 'error');
}

// 去背預覽相關功能
let previewFramesCache = {};
let previewFramesList = [];

async function loadPreviewFrames() {
    if (!window.pywebview || !window.pywebview.api) return;

    const statusEl = document.getElementById('bg-removal-status');
    statusEl.textContent = '🔄 正在載入轉換頁面的影格...';

    try {
        const result = await window.pywebview.api.loadPreviewFrames();
        
        if (result && result.success) {
            previewFramesList = result.frames || [];
            const frameCount = result.frameCount || 0;
            
            if (frameCount > 0) {
                statusEl.innerHTML = `
                    ✅ 影格已載入完成<br><br>
                    📁 來源：${result.videoName || '未知'}<br>
                    🎬 FPS：${result.fps || 24}<br>
                    📊 影格數量：${frameCount}<br><br>
                    ⚡ 拖動 Slider 可立即預覽
                `;
                statusEl.className = 'status-message success';

                // 更新影格 Slider
                const frameSlider = document.getElementById('frame-slider');
                frameSlider.max = frameCount;
                frameSlider.value = 1;
                updateFrameInfo(1);
            } else {
                statusEl.innerHTML = `
                    💡 請先到「轉換」頁面處理影片<br><br>
                    轉換時會自動提取影格供此頁面預覽使用<br><br>
                    🔄 處理完成後，此頁面會自動載入影格
                `;
                statusEl.className = 'status-message';
            }
        } else {
            statusEl.textContent = `❌ 載入失敗：${result ? result.error : '未知錯誤'}`;
            statusEl.className = 'status-message error';
        }
    } catch (error) {
        statusEl.textContent = `❌ 載入失敗：${error.message || error}`;
        statusEl.className = 'status-message error';
    }
}

function updateFrameInfo(frameIndex) {
    const frameInfoEl = document.getElementById('frame-info');
    if (previewFramesList.length > 0) {
        frameInfoEl.textContent = `第 ${frameIndex} 幀 / 共 ${previewFramesList.length} 幀`;
        window.currentFrameIndex = frameIndex;
    } else {
        frameInfoEl.textContent = '請先提取影格';
    }
}

async function previewCurrentFrame() {
    if (!window.pywebview || !window.pywebview.api) return;

    const frameSlider = document.getElementById('frame-slider');
    const toleranceSlider = document.getElementById('tolerance-slider');
    
    if (!frameSlider || !toleranceSlider) return;

    const frameIndex = parseInt(frameSlider.value);
    const tolerance = parseInt(toleranceSlider.value);

    if (previewFramesList.length === 0) {
        showMessage('請先載入影格', 'error');
        return;
    }

    const frameIdx = frameIndex - 1;
    if (frameIdx < 0 || frameIdx >= previewFramesList.length) {
        showMessage('影格索引超出範圍', 'error');
        return;
    }

    const previewMessageEl = document.getElementById('bg-removal-preview-message');
    previewMessageEl.textContent = '正在處理預覽...';

    try {
        // 檢查快取
        const cacheKey = `${frameIdx}_${tolerance}`;
        if (previewFramesCache[cacheKey]) {
            const cached = previewFramesCache[cacheKey];
            displayPreviewImages(cached.original, cached.processed);
            previewMessageEl.innerHTML = `
                ✅ 預覽完成（從快取載入）<br><br>
                📁 影格：第 ${frameIndex}/${previewFramesList.length} 幀<br>
                🎨 模式：自動檢測（從四個角落）<br>
                📏 容差值：${tolerance}<br>
                🎨 洋紅色區域 = 透明（已去背）<br>
                ⚡ 快取命中！瞬間載入
            `;
            previewMessageEl.className = 'status-message success';
            return;
        }

        const result = await window.pywebview.api.previewBgRemovalFrame({
            framePath: previewFramesList[frameIdx],
            tolerance: tolerance
        });

        if (result && result.success) {
            // 存入快取
            previewFramesCache[cacheKey] = {
                original: result.originalPath,
                processed: result.processedPath
            };

            displayPreviewImages(result.originalPath, result.processedPath);
            
            const cacheSize = Object.keys(previewFramesCache).length;
            previewMessageEl.innerHTML = `
                ✅ 預覽完成<br><br>
                📁 影格：第 ${frameIndex}/${previewFramesList.length} 幀<br>
                🎨 模式：自動檢測（從四個角落）<br>
                📏 容差值：${tolerance}<br>
                🎨 洋紅色區域 = 透明（已去背）<br><br>
                💾 已快取（共 ${cacheSize} 個）<br>
                💡 調整 Slider 會自動預覽，已快取的會瞬間載入
            `;
            previewMessageEl.className = 'status-message success';
        } else {
            previewMessageEl.textContent = `❌ 預覽失敗：${result ? result.error : '未知錯誤'}`;
            previewMessageEl.className = 'status-message error';
        }
    } catch (error) {
        previewMessageEl.textContent = `❌ 預覽失敗：${error.message || error}`;
        previewMessageEl.className = 'status-message error';
    }
}

function displayPreviewImages(originalPath, processedPath) {
    const originalImg = document.getElementById('original-preview');
    const processedImg = document.getElementById('processed-preview');

    if (originalPath) {
        originalImg.src = `file:///${originalPath.replace(/\\/g, '/')}`;
        originalImg.style.display = 'block';
    }

    if (processedPath) {
        processedImg.src = `file:///${processedPath.replace(/\\/g, '/')}`;
        processedImg.style.display = 'block';
    }
}

async function savePreviewImage() {
    if (!window.pywebview || !window.pywebview.api) return;

    const frameSlider = document.getElementById('frame-slider');
    const toleranceSlider = document.getElementById('tolerance-slider');
    
    if (!frameSlider || !toleranceSlider) return;

    const frameIndex = parseInt(frameSlider.value);
    const tolerance = parseInt(toleranceSlider.value);

    if (previewFramesList.length === 0) {
        showMessage('請先載入影格', 'error');
        return;
    }

    const frameIdx = frameIndex - 1;
    const cacheKey = `${frameIdx}_${tolerance}`;
    
    if (!previewFramesCache[cacheKey]) {
        showMessage('請先預覽此影格', 'error');
        return;
    }

    const saveMessageEl = document.getElementById('save-preview-message');
    saveMessageEl.textContent = '正在保存...';

    try {
        const result = await window.pywebview.api.savePreviewImage({
            framePath: previewFramesList[frameIdx],
            tolerance: tolerance
        });

        if (result && result.success) {
            saveMessageEl.textContent = `✅ 已保存到：${result.outputPath || 'videos 目錄'}`;
            saveMessageEl.className = 'status-message success';
        } else {
            saveMessageEl.textContent = `❌ 保存失敗：${result ? result.error : '未知錯誤'}`;
            saveMessageEl.className = 'status-message error';
        }
    } catch (error) {
        saveMessageEl.textContent = `❌ 保存失敗：${error.message || error}`;
        saveMessageEl.className = 'status-message error';
    }
}
