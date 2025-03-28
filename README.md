# Documents OCR App

This project is a Dockerized document OCR app. It allows you to process text using an OCR engine. The app is packaged as a Docker container and can be easily set up using Docker Compose.

---

## Prerequisites

Before you begin, ensure you have the following installed:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/install/)

---

## Setup

### 1. Clone the Repository
To get started, clone this repository to your local machine:
```bash
git clone https://github.com/Usamafuward/ocr-documents.git
cd ocr-documents
```

---

### 2. Create a `.env` File
This app requires an environment variable (`GEMINI_API_KEY`) for proper configuration. Create a `.env` file in the project root directory:
```bash
echo "GEMINI_API_KEY=your_api_key" > .env
```
Replace `your_api_key` with your actual Gemini API key.

---

### 3. Build and Run the App
Use Docker Compose to build and start the application:
```bash
docker-compose up --build
```
This will:
- Build the `ocr-app` Docker image.
- Start the container and expose the app on port `8000`.

---

### 4. Access the App
Once the app is running, you can access it in your browser or via an API client (e.g., Postman) at:
```
http://localhost:8000
```

---

## Configuration

- **Environment Variables**:  
  The app requires the following environment variable:
  - `GEMINI_API_KEY`: Your API key for authentication.

- **Docker Compose**:  
  The `docker-compose.yml` file is configured to:
  - Build the app image from the current directory.
  - Expose the app on port `8000`.
  - Automatically restart the container unless stopped.

---

## Stopping the App
To stop the running containers, use:
```bash
docker-compose down
```
This will stop and remove the containers while keeping the built images intact.

---

- This repository does not include sensitive files like `.env` or configurations containing API keys.
- Make sure to secure your `.env` file and avoid sharing it publicly.

---

# Documents OCR App

This project is a Dockerized document OCR app. It allows you to process text using an OCR engine. The app is packaged as a Docker container and can be easily set up using Docker Compose.

---

## Prerequisites

Before you begin, ensure you have the following installed:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/install/)

---

## Setup

### 1. Clone the Repository
To get started, clone this repository to your local machine:
```bash
git clone https://github.com/Usamafuward/ocr-documents.git
cd ocr-documents
```

---

### 2. Create a `.env` File
This app requires an environment variable (`GEMINI_API_KEY`) for proper configuration. Create a `.env` file in the project root directory:
```bash
echo "GEMINI_API_KEY=your_api_key" > .env
```
Replace `your_api_key` with your actual Gemini API key.

---

### 3. Build and Run the App
Use Docker Compose to build and start the application:
```bash
docker-compose up --build
```
This will:
- Build the `ocr-app` Docker image.
- Start the container and expose the app on port `8000`.

---

### 4. Access the App
Once the app is running, you can access it in your browser or via an API client (e.g., Postman) at:
```
http://localhost:8000
```

---

## Configuration

- **Environment Variables**:  
  The app requires the following environment variable:
  - `GEMINI_API_KEY`: Your API key for authentication.

- **Docker Compose**:  
  The `docker-compose.yml` file is configured to:
  - Build the app image from the current directory.
  - Expose the app on port `8000`.
  - Automatically restart the container unless stopped.

---

## Stopping the App
To stop the running containers, use:
```bash
docker-compose down
```
This will stop and remove the containers while keeping the built images intact.

---

- This repository does not include sensitive files like `.env` or configurations containing API keys.
- Make sure to secure your `.env` file and avoid sharing it publicly.

---

