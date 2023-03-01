$ = mdui.$;

const USER_ID = localStorage.getItem("user-id") ||
        Math.random().toString(36).slice(-10) +
        new Date().getTime().toString(32).slice(-4);
localStorage.setItem("user-id", USER_ID);


async function apiFetch(path, args={}) {
    args = Object.assign(args, {
        method: 'GET',
        headers: { 'User-Id': USER_ID }
    });
    try {
      let res = await fetch(path, args);
      res = await res.json();
      if (res.code === 0) return res.data
    } catch (error) {
      console.error("apiFetch", error);
      mdui.snackbar(error.message);
    }
}


async function refreshImgsRow(img_list) {
  if (!img_list) {
    img_list = await apiFetch("/api/get_imgs_list") || [];
  }
  
  imgs_row = $("#user-imgs-row");

  // 移除所有非 template 的图片
  imgs_row.children(':not(img[class$="-template"])').remove();
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
      apiFetch("/api/upload_imgs", {
          method: 'POST',
          body: data
      }).then((res) => {
          refreshImgsRow(res).then(()=> uploadBt.removeAttr('disabled'));
      });
  });
})($("#upload-img-input"), $("#upload-img-bt"));

function formatDocument(document) {
    let text = ""
    for (let element of result) {
      if (element.type === "choice_ques") {
          text += `${element["num"]}. ${element["text"]}`;
          for (let option of element["options"]) {
            text += `-- ${option["choice"]}. ${option["text"]}`;
          }
      }
    }
}

$("#scan-imgs-bt").on("click", () => {
    apiFetch("/api/scan_imgs").then((res) => {
        let text = ""
        for (let doc in res) {
          text += formatDocument(doc);
        }

        $("output-text").val(text);
        $("output-card").show();
    });
});