$ = mdui.$;

const USER_ID = localStorage.getItem("user-id") ||
        Math.random().toString(36).slice(-10) +
        new Date().getTime().toString(32).slice(-4);
localStorage.setItem("user-id", USER_ID);

function ThrowError(error) {
    console.error("Error", error);
    mdui.snackbar(error.message || error);
}

async function refreshImgsRow(img_list) {
  if (!img_list) {
    img_list = await fetch("/api/get_imgs_list", {
        headers: { 'User-Id': USER_ID }
    });
    img_list = await img_list.json();
    img_list = img_list.data || [];
  }
  
  imgs_row = $("#user-imgs-row");

  // 移除所有非 template 的图片
  imgs_row.children(':not(img[class$="-template"])').remove();
  console.log(img_list)
  img_list.forEach((img) => {
    img_ele = imgs_row.children(".user-img-template").clone().removeClass("user-img-template");
    img_ele.attr("src", img.url);
    imgs_row.append(img_ele);
  });
}

((fileInput, uploadBt) => {
  // 图片表格加载出来后再允许上传图片
  refreshImgsRow().then(()=> uploadBt.removeAttr('disabled'));

  // 当点击上传图片按钮时触发被隐藏的 input
  uploadBt.on("click", () => fileInput.trigger('click'));
  fileInput.on("change", (e) => {
      // 先禁止上传图片，防止同时上传多条
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
            refreshImgsRow(res.data).then(()=> uploadBt.removeAttr('disabled'));
        } else ThrowError(res);
      }).catch((e) => ThrowError(e));
  });
})($("#upload-img-input"), $("#upload-img-bt"));

$("#scan-imgs-bt").on("click", () => {
});