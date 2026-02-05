#from helper_utils import word_wrap # helper functions from utilities
from langchain.text_splitter import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter
from dotenv import dotenv_values
import chromadb
import openai
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


env_vars = dotenv_values('.env')
openai.api_key = env_vars.get('OPENAI_API_KEY')
openai_client = openai.OpenAI(api_key=openai.api_key)

def text_splitter_chunks(pdf_texts):
    character_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ". ", " ", ""],
        chunk_size=1000,
        chunk_overlap=0
    )
    character_split_texts = character_splitter.split_text('\n\n'.join(pdf_texts))
    # print(character_split_texts[10])
    # print(f"\nTotal chunks: {len(character_split_texts)}")
    return character_split_texts

def sentence_transfomer_textsplitter(character_split_texts):
    token_splitter = SentenceTransformersTokenTextSplitter(chunk_overlap=0, tokens_per_chunk=256)
    token_split_texts = []
    for text in character_split_texts:
        token_split_texts += token_splitter.split_text(text)
    # print(token_split_texts[10])
    # print(f"\nTotal chunks: {len(token_split_texts)}")
    return token_split_texts


def embedding():
    embedding_function = SentenceTransformerEmbeddingFunction()
    # print(embedding_function([token_split_texts[10]]))
    return embedding_function

def connect_with_chromadb(embedding_function, token_split_texts):
    chroma_client = chromadb.Client()
    chroma_collection = chroma_client.create_collection("m21", embedding_function=embedding_function)

    ids = [str(i) for i in range(len(token_split_texts))]

    chroma_collection.add(ids=ids, documents=token_split_texts)
    chroma_collection.count()
    return chroma_collection

def vectordb_answer_question(query, chroma_collection):
    # query = "What was the total revenue?"
    results = chroma_collection.query(query_texts=[query], n_results=5)
    retrieved_documents = results['documents'][0]

    # for document in retrieved_documents:
    #     print(document)
    #     print('\n')
    return retrieved_documents

def openai_model_answer(query, retrieved_documents, model="gpt-3.5-turbo"):
    information = "\n\n".join(retrieved_documents)

    messages = [
        {
            "role": "system",
            "content": "You are happy assistant. Use the context provided below to answer the question. Answer question in summarization "
        },
        {"role": "user", "content": f"Question: {query}. \n Information: {information}"}
    ]
    
    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
    )
    content = response.choices[0].message.content
    return content

