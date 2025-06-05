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
          facingMode: 'environment', // atau 'user' jika depan
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
    const canvas = document.createElement('canvas');
    canvas.width = desktopVideo.videoWidth;
    canvas.height = desktopVideo.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(desktopVideo, 0, 0, canvas.width, canvas.height);
    const photoData = canvas.toDataURL('image/jpeg');
    localStorage.setItem('capturedImage', photoData); // Simpan gambar ke local storage
    window.location.href = '/preview'; // Arahkan ke halaman preview
  }

  function handleDesktopImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      localStorage.setItem('capturedImage', e.target.result); // Simpan gambar ke local storage
      console.log('Foto yang diunggah:', e.target.result);
      window.location.href = '/preview'; // Arahkan ke halaman preview
    };
    reader.readAsDataURL(file);
  }

  desktopCaptureButton.addEventListener('click', captureDesktopPhoto);
  desktopUploadInput.addEventListener('change', handleDesktopImageUpload);

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
          facingMode: 'environment', // Hanya kamera belakang
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
    const supportsTorch = capabilities && 'torch' in capabilities;

    try {
      track.applyConstraints({
        advanced: [{ torch: true }]
      }).then(() => {
        flashToggle.classList.remove('hidden');
        flashToggle.disabled = false;
      }).catch(() => {
        flashToggle.classList.add('hidden');
        flashToggle.disabled = true;
      });
    } catch (error) {
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
    const canvas = document.createElement('canvas');
    canvas.width = mobileVideo.videoWidth;
    canvas.height = mobileVideo.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(mobileVideo, 0, 0, canvas.width, canvas.height);
    const photoData = canvas.toDataURL('image/jpeg');
    localStorage.setItem('capturedImage', photoData); // Simpan gambar ke local storage
    window.location.href = '/preview'; // Arahkan ke halaman preview
  }

  function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      localStorage.setItem('capturedImage', e.target.result); // Simpan gambar ke local storage
      console.log('Foto yang diunggah:', e.target.result);
      window.location.href = '/preview'; // Arahkan ke halaman preview
    };
    reader.readAsDataURL(file);
  }

  mobileCaptureButton.addEventListener('click', captureMobilePhoto);
  flashToggle.addEventListener('click', toggleFlash);
  mobileUploadInput.addEventListener('change', handleImageUpload);

  startMobileCamera();

  // Focus Circle Implementation
  const focusCircleElement = document.getElementById('focusCircle');

  mobileVideo.addEventListener('click', async (event) => {
    // Pastikan stream sudah ada
    if (!mobileStream) return;

    // Dapatkan koordinat klik relatif terhadap video
    const rect = mobileVideo.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Tampilkan dan posisikan lingkaran fokus
    focusCircleElement.style.left = `${x}px`;
    focusCircleElement.style.top = `${y}px`;
    focusCircleElement.style.transform = 'translate(-50%, -50%)';
    focusCircleElement.style.opacity = '1';

    try {
      // Dapatkan track video
      const track = mobileStream.getVideoTracks()[0];
      
      // Coba fokus manual (bergantung pada dukungan perangkat)
      await track.applyConstraints({
        advanced: [{
          focusMode: 'manual',
          focusDistance: 0
        }]
      });

      // Sembunyikan lingkaran fokus setelah beberapa saat
      setTimeout(() => {
        focusCircleElement.style.opacity = '0';
      }, 1000);

    } catch (error) {
      console.warn('Fokus manual tidak didukung:', error);
      
      // Sembunyikan lingkaran fokus
      setTimeout(() => {
        focusCircleElement.style.opacity = '0';
      }, 1000);
    }
  });


});