> [!WARNING]
> This is not an officially supported Google product. This project is not
> eligible for the [Google Open Source Software Vulnerability Rewards
> Program](https://bughunters.google.com/open-source-security).
> 
> This project is intended for demonstration purposes only. It is not
> intended for use in a production environment.
> 
> You can review [Google Cloud terms of service
> here](https://console.cloud.google.com/tos?id=cloud).

# Demo: Observability in Action

This demo was showcased on the show floor at Google Cloud Next 2025.

It illustrates the use of metrics and logging to produce observability data streams.
This demo leverages Cloud Run, Vertex AI, BigQuery, Firestore, Cloud Logging, Cloud Monitoring, and Cloud Trace.

## Firestore data

The app assumes a Firestore database called `o11ydemo`, an a collection called `questions`. Question documents should have the following structure:

- `question`: The content of the question.
- `constraint`: The constraint of the question.
- `code`: The answer, one of "FLASH", "FLASHLITE", or "GEMMA".
- `full`: The full name of the answer (e.g. "Gemini 2.0 Flash").

## Backend API

The backend for the app has the following URL routes:

- `POST /prompt`: Sends the user prompt and receives the questions. (sid, prompt)
- `POST /answer`: Sends the user's answer to one particular question. (sid, qid, answer)
- `GET /final`: Sends the flag that the user has completed the demo. (sid)

## Running the frontend

The frontend is located inside of the `frontend/` directory.

### Installing dependencies

```sh
npm install
```

### Running the development server (supports hot-reload)

```sh
npm run dev
```

### Building the production server

```sh
npm run build
```
