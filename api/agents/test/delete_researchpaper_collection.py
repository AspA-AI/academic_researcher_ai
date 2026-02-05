from api.utils.weaviate_client import get_weaviate_manager

if __name__ == "__main__":
    weaviate_manager = get_weaviate_manager()
    if weaviate_manager.is_available():
        print("[INFO] Attempting to delete 'ResearchPaper' collection...")
        result = weaviate_manager.delete_collection("ResearchPaper")
        if result:
            print("[SUCCESS] 'ResearchPaper' collection deleted.")
        else:
            print("[ERROR] Failed to delete 'ResearchPaper' collection or it does not exist.")
    else:
        print("[ERROR] Weaviate is not available.") 