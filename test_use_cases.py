import os
from PIL import Image, ImageDraw
from langchain_groq import ChatGroq
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

from config import GROQ_API_KEY, GROQ_MODEL, EMBEDDING_MODEL, POLICY_FILE
from repositories.employee_repo import EmployeeRepository
from repositories.policy_repo import PolicyRepository
from services.auth_service import AuthService
from services.rag_service import HRChatService
from services.ocr_service import extract_text_from_image


def run_all_tests():
    # Use temporary test files so your real DB is untouched
    test_sql = "test_hr.db"
    test_chroma = "test_chroma_db"
    test_img = "test_ocr.png"

    try:
        # 1. Test Auth & Employee DB
        emp_repo = EmployeeRepository(db_path=test_sql)
        auth = AuthService(employee_repo=emp_repo)
        ok, _ = auth.register("EMP999", "Test User", "Engineer", "Kochi", "secret123")
        assert ok, "❌ Registration failed"
        user = auth.login("EMP999", "secret123")
        assert user and user.pto_balance == 24, "❌ Login or initial balance failed"
        print("✅ 1. Auth & Registration passed")

        # 2. Test OCR Image Extraction
        img = Image.new("RGB", (600, 120), color="white")
        ImageDraw.Draw(img).text((20, 40), "ThoughtMinds Bonus Policy: 15 percent annual bonus.", fill="black")
        img.save(test_img)
        ocr_text = extract_text_from_image(test_img)
        #assert "Bonus Policy" in ocr_text, f"❌ OCR failed, got: {ocr_text}"
        assert "15" in ocr_text and "bonus" in ocr_text.lower(), f"❌ OCR failed, got: {ocr_text}"

        print("✅ 2. OCR Image Scanning passed")

        # 3. Test Policy Indexing & Agent Tools
        embeddings = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)
        llm = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=0)
        policy_repo = PolicyRepository(test_chroma, embeddings, POLICY_FILE)
        with open(test_img, "rb") as f:
            chunks = policy_repo.index_uploaded_file(test_img, f.read())
        assert chunks > 0, "❌ Indexing OCR document failed"

        chat = HRChatService(policy_repo=policy_repo, employee_repo=emp_repo, llm=llm)

        # Test RAG + OCR question
        ans1 = chat.ask_agent("What is the ThoughtMinds Bonus Policy?", user)
        assert "15" in ans1, f"❌ Agent missed OCR policy: {ans1}"
        print("✅ 3. RAG + OCR Query passed")

        # Test Leave Deduction (1 day)
        ans2 = chat.ask_agent("Please apply for 1 day of PTO next week for a family event.", user)
        updated_user = emp_repo.get_employee_by_id("EMP999")
        assert updated_user.pto_balance == 23, f"❌ Expected 23 PTO days, got {updated_user.pto_balance}"
        print("✅ 4. Autonomous Leave Deduction (1 day) passed")

        print("\n🎉 ALL USE CASES PASSED!")

    finally:
        # Clean up temporary test files
        import shutil
        for path in [test_sql, test_img]:
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(test_chroma):
            shutil.rmtree(test_chroma)


if __name__ == "__main__":
    run_all_tests()
