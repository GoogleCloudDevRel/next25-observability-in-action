import os
import random
import datetime
import requests
import json
import asyncio

from quart import Quart, request, jsonify
from quart_cors import cors
from google.cloud import firestore
import google.auth.transport.requests
import google.oauth2.id_token
from concurrent import futures
from google.cloud import pubsub_v1
from typing import Callable


from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

from gcplogger import getJSONLogger
import models

logger = getJSONLogger()

app = Quart(__name__)
app = cors(app, allow_origin="*")
app.asgi_app = OpenTelemetryMiddleware(app.asgi_app)

PROJECT=os.getenv("GOOGLE_CLOUD_PROJECT")
GEMMA_ENDPOINT=os.getenv("GEMMA_ENDPOINT")
LLM_BACKENDS = {
  "gemini-flash": models.getGemini(PROJECT, model="gemini-2.0-flash"),
  "gemini-flash-lite": models.getGemini(PROJECT, model="gemini-2.0-flash-lite")
}

fclient = firestore.Client(
  project=PROJECT,
  database="o11ydemo",
)

publisher = pubsub_v1.PublisherClient()
topic_name = f'projects/{PROJECT}/topics/logPromptsAndResponses'
collection_ref = fclient.collection("questions")
all_document_ids = [doc.id for doc in collection_ref.stream()]

player_questions = {} 
player_prompts = {}

def get_random_document_keys(collection_name, num_keys=3):
    """
    Retrieves a specified number of random document keys from a Firestore collection.

    Args:
        collection_name: The name of the Firestore collection.
        num_keys: The number of random keys to retrieve (default is 3).

    Returns:
        A list containing the randomly selected document keys, or an empty list if the collection is empty or an error occurs.
    """

    num_keys = min(num_keys, len(all_document_ids))
    random_keys = random.sample(all_document_ids, num_keys)

    return random_keys


def setup_otel(project):
  tprovider = TracerProvider(sampler=ALWAYS_ON)
  trace.set_tracer_provider(tprovider)
  trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(insecure=True))
  )
  mreader = PeriodicExportingMetricReader(OTLPMetricExporter())
  mprovider = MeterProvider(metric_readers=[mreader])
  metrics.set_meter_provider(mprovider)

setup_otel(os.getenv("GOOGLE_CLOUD_PROJECT"))
tracer = trace.get_tracer(__name__)

#define metrics for use below.
meter = metrics.get_meter("quizdemo")
q_counter = meter.create_counter("questions_asked")
answer_counter = meter.create_counter("questions_answered")
llm_count = meter.create_counter("llm_requests")
llm_histogram = meter.create_histogram(
  name="llm_latency",
  unit="ms",
  description="latency of proxied llm requests, in milliseconds"
)
question_latency = meter.create_histogram(
  name="questions_latency",
  unit="ms",
  description="latency of quiz question requests, in milliseconds"
)
 
@app.route("/")
def health():
  return "ok", 200

@app.route("/question")
def random_q():
  starttime = datetime.datetime.now()
  session_id = str(request.args.get("sid"))
  specific_questions = player_questions[session_id]
  if len(specific_questions) > 0:
    qid = specific_questions.pop()
    doc_ref = fclient.collection('questions').document(qid)
    stoptime = datetime.datetime.now()
    latency = (stoptime - starttime) / datetime.timedelta(milliseconds=1)
    question_latency.record(latency, attributes={'qid': doc_ref.id})
    logger.info("asking question", qid=doc_ref.id, latency=latency)
    return docref_for_output(doc_ref)
  return jsonify ({
    "response": "Congrats you broke it"
  })

@app.route("/question/<qid>", methods=['GET'])
def get_question(qid):
  #debug shortcut. if we have a query string, call the post version.
  if request.args.get("answer", None):
    return score_question(qid)
  dr = fclient.collection('questions').document(qid)
  logger.info("asking question", qid=dr.id)
  q_counter.add(1)
  return docref_for_output(dr)

# format a docref for output by flask.
def docref_for_output(docref):
  rv = docref.get().to_dict()
  rv['id'] = docref.id
  return jsonify(rv)

def publish(message):
  message_string = json.dumps(message)
  future = publisher.publish(topic_name, data=message_string.encode('UTF-8'))
  message_id = future.result()  # This will block until the message is published
  return message_id

@app.route("/final",methods=['GET'])
def get_final():
  sid = str(request.args.get("sid", None))
  answer = "FLASH"
  prompt = f"How did you get here?! There was no prompt submitted for this {sid}, welps the answer is FLASH but it's hardcoded, good job you broke it."
  condition = "Nothing ran, congrats, you broke it"
  if sid in player_prompts:
    prompt = player_prompts[sid]

  return jsonify(
    {
      "prompt": prompt,
      "condition": condition,
      "answer": answer
    }
  )


@app.route("/answer", methods=['POST'])
def score_question():
  local_fclient = firestore.Client(
    project=PROJECT,
    database="o11ydemo",
  )
  got = request.args.get("answer", None)
  qid = request.args.get("qid", None)
  sid = str(request.args.get("sid", None))
  dr = local_fclient.collection('questions').document(qid)
  want = dr.get().get("code")
  logger.info("scoring question", qid=dr.id, correct=(got == want))
  answer_counter.add(1, attributes={'correct': (got == want), 'qid': dr.id})
  return jsonify({"correct": got == want,
                  "right_answer": want })

@app.route("/prompt", methods=['POST'])
async def call_llm():
  prompt = request.args.get("prompt")
  session_id = str(request.args.get("sid"))
  player_questions[session_id] = get_random_document_keys("questions",3)
  player_prompts[session_id] = prompt
  verbose_player_question = []
  for question in player_questions[session_id]:
    doc_ref = fclient.collection('questions').document(question)
    question_dict = doc_ref.get().to_dict()
    question_dict["qid"] = question
    verbose_player_question.append(question_dict)

  for llm_key in LLM_BACKENDS:
     asyncio.create_task(call_gemini(prompt, llm_key, session_id))
  asyncio.create_task(call_gemma(prompt, session_id))
  return jsonify({"player_questions": verbose_player_question})

async def call_gemini(prompt,model,sid):
  llm = LLM_BACKENDS[model]
  resp = ""
  with tracer.start_as_current_span(f"calling {model}") as span:
    span.set_attribute(key="model", value=model)
    starttime = datetime.datetime.now()
    resp = llm.invoke(prompt)
    stoptime = datetime.datetime.now()
    llmlatency = (stoptime - starttime) / datetime.timedelta(milliseconds=1)
    logger.info("LLM called", model=model, latency=llmlatency, session_id=sid)
    llm_histogram.record(llmlatency, attributes={'model': model})
    llm_count.add(1, attributes={'model': model})
  message_dict = {
    "session_id":sid,
    "model": model,
    "prompt": prompt,
    "response": str(resp.text)
  }
  publish(message_dict)
  logger.info("LLM responded", model=model, session_id=sid)
  return resp


async def call_gemma(prompt,sid):
  url = f'{GEMMA_ENDPOINT}/api/generate'
  data = {
      "model": "gemma3:1b",
      "prompt": prompt
  }
  model = "Gemma3"
  auth_req = google.auth.transport.requests.Request()
  id_token = google.oauth2.id_token.fetch_id_token(auth_req, url)


  headers = {
    'Content-Type': 'application/json',
    'Authorization': f"Bearer {id_token}"
  }
  resp = ""

  with tracer.start_as_current_span(f"calling {model}") as span:
    span.set_attribute(key="model", value=model)
    starttime = datetime.datetime.now()
    try:
      resp = requests.post(url, data=json.dumps(data), headers=headers) # Use json.dumps to convert the dictionary to a JSON string
    except: 
      pass
    stoptime = datetime.datetime.now()
    llmlatency = (stoptime - starttime) / datetime.timedelta(milliseconds=1)
    logger.info("LLM called", model=model, latency=llmlatency, session_id=sid)
    llm_histogram.record(llmlatency, attributes={'model': model})
    llm_count.add(1, attributes={'model': model})
  message_dict = {
    "session_id":sid,
    "model": model,
    "prompt": prompt,
    "response": str(resp.text)
  }
  publish(message_dict)
  logger.info("LLM responded", model=model, session_id=sid)
  return resp


@app.route("/llmz")
def debug_list_backends():
  return jsonify(list(LLM_BACKENDS.keys()))


if __name__ == "__main__":
  app.run()
