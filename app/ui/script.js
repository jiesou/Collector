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
    var img_list = await apiFetch("/api/get_imgs_list") || [];
  }
  
  const imgs_row = $("#user-imgs-row");
  const scan_bt = $("#scan-imgs-bt");
  scan_bt.on("click", () => {
      // 先禁用按钮，防止同时提交多个请求
      scan_bt.attr('disabled');
      apiFetch("/api/scan_imgs").then((res) => {
          mdui.snackbar("已提交请求");
      });
  });

  // 移除所有非 template 的图片
  imgs_row.children(':not([class$="-template"])').remove();
  let imgs_loaded = 0;
  img_list.forEach((img) => {
    const img_frame = imgs_row.children(".user-img-template").clone().removeClass("user-img-template");
    const img_ele = img_frame.find('img');
    img_ele.attr("src", img.url);
    img_ele.on('load', () => {
        imgs_loaded ++;
        // 所有图片加载完后隐藏加载条
        if (imgs_loaded >= img_list.length) $("#users-imgs-progress").hide();
    });
    imgs_row.append(img_frame);
    
    // 有未扫描的图片就显示提交扫描按钮
    if (img.document_status === 'unscanned') {
      scan_bt.removeAttr('disabled');
    }
  });
}

((upload_input, upload_bt) => {
  // 图片表格加载出来后再允许上传图片
  refreshImgsRow().then(()=>upload_bt.removeAttr('disabled'));

  // 当点击上传图片按钮时触发被隐藏的 input
  
upload_bt.on("click", () => upload_input.trigger('click'));
  upload_input.on("change", (e) => {
      // 先禁用按钮，防止同时上传多条
      upload_bt.attr('disabled', true)
      const data = new FormData();
      for (let file of e.target.files) {
        data.append('file', file);
      }
      apiFetch("/api/upload_imgs", {
          method: 'POST',
          body: data
      }).then((res) => {
          refreshImgsRow(res).then(()=>upload_bt.removeAttr('disabled'));
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

