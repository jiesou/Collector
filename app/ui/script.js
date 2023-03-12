$ = mdui.$;

const USER_ID = localStorage.getItem("user-id") ||
        Math.random().toString(36).slice(-10) +
        new Date().getTime().toString(32).slice(-4);
localStorage.setItem("user-id", USER_ID);


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

function updateProgress(percent) {
  let progress_bar = $("#users-imgs-progress");
  progress_bar.show();
  if (percent) {
    progress_bar = progress_bar.find('.mdui-progress-determinate');
  } else {
    progress_bar = progress_bar.find('.mdui-progress-indeterminate');
    progress_bar.show();
  }
  progress_bar.css('width', `${percent*100}%`);
  return progress_bar
}

async function pollProgress(progress_bar) {
  imgs_list = await new apiFetch("/api/get_imgs_list").send();
  const finishedImgs = list.filter(img => img.document_status === "scanned");
  const finishedPercent = finishedImgs.length/list.length;
  if (finishedPercent >= 1) {
    progress_bar.hide();
    clearInterval(pollProgress);
  }
  updateProgress(finishedPercent);
  // 十秒一次轮询
  setTimeout(pollProgress, 10000);
}
async function refreshImgsRow(imgs_list) {
  if (!imgs_list) {
    var imgs_list = await new apiFetch("/api/get_imgs_list").send();
  }
  
  const imgs_row = $("#user-imgs-row");
  const scan_bt = $("#scan-imgs-bt");
  scan_bt.on("click", () => {
      // 先禁用按钮，防止同时提交多个请求
      scan_bt.attr('disabled');
      new apiFetch("/api/scan_imgs").send().then((res) => {
          const progress_bar = $("#users-imgs-progress")
            .find(".mdui-progress-determinate");
          progress_bar.css('width', 0);
          progress_bar.show();
          mdui.snackbar("已提交请求");
          
          pollProgress(progress_bar);
      });
  });

  // 移除所有非 template 的图片
  imgs_row.children(':not([template])').remove();
  let imgs_loaded = 0;
  imgs_list.forEach((img) => {
    const img_frame = imgs_row.children("[template]").clone().removeAttr("template");
    const img_ele = img_frame.find('img');
    img_ele.attr("src", img.url);
    img_ele.on('load', () => {
        imgs_loaded ++;
        if (imgs_loaded >= imgs_list.length) updateProgress().parent().hide();
    });
    imgs_row.append(img_frame);

    // 有未扫描的图片就显示提交扫描按钮
    if (img.document_status === 'unscanned') {
      scan_bt.removeAttr('disabled');
    }
  });
  // 没图片可加载也隐藏进度条
  if (imgs_list.length === 0) updateProgress().parent().hide();
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
      new apiFetch("/api/upload_imgs", {
          method: 'POST',
          body: data
      }).send().then((res) => {
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

const messages_list = $("#generator-messages-list")
async function refreshMessages(last_message) {
    const messages_fragment = [];
    const divider = $('<div>').addClass('mdui-divider-inset mdui-m-y-0');
    let messages;
    if (last_message) {
      messages = [last_message];
    } else {
      messages = await new apiFetch('/api/generator/messages').send();
      messages_list.children(':not([template])').remove();
    }
    
    let message_ele
    messages.forEach((message) => {
      message_ele = messages_list.children('[template="generator-message"]').clone().removeAttr('template');
      if (message.role === 'user') {
        message_ele = messages_list.children('[template="user-message"]').clone().removeAttr('template');
      }
      
      const text = message.content.replace('\n', '<br>');
      message_ele.find('.mdui-list-item-text').html(text);
      messages_fragment.push(divider.clone(), message_ele);
    });
    messages_list.append(...messages_fragment);
    return message_ele
}

((clear_bt, prompt_box) => {
  refreshMessages().then(() => {
    // 首次加载消息列表，删除第一条多余的 间隔线
    messages_list.children('div')[0].remove();
  });
  
  clear_bt.on('click', () => {
    clear_bt.attr('disabled', true);
    new apiFetch("/api/generator/clear").send().then(() => {
      refreshMessages().then(() => clear_bt.removeAttr('disabled'));
    });
  });
  
  const send_bt = prompt_box.children('button');
  const prompt_text = prompt_box.find('.mdui-textfield-input');
  send_bt.on('click', () => {
    send_bt.attr('disabled', true);
    const req = new apiFetch("/api/generator/send", {
      method: 'POST',
      body: prompt_text.val()
    });
    fetch(req.path, req.args).then(async (res) => {
      const reader = res.body.getReader();
      const message_ele = await refreshMessages({'role': 'assistant', 'content': ''});
      text_ele = message_ele.find('.mdui-list-item-text');

      reader.read().then(function appendAnswer({ done, value }) {
        if (done) {
          prompt_text.val('');
          send_bt.removeAttr('disabled');
          return;
        }
        text_ele.append(new TextDecoder().decode(value));

        return reader.read().then(appendAnswer);
      });
    });
    refreshMessages({'role': 'user', 'content': prompt_text.val()});
  }); 
})($('#generator-clear-bt'), $("#generator-prompt-box"));