document.addEventListener('DOMContentLoaded', function () {
    const video = document.getElementById('webcam');
    const canvas = document.getElementById('canvas');
    const captureButton = document.getElementById('capture-button');
    const saveButton = document.getElementById('save-button');
    const imagePreview = document.getElementById('image-preview');

    let stream; // Store the webcam stream for stopping it later

    function startCamera() {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then((streamObj) => {
                stream = streamObj; // Store the stream
                video.srcObject = stream;
            })
            .catch((error) => {
                console.error('Error accessing webcam:', error);
            });
    }

    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach((track) => {
                track.stop();
            });
        }
    }

    captureButton.addEventListener('click', () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);

        // Hide the webcam and capture button
        video.style.display = 'none';
        captureButton.style.display = 'none';

        // Show the single save button
        saveButton.style.display = 'block';
    });

    saveButton.addEventListener('click', () => {
        // Handle saving the image here (you can use AJAX to send it to the server).
        // Then, reset the canvas, hide the image preview, and stop the webcam stream.
        canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
        imagePreview.style.display = 'none';
        saveButton.style.display = 'none';

        stopCamera(); // Stop the webcam stream

        // Show the webcam and capture button
        video.style.display = 'block';
        captureButton.style.display = 'block';

        startCamera(); // Restart the camera
    });

    // Start the camera when the page loads
    startCamera();
});
