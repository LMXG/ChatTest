# -*- coding: utf-8 -*-
# Date       ：2023/8/4
# Author     ：Mahy
# Description：text2vec与whisper接口化

from fastapi import FastAPI, File, UploadFile
from langchain.embeddings import HuggingFaceEmbeddings
import warnings
import os
from pywhispercpp.model import Model

warnings.filterwarnings("ignore")

app = FastAPI()

model_name = "C:/Users/haoyangma/.cache/torch/sentence_transformers/text2vec-base-chinese"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': True}

def text2cev(text):
    hf = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

    embeddings = hf.embed_query(text)

    return embeddings

def speech2text(speech):

    model = Model(model='medium', n_threads=6, language='zh')
    segments = model.transcribe(speech, speed_up=True)
    text = segments[0]

    return text

@app.post("/text-to-embed")
def text_to_embed(text: str):
    embedding = text2cev(text)
    return {"embedding": embedding}


@app.post("/audio-to-text")
async def audio_to_text(file: UploadFile = File(...)):
    fn = file.filename
    save_path = f'C:/Users/haoyangma/Desktop/practice/fastapi/'
    if not os.path.exists(save_path):
        os.mkdir(save_path)

    save_file = os.path.join(save_path, fn)

    f = open(save_file, 'wb')
    data = await file.read()
    f.write(data)
    f.close()

    text = speech2text(save_file)

    return {"text": text}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app="main:app", host="127.0.0.1", port=8888, reload=True)