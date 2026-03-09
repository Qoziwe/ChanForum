const fileInput = document.getElementById("profile_image");
const fileNameDisplay = document.getElementById("PU-C-F-ID-ImageName");
const uploadLabel = document.getElementById("PU-C-F-ID-Label");

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

{
  /* <label for="profile_image" id="PU-C-F-ID-Label"
          >Upload New Profile Image:</label
        >
        <input
          type="file"
          id="profile_image"
          name="profile_image"
          accept="image/*"
          style="display: none"
        />
        <p id="PU-C-F-ID-ImageName">The file is not selected</p> */
}
