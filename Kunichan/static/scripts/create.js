const fileInput = document.getElementById("MC-I-F-ImgUpload");
const fileNameDisplay = document.getElementById("MC-I-F-ImgName");
const uploadLabel = document.getElementById("MC-I-F-ImgUploadLabel");

fileInput.addEventListener("change", function () {
  if (this.files.length > 0) {
    fileNameDisplay.textContent = `You selected file: ${this.files[0].name}`;
    uploadLabel.textContent = "Delete image:";
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
  uploadLabel.removeEventListener("click", removeFile);
}
