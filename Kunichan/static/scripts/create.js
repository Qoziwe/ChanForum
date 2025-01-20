const fileInput = document.getElementById("MC-I-F-ImgUpload");
const fileNameDisplay = document.getElementById("MC-I-F-ImgName");
const uploadLabel = document.getElementById("MC-I-F-ImgUploadLabel");

fileInput.addEventListener("change", function () {
  if (this.files.length > 0) {
    fileNameDisplay.textContent = `You selected file: ${this.files[0].name}`;
    uploadLabel.textContent = "Delete image:";
    // uploadLabel.style.backgroundColor = "#FF0000";

    // Добавляем функциональность для удаления изображения
    uploadLabel.addEventListener("click", removeFile);
  } else {
    resetUpload();
  }
});

function removeFile() {
  fileInput.value = "";
  resetUpload();
}

function resetUpload() {
  fileNameDisplay.textContent = "The file is not selected";
  uploadLabel.textContent = "Upload image:";
  //   uploadLabel.style.backgroundColor = "#007BFF";
  uploadLabel.removeEventListener("click", removeFile);
}
