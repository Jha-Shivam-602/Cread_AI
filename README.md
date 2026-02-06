# Cred AI Image Builder

## Aim of the Project
The goal of **Cred AI Image Builder** is to create a personalized anime-style image generation pipeline. It takes a user's photo, transforms it into a specific anime style (e.g., Nekomimi, Shonen, Ghibli), and seamlessly integrates it into a "Moment" polaroid-style frame or background. This creates a stylized, shareable memory card.

The system uses **Google Gemini 1.5 Pro (Vision)** for the image-to-image stylistic transformation and **AWS S3** for valid storage handling.

## Sample Assets

### Subject Images (Input)
| Subject 1 | Subject 2 |
| :---: | :---: |
| ![Subject 1](assets/subject_sample_1.png) | ![Subject 2](assets/subject_sample_2.jpg) |

### Frame / Background (Input)
![Frame](assets/frame_sample.jpg)

### Generated Output (Result)
| Output 1 | Output 2 |
| :---: | :---: |
| ![Output 1](assets/output_sample_1.png) | ![Output 2](assets/output_sample_2.png) |

---

## Setup & Installation

1.  **Navigate to the project root.**
2.  **Install Dependencies:**
    ```bash
    pip install -r server/requirements.txt
    ```
    *(Note: Ensure you have your `venv` active if using one)*

3.  **Environment Variables:**
    Ensure default `.env` or your own `.env` inside `server/.env` contains:
    ```env
    GOOGLE_API_KEY=your_google_api_key
    AWS_ACCESS_KEY_ID=your_aws_key
    AWS_SECRET_ACCESS_KEY=your_aws_secret
    ```

4.  **Run the Server:**
    ```bash
    cd server
    python api.py
    ```
    The server will start at `http://127.0.0.1:5000`.

---

## Usage (cURL Commands)

You can interact with the API using `curl`. Run these commands from your terminal (e.g., Git Bash, PowerShell).

### 1. Check Available Styles
```bash
curl -X GET http://127.0.0.1:5000/styles
```

### 2. Upload Subject Image
```bash
curl -X POST -F "file=@assets/subject_sample_1.png" http://127.0.0.1:5000/upload
```
*Returns a JSON with `url` (e.g., `https://.../input/subject.png`). Save this.*

### 3. Upload Background/Frame
```bash
curl -X POST -F "file=@assets/frame_sample.jpg" http://127.0.0.1:5000/upload
```
*Returns a JSON with `url` (e.g., `https://.../input/frame.jpg`). Save this.*

### 4. Process (Generate Image)
Replace the URLs below with the ones you got from the previous steps.

```bash
curl -X POST http://127.0.0.1:5000/process \
-H "Content-Type: application/json" \
-d '{
    "subject_url": "YOUR_SUBJECT_S3_URL",
    "background_url": "YOUR_BACKGROUND_S3_URL",
    "style": "nekomimi_anime"
}'
```

**Supported Styles:**
- `nekomimi_anime` (Nekomimi / Cat Ears)
- `shonen_anime` (Shonen Action)
- `kawaii_anime` (Kawaii / Cute)
- `mushoku_tensei_anime` (Fantasy / Mushoku Tensei)
- `ghibli_japanese_anime` (Ghibli Inspired)
- `shojo_anime` (Shojo / Romance)
