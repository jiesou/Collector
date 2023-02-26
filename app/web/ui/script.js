$ = mdui.$;

const USER_ID = localStorage.getItem("user-id") ||
        Math.random().toString(36).slice(-10) +
        new Date().getTime().toString(32).slice(-4);
localStorage.setItem("user-id", USER_ID);

function ThrowError(error) {
    console.error("Error", error);
    mdui.snackbar(error.message || error);
}

((fileInput, uploadBt) => {
  // 当点击上传图片按钮时触发被隐藏的 input
  uploadBt.on("click", () => fileInput.trigger('click'));
  fileInput.on("change", (e) => {
      // 先让上传图片按钮变灰，防止同时上传多条
      $("#upload-img-bt").attr('disabled', true)
      const data = new FormData();
      for (let file of e.target.files) {
        data.append('file', file);
      }
      fetch("/api/upload_imgs", {
          method: 'POST',
          body: data,
          headers: { 'User-Id': USER_ID }
      }).then((res) => res.json()).then((res) => {
        if (res.code === 0) {
          uploadBt.removeAttr('disabled');
        } else ThrowError(res);
      }).catch((e) => ThrowError(e));
  });
})($("#upload-img-input"), $("#upload-img-bt"));