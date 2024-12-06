# from transformers import AutoTokenizer, AutoModel
# from langchain_community.vectorstores import FAISS
# import torch
# import numpy as np

# # Load tokenizer và model từ Hugging Face
# tokenizer = AutoTokenizer.from_pretrained('keepitreal/vietnamese-sbert')
# model = AutoModel.from_pretrained('keepitreal/vietnamese-sbert')

# # Đọc file văn bản
# with open('actions/doc.txt', 'r', encoding='utf-8') as file:
#     documents = file.readlines()

# # Loại bỏ các ký tự thừa
# documents = [doc.strip() for doc in documents]

# # Hàm tạo embeddings
# def create_embeddings(documents, tokenizer, model):
#     embeddings = []
#     for doc in documents:
#         # Tokenize văn bản
#         inputs = tokenizer(doc, padding=True, truncation=True, return_tensors="pt", max_length=512)
        
#         # Disable gradient computation để tăng tốc
#         with torch.no_grad():
#             # Pass tokens qua model và lấy hidden states
#             outputs = model(**inputs)
#             # Mean pooling để tạo embedding
#             embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
#             embeddings.append(embedding)
#     return embeddings

# # Tạo embeddings
# embeddings = create_embeddings(documents, tokenizer, model)

# # Chuyển embeddings thành numpy array
# embeddings = np.array(embeddings)

# # Tạo FAISS index bằng phương thức from_texts
# db = FAISS.from_texts(texts=documents, embedding=embeddings)

# # Lưu FAISS VectorStore
# db.save_local("faiss_vector_store")

# print("FAISS VectorStore đã được lưu thành công!")
