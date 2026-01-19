import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()
notion = Client(auth=os.getenv("NOTION_TOKEN"))
DATABASE_ID = os.getenv("DATABASE_ID")

def test_notion():
    print("Testing Notion Connection...")
    try:
        # Try to retrieve the database metadata
        db = notion.databases.retrieve(database_id=DATABASE_ID)
        print(f"✅ Connection Successful! Database Name: {db['title'][0]['plain_text']}")
        
        # Try a simple query
        print("Testing Query...")
        response = notion.databases.query(database_id=DATABASE_ID, page_size=1)
        print("✅ Query Successful!")
        
    except Exception as e:
        print(f"❌ Notion Connection Error: {e}")

if __name__ == "__main__":
    test_notion()