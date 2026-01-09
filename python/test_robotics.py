
import base64
import os
from google import genai
from google.genai import types


def generate():
    api_key = os.environ.get("GEMINI_KEY")
    # The warning check for GEMINI_KEY is removed as per instruction.

    try:
        client = genai.Client(
            api_key=api_key,
        )

        model = "gemini-robotics-er-1.5-preview"
        print(f"Testing model with image: {model}")
        
        # Read image-1.png
        image_path = os.path.join(os.path.dirname(__file__), 'image-1.png')
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="Describe this image."),
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                ],
            ),
        ]
     
        print("Sending request...")
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
     
        ):
            print(chunk.text, end="")
        print("\nDone.")
            
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    generate()
