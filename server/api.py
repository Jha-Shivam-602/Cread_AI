import os
import io
import uuid
import boto3
import datetime
from PIL import Image
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from urllib.parse import urlparse
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

app = Flask(__name__)

# =========================================================
# MODEL
# =========================================================

MODEL_ID = "gemini-3-pro-image-preview"

# =========================================================
# ANIME STYLES
# =========================================================

ANIME_STYLES = {
    "nekomimi_anime": {
        "name": "Nekomimi (Kemonomimi)",
        "positive": "A nekomimi anime character, human-animal hybrid with soft cat ears and a fluffy tail, large expressive anime eyes with gentle highlights, soft layered hair with natural shine, cute and playful expression with a hint of mischief, slim anime body proportions, fantasy-inspired outfit with soft fabrics and flowing details, warm pastel color palette, clean anime line art, soft shading, kemonomimi anime style, best quality, masterpiece, anime illustration, high resolution, ultra-detailed",
        "negative": "realistic human, photorealistic, animal face instead of human, extra ears, extra tails, deformed anatomy, bad proportions, harsh shadows, dull colors, messy line art, extra limbs, extra fingers, missing fingers, malformed hands, bad anatomy, distorted face, cross-eye, blurry, jpeg artifacts, watermark, text, logo"
    },
    "shonen_anime": {
        "name": "Shonen",
        "positive": "A shonen anime protagonist with sharp facial features and intense determined eyes, spiky dynamic hairstyle, athletic muscular build, strong heroic posture, battle-ready stance, dramatic lighting with high contrast, bold anime line art, dynamic composition, vivid colors and action-focused atmosphere, classic shonen anime style, best quality, masterpiece, anime illustration, high resolution, ultra-detailed",
        "negative": "cute chibi style, soft pastel colors, weak expression, thin fragile body, photorealism, flat lighting, static pose, low detail, extra limbs, extra fingers, missing fingers, malformed hands, bad anatomy, distorted face, cross-eye, blurry, jpeg artifacts, watermark, text, logo"
    },
    "kawaii_anime": {
        "name": "Kawaii",
        "positive": "A kawaii anime character with chibi proportions, very large sparkling eyes and rounded facial features, small nose and tiny mouth, soft pastel color palette, cute outfit with playful accessories, innocent cheerful expression, simple clean line art, soft shading, kawaii anime style, best quality, masterpiece, anime illustration, high resolution, ultra-detailed",
        "negative": "realistic proportions, muscular body, sharp facial features, dark gritty tones, photorealism, horror style, angry expression, harsh shadows, complex textures, extra limbs, extra fingers, missing fingers, malformed hands, bad anatomy, distorted face, cross-eye, blurry, jpeg artifacts, watermark, text, logo"
    },
    "mushoku_tensei_anime": {
        "name": "Mushoku Tensei",
        "positive": "A fantasy anime character in Mushoku Tensei style, large expressive eyes with detailed irises, soft realistic facial proportions, natural skin tones and subtle shading, highly detailed voluminous hair with defined strands, medieval fantasy outfit with fine details, cinematic lighting and depth, immersive anime illustration, best quality, masterpiece, anime illustration, high resolution, ultra-detailed",
        "negative": "cartoonish style, chibi proportions, flat shading, simple line art, neon colors, photorealistic skin, plastic texture, low detail, extra limbs, extra fingers, missing fingers, malformed hands, bad anatomy, distorted face, cross-eye, blurry, jpeg artifacts, watermark, text, logo"
    },
    "ghibli_japanese_anime": {
        "name": "Japanese Anime (Ghibli Inspired)",
        "positive": "Studio Ghibli style illustration, whimsical atmosphere, lush detailed backgrounds, soft painterly textures, gentle pastel color palette, warm natural lighting, expressive characters with large kind eyes, cinematic composition, smooth shading, hand-painted look, magical and cozy environment, inspired by Hayao Miyazaki, ultra high detail from image, 8k resolution, nostalgic and heartwarming mood.",
        "negative": "blurry, low resolution, pixelated, bad anatomy, bad proportions, extra limbs, missing limbs, mutated features, creepy eyes, harsh shadows, overly dark colors, monochrome, grayscale, messy background, distorted scenery, flat colors, rough sketch lines, grainy, overexposed, underexposed, watermark, text, signature, off-style, low detail"
    },
    "shojo_anime": {
        "name": "Shojo",
        "positive": "A shojo anime character with large sparkling eyes, delicate facial features and soft expression, long flowing detailed hair, slim elegant proportions, romantic pastel color palette, soft glowing lighting, clean refined anime line art, emotional and dreamy shojo anime style, best quality, masterpiece, anime illustration, high resolution, ultra-detailed",
        "negative": "masculine features, muscular body, harsh lighting, gritty textures, dark color palette, photorealism, action battle pose, chibi style, extra limbs, extra fingers, missing fingers, malformed hands, bad anatomy, distorted face, cross-eye, blurry, jpeg artifacts, watermark, text, logo"
    }
}

STYLE_OPTIONS = {v["name"]: k for k, v in ANIME_STYLES.items()}

def generate_anime_image(api_key, subject_bytes, bg_bytes, style_key):
    """
    Generates an anime style image using Google GenAI.
    """
    if style_key not in ANIME_STYLES:
        raise ValueError(f"Invalid style key: {style_key}")

    style = ANIME_STYLES[style_key]
    client = genai.Client(api_key=api_key)

    prompt = f"""
    Task:
    - Transform the entire Image 1 into {style['name']} anime style.
    - Preserve the original composition, background, and all details of Image 1.
    - Do not extract the subject or remove the background.
    - Use Image 2 as a style/tone reference if applicable, otherwise focus on Image 1.
    - Place them naturally into Image 2 background
    Style Details:
    {style['positive']}

    Avoid:
    {style['negative']}
    """

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[
                types.Part.from_bytes(data=subject_bytes, mime_type="image/jpeg"),
                types.Part.from_bytes(data=bg_bytes, mime_type="image/jpeg"),
                prompt
            ],
            config=types.GenerateContentConfig(temperature=0.7)
        )

        if response.candidates and response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]
            if part.inline_data and part.inline_data.data:
                # Convert bytes to PIL Image
                return Image.open(io.BytesIO(part.inline_data.data))
        
        print("DEBUG: Unexpected response structure.")
        raise Exception("No image generated by the model.")
            
    except Exception as e:
        # Re-raise dependencies to be handled by caller (Streamlit/Flask)
        raise e

# AWS S3 Configuration
S3_BUCKET = "cred-ai-image-bucket"
S3_REGION = "us-east-1"
S3_BASE_URL = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com"

# Initialize S3 Client
s3_client = boto3.client(
    "s3",
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

def get_s3_key_from_url(url):
    """Extracts S3 key from a full S3 URL."""
    if not url:
        return None
    parsed = urlparse(url)
    return parsed.path.lstrip("/")

@app.route('/upload', methods=['POST'])
def upload_file():
    """Uploads a file to the S3 input folder."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Generate unique filename with timestamp
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{uuid.uuid4()}.{ext}"
        s3_key = f"input/{filename}"
        
        s3_client.upload_fileobj(
            file,
            S3_BUCKET,
            s3_key,
            ExtraArgs={'ContentType': file.content_type} 
        )
        
        url = f"{S3_BASE_URL}/{s3_key}"
        return jsonify({"message": "File uploaded successfully", "url": url}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/styles', methods=['GET'])
def get_styles():
    """Returns available anime styles."""
    return jsonify(STYLE_OPTIONS)

@app.route('/process', methods=['POST'])
def process_image():
    """
    Generates an anime image from S3 inputs and saves to S3 output.
    Expected JSON body:
    {
        "subject_url": "https://...",
        "background_url": "https://...",
        "style": "Shonen"
    }
    """
    data = request.json
    subject_url = data.get("subject_url")
    bg_url = data.get("background_url")
    style_name = data.get("style")

    if not subject_url or not bg_url or not style_name:
        return jsonify({"error": "Missing required fields"}), 400

    style_key = STYLE_OPTIONS.get(style_name)
    if not style_key:
         # Try finding by key if name doesn't match
        if style_name in ANIME_STYLES:
            style_key = style_name
        else:
            return jsonify({"error": "Invalid style"}), 400
            
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
         return jsonify({"error": "Server configuration error: Missing API Key"}), 500
         
    try:
        # Download images from S3
        subject_key = get_s3_key_from_url(subject_url)
        bg_key = get_s3_key_from_url(bg_url)
        
        subject_obj = s3_client.get_object(Bucket=S3_BUCKET, Key=subject_key)
        bg_obj = s3_client.get_object(Bucket=S3_BUCKET, Key=bg_key)
        
        subject_bytes = subject_obj['Body'].read()
        bg_bytes = bg_obj['Body'].read()
        
        # Generate Image
        result_image = generate_anime_image(api_key, subject_bytes, bg_bytes, style_key)
        
        if result_image:
            # Save result to buffer
            buf = io.BytesIO()
            result_image.save(buf, format="PNG")
            buf.seek(0)
            
            # Upload Result to S3
            output_filename = f"generated_{uuid.uuid4()}.png"
            output_key = f"output/{output_filename}"
            
            s3_client.upload_fileobj(
                buf,
                S3_BUCKET,
                output_key,
                ExtraArgs={'ContentType': 'image/png'}
            )
            
            output_url = f"{S3_BASE_URL}/{output_key}"
            
            response_payload = {
                "user_id": "",
                "input_s3_url": subject_url,
                "output_s3_url": output_url,
                "style": style_name,
                "background": bg_url
            }
            return jsonify(response_payload), 200
        else:
            return jsonify({"error": "Generation failed (model returned no image)"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
