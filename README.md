This is not an officially supported Google product. This project is not
eligible for the [Google Open Source Software Vulnerability Rewards
Program](https://bughunters.google.com/open-source-security).

This project is intended for demonstration purposes only. It is not
intended for use in a production environment.

You can review [Google Cloud terms of service
here](https://console.cloud.google.com/tos?id=cloud).


# Observability Demo App

This app is intended for deployment to Cloud Run, and  uses a firestore database
to ask some trivia questions.

It also illustrates the use of logging, and opentelemetry to produce
observability data streams.


## Firestore data

The app assumes a firestore database called `o11ydemo`, an a collection called `questions`. Question documents should have the following structure:

- `q`: the contents of the question, for onscreen display
- `answer`: the expected correct answer
- `options`: (optional) a set of possible answers to the question. there should be a maximum of 3 for UI display.

## Backend API

The backend for the app has the following URL routes:

- `/question` - gets a random question from the question database
- `/question/<id>` - Gets the question with the specified ID. If send with an
    `answer` query param or via HTTP POST, it determines if the supplied answer is
    correct.
