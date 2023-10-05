document.addEventListener('DOMContentLoaded', function () {
    const imageInput = document.querySelector('#webcam_image');
    const imagePreview = document.querySelector('#image-preview');
    const previewImage = document.querySelector('#preview-image');
    const saveImageBtn = document.querySelector('#save-image');

    imageInput.addEventListener('change', function () {
        const file = imageInput.files[0];

        if (file) {
            const reader = new FileReader();

            reader.onload = function (e) {
                previewImage.src = e.target.result;
                imagePreview.style.display = 'block';
            };

            reader.readAsDataURL(file);
        }
    });

    saveImageBtn.addEventListener('click', function () {
        // Save the image here (you can use AJAX to send it to the server).
        // Then, close the preview and reset the input field.
        imagePreview.style.display = 'none';
        imageInput.value = '';
    });
});
