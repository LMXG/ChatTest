# -*- coding: utf-8 -*-
# Date       ：2023/7/27
# Author     ：Mahy
# Description：
"""
流程：
上传文件
1、读取文件为字符串列表
2、生成摘要
3、拼接成上下文问答对 {原文段：原文段上下1行}
4、送入FAISS建立索引（是否使用BertModel进行embedding？）

提问
1、查找与问题最相似的上下文，返回背景段落
2、将相似段落与历史段落拼接成text(Q,A)形式送入ChatGLM-6B，返回答案
"""
import yaml
import time
import json
import gradio as gr
import asyncio
import requests
from pathlib import Path
from sentence_transformers import SentenceTransformer as SBert
from query2glm import ChatGLM
from processFile.fileProcess import ProcessBook



# create a static directory to store the static files
static_dir = Path('C:/Users/haoyangma/Desktop/practice/ChatTest/static')
static_dir.mkdir(parents=True, exist_ok=True)

with open("config.yaml") as f:
    config = yaml.safe_load(f)

encode_model = SBert(config['encode_model_path'])
glm_chater = ChatGLM(chat_url=config['chatglm6b_url'], faiss_path=config['faiss_path'], encode_model=encode_model)
global c_range_id
history_id_dic = {}  # {id: history_list}
c_range_id_dic = {}  # {文件名：md5_id}


# TODO 设计无文件上传的情况
# 聊天窗口显示用户输入
def user(query, history, doc_list):  # 输入输出为msg_btn的inputs和outputs
    global c_range_id
    global c_range_id_dic
    # 获取c_range_id
    if doc_list != "":
        c_range_id = c_range_id_dic[doc_list]
        history += [[query, None]]
    return "", history

def get_pdf(pdf_path, target_url):
    data = {"pdf_filename": pdf_path}
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    headers = {'Content-Type': 'application/json'}
    response = requests.request("post", target_url, headers=headers, data=payload)
    result = json.loads(response.text)["out_html"]
    return result

# 聊天窗口显示机器返回
def bot(history):  # 输入输出均传给chatbot控件
    global c_range_id
    global file_dropdown
    global history_id_dic
    query = history[-1][0]
    if query[-1] not in [",", ".", "?", "!", "，", "。", "？", "！"]:
        query1 = query + "？"
    else:
        query1 = query
    if c_range_id == "":
        response = "请导入文件"
    else:
        response = asyncio.run(glm_chater.generate(c_range_id, query1, history=history_id_dic[c_range_id]))
    history_id_dic[c_range_id].append([query1, response])
    # 打字机效果
    history[-1][1] = ""
    for character in response:
        history[-1][1] += character
        time.sleep(0.02)
        yield history


# 上传文件
def add_file(file, doc_list):
    global c_range_id
    global c_range_id_dic
    global history_id_dic
    preprocess = ProcessBook(encode_model, **config['header_and_footer'])
    c_range_id = preprocess.upload(config['faiss_path'], file.name)
    doc_name = file.name.split("/")[-1]
    c_range_id_dic[doc_name] = c_range_id
    doc_list = list(c_range_id_dic.keys())
    pdf_html = get_pdf(file.name, config['pdf_url'])
    if c_range_id not in history_id_dic:  # 初次上传，初始化文件history
        history_id_dic[c_range_id] = []
    return gr.Dropdown.update(choices=doc_list, value=doc_name), gr.HTML.update(value=pdf_html)


# 页面启动执行的内容
def load(doc_list):
    global c_range_id
    global c_range_id_dic
    global history_id_dic
    doc_list = list(c_range_id_dic.keys())
    default_pdf = get_pdf(config['default_pdf'], config['pdf_url'])
    for key in c_range_id_dic.keys():
        # 尝试找到value
        if c_range_id_dic[key] == c_range_id:
            doc_name = key
            return gr.Dropdown.update(choices=doc_list, value=doc_name), gr.HTML.update(value=default_pdf)
    # 不存在合适的value则用户选择
    return gr.Dropdown.update(choices=doc_list), gr.HTML.update(value=default_pdf)


with gr.Blocks() as demo:

    with gr.Row(variant='panel'):
        with gr.Column(scale=3):
            file_dropdown = gr.Dropdown(
                choices=list(c_range_id_dic.keys()),
                show_label=False,
                interactive=True
            ).style(container=False)
        with gr.Column(scale=0.35):
            upload_button = gr.UploadButton("上传文档 📁", file_types=["file"])

    with gr.Row().style(equal_height=True):
        # 显示文档
        with gr.Column(variant='panel'):
            file_display = gr.HTML()

        with gr.Column(variant='panel'):
            with gr.Tabs():
                # 大模型问答模块
                with gr.TabItem("大模型问答模块"):
                    # 标题
                    gr.Markdown("<div align='center'> <h3> 文档内容问答 </span> </h3> </div>")
                    # 聊天框
                    chatbot = gr.Chatbot([], label="聊天框", elem_id="chatbot").style(height=850)
                    # 问题发送窗口
                    with gr.Row():
                        with gr.Column(scale=0.85):
                            msg_box = gr.Textbox(show_label=False, placeholder="请输入问题：").style(container=False)
                        with gr.Column(scale=0.15):
                            msg_button = gr.Button("发送问题", variant='primary')


    msg_button.click(fn=user, inputs=[msg_box, chatbot, file_dropdown], outputs=[msg_box, chatbot], queue=False
                     ).then(fn=bot, inputs=chatbot, outputs=chatbot)
    upload_button.upload(fn=add_file, inputs=[upload_button, file_dropdown], outputs=[file_dropdown, file_display])
    demo.load(load, inputs=file_dropdown, outputs=[file_dropdown, file_display])

if __name__ == "__main__":
    # app = gr.mount_gradio_app(app, demo, path="/")
    # uvicorn.run(app, host="0.0.0.0", port=9031)
    demo.queue().launch(server_name="127.0.0.1", server_port=9032, share=True)
