document.getElementById("uploadForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const fileInput = document.getElementById("pdfFile");
  const file = fileInput.files[0];

  if (!file) {
      alert("Please select a file.");
      return;
  }

  const loadingIndicator = document.getElementById("loading");
  const resultSection = document.getElementById("result");
  const scriptOutput = document.getElementById("scriptOutput");

  loadingIndicator.style.display = "block";
  resultSection.style.display = "none";

  const formData = new FormData();
  formData.append("pdf_file", file);

  try {
      const response = await fetch("http://127.0.0.1:5000/convert", {
          method: "POST",
          body: formData,
      });

      if (response.ok) {
          const data = await response.json();
          scriptOutput.textContent = data.script;
          loadingIndicator.style.display = "none";
          resultSection.style.display = "block";
      } else {
          throw new Error("Failed to convert the PDF.");
      }
  } catch (error) {
      loadingIndicator.style.display = "none";
      alert("An error occurred: " + error.message);
  }
});

document.getElementById("reset").addEventListener("click", () => {
  document.getElementById("uploadForm").reset();
  document.getElementById("result").style.display = "none";
});
