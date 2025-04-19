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

      console.log("Raw Response:", response); // Log response object for debugging

      if (response.ok) {
        // Parse and log the JSON data
        const data = await response.json();
        console.log("Parsed Data:", data);
        scriptOutput.textContent = data.script;
        loadingIndicator.style.display = "none";
        resultSection.style.display = "block";
    } else {
        // Log status and any error text
        console.error("Response Status:", response.status);
        const errorText = await response.text();
        console.error("Error Text:", errorText);
        throw new Error("Failed to convert the PDF. " + errorText);
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
