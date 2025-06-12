document.addEventListener('DOMContentLoaded', () => {
  /* ======= Desktop Camera Setup ======= */
  const desktopVideo = document.getElementById('desktopCameraPreview');
  const desktopCaptureButton = document.getElementById('desktopCaptureButton');
  const desktopUploadInput = document.getElementById('desktop-upload-input');

  let desktopStream = null;

  async function startDesktopCamera() {
    if (desktopStream) {
      desktopStream.getTracks().forEach(track => track.stop());
    }
    try {
      const constraints = {
        video: {
          facingMode: 'environment',
          width: { ideal: 1920, max: 3840 },
          height: { ideal: 1080, max: 2160 }
        }
      };
      desktopStream = await navigator.mediaDevices.getUserMedia(constraints);
      desktopVideo.srcObject = desktopStream;
      await new Promise(resolve => {
        desktopVideo.onloadedmetadata = () => {
          desktopVideo.play();
          resolve();
        };
      });
    } catch (error) {
      console.error('Error mengakses kamera:', error);
      alert('Tidak dapat mengakses kamera. Pastikan Anda memberikan izin.');
    }
  }

  function captureDesktopPhoto() {
    if (!desktopStream) {
      alert('Kamera belum siap');
      return;
    }
    
    try {
      const canvas = document.createElement('canvas');
      canvas.width = desktopVideo.videoWidth;
      canvas.height = desktopVideo.videoHeight;
      const context = canvas.getContext('2d');
      context.drawImage(desktopVideo, 0, 0, canvas.width, canvas.height);
      
      // Convert to JPEG with good quality
      const photoData = canvas.toDataURL('image/jpeg', 0.8);
      
      console.log('Desktop photo captured, size:', photoData.length);
      localStorage.setItem('capturedImage', photoData);
      window.location.href = '/preview';
    } catch (error) {
      console.error('Error capturing photo:', error);
      alert('Gagal mengambil foto. Silakan coba lagi.');
    }
  }

  function handleDesktopImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Silakan pilih file gambar yang valid.');
      return;
    }
    
    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('Ukuran file terlalu besar. Maksimal 10MB.');
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const imageData = e.target.result;
        console.log('Desktop image uploaded, size:', imageData.length);
        localStorage.setItem('capturedImage', imageData);
        window.location.href = '/preview';
      } catch (error) {
        console.error('Error processing uploaded image:', error);
        alert('Gagal memproses gambar. Silakan coba lagi.');
      }
    };
    reader.onerror = () => {
      alert('Gagal membaca file gambar.');
    };
    reader.readAsDataURL(file);
  }

  if (desktopCaptureButton) {
    desktopCaptureButton.addEventListener('click', captureDesktopPhoto);
  }
  if (desktopUploadInput) {
    desktopUploadInput.addEventListener('change', handleDesktopImageUpload);
  }

  startDesktopCamera();

  /* ======= Mobile Camera Setup ======= */
  const mobileVideo = document.getElementById('cameraPreview');
  const mobileCaptureButton = document.getElementById('captureButton');
  const flashToggle = document.getElementById('flashToggle');
  const mobileUploadInput = document.getElementById('mobile-upload-input');

  let mobileStream = null;
  let torchActive = false;

  async function startMobileCamera() {
    if (mobileStream) {
      mobileStream.getTracks().forEach(track => track.stop());
    }

    try {
      const constraints = {
        video: {
          facingMode: 'environment',
          width: { ideal: 1920, max: 3840 },
          height: { ideal: 1080, max: 2160 }
        }
      };

      mobileStream = await navigator.mediaDevices.getUserMedia(constraints);
      mobileVideo.srcObject = mobileStream;
      await new Promise((resolve) => {
        mobileVideo.onloadedmetadata = () => {
          mobileVideo.play();
          resolve();
        };
      });

      checkTorchCapability();

    } catch (error) {
      console.error('Error mengakses kamera:', error);
      alert('Tidak dapat mengakses kamera. Pastikan Anda memberikan izin.');
    }
  }

  function checkTorchCapability() {
    if (!mobileStream) return;

    const track = mobileStream.getVideoTracks()[0];
    const capabilities = track.getCapabilities();
    
    if (capabilities && 'torch' in capabilities) {
      flashToggle.classList.remove('hidden');
      flashToggle.disabled = false;
    } else {
      flashToggle.classList.add('hidden');
      flashToggle.disabled = true;
    }
  }

  async function toggleFlash() {
    if (!mobileStream) return;

    const track = mobileStream.getVideoTracks()[0];
    
    try {
      torchActive = !torchActive;
      
      await track.applyConstraints({
        advanced: [{ torch: torchActive }]
      });
      
      flashToggle.classList.toggle('text-yellow-500', torchActive);
    } catch (error) {
      console.warn('Gagal mengatur flash:', error);
      torchActive = !torchActive;
      alert('Tidak dapat mengaktifkan flash di perangkat ini.');
    }
  }

  function captureMobilePhoto() {
    if (!mobileStream) {
      alert('Kamera belum siap');
      return;
    }
    
    try {
      const canvas = document.createElement('canvas');
      canvas.width = mobileVideo.videoWidth;
      canvas.height = mobileVideo.videoHeight;
      const context = canvas.getContext('2d');
      context.drawImage(mobileVideo, 0, 0, canvas.width, canvas.height);
      
      // Convert to JPEG with good quality
      const photoData = canvas.toDataURL('image/jpeg', 0.8);
      
      console.log('Mobile photo captured, size:', photoData.length);
      localStorage.setItem('capturedImage', photoData);
      window.location.href = '/preview';
    } catch (error) {
      console.error('Error capturing photo:', error);
      alert('Gagal mengambil foto. Silakan coba lagi.');
    }
  }

  function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Silakan pilih file gambar yang valid.');
      return;
    }
    
    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('Ukuran file terlalu besar. Maksimal 10MB.');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const imageData = e.target.result;
        console.log('Mobile image uploaded, size:', imageData.length);
        localStorage.setItem('capturedImage', imageData);
        window.location.href = '/preview';
      } catch (error) {
        console.error('Error processing uploaded image:', error);
        alert('Gagal memproses gambar. Silakan coba lagi.');
      }
    };
    reader.onerror = () => {
      alert('Gagal membaca file gambar.');
    };
    reader.readAsDataURL(file);
  }

  if (mobileCaptureButton) {
    mobileCaptureButton.addEventListener('click', captureMobilePhoto);
  }
  if (flashToggle) {
    flashToggle.addEventListener('click', toggleFlash);
  }
  if (mobileUploadInput) {
    mobileUploadInput.addEventListener('change', handleImageUpload);
  }

  startMobileCamera();

  // Focus Circle Implementation
  const focusCircleElement = document.getElementById('focusCircle');

  if (mobileVideo && focusCircleElement) {
    mobileVideo.addEventListener('click', async (event) => {
      if (!mobileStream) return;

      const rect = mobileVideo.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      
      focusCircleElement.style.left = `${x}px`;
      focusCircleElement.style.top = `${y}px`;
      focusCircleElement.style.transform = 'translate(-50%, -50%)';
      focusCircleElement.style.opacity = '1';

      try {
        const track = mobileStream.getVideoTracks()[0];
        
        await track.applyConstraints({
          advanced: [{
            focusMode: 'manual',
            focusDistance: 0
          }]
        });

        setTimeout(() => {
          focusCircleElement.style.opacity = '0';
        }, 1000);

      } catch (error) {
        console.warn('Fokus manual tidak didukung:', error);
        
        setTimeout(() => {
          focusCircleElement.style.opacity = '0';
        }, 1000);
      }
    });
  }
});