$ = mdui.$;

const USER_ID = localStorage.getItem("user-id") ||
        Math.random().toString(36).slice(-10) +
        new Date().getTime().toString(32).slice(-4);
localStorage.setItem("user-id", USER_ID);

marked.setOptions({
  breaks: true
});

class apiFetch {
  constructor(path, args={}) {
      this.path = path;
      const defaultArgs = {
          method: 'GET',
          headers: { 'User-Id': USER_ID }
      }
      this.args = { ...defaultArgs, ...args };
  }
  
  async send() {
      this.res = await fetch(this.path, this.args);
      
      if (!this.res.ok) {
        mdui.snackbar("Server Error " + this.res.message);
      }
      try {
        const json = await this.res.json();
        if (json.code === 0 && json.data) {
          return json.data
        } else {
          return []
        }
      } catch {
        return []
      }
  }
}

/*
percent >= 1 hide all
percent 0~1 determinate
percent none indeterminate
*/
function updateProgress(percent) {
  let progress_bar = $("#users-imgs-progress");
  progress_bar.show();
  if (percent) {
    if (percent >= 1) progress_bar.hide();
    progress_bar = progress_bar.find('.mdui-progress-determinate');
  } else {
    progress_bar = progress_bar.find('.mdui-progress-indeterminate');
    progress_bar.show();
  }
  progress_bar.css('width', `${percent*100}%`);
  return progress_bar
}


class ImgsList {
  constructor() {
    this.list_ele = $("#user-imgs-row");
    this.imgs = [];
  }
  
  async refresh() {
    this.imgs = await new apiFetch("/api/imgs/list").send();
    // 移除所有非 template 的图片，以便刷新
    this.list_ele.children(':not([template])').remove();
    let imgs_loaded = 0;
    let imgs_scanned = 0;
    const imgs_fragment = [];
    this.imgs.forEach((img, index) => {
      const img_frame = this.imgEle(img, index);
      
      img_frame.find('img').on("load", () => {
          imgs_loaded ++;
          updateProgress(imgs_loaded / this.imgs.length);
      });
      
      if (img.document_status === 'scanned') imgs_scanned ++;
      
      imgs_fragment.push(img_frame);
    });
    this.list_ele.append(...imgs_fragment);
    
    // 没图片可加载就隐藏进度条（正常需要图片加载完成才能隐藏进度条）
    if (this.imgs.length === 0) {
      updateProgress(1);
    } else if (imgs_scanned >= this.imgs.length) {
      // 全部扫描过就启用 生成答案 按钮
      $("#output-imgs-bt").removeAttr("disabled");
    } else if (this.imgs.findIndex((img) => img.document_status === "unscanned") >= 0) {
      // 有任意一张图片未扫描就允许再次扫描
      $("#scan-imgs-bt").removeAttr('disabled');
    }
  }
  
  imgEle(img, index) {
    const img_frame = this.list_ele.children("[template]").clone().removeAttr("template");

    img_frame.find(".mdui-grid-tile-title").text(index + 1);
    img_frame.find('img').attr("src", img.url);
    
    const icon = $("<i>").addClass("mdui-icon material-icons");
    const status_fragment = [];
    if (img.document_status === "scanned") {
      icon.text("check");
      status_fragment.push(icon, "已识别");
    } else if (img.document_status === "unscanned") {
      icon.text("info_outline");
      status_fragment.push(icon, "未识别");
    } else if (img.document_status === "scanning") {
      icon.text("wifi_tethering");
      status_fragment.push(icon, "识别中");
    }
    img_frame.find(".mdui-grid-tile-subtitle").append(...status_fragment);
    
    img_frame.find("button").on("click", (e) => {
      const delete_bt = $(e.target);
      mdui.snackbar({
        message: "确定删除？",
        buttonText: "确定",
        onButtonClick: () => {
            delete_bt.attr("disabled");
            new apiFetch(`/api/imgs/delete/${index}`).send().then(() => {
              delete_bt.closest("div.mdui-col").remove();
              imgs_list.refresh();
            });
        }
      });
    });
    
    return img_frame;
  }
}

const imgs_list = new ImgsList();
/* 初始化 imgs_list，同时激活上传图片功能 */
imgs_list.refresh().then(() => {
  const upload_input = $("#upload-img-input");
  upload_input.on("change", (e) => {
      const data = new FormData();
      for (let file of e.target.files) {
        data.append('file', file);
      }
      new apiFetch("/api/imgs/upload", {
          method: 'POST',
          body: data
      }).send().then((res) => {
          upload_bt.removeAttr('disabled');
          imgs_list.refresh();
      });
  });
  
  const upload_bt = $("#upload-img-bt");
  upload_bt.on("click", (e) => {
    upload_bt.attr('disabled');
    // 当点击上传图片按钮时触发被隐藏的 input
    upload_input.trigger('click');
  });
  upload_bt.removeAttr('disabled');
});

// 开始识别功能
$("#scan-imgs-bt").on("click", (e) => {
    $(e.target).attr('disabled');
    const img_cols = $("#user-imgs-row > .mdui-col");
    const req = new apiFetch("/api/imgs/scan");
    fetch(req.path, req.args).then((res) => {
      updateProgress(0);
      mdui.snackbar("已提交请求，可关闭浏览器");
      
      const reader = res.body.getReader();
      const imgs_scanned = [];
      reader.read().then(function updateScanProgress({ done, value }) {
        if (done) {
          mdui.snackbar("全部扫描完成");
        }
        const img = JSON.parse(new TextDecoder().decode(value));
        imgs_scanned.push(img);
        
        // 替换为扫描后的新图片
        const img_frame = imgs_list.imgEle(img, imgs_scanned.length)
        img_cols[imgs_scanned.length].replaceWith(img_frame);
        updateProgress(imgs_scanned.length / imgs_list.imgs.length);
        // 下一轮读取
        return reader.read().then(updateScanProgress);
      });
    });
});

// 生成答案功能
$("#output-imgs-bt").on("click", (e) => {
    $(e.target).attr("disabled");
    new apiFetch("/api/generator/generate_prompt", {
        "method": "POST"
    }).send().then((res) => {
        $(e.target).removeAttr("disabled");
        if (res.prompt) {
          // const prompt_box = $("#generator-prompt-box");
          // prompt_box.find(".mdui-textfield-input").val(res.prompt);
          // prompt_box.find("button").trigger("click");
          
          messages_list.sendApi({'content': res.prompt, 'tag': 'ques'});
        }
    });
});


class MessagesList {
  constructor() {
    this.list_ele = $("#generator-messages-list");
    this.messages = [];
    this.divider = null;
  }
  
  #getDivider() {
    this.divider = this.divider || $('<div>').addClass('mdui-divider-inset mdui-m-y-0');
  }
  
  async refresh() {
    this.messages = await new apiFetch('/api/generator/messages').send();
    
  let messages_fragment = [];
    this.messages.forEach((message) => {
      const message_fragment = this.msgEle(message);
      messages_fragment = [...messages_fragment, ...message_fragment];
    });
    this.list_ele.children(':not([template])').remove();
    this.list_ele.append(...messages_fragment);
  }
  
  msgEle(message) {
    const message_fragment = [];

    let message_frame = this.list_ele.children('[template="generator-message"]').clone().removeAttr('template');
    if (message.role === 'user') {
      message_frame = this.list_ele.children('[template="user-message"]').clone().removeAttr('template');
    }
    
    let html = "";
    if (message.tag === 'ques') {
      html = '<i class="mdui-icon material-icons">info</i>识别的题目';
    } else if (message.content) {
      html = marked.parse(message.content);
    }
    message_frame.find('.mdui-list-item-text').html(html);

    if (this.divider) {
      message_fragment.push(this.divider.clone());
    }
    message_fragment.push(message_frame);

    this.#getDivider();
    return message_fragment;
  }
  
  sendApi(message, callback) {
    message.role = "user";
    
    const req = new apiFetch(`/api/generator/send${message.tag ? '?tag=' + message.tag : ''}`, {
      method: 'POST',
      body: message.content
    });
    fetch(req.path, req.args).then(async (res) => {
      // 先创建一个空元素，再往里面添字
      const message_fragment = this.msgEle({});
      const list_ele = this.list_ele.append(...message_fragment);
      // 获取最后一个添加的文本元素
      const text_ele = list_ele.find('.mdui-list-item-text').last();
      const reader = res.body.getReader();

      // 读取流，动态添加响应
      reader.read().then(function appendAnswer({ done, value }) {
        if (done) {
          //text_ele.html(marked.parse(text_ele.text()));
          return;
        }
        text_ele.append(new TextDecoder().decode(value));
  
        return reader.read().then(appendAnswer);
      });
      callback();
      this.#getDivider();
    });
  }
}

const messages_list = new MessagesList();
messages_list.refresh().then(() => {
  const clear_bt = $('#generator-clear-bt');
  clear_bt.on('click', (e) => {
    clear_bt.attr('disabled', true);
    new apiFetch("/api/generator/clear").send().then(() => {
      messages_list.list_ele.children(':not([template])').remove();
      messages_list.divider = null;
      clear_bt.removeAttr('disabled');
    });
  });
  
  const prompt_box = $("#generator-prompt-box")
  const send_bt = prompt_box.children('button');
  const prompt_text = prompt_box.find('.mdui-textfield-input');
  send_bt.on('click', () => {
    send_bt.attr('disabled');
    const message = {'role': 'user', 'content': prompt_text.val()};
    const message_fragment = messages_list.msgEle(message);
    messages_list.list_ele.append(...message_fragment);
    prompt_text.val('');
    messages_list.sendApi(message, () => {
      send_bt.removeAttr('disabled');
    });
  });
});
