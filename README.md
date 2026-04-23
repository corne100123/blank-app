# 🎈 Blank app template

A simple Streamlit app template for you to modify!

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://blank-app-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements

   ```
   pip install -r requirements.txt
   ```

2. Run the app

   ```
   streamlit run DFUS_30_Suite/app.py
   ```

### Build with Docker

```bash
docker build -t blank-app .
docker run -p 8501:8501 blank-app
```

### CI / Deployment

This repository includes a GitHub Actions workflow at `.github/workflows/docker-build-publish.yml` that builds a Docker image and publishes it to GitHub Container Registry (`ghcr.io`).
