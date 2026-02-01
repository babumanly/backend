import os
import google.generativeai as genai
from dotenv import load_dotenv  # <-- ADD THIS IMPORT

# --- Load environment variables from .env file ---
load_dotenv() # <-- ADD THIS LINE TO LOAD THE .ENV FILE

# --- Configure Gemini API ---
# This now securely loads your key from the .env file
try:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        llm_model = genai.GenerativeModel("gemini-2.5-flash")
    else:
        llm_model = None
        print("GEMINI_API_KEY environment variable not found.")
except Exception as e:
    llm_model = None
    print(f"Gemini API could not be configured. Error: {e}")


# --- Helper Functions ---
def get_treatment_plan(disease_name: str, severity: float, language: str) -> str:
    """Uses Gemini API to generate a treatment plan."""
    if not llm_model:
        return f"Gemini API not configured. Placeholder plan for {disease_name} in {language}."

    prompt = (
        f"You are an expert agricultural advisor for farmers in Andhra Pradesh, India. "
        f"Provide a detailed and practical medication and treatment plan for the plant disease '{disease_name}' with a severity of {severity:.1f}%, written in the {language} language. "
        f"The plan must be tailored specifically to Indian standards and be easy for a farmer to understand.\n\n"
        f"Crucially, you must follow these rules:\n"
        f"1. **Format the entire response using simple Markdown.** Use `##` for main headings and `*` for bullet points. Do not use complex Markdown.\n"
        f"2. **Do not create tables using characters like '|' and '-'.** Instead, list product details using bullet points under a heading.\n"
        f"3. All suggested chemical pesticides or commercial products must be brands **commonly available in India**.\n"
        f"4. Provide an estimated cost for these products in **Indian Rupees (INR, ₹)**.\n"
        f"5. Include detailed sections for organic/home remedies and preventive measures suitable for local conditions.\n"
        f"6. The outcome must not contain any comments.\n"
        # --- ADD THIS NEW RULE ---
        f"7. **Finally, create a simple '7-Day Action Plan' or checklist based on the severity.** For example: Day 1: Apply [Pesticide A]. Day 3: Monitor leaves. Day 5: Apply [Organic Remedy B]."
    )
    try:
        response = llm_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating plan for {disease_name} in {language}. Error: {e}"