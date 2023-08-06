# -*- coding: utf-8 -*-
# Date       ：2023/7/22
# Author     ：Mahy
# Description：ChatGLM测试，这东西怎么这么难用？

from transformers import AutoTokenizer, AutoModel
tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm-6b-int4", trust_remote_code=True)
model = AutoModel.from_pretrained("THUDM/chatglm-6b-int4", trust_remote_code=True,).float()
model = model.eval()
response, history = model.chat(tokenizer, "你是一个AI助手，严格遵照我所提供的知识回答问题，并给出简洁的答复。依据来自文本第1页段落：第九条申请机动车登记，应当提交以下证明、凭证：(一)机动车所有人的身份证明;(二)机动车来历证明;(三)机动车整车出厂合格证明或者进口机动车进口凭证;(四)车辆购置税的完税证明或者免税凭证;(五)法律、行政法规规定应当在机动车登记时提交的其他证明、凭证。应当提交什么证明？，回答的最后给出参考依据。", history=[])
print(response)