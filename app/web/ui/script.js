$ = mdui.$;

$("#upload-img-bt").on("click", () => {
    // tks https://stackoverflow.com/a/50782106
    const fileInput = document.createElement("input")
    fileInput.type = 'file'
    fileInput.accept = 'image/*'
    fileInput.style.display = 'none'
    fileInput.multiple = true
    fileInput.onchange = (e) => {
      $("#upload-img-bt").attr('disabled', true)
      const timestamp = String(new Date().getTime());
      const reader = new FileReader();
      const data = new FormData();
      for (let file of e.target.files) {
        data.append('file', file);
      }
      fetch("/upload", {
          method: 'POST',
          body: data,
          headers: { 'X-Timestamp': timestamp,
          'Content-Type': 'multipart/form-data' }
      });
      document.body.removeChild(fileInput);
    }
    document.body.appendChild(fileInput);
    fileInput.click();
});