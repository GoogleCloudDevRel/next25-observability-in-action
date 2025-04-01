import os
import random
import datetime
import requests
import json
import asyncio
from collections import defaultdict

from quart import Quart, request, jsonify
from quart_cors import cors
from google.cloud import firestore
import google.auth.transport.requests
import google.oauth2.id_token
from concurrent import futures
from google.cloud import pubsub_v1
from typing import Callable
from google import genai
from google.genai import types

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

logger = getJSONLogger()

app = Quart(__name__)
app = cors(app, allow_origin="*")
app.asgi_app = OpenTelemetryMiddleware(app.asgi_app)

PROJECT=os.getenv("GOOGLE_CLOUD_PROJECT")
GEMMA_ENDPOINT=os.getenv("GEMMA_ENDPOINT")

fclient = firestore.Client(
  project=PROJECT,
  database="o11ydemo",
)

class gemini_models:
  def __init__(self,model):
    self.model = model 
    self.client = genai.Client(
        vertexai=True,
        project=PROJECT,
        location="us-central1",
    )
    self.generate_content_config = types.GenerateContentConfig(
      temperature = 0.2,
      top_p = 0.8,
      max_output_tokens = 1024,
      response_modalities = ["TEXT"],
      safety_settings = [types.SafetySetting(
      category="HARM_CATEGORY_HATE_SPEECH",
      threshold="OFF"
      ),types.SafetySetting(
      category="HARM_CATEGORY_DANGEROUS_CONTENT",
      threshold="OFF"
      ),types.SafetySetting(
      category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
      threshold="OFF"
      ),types.SafetySetting(
      category="HARM_CATEGORY_HARASSMENT",
      threshold="OFF"
      )],
    )

  def invoke(self, prompt):
    contents = [
        types.Content(
        role="user",
        parts=[
            types.Part.from_text(text=prompt)
        ]
      )
    ]
    
    full_chunks = ""
    full_response = ""
    for chunk in self.client.models.generate_content_stream(
        model = self.model,
        contents = contents,
        config = self.generate_content_config,
        ):
        full_chunks = full_chunks + str(chunk)
        full_response = full_response + chunk.text

    return (full_chunks,full_response)

LLM_BACKENDS = {
  "gemini-flash": gemini_models("gemini-2.0-flash"),
  "gemini-flash-lite": gemini_models("gemini-2.0-flash-lite")
}

all_models =  ['FLASH','FLASHLITE','GEMMA3']
publisher = pubsub_v1.PublisherClient()
topic_name = f'projects/{PROJECT}/topics/logPromptsAndResponses'
all_doc_ids = {}
for collection in all_models: 
    collection_ref = fclient.collection(collection)
    all_doc_ids[collection] = [doc.id for doc in collection_ref.stream()]

player_questions = {} 
player_prompts = {}
player_responses = defaultdict(list)

def get_random_document_keys(collection_name, num_keys=1):
    """
    Retrieves a specified number of random document keys from a Firestore collection.

    Args:
        collection_name: The name of the Firestore collection.
        num_keys: The number of random keys to retrieve (default is 3).

    Returns:
        A list containing the randomly selected document keys, or an empty list if the collection is empty or an error occurs.
    """

    num_keys = min(num_keys, len(all_doc_ids[collection_name]))
    random_keys = random.sample(all_doc_ids[collection_name], num_keys)

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
    condition = random.choice(player_responses[sid])

  return jsonify(
    {
      "prompt": prompt,
      "condition": condition[1],
      "answer": condition[0]
    }
  )


@app.route("/answer", methods=['POST'])
def score_question():
  got = request.args.get("answer", None)
  qid = request.args.get("qid", None)
  sid = str(request.args.get("sid", None))
  want = player_questions[sid][qid]
  logger.info("scoring question", qid=qid, correct=(got == want), model=want)
  answer_counter.add(1, attributes={'correct': (got == want), 'qid': qid})
  return jsonify({"correct": got == want,
                  "right_answer": want })

@app.route("/prompt", methods=['POST'])
async def call_llm():
  prompt = request.args.get("prompt")
  session_id = str(request.args.get("sid"))
  player_questions[session_id] = {}
  verbose_player_question = []
  for collection in all_models:
    doc_id = get_random_document_keys(collection,1)[0]
    doc_ref = fclient.collection(collection).document(doc_id)
    question_dict = doc_ref.get().to_dict()
    question_dict["qid"] = doc_id
    player_questions[session_id][doc_id] = question_dict["code"]
    verbose_player_question.append(question_dict)
  player_prompts[session_id] = prompt

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
    "response": resp[0]
  }

  code = "FLASH"
  if model == "gemini-flash-lite":
    code = "FLASHLITE"
    
  player_responses[sid].append((code,resp[1]))
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
  full_text = ""
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
  
  resp_array = resp.text.split("\n")
  resp_array.pop()
  for resp_dict in resp_array:
    resp_json = json.loads(str(resp_dict))
    full_text = full_text + resp_json["response"]
  message_dict = {
    "session_id":sid,
    "model": model,
    "prompt": prompt,
    "response": str(resp.text)
  }
  player_responses[sid].append(("GEMMA3",full_text))
  publish(message_dict)
  logger.info("LLM responded", model=model, session_id=sid)
  return resp


@app.route("/llmz")
def debug_list_backends():
  return jsonify(list(LLM_BACKENDS.keys()))


if __name__ == "__main__":
  app.run()
